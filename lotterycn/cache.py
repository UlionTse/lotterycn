# coding=utf-8
# author=Ulion.Tse

import datetime
import os
from pathlib import Path
from typing import Optional, Union, cast

import pandas

from .data import load_history_data

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


def load_cached_history_data(
    lottery_name: str, cache_dir: Optional[str] = None, **kwargs
) -> Union[list, pandas.DataFrame]:
    """带本地缓存的历史开奖数据加载。

    首次调用全量拉取并写入 CSV；之后读取本地缓存，仅拉取最后开奖日期之后的数据并合并去重。
    is_detail_result=True 的明细结果不落盘，直接透传。

    :param lottery_name: str, 彩种代码。
    :param cache_dir: str, optional, 缓存目录；None 时取环境变量或默认值（见 get_cache_path）。
    :param **kwargs: 透传给 load_history_data（如 is_detail_result、if_cached）；命中缓存时
        begin_date 会被改写为增量起点（福彩系）。
    :return: Union[list, pandas.DataFrame], is_detail_result=True 时透传明细（list），否则返回
        合并去重后的历史 DataFrame。
    """
    if kwargs.get("is_detail_result", False):
        return load_history_data(lottery_name=lottery_name, **kwargs)

    path = get_cache_path(lottery_name=lottery_name, cache_dir=cache_dir)
    cached = None
    if path.exists():
        cached = pandas.read_csv(path, dtype=str).fillna("")
        cached = cached[cached["lottery_date"].notna() & (cached["lottery_date"] != "")]

    if cached is None or cached.empty:
        frame = cast(pandas.DataFrame, load_history_data(lottery_name=lottery_name, **kwargs))
    else:
        kwargs.pop("begin_date", None)
        if lottery_name in CWL_PROJECTS:
            last_date = datetime.date.fromisoformat(cached["lottery_date"].max())
            kwargs["begin_date"] = (last_date + datetime.timedelta(days=1)).isoformat()
        fresh = cast(pandas.DataFrame, load_history_data(lottery_name=lottery_name, **kwargs))

        frame = pandas.concat([cached, fresh], axis=0, ignore_index=True)

    frame = frame.drop_duplicates(subset=["lottery_name", "lottery_order"], keep="last")
    frame = frame.sort_values(by=["lottery_date", "lottery_order"]).reset_index(drop=True)
    try:
        frame.to_csv(path, index=False)
    except OSError:
        pass  # 缓存写入失败不影响数据返回
    return frame
