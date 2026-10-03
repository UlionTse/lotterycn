# coding=utf-8
# author=Ulion.Tse

import pandas
import pytest

from lotterycn.predict import load_predict_numbers
from lotterycn.utils import LotteryError

CL_COLS = ["lottery_name", "lottery_order", "lottery_date", "lottery_red", "lottery_blue"]

# 手工构造、频率可手算的双色球历史：
# 红球 01 出现 4 次；02/03/04 各 2 次；05~18 各 1 次；19~33 为 0
# 蓝球 07 出现 2 次；08/09 各 1 次；其余为 0
SSQ_HISTORY = pandas.DataFrame(
    [
        ["ssq", "2026001", "2026-01-01", "01,02,03,04,05,06", "07"],
        ["ssq", "2026002", "2026-01-03", "01,02,03,07,08,09", "07"],
        ["ssq", "2026003", "2026-01-05", "01,04,10,11,12,13", "08"],
        ["ssq", "2026004", "2026-01-07", "01,14,15,16,17,18", "09"],
    ],
    columns=CL_COLS,
)

GAME_ROWS = {
    "ssq": ("01,02,03,04,05,06", "07"),
    "qlc": ("01,02,03,04,05,06,07", "08"),
    "kl8": ("01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20", ""),
    "3d": ("1,2,3", ""),
    "pls": ("4,5,6", ""),
    "plw": ("1,2,3,4,5", ""),
    "dlt": ("01,02,03,04,05", "01,02"),
    "qxc": ("1,2,3,4,5,6", "14"),
}


def _game_history(name, dates=("2026-01-01", "2026-01-03")):
    rows = []
    for i, date in enumerate(dates):
        red, blue = GAME_ROWS[name]
        rows.append([name, f"2026{i + 1:03d}", date, red, blue])
    return pandas.DataFrame(rows, columns=CL_COLS)


def test_random_predictor_shape():
    frame = load_predict_numbers("ssq", method="random", amount=3)
    assert len(frame) == 3
    assert (frame["method"] == "random").all()
    assert list(frame.columns) == CL_COLS + ["method"]
    for red, blue in zip(frame["lottery_red"], frame["lottery_blue"]):
        nums = [int(x) for x in red.split(",")]
        assert len(set(nums)) == 6 and all(1 <= n <= 33 for n in nums)
        assert 1 <= int(blue) <= 16


def test_frequency_hot_cold_deterministic():
    hot = load_predict_numbers("ssq", method="hot", amount=1, history=SSQ_HISTORY, explore_ratio=0)
    assert [int(x) for x in hot.iloc[0]["lottery_red"].split(",")] == [1, 2, 3, 4, 5, 6]
    assert hot.iloc[0]["lottery_blue"] == "07"  # 出现 2 次的最热蓝球
    assert (hot["method"] == "frequency").all()

    cold = load_predict_numbers("ssq", method="cold", amount=1, history=SSQ_HISTORY, explore_ratio=0)
    assert [int(x) for x in cold.iloc[0]["lottery_red"].split(",")] == [19, 20, 21, 22, 23, 24]
    assert cold.iloc[0]["lottery_blue"] == "01"  # 未出现过的蓝球，并列取最小号

    # 别名允许显式 mode 覆盖：hot 别名 + mode='cold' → 取冷号
    overridden = load_predict_numbers("ssq", method="hot", amount=1, history=SSQ_HISTORY, explore_ratio=0, mode="cold")
    assert [int(x) for x in overridden.iloc[0]["lottery_red"].split(",")] == [19, 20, 21, 22, 23, 24]


def test_frequency_sliding_window():
    # recent_n=1 时只看最近一期：hot top-6 = 最近一期开出的 6 个红球
    frame = load_predict_numbers("ssq", method="frequency", amount=1, history=SSQ_HISTORY, recent_n=1, explore_ratio=0)
    assert [int(x) for x in frame.iloc[0]["lottery_red"].split(",")] == [1, 14, 15, 16, 17, 18]


def test_kl8_frequency_hot_matches_draw():
    history = _game_history("kl8")
    frame = load_predict_numbers("kl8", method="frequency", amount=1, history=history, explore_ratio=0)
    drawn = sorted(int(x) for x in GAME_ROWS["kl8"][0].split(","))
    picked = [int(x) for x in frame.iloc[0]["lottery_red"].split(",")]
    assert picked == drawn  # 一期窗口内 hot top-20 恰为开出的 20 个号
    assert frame.iloc[0]["lottery_blue"] == ""


