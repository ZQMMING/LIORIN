"""起例卷之上 · 元气干支两说并存 + 干支纳卦表（原典 L471–L516 / L681–L693）

本模块 2026-10-08 新增。三份只读审计查出的「原典有文而未实现」缺口，
本模块落其中**判据完全确定、且能自校验**的三张表。

═══ 一、为什么是「两说并存」而不是「择一」═══

原典在 L471–L477 给了一张八卦干支表（称「纳表」）：

    L471  凡人当生年天干为天元气，主贵，地支为地元气，主富，纳音为人元气，主寿。
    L474  乾壬甲戌亥　坎戊子　震庚卯　艮丙丑寅
    L477  坤乙癸未申　离己午　兑丁酉　巽辛辰巳

随后在 L495–L516 给了「反」表，再在 L519–L540 另给一张表，**开头明写「又云」**：

    L519  又云乾卦干主辛，支主辰巳，纳音木，与巽相反。

2026-10-07 的审计把它列为「原典自相矛盾，需第二传本」，要求取得第二传本再定。
2026-10-08 已用**四本独立转录**交叉核对（原著 A／河洛真数OCR C／续修四库点校 D／
河洛数待整理 E，见 tools/heluo/fetch_yuanqi_evidence.py），结论是：

* **不是转录讹误。** A/B/D/E 四本逐字一致地把这两段并列排出，且 L519 的
  「又云」四本俱在——「又云」是原典自己的措辞，意思是**另有一说**，
  不是校勘者的更正标记。
* **两说各自都自洽，但「相反」的定义不同**——这是本轮最要紧的发现：
  * 说一的「相反」= **错卦（对宫）**（见自校验①：反表每条的反者干支正好是
    对宫卦的干支组，八条全中）。
  * 说二的「相反」= **按该说纳音五行的相克**（乾↔巽金克木、坤↔艮土克水、
    坎↔离水克火、兑↔震金克木）。初版我按「两说都用错卦」写断言，导入即失败，
    才发现八条里**只有坎↔离同时也是对宫**，其余六条都不是。
  * 故两说的干支归属差异**不是笔误**，而是按各自相反关系整体重排的结果——
    穷举八组，**八组全部互换**，无一相同。
  * **这两套「相反」不可混用，更不可择一。** 凡输出「元气相反」处，
    必须标明用的是哪一说，否则会把两个不同判据揉成一个结论。

所以正确处理**不是择一，而是两套并存、分名登记、都可查、互不覆盖**。
择一会凭空丢掉原典的一半信息，且会把一次取舍伪装成原典结论。

═══ 二、自校验（把原典的内在结构变成可执行的断言）═══

1. 反表（L495–L516）八条，每条的「反者干支」必须正好是**对宫卦**在纳表（L474/L477）
   里的干支组。八条全中。**这一条同时钉死了「震反辛辰己」的讹字**——
   A/D 本作「己」，但「辛辰己」不是任何卦的干支组（巽为辛辰**巳**），
   取「巳」则八条自校验全过；C（OCR）本亦作「巳」。故取「巳」，「己」旁注存疑。
2. 又云表（L519–L540）八条，每条的「干支」必须正好是**对宫卦**在纳表里的干支组。
   八条全中。
3. 干支纳卦表（L681–L693）五组各十二干支，须恰好覆盖六十甲子，无重无漏。

三条断言写在本模块底部，导入即验；任一条不成立即抛 AssertionError——
这意味着**任何人改动本模块的表而破坏原典结构，测试与生产都会立刻炸**。

═══ 三、与既有模块的边界 ═══

* `yuan_qi.STEM_TO_TRIGRAM` 是**天干单字 → 卦**（甲壬→乾…），来自 L471 那句
  「年干为天元气」的天干纳甲，与本模块的**干支组 → 卦**是两回事，不互相覆盖。
* 本模块只做**查询**，不改判词。要接进 `yuan_qi.compute_yuan_qi` 的 REVERSE 分支
  （输出定域病症）时，用 `yuanqi_fan_suffering()` 取，不得在判词里另写一遍。
* 干支纳卦表（L681）原文自带一句限定：**「木命生年干支所纳之卦，即纳音」**
  ——即该表说的是**纳音**，故与 `canping._NAYIN`（纳音→五行）大面积重合；
  但这是**两张独立表**，重合不等于同一，**不得合并**，注释亦不得删。
"""
from __future__ import annotations

