# coding=utf-8
# author=Ulion.Tse

import pytest

from lotterycn.odds import load_dlt_compound_expectation, load_prize_expectation, load_prize_odds
from lotterycn.utils import LotteryError

# 以下基准值均来自官方规则独立验算（见 config.py 中的规则来源）
SSQ_TOTAL = 17_721_088  # C(33,6) * 16
DLT_TOTAL = 21_425_712  # C(35,5) * C(12,2)
QXC_TOTAL = 15_000_000  # 10^6 * 15
QLC_TOTAL = 2_035_800  # C(30,7)
QLC_WAYS = (1, 7, 154, 462, 4851, 8085, 53900)  # 一~七等奖命中组合数
QXC_WAYS = (1, 14, 54, 1971, 31590, 1188270)  # 一~六等奖命中组合数


def test_ssq_odds():
    odds = load_prize_odds("ssq")
    assert len(odds) == 6
    assert odds.iloc[0]["winning_combinations"] == 1
    assert odds.iloc[0]["total_combinations"] == SSQ_TOTAL
    assert odds.iloc[-1]["winning_combinations"] == 1_043_640
    assert odds["prize_amount"].tolist()[:3] == [5_000_000.0, 150_000.0, 3_000.0]
    assert odds.iloc[2]["prize_type"] == "固定"


def test_qlc_odds_seven_levels():
    odds = load_prize_odds("qlc")
    assert len(odds) == 7
    assert odds["winning_combinations"].tolist() == list(QLC_WAYS)
    assert odds.iloc[0]["total_combinations"] == QLC_TOTAL


def test_dlt_odds_current_rule():
    odds = load_prize_odds("dlt")
    assert len(odds) == 7  # 现行七个奖级
    assert odds.iloc[0]["total_combinations"] == DLT_TOTAL
    assert odds.iloc[2]["winning_combinations"] == 195  # 三等奖 5+0 / 4+2
    assert odds.iloc[2]["prize_amount"] == 5000.0  # 奖池低于8亿档
    assert load_prize_odds("dlt", if_pool_over_800m=True).iloc[2]["prize_amount"] == 6666.0


def test_qxc_odds():
    odds = load_prize_odds("qxc")
    assert len(odds) == 6
    assert odds["winning_combinations"].tolist() == list(QXC_WAYS)
    assert odds.iloc[0]["total_combinations"] == QXC_TOTAL


def test_kl8_odds():
    odds = load_prize_odds("kl8", pick=10)
    pick10 = odds[odds["play_type"] == "选10"]
    hit10 = pick10[pick10["prize_level"] == "选10中10"].iloc[0]
    assert hit10["winning_combinations"] == 184_756  # C(20,10)
    assert hit10["total_combinations"] == 1_646_492_110_120  # C(80,10)
    miss = pick10[pick10["prize_level"] == "选10全不中"].iloc[0]
    assert miss["prize_amount"] == 2.0

    pick1 = load_prize_odds("kl8", pick=1)
    assert pick1.iloc[0]["winning_probability"] == pytest.approx(0.25)  # 20/80

    all_odds = load_prize_odds("kl8")
    assert len(all_odds["play_type"].unique()) == 10


def test_digit_odds():
    odds = load_prize_odds("3d")
    assert odds["winning_probability"].tolist() == [0.001, 0.003, 0.006]
    exp = load_prize_expectation("3d")
    direct = exp[exp["play_type"] == "单选"].iloc[0]
    assert direct["expected_value_yuan"] == pytest.approx(1.04)  # 1040 * 1/1000
    assert direct["return_rate"] == pytest.approx(0.52)

    plw = load_prize_odds("plw")
    assert plw.iloc[0]["total_combinations"] == 100_000
    assert plw.iloc[0]["prize_amount"] == 100_000.0


def test_probability_sums_within_one():
    for name in ("ssq", "qlc", "kl8", "3d", "dlt", "pls", "plw", "qxc"):
        odds = load_prize_odds(name)
        sums = odds.groupby("play_type")["winning_probability"].sum()
        assert ((sums > 0) & (sums <= 1)).all(), name


def test_expectation_bounded():
    for name in ("ssq", "qlc", "kl8", "3d", "dlt", "pls", "plw", "qxc"):
        exp = load_prize_expectation(name)
        assert ((exp["return_rate"] > 0) & (exp["return_rate"] < 1.2)).all(), name


def test_invalid_lottery_name_raises():
    with pytest.raises(LotteryError):
        load_prize_odds("abc")
    with pytest.raises(LotteryError):
        load_prize_odds("kl8", pick=11)


def test_dlt_add_bet_expectation():
    base = load_prize_expectation("dlt").iloc[0]
    add_bet = load_prize_expectation("dlt", if_add_bet=True).iloc[0]
    assert add_bet["bet_price_yuan"] == 3

    # E_追加 = 固定期望 + 0.8 × 浮动期望（环境变量覆盖后再按 80% 折算）
    odds = load_prize_odds("dlt")
    fixed = odds[odds["prize_type"] == "固定"].eval("winning_probability * prize_amount").sum()
    floating = base["expected_value_yuan"] - fixed
    assert add_bet["expected_value_yuan"] == pytest.approx(fixed + 0.8 * floating)
    assert add_bet["return_rate"] == pytest.approx(add_bet["expected_value_yuan"] / 3)

    add_bet_high = load_prize_expectation("dlt", if_add_bet=True, if_pool_over_800m=True).iloc[0]
    assert add_bet_high["expected_value_yuan"] > add_bet["expected_value_yuan"]


def test_dlt_compound_degenerates_to_single():
    # n_red=5, m_blue=2 即单式：注数 1、成本 2 元、期望与返奖率等于单式
    base = load_prize_expectation("dlt").iloc[0]
    compound = load_dlt_compound_expectation(5, 2).iloc[0]
    assert compound["total_bets"] == 1
    assert compound["cost_yuan"] == 2
    assert compound["expected_prize_yuan"] == pytest.approx(base["expected_value_yuan"])
    assert compound["return_rate"] == pytest.approx(base["return_rate"])


def test_dlt_compound_cost_and_linearity():
    # C(6,5) * C(3,2) = 18 注；由期望线性性：整票期望 = 总注数 × 单式期望
    base = load_prize_expectation("dlt").iloc[0]
    compound = load_dlt_compound_expectation(6, 3).iloc[0]
    assert compound["total_bets"] == 18
    assert compound["cost_yuan"] == 36
    assert compound["expected_prize_yuan"] == pytest.approx(18 * base["expected_value_yuan"])
    assert compound["return_rate"] == pytest.approx(base["return_rate"])

    compound_add_bet = load_dlt_compound_expectation(6, 3, if_add_bet=True).iloc[0]
    assert compound_add_bet["cost_yuan"] == 54  # 18 注 × 3 元
    assert compound_add_bet["return_rate"] == pytest.approx(
        compound_add_bet["expected_prize_yuan"] / compound_add_bet["cost_yuan"]
    )


def test_dlt_compound_invalid_bounds():
    with pytest.raises(LotteryError):
        load_dlt_compound_expectation(4, 2)
    with pytest.raises(LotteryError):
        load_dlt_compound_expectation(5, 1)
    with pytest.raises(LotteryError):
        load_dlt_compound_expectation(36, 2)
