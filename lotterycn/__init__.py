__version__ = "1.0.0"
__author__ = "Ulion.Tse"


from lotterycn.analysis import load_number_statistics
from lotterycn.backtest import backtest, backtest_summary
from lotterycn.check import load_check_result
from lotterycn.data import load_history_data, load_random_data, lottery_pool
from lotterycn.draws import load_draw_detail, load_first_prize_by_province, load_prize_results
from lotterycn.odds import load_dlt_compound_expectation, load_prize_expectation, load_prize_odds
from lotterycn.predict import load_predict_numbers

__all__ = [
    "lottery_pool",
    "load_random_data",
    "load_history_data",
    "load_prize_odds",
    "load_prize_expectation",
    "load_dlt_compound_expectation",
    "load_check_result",
    "load_number_statistics",
    "load_predict_numbers",
    "load_draw_detail",
    "load_prize_results",
    "load_first_prize_by_province",
    "backtest",
    "backtest_summary",
]