from dataclasses import dataclass

# ── 错卦（六爻全变，先天方位对宫）──────────────────────────────
#: 六画卦层面的对宫。与化工相反（四季对宫，见 hua_gong.OPPOSITE_TRIGRAM）
#: 是两回事，两表彻底分开命名，不得混称。
#:
#: 2026-10-22：本表原先是 QIANXI_DUKONG 的**内容副本**（第四份），改引用
#: 权威单一来源，保名不保表 —— 避免同内容双公开名各自漂移。
from .hexagram_state import QIANXI_DUKONG as DUI_GUA

# ── 说一：纳表（L474/L477）卦 → 干支组 ───────────────────────────
#: 原典逐字：
#:   L474「乾壬甲戌亥　坎戊子　震庚卯　艮丙丑寅」
#:   L477「坤乙癸未申　离己午　兑丁酉　巽辛辰巳」
#: 前者为天干组、后者为地支组（据 L471「年天干为天元气，地支为地元气」）。
YUANQI_GANZHI_TABLE_A: dict[str, tuple[str, str]] = {
    "乾": ("壬甲", "戌亥"),
    "坎": ("戊", "子"),
    "震": ("庚", "卯"),
    "艮": ("丙", "丑寅"),
    "坤": ("乙癸", "未申"),
    "离": ("己", "午"),
    "兑": ("丁", "酉"),
    "巽": ("辛", "辰巳"),
}


# ── 说二：又云表（L519–L540）卦 → 干/支/纳音五行/相反卦 ─────────
@dataclass(frozen=True)
class YuanQiGuaRow:
    """又云表一行。"""
    gua: str            # 卦
    gan: str            # 干主
    zhi: str            # 支主
    nayin_element: str  # 纳音五行
    opposite_gua: str   # 原典明写的「与X相反」


#: 原典逐字（L519–L540），开头 L519 带「又云」二字，是**原典自己的另立一说**标记。
YUANQI_GANZHI_TABLE_B: dict[str, YuanQiGuaRow] = {
    "乾": YuanQiGuaRow("乾", "辛", "辰巳", "木", "巽"),
    "坤": YuanQiGuaRow("坤", "丙", "丑寅", "水", "艮"),
    "坎": YuanQiGuaRow("坎", "己", "午", "火", "离"),
    "离": YuanQiGuaRow("离", "戊", "子", "水", "坎"),
    "兑": YuanQiGuaRow("兑", "庚", "卯", "木", "震"),
    "艮": YuanQiGuaRow("艮", "乙癸", "申未", "土", "坤"),
    "震": YuanQiGuaRow("震", "丁", "酉", "金", "兑"),
    "巽": YuanQiGuaRow("巽", "壬甲", "戌亥", "金", "乾"),
}


# ── 反表（L495–L516）卦 → 反者干支 / 病症 / 病位 ─────────────────
@dataclass(frozen=True)
class YuanQiFanRow:
    """元气反表一行。"""
    gua: str            # 本卦
    fan_ganzhi: str     # 原典写的「反者」干支组
    suffering: str      # 病症
    body_part: str      # 病位


#: 原典逐字：
#:   L495「乾反乙癸未申主夭寿，反天道也。」
#:   L498「坤反壬甲戌亥主贫贱，反地道也。」
#:   L501「艮反丁酉主瘫疽，气不通，手受病也。」
#:   L504「兑反丙丑寅主缺唇翻唇疏齿，口受病也。」
#:   L507「震反辛辰巳主跛，足受病也。」
#:   L510「巽反庚卯主痼疾，股受病也。」
#:   L513「坎反己午主聋，耳受病也。」
#:   L516「离反戊子主瞽眇，目受病也。」
#:
#: ⚠ L507 的「巳」：A/D 两本转录作「己」。本表取「巳」——理由是下面第一条
#:   自校验：反者的干支组必须正好是对宫卦在纳表里的干支组，巽为「辛辰**巳**」，
#:   作「己」则「辛辰己」不是任何卦的干支组，校验立即失败。C（OCR）本亦作「巳」。
#:   「己」作为异读旁注存疑，不得当作原文。
#: ⚠ L495/L498 的「夭寿」「贫贱」是**祸福**不是**病**，与其余六条的病位不同类，
#:   病位留空。
YUANQI_FAN_TABLE: dict[str, YuanQiFanRow] = {
    "乾": YuanQiFanRow("乾", "乙癸未申", "夭寿", ""),
    "坤": YuanQiFanRow("坤", "壬甲戌亥", "贫贱", ""),
    "艮": YuanQiFanRow("艮", "丁酉", "瘫疽（气不通）", "手"),
    "兑": YuanQiFanRow("兑", "丙丑寅", "缺唇翻唇疏齿", "口"),
    "震": YuanQiFanRow("震", "辛辰巳", "跛", "足"),
    "巽": YuanQiFanRow("巽", "庚卯", "痼疾", "股"),
    "坎": YuanQiFanRow("坎", "己午", "聋", "耳"),
    "离": YuanQiFanRow("离", "戊子", "瞽眇", "目"),
}


