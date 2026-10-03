# predict — Number-generation strategies

Strategies are pure-injection: declared via the `needs_history` / `method` / `aliases` class attributes and auto-registered by the base `__init_subclass__`; the `load_predict_numbers` factory resolves them and injects history data.

!!! warning "For entertainment only — no predictive power"

    Lottery draws are independent random events; every strategy has exactly the same expected value as the `random` baseline.

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
