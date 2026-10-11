# coding=utf-8
# author=uliontse

"""开奖详情：销售额、奖池、各奖级中奖注数与单注奖金、一等奖省级分布。

数据来源与 data.py 相同（cwl.gov.cn / lottery.gov.cn 官方网站），
只是保留并归一化了原本被丢弃的字段，输出三张 tidy 表：

  detail    宽表（每期一行）：期号 / 日期 / 号码 / 销售额 / 奖池
  prizes    长表（期 × 奖级）：中奖注数、单注奖金（dlt 含追加档，未开出的单注奖金为 NaN）
  province  长表（期 × 省）：一等奖省级分布（仅 ssq / qlc / kl8 提供，3d 官网接口恒为空）

!!! warning "仅供娱乐，不构成任何预测力"

    这些字段刻画的是当期开奖结果与资金面，可作为特征工程的原材料，但它们
    由同一期随机开奖决定，与未来开奖号码之间不存在因果信息。请理性购彩。
"""

import re
import datetime
from typing import Callable, Optional, cast

import pandas

from .cache import CWL_PROJECTS, get_cache_path
from .data import load_history_data, lottery_pool
from .utils import LotteryError


DETAIL_COLS = [
    "lottery_name",
    "lottery_order",
    "lottery_date",
    "lottery_red",
    "lottery_blue",
    "sales_yuan",
    "pool_yuan",
]
PRIZE_COLS = [
    "lottery_name",
    "lottery_order",
    "lottery_date",
    "play_type",
    "prize_level",
    "winner_count",
    "prize_per_bet_yuan",
]
PROVINCE_COLS = ["lottery_name", "lottery_order", "lottery_date", "province", "count"]

DEDUP_KEYS = {
    "detail": ["lottery_name", "lottery_order"],
    "prizes": ["lottery_name", "lottery_order", "play_type", "prize_level"],
    "province": ["lottery_name", "lottery_order", "province"],
}
NUMERIC_COLS = {
    "detail": ["sales_yuan", "pool_yuan"],
    "prizes": ["winner_count", "prize_per_bet_yuan"],
    "province": ["count"],
}

CN_LEVELS = "一二三四五六七八九十"
KL8_PREFIX = {
    "x10": "选十",
    "x9": "选九",
    "x8": "选八",
    "x7": "选七",
    "x6": "选六",
    "x5": "选五",
    "x4": "选四",
    "x3": "选三",
    "x2": "选二",
    "x1": "选一",
}
CN_DIGITS = {str(i): c for i, c in enumerate(CN_LEVELS[:10], start=1)} | {"10": "十"}
PROVINCE_RE = re.compile(r"([\u4e00-\u9fa5]{1,8}?)(\d+)注")


def _to_int(text) -> Optional[int]:
    digits = re.sub(r"[^\d-]", "", str(text or ""))
    return int(digits) if digits not in ("", "-") else None


def _to_float(text) -> Optional[float]:
    cleaned = re.sub(r"[^\d.\-]", "", str(text or ""))
    return float(cleaned) if cleaned not in ("", "-", ".") else None


def _detail_row_cwl(record: dict, lottery_name: str) -> dict:
    # CWL date 字段可能带星期后缀，如 '2026-09-29(二)'
    return {
        "lottery_name": lottery_name,
        "lottery_order": str(record.get("code", "")),
        "lottery_date": str(record.get("date", "")).split("(")[0],
        "lottery_red": record.get("red", ""),
        "lottery_blue": record.get("blue") or "",
        "sales_yuan": _to_float(record.get("sales")),
        "pool_yuan": _to_float(record.get("poolmoney")),
    }


def _prize_rows_cwl(record: dict, lottery_name: str) -> list:
    rows = []
    base = _detail_row_cwl(record, lottery_name)
    for grade in record.get("prizegrades") or []:
        winner_count = _to_int(grade.get("typenum"))
        prize = _to_int(grade.get("typemoney"))
        if winner_count is None and prize is None:
            continue  # 空档位（如 3d 未提供、ssq 第七档占位）
        gtype = str(grade.get("type", ""))
        if lottery_name == "kl8":
            prefix, k = gtype.split("z", 1)
            play_type = KL8_PREFIX.get(prefix, prefix)
            prize_level = f"{play_type}全不中" if k == "0" else f"{play_type}中{CN_DIGITS[k]}"
        else:
            play_type = "单式"
            prize_level = f"{CN_LEVELS[int(gtype) - 1]}等奖" if gtype.isdigit() else gtype
        rows.append(
            {
                **{c: base[c] for c in ("lottery_name", "lottery_order", "lottery_date")},
                "play_type": play_type,
                "prize_level": prize_level,
                "winner_count": winner_count,
                "prize_per_bet_yuan": prize if (prize is None or prize >= 0) else None,
            }
        )
    return rows


