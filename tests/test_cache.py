# coding=utf-8
# author=Ulion.Tse

import pandas

import lotterycn.cache as cache_mod
from lotterycn.cache import get_cache_path, load_cached_history_data

CL_COLS = [
    "lottery_name",
    "lottery_zh_name",
    "lottery_order",
    "lottery_date",
    "lottery_red",
    "lottery_blue",
]


def _frame(rows):
    return pandas.DataFrame(rows, columns=CL_COLS)


def _rows(dates):
    # lottery_order 由日期派生，保证跨调用唯一且确定
    return [["ssq", "双色球", date.replace("-", ""), date, "01,05,12,18,27,33", "08"] for date in dates]


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
        return _frame([["dlt", "超级大乐透", "26001", "2026-01-01", "01,05,12,18,27", "03,08"]])

    monkeypatch.setattr(cache_mod, "load_history_data", fake_load)
    cache_dir = str(tmp_path / "cache")
    load_cached_history_data("dlt", cache_dir=cache_dir)
    load_cached_history_data("dlt", cache_dir=cache_dir)
    assert "begin_date" not in seen or seen.get("begin_date") is None


def test_public_entry_empty_cache_no_recursion(monkeypatch, tmp_path):
    # 回归：走真实 data.load_history_data → cache 分发链路（mock 网络层而非 cache 层），
    # 防止 if_cached 被原样透传回 data 层导致无限递归（mock cache 层的旧测法会掩盖此 bug）。
    import lotterycn.data as data_mod

    calls = []

    def fake_cwl(lottery_name, **kwargs):  # instance-attribute stub: no self is passed
        calls.append(kwargs.copy())
        return _cwl_raw(["2026-01-01", "2026-01-02"])

    monkeypatch.setattr(data_mod._cl, "cwl", fake_cwl)
    cache_dir = str(tmp_path / "cache")

    # 首次调用（缓存为空）：必须直达网络层并落盘，而不是 data↔cache 互调递归
    frame = data_mod.load_history_data("ssq", if_cached=True, cache_dir=cache_dir)
    assert list(frame["lottery_date"]) == ["2026-01-01", "2026-01-02"]
    assert get_cache_path("ssq", cache_dir=cache_dir).exists()

    # 第二次调用（缓存命中）：增量分支同样不得递归
    frame2 = data_mod.load_history_data("ssq", if_cached=True, cache_dir=cache_dir)
    assert list(frame2["lottery_date"]) == ["2026-01-01", "2026-01-02"]
    assert len(calls) == 2  # 每次 public 调用恰触发一次真实抓取


def test_public_entry_normalises_weekday_dates(monkeypatch, tmp_path):
    # 回归：官方 CWL 接口日期带星期后缀（"2026-10-08(四)"），入口层需规整为纯 ISO，
    # 否则公共 DataFrame / 缓存 CSV 全是脏日期，增量分支 fromisoformat 直接 ValueError。
    import lotterycn.data as data_mod

    def fake_cwl(lottery_name, **kwargs):  # instance-attribute stub: no self is passed
        return _cwl_raw(["2026-10-06(二)", "2026-10-08(四)"])

    monkeypatch.setattr(data_mod._cl, "cwl", fake_cwl)
    cache_dir = str(tmp_path / "cache")

    frame = data_mod.load_history_data("ssq", if_cached=True, cache_dir=cache_dir)
    assert list(frame["lottery_date"]) == ["2026-10-06", "2026-10-08"]

    # 缓存命中后增量刷新：begin_date 从规整后的缓存日期推导，不抛 ValueError
    seen = {}

    def fake_incremental(lottery_name, **kwargs):
        seen.update(kwargs)
        return _cwl_raw([])  # 增量窗口无开奖：空原始响应（带原始列名）

    monkeypatch.setattr(data_mod._cl, "cwl", fake_incremental)
    frame2 = data_mod.load_history_data("ssq", if_cached=True, cache_dir=cache_dir)
    assert seen.get("begin_date") == "2026-10-09"
    assert list(frame2["lottery_date"]) == ["2026-10-06", "2026-10-08"]


