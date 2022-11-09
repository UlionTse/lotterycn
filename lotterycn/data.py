# coding=utf-8
# author=uliontse

import time
import datetime
import random
import urllib.parse
from typing import Union

import tqdm
import numpy
import pandas
import requests


# pandas.options.display.max_columns = None
# pandas.options.display.max_rows = None


class Tse:
    def __init__(self):
        self.author = 'Ulion.Tse'
        self.today_date = self.get_date(fake_today='today', move_days=0, date_format='%Y-%m-%d')

    @staticmethod
    def get_headers(host_url, if_api=False, if_referer_for_host=True, if_ajax_for_api=True, if_json_for_api=False):
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
        url_path = urllib.parse.urlparse(host_url).path
        host_headers = {
            'Referer' if if_referer_for_host else 'Host': host_url,
            "User-Agent": user_agent,
        }
        api_headers = {
            'Origin': host_url.split(url_path)[0] if url_path else host_url,
            'Referer': host_url,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            "User-Agent": user_agent,
        }
        if if_api and not if_ajax_for_api:
            api_headers.pop('X-Requested-With')
            api_headers.update({'Content-Type': 'text/plain'})
        if if_api and if_json_for_api:
            api_headers.update({'Content-Type': 'application/json'})
        return host_headers if not if_api else api_headers

    def get_date(self, fake_today='today', move_days=0, date_format='%Y-%m-%d'):
        fake_today = datetime.date.today() if fake_today == 'today' else datetime.datetime.strptime(fake_today, date_format)
        return (fake_today + datetime.timedelta(days=move_days)).strftime(date_format)

    def get_during_list(self, begin_date, end_date, freq='1D'):
        pd_dates = pandas.date_range(start=begin_date, end=end_date, freq=freq, inclusive='neither')
        durings = numpy.array([[str(x)[:10], self.get_date(fake_today=str(x)[:10], move_days=1)] for x in pd_dates]).flatten().tolist()
        return [begin_date] + durings + [end_date]


class LotteryError(Exception):
    pass


class ChinaWelfareLottery(Tse):
    def __init__(self):
        super().__init__()
        self.session = None
        self.cwl_projects = ('ssq', 'qlc', 'kl8', '3d')
        self.cwl_data_cols = ['name', 'code', 'date', 'red', 'blue', 'blue2']
        self.cwl_host_url = 'http://www.cwl.gov.cn'  # http
        self.cwl_api_url = 'http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice'  # http
        self.cwl_host_headers = self.get_headers(self.cwl_host_url, if_api=False, if_referer_for_host=True)
        self.cwl_api_headers = self.get_headers(self.cwl_api_url, if_api=True, if_ajax_for_api=True)
        self.cwl_kl8_history_begin_date = '2020-10-28'
        self.cwl_ssq_qlc_3d_history_begin_date = '2013-01-01'
        self.cwl_max_batch = 99

    def check_params(self, lottery_name: str, begin_date: str, end_date: str) -> tuple:
        if lottery_name not in self.cwl_projects:
            raise LotteryError
        if begin_date > end_date or begin_date > self.today_date:
            raise LotteryError
        if lottery_name == 'kl8':
            begin_date = self.cwl_kl8_history_begin_date if begin_date < self.cwl_kl8_history_begin_date else begin_date
        else:
            begin_date = self.cwl_ssq_qlc_3d_history_begin_date if begin_date < self.cwl_ssq_qlc_3d_history_begin_date else begin_date
        end_date = self.today_date if end_date > self.today_date else end_date
        return lottery_name, begin_date, end_date

    def cwl(self,
            lottery_name: str = 'ssq',
            begin_date: str = '2013-01-01',
            end_date: str = '3022-01-01',
            **kwargs
            ) -> Union[list, pandas.DataFrame]:
        """
        https://www.cwl.gov.cn
        http://www.cwl.gov.cn/fcpz/yxjs
        :param lottery_name: str, must in ('ssq', 'qlc', 'kl8', '3d'). # 双色球、七乐彩、快乐8、福彩3D
        :param begin_date: str, eg: '2022-01-01'.
        :param end_date: str, eg: '2022-01-01'.
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: list or pandas.DataFrame
        """

        is_detail_result = kwargs.get('is_detail_result', False)
        lottery_name, begin_date, end_date = self.check_params(lottery_name, begin_date, end_date)

        durings = self.get_during_list(begin_date, end_date, freq=f'{self.cwl_max_batch}D')
        data = [] if is_detail_result else pandas.DataFrame()
        for i in tqdm.tqdm(range(0, len(durings), 2), desc=f'Downloading <{lottery_name}>', ncols=80):
            result = self._cwl(lottery_name=lottery_name, begin_date=durings[i], end_date=durings[i+1], **kwargs)
            data = data + result['result'][::-1] if is_detail_result else pandas.concat([data, result.sort_values(by=['code'])], axis=0)
        return data if is_detail_result else data.reset_index(drop=True)

    def _cwl(self, lottery_name: str, begin_date: str, end_date: str, **kwargs) -> Union[dict, pandas.DataFrame]:
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())

        if not self.session:
            self.session = requests.Session()
            _ = self.session.get(self.cwl_host_url, headers=self.cwl_host_headers, timeout=timeout, proxies=proxies)

        params = {
            'name': lottery_name, 'dayStart': begin_date, 'dayEnd': end_date,
            'issueCount': '', 'issueStart': '', 'issueEnd': '',
        }
        r = self.session.get(self.cwl_api_url, params=params, headers=self.cwl_api_headers, timeout=timeout, proxies=proxies)
        data = r.json()
        time.sleep(sleep_seconds)
        return data if is_detail_result else pandas.DataFrame([{key: item[key] for key in self.cwl_data_cols} for item in data['result']])


