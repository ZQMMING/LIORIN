# -*- coding: utf-8 -*-
"""工程推定区 (Engineering Assumptions Registry)
==============================================================
集中登记引擎中所有"非原典显式给出、为机器可执行而做的离散化参数/裁决结构"。

铁律:
1. 原典显式语义(CLASSICAL) 与 工程离散取值(ENGINEERING_*) 严格分开, 不得混同.
2. ENGINEERING_UNVERIFIED 的具体取值仅为工程初值, 【待 YHZP/SMTH 真实命例回归校准】;
   回归前不锁死、不刻碑, 临界点可能被真实命例打翻.
3. 任何新增离散阈值必须在 ASSUMPTIONS 登记, 不得在各层散落硬编码.
4. 工程只做"离散布尔化 / 序数化", 全程禁浮点加权; 不得添加原典没有的语义或吉凶.

状态标签:
- CLASSICAL             : 原典显式表述或稳定通例, 可直接用
- ENGINEERING_UNVERIFIED: 工程离散取值, 待真实命例回归
- ENGINEERING_STRUCTURE : 工程裁决结构(非取值), 各分量依原典
==============================================================
"""
from typing import Any, Dict, List

# --------------------------------------------------------------
# 状态标签
# --------------------------------------------------------------
CLASSICAL = "CLASSICAL"
ENGINEERING_UNVERIFIED = "ENGINEERING_UNVERIFIED"
ENGINEERING_STRUCTURE = "ENGINEERING_STRUCTURE"

# ==============================================================
# 1. 成党 / 成势离散阈值
#    计数口径(CLASSICAL 原则): 他干透干(排除日干) + 本气根(不含中气余气)
#    combo = 透干数 + 本气根数
# ==============================================================
DANG_COMBO = 4          # combo >= 4  -> 成党 (dang_level=0)
SHI_COMBO_MIN = 1       # combo >= 1  -> 成势 (dang_level=1); combo=0 -> 不成(2)

DANG_LEVEL_DANG = 0     # 成党
DANG_LEVEL_SHI = 1      # 成势
DANG_LEVEL_NONE = 2     # 不成

# ==============================================================
# 2. 月令旺相休囚死序数 (CLASSICAL 通例)
#    当令者旺, 令所生者相, 生令者休, 克令者囚, 令所克者死.
#    序数越小越旺, 以序数入辩层比较键(非数值权重).
# ==============================================================
MONTH_ORDER_NUM = {"旺": 1, "相": 2, "休": 3, "囚": 4, "死": 5}
MONTH_STATE_FALLBACK = 9   # 月令信息缺失时的占位(不参与正常比较)

# ==============================================================
# 3. 五行(日主)四档旺衰 tier 边界 —— ENGINEERING_UNVERIFIED
#    强(3) / 旺(2) / 平(1) / 衰(0), 布尔谓词逐级判定.
# ==============================================================
TIER_STRONG = 3
TIER_WANG = 2
TIER_PING = 1
TIER_SHUAI = 0

# ★ V7.99 阈值性质与裁决纪律: 本气根"个数"阈值原典未给数字(PZZQ L800-801 只言【轻重根之别】,
#   SMTH 旺相休囚死序为通例), 故此二值为【工程推定|ENGINEERING_UNVERIFIED】, 仅作现行默认.
#   纪律: 不得以【命例】反推或手调本阈值以求全绿 —— 命例是验证物, 非规格来源(AGENTS.md v3 公理三);
#   调整须先有 grade=A 原句依据, 并留档变更理由. 待【原典专项裁决】.
TIER_STRONG_BEN_MULTI = 3   # 强: 本气根 >= 3  (ENGINEERING_UNVERIFIED, 待原典专项裁决)
TIER_WANG_BEN = 2           # 旺: 本气根 >= 2  (ENGINEERING_UNVERIFIED, 待原典专项裁决)
# 其余为组合布尔条件(成局 / 当令配合 / 中余气根 / 半合 / 相令透干),
# 见 transit_power.element_power_tier.
# ★ V7.99 纪律: 本表所有 ENGINEERING_UNVERIFIED 阈值一律不得以命例反推/手调全绿;
#   须先得 grade=A 原句依据方可调整(AGENTS.md v3 公理三 + 验收四条).