def test_legacy_cache_with_weekday_dates(monkeypatch, tmp_path):
    # 旧版本写入的缓存日期带星期后缀：增量解析需容错提取 ISO 前缀，老缓存不用手删
    cache_dir = str(tmp_path / "cache")
    path = get_cache_path("ssq", cache_dir=cache_dir)
    _frame(_rows(["2026-10-08(四)"])).to_csv(path, index=False)

    seen = {}

    def fake_load(lottery_name, **kwargs):
        seen.update(kwargs)
        return _frame(_rows(["2026-10-09(五)"]))

    monkeypatch.setattr(cache_mod, "load_history_data", fake_load)
    frame = load_cached_history_data("ssq", cache_dir=cache_dir)
    assert seen.get("begin_date") == "2026-10-09"
    assert len(frame) == 2


def test_cache_skips_fetch_when_already_current(monkeypatch, tmp_path):
    # 回归：缓存已覆盖到今天（或接口返回了未来日期行）时，增量 begin_date 会落在
    # 明天，check_params 直接拒绝——应跳过网络抓取并直接返回缓存。
    import datetime

    today = datetime.date.today().isoformat()
    cache_dir = str(tmp_path / "cache")
    path = get_cache_path("ssq", cache_dir=cache_dir)
    _frame(_rows([today])).to_csv(path, index=False)

    def fail_load(lottery_name, **kwargs):
        raise AssertionError("network fetch must be skipped when the cache is current")

    monkeypatch.setattr(cache_mod, "load_history_data", fail_load)
    frame = load_cached_history_data("ssq", cache_dir=cache_dir)
    assert list(frame["lottery_date"]) == [today]


def test_public_entry_empty_draw_window(monkeypatch, tmp_path):
    # 回归：增量窗口内可能没有开奖（ssq 每周三/日开奖），_cwl 必须返回带列名的空表，
    # 否则 cwl() 的 sort_values("code") 抛 KeyError；增量刷新应安全返回缓存内容。
    import lotterycn.data as data_mod

    rows = [
        {"name": "双色球", "code": "2026001", "date": "2026-01-01(五)", "red": "01,05,12,18,27,33", "blue": "08"},
        {"name": "双色球", "code": "2026002", "date": "2026-01-04(日)", "red": "02,06,11,15,22,31", "blue": "09"},
    ]

    # 首个全量窗口返回两期开奖；后续增量窗口（dayStart 不同）一律无开奖
    def fake_fetch_json(*args, **kwargs):
        params = kwargs.get("params") or args[1]
        return {"result": rows} if params.get("dayStart") == "2013-01-01" else {"result": []}

    monkeypatch.setattr(data_mod._cl, "session", object())  # skip the host warm-up request
    monkeypatch.setattr(data_mod._cl, "fetch_json", fake_fetch_json)
    cache_dir = str(tmp_path / "cache")

    frame = data_mod.load_history_data("ssq", if_cached=True, cache_dir=cache_dir, sleep_seconds=0)
    assert list(frame["lottery_date"]) == ["2026-01-01", "2026-01-04"]  # 入口日期规整同时被覆盖

    frame2 = data_mod.load_history_data("ssq", if_cached=True, cache_dir=cache_dir, sleep_seconds=0)
    assert list(frame2["lottery_date"]) == ["2026-01-01", "2026-01-04"]  # 增量无新增，安全返回缓存


def _csl_page(rows):
    """体彩 _csl 原始返回：4 列（无 blue），日期带星期后缀，red 含空格分隔的前后区。"""
    return pandas.DataFrame(rows, columns=["lotteryGameName", "lotteryDrawNum", "lotteryDrawTime", "lotteryDrawResult"])


def _cwl_raw(dates):
    """官方 CWL 接口原始返回：name/code/date/red/blue，date 带星期后缀。

    注意：cwl 桩必须用原始 5 列形状——get_history_data_dataframe 在其上做列名映射并输出
    公共 6 列 schema，公共 schema 是它的输出而非输入。
    """
    rows = [
        {
            "name": "双色球",
            "code": f"2026{i:04d}",
            "date": date,
            "red": "01,05,12,18,27,33",
            "blue": "08",
        }
        for i, date in enumerate(dates, start=1)
    ]
    # explicit columns: the empty case must still carry the raw schema, like the real guard
    return pandas.DataFrame(rows, columns=["name", "code", "date", "red", "blue"])


