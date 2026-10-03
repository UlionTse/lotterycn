# Contributing to LotteryCN

Thank you for considering a contribution! This document explains how to set up the project and the rules a pull request must follow.

## Development Setup

```shell
git clone https://github.com/UlionTse/lotterycn
cd lotterycn
pip install -e .
pip install pytest ruff
```

Optional but recommended:

```shell
pip install pre-commit && pre-commit install
```

## Project Layout

| Path | Purpose |
|---|---|
| `lotterycn/data.py` | Official API clients (welfare / sports lottery) and random number generation |
| `lotterycn/config.py` | Prize tiers, winning conditions and fixed amounts per game, with official rule URLs |
| `lotterycn/odds.py` | Combinatorial odds, expected value and return rate |
| `lotterycn/check.py` | Ticket checking against a draw |
| `lotterycn/cache.py` | Local CSV cache with incremental refresh |
| `lotterycn/utils.py` | Shared HTTP/date helpers (`Tse`) and `LotteryError` |
| `tests/` | pytest suite (`network` marker for tests that hit official APIs) |

## Running Tests

```shell
pytest                # offline tests only — this is what CI runs
pytest -m network     # tests that call the official APIs
ruff check lotterycn tests
```

Please make sure offline tests pass before opening a pull request.

## Data Source Policy (important)

Prize tiers, winning conditions and prize amounts **must be verified against official sources**:

Official sources are limited to exactly two sites:

- China Welfare Lottery: [cwl.gov.cn](https://www.cwl.gov.cn)
- China Sports Lottery: [lottery.gov.cn](https://www.lottery.gov.cn)

Do not cite any other website as a rule source — including company-operated portals such as company-operated lottery portals.

**Third-party lottery websites must not be used as a rule source** — their tables are frequently outdated. Every rule change in `lotterycn/config.py` must carry the URL of the official rule page in the class docstring or `*_rule_url` attribute, and the corresponding test in `tests/test_odds.py` must be updated with independently verified combination counts.

## Pull Request Guidelines

1. Fork, create a feature branch (`feat/...` or `fix/...`).
2. Keep changes focused; update `tests/` and, when user-facing, `README.md` / `README_zh.md` together.
3. Follow the existing code style (ruff-clean, 4-space indent, UTF-8 headers `# coding=utf-8`).
4. Bump `__version__` in `lotterycn/__init__.py` and add a `change_log.txt` entry for user-facing changes.
5. Ensure `pytest` (offline) and `ruff check` pass.

## Reporting Issues

Use the issue templates (bug report / feature request). For data-accuracy reports, please include the official rule page URL that supports your correction.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