class ChinaSportsLottery(Tse):
    def __init__(self):
        super().__init__()
        self.session = None
        self.csl_projects = {'dlt': '85', 'pls': '35', 'plw': '350133', 'qxc': '04'}
        self.csl_data_cols = ['lotteryGameName', 'lotteryDrawNum', 'lotteryDrawTime', 'lotteryDrawResult']
        self.csl_host_url = 'https://www.lottery.gov.cn/'
        self.csl_api_url = 'https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry'
        self.csl_project_url = 'https://www.lottery.gov.cn/tz_kj.json'
        self.csl_referer_url = 'https://static.sporttery.cn'
        self.csl_host_headers = self.get_headers(self.csl_host_url, if_api=False, if_referer_for_host=True)
        self.csl_api_headers = self.get_headers(self.csl_referer_url, if_api=True, if_ajax_for_api=True)
        self.csl_pages = None
        self.csl_max_batch = 30

    def get_params(self, game_no: int = 85, page_no: int = 1) -> dict:
        return {'gameNo': game_no, 'pageNo': page_no, 'pageSize': self.csl_max_batch, 'provinceId': 0, 'isVerify': 1}

    def csl(self, lottery_name: str = 'dlt', **kwargs) -> Union[list, pandas.DataFrame]:
        """
        https://www.lottery.gov.cn
        https://www.lottery.gov.cn/bzzx/yxgz
        :param lottery_name: str, must in ('dlt', 'pls', 'plw', 'qxc'). # 大乐透、排列3、排列5、7星彩
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: list or pandas.DataFrame
        """
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        if lottery_name not in self.csl_projects:
            raise LotteryError

        if not self.session or not self.csl_pages:
            self.session = requests.Session()
            _ = self.session.get(self.csl_host_url, headers=self.csl_host_headers, timeout=timeout, proxies=proxies)
            _ = self.session.get(self.csl_project_url, headers=self.csl_host_headers, timeout=timeout, proxies=proxies)
            page_r = self.session.get(self.csl_api_url, params=self.get_params(), headers=self.csl_api_headers, timeout=timeout, proxies=proxies)
            self.csl_pages = page_r.json()['value']['pages']

        data = [] if is_detail_result else pandas.DataFrame()
        for page_no in tqdm.tqdm(range(1, self.csl_pages + 1), desc=f'Downloading <{lottery_name}>', ncols=80):
            result = self._csl(lottery_name=lottery_name, page_no=page_no, **kwargs)
            data = data + result['value']['list'] if is_detail_result else pandas.concat([data, result], axis=0)
        return data[::-1] if is_detail_result else data[::-1].reset_index(drop=True)

    def _csl(self, lottery_name: str, page_no: int, **kwargs) -> Union[dict, pandas.DataFrame]:
        is_detail_result = kwargs.get('is_detail_result', False)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())

        params = self.get_params(game_no=self.csl_projects[lottery_name], page_no=page_no)
        r = self.session.get(self.csl_api_url, params=params, headers=self.csl_api_headers, timeout=timeout, proxies=proxies)
        r.raise_for_status()
        data = r.json()
        time.sleep(sleep_seconds)
        return data if is_detail_result else pandas.DataFrame([{key: item[key] for key in self.csl_data_cols} for item in data['value']['list']])


