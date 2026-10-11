# coding=utf-8
# author=Ulion.Tse

import sys
import time
import random
from typing import Optional, Union

import pandas
import requests

from .utils import LotteryError, Tse, progress_bar

# display names shown as lottery_zh_name (the raw APIs carry them in their name fields)
GAME_ZH_NAMES = {
    "ssq": "双色球",
    "qlc": "七乐彩",
    "kl8": "快乐8",
    "3d": "福彩3D",
    "dlt": "超级大乐透",
    "pls": "排列3",
    "plw": "排列5",
    "qxc": "7星彩",
}

# pandas.options.display.max_columns = None
# pandas.options.display.max_rows = None


class ChinaWelfareLottery(Tse):
    def __init__(self):
        super().__init__()
        self.session = None
        self.cwl_projects = ("ssq", "qlc", "kl8", "3d")
        self.cwl_data_cols = ["name", "code", "date", "red", "blue"]  # 'blue2'
        self.cwl_host_url = "http://www.cwl.gov.cn"  # http
        self.cwl_api_url = "http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"  # http
        self.cwl_host_headers = self.get_headers(self.cwl_host_url, if_api=False, if_referer_for_host=True)
        self.cwl_api_headers = self.get_headers(self.cwl_api_url, if_api=True, if_ajax_for_api=True)
        self.cwl_kl8_history_begin_date = "2020-10-28"
        self.cwl_ssq_qlc_3d_history_begin_date = "2013-01-01"
        self.cwl_max_batch = 99

    def check_params(self, lottery_name: str, begin_date: str, end_date: str) -> tuple:
        """校验并规整福彩系请求参数。

        :param lottery_name: str, must in ('ssq', 'qlc', 'kl8', '3d').
        :param begin_date: str, 起始日期（含）。
        :param end_date: str, 结束日期（含）。
        :return: tuple, 规整后的 (lottery_name, begin_date, end_date)：日期范围收敛到
            各彩种最早可得日期与今天。
        """
        if lottery_name not in self.cwl_projects:
            raise LotteryError(f"unsupported welfare lottery name {lottery_name!r}, must be one of {self.cwl_projects}")
        if begin_date > end_date or begin_date > self.today_date:
            raise LotteryError(
                f"invalid date range: begin_date ({begin_date}) must be <= end_date ({end_date}) and not in the future"
            )
        if lottery_name == "kl8":
            begin_date = self.cwl_kl8_history_begin_date if begin_date < self.cwl_kl8_history_begin_date else begin_date
        else:
            begin_date = (
                self.cwl_ssq_qlc_3d_history_begin_date
                if begin_date < self.cwl_ssq_qlc_3d_history_begin_date
                else begin_date
            )
        end_date = self.today_date if end_date > self.today_date else end_date
        return lottery_name, begin_date, end_date

    def cwl(
        self, lottery_name: str = "ssq", begin_date: str = "2013-01-01", end_date: str = "3022-01-01", **kwargs
    ) -> Union[list, pandas.DataFrame]:
        """
        https://www.cwl.gov.cn
        http://www.cwl.gov.cn/fcpz/yxjs
        :param lottery_name: str, must in ('ssq', 'qlc', 'kl8', '3d'). # 双色球、七乐彩、快乐8、福彩3D
        :param begin_date: str, eg: '2022-01-01'.
        :param end_date: str, eg: '2022-01-01'.
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param timeout: float, default 15.
                :param max_retries: int, default 3.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: list or pandas.DataFrame
        """

        is_detail_result = kwargs.get("is_detail_result", False)
        lottery_name, begin_date, end_date = self.check_params(lottery_name, begin_date, end_date)

        durings = self.get_during_list(begin_date, end_date, freq=f"{self.cwl_max_batch}D")

        sleep_seconds = kwargs.get("sleep_seconds", random.random())

        data: list = []
        with progress_bar(f"Downloading {lottery_name}", unit="batches", total=len(range(0, len(durings), 2))) as bar:
            for i in range(0, len(durings), 2):
                result = self._cwl(lottery_name=lottery_name, begin_date=durings[i], end_date=durings[i + 1], **kwargs)
                if is_detail_result:
                    data.extend((result.get("result") or [])[::-1])  # append batches reversed to ascending order
                else:
                    data.append(result)
                bar.advance()
                bar.set_info(f"{durings[i]} -> {durings[i + 1]}")
                if i + 2 < len(durings):
                    time.sleep(sleep_seconds)  # no sleep after the final batch
        if is_detail_result:
            return data
        if not data:
            return pandas.DataFrame()
        return pandas.concat(data, axis=0).sort_values(by=["code"]).reset_index(drop=True)

    def _cwl(self, lottery_name: str, begin_date: str, end_date: str, **kwargs) -> Union[dict, pandas.DataFrame]:
        is_detail_result = kwargs.get("is_detail_result", False)
        timeout = kwargs.get("timeout", 15)
        proxies = kwargs.get("proxies", None)
        max_retries = kwargs.get("max_retries", 3)

        if not self.session:
            self.session = requests.Session()
            _ = self.session.get(self.cwl_host_url, headers=self.cwl_host_headers, timeout=timeout, proxies=proxies)

        params = {
            "name": lottery_name,
            "dayStart": begin_date,
            "dayEnd": end_date,
            "issueCount": "",
            "issueStart": "",
            "issueEnd": "",
        }
        data = self.fetch_json(
            self.cwl_api_url,
            params=params,
            headers=self.cwl_api_headers,
            timeout=timeout,
            proxies=proxies,
            max_retries=max_retries,
            source="cwl",
        )

        if is_detail_result:
            return data
        rows = data.get("result") or []
        if rows:
            return pandas.DataFrame([{key: item[key] for key in self.cwl_data_cols} for item in rows])
        # a date window may legitimately contain no draws (e.g. incremental refresh on a
        # non-draw day): keep the expected columns so downstream concat/sort still work
        return pandas.DataFrame(columns=self.cwl_data_cols)


