# 彩种与官方规则

本库实现的是**现行**官方规则。官方来源仅限两个站点：

- 中国福利彩票：[cwl.gov.cn](https://www.cwl.gov.cn)
- 中国体育彩票：[lottery.gov.cn](https://www.lottery.gov.cn)

公司运营的门户站点（如中彩网）**不作为**规则或数据来源。

| 代码 | 彩种 | 机构 | 号码格式 | 官方规则来源 |
|---|---|---|---|---|
| `ssq` | 双色球 | 福彩 | 6 红（1-33）+ 1 蓝（1-16） | [玩法介绍](https://www.cwl.gov.cn/fcpz/yxjs/ssq/) |
| `qlc` | 七乐彩 | 福彩 | 30 选 7 + 特别号 | [玩法介绍](https://www.cwl.gov.cn/fcpz/yxjs/qlc/) |
| `kl8` | 快乐8 | 福彩 | 80 选 20，玩法选 1-10 | [玩法介绍](https://www.cwl.gov.cn/fcpz/yxjs/kl8/) |
| `3d` | 福彩3D | 福彩 | 3 位定位数字 | [玩法介绍](https://www.cwl.gov.cn/fcpz/yxjs/fc3d/) |
| `dlt` | 超级大乐透 | 体彩 | 前区 5（1-35）+ 后区 2（1-12） | [游戏规则（现行七奖级）](https://www.lottery.gov.cn/bzzx/yxgz/20191119/1002858.html) |
| `pls` | 排列3 | 体彩 | 3 位定位数字 | [游戏规则](https://www.lottery.gov.cn/bzzx/yxgz/20191119/1002855.html) |
| `plw` | 排列5 | 体彩 | 5 位定位数字 | [游戏规则](https://www.lottery.gov.cn/bzzx/yxgz/20191119/10011178.html) |
| `qxc` | 7星彩 | 体彩 | 前区 6 位（0-9）+ 末位（0-14） | [游戏规则](https://www.lottery.gov.cn/bzzx/yxgz/20191119/1002857.html) |

规则版本同时以 `*_rule_url` 形式嵌入 `lotterycn/config.py`；规则变更时，须同步更新 `tests/test_odds.py` 中独立验算的组合数断言。
