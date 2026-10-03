# coding=utf-8
# author=Ulion.Tse

"""历史号码统计分析：出现次数、频率、当前遗漏、最大遗漏与平均遗漏。

!!! note "仅供观察与娱乐参考"

    以下统计描述的是历史分布。彩票开奖为独立随机事件，历史统计不改变
    任何号码下一期的真实中奖概率。
"""

from typing import Optional, cast

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
    rows = []
    for side in (side for side in ("red", "blue") if side in pool):
        lo, hi = pool[side]
        for number in range(lo, hi + 1):
            count, current_miss, max_miss, miss_sum = 0, 0, 0, 0
            for _, row in history.iterrows():
                if number in _split(row[f"lottery_{side}"]):
                    count += 1
                    miss_sum += current_miss
                    max_miss = max(max_miss, current_miss)
                    current_miss = 0
                else:
                    current_miss += 1
            max_miss = max(max_miss, current_miss)  # 从未出现的号码：最大遗漏 = 总期数
            rows.append(
                {
                    "lottery_name": lottery_name,
                    "side": side,
                    "number": number,
                    "count": count,
                    "freq": count / len(history) if len(history) else 0.0,
                    "current_miss": current_miss,
                    "max_miss": max_miss,
                    "avg_miss": miss_sum / count if count else float("nan"),
                }
            )
    return pandas.DataFrame(rows)
