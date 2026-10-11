# coding=utf-8
# author=Ulion.Tse

"""选号策略集（娱乐与教学用途）。

!!! warning "仅供娱乐，不构成任何预测力"

    彩票开奖为独立随机事件，以下任何策略都不具备真实预测力，任何一注号码的
    中奖概率与随机选号完全相同。本模块仅提供统计选号参考与教学示例；
    `random` 为基线策略，任何策略都应先与它对比（可用 `lotterycn.backtest`
    复现实验）。请理性购彩。

策略来源（社区彩票圈/股票分析框架的平移，均无真实预测力）：
    随机基线      random
    走势图派      frequency（冷热）、omission（遗漏回补）、tail（尾数）、trend（和值均线通道）
    形态派        filter（奇偶/大小/质合/012路/三区比/AC值/连号/杀号 可组合缩水）
    序列派        markov（一阶）、markov2（二阶，稀疏性教学）、repeat（重号/邻号/斜连号）
    统计派        deviation（卡方偏离度）
    集成派        ensemble（多策略投票）

设计约定：策略类是"纯注入"的——构造器不做任何网络 IO，历史数据由
`load_predict_numbers` 工厂统一解析并注入（子类通过 `needs_history`
声明是否依赖历史，通过 `aliases` 声明别名，两者均由基类自动注册）。
需要历史数据的子类调用 `self._require_history()`。
"""

import math
import random
import statistics
from typing import Optional

import numpy
import pandas

from .analysis import NUMBER_POOLS, _miss_statistics, _occurrence_matrix, _split
from .data import GAME_ZH_NAMES, load_history_data, load_random_data
from .utils import LotteryError

CL_COLS = [
    "lottery_name",
    "lottery_zh_name",
    "lottery_order",
    "lottery_date",
    "lottery_red",
    "lottery_blue",
]

RED_COUNTS = {"ssq": 6, "qlc": 7, "kl8": 20, "3d": 3, "pls": 3, "plw": 5, "qxc": 6, "dlt": 5}
BLUE_COUNTS = {"ssq": 1, "qlc": 1, "dlt": 2, "qxc": 1}

# 号码池为两位数区间的彩种，输出与官方开奖公告一致（两位补零）；数字型彩种不补零
PAD_GAMES = {"ssq", "qlc", "kl8", "dlt"}

# 仅在需要联网拉取历史时透传给 load_history_data 的参数；其余 kwargs 归策略构造器
_FETCH_KEYS = ("if_cached", "timeout", "proxies", "max_retries", "sleep_seconds", "begin_date")

PRIMES = frozenset({2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31})


def _format_numbers(numbers: list, if_pad: bool) -> str:
    if if_pad:
        return ",".join(f"{n:02d}" for n in numbers)
    return ",".join(map(str, numbers))


def _frequency_scores(frame: pandas.DataFrame, side: str, pool: dict) -> dict:
    lo, hi = pool[side]
    counts = _occurrence_matrix(frame, f"lottery_{side}", lo, hi).sum(axis=0)
    return {n: int(counts[i]) for i, n in enumerate(range(lo, hi + 1))}


def _pick_by_score(scores: dict, k: int, mode: str = "hot", explore_ratio: float = 0.5) -> list:
    """按分数取 k 个号码：explore_ratio=0 时确定性取头部，越大越随机。"""
    if not scores or k <= 0:
        return []
    ranked = sorted(scores, key=lambda n: scores[n], reverse=(mode == "hot"))
    k = min(k, len(ranked))
    # 候选池 = 头部 k 个再外扩 ceil(explore_ratio × (候选总数 − k)) 个：
    # explore_ratio=0 → 恰好头部 k 个（确定性）；=1 → 全池均匀随机。
    m = k + math.ceil(max(0.0, min(1.0, explore_ratio)) * (len(ranked) - k))
    return sorted(random.sample(ranked[:m], k))


def _weighted_sample_no_replacement(weights: dict, k: int) -> list:
    """按权重不放回采样（Efraimidis-Spirakis 算法）。"""
    if not weights or k <= 0:
        return []
    k = min(k, len(weights))
    # Efraimidis–Spirakis：key = U^(1/w)（U ~ Uniform(0,1)），按 key 降序取前 k 个
    # 等价于按权重 w 的不放回加权抽样；权重全相等时退化为等概率抽样。
    keyed = sorted(weights, key=lambda n: random.random() ** (1.0 / max(weights[n], 1e-9)), reverse=True)
    return sorted(keyed[:k])


def _ac_value(reds: list) -> int:
    """AC 值 = 号码两两差值的不同个数 - (号码个数 - 1)。"""
    uniq = sorted(set(reds))
    if len(uniq) < 2:
        return 0
    # 例：{01,02,06,13,27,33} 两两差值恰有 15 个不同值 → AC = 15 - (6 - 1) = 10（6 个号的理论最大值）；
    # 全连号 {01..06} 差值只有 {1..5} 共 5 个 → AC = 0。
    diffs = {b - a for i, a in enumerate(uniq) for b in uniq[i + 1 :]}
    return len(diffs) - (len(uniq) - 1)


