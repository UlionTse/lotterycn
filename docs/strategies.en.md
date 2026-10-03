# Strategies (for entertainment only)

`lotterycn.predict` ships eleven number-generation strategies plus a composable filter engine. **None of them has any predictive power** — draws are independent random events, so every strategy has exactly the same expected value as the `random` baseline. This module exists for statistical observation and entertainment.

| Method | Aliases | School | Idea |
|---|---|---|---|
| `random` | — | baseline | Uniform random — every other strategy should be compared against it |
| `frequency` | `hot` / `cold` | trend charts | Pick numbers by appearance frequency over a sliding window (`recent_n`), `explore_ratio` controls determinism |
| `omission` | `chase` | trend charts | Mean-reversion chase: score = current omission / average omission ("hot-then-cold" numbers rank highest) |
| `deviation` | `chisq` | statistics | Chi-square deviation (observed − expected)² / expected; `side='hot'` or `'cold'` |
| `repeat` | — | community | Repeat / neighbor (±1) / jump (second-last draw ±1) weighting — the repeat / neighbor / jump-number playbook |
| `trend` | — | stock framework | Sum moving-average channel: random candidates kept only if their sum falls inside MA ± k·σ |
| `tail` | — | trend charts | Two-level picks: choose tail digits (number % 10) by frequency, then numbers within those tails |
| `markov` | — | sequence | First-order transition sampling P(appear now \| appeared/not last draw) — collapses to frequency under independence |
| `markov2` | — | sequence | Second-order transition (last two draws, 4 states) — shows how higher-order states collapse to uniform through sparsity |
| `filter` | — | shape school | Composable shrink engine: `sum_range`, `odd_range`, `prime_range`, `zone_ratio`, `mod3_range` (012-route), `ac_range`, `consecutive_range`, `exclude_numbers` (kill numbers) |
| `ensemble` | — | integration | Multi-strategy voting: members each contribute a top-k ticket, numbers ranked by votes (`votes_min` threshold) |

## Usage

```python
from lotterycn import load_predict_numbers

picks = load_predict_numbers('ssq', method='hot', amount=5)          # alias of frequency + mode='hot'
chase = load_predict_numbers('ssq', method='omission', amount=3)     # mean-reversion chase
dev = load_predict_numbers('ssq', method='deviation', side='cold', explore_ratio=0)
rep = load_predict_numbers('ssq', method='repeat', repeat_weight=3.0)
band = load_predict_numbers('ssq', method='trend', k_sigma=1.0)
shrink = load_predict_numbers('ssq', method='filter', amount=3,
                              sum_range=(90, 120), prime_range=(2, 3),
                              zone_ratio=(2, 2, 2), exclude_numbers={7, 13})
votes = load_predict_numbers('ssq', method='ensemble', amount=1,
                             members=('frequency', 'omission', 'repeat'))
```

Pass `history=` to inject a DataFrame and work fully offline; otherwise the factory fetches draw history (respects `if_cached=True`).

## Backtesting — verify the "no predictive power" claim yourself

```python
from lotterycn import backtest, backtest_summary

results = backtest(methods=('random', 'hot', 'omission', 'ensemble'),
                   lottery_name='ssq', window=100)
print(backtest_summary(results))
```

Each strategy is driven by the preceding `window` draws and evaluated against the next real draw (red/blue hit counts). The expected outcome — reproduced every time — is that all strategies perform on par with `random`. Community machine-learning attempts (LSTM/XGBoost on number sequences) reach the same conclusion: on a Pick-3-sized space (1/1000) an LSTM lands at ≈ 4.2‰ accuracy, i.e. the baseline. Any "significantly better than random" observation should be treated as overfitting or noise.

## A note on the stock-analysis analogy

Several strategies deliberately mirror stock-analysis frameworks (momentum ≈ hot numbers, mean reversion ≈ omission chase, moving-average channels ≈ trend, volume ≈ sales/pool features from `draws.py`). The analogy is pedagogical: in an efficient market *and* in a lottery, frameworks do not create edge — but they make the randomness measurable.
