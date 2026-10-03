# coding=utf-8
# author=Ulion.Tse

import math
from typing import Optional

import pandas

from .config import CONFIG_MAP, get_env_prize
from .utils import LotteryError


class LotteryPac:
    """中奖概率与奖金期望计算框架。

    各彩种的奖级、中奖条件与奖金均以官方游戏规则为准（详见 config.py 中的规则来源），
    浮动奖按默认假设值计算期望，可用环境变量覆盖（键名见各配置类的 *_prize_env）。
    """

    PRIZE_LABELS = "一二三四五六七"

    def __init__(self, cfg):
        self.cfg = cfg
        self.bet_price = cfg.bet_price

    @staticmethod
    def pac_c(n: int, k: int) -> int:
        """组合数 C(n, k)。"""
        return math.comb(n, k)

    @staticmethod
    def pac_p(n: int, k: int) -> int:
        """排列数 P(n, k)。"""
        return math.perm(n, k)

    @staticmethod
    def hyper_c(total: int, drawn: int, pick: int, hit: int) -> int:
        """单池超几何组合数：号码池 total 个、每期开出 drawn 个、投注 pick 个时，
        恰有 hit 个投注号码被开出的组合数。"""
        if hit < 0 or hit > min(drawn, pick) or pick - hit > total - drawn:
            return 0
        return math.comb(drawn, hit) * math.comb(total - drawn, pick - hit)

    def lottery_pac_c(
        self, red_sum: int, red_aim: int, red_get: int, blue_sum: int = 1, blue_aim: int = 1, blue_get: int = 1
    ) -> int:
        """双池乐透（红/蓝两区独立，如双色球、大乐透）命中 (red_get, blue_get) 的组合数。"""
        return self.hyper_c(red_sum, red_aim, red_aim, red_get) * self.hyper_c(blue_sum, blue_aim, blue_aim, blue_get)

    @staticmethod
    def get_prize_level(prize_role: dict, hit: tuple):
        """根据命中情况反查奖级。

        :param prize_role: dict, 奖级 → 命中组合集合的映射（如 {1: {(6, 1)}, ...}）。
        :param hit: tuple, 实际命中情况（如 (红命中数, 蓝命中数)）。
        :return: int, 奖级（1 起）；未中奖返回 None。
        """
        for level, roles in prize_role.items():
            if hit in roles:
                return level
        return None

    @staticmethod
    def resolve_prize(award: dict, env_map: Optional[dict], level: int) -> float:
        """解析某奖级的单注奖金：环境变量覆盖优先于默认值。

        :param award: dict, 奖级 → 默认奖金映射。
        :param env_map: Optional[dict], 奖级 → 环境变量名映射；None 表示无覆盖项。
        :param level: int, 奖级。
        :return: float, 单注奖金（元）。
        """
        value = award[level]
        env_name = env_map.get(level) if env_map else None
        return get_env_prize(env_name, value) if env_name else float(value)

    def _make_row(
        self,
        lottery_name: str,
        play_type: str,
        prize_level: str,
        hit_condition: str,
        ways: int,
        total: int,
        prize_amount: float,
        prize_type: str,
    ) -> dict:
        return {
            "lottery_name": lottery_name,
            "play_type": play_type,
            "prize_level": prize_level,
            "hit_condition": hit_condition,
            "winning_combinations": ways,
            "total_combinations": total,
            "winning_probability": ways / total,
            "one_in_odds": round(total / ways, 4),
            "prize_amount": prize_amount,
            "prize_type": prize_type,
        }

    def get_expectation_dataframe(self, bet_price: Optional[float] = None, **kwargs) -> pandas.DataFrame:
        """按投注方式汇总单注期望奖金（元）与返奖率。

        :param bet_price: float, 覆盖单注价格（如大乐透追加投注为 3 元）；None 时用配置默认。
        :param **kwargs: 透传给 get_odds_dataframe（如 if_pool_over_800m、if_add_bet）。
        :return: pandas.DataFrame
            columns: lottery_name, play_type, bet_price_yuan, expected_value_yuan, return_rate。
        """
        frame = self.get_odds_dataframe(**kwargs)
        frame = frame.assign(expected_value=frame["winning_probability"] * frame["prize_amount"])
        expectation = frame.groupby(["lottery_name", "play_type"], sort=False, as_index=False)["expected_value"].sum()
        expectation = expectation.rename(columns={"expected_value": "expected_value_yuan"})
        price = self.bet_price if bet_price is None else bet_price
        expectation["bet_price_yuan"] = price
        expectation["return_rate"] = expectation["expected_value_yuan"] / price
        return expectation[["lottery_name", "play_type", "bet_price_yuan", "expected_value_yuan", "return_rate"]]

    def get_odds_dataframe(self, **kwargs) -> pandas.DataFrame:
        """各彩种子类实现：返回各奖级中奖组合数、概率与单注奖金明细表（抽象方法）。"""
        raise NotImplementedError


