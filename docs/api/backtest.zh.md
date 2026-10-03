# backtest — 策略回测

滚动窗口回测：用前 `window` 期历史驱动各策略出票，与下一期真实开奖比对命中数——把
predict.py 的免责声明变成可复现的实验，反复证明所有策略与 `random` 基线无差异；
`backtest_summary` 汇总各策略的平均命中供对比。

::: lotterycn.backtest
    options:
      members:
        - backtest
        - backtest_summary
