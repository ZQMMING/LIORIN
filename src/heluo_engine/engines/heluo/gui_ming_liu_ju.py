"""贵命**前六项**判据 —— 原典转录（2026-10-22 定位更正）

⚠⚠ **本模块不是「另一套贵命判据」，而是「贵命十体」的前六项。**
2026-10-22 逐字核实结论：

  · 原典的正式条目是 **《河洛真数·起例卷之上》L209-L224「贵命十体」**：
        L209  贵命十体
        L210  一卦名吉（如泰、大有、同人、晋、豫之类是也）
        L211  二爻吉（如元堂住在二五爻是也）
        L212  三辞吉（卦爻中有元吉亨利是也）
        L213  四得时（如春震木、夏离火、秋兑金、冬坎水之类。又如正月得泰卦、
                    九月得剥卦之类皆是）
        L214  五有援（谓元堂在阳爻，应爻得阴，或元堂在阴爻，而应爻得阳是也）
        L215  六顺时（谓天地二数多寡与时偕行。如正月生人得天数多地数少，
                    九月生人得地数多天数少是也）
        L216  七得体 … L219 十众宗
        L220  分级：得三四者选曹命，得五六者如通命，得七八者乡监侍从，
                    得九十者将相侯王
        L221-L224  贱命十体（皆与十贵相反）＋其分级
  · 本模块收录的六项（卦名/爻位/爻辞/得时/有援/顺时）**恰是上面十项的
    前六项**（①~⑥），逐字条文一一对应。
  · 本模块 LIU_JU 里标的行号 L633-L648 是**另一底本**（整本 txt）的行号 ——
    包内 `heluo_engine/orig/河洛真数_起例卷之中.txt` 只有 213 行，
    且其中**并无**这六项（它讲的是十二月卦气）。该六项在包内原典中的
    可回查位置是**《起例卷之上》L210-L215**。

**裁定（2026-10-22）**：贵命十体**只有一套规则**，权威出处 =
《河洛真数·起例卷之上》L209-L224。生产口径是
``guajie.judge_gui_ming_shi_ti`` / ``judge_jian_ming_shi_ti``（**十项全套**
＋分级＋贱命取反，出处在库）；**本模块是前六项的子集转录，供留档与对拍，
不作生产口径**。

本模块保留的价值：它逐条附了另一底本的行号与「原典未言者一律返回 None
并登记『原典无明文』，不猜」的严谨姿态。其中三处判读比生产实现更贴合原典，
已于 2026-10-22 合并进 ``guajie``（见该模块注释）：
  ① 卦名：不在明举例内 → **不判**（原典用「之类」= 举例未穷举，不得判凶）
  ③ 辞吉：按**词组**「元吉/亨利」命中（单字匹配会几乎恒中）
  ④ 得时：补上原文明文的第二类「正月得泰卦、九月得剥卦」

本模块把起例卷之中「贵命」一节的**六项明文判据**落成可执行查表，
用于替换先前无原典依据的自拟打分。

原典逐条（六项，节引原文）：

    一卦名吉 …  二爻吉（如元堂住在二五爻是也）
    三辞吉（卦爻中有元吉亨利是也）
    四得时（如春震木、夏离火、秋兑金、冬坎水之类。
            又如正月得泰卦、九月得剥卦之类皆是）
    五有援（谓元堂在阳爻，应爻得阴，或元堂在阴爻，
            而应爻得阳是也）
    六顺时（谓天地二数多寡与时偕行。
            如正月生人得天数多地数少，九月生人得地数多天数少是也）

反见（另一底本 L669；包内对应《起例卷之上》L222）：

    一卦名凶　二爻位凶　三辞凶　四不得时　五无援

**本模块只做「原典说了什么」的事，不发明分数。**
所有判定返回**原典判据名 + 原文依据**，由调用方决定如何呈现；
凡原典未言者，一律返回 ``None`` 并登记「原典无明文」，**不猜**。

⚠️ 替换关系：本模块取代 ``hexagram_state.get_base_factors`` 与
``interpretation._hexagram_base_score`` 中**无原典依据的自拟数值**
（静0.5/动0.7/变0.6/互0.4、乾0.8/坤0.6/震巽0.5/坎离0.4…）。
那些分数在任何原典条目中都找不到出处，属凭空捏造。
"""
from __future__ import annotations

from dataclasses import dataclass

# ═══════════════════════════════════════════════════════════════════
# 一、六项判据的定义与原文
# ═══════════════════════════════════════════════════════════════════

