# Games & Official Rules

This library implements **current** official rules. Official sources are limited to exactly two sites:

- China Welfare Lottery: [cwl.gov.cn](https://www.cwl.gov.cn)
- China Sports Lottery: [lottery.gov.cn](https://www.lottery.gov.cn)

Company-operated portals are **not** used as rule or data sources.

| Code | Game | Operator | Pool / Format | Official rule source |
|---|---|---|---|---|
| `ssq` | 双色球 | Welfare | 6 red (1-33) + 1 blue (1-16) | [Game rules](https://www.cwl.gov.cn/fcpz/yxjs/ssq/) |
| `qlc` | 七乐彩 | Welfare | 7 from 30 + special | [Game rules](https://www.cwl.gov.cn/fcpz/yxjs/qlc/) |
| `kl8` | 快乐8 | Welfare | 20 drawn from 80, pick 1-10 | [Game rules](https://www.cwl.gov.cn/fcpz/yxjs/kl8/) |
| `3d` | 福彩3D | Welfare | 3-digit positional | [Game rules](https://www.cwl.gov.cn/fcpz/yxjs/fc3d/) |
| `dlt` | 超级大乐透 | Sports | 5 front (1-35) + 2 back (1-12) | [Game rules (current 7 tiers)](https://www.lottery.gov.cn/bzzx/yxgz/20191119/1002858.html) |
| `pls` | 排列3 | Sports | 3-digit positional | [Game rules](https://www.lottery.gov.cn/bzzx/yxgz/20191119/1002855.html) |
| `plw` | 排列5 | Sports | 5-digit positional | [Game rules](https://www.lottery.gov.cn/bzzx/yxgz/20191119/10011178.html) |
| `qxc` | 7星彩 | Sports | 6-digit front (0-9) + last (0-14) | [Game rules](https://www.lottery.gov.cn/bzzx/yxgz/20191119/1002857.html) |

Rule versions currently implemented are also embedded as `*_rule_url` attributes in `lotterycn/config.py`. When rules change, the corresponding tests in `tests/test_odds.py` must be updated with independently verified combination counts.
