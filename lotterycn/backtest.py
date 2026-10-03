# coding=utf-8
# author=Ulion.Tse

"""策略回测：滚动窗口对比 random 基线。

!!! note "预期结论：所有策略与随机基线无差异"

    本模块把 predict.py 的免责声明变成一个可复现的实验：滚动地用前
    window 期历史驱动策略出票，与下一期真实开奖比对命中个数。
    任何"显著优于随机"的观察都应首先怀疑为过拟合或样本噪声。

用法：
    results = backtest(methods=('random', 'frequency'), lottery_name='ssq', window=100)
    print(backtest_summary(results))
"""

from typing import Optional

import pandas

from .analysis import _split
from .data import load_history_data
from .predict import load_predict_numbers
from .utils import LotteryError


def _hits(lottery_name: str, pred_reds: list, pred_blues: list, act_reds: list, act_blues: list) -> tuple:
    """按彩种计算命中个数：乐透/康乐类用集合交集，数字型按位比对。"""
    if lottery_name in ("3d", "pls", "plw", "qxc"):
        red_hits = sum(1 for a, b in zip(pred_reds, act_reds) if a == b)
        blue_hits = 1 if pred_blues and act_blues and pred_blues[0] == act_blues[0] else 0
        return red_hits, blue_hits
    return len(set(pred_reds) & set(act_reds)), len(set(pred_blues) & set(act_blues))


def backtest(
    methods: tuple[str, ...] = ("random",),
    lottery_name: str = "ssq",
    window: int = 100,
    trials: Optional[int] = None,
    history: Optional[pandas.DataFrame] = None,
    **fetch_kwargs,
) -> pandas.DataFrame:
    """滚动窗口回测：逐期评估各策略的中奖命中情况。

    :param methods: tuple[str, ...], 参与对比的策略名（见 predict.load_predict_numbers）。
    :param lottery_name: str, must in ('ssq', 'qlc', 'kl8', '3d', 'dlt', 'pls', 'plw', 'qxc').
    :param window: int, 每次出票使用的历史窗口期数（不含评估期）。
    :param trials: int, 每个策略最多评估的期数；None 表示评估全部可评估期。
    :param history: pandas.DataFrame, 显式注入历史数据（离线使用）；为 None 时联网拉取。
    :param **fetch_kwargs: 仅 history 为 None 时生效，透传给 load_history_data（如 if_cached）。
    :return: pandas.DataFrame
        columns: method, lottery_order, lottery_date, red_hits, blue_hits
    """
    if lottery_name not in ("ssq", "qlc", "kl8", "3d", "dlt", "pls", "plw", "qxc"):
        raise LotteryError(f"unsupported lottery name {lottery_name!r}")
    if window < 1:
        raise LotteryError(f"window ({window}) must be >= 1")
    if history is None:
        from typing import cast

        history = cast(pandas.DataFrame, load_history_data(lottery_name=lottery_name, **fetch_kwargs))
    history = history.sort_values(by=["lottery_date", "lottery_order"]).reset_index(drop=True)
    if window >= len(history):
        raise LotteryError(f"window ({window}) must be smaller than history length ({len(history)})")

    rows = []
    for method in methods:
        evaluated = 0
        for i in range(window, len(history)):
            if trials is not None and evaluated >= trials:
                break
            train = history.iloc[max(0, i - window) : i]
            actual = history.iloc[i]
            try:
                ticket = load_predict_numbers(
                    lottery_name, method=method, amount=1, history=train, **fetch_kwargs
                ).iloc[0]
            except LotteryError:
                continue  # 样本不足等策略性跳过
            red_hits, blue_hits = _hits(
                lottery_name,
                _split(ticket["lottery_red"]),
                _split(ticket["lottery_blue"]) if ticket["lottery_blue"] else [],
                _split(actual["lottery_red"]),
                _split(actual["lottery_blue"]) if actual["lottery_blue"] else [],
            )
            rows.append(
                {
                    "method": method,
                    "lottery_order": actual["lottery_order"],
                    "lottery_date": actual["lottery_date"],
                    "red_hits": red_hits,
                    "blue_hits": blue_hits,
                }
            )
            evaluated += 1
    return pandas.DataFrame(rows)


def backtest_summary(results: pandas.DataFrame) -> pandas.DataFrame:
    """汇总回测明细：各策略的平均命中个数与评估期数，供与 random 基线对比。

    :param results: pandas.DataFrame, backtest 返回的明细表（method / red_hits / blue_hits 等列）。
    :return: pandas.DataFrame
        columns: method, trials, avg_red_hits, avg_blue_hits，按 method 排序；results 为空时返回同结构空表。
    """
    if results.empty:
        return pandas.DataFrame(columns=["method", "trials", "avg_red_hits", "avg_blue_hits"])
    summary = results.groupby("method", as_index=False).agg(
        trials=("method", "size"),
        avg_red_hits=("red_hits", "mean"),
        avg_blue_hits=("blue_hits", "mean"),
    )
    return summary.sort_values("method").reset_index(drop=True)
