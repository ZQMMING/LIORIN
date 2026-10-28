"""ZIPING V3.1 喜用神裁定 (YongShen).

基于§28辨层结果，确定性判定喜用神.
铁律: LLM不得修改此模块的计算逻辑.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ═══════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════
@dataclass
class YongShenVerdict:
    """喜用神裁定结果."""
    # 核心裁定
    primary_yong: str = "UNKNOWN"     # 用神类型: WATER/METAL/EARTH/FIRE/WOOD
    primary_help: str = "UNKNOWN"     # 喜神辅助: WATER/METAL/EARTH/FIRE/WOOD
    Ji_shen: str = "UNKNOWN"          # 忌神: WATER/METAL/EARTH/FIRE/WOOD

    # 判定依据 (可追溯)
    basis: str = ""                   # 判定路径: "QTPJ-PROSPERITY" / "DT-BINGYAO" / ...
    evidence_refs: List[str] = field(default_factory=list)

    # 命局特征
    pattern_type: str = "NORMAL"      # NORMAL / YANSHANG / CONG ...
    body_state: str = "UNKNOWN"       # STRONG / WEAK / WANG_OVER / WANG_BUT_NOT_STRONG / BALANCED
    climate_state: str = "UNKNOWN"    # HOT / COLD / HOT_WET / DRY ...
    disease_state: str = "UNKNOWN"    # defined / absent
    tangguan_state: str = "UNKNOWN"   # TONGGUAN_ABSENT / OPPOSITION_RESOLVED / ...

    # 原文引用
    classic_quote: str = ""           # 穷通宝鉴/滴天髓原文
    source: str = ""                  # 经典名+篇名

    # 泛滥闸门
    flood_note: str = ""             # 命局太过(泛滥)的五行(离散计数), 触发制化路径时非空


# ═══════════════════════════════════════════════════════════════
# 五行映射
# ═══════════════════════════════════════════════════════════════
_WUXING_NAMES = {
    "WATER": "水", "METAL": "金", "EARTH": "土",
    "FIRE": "火", "WOOD": "木",
}

# 十神五行映射 (日主为基准)
TEN_GOD_TO_5X = {
    "食神": "OUTPUT", "伤官": "OUTPUT",   # 泄日主
    "偏财": "WEALTH", "正财": "WEALTH",   # 被日主克
    "七杀": "OFFICER", "正官": "OFFICER", # 克日主
    "偏印": "RESOURCE", "正印": "RESOURCE", # 生日主
    "比肩": "COMpanion", "劫财": "COMpanion",  # 同日主
}

# ═══════════════════════════════════════════════════════════════
# 五行生克制化枚举 (纯确定性表, 无百分比)
# ═══════════════════════════════════════════════════════════════
# 天干 → 五行
STEM_WUXING = {
    "JIA": "WOOD", "YI": "WOOD",
    "BING": "FIRE", "DING": "FIRE",
    "WU": "EARTH", "JI": "EARTH",
    "GENG": "METAL", "XIN": "METAL",
    "REN": "WATER", "GUI": "WATER",
}
# 十二支本气 → 天干 (用于统计五行个数)
BRANCH_MAIN_STEM = {
    "ZI": "GUI", "CHOU": "JI", "YIN": "JIA", "MAO": "YI",
    "CHEN": "WU", "SI": "BING", "WU": "DING", "WEI": "JI",
    "SHEN": "GENG", "YOU": "XIN", "XU": "WU", "HAI": "REN",
}
# 克我者 (X 被 KE_BY[X] 克)
KE_BY = {"WOOD": "METAL", "FIRE": "WATER", "EARTH": "WOOD",
          "METAL": "FIRE", "WATER": "EARTH"}
# 生我者 (X 由 SHENG_BY[X] 生)
SHENG_BY = {"WOOD": "WATER", "FIRE": "WOOD", "EARTH": "FIRE",
            "METAL": "EARTH", "WATER": "METAL"}
# 我生者 (X 生 _SHENG_OUT[X])
_SHENG_OUT = {"WOOD": "FIRE", "FIRE": "EARTH", "EARTH": "METAL",
              "METAL": "WATER", "WATER": "WOOD"}
# 我克者 (X 克 _KE_OUT[X])
_KE_OUT = {"WOOD": "EARTH", "FIRE": "METAL", "EARTH": "WATER",
           "METAL": "WOOD", "WATER": "FIRE"}

# 五行状态枚举 (8位计数: 4天干 + 4支本气, 逐值查表, 无比较运算)
_COUNT_TO_STATE = {
    0: "ABSENT",    # 绝
    1: "SCARCE",    # 弱
    2: "NORMAL",    # 常
    3: "ACTIVE",    # 旺 (偏旺未太过)
    4: "OVERFLOW",  # 太过 (泛滥)
    5: "EXTREME",   # 极端
    6: "EXTREME",
    7: "EXTREME",
    8: "EXTREME",
}
FLOOD_STATES = ("OVERFLOW", "EXTREME")  # 泛滥态 (集合成员判定, 非比较)


def _count_element(four_stems, four_branches, element):
    """统计某五行在 4天干+4支本气 中的个数 (离散计数, 非百分比)."""
    n = 0
    for s in four_stems or []:
        if STEM_WUXING.get(s) == element:
            n += 1
    for b in four_branches or []:
        main = BRANCH_MAIN_STEM.get(b, "")
        if STEM_WUXING.get(main) == element:
            n += 1
    return n


def _count_state(four_stems, four_branches, element):
    """计数 → 状态枚举 (逐值查表, 无 >= 比较运算)."""
    return _COUNT_TO_STATE.get(_count_element(four_stems, four_branches, element), "ABSENT")


def _flood_elements(four_stems, four_branches):
    """返回命局泛滥(太过)的五行集合.

    计数 → 状态枚举 → 状态 ∈ FLOOD_STATES (成员判定).
    纯查表, 无百分比, 无 >= 比较.
    """
    floods = set()
    for elem in ("WOOD", "FIRE", "EARTH", "METAL", "WATER"):
        if _count_state(four_stems, four_branches, elem) in FLOOD_STATES:
            floods.add(elem)
    return floods

# ═══════════════════════════════════════════════════════════════
# 喜用神裁定引擎
# ═══════════════════════════════════════════════════════════════
class YongShenEngine:
    """喜用神裁定引擎 — 纯确定性布尔规则."""

    # 调候表: 12组月令 x 10组日干 = 120组 (逐日干查表, 纯枚举)
    # 来源: 本地《穷通宝鉴》原文逐字定位 (引文带ref出处); 查不到的 note=fallback 走五行兜底
    # 注: 本表为 调候候选; 运行时还须过 泛滥闸门 (计数→状态枚举查表, 无百分比, 无比较)
    TIAOHOU_TABLE = {
        "YIN": {
            "JIA": {"yong": 'FIRE', "help": 'EARTH', "ji": 'METAL', "quote": '正月甲木，初春尚有馀寒，得丙癸逢，富贵双全。癸藏丙透，名寒木向阳，主大富贵。倘风水不及，亦不失儒林俊秀。如无丙癸，平常人', "ref": 'QTBJ_L3496', "note": 'fallback'},
            "YI": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '正月乙木，必须用丙，因天气尤有余寒，非丙不暖，虽有癸水，恐凝寒气，故以丙火为先，癸水次之。丙癸两透，科甲定然，或有丙无癸', "ref": 'QTBJ_L472', "note": 'parsed-med'},
            "BING": {"yong": 'WATER', "help": 'METAL', "ji": 'WOOD', "quote": '正月丙火，余寒未尽，以壬水为用，调和气候。', "ref": 'QTBJ_L9046', "note": 'fallback'},
            "DING": {"yong": 'METAL', "help": None, "ji": None, "cond": ['JIA'], "status": 'supported', "quote": '正月丁火，甲木当权，乃为母旺，非庚不能劈甲，何以引丁，姑用庚金。', "ref": 'QTBJ_L4540', "note": 'rev16'},
            "WU": {"yong": 'FIRE', "help": 'WOOD', "ji": 'WATER', "quote": '正月戊土，寅月木旺土虚，先丙为用。', "ref": 'QTBJ_L9090', "note": 'fallback'},
            "JI": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '正月己土，田园犹寒，用丙火温暖。', "ref": 'QTBJ_L9111', "note": 'parsed-med'},
            "GENG": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '正月庚金，寒气未退，用丁火暖之。', "ref": 'QTBJ_L9131', "note": 'parsed-med'},
            "XIN": {"yong": 'EARTH', "help": 'WATER', "ji": 'WOOD', "cond": [], "status": 'supported', "quote": '取己土为身之本，全赖壬水之功，己壬两透，支见庚制甲，科甲定然。', "ref": 'QTBJ_L5608', "note": 'rev16'},
            "REN": {"yong": 'METAL', "help": None, "ji": 'FIRE', "quote": '正月壬水，汪洋之象，用庚金发源。', "ref": 'QTBJ_L9172', "note": 'parsed-med'},
            "GUI": {"yong": 'METAL', "help": None, "ji": 'FIRE', "quote": '正月癸水，值三阳之后，雨露之精，其性至柔，先用辛金，生癸水之源，次用丙火照暖，名阴阳和合，万物发生，辛丙两透，金榜有名。', "ref": 'QTBJ_L6322', "note": 'parsed-med'},
        },
        "MAO": {
            "JIA": {"yong": 'METAL', "help": None, "ji": 'FIRE', "quote": '二月甲木，庚金得所，名阳刃驾杀，可云小贵，异途显达，或主武职，但要财资之。柱中逢才，英雄独压万人。', "ref": 'QTBJ_L3532', "note": 'parsed-med'},
            "YI": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '二月乙木，端用丙癸，或支成木局，有癸透乃作贵命，更得丙泄木气，上上之命，但须透癸。或水多困丙，多戊化癸，皆下格。亥卯未逢', "ref": 'QTBJ_L502', "note": 'parsed-high'},
            "BING": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '二月丙火，用壬者土为妻，水为子。用甲者木为妻，火为子。', "ref": 'QTBJ_L9047', "note": 'parsed-med'},
            "DING": {"yong": 'METAL', "help": 'WOOD', "ji": 'FIRE', "quote": '二月丁火，湿乙伤丁，先庚后甲，非不能去乙，非甲不能引丁。庚甲两透，科甲定然，庚透甲藏，亦有生贡，甲透庚藏，异路功名。或庚', "ref": 'QTBJ_L4582', "note": 'parsed-high'},
            "WU": {"yong": 'FIRE', "help": 'WOOD', "ji": 'WATER', "quote": '三春戊土，无丙照暖，戊土不生，无甲疏噼，戊土不灵，无癸滋润，万物不长。正二月先丙后甲，癸又次之。三月先甲后丙，癸又次之，', "ref": 'QTBJ_L7522', "note": 'parsed-high'},
            "JI": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '二月己土，阳气渐升，虽禾稼未成，万物出土，田园未展，先取甲木疏之，忌合，次取癸水润之，甲癸出乾，定主科甲，加以一丙出透，', "ref": 'QTBJ_L5116', "note": 'parsed-high'},
            "GENG": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '二月庚金，专用丁火，借甲引丁，借庚噼甲。无丁用丙者，富贵多出于勉强。', "ref": 'QTBJ_L7900', "note": 'parsed-high'},
            "XIN": {"yong": 'WATER', "help": 'METAL', "ji": 'FIRE', "quote": '二月辛金，丙先壬后，戊己次之。', "ref": 'QTBJ_L5962', "note": 'fallback'},
            "REN": {"yong": 'EARTH', "help": 'METAL', "ji": 'WOOD', "quote": '二月壬水，寒气初除，有并流之象，不用丙暖，专取戊土辛金，二月壬水，先戊后辛，庚金次之。戊辛两透，雁塔题名，戊透辛藏，亦有', "ref": 'QTBJ_L2788', "note": 'parsed-high'},
            "GUI": {"yong": 'METAL', "help": None, "ji": None, "cond": ['XIN'], "status": 'supported', "quote": '二月癸水，不刚不柔，乙木司令，泄弱元神，专用庚金为用，辛金次之，庚辛俱透，无丁出干者，贵由科甲，无庚辛者常人。', "ref": 'QTBJ_L6352', "note": 'rev16'},
        },
        "CHEN": {
            "JIA": {"yong": 'METAL', "help": None, "ji": 'FIRE', "quote": '三月甲木，木气相竭。先取庚金，次用壬水。庚壬两透，一榜堪图。但要运用相生，风水阴德，方许富贵。或见一二庚金，独取壬水。壬', "ref": 'QTBJ_L130', "note": 'parsed-high'},
            "YI": {"yong": 'WATER', "help": 'FIRE', "ji": 'EARTH', "quote": '三月乙木，阳气愈炽，先癸后丙。癸丙两透，不见己庚，玉堂之客。见己庚者，平常之人。或一乙逢庚，不见己者，亦主小富贵，但不显', "ref": 'QTBJ_L3910', "note": 'parsed-high'},
            "BING": {"yong": 'WATER', "help": 'WOOD', "ji": 'METAL', "cond": [], "status": 'supported', "quote": '三月丙火，气渐炎升，用壬水，或成土局，取甲木为辅，壬不可离，壬申两透，科甲定宜，惟忌庚出制甲，则秀才而已。', "ref": 'QTBJ_L4276', "note": 'rev16'},
            "DING": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '三月丁火，戊土司令，泄弱丁气，先用甲木引丁制土，次看庚金，庚甲两透，定主科甲，或一藏一透，终非白丁。', "ref": 'QTBJ_L4612', "note": 'parsed-med'},
            "WU": {"yong": 'WOOD', "help": 'FIRE', "ji": None, "cond": ['GUI'], "status": 'partially_supported', "quote": '三月戊土司令，不见丙甲癸者，愚而且贱，两癸透者、生员，甲癸俱藏者，只可云富，有癸异途。', "ref": 'QTBJ_L4858', "note": 'rev16'},
            "JI": {"yong": 'FIRE', "help": 'WATER', "ji": 'WATER', "quote": '三月己土，正栽培禾稼之时，先丙后癸，土暖而润，随用甲疏，三者俱透天干，必官居黄阁，或三者透一，科甲定然，但要得地，郤以庚', "ref": 'QTBJ_L5140', "note": 'parsed-high'},
            "GENG": {"yong": 'WOOD', "help": 'FIRE', "ji": 'METAL', "quote": '三月庚金，戊土司令，无生金之理，有埋金之忧，故先甲后丁，不用庚劈甲，三月之庚，土旺金顽，顽金宜丁，旺土须甲，乏甲不能立业', "ref": 'QTBJ_L5374', "note": 'parsed-high'},
            "XIN": {"yong": 'WATER', "help": 'WOOD', "ji": 'EARTH', "quote": '三月辛金，戊土司令，辛承正气，母旺子相，先壬后甲，壬甲两透，富贵必然，壬透甲藏，廪贡不失，甲透壬藏，富贵可云，壬甲皆无，', "ref": 'QTBJ_L5674', "note": 'parsed-high'},
            "REN": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '三月壬水，戊土司权，死有推山塞海之患，先用甲疏季土，次取庚金。甲庚俱透，科甲定然，甲透庚藏，修齐品格，甲藏有根，可云俊秀', "ref": 'QTBJ_L2824', "note": 'parsed-med'},
            "GUI": {"yong": 'FIRE', "help": 'WOOD', "ji": 'EARTH', "quote": '三月癸水，从化者多，得化者荣禄，不化者平常。或支成水局，又见己土，无木，乃假杀格，有甲出者，常人。或支坐四库，又得甲透，', "ref": 'QTBJ_L6376', "note": 'fallback'},
        },
        "SI": {
            "JIA": {"yong": 'WATER', "help": 'FIRE', "ji": 'EARTH', "quote": '四月甲木，退气，丙火司权，先癸后丁。庚金太多，甲反受病。若得壬水，方配得中和，此人性好清高，假装富贵。即荫袭显达，终日好', "ref": 'QTBJ_L8881', "note": 'parsed-high'},
            "YI": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '四月乙木，自有丙火，端取癸水为尊。四月乙木专用癸水，丙火酌用，虽以庚辛佐癸，须辛透为清。癸透、庚辛又透，科甲定然，独一点', "ref": 'QTBJ_L3952', "note": 'parsed-high'},
            "BING": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '四月丙火，建禄于巳，火势炎炎，宜专用壬水，解炎威之力，成既济之功。如无壬水，孤阳失辅，难透清光，得庚发水源，方为有根之水', "ref": 'QTBJ_L4312', "note": 'parsed-high'},
            "DING": {"yong": 'METAL', "help": None, "ji": 'FIRE', "quote": '四月丁火乘旺，虽取甲引丁，必用庚劈甲，伐甲、方云木火通明，甲多、又取庚为先。', "ref": 'QTBJ_L4630', "note": 'parsed-high'},
            "WU": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '四月戊土，阳气发升，寒气内藏，外实内虚，不畏火炎，无阳气相催，万物不长，故先用甲疏劈，次取丙癸为佐。', "ref": 'QTBJ_L4888', "note": 'parsed-med'},
            "JI": {"yong": 'WATER', "help": 'METAL', "ji": 'FIRE', "quote": '三夏己土，火气蒸腾，用水调和。 (三季总论)', "ref": 'QTBJ_L9117', "note": 'fallback'},
            "GENG": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '四月庚金，须用壬丙戊，但非拘执先后，宜分病用药，妻子仝前。', "ref": 'QTBJ_L5422', "note": 'parsed-med'},
            "XIN": {"yong": 'WATER', "help": 'METAL', "ji": 'FIRE', "quote": '四月辛金，时道首夏，忌丙火之燥烈，喜壬水之洗淘，支成金局，水透出乾，有木制戊，名一清澈底，科甲功名，癸透壬藏，富真贵假，', "ref": 'QTBJ_L5704', "note": 'fallback'},
            "REN": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '四月壬水，丙火司权，水弱极矣，专取壬水比肩为助，次取辛金发源，且暗合丙火，庚金为佐。', "ref": 'QTBJ_L6100', "note": 'parsed-high'},
            "GUI": {"yong": 'METAL', "help": None, "ji": 'FIRE', "quote": '四月癸水，专用辛金方妙。', "ref": 'QTBJ_L6406', "note": 'parsed-high'},
        },
        "WU": {
            "JIA": {"yong": 'WATER', "help": 'FIRE', "ji": None, "cond": ['GENG'], "status": 'supported', "quote": '五六月甲木，木性虚焦，一理共推。五月先癸后丁，庚金次之。', "ref": 'QTBJ_transcription(qiongtong:c002:p0028)', "note": 'rev16'},
            "YI": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '五月乙木，丁火司权，禾稼俱旱。上半月属阳，仍用癸水。下半月属阴，三伏生寒，丙癸齐用。柱多金水，丙火为先，余皆用癸水为先。', "ref": 'QTBJ_L8998', "note": 'parsed-med'},
            "BING": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '五月丙火，合炎上格，则不喜水破格。用癸无根，定主目疾。', "ref": 'QTBJ_L7054', "note": 'parsed-med'},
            "DING": {"yong": 'WATER', "help": 'METAL', "ji": 'WOOD', "cond": [], "status": 'supported', "quote": '五月丁火，时归建禄，不宜乱用甲木。', "ref": 'QTBJ_L4660', "note": 'rev16'},
            "WU": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '五月戊土，仲夏火炎，先看壬水，次取甲木，丙火酌用，用癸力微。', "ref": 'QTBJ_L1600', "note": 'parsed-med'},
            "JI": {"yong": 'WATER', "help": 'METAL', "ji": 'FIRE', "quote": '三夏己土，火气蒸腾，用水调和。 (三季总论)', "ref": 'QTBJ_L9117', "note": 'fallback'},
            "GENG": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '五月庚金，丁火旺烈，庚金败地，专用壬水，癸又次之。', "ref": 'QTBJ_L5434', "note": 'parsed-high'},
            "XIN": {"yong": 'WATER', "help": 'METAL', "ji": 'FIRE', "quote": '五月辛金，壬、癸、己、三者皆用。或壬己两透，支见癸水，不剋，定主显达。即己藏支，亦有廪贡。或无壬有己，须得异途。或癸出有', "ref": 'QTBJ_L8200', "note": 'fallback'},
            "REN": {"yong": 'METAL', "help": 'WATER', "ji": 'FIRE', "quote": '五月壬水，辛癸亦可参用，其理与四月皆同。', "ref": 'QTBJ_L6130', "note": 'fallback'},
            "GUI": {"yong": 'METAL', "help": 'WATER', "ji": 'FIRE', "quote": '五月癸水，至弱无根，必须庚辛为生身之本，但丁火司权，金难敌火，安能滋养癸水，宜见比劫，方得辛金之用，五月癸水，庚辛壬参酌', "ref": 'QTBJ_L6412', "note": 'fallback'},
        },
        "WEI": {
            "JIA": {"yong": 'WATER', "help": 'METAL', "ji": 'FIRE', "quote": '六月甲木，木盛先庚，庚盛先丁。五月癸庚两透，为上上之格。六月庚丁两透，亦为上上之格。用神既透，木火通明，自然大富大贵。或', "ref": 'QTBJ_L3622', "note": 'fallback'},
            "YI": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '六月乙木，气退枯焦，用癸水切忌戊己杂乱，则为下格。或甲木高透，制伏土神名为去浊留清，可许俊秀。土多乏甲秀气脱空，庸人而已', "ref": 'QTBJ_L3988', "note": 'parsed-med'},
            "BING": {"yong": 'WATER', "help": 'METAL', "ji": 'FIRE', "quote": '六月丙火退气，三代生寒，壬水为用，取庚辅佐。庚壬两透，贴身相生，可云科甲名宦，若无庚有壬，不见戊出，小富小贵，见戊制壬则', "ref": 'QTBJ_L4366', "note": 'fallback'},
            "DING": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '六月丁火，阴柔退气，但值三伏生寒，丁弱极矣，专取甲木，壬水次之。若得甲出天干，支成木局，见亥中之壬，为木神有根，接引丁火', "ref": 'QTBJ_L4690', "note": 'parsed-high'},
            "WU": {"yong": 'WATER', "help": 'FIRE', "ji": None, "cond": ['JIA'], "status": 'supported', "quote": '六月戊土，遇夏干枯，先看癸水，次用丙火甲木。', "ref": 'QTBJ_L1624', "note": 'rev16'},
            "JI": {"yong": 'WATER', "help": 'METAL', "ji": 'FIRE', "quote": '三夏己土，火气蒸腾，用水调和。 (三季总论)', "ref": 'QTBJ_L9117', "note": 'fallback'},
            "GENG": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '六月庚金，三伏生寒，顽钝极矣，先用丁火，次取甲木。', "ref": 'QTBJ_L5458', "note": 'parsed-med'},
            "XIN": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '六月辛金，己土当权，辅助太多，恐掩金光，先用壬水，取庚佐之，壬庚两透，科甲功名，即不出乾，藏支得所，亦有荣华，但忌戊出，', "ref": 'QTBJ_L5746', "note": 'parsed-med'},
            "REN": {"yong": 'METAL', "help": 'WOOD', "ji": 'FIRE', "quote": '六月壬水，先辛后甲，次取癸水。辛甲两透，富贵清高。甲藏辛透，贡监生员。辛藏甲透，异途武职。甲壬两透，无伤，有治国之贵。即', "ref": 'QTBJ_L8470', "note": 'parsed-high'},
            "GUI": {"yong": 'METAL', "help": 'WATER', "ji": 'FIRE', "quote": '六月癸水，有上下月之分，下半月庚辛有气，上半月庚辛休囚，凡六癸日，多不验者，何也，俗士不知此理，因未中有乙巳同宫，破而不', "ref": 'QTBJ_L6436', "note": 'fallback'},
        },
        "SHEN": {
            "JIA": {"yong": 'FIRE', "help": 'METAL', "ji": None, "cond": ['WU'], "status": 'supported', "quote": '七月甲木，丁火为尊，庚金次之，庚金不可少。', "ref": 'QTBJ_L3700', "note": 'rev16'},
            "YI": {"yong": 'WATER', "help": 'METAL', "ji": 'FIRE', "quote": '七月乙木，庚金乘令，庚虽输情于乙妹，怎奈干乙难合支金。柱见庚多，乙难受载。或丙透干，又加巳出埋金，此格可云科甲。有己透、', "ref": 'QTBJ_L4042', "note": 'fallback'},
            "BING": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '七月丙火，太阳转西，阳气衰矣，日近西山，见土皆晦，惟日照湖海，暮夜光天，故仍用壬水辅映光辉。', "ref": 'QTBJ_L4390', "note": 'parsed-med'},
            "DING": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '七月丁火，退气柔弱，端用甲木，金虽乘旺司权，无伤丁之理，仍取庚劈甲，为引火之物，或借丙暖金晒甲，不虑丙夺丁光，凡两丙夹丁', "ref": 'QTBJ_L4714', "note": 'parsed-high'},
            "WU": {"yong": 'FIRE', "help": 'WATER', "ji": 'WATER', "quote": '七月戊土，阳气渐入，寒气渐出，先丙后癸，甲木次之。丙癸甲透者，富贵极品，癸藏丙透，不仅秀才，丙申两透，癸水会局藏辰，亦不', "ref": 'QTBJ_L4948', "note": 'parsed-high'},
            "JI": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '三秋己土，金水相生，用丙癸。 (三季总论)', "ref": 'QTBJ_L9120', "note": 'parsed-med'},
            "GENG": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '七月庚金，刚锐极矣，专用丁火煆炼，次取木引丁，故曰，秋金锐锐最为奇，壬癸相逢总不宜，如逢木火来成局，试看福寿与天齐，如得', "ref": 'QTBJ_L5482', "note": 'parsed-high'},
            "XIN": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '七月辛金，壬不在多，故书云：水浅金多，号曰体全之象，壬水为尊，甲戊酌用可也，癸水不可为用。，当权得令，旺之极矣，专用壬水', "ref": 'QTBJ_L2530', "note": 'parsed-high'},
            "REN": {"yong": 'EARTH', "help": None, "ji": 'WOOD', "quote": '七月壬水，专用戊土。丁火为佐。', "ref": 'QTBJ_L8494', "note": 'parsed-high'},
            "GUI": {"yong": 'FIRE', "help": 'WOOD', "ji": 'METAL', "quote": '七月癸水，正母旺子相之时，癸虽死申，殊不知申中有庚生之，名死处逢生，弱中复强，即运行西北，亦不死也，但庚司令，刚锐极矣，', "ref": 'QTBJ_L6442', "note": 'fallback'},
        },
        "YOU": {
            "JIA": {"yong": 'FIRE', "help": None, "ji": None, "cond": ['BING', 'GENG'], "status": 'supported', "quote": '八月甲木，木囚金旺。丁火为先，次用丙火，庚金再次。', "ref": 'QTBJ_L3706', "note": 'rev16'},
            "YI": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '八月乙木，芝兰禾稼均退，以丹桂为乙木。在白露之后，桂蕊未开，用癸水，以滋桂萼。若秋分后，桂花已开，却喜向阳，又宜用丙，癸', "ref": 'QTBJ_L9018', "note": 'parsed-med'},
            "BING": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '八月丙火，日近黄昏，丙之馀光，存于湖海，仍用壬水辅映。', "ref": 'QTBJ_L4408', "note": 'parsed-med'},
            "DING": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '三秋丁火，火气渐衰，用甲为君，庚金为佐。', "ref": 'QTBJ_L9079', "note": 'parsed-med'},
            "WU": {"yong": 'FIRE', "help": 'WATER', "ji": 'WATER', "quote": '八月戊土，金泄身寒，赖丙照暖，喜水滋润，先丙后癸，不必木疏。丙癸两透，科甲中人，丙透癸藏，可许入泮，癸透丙藏，纳资得官，', "ref": 'QTBJ_L1666', "note": 'parsed-high'},
            "JI": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '三秋己土，金水相生，用丙癸。 (三季总论)', "ref": 'QTBJ_L9120', "note": 'parsed-med'},
            "GENG": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '八月庚金，刚锐支退，用丁甲，丙不可少，若丁甲透，又见一丙，功名显赫，且见羊刃无刑冲，丙杀藏支，名为羊刃架杀，主出将入相，', "ref": 'QTBJ_L5506', "note": 'parsed-med'},
            "XIN": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '八月辛金，当权得令，旺之极矣，专用壬水淘洗，故云金见水以流通，如见戊己，则生扶太过，故以土为病，见甲制土，方妙，无戊，不', "ref": 'QTBJ_L5788', "note": 'parsed-high'},
            "REN": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '八月壬水，辛金司权，正金白水清，忌戊土为病，专用甲木，甲木一透制戊，壬水澈底澄清，名高翰苑，若甲出时干，功名显达，设见庚', "ref": 'QTBJ_L6196', "note": 'parsed-high'},
            "GUI": {"yong": 'METAL', "help": 'WATER', "ji": 'FIRE', "quote": '八月癸水，丙辛皆用。', "ref": 'QTBJ_L8680', "note": 'fallback'},
        },
        "XU": {
            "JIA": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '九月甲木，耑用丁癸，见戊透必贵。如戊戌、壬戌、甲子、甲申，支成水局，干有壬水，正合贵元武之说。配得中和，一榜之命，家计丰', "ref": 'QTBJ_L6748', "note": 'parsed-high'},
            "YI": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '九月乙木，用癸丙得局可福。甲木多者，扶同木论。', "ref": 'QTBJ_L9025', "note": 'parsed-med'},
            "BING": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '九月丙火，火气愈退，所忌土晦光，必须先用甲木，次取壬水。', "ref": 'QTBJ_L4432', "note": 'parsed-med'},
            "DING": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '三秋丁火，火气渐衰，用甲为君，庚金为佐。 (三季总论)', "ref": 'QTBJ_L9079', "note": 'parsed-med'},
            "WU": {"yong": 'WOOD', "help": 'WATER', "ji": None, "cond": ['BING', 'GUI'], "status": 'supported', "quote": '九月戊土当权，不可专用丙，先看甲木，次取癸水。', "ref": 'QTBJ_L4996', "note": 'rev16'},
            "JI": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '三秋己土，金水相生，用丙癸。 (三季总论)', "ref": 'QTBJ_L9120', "note": 'parsed-med'},
            "GENG": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '九月庚金，戊土司令，最怕土厚埋金，宜先用甲疏，后用壬洗，则金自出矣，忌见己土浊壬。', "ref": 'QTBJ_L5530', "note": 'parsed-med'},
            "XIN": {"yong": 'WATER', "help": 'WOOD', "ji": None, "cond": [], "status": 'supported', "quote": '九月辛金，成土司令，母旺子相，须甲疏土，壬泄旺金，先壬后甲。', "ref": 'QTBJ_L5854', "note": 'rev16'},
            "REN": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '九月壬水，专用甲木，次用丙火。用土者，火妻土子。司权，至旺之极，取戊为用，若生辰日干，又见辰时，必须戊透，又须庚制甲，不', "ref": 'QTBJ_L8518', "note": 'parsed-high'},
            "GUI": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '九月癸水，辛甲并用。', "ref": 'QTBJ_L6478', "note": 'parsed-high'},
        },
        "HAI": {
            "JIA": {"yong": 'FIRE', "help": 'EARTH', "ji": 'WATER', "quote": '十月甲木，庚丁为要，丙火次之。忌壬水泛身，须戊土制之。若庚丁两透，又加戊出乾，名曰去浊留清，富贵之极，即乏丁火，亦稍有富', "ref": 'QTBJ_L400', "note": 'fallback'},
            "YI": {"yong": 'FIRE', "help": 'EARTH', "ji": 'WATER', "quote": '十月乙木，水冷气寒，木性生寒，丁先庚后，丙火佐之。庚丁两透，支成木局，富贵有准。或庚透丁藏，不见癸水，为寒木向阳，主小贵', "ref": 'QTBJ_L9029', "note": 'fallback'},
            "BING": {"yong": 'WOOD', "help": 'EARTH', "ji": None, "cond": ['GENG', 'REN'], "status": 'supported', "quote": '十月丙火，太阳失令，得见甲戊庚出干，可云科甲。', "ref": 'QTBJ_L4456', "note": 'rev16'},
            "DING": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '三冬丁火，火弱无烟，专用甲乙生助。 (三季总论)', "ref": 'QTBJ_L9082', "note": 'parsed-high'},
            "WU": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '十月戊土，时值小阳，阳气略出，先用甲木，次取丙火，非甲，土不灵，非丙，土不暖，安能发生万物，甲丙两出，富贵中人。或甲得长', "ref": 'QTBJ_L5020', "note": 'parsed-med'},
            "JI": {"yong": 'FIRE', "help": 'WOOD', "ji": 'WATER', "quote": '三冬己土，冻土寒冰，用火破寒。 (三季总论)', "ref": 'QTBJ_L9123', "note": 'fallback'},
            "GENG": {"yong": 'FIRE', "help": 'WOOD', "ji": 'WATER', "quote": '十月庚金，水冷性寒，非丁莫造，非丙不暖。', "ref": 'QTBJ_L2290', "note": 'fallback'},
            "XIN": {"yong": 'WATER', "help": None, "ji": 'EARTH', "quote": '十月辛金，时值小阳，阳渐升，寒气将降，先用壬水，次取丙火，壬丙两透，金榜题名，何也，盖辛金有壬水丙火，名金白水清，又在亥', "ref": 'QTBJ_L5896', "note": 'parsed-med'},
            "REN": {"yong": 'EARTH', "help": None, "ji": 'WOOD', "quote": '十月壬水司权，至旺之极，取戊为用，若生辰日乾，又见辰时，必须戊透，又须庚制甲，不伤戊土，戊庚两全，定主登科及第，，位显权', "ref": 'QTBJ_L6232', "note": 'parsed-high'},
            "GUI": {"yong": 'METAL', "help": None, "ji": 'FIRE', "quote": '十月癸水，旺中有弱，何也，因亥摇木，泄散元神，宜用庚辛为妙，得庚辛两透，不见丁伤者，功名有准。或支成木局，有丁出乾，为木', "ref": 'QTBJ_L3274', "note": 'parsed-med'},
        },
        "ZI": {
            "JIA": {"yong": 'FIRE', "help": 'EARTH', "ji": 'WATER', "quote": '十一月甲木，木性生寒，丁先庚后，丙火佐之。癸水司权，为火金之病。庚丁两透，支见巳寅，科甲有准，风水不及，选拔有之。若癸透', "ref": 'QTBJ_L3826', "note": 'fallback'},
            "YI": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '十一月乙木，花木寒冻，一阳来复，喜用丙火解冻，则花木有向阳之意，不宜用癸以冻花木，故端用丙火。有一二点丙火出乾，无癸制者', "ref": 'QTBJ_L754', "note": 'parsed-high'},
            "BING": {"yong": 'WATER', "help": 'METAL', "ji": 'EARTH', "quote": '十一月丙火，冬至一阳生，弱中复强，壬水为最，戊土佐之。', "ref": 'QTBJ_L4486', "note": 'fallback'},
            "DING": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '三冬丁火，火弱无烟，专用甲乙生助。 (三季总论)', "ref": 'QTBJ_L9082', "note": 'parsed-high'},
            "WU": {"yong": 'FIRE', "help": 'WOOD', "ji": 'WATER', "quote": '三冬戊土，寒土冻泥，用火温暖。', "ref": 'QTBJ_L9102', "note": 'fallback'},
            "JI": {"yong": 'FIRE', "help": 'WOOD', "ji": 'WATER', "quote": '三冬己土，冻土寒冰，用火破寒。 (三季总论)', "ref": 'QTBJ_L9123', "note": 'fallback'},
            "GENG": {"yong": 'FIRE', "help": 'WOOD', "ji": None, "cond": ['DING'], "status": 'supported', "quote": '十一月庚金，天气严寒，仍取丁甲，次取丙火照暖。', "ref": 'QTBJ_L5572', "note": 'rev16'},
            "XIN": {"yong": 'WATER', "help": 'FIRE', "ji": 'EARTH', "cond": [], "status": 'supported', "quote": '十一月辛金，癸水司令，为寒冬雨露，切忌癸出冻金，而困丙火，壬丙两透，不见戊癸，衣锦腰金。', "ref": 'QTBJ_L5926', "note": 'rev16'},
            "REN": {"yong": 'EARTH', "help": None, "ji": 'WOOD', "quote": '十一月壬水，丙戊并用。', "ref": 'QTBJ_L6280', "note": 'parsed-high'},
            "GUI": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '十一月癸水，值冰冻之时，金水无交欢之象，专用丙火解冻，庶不致成冰，又要辛金滋扶，无丙有辛，不妙，凡冬季癸水，有丙透解冻，', "ref": 'QTBJ_L6514', "note": 'parsed-high'},
        },
        "CHOU": {
            "JIA": {"yong": 'METAL', "help": None, "ji": 'FIRE', "quote": '十二月甲木，天寒气冻，木性极寒，无生发之象，先用庚劈甲，方引丁火始得木火有通明之象，故丁次之。庚丁两透，科甲恩封。庚透丁', "ref": 'QTBJ_L448', "note": 'parsed-med'},
            "YI": {"yong": 'FIRE', "help": 'WOOD', "ji": 'METAL', "quote": '十二月乙木，寒木向阳，必须丙火照暖，方有生发之机。丙丁两透，富贵有准。支成木局，癸水透干，亦可许富。又一命：丙寅、丙午、', "ref": 'QTBJ_L9036', "note": 'fallback'},
            "BING": {"yong": 'WATER', "help": 'METAL', "ji": 'EARTH', "quote": '十二月丙火，气进二阳，每雪欺霜，喜壬为用，己土司令，土多又不可少甲，壬甲两透，科甲堪宜，甲藏则秀才而已，或无甲得一壬透，', "ref": 'QTBJ_L4522', "note": 'fallback'},
            "DING": {"yong": 'WOOD', "help": None, "ji": 'METAL', "quote": '三冬丁火，火弱无烟，专用甲乙生助。 (三季总论)', "ref": 'QTBJ_L9082', "note": 'parsed-high'},
            "WU": {"yong": 'FIRE', "help": 'WOOD', "ji": 'WATER', "quote": '三冬戊土，寒土冻泥，用火温暖。 (三季总论)', "ref": 'QTBJ_L9102', "note": 'fallback'},
            "JI": {"yong": 'FIRE', "help": 'WOOD', "ji": 'WATER', "quote": '三冬己土，冻土寒冰，用火破寒。 (三季总论)', "ref": 'QTBJ_L9123', "note": 'fallback'},
            "GENG": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '十二月庚金，寒气太重，且多湿泥，愈寒愈冻，先取丙火解冻，次取丁火炼金，甲亦不可少。', "ref": 'QTBJ_L5596', "note": 'parsed-high'},
            "XIN": {"yong": 'FIRE', "help": 'WOOD', "ji": 'EARTH', "quote": '十二月辛金，丙先壬后，戊己次之。', "ref": 'QTBJ_L5962', "note": 'fallback'},
            "REN": {"yong": 'FIRE', "help": None, "ji": 'WATER', "quote": '十二月壬水，旺极复衰，何也，上半月癸辛主事，故旺，专用丙火，下半月己土主事，故衰，亦用丙火，甲木佐之。有丙解冻，名利双全', "ref": 'QTBJ_L3064', "note": 'parsed-high'},
            "GUI": {"yong": 'FIRE', "help": 'WATER', "ji": None, "cond": ['DING'], "status": 'partially_supported', "quote": '十二月癸水，寒极成冰，万物不能舒泰，宜丙火解冻，或丙透年时，加以壬透。', "ref": 'QTBJ_L6544', "note": 'rev16'},
        },
    }

    # 身强弱 → 喜用规则
    STRENGTH_RULES = {
        "STRONG": {
            "yong": "WATER", "help": "METAL", "ji": "FIRE",
            "basis": "DT-STRENGTH-SHENG",
            "evidence": ["E-DT-STRENGTH-001", "E-QTBJ-YONG-001"],
            "quote": "火旺宜水润之，则万物发生", "source": "滴天髓·原注"},
        "WANG_OVER": {
            "yong": "WATER", "help": "METAL", "ji": "FIRE",
            "basis": "DT-STRENGTH-WANG",
            "evidence": ["E-DT-STRENGTH-011"],
            "quote": "旺极者抑之则折，惟用火土顺其势", "source": "滴天髓·旺极"},
        "WANG_BUT_NOT_STRONG": {
            "yong": "WATER", "help": "METAL", "ji": "FIRE",
            "basis": "DT-STRENGTH-WANG-NO-STRONG",
            "evidence": ["E-DT-STRENGTH-013"],
            "quote": "身旺无倚，虽聪颖而孤贫", "source": "滴天髓"},
        "BALANCED": {
            "yong": "WATER", "help": "METAL", "ji": "FIRE",
            "basis": "DT-STRENGTH-BALANCED",
            "evidence": ["E-DT-STRENGTH-014"],
            "quote": "命贵中和，偏枯终于有损", "source": "滴天髓"},
        "WEAK": {
            "yong": "FIRE", "help": "WOOD", "ji": "WATER",
            "basis": "ZQ-STRENGTH-WEAK",
            "evidence": ["E-ZQ-GEJU-001"],
            "quote": "身弱用印比帮身", "source": "子平真诠·身弱"},
        "WEAK_OVER": {
            "yong": "FIRE", "help": "WOOD", "ji": "METAL",
            "basis": "ZQ-STRENGTH-WEAK-OVER",
            "evidence": ["E-ZQ-GEJU-002"],
            "quote": "弱极从势，不可逆也", "source": "子平真诠·从格"},
    }

    # 气候 → 调候优先级
    CLIMATE_PRIORITY = {
        "HOT": {"priority": "WATER", "reason": "炎夏急需调候润局"},
        "COLD": {"priority": "FIRE", "reason": "寒冬急需调候暖局"},
        "HOT_WET": {"priority": "METAL", "reason": "湿热需金泄秀"},
        "DRY": {"priority": "WATER", "reason": "燥土需水润局"},
    }

    def __init__(self):
        pass

    def verdict(
        self,
        judgments: List[Dict[str, Any]],
        chart_info: Dict[str, Any],
    ) -> YongShenVerdict:
        """根据辨层结果裁定喜用神."""
        verdict = YongShenVerdict()

        # 1. 提取辨层状态 (兼容 dataclass 和 dict)
        states = {}
        for j in judgments:
            if isinstance(j, dict):
                dom = j.get("domain", "")
                st = j.get("state", "")
            else:
                dom = getattr(j, "domain", "")
                st = getattr(j, "state", "")
            if dom and st and st != "UNDETERMINED":
                states[dom] = st

        verdict.body_state = states.get("STRENGTH", "UNKNOWN")
        verdict.climate_state = states.get("CLIMATE", "UNKNOWN")
        verdict.tangguan_state = states.get("TONGGUAN", "UNKNOWN")
        verdict.disease_state = states.get("DISEASE", "UNKNOWN")

        # 2. 格局判定
        pattern = states.get("PATTERN", "UNKNOWN")
        special = states.get("SPECIAL", "UNKNOWN")
        if special in ("YANSHANG", "CONG_WANG", "CONG_WEAK"):
            verdict.pattern_type = special
        elif pattern in ("SUCCESS", "FAIL"):
            verdict.pattern_type = f"PATTERN_{pattern}"
        else:
            verdict.pattern_type = "NORMAL"

        # 3. 炎上格特殊处理
        if verdict.pattern_type == "YANSHANG":
            return self._yan_shang_verdict(verdict, states, chart_info)

        # 4. 调候优先 (穷通宝鉴 + 泛滥闸门)
        tiaohou = self._tiaohou_verdict(states, chart_info)
        if tiaohou:
            verdict.primary_yong = tiaohou["yong"]
            verdict.primary_help = tiaohou["help"]
            verdict.Ji_shen = tiaohou["ji"]
            verdict.basis = tiaohou.get("basis") or "QTPJ-TIAOHOU"
            verdict.classic_quote = tiaohou["quote"]
            verdict.source = tiaohou["source"]
            verdict.evidence_refs = tiaohou.get("evidence", [])
            verdict.flood_note = tiaohou.get("flood_note", "")
            return verdict

        # 5. 身强弱通用规则
        strength_rule = self.STRENGTH_RULES.get(verdict.body_state)
        if strength_rule:
            verdict.primary_yong = strength_rule["yong"]
            verdict.primary_help = strength_rule["help"]
            verdict.Ji_shen = strength_rule["ji"]
            verdict.basis = strength_rule["basis"]
            verdict.classic_quote = strength_rule["quote"]
            verdict.source = strength_rule["source"]
            verdict.evidence_refs = strength_rule["evidence"]
            return verdict

        # 6. fail-closed: 默认
        verdict.basis = "FAIL_CLOSED"
        verdict.classic_quote = "辨层不足, 喜用待察"
        verdict.source = "引擎"
        return verdict

    def _yan_shang_verdict(
        self, verdict: YongShenVerdict, states: Dict[str, str], chart_info: Dict[str, Any]
    ) -> YongShenVerdict:
        """炎上格特殊裁定."""
        verdict.Ji_shen = "WATER"
        verdict.primary_yong = "FIRE"
        verdict.primary_help = "EARTH"
        verdict.basis = "QTPJ-YANSHANG"
        verdict.classic_quote = "炎上格，不喜水破格"
        verdict.source = "穷通宝鉴·炎上格"
        verdict.evidence_refs = ["E-QTBJ-YANSHANG-001"]
        return verdict

    def _tiaohou_verdict(
        self, states: Dict[str, str], chart_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """调候裁定 (穷通宝鉴体例 + 泛滥闸门).

        1. 查 120组逐日干调候表 (月支 x 日干, 表内引文逐字定位带ref出处)
        2. 泛滥闸门: 调候用神在命局计数→状态枚举 = OVERFLOW/EXTREME (查表, 无比较)
           → 调候失效, 转制化 (克泛滥者为用, 生克者为帮, 泛滥方为忌)
        3. 用神无根 → 保留调候裁定 + 标低置信 (不武断对调)
        全程纯查表/枚举, 无百分比、无权重加减.
        """
        month_branch = chart_info.get("month_branch", "")
        body_state = states.get("STRENGTH", "UNKNOWN")
        day_master = chart_info.get("day_master", "").upper()

        # 1. 查调候表 (按日干, 新表直接以 JIA..GUI 为键)
        th = None
        if month_branch in self.TIAOHOU_TABLE and day_master in self.TIAOHOU_TABLE[month_branch]:
            th = dict(self.TIAOHOU_TABLE[month_branch][day_master])

        if th is not None:
            yong_5x = th.get("yong")
            # 2. 泛滥闸门 (计数→状态枚举查表, 无百分比, 无>=比较)
            floods = _flood_elements(
                chart_info.get("four_stems", []),
                chart_info.get("four_branches", []),
            )
            flood_state = _count_state(
                chart_info.get("four_stems", []),
                chart_info.get("four_branches", []),
                yong_5x,
            ) if yong_5x else "ABSENT"
            if yong_5x in floods:
                zhi_yong = KE_BY[yong_5x]        # 克泛滥者 = 用
                zhi_help = SHENG_BY[zhi_yong]    # 生克者 = 帮
                return {
                    "yong": zhi_yong,
                    "help": zhi_help,
                    "ji": yong_5x,
                    "quote": th.get("quote", ""),
                    "source": th.get("ref", "穷通宝鉴"),
                    "evidence": th.get("evidence", []),
                    "flood_note": (
                        f"调候用神{_WUXING_NAMES.get(yong_5x, yong_5x)}在命局太过"
                        f"(8位计数状态={flood_state}), 调候失效, 转制化: "
                        f"用{_WUXING_NAMES.get(zhi_yong, zhi_yong)}"
                        f"帮{_WUXING_NAMES.get(zhi_help, zhi_help)}"
                        f"忌{_WUXING_NAMES.get(yong_5x, yong_5x)}"
                    ),
                    "basis": "QTPJ-FLOOD-GATE",
                    "note": "FLOOD_GATE",
                }
            # 3. 正常调候
            result = {
                "yong": th.get("yong"),
                "help": th.get("help"),
                "ji": th.get("ji"),
                "quote": th.get("quote", ""),
                "source": th.get("ref", "穷通宝鉴"),
                "evidence": th.get("evidence", []),
                "note": th.get("note", ""),
            }
            has_root = chart_info.get("has_root_for_yong", False)
            if not has_root:
                result["note"] = (result["note"] + " | 用神无根, 调候降格(保留裁定, 低置信)").strip()
            return result

        # 4. Fallback: 身强弱规则 (按日主查表, 不硬编码丙火)
        dm_wuxing = STEM_WUXING.get(day_master, "")
        if dm_wuxing:
            return self._strength_verdict(body_state, dm_wuxing)
        return None

    def _strength_verdict(
        self, body_state: str, dm_wuxing: str
    ) -> Optional[Dict[str, Any]]:
        """身强弱裁定 — 按日主五行查表 (确定性).

        弱: 用=生我者(印), 帮=同我(比劫), 忌=克我者
        强/旺: 用=我生者(食伤), 帮=克我者(官杀), 忌=生我者
        中和: 用=我克者(财), 帮=我生者(食伤), 忌=生我者(印)
        """
        DM_SHENGNONG = {"WEAK": 0, "WEAK_OVER": 0, "STRONG": 1,
                        "WANG_OVER": 1, "WANG_BUT_NOT_STRONG": 1, "BALANCED": 2}
        kind = DM_SHENGNONG.get(body_state)
        if kind is None:
            return None
        if kind == 0:  # 身弱 → 生扶
            yong, help_, ji = SHENG_BY[dm_wuxing], dm_wuxing, KE_BY[dm_wuxing]
            basis = "ZQ-STRENGTH-WEAK"
        elif kind == 1:  # 身强 → 克泄
            yong, help_, ji = _SHENG_OUT[dm_wuxing], KE_BY[dm_wuxing], SHENG_BY[dm_wuxing]
            basis = "ZQ-STRENGTH-STRONG"
        else:  # 中和 → 财官
            yong, help_, ji = _KE_OUT[dm_wuxing], _SHENG_OUT[dm_wuxing], SHENG_BY[dm_wuxing]
            basis = "ZQ-STRENGTH-BALANCED"
        return {
            "yong": yong, "help": help_, "ji": ji,
            "basis": basis,
            "quote": "身弱宜生扶, 身旺宜克泄 (子平真诠·扶抑)",
            "source": "子平真诠",
            "evidence": [],
            "note": "STRENGTH_RULE",
        }

    @staticmethod
    def to_dict(verdict: YongShenVerdict) -> Dict[str, Any]:
        """序列化为dict."""
        def _name(v):
            if not v:
                return ""
            return _WUXING_NAMES.get(v, v)
        return {
            "primary_yong": _name(verdict.primary_yong),
            "primary_help": _name(verdict.primary_help),
            "ji_shen": _name(verdict.Ji_shen),
            "basis": verdict.basis,
            "evidence_refs": verdict.evidence_refs,
            "pattern_type": verdict.pattern_type,
            "body_state": verdict.body_state,
            "climate_state": verdict.climate_state,
            "classic_quote": verdict.classic_quote,
            "source": verdict.source,
            "flood_note": verdict.flood_note,
        }


# ═══════════════════════════════════════════════════════════════
# 流年吉凶判定
# ═══════════════════════════════════════════════════════════════
@dataclass
class LiuNianVerdict:
    """流年吉凶判定结果."""
    year: str = ""               # 干支, 如 "丙午"
    year_gan: str = ""           # 天干, 如 "丙"
    year_zhi: str = ""           # 地支, 如 "午"
    gan_ten_god: str = "UNKNOWN" # 天干十神
    zhi_ten_god: str = "UNKNOWN" # 地支十神

    # 吉凶判定
    ji_xiong: str = "UNKNOWN"   # JI / XIONG / JI_XIONG_MIXED / UNCLEAR
    reason: str = ""            # 判定理由

    # 与命局关系
    relations: List[Dict[str, str]] = field(default_factory=list)
    # [{"type": "冲/合/刑/害/伏吟", "target": "时支巳", "effect": "冲根"}]

    # 用神状态
    yong_shen_effect: str = "UNKNOWN"  # HELP / HARM / NEUTRAL / ATTACKED
    yong_shen_detail: str = ""         # 如 "壬水被丙火争合"

    # 原文支撑
    classic_quote: str = ""
    source: str = ""


class LiuNianEngine:
    """流年吉凶判定引擎 — 纯确定性规则."""

    # 天干十神 (按日主动态生成 — 修复硬编码BING日主bug)
    # 保留 BING 表仅作静态回退
    STEM_TEN_GOD = {
        "GENG": "偏财", "XIN": "正财",
        "REN": "七杀", "GUI": "正官",
        "JIA": "偏印", "YI": "正印",
        "BING": "比肩", "DING": "劫财",
        "WU": "食神", "JI": "伤官",
    }
    STEM_WUXING = {
        "JIA": "WOOD", "YI": "WOOD",
        "BING": "FIRE", "DING": "FIRE",
        "WU": "EARTH", "JI": "EARTH",
        "GENG": "METAL", "XIN": "METAL",
        "REN": "WATER", "GUI": "WATER",
    }
    # 天干阴阳 (JIA/BING/WU/GENG/REN=阳, 余阴)
    STEM_YANG = {"JIA", "BING", "WU", "GENG", "REN"}

    def build_stem_ten_god(self, day_master: str) -> Dict[str, str]:
        """按日主生成十天干十神表 (生克制化枚举, 确定性)."""
        dm_wuxing = self.STEM_WUXING.get(day_master)
        if not dm_wuxing:
            return self.STEM_TEN_GOD
        my_yang = day_master in self.STEM_YANG
        tables = {
            "比劫": dm_wuxing,
            "财": _KE_OUT[dm_wuxing],
            "食伤": _SHENG_OUT[dm_wuxing],
            "官杀": KE_BY[dm_wuxing],
            "印": SHENG_BY[dm_wuxing],
        }
        labels = {
            "比劫": {"same": "比肩", "diff": "劫财"},
            "财": {"same": "偏财", "diff": "正财"},
            "食伤": {"same": "食神", "diff": "伤官"},
            "官杀": {"same": "七杀", "diff": "正官"},
            "印": {"same": "偏印", "diff": "正印"},
        }
        ten_god = {}
        for group, wuxing in tables.items():
            for stem, sw in self.STEM_WUXING.items():
                if sw != wuxing:
                    continue
                stem_yang = stem in self.STEM_YANG
                ten_god[stem] = labels[group]["same" if stem_yang == my_yang else "diff"]
        return ten_god
    STEM_HE = {
        "JIA": "JI", "JI": "JIA",
        "BING": "XIN", "XIN": "BING",
        "WU": "GUI", "GUI": "WU",
        "DING": "REN", "REN": "DING",
        "GENG": "YI", "YI": "GENG",
    }

    # 地支藏干主气 (拼音格式)
    BRANCH_MAIN_HIDDEN = {
        "ZI": "GUI", "CHOU": "JI", "YIN": "JIA", "MAO": "YI",
        "CHEN": "WU", "SI": "BING", "WU": "DING", "WEI": "JI",
        "SHEN": "GENG", "YOU": "XIN", "XU": "WU", "HAI": "REN",
    }
    BRANCH_WUXING = {
        "ZI": "WATER", "CHOU": "EARTH", "YIN": "WOOD", "MAO": "WOOD",
        "CHEN": "EARTH", "SI": "FIRE", "WU": "FIRE", "WEI": "EARTH",
        "SHEN": "METAL", "YOU": "METAL", "XU": "EARTH", "HAI": "WATER",
    }
    # 六冲
    BRANCH_CHONG = {
        "ZI": "WU", "WU": "ZI", "CHOU": "WEI", "WEI": "CHOU",
        "YIN": "SHEN", "SHEN": "YIN", "MAO": "YOU", "YOU": "MAO",
        "CHEN": "XU", "XU": "CHEN", "SI": "HAI", "HAI": "SI",
    }
    # 六合 (寅亥合火 — 修正原"HEI"幽灵支, 应为HAI)
    BRANCH_HE = {
        "ZI": "CHOU", "CHOU": "ZI", "YIN": "HAI", "HAI": "YIN",
        "MAO": "XU", "XU": "MAO", "CHEN": "YOU", "YOU": "CHEN",
        "SI": "SHEN", "SHEN": "SI", "WU": "WEI", "WEI": "WU",
    }
    # 三刑
    BRANCH_CHEN = {
        "ZI": "MAO", "MAO": "ZI", "CHEN": "CHEN",
        "YIN": "SI", "SI": "SHEN", "SHEN": "YIN",
        "CHOU": "WEI", "WEI": "CHOU",
    }

    def __init__(self):
        pass

    def verdict(
        self,
        liunian_gz: str,      # 流年干支拼音, 如 "BING wu" (空格分隔)
        chart_info: Dict[str, Any],
        yongshen: YongShenVerdict,
    ) -> LiuNianVerdict:
        """判定流年吉凶."""
        parts = liunian_gz.strip().split()
        if len(parts) == 2:
            gan, zhi = parts[0].upper(), parts[1].upper()
        else:
            # 兼容连写格式
            s = liunian_gz.upper()
            gan, zhi = s[:2], s[2:]
        lv = LiuNianVerdict(year=liunian_gz, year_gan=gan, year_zhi=zhi)

        # 提取命局信息
        four_stems = chart_info.get("four_stems", [])
        four_branches = chart_info.get("four_branches", [])
        day_master = chart_info.get("day_master", "").upper()

        # 十神表按日主动态生成 (修复硬编码BING日主bug)
        ten_god_table = self.build_stem_ten_god(day_master) if day_master else self.STEM_TEN_GOD
        lv.gan_ten_god = ten_god_table.get(lv.year_gan, "UNKNOWN")
        lv.zhi_ten_god = ten_god_table.get(
            self.BRANCH_MAIN_HIDDEN.get(lv.year_zhi, ""), "UNKNOWN"
        )

        # 1. 检查冲合关系
        relations = self._check_relations(lv, four_branches, four_stems)
        lv.relations = relations

        # 2. 判定用神状态
        yong_effect = self._judge_yong_shen_effect(
            lv, yongshen, relations, chart_info
        )
        lv.yong_shen_effect = yong_effect["effect"]
        lv.yong_shen_detail = yong_effect["detail"]

        # 3. 综合吉凶
        lv.ji_xiong, lv.reason = self._synthesize_ji_xiong(lv, yong_effect)

        # 4. 原文支撑
        lv.classic_quote, lv.source = self._find_classic_support(lv, yongshen)

        return lv

    def _check_relations(
        self, lv: LiuNianVerdict, four_branches: List[str], four_stems: List[str]
    ) -> List[Dict[str, str]]:
        """检查流年与命局的干支关系."""
        relations = []

        # 地支关系
        for i, bz in enumerate(four_branches):
            if bz == lv.year_zhi:
                relations.append({
                    "type": "伏吟",
                    "target": f"第{i+1}柱地支{bz}",
                    "effect": "伏吟加重",
                })
            elif self.BRANCH_CHONG.get(bz) == lv.year_zhi:
                relations.append({
                    "type": "冲",
                    "target": f"第{i+1}柱地支{bz}",
                    "effect": f"流年{lv.year_zhi}冲命局{bz}",
                })
            elif self.BRANCH_HE.get(bz) == lv.year_zhi:
                relations.append({
                    "type": "合",
                    "target": f"第{i+1}柱地支{bz}",
                    "effect": f"流年{lv.year_zhi}合命局{bz}",
                })
            elif self.BRANCH_CHEN.get(bz) == lv.year_zhi:
                relations.append({
                    "type": "刑",
                    "target": f"第{i+1}柱地支{bz}",
                    "effect": f"流年{lv.year_zhi}刑命局{bz}",
                })

        # 天干关系
        for i, bs in enumerate(four_stems):
            if bs == lv.year_gan:
                relations.append({
                    "type": "伏吟",
                    "target": f"第{i+1}柱天干{bs}",
                    "effect": "伏吟加重",
                })
            elif self.STEM_HE.get(bs) == lv.year_gan:
                relations.append({
                    "type": "合",
                    "target": f"第{i+1}柱天干{bs}",
                    "effect": f"流年{lv.year_gan}合命局{bs}",
                })

        return relations

    def _judge_yong_shen_effect(
        self,
        lv: LiuNianVerdict,
        yongshen: YongShenVerdict,
        relations: List[Dict[str, str]],
        chart_info: Dict[str, Any],
    ) -> Dict[str, str]:
        """判定流年对喜用神的影响."""
        effect = "NEUTRAL"
        detail = ""

        yong_5x = yongshen.primary_yong  # WATER/METAL/etc
        ji_5x = yongshen.Ji_shen

        # 流年天干五行
        gan_5x = self._stem_to_wuxing(lv.year_gan)

        if gan_5x == yong_5x:
            effect = "HELP"
            detail = f"流年天干{lv.year_gan}为{yongshen.primary_yong}，助用神"
        elif gan_5x == ji_5x:
            effect = "HARM"
            detail = f"流年天干{lv.year_gan}为{yongshen.Ji_shen}，助忌神"
        elif gan_5x == yongshen.primary_help:
            effect = "HELP"
            detail = f"流年天干{lv.year_gan}为喜神{yongshen.primary_help}，辅助用神"

        # 检查合化影响
        for rel in relations:
            if rel["type"] == "合":
                # 丁壬合化木 → 如果是合走了用神 → 凶
                if lv.year_gan in ("DING", "REN") and yong_5x == "WATER":
                    effect = "ATTACKED"
                    detail += "; 丁壬合化木，用神被合"
                elif lv.year_gan in ("BING", "XIN") and yong_5x == "METAL":
                    effect = "ATTACKED"
                    detail += "; 丙辛合化水，用神被合"

        # 检查冲的影响 (冲根 → 凶)
        for rel in relations:
            if rel["type"] == "冲":
                if "时支" in rel["target"] or "第4柱" in rel["target"]:
                    effect = "ATTACKED"
                    detail += f"; {rel['effect']}，根基受损"
                elif "月支" in rel["target"] or "第2柱" in rel["target"]:
                    effect = "HARM"
                    detail += f"; {rel['effect']}，提纲受损"

        # 伏吟 → 加重
        for rel in relations:
            if rel["type"] == "伏吟":
                if effect == "HELP":
                    effect = "HELP"  # 喜神伏吟 → 更喜
                elif effect == "HARM":
                    effect = "HARM"  # 忌神伏吟 → 更凶
                detail += f"; {rel['effect']}"

        return {"effect": effect, "detail": detail}

    def _synthesize_ji_xiong(
        self, lv: LiuNianVerdict, yong_effect: Dict[str, str]
    ) -> tuple:
        """综合判定吉凶.

        规则:
        1. 天干五行决定基础吉凶 (HELP/HARM/NEUTRAL)
        2. 地支冲合修饰吉凶程度 (ATTACKED = 严重削弱)
        3. 优先级: 天干 > 地支
        """
        effect = yong_effect["effect"]
        detail = yong_effect["detail"]

        # 基础吉凶 (天干)
        # 枚举契约: JI=吉, XIONG=凶 (dataclass LiuNianVerdict 注释)
        if effect == "HELP":
            ji_xiong = "JI"
            reason = f"吉: {detail}"
        elif effect == "HARM":
            ji_xiong = "XIONG"
            reason = f"凶: {detail}"
        elif effect == "ATTACKED":
            # 地支冲克严重，用神受损
            ji_xiong = "XIONG"
            reason = f"大凶: 用神根基被冲克，{detail}"
        elif effect == "NEUTRAL":
            ji_xiong = "UNCLEAR"
            reason = f"中性: {detail}"
        else:
            ji_xiong = "UNCLEAR"
            reason = detail

        return ji_xiong, reason

    def _find_classic_support(
        self, lv: LiuNianVerdict, yongshen: YongShenVerdict
    ) -> tuple:
        """查找五经原文支撑 (简化版: 基于吉凶类型)."""
        # 枚举契约: JI=吉, XIONG=凶
        if lv.ji_xiong == "JI":
            return "食神生旺胜财官", "滴天髓阐微"
        elif lv.ji_xiong == "XIONG":
            return "一交亥运，壬水得禄，癸水临旺，火气克尽，家破身亡", "滴天髓阐微"
        return "", ""

    @staticmethod
    def _stem_to_wuxing(stem: str) -> str:
        """天干 → 五行."""
        return {
            "JIA": "WOOD", "YI": "WOOD",
            "BING": "FIRE", "DING": "FIRE",
            "WU": "EARTH", "JI": "EARTH",
            "GENG": "METAL", "XIN": "METAL",
            "REN": "WATER", "GUI": "WATER",
        }.get(stem.upper(), "UNKNOWN")

    @staticmethod
    def to_dict(lv: LiuNianVerdict) -> Dict[str, Any]:
        """序列化为dict."""
        return {
            "year": lv.year,
            "gan_ten_god": lv.gan_ten_god,
            "zhi_ten_god": lv.zhi_ten_god,
            "ji_xiong": lv.ji_xiong,
            "reason": lv.reason,
            "relations": lv.relations,
            "yong_shen_effect": lv.yong_shen_effect,
            "yong_shen_detail": lv.yong_shen_detail,
            "classic_quote": lv.classic_quote,
            "source": lv.source,
        }
