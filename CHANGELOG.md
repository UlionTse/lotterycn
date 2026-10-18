# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

English | [简体中文](CHANGELOG_zh.md).

## [1.0.1] - 2026-10-10

### Highlights

- Core statistics & strategies vectorized with occurrence matrices — 250–380× faster.
- Sports-lottery cache hits refresh incrementally (a dlt refresh drops from ~15s to instant).
- Progress bars rebuilt on rich (brand gradient bar, replaces tqdm).
- `lottery_zh_name` column added; `lottery_name` canonicalised to game codes.
- Release-driven publishing: bilingual draft release + tag/version guards.

### Breaking Changes

- `lottery_name` now carries the game code (`ssq`/`dlt`), not the display name.
- `backtest` results add a `lottery_name` column; `backtest_summary` is reshaped
  (rate columns, grouped by `lottery_name + method`).
- Dependencies: `tqdm` removed; `rich>=15.0.0` and `numpy>=1.26.4` added.

### Changes

- Python 3.15 supported (classifiers + CI matrix 3.10–3.15).
- Release tooling: `prepare-release.yml` / `release.yml` / `tools/extract_changelog.py`;
  RELEASE.md rewritten; CI ruff/mypy pinned to the pre-commit revs.
- PEP 561 `py.typed`; pre-commit (ruff v0.17.0 + mypy v2.4.0); PR template;
  offline guard for non-network tests.
- READMEs slimmed and de-duplicated; docs homepage re-ordered; API Reference
  index page added; quickstart examples use `if_cached=True` / `sleep_seconds=0.1`.
- `.gitattributes`: built docs site and self-hosted MathJax excluded from
  language statistics.

### Fixed

- `if_cached=True` no longer recurses forever (the cache layer consumes the flag).
- CWL dates with weekday suffixes (`2026-10-08(四)`) normalised to ISO at ingestion;
  legacy caches tolerated.
- Empty draw windows no longer crash with `KeyError: 'code'`.
- Incremental refresh skips the network when the cache already covers today.
- README Python requirement corrected (3.9+ → 3.10–3.15); `deviation` parenthesis
  fixed; `mod3_range` documented as an exact match.

### Notes

- Legacy cache CSVs migrate automatically (display names → codes,
  `lottery_zh_name` backfilled) — no manual cleanup needed.
- For entertainment only: every strategy matches the `random` baseline in
  expected value (verify with `lotterycn.backtest`).

## [1.0.0] - 2026-10-03

### Highlights

- Official draw history for all 8 games (`cwl.gov.cn` / `lottery.gov.cn`) with
  local caching and incremental updates.
- Prize odds, expected value and return rates from exact combinatorics, plus
  winning ticket checks.
- 11 number-picking strategies with a rolling backtest against the `random` baseline.
- Bilingual documentation site and a `lotterycn` CLI.

### Breaking Changes

- Full rewrite of the 0.0.4 API: package layout, public functions and output
  schema all changed — 0.0.4 code must migrate to the new entry points.

### Changes

- Packaging migrated to `pyproject.toml` (dynamic version, console script);
  tests moved to `tests/` with an offline/network split; CI matrix on GitHub
  Actions; internal draw-API host removed from all documentation.

### Fixed

- `material/chart-line` icon fallback; MathJax rendering on the docs site
  (self-hosted assets); `README_zh.md` lead paragraph rewritten.

### Notes

- Official sources only — prize rules and draw data verified from
  `cwl.gov.cn` / `lottery.gov.cn`, never third-party sites.
- Strategies are for statistical observation and entertainment, not prediction.

## [0.0.4] - 2022-11-18

### Changes

- Unified output schema: every game returns the same five columns
  (`lottery_name` … `lottery_blue`); all 8 games supported (incl. kl8).

## [0.0.3] - 2022-11-10

### Highlights

- Initial public release: `load_random_data()` and `load_history_data()` over
  the official CWL / CSL APIs.