class SsqPac(LotteryPac):
    """双色球中奖概率与奖金期望。"""

    name = "ssq"

    def __init__(self):
        super().__init__(CONFIG_MAP[self.name]())

    def ssq_pac_c(self, red_get: int, blue_get: int = 1) -> int:
        red_sum, red_drawn, red_pick = self.cfg.ssq_role_red
        blue_sum, blue_drawn, blue_pick = self.cfg.ssq_role_blue
        return self.lottery_pac_c(red_sum, red_drawn, red_get, blue_sum, blue_drawn, blue_get)

    def get_odds_dataframe(self) -> pandas.DataFrame:
        cfg = self.cfg
        red_sum, _, red_pick = cfg.ssq_role_red
        blue_sum, _, blue_pick = cfg.ssq_role_blue
        total = math.comb(red_sum, red_pick) * math.comb(blue_sum, blue_pick)
        rows = []
        for level in sorted(cfg.ssq_prize_role):
            pairs = cfg.ssq_prize_role[level]
            ways = sum(self.ssq_pac_c(r, b) for r, b in pairs)
            prize = self.resolve_prize(cfg.ssq_prize_award, cfg.ssq_prize_env, level)
            rows.append(
                self._make_row(
                    self.name,
                    "单式",
                    f"{self.PRIZE_LABELS[level - 1]}等奖",
                    " / ".join(f"{r}+{b}" for r, b in pairs),
                    ways,
                    total,
                    prize,
                    cfg.ssq_floating_levels.get(level, "固定"),
                )
            )
        return pandas.DataFrame(rows)


class QlcPac(LotteryPac):
    """七乐彩中奖概率与奖金期望。

    投注 7 个号码，开奖为 7 个基本号码 + 1 个特别号码（同池，特别号从剩余号码中开出），
    属于多类别超几何分布：命中 (基本号 r 个, 特别号 s 个) 的组合数为
    C(7, r) * C(1, s) * C(22, 7 - r - s)，总组合数为 C(30, 7)。
    """

    name = "qlc"

    def __init__(self):
        super().__init__(CONFIG_MAP[self.name]())

    def qlc_pac_c(self, basic_get: int, special_get: int = 0) -> int:
        total, basic, special, pick = self.cfg.qlc_role
        rest = pick - basic_get - special_get
        if basic_get < 0 or special_get not in (0, 1) or rest < 0 or rest > total - basic - special:
            return 0
        return math.comb(basic, basic_get) * math.comb(special, special_get) * math.comb(total - basic - special, rest)

    def get_odds_dataframe(self) -> pandas.DataFrame:
        cfg = self.cfg
        total_pool, _, _, pick = cfg.qlc_role
        total = math.comb(total_pool, pick)
        rows = []
        for level in sorted(cfg.qlc_prize_role):
            pairs = cfg.qlc_prize_role[level]
            ways = sum(self.qlc_pac_c(r, s) for r, s in pairs)
            prize = self.resolve_prize(cfg.qlc_prize_award, cfg.qlc_prize_env, level)
            rows.append(
                self._make_row(
                    self.name,
                    "单式",
                    f"{self.PRIZE_LABELS[level - 1]}等奖",
                    " / ".join(f"{r}+{s}" for r, s in pairs),
                    ways,
                    total,
                    prize,
                    cfg.qlc_floating_levels.get(level, "固定"),
                )
            )
        return pandas.DataFrame(rows)


