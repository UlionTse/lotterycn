# coding=utf-8
"""Property-based tests for odds / expectation invariants (hypothesis, offline)."""

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lotterycn import load_dlt_compound_expectation, load_prize_expectation

DLT_GAMES = ["ssq", "qlc", "kl8", "3d", "dlt", "pls", "plw", "qxc"]


@pytest.mark.parametrize("lottery_name", DLT_GAMES)
def test_return_rate_within_unit_interval(lottery_name):
    exp = load_prize_expectation(lottery_name)
    assert (exp["return_rate"] >= 0).all() and (exp["return_rate"] <= 1).all()
    assert (exp["expected_value_yuan"] >= 0).all()


@settings(max_examples=30, deadline=None)
@given(n_red=st.integers(min_value=5, max_value=35), m_blue=st.integers(min_value=2, max_value=12))
def test_dlt_compound_bets_match_combinatorics(n_red, m_blue):
    result = load_dlt_compound_expectation(n_red=n_red, m_blue=m_blue).iloc[0]
    assert result["total_bets"] == math.comb(n_red, 5) * math.comb(m_blue, 2)
    assert result["cost_yuan"] == result["total_bets"] * 2


@settings(max_examples=30, deadline=None)
@given(n_red=st.integers(min_value=5, max_value=35), m_blue=st.integers(min_value=2, max_value=12))
def test_dlt_compound_expectation_is_linear(n_red, m_blue):
    compound = load_dlt_compound_expectation(n_red=n_red, m_blue=m_blue).iloc[0]
    single = load_prize_expectation("dlt").iloc[0]
    assert compound["total_bets"] * single["expected_value_yuan"] == pytest.approx(
        compound["expected_prize_yuan"], rel=1e-9
    )


@settings(max_examples=30, deadline=None)
@given(n_red=st.integers(min_value=5, max_value=35), m_blue=st.integers(min_value=2, max_value=12))
def test_dlt_compound_return_rate_within_unit_interval(n_red, m_blue):
    result = load_dlt_compound_expectation(n_red=n_red, m_blue=m_blue).iloc[0]
    assert 0 < result["return_rate"] <= 1