class ChinaLottery(ChinaWelfareLottery, ChinaSportsLottery):
    def __init__(self):
        super().__init__()

    def load_history_data(self, lottery_name: str, **kwargs):
        """
        https://www.lottery.gov.cn, https://www.cwl.gov.cn
        https://www.lottery.gov.cn/bzzx/yxgz, https://www.cwl.gov.cn/fcpz/yxjs
        大乐透、排列3、排列5、7星彩、双色球、七乐彩、快乐8、福彩3D
        :param lottery_name: str, must in ('dlt', 'pls', 'plw', 'qxc', 'ssq', 'qlc', 'kl8', '3d').
        :param **kwargs:
                :param is_detail_result: boolean, default False.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: list or pandas.DataFrame
        """
        if lottery_name in self.cwl_projects:
            return self.cwl(lottery_name=lottery_name, **kwargs)
        return self.csl(lottery_name=lottery_name, **kwargs)

    def load_random_data(self, lottery_name: str = 'ssq', amount: int = 1) -> list:
        """
        https://www.lottery.gov.cn, https://www.cwl.gov.cn
        https://www.lottery.gov.cn/bzzx/yxgz, https://www.cwl.gov.cn/fcpz/yxjs
        大乐透、排列3、排列5、7星彩、双色球、七乐彩、快乐8、福彩3D
        :param lottery_name: str, default 'ssq'. must in ('dlt', 'pls', 'plw', 'qxc', 'ssq', 'qlc', 'kl8', '3d')
        :param amount: int, default 1.
        :return: list
        """
        if amount < 1:
            raise LotteryError
        return [self.get_random_lottery(lottery_name) for _ in tqdm.tqdm(range(amount), desc=f'Generating <{lottery_name}>', ncols=80)]

    def get_random_base(self, k: int, max_n: int, min_n: int = 1, if_sort: bool = True, if_str: bool = True) -> Union[str, list]:
        lotts = random.sample(range(min_n, max_n + 1), k=k)
        lotts = sorted(lotts) if if_sort else lotts
        return ','.join(map(str, lotts)) if if_str else lotts

    def get_random_lottery(self, lottery_name: str = 'ssq') -> list:
        if lottery_name == 'ssq':
            return [self.get_random_base(k=6, max_n=33), self.get_random_base(k=1, max_n=16)]
        elif lottery_name == 'qlc':
            lotts = self.get_random_base(k=8, max_n=30, if_sort=False, if_str=False)
            return [','.join(map(str, sorted(lotts[:-1]))), str(lotts[-1])]
        elif lottery_name == 'kl8':
            return [self.get_random_base(k=20, max_n=80)]
        elif lottery_name in ('3d', 'pls'):
            return [','.join(self.get_random_base(k=1, max_n=9, min_n=0) for _ in range(3))]
        elif lottery_name == 'plw':
            return [','.join(self.get_random_base(k=1, max_n=9, min_n=0) for _ in range(5))]
        elif lottery_name == 'dlt':
            return [self.get_random_base(k=5, max_n=35), self.get_random_base(k=2, max_n=12)]
        elif lottery_name == 'qxc':
            return [','.join(self.get_random_base(k=1, max_n=9, min_n=0) for _ in range(5)), self.get_random_base(k=1, max_n=14, min_n=0)]
        else:
            raise LotteryError


_cl = ChinaLottery()
load_random_data = _cl.load_random_data
load_history_data = _cl.load_history_data
