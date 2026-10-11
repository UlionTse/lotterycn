# coding=utf-8
# author=Ulion.Tse

"""历史号码统计分析：出现次数、频率、当前遗漏、最大遗漏与平均遗漏。

!!! note "仅供观察与娱乐参考"

    以下统计描述的是历史分布。彩票开奖为独立随机事件，历史统计不改变
    任何号码下一期的真实中奖概率。
"""

from typing import Optional, cast

import numpy
import pandas

from .data import load_history_data
from .utils import LotteryError

# 各彩种号码池（与 config.py 中的角色定义保持一致）
NUMBER_POOLS: dict[str, dict] = {
    "ssq": {"red": (1, 33), "blue": (1, 16)},
    "qlc": {"red": (1, 30), "blue": (1, 30)},
    "kl8": {"red": (1, 80)},
    "3d": {"red": (0, 9), "positional": True},
    "pls": {"red": (0, 9), "positional": True},
    "plw": {"red": (0, 9), "positional": True},
    "qxc": {"red": (0, 9), "positional": True, "blue": (0, 14)},
    "dlt": {"red": (1, 35), "blue": (1, 12)},
}


def _split(text) -> list:
    if text is None or (not isinstance(text, (list, tuple)) and pandas.isna(text)):
        return []
    if isinstance(text, (list, tuple)):
        return [int(x) for x in text]
    return [int(x) for x in str(text).split(",") if str(x).strip() != ""]


def _normalize_draw_text(value) -> str:
    """把开奖单元格规整为 '1,2,3' 形式的字符串（NaN/空值 → ''，列表 → 逗号串）。"""
    if value is None or (not isinstance(value, (list, tuple)) and pandas.isna(value)):
        return ""
    if isinstance(value, (list, tuple)):
        return ",".join(str(int(x)) for x in value)
    return str(value)


def _occurrence_matrix(frame: pandas.DataFrame, column: str, lo: int, hi: int) -> numpy.ndarray:
    """按期出现矩阵 (期数 × 号码数)：同一期重复出现的号码只计一次。

    字符串列一次性向量化解析（兼容 pandas>=2.3.3），空值/非数值 token 计为未出现，
    与 `_split` 的按期去重口径一致。
    """
    texts = frame[column]
    if texts.dtype == object:
        texts = pandas.Series([_normalize_draw_text(v) for v in texts], index=texts.index, dtype="string")
    else:
        texts = texts.astype("string").fillna("")
    tokens = texts.str.split(",", expand=True)
    values = tokens.apply(pandas.to_numeric, errors="coerce").to_numpy(dtype=float)
    if values.size == 0:
        return numpy.zeros((len(frame), hi - lo + 1), dtype=bool)
    numbers = numpy.arange(lo, hi + 1)
    return (values[:, None, :] == numbers[None, :, None]).any(axis=2)


def _miss_statistics(hits: numpy.ndarray) -> tuple:
    """由出现矩阵单趟扫描出逐号码的 count / current_miss / max_miss / miss_sum。

    每期一次 numpy 向量更新（跨号码并行），miss_sum 为各次出现前的遗漏总和，
    用于计算 avg_miss；从未出现的号码 max_miss = 总期数、avg_miss = NaN。
    """
    count = hits.sum(axis=0)
    current = numpy.zeros(hits.shape[1], dtype=int)
    max_miss = numpy.zeros(hits.shape[1], dtype=int)
    miss_sum = numpy.zeros(hits.shape[1], dtype=int)
    for row in hits:
        miss_sum += current * row
        max_miss = numpy.maximum(max_miss, numpy.where(row, current, 0))
        current = numpy.where(row, 0, current + 1)
    max_miss = numpy.maximum(max_miss, current)
    return count, current, max_miss, miss_sum


def load_number_statistics(
    lottery_name: str, history: Optional[pandas.DataFrame] = None, **fetch_kwargs
) -> pandas.DataFrame:
    """返回各彩种每个号码的出现统计。

    :param lottery_name: str, must in ('ssq', 'qlc', 'kl8', '3d', 'dlt', 'pls', 'plw', 'qxc').
    :param history: pandas.DataFrame, 显式传入历史开奖数据（离线使用）；为 None 时联网拉取。
    :keyword **fetch_kwargs: 仅 history 为 None 时生效，透传给 load_history_data（如 if_cached）。
    :return: pandas.DataFrame
        columns: lottery_name, side, number, count, freq, current_miss, max_miss, avg_miss。
        统计口径为"按期出现"：同一期重复出现的数字（数字型彩种）只计一次；
        avg_miss 为各次出现前的平均遗漏期数，从未出现时为 NaN。
    """
    if lottery_name not in NUMBER_POOLS:
        raise LotteryError(f"unsupported lottery name {lottery_name!r}, must be one of {sorted(NUMBER_POOLS)}")
    if history is None:
        history = cast(pandas.DataFrame, load_history_data(lottery_name=lottery_name, **fetch_kwargs))
    history = history.sort_values(by=["lottery_date", "lottery_order"]).reset_index(drop=True)

    pool = NUMBER_POOLS[lottery_name]
    total = len(history)
    rows = []
    for side in (side for side in ("red", "blue") if side in pool):
        lo, hi = pool[side]
        hits = _occurrence_matrix(history, f"lottery_{side}", lo, hi)
        counts, currents, max_misses, miss_sums = _miss_statistics(hits)
        for i, number in enumerate(range(lo, hi + 1)):
            count = int(counts[i])
            rows.append(
                {
                    "lottery_name": lottery_name,
                    "side": side,
                    "number": number,
                    "count": count,
                    "freq": count / total if total else 0.0,
                    "current_miss": int(currents[i]),
                    "max_miss": int(max_misses[i]),
                    "avg_miss": miss_sums[i] / count if count else float("nan"),
                }
            )
    return pandas.DataFrame(rows)