#: 六项判据名 → 原典出处（起例卷之中行号 + 原文摘录）
LIU_JU = {
    "卦名": (633, "一卦名吉"),
    "爻位": (636, "二爻吉。（如元堂住在二五爻是也。）"),
    "爻辞": (639, "三辞吉。（卦爻中有元吉亨利是也。）"),
    "得时": (642, "四得时。（如春震木、夏离火、秋兑金、冬坎水之类。"
                 "又如正月得泰卦、九月得剥卦之类皆是。）"),
    "有援": (645, "五有援。（谓元堂在阳爻，应爻得阴，"
                 "或元堂在阴爻，而应爻得阳是也。）"),
    "顺时": (648, "六顺时。（谓天地二数多寡与时偕行。"
                 "如正月生人得天数多地数少，九月生人得地数多天数少是也。）"),
}

#: 凶断对应项（L669「一卦名凶 二爻位凶 三辞凶 四不得时 五无援」）
XIU_JU = {
    "卦名": "一卦名凶",
    "爻位": "二爻位凶",
    "爻辞": "三辞凶",
    "得时": "四不得时",
    "有援": "五无援",
}

#: 爻位索引（0=初爻 … 5=上爻）→ 爻位名
_YAO_POS_NAME = ("初爻", "二爻", "三爻", "四爻", "五爻", "上爻")


#: 元堂爻「吉位」——原典 L636「元堂住在二五爻是也」
JI_YAO_GOOD = (1, 4)          # 二爻、五爻（爻位 0=初 … 5=上）

#: 一卦名吉 —— 原典 L633 明文列举五卦
#: 「一卦名吉。（如泰、大有、同人、晋、豫之类是也。）」
#: 注意原文用「**之类**」，即只举例未穷举；本表登记原文明举者，
#: 不据此断言其余卦皆凶。
GUA_MING_GOOD_EXAMPLES = ("泰", "大有", "同人", "晋", "豫")

#: 爻辞中的吉字——原典 L639「卦爻中有元吉亨利是也」
JI_CI_GOOD_CHARS = ("元吉", "亨利")


@dataclass(frozen=True)
class JuResult:
    """一项判据的判定结果。"""

    name: str                # 判据名：卦名/爻位/爻辞/得时/有援/顺时
    passed: bool | None      # True=吉, False=凶, None=原典未言/无法判定
    basis: str               # 原典依据（原文摘录）
    detail: str = ""         # 判定过程说明


def judge_yao_wei(yuantang_index: int) -> JuResult:
    """二爻位吉凶（原典 L636：「元堂住在二五爻是也」）。"""
    passed = yuantang_index in JI_YAO_GOOD
    return JuResult(
        name="爻位",
        passed=passed,
        basis=LIU_JU["爻位"][1],
        detail=f"元堂在{_YAO_POS_NAME[yuantang_index]}→ {'吉（二五爻）' if passed else '非二五爻'}",
    )


def judge_yao_ci(yao_ci: str) -> JuResult:
    """三辞吉凶（原典 L639：「卦爻中有元吉亨利是也」）。"""
    hit = [c for c in JI_CI_GOOD_CHARS if c in yao_ci]
    return JuResult(
        name="爻辞",
        passed=bool(hit),
        basis=LIU_JU["爻辞"][1],
        detail=f"爻辞含{hit[0] if hit else '无'}「元吉/亨利」",
    )


def judge_de_shi(
    trigram: str,
    month: int | None = None,
    gua_qi_month: int | None = None,
    season: str | None = None,
) -> JuResult:
    """四得时（原典 L642）。

    原典给**两类**得时的例：
      1. **卦气月得时**：「又如正月得泰卦、九月得剥卦之类皆是」
         ——即生月 == 该卦的卦气月（十二月卦气表见 ``guajie.GUA_QI_MONTH_TABLE``）。
         **此例可直接机械判定。**
      2. **四时正卦得时**：「如春震木、夏离火、秋兑金、冬坎水之类」
         ——「得时」条里**只给了四季的代表卦**，没在这条里写月份划分；
         但原典**别处**有可回查的月份分季引文链（见 ``SEASON_TRIGRAM_GUA``
         上方注释：「坤艮卦主四季辰戌丑未月」L189、「丑寅之分，季冬孟春之间」
         L416、「仲春之月」L12），可闭合到 寅卯辰春/巳午未夏/申酉戌秋/亥子丑冬。
         故本模块仍**只接受调用方显式传入季节**（``season`` 参数），
         **不在此处自行摊月** —— 摊月只允许调用方按上述引文链推衍后传入，
         免得各处各摊一套（口径统一由 ``guajie._SEASON_BY_BRANCH`` 承担）。

    ``month`` 为节气月（寅=正月…丑=十二月），与 guajie.BRANCH_TO_MONTH 同口径。
    """
    detail_parts: list[str] = []
    hit_qi = hit_season = False

    if month is not None and gua_qi_month is not None:
        hit_qi = (month == gua_qi_month)
        detail_parts.append(
            f"卦气月：生月{month} vs 卦气属{gua_qi_month}月 → {'合' if hit_qi else '不合'}")

    if season:
        season_gua = SEASON_TRIGRAM_GUA.get(season)
        if season_gua:
            hit_season = (trigram == season_gua)
            detail_parts.append(
                f"四时正卦：{season}当{season_gua} → {'合' if hit_season else '不合'}")
    else:
        detail_parts.append("四时正卦：未给季节（按上条裁定，不自行摊月）→ 未判")

    if not detail_parts:
        return JuResult("得时", None, LIU_JU["得时"][1], "缺生月或卦气月，无法判定")

    if not hit_qi and not hit_season and season is None:
        # 仅凭卦气月未合、且季节未给：返回 None 而非 False，不把「未判」当「不得时」
        return JuResult("得时", None, LIU_JU["得时"][1], "；".join(detail_parts))

    passed = hit_qi or hit_season
    return JuResult("得时", passed, LIU_JU["得时"][1], "；".join(detail_parts))