# ── 干支纳卦表（L681–L693）干支 → 卦组 ──────────────────────────
#: 原典逐字，五组各十二干支：
#:   L681「甲子、甲午、乙丑、乙未、庚戌、庚辰、辛巳、辛亥、壬寅、壬申、癸卯、癸酉
#:         十二干支纳**乾兑金卦**。」
#:   L684「甲寅、甲申、乙卯、乙酉、丙子、丙午、丁丑、丁未、壬辰、壬戌、癸巳、癸亥
#:         十二干支纳**坎水卦**。」
#:   L687「甲辰、甲戌、乙巳、乙亥、丙寅、丙申、丁卯、丁酉、戊子、戊午、己丑、己未
#:         十二干支纳**离火卦**。」
#:   L690「丙辰、丙戌、丁巳、丁亥、戊寅、戊申、己卯、己酉、庚子、庚午、辛丑、辛未
#:         十二干支纳**坤艮土卦**。」
#:   L693「戊辰、戊戌、己巳、己亥、庚寅、庚申、辛卯、辛酉、壬子、壬午、癸丑、癸未
#:         十二干支纳**震巽木卦**。」
#:
#: ⚠ L681 原文自带限定：「**木命生年干支所纳之卦，即纳音**，元气主疾病之类」——
#:   即这张表说的就是纳音，故与 canping._NAYIN（纳音→五行）大面积重合。
#:   但这是**两张独立表**：_NAYIN 给的是五行，本表给的是**卦**（两个卦一组）。
#:   重合不等于同一，**不得合并**，本段注释亦不得删。
GANZHI_GUA_GROUPS: dict[str, tuple[tuple[str, ...], str]] = {
    # 五行: (十二干支, 卦组名)
    "金": (("甲子", "甲午", "乙丑", "乙未", "庚戌", "庚辰",
            "辛巳", "辛亥", "壬寅", "壬申", "癸卯", "癸酉"), "乾兑"),
    "水": (("甲寅", "甲申", "乙卯", "乙酉", "丙子", "丙午",
            "丁丑", "丁未", "壬辰", "壬戌", "癸巳", "癸亥"), "坎"),
    "火": (("甲辰", "甲戌", "乙巳", "乙亥", "丙寅", "丙申",
            "丁卯", "丁酉", "戊子", "戊午", "己丑", "己未"), "离"),
    "土": (("丙辰", "丙戌", "丁巳", "丁亥", "戊寅", "戊申",
            "己卯", "己酉", "庚子", "庚午", "辛丑", "辛未"), "坤艮"),
    "木": (("戊辰", "戊戌", "己巳", "己亥", "庚寅", "庚申",
            "辛卯", "辛酉", "壬子", "壬午", "癸丑", "癸未"), "震巽"),
}

#: 干支 → (卦组名, 五行)。由 GANZHI_GUA_GROUPS 派生，导入即建，不手工维护。
GANZHI_TO_GUA: dict[str, tuple[str, str]] = {}
for _el, (_list, _guas) in GANZHI_GUA_GROUPS.items():
    for _gz in _list:
        assert _gz not in GANZHI_TO_GUA, "干支 %s 重复出现在两组" % _gz
        GANZHI_TO_GUA[_gz] = (_guas, _el)


# ═══════════════ 查询接口 ═══════════════
def ganzhi_element(ganzhi: str) -> str:
    """干支 → 五行（纳音口径，L681–L693）。未知返回 ""。"""
    row = GANZHI_TO_GUA.get(ganzhi)
    return row[1] if row else ""