def test_csl_incremental_stops_at_overlap(monkeypatch, tmp_path):
    # 体彩系缓存命中：第 1 页（最新在前）与缓存有交集即停，不再全量重抓几十页
    import lotterycn.data as data_mod

    cache_dir = str(tmp_path / "cache")
    path = get_cache_path("dlt", cache_dir=cache_dir)
    _frame(
        [
            ["dlt", "超级大乐透", "26095", "2026-09-23", "01,05,12,18,27", "03,08"],
            ["dlt", "超级大乐透", "26096", "2026-09-26", "02,06,11,15,22", "05,09"],
        ]
    ).to_csv(path, index=False)

    pages = {
        1: _csl_page(
            [
                ["超级大乐透", "26098", "2026-09-30(三)", "03,07,13,19,25 04,10"],
                ["超级大乐透", "26097", "2026-09-28(一)", "01,04,10,16,21 02,07"],
                ["超级大乐透", "26096", "2026-09-26(六)", "02,06,11,15,22 05,09"],  # 与缓存重叠 → 停
            ]
        ),
        2: _csl_page([["超级大乐透", "26095", "2026-09-23(三)", "06,08,14,20,26 01,03"]]),  # 不应被抓取
    }
    fetched = []

    def fake__csl(lottery_name, page_no, **kwargs):
        fetched.append(page_no)
        return pages[page_no]

    monkeypatch.setattr(data_mod._cl, "csl_warmup", lambda **kwargs: 2)
    monkeypatch.setattr(data_mod._cl, "_csl", fake__csl)

    frame = load_cached_history_data("dlt", cache_dir=cache_dir, sleep_seconds=0)
    assert fetched == [1]  # 第 1 页出现重叠即停
    assert sorted(frame["lottery_order"]) == ["26095", "26096", "26097", "26098"]
    assert list(frame["lottery_date"]) == ["2026-09-23", "2026-09-26", "2026-09-28", "2026-09-30"]  # 干净日期


def test_csl_incremental_full_refresh_when_no_overlap(monkeypatch, tmp_path):
    # 缓存很旧且与第 1 页无交集：翻完全部页数（等价全量刷新），结果仍正确
    import lotterycn.data as data_mod

    cache_dir = str(tmp_path / "cache")
    path = get_cache_path("dlt", cache_dir=cache_dir)
    _frame(
        [
            ["dlt", "超级大乐透", "26091", "2026-09-12", "01,05,12,18,27", "03,08"],
            ["dlt", "超级大乐透", "26092", "2026-09-14", "02,06,11,15,22", "05,09"],
        ]
    ).to_csv(path, index=False)

    pages = {
        1: _csl_page(
            [
                ["超级大乐透", "26098", "2026-09-30(三)", "03,07,13,19,25 04,10"],
                ["超级大乐透", "26097", "2026-09-28(一)", "01,04,10,16,21 02,07"],
                ["超级大乐透", "26096", "2026-09-26(六)", "02,06,11,15,22 05,09"],
            ]
        ),
        2: _csl_page(
            [
                ["超级大乐透", "26095", "2026-09-23(三)", "06,08,14,20,26 01,03"],
                ["超级大乐透", "26094", "2026-09-20(日)", "04,09,15,21,27 02,08"],
            ]
        ),
    }
    fetched = []

    def fake__csl(lottery_name, page_no, **kwargs):
        fetched.append(page_no)
        return pages[page_no]

    monkeypatch.setattr(data_mod._cl, "csl_warmup", lambda **kwargs: 2)
    monkeypatch.setattr(data_mod._cl, "_csl", fake__csl)

    frame = load_cached_history_data("dlt", cache_dir=cache_dir, sleep_seconds=0)
    assert fetched == [1, 2]  # 无重叠 → 翻完全部页数
    assert sorted(frame["lottery_order"]) == ["26091", "26092", "26094", "26095", "26096", "26097", "26098"]
    assert not frame["lottery_date"].str.contains(r"\(").any()  # 全部规整为干净日期
