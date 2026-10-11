# 策略（仅供娱乐）

`lotterycn.predict` 内置 11 个选号策略与 1 个可组合缩水引擎。**它们都不具备任何预测力**——开奖是独立随机事件，所有策略的期望收益与 `random` 基线完全相同。本模块仅用于统计观察与娱乐。

| 策略 | 别名 | 流派 | 思路 |
|---|---|---|---|
| `random` | — | 基线 | 均匀随机——一切策略的对照 |
| `frequency` | `hot` / `cold` | 走势图 | 滑动窗口（`recent_n`）频率选号，`explore_ratio` 控制确定性 |
| `omission` | `chase` | 走势图 | 遗漏回补：当前遗漏 / 平均遗漏，"热后转冷"排最前 |
| `deviation` | `chisq` | 统计 | 卡方偏离度（实际 − 期望）² / 期望；`side='hot'` 或 `'cold'` |
| `repeat` | — | 社区 | 重号 / 邻号(±1) / 斜连号（上上期±1）三权重打分 |
| `trend` | — | 股票框架 | 和值均线通道：候选和值落入 MA ± k·σ 才保留 |
| `tail` | — | 走势图 | 两级选号：先按尾数（号码%10）频率选尾，再尾内取号 |
| `markov` | — | 序列 | 一阶转移采样 P(本期出现\|上期出现/未出现)——独立下退化为频率 |
| `markov2` | — | 序列 | 二阶转移（上两期 4 态）——展示高阶状态稀疏后退化均匀 |
| `filter` | — | 形态 | 可组合缩水：和值 / 奇偶 / 质合 / AC 值 / 连号区间，三区比与 012 路精确匹配，杀号 |
| `ensemble` | — | 集成 | 多策略投票：成员各出 top-k，按号码得票排序（`votes_min` 阈值） |

## 用法

```python
from lotterycn import load_predict_numbers

# method='hot' 是 frequency + mode='hot' 的别名
picks = load_predict_numbers("ssq", method="hot", amount=5)
chase = load_predict_numbers("ssq", method="omission", amount=3)  # 遗漏回补
dev = load_predict_numbers("ssq", method="deviation", side="cold", explore_ratio=0)
shrink = load_predict_numbers(
    "ssq",
    method="filter",
    amount=3,
    sum_range=(90, 120),
    prime_range=(2, 3),
    zone_ratio=(2, 2, 2),
    exclude_numbers={7, 13},
)
votes = load_predict_numbers(
    "ssq",
    method="ensemble",
    amount=1,
    members=("frequency", "omission", "repeat"),
)
```

传 `history=` 注入 DataFrame 可完全离线；否则工厂拉取历史（支持 `if_cached=True`）。

## Filter 形态指标口径

所有 `*_range` 过滤为闭区间 `(lo, hi)`；`zone_ratio` 与 `mod3_range` 为计数三元组的**精确匹配**。

- **AC 值** —— 排序去重后两两差值的不同个数 −（号码个数 − 1）。例：`{01,02,06,13,27,33}` 两两差值恰有 15 个不同值，AC = 15 −（6 − 1）= 10（6 个号的理论最大值）；全连号 `{01..06}` 只有 5 个，AC = 0。
- **三区比（精确匹配）** —— 红球池三等分，各区计数必须与给定 `(一区, 二区, 三区)` 完全一致。各彩种分界：

  | 彩种（红球池） | 一区 | 二区 | 三区 |
  |---|---|---|---|
  | `ssq`（1-33） | 1-11 | 12-22 | 23-33 |
  | `qlc`（1-30） | 1-10 | 11-20 | 21-30 |
  | `kl8`（1-80） | 1-27 | 28-54 | 55-80 |
  | `dlt`（1-35） | 1-12 | 13-24 | 25-35 |
  | 数字型 `3d`/`pls`/`plw`/`qxc`（0-9） | 0-3 | 4-6 | 7-9 |

- **012 路 `mod3_range`（精确匹配）** —— 号码除以 3 余 0 / 1 / 2 的计数三元组必须与给定值完全一致。
- **质数** —— {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}（1 不算质数）。
- **连号对数** —— 排序去重后相邻两数恰差 1 的对数。

与其他策略一致：过滤只改变选号的分布形态，不改变任何一注的中奖概率。

## 回测——亲自验证"无预测力"

```python
from lotterycn import backtest, backtest_summary

results = backtest(
    methods=("random", "hot", "omission", "ensemble"),
    lottery_name="ssq",
    window=100,
)
print(backtest_summary(results))
```

每个策略由前 `window` 期历史驱动出票，与下一期真实开奖比对红/蓝命中数。每次复现的结论都一样：**所有策略与 `random` 表现相当**。社区机器学习尝试（LSTM/XGBoost 预测号码序列）结论一致：排列三量级（1/1000）空间上 LSTM 准确率 ≈ 4.2‰，即基线水平。任何"显著优于随机"的观察都应视为过拟合或噪声。

## 关于股票分析类比

部分策略刻意沿用了股票分析框架（动量 ≈ 追热、均值回归 ≈ 遗漏回补、均线通道 ≈ trend、量 ≈ `draws.py` 的销售/奖池特征）。类比是教学性的：在有效市场和彩票里，框架都不创造优势——但它们让随机性变得可度量。
