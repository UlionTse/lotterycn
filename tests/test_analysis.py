# coding=utf-8
# author=Ulion.Tse

import math

import pandas
import pytest

from lotterycn.analysis import load_number_statistics
from lotterycn.utils import LotteryError

CL_COLS = ["lottery_name", "lottery_order", "lottery_date", "lottery_red", "lottery_blue"]


def _history(rows):
    return pandas.DataFrame(rows, columns=CL_COLS)


SSQ_HISTORY = _history(
    [
        ["ssq", "2026001", "2026-01-01", "01,02,03,04,05,06", "07"],
        ["ssq", "2026002", "2026-01-03", "07,08,09,10,11,12", "07"],
        ["ssq", "2026003", "2026-01-05", "01,03,05,13,14,15", "13"],
    ]
)


def test_ssq_statistics():
    stats = load_number_statistics("ssq", history=SSQ_HISTORY)
    assert len(stats) == 33 + 16  # 红球与蓝球全池

    n01 = stats[(stats["side"] == "red") & (stats["number"] == 1)].iloc[0]
    assert n01["count"] == 2
    assert n01["freq"] == pytest.approx(2 / 3)
    assert n01["current_miss"] == 0
    assert n01["max_miss"] == 1
    assert n01["avg_miss"] == pytest.approx(0.5)  # 两次出现前遗漏 0 和 1

    n33 = stats[(stats["side"] == "red") & (stats["number"] == 33)].iloc[0]
    assert n33["count"] == 0
    assert n33["current_miss"] == 3
    assert n33["max_miss"] == 3
    assert math.isnan(n33["avg_miss"])

    b07 = stats[(stats["side"] == "blue") & (stats["number"] == 7)].iloc[0]
    assert b07["count"] == 2 and b07["current_miss"] == 1

    b13 = stats[(stats["side"] == "blue") & (stats["number"] == 13)].iloc[0]
    assert b13["count"] == 1 and b13["current_miss"] == 0


def test_digit_statistics_presence_semantics():
    # 数字型彩种按"期"统计：同一期重复出现的数字只计一次
    history = _history(
        [
            ["3d", "2026001", "2026-01-01", "1,1,2", ""],
            ["3d", "2026002", "2026-01-03", "2,3,4", ""],
        ]
    )
    stats = load_number_statistics("3d", history=history)
    assert len(stats) == 10  # 0-9

    n1 = stats[(stats["side"] == "red") & (stats["number"] == 1)].iloc[0]
    assert n1["count"] == 1 and n1["current_miss"] == 1
    n2 = stats[(stats["side"] == "red") & (stats["number"] == 2)].iloc[0]
    assert n2["count"] == 2 and n2["current_miss"] == 0


def test_unsorted_history_is_sorted_internally():
    shuffled = _history(
        [
            ["ssq", "2026003", "2026-01-05", "01,03,05,13,14,15", "13"],
            ["ssq", "2026001", "2026-01-01", "01,02,03,04,05,06", "07"],
            ["ssq", "2026002", "2026-01-03", "07,08,09,10,11,12", "07"],
        ]
    )
    stats = load_number_statistics("ssq", history=shuffled)
    n01 = stats[(stats["side"] == "red") & (stats["number"] == 1)].iloc[0]
    # 若未按时间排序，01 的"当前遗漏"会误算为 2
    assert n01["current_miss"] == 0
    assert n01["max_miss"] == 1


def test_invalid_lottery_name_raises():
    with pytest.raises(LotteryError):
        load_number_statistics("abc", history=SSQ_HISTORY)