def _consecutive_pairs(reds: list) -> int:
    uniq = sorted(set(reds))
    return sum(1 for a, b in zip(uniq, uniq[1:]) if b - a == 1)


def _zone_counts(reds: list, pool: dict) -> tuple:
    lo, hi = pool["red"]
    width = (hi - lo + 1) / 3
    # 号码池三等分：n 落入第 int((n - lo) / width) 区（width = 池大小 / 3），
    # min(2, ·) 兜底除法边界；各彩种确切分界见 docs/strategies「Filter 形态指标口径」。
    counts = [0, 0, 0]
    for n in reds:
        counts[min(2, int((n - lo) / width))] += 1
    return tuple(counts)


def _mod3_counts(reds: list) -> tuple:
    counts = [0, 0, 0]
    for n in reds:
        counts[n % 3] += 1
    return tuple(counts)


class BasePredictor:
    """策略基类（纯注入，构造器零 IO，torch Layer 风格）。

    子类声明三个类属性，注册由基类 `__init_subclass__` 自动完成：
        needs_history — 是否依赖历史数据（工厂据此决定是否联网拉取并注入）；
        method        — 输出 DataFrame 的 method 列标签，同时作为注册键；
        aliases       — 别名 → 策略参数覆盖（可选）。

    :param lottery_name: str, must in NUMBER_POOLS.
    :param history: pandas.DataFrame, 历史开奖数据；由工厂注入或调用方显式传入。
        不依赖历史的子类（needs_history = False）可为 None。
    """

    method = "base"
    needs_history = True
    aliases: dict[str, dict] = {}
    _registry: dict[str, type["BasePredictor"]] = {}
    _alias_map: dict[str, tuple[type["BasePredictor"], dict]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BasePredictor._registry[cls.method] = cls
        for alias, overrides in cls.aliases.items():
            BasePredictor._alias_map[alias] = (cls, overrides)

    def __init__(self, lottery_name: str = "ssq", history: Optional[pandas.DataFrame] = None):
        if lottery_name not in NUMBER_POOLS:
            raise LotteryError(f"unsupported lottery name {lottery_name!r}, must be one of {sorted(NUMBER_POOLS)}")
        self.lottery_name = lottery_name
        self.pool = NUMBER_POOLS[lottery_name]
        self.history = history

    def _require_history(self) -> pandas.DataFrame:
        if self.history is None:
            raise LotteryError(f"{type(self).__name__} requires history data")
        return self.history

    def predict(self, amount: int = 1) -> pandas.DataFrame:
        """生成一注选号（抽象方法，各策略子类实现）。"""
        raise NotImplementedError

    def _to_frame(self, tickets: list) -> pandas.DataFrame:
        frame = pandas.DataFrame(tickets, columns=["lottery_red", "lottery_blue"])
        frame.insert(0, "lottery_date", "")
        frame.insert(0, "lottery_order", range(len(frame)))
        frame.insert(0, "lottery_name", self.lottery_name)
        frame.insert(1, "lottery_zh_name", GAME_ZH_NAMES.get(self.lottery_name, ""))
        frame["method"] = self.method
        return frame


class RandomPredictor(BasePredictor):
    """基线策略：均匀随机（等价 load_random_data）。"""

    method = "random"
    needs_history = False

    def predict(self, amount: int = 1) -> pandas.DataFrame:
        """均匀随机生成选号（random 基线）。"""
        if_pad = self.lottery_name in PAD_GAMES
        tickets: list = []
        for _ in range(amount):
            parts = load_random_data(lottery_name=self.lottery_name, amount=1, is_detail_result=True)[0]
            reds = [int(x) for x in parts[0].split(",")]
            blues = [int(x) for x in parts[1].split(",")] if len(parts) > 1 else []
            tickets.append((_format_numbers(reds, if_pad), _format_numbers(blues, if_pad) if blues else ""))
        return self._to_frame(tickets)


class FrequencyPredictor(BasePredictor):
    """冷热号策略（动量）：按近 N 期出现频率取号。

    :param recent_n: int, 滑动窗口期数，None 表示全历史。
    :param mode: str, 'hot' 取高频头部，'cold' 取低频头部。
    :param explore_ratio: float, 0~1。0 为确定性取头部 k 个；越大越随机。
    """

    method = "frequency"
    aliases = {"hot": {"mode": "hot"}, "cold": {"mode": "cold"}}

    def __init__(
        self,
        lottery_name: str = "ssq",
        history: Optional[pandas.DataFrame] = None,
        recent_n: Optional[int] = None,
        mode: str = "hot",
        explore_ratio: float = 0.5,
    ):
        super().__init__(lottery_name, history)
        if mode not in ("hot", "cold"):
            raise LotteryError(f"mode must be 'hot' or 'cold', got {mode!r}")
        self.mode = mode
        self.explore_ratio = explore_ratio
        frame = self._require_history()
        window = frame.tail(recent_n) if recent_n else frame
        self.scores = {
            side: _frequency_scores(window, side, self.pool) for side in ("red", "blue") if side in self.pool
        }

    def predict(self, amount: int = 1) -> pandas.DataFrame:
        """按滑动窗口频率得分选号：mode 控制冷/热，explore_ratio 控制探索随机性。"""
        if_pad = self.lottery_name in PAD_GAMES
        tickets: list = []
        for _ in range(amount):
            reds = _pick_by_score(
                self.scores["red"], k=RED_COUNTS[self.lottery_name], mode=self.mode, explore_ratio=self.explore_ratio
            )
            blues = (
                _pick_by_score(
                    self.scores["blue"],
                    k=BLUE_COUNTS[self.lottery_name],
                    mode=self.mode,
                    explore_ratio=self.explore_ratio,
                )
                if "blue" in self.scores
                else []
            )
            tickets.append((_format_numbers(reds, if_pad), _format_numbers(blues, if_pad) if blues else ""))
        return self._to_frame(tickets)


class OmissionPredictor(BasePredictor):
    """遗漏回补策略（均值回归）：按"当前遗漏 / 平均遗漏"的偏移度取号。

    直觉：某号码当前连续未出期数远超其历史平均遗漏时，社区称之为"遗漏
    回补"。数学真相：独立开奖下这仍是均匀抽样的另一种表达，不改变概率。

    :param recent_n: int, 计算平均遗漏的窗口期数，None 表示全历史。
    """

    method = "omission"
    aliases = {"chase": {}}

    def __init__(
        self,
        lottery_name: str = "ssq",
        history: Optional[pandas.DataFrame] = None,
        recent_n: Optional[int] = None,
        explore_ratio: float = 0.5,
    ):
        super().__init__(lottery_name, history)
        self.explore_ratio = explore_ratio
        frame = self._require_history()
        window = frame.tail(recent_n) if recent_n else frame
        self.scores = {
            side: self._omission_scores(window, side, self.pool) for side in ("red", "blue") if side in self.pool
        }

    @staticmethod
    def _omission_scores(frame: pandas.DataFrame, side: str, pool: dict) -> dict:
        lo, hi = pool[side]
        hits = _occurrence_matrix(frame, f"lottery_{side}", lo, hi)
        counts, currents, _, miss_sums = _miss_statistics(hits)
        scores = {}
        for i, n in enumerate(range(lo, hi + 1)):
            avg = miss_sums[i] / counts[i] if counts[i] else float(len(frame))
            scores[n] = currents[i] / max(avg, 1.0)
        return scores

    def predict(self, amount: int = 1) -> pandas.DataFrame:
        """遗漏回补选号：当前遗漏 / 平均遗漏比值越高越优先（热后转冷）。"""
        if_pad = self.lottery_name in PAD_GAMES
        tickets: list = []
        for _ in range(amount):
            reds = _pick_by_score(
                self.scores["red"], k=RED_COUNTS[self.lottery_name], mode="hot", explore_ratio=self.explore_ratio
            )
            blues = (
                _pick_by_score(
                    self.scores["blue"], k=BLUE_COUNTS[self.lottery_name], mode="hot", explore_ratio=self.explore_ratio
                )
                if "blue" in self.scores
                else []
            )
            tickets.append((_format_numbers(reds, if_pad), _format_numbers(blues, if_pad) if blues else ""))
        return self._to_frame(tickets)


class DeviationPredictor(BasePredictor):
    """卡方偏离度策略：按 (实际频次 - 期望频次)² / 期望频次 取号。

    :param recent_n: int, 窗口期数，None 表示全历史。
    :param side: str, 'hot' 取正偏离头部（实际多于期望），'cold' 取负偏离头部。
    """

    method = "deviation"
    aliases = {"chisq": {}}

    def __init__(
        self,
        lottery_name: str = "ssq",
        history: Optional[pandas.DataFrame] = None,
        recent_n: Optional[int] = None,
        side: str = "hot",
        explore_ratio: float = 0.5,
    ):
        super().__init__(lottery_name, history)
        if side not in ("hot", "cold"):
            raise LotteryError(f"side must be 'hot' or 'cold', got {side!r}")
        self.side = side
        self.explore_ratio = explore_ratio
        frame = self._require_history()
        window = frame.tail(recent_n) if recent_n else frame
        self.scores = {}
        for side_name in ("red", "blue") if "blue" in self.pool else ("red",):
            lo, hi = self.pool[side_name]
            counts = _frequency_scores(window, side_name, self.pool)
            drawn_per_draw = (
                RED_COUNTS[self.lottery_name] if side_name == "red" else BLUE_COUNTS.get(self.lottery_name, 0)
            )
            expected = len(window) * drawn_per_draw / (hi - lo + 1) if len(window) else 0.0
            # 期望频次 = 窗口期数 × 每期开出个数 ÷ 号码池大小（均匀开奖下的理论均值）；
            # 卡方偏离度 = (实际 − 期望)² / 期望，衡量单个号码对均匀性的偏离方向与幅度。
            self.scores[side_name] = {n: (c - expected) ** 2 / max(expected, 1e-9) for n, c in counts.items()}

    def predict(self, amount: int = 1) -> pandas.DataFrame:
        """卡方偏离选号：按 (实际-期望)²/期望 的偏离度选号，side 控制冷/热方向。"""
        if_pad = self.lottery_name in PAD_GAMES
        tickets: list = []
        for _ in range(amount):
            reds = _pick_by_score(
                self.scores["red"], k=RED_COUNTS[self.lottery_name], mode=self.side, explore_ratio=self.explore_ratio
            )
            blues = (
                _pick_by_score(
                    self.scores["blue"],
                    k=BLUE_COUNTS[self.lottery_name],
                    mode=self.side,
                    explore_ratio=self.explore_ratio,
                )
                if "blue" in self.scores
                else []
            )
            tickets.append((_format_numbers(reds, if_pad), _format_numbers(blues, if_pad) if blues else ""))
        return self._to_frame(tickets)


class RepeatNeighborPredictor(BasePredictor):
    """重号/邻号/斜连号策略：按与最近两期号码的邻近关系打分。

    score(n) = repeat_weight·[n ∈ 上期] + neighbor_weight·[n 与上期某号相差 1]
               + jump_weight·[n 与上上期某号相差 1]（斜连号）。

    :param repeat_weight: float, 重号权重。
    :param neighbor_weight: float, 邻号权重。
    :param jump_weight: float, 斜连号（上上期 ±1）权重。
    """

    method = "repeat"

    def __init__(
        self,
        lottery_name: str = "ssq",
        history: Optional[pandas.DataFrame] = None,
        repeat_weight: float = 2.0,
        neighbor_weight: float = 1.0,
        jump_weight: float = 1.0,
        explore_ratio: float = 0.5,
    ):
        super().__init__(lottery_name, history)
        self.repeat_weight = repeat_weight
        self.neighbor_weight = neighbor_weight
        self.jump_weight = jump_weight
        self.explore_ratio = explore_ratio
        frame = self._require_history()
        if len(frame) < 1:
            raise LotteryError("repeat predictor needs at least 1 draw of history")
        self.last_sets = {
            side: set(_split(frame.iloc[-1][f"lottery_{side}"])) for side in ("red", "blue") if side in self.pool
        }
        prev_sets = (
            {side: set(_split(frame.iloc[-2][f"lottery_{side}"])) for side in ("red", "blue") if side in self.pool}
            if len(frame) >= 2
            else None
        )
        self.scores = {}
        for side in ("red", "blue") if "blue" in self.pool else ("red",):
            lo, hi = self.pool[side]
            last = self.last_sets.get(side, set())
            prev = prev_sets.get(side, set()) if prev_sets else set()
            scores = {}
            for n in range(lo, hi + 1):
                score = self.repeat_weight * (n in last)
                score += self.neighbor_weight * ((n - 1) in last or (n + 1) in last)
                score += self.jump_weight * ((n - 1) in prev or (n + 1) in prev)
                scores[n] = score
            self.scores[side] = scores

    def predict(self, amount: int = 1) -> pandas.DataFrame:
        """重号 / 邻号 / 斜连号三权重打分选号。"""
        if_pad = self.lottery_name in PAD_GAMES
        tickets: list = []
        for _ in range(amount):
            reds = _pick_by_score(
                self.scores["red"], k=RED_COUNTS[self.lottery_name], mode="hot", explore_ratio=self.explore_ratio
            )
            blues = (
                _pick_by_score(
                    self.scores["blue"], k=BLUE_COUNTS[self.lottery_name], mode="hot", explore_ratio=self.explore_ratio
                )
                if "blue" in self.scores
                else []
            )
            tickets.append((_format_numbers(reds, if_pad), _format_numbers(blues, if_pad) if blues else ""))
        return self._to_frame(tickets)


class TrendPredictor(BasePredictor):
    """和值均线通道策略（股票均线框架平移）：按和值的 MA ± k·σ 生成和值带。

    随机候选的和值落入带内才保留。数学真相：和值序列无趋势，
    带只是历史分布的描述。

    :param window: int, 均线与波动率计算的窗口期数。
    :param k_sigma: float, 通道宽度系数（MA ± k·σ）。
    :param max_trials: int, 最大尝试次数。
    """

    method = "trend"

    def __init__(
        self,
        lottery_name: str = "ssq",
        history: Optional[pandas.DataFrame] = None,
        window: int = 10,
        k_sigma: float = 1.0,
        max_trials: int = 10000,
    ):
        super().__init__(lottery_name, history)
        frame = self._require_history()
        if len(frame) < 2:
            raise LotteryError("trend predictor needs at least 2 draws of history")
        self.window = window
        self.k_sigma = k_sigma
        self.max_trials = max_trials
        sums = [sum(_split(t)) for t in frame["lottery_red"].tail(window)]
        # 和值带 = 近 window 期红球和值的均值 ± k·σ（即文档记号 MA ± k·σ）。
        # σ 取总体标准差 pstdev（分母 N），与记号 σ 一致；样本标准差（分母 N−1）才记作 s。
        self.sum_band = (
            statistics.mean(sums) - k_sigma * statistics.pstdev(sums),
            statistics.mean(sums) + k_sigma * statistics.pstdev(sums),
        )

    def predict(self, amount: int = 1) -> pandas.DataFrame:
        """和值均线通道选号：随机候选的和值须落入 MA ± k·σ 才保留。"""
        tickets: list = []
        trials = 0
        while len(tickets) < amount and trials < self.max_trials:
            trials += 1
            parts = load_random_data(lottery_name=self.lottery_name, amount=1, is_detail_result=True)[0]
            reds = [int(x) for x in parts[0].split(",")]
            if not self.sum_band[0] <= sum(reds) <= self.sum_band[1]:
                continue
            tickets.append((parts[0], parts[1] if len(parts) > 1 else ""))
        if len(tickets) < amount:
            raise LotteryError("sum band too narrow, no ticket matched")
        return self._to_frame(tickets)


class TailPredictor(BasePredictor):
    """尾数策略：先按尾数（号码 % 10）频率选尾集合，再在选中尾内取号。

    仅作用于红球/前区；蓝球按普通频率取号。数字型彩种每位 0-9，
    尾即号码本身，策略退化为号码级频率。

    :param tail_count: int, 选用的尾数个数；None 时按号码池与注数自动推导。
    """

    method = "tail"

    def __init__(
        self,
        lottery_name: str = "ssq",
        history: Optional[pandas.DataFrame] = None,
        recent_n: Optional[int] = None,
        mode: str = "hot",
        explore_ratio: float = 0.5,
        tail_count: Optional[int] = None,
    ):
        super().__init__(lottery_name, history)
        self.mode = mode
        self.explore_ratio = explore_ratio
        self.tail_count = tail_count
        frame = self._require_history()
        window = frame.tail(recent_n) if recent_n else frame
        self.tail_scores = {
            side: self._tail_scores(window, side, self.pool) for side in ("red", "blue") if side in self.pool
        }

    @staticmethod
    def _tail_scores(frame: pandas.DataFrame, side: str, pool: dict) -> dict:
        lo, hi = pool[side]
        counts = _occurrence_matrix(frame, f"lottery_{side}", lo, hi).sum(axis=0)
        scores = {t: 0 for t in range(0, 10) if any(lo <= t + 10 * m <= hi for m in range(0, hi // 10 + 1))}
        for i, n in enumerate(range(lo, hi + 1)):
            tail = n % 10
            if tail in scores:
                scores[tail] += int(counts[i])
        return scores

    def _auto_tail_count(self, k: int, pool: dict) -> int:
        lo, hi = pool["red"]
        per_tail = max(1, (hi - lo + 1) / 10)
        return max(2, math.ceil(k / per_tail))

    def predict(self, amount: int = 1) -> pandas.DataFrame:
        """两级尾数选号：先按尾数频率选尾，再在选中尾内取号。"""
        if_pad = self.lottery_name in PAD_GAMES
        tickets: list = []
        for _ in range(amount):
            k = RED_COUNTS[self.lottery_name]
            t = self.tail_count or self._auto_tail_count(k, self.pool)
            selected_tails = set(
                _pick_by_score(self.tail_scores["red"], k=t, mode=self.mode, explore_ratio=self.explore_ratio)
            )
            lo, hi = self.pool["red"]
            candidates = [n for n in range(lo, hi + 1) if n % 10 in selected_tails]
            while len(candidates) < k and selected_tails:
                # 候选不足时按尾数得分顺序补尾
                red_tail_scores = self.tail_scores["red"]
                ranked = sorted(red_tail_scores, key=lambda x: red_tail_scores[x], reverse=(self.mode == "hot"))
                for tail in ranked:
                    if tail not in selected_tails:
                        selected_tails.add(tail)
                        candidates = [n for n in range(lo, hi + 1) if n % 10 in selected_tails]
                        break
                else:
                    break
            if len(candidates) < k:
                raise LotteryError("not enough numbers for selected tails")
            reds = sorted(random.sample(candidates, k))
            blues = (
                _pick_by_score(
                    self.tail_scores["blue"],
                    k=BLUE_COUNTS[self.lottery_name],
                    mode=self.mode,
                    explore_ratio=self.explore_ratio,
                )
                if "blue" in self.tail_scores
                else []
            )
            tickets.append((_format_numbers(reds, if_pad), _format_numbers(blues, if_pad) if blues else ""))
        return self._to_frame(tickets)


class MarkovPredictor(BasePredictor):
    """一阶马尔可夫策略：按 P(本期出现 | 上期出现/未出现) 的转移概率采样。

    教学要点：对独立开奖，转移概率收敛到边际频率，本策略退化为频率法，
    用于直观验证"历史模式无预测力"。
    """

    method = "markov"

    def __init__(self, lottery_name: str = "ssq", history: Optional[pandas.DataFrame] = None):
        super().__init__(lottery_name, history)
        frame = self._require_history()
        if len(frame) < 2:
            raise LotteryError("markov predictor needs at least 2 draws of history")
        self.transition: dict = {side: {} for side in ("red", "blue") if side in self.pool}
        for side in self.transition:
            lo, hi = self.pool[side]
            hits = _occurrence_matrix(frame, f"lottery_{side}", lo, hi)
            prev, cur = hits[:-1], hits[1:]
            # Laplace 平滑：[上期未出现/出现][本期未出现/出现]，跨号码向量化计数
            both = (prev & cur).sum(axis=0)
            prev_only = (prev & ~cur).sum(axis=0)
            cur_only = (~prev & cur).sum(axis=0)
            neither = (~prev & ~cur).sum(axis=0)
            for i, n in enumerate(range(lo, hi + 1)):
                self.transition[side][n] = [
                    [int(neither[i]) + 1, int(cur_only[i]) + 1],
                    [int(prev_only[i]) + 1, int(both[i]) + 1],
                ]

    def predict(self, amount: int = 1) -> pandas.DataFrame:
        """一阶转移采样选号：按上期出现 / 未出现的转移概率采样，独立时退化为频率。"""
        frame = self._require_history()
        last = {side: set(_split(frame.iloc[-1][f"lottery_{side}"])) for side in ("red", "blue") if side in self.pool}
        if_pad = self.lottery_name in PAD_GAMES
        tickets: list = []
        for _ in range(amount):
            parts = []
            for side in ("red", "blue") if "blue" in self.pool else ("red",):
                weights = {}
                for n, counts in self.transition[side].items():
                    prev = 1 if n in last[side] else 0
                    weights[n] = counts[prev][1] / (counts[prev][0] + counts[prev][1])
                k = RED_COUNTS[self.lottery_name] if side == "red" else BLUE_COUNTS.get(self.lottery_name, 0)
                parts.append(_format_numbers(_weighted_sample_no_replacement(weights, k), if_pad))
            tickets.append((parts[0], parts[1] if len(parts) > 1 else ""))
        return self._to_frame(tickets)


class Markov2Predictor(BasePredictor):
    """二阶马尔可夫策略：状态为上两期的出现/未出现组合（4 态）。

    教学要点：样本在高阶状态下迅速稀疏，Laplace 平滑后大量状态退化为
    均匀分布——直观展示"历史模式越复杂，越接近随机"。
    """

    method = "markov2"

    def __init__(self, lottery_name: str = "ssq", history: Optional[pandas.DataFrame] = None):
        super().__init__(lottery_name, history)
        frame = self._require_history()
        if len(frame) < 2:
            raise LotteryError("markov2 predictor needs at least 2 draws of history")
        self.transition: dict = {side: {} for side in ("red", "blue") if side in self.pool}
        for side in self.transition:
            lo, hi = self.pool[side]
            hits = _occurrence_matrix(frame, f"lottery_{side}", lo, hi)
            for n in range(lo, hi + 1):
                self.transition[side][n] = [[1, 1] for _ in range(4)]  # [上两期状态(0-3)][本期未出现/出现]
            if len(hits) >= 3:
                # 状态编码：上上期出现 ×2 + 上期出现 → 0..3 共 4 态，跨号码向量化计数
                state = hits[:-2].astype(numpy.int8) * 2 + hits[1:-1]
                for s in range(4):
                    mask = state == s
                    appear = (hits[2:] & mask).sum(axis=0)
                    missing = (~hits[2:] & mask).sum(axis=0)
                    for i, n in enumerate(range(lo, hi + 1)):
                        self.transition[side][n][s][0] += int(missing[i])
                        self.transition[side][n][s][1] += int(appear[i])

    def predict(self, amount: int = 1) -> pandas.DataFrame:
        """二阶转移采样选号：以上两期组合为状态（4 态），展示高阶状态稀疏后退化均匀。"""
        frame = self._require_history()
        if len(frame) < 2:
            raise LotteryError("markov2 predictor needs at least 2 draws of history")
        prev2 = {side: set(_split(frame.iloc[-2][f"lottery_{side}"])) for side in self.transition}
        prev1 = {side: set(_split(frame.iloc[-1][f"lottery_{side}"])) for side in self.transition}
        if_pad = self.lottery_name in PAD_GAMES
        tickets: list = []
        for _ in range(amount):
            parts = []
            for side in ("red", "blue") if "blue" in self.pool else ("red",):
                weights = {}
                for n, counts in self.transition[side].items():
                    state = (1 if n in prev2[side] else 0) * 2 + (1 if n in prev1[side] else 0)
                    total = sum(counts[state])
                    weights[n] = counts[state][1] / total if total else 0.5
                k = RED_COUNTS[self.lottery_name] if side == "red" else BLUE_COUNTS.get(self.lottery_name, 0)
                parts.append(_format_numbers(_weighted_sample_no_replacement(weights, k), if_pad))
            tickets.append((parts[0], parts[1] if len(parts) > 1 else ""))
        return self._to_frame(tickets)


class EnsemblePredictor(BasePredictor):
    """集成投票策略：多个子策略各出 top-k，按号码得票数取前 k。

    集成不改变期望——各子策略无预测力，投票亦然；提供它是为了
    把"多策略共振"这一社区习惯变成可复现的实验。

    :param members: tuple, 子策略 method 名（不能含 'ensemble'，避免递归）。
    :param votes_min: int, 入选号码的最少得票数；不足 k 个时按票数补齐。
    """

    method = "ensemble"

    def __init__(
        self,
        lottery_name: str = "ssq",
        history: Optional[pandas.DataFrame] = None,
        members: tuple = ("frequency", "omission", "repeat"),
        votes_min: int = 1,
    ):
        super().__init__(lottery_name, history)
        if "ensemble" in members:
            raise LotteryError("ensemble members must not include ensemble itself")
        if votes_min < 1:
            raise LotteryError(f"votes_min ({votes_min}) must be >= 1")
        frame = self._require_history()
        self.votes_min = votes_min
        self.member_instances = []
        for name in members:
            member_cls = BasePredictor._registry.get(name)
            if member_cls is None or member_cls.method == "ensemble":
                raise LotteryError(f"unknown ensemble member {name!r}")
            self.member_instances.append(member_cls(lottery_name=self.lottery_name, history=frame))

    def predict(self, amount: int = 1) -> pandas.DataFrame:
        """多策略投票选号：成员各出 top-k，按号码得票排序取前 amount 注。"""
        if_pad = self.lottery_name in PAD_GAMES
        k = RED_COUNTS[self.lottery_name]
        tickets: list = []
        for _ in range(amount):
            votes: dict = {}
            blues: list = []
            for member in self.member_instances:
                row = member.predict(1).iloc[0]
                for n in _split(row["lottery_red"]):
                    votes[n] = votes.get(n, 0) + 1
                if row["lottery_blue"]:
                    blues.extend(_split(row["lottery_blue"]))
            ranked = sorted(votes, key=lambda n: (-votes[n], random.random()))
            chosen = [n for n in ranked if votes[n] >= self.votes_min][:k]
            if len(chosen) < k:
                chosen += [n for n in ranked if n not in chosen][: k - len(chosen)]
            blue_str = ""
            if blues:
                counts: dict = {}
                for b in blues:
                    counts[b] = counts.get(b, 0) + 1
                top = max(counts.items(), key=lambda kv: kv[1])[0]
                blue_str = _format_numbers([top], if_pad)
            tickets.append((_format_numbers(sorted(chosen[:k]), if_pad), blue_str))
        return self._to_frame(tickets)


class FilterPredictor(BasePredictor):
    """形态缩水策略：批量随机候选，按多组形态约束过滤。

    注意：过滤只改变选号的分布形态，不改变任何一注的中奖概率。

    :param sum_range: tuple, 红球和值区间 (lo, hi)，None 不过滤。
    :param odd_range: tuple, 红球奇数个数区间 (lo, hi)，None 不过滤。
    :param prime_range: tuple, 红球质数个数区间 (lo, hi)，None 不过滤。
    :param zone_ratio: tuple, 三区比（红球按号码池三等分的分布），精确匹配，如 (2, 2, 2)。
    :param mod3_range: tuple, 012 路分布（号码 % 3 的计数），精确匹配，如 (1, 3, 2)。
    :param ac_range: tuple, AC 值区间 (lo, hi)，None 不过滤。
    :param consecutive_range: tuple, 连号对数区间 (lo, hi)，None 不过滤。
    :param exclude_numbers: iterable, 杀号集合（命中的候选直接淘汰）。
    :param max_trials: int, 最大尝试次数，防止过滤条件过严导致死循环。
    """

    method = "filter"
    needs_history = False

    def __init__(
        self,
        lottery_name: str = "ssq",
        history: Optional[pandas.DataFrame] = None,
        sum_range=None,
        odd_range=None,
        prime_range=None,
        zone_ratio=None,
        mod3_range=None,
        ac_range=None,
        consecutive_range=None,
        exclude_numbers=None,
        max_trials: int = 10000,
    ):
        super().__init__(lottery_name, history)  # 无历史依赖，参数仅为接口统一
        self.sum_range = sum_range
        self.odd_range = odd_range
        self.prime_range = prime_range
        self.zone_ratio = tuple(zone_ratio) if zone_ratio else None
        self.mod3_range = tuple(mod3_range) if mod3_range else None
        self.ac_range = ac_range
        self.consecutive_range = consecutive_range
        self.exclude_numbers = frozenset(exclude_numbers) if exclude_numbers else frozenset()
        self.max_trials = max_trials

    def _passes(self, reds: list) -> bool:
        if self.exclude_numbers and any(n in self.exclude_numbers for n in reds):
            return False
        if self.sum_range and not self.sum_range[0] <= sum(reds) <= self.sum_range[1]:
            return False
        odd_count = sum(1 for n in reds if n % 2)
        if self.odd_range and not self.odd_range[0] <= odd_count <= self.odd_range[1]:
            return False
        prime_count = sum(1 for n in reds if n in PRIMES)
        if self.prime_range and not self.prime_range[0] <= prime_count <= self.prime_range[1]:
            return False
        if self.zone_ratio and _zone_counts(reds, self.pool) != self.zone_ratio:
            return False
        if self.mod3_range and _mod3_counts(reds) != self.mod3_range:
            return False
        if self.ac_range and not self.ac_range[0] <= _ac_value(reds) <= self.ac_range[1]:
            return False
        if (
            self.consecutive_range
            and not self.consecutive_range[0] <= _consecutive_pairs(reds) <= self.consecutive_range[1]
        ):
            return False
        return True

    def predict(self, amount: int = 1) -> pandas.DataFrame:
        """可组合形态缩水选号：和值 / 奇偶 / 质合 / 三区比 / 012 路 / AC 值 / 连号 / 杀号约束下随机采样。"""
        tickets: list = []
        trials = 0
        while len(tickets) < amount and trials < self.max_trials:
            trials += 1
            parts = load_random_data(lottery_name=self.lottery_name, amount=1, is_detail_result=True)[0]
            reds = [int(x) for x in parts[0].split(",")]
            if self._passes(reds):
                tickets.append((parts[0], parts[1] if len(parts) > 1 else ""))
        if len(tickets) < amount:
            raise LotteryError("filter conditions too strict, no ticket matched")
        return self._to_frame(tickets)


def _resolve_predictor(method: str) -> tuple[type["BasePredictor"], dict]:
    """解析策略名（含别名）为预测器类与别名默认参数；未知策略抛 LotteryError。"""
    predictor_cls = BasePredictor._registry.get(method)
    if predictor_cls is None and method in BasePredictor._alias_map:
        cls, overrides = BasePredictor._alias_map[method]
        return cls, dict(overrides)
    if predictor_cls is None:
        raise LotteryError(f"unknown predict method {method!r}")
    return predictor_cls, {}


def load_predict_numbers(
    lottery_name: str = "ssq",
    method: str = "random",
    amount: int = 1,
    history: Optional[pandas.DataFrame] = None,
    **kwargs,
) -> pandas.DataFrame:
    """Generate numbers with a strategy. Output mirrors load_random_data
    (plus a `method` column).

    ⚠️ Entertainment only — every strategy has exactly the same expected value
    as the `random` baseline (verify with `lotterycn.backtest`).

    !!! note "中文说明"

        按指定策略生成选号。可用策略：random 基线 / frequency 冷热（别名
        hot/cold）/ omission 遗漏回补（chase）/ deviation 卡方偏离（chisq）/
        repeat 重邻斜 / trend 和值均线 / tail 尾数 / markov / markov2 /
        filter 形态缩水（和值/奇偶/质合/三区/012路/AC值/连号/杀号）/
        ensemble 多策略投票。`history=` 注入 DataFrame 可完全离线；
        否则按需拉取（支持 if_cached）。

    :param lottery_name: str, must in ('ssq', 'qlc', 'kl8', '3d', 'dlt', 'pls', 'plw', 'qxc').
    :param method: str, 'random' | 'frequency'（别名 'hot'/'cold'）| 'omission'（'chase'）
        | 'deviation'（'chisq'）| 'repeat' | 'trend' | 'tail' | 'markov' | 'markov2'
        | 'filter' | 'ensemble'.
    :param amount: int, 生成注数，default 1.
    :param history: pandas.DataFrame, 显式注入历史数据（离线使用）；为 None 且策略
        需要历史时按 **kwargs 中的数据获取参数联网拉取。
    :keyword **kwargs: 两类参数——
            策略参数：recent_n / mode / explore_ratio（frequency/omission/deviation/tail），
                      repeat_weight / neighbor_weight / jump_weight（repeat），
                      window / k_sigma（trend），members / votes_min（ensemble），
                      sum_range / odd_range / prime_range / zone_ratio / mod3_range /
                      ac_range / consecutive_range / exclude_numbers / max_trials（filter）；
            数据获取参数（仅拉取时生效）：if_cached / timeout / proxies / max_retries 等。
    :return: pandas.DataFrame
    """
    fetch_kwargs = {k: kwargs.pop(k) for k in _FETCH_KEYS if k in kwargs}
    predictor_cls, overrides = _resolve_predictor(method)
    kwargs = {**overrides, **kwargs}  # 显式传入的策略参数优先于别名默认值
    if history is None and predictor_cls.needs_history:
        history = load_history_data(lottery_name=lottery_name, **fetch_kwargs)
    return predictor_cls(lottery_name=lottery_name, history=history, **kwargs).predict(amount=amount)
