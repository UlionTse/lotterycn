# coding=utf-8
# author=Ulion.Tse

import os


class SsqConfig:
    """双色球（中国福利彩票）。

    规则来源（官方）：中国福彩网“玩法介绍”栏目（含各彩种游戏规则入口）
    https://www.cwl.gov.cn/fcpz/yxjs/ssq/
    红球 33 选 6、蓝球 16 选 1，单注 2 元，返奖率 51%。
    一、二等奖为浮动奖（单注封顶 500 万元）；三至六等奖为固定奖。
    """

    def __init__(self):
        self.bet_price = 2
        self.ssq_rule_url = "https://www.cwl.gov.cn/fcpz/yxjs/ssq/"
        # 红球/蓝球：(号码总数, 开奖个数, 投注个数)
        self.ssq_role_red = (33, 6, 6)
        self.ssq_role_blue = (16, 1, 1)
        # 各奖级中奖条件：(命中红球数, 命中蓝球数)
        self.ssq_prize_role = {
            1: [(6, 1)],
            2: [(6, 0)],
            3: [(5, 1)],
            4: [(5, 0), (4, 1)],
            5: [(4, 0), (3, 1)],
            6: [(2, 1), (1, 1), (0, 1)],
        }
        # 浮动奖金额为计算期望所用的默认假设值，可用环境变量覆盖。
        self.ssq_prize_award = {1: 5e6, 2: 15e4, 3: 3000, 4: 200, 5: 10, 6: 5}
        self.ssq_floating_levels = {1: "浮动(单注封顶500万元)", 2: "浮动(单注封顶500万元)"}
        self.ssq_prize_env = {1: "lotterycn_ssq_1st_prize", 2: "lotterycn_ssq_2nd_prize"}


class QlcConfig:
    """七乐彩（中国福利彩票）。

    规则来源（官方）：中国福彩网“玩法介绍”栏目（含各彩种游戏规则入口）
    https://www.cwl.gov.cn/fcpz/yxjs/qlc/
    30 选 7 个基本号码 + 1 个特别号码（从剩余 23 个中开出），单注 2 元，返奖率 50%。
    现行设七个奖等：一至三等奖为浮动奖（占高奖等奖金 70%/10%/20%，单注封顶 500 万元），
    四至七等奖为固定奖。
    """

    def __init__(self):
        self.bet_price = 2
        self.qlc_rule_url = "https://www.cwl.gov.cn/fcpz/yxjs/qlc/"
        # (号码总数, 基本号码个数, 特别号码个数, 投注个数)
        self.qlc_role = (30, 7, 1, 7)
        # 各奖级中奖条件：(命中基本号码数, 是否命中特别号码)
        self.qlc_prize_role = {
            1: [(7, 0)],
            2: [(6, 1)],
            3: [(6, 0)],
            4: [(5, 1)],
            5: [(5, 0)],
            6: [(4, 1)],
            7: [(4, 0)],
        }
        self.qlc_prize_award = {1: 1e6, 2: 5e4, 3: 5e3, 4: 200, 5: 50, 6: 10, 7: 5}
        self.qlc_floating_levels = {
            1: "浮动(高奖等奖金70%,单注封顶500万元)",
            2: "浮动(高奖等奖金10%,单注封顶500万元)",
            3: "浮动(高奖等奖金20%,单注封顶500万元)",
        }
        self.qlc_prize_env = {
            1: "lotterycn_qlc_1st_prize",
            2: "lotterycn_qlc_2nd_prize",
            3: "lotterycn_qlc_3rd_prize",
        }