#: 四时正卦得时表（原典 L642**仅给春/夏/秋/冬四季**的代表卦，
#: 未在「得时」条里给月份划分规则，故键为季节而非月份）。
#:
#: 2026-10-22 原典取证补充：原典**别处**给出了月份分季的可回查引文链 ——
#: 「坤艮卦主四季辰戌丑未月」（起例卷之上 L189）、「艮乃丑寅之分，季冬孟春
#: 之间」（易卦释义·下经卷之下 L416）、「仲春之月」（起例卷之中 L12）——
#: 三处可逐环闭合到 **寅卯辰春 / 巳午未夏 / 申酉戌秋 / 亥子丑冬**。
#: 故本表所依据的**季节**不再算「引擎自定」，而是**依原典月令分季推衍**
#: （引擎只实现推衍结果，未改判词）。
SEASON_TRIGRAM_GUA: dict[str, str] = {
    "春": "震",   # 原典「春震木」
    "夏": "离",   # 原典「夏离火」
    "秋": "兑",   # 原典「秋兑金」
    "冬": "坎",   # 原典「冬坎水」
}


def ying_yao_index(yuantang_index: int) -> int:
    """应爻爻位（元堂隔三位）。

    原典依据（逐字，两例互证）：

      · 起例卷之上 L121「假如同人九三爻是元堂……二岁取应爻，变同人上九为革上六」
        → 同人卦九三（爻位 2）的应爻是上九（爻位 5）。
      · 起例卷之上 L126「又假如小象是泰卦九二，卦应爻居五」
        → 泰卦九二（爻位 1）的应爻居五（爻位 4）。

    两例的爻位差都是 3，故：**应爻 = 与元堂相隔三位之爻**（六爻内互为应）。

    注意：本函数只定位**爻位**；应爻的**阴阳**取自本卦该爻的爻性，
    须由调用方传入卦的六爻（见 :func:`judge_you_yuan` 的 ``+1/-1`` 约定）。
    """
    return (yuantang_index + 3) % 6


def judge_you_yuan(
    yuantang_line: int,
    ying_yao_line: int,
) -> JuResult:
    """五有援 / 五无援（原典 L645）。

    原文：「谓元堂在阳爻，应爻得阴，或元堂在阴爻，而应爻得阳是也。」

    即：元堂爻与应爻**阴阳相反**者谓之有援。
    ``yuantang_line`` / ``ying_yao_line`` 取 +1(阳) / -1(阴)。
    """
    passed = (yuantang_line * ying_yao_line) < 0
    return JuResult(
        name="有援",
        passed=passed,
        basis=LIU_JU["有援"][1],
        detail=f"元堂为{'阳' if yuantang_line > 0 else '阴'}爻、"
               f"应爻为{'阳' if ying_yao_line > 0 else '阴'}爻 → "
               f"{'阴阳相反，有援' if passed else '阴阳相同，无援'}",
    )