class KenoPac(LotteryPac):
    """快乐8 中奖概率与奖金期望（选一至选十）。"""

    name = "kl8"

    def __init__(self):
        super().__init__(CONFIG_MAP[self.name]())

    def keno_pac_c(self, pick: int, hit: int) -> int:
        total, drawn = self.cfg.kl8_role
        return self.hyper_c(total, drawn, pick, hit)

    def get_odds_dataframe(self, pick: Optional[int] = None) -> pandas.DataFrame:
        cfg = self.cfg
        if pick is not None and pick not in cfg.kl8_prize_table:
            raise LotteryError(f"invalid pick {pick!r} for kl8, must be one of {sorted(cfg.kl8_prize_table)}")
        picks = [pick] if pick is not None else sorted(cfg.kl8_prize_table)
        total_pool, _ = cfg.kl8_role
        rows = []
        for n in picks:
            total = math.comb(total_pool, n)
            for hit in sorted(cfg.kl8_prize_table[n], reverse=True):
                prize_level = f"选{n}中{hit}" if hit > 0 else f"选{n}全不中"
                env_name = cfg.kl8_prize_env.get((n, hit))
                default = cfg.kl8_prize_table[n][hit]
                prize = get_env_prize(env_name, default) if env_name else float(default)
                rows.append(
                    self._make_row(
                        self.name,
                        f"选{n}",
                        prize_level,
                        f"中{hit}" if hit > 0 else "全不中",
                        self.keno_pac_c(n, hit),
                        total,
                        prize,
                        cfg.kl8_floating_levels.get((n, hit), "固定"),
                    )
                )
        return pandas.DataFrame(rows)


class DltPac(LotteryPac):
    """超级大乐透中奖概率与奖金期望（现行七个奖级规则）。"""

    name = "dlt"

    def __init__(self):
        super().__init__(CONFIG_MAP[self.name]())

    def dlt_pac_c(self, red_get: int, blue_get: int = 1) -> int:
        red_sum, red_drawn, red_pick = self.cfg.dlt_role_red
        blue_sum, blue_drawn, blue_pick = self.cfg.dlt_role_blue
        return self.lottery_pac_c(red_sum, red_drawn, red_get, blue_sum, blue_drawn, blue_get)

    def get_odds_dataframe(self, if_pool_over_800m: bool = False, if_add_bet: bool = False) -> pandas.DataFrame:
        """追加投注（每注 3 元）仅参与浮动奖分配：浮动奖按基本投注对应奖金的 80% 兑付，固定奖不变。"""
        cfg = self.cfg
        award = dict(cfg.dlt_prize_award)
        if if_pool_over_800m:
            award.update(cfg.dlt_prize_award_pool_over_800m)
        red_sum, red_drawn, red_pick = cfg.dlt_role_red
        blue_sum, blue_drawn, blue_pick = cfg.dlt_role_blue
        total = math.comb(red_sum, red_pick) * math.comb(blue_sum, blue_pick)
        rows = []
        for level in sorted(cfg.dlt_prize_role):
            pairs = cfg.dlt_prize_role[level]
            ways = sum(self.dlt_pac_c(r, b) for r, b in pairs)
            prize = self.resolve_prize(award, cfg.dlt_prize_env, level)
            if if_add_bet and level in cfg.dlt_floating_levels:
                prize *= 0.8  # 追加投注浮动奖为基本投注的 80%
            rows.append(
                self._make_row(
                    self.name,
                    "单式",
                    f"{self.PRIZE_LABELS[level - 1]}等奖",
                    " / ".join(f"{r}+{b}" for r, b in pairs),
                    ways,
                    total,
                    prize,
                    cfg.dlt_floating_levels.get(level, "固定"),
                )
            )
        return pandas.DataFrame(rows)

    def get_expectation_dataframe(self, if_pool_over_800m: bool = False, if_add_bet: bool = False) -> pandas.DataFrame:
        """追加投注单注 3 元：浮动奖按基本投注的 80% 兑付，固定奖不变。"""
        return super().get_expectation_dataframe(
            bet_price=3 if if_add_bet else None, if_pool_over_800m=if_pool_over_800m, if_add_bet=if_add_bet
        )


class DigitPac(LotteryPac):
    """数字型彩票（福彩3D、排列3、排列5）中奖概率与奖金期望。"""

    def __init__(self, lottery_name: str = "3d"):
        self.name = lottery_name
        self.prefix = "fc3d" if lottery_name == "3d" else lottery_name
        super().__init__(CONFIG_MAP[lottery_name]())

    hit_condition_map = {
        "单选": "按位完全相同",
        "直选": "按位完全相同",
        "组选3": "数字相同顺序不限(开奖号含两位相同)",
        "组选6": "数字相同顺序不限(开奖号三位各不相同)",
    }

    def get_odds_dataframe(self) -> pandas.DataFrame:
        cfg = self.cfg
        digits = getattr(cfg, f"{self.prefix}_digits")
        play = getattr(cfg, f"{self.prefix}_prize_play")
        total = 10**digits
        rows = []
        for play_type, (ways, prize) in play.items():
            rows.append(
                self._make_row(
                    self.name,
                    play_type,
                    "固定奖",
                    self.hit_condition_map[play_type],
                    ways,
                    total,
                    float(prize),
                    "固定",
                )
            )
        return pandas.DataFrame(rows)