def ganzhi_guas(ganzhi: str) -> tuple[str, ...]:
    """干支 → 所纳之卦（L681–L693，每组一或两个卦）。未知返回 ()。"""
    row = GANZHI_TO_GUA.get(ganzhi)
    if not row:
        return ()
    return tuple(row[0])


def gua_of_ganzhi_table_a(gua: str) -> tuple[str, str]:
    """说一（纳表 L474/L477）：卦 → (干组, 支组)。"""
    return YUANQI_GANZHI_TABLE_A.get(gua, ("", ""))


def gua_of_ganzhi_table_b(gua: str) -> YuanQiGuaRow | None:
    """说二（又云表 L519–L540）：卦 → 该说下的干/支/纳音/相反卦。"""
    return YUANQI_GANZHI_TABLE_B.get(gua)


def yuanqi_fan_suffering(gua: str) -> tuple[str, str]:
    """反表（L495–L516）：卦 → (病症, 病位)。无据返回 ("", "")。"""
    row = YUANQI_FAN_TABLE.get(gua)
    return (row.suffering, row.body_part) if row else ("", "")


def yuanqi_fan_relation(gua: str, other: str) -> tuple[str, ...]:
    """``(gua, other)`` 是否构成「元气相反」，返回成立的那几套说法。

    两说对**谁是对方**的判断完全一致（都是错卦/对宫，见 ``_self_check``），
    差别只在**干支归属**——那件事由 :func:`yuanqi_ganzhi_conflict` 单独回答。
    故本函数返回的名字只表示「哪几说的对宫关系支持这条」。
    """
    out = []
    if DUI_GUA.get(gua) == other:
        out.append("说一")
    row = YUANQI_GANZHI_TABLE_B.get(gua)
    if row is not None and row.opposite_gua == other:
        out.append("说二")
    return tuple(out)


def yuanqi_fan_ganzhi(gua: str) -> tuple[str, ...]:
    """卦的相反者干支组，按说返回。

    返回长度 ≤ 2：说一给 1 个（来自 L495–L516 反表），说二给 1 个（来自 L519–L540）。
    两者不同时长度即为 2——**这正是原典两说的分歧点，不得取其一**。
    """
    out = []
    row = YUANQI_FAN_TABLE.get(gua)
    if row is not None:
        out.append(row.fan_ganzhi)
    r2 = YUANQI_GANZHI_TABLE_B.get(gua)
    if r2 is not None:
        duo = YUANQI_GANZHI_TABLE_A[DUI_GUA[gua]]
        cand = duo[0] + duo[1]
        if cand not in out:
            out.append(cand)
    return tuple(out)


def _canon(gan: str, zhi) -> str:
    """干支组的规范形：干原样 + 支**排序后**拼接（支序无关）。"""
    return gan + "".join(sorted(zhi))


#: 规范形 → 卦。用于「一个干支组属于哪一卦」的反查，支序无关。
_A_BY_KEY: dict[str, str] = {
    _canon(gan, zhi): g for g, (gan, zhi) in YUANQI_GANZHI_TABLE_A.items()
}
_B_BY_KEY: dict[str, str] = {
    _canon(r.gan, r.zhi): r.gua for r in YUANQI_GANZHI_TABLE_B.values()
}


def yuanqi_ganzhi_conflict(gan: str, zhi: str) -> tuple[str, str]:
    """一个干支组在两说下归属的卦是否不同。

    ⚠ **必须传 (gan, zhi) 两参，不能拼成一个字符串。** 干组长度不定
    （「壬甲」两字、「戊」一字），按位置切片会把「戊子」切成 gan="戊子"、
    zhi=""，整组查不到——这是本函数第一版的实际 bug。

    返回 ``(说一归属卦, 说二归属卦)``；两者相同或任一为无据时返回 ("", "")。
    穷举八组，**八组全部出现分歧**（两说把每组干支都换给了对方卦）——
    这不是本模块的缺陷，是原典 L519「又云」自陈的另立一说。
    ⚠ 支组按**集合**比：L477 坤作「乙癸未申」、L534 艮作「乙癸，支主申未」，
      同一组只是行文次序不同，按串比会漏判。
    """
    k = _canon(gan, zhi)
    a, b = _A_BY_KEY.get(k, ""), _B_BY_KEY.get(k, "")
    if not a or not b or a == b:
        return ("", "")
    return (a, b)


