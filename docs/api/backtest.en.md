# backtest — Strategy backtesting

Rolling-window backtesting: each strategy is driven by the preceding `window` draws and
scored against the next real draw (red/blue hit counts) — a reproducible experiment that
keeps proving every strategy matches the `random` baseline. `backtest_summary` aggregates
per-strategy averages for the comparison.

::: lotterycn.backtest
    options:
      members:
        - backtest
        - backtest_summary