class QxcPac(LotteryPac):
    """7星彩中奖概率与奖金期望。

    前六位每位 0-9（按位比对），最后一位 0-14，共 10^6 * 15 种组合。
    命中 (前区 f 位, 最后一位 l) 的组合数为 C(6, f) * 9^(6-f) * (1 if l else 14)。
    """

    name = "qxc"

    def __init__(self):
        super().__init__(CONFIG_MAP[self.name]())

    def qxc_pac_c(self, front_get: int, last_get: int = 0) -> int:
        cfg = self.cfg
        positions, radix, last_radix = cfg.qxc_front_positions, cfg.qxc_front_radix, cfg.qxc_last_radix
        if not 0 <= front_get <= positions or last_get not in (0, 1):
            return 0
        ways = math.comb(positions, front_get) * (radix - 1) ** (positions - front_get)
        return ways * (1 if last_get == 1 else last_radix - 1)

    def get_odds_dataframe(self) -> pandas.DataFrame:
        cfg = self.cfg
        total = cfg.qxc_front_radix**cfg.qxc_front_positions * cfg.qxc_last_radix
        rows = []
        for level in sorted(cfg.qxc_prize_role):
            pairs = cfg.qxc_prize_role[level]
            ways = sum(self.qxc_pac_c(fr, ls) for fr, ls in pairs)
            prize = self.resolve_prize(cfg.qxc_prize_award, cfg.qxc_prize_env, level)
            rows.append(
                self._make_row(
                    self.name,
                    "单式",
                    f"{self.PRIZE_LABELS[level - 1]}等奖",
                    " / ".join(f"{fr}+{ls}" for fr, ls in pairs),
                    ways,
                    total,
                    prize,
                    cfg.qxc_floating_levels.get(level, "固定"),
                )
            )
        return pandas.DataFrame(rows)


def load_prize_odds(lottery_name: str = "ssq", **kwargs) -> pandas.DataFrame:
    """Return the per-prize odds table for a game.

    Exact combinatorics on top of the current official rules (source URLs in
    `config.py`): winning combinations, probabilities, prize amounts, prize type.

    !!! note "中文说明"

        返回指定彩种各奖级的中奖组合数、中奖概率与奖金明细表——规则来源均为
        官网（cwl.gov.cn / lottery.gov.cn，见 config.py）。

    :param lottery_name: str, must in ('ssq', 'qlc', 'kl8', '3d', 'dlt', 'pls', 'plw', 'qxc').
    :param **kwargs:
            :param pick: int, only for kl8, 1-10, default None（返回全部玩法）.
            :param if_pool_over_800m: boolean, only for dlt, default False.
            :param if_add_bet: boolean, only for dlt, default False. 追加投注：浮动奖按 80% 兑付。
    :return: pandas.DataFrame
    """
    return _get_pac(lottery_name).get_odds_dataframe(**kwargs)


def load_prize_expectation(lottery_name: str = "ssq", **kwargs) -> pandas.DataFrame:
    """返回指定彩种的单注期望奖金（元）与返奖率。

    浮动奖按 config.py 中的默认假设值计算（可用环境变量覆盖），
    因此返奖率为基于假设值的静态期望，    实际返奖率以当期开奖公告为准。

    :param lottery_name: str, must in ('ssq', 'qlc', 'kl8', '3d', 'dlt', 'pls', 'plw', 'qxc').
    :param **kwargs:
            :param pick: int, only for kl8, 1-10, default None（返回全部玩法）.
            :param if_pool_over_800m: boolean, only for dlt, default False.
            :param if_add_bet: boolean, only for dlt, default False. 追加投注：3 元/注，浮动奖按 80% 兑付。
    :return: pandas.DataFrame
    """
    return _get_pac(lottery_name).get_expectation_dataframe(**kwargs)