def test_markov_predictor():
    frame = load_predict_numbers("ssq", method="markov", amount=2, history=SSQ_HISTORY)
    assert len(frame) == 2 and (frame["method"] == "markov").all()
    for red in frame["lottery_red"]:
        nums = [int(x) for x in red.split(",")]
        assert len(set(nums)) == 6 and all(1 <= n <= 33 for n in nums)


def test_filter_predictor():
    frame = load_predict_numbers(
        "ssq", method="filter", amount=3, history=SSQ_HISTORY, sum_range=(90, 120), odd_range=(2, 4)
    )
    assert len(frame) == 3
    for red in frame["lottery_red"]:
        nums = [int(x) for x in red.split(",")]
        assert 90 <= sum(nums) <= 120
        assert 2 <= sum(1 for n in nums if n % 2) <= 4


def test_all_games_all_methods():
    for name, (red, blue) in GAME_ROWS.items():
        history = _game_history(name)
        for method in ("random", "frequency", "markov", "filter"):
            frame = load_predict_numbers(name, method=method, amount=1, history=history)
            row = frame.iloc[0]
            assert row["lottery_red"] != "", (name, method)
            assert row["method"] == method, (name, method)
            if blue:
                assert row["lottery_blue"] != "", (name, method)
            else:
                assert row["lottery_blue"] == "", (name, method)


OMISSION_HISTORY = (
    pandas.DataFrame(
        [
            [
                ["ssq", f"202600{i + 1}", "2026-01-0{1}".replace("{1}", str(i + 1)), "01,02,03,04,05,06", "07"]
                if i < 3
                else ["ssq", f"202600{i + 1}", f"2026-01-{i + 1:02d}", "07,08,09,10,11,12", "07"]
                for i in range(8)
            ][j]
        ]
        for j in range(0)
    )
    if False
    else pandas.DataFrame(
        [
            ["ssq", "2026001", "2026-01-01", "01,02,03,04,05,06", "07"],
            ["ssq", "2026002", "2026-01-02", "01,02,03,04,05,06", "07"],
            ["ssq", "2026003", "2026-01-03", "01,02,03,04,05,06", "07"],
            ["ssq", "2026004", "2026-01-04", "07,08,09,10,11,12", "07"],
            ["ssq", "2026005", "2026-01-05", "07,08,09,10,11,12", "07"],
            ["ssq", "2026006", "2026-01-06", "07,08,09,10,11,12", "07"],
            ["ssq", "2026007", "2026-01-07", "07,08,09,10,11,12", "07"],
            ["ssq", "2026008", "2026-01-08", "07,08,09,10,11,12", "07"],
        ],
        columns=CL_COLS,
    )
)


def test_omission_chase():
    # 01~06 连热 3 期后连续 5 期未出：current=5、avg=0 → score=5/1 最高
    frame = load_predict_numbers("ssq", method="omission", amount=1, history=OMISSION_HISTORY, explore_ratio=0)
    assert [int(x) for x in frame.iloc[0]["lottery_red"].split(",")] == [1, 2, 3, 4, 5, 6]
    assert (frame["method"] == "omission").all()


def test_deviation_hot_cold():
    hot = load_predict_numbers("ssq", method="deviation", amount=1, history=SSQ_HISTORY, explore_ratio=0)
    # 01 出现 4 次，正偏离最大；出现 0 次的 19~33 偏离大于出现 1 次的号码
    assert [int(x) for x in hot.iloc[0]["lottery_red"].split(",")] == [1, 2, 3, 4, 19, 20]
    cold = load_predict_numbers("ssq", method="deviation", amount=1, history=SSQ_HISTORY, explore_ratio=0, side="cold")
    # 出现 1 次的号码负偏离最大（出现 0 次的偏离反而略高）
    assert [int(x) for x in cold.iloc[0]["lottery_red"].split(",")] == [5, 6, 7, 8, 9, 10]


def test_repeat_neighbor():
    frame = load_predict_numbers("ssq", method="repeat", amount=1, history=SSQ_HISTORY, explore_ratio=0)
    # 14 重号(2)+邻号(1)+斜连(1)=4 分最高；01 重号(2)+斜连(1)=3
    picks = [int(x) for x in frame.iloc[0]["lottery_red"].split(",")]
    assert picks == [1, 14, 15, 16, 17, 18]


