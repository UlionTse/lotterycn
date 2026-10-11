# coding=utf-8
# author=Ulion.Tse

import pandas
import pytest

from lotterycn.analysis import NUMBER_POOLS
from lotterycn.data import GAME_ZH_NAMES
from lotterycn.predict import (
    MarkovPredictor,
    _ac_value,
    _consecutive_pairs,
    _mod3_counts,
    _zone_counts,
    load_predict_numbers,
)
from lotterycn.utils import LotteryError

CL_COLS = [
    "lottery_name",
    "lottery_zh_name",
    "lottery_order",
    "lottery_date",
    "lottery_red",
    "lottery_blue",
]

# 手工构造、频率可手算的双色球历史：
# 红球 01 出现 4 次；02/03/04 各 2 次；05~18 各 1 次；19~33 为 0
# 蓝球 07 出现 2 次；08/09 各 1 次；其余为 0
SSQ_HISTORY = pandas.DataFrame(
    [
        ["ssq", "双色球", "2026001", "2026-01-01", "01,02,03,04,05,06", "07"],
        ["ssq", "双色球", "2026002", "2026-01-03", "01,02,03,07,08,09", "07"],
        ["ssq", "双色球", "2026003", "2026-01-05", "01,04,10,11,12,13", "08"],
        ["ssq", "双色球", "2026004", "2026-01-07", "01,14,15,16,17,18", "09"],
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
        rows.append([name, GAME_ZH_NAMES.get(name, ""), f"2026{i + 1:03d}", date, red, blue])
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


def test_markov_transition_counts_match_reference():
    # 手算可验证：号码 01 出现序列为 [出, 未出, 出, 未出]
    # 相邻对 (出,未出)×2、(未出,出)×1 → Laplace 平滑后 [[1, 2], [3, 1]]
    frame = pandas.DataFrame(
        [
            ["ssq", "双色球", "2026001", "2026-01-01", "01,02,03,04,05,06", "07"],
            ["ssq", "双色球", "2026002", "2026-01-02", "08,09,10,11,12,13", "07"],
            ["ssq", "双色球", "2026003", "2026-01-03", "01,14,15,16,17,18", "08"],
            ["ssq", "双色球", "2026004", "2026-01-04", "19,20,21,22,23,24", "09"],
        ],
        columns=CL_COLS,
    )
    predictor = MarkovPredictor(lottery_name="ssq", history=frame)
    assert predictor.transition["red"][1] == [[1, 2], [3, 1]]
    # 从未出现的号码 33：4 期均为未出现 → (未出,未出)×3，Laplace 平滑后 [[4, 1], [1, 1]]
    assert predictor.transition["red"][33] == [[4, 1], [1, 1]]


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
                [
                    "ssq",
                    "双色球",
                    f"202600{i + 1}",
                    "2026-01-0{1}".replace("{1}", str(i + 1)),
                    "01,02,03,04,05,06",
                    "07",
                ]
                if i < 3
                else ["ssq", "双色球", f"202600{i + 1}", f"2026-01-{i + 1:02d}", "07,08,09,10,11,12", "07"]
                for i in range(8)
            ][j]
        ]
        for j in range(0)
    )
    if False
    else pandas.DataFrame(
        [
            ["ssq", "双色球", "2026001", "2026-01-01", "01,02,03,04,05,06", "07"],
            ["ssq", "双色球", "2026002", "2026-01-02", "01,02,03,04,05,06", "07"],
            ["ssq", "双色球", "2026003", "2026-01-03", "01,02,03,04,05,06", "07"],
            ["ssq", "双色球", "2026004", "2026-01-04", "07,08,09,10,11,12", "07"],
            ["ssq", "双色球", "2026005", "2026-01-05", "07,08,09,10,11,12", "07"],
            ["ssq", "双色球", "2026006", "2026-01-06", "07,08,09,10,11,12", "07"],
            ["ssq", "双色球", "2026007", "2026-01-07", "07,08,09,10,11,12", "07"],
            ["ssq", "双色球", "2026008", "2026-01-08", "07,08,09,10,11,12", "07"],
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


def test_ac_value_definition():
    # AC 值 = 两两差值的不同个数 - (号码个数 - 1)
    assert _ac_value([1, 2, 6, 13, 27, 33]) == 10  # 15 个互异差值，6 个号的理论最大值
    assert _ac_value([1, 2, 3, 4, 5, 6]) == 0  # 全连号：差值仅 {1..5} 共 5 个
    assert _ac_value([3, 3, 3]) == 0  # 去重后不足 2 个号码
    assert _ac_value([1, 33]) == 0  # 仅 1 个差值：1 - (2 - 1) = 0


def test_consecutive_pairs_definition():
    assert _consecutive_pairs([1, 2, 6, 13, 27, 33]) == 1
    assert _consecutive_pairs([1, 2, 3, 4, 5, 6]) == 5
    assert _consecutive_pairs([1, 3, 5, 7]) == 0
    assert _consecutive_pairs([3, 2, 2, 1]) == 2  # 先去重排序：1,2,3 → 两对


def test_mod3_counts_definition():
    # 012 路：号码 % 3 的计数（6,27,33 余 0；1,13 余 1；2 余 2）
    assert _mod3_counts([1, 2, 6, 13, 27, 33]) == (3, 2, 1)
    assert _mod3_counts([3, 6, 9]) == (3, 0, 0)


def test_zone_counts_boundaries():
    # 三区比分界与 docs/strategies「Filter 形态指标口径」表一致，锁定边界号的归属
    assert _zone_counts([1, 5, 12, 18, 27, 33], NUMBER_POOLS["ssq"]) == (2, 2, 2)
    # ssq 11/12 与 22/23 是一、二区与二、三区的分界
    assert _zone_counts([11, 12, 22, 23, 24, 25], NUMBER_POOLS["ssq"]) == (1, 2, 3)
    # kl8 为 27/27/26 分界：27 属一区，28/54 属二区，55 起属三区
    assert _zone_counts([27, 28, 54, 55, 56, 57], NUMBER_POOLS["kl8"]) == (1, 2, 3)
    # dlt 前区为 12/12/11 分界：12 属一区，13/24 属二区，25 起属三区
    assert _zone_counts([12, 13, 24, 25, 26, 27], NUMBER_POOLS["dlt"]) == (1, 2, 3)
    # qlc 均匀三等分：10 属一区，11/20 属二区，21 起属三区
    assert _zone_counts([10, 11, 20, 21, 22, 23], NUMBER_POOLS["qlc"]) == (1, 2, 3)
    # 数字型 0-9 分界为 0-3 / 4-6 / 7-9
    assert _zone_counts([0, 3, 4, 6, 7, 9], NUMBER_POOLS["3d"]) == (2, 2, 2)


def test_invalid_inputs_raise():
    with pytest.raises(LotteryError):
        load_predict_numbers("ssq", method="nope", history=SSQ_HISTORY)
    with pytest.raises(LotteryError):
        load_predict_numbers("ssq", method="frequency", history=SSQ_HISTORY, mode="warm")
    with pytest.raises(LotteryError):
        load_predict_numbers("ssq", method="markov", history=SSQ_HISTORY.iloc[:1])  # 马尔可夫至少 2 期
    with pytest.raises(LotteryError):
        load_predict_numbers("abc", method="random")
