# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

English | [简体中文](CHANGELOG_zh.md).

## [1.0.0] - 2026-10-03

### Added

- Draw history for all 8 games (`ssq`, `qlc`, `kl8`, `3d`, `dlt`, `pls`, `plw`, `qxc`)
  from the official APIs (`cwl.gov.cn` / `lottery.gov.cn`) with retry and exponential
  backoff, unified into a tidy DataFrame (`data.py`).
- Local CSV cache with incremental update: `load_history_data(if_cached=True, cache_dir=...)`
  (`cache.py`).
- Prize odds, expected value and return rate for all 8 games (`odds.py`), computed with
  exact combinatorics (`math.comb`) on the current official rules — prize tiers, winning
  conditions and fixed amounts verified from cwl.gov.cn / lottery.gov.cn only, with rule
  source URLs kept in `config.py`.
- Super Lotto additional-bet (追加投注：3 yuan/bet, floating prizes paid at 80%) and
  compound-bet (复式) bet count, cost and whole-ticket expectation, with the derivation
  documented as LaTeX formulas (`odds.py`).
- Winning check against a given draw or the latest draw, returning hit detail, prize tier
  and amount (`check.py`).
- Number statistics: per-number frequency, current/max/average omission for both red and
  blue pools (`analysis.py`).
- Strategy-based number generation (`predict.py`): `random` baseline, frequency hot/cold
  (aliases `hot` / `cold`), omission (alias `chase`), chi-square deviation (alias `chisq`),
  repeat/neighbor, sum-band trend, tail, first/second-order Markov, composable shape filter
  (sum / odd / prime / zone ratio / 012-route / AC value / consecutive pairs / kill numbers)
  and multi-strategy ensemble voting — for statistical observation and entertainment only.
  Strategies are pure-injection (no network IO in constructors); `history=` makes usage
  fully offline.
- Rolling-window backtest comparing every strategy with the `random` baseline (`backtest.py`).
- Rich draw records (`draws.py`): per-draw sales & prize pool, per-prize-level winner counts
  & per-bet prizes (including the DLT additional-bet tier), and first-prize province
  distribution — three tidy tables with incremental caching.
- CLI `lotterycn` with subcommands `odds / expect / stats / predict / check / detail /
  prizes / provinces / backtest`.
- Property-based tests (hypothesis) for odds/expectation invariants, a coverage gate
  (`fail_under = 80`), a distributions build check, a non-blocking pip-audit scan and a
  Dependabot config in CI.
- Bilingual docs quality gate `tools/check_docs_sync.py` — en/zh page pairing, no CJK in
  English pages, unified tagline words and a ban on internal draw-API domains — wired
  into CI as the first step of the test job.
- Self-hosted MathJax 3.2.2 (`docs/assets/mathjax/`: `tex-chtml.js` component plus
  woff-v2 fonts) with a minimal `mathjax.js` config, so formulas render offline and
  on networks where public CDNs are unreachable.

### Changed

- Refactor: shared `Tse` / `LotteryError` into `utils.py`, relative imports, requests with
  retry and exponential backoff, default timeout.
- Packaging: metadata migrated to `pyproject.toml` (`[project]` table, SPDX license, dynamic
  version, console script); removed `setup.py`, `setup.cfg`, `MANIFEST`, `MANIFEST.in` and
  `requirements.txt`.
- Tests: pytest suite in `tests/` with offline/network split and real assertions; removed
  legacy `lotterycn/test.py`.
- CI: GitHub Actions matrix aligned to `requires-python` (3.10–3.12) with ruff, mypy and
  offline pytest coverage; tag-triggered PyPI release workflow; GitHub Pages deployment
  workflow.
- Project story realigned around four pillars with **number-picking strategies &
  backtesting** as the core feature: README (en/zh) lead and highlights, homepage cards,
  a full strategy table and backtest example in both READMEs; tagline unified as
  "enjoyable analysis" / 有趣好玩 across README and the docs site.
- All English doc pages are now English (API page intros, strategy terms, games-table
  link texts); the Chinese README lead paragraph no longer mixes English sentences.
- The internal draw-API host is removed from all documentation and docstrings; docs
  now cite the two official websites only (`cwl.gov.cn`, `lottery.gov.cn`).
- `LotteryError` raised with descriptive messages across the package; source formatted
  with `ruff format`.
- Docstrings completed across the package: every public function now documents its
  parameters, return value and column layout (`backtest`, `backtest_summary`, the
  cache / draws / data helpers, all twelve strategy `predict` implementations, odds
  helpers and utils); `methods` typed as `tuple[str, ...]`, `argv` as `list[str] | None`.
- Documentation site: the Chinese homepage mirrors the English one — hero (logo / tagline /
  CTA buttons), grid cards and a stable `#quickstart` anchor; visual pass with teal accent
  for both color schemes, hero gradient wash, 2×2 card grid with a light blue-green
  background and hover highlight, red-purple footer gradient echoing the logo, and a
  `chart-line` icon for the strategies card.
- MathJax moved from a public CDN to self-hosted assets; the docs site was rebuilt and
  every formula verified in a headless browser (en/zh).

### Fixed

- `:material-show-chart:` silently falling back to raw text (not part of the bundled
  icon set) replaced with `material/chart-line`.
- LaTeX formulas not rendering anywhere on the docs site (unreachable CDN, the
  `tex-mml-chtml` component producing empty containers, and an over-strict MathJax
  config) — confirmed fixed by headless-browser screenshots on both locales.
- `README_zh.md`: mixed English/Chinese lead paragraph rewritten; missing quickstart
  output example added.

### Documentation

- README rewritten in English with `README_zh.md`; added CONTRIBUTING, CODE_OF_CONDUCT,
  SECURITY and a data-correction issue template.
- Added `RELEASE.md`: maintainer release guide for the tag-driven Trusted-Publisher flow.
- Documentation site rebuilt with mkdocs-material + mkdocstrings and deployed to GitHub
  Pages, fully bilingual (English / 简体中文) via mkdocs-static-i18n with a language
  switcher; API reference generated from source for all 9 modules.
- Bilingual docstrings (English body + 中文说明 admonition) piloted on the four core APIs:
  `load_history_data`, `load_prize_odds`, `load_check_result` and `load_predict_numbers`.
- Site typography borrowed from fastapi / pydantic / polars documentation practices:
  self-hosted Alibaba PuHuiTi webfont (Apache 2.0 license included, `font-display: swap`),
  Monaco-first italic code style, MathJax rendering for formulas in docstrings, and
  spacing/typography normalization.
- Build hook (`hooks.py`): folds redundant blank lines in generated HTML (protecting
  `<pre>` blocks) and rewrites absolute `site_url` links to depth-relative paths, so the
  language switcher works in local IDE previews, offline pages and GitHub Pages project
  paths (previously returned 404).
