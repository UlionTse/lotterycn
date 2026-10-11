<p align="center">
  <img src="https://github.com/UlionTse/lotterycn/blob/main/docs/assets/lotterycn_logo.png" width="140" alt="LotteryCN"/>
</p>
<h1 align="center">LotteryCN</h1>
<p align="center">
  A Python library for <b>enjoyable</b> analysis of Chinese welfare &amp; sports lotteries — <b>official</b> draw data, combinatorial odds &amp; expected value, number-picking strategies with backtesting, and winning checks.
</p>
<p align="center">
  <a href="https://uliontse.github.io/lotterycn/"><b>Documentation</b></a> ·
  <a href="https://uliontse.github.io/lotterycn/zh/"><b>中文文档</b></a>
</p>
<p align="center">
  <a href="https://github.com/UlionTse/lotterycn/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/UlionTse/lotterycn/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://uliontse.github.io/lotterycn/"><img alt="Docs" src="https://img.shields.io/badge/docs-online-4051B5"></a>
  <a href="https://pypi.org/project/lotterycn"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/lotterycn.svg"></a>
  <a href="https://anaconda.org/conda-forge/lotterycn"><img alt="Conda - Version" src="https://img.shields.io/conda/vn/conda-forge/lotterycn.svg"></a>
  <a href="https://pypi.org/project/lotterycn"><img alt="PyPI - License" src="https://img.shields.io/pypi/l/lotterycn.svg"></a>
  <a href="https://pypi.org/project/lotterycn"><img alt="PyPI - Python" src="https://img.shields.io/pypi/pyversions/lotterycn.svg"></a>
  <a href="https://pepy.tech/projects/lotterycn"><img alt="Downloads" src="https://static.pepy.tech/badge/lotterycn"></a>
</p>

English | [简体中文](README_zh.md)

## Table of Contents

- [Why LotteryCN](#why-lotterycn)
- [Supported Games, Strategies & Data Sources](#supported-games-strategies--data-sources)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Command Line](#command-line)
- [License](#license)
- [Disclaimer](#disclaimer)

* * *

## Why LotteryCN

- **Official data only** — winning numbers and draw details (sales, prize pools, per-level results, province distribution) come straight from official channels; no third-party scrapers.
- **Combinatorial math for probabilities & expectations** — exact prize-tier counts; current prize tiers, conditions and amounts in one auditable config with source URLs; probabilities, expected values and return rates derived from official prize tables, plus instant ticket checking.
- **Number-picking strategies & backtesting (core)** — 11 strategies + a composable shrink engine + built-in rolling backtest; the backtest keeps proving every strategy matches the random baseline in expected value.
- **Full pipeline** — collect (cached incrementally) → analyze → predict → backtest → check.

## Supported Games, Strategies & Data Sources

### Games

| Code | Game | Operator | Notes |
|---|---|---|---|
| `ssq` | 双色球 (Double Color Ball) | Welfare | 6 red (1-33) + 1 blue (1-16) |
| `qlc` | 七乐彩 (7 Happy Lotto) | Welfare | 7 from 30 + special number |
| `kl8` | 快乐8 (Happy 8) | Welfare | 20 drawn from 80, pick 1-10 |
| `3d` | 福彩3D (Welfare 3D) | Welfare | 3-digit positional |
| `dlt` | 超级大乐透 (Super Lotto) | Sports | 5 front (1-35) + 2 back (1-12) |
| `pls` | 排列3 (P3) | Sports | 3-digit positional |
| `plw` | 排列5 (P5) | Sports | 5-digit positional |
| `qxc` | 7星彩 (7 Star Lotto) | Sports | 6-digit front (0-9) + last digit (0-14) |

### Strategies

`lotterycn.predict` ships eleven number-generation strategies plus a composable filter engine. **None of them has any predictive power** — draws are independent random events, so every strategy has exactly the same expected value as the `random` baseline. Full details: the [Strategies](https://uliontse.github.io/lotterycn/strategies/) page.

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
| `filter` | — | shape school | Composable shrink: sum / odd / prime / AC value / consecutive ranges, exact-match zone ratio & 012-route, kill numbers |
| `ensemble` | — | integration | Multi-strategy voting: members each contribute a top-k ticket, numbers ranked by votes |

> **Honest disclaimer**: historical statistics cannot predict future draws — play rationally.

### Data Sources

All rules and draw data come from official channels only:

- China Welfare Lottery: [cwl.gov.cn](https://www.cwl.gov.cn)
- China Sports Lottery: [lottery.gov.cn](https://www.lottery.gov.cn)

*Rule and data sources exclude all company-operated portals (see [CONTRIBUTING.md](CONTRIBUTING.md)); the rule versions currently implemented are cited with URLs in [`lotterycn/config.py`](lotterycn/config.py).*

## Installation

```shell
pip install --upgrade lotterycn
```

```shell
conda install -c conda-forge lotterycn
```

Requires Python **3.10 – 3.15**.

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
Every strategy matches `random` in expected value — the backtest above reproduces this conclusion every time; any "significantly better than random" observation is overfitting or noise. Ticket formats follow the published draw results; per-game play types (`kl8` `pick=1..10`, `dlt` `if_pool_over_800m` / `if_add_bet`, compound bets) and all other parameters are documented in the [API Reference](https://uliontse.github.io/lotterycn/api/odds/).

## Command Line

The package installs a `lotterycn` console script (also available as `python -m lotterycn.cli`):

```shell
lotterycn odds ssq
lotterycn expect dlt --pool-over-800m
lotterycn predict ssq --method hot --amount 5 --cached
lotterycn check ssq \
  --number '01,05,12,18,27,33|08' \
  --draw '01,05,12,18,27,33|08'
```

`--cached` reads the local cache and refreshes it incrementally (first run requires network).

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). For local checks: `pip install pytest ruff && pytest` (offline; network tests via `pytest -m network`).

## License

[MIT](LICENSE)

## Disclaimer

This project is for data analysis and educational purposes only. It is **not affiliated with** any lottery operator. Lottery data and rules may change at any time; always refer to official announcements. Play rationally — lotteries are for adults (18+) and should never be treated as an investment.