def test_trend_band():
    frame = load_predict_numbers("ssq", method="trend", amount=3, history=SSQ_HISTORY, k_sigma=2.0)
    assert len(frame) == 3
    # SSQ_HISTORY 和值均值 45.75、k_sigma=2 → 带内上界约 91.6，全部命中带内
    for red in frame["lottery_red"]:
        assert sum(int(x) for x in red.split(",")) <= 91.6


def test_trend_too_narrow_raises():
    with pytest.raises(LotteryError):
        predictor = load_predict_numbers(
            "ssq", method="trend", amount=1, history=SSQ_HISTORY, k_sigma=0.01, max_trials=5
        )
        predictor if False else None


def test_tail_strategy():
    frame = load_predict_numbers("ssq", method="tail", amount=1, history=SSQ_HISTORY, explore_ratio=0)
    # 尾数 1、2 最热（tail_count 自动推导为 2），全部选号尾数 ∈ {1, 2}
    for red in frame["lottery_red"]:
        assert {int(x) % 10 for x in red.split(",")} <= {1, 2}


def test_markov2_strategy():
    frame = load_predict_numbers("ssq", method="markov2", amount=1, history=SSQ_HISTORY)
    assert (frame["method"] == "markov2").all()
    for red in frame["lottery_red"]:
        nums = [int(x) for x in red.split(",")]
        assert len(set(nums)) == 6 and all(1 <= n <= 33 for n in nums)
    with pytest.raises(LotteryError):
        load_predict_numbers("ssq", method="markov2", history=SSQ_HISTORY.iloc[:1])


def test_ensemble_votes():
    frame = load_predict_numbers("ssq", method="ensemble", amount=1, history=SSQ_HISTORY)
    assert (frame["method"] == "ensemble").all()
    nums = [int(x) for x in frame.iloc[0]["lottery_red"].split(",")]
    assert len(set(nums)) == 6 and all(1 <= n <= 33 for n in nums)
    with pytest.raises(LotteryError):
        load_predict_numbers("ssq", method="ensemble", history=SSQ_HISTORY, members=("frequency", "ensemble"))
    with pytest.raises(LotteryError):
        load_predict_numbers("ssq", method="ensemble", history=SSQ_HISTORY, votes_min=0)


def test_filter_shape_constraints():
    frame = load_predict_numbers(
        "ssq",
        method="filter",
        amount=2,
        history=SSQ_HISTORY,
        prime_range=(2, 3),
        zone_ratio=(2, 2, 2),
        mod3_range=(1, 2, 3),
        ac_range=(4, 9),
        consecutive_range=(0, 1),
        exclude_numbers={1, 2, 3},
    )
    assert len(frame) == 2
    for red in frame["lottery_red"]:
        nums = [int(x) for x in red.split(",")]
        primes = sum(1 for n in nums if n in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31))
        assert 2 <= primes <= 3
        assert not {1, 2, 3} & set(nums)
        uniq = sorted(set(nums))
        assert sum(1 for a, b in zip(uniq, uniq[1:]) if b - a == 1) <= 1
        zones = [0, 0, 0]
        for n in nums:
            zones[min(2, (n - 1) * 3 // 33)] += 1
        assert tuple(zones) == (2, 2, 2)
        routes = [0, 0, 0]
        for n in nums:
            routes[n % 3] += 1
        assert tuple(routes) == (1, 2, 3)


def test_unknown_strategy_raises():
    with pytest.raises(LotteryError):
        load_predict_numbers("ssq", method="astro", history=SSQ_HISTORY)


def test_invalid_inputs_raise():
    with pytest.raises(LotteryError):
        load_predict_numbers("ssq", method="nope", history=SSQ_HISTORY)
    with pytest.raises(LotteryError):
        load_predict_numbers("ssq", method="frequency", history=SSQ_HISTORY, mode="warm")
    with pytest.raises(LotteryError):
        load_predict_numbers("ssq", method="markov", history=SSQ_HISTORY.iloc[:1])  # 马尔可夫至少 2 期
    with pytest.raises(LotteryError):
        load_predict_numbers("abc", method="random")