def _province_rows_cwl(record: dict, lottery_name: str) -> list:
    text = re.sub(r"共\d+注。?", "", str(record.get("content") or ""))
    base = {c: _detail_row_cwl(record, lottery_name)[c] for c in ("lottery_name", "lottery_order", "lottery_date")}
    return [{**base, "province": province, "count": int(count)} for province, count in PROVINCE_RE.findall(text)]


def _split_result_csl(record: dict, lottery_name: str) -> tuple:
    parts = str(record.get("lotteryDrawResult") or "").split(" ")
    if lottery_name == "dlt":
        return ",".join(parts[:5]), ",".join(parts[5:])
    if lottery_name == "qxc":
        return ",".join(parts[:6]), ",".join(parts[6:])
    return ",".join(parts), ""


def _detail_row_csl(record: dict, lottery_name: str) -> dict:
    red, blue = _split_result_csl(record, lottery_name)
    return {
        "lottery_name": lottery_name,
        "lottery_order": str(record.get("lotteryDrawNum", "")),
        "lottery_date": str(record.get("lotteryDrawTime", "")),
        "lottery_red": red,
        "lottery_blue": blue,
        "sales_yuan": _to_float(record.get("totalSaleAmount")),
        "pool_yuan": _to_float(record.get("poolBalanceAfterdraw")),
    }


def _prize_rows_csl(record: dict, lottery_name: str) -> list:
    rows = []
    base = _detail_row_csl(record, lottery_name)
    for level in record.get("prizeLevelList") or []:
        prize_level = str(level.get("prizeLevel", ""))
        winner_count = _to_int(level.get("stakeCount"))
        prize = _to_int(level.get("stakeAmountFormat"))
        rows.append(
            {
                **{c: base[c] for c in ("lottery_name", "lottery_order", "lottery_date")},
                "play_type": "追加" if "追加" in prize_level else "单式",
                "prize_level": prize_level,
                "winner_count": winner_count,
                "prize_per_bet_yuan": prize if (prize is None or prize >= 0) else None,
            }
        )
    return rows


def _build_detail(lottery_name: str, records: list) -> pandas.DataFrame:
    if lottery_name in CWL_PROJECTS:
        rows = [_detail_row_cwl(r, lottery_name) for r in records]
    else:
        rows = [_detail_row_csl(r, lottery_name) for r in records]
    return pandas.DataFrame(rows, columns=DETAIL_COLS)


def _build_prizes(lottery_name: str, records: list) -> pandas.DataFrame:
    rows = []
    for r in records:
        rows.extend(
            _prize_rows_cwl(r, lottery_name) if lottery_name in CWL_PROJECTS else _prize_rows_csl(r, lottery_name)
        )
    return pandas.DataFrame(rows, columns=PRIZE_COLS)


def _build_province(lottery_name: str, records: list) -> pandas.DataFrame:
    rows = []
    if lottery_name in CWL_PROJECTS:
        for r in records:
            rows.extend(_province_rows_cwl(r, lottery_name))
    return pandas.DataFrame(rows, columns=PROVINCE_COLS)


def _raw_records(lottery_name: str, records, fetch_kwargs: dict) -> list:
    if records is not None:
        return records
    return cast(list, load_history_data(lottery_name=lottery_name, is_detail_result=True, **fetch_kwargs))


