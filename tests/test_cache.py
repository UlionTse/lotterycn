# coding=utf-8
# author=Ulion.Tse

import pandas

import lotterycn.cache as cache_mod
from lotterycn.cache import get_cache_path, load_cached_history_data

CL_COLS = ["lottery_name", "lottery_order", "lottery_date", "lottery_red", "lottery_blue"]


def _frame(rows):
    return pandas.DataFrame(rows, columns=CL_COLS)


def _rows(dates):
    # lottery_order 由日期派生，保证跨调用唯一且确定
    return [["ssq", date.replace("-", ""), date, "01,05,12,18,27,33", "08"] for date in dates]


def test_cache_creates_file_and_reuses(monkeypatch, tmp_path):
    calls = []

    def fake_load(lottery_name, **kwargs):
        calls.append(kwargs.copy())
        return _frame(_rows(["2026-01-01", "2026-01-02"]))

    monkeypatch.setattr(cache_mod, "load_history_data", fake_load)
    cache_dir = str(tmp_path / "cache")

    frame = load_cached_history_data("ssq", cache_dir=cache_dir)
    assert len(frame) == 2
    path = get_cache_path("ssq", cache_dir=cache_dir)
    assert path.exists()

    # 第二次调用命中缓存：fake 返回空增量，仅返回缓存内容
    monkeypatch.setattr(cache_mod, "load_history_data", lambda lottery_name, **kwargs: pandas.DataFrame())
    frame2 = load_cached_history_data("ssq", cache_dir=cache_dir)
    assert len(frame2) == 2
    assert list(frame2["lottery_date"]) == ["2026-01-01", "2026-01-02"]


def test_cache_incremental_fetch(monkeypatch, tmp_path):
    monkeypatch.setattr(
        cache_mod, "load_history_data", lambda lottery_name, **kwargs: _frame(_rows(["2026-01-01", "2026-01-02"]))
    )
    cache_dir = str(tmp_path / "cache")
    load_cached_history_data("ssq", cache_dir=cache_dir)

    seen = {}

    def fake_incremental(lottery_name, **kwargs):
        seen.update(kwargs)
        return _frame(_rows(["2026-01-03", "2026-01-04"]))

    monkeypatch.setattr(cache_mod, "load_history_data", fake_incremental)
    frame = load_cached_history_data("ssq", cache_dir=cache_dir)

    # cwl 系按最后开奖日期 +1 天增量拉取
    assert seen.get("begin_date") == "2026-01-03"
    assert list(frame["lottery_date"]) == ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]


def test_cache_deduplicates(monkeypatch, tmp_path):
    monkeypatch.setattr(
        cache_mod, "load_history_data", lambda lottery_name, **kwargs: _frame(_rows(["2026-01-01", "2026-01-02"]))
    )
    cache_dir = str(tmp_path / "cache")
    load_cached_history_data("ssq", cache_dir=cache_dir)

    # 接口返回与缓存重叠的旧数据时按 lottery_order 去重
    monkeypatch.setattr(
        cache_mod, "load_history_data", lambda lottery_name, **kwargs: _frame(_rows(["2026-01-02", "2026-01-03"]))
    )
    frame = load_cached_history_data("ssq", cache_dir=cache_dir)
    assert list(frame["lottery_date"]) == ["2026-01-01", "2026-01-02", "2026-01-03"]


def test_detail_result_bypasses_cache(monkeypatch, tmp_path):
    def fake_load(lottery_name, **kwargs):
        assert kwargs.get("is_detail_result") is True
        return [{"result": []}]

    monkeypatch.setattr(cache_mod, "load_history_data", fake_load)
    result = load_cached_history_data("ssq", cache_dir=str(tmp_path / "cache"), is_detail_result=True)
    assert result == [{"result": []}]
    assert not get_cache_path("ssq", cache_dir=str(tmp_path / "cache")).exists()


def test_csl_not_incremental(monkeypatch, tmp_path):
    # csl 系接口不支持日期区间：不做增量参数，全量刷新后去重
    seen = {}

    def fake_load(lottery_name, **kwargs):
        seen.update(kwargs)
        return _frame([["dlt", "26001", "2026-01-01", "01,05,12,18,27", "03,08"]])

    monkeypatch.setattr(cache_mod, "load_history_data", fake_load)
    cache_dir = str(tmp_path / "cache")
    load_cached_history_data("dlt", cache_dir=cache_dir)
    load_cached_history_data("dlt", cache_dir=cache_dir)
    assert "begin_date" not in seen or seen.get("begin_date") is None