def yuanqi_fan_by_dui(gua: str) -> str:
    """按错卦（对宫）求相反卦——这是**唯一两说共通**的关系。

    L492 总则「凡人与元气相反者，如木人得兑，火人得坎，土人得震，金人得离，
    水人得土之类」说的是**纳音五行与其相反者**，与八卦对宫同构：
    木↔金、火↔水、土↔木、…
    本函数给的是卦层面的对宫，两说皆同，可安全用于判词。
    """
    return DUI_GUA.get(gua, "")


# ═══════════════ 导入即验的自校验 ═══════════════
def _ganzhi_key(gan: str, zhi: str) -> str:
    return gan + zhi


def _self_check() -> None:
    guas = set(DUI_GUA)
    assert guas == set(YUANQI_GANZHI_TABLE_A) == set(YUANQI_GANZHI_TABLE_B), \
        "三张表未覆盖同一组八卦"
    assert set(YUANQI_FAN_TABLE) == guas, "反表未覆盖八卦"

    # ① 反表（L495–L516）：反者干支 == 对宫卦在纳表里的干支组
    for g, row in YUANQI_FAN_TABLE.items():
        duo_gan, duo_zhi = YUANQI_GANZHI_TABLE_A[DUI_GUA[g]]
        want = _ganzhi_key(duo_gan, duo_zhi)
        assert row.fan_ganzhi == want, (
            "反表 %s：原典作「%s」，但对宫 %s 在纳表(L474/L477)中的干支是「%s」"
            "——两者必须一致，否则这条不是「对宫反」"
            % (g, row.fan_ganzhi, DUI_GUA[g], want))

    # ② 又云表（L519–L540）：两件事必须同时成立
    #    ②a 该说下的干支 == 纳表里「该说自陈的相反卦」的干支组
    #        （即干支归属按其自陈的相反关系整体重排，不是抄纳表）
    #    ②b 该说下的「相反」== **按该说纳音五行的相克**，而不是对宫。
    #        相克判**不分方向**：乾(木)↔巽(金) 是巽克乾，坤(水)↔艮(土) 是艮克坤，
    #        兑(木)↔震(金) 是震克兑——这三组都是「对方克本方」；
    #        但坎(火)↔离(水) 却是本方离克坎，**方向与前三组相反**。
    #        故只能说「两两相克」，不能说「本方克对方」。
    #        ⚠ 以上是 2026-10-08 导入自校验时才发现的：初版我按「两说都用
    #        错卦」去校验，断言立刻失败。实则又云表的相反关系是
    #        乾↔巽、坤↔艮、坎↔离、兑↔震，**只有坎↔离同时也是对宫**，
    #        其余六条都不是。**两说的「相反」定义根本不同**，不可混用，更不可择一。
    _KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}  # a 克 b
    for g, row in YUANQI_GANZHI_TABLE_B.items():
        opp = row.opposite_gua
        duo_gan, duo_zhi = YUANQI_GANZHI_TABLE_A[opp]
        # ⚠ 支组须按**集合**比，不能比字符串：L477 坤作「乙癸未申」（未在前），
        #   L534 艮作「乙癸，支主申未」（申在前）——同一组，只是行文次序不同。
        #   按串比会在这里误报。
        assert row.gan == duo_gan, (
            "又云表 %s：干「%s」与该说自陈的相反卦 %s 在纳表中的干「%s」不符"
            % (g, row.gan, opp, duo_gan))
        assert set(row.zhi) == set(duo_zhi), (
            "又云表 %s：支「%s」与该说自陈的相反卦 %s 在纳表中的支「%s」不符"
            % (g, row.zhi, opp, duo_zhi))
        opp_row = YUANQI_GANZHI_TABLE_B[opp]
        a, b = row.nayin_element, opp_row.nayin_element
        assert _KE.get(a) == b or _KE.get(b) == a, (
            "又云表 %s：原典称「与%s相反」，但 %s(纳音%s) 与 %s(纳音%s) 不相克——"
            "该说的相反关系应按其纳音五行两两相克"
            % (g, opp, g, a, opp, b))

    # ③ 干支纳卦表（L681–L693）：五组各十二，恰好覆盖六十甲子
    total = sum(len(v[0]) for v in GANZHI_GUA_GROUPS.values())
    assert total == 60, "干支纳卦表共 %d 项，应为 60" % total
    for el, (lst, _guas) in GANZHI_GUA_GROUPS.items():
        assert len(lst) == 12, "%s 组 %d 项，原典明言「十二干支」" % (el, len(lst))


_self_check()