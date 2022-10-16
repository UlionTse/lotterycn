# coding=utf-8
# author=uliontse
# datetime=2022/10/8_1:56

import sys
import time
import random
import functools
import urllib.parse
from typing import Union

import pandas
import loguru
import requests



loguru.logger.remove()
loguru.logger.add(sys.stdout, format='[{time:HH:mm:ss}] <lvl>{message}</lvl>', level='INFO')
loguru.logger.opt(colors=True)


class Tse:
    def __init__(self):
        self.author = 'Ulion.Tse'

    @staticmethod
    def time_stat(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            t1 = time.time()
            r = func(*args, **kwargs)
            t2 = time.time()
            loguru.logger.success('CostTime(fn: {}): {}s'.format(func.__name__, round((t2 - t1), 1)), style='braces')
            return r
        return _wrapper

    @staticmethod
    def get_headers(host_url, if_api=False, if_referer_for_host=True, if_ajax_for_api=True, if_json_for_api=False):
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
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


class ChinaWelfareLottery(Tse):
    def __init__(self):
        super().__init__()
        self.cwl_host_url = 'http://www.cwl.gov.cn'  # http
        self.cwl_api_url = 'http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice'  # http
        self.cwl_host_headers = self.get_headers(self.cwl_host_url, if_api=False, if_referer_for_host=True)
        self.cwl_api_headers = self.get_headers(self.cwl_api_url, if_api=True, if_ajax_for_api=True)
        self.cwl_ssq_qlc_3d_begin_date = '2013-01-01'
        self.cwl_kl8_begin_date = '2020-10-28'
        self.cwl_key_pool = ['name', 'code', 'date', 'red', 'blue', 'blue2']

    def cwl(self, lottery_name: str, **kwargs) -> Union[dict, pandas.DataFrame]:
        """
        https://www.cwl.gov.cn
        :param lottery_name: str, must in ('ssq', 'qlc', 'kl8', '3d'). # 双色球、七乐彩、快乐8、福彩3D
        :param **kwargs:
                :param is_detail_result: boolean, default True.
                :param timeout: float, default None.
                :param proxies: dict, default None.
                :param sleep_seconds: float, default `random.random()`.
        :return: str or list
        """
        is_detail_result = kwargs.get('is_detail_result', True)
        timeout = kwargs.get('timeout', None)
        proxies = kwargs.get('proxies', None)
        sleep_seconds = kwargs.get('sleep_seconds', random.random())
        with requests.Session() as session:
            _ = session.get(self.cwl_host_url, headers=self.cwl_host_headers, timeout=timeout, proxies=proxies)
            params = {
                'name': lottery_name, 'dayStart': '2022-01-01', 'dayEnd': '2022-05-31',
                'issueCount': '', 'issueStart': '', 'issueEnd': '',
            }
            r = session.get(self.cwl_api_url, params=params, headers=self.cwl_api_headers, timeout=timeout, proxies=proxies)
            data = r.json()

        return data if is_detail_result else pandas.DataFrame([{key: item[key] for key in self.cwl_key_pool} for item in data['result']])


if __name__ == '__main__':
    cwl = ChinaWelfareLottery()
    dd = cwl.cwl(lottery_name='ssq', is_detail_result=False)
    print(dd)
