# coding=utf-8
# author=Ulion.Tse

"""lotterycn 命令行入口。

用法：

```text
lotterycn odds    <game> [--pick N] [--pool-over-800m] [--add-bet]
lotterycn expect  <game> [--pool-over-800m] [--add-bet]
lotterycn stats   <game> [--cached]
lotterycn predict <game> [--method hot] [--amount 5] [--cached]
lotterycn check   <game> --number '01,...|08' [--draw '...'] [--cached]
lotterycn backtest <game> [--methods random,frequency] [--window 100] [--cached]
```

`--cached` 使用本地缓存与增量更新（需首次联网建立缓存）。
"""

import argparse
import sys

from lotterycn.analysis import load_number_statistics
from lotterycn.backtest import backtest as run_backtest
from lotterycn.backtest import backtest_summary
from lotterycn.check import load_check_result
from lotterycn.draws import load_draw_detail, load_first_prize_by_province, load_prize_results
from lotterycn.odds import load_prize_expectation, load_prize_odds
from lotterycn.predict import load_predict_numbers
from lotterycn.utils import LotteryError


def _print(frame):
    print(frame.to_string(index=False))


def build_parser() -> argparse.ArgumentParser:
    """构建 CLI 参数解析器：定义全部子命令与选项。

    :return: argparse.ArgumentParser, 配置完成的解析器实例。
    """
    parser = argparse.ArgumentParser(
        prog="lotterycn",
        description="Chinese welfare & sports lottery data and analysis toolkit",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    odds_p = sub.add_parser("odds", help="per-prize odds table")
    odds_p.add_argument("lottery_name", help="ssq | qlc | kl8 | 3d | dlt | pls | plw | qxc")
    odds_p.add_argument("--pick", type=int, default=None, help="kl8: play type 1-10")
    odds_p.add_argument("--pool-over-800m", action="store_true", help="dlt: fixed prizes for pool >= 800m")
    odds_p.add_argument("--add-bet", action="store_true", help="dlt: additional bet (3 yuan, floating x0.8)")

    expect_p = sub.add_parser("expect", help="expected value & return rate per bet")
    expect_p.add_argument("lottery_name")
    expect_p.add_argument("--pool-over-800m", action="store_true", help="dlt only")
    expect_p.add_argument("--add-bet", action="store_true", help="dlt only")

    stats_p = sub.add_parser("stats", help="number frequency & omission statistics")
    stats_p.add_argument("lottery_name")
    stats_p.add_argument("--cached", action="store_true", help="use local cache with incremental update")

    predict_p = sub.add_parser("predict", help="generate numbers with a strategy (for entertainment only)")
    predict_p.add_argument("lottery_name")
    predict_p.add_argument("--method", default="random", help="random | frequency (aliases hot/cold) | markov | filter")
    predict_p.add_argument("--amount", type=int, default=1)
    predict_p.add_argument("--cached", action="store_true", help="use local cache with incremental update")

    detail_p = sub.add_parser("detail", help="draw details: sales, pool, numbers")
    detail_p.add_argument("lottery_name")
    detail_p.add_argument("--cached", action="store_true", help="use local cache with incremental update")

    prizes_p = sub.add_parser("prizes", help="winner counts & per-bet prize per level (long table)")
    prizes_p.add_argument("lottery_name")
    prizes_p.add_argument("--cached", action="store_true")

    prov_p = sub.add_parser("provinces", help="first-prize distribution by province (long table)")
    prov_p.add_argument("lottery_name")
    prov_p.add_argument("--cached", action="store_true")

    backtest_p = sub.add_parser("backtest", help="rolling-window strategy backtest vs random baseline")
    backtest_p.add_argument("lottery_name")
    backtest_p.add_argument("--methods", default="random,frequency", help="comma-separated strategy names")
    backtest_p.add_argument("--window", type=int, default=100)
    backtest_p.add_argument("--trials", type=int, default=None)
    backtest_p.add_argument("--cached", action="store_true")

    check_p = sub.add_parser("check", help="check a ticket against a draw")
    check_p.add_argument("lottery_name")
    check_p.add_argument("--number", required=True, help="ticket, e.g. '01,05,12,18,27,33|08'")
    check_p.add_argument("--draw", default=None, help="draw numbers; default: fetch the latest draw")
    check_p.add_argument("--cached", action="store_true", help="use local cache for the latest draw")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI 主入口：解析子命令并分发到对应 load_* 函数，打印结果表。

    :param argv: list[str], optional, 命令行参数；None 时取 sys.argv[1:]。
    :return: int, 退出码：0 成功；1 彩票参数错误（LotteryError）。
    """
    try:
        # Windows 控制台默认 GBK，重定向时中文列名会乱码
        reconfigure = getattr(sys.stdout, "reconfigure", None)
        if callable(reconfigure) and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
            reconfigure(encoding="utf-8")
    except (AttributeError, ValueError, OSError):
        pass
    args = build_parser().parse_args(argv)
    cached_flag = getattr(args, "cached", False)
    dlt_kwargs = (
        {"if_pool_over_800m": args.pool_over_800m, "if_add_bet": args.add_bet} if args.lottery_name == "dlt" else {}
    )
    try:
        if args.command == "odds":
            kwargs = dict(dlt_kwargs)
            if args.lottery_name == "kl8":
                kwargs["pick"] = args.pick
            _print(load_prize_odds(args.lottery_name, **kwargs))
        elif args.command == "expect":
            _print(load_prize_expectation(args.lottery_name, **dlt_kwargs))
        elif args.command == "stats":
            _print(load_number_statistics(args.lottery_name, if_cached=cached_flag))
        elif args.command == "predict":
            _print(
                load_predict_numbers(args.lottery_name, method=args.method, amount=args.amount, if_cached=cached_flag)
            )
        elif args.command == "detail":
            _print(load_draw_detail(args.lottery_name, if_cached=cached_flag))
        elif args.command == "prizes":
            _print(load_prize_results(args.lottery_name, if_cached=cached_flag))
        elif args.command == "provinces":
            _print(load_first_prize_by_province(args.lottery_name, if_cached=cached_flag))
        elif args.command == "backtest":
            methods = tuple(m.strip() for m in args.methods.split(",") if m.strip())
            results = run_backtest(
                methods=methods,
                lottery_name=args.lottery_name,
                window=args.window,
                trials=args.trials,
                if_cached=cached_flag,
            )
            _print(results)
            _print(backtest_summary(results))
        elif args.command == "check":
            if args.draw:
                _print(load_check_result(args.lottery_name, args.number, args.draw))
            else:
                _print(load_check_result(args.lottery_name, args.number, if_cached=cached_flag))
        return 0
    except LotteryError as e:
        print(f"error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