# ==============================================================
# 4. 转归层判据
#    过当(布尔): 成党(dang_level==0) 或 当令(month_order==旺=1)
#    日主弱(布尔): 无重根(has_heavy == False)
#    化/帮: 过当 AND 日主无重根 -> 次病; 否则 -> 药
#    制(克病): 不看量, 无条件转药(克病恒正向)
# ==============================================================
GUODANG_BY_DANG_LEVEL = 0    # 成党
GUODANG_BY_MONTH_ORDER = 1   # 月令序数=1(当令旺)

# ==============================================================
# 5. 天干合化条件 (CLASSICAL, 实现见 daymaster_tian_he)
#    合化: 化神得月令之气, 或 逢辰(龙); 满足 -> 合而化
#    否则 -> 合而不化(合绊 / 合去), 被合之神暂失本职
# ==============================================================
HE_HUA_BY_MONTH_QI = True    # 化神得月令
HE_HUA_BY_LONG_CHEN = True   # 逢辰(龙)即化

# ==============================================================
# 6. 地支关系优先级 —— ENGINEERING_STRUCTURE (类型序依原典, 工程整理)
#    多关系并存时取类型优先级最高者; 并列则冲突保留.
# ==============================================================
RELATION_PRIORITY = {
    "sanhui": 7,    # 三会
    "sanhe": 6,     # 三合
    "banhe": 5,     # 半合
    "liuhe": 4,     # 六合
    "liuchong": 3,  # 冲
    "sanxing": 2,   # 刑
    "liuhai": 1,    # 害
    "liupo": 0,     # 破
}