class ChinaSportsLottery(Tse):
    def __init__(self):
        super().__init__()
        self.session = None
        self.csl_projects = {"dlt": "85", "pls": "35", "plw": "350133", "qxc": "04"}
        self.csl_data_cols = ["lotteryGameName", "lotteryDrawNum", "lotteryDrawTime", "lotteryDrawResult"]
        self.csl_host_url = "https://www.lottery.gov.cn/"
        self.csl_api_url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
        self.csl_project_url = "https://www.lottery.gov.cn/tz_kj.json"
        self.csl_referer_url = "https://static.sporttery.cn"
        self.csl_host_headers = self.get_headers(self.csl_host_url, if_api=False, if_referer_for_host=True)
        self.csl_api_headers = self.get_headers(self.csl_referer_url, if_api=True, if_ajax_for_api=True)
        self.csl_pages = None
        self.csl_max_batch = 30

    def get_params(self, game_no: str = "85", page_no: int = 1) -> dict:
        """构造体彩分页查询参数。

        :param game_no: str, 体彩游戏编号（官方接口的 gameNo）。
        :param page_no: int, 页码，从 1 起。
        :return: dict, 官方接口所需的查询参数。
        """
        return {"gameNo": game_no, "pageNo": page_no, "pageSize": self.csl_max_batch, "provinceId": 0, "isVerify": 1}

    def csl_warmup(self, timeout: float, proxies: Optional[dict], max_retries: int) -> int:
        """建立会话并探测体彩历史总页数（幂等；返回总页数，调用方据此翻页）。"""
        if not self.session or not self.csl_pages:
            self.session = requests.Session()
            _ = self.session.get(self.csl_host_url, headers=self.csl_host_headers, timeout=timeout, proxies=proxies)
            _ = self.session.get(self.csl_project_url, headers=self.csl_host_headers, timeout=timeout, proxies=proxies)
            pages_json = self.fetch_json(
                self.csl_api_url,
                params=self.get_params(),
                headers=self.csl_api_headers,
                timeout=timeout,
                proxies=proxies,
                max_retries=max_retries,
                source="csl",
            )
            self.csl_pages = (pages_json.get("value") or {}).get("pages")
            if not isinstance(self.csl_pages, int) or self.csl_pages < 1:
                raise LotteryError(f"csl api unexpected pages: {self.csl_pages!r}")
        return self.csl_pages

    def csl(self, lottery_name: str = "dlt", **kwargs) -> Union[list, pandas.DataFrame]:
        """
        https://www.lottery.gov.cn
        https://www.lottery.gov.cn/bzzx/yxgz
        大乐透、排列3、排列5、7星彩、双色球、七乐彩、快乐8、福彩3D
        :param lottery_name: str, must in ('dlt', 'pls', 'plw', 'qxc'). # 大乐透、排列3、排列5、7星彩
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param timeout: float, default 15.
                :param max_retries: int, default 3.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: list or pandas.DataFrame
        """
        is_detail_result = kwargs.get("is_detail_result", False)
        timeout = kwargs.get("timeout", 15)
        proxies = kwargs.get("proxies", None)
        max_retries = kwargs.get("max_retries", 3)
        if lottery_name not in self.csl_projects:
            raise LotteryError(f"unsupported sports lottery name {lottery_name!r}, must be one of {self.csl_projects}")

        total_pages = self.csl_warmup(timeout=timeout, proxies=proxies, max_retries=max_retries)

        sleep_seconds = kwargs.get("sleep_seconds", random.random())

        data: list = []
        rows_fetched = 0

        with progress_bar(f"Downloading {lottery_name}", unit="pages", total=total_pages) as bar:
            for page_no in range(1, total_pages + 1):
                result = self._csl(lottery_name=lottery_name, page_no=page_no, **kwargs)
                if is_detail_result:
                    data.extend(result["value"]["list"])
                else:
                    data.append(result)
                rows_fetched += len(result)
                bar.advance()
                bar.set_info(f"{rows_fetched} rows")
                if page_no < total_pages:
                    time.sleep(sleep_seconds)  # no sleep after the final page
        if is_detail_result:
            return data[::-1]
        if not data:
            return pandas.DataFrame()
        return pandas.concat(data, axis=0)[::-1].reset_index(drop=True)

    def _csl(self, lottery_name: str, page_no: int, **kwargs) -> Union[dict, pandas.DataFrame]:
        is_detail_result = kwargs.get("is_detail_result", False)
        timeout = kwargs.get("timeout", 15)
        proxies = kwargs.get("proxies", None)
        max_retries = kwargs.get("max_retries", 3)

        params = self.get_params(game_no=self.csl_projects[lottery_name], page_no=page_no)
        data = self.fetch_json(
            self.csl_api_url,
            params=params,
            headers=self.csl_api_headers,
            timeout=timeout,
            proxies=proxies,
            max_retries=max_retries,
            source="csl",
        )

        if is_detail_result:
            return data
        rows = data["value"]["list"]
        if rows:
            return pandas.DataFrame([{key: item[key] for key in self.csl_data_cols} for item in rows])
        return pandas.DataFrame(columns=self.csl_data_cols)  # symmetric guard: empty page keeps columns


