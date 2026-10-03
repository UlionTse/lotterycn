<p align="center">
  <img src="https://github.com/UlionTse/lotterycn/blob/main/docs/assets/lotterycn_logo.png" width="140" alt="LotteryCN"/>
</p>
<h1 align="center">LotteryCN</h1>
<p align="center">
  A Python library for <b>enjoyable</b> analysis of Chinese welfare &amp; sports lotteries — <b>official</b> draw data, combinatorial odds &amp; expected value, number-picking strategies with backtesting, and winning checks.
</p>
<p align="center">
  <a href="https://github.com/UlionTse/lotterycn/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/UlionTse/lotterycn/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://pypi.org/project/lotterycn"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/lotterycn.svg"></a>
  <a href="https://anaconda.org/conda-forge/lotterycn"><img alt="Conda - Version" src="https://img.shields.io/conda/vn/conda-forge/lotterycn.svg"></a>
  <a href="https://pypi.org/project/lotterycn"><img alt="PyPI - License" src="https://img.shields.io/pypi/l/lotterycn.svg"></a>
  <a href="https://pypi.org/project/lotterycn"><img alt="PyPI - Python" src="https://img.shields.io/pypi/pyversions/lotterycn.svg"></a>
  <a href="https://pepy.tech/projects/lotterycn"><img alt="Downloads" src="https://static.pepy.tech/badge/lotterycn"></a>
</p>

English | [简体中文](README_zh.md)

* * *

**LotteryCN** aims to bring **enjoyable** analysis of lottery in Python. It wraps the official draw APIs of China Welfare Lottery and China Sports Lottery and builds a full pipeline on top — official data (winning numbers and draw details), combinatorial odds, expected values and ticket checking, **number-picking strategies with backtesting (the core feature)**, and exact combinatorial math throughout.

## Why LotteryCN

- **Number-picking strategies & backtesting (core)** — 11 strategies + a composable shrink engine + built-in rolling backtest; the backtest keeps proving every strategy matches the random baseline in expected value.
- **Official data only** — winning numbers and draw details (sales, prize pools, per-level results, province distribution) come straight from official channels; no third-party scrapers.
- **Combinatorial math for probabilities & expectations** — exact prize-tier counts; current prize tiers, conditions and amounts in one auditable config with source URLs; probabilities, expected values and return rates derived from official prize tables, plus instant ticket checking.
- **Full pipeline** — collect (cached incrementally) → analyze → predict → backtest → check.

## Number-Picking Strategies & Backtesting (Core)

`lotterycn.predict` ships eleven number-generation strategies plus a composable filter engine. **None of them has any predictive power** — draws are independent random events, so every strategy has exactly the same expected value as the `random` baseline. This module exists for statistical observation and entertainment.

| Method | Aliases | School | Idea |
|---|---|---|---|
| `random` | — | baseline | Uniform random — the baseline every strategy is compared against |
| `frequency` | `hot` / `cold` | trend charts | Pick by frequency over a sliding window (`recent_n`); `explore_ratio` controls determinism |
| `omission` | `chase` | trend charts | Mean-reversion chase: current omission / average omission |
| `deviation` | `chisq` | statistics | Chi-square deviation (observed − expected)² / expected; `side='hot'` or `'cold'` |
| `repeat` | — | community | Repeat / neighbor (±1) / jump (second-last draw ±1) weighting |
| `trend` | — | stock framework | Sum moving-average channel: keep candidates whose sum falls inside MA ± k·σ |
| `tail` | — | trend charts | Two-level picks: tail digits by frequency, then numbers within those tails |
| `markov` | — | sequence | First-order transition sampling — collapses to frequency under independence |
| `markov2` | — | sequence | Second-order transition (last two draws, 4 states) |
| `filter` | — | shape school | Composable shrink: sum / odd / prime / zone ratio / 012-route / AC value / consecutive / kill numbers |
| `ensemble` | — | integration | Multi-strategy voting: members each contribute a top-k ticket, numbers ranked by votes |

```python
from lotterycn import backtest, backtest_summary

results = backtest(methods=('random', 'hot', 'omission', 'ensemble'),
                   lottery_name='ssq', window=100)
print(backtest_summary(results))
```

