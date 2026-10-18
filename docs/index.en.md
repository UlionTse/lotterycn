---
hide:
  - navigation
---

# LotteryCN

<div class="hero" markdown>

![LotteryCN](assets/lotterycn_logo.png){ .logo }

**A Python library for enjoyable analysis of Chinese welfare & sports lotteries** — official draw data, combinatorial odds & expected value, number-picking strategies with backtesting, and winning checks.

[Get Started](#quickstart){ .md-button .md-button--primary }
[API Reference](api/index.md){ .md-button }

</div>

<div class="grid cards" markdown>

- :material-database:{ .lg .middle } **Official data only**

    ---

    Winning numbers and full draw details (sales, prize pools, per-level results, province distribution) — straight from official channels, no third-party scrapers. Every prize rule is verified against the official game rules: see [Games & Rules](games.md).

- :material-calculator:{ .lg .middle } **Combinatorial odds & expectations**

    ---

    Exact counts for every prize tier; probabilities, expected values and return rates from official prize tables; instant ticket checking.

- :material-chart-line:{ .lg .middle } **Strategies & backtesting (core)**

    ---

    11 number-picking strategies + a composable shrink engine, with a built-in rolling backtest — every strategy matches random in expected value.

- :material-check-decagram:{ .lg .middle } **Full pipeline**

    ---

    Collect (cached incrementally) → analyze → predict → backtest → check.

</div>

## Quickstart

One full pipeline — collect (cached & refreshed incrementally) → analyze → predict → backtest → check:

```python
import lotterycn

df_ssq = lotterycn.load_history_data(lottery_name='ssq', if_cached=True, sleep_seconds=0.1)
stats = lotterycn.load_number_statistics(lottery_name='ssq', history=df_ssq)
print(lotterycn.load_prize_expectation(lottery_name='ssq'))

picks = lotterycn.load_predict_numbers(lottery_name='ssq', method='hot', amount=5)
results = lotterycn.backtest(lottery_name='ssq', methods=('random', 'hot'), window=10)
print(lotterycn.backtest_summary(results=results))

print(lotterycn.load_check_result(lottery_name='ssq', my_number='01,05,12,18,27,33|08', if_cached=True))
```

See the [API Reference](api/index.md) for details.

!!! warning "Honest disclaimer"

    Lottery draws are **independent random events**. Historical statistics cannot predict
    future draws — every strategy in this library has exactly the same expected value as
    random picking. Everything here is for statistical observation and entertainment.
    Play rationally (18+).
