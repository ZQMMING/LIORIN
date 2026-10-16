"""Bazi 十二长生 / 禄位 / 帝旺 — fixed doctrinal tables (P1-01).

Standard 子平 fixed data (not invented semantics), consumed by the
RuleContext fields added in P1-01:
    day_master_stage_month   — 十二长生位 of 日主 in 月支
    day_master_road_month    — 月支 is 日主禄位 (建禄)
    day_master_absolute_month— 月支 is 日主帝旺位 (阳刃/帝旺)

Conventions (all 传统通行):
  - 十二长生顺序: 长生 沐浴 冠带 临官 帝旺 衰 病 死 墓 绝 胎 养
  - 阳干顺布, 阴干逆布 (甲长生在亥, 乙长生在午 …)
  - 十干禄位: 甲禄在寅, 乙禄在卯, 丙戊禄在巳, 丁己禄在午,
              庚禄在申, 辛禄在酉, 壬禄在亥, 癸禄在子
  - 帝旺位 = 阳刃位 (甲卯 / 丙午 / 戊午 / 庚酉 / 壬子 …)

P0-15 discipline: these are fixed definitional tables (same class as
BRANCH_HIDDEN_STEMS in bazi_ten_gods), not classical prose quotations;
the associated rules cite 三命通会《论天干生旺死绝》/ 渊海子平《论天干》
as chapter provenance with 待校 paraphrase, never fabricated verbatim text.
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# 十二长生表 — stem -> branch -> stage (阳顺阴逆, standard doctrine).
# --------------------------------------------------------------------------- #
LONGHU_STAGE: dict[str, dict[str, str]] = {
    # 阳干顺布
    "JIA": {
        "HAI": "长生", "ZI": "沐浴", "CHOU": "冠带", "YIN": "临官",
        "MAO": "帝旺", "CHEN": "衰", "SI": "病", "WU": "死",
        "WEI": "墓", "SHEN": "绝", "YOU": "胎", "XU": "养",
    },
    "BING": {
        "YIN": "长生", "MAO": "沐浴", "CHEN": "冠带", "SI": "临官",
        "WU": "帝旺", "WEI": "衰", "SHEN": "病", "YOU": "死",
        "XU": "墓", "HAI": "绝", "ZI": "胎", "CHOU": "养",
    },
    # 戊随丙
    "WU": {
        "YIN": "长生", "MAO": "沐浴", "CHEN": "冠带", "SI": "临官",
        "WU": "帝旺", "WEI": "衰", "SHEN": "病", "YOU": "死",
        "XU": "墓", "HAI": "绝", "ZI": "胎", "CHOU": "养",
    },
    "GENG": {
        "SI": "长生", "WU": "沐浴", "WEI": "冠带", "SHEN": "临官",
        "YOU": "帝旺", "XU": "衰", "HAI": "病", "ZI": "死",
        "CHOU": "墓", "YIN": "绝", "MAO": "胎", "CHEN": "养",
    },
    "REN": {
        "SHEN": "长生", "YOU": "沐浴", "XU": "冠带", "HAI": "临官",
        "ZI": "帝旺", "CHOU": "衰", "YIN": "病", "MAO": "死",
        "CHEN": "墓", "SI": "绝", "WU": "胎", "WEI": "养",
    },
    # 阴干逆布
    "YI": {
        "WU": "长生", "SI": "沐浴", "CHEN": "冠带", "MAO": "临官",
        "YIN": "帝旺", "CHOU": "衰", "ZI": "病", "HAI": "死",
        "XU": "墓", "YOU": "绝", "SHEN": "胎", "WEI": "养",
    },
    "DING": {
        "YOU": "长生", "SHEN": "沐浴", "WEI": "冠带", "WU": "临官",
        "SI": "帝旺", "CHEN": "衰", "MAO": "病", "YIN": "死",
        "CHOU": "墓", "ZI": "绝", "HAI": "胎", "XU": "养",
    },
    # 己随丁
    "JI": {
        "YOU": "长生", "SHEN": "沐浴", "WEI": "冠带", "WU": "临官",
        "SI": "帝旺", "CHEN": "衰", "MAO": "病", "YIN": "死",
        "CHOU": "墓", "ZI": "绝", "HAI": "胎", "XU": "养",
    },
    "XIN": {
        "ZI": "长生", "HAI": "沐浴", "XU": "冠带", "YOU": "临官",
        "SHEN": "帝旺", "WEI": "衰", "WU": "病", "SI": "死",
        "CHEN": "墓", "MAO": "绝", "YIN": "胎", "CHOU": "养",
    },
    "GUI": {
        "MAO": "长生", "YIN": "沐浴", "CHOU": "冠带", "ZI": "临官",
        "HAI": "帝旺", "XU": "衰", "YOU": "病", "SHEN": "死",
        "WEI": "墓", "WU": "绝", "SI": "胎", "CHEN": "养",
    },
}

# 十干禄位(支)
ROAD_BRANCH: dict[str, str] = {
    "JIA": "YIN", "YI": "MAO",
    "BING": "SI", "DING": "WU",
    "WU": "SI", "JI": "WU",
    "GENG": "SHEN", "XIN": "YOU",
    "REN": "HAI", "GUI": "ZI",
}

# 十干帝旺位(支) = 阳刃位
ABSOLUTE_BRANCH: dict[str, str] = {
    "JIA": "MAO", "YI": "YIN",
    "BING": "WU", "DING": "SI",
    "WU": "WU", "JI": "SI",
    "GENG": "YOU", "XIN": "SHEN",
    "REN": "ZI", "GUI": "HAI",
}

LONGHU_STAGES = (
    "长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养",
)


def longhu_stage(stem: str, branch: str) -> str:
    """十二长生位 of stem in branch (阳顺阴逆)."""
    return LONGHU_STAGE[stem][branch]


def road_branch(stem: str) -> str:
    """十干禄位之支 (建禄)."""
    return ROAD_BRANCH[stem]


def absolute_branch(stem: str) -> str:
    """十干帝旺位之支 (阳刃)."""
    return ABSOLUTE_BRANCH[stem]


# --------------------------------------------------------------------------- #
# 天乙贵人 — 日干查命局地支 (神煞, 三命通会《论天乙贵人》通行口诀).
# 口诀: 甲戊庚牛羊, 乙己鼠猴乡, 丙丁猪鸡位, 壬癸兔蛇藏, 六辛逢马虎.
# 采用通行「日干查四支」定式; 阴贵/阳贵(昼贵/夜贵)细化不在 P1-01 范围.
# --------------------------------------------------------------------------- #
TIANYI_GUIREN: dict[str, tuple[str, ...]] = {
    "JIA": ("CHOU", "WEI"), "WU": ("CHOU", "WEI"), "GENG": ("CHOU", "WEI"),
    "YI": ("ZI", "SHEN"), "JI": ("ZI", "SHEN"),
    "BING": ("HAI", "YOU"), "DING": ("HAI", "YOU"),
    "REN": ("MAO", "SI"), "GUI": ("MAO", "SI"),
    "XIN": ("WU", "YIN"),
}


def tianyi_guiren(stem: str) -> tuple[str, ...]:
    """日干之天乙贵人生支 (可能两支)."""
    return TIANYI_GUIREN[stem]
