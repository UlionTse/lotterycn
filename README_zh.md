<p align="center">
  <img src="https://github.com/UlionTse/lotterycn/blob/main/docs/assets/lotterycn_logo.png" width="140" alt="LotteryCN"/>
</p>
<h1 align="center">LotteryCN</h1>
<p align="center">
  一个<b>有趣好玩</b>的中国福利彩票与体育彩票分析库——官方开奖数据、组合数学概率与期望、选号策略与预测回测、中奖校验。
</p>
<p align="center">
  <a href="https://uliontse.github.io/lotterycn/zh/"><b>中文文档</b></a> ·
  <a href="https://uliontse.github.io/lotterycn/"><b>English Docs</b></a>
</p>
<p align="center">
  <a href="https://github.com/UlionTse/lotterycn/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/UlionTse/lotterycn/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://uliontse.github.io/lotterycn/zh/"><img alt="Docs" src="https://img.shields.io/badge/docs-online-4051B5"></a>
  <a href="https://pypi.org/project/lotterycn"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/lotterycn.svg"></a>
  <a href="https://anaconda.org/conda-forge/lotterycn"><img alt="Conda - Version" src="https://img.shields.io/conda/vn/conda-forge/lotterycn.svg"></a>
  <a href="https://pypi.org/project/lotterycn"><img alt="PyPI - License" src="https://img.shields.io/pypi/l/lotterycn.svg"></a>
  <a href="https://pypi.org/project/lotterycn"><img alt="PyPI - Python" src="https://img.shields.io/pypi/pyversions/lotterycn.svg"></a>
  <a href="https://pepy.tech/projects/lotterycn"><img alt="Downloads" src="https://static.pepy.tech/badge/lotterycn"></a>
</p>

[English](README.md) | 简体中文

## 目录

- [项目特点](#项目特点)
- [支持彩种、策略与数据来源](#支持彩种策略与数据来源)
- [安装](#安装)
- [快速上手](#快速上手)
- [命令行](#命令行)
- [许可证](#许可证)
- [免责声明](#免责声明)

* * *

## 项目特点

- **只采用官方数据** —— 中奖号码与开奖详情（销售额 / 奖池 / 各奖级中奖情况 / 省级分布）直接来自官方渠道，无第三方爬虫
- **利用组合数学进行概率期望计算与验证** —— 精确组合计数各奖级命中数；现行奖级、中奖条件、固定奖金集中于 config 模块并附来源链接；概率、期望、返奖率由官方奖金表推导，支持投注号码即时校验
- **选号策略与预测回测（核心功能）** —— 11 个选号策略 + 可组合缩水引擎 + 内置滚动回测；回测反复证明：所有策略与随机基线期望完全相同
- **完整流水线** —— 收集（增量缓存）→ 分析 → 预测 → 回测 → 校验

## 支持彩种、策略与数据来源

### 彩种

| 代码 | 彩种 | 机构 | 规则 |
|---|---|---|---|
| `ssq` | 双色球 | 福彩 | 6 红（1-33）+ 1 蓝（1-16） |
| `qlc` | 七乐彩 | 福彩 | 30 选 7 + 特别号 |
| `kl8` | 快乐8 | 福彩 | 80 选 20，玩法选一至选十 |
| `3d` | 福彩3D | 福彩 | 三位定位数字 |
| `dlt` | 超级大乐透 | 体彩 | 前区 5（1-35）+ 后区 2（1-12） |
| `pls` | 排列3 | 体彩 | 三位定位数字 |
| `plw` | 排列5 | 体彩 | 五位定位数字 |
| `qxc` | 7星彩 | 体彩 | 前区 6 位（0-9）+ 最后一位（0-14） |

### 策略

`lotterycn.predict` 内置 11 个选号策略与 1 个可组合缩水引擎。**它们都不具备任何预测力**——开奖是独立随机事件，所有策略的期望收益与 `random` 基线完全相同。完整说明见文档站 [Strategies](https://uliontse.github.io/lotterycn/zh/strategies/) 页。

| 策略 | 别名 | 流派 | 思路 |
|---|---|---|---|
| `random` | — | 基线 | 均匀随机——一切策略的对照 |
| `frequency` | `hot` / `cold` | 走势图 | 滑动窗口（`recent_n`）频率选号，`explore_ratio` 控制确定性 |
| `omission` | `chase` | 走势图 | 遗漏回补：当前遗漏 / 平均遗漏，"热后转冷"排最前 |
| `deviation` | `chisq` | 统计 | 卡方偏离度（实际 − 期望）² / 期望；`side='hot'` 或 `'cold'` |
| `repeat` | — | 社区 | 重号 / 邻号(±1) / 斜连号（上上期±1）三权重打分 |
| `trend` | — | 股票框架 | 和值均线通道：候选和值落入 MA ± k·σ 才保留 |
| `tail` | — | 走势图 | 两级选号：先按尾数频率选尾，再尾内取号 |
| `markov` | — | 序列 | 一阶转移采样——独立下退化为频率 |
| `markov2` | — | 序列 | 二阶转移（上两期 4 态）——展示高阶状态稀疏后退化均匀 |
| `filter` | — | 形态 | 可组合缩水：和值 / 奇偶 / 质合 / AC 值 / 连号区间，三区比与 012 路精确匹配，杀号 |
| `ensemble` | — | 集成 | 多策略投票：成员各出 top-k，按号码得票排序 |

> **诚实声明**：历史统计无法预测未来开奖——请理性购彩。

### 数据来源

规则与开奖数据仅来自官方渠道：

- 中国福利彩票：[cwl.gov.cn](https://www.cwl.gov.cn)
- 中国体育彩票：[lottery.gov.cn](https://www.lottery.gov.cn)

*规则与数据来源不含任何公司运营门户站点（见 [CONTRIBUTING.md](CONTRIBUTING.md)）；当前实现的规则版本及来源 URL 见 [`lotterycn/config.py`](lotterycn/config.py)。*

## 安装

```shell
pip install --upgrade lotterycn
```

```shell
conda install -c conda-forge lotterycn
```

要求 Python **3.10 – 3.15**。

## 快速上手

一条完整流水线——收集（缓存增量）→ 分析 → 预测 → 回测 → 校验：

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

所有策略与 `random` 期望完全相同——上面的回测每次都复现该结论；任何"显著优于随机"的观察都是过拟合或噪声。投注号码格式与开奖公告一致；各玩法参数（快乐8 `pick=1..10`、大乐透 `if_pool_over_800m` / `if_add_bet`、复式投注）及其余参数说明见 [API 参考](https://uliontse.github.io/lotterycn/zh/api/odds/)。

## 命令行

安装后提供 `lotterycn` 控制台命令（也可用 `python -m lotterycn.cli`）：

```shell
lotterycn odds ssq
lotterycn expect dlt --pool-over-800m
lotterycn predict ssq --method hot --amount 5 --cached
lotterycn check ssq \
  --number '01,05,12,18,27,33|08' \
  --draw '01,05,12,18,27,33|08'
```

`--cached` 读取本地缓存并增量刷新（首次需联网建立缓存）。

欢迎提交 Issue 与 PR，请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。本地自检：`pip install pytest ruff && pytest`（默认离线；联网用例 `pytest -m network`）。

## 许可证

[MIT](LICENSE)

## 免责声明

本项目仅用于数据分析与学习交流，**与任何彩票发行机构无关**。彩票数据与规则可能随时调整，请以官方公告为准。请理性购彩——彩票仅限成年人（18 周岁以上）参与，切勿当作投资。
