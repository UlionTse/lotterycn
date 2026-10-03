# predict — 选号策略集

策略为纯注入设计：`needs_history` / `method` / `aliases` 三个类属性声明，由基类 `__init_subclass__` 自动注册；`load_predict_numbers` 工厂统一解析并注入历史数据。

!!! warning "仅供娱乐，不构成任何预测力"

    彩票开奖为独立随机事件，任何策略的期望收益都与 `random` 基线完全相同。

::: lotterycn.predict
    options:
      members:
        - load_predict_numbers
        - BasePredictor
        - RandomPredictor
        - FrequencyPredictor
        - OmissionPredictor
        - DeviationPredictor
        - RepeatNeighborPredictor
        - TrendPredictor
        - TailPredictor
        - MarkovPredictor
        - Markov2Predictor
        - FilterPredictor
        - EnsemblePredictor
