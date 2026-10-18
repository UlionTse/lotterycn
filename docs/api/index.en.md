# API Reference

`lotterycn` exposes a small set of entry-point functions — one group per pipeline
stage. All of them take `lottery_name` as the first parameter and return
`pandas.DataFrame` by default (detail-mode list variants are noted in their docstrings).

| Module | Contents | Key functions |
|---|---|---|
| [data](data.md) | Official draw history & random tickets | `load_history_data`, `load_random_data` |
| [odds](odds.md) | Prize odds, expected value, compound bets | `load_prize_odds`, `load_prize_expectation`, `load_dlt_compound_expectation` |
| [check](check.md) | Winning ticket check | `load_check_result` |
| [analysis](analysis.md) | Frequency & omission statistics per number | `load_number_statistics` |
| [predict](predict.md) | 11 number-picking strategies | `load_predict_numbers` |
| [backtest](backtest.md) | Rolling-window backtest vs the random baseline | `backtest`, `backtest_summary` |
| [draws](draws.md) | Sales, prize pools, per-level results, province distribution | `load_draw_detail`, `load_prize_results`, `load_first_prize_by_province` |
| [cache](cache.md) | Local CSV cache & incremental update | `load_cached_history_data`, `get_cache_path` |
| [cli](cli.md) | Console commands | `lotterycn odds / expect / stats / predict / check / ...` |
