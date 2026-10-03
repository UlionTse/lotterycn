# coding=utf-8
# author=Ulion.Tse

from typing import cast

import pandas

from .config import CONFIG_MAP, get_env_prize
from .odds import LotteryPac
from .utils import LotteryError


class LotteryChecker(LotteryPac):
    r"""中奖校验：解析投注号码与开奖号码，输出命中情况、奖级与奖金。

        **投注号码格式**（与 data.py 历史开奖数据的 lottery_red / lottery_blue 列一致）：

    | 彩种 | 格式 | 示例 |
    |---|---|---|
    | ssq | 6 红 + 1 蓝 | `'01,05,12,18,27,33\|08'` |
    | dlt | 5 前区 + 2 后区 | `'01,05,12,18,27\|03,08'` |
    | qlc | 仅 7 个号码（特别号不可自选） | `'01,05,12,18,22,27,30'` |
    | kl8 | 选 1-10 个号码 | `'01,02,03,04,05'` |
    | 3d / pls | 3 位数字 | `'123'` 或 `'1,2,3'` |
    | plw | 5 位数字 | `'12345'` 或 `'1,2,3,4,5'` |
    | qxc | 6 位前区 + 末位(0-14) | `'1,2,3,4,5,6\|14'` |

    开奖号码除字符串外，还支持传入含 `lottery_red` / `lottery_blue` 字段的 dict 或 pandas.Series。

    !!! tip "自动拉取最新开奖"

        `load_check_result(..., draw_number=None)` 时自动联网获取最新一期开奖，
        配合 `if_cached=True` 走本地缓存与增量更新。

    !!! note "校验失败"

        号码个数、取值范围或去重不合法时抛出 `LotteryError`。
    """

    def __init__(self, lottery_name: str = "ssq"):
        if lottery_name not in CONFIG_MAP:
            raise LotteryError(f"unsupported lottery name {lottery_name!r}, must be one of {sorted(CONFIG_MAP)}")
        self.name = lottery_name
        self.prefix = "fc3d" if lottery_name == "3d" else lottery_name
        super().__init__(CONFIG_MAP[lottery_name]())

    # ---- 号码解析 ----

    @staticmethod
    def _to_int_list(text, if_split_chars: bool = False) -> list:
        # pandas.isna 覆盖 np.nan 与 pd.NA；列表/元组短路避免对容器误调 isna
        if text is None or (not isinstance(text, (list, tuple)) and pandas.isna(text)):
            return []
        if isinstance(text, (list, tuple)):
            parts = list(text)
        else:
            text = str(text).strip()
            if not text:
                return []
            if "," in text:
                parts = text.split(",")
            elif " " in text:
                parts = text.split()
            elif if_split_chars:
                parts = list(text)
            else:
                parts = [text]
        return [int(str(part).strip()) for part in parts if str(part).strip() != ""]

    def _parse_lottery_number(self, number) -> tuple:
        if isinstance(number, str):
            red_text, _, blue_text = number.partition("|")
        elif isinstance(number, (list, tuple)) and len(number) == 2:
            red_text, blue_text = number
        else:
            raise LotteryError(f'invalid number {number!r}, expected "reds|blue" or (reds, blues)')
        if_split_chars = self.name in ("3d", "pls", "plw", "qxc")
        reds = self._to_int_list(red_text, if_split_chars=if_split_chars)
        blues = self._to_int_list(blue_text)
        return reds, blues

    def _normalize_draw(self, draw_number) -> tuple:
        if isinstance(draw_number, str):
            return self._parse_lottery_number(draw_number)
        if isinstance(draw_number, dict) or hasattr(draw_number, "get"):
            if_split_chars = self.name in ("3d", "pls", "plw", "qxc")
            reds = self._to_int_list(draw_number.get("lottery_red"), if_split_chars=if_split_chars)
            blues = self._to_int_list(draw_number.get("lottery_blue"))
            return reds, blues
        if isinstance(draw_number, (list, tuple)) and len(draw_number) == 2:
            return self._parse_lottery_number(tuple(draw_number))
        raise LotteryError(f'invalid draw number {draw_number!r}, expected "reds|blue" or (reds, blues)')

    def _validate(self, reds: list, blues: list):
        name = self.name

        def check_pool(numbers, pool, count, if_unique=True):
            if len(numbers) != count or (if_unique and len(set(numbers)) != count):
                raise LotteryError(f"{name}: expected {count} unique numbers, got {numbers!r}")
            if any(not 1 <= n <= pool for n in numbers):
                raise LotteryError(f"{name}: numbers must be in 1..{pool}, got {numbers!r}")

        if name == "ssq":
            check_pool(reds, 33, 6)
            check_pool(blues, 16, 1)
        elif name == "dlt":
            check_pool(reds, 35, 5)
            check_pool(blues, 12, 2)
        elif name == "qlc":
            check_pool(reds, 30, 7)
            if blues:
                raise LotteryError("qlc does not accept a blue (special) number")
        elif name == "kl8":
            if not 1 <= len(reds) <= 10 or len(set(reds)) != len(reds):
                raise LotteryError(f"kl8: expected 1-10 unique numbers, got {len(reds)}")
            if any(not 1 <= n <= 80 for n in reds) or blues:
                raise LotteryError(f"kl8: numbers must be in 1..80, no blues allowed: {reds!r}")
        elif name in ("3d", "pls"):
            if len(reds) != 3 or any(not 0 <= n <= 9 for n in reds) or blues:
                raise LotteryError(f"{name}: expected 3 digits in 0..9, no blues allowed: {reds!r}")
        elif name == "plw":
            if len(reds) != 5 or any(not 0 <= n <= 9 for n in reds) or blues:
                raise LotteryError(f"plw: expected 5 digits in 0..9, no blues allowed: {reds!r}")
        elif name == "qxc":
            if len(reds) != 6 or any(not 0 <= n <= 9 for n in reds):
                raise LotteryError(f"qxc: expected 6 digits in 0..9, got {reds!r}")
            if len(blues) != 1 or not 0 <= blues[0] <= 14:
                raise LotteryError(f"qxc: expected exactly 1 last digit in 0..14, got {blues!r}")

    # ---- 奖金解析 ----

    def _prize_row(self, prize_level, hit_detail, prize_amount, prize_type) -> dict:
        return {
            "lottery_name": self.name,
            "prize_level": prize_level,
            "hit_detail": hit_detail,
            "prize_amount": prize_amount,
            "prize_type": prize_type,
        }

    def _miss_row(self, hit_detail) -> dict:
        return self._prize_row("未中奖", hit_detail, 0.0, "-")

    def _level_prize(self, level, award_attr, env_attr, floating_attr, labels):
        if level is None:
            return None
        award = getattr(self.cfg, award_attr)
        env_map = getattr(self.cfg, env_attr, None)
        prize = self.resolve_prize(award, env_map, level)
        prize_type = getattr(self.cfg, floating_attr, {}).get(level, "固定")
        return self._prize_row(f"{labels[level - 1]}等奖", "", prize, prize_type)

    # ---- 各彩种校验 ----

    def _check_dual_pool(self, my_reds, my_blues, draw_reds, draw_blues, role_attr, red_label, blue_label) -> dict:
        red_hit = len(set(my_reds) & set(draw_reds))
        blue_hit = len(set(my_blues) & set(draw_blues))
        level = self.get_prize_level(getattr(self.cfg, role_attr), (red_hit, blue_hit))
        hit_detail = f"{red_label}中{red_hit}个,{blue_label}中{blue_hit}个"
        if level is None:
            return self._miss_row(hit_detail)
        row = self._level_prize(
            level,
            f"{self.name}_prize_award",
            f"{self.name}_prize_env",
            f"{self.name}_floating_levels",
            "一二三四五六七",
        )
        row["hit_detail"] = hit_detail
        return row

    def _check_qlc(self, my_reds, draw_reds, draw_blues) -> dict:
        red_hit = len(set(my_reds) & set(draw_reds))
        special_hit = 1 if draw_blues and draw_blues[0] in my_reds else 0
        level = self.get_prize_level(self.cfg.qlc_prize_role, (red_hit, special_hit))
        hit_detail = f"基本号中{red_hit}个,特别号{'命中' if special_hit else '未中'}"
        if level is None:
            return self._miss_row(hit_detail)
        row = self._level_prize(level, "qlc_prize_award", "qlc_prize_env", "qlc_floating_levels", "一二三四五六七")
        row["hit_detail"] = hit_detail
        return row

    def _check_kl8(self, my_reds, draw_reds) -> dict:
        pick = len(my_reds)
        hit = len(set(my_reds) & set(draw_reds))
        prize_table = self.cfg.kl8_prize_table[pick]
        hit_detail = f"选{pick}中{hit}" if hit > 0 else f"选{pick}全不中"
        if hit not in prize_table:
            return self._miss_row(hit_detail)
        env_name = self.cfg.kl8_prize_env.get((pick, hit))
        prize = get_env_prize(env_name, prize_table[hit]) if env_name else float(prize_table[hit])
        prize_type = self.cfg.kl8_floating_levels.get((pick, hit), "固定")
        return self._prize_row(hit_detail, hit_detail, prize, prize_type)

    def _check_digit(self, my_reds, draw_reds) -> list:
        exact = my_reds == draw_reds
        same_multiset = sorted(my_reds) == sorted(draw_reds)
        has_repeat = len(set(draw_reds)) < len(draw_reds)
        play = getattr(self.cfg, f"{self.prefix}_prize_play")

        exact_play = "单选" if "单选" in play else "直选"
        hit_plays = []
        if exact:
            hit_plays.append((exact_play, "按位完全相同"))
        if same_multiset and has_repeat and "组选3" in play:
            hit_plays.append(("组选3", "数字相同顺序不限,开奖号含两位相同"))
        if same_multiset and not has_repeat and "组选6" in play:
            hit_plays.append(("组选6", "数字相同顺序不限,开奖号三位各不相同"))

        if not hit_plays:
            return [self._miss_row("未与开奖号码相符")]
        rows = []
        for play_type, hit_detail in hit_plays:
            _, prize = play[play_type]
            rows.append(self._prize_row(play_type, hit_detail, float(prize), "固定"))
        return rows

    def _check_qxc(self, my_reds, my_blues, draw_reds, draw_blues) -> dict:
        front_hit = sum(1 for a, b in zip(my_reds, draw_reds) if a == b)
        last_hit = 1 if my_blues and draw_blues and my_blues[0] == draw_blues[0] else 0
        level = self.get_prize_level(self.cfg.qxc_prize_role, (front_hit, last_hit))
        hit_detail = f"前区按位中{front_hit}个,最后一位{'命中' if last_hit else '未中'}"
        if level is None:
            return self._miss_row(hit_detail)
        row = self._level_prize(level, "qxc_prize_award", "qxc_prize_env", "qxc_floating_levels", "一二三四五六")
        row["hit_detail"] = hit_detail
        return row

    # ---- 对外接口 ----

    def check(self, my_number, draw_number) -> pandas.DataFrame:
        """校验投注号码与开奖号码，返回命中情况、奖级与奖金明细。"""
        my_reds, my_blues = self._parse_lottery_number(my_number)
        self._validate(my_reds, my_blues)
        draw_reds, draw_blues = self._normalize_draw(draw_number)

        if self.name in ("ssq", "dlt"):
            labels = {"ssq": ("红球", "蓝球"), "dlt": ("前区", "后区")}[self.name]
            rows = [self._check_dual_pool(my_reds, my_blues, draw_reds, draw_blues, f"{self.name}_prize_role", *labels)]
        elif self.name == "qlc":
            rows = [self._check_qlc(my_reds, draw_reds, draw_blues)]
        elif self.name == "kl8":
            rows = [self._check_kl8(my_reds, draw_reds)]
        elif self.name in ("3d", "pls", "plw"):
            rows = self._check_digit(my_reds, draw_reds)
        elif self.name == "qxc":
            rows = [self._check_qxc(my_reds, my_blues, draw_reds, draw_blues)]
        else:
            raise LotteryError(f"unsupported lottery name {self.name!r} for prize checking")

        frame = pandas.DataFrame(rows)
        frame.insert(1, "my_number", str(my_number))
        frame.insert(2, "draw_number", str(draw_number))
        return frame

    def check_latest(self, my_number, **kwargs) -> pandas.DataFrame:
        """拉取最新一期开奖号码并校验（需联网）。"""
        from .data import load_history_data

        frame = cast(pandas.DataFrame, load_history_data(lottery_name=self.name, **kwargs))

        latest = frame.iloc[-1]
        draw_number = {
            "lottery_red": latest.get("lottery_red"),
            "lottery_blue": latest.get("lottery_blue"),
        }
        return self.check(my_number, draw_number)


def load_check_result(lottery_name: str, my_number, draw_number=None, **kwargs) -> pandas.DataFrame:
    """Check a ticket against a draw and report hit counts, prize tier and amount.

    !!! note "中文说明"

        校验指定彩票是否中奖：解析投注号码与开奖号码，输出命中详情、奖级
        与奖金；`draw_number=None` 时自动拉取最新一期开奖（配合
        `if_cached=True` 走本地缓存）。

    :param lottery_name: str, must in ('ssq', 'qlc', 'kl8', '3d', 'dlt', 'pls', 'plw', 'qxc').
    :param my_number: str or tuple, 投注号码，格式见 LotteryChecker 文档。
    :param draw_number: str or dict or None, 开奖号码；为 None 时自动拉取最新一期开奖（需联网）。
    :param **kwargs:
            :param if_cached: boolean, default False. only for draw_number=None.
            :param timeout: float, default 15. only for draw_number=None.
            :param proxies: dict, default None. only for draw_number=None.
    :return: pandas.DataFrame
    """
    checker = LotteryChecker(lottery_name=lottery_name)
    if draw_number is None:
        return checker.check_latest(my_number, **kwargs)
    return checker.check(my_number, draw_number)