def _cached_table(
    lottery_name: str,
    table: str,
    build_fn: Callable,
    if_cached: bool,
    cache_dir: Optional[str],
    records,
    fetch_kwargs: dict,
):
    """三张表共用的构建 + 增量缓存逻辑（期 × 行，按最后开奖日期增量刷新）。"""
    path = get_cache_path(lottery_name, cache_dir=cache_dir, table=table)
    use_cache = if_cached and records is None
    if use_cache and path.exists():
        cached = pandas.read_csv(path, dtype=str).fillna("")
        cached = cached[cached["lottery_date"].notna() & (cached["lottery_date"] != "")]
        if cached.empty:
            cached = None
    else:
        cached = None

    if cached is None:
        frame = build_fn(lottery_name, _raw_records(lottery_name, records, fetch_kwargs))
    else:
        fetch_kwargs = dict(fetch_kwargs)
        fetch_kwargs.pop("begin_date", None)
        if lottery_name in CWL_PROJECTS:
            last_date = datetime.date.fromisoformat(cached["lottery_date"].max())
            fetch_kwargs["begin_date"] = (last_date + datetime.timedelta(days=1)).isoformat()
        fresh = build_fn(lottery_name, _raw_records(lottery_name, records, fetch_kwargs))
        frame = pandas.concat([cached, fresh], axis=0, ignore_index=True)

    if frame.empty:
        return frame
    frame = frame.drop_duplicates(subset=DEDUP_KEYS[table], keep="last")
    frame = frame.sort_values(by=["lottery_date", "lottery_order"]).reset_index(drop=True)
    for col in NUMERIC_COLS[table]:
        frame[col] = pandas.to_numeric(frame[col], errors="coerce")
    if use_cache:
        try:
            frame.to_csv(path, index=False)
        except OSError:
            pass  # 缓存写入失败不影响数据返回
    return frame


def _check_game(lottery_name: str):
    if lottery_name not in lottery_pool:
        raise LotteryError(f"unsupported lottery name {lottery_name!r}, must be one of {sorted(lottery_pool)}")


def load_draw_detail(
    lottery_name: str, records=None, if_cached: bool = False, cache_dir: Optional[str] = None, **fetch_kwargs
) -> pandas.DataFrame:
    """返回宽表（每期一行）：期号 / 开奖日期 / 号码 / 销售额 / 奖池累计金额。

    :param lottery_name: str, 彩种代码。
    :param records: list, 显式传入原始开奖记录（离线使用）；为 None 时联网拉取。
    :param if_cached: boolean, 启用本地 CSV 缓存与增量更新。
    :param cache_dir: str, optional, 缓存目录；None 时取环境变量或默认值。
    :param **fetch_kwargs: 透传给 load_history_data（timeout / max_retries / proxies 等）。
    :return: pandas.DataFrame, 宽表（每期一行）：期号 / 开奖日期 / 号码 / 销售额 / 奖池累计金额。
    """
    _check_game(lottery_name)
    return _cached_table(lottery_name, "detail", _build_detail, if_cached, cache_dir, records, fetch_kwargs)


def load_prize_results(
    lottery_name: str, records=None, if_cached: bool = False, cache_dir: Optional[str] = None, **fetch_kwargs
) -> pandas.DataFrame:
    """返回长表（期 × 奖级）：各奖级中奖注数与单注奖金。

    dlt 含追加档（prize_level 带"(追加)"）；未开出的奖级单注奖金为 NaN；
    3d 官网接口不提供奖级数据，返回空表。

    :param lottery_name: str, 彩种代码。
    :param records: list, 显式传入原始开奖记录（离线使用）；为 None 时联网拉取。
    :param if_cached: boolean, 启用本地 CSV 缓存与增量更新。
    :param cache_dir: str, optional, 缓存目录；None 时取环境变量或默认值。
    :param **fetch_kwargs: 透传给 load_history_data（timeout / max_retries / proxies 等）。
    :return: pandas.DataFrame, 长表（期 × 奖级）：中奖注数与单注奖金。
    """
    _check_game(lottery_name)
    return _cached_table(lottery_name, "prizes", _build_prizes, if_cached, cache_dir, records, fetch_kwargs)


def load_first_prize_by_province(
    lottery_name: str, records=None, if_cached: bool = False, cache_dir: Optional[str] = None, **fetch_kwargs
) -> pandas.DataFrame:
    """返回长表（期 × 省）：一等奖省级分布及注数。

    仅部分玩法提供（ssq / qlc / kl8 的 content 字段），其余彩种返回空表。

    :param lottery_name: str, 彩种代码。
    :param records: list, 显式传入原始开奖记录（离线使用）；为 None 时联网拉取。
    :param if_cached: boolean, 启用本地 CSV 缓存与增量更新。
    :param cache_dir: str, optional, 缓存目录；None 时取环境变量或默认值。
    :param **fetch_kwargs: 透传给 load_history_data（timeout / max_retries / proxies 等）。
    :return: pandas.DataFrame, 长表（期 × 省）：一等奖省级分布及注数。
    """
    _check_game(lottery_name)
    return _cached_table(lottery_name, "province", _build_province, if_cached, cache_dir, records, fetch_kwargs)
