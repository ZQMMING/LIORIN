"""H8: 河洛解卦层（原典查询式字典引擎）

职责：把已排好的主链（先天/后天/大运/流年/流月/流日）转成原典判词。
数据源：heluo_engine/data/guajie_data.json（《河洛真数·易卦释义》，续修四库全书·天一阁本）
+ 起例卷"数足不足论"（中华典藏 21177 天一阁本）。

解卦四要素（原典《河洛真数》起例）：
  1. 得时     = 生月与卦之旺时相符（卦气属X月 / 旺时区间）
  2. 纳甲本命 = 生年干支在卦之纳甲范围
  3. 叶/不叶  = 命局与卦爻时机相合（叶吉）或不合（不叶）
  4. 岁运逢爻 = 走大运/流年到此爻，按在仕/在士/在庶俗/女命分断

数之凶吉（起例卷之中·数足不足论）：
  天数二十五为正、地数三十为正；无余无不足=最佳（安和自宁）
  天数不足<25 / 地数不足<30；有余档（孤阳不偶/孤阴背阳/以弱敌强）
  有余/不足均须按生月节气合时判断凶吉（阳月/阴月）

元气化工（命之根基，yuan_qi.py/hua_gong.py）：
  流年遇元气 → 必然得财利；遇化工 → 中举中进士生贵子
  爻辞虽凶不免灾眚，但于富贵天年不碍。不要拘泥爻辞吉凶。

正对反对卦（生死大凶断）：
  流年先后天大象遇正对/反对 + 爻辞凶 + 卦无元气化工 → 必死，不死亦有横灾
  命卦正对/反对是十二卦（复临泰大壮夬乾姤遁否观剥坤）之一 → 不吉
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .yuan_qi import STEM_TO_TRIGRAM, BRANCH_TO_TRIGRAM
from .timeline_yun import materialize_month_days
from .jiehhou import solar_term_date  # 批次 L：带缓存的节气查表
from .yao_xiang import scan_and_evidence as _scan_yao_xiang
# 错卦（先天方位对宫）单一来源；批次 G 起本模块不再自存一份。
from .hexagram_state import QIANXI_DUKONG
# 60 甲子纳音单一来源（2026-10-22 收敛；原 canping/guajie 各存一份同名副本）
from .nayin import NAYIN_TABLE, get_nayin_element as _nayin_get_nayin_element
from .calendar_guard import check_calendar_consistency

# ── 数据定位（**零路径绑定**，2026-10-24 结构性重构）─────────────────
# ⚠ 旧实现 `_REPO_ROOT = Path(__file__).resolve().parents[4]` 靠**目录层级深度**
#   反推仓库根，再拼 "data/heluo/xxx.json"：
#     · 换任何一层目录即失效（打包/安装/改层级全断）；
#     · 与主仓仓库结构**硬耦合** —— 河洛包无法独立部署到服务器；
#     · 且与主仓 `tongshu` 命名空间冲突（见 heluo_engine/docs/河洛回灌接线决策单_20261024.md）。
#   现改为：数据**随包分发**，按包定位（见 heluo_engine._paths）——
#   与安装位置、运行目录、CWD 全无关。
from ..._paths import pkg_data as _pkg_data

_GUAJIE_DATA = _pkg_data("guajie_data.json")
_JINGYI_DATA = _pkg_data("guajie_jingyi.json")  # 精义/释义 706 单元（64卦辞+258卦象断语+384爻辞）

# 十二凶卦（命卦正对/反对为其中之一 → 不吉）
TWELVE_XIONG_GUA = ["复", "临", "泰", "大壮", "夬", "乾", "姤", "遁", "否", "观", "剥", "坤"]

# 错卦（先天方位对宫，六爻全变）—— 见顶部 import 的 QIANXI_DUKONG。
# ⚠ 2026-10-08 批次 G：错卦此前在 guajie / yuan_qi / hexagram / hua_gong
#   四处各存一份（内容相同），名字统一叫 OPPOSITE_TRIGRAM。
#   更糟的是另有一个**不同义**的表也叫 OPPOSITE_TRIGRAM——化工相反
#   （四季对宫，仅坎离震兑四项），对乾/坤/艮/巽 取 .get() 直接返回 None。
#   import 错了就是静默判错。故错卦统一名 QIANXI_DUKONG（单一来源），
#   化工相反另名 HUAGONG_FAN_GUA；改后无任何公开符号叫 OPPOSITE_TRIGRAM。


# 纯卦 → 上/下三画
PURE_GUA = {"乾": ("乾", "乾"), "坤": ("坤", "坤"), "坎": ("坎", "坎"), "离": ("离", "离"),
            "震": ("震", "震"), "艮": ("艮", "艮"), "巽": ("巽", "巽"), "兑": ("兑", "兑")}

# 64卦 → (上卦, 下卦) 三画分解（由 64 卦名表推导，仅列非纯卦）
COMPOUND_GUA: dict[str, tuple[str, str]] = {
    "屯": ("坎", "震"), "蒙": ("艮", "坎"), "需": ("坎", "乾"), "讼": ("乾", "坎"),
    "师": ("坤", "坎"), "比": ("坎", "坤"), "小畜": ("巽", "乾"), "履": ("乾", "兑"),
    "泰": ("坤", "乾"), "否": ("乾", "坤"), "同人": ("乾", "离"), "大有": ("离", "乾"),
    "谦": ("坤", "艮"), "豫": ("震", "坤"), "随": ("兑", "震"), "蛊": ("艮", "巽"),
    "临": ("坤", "兑"), "观": ("巽", "坤"), "噬嗑": ("离", "震"), "贲": ("艮", "离"),
    "剥": ("艮", "坤"), "复": ("坤", "震"), "无妄": ("乾", "震"), "大畜": ("艮", "乾"),
    "颐": ("艮", "震"), "大过": ("兑", "巽"), "咸": ("兑", "艮"), "恒": ("震", "巽"),
    "遁": ("乾", "艮"), "大壮": ("震", "乾"), "晋": ("离", "坤"), "明夷": ("坤", "离"),
    "家人": ("巽", "离"), "睽": ("离", "兑"), "蹇": ("坎", "艮"), "解": ("震", "坎"),
    "损": ("艮", "兑"), "益": ("巽", "震"), "夬": ("兑", "乾"), "姤": ("乾", "巽"),
    "萃": ("兑", "坤"), "升": ("坤", "巽"), "困": ("兑", "坎"), "井": ("坎", "巽"),
    "革": ("兑", "离"), "鼎": ("离", "巽"), "渐": ("巽", "艮"), "归妹": ("震", "兑"),
    "丰": ("震", "离"), "旅": ("离", "艮"), "涣": ("巽", "坎"), "节": ("坎", "兑"),
    "中孚": ("巽", "兑"), "小过": ("震", "艮"), "既济": ("坎", "离"), "未济": ("离", "坎"),
}
COMPOUND_GUA.update(PURE_GUA)

# 三画卦 → 正五行（纳音相生用）
TRIGRAM_ELEMENT: dict[str, str] = {
    "乾": "金", "兑": "金", "坤": "土", "艮": "土",
    "震": "木", "巽": "木", "坎": "水", "离": "火",
}

# 五行相生关系（key 生 value）
ELEMENT_GENERATES: dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

# 60甲子纳音五行（两柱一组，30组）
# ⚠ 2026-10-22 收敛：原为 canping 与 guajie 各存一份的同名副本，现共用
#   nayin.py 这一份单一来源（两表原内容逐条完全一致）。
#   `_NAYIN` 作为**别名**保留（保名不保表）：外部/测试有直接引用
#   （tests/heluo/test_yuanqi_tables_fidelity.py），故不得删名。
_NAYIN = NAYIN_TABLE


def get_nayin_element(year_gan: str, year_zhi: str) -> str:
    """年柱纳音五行（甲子乙丑海中金…）。

    ⚠ 签名保持 **两柱分列**（year_gan, year_zhi）不变——外部有调用方
    （hua_gong.py 延迟导入本模块的 get_nayin_element、既有测试）。
    实际查表走 nayin.get_nayin_element（干支二字合一），此处仅转发。
    """
    return _nayin_get_nayin_element(year_gan + year_zhi)


def compute_huti(six_lines: list[int]) -> tuple[str, str]:
    """
    互体（《河洛真数·起例卷之上·互体伏体论》）：
      "以正体内外卦除初上二爻，用中四爻，交互成卦，谓之互体"
    取法：下互=二三四爻（lines[1:4]），上互=三四五爻（lines[2:5]）。
    原典例（渐卦）："九五六四九三互离，六四九三六二互坎，合之为未济" ✓
    返回 (上互卦名, 下互卦名)。
    """
    rev = {"111": "乾", "110": "兑", "101": "离", "100": "震",
           "011": "巽", "010": "坎", "001": "艮", "000": "坤"}
    def _tri(chunk: list[int]) -> str:
        return rev.get("".join("1" if l == 1 else "0" for l in chunk), "")
    lower = _tri(six_lines[1:4])
    upper = _tri(six_lines[2:5])
    return upper, lower


def judge_nayin_yuanqi(
    year_gan: str, year_zhi: str, gua_name: str,
) -> list[str]:
    """
    纳音五行元气（《河洛真数·起例卷之上》）：
      "元气谓壬甲戌亥及金音人得乾兑之卦是也"
      "又看彼此相生。如火人得木卦，金人得土卦之类，亦能相生为福。
       但得水火卦者，极忌相反"
    返回证据列表（空=无纳音元气）。
    """
    ev: list[str] = []
    nayin = get_nayin_element(year_gan, year_zhi)
    if not nayin:
        return ev
    gua = COMPOUND_GUA.get(gua_name)
    if not gua:
        return ev
    upper, lower = gua
    el_upper, el_lower = TRIGRAM_ELEMENT.get(upper, ""), TRIGRAM_ELEMENT.get(lower, "")
    ev.append(f"年柱{year_gan}{year_zhi}纳音{nayin}；{gua_name}卦体={upper}({el_upper})/{lower}({el_lower})")

    # 金音人得乾兑（原文明文）
    if nayin == "金" and el_upper in ("金",) or nayin == "金" and el_lower in ("金",):
        ev.append("金音人得乾兑（金体）之卦 → 元气（原典：元气谓…金音人得乾兑之卦是也）")
    # 卦体五行生纳音（生我者=相生为福）
    for el in (el_upper, el_lower):
        if el and ELEMENT_GENERATES.get(el) == nayin:
            ev.append(f"{el}体({el})生纳音{nayin} → 相生为福（原典：彼此相生）")
    # 水火相克相反（极忌）
    for el in (el_upper, el_lower):
        if el == "水" and nayin == "火":
            ev.append(f"得水卦而纳音火 → 极忌相反（原典：得水火卦者极忌相反）")
        if el == "火" and nayin == "水":
            ev.append(f"得火卦而纳音水 → 极忌相反（原典：得水火卦者极忌相反）")
    return ev


# 三画卦 → 六爻序列（1阳 0阴，下卦在前）
_TRIGRAM_LINES = {
    "乾": [1, 1, 1], "兑": [1, 1, 0], "离": [1, 0, 1], "震": [1, 0, 0],
    "巽": [0, 1, 1], "坎": [0, 1, 0], "艮": [0, 0, 1], "坤": [0, 0, 0],
}

# 四正节卦：起于二分二至，每卦90日、每爻15日（起例卷之下·节候卦爻 L1492）
# 原典：「节卦坎初六起冬至，九二小寒，六三大寒，六四立春，九五雨水，上六惊蛰。
#        震初九起春分，六二清明，六三谷雨，九四立夏，六五小满，上六芒种。
#        离初九起夏至，六二小暑，**九二大暑**，九四立秋，六五处暑，上九白露。
#        兑初九起秋分，九二寒露，**九三霜降**，九四立冬，九五小雪，上六大雪。」
#
# 2026-10-07 更正两处错字：
#   离卦第三爻「九三」→「**九二**」（原典作「九二大暑」）
#   兑卦第三爻「六三」→「**九三**」（原典作「九三霜降」）
# 更进一步：爻名序列改由 jiegua.JIE_GUA_TABLE 单一来源提供，
# 本表只保留**二分二至的公历起点日**（原典未给具体日期，属近似），
# 避免节卦爻名在两处各抄一份、日后再次分叉。
_JIE_GUA_START: tuple[tuple[int, int, str], ...] = (
    (12, 22, "坎"),   # 冬至附近
    (3, 21, "震"),    # 春分附近
    (6, 21, "离"),    # 夏至附近
    (9, 23, "兑"),    # 秋分附近
)


def trigram_to_lines(trigram: str) -> list[int]:
    """三画卦 → 六爻序列（下卦3爻+上卦3爻，1阳0阴）。"""
    return list(_TRIGRAM_LINES.get(trigram, [0, 0, 0]))


def hexagram_to_lines(gua_name: str) -> list[int]:
    """卦名 → 六爻序列（下卦3爻+上卦3爻）。"""
    u, l = COMPOUND_GUA.get(gua_name, ("", ""))
    return trigram_to_lines(l) + trigram_to_lines(u)


def judge_jiehua_gong(birth_date: str) -> list[str]:
    """
    生时值节卦 → 化工（《河洛真数·起例卷之下·节候卦爻》）：
      "节卦坎初六起冬至，九二小寒…震初九起春分…离初九起夏至…兑初九起秋分。
       每卦总管九十日，自下而上，每一爻各直十五日。……生时值节卦者，谓之化工，
       生月值卦者，谓之得令"
    四正节卦：坎起冬至/震起春分/离起夏至/兑起秋分（公历近似，边界±1日）。
    返回证据列表（空=无节候卦化工记录）。
    """
    ev: list[str] = []
    try:
        y, m, d = birth_date.split("-")[0:3]
        y, m, d = int(y), int(m), int(d)
    except (ValueError, AttributeError):
        return ev
    import datetime as _dt
    cur = _dt.date(y, m, d)
    # 节卦爻名取自 jiegua.JIE_GUA_TABLE（单一来源，已由原典逐条校验）
    from .jiegua import JIE_GUA_TABLE, get_jie_gua
    for sm, sd, gua in _JIE_GUA_START:
        for yy in (y - 1, y):
            start = _dt.date(yy, sm, sd)
            days = (cur - start).days
            if 0 <= days < 90:
                # 爻位按原典「每一爻各直十五日」推进。
                # ⚠️ 原典明文：「气候有盈虚，**卦爻有超接**」——故此均分是
                #    近似，原典自身即声明「分至之爻既定，其余可推而知矣」。
                #    精确超接需逐年实测超接量，本仓未实现，不臆造。
                idx = min(days // 15, 5)
                # JIE_GUA_TABLE 依四正卦分组（坎/震/离/兑各六爻，起冬至/春分/夏至/秋分）
                trigram_entries = [e for e in JIE_GUA_TABLE if e.trigram == gua]
                yao_name = trigram_entries[idx].yao_name if idx < len(trigram_entries) else "?"
                jq_name = trigram_entries[idx].jq_name if idx < len(trigram_entries) else "?"
                ev.append(
                    f"生时值节卦：{gua}节卦起于{sm}月{sd}日，出生日距起{days}日"
                    f"（第{idx + 1}段，{jq_name}·{yao_name}爻）"
                    f"→ 化工（原典：生时值节卦者谓之化工）")
                return ev
    return ev


def judge_nayin_huti(
    year_gan: str, year_zhi: str,
    prenatal_name: str, postnatal_name: str,
) -> list[str]:
    """
    互体纳音元气（《河洛真数·起例卷之上》）：
      "甲子生人得小过，虽卦中无乾兑金元气，然互体有兑，亦是纳音元气"
    取先天/后天命卦之互体，纳入纳音元气判定。
    """
    ev: list[str] = []
    seen: set[str] = set()
    for g in (prenatal_name, postnatal_name):
        lines = hexagram_to_lines(g)
        if len(lines) != 6:
            continue
        up, lo = compute_huti(lines)
        for cand, (cu, cl) in COMPOUND_GUA.items():
            if cu == up and cl == lo:
                huti_name = cand
                break
        else:
            huti_name = up + lo
        key = f"{g}->{huti_name}"
        if key in seen:
            continue
        seen.add(key)
        nayin = get_nayin_element(year_gan, year_zhi)
        el_up, el_lo = TRIGRAM_ELEMENT.get(up, ""), TRIGRAM_ELEMENT.get(lo, "")
        if nayin == "金" and (el_up == "金" or el_lo == "金"):
            ev.append(f"{g}互体（{up}{lo}={huti_name}）含金体 → 金音人互体得金，亦是纳音元气（原典：互体有兑亦是纳音元气）")
        matched = False
        for el in (el_up, el_lo):
            if el and ELEMENT_GENERATES.get(el) == nayin and not matched:
                ev.append(f"{g}互体（{up}{lo}={huti_name}）{el}体生纳音{nayin} → 互体相生为福（原典：彼此相生）")
                matched = True
    return ev


# 综卦（反对）：**六爻倒转**。
#
# 2026-10-22：原为 64 条手抄表。实测该表与「严格六爻倒转」在 6 条上不符
# （震/艮/巽/兑 被当成自反、颐/大过 被当成一对），其自反卦为 10 个；
# 而《河洛真数·起例卷之下》L47「上经正卦六，反卦二十四……下经正卦二，
# 反卦三十二」要求自反卦合计 **8 个**，且上经 6 / 下经 2 逐位吻合
# **严格六爻倒转**（乾坤坎离颐大过 / 中孚小过）。
# 另两种口径（上下卦对调、该手抄表）分别得 4/4 与 4/6，均不符原典计数。
# 现改为由权威实现 hexagram.compute_zong_gua 派生，杜绝第二份副本漂移。
def _build_zong_gua() -> dict[str, str]:
    from .hexagram import compute_zong_gua
    from .numbers import SIXTY_FOUR_HEXAGRAMS, short_hexagram_name

    out: dict[str, str] = {}
    for (up, lo), full in SIXTY_FOUR_HEXAGRAMS.items():
        out[short_hexagram_name(full)] = short_hexagram_name(
            compute_zong_gua(up, lo))
    return out


ZONG_GUA: dict[str, str] = _build_zong_gua()

# 月名数字映射（卦气属X月）
_CN_MONTH = {"正": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12, "腊": 12}


# ═══════════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════════

@dataclass
class YaoDuan:
    """单爻判词（原典释义）。"""
    yao: str            # 初九/六二/…
    ci: str             # 爻辞
    xiang: str          # 象曰
    yi: str             # 释义
    ye: str             # 叶吉断语
    buye: str           # 不叶断语
    suiyun: str         # 岁运逢之断语
    shao: str           # 邵曰
    jingyi: str = ""    # 爻辞精义（现代语义，guajie_jingyi.json）
    shiyi: str = ""     # 爻辞释义（现代语义，guajie_jingyi.json）


@dataclass
class GuaDuan:
    """单卦判词（原典释义）。"""
    name: str
    gua_ci: str         # 卦辞
    gua_qi_month: Optional[int]  # 卦气属X月
    najia: list[str]    # 纳甲干支（本卦）
    gua_lines: list[str]  # 卦头断语（含旺时/得时信息）
    #: 原典「借用…」段的干支（借别卦之甲）。**不并入 najia**（原典语义：
    #: 借用是另一卦的甲），但须单独留存，否则解析时会被整段丢弃。
    jieyong: list[str] = field(default_factory=list)
    # ── 精义/释义（guajie_jingyi.json 现代语义，2026-09-15 接入） ──
    gua_ci_jingyi: str = ""            # 卦辞精义
    gua_ci_shiyi: str = ""             # 卦辞释义
    lines_jingyi: list[str] = field(default_factory=list)  # 卦象断语精义（与 gua_lines 对齐）
    lines_shiyi: list[str] = field(default_factory=list)   # 卦象断语释义（与 gua_lines 对齐）
    yaos: dict[str, YaoDuan] = field(default_factory=dict)


def _collect_liuqin_hits(yao: object) -> list[dict]:
    """一个爻的断语中命中的**六亲/婚育/寿夭**意象（2026-10-24 新增）。

    委托 :mod:`liuqin_tagger`；此处只做**惰性导入**（避免判词层加载期多一个依赖）
    与**异常隔离**（标注失败不得影响主链 —— 缺失被当成正常，比答错更坏，
    但这里是「锦上添花」的附加维度，失败就不产出，不留半截数据）。
    """
    try:
        from .liuqin_tagger import collect_from_yao
        return collect_from_yao(yao)
    except Exception:
        return []


@dataclass
class YeBuYeResult:
    """叶/不叶判定结果。"""
    ye: bool                    # 叶（相合）
    buye: bool                  # 不叶（不合）
    gua_qi_month: Optional[int]
    birth_month: int
    najia_hit: bool             # 年干支是否在纳甲
    evidence: list[str] = field(default_factory=list)


class TaggedEvidence(list):
    """**带维度标签**的证据列表（2026-10-24）。

    为什么要它
    ----------
    判词层的 ``evidence`` 此前是**平铺**的字符串列表：下游只能靠**解析中文**
    才能知道某条判词属于哪个人生领域（12 域 / 41 子维度，见
    ``docs/heluo/统一维度表_河洛细粒度落位_20261024.md``）——
    这是「维度视图」迟迟落不了地的根因。

    而 ``evidence`` 被**大量**消费方当作 ``list[str]`` 使用
    （诊断规则图、冻结态、数十个守卫）⇒ **不能改条目类型**。

    ⇒ 本类在**保持 list[str] 语义**的前提下，额外记录逐条维度：

        ev.append("流年卦豫 九四爻：…")                  # 默认 UNCLASSIFIED
        ev.append("流年卦豫 九四爻：…", dim="TIMELINE.02")  # 显式标注
        ev.extend(gen, dim="HEALTH.02")                 # 整段标注

    ⚠ 未标注的条目**不静默**：``coverage()`` 会把条数报出，
      守卫亦据此断言「不得有判据证据漏标」（见 tests/heluo/
      test_heluo_dimensions.py）。
    """

    def __init__(self, iterable=(), dims=None) -> None:
        super().__init__(iterable)
        #: 逐条维度 id（与列表**一一对应**）
        self.dims: list[str] = list(dims) if dims is not None else []

    def append(self, item, dim: str = "UNCLASSIFIED") -> None:
        super().append(item)
        self.dims.append(dim)

    def extend(self, items, dim: str = "UNCLASSIFIED") -> None:
        for it in items:
            self.append(it, dim)

    def insert(self, index: int, item, dim: str = "UNCLASSIFIED") -> None:
        super().insert(index, item)
        self.dims.insert(index, dim)

    def copy(self) -> "TaggedEvidence":
        return TaggedEvidence(list(self), list(self.dims))

    def to_plain(self) -> list[str]:
        """退化为普通 ``list[str]``（给只认 list 的消费方）。"""
        return list(self)


@dataclass
class ShuXiongResult:
    """数之凶吉判定结果（起例卷·数足不足论）。"""
    tian_shu: int
    di_shu: int
    tian_state: str             # 有余/足/不足
    di_state: str
    shu_xiong: bool             # 数凶
    pattern: str                # 孤阳不偶/孤阴背阳/以弱敌强/安和自宁…
    evidence: list[str] = field(default_factory=list)
    matched: tuple[str, ...] = ()        # 全部命中的数格名（原典出场次序）
    conflicts: tuple[str, ...] = ()      # 命中数格之间的原典冲突，须显式披露
    lu_shu: tuple = ()                   # 阴阳禄数命中（L105）
    xingbei: tuple = ()                  # 性别向背（L34/L56/L61/L80）
    ming_wu_yin_yang: tuple = ()         # 命无阴阳（L95）：(说明, 凶否）
    chun_qi_qi_ou: tuple = ()            # 三阳奇偶合象（L99/L714）：(说明, 合否)


@dataclass
class GuaJieResult:
    """解卦层综合输出。"""
    liunian_hexagram: str = ""             # 流年卦名（2026-09-13 入库）
    liunian_year: Optional[int] = None      # 流年公历年份
    liunian_yao: Optional[YaoDuan] = None   # 流年动爻判词
    liunian_ye_buye: Optional[YeBuYeResult] = None
    liuyue_hexagram: str = ""             # 流月卦名
    liuyue_yao: Optional[YaoDuan] = None    # 流月动爻判词（应期定位）
    liuri_hexagram: str = ""              # 流日卦名
    liuri_lunar: Optional[dict] = None       # H9b 流日黄历标注（solar_date/lunar/day_ganzhi/day_nayin/jie_qi/yi/ji/source）
    liuri_yao: Optional[YaoDuan] = None     # 流日动爻判词（应期定位）
    liushi_hexagram: str = ""             # 流时卦名（2026-10-06 起该层已剥离，恒为 ""）
    liushi_yao: Optional[YaoDuan] = None    # 流时动爻判词（同上，恒为 None）
    shu_xiong: Optional[ShuXiongResult] = None
    yuan_qi_hit: bool = False               # 流年遇元气
    hua_gong_hit: bool = False              # 流年遇化工
    zhengdui_fandui: list[str] = field(default_factory=list)  # 正对反对警示
    twelve_xiong: bool = False              # 命卦属十二凶卦
    si_duan: list[str] = field(default_factory=list)  # 死断诸法（起例卷之下·后天详说）
    nayin_yuanqi: list[str] = field(default_factory=list)  # 纳音五行元气（起例卷之上）
    jiehua_gong: list[str] = field(default_factory=list)  # 生时值节卦化工（起例卷之下·节候卦爻）
    benming: Optional[dict] = None  # 命卦判词（先天卦辞+卦象断语+精义/释义，2026-09-15 接入）
    kuozhan: dict = field(default_factory=dict)  # 扩展断法（K3-447卷一：四体八体/福力/五命得卦/余数断/四时五行/数极）
    canping: Optional[dict] = None  # 参评诗断（K3-447卷十·金锁银匙歌，2026-10-06 接入）
    summary: list[str] = field(default_factory=list)  # 综合判词（人话）
    #: 判据证据链（**仍是 list[str]**，消费方无感；逐条维度见 :attr:`evidence_dims`）
    evidence: list[str] = field(default_factory=TaggedEvidence)
    #: 爻辞取象命中（原典 L741「近取诸身，远取诸物，如言龙则必贵……」），
    #: 2026-10-08 接入生产链。元素为 yao_xiang.YaoXiangHit。
    yao_xiang_hits: list = field(default_factory=list)

    # ── 维度视图（2026-10-24）────────────────────────────────────────
    @property
    def evidence_dims(self) -> list[str]:
        """逐条证据的维度 id（与 :attr:`evidence` **一一对应**）。

        ⚠ 若 ``evidence`` 被整体替换成普通 list（外部赋值），此处退化为
        全部 ``UNCLASSIFIED`` —— **显式**暴露「维度不可信」，
        而非静默给出错误维度。
        """
        dims = getattr(self.evidence, "dims", None)
        if dims is None or len(dims) != len(self.evidence):
            return ["UNCLASSIFIED"] * len(self.evidence)
        return list(dims)

    def by_dimension(self) -> dict:
        """按**统一维度表**归组证据（12 域 / 41 子维度 + PROCESS/UNCLASSIFIED）。"""
        from .dimensions import build_by_dimension
        return build_by_dimension(list(self.evidence), self.evidence_dims)

    def dimension_coverage(self) -> dict:
        """维度覆盖率（未标注条数**显式报出**，不静默）。"""
        from .dimensions import coverage
        return coverage(list(self.evidence), self.evidence_dims)

    def to_dict(self) -> dict:
        return {
            "liunian_hexagram": self.liunian_hexagram,
            "liunian_year": self.liunian_year,
            "liunian_yao": {
                "yao": self.liunian_yao.yao, "ci": self.liunian_yao.ci,
                # 2026-10-07 审计修：xiang（象曰）与 yi（释义）是 YaoDuan 的
                # 两个非空字段，实测确有内容，此前**四处模板全丢**——生产 API 走
                # dataclasses.asdict 而非本 to_dict，故此丢失只在 to_dict 路径上生效。
                "xiang": self.liunian_yao.xiang, "yi": self.liunian_yao.yi,
                "ye": self.liunian_yao.ye, "buye": self.liunian_yao.buye,
                "suiyun": self.liunian_yao.suiyun, "shao": self.liunian_yao.shao,
                "jingyi": self.liunian_yao.jingyi, "shiyi": self.liunian_yao.shiyi,
            } if self.liunian_yao else None,
            "liunian_ye_buye": {
                "ye": self.liunian_ye_buye.ye, "buye": self.liunian_ye_buye.buye,
                # 2026-10-07 审计修：gua_qi_month（卦气属几月）与 birth_month
                # 是「叶/不叶」这一判定的**两个决定性输入**，此前只存在于
                # dataclass 上，to_dict 未序列化 → 下游拿到结论却看不到依据。
                "gua_qi_month": self.liunian_ye_buye.gua_qi_month,
                "birth_month": self.liunian_ye_buye.birth_month,
                "najia_hit": self.liunian_ye_buye.najia_hit,
                "evidence": self.liunian_ye_buye.evidence,
            } if self.liunian_ye_buye else None,
            # 2026-10-06 修正：下列三个卦名此前**只存在于 dataclass 字段**，
            # to_dict() 漏发，导致 build_guajie_from_result 算出的流月/流日/流时
            # 应期卦名在输出边界被静默丢弃——只发出 _yao，下游拿到"九三"却不知
            # 是何卦之九三。纯增补，不改动任何既有键。
            "liuyue_hexagram": self.liuyue_hexagram,
            "liuyue_yao": {
                "yao": self.liuyue_yao.yao, "ci": self.liuyue_yao.ci,
                "xiang": self.liuyue_yao.xiang, "yi": self.liuyue_yao.yi,   # 2026-10-07 补，见流年模板
                "ye": self.liuyue_yao.ye, "buye": self.liuyue_yao.buye,
                "suiyun": self.liuyue_yao.suiyun, "shao": self.liuyue_yao.shao,
                "jingyi": self.liuyue_yao.jingyi, "shiyi": self.liuyue_yao.shiyi,
            } if self.liuyue_yao else None,
            "liuri_hexagram": self.liuri_hexagram,
            "liuri_lunar": self.liuri_lunar,
            "liuri_yao": {
                "yao": self.liuri_yao.yao, "ci": self.liuri_yao.ci,
                "xiang": self.liuri_yao.xiang, "yi": self.liuri_yao.yi,   # 2026-10-07 补，见流年模板
                "ye": self.liuri_yao.ye, "buye": self.liuri_yao.buye,
                "suiyun": self.liuri_yao.suiyun, "shao": self.liuri_yao.shao,
                "jingyi": self.liuri_yao.jingyi, "shiyi": self.liuri_yao.shiyi,
            } if self.liuri_yao else None,
            "liushi_hexagram": self.liushi_hexagram,
            "liushi_yao": {
                "yao": self.liushi_yao.yao, "ci": self.liushi_yao.ci,
                "xiang": self.liushi_yao.xiang, "yi": self.liushi_yao.yi,   # 2026-10-07 补，见流年模板
                "ye": self.liushi_yao.ye, "buye": self.liushi_yao.buye,
                "suiyun": self.liushi_yao.suiyun, "shao": self.liushi_yao.shao,
                "jingyi": self.liushi_yao.jingyi, "shiyi": self.liushi_yao.shiyi,
            } if self.liushi_yao else None,
            "shu_xiong": {
                "tian_shu": self.shu_xiong.tian_shu, "di_shu": self.shu_xiong.di_shu,
                "tian_state": self.shu_xiong.tian_state, "di_state": self.shu_xiong.di_state,
                "shu_xiong": self.shu_xiong.shu_xiong, "pattern": self.shu_xiong.pattern,
                "evidence": self.shu_xiong.evidence,
                # 2026-10-07 补：以下六项此前只存在于 dataclass 上，
                # to_dict 未序列化，等于新增判定**根本没进输出管道**。
                # （守卫生成时只查 evidence 文本，故未暴露。）
                "matched": list(self.shu_xiong.matched),
                "conflicts": list(self.shu_xiong.conflicts),
                "lu_shu": [vars(h) for h in self.shu_xiong.lu_shu],
                "xingbei": [vars(x) for x in self.shu_xiong.xingbei],
                "ming_wu_yin_yang": list(self.shu_xiong.ming_wu_yin_yang),
                "chun_qi_qi_ou": list(self.shu_xiong.chun_qi_qi_ou),
            } if self.shu_xiong else None,
            "yuan_qi_hit": self.yuan_qi_hit,
            "hua_gong_hit": self.hua_gong_hit,
            "zhengdui_fandui": self.zhengdui_fandui,
            "twelve_xiong": self.twelve_xiong,
            "si_duan": self.si_duan,
            "nayin_yuanqi": self.nayin_yuanqi,
            "jiehua_gong": self.jiehua_gong,
            "benming": self.benming,
            "kuozhan": self.kuozhan,
            "canping": self.canping,
            "summary": self.summary,
            "evidence": self.evidence,
            # ── 维度视图（2026-10-24 新增）──────────────────────────
            # 判据证据此前是**平铺**的，下游只能靠**解析中文**判断某条属于
            # 哪个人生领域 ⇒ 12 域视图落不了地。现按统一维度表逐条打标签，
            # 并给出 by_dimension（按维度归组，items 只带 index 回指 evidence）
            # 与 dimension_coverage（未标注条数**显式报出**）。
            "by_dimension": self.by_dimension(),
            "dimension_coverage": self.dimension_coverage(),
            # 逐条维度 id（与 evidence 一一对应）——
            # 解读层编排（interpretation_pipeline）据此把证据转成
            # V13 EngineEvidence（规则节点 = 维度 id）⇒ 维度标签不能丢。
            "evidence_dims": self.evidence_dims,
            # 2026-10-08 补：爻辞取象命中的结构化输出（原典 L741）。
            # 逐条给 key/verdict/条件/是否参与判定，下游不必回解析 evidence 文本。
            "yao_xiang_hits": [
                {"key": h.key, "verdict": h.verdict,
                 "conditional": h.conditional, "condition": h.condition,
                 "satisfied": h.satisfied, "participated": h.participated}
                for h in self.yao_xiang_hits
            ],
        }


# ═══════════════════════════════════════════════════════════════════
# 数据加载
# ═══════════════════════════════════════════════════════════════════

_LOADED: Optional[dict[str, GuaDuan]] = None

#: 精义库（guajie_jingyi.json）最近一次加载失败的痕迹；正常为 ""。
#: 非空即表示精义/释义层缺失，须由调用方向 evidence 披露。
_JINGYI_LOAD_ERROR = ""


def jingyi_load_error() -> str:
    """精义库加载失败痕迹（空串＝正常）。"""
    return _JINGYI_LOAD_ERROR


def _split_duans(duans: list[str]) -> tuple[str, str, str]:
    """把断语列表分成 叶吉/不叶/岁运 三类（原典措辞变体）。

    ⚠ 2026-10-24 第三轮审计修（**否定式优先**）：
      原实现先判叶关键词（"叶吉","叶者","归元","入局","得时","当此爻","入贵格"）
      再判不叶关键词（"不叶","不归元","不入局",…）。但原典的**不叶**断语
      常写作「数卦**不叶吉**者」——「不叶吉」**包含**「叶吉」子串，
      叶分支先命中 ⇒ 50 条不叶断语被归进**叶吉**类。

      实测（原始 duans 1088 条）：50 条被误归，其中 8 个爻的
      `_yao_buji` 判定因此翻转（False → True，即漏判了凶）。

      修法：把**否定式叶术语**（不叶吉 / 不归元 / 不入局 / 难当此爻 /
      生不及时 / 不及时 / 失正 / 失位）优先判为不叶。
      逐条核对原典上下文确认：每条被改判的断语都紧跟在对应的
      「数卦叶吉者如此。」之后，是**成对的不叶分支**，改判正确。
    """
    ye, buye, suiyun = [], [], []
    for d in duans:
        if any(k in d for k in ("岁运逢", "岁运值")):
            suiyun.append(d)
        elif any(k in d for k in ("不叶吉", "不叶者", "不叶", "不归元",
                                 "不入局", "生不及时", "不及时",
                                 "难当此爻", "失正", "失位")):
            # 否定式优先（见 docstring）
            buye.append(d)
        elif any(k in d for k in ("叶吉", "叶者", "归元", "入局", "得时",
                                 "当此爻", "入贵格")):
            ye.append(d)
        elif any(k in d for k in ("数凶", "寿危", "身亡")):
            suiyun.append(d)
        else:
            ye.append(d)
    return " ".join(ye), " ".join(buye), " ".join(suiyun)


_GAZHI_RE = re.compile(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]")


def _split_gz(text: str) -> list[str]:
    """把干支串切成合法干支列表（讹字如「丙戊」自然被剔除）。"""
    return [p for p in re.split(r"[、，,\s]+", text) if _GAZHI_RE.fullmatch(p)]


def _parse_gua_header(lines: list[str]) -> tuple[Optional[int], list[str], list[str]]:
    """从卦头断语提取 卦气属X月 + 纳甲干支 + 借用干支。

    卦头形如：「乾宫四世卦属八月，纳甲是乙未、乙巳、乙卯、辛巳、辛卯、辛丑，
    借用癸未、癸巳、癸卯，生于八月及纳甲本命者，大贵人也。」

    ⚠ 2026-10-24 修正（此前只取「纳甲是」段、遇「借用」即 break）：
      旧正则 `[^，。；]{2,60}` 在**第一个逗号处**就截断，而原典的「借用」段
      前面正好跟一个逗号 —— 于是「借用」干支从未被读到，整段被静默丢弃。

      现在：纳甲段与借用段**分开返回**。借用段单独存字段备查，
      **不并入本卦 najia**、**不改「年干支在纳甲本命」的命中判定** ——
      原典从未解释「借用」的语义（已检索《河洛真数》全书影印本与网络清本，
      「借用」仅出现于卦头格式，未见释义），**无据不擅改口径**。

      附：3 卦（比 / 小畜 / 夬）的「纳甲是」段只有内卦 3 条，其外卦 3 条
      出现在借用段后 3 位（影印本逐页核实：比=借用段后 3 条即其外卦
      戊申戊戌戊子）。此事实已留档（heluo_engine/docs/纳甲异文多源对拍_20261024.md），
      但**不据此改写 najia**（那属订正原典，须另立据）。
    """
    text = " ".join(lines)
    month = None
    # ⚠ 2026-10-24 第三轮审计修：原正则 `(?:卦气|宫)[^属]{0,6}属(...)月`
    #   **只认「属」**。但原典坤卦卦头写的是「**卦气在十月**」
    #   （《河洛真数·易卦释义·上经卷之上》L91 逐字：
    #     「星辰之气。德合无疆，坤象地道也…**卦气在十月**，纳甲是乙未…」）
    #   —— 坤卦卦头**没有**「XX宫N世卦属X月」那一段，故「宫…属」分支兜不住，
    #   「卦气…属」分支又不认「在」⇒ 坤卦 gua_qi_month 恒为 None。
    #   后果：坤卦十月生被判「不叶（凶象）」，而原典明写「如生于十月纳甲…
    #   叶吉」—— 结论方向反了；evidence 只写「坤卦无卦气月记录」，
    #   读起来像「原典没写」，**无痕**。
    #   修法：卦气分支补「在」。**不改动**已能解析的 55 卦（宫…属分支不变）。
    #
    # ⚠ 2026-10-24 第三轮审计修（同一处的第二个坑）：月名字符集原为
    #   `[正二三四五六七八九十腊]` —— **缺「一」** ⇒「十一月」「十二月」
    #   永远匹配不上（正则吃到「十」就断，剩「一月」接不上）。
    #   后果：小畜/贲/复/节 四卦的「属十一月」被漏掉 ⇒ gua_qi_month=None。
    #   （「十二月」看似能捕到，实为捕到「二」+「月」，侥幸得到 12 ——
    #   但那是靠「二」在字符集里，不是真的匹配了「十二」。）
    #   修法：月名加「一」，并用 `十一|十二` **优先**（长的先试），
    #   避免「十二月」被「十」抢先。
    _MONTH_RE = r"(十一|十二|[正二三四五六七八九十腊])"
    m = re.search(r"卦气(?:属|在)" + _MONTH_RE + r"月", text)
    if m:
        month = _CN_MONTH.get(m.group(1))
    if month is None:
        m = re.search(r"(?:卦气|宫)[^属]{0,6}属" + _MONTH_RE + r"月", text)
        if m:
            month = _CN_MONTH.get(m.group(1))
    if month is None:
        # ⚠ 2026-10-24 第三轮审计修（第三个坑）：**八纯卦**的卦头没有
        #   「XX宫N世卦」也没有「卦气」二字，只有「八纯卦世在六爻属十月」
        #   /「八纯六世卦属四月」这类句式 ⇒ 前两个分支都兜不住，
        #   兑/坎/巽/离 四卦 gua_qi_month 恒为 None。
        #   通用回退：直接找「属X月」。
        #   **安全性已核**：全库 63 处「属X月」**逐一检查过**，
        #   全部是卦气月标记（无一例外），故通用回退不会误取。
        m = re.search(r"属" + _MONTH_RE + r"月", text)
        if m:
            month = _CN_MONTH.get(m.group(1))
    if month is None:
        m = re.search(r"属(\d+)月", text)
        if m:
            month = int(m.group(1))
    najia: list[str] = []
    jieyong: list[str] = []
    # 取到句号为止（跨逗号），再按「借用」切开两段
    m = re.search(r"纳甲(?:是|有)[：:]?\s*([^。]{2,160})", text)
    if m:
        seg = m.group(1)
        head, sep, tail = seg.partition("借用")
        najia = _split_gz(head)
        if sep:
            jieyong = _split_gz(tail)
    return month, najia, jieyong


# 中华典藏网页爬取残留行（混入 guajie_data.lines，load 时过滤，保持卦象断语纯净）
_WEB_NOISE = ("上一章", "返回目录", "下一章", "中华典藏网", "本站非营利性站点", "吸取国学精华")


def _filter_web_noise(lines: list[str]) -> list[str]:
    """过滤 gua_lines 中的网页残留行（如"上一章/返回目录/中华典藏网…"）。"""
    return [l for l in lines if not any(n in l for n in _WEB_NOISE)]


def load_guajie_data() -> dict[str, GuaDuan]:
    """加载 64 卦判词库（懒加载）。"""
    global _LOADED
    if _LOADED is not None:
        return _LOADED
    raw = json.loads(_GUAJIE_DATA.read_text(encoding="utf-8"))
    global _JINGYI_LOAD_ERROR
    try:
        jy_raw = json.loads(_JINGYI_DATA.read_text(encoding="utf-8"))
    except Exception as exc:
        jy_raw = {}  # 精义库缺失/损坏不阻塞判词主链
        # ⚠ 2026-10-07 审计修：旧代码静默置空、不留任何痕迹，精义/释义整层
        # 缺失却无法与「本来就没写」区分。现记录失败原因供调用方披露。
        _JINGYI_LOAD_ERROR = "%s: %s" % (type(exc).__name__, exc)
    out: dict[str, GuaDuan] = {}
    for g in raw:
        month, najia, jieyong = _parse_gua_header(g.get("lines", []))
        jg = jy_raw.get(g["name"], {})
        gd = GuaDuan(
            name=g["name"],
            gua_ci=g.get("gua_ci", ""),
            gua_qi_month=month,
            najia=najia,
            jieyong=jieyong,
            gua_lines=_filter_web_noise(g.get("lines", [])),
            gua_ci_jingyi=(jg.get("gua_ci") or {}).get("jingyi", ""),
            gua_ci_shiyi=(jg.get("gua_ci") or {}).get("shiyi", ""),
            lines_jingyi=[x.get("jingyi", "") for x in jg.get("lines", [])],
            lines_shiyi=[x.get("shiyi", "") for x in jg.get("lines", [])],
        )
        yao_jy = {x.get("yao"): x for x in jg.get("yaos", [])}
        for y in g.get("yaos", []):
            ye, buye, suiyun = _split_duans(y.get("duans", []))
            yj = yao_jy.get(y["yao"], {})
            gd.yaos[y["yao"]] = YaoDuan(
                yao=y["yao"], ci=y.get("ci", ""), xiang=y.get("xiang", ""),
                yi=y.get("yi", ""), ye=ye, buye=buye, suiyun=suiyun, shao=y.get("shao", ""),
                jingyi=yj.get("jingyi", ""), shiyi=yj.get("shiyi", ""),
            )
        out[g["name"]] = gd
    _LOADED = out
    return out


def query_yao_duan(hexagram_name: str, yao_name: str) -> Optional[YaoDuan]:
    """查 64 卦逐爻判词（查询式字典）。"""
    data = load_guajie_data()
    g = data.get(hexagram_name)
    if g is None:
        return None
    return g.yaos.get(yao_name)


# ═══════════════════════════════════════════════════════════════════
# 叶/不叶判定
# ═══════════════════════════════════════════════════════════════════

def judge_ye_buye(
    hexagram_name: str,
    birth_month: int,
    year_ganzhi: str = "",
) -> Optional[YeBuYeResult]:
    """
    判定某卦的叶/不叶（得时 + 纳甲本命）。

    原典（乾卦）：
      "卦气属四月，纳甲是甲子甲寅甲辰壬午壬申壬戌…如生于四月及纳甲本命者，
       多属富贵…乾金秋正旺，如生月不及时又不在纳甲者，主贫贱"
      "生于二月以后八月以前者，得时也"
    """
    data = load_guajie_data()
    g = data.get(hexagram_name)
    if g is None:
        return None
    ev: list[str] = []
    ye = False
    buye = False
    gua_text = " ".join(g.gua_lines)

    # 1. 卦气月匹配
    if g.gua_qi_month is not None:
        if birth_month == g.gua_qi_month:
            ye = True
            ev.append(f"生月{birth_month}月 = 卦气月（{g.name}卦气属{g.gua_qi_month}月）→ 得时")
        else:
            ev.append(f"生月{birth_month}月 ≠ 卦气月{g.gua_qi_month}月")
    else:
        ev.append(f"{g.name}卦无卦气月记录")

    # 2. 纳甲本命（生年干支是否在纳甲）
    najia_hit = False
    if g.najia and year_ganzhi:
        najia_hit = year_ganzhi in g.najia
        ev.append(f"年干支{year_ganzhi} {'在' if najia_hit else '不在'}纳甲[{','.join(g.najia)}]")
    elif g.najia:
        ev.append(f"未提供年干支，纳甲[{','.join(g.najia)}]不参与判定")
    # 借用段（2026-10-24 新增披露）：原典「借用…」干支**不参与**本判定
    # （原典未释其义，无据不擅改口径），但须显形，避免信息被静默吞掉。
    if g.jieyong:
        ev.append(f"原典借用[{','.join(g.jieyong)}]（借别卦之甲，不计入纳甲本命判定）")

    # 3. 旺时区间（得时/及时）—— 原典每卦措辞不同，逐条对照抽取。
    # ⚠ 2026-10-24 第三轮审计修：此前此处只有一条正则
    #   `生于A月以后B月以前[^\n，。]*得时`，对 64 卦实测 **0 命中**
    #   （①的原文中间被「，」截断；其余 6 类措辞根本不认）
    #   ⇒ 「旺时」这一原典判据**从未生效**，原文明写得时的卦被误判「不叶」。
    #   现按 _WANGSHI_PATTERNS 逐条抽取（16 卦），未实现者见 _WANGSHI_SKIPPED。
    wangshi_months, wangshi_src = _extract_wangshi(g.gua_lines)
    if wangshi_months:
        if birth_month in wangshi_months:
            ye = True
            ev.append(f"生月{birth_month} ∈ 旺时（{g.name}「{wangshi_src[:24]}」）→ 得时")
        else:
            ev.append(f"生月{birth_month} ∉ 旺时（{g.name}「{wangshi_src[:24]}」）")
    m2 = re.search(r"如生(月)?不及时[^，。]*不在纳甲[^，。]*", gua_text)
    if m2:
        ev.append(f"卦头提示：{m2.group(0)}")

    if not ye and not najia_hit:
        buye = True
        ev.append("生月不当时令、年干支不在纳甲 → 不叶（凶象，须结合元气化工与爻辞断吉凶）")
    elif ye and najia_hit:
        ev.append("得时 + 纳甲本命 → 叶（吉象，富贵之兆）")
    elif ye and not najia_hit:
        ev.append("得时但不在纳甲 → 半叶（吉中带损，依爻辞细断）")
    elif not ye and najia_hit:
        ev.append("不在卦气时令但年干支合纳甲 → 半叶")

    return YeBuYeResult(ye=ye, buye=buye, gua_qi_month=g.gua_qi_month,
                        birth_month=birth_month, najia_hit=najia_hit, evidence=ev)


# ═══════════════════════════════════════════════════════════════════
# 数之凶吉（起例卷·数足不足论）
# ═══════════════════════════════════════════════════════════════════

def judge_shu_xiong(tian_shu: int, di_shu: int, birth_month: int,
                     gender: str = "") -> ShuXiongResult:
    """
    数足不足论（原典「余」= 天数−25／地数−30，奇偶据此判）：
      天数二十五为正、地数三十为正；无余无不足=安和自宁。
      天数不足<25；地数不足<30。

      孤阳不偶  L974「天数二十六以上，至四十以下，**余偶数**，
                 而地数只得三十」→ 阳有余阴无余
      孤阳自偶  L983「天数三十一至四十一、五十一，**余奇数**，
                 地数只得三十」（与上条同区间，以余数奇偶相区分）
      孤阴背阳  L1046「地数三十至五十、六十，**余偶数**，
                 而天数只二十五」→ 阳无余阴有余
      孤阴向阳  L1055「天数二十五，地数得四十至六十以下，**余奇数**」
      以弱敌强  L1073「地数三十至四十、五十、六十以上，天数只得二十四以下」
      太过有余伤（诗）：有余为凶。

      2026-10-07 补入八条原典命名（详见 yue_ling_shu_ge.SHU_GE_TABLE）：
        阳数偏少 L56、以强伏弱 L58、地数至弱 L65、地数得中 L71、
        地数太过 L72、阴数偏少 L80、天地俱羸 L90、阴阳相战 L93。
      并接入性别向背（L34/L56/L61/L80）、禄数（L105）、援阴阳（L100/L101）、
      命无阴阳（L95）。

    :param gender: ``"male"`` / ``"female"`` / ``""``（未给）。未给性别时，
        性别向背、禄数男女利害、命无阴阳三项一律**不判**，
        绝不按默认性别强套。

      ⚠️ 凶断集合只含 孤阳不偶 / 孤阴背阳 / 以弱敌强 / 太过有余 四条。
         **孤阳自偶与孤阴向阳不进该集合**——原典对二者只给诗断、未言「必凶」：
           孤阳自偶「壮岁艰辛勤苦立，**晚年得势始荣欣**」
           孤阴向阳「**有阳能改过**，有阴奸盗随」
         故按原典只记录命名前后，不套用孤阳不偶的凶断。
         （2026-10-07 修正前，二者被误吞进孤阳不偶/孤阴背阳而误判凶。）
    """
    from .yue_ling_shu_ge import (
        classify_shu_ge, judge_lu_shu, judge_you_yin_yang,
        judge_ming_wu_yin_yang, shu_ge_conflicts, xingbie_xiang_bei,
        judge_chun_qi_qi_ou,
    )

    ev: list[str] = []
    t_state = "有余" if tian_shu > 25 else ("不足" if tian_shu < 25 else "足")
    d_state = "有余" if di_shu > 30 else ("不足" if di_shu < 30 else "足")
    ev.append(f"天数{tian_shu}（正=25，{t_state}）；地数{di_shu}（正=30，{d_state}）")

    pattern = ""
    shu_xiong = False
    # 「余」= 天数−25（阳数之正）／地数−30（阴数之正），奇偶据此判。
    # 原典 L974「孤阳不偶……余**偶**数」、L983「孤阳自偶……余**奇**数」——
    # 两条以奇偶相区分，**必须判余数**，否则孤阳自偶会被孤阳不偶吞掉。
    tian_yu = tian_shu - 25
    di_yu = di_shu - 30
    if t_state == "足" and d_state == "足":
        pattern = "安和自宁"
        ev.append("天地二数无余无不足，最佳，吉凶极定（依卦中断）")
    elif 26 <= tian_shu <= 40 and di_shu == 30 and tian_yu % 2 == 0:
        # 原典 L974：「孤阳不偶　天数二十六以上，至四十以下，**余偶数**，
        #             而地数只得三十是也，乃阳数有余，阴数无余。」
        pattern = "孤阳不偶"
        ev.append(f"天数{tian_shu}（余{tian_yu}，偶）、地数30："
                  f"阳数有余、阴数无余 → 孤阳不偶")
    elif 26 <= tian_shu <= 40 and di_shu == 30:
        # 原典 L983：「孤阳自偶　天数三十一至四十一、五十一，**余奇数**，
        #             地数只得三十是也。」——与上条同区间而余数奇偶相反。
        pattern = "孤阳自偶"
        ev.append(f"天数{tian_shu}（余{tian_yu}，奇）、地数30："
                  f"阳数自偶 → 孤阳自偶（原典 L983）")
    elif 4 <= tian_shu <= 8:
        # 原典 L38：「天数至弱　天数一十有五，如只得四五六七八数，此不满一策，
        #           是谓至弱。」
        # 判据「四五六七八」自足：策＝9（L950「论九是阳之一策」），8 不足一策；
        # 且 L950 明确 9–24 属「不足」而「即非至弱之比」，二者互不重叠。
        # 「天数一十有五」是与「地数三十」平行的**基线陈述**，与 L950
        # 「天数二十五为正」有冲突，但基线不影响落点（正＝25 或正＝15
        # 推出来都是「至弱＝天数 4–8」），故不据此拒算。基线数字本身仍待
        # 网络第二证据，登记在 yue_ling_shu_ge.REFUSED。
        pattern = "天数至弱"
        ev.append(f"天数{tian_shu}（4–8）：「如只得四五六七八数，此不满一策，是谓至弱」"
                  f"→ 天数至弱（原典 L38；策＝9）")
    elif 4 <= tian_shu <= 24 and di_shu == 30:
        # 原典 L56：「阳数偏少　天数二十有五，只得四、五、六至二十四，
        #           地数三十是也。乃阳数不足，阴数足也。此谓之有阴无阳，
        #           得阳数偏少，利女子，不利男子。」
        pattern = "阳数偏少"
        ev.append(f"天数{tian_shu}（4–24）、地数30：阳数不足而阴数足 → "
                  f"阳数偏少（原典 L56，「利女子，不利男子」）")
    elif tian_shu >= 30 and (di_shu == 30 or di_shu <= 12):
        # 原典 L58：「以强伏弱　如天数三十、四十、五十之类，
        #           地数三十或至十二以下是也。若值阳月令不妨，
        #           逢阴月令颇有恃势致凶之象。」
        # 注：地数 13–29 原典未言，本条不覆盖。
        pattern = "以强伏弱"
        ev.append(f"天数{tian_shu}（≥30，原典举三十、四十、五十之类）、"
                  f"地数{di_shu}（30 或 ≤12）→ 天强地弱 → 以强伏弱（原典 L58）")
    elif 8 <= di_shu <= 12:
        # 原典 L65：「地数至弱　地数三十，只得八、九、十、十一、十二数者，是谓至弱。」
        pattern = "地数至弱"
        ev.append(f"地数{di_shu}（8–12）：「地数三十，只得八、九、十、十一、十二数者，"
                  f"是谓至弱」→ 阴数至弱（原典 L65）")
    # 注：「地数得中 L71（32–45）」「地数太过 L72（≥50）」是**地数单轴分档**，
    # 不是「数×月」组合判，故**不占用 pattern 主判位**——否则会把
    # (天数20, 地数40) 的「以弱敌强」顶成「地数得中」，进而让阴月令也被判凶，
    # 与原典 L1073「阴月令逢之，尚庶几」相悖。二者改由下方
    # 「全部命中的数格」循环统一输出判语。
    elif 30 <= di_shu <= 60 and tian_shu == 25 and di_yu % 2 == 0:
        # 原典 L1046：「孤阴背阳　地数三十至五十、六十，**余偶数**，
        #              而天数只二十五是也。乃阳无余，阴数有余。」
        pattern = "孤阴背阳"
        ev.append(f"地数{di_shu}（余{di_yu}，偶）、天数25："
                  f"阴数有余、阳数无余 → 孤阴背阳")
    elif tian_shu == 25 and 40 <= di_shu <= 60:
        # 原典 L1055：「孤阴向阳　天数二十五，地数得四十至六十以下，
        #              **余奇数**是也。乃阴数过，阳数足。」
        # 本条为 2026-10-07 补（原实现完全缺失）。
        pattern = "孤阴向阳"
        ev.append(f"天数25、地数{di_shu}（余{di_yu}）："
                  f"阴数过、阳数足 → 孤阴向阳（原典 L1055）")
    elif tian_shu == 25 and 18 <= di_shu <= 28:
        # 原典 L80：「阴数偏少　地数十八至二十八，天数二十五是也。
        #           乃阳数足，阴数不足。阴数无用与不足，同是谓阴数偏于少也。」
        pattern = "阴数偏少"
        ev.append(f"天数25、地数{di_shu}（18–28）：阳数足、阴数不足 → "
                  f"阴数偏少（原典 L80，「利男子不利女人」）")
    elif di_shu >= 30 and tian_shu <= 24:
        # 原典 L1073：「以弱敌强　地数三十至四十、五十、六十以上，
        #              天数只得二十四以下是也。」
        pattern = "以弱敌强"
        ev.append("地数30以上、天数24以下：地数太过天数不足 → 以弱敌强")
    elif tian_shu <= 24 and di_shu <= 29:
        # 原典 L90：「天地俱羸　天数二十四以下，地数二十九以下，
        #           是乃阴阳二数俱不足者也。」
        pattern = "天地俱羸"
        ev.append(f"天数{tian_shu}（≤24）、地数{di_shu}（≤29）：阴阳二数俱不足 → "
                  f"天地俱羸（原典 L90）")
    elif tian_shu > 25 and di_shu != 30:
        # 原典 L93：「阴阳相战　盖阳数多，阴数少，或阴阳二数俱多，
        #           清浊相干者是也。」
        pattern = "阴阳相战"
        side = "阴数少" if di_shu < 30 else "阴阳二数俱多"
        ev.append(f"天数{tian_shu}（>25，阳数多）、地数{di_shu}（{side}）→ "
                  f"阴阳相战（原典 L93）")
    elif t_state == "有余" or d_state == "有余":
        pattern = "太过有余"
        ev.append("天数或地数有余 → 太过有余伤（诗曰：太过有余伤，性暴应多狠，祸去有余殃）")

    # ── 全量命中与原典冲突披露（2026-10-07 补）────────────────────
    # 不做「首个命中即返回」：L56 阳数偏少与 L83 以弱敌强在
    # (天数≤24, 地数=30) 处判语相反且原典未裁先后，须把全部命中摊开，
    # 由上层显式披露，不静默挑一条。
    _ge = classify_shu_ge(tian_shu, di_shu)
    matched = tuple(r.name for r in _ge)
    conflicts = shu_ge_conflicts(tian_shu, di_shu)
    if matched:
        ev.append("原典命中的数格（出场次序）：" + "、".join(matched))
    for _r in _ge:
        ev.append(f"  数格「{_r.name}」（{_r.citation.split(chr(12290))[0]}）：{_r.verdict}")
    for _c in conflicts:
        ev.append(f"⚠️ 原典冲突未裁：{_c}")

    # ── 援阴／援阳（L100–L101）──────────────────────────────────
    _yy = judge_you_yin_yang(tian_shu, di_shu)
    if _yy["name"]:
        ev.append(f"阳弱援：{_yy['name']}（天数{tian_shu} → {_yy['gua']}卦）"
                  f"（原典 L100「阳弱而余二四六八者，谓之援阴；"
                  f"阳弱而余一三七九者，谓之援阳」）")
    if _yy.get("di_jie"):
        ev.append(f"阴弱援：地数{di_shu} → {_yy['di_jie']}（原典 L101）")

    # ── 阴阳禄数（L105）────────────────────────────────────────
    _lu = judge_lu_shu(tian_shu, di_shu, gender)
    for _h in _lu:
        _fit = ("（性别未给，不判利不利）" if _h.gender_fit is None else
                "（与本性别相利）" if _h.gender_fit else "（与本性别相妨）")
        ev.append(f"阴阳禄数：{_h.which}数{_h.value} 为{_h.name}，"
                  f"{_h.xing_bie} {_fit}（原典 L105）")

    # ── 性别向背（L34/L56/L61/L80）─────────────────────────────
    _xb = xingbie_xiang_bei(tian_shu, di_shu, birth_month, gender)
    for _x in _xb:
        if not _x.applies:
            continue
        _ok = (gender == "male" and _x.favor == "男") or \
              (gender == "female" and _x.favor == "女")
        ev.append(f"性别向背（{_x.rule}）：{gender}命 → "
                  f"{'相利' if _ok else '相妨'}（该条利{_x.favor}、"
                  f"不利{_x.against}）——{_x.reason}")

    # ── 三阳奇偶合象（L99/L714）──────────────────────────────
    # 该条要按**节气窗口**判，须出生公历日；本函数只有 birth_month，
    # 故此处以 birth_date="" 调用，恒返回 None 不判——真正的判定在
    # build_guajie_from_result（有 result.input.birth_date）处另行接入。
    _cq = judge_chun_qi_qi_ou(tian_shu, "")

    # ── 命无阴阳（L95）────────────────────────────────────────
    _mwy, _mwy_xiong = judge_ming_wu_yin_yang(tian_shu, di_shu, birth_month, gender)
    if gender:
        ev.append(f"命无阴阳（L95）：{_mwy}")
        if _mwy_xiong:
            shu_xiong = True

    # 数凶：有余/不足 + 生月合时（阳月令 / 阴月令）
    #
    # 2026-10-07 按原典更正（此前为 birth_month in (1,2,3,4,5,6)，错判 5/6/11/12 四月）。
    #
    # 依据：原典 L854–L914 逐月给出卦气与阴阳消长，**无需推断，只须读表**：
    #     正月雨水→泰  「三阳出于寅」
    #     二月春分→大壮「四阳生于卯」
    #     三月谷雨→夬  「五阳生于辰」
    #     四月小满→乾  「六阳终于巳……乃纯阳之月」
    #     五月夏至→姤  「一阴始生于午」   ← 阴令起点
    #     六月大暑→遁  「二阴生于未」
    #     七月处暑→否  「三阴生于申」
    #     八月秋分→观  「四阴生于酉」
    #     九月霜降→剥  「五阴生于戌」
    #     十月      →坤  「六阴生于亥……乃纯阴之时」
    #     十一月冬至→复「一阳生于子」     ← 阳令起点
    #     十二月大寒→临「二阳生于丑」
    #
    # 即：阳气自十一月冬至一阳生，至四月小满六阳俱备（纯乾）；
    #     阴气自五月夏至一阴生，至十月六阴俱纯（纯坤）。
    #     → 阳月令 = 十一、十二、正、二、三、四月；阴月令 = 五~十月。
    #
    # 原典内部四条交叉验证：
    #     L869「三月谷雨后，阳数太多，而阴数不足，无妨」        → 三月属阳
    #     L872「三四月阳数当健之时，阳数不足，阴数有余」        → 三四月属阳
    #     L872「如夏至阴生，至处暑前后，三阴正长」              → 五月属阴
    #     L714「男命阳月生者，冬至以后，雨水前……」             → 十一月属阳
    #
    # 用处：原典 L1073「以弱敌强……阴月令逢之，尚庶几，
    #       阳月令逢之，必主灭顶之凶」——阳月令逢之才凶，阴月令尚可。
    yang_month = birth_month in YANG_YUE_LING
    if pattern == "以强伏弱":
        # 原典 L58 的方向与下面几条**相反**：「若值阳月令不妨，
        # 逢阴月令颇有恃势致凶之象。」故单独判，不并入通用分支。
        if not yang_month:
            shu_xiong = True
            ev.append(f"生月{birth_month}月（阴月），以强伏弱逢阴月令 → "
                      f"恃势致凶（原典 L58「颇有恃势致凶之象」）")
        else:
            ev.append(f"生月{birth_month}月（阳月），以强伏弱逢阳月令 → "
                      f"「不妨」（原典 L58）")
    elif pattern in ("孤阳不偶", "孤阴背阳", "以弱敌强", "太过有余"):
        if yang_month:
            shu_xiong = True
            ev.append(f"生月{birth_month}月（阳月），数有余逢阳月 → 数凶（不可妄行致凶）")
        else:
            ev.append(f"生月{birth_month}月（阴月），数有余逢阴月 → 数凶程度减轻（依爻辞细断）")
    elif t_state == "不足" or d_state == "不足":
        shu_xiong = True
        ev.append("数不足 → 主夭贫贱薄（虚贫之象），须参元气化工与卦爻断")
    # 2026-10-07 更正：本行原为
    #   「判词：数凶者身亡，但德小者不能当之」
    # 当时的判断是「经 20158 行全库检索，『德小者』『不能当之』两段**零命中**，
    # 该判词是拼凑半句伪造的」——
    # ⚠ **2026-10-24 再订正**：该判断**错了**（错在方法，不在结论）。
    #   补切《河洛理数》**卷二经文**后，在**震卦**断语里查到原句：
    #     「…山身亡但**德小者不能之**」（OCR 形态；正字疑为「德小者不能当之」，
    #     「当」字被 OCR 漏识）⇒ **它有原典出处，不是拼凑**。
    #   原判断错在：把「**包内切片里检索不到**」当成了「**原典没有**」——
    #   当时包内**不含卷二经文**（切片缺口）⇒ 零命中是必然的。
    #   ⇒ 这正是「不得用『包内检索不到』当作『原典没有』」的又一次实证。
    #
    # 引擎**行为不变、仍不引用它**，理由改为（原判的理由是错的）：
    #   「山身亡但德小者不能当之」是**震卦的特定语境**下的**条件式**断语，
    #   脱离「震卦 + 数凶 + 士庶女命分层」的语境即失真；
    #   而数凶的通用判据须**按卦随原典分条**列出，不拼造整句：
    #   L2274「岁运逢之，皆当如此处之，数凶则当以不吉祥断。」
    #   L2292「岁运逢之，居家见服，在仕防谗，去仕不遑，是非难辨，
    #         若数凶，寿何可久？」
    #   L741  「如卦数凶，此走空浮薄之夫。」
    #   L956  「……若阳不足，则非所困而困焉，名必辱……」——合时不足之凶
    ev.append("判词（据原典分条，非整句）："
              "L2274「数凶则当以不吉祥断」；L2292「若数凶，寿何可久」；"
              "L741「如卦数凶，此走空浮薄之夫」")

    return ShuXiongResult(tian_shu=tian_shu, di_shu=di_shu, tian_state=t_state,
                          di_state=d_state, shu_xiong=shu_xiong, pattern=pattern,
                          evidence=ev, matched=matched, conflicts=conflicts,
                          lu_shu=_lu, xingbei=_xb, ming_wu_yin_yang=(_mwy, _mwy_xiong),
                          chun_qi_qi_ou=_cq)


# ═══════════════════════════════════════════════════════════════════
# 正对反对（生死大凶断）
# ═══════════════════════════════════════════════════════════════════

def check_zhengdui_fandui(hexagram: str, other_hexagram: str = "") -> list[str]:
    """
    检查流年卦/命卦是否与对宫构成正对/反对。

    原典依据（《河洛真数·起例卷之上·八卦游年图》）：
      "皆变为体　三爻毕变为体。以卦考之，即正对也。故谓之绝体，
       宜与绝命相同，而诸凶此为最焉" → 正对=三画卦三爻全变（六画卦六爻全变等价）
    《起例卷之下·出后天六合论》：反对+爻凶理失→寿终；《后天详说》：
      "如遇小象与大象反对，定死无疑" → 反对=卦象倒转（综），生死断关键。

    实现映射：
    - 正对（原著=绝体）：六爻全变（三画对宫）
    - 反对（原著=游魂/倒转）：六爻倒转
    - 十二凶卦：⚠️ 今人口径（三门观易整理），10 卷原文未见，仅供判词参考
    返回警示列表（空=无）。
    """
    warns: list[str] = []
    # 正对：错卦
    if hexagram in COMPOUND_GUA and other_hexagram in COMPOUND_GUA:
        u1, l1 = COMPOUND_GUA[hexagram]
        u2, l2 = COMPOUND_GUA[other_hexagram]
        if QIANXI_DUKONG.get(u1) == u2 and QIANXI_DUKONG.get(l1) == l2:
            warns.append(f"{hexagram}与{other_hexagram}互为错卦（正对），六爻全变")
    # 反对：综卦
    if ZONG_GUA.get(hexagram) == other_hexagram:
        warns.append(f"{hexagram}与{other_hexagram}互为综卦（反对），卦象倒转")
    # ⚠ 2026-10-07 审计修：十二凶卦原写在此处，且有两个硬伤——
    #   ① 本函数第一参数在两个调用点传的都是**流年卦/日卦**，文案却写死「命卦」，
    #      实测 case2 命卦实为艮卦，却产出「命卦夬属十二凶卦」的错误凶警；
    #   ② 该判只依赖 hexagram，与 other_hexagram 无关，而调用点按
    #      「先天卦 + 后天卦」调了两次 → **必然重复两条**。
    #   现拆为独立函数 check_twelve_xiong，由调用方按真实卦名与标签各调一次。
    return warns


def check_twelve_xiong(hexagram: str, label: str = "卦") -> list[str]:
    """十二凶卦判别（**单卦属性**，与配对卦无关，故独立成函数）。

    ⚠ 口径：TWELVE_XIONG_GUA 出自今人「三门观易」整理口径，非原典。
    label 必须由调用方按该卦的真实身份传入（命卦／流年卦／日卦…），
    不得写死——2026-10-07 审计查出写死「命卦」曾导致流年卦被误标为命卦。
    """
    if hexagram and hexagram in TWELVE_XIONG_GUA:
        return [f"{label}{hexagram}属十二凶卦（复临泰大壮夬乾姤遁否观剥坤）"
                f" → 不吉，若卦中相生或与月卦相投可去凶"]
    return []


# ═══════════════════════════════════════════════════════════════════
# 死断诸法（起例卷之下·后天详说）
# ═══════════════════════════════════════════════════════════════════

def _yao_buji(ci: str, buye: str = "", suiyun: str = "") -> bool:
    """判爻辞凶（含不叶/岁运逢凶）。原典：爻凶理失/爻辞凶。"""
    text = f"{ci} {buye} {suiyun}"
    bad = ("凶", "危", "死", "灾", "咎", "厉", "悔", "亡", "败", "伤", "困", "病", "讼")
    return any(w in text for w in bad)


_SD_ALT = "同书「僧人多极后天」条另载：「此数不许行到后天五爻，行到四爻，方可断人生死」"

# 阴骘说明：出《书·洪范》「惟天阴骘下民」，指**暗中积累的德行**（阴德）——
# 做了不为人知的善事而积下的功德，属相学/伦理范畴，可由泪堂等面相征象佐证。
# 它**不是**由生辰干支、卦象或河洛数理能推算出来的量。
# 故本层无法替用户判定有无阴骘，触发时只能两支并陈，不得径取「无阴骘」。
_SD_YINZHI = ("阴骘＝暗中积累的德行（出《书·洪范》「惟天阴骘下民」），"
              "非生辰卦数所能推算，故本盘不作预设，两支并陈")


def _sd(quote: str, trigger: str, limit: str, alt: str = "—") -> str:
    """死断断语四段式：原句照出 + 触发 + 限定 + 异说。

    2026-10-06 用户裁定：原典硬断原句**照出**（保留考据），
    但必须强制前后带限定，避免下游 LLM 脱离条件字面复述成寿命断言。
    """
    return (f"【原典断语·须带条件读，勿字面直解】{quote}"
            f"｜触发：{trigger}｜限定：{limit}｜异说：{alt}")


def judge_si_duan(
    *,
    prenatal_name: str,
    postnatal_name: str,
    tian_yuan_fan: str = "",        # 天元反卦（年干纳甲之错卦）
    di_yuan_fan: str = "",          # 地元反卦（年支宫位之错卦）
    shu_xiong: bool = False,        # 数凶
    dayun_line_index: int | None = None,      # 当前大运行至爻位（0初~5上）
    dayun_phase: str = "",                # 当前大运段 先天/后天（死断四法限定用）
    recent_years: list[dict] | None = None,   # 近3年流年判词 [{year, hexagram, yao, ci, buye, suiyun}]
    recent_dayun_yao: list[dict] | None = None,  # 已行大运爻判词（含当前）[{hexagram, yao, ci, buye, suiyun}]
) -> list[str]:
    """
    死断诸法（《河洛真数·起例卷之下·后天详说》，2026-10-06 按原著上下文校订）。

    原文逐字：

      「如后天之气数行至君爻之位，此为数足，到此必死。无阴骘者，生日之前便死。
        如遇小象与大象反对，定死无疑。有阴骘者，到君爻阳爻延九年，必须迍蹇天眚之患，
        纵到君爻，亦不许行至上极一爻，寿必不久。此或有到此者，必须主大变之祸殃，
        凶暴之挠，或生异疾，或殃及子孙，或反本复始之失。……有过此上极之爻，
        当为超凡越世之士，乃逃出先后之命，不系数中，不属天地所拘。」

      「若行后天，连三爻不吉，必多坎壈。若过了第四爻，遇凶，十死八九。
        若流年连三年不吉，卦爻又不吉，本身卦不佳，重反支干元气，便可以死断之。」

    ── 本次校订的六处（依据原著上下文，非字面臆断）─────────────────

    ① **阴骘前置原先整个丢失**。原文死断明写「无阴骘者…便死」「有阴骘者…延九年」，
       这是死断的**成立前提**，且同篇《大易之数》另有「九五、六五、上九、上六乃君庙
       之极，物极必反，理之当然，**非大器阴骘，未至先亡**」——阴骘是两处极断的
       共同例外条款。旧实现不判阴骘，等于对所有人一律按「无阴骘」断言。
       然阴骘（暗中积德）属德行/相学范畴，**非生辰卦数可推**，
       故本层不预设，两支并陈（见 _sd_yinzhi）。
    ② **「过了第四爻」原先差一位**。旧实现判 li==3（正在第四爻）。
       原著同篇「大易之数」条自解其义：「假令上爻坐元堂，四五爻是君庙五爻……
       以上初是初爻，**以五上是过**」——「过」指越过本爻之后，即已入下一爻。
       故「过了第四爻」＝已过四爻入五爻（li>=4），非「正行第四爻」。
    ③ **「连三爻」原先换了口径**。原文「连**三爻**」指大运所历的连续三**爻**；
       旧实现拿「近三年**流年**判词」代替。此条是实测命中最频繁的一条
       （180 盘 54 盘），口径偏差影响面最大，现改由 recent_dayun_yao 传入。
    ④ **「反对定死无疑」原先被提成独立法**。它在原文中紧接「无阴骘者…便死」
       之后，是**该分支的附加条件**，不与前条并列。故有阴骘者不作此断。
    ⑤ **上爻后果原先只引半句**。原文于上极所列后果为「主大变之祸殃，凶暴之挠，
       或生异疾，或殃及子孙，或反本复始之失」，且紧接着说「有过此上极之爻，
       当为超凡越世之士」。旧实现只引「寿必不久」一句，把两头全丢了。
    ⑦ **四法（①君爻②过四爻③小象大象反对④上极）原典全部限定在**后天段**。
       原文三处独立明证：L1552「如**后天**之气数行至君爻之位」
       「纵到君爻，亦不许行至上极一爻」、L1555「若**行后天**，连三爻不吉」、
       L1567「此数不许行到**后天**五爻，行到四爻，方可断人生死」。
       且全库检索「先天之气数」**零命中**——原典根本没有先天死断一支。
       旧实现取 dayun_line_index 只按虚岁命中段、不辨 phase，
       致先天段行至上爻（li=5）误触上极条，而该条触发语写死
       「后天运程行至上爻」——标签与事实相反。2026-10-07 补 phase 门控。
       形参 dayun_phase 默认空串而非「后天」：漏传时不触发，
       宁可沉默也不替原典补一条它没有的先天死断。
       **⑥流年三连条未加门控**：原典该句另起「若」字新分句、主语是流年
       （流年不分先后天段），与①②③④的大运爻位口径不同，两存待考。
    ⑥ **原典自相矛盾，须两说并存**。「僧人多极后天」条明载：「或谓康节曰，
       此数不许行到后天五爻，行到四爻，方可断人生死，今有不满二十而死者，
       亦有八九十而死者，祸福安在？」——一处说五爻即死、一处说四爻才断，
       且后一条自带反例否证。故每条均带「异说」段留档，不做单方裁断。
    """
    warns: list[str] = []

    cur_yao = recent_years[-1] if recent_years else None
    cur_buji = bool(cur_yao) and _yao_buji(
        cur_yao.get("ci", ""), cur_yao.get("buye", ""), cur_yao.get("suiyun", ""))

    # 2026-10-07 修：死断四法（①②③④）原典限定后天段，详见 docstring ⑦。
    is_hou_tian = (dayun_phase == "后天")

    # ── ① 君爻（五爻）：数足，原典死断以「无阴骘」为前提 ────────────
    # 2026-10-06 修：原判 `>= 4` 把上爻（li=5）也并入君爻条。
    # 原文「纵到君爻，亦不许行至上极一爻」——君爻=五爻、上极=上爻，两级分明；
    # li=5 只走上极条（④），不报君爻。
    if is_hou_tian and dayun_line_index == 4:
        warns.append(_sd(
            quote="「如后天之气数行至君爻之位，此数为足，到此必死。"
                  "无阴骘者，生日之前便死。有阴骘者，到君爻阳爻延九年，"
                  "必须迍蹇天眚之患。」",
            trigger="后天运程行至五爻（君位·君庙之极）",
            limit=f"{_SD_YINZHI}。本条为**条件式立断**，两支须同时呈现，"
                  f"不得径取「无阴骘」一支当作已定之论",
            alt=_SD_ALT,
        ))

        # ② 「若过了第四爻，遇凶，十死八九」——原典指已过四爻入五爻（li>=4）。
        # 2026-10-06 修：此条自君爻块拆出独立判。原典「若过了第四爻」是独立一句，
        # 语义为「已过四爻入五爻及以上」；若留在君爻块（现==4）则 li=5 时漏断。
        if cur_buji and dayun_line_index is not None and dayun_line_index >= 4:
            warns.append(_sd(
                quote="「若过了第四爻，遇凶，十死八九。」",
                trigger="运程已过第四爻、进入五爻及以上 + 当前流年爻辞凶",
                limit="原典「大易之数」条以「以五上是过」自释「过」字，"
                      "「过」指越过本爻入下一爻；故此处不是「正行第四爻」",
                alt=_SD_ALT,
            ))

        # ③ 「如遇小象与大象反对，定死无疑」——原典系「无阴骘」分支的附加条件
        if cur_yao:
            hx = cur_yao.get("hexagram", "")
            if hx:
                # 只取「反对」信号，故不并入 check_twelve_xiong
                fan = (check_zhengdui_fandui(hx, prenatal_name)
                       + check_zhengdui_fandui(hx, postnatal_name))
                if any("反对" in w for w in fan) and cur_buji:
                    warns.append(_sd(
                        quote="「如遇小象与大象反对，定死无疑。」",
                        trigger=f"行至君爻 + 流年小象（{hx}）与命卦大象成反对 + 爻辞凶",
                        limit=f"{_SD_YINZHI}。本条在原文系「无阴骘者…便死」的"
                              "**附加条件**，非独立判据；有阴骘者不作此断",
                        alt=_SD_ALT,
                    ))

    # ── ④ 上爻（上极）：原典所列后果不止「寿必不久」 ────────────────
    if is_hou_tian and dayun_line_index == 5:
        warns.append(_sd(
            quote="「纵到君爻，亦不许行至上极一爻，寿必不久。此或有到此者，"
                  "必须主大变之祸殃，凶暴之挠，或生异疾，或殃及子孙，"
                  "或反本复始之失。……有过此上极之爻，当为超凡越世之士，"
                  "乃逃出先后之命，不系数中，不属天地所拘。」",
            trigger="后天运程行至上爻（上极）",
            limit="原典于上极所列后果为祸殃、异疾、殃及子孙、反本复始，"
                  "**并非直断死亡**；原文紧接着又说「有过此上极之爻，当为超凡越世之士」，"
                  "旧实现只引「寿必不久」半句，漏此两头",
        ))

    # ── ⑤ 「连三爻不吉」：原典指大运所历之爻，非流年 ─────────────────
    # 2026-10-06 修：原文「若**行后天**，连三爻不吉，必多坎壈」——主语是行后天段。
    # 先天段（本盘渐卦先天六爻段）不得触发坎壈。门控：最近连续三大运爻须全属后天段。
    if recent_dayun_yao and len(recent_dayun_yao) >= 3:
        last3 = recent_dayun_yao[-3:]
        if all(y.get("phase") == "后天" for y in last3) and all(
                _yao_buji(y.get("ci", ""), y.get("buye", ""), y.get("suiyun", ""))
                for y in last3):
            seq = "、".join(f"{y.get('hexagram', '')}{y.get('yao', '')}" for y in last3)
            warns.append(_sd(
                quote="「若行后天，连三爻不吉，必多坎壈。」",
                trigger=f"已行连续三个大运爻且其爻辞皆不吉（{seq}）",
                limit="原典「连三爻」主语是大运所历之**爻**；"
                      "旧实现误用近三年**流年**判词代替，口径不同",
            ))

    # ── ⑥ 全篇唯一未附阴骘前置者 ─────────────────────────────────────
    # 原典四条件（起例卷之下·后天详说 L1555，**影印原页第 142 页逐字核定**）：
    #   「若流年连三年不吉，**卦爻又不吉**，本身卦不佳，重反支干元气，便可以死断之。」
    # 逐条件对应：
    #   ① 流年连三年不吉   → 近三年流年卦皆不吉
    #   ② 卦爻又不吉       → **主语 = 流年卦之爻**（见下）
    #   ③ 本身卦不佳       → 数凶（shu_xiong）
    #   ④ 重反支干元气     → 天元反/地元反俱在命卦
    #
    # ⚠ 2026-10-24 核定（此前「②未单列」是**遗漏**，本轮补上依据）：
    #   影印原页逐字确认四条件俱在，「卦爻又不吉」**不是** OCR/传抄讹误。
    #   「卦爻」= **流年卦之爻**，依据：
    #     · L780「凡看大贵人命，**流年卦爻**多有不佳」—— 原典把
    #       「流年卦爻」当完整名词短语用（与「流年小象」L774 并用）；
    #     · L486「如遇**本身卦爻**理体不吉」/ L1843「富郑公以**本身卦**
    #       及流年卦大书于庭中壁上」—— 原典指本身卦时会明写「本身卦」，
    #       L34 第三条件已写「本身卦不佳」，第二条件若也指它应作
    #       「本身卦爻又不吉」，实际作「卦爻又不吉」（无「本身」二字）。
    #
    # ⚠ 为何 ② 与 ① **合流**（不单列）：
    #   原典只说「卦爻又不吉」，**未说「卦爻」指哪一爻**。
    #     · 若取**行年爻**（＝流年判词所取之爻，见 §14.35 L369 自注
    #       「流年佳。（即小象行年爻也。）」）⇒ ② 与 ① 是**同一个爻、
    #       同一个凶字判据**，② 成为 ① 的同义反复，拆分**无判别力**；
    #     · 若取别的爻 ⇒ 原典无据，属**无据擅改**。
    #   故维持合流（引擎现状恰等于「②取行年爻」这一解释），
    #   并把「②未单列」显式留档 —— 使后人知它是**有据的取舍**而非遗漏。
    #   留档：heluo_engine/docs/死断四条件核定_20261024.md（附完整证据链）。
    #   重开条件：若取得新版本原典或旁证明确「本身卦爻又不吉」，则可重开此条。
    #
    # ⚠ 另记（《河洛理数》版本差异，**不改**）：1632 笔写本 L6784-6785
    #   作「若流年連三年不吉**本身卦又不佳**可以死之」—— **只有三条件**，
    #   无「卦爻又不吉」。但《河洛理数》与《河洛真数》是**两部不同的书**
    #   （归一化 10-gram 重合仅 3.9%，第一轮已实测），故那是**另一部书的删节**，
    #   不是《河洛真数》的异文 ⇒ **不得**据此删改本条的第二条件。
    if (
        recent_years and len(recent_years) >= 3
        and all(_yao_buji(y.get("ci", ""), y.get("buye", ""), y.get("suiyun", ""))
                for y in recent_years[-3:])
        and shu_xiong
        and tian_yuan_fan and di_yuan_fan
        and _in_gua(tian_yuan_fan, prenatal_name, postnatal_name)
        and _in_gua(di_yuan_fan, prenatal_name, postnatal_name)
    ):
        warns.append(_sd(
            quote="「若流年连三年不吉，卦爻又不吉，本身卦不佳，"
                  "重反支干元气，便可以死断之。」",
            trigger="近三年流年卦爻皆不吉（含「卦爻又不吉」，与「流年连三年不吉」"
                    f"同一判据：行年爻） + 数凶（本身卦不佳） + "
                    f"天元反{tian_yuan_fan}、地元反{di_yuan_fan}俱在命卦",
            limit="本条原典未附阴骘前置，是《后天详说》全篇唯一无此限定者；"
                  "四条件中的「卦爻又不吉」与「流年连三年不吉」在本实现中合流"
                  "（原典未指明「卦爻」取哪一爻，取行年爻则二者为同一判据），"
                  "详见 heluo_engine/docs/死断四条件核定_20261024.md",
        ))

    return warns


def _in_gua(trigram: str, *gua_names: str) -> bool:
    """三画卦是否出现在某命卦（上/下卦）中。"""
    for g in gua_names:
        if g in COMPOUND_GUA and trigram in COMPOUND_GUA[g]:
            return True
    return False


# ═══════════════════════════════════════════════════════════════════
# 综合断卦
# ═══════════════════════════════════════════════════════════════════

def compose_guajie(
    *,
    # 命主主链
    prenatal_name: str,
    postnatal_name: str,
    yuantang_yao: str,            # 先天元堂爻名（如"九三"）
    birth_month: int,
    tian_shu: int,
    di_shu: int,
    year_ganzhi: str = "",        # 年干支（纳甲本命）
    gender: str = "",             # "male"/"female"/""（未给）。起例卷之中
                                   # L34/L61「利男子/利女人」、L95「命无阴阳」、
                                   # L105「利男不利女/利女不利男」的入参；
                                   # 空串表示未给，judge_shu_xiong 一律不判性别向背。
    # 流年
    liunian_hexagram: str = "",
    liunian_yao: str = "",
    target_year: Optional[int] = None,     # 流年公历年份（入库）
    # 流月（应期）
    liuyue_hexagram: str = "",
    liuyue_yao: str = "",
    # 元气化工
    yuan_qi_trigrams: list[str] | None = None,   # 天/地元气卦
    hua_gong_trigram: str = "",
) -> GuaJieResult:
    """
    组合解卦：先天/后天 + 元堂 + 流年判词 + 流月应期 + 数凶 + 元气化工 + 正对反对。
    """
    res = GuaJieResult()
    res.liunian_hexagram = liunian_hexagram
    res.liunian_year = target_year
    res.liuyue_hexagram = liuyue_hexagram
    ev = res.evidence

    # ── 命卦判词（先天卦辞+卦象断语+精义/释义） ─────────────────
    bm = load_guajie_data().get(prenatal_name)
    if bm:
        res.benming = {
            "hexagram": prenatal_name,
            "gua_ci": bm.gua_ci,
            "gua_ci_jingyi": bm.gua_ci_jingyi,
            "gua_ci_shiyi": bm.gua_ci_shiyi,
            "lines": bm.gua_lines,
            "lines_jingyi": bm.lines_jingyi,
            "lines_shiyi": bm.lines_shiyi,
        }
        # ★ 2026-10-24：命卦层的**卦头断语**同样扫描六亲/婚育/寿夭意象。
        #   命卦断语是**本命层**（非流年），但它落在的**人生领域**不变
        #   （维度表 L2 是「领域」，不是「时间层」）⇒ 仍归对应子维度。
        #   命卦断语是**条件式**的（「数卦不叶…」「岁运逢之…」）⇒ 原句带条件一并留。
        for _hit in _collect_liuqin_hits(bm):
            ev.append(
                f"  本命卦{_hit['category']}（{_hit['keyword']}）：{_hit['quote']}",
                dim=_hit["dimension"])

    # ── 流年动爻判词（查询式字典） ──────────────────────────────
    if liunian_hexagram and liunian_yao:
        y = query_yao_duan(liunian_hexagram, liunian_yao)
        if y:
            res.liunian_yao = y
            ev.append(f"流年卦{liunian_hexagram} {liunian_yao}爻：{y.ci}",
                      dim="TIMELINE.02")
            if y.ye:
                ev.append(f"  叶者：{y.ye}", dim="TIMELINE.02")
            if y.buye:
                ev.append(f"  不叶者：{y.buye}", dim="TIMELINE.02")
            if y.suiyun:
                ev.append(f"  岁运逢之：{y.suiyun}", dim="TIMELINE.01")
            # ★ 2026-10-24 六亲/婚育/寿夭意象接入（维度缺口补齐）：
            #   判词库原句里本就有「免克绝子孙」「亲眷刑伤，婚嗣孤克」
            #   「或生子孙」「兄弟之忧」等断语，此前**只按卦名归位、不断语归位**
            #   ⇒ 「婚姻/子女/父母/手足/夭横」几格维度从不出现在证据链里。
            #   现按**原句匹配**（不生成新断语、不改一字）产出带维度的证据；
            #   断语是**条件式**的（「岁运逢之…」「数卦不叶…」）⇒ 原句连同
            #   条件一并带出，脱离条件引用即失真。
            for _hit in _collect_liuqin_hits(y):
                ev.append(
                    f"  {_hit['category']}（{_hit['keyword']}）：{_hit['quote']}",
                    dim=_hit["dimension"])
        # 叶/不叶
        yb = judge_ye_buye(liunian_hexagram, birth_month, year_ganzhi)
        if yb:
            res.liunian_ye_buye = yb
            ev.extend((f"  叶/不叶：{e}" for e in yb.evidence), dim="TIMELINE.02")
        # 正对反对（流年卦 vs 先天卦 / vs 后天卦）——两次配对的 other 各不相同，
        # 本身合法；但先天卦与后天卦可能同名，故此处去重（保持原序）。
        # 十二凶卦是流年卦自身的属性，调一次、标签写「流年卦」（见 P1-a）。
        zdfd = (check_zhengdui_fandui(liunian_hexagram, prenatal_name)
                + check_zhengdui_fandui(liunian_hexagram, postnatal_name)
                + check_twelve_xiong(liunian_hexagram, "流年卦"))
        zdfd = list(dict.fromkeys(zdfd))   # 去重且保序
        res.zhengdui_fandui = zdfd
        ev.extend((f"  正对反对：{w}" for w in zdfd), dim="PATTERN.04")

    # ── 流月应期 ──────────────────────────────────────────────
    if liuyue_hexagram and liuyue_yao:
        y = query_yao_duan(liuyue_hexagram, liuyue_yao)
        if y:
            res.liuyue_yao = y
            ev.append(f"流月卦{liuyue_hexagram} {liuyue_yao}爻：{y.ci}", dim="TIMELINE.03")
            if y.suiyun:
                ev.append(f"  岁运逢之：{y.suiyun}", dim="TIMELINE.01")
            # ★ 2026-10-24：流月层同样接入六亲/婚育/寿夭意象（见流年处说明）
            for _hit in _collect_liuqin_hits(y):
                ev.append(
                    f"  {_hit['category']}（{_hit['keyword']}）：{_hit['quote']}",
                    dim=_hit["dimension"])

    # ── 数凶 ──────────────────────────────────────────────────
    sx = judge_shu_xiong(tian_shu, di_shu, birth_month, gender)
    res.shu_xiong = sx
    ev.extend((f"  数之凶吉：{e}" for e in sx.evidence), dim="PATTERN.02")

    # ── 爻辞取象（原典 L741，2026-10-08 接入）─────────────────────
    # 原典「凡看爻辞依不得周易正解……文王作易，近取诸身，远取诸物，
    #       如言龙则必贵」——不看爻辞吉凶，只看辞中出了哪个字。
    # 本层取**辞面**（ci 爻辞 + xiang 象曰）逐层扫描，三层爻辞都在内：
    #   流年（主断位）＞ 流月、流日（应期位，辞面较短，命中自然少）。
    #
    # 两个入参刻意**不填**，理由如下，不得随手补上：
    #   ① 农历日（言月「生望前者佳」）：compose_guajie 没有日粒度输入。
    #      拿公历日冒充农历日正是 2026-10-07 化工层修掉的那类错，不重犯。
    #   ② 卦数凶（言鸟「如卦数凶，此走空浮薄之夫」）：本卷未给「卦数凶」判法。
    #      judge_shu_xiong 判的是**天数/地数**之凶，与「卦数」不是同一物，
    #      拿它代填等于凭空造一条原典没有的判据。→ 二者条件均判为不可判。
    #
    # 条件不可判者**照常登记断语**，但不参与判定（participated=False），
    # 与 yao_xiang 模块的约定一致：能落的是取字↔断语，不能落的是吉凶方向。
    for _tag, _yd in (("流年", res.liunian_yao), ("流月", res.liuyue_yao),
                      ("流日", res.liuri_yao)):
        if _yd is None:
            continue
        _text = f"{_yd.ci or ''} {_yd.xiang or ''}"
        _hits, _evs = _scan_yao_xiang(
            _text, birth_month=birth_month or None, day_lunar=None,
            gender=gender, shu_gua_xiang=None)
        if not _hits:
            continue
        for _h in _hits:
            res.yao_xiang_hits.append(_h)
        ev.append(f"  {_tag}爻辞取象（{len(_hits)} 条）："
                  + "、".join(f"言{h.key}" for h in _hits), dim="HEALTH.02")
        ev.extend((f"    {e}" for e in _evs), dim="HEALTH.02")


    # ── 元气化工（流年遇） ─────────────────────────────────────
    if yuan_qi_trigrams:
        res.yuan_qi_hit = bool(yuan_qi_trigrams)
        if res.yuan_qi_hit:
            ev.append("流年遇元气 → 必然得财利", dim="WEALTH.01")
    if hua_gong_trigram:
        res.hua_gong_hit = True
        ev.append(f"流年遇化工（{hua_gong_trigram}）→ 中举中进士生贵子",
                      dim="CAREER.01")

    # ── 纳音五行元气（互体亦算，起例卷之上） ─────────────────────
    if year_ganzhi and len(year_ganzhi) == 2:
        nayin_ev = judge_nayin_yuanqi(year_ganzhi[0], year_ganzhi[1], prenatal_name)
        if nayin_ev:
            res.nayin_yuanqi.extend(nayin_ev)
            ev.extend((f"  纳音元气：{e}" for e in nayin_ev), dim="HEALTH.01")
        huti_ev: list[str] = []
        for g in (prenatal_name, postnatal_name):
            if g in COMPOUND_GUA:
                pass  # 互体需六爻序列，主链另行挂载（build 层）
        if huti_ev:
            res.nayin_yuanqi.extend(huti_ev)
            ev.extend((f"  互体纳音：{e}" for e in huti_ev), dim="HEALTH.01")

    # ── 元堂断语（六位贵贱，起例卷之上） ───────────────────────
    # 原典："初为庶民，二为侯牧，三为公卿节制，四为近侍大臣，
    #        五为君位，六为天枢，又为宗庙宫庭大内，又为山林八极之外。
    #        惟五位为佳，二次之，三四又次之"
    # 2026-09-15 定案：初=庶民（1632印本/10卷本/中华典藏三源一致）；
    # 三=公卿节制（1632最古刻本；通行本"公乡"为形近误刻）。
    if yuantang_yao:
        _wei = yuantang_yao[1] if len(yuantang_yao) > 1 and yuantang_yao[0] in ("九", "六") else yuantang_yao[0]
        # ⚠ 2026-10-24 修正：下列各处原写「（原典：初为庶民，元堂居初爻者多从寒微起家）」
        #   —— 逗号**后半段是引擎自己的释语**，不是原典话；把它并进「原典：」标注，
        #   等于以原典的权威呈现一句并非原典的话（自撰冒引）。现只把**纯原典**部分
        #   放进标注，引擎释语留在标注之外。原典实句见起例卷之上「六位贵贱」。
        #   注：「初上又次之」是引擎据 1632 刻本补的（通行本「六位贵贱」段无此语），
        #   故不进「原典：」标注，改标刻本依据。
        if _wei == "初":
            ev.append(f"元堂居{yuantang_yao}（庶民位）：多从寒微起家（原典：初为庶民）",
                      dim="CAREER.03")
        elif _wei == "二":
            ev.append(f"元堂居{yuantang_yao}（侯牧位）：卦佳数足可牧民一方"
                      f"（原典：二为侯牧；惟五位为佳，二次之）", dim="CAREER.03")
        elif _wei == "三":
            ev.append(f"元堂居{yuantang_yao}（公卿节制位）：掌节制之权，次五二之贵（原典：三为公卿节制）",
                      dim="CAREER.03")
        elif _wei == "四":
            ev.append(f"元堂居{yuantang_yao}（近侍大臣位）：近君侍从之贵（原典：四为近侍大臣）",
                      dim="CAREER.03")
        elif _wei == "五":
            ev.append(f"元堂居{yuantang_yao}（君位）：卦名佳、二数足、化工元气得时 → 贤良上贵之命"
                      f"（原典：五为君位；惟五位为佳）", dim="CAREER.03")
        elif _wei == "上":
            ev.append(f"元堂居{yuantang_yao}（天枢/宗庙宫庭大内/山林八极之外）：贵极为三公，否则闲散卑职（原典：六为天枢，又为宗庙宫庭大内，又为山林八极之外）",
                      dim="CAREER.03")

    # ── 十二凶卦（命卦） ───────────────────────────────────────
    if prenatal_name in TWELVE_XIONG_GUA:
        res.twelve_xiong = True
        ev.append(f"先天命卦{prenatal_name}属十二凶卦之一 → 不吉（相生或与月卦相投可去凶）",
                      dim="PATTERN.01")

    # ── 综合判词（人话摘要） ───────────────────────────────────
    s = res.summary
    if res.liunian_yao:
        if res.liunian_yao.ye:
            s.append(f"流年{liunian_hexagram}{liunian_yao}爻叶者：{res.liunian_yao.ye}")
        if res.liunian_yao.buye:
            s.append(f"流年{liunian_hexagram}{liunian_yao}爻不叶者：{res.liunian_yao.buye}")
        if res.liunian_yao.suiyun:
            s.append(f"岁运逢之：{res.liunian_yao.suiyun}")
    if sx.shu_xiong:
        # 2026-10-07 更正：原为「→ 数凶者身亡，但德小者不能当之」，
        # 改引原典 L2274 / L2292 两条明文。
        # ⚠ 2026-10-24 再订正：**该整句并非伪造** —— 它是《河洛理数》卷二经文
        #   震卦的原句（「…山身亡但德小者不能之」，OCR 漏识「当」字）；
        #   当时判「伪造」是因**包内切片不含经文**（把切片缺口当成原典缺口）。
        #   仍不引用它的理由：那是**震卦特定语境**的条件式断语，脱离该语境即失真；
        #   数凶的通用判据须**按卦随原典分条**列出。
        s.append(f"数凶（{sx.pattern}：天{sx.tian_shu}/{sx.di_shu}）"
                 f"→ 原典 L2274「数凶则当以不吉祥断」；L2292「若数凶，寿何可久」")
    if res.zhengdui_fandui:
        s.append("流年卦与命卦成正对/反对 + 爻辞凶 + 无元气化工 → 生死大凶（不死亦有横灾）")
    if res.yuan_qi_hit and not sx.shu_xiong:
        s.append("流年遇元气/化工 → 得财利、科甲之喜；爻辞虽凶，于富贵天年不碍")
    if not s:
        s.append("（无流年/流月输入，仅命卦判词）")

    return res


# 月支 → 节气月（寅=正月…丑=十二月，河洛以节气定月）
BRANCH_TO_MONTH = {"寅": 1, "卯": 2, "辰": 3, "巳": 4, "午": 5, "未": 6,
                   "申": 7, "酉": 8, "戌": 9, "亥": 10, "子": 11, "丑": 12}

# 阳月令 / 阴月令（原典《河洛真数·起例卷之中》L10-L30 十二月卦气表，
# 2026-10-07 逐条取证；2026-10-22 更正行号，见 GUA_QI_MONTH_TABLE 处说明）
#
#   阳气：十一月冬至「一阳生于子」→ 四月小满「六阳终于巳，乃纯阳之月」
#   阴气：五月夏至  「一阴始生于午」→ 十月      「六阴生于亥，乃纯阴之时」
#
# 故阳月令 = 11、12、1、2、3、4；阴月令 = 5、6、7、8、9、10。
# 注：此处月份为**节气月**（建寅），与 BRANCH_TO_MONTH 一致。
#     ⚠ 2026-10-24 订正：原注释写「寅月=正月=**雨水后**」——
#     建寅的正月自**立春**起（雨水后已是卯月），差一个月。
#     BRANCH_TO_MONTH 的**代码是对的**（寅=1 … 丑=12），错的只是这句说明。
YANG_YUE_LING = frozenset({11, 12, 1, 2, 3, 4})
YIN_YUE_LING = frozenset({5, 6, 7, 8, 9, 10})

# 十二月卦气表（**十二辟卦的月令卦**）：月 → (节气, 卦名, 原典自述)
# 「原典自述」一栏直接摘自原文，供守卫逐条比对，不得改写。
#
# ⚠ 2026-10-22 更正出处行号：原注释写「原典 L854–L914」，那**不是包内底本**
#   的行号（heluo_engine/orig/河洛真数_起例卷之中.txt 只有 213 行）——
#   应是取证时所用另一底本（更长的整本 txt）的行号，搬进包内后未同步。
#   现改为**包内可回查**的实际位置：《河洛真数·起例卷之中》L10-L30
#   （泰 L10 / 大壮 L12 / 夬 L14 / 乾 L18 / 姤 L20 / 遁 L21 / 否 L23 /
#     观 L25 / 剥 L27 / 坤 L28 / 复 L29 / 临 L30）。
#   守卫 tests/heluo/test_heluo_gua_qi_month_rules.py 按此逐条比对。
#
# ⚠ 本表与「每卦卦头自述的卦气属X月」（`_parse_gua_header` 从 JSON 解析，
#   55 卦、多对多）**是两套不同的原典规则**，不是同一规则的两个来源：
#   本表是「月 → 该月的月令卦」（十二辟卦），后者是「每卦 → 属几月」。
#   二者唯一的交叉点是：十二辟卦的卦头自述卦气月必须等于其月令月
#   （坤、复的卦头未写，属已知留档）。**不得互相替代。**
GUA_QI_MONTH_TABLE: dict[int, tuple[str, str, str]] = {
    1:  ("雨水", "泰",   "三阳出于寅，三阳至而大道成"),
    2:  ("春分", "大壮", "四阳生于卯，四阳盛壮"),
    3:  ("谷雨", "夬",   "五阳生于辰，其卦为夬"),
    4:  ("小满", "乾",   "六阳终于巳……乃纯阳之月"),
    5:  ("夏至", "姤",   "一阴始生于午"),
    6:  ("大暑", "遁",   "二阴生于未，其卦为遁"),
    7:  ("处暑", "否",   "三阴生于申，其卦为否"),
    8:  ("秋分", "观",   "四阴生于酉，四阴既长，是名观卦"),
    9:  ("霜降", "剥",   "五阴生于戌，五阴长而阳剥落"),
    10: ("—",    "坤",   "六阴生于亥……乃纯阴之时"),
    11: ("冬至", "复",   "一阳生于子"),
    12: ("大寒", "临",   "二阳生于丑，其卦为临"),
}

# 阳数递增序（正月三阳→四月六阳）与阴数递增序（五月一阴→十月六阴）
# 用于守卫「月令阴阳」与「卦气阴阳进退」严格对应，防止将来再简化成
# 「1-6 月为阳」这类按春夏秋切分的错法。
_YANG_MONTHS_BY_YANG_COUNT = {1: 11, 2: 12, 3: 1, 4: 2, 5: 3, 6: 4}
_YIN_MONTHS_BY_YIN_COUNT = {1: 5, 2: 6, 3: 7, 4: 8, 5: 9, 6: 10}

# 全称 → 简称（64 卦，与 yi_interpreter ALIASES 一致反查）
_FULL_TO_SHORT = {
    "乾为天": "乾", "坤为地": "坤", "水雷屯": "屯", "山水蒙": "蒙",
    "水天需": "需", "天水讼": "讼", "地水师": "师", "水地比": "比",
    "风天小畜": "小畜", "天泽履": "履", "地天泰": "泰", "天地否": "否",
    "天火同人": "同人", "火天大有": "大有", "地山谦": "谦", "雷地豫": "豫",
    "泽雷随": "随", "山风蛊": "蛊", "地泽临": "临", "风地观": "观",
    "火雷噬嗑": "噬嗑", "山火贲": "贲", "山地剥": "剥", "地雷复": "复",
    "天雷无妄": "无妄", "山天大畜": "大畜", "山雷颐": "颐", "泽风大过": "大过",
    "坎为水": "坎", "离为火": "离", "泽山咸": "咸", "雷风恒": "恒",
    "天山遁": "遁", "雷天大壮": "大壮", "火地晋": "晋", "地火明夷": "明夷",
    "风火家人": "家人", "火泽睽": "睽", "水山蹇": "蹇", "雷水解": "解",
    "山泽损": "损", "风雷益": "益", "泽天夬": "夬", "天风姤": "姤",
    "泽地萃": "萃", "地风升": "升", "泽水困": "困", "水风井": "井",
    "泽火革": "革", "火风鼎": "鼎", "震为雷": "震", "艮为山": "艮",
    "风山渐": "渐", "雷泽归妹": "归妹", "雷火丰": "丰", "火山旅": "旅",
    "巽为风": "巽", "兑为泽": "兑", "风水涣": "涣", "水泽节": "节",
    "风泽中孚": "中孚", "雷山小过": "小过", "水火既济": "既济", "火水未济": "未济",
}


def _short(name: str) -> str:
    return _FULL_TO_SHORT.get(name, name)


#: 旺时区间抽取（2026-10-24 第三轮审计新增）
#:
#: 原典对「旺时/及时/得时」的措辞**每卦不同**，共 7 类句式：
#:   ① 「生于A月以后B月以前者，得时也」   （乾）
#:   ② 「自A月至B月得时」                  （屯）
#:   ③ 「生于A…月为及时」                  （豫/颐/丰/益/恒/大壮/小过/离/解）
#:   ④ 「生于M月及A…月得时」               （震/归妹）
#:   ⑤ 「若A月至B月生者及时」              （复）
#:   ⑥ 「宜生于A月已后，B月以前及时」      （噬嗑）
#:   ⑦ 「在冬则及时」                      （渐）
#:
#: ⚠ 2026-10-24 修（此前**恒假分支**）：原实现只有一条正则
#:   `生于A月以后B月以前[^\n，。]*得时`，
#:   而①的原文「生于二月以后八月以前者，得时也」中间被「，」截断 → **0 命中**；
#:   其余 6 类措辞根本不认 ⇒ 「旺时」这一原典判据在 64 卦上**从未生效**。
#:   后果：原文明写「生于二月至八月得时」的卦（屯/复/解/益/丰/恒/大壮/小过/豫…），
#:   生在旺时却因「卦气月≠生月 + 纳甲未中」被判「不叶（凶象）」—— 方向反了，
#:   且 evidence 无任何痕迹。
#:
#: **只实现原典明写的区间**，逐条对照原文；拿不准的不实现（见 _WANGSHI_SKIPPED）。
#: 「失时」段落**不反向实现** —— 原典失时区间与及时区间未必互补
#: （如益卦「又二月至八月生者，福力重，余月非时」措辞不同），不据推测补全。
_WANGSHI_PATTERNS: tuple[tuple[str, str], ...] = (
    # ① 乾：生于二月以后八月以前者，得时也
    #   ⚠ 中间有「，」⇒ 不可用 [^，。]*（那正是旧实现恒不命中的原因）。
    #   改为「者，得时」定界：只跨到「得时」二字为止。
    ("生于([正二三四五六七八九十冬腊]+)月以后([正二三四五六七八九十冬腊]+)月以前[^。]{0,12}?得时", "A-B"),
    # ② 屯：自二月至八月得时
    ("自([正二三四五六七八九十冬腊]+)月至([正二三四五六七八九十冬腊]+)月[^，。]*得时", "A-B"),
    # ⑤ 复：若二月至八月生者及时
    ("若([正二三四五六七八九十冬腊]+)月至([正二三四五六七八九十冬腊]+)月生者及[时時]", "A-B"),
    # ⑥ 噬嗑：宜生于二月已后，八月以前及时
    ("生于([正二三四五六七八九十冬腊]+)月已后，([正二三四五六七八九十冬腊]+)月以前及[时時]", "A-B"),
    # ③ 豫：生于二三四五六七八月为及时 / 颐：又二月至七月生者及时
    ("(?:生于|又)([正二三四五六七八九十冬腊]+)月至([正二三四五六七八九十冬腊]+)月生?者?及[时時]", "A-B"),
    # ③ 丰：又二月生至八月为及时
    ("又([正二三四五六七八九十冬腊]+)月生至([正二三四五六七八九十冬腊]+)月为及[时時]", "A-B"),
    # ③ 恒：又二三四五六七八月生为及时
    ("又([正二三四五六七八九十冬腊]+)月生为及[时時]", "LIST"),
    # ③ 大壮：又四五六七八月生者为及时
    ("又([正二三四五六七八九十冬腊]+)月生者为及[时時]", "LIST"),
    # ③ 小过：又三四五六七八月为及时
    ("又([正二三四五六七八九十冬腊]+)月为及[时時]", "LIST"),
    # ③ 离：如生于四月五月六月为及时（月份连写，无「至/及」）
    ("生于([正二三四五六七八九十冬腊]+)月为及[时時]", "LIST"),
    # ③ 离：如生于四月五月六月为及时 —— 需允许「月」重复（如「四月五月六月为及时」）
    ("生于((?:[正二三四五六七八九十冬腊]+月){2,4})为及[时時]", "LIST2"),
    # ③ 解：又二三四五六七八月为雷雨及时
    ("又([正二三四五六七八九十冬腊]+)月为雷雨及[时時]", "LIST"),
    # ③ 益：又二月至八月生者，福力重（措辞为「福力重」而非「及时」）
    ("又([正二三四五六七八九十冬腊]+)月至([正二三四五六七八九十冬腊]+)月生者，福力重", "A-B"),
    # ③ 随：皆宜生于二月至八月及时也
    ("宜生于([正二三四五六七八九十冬腊]+)月至([正二三四五六七八九十冬腊]+)月及[时時]", "A-B"),
    # ④ 震：如生于十月及二三四五六七八月得时
    ("生于([正二三四五六七八九十冬腊]+)月及([正二三四五六七八九十冬腊]+)月[^，。]*得时", "A+LIST"),
    # ④ 归妹：如生于七月及二三四五六七八月为及时
    ("生于([正二三四五六七八九十冬腊]+)月及([正二三四五六七八九十冬腊]+)月为及[时時]", "A+LIST"),
)

#: 本轮**明确不实现**的旺时措辞（留档，防止后来者以为漏了）
_WANGSHI_SKIPPED: tuple[tuple[str, str], ...] = (
    ("渐", "「在冬则及时」—— 冬为节气区间（亥子丑），非单月；本轮不实现"),
    ("兑", "「生于秋则及时」—— 秋季区间，非单月；本轮不实现"),
    ("履", "「乾兑二体属金，秋正旺」—— 五行旺时，非月份区间"),
    ("夬", "「乾兑二体属金，秋正旺」—— 同上"),
    ("大有", "「春生和气，秋生得时，日生得地」—— 取象三类，非月份区间"),
    ("无妄", "「宜春夏得时，秋冬不利」—— 四季区间"),
)

_CN_MONTH_CHARS = "正一二三四五六七八九十冬腊"


def _expand_months(s: str) -> list[int]:
    """「二三四五六七八」这类连写 → 月份列表；「十一」「十二」按整体识别。"""
    out: list[int] = []
    i = 0
    while i < len(s):
        two = s[i:i + 2]
        if two in ("十一", "十二"):
            out.append(11 if two == "十一" else 12)
            i += 2
            continue
        ch = s[i]
        if ch in _CN_MONTH:
            out.append(_CN_MONTH[ch])
        i += 1
    return out


def _extract_wangshi(gua_lines: list[str]) -> tuple[set[int] | None, str]:
    """从卦头原文抽旺时月份集合。返回 (月份集合 or None, 命中的原文片段)。"""
    text = " ".join(gua_lines)
    for pat, kind in _WANGSHI_PATTERNS:
        m = re.search(pat, text)
        if not m:
            continue
        groups = list(m.groups())
        if kind == "A-B":
            a = _expand_months(groups[0])
            b = _expand_months(groups[1])
            if a and b:
                return set(range(min(a[0], b[0]), max(a[-1], b[-1]) + 1)), m.group(0)
        elif kind == "LIST":
            a = _expand_months(groups[0])
            if a:
                return set(a), m.group(0)
        elif kind == "LIST2":
            # 「四月五月六月」：连写的「X月」序列
            months: list[int] = []
            for seg in re.findall(r"([正二三四五六七八九十冬腊]+)月", groups[0]):
                months.extend(_expand_months(seg))
            if months:
                return set(months), m.group(0)
        elif kind == "A+LIST":
            a = _expand_months(groups[0])
            b = _expand_months(groups[1])
            if a and b:
                return set(a) | set(b), m.group(0)
    return None, ""


def _yao_name(idx: int, line: int) -> str:
    """爻索引+爻性 → 爻名（1=阳 -1=阴）。"""
    pos = ("初", "二", "三", "四", "五", "上")[idx]
    ch = "九" if line == 1 else "六"
    if idx in (0, 5):
        return f"{pos}{ch}"
    return f"{ch}{pos}"


def _pick_liunian_yao_index(entry: dict, entries: list[dict]) -> int | None:
    """取某年流年卦的**行年爻位**（该年小象游变变出的那一爻）。

    原典依据（起例卷之上·小象行年卦气）：流年判词取**小象行年爻**，
    不是「年卦的元堂爻」（= 大运段爻，同段 9 年恒定）—— 那是 §14.33
    修掉的旧错；死断「流年连三年不吉」判的也是流年判词，故同口径。

    取爻优先级（逐级回退，均为**可审计**口径）：
      1. `xingnian_yao_index` —— 该年小象变出之爻（引擎显式落字段，首选）；
      2. `dayun_seg_yuantang_index` —— 大运段元堂爻（旧口径，仅当 1 不可得）；
      3. 与**上一年**流年卦的唯一差异爻（独立复算口径，可自洽验证）。

    返回 None 表示三者皆不可得（调用方须留痕，不得静默代换一个爻）。
    """
    lines = entry.get("lines") or []
    xy = entry.get("xingnian_yao_index")
    if isinstance(xy, int) and 0 <= xy < len(lines):
        return xy
    seg = entry.get("dayun_seg_yuantang_index")
    if isinstance(seg, int) and 0 <= seg < len(lines):
        return seg
    # 回退三：与上一年流年卦的唯一差异爻
    year = entry.get("year")
    for i, e in enumerate(entries):
        if e.get("year") != year:
            continue
        if i == 0:
            break
        prev_lines = entries[i - 1].get("lines") or []
        diffs = [k for k in range(6)
                 if len(lines) > k and len(prev_lines) > k
                 and lines[k] != prev_lines[k]]
        if len(diffs) == 1:
            return diffs[0]
        break
    return None


def build_guajie_from_result(
    result,
    bazi: list[tuple[str, str]] | None = None,
    target_year: int | None = None,
    target_month: int | None = None,
    target_day: int | None = None,
    target_hour: int | None = None,
    liuyue_hexagram: str = "",
    liuyue_yao: str = "",
    huangli_provider: object = None,
) -> dict:
    """
    从 HeluoResult 构建解卦层输出（挂载到 result.guajie）。

    bazi: 中文四柱 [(年干,年支),(月干,月支),(日干,日支),(时干,时支)]，
          缺省时退化为仅命卦判词（无流年解）。
    target_year: 指定解某公历流年（缺省解命卦基础判词）。
    target_month: 流月应期定位（1-12）—— **节气月序**（农历月序，建寅：
                 正月=立春月、七月=立秋月…），**不是公历月**。
                 从该流年 timeline.months 自动取卦。
                 ⚠ 2026-10-24：公历 → (节气月序, 节后日序) 的换算见
                 canonical.resolve_jieqi_window；adapter 层已自动换算，
                 直调本函数者须用**同一口径**（否则取到别的月）。
    target_day: 流日应期定位（1-30）—— **自节起的日序**（1 = 节当日），
             按《河洛理数》日卦定式「每月變五卦每卦管六日」（gua6 口径）
             从流月 days 自动取卦。
             ⚠ 原 docstring 写「每爻管5日」是《河洛真数》L390 的 hou5 旧法，
             生产口径已于 2026-10-22 统一为 gua6。
    liuyue_hexagram/liuyue_yao: 手动指定流月（可选，优先于 target_month）。
    """
    _lunar_anno = None  # H9b 流日黄历标注（命中日段时填充）
    # 目标日缺省回退：结果对象自带**流日取用日**（canonical 记录）——
    #   「流日卦按当前日期自动算」的契约下，调用方不必再重复传一遍三元组，
    #   也不会出现「算的是今天、问的是另一天」的时间轴不自洽。
    #
    # ⚠ 2026-10-24 口径修复：target_date 有**两种口径**（见 HeluoResult.target_date_caliber）：
    #   "solar" = 公历 YYYY-MM-DD → 须先过 resolve_jieqi_window 换成
    #             (节气月序, 自节起的日序) 才能定位流月/流日；
    #   "jieqi" = (年, 节气月序, 节后日序) 的伪日期 → 直接用。
    #   此前**一律按公历拆三段**再当节气月序用 ⇒ 公历 10 月被当成十月（立冬月），
    #   流日取到别的月（真缺陷，实测 target_date=2026-10-23 取到 date_from=2026-11-25）。
    _cal_note = str(getattr(result, "target_date_note", "") or "")
    if target_year is None:
        _cal = str(getattr(result, "target_date_caliber", "") or "")
        _td = str(getattr(result, "target_date", "") or "")[:10]
        if _td:
            try:
                _y, _m, _d = (int(x) for x in _td.split("-"))
            except Exception:
                # 解析失败 → 保持「未指定」，不猜（不静默取今天）
                target_year = None
            else:
                if _cal == "jieqi":
                    # 已是 (年, 节气月序, 节后日序)
                    target_year, target_month, target_day = _y, _m, _d
                else:
                    from .canonical import resolve_jieqi_window as _rjw
                    _w = _rjw(_y, _m, _d)
                    if _w.get("ok"):
                        target_year = _y
                        target_month = int(_w["month"])
                        target_day = int(_w["day"])
                    else:
                        # 换算失败 → 保持「未指定」并留痕（不静默取今天）
                        target_year = None
                        _cal_note = (
                            (_cal_note + " " if _cal_note else "")
                            + f"⚠ 流日取用日 { _td } 无法换算为节气窗口"
                              f"（{_w.get('error') or '未知原因'}），流月/流日未定位"
                        )
    try:
        prenatal = _short(result.prenatal.hexagram_name)
        postnatal = _short(result.postnatal.hexagram_name)
        yuantang_yao = result.yuantang.yuantang
        tian = result.numbers.tian_shu
        di = result.numbers.di_shu

        birth_month = None
        year_ganzhi = ""
        if bazi and len(bazi) >= 2:
            year_ganzhi = bazi[0][0] + bazi[0][1]
            mb = bazi[1][1]
            birth_month = BRANCH_TO_MONTH.get(mb)

        # 性别（起例卷之中 L34/L61「利男子/利女人」、L95「命无阴阳」、
        # L105「利男不利女/利女不利男」四条性判的入参）。
        # 取法与本函数下方参评诗断处一致：result.input.gender 缺省为空串，
        # 空串表示**未给性别**，judge_shu_xiong 会一律不判性别向背，不按默认性别强套。
        _gender = str(getattr(getattr(result, "input", None), "gender", "") or "")

        # 流年（timeline 定位）
        liunian_hex = ""
        liunian_yao_name = ""
        liuyue_hex_name = liuyue_hexagram
        liuyue_yao_name = liuyue_yao
        liuri_hex_name = ""
        liuri_yao_name = ""
        if target_year is not None and result.timeline is not None:
            entries = result.timeline.yearly_hexagrams or []
            for e in entries:
                if e.get("year") == target_year:
                    liunian_hex = _short(e.get("hexagram", ""))
                    # 流年断爻：**小象行年爻** = 该年小象变出的那一爻
                    # （原典起例卷之上·小象行年卦气：「一岁在同人九三（阳）爻；
                    #   二岁取应爻变，同人上九为革上六；三岁复取应爻变，革九三为随六三；
                    #   然后自下而上，四岁变随九四为屯六四……」—— 句中那个爻即行年爻）。
                    # ⚠ 2026-10-24 修正：此前取「年卦的元堂爻」= **大运段爻**，
                    #   同一大运段内 9 年恒同（实测 2024/2025/2026 皆取「上九」），
                    #   而原典要求行年爻**逐年挨次变** —— 故流年判词整层取错爻。
                    #   现优先取 xingnian_yao_index（该年变出之爻）；
                    #   缺失时回退「与上年 diff 唯一差异爻」；再回退本命元堂爻。
                    #   取爻口径统一走 `_pick_liunian_yao_index`（与死断「流年连三年
                    #   不吉」同一函数），杜绝两条路径口径再分叉。
                    cur_lines = e.get("lines") or []
                    _yao_idx = _pick_liunian_yao_index(e, entries)
                    if _yao_idx is not None and len(cur_lines) > _yao_idx:
                        liunian_yao_name = _yao_name(_yao_idx, cur_lines[_yao_idx])
                    if not liunian_yao_name:
                        liunian_yao_name = yuantang_yao
                    # 流月应期：从当年 months 自动定位
                    if target_month and not liuyue_hex_name:
                        for m in (e.get("months") or []):
                            if m.get("month") == target_month:
                                liuyue_hex_name = _short(m.get("name", ""))
                                yi = m.get("yue_yao_index")
                                ml = m.get("lines") or []
                                if yi is not None and len(ml) > yi:
                                    liuyue_yao_name = _yao_name(yi, ml[yi])
                                # 流日应期：当月 days 段自动定位
                                # 2026-10-06：days 已按需化，_build_timeline
                                # 只存廉价定位字段，此处对**命中的这一个月**
                                # 现算完整日段（含卦名/六爻），1,116 个月里
                                # 只付这一次代价。算法口径与预展开完全一致。
                                # 2026-10-22 口径统一：流日为 gua6（一卦管 6 日、
                                # 一爻一日、首日从初爻起），全量与 fast path 一致。
                                if target_day and m.get("days"):
                                    for dseg in materialize_month_days(m):
                                        d_from = dseg.get("day_from", 1)
                                        d_to = dseg.get("day_to", 5)
                                        if d_from <= target_day <= d_to:
                                            # 2026-10-07：起日卦改逐日一爻（原典 L390
                                            # 「挨次而变」+「阳日寻阳位、阴日寻阴位」），
                                            # 段内五日**各有一卦**，段级 name/lines
                                            # 只代表该段首日。故须取 day_items 中
                                            # 目标日那一条；缺失时才退回段级。
                                            item = next(
                                                (it for it in (dseg.get("day_items") or [])
                                                 if it.get("day") == target_day), None)
                                            src = item or dseg
                                            # H9b 河洛×黄历：流日应期段挂黄历标注（注入优先，lunar_python 兜底）
                                            # ⚠ 2026-10-24：取**目标日自身**的时刻，
                                            #   而非段首日 —— 原典 L491「每日添一刻七分天」
                                            #   给出逐日时刻。此前一律用 date_from（段首日），
                                            #   导致：① 黄历标注的是**别的日**的农历日/日柱/宜忌；
                                            #   ② 平台层 DAILY 信号按**段首日**发
                                            #      （canonical_signals 取 liuri_lunar.solar_date）
                                            #   ⇒ 用户问 23 号，信号却落在 20 号。
                                            liuri_solar_date = (
                                                src.get("date") or item.get("date")
                                                or src.get("date_from")
                                                or dseg.get("date_from") or "")
                                            if liuri_solar_date:
                                                try:
                                                    hd = huangli_provider(liuri_solar_date) if callable(huangli_provider) else None
                                                except Exception:
                                                    hd = None
                                                from .heluo_lunar_bridge import annotate_day as _anno
                                                _lunar_anno = _anno(liuri_solar_date, hd) if hd is not None else _anno(liuri_solar_date)
                                            else:
                                                _lunar_anno = None
                                            liuri_hex_name = _short(src.get("name", ""))
                                            dl = src.get("lines") or []
                                            # 2026-10-07：起日卦改**链式累变**（原典 L390
                                            # 「初二日变履九四」明言自前一日卦而变），
                                            # 日卦与月卦相差**不止一爻**，故不能再靠
                                            # 「与月卦 diff 唯一差异爻」反推变爻——
                                            # 直接取原典登记的当日变爻位。
                                            day_yao = src.get("day_yao_index")
                                            if day_yao is None:
                                                diffs = [k for k in range(6)
                                                         if len(dl) > k and len(ml) > k and dl[k] != ml[k]]
                                                day_yao = diffs[0] if len(diffs) == 1 else None
                                            if day_yao is not None and len(dl) > day_yao:
                                                liuri_yao_name = _yao_name(day_yao, dl[day_yao])
                                            # 流时应期：值日卦 hours（起时卦例：前六时进/后六时退）
                                            # ── 流时层 2026-10-06 剥离 ──
                                            # 原典起时卦例（值日卦前六时进数/后六时退数）
                                            # 的推演已整体摘除：当前引擎吃不消该层，
                                            # 且其唯一消费点就是下面这两行。
                                            # compute_liushi 本体**保留在 timeline_yun**。
                                            # 2026-10-22：算法本体已按原典「二法皆通，
                                            # **前法为优**」更正（原实现是两法混用），
                                            # 但**生产链维持剥离** —— 用户裁决「不要算流时卦，
                                            # 到流日就可以」，故此处仍不产出流时。
                                            break
                                break
                    break

        # ⚠ 2026-10-07 审计修：`birth_month or 1` 把漏传静默改成正月，
        # 叶/不叶与 kuozhan 会整体走错分支（实测 kuozhan 由 11 项缩至 8 项）
        # 而 summary 不作任何提示。缺生月就**明确留痕**，仍按 1 兜底以免中断主链。
        _birth_month_missing = not birth_month
        gj = compose_guajie(
            prenatal_name=prenatal, postnatal_name=postnatal,
            yuantang_yao=yuantang_yao,
            birth_month=birth_month or 1, tian_shu=tian, di_shu=di,
            year_ganzhi=year_ganzhi, gender=_gender,
            liunian_hexagram=liunian_hex, liunian_yao=liunian_yao_name,
            liuyue_hexagram=liuyue_hex_name, liuyue_yao=liuyue_yao_name,
            target_year=target_year,
        )
        if _birth_month_missing:
            gj.summary.append("⚠ 未取得出生月，叶/不叶与部分扩展断法按正月兜底，"
                              "相关结论不可尽信（生月缺失已影响判定）")
            gj.evidence.append("  生月：调用方未传 birth_month，已按正月(1)兜底——"
                               "叶/不叶、kuozhan 相关项结果随之改变", dim="PROCESS")

        # ⚠ 2026-10-24 显式化：流日**日历口径**异常时的留痕
        #   （如节气表不可用而退回公历月日口径 —— 此时流日取用月/日不可信）。
        #   口径异常若只藏在代码里，等于「用错口径的结果被当成正常结果交付」。
        if _cal_note:
            gj.summary.insert(0, _cal_note)
            gj.evidence.append("  流日口径：" + _cal_note.lstrip("⚠ "), dim="PROCESS")

        # ⚠ 2026-10-24 显式化：目标日**超出「五卦×六日 = 30 日」的卦月模型**。
        #   节气月实测 29–32 日（1900–2100：31 日 923 个、32 日 225 个），
        #   故每年约 8 天的日序 > 30 —— 原典的卦月只有 30 日
        #   （K3-447 L1154「日卦者每月變五卦每卦管六日方成一月」），
        #   超出部分**无卦可取**。引擎按时间把它归入**末段**
        #   （实测末段时间范围确实覆盖该月最后一日），但这属于**模型外延用**，
        #   必须说明，否则「第 31 日」与「第 30 日」返回同一卦会被当成正常。
        if target_day and int(target_day) > 30:
            _of = (
                f"⚠ 目标日为该节气月第 {int(target_day)} 日，超出「五卦×六日 = 30 日」"
                f"的卦月模型（原典 K3-447 L1154），已按时间归入本月末段"
                f"（该段覆盖该月最后一日），流日结果与第 30 日同段"
            )
            gj.summary.insert(0, _of)
            gj.evidence.append("  流日：" + _of.lstrip("⚠ "), dim="PROCESS")

        # ⚠ 2026-10-24 显式化：目标年**不在流年序列**时（超出一轮大运覆盖），
        #   流年卦与流年判词为空 —— 平台层会因此**不产出该年信号**。
        #   此前只有 evidence 里一句「timeline 无 YYYY 年流年卦」，
        #   summary/用户侧看不见 ⇒ 等于静默缺失。
        #   大运口径本身**不改**（《河洛理数·卷之四》只走一轮：
        #   先天卦 6 段 + 后天卦 6 段，覆盖到 ~75 岁视阴阳爻组合而定），
        #   这里只把「为什么没有」说清楚。
        if target_year is not None and not liunian_hex:
            _why = (f"目标年 {target_year} 不在本命大运覆盖内"
                    f"（大运按《河洛理数·卷之四》只走一轮：先天6段+后天6段），"
                    f"故该年无流年卦/流年判词，该年相关信号不产出")
            gj.summary.insert(0, "⚠ " + _why)
            gj.evidence.append("  流年：" + _why, dim="PROCESS")

        # ── 三阳奇偶合象（L99 / L714 平行印证）────────────────────
        # 该条按节气窗口「冬至后至雨水前」判，**必须有出生公历日**。
        # compose_guajie 只有 birth_month，故在此处补判——
        # build_guajie_from_result 是全链路唯一握有 result.input.birth_date 的地方。
        try:
            from .yue_ling_shu_ge import judge_chun_qi_qi_ou as _jq
            _bd = str(getattr(getattr(result, "input", None), "birth_date", "") or "")
            _cq_note, _cq_ok = _jq(tian, _bd)
            if gj.shu_xiong is not None:
                gj.shu_xiong.chun_qi_qi_ou = (_cq_note, _cq_ok)
            if _cq_ok is not None:
                gj.evidence.append(f"  三阳奇偶合象（L99/L714）：{_cq_note}", dim="TIMELINE.05")
        except Exception as _e:            # 该条不阻塞主链
            gj.evidence.append(f"  三阳奇偶合象：计算跳过（{_e}）", dim="PROCESS")

        # 流日判词（应期定位，独立查询不并入综合判词）
        if liuri_hex_name and liuri_yao_name:
            gj.liuri_hexagram = liuri_hex_name
            gj.liuri_yao = query_yao_duan(liuri_hex_name, liuri_yao_name)
            gj.evidence.append(
                f"流日定位：{liuri_hex_name}{liuri_yao_name}"
                f"（原典起日卦例·**逐日一爻**，段内五日各变一次；本行为第{target_day}日）",
                dim="TIMELINE.04")
        # 流时层已剥离（2026-10-06）：起时卦例的推演整段摘除。
        # 若调用方仍传 target_hour，**明确留痕**而不是静默忽略——
        # 静默忽略会让调用方以为该层已生效，正是本轮反复清理的那类缺陷。
        if target_hour is not None:
            gj.evidence.append(
                f"  流时：已剥离，不产出（传入 target_hour={target_hour} 被忽略；"
                f"原典起时卦例层待引擎能力就绪后恢复）", dim="PROCESS")

        # 出生年占位留痕（2026-10-22）：调用方既未传 birth_year、也未传
        # birth_date 时，引擎用 1984（甲子年）作占位推流年 —— 与真实出生年
        # 不同余 60 时，**流年干支整体错位一年**，流年/流月/流日判词随之全错。
        # 缺失输入被当成真实输入，比答错更坏，故在此明确留痕。
        if getattr(result, "birth_year_source", "") == "placeholder":
            gj.evidence.append(
                "  出生年：占位推流年（未传 birth_year 且无 birth_date，"
                "引擎以 1984 甲子年占位）——流年干支与真实出生年可能错位，"
                "流年/流月/流日判词请谨慎采信；请补传 birth_year 或 birth_date",
                dim="PROCESS")

        # 历法口径自检留痕（2026-10-22）：把**输入四柱**与 sxtwl 自算四柱
        # （1582 年前 = 儒略历）比对。不一致时说明上游的公历换算口径与河洛
        # 节气链不同（如把古农历按 proleptic Gregorian 换算，1150/1206 年差 7 天），
        # 此时日柱/支数/卦/元堂整条链会错。错位输入被当成真实输入，比答错更坏，
        # 故在此明确留痕（详见 calendar_guard 模块）。
        try:
            _cal_notes = check_calendar_consistency(
                getattr(result, "bazi", None),
                getattr(result.input, "birth_date", "") or "")
            gj.evidence.extend(_cal_notes, dim="PROCESS")
        except Exception as _e:            # 该条不阻塞主链
            gj.evidence.append(f"  历法口径自检：跳过（{_e}）", dim="PROCESS")

        # 历法口径自校留痕（2026-10-22）：canonical 已按河洛自己的 sxtwl 节气
        # 口径修正了输入四柱的年/月柱（八字引擎在 1582 年前的节边界差 7 天）。
        # 这里把「改了什么、为什么」摆到台面上，避免下游误以为输入四柱原样生效。
        for _note in (getattr(result, "bazi_caliber_notes", None) or []):
            gj.evidence.append(_note, dim="PROCESS")

        # ── 生时化工（四正节卦，起例卷之下·节候卦爻） ────────────────
        try:
            bd = getattr(result.input, "birth_date", "") or ""
            if bd:
                jh = judge_jiehua_gong(bd)
                gj.jiehua_gong = jh
                gj.evidence.extend((f"  节候卦化工：{e}" for e in jh), dim="TIMELINE.05")
                if jh and "化工" in jh[0]:
                    gj.summary.append(jh[0])
        except Exception as _e:
            gj.evidence.append(f"  节候卦化工：跳过（{_e}）", dim="PROCESS")

        # ── 互体纳音元气（起例卷之上：互体有兑亦是纳音元气） ─────────
        try:
            if bazi and len(bazi) >= 1:
                hn = judge_nayin_huti(bazi[0][0], bazi[0][1], prenatal, postnatal)
                if hn:
                    gj.nayin_yuanqi.extend(hn)
                    gj.evidence.extend((f"  互体纳音：{e}" for e in hn), dim="HEALTH.01")
        except Exception as _e:
            gj.evidence.append(f"  互体纳音：跳过（{_e}）", dim="PROCESS")

        # ── 死断诸法（起例卷之下·后天详说） ─────────────────────────
        try:
            si = _collect_si_duan(
                result=result, prenatal=prenatal, postnatal=postnatal,
                bazi=bazi, target_year=target_year,
                shu_xiong=gj.shu_xiong.shu_xiong if gj.shu_xiong else False,
                year_ganzhi=year_ganzhi,
            )
            gj.si_duan = si
            gj.evidence.extend((f"  死断：{w}" for w in si), dim="LIFESPAN.03")
            # summary 走改写表述，不放原典硬断原句。
            # 原句仍在 si_duan / evidence 中完整留档可回溯，但直出到
            # summary 就会被下游 LLM 当成结论复述——「到此必死」「定死无疑」
            # 在中文里没有第二种读法。四段式断语自带触发与限定，
            # 这里只取其结构，不取其字面。
            hit_sd = any(k in w for w in si
                         for k in ("必死", "定死", "死断", "寿必不久"))
            if hit_sd and not any("《后天详说》死断条" in s for s in gj.summary):
                gj.summary.append(
                    "《后天详说》死断条：运程行至极位，原典于此立断。"
                    "该断为条件式——原典以「阴骘」（暗中积德，非生辰可推）"
                    "分两支，且同书另有「行到四爻方可断人生死」一说不采五爻，"
                    "两存待考。原句与触发条件见 evidence 中「死断」各条；"
                    "此为术数立断语，不作寿命事实断言。")
        except Exception as _e:  # 死断不阻塞主链
            gj.evidence.append(f"  死断：计算跳过（{_e}）", dim="PROCESS")

        # ── 扩展断法（K3-447卷一：四体八体/福力/五命得卦/余数断/四时五行/数极） ──
        try:
            gj.kuozhan = _build_kuozhan(
                result=result, bazi=bazi, prenatal=prenatal, postnatal=postnatal,
                year_ganzhi=year_ganzhi, tian=tian, di=di,
                tian_reduced=getattr(result.numbers, "tian_reduced", 0),
                di_reduced=getattr(result.numbers, "di_reduced", 0),
                si_duan=gj.si_duan or [],
                target_year=target_year,
            )
            for _k, _v in gj.kuozhan.items():
                if isinstance(_v, list):
                    # 扩展断法含 13 类**不同**机制 ⇒ 逐 key 定维度
                    # （映射表见 dimensions.KUOZHAN_DIM，附各判法的原典出处）。
                    from .dimensions import KUOZHAN_DIM as _KZD
                    _kd = _KZD.get(_k, "PATTERN.01")
                    for _e in _v:
                        gj.evidence.append(f"  {_k}：{_e}", dim=_kd)
        except Exception as _e:  # 扩展断法不阻塞主链
            gj.evidence.append(f"  扩展断法：计算跳过（{_e}）", dim="PROCESS")

        # ── 参评诗断（K3-447卷十·金锁银匙歌起参评例）────────────────
        # 2026-10-06 接入。canping.py 此前有完整的起数算法与逐页转录语料，
        # 但两者从未接起来：起数结果没有回查诗断表，生产链路拿不到任何一条
        # 参评断语。本处把「起数 → 查表 → 按性别取本命层两句」串起来。
        # 起数口径（金锁银匙歌）已在 canping 模块头用原典三例复算校验。
        try:
            from .canping import judge_canping
            if bazi and len(bazi) >= 4:
                yg, yz = bazi[0][0], bazi[0][1]
                dz, hz = bazi[2][1], bazi[3][1]
                _g = str(getattr(getattr(result, "input", None), "gender", "male"))
                cp = judge_canping(dz, hz, yg, yz, "female" if _g == "female" else "male")
                gj.canping = cp
                if cp.get("ok"):
                    gj.evidence.append(
                        f"  参评诗断：金锁银匙歌起数得 {cp['total']}"
                        f"（{cp.get('part_cn') or '—'}，第 {cp.get('page')} 页），"
                        f"{cp['layer']}层："
                        + "／".join(cp.get("lines") or []), dim="PATTERN.02")
                    for _ln in (cp.get("lines") or []):
                        gj.summary.append(f"参评·{cp['layer']}：{_ln}")
                else:
                    gj.evidence.append(f"  参评诗断：{cp.get('note', '起数失败')}", dim="PATTERN.02")
        except Exception as _e:  # 参评不阻塞主链
            gj.evidence.append(f"  参评诗断：计算跳过（{_e}）", dim="PROCESS")


        # H9b 河洛×黄历：流日应期段挂黄历标注（注入优先，lunar_python 兜底）
        if _lunar_anno is not None and gj is not None:
            gj.liuri_lunar = _lunar_anno
            gj.evidence.append(
                f"流日黄历：{_lunar_anno.get('solar_date')} {_lunar_anno.get('lunar')} "
                f"{_lunar_anno.get('day_ganzhi')} {_lunar_anno.get('day_nayin')} "
                f"（source={_lunar_anno.get('source')}）", dim="TIMELINE.04")
        return gj.to_dict()
    except Exception as e:  # 解卦层不阻塞主链（防御性兜底）
        return {"error": f"guajie 构建失败: {e}"}


def _collect_si_duan(
    *,
    result,
    prenatal: str,
    postnatal: str,
    bazi: list[tuple[str, str]] | None,
    target_year: int | None,
    shu_xiong: bool,
    year_ganzhi: str,
) -> list[str]:
    """收集死断诸法（后天详说）：大运爻位 + 近3年流年判词 + 重反支干元气。

    2026-10-06 校订新增：
      - recent_dayun_yao：原典「连三爻不吉」主语是大运所历之**爻**，
        由已行大运段的 (hexagram, line_index) 反查爻辞得出，
        不再借用近三年流年判词顶替。
    """
    if not bazi or len(bazi) < 1:
        return []
    year_stem, year_branch = bazi[0][0], bazi[0][1]
    tian = STEM_TO_TRIGRAM.get(year_stem, "")
    tian_fan = QIANXI_DUKONG.get(tian, "")
    di = BRANCH_TO_TRIGRAM.get(year_branch, "")
    di_fan = QIANXI_DUKONG.get(di, "")

    # 当前大运爻位（qi_phase.dayun：age_start..age_end → line_index）
    dayun_line_index: int | None = None
    dayun_phase: str = ""
    qi = (result.timeline.qi_phase if result.timeline else None) or {}
    dayun_entries = qi.get("dayun") or []
    age_now: int | None = None
    if target_year is not None and result.timeline is not None:
        for e in (result.timeline.yearly_hexagrams or []):
            if e.get("year") == target_year:
                age_now = e.get("age")
                break
    if age_now is not None:
        for de in dayun_entries:
            if de.get("age_start") and de.get("age_end") and de["age_start"] <= age_now <= de["age_end"]:
                dayun_line_index = de.get("line_index")
                dayun_phase = de.get("phase", "") or ""
                break

    # 近3年流年判词（target_year-2 .. target_year）
    recent: list[dict] = []
    if target_year is not None and result.timeline is not None:
        entries = result.timeline.yearly_hexagrams or []
        for e in entries:
            y = e.get("year")
            if y is not None and target_year - 2 <= y <= target_year:
                hx = _short(e.get("hexagram", ""))
                cur_lines = e.get("lines") or []
                # ⚠ 2026-10-24 修正（经原著逐字核实）：此处原取
                #   `e.get("yuantang_index")` = **大运段元堂爻位**（同段 9 年恒定）。
                #
                #   原典依据（起例卷之上 L369，三源逐字一致）：
                #     「大象虽佳，（即所得阳爻九年，阴爻六年是也。）
                #       **不若流年佳。（即小象行年爻也。）**
                #       流年若佳，未有不应之者。若流年多凶，大象身爻虽佳，亦奚以为。」
                #   → 原典**自注**「流年」即「小象行年爻」，故「流年」层面
                #     的吉凶判断，其取爻唯一确定 = 行年爻。
                #   另见 L783「流年爻辞吉凶有未交生，虚当岁数，即见祸福者……」
                #     （流年判到**爻辞**层）、L486「如遇本身卦爻理体不吉，
                #     便可以死断之」（死断的爻层判据）。
                #
                #   死断原句（起例卷之下·后天详说 L1555，四库全书本同）：
                #     「若流年连三年不吉，卦爻又不吉，本身卦不佳，
                #       重反支干元气，便可以死断之。」
                #   → 「流年连三年不吉」的主语是**流年**，取流年判词即取行年爻。
                #
                #   旧口径的病根是**量纲错配**：大运段元堂爻位属**大运卦**
                #   （该段所临之卦），与流年卦是两个不同的卦；
                #   把大运卦的爻位号套到流年卦上取爻，原典无此配法。
                yao_idx = _pick_liunian_yao_index(e, entries)
                yao_name = ""
                if yao_idx is not None and len(cur_lines) > yao_idx:
                    yao_name = _yao_name(yao_idx, cur_lines[yao_idx])
                d = query_yao_duan(hx, yao_name) if yao_name else None
                recent.append({
                    "year": y, "hexagram": hx, "yao": yao_name,
                    "ci": (d.ci if d else ""), "buye": (d.buye if d else ""),
                    "suiyun": (d.suiyun if d else ""),
                })
        recent.sort(key=lambda r: r["year"])

    # 已行大运所历之爻（截至当前段，含当前）。原典「连三爻不吉」主语在此，
    # 旧实现误用 recent_years（近三年流年）——口径不同，已在判据层更正。
    dayun_yao: list[dict] = []
    if age_now is not None:
        for de in dayun_entries:
            ls, le = de.get("age_start"), de.get("age_end")
            if not (ls and le) or ls > age_now:
                continue
            li = de.get("line_index")
            hx = _short(de.get("hexagram", ""))
            lines = de.get("lines") or _gua_to_lines(hx) or []
            yao_name = _yao_name(li, lines[li]) if (li is not None and len(lines) > li) else ""
            d = query_yao_duan(hx, yao_name) if (hx and yao_name) else None
            dayun_yao.append({
                "hexagram": hx, "yao": yao_name, "line_index": li,
                "age_start": ls, "age_end": le,
                "phase": de.get("phase", ""),
                "ci": (d.ci if d else ""), "buye": (d.buye if d else ""),
                "suiyun": (d.suiyun if d else ""),
            })

    return judge_si_duan(
        prenatal_name=prenatal, postnatal_name=postnatal,
        tian_yuan_fan=tian_fan, di_yuan_fan=di_fan,
        shu_xiong=shu_xiong,
        dayun_line_index=dayun_line_index,
        dayun_phase=dayun_phase,
        recent_years=recent or None,
        recent_dayun_yao=dayun_yao or None,
    )


# ═══════════════════════════════════════════════════════════════════
# 扩展断法（K3-447《河洛理数》卷一·原著优先 2026-09-12）
#   ① 四体八体/伏体  ② 五命得卦  ③ 数极京城山林
#   ④ 论所得卦数吉凶（余数断）  ⑤ 月令非时论·四时五行盛衰
# 原文出处：卷一 p117-119（四时）p129-130（余数断）p135-137（五命得卦）
#           p128-130（应时合用·福力）p140（四体八体）p154-156（数极京城山林）
# 断语库：heluo_engine/data/kuozhan_duanyu.json（原文直录）
# ═══════════════════════════════════════════════════════════════════

_KUOZHAN_DATA: Optional[dict] = None


def _load_kuozhan() -> dict:
    """加载扩展断语库（首次调用缓存）。"""
    global _KUOZHAN_DATA
    if _KUOZHAN_DATA is None:
        _KUOZHAN_DATA = json.loads(
            _pkg_data("kuozhan_duanyu.json").read_text(encoding="utf-8"))
    return _KUOZHAN_DATA


# 五命五行（卷一·五命得卦："金庚辛申酉…"）：年干优先、年支兜底
_WUMING_STEMS = {"庚": "金", "辛": "金", "甲": "木", "乙": "木", "壬": "水", "癸": "水",
                 "丙": "火", "丁": "火", "戊": "土", "己": "土"}
_WUMING_BRANCHES = {"申": "金", "酉": "金", "寅": "木", "卯": "木", "亥": "水", "子": "水",
                    "巳": "火", "午": "火", "辰": "土", "戌": "土", "丑": "土", "未": "土"}

# 三画卦 → 六爻（初→上，1阳0阴）
_TRI_LINES = {"乾": [1, 1, 1], "兑": [1, 1, 0], "离": [1, 0, 1], "震": [1, 0, 0],
              "巽": [0, 1, 1], "坎": [0, 1, 0], "艮": [0, 0, 1], "坤": [0, 0, 0]}

# 三爻串 → 卦名
_TRI_NAME = {"111": "乾", "110": "兑", "101": "离", "100": "震",
             "011": "巽", "010": "坎", "001": "艮", "000": "坤"}


def _wuming_element(year_gan: str, year_zhi: str) -> str:
    """五命五行（年干优先，年支兜底）。"""
    return _WUMING_STEMS.get(year_gan, "") or _WUMING_BRANCHES.get(year_zhi, "")


def _gua_to_lines(gua_name: str) -> Optional[list[int]]:
    """卦名 → 六爻阴阳（初→上）。纯卦/复卦均按 COMPOUND_GUA 分解；无效卦名返回 None。"""
    up, low = COMPOUND_GUA.get(gua_name, ("", ""))
    if not up or not low:
        return None
    return _TRI_LINES.get(low, [0, 0, 0]) + _TRI_LINES.get(up, [0, 0, 0])


def _lines_to_gua(lines: list[int]) -> str:
    """六爻阴阳 → 卦名（反查 64 卦表；找不到返回空串）。"""
    up = _TRI_NAME.get("".join("1" if x == 1 else "0" for x in lines[3:6]), "")
    low = _TRI_NAME.get("".join("1" if x == 1 else "0" for x in lines[0:3]), "")
    for name, (u, l) in COMPOUND_GUA.items():
        if u == up and l == low:
            return name
    return ""


def compute_siti_bati(prenatal_name: str, postnatal_name: str) -> dict:
    """四体八体（卷一·论互体四体八体）：正体+伏体+互体+变体 = 8 个三画卦。

    原典（渐卦例）："艮有伏震，巽有伏兑"（伏体=错卦）；
    "九五六四九三互离，六四九三六二互坎"（互体，合之为未济）；
    变体=后天卦上下。八体存焉。
    """
    up, low = COMPOUND_GUA.get(prenatal_name, ("", ""))
    post_up, post_low = COMPOUND_GUA.get(postnatal_name, ("", ""))
    six = _gua_to_lines(prenatal_name)
    hu_up, hu_low = ("", "")
    if six is not None:
        hu_up, hu_low = compute_huti(six)
    return {
        "zheng_ti": {"upper": up, "lower": low},
        "fu_ti": {"upper": QIANXI_DUKONG.get(up, ""), "lower": QIANXI_DUKONG.get(low, "")},
        "hu_ti": {"upper": hu_up, "lower": hu_low},
        "bian_ti": {"upper": post_up, "lower": post_low},
    }


def judge_fu_li(prenatal_name: str) -> list[str]:
    """福力层次（卷一·论应其时合其用）：本体为最，互体福、反体安、对体余福。

    原文："互体若有，亦受兄弟子孙之福者也。反体若有，亦遭变故而得安宁者也。
           对体若有，虽死而有余福者也。皆不若本体有之为妙耳"
    反体=反对（综卦，六爻倒置）；对体=正对（错卦，六爻全变）。
    """
    data = _load_kuozhan()["fu_li"]
    out = [f"本体（{prenatal_name}）：{data['benti']}"]
    six = _gua_to_lines(prenatal_name)
    if six is None:
        return out
    hu_up, hu_low = compute_huti(six)
    if hu_up and hu_low:
        out.append(f"互体（{hu_up}上/ {hu_low}下）：{data['huti']}")
    fan = _lines_to_gua(list(reversed(six)))
    if fan:
        out.append(f"反体（{fan}）：{data['fanti']}")
    dui = _lines_to_gua([1 - x for x in six])
    if dui:
        out.append(f"对体（{dui}）：{data['duiti']}")
    return out


def judge_wuming_de_gua(year_ganzhi: str, prenatal_name: str) -> list[str]:
    """五命得卦（卷一·五命得卦）：命主五行（年干优先）× 先天卦上下卦 → 断语。

    原文："金庚辛申酉…"五命各配八卦断语（40 条）；得卦=先天卦上下卦各查。
    """
    if not year_ganzhi or len(year_ganzhi) != 2:
        return []
    wm = _wuming_element(year_ganzhi[0], year_ganzhi[1])
    if not wm:
        return []
    data = _load_kuozhan()["wuming_de_gua"].get(wm, {})
    up, low = COMPOUND_GUA.get(prenatal_name, ("", ""))
    out = [f"五命得卦：{wm}命（{year_ganzhi}年），得先天{prenatal_name}"]
    if up in data:
        out.append(f"  上卦得{up}：{data[up]}")
    if low in data:
        out.append(f"  下卦得{low}：{data[low]}")
    return out


def judge_shu_ji(si_duan: list[str]) -> list[str]:
    """数极京城山林（卷一·详说伏体要旨）：数足（君爻/上极）触发时提示两分。

    原文："数极有京城有山林，京城者福，山林者苦，京城减寿，山林崇高"
    京城/山林判据原典未明载 → 标注级，随死断触发提示，不作硬断。
    """
    data = _load_kuozhan()["shuji"]
    if not any(("君爻" in w or "上极" in w or "数足" in w) for w in si_duan):
        return []
    return [f"{data['label']}：{data['jingcheng']}；{data['shanlin']}（{data['note']}）"]


def judge_suoshu_ji_xiong(
    tian_shu: int, di_shu: int,
    tian_reduced: int, di_reduced: int,
    half_year: str,
) -> list[str]:
    """论所得卦数吉凶（卷一 p129-130）：余数 1-9 按卦断。

    原文："自冬至以后雨水前至三阳开泰之时，除天数二十五之外有奇数之余，
            即君子之合象也；如是偶数是舍君子从小人…有二四者轻六八者重"
          "自夏至以后处暑以前三阴渐长之时，除地数三十之外得阳零数者…
            但九七者轻一三者重"
    冬半年（阳令）：天数>25 才论（奇数吉/偶数凶，2坤4巽轻 6乾8艮重）
    夏半年（阴令）：地数>30 才论（1坎3震重 7兑9离轻；2/4/6/8 原文未载轻重）
    half_year: 'winter'/'summer'（以节气月令近似：子丑寅卯辰巳=冬半年）
    """
    data = _load_kuozhan()["suoshu_ji_xiong"]
    out: list[str] = []
    if half_year == "winter" and tian_shu > 25:
        r = tian_reduced
        phase = "冬半年（阳令）：天数除25之外"
        if r <= 0 or r > 9:
            return out
        if r % 2 == 1:
            out.append(f"{phase}余{r}为奇数——君子之合象（吉），得时顺节则妙")
            return out
        item = data.get(str(r))
        if item:
            w = item.get("winter_weight") or "未载"
            out.append(f"{phase}余{r}={item['gua']}卦（{w}）：{item['duan']}")
    elif half_year == "summer" and di_shu > 30:
        r = di_reduced
        phase = "夏半年（阴令）：地数除30之外"
        if r <= 0 or r > 9:
            return out
        item = data.get(str(r))
        if item:
            w = item.get("summer_weight") or "未载"
            out.append(f"{phase}余{r}={item['gua']}卦（{w}）：{item['duan']}")
    return out


# 生月支 → 季（卷一·月令非时论：寅卯辰春/巳午未夏/申酉戌秋/亥子丑冬）
#
# 口径定性（2026-10-22 原典取证后改标）：**「依原典月令分季推衍」**，
# 不再标注为「引擎自定」。原典**没有**把这张表写成一句，但引文链可逐环回查：
#   ① 《起例卷之中》「阴阳二数随月令消息论」把十二**节气月**排成四个「三月」块，
#      冠以春/夏/秋/冬，各块首月的节令为立春正月、立夏四月、立秋七月、立冬十月
#      （起例卷之中 L8/L17/L22/L27；「自正月立春后」见 L36）。
#   ② 《起例卷之上》L189「坤艮卦主四季**辰戌丑未**月，除正节气十二日外，各旺十八日」
#      → 辰戌丑未为季月；L32「土旺于辰戌丑未月十八日」同义。
#   ③ 《易卦释义·下经卷之下》L416「艮乃**丑寅**之分，**季冬孟春**之间」
#      → 丑＝季冬、寅＝孟春；《起例卷之中》L12「**仲春**之月，气象暄和」（二月＝仲春）。
#   ④ 由②③的季界固定在辰/巳/未/申/戌/亥六支 ⇒ 寅卯辰春、巳午未夏、申酉戌秋、亥子丑冬。
#
# ⚠ **不得与另两套节气锚定口径混用**（原典把它们当三个不同概念）：
#   - 生月化工（起例卷之上 L185-L189）：震木＝**春分后～芒种**、离火＝夏至后～白露、
#     兑金＝秋分后～大雪、坎水＝冬至后～惊蛰、坤艮＝四季辰戌丑未月 —— 以节气中段起算；
#   - 八卦旺废图（起例卷之上 L233）：旺卦随八节更替（立春艮/春分震/立夏巽/夏至离…）。
#   故在季初、季末两支上，本表与「化工/旺废」口径**并不一致**，各自独立使用。
_SEASON_BY_BRANCH = {"寅": "春", "卯": "春", "辰": "春", "巳": "夏", "午": "夏", "未": "夏",
                     "申": "秋", "酉": "秋", "戌": "秋", "亥": "冬", "子": "冬", "丑": "冬"}

# 月支 → 阴阳令（冬至后-夏至前=冬半年阳令；夏至后-冬至前=夏半年阴令）
# 注意：仅作 bazi 缺失时的兜底近似；正式判定用 _solar_phase（节气精确）
_HALF_YEAR_BY_BRANCH = {"子": "winter", "丑": "winter", "寅": "winter", "卯": "winter",
                        "辰": "winter", "巳": "winter", "午": "summer", "未": "summer",
                        "申": "summer", "酉": "summer", "戌": "summer", "亥": "summer"}


def _solar_phase(birth_date: str) -> str:
    """出生公历日期 → 精确半年相（与 canonical._solar_phase_for_date 同逻辑）。

    winter: 冬至后至夏至前（阳令，看天数余）  summer: 夏至后至冬至前（阴令，看地数余）
    修正月支近似在午月初（夏至前）/子月初（冬至前）的节气误差。
    """
    from datetime import date as _date
    from datetime import timedelta
    try:
        import sxtwl
    except ImportError:
        return ""
    try:
        y, m, d = (int(x) for x in birth_date.split("-")[:3])
    except (ValueError, AttributeError):
        return ""
    bd = _date(y, m, d)

    def _find_jie(year: int, month: int, jq: int) -> _date:
        # 批次 L：原为逐日扫整月调 sxtwl.fromSolar（一次 ~92 次），且 guajie.py
        # 有一份**逐字相同**的拷贝 —— 两处合计 184 次做同一件事。
        # 改用 jiehhou.solar_term_date（走 getJieQiByYear 的按年缓存）。
        # 等价性已实测：1900–2100 逐年 201 组与逐日扫描**零不一致**。
        d = solar_term_date(year, jq)
        if d is not None and d.month == month:
            return d
        return _date(year, month, 1)

    try:
        dongzhi_prev = _find_jie(y - 1, 12, 0)   # 冬至 jq=0（上一年）
        dongzhi_cur = _find_jie(y, 12, 0)        # 冬至 jq=0（当年）
        xiazhi_cur = _find_jie(y, 6, 12)         # 夏至 jq=12
        if bd >= dongzhi_cur:
            return "winter"
        if dongzhi_prev <= bd < xiazhi_cur:
            return "winter"
        if xiazhi_cur <= bd < dongzhi_cur:
            return "summer"
    except Exception:
        return ""
    return ""


def judge_yue_ling_fei_shi(
    bazi: list[tuple[str, str]] | None,
    tian_shu: int, di_shu: int,
) -> list[str]:
    """月令非时论·四时五行盛衰（卷一 p117-119）：季 × 命中盛行之五行 → 断语。

    原文（春三月例）："有火盛者则木去生火为子孙昌荣…"以当令之行为主，
    视他行盛衰对当令之行的生克断吉凶；命中盛行=四柱干支五行计数最多者。
    """
    if not bazi or len(bazi) < 2:
        return []
    month_branch = bazi[1][1]
    season = _SEASON_BY_BRANCH.get(month_branch, "")
    if not season:
        return []
    data = _load_kuozhan()["sishi_wuxing"][season]
    out = [f"月令非时论（{season}三月，月支{month_branch}）：{data['yang_ok']}；{data['yin_ok']}",
           f"  本命天{tian_shu}/地{di_shu}"]
    counts: dict[str, int] = {}
    for g, z in bazi:
        for ch, e in ((g, _WUMING_STEMS.get(g)), (z, _WUMING_BRANCHES.get(z))):
            if e:
                counts[e] = counts.get(e, 0) + 1
    if not counts:
        out.append("  总纲：得时顺节则妙，逆时背令则无用，又当参诸卦爻以究其吉凶消长之道")
        return out
    sheng = max(counts, key=counts.get)
    wu = data.get("wu", {})
    if sheng in wu:
        out.append(f"  命中{sheng}盛：{wu[sheng]}")
    else:
        out.append(f"  命中{sheng}盛：{sheng}为当时当令（{season}令），不入忌断")
    out.append("  总纲：得时顺节则妙，逆时背令则无用，又当参诸卦爻以究其吉凶消长之道")
    return out



# ═══════════════════════════════════════════════════════════════════
# 解卦层扩充断法·第二轮（2026-09-12 原著优先·K3-447 卷一/河洛真数起例卷之上）
#   ⑦ 六位贵贱升级  ⑧ 贵命十体  ⑨ 贱命十体（贵体取反）
#   ⑩ 吉凶爻辞比例断命  ⑪ 相生为福·得体·得局生气表  ⑫ 运反流年反数反·先天后天元气变迁
# 原文出处：起例卷之上 L198（比例断命）L200（元气有无论/运反数反）L208（六位贵贱）
#           L209-224（贵命贱命十体）L235（得局生气表）L161（得体/相生为福）
# 断语判据均出自原文明文；原文未载判据处一律标注参考级，不自行推导。
# ═══════════════════════════════════════════════════════════════════

# 贵命十体·卦名吉（原文仅列示例："如泰、大有、同人、晋、豫之类是也"）→ 参考级
GUI_MING_EXAMPLE_GUA = {"泰", "大有", "同人", "晋", "豫"}

#: 贵命十体·③辞吉的吉词（**词组**口径）
#: 原典起例卷之上 L212「三辞吉。（卦爻中有**元吉亨利**是也。）」
#: 「元吉」「亨利」是两个完整吉词。⚠ 不可改用单字「元/吉/亨/利」匹配 ——
#: 周易爻辞普遍含「元亨利贞」，单字匹配会让本项几乎恒中（2026-10-22 修正）。
_GUI_JI_CI_GOOD_CHARS = ("元吉", "亨利")

#: 节气月 → 该月的月令卦（十二月卦气表，原典《起例卷之中》L10-L30）
#: 用于贵命十体④「又如正月得泰卦、九月得剥卦」的留痕文案。
_GUA_QI_MONTH_BY_NUM: dict[int, str] = {
    m: v[1] for m, v in GUA_QI_MONTH_TABLE.items()
}

# 得时表（原文："春震木、夏离火、秋兑金、冬坎水"）
_SEASON_DESHI_GUA = {"春": "震", "夏": "离", "秋": "兑", "冬": "坎"}

# 得体表（原文 L161："木人得巽，火人得离，土人得坤艮之类，皆为得体，虽遇凶爻亦无甚害"）
_DETI_BY_WUMING = {"木": {"巽"}, "火": {"离"}, "土": {"坤", "艮"}}

# 得局/生气表（原文 L235："木人得震巽为得局，坎为生气；土人得坤艮离；
#   金人得乾兑艮坤；水人得乾兑坎，皆是"）——火人原文未载 → 标注
_DEJU_SHENGQI = {
    "木": {"得局": {"震", "巽"}, "生气": {"坎"}},
    "土": {"得局": {"坤", "艮", "离"}, "生气": set()},
    "金": {"得局": {"乾", "兑", "艮", "坤"}, "生气": set()},
    "水": {"得局": {"乾", "兑", "坎"}, "生气": set()},
    "火": {"得局": set(), "生气": set()},   # 原文未载火人
}

# 贵命十体·顺时例（原文："正月生人得天数多地数少，九月生人得地数多天数少"）
# 节气月：寅=1（正月）…戌=9（九月）——仅此两例为原文明文，其余月份不判
_GUI_SHUNSHI_MONTHS = {1: ("天多", "地少"), 9: ("地多", "天少")}


def _yao_wei(yuantang_yao: str) -> str:
    """爻名 → 爻位（九三→三，六二→二，初九→初，上九→上）。"""
    if not yuantang_yao:
        return ""
    if len(yuantang_yao) > 1 and yuantang_yao[0] in ("九", "六"):
        return yuantang_yao[1]
    return yuantang_yao[0]


def _yao_yinyang(yuantang_yao: str) -> Optional[int]:
    """爻名 → 阴阳（含"九"=1阳，含"六"=0阴，如初九/六二/九三/上六；无法判定=None）。"""
    if not yuantang_yao:
        return None
    if "九" in yuantang_yao:
        return 1
    if "六" in yuantang_yao:
        return 0
    return None


def judge_liu_wei_gui_jian(yuantang_yao: str) -> list[str]:
    """六位贵贱升级（起例卷之上·六位贵贱 + 元堂断语）。

    原文："初为庶民，二为侯牧，三为公卿节制，四为近侍大臣，五为君位，
           六为天枢，又为宗庙宫庭大内，又为山林八极之外。
           惟五位为佳，二次之，三四又次之，初上又次之"
    定案（2026-09-15）：初=庶民（1632印本/10卷本/中华典藏三源一致，原书通行文字）；
           三=公卿节制（1632最古刻本；通行本"公乡"为"卿"形近误刻）。
           「元士」系易纬乾凿度爻位体系（初元士/二大夫/三三公…），非河洛真数文字，弃用。
    """
    if not yuantang_yao:
        return []
    w = _yao_wei(yuantang_yao)
    pos = {
        "初": "庶民（多从寒微起家）",
        "二": "侯牧（卦佳数足可牧民一方）",
        "三": "公卿节制（掌节制之权，次五二之贵）",
        "四": "近侍大臣（近君侍从之贵）",
        "五": "君位（卦名佳、二数足、化工元气得时 → 贤良上贵）",
        "上": "天枢/宗庙宫庭大内/山林八极之外（贵极为三公，否则闲散卑职）",
    }
    rank = {"五": "惟五位为佳", "二": "二次之", "三": "三四又次之", "四": "三四又次之",
            "初": "初上又次之", "上": "初上又次之"}
    if w not in pos:
        return []
    # ⚠ 2026-10-24 修正：原写「（原典：列贵贱者存乎位…惟五位为佳，二次之，三四又次之，
    #   初上又次之）」—— 末句「初上又次之」是引擎据 1632 刻本补的，**通行本
    #   「六位贵贱」段无此语**（原典止于「惟五位为佳，二次之，三四又次之」）。
    #   把它并进「原典：」标注即自撰冒引。现只留通行本逐字可核的部分，
    #   刻本补充另标出处。
    return [f"六位贵贱：元堂居{yuantang_yao}（{pos[w]}）——{rank[w]}"
            f"（原典：列贵贱者存乎位…惟五位为佳，二次之，三四又次之；"
            f"「初上又次之」据 1632 刻本补）"]


def judge_gui_ming_shi_ti(
    *,
    prenatal_name: str,
    yuantang_yao: str = "",
    yao_cis: list[str] | None = None,      # 先天六爻辞（初→上），判辞吉
    yao_lines: list[int] | None = None,    # 先天六爻序列（1阳0阴），判有援/众宗
    birth_month_branch: str = "",          # 生月支（节气月），判得时/顺时/当位
    gua_qi_month: int | None = None,       # 本卦的卦气月（卦头自述），判「正月得泰卦」那半
    tian_shu: int = 0, di_shu: int = 0,
    year_gan: str = "", year_zhi: str = "",
) -> list[str]:
    """贵命十体（起例卷之上·贵命十体）：

    ①卦名吉（泰大有同人晋豫，参考级）②爻吉（元堂二五）③辞吉（卦爻中有元吉亨利）
    ④得时（春震夏离秋兑冬坎）⑤有援（元堂阳爻应爻阴/阴爻应爻阳）
    ⑥顺时（正月天多地少/九月地多天少，仅原文两例）⑦得体（土命坤艮/火命离/木命巽）
    ⑧当位（阳月元堂阳/阴月元堂阴）⑨合理（金命见坤艮土生金）⑩众宗（一阳五阴/一阴五阳）

    分级（原典）：得三四者选曹命，得五六者如通命，得七八者乡监侍从，
    得九十者将相侯王；兼有元气化工者位极人臣官高一品五福全备。
    """
    if not prenatal_name:
        return []
    out: list[str] = [f"贵命十体（{prenatal_name}命，元堂{yuantang_yao}）："]
    got: list[str] = []
    w = _yao_wei(yuantang_yao)
    yy = _yao_yinyang(yuantang_yao)
    wm = _wuming_element(year_gan, year_zhi)
    up, low = COMPOUND_GUA.get(prenatal_name, ("", ""))
    season = _SEASON_BY_BRANCH.get(birth_month_branch, "")
    mon = BRANCH_TO_MONTH.get(birth_month_branch)

    # ① 卦名吉（**参考级**：原文仅列示例）
    #    原典 L210「一卦名吉。（如泰、大有、同人、晋、豫**之类**是也。）」
    #    ——「之类」= 举例未穷举，故**不在明举例内的卦既不判吉、也不判凶**，
    #    该体不计入十体命中数（见下方留痕）。
    if prenatal_name in GUI_MING_EXAMPLE_GUA:
        got.append("①卦名吉（泰/大有/同人/晋/豫类，参考级）")
    # ② 爻吉（元堂二五）
    if w in ("二", "五"):
        got.append("②爻吉（元堂居二五爻）")
    # ③ 辞吉（卦爻中有元吉亨利）
    #    原典 L212「三辞吉。（卦爻中有**元吉亨利**是也。）」
    #    「元吉」「亨利」是**两个完整吉词**，须按词组命中。
    #    ⚠ 不可用单字「元/吉/亨/利」匹配：实测 64 卦中单字口径命中 **60 卦
    #    （93.8%）** —— 本项几乎恒中，贵为「几乎必中」、贱为「几乎必不中」，
    #    贵贱十体不再对称，分级失去意义。词组口径命中 11 卦（17.2%），
    #    且是单字口径的**子集**（不产生反向差异）。
    if yao_cis and any(any(k in (c or "") for k in _GUI_JI_CI_GOOD_CHARS) for c in yao_cis):
        got.append("③辞吉（卦爻中有元吉亨利）")
    # ④ 得时（春震木、夏离火、秋兑金、冬坎水 ＋ 正月得泰卦、九月得剥卦）
    #    原典 L213「四得时。（如春震木、夏离火、秋兑金、冬坎水之类。
    #      **又如正月得泰卦、九月得剥卦之类皆是。**）」
    #    后半「正月得泰卦」= 生月与该卦的**卦气月**相合，机械可判：
    #    该卦的卦气月取自其卦头自述（gua_qi_month 入参）。
    #    ⚠ 前半的「月份→季节」划分（_SEASON_BY_BRANCH 寅卯辰春…）**依原典月令
    #    分季推衍**（引文链见 _SEASON_BY_BRANCH 上方注释）：原典未把这张表写成
    #    一句，但「辰戌丑未为季月」「丑＝季冬、寅＝孟春」「二月＝仲春」三处
    #    明文可逐环闭合到本表。
    #    注：原典「得时」是**两项并列**（季节卦 + 月份卦气），另由六顺时/七得体/
    #    八当位共同成立 —— 本函数只覆盖季节卦与卦气月两项。
    _deshi_hit = bool(season and _SEASON_DESHI_GUA.get(season) in (up, low))
    _guaqi_hit = bool(mon is not None and gua_qi_month is not None
                      and mon == gua_qi_month)
    if _deshi_hit or _guaqi_hit:
        _why = []
        if _deshi_hit:
            _why.append(f"{season}月得{_SEASON_DESHI_GUA[season]}卦")
        if _guaqi_hit:
            _why.append(f"生月{mon}月=卦气月（{_GUA_QI_MONTH_BY_NUM.get(mon, '')}卦）")
        got.append("④得时（" + "、".join(_why) + "）")
    # ⑤ 有援（元堂阳应阴 / 元堂阴应阳）
    if yy is not None and yao_lines and len(yao_lines) == 6 and w:
        idx = {"初": 0, "二": 1, "三": 2, "四": 3, "五": 4, "上": 5}.get(w)
        if idx is not None:
            ying = yao_lines[(idx + 3) % 6]
            if (yy == 1 and ying == 0) or (yy == 0 and ying == 1):
                got.append("⑤有援（元堂与应爻阴阳相济）")
    # ⑥ 顺时（正月天多地少 / 九月地多天少，原文明文两例）
    if mon in _GUI_SHUNSHI_MONTHS:
        want = _GUI_SHUNSHI_MONTHS[mon]
        ok = (want == ("天多", "地少") and tian_shu > di_shu) or \
             (want == ("地多", "天少") and di_shu > tian_shu)
        if ok:
            got.append(f"⑥顺时（节气月{mon}：{'天多地少' if want[0] == '天多' else '地多天少'}，与时偕行）")
    # ⑦ 得体（土命坤艮/火命离/木命巽）
    if wm in _DETI_BY_WUMING and (_DETI_BY_WUMING[wm] & {up, low}):
        got.append(f"⑦得体（{wm}命得{','.join(sorted(_DETI_BY_WUMING[wm] & {up, low}))}）")
    # ⑧ 当位（阳月元堂阳 / 阴月元堂阴）
    if yy is not None and birth_month_branch:
        hy = _HALF_YEAR_BY_BRANCH.get(birth_month_branch)
        if (hy == "winter" and yy == 1) or (hy == "summer" and yy == 0):
            got.append("⑧当位（阳月元堂阳 / 阴月元堂阴，阴阳得位）")
    # ⑨ 合理（金命见坤艮，土生金助成吉祥）
    if wm == "金" and (up in ("坤", "艮") or low in ("坤", "艮")):
        got.append("⑨合理（金命不得乾兑金卦，本卦见坤艮，土生金亦能助成吉祥）")
    # ⑩ 众宗（一阳五阴 / 一阴五阳）
    if yao_lines and len(yao_lines) == 6 and yy is not None and w:
        idx = {"初": 0, "二": 1, "三": 2, "四": 3, "五": 4, "上": 5}.get(w)
        if idx is not None and yao_lines[idx] == yy:
            total = sum(1 for l in yao_lines if l == 1)
            if (yy == 1 and total == 1) or (yy == 0 and total == 5):
                got.append("⑩众宗（元堂一阳为五阴所宗 / 一阴为众阳所宗）")

    if not got:
        out.append(f"贵命十体（{prenatal_name}命，元堂{yuantang_yao}）：十体均未命中")
        if prenatal_name not in GUI_MING_EXAMPLE_GUA:
            out.append("①卦名不判（不在原文明举例「泰/大有/同人/晋/豫」内；"
                       "原典用「之类」= 举例未穷举，未举例者不判吉亦不判凶）")
        return out
    if prenatal_name not in GUI_MING_EXAMPLE_GUA:
        out.append("①卦名不判（不在原文明举例「泰/大有/同人/晋/豫」内；"
                   "原典用「之类」= 举例未穷举，未举例者不判吉亦不判凶）")
    out.append("；".join(got))
    n = len(got)
    if n <= 2:
        out.append(f"得{n}体：碌碌长流（原典：外此十体，或得一二者，乃一二分之福分也）")
    elif n <= 4:
        out.append(f"得{n}体：选曹命（原典：得三四者选曹命）")
    elif n <= 6:
        out.append(f"得{n}体：如通命（原典：得五六者如通命）")
    elif n <= 8:
        out.append(f"得{n}体：乡监侍从（原典：得七八者乡监侍从）")
    else:
        out.append(f"得{n}体：将相侯王（原典：得九十者将相侯王）；兼有元气化工者位极人臣官高一品五福全备")
    return out


def judge_jian_ming_shi_ti(
    *,
    prenatal_name: str,
    yuantang_yao: str = "",
    yao_cis: list[str] | None = None,
    yao_lines: list[int] | None = None,
    birth_month_branch: str = "",
    gua_qi_month: int | None = None,       # 本卦的卦气月（卦头自述），判④取反
    tian_shu: int = 0, di_shu: int = 0,
    year_gan: str = "", year_zhi: str = "",
) -> list[str]:
    """贱命十体（起例卷之上·贱命十体）：皆与十贵相反。

    原文："贱命十体皆与十贵相反是也……得三四者，僧道九流之命，得五六者吏僧孤独，
           得七八者夭横凶顽，得九十者乞丐斩戮。右十体非夭即横，量轻重可定吉凶"
    判据=贵命十体逐条取反（原文明言"皆与十贵相反"），非另列判据。
    """
    if not prenatal_name:
        return []
    got: list[str] = []
    w = _yao_wei(yuantang_yao)
    yy = _yao_yinyang(yuantang_yao)
    wm = _wuming_element(year_gan, year_zhi)
    up, low = COMPOUND_GUA.get(prenatal_name, ("", ""))
    season = _SEASON_BY_BRANCH.get(birth_month_branch, "")
    mon = BRANCH_TO_MONTH.get(birth_month_branch)

    # ① 卦名：**不判**
    #    ⚠ 2026-10-22 修正：原实现在此产出「①卦名凶（非贵命示例卦，参考级）」。
    #    原典 L210「一卦名吉。（如泰、大有、同人、晋、豫**之类**是也。）」
    #    用「之类」= 举例未穷举，**并未言其余卦为凶**；L221「贱命十体皆与十贵相反」
    #    的「取反」是把**已判**的十贵体取反，而①在未举例之卦上本就未判，
    #    无从取反得凶。
    #    另一条更硬的理由是**对称性**：十体是计分制（L220 分级），贵贱两侧
    #    必须同一把尺子。若贱命侧①对 59/64 卦恒判凶，则贵为 9 项制、贱为 10 项制，
    #    两边的分级不在同一尺度上。故该体**不判、不计入**。
    if w not in ("二", "五"):
        got.append("②爻位凶（元堂不居二五）")
    # ③ 辞凶（卦爻无元吉亨利）—— 词组口径，与贵命十体③同一判据
    if yao_cis and not any(any(k in (c or "") for k in _GUI_JI_CI_GOOD_CHARS) for c in yao_cis):
        got.append("③辞凶（卦爻无元吉亨利）")
    # ④ 不得时（两半取反：季节卦 + 卦气月）
    _deshi_hit = bool(season and _SEASON_DESHI_GUA.get(season) in (up, low))
    _guaqi_hit = bool(mon is not None and gua_qi_month is not None
                      and mon == gua_qi_month)
    if not (_deshi_hit or _guaqi_hit):
        got.append("④不得时（既非季正卦、卦气月亦不合）")
    if yy is not None and yao_lines and len(yao_lines) == 6 and w:
        idx = {"初": 0, "二": 1, "三": 2, "四": 3, "五": 4, "上": 5}.get(w)
        if idx is not None:
            ying = yao_lines[(idx + 3) % 6]
            if not ((yy == 1 and ying == 0) or (yy == 0 and ying == 1)):
                got.append("⑤无援（元堂与应爻阴阳不济）")
    if mon in _GUI_SHUNSHI_MONTHS:
        want = _GUI_SHUNSHI_MONTHS[mon]
        ok = (want == ("天多", "地少") and tian_shu > di_shu) or \
             (want == ("地多", "天少") and di_shu > tian_shu)
        if not ok:
            got.append("⑥数逆时（天地二数与时令相逆）")
    if wm in _DETI_BY_WUMING and not (_DETI_BY_WUMING[wm] & {up, low}):
        got.append(f"⑦不得体（{wm}命不得{','.join(sorted(_DETI_BY_WUMING[wm]))}）")
    if yy is not None and birth_month_branch:
        hy = _HALF_YEAR_BY_BRANCH.get(birth_month_branch)
        if not ((hy == "winter" and yy == 1) or (hy == "summer" and yy == 0)):
            got.append("⑧位不当（阴阳失位）")
    if wm == "金" and not (up in ("坤", "艮") or low in ("坤", "艮")):
        got.append("⑨违时/不合理（金命不见坤艮土生金）")
    if yao_lines and len(yao_lines) == 6 and yy is not None and w:
        idx = {"初": 0, "二": 1, "三": 2, "四": 3, "五": 4, "上": 5}.get(w)
        if idx is not None and yao_lines[idx] == yy:
            total = sum(1 for l in yao_lines if l == 1)
            if not ((yy == 1 and total == 1) or (yy == 0 and total == 5)):
                got.append("⑩众嫉（非一阳五阴/一阴五阳之宗）")

    out = [f"贱命十体（{prenatal_name}命，元堂{yuantang_yao}，贵体取反）："]
    if prenatal_name not in GUI_MING_EXAMPLE_GUA:
        out.append("①卦名不判（不在原文明举例内；原典用「之类」= 举例未穷举，"
                   "未举例者不判吉亦不判凶，故无「卦名凶」可取反）")
    if not got:
        out.append("十贱体均未命中")
        return out
    out.append("；".join(got))
    n = len(got)
    if n <= 2:
        out.append(f"得{n}贱体：量轻重可定吉凶（原典：右十体非夭即横）")
    elif n <= 4:
        out.append(f"得{n}贱体：僧道九流之命（原典：得三四者僧道九流之命）")
    elif n <= 6:
        out.append(f"得{n}贱体：吏僧孤独（原典：得五六者吏僧孤独）")
    elif n <= 8:
        out.append(f"得{n}贱体：夭横凶顽（原典：得七八者夭横凶顽）")
    else:
        out.append(f"得{n}贱体：乞丐斩戮（原典：得九十者乞丐斩戮）；伤时犯忌有凶无吉尤验")
    return out


#: 爻辞**吉**词（爻辞专用，区别于断语的 ``POLARITY_GOOD_WORDS``）
#: 出处：起例卷之上 L198「凶多吉少者…吉多凶少者…」＋ L212「元吉亨利」
#: ⚠ 2026-10-25 提升为模块级：原先是 ``judge_yao_ci_bi_li`` 的函数内局部变量，
#:   导致别处无法复用同一张表 ⇒ 只能另立手抄表（必漂移）。现提升为单一来源。
YAO_CI_GOOD_WORDS: tuple = ("元", "吉", "亨", "利", "贞")

#: 爻辞**凶**词（爻辞专用；"咎" 单独作凶字时须排除"无咎"）
#:
#: ⚠ 2026-10-25 标注：本表**只用于「吉凶爻辞比例断命」**（六爻样本的计数），
#:   **不可**用于「单爻判凶」。理由（见 time_layer_judgment 模块注释）：
#:     · 原典 L222 贱命十体「三辞凶」**只给名目、未给凶词门槛**；
#:     · 爻辞凶语**无固定形态**：「悔亡」是吉语（亡而悔消），
#:       「厉终有悔」是凶语 —— 同一个「悔」字两义，单字词表必然误判。
#:   故**单爻判凶在本包无据** ⇒ 一律不判（宁可不判，不可编判）。
YAO_CI_BAD_WORDS: tuple = ("凶", "厉", "悔", "吝", "危", "死", "灾", "亡")


def judge_yao_ci_bi_li(ci_list: list[str] | None) -> list[str]:
    """吉凶爻辞比例断命（起例卷之上）：

    原文："凶多吉少者，僧道九流之命也。吉多凶少者，浊富之人也。
           有化工之气者，艰难获福……全凶至贫贱夭寿，全吉至富贵高寿，毫厘不爽也"
    判据：爻辞含（元/吉/亨/利/贞）计吉，含（凶/厉/悔/吝/咎/危/死/灾/亡）计凶，
    同含取凶，均不含计平。以本命卦六爻辞为样本。

    ⚠ 此处是**六爻样本的比例**判命（原文即论"凶多吉少/吉多凶少"），
      与「单爻判凶」不是同一件事 —— 见 ``YAO_CI_BAD_WORDS`` 的标注。
    """
    if not ci_list:
        return []
    ji_words = YAO_CI_GOOD_WORDS
    xiong_words = YAO_CI_BAD_WORDS
    ji = xiong = 0
    for c in ci_list:
        text = c or ""
        has_ji = any(k in text for k in ji_words)
        # "咎"仅作凶字需排除"无咎"（无咎=无灾祸，吉辞）
        has_xiong = any(k in text for k in xiong_words) or \
            ("咎" in text and "无咎" not in text)
        if has_xiong:
            xiong += 1
        elif has_ji:
            ji += 1
    total = ji + xiong
    if total == 0:
        return []
    jp, xp = ji / total, xiong / total
    head = f"吉凶爻辞比例（本命卦六爻，吉{ji}/凶{xiong}，共{total}爻）"
    if xiong == 0:
        # ⚠ 2026-10-24 修正：原写「（原典：全吉至富贵高寿，毫厘不爽也）」——
        #   原典实句是「全凶至贫贱夭寿，全吉至富贵高寿，毫厘不爽也」，
        #   「毫厘不爽也」是**全句的收尾**，不属前半。拆用即引文不实。
        #   现各分支只引属于自己那半的原典短句。
        return [f"{head}：全吉 → 富贵高寿（原典：全吉至富贵高寿）"]
    if ji == 0:
        return [f"{head}：全凶 → 贫贱夭寿（原典：全凶至贫贱夭寿）"]
    if xp > jp:
        return [f"{head}：凶多吉少 → 僧道九流之命；有化工之气者艰难获福（原典：凶多吉少者僧道九流之命也）"]
    return [f"{head}：吉多凶少 → 浊富之人（原典：吉多凶少者浊富之人也）"]


def judge_xiang_sheng_wei_fu(
    prenatal_name: str, year_gan: str, year_zhi: str,
) -> list[str]:
    """相生为福·得体·得局生气表（起例卷之上）：

    原文 L161："又如木人得巽，火人得离，土人得坤艮之类，皆为得体，虽遇凶爻亦无甚害"
    原文 L235："木人得震巽为得局，坎为生气；土人得坤艮离；金人得乾兑艮坤；
                水人得乾兑坎，皆是"
    注：火人得局生气原文未载 → 标注；纳音相生为福已由 judge_nayin_yuanqi 覆盖，不重复。
    """
    if not prenatal_name:
        return []
    wm = _wuming_element(year_gan, year_zhi)
    if not wm:
        return []
    up, low = COMPOUND_GUA.get(prenatal_name, ("", ""))
    out: list[str] = [f"相生为福·得体·得局生气（{wm}命，{year_gan}{year_zhi}年，得{prenatal_name}）"]
    got = False
    deti = _DETI_BY_WUMING.get(wm, set())
    hit = deti & {up, low}
    if hit:
        got = True
        out.append(f"  得体：得{','.join(sorted(hit))}，虽遇凶爻亦无甚害（原典：皆为得体）")
    dsq = _DEJU_SHENGQI.get(wm)
    if dsq is not None:
        dju = dsq["得局"] & {up, low}
        sq = dsq["生气"] & {up, low}
        if dju:
            got = True
            # ⚠ 2026-10-24 修正：原写「（原典：{wm}人得…为得局）」—— 这是引擎按
            #   模板拼出的**概括句**（且「为得局」三字非原典措辞），标成原典引文
            #   属自撰冒引。原典实句形如「木人得震巽为得局，坎为生气；
            #   土人得坤艮离；金人得乾兑艮坤；水人得乾兑坎，皆是」——
            #   现按五命分别引该句的**原典实证句**。
            _deju_quote = {
                "木": "木人得震巽为得局",
                "土": "土人得坤艮离",
                "金": "金人得乾兑艮坤",
                "水": "水人得乾兑坎",
            }.get(wm, "")
            _q = f"（原典：{_deju_quote}）" if _deju_quote else \
                ("（原典：木人得震巽为得局，坎为生气；土人得坤艮离；"
                 "金人得乾兑艮坤；水人得乾兑坎，皆是）")
            out.append(f"  得局：得{','.join(sorted(dju))}{_q}")
        if sq:
            got = True
            out.append(f"  生气：得{','.join(sorted(sq))}（原典：坎为生气）")
        if wm == "火" and not got:
            out.append("  火人得局生气原文未载（原典仅列木土金水），不作硬断")
    if not got:
        out.append("  得体/得局/生气均未命中")
    return out


def judge_yun_liunian_shu_fan(
    *,
    yun_fan: bool = False, liunian_fan: bool = False, shu_fan: bool = False,
    dayun_gua: str = "", liunian_gua: str = "", age_now: int | None = None,
) -> list[str]:
    """运反+流年反+数反 → 不可保（起例卷之上·化工元气有无论）：

    原文："如运中有之，虽流年数不吉，不为害。且如流年有之，虽月数不吉，不为害。
           若运既反，流年又反，数又反，其人不可保矣"
    判据：运反/流年反 = 大运卦/流年卦无化工且无元气（_yun_liunian_fan，
    按 L200"卦体中二者俱反"口径）；数反 = 数凶（si_duan 数凶）。
    """
    if not (yun_fan or liunian_fan or shu_fan):
        return []
    gua_info = f"大运卦{dayun_gua or '?'}、流年卦{liunian_gua or '?'}" + \
        (f"（虚岁{age_now}）" if age_now is not None else "")
    out = [f"元气化工组合断：{gua_info}｜运反={yun_fan}，流年反={liunian_fan}，数反={shu_fan}"]
    if yun_fan and liunian_fan and shu_fan:
        out.append("运既反，流年又反，数又反 → 其人不可保矣（原典：化工元气有无论）")
    elif shu_fan and (yun_fan or liunian_fan):
        out.append("数反 + 运反或流年反 → 重，须参元气化工有无消息（原典：运中有之虽流年数不吉不为害）")
    elif liunian_fan:
        out.append("流年反而数不反 → 不为害，若月数不吉亦不为害（原典：流年有之虽月数不吉不为害）")
    else:
        # ⚠ 2026-10-24 修正：原标注把「三者俱反方不可保」写作原典引文 ——
        #   但那是**引擎自撰的概括语**，原典实为
        #   「若运既反，流年又反，数又反，其人不可保矣」（起例卷之上
        #   化工元气有无论）。冒引原典 = 以原典的权威呈现一句并非原典的话，
        #   比不标更坏。现改为标注引擎口径，并把原典实句并列给出（真引文，
        #   逐字可核）。守卫见 tests/heluo/test_heluo_original_quotes.py。
        out.append("仅运反或数反一项，未至不可保（引擎口径；原典："
                   "「若运既反，流年又反，数又反，其人不可保矣」）")
    return out


def judge_xian_tian_hou_tian_yuan_qi(
    *,
    xiantian_yq: bool = False, houtian_yq: bool = False,
) -> list[str]:
    """先天后天元气有无（起例卷之上·化工元气有无论）：

    原文："元气化工二者最重，兼有之，若本数又吉，必功名富贵福寿人也。
           如卦体中二者俱反，必贫穷困苦夭死者也。
           先天若有，后天若无，此先富贵而后贫贱者也。
           先天若无，后天始有，此先贫贱而后富贵者也"
    """
    if xiantian_yq and houtian_yq:
        return ["先天后天元气俱有：二者兼有，若本数又吉，必功名富贵福寿人也（原典：化工元气有无论）"]
    if xiantian_yq and not houtian_yq:
        return ["先天有元气而后天无：先富贵而后贫贱者也（原典：先天若有后天若无）"]
    if not xiantian_yq and houtian_yq:
        return ["先天无元气而后天始有：先贫贱而后富贵者也（原典：先天若无后天始有）"]
    return ["先天后天元气俱无：如卦体中二者俱反，必贫穷困苦夭死者也（原典：化工元气有无论）"]


def _kz_gua_qi_month(gua_name: str) -> int | None:
    """该卦的**卦气月**（卦头自述「卦气属X月」），取不到返回 None。

    用于贵命十体④「又如正月得泰卦、九月得剥卦之类皆是」——
    判据是「生月与该卦的卦气月相合」，故需**本卦自己的**卦气月
    （不是十二月卦气表里那个月的月令卦）。
    """
    try:
        g = load_guajie_data().get(gua_name)
    except Exception:
        return None
    return g.gua_qi_month if g else None


def _kz_yao_cis(gua_name: str) -> list[str]:
    """先天命卦六爻辞（初→上，query_yao_duan 的 ci 字段；缺失补空串）。"""
    lines = _gua_to_lines(gua_name)
    if not lines:
        return []
    out: list[str] = []
    for i, lv in enumerate(lines):
        d = query_yao_duan(gua_name, _yao_name(i, lv))
        out.append(d.ci if d else "")
    return out



# 化工卦集（起例卷之上·化工论 L191：春木(震)夏火(离)秋金(兑)冬水(坎)；
#   L189：坤艮主四季辰戌丑未月。L191 又云"岂必拘于坎而不以震木为化工乎"——
#   卦内含四正化工卦或坤艮即为有化工，不必拘于当令）
_HG_SIGUA = {"震", "离", "兑", "坎", "坤", "艮"}


def _gua_has_huagong(gua_name: str) -> bool:
    """卦含化工（上卦或下卦 ∈ 震离兑坎坤艮）。乾/巽为主的卦无化工。"""
    if not gua_name:
        return False
    up, low = COMPOUND_GUA.get(gua_name, ("", ""))
    return (up in _HG_SIGUA) or (low in _HG_SIGUA)


def _gua_has_yuanqi(gua_name: str, year_gan: str, year_zhi: str) -> bool:
    """卦含元气（原典 L205：元气谓壬甲戌亥及金音人得乾兑之卦是也；
    又 L191/203：卦体生纳音者相生为福，亦算元气）。

    注意：不复用 judge_nayin_yuanqi 的 bool()（其返回列表含基础信息行，
    恒非空），按原文口径独立复算：金音人得乾兑（金体）或卦体五行生纳音。
    """
    if not gua_name or not year_gan or not year_zhi:
        return False
    nayin = get_nayin_element(year_gan, year_zhi)
    if not nayin:
        return False
    gua = COMPOUND_GUA.get(gua_name)
    if not gua:
        return False
    upper, lower = gua
    els = {TRIGRAM_ELEMENT.get(upper, ""), TRIGRAM_ELEMENT.get(lower, "")}
    els.discard("")
    if nayin == "金" and "金" in els:
        return True  # 金音人得乾兑（金体）→ 元气（原典明文）
    for el in els:
        if ELEMENT_GENERATES.get(el) == nayin:
            return True  # 卦体五行生纳音 → 相生为福（原典：彼此相生）
    return False


def _yun_liunian_fan(
    gua_name: str, year_gan: str, year_zhi: str,
) -> tuple[bool, list[str]]:
    """运反/流年反判据（起例卷之上·化工元气有无论 L200 语境）：

    原文："如卦体中二者俱反，必贫穷困苦夭死者也……如运中有之，虽流年数不吉，
           不为害。且如流年有之，虽月数不吉，不为害。
           若运既反，流年又反，数又反，其人不可保矣"
    判据：运/流年卦「无化工（卦不含震离兑坎坤艮）且无元气（L205 纳音口径）」= 反。
    返回 (是否反, 证据列表)；缺卦名/年柱信息时 (False, []) 不硬断。
    """
    if not gua_name or not year_gan or not year_zhi:
        return False, []
    has_hg = _gua_has_huagong(gua_name)
    yq = _gua_has_yuanqi(gua_name, year_gan, year_zhi)
    ev = [
        f"  判据：{gua_name}卦化工={'有' if has_hg else '无'}，"
        f"元气={'有' if yq else '无'}（原典：卦体中二者俱反必贫穷困苦夭死）",
    ]
    fan = (not has_hg) and (not yq)
    if not fan:
        ev.append("  运/流年卦含化工或元气 → 虽流年数不吉不为害（原典：运中有之虽流年数不吉不为害）")
    return fan, ev


def _kz_yun_liunian_info(result, target_year: int | None):
    """定位当前大运卦与流年卦（timeline.qi_phase.dayun + yearly_hexagrams）。

    target_year 缺省 → 取系统当前年份；yearly 中无该年 → (None, None, 说明)。
    返回 (dayun_gua, liunian_gua, age_now, note)。
    """
    if result.timeline is None:
        return None, None, None, "无 timeline，不判运反/流年反"
    yearly = result.timeline.yearly_hexagrams or []
    if target_year is None:
        import time as _t
        target_year = _t.localtime().tm_year
    dayun_entries = (result.timeline.qi_phase or {}).get("dayun") or []
    age_now = None
    liunian_gua = ""
    for e in yearly:
        if e.get("year") == target_year:
            age_now = e.get("age")
            liunian_gua = _short(e.get("hexagram", ""))
            break
    if not liunian_gua:
        return None, None, None, f"timeline 无 {target_year} 年流年卦，不判运反/流年反"
    dayun_gua = ""
    if age_now is not None:
        for de in dayun_entries:
            a0, a1 = de.get("age_start"), de.get("age_end")
            if a0 is not None and a1 is not None and a0 <= age_now <= a1:
                dayun_gua = _short(de.get("hexagram", ""))
                break
    if not dayun_gua:
        return None, liunian_gua, age_now, f"{target_year} 年(虚岁{age_now})未定位到大运卦，运反不判（流年反照判）"
    return dayun_gua, liunian_gua, age_now, ""



# ═══════════════════════════════════════════════════════════════════
# 解卦层「原文 + 精义/释义」结构化映射（2026-09-13）
#   每项断法：text=断语释义（引擎输出）｜origin=原文引文｜source=出处｜level=明文/参考/标注
#   原文引文全部摘自核证表 16.1 与各断法函数 docstring，不改动断语文本。
# ═══════════════════════════════════════════════════════════════════

KUOZHAN_META: dict = {
    "siti_bati": {
        "cn": "四体八体", "source": "卷一·论互体四体八体",
        "origin": "凡卦有互体，以正体内外卦除初上二爻，用中四爻，交互成卦，谓之互体；又有伏体、变体，合正体为四体八体",
        "level": "原典明文",
    },
    "fu_li": {
        "cn": "福力层次", "source": "卷一·论应其时合其用",
        "origin": "互体若有，亦受兄弟子孙之福者也。反体若有，亦遭变故而得安宁者也。对体若有，虽死而有余福者也。皆不若本体有之为妙耳",
        "level": "原典明文",
    },
    "wuming_de_gua": {
        "cn": "五命得卦", "source": "卷一·五命得卦 p135-137",
        "origin": "五命得卦：金庚辛申酉、木甲乙寅卯、水壬癸亥子、火丙丁巳午、土戊己辰戌丑未，各配八卦断语",
        "level": "原典明文",
    },
    "suoshu_ji_xiong": {
        "cn": "余数断", "source": "卷一·论所得卦数吉凶 p129-130",
        "origin": "所得卦数吉凶，余数 1-9 各按卦断（一二为乾…九为坤）",
        "level": "原典明文",
    },
    "yue_ling_fei_shi": {
        "cn": "月令非时", "source": "卷一·月令非时论 p117-119",
        "origin": "得时顺节则妙，逆时背令则无用；春木夏火秋金冬水，各令盛衰宜忌",
        "level": "原典明文",
    },
    "shu_ji": {
        "cn": "数极京城山林", "source": "起例卷之下·出后天六合论",
        "origin": "数极有京城，有山林。京城者福，山林者苦。京城减寿，山林则崇高",
        "level": "标注级（京城/山林判据原典未明载）",
    },
    "liu_wei_gui_jian": {
        "cn": "六位贵贱", "source": "起例卷之上·六位贵贱 L208",
        "origin": "初为庶民，二为侯牧，三为公卿节制，四为近侍大臣，五为君位，六为天枢…惟五位为佳，二次之，三四又次之，初上又次之",
        "level": "原典明文",
    },
    "gui_ming_shi_ti": {
        "cn": "贵命十体", "source": "起例卷之上·贵命十体 L209-224",
        "origin": "一卦名吉、二爻吉、三辞吉、四得时、五有援、六顺时、七得体、八当位、九合理、十众宗；得三四者选曹命，得五六者如通命，得七八者乡监侍从，得九十者将相侯王",
        "level": "原典明文（①卦名吉仅列示例，参考级）",
    },
    "jian_ming_shi_ti": {
        "cn": "贱命十体", "source": "起例卷之上·贱命十体 L209-224",
        "origin": "贱命十体皆与十贵相反…得三四者僧道九流之命，得五六者吏僧孤独，得七八者夭横凶顽，得九十者乞丐斩戮",
        "level": "原典明文",
    },
    "yao_ci_bi_li": {
        "cn": "吉凶爻辞比例", "source": "起例卷之上 L198",
        "origin": "凶多吉少者，僧道九流之命也。吉多凶少者，浊富之人也…全凶至贫贱夭寿，全吉至富贵高寿，毫厘不爽也",
        "level": "原典明文",
    },
    "xiang_sheng_wei_fu": {
        "cn": "相生为福·得体·得局生气", "source": "起例卷之上 L161/L235",
        "origin": "木人得巽，火人得离，土人得坤艮，皆为得体…木人得震巽为得局，坎为生气；土人得坤艮离；金人得乾兑艮坤；水人得乾兑坎",
        "level": "原典明文（火人得局生气未载，标注）",
    },
    "yun_liunian_shu_fan": {
        "cn": "运反+流年反+数反", "source": "起例卷之上·化工元气有无论 L200",
        "origin": "如运中有之，虽流年数不吉，不为害…若运既反，流年又反，数又反，其人不可保矣",
        "level": "原典明文",
    },
    "xian_tian_hou_tian_yuan_qi": {
        "cn": "先天后天元气变迁", "source": "起例卷之上·化工元气有无论 L200",
        "origin": "先天若有，后天若无，此先富贵而后贫贱者也。先天若无，后天始有，此先贫贱而后富贵者也；卦体中二者俱反，必贫穷困苦夭死者也",
        "level": "原典明文",
    },
}



# ═══════════════════════════════════════════════════════════════════
# 词汇映射器（B）——极性标注 + 维度归类（2026-09-13）
#   确定性词表命中，可复核可测试；不接 LLM、不改变断语文本。
# ═══════════════════════════════════════════════════════════════════

# 极性词表（按词长降序匹配，避免"不吉/不为害"等误判）
POLARITY_GOOD_WORDS: tuple = (
    "功名富贵", "富贵福寿", "多获福庆", "受福禄", "立大功名", "享大富贵",
    "吉多凶少", "慈母惜子", "终吉", "喜庆", "福庆", "福寿", "富贵", "功名", "福禄",
    "安宁", "欢欣", "得局", "得体", "得生", "为妙", "为佳", "有利", "大吉",
    "元吉", "亨利", "通命", "侯牧", "吉", "福", "庆", "利", "安", "荣",
    "亨", "通", "妙", "佳", "善", "成", "高",
)
POLARITY_BAD_WORDS: tuple = (
    "不可保", "贫穷困苦", "贫贱夭寿", "夭横凶顽", "乞丐斩戮", "僧道九流",
    "数足必死", "恐亦凶", "减寿", "凶多吉少", "刑伤", "灾祸", "夭死",
    "凶", "夭", "贫", "贱", "困", "苦", "灾", "祸", "刑", "伤", "破",
    "败", "劫", "丧", "疾", "病", "诛", "斩", "嫉", "杀", "死", "吝",
)
POLARITY_ALERT_WORDS: tuple = (
    "数足必死", "必死", "身亡", "不可保", "夭死", "夭横", "斩戮",
)
# 非凶豁免：单独成词时不算凶（"无咎"、"不为害"、"不吉不为害"）
_POLARITY_EXEMPT: tuple = ("无咎", "不吉", "不为害")

# 维度静态表（断法属性，非文本推断）
KUOZHAN_DIMENSION: dict = {
    "siti_bati": "命格",
    "fu_li": "福力",
    "wuming_de_gua": "命格",
    "suoshu_ji_xiong": "数理",
    "yue_ling_fei_shi": "时令",
    "shu_ji": "寿夭",
    "liu_wei_gui_jian": "官贵",
    "gui_ming_shi_ti": "官贵",
    "jian_ming_shi_ti": "命格",
    "yao_ci_bi_li": "财禄",
    "xiang_sheng_wei_fu": "五行",
    "yun_liunian_shu_fan": "寿夭",
    "xian_tian_hou_tian_yuan_qi": "命格",
}


def _polarity_count(text: str) -> tuple[int, int]:
    """吉词/凶词计数（词表按长词优先；无咎/不为害豁免）。"""
    good = bad = 0
    t = text
    for w in _POLARITY_EXEMPT:
        t = t.replace(w, "")
    for w in POLARITY_GOOD_WORDS:
        if w in t:
            good += t.count(w)
    for w in POLARITY_BAD_WORDS:
        if w in t:
            bad += t.count(w)
    return good, bad


def polarity_of(text: str, name: str = "") -> str:
    """断语极性：警示 / 吉 / 凶 / 平（确定性词表）。

    规则：命中警示词→警示；否则吉凶词计数比较；相等→平。
    示例："数足必死"→警示；"吉多凶少→浊富"→吉；"无咎"不计凶。
    """
    if not text:
        return "平"
    if any(w in text for w in POLARITY_ALERT_WORDS):
        return "警示"
    g, b = _polarity_count(text)
    if g > b:
        return "吉"
    if b > g:
        return "凶"
    return "平"


def dimension_of(name: str) -> str:
    """断法名 → 维度（静态表，未覆盖返回'其他'）。"""
    return KUOZHAN_DIMENSION.get(name, "其他")


def structure_kuozhan(kuozhan: dict) -> list[dict]:
    """扩展断法 → 结构化条目 [{name, cn, text, origin, source, level}]。

    text=断语释义（引擎原输出，join"；"）；origin/source/level 取自 KUOZHAN_META；
    META 未覆盖的项只保留 name+text（不编造出处）。
    """
    out: list[dict] = []
    for name, v in (kuozhan or {}).items():
        meta = KUOZHAN_META.get(name) or {}
        if isinstance(v, str):
            text = v
        elif isinstance(v, list):
            text = "；".join(v)
        elif isinstance(v, dict):
            import json as _json
            text = _json.dumps(v, ensure_ascii=False)
        else:
            text = str(v)
        item: dict = {"name": name, "text": text,
                   "polarity": polarity_of(text, name),
                   "dimension": dimension_of(name)}
        if meta:
            item["cn"] = meta.get("cn", "")
            item["origin"] = meta.get("origin", "")
            item["source"] = meta.get("source", "")
            item["level"] = meta.get("level", "")
        out.append(item)
    return out


def _yaoduan_detail(d: Optional[dict], hexagram: str = "", year=None) -> dict:
    """流年/流月/流日爻断 → 结构化（原文 ci + 精义 shao + 叶/不叶/岁运）。"""
    if not d:
        return {}
    out = {
        "yao": d.get("yao", ""),
        "origin": d.get("ci", ""),          # 原文爻辞
        "yiyi": d.get("shao", ""),          # 精义/释义（原著自带）
        "ye": d.get("ye", ""),              # 数卦叶
        "buye": d.get("buye", ""),          # 数卦不叶
        "suiyun": d.get("suiyun", ""),      # 岁运断
    }
    if hexagram:
        out["hexagram"] = hexagram
    if year:
        out["year"] = year
    return out


def to_structured(gj: dict) -> dict:
    """解卦层 dict → 原文+精义/释义 结构化视图（不修改 gj 本身）。

    - life:   命格断法条目（kuozhan 13 项，带原文引文/出处/等级）
    - timing: 流年/流月/流日/流时爻断（原文 ci + 精义 shao + 叶/不叶）
    - warnings: 死断/正对反对/数凶/元气化工/节候化工（原文引文在断语文本内标注）
    - summary: 综合判词（人话，保持原样）
    """
    out: dict = {}
    out["life"] = structure_kuozhan(gj.get("kuozhan") or {})
    timing: dict = {}
    for k in ("liunian", "liuyue", "liuri", "liushi"):
        v = _yaoduan_detail(gj.get(k + "_yao") or {},
                            gj.get(k + "_hexagram") or "",
                            gj.get("liunian_year") if k == "liunian" else None)
        if v:
            timing[k] = v
    if gj.get("liunian_ye_buye"):
        timing["liunian_ye_buye"] = {
            "ye": gj["liunian_ye_buye"].get("ye", ""),
            "buye": gj["liunian_ye_buye"].get("buye", ""),
            "evidence": gj["liunian_ye_buye"].get("evidence", []),
        }
    out["timing"] = timing
    warns: list[str] = []
    for w in (gj.get("si_duan") or []):
        warns.append(w)
    for w in (gj.get("zhengdui_fandui") or []):
        warns.append(w)
    if gj.get("shu_xiong") and gj["shu_xiong"].get("shu_xiong"):
        _sx = gj["shu_xiong"]
        warns.append(f"数凶（{_sx.get('tian_shu', '?')}/{_sx.get('di_shu', '?')}，{_sx.get('pattern', '')}）")
    out["warnings"] = [{"text": w, "polarity": polarity_of(w)} for w in warns]
    out["nayin_yuanqi"] = gj.get("nayin_yuanqi") or []
    out["jiehua_gong"] = gj.get("jiehua_gong") or []
    out["summary"] = gj.get("summary") or []
    # 2026-10-08 审计修（P4）：以下三块此前**只存在于 to_dict**，
    # 结构化视图里完全看不到——运行时实测 to_dict 有 23 键而 structured 只 6 块，
    # benming / canping / evidence 整块丢失（evidence 数十行）。
    # 本函数在 src/ 下零调用方，属潜伏缺陷，但「结构化视图比原始 dict 少三块」
    # 本身就是个坑：任何接上它的人都会静默丢判词。
    # 注意口径：透传原值，不改结构、不编造出处。
    out["benming"] = gj.get("benming")
    out["canping"] = gj.get("canping")
    out["evidence"] = gj.get("evidence") or []
    # 2026-10-08 接入：爻辞取象命中。与上面三块同理——to_dict 有、结构化
    # 视图无，则接上本函数的人会静默丢掉 L741 整层取象。透传原值不改结构。
    out["yao_xiang_hits"] = gj.get("yao_xiang_hits") or []
    return out


#: 八个扩展断法中**计算失败**的痕迹；正常应为空。非空即表示该判法失败而非无结论。
_KZ_ERRORS: list[str] = []


def kuozhan_errors() -> list[str]:
    """最近一次 _build_kuozhan 中失败的判法及异常（正常应为空）。"""
    return list(_KZ_ERRORS)


def _build_kuozhan(
    result, bazi, prenatal: str, postnatal: str,
    year_ganzhi: str, tian: int, di: int,
    tian_reduced: int, di_reduced: int,
    si_duan: list[str], target_year: int | None = None,
) -> dict:
    """组装扩展断法（每项独立 try，单项失败不阻塞其余）。"""
    # ⚠ 2026-10-24 审计修：原实现**只 append 从不清空**，而本函数 docstring
    #   与 `kuozhan_errors()` 都声称「最近一次」。实际返回的是**进程级历史累积**
    #   —— 第一盘失败过一次，之后每一盘的 kuozhan_errors() 都带着那条陈迹，
    #   调用方无法区分「本盘失败」与「历史上有过一盘失败」。
    #   现于入口清空（与 diagnosis_rule_graph.build_diagnosis_graph 的
    #   _DROPPED_RULES.clear() 同款），使语义与文档一致。
    _KZ_ERRORS.clear()
    kz: dict = {}

    # 运反/流年反/数反接驳（起例卷之上·化工元气有无论 L200；2026-09-12 接驳）
    def _kz_yun_liunian_kuozhan(result_, bazi_, target_year_, si_duan_):
        try:
            dayun_gua, liunian_gua, age_now, note = _kz_yun_liunian_info(
                result_, target_year_)
            yg = (bazi_[0][0] if bazi_ and len(bazi_) >= 1 else "")
            yz = (bazi_[0][1] if bazi_ and len(bazi_) >= 1 else "")
            shu_fan = bool(si_duan_ and any("数凶" in w for w in si_duan_))
            yun_fan, yun_ev = _yun_liunian_fan(dayun_gua, yg, yz) if dayun_gua else (False, [])
            lf, liu_ev = _yun_liunian_fan(liunian_gua, yg, yz) if liunian_gua else (False, [])
            out = judge_yun_liunian_shu_fan(
                yun_fan=yun_fan, liunian_fan=lf, shu_fan=shu_fan,
                dayun_gua=dayun_gua or "", liunian_gua=liunian_gua or "",
                age_now=age_now,
            )
            if note:
                out.append(f"  注：{note}")
            out.extend(yun_ev)
            out.extend(liu_ev)
            return out
        except Exception as _e:
            return [f"运反/流年反/数反：计算跳过（{_e}）"]

    half_year = ""
    bd = getattr(result.input, "birth_date", "") or ""
    if bd:
        half_year = _solar_phase(bd) or ""
    if not half_year and bazi and len(bazi) >= 2:
        half_year = _HALF_YEAR_BY_BRANCH.get(bazi[1][1], "")
    for name, fn in (
        ("siti_bati", lambda: compute_siti_bati(prenatal, postnatal)),
        ("fu_li", lambda: judge_fu_li(prenatal)),
        ("wuming_de_gua", lambda: judge_wuming_de_gua(year_ganzhi, prenatal)),
        ("suoshu_ji_xiong", lambda: judge_suoshu_ji_xiong(tian, di, tian_reduced, di_reduced, half_year)),
        ("yue_ling_fei_shi", lambda: judge_yue_ling_fei_shi(bazi, tian, di)),
        ("shu_ji", lambda: judge_shu_ji(si_duan)),
        # ── 解卦层第二轮扩充（2026-09-12）──────────────────────────
        ("liu_wei_gui_jian", lambda: judge_liu_wei_gui_jian(
            getattr(getattr(result, "yuantang", None), "yuantang", "") or "")),
        ("gui_ming_shi_ti", lambda: judge_gui_ming_shi_ti(
            prenatal_name=prenatal,
            yuantang_yao=getattr(getattr(result, "yuantang", None), "yuantang", "") or "",
            yao_cis=_kz_yao_cis(prenatal),
            yao_lines=_gua_to_lines(prenatal),
            birth_month_branch=(bazi[1][1] if bazi and len(bazi) >= 2 else ""),
            gua_qi_month=_kz_gua_qi_month(prenatal),
            tian_shu=tian, di_shu=di,
            year_gan=(bazi[0][0] if bazi else ""), year_zhi=(bazi[0][1] if bazi else ""))),
        ("jian_ming_shi_ti", lambda: judge_jian_ming_shi_ti(
            prenatal_name=prenatal,
            yuantang_yao=getattr(getattr(result, "yuantang", None), "yuantang", "") or "",
            yao_cis=_kz_yao_cis(prenatal),
            yao_lines=_gua_to_lines(prenatal),
            birth_month_branch=(bazi[1][1] if bazi and len(bazi) >= 2 else ""),
            gua_qi_month=_kz_gua_qi_month(prenatal),
            tian_shu=tian, di_shu=di,
            year_gan=(bazi[0][0] if bazi else ""), year_zhi=(bazi[0][1] if bazi else ""))),
        ("yao_ci_bi_li", lambda: judge_yao_ci_bi_li(_kz_yao_cis(prenatal))),
        ("xiang_sheng_wei_fu", lambda: judge_xiang_sheng_wei_fu(
            prenatal, (bazi[0][0] if bazi else ""), (bazi[0][1] if bazi else ""))),
        ("yun_liunian_shu_fan", lambda: _kz_yun_liunian_kuozhan(
            result, bazi, target_year, si_duan)),
        ("xian_tian_hou_tian_yuan_qi", lambda: judge_xian_tian_hou_tian_yuan_qi(
            xiantian_yq=bool(judge_nayin_yuanqi(
                (bazi[0][0] if bazi else ""), (bazi[0][1] if bazi else ""), prenatal)),
            houtian_yq=bool(judge_nayin_yuanqi(
                (bazi[0][0] if bazi else ""), (bazi[0][1] if bazi else ""), postnatal)))),
    ):
        try:
            v = fn()
            if v:
                kz[name] = v
        except Exception as _e:
            # 2026-10-08 审计修（⚪19）：旧代码此处是裸 pass——八个判法逐个 try，
            # 任一失败即从 kz 里**彻底消失**，既不进 evidence 也不记日志，
            # 比本文件其他块（至少写「计算跳过（{e}）」）更弱，下游只会看到
            # 「这个判法好像本来就没结论」。现登记到 kuozhan_errors() 供调用方披露。
            _KZ_ERRORS.append("%s: %s: %s" % (name, type(_e).__name__, _e))
    return kz



__all__ = [
    "GuaDuan", "YaoDuan", "YeBuYeResult", "ShuXiongResult", "GuaJieResult",
    "load_guajie_data", "query_yao_duan", "judge_ye_buye",
    "judge_shu_xiong", "check_zhengdui_fandui", "check_twelve_xiong",
    "jingyi_load_error", "judge_si_duan",
    "compute_huti", "judge_nayin_yuanqi", "get_nayin_element",
    "judge_jiehua_gong", "judge_nayin_huti", "hexagram_to_lines",
    "compose_guajie", "build_guajie_from_result",
    "compute_siti_bati", "judge_fu_li", "judge_wuming_de_gua",
    "judge_shu_ji", "judge_suoshu_ji_xiong", "judge_yue_ling_fei_shi",
    "judge_liu_wei_gui_jian", "judge_gui_ming_shi_ti", "judge_jian_ming_shi_ti",
    "judge_yao_ci_bi_li", "judge_xiang_sheng_wei_fu",
    "judge_yun_liunian_shu_fan", "judge_xian_tian_hou_tian_yuan_qi",
    "structure_kuozhan", "to_structured", "KUOZHAN_META",
    "polarity_of", "dimension_of", "KUOZHAN_DIMENSION",
    # ⚠ 2026-10-24 第三轮审计修：原导出 "wuming_element"（**无下划线**），
    #   而模块里只有 `_wuming_element` ⇒ `from ...guajie import *` 直接
    #   AttributeError（公开导出面与实现不一致）。
    #   修法：导出实际存在的名字。
    "_wuming_element",
    "TWELVE_XIONG_GUA", "QIANXI_DUKONG", "ZONG_GUA", "BRANCH_TO_MONTH",
    "TRIGRAM_ELEMENT", "ELEMENT_GENERATES",
]
