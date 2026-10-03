# coding=utf-8
# author=Ulion.Tse

import pytest

from lotterycn.check import load_check_result
from lotterycn.utils import LotteryError


def test_ssq_first_prize():
    frame = load_check_result("ssq", "01,05,12,18,27,33|08", "01,05,12,18,27,33|08")
    assert frame.iloc[0]["prize_level"] == "一等奖"
    assert frame.iloc[0]["prize_type"] == "浮动(单注封顶500万元)"


def test_ssq_third_prize():
    frame = load_check_result("ssq", "01,05,12,18,27,32|08", "01,05,12,18,27,33|08")
    assert frame.iloc[0]["prize_level"] == "三等奖"
    assert frame.iloc[0]["prize_amount"] == 3000.0


def test_ssq_miss():
    frame = load_check_result("ssq", "02,04,07,11,20,31|09", "01,05,12,18,27,33|08")
    assert frame.iloc[0]["prize_level"] == "未中奖"
    assert frame.iloc[0]["prize_amount"] == 0.0


def test_dlt_first_prize():
    frame = load_check_result("dlt", "01,05,12,18,27|03,08", "01,05,12,18,27|03,08")
    assert frame.iloc[0]["prize_level"] == "一等奖"


def test_qlc_prizes():
    draw = "01,05,12,18,22,27,30|09"
    first = load_check_result("qlc", "01,05,12,18,22,27,30", draw)
    assert first.iloc[0]["prize_level"] == "一等奖"
    second = load_check_result("qlc", "01,05,12,18,22,27,09", draw)
    assert second.iloc[0]["prize_level"] == "二等奖"


def test_kl8_check():
    frame = load_check_result(
        "kl8", "01,02,03,04,05,06,07,08,09,10", "01,02,03,04,05,06,07,08,60,61,62,63,64,65,66,67,68,69,70,71"
    )
    assert frame.iloc[0]["prize_level"] == "选10中8"
    assert frame.iloc[0]["prize_amount"] == 720.0


def test_digit_checks():
    exact = load_check_result("3d", "123", "123")
    assert set(exact["prize_level"]) == {"单选", "组选6"}  # 单选与组选6均可命中
    assert exact[exact["prize_level"] == "单选"].iloc[0]["prize_amount"] == 1040.0

    group6 = load_check_result("3d", "123", "213")
    assert group6.iloc[0]["prize_level"] == "组选6"
    assert group6.iloc[0]["prize_amount"] == 173.0

    group3 = load_check_result("pls", "122", "212")
    assert group3.iloc[0]["prize_level"] == "组选3"
    assert group3.iloc[0]["prize_amount"] == 346.0

    miss = load_check_result("plw", "12345", "54321")
    assert miss.iloc[0]["prize_level"] == "未中奖"


def test_qxc_third_prize():
    frame = load_check_result("qxc", "1,2,3,4,5,6|7", "1,2,3,4,5,9|7")
    assert frame.iloc[0]["prize_level"] == "三等奖"
    assert frame.iloc[0]["prize_amount"] == 3000.0


def test_draw_from_dict_row():
    draw = {"lottery_red": "01,05,12,18,27,33", "lottery_blue": "08"}
    frame = load_check_result("ssq", "01,05,12,18,27,33|08", draw)
    assert frame.iloc[0]["prize_level"] == "一等奖"


def test_invalid_numbers_raise():
    with pytest.raises(LotteryError):
        load_check_result("ssq", "1,2|3", "01,05,12,18,27,33|08")  # 红球数量不足
    with pytest.raises(LotteryError):
        load_check_result("ssq", "01,05,12,18,27,34|08", "01,05,12,18,27,33|08")  # 越界
    with pytest.raises(LotteryError):
        load_check_result("qlc", "01,05,12,18,22,27,30|09", "01,05,12,18,22,27,30|09")  # 七乐彩不可自选特别号
    with pytest.raises(LotteryError):
        load_check_result("abc", "1,2,3", "1,2,3")