# ==============================================================
# 注册表: 每个工程参数/结构的性质、依据、说明
# ==============================================================
ASSUMPTIONS: List[Dict[str, Any]] = [
    # --- 取值类(待回归) ---
    {"key": "DANG_COMBO", "value": DANG_COMBO, "status": ENGINEERING_UNVERIFIED,
     "source": "工程离散值(无原典精确数字)",
     "note": "他干透干+本气根 combo>=4 判成党; 临界点待真实命例回归, 或为3/5",
     "classical_verification_2026_10_21": (
         "已查证(维基文库《滴天髓》辑要底本 + PZZQ-005-005 grade=A): "
         "PZZQ 只言「干多不如根重」「长生禄刃根之重者, 墓库余气根之轻者」(轻重根之别), "
         "全文检索「成党/党众」无计数门槛明文 -> 本值无 grade=A 数字依据, 维持现值不变.")},
    {"key": "LIANGQI_COUNT_MIN", "value": 3, "status": ENGINEERING_UNVERIFIED,
     "source": "工程离散值(无原典精确数字)",
     "note": "两气成象「各成势」计数>=3(含天干+地支本气); 见 special_pattern.py L770-774 登记",
     "classical_verification_2026_10_21": (
         "已查证(《滴天髓·形象论》底本: 「两气合而成象, 像不可破也」「天干属木, 地支属火...若见金即破, 余仿此」): "
         "底本只给「两行相生成象 + 见第三行即破」结构条件, 无任何数字门槛 -> 维持现值不变. "
         "★ 不可挪《阐微》「五气聚而成形, 形不可害也」(属五气聚形章)作两气成象门槛 —— "
         "2026-10-21 两次据此误改, 均致三锚点盘判 None, 已撤回.")},
    {"key": "SHI_COMBO_MIN", "value": SHI_COMBO_MIN, "status": ENGINEERING_UNVERIFIED,
     "source": "工程离散值",
     "note": "combo>=1 判成势; 与成党阈值配套回归"},
    {"key": "TIER_STRONG_BEN_MULTI", "value": TIER_STRONG_BEN_MULTI,
     "status": ENGINEERING_UNVERIFIED,
     "source": "工程离散值",
     "note": "本气根>=3 判强; 四档边界整体待命例回归",
     "classical_verification_2026_10_21": (
         "已查证(PZZQ-005-005 grade=A + 底本校对): PZZQ 只言「长生禄刃, 根之重者也; 墓库余气, 根之轻者也」"
         "(轻重根之别), 无「几根为强/旺」数字明文 -> 维持现值不变, 待原典专项裁决.")},
    {"key": "TIER_WANG_BEN", "value": TIER_WANG_BEN, "status": ENGINEERING_UNVERIFIED,
     "source": "工程离散值",
     "note": "本气根>=2 判旺; 与强/平边界配套回归",
     "classical_verification_2026_10_21": (
         "已查证: 同 TIER_STRONG_BEN_MULTI, 无 grade=A 数字明文 -> 维持现值不变.")},
    {"key": "YOU_QI", "value": 1, "status": ENGINEERING_UNVERIFIED,
     "source": "工程离散值(dts_yuanliu 有气阈值)",
     "note": "源流追踪「有气即住」最简工程化: combo>=1 视为有气; 见 dts_yuanliu.py YOU_QI",
     "classical_verification_2026_10_21": (
         "已查证(DTS-019-002 L108 源流/通关语境 + 底本《滴天骼·源流论》「以取最多旺, 可为全局祖者宗为源头」): "
         "原典只言「最多最旺」为源、「有情/住」为流, 无「计数>=1」门槛 -> 维持现值不变.")},
    # --- 原典通例类 ---
    {"key": "MONTH_ORDER_NUM", "value": MONTH_ORDER_NUM, "status": CLASSICAL,
     "source": "渊海子平/滴天髓 月令旺相休囚死通例",
     "note": "定性映射为原典通例; 以序数入键, 非浮点权重"},
    {"key": "HE_HUA 条件", "value": "化神得月令 / 逢辰", "status": CLASSICAL,
     "source": "渊海子平 天干合化(得时化, 逢龙化)",
     "note": "不满足则合而不化; 实现见 daymaster_tian_he"},
    {"key": "制不看量", "value": "克病恒正向", "status": CLASSICAL,
     "source": "原典病药通例(食神制杀/官制比劫/财破印)",
     "note": "凡克主病者无条件转药; 化/帮才看过当"},
    # --- 结构类 ---
    {"key": "辩层比较键", "value": "(月令序数, 成党级别, -透干, -本根)",
     "status": ENGINEERING_STRUCTURE,
     "source": "月令为提纲当令者旺(原典), 故居首; 分量依原典(成党/透藏/根气)",
     "note": "全整数字典序, 无浮点; 结构本身为工程裁决, 透干排除日干"},
    {"key": "转归过当判据", "value": "成党 或 当令; 且日主无重根",
     "status": ENGINEERING_STRUCTURE,
     "source": "DTS 水泛木浮(FAN_JU.001)/YHZP 生多反害",
     "note": "复用算层布尔事实, 不引入连续评分; 与关系为 AND"},
    {"key": "RELATION_PRIORITY", "value": "会>合>冲>刑>害>破",
     "status": ENGINEERING_STRUCTURE,
     "source": "原典冲合优先通例 + 工程整理",
     "note": "完整8级序为工程整理; 同类并列则冲突保留"},
    {"key": "成局力量入偏序键", "value": "暂未入键(裁决层引动收紧兜底)",
     "status": ENGINEERING_UNVERIFIED,
     "source": "复合局岁运成局已检测(transit_power 追加三合三会), 但入键序位未定",
     "note": "争议: 失月令之局(如戌月亥卯未)与提纲谁优先, 命理有条件分歧; "
             "须带三合三会原断的真实命例定序位, 现不脑补、不写死"},
]


def engineering_unverified_keys() -> List[str]:
    """列出所有待真实命例回归的取值参数(校准清单)."""
    return [a["key"] for a in ASSUMPTIONS if a["status"] == ENGINEERING_UNVERIFIED]


def describe_assumptions() -> str:
    """生成工程推定清单(人读)."""
    lines = ["工程推定区清单", "=" * 60]
    status_cn = {CLASSICAL: "原典通例", ENGINEERING_UNVERIFIED: "待回归取值",
                 ENGINEERING_STRUCTURE: "工程结构"}
    for a in ASSUMPTIONS:
        lines.append("[%s] %s = %s" % (status_cn[a["status"]], a["key"], a["value"]))
        lines.append("    依据: %s" % a["source"])
        lines.append("    说明: %s" % a["note"])
    lines.append("=" * 60)
    lines.append("待真实命例回归校准的取值: %s"
                 % ", ".join(engineering_unverified_keys()))
    return "\n".join(lines)


if __name__ == "__main__":
    print(describe_assumptions())
