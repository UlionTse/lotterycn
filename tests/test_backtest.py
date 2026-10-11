# coding=utf-8
# author=Ulion.Tse

import random

import pandas
import pytest

from lotterycn.backtest import backtest, backtest_summary
from lotterycn.utils import LotteryError

CL_COLS = [
    "lottery_name",
    "lottery_zh_name",
    "lottery_order",
    "lottery_date",
    "lottery_red",
    "lottery_blue",
]


def _history(n=30):
    rows = []
    for i in range(n):
        reds = sorted(random.Random(i).sample(range(1, 34), 6))
        rows.append(
            [
                "ssq",
                "双色球",
                f"2026{i + 1:04d}",
                f"2026-01-{i + 1:02d}",
                ",".join(f"{x:02d}" for x in reds),
                f"{i % 16 + 1:02d}",
            ]
        )
    return pandas.DataFrame(rows, columns=CL_COLS)


def test_backtest_shape():
    results = backtest(methods=("random", "frequency"), lottery_name="ssq", window=10, history=_history())
    assert len(results) == 40  # 2 策略 × 20 个可评估期
    assert list(results.columns) == [
        "method",
        "lottery_name",
        "lottery_order",
        "lottery_date",
        "red_hits",
        "blue_hits",
    ]
    assert (results["lottery_name"] == "ssq").all()
    assert results["red_hits"].between(0, 6).all()


def test_backtest_summary():
    results = backtest(methods=("random", "frequency"), lottery_name="ssq", window=10, history=_history())
    summary = backtest_summary(results)
    assert len(summary) == 2
    assert list(summary.columns) == [
        "lottery_name",
        "method",
        "trials",
        "avg_red_hits",
        "avg_blue_hits",
        "avg_red_hit_rate",
        "avg_blue_hit_rate",
        "random_red_hit_rate",
        "random_blue_hit_rate",
    ]
    assert (summary["trials"] == 20).all()
    # 捕获率 = 平均命中 ÷ 每期开出球数（ssq 红 6 / 蓝 1）；理论值红 6/33 ≈ 0.18
    assert summary["avg_red_hit_rate"].between(0.1, 0.3).all()
    assert summary["avg_blue_hit_rate"].between(0.0, 0.2).all()
    # random 基线的实测捕获率广播到每行，供与策略并排对照
    random_row = summary[summary["method"] == "random"].iloc[0]
    assert (summary["random_red_hit_rate"] == random_row["avg_red_hit_rate"]).all()
    assert (summary["random_blue_hit_rate"] == random_row["avg_blue_hit_rate"]).all()


def test_summary_without_random_baseline():
    # 结果集不含 random 方法：基线捕获率两列为 NaN（docstring 已注明）
    results = backtest(methods=("hot",), lottery_name="ssq", window=10, history=_history())
    summary = backtest_summary(results)
    assert len(summary) == 1
    assert summary["random_red_hit_rate"].isna().all()
    assert summary["random_blue_hit_rate"].isna().all()


def test_summary_blue_rate_nan_for_kl8():
    # kl8 无蓝球：蓝捕获率全 NaN；红捕获率 = avg_red_hits ÷ 20（每期开出 20 个）
    rows = [
        {
            "method": "random",
            "lottery_name": "kl8",
            "lottery_order": str(i),
            "lottery_date": "2026-01-01",
            "red_hits": 5,
            "blue_hits": 0,
        }
        for i in range(10)
    ]
    summary = backtest_summary(pandas.DataFrame(rows))
    assert summary["avg_red_hit_rate"].iloc[0] == pytest.approx(5 / 20)
    assert summary["avg_blue_hit_rate"].isna().all()
    assert summary["random_red_hit_rate"].iloc[0] == summary["avg_red_hit_rate"].iloc[0]


def test_backtest_trials_limit():
    results = backtest(methods=("random",), lottery_name="ssq", window=10, trials=5, history=_history())
    assert len(results) == 5


def test_backtest_empty_summary():
    assert backtest_summary(pandas.DataFrame()).empty


def test_backtest_invalid_inputs():
    with pytest.raises(LotteryError):
        backtest(methods=("random",), lottery_name="ssq", window=30, history=_history(30))
    with pytest.raises(LotteryError):
        backtest(methods=("random",), lottery_name="abc", window=10, history=_history())
