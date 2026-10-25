# -*- coding: utf-8 -*-
"""时间层判据：流年 / 流月 / 流日的**原典有据**方向判定（2026-10-25 新增）。

背景
----
诊断图注册了 ``HL_DAYUN`` / ``HL_LIUNIAN_GUA`` / ``HL_YUEGUA`` / ``HL_RIGUA``
四条时间层规则，但 ``HeLuoEvidenceProducer`` **从不产出**这四条证据
⇒ 四条注册是「注册了却不存在」的空授权；同时
``diagnosis_rule_graph.heluo_own_direction`` 也没有这四条的处理分支
⇒ 即使补了证据也进不了图。

而引擎侧**数据是齐备**的（``HeluoResult.timeline``）：
``yearly_hexagrams``（流年卦 + 大运段）、``monthly_hexagrams``（12 月卦）、
``daily_hexagram``（日卦段 + 逐日一爻）；判词层也已有四层的**爻辞**
（``guajie.liunian_yao`` / ``liuyue_yao`` / ``liuri_yao``）。

本模块补上**中间那一环**：把时间层卦的**爻辞**送进已有的原典判据
（``gui_ming_liu_ju`` 的「三辞吉」），得出**吉 / 凶 / 不判**。

原典依据（逐条可回查）
--------------------
① **判据本身**：《河洛真数·起例卷之上》L212
   「**三辞吉**（卦爻中有元吉亨利是也）」——即以**爻辞**含「元吉/亨利」
   为吉。已落码于 ``gui_ming_liu_ju``（``LIU_JU["爻辞"]``，
   另一底本行号 L639）。
② **凶断 counterparts**：同书 L222 贱命十体「一卦名凶　二爻位凶　**三辞凶**」；
   L254「凡流年先后天大象遇正对反对卦，更值**爻辞凶**，卦无元气化工，必死」。
   ⚠ 但这两处**只给名目、未给凶词门槛** ⇒ 本模块**不判凶**（见下纪律②）。
③ **为什么时间层可以这样判**：《河洛真数·起例卷之上》L122
   「大象虽佳…**不若流年佳**。（即小象行年爻也。）**流年若佳，未有不应之者。
   若流年多凶，大象身爻虽佳，亦奚以为。**」
   ⇒ 原典明确以**流年卦之吉凶**论休咎，且明言流年之吉凶**重于**大象。
④ **流月**：《河洛真数·起例卷之上》L123-L127「起月卦例」
   「凡起月卦，就年卦中前一位起，单月变爻，双月变应爻…」
   ⇒ 月卦是**有取法、有卦象**的一层，可同法取其爻辞。
⑤ **流日**：《河洛理数》日卦六日制（K3-448 L488／K3-447 L1154）
   「日卦者每月變五卦每卦管六日方成一月」⇒ 日卦亦是一卦一爻一层。

⚠ 三条硬纪律（与解读层接线同一口径）
----------------------------------------
1. **只给吉 / 凶 / 不判**，**绝不给 0–1 分数** —— 分数是自拟的，无原典依据。
2. **原典未言 ⇒ 不判**（``passed=None``），不得把「没判」当成「吉」或「凶」。
   尤其两条：
     · **「爻辞不含吉词」推不出「凶」** —— 原典 L257 明言
       「若**拘拘于爻辞吉凶，则失之矣**…爻辞或凶，则不免有灾眚，
       而于富贵天年不碍也」；且 L222「三辞凶」**只给名目未给门槛**
       ⇒ 本模块**恒不判凶**。
     · **吉的门槛极窄**：只认 L212 明列的「元吉」「亨利」两个**词组**，
       不按单字（否则「吉」字满篇皆吉，等于没判）。
3. **不复活自拟分数** —— 不引用 ``hexagram_state.get_base_factors`` /
   ``calculate_element_modifier``（已于 2026-10-07 作废）。

⚠ **边界**：本判据只判「该层该爻」的吉凶，**不判整命**。
   原典 L257 同段还明说「虽流年小象**全凭元气化工**」⇒ 时间层方向
   须与元气/化工合看；本模块只提供**有据的单项**，合看由上层决定。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .gui_ming_liu_ju import LIU_JU, JI_CI_GOOD_CHARS


#: 爻辞中的**吉**词（原典 L212「三辞吉」：卦爻中有元吉亨利是也）
#: 取自 ``gui_ming_liu_ju.JI_CI_GOOD_CHARS``（**按词组**匹配，不按单字）。
JI_CI_GOOD = tuple(JI_CI_GOOD_CHARS)


def _polarity_of(ci: str) -> tuple[Optional[str], Optional[str]]:
    """爻辞的极性 → (吉词, 凶词)。

    ⚠ **吉**的门槛取自原典 L212 明文：「卦爻中有**元吉亨利**是也」
      ⇒ 只认「元吉」「亨利」两个**词组**（不按单字，否则「吉」字满篇皆吉）。
      用 ``gui_ming_liu_ju.JI_CI_GOOD_CHARS``（判据层单一来源）。

    ⚠ **凶**在本包原典中**无门槛** ⇒ 本函数**恒不判凶**（返回 None）。

      为什么不用别处的凶词表硬凑：
        · 《起例卷之上》L222 贱命十体确有「三辞凶」一条，但**只给了名目，
          没给哪些辞算凶**；
        · L257 明言「若**拘拘于爻辞吉凶，则失之矣**…**爻辞或凶**，则不免有
          灾眚，而于富贵天年不碍也」⇒ 「爻辞或凶」是**灾害**的描述，
          不是「此爻即为凶断」的判定门槛；
        · 且爻辞凶语**无固定形态**：如「悔亡」是**吉语**（亡而悔消），
          「厉终有悔」是凶语，「困于葛藟」是凶语 —— 同一个「悔」字两义，
          单字词表**必然误判**。
      ⇒ 判凶需要**逐条语境**，本包无此判据 ⇒ **不判**。
      这与「卦名」判据同口径：原典举例未穷举者，不得据此判凶。

    Returns:
        (吉词 or None, 凶词 or None)。目前**恒有第二个分量为 None**。
    """
    text = ci or ""
    good = next((w for w in JI_CI_GOOD if w in text), None)
    return good, None




#: 三条时间层规则 → 原典出处（可回查）
SOURCE_REFS: Dict[str, str] = {
    "HL_LIUNIAN_GUA": (
        "起例卷之上·小象阳爻九年运行例（L121-L122「流年若佳，未有不应之者；"
        "若流年多凶，大象身爻虽佳，亦奚以为」）"
    ),
    "HL_YUEGUA": (
        "起例卷之上·起月卦例（L124-L127「单月变爻，双月变应爻」）"
    ),
    "HL_RIGUA": (
        "起例卷之下·起日卦定式（K3-448 L488／K3-447 L1154 "
        "「日卦者每月變五卦每卦管六日方成一月」）"
    ),
    "HL_DAYUN": (
        "起例卷之上·小象阳爻九年运行例（L121「阳爻九年，阴爻六年」）"
    ),
}

#: 爻辞判据的原文（用于证据里留痕，不只是引用）
_CI_BASIS = LIU_JU["爻辞"][1]


@dataclass(frozen=True)
class TimeLayerJudgment:
    """一层时间判定的结果。

    Attributes:
        rule_id:     诊断规则 id（HL_LIUNIAN_GUA 等）
        hexagram:    该层卦名（"" = 取不到）
        yao:         该层动爻名（"" = 取不到）
        ci:          该层动爻爻辞（"" = 取不到）
        passed:      True=吉 / False=凶 / **None=不判**（原典未言或取不到爻辞）
        basis:       判定依据（原文摘录）
        detail:      判定过程说明
        source_ref:  原典出处
    """

    rule_id: str
    hexagram: str = ""
    yao: str = ""
    ci: str = ""
    passed: Optional[bool] = None
    basis: str = ""
    detail: str = ""
    source_ref: str = ""

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "hexagram": self.hexagram,
            "yao": self.yao,
            "ci": self.ci,
            # ⚠ 只给三态，不给分数
            "passed": self.passed,
            "basis": self.basis,
            "detail": self.detail,
            "source_ref": self.source_ref,
        }


def judge_time_layer_by_ci(
    rule_id: str,
    hexagram: str = "",
    yao: str = "",
    ci: str = "",
    gua_ci_list: Optional[List[str]] = None,
) -> TimeLayerJudgment:
    """按**爻辞**判一层时间的吉凶（原典 L212「三辞吉」）。

    判法
    ----
    L212 的原文是「**卦爻中**有元吉亨利是也」——「卦爻」指**该卦的六爻**，
    故本判据按**卦级**执行：取该层卦的六爻爻辞，其中**有**「元吉」或「亨利」
    ⇒ **吉**。

    三态：

    * 该卦六爻辞含**吉词组**（元吉 / 亨利） ⇒ **吉**；
    * 其余 ⇒ **不判**（``passed=None``）。

    ⚠ 为什么**不判凶**（哪怕爻辞明显是凶语）：
      《河洛真数·起例卷之上》L222 贱命十体确有「三辞凶」一条，
      但**只给名目、未给哪些辞算凶**；L257 又明言
      「若**拘拘于爻辞吉凶，则失之矣**…**爻辞或凶**，则不免有灾眚，
      而于富贵天年不碍也」⇒ 「爻辞或凶」是**灾害**的描述，
      不是「此爻即为凶断」的门槛。
      且爻辞凶语**无固定形态**：「悔亡」是**吉语**（亡而悔消），
      「厉终有悔」是凶语 —— 同一个「悔」字两义，单字词表必然误判。
      ⇒ 本包**无单爻判凶之据** ⇒ 一律不判（宁可不判，不可编判）。
      这与「卦名」判据同口径：原典举例未穷举者，不得据此判凶。

    ⚠ **命中率低是原典实况，不是实现缺陷**：L212 的门槛极窄
      （只认「元吉」「亨利」两个词组），实测 64 卦中仅 **11 卦**的六爻辞
      含这两个词组 ⇒ 多数盘在时间层**判不出方向**，这是**如实反映**，
      不得为了提高命中率而放宽门槛（放宽即成自拟）。

    Args:
        rule_id:     诊断规则 id。
        hexagram:    该层卦名。
        yao:         该层动爻名。
        ci:          该层动爻爻辞（单爻，仅作留痕）。
        gua_ci_list: 该卦六爻爻辞（卦级判据的样本；缺省时退化为只看 ``ci``）。

    Returns:
        TimeLayerJudgment。``passed`` 为 True / None。
    """
    src = SOURCE_REFS.get(rule_id, "")
    ci = (ci or "").strip()

    # 卦级样本：六爻辞齐 ⇒ 按卦判；否则退化为单爻（并注明）
    sample = [c for c in (gua_ci_list or []) if c]
    scope = "卦级（六爻辞整体）"
    if not sample:
        sample = [ci] if ci else []
        scope = "单爻（未取到该卦六爻辞）"

    if not sample:
        return TimeLayerJudgment(
            rule_id=rule_id, hexagram=hexagram, yao=yao, ci="",
            passed=None,
            basis=_CI_BASIS,
            detail="无爻辞 ⇒ 不判（原典未言者不猜）",
            source_ref=src,
        )

    good_hit = None
    for c in sample:
        hit = next((w for w in JI_CI_GOOD if w in c), None)
        if hit:
            good_hit = hit
            break

    if good_hit:
        return TimeLayerJudgment(
            rule_id=rule_id, hexagram=hexagram, yao=yao, ci=ci,
            passed=True,
            basis=_CI_BASIS,
            detail="该卦爻辞含吉词「%s」⇒ 吉（原典 L212「卦爻中有元吉亨利是也」；"
                   "判据为**卦级**，按**词组**匹配；样本口径：%s）"
                   % (good_hit, scope),
            source_ref=src,
        )

    return TimeLayerJudgment(
        rule_id=rule_id, hexagram=hexagram, yao=yao, ci=ci,
        passed=None,
        basis=_CI_BASIS,
        detail="该卦爻辞无「元吉/亨利」⇒ **不判**"
               "（原典 L257「若拘拘于爻辞吉凶，则失之矣」——"
               "不得由「没命中吉辞」反推为凶；门槛窄是原典实况，不得放宽；"
               "样本口径：%s）" % scope,
        source_ref=src,
    )


# ═══════════════════════════════════════════════════════════════
# 从引擎数据抽取四层
# ═══════════════════════════════════════════════════════════════

def _yao_ci_from_guajie(guajie: Any, attr: str) -> tuple[str, str]:
    """从判词层取出某层的 (爻名, 爻辞)。取不到返回 ("", "")。"""
    obj = getattr(guajie, attr, None) if guajie is not None else None
    if obj is None and isinstance(guajie, dict):
        obj = guajie.get(attr)
    if obj is None:
        return ("", "")
    yao = getattr(obj, "yao", "") or ""
    ci = getattr(obj, "ci", "") or ""
    if isinstance(obj, dict):
        yao = obj.get("yao", "") or yao
        ci = obj.get("ci", "") or ci
    return (yao, ci)


def _hexagram_from_guajie(guajie: Any, attr: str) -> str:
    obj = getattr(guajie, attr, None) if guajie is not None else None
    if obj is None and isinstance(guajie, dict):
        obj = guajie.get(attr)
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    return getattr(obj, "hexagram", "") or getattr(obj, "name", "") or ""


def _gua_ci_list(guajie: Any, gua_name: str) -> List[str]:
    """取某卦的**六爻爻辞**（L212「卦爻中」的样本）。

    优先用判词层已加载的 ``load_guajie_data()``（判词层单一来源）；
    取不到返回空列表（调用方退化为单爻）。
    """
    if not gua_name:
        return []
    try:
        from .guajie import load_guajie_data
        data = load_guajie_data()
    except Exception:
        return []
    g = data.get(gua_name)
    if g is None:
        return []
    yaos = getattr(g, "yaos", None) or {}
    if isinstance(yaos, dict):
        values = yaos.values()
    else:
        values = yaos
    out: List[str] = []
    for y in values:
        ci = getattr(y, "ci", "") or ""
        if ci:
            out.append(ci)
    return out


#: 爻位索引（0=初爻 … 5=上爻）→ 爻位名。
#:
#: ⚠ 2026-10-25 合并：此前本文件有**两张内容完全相同**的表
#:   （``_YAO_NAME_BY_IDX`` 与 ``_YAO_NAME_BY_IDX_FULL``），
#:   且 ``_YAO_NAME_BY_IDX`` 还被**重复定义**了两次
#:   —— Ruff F811 / mypy no-redef 都报了。
#:   另：原注释写「取自判词层的爻名表（判词层单一来源）」**与事实不符**
#:   （本表内容就是「初爻…上爻」，并非判词层的「初九/六二…」爻名），
#:   注释会误导后来者以为存在一个「判词层爻名表」被依赖。
#:   ⇒ 合并为一张表，注释改为如实描述。
_YAO_NAME_BY_IDX: Dict[int, str] = {
    0: "初爻", 1: "二爻", 2: "三爻", 3: "四爻", 4: "五爻", 5: "上爻",
}


def _timeline_target_year(tl: Any) -> Optional[dict]:
    """从 timeline 取**目标年**的流年数据。

    优先按 ``timeline.target_year_hexagram`` 匹配；取不到则用**最后一条**
    （``yearly_hexagrams`` 是升序，最后一条 = 目标年）。
    """
    if tl is None:
        return None
    ys = getattr(tl, "yearly_hexagrams", None) or []
    if not ys:
        return None
    target = getattr(tl, "target_year_hexagram", None)
    if target:
        for y in ys:
            if isinstance(y, dict) and y.get("year") == target:
                return y
    last = ys[-1]
    return last if isinstance(last, dict) else None


def collect_time_layer_judgments(
    result: Any,
    guajie: Any = None,
) -> List[TimeLayerJudgment]:
    """抽出三层时间判定（流年 / 流月 / 流日）。

    数据来源**双通道**（判词层优先，timeline 兜底）：

    * 判词层（``result.guajie``）—— 含**动爻爻辞**（判词层的强项）；
    * ``result.timeline`` —— 含**流年卦 / 行年爻 / 十二月卦**（引擎的强项）。

    ⚠ 为何必须双通道：``HeluoCanonical.calculate()`` **直调**时
      ①不挂判词层、②无 ``target_date`` ⇒ 时序层只算年不算月/日；
      此时判词层的流月/流日为空，但 ``timeline`` 里**仍有时序数据**。
      只走判词层 ⇒ 直调场景下时间层证据整体丢失（实测如此）。

    只产出**有据**的判定：爻辞取不到 ⇒ ``passed=None``（不判），
    绝不臆造方向。

    Returns:
        list[TimeLayerJudgment]（顺序：流年 → 流月 → 流日）。
    """
    # ⚠ 2026-10-25：``getattr`` 的默认值只对「属性不存在」生效；
    #   属性访问**本身抛异常**时会穿透 ⇒ 本模块自己兜住，
    #   免得把异常甩给调用方（缺失被当成正常，比答错更坏）。
    if guajie is None:
        try:
            guajie = getattr(result, "guajie", None)
        except Exception:
            guajie = None

    try:
        tl = getattr(result, "timeline", None)
    except Exception:
        tl = None
    out: List[TimeLayerJudgment] = []

    # ── 流年 ──────────────────────────────────────────────────────
    y_yao, y_ci = _yao_ci_from_guajie(guajie, "liunian_yao")
    y_gua = _hexagram_from_guajie(guajie, "liunian_hexagram")
    y_row = _timeline_target_year(tl) or {}
    if not y_gua:
        y_gua = y_row.get("hexagram", "") or ""
    if not y_yao:
        _idx = y_row.get("xingnian_yao_index")
        if _idx is not None:
            y_yao = _YAO_NAME_BY_IDX.get(int(_idx), "") or ""
    out.append(judge_time_layer_by_ci(
        "HL_LIUNIAN_GUA",
        hexagram=y_gua, yao=y_yao, ci=y_ci,
        gua_ci_list=_gua_ci_list(guajie, y_gua),
    ))

    # ── 流月 ──────────────────────────────────────────────────────
    m_yao, m_ci = _yao_ci_from_guajie(guajie, "liuyue_yao")
    m_gua = _hexagram_from_guajie(guajie, "liuyue_hexagram")
    if not m_gua:
        _months = y_row.get("months") or []
        _target_month = getattr(tl, "daily_hexagram", None) or {}
        _m_no = _target_month.get("month") if isinstance(_target_month, dict) else None
        for m in _months:
            if isinstance(m, dict) and (_m_no is None or m.get("month") == _m_no):
                m_gua = m.get("name", "") or ""
                _mi = m.get("yue_yao_index")
                if not m_yao and _mi is not None:
                    m_yao = _YAO_NAME_BY_IDX.get(int(_mi), "") or ""
                break
    out.append(judge_time_layer_by_ci(
        "HL_YUEGUA",
        hexagram=m_gua, yao=m_yao, ci=m_ci,
        gua_ci_list=_gua_ci_list(guajie, m_gua),
    ))

    # ── 流日 ──────────────────────────────────────────────────────
    d_yao, d_ci = _yao_ci_from_guajie(guajie, "liuri_yao")
    d_gua = _hexagram_from_guajie(guajie, "liuri_hexagram")
    if not d_gua:
        _dh = getattr(tl, "daily_hexagram", None) or {}
        _base = _dh.get("base_hex") if isinstance(_dh, dict) else None
        if isinstance(_base, dict):
            d_gua = _base.get("name", "") or ""
    out.append(judge_time_layer_by_ci(
        "HL_RIGUA",
        hexagram=d_gua, yao=d_yao, ci=d_ci,
        gua_ci_list=_gua_ci_list(guajie, d_gua),
    ))

    return out


def collect_dayun_judgment(
    result: Any,
) -> TimeLayerJudgment:
    """大运层判定。

    ⚠ 大运方向**目前不判**（``passed=None``），理由：
      原典对大运的表述是**年数的更替**（L121「阳爻九年，阴爻六年」、
      「至十岁换九四爻…」），给出的是**取法**（哪个爻当值），
      **不是**吉凶判据；把爻辞判据套到「大运所值之爻」上，
      等于用「年卦的爻辞」代替「大运之吉凶」——那是**换一个对象**，
      不是同一个对象的另一种判法。原典里大运的吉凶要靠
      「小象与大象反对」等**专门条目**（L「如后天之气数行至君爻之位…」），
      该条目本包**未切** ⇒ 无据不判。

      但**大运所值之爻**这一**事实**仍产出（进诊断图的证据环），
      供平台侧作时间轴定位。

    Returns:
        TimeLayerJudgment（``passed`` 恒为 None）。
    """
    try:
        tl = getattr(result, "timeline", None)
    except Exception:
        tl = None
    hexagram = ""
    yao = ""
    detail = "大运层无吉凶判据（原典只给取法不给门槛）⇒ 不判"

    ys = getattr(tl, "yearly_hexagrams", None) or []
    if ys:
        last = ys[-1] if isinstance(ys, list) else None
        if isinstance(last, dict):
            hexagram = last.get("hexagram", "") or ""
            idx = last.get("dayun_seg_yuantang_index")
            if idx is not None:
                yao = _YAO_NAME_BY_IDX.get(idx, "") or ""

    return TimeLayerJudgment(
        rule_id="HL_DAYUN",
        hexagram=hexagram,
        yao=yao,
        ci="",
        passed=None,
        basis="起例卷之上·小象阳爻九年运行例（L121）",
        detail=detail,
        source_ref=SOURCE_REFS["HL_DAYUN"],
    )


