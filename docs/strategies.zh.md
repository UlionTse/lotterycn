# 策略（仅供娱乐）

`lotterycn.predict` 内置 11 个选号策略与 1 个可组合缩水引擎。**它们都不具备任何预测力**——开奖是独立随机事件，所有策略的期望收益与 `random` 基线完全相同。本模块仅用于统计观察与娱乐。

| 策略 | 别名 | 流派 | 思路 |
|---|---|---|---|
| `random` | — | 基线 | 均匀随机——一切策略的对照 |
| `frequency` | `hot` / `cold` | 走势图 | 滑动窗口（`recent_n`）频率选号，`explore_ratio` 控制确定性 |
| `omission` | `chase` | 走势图 | 遗漏回补：当前遗漏 / 平均遗漏，"热后转冷"排最前 |
| `deviation` | `chisq` | 统计 | 卡方偏离度（实际-期望)²/期望；`side='hot'` 或 `'cold'` |
| `repeat` | — | 社区 | 重号 / 邻号(±1) / 斜连号（上上期±1）三权重打分 |
| `trend` | — | 股票框架 | 和值均线通道：候选和值落入 MA ± k·σ 才保留 |
| `tail` | — | 走势图 | 两级选号：先按尾数（号码%10）频率选尾，再尾内取号 |
| `markov` | — | 序列 | 一阶转移采样 P(本期出现\|上期出现/未出现)——独立下退化为频率 |
| `markov2` | — | 序列 | 二阶转移（上两期 4 态）——展示高阶状态稀疏后退化均匀 |
| `filter` | — | 形态 | 可组合缩水：和值 / 奇偶 / 质合 / 三区比 / 012 路 / AC 值 / 连号 / 杀号 |
| `ensemble` | — | 集成 | 多策略投票：成员各出 top-k，按号码得票排序（`votes_min` 阈值） |

## 用法

```python
from lotterycn import load_predict_numbers

picks = load_predict_numbers('ssq', method='hot', amount=5)          # frequency + mode='hot'
chase = load_predict_numbers('ssq', method='omission', amount=3)     # 遗漏回补
dev = load_predict_numbers('ssq', method='deviation', side='cold', explore_ratio=0)
shrink = load_predict_numbers('ssq', method='filter', amount=3,
                              sum_range=(90, 120), prime_range=(2, 3),
                              zone_ratio=(2, 2, 2), exclude_numbers={7, 13})
votes = load_predict_numbers('ssq', method='ensemble', amount=1,
                             members=('frequency', 'omission', 'repeat'))
```

传 `history=` 注入 DataFrame 可完全离线；否则工厂拉取历史（支持 `if_cached=True`）。

## 回测——亲自验证"无预测力"

```python
from lotterycn import backtest, backtest_summary

results = backtest(methods=('random', 'hot', 'omission', 'ensemble'),
                   lottery_name='ssq', window=100)
print(backtest_summary(results))
```

每个策略由前 `window` 期历史驱动出票，与下一期真实开奖比对红/蓝命中数。每次复现的结论都一样：**所有策略与 `random` 表现相当**。社区机器学习尝试（LSTM/XGBoost 预测号码序列）结论一致：排列三量级（1/1000）空间上 LSTM 准确率 ≈ 4.2‰，即基线水平。任何"显著优于随机"的观察都应视为过拟合或噪声。

## 关于股票分析类比

部分策略刻意沿用了股票分析框架（动量 ≈ 追热、均值回归 ≈ 遗漏回补、均线通道 ≈ trend、量 ≈ `draws.py` 的销售/奖池特征）。类比是教学性的：在有效市场和彩票里，框架都不创造优势——但它们让随机性变得可度量。
