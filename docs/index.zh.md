---
hide:
  - navigation
---

# LotteryCN

<div class="hero" markdown>

![LotteryCN](assets/lotterycn_logo.png){ .logo }

**一个有趣好玩的中国福利彩票与体育彩票分析库**——官方开奖数据、组合数学概率与期望、选号策略与预测回测、中奖校验。

[快速上手](#quickstart){ .md-button .md-button--primary }
[API 参考](api/odds.md){ .md-button }

</div>

本库中每一个奖级、中奖条件与固定奖金，均对照**官方游戏规则**核实（`cwl.gov.cn` 中国福利彩票、`lottery.gov.cn` 中国体育彩票）。

<div class="grid cards" markdown>

- :material-chart-line:{ .lg .middle } **选号策略与回测（核心）**

    ---

    11 个策略 + 可组合缩水引擎，内置滚动回测——所有策略与随机等期望。

- :material-database:{ .lg .middle } **只采官方数据**

    ---

    中奖号码与开奖详情（销售额 / 奖池 / 各奖级中奖情况 / 省级分布）直接来自官方渠道——无第三方爬虫。

- :material-calculator:{ .lg .middle } **组合数学的概率与期望**

    ---

    精确组合计数各奖级命中数；概率、期望、返奖率由官方奖金表推导；支持投注号码即时校验。

- :material-check-decagram:{ .lg .middle } **完整流水线**

    ---

    收集（增量缓存）→ 分析 → 预测 → 回测 → 校验。

</div>

## 快速上手 { #quickstart }

```python
from lotterycn import (backtest, backtest_summary, load_history_data,
                       load_number_statistics, load_predict_numbers,
                       load_check_result, load_prize_expectation)

df = load_history_data('ssq', if_cached=True)          # 收集（缓存增量）
stats = load_number_statistics('ssq', history=df)      # 分析
picks = load_predict_numbers('ssq', method='hot', amount=5)  # 策略沙盒
print(load_prize_expectation('ssq'))                   # 概率与期望
print(backtest_summary(backtest(methods=('random', 'hot'),
                                lottery_name='ssq', window=100)))
```

详见 [API 参考](api/odds.md)。

!!! warning "诚实声明"

    彩票开奖是**独立随机事件**。历史统计无法预测未来开奖——本库任何策略的期望
    收益都与随机选号完全相同。一切内容仅用于统计观察与娱乐。请理性购彩（18+）。
