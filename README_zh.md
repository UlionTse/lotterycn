<p align="center">
  <img src="https://github.com/UlionTse/lotterycn/blob/main/docs/assets/lotterycn_logo.png" width="140" alt="LotteryCN"/>
</p>
<h1 align="center">LotteryCN</h1>
<p align="center">
  一个<b>有趣好玩</b>的中国福利彩票与体育彩票分析库——官方开奖数据、组合数学概率与期望、选号策略与预测回测、中奖校验。
</p>
<p align="center">
  <a href="https://github.com/UlionTse/lotterycn/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/UlionTse/lotterycn/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://pypi.org/project/lotterycn"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/lotterycn.svg"></a>
  <a href="https://anaconda.org/conda-forge/lotterycn"><img alt="Conda - Version" src="https://img.shields.io/conda/vn/conda-forge/lotterycn.svg"></a>
  <a href="https://pypi.org/project/lotterycn"><img alt="PyPI - License" src="https://img.shields.io/pypi/l/lotterycn.svg"></a>
  <a href="https://pypi.org/project/lotterycn"><img alt="PyPI - Python" src="https://img.shields.io/pypi/pyversions/lotterycn.svg"></a>
  <a href="https://pepy.tech/projects/lotterycn"><img alt="Downloads" src="https://static.pepy.tech/badge/lotterycn"></a>
</p>

[English](README.md) | 简体中文

* * *

**LotteryCN** 旨在带来**有趣好玩**的 Python 彩票分析。它封装中国福彩与体彩的官方开奖接口，并在此之上提供完整分析流水线：官方数据（中奖号码与开奖详情）、组合数学的概率与期望计算及中奖校验、**选号策略与预测回测（核心功能）**，以及贯穿始终的真实组合数学。

## 项目特点

- **选号策略与预测回测（核心功能）** —— 11 个选号策略 + 可组合缩水引擎 + 内置滚动回测；回测反复证明：所有策略与随机基线期望完全相同
- **只采用官方数据** —— 中奖号码与开奖详情（销售额 / 奖池 / 各奖级中奖情况 / 省级分布）直接来自官方渠道，无第三方爬虫
- **利用组合数学进行概率期望计算与验证** —— 精确组合计数各奖级命中数；现行奖级、中奖条件、固定奖金集中于 config 模块并附来源链接；概率、期望、返奖率由官方奖金表推导，支持投注号码即时校验
- **完整流水线** —— 收集（增量缓存）→ 分析 → 预测 → 回测 → 校验

## 选号策略与预测回测（核心功能）

`lotterycn.predict` 内置 11 个选号策略与 1 个可组合缩水引擎。**它们都不具备任何预测力**——开奖是独立随机事件，所有策略的期望收益与 `random` 基线完全相同；本模块仅用于统计观察与娱乐。

| 策略 | 别名 | 流派 | 思路 |
|---|---|---|---|
| `random` | — | 基线 | 均匀随机——一切策略的对照 |
| `frequency` | `hot` / `cold` | 走势图 | 滑动窗口（`recent_n`）频率选号，`explore_ratio` 控制确定性 |
| `omission` | `chase` | 走势图 | 遗漏回补：当前遗漏 / 平均遗漏，"热后转冷"排最前 |
| `deviation` | `chisq` | 统计 | 卡方偏离度（实际-期望)²/期望；`side='hot'` 或 `'cold'` |
| `repeat` | — | 社区 | 重号 / 邻号(±1) / 斜连号（上上期±1）三权重打分 |
| `trend` | — | 股票框架 | 和值均线通道：候选和值落入 MA ± k·σ 才保留 |
| `tail` | — | 走势图 | 两级选号：先按尾数频率选尾，再尾内取号 |
| `markov` | — | 序列 | 一阶转移采样——独立下退化为频率 |
| `markov2` | — | 序列 | 二阶转移（上两期 4 态）——展示高阶状态稀疏后退化均匀 |
| `filter` | — | 形态 | 可组合缩水：和值 / 奇偶 / 质合 / 三区比 / 012 路 / AC 值 / 连号 / 杀号 |
| `ensemble` | — | 集成 | 多策略投票：成员各出 top-k，按号码得票排序 |