class Kl8Config:
    """快乐8（中国福利彩票）。

    规则来源（官方）：中国福彩网“玩法介绍”栏目（含各彩种游戏规则入口）
    https://www.cwl.gov.cn/fcpz/yxjs/kl8/
    每期从 80 个号码中开出 20 个，玩家可选 1-10 个号码（选一至选十），单注 2 元。
    奖金表与中国福彩网开奖公告的现行数值一致。
    """

    def __init__(self):
        self.bet_price = 2
        self.kl8_rule_url = "https://www.cwl.gov.cn/fcpz/yxjs/kl8/"
        # (号码总数, 每期开出个数)
        self.kl8_role = (80, 20)
        # 各玩法各档位单注奖金（元）：{选N: {命中个数: 奖金}}
        self.kl8_prize_table = {
            1: {1: 4.5},
            2: {2: 19},
            3: {3: 52, 2: 3},
            4: {4: 93, 3: 5, 2: 3},
            5: {5: 1000, 4: 20, 3: 3},
            6: {6: 2880, 5: 30, 4: 10, 3: 3},
            7: {7: 8500, 6: 300, 5: 30, 4: 4, 0: 2},
            8: {8: 50000, 7: 800, 6: 80, 5: 10, 4: 3, 0: 2},
            9: {9: 25e4, 8: 2000, 7: 225, 6: 22, 5: 5, 4: 3, 0: 2},
            10: {10: 5e6, 9: 8000, 8: 720, 7: 80, 6: 5, 5: 3, 0: 2},
        }
        # 浮动奖档位：(选N, 命中个数) -> 说明；金额为默认假设值，可用环境变量覆盖。
        self.kl8_floating_levels = {
            (9, 9): "浮动(单注封顶25万元)",
            (10, 10): "浮动(单注封顶500万元)",
        }
        self.kl8_prize_env = {
            (9, 9): "lotterycn_kl8_pick9_1st_prize",
            (10, 10): "lotterycn_kl8_pick10_1st_prize",
        }


class Fc3dConfig:
    """福彩3D（中国福利彩票）。

    规则来源（官方）：中国福彩网“玩法介绍”栏目（含各彩种游戏规则入口）
    https://www.cwl.gov.cn/fcpz/yxjs/fc3d/
    000-999 三位数，单注 2 元，返奖率 53%，均为固定奖。
    除单选/组选外还有 1D、2D、通选、和数、包选等玩法，此处收录核心单式玩法。
    """

    def __init__(self):
        self.bet_price = 2
        self.fc3d_rule_url = "https://www.cwl.gov.cn/fcpz/yxjs/fc3d/"
        self.fc3d_digits = 3
        # 各投注方式：(中奖组合数, 单注奖金)。单选 1/1000、组选3 3/1000、组选6 6/1000。
        self.fc3d_prize_play = {
            "单选": (1, 1040),
            "组选3": (3, 346),
            "组选6": (6, 173),
        }


class DltConfig:
    """超级大乐透（中国体育彩票）。

    规则来源（官方）：中国体彩网《超级大乐透游戏规则》（现行七个奖级版）
    https://www.lottery.gov.cn/bzzx/yxgz/20191119/1002858.html
    规则调整动态：https://www.lottery.gov.cn/dlt/ltdt/index.html
    前区 35 选 5、后区 12 选 2，单注基本投注 2 元，返奖率 51%。
    一、二等奖为浮动奖（单注封顶 500 万元）；三至七等奖为固定奖，
    固定奖金额与奖池挂钩：奖池低于 8 亿元与不低于 8 亿元两档。
    """

    def __init__(self):
        self.bet_price = 2
        self.dlt_rule_url = "https://www.lottery.gov.cn/bzzx/yxgz/20191119/1002858.html"
        self.dlt_role_red = (35, 5, 5)
        self.dlt_role_blue = (12, 2, 2)
        # 各奖级中奖条件：(命中前区号码数, 命中后区号码数)
        self.dlt_prize_role = {
            1: [(5, 2)],
            2: [(5, 1)],
            3: [(5, 0), (4, 2)],
            4: [(4, 1)],
            5: [(4, 0), (3, 2)],
            6: [(3, 1), (2, 2)],
            7: [(3, 0), (2, 1), (1, 2), (0, 2)],
        }
        # 奖池低于 8 亿元时的固定奖金额。
        self.dlt_prize_award = {1: 5e6, 2: 1e5, 3: 5000, 4: 300, 5: 150, 6: 15, 7: 5}
        # 奖池不低于 8 亿元时的固定奖金额（仅覆盖三至七等奖）。
        self.dlt_prize_award_pool_over_800m = {3: 6666, 4: 380, 5: 200, 6: 18, 7: 7}
        self.dlt_floating_levels = {1: "浮动(单注封顶500万元)", 2: "浮动(单注封顶500万元)"}
        self.dlt_prize_env = {1: "lotterycn_dlt_1st_prize", 2: "lotterycn_dlt_2nd_prize"}


