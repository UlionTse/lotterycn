# API 参考

`lotterycn` 按流水线阶段暴露少量入口函数——均以 `lottery_name` 为首参，默认返回
`pandas.DataFrame`（明细模式的 list 变体见各自 docstring）。

| 模块 | 内容 | 关键函数 |
|---|---|---|
| [data](data.md) | 官方历史开奖与随机选号 | `load_history_data`、`load_random_data` |
| [odds](odds.md) | 各奖级概率、期望、复式投注 | `load_prize_odds`、`load_prize_expectation`、`load_dlt_compound_expectation` |
| [check](check.md) | 中奖校验 | `load_check_result` |
| [analysis](analysis.md) | 每号码频率与遗漏统计 | `load_number_statistics` |
| [predict](predict.md) | 11 个选号策略 | `load_predict_numbers` |
| [backtest](backtest.md) | 滚动窗口回测（对照随机基线） | `backtest`、`backtest_summary` |
| [draws](draws.md) | 销售额、奖池、各奖级结果、省级分布 | `load_draw_detail`、`load_prize_results`、`load_first_prize_by_province` |
| [cache](cache.md) | 本地 CSV 缓存与增量更新 | `load_cached_history_data`、`get_cache_path` |
| [cli](cli.md) | 控制台命令 | `lotterycn odds / expect / stats / predict / check / ...` |
