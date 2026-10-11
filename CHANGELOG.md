# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

English | [简体中文](CHANGELOG_zh.md).

## [1.0.1] - 2026-10-10

### Added

- Python 3.15 support: classifiers now cover 3.10–3.15 and the CI matrix tests all six
  versions (3.13/3.14 were previously declared but never tested).
- Release-driven publishing: on tag push, `prepare-release.yml` creates a bilingual
  draft GitHub Release extracted from `CHANGELOG.md` / `CHANGELOG_zh.md` via the new
  `tools/extract_changelog.py`; PyPI upload runs only when the Release is published
  (`release.yml`). Both workflows guard that the tag matches `__version__`.
- Filter shape-metric definitions documented (AC value, per-game zone boundaries,
  012-route, primes, consecutive pairs) with unit tests locking the exact semantics
  (`tests/test_predict.py`).
- Inline comments added to the math-heavy parts of `predict.py` (sum band MA ± k·σ,
  chi-square expectation, AC value, omission score, Efraimidis–Spirakis sampling).

### Changed

- READMEs (en/zh) restructured: table of contents added, documentation site links
  promoted to the top (centered links + Docs badge), Python requirement stated as
  3.10 – 3.15.
- Code blocks in both READMEs and on the docs homepage reformatted to black-style
  vertical calls (≤ 79 columns) so they no longer wrap mid-token on narrow screens.
- RELEASE.md rewritten for the release-driven flow with a step-by-step publishing
  tutorial; release notes are now generated instead of pasted by hand.
- READMEs slimmed down: table of contents cut from 16 to 7 entries; games, strategies
  and data sources merged into one section; Quickstart reduced to a single cached
  end-to-end pipeline (mirrored on the docs homepage, which now also demonstrates the
  winning check); API overview, caching, draw-details, floating-prize and statistics
  sections removed — all fully documented on the docs site.
- README openings de-duplicated: intro paragraph removed (tagline and the "Why
  LotteryCN" bullets tell the story once); the four Why bullets and the docs homepage
  grid cards reordered to follow the pipeline (data → math → strategies (core) →
  pipeline); the docs homepage's mid-page rules paragraph folded into the
  official-data card with the Games & Rules link, and Quickstart gained the same
  pipeline lead-in.
- Performance: `load_number_statistics` and the strategy predictors (frequency / tail /
  omission / markov / markov2) now parse each draw once into occurrence matrices and
  compute with vectorized numpy — full-history statistics run ≈ 250–380× faster
  (ssq 3000 draws: 1.2s → 0.015s; kl8 8000 draws: 5.8s → 0.04s), with results verified
  identical by pure-Python reference-implementation tests; backtest pre-parses actual
  draws and resolves predictor classes once per method; `numpy` is now an explicit
  dependency (compatible with pandas >= 2.3.3 and 3.x).
- PEP 561 `py.typed` marker shipped via wheel package-data, so downstream `mypy`
  users get inline types; PR template added; pre-commit upgraded to ruff v0.17.0
  (ruff + ruff-format) with a mypy hook pinned to the project dependency set.
- History / random / strategy frames now carry a `lottery_zh_name` column (the API
  display name, e.g. '双色球') right after `lottery_name`, whose value stays the game
  code; the ingestion pipeline maps raw API columns by name instead of by position.
  Legacy cache CSVs migrate automatically (display names are mapped to codes and the
  missing column is backfilled).
- Sports-lottery games (dlt / pls / plw / qxc) no longer re-download every page on a
  cache hit: the CSL API has no date-window query, so the incremental refresh now walks
  pages newest-first and stops at the first page overlapping the cached draws (usually
  page 1; exhausting all pages degrades to a full refresh with dedup), with the same
  rich progress bar as full fetches — its total shrinks to the pages actually fetched
  and the info field reports real row counts. A warmup helper returns the page count
  explicitly. Real-world effect: a dlt refresh drops from ~15s (full crawl) to instant
  when the cache is up to date.
- `lottery_name` is canonicalised to the game code (`ssq`/`dlt`/...) at ingestion: the
  raw APIs carry display names ('双色球'/'超级大乐透') while the rest of the library and
  the documentation key on codes, so the column previously disagreed with them.
- The incremental cache refresh no longer crashes when the cache already covers every
  draw up to today (or the API returned a future-dated row): the computed `begin_date`
  fell beyond today and `check_params` rejected it. The cache layer now skips the
  network fetch and returns the cached frame directly in that case.
- `backtest` results now include a `lottery_name` column, and `backtest_summary` adds
  four rate columns: `avg_red_hit_rate` / `avg_blue_hit_rate` (a strategy's average
  hits ÷ balls drawn per game — the share of the drawn balls a ticket captures) and
  `random_red_hit_rate` / `random_blue_hit_rate` (the `random` baseline's measured
  share, shown on every row for comparison; NaN when the results contain no `random`
  method). Theoretical shares are `R ÷ N` and `B ÷ N_blue` (e.g. ssq reds 6 ÷ 33 ≈ 18%),
  so both the strategy and the baseline should sit close to them; `backtest_summary`
  groups by `lottery_name + method` accordingly.
- Progress bars rebuilt on rich (replacing tqdm, which is removed from the
  dependencies): brand blue -> teal true-gradient bar (cell-by-cell interpolation
  with a pip-style half-filled boundary cell), live date-window / row-count info,
  CJK-correct adaptive width, stderr output, automatic silencing when stderr is not
  a TTY, and a persistent completion row (pip-style).

### Fixed

- `if_cached=True` crashed with `RecursionError` on every real code path (empty-cache
  fallback, incremental refresh, detail passthrough): the flag was passed back to
  `load_history_data`, which re-dispatched into the cache layer forever. The flag is
  now consumed by the cache layer; a regression test drives the real
  `load_history_data -> cache -> network` dispatch (mocking the network layer, not
  the cache layer, which is how earlier tests masked this).
- The official CWL API returns draw dates with a weekday suffix (`2026-10-08(四)`), which
  reached the public DataFrame and the cache CSV verbatim and crashed the incremental
  refresh with `ValueError: Invalid isoformat string`. Dates are now normalised to the
  ISO prefix at ingestion, and the cache's incremental parser tolerates legacy CSVs
  already written with suffixes (no manual cache cleanup needed).
- Incremental refresh through an empty draw window crashed with `KeyError: 'code'`: the
  API legitimately returns no draws for some date windows (ssq draws three times a
  week), and the empty response was parsed into a column-less DataFrame. Empty API
  responses now keep the expected columns on both the CWL and CSL paths.
- README stated a Python requirement of 3.9+ while the package requires ≥ 3.10.
- The `deviation` strategy description used mismatched full/half-width parentheses in
  the Chinese docs（实际-期望)² → （实际 − 期望）².
- `filter` strategy docs now state that `zone_ratio` and `mod3_range` are exact
  matches (the `mod3_range` name alone reads like a range).

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
