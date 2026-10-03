# coding=utf-8
# author=Ulion.Tse

import pathlib

import pandas
import pytest

import lotterycn.draws as draws_mod
from lotterycn.draws import load_draw_detail, load_first_prize_by_province, load_prize_results
from lotterycn.utils import LotteryError

# fixtures 按 _tmp_probe 实测的官方响应结构构造
SSQ_RECORD = {
    "name": "双色球",
    "code": "2026001",
    "date": "2026-01-01(四)",
    "red": "01,05,12,18,27,33",
    "blue": "08",
    "sales": "361167416",
    "poolmoney": "2782271788",
    "content": "浙江2注，湖南1注，新疆1注，共4注。",
    "prizegrades": [
        {"type": 1, "typenum": "4", "typemoney": "8704419"},
        {"type": 2, "typenum": "128", "typemoney": "144703"},
        {"type": 3, "typenum": "1988", "typemoney": "3000"},
        {"type": 4, "typenum": "104550", "typemoney": "200"},
        {"type": 5, "typenum": "1818555", "typemoney": "10"},
        {"type": 6, "typenum": "11564820", "typemoney": "5"},
        {"type": 7, "typenum": "", "typemoney": ""},
    ],
}

KL8_RECORD = {
    "name": "快乐8",
    "code": "2026001",
    "date": "2026-01-01",
    "red": "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20",
    "blue": "",
    "sales": "103779246",
    "poolmoney": "104539707.67",
    "content": "浙江1注，广东8注。",
    "prizegrades": [
        {"type": "x10z10", "typenum": "1", "typemoney": "5000000"},
        {"type": "x10z9", "typenum": "9", "typemoney": "8000"},
        {"type": "x10z0", "typenum": "297075", "typemoney": "2"},
        {"type": "x9z9", "typenum": "1", "typemoney": "250000"},
        {"type": "x9z0", "typenum": "266289", "typemoney": "2"},
    ],
}

D3_RECORD = {
    "name": "福彩3D",
    "code": "2026262",
    "date": "2026-09-29(二)",
    "red": "9,6,8",
    "blue": "",
    "sales": "96846432",
    "poolmoney": "",
    "content": "",
    "prizegrades": [{"type": i, "typenum": "", "typemoney": ""} for i in range(1, 8)],
}

DLT_RECORD = {
    "lotteryDrawNum": "26112",
    "lotteryDrawTime": "2026-09-30",
    "lotteryDrawResult": "01 03 05 10 22 03 09",
    "totalSaleAmount": "306,396,671",
    "poolBalanceAfterdraw": "798,649,740.87",
    "prizeLevelList": [
        {"prizeLevel": "一等奖", "stakeCount": "6", "stakeAmountFormat": "8047843"},
        {"prizeLevel": "一等奖(追加)", "stakeCount": "0", "stakeAmountFormat": "-1"},
        {"prizeLevel": "二等奖", "stakeCount": "109", "stakeAmountFormat": "133482"},
        {"prizeLevel": "三等奖", "stakeCount": "1,121", "stakeAmountFormat": "6666"},
    ],
}


def test_detail_cwl():
    frame = load_draw_detail("ssq", records=[SSQ_RECORD])
    row = frame.iloc[0]
    assert row["lottery_date"] == "2026-01-01"  # 星期后缀被清洗
    assert row["lottery_order"] == "2026001"
    assert row["sales_yuan"] == 361167416.0
    assert row["pool_yuan"] == 2782271788.0


def test_detail_csl_split():
    frame = load_draw_detail("dlt", records=[DLT_RECORD])
    row = frame.iloc[0]
    assert row["lottery_red"] == "01,03,05,10,22"
    assert row["lottery_blue"] == "03,09"
    assert row["sales_yuan"] == 306396671.0
    assert row["pool_yuan"] == 798649740.87


def test_detail_3d_no_pool():
    frame = load_draw_detail("3d", records=[D3_RECORD])
    assert frame.iloc[0]["sales_yuan"] == 96846432.0
    assert pandas.isna(frame.iloc[0]["pool_yuan"])  # 3d 无奖池字段