class PlsConfig:
    """排列3（中国体育彩票）。

    规则来源（官方）：体彩官网《排列3游戏规则》
    https://www.lottery.gov.cn/bzzx/yxgz/20191119/1002855.html
    000-999 三位数，单注 2 元，返奖率 53%，均为固定奖。
    """

    def __init__(self):
        self.bet_price = 2
        self.pls_rule_url = "https://www.lottery.gov.cn/bzzx/yxgz/20191119/1002855.html"
        self.pls_digits = 3
        self.pls_prize_play = {
            "直选": (1, 1040),
            "组选3": (3, 346),
            "组选6": (6, 173),
        }


class PlwConfig:
    """排列5（中国体育彩票）。

    规则来源（官方）：体彩官网《排列5游戏规则》
    https://www.lottery.gov.cn/bzzx/yxgz/20191119/10011178.html
    00000-99999 五位数，单注 2 元，返奖率 50%，仅设一个固定奖奖级。
    """

    def __init__(self):
        self.bet_price = 2
        self.plw_rule_url = "https://www.lottery.gov.cn/bzzx/yxgz/20191119/10011178.html"
        self.plw_digits = 5
        self.plw_prize_play = {
            "直选": (1, 100000),
        }


class QxcConfig:
    """7星彩（中国体育彩票）。

    规则来源（官方）：中国体彩网《中国体育彩票7星彩游戏规则》
    https://www.lottery.gov.cn/bzzx/yxgz/20191119/1002857.html
    前六位从 000000-999999（每位 0-9）中选取，最后一位从 0-14 中选取，
    共 10^6 * 15 = 1500 万种组合，单注 2 元，返奖率 50%。
    一、二等奖为浮动奖（单注封顶 500 万元）；三至六等奖为固定奖。
    """

    def __init__(self):
        self.bet_price = 2
        self.qxc_rule_url = "https://www.lottery.gov.cn/bzzx/yxgz/20191119/1002857.html"
        self.qxc_front_positions = 6
        self.qxc_front_radix = 10
        self.qxc_last_radix = 15
        # 各奖级中奖条件：(前六位按位命中个数, 是否命中最后一位)
        self.qxc_prize_role = {
            1: [(6, 1)],
            2: [(6, 0)],
            3: [(5, 1)],
            4: [(5, 0), (4, 1)],
            5: [(4, 0), (3, 1)],
            6: [(3, 0), (2, 1), (1, 1), (0, 1)],
        }
        self.qxc_prize_award = {1: 5e6, 2: 1e4, 3: 3000, 4: 500, 5: 30, 6: 5}
        self.qxc_floating_levels = {1: "浮动(单注封顶500万元)", 2: "浮动(单注封顶500万元)"}
        self.qxc_prize_env = {1: "lotterycn_qxc_1st_prize", 2: "lotterycn_qxc_2nd_prize"}


def get_env_prize(env_name: str, default_value) -> float:
    """读取环境变量中的浮动奖金额覆盖值，未设置时返回默认值。

    :param env_name: str, 环境变量名。
    :param default_value: float, 未设置时的默认奖金。
    :return: float, 单注奖金（元）。
    """
    return float(os.environ.get(env_name, default_value))


# ----- assembly：彩种注册表（依赖上方配置类定义，统一置于文件末尾）-----
CONFIG_MAP = {
    "ssq": SsqConfig,
    "qlc": QlcConfig,
    "kl8": Kl8Config,
    "3d": Fc3dConfig,
    "dlt": DltConfig,
    "pls": PlsConfig,
    "plw": PlwConfig,
    "qxc": QxcConfig,
}
