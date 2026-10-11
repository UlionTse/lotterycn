# coding=utf-8
# author=Ulion.Tse

import datetime
import decimal
import random
import sys
import time
import urllib.parse
from typing import Optional, Union

import pandas
import requests
from rich.console import Console
from rich.progress import (
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.text import Text


class Tse:
    """彩票数据基类：请求头构造、日期区间与四舍五入等通用工具。"""

    session: Optional[requests.Session] = None

    def __init__(self):
        self.author = "Ulion.Tse"
        self.today_date = self.get_date(fake_today="today", move_days=0, date_format="%Y-%m-%d")

    @staticmethod
    def get_headers(
        host_url: str,
        if_api: bool = False,
        if_referer_for_host: bool = True,
        if_ajax_for_api: bool = True,
        if_json_for_api: bool = False,
    ) -> dict:
        """构造请求头：主机头（Host/Referer + UA）或 API 头（追加 Origin / X-Requested-With 等）。

        :param host_url: str, 目标站点 URL。
        :param if_api: bool, optional, True 返回接口调用头，False 返回页面访问头，默认 False。
        :param if_referer_for_host: bool, optional, 主机头用 Referer 替代 Host，默认 True。
        :param if_ajax_for_api: bool, optional, API 头是否带 X-Requested-With，默认 True。
        :param if_json_for_api: bool, optional, API 头是否带 application/json，默认 False。
        :return: dict, 请求头。
        """

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"  # noqa: E501  # noqa: E501  # noqa: E501
        url_path = urllib.parse.urlparse(host_url).path
        host_headers = {
            "Referer" if if_referer_for_host else "Host": host_url,
            "User-Agent": user_agent,
        }
        api_headers = {
            "Origin": host_url.split(url_path)[0] if url_path else host_url,
            "Referer": host_url,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": user_agent,
        }
        if if_api and not if_ajax_for_api:
            api_headers.pop("X-Requested-With")
            api_headers.update({"Content-Type": "text/plain"})
        if if_api and if_json_for_api:
            api_headers.update({"Content-Type": "application/json"})
        return host_headers if not if_api else api_headers

    @staticmethod
    def get_date(fake_today: str = "today", move_days: int = 0, date_format: str = "%Y-%m-%d") -> str:
        """按格式计算日期（可基于今天或指定日期平移）。

        :param fake_today: str, optional, 基准日期（date_format 格式）或 'today'，默认 'today'。
        :param move_days: int, optional, 平移天数，默认 0。
        :param date_format: str, optional, 日期格式，默认 '%Y-%m-%d'。
        :return: str, 格式化后的日期字符串。
        """
        day = (
            datetime.date.today()
            if fake_today == "today"
            else datetime.datetime.strptime(fake_today, date_format).date()
        )
        return (day + datetime.timedelta(days=move_days)).strftime(date_format)

    def get_during_list(self, begin_date: str, end_date: str, freq: str = "1D") -> list:
        """生成日期区间的增量抓取边界列表（起点 + 各分段边界 + 终点）。

        :param begin_date: str, 起始日期。
        :param end_date: str, 结束日期。
        :param freq: str, optional, pandas.date_range 频率，默认 '1D'。
        :return: list, [begin_date, ...分段边界..., end_date]。
        """
        during_list = [
            x
            for d in pandas.date_range(start=begin_date, end=end_date, freq=freq, inclusive="neither")
            for x in (str(d)[:10], self.get_date(fake_today=str(d)[:10], move_days=1))
        ]
        return [begin_date] + during_list + [end_date]

    def fetch_json(
        self,
        url: str,
        params: dict,
        headers: dict,
        timeout: float,
        proxies: Optional[dict],
        max_retries: int,
        source: str,
    ) -> dict:
        """带重试与指数退避的 GET 请求，返回 JSON dict（需先建立 self.session）。

        :param url: str, 接口地址。
        :param params: dict, 查询参数。
        :param headers: dict, 请求头。
        :param timeout: float, 单次请求超时（秒）。
        :param proxies: Optional[dict], 代理配置。
        :param max_retries: int, 最大重试次数（至少 1）。
        :param source: str, 来源标识（用于错误消息）。
        :return: dict, 接口返回的 JSON。
        """
        if self.session is None:
            self.session = requests.Session()
        max_retries = max(1, max_retries)
        for attempt in range(max_retries):
            try:
                r = self.session.get(url, params=params, headers=headers, timeout=timeout, proxies=proxies)
                r.raise_for_status()
                return r.json()
            except (requests.RequestException, ValueError) as e:
                if attempt == max_retries - 1:
                    raise LotteryError(f"{source} api failed after {max_retries} retries: {params}") from e
                time.sleep(2**attempt + random.random())  # 指数退避后重试
        raise LotteryError(f"{source} api failed after {max_retries} retries: {params}")

    @staticmethod
    def round_half_up(number: Union[float, int], n_digits: int = 0, if_return_float: bool = False) -> Union[str, float]:
        """四舍五入（ROUND_HALF_UP：逢五进位）。

        :param number: Union[float, int], 待舍入数。
        :param n_digits: int, optional, 保留小数位，默认 0。
        :param if_return_float: bool, optional, True 返回 float，False 返回字符串，默认 False。
        :return: Union[str, float], 舍入结果。
        """
        dc_num = decimal.Decimal(str(number)).quantize(
            exp=decimal.Decimal(f"0.{'0' * n_digits}"), rounding=decimal.ROUND_HALF_UP
        )
        return float(dc_num) if if_return_float else str(dc_num)


class LotteryError(Exception):
    pass


# ----- progress bars: rich-based, brand gradient, non-TTY safe -----


class GradientBarColumn(ProgressColumn):
    """True-gradient bar: the filled part interpolates blue -> teal cell by cell.

    All styling lives as class attributes — subclass and override them to re-theme.
    """

    BAR_WIDTH = 30
    BAR_CHAR = "━"
    BAR_HALF = "╸"  # half-filled boundary cell, same trick pip uses
    BAR_TRACK_STYLE = "grey35"
    RGB_FROM = (0x40, 0x51, 0xB5)  # brand blue, matches the docs site / badge
    RGB_TO = (0x00, 0xC8, 0x96)  # teal reached at 100%
    BRAND_COLOUR = "#4051B5"  # spinner / description accent (same brand blue)

    def __init__(self, bar_width: Optional[int] = None):
        super().__init__()  # rich ProgressColumn init: required for get_table_column()
        self.bar_width = self.BAR_WIDTH if bar_width is None else bar_width

    @classmethod
    def lerp_colour(cls, fraction: float) -> str:
        """Interpolate RGB_FROM -> RGB_TO linearly (fraction 0..1) and return a hex colour."""
        rgb = tuple(round(a + (b - a) * fraction) for a, b in zip(cls.RGB_FROM, cls.RGB_TO))
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def render(self, task) -> Text:
        filled = round(self.bar_width * task.percentage / 100)
        text = Text()
        for i in range(self.bar_width):
            if filled and i < filled:
                text.append(self.BAR_CHAR, style=self.lerp_colour(i / max(filled - 1, 1)))
            elif i == filled and 0 < filled < self.bar_width:
                text.append(self.BAR_HALF, style=self.lerp_colour(i / self.bar_width))
            else:
                text.append(self.BAR_CHAR, style=self.BAR_TRACK_STYLE)
        return text


class _RichBar:
    """Thin single-task wrapper around rich Progress: context manager + advance/set_info."""

    def __init__(self, desc: str, unit: str, total: Optional[int], disable: bool):
        self._desc = desc
        self._unit = unit
        self._total = total
        self._disable = disable
        self._progress: Optional[Progress] = None
        self._task_id: Optional[TaskID] = None

    def __enter__(self) -> "_RichBar":
        self._progress = Progress(
            SpinnerColumn(style=GradientBarColumn.BRAND_COLOUR),
            TextColumn("[bold]{task.description}[/bold]"),
            GradientBarColumn(),
            MofNCompleteColumn(),
            TextColumn("[dim]{task.fields[unit]}[/dim]"),
            TextColumn("·", style="dim"),
            TimeElapsedColumn(),
            TimeRemainingColumn(compact=True),
            TextColumn("[dim]{task.fields[info]}[/dim]"),
            transient=False,  # pip-style: keep the finished bar row on screen
            console=Console(stderr=True),  # keep stdout clean for piping
            disable=self._disable,  # auto-off when stderr is not a terminal
        )
        self._progress.start()
        self._task_id = self._progress.add_task(self._desc, total=self._total, unit=self._unit, info="")
        return self

    def __exit__(self, *exc_info) -> None:
        assert self._progress is not None, "progress bar context manager not entered"
        self._progress.stop()

    def advance(self, n: int = 1) -> None:
        assert self._progress is not None and self._task_id is not None, "context manager not entered"
        self._progress.advance(self._task_id, advance=n)

    def set_info(self, text: str) -> None:
        """Update the trailing live-info field (e.g. the date window being fetched)."""
        assert self._progress is not None and self._task_id is not None, "context manager not entered"
        self._progress.update(self._task_id, info=text)

    def set_total(self, total: int) -> None:
        """Adjust the task total after the fact (e.g. an overlap-stop shows pages actually fetched)."""
        assert self._progress is not None and self._task_id is not None, "context manager not entered"
        self._progress.update(self._task_id, total=total)


def progress_bar(
    desc: str, unit: str = "items", total: Optional[int] = None, disable: Optional[bool] = None
) -> _RichBar:
    """Uniform progress-bar factory: brand gradient, live info, auto-off without a TTY.

    :param desc: str, task description, e.g. 'Downloading ssq'.
    :param unit: str, semantic unit shown after the counter, e.g. 'batches' / 'pages'.
    :param total: Optional[int], expected number of steps; None for an indeterminate bar.
    :param disable: Optional[bool], force on/off; defaults to off when stderr is not a TTY.
    :return: _RichBar, context manager with advance() / set_info().
    """
    disable = (not sys.stderr.isatty()) if disable is None else disable
    return _RichBar(desc=desc, unit=unit, total=total, disable=disable)
