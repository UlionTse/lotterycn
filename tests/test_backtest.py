# coding=utf-8
# author=Ulion.Tse

import random

import pandas
import pytest

from lotterycn.backtest import backtest, backtest_summary
from lotterycn.utils import LotteryError

CL_COLS = ["lottery_name", "lottery_order", "lottery_date", "lottery_red", "lottery_blue"]


def _history(n=30):
    rows = []
    for i in range(n):
        reds = sorted(random.Random(i).sample(range(1, 34), 6))
        rows.append(
            ["ssq", f"2026{i + 1:04d}", f"2026-01-{i + 1:02d}", ",".join(f"{x:02d}" for x in reds), f"{i % 16 + 1:02d}"]
        )
    return pandas.DataFrame(rows, columns=CL_COLS)


def test_backtest_shape():
    results = backtest(methods=("random", "frequency"), lottery_name="ssq", window=10, history=_history())
    assert len(results) == 40  # 2 策略 × 20 个可评估期
    assert list(results.columns) == ["method", "lottery_order", "lottery_date", "red_hits", "blue_hits"]
    assert results["red_hits"].between(0, 6).all()


def test_backtest_summary():
    results = backtest(methods=("random", "frequency"), lottery_name="ssq", window=10, history=_history())
    summary = backtest_summary(results)
    assert len(summary) == 2
    assert list(summary.columns) == ["method", "trials", "avg_red_hits", "avg_blue_hits"]
    assert (summary["trials"] == 20).all()
    # 教学核心断言：各策略平均命中彼此接近（无预测力）
    assert summary["avg_red_hits"].std() < 1.0


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