def test_prizes_cwl_ssq():
    frame = load_prize_results("ssq", records=[SSQ_RECORD])
    assert len(frame) == 6  # 第 7 档空占位被跳过
    first = frame[frame["prize_level"] == "一等奖"].iloc[0]
    assert first["winner_count"] == 4
    assert first["prize_per_bet_yuan"] == 8704419.0
    assert (frame["play_type"] == "单式").all()


def test_prizes_kl8_play_types():
    frame = load_prize_results("kl8", records=[KL8_RECORD])
    assert len(frame) == 5
    pick10 = frame[frame["play_type"] == "选十"]
    assert set(pick10["prize_level"]) == {"选十中十", "选十中九", "选十全不中"}
    assert pick10[pick10["prize_level"] == "选十中十"].iloc[0]["prize_per_bet_yuan"] == 5000000.0
    assert (frame[frame["play_type"] == "选九"]["prize_level"] == "选九全不中").any()


def test_prizes_dlt_with_addon():
    frame = load_prize_results("dlt", records=[DLT_RECORD])
    assert len(frame) == 4
    addon = frame[frame["play_type"] == "追加"].iloc[0]
    assert addon["prize_level"] == "一等奖(追加)"
    assert pandas.isna(addon["prize_per_bet_yuan"])  # -1 → NaN
    assert addon["winner_count"] == 0
    normal = frame[frame["prize_level"] == "三等奖"].iloc[0]
    assert normal["winner_count"] == 1121
    assert normal["prize_per_bet_yuan"] == 6666.0


def test_prizes_3d_empty():
    frame = load_prize_results("3d", records=[D3_RECORD])
    assert frame.empty  # 3d 官网接口不提供奖级数据


def test_province_parse():
    frame = load_first_prize_by_province("ssq", records=[SSQ_RECORD])
    assert len(frame) == 3  # '共4注。' 汇总段被剔除
    assert dict(zip(frame["province"], frame["count"])) == {"浙江": 2, "湖南": 1, "新疆": 1}

    kl8 = load_first_prize_by_province("kl8", records=[KL8_RECORD])
    assert dict(zip(kl8["province"], kl8["count"])) == {"浙江": 1, "广东": 8}

    assert load_first_prize_by_province("3d", records=[D3_RECORD]).empty


def test_invalid_game_raises():
    with pytest.raises(LotteryError):
        load_draw_detail("abc")


def test_detail_cache_incremental(monkeypatch, tmp_path):
    def full_history(lottery_name, **kwargs):
        return [
            {
                "name": "双色球",
                "code": "2026001",
                "date": "2026-01-01",
                "red": "01,05,12,18,27,33",
                "blue": "08",
                "sales": "100",
                "poolmoney": "200",
                "content": "",
                "prizegrades": [],
            }
        ]

    monkeypatch.setattr(draws_mod, "load_history_data", full_history)
    cache_dir = str(tmp_path / "cache")
    frame = load_draw_detail("ssq", if_cached=True, cache_dir=cache_dir)
    assert len(frame) == 1
    assert (pathlib.Path(cache_dir) / "lotterycn_detail_ssq.csv").exists()

    seen = {}

    def incremental(lottery_name, **kwargs):
        seen.update(kwargs)
        return [
            {
                "name": "双色球",
                "code": "2026002",
                "date": "2026-01-03",
                "red": "02,06,11,15,22,30",
                "blue": "09",
                "sales": "110",
                "poolmoney": "210",
                "content": "",
                "prizegrades": [],
            }
        ]

    monkeypatch.setattr(draws_mod, "load_history_data", incremental)
    frame = load_draw_detail("ssq", if_cached=True, cache_dir=cache_dir)
    assert seen.get("begin_date") == "2026-01-02"  # 最后开奖日期 +1 天
    assert list(frame["lottery_date"]) == ["2026-01-01", "2026-01-03"]
