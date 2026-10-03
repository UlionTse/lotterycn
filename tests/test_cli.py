# coding=utf-8
# author=Ulion.Tse

from lotterycn.cli import main


def test_cli_odds(capsys):
    assert main(["odds", "ssq"]) == 0
    out = capsys.readouterr().out
    assert "一等奖" in out and "17721088" in out


def test_cli_odds_dlt_add_bet(capsys):
    assert main(["odds", "dlt", "--add-bet"]) == 0
    out = capsys.readouterr().out
    assert "4000000.0" in out  # 一等奖浮动 5e6 × 0.8


def test_cli_expect(capsys):
    assert main(["expect", "ssq"]) == 0
    out = capsys.readouterr().out
    assert "bet_price_yuan" in out and "return_rate" in out


def test_cli_check_offline(capsys):
    argv = ["check", "ssq", "--number", "01,05,12,18,27,33|08", "--draw", "01,05,12,18,27,33|08"]
    assert main(argv) == 0
    assert "一等奖" in capsys.readouterr().out


def test_cli_lottery_error_returns_1(capsys):
    assert main(["odds", "abc"]) == 1
    assert "error" in capsys.readouterr().out


def test_cli_predict_unknown_method_returns_1(capsys):
    assert main(["predict", "ssq", "--method", "nope"]) == 1
