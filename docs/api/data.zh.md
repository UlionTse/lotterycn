# data — 官方开奖数据

从 `cwl.gov.cn` 与 `lottery.gov.cn` 官方网站拉取 8 个彩种的历史开奖数据，输出统一格式的 `pandas.DataFrame`。

::: lotterycn.data
    options:
      members:
        - ChinaWelfareLottery
        - ChinaSportsLottery
        - ChinaLottery
        - lottery_pool
        - load_history_data
        - load_random_data
