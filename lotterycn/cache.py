# coding=utf-8
# author=Ulion.Tse

import os
import re
import time
import random
import datetime
from pathlib import Path
from typing import Optional, Union, cast

import pandas

from .data import GAME_ZH_NAMES, LotteryError, load_history_data
from .utils import progress_bar


DEFAULT_CACHE_DIR = Path.home() / ".lotterycn" / "history"

# cwl 系接口支持日期区间，可增量更新；csl 系接口仅按页全量返回，刷新后靠去重合并。
CWL_PROJECTS = ("ssq", "qlc", "kl8", "3d")


def get_cache_path(lottery_name: str, cache_dir: Optional[str] = None, table: str = "history") -> Path:
    """计算某彩种某表的缓存 CSV 路径，并确保缓存目录存在。

    :param lottery_name: str, 彩种代码。
    :param cache_dir: str, optional, 缓存目录；None 时取环境变量或默认值（见 get_cache_path）。
    :param table: str, 数据表名（如 history / detail / prizes / provinces）。
    :return: pathlib.Path, 缓存文件路径 `lotterycn_{table}_{lottery_name}.csv`。
    """
    if cache_dir is None:
        cache_dir = os.environ.get("lotterycn_cache_dir", str(DEFAULT_CACHE_DIR))
    root = Path(cache_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root / f"lotterycn_{table}_{lottery_name}.csv"


def _load_fresh_csl_pages(lottery_name: str, cached_orders: frozenset, **kwargs) -> pandas.DataFrame:
    """体彩系增量抓取：从第 1 页（最新在前）翻页，直到某页与缓存订单集重叠即停。

    体彩接口无日期窗口查询，页面按新到旧排序，因此"页内出现已缓存期号"意味着更旧的
    页全部冗余；通常第 1 页即可覆盖增量。翻完全部页数则等价全量刷新，由调用方去重
    兜底正确性。
    """
    from .data import _cl

    timeout = kwargs.get("timeout", 15)
    proxies = kwargs.get("proxies", None)
    max_retries = kwargs.get("max_retries", 3)
    sleep_seconds = kwargs.get("sleep_seconds", random.random())
    total_pages = _cl.csl_warmup(timeout=timeout, proxies=proxies, max_retries=max_retries)

    frames = []
    rows_fetched = 0
    with progress_bar(f"Downloading {lottery_name}", unit="pages", total=total_pages) as bar:
        for page_no in range(1, total_pages + 1):
            raw = _cl._csl(
                lottery_name=lottery_name, page_no=page_no, timeout=timeout, proxies=proxies, max_retries=max_retries
            )
            frame = _cl.get_history_data_dataframe(raw, lottery_name)
            frames.append(frame)
            rows_fetched += len(frame)
            bar.advance()
            bar.set_info(f"{rows_fetched} rows")
            if set(frame["lottery_order"]) & cached_orders:
                # reached draws already present in the cache; reflect pages actually fetched
                bar.set_total(page_no)
                break  # older pages add nothing
            if page_no < total_pages:
                time.sleep(sleep_seconds)
    return pandas.concat(frames, axis=0, ignore_index=True)


def load_cached_history_data(
    lottery_name: str, cache_dir: Optional[str] = None, **kwargs
) -> Union[list, pandas.DataFrame]:
    """带本地缓存的历史开奖数据加载。

    首次调用全量拉取并写入 CSV；之后读取本地缓存，仅拉取最后开奖日期之后的数据并合并去重。
    is_detail_result=True 的明细结果不落盘，直接透传。

    :param lottery_name: str, 彩种代码。
    :param cache_dir: str, optional, 缓存目录；None 时取环境变量或默认值（见 get_cache_path）。
    :param **kwargs: 透传给 load_history_data（如 is_detail_result、timeout）；if_cached 由本层
        消费后立即剥离，防止 data 层再次分发回本层造成无限递归；命中缓存时 begin_date 会被
        改写为增量起点（福彩系）。
    :return: Union[list, pandas.DataFrame], is_detail_result=True 时透传明细（list），否则返回
        合并去重后的历史 DataFrame。
    """
    kwargs.pop("if_cached", None)  # consumed here; re-passing it re-dispatches data -> cache forever

    if kwargs.get("is_detail_result", False):
        return load_history_data(lottery_name=lottery_name, **kwargs)

    path = get_cache_path(lottery_name=lottery_name, cache_dir=cache_dir)
    cached = None
    if path.exists():
        cached = pandas.read_csv(path, dtype=str).fillna("")
        # migrate caches written by older versions: display names -> codes, and the
        # lottery_zh_name column did not exist before 1.0.1
        cached["lottery_name"] = cached["lottery_name"].replace({v: k for k, v in GAME_ZH_NAMES.items()})
        if "lottery_zh_name" not in cached.columns:
            cached.insert(1, "lottery_zh_name", "")
        cached = cached[cached["lottery_date"].notna() & (cached["lottery_date"] != "")]

    if cached is None or cached.empty:
        frame = cast(pandas.DataFrame, load_history_data(lottery_name=lottery_name, **kwargs))
    else:
        kwargs.pop("begin_date", None)
        if lottery_name in CWL_PROJECTS:
            # tolerate legacy caches written before date normalisation ("2026-10-08(四)")
            match = re.match(r"(\d{4}-\d{2}-\d{2})", str(cached["lottery_date"].max()))
            if match is None:
                raise LotteryError(f"cannot parse latest cached date: {cached['lottery_date'].max()!r}")
            next_date = datetime.date.fromisoformat(match.group(1)) + datetime.timedelta(days=1)
            if next_date > datetime.date.today():
                # the cache already covers every draw up to today: a begin_date beyond
                # today would be rejected by check_params, and no newer draw can exist
                fresh = cached.iloc[0:0]
            else:
                kwargs["begin_date"] = next_date.isoformat()
                fresh = cast(pandas.DataFrame, load_history_data(lottery_name=lottery_name, **kwargs))
        else:
            # csl 系接口按页返回且最新在前：翻页直到与缓存重叠即停（通常仅第 1 页），
            # 避免缓存命中后仍全量重抓几十页；翻完全部页数则等价全量刷新，去重兜底正确性。
            fresh = _load_fresh_csl_pages(
                lottery_name=lottery_name, cached_orders=frozenset(cached["lottery_order"]), **kwargs
            )

        frame = pandas.concat([cached, fresh], axis=0, ignore_index=True)

    # lottery_order is unique within a game file; keying on it alone keeps the dedup
    # correct even when legacy rows still carry display names in lottery_name
    frame = frame.drop_duplicates(subset=["lottery_order"], keep="last")
    frame = frame.sort_values(by=["lottery_date", "lottery_order"]).reset_index(drop=True)
    try:
        frame.to_csv(path, index=False)
    except OSError:
        pass  # 缓存写入失败不影响数据返回
    return frame