```python
from lotterycn import backtest, backtest_summary

results = backtest(methods=('random', 'hot', 'omission', 'ensemble'),
                   lottery_name='ssq', window=100)
print(backtest_summary(results))
```

每次复现的结论都一样：**所有策略与 `random` 表现相当**。任何"显著优于随机"的观察都应视为过拟合或噪声。完整说明见文档站 [Strategies](https://uliontse.github.io/lotterycn/zh/strategies/) 页。

## 支持彩种

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

## 安装

```shell
pip install --upgrade lotterycn
```

```shell
conda install -c conda-forge lotterycn
```

要求 Python **3.9+**。

## 快速上手

### 1. 加载历史开奖

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

传 `if_cached=True` 可启用本地缓存与增量更新（见[本地缓存](#本地缓存)）。

### 2. 中奖概率与奖金期望

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

大乐透可传 `if_pool_over_800m=True` 使用奖池 ≥8 亿元档固定奖；快乐8 可用 `pick=1..10` 指定玩法（默认返回全部）。`if_add_bet=True` 计算追加投注口径（3 元/注，浮动奖按 80% 兑付）；`load_dlt_compound_expectation(n_red, m_blue)` 计算复式投注的注数、成本与期望。

### 3. 中奖校验

```python
from lotterycn import load_check_result

# draw_number=None 时自动拉取最新一期开奖（需联网）
print(load_check_result('ssq', '01,05,12,18,27,33|08', '01,05,12,18,27,33|08'))
```

```text
  lottery_name              my_number             draw_number prize_level       hit_detail  prize_amount             prize_type
0          ssq  01,05,12,18,27,33|08  01,05,12,18,27,33|08        一等奖  红球中6个,蓝球中1个     5000000.0  浮动(单注封顶500万元)
```

投注号码格式与开奖公告一致：`ssq` 为 `'红,红,...|蓝'`，`dlt` 为 `'前区|后区1,后区2'`，七乐彩只选 7 个基本号（特别号不可自选），数字型彩种接受 `'123'` 或 `'1,2,3'`，`qxc` 为 `'d1,...,d6|末位'`。

### 4. 生成随机号码

```python
from lotterycn import load_random_data

print(load_random_data('dlt', amount=2))
```

随机号码遵循各彩种规则（取值范围、去重、红蓝分区）。

## API 一览

| 函数 | 用途 | 关键参数 |
|---|---|---|
| `load_history_data(lottery_name, **kwargs)` | 历史开奖 DataFrame | `if_cached`、`cache_dir`、`begin_date`（福彩系）、`timeout`、`max_retries`、`proxies` |
| `load_random_data(lottery_name, amount=1)` | 随机选号 | `is_detail_result` |
| `load_prize_odds(lottery_name, **kwargs)` | 各奖级概率明细表 | `pick`（快乐8）、`if_pool_over_800m`（大乐透） |
| `load_prize_expectation(lottery_name, **kwargs)` | 单注期望与返奖率 | 同上 |
| `load_check_result(lottery_name, my_number, draw_number=None)` | 中奖校验 | `draw_number=None` 自动拉取最新开奖 |
| `load_number_statistics(lottery_name, **kwargs)` | 每个号码的频率与遗漏统计 | `history`（离线注入）、`if_cached` |
| `load_predict_numbers(lottery_name, method='random', amount=1)` | 按策略生成选号 | `method`: `random` / `frequency`（别名 `hot`/`cold`）/ `markov` / `filter` |
| `load_dlt_compound_expectation(n_red, m_blue)` | 大乐透复式投注的注数、成本与期望 | `if_pool_over_800m`、`if_add_bet` |
| `load_draw_detail(lottery_name, **kwargs)` | 开奖详情：销售额、奖池（每期一行） | `records`（离线）、`if_cached` |
| `load_prize_results(lottery_name, **kwargs)` | 各奖级中奖注数与单注奖金（长表） | 同上 |
| `load_first_prize_by_province(lottery_name, **kwargs)` | 一等奖省级分布（长表） | 同上 |

## 本地缓存

```python
df = load_history_data('ssq', if_cached=True)
```

首次调用全量拉取并写入 `~/.lotterycn/history` 下的 CSV（可通过 `cache_dir=` 参数或环境变量 `lotterycn_cache_dir` 覆盖）；之后调用读取缓存，仅拉取最后开奖日期之后的新数据（福彩系支持日期区间增量，体彩系全量刷新后去重合并）。

## 开奖详情

```python
from lotterycn import load_draw_detail, load_prize_results, load_first_prize_by_province

detail = load_draw_detail('ssq', if_cached=True)      # 日期 / 号码 / 销售额 / 奖池，每期一行
prizes = load_prize_results('ssq', if_cached=True)    # 各奖级中奖注数与单注奖金（长表）
prov = load_first_prize_by_province('ssq', if_cached=True)  # 一等奖省级分布
```

这些是官方开奖公告中的字段（销售额、奖池、各奖级中奖情况），被归一化为 tidy 表并与标准历史数据
一起增量缓存，可直接用于你自己的特征工程。注意：3d 的奖级数据官网接口不提供；省级分布仅部分
福彩玩法发布。这些记录描述的是过去的开奖，不构成任何预测力。

## 浮动奖配置

标记为"浮动"的奖级取决于奖池与中奖注数，本库按文档化的默认假设值计算期望，可用环境变量覆盖：

| 环境变量 | 默认值 | 含义 |
|---|---|---|
| `lotterycn_ssq_1st_prize` | `5000000` | 双色球一等奖默认值（单注封顶500万） |
| `lotterycn_dlt_1st_prize` | `5000000` | 大乐透一等奖默认值 |
| `lotterycn_kl8_pick10_1st_prize` | `5000000` | 快乐8选十中十默认值 |
| ... | ... | 见 [`lotterycn/config.py`](lotterycn/config.py) 中的 `*_prize_env` |

## 统计与选号策略

```python
from lotterycn import load_number_statistics, load_predict_numbers

stats = load_number_statistics('ssq', if_cached=True)
print(stats.sort_values('current_miss', ascending=False).head())   # 遗漏最长的号码

picks = load_predict_numbers('ssq', method='frequency', amount=5)  # 别名：method='hot' / 'cold'
print(picks)
```

完整策略表见上文「选号策略与预测回测（核心功能）」章节。

> **诚实声明**：彩票开奖是独立随机事件，历史统计**无法预测**未来开奖——以上任何策略的期望收益都与随机选号完全相同。本模块仅用于统计观察与娱乐；`random` 是所有策略应对照的基线。请理性购彩。

## 命令行

安装后提供 `lotterycn` 控制台命令（也可用 `python -m lotterycn.cli`）：

```shell
lotterycn odds ssq
lotterycn odds dlt --add-bet
lotterycn expect dlt --pool-over-800m
lotterycn stats ssq --cached
lotterycn predict ssq --method hot --amount 5 --cached
lotterycn check ssq --number '01,05,12,18,27,33|08' --draw '01,05,12,18,27,33|08'
```

`--cached` 读取本地缓存并增量刷新（首次需联网建立缓存）。

## 数据来源

规则与开奖数据仅来自官方渠道：

- 中国福利彩票：[cwl.gov.cn](https://www.cwl.gov.cn)
- 中国体育彩票：[lottery.gov.cn](https://www.lottery.gov.cn)

*规则与数据来源不含任何公司运营门户站点（见 [CONTRIBUTING.md](CONTRIBUTING.md)）。*

当前实现的规则版本及来源 URL 见 [`lotterycn/config.py`](lotterycn/config.py)。

## 测试

```shell
pip install pytest ruff
pytest                # 仅离线用例（联网用例默认跳过）
pytest -m network     # 访问官方接口的用例
```

## 参与贡献

欢迎提交 Issue 与 PR，请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)——尤其是**数据来源政策**：奖级规则必须以官方渠道核实，不得采用第三方网站数据。

## 许可证

[MIT](LICENSE)

## 免责声明

本项目仅用于数据分析与学习交流，**与任何彩票发行机构无关**。彩票数据与规则可能随时调整，请以官方公告为准。请理性购彩——彩票仅限成年人（18 周岁以上）参与，切勿当作投资。
