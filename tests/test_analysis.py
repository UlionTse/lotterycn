# coding=utf-8
# author=Ulion.Tse

import math
import random

import pandas
import pytest

from lotterycn.analysis import load_number_statistics
from lotterycn.utils import LotteryError

CL_COLS = [
    "lottery_name",
    "lottery_zh_name",
    "lottery_order",
    "lottery_date",
    "lottery_red",
    "lottery_blue",
]


def _history(rows):
    return pandas.DataFrame(rows, columns=CL_COLS)


def _reference_side_stats(texts, lo, hi):
    """纯 Python 参考实现（逐号码 × 逐期），用于对拍向量化实现。"""
    out = {}
    for number in range(lo, hi + 1):
        count, current, max_miss, miss_sum = 0, 0, 0, 0
        for text in texts:
            drawn = [int(x) for x in str(text).split(",") if str(x).strip() != ""] if pandas.notna(text) else []
            if number in drawn:
                count += 1
                miss_sum += current
                max_miss = max(max_miss, current)
                current = 0
            else:
                current += 1
        max_miss = max(max_miss, current)
        out[number] = (count, current, max_miss, miss_sum / count if count else float("nan"))
    return out


SSQ_HISTORY = _history(
    [
        ["ssq", "双色球", "2026001", "2026-01-01", "01,02,03,04,05,06", "07"],
        ["ssq", "双色球", "2026002", "2026-01-03", "07,08,09,10,11,12", "07"],
        ["ssq", "双色球", "2026003", "2026-01-05", "01,03,05,13,14,15", "13"],
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
            ["3d", "福彩3D", "2026001", "2026-01-01", "1,1,2", ""],
            ["3d", "福彩3D", "2026002", "2026-01-03", "2,3,4", ""],
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
            ["ssq", "双色球", "2026003", "2026-01-05", "01,03,05,13,14,15", "13"],
            ["ssq", "双色球", "2026001", "2026-01-01", "01,02,03,04,05,06", "07"],
            ["ssq", "双色球", "2026002", "2026-01-03", "07,08,09,10,11,12", "07"],
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


def test_statistics_matches_reference_implementation():
    # 固定种子合成 300 期 ssq 历史：向量化实现必须与纯 Python 参考实现逐列一致
    random.seed(2026)
    red_texts = [",".join(f"{n:02d}" for n in random.sample(range(1, 34), 6)) for _ in range(300)]
    blue_texts = [f"{random.randint(1, 16):02d}" for _ in range(300)]
    history = _history(
        [
            ["ssq", "双色球", f"{i:06d}", "2026-01-01", red, blue]
            for i, (red, blue) in enumerate(zip(red_texts, blue_texts))
        ]
    )

    stats = load_number_statistics("ssq", history=history)
    red = stats[stats["side"] == "red"].set_index("number")
    blue = stats[stats["side"] == "blue"].set_index("number")
    for side_df, texts, lo, hi in ((red, red_texts, 1, 33), (blue, blue_texts, 1, 16)):
        for number, (count, current, max_miss, avg) in _reference_side_stats(texts, lo, hi).items():
            row = side_df.loc[number]
            assert row["count"] == count, (side_df.index.name, number)
            assert row["current_miss"] == current
            assert row["max_miss"] == max_miss
            if math.isnan(avg):
                assert math.isnan(row["avg_miss"])
            else:
                assert row["avg_miss"] == pytest.approx(avg)


def test_empty_history_statistics():
    stats = load_number_statistics("ssq", history=_history([]))
    assert len(stats) == 33 + 16
    assert (stats["count"] == 0).all()
    assert (stats["freq"] == 0.0).all()
    assert (stats["current_miss"] == 0).all()
    assert (stats["max_miss"] == 0).all()
    assert stats["avg_miss"].isna().all()