class ChinaLottery(ChinaWelfareLottery, ChinaSportsLottery):
    def __init__(self):
        super().__init__()
        self.cl_projects = ("dlt", "pls", "plw", "qxc", "ssq", "qlc", "kl8", "3d")
        self.cl_cols = [
            "lottery_name",
            "lottery_zh_name",
            "lottery_order",
            "lottery_date",
            "lottery_red",
            "lottery_blue",
        ]
        self.cl_has_blue_projects = ["ssq", "qlc", "dlt", "qxc"]

    def load_history_data(self, lottery_name: str, **kwargs) -> Union[list, pandas.DataFrame]:
        """Load draw history for all 8 games as a tidy DataFrame.

        Fetches from the official websites (cwl.gov.cn / lottery.gov.cn) with
        retry/backoff; supports incremental CSV caching.

        !!! note "中文说明"

            拉取 8 个彩种（大乐透/排列3/排列5/7星彩/双色球/七乐彩/快乐8/福彩3D）
            的历史开奖数据，输出统一列结构的 DataFrame
            （lottery_name / lottery_order / lottery_date / lottery_red / lottery_blue）。

            - `if_cached=True` 启用本地 CSV 缓存与增量更新（目录默认
              `~/.lotterycn/history`，可用 `cache_dir` 或环境变量
              `lotterycn_cache_dir` 覆盖）；
            - 福彩系支持 `begin_date` 日期区间增量，体彩系全量刷新后去重。

        :param lottery_name: str, must in ('dlt', 'pls', 'plw', 'qxc', 'ssq', 'qlc', 'kl8', '3d').
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param if_cached: boolean, default False. Enable local CSV cache + incremental update.
                :param cache_dir: str, default None (`~/.lotterycn/history`).
                :param begin_date: str, welfare games only.
                :param timeout: float, default 15.
                :param max_retries: int, default 3.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: list or pandas.DataFrame
        """
        is_detail_result = kwargs.get("is_detail_result", False)
        if kwargs.get("if_cached", False):
            from .cache import load_cached_history_data

            return load_cached_history_data(lottery_name=lottery_name, **kwargs)
        if lottery_name in self.cwl_projects:
            data = self.cwl(lottery_name=lottery_name, **kwargs)
        else:
            data = self.csl(lottery_name=lottery_name, **kwargs)
        return data if is_detail_result else self.get_history_data_dataframe(data, lottery_name)

    def load_random_data(self, lottery_name: str = "ssq", amount: int = 1, **kwargs) -> Union[list, pandas.DataFrame]:
        """
        https://www.lottery.gov.cn, https://www.cwl.gov.cn
        https://www.lottery.gov.cn/bzzx/yxgz, https://www.cwl.gov.cn/fcpz/yxjs
        大乐透、排列3、排列5、7星彩、双色球、七乐彩、快乐8、福彩3D
        :param lottery_name: str, default 'ssq'. must in ('dlt', 'pls', 'plw', 'qxc', 'ssq', 'qlc', 'kl8', '3d')
        :param amount: int, default 1.
        :param **kwargs:
                :param is_detail_result: boolean, default False.
        :return: list or pandas.DataFrame
        """
        is_detail_result = kwargs.get("is_detail_result", False)
        if amount < 1:
            raise LotteryError(f"amount ({amount}) must be >= 1")
        data_list = []
        with progress_bar(f"Generating {lottery_name}", unit="tickets", total=amount, disable=amount < 10) as bar:
            for _ in range(amount):
                data_list.append(self.get_random_lottery(lottery_name))
                bar.advance()
        return data_list if is_detail_result else self.get_random_data_dataframe(data_list, lottery_name, amount)

    def get_random_base(
        self, k: int, max_n: int, min_n: int = 1, if_sort: bool = True, if_str: bool = True
    ) -> Union[str, list]:
        """基础随机采样：从 [min_n, max_n] 中不重复抽取 k 个。

        :param k: int, 抽取个数。
        :param max_n: int, 号码上限。
        :param min_n: int, optional, 号码下限，默认 1。
        :param if_sort: bool, optional, 是否升序排序，默认 True。
        :param if_str: bool, optional, True 返回逗号连接字符串，False 返回 list，默认 True。
        :return: Union[str, list], 采样结果。
        """
        lotts = random.sample(range(min_n, max_n + 1), k=k)
        lotts = sorted(lotts) if if_sort else lotts
        return ",".join(map(str, lotts)) if if_str else lotts

    def get_random_lottery(self, lottery_name: str = "ssq") -> list:
        """按彩种规则生成一注随机号码（范围 / 去重 / 红蓝分区 / 位数）。

        :param lottery_name: str, 彩种代码。
        :return: list, 各区号码（与 data.py 的 lottery_red / lottery_blue 拆分一致）。
        """
        if lottery_name == "ssq":
            data = [self.get_random_base(k=6, max_n=33), self.get_random_base(k=1, max_n=16)]
        elif lottery_name == "qlc":
            lotts = self.get_random_base(k=8, max_n=30, if_sort=False, if_str=False)
            data = [",".join(map(str, sorted(lotts[:-1]))), str(lotts[-1])]
        elif lottery_name == "kl8":
            data = [self.get_random_base(k=20, max_n=80)]
        elif lottery_name in ("3d", "pls"):
            data = [",".join(str(self.get_random_base(k=1, max_n=9, min_n=0)) for _ in range(3))]
        elif lottery_name == "plw":
            data = [",".join(str(self.get_random_base(k=1, max_n=9, min_n=0)) for _ in range(5))]
        elif lottery_name == "dlt":
            data = [self.get_random_base(k=5, max_n=35), self.get_random_base(k=2, max_n=12)]
        elif lottery_name == "qxc":
            data = [
                ",".join(str(self.get_random_base(k=1, max_n=9, min_n=0)) for _ in range(6)),
                self.get_random_base(k=1, max_n=14, min_n=0),
            ]
        else:
            raise LotteryError(f"unsupported lottery name {lottery_name!r} for random generation")
        return data

    def get_random_data_dataframe(self, data_list: list, lottery_name: str, amount: int) -> pandas.DataFrame:
        """把随机号码列表规整为与历史开奖同列结构的 DataFrame。

        :param data_list: list, get_random_lottery 产出的号码列表。
        :param lottery_name: str, 彩种代码。
        :param amount: int, 注数。
        :return: pandas.DataFrame, 列与 cl_cols 一致（lottery_order 为 0..amount-1）。
        """
        if lottery_name in self.cl_has_blue_projects:
            data = pandas.DataFrame(data_list, columns=["lottery_red", "lottery_blue"])
        else:
            data = pandas.DataFrame(data_list, columns=["lottery_red"])
            data["lottery_blue"] = ""  # no-blue games keep an empty blue column for schema parity
        data.insert(0, "lottery_date", "")
        data.insert(0, "lottery_order", range(amount))
        data.insert(0, "lottery_zh_name", GAME_ZH_NAMES.get(lottery_name, ""))
        data.insert(0, "lottery_name", lottery_name)
        return data[self.cl_cols]

    def get_history_data_dataframe(self, data_frame: pandas.DataFrame, lottery_name: str) -> pandas.DataFrame:
        """把官方接口原始记录规整为统一列结构的历史 DataFrame。

        :param data_frame: pandas.DataFrame, 官方接口返回的原始记录。
        :param lottery_name: str, 彩种代码（体彩系需从空格分隔串拆分前区/后区列）。
        :return: pandas.DataFrame, 列与 cl_cols 一致。
        """
        if lottery_name in self.csl_projects:
            data = pandas.DataFrame(data_frame.to_numpy(), columns=self.csl_data_cols)
            data = data.rename(
                columns={
                    "lotteryGameName": "lottery_name",
                    "lotteryDrawNum": "lottery_order",
                    "lotteryDrawTime": "lottery_date",
                    "lotteryDrawResult": "lottery_red",
                }
            )
            if lottery_name == "dlt":
                data["lottery_blue"] = data["lottery_red"].str.split(" ").str[-2:].str.join(",")
                data["lottery_red"] = data["lottery_red"].str.split(" ").str[:-2].str.join(",")
            elif lottery_name == "qxc":
                data["lottery_blue"] = data["lottery_red"].str.split(" ").str[-1:].str.join(",")
                data["lottery_red"] = data["lottery_red"].str.split(" ").str[:-1].str.join(",")
            else:
                data["lottery_red"] = data["lottery_red"].str.split(" ").str.join(",")
        else:
            data = pandas.DataFrame(data_frame.to_numpy(), columns=self.cwl_data_cols)
            data = data.rename(
                columns={
                    "name": "lottery_name",
                    "code": "lottery_order",
                    "date": "lottery_date",
                    "red": "lottery_red",
                    "blue": "lottery_blue",
                }
            )
        # keep the API display name ('双色球'/'超级大乐透') as lottery_zh_name, then
        # canonicalise lottery_name to the game code — the rest of the library keys on codes
        zh_names = data["lottery_name"]
        data["lottery_name"] = lottery_name
        data.insert(1, "lottery_zh_name", zh_names)
        # the official CWL API carries a weekday suffix in draw dates ("2026-10-08(四)");
        # keep the ISO prefix only so downstream consumers (cache, user code) see clean dates
        data["lottery_date"] = (
            data["lottery_date"]
            .astype("string")
            .str.extract(r"(\d{4}-\d{2}-\d{2})", expand=False)
            .fillna(data["lottery_date"])
        )
        return data


# ----- assembly：默认客户端与模块级 API（上游惯例：装配区置于文件末尾）-----
_cl = ChinaLottery()
load_random_data = _cl.load_random_data
load_history_data = _cl.load_history_data

lottery_pool = _cl.cl_projects
sys.stderr.write(f"Support lottery_pool {lottery_pool} only.\n")
