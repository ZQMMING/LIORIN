# -*- coding: utf-8 -*-
"""盲派八字引擎 — MangPai Bazi Engine (增强版 · 做功引擎)

基于段建业/杨清贫盲派方法论 + bonesyear/MangPai-Destiny 参考实现。
只实现确定性算法，不使用 LLM。

盲派核心概念（2026-08-27 互联网/典籍校对）：
- 宾主：日柱为「主」（我），其余为「宾」（外界）
- 体用：体（本钱）= 比肩/劫财/印/食神/伤官/禄；用（目标）= 财/官杀
- 做功：用「体」去取「用」，靠 合/冲/克/制/化/墓 等关系实现
- 五种做功：制用 / 化用 / 生用 / 合用 / 墓用
"""
from __future__ import annotations

# ═══ 架构铁律（用户多次强调，禁止违反）══════════════════════════════════
# 盲派引擎与子平引擎是【完全独立】的两个引擎：
#   - 唯一共同消费层 = 八字排盘引擎输出的基础事实
#     （四柱/藏干/十神/五行生克/禄刃位置，全部为客观可计算事实）
#   - 盲派引擎【禁止】import / 消费 / 复用子平辨层任何东西：
#     （旺衰 / 强弱 / 格局 / 用神 / 喜忌 / 调候 / 身强身弱 / 评分阈值）
#   - 子平引擎同样独立，两者互不调用。
# 违者 = 架构违规。见规则文档 §70（ZI_PING_CLASSICS ≠ BLIND_PAI_SOURCE）
# 与 §90（ZIPING_DEPENDENCY: FORBIDDEN）。
# ═══════════════════════════════════════════════════════════════════════

import enum
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from ..engines.bazi_engine import BaziEngine, BaziChart, STEM_ELEMENT, _branch_element, canonical_bazi_engine
from ..signal.canonical_signal import CanonicalSignal, SourceEngine, SignalLayer, SignalTemporalScope
from ..signal.adapters import BaseAdapter, AdapterContext
from ..spec.event_ontology_v1 import Domain, EventDirection
from ..reasoning.bazi_ten_gods import ten_god, BRANCH_HIDDEN_STEMS, GENERATES, CONTROLS
from ..reasoning.bazi_fixed_tables import road_branch, absolute_branch


# ─── 盲派核心常量 ─────────────────────────────────────────────────────────────

# 地支六合
BRANCH_LIUHE = {
    'ZI': 'CHOU', 'CHOU': 'ZI',
    'YIN': 'HAI', 'HAI': 'YIN',
    'MAO': 'XU', 'XU': 'MAO',
    'CHEN': 'YOU', 'YOU': 'CHEN',
    'SI': 'SHEN', 'SHEN': 'SI',
    'WU': 'WEI', 'WEI': 'WU',
}

# 地支三合
BRANCH_SANHE = {
    'SHEN-ZI-CHEN': {'SHEN', 'ZI', 'CHEN'},  # 水局
    'HAI-MAO-WEI': {'HAI', 'MAO', 'WEI'},    # 木局 (fix: 原SHEN-MAO-WEI错误)
    'YIN-WU-XU': {'YIN', 'WU', 'XU'},       # 火局
    'SI-YOU-CHOU': {'SI', 'YOU', 'CHOU'},   # 金局
}

# 地支六冲（盲派体用失衡判据：体支被冲 = 体受伤）
BRANCH_CHONG = {
    'ZI': 'WU', 'WU': 'ZI',
    'CHOU': 'WEI', 'WEI': 'CHOU',
    'YIN': 'SHEN', 'SHEN': 'YIN',
    'MAO': 'YOU', 'YOU': 'MAO',
    'CHEN': 'XU', 'XU': 'CHEN',
    'SI': 'HAI', 'HAI': 'SI',
}

# 地支六害(六穿) — V2.4: 盲派核心技法, 穿比冲更狠(背后偷袭、排斥破坏)
# 子未穿/丑午穿/寅巳穿/卯辰穿/申亥穿/酉戌穿
BRANCH_CHUAN = {
    'ZI': 'WEI', 'WEI': 'ZI',
    'CHOU': 'WU', 'WU': 'CHOU',
    'YIN': 'SI', 'SI': 'YIN',
    'MAO': 'CHEN', 'CHEN': 'MAO',
    'SHEN': 'HAI', 'HAI': 'SHEN',
    'YOU': 'XU', 'XU': 'YOU',
}

# 地支三刑 — V3.0（原书：体用宾主之字进行刑冲克穿合墓都是做功的方式）
# 寅巳申=无恩之刑 / 丑戌未=恃势之刑 / 子卯=无礼之刑 / 辰午酉亥=自刑
# 注意：巳申既刑又六合，做功关系判定按"合优先"（巳申合为主，合功优先于刑）。
BRANCH_SANXING_PAIRS: Set[Tuple[str, str]] = {
    ('YIN', 'SI'), ('YIN', 'SHEN'), ('SI', 'SHEN'),
    ('CHOU', 'XU'), ('CHOU', 'WEI'), ('XU', 'WEI'),
    ('ZI', 'MAO'),
    ('CHEN', 'CHEN'), ('WU', 'WU'), ('YOU', 'YOU'), ('HAI', 'HAI'),
}

# 地支六破（《渊海子平·地支六破》）：子酉/丑辰/寅亥/卯午/巳申/未戌
# 破=六合被冲坏之变体, 破坏/重组; 与六合冲突对(寅亥/巳申)以六合优先, 与三刑冲突对(未戌)以刑优先
BRANCH_PO = {
    'ZI': 'YOU', 'YOU': 'ZI',
    'CHOU': 'CHEN', 'CHEN': 'CHOU',
    'YIN': 'HAI', 'HAI': 'YIN',
    'MAO': 'WU', 'WU': 'MAO',
    'SI': 'SHEN', 'SHEN': 'SI',
    'WEI': 'XU', 'XU': 'WEI',
}

# 地支半合（三合局含中神的两字）：申子/子辰水、亥卯/卯未木、寅午/午戌火、巳酉/酉丑金
# 半合力量小于全合, 大于拱合; 盲派"申子合=夫到夫宫/财到财宫"即半合信号
BRANCH_BANHE: Set[Tuple[str, str]] = {
    # 水局(申子辰)：申子、子辰（含中神子）
    ('SHEN', 'ZI'), ('ZI', 'SHEN'), ('ZI', 'CHEN'), ('CHEN', 'ZI'),
    # 木局(亥卯未)：亥卯、卯未（含中神卯）
    ('HAI', 'MAO'), ('MAO', 'HAI'), ('MAO', 'WEI'), ('WEI', 'MAO'),
    # 火局(寅午戌)：寅午、午戌（含中神午）
    ('YIN', 'WU'), ('WU', 'YIN'), ('WU', 'XU'), ('XU', 'WU'),
    # 金局(巳酉丑)：巳酉、酉丑（含中神酉）
    ('SI', 'YOU'), ('YOU', 'SI'), ('YOU', 'CHOU'), ('CHOU', 'YOU'),
}

# 地支拱合（两字拱中神，不含中神）：寅戌拱午/巳丑拱酉/申辰拱子/亥未拱卯
# 拱合=隔位暗拱中神, 力量最弱; 口诀"两辰拱财局=婚姻好"即拱局类信号
BRANCH_GONG: Set[Tuple[str, str]] = {
    ('YIN', 'XU'), ('XU', 'YIN'),   # 拱午(火)
    ('SI', 'CHOU'), ('CHOU', 'SI'), # 拱酉(金)
    ('SHEN', 'CHEN'), ('CHEN', 'SHEN'), # 拱子(水)
    ('HAI', 'WEI'), ('WEI', 'HAI'), # 拱卯(木)
}

# 三刑组（三字齐全才论三刑；两字寅巳=六穿优先、丑未=六冲优先、戌未/丑戌=恃势之刑）
SANXING_GROUPS = [
    {'YIN', 'SI', 'SHEN'},   # 无恩之刑
    {'CHOU', 'XU', 'WEI'},   # 恃势之刑
]


def _sanxing_full(b1: str, b2: str, all_branches: List[str]) -> bool:
    """三刑判定：寅巳申/丑戌未三字齐全时, 组内任意两字=刑；子卯=无礼之刑恒论；自刑恒论。
    两字不全的三刑拆对(如寅巳、巳申)不按刑论——寅巳归六穿(害), 巳申归六合。"""
    for grp in SANXING_GROUPS:
        if b1 in grp and b2 in grp and grp.issubset(all_branches):
            return True
    # 子卯无礼之刑（恒论）
    if (b1, b2) in (('ZI', 'MAO'), ('MAO', 'ZI')):
        return True
    # 自刑
    if b1 == b2 and b1 in ('CHEN', 'WU', 'YOU', 'HAI'):
        return True
    return False


def resolve_branch_relation(b1: str, b2: str, all_branches: List[str]) -> Optional[str]:
    """统一地支关系解析层（盲派优先级）：
    六合 > 六冲 > 三刑(三字全) > 六穿(害) > 六破 > 半合 > 拱合。
    解决"同一对支在不同判定点结论不一致"(巳申=合/刑/破三重、寅巳=穿/刑双重、未戌=刑/破双重)。
    依据：盲派巳申合克=合优先；寅巳申三字全=三刑（三字全论刑）、
    两字不全寅巳=六穿(害)；丑戌未三字全=刑、未戌两字=刑（恃势之刑两字亦论）。
    注：三刑(三字全)优先于穿——寅巳申三字全：寅巳=刑（非穿）。"""
    # 1. 六合优先（巳申既合又刑又破→合克；寅亥既合又破→合）
    if BRANCH_LIUHE.get(b1) == b2:
        return 'liuhe'
    # 2. 六冲
    if BRANCH_CHONG.get(b1) == b2:
        return 'chong'
    # 3. 三刑（三字全优先于穿；未戌刑优先于未戌破；子卯无礼之刑恒论）
    if _sanxing_full(b1, b2, all_branches):
        return 'xing'
    # 4. 六穿（寅巳两字不全时=穿；盲派穿比冲狠）
    if BRANCH_CHUAN.get(b1) == b2:
        return 'chuan'
    # 5. 六破（子酉/丑辰/卯午/未戌余对）
    if BRANCH_PO.get(b1) == b2:
        return 'po'
    # 6. 半合
    if (b1, b2) in BRANCH_BANHE:
        return 'banhe'
    # 7. 拱合
    if (b1, b2) in BRANCH_GONG:
        return 'gong'
    return None


# 墓库 — V2.4: 辰=水墓, 戌=火墓, 丑=金墓, 未=木墓
# 墓库收放: 闭库收物=财富聚拢, 冲库开库=财官出来, 墓喜冲不冲不发
MU_KU = {
    'CHEN': 'WATER',   # 辰=水库(水墓)
    'XU': 'FIRE',      # 戌=火库(火墓)
    'CHOU': 'METAL',   # 丑=金库(金墓)
    'WEI': 'WOOD',     # 未=木库(木墓)
}

# 天干五合（盲派「合功」：日干合财/合官 → 得财/得权）
STEM_HE: Set[Tuple[str, str]] = {
    ('JIA', 'JI'), ('YI', 'GENG'), ('BING', 'XIN'),
    ('DING', 'REN'), ('WU', 'GUI'),
}

# 体用十神分类（段建业盲派，原书原文）：
#   体 = 日主/比肩/禄/印/食神（本钱）；用 = 财/官/伤官（追求目标）
# 伤官为"条件双角色"（规则 BU-006）：做功工具侧归体（食伤制杀/伤官去官），
# 被制目标侧归用（印制食伤中伤官为被制方）。TI_TEN_GODS 保留伤官供工具侧判定，
# 印制食伤等结构在独立块中按"伤官为被制方(用侧)"处理。
TI_TEN_GODS = {'比肩', '劫财', '偏印', '正印', '食神', '伤官'}   # 体（本钱/工具）
YONG_TEN_GODS = {'正财', '偏财', '正官', '七杀'}               # 用（目标：财官）
# 伤官在用侧的条件角色（原书：用=财官伤；印制食伤中伤官为被制方）
YONG_TEN_GODS_CONDITIONAL = {'伤官'}

# 财/官/食伤/印/比劫 分组
GROUP_CAI = {'正财', '偏财'}
GROUP_GUAN = {'正官', '七杀'}
GROUP_SHI = {'食神', '伤官'}
GROUP_YIN = {'正印', '偏印'}
GROUP_BI = {'比肩', '劫财'}

# ─── V3.2 新规则常量（VERIFY-BLIND-034/035/036 + 009 扩展）───────────────
# 燥土脆金（VERIFY-BLIND-034，段氏理象学·相生反常）：
#   原书"土能生金有两种情况不生：1.燥土不能生金反脆金 2.土多埋金"；
#   "如四柱有水，虽见未戌之燥土，亦可生金；如四柱无水，见未戌之燥土定主脆金"；
#   "以未土脆金为最，只因为未中不藏金反藏火"。
DRY_EARTH_BRANCHES = {'WEI', 'XU'}          # 燥土（未/戌）
WET_EARTH_BRANCHES = {'CHEN', 'CHOU'}       # 湿土（辰/丑，生金不伤金）
METAL_BRANCHES = {'SHEN', 'YOU'}            # 金支
WATER_STEMS = {'REN', 'GUI'}                # 水天干（四柱无水判据）
WATER_BRANCHES = {'ZI', 'HAI'}              # 水地支

# 连体柱（VERIFY-BLIND-035 R4，盲派中级命理学第01章"戊申连体/辛酉连体"）
# 干支一气之体=本柱干支同气一体（印带身/禄带身），坏之伤寿：
#   戊申=戊土生申金为一体(用金)；辛酉=金气连体；庚子=金水连体；甲午=木火连体
LIAN_TI_COLUMNS = {
    'WU-SHEN': 'EARTH-METAL', 'XIN-YOU': 'METAL-METAL',
    'GENG-ZI': 'METAL-WATER', 'JIA-WU': 'WOOD-FIRE',
}

# 纳音五行映射（VERIFY-BLIND-036 六亲计数，纳音同类论手足）
# 六十甲子纳音 30 种 → 五行（《三命通会·论纳音》E-SMTH-003-001）
NAYIN_FIVE_ELEMENT = {
    '海中金': 'METAL', '剑锋金': 'METAL', '白蜡金': 'METAL', '沙中金': 'METAL',
    '金箔金': 'METAL', '钗钏金': 'METAL',
    '大林木': 'WOOD', '杨柳木': 'WOOD', '松柏木': 'WOOD', '平地木': 'WOOD',
    '桑柘木': 'WOOD', '石榴木': 'WOOD',
    '涧下水': 'WATER', '泉中水': 'WATER', '长流水': 'WATER', '天河水': 'WATER',
    '大溪水': 'WATER', '大海水': 'WATER',
    '炉中火': 'FIRE', '山头火': 'FIRE', '霹雳火': 'FIRE', '山下火': 'FIRE',
    '覆灯火': 'FIRE', '天上火': 'FIRE',
    '路旁土': 'EARTH', '城头土': 'EARTH', '屋上土': 'EARTH', '壁上土': 'EARTH',
    '大驿土': 'EARTH', '沙中土': 'EARTH',
}


# ─── 盲派数据结构 ─────────────────────────────────────────────────────────────

# ── 新规则枚举（V1-FINAL：method_scope / 做功强弱 / 结构外显 / 功神角色）──

class MethodScope(str, enum.Enum):
    """盲派传承隔离（规则 §4/§90）。当前实现段建业主线。"""
    DUAN_JIANYE = "DUAN_JIANYE"
    XIA_ZHONGQI = "XIA_ZHONGQI"
    HAO_JINYANG = "HAO_JINYANG"


class WorkEfficiency(str, enum.Enum):
    """做功强弱四档（WK-EFFICIENCY-001，古籍：大/中/小/无效做功）。"""
    LARGE = "LARGE"          # 大效率
    MEDIUM = "MEDIUM"        # 中效率
    SMALL = "SMALL"          # 小效率
    NONE = "NONE"            # 无效做功
    UNDETERMINED = "UNDETERMINED"


# V3.1: 做功归因枚举（盲派核心：谁在做功、是否为我所用）
# 主位做功=为我所用(有效), 宾位做功=非我所有(他作嫁,无效),
# 负功=受损类(禄神受穿等), 中性=无法判定主宾
ZuoGongAttribution = {
    "EFFECTIVE": "EFFECTIVE",      # 主位得气
    "INEFFECTIVE": "INEFFECTIVE",  # 宾位做功(非我所有)
    "NEGATIVE": "NEGATIVE",        # 负功(受损)
    "NEUTRAL": "NEUTRAL",          # 中性
}


class StructureClarity(str, enum.Enum):
    """结构外显四态（WK-EFFICIENCY-003，古籍：清晰/较清/有杂/混乱）。"""
    CLEAR = "CLEAR"
    PARTIALLY_CLEAR = "PARTIALLY_CLEAR"
    MIXED = "MIXED"
    CHAOTIC = "CHAOTIC"
    UNDETERMINED = "UNDETERMINED"


class GongShenRole(str, enum.Enum):
    """功神/废神角色（规则 GS-001~003 / §77）。"""
    WORKING = "WORKING"        # 功神（实际做功）
    SUPPORTING = "SUPPORTING"  # 辅神（辅助做功）
    TARGET = "TARGET"          # 目标（做功对象）
    BLOCKING = "BLOCKING"      # 阻神（阻断/干扰做功）
    IDLE = "IDLE"              # 闲神（method_scope 定义无作用）
    WASTE = "WASTE"            # 废神（明确规则定义为废）
    UNDETERMINED = "UNDETERMINED"


@dataclass
class BlindBaziResult:
    """盲派八字分析结果"""
    # 宾主判定
    main_branches: Set[str] = field(default_factory=set)
    guest_branches: Set[str] = field(default_factory=set)

    # 体用分析
    ti_branches: Set[str] = field(default_factory=set)
    yong_branches: Set[str] = field(default_factory=set)
    ti_stems: List[str] = field(default_factory=list)      # 体天干
    yong_stems: List[str] = field(default_factory=list)    # 用天干

    # 做功判断
    zuo_gong: bool = False
    zuo_gong_type: str = ""
    # ㊻s122c ch3 五类神口径: INEFFECTIVE(宾位做功, 非我所有, 他作嫁) 方法 移出"做功清单"
    # 记入 zuo_gong_images(他作嫁象, 仅取象参考); 新增 zuo_gong_effective=真做功清单
    # (EFFECTIVE+NEGATIVE, 供 L4 效率/层次/区分度判定)。㊻s122 过度收敛回退(可真值 87.8→85.4,
    # 总方向 92→91), ㊻s122c 修正: zuo_gong_methods 保持完整触发清单(供 L7 各域消费),
    # 区分度改用 zuo_gong_effective 判定, 不再删减 L7 依赖的 INEFFECTIVE 方法。
    zuo_gong_effective: List[str] = field(default_factory=list)   # 真做功(为我所用/为我不利, 参与断层次)
    zuo_gong_effective_detail: List[str] = field(default_factory=list)
    # ㊻s124 ch10 婚姻颗粒度(原书 L30-34/L40/L45-46):
    #   liyi_risk(轻则离/重则必离): ch10 "破坏轻则婚姻不好不一定离; 破坏重则必离".
    #   判据: marriage_state=BROKEN(宫坏+星弱, 重)=必离; CHALLENGED(轻)=不一定离(可经营).
    liyi_risk: str = "UNDETERMINED"            # CHU(重, 必离) / QING(轻, 不一定离) / UNDETERMINED
    liyi_risk_evidence: List[str] = field(default_factory=list)
    #   比劫争夫争妻(轻=第三者, 重=离婚): ch10 "比劫争夫/争妻: 轻者有第三者, 重者必离婚.
    #   比肩只要和夫星(妻星)有关系就行, 不一定要和夫宫有关".
    zhenfu_risk: str = "UNDETERMINED"          # THIRD_PARTY(第三者) / DIVORCE(离婚) / NONE / UNDETERMINED
    zhenfu_risk_evidence: List[str] = field(default_factory=list)
    #   正偏夫/妻: ch10 L38 "夫星(妻星)坐正位=正夫(正妻), 偏位=偏夫(偏妻). 不以星的正偏定, 以宫位定".
    poshui_star: str = "UNDETERMINED"          # ZHENG(正) / PIAN(偏) / UNDETERMINED
    poshui_star_evidence: List[str] = field(default_factory=list)
    # ㊻s124 婚姻三子维细分: 宫动静/合冲/婚外缘分 引擎已有, 此处补 正偏夫(妻)/争夫争妻/离异轻重
    # ㊻s124 ch11 学业颗粒度(原书 L15 文理细分 / L24 伤官太旺中断):
    #   学中断: ch11 L24 "伤官太旺无制→中途中断学历, 后补文凭(八字有官则后补)"
    edu_zhongduan: str = "UNDETERMINED"        # ZHONGDUAN(伤官旺中断) / HOU_BU(八字有官后补) / UNDETERMINED
    edu_zhongduan_evidence: List[str] = field(default_factory=list)
    zuo_gong_images: List[str] = field(default_factory=list)   # 他作嫁象(INEFFECTIVE 宾位做功, 非我所有)
    zuo_gong_image_detail: List[str] = field(default_factory=list)  # 他作嫁象判据说明
    zuo_gong_methods: List[str] = field(default_factory=list)   # ['合财','食伤制杀',...]
    zuo_gong_detail: List[str] = field(default_factory=list)
    # 做功归因（V3.1：与 zuo_gong_detail 一一对应）
    # EFFECTIVE=主位得气(为我所用) / INEFFECTIVE=宾位做功(非我所有,他作嫁)
    # / NEGATIVE=负功(禄神受穿等受损类) / NEUTRAL=无法判定主宾
    zuo_gong_attributions: List[str] = field(default_factory=list)
    zuo_gong_actor_dimensions: List[str] = field(default_factory=list)  # 根因D：谁在做功三维度(日主亲自/禄身/主位借力/宾位), 与 methods 一一对应

    # 十神配置（透干十神）
    transparent_ten_gods: Dict[str, str] = field(default_factory=dict)  # {柱: 十神}

    # ── 新规则字段（V1-FINAL）──────────────────────────────────
    method_scope: str = MethodScope.DUAN_JIANYE.value      # 传承隔离
    # 做功强弱（WK-EFFICIENCY-001~005）
    work_efficiency: str = WorkEfficiency.UNDETERMINED.value   # 大/中/小/无效
    structure_clarity: str = StructureClarity.UNDETERMINED.value  # 结构外显四态
    eff_path_direct: bool = False        # 三判据① 做功路径是否直接
    eff_power_concentrated: bool = False # 三判据② 做功力量是否集中
    eff_target_effective: bool = False   # 三判据③ 做功对象是否得力
    work_level: str = "UNDETERMINED"     # 做功等级五档（理法-结果层）
    zheng_fan_ju: str = ""               # 正局/反局（段建业第一章）: ZHENG/FAN/UNKNOWN
    zei_bu: str = ""                    # 贼神捕神结构（段建业大连讲义）: ZEI_BU/NO
    zei_bu_reason: str = ""             # 贼捕结构理由
    # 寻根溯源（段建业哈尔滨讲义：宾主体用后先找财官根在哪柱，定我家他家）
    # {ten_god: [{"root_branch":支, "pillar":YEAR/MONTH/DAY/HOUR, "owner":GUEST/HOST}]}
    # 我宫(主)=DAY/HOUR；他宫(宾)=YEAR/MONTH。财官根在他家=公家/打工；根在我家=自己的
    root_provenance: Dict[str, list] = field(default_factory=dict)
    # 功神/废神角色（GS-001~003）
    gong_shen: Dict[str, List[str]] = field(default_factory=dict)  # {角色: [支/干]}
    # 做功参与支（结构枚举，供功神/废神划分：功神=参与做功、废神/闲神=不参与）
    zuo_gong_actors: Set[str] = field(default_factory=set)   # 参与做功的支（功神）
    zuo_gong_targets: Set[str] = field(default_factory=set)  # 做功目标支（目标神）
    # 制尽（规则 §37 CONTROL_COMPLETENESS）
    control_completeness: str = "UNDETERMINED"   # COMPLETE / PARTIAL / UNDETERMINED
    # ── 未核证规则域占位（VERIFY-BLIND 门禁）────────────────
    # 规则文档已列规则域但核证未通过（VERIFY-BLIND-015/017/022/023）：
    # 按"核证通过前不施工、不自行发明规则"原则，引擎只输出 UNDETERMINED 占位，
    # 不发明判定逻辑。核证完成并锁定规则后再落地。
    thief_capture: str = "UNDETERMINED"          # 贼神/捕神 §24（VERIFY-BLIND-015）
    ganzhi_transmission: str = "UNDETERMINED"    # 干支互通 §26（VERIFY-BLIND-017）
    image_substitution: str = "UNDETERMINED"     # 换象 §27（VERIFY-BLIND-022）
    kinship_chain: str = "UNDETERMINED"          # 六亲组合链 §30（VERIFY-BLIND-023）
    # ── V3.2 新增（VERIFY-BLIND-034/035/036 + 009扩展，古籍核证后施工）──
    dry_earth_brittle: str = "UNDETERMINED"      # 燥土脆金 §VERIFY-034（TRIGGERED / NOT_TRIGGERED）
    he_ban_structures: List[str] = field(default_factory=list)  # 合绊 §WK-H-003（VERIFY-009 扩展）
    zheng_fan_ju: str = "UNDETERMINED"           # 正局/反局 §VERIFY-035（ZHENG / FAN_JU / UNDETERMINED）
    zheng_fan_ju_detail: str = ""                # 反局类型/所在（R1-R4/岁运）
    blind_wangshuai: str = "UNDETERMINED"        # 盲派旺衰五态 §VERIFY-036 前置
    kinship_count: Dict[str, object] = field(default_factory=dict)  # 六亲计数 §VERIFY-036
    nayin_five_elements: Dict[str, str] = field(default_factory=dict)  # 纳音五行事实（排盘层消费）
    # V3.6.9㉞ ch13 虚实法则: 虚透星(干透但支无根=虚, 力量弱/应期推迟或虚化)
    # 原书 ch13 "虚透=虚无根, 实=有根有力"。识别口径: 某非日主十神星干透于四柱干,
    # 但其落根支(该干长生禄位)不在四柱支 = 虚透。分用忌: 为用虚透=力弱事难成,
    # 为忌虚透=忌神力量弱(反吉)。引擎输出 xutu_stars={ten_god_name: [stem_en]}
    xutu_stars: Dict[str, List[str]] = field(default_factory=dict)
    # V3.6.9㊴ ch4 神煞: 驿马(马星=走动/远方/交通)+ 空亡(务虚/玄学事业)
    # 驿马: 年支/日支三合局冲支=马星。子午卯酉=寅申(申子辰马在寅), 寅午戌=申(申子辰马在寅→寅午戌马在申), 申子辰=寅, 巳酉丑=亥。
    yima_branches: List[str] = field(default_factory=list)
    # 空亡: 日柱旬空两字。空亡=有其气无其形/务虚事业(金空鸣/火空发/水空流/木空朽/土空陷)
    xunkong_branches: List[str] = field(default_factory=list)
    # V3.6.9㊵ ch11 学历判定: 三神(官杀/印/食神) + 三破神(财/伤官/比劫) + "制了啥啥就好"
    # ㊻s117 ch11 收敛: 原书 L4 "制了啥啥就好 — 杀制尽伤食=数学博士; 伤官无制=聪明但学历不高;
    # 印不做功=懒惰不开化" 只有 有无学历+层次(高/低/无) 两档口径, 无 本科/高中/初中 精确分档.
    # 原判据 7 处 "本科" 为引擎发明(无 ch 支撑), ㊻s117 收敛为 3 枚举:
    #   HIGHER_EDU(高学历, 三神齐功/双神功=博士/硕士例) / BASIC_EDU(有学历, 单神功/泄秀)
    #   / NO_EDU(无学历, 印不做功/财破印/伤官无制). 保留 博士/硕士 原文例作 evidence 细分.
    education_level: str = "UNDETERMINED"     # HIGHER_EDU/BASIC_EDU/NO_EDU/UNDETERMINED
    education_evidence: List[str] = field(default_factory=list)  # 判据说明
    shi_xueyi_xiang: str = "UNDETERMINED"      # ch11 学域 L1 势向(势去制财=欲望破学业/势去制官杀=学业受阻)
    # V3.6.9㊸ ch3 支主学科分流(原书ch3"支主学科: 金水主理/木火主文/戌亥=数学/丑=玄学/申酉=法律/辰=化学")
    education_field: str = "UNDETERMINED"     # 理科/文科/数学/法律/玄学/化学/UNDETERMINED
    education_field_evidence: List[str] = field(default_factory=list)  # 判据说明
    # V3.6.9㊹ ch14 日主性格五行特性(原书ch14"甲怕金/乙喜金克成器/丙怕焚/丁喜旺主玄学/金主杀头形之成")
    day_master_personality: str = "UNDETERMINED"   # 日主性格断语(甲/乙/丙/丁/戊己/庚辛/壬癸)
    day_master_personality_evidence: List[str] = field(default_factory=list)  # 判据说明
    # V3.6.9㊺ ch14 形气循环(原书ch14"辰戌同见=生死起灭/辰=形之初/戌=气始收")
    xingqi_cycle: str = "UNDETERMINED"            # CHEN_XU_TONGJIAN(辰戌同见生死起灭)/UNDETERMINED
    xingqi_cycle_evidence: List[str] = field(default_factory=list)  # 判据说明
    # V3.6.9㊻ ch13 戊己土开库法则(原书ch13"戊开戌辰[形→气], 己开丑未[气→形], 方向相反")
    wuji_kai_ku: str = "UNDETERMINED"            # WU_KAI_XU_CHEN(戊开戌辰)/JI_KAI_CHOU_WEI(己开丑未)/UNDETERMINED
    wuji_kai_ku_evidence: List[str] = field(default_factory=list)  # 判据说明
    # V3.6.9㊽ ch1 势方向(原书ch1"势: 原局五行成势去谁[≥3支成势], 势所制对象=势方向")
    shi_direction: str = "UNDETERMINED"         # 势方向(成势五行→所制五行), 如 FIRE→METAL
    # V3.6.9㊻s86 ch1 定势升级: 势本党/势所制/势强度(三要素: 数量+同党合流+制净)
    shi_party: List[str] = field(default_factory=list)      # 势本党五行(同党合流, 如 ["FIRE","EARTH"])
    shi_controlled: List[str] = field(default_factory=list) # 势所制五行(如 ["METAL","WATER"])
    shi_strength: str = "UNDETERMINED"         # STRONG(单五行≥3支)/WEAK(合流≥3支)/UNDETERMINED
    shi_zhi_jing: str = "UNDETERMINED"          # ZHI_JING(所制无根)/ZHI_BU_JING(所制有根, ch8当财看)/UNDETERMINED
    shi_evidence: List[str] = field(default_factory=list)   # 定势判据说明(数量/燥湿分流/合流/制净)
    # V3.6.9㊻s88 ch1 日干合官方位法则(原书ch1"日干合年月官=我管他, 合时上官=他管我[时上=头脑=被控制]")
    guan_he_fangwei: str = "UNDETERMINED"       # WOGUAN_TA(合年月官=我管他)/TAGUAN_WO(合时上官=他管我/被控制)/UNDETERMINED
    # V3.6.9㊻s88 ch13 虚实法则(原书ch13"一贵抵九贱, 一贱消九贵: 命局中 一个 有功 字 可 抵 九 个 贱字, 一个 有病 字 可 消 九 个 贵字; 断 整体 吉凶 看 哪个 字 权重 最大"):
    # 权重 判 据: 有 功 字(EFFECTIVE 做功 参与 支)=贵; 有 病 字(NEGATIVE 做功 支 或 被 坏 体/时支)=贱.
    gui_jian_dui_mi: str = "UNDETERMINED"      # YI_GUI(贵 字 权重 占 优=整体 吉)/YI_JIAN(贱 字 权重 占 优=整体 凶)/UNDETERMINED
    # V3.6.9㊻ ch4 空亡十象(原书ch4"金空则鸣/火空则发/水空则流/木空则朽/土空则陷; 所用之神旺相而空亡→务虚事业")
    kk_shixiang: str = "UNDETERMINED"           # 金空则鸣/火空则发/水空则流/木空则朽/土空则陷
    kk_wuxu: str = "UNDETERMINED"              # 务虚/玄学事业(印星做功+空亡)
    xinkong_evidence: List[str] = field(default_factory=list)  # 空亡十象判据说明
    # V3.6.9㊻o ch8 比劫双向口径(原书ch8"比劫制财=得财(用劫富命); 比劫分禄=破财, 要看制的是财还是分的是禄")
    bijie_zhichai_fenliu: str = "UNDETERMINED"  # 比劫制财双向: ZHICHAI_DECAI(宾位比劫制财=得财)/FENLU_POCAI(主位比劫分禄=破财)/UNDETERMINED
    # V3.6.9㊻s ch8 禄神当财(原书ch8"无财八字用禄, 喜印生禄, 忌伤食劫财")
    lu_dangcai: str = "UNDETERMINED"            # 禄神当财: YINSHENG_LU_WEALTH(喜印生禄=得财吉)/LU_PO(忌伤食劫财=禄破)/LU_WEALTH_BASE(无财用禄基础口径)/UNDETERMINED
    # V3.6.9㊾ ch5 空间类象+车象(原书ch5"年=远方/月=家乡/日支=居所/时=门户车")
    space_palace: str = "UNDETERMINED"          # 空间方位类象(年=远方/月=家乡/日支=居所/时=门户)
    # ㊻s118 ch5 空间/物品 + ch4 驿马 动态判定: 家宅居所/出行异地域塌缩修复(原 L4741 静态串每盘同句无区分度)
    space_dynamic: str = "UNDETERMINED"          # STABLE(安定)/YIDI(异地谋生)/BANQIAN(搬迁)/JIAZHAI_DONG(家宅动荡)/CHUYING(门户出门)
    space_dynamic_evidence: List[str] = field(default_factory=list)
    car_signal: str = "UNDETERMINED"            # 车象(时支表车/辰=车, 买车车祸均看时支)
    # V3.6.9㊻b ch8 门户做功(原书ch8"门户(时上)做功: 贸易/炒作, 人不能多")
    menhu_trading: str = "UNDETERMINED"         # 门户做功(时柱做功=贸易/炒作品类)
    # V3.6.9㊻d ch7 借象原则(原书ch7"副宫定义: ①从夫妻宫引出的字→该字为副宫; ②与夫妻宫同五行的字; 副宫表短暂[婚姻短暂/副职]; 副宫多现=多婚/多事")
    fugong_palace: str = "UNDETERMINED"         # 副宫(短暂婚姻/副职信号)
    # V3.6.9㊻f ch3 五类神分类(原书ch3"喜神/用神/忌神/病神/闲神: 忌神被强用神制服→行忌神运吉")
    wulei_shen: Dict[str, list] = field(default_factory=dict)  # yongshen/jishen/xianshen
    tone_char: str = "UNDETERMINED"          # V3.6.9㊻g ch13 一贵抵九贱权重定基调(权重最大字)
    # V3.6.9㊻n ch4 神煞类象(驿马/天医/华盖/将星): 排盘层神煞支→断事层类象标注
    shensha_leixiang: str = "UNDETERMINED"    # 驿马(走动/远方/交通)/华盖(玄学)/将星(权柄)/天医(医药)
    # V3.6.9㊶ ch12 牢狱判定: 犯罪结构四类 + 以阴灭阳 + 出狱定法
    crime_structure: str = "UNDETERMINED"     # RIBISHANG_GUAN(比劫伤官)/QISHA_WUZHI(七杀无制)/LU_GUAN_KONGDUI(禄与官对抗)/YIN_MIE_YANG(以阴灭阳)/UNDETERMINED
    crime_present: bool = False               # ㊻s117 ch12 有无口径: 有无犯罪结构(True=有牢狱象/False=无), 供断语层"有无牢狱象"断语
    # ㊻s119 ch6/ch8/ch12 人际合伙域(用户维度文本 13 子域#7, 原书 ch6 比劫/伤官类象 + ch8 比劫当财双向 + ch12 比劫伤官拉帮结派):
    #   4 子维度: 同辈互动(ch6 比肩兄弟/同辈) / 合伙成败(ch8 比劫当财 用劫富命 vs 比劫分禄破财)
    #            / 利益争夺(ch6 劫财 争夺/破财) / 同伴反目(ch12 劫财+伤官=拉帮结派 与官杀对抗)
    interpersonal_structure: str = "UNDETERMINED"  # 4 枚举 + UNDETERMINED:
    #   BIXIONG(比劫+伤官=拉帮结派/同伴反目, 消费 crime_structure=RIBISHANG_GUAN)
    #   HEHUA_DECAI(合伙得财=宾位比劫制财EFFECTIVE, ch8 用劫富命)
    #   FENLU_ZHENGDUI(利益争夺/破财=主位比劫分禄NEGATIVE, ch6 劫财争夺)
    #   TONGPEI_STABLE(同辈互动=比肩在局无争夺/无反目, 平稳)
    #   UNDETERMINED(无比劫/伤官做功, 人际象未明)
    interpersonal_evidence: List[str] = field(default_factory=list)  # 判据说明
    # ㊻s120 ch9/ch11/ch14 名气口碑域(用户维度文本 13 子域#9, 原书: ch9 L18 官杀虚透=名气 + ch11 泄秀=成名 + 得奖):
    #   3 枚举 + UNDETERMINED:
    #   XUTOU_MINGQU(官杀虚透=名气非实官, ch9 L18 "官杀无根=名气不是实官")
    #   XIUXIU_CHENGMING(秀气泄秀=成名, 原书 "日主之秀气活本丙火泄秀故人得漂亮成名")
    #   XINGZUO_DEJIANG(有作品/得奖扬名, 原书 "得金杯/合国第二届" 得奖象)
    #   UNDETERMINED(无名气象)
    mingqi_structure: str = "UNDETERMINED"
    mingqi_evidence: List[str] = field(default_factory=list)
    # ㊻s120 ch14 撤干神心性(用户维度文本 13 子域#12, 原书 ch14 L12 "撤开干支十神单看日干心性"):
    #   外层表象 vs 内里心性的二象(如 "戊子撤开=外表忠厚内心水")。在 day_master_personality
    #   (日干五行象) 基础上加 "撤干神" 维度: 日干坐支/干支一体撤开后, 内里心性独立于外层。
    xingxing_cheganshen: str = "UNDETERMINED"   # 撤干神心性二象描述(外层 vs 内里)
    xingxing_evidence: List[str] = field(default_factory=list)
    # ㊻s120 ch2/ch4/ch13 福分寿元域(用户维度文本 13 子域#13, 原书 "寿元星=日主/禄/印/食神/财星"
    # + "食神为日主寿元, 穿倒寿元星主死" + "合为有寿怕解合" + "正印为忌=操心劳碌"):
    #   3 枚举 + UNDETERMINED:
    #   SHOUDIAN_YANHE(寿元有根/合寿, 寿元星在局有力=寿元长)
    #   SHOUYUAN_XUEYUAN(寿元星被穿倒/枭克, 主寿元受损/健康早夭隐患)
    #   CAOLAO(正印为忌=操心劳碌, 享福薄)
    #   UNDETERMINED(寿元象未明)
    fufen_structure: str = "UNDETERMINED"
    fufen_evidence: List[str] = field(default_factory=list)
    crime_evidence: List[str] = field(default_factory=list)  # 判据说明
    release_path: str = "UNDETERMINED"        # V3.6.9㊻ ch12 出狱定法: 日主得禄之年/冲穿坏库
    # ── V3.3 L1e 事件结构（盲派生产规则 60-64章，全布尔/枚举，无吉凶词汇）──
    marriage_event_structure: Dict[str, str] = field(default_factory=dict)  # 婚姻系统 §60
    wealth_event_structure: Dict[str, str] = field(default_factory=dict)    # 财富系统 §61
    official_event_structure: Dict[str, str] = field(default_factory=dict)  # 官贵系统 §62
    occupation_candidate: Dict[str, object] = field(default_factory=dict)   # 职业系统 §63
    body_event_candidate: Dict[str, str] = field(default_factory=dict)      # 身体/疾病象 §64
    parental_event_structure: Dict[str, str] = field(default_factory=dict) # 父母系统 §65
    # V3.6.9㊻s95 ch4 子女系统(原书ch4 L29"正官为女、七杀为儿" + L11"时支空=子女迟育或有损"):
    child_event_structure: Dict[str, str] = field(default_factory=dict)     # 子女系统 §66
    # 时间层/规则追踪
    undetermined_reasons: List[str] = field(default_factory=list)
    rules_triggered: List[str] = field(default_factory=list)

    # 盲派信号
    signals: List[CanonicalSignal] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'main_branches': list(self.main_branches),
            'guest_branches': list(self.guest_branches),
            'ti_branches': list(self.ti_branches),
            'yong_branches': list(self.yong_branches),
            'ti_stems': self.ti_stems,
            'yong_stems': self.yong_stems,
            'zuo_gong': self.zuo_gong,
            'zuo_gong_type': self.zuo_gong_type,
            'zuo_gong_methods': self.zuo_gong_methods,
            'zuo_gong_effective': self.zuo_gong_effective,
            'zuo_gong_effective_detail': self.zuo_gong_effective_detail,
            'zuo_gong_images': self.zuo_gong_images,
            'zuo_gong_image_detail': self.zuo_gong_image_detail,
            'zuo_gong_detail': self.zuo_gong_detail,
            'zuo_gong_attributions': self.zuo_gong_attributions,
            'zuo_gong_actor_dimensions': self.zuo_gong_actor_dimensions,
            'transparent_ten_gods': self.transparent_ten_gods,
            'method_scope': self.method_scope,
            'work_efficiency': self.work_efficiency,
            'structure_clarity': self.structure_clarity,
            'eff_path_direct': self.eff_path_direct,
            'eff_power_concentrated': self.eff_power_concentrated,
            'eff_target_effective': self.eff_target_effective,
            'work_level': self.work_level,
        'zheng_fan_ju': self.zheng_fan_ju,
        'zei_bu': self.zei_bu,
        'zei_bu_reason': self.zei_bu_reason,
            'gong_shen': self.gong_shen,
            'zuo_gong_actors': sorted(self.zuo_gong_actors),
            'zuo_gong_targets': sorted(self.zuo_gong_targets),
            'control_completeness': self.control_completeness,
            'thief_capture': self.thief_capture,
            'ganzhi_transmission': self.ganzhi_transmission,
            'image_substitution': self.image_substitution,
            'kinship_chain': self.kinship_chain,
            'dry_earth_brittle': self.dry_earth_brittle,
            'he_ban_structures': self.he_ban_structures,
            'zheng_fan_ju': self.zheng_fan_ju,
            'zheng_fan_ju_detail': self.zheng_fan_ju_detail,
            'blind_wangshuai': self.blind_wangshuai,
            'kinship_count': self.kinship_count,
            'nayin_five_elements': self.nayin_five_elements,
            'xutu_stars': self.xutu_stars,
            'marriage_event_structure': self.marriage_event_structure,
            'wealth_event_structure': self.wealth_event_structure,
            'official_event_structure': self.official_event_structure,
            'occupation_candidate': self.occupation_candidate,
            'body_event_candidate': self.body_event_candidate,
            'child_event_structure': self.child_event_structure,
            'parental_event_structure': self.parental_event_structure,
            'rules_triggered': self.rules_triggered,
            'undetermined_reasons': self.undetermined_reasons,
            'signals': [s.to_dict() for s in self.signals],
            # ㊻s123c: 13 域维度层字段(㊻s117-s121 新增, to_dict 此前漏输出 → 验证脚本读 None)
            'education_level': self.education_level,
            'education_field': self.education_field,
            'crime_structure': self.crime_structure,
            'crime_present': self.crime_present,
            'crime_evidence': self.crime_evidence,
            'interpersonal_structure': self.interpersonal_structure,
            'interpersonal_evidence': self.interpersonal_evidence,
            'mingqi_structure': self.mingqi_structure,
            'mingqi_evidence': self.mingqi_evidence,
            'xingxing_cheganshen': self.xingxing_cheganshen,
            'xingxing_evidence': self.xingxing_evidence,
            'fufen_structure': self.fufen_structure,
            'fufen_evidence': self.fufen_evidence,
            'space_dynamic': self.space_dynamic,
            'space_palace': self.space_palace,
            'car_signal': self.car_signal,
            'fugong_palace': self.fugong_palace,
            'day_master_personality': self.day_master_personality,
            'bijie_zhichai_fenliu': self.bijie_zhichai_fenliu,
            'yin_mie_yang_present': self.crime_present,
        }


# ─── 盲派引擎 ─────────────────────────────────────────────────────────────────

class BlindBaziEngine:
    """盲派八字引擎 - 宾主/体用/做功/断事分析"""

    def __init__(self, bazi_engine=None):
        self.bazi_engine = bazi_engine or canonical_bazi_engine

    # ── 主入口 ─────────────────────────────────────────────
    def compute(self, birth: Tuple[int, int, int, int], gender: str = "male") -> BlindBaziResult:
        """阳历入口：先排盘，再委托 compute_from_chart（单一真相源）。

        V2.1 切片 S0 前置：compute(birth) 与 compute_from_chart(chart) 共用同一段
        主链逻辑，排盘动作只发生在 compute 内；compute_from_chart 绝不重排盘。
        """
        chart = self.bazi_engine.compute(birth, gender=gender)
        return self.compute_from_chart(chart, gender=gender, birth_year=birth[0])

    # ── S0 切片契约入口（生产/测试 共用，不重排盘）──────────────────
    def compute_from_chart(
        self,
        chart,
        gender: Optional[str] = None,
        birth_year: Optional[int] = None,
    ) -> BlindBaziResult:
        """吃外部 BaziChart（已由 BaziEngine.compute 排好），跑盲派主链。

        V2.1 切片 S0 契约（骨架 盲派切片工程骨架.txt 第〇节）：
          - 输入 = BaziChart（含 18 可消费字段），禁止重新排盘
          - gender: 缺省时取 chart.gender
          - birth_year: 仅用于 signal id 前缀；缺省从 chart.birth_datetime 取，
            仍缺省则用 None → signal id 前缀 "UNKNOWN"（不编造，守审计红线）
          - 失败 fail-closed：chart 非 BaziChart / 四柱不齐 直接抛异常

        主链逻辑与原 compute(birth) 第 435–604 行完全一致（单一真相源）。
        """
        from .bazi_engine import BaziChart as _BaziChart
        if not isinstance(chart, _BaziChart):
            raise TypeError(
                "compute_from_chart 只接受 BaziChart（S0 G-B01）；"
                f"got {type(chart).__name__}"
            )
        # 四柱干支齐全检查（S0 G-B03）
        for pos in ("year", "month", "day", "hour"):
            p = getattr(chart, f"{pos}_pillar")
            if not p.heavenly_stem or not p.earthly_branch:
                raise ValueError(f"S0 G-B03 fail-closed: {pos}_pillar 干支不齐")
        if chart.day_master != chart.day_pillar.heavenly_stem:
            raise ValueError("S0 G-B03 fail-closed: day_master 与日柱天干不一致")

        if gender is None:
            gender = getattr(chart, "gender", "male") or "male"
        if birth_year is None:
            bd = getattr(chart, "birth_datetime", None)
            birth_year = bd.year if bd is not None else None

        result = BlindBaziResult()

        # 1. 宾主判定（主位=日柱+时柱，宾位=年柱+月柱；与应期引擎
        #    main_branches=[day,hour] 一致，时柱不得归入宾位）
        result.main_branches.add(chart.day_pillar.earthly_branch)
        result.main_branches.add(chart.hour_pillar.earthly_branch)
        result.guest_branches.add(chart.year_pillar.earthly_branch)
        result.guest_branches.add(chart.month_pillar.earthly_branch)

        # 日主(提前定义, 供体用分析和透干十神使用)
        day_master = chart.day_master

        # 2. 体用分析（V2.6: 遍历所有支含日支藏干, 原逻辑日支只进体不进用导致日支藏财官缺失）
        # 体（本钱）= 比肩/劫财/印/食神/伤官; 用（目标）= 财/官杀
        # 日支为日主之根, 天然属体; 同时按藏干十神分类, 一支可同时属体用
        result.ti_branches.add(chart.day_pillar.earthly_branch)
        all_branches = [
            chart.year_pillar.earthly_branch,
            chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch,
            chart.hour_pillar.earthly_branch,
        ]
        for b in all_branches:
            for hidden_stem, _pos in BRANCH_HIDDEN_STEMS.get(b, []):
                tg = ten_god(day_master, hidden_stem)
                if tg in TI_TEN_GODS:
                    result.ti_branches.add(b)
                elif tg in YONG_TEN_GODS:
                    result.yong_branches.add(b)

        # 3. 透干十神（年/月/时干相对日主）
        stems = {
            'year': (chart.year_pillar.heavenly_stem, ten_god(day_master, chart.year_pillar.heavenly_stem)),
            'month': (chart.month_pillar.heavenly_stem, ten_god(day_master, chart.month_pillar.heavenly_stem)),
            'hour': (chart.hour_pillar.heavenly_stem, ten_god(day_master, chart.hour_pillar.heavenly_stem)),
        }
        result.transparent_ten_gods = {k: v[1] for k, v in stems.items()}
        # 体用天干
        result.ti_stems = [st for _, (st, tg) in stems.items() if tg in TI_TEN_GODS]
        result.yong_stems = [st for _, (st, tg) in stems.items() if tg in YONG_TEN_GODS]

        # V3.6.9㉞ ch13 虚实法则: 虚透星识别(干透但支无根=虚, 力量弱/应期推迟或虚化)
        # 原书 ch13 "虚透=虚无根, 实=有根有力"。识别口径: 某非日主十神星干透于四柱干,
        # 但该干五行在四柱地支藏干中无任何根(长生/禄/墓均无) = 虚透。
        # V3.6.9㊻b 修: 原口径用"落根支(长生/禄位)不在四支"判虚, 过严——
        # 辛落根酉不在支≠辛无根(酉藏辛干=该干自身), 改为"藏干中无该五行任何干"。
        # 例: 辛亥壬辰辛巳壬辰, 辛=金, 支藏干: 亥藏壬甲(无金), 辰藏戊乙癸(无金),
        #     巳藏丙庚戊(藏庚=金!), 辛在巳中庚金=有根 → 辛不透虚; 但亥/辰无金根=辛仅根在巳,
        #     若巳不在支则辛=虚透。此例巳在支=辛有根, 不虚。
        from tongshu.facts.bazi_facts import BRANCH_HIDDEN_STEMS as _BHS
        # ㊻b2: 虚透须该干本身在藏干中无同类干(含该干自身), 不能以"他干同类有根"替代自身有根。
        # 原书 ch13 "虚=该干无根", 非"该五行无根"——丙无根=丙虚(不以乙根替代), 庚无根=庚虚(不以辛根替代)。
        # 判据: 某非日主天干透于四柱干, 且 藏干中无该干同类干(含自身)=虚透。
        seen_xu_stems = set()
        for _, (st, tg) in stems.items():
            if st == day_master or st in seen_xu_stems:
                continue
            # ㊻b2: 该干自身(同类十干)是否在藏干中(含禄位支, 如甲→寅藏甲)
            st_elem = {"JIA":"WOOD","YI":"WOOD","BING":"FIRE","DING":"FIRE",
                       "WU":"EARTH","JI":"EARTH","GENG":"METAL","XIN":"METAL",
                       "REN":"WATER","GUI":"WATER"}.get(st, "")
            same_elem_stems = {"WOOD":["JIA","YI"],"FIRE":["BING","DING"],
                               "EARTH":["WU","JI"],"METAL":["GENG","XIN"],
                               "WATER":["REN","GUI"]}.get(st_elem, [])
            has_self_root = any(
                h in same_elem_stems
                for _b in all_branches
                for h, _p in _BHS.get(_b, [])
            )
            if not has_self_root:
                seen_xu_stems.add(st)
                result.xutu_stars.setdefault(tg, []).append(st)

        # V3.6.9㊴ ch4 神煞: 驿马(马星=走动/远方/交通) + 空亡(务虚/玄学事业)
        # 驿马: 年支/日支三合局冲支=马星。
        #   子午卯酉(四正)→驿马=寅申(寅申冲=驿马动)
        #   寅午戌(三合火局)→驿马=申
        #   申子辰(三合水局)→驿马=寅
        #   巳酉丑(三合金局)→驿马=亥
        YIMA_MAP = {
            "ZI": "YIN", "WU": "SHEN", "MAO": "YIN", "YOU": "SHEN",  # 子午卯酉
            "YIN": "SHEN", "WU": "SHEN", "XU": "SHEN",               # 寅午戌(火局)
            "SHEN": "YIN", "ZI": "YIN", "CHEN": "YIN",                # 申子辰(水局)
            "SI": "HAI", "YOU": "HAI", "CHOU": "HAI",                # 巳酉丑(金局)
        }
        # 驿马支 = 年支三合局马 + 日支三合局马
        year_b = chart.year_pillar.earthly_branch
        day_b = chart.day_pillar.earthly_branch
        yima_set = set()
        yima_set.add(YIMA_MAP.get(year_b, ""))
        yima_set.add(YIMA_MAP.get(day_b, ""))
        result.yima_branches = sorted([b for b in yima_set if b])

        # 空亡: 日柱旬空两字(查法: 日柱干支在六十甲子中的旬首, 旬首后第10、11个支=空亡)
        GANS60 = ["JIA","YI","BING","DING","WU","JI","GENG","XIN","REN","GUI"]
        ZHIS60 = ["ZI","CHOU","YIN","MAO","CHEN","SI","WU","WEI","SHEN","YOU","XU","HAI"]
        di = GANS60.index(day_master)
        zi = ZHIS60.index(day_b)
        day_idx = next(i for i in range(60) if i % 10 == di and i % 12 == zi)
        xun_start = (day_idx // 10) * 10
        xun_branches = [ZHIS60[(xun_start + k) % 12] for k in range(10)]
        xunkong = [b for b in ZHIS60 if b not in xun_branches]
        result.xunkong_branches = xunkong
        # V3.6.9㊻ ch4 空亡十象(原书ch4"金空则鸣/火空则发/水空则流/木空则朽/土空则陷"):
        # 空亡支的五行=该五行空亡象. 所用之神旺相而空亡→务虚事业(佛道玄学五术气功艺术).
        KK_SHIXIANG = {
            "METAL": "金空则鸣",
            "FIRE": "火空则发",
            "WATER": "水空则流",
            "WOOD": "木空则朽",
            "EARTH": "土空则陷",
        }
        kk_shixiang = [KK_SHIXIANG.get(_branch_element(b), "UNDETERMINED") for b in xunkong]
        result.kk_shixiang = "、".join(kk_shixiang) if kk_shixiang else "UNDETERMINED"
        # 所用之神旺相而空亡→务虚事业(佛道玄学): 印星做功EFFECTIVE+印星所在支空亡
        # V3.6.9㊻ 修: 此段在 compute_from_chart 早期调用(zuogong 未算),
        # 改为查 xunkong 支的五行是否为木/金/水(印星五行)+ 全局印星做功EFFECTIVE
        # 延迟到 _resolve_education_level 后统一计算(见下方 _resolve_kk_wuxu)
        result.xinkong_evidence = kk_shixiang


        # 4. 做功分析
        self._analyze_zuogong(chart, result, stems, day_master)

        # 5b. 制尽三态（VERIFY-BLIND-020/021，段氏理象学·制净原则 + 制尽杀星得天下）
        # V3.2 升级：原 COMPLETE/PARTIAL 二态 → CLEAN/PARTIAL/DIRTY 三态。
        #   原书（段氏理象学制用做功）："制得越彻底（制净）层次越高。大富贵：
        #     印比成势，财星孤立无援被制净…普通人：印比成势但财星也有根气，
        #     制不干净，属势大有功但不彻底"；"制尽杀星得天下"；
        #   原书"年上午制不净，官杀制不净当财看；时上午制净了，当官看"。
        # 诊断：V3.1 遗留域缺口——印制食伤干净=巨财，制净层次未区分，
        #       一律 COMPLETE 导致层次判断不到；制不净需显式 PARTIAL。
        # 布尔规则（零评分）：
        #   CLEAN   = 控制路径存在 且 目标支孤立无援（目标五行在四柱无同类/无生扶）
        #   PARTIAL = 控制路径存在 但 目标支有根气（制不干净）
        #   DIRTY   = 目标为官杀 且 PARTIAL → 官杀制不净当财看（解锁换象 HX3）
        if result.zuo_gong and result.yong_branches:
            control_methods = [
                m for m in result.zuo_gong_methods
                if ('制' in m or '穿' in m or '冲' in m or '脆' in m or '收' in m)
            ]
            if control_methods:
                # 目标支孤立无援判据（布尔）：目标支本气五行在四柱其他支
                # 无同类本气/藏干（孤立=制净；有同类=有根气=制不净）
                target_isolated = self._target_isolated(chart, result)
                if target_isolated:
                    result.control_completeness = "CLEAN"
                    result.rules_triggered.append("CONTROL-COMPLETENESS-001")
                else:
                    result.control_completeness = "PARTIAL"
                    result.rules_triggered.append("CONTROL-COMPLETENESS-002")
            else:
                result.control_completeness = "PARTIAL"
                result.rules_triggered.append("CONTROL-COMPLETENESS-002")
        else:
            result.control_completeness = "UNDETERMINED"
            result.rules_triggered.append("CONTROL-COMPLETENESS-003")


        # 4b. 做功强弱（WK-EFFICIENCY-001~005，古籍三判据 → 四档枚举）
        self._resolve_work_efficiency(chart, result)

        # 4c. 功神/废神角色（GS-001~003）
        self._resolve_gong_shen(chart, result)

        # 4d. 正局/反局（VERIFY-BLIND-035，盲派中级命理学第01章 R1-R4）
        self._resolve_zheng_fan_ju(chart, result, day_master)

        # 5. 生成盲派信号
        self._generate_signals(chart, result, birth_year, stems, day_master)

        # 5d. 贼神/捕神（VERIFY-BLIND-015 已核证解锁，原书：主/体旺制宾/用弱
        #      且制死制净=贼捕结构；官杀无制非贼捕，喜行捕神运；贼捕喜走贼神运）
        tg_set_all = set(t for _, t in stems.values())
        for b_ in all_branches:
            for hidden_stem_, _p_ in BRANCH_HIDDEN_STEMS.get(b_, []):
                tg_set_all.add(ten_god(day_master, hidden_stem_))
        has_officer_killer = bool(tg_set_all & (GROUP_GUAN | {'正官', '七杀'}))
        officer_methods = [
            m for m in result.zuo_gong_methods
            if ('官' in m or '杀' in m)
        ]
        if result.zuo_gong and result.control_completeness == "CLEAN":
            result.thief_capture = "THIEF_CAPTURE"
            result.rules_triggered.append("THIEF-001")
            result.rules_triggered.append("CAPTURE-001")
        elif has_officer_killer and not officer_methods:
            # 段建业原书原文: "局中官杀无制，不属于贼捕结构，喜行捕神的大运和流年"
            result.thief_capture = "NO_THIEF_CAPTURE_OFFICER_UNCONTROLLED"
            result.rules_triggered.append("THIEF-002")

        # 5e. 干支互通（VERIFY-BLIND-017 已核证解锁，段氏理象学第三节·干支配置原理）
        # 自合柱：辛巳/癸巳/丁亥/己亥=支克干；戊子/甲午/壬午/壬戌/丙戌=干克支
        # （原书：干支相合的情况下论地支克天干…壬戌丙戌两柱必须刑开才能自合）
        SELF_HE_COLUMN_DIR = {
            'XIN-SI': 'BRANCH_KILLS_STEM', 'GUI-SI': 'BRANCH_KILLS_STEM',
            'DING-HAI': 'BRANCH_KILLS_STEM', 'JI-HAI': 'BRANCH_KILLS_STEM',
            'WU-ZI': 'STEM_KILLS_BRANCH', 'JIA-WU': 'STEM_KILLS_BRANCH',
            'REN-WU': 'STEM_KILLS_BRANCH', 'REN-XU': 'STEM_KILLS_BRANCH',
            'BING-XU': 'STEM_KILLS_BRANCH',
        }
        self_he_list = []
        for pillar_ in [
            chart.year_pillar, chart.month_pillar,
            chart.day_pillar, chart.hour_pillar,
        ]:
            key = f"{pillar_.heavenly_stem}-{pillar_.earthly_branch}"
            if key in SELF_HE_COLUMN_DIR:
                self_he_list.append(f"{key}:{SELF_HE_COLUMN_DIR[key]}")
        if self_he_list:
            result.ganzhi_transmission = "SELF_HE_COLUMN(" + ",".join(self_he_list) + ")"
            result.rules_triggered.append("GT-001")
            result.rules_triggered.append("GT-002")
        else:
            result.ganzhi_transmission = "NO_SELF_HE_COLUMN"

        # 5f. 换象（VERIFY-BLIND-022 解锁，盲派中级命理学财命专辑 + 命理珍宝）
        # 消费制尽 DIRTY（官杀制不净当财看）→ HX3；HX1/HX2/HX5 独立判定
        self._resolve_image_substitution(chart, result, day_master)

        # 4b. 做功强弱（WK-EFFICIENCY-001~005，古籍三判据 → 四档枚举）
        # V3.2 后移至此：需消费 control_completeness(5b) 与 image_substitution(换象)
        self._resolve_work_efficiency(chart, result)

        # 5g. 盲派旺衰五态 + 六亲计数（VERIFY-BLIND-036，命理玄机探秘四定律）
        # 前置=盲派自身旺衰（按势体系，非子平评分）；消费排盘层纳音
        self._resolve_blind_wangshuai(chart, result, day_master)
        self._resolve_kinship_count(chart, result, day_master, gender)

        # ㊻s88 底层拓扑修: L1 定势 + L4 正犯局 须先于 L7 域执行.
        # 原顺序定势(L814)/正犯局(L821)在 L7 域(婚/财/官 L775-777)之后, 致 L7 域消费
        # shi_controlled/zheng_fan_ju 时字段未赋值(全 UNDETERMINED), 域层接线空转.
        # 定势只依赖 L0 体用+L1 成势, 正犯局只依赖定势+L3 日柱追求(自身算), 均不依赖 L7 域,
        # 前移安全. ㊻s88 P1 域层接线的前提.
        # V3.6.9㊽ ch1 势方向(成势去谁→势所制=忌向, 势本党+生势=喜向; 忌喜是 L1 的推论, 非独立层)
        self._resolve_shi_direction(chart, result, day_master)
        # V3.6.9㊽ ch1 正局/反局(R1-R4, 消费 L1 定势 + L3 日柱追求)
        self._resolve_zheng_fan_ju(chart, result, day_master)

        # 5h. L1e 事件结构（60-64章，消费 L0+L1 全结构事实，无吉凶词汇）
        self._resolve_marriage_structure(chart, result, day_master)
        self._resolve_wealth_structure(chart, result, day_master)
        self._resolve_official_structure(chart, result, day_master)
        # V3.6.9㊵ ch11 学历判定(三神三破神 + 制了啥啥就好)
        self._resolve_education_level(chart, result, day_master)
        # V3.6.9㊸ ch3 支主学科分流(金水主理/木火主文/戌亥=数学/丑=玄学/申酉=法律/辰=化学)
        self._resolve_education_field(chart, result, day_master)
        # V3.6.9㊶ ch12 牢狱判定(犯罪结构四类 + 以阴灭阳)
        self._resolve_crime_structure(chart, result, day_master)
        # ㊻s33 时序修: crime_direction 须在犯罪结构算完后回填(ch12 牢狱域方向)。
        # ㊻s6 把它写在 _resolve_official_structure 里读 result.crime_structure, 但
        # _resolve_official_structure(L766) 先于 _resolve_crime_structure(L772) 执行,
        # 读到的是默认 UNDETERMINED → crime_direction 永远 NEUTRAL(时序 bug)。
        # 修: 犯罪结构算完后回填, 有犯罪结构(非 UNDETERMINED)=有牢狱信号(NEGATIVE),
        # 无犯罪结构=中性(NEUTRAL), 不轻判吉/凶。
        if isinstance(result.official_event_structure, dict):
            result.official_event_structure["crime_direction"] = (
                "NEGATIVE" if result.crime_structure != "UNDETERMINED" else "NEUTRAL"
            )

        self._resolve_zei_bu(chart, result, day_master)  # V3.6.9㊻j ch9 贼捕结构(死代码修复)
        # ㊻s119 ch6/ch8/ch12 人际合伙域(4 子维度: 同辈互动/合伙成败/利益争夺/同伴反目)
        self._resolve_interpersonal(chart, result, day_master)
        # ㊻s120 ch9/ch11/ch14/ch2/ch4 深度核查 3 域(名气口碑/撤干神心性/福分寿元)
        self._resolve_mingqi_fufen_xingxing(chart, result, day_master)
        # V3.6.9㊹ ch14 日主性格五行特性(甲怕金/乙喜金克成器/丙怕焚/丁喜旺主玄学/金主杀头形之成)
        self._resolve_day_master_personality(chart, result, day_master)
        # V3.6.9㊺ ch14 形气循环(辰戌同见=生死起灭)
        self._resolve_xingqi_cycle(chart, result, day_master)
        # V3.6.9㊻ ch13 戊己土开库法则(戊开戌辰/己开丑未)
        self._resolve_wuji_kai_ku(chart, result, day_master)
        # V3.6.9㊻ ch4 空亡十象: 印星做功EFFECTIVE+空亡支为木/金/水=玄学/务虚事业(延迟到做功层算完)
        self._resolve_kk_wuxu(chart, result, day_master)
        # V3.6.9㊻f ch3 五类神分类(喜神/用神/忌神/病神/闲神, 消费做功层)
        self._resolve_wulei_shen(chart, result, day_master)
        # V3.6.9㊻g ch13 一贵抵九贱权重定基调(权重最大字)
        self._resolve_tone_char(chart, result, day_master)
        # V3.6.9㊻b ch8 门户做功(时柱做功=贸易/炒作)
        self._resolve_menhu_trading(chart, result, day_master)
        # V3.6.9㊻d ch7 借象原则(副宫=日支同五行支, 副宫多现=婚姻短暂/多事信号)
        self._resolve_fugong_palace(chart, result, day_master)
        self._resolve_shensha_leixiang(chart, result, day_master)
        self._resolve_lu_dangcai(chart, result, day_master)
        # ㊻s88: _resolve_shi_direction 与 _resolve_zheng_fan_ju 已前移至 L7 域之前(见 L774 附近),
        # 此处原重复调用已删, 避免二次覆盖.
        # V3.6.9㊾ ch5 空间类象+车象(年=远方/月=家乡/日支=居所/时=门户车)
        self._resolve_space_palace(chart, result, day_master)
        self._resolve_occupation_candidate(chart, result, day_master)
        self._resolve_body_candidate(chart, result, day_master)
        self._resolve_parental_structure(chart, result, day_master)
        self._resolve_root_provenance(chart, result, day_master)

        # 5c. 未核证规则域占位说明（只记一次）
        # V3.2：六亲计数(VERIFY-BLIND-036)已解锁；023 六亲组合链=实战断语技法域，
        # 只做计数不编断语，维持占位（用户铁律：不自行发明规则）
        pending = {"六亲组合链": "VERIFY-BLIND-023"}
        for domain, verify_id in pending.items():
            if not any(verify_id in r for r in result.undetermined_reasons):
                result.undetermined_reasons.append(
                    f"{domain}: {verify_id} 核证通过前不施工，输出 UNDETERMINED 占位"
                )

        return result

    # ── 做功分析 ───────────────────────────────────────────
    def _analyze_zuogong(self, chart, result, stems, day_master):
        """识别盲派做功方式：合用/制用/化用/生用 + 地支冲合。

        V2.2: 做功关系精确判定. 原逻辑"只要十神共存就触发"过于宽松(加入地支藏干后
        几乎所有做功方式都被触发). V2.2加入:
        1. 位置信息(柱索引0-3): 体用各自的位置
        2. 作用距离: 同柱(0)/相邻(1)/隔一位(2)/遥隔(3,不作用)
        3. 作用关系: 天干五合/地支六合/地支六冲/体克用(制)/体生用(生)/用生体(化)
        只有距离<=2且有明确作用关系的体用对才触发做功.
        """
        methods = []
        detail = []
        # 做功参与支收集（V3.0 功神/废神划分：功神=参与做功的字，废神/闲神=不参与）
        working_branches: Set[str] = set()
        target_branches: Set[str] = set()

        # ── 建立体用位置信息 ──
        # 格式: (stem, tg, pillar_idx, branch, is_hidden)
        # V3.6.7 修(可真值41例校对): 藏干过宽致 11 种方法全触发(凑数)。
        # 盲派口径: 六合"余气不单独论"(根因E已修), 但克/制/穿/刑类关系余气仍参与做功
        # (巳申合克=巳中丙合克申中庚, 庚=中气; 子未穿=未中丁穿子, 丁=余气)。
        # 故不剔除余气——只做"中气+中气/余气+余气 双弱配对"的做功效力降级,
        # 不直接跳过(避免 golden 锚点回归)。
        ti_positions = []
        yong_positions = []
        pillars = [
            (0, chart.year_pillar.heavenly_stem, chart.year_pillar.earthly_branch),
            (1, chart.month_pillar.heavenly_stem, chart.month_pillar.earthly_branch),
            (2, day_master, chart.day_pillar.earthly_branch),
            (3, chart.hour_pillar.heavenly_stem, chart.hour_pillar.earthly_branch),
        ]
        for pillar_idx, stem, branch in pillars:
            # 天干(透干)
            if pillar_idx == 2:
                # 日主本身是体(比肩)
                ti_positions.append((stem, '比肩', pillar_idx, branch, False))
            else:
                tg = ten_god(day_master, stem)
                if tg in TI_TEN_GODS:
                    ti_positions.append((stem, tg, pillar_idx, branch, False))
                elif tg in YONG_TEN_GODS:
                    yong_positions.append((stem, tg, pillar_idx, branch, False))
            # 地支藏干(全部纳入, 克/穿/刑类余气仍做功; 六合类由根因E主气约束)
            for hidden_stem, _pos in BRANCH_HIDDEN_STEMS.get(branch, []):
                tg = ten_god(day_master, hidden_stem)
                if tg in TI_TEN_GODS:
                    ti_positions.append((hidden_stem, tg, pillar_idx, branch, True))
                elif tg in YONG_TEN_GODS:
                    yong_positions.append((hidden_stem, tg, pillar_idx, branch, True))

        # ── 作用关系判定 ──
        # 记录已触发的做功方式(避免重复)
        triggered = set()
        # V3.1: 做功归因（与 methods/detail 一一对应）
        attributions = []
        # 根因D：谁在做功三维度（与 methods 一一对应）
        actor_dims = []

        all_branches_list = [p[2] for p in pillars]
        for ti in ti_positions:
            ti_stem, ti_tg, ti_idx, ti_branch, ti_hidden = ti
            for yong in yong_positions:
                yong_stem, yong_tg, yong_idx, yong_branch, yong_hidden = yong

                # 作用距离
                distance = abs(ti_idx - yong_idx)
                if distance > 2:
                    continue  # 遥隔不作用

                # 作用关系判定
                relation = None
                # 天干五合(仅天干之间)
                if not ti_hidden and not yong_hidden:
                    if (ti_stem, yong_stem) in STEM_HE or (yong_stem, ti_stem) in STEM_HE:
                        relation = "he"
                # 统一地支关系解析层（六合>冲>穿>三刑(三字全)>破>半合>拱；仅支藏干之间）
                # 根因E修复：同一对支不再多处独立判定（巳申=合/刑/破、寅巳=穿/刑、未戌=刑/破
                # 此前做功层判刑、禄神判定判穿、配偶宫判合绊——三处结论矛盾）
                if relation is None and ti_branch != yong_branch and ti_hidden and yong_hidden:
                    _rel = resolve_branch_relation(ti_branch, yong_branch, all_branches_list)
                    if _rel == "liuhe":
                        # 根因E修复：地支六合以两支主气为代表（盲派"巳申合克"=巳丙合克申庚）
                        # 余气藏干不单独论合——否则巳申合同时判出财制印(丙庚)+劫财合官(壬戊)
                        # 双重结论矛盾（金融巨头被误判官被劫）。劫财合官=申主气庚
                        # =劫财, 主气约束下仍正确触发。
                        _ti_master = BRANCH_HIDDEN_STEMS[ti_branch][0][0]
                        _yo_master = BRANCH_HIDDEN_STEMS[yong_branch][0][0]
                        if ti_stem != _ti_master or yong_stem != _yo_master:
                            continue   # 余气不参与六合做功
                        _ti_el_h = _branch_element(ti_branch)
                        _yo_el_h = _branch_element(yong_branch)
                        if ti_tg == "劫财" and yong_tg in GROUP_GUAN:
                            # 盲派"巳申合克"合为先：官与劫财合=官被劫财合走=非我所有（做负功）
                            # 不是"官杀制比劫"（那是纯克关系）——合克本质是合, 合走非制住
                            relation = "liuhe"   # 保持合, 走合功分支劫财合官 NEGATIVE
                        elif CONTROLS.get(_ti_el_h) == _yo_el_h:
                            relation = "ke_ti_yong"   # 合克：体克用
                        elif CONTROLS.get(_yo_el_h) == _ti_el_h:
                            relation = "ke_yong_ti"   # 合克：用克体
                        else:
                            relation = "liuhe"
                    elif _rel in ("chong", "xing", "chuan", "po", "banhe", "gong"):
                        relation = _rel
                # 五行关系
                ti_el = STEM_ELEMENT[ti_stem]
                yong_el = STEM_ELEMENT[yong_stem]
                if relation is None and CONTROLS.get(ti_el) == yong_el:
                    relation = "ke_ti_yong"  # 体克用(制用)
                if relation is None and CONTROLS.get(yong_el) == ti_el:
                    relation = "ke_yong_ti"  # V2.3: 用克体(财制印、官杀制比劫)
                if relation is None and GENERATES.get(ti_el) == yong_el:
                    relation = "sheng_ti_yong"  # 体生用(生用)
                if relation is None and GENERATES.get(yong_el) == ti_el:
                    relation = "sheng_yong_ti"  # 用生体(化用)

                if relation is None:
                    continue

                # ── 根据十神类型+作用关系判定做功方式 ──
                method = None
                method_detail = None
                # V2.3: 做功主体判定 — 体在主位(日时,idx2-3)还是宾位(年月,idx0-1)
                # 盲派核心: 主位做功=为我所用, 宾位做功=非我所有(效力打折)
                # V3.6.6 修(可真值41例校对): 体用位置归属以"所坐之柱"为准, 非字本身。
                # 藏干位置=所坐支所在柱: 日支藏干=日柱=主位(idx2), 时支藏干=时柱=主位(idx3),
                # 年支藏干=年柱=宾位(idx0), 月支藏干=月柱=宾位(idx1)。
                # 原以"字本身所在柱索引"判主宾, 致 癸卯丁巳丁巳壬寅(年支卯藏丁比肩制庚财)
                # 被判主位比劫制财=破财, 实际丁坐年柱=宾位比肩, 不构成主位夺财。
                # 藏干 idx 已等于所坐柱 idx(ti_positions 建列时 pillar_idx 正确), 直接用即可。
                ti_in_main = ti_idx >= 2  # 日时为主位(藏干 idx 已=所坐柱 idx)
                yong_in_main = yong_idx >= 2
                # 根因D：谁在做功三维度（日主亲自>禄身>主位借力>宾位）——纯枚举非评分
                # 段氏"体=日主/比肩(禄)/印/食伤"：日主亲自=最有力, 禄身=日主化身,
                # 主位借力=我之工具, 宾位=他作嫁
                if ti_stem == day_master:
                    actor_dim = "SELF_DIRECT"
                elif ti_branch == chart.day_pillar.earthly_branch:
                    actor_dim = "LU_SELF"
                elif ti_idx >= 2:
                    actor_dim = "TOOL_ASSISTED"
                else:
                    actor_dim = "OTHER"
                # 主体获取宾位用(体在主、用在宾)=能获取外界财官, 做功效率高
                ti_gets_yong = ti_in_main and not yong_in_main

                # ① 合功: 合的对象是用(财/官) → 得财/得权
                # V3.6.6 修(可真值41例校对): 合绊与合功的归因区分。
                # 合官/合财(天干五合或地支六合) 若"紧贴且双方有根气"=合绊(互绊失性),
                # 做功效力被绑住——原判一律 EFFECTIVE(主位)/INEFFECTIVE(宾位),
                # 致 癸卯丁巳丁巳壬寅(丁壬合=官星被合绊)误判得官、
                # 丁亥庚戌己巳庚午(庚甲合=官被合绊)误判取官。
                # 合绊=做功被绑, 非"得用", 归 INEFFECTIVE(效力打折), 但结构事实仍记录。
                # 非合绊的合(有根气不足/非紧贴)=正常合功, 维持原 EFFECTIVE/INEFFECTIVE。
                if relation in ("he", "liuhe") and yong_tg in YONG_TEN_GODS:
                    if ti_tg == "劫财" and yong_tg in GROUP_GUAN:
                        # 根因C修复：劫财合官=官被劫财合走=非我所有（盲派原书
                        # "官星被劫财合去→非我所有、做功无效"；官贵章）
                        # 劫财≠日主, 此合非日主参与=做负功（申庚劫财合巳丙官）
                        method = "劫财合官"
                        method_detail = f"{'天干五合' if relation=='he' else '地支六合'}: {ti_stem}(劫财)合{yong_stem}({yong_tg}), 距{distance}{'[宾位]' if not ti_in_main else ''}=官被劫走非我所有"
                        attribution = ZuoGongAttribution["NEGATIVE"]
                    else:
                        method = f"合{yong_tg}"
                        # V3.6.6: 紧贴+有根气=合绊(互绊失性)→ INEFFECTIVE(做功被绑)
                        _is_tight = distance <= 1
                        _ti_root_el = STEM_ELEMENT[ti_stem]
                        _yo_root_el = STEM_ELEMENT[yong_stem]
                        _ti_has_root = any(
                            b != ti_branch and any(STEM_ELEMENT[h] == _ti_root_el
                                                  for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
                            for b in all_branches_list
                        )
                        _yo_has_root = any(
                            b != yong_branch and any(STEM_ELEMENT[h] == _yo_root_el
                                                    for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
                            for b in all_branches_list
                        )
                        _is_he_ban = _is_tight and (_ti_has_root or _yo_has_root)
                        if _is_he_ban:
                            attribution = ZuoGongAttribution["INEFFECTIVE"]
                            method_detail = f"{'天干五合' if relation=='he' else '地支六合'}: {ti_stem}({ti_tg})合{yong_stem}({yong_tg}), 距{distance}[合绊=互绊失性, 做功被绑]"
                        elif ti_in_main:
                            attribution = ZuoGongAttribution["EFFECTIVE"]
                            method_detail = f"{'天干五合' if relation=='he' else '地支六合'}: {ti_stem}({ti_tg})合{yong_stem}({yong_tg}), 距{distance}[主取宾]"
                        else:
                            attribution = ZuoGongAttribution["INEFFECTIVE"]
                            method_detail = f"{'天干五合' if relation=='he' else '地支六合'}: {ti_stem}({ti_tg})合{yong_stem}({yong_tg}), 距{distance}[宾做功]"
                # ①b V2.4: 穿害做功 — 穿比冲更狠, 背后偷袭
                # V3.6 修(可真值41例校对): 穿官细分——穿的是官库支(墓库)=去官得权(制官语境),
                # 穿官星本体之支(非墓库)=官根受损。原判"穿官一律 DAMAGED"过宽,
                # 致"戌运当官升职"(穿官库去官得权)误判官贵受损。
                elif relation == "chuan" and ti_tg in TI_TEN_GODS and yong_tg in YONG_TEN_GODS:
                    if yong_tg in GROUP_GUAN:
                        if yong_branch in MU_KU:
                            method = f"穿制{yong_tg}"
                            method_detail = f"地支六穿: {ti_branch}({ti_tg})穿{yong_branch}({yong_tg}), 距{distance}[穿官库=去官得权]"
                            attribution = (ZuoGongAttribution["EFFECTIVE"] if ti_in_main
                                           else ZuoGongAttribution["INEFFECTIVE"])
                        else:
                            method = f"穿损{yong_tg}"
                            method_detail = f"地支六穿: {ti_branch}({ti_tg})穿{yong_branch}({yong_tg}), 距{distance}=损官做负功(官根受损)"
                            attribution = ZuoGongAttribution["NEGATIVE"]
                    else:
                        method = f"穿制{yong_tg}"
                        method_detail = f"地支六穿: {ti_branch}({ti_tg})穿{yong_branch}({yong_tg}), 距{distance}{'[主取宾]' if ti_gets_yong else '[宾做功]' if not ti_in_main else ''}"
                        attribution = (ZuoGongAttribution["EFFECTIVE"] if ti_in_main
                                       else ZuoGongAttribution["INEFFECTIVE"])
                # ①c V3.0: 刑做功（原书做功六方式之一；规则§13 刑制）
                # 刑发生在体用之字间即做功方式；detail 注明是否带五行制（刑+克=刑制）
                elif relation == "xing" and ti_tg in TI_TEN_GODS and yong_tg in YONG_TEN_GODS:
                    ti_el2 = STEM_ELEMENT[ti_stem]
                    yong_el2 = STEM_ELEMENT[yong_stem]
                    xing_with_control = CONTROLS.get(ti_el2) == yong_el2
                    method = f"刑制{yong_tg}" if xing_with_control else f"刑{yong_tg}"
                    method_detail = f"地支三刑: {ti_branch}({ti_tg})刑{yong_branch}({yong_tg}), 距{distance}{'+五行制' if xing_with_control else '(互动无制)'}{'[主取宾]' if ti_gets_yong else ''}"
                    attribution = (ZuoGongAttribution["EFFECTIVE"] if ti_in_main
                                   else ZuoGongAttribution["INEFFECTIVE"])
                # ② 食伤制杀: 体是食伤, 用是七杀, 体克用
                elif relation == "ke_ti_yong" and ti_tg in GROUP_SHI and yong_tg == "七杀":
                    method = "食伤制杀"
                    method_detail = f"{ti_stem}({ti_tg})制{yong_stem}({yong_tg}), 距{distance}{'[主取宾]' if ti_gets_yong else ''}"
                    attribution = (ZuoGongAttribution["EFFECTIVE"] if ti_in_main
                                   else ZuoGongAttribution["INEFFECTIVE"])
                # ③ 伤官制官: 体是伤官, 用是正官, 体克用
                elif relation == "ke_ti_yong" and ti_tg == "伤官" and yong_tg == "正官":
                    method = "伤官制官"
                    method_detail = f"{ti_stem}({ti_tg})制{yong_stem}({yong_tg}), 距{distance}{'[主取宾]' if ti_gets_yong else ''}"
                    attribution = (ZuoGongAttribution["EFFECTIVE"] if ti_in_main
                                   else ZuoGongAttribution["INEFFECTIVE"])
                # ④ 比劫制财: 体是比劫, 用是财, 体克用
                # V3.6.6 修(可真值41例校对): 主宾归属判据。
                # 体比劫在主位(日支/时柱)制财=本人把财夺散(破财, NEGATIVE);
                # 体比劫在宾位(年/月)制财=制住同伙, 财归我(EFFECTIVE, 取财成立)。
                # 癸卯丁巳丁巳壬寅: 日主丁, 日支巳藏丙=劫财(主位);
                # 月干丁比肩(宾位)制庚正财=宾位比劫被制=财归我, 但主位劫财(巳丙)夺财并存。
                # V3.6.9㊻c 修(㊻b全量94%过宽溯源): 日主透干本身(日柱干, idx=2 非藏干)在
                # ti_positions 中记为"比肩", 导致"日主制财"被误标为"比劫制财"(219例NEGATIVE/
                # 全量234=94%过宽)。盲派"比劫制财"专指比肩/劫财"他字"克财, 非日主身制财
                # (身制财=正常取财做功, 归合财/食伤生财/财制印等, 非比劫制财)。
                # 修后: 排除日主透干本身(日柱干, ti_idx==2 且非藏干)作为"比劫"体,
                # 只认非日主比肩/劫财他字(年/月柱干, 或藏干比劫)克财=比劫制财。
                elif (relation == "ke_ti_yong" and ti_tg in GROUP_BI and yong_tg in GROUP_CAI
                      and not (ti_idx == 2 and not ti_hidden)):
                    method = "比劫制财"
                    if ti_in_main:
                        attribution = ZuoGongAttribution["NEGATIVE"]
                        method_detail = f"{ti_stem}({ti_tg})制{yong_stem}({yong_tg}), 距{distance}[主位比劫夺财=破财]"
                    else:
                        attribution = ZuoGongAttribution["EFFECTIVE"]
                        method_detail = f"{ti_stem}({ti_tg})制{yong_stem}({yong_tg}), 距{distance}[宾位比劫被制=财归我]"
                # ⑤ 财制印: V2.3 fix — 用是财, 体是印, 用克体(原写反为体克用,财属用不属体永不触发)
                # 盲派视"财制印"层次极高: 财星主动制合印星(资源/权力), 制得干净则大贵
                elif relation == "ke_yong_ti" and yong_tg in GROUP_CAI and ti_tg in GROUP_YIN:
                    method = "财制印"
                    method_detail = f"{yong_stem}({yong_tg})制{ti_stem}({ti_tg}), 距{distance}{'[用克体]' if not ti_in_main else ''}"
                    attribution = (ZuoGongAttribution["EFFECTIVE"] if (ti_in_main or yong_in_main)
                                   else ZuoGongAttribution["INEFFECTIVE"])
                # ⑤b 官杀制比劫: 用是官杀, 体是比劫, 用克体
                # V3.6.9㊻e 修(㊻b全量93%过宽溯源): 142/219例"被制体"(比劫)=日主透干本身
                # (日柱干, ti_idx==2非藏干), 即"官杀制日主本身"=正常官制身/杀制身结构事实,
                # 非盲派"官杀制比劫"(官杀制比劫他字=制住争比劫=官权做功)口径.
                # 修后: 排除日主透干本身(ti_idx==2且非藏干)作为"比劫体",
                # 只认官杀制非日主比肩/劫财他字(年月柱干比肩/劫财, 或日时支藏干比劫).
                elif (relation == "ke_yong_ti" and yong_tg in GROUP_GUAN and ti_tg in GROUP_BI
                      and not (ti_idx == 2 and not ti_hidden)):
                    method = "官杀制比劫"
                    method_detail = f"{yong_stem}({yong_tg})制{ti_stem}({ti_tg}), 距{distance}"
                    attribution = (ZuoGongAttribution["EFFECTIVE"] if (ti_in_main or yong_in_main)
                                   else ZuoGongAttribution["INEFFECTIVE"])
                # ⑤c V3.0: 财制比劫（原书比肩去财局之二：财旺制比劫, 比劫当财看=换象）
                # 段建业原书原文: "财制比劫局……比肩劫财当财看" → 解锁 VERIFY-BLIND-022 换象
                elif relation == "ke_yong_ti" and yong_tg in GROUP_CAI and ti_tg in GROUP_BI:
                    method = "财制比劫"
                    method_detail = f"{yong_stem}({yong_tg})制{ti_stem}({ti_tg}), 距{distance}[换象: 比劫当财看]"
                    attribution = (ZuoGongAttribution["EFFECTIVE"] if (ti_in_main or yong_in_main)
                                   else ZuoGongAttribution["INEFFECTIVE"])
                    result.image_substitution = "HUAN_XIANG_BIJIE_DANG_CAI"
                # ⑥ 印化官杀: 体是印, 用是官杀, 用生体
                # V3.6.9⑮ 主位口径(原书"官中有印=印主权力"): 印(体)落主位(日/时)=制官 EFFECTIVE,
                # 印落宾位(年/月)=官泄外人 INEFFECTIVE。沿用既有 ti_in_main 判据。
                elif relation == "sheng_yong_ti" and ti_tg in GROUP_YIN and yong_tg in GROUP_GUAN:
                    method = "印化官杀"
                    method_detail = f"{yong_stem}({yong_tg})生{ti_stem}({ti_tg}), 距{distance}{'[主位印化官杀=制官]' if ti_in_main else '[宾位印=官泄外,不制]'}"
                    attribution = (ZuoGongAttribution["EFFECTIVE"] if ti_in_main
                                   else ZuoGongAttribution["INEFFECTIVE"])
                # ⑦ 食伤生财: 体是食伤, 用是财, 体生用
                elif relation == "sheng_ti_yong" and ti_tg in GROUP_SHI and yong_tg in GROUP_CAI:
                    method = "食伤生财"
                    method_detail = f"{ti_stem}({ti_tg})生{yong_stem}({yong_tg}), 距{distance}{'[主取宾]' if ti_gets_yong else ''}"
                    attribution = (ZuoGongAttribution["EFFECTIVE"] if ti_in_main
                                   else ZuoGongAttribution["INEFFECTIVE"])
                else:
                    attribution = ZuoGongAttribution["NEUTRAL"]

                if method and method not in triggered:
                    triggered.add(method)
                    methods.append(method)
                    detail.append(method_detail)
                    attributions.append(attribution)
                    actor_dims.append(actor_dim)
                    # 功神/目标收集（V3.0）：参与做功的体支=功神候选, 用支=目标候选
                    working_branches.add(ti_branch)
                    target_branches.add(yong_branch)
                elif method:
                    # V3.4.3 归因升级（盲派核心"谁在做功/是否为我所用"）：
                    # 同一做功方式存在多个配对时，首个（可能宾位）抢注会导致
                    # 主位 EFFECTIVE 版本被丢弃（日支申制时支巳七杀=主位制杀，
                    # 被"月未丁官制年支申比肩(宾位)"抢注成 INEFFECTIVE；
                    # 日支巳财制年支申印=主位财制印，被"月未丁财制年支申印"
                    # 抢注成 INEFFECTIVE）。
                    # V3.6.6 修(可真值41例校对): 主位版本覆盖宾位版本(主位优先),
                    # 同主宾层级保留对本人最不利归因(NEGATIVE>INEFFECTIVE>EFFECTIVE)。
                    # 原 V3.6.5 "保留最有利归因"(EFFECTIVE>NEGATIVE>NEUTRAL>INEFFECTIVE)
                    # 致 癸卯丁巳丁巳壬寅(主位比劫制财 NEGATIVE) 被宾位版本抢注后丢弃,
                    # 破财风险漏判。
                    _mi = methods.index(method)
                    _PRIORITY = {
                        ZuoGongAttribution["NEGATIVE"]: 3,
                        ZuoGongAttribution["INEFFECTIVE"]: 2,
                        ZuoGongAttribution["EFFECTIVE"]: 1,
                        ZuoGongAttribution["NEUTRAL"]: 0,
                    }
                    _cur_is_main = "[主位]" in detail[_mi]
                    _new_is_main = "[主位]" in method_detail
                    if _new_is_main and not _cur_is_main:
                        # 主位版本覆盖宾位版本
                        attributions[_mi] = attribution
                        detail[_mi] = method_detail
                        working_branches.add(ti_branch)
                        target_branches.add(yong_branch)
                    elif _PRIORITY.get(attribution, 0) > _PRIORITY.get(attributions[_mi], 0):
                        # 同主宾层级, 保留对本人最不利归因
                        attributions[_mi] = attribution
                        detail[_mi] = method_detail
                        working_branches.add(ti_branch)
                        target_branches.add(yong_branch)

        # ⑦b V3.6.9 食伤当财(比劫生食伤, 体体配对): 原书 L1962 "伤食当财: 八字无财星,
        # 却有伤食星, 以伤食当财富看"。比劫(手)生食伤(面)=手艺活赚钱
        # (真值 壬子癸卯癸卯壬子: 比劫手, 卯曲面, 拉面馆生意很好)。
        # 食伤属体不在用侧, 体×yong 循环不覆盖体体配对, 需独立遍历体-体。
        # 条件: 原局无用侧财星(食伤才代财, 有真财走食伤生财)。
        # V3.6.9⑨ 归因收窄: 比劫(手)需主位(日/时柱, 本人手)生食伤才 EFFECTIVE,
        # 宾位比劫生食伤=非我手艺 → INEFFECTIVE。修 壬子癸卯癸卯壬子
        # (比劫手卯曲面生意很好) 原判 INEFFECTIVE 与原书"生意很好"矛盾。
        has_real_cai_yong = any(yong_tg in GROUP_CAI for (_s, yong_tg, _i, _b, _h) in yong_positions)
        if not has_real_cai_yong:
            # V3.6.9⑨ 食伤当财体体配对遍历: 收集所有比劫生食伤配对, 取归因最强
            # (主位手>EFFECTIVE, 宾位手>INEFFECTIVE)。先宾后主遍历时, 主位对归因
            # 需覆盖宾位对(真值 壬子癸卯癸卯壬子: 年壬手是宾, 时壬手是主, 取主)。
            bi_shi_pairs = []  # (ti, yong, ti_in_main, ti_branch, yong_branch, distance)
            for ti in ti_positions:
                ti_stem, ti_tg, ti_idx, ti_branch, ti_hidden = ti
                if ti_tg not in GROUP_BI:
                    continue
                for yong in ti_positions:
                    yong_stem, yong_tg, yong_idx, yong_branch, yong_hidden = yong
                    if yong_idx < ti_idx:
                        continue
                    distance = abs(ti_idx - yong_idx)
                    if distance > 2:
                        continue
                    if yong_tg not in GROUP_SHI:
                        continue
                    ti_el = STEM_ELEMENT[ti_stem]
                    yong_el = STEM_ELEMENT[yong_stem]
                    if GENERATES.get(ti_el) == yong_el:
                        bi_shi_pairs.append((ti_stem, ti_tg, ti_idx, ti_branch,
                                              yong_stem, yong_tg, yong_branch, distance))
            if bi_shi_pairs:
                # 取归因最强对: 主位手(idx>=2)优先, 同主位取日支=LU_SELF, 其次时柱
                main_pairs = [p for p in bi_shi_pairs if p[2] >= 2]
                if main_pairs:
                    # 日支(LU_SELF) > 时柱(TOOL_ASSISTED)
                    day_br = chart.day_pillar.earthly_branch
                    lu_self = [p for p in main_pairs if p[3] == day_br]
                    chosen = (lu_self[0] if lu_self else main_pairs[0])
                else:
                    chosen = bi_shi_pairs[0]
                (ti_stem, ti_tg, ti_idx, ti_branch,
                 yong_stem, yong_tg, yong_branch, distance) = chosen
                ti_in_main = ti_idx >= 2
                if ti_branch == chart.day_pillar.earthly_branch:
                    _actor_dim_bi = "LU_SELF"
                elif ti_in_main:
                    _actor_dim_bi = "TOOL_ASSISTED"
                else:
                    _actor_dim_bi = "OTHER"
                method = "比劫生食伤(食伤当财)"
                method_detail = (f"{ti_stem}({ti_tg})生{yong_stem}({yong_tg}), "
                                 f"距{distance}[食伤当财]")
                attribution = (ZuoGongAttribution["EFFECTIVE"] if ti_in_main
                               else ZuoGongAttribution["INEFFECTIVE"])
                if method not in triggered:
                    triggered.add(method)
                    methods.append(method)
                    detail.append(method_detail)
                    attributions.append(attribution)
                    actor_dims.append(_actor_dim_bi)
                    working_branches.add(ti_branch)
                    target_branches.add(yong_branch)

        # ⑧ 地支三合(独立判定, 不依赖体用对)
        all_branch_set = {p[2] for p in pillars}
        for sanhe_key, sanhe_set in BRANCH_SANHE.items():
            if sanhe_set.issubset(all_branch_set):
                method = "地支三合"
                if method not in triggered:
                    triggered.add(method)
                    methods.append(method)
                    detail.append(f"地支三合: {sanhe_key}")
                    # 三合局有主位支参与=为我所用；否则宾位局=非我所有
                    has_main_in_sanhe = any(
                        p[2] in sanhe_set and p[0] >= 2 for p in pillars
                    )
                    attributions.append(ZuoGongAttribution["EFFECTIVE"] if has_main_in_sanhe
                                        else ZuoGongAttribution["INEFFECTIVE"])
                    actor_dims.append(actor_dim)

        # ⑨ V2.4: 墓库收放 — 辰戌丑未墓库, 闭库收物=财富聚拢, 冲库开库=财官出来
        # 墓喜冲: 库不开则财官无用, 一冲则发
        all_branches_list = [p[2] for p in pillars]
        muku_branches = [b for b in all_branches_list if b in MU_KU]
        for muku_b in muku_branches:
            muku_element = MU_KU[muku_b]
            muku_idx = all_branches_list.index(muku_b)
            muku_in_main = muku_idx >= 2
            # 检查墓库是否被冲(辰戌冲、丑未冲) — 冲则开库
            chong_target = BRANCH_CHONG.get(muku_b)
            is_chonged = chong_target in all_branches_list

            # 检查该五行是否在其他支中有根(被墓库收)
            element_stems = {"WOOD": ["JIA","YI"], "FIRE": ["BING","DING"],
                              "EARTH": ["WU","JI"], "METAL": ["GENG","XIN"], "WATER": ["REN","GUI"]}
            target_stems = element_stems.get(muku_element, [])
            has_root_elsewhere = False
            for b in all_branches_list:
                if b == muku_b:
                    continue
                for hidden_stem, _pos in BRANCH_HIDDEN_STEMS.get(b, []):
                    if hidden_stem in target_stems:
                        has_root_elsewhere = True
                        break
                if has_root_elsewhere:
                    break

            if is_chonged:
                # 冲库开库: 财官出来, 做功(墓喜冲不冲不发)
                # V3.1 归因修正: 谁冲谁=冲者主动。主位冲开宾位库=主取宾(为我所用)
                # 段建业原书原文: "以我宫未土杀库,冲制宾位丑土财库"=主位未冲开宾位丑=EFFECTIVE
                method = "冲开墓库"
                if method not in triggered:
                    triggered.add(method)
                    methods.append(method)
                    chong_source_idx = (all_branches_list.index(chong_target)
                                        if chong_target in all_branches_list else -1)
                    chong_source_main = chong_source_idx >= 2
                    detail.append(f"冲开{muku_b}({muku_element}墓): {chong_target}冲{muku_b}, 开库出财官{'[主冲宾]' if chong_source_main and not muku_in_main else '[宾冲主]' if not chong_source_main and muku_in_main else ''}")
                    attributions.append(ZuoGongAttribution["EFFECTIVE"] if (muku_in_main or chong_source_main)
                                        else ZuoGongAttribution["INEFFECTIVE"])
                    actor_dims.append(actor_dim)
            elif has_root_elsewhere:
                # 闭库收物: 墓库收该五行=财富聚拢, 做功
                method = "墓库收物"
                if method not in triggered:
                    triggered.add(method)
                    methods.append(method)
                    detail.append(f"闭库收{muku_element}: {muku_b}墓库收{muku_element}气=财富聚拢{'[主位]' if muku_in_main else '[宾位]'}")
                    attributions.append(ZuoGongAttribution["EFFECTIVE"] if muku_in_main
                                        else ZuoGongAttribution["INEFFECTIVE"])
                    actor_dims.append(actor_dim)

        # ⑨b V3.6.9㊻y ch8 西瓜皮肉"合财入库"独立方法:
        # 原书ch8"取财实质: 日主合到财, 看合的是皮[财库外]还是肉[财实质/库中].
        # 吃到肉=富, 吃皮丢肉=穷". ㊻w确证CUI_REN全量0命中, 根因=做功层无独立"合财入库"方法,
        # 原he_fin_ku关键词含"冲开"与"冲开墓库"重叠误判. ㊻y修后:
        # 判据: 日主天干五合partner=财星(男财/女官杀换象当财, ㊻s image_substitution口径),
        #       partner所落柱位=主位(日/时), 且原局有财库支(丑戌藏干含财, 未辰次之)present
        #       → 合财入库=吃到财库(肉)=EFFECTIVE(主位合财入主位/宾位库).
        # 反例(吃皮丢肉): 日主合财但财库支不在局(财无库)=CHI_PI, 不触发本方法.
        CAI_TG_SET = set()
        # 男命财星=偏财/正财, 女命官杀换象当财(image_substitution HUAN_XIANG_GUANSHA_DANG_CAI)
        if chart.gender == "male":
            CAI_TG_SET = GROUP_CAI
        else:
            CAI_TG_SET = GROUP_CAI | GROUP_GUAN   # 女命官杀当财(㊻s换象口径)
        muku_has_cai_y = any(
            ten_god(day_master, h) in CAI_TG_SET
            for b in all_branches_list if b in ("CHOU","XU","CHEN","WEI")
            for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        if muku_has_cai_y:
            for pair in [("JIA","JI"),("YI","GENG"),("BING","XIN"),("DING","REN"),("WU","GUI")]:
                st, partner_st = pair
                if day_master not in (st, partner_st):
                    continue
                my_st = st if day_master == st else partner_st
                he_st = partner_st if day_master == st else st
                # 日主天干=财星? partner天干=财星?
                tg_my = ten_god(day_master, my_st)
                tg_he = ten_god(day_master, he_st)
                cai_partner_hit = tg_he in CAI_TG_SET
                if not cai_partner_hit:
                    continue
                # ㊻y6 修: 合财=日主(我)合财星=我做功取财, 不论财星落哪柱位都是我主动做功,
                # 盲派做功层口径: 日主合财=EFFECTIVE(我取财), 非"财星在宾位=INEFFECTIVE".
                # ㊻y 初建误用 partner_pos 判主宾, ㊻y5 溯源癸未乙卯甲子己巳(己落时柱)判 INEFFECTIVE,
                # ㊻y6 修后: 合财入库=日主身合财=我取财=EFFECTIVE.
                partner_pos = None
                for pos_idx, pp in enumerate(pillars):
                    if pp[0] == he_st:
                        partner_pos = pos_idx
                        break
                method = "合财入库"
                if method not in triggered:
                    triggered.add(method)
                    methods.append(method)
                    detail.append(
                        f"ch8合财入库(西瓜皮肉): 日主{day_master}合{he_st}"
                        f"({tg_he}=财星)"
                        f"{['年','月','日','时'][partner_pos] if partner_pos is not None else '?'}柱"
                        f"+财库支在局={'+'.join(b for b in all_branches_list if b in ('CHOU','XU','CHEN','WEI'))}"
                        f"=我合财吃到财库(肉)"
                    )
                    # ㊻y6: 日主身合财=我做功=EFFECTIVE(盲派做功层口径, 不论财星柱位)
                    attributions.append(ZuoGongAttribution["EFFECTIVE"])
                    actor_dims.append(actor_dim)
                break   # 一干一合即可, 不重复堆叠

        # ⑩ V2.5: 暗合 — 地支藏干之间的天干五合(如辰癸午丁暗合)
        # 盲派原书: 辰中癸水与午中丁火暗合=财富靠整合资源收拢资本
        # 只在体用对之间, 且非天干/地支明合时判定
        hidden_he_triggered = set()
        # 根因B修复：暗合边界收紧（盲派暗合=相邻支藏干五合, 如辰癸午丁紧邻）：
        #   ① 距离约束：限相邻柱(abs(idx差)<=1)，排除跨支遥合（巳-酉隔申不再暗合）
        #   ② 一支不两合：已与其他支六合的支不参与暗合（巳申合优先, 巳丙不再暗合酉辛）
        #      ——解决"官被劫财合走(ROBBED)"与"暗合资源整合"同支矛盾
        liuhe_locked = set()
        for b_a in all_branches_list:
            for b_b in all_branches_list:
                if b_a != b_b and BRANCH_LIUHE.get(b_a) == b_b:
                    liuhe_locked.add(b_a)
                    liuhe_locked.add(b_b)
        for b1_idx, b1 in enumerate(all_branches_list):
            b1_in_main = b1_idx >= 2
            if b1 in liuhe_locked:
                continue
            for b2_idx, b2 in enumerate(all_branches_list):
                if b1_idx >= b2_idx or b1 == b2:
                    continue
                if b2 in liuhe_locked:
                    continue
                if abs(b1_idx - b2_idx) > 1:
                    continue  # 暗合限相邻柱
                # 检查两藏干之间是否有天干五合(相邻支暗合)
                for h1, _p1 in BRANCH_HIDDEN_STEMS.get(b1, []):
                    for h2, _p2 in BRANCH_HIDDEN_STEMS.get(b2, []):
                        if (h1, h2) in STEM_HE or (h2, h1) in STEM_HE:
                            key = tuple(sorted([b1, b2]))
                            if key in hidden_he_triggered:
                                continue
                            hidden_he_triggered.add(key)
                            # 判定暗合的十神组合(以两藏干相对日主)
                            tg1 = ten_god(day_master, h1)
                            tg2 = ten_god(day_master, h2)
                            # 暗合取财/官为做功
                            if tg1 in YONG_TEN_GODS or tg2 in YONG_TEN_GODS:
                                in_main = b1_in_main or b2_idx >= 2
                                method = "暗合"
                                if method not in triggered:
                                    triggered.add(method)
                                    methods.append(method)
                                    detail.append(f"暗合: {b1}藏{h1}({tg1})合{b2}藏{h2}({tg2})={'资源整合' if in_main else '暗藏信息'}")
                                    attributions.append(ZuoGongAttribution["EFFECTIVE"] if in_main
                                                        else ZuoGongAttribution["INEFFECTIVE"])
                                    actor_dims.append(actor_dim)
                            break
                    else:
                        continue
                    break

        # ⑪ V2.5: 包局 — 多支同气包围一支异气(如三寅包一子)
        # 盲派包局（段建业原书佐证）: 三重寅木包一子水, 包局主贵, 体强包用得权
        # V3.1 修正（原书核证）：原判据"被包围者在主位"过松——
        # 申酉2支围未=比劫围库(争财), 非包局得权;
        # 原书包局=三寅包一子=体(比劫/禄)以强势(≥3支)包用(财官印)。
        # 判据: 同气支≥3(原书"三重"起算) 且 被包围者含财官印(用)
        branch_elems = {}
        for b_idx, b in enumerate(all_branches_list):
            el = _branch_element(b)  # V3.1 fix: 必须用支五行, 禁 STEM_ELEMENT(天干映射)查支
            branch_elems.setdefault(el, []).append(b)
        for el, bs in branch_elems.items():
            if len(bs) < 3:
                continue
            # 其他支(异五行)
            other_bs = [b for b in all_branches_list if b not in bs]
            if not other_bs:
                continue
            # 被包围者必须含用(财官印)——体强包用方得权
            for ob in other_bs:
                ob_tgs = [ten_god(day_master, h) for h, _p in BRANCH_HIDDEN_STEMS.get(ob, [])]
                if not any(t in YONG_TEN_GODS or t in GROUP_YIN for t in ob_tgs):
                    continue
                ob_idx = all_branches_list.index(ob)
                method = "包局"
                if method not in triggered:
                    triggered.add(method)
                    methods.append(method)
                    detail.append(f"包局: {len(bs)}个{el}支{bs}包围{ob}={('武力掌控权力' if len(bs)>=3 else '多方包围')}")
                    attributions.append(ZuoGongAttribution["EFFECTIVE"])
                    # 根因D修复：包局谁在包——包群含日支或日主禄支=日主化身亲临(LU_SELF)；
                    # 含主位支(日时)=主位借力(TOOL_ASSISTED)；全宾位=他作嫁(OTHER)。
                    # 禁止沿用主循环残留 actor_dim；禁止用 index() 查重复支(只回首个索引)。
                    _bs_set = set(bs)
                    if chart.day_pillar.earthly_branch in _bs_set:
                        _bao_dim = "LU_SELF"
                    elif road_branch(day_master) in _bs_set:
                        _bao_dim = "LU_SELF"   # 禄包=日主化身收权（甲禄在寅: 三寅包一子=禄包权）
                    elif any(i >= 2 for i, b in enumerate(all_branches_list) if b in _bs_set):
                        _bao_dim = "TOOL_ASSISTED"   # 包群含主位支=我之工具借力
                    else:
                        _bao_dim = "OTHER"
                    actor_dims.append(_bao_dim)
                    working_branches.update(bs)
                    target_branches.add(ob)
                break
            else:
                continue
            break

        # V3.6.9㉟ ch14 包围型(年时同字夹日): 年支==时支 夹日柱=包围型,
        # 原书 ch14 "年时同字夹日, 全包围=天子, 半包围=半个主子(不得善终)"。
        # 全包围: 年支==时支 且 月支 同五行=四面同字包围日柱(天子口径)。
        # 半包围: 年支==时支 但 月支 异五行=两面夹(半个主子口径)。
        # 这是独立于包局(多支同气包围)的结构事实——包局=体强(≥3支同气)包用,
        # 包围型=年时同字夹日的对称结构, 两者口径不同, 各自表达。
        year_b = chart.year_pillar.earthly_branch
        hour_b = chart.hour_pillar.earthly_branch
        month_b = chart.month_pillar.earthly_branch
        if year_b == hour_b and year_b != "":
            month_el = _branch_element(month_b)
            year_el = _branch_element(year_b)
            bao_type = "FULL" if month_el == year_el else "HALF"
            method = f"包围型_{bao_type}"
            if method not in triggered:
                triggered.add(method)
                methods.append(method)
                bao_desc = "全包围(年时月三支同气夹日)=天子口径" if bao_type == "FULL" else "半包围(年时同字夹日)=半个主子口径"
                detail.append(f"包围型: 年{year_b}时{hour_b}夹日柱{bao_desc}")
                attributions.append(ZuoGongAttribution["EFFECTIVE"])
                _bao2_dim = "LU_SELF" if year_b == road_branch(day_master) else "OTHER"
                actor_dims.append(_bao2_dim)
                working_branches.update({year_b, hour_b, month_b})

        # ⑫a V3.0: 印制食伤（制用结构五种之一，原书：印制食伤）
        # 印(体)制食伤(此结构下食伤为被制方=用侧)：印之五行克食伤之五行
        # （印→日主→食伤，故印克食伤恒成立；原书制用五种含印制食伤）
        # V3.1 fix: 优先取主位(日时)的印-食伤对；全宾位对才取(非我所有)
        yin_pairs = []
        for ti1 in ti_positions:
            if ti1[1] not in GROUP_YIN:
                continue
            for ti2 in ti_positions:
                if ti1[2] == ti2[2] and ti1[3] == ti2[3] and ti1[0] == ti2[0]:
                    continue  # 同一字
                if ti2[1] not in GROUP_SHI:
                    continue
                if abs(ti1[2] - ti2[2]) > 2:
                    continue
                el1 = STEM_ELEMENT[ti1[0]]
                el2 = STEM_ELEMENT[ti2[0]]
                if CONTROLS.get(el1) != el2:
                    continue
                yin_pairs.append((ti1, ti2))
        if yin_pairs:
            # 主位印优先（主位巳中庚印制宾位未中乙食=主位印制食伤，制用五种·印制食伤）
            yin_pairs.sort(key=lambda p: 0 if p[0][2] >= 2 else 1)
            ti1, ti2 = yin_pairs[0]
            method = "印制食伤"
            if method not in triggered:
                triggered.add(method)
                methods.append(method)
                detail.append(f"印制食伤: {ti1[0]}({ti1[1]})制{ti2[0]}({ti2[1]}), 距{abs(ti1[2]-ti2[2])}")
                working_branches.add(ti1[3])
                target_branches.add(ti2[3])
                attributions.append(ZuoGongAttribution["EFFECTIVE"] if ti1[2] >= 2
                                    else ZuoGongAttribution["INEFFECTIVE"])
                # V3.6.9㉒ 修: 旧版 actor_dims.append(actor_dim) 引用了本块未定义的 actor_dim
                # (只在 财制印/官杀制财 等前块 才 有 actor_dim 局部 变量), 印制食伤 触发 时
                # actor_dim 未 绑 定 → UnboundLocalError. 修后 本 块 自 算 actor_dim:
                #   主 位 印 (日/时)=我 制 用 → LU_SELF; 宾 位 印 (年/月)=非 我 制 → OTHER.
                actor_dims.append("LU_SELF" if ti1[2] >= 2 else "OTHER")

        # ⑫b V3.0: 食伤泄秀（生用结构②，原书：食伤泄秀一般不发大财）
        # 定义：食伤贴近日主（月干/时干透出）泄日主之气，只输出结构不判财
        # V3.6.9⑲ 扩(修真值"泄秀"8例缺口): 旧版仅 月/时 干 食伤 透 干 触 发,
        # 年 干 食伤 透 干 也 是 食伤 泄 日 主(原书"食伤 主 才 华, 透 干 则 泄 秀"),
        # 修后 年/月/时 干 食伤 透 干 均 触 发 食 伤 泄 秀(唯 日 干 不 算, 日 干 是 日 主 本 身)。
        for st_idx, (st_, tg_) in stems.items():
            if st_idx == 'day':
                continue
            if tg_ in GROUP_SHI:
                method = "食伤泄秀"
                if method not in triggered:
                    triggered.add(method)
                    methods.append(method)
                    detail.append(f"食伤泄秀: {st_}({tg_})在{st_idx}干贴身泄日主(一般不发大财)")
                    # 泄秀是日主自身之气外泄, 一律主位得气
                    attributions.append(ZuoGongAttribution["EFFECTIVE"])
                    actor_dims.append(actor_dim)

        # ⑫c V3.0: 势做功（原书口诀：有势又有功定是富贵翁；木成势制土坏金…）
        # 成势=某五行支≥3成党（段建业原书"局中木火有势"），势做功=势五行克其对象
        branch_el_count = Counter(_branch_element(b) for b in all_branches_list)
        for el, cnt in branch_el_count.items():
            if cnt < 3:
                continue
            controlled_el = CONTROLS.get(el)
            if controlled_el is None:
                continue
            if any(_branch_element(b) == controlled_el for b in all_branches_list):
                method = "势做功"
                if method not in triggered:
                    triggered.add(method)
                    methods.append(method)
                    detail.append(f"势做功: {el}成势({cnt}支)制{controlled_el}")
                    # 势中有主位支=我成势(为我所用)；纯宾位成势=非我所有
                    has_main = any(
                        all_branches_list.index(b) >= 2 for b in all_branches_list
                        if _branch_element(b) == el
                    )
                    attributions.append(ZuoGongAttribution["EFFECTIVE"] if has_main
                                        else ZuoGongAttribution["INEFFECTIVE"])
                    actor_dims.append(actor_dim)

        # ⑫ V2.5: 禄刃 — 禄神/羊刃特殊判定(身体、福报、自我意志)
        # 禄=福气身体, 刃=刀风险; 禄怕见绝更怕穿害; 禄合财=轻松赚钱, 禄克财=辛苦求财
        dm = day_master
        dm_lu = road_branch(dm)      # 日主禄位
        dm_ren = absolute_branch(dm)  # 日主帝旺(阳刃)位
        lu_in_chart = dm_lu in all_branches_list
        ren_in_chart = dm_ren in all_branches_list
        # 禄被穿害(六害) → 禄神受损, 身体/福报受损
        lu_chuaned = None
        if lu_in_chart:
            for other_b in all_branches_list:
                if other_b != dm_lu and BRANCH_CHUAN.get(dm_lu) == other_b:
                    lu_chuaned = other_b
                    break
        # 禄被冲 → 禄神破损(身体/福报受损, 原书"禄怕见冲, 禄破=伤身/失禄")
        lu_chonged = None
        if lu_in_chart:
            lu_chong_target = BRANCH_CHONG.get(dm_lu)
            if lu_chong_target in all_branches_list:
                lu_chonged = lu_chong_target
        # 禄合财/官 → 轻松求财/得权(原书"禄合财=轻松赚钱, 禄合官=得权")
        lu_he_cai_guan = None
        if lu_in_chart:
            lu_he_partner = BRANCH_LIUHE.get(dm_lu)
            if lu_he_partner and lu_he_partner in all_branches_list:
                for _hb, _hp in BRANCH_HIDDEN_STEMS.get(lu_he_partner, []):
                    _htg = ten_god(day_master, _hb)
                    if _htg in GROUP_CAI or _htg in GROUP_GUAN:
                        lu_he_cai_guan = lu_he_partner
                        break
        if lu_chuaned:
            method = "禄神受穿"
            if method not in triggered:
                triggered.add(method)
                methods.append(method)
                detail.append(f"禄神{dm_lu}被{lu_chuaned}穿害: 禄怕穿害, 身体/福报受损")
                # 禄=日主本身, 被穿=做负功(受损类)
                attributions.append(ZuoGongAttribution["NEGATIVE"])
                actor_dim = "LU_SELF"   # 禄=日主化身, 禄被穿=日主亲自受伤
                actor_dims.append(actor_dim)
        # 禄被冲 → 禄神破损(NEGATIVE, 原书"禄破=伤身/失禄", 禄怕冲)
        elif lu_chonged:
            method = "禄神受冲"
            if method not in triggered:
                triggered.add(method)
                methods.append(method)
                detail.append(f"禄神{dm_lu}被{lu_chonged}冲破: 禄破=身体/福报受损")
                attributions.append(ZuoGongAttribution["NEGATIVE"])
                actor_dim = "LU_SELF"
                actor_dims.append(actor_dim)
        # 禄合财/官 → 轻松求财/得权(EFFECTIVE, 原书"禄合财=轻松赚钱")
        elif lu_he_cai_guan:
            method = "禄合财官"
            if method not in triggered:
                triggered.add(method)
                methods.append(method)
                detail.append(f"禄神{dm_lu}合{lu_he_cai_guan}(财/官): 禄合财官=轻松求财/得权")
                lu_in_main = all_branches_list.index(dm_lu) >= 2
                attributions.append(ZuoGongAttribution["EFFECTIVE"] if lu_in_main
                                     else ZuoGongAttribution["INEFFECTIVE"])
                actor_dim = "LU_SELF" if lu_in_main else "OTHER"
                actor_dims.append(actor_dim)
        # 阳刃(帝旺)下坐财星或冲官 → 军警/运动员/高风险(刃=刀)
        elif ren_in_chart:
            method = "阳刃"
            if method not in triggered:
                triggered.add(method)
                methods.append(method)
                detail.append(f"阳刃在{dm_ren}: 刃=刀, 身体能力自我意志强{'[主位]' if dm_ren in all_branches_list[2:] else ''}")
                attributions.append(ZuoGongAttribution["EFFECTIVE"] if dm_ren in all_branches_list[2:]
                                    else ZuoGongAttribution["NEUTRAL"])
                actor_dim = "LU_SELF" if dm_ren in all_branches_list[2:] else "OTHER"  # 刃=日主化身(主位)/他刃(宾位)
                actor_dims.append(actor_dim)

        # ── ⑫d V3.6.9⑰ 枭神夺食（VERIFY-BLIND-037，原书"枭神夺食=子息/技艺受损"）──
        # 盲派: 枭神(偏印)克食神=枭神夺食, 主 子息 受损/技艺 受损/母 缘 薄。
        # 判据: 偏 印 present(透 干 或 藏 干) + 食 神 present(透 干 或 藏 干), 且
        #       偏 印 与 食 神 有 直接 克制 关系(偏 印 五行 克 食 神 五行, 印 → 日主 → 食伤 故 偏 印 克 食 神 恒成立)。
        # 主 宾 归 因: 偏 印 落 主 位(日/时)=为 我 夺 食 EFFECTIVE(伤 子息/技艺), 宾 位(年/月)=非 我 夺 INEFFECTIVE。
        _xiao_stems = [s for s in [chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
                                    chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem]
                       if ten_god(day_master, s) == "偏印"]
        _xiao_hidden = [h for b in [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                                     chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch]
                       for h, _pp in BRANCH_HIDDEN_STEMS.get(b, []) if ten_god(day_master, h) == "偏印"]
        _shi_stems = [s for s in [chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
                                   chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem]
                      if ten_god(day_master, s) == "食神"]
        _shi_hidden = [h for b in [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                                    chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch]
                       for h, _pp in BRANCH_HIDDEN_STEMS.get(b, []) if ten_god(day_master, h) == "食神"]
        if (_xiao_stems or _xiao_hidden) and (_shi_stems or _shi_hidden):
            method = "枭神夺食"
            if method not in triggered:
                triggered.add(method)
                methods.append(method)
                # 偏印主宾归因: 偏印在日干/时干或日支/时支藏干=主位 EFFECTIVE(伤子息); 年月=宾位 INEFFECTIVE
                _main_stems = {chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem}
                _main_branches = {chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch}
                _xiao_in_main = (
                    any(s in _main_stems for s in _xiao_stems)
                    or any(
                        ten_god(day_master, h) == "偏印"
                        for b in _main_branches
                        for h, _pp in BRANCH_HIDDEN_STEMS.get(b, [])
                    )
                )
                detail.append(f"枭神(偏印)夺食神: 子息/技艺受损{'[主位伤子]' if _xiao_in_main else '[宾位非我]'}")
                attributions.append(ZuoGongAttribution["EFFECTIVE"] if _xiao_in_main
                                     else ZuoGongAttribution["INEFFECTIVE"])
                actor_dims.append("LU_SELF" if _xiao_in_main else "OTHER")

        # ── ⑬ V3.2: 燥土脆金（VERIFY-BLIND-034，段氏理象学·相生反常）──
        # 诊断：V3.1 遗留域缺口——引擎把"土生金"一律按正生处理，
        #       未识别"燥土(未戌)不生金反脆金=制金"，财制印层次判不到位。
        # 原书（段氏理象学）："燥土不能生金，土燥，因土中含火，性燥，不能生金反脆金"；
        #   "如四柱无水，见未戌之燥土定主脆金；如四柱有水，虽见未戌之燥土，亦可生金"；
        #   "以未土脆金为最，只因为未中不藏金反藏火"。
        # 布尔规则（全部条件判定，零评分）：
        #   REQUIRED: 燥土支(未/戌)∈四柱
        #         AND 金干支(庚/辛/申/酉)∈四柱
        #         AND NOT (天干壬/癸 或 地支亥/子 任一见之)   # 四柱无水才脆金
        #   FORMATION: 燥土脆金 = 制金(非生金)；未>戌（未中不藏金反藏火）
        #   V3.2 修复：日主属金时脆金=脆自己(比劫)，非口诀"脆财星"场景
        #   -> REQUIRED 加 AND 日主五行 != 金
        day_master_not_metal = STEM_ELEMENT[day_master] != "METAL"
        has_dry_earth = any(b in DRY_EARTH_BRANCHES for b in all_branches_list)
        metal_stems_present = any(
            s in ('GENG', 'XIN') for s in [p[1] for p in pillars]
        )
        metal_branches_present = any(
            b in METAL_BRANCHES for b in all_branches_list
        )
        has_water_four = (
            any(s in WATER_STEMS for s in [p[1] for p in pillars])
            or any(b in WATER_BRANCHES for b in all_branches_list)
        )
        if (day_master_not_metal and has_dry_earth
                and (metal_stems_present or metal_branches_present)
                and not has_water_four):
            for de_b in [b for b in all_branches_list if b in DRY_EARTH_BRANCHES]:
                for metal_b in [b for b in all_branches_list
                                if b in METAL_BRANCHES or (b in all_branches_list
                                                           and any(h in ('GENG', 'XIN') for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])))]:
                    if de_b == metal_b:
                        continue
                    de_idx = all_branches_list.index(de_b)
                    mt_idx = all_branches_list.index(metal_b)
                    if abs(de_idx - mt_idx) > 2:
                        continue
                    method = "燥土脆金"
                    if method not in triggered:
                        triggered.add(method)
                        methods.append(method)
                        de_in_main = de_idx >= 2
                        detail.append(
                            f"燥土脆金: {de_b}(燥土)脆{metal_b}(金), 四柱无水见燥土定主脆金"
                            f"{'(未>戌: 未中不藏金反藏火)' if de_b=='WEI' else ''}"
                            f"{'[主位]' if de_in_main else '[宾位]'}"
                        )
                        attributions.append(ZuoGongAttribution["EFFECTIVE"] if de_in_main
                                            else ZuoGongAttribution["INEFFECTIVE"])
                        actor_dim = "TOOL_ASSISTED" if de_in_main else "OTHER"
                        actor_dims.append(actor_dim)
                        working_branches.add(de_b)
                        target_branches.add(metal_b)
                        result.dry_earth_brittle = "TRIGGERED"
                        result.rules_triggered.append("VERIFY-BLIND-034")
        else:
            result.dry_earth_brittle = ("NOT_TRIGGERED" if has_dry_earth
                                        else "NO_DRY_EARTH")

        # ── ⑭ V3.2: 合绊（VERIFY-BLIND-009 扩展，段氏理象学·地支六合 +
        #             盲派初级班讲义"有合先论合"）──
        # 诊断：WK-H-003 合绊在 V1-FINAL 已列为缺口；"三合互绊=
        #       合多为绊"未检出，合绊状态未参与做功归因。
        # 原书（段氏理象学）："六合之合，只要相邻都有合绊之意"；
        #   "命局中两个字紧贴且力量相当相合为绊…合绊也是一种做功(把对方手脚绑住)"；
        #   "有合先论合，无合论生克"；"再旺一合也绊住变弱了"（初级班讲义）。
        # 布尔规则：
        #   REQUIRED: 天干五合 或 地支六合 成立
        #         AND 双方相邻(距离<=1，原书"紧贴")
        #         AND 双方都有根气(力量相当，不满足化气条件) → 合绊(互绊失性)
        #   EFFECT: 合绊=一种做功(绑定对方)；绊住用神应凶，绊住忌神应吉；逢冲还原
        he_ban_seen = set()
        for ti_hb in ti_positions:
            for yo_hb in yong_positions:
                if abs(ti_hb[2] - yo_hb[2]) > 1:
                    continue  # 原书"紧贴"=相邻
                if ti_hb[2] == yo_hb[2]:
                    continue
                hb_relation = None
                # 天干五合（相邻天干）
                if not ti_hb[4] and not yo_hb[4]:
                    if (ti_hb[0], yo_hb[0]) in STEM_HE or (yo_hb[0], ti_hb[0]) in STEM_HE:
                        hb_relation = f"天干五合({ti_hb[0]}{yo_hb[0]})"
                # 地支六合（相邻地支）
                if hb_relation is None and ti_hb[3] != yo_hb[3]:
                    if BRANCH_LIUHE.get(ti_hb[3]) == yo_hb[3]:
                        hb_relation = f"地支六合({ti_hb[3]}{yo_hb[3]})"
                if hb_relation is None:
                    continue
                # 力量相当判据（布尔）：双方各有根气（藏干同五行支存在）
                ti_root_el = STEM_ELEMENT[ti_hb[0]]
                yo_root_el = STEM_ELEMENT[yo_hb[0]]
                ti_has_root = any(
                    b != ti_hb[3] and any(STEM_ELEMENT[h] == ti_root_el
                                          for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
                    for b in all_branches_list
                )
                yo_has_root = any(
                    b != yo_hb[3] and any(STEM_ELEMENT[h] == yo_root_el
                                          for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
                    for b in all_branches_list
                )
                ban_key = tuple(sorted([ti_hb[3], yo_hb[3]])) if '六合' in hb_relation \
                    else tuple(sorted([ti_hb[0], yo_hb[0]]))
                if ban_key in he_ban_seen:
                    continue
                he_ban_seen.add(ban_key)
                ban_str = f"合绊: {hb_relation}紧贴{'互绊失性' if (ti_has_root or yo_has_root) else '(无根之合)'}"
                result.he_ban_structures.append(ban_str)
                # 合绊=一种做功（绑住对方手脚），十神侧=绊住用神/忌神
                # V3.2 归因修复：主宾位判定——双方都在宾位=非我所有(INEFFECTIVE)
                hb_in_main = ti_hb[2] >= 2 or yo_hb[2] >= 2
                method = "合绊"
                if method not in triggered:
                    triggered.add(method)
                    methods.append(method)
                    detail.append(ban_str + ("[主位]" if hb_in_main else "[宾位]"))
                    attributions.append(ZuoGongAttribution["EFFECTIVE"] if hb_in_main
                                        else ZuoGongAttribution["INEFFECTIVE"])
                    actor_dim = ("LU_SELF" if ti_hb[3] == chart.day_pillar.earthly_branch
                                 else "TOOL_ASSISTED" if ti_hb[2] >= 2 else "OTHER")
                    actor_dims.append(actor_dim)
                    working_branches.add(ti_hb[3])
                    target_branches.add(yo_hb[3])
                    result.rules_triggered.append("VERIFY-BLIND-009-HEBAN")

        result.zuo_gong = len(methods) > 0
        result.zuo_gong_type = "+".join(methods) if methods else ""
        result.zuo_gong_methods = methods
        result.zuo_gong_detail = detail
        result.zuo_gong_attributions = attributions
        result.zuo_gong_actor_dimensions = actor_dims
        # V3.0: 功神/废神划分依据（参与做功的支=功神候选, 目标支=目标候选）
        result.zuo_gong_actors = working_branches
        result.zuo_gong_targets = target_branches
        # ㊻s122c ch3 五类神口径修正(㊻s122 过度收敛回退: 可真值 87.8→85.4/总方向 92→91):
        # "废神不参与做功"是"层次判定"口径(无效做功不参与"做功"=断层次), 非"触发方法清单"
        # 口径。ch1 做功断法看"触发了哪些方法+每个有效/无效", INEFFECTIVE=有象但非我所有
        # (他作嫁), 不是"不存在"。L7 各域(官域伤官制官/子域/事业行业)依赖"被触发方法",
        # 移出 INEFFECTIVE 致 L7 判空。故:
        #   zuo_gong_methods = 完整触发清单(EFFECTIVE+NEGATIVE+INEFFECTIVE, 供 L7 消费)
        #   zuo_gong_effective = 真做功清单(EFFECTIVE+NEGATIVE, 供 L4 效率/层次/区分度判定)
        #   zuo_gong_images = 他作嫁象(INEFFECTIVE, 仅取象参考, 不坐实断事)
        _eff_idx = [i for i, a in enumerate(attributions)
                    if a in (ZuoGongAttribution["EFFECTIVE"], ZuoGongAttribution["NEGATIVE"])]
        _img_idx = [i for i, a in enumerate(attributions)
                   if a == ZuoGongAttribution["INEFFECTIVE"]]
        result.zuo_gong_effective = [methods[i] for i in _eff_idx]
        result.zuo_gong_effective_detail = [detail[i] for i in _eff_idx]
        result.zuo_gong_images = [methods[i] for i in _img_idx]
        result.zuo_gong_image_detail = [detail[i] for i in _img_idx]

    # ── 做功强弱（WK-EFFICIENCY-001~005）────────────────────
    def _resolve_work_efficiency(self, chart, result: "BlindBaziResult") -> None:
        day_master = chart.day_master
        """做功强弱 = 古籍三判据 → 四档枚举。

        古籍原文（《盲派初级命理学》第二章·做功效率 p.20-25）：
          "做功效率高低的判断：看做功路径是否直接、看做功力量是否集中、
            看做功对象是否得力。"
        V3.1 修复（原书核证，段建业体系）：
          ① 主位得气：盲派核心"谁在做功、是否为我所用"——
             主位做功(日时)=为我所用(有效)；宾位做功(年月)=非我所有(他作嫁)。
             "劫财合官非我所有"→ 必须判无效做功，不得 MEDIUM（规则反证，非验证样本）。
          ② 力量集中：原判据 len(methods)<=1 写反（方法少≠集中）。
             正确=做功目标集中(目标支≤1) 或 单体吸收结构
             （闭库收物/冲开墓库/包局/势做功/暗合=一器收多，原书"收的力量极大"）。
          ③ 对象得力：制/开/收/包=得手；仅合/化/生=弱得手。
        全部结构判定，零数字化（BLIND-ARCH-006 / BLIND-G16）。
        """
        methods = result.zuo_gong_methods
        attrs = result.zuo_gong_attributions
        result.rules_triggered.append("WK-EFFICIENCY-001")

        if not methods:
            # WK-EFFICIENCY-002：路径/力量/对象全不满足 → 无效做功
            result.work_efficiency = WorkEfficiency.NONE.value
            result.structure_clarity = StructureClarity.CHAOTIC.value
            result.work_level = "POOR"
            result.undetermined_reasons.append(
                "无有效做功方法 → WORK_EFFICIENCY=NONE（古籍：无效做功=贫贱）"
            )
            return

        # V3.1 主位得气：主位参与做功=为我所用（盲派核心"谁在做功"）
        effective_methods = [m for m, a in zip(methods, attrs)
                             if a == ZuoGongAttribution["EFFECTIVE"]]
        ineffective_methods = [m for m, a in zip(methods, attrs)
                               if a == ZuoGongAttribution["INEFFECTIVE"]]
        negative_methods = [m for m, a in zip(methods, attrs)
                            if a == ZuoGongAttribution["NEGATIVE"]]

        if not effective_methods:
            # 主位零得气：全宾位做功=他作嫁（原书：满盘财官在宾位与日主无情=为他人作嫁）
            result.work_efficiency = WorkEfficiency.NONE.value
            result.structure_clarity = StructureClarity.CHAOTIC.value
            result.work_level = "POOR"
            result.undetermined_reasons.append(
                "主位无得气做功（宾位做功=%s 非我所有）→ WORK_EFFICIENCY=NONE"
                % ("/".join(ineffective_methods) if ineffective_methods else "无")
            )
            result.eff_path_direct = bool(effective_methods or ineffective_methods)
            result.eff_power_concentrated = False
            result.eff_target_effective = False
            return

        # 判据① 路径直接：做功方法存在且非遥隔（_analyze_zuogong 已按距离<=2 过滤）
        result.eff_path_direct = True

        # 判据② 力量集中：目标集中(目标支≤1) 或 单体吸收结构（一器收多=集中）
        # 段建业原书"辰库收水"：一个辰收满盘水=收的力量极大（集中）
        # 吸收结构=闭库收物/冲开墓库/包局/势做功（多对一或一对多=力量聚拢）；
        # 暗合=两字一对一整合, 不构成"收"的集中（暗合不可判集中）
        # V3.1 fix: 吸收结构只认主位得气(EFFECTIVE)的方法——
        # 宾位"闭库收物"是他人收物, 不得判集中（主宾有别）
        target_branches = set(result.zuo_gong_targets)
        absorb_structure = any(
            ('闭库收' in d or '冲开' in d or '包局' in d or '势做功' in d)
            for d, a in zip(result.zuo_gong_detail, attrs)
            if a == ZuoGongAttribution["EFFECTIVE"]
        )
        result.eff_power_concentrated = len(target_branches) <= 1 or absorb_structure

        # 判据③ 对象得力：有效做功方法含 制/开/收/包（得手）；仅合/化/生=弱
        result.eff_target_effective = any(
            ('制' in m or '开' in m or '收' in m or '包' in m)
            for m in effective_methods
        )
        weak_only = (not result.eff_target_effective and any(
            ('合' in m or '化' in m or '生' in m) for m in effective_methods
        ))

        # V3.2 效率联动 v3（文献特例制，其余保持 V3.1 基线）：
        #   降档: PARTIAL 且 有效制类制的是食伤(印制食伤)
        #     -> 文献"火燥土势制食神 克制效率不高"=MEDIUM
        #   升级: CLEAN + (集中或得力) + 换象成立(食伤当财/官杀当财)
        #     -> 文献"印制食伤干净=巨财"
        #   升级: CLEAN + (集中或得力) + 有效制官类(伤官制官/食伤制杀)
        #     -> 文献"制尽杀星得天下"
        #   升级: CLEAN + (集中或得力) + 主位财>=2(财重制净)
        #     -> 文献"过河拆桥：先取后用"
        #   不适用: 主位财轻=1 -> 不升级；卯戌合制财 -> 不降
        effective_methods_l = list(effective_methods)
        eff_control_shishang = any(
            a == ZuoGongAttribution["EFFECTIVE"]
            and ('印制食伤' in m or '制食伤' in m or '制伤官' in m)
            for m, a in zip(methods, attrs)
        )
        eff_control_guan = any(
            a == ZuoGongAttribution["EFFECTIVE"]
            and ('伤官制官' in m or '食伤制杀' in m or '制杀' in m or '制官' in m)
            for m, a in zip(methods, attrs)
        )
        # 主位财重（日时支藏干+透干财星 >=2）
        main_cai_count = 0
        for b in (chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch):
            for h, _p in BRANCH_HIDDEN_STEMS.get(b, []):
                if ten_god(day_master, h) in GROUP_CAI:
                    main_cai_count += 1
        for st_ in (chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem):
            if ten_god(day_master, st_) in GROUP_CAI:
                main_cai_count += 1
        main_cai_heavy = main_cai_count >= 2

        # 降档（3支火土势制食神不净=效率不高；无此势不降）
        branch_el_count_shu = {}
        for b_ in (chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                   chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch):
            el_ = _branch_element(b_)
            branch_el_count_shu[el_] = branch_el_count_shu.get(el_, 0) + 1
        # 火燥土势=火土合并>=3 且 EARTH>=2（午+戌戌=3 制申金食神；
        #   酉申申=金势不算；无火土势不算）
        has_shi_potential = (
            branch_el_count_shu.get("EARTH", 0)
            + branch_el_count_shu.get("FIRE", 0) >= 3
            and branch_el_count_shu.get("EARTH", 0) >= 2
        )
        # 降档(3支火土势制食神不净=效率不高; 无此势不降)
        if (result.control_completeness == "PARTIAL" and has_shi_potential
                and eff_control_shishang):
            result.work_efficiency = WorkEfficiency.MEDIUM.value
            result.structure_clarity = StructureClarity.PARTIALLY_CLEAR.value
            result.work_level = "MEDIUM_NOBLE"
            result.undetermined_reasons.append(
                "制食伤不净(PARTIAL)+印制食伤为有效做功：文献'克制效率不高'->MEDIUM"
            )
        # 升级（制净得用）
        elif (result.control_completeness == "CLEAN"
              and (result.eff_power_concentrated or result.eff_target_effective)
              and (result.image_substitution != "UNDETERMINED"
                   or eff_control_guan or main_cai_heavy)):
            result.work_efficiency = WorkEfficiency.LARGE.value
            result.structure_clarity = StructureClarity.CLEAR.value
            result.work_level = "LARGE_NOBLE"
        elif result.eff_path_direct and result.eff_power_concentrated and result.eff_target_effective:
            result.work_efficiency = WorkEfficiency.LARGE.value
            result.structure_clarity = StructureClarity.CLEAR.value
            result.work_level = "LARGE_NOBLE"
        elif result.eff_path_direct and (
            result.eff_power_concentrated or result.eff_target_effective
        ):
            result.work_efficiency = WorkEfficiency.MEDIUM.value
            result.structure_clarity = StructureClarity.PARTIALLY_CLEAR.value
            result.work_level = "MEDIUM_NOBLE"
        elif result.eff_path_direct and weak_only:
            result.work_efficiency = WorkEfficiency.SMALL.value
            result.structure_clarity = StructureClarity.MIXED.value
            result.work_level = "SMALL_NOBLE"
        elif result.eff_path_direct:
            result.work_efficiency = WorkEfficiency.SMALL.value
            result.structure_clarity = StructureClarity.MIXED.value
            result.work_level = "SMALL_NOBLE"
        else:
            result.work_efficiency = WorkEfficiency.NONE.value
            result.structure_clarity = StructureClarity.CHAOTIC.value
            result.work_level = "POOR"

        # 根因C修复：做负功（劫财合官/穿官损官/禄被穿）→ 效率降一档
        # 盲派"做负功者凶"：负面做功存在时成就层次压一档
        # （官被劫财合走=非我所有 → MEDIUM 降 SMALL；不做全盘否定, 保留有效做功档位）
        if negative_methods:
            if result.work_efficiency == WorkEfficiency.LARGE.value:
                result.work_efficiency = WorkEfficiency.MEDIUM.value
                result.structure_clarity = StructureClarity.PARTIALLY_CLEAR.value
                result.work_level = "MEDIUM_NOBLE"
                result.undetermined_reasons.append(
                    "存在做负功归因(%s) → 效率降档 LARGE→MEDIUM" % "/".join(negative_methods)
                )
            elif result.work_efficiency == WorkEfficiency.MEDIUM.value:
                result.work_efficiency = WorkEfficiency.SMALL.value
                result.structure_clarity = StructureClarity.MIXED.value
                result.work_level = "SMALL_NOBLE"
                result.undetermined_reasons.append(
                    "存在做负功归因(%s) → 效率降档 MEDIUM→SMALL" % "/".join(negative_methods)
                )

        # 根因D消费：日主得气校准（文献依据《盲派命理-案例资料集》：
        #   "有财官≠有富贵, 关键在于'谁在做功'、'是否为我所用'"；
        #   "做功方式不对(劫财合官,非日主得气)→非我所有,终身仓库保管员")
        # 规则: 有效功存在但无一日主亲自(SELF_DIRECT)/禄身(LU_SELF)——
        #       功全靠借力(TOOL_ASSISTED)/宾位(OTHER)完成=日主不得气 → 效率压一档
        #       仅压 LARGE→MEDIUM / MEDIUM→SMALL, SMALL 与 NONE 底部不压
        _eff_dims = [dd for m, a, dd in zip(methods, attrs, result.zuo_gong_actor_dimensions)
                     if a == ZuoGongAttribution["EFFECTIVE"]]
        if _eff_dims and not any(dd in ("SELF_DIRECT", "LU_SELF") for dd in _eff_dims):
            if result.work_efficiency == WorkEfficiency.LARGE.value:
                result.work_efficiency = WorkEfficiency.MEDIUM.value
                result.structure_clarity = StructureClarity.PARTIALLY_CLEAR.value
                result.work_level = "MEDIUM_NOBLE"
                result.undetermined_reasons.append(
                    "有效做功但日主不得气(无亲自/禄身, 全靠借力/宾位=%s) → 效率压档 LARGE→MEDIUM（文献: 非日主得气→层次压低）"
                    % "/".join(sorted(set(_eff_dims)))
                )
            elif result.work_efficiency == WorkEfficiency.MEDIUM.value:
                result.work_efficiency = WorkEfficiency.SMALL.value
                result.structure_clarity = StructureClarity.MIXED.value
                result.work_level = "SMALL_NOBLE"
                result.undetermined_reasons.append(
                    "有效做功但日主不得气(无亲自/禄身, 全靠借力/宾位=%s) → 效率压档 MEDIUM→SMALL（文献: 非日主得气→层次压低）"
                    % "/".join(sorted(set(_eff_dims)))
                )

        # ── V3.6.9⑦ 效率加倍结构(原书"去巳劫, 劫凶神反为用效率加倍, 很有手段")──
        # 主位穿制凶神(比劫/七杀, EFFECTIVE 归因)=凶神反为用, 做功效率提一档。
        # 放在所有降档之后, 使"穿制凶神反为用"能最终升档(净赢=凶神为我所用)。
        # 真值 壬寅戊申丙申壬辰(股票庄家控制几十亿)=主位穿制劫财反为用。
        chuan_xiongshen = any(
            m in ("穿制劫财", "穿制比肩", "穿制七杀", "穿损七杀", "穿制伤官")
            and a == ZuoGongAttribution["EFFECTIVE"]
            for m, a in zip(methods, attrs)
        )
        if chuan_xiongshen and result.eff_path_direct and result.eff_target_effective:
            if result.work_efficiency == WorkEfficiency.NONE.value:
                result.work_efficiency = WorkEfficiency.SMALL.value
                result.structure_clarity = StructureClarity.MIXED.value
                result.work_level = "SMALL_NOBLE"
                result.undetermined_reasons.append(
                    "V3.6.9⑦ 穿制凶神反为用(效率加倍): NONE→SMALL"
                )
            elif result.work_efficiency == WorkEfficiency.SMALL.value:
                result.work_efficiency = WorkEfficiency.MEDIUM.value
                result.structure_clarity = StructureClarity.PARTIALLY_CLEAR.value
                result.work_level = "MEDIUM_NOBLE"
                result.undetermined_reasons.append(
                    "V3.6.9⑦ 穿制凶神反为用(效率加倍): SMALL→MEDIUM"
                )
            elif result.work_efficiency == WorkEfficiency.MEDIUM.value:
                result.work_efficiency = WorkEfficiency.LARGE.value
                result.structure_clarity = StructureClarity.CLEAR.value
                result.work_level = "LARGE_NOBLE"
                result.undetermined_reasons.append(
                    "V3.6.9⑦ 穿制凶神反为用(效率加倍): MEDIUM→LARGE"
                )

        result.rules_triggered.append("WK-EFFICIENCY-002")
        result.rules_triggered.append("WK-EFFICIENCY-003")
        result.rules_triggered.append("WK-EFFICIENCY-004")
        result.rules_triggered.append("WK-EFFICIENCY-005")

    # ── 功神/废神角色（GS-001~003 + 原书功神废神二元）──────────────
    def _resolve_gong_shen(self, chart, result: "BlindBaziResult") -> None:
        """功神/废神角色分配（结构枚举）。

        原书原文：八字中凡参与做功的神称为功神；废神=不参与做功/耗能不产效。
        - WORKING = 实际参与做功的支（功神）
        - TARGET  = 做功目标支（目标神）
        - IDLE    = 四柱中不参与做功的支（闲神/废神，原书ch3"闲神=不参与做功之神"）
        禁"没有做功=废神"（规则§23：须 METHOD_SCOPE 定义才标 WASTE），
        故 IDLE 只标"不参与做功的支"，非贬义"废"。㊻s88 补 IDLE 显式枚举。
        """
        result.rules_triggered.append("GS-001")
        if not result.zuo_gong_methods:
            result.gong_shen = {"UNDETERMINED": []}
            return
        working = sorted(result.zuo_gong_actors)
        target = sorted(result.zuo_gong_targets)
        if working or target:
            # 闲神/废神(ch3 五类神 + patterns): 四柱全支 中 既 不做功参与(actors) 也 非做功目标(targets) 的 支
            # = 不参与 做功 的 字(闲神/废神), 显式 枚举 供 归因 层 消费.
            all_branches = sorted({
                chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
            })
            _used = set(working) | set(target)
            idle = [b for b in all_branches if b not in _used]
            result.gong_shen = {
                "WORKING": working,
                "TARGET": target,
                "IDLE": idle,   # 闲神/废神(不参与做功的支, 原书ch3 闲神 + patterns 废神)
            }
            result.rules_triggered.append("GS-002")
        else:
            result.gong_shen = {"UNDETERMINED": []}

    # ── 断事信号 ───────────────────────────────────────────
    def _generate_signals(self, chart, result, birth_year, stems, day_master):
        signals = []
        # S0: birth_year 缺省（外部 chart 无阳历年）→ signal id 前缀用 UNKNOWN，不编造
        by = birth_year if birth_year is not None else "UNKNOWN"
        # V2.1: 合并天干+地支藏干十神, 用于信号判定(原只看天干透干)
        tg_set = set(t for _, t in stems.values())
        for b in [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                  chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch]:
            for hidden_stem, _pos in BRANCH_HIDDEN_STEMS.get(b, []):
                tg_set.add(ten_god(day_master, hidden_stem))
        methods = result.zuo_gong_methods

        # ── 信号强度合规（BLIND-ARCH-006 / BLIND-G16）：─────────────
        # 盲派禁止"能量/效率/层功"数字化评分；CanonicalSignal.strength 是
        # 平台契约必填字段（[0.0,1.0]），此处统一固定为中性值 0.5，
        # 不表达任何做功强弱排序。盲派做功强弱一律走结构枚举
        # （EFFECTIVE/PARTIAL/BLOCKED/BROKEN/COMPLETE/INCOMPLETE）。
        # ─────────────────────────────────────────────────────────────

        # ── 财运信号（盲派：合财/比劫制财/食伤生财/财星）──
        cai_signals = [m for m in methods if '财' in m]
        # ㊻s66 修(乞丐命·破财方向缺口, ㊻s61 PRESENT_ROBBED 修复后暴露):
        # 旧版 WEALTH_GAIN 信号方向固定 POSITIVE, 但乞丐命(比劫分禄=破财 FENLU_POCAI
        # + 无取财功法 + 主位比劫夺财 = PRESENT_ROBBED 最穷)的财运方向实为 NEGATIVE
        # (有财也守不住/财来财去反穷, 原书"八字有财行财运正是最穷的时候")。
        # 修后: 乞丐命口径(主位比劫制财 NEGATIVE 且 无取财功法食伤生财/泄秀/合财入库)
        # 的财运方向翻转为 NEGATIVE(破财/贫困), 其余财做功保持 POSITIVE。
        # 注: 不新增 event_type(用 平台既有 WEALTH_GAIN + 方向翻转变体), 不扩展事件词汇。
        # ㊻s66 时序修: _generate_signals(L703) 先于 _resolve_wealth_structure(L765,
        # 写入 bijie_zhichai_fenliu) 执行, 故 result.bijie_zhichai_fenliu 此时恒默认
        # UNDETERMINED(同 ㊻s33 crime_direction 时序 bug 同类), 不能用 result 字段,
        # 须本地重算: 主位比劫制财 NEGATIVE(=bi_jie_po) + 无取财功法 EFFECTIVE
        # = 乞丐命破财口径, 与 _resolve_wealth_structure(L3185-3189 FENLU_POCAI
        # 判定链: eff_bijie_decai 无 + neg_bijie_po 有) 同口径。
        neg_bijie_po_s66 = any(
            m == "比劫制财" and a == ZuoGongAttribution["NEGATIVE"]
            for m, a in zip(methods, result.zuo_gong_attributions)
        )
        eff_bijie_decai_s66 = any(
            m == "比劫制财" and a == ZuoGongAttribution["EFFECTIVE"]
            for m, a in zip(methods, result.zuo_gong_attributions)
        )
        qu_cai_eff_s66 = any(
            m in ("食伤生财", "食伤泄秀", "合财入库")
            and a == ZuoGongAttribution["EFFECTIVE"]
            for m, a in zip(methods, result.zuo_gong_attributions)
        )
        # FENLU_POCAI 口径(同 _resolve_wealth_structure L3185-3189): 无宾位得财
        # (eff_bijie_decai 无) + 有主位破财(neg_bijie_po 有)。
        # ㊻s68/s70 修(全量 NEGATIVE 财 态 分 布 核 对): ㊻s68 旧版 只 排 除 宾 位 得 财
        # 未 排 除 换 象 当 财/取 财 功 法, 致 125 条 非 PRESENT_ROBBED 例 误 判 NEGATIVE
        # (㊻s68 全 量 核 对 TOTAL=148, 其 中 70 DIRECTED_WITH_ROBBERY + 28 SUB_CAND +
        # 14 DIRECTED_AND_EST + 13 SUB_AND_EST 均 有 财 路/换 象, 破 财 仅 风 险 非 主 判)。
        # 修 后 与 _resolve_wealth_structure L3189-3209 本 局 判 链 完 全 对 齐:
        # 主 位 破 财(neg_bijie_po) + 无 宾 位 得 财(not eff_bijie_decai)
        # + 无 取 财 功 法(not qu_cai_eff, 食 伤 生 财/泄 秀/合 财 入 库)
        # + 无 换 象 当 财(排 除 image_substitution≠UNDETERMINED 例,
        # SUBSTITUTED_* 财 路 通, 破 财 仅 风 险) = 乞 丐 命 破 财 主 判, 全 量 → 23 条。
        _has_substitution_s70 = getattr(result, "image_substitution", "UNDETERMINED") != "UNDETERMINED"
        _poverty_s66 = (
            neg_bijie_po_s66
            and not eff_bijie_decai_s66
            and not qu_cai_eff_s66
            and not _has_substitution_s70
        )
        if cai_signals:
            _dir_s66 = EventDirection.NEGATIVE if _poverty_s66 else EventDirection.POSITIVE
            signals.append(CanonicalSignal(
                signal_id=f"blind-cai-{by}", source_engine=SourceEngine.BLIND,
                event_type="WEALTH_GAIN", domain=Domain.LIFE_EVENT,
                direction=_dir_s66, strength=0.5,  # 平台中性值，非做功数字化
                temporal_scope=SignalTemporalScope(granularity="YEARLY"),
                evidence_refs=[f"E-BLIND-CAI-{by}"], rule_refs=["BLIND-CAI-001"],
                layer=SignalLayer.BASELINE))
            if _poverty_s66:
                result.rules_triggered.append("EVT-CAI-POVERTY-001")
        else:
            # 规则 §33 WEALTH-001/002：禁"财星存在=财富"。
            # 无做功链时财富事件结论 UNDETERMINED（结构事实=财星透藏已由
            # transparent_ten_gods 输出，此处不派生出事件信号）。
            result.undetermined_reasons.append(
                "财星存在但无做功链：WEALTH 事件 UNDETERMINED（WEALTH-001/002，禁星存在=吉凶）"
            )

        # ── 子嗣信号(盲派: 时柱=子女宫, 官杀/食伤=子女星)──
        # 原书: 时柱被冲/穿=子女宫受损(子息不利); 官杀/食伤做功=子息可断。
        # (修 可真值 80 例 "子" 关键词 4/10 未覆盖: 甲辰丁丑甲戌丁卯/癸未乙卯甲子己巳/
        #  庚午戊子丙寅丙申/壬子丁未丁卯辛丑 等 断语含"子息/子女" 引擎无子嗣信号)
        hour_branch = chart.hour_pillar.earthly_branch
        hour_attacked = any(
            BRANCH_CHONG.get(b) == hour_branch or BRANCH_CHUAN.get(b) == hour_branch
            for b in [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                      chart.day_pillar.earthly_branch]
        )
        child_star_work = any(
            ('官' in m or '杀' in m or '食' in m or '伤' in m)
            for m in methods
        )
        if hour_attacked or child_star_work:
            signals.append(CanonicalSignal(
                signal_id=f"blind-child-{by}", source_engine=SourceEngine.BLIND,
                event_type="CHILD_REACH", domain=Domain.FAMILY,
                direction=EventDirection.NEUTRAL, strength=0.5,
                temporal_scope=SignalTemporalScope(granularity="YEARLY"),
                evidence_refs=[f"E-BLIND-CHILD-{by}"], rule_refs=["BLIND-CHILD-001"],
                layer=SignalLayer.BASELINE))

        # ── 父母事件信号(盲派: 父母离异/家庭离异 = 父母星缘薄 结构事实)──
        # 原书: 命主父母离异=家庭离异事件, 非婚姻结构. 父母离异 原书 明断
        # (真值 壬寅癸丑辛亥己亥: "你姊妹五个, 你占老大, 你父母离了婚").
        # 父母系统 父/母 任一侧 ABSENT/WEAKENED(缘薄) = 家庭离异 结构事实.
        # 用本地计算(非消费 result.parental_event_structure——5h 在 _generate_signals 之前已写入,
        # 但为保持信号层自洽, 本地重算 父/母 星 present/weakened 判定):
        from ..reasoning.bazi_ten_gods import ten_god as _tg_local
        _branches_p = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        _stems_p = [
            chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
            chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
        ]
        _cai_local = any(
            _tg_local(day_master, s) in GROUP_CAI for s in _stems_p
        ) or any(
            _tg_local(day_master, h) in GROUP_CAI
            for b in _branches_p for h, _pp in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        _bi_local = any(
            _tg_local(day_master, s) in GROUP_BI for s in _stems_p
        ) or any(
            _tg_local(day_master, h) in GROUP_BI
            for b in _branches_p for h, _pp in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        # 父=偏财 弱(比劫夺财=父缘薄); 母=正印 弱(财克印=母缘薄)
        _p_thin = _bi_local or _cai_local
        if _p_thin:
            signals.append(CanonicalSignal(
                signal_id=f"blind-parent-{by}", source_engine=SourceEngine.BLIND,
                event_type="PARENTAL_EVENT", domain=Domain.FAMILY,
                direction=EventDirection.NEGATIVE, strength=0.5,
                temporal_scope=SignalTemporalScope(granularity="YEARLY"),
                evidence_refs=[f"E-BLIND-PARENT-{by}"], rule_refs=["BLIND-PARENT-001"],
                layer=SignalLayer.BASELINE))
            result.rules_triggered.append("EVT-PARENTAL-002")

        # ── 羊刃信号(盲派: 坐刃=自我意志/刚烈, 刃逢冲=血光)──
        # (修 可真值 "刃" 9 例 缺口: 日支坐刃 结构事实 但 体 候选 UNDETERMINED)
        _yang_ren_branches = [
            b for b in [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                        chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch]
            if b in getattr(chart, 'shensha', {}).get('YANG_REN', [])
        ]
        if _yang_ren_branches:
            signals.append(CanonicalSignal(
                signal_id=f"blind-yangren-{by}", source_engine=SourceEngine.BLIND,
                event_type="YANG_REN_PRESENT", domain=Domain.LIFE_EVENT,
                direction=EventDirection.NEUTRAL, strength=0.5,
                temporal_scope=SignalTemporalScope(granularity="STATIC"),
                evidence_refs=[f"E-BLIND-YANGREN-{by}"], rule_refs=["BLIND-YANGREN-001"],
                layer=SignalLayer.BASELINE))
            result.rules_triggered.append("EVT-BODY-002")

        # ── 事业信号（合官/食伤制杀/印化官杀/官杀）──
        guan_signals = [m for m in methods if '官' in m or '杀' in m]
        if guan_signals:
            signals.append(CanonicalSignal(
                signal_id=f"blind-guan-{by}", source_engine=SourceEngine.BLIND,
                event_type="CAREER_PROMOTION", domain=Domain.CAREER,
                direction=EventDirection.POSITIVE, strength=0.5,  # 平台中性值，非做功数字化
                temporal_scope=SignalTemporalScope(granularity="YEARLY"),
                evidence_refs=[f"E-BLIND-GUAN-{by}"], rule_refs=["BLIND-GUAN-001"],
                layer=SignalLayer.BASELINE))
        else:
            # 规则 §30 OFF-001：禁"官星出现=官贵/事业"。
            # 无做功链时事业事件结论 UNDETERMINED。
            result.undetermined_reasons.append(
                "官杀存在但无做功链：CAREER 事件 UNDETERMINED（OFF-001，禁星存在=事业）"
            )

        # ── 性格（伤官/七杀/食神）──
        if '伤官' in tg_set:
            signals.append(CanonicalSignal(
                signal_id=f"blind-xing-shangguan-{by}", source_engine=SourceEngine.BLIND,
                event_type="PERSONALITY", domain=Domain.LIFE_EVENT,
                direction=EventDirection.NEUTRAL, strength=0.5,
                temporal_scope=SignalTemporalScope(granularity="STATIC"),
                evidence_refs=[f"E-BLIND-XSG-{by}"], rule_refs=["BLIND-X-001"],
                layer=SignalLayer.BASELINE))
        if '七杀' in tg_set:
            signals.append(CanonicalSignal(
                signal_id=f"blind-xing-qisha-{by}", source_engine=SourceEngine.BLIND,
                event_type="PERSONALITY", domain=Domain.LIFE_EVENT,
                direction=EventDirection.NEUTRAL, strength=0.5,
                temporal_scope=SignalTemporalScope(granularity="STATIC"),
                evidence_refs=[f"E-BLIND-XQS-{by}"], rule_refs=["BLIND-X-002"],
                layer=SignalLayer.BASELINE))

        # ── 婚姻（配偶宫冲害 → 纯结构判据）──
        # V2.7: 移除 spouse_star_strength=='weak' 消费（Bazi 判断层字段，
        # 标注 NOT_AUTHORIZED，违反 BLIND-ARCH-003 禁止消费子平判断）。
        # 仅用客观结构：日支（配偶宫）被冲/被穿/被合绊。
        day_branch_structure = (
            getattr(chart, 'day_branch_clash', False)
            or getattr(chart, 'day_branch_harm', False)
        )
        # 配偶宫被冲（寅申冲等）：日支对冲支出现在四柱
        day_branch_chong = BRANCH_CHONG.get(chart.day_pillar.earthly_branch)
        if day_branch_chong in [
            chart.year_pillar.earthly_branch,
            chart.month_pillar.earthly_branch,
            chart.hour_pillar.earthly_branch,
        ]:
            day_branch_structure = True

        if day_branch_structure:
            signals.append(CanonicalSignal(
                signal_id=f"blind-hunyin-{by}", source_engine=SourceEngine.BLIND,
                event_type="MARRIAGE_CHALLENGE", domain=Domain.FAMILY,
                direction=EventDirection.NEGATIVE, strength=0.5,
                temporal_scope=SignalTemporalScope(granularity="YEARLY"),
                evidence_refs=[f"E-BLIND-HY-{by}"], rule_refs=["BLIND-HY-001"],
                layer=SignalLayer.BASELINE))

        # ── 健康（五行失衡 / 体支被冲 / 官杀无制=病灾）──
        # V2.6 fix: 原逻辑BRANCH_CHONG.get(b) in ti_branches(用支对冲在体=体冲用)方向反了.
        # 盲派: 体支被冲=体受伤. 正确=体支的对冲支在用支中(体被用冲).
        body_chonged = any(
            BRANCH_CHONG.get(b) in result.yong_branches
            for b in result.ti_branches
        )
        # V3.6.9⑭ 官杀无制=病灾(原书"官杀无制=伤身/病灾", 官杀=克身之神, 无制则伤身):
        # 修真值"病/灾/寿"10例缺口.
        # V3.6.9⑯ 时序修: _generate_signals 在 _resolve_official_structure(5h) 之前运行,
        # 此时 result.official_event_structure 尚未写入, 旧版 消费 result 取值 永远 空 → 恒 False.
        # 修后 直接 以 5h 口径 重算 official_state: 官 杀 present + 无 制(用 5g 已 写入 的
        # zuo_gong_methods/attributions 判 制 类 做功) + 无 穿 损/墓 库 收/合 走 → UNCONTROLLED.
        _guan_stems = [s for s in [chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
                                    chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem]
                       if ten_god(day_master, s) in ("正官", "七杀", "偏官")]
        _guan_hidden = any(
            ten_god(day_master, h) in ("正官", "七杀", "偏官")
            for b in [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                      chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch]
            for h, _pp in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        _officer_present = bool(_guan_stems or _guan_hidden)
        # 制官 判据 = 5h 同 口径: 制 类 关键词 有 EFFECTIVE + 墓库收官
        _zhi_kw = ("食伤制杀", "伤官制官", "刑制正官", "刑制七杀", "冲制官杀",
                   "刑正官", "刑七杀", "冲正官", "冲七杀", "合正官", "合七杀",
                   "穿制正官", "穿制七杀", "印化官杀", "印制官杀")
        _eff_ms = [m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
                   if a == "EFFECTIVE"]
        _zhi_officer = any(m in _eff_ms for m in _zhi_kw)
        # 墓库收官: 官 杀 支 为 墓库 且 墓 库 收物 EFFECTIVE
        _off_br = [b for b in [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                                chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch]
                   if any(ten_god(day_master, h) in ("正官", "七杀", "偏官")
                          for h, _pp in BRANCH_HIDDEN_STEMS.get(b, []))]
        _muku_zhi = any(b in ("CHEN", "XU", "CHOU", "WEI") and "墓库收物" in _eff_ms for b in _off_br)
        _controlled = _zhi_officer or _muku_zhi
        # 穿损/合走/换象 → 非 UNCONTROLLED
        _chuan_sun = any(m.startswith("穿损") and ("正官" in m or "七杀" in m)
                         for m in result.zuo_gong_methods)
        _guan_robbed = any(
            [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
             chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch].index(b_bi) < 2
            and [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                 chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch].index(o_b) < 2
            and BRANCH_LIUHE.get(b_bi) == o_b
            for b_bi in [b for b in [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                                     chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch]
                         if any(ten_god(day_master, h) in ("比肩", "劫财")
                                for h, _pp in BRANCH_HIDDEN_STEMS.get(b, []))]
            for o_b in _off_br
        )
        _guan_uncontrolled = (_officer_present and not _controlled
                              and not _chuan_sun and not _guan_robbed
                              and result.image_substitution == "UNDETERMINED")
        guan_wu_zhi = _guan_uncontrolled
        if body_chonged or guan_wu_zhi:
            signals.append(CanonicalSignal(
                signal_id=f"blind-health-{by}", source_engine=SourceEngine.BLIND,
                event_type="HEALTH_ISSUE", domain=Domain.LIFE_EVENT,
                direction=EventDirection.NEGATIVE, strength=0.5,
                temporal_scope=SignalTemporalScope(granularity="YEARLY"),
                evidence_refs=[f"E-BLIND-HEALTH-{by}"], rule_refs=["BLIND-HEALTH-001"],
                layer=SignalLayer.BASELINE))
            if guan_wu_zhi and not body_chonged:
                result.rules_triggered.append("EVT-HEALTH-002")

        # ── 事业变动（规则 §58 象→事过滤链）──
        # 原 BLIND-001"宾主五行相异→JOB_CHANGE"是"结构差异=事件"的泛化直断：
        # 宾主五行相异只是象层事实，未过 DOMAIN/PALACE/TEN_GOD/WORK 完整链，
        # 不得派生出 JOB_CHANGE 事件。结构事实（宾主支集合）已由
        # main_branches/guest_branches 输出，此处仅记 UNDETERMINED。
        main_elems = {_branch_element(b) for b in result.main_branches}
        guest_elems = {_branch_element(b) for b in result.guest_branches}
        if main_elems and guest_elems and main_elems.isdisjoint(guest_elems):
            result.undetermined_reasons.append(
                "宾主五行相异但无做功链：JOB_CHANGE 事件 UNDETERMINED（§58，象层事实不直断事件）"
            )

        result.signals = signals

    # ── V3.2 正局/反局（VERIFY-BLIND-035，盲派中级命理学第01章）────────────
    def _resolve_zheng_fan_ju(self, chart, result, day_master):
        """正局/反局判定（原局层 R1-R4；岁运反局 R5-R6 接时间层二期）。

        原书（《盲派中级命理学》第01章 正局、反局）：
          "反局：日柱做功所表达的意思与原局表达的意思相反，为凶。
           反局分原局反局、大运反局、流年反局三种。"
          R3 冲合反局："年月与日时有冲合反局…日时是冲局、年月反是合局；
            或日时为合局、年月反为冲局…是反局八字。干合与支冲不算反局，
            必须是地支之间的冲合才是反局。"
          R2 日主之功与日支之功相反："以日主为主…日主合时柱官做功，
            要看官坐下的支去干啥了…官的坐支与日支做的功相反时，就反局了"
          R1 日支做功与势对抗："日支做的功与八字的势对抗，就是反局"
          R4 连体被坏："戊申一柱，戊生申为一体…连体金不可坏，坏则伤寿"
        诊断：反局（原局大反局：左边伤官制官，
              右边合财）"=R2 日主合财(追求财)
              vs 原局伤官制官(去官) 意向冲突。
        布尔规则（零评分）：
          FAN_JU 当任一成立：
            R1 日支参与做功 且 做功对象五行 = 势(≥3支)所制对象 → 日支与势对抗
            R2 日主天干五合(合财/合官=追求) 且 原局存在制类做功(制官/制杀)
               且 合的对象与被制的对象不同党 → 意向冲突
            R3 年月冲∧日时合 或 年月合∧日时冲（仅地支间）
            R4 连体柱在局 且 连体之支被制/被冲/被穿/被刑
        """
        pillars = [
            (0, chart.year_pillar.heavenly_stem, chart.year_pillar.earthly_branch),
            (1, chart.month_pillar.heavenly_stem, chart.month_pillar.earthly_branch),
            (2, chart.day_pillar.heavenly_stem, chart.day_pillar.earthly_branch),
            (3, chart.hour_pillar.heavenly_stem, chart.hour_pillar.earthly_branch),
        ]
        all_branches_list = [p[2] for p in pillars]
        methods = result.zuo_gong_methods
        reasons = []

        # ── R3 冲合反局（仅地支间：年月冲∧日时合 或 年月合∧日时冲）──
        y_b, m_b, d_b, h_b = all_branches_list
        ym_he = (BRANCH_LIUHE.get(y_b) == m_b)
        ym_chong = (BRANCH_CHONG.get(y_b) == m_b)
        dh_he = (BRANCH_LIUHE.get(d_b) == h_b)
        dh_chong = (BRANCH_CHONG.get(d_b) == h_b)
        if (ym_he and dh_chong) or (ym_chong and dh_he):
            reasons.append(
                f"R3冲合反局: 年月{y_b}{m_b}{'合' if ym_he else '冲'}∧"
                f"日时{d_b}{h_b}{'冲' if dh_chong else '合'}"
            )

        # ── R2 日主之功与日支之功相反（意向冲突）──
        # 日主天干与透干（年/月/时干）五合 = 日主明合（追求方向）。
        # 禁暗合/宾位合/泛化"有合方法"——只认日干直接参与的明合（原书"日主合时柱官"）。
        day_he_targets = []
        for p_ in pillars:
            if p_[0] == 2:
                continue
            if (day_master, p_[1]) in STEM_HE or (p_[1], day_master) in STEM_HE:
                day_he_targets.append((p_[1], ten_god(day_master, p_[1])))
        day_he_methods = [f"日主合{tg}" for _, tg in day_he_targets]
        # 原局【有效】的"去正官"方法（伤官制官/制正官/刑制正官/穿制正官）
        # V3.4.3 R2 判据再次收紧（对齐段氏原书官杀章原文）：
        #  1) 必须 EFFECTIVE（无效的伤官制官不构成去官意向——伤官制官 INEFFECTIVE 则非去官）
        #  2) 排除"官杀制X/比劫制财/财制印"——那些不是去官（官杀制比劫=官杀自己做功）
        #  3) 制【七杀】≠ 去正官：合官+制杀=制凶得权，方向同向不冲突（合正官+制七杀=大贵）
        #  4) 反局依据=日主合【财】+ 伤官制官 EFFECTIVE（求财 vs 丢官）
        zhi_guan_eff = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
            and ('伤官制官' in m or '制正官' in m or '刑制正官' in m or '穿制正官' in m)
        ]
        # V3.4.3 【天干伤官明克正官】（反局原文"左边伤官
        # 制官"=年柱天干紧贴明克，是反局依据；引擎做功层按藏干/
        # 宾位判 INEFFECTIVE 丢失）：
        # 判据：相邻(含同柱)的天干伤官 克 天干正官（明干相克=原局实际发生的去官功）。
        zhi_tiangan = False
        _stems4 = [
            chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
            chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
        ]
        for _i in range(4):
            for _j in range(4):
                if abs(_i - _j) > 1:
                    continue
                if (ten_god(day_master, _stems4[_i]) == "伤官"
                        and ten_god(day_master, _stems4[_j]) == "正官"
                        and CONTROLS.get(STEM_ELEMENT[_stems4[_i]]) == STEM_ELEMENT[_stems4[_j]]):
                    zhi_tiangan = True
                    break
            if zhi_tiangan:
                break
        # 原书R2："日主合时柱官做功，要看官坐下的支去干啥了；官的坐支与日支
        # 做的功相反时，就反局了" —— 日主合正官(追求权位) 或 日主合财(求财)
        # 与原局去正官（丢官）并存 = 意向冲突。
        # ㊻s88 修: R2"日主合官 vs 去官冲突"须 去官 方 有效 (EFFECTIVE) 才构成 冲突.
        # ch1 例①朱元璋"日主合月令官=意在管理控制, 财官全被我制=正局皇帝命":
        # 伤官制官/印化官杀 是 宾位/藏干 INEFFECTIVE(做功无效) 时, 不构成 去官意向, 不判 R2 冲突.
        # 原口径 zhi_tiangan 只看 天干 明克(无 效率 门控), 致 朱元璋 误判 FAN_JU.
        zhi_tiangan_eff = False
        if zhi_tiangan:
            zhi_tiangan_eff = any(
                '伤官制官' in m and a == ZuoGongAttribution["EFFECTIVE"]
                for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            )
        if day_he_methods and (zhi_guan_eff or zhi_tiangan_eff):
            _zhi_eff_src = zhi_guan_eff if zhi_guan_eff else ['伤官制官(天干明克)']
            he_has_guan = any('正官' in m for m in day_he_methods)
            he_has_cai = any('财' in m for m in day_he_methods)
            if he_has_guan or he_has_cai:
                reasons.append(
                    f"R2日主做功与日支做功相反: {'+'.join(day_he_methods)}(追求)"
                    f" vs 原局{'+'.join(_zhi_eff_src)}"
                    "(去除正官)"
                )

        # ── R1 日柱追求与势对抗(定势法序列: 消费 L1 的 shi_party/shi_controlled) ──
        # 原书 ch1 "日支追求的意思与势对抗=反局"(例②"丑合子水=追求水"):
        # 日柱追求方向 = 日干五合/生目标(仅当日干在做功) + 日支合/破/三合/暗合对象五行。
        # 追求 = 势所制(忌, shi_controlled) → 逆势 FAN_JU; 追求 = 势本党/生势(喜) → 顺势。
        # 喜/忌是 L1 定势的推论(忌=势所制, 喜=势本党+生势), 非独立忌喜层(原著无此层)。
        # 日干与日支同时做功且方向相反(ch1 "日主与日支同时做功, 以日主为准; 两者相反也反局"):
        # 意向冲突 → FAN_JU。势 UNDETERMINED 时保留旧单五行≥3支口径兜底(不消费势)。
        shi = getattr(result, "shi_direction", "UNDETERMINED")
        shi_ctrl = list(getattr(result, "shi_controlled", []) or [])
        shi_party = list(getattr(result, "shi_party", []) or [])
        # 喜 = 势本党 + 生势五行(去重) —— L1 推论, 直接由 shi_party 算, 不依赖独立忌喜层
        _gen_to = {}
        for _g, _t in GENERATES.items():
            _gen_to.setdefault(_t, []).append(_g)
        xishen_all = []
        for p in shi_party:
            if p not in xishen_all:
                xishen_all.append(p)
            for g in _gen_to.get(p, []):
                if g not in xishen_all:
                    xishen_all.append(g)
        day_branch = all_branches_list[2]
        # 日柱追求方向分两路: 日干追求(仅在做功时, 合/生/克谁) + 日支追求(合/破/三合/暗合/克/冲/刑/穿/墓对象)
        # ch1 "先看日主是否做功(合、生、克), 不做功就看日支": 日干做功=合官/合财/生谁/克谁(追求)
        stem_pursue_els = set()
        # ch1 日干做功门控: 日干有 合/生/克 意图即做功(不论宾主, 日柱=主位), ㊻s88 放宽原 zuo_gong_actors 门控
        stem_is_actor = any(
            (day_master, p_[1]) in STEM_HE or (p_[1], day_master) in STEM_HE
            for p_ in pillars if p_[0] != 2
        ) or any(
            GENERATES.get(STEM_ELEMENT.get(day_master, ""), "") == STEM_ELEMENT.get(p_[1], "")
            for p_ in pillars if p_[0] != 2
        )
        if stem_is_actor:
            day_el = STEM_ELEMENT.get(day_master, "")
            # ch1 定势法: 日干追求的是"官/财/印"(十神, 做功目标), 非"目标干五行".
            # 朱元璋造"丁壬合月令官=意在管理控制, 财官全被我制=正局皇帝命":
            # 日干合官=追求官(管理权), 非"追壬的五行水(忌)". ㊻s88 修 目标定义 偏.
            # 目标干十神 → 追求该十神(官=追求官/财=追求财/印=追求印/比劫=追求禄)
            for p_ in pillars:
                if p_[0] == 2:
                    continue
                if (day_master, p_[1]) in STEM_HE or (p_[1], day_master) in STEM_HE:
                    _tg = ten_god(day_master, p_[1])
                    # 合官(正官/七杀)=追求官; 合财(正财/偏财)=追求财; 合印=追求印
                    if _tg in GROUP_GUAN:
                        stem_pursue_els.add("GUAN")   # 追求官(管理/官职)
                    elif _tg in GROUP_CAI:
                        stem_pursue_els.add("CAI")    # 追求财
                    elif _tg in GROUP_YIN:
                        stem_pursue_els.add("YIN")    # 追求印
                    elif _tg in GROUP_BI:
                        # 合到比劫(争财/分禄)=L5 做功层, 非 L1 定势 追求 目标
                        stem_pursue_els.add("OTHER")
                    else:
                        # 合到食伤(泄秀)=L5 做功层, 非 L1 定势 追求 目标
                        stem_pursue_els.add("OTHER")
            # ch1 "日主做功(合、生)": 日干生谁=追求被生者(生官/生财等意向)
            for p_ in pillars:
                if p_[0] == 2:
                    continue
                tgt_el = STEM_ELEMENT.get(p_[1], "")
                if day_el and tgt_el and GENERATES.get(day_el) == tgt_el:
                    _tg2 = ten_god(day_master, p_[1])
                    if _tg2 in GROUP_GUAN:
                        stem_pursue_els.add("GUAN")
                    elif _tg2 in GROUP_CAI:
                        stem_pursue_els.add("CAI")
                    elif _tg2 in GROUP_YIN:
                        stem_pursue_els.add("YIN")
                    else:
                        stem_pursue_els.add("OTHER")   # 生到 比劫/食伤=泄秀/争财, 非 L1 定势 忌/喜 判定目标
            stem_pursue_els.discard("")
        # 日支追求: 日支与全局各支的合/破/三合/暗合对象五行(ch1 例②"丑合子水=追求水")
        branch_pursue_els = set()
        # 三合局→局五行(追求方向=局五行, 非目标支自身五行)
        _SHUREN_JU = {
            'SHEN-ZI-CHEN': 'WATER',   # 水局
            'HAI-MAO-WEI': 'WOOD',     # 木局
            'YIN-WU-XU': 'FIRE',      # 火局
            'SI-YOU-CHOU': 'METAL',   # 金局
        }
        for ob in all_branches_list:
            if ob == day_branch:
                continue
            ob_el = _branch_element(ob)
            if (BRANCH_LIUHE.get(day_branch) == ob
                    or (day_branch, ob) in BRANCH_BANHE
                    or (ob, day_branch) in BRANCH_BANHE):
                branch_pursue_els.add(ob_el)
            for _sh_key, _sh_set in BRANCH_SANHE.items():
                if day_branch in _sh_set and ob in _sh_set:
                    # 三合: 追求方向 = 局五行(非目标支自身), ch1 例②口径
                    branch_pursue_els.add(_SHUREN_JU.get(_sh_key, ob_el))
        # ch1 "日支追求的意思"暗合口径: 日支与全局支的暗合(藏干相合, 如未亥拱木=未中己丁乙合亥中壬甲)
        # 暗合=日支藏干与目标支藏干有干合→追求目标支本气五行(例②"丑合子水"同类, 非仅明合)
        # ch1 例①"朱元璋造 丑未冲/丑戌刑=制财库(做功=顺势), 非追求": 暗合项仅当
        # 目标支 藏干 含 非 日支 自身 干气 的 五行 才 记 追求 (丑暗合辰戌=癸合戊, 癸为丑中 干气,
        # 非丑 本气己, 追求 目标支 辰戌 的 本气土=丑 自身 干气=不记 追求). ㊻s88 修 朱元璋例 暗合 过宽.
        _HIDDEN = BRANCH_HIDDEN_STEMS
        if _HIDDEN:
            day_hidden = set(h for h, _p in _HIDDEN.get(day_branch, []))
            # 日支 自身 干气 五行 (本气= 主 藏干), 暗合 目标支 若 本气 同 日支 干气=自干气 不记
            _day_main_el = _branch_element(day_branch)
            for ob in all_branches_list:
                if ob == day_branch:
                    continue
                ob_hidden = set(h for h, _p in _HIDDEN.get(ob, []))
                ob_main_el = _branch_element(ob)
                # 日支藏干 与 目标支藏干 存在五合(如乙庚/甲己/丁壬/丙辛/戊癸)→暗合追求
                if any((a, b) in STEM_HE or (b, a) in STEM_HE
                       for a in day_hidden for b in ob_hidden):
                    # 目标支 本气 五行 与 日支 本气 同 (如丑暗合辰戌=土, 丑 本气土)=自干气, 不记 追求
                    if ob_main_el != _day_main_el:
                        branch_pursue_els.add(ob_main_el)
        # ch1 "日主做功(合、生、克、冲、刑、穿、墓、破)": 日支的克/冲/刑/穿/墓=追求被作用对象
        # 克: 日支五行克目标支五行=追求克对象; 冲/刑/穿: 支间作用=追求该支; 墓: 日支为某五行库
        # ch1 例②"丑合子水=追求水"口径: 日支追求=合/破/三合/暗合对象(主动求取之意),
        # 冲/刑/穿/墓=被动作用(被冲/被刑=体坏, 非追求), ㊻s88 回退过宽的克/冲/刑/墓追求项.
        # ch1 例③"辛丑不追火=顺势"锚点: 丑未刑不应反推"追求水忌", 刑=破毁非追求.
        branch_pursue_els.discard("")
        # ch1 方位法则(原书"日干合年月官=我管他, 合时上官=他管我[时上=头脑=被控制]"):
        # 日干合官, 合的对象在年月(宾位官)=管理权(我管他); 合时上官(主位官)=头脑被控制(他管我).
        result.guan_he_fangwei = "UNDETERMINED"
        for p_ in pillars:
            if p_[0] == 2:
                continue
            tgt_stem = p_[1]
            if (day_master, tgt_stem) in STEM_HE or (tgt_stem, day_master) in STEM_HE:
                _tg = ten_god(day_master, tgt_stem)
                if _tg in GROUP_GUAN:  # 正官/七杀
                    # 年月(0,1)=宾位官=我管他; 时(3)=主位官=他管我
                    result.guan_he_fangwei = "WOGUAN_TA" if p_[0] in (0, 1) else "TAGUAN_WO"
                    break

        # 合并日柱追求(去重): ch1 定势法 精校——
        # 日干做功(合官/合财/生)=合住官财=做功("制了就要得到")=顺势(与势同向, 不判逆);
        # 日支追求(合/破/三合/暗合 忌神)=主动求取忌=逆势(与势相反, 判 R1).
        # ㊻s88 修: 原把日干合官当"追求官星五行(忌)=逆势"致朱元璋例误判 FAN_JU;
        # ch1 例①"丁壬合月令官=意在管理控制, 财官全被我制=正局"锚定 日干做功=顺势.
        _day_el = STEM_ELEMENT.get(day_master, "")
        _guan_el = next((e for e, c in CONTROLS.items() if c == _day_el), "")   # 官星五行
        _cai_el = CONTROLS.get(_day_el, "")                                     # 财星五行
        _yin_el = next((g for g, t in GENERATES.items() if t == _day_el), "")   # 印星五行
        _marker2el = {"GUAN": _guan_el, "CAI": _cai_el, "YIN": _yin_el, "OTHER": ""}
        stem_pursue_els_x = set(_marker2el.get(m, m) for m in stem_pursue_els)
        stem_pursue_els_x.discard("")
        # ch1 定势法: 日干做功=顺势(合住官财=做功), 不判 R1 逆势; R1 逆势仅由 日支追求 判定.
        # "日主与日支同时做功, 以日主为准; 两者相反也反局": 日主做功=顺势(与势同向),
        # 日支追求忌=逆势 → 日主日支相反=反局(R1). 故 R1 判据 = 日支追求忌(逆势) 且 日干在做功(顺势)
        # 或 日干不做功且日支追求忌(逆势). 核心 = 日支追求忌(逆势) 触发 R1.
        if shi != "UNDETERMINED" and shi_ctrl:
            _gen_to = {}
            for _g, _t in GENERATES.items():
                _gen_to.setdefault(_t, []).append(_g)
            xishen_all = []
            for p in shi_party:
                if p not in xishen_all:
                    xishen_all.append(p)
                for g in _gen_to.get(p, []):
                    if g not in xishen_all:
                        xishen_all.append(g)
            # 日支追求: 追求势所制(忌)=逆势; 追求势本党/生势(喜)=顺势
            branch_pursues_ctrl = [el for el in branch_pursue_els if el in shi_ctrl]
            branch_pursues_party = [el for el in branch_pursue_els if el in xishen_all]
            stem_active = bool(stem_pursue_els)   # 日干是否在做功(合/生)
            if branch_pursues_ctrl and not branch_pursues_party:
                if stem_active:
                    # 日主做功(顺势) 但 日支追求忌(逆势)=日主日支相反 → 反局(ch1 "两者相反也反局")
                    reasons.append(
                        f"R1日主日支相反: 势={shi}(忌={shi_ctrl}), 日干做功顺势"
                        f"(合住官财=制了就要得到), 日支追求忌={branch_pursues_ctrl}=逆势(ch1 定势法)"
                    )
                else:
                    # 日干不做功, 看日支: 日支追求忌=逆势 → 反局(ch1 "不做功就看日支")
                    reasons.append(
                        f"R1日支追求与势对抗: 势={shi}(忌={shi_ctrl}), 日支追求五行={sorted(branch_pursue_els)}"
                        f"(追求忌神={branch_pursues_ctrl}=逆势, ch1 定势法)"
                    )
            elif branch_pursues_ctrl and branch_pursues_party:
                # ch1 定势法 R1 意向冲突(李嘉诚锚 ㊻s124i): 日支同时追求忌与喜,
                # 但 日支自身(原身)在 势本党 时(如 火土势中 日支=戊=本党), 日支追求忌=
                # "日支所坐之物(亥水)被势所制, 日支追求它=追求被制之物=得忌=做功",
                # 与 日干做功(财制印 EFFECTIVE=制财原神/制印=做功指向忌) 同向, 非真正矛盾.
                # 判据: 日支自身五行 在 势本党(日支为 势中 之物) 且 日干 在做功(顺势)
                # → 不构成 R1 反局(日主日支 同向 顺势), 日支追忌=得忌做功.
                _day_branch_el = _branch_element(day_branch)
                # ch1 定势法 "做功于忌=得忌=吉": 日支自身(原身/坐支)在势本党+势制不净(忌转财)
                # 双条件齐 → 日支追忌=追被制之忌=得忌做功, 与势同向, 非真正矛盾, 不判 R1 反局.
                # 李嘉诚锚: 日支午(火, 火土势本党)+势制不净(ZHI_BU_JING, 金水忌转财)+午亥合(官与食神做功)
                # =做功指向忌(财=忌被我制)=正局富命. 制不净是关键门控: 制净时忌仍是忌, 追忌=逆势.
                # 不要求日干五合(stem_active), 做功主体在日支(日支为势中之物, 追忌=得忌).
                _day_branch_in_party = _day_branch_el in xishen_all or _day_branch_el in shi_party
                _zhi_jing_flag = getattr(result, "shi_zhi_jing", "ZHI_JING") == "ZHI_BU_JING"
                if _day_branch_in_party and _zhi_jing_flag:
                    # ㊻s124i 李嘉诚锚(ch8"官杀制不尽当财看,是发财的命"+ch1"日干做功=制了就要得到"):
                    pass  # 不加 R1 reason, 后续判 ZHENG
                else:
                    # 日支 不 在 势本党(如 日支=亥水 忌 神 自身), 日支 同时 追忌 与 追喜=真 矛盾
                    reasons.append(
                        f"R1日支意向冲突: 势={shi}(忌={shi_ctrl}, 喜={xishen_all}), "
                        f"日支追求忌={branch_pursues_ctrl} 且追喜={branch_pursues_party}"
                        f"(日支同时追忌与喜=意向矛盾=逆势, ch1 定势法)"
                    )
        elif shi == "UNDETERMINED":
            # 无明确势: 保留旧单五行≥3支口径兜底(日支追求对象==势所制=逆)
            branch_el_count = Counter(_branch_element(b) for b in all_branches_list)
            for el, cnt in branch_el_count.items():
                if cnt < 3:
                    continue
                controlled_el = CONTROLS.get(el)
                if controlled_el is None:
                    continue
                if controlled_el in branch_pursue_els:
                    reasons.append(
                        f"R1日支追求与势对抗: 势={el}({cnt}支)制{controlled_el}, "
                        f"日支追求{controlled_el}(逆势)"
                    )
                break
        # ── R4 连体被坏（连体柱支被冲/穿/刑，或柱干被五合走）──
        # 制=做功(吉)不破坏连体；冲/穿/刑=坏(凶)。连体柱被制（财制印=做功）不判反局。
        for p_idx, (s_, b_,) in enumerate([(p[1], p[2]) for p in pillars]):
            key = f"{s_}-{b_}"
            if key not in LIAN_TI_COLUMNS:
                continue
            # 连体支是否被冲/穿/刑（坏，非制）
            b_broken = False
            for m in methods:
                if b_ in m and ('冲' in m or '穿' in m or '刑' in m):
                    b_broken = True
                    break
            # 支间冲穿刑（六合优先：巳申既合又刑→合优先，不算破坏）
            for ob in all_branches_list:
                if ob == b_:
                    continue
                if BRANCH_LIUHE.get(b_) == ob:
                    continue  # 合优先于刑（巳申合为主）
                if (BRANCH_CHONG.get(b_) == ob or BRANCH_CHUAN.get(b_) == ob
                        or (b_, ob) in BRANCH_SANXING_PAIRS
                        or (ob, b_) in BRANCH_SANXING_PAIRS):
                    b_broken = True
                    break
            if b_broken:
                reasons.append(f"R4连体被坏: {key}({LIAN_TI_COLUMNS[key]})连体被冲穿刑坏")

        # ch1 "时支不可坏": 己日主甲戌时 / 辛日主丙申时, 时支为劫财为体, 必须用, 时支不可坏
        hour_stem = pillars[3][1]
        hour_branch = pillars[3][2]
        shi_zhi_body = ((day_master == "JI" and hour_stem == "JIA" and hour_branch == "XU")
                        or (day_master == "XIN" and hour_stem == "BING" and hour_branch == "SHEN"))
        if shi_zhi_body:
            hour_broken = False
            for m in methods:
                if hour_branch in m and ('冲' in m or '穿' in m or '刑' in m or '合' in m):
                    hour_broken = True
                    break
            if not hour_broken:
                for ob in all_branches_list:
                    if ob == hour_branch:
                        continue
                    if BRANCH_CHONG.get(hour_branch) == ob or BRANCH_CHUAN.get(hour_branch) == ob \
                            or (hour_branch, ob) in BRANCH_SANXING_PAIRS or (ob, hour_branch) in BRANCH_SANXING_PAIRS:
                        hour_broken = True
                        break
            if hour_broken:
                reasons.append(
                    f"ch1时支被坏: {day_master}日主{hour_stem}{hour_branch}时, 时支为劫财为体被冲穿刑合坏, 反局"
                )

        # ch1 总纲"体坏=反局": 日主禄支(身支)被冲=根失=体坏.
        # ㊻s88 修: ch1例③锚点"辛丑不追火=顺势"——禄支在宾位(年月)被冲=宾位根损非体坏,
        # 禄支在主位(日支/时支)被冲=体坏; 日支被冲(配偶宫坏)另判, 不入"体坏"反局.
        _LU_BRANCH = {
            "JIA": "YIN", "YI": "MAO", "BING": "SI", "DING": "WU",
            "WU": "SHEN", "JI": "YOU", "GENG": "SHEN", "XIN": "YOU",
            "REN": "ZI", "GUI": "CHOU",
        }
        lu_b = _LU_BRANCH.get(day_master)
        ti_core = set()
        if lu_b and lu_b in all_branches_list[2:]:  # 禄支在主位(日/时)才算体支
            ti_core.add(lu_b)
        ti_broken = False
        for tb in ti_core:
            for ob in all_branches_list:
                if ob == tb:
                    continue
                if BRANCH_CHONG.get(tb) == ob:
                    ti_broken = True
                    break
            if ti_broken:
                break
        if ti_broken:
            reasons.append(
                f"L4体坏: 日主禄支(主位={sorted(ti_core)})被冲坏(根失), ch1'体坏=反局'"
            )

        if reasons:
            result.zheng_fan_ju = "FAN_JU"
            result.zheng_fan_ju_detail = "；".join(reasons)
            result.rules_triggered.append("VERIFY-BLIND-035")
        else:
            result.zheng_fan_ju = "ZHENG"
            result.rules_triggered.append("VERIFY-BLIND-035-ZHENG")

    # ── V3.2 制尽辅助：目标支孤立无援判据 ────────────────────────────
    def _target_isolated(self, chart, result) -> bool:
        """目标支孤立无援判据（布尔）：任一目标支满足——
          ① 本气五行在四柱无同类藏干/天干（孤立）；
          ② 或被四柱他支冲（根被冲掉=孤立）。
        原书（段氏理象学制净原则）："财星孤立无援被制净=大富贵"；
        "制尽杀星得天下"。有根气=制不干净。
        诊断：卯木伤官之根被酉冲（卯酉冲）=根失=制净，
          原实现只看同类藏干（辰藏乙=木同类）误判 PARTIAL。
        """
        all_branches = [
            chart.year_pillar.earthly_branch,
            chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch,
            chart.hour_pillar.earthly_branch,
        ]
        all_stems = chart.four_stems()
        targets = list(result.zuo_gong_targets)
        if not targets:
            return False
        for t in targets:
            t_el = _branch_element(t)
            has_same_branch = any(
                b != t and any(STEM_ELEMENT[h] == t_el
                               for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
                for b in all_branches
            )
            has_same_stem = any(STEM_ELEMENT[s] == t_el for s in all_stems)
            # 被冲=同类根被冲掉（如卯酉冲：卯木之根被冲）
            t_chong = BRANCH_CHONG.get(t)
            is_chonged = t_chong in all_branches
            if (not has_same_branch and not has_same_stem) or is_chonged:
                return True
        return False

    # ── V3.2 换象（VERIFY-BLIND-022 解锁，财命专辑+命理珍宝）──────────
    def _resolve_image_substitution(self, chart, result, day_master):
        """换象解锁 HX1-HX5（保留已有 HX4 比劫当财）。

        原书（《盲派中级命理学》财命专辑）：
          "伤食当财：八字无财星，却有伤食星，以伤食当财富看"
        原书（《命理珍宝》）："为我所支配者为财；为我所享用者禄也为财；
          我所苦心追求者乃伤官，伤官谋为之财…伤官当财者宜身旺，又忌财星明现"
        原书（盲派象法）："八字无财，以禄当财；官杀制不净当财看；官星被合绊当财看"
        诊断：V3.1 遗留域缺口——金水伤官不见财官→伤官当财富看；
          八字无财伤食当财；卯官当财（换象）。
        布尔规则（零评分）：
          HX1 伤官当财: 四柱无财星(天干+地支藏干) ∧ 有伤食星
          HX2 禄当财  : 四柱无财星 ∧ 日主禄在局
          HX3 官杀当财: control_completeness==PARTIAL ∧ 目标含官杀(制不净)
          HX5 官当财  : 合绊结构中 ti/yo 十神含官星
        """
        if result.image_substitution != "UNDETERMINED":
            return  # HX4 比劫当财已由财制比劫方法触发

        # 四柱财星检查（天干+地支藏干）
        all_branches = [
            chart.year_pillar.earthly_branch,
            chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch,
            chart.hour_pillar.earthly_branch,
        ]
        all_stems = chart.four_stems()
        has_cai = any(ten_god(day_master, s) in GROUP_CAI for s in all_stems)
        if not has_cai:
            for b in all_branches:
                for h, _p in BRANCH_HIDDEN_STEMS.get(b, []):
                    if ten_god(day_master, h) in GROUP_CAI:
                        has_cai = True
                        break
                if has_cai:
                    break

        # 有伤食星
        has_shishang = any(
            ten_god(day_master, s) in GROUP_SHI for s in all_stems
        ) or any(
            ten_god(day_master, h) in GROUP_SHI
            for b in all_branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])
        )

        if not has_cai and has_shishang:
            # HX1 伤官当财（原书：无财星有伤食星，以伤食当财富看）
            result.image_substitution = "HUAN_XIANG_SHANGSHI_DANG_CAI"
            result.rules_triggered.append("VERIFY-BLIND-022-HX1")
            return

        if not has_cai:
            # HX2 禄当财（原书：八字无财，以禄当财）
            dm_lu = road_branch(day_master)
            if dm_lu in all_branches:
                result.image_substitution = "HUAN_XIANG_LU_DANG_CAI"
                result.rules_triggered.append("VERIFY-BLIND-022-HX2")
                return

        # HX3 官杀当财（原书ch9"官杀制不净当财看，是发财的命"）
        # 口径: 官杀present + 无控制(UNCONTROLLED)=制不净 → 当财看(发财命).
        # 原书ch9 L9"官杀被制但制不干净→当财看"; official_state=UNCONTROLLED/DAMAGED
        # + 官杀present + 做功层有制官杀方法(食伤制杀/伤官制官/官杀制比劫)
        # = 制不净状态(有制但没制干净), 非完全无制(ABSENT).
        if result.control_completeness == "PARTIAL":
            zhi_targets = set()
            for m, d in zip(result.zuo_gong_methods, result.zuo_gong_detail):
                if '制' in m:
                    for b in all_branches:
                        if b in d:
                            zhi_targets.add(b)
            targets_have_guan = any(
                ten_god(day_master, h) in GROUP_GUAN
                for t in zhi_targets
                for h, _p in BRANCH_HIDDEN_STEMS.get(t, [])
            )
            if targets_have_guan:
                result.image_substitution = "HUAN_XIANG_GUANSHA_DANG_CAI"
                result.rules_triggered.append("VERIFY-BLIND-022-HX3")
                return
        # V3.6.9㊻r ch9 官杀制不净当财扩(原书ch9"官杀制不好当财看, 是发财的命"):
        # 口径: 官杀present + 功层有官杀EFFECTIVE方法 + control_completeness=PARTIAL(制不净).
        # PARTIAL=官杀被制但没制干净(留有痕迹)=制不净当财; CLEAN=制干净不判; UNCONTROLLED=无制不判.
        # ㊻ 前 HX3 仅查制类方法目标支藏干含官, 过严漏判(官杀present但制类方法目标支不含官藏干).
        guansha_in_four = any(
            ten_god(day_master, s) in GROUP_GUAN for s in all_stems
        ) or any(
            ten_god(day_master, h) in GROUP_GUAN
            for b in all_branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        guan_eff = any(
            "杀" in m or "官" in m
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        )
        # 制不净: 官杀present + 官杀EFFECTIVE做功(官杀在做功路径上) + 制不净(PARTIAL)
        if guansha_in_four and guan_eff and result.control_completeness == "PARTIAL":
            result.image_substitution = "HUAN_XIANG_GUANSHA_DANG_CAI"
            result.rules_triggered.append("VERIFY-BLIND-022-HX3")
            return

        # HX5 官当财（原书：官星被合绊当财看；卯官当财为换象实例）
        for hb_str in result.he_ban_structures:
            if '官' in hb_str or '杀' in hb_str:
                result.image_substitution = "HUAN_XIANG_GUAN_DANG_CAI"
                result.rules_triggered.append("VERIFY-BLIND-022-HX5")
                return

    # ── V3.2 盲派旺衰五态（VERIFY-BLIND-036 前置，势体系非评分）────────
    def _resolve_blind_wangshuai(self, chart, result, day_master):
        """盲派旺衰五态（中和/偏弱/太弱/旺/旺极弱极）。

        依据（《命理玄机探秘》四定律 + 段氏势体系，布尔结构判定，零评分）：
          - 旺极/弱极：全局近乎单一五行（从格类，日主五行占≥3支且无强对立）
          - 旺     ：日主得令(月支本气=日主五行或生日主) 或 全局日主五行≥3支
          - 太弱   ：日主无根(本气藏干无同五行) 且 全局日主五行≤1
          - 中和/偏弱：其余（有根但不得令）
        铁律：这是盲派自身旺衰（按势/结构），不消费子平 STRONG/WEAK。
        """
        dm_el = STEM_ELEMENT[day_master]
        all_branches = [
            chart.year_pillar.earthly_branch,
            chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch,
            chart.hour_pillar.earthly_branch,
        ]
        # 日主五行支数（本气）
        root_branches = [b for b in all_branches if _branch_element(b) == dm_el]
        # 日主五行全局计数（本气+藏干+天干）
        party_count = len(root_branches)
        for b in all_branches:
            for h, _p in BRANCH_HIDDEN_STEMS.get(b, []):
                if STEM_ELEMENT[h] == dm_el:
                    party_count += 1
        for s in chart.four_stems():
            if STEM_ELEMENT[s] == dm_el:
                party_count += 1
        # 月支本气
        month_branch = chart.month_pillar.earthly_branch
        month_main_el = _branch_element(month_branch)
        in_season = (
            month_main_el == dm_el
            or GENERATES.get(month_main_el) == dm_el  # 月令生日主
        )
        # 对立五行（克日主）计数
        controlling_el = CONTROLS.get(dm_el)
        opponent_count = sum(
            1 for b in all_branches if _branch_element(b) == controlling_el
        )
        # 金透干计数（非日主的日主五行天干, 段氏"比劫帮身"）
        jin_gan = sum(
            1 for s in chart.four_stems()
            if STEM_ELEMENT[s] == dm_el and s != day_master
        )
        # ── V3.6.9⑩ 坐禄被冲/穿(禄破)细化(原书"坐禄被冲/穿=身弱", 段氏"卯酉冲破禄身弱")──
        # 禄破 = 日支坐禄 被 冲/穿 且 冲穿支不帮日主(不生日主/不同五行)。
        # 失令党重但坐禄被冲=帮身力减, 原书"身弱"(真值 丁未壬子丁巳辛亥: 丁火日主,
        # 坐禄巳被亥冲, 亥水克火=不帮, 原书"身弱官作忌")。禄破时 党重判旺 降偏弱。
        day_branch = chart.day_pillar.earthly_branch
        lu_clash = any(
            (BRANCH_CHONG.get(day_branch) == b or BRANCH_CHUAN.get(day_branch) == b)
            and _branch_element(b) != dm_el
            and GENERATES.get(_branch_element(b)) != dm_el
            for b in all_branches if b != day_branch
        )
        lu_chuan = any(
            BRANCH_CHUAN.get(day_branch) == b
            and _branch_element(b) != dm_el
            and GENERATES.get(_branch_element(b)) != dm_el
            for b in all_branches if b != day_branch
        )

        if len(root_branches) >= 3 and opponent_count == 0:
            result.blind_wangshuai = "WANG_JI"
            result.rules_triggered.append("VERIFY-BLIND-036-WS-001")
        elif len(root_branches) == 0 and party_count <= 1:
            result.blind_wangshuai = "TAI_RUO"
            result.rules_triggered.append("VERIFY-BLIND-036-WS-002")
        elif in_season and not (lu_clash or lu_chuan):
            # 得令且禄不破: 直接判旺(月令本气=日主或生日主)
            result.blind_wangshuai = "WANG"
            result.rules_triggered.append("VERIFY-BLIND-036-WS-003")
        elif in_season and (lu_clash or lu_chuan):
            # V3.6.9⑩ 得令但坐禄被冲/穿(禄破): 帮身力减 → 偏弱.
            result.blind_wangshuai = "ZHONG_HE_PIAN_RUO"
            result.rules_triggered.append("VERIFY-BLIND-036-WS-007")
            result.undetermined_reasons.append(
                "V3.6.9⑩ 得令但坐禄被冲/穿(禄破): 帮身力减→偏弱"
            )
        elif party_count >= 4 and not (lu_clash or lu_chuan) or (
            jin_gan >= 1 and len(root_branches) >= 2 and not (lu_clash or lu_chuan)
        ):
            # 失令党重(禄未破)：pc>=4 或 金透干>=1且根>=2 → 旺
            result.blind_wangshuai = "WANG"
            result.rules_triggered.append("VERIFY-BLIND-036-WS-003")
        elif party_count >= 3 and (lu_clash or lu_chuan):
            # V3.6.9⑩ 失令党重但坐禄被冲/穿(禄破): 帮身力减 → 偏弱.
            result.blind_wangshuai = "ZHONG_HE_PIAN_RUO"
            result.rules_triggered.append("VERIFY-BLIND-036-WS-008")
            result.undetermined_reasons.append(
                "V3.6.9⑩ 失令党重但坐禄被冲/穿(禄破): 帮身力减→偏弱"
            )
        else:
            result.blind_wangshuai = "ZHONG_HE_PIAN_RUO"
            result.rules_triggered.append("VERIFY-BLIND-036-WS-004")

    # ── V3.2 六亲计数（VERIFY-BLIND-036，命理玄机探秘四定律+纳音）──────
    def _resolve_kinship_count(self, chart, result, day_master, gender):
        """同胞计数（四定律 + 纳音计数 + 刑冲穿克往下减）。

        原书（《命理玄机探秘》·从兄弟个数谈起）：
          "规律一：身中和或中和偏弱，以比劫为兄弟姐妹（纳音也包括在个数之内）；
           规律二：身太弱，印、比、劫皆为兄弟姐妹，兼顾合；
           规律三：身旺（非旺极）以官杀（包括纳音）为兄弟姐妹；
           规律四：旺极弱极仍取比劫。以上四定律反过来也成立。"
        口诀："兄弟姐妹看四柱，同类五行为手足。天干地支都在内，支藏人元也算数。
               刑冲穿克往下减，合化五行要看住。不算人元也可以，纳音同类论手足。
               男命比肩为兄弟，劫财姐妹不差数。女命比肩为姐妹，劫财兄弟是手足。"
        诊断：V3.1 遗留域缺口——三正五行金+一纳音金=四同胞；
          身旺无官杀以食伤为同胞，五重水=五胎损一，引擎未实现。
        布尔规则：
          取星: 中和/偏弱→比劫; 太弱→印比劫; 旺(非旺极)→官杀; 旺极弱极→比劫;
                旺且无官杀→食伤（盲派六亲计数口诀）
          计数: 天干 + 地支本气 + 支藏人元 + 纳音同类
          减损: 被冲/穿/刑/克的字减一
          性别: 男比肩=兄弟 劫财=姐妹; 女反之
        """
        all_branches = [
            chart.year_pillar.earthly_branch,
            chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch,
            chart.hour_pillar.earthly_branch,
        ]
        all_stems = chart.four_stems()
        ws = result.blind_wangshuai

        # 取星（四定律）
        if ws in ("WANG_JI",):
            star_groups = [GROUP_BI]
        elif ws == "TAI_RUO":
            star_groups = [GROUP_BI, GROUP_YIN]
        elif ws == "WANG":
            # 身旺以官杀；身旺无官杀以食伤（盲派六亲计数口诀）
            has_guan = any(
                ten_god(day_master, s) in GROUP_GUAN for s in all_stems
            ) or any(
                ten_god(day_master, h) in GROUP_GUAN
                for b in all_branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])
            )
            star_groups = [GROUP_GUAN] if has_guan else [GROUP_SHI]
        else:  # ZHONG_HE_PIAN_RUO
            star_groups = [GROUP_BI]

        # 纳音五行（排盘层事实，消费 chart.nayin）
        nayin_els = []
        for pos in ('year', 'month', 'day', 'hour'):
            nayin_name = chart.nayin.get(pos, "")
            if nayin_name:
                nayin_els.append(NAYIN_FIVE_ELEMENT.get(nayin_name, ""))
        result.nayin_five_elements = {
            pos: NAYIN_FIVE_ELEMENT.get(chart.nayin.get(pos, ""), "")
            for pos in ('year', 'month', 'day', 'hour')
        }

        # 计数：天干 + 地支本气 + 支藏人元 + 纳音同类
        count = 0
        counted = []  # 计数明细（供审计）
        def _tg_in_groups(tg, groups):
            return any(tg in g for g in groups)

        # 天干
        for s in all_stems:
            tg = ten_god(day_master, s)
            if _tg_in_groups(tg, star_groups):
                count += 1
                counted.append(f"干{s}({tg})")
        # 地支本气 + 支藏人元
        for b in all_branches:
            for h, is_main in BRANCH_HIDDEN_STEMS.get(b, []):
                tg = ten_god(day_master, h)
                if _tg_in_groups(tg, star_groups):
                    count += 1
                    counted.append(f"{b}藏{h}({tg})")
        # 纳音同类（纳音五行 = 取星五行的同类）
        for pos, el in zip(('year', 'month', 'day', 'hour'), nayin_els):
            if el and any(
                STEM_ELEMENT[h] == el
                for b in all_branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])
            ):
                count += 1
                counted.append(f"{pos}纳音({chart.nayin.get(pos, '')})")

        # 减损：刑冲穿克往下减（被冲/穿/刑/克的字减一）
        # 简化布尔判据：四柱存在冲/穿/刑关系 → 减一（口诀"刑冲穿克往下减"）
        has_jian = False
        for i, b1 in enumerate(all_branches):
            for b2 in all_branches[i + 1:]:
                if (BRANCH_CHONG.get(b1) == b2 or BRANCH_CHUAN.get(b1) == b2
                        or (b1, b2) in BRANCH_SANXING_PAIRS
                        or (b2, b1) in BRANCH_SANXING_PAIRS):
                    has_jian = True
                    break
            if has_jian:
                break
        reduced = 0
        if has_jian:
            count = max(0, count - 1)
            reduced = 1

        # 性别分配：男比肩=兄弟 劫财=姐妹；女反之
        if gender == "male":
            brother_tg, sister_tg = '比肩', '劫财'
        else:
            brother_tg, sister_tg = '劫财', '比肩'
        brother_count = sum(
            1 for c in counted if f"({brother_tg})" in c
        )
        sister_count = count - brother_count

        result.kinship_count = {
            "wangshuai": ws,
            "star_rule": "四定律-" + {
                "WANG_JI": "旺极弱极取比劫",
                "TAI_RUO": "身太弱印比劫皆为兄弟姐妹",
                "WANG": "身旺以官杀(含纳音)",
                "ZHONG_HE_PIAN_RUO": "身中和偏弱以比劫(含纳音)",
            }.get(ws, ws),
            "count_detail": counted,
            "nayin_consumed": result.nayin_five_elements,
            "total": count,
            "reduced": reduced,
            "brother_count": brother_count,
            "sister_count": sister_count,
            "gender": gender,
        }
        result.kinship_chain = f"KINSHIP_COUNT(total={count},兄弟{brother_count},姐妹{sister_count})"
        result.rules_triggered.append("VERIFY-BLIND-036")


    # ── V3.3 L1e 事件结构（盲派生产规则 60-64 章）───────────────────────────
    # 全布尔/枚举；只消费 L0（四柱/藏干/冲穿合刑）与 L1（做功/制尽/换象/旺衰）
    # 自身事实；不消费子平判断字段（spouse_star_strength 等 NOT_AUTHORIZED）。

    def _resolve_marriage_structure(self, chart, result, day_master):
        """婚姻系统（§60）。原书（盲派中级命理学·婚姻篇）：
        配偶宫=日支；配偶星=男财女官；配偶宫与星相生/合/拱=关联，
        相穿/刑/破=婚姻出问题。禁止"日支被冲→婚姻失败"（§60 明示）。"""
        day_branch = chart.day_pillar.earthly_branch
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            day_branch, chart.hour_pillar.earthly_branch,
        ]
        others = [b for b in branches if b != day_branch]
        # 配偶宫状态（结构事实，单条不判吉凶）— 用 flag 集合收敛枚举（无重复拼接）
        # 根因E修复：日支与其他支的关系统一走 resolve_branch_relation 解析层，
        # 不再各自查冲/穿/刑表（避免巳申=合/刑/破、寅巳=穿/刑结论矛盾）
        palace_flags = []
        for ob in others:
            rel = resolve_branch_relation(day_branch, ob, branches)
            if rel == "chong":
                if "CLASHED" not in palace_flags:
                    palace_flags.append("CLASHED")
            elif rel == "chuan":
                if "HARMED" not in palace_flags:
                    palace_flags.append("HARMED")
            elif rel == "xing":
                if "PUNISHED" not in palace_flags:
                    palace_flags.append("PUNISHED")
            elif rel == "po":
                if "PO_BROKEN" not in palace_flags:
                    palace_flags.append("PO_BROKEN")
        # 合绊（V3.2 合绊域：日支与其他支六合=被合绊, 感情易被牵动）
        if any(day_branch in h for h in result.he_ban_structures):
            palace_flags.append("HE_BANNED")
        palace_state = "STABLE" if not palace_flags else "_AND_".join(palace_flags)
        # 配偶星（男=财 女=官杀）— 藏干+透干都算存在（透干漏判修复）
        spouse_group = GROUP_CAI if chart.gender == "male" else GROUP_GUAN
        stems = [
            chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
            chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
        ]
        star_branches = [
            b for b in branches
            if any(ten_god(day_master, h) in spouse_group for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
        ]
        star_present = bool(star_branches) or any(
            ten_god(day_master, st) in spouse_group for st in stems
        )
        star_weakened = any(
            resolve_branch_relation(b, ob, branches) in ("chong", "chuan", "xing", "po")
            for b in star_branches for ob in branches if ob != b
        )
        # 根因A修复：星入宫正向信号（盲派"申子合=夫到夫宫/妻星入宫"）
        # 配偶星支与日支(配偶宫) 六合/半合/拱合 = 星入宫 = 婚缘/正缘信号
        star_linked_palace = any(
            resolve_branch_relation(b, day_branch, branches) in ("liuhe", "banhe", "gong")
            for b in star_branches
        )
        # V3.4.3 【宾主易位·官星投墓】（对齐段氏原书官星投墓原文）：
        # 原文"日支亥水夫星被亥子水局推向月令→夫星出走；时柱戊土劫财坐辰(亥的墓库)
        # →丈夫(亥中甲木)被戊土(竞争对手)合走→官星投墓；官星在宾位有根(寅)，
        # 主位官星又被劫财收→宾主易位，婚姻难长久"。
        # 布尔判据：配偶星所在支（尤其日支=配偶宫）为入墓之字，且墓库支坐比劫
        # （竞争对手收走配偶星）→ 官星/妻星投墓 = 宾主易位 = 婚姻难长久。
        star_into_muku = False
        for sb in star_branches:
            sb_el = _branch_element(sb)
            # 该配偶星五行的墓库支（辰戌丑未）
            muku_b = None
            for mb, mel in MU_KU.items():
                if mel == sb_el:
                    muku_b = mb
                    break
            if muku_b is None or muku_b not in branches:
                continue
            # 墓库支坐比劫（竞争对手收走配偶星）→ 官星/妻星投墓
            muku_idx = branches.index(muku_b)
            muku_stem = [
                chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
                chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
            ][muku_idx]
            if ten_god(day_master, muku_stem) in GROUP_BI:
                star_into_muku = True
                break
        # V3.6.9⑧ 官杀同现(原书"官杀同现=多婚源"): 男命财(妻星)现+官杀也现=争配偶
        # (比劫/官杀争财), 女命官(夫星)现+财也现=财克夫多婚. 判多次婚源。
        guansha_present = any(ten_god(day_master, st) in GROUP_GUAN for st in stems) or any(
            ten_god(day_master, h) in GROUP_GUAN
            for b in branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        star_hidden_count = len(star_branches)  # 藏干含配偶星的地支数
        # 日支(配偶宫)受 冲/穿/刑 坏的不同支数(原书 L4482 "坏宫看有几个")
        palace_attackers = set()
        for b in branches:
            if b != day_branch and resolve_branch_relation(day_branch, b, branches) in ("chong", "chuan", "xing"):
                palace_attackers.add(b)
        # V3.6.9㊻s ch10 婚姻次数 口 径 溯 源 (㊻j2 全 量 MULTIPLE 196/234=84% 过 宽):
        # ㊻s 初 建 duospouse 第 三 判 据 guansha_compete = "配偶 星 无 藏 干 根 (star_hidden_count==0) + 官 杀 同 现"
        # = 财/官 星 仅 透 干 无 根 + 局 中 另 有 官 杀 支 = 争 配 偶 多 婚 源. 但 363 例 中 84% 命 中,
        # 溯 源: "星 无 藏 干 根"口 径 过 宽 — 盲 派 原 书 ch10 "因 夫 妻 星 多 现 而 离 婚 者, 有 几 个 夫 妻 星 几 次 婚 姻"
        # = 多 婚 源 指 配 偶 星 在 局 中 多 现(≥2 个 柱 位 有 同 类 配 偶 星 干 或 藏 干 根), 非 "无 根 + 官 杀 同 现".
        # "官 杀 同 现" 是 争 夫 相(夫 争 妻 象), 不 是 "多 婚" 口 径(多 婚=配 偶 星 多 现).
        # ㊻j2 修 复: 收 窄 第 三 判 据 为 "配 偶 星 透 干 多 现(≥2 个 柱 位 有 配 偶 星 干, 且 非 日 干 本 身)
        # = 配 偶 星 多 现 多 婚 源", 删 除 "无 根 + 官 杀 同 现" 过 宽 口 径.
        _spouse_group = GROUP_CAI if chart.gender == "male" else GROUP_GUAN
        spouse_stem_pillar_count = sum(
            1 for st in [chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
                         chart.hour_pillar.heavenly_stem]
            if ten_god(day_master, st) in _spouse_group
        )
        spouse_star_tougan_multi = spouse_stem_pillar_count >= 2
        guansha_compete = spouse_star_tougan_multi   # ㊻j2 修: 配 偶 星 多 现(≥2 柱 透 干)=多 婚 源
        duospouse = star_hidden_count >= 2 or len(palace_attackers) >= 1 or guansha_compete
        # 综合(结构枚举，非吉凶词汇)
        broken_palace = any(tok in palace_state for tok in ("CLASHED", "HARMED", "PUNISHED"))
        # V3.6.9㊻u/㊻v ch10 好婚三式③"原局夫妻宫为所忌之神, 被夫妻星制之吉者, 婚姻较好":
        # ㊻t 抽检癸丑庚申庚子壬午(女命伤官制官好婚案例)发现引擎判BROKEN(宫CLASHED+星weakened),
        # 口径缺失"宫为忌被星制=吉"三式③. ㊻u 初建后全量146例HARMONIOUS(过宽, 误放行BROKEN),
        # ㊻v 收窄: 原书ch10 L12"制之不住, 反为坏婚姻"→③口径必须制干净(CLEAN):
        #   ① 日支十神=忌神(非配偶星组, 非正印/正官正星, 即偏印/食神/伤官/比肩/劫财/偏财/七杀)
        #   ② 做功层有配偶星制宫忌神EFFECTIVE(制官/制杀/伤官制官/食伤制官/官杀制食伤等)
        #   ③ 制干净: control_completeness=CLEAN(官杀制尽口径)
        #   ④ 满足①②③ → HARMONIOUS; 不满足③(制不住) → 仍走原BROKEN/CHALLENGED判定
        eff_methods_now = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        ]
        # 日支十神(藏干主气)
        from ..reasoning.bazi_ten_gods import ten_god as _tg
        palace_stems = [h for h, _p in BRANCH_HIDDEN_STEMS.get(day_branch, [])]
        palace_tg = _tg(day_master, palace_stems[0]) if palace_stems else ""
        # 忌神口径(不含配偶星组/正星: 男财女官杀/正印正官)
        spouse_tg_set = GROUP_CAI if chart.gender == "male" else GROUP_GUAN
        # 正星(正印/正官)不算忌神, ③口径排除
        ZHENG_TG_EXCLUDE = {"正印", "正官", "正财"}
        palace_is_ji = (palace_tg not in spouse_tg_set
                        and palace_tg not in ZHENG_TG_EXCLUDE
                        and palace_tg != "")
        # ② 做功层有配偶星制宫忌神EFFECTIVE(制官/制杀/伤官制官/食伤制官/官杀制食伤等)
        ZHIGONG_KWS = ("伤官制官", "食伤制杀", "官杀制食伤", "官杀制伤",
                        "刑制正官", "刑制七杀", "冲制官杀", "穿制正官", "穿制七杀",
                        "合正官", "合七杀", "印制官杀", "印化官杀",
                        "比劫制财", "官杀制比劫", "食伤泄秀")
        zhi_gong_eff = any(kw in m for m in eff_methods_now for kw in ZHIGONG_KWS)
        # ③ 制干净(CLEAN): 官杀制尽口径, ㊻v 收窄
        zhi_gengjing = (result.control_completeness == "CLEAN")
        gong_ji_zhi_star = palace_is_ji and zhi_gong_eff and zhi_gengjing
        if star_into_muku:
            marriage_state = "BROKEN"   # 宾主易位/官星投墓=婚姻难长久（段氏原书）
        elif gong_ji_zhi_star:
            # ㊻v: 好婚三式③宫为忌被星制且制干净=吉(原书ch10好婚组合③), 判HARMONIOUS
            marriage_state = "HARMONIOUS"
        elif palace_state == "STABLE" and star_present and star_linked_palace and not star_weakened and not duospouse:
            marriage_state = "HARMONIOUS"  # 星入宫且宫稳无伤无多婚源=正缘
        elif palace_state == "STABLE" and star_present and not star_weakened and not duospouse:
            marriage_state = "HARMONIOUS"
        elif broken_palace and star_weakened:
            marriage_state = "BROKEN"
        elif palace_state != "STABLE" or star_weakened or duospouse:
            marriage_state = "CHALLENGED"
        else:
            marriage_state = "UNDETERMINED"
        # ── V3.6.9⑧ 婚姻次数（原书 L4481/4482/4667 口诀, 口径含官杀同现）──
        # "因夫妻星多现而离婚者, 有几个夫妻星几次婚姻" / "坏宫看有几个, 有几个几次婚姻"
        # 官杀同现=争配偶多婚源(男命财见官杀/女命官见财克夫), 亦判 MULTIPLE。
        marriage_count_signal = "MULTIPLE" if duospouse else "SINGLE"
        # ── V3.6.9㊻q ch10 婚姻早晚 + 独身四型(原书ch10"年月现配偶星=早婚, 日时现配偶星=晚婚";
        # "独身四型: ①夫妻宫与子女宫占比劫/禄/印而星不易入 ②宫落制星之星制不成 ③宫占星墓无刑冲 ④水中捞月")──
        # ① 早晚婚: 配偶星藏干在年/月柱=早婚, 在日/时柱=晚婚, 双现=UNDETERMINED(无倾向)
        # ㊻h 修: 原仅查藏干, 配偶星虚透(天干透但藏干无同类根)时=星无柱位归属, 判 UNDET 误;
# 补: 天干(年/月干=早, 时干=晚)在配偶星组=直接按柱位归属
        def _spouse_in_branch(b):
            return any(ten_god(day_master, h) in spouse_group
                       for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
        def _spouse_in_stem(st):
            return ten_god(day_master, st) in spouse_group
        year_month_star = [b for b in (chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch)
                           if _spouse_in_branch(b)]
        day_hour_star = [b for b in (day_branch, chart.hour_pillar.earthly_branch)
                         if _spouse_in_branch(b)]
        year_month_stem_hit = [_spouse_in_stem(chart.year_pillar.heavenly_stem),
                               _spouse_in_stem(chart.month_pillar.heavenly_stem)]
        hour_stem_hit = _spouse_in_stem(chart.hour_pillar.heavenly_stem)
        if year_month_star and not day_hour_star:
            marriage_timing = "EARLY"   # 年月现配偶星=早婚
        elif day_hour_star and not year_month_star:
            marriage_timing = "LATE"    # 日时现配偶星=晚婚
        elif year_month_star and day_hour_star:
            marriage_timing = "MIXED"   # 双现=无早晚倾向
        elif any(year_month_stem_hit) and not hour_stem_hit:
            marriage_timing = "EARLY"   # ㊻h: 年月干虚透配偶星=早婚(星无柱位归属, 按干位判)
        elif hour_stem_hit and not any(year_month_stem_hit):
            marriage_timing = "LATE"    # ㊻h: 时干虚透配偶星=晚婚
        elif any(year_month_stem_hit) and hour_stem_hit:
            marriage_timing = "MIXED"   # ㊻h: 双干虚透=无倾向
        else:
            marriage_timing = "UNDETERMINED"
        # ② 独身四型(原书ch10): 仅判④水中捞月(最精确可编码)
        # 水中捞月三条件: ①正星坐夫妻宫 ②日主与日支自合(己亥/戊子/辛巳/壬午/癸巳/丁亥 自合日柱) ③天干偏星干扰
        zihhe_pillars = ("JIA_WU", "YI_CHEN", "DING_HAI", "JI_HAI", "WU_ZI", "XIN_SI", "REN_WU", "GUI_SI")
        zihhe = f"{chart.day_pillar.heavenly_stem}_{day_branch}"
        # 条件①正星坐夫妻宫: 日支藏干含配偶星正神(正财/正官)
        spouse_zheng = "正财" if chart.gender == "male" else "正官"
        star_in_palace_zheng = any(
            ten_god(day_master, h) == spouse_zheng
            for h, _p in BRANCH_HIDDEN_STEMS.get(day_branch, [])
        )
        # 条件③天干偏星干扰: 天干有偏星(男命偏财/女命偏官)
        pianxing = "偏财" if chart.gender == "male" else "偏官"
        pian_tou = any(ten_god(day_master, st) == pianxing for st in stems)
        water_moon = star_in_palace_zheng and zihhe in zihhe_pillars and pian_tou
        marriage_solitary = "SHUI_ZHONG_LAO_YUE" if water_moon else "UNDETERMINED"
        # ch10 婚域消费 L1 势方向 + L4 反局定位凶事宫位(原书 ch1 例②"坤造火土燥势去金水,
        # 局去子水, 日支丑却合子水(追求水, 与势相反)→反局; 反在夫妻宫, 婚姻不好,
        # 子水为夫星, 主夫早死/子女残疾"):
        #   ① 势方向 shi_controlled 含 配偶星五行(男财女官杀)= 势"去制配偶星"= 配偶星被势制
        #      = 配偶星受损方向(婚姻不利); 势去制非配偶星相关=不消费势.
        #   ② 反局(FAN_JU)+反局 R1 因素=日支(配偶宫)追求忌(逆势)= "反在夫妻宫"
        #      = 婚姻大凶(配偶星/宫受损, 原书 ch10 差婚口径).
        # ㊻s88 P1 域层接线: 婚域此前各判各的, 未接 L1 势向 + L4 反局宫位.
        _spouse_el = CONTROLS.get(STEM_ELEMENT.get(day_master, ""), "") if chart.gender == "male" else next(
            (e for e, c in CONTROLS.items() if c == STEM_ELEMENT.get(day_master, "")), "")
        _sh_ctrl_m = list(getattr(result, "shi_controlled", []) or [])
        _shi_zhipei = "SHI_ZHIFEIXING" if (_spouse_el and _spouse_el in _sh_ctrl_m) else "UNDETERMINED"
        _zgj = getattr(result, "zheng_fan_ju", "UNDETERMINED")
        _r1_detail = getattr(result, "zheng_fan_ju_detail", "") or ""
        # 反在夫妻宫: ch1 定势法 R1 只由 日支(=配偶宫) 追求 触发 逆 势:
        #   ① FAN_JU 且 势 去制 配偶 星 (spouse_el in shi_controlled)=配偶 星 被 势 制=配偶 星 受损
        #   ② FAN_JU 且 R1 detail 含 "日 支 追求 忌"(日 支 合/破/三合/暗合 势 所制)=日 支 追求 忌=逆 势
        #   ③ FAN_JU 且 R1 detail 含 "日 主日 支 相反"(日 干 做功 顺 势+日 支 追求 忌=两 意 相 反)
        # ②③ R1 detail 必 含 "日 支"(逆 势 只 由 日 支 触发), 故 ②③ 合 并 为 "R1 detail 含 日 支".
        # 原 书 ch1 例②"坤造火土 燥势去金水, 局 去子 水, 日 支丑却 合子 水(追求 水, 与势 相反)→反局;
        # 反在 夫妻宫, 婚姻 不 好, 子 水 为 夫 星, 主 夫 早 死/子女 残疾". ㊻s88 P1 域 层 接线:
        # 婚 域 此 前 各 判 各 的, 未 接 L1 势 向 + L4 反 局 宫 位.
        _fan_in_cifu = "FAN_IN_CIFU" if (
            _zgj == "FAN_JU" and (
                (_spouse_el and _spouse_el in _sh_ctrl_m)
                or ("日支" in _r1_detail)
            )
        ) else "UNDETERMINED"
        result.marriage_event_structure = {
            "spouse_palace": day_branch,
            "palace_state": palace_state,
            "spouse_star_present": str(star_present),
            "spouse_star_weakened": str(star_weakened),
            "spouse_star_into_muku": str(star_into_muku),
            "spouse_star_linked_palace": str(star_linked_palace),
            "marriage_state": marriage_state,
            "marriage_count_signal": marriage_count_signal,
            "marriage_timing": marriage_timing,       # V3.6.9㊻q ch10 早晚婚(早/晚/混合/UNDET)
            "marriage_solitary": marriage_solitary,   # V3.6.9㊻q ch10 独身四型(水中捞月/UNDET)
            # ch10 婚域消费 L1 势向 + L4 反局定位凶事宫位
            "shi_zhipeixiang": _shi_zhipei,       # ch10: 势去制配偶星=配偶星受损方向
            "fanzu_cifugong": _fan_in_cifu,       # ch1 例②: 反在夫妻宫=婚姻大凶(夫早死/子女残疾)
        }
        result.rules_triggered.append("EVT-MARRIAGE-001")

        # ── ㊻s124 ch10 婚姻三子维细分(原书 L30-34 差婚轻重 / L40 比劫争夫 / L38 正偏夫) ──
        _liyi_ev: List[str] = []
        if marriage_state == "BROKEN":
            _liyi_risk = "CHU"
            _liyi_ev.append("ch10 差婚重(宫坏+星弱/宾主易位)=必离")
        elif marriage_state == "CHALLENGED":
            _liyi_risk = "QING"
            _liyi_ev.append("ch10 差婚轻(宫/星有伤但可经营)=不一定离")
        else:
            _liyi_risk = "UNDETERMINED"
            _liyi_ev.append("ch10 婚姻状态非差婚, 离异轻重未分")
        result.liyi_risk = _liyi_risk
        result.liyi_risk_evidence = _liyi_ev

        _zf_ev: List[str] = []
        _bijie_zhoushou = any(kw in m for m in result.zuo_gong_methods
                              for kw in ("比劫制财", "比劫制官", "比劫争"))
        _bijie_neg = any(m in ("比劫制财", "比劫制官") and a == ZuoGongAttribution["NEGATIVE"]
                         for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions))
        if _bijie_zhoushou and _bijie_neg:
            _zhenfu_risk = "DIVORCE"
            _zf_ev.append("ch10 比劫争夫(妻)重(主位比劫NEGATIVE制配偶星)=离婚")
        elif _bijie_zhoushou:
            _zhenfu_risk = "THIRD_PARTY"
            _zf_ev.append("ch10 比劫争夫(妻)轻(比劫制配偶星但非NEGATIVE)=有第三者/争夫象")
        else:
            _zhenfu_risk = "NONE"
            _zf_ev.append("ch10 无比劫争夫(妻)做功")
        result.zhenfu_risk = _zhenfu_risk
        result.zhenfu_risk_evidence = _zf_ev

        # 正偏夫(妻): ch10 L38 "夫星(妻星)坐正位=正夫, 偏位=偏夫. 不以星的正偏定, 以宫位定".
        # 宫位正偏口径: 日支(夫妻宫)藏干含 正星(男正财/女正官)=正; 藏干含 偏星(男偏财/女偏官)=偏.
        _ph_ev: List[str] = []
        _spouse_zheng = "正财" if chart.gender == "male" else "正官"
        _spouse_pian = "偏财" if chart.gender == "male" else "偏官"
        _palace_stems = [h for h, _p in BRANCH_HIDDEN_STEMS.get(day_branch, [])]
        _palace_tg_list = [_tg(day_master, h) for h in _palace_stems]
        if _spouse_zheng in _palace_tg_list:
            _poshui_star = "ZHENG"
            _ph_ev.append(f"ch10 夫(妻)星坐正位(日支藏干含{_spouse_zheng})=正夫(正妻)")
        elif _spouse_pian in _palace_tg_list:
            _poshui_star = "PIAN"
            _ph_ev.append(f"ch10 夫(妻)星坐偏位(日支藏干含{_spouse_pian})=偏夫(偏妻)")
        else:
            _poshui_star = "UNDETERMINED"
            _ph_ev.append("ch10 夫(妻)星正偏未分(日支未藏正/偏配偶星)")
        result.poshui_star = _poshui_star
        result.poshui_star_evidence = _ph_ev


    def _resolve_wealth_structure(self, chart, result, day_master):
        """财富系统（§61）。原书：禁止"财多→富/财旺→富"；
        必须 WEALTH_PRESENT + WEALTH_TARGETED + WEALTH_WORK_ESTABLISHED。"""
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        stems = [
            chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
            chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
        ]
        wealth_present = (
            any(ten_god(day_master, st) in GROUP_CAI for st in stems)
            or any(ten_god(day_master, h) in GROUP_CAI
                   for b in branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
        )
        # 取财检测（制/合/穿/刑/冲开墓库——必须 EFFECTIVE 才是取财结构事实）
        # V3.6.1 修(可真值41例二次校对): 比劫制财一律 NEUTRAL(夺财结构事实, 非取财方向),
        # 不进入 wealth_positive。原书"比劫制财=同我夺我之财", 制住的是同伙的财,
        # 本人并未取得——原判(宾位比劫制财=财归我 EFFECTIVE)致 丁亥庚戌己巳庚午
        # 误判 PRESENT_UNTAKEN、癸卯丁巳丁巳壬寅 误判 DIRECTED_AND_ESTABLISHED。
        # 取财只看主取宾路径: 食伤生财/财制印/冲开墓库/合财(主位体合宾位财)。
        # ㊻s61 修(乞丐命误判 DIRECTED_WITH_ROBBERY 非 PRESENT_ROBBED): 旧版只排除
        # "比劫制财", 未排除 "穿制正财/穿制偏财" —— 穿=破/坏/不兼容(原书ch7取象七
        # 原则"穿象"), 穿制财=财被穿坏(有财也守不住), 是破财路径而非取财功法,
        # 误入 wealth_positive 致癸卯丁巳丁巳壬寅(乞丐命·穿制正财EFFECTIVE+比劫
        # 制财NEGATIVE)判 DIRECTED_WITH_ROBBERY(财来财去) 而非 PRESENT_ROBBED(最穷)。
        # 修后: 取财功法 = 财/冲开/冲库 类 EFFECTIVE, 排除比劫制财(夺财事实)
        # 与穿制正财/穿制偏财(破财事实)。
        wealth_positive = any(
            ('财' in m or '冲开' in m or '冲库' in m)
            and m != "比劫制财"
            and m not in ("穿制正财", "穿制偏财")
            and a == ZuoGongAttribution["EFFECTIVE"]
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
        )
        # 比劫夺财风险（比劫制财 NEGATIVE = 有财被同我夺的风险事实）
        # V3.6.6 修(可真值41例校对): 主位比劫制财(NEGATIVE) 即构成夺财风险, 不必比劫成势。
        # 原书"比劫制财=同我夺我之财": 主位比劫(日支藏干/时柱干)制财=本人把财夺散,
        # 单一主位比劫即破财(癸卯丁巳丁巳壬寅: 日支巳藏丙劫财制庚财=主位夺财)。
        # 宾位比劫制财(EFFECTIVE)=制住同伙财归我, 不构成夺财风险。
        wealth_robbed = any(
            m == "比劫制财" and a == ZuoGongAttribution["NEGATIVE"]
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
        )
        # V3.6.9㊻o ch8 比劫双向口径(原书ch8 L12"比劫当财(制财局): 比劫制财为得财, 用劫是富命";
        # L36"比劫制财=得财(用劫富命), 比劫分禄=破财, 要看制的是财还是分的是禄"):
        # 宾位比劫制财(EFFECTIVE)=制住同伙财归我=得财(用劫富命); 主位比劫制财(NEGATIVE)=分自身禄=破财。
        # 双向口径: 宾位比劫制财EFFECTIVE 存在 → 得财富命方向(ZHICHAI_DECAI);
        # 主位比劫制财NEGATIVE 存在且无宾位得财口径 → 破财方向(FENLU_POCAI)。
        eff_bijie_decai = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if m == "比劫制财" and a == ZuoGongAttribution["EFFECTIVE"]
        ]
        neg_bijie_po = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if m == "比劫制财" and a == ZuoGongAttribution["NEGATIVE"]
        ]
        if eff_bijie_decai:
            result.bijie_zhichai_fenliu = "ZHICHAI_DECAI"   # 宾位比劫制财=得财(用劫富命)
        elif neg_bijie_po:
            result.bijie_zhichai_fenliu = "FENLU_POCAI"       # 主位比劫分禄=破财
        else:
            result.bijie_zhichai_fenliu = "UNDETERMINED"
        substitution = result.image_substitution != "UNDETERMINED"
        # ㊻s92 ch8 换象当财"被夺否决"(原书ch8 L8/L11"禄神当财忌劫财"/"食伤配财=经商"):
        # 禄当财 + 主位比劫制财NEGATIVE(禄被同我夺) = 禄被夺=贪污/破财, 否决"发财命"。
        # 食伤当财 + 比劫夺财 = 食伤被夺=财路断, 否决。
        # 官杀当财(HX3 制不净, ch8 L9"官杀制不净当财看是发财的命") 是"被制之物"逻辑,
        # 比劫夺财不影响官杀制不净(官杀自身在做功), 不否决。
        he_fin_ku_s93 = any(
            m == "合财入库"
            and a == ZuoGongAttribution["EFFECTIVE"]
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
        )
        # ch8 L8"禄神当财: 无财八字用禄, 喜印生禄、忌伤食劫财": 禄当财 + 比劫夺财 = 禄被夺=贪污, 否决。
        # 食伤当财(HX1 无财用食伤) 比劫夺财不影响食伤为财之原神(食伤自身做功), 不否决(ch8 L9 同官杀当财逻辑)。
        # 官杀当财(HX3 制不净, ch8 L9"官杀制不净当财看是发财的命") 是"被制之物"逻辑,
        # 比劫夺财不影响官杀制不净(官杀自身在做功), 不否决。
        # ㊻s93 教训: 曾试"官杀当财+财入库+比劫夺财=贪污"否决项, 误伤官杀当财吉例(财域 84%→74%), 已回滚。
        _substitution_robbed = (
            result.image_substitution == "HUAN_XIANG_LU_DANG_CAI"
        ) and wealth_robbed
        # ㊻s93 教训: 曾试"官杀当财+财入库+比劫夺财=贪污"否决项(_guansha_caingu_mukuluo),
        # 误伤官杀当财吉例(财域 84%→74%), 已回滚。官杀当财路径维持 ch8 L9"制不净当财=发财"原文口径。
        if substitution and _substitution_robbed:
            wealth_state = "SUBSTITUTED_ROBBED"
        elif substitution:
            # 换象当财（食伤当财/官杀当财）：以用代财=财路事实
            wealth_state = (
                "SUBSTITUTED_AND_ESTABLISHED"
                if result.work_efficiency in (WorkEfficiency.LARGE.value, WorkEfficiency.MEDIUM.value)
                else "SUBSTITUTED_CANDIDATE"
            )
        elif wealth_present and wealth_positive:
            if result.work_efficiency in (WorkEfficiency.LARGE.value, WorkEfficiency.MEDIUM.value):
                if wealth_robbed:
                    # V3.6.6: 有主取宾取财路径, 但主位比劫夺财并存(破财)
                    # → 财来财去, 得而复失。原书"乞丐命·有财行财运最穷"=主位比劫夺财。
                    wealth_state = "DIRECTED_WITH_ROBBERY"
                else:
                    wealth_state = "DIRECTED_AND_ESTABLISHED"
            else:
                # V3.6.6: 效率低(SMALL)但主位比劫夺财=破财压过取财(乞丐命)
                if wealth_robbed:
                    wealth_state = "DIRECTED_WITH_ROBBERY"
                else:
                    wealth_state = "DIRECTED_PARTIAL"
        elif wealth_present and not wealth_positive:
            # ㊻s12+s17 ch8 修(财域方向校对): "无主取宾取财+比劫夺"旧判 PRESENT_ROBBED(最穷)
            # 漏了取财功法口径。ch8 "取财方式": 食伤生财/食伤泄秀(食伤取财)+合财入库(财合入宾位财库)
            # 均为"有财路"取财功法, 有取财功法有功=有财路(吉), 比劫夺财只是"得而复失"风险,
            # 不改变"有财路"主判。"比劫手拉面馆生意很好/发财数百万"被旧判"最穷"误伤。
            # ㊻s92 ch8 取财功法补全(原书ch8"可当财论": 食伤(无财时)/财库/比劫制财局/禄):
            # 印制食伤 EFFECTIVE=印做功用(学业/职业有基础, 原书ch11"印不做功=没学历; 印制伤官=有学历"),
            # 印制住食伤=食伤被管制=有职业方向(工薪取财, 原书ch8"官杀配印/印做功=上班/体制内"),
            # 故 印制食伤EFFECTIVE 纳入取财功法(工薪方向), 不再误判 PRESENT_ROBBED(最穷)。
            qu_cai_eff = any(
                m in ("食伤生财", "食伤泄秀", "合财入库", "印制食伤") and a == ZuoGongAttribution["EFFECTIVE"]
                for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            )
            if wealth_robbed and qu_cai_eff:
                # 比劫夺财并存 + 取财功法(食伤生财/泄秀/合财入库)有功 = 财来财去(有财路但有破财风险)=偏吉
                wealth_state = "DIRECTED_AND_ESTABLISHED"
            elif wealth_robbed:
                # 无取财功法 + 主位比劫夺财 = 财被同我夺, 最穷(乞丐命)
                wealth_state = "PRESENT_ROBBED"
            else:
                # ㊻s13+s17: 无比劫夺财但取财功法(食伤生财/泄秀/合财入库) EFFECTIVE
                # → 财路通, 非"财虚透无功(最穷)"
                shisheng_cai_eff2 = any(
                    m in ("食伤生财", "食伤泄秀", "合财入库") and a == ZuoGongAttribution["EFFECTIVE"]
                    for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
                )
                if shisheng_cai_eff2:
                    wealth_state = "DIRECTED_AND_ESTABLISHED"  # 取财功法有功=有财路(吉)
                else:
                    wealth_state = "PRESENT_UNTAKEN"   # 无取财功法=财虚透无功(财没路)
        elif not wealth_present:
            wealth_state = "ABSENT_NO_SUBSTITUTION"
        else:
            wealth_state = "UNDETERMINED"
        # V3.6.9㊻ ch8 西瓜皮肉原则(原书ch8"取财实质: 合到财库=吃肉富; 合到财外=吃皮穷")
        # 判据: 取财路径(wealth_positive)中合入宾位财库(丑未戌辰中藏财)=吃肉(富),
        # 合到财外(财星虚透/财不在库)=吃皮(穷). 同日同刻不同人, 差别在吃到皮还是肉.
        # 财库=宾位四库(丑未戌辰)藏干含财; 财外=财星仅天干透/无库.
        # ㊻s93: muku_branches/muku_has_cai 须在本层(西瓜皮肉)计算(substitution 分支已用 he_fin_ku_s93 精确判据,
        # 不需 muku_has_cai; 此处恢复原 ㊻z 口径供 CHI_ROU/CHI_PI 消费)。
        muku_branches = [b for b in branches if b in ("CHEN", "XU", "CHOU", "WEI")]
        muku_has_cai = any(
            ten_god(day_master, h) in GROUP_CAI
            for b in muku_branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        # 取财路径中是否有合入财库(合财入墓=吃肉)
        # ㊻z 修: CUI_REN(吃肉=富)只用"合财入库"独立方法(㊻y新建), 不再含"冲开"口径(冲开墓库
        # 是财出来做功, 非"吃到财库肉"原书口径, ㊻w确证重叠误判根因).
        he_fin_ku = any(
            m == "合财入库"
            and a == ZuoGongAttribution["EFFECTIVE"]
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
        )
        # 取财路径中是否有合到财外(食伤生财但财虚透/财无库)
        he_fin_wai = any(
            ('食伤生财' in m or '财制印' in m or '食伤泄秀' in m)
            and a == ZuoGongAttribution["EFFECTIVE"]
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
        )
        if he_fin_ku and muku_has_cai:
            wealth_efficiency = "CHI_ROU"   # ㊻z: 吃肉富(合到财库, ㊻y新建合财入库方法, 原书"吃到肉")
        elif he_fin_wai and not muku_has_cai:
            wealth_efficiency = "CHI_PI"    # 吃皮穷(合到财外, 财无库)
        else:
            wealth_efficiency = "UNDETERMINED"
        # ch8 财域消费 L1 势方向(原书 ch8 李嘉诚/奥纳西斯"火土燥势去亥水(亥带财+财原神)
        # 官印有势去财星与财原神=超级富命" / 风险例"主位财星成火土势去印及劫"):
        # 势方向 shi_controlled 含 财星五行(日主所克=财) 或 财原神(生财=食伤) = 势"去制财星/财原神"
        # = 势为取财做功(超富方向); 势去制非财相关(官印等)=不消费势(保持现状).
        # ㊻s88 P1 域层接线: 财域此前各判各的, 未接 L1 势向.
        _cai_el = CONTROLS.get(STEM_ELEMENT.get(day_master, ""), "")   # 财星五行(日主所克)
        _cai_ys = next((g for g, t in GENERATES.items() if t == _cai_el), "")  # 财原神(生财者=食伤)
        shi_ctrl = list(getattr(result, "shi_controlled", []) or [])
        shi_zhicaixiang = bool(shi_ctrl) and (_cai_el in shi_ctrl or _cai_ys in shi_ctrl)
        _shi_zhicaixiang_out = "SHI_ZHICAI" if shi_zhicaixiang else "UNDETERMINED"
        result.wealth_event_structure = {
            "wealth_present": str(wealth_present),
            "wealth_targeted": str(wealth_positive),
            "wealth_robbed": str(wealth_robbed),
            "image_substitution": result.image_substitution,
            "wealth_state": wealth_state,
            "wealth_efficiency": wealth_efficiency,  # V3.6.9㊻ 西瓜皮肉(吃肉富/吃皮穷)
            "bijie_zhichai_fenliu": result.bijie_zhichai_fenliu,
            "lu_dangcai": result.lu_dangcai,  # V3.6.9㊻s ch8 禄神当财(印生禄吉/伤食劫财破)
            "shi_zhicaixiang": _shi_zhicaixiang_out,  # ch8 财域消费 L1 势方向(势去制财星/财原神=超富方向)
        }
        result.rules_triggered.append("EVT-WEALTH-001")

    def _resolve_official_structure(self, chart, result, day_master):
        """官贵系统（§62）。原书：禁止"官多→贵/杀旺→贵"；
        必须 OFFICER_PRESENT + BODY_USE_RELATION + WORK_ESTABLISHED + RESULT_STRUCTURE。
        OFF-001：官杀无制必犯官非（VERIFY-BLIND-025：官杀旺而无制化则成了官灾）。"""
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        stems = [
            chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
            chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
        ]
        officer_present = (
            any(ten_god(day_master, st) in GROUP_GUAN for st in stems)
            or any(ten_god(day_master, h) in GROUP_GUAN
                   for b in branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
        )
        # 制官类有效方法（食伤制官/刑制官/冲制官/合官；排除"官杀制比劫"=官杀自身做功）
        # 命名双源：L638 五行制=刑制X / 互动无制=刑X；合官=官被合绊（制官一种）
        # V3.4.3 修正（对齐段氏原书穿官原文）：【穿≠制】——
        # 盲派"穿的力量比冲大，穿是背后偷袭、排斥破坏"；"子水伤官穿未土官库=伤官损官，
        # 官根受损，体制内不适应、反骨"（盲派核心技法 §3）。穿官=损官（破坏官根），
        # 不是制官。故穿类方法从制官判据中剔除，另立"官根受损(DAMAGED)"状态。
        # V3.6.7 修(可真值41例校对): 穿官库=去官得权(制官语境), 纳入制官判据。
        # 原"穿≠制"一刀切把"穿官库去官得权"也剔出制官, 致"戌运当官升职"误判 DAMAGED。
        # 区分: 穿制X(穿官库, EFFECTIVE/INEFFECTIVE)=去官得权, 进制官;
        #        穿损X(穿官星本体, NEGATIVE)=官根受损, 进 DAMAGED。
        # V3.6.9⑮ 修(可真值"官"缺口 乙卯甲申甲辰戊辰 官=UNCONTROLLED):
        # 原书"官中有印=印主权力"——印化官杀 是 制官一法(印制官杀), 旧版 制官 关键词 漏 此法,
        # 致 官 present + 印化官杀 EFFECTIVE 时 误判 UNCONTROLLED。修后 纳入 印化官杀/印制官杀。
        control_officer_keywords = (
            '伤官制官', '食伤制杀',
            '刑制正官', '刑制七杀', '冲制官杀',
            '刑正官', '刑七杀', '冲正官', '冲七杀',
            '合正官', '合七杀',
            '穿制正官', '穿制七杀',   # V3.6.7: 穿官库=去官得权
            '制官', '制杀',
            '印化官杀', '印制官杀',    # V3.6.9⑮: 印化/印制官杀=制官一法(原书"官中有印=印主权力")
        )
        eff_methods = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        ]
        controlled = any(m in eff_methods for m in control_officer_keywords) or any(
            m in eff_methods and ('制官' in m or '制杀' in m) and '官杀制' not in m
            for m in eff_methods
        )
        # 墓库收官：官杀所在支为墓库且墓库收物有效=官被收（辛入丑墓→有制但制不净）
        officer_branches = [
            b for b in branches
            if any(ten_god(day_master, h) in GROUP_GUAN for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
        ]
        muku_officer_controlled = any(
            b in MU_KU and '墓库收物' in eff_methods for b in officer_branches
        )
        controlled = controlled or muku_officer_controlled
        # V3.4.3 【穿官=损官】DAMAGED：穿官类方法（含 NEGATIVE 做负功）→ 官根受损
        # V3.6 修(可真值41例校对): 穿官库(去官得权)不是"官根受损"——
        # "穿制X"已表示穿官库=得权(制官语境), 只有"穿损X"(穿官星本体)才是官根受损。
        # officer_damaged 判据(V3.6.9㊻s11 ch9 修): 穿损官星本体(非墓库支)=官根受损。
        # ㊻s11 修(可真值方向校对): 原判"只要做功有穿损官杀就判 DAMAGED"过宽——
        # 4 条"戌运当官升职"案例被误判官根受损(凶), 实为"穿官库=去官得权"(吉)。
        # 精修: 穿损官杀时, 若 ①官杀另有制法(合正官/合七杀/刑官/冲官 有做功) 或
        #       ②官库(戌)在局(官库冲开=升职应期, ch9"戌=官库") → 官根未彻底受损, 不判 DAMAGED。
        # 仅"穿损官星本体 + 无其他制法 + 无官库在局"才判官根受损(DAMAGED)。
        _other_guan_zhi = any(
            (m in ("合正官", "合七杀", "刑正官", "刑七杀", "冲正官", "冲七杀",
                   "印化官杀", "印制官杀", "伤官制官", "食伤制杀")
             and a == ZuoGongAttribution["EFFECTIVE"])
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
        )
        _guan_ku_in = any(b in MU_KU and b in ("XU", "WEI", "CHEN", "CHOU")
                          for b in branches)
        _chuan_sun_off = any(
            m and m.startswith('穿损') and ('正官' in m or '七杀' in m)
            for m in result.zuo_gong_methods
        )
        officer_damaged = (
            _chuan_sun_off
            and not _other_guan_zhi       # 官杀无其他制法(彻底受损)
            and not _guan_ku_in          # 官库不在局(无升职应期)
        )
        # V3.4.3 【官被劫财合走】ROBBED：官杀支被比劫支六合（如巳申=官被劫财合去）
        # （原书原文"官星被劫财合去→非我所有、做功无效"，官贵章）
        # 宾主约束：官支在宾位（年月）且比劫支也在宾位（年月）→ 宾位劫财合走宾位官
        # = 非我所有。主位比肩合宾位官（时支合年支）
        # = 制杀得权，不算被夺。
        # ㊻s16 ch9 修(官域ROBBED校对): 宾位官杀被比劫合走时, 若官杀有制法(财制印/食伤制杀/
        # 印化官杀 EFFECTIVE)=宾位官杀被制住=得权(吉), 非"官被夺(凶)"。
        # 原书ch9"宾位官杀关联到主位, 大运制住宾位官杀=升官": 制住宾位官=得宾位权力(吉)。
        # 庚戌己卯戊子癸亥日主戊: 财制印EFFECTIVE+食伤泄秀EFFECTIVE=官杀被制=得权,
        # 旧判ROBBED(夺官凶)误伤, 修后判CONTROLLED(制宾位官得权吉)。
        _other_guan_zhi_s16 = any(
            (m in ("财制印", "食伤制杀", "食伤制官", "印化官杀", "印制官杀",
                   "伤官制官", "刑正官", "刑七杀", "冲正官", "冲七杀", "合正官", "合七杀")
             and a == ZuoGongAttribution["EFFECTIVE"])
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
        )
        bi_branches = [
            b for b in branches
            if any(ten_god(day_master, h) in GROUP_BI for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
        ]
        officer_robbed = any(
            branches.index(b_bi) < 2 and branches.index(o_b) < 2
            and BRANCH_LIUHE.get(b_bi) == o_b
            for b_bi in bi_branches for o_b in officer_branches
        )
        # ㊻s16: 宾位官杀被比劫合走 + 官杀有制法(得权口径) → 不判ROBBED(夺官), 判CONTROLLED(制宾位官得权)
        officer_robbed = officer_robbed and not _other_guan_zhi_s16
        # ㊻r3 官 贵 虚 精 准 口 径(ch9 "官 命 必 须 有 根, 虚 透=名 气 非 实 官" 精 准 化):































        # ㊻s26 ch9 "官命必须有根, 官有根/有源=有权(吉)" 口径(可真值官域方向校对):
        # 盲派 ch9 "官杀主职务, 必须有根(虚透=名气非实官)". 引擎旧版 UNCONTROLLED 一律判凶(OFF-001
        # "官杀无制必犯官非"), 漏了 "官有根/有源=有权" 口径: 官杀虽无制, 但有根(地支同五行根)
        # 或被财生(财生官=官得源) → 官有权柄, 结构层判"有官(吉)"非"官非(凶)".
        # 庚戌己卯戊子癸亥(日主戊): 官乙(正官)藏卯(月支, 宾位), 财癸(正财, 时干)生官乙=官得源,
        # 断语"宾位官杀关联主位=得宾位权力, 大运制住则升官"(吉), 旧判 UNCONTROLLED(凶)误伤.
        # 判据: 官杀 present + 无制(将判 UNCONTROLLED) + (官杀有根 OR 财生官做功) → 有权(吉).
        # 有根 = 官杀天干/藏干有同五行地支根(官杀星坐实/得地); 财生官 = 财星做功生官(财→官链路).
        officer_rooted = False
        officer_elements = []
        for st in stems:
            if ten_god(day_master, st) in GROUP_GUAN:
                officer_elements.append(STEM_ELEMENT[st])
        for b in branches:
            for h, _p in BRANCH_HIDDEN_STEMS.get(b, []):
                if ten_god(day_master, h) in GROUP_GUAN:
                    officer_elements.append(STEM_ELEMENT[h])
        if officer_elements:
            # 官杀有根: 官杀同五行在地支有根(坐实/得地)
            officer_rooted = any(
                b in branches and STEM_ELEMENT.get(b[0].upper()) in officer_elements
                or any(STEM_ELEMENT.get(h.upper()) in officer_elements
                       for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
                for b in branches
            )
        # 财生官: 财星做功生官(财→官生链, ch8 "官杀主职务, 财为官之原神")
        cai_sheng_guan = any(
            m in ("财生官", "财生官杀")
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        )
        officer_has_power = officer_rooted or cai_sheng_guan

        if officer_present and officer_damaged:
            official_state = "DAMAGED"            # 官根受损（非官非，非官贵）
        elif officer_present and officer_robbed:
            official_state = "ROBBED"             # 官被劫财合走（非我所有）
        elif officer_present and not controlled and officer_has_power:
            # ㊻s26 ch9 "官有根/有源=有权": 官杀无制但有根或被财生 → 有权(吉), 非"官非(凶)"
            official_state = "CONTROLLED_PARTIAL"   # 有官权(部分制/有源), 方向吉
        elif officer_present and controlled and result.control_completeness == "CLEAN":
            official_state = "CONTROLLED_AND_CLEAN"   # 金水伤官制净（制尽杀星得天下）
        elif officer_present and controlled:
            official_state = "CONTROLLED_PARTIAL"
        elif officer_present and not controlled:
            official_state = "UNCONTROLLED"           # OFF-001 官杀无制必犯官非
        elif not officer_present and road_branch(day_master) in branches:
            # V3.6.1 修(可真值41例"以禄当财/官禄格"): 官星不透但禄神在局=官禄格,
            # 原书"官禄格中以禄当财/禄代官"。无官星本体, 禄神代位 → 官贵以禄代。
            official_state = "LU_SUBSTITUTED"
        else:
            official_state = "UNDETERMINED"
        # V3.6.9㊻t ch9 财库制印=企业之官(原书ch9"财库(戌/财库)制印=管企业=企业之官; 财库=股权/资产"):
        # 判据: 财库支(戌=财库, 原书"戌为官库"兼财库; 财临库=财库)在局 + 财库藏干含印星(印被财库收)
        # + 印星做功EFFECTIVE(印制食伤/印化官杀)=印在做功路径上被财库制约 → 财库制印=管企业/企业之官.
        # 与 ㊻r 官杀制不尽当财互转(官杀→财), 本条为 财库/资产→权(企业之官).
        # 戌=财库(原书ch9"官库=戌", 戌亦为财库), 财库藏干含印(戌藏辛丁戊, 辛=印类)
        cai_ku_zhi_yin = False
        yin_eff_off = any(
            ("印制食伤" in m or "印化官杀" in m)
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        )
        # ch9 财库制印=企业之官: 戌(XU)在局 + 印星在做功路径上EFFECTIVE(印制食伤/印化官杀)
        # "财库制印"=戌库收印(财库=股权/资产, 制印=管企业), 非"财星制印"(财制印是另一口径, 不在此)
        if yin_eff_off and "XU" in branches:
            cai_ku_zhi_yin = True
        # ㊻s6 牢 狱 域 方 向: 罪 犯 结 构 非 UNDETERMINED = 有 牢 狱 信 号(凶);
        # UNDETERMINED = 无 明 确 牢 狱 结 构(中 性), 不 轻 判 吉/凶.
        # ch12 罪 犯 结 构 四 类 + 以 阴 灭 阳 + 反 局 辰 丑 = 有 刑 伤/牢 狱 风 险.
        crime_direction = (
            "NEGATIVE" if result.crime_structure != "UNDETERMINED" else "NEUTRAL"
        )
        # ch1 方位法则消费: 日干合年月官=我管他(管理权), 合时上官=他管我(头脑被控制).
        # 合时上官(主位官)=头脑被管→官域"受控"(工作受上级/体制约束, 管理幅度受限);
        # 合年月官(宾位官)=我管他→官域"管理权"(管理他人/下级). 仅当合官 EFFECTIVE 时消费.
        guan_he_fangwei = getattr(result, "guan_he_fangwei", "UNDETERMINED")
        he_guan_eff = any(
            m in ("合正官", "合七杀") and a == ZuoGongAttribution["EFFECTIVE"]
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
        )
        if guan_he_fangwei == "TAGUAN_WO" and he_guan_eff:
            guan_he_eff = True   # 合时上官且有效=头脑被控制(受控)
        elif guan_he_fangwei == "WOGUAN_TA" and he_guan_eff:
            guan_he_eff = False  # 合年月官且有效=我管他(管理权)
        else:
            guan_he_eff = None   # UNDETERMINED
        # ch9 官域消费 L1 势方向(原书 ch9"官杀主职务+印主权柄, 必须有根; 官杀虚透=名气"
        # + ch8 衔接"官杀制不尽当财看"): 势方向 shi_controlled 含 官杀星五行(克日主=官杀)
        # = 势"去制官杀" = 官星被制方向(官权受势/制不尽当财看); 势去制非官杀相关=不消费势.
        # ㊻s88 P1 域层接线: 官域此前各判各的, 未接 L1 势向.
        _guan_el_off = next((e for e, c in CONTROLS.items() if c == STEM_ELEMENT.get(day_master, "")), "")
        _sh_ctrl_off = list(getattr(result, "shi_controlled", []) or [])
        _shi_zhiguanxiang_out = "SHI_ZHIGUAN" if (_guan_el_off and _guan_el_off in _sh_ctrl_off) else "UNDETERMINED"
        result.official_event_structure = {
            "officer_present": str(officer_present),
            "officer_controlled": str(controlled),
            "control_completeness": result.control_completeness,
            "official_state": official_state,
            "cai_ku_zhi_yin": "TRIGGERED" if cai_ku_zhi_yin else "UNDETERMINED",
            # ch1 方位法则: 合时上官=受控(他管我) / 合年月官=管理权(我管他)
            "guan_he_fangwei": guan_he_fangwei if guan_he_fangwei != "UNDETERMINED" else "UNDETERMINED",
            "guan_he_consume": "SUKONG" if guan_he_eff is True else ("MANLI" if guan_he_eff is False else "UNDETERMINED"),
            # ch9/ch8 衔接: 势去制官杀=官星被制方向(制不尽当财看)
            "shi_zhiguanxiang": _shi_zhiguanxiang_out,
            "crime_direction": "NEUTRAL",
            # ch12 牢域 L1 势向: 势去制官杀(法/秩序被势)= 牢狱/犯罪风险方向
            # (ch12"反局结构主牢狱" + ch1"势=定局根本"; ㊻s91 P1 域层接线)
            "shi_zhiguan_shi_fawu": _shi_zhiguanxiang_out,   # 官杀=法/秩序, 势去制=秩序被势=牢狱方向
        }
        result.rules_triggered.append("EVT-OFFICIAL-001")

    # ── V3.6.9 §65 父母系统（原书 L1875 "正偏财为父, 官杀为父; 食/伤/禄为母; 印=父母星"）──
    # 盲派父母取法: 父=偏财(男)/正印(女, 印为父母星通论), 母=正印(男)/偏财(女, 食伤/禄为母)。
    # 简化枚举(全布尔/枚举, 无吉凶): 父星/母星 present + weakened + 年柱(祖上宫)被伤 → 父母状态。
    # 定位: 父=偏财, 母=正印(原书 L1875 通论"印是父母星"); 食伤/禄=母(女命)。
    def _resolve_parental_structure(self, chart, result, day_master):
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        stems = [
            chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
            chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
        ]
        # 父星=偏财, 母星=正印(原书通论; 女命父=正印母=偏财, 男命父=偏财母=正印, 通论取偏财/正印)
        father_star = "偏财"
        mother_star = "正印"
        f_stem = [st for st in stems if ten_god(day_master, st) == father_star]
        m_stem = [st for st in stems if ten_god(day_master, st) == mother_star]
        f_hidden = [b for b in branches
                    if any(ten_god(day_master, h) == father_star
                           for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))]
        m_hidden = [b for b in branches
                    if any(ten_god(day_master, h) == mother_star
                           for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))]
        father_present = bool(f_stem) or bool(f_hidden)
        mother_present = bool(m_stem) or bool(m_hidden)
        # 年柱(祖上宫)被冲/穿=父母缘浅
        year_br = chart.year_pillar.earthly_branch
        year_attacked = any(
            BRANCH_CHONG.get(b) == year_br or BRANCH_CHUAN.get(b) == year_br
            for b in branches if b != year_br
        )
        # 父星/母星 被克/穿(星弱=缘薄)
        father_weakened = any(
            resolve_branch_relation(b, ob, branches) in ("chong", "chuan", "po")
            for b in f_hidden for ob in branches if ob != b
        ) or (f_stem and any(
            ten_god(day_master, st) in GROUP_BI
            for st in stems if st != f_stem[0]
        ))
        mother_weakened = any(
            resolve_branch_relation(b, ob, branches) in ("chong", "chuan", "po")
            for b in m_hidden for ob in branches if ob != b
        )
        mother_weakened = any(
            resolve_branch_relation(b, ob, branches) in ("chong", "chuan", "po")
            for b in m_hidden for ob in branches if ob != b
        )
        # ── V3.6.9⑥ 父母星"克星"判据(原书通论"财克印=母缘薄, 比劫夺财=父缘薄")──
        # 母星=正印, 原局有财星(正财/偏财)=财克印=母缘薄; 父星=偏财, 原局有比劫=比劫夺财=父缘薄。
        # 财/比劫克星 present → 对应父母星判 WEAKENED(缘薄), 非 STRONG。
        # 这是原书"财克印母早丧/缘薄"的取值方向, 非吉凶评分(守 BLIND-G16)。
        cai_present = any(
            ten_god(day_master, st) in GROUP_CAI for st in stems
        ) or any(
            ten_god(day_master, h) in GROUP_CAI
            for b in branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        bi_present = any(
            ten_god(day_master, st) in GROUP_BI for st in stems
        ) or any(
            ten_god(day_master, h) in GROUP_BI
            for b in branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        # 父星弱判据(原局比劫 present=夺父财): 合并入 father_weakened
        father_weakened = father_weakened or bi_present
        # 母星弱判据(原局财 present=克母印): 合并入 mother_weakened
        mother_weakened = mother_weakened or cai_present
        # 枚举状态(全布尔): STRONG(星present且无弱/无克星) / WEAKENED(present但弱或克星) / ABSENT(不present)
        father_state = ("ABSENT" if not father_present
                        else "WEAKENED" if father_weakened else "STRONG")
        mother_state = ("ABSENT" if not mother_present
                       else "WEAKENED" if mother_weakened else "STRONG")
        result.parental_event_structure = {
            "father_star": father_star, "mother_star": mother_star,
            "father_present": str(father_present), "mother_present": str(mother_present),
            "father_state": father_state, "mother_state": mother_state,
            "palace_year_attacked": str(year_attacked),
            "caikprint": str(cai_present), "bijiechou": str(bi_present),
            "note": "原书L1875: 正偏财为父,食伤禄为母,印=父母星; 年柱=祖上宫被冲穿=缘薄; "
                    "财克印=母缘薄, 比劫夺财=父缘薄(V3.6.9⑥)",
        }
        result.rules_triggered.append("EVT-PARENTAL-001")

    def _resolve_occupation_candidate(self, chart, result, day_master):
        """职业系统（§63）。原书：职业不是十神单独决定；
        食伤制官→CONTROL_OFFICER_BY_FOOD_INJURY→再由象法映射职业候选。
        V3.5：OCCUPATION-IMAGE 已按古籍原文取证解锁部分映射（VERIFY-BLIND-003/004/005/007/020/026），
        仅收录有明文实例的 method→职业 映射；无明文仍 UNDETERMINED。"""
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        eff_methods = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        ]
        work_types = []
        if any(m in ('伤官制官', '食伤制杀') for m in eff_methods):
            work_types.append("CONTROL_OFFICER_BY_FOOD_INJURY")
        if '比劫制财' in eff_methods:
            work_types.append("CONTROL_WEALTH_BY_BIJIE")
        # 互动制财（命名双源：刑制X/刑X/穿制X/穿X/冲制X/合X；正财偏财全变体）
        if any(m in ('刑制偏财', '刑制正财', '刑偏财', '刑正财',
                     '穿制偏财', '穿制正财', '穿偏财', '穿正财',
                     '冲制偏财', '冲制正财', '冲偏财', '冲正财',
                     '合正财', '合偏财') for m in eff_methods):
            work_types.append("CONTROL_WEALTH_BY_INTERACTION")
        # 互动制官（命名双源，全变体）
        if any(m in ('刑制正官', '刑制七杀', '刑正官', '刑七杀',
                     '穿制正官', '穿制七杀', '穿正官', '穿七杀',
                     '冲制官杀', '冲正官', '冲七杀',
                     '合正官', '合七杀') for m in eff_methods):
            work_types.append("CONTROL_OFFICER_BY_INTERACTION")
        if '食伤生财' in eff_methods:
            work_types.append("GENERATE_WEALTH_BY_FOOD_INJURY")
        if '财制印' in eff_methods:
            work_types.append("CONTROL_RESOURCE_BY_WEALTH")
        if '印化官杀' in eff_methods:
            work_types.append("TRANSFORM_OFFICER_BY_RESOURCE")
        if '印制食伤' in eff_methods:
            work_types.append("CONTROL_FOOD_INJURY_BY_RESOURCE")
        if '官杀制比劫' in eff_methods:
            work_types.append("CONTROL_BIJIE_BY_OFFICER")
        if '食伤泄秀' in eff_methods:
            work_types.append("DRAIN_BY_FOOD_INJURY")
        if any(m in ('墓库收物', '冲开墓库') for m in eff_methods):
            work_types.append("STORE_BY_MUKU")
        # 宫位方向（主位=日时藏透财/官）
        day_branch = chart.day_pillar.earthly_branch
        hour_branch = chart.hour_pillar.earthly_branch
        toward = []
        for b, st in ((day_branch, chart.day_pillar.heavenly_stem),
                      (hour_branch, chart.hour_pillar.heavenly_stem)):
            if ten_god(day_master, st) in GROUP_CAI or any(
                    ten_god(day_master, h) in GROUP_CAI for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])):
                toward.append("TOWARD_WEALTH")
            if ten_god(day_master, st) in GROUP_GUAN or any(
                    ten_god(day_master, h) in GROUP_GUAN for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])):
                toward.append("TOWARD_OFFICIAL")
        # ── OCCUPATION-IMAGE 职业象映射（V3.5 解锁，仅收录古籍原文取证的映射）──
        # 原则：方法层→职业候选 必须逐条有盲派原文支撑，无明文=UNDETERMINED。
        #   制用五种·食伤制杀："主位卯穿制官星辰土→
        #           伤食制官局，命有官职；八字无财，以伤食当财富看→银行无疑"
        #   生用结构·食伤生财："时柱食神生财→食伤做功技术赚"
        #   化用结构·印化官杀："食神主技能、印主单位→技能被单位重用"
        #   官贵章·官星被劫财合走："官星被劫财合去→非我所有、做功无效"
        #   辰库口诀："辰库=银行、金融中心、巨大储蓄量"
        occ_names = []
        if "CONTROL_OFFICER_BY_FOOD_INJURY" in work_types:
            occ_names.append(("官职/公职", "制用五种·食伤制杀(伤食制官局,命有官职)"))
        if "GENERATE_WEALTH_BY_FOOD_INJURY" in work_types:
            occ_names.append(("技艺谋财", "生用结构·食伤生财(食伤做功技术赚)"))
        if "TRANSFORM_OFFICER_BY_RESOURCE" in work_types:
            occ_names.append(("单位文职", "化用结构·印化官杀(印主单位)"))
        # 互动制官：仅"互动+五行制"（刑制/穿制/冲制官）映射官职（卯穿制官
        # 辰=命有官职）；纯合官（合正官/合七杀）无明文不映射；官 DAMAGED 互斥
        # （子水穿未土官库=官根受损，制用五种·伤官去官）
        occ_off = result.official_event_structure or {}
        occ_official_state = occ_off.get("official_state", "UNDETERMINED")
        interaction_officer_with_control = any(
            m in eff_methods for m in (
                '刑制正官', '刑制七杀', '刑正官', '刑七杀',
                '穿制正官', '穿制七杀', '穿正官', '穿七杀',
                '冲制官杀', '冲正官', '冲七杀',
            )
        )
        if (interaction_officer_with_control
                and occ_official_state != "DAMAGED"):
            occ_names.append(("官职/公职", "制用五种·互动制官(命有官职)"))
        # ROBBED：官被劫财合走 → 非管理职/看守（官贵章：官星被劫财合走=非我所有）
        if occ_official_state == "ROBBED":
            occ_names.append(("非管理/看守", "官贵章(官被劫财合走,非我所有)"))
        # 墓库收物且官非ROBBED → 金融/银行，仅限辰库（辰库口诀"辰库=银行、
        # 金融中心、巨大储蓄量"；丑/未/戌库无明文，不映射=UNDETERMINED）
        has_chen = any(
            b == "CHEN" for b in (
                chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
            )
        )
        if ("STORE_BY_MUKU" in work_types and occ_official_state != "ROBBED"
                and has_chen):
            occ_names.append(("金融/银行", "辰库口诀(辰库=银行金融中心,巨大储蓄量)"))

        # V3.6.9㊱ ch9 官命部门定位（原书 ch9"部门定位法"，逐条有原文明文支撑）：
        # ① 申酉做功→检察/法院/法律（原书"申酉=法律公检"）
        # ② 申酉丑寅组合→公安部门（原书"申酉丑寅=公安系统"）
        # ③ 刃+杀→执法/实权/军队（原书"刃=枪、杀=权，三象共出断公安系统"）
        # ④ 伤官旺→文官/文化（原书"伤食旺=文化或文官"）
        # ⑤ 官杀配伤食(贼捕结构)→纪检/实权（原书"伤食制官杀=贼捕=纪检"）
        all_branches_list = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        all_branches_set = set(all_branches_list)
        # ① 申酉做功(㊻w 修复: 原判据仅限伤官制官/食伤制杀/印化官杀三条EFFECTIVE, 过严;
        #    原书ch9 L12"申酉做功→检察法院法律", 做功=官杀/印星/伤食/制官类方法与申酉交互, 不限三条;
        #    且申支类象本身=法律/公家(原书ch3"申=法律"), 申酉在局+官职/公职已有命中=申酉做办公检法结构)
        _shen_you_zuogong = any(
            m in ('伤官制官', '食伤制杀', '印化官杀',
                 '穿制正官', '穿制七杀', '刑制正官', '刑制七杀',
                 '冲制官杀', '冲正官', '冲七杀', '比劫制财',
                 '墓库收物', '官杀制比劫')
            for m in eff_methods
        )
        _has_guan_official = any(n == "官职/公职" for n, _e in occ_names)
        _shen_you_in = "SHEN" in all_branches_set or "YOU" in all_branches_set
        # ㊻w: 申酉在局即含法律类象(原书ch3"申=法律, 酉=法律"), 不论做功方法, 只要申酉在局即加"公检法/法律"类象
        # 与"官职/公职"并行(部门定位是结构事实, 不影响吉凶方向), 但需申酉在局
        if _shen_you_in:
            _ev = "ch9部门定位法(申酉做功→检察法院法律, ㊻w放宽: 制官类方法或官职公职+申酉在局)"
            if _shen_you_zuogong:
                _ev = "ch9部门定位法(申酉做功→检察法院法律, ㊻w: 有官杀/印/制官方法EFFECTIVE+申酉在局)"
            elif _has_guan_official:
                _ev = "ch9部门定位法(申酉做功→检察法院法律, ㊻w: 官职/公职+申酉在局=公检法结构)"
            else:
                _ev = "ch3类象(申=法律/公家, 酉=法律, ㊻w: 申酉在局本身含法律类象)"
            occ_names.append(("公检法/法律", _ev))
        # ② 申酉丑寅组合→公安
        if any(b in ("SHEN", "YOU", "CHOU", "YIN") for b in all_branches_set) \
                and len([b for b in all_branches_set if b in ("SHEN", "YOU", "CHOU", "YIN")]) >= 2 \
                and occ_official_state not in ("ROBBED", "DAMAGED"):
            occ_names.append(("公安/执法", "ch9部门定位法(申酉丑寅组合→公安部门)"))
        # ③ 刃+杀→军警执法(三象共出: 阳刃支存在 + 七杀做功 + 官非ROBBED/DAMAGED)
        # V3.6.9㊻i ch4 三象共出修正: 原查eff_methods含"阳刃"字符串(从不命中),
        # 改为查排盘层shensha中阳刃支存在(branches含YANG_REN) + 做功层有杀相关方法
        yang_ren_b = [b for b in branches if b in getattr(chart, 'shensha', {}).get('YANG_REN', [])]
        has_sha_zuogong = any(
            any(c in m for c in ("杀", "七杀")) for m in eff_methods
        )
        if yang_ren_b and has_sha_zuogong \
                and occ_official_state not in ("ROBBED", "DAMAGED"):
            occ_names.append(("军警/执法", "ch4三象共出(阳刃+七杀做功=枪+权→公检法/军警执法)"))
        # ④ 伤官旺→文官/文化（原书"伤食旺=文化或文官"）
        # V3.6.9㊻i 修正: 原查 work_types 含"食伤泄秀"(实为枚举名 DRAIN_BY_FOOD_INJURY, 从不命中)
        if "DRAIN_BY_FOOD_INJURY" in work_types and occ_official_state not in ("ROBBED", "DAMAGED"):
            occ_names.append(("文官/文化", "ch4伤官泄刃(伤食旺→文化或文官, 原书'伤官泄了羊刃主文笔')"))
        # ⑤ 贼捕结构(伤食制杀=捕杀重贼轻)→纪检
        if "食伤制杀" in " ".join(eff_methods) and occ_official_state != "ROBBED":
            occ_names.append(("纪检/实权", "ch9贼捕结构(伤食制杀=贼捕→纪检)"))
        # ⑥ 食神合印(佩印)→思想文化(原书ch9 L16"食神合印(佩印)→思想文化行业")
        # 食神/伤官在EFFECTIVE + 印星(正印/偏印)在局(藏干含印) = 食神配印结构, 主思想文化/教育
        _yin_stems = [
            s for p in ("year_pillar", "month_pillar", "day_pillar", "hour_pillar")
            for s in [getattr(chart, p).heavenly_stem]
            if ten_god(day_master, s) in ("正印", "偏印")
        ]
        _yin_in = any(
            ten_god(day_master, h) in ("正印", "偏印")
            for b in (chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                      chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch)
            for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        _shishen_eff = any(m in ("食伤生财", "食伤泄秀", "食伤制官", "伤官制官", "食神生财") for m in eff_methods)
        if _shishen_eff and _yin_in and occ_official_state not in ("ROBBED", "DAMAGED"):
            occ_names.append(("思想文化/教育", "ch9食神合印佩印(食神做功+印星在局=思想文化行业, 原书'食神合印→思想文化')"))

        # V3.6.9㊳ ch8 取财方式四分(原书ch8"取财方法: 经营/风险/工薪/打工"):
        # ① 经营取财 = 食伤生财(内食神格做企业)或食伤配官杀(伤食配官杀=多种经营)
        # ② 风险取财 = 比劫制财(劫财做功主风险投资), 原局有丑=赌博, 无=炒股
        # ③ 工薪取财 = 官配印(官杀配印/印做功, 上班体制内)
        # ④ 打工取财 = 食入官库(食伤入官库=给人打工当经理)
        # ㊻d 修: 原查 work_types(枚举名)判据过严(UNDET 153 例), 改查 eff_methods(方法名)
        all_branches_set = set([
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ])
        wealth_style = []
        if "食伤生财" in eff_methods:
            wealth_style.append("经营取财")
        if "比劫制财" in eff_methods:
            wealth_style.append("风险取财_赌博" if "CHOU" in all_branches_set else "风险取财_炒股")
        # ㊻d: 工薪取财=官杀配印(印化官杀/官杀制比劫EFFECTIVE+印在局=体制内工薪)
        if "印化官杀" in eff_methods or "官杀制比劫" in eff_methods:
            wealth_style.append("工薪取财")
        # ㊻d: 打工取财=食伤入官库(食伤泄秀/食伤生财EFFECTIVE+官库在局=给人打工当经理)
        muku_in_set = any(b in ("CHEN","XU","CHOU","WEI") for b in all_branches_set)
        if ("食伤泄秀" in eff_methods or "食伤生财" in eff_methods) and muku_in_set:
            wealth_style.append("打工取财")
        wealth_style = wealth_style or ["UNDETERMINED"]

        occ_uniq = []
        for n, e in occ_names:
            if n not in [x[0] for x in occ_uniq]:
                occ_uniq.append((n, e))
        result.occupation_candidate = {
            "work_types": list(dict.fromkeys(work_types)) or ["UNDETERMINED"],
            "palace_direction": list(dict.fromkeys(toward)) or ["UNDETERMINED"],
            "occupation_names": [{"name": n, "evidence": e} for n, e in occ_uniq],
            "occupation_name": "、".join(n for n, _e in occ_uniq) or "UNDETERMINED",
            "wealth_style": wealth_style,
            "yima_branches": result.yima_branches,
            "xunkong_branches": result.xunkong_branches,
            "education_level": result.education_level,
            "education_evidence": result.education_evidence,
            "education_field": result.education_field,
            "education_field_evidence": result.education_field_evidence,
            "crime_structure": result.crime_structure,
            "crime_evidence": result.crime_evidence,
            "release_path": result.release_path,
            "day_master_personality": result.day_master_personality,
            "day_master_personality_evidence": result.day_master_personality_evidence,
            "xingqi_cycle": result.xingqi_cycle,
            "xingqi_cycle_evidence": result.xingqi_cycle_evidence,
            "wuji_kai_ku": result.wuji_kai_ku,
            "wuji_kai_ku_evidence": result.wuji_kai_ku_evidence,
            "shi_direction": result.shi_direction,
            "shi_strength": result.shi_strength,
            "shi_zhi_jing": result.shi_zhi_jing,
            "shi_party": result.shi_party,
            "shi_controlled": result.shi_controlled,
            "shi_evidence": result.shi_evidence,
            "guan_he_fangwei": result.guan_he_fangwei,
            "space_palace": result.space_palace,
            "space_dynamic": result.space_dynamic,
            "car_signal": result.car_signal,
            "interpersonal_structure": result.interpersonal_structure,
            "interpersonal_evidence": result.interpersonal_evidence,
            "mingqi_structure": result.mingqi_structure,
            "mingqi_evidence": result.mingqi_evidence,
            "xingxing_cheganshen": result.xingxing_cheganshen,
            "xingxing_evidence": result.xingxing_evidence,
            "fufen_structure": result.fufen_structure,
            "fufen_evidence": result.fufen_evidence,
            "kk_shixiang": result.kk_shixiang,
            "kk_wuxu": result.kk_wuxu,
            "menhu_trading": result.menhu_trading,
            "fugong_palace": result.fugong_palace,
            "wulei_shen": result.wulei_shen,
            "tone_char": result.tone_char,
            "shensha_leixiang": result.shensha_leixiang,
            "xinkong_evidence": result.xinkong_evidence,
            "status": "CANDIDATE" if work_types else "UNDETERMINED",
        }
        result.rules_triggered.append("EVT-OCCUPATION-001")

    def _resolve_root_provenance(self, chart, result, day_master):
        """寻根溯源（段建业哈尔滨讲义：宾主体用后先找财官根在哪柱，定我家他家）。

        规则：
        - 我宫(主) = DAY/HOUR 柱；他宫(宾) = YEAR/MONTH 柱
        - 财星 = 日主所克五行；官杀 = 克日主五行
        - 某财/官五行藏在某柱地支藏干中（主/中/余气任一）= 该财/官根在该柱
        - 根在他家(YEAR/MONTH) = 公家/外人的财官；根在我家(DAY/HOUR) = 自己的财官
        输出 result.root_provenance = {ten_god: [{root_branch, pillar, owner}]}
        """
        # 五行生克
        dm_el = STEM_ELEMENT[day_master]
        # 五行相克：木克土、土克水、水克火、火克金、金克木
        KE = {"WOOD":"EARTH","EARTH":"WATER","WATER":"FIRE","FIRE":"METAL","METAL":"WOOD"}
        cai_el = KE[dm_el]                          # 我克者=财（如土克水）
        guan_el = [k for k,v in KE.items() if v == dm_el][0]  # 克我者=官杀（如木克土）


        pillars = {"year": chart.year_pillar.earthly_branch,
                   "month": chart.month_pillar.earthly_branch,
                   "day": chart.day_pillar.earthly_branch,
                   "hour": chart.hour_pillar.earthly_branch}
        hidden = chart.hidden_stems  # {'year':{'main':..,'middle':..,'residual':..},..}
        my_home = {"day", "hour"}

        prov = {}
        for ten_god_label, target_el in (("财", cai_el), ("官杀", guan_el)):
            roots = []
            for pl in ("year","month","day","hour"):
                hs = hidden.get(pl, {})
                for pos in ("main","middle","residual"):
                    stem = hs.get(pos)
                    if stem and STEM_ELEMENT.get(stem) == target_el:
                        roots.append({
                            "root_branch": pillars[pl],
                            "pillar": pl.upper(),
                            "owner": "HOST" if pl in my_home else "GUEST",
                        })
                        break  # 一柱一根即可
            if roots:
                prov[ten_god_label] = roots
        result.root_provenance = prov
        result.rules_triggered.append("BLIND-ROOT-PROVENANCE-001")

    def _resolve_education_level(self, chart, result, day_master):
        """ch11 学历判定(原书ch11"三神三破神 + 制了啥啥就好").
        三神(官杀/印/食神)=学历之神; 三破神(财/伤官/比劫)=破坏学历之神.
        ㊻s117 ch11 收敛: 原书 L4 "制了啥啥就好 — 杀制尽伤食=数学博士; 伤官无制=聪明但
        学历不高; 印不做功=懒惰不开化" 只有 有无学历+层次(高/低/无) 口径, 无 本科/高中
        精确分档(原判据 7 处"本科"为引擎发明, 无 ch 支撑). 收敛 3 枚举:
          HIGHER_EDU(高学历: 三神齐功/双神功 = 原书 博士/硕士 例)
          BASIC_EDU (有学历: 单神功/泄秀 = 原书"有学历"档, 不精确到本科)
          NO_EDU    (无学历: 印不做功/财破印/伤官无制 = 原书"懒惰不开化/学历不高/中途中断")
          UNDETERMINED(印无做功且无破神 = 学历象未明)
        原 博士/硕士 细分保留在 education_evidence(判据说明), education_level 只出层次档."""
        # 三神(官杀/印/食神)=学历之神; 三破神(财/伤官/比劫)=破坏学历之神.
        eff_methods_list = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        ]
        edu_evidence = []
        shishang_zhisha = "食伤制杀" in eff_methods_list
        yin_zhi_shishang = "印制食伤" in eff_methods_list
        yin_hua_guansha = "印化官杀" in eff_methods_list
        shishang_xiexiu = "食伤泄秀" in eff_methods_list
        cai_zhi_yin = "财制印" in eff_methods_list
        shangguan_wu_zhi = (shishang_xiexiu and not yin_zhi_shishang and not shishang_zhisha)
        # ㊻s117 高学历档(原书 博士/硕士 例): 杀印伤三功 或 双神功
        if shishang_zhisha and yin_zhi_shishang and yin_hua_guansha:
            result.education_level = "HIGHER_EDU"
            edu_evidence.append("ch11三神齐功: 食伤制杀+印制食伤+印化官杀=学者型高学历(数学博士例)")
        elif shishang_zhisha and yin_zhi_shishang:
            result.education_level = "HIGHER_EDU"
            edu_evidence.append("ch11双神功: 食伤制杀+印制食伤=学业有成(硕士例)")
        elif yin_hua_guansha and yin_zhi_shishang:
            result.education_level = "HIGHER_EDU"
            edu_evidence.append("ch11双神功: 印化官杀+印制食伤=学业有成(硕士例)")
        # ㊻s117 有学历档(原书"有学历", 不精确到本科): 单神功/泄秀/印制食伤
        elif yin_zhi_shishang and shishang_xiexiu:
            result.education_level = "BASIC_EDU"
            edu_evidence.append("ch11印制食伤+食伤泄秀=有学历(中等档)")
        elif "食伤生财" in eff_methods_list:
            result.education_level = "BASIC_EDU"
            edu_evidence.append("ch11食伤生财: 食伤做功有成=有学历基础")
        elif "食伤制杀" in eff_methods_list:
            result.education_level = "BASIC_EDU"
            edu_evidence.append("ch11食伤制杀单功: 有制杀之功=学业有成")
        elif "印化官杀" in eff_methods_list:
            result.education_level = "BASIC_EDU"
            edu_evidence.append("ch11印化官杀单功: 官配印=学业有成")
        elif "印制食伤" in eff_methods_list:
            result.education_level = "BASIC_EDU"
            edu_evidence.append("ch6/ch11印做功用单功: 印=学位/学术类象, 有学历基础")
        # ㊻s117 无学历档(原书"无学历/学历不高/中途中断"): 伤官无制/财破印
        elif shangguan_wu_zhi:
            result.education_level = "NO_EDU"
            edu_evidence.append("ch11伤官无制: 聪明但学历不高(伤官太旺无印制=中途中断学历)")
        elif cai_zhi_yin:
            result.education_level = "NO_EDU"
            edu_evidence.append("ch11财破印: 财制印=欲望大, 学不进去(学历受损)")
        else:
            result.education_level = "UNDETERMINED"
            edu_evidence.append("ch11无三神做功/无破神: 学历象未明")
        # ch11 学域消费 L1 势方向(原书 ch11"三破神含财=欲望(破学业)" + ch1"势=定局根本"):
        # 势方向 shi_controlled 含 财星五行(日主所克)= 势"去制财"(破学业欲望) 或
        # 势去制 官杀(身受损, 学业受阻). ㊻s91 P1 域层接线: 学域此前各判各的, 未接 L1 势向.
        _cai_el_edu = CONTROLS.get(STEM_ELEMENT.get(day_master, ""), "")
        _guan_el_edu = next((e for e, c in CONTROLS.items() if c == STEM_ELEMENT.get(day_master, "")), "")
        _sh_ctrl_edu = list(getattr(result, "shi_controlled", []) or [])
        if _cai_el_edu and _cai_el_edu in _sh_ctrl_edu:
            _shi_xueyi_out = "SHI_ZHICAI_HUO_XUEYE"
        elif _guan_el_edu and _guan_el_edu in _sh_ctrl_edu:
            _shi_xueyi_out = "SHI_ZHIGUAN_SHA_SHOU_SHANG"
        else:
            _shi_xueyi_out = "UNDETERMINED"
        # ㊻s124 ch11 学业颗粒度: 学中断(伤官太旺无制中断, 八字有官后补; 原书 L24)
        _zd_ev: List[str] = []
        if shishang_xiexiu and not yin_zhi_shishang and not shishang_zhisha:
            # 伤官太旺无印制 = 中途中断学历
            _guan_in_bureau = any(ten_god(day_master, st) in ("正官", "七杀")
                                  for st in (chart.year_pillar.heavenly_stem,
                                              chart.month_pillar.heavenly_stem,
                                              chart.hour_pillar.heavenly_stem))
            if _guan_in_bureau:
                result.edu_zhongduan = "HOU_BU"
                _zd_ev.append("ch11 伤官太旺无制=中途中断学历; 八字有官=后补文凭(原书L24)")
            else:
                result.edu_zhongduan = "ZHONGDUAN"
                _zd_ev.append("ch11 伤官太旺无制且八字无官=中途中断学历不补(原书L24)")
        else:
            result.edu_zhongduan = "UNDETERMINED"
            _zd_ev.append("ch11 伤官非太旺/有印制/无伤官=学中断象未坐实")
        result.edu_zhongduan_evidence = _zd_ev
        result.education_evidence = edu_evidence
        result.shi_xueyi_xiang = _shi_xueyi_out   # ch11 学域 L1 势向(势去制财=欲望破学业/势去制官杀=学业受阻)

    def _resolve_education_field(self, chart, result, day_master):
        """ch3 支主学科分流(原书ch3"支主学科: 金水主理, 木火主文, 戌亥=数学, 丑=玄学, 申酉=法律, 辰=化学").
        判据(基于日主五行 + 原局地支):
        ① 金水主理: 日主属金水(庚辛壬癸) → 理科
        ② 木火主文: 日主属木火(甲乙丙丁) → 文科
        ③ 戌亥=数学: 原局戌/亥 present + 日主金水 → 数学
        ④ 丑=玄学: 原局丑 present + 印星做功用(印制食伤/印化官杀) → 玄学
        ⑤ 申酉=法律: 原局申酉 present + 官杀做功(官杀制比劫/伤官制官) → 法律
        ⑥ 辰=化学: 原局辰 present + 子辰半合水局 → 化学
        优先级: 戌亥数学 > 申酉法律 > 丑玄学 > 辰化学 > 金水理科 > 木火文科"""
        dm_el = STEM_ELEMENT[day_master]
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        eff_methods_list = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        ]
        has_xu = "XU" in branches
        has_hai = "HAI" in branches
        has_chou = "CHOU" in branches
        has_shen = "SHEN" in branches
        has_you = "YOU" in branches
        has_chen = "CHEN" in branches
        has_zi = "ZI" in branches
        jinsui = dm_el in ("METAL", "WATER")
        muhuo = dm_el in ("WOOD", "FIRE")
        guan_sha_eff = "官杀制比劫" in eff_methods_list or "伤官制官" in eff_methods_list
        yin_eff = "印制食伤" in eff_methods_list or "印化官杀" in eff_methods_list
        # ㊻s101 ch3 L20 金融分流: 申present(非酉)+财星做功=金融(申主金融); 酉(非申)+官杀做功=法律(酉不主金融)
        _cai_eff = "财制比劫" in eff_methods_list or "伤官生财" in eff_methods_list or "官杀当财" in eff_methods_list

        field_evidence = []
        # ③ 戌亥=数学(原书"戌亥主计算/运算")
        if (has_xu or has_hai) and jinsui:
            result.education_field = "数学"
            field_evidence.append("ch3支主学科: 戌亥present+日主金水=数学(戌亥主计算运算)")
        # ㊻s101 ch3 L20 金融分流(原书"申酉主法律, 申还主金融, 酉不主"):
        # 申present(非酉)+财星做功=金融(申主金融); 酉(非申)+官杀做功=法律(酉主法律/技术/玄学, 不主金融)
        elif has_shen and _cai_eff and not has_you:
            result.education_field = "金融"
            field_evidence.append("ch3支主学科: 申present+财星做功=金融(申主金融, 酉不主)")
        # ⑤ 酉=法律(原书"酉主法律/技术/玄学, 不主金融")
        elif has_you and guan_sha_eff:
            result.education_field = "法律"
            field_evidence.append("ch3支主学科: 酉present+官杀做功=法律(酉主法律/技术/玄学)")
        # ⑤ 申=法律(原书"申主法律")
        elif has_shen and guan_sha_eff:
            result.education_field = "法律"
            field_evidence.append("ch3支主学科: 申present+官杀做功=法律(申主法律)")
        # ④ 丑=玄学(原书"丑主玄学")
        elif has_chou and yin_eff:
            result.education_field = "玄学"
            field_evidence.append("ch3支主学科: 丑present+印星做功=玄学(丑主玄学)")
        # ⑥ 辰=化学(原书"辰见子为化学")
        elif has_chen and has_zi:
            result.education_field = "化学"
            field_evidence.append("ch3支主学科: 辰+子present=化学(辰见子为化学)")
        # ① 金水主理(原书"金水主理")
        elif jinsui:
            result.education_field = "理科"
            field_evidence.append("ch3支主学科: 日主金水=理科(金水主理)")
        # ② 木火主文(原书"木火主文")
        elif muhuo:
            result.education_field = "文科"
            field_evidence.append("ch3支主学科: 日主木火=文科(木火主文)")
        else:
            result.education_field = "UNDETERMINED"
        # 存入 result(兼容 education_field_evidence 字段)
        result.education_field_evidence = field_evidence

    def _resolve_day_master_personality(self, chart, result, day_master):
        """ch14 日主性格五行特性(原书ch14"日主性格断法: 甲怕金/乙喜金克成器/丙怕焚/丁喜旺主玄学/金主杀头形之成/水主智谋任性/木主仁慈柔韧/土主忠厚老成/金主刚强/水主聪明机敏").
        判据: 基于日主天干 + 原局地支藏干 + 做功层十神:
        ① 甲(木阳): 怕金(原局申酉present=金旺克甲, 需火制金/土生木化解)
        ② 乙(木阴): 喜金克成器(原局庚金present=金克乙, 乙木成器)
        ③ 丙(火阳): 怕焚(原局木旺=过旺, 需水制)
        ④ 丁(火阴): 喜旺主玄学(原局丁火present≥2=旺, 丁多=神秘之字)
        ⑤ 戊己(土): 忠厚老成(无特殊口经=默认)
        ⑥ 庚辛(金): 刚强/形之成/杀头(原局金旺=刚强)
        ⑦ 壬(水阳): 智谋任性(原局水旺=任性)
        ⑧ 癸(水阴): 聪明机敏(原局水旺=机敏)"""
        dm = day_master
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        stems = [
            chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
            chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
        ]
        # 查 原 局 各 五 行 present(支 藏 干 + 透 干)
        has_shen = "SHEN" in branches
        has_you = "YOU" in branches
        has_jin = has_shen or has_you or any(s in ("GENG", "XIN") for s in stems)
        has_mu = any(b in ("YIN", "MAO") for b in branches) or any(s in ("JIA", "YI") for s in stems)
        has_shui = any(b in ("ZI", "HAI") for b in branches) or any(s in ("REN", "GUI") for s in stems)
        has_bing = "BING" in stems or "SI" in branches or "WU" in branches
        has_ding = "DING" in stems
        dcount = stems.count("DING") + sum(1 for b in branches if b == "WU")
        evidence = []
        if dm == "JIA":
            result.day_master_personality = "甲木宽仁磊落"
            if has_jin:
                result.day_master_personality += "+甲怕金(原局金旺克甲, 需火制金化解)"
                evidence.append("ch14日主性格: 甲日主+原局金present=甲怕金(原书'甲最怕金怕外来力量侵害')")
            else:
                evidence.append("ch14日主性格: 甲日主(宽仁磊落, 直, 肝胆)")
        elif dm == "YI":
            result.day_master_personality = "乙木朴实柔情"
            if has_jin:
                result.day_master_personality += "+乙喜金克成器(金克乙成器)"
                evidence.append("ch14日主性格: 乙日主+原局金present=乙喜金克成器(原书'乙日主喜金克, 克才能成器')")
            else:
                evidence.append("ch14日主性格: 乙日主(朴实柔情, 曲, 颈脊)")
        elif dm == "BING":
            result.day_master_personality = "丙火激情多言"
            if has_mu:
                result.day_master_personality += "+丙怕焚(木旺过旺, 需水制)"
                evidence.append("ch14日主性格: 丙日主+原局木旺=丙怕焚(原书'丙日主最怕焚, 过旺需水制')")
            else:
                evidence.append("ch14日主性格: 丙日主(太阳/激情多言, 大, 眼脑)")
        elif dm == "DING":
            result.day_master_personality = "丁火文雅多思"
            if dcount >= 2:
                result.day_master_personality += "+丁喜旺主玄学(丁多=神秘之字)"
                evidence.append("ch14日主性格: 丁日主+丁present≥2=丁喜旺主玄学(原书'丁是神秘之字, 天干中丁越多越好')")
            else:
                evidence.append("ch14日主性格: 丁日主(星灯/文化/玄学, 小, 心/血管)")
        elif dm in ("WU", "JI"):
            result.day_master_personality = "戊己忠厚老成"
            evidence.append(f"ch14日主性格: {dm}日主(大地/山丘/政府/忠厚老成, 方, 鼻/胃)")
        elif dm in ("GENG", "XIN"):
            result.day_master_personality = "庚辛刚强暴躁"
            if has_jin:
                result.day_master_personality += "+金旺主杀头形之成"
                evidence.append("ch14日主性格: 庚辛日主+原局金present=刚强(原书'金主杀头/形之成, 不必考虑旺衰, 关键是如何去用')")
            else:
                evidence.append("ch14日主性格: 庚辛日主(顽铁/刚强, 棱角, 大肠/骨骼)")
        elif dm == "REN":
            result.day_master_personality = "壬水智谋任性"
            if has_shui:
                result.day_master_personality += "+水旺任性"
                evidence.append("ch14日主性格: 壬日主+原局水present=智谋任性(原书'壬主智谋任性, 形无规则')")
            else:
                evidence.append("ch14日主性格: 壬日主(海/江河/航运, 无规则, 膀胱/血液)")
        elif dm == "GUI":
            result.day_master_personality = "癸水聪明机敏"
            if has_shui:
                result.day_master_personality += "+水旺机敏"
                evidence.append("ch14日主性格: 癸日主+原局水present=聪明机敏(原书'癸主聪明机敏, 形圆润')")
            else:
                evidence.append("ch14日主性格: 癸日主(雨露/泉/泪/玄学, 圆润, 肾/脑)")
        result.day_master_personality_evidence = evidence

    def _resolve_xingqi_cycle(self, chart, result, day_master):
        """ch14 形气循环(原书ch14"辰戌同见=生死起灭/辰=形之初/戌=气始收/六壬辰戌结构有屠宰场含义").
        判据: 原局辰+戌同时present → 形气循环(生死起灭/屠宰场象)."""
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        has_chen = "CHEN" in branches
        has_xu = "XU" in branches
        if has_chen and has_xu:
            result.xingqi_cycle = "CHEN_XU_TONGJIAN"
            result.xingqi_cycle_evidence = [
                "ch14形气循环: 辰戌同见=生死起灭(原书'辰戌同见=生死起灭/六壬辰戌结构有屠宰场含义')"
            ]
        else:
            result.xingqi_cycle = "UNDETERMINED"
            result.xingqi_cycle_evidence = []

    def _resolve_wuji_kai_ku(self, chart, result, day_master):
        """ch13 戊己土开库法则(原书ch13"戊开戌辰[形→气], 己开丑未[气→形], 方向相反").
        ㊻m 修 2: 原 判 据 仅 日 主=戊/己(㊻f 初 建), UNDET=229/234 过 严;
        原 书 ch13 L24'戊 己 土 开 库'通 论: 任 何 日 主 局 中 有 戊 或 己(天 干 透 或 藏 干 含)+
        对 应 库 支 在 局+ 冲 库/刑 库/开 库 EFFECTIVE = 戊 己 开 库 口 径 成 立.
        判 据:
        ① 戊 开 戌 辰(形→气): 原 局 有 戊(天 干 或 藏 干)+ 戌/辰 在 局+ 冲 库 EFFECTIVE
        ② 己 开 丑 未(气→形): 原 局 有 己(天 干 或 藏 干)+ 丑/未 在 局+ 冲 库 EFFECTIVE
        未 成 立 → UNDETERMINED(不 开 库)."""
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        all_stems = [
            chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
            chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
        ]
        # ㊻m: 局 中 有 戊/己(天 干 透 或 藏 干 含)
        wu_present = ("WU" in all_stems or
                      any(h == "WU" for b in branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])))
        ji_present = ("JI" in all_stems or
                      any(h == "JI" for b in branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])))
        eff_methods_list = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        ]
        has_kai_ku = ("冲开墓库" in eff_methods_list or "冲开" in eff_methods_list
                      or "刑库" in " ".join(result.zuo_gong_methods)
                      or "开库" in " ".join(eff_methods_list))
        # 戊 开 戌 辰(形→气)
        if wu_present and ("XU" in branches or "CHEN" in branches) and has_kai_ku:
            result.wuji_kai_ku = "WU_KAI_XU_CHEN"
            result.wuji_kai_ku_evidence = [
                f"ch13戊己开库: 戊在局({ '天干' if 'WU' in all_stems else '藏干'})+"
                f"戌/辰在局+开库EFFECTIVE=形→气(戊开戌辰)"
            ]
        # 己 开 丑 未(气→形)
        elif ji_present and ("CHOU" in branches or "WEI" in branches) and has_kai_ku:
            result.wuji_kai_ku = "JI_KAI_CHOU_WEI"
            result.wuji_kai_ku_evidence = [
                f"ch13戊己开库: 己在局({ '天干' if 'JI' in all_stems else '藏干'})+"
                f"丑/未在局+开库EFFECTIVE=气→形(己开丑未)"
            ]
        else:
            result.wuji_kai_ku = "UNDETERMINED"
            result.wuji_kai_ku_evidence = []

    def _resolve_shi_direction(self, chart, result, day_master):
        """ch1 定势 (原书"势: 原局五行成势去谁, 定局的根本"; patterns 模式1"势=数量+位置+生克, 非单一旺衰").

        V3.6.9㊻s88 原著口径修正 (㊻s86 三处不准/自造全部对齐原著, 不新增自造规则):
          ① 土分燥湿 (㊻s86 缺失): 燥土 DRY_EARTH(戌/未) 归火土燥势, 湿土 WET_EARTH(辰/丑)
            归金水湿势 —— 引擎已有 DRY_EARTH_BRANCHES/WET_EARTH_BRANCHES 常量 (㊻s 燥土脆金), 定势直接用。
            原书 ch8"火土燥势"=火+燥土(戌未), ch9"金水湿土成势"=金水+湿土(辰丑)。
          ② 天干透出入势 (㊻s86 只数地支): 原书"同党合流"=干支一体看 ——
            火党=巳午支+丙丁干, 土党=辰戌丑未支+戊己干, 金党=申酉支+庚辛干, 水党=亥子支+壬癸干, 木党=寅卯支+甲乙干。
          ③ 删㊻s86自造: "土金同党(土生金)制水木" / "水木同党(水生木)制火土" 两种合流
            原书 ch8/ch9/ch11 无此断例 (原书势型只有 金水/火土/木火/湿土/燥土 五种, patterns 模式1),
            违反"不自行发明规则"铁律, 删除。
          ④ 制净判定含干 (㊻s86 只数支): 势所制五行在局有根(支≥2 或 干透≥1 且该干坐支同五行)
            = 制不净 (ch8"官杀制不尽当财看"); 无根(仅支<2且无干)=制净, 忌神成立。
            1983例: 所制金水, 金0支, 水1支(亥) <2 但 壬壬癸三干透(亥坐壬根) = 制不净 → 忌神被合绊, 财象(当财看)。

        势判定链 (原著五种势型, 优先级 单五行≥3 > 合流):
          ① 单五行≥3支 (旧㊻s82 口径保留): 支+干合计≥3, 按 CONTROLS 克链制对家
          ② 火土燥势合流: 火党(巳午+丙丁) + 燥土(戌未+戊己) 合计≥3支(支计) 且 火党≥1
          ③ 金水湿势合流: 金党(申酉+庚辛) + 水党(亥子+壬癸) + 湿土(辰丑+戊己) 合计≥3支 且 金水≥1
          ④ 木火同党合流: 木党(寅卯+甲乙) + 火党(巳午+丙丁) 合计≥3支(支计) 且 木党≥1
          无成势 → UNDETERMINED (L5 忌喜层退 wulei_shen 兜底)。

        势方向输出: shi_direction / shi_party / shi_controlled / shi_strength / shi_zhi_jing / shi_evidence。
        """
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        all_stems = [
            chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
            chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
        ]
        el_count = {}
        for b in branches:
            el = _branch_element(b)
            el_count[el] = el_count.get(el, 0) + 1
        fire = el_count.get("FIRE", 0)
        earth = el_count.get("EARTH", 0)
        metal = el_count.get("METAL", 0)
        water = el_count.get("WATER", 0)
        wood = el_count.get("WOOD", 0)
        # 土分燥湿 (原著 ch8/ch9): 燥土=戌未, 湿土=辰丑
        dry_earth = el_count.get("DRY_EARTH", 0) or sum(
            1 for b in branches if b in DRY_EARTH_BRANCHES)
        wet_earth = el_count.get("WET_EARTH", 0) or sum(
            1 for b in branches if b in WET_EARTH_BRANCHES)
        # 天干透出入势 (原著"同党合流"=干支一体): 各五行天干计数
        stem_count = {}
        for s in all_stems:
            se = STEM_ELEMENT.get(s, "UNDETERMINED")
            stem_count[se] = stem_count.get(se, 0) + 1

        def _total(el_name):
            """一支+干合计 (原著同党合流口径)."""
            return el_count.get(el_name, 0) + stem_count.get(el_name, 0)

        def _ctrl_of_els(els):
            out = []
            for e in els:
                c = CONTROLS.get(e)
                if c and c not in out:
                    out.append(c)
            return out

        def _zhi_jing_ctrl(ctrl_els):
            """势所制五行是否制净 (原著 ch8 制不尽当财 + ch13 虚实):
            被制者有根(支≥2, 或 支≥1且干≥1) **或 有原神(生被制者的五行在局支/干有气)**
            = 制不净(ch8"制不好当财看", ch13"实"); 无根且无原神=制净(忌神成立, ch13"虚")."""
            br = sum(el_count.get(c, 0) for c in ctrl_els)
            st = sum(stem_count.get(c, 0) for c in ctrl_els)
            has_root = (br >= 2) or (br >= 1 and st >= 1)
            # 原神: 生被制五行的五行在局有气(支或干) → 被制者得源, 制不净
            has_yuanshen = False
            for c in ctrl_els:
                yuanshen = GENERATES.get(c)   # c 由谁生 = 该五行
                if yuanshen and (el_count.get(yuanshen, 0) >= 1 or stem_count.get(yuanshen, 0) >= 1):
                    has_yuanshen = True
                    break
            zj = "ZHI_JING" if not (has_root or has_yuanshen) else "ZHI_BU_JING"
            return zj, br, st, has_yuanshen

        def _set_out(ctrl_els, party, direction, strength, ev):
            zj, br, st, has_ys = _zhi_jing_ctrl(ctrl_els)
            result.shi_party = list(party)
            result.shi_controlled = list(ctrl_els)
            result.shi_strength = strength
            result.shi_zhi_jing = zj
            result.shi_direction = direction
            result.shi_evidence = [
                ev,
                f"势所制={ctrl_els} 在局支{br}+干{st}, 原神{'有' if has_ys else '无'}, {zj}"
                f"({'忌神成立' if zj == 'ZHI_JING' else 'ch8 制不尽当财看, 忌象减轻/转财'})",
            ]

        # 原著优先级: 先查合流(火土燥势/金水湿势/木火同党, 同党≥3支含干支),
        # 再查单五行成势(防合流吞掉纯单五行)。ch1 例③"金水湿土成势"= 合流先于单土。
        # ② 火土燥势 (ch8): 火党(巳午支+丙丁干) + 燥土(戌未支+戊己干) ≥3, 火党≥1 —— 湿土(辰丑)不入火土党
        dry_earth_br = sum(1 for b in branches if b in DRY_EARTH_BRANCHES)
        wet_earth_br = sum(1 for b in branches if b in WET_EARTH_BRANCHES)
        fe_party = fire + dry_earth_br + stem_count.get("FIRE", 0) + stem_count.get("EARTH", 0)
        fire_party = fire + stem_count.get("FIRE", 0)
        if fe_party >= 3 and fire_party >= 1:
            ctrl_els = _ctrl_of_els(["FIRE", "EARTH"])   # 火克金 + 土克水 = 金水
            _set_out(ctrl_els, ["FIRE", "EARTH"], "FIRE_EARTH→METAL_WATER",
                     "STRONG" if fire_party >= 2 else "WEAK",
                     f"火土燥势(火{fire}+燥土{dry_earth_br}+火干{stem_count.get('FIRE', 0)}"
                     f"+土干{stem_count.get('EARTH', 0)}={fe_party}), 火生燥土同党, 制{ctrl_els}")
            return
        # ③ 金水湿势 (ch9): 金水党(申酉亥子支+庚辛壬癸干) + 湿土(辰丑支+戊己干) ≥3, 金水≥1
        mw_party = metal + water + wet_earth_br + stem_count.get("METAL", 0) + stem_count.get("WATER", 0)
        metal_water = metal + water + stem_count.get("METAL", 0) + stem_count.get("WATER", 0)
        if mw_party >= 3 and metal_water >= 1:
            ctrl_els = _ctrl_of_els(["METAL", "WATER"])   # 金克木 + 水克火 = 木火
            _set_out(ctrl_els, ["METAL", "WATER"], "METAL_WATER→FIRE_EARTH",
                     "STRONG" if metal_water >= 2 else "WEAK",
                     f"金水湿势(金{metal}+水{water}+湿土{wet_earth_br}+金干{stem_count.get('METAL', 0)}"
                     f"+水干{stem_count.get('WATER', 0)}={mw_party}), 金生水同党, 制{ctrl_els}")
            return
        # ④ 木火同党 (ch8/ch11): 木党(寅卯支+甲乙干) + 火党(巳午支+丙丁干) ≥3, 木党≥1
        wf_party = wood + fire + stem_count.get("WOOD", 0) + stem_count.get("FIRE", 0)
        wood_party = wood + stem_count.get("WOOD", 0)
        if wf_party >= 3 and wood_party >= 1:
            ctrl_els = _ctrl_of_els(["WOOD", "FIRE"])     # 木克土 + 火克金 = 土金
            _set_out(ctrl_els, ["WOOD", "FIRE"], "WOOD_FIRE→EARTH_METAL",
                     "STRONG" if wood_party >= 2 else "WEAK",
                     f"木火同党(木{wood}+火{fire}+木干{stem_count.get('WOOD', 0)}"
                     f"+火干{stem_count.get('FIRE', 0)}={wf_party}), 木生火同党, 制{ctrl_els}")
            return
        # ① 单五行成势 (合流未中时, 防纯单五行≥3被漏判; 湿土不入单土党)
        for el in ("FIRE", "METAL", "WATER", "WOOD", "EARTH"):
            br_n = el_count.get(el, 0)
            st_n = stem_count.get(el, 0)
            if el == "EARTH":
                br_n = dry_earth_br   # 单土党只算燥土(戌未), 湿土(辰丑)已归金水湿势
            if br_n >= 3 or (br_n >= 2 and st_n >= 1):
                ctrl = CONTROLS.get(el, "UNDETERMINED")
                ctrl_els = [ctrl] if ctrl and ctrl != "UNDETERMINED" else []
                if ctrl_els:
                    _set_out(ctrl_els, [el], f"{el}→{ctrl}", "STRONG",
                             f"单五行{el}支{br_n}+干{st_n}成势(有根), 制{ctrl}")
                    return
        # 无成势
        result.shi_direction = "UNDETERMINED"
        result.shi_party = []
        result.shi_controlled = []
        result.shi_strength = "UNDETERMINED"
        result.shi_zhi_jing = "UNDETERMINED"
        result.shi_evidence = ["无成势(原著五势型均不满足), 退 wulei_shen 定忌喜兜底"]
        result.shi_strength = "UNDETERMINED"
        result.shi_zhi_jing = "UNDETERMINED"
        result.shi_evidence = [f"无成势(单五行最高{max(el_count.values()) if el_count else 0}支, 合流最高{max(fire+earth, metal+water, wood+fire, earth+metal, water+wood)}支)"]

    def _resolve_space_palace(self, chart, result, day_master):
        """ch5 空间类象+车象(原书ch5"年=远方/海外, 月=祖籍/家乡/根, 日支=现在居所, 时=门户/出门/车").
        判据: 基于四柱宫位=空间映射:
        ① 年支=远方/海外(年柱主外, 离日柱最远)
        ② 月支=家乡/祖籍(月柱主内, 家乡根)
        ③ 日支=现居所/配偶宫(日支主自身)
        ④ 时支=门户/出门/车(时柱主外, 门户象)
        车象: 时支=车(买车车祸均看时支) + 辰=车象(辰主运动/机器/车辆)
        输出 space_palace(空间方位)+car_signal(车象)."""
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        # 空间类象(四柱宫位→空间方位): 静态映射保留为参考
        result.space_palace = "年=远方/月=家乡/日支=居所/时=门户"
        # ㊻s118 ch5 空间/物品 + ch4 驿马 + ch2 冲合穿刑=应事: 动态判定家宅居所/出行异地
        # 原实现 space_palace/car_signal 写死静态串(每盘同句=没断, 无逐盘区分度). 动态判据:
        # ① 驿马在年柱(远方/远祖)=异地谋生/远行象; 驿马在时柱(门户)=出门/走动/交通
        # ② 月柱(家业/单位)被冲穿=家宅动荡/单位搬迁; 日支(居所/配偶宫)被冲=搬迁
        # ③ 驿马被合/冲(大运/流年引动)=走动应期; 无驿马且宫位无冲=安定
        yima_set = set(result.yima_branches or [])
        yima_pos = []
        for pos_name, b in [("年", chart.year_pillar.earthly_branch),
                            ("月", chart.month_pillar.earthly_branch),
                            ("日", chart.day_pillar.earthly_branch),
                            ("时", chart.hour_pillar.earthly_branch)]:
            if b in yima_set:
                yima_pos.append(pos_name)
        space_ev = []
        space_dyn = []
        # ① 驿马引动(走动/异地/门户)
        if "年" in yima_pos:
            space_dyn.append("YIDI")
            space_ev.append("ch4年驿马=远祖/远方, ch5年柱=远方/海外 → 异地谋生/远行象")
        if "时" in yima_pos:
            space_dyn.append("CHUYING")
            space_ev.append("ch4时驿马=门户之马, ch5时柱=门户/出门 → 出门/走动/交通象")
        if "月" in yima_pos:
            space_ev.append("ch4月驿马=走动, ch5月柱=家业/单位 → 单位搬迁/走动象")
        # ② 宫位被冲穿(家宅/居所动)
        chong_map = getattr(chart, "branch_clash_map", {}) or {}
        # 日支被冲=居所动(搬迁); 月支被冲=家宅/单位动
        day_b = chart.day_pillar.earthly_branch
        month_b = chart.month_pillar.earthly_branch
        # 原局四支中 与 日支 相冲的支 present = 日支被冲
        four_b = [chart.year_pillar.earthly_branch, month_b, day_b, chart.hour_pillar.earthly_branch]
        day_clash = BRANCH_CHONG.get(day_b)
        if day_clash and day_clash in four_b:
            space_dyn.append("BANQIAN")
            space_ev.append(f"ch5日支{day_b}被{day_clash}冲=居所动(搬迁)象")
        month_clash = BRANCH_CHONG.get(month_b)
        if month_clash and month_clash in four_b:
            space_dyn.append("JIAZHAI_DONG")
            space_ev.append(f"ch5月支{month_b}被{month_clash}冲=家宅/单位动象")
        # ③ 安定(无驿马引动且无宫位被冲)
        if not space_dyn:
            space_dyn.append("STABLE")
            space_ev.append("ch5空间: 无驿马引动/宫位无冲 → 安居/无搬迁异地象")
        result.space_dynamic = "+".join(space_dyn)
        result.space_dynamic_evidence = space_ev
        # 车象(㊻s118 区分度): 时支被冲/刑=车祸象; 辰 present=车; 无则 UNDETERMINED
        hour_branch = chart.hour_pillar.earthly_branch
        has_chen = "CHEN" in four_b
        car_signals = []
        hour_clash = BRANCH_CHONG.get(hour_branch)
        if hour_clash and hour_clash in four_b:
            car_signals.append(f"ch5时支{hour_branch}被{hour_clash}冲=车象受损(车祸/车损)象")
        elif has_chen:
            car_signals.append("ch5辰=车象(原书'辰主运动/机器/车辆')")
        result.car_signal = "；".join(car_signals) if car_signals else "UNDETERMINED"

    def _resolve_wulei_shen(self, chart, result, day_master):
        """ch3 五类神分类(原书ch3"喜神/用神/忌神/病神/闲神: 忌神被强用神制服→行忌神运吉;
        忌神本身被制则不忌; 喜神=最需之神, 忌神=最需制之神, 病神=致病之神, 闲神=不参与做功之神").
        分类口径(消费做功层): 做功EFFECTIVE方法涉及十神=用神/喜神; 做功NEGATIVE涉及十神=忌神;
        未做功十神=闲神. 在 _analyze_zuogong 后调用."""
        stems = {
            'year': (chart.year_pillar.heavenly_stem, ten_god(day_master, chart.year_pillar.heavenly_stem)),
            'month': (chart.month_pillar.heavenly_stem, ten_god(day_master, chart.month_pillar.heavenly_stem)),
            'hour': (chart.hour_pillar.heavenly_stem, ten_god(day_master, chart.hour_pillar.heavenly_stem)),
        }
        eff_tgs = set()
        neg_tgs = set()
        for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions):
            for tg in ("财", "官", "杀", "印", "食", "伤", "比", "劫"):
                if tg in m:
                    if a == ZuoGongAttribution["EFFECTIVE"]:
                        eff_tgs.add(tg)
                    elif a == ZuoGongAttribution["NEGATIVE"]:
                        neg_tgs.add(tg)
        jishen = [st for st, tg in stems.values() if any(c in tg for c in neg_tgs)]
        yongshen = [st for st, tg in stems.values() if any(c in tg for c in eff_tgs)]
        xianshen = [st for st, tg in stems.values()
                    if not any(c in tg for c in (eff_tgs | neg_tgs))]
        # V3.6.9㊻k ch3 五类神分类中文标签(原书ch3"喜神/用神/忌神/病神/闲神"原文明词),
        # 使引擎输出含"忌神/用神/闲神"中文字面, 可真值对照按断语关键词匹配可命中
        # (㊻f 旧版仅输出英文键 yongshen/jishen/xianshen, "忌神"中文字面缺失→可真值"忌神"条未命中)
        wulei_zh = {}
        if yongshen:
            wulei_zh["yongshen"] = "用神"
        if jishen:
            wulei_zh["jishen"] = "忌神"
        if xianshen:
            wulei_zh["xianshen"] = "闲神"
        result.wulei_shen = {
            "yongshen": yongshen,
            "jishen": jishen,
            "xianshen": xianshen,
            "wulei_zh": wulei_zh,
        }

    def _resolve_kk_wuxu(self, chart, result, day_master):
        """ch4 空亡十象: 印星做功EFFECTIVE+空亡支为木/金/水=玄学/务虚事业.
        原书ch4"所用之神旺相而空亡→务虚事业(佛道玄学五术气功艺术)".
        判据: 印星/食伤做功EFFECTIVE(食伤泄秀=玄学/印星=玄学)+空亡支含木/金/水(印星五行).
        印星五行: 木(甲乙)=文/金(庚辛)=武/水(壬癸)=玄. 空亡中印星五行=玄学事业."""
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        eff_methods_list = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        ]
        yin_eff = any('印制食伤' in m or '食伤泄秀' in m or '印化官杀' in m for m in eff_methods_list)
        # 所用之神旺相而空亡→务虚事业: 空亡支中印星五行(木/金/水)+做功层印星/食伤EFFECTIVE
        # 原书"所用之神旺相而空亡→务虚事业(佛道玄学五术气功艺术)"
        # 口径收紧: 空亡支含印星五行(木/金/水) AND 印星做功EFFECTIVE(印制食伤/食伤泄秀/印化官杀)
        xinkong_wuxu = any(
            _branch_element(b) in ("WOOD", "METAL", "WATER")
            for b in result.xunkong_branches
        )
        if yin_eff and xinkong_wuxu:
            result.kk_wuxu = "玄学/务虚事业"
            result.xinkong_evidence.append("ch4空亡十象: 印星做功EFFECTIVE+空亡含木/金/水=玄学/务虚事业")
        else:
            result.kk_wuxu = "UNDETERMINED"

    def _resolve_shensha_leixiang(self, chart, result, day_master):
        """V3.6.9㊻n ch4 神煞类象(驿马/天医/华盖/将星): 排盘层已算好的神煞支,
        断事层消费为类象标注(走动/远方/交通=驿马; 医药=天医; 玄学孤独=华盖; 权柄=将星).
        原书ch4"驿马之象: 马=走动/远方/交通; 年驿马主远祖, 时驿马主门户之马(车)".
        非断事层核心结构(财/官/婚/子/病/狱), 仅作类象细节标注(断职业/动态时参考)."""
        shensha = getattr(chart, "shensha", {})
        notes = []
        yima = shensha.get("YI_MA", [])
        if yima:
            yima_pos = []
            branches = [
                ("年", chart.year_pillar.earthly_branch), ("月", chart.month_pillar.earthly_branch),
                ("日", chart.day_pillar.earthly_branch), ("时", chart.hour_pillar.earthly_branch),
            ]
            for pos_name, b in branches:
                if b in yima:
                    yima_pos.append(pos_name)
            if yima_pos:
                note = f"驿马(走动/远方/交通)在{'+'.join(yima_pos)}柱"
                if "时" in yima_pos:
                    note += "时驿马主门户之马(车/交通行业)"
                if "年" in yima_pos:
                    note += "年驿马主远祖/远方"
                notes.append(note)
        huagai = shensha.get("HUA_GAI", [])
        if huagai:
            notes.append(f"华盖(玄学/孤独/艺术)在{'+'.join(p for p, b in [('年',chart.year_pillar.earthly_branch),('月',chart.month_pillar.earthly_branch),('日',chart.day_pillar.earthly_branch),('时',chart.hour_pillar.earthly_branch)] if b in huagai)}柱")
        jiangxing = shensha.get("JIANG_XING", [])
        if jiangxing:
            notes.append(f"将星(权柄/武职)在{'+'.join(p for p, b in [('年',chart.year_pillar.earthly_branch),('月',chart.month_pillar.earthly_branch),('日',chart.day_pillar.earthly_branch),('时',chart.hour_pillar.earthly_branch)] if b in jiangxing)}柱")
        tianyi = shensha.get("TIAN_YI", [])
        if tianyi:
            notes.append(f"天医(医药/医护)在{'+'.join(p for p, b in [('年',chart.year_pillar.earthly_branch),('月',chart.month_pillar.earthly_branch),('日',chart.day_pillar.earthly_branch),('时',chart.hour_pillar.earthly_branch)] if b in tianyi)}柱")
        # V3.6.9㊻p 补漏: 文昌(排盘层 WEN_CHANG)在ch11学历/学业类象, 加进神煞类象标注
        wenchang = shensha.get("WEN_CHANG", [])
        if wenchang:
            notes.append(f"文昌(学业/文书/文笔)在{'+'.join(p for p, b in [('年',chart.year_pillar.earthly_branch),('月',chart.month_pillar.earthly_branch),('日',chart.day_pillar.earthly_branch),('时',chart.hour_pillar.earthly_branch)] if b in wenchang)}柱")
        result.shensha_leixiang = "; ".join(notes) if notes else "UNDETERMINED"

    def _resolve_lu_dangcai(self, chart, result, day_master):
        """V3.6.9㊻s ch8 禄 神 当 财(原 书 ch8"无 财 八 字 用 禄, 喜 印 生 禄, 忌 伤 食 劫 财").
        判 据:
          ① 无 财 八 字(天 干 + 藏 干 无 财 星) + 日 主 禄 在 四 柱 = 禄 当 财 口 径 启 用
          ② 印 星 做 功 EFFECTIVE(印 生 禄 功 能)→ YINSHENG_LU_WEALTH(喜 印 生 禄, 得 财 吉)
          ③ 伤 食/比 劫 在 局(原 书"忌 伤 食 劫 财", 伤 食 泄 禄/比 劫 分 禄)→ LU_PO(禄 破 不 吉)
          ④ 无 财 + 禄 在 局 无 功 无 忌 → LU_WEALTH_BASE(禄 当 财 基 础 口 径)"""
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        stems = chart.four_stems()
        # ㊻i 修(全量234/UNDET缺口): 原书ch8"无财八字用禄"口径=财不透干(虚财), 非"藏干也无财"。
        # 盲派"无财"=财星不在天干(虚财财气薄), 禄可代财; 藏干含财=财有根但虚(不现天干),
        # 仍属"无财八字"用禄口径。㊻s初建误用"藏干也无财"(过严, 363例仅14例满足→全量UNDET),
        # ㊻i修后: 天干无财即启用禄当财口径(天干无财126例, 其中禄在局37例应触发)。
        has_cai = any(ten_god(day_master, s) in GROUP_CAI for s in stems)
        if has_cai:
            result.lu_dangcai = "UNDETERMINED"
            return
        # 无 财 八 字 → 查 日 主 禄 在 局
        dm_lu = road_branch(day_master)
        if dm_lu not in branches:
            result.lu_dangcai = "UNDETERMINED"
            return
        eff_methods = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        ]
        yin_eff = any("印" in m for m in eff_methods)
        shiji_present = any(
            ten_god(day_master, s) in (GROUP_SHI, GROUP_BI) for s in stems
        ) or any(
            ten_god(day_master, h) in (GROUP_SHI, GROUP_BI)
            for b in branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        if yin_eff:
            result.lu_dangcai = "YINSHENG_LU_WEALTH"   # 喜 印 生 禄=得 财 吉
        elif shiji_present:
            result.lu_dangcai = "LU_PO"                # 忌 伤 食 劫 财=禄 破
        else:
            result.lu_dangcai = "LU_WEALTH_BASE"       # 无 财 用 禄 基 础 口 径
        result.rules_triggered.append("EVT-LU-001")

    def _resolve_menhu_trading(self, chart, result, day_master):
        """ch8 门户做功(原书ch8"门户(时上)做功: 贸易/炒作, 人不能多").
        判据: 时柱藏干/时干含食神/伤官/正财/偏财(时柱=门户取财)=门户/贸易炒作品类."""
        hour_branch = chart.hour_pillar.earthly_branch
        hour_stem = chart.hour_pillar.heavenly_stem
        hour_tgs = [ten_god(day_master, h) for h, _p in BRANCH_HIDDEN_STEMS.get(hour_branch, [])]
        hour_stem_tg = ten_god(day_master, hour_stem)
        hour_has_work = any(
            t in ("食神", "伤官", "正财", "偏财") for t in hour_tgs + [hour_stem_tg]
        )
        if hour_has_work:
            result.menhu_trading = "门户/贸易炒作"
        else:
            result.menhu_trading = "UNDETERMINED"

    def _resolve_fugong_palace(self, chart, result, day_master):
        """ch7 借象原则(原书ch7"副宫定义: ①从夫妻宫引出的字→该字为副宫; ②与夫妻宫同五行的字; 副宫表短暂").
        判据: 夫妻宫=日支, 副宫=日支同五行支(寅卯同木/巳午同火/申酉同金/亥子同水/辰戌丑未同土),
        副宫多现=副宫≥2支(婚姻短暂/多婚信号); 副宫=日支同五行但非日支本身.
        副宫做功(副宫被穿/冲)=婚姻短暂象."""
        day_branch = chart.day_pillar.earthly_branch
        day_el = _branch_element(day_branch)
        # 副宫=与日支同五行的其他支(原书"寅木为副宫, 卯木为妻宫, 寅上透庚财星则庚也是妻星")
        same_el_branches = [b for b in ("ZI","CHOU","YIN","MAO","CHEN","SI","WU","WEI","SHEN","YOU","XU","HAI")
                            if _branch_element(b) == day_el and b != day_branch]
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.hour_pillar.earthly_branch,
        ]
        fugong_present = [b for b in branches if b in same_el_branches]
        if len(fugong_present) >= 2:
            result.fugong_palace = "多现副宫(婚姻短暂/多事信号)"
        elif len(fugong_present) == 1:
            result.fugong_palace = "单现副宫(副职/短暂婚姻)"
        else:
            result.fugong_palace = "UNDETERMINED"

    def _resolve_tone_char(self, chart, result, day_master):
        """ch13 一贵抵九贱权重定基调(原书ch13"一贵抵九贱/一贱消九贵: 看权重最大的字定整体吉凶基调").
        判据: 做功层EFFECTIVE方法最多的十神=基调字(权重最大); 无EFFECTIVE=基调不确定."""
        from collections import Counter as _Counter
        eff_tg_count = _Counter()
        for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions):
            if a == ZuoGongAttribution["EFFECTIVE"]:
                for tg in ("财", "官", "杀", "印", "食", "伤", "比", "劫"):
                    if tg in m:
                        eff_tg_count[tg] += 1
        if eff_tg_count:
            top_tg, _cnt = eff_tg_count.most_common(1)[0]
            # 透干十神名→对应天干
            stems_all = [
                chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
                chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
            ]
            tg_to_stem = {
                "财": "CaiStem", "官": "GuanStem", "杀": "ShaStem",
                "印": "YinStem", "食": "ShiStem", "伤": "ShangStem",
                "比": "BiStem", "劫": "JieStem",
            }
            result.tone_char = f"{top_tg}(权重最大)"
        else:
            result.tone_char = "UNDETERMINED"

    def _resolve_crime_structure(self, chart, result, day_master):
        """ch12 牢狱判定(原书ch12"犯罪结构四类 + 以阴灭阳 + 出狱定法").
        犯罪结构四类:
        ① 比劫伤官组合=拉帮结派(比劫本是无知物, 一见伤官势必归)
        ② 七杀无制化/夹制日主=犯罪
        ③ 禄与官杀对抗(禄冲制七杀)=犯罪
        ④ 以阴灭阳(亥丑辰等阴字坏阳用之物)=牢狱第一信号
        出狱: 日主得禄之年/冲穿坏库.
        判据基于做功层+原局结构:
        ① 比劫制财EFFECTIVE/NEGATIVE + 伤官制官EFFECTIVE + 伤官泄秀EFFECTIVE
           → 比劫+伤官组合(拉帮结派)
        ② official_state=UNCONTROLLED(七杀无制) 或 七杀制比劫=犯罪
        ③ 阳刃/禄神 + 官杀制比劫EFFECTIVE → 禄与官杀对抗
        ④ 亥/丑/辰 present 且 阳干日主(丙丁) + 穿损/合损阳干支 → 以阴灭阳"""
        eff_methods_list = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        ]
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        crime_evidence = []
        # ① 比劫伤官组合=拉帮结派(原书ch12"比劫本是无知物, 一见伤官势必归")
        # ㊻u 原判据要求 伤官制官+食伤泄秀 双 EFFECTIVE 才命中(0例); 放宽为:
        # 比劫制财在局 + (食伤泄秀 EFFECTIVE 或 伤官制官在局 或 伤官制官 EFFECTIVE)
        # = 比劫(伙计)+伤官(思想/口供)组合, 不需同时制官(拉帮结派=团伙对抗, 非制官)
        bijie_zhizhi = "比劫制财" in " ".join(result.zuo_gong_methods)
        shangguan_zhiguan = "伤官制官" in eff_methods_list
        shangguan_zhiguan_present = "伤官制官" in " ".join(result.zuo_gong_methods)
        shangguan_xiexiu = "食伤泄秀" in eff_methods_list
        # V3.6.9㊻v ch12 官杀无制对抗(原书ch12"伤官与官杀对抗(不是制)=违法; 比劫多现+官杀无制=犯罪结构"):
        # 比劫制财在局 + 官杀制比劫在局 + official_state=UNCONTROLLED(官杀无制)
        # = 比劫(伙计)与官杀(法律/公家)对抗, 官杀无制=制官不成=违法(不需伤官在局)
        guansha_wuzhi_antag = (
            bijie_zhizhi
            and "官杀制比劫" in " ".join(result.zuo_gong_methods)
            and result.official_event_structure.get("official_state") == "UNCONTROLLED"
        )
        # ㊻v 补: 比劫制财在局 + 官杀制比劫在局(不论 official_state, 官杀制比劫本身即=官杀与比劫对抗)
        # ㊻s112 ch12 L16 原文核对: "七杀无制化=犯罪结构" 关键词"无制化".
        # s96 原判据过宽: 未检查官杀是否有制化路径(印化官杀/食伤制杀在局).
        # "印化官杀/食伤制杀在局" = 官杀已被制化(泄入印/食伤制杀), 非"无制化" → 否决 QISHA_WUZHI.
        _guansha_zhihua_present = any(
            m in ("印化官杀", "印制官杀", "食伤制杀")
            for m in result.zuo_gong_methods
        )
        guansha_bijie_antag = (
            bijie_zhizhi
            and "官杀制比劫" in " ".join(result.zuo_gong_methods)
            and not _guansha_zhihua_present   # ㊻s112: 官杀有制化路径→非"无制化"→否决
        )
        if (bijie_zhizhi and (shangguan_xiexiu or shangguan_zhiguan or shangguan_zhiguan_present)):
            result.crime_structure = "RIBISHANG_GUAN"
            crime_evidence.append("ch12比劫伤官组合: 比劫制财+伤官(制官/泄秀)=拉帮结派(一见伤官势必归)")
        elif guansha_wuzhi_antag:
            # ㊻v 官杀无制对抗: 比劫制财+官杀制比劫+UNCONTROLLED(官杀无制且比劫在局=与官杀对抗=违法)
            result.crime_structure = "QISHA_WUZHI"
            crime_evidence.append(
                "ch12㊻v官杀无制对抗: 比劫制财+官杀制比劫+official_state=UNCONTROLLED"
                "(官杀无制且比劫在局=与官杀对抗=违法结构, 原书ch12'伤官与官杀对抗(不是制)=违法')"
            )
        elif guansha_bijie_antag:
            # ㊻v 补: 官杀比劫对抗(不需 UNCONTROLLED, 有对抗即有犯罪信号)
            result.crime_structure = "QISHA_WUZHI"
            crime_evidence.append(
                "ch12㊻v官杀比劫对抗: 比劫制财+官杀制比劫(官杀与比劫对抗=违法结构, 原书ch12'伤官与官杀对抗(不是制)=违法')"
            )
        # ② 七杀无制化=犯罪结构(原书"七杀无制化/夹制日主=犯罪")
        elif result.official_event_structure.get("official_state") == "UNCONTROLLED" \
                and "官杀制比劫" in " ".join(result.zuo_gong_methods):
            result.crime_structure = "QISHA_WUZHI"
            crime_evidence.append("ch12七杀无制: 官杀无制且官杀制比劫=犯罪结构")
        # ③ 禄与官杀对抗(原书"禄冲制七杀=犯罪")
        elif "阳刃" in eff_methods_list and "官杀制比劫" in " ".join(result.zuo_gong_methods):
            result.crime_structure = "LU_GUAN_KONGDUI"
            crime_evidence.append("ch12禄与官杀对抗: 阳刃+官杀制比劫=禄冲制七杀(犯罪)")
        # ④ 以阴灭阳(亥/丑/辰 present 且 阳干日主 + 穿损/合损阳干支)
        # V3.6.9㊻g ch3 阴阳三分法(原书ch3"丑酉为阴中阴=牢狱/黑社会/玄学; 戌为阳中阳=阳乱"):
        # 丑酉双现(阴中阴)=牢狱/黑社会信号, 加入 crime_structure 判据
        # V3.6.9㊻j ch12 申酉+辰(官库)组合=服刑结构(原书ch3"申酉=法律公检"+ch12"库为牢狱"):
        # 申/酉 present + 辰(官库) present = 服刑/牢狱信号(公检法入狱)
        # V3.6.9㊻u fix: ①②③已命中时跳过④⑤(最特定口径优先, 防止④/⑤else分支覆盖①②③结果)
        if result.crime_structure == "UNDETERMINED":
            chouyou_baoju = "CHOU" in branches and "YOU" in branches
            shenyou_chen = any(b in ("SHEN", "YOU") for b in branches) and "CHEN" in branches
            if chouyou_baoju or shenyou_chen:
                result.crime_structure = "YIN_MIE_YANG"
                ev = []
                if chouyou_baoju:
                    ev.append("ch3阴阳三分法: 丑酉双现(阴中阴)=牢狱/黑社会信号")
                if shenyou_chen:
                    ev.append("ch12申酉+辰(官库)组合: 公检法入狱/服刑结构(申酉=法律+辰=库=牢狱)")
                crime_evidence.extend(ev)
            else:
                # ⑤ V3.6.9㊻l ch1 反局主牢狱(原书ch1"大部分反局结构主牢狱之象"+ch12"反局+辰丑=牢狱"):
                # ①②③④均不命中时, 若反局(FAN_JU)+四柱含辰/丑(库=收藏机构) → 反局牢狱
                fanguan_laoyu = (
                    result.zheng_fan_ju == "FAN_JU"
                    and any(b in ("CHEN", "CHOU") for b in branches)
                )
                if fanguan_laoyu:
                    result.crime_structure = "FANJU_CHONGHE"
                    crime_evidence.append(
                        "ch1反局主牢狱: 反局(日柱做功与势对抗)+辰/丑(库=牢狱收藏机构)"
                        "组合=反局牢狱结构(原书'大部分反局结构主牢狱之象, 局中有辰丑时'ch12)"
                    )
        result.crime_evidence = crime_evidence
        # V3.6.9㊻ ch12 出狱定法(原书ch12"出狱: 日主得禄之年, 或冲穿坏库[牢狱为库]")
        # 判据: 犯罪结构非UNDETERMINED(有牢狱) + 原局有库支(辰戌丑未, 牢狱为库) + 库被冲穿
        # 出狱路径: ①日主得禄之年(流年见日主禄支=出狱) ②冲穿坏库(库支被冲=出狱)
        if result.crime_structure != "UNDETERMINED":
            muku_present = [b for b in branches if b in ("CHEN", "XU", "CHOU", "WEI")]
            dm_lu = road_branch(day_master)
            chong_ku = any(
                b in muku_present and BRANCH_CHONG.get(b) in branches
                for b in muku_present
            )
            # V3.6.9㊻a ch12 出狱定法第三条口径: "日主合出/冲出日主之年"
            # 日主天干五合 partner stem 在原局天干中(非日干自身)=合出日主(该合支冲/穿=出狱);
            # 日主禄支的冲支在原局支中=冲出日主(该冲支出现=出狱定年)
            he_partner_stems = [
                other for pair in STEM_HE
                for other in [pair[0], pair[1]]
                if day_master in pair and other != day_master
            ]
            all_stems = [
                chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
                chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
            ]
            # ㊻a 修: 排 除 日 主 天 干 本 身(五 合 须 为 日 干 合 其 他 干, 非 自 合)
            he_chu_dm = any(s in he_partner_stems for s in all_stems if s != day_master)
            dm_lu = road_branch(day_master)
            chong_chu_dm = BRANCH_CHONG.get(dm_lu) in branches
            release_paths = []
            release_paths.append(f"日主得禄之年({dm_lu}出现=出狱)")
            if he_chu_dm:
                release_paths.append(f"日主合出之年({he_partner_stems}合日主=出狱)")
            if chong_chu_dm:
                release_paths.append(f"冲出日主之年({BRANCH_CHONG.get(dm_lu)}冲日主禄{dm_lu}=出狱)")
            if chong_ku:
                release_paths.append(f"冲穿坏库({muku_present}库被冲=出狱)")
            result.release_path = "；".join(release_paths)
        else:
            result.release_path = "UNDETERMINED"  # 无牢狱结构, 无出狱口径
        # ㊻s117 ch12 有无口径: crime_present = 有无犯罪结构(供断语层"有无牢狱象")
        result.crime_present = (result.crime_structure != "UNDETERMINED")

    def _resolve_interpersonal(self, chart, result, day_master):
        """㊻s119 ch6/ch8/ch12 人际合伙域(用户维度文本 13 子域#7: 同辈互动/合伙成败/利益争夺/同伴反目).
        原书支撑:
          ch6 L14 比肩"兄弟/同辈/独立/争财", L15 劫财"同我同性, 争夺/破财/结伙, 劫财+伤官=拉帮结派(犯罪结构)"
          ch8 L12 比劫当财"比劫制财为得财, 用劫是富命"(合伙得财); 主位比劫分禄=破财(利益争夺)
          ch12 L4 "劫财+伤官=拉帮结派(比劫野蛮+伤官思想=都听伤官), 与官杀对抗必为牢狱"(同伴反目)
        4 枚举判据(消费已算好的 bijie_zhichai_fenliu + crime_structure, 不重算):
          ① BIXIONG(同伴反目): crime_structure=RIBISHANG_GUAN(比劫伤官拉帮结派, ch12 L4)
             → 同辈/合伙关系带对抗/反目(合伙散伙/遭人出卖/利益分配翻脸)
          ② HEHUA_DECAI(合伙得财): bijie_zhichai_fenliu=ZHICHAI_DECAI(宾位比劫制财EFFECTIVE,
             ch8 L12 用劫富命) → 合伙/同辈帮身成事(合作得财)
          ③ FENLU_ZHENGDUI(利益争夺): bijie_zhichai_fenliu=FENLU_POCAI(主位比劫分禄NEGATIVE,
             ch6 L15 劫财争夺/破财) → 同辈争财/利益被分(合伙争利/破财)
          ④ TONGPEI_STABLE(同辈平稳): 无比劫制财负功且非比劫伤官结构, 比肩在局 → 同辈缘分平稳
          ⑤ UNDETERMINED: 无比劫/伤官做功, 人际象未明
        优先级: ①>②>③>④>⑤ (反目结构优先于合伙得财, 因 ch12 拉帮结派=对抗最强)"""
        ev = []
        bijie_fenliu = result.bijie_zhichai_fenliu
        crime = result.crime_structure
        # ① 同伴反目(比劫伤官拉帮结派, ch12 L4)
        if crime == "RIBISHANG_GUAN":
            result.interpersonal_structure = "BIXIONG"
            ev.append("ch12比劫伤官=拉帮结派(同伴反目): 合伙散伙/遭人出卖/利益分配翻脸, 与官杀对抗")
        # ② 合伙得财(宾位比劫制财EFFECTIVE, ch8 L12 用劫富命)
        elif bijie_fenliu == "ZHICHAI_DECAI":
            result.interpersonal_structure = "HEHUA_DECAI"
            ev.append("ch8比劫当财=宾位制住同伙财归我(合伙得财/用劫富命): 合作帮身成事")
        # ③ 利益争夺(主位比劫分禄NEGATIVE, ch6 L15 劫财争夺/破财)
        elif bijie_fenliu == "FENLU_POCAI":
            result.interpersonal_structure = "FENLU_ZHENGDUI"
            ev.append("ch6劫财=主位分禄破财(利益争夺): 同辈争财/合伙争利被分")
        # ④ 同辈平稳(比肩在局无争夺/无反目)
        else:
            # 查比肩/劫财是否在局(十神)
            from ..reasoning.bazi_ten_gods import ten_god
            has_bijie = False
            for p in ("year", "month", "hour"):
                st = getattr(chart, f"{p}_pillar").heavenly_stem
                if ten_god(day_master, st) in ("比肩", "劫财"):
                    has_bijie = True
                    break
            if has_bijie:
                result.interpersonal_structure = "TONGPEI_STABLE"
                ev.append("ch6比肩/劫财在局且无争夺/拉帮结派结构: 同辈缘分平稳")
            else:
                result.interpersonal_structure = "UNDETERMINED"
                ev.append("ch6无比劫/伤官做功: 人际合伙象未明")
        result.interpersonal_evidence = ev

    def _resolve_mingqi_fufen_xingxing(self, chart, result, day_master):
        """㊻s120 ch9/ch11/ch14 深度核查 3 域(名气口碑/福分寿元/撤干神心性):
        用户维度文本 13 子域#9/#12/#13。原始资料断法级支撑:
          - 名气口碑(ch9 L18 官杀虚透=名气 + ch11 泄秀=成名 + 得奖): 官杀虚透/食伤泄秀/官杀当功
          - 撤干神心性(ch14 L12 撤开干支十神单看日干, 如"戊子撤开=外表忠厚内心水"): 日干坐支/干支一体撤开
          - 福分寿元(ch2 "合为有寿怕解合" + ch4 禄印食=寿元星 + 枭克夺食伤 + "正印为忌=操心"): 寿元星被穿倒/枭克
        全部消费已算字段(official_event_structure/做功/日干坐支/食伤/枭), 不重算底层。"""
        from ..reasoning.bazi_ten_gods import ten_god
        # ── ① 名气口碑 (ch9 虚透=名气 + ch11 泄秀=成名) ──
        mq_ev = []
        off = result.official_event_structure
        officer_present = off.get("officer_present", "False")
        control_completeness = off.get("control_completeness", "UNDETERMINED")
        # 官杀虚透=名气(ch9 L18 "官杀无根=名气不是实官"): 官杀透干但无根(被制干净/无支根)=虚透名气
        _off_gz = []
        for b in [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                  chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch]:
            for h, _p in BRANCH_HIDDEN_STEMS.get(b, []):
                if ten_god(day_master, h) in ("正官", "七杀"):
                    _off_gz.append(b)
        has_officer_root = len(_off_gz) > 0
        # 官杀透干(虚透=名气)
        officer_stem_present = any(
            ten_god(day_master, getattr(chart, f"{p}_pillar").heavenly_stem) in ("正官", "七杀")
            for p in ("year", "month", "hour")
        )
        # ㊻s121 名气域收紧(原 XIUXIU 判偏宽: 任何食伤泄秀/印制食伤都命中=没区分度):
        # ch11 "泄秀成名"要求泄秀配印(秀气流通有情, 食伤生财/印制食伤=文名)才成"名气";
        # 仅食伤泄秀(无配印/无官杀虚透)=技艺/才华, 非"名气"。
        if officer_stem_present and not has_officer_root:
            result.mingqi_structure = "XUTOU_MINGQU"
            mq_ev.append("ch9官杀虚透(透干无根)=名气非实官(虚名)")
        else:
            eff_methods = [m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
                          if a == ZuoGongAttribution["EFFECTIVE"]]
            # 配印=秀气流通有情(文名): 食伤做功 + 印制食伤/印化官杀(印星在局护泄秀)
            has_yin = any(m in ("印制食伤", "印化官杀", "食伤生财") for m in eff_methods)
            xie_shou = any(m in ("食伤泄秀", "食伤生财") for m in eff_methods)
            if xie_shou and has_yin:
                result.mingqi_structure = "XIUXIU_CHENGMING"
                mq_ev.append("ch11秀气泄秀配印(流通有情)=文名/成名(得漂亮成名)")
            elif xie_shou:
                result.mingqi_structure = "XINGZUO_DEJIANG"
                mq_ev.append("ch11食伤做功未配印=技艺/才华(非名气, 有作品/得奖象)")
            elif has_yin:
                result.mingqi_structure = "XINGZUO_DEJIANG"
                mq_ev.append("ch11印制食伤做功=文艺作品(得奖扬象, 非虚名)")
            else:
                result.mingqi_structure = "UNDETERMINED"
                mq_ev.append("ch9/ch11无名气做功象(无虚透/无泄秀配印): 名气未明")
        result.mingqi_evidence = mq_ev
        # ── ② 撤干神心性 (ch14 L12 "撤开干支十神单看日干心性, 外层 vs 内里") ──
        # ㊻s121 撤干神通根细分(ch14 "无根=虚"): 日干通根(地支藏干含日干或同五行)=实(外表坐实),
        # 日干无根(地支无同五行藏干)=虚(外表虚浮)。外层/内里二象 + 通根虚实。
        xing_ev = []
        dm_stem = day_master
        dm_branch = chart.day_pillar.earthly_branch
        dm_stem_el = STEM_ELEMENT.get(dm_stem, "")
        ZHI_EL = {"ZI": "WATER", "CHOU": "EARTH", "YIN": "WOOD", "MAO": "WOOD", "CHEN": "EARTH",
                  "SI": "FIRE", "WU": "FIRE", "WEI": "EARTH", "SHEN": "METAL", "YOU": "METAL",
                  "XU": "EARTH", "HAI": "WATER"}
        ZHI_EL_CN = {"WATER": "水", "EARTH": "土", "WOOD": "木", "FIRE": "火", "METAL": "金"}
        stem_el_cn = {"WOOD": "木", "FIRE": "火", "EARTH": "土", "METAL": "金", "WATER": "水"}.get(dm_stem_el, "")
        br_el_cn = ZHI_EL_CN.get(ZHI_EL.get(dm_branch, ""), "")
        # 日干通根: 四柱地支藏干含 日干(本气) 或 日干同五行 = 有根(实)
        all_branches = [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                        chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch]
        stem_root = any(
            ten_god(day_master, h) in ("比肩", "劫财")
            for b in all_branches
            for h, _ in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        if stem_el_cn and br_el_cn and stem_el_cn != br_el_cn:
            root_cn = "有根(实)" if stem_root else "无根(虚, ch14无根=虚)"
            result.xingxing_cheganshen = (f"外层{stem_el_cn}(日干{root_cn})·内里{br_el_cn}(坐支撤干神) — ch14撤干神心性二象")
            xing_ev.append(f"ch14撤干神: 日干{dm_stem}五行={stem_el_cn}({root_cn}), 坐支{dm_branch}五行={br_el_cn}(内里心性)")
        else:
            result.xingxing_cheganshen = "UNDETERMINED"
            xing_ev.append(f"ch14撤干神: 日干与坐支五行同(二象未分), 通根={'有' if stem_root else '无'}(实/虚)")
        result.xingxing_evidence = xing_ev
        # ── ③ 福分寿元 (ch2 合寿/解合 + ch4 禄印食=寿元星 + 枭克夺食伤 + 正印忌=操心) ──
        ff_ev = []
        # ㊻s121 修正: 枭神夺食 主宾归因(L1738 口径): 偏印落主位(日/时)=EFFECTIVE(为我夺食=夺寿元星),
        # 宾位(年/月)=INEFFECTIVE(非我夺, 不作夺寿断)。原 ㊻s120 查 NEGATIVE 归因漏掉
        # "主位枭神夺食 EFFECTIVE" 的夺寿口径。
        xiao_duo_shi = any(
            m == "枭神夺食" and a == ZuoGongAttribution["EFFECTIVE"]
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
        )
        # 食伤在局(寿元星有力)
        has_shishang = any(
            ten_god(day_master, getattr(chart, f"{p}_pillar").heavenly_stem) in ("食神", "伤官")
            for p in ("year", "month", "hour")
        ) or any(
            ten_god(day_master, h) in ("食神", "伤官")
            for b in [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                      chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch]
            for h, _ in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        if xiao_duo_shi:
            result.fufen_structure = "SHOUYUAN_XUEYUAN"
            ff_ev.append("ch4枭神夺食=夺寿元星(寿元受损/健康早夭隐患)")
        elif has_shishang:
            result.fufen_structure = "SHOULD_YANHE"
            ff_ev.append("ch4食伤在局=寿元星有力(寿元有根/合寿延)")
        else:
            # 正印为忌=操心劳碌(ch2 "正印为忌主烦心, 是心思操劳")
            yin_ji = "印制食伤" in [m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
                                     if a == ZuoGongAttribution["EFFECTIVE"]] and not has_shishang
            if yin_ji:
                result.fufen_structure = "CAOLAO"
                ff_ev.append("ch2正印为忌=操心劳碌(享福薄, 为别人操心)")
            else:
                result.fufen_structure = "UNDETERMINED"
                ff_ev.append("ch2/ch4寿元象未明: 无食伤寿元星且无枭克/印忌")
        result.fufen_evidence = ff_ev

    def _resolve_zei_bu(self, chart, result, day_master):
        """ch9 贼捕结构(原书ch9 L21'贼捕结构: 杀(捕)重而伤食(贼)轻, 喜行贼运';
        ch9 L9'官杀配伤食: 伤食制官杀或官杀制伤食(贼捕结构)→公检法/纪检/实权'):
        ㊻j 修 2: 原口径'主位五行克宾位无根'=盲派'贼捕'的错误理解(全量 0 命中),
        正确口径=制官/制杀做功 EFFECTIVE(伤食制官杀 或 官杀制伤食)+官杀在局, 与
        _resolve_official_structure 制官关键词同源, 但 贼捕是官贵域独立结构标记.
        判据:
          ① 官杀在局(officer_present, 与 official_event_structure 同源)
          ② 制官类方法 EFFECTIVE(伤官制官/食伤制杀/刑制正官/刑制七杀/冲制官杀/合正官/合七杀/
             穿制正官/穿制七杀/印化官杀/印制官杀, 与 _resolve_official_structure 制官关键词一致)
          ③ 贼捕特化: 伤食制官杀(伤食=贼, 官杀=捕, 贼制捕=纪检实权)
             或 官杀制伤食(捕制贼=执法) 两种方向, 命中任一即 ZEI_BU."""
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        stems = [
            chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
            chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
        ]
        officer_present = (
            any(ten_god(day_master, st) in GROUP_GUAN for st in stems)
            or any(ten_god(day_master, h) in GROUP_GUAN
                   for b in branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, []))
        )
        # 制官关键词(与 _resolve_official_structure control_officer_keywords 同源, 贼捕口径收窄:
        # 只取'伤食制官杀'(贼制捕=纪检) + '官杀制伤食'(捕制贼=执法), 含 刑/冲/穿/合 互动制官)
        ZHB_KEYWORDS = (
            "伤官制官", "食伤制杀",
            "刑制正官", "刑制七杀", "冲制官杀", "穿制正官", "穿制七杀",
            "合正官", "合七杀",
            "印制官杀", "印化官杀",
            "官杀制食伤", "官杀制伤",
        )
        eff_methods = [
            m for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
            if a == ZuoGongAttribution["EFFECTIVE"]
        ]
        zhb_hit = any(kw in eff_methods or any(kw in m for m in eff_methods)
                       for kw in ZHB_KEYWORDS)
        if officer_present and zhb_hit:
            result.zei_bu = "ZEI_BU"
            hit_kws = [kw for kw in ZHB_KEYWORDS
                       if kw in eff_methods or any(kw in m for m in eff_methods)]
            result.zei_bu_reason = (
                f"ch9贼捕结构: 官杀在局+制官EFFECTIVE({'+'.join(hit_kws[:3])})"
                f"=纪检/公检法/实权(原书ch9'伤食制官杀(贼捕)→公检法/纪检/实权')"
            )
        else:
            result.zei_bu = "NO"
            if not officer_present:
                result.zei_bu_reason = "官杀不在局, 非贼捕结构"
            else:
                result.zei_bu_reason = "官杀在局但制官方法未EFFECTIVE, 非贼捕结构"

    def _resolve_body_candidate(self, chart, result, day_master):
        """身体/疾病象（§64）。原书：身体象必须 IMAGE+PALACE+TEN_GOD+INTERACTION
        +TEMPORAL_TRIGGER；不得单一五行推断诊断。
        只输出 BODY_EVENT_CANDIDATE（对象+机制），部位/疾病名=UNDETERMINED。
        禄怕见绝更怕穿害（盲派身体章：禄神被穿害则受损）。
        ㊻s95 ch4 子女系统：原书ch4 L29"正官为女、七杀为儿"（子女星=官杀，按性别定）
        + L11"时支空=子女迟育或有损"（时柱被冲/穿=子女宫受损=子息不利=凶）
        + L2207"官杀/食伤做功=子息可断"（子女星做功=吉）：
        子女域输出 child_event_structure: child_star_present(子女星在局) +
        hour_attacked(时柱被冲穿=子女宫受损) + child_state(吉/凶/中性)"""
        branches = [
            chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch,
        ]
        # 禄神（日主禄位）
        dm_lu = road_branch(day_master)
        lu_present = dm_lu in branches
        # V3.4.3 【禄被合克】（对齐段氏原书禄被合克原文）：
        # "巳申合：传统为合化水，盲派为合克（火克金）"；"禄怕见绝更怕穿害"——
        # 禄支被六合且相克之支合克（巳火合克申金禄）=禄神环境恶劣。
        lu_attacked = any(
            b != dm_lu and (BRANCH_CHONG.get(b) == dm_lu or BRANCH_CHUAN.get(b) == dm_lu)
            for b in branches
        )
        lu_he_ke = any(
            b != dm_lu and BRANCH_LIUHE.get(b) == dm_lu
            and CONTROLS.get(_branch_element(b)) == _branch_element(dm_lu)
            for b in branches
        )
        lu_attacked = lu_attacked or lu_he_ke
        # V3.4.3 【燥土脆金伤禄】（对齐段氏原书燥土脆金原文"如四柱无水，
        # 见未戌之燥土定主脆金"，VERIFY-BLIND-034）：禄支五行=金 且 局有未/戌燥土
        # 且 四柱无水（无壬癸干、无亥子支）→ 禄被燥土脆金。
        stems_l = [
            chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
            chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
        ]
        lu_cui_jin = (
            _branch_element(dm_lu) == "METAL"
            and any(b in DRY_EARTH_BRANCHES for b in branches)
            and not any(s in WATER_STEMS for s in stems_l)
            and not any(b in WATER_BRANCHES for b in branches)
        )
        lu_attacked = lu_attacked or lu_cui_jin
        # 禄神受穿 NEGATIVE（V3.2 做功域已输出）
        lu_negative = any(
            '禄' in m and a == ZuoGongAttribution["NEGATIVE"]
            for m, a in zip(result.zuo_gong_methods, result.zuo_gong_attributions)
        )
        # 羊刃(排盘层 shensha YANG_REN): 日主禄位支=羊刃(甲卯/丙巳/戊巳/庚酉/壬亥)
        # V3.6.9⑬ 修(可真值"刃"缺口 9 例): 日支坐刃=结构事实, 即使 刃 未被冲 亦 应 体现.
        # 原书"坐刃": 日主 坐 刃 支(阳干 刃=临官; 阴干 以 禄 代 刃, 盲派通例 不论 阴阳 一律 刃=临官).
        # 修后: 刃 存在(任一 支 坐 刃) → 体 候选 YANG_REN_PRESENT(无 冲 时), 刃 逢 冲 → YANG_REN_CLASHED.
        yang_ren = [b for b in branches if b in getattr(chart, 'shensha', {}).get('YANG_REN', [])]
        ren_clashed = any(BRANCH_CHONG.get(b) in yang_ren for b in branches)
        # ㊻s124h 身体域(原书ch4"禄也是身体"): 禄 被 穿 但 未 被 冲(受 穿 而 非 受 冲 = 慢 病 方 向,
        # ch4"禄 神 受 穿"口 经). lu_attacked 已 含 冲/穿/合 克/脆 金 全 口 经, 此 处 仅
        # 筛 出 "仅 被 穿"(BRANCH_CHUAN 有 指 向 日 主 禄 位, 且 无 BRANCH_CHONG 指 向 日 主 禄 位).
        lu_chuan_only = lu_present and any(
            b != dm_lu and BRANCH_CHUAN.get(b) == dm_lu for b in branches
        ) and not any(
            b != dm_lu and BRANCH_CHONG.get(b) == dm_lu for b in branches
        )
        if lu_present and (lu_attacked or lu_negative):
            candidate = "LU_UNDER_ATTACK"
        elif yang_ren and ren_clashed:
            candidate = "YANG_REN_CLASHED"   # 盲派口诀: 羊刃逢冲血光之灾
        elif lu_chuan_only:
            candidate = "LU_UNDER_ATTACK"     # 禄 仅 被 穿(未 冲) = 身 体 受 穿 = 慢 病(ch4)
        elif yang_ren:
            candidate = "YANG_REN_PRESENT"    # V3.6.9⑬: 坐刃结构事实(无冲), 原书"坐刃"
        else:
            candidate = "UNDETERMINED"
        # V3.6.9㊼ ch5 宫位八维身体映射(原书ch5"身体类象: 年=腿足四肢, 月=躯干脊肩背, 日支=五脏六腑心脑髓, 时=头面手眼嘴耳鼻排泄器"):
        # 禄神所在宫位=身体受损部位(原书宫位八维"身体"维度, 非单一五行推断诊断):
        # 禄在年支=腿足四肢 / 禄在月支=躯干脊肩背 / 禄在日支=五脏六腑心脑髓 / 禄在时支=头面手眼嘴耳鼻排泄器
        # 禄被冲穿=对应宫位身体部位受损(做功于该柱). 若禄不在四柱(无禄)=UNDETERMINED(不表部位).
        body_part_map = {
            "YEAR": "腿足四肢",
            "MONTH": "躯干脊肩背",
            "DAY": "五脏六腑心脑髓",
            "HOUR": "头面手眼嘴耳鼻",
        }
        body_part_map = {
            "YEAR": "腿足四肢",
            "MONTH": "躯干脊肩背",
            "DAY": "五脏六腑心脑髓",
            "HOUR": "头面手眼嘴耳鼻",
        }
        pillar_to_name = {
            chart.year_pillar.earthly_branch: "YEAR",
            chart.month_pillar.earthly_branch: "MONTH",
            chart.day_pillar.earthly_branch: "DAY",
            chart.hour_pillar.earthly_branch: "HOUR",
        }
        if lu_present:
            lu_pillar_name = pillar_to_name.get(dm_lu, "UNDETERMINED")
            body_part = body_part_map.get(lu_pillar_name, "UNDETERMINED")
            # 禄被冲穿=该宫位身体受损(部位定象)
            if lu_attacked or lu_negative:
                body_part_confirmed = body_part
            else:
                body_part_confirmed = "UNDETERMINED"
        else:
            # 无禄(禄不在四柱): 查羊刃所在柱位(羊刃=禄之上位, 同柱位身体映射)
            if yang_ren:
                ren_pillar_name = pillar_to_name.get(yang_ren[0], "UNDETERMINED")
                body_part = body_part_map.get(ren_pillar_name, "UNDETERMINED")
                body_part_confirmed = body_part if ren_clashed else "UNDETERMINED"
            else:
                body_part = "UNDETERMINED"
                body_part_confirmed = "UNDETERMINED"
        result.body_event_candidate = {
            "lu_present": str(lu_present),
            "lu_attacked": str(lu_attacked or lu_negative),
            "yang_ren": sorted(yang_ren) or ["UNDETERMINED"],
            "candidate": candidate,
            "body_part": body_part_confirmed,   # V3.6.9㊼ ch5宫位八维身体映射(原书ch5"年=腿足/月=躯干/日支=五脏/时=头面")
            "body_part_palace": body_part,       # 宫位映射(即使未冲穿也表部位象, 冲穿才确认受损)
        }
        result.rules_triggered.append("EVT-BODY-001")
        # ㊻s95 ch4 子女系统(原书ch4 L29"正官为女、七杀为儿" + L11"时支空=子女迟育或有损"):
        # 子女星=官杀(男命杀=儿/官=女, 女命官=子/杀=女, 按性别定)。
        child_stems = [
            chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
            chart.day_pillar.heavenly_stem, chart.hour_pillar.heavenly_stem,
        ]
        child_star_present = any(
            ten_god(day_master, s) in GROUP_GUAN for s in child_stems
        ) or any(
            ten_god(day_master, h) in GROUP_GUAN
            for b in branches for h, _p in BRANCH_HIDDEN_STEMS.get(b, [])
        )
        hour_branch = chart.hour_pillar.earthly_branch
        hour_attacked_child = any(
            BRANCH_CHONG.get(b) == hour_branch or BRANCH_CHUAN.get(b) == hour_branch
            for b in [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                      chart.day_pillar.earthly_branch]
        )
        # ㊻s96 ch4 L11 原文收窄: "时支**空亡**=子女迟育或有损"——原文是"空亡"口径, 非"冲穿"口径.
        # ㊻s95 误用 hour_attacked(冲穿) 判凶, 癸丑庚申丙午戊子(女命生两女=吉) 午冲子=hour_attacked
        # 误判 NEGATIVE. 修后: 凶判须 时支空亡(原书明列), 冲穿仅作结构标注(不入吉凶判定).
        # 空亡查法(ch4 L14"四柱空亡查法: 以日柱或年柱为主, 观他支中见者为空"):
        # 甲子旬(甲子→癸酉)空戌亥; 甲戌旬(甲戌→癸未)空申酉; 甲申旬(甲申→癸巳)空午未;
        # 甲午旬(甲午→癸卯)空辰巳; 甲辰旬(甲辰→癸丑)空寅卯; 甲寅旬(甲寅→癸亥)空子丑.
        XUN_KONG = {
            "甲子": ("XU", "HAI"), "甲戌": ("SHEN", "YOU"), "甲申": ("WU", "WEI"),
            "甲午": ("CHEN", "SI"),  "甲辰": ("YIN", "MAO"), "甲寅": ("ZI", "CHOU"),
        }
        # 以日柱定旬空亡: 日柱天干所在旬
        day_stem = chart.day_pillar.heavenly_stem
        day_branch = chart.day_pillar.earthly_branch
        # 旬首 = 甲X, 其中 X = 日柱干序与支序之差决定的支 (干序%12==支序%12 时旬首支=日支)
        # 准确查法: 旬首支序 = (支序 - 干序) mod 12
        ZHI_IDX = {"ZI": 0, "CHOU": 1, "YIN": 2, "MAO": 3, "CHEN": 4, "SI": 5,
                   "WU": 6, "WEI": 7, "SHEN": 8, "YOU": 9, "XU": 10, "HAI": 11}
        GAN_IDX = {"JIA": 0, "YI": 1, "BING": 2, "DING": 3, "WU": 4, "JI": 5,
                   "GENG": 6, "XIN": 7, "REN": 8, "GUI": 9}
        xun_shou_branch = (ZHI_IDX.get(day_branch, 0) - GAN_IDX.get(day_stem, 0)) % 12
        ZHI_NAMES = ["ZI", "CHOU", "YIN", "MAO", "CHEN", "SI", "WU", "WEI", "SHEN", "YOU", "XU", "HAI"]
        xun_shou_key = f"甲{ZHI_NAMES[xun_shou_branch]}"
        kong_wang = XUN_KONG.get(xun_shou_key, ())
        hour_kongwang = hour_branch in kong_wang  # 时支空亡(ch4 L11 原书明列=子女迟育/有损)
        # hour_attacked 仅作结构标注(冲穿子女宫), 不入凶判(原书无"时柱被冲=子女不利"明列支撑)
        if child_star_present and hour_kongwang:
            child_state = "NEGATIVE"  # 子女星present + 时支空亡 = 子女迟育/有损(ch4 L11 原书明列)
        elif child_star_present:
            child_state = "POSITIVE"  # 子女星present + 时支未空 = 子息可断(ch4 L29"官杀做功=子息可断")
        else:
            child_state = "UNDETERMINED"  # 子女星absent = 不可断(ch4 无"不在局=无子"明列支撑)
        result.child_event_structure = {
            "child_star_present": str(child_star_present),
            "hour_kongwang": str(hour_kongwang),
            "hour_attacked": str(hour_attacked_child),  # 结构标注(冲穿子女宫), 不入吉凶判定
            "child_state": child_state,
        }
        result.rules_triggered.append("EVT-CHILD-001")

    def get_adapter(self) -> "BlindAdapter":
        return BlindAdapter(self)


# ─── 盲派适配器 ───────────────────────────────────────────────────────────────

class BlindAdapter(BaseAdapter):
    """盲派信号适配器"""
    ENGINE_NAME = "BLIND"

    def adapt(self, engine_output: BlindBaziResult, context: Optional[AdapterContext] = None) -> List[CanonicalSignal]:
        return engine_output.signals


# ─── 导出接口 ─────────────────────────────────────────────────────────────────

def compute_blind_bazi(birth: Tuple[int, int, int, int], gender: str = "male") -> BlindBaziResult:
    """盲 派 引 擎 对 外 入 口(盲 派 = 排 盘 + 盲 派 断 事 一 条 龙).

    ㊻s85 删 旧 误 植: 本 函 数 尾 部 原 误 挂 一 个 同 名 但 不 属 于 任 何 类 的
    "_resolve_zheng_fan_ju(self, chart, result)" 简 化 版 定 义(输 出 ZHENG/FAN),
    该 版 被 BlindBaziEngine 类 体 内 后 定 义 的 方 法 覆 盖, 致 实 际 运 行 走 简 化 口 径
    (日 干 外 用/内 扶 vs 日 支 单 向 比 对), 跳 过 ch1 定 势 法 的 R1-R4(定 势 → 日 柱
    做 功 顺/逆 势 → 正 反 局), 盲 派 底 层 序 列 偏 了。已 删 除, 恢 复 L2388 的
    R1-R4 定 势 法 版 为 正 局/反 局 唯 一 入 口。
    """
    engine = BlindBaziEngine()
    return engine.compute(birth, gender=gender)

    
