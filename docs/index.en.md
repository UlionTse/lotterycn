---
hide:
  - navigation
---

# LotteryCN

<div class="hero" markdown>

![LotteryCN](assets/lotterycn_logo.png){ .logo }

**A Python library for enjoyable analysis of Chinese welfare & sports lotteries** — official draw data, combinatorial odds & expected value, number-picking strategies with backtesting, and winning checks.

[Get Started](#quickstart){ .md-button .md-button--primary }
[API Reference](api/odds.md){ .md-button }

</div>

Every prize rule, odds table and fixed prize amount in this library is verified against the **official game rules** published on `cwl.gov.cn` (China Welfare Lottery) and `lottery.gov.cn` (China Sports Lottery). See [Games & Rules](games.md) for the complete official source table.

<div class="grid cards" markdown>

- :material-chart-line:{ .lg .middle } **Strategies & backtesting (core)**

    ---

    11 number-picking strategies + a composable shrink engine, with a built-in rolling backtest — every strategy matches random in expected value.

- :material-database:{ .lg .middle } **Official data only**

    ---

    Winning numbers and full draw details (sales, prize pools, per-level results, province distribution) — straight from official channels, no third-party scrapers.

- :material-calculator:{ .lg .middle } **Combinatorial odds & expectations**

    ---

    Exact counts for every prize tier; probabilities, expected values and return rates from official prize tables; instant ticket checking.

- :material-check-decagram:{ .lg .middle } **Full pipeline**

    ---

    Collect (cached incrementally) → analyze → predict → backtest → check.

</div>

## Quickstart

```python
from lotterycn import (backtest, backtest_summary, load_history_data,
                       load_number_statistics, load_predict_numbers,
                       load_check_result, load_prize_expectation)

df = load_history_data('ssq', if_cached=True)          # collect (cached, incremental)
stats = load_number_statistics('ssq', history=df)      # analyze
picks = load_predict_numbers('ssq', method='hot', amount=5)  # strategy sandbox
print(load_prize_expectation('ssq'))                   # odds & expected value
print(backtest_summary(backtest(methods=('random', 'hot'),
                                lottery_name='ssq', window=100)))
```

See the [API Reference](api/odds.md) for details.

!!! warning "Honest disclaimer"

    Lottery draws are **independent random events**. Historical statistics cannot predict
    future draws — every strategy in this library has exactly the same expected value as
    random picking. Everything here is for statistical observation and entertainment.
    Play rationally (18+).