The conclusion reproduces every time: **all strategies perform on par with `random`**. Any "significantly better than random" observation should be treated as overfitting or noise. Full details: the [Strategies](https://uliontse.github.io/lotterycn/strategies/) page.

## Supported Games

| Code | Game                    | Operator | Notes |
|---|-------------------------|---|---|
| `ssq` | 双色球 (Double Color Ball) | Welfare | 6 red (1-33) + 1 blue (1-16) |
| `qlc` | 七乐彩 (7 Happy Lotto)     | Welfare | 7 from 30 + special number |
| `kl8` | 快乐8 (Happy 8)           | Welfare | 20 drawn from 80, pick 1-10 |
| `3d` | 福彩3D (Welfare 3D)       | Welfare | 3-digit positional |
| `dlt` | 超级大乐透 (Super Lotto)     | Sports | 5 front (1-35) + 2 back (1-12) |
| `pls` | 排列3 (P3)                | Sports | 3-digit positional |
| `plw` | 排列5 (P5)                | Sports | 5-digit positional |
| `qxc` | 7星彩 (7 Star Lotto)      | Sports | 6-digit front (0-9) + last digit (0-14) |

## Installation

```shell
pip install --upgrade lotterycn
```

```shell
conda install -c conda-forge lotterycn
```

Requires Python **3.9+**.

## Quickstart

### 1. Load draw history

```python
from lotterycn import load_history_data

df = load_history_data('ssq')
print(df.tail(2))
```

```text
    lottery_name lottery_order lottery_date        lottery_red lottery_blue
0            ssq       2023001   2023-01-01  02,08,13,17,26,31           06
...
```

Add `if_cached=True` to store results locally and refresh incrementally (see [Caching](#caching)).

### 2. Prize odds & expected value

```python
from lotterycn import load_prize_odds, load_prize_expectation

odds = load_prize_odds('ssq')
print(odds.head(3))
```

```text
  lottery_name play_type prize_level hit_condition  winning_combinations  total_combinations  winning_probability     one_in_odds  prize_amount              prize_type
0          ssq        单式        一等奖           6+1                     1            17721088         5.642994e-08  1.772109e+07     5000000.0  浮动(单注封顶500万元)
1          ssq        单式        二等奖           6+0                    15            17721088         8.464492e-07  1.181406e+06      150000.0  浮动(单注封顶500万元)
2          ssq        单式        三等奖           5+1                   162            17721088         9.141651e-06  1.093894e+05        3000.0               固定
```

```python
exp = load_prize_expectation('ssq')
print(exp)
```

```text
  lottery_name play_type  bet_price_yuan  expected_value_yuan  return_rate
0          ssq        单式               2             0.895428     0.447714
```

For `dlt`, pass `if_pool_over_800m=True` to use the higher fixed-prize tier (prize pool ≥ 800 million); for `kl8`, select a play type with `pick=1..10` (default: all). `if_add_bet=True` computes the additional-bet variant (3 yuan/bet, floating prizes paid at 80%); `load_dlt_compound_expectation(n_red, m_blue)` computes compound-bet (复式) bets, cost and expectation.

### 3. Check a winning ticket

```python
from lotterycn import load_check_result

# draw_number=None fetches the latest draw automatically (requires network)
print(load_check_result('ssq', '01,05,12,18,27,33|08', '01,05,12,18,27,33|08'))
```

```text
  lottery_name              my_number             draw_number prize_level       hit_detail  prize_amount             prize_type
0          ssq  01,05,12,18,27,33|08  01,05,12,18,27,33|08        一等奖  红球中6个,蓝球中1个     5000000.0  浮动(单注封顶500万元)
```

Ticket formats follow the published draw results: `ssq` `'reds|blue'`, `dlt` `'front|back1,back2'`, `qlc` seven numbers only (the special number cannot be picked), digit games accept `'123'` or `'1,2,3'`, `qxc` is `'d1,...,d6|last'`.

### 4. Generate random numbers

```python
from lotterycn import load_random_data

print(load_random_data('dlt', amount=2))
```

Random numbers follow each game's rules (ranges, uniqueness, red/blue split).

## API Overview

| Function | Purpose | Key parameters |
|---|---|---|
| `load_history_data(lottery_name, **kwargs)` | Draw history as a `pandas.DataFrame` | `if_cached`, `cache_dir`, `begin_date` (welfare games), `timeout`, `max_retries`, `proxies` |
| `load_random_data(lottery_name, amount=1)` | Random tickets | `is_detail_result` |
| `load_prize_odds(lottery_name, **kwargs)` | Per-prize odds table | `pick` (kl8), `if_pool_over_800m` (dlt) |
| `load_prize_expectation(lottery_name, **kwargs)` | Expected value & return rate per bet | same as above |
| `load_check_result(lottery_name, my_number, draw_number=None)` | Prize-tier check | `draw_number=None` fetches the latest draw |
| `load_number_statistics(lottery_name, **kwargs)` | Frequency & omission stats per number | `history` (offline), `if_cached` |
| `load_predict_numbers(lottery_name, method='random', amount=1)` | Strategy-based number generation | `method`: `random` / `frequency` (aliases `hot`/`cold`) / `markov` / `filter` |
| `load_dlt_compound_expectation(n_red, m_blue)` | Super Lotto compound-bet (复式) bets, cost & expectation | `if_pool_over_800m`, `if_add_bet` |
| `load_draw_detail(lottery_name, **kwargs)` | Draw details: sales, prize pool (one row per draw) | `records` (offline), `if_cached` |
| `load_prize_results(lottery_name, **kwargs)` | Winner counts & per-bet prize per level (long table) | same as above |
| `load_first_prize_by_province(lottery_name, **kwargs)` | First-prize distribution by province (long table) | same as above |

## Caching

```python
df = load_history_data('ssq', if_cached=True)
```

The first call performs a full fetch and writes a CSV under `~/.lotterycn/history` (override with `cache_dir=` or the `lotterycn_cache_dir` environment variable). Subsequent calls load the cache and only fetch draws newer than the latest cached date (welfare games support date-range fetching; sports games are refreshed fully and deduplicated). Pass `cache_dir` per call or set the env var once.

## Draw Details

```python
from lotterycn import load_draw_detail, load_prize_results, load_first_prize_by_province

detail = load_draw_detail('ssq', if_cached=True)      # date / numbers / sales / pool, one row per draw
prizes = load_prize_results('ssq', if_cached=True)    # winner counts & per-bet prize per level (long table)
prov = load_first_prize_by_province('ssq', if_cached=True)  # first-prize distribution by province
```

These are the fields of the official draw announcements (sales, jackpot pool, per-prize-level results),
normalized into tidy tables and cached incrementally alongside the standard history — ready for your own
feature engineering. Note: 3d prize results are not provided by the official API; province distribution exists
only for the welfare games that publish it. The records describe past draws and carry no predictive power.

## Configuring Floating Prizes

Prizes marked 浮动 (floating) depend on prize pools and winner counts. This library computes expectations from documented default assumptions; override them per run with environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `lotterycn_ssq_1st_prize` | `5000000` | SSQ 1st-prize default (capped at ¥5M per bet) |
| `lotterycn_dlt_1st_prize` | `5000000` | DLT 1st-prize default |
| `lotterycn_kl8_pick10_1st_prize` | `5000000` | KL8 pick-10 first-prize default |
| ... | ... | see `*_prize_env` in [`lotterycn/config.py`](lotterycn/config.py) |

## Statistics & Number Strategies

```python
from lotterycn import load_number_statistics, load_predict_numbers

stats = load_number_statistics('ssq', if_cached=True)
print(stats.sort_values('current_miss', ascending=False).head())   # longest-missing numbers

picks = load_predict_numbers('ssq', method='frequency', amount=5)  # alias: method='hot' / 'cold'
print(picks)
```

For the complete strategy table see **Number-Picking Strategies & Backtesting** above.

> **Honest disclaimer**: lottery draws are independent random events. Historical statistics **cannot predict** future draws — every strategy above has exactly the same expected value as random picking. This module exists for statistical observation and entertainment; `random` is the baseline any strategy should be compared against. Play rationally.

## Command Line

The package installs a `lotterycn` console script (also available as `python -m lotterycn.cli`):

```shell
lotterycn odds ssq
lotterycn odds dlt --add-bet
lotterycn expect dlt --pool-over-800m
lotterycn stats ssq --cached
lotterycn predict ssq --method hot --amount 5 --cached
lotterycn check ssq --number '01,05,12,18,27,33|08' --draw '01,05,12,18,27,33|08'
```

`--cached` reads the local cache and refreshes it incrementally (first run requires network).

## Data Sources

All rules and draw data come from official channels only:

- China Welfare Lottery: [cwl.gov.cn](https://www.cwl.gov.cn)
- China Sports Lottery: [lottery.gov.cn](https://www.lottery.gov.cn)

*Rule and data sources exclude all company-operated portals (see [CONTRIBUTING.md](CONTRIBUTING.md)).*

Rule versions currently implemented are cited with URLs in [`lotterycn/config.py`](lotterycn/config.py).

## Testing

```shell
pip install pytest ruff
pytest                # offline tests only (network tests are deselected by default)
pytest -m network     # tests that hit the official APIs
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) — in particular the **data source policy**: prize rules must be verified against official sources, never third-party websites.

## License

[MIT](LICENSE)

## Disclaimer

This project is for data analysis and educational purposes only. It is **not affiliated with** any lottery operator. Lottery data and rules may change at any time; always refer to official announcements. Play rationally — lotteries are for adults (18+) and should never be treated as an investment.