def load_dlt_compound_expectation(
    n_red: int = 5, m_blue: int = 2, if_pool_over_800m: bool = False, if_add_bet: bool = False
) -> pandas.DataFrame:
    r"""返回大乐透复式投注的注数、成本与整票期望。

    复式票选定 \(n_{red}\) 个前区号码与 \(m_{blue}\) 个后区号码，组合为
    \(\binom{n_{red}}{5}\times\binom{m_{blue}}{2}\) 注单式。开奖后前区命中
    \(r\) 个、后区命中 \(b\) 个时：

    $$P(r,b)=\frac{\binom{5}{r}\binom{30}{n_{red}-r}}{\binom{35}{n_{red}}}
    \times\frac{\binom{2}{b}\binom{10}{m_{blue}-b}}{\binom{12}{m_{blue}}}$$

    $$\text{i 等奖中奖注数}=\sum_{(j,l)\in R_i}\binom{r}{j}\binom{n_{red}-r}{5-j}
    \binom{b}{l}\binom{m_{blue}-b}{2-l}$$

    $$\mathbb{E}[\text{整票奖金}]=\sum_{r,b}P(r,b)\cdot\text{Prize}(r,b)$$

    由期望的线性性，整票期望恒等于 **总注数 × 单式期望**（返奖率不变），
    复式只改变成本与方差。

    :param n_red: int, 前区号码个数，5-35。
    :param m_blue: int, 后区号码个数，2-12。
    :param if_pool_over_800m: boolean, 奖池 ≥ 8 亿元档固定奖，default False.
    :param if_add_bet: boolean, 复式追加（3 元/注，浮动奖 80%），default False.
    :return: pandas.DataFrame（单行）
        columns: lottery_name, n_red, m_blue, total_bets, cost_yuan, expected_prize_yuan, return_rate
    """
    if not 5 <= n_red <= 35 or not 2 <= m_blue <= 12:
        raise LotteryError(f"n_red ({n_red}) must be in 5..35 and m_blue ({m_blue}) in 2..12")
    pac = DltPac()
    cfg = pac.cfg
    award = dict(cfg.dlt_prize_award)
    if if_pool_over_800m:
        award.update(cfg.dlt_prize_award_pool_over_800m)
    price = 3 if if_add_bet else 2
    total_bets = math.comb(n_red, 5) * math.comb(m_blue, 2)
    red_denominator = math.comb(35, n_red)
    blue_denominator = math.comb(12, m_blue)

    expected = 0.0
    for r in range(0, 6):
        red_probability = math.comb(5, r) * math.comb(30, n_red - r) / red_denominator
        for b in range(0, 3):
            blue_probability = math.comb(2, b) * math.comb(10, m_blue - b) / blue_denominator
            prize = 0.0
            for level, roles in cfg.dlt_prize_role.items():
                bets = sum(
                    math.comb(r, j) * math.comb(n_red - r, 5 - j) * math.comb(b, ls) * math.comb(m_blue - b, 2 - ls)
                    for j, ls in roles
                )
                if bets == 0:
                    continue
                amount = pac.resolve_prize(award, cfg.dlt_prize_env, level)
                if if_add_bet and level in cfg.dlt_floating_levels:
                    amount *= 0.8
                prize += bets * amount
            expected += red_probability * blue_probability * prize

    return pandas.DataFrame(
        [
            {
                "lottery_name": "dlt",
                "n_red": n_red,
                "m_blue": m_blue,
                "total_bets": total_bets,
                "cost_yuan": total_bets * price,
                "expected_prize_yuan": expected,
                "return_rate": expected / (total_bets * price),
            }
        ]
    )


# ----- assembly：默认实例池与派发（依赖上方类定义，统一置于文件末尾）-----

# 模块级实例池：与 data.py 底部 `_cl = ChinaLottery()` 同一风格；
# Pac 实例无状态（cfg 固定，kwargs 按次传入），单例安全。
_lottery_pac_pool = {
    "ssq": SsqPac(),
    "qlc": QlcPac(),
    "kl8": KenoPac(),
    "3d": DigitPac("3d"),
    "pls": DigitPac("pls"),
    "plw": DigitPac("plw"),
    "dlt": DltPac(),
    "qxc": QxcPac(),
}


def _get_pac(lottery_name: str) -> LotteryPac:
    pac = _lottery_pac_pool.get(lottery_name)
    if pac is None:
        raise LotteryError(f"unsupported lottery name {lottery_name!r}")
    return pac
