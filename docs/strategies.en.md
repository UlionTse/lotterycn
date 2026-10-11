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
| `filter` | — | shape school | Composable shrink engine: `sum_range`, `odd_range`, `prime_range`, `ac_range`, `consecutive_range` (ranges), `zone_ratio` & `mod3_range` (012-route, exact match), `exclude_numbers` (kill numbers) |
| `ensemble` | — | integration | Multi-strategy voting: members each contribute a top-k ticket, numbers ranked by votes (`votes_min` threshold) |

## Usage

```python
from lotterycn import load_predict_numbers

# method='hot' is an alias of frequency + mode='hot'
picks = load_predict_numbers("ssq", method="hot", amount=5)
chase = load_predict_numbers("ssq", method="omission", amount=3)  # mean reversion
dev = load_predict_numbers("ssq", method="deviation", side="cold", explore_ratio=0)
rep = load_predict_numbers("ssq", method="repeat", repeat_weight=3.0)
band = load_predict_numbers("ssq", method="trend", k_sigma=1.0)
shrink = load_predict_numbers(
    "ssq",
    method="filter",
    amount=3,
    sum_range=(90, 120),
    prime_range=(2, 3),
    zone_ratio=(2, 2, 2),
    exclude_numbers={7, 13},
)
votes = load_predict_numbers(
    "ssq",
    method="ensemble",
    amount=1,
    members=("frequency", "omission", "repeat"),
)
```

Pass `history=` to inject a DataFrame and work fully offline; otherwise the factory fetches draw history (respects `if_cached=True`).

## Filter shape-metric definitions

All `*_range` filters are inclusive `(lo, hi)` intervals; `zone_ratio` and `mod3_range` are **exact matches** on the count triple.

- **AC value** — number of distinct pairwise differences among the sorted unique numbers, minus (count − 1). Example: `{01,02,06,13,27,33}` has exactly 15 distinct pairwise differences, so AC = 15 − (6 − 1) = 10 (the theoretical maximum for 6 numbers); the fully consecutive `{01..06}` has only 5, so AC = 0.
- **Zone ratio (exact match)** — the red pool is split into three zones; per-zone counts must equal the given `(zone1, zone2, zone3)` exactly. Zone boundaries per game:

  | Game (red pool) | Zone 1 | Zone 2 | Zone 3 |
  |---|---|---|---|
  | `ssq` (1-33) | 1-11 | 12-22 | 23-33 |
  | `qlc` (1-30) | 1-10 | 11-20 | 21-30 |
  | `kl8` (1-80) | 1-27 | 28-54 | 55-80 |
  | `dlt` (1-35) | 1-12 | 13-24 | 25-35 |
  | digit games `3d`/`pls`/`plw`/`qxc` (0-9) | 0-3 | 4-6 | 7-9 |

- **012-route `mod3_range` (exact match)** — counts of numbers ≡ 0 / 1 / 2 (mod 3) must equal the given triple exactly.
- **Primes** — {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31} (1 is not prime).
- **Consecutive pairs** — adjacent pairs (differ by exactly 1) among the sorted unique numbers.

As with every strategy, filtering changes only the *shape* of the picked tickets — it never changes any ticket's winning probability.

## Backtesting — verify the "no predictive power" claim yourself

```python
from lotterycn import backtest, backtest_summary

results = backtest(
    methods=("random", "hot", "omission", "ensemble"),
    lottery_name="ssq",
    window=100,
)
print(backtest_summary(results))
```

Each strategy is driven by the preceding `window` draws and evaluated against the next real draw (red/blue hit counts). The expected outcome — reproduced every time — is that all strategies perform on par with `random`. Community machine-learning attempts (LSTM/XGBoost on number sequences) reach the same conclusion: on a Pick-3-sized space (1/1000) an LSTM lands at ≈ 4.2‰ accuracy, i.e. the baseline. Any "significantly better than random" observation should be treated as overfitting or noise.

## A note on the stock-analysis analogy

Several strategies deliberately mirror stock-analysis frameworks (momentum ≈ hot numbers, mean reversion ≈ omission chase, moving-average channels ≈ trend, volume ≈ sales/pool features from `draws.py`). The analogy is pedagogical: in an efficient market *and* in a lottery, frameworks do not create edge — but they make the randomness measurable.
