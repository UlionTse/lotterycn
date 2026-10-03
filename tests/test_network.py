# coding=utf-8
# author=Ulion.Tse

import pytest

from lotterycn.data import load_history_data, lottery_pool


@pytest.mark.network
def test_load_history_data():
    for lottery_name in lottery_pool:
        frame = load_history_data(lottery_name=lottery_name)
        assert len(frame) > 0
        assert list(frame.columns) == ["lottery_name", "lottery_order", "lottery_date", "lottery_red", "lottery_blue"]


@pytest.mark.network
def test_load_cached_history_data():
    from lotterycn.data import load_history_data as loader

    # 真实网络下的缓存读写与增量更新冒烟
    frame = loader("ssq", if_cached=True)
    assert len(frame) > 0