def judge_shun_shi(
    month: int,
    tian_shu: int,
    di_shu: int,
) -> JuResult:
    """六顺时（原典 L648）。

    原文逐字（**照录，不订正**）：

        六顺时。（谓天地二数多寡与时偕行。如正月生人得天数多地数少，
        **九月生人得地数多人数少**是也。）

    ⚠ **讹字留证**：九月那一句，原典转录本作「地数多**人**数少」——
    「人」当是「天」之讹。本实现的判读与下游文案一律作「天数少」，
    理由有二，两条都出自本句自身，不引外部：

      ① 本句前半已自限范围：「谓天地**二数**多寡与时偕行」。天地只有天数、
         地数二数，全句无第三个数叫「人数」，故「人数」无所指。
      ② 与前句「正月生人得天数多地数少」构成互文对仗：正月「天数多、地数少」，
         九月则应「地数多、天数少」，两两互换才成对；作「人数」则前句的
         「天数」在两句中各出现一次，句式失衡。

    ⚠ 因此**代码里的「天数少」是对讹字的订正，不是原文**。引用时必须连本条
    讹字说明一起引，不得径称「原典作天数少」——那会把一次订正伪装成原文，
    与本项目「讹误须留证」的规矩相反。

    ⚠️ **原典只给了正月、九月两例，未给出其余十个月的天数/地数多寡规则。**
    故本模块**只判定原文明文覆盖的正月与九月**，
    其余月份一律返回 ``passed=None`` 并注明「原典未言此月」——
    **绝不按「阳月令=天数多」自行推广**（那属推断，且正月与九月分属
    阳月令与阴月令两极，无法据此内插）。

    正月（雨水）、九月（霜降）均为原典明文所举之例。
    """
    KNOWN = {
        1: ("天数多地数少", tian_shu > di_shu,
            "原典「正月生人得天数多地数少」（L648 逐字，无讹）"),
        9: ("地数多天数少", di_shu > tian_shu,
            "原典 L648 逐字作「地数多**人**数少」——「人」为「天」之讹，"
            "据本句「天地二数」自限与上下句互文对仗订正为「天」；"
            "原典转录作「人」，此为讹字留证"),
    }
    if month not in KNOWN:
        return JuResult(
            name="顺时", passed=None, basis=LIU_JU["顺时"][1],
            detail=f"{month}月不在原典明文举例内（只举正月、九月两例），"
                   f"原典无明文规则 → 不判（实得天{tian_shu}地{di_shu}）")
    want, ok, basis = KNOWN[month]
    return JuResult(
        name="顺时", passed=ok, basis=LIU_JU["顺时"][1],
        detail=f"{basis}；{month}月应{want}；实得天{tian_shu}地{di_shu} → "
               f"{'合' if ok else '不合'}",
    )


def judge_liu_ju(
    *,
    gua_name: str = "",
    gua_ci: str = "",
    yuantang_index: int | None = None,
    yuantang_line: int | None = None,
    ying_yao_index: int | None = None,
    ying_yao_line: int | None = None,
    trigram: str = "",
    month: int | None = None,
    gua_qi_month: int | None = None,
    season: str | None = None,
    tian_shu: int | None = None,
    di_shu: int | None = None,
) -> dict[str, JuResult]:
    """一次性跑全部六项判据。

    原典未给出可机械判定的规则者（如「卦名吉」须依卦辞库逐卦断），
    返回 ``passed=None`` 并在 ``detail`` 注明「原典未言/需查卦辞库」，
    **绝不臆造分数**。
    """
    out: dict[str, JuResult] = {}

    out["卦名"] = JuResult(
        "卦名",
        True if gua_name in GUA_MING_GOOD_EXAMPLES else None,
        LIU_JU["卦名"][1],
        f"原文明举吉卦{GUA_MING_GOOD_EXAMPLES}（原文作「之类」=举例未穷举）；"
        f"当前卦={gua_name or '未传'}"
        + ("→ 落在原文明举之列" if gua_name in GUA_MING_GOOD_EXAMPLES
           else "→ 不在明举例内，但原典未言其余卦为凶，故不判"))

    if yuantang_index is not None:
        out["爻位"] = judge_yao_wei(yuantang_index)

    if gua_ci:
        out["爻辞"] = judge_yao_ci(gua_ci)

    if trigram and (month is not None or season):
        out["得时"] = judge_de_shi(trigram, month, gua_qi_month, season)

    if yuantang_line is not None and ying_yao_line is not None:
        out["有援"] = judge_you_yuan(yuantang_line, ying_yao_line)

    if month is not None and tian_shu is not None and di_shu is not None:
        out["顺时"] = judge_shun_shi(month, tian_shu, di_shu)

    return out


__all__ = [
    "LIU_JU", "XIU_JU", "JI_YAO_GOOD", "JI_CI_GOOD_CHARS",
    "SEASON_TRIGRAM_GUA", "JuResult",
    "judge_yao_wei", "judge_yao_ci", "judge_de_shi",
    "judge_you_yuan", "judge_shun_shi", "judge_liu_ju", "ying_yao_index",
]
