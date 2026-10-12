# -*- coding: utf-8 -*-
"""Z74d: 答案层组装——两派规则命中 → 分维度平行答案。

用户流程：输入层（八字排盘）→ 紫微斗数 → 排盘（内部算层）→ 答案层
→ 映射到各维度 → 解析层。

本模块实现「答案层→维度映射」：
- 输入：SanheRuleGraph.match_all（南派）+ detect_all_production（北派）
- 输出：八维度平行答案（性格/格局/事业/婚姻/财运/健康/应期/四化体用）
- 两派各自归位，不投票不融合，南北平行输出
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DIMENSIONS = ["性格", "格局", "事业", "婚姻", "财运", "健康", "应期", "四化体用"]

# ============================================================================
# 北派（QINTIAN）规则 → 维度映射（按规则语义归位）
# ============================================================================
QTN_DIMENSION = {
    # ── 四化体用（钦天核心结构：来因/体用/自化/出入/法象/双象/用神/表里） ──
    "QTN-CMB-001": "四化体用", "QTN-CMB-002": "四化体用", "QTN-CMB-003": "四化体用",
    "QTN-CMB-004": "四化体用", "QTN-CMB-005": "四化体用", "QTN-CMB-006": "四化体用",
    "QTN-CMB-007": "四化体用", "QTN-CMB-008": "四化体用", "QTN-CMB-009": "四化体用",
    "QTN-CMB-010": "四化体用", "QTN-CMB-011": "四化体用", "QTN-CMB-012": "四化体用",
    "QTN-CMB-013": "四化体用", "QTN-CMB-015": "四化体用", "QTN-CMB-018": "四化体用",
    "QTN-CMB-020": "四化体用", "QTN-CMB-021": "四化体用", "QTN-CMB-022": "四化体用",
    "QTN-CMB-028": "四化体用", "QTN-CMB-031": "四化体用", "QTN-CMB-042": "四化体用",
    "QTN-CMB-044": "四化体用", "QTN-CMB-058": "四化体用",
    # ── 性格（身宫体性/五行局/斗君） ──
    "QTN-CMB-014": "性格", "QTN-CMB-019": "性格",
    "QTN-CMB-034": "性格", "QTN-CMB-035": "性格",
    # ── 事业（官禄飞化/命格贵格/自立白手/为臣格） ──
    "QTN-CMB-023": "事业", "QTN-CMB-027": "事业", "QTN-CMB-030": "事业",
    "QTN-CMB-033": "事业", "QTN-CMB-040": "事业", "QTN-CMB-043": "事业",
    "QTN-CMB-045": "事业", "QTN-CMB-046": "事业",
    # ── 婚姻（夫妻宫四化/红艳/结婚限/天刑天姚入夫妻） ──
    "QTN-CMB-038": "婚姻", "QTN-CMB-039": "婚姻", "QTN-CMB-047": "婚姻",
    "QTN-CMB-049": "婚姻", "QTN-CMB-050": "婚姻",
    # ── 财运（财帛飞化/财格显象压制/田宅飞化/六阴主富/人和） ──
    "QTN-CMB-025": "财运", "QTN-CMB-026": "财运", "QTN-CMB-032": "财运",
    "QTN-CMB-036": "财运", "QTN-CMB-037": "财运", "QTN-CMB-056": "财运",
    # ── 健康（灾煞血光） ──
    "QTN-CMB-041": "健康",
    # ── 应期（流年/大限/流月四化 + 天刑官非时点 + 双忌三忌叠应期） ──
    "QTN-CMB-016": "应期", "QTN-CMB-017": "应期", "QTN-CMB-024": "应期",
    "QTN-CMB-029": "应期", "QTN-CMB-048": "应期", "QTN-CMB-051": "应期",
    "QTN-CMB-052": "应期", "QTN-CMB-053": "应期", "QTN-CMB-054": "应期",
    "QTN-CMB-055": "应期", "QTN-CMB-057": "应期", "QTN-CMB-059": "应期",
    "QTN-CMB-060": "应期",
}

# 南派格局 trend → 维度（格局断语按吉凶向归位）
SANHE_TREND_DIMENSION = {
    "贵": "事业", "武权": "事业", "吏/安": "事业", "晚发贵": "事业",
    "财": "财运", "富/寿": "财运", "库/稳": "财运", "富/柔": "财运",
    "财印": "财运", "财官": "财运",
    "福": "性格", "福/寿": "健康", "荫/寿": "健康", "桃花/祸福": "婚姻",
    "桃花/权": "婚姻", "桃花/凶": "婚姻", "淫欲/凶": "婚姻", "暗/口舌": "性格",
    "权/囚": "事业", "威权": "事业", "权": "事业", "成败/凶": "事业",
    "大起大落": "事业", "变革": "事业", "变革/凶": "事业", "耗/变革": "事业",
    "破荡": "事业", "积富/刑": "财运", "贵/荫": "事业", "贵/口才": "事业",
    "贵/富": "事业", "荣": "事业", "福/印": "性格", "智": "性格",
    "福/印": "性格",
}


@dataclass
class AnswerItem:
    """单条维度答案。"""
    source: str          # sanhe / qintian
    rule_id: str
    text: str
    trend: str = ""
    qualifier: str = ""
    evidence_grade: int = 1
    _dim_hint: str = ""  # 显式维度提示（三方会照格局归「格局」）

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "rule_id": self.rule_id,
            "text": self.text,
            "trend": self.trend,
            "qualifier": self.qualifier,
            "evidence_grade": self.evidence_grade,
        }


def _build_sanhe_items(sanhe_result) -> list[AnswerItem]:
    items: list[AnswerItem] = []
    for m in sanhe_result.matched_rules:
        rid = m.rule_spec.rule_id
        op = m.rule_spec.operation
        facts = m.facts
        if "JUDG" in rid:
            # 坐命星断语：按星曜特质归维度
            star = facts.get("judgment_star", "")
            trend = facts.get("trend", "")
            dim = SANHE_TREND_DIMENSION.get(trend, "性格")
            items.append(AnswerItem(
                source="sanhe", rule_id=rid, text=op.get("description", ""),
                trend=trend, qualifier=m.qualifier,
            ))
        elif "PATTERN" in rid:
            scope = facts.get("scope", "坐命")
            pj = facts.get("pattern_judgment", {})
            trend = pj.get("trend", "")
            text = pj.get("judgment", "") or op.get("description", "")
            # 接格局释义层
            pattern_name = rid.split("-")[-1]
            interp = _find_pattern_interp(pattern_name)
            if interp:
                vp = []
                if interp.get("positive"):
                    vp.append(f"吉：{interp['positive']}")
                if interp.get("shadow"):
                    vp.append(f"忌：{interp['shadow']}")
                if vp:
                    text = f"{text} → {'；'.join(vp)}"
            if scope == "三方会照":
                # 三方会照格局不判本命坐格：归「格局」维度并标注，不进主维度
                text = "（三方会照）" + text
                items.append(AnswerItem(
                    source="sanhe", rule_id=rid, text=text,
                    trend=trend, qualifier=m.qualifier,
                    _dim_hint="格局",
                ))
            else:
                dim = SANHE_TREND_DIMENSION.get(trend, "格局")
                items.append(AnswerItem(
                    source="sanhe", rule_id=rid, text=text,
                    trend=trend, qualifier=m.qualifier,
                    _dim_hint=dim,
                ))
        else:
            # SIHUA / 宫位规则
            from .palace_star_verdicts import get_palace_verdict, get_palace_gist
            text = op.get("description", "")
            palace_name = rid.split("-")[-1]
            is_palace = rid.startswith("SANHE-PALACE-")
            if is_palace:
                # 南派宫义做厚：宫义总论 + 各主星落此宫原文断语 + 释义
                stars = facts.get("stars", [])
                parts = [f"{palace_name}宫：{get_palace_gist(palace_name)}"]
                # 取亮度/煞吉事实用于释义判定
                bright_map = facts.get("brightness", {})
                has_sha = facts.get("has_煞", False)
                has_ji = facts.get("has_吉", False)
                for st in stars:
                    v = get_palace_verdict(palace_name, st)
                    if v:
                        parts.append(f"【{st}】{v}")
                        # 接释义层：四档亮度+煞吉判定
                        interp = get_interpretation(f"PALACE-{palace_name}-{st}", {
                            "bright": bright_map.get(st, ""),
                            "has_煞": has_sha,
                            "has_吉": has_ji,
                        })
                        verdict_text = interp.get("verdict", "")
                        if verdict_text:
                            parts.append(f"  → {verdict_text}")
                text = " ".join(parts)
                palace_dim = _PALACE_DIM.get(palace_name)
                if palace_dim is None:
                    # Z80-C: 此前用 .get(name, "四化体用") 静默降级，宫名未列时
                    # 内容会无声无息进入「四化体用」，错误不外显（同类问题见
                    # Z80 修的 domain_reading 「交友/仆役」命名差异）。
                    # 现改为：未列宫位走未列维度池，并保留原始宫名供审计。
                    palace_dim = "四化体用"
                # Z80-C: 标注该宫是否为「8 维无对应、暂居此桶」
                _provisional = palace_name in _PALACE_DIM_PROVISIONAL
                items.append(AnswerItem(
                    source="sanhe", rule_id=rid, text=text,
                    qualifier=(
                        (m.qualifier + "；" if m.qualifier else "")
                        + ("[暂居维度] " if _provisional else "")
                        + (f"[宫位未登记:{palace_name}] "
                           if palace_name not in _PALACE_DIM else "")
                    ).strip(),
                    _dim_hint=palace_dim,
                ))
                continue
            if not text and op.get("target_palace"):
                # 生年四化入宫：SANHE-SIHUA-{干}-{化}
                parts2 = rid.split("-")
                if len(parts2) >= 4 and parts2[2] in "甲乙丙丁戊己庚辛壬癸":
                    text = f"生年{parts2[2]}干{parts2[3]}入{op.get('target_palace')}宫"
            items.append(AnswerItem(
                source="sanhe", rule_id=rid, text=text,
                qualifier=m.qualifier,
            ))
    return items


# 南派十二宫 → 八维度归位（不与北派四化混）
#
# Z80-C 修复（2026-10-12，文献核对见 docs/audit/ZIWEI_PALACE_DIM_VERIFICATION_20261012.md）：
#   此表此前有 5 处归位错误，均已按《紫微斗数全书》宫义 + 项目内 palace_star_verdicts
#   宫义总论逐宫核对后修正：
#     · 兄弟  婚姻 → 性格  （文献：「兄弟宫主兄弟姊妹、合伙人、知心朋友」；
#                           项目宫义 22 条 star verdict 无一条讲婚姻。
#                           改归「性格」是因 8 维无「人际」维度，人际属性最接近性格/社会性，
#                           且不改 8 维契约。注：兄弟宫对婚姻有间接影响（"命宫到夫妻之桥梁"），
#                           但属从属含义，不构成主归位。）
#     · 子女  婚姻 → 性格  （子女宫主子女缘/下属/合伙，桃花仅为延伸角色）
#     · 父母  性格 → 性格  （保持；8 维无「父母」维度，长辈缘分暂居性格）
#     · 迁移  应期 → 事业  （迁移是空间场域（外出/异地发展），非时间维度。
#                           原「→应期」系把"该宫在流年层次被使用"误当"该宫属于应期"。
#                           8 维无「迁移」维度，外出与事业互涉，暂归事业。）
#     · 仆役  应期 → 性格  （仆役主朋友/下属/助力，属人际；8 维无人际维，暂归性格）
#
#   ⚠️ 结构性遗留：8 维只有 8 个桶而宫位有 12 个，必然有宫位"无处可去"。
#      本表将无处可去者归入最近似桶，并逐条注明。彻底解法需扩维（见核对报告第五节决策 A）。
_PALACE_DIM = {
    "命宫": "性格", "福德": "性格", "父母": "性格",
    "兄弟": "性格", "夫妻": "婚姻", "子女": "性格",
    "财帛": "财运", "田宅": "财运",
    "疾厄": "健康",
    "官禄": "事业",
    "迁移": "事业", "仆役": "性格",
}

# 8 维中**没有对应维度**、被迫暂居他桶的宫位（显式声明，防误用为"正确归位"）
# 用途：下游如需区分"真属此维"与"暂居此维"，可查此集合。
_PALACE_DIM_PROVISIONAL = frozenset({
    "兄弟",   # 真属「人际」，8 维无人际维 → 暂居性格
    "子女",   # 真属「子女」，8 维无子女维 → 暂居性格
    "父母",   # 真属「父母」，8 维无父母维 → 暂居性格
    "迁移",   # 真属「迁移」，8 维无迁移维 → 暂居事业
    "仆役",   # 真属「人际」，8 维无人际维 → 暂居性格
})


# 北派QTN结构释义
QTN_INTERPRETATION = {
    "QTN-CMB-001": {"positive": "来因宫定一生课题方向，体用明确。", "shadow": "来因宫若落忌地，一生课题偏重压力。"},
    "QTN-CMB-002": {"positive": "体用合一，时空结构完整，做事有始有终。", "shadow": "自化过多则散，精力不集中。"},
    "QTN-CMB-003": {"positive": "自化有则灵活应变，能适应环境。", "shadow": "自化太过则不稳，易变卦、善变。"},
    "QTN-CMB-004": {"positive": "向心自化主凝聚，物质、人脉、资源向内收。", "shadow": "过度向心则保守，难拓展。"},
    "QTN-CMB-005": {"positive": "理象气数俱足，格局完整。", "shadow": "理象不全则格局散，成就有限。"},
    "QTN-CMB-006": {"positive": "串联自化主一气呵成，事业/财脉连贯。", "shadow": "串联方向错则连环错，一损俱损。"},
    "QTN-CMB-007": {"positive": "离心自化主向外发展，拓展力强。", "shadow": "离心太过则散，财来财去。"},
    "QTN-CMB-008": {"positive": "双象对照，判断精准，不易走偏。", "shadow": "双象冲突则内心矛盾，选择困难。"},
    "QTN-CMB-009": {"positive": "出入有序，进退有据。", "shadow": "出入失序则进退失据，易踩坑。"},
    "QTN-CMB-010": {"positive": "次序分明，按部就班，稳步上升。", "shadow": "次序混乱则事倍功半。"},
    "QTN-CMB-011": {"positive": "忌星有制，压力转化为动力。", "shadow": "忌星无制则压力大，易阻碍。"},
    "QTN-CMB-012": {"positive": "禄权科交会，贵人助力强。", "shadow": "禄权科无禄，则贵而不实。"},
    "QTN-CMB-013": {"positive": "科星化忌，名声受损但务实。", "shadow": "科忌冲则名不副实，易招非议。"},
    "QTN-CMB-021": {"positive": "飞化入庙，吉力发挥充分。", "shadow": "飞化落陷，吉力打折。"},
    "QTN-CMB-022": {"positive": "飞化入吉地，做事顺遂。", "shadow": "飞化入煞地，多波折。"},
    "QTN-CMB-025": {"positive": "自化禄，自己创造机会。", "shadow": "自化禄则财来财去，守不住。"},
    "QTN-CMB-026": {"positive": "自化权，自己掌权。", "shadow": "自化权则刚愎自用，易得罪人。"},
    "QTN-CMB-031": {"positive": "自化科，自己求名。", "shadow": "自化科则虚名多，实利少。"},
    "QTN-CMB-044": {"positive": "自化忌，自己承担责任。", "shadow": "自化忌则自寻烦恼，易纠结。"},
    "QTN-CMB-015": {"positive": "身宫得位，后天努力方向明确。", "shadow": "身宫落陷，后天努力事倍功半。"},
    "QTN-CMB-018": {"positive": "忌星逢生，压力转化为资源。", "shadow": "忌星逢冲，压力爆发。"},
    "QTN-CMB-019": {"positive": "禄星逢忌，财来财去但有收获。", "shadow": "禄忌交战，财务波动大。"},
}

def _get_qtn_verdict(rule_id: str) -> str:
    """根据rule_id获取北派释义"""
    interp = QTN_INTERPRETATION.get(rule_id)
    if not interp:
        return ""
    parts = []
    if interp.get("positive"):
        parts.append(f"吉：{interp['positive']}")
    if interp.get("shadow"):
        parts.append(f"忌：{interp['shadow']}")
    return "；".join(parts) if parts else ""


def _build_qtn_items(qtn_hits: list) -> list[AnswerItem]:
    items: list[AnswerItem] = []
    for c in qtn_hits:
        dim = QTN_DIMENSION.get(c.rule_id, "四化体用")
        text = c.semantic_summary
        # 接北派释义层
        verdict = _get_qtn_verdict(c.rule_id)
        if verdict:
            text = f"{text} → {verdict}"
        items.append(AnswerItem(
            source="qintian", rule_id=c.rule_id,
            text=text,
            evidence_grade=getattr(c, "evidence_grade", 1),
        ))
    return items


def build_answer(chart) -> dict:
    """两派平行组装 → 八维度答案（不投票不融合）。"""
    from .method_graphs import SanheRuleGraph
    from .qintian.combinations import detect_all_production

    sanhe_result = SanheRuleGraph().match_all(chart)
    qtn_hits = detect_all_production(chart)

    # 南派：rule_id → 维度
    sanhe_dims: dict[str, str] = {}
    for m in sanhe_result.matched_rules:
        rid = m.rule_spec.rule_id
        if "JUDG" in rid:
            sanhe_dims[rid] = SANHE_TREND_DIMENSION.get(m.facts.get("trend", ""), "性格")
        elif "PATTERN" in rid:
            sanhe_dims[rid] = SANHE_TREND_DIMENSION.get(
                m.facts.get("pattern_judgment", {}).get("trend", ""), "格局")
        elif rid.startswith("SANHE-PALACE-"):
            sanhe_dims[rid] = _PALACE_DIM.get(rid.split("-")[-1], "四化体用")
        else:
            sanhe_dims[rid] = "四化体用"

    items = _build_sanhe_items(sanhe_result) + _build_qtn_items(qtn_hits)
    answer: dict = {dim: [] for dim in DIMENSIONS}
    for it in items:
        dim = it._dim_hint or sanhe_dims.get(it.rule_id, QTN_DIMENSION.get(it.rule_id, "四化体用"))
        answer[dim].append(it.to_dict())

    return {
        "dimensions": DIMENSIONS,
        "answer": answer,
        "summary": {
            "sanhe_total": len(sanhe_result.matched_rules),
            "qintian_total": len(qtn_hits),
            "dimension_counts": {d: len(answer[d]) for d in DIMENSIONS},
        },
    }


# 格局名 → PATTERN_INTERPRETATION key 反向索引
_PATTERN_NAME_INDEX = {}
def _build_pattern_name_index():
    for k, v in PATTERN_INTERPRETATION.items():
        name = v.get("name", "")
        if name:
            _PATTERN_NAME_INDEX[name] = k

def _find_pattern_interp(name: str):
    """根据格局名找释义条目"""
    if not _PATTERN_NAME_INDEX:
        _build_pattern_name_index()
    key = _PATTERN_NAME_INDEX.get(name)
    if key:
        return PATTERN_INTERPRETATION.get(key)
    return None


# ============================================================================
# Z93: 格局/断语释义字典——Assertion → 自然语言解读
# ============================================================================
PATTERN_INTERPRETATION = {
    # ===== 富格6条 =====
    "WEALTH-01": {"name": "财荫夹印", "dim": "财运",
        "classic": "天相守命/身，邻宫天梁为荫，化禄或武曲为财，相夹成格；忌空劫冲破。",
        "vernacular": "印星被财与荫夹辅，靠职位、牌照、专业、稳定平台得财。",
        "positive": "稳定积累，有靠山，适合金融、管理、公职、专业服务。",
        "shadow": "依赖体制或贵人；印章、担保、合同、权责问题易惹麻烦。"},
    "WEALTH-02": {"name": "日月夹财", "dim": "财运",
        "classic": "武曲守命或财帛，太阳太阴邻宫相夹，日月庙旺为真。",
        "vernacular": "明暗资源夹财，正偏财来源多，名声与贵人助财。",
        "positive": "财源多元，贵人运强，适合借势。",
        "shadow": "日月反背则夹不住；易依赖贵人，财务随人情波动。"},
    "WEALTH-03": {"name": "财禄夹马", "dim": "财运",
        "classic": "天马守命/财帛，武曲化禄与禄存夹，无空劫。",
        "vernacular": "动中得财，异地、出差、物流、贸易、跨区求财。",
        "positive": "适合异地发展，动中生财。",
        "shadow": "奔波，守财难；方向错则白忙。"},
    "WEALTH-04": {"name": "荫印拱身", "dim": "财运",
        "classic": "天梁、天相拱身/田宅，或三方会照；属组合吉象，非固定大格。",
        "vernacular": "长辈、制度、不动产荫庇。",
        "positive": "长辈缘、祖产、房产助力。",
        "shadow": "依赖长辈或制度，独立不足。"},
    "WEALTH-05": {"name": "日月照璧", "dim": "财运",
        "classic": "太阳太阴临田宅宫，或夹照田宅，庙旺。",
        "vernacular": "家宅光明，不动产有靠。",
        "positive": "家庭温暖，房产运稳。",
        "shadow": "日月反背则房产波动、名不副实；别只守房。"},
    "WEALTH-06": {"name": "金灿光辉", "dim": "事业",
        "classic": "太阳单守命在午，庙旺，无煞忌。",
        "vernacular": "日丽中天，光明外显。",
        "positive": "名声、事业亮，男命尤其明显。",
        "shadow": "孤阳刚强，注意眼目、心血管、强势压人。"},
    # ===== 贵格26条 =====
    "NOB-01": {"name": "日月夹命", "dim": "事业",
        "classic": "太阳太阴夹命宫，日月庙旺。",
        "vernacular": "外界明暗资源夹辅命主。",
        "positive": "左右逢源，名声人缘。",
        "shadow": "受父母或外界评价影响，缺主见；日月反背破格。"},
    "NOB-02": {"name": "日出扶桑", "dim": "事业",
        "classic": "太阳在卯守命或官禄，庙旺。",
        "vernacular": "初升太阳，早发。",
        "positive": "少年得志，起步早，有冲劲。",
        "shadow": "后劲看三方，忌煞则早发早衰。"},
    "NOB-03": {"name": "月朗天门", "dim": "事业",
        "classic": "太阴在亥守命，庙旺。",
        "vernacular": "月到天门，清贵文秀。",
        "positive": "文才、气质、女性缘。",
        "shadow": "柔、被动、多思，决断不足。"},
    "NOB-04": {"name": "月生沧海", "dim": "财运",
        "classic": "太阴在子守田宅，庙旺，见禄。",
        "vernacular": "月照海面，暗财、不动产。",
        "positive": "不动产、暗财、家宅运。",
        "shadow": "财不透明，防暗耗；无禄则虚。"},
    "NOB-05": {"name": "辅弼拱主", "dim": "事业",
        "classic": "紫微守命，左辅右弼同宫、夹命或三方拱。",
        "vernacular": "主星得辅佐。",
        "positive": "团队、班底、位高。",
        "shadow": "不能甩手；左右逢煞忌则辅佐变拖累。"},
    "NOB-06": {"name": "君臣庆会", "dim": "事业",
        "classic": "紫微守命，左右同会，更会武曲、天相、太阴等吉。",
        "vernacular": "帝星加百官，格局大。",
        "positive": "领导、班底、事业大。",
        "shadow": "人际复杂，高处不胜寒。"},
    "NOB-07": {"name": "财印夹禄", "dim": "财运",
        "classic": "禄存守命，天梁天相或化禄化科夹；或财印夹禄。",
        "vernacular": "财、印、禄互夹，财权名相生。",
        "positive": "财运事业互相成就。",
        "shadow": "钱权绑太紧，合同、官非风险。"},
    "NOB-08": {"name": "禄马佩印", "dim": "财运",
        "classic": "禄存天马同宫或对照，更见天相或化科为印。",
        "vernacular": "动中得财得名。",
        "positive": "异地发展，边赚边升。",
        "shadow": "奔波辛苦；无印则只财不贵。"},
    "NOB-09": {"name": "坐贵向贵", "dim": "事业",
        "classic": "天魁天钺坐命、迁移，或夹命、拱命。",
        "vernacular": "前后有贵人。",
        "positive": "逢凶化吉，考试运。",
        "shadow": "依赖贵人；魁钺落空则虚。"},
    "NOB-10": {"name": "马头带剑", "dim": "事业",
        "classic": "天马与擎羊同宫在午，或擎羊在午会天马，庙旺有制。",
        "vernacular": "马背带刀，武贵。",
        "positive": "军警、武职、边疆、开创。",
        "shadow": "刀光风险，血光意外。"},
    "NOB-11": {"name": "七杀朝斗", "dim": "事业",
        "classic": "七杀守命寅申，对宫或三方见紫微天府，会禄权科；不单以辰戌丑未论。",
        "vernacular": "七杀向帝星，权威开创。",
        "positive": "魄力、武职、创业。",
        "shadow": "冲撞、意外、树敌。"},
    "NOB-12": {"name": "日月并明", "dim": "事业",
        "classic": "太阳太阴皆庙旺，同宫、对照或三合，非泛称入庙。",
        "vernacular": "日月双明，阴阳调和。",
        "positive": "事业家庭兼顾，声名。",
        "shadow": "日月反背则矛盾；两面性。"},
    "NOB-13": {"name": "明珠出海", "dim": "事业",
        "classic": "太阴在亥，太阳在卯，对照或三合。",
        "vernacular": "月出海面，文星。",
        "positive": "文才、科名、学问。",
        "shadow": "柔、不实际；需禄权科实化。"},
    "NOB-14": {"name": "日月同临", "dim": "事业",
        "classic": "太阳太阴同宫丑未，或对照，庙旺。",
        "vernacular": "日月同临，多才。",
        "positive": "能力全面，人缘广。",
        "shadow": "性格矛盾，忽冷忽热。"},
    "NOB-15": {"name": "刑囚夹印", "dim": "事业",
        "classic": "天相守命，邻宫廉贞、天刑相夹；或廉贞天刑同会天相。",
        "vernacular": "刑囚夹印，司法武职。",
        "positive": "军警、司法、外科、纪律。",
        "shadow": "官非、血光、刑伤。"},
    "NOB-16": {"name": "科权禄拱", "dim": "事业",
        "classic": "生年化禄权科三方四正拱命，无煞忌。",
        "vernacular": "三奇加会。",
        "positive": "财权名三全。",
        "shadow": "压力大；忌煞则虚名。"},
    "NOB-17": {"name": "贪火相逢", "dim": "事业",
        "classic": "贪狼火星同宫庙旺，或火贪、铃贪。",
        "vernacular": "火贪暴发。",
        "positive": "横发、快猛，武贵。",
        "shadow": "横破，守不住。"},
    "NOB-18": {"name": "武曲守垣", "dim": "财运",
        "classic": "武曲守命于庙旺宫，见禄权；具体宫位需回查流派。",
        "vernacular": "财星归位，理财。",
        "positive": "理财、赚钱、财务。",
        "shadow": "重钱、硬冷。"},
    "NOB-19": {"name": "府相朝垣", "dim": "事业",
        "classic": "天府天相三合朝命，庙旺。",
        "vernacular": "财库印星朝。",
        "positive": "位高、班底、财库。",
        "shadow": "守成，不够进取。"},
    "NOB-20": {"name": "紫府朝垣", "dim": "事业",
        "classic": "紫微天府同宫或会照朝命。",
        "vernacular": "帝星财库。",
        "positive": "领导守财，富贵。",
        "shadow": "太稳，缺冲。"},
    "NOB-21": {"name": "文星暗拱", "dim": "事业",
        "classic": "文昌文曲夹命或拱命，非单称暗拱。",
        "vernacular": "文星暗中助。",
        "positive": "文才、科名、考试。",
        "shadow": "只读不做，需实践。"},
    "NOB-22": {"name": "权禄生逢", "dim": "财运",
        "classic": "生年化权化禄同守命，庙旺。",
        "vernacular": "财权同来。",
        "positive": "财权双得。",
        "shadow": "顺境易飘；忌煞则争权。"},
    "NOB-23": {"name": "羊刃入庙", "dim": "事业",
        "classic": "擎羊守命辰戌丑未，庙旺，遇吉化制。",
        "vernacular": "刀入庙有制。",
        "positive": "武贵、魄力。",
        "shadow": "刀仍是刀，防伤。"},
    "NOB-24": {"name": "巨机居卯", "dim": "事业",
        "classic": "天机巨门同守卯宫，庙旺，见禄权科。",
        "vernacular": "口才智慧在卯。",
        "positive": "口才、技术、专业。",
        "shadow": "口舌是非，巨门暗。"},
    "NOB-25": {"name": "明禄暗禄", "dim": "财运",
        "classic": "禄存与化禄一明一暗，或双禄夹拱命。",
        "vernacular": "明暗双禄。",
        "positive": "财厚，意外财。",
        "shadow": "贪则双耗，忌空劫。"},
    "NOB-26": {"name": "金舆扶驾", "dim": "事业",
        "classic": "紫微守命，太阳太阴前后夹。",
        "vernacular": "帝星日月护驾。",
        "positive": "贵人、左右逢源。",
        "shadow": "依赖贵人；日月陷则虚。"},
    # ===== 贫格8条 =====
    "POV-01": {"name": "生不逢时", "dim": "性格",
        "classic": "命坐空亡，廉贞同度或会照，煞忌。",
        "vernacular": "时机不对。",
        "positive": "有才待时。",
        "shadow": "怨天尤人，需等运。"},
    "POV-02": {"name": "禄逢两杀", "dim": "财运",
        "classic": "禄存坐空亡，逢空劫。",
        "vernacular": "钱来钱去。",
        "positive": "能赚。",
        "shadow": "更能花，注意储蓄。"},
    "POV-03": {"name": "马落空亡", "dim": "财运",
        "classic": "天马落空亡。",
        "vernacular": "跑无功。",
        "positive": "能跑。",
        "shadow": "方向错，选对路。"},
    "POV-04": {"name": "日月藏辉", "dim": "事业",
        "classic": "日月反背，逢巨门或暗星。",
        "vernacular": "名声不显。",
        "positive": "低调有能力。",
        "shadow": "太闷，要表现。"},
    "POV-05": {"name": "财与囚仇", "dim": "财运",
        "classic": "武曲廉贞同守身命，煞忌。",
        "vernacular": "钱权是非。",
        "positive": "懂钱懂权。",
        "shadow": "因钱惹官非。"},
    "POV-06": {"name": "一生孤贫", "dim": "性格",
        "classic": "破军守命陷地，煞忌空劫。",
        "vernacular": "破军陷地，奔波耗。",
        "positive": "能闯。",
        "shadow": "太耗，注意休息。"},
    "POV-07": {"name": "君子在野", "dim": "事业",
        "classic": "四杀守身命临陷地，吉星无力。",
        "vernacular": "有才没机会。",
        "positive": "有才。",
        "shadow": "别自暴自弃。"},
    "POV-08": {"name": "两重华盖", "dim": "财运",
        "classic": "禄存化禄坐命遇空劫，华盖重。",
        "vernacular": "有钱多耗，宗教缘。",
        "positive": "财有。",
        "shadow": "留不住，注意守财。"},
    # ===== 杂格8条 =====
    "MISC-01": {"name": "风云际会", "dim": "应期",
        "classic": "身命弱，二限逢禄马吉化。",
        "vernacular": "大运补命。",
        "positive": "时来运转。",
        "shadow": "别错过。"},
    "MISC-02": {"name": "锦上添花", "dim": "应期",
        "classic": "限破恶星，行吉地。",
        "vernacular": "先差后好。",
        "positive": "越来越好。",
        "shadow": "别得意早。"},
    "MISC-03": {"name": "禄衰马困", "dim": "财运",
        "classic": "限逢七杀，禄马空亡。",
        "vernacular": "财运困。",
        "positive": "知道困在哪。",
        "shadow": "别硬冲。"},
    "MISC-04": {"name": "衣锦还乡", "dim": "应期",
        "classic": "少年不遂，四十后行墓运吉。",
        "vernacular": "晚发。",
        "positive": "大器晚成。",
        "shadow": "别放弃。"},
    "MISC-05": {"name": "步数无依", "dim": "应期",
        "classic": "前后限连绵不分。",
        "vernacular": "运势不清。",
        "positive": "灵活。",
        "shadow": "没方向，要定下来。"},
    "MISC-06": {"name": "水上驾星", "dim": "应期",
        "classic": "一年好一年不好。",
        "vernacular": "起伏大。",
        "positive": "有好时。",
        "shadow": "不好时别硬冲。"},
    "MISC-07": {"name": "吉凶相伴", "dim": "应期",
        "classic": "命有主星，限前发限衰不发。",
        "vernacular": "早年发晚年衰。",
        "positive": "早年好。",
        "shadow": "晚年别飘。"},
    "MISC-08": {"name": "枯木逢春", "dim": "应期",
        "classic": "命衰限好。",
        "vernacular": "运补命。",
        "positive": "转运。",
        "shadow": "别等运，要努力。"},
}

VERDICT_INTERPRETATION = {
    ("仆役", "七杀"): {"classic": "七杀在仆役宫，欺主有刚强之仆多盗家财；武曲同背主；廉贞欠力；加羊陀火铃空劫全难招。", "vernacular": "欺主有刚强之仆多盗家财；武曲同背主；廉贞欠力；加羊陀火铃空劫全难招。", "positive": "", "shadow": "武曲同背主；廉贞欠力"},
    ("仆役", "右弼"): {"classic": "右弼在仆役宫，得力；加吉星有忠仆；加羊陀火铃空劫逃走。", "vernacular": "得力；加吉星有忠仆；加羊陀火铃空劫逃走。", "positive": "得力；加吉星有忠仆", "shadow": "加羊陀火铃空劫逃走。"},
    ("仆役", "天同"): {"classic": "天同在仆役宫，得力旺相；巨门先难后易；太阴同得力；天梁同助主；加羊陀火铃有背主之奴，见空劫怨主会走。", "vernacular": "得力旺相；巨门先难后易；太阴同得力；天梁同助主；加羊陀火铃有背主之奴，见空劫怨主会走。", "positive": "得力旺相；太阴同得力", "shadow": "巨门先难后易；加羊陀火铃有背主之奴，见空劫怨主会走。"},
    ("仆役", "天府"): {"classic": "天府在仆役宫，得力一呼百诺；紫微同助主；武曲同奴仆有；加陀羊火铃空劫多背主逃走。", "vernacular": "得力一呼百诺；紫微同助主；武曲同奴仆有；加陀羊火铃空劫多背主逃走。", "positive": "得力一呼百诺", "shadow": ""},
    ("仆役", "天机"): {"classic": "天机在仆役宫，入庙得力；陷空怨主；天梁同晚招；太阴同欠力；巨门加吉星有奴婢，加擎陀火铃空劫全难。", "vernacular": "入庙得力；陷空怨主；天梁同晚招；太阴同欠力；巨门加吉星有奴婢，加擎陀火铃空劫全难。", "positive": "入庙得力", "shadow": "陷空怨主；太阴同欠力"},
    ("仆役", "天梁"): {"classic": "天梁在仆役，奴多旺主。", "vernacular": "下属可靠，长辈缘。", "positive": "有人帮。", "shadow": "依赖；天梁陷则招非。"},
    ("仆役", "天相"): {"classic": "天相在仆役宫，末年招得；紫微同多奴多婢；武曲同怨主；廉贞同末年可招；加羊陀火铃空劫欠力逃走。", "vernacular": "末年招得；紫微同多奴多婢；武曲同怨主；廉贞同末年可招；加羊陀火铃空劫欠力逃走。", "positive": "紫微同多奴多婢", "shadow": "武曲同怨主；加羊陀火铃空劫欠力逃走。"},
    ("仆役", "天魁天钺"): {"classic": "天魁天钺在仆役宫，得力；加吉星有贵人仆。", "vernacular": "得力；加吉星有贵人仆。", "positive": "得力；加吉星有贵人仆。", "shadow": ""},
    ("仆役", "太阳"): {"classic": "太阳在仆役，入庙旺主发。", "vernacular": "下属、朋友有力，男贵人多。", "positive": "贵人朋友。", "shadow": "被朋友坑；太阳陷则劳。"},
    ("仆役", "太阴"): {"classic": "太阴在仆役宫，庙地得力成行；太阳同多奴多婢；天机同欠力；天同同旺主；加羊陀火铃空劫虽有而走，陷地全无。", "vernacular": "庙地得力成行；太阳同多奴多婢；天机同欠力；天同同旺主；加羊陀火铃空劫虽有而走，陷地全无。", "positive": "庙地得力成行；太阳同多奴多婢", "shadow": "天机同欠力；加羊陀火铃空劫虽有而走，陷地全无。"},
    ("仆役", "左辅"): {"classic": "左辅在仆役宫，得力；加吉星一呼百诺；加羊陀火铃空劫背主。", "vernacular": "得力；加吉星一呼百诺；加羊陀火铃空劫背主。", "positive": "得力；加吉星一呼百诺", "shadow": "加羊陀火铃空劫背主。"},
    ("仆役", "巨门"): {"classic": "巨门在仆役宫，入庙早年不得力招是非不能久居；太阳同助主卫家；天同同末年招得。", "vernacular": "入庙早年不得力招是非不能久居；太阳同助主卫家；天同同末年招得。", "positive": "", "shadow": ""},
    ("仆役", "廉贞"): {"classic": "廉贞在仆役宫，陷地奴背主晚年方招得；入庙一呼百诺；贪狼同欠力；七杀同背主；天同同多奴多婢；加羊陀火铃不旺会走。", "vernacular": "陷地奴背主晚年方招得；入庙一呼百诺；贪狼同欠力；七杀同背主；天同同多奴多婢；加羊陀火铃不旺会走。", "positive": "入庙一呼百诺；天同同多奴多婢", "shadow": "陷地奴背主晚年方招得；贪狼同欠力"},
    ("仆役", "擎羊陀罗"): {"classic": "擎羊陀罗在仆役宫，欠力；加吉星有强仆；加空劫全无。", "vernacular": "欠力；加吉星有强仆；加空劫全无。", "positive": "加吉星有强仆", "shadow": "欠力；加空劫全无。"},
    ("仆役", "文昌"): {"classic": "文昌在仆役宫，得力；加吉星有文仆；加羊陀火铃空劫欠力。", "vernacular": "得力；加吉星有文仆；加羊陀火铃空劫欠力。", "positive": "得力；加吉星有文仆", "shadow": "加羊陀火铃空劫欠力。"},
    ("仆役", "文曲"): {"classic": "文曲在仆役宫，得力；加吉星有巧仆；加羊陀火铃空劫怨主。", "vernacular": "得力；加吉星有巧仆；加羊陀火铃空劫怨主。", "positive": "得力；加吉星有巧仆", "shadow": "加羊陀火铃空劫怨主。"},
    ("仆役", "武曲"): {"classic": "武曲在仆役宫，旺宫不少一呼百诺；天府同多奴多婢；破军同招怨会走末年有招；天相同得力；七杀同背主；贪狼同欠力。", "vernacular": "旺宫不少一呼百诺；天府同多奴多婢；破军同招怨会走末年有招；天相同得力；七杀同背主；贪狼同欠力。", "positive": "天府同多奴多婢；天相同得力", "shadow": "破军同招怨会走末年有招；七杀同背主"},
    ("仆役", "火星铃星"): {"classic": "火星铃星在仆役宫，招怨；加吉星可用；加空劫逃走。", "vernacular": "招怨；加吉星可用；加空劫逃走。", "positive": "加吉星可用", "shadow": "招怨；加空劫逃走。"},
    ("仆役", "破军"): {"classic": "破军在仆役宫，入庙得力；陷宫招怨背主；武曲同违背；紫微同得力；廉贞同欠力；加羊陀火铃空劫难招。", "vernacular": "入庙得力；陷宫招怨背主；武曲同违背；紫微同得力；廉贞同欠力；加羊陀火铃空劫难招。", "positive": "入庙得力；紫微同得力", "shadow": "陷宫招怨背主；武曲同违背"},
    ("仆役", "禄存"): {"classic": "禄存在仆役宫，得力；加吉星有财奴；加羊陀火铃空劫怨主。", "vernacular": "得力；加吉星有财奴；加羊陀火铃空劫怨主。", "positive": "得力；加吉星有财奴", "shadow": "加羊陀火铃空劫怨主。"},
    ("仆役", "紫微"): {"classic": "紫微在仆役宫，成行得力，旺主生财；加擎羊火铃陀罗欠力；破军同先难后招；天相同得力；加空劫招怨逃走。", "vernacular": "成行得力，旺主生财；加擎羊火铃陀罗欠力；破军同先难后招；天相同得力；加空劫招怨逃走。", "positive": "成行得力，旺主生财；天相同得力", "shadow": "加擎羊火铃陀罗欠力；破军同先难后招"},
    ("仆役", "贪狼"): {"classic": "贪狼在仆役宫，初难招败主之奴；陷地全无；廉贞同亦少；紫微同之奴婢加羊陀火铃空劫虽有难育。", "vernacular": "初难招败主之奴；陷地全无；廉贞同亦少；紫微同之奴婢加羊陀火铃空劫虽有难育。", "positive": "", "shadow": "初难招败主之奴；陷地全无"},
    ("兄弟", "七杀"): {"classic": "七杀在兄弟宫，主孤克，在子午寅申宫方有三人，也不和宜各自；加昌曲左右更好。", "vernacular": "主孤克，在子午寅申宫方有三人，也不和宜各自；加昌曲左右更好。", "positive": "加昌曲左右更好。", "shadow": "主孤克，在子午寅申宫方有三人，也不和宜各自"},
    ("兄弟", "右弼"): {"classic": "右弼在兄弟宫，三人；同府相紫微昌曲有四五人；加羊陀火铃二人；有空劫欠力不和睦。", "vernacular": "三人；同府相紫微昌曲有四五人；加羊陀火铃二人；有空劫欠力不和睦。", "positive": "同府相紫微昌曲有四五人", "shadow": "有空劫欠力不和睦。"},
    ("兄弟", "天同"): {"classic": "天同在兄弟宫，入庙四五人；天梁同二三人；巨门同无杀三人；太阴同四五人；陷地只二人；见羊陀火铃空劫忌，少宜分居不和。", "vernacular": "入庙四五人；天梁同二三人；巨门同无杀三人；太阴同四五人；陷地只二人；见羊陀火铃空劫忌，少宜分居不和。", "positive": "入庙四五人", "shadow": "陷地只二人；见羊陀火铃空劫忌，少宜分居不和。"},
    ("兄弟", "天府"): {"classic": "天府在兄弟宫，有五人；紫微同加左右昌曲有六七人；廉贞同三人；见羊陀火铃空劫只二人。", "vernacular": "有五人；紫微同加左右昌曲有六七人；廉贞同三人；见羊陀火铃空劫只二人。", "positive": "紫微同加左右昌曲有六七人", "shadow": "见羊陀火铃空劫只二人。"},
    ("兄弟", "天机"): {"classic": "天机在兄弟宫，庙旺有二人；与巨门同二人；陷地相背不一心；天梁同二人；太阴同二三人；见羊陀火铃虽有而克害。", "vernacular": "庙旺有二人；与巨门同二人；陷地相背不一心；天梁同二人；太阴同二三人；见羊陀火铃虽有而克害。", "positive": "庙旺有二人", "shadow": "陷地相背不一心；见羊陀火铃虽有而克害。"},
    ("兄弟", "天梁"): {"classic": "天梁在兄弟宫，庙旺二人和顺，或多不同胞且不和；陷宫全无；天同同三人；天机同二人；见羊陀火铃空劫少。", "vernacular": "庙旺二人和顺，或多不同胞且不和；陷宫全无；天同同三人；天机同二人；见羊陀火铃空劫少。", "positive": "", "shadow": "陷宫全无；见羊陀火铃空劫少。"},
    ("兄弟", "天相"): {"classic": "天相在兄弟宫，和平有二三人；见杀全无；紫微同三四人；武曲同二人；廉贞同二人；见羊陀火铃空劫孤单。", "vernacular": "和平有二三人；见杀全无；紫微同三四人；武曲同二人；廉贞同二人；见羊陀火铃空劫孤单。", "positive": "", "shadow": "见杀全无；见羊陀火铃空劫孤单。"},
    ("兄弟", "太阳"): {"classic": "太阳在兄弟宫，庙旺三人；与巨门同无杀加有三人；太阴同五人；陷地不和欠力；加羊陀火铃空劫更克减半。", "vernacular": "庙旺三人；与巨门同无杀加有三人；太阴同五人；陷地不和欠力；加羊陀火铃空劫更克减半。", "positive": "庙旺三人", "shadow": "陷地不和欠力；加羊陀火铃空劫更克减半。"},
    ("兄弟", "太阴"): {"classic": "太阴在兄弟宫，入庙兄弟五人；太阳同五六人；天机同二人；科权同四五人；见羊陀火铃空劫减半且克，宜分居相背。", "vernacular": "入庙兄弟五人；太阳同五六人；天机同二人；科权同四五人；见羊陀火铃空劫减半且克，宜分居相背。", "positive": "入庙兄弟五人", "shadow": "见羊陀火铃空劫减半且克，宜分居相背。"},
    ("兄弟", "左辅"): {"classic": "左辅在兄弟宫，有三人；同天同昌曲有四五人；加羊陀火铃二人；有空劫欠力不和。", "vernacular": "有三人；同天同昌曲有四五人；加羊陀火铃二人；有空劫欠力不和。", "positive": "同天同昌曲有四五人", "shadow": "有空劫欠力不和。"},
    ("兄弟", "巨门"): {"classic": "巨门在兄弟宫，庙旺二人；陷地各有宜分居；太阳同加左右昌曲三人；天机同二人更乖违不一心；天同二三人；加羊陀火铃空劫孤克。", "vernacular": "庙旺二人；陷地各有宜分居；太阳同加左右昌曲三人；天机同二人更乖违不一心；天同二三人；加羊陀火铃空劫孤克。", "positive": "庙旺二人；太阳同加左右昌曲三人", "shadow": "陷地各有宜分居；加羊陀火铃空劫孤克。"},
    ("兄弟", "廉贞"): {"classic": "廉贞在兄弟宫，入庙二人；贪狼同招怨；天相同二人；七杀同一人；天府同加左右昌曲有三人；见羊陀火铃空劫有克且不和。", "vernacular": "入庙二人；贪狼同招怨；天相同二人；七杀同一人；天府同加左右昌曲有三人；见羊陀火铃空劫有克且不和。", "positive": "入庙二人；天府同加左右昌曲有三人", "shadow": "贪狼同招怨；见羊陀火铃空劫有克且不和。"},
    ("兄弟", "擎羊"): {"classic": "擎羊在兄弟宫，克害入庙一人；众吉星加有二三人；陷地全无。", "vernacular": "克害入庙一人；众吉星加有二三人；陷地全无。", "positive": "众吉星加有二三人", "shadow": "陷地全无。"},
    ("兄弟", "文昌文曲"): {"classic": "文昌文曲在兄弟宫，诸宫皆有三人；见羊陀火铃庙旺不克，陷宫孤单；加空劫全无。", "vernacular": "诸宫皆有三人；见羊陀火铃庙旺不克，陷宫孤单；加空劫全无。", "positive": "", "shadow": "加空劫全无。"},
    ("兄弟", "斗君"): {"classic": "斗君在兄弟宫，逢在兄弟宫过度，逢吉星兄弟一年和睦，逢凶杀有刑者主有兄弟争斗。", "vernacular": "逢在兄弟宫过度，逢吉星兄弟一年和睦，逢凶杀有刑者主有兄弟争斗。", "positive": "", "shadow": ""},
    ("兄弟", "武曲"): {"classic": "武曲在兄弟宫，庙旺有二人不合；陷宫加杀只一人；天相同二人；破军七杀同一人不和睦；加昌曲左右有三人；见羊陀火铃空劫孤单。", "vernacular": "庙旺有二人不合；陷宫加杀只一人；天相同二人；破军七杀同一人不和睦；加昌曲左右有三人；见羊陀火铃空劫孤单。", "positive": "庙旺有二人不合；加昌曲左右有三人", "shadow": "陷宫加杀只一人；破军七杀同一人不和睦"},
    ("兄弟", "火星"): {"classic": "火星在兄弟宫，入庙逢有吉星有一二人；加廉杀破铃孤克。", "vernacular": "入庙逢有吉星有一二人；加廉杀破铃孤克。", "positive": "入庙逢有吉星有一二人", "shadow": "加廉杀破铃孤克。"},
    ("兄弟", "破军"): {"classic": "破军在兄弟宫，入庙三人；陷地加杀孤单；武曲同二人；紫微同二人；廉贞同一人；加昌曲左右三人和睦；羊陀火铃空劫孤单。", "vernacular": "入庙三人；陷地加杀孤单；武曲同二人；紫微同二人；廉贞同一人；加昌曲左右三人和睦；羊陀火铃空劫孤单。", "positive": "入庙三人；加昌曲左右三人和睦", "shadow": "陷地加杀孤单；羊陀火铃空劫孤单。"},
    ("兄弟", "禄存"): {"classic": "禄存在兄弟宫，相生有兄弟；见杀克害招怨。", "vernacular": "相生有兄弟；见杀克害招怨。", "positive": "", "shadow": "见杀克害招怨。"},
    ("兄弟", "紫微"): {"classic": "紫微在兄弟宫，有倚靠年长之兄；与天府同三人，天相同三四人，破军同三人或各胞生；加羊陀火铃空劫克害有则欠和。", "vernacular": "有倚靠年长之兄；与天府同三人，天相同三四人，破军同三人或各胞生；加羊陀火铃空劫克害有则欠和。", "positive": "", "shadow": "与天府同三人，天相同三四人，破军同三人或各胞生；加羊陀火铃空劫克害有则欠和。"},
    ("兄弟", "贪狼"): {"classic": "贪狼在兄弟宫，庙旺二人；陷地宜各胞；廉贞同不和；紫微同三人；加羊陀火铃空劫孤单。", "vernacular": "庙旺二人；陷地宜各胞；廉贞同不和；紫微同三人；加羊陀火铃空劫孤单。", "positive": "庙旺二人", "shadow": "陷地宜各胞；廉贞同不和"},
    ("兄弟", "铃星"): {"classic": "铃星在兄弟宫，入庙相生有兄弟；加羊陀火空劫全无。", "vernacular": "入庙相生有兄弟；加羊陀火空劫全无。", "positive": "入庙相生有兄弟", "shadow": "加羊陀火空劫全无。"},
    ("兄弟", "陀罗"): {"classic": "陀罗在兄弟宫，克害入庙一人；众吉星加有二三人；陷地全无。", "vernacular": "克害入庙一人；众吉星加有二三人；陷地全无。", "positive": "众吉星加有二三人", "shadow": "陷地全无。"},
    ("命宫", "七杀"): {"classic": "七杀在命宫，刚毅果决，冲锋陷阵。入庙武贵。", "vernacular": "将星坐命，果断勇猛，敢闯敢拼。", "positive": "果断、勇猛、开创力。", "shadow": "太冲，易树敌。"},
    ("命宫", "天同"): {"classic": "天同在命宫，温和宽厚，福寿双全。入庙清福。", "vernacular": "福星坐命，温和乐观，享受生活。", "positive": "温和、福气、人缘好。", "shadow": "懒散，缺乏冲劲。"},
    ("命宫", "天府"): {"classic": "天府在命宫，宽厚包容，守成之主。入庙财禄丰厚。", "vernacular": "财库星坐命，稳重保守，善于守成。", "positive": "稳重、包容、守财。", "shadow": "太保守，缺乏开创。"},
    ("命宫", "天机"): {"classic": "天机在命宫，机谋多变，性急心慈。得左右昌曲魁钺凑合，文武大贵。", "vernacular": "智慧星坐命，聪明善谋，反应快。", "positive": "智谋、点子多、学习力强。", "shadow": "多虑多变，易犹豫不决。"},
    ("命宫", "天梁"): {"classic": "天梁在命宫，老成持重，长辈缘。入庙清贵。", "vernacular": "荫星坐命，成熟稳重，有长辈缘。", "positive": "成熟、可靠、长辈缘。", "shadow": "太老成，不够灵活。"},
    ("命宫", "天相"): {"classic": "天相在命宫，稳重大方，辅佐之材。入庙文武皆宜。", "vernacular": "印星坐命，稳重可靠，善于辅佐。", "positive": "稳重、可靠、辅佐力强。", "shadow": "依赖他人，缺乏主见。"},
    ("命宫", "太阳"): {"classic": "太阳在命宫，博爱光明，性刚急躁。入庙食禄千锺。", "vernacular": "太阳星坐命，热情外向，光明磊落。", "positive": "热情、名声、贵人。", "shadow": "太刚易折，操心劳碌。"},
    ("命宫", "太阴"): {"classic": "太阴在命宫，温柔文静，富屋贫人。入庙清贵。", "vernacular": "月亮星坐命，温柔细腻，感性。", "positive": "温柔、细腻、想象力丰富。", "shadow": "多愁善感，不够果断。"},
    ("命宫", "巨门"): {"classic": "巨门在命宫，口才出众，暗中伤人。入庙口才好。", "vernacular": "暗星坐命，口才好，善分析。", "positive": "口才、分析、研究力。", "shadow": "多疑，易口舌是非。"},
    ("命宫", "廉贞"): {"classic": "廉贞在命宫，刚毅不屈，敢作敢为。入庙文武双全。", "vernacular": "次桃花星坐命，敢冲敢拼，感情丰富。", "positive": "冲劲、魅力、执行力。", "shadow": "情绪化，易走极端。"},
    ("命宫", "武曲"): {"classic": "武曲在命宫，刚毅果决，理财能手。入庙武职峥嵘。", "vernacular": "财星坐命，实际果断，重视金钱。", "positive": "理财、决断、执行力强。", "shadow": "太硬太冷，人际关系弱。"},
    ("命宫", "破军"): {"classic": "破军在命宫，变革开创，破坏性强。入庙横发。", "vernacular": "耗星坐命，变革创新，不守旧。", "positive": "开创、变革、行动力。", "shadow": "破坏性强，易走极端。"},
    ("命宫", "紫微"): {"classic": "紫微在命宫，忠厚老成，谦恭耿直。与府相左右日月昌曲三合极吉，巨富大贵。", "vernacular": "帝星坐命，领导气质，宽厚有威望。", "positive": "领导、班底、大格局。", "shadow": "无辅佐则孤君，易孤独。"},
    ("命宫", "贪狼"): {"classic": "贪狼在命宫，多才多艺，欲望强烈。入庙横发。", "vernacular": "桃花星坐命，多才多艺，交际广。", "positive": "多才、交际、欲望强。", "shadow": "贪心，易沉迷。"},
    ("夫妻", "七杀"): {"classic": "七杀在夫妻宫，早克；武曲同亦克，或迟娶免刑；廉贞主生离；加羊陀火铃空劫克三妻。", "vernacular": "早克；武曲同亦克，或迟娶免刑；廉贞主生离；加羊陀火铃空劫克三妻。", "positive": "", "shadow": "早克；武曲同亦克，或迟娶免刑"},
    ("夫妻", "天同"): {"classic": "天同在夫妻宫，迟娶谐老，夫宜长妻宜少；加四杀欠和生离；巨门同加四杀亦克；太阴同助美容；天梁同极美夫妇。", "vernacular": "迟娶谐老，夫宜长妻宜少；加四杀欠和生离；巨门同加四杀亦克；太阴同助美容；天梁同极美夫妇。", "positive": "", "shadow": "迟娶谐老，夫宜长妻宜少；加四杀欠和生离"},
    ("夫妻", "天府"): {"classic": "天府在夫妻宫，相生宠爱夫主贵；见羊陀火铃空劫迟娶免刑，晚娶得谐老。", "vernacular": "相生宠爱夫主贵；见羊陀火铃空劫迟娶免刑，晚娶得谐老。", "positive": "相生宠爱夫主贵", "shadow": "见羊陀火铃空劫迟娶免刑，晚娶得谐老。"},
    ("夫妻", "天机"): {"classic": "天机在夫妻宫，宜年少刚强，妻可配夫宜长；加羊陀火铃主生离，晚娶吉；天梁同宜年长；太阴同内助美容。", "vernacular": "宜年少刚强，妻可配夫宜长；加羊陀火铃主生离，晚娶吉；天梁同宜年长；太阴同内助美容。", "positive": "加羊陀火铃主生离，晚娶吉", "shadow": "宜年少刚强，妻可配夫宜长"},
    ("夫妻", "天梁"): {"classic": "天梁在夫妻宫，妻宜大美容；天同同和气；天机招美淑；加羊陀火铃空劫不和顺。", "vernacular": "妻宜大美容；天同同和气；天机招美淑；加羊陀火铃空劫不和顺。", "positive": "", "shadow": ""},
    ("夫妻", "天相"): {"classic": "天相在夫妻宫，貌美贤淑，夫宜年长，亲上成亲；紫微同谐老；武曲少和；廉贞同入庙免刑；加羊陀火铃空劫刑克。", "vernacular": "貌美贤淑，夫宜年长，亲上成亲；紫微同谐老；武曲少和；廉贞同入庙免刑；加羊陀火铃空劫刑克。", "positive": "貌美贤淑，夫宜年长，亲上成亲", "shadow": "武曲少和；加羊陀火铃空劫刑克。"},
    ("夫妻", "天魁天钺"): {"classic": "天魁天钺在夫妻宫，多主夫妇美丽；坐妻宫必主得妻财；加吉星同主贵美夫妇。", "vernacular": "多主夫妇美丽；坐妻宫必主得妻财；加吉星同主贵美夫妇。", "positive": "多主夫妇美丽；加吉星同主贵美夫妇。", "shadow": ""},
    ("夫妻", "太阳"): {"classic": "太阳在夫妻宫，庙旺迟娶吉，早娶克，因妻得贵；与天梁同加左右招贤明之妻；太阴同内助；巨门同无羊陀火铃空劫不克，有此四杀反空劫定克。", "vernacular": "庙旺迟娶吉，早娶克，因妻得贵；与天梁同加左右招贤明之妻；太阴同内助；巨门同无羊陀火铃空劫不克，有此四杀反空劫定克。", "positive": "", "shadow": "巨门同无羊陀火铃空劫不克，有此四杀反空劫定克。"},
    ("夫妻", "太阴"): {"classic": "太阴在夫妻宫，入庙男女皆贵美夫妇；加昌曲极美；加羊陀火铃空劫耗忌，不克主生离；太阳同谐老；天机同美好宜少年。", "vernacular": "入庙男女皆贵美夫妇；加昌曲极美；加羊陀火铃空劫耗忌，不克主生离；太阳同谐老；天机同美好宜少年。", "positive": "入庙男女皆贵美夫妇；加昌曲极美", "shadow": "加羊陀火铃空劫耗忌，不克主生离；天机同美好宜少年。"},
    ("夫妻", "左辅右弼"): {"classic": "左辅右弼在夫妻宫，谐老；加羊陀火铃空劫贪廉同，宜年长刚强之妻。", "vernacular": "谐老；加羊陀火铃空劫贪廉同，宜年长刚强之妻。", "positive": "", "shadow": "加羊陀火铃空劫贪廉同，宜年长刚强之妻。"},
    ("夫妻", "巨门"): {"classic": "巨门在夫妻宫，宜年长定克欠和；太阳同无四杀加谐老；天机同内助美貌；天同同性聪之妻并头；加羊陀火铃空劫定克二妻或主生离。", "vernacular": "宜年长定克欠和；太阳同无四杀加谐老；天机同内助美貌；天同同性聪之妻并头；加羊陀火铃空劫定克二妻或主生离。", "positive": "", "shadow": "宜年长定克欠和；加羊陀火铃空劫定克二妻或主生离。"},
    ("夫妻", "廉贞"): {"classic": "廉贞在夫妻宫，三度作新郎，与贪狼同愈克，七杀同亦刑且欠和；加羊陀火铃主生离；天府同谐老性刚无克。", "vernacular": "三度作新郎，与贪狼同愈克，七杀同亦刑且欠和；加羊陀火铃主生离；天府同谐老性刚无克。", "positive": "", "shadow": "三度作新郎，与贪狼同愈克，七杀同亦刑且欠和；天府同谐老性刚无克。"},
    ("夫妻", "擎羊陀罗"): {"classic": "擎羊陀罗在夫妻宫，入庙加吉星迟娶免刑或久和；陷地早克；加日月巨机火铃武杀主生离。", "vernacular": "入庙加吉星迟娶免刑或久和；陷地早克；加日月巨机火铃武杀主生离。", "positive": "", "shadow": "陷地早克"},
    ("夫妻", "文昌"): {"classic": "文昌在夫妻宫，妻少内助聪明；天机太阴同主美容；不宜陷地；加羊陀火铃空劫深忌。", "vernacular": "妻少内助聪明；天机太阴同主美容；不宜陷地；加羊陀火铃空劫深忌。", "positive": "", "shadow": "妻少内助聪明；不宜陷地"},
    ("夫妻", "文曲"): {"classic": "文曲在夫妻宫，相生会太阴诸吉星谐老；同昌曲妻妾多；加羊陀火铃空劫忌星有克。", "vernacular": "相生会太阴诸吉星谐老；同昌曲妻妾多；加羊陀火铃空劫忌星有克。", "positive": "相生会太阴诸吉星谐老；同昌曲妻妾多", "shadow": "加羊陀火铃空劫忌星有克。"},
    ("夫妻", "斗君"): {"classic": "斗君在夫妻宫，过度在妻宫逢吉星妻妾美无灾克；逢恶星妻妾有灾厄；本命妻宫克妻者主其年刑伤妻妾。", "vernacular": "过度在妻宫逢吉星妻妾美无灾克；逢恶星妻妾有灾厄；本命妻宫克妻者主其年刑伤妻妾。", "positive": "", "shadow": "本命妻宫克妻者主其年刑伤妻妾。"},
    ("夫妻", "武曲"): {"classic": "武曲在夫妻宫，背克宜迟娶，同年夫妇相当；加吉星因妻得财；凶星因妻去产；贪狼同迟无刑；七杀同克二三妻；加羊陀火铃空劫更克。", "vernacular": "背克宜迟娶，同年夫妇相当；加吉星因妻得财；凶星因妻去产；贪狼同迟无刑；七杀同克二三妻；加羊陀火铃空劫更克。", "positive": "加吉星因妻得财", "shadow": "背克宜迟娶，同年夫妇相当；凶星因妻去产"},
    ("夫妻", "火星铃星"): {"classic": "火星铃星在夫妻宫，入庙加吉无刑；陷地刑克。", "vernacular": "入庙加吉无刑；陷地刑克。", "positive": "", "shadow": "陷地刑克。"},
    ("夫妻", "破军"): {"classic": "破军在夫妻，男女俱克别聚主生离。", "vernacular": "婚姻多波折，配偶个性强，聚少离多。", "positive": "配偶有冲劲、能力。", "shadow": "早婚不利，感情多变，需空间。"},
    ("夫妻", "禄存"): {"classic": "禄存在夫妻宫，相生无克，妻宜年少并头迟娶者；加羊陀火铃空劫见截路空亡孤单。", "vernacular": "相生无克，妻宜年少并头迟娶者；加羊陀火铃空劫见截路空亡孤单。", "positive": "", "shadow": "相生无克，妻宜年少并头迟娶者；加羊陀火铃空劫见截路空亡孤单。"},
    ("夫妻", "紫微"): {"classic": "紫微在夫妻宫，晚聘谐老，性刚；天府同谐老；天相同年少；破军同克刑；加羊陀火铃亦刑；贪狼同有吉星免刑。", "vernacular": "晚聘谐老，性刚；天府同谐老；天相同年少；破军同克刑；加羊陀火铃亦刑；贪狼同有吉星免刑。", "positive": "", "shadow": "天相同年少；破军同克刑"},
    ("夫妻", "贪狼"): {"classic": "贪狼在夫妻宫，男女不得美，三次作新郎；入庙宜迟娶；廉贞同主克；加羊陀火铃主生离；紫微同年长方可对。", "vernacular": "男女不得美，三次作新郎；入庙宜迟娶；廉贞同主克；加羊陀火铃主生离；紫微同年长方可对。", "positive": "入庙宜迟娶", "shadow": "廉贞同主克"},
    ("子女", "七杀"): {"classic": "七杀在子女宫，主孤一人之分；紫微同再吉星有三人；见羊陀火铃空劫全无，纵有不成器必强横败家之子。", "vernacular": "主孤一人之分；紫微同再吉星有三人；见羊陀火铃空劫全无，纵有不成器必强横败家之子。", "positive": "紫微同再吉星有三人", "shadow": "主孤一人之分"},
    ("子女", "右弼"): {"classic": "右弼在子女宫，三人；加吉星有贵子；见羊陀火铃空劫减半。", "vernacular": "三人；加吉星有贵子；见羊陀火铃空劫减半。", "positive": "加吉星有贵子", "shadow": "见羊陀火铃空劫减半。"},
    ("子女", "天同"): {"classic": "天同在子女宫，庙旺五子有贵；巨门同三人；太阴同五人；午宫陷地减半；天梁同先女后男有二子；守申宫只留一子送终；寅宫加吉星有三子；加羊陀火铃空劫子少送终。", "vernacular": "庙旺五子有贵；巨门同三人；太阴同五人；午宫陷地减半；天梁同先女后男有二子；守申宫只留一子送终；寅宫加吉星有三子；加羊陀火铃空劫子少送终。", "positive": "庙旺五子有贵；寅宫加吉星有三子", "shadow": "午宫陷地减半；加羊陀火铃空劫子少送终。"},
    ("子女", "天府"): {"classic": "天府在子女宫，五人；武曲同二人；紫微同四五人；廉贞同三人；加羊陀火铃空劫止三人。", "vernacular": "五人；武曲同二人；紫微同四五人；廉贞同三人；加羊陀火铃空劫止三人。", "positive": "", "shadow": "加羊陀火铃空劫止三人。"},
    ("子女", "天机"): {"classic": "天机在子女宫，庙旺二人，或庶生多；巨门一人；天梁同在寅宫二三人，在申宫女多男少只可一子；太阴同二三人；加羊陀火铃空劫全无子。", "vernacular": "庙旺二人，或庶生多；巨门一人；天梁同在寅宫二三人，在申宫女多男少只可一子；太阴同二三人；加羊陀火铃空劫全无子。", "positive": "庙旺二人，或庶生多", "shadow": "加羊陀火铃空劫全无子。"},
    ("子女", "天梁"): {"classic": "天梁在子女宫，庙旺二人；加羊陀火铃空劫早克；天同同加昌曲左右吉星三人；天机同二人；加羊陀火铃空劫全无。", "vernacular": "庙旺二人；加羊陀火铃空劫早克；天同同加昌曲左右吉星三人；天机同二人；加羊陀火铃空劫全无。", "positive": "庙旺二人；天同同加昌曲左右吉星三人", "shadow": "加羊陀火铃空劫早克；加羊陀火铃空劫全无。"},
    ("子女", "天相"): {"classic": "天相在子女宫，无羊陀火铃同有二子成器；有杀先招祀子居长亲生一二子；紫微同昌曲左右三四人；武曲同三人；见羊陀火铃空劫必克，宜偏室生。", "vernacular": "无羊陀火铃同有二子成器；有杀先招祀子居长亲生一二子；紫微同昌曲左右三四人；武曲同三人；见羊陀火铃空劫必克，宜偏室生。", "positive": "无羊陀火铃同有二子成器；紫微同昌曲左右三四人", "shadow": "见羊陀火铃空劫必克，宜偏室生。"},
    ("子女", "天魁天钺"): {"classic": "天魁天钺在子女宫，单守主有贵子。", "vernacular": "单守主有贵子。", "positive": "单守主有贵子。", "shadow": ""},
    ("子女", "太阳"): {"classic": "太阳在子女宫，入庙男三女二晚子贵；巨门同三人；太阴同五人；陷地有三子不成盖；再加羊陀火铃空劫止留一子送终。", "vernacular": "入庙男三女二晚子贵；巨门同三人；太阴同五人；陷地有三子不成盖；再加羊陀火铃空劫止留一子送终。", "positive": "入庙男三女二晚子贵", "shadow": "再加羊陀火铃空劫止留一子送终。"},
    ("子女", "太阴"): {"classic": "太阴在子女宫，女三男二先女后男；庙旺有贵子；陷地减半，招软弱之子或虚花不成器；太阳同五人；天机同二人；天同同五人；加羊陀火铃空劫子少。", "vernacular": "女三男二先女后男；庙旺有贵子；陷地减半，招软弱之子或虚花不成器；太阳同五人；天机同二人；天同同五人；加羊陀火铃空劫子少。", "positive": "庙旺有贵子", "shadow": "加羊陀火铃空劫子少。"},
    ("子女", "左辅"): {"classic": "左辅在子女宫，单居男三女一；见紫微天府诸吉星主贵子；见破杀羊陀火铃空劫止二人，有也不成器。", "vernacular": "单居男三女一；见紫微天府诸吉星主贵子；见破杀羊陀火铃空劫止二人，有也不成器。", "positive": "见紫微天府诸吉星主贵子", "shadow": ""},
    ("子女", "巨门"): {"classic": "巨门在子女宫，入庙二人先难后易；太阳同一二子易养；加羊陀火铃子少；天机同一人，有吉星同二人，加空劫全无。", "vernacular": "入庙二人先难后易；太阳同一二子易养；加羊陀火铃子少；天机同一人，有吉星同二人，加空劫全无。", "positive": "", "shadow": "加羊陀火铃子少"},
    ("子女", "廉贞"): {"classic": "廉贞在子女宫，一人；天府同主贵子三人；贪狼破军七杀同主孤，再加羊陀火铃空劫全无；天相同有二子。", "vernacular": "一人；天府同主贵子三人；贪狼破军七杀同主孤，再加羊陀火铃空劫全无；天相同有二子。", "positive": "天府同主贵子三人", "shadow": "贪狼破军七杀同主孤，再加羊陀火铃空劫全无"},
    ("子女", "擎羊陀罗"): {"classic": "擎羊陀罗在子女宫，陷宫孤单；加吉星庙旺有一人；对宫有吉星多无杀冲亦有三四人；见耗杀忌在本宫绝嗣。", "vernacular": "陷宫孤单；加吉星庙旺有一人；对宫有吉星多无杀冲亦有三四人；见耗杀忌在本宫绝嗣。", "positive": "加吉星庙旺有一人；对宫有吉星多无杀冲亦有三四人", "shadow": "陷宫孤单；见耗杀忌在本宫绝嗣。"},
    ("子女", "文昌"): {"classic": "文昌在子女宫，三人；加吉星更多；有擎陀火铃空劫只可一子之分。", "vernacular": "三人；加吉星更多；有擎陀火铃空劫只可一子之分。", "positive": "加吉星更多", "shadow": "有擎陀火铃空劫只可一子之分。"},
    ("子女", "文曲"): {"classic": "文曲在子女宫，庙旺有四人；陷地有二三人；加擎羊罗陀火铃子少。", "vernacular": "庙旺有四人；陷地有二三人；加擎羊罗陀火铃子少。", "positive": "庙旺有四人", "shadow": "陷地有二三人；加擎羊罗陀火铃子少。"},
    ("子女", "斗君"): {"classic": "斗君在子女宫，在子女宫过度，逢吉子女昌盛，逢凶刑克或子破家。", "vernacular": "在子女宫过度，逢吉子女昌盛，逢凶刑克或子破家。", "positive": "", "shadow": ""},
    ("子女", "武曲"): {"classic": "武曲在子女宫，主一子或成至生者多；破军同主刑止一人；加羊陀火铃空劫绝祀；贪狼晚招二子；天相同先招外子后亲生一子；七杀同主孤或伤残之子。", "vernacular": "主一子或成至生者多；破军同主刑止一人；加羊陀火铃空劫绝祀；贪狼晚招二子；天相同先招外子后亲生一子；七杀同主孤或伤残之子。", "positive": "主一子或成至生者多", "shadow": "破军同主刑止一人；加羊陀火铃空劫绝祀"},
    ("子女", "火星"): {"classic": "火星在子女宫，逢吉同不孤；陷宫加杀刑伤。", "vernacular": "逢吉同不孤；陷宫加杀刑伤。", "positive": "", "shadow": "陷宫加杀刑伤。"},
    ("子女", "破军"): {"classic": "破军在子女宫，入庙三人身刚强之子；紫微同三人；武曲同加昌曲左右三人；廉贞同一人；见羊陀相生有制，无制见空劫火陀少子。", "vernacular": "入庙三人身刚强之子；紫微同三人；武曲同加昌曲左右三人；廉贞同一人；见羊陀相生有制，无制见空劫火陀少子。", "positive": "入庙三人身刚强之子；武曲同加昌曲左右三人", "shadow": "见羊陀相生有制，无制见空劫火陀少子。"},
    ("子女", "禄存"): {"classic": "禄存在子女宫，主孤宜庶出一螟蛉之子；加吉星有一人；加火星诸杀孤刑。", "vernacular": "主孤宜庶出一螟蛉之子；加吉星有一人；加火星诸杀孤刑。", "positive": "加吉星有一人", "shadow": "主孤宜庶出一螟蛉之子；加火星诸杀孤刑。"},
    ("子女", "紫微"): {"classic": "紫微在子女宫，庙旺男三女二；加左右昌曲有五人；加羊陀火铃空劫只一双，不然偏室生或招祀子居长；破军同三人；天府同加吉星四五人。", "vernacular": "庙旺男三女二；加左右昌曲有五人；加羊陀火铃空劫只一双，不然偏室生或招祀子居长；破军同三人；天府同加吉星四五人。", "positive": "庙旺男三女二；加左右昌曲有五人", "shadow": "加羊陀火铃空劫只一双，不然偏室生或招祀子居长；破军同三人"},
    ("子女", "贪狼"): {"classic": "贪狼在子女宫，庙旺二人，早有刑克；紫微同二人；廉贞同子少；武曲同三人先难后易。", "vernacular": "庙旺二人，早有刑克；紫微同二人；廉贞同子少；武曲同三人先难后易。", "positive": "", "shadow": "廉贞同子少；武曲同三人先难后易。"},
    ("子女", "铃星"): {"classic": "铃星在子女宫，独守孤单；加吉星入庙可许庶出；看对宫吉多二三人。", "vernacular": "独守孤单；加吉星入庙可许庶出；看对宫吉多二三人。", "positive": "加吉星入庙可许庶出；看对宫吉多二三人。", "shadow": "独守孤单"},
    ("官禄", "七杀"): {"classic": "七杀在官禄宫，庙旺武职峥嵘权贵非小不宜文人；武曲同权贵；廉贞同功名显达。", "vernacular": "庙旺武职峥嵘权贵非小不宜文人；武曲同权贵；廉贞同功名显达。", "positive": "庙旺武职峥嵘权贵非小不宜文人；武曲同权贵", "shadow": ""},
    ("官禄", "右弼"): {"classic": "右弼在官禄宫，宜居武职不和文人；与紫府昌曲同财官双美；陷宫成败有贬谪；见羊陀火铃空劫亦有黜降。", "vernacular": "宜居武职不和文人；与紫府昌曲同财官双美；陷宫成败有贬谪；见羊陀火铃空劫亦有黜降。", "positive": "与紫府昌曲同财官双美", "shadow": "宜居武职不和文人；见羊陀火铃空劫亦有黜降。"},
    ("官禄", "天同"): {"classic": "天同在官禄宫，入庙文武皆宜无羊陀火铃吉；巨门同先小后大；太阳昌曲科权禄吉美；太阴同权贵；陷宫胥更论。", "vernacular": "入庙文武皆宜无羊陀火铃吉；巨门同先小后大；太阳昌曲科权禄吉美；太阴同权贵；陷宫胥更论。", "positive": "入庙文武皆宜无羊陀火铃吉；太阳昌曲科权禄吉美", "shadow": "陷宫胥更论。"},
    ("官禄", "天府"): {"classic": "天府在官禄宫，入庙文武皆吉无羊陀火铃空耗全美；紫微同文武声名；廉贞武曲同权贵；见空劫平常。", "vernacular": "入庙文武皆吉无羊陀火铃空耗全美；紫微同文武声名；廉贞武曲同权贵；见空劫平常。", "positive": "廉贞武曲同权贵", "shadow": "见空劫平常。"},
    ("官禄", "天机"): {"classic": "天机在官禄宫，入庙权贵会文曲为良；见羊陀火铃方宜；天梁同文武之材；太阴同名振边夷；陷宫退官失职，吏员立脚。", "vernacular": "入庙权贵会文曲为良；见羊陀火铃方宜；天梁同文武之材；太阴同名振边夷；陷宫退官失职，吏员立脚。", "positive": "入庙权贵会文曲为良", "shadow": "陷宫退官失职，吏员立脚。"},
    ("官禄", "天梁"): {"classic": "天梁在官禄宫，庙午会左右魁钺文武之材；天同同权贵不小；天机同峥嵘贵显；加羊陀火铃空劫平。", "vernacular": "庙午会左右魁钺文武之材；天同同权贵不小；天机同峥嵘贵显；加羊陀火铃空劫平。", "positive": "庙午会左右魁钺文武之材；天同同权贵不小", "shadow": "加羊陀火铃空劫平。"},
    ("官禄", "天相"): {"classic": "天相在官禄，入庙文武皆宜。", "vernacular": "辅佐行政、管理、服务。", "positive": "稳、会辅佐。", "shadow": "别长期二把手，需自主。"},
    ("官禄", "太阳"): {"classic": "太阳在官禄宫，入庙文武为良；不见羊陀火铃吉；太阴同贵显；左右昌曲魁钺同更君科禄权，定居一品之贵。", "vernacular": "入庙文武为良；不见羊陀火铃吉；太阴同贵显；左右昌曲魁钺同更君科禄权，定居一品之贵。", "positive": "入庙文武为良；不见羊陀火铃吉", "shadow": ""},
    ("官禄", "太阴"): {"classic": "太阴在官禄宫，入庙多贵；陷地气高横破难显达；会太阳昌曲左右三品之贵；天同同文武皆宜；天机同闹中进身吏员立脚。", "vernacular": "入庙多贵；陷地气高横破难显达；会太阳昌曲左右三品之贵；天同同文武皆宜；天机同闹中进身吏员立脚。", "positive": "入庙多贵；会太阳昌曲左右三品之贵", "shadow": "陷地气高横破难显达"},
    ("官禄", "左辅"): {"classic": "左辅在官禄宫，入庙文武之材，武职最旺不利文人；会吉星身中清文武皆良；见羊陀火铃空劫进退声名。", "vernacular": "入庙文武之材，武职最旺不利文人；会吉星身中清文武皆良；见羊陀火铃空劫进退声名。", "positive": "入庙文武之材，武职最旺不利文人；会吉星身中清文武皆良", "shadow": "见羊陀火铃空劫进退声名。"},
    ("官禄", "巨门"): {"classic": "巨门在官禄宫，入庙武职权贵文人不耐久；太阳同有进退入庙久长；天机同在卯宫吉美，在酉宫虽美无始终；陷宫遭悔吝，加羊陀火铃空劫退宫卸职。", "vernacular": "入庙武职权贵文人不耐久；太阳同有进退入庙久长；天机同在卯宫吉美，在酉宫虽美无始终；陷宫遭悔吝，加羊陀火铃空劫退宫卸职。", "positive": "入庙武职权贵文人不耐久；太阳同有进退入庙久长", "shadow": "陷宫遭悔吝，加羊陀火铃空劫退宫卸职。"},
    ("官禄", "廉贞"): {"classic": "廉贞在官禄宫，入庙武职权贵不耐久；贪狼同闹中权贵；紫微会三方文职；七杀同军旅出身；天相天府同衣锦富贵。", "vernacular": "入庙武职权贵不耐久；贪狼同闹中权贵；紫微会三方文职；七杀同军旅出身；天相天府同衣锦富贵。", "positive": "入庙武职权贵不耐久；贪狼同闹中权贵", "shadow": ""},
    ("官禄", "擎羊"): {"classic": "擎羊在官禄宫，入庙最利武职；同吉星权贵；陷地平常虚名而已。", "vernacular": "入庙最利武职；同吉星权贵；陷地平常虚名而已。", "positive": "入庙最利武职；同吉星权贵", "shadow": "陷地平常虚名而已。"},
    ("官禄", "文昌"): {"classic": "文昌在官禄宫，入庙太阳同加吉科权禄文武之材；同天府文曲富贵双全。", "vernacular": "入庙太阳同加吉科权禄文武之材；同天府文曲富贵双全。", "positive": "入庙太阳同加吉科权禄文武之材；同天府文曲富贵双全。", "shadow": ""},
    ("官禄", "文曲"): {"classic": "文曲在官禄宫，庙旺文武皆宜；陷宫与天机太阴同宫胥吏权贵；会紫府左右近君频而执政；加羊陀火铃空劫平常。", "vernacular": "庙旺文武皆宜；陷宫与天机太阴同宫胥吏权贵；会紫府左右近君频而执政；加羊陀火铃空劫平常。", "positive": "庙旺文武皆宜", "shadow": "加羊陀火铃空劫平常。"},
    ("官禄", "斗君"): {"classic": "斗君在官禄宫，遇吉其年月财官旺；逢凶忌财官不显达，有劳禄奔波。", "vernacular": "遇吉其年月财官旺；逢凶忌财官不显达，有劳禄奔波。", "positive": "遇吉其年月财官旺", "shadow": "逢凶忌财官不显达，有劳禄奔波。"},
    ("官禄", "武曲"): {"classic": "武曲在官禄，入庙武职峥嵘。", "vernacular": "事业适合金融、管理、武职。", "positive": "决断、赚钱。", "shadow": "太硬，人际冷。"},
    ("官禄", "火星"): {"classic": "火星在官禄宫，晚年功名遂心，早年成败；会紫微贪狼吉；陷地不美。", "vernacular": "晚年功名遂心，早年成败；会紫微贪狼吉；陷地不美。", "positive": "会紫微贪狼吉", "shadow": "陷地不美。"},
    ("官禄", "破军"): {"classic": "破军在官禄宫，庙旺武职轩冕；武曲同加权禄；文昌文曲显达；加羊陀火铃平常；紫微同名振扬；廉贞同文人不耐久，胥吏最美。", "vernacular": "庙旺武职轩冕；武曲同加权禄；文昌文曲显达；加羊陀火铃平常；紫微同名振扬；廉贞同文人不耐久，胥吏最美。", "positive": "庙旺武职轩冕；文昌文曲显达", "shadow": ""},
    ("官禄", "禄存"): {"classic": "禄存在官禄宫，会吉文武皆良，财官双美，子孙爵秩，诸宫为美。", "vernacular": "会吉文武皆良，财官双美，子孙爵秩，诸宫为美。", "positive": "会吉文武皆良，财官双美，子孙爵秩，诸宫为美。", "shadow": ""},
    ("官禄", "紫微"): {"classic": "紫微在官禄宫，庙旺遇左右昌曲魁钺，轩冕位至封侯伯；加羊陀火铃平常；天府同权贵名利两全；天相加内外权贵清正；破军同闹中安身。", "vernacular": "庙旺遇左右昌曲魁钺，轩冕位至封侯伯；加羊陀火铃平常；天府同权贵名利两全；天相加内外权贵清正；破军同闹中安身。", "positive": "庙旺遇左右昌曲魁钺，轩冕位至封侯伯；天府同权贵名利两全", "shadow": "破军同闹中安身。"},
    ("官禄", "贪狼"): {"classic": "贪狼在官禄宫，入庙遇火铃武职掌大权；紫微同文武之职权贵非小；陷宫贪污之官；加羊陀空劫平常。", "vernacular": "入庙遇火铃武职掌大权；紫微同文武之职权贵非小；陷宫贪污之官；加羊陀空劫平常。", "positive": "入庙遇火铃武职掌大权；紫微同文武之职权贵非小", "shadow": "陷宫贪污之官；加羊陀空劫平常。"},
    ("官禄", "铃星"): {"classic": "铃星在官禄宫，独守旺宫吉；陷地不美；加诸吉星权贵。", "vernacular": "独守旺宫吉；陷地不美；加诸吉星权贵。", "positive": "独守旺宫吉；加诸吉星权贵。", "shadow": "陷地不美"},
    ("官禄", "陀罗"): {"classic": "陀罗在官禄宫，独守平常；加吉星亦虚名而已。", "vernacular": "独守平常；加吉星亦虚名而已。", "positive": "加吉星亦虚名而已。", "shadow": ""},
    ("父母", "七杀"): {"classic": "七杀在父母宫，克早离祖六亲骨肉孤独；武曲同亦刑；廉贞同刑早；紫微同加吉星无刑；加羊陀火铃空劫父母不周全。", "vernacular": "克早离祖六亲骨肉孤独；武曲同亦刑；廉贞同刑早；紫微同加吉星无刑；加羊陀火铃空劫父母不周全。", "positive": "", "shadow": "克早离祖六亲骨肉孤独；武曲同亦刑"},
    ("父母", "右弼"): {"classic": "右弼在父母宫，独守无刑；加吉星得父母庇荫；见羊陀火铃凑离祖二姓安居。", "vernacular": "独守无刑；加吉星得父母庇荫；见羊陀火铃凑离祖二姓安居。", "positive": "加吉星得父母庇荫", "shadow": "独守无刑"},
    ("父母", "天同"): {"classic": "天同在父母宫，独守庙旺无刑；加四杀重拜父母；巨门同欠和；太阴同父母双全；天梁同无刑或退祖业；加羊陀火铃空劫父母不全。", "vernacular": "独守庙旺无刑；加四杀重拜父母；巨门同欠和；太阴同父母双全；天梁同无刑或退祖业；加羊陀火铃空劫父母不全。", "positive": "", "shadow": "巨门同欠和；天梁同无刑或退祖业"},
    ("父母", "天府"): {"classic": "天府在父母宫，父母双全；紫微同亦无刑；廉贞武曲同在庙旺无刑；加羊陀火铃空劫主伤。", "vernacular": "父母双全；紫微同亦无刑；廉贞武曲同在庙旺无刑；加羊陀火铃空劫主伤。", "positive": "", "shadow": "紫微同亦无刑；加羊陀火铃空劫主伤。"},
    ("父母", "天机"): {"classic": "天机在父母宫，庙旺无刑；陷地逢羊陀火铃空劫二姓寄居重拜父母或过房入赘；太阴同免刑；天梁同无刑俱要无杀，加杀亦不免刑伤；巨门早刑。", "vernacular": "庙旺无刑；陷地逢羊陀火铃空劫二姓寄居重拜父母或过房入赘；太阴同免刑；天梁同无刑俱要无杀，加杀亦不免刑伤；巨门早刑。", "positive": "", "shadow": "陷地逢羊陀火铃空劫二姓寄居重拜父母或过房入赘；太阴同免刑"},
    ("父母", "天梁"): {"classic": "天梁在父母宫，陷地加羊陀火铃孤克弃祖入赘更名寄人，保养免刑；天同同加四杀有刑，无杀无刑；天机同无刑；太阳同克迟，加四杀空劫亦克早。", "vernacular": "陷地加羊陀火铃孤克弃祖入赘更名寄人，保养免刑；天同同加四杀有刑，无杀无刑；天机同无刑；太阳同克迟，加四杀空劫亦克早。", "positive": "", "shadow": "陷地加羊陀火铃孤克弃祖入赘更名寄人，保养免刑；天同同加四杀有刑，无杀无刑"},
    ("父母", "天相"): {"classic": "天相在父母宫，庙旺无刑；紫微同无刑克；廉贞同亦刑；加羊陀火铃空劫早刑。", "vernacular": "庙旺无刑；紫微同无刑克；廉贞同亦刑；加羊陀火铃空劫早刑。", "positive": "", "shadow": "紫微同无刑克；廉贞同亦刑"},
    ("父母", "天魁天钺"): {"classic": "天魁天钺在父母宫，主父母荣贵；同吉星双全。", "vernacular": "主父母荣贵；同吉星双全。", "positive": "主父母荣贵；同吉星双全。", "shadow": ""},
    ("父母", "太阳"): {"classic": "太阳在父母宫，入庙无克；陷地克父；加羊陀火铃空劫克父母早；太阴同无刑，羊陀凑父母全迟刑；巨门同加四杀空劫早克；天梁同无刑。", "vernacular": "入庙无克；陷地克父；加羊陀火铃空劫克父母早；太阴同无刑，羊陀凑父母全迟刑；巨门同加四杀空劫早克；天梁同无刑。", "positive": "", "shadow": "陷地克父；加羊陀火铃空劫克父母早"},
    ("父母", "太阴"): {"classic": "太阴在父母，入庙无克。", "vernacular": "母亲缘深。", "positive": "母亲帮。", "shadow": "依赖母亲；太阴陷则母劳。"},
    ("父母", "左辅"): {"classic": "左辅在父母宫，独守无刑；廉贞同早刑；加文昌相生无刑；加羊陀火铃刑伤退祖二姓延生。", "vernacular": "独守无刑；廉贞同早刑；加文昌相生无刑；加羊陀火铃刑伤退祖二姓延生。", "positive": "", "shadow": "独守无刑；廉贞同早刑"},
    ("父母", "巨门"): {"classic": "巨门在父母宫，陷地伤克弃祖过房；太阳同少和；天机同重拜；天同同或退祖无刑；加羊陀火铃空劫父母不周全。", "vernacular": "陷地伤克弃祖过房；太阳同少和；天机同重拜；天同同或退祖无刑；加羊陀火铃空劫父母不周全。", "positive": "", "shadow": "陷地伤克弃祖过房；太阳同少和"},
    ("父母", "廉贞"): {"classic": "廉贞在父母宫，难为祖重拜；贪狼同早刑；七杀孤克；天府同免刑；破军同早刑；加羊陀火铃空劫父母不周全。", "vernacular": "难为祖重拜；贪狼同早刑；七杀孤克；天府同免刑；破军同早刑；加羊陀火铃空劫父母不周全。", "positive": "", "shadow": "难为祖重拜；贪狼同早刑"},
    ("父母", "擎羊"): {"classic": "擎羊在父母宫，刑克早会日月重重退祖；加吉星众免刑。", "vernacular": "刑克早会日月重重退祖；加吉星众免刑。", "positive": "", "shadow": "刑克早会日月重重退祖"},
    ("父母", "文昌"): {"classic": "文昌在父母宫，加吉星入庙无刑；加羊陀火铃有刑；或退祖二姓延生。", "vernacular": "加吉星入庙无刑；加羊陀火铃有刑；或退祖二姓延生。", "positive": "", "shadow": "加羊陀火铃有刑"},
    ("父母", "文曲"): {"classic": "文曲在父母宫，独守入庙无刑；加羊陀火铃空劫父母俱不周全。", "vernacular": "独守入庙无刑；加羊陀火铃空劫父母俱不周全。", "positive": "", "shadow": "加羊陀火铃空劫父母俱不周全。"},
    ("父母", "斗君"): {"classic": "斗君在父母宫，过度逢吉父母吉利无灾伤；得安逸内外有喜；遇凶则父母不利。", "vernacular": "过度逢吉父母吉利无灾伤；得安逸内外有喜；遇凶则父母不利。", "positive": "得安逸内外有喜", "shadow": "遇凶则父母不利。"},
    ("父母", "武曲"): {"classic": "武曲在父母宫，克早退祖业不刑；贪狼同刑克；七杀同有刑；天相同加羊陀火铃空劫刑伤。", "vernacular": "克早退祖业不刑；贪狼同刑克；七杀同有刑；天相同加羊陀火铃空劫刑伤。", "positive": "", "shadow": "克早退祖业不刑；贪狼同刑克"},
    ("父母", "火星"): {"classic": "火星在父母宫，独守孤克二姓延生；加吉星平和。", "vernacular": "独守孤克二姓延生；加吉星平和。", "positive": "加吉星平和。", "shadow": "独守孤克二姓延生"},
    ("父母", "破军"): {"classic": "破军在父母宫，克早离祖更名寄养免刑；武曲同克早；廉贞同亦早克；紫微同无刑。", "vernacular": "克早离祖更名寄养免刑；武曲同克早；廉贞同亦早克；紫微同无刑。", "positive": "", "shadow": "克早离祖更名寄养免刑；武曲同克早"},
    ("父母", "禄存"): {"classic": "禄存在父母宫，无克；加空劫羊陀火铃早年有破父财，且刑伤中不自成家计。", "vernacular": "无克；加空劫羊陀火铃早年有破父财，且刑伤中不自成家计。", "positive": "", "shadow": "无克"},
    ("父母", "紫微"): {"classic": "紫微在父母宫，无克；天府同亦无刑，加羊陀火铃空劫亦克；天相同无刑；贪狼同无杀加亦无刑；破军同早克。", "vernacular": "无克；天府同亦无刑，加羊陀火铃空劫亦克；天相同无刑；贪狼同无杀加亦无刑；破军同早克。", "positive": "", "shadow": "无克；天府同亦无刑，加羊陀火铃空劫亦克"},
    ("父母", "贪狼"): {"classic": "贪狼在父母宫，陷地早弃祖重拜过房入赘；廉贞同早刑主孤单；紫微同无杀加双全。", "vernacular": "陷地早弃祖重拜过房入赘；廉贞同早刑主孤单；紫微同无杀加双全。", "positive": "", "shadow": "陷地早弃祖重拜过房入赘；廉贞同早刑主孤单"},
    ("父母", "铃星"): {"classic": "铃星在父母宫，刑克孤单二姓安居；重拜父母入赘过房。", "vernacular": "刑克孤单二姓安居；重拜父母入赘过房。", "positive": "", "shadow": "刑克孤单二姓安居"},
    ("父母", "陀罗"): {"classic": "陀罗在父母宫，幼年刑伤；会日月重重退祖二姓安居；加吉星入赘过房或重拜二姓延生。", "vernacular": "幼年刑伤；会日月重重退祖二姓安居；加吉星入赘过房或重拜二姓延生。", "positive": "加吉星入赘过房或重拜二姓延生。", "shadow": "幼年刑伤"},
    ("田宅", "七杀"): {"classic": "七杀在田宅宫，自置；加羊陀火铃空劫有进有退。", "vernacular": "自置；加羊陀火铃空劫有进有退。", "positive": "", "shadow": "加羊陀火铃空劫有进有退。"},
    ("田宅", "天同"): {"classic": "天同在田宅，先少后多。", "vernacular": "田产先少后多，晚年自置。", "positive": "家庭温暖。", "shadow": "别想一夜暴富。"},
    ("田宅", "天府"): {"classic": "天府在田宅宫，田园茂盛守祖自置旺相；紫微同大富；廉贞武曲同守祖业荣昌；见羊陀火铃空劫更少有成败。", "vernacular": "田园茂盛守祖自置旺相；紫微同大富；廉贞武曲同守祖业荣昌；见羊陀火铃空劫更少有成败。", "positive": "田园茂盛守祖自置旺相；廉贞武曲同守祖业荣昌", "shadow": ""},
    ("田宅", "天机"): {"classic": "天机在田宅宫，退祖新创置；巨门同在卯宫有田庄，在酉宫不守祖业先大后小；天梁同有置晚年富；太阴同自置旺相。", "vernacular": "退祖新创置；巨门同在卯宫有田庄，在酉宫不守祖业先大后小；天梁同有置晚年富；太阴同自置旺相。", "positive": "太阴同自置旺相。", "shadow": ""},
    ("田宅", "天梁"): {"classic": "天梁在田宅宫，入庙旺有祖业；天同同先难后易；天机同不见羊陀火铃空劫终有田宅。", "vernacular": "入庙旺有祖业；天同同先难后易；天机同不见羊陀火铃空劫终有田宅。", "positive": "入庙旺有祖业", "shadow": "天同同先难后易；天机同不见羊陀火铃空劫终有田宅。"},
    ("田宅", "天相"): {"classic": "天相在田宅宫，庙旺有分；紫微同自置；武曲同无分；廉贞加羊陀火铃空劫飘零祖业。", "vernacular": "庙旺有分；紫微同自置；武曲同无分；廉贞加羊陀火铃空劫飘零祖业。", "positive": "庙旺有分", "shadow": "廉贞加羊陀火铃空劫飘零祖业。"},
    ("田宅", "太阳"): {"classic": "太阳在田宅宫，入庙得祖业初旺未平；太阴同加吉星田多；巨门同在寅宫旺盛，在申宫退祖不为无田产；陷地逢羊陀火铃空劫全无。", "vernacular": "入庙得祖业初旺未平；太阴同加吉星田多；巨门同在寅宫旺盛，在申宫退祖不为无田产；陷地逢羊陀火铃空劫全无。", "positive": "入庙得祖业初旺未平；太阴同加吉星田多", "shadow": "陷地逢羊陀火铃空劫全无。"},
    ("田宅", "太阴"): {"classic": "太阴在田宅宫，入庙田多；陷地加忌及羊陀火铃空劫田全无；天机同自创置；天同同白手自置；同左右权禄及禄存主多田产。", "vernacular": "入庙田多；陷地加忌及羊陀火铃空劫田全无；天机同自创置；天同同白手自置；同左右权禄及禄存主多田产。", "positive": "入庙田多；同左右权禄及禄存主多田产。", "shadow": "陷地加忌及羊陀火铃空劫田全无"},
    ("田宅", "左辅"): {"classic": "左辅在田宅宫，有祖业；加羊陀火铃空劫退祖田地少；会吉星多。", "vernacular": "有祖业；加羊陀火铃空劫退祖田地少；会吉星多。", "positive": "会吉星多。", "shadow": "加羊陀火铃空劫退祖田地少"},
    ("田宅", "巨门"): {"classic": "巨门在田宅，庙旺横发。", "vernacular": "田产横发也招非。", "positive": "有机会。", "shadow": "不动产纠纷、口舌。"},
    ("田宅", "廉贞"): {"classic": "廉贞在田宅宫，破祖；贪狼同有祖业不耐久；七杀同自置；天府同守见成家业；天相同先无后有。", "vernacular": "破祖；贪狼同有祖业不耐久；七杀同自置；天府同守见成家业；天相同先无后有。", "positive": "天府同守见成家业", "shadow": "破祖"},
    ("田宅", "擎羊"): {"classic": "擎羊在田宅宫，入庙先破后成；陷地加空劫退祖业。", "vernacular": "入庙先破后成；陷地加空劫退祖业。", "positive": "", "shadow": "陷地加空劫退祖业。"},
    ("田宅", "文昌"): {"classic": "文昌在田宅宫，会诸吉田园广置；加羊陀火铃空劫败祖。", "vernacular": "会诸吉田园广置；加羊陀火铃空劫败祖。", "positive": "会诸吉田园广置", "shadow": "加羊陀火铃空劫败祖。"},
    ("田宅", "文曲"): {"classic": "文曲在田宅宫，旺地有分守祖业；加吉星自置；同羊陀火铃空劫凑有进有退。", "vernacular": "旺地有分守祖业；加吉星自置；同羊陀火铃空劫凑有进有退。", "positive": "旺地有分守祖业；加吉星自置", "shadow": "同羊陀火铃空劫凑有进有退。"},
    ("田宅", "斗君"): {"classic": "斗君在田宅宫，过度遇吉星其年田产倍进；逢凶杀忌耗退败。", "vernacular": "过度遇吉星其年田产倍进；逢凶杀忌耗退败。", "positive": "过度遇吉星其年田产倍进", "shadow": "逢凶杀忌耗退败。"},
    ("田宅", "武曲"): {"classic": "武曲在田宅宫，单居旺地得祖父大业，陷地退后方成；破军大耗同破荡家产有也不耐久；天相同先见破后方有；七杀同心不欲；天府同守见成家业；贪狼同晚置见火铃极美田产茂盛，同空劫有进有退。", "vernacular": "单居旺地得祖父大业，陷地退后方成；破军大耗同破荡家产有也不耐久；天相同先见破后方有；七杀同心不欲；天府同守见成家业；贪狼同晚置见火铃极美田产茂盛，同空劫有进有退。", "positive": "天府同守见成家业", "shadow": "破军大耗同破荡家产有也不耐久；天相同先见破后方有"},
    ("田宅", "火星"): {"classic": "火星在田宅宫，独守退祖业；会吉星先无后有；加空劫全无。", "vernacular": "独守退祖业；会吉星先无后有；加空劫全无。", "positive": "会吉星先无后有", "shadow": "加空劫全无。"},
    ("田宅", "破军"): {"classic": "破军在田宅宫，在子午宫守祖业荣常有进退；加羊陀火铃退祖田少；紫微同有见成家业；廉贞同先破后有置；耗忌全无。", "vernacular": "在子午宫守祖业荣常有进退；加羊陀火铃退祖田少；紫微同有见成家业；廉贞同先破后有置；耗忌全无。", "positive": "在子午宫守祖业荣常有进退；紫微同有见成家业", "shadow": "加羊陀火铃退祖田少；廉贞同先破后有置"},
    ("田宅", "禄存"): {"classic": "禄存在田宅宫，田园多旺自置；会吉星承祖业荣昌；加羊陀火铃空劫田宅少。", "vernacular": "田园多旺自置；会吉星承祖业荣昌；加羊陀火铃空劫田宅少。", "positive": "田园多旺自置；会吉星承祖业荣昌", "shadow": "加羊陀火铃空劫田宅少。"},
    ("田宅", "紫微"): {"classic": "紫微在田宅宫，茂盛自置旺相；加羊陀火铃空劫有置有去；破军同退祖；天相同有见成家业，得左右昌曲。", "vernacular": "茂盛自置旺相；加羊陀火铃空劫有置有去；破军同退祖；天相同有见成家业，得左右昌曲。", "positive": "茂盛自置旺相；天相同有见成家业，得左右昌曲。", "shadow": "加羊陀火铃空劫有置有去；破军同退祖"},
    ("田宅", "贪狼"): {"classic": "贪狼在田宅宫，陷宫退祖一世田少；庙旺有祖业也去中未自有置；廉贞同无分；紫微同有祖业；武曲同晚置；见火铃星守祖业有自创，但恐火焚屋宅。", "vernacular": "陷宫退祖一世田少；庙旺有祖业也去中未自有置；廉贞同无分；紫微同有祖业；武曲同晚置；见火铃星守祖业有自创，但恐火焚屋宅。", "positive": "庙旺有祖业也去中未自有置", "shadow": "陷宫退祖一世田少"},
    ("田宅", "铃星"): {"classic": "铃星在田宅宫，退祖；入庙加吉星自有置；见空劫全无。", "vernacular": "退祖；入庙加吉星自有置；见空劫全无。", "positive": "入庙加吉星自有置", "shadow": "见空劫全无。"},
    ("田宅", "陀罗"): {"classic": "陀罗在田宅宫，退祖辛勤度日；加吉星先无后有；加空劫全无。", "vernacular": "退祖辛勤度日；加吉星先无后有；加空劫全无。", "positive": "加吉星先无后有", "shadow": "加空劫全无。"},
    ("疾厄", "七杀"): {"classic": "七杀在疾厄宫，幼年多灾，长主痔疾；武曲同加四杀手足伤残；廉贞同主目疾；加擎羊四肢有伤残。", "vernacular": "幼年多灾，长主痔疾；武曲同加四杀手足伤残；廉贞同主目疾；加擎羊四肢有伤残。", "positive": "幼年多灾，长主痔疾", "shadow": "武曲同加四杀手足伤残；加擎羊四肢有伤残。"},
    ("疾厄", "右弼"): {"classic": "右弼在疾厄宫，独守逢灾有救；见羊陀火铃空劫灾多。", "vernacular": "独守逢灾有救；见羊陀火铃空劫灾多。", "positive": "", "shadow": ""},
    ("疾厄", "天同"): {"classic": "天同在疾厄宫，入庙灾少；巨门同心气疾；太阴同加羊火血气疾；天梁同加四杀心气疾。", "vernacular": "入庙灾少；巨门同心气疾；太阴同加羊火血气疾；天梁同加四杀心气疾。", "positive": "", "shadow": ""},
    ("疾厄", "天府"): {"classic": "天府在疾厄宫，灾少临灾有救；紫微同灾少；加羊陀火铃空劫有疯疾；廉贞同加劫杀空亡，半途伤残。", "vernacular": "灾少临灾有救；紫微同灾少；加羊陀火铃空劫有疯疾；廉贞同加劫杀空亡，半途伤残。", "positive": "", "shadow": "灾少临灾有救；紫微同灾少"},
    ("疾厄", "天机"): {"classic": "天机在疾厄，襁褓多灾。", "vernacular": "幼年多灾，注意神经、肝胆、手足、失眠。", "positive": "警觉、恢复力。", "shadow": "思虑过度，神经痛。"},
    ("疾厄", "天梁"): {"classic": "天梁在疾厄宫，下部疾；加四杀心气疾。", "vernacular": "下部疾；加四杀心气疾。", "positive": "", "shadow": ""},
    ("疾厄", "天相"): {"classic": "天相在疾厄宫，灾少面皮黄肿血气之疾；紫微同灾少；武曲同加四杀破相；廉贞同加空劫手足伤。", "vernacular": "灾少面皮黄肿血气之疾；紫微同灾少；武曲同加四杀破相；廉贞同加空劫手足伤。", "positive": "", "shadow": "灾少面皮黄肿血气之疾；紫微同灾少"},
    ("疾厄", "太阳"): {"classic": "太阳在疾厄宫，头风；太阴同加化忌，羊陀主眼目有伤；陷宫亦主目疾欠光明。", "vernacular": "头风；太阴同加化忌，羊陀主眼目有伤；陷宫亦主目疾欠光明。", "positive": "", "shadow": "太阴同加化忌，羊陀主眼目有伤；陷宫亦主目疾欠光明。"},
    ("疾厄", "太阴"): {"classic": "太阴在疾厄宫，庙旺无灾；陷地灾多主劳伤之症，女人主大伤残；太阳同加吉一生灾少；羊陀火铃眼目疾；加空劫有疯疾；天同同加羊陀陷宫主加症，同火铃多灾。", "vernacular": "庙旺无灾；陷地灾多主劳伤之症，女人主大伤残；太阳同加吉一生灾少；羊陀火铃眼目疾；加空劫有疯疾；天同同加羊陀陷宫主加症，同火铃多灾。", "positive": "庙旺无灾", "shadow": "加空劫有疯疾"},
    ("疾厄", "左辅"): {"classic": "左辅在疾厄宫，独守平和；加吉星灾少；见羊陀火铃空劫常有灾。", "vernacular": "独守平和；加吉星灾少；见羊陀火铃空劫常有灾。", "positive": "", "shadow": "见羊陀火铃空劫常有灾。"},
    ("疾厄", "巨门"): {"classic": "巨门在疾厄宫，少年脓血之厄；太阳同有头疯疽；天同同下部主有疯症；加羊火酒色之疾；加忌有耳目之忧。", "vernacular": "少年脓血之厄；太阳同有头疯疽；天同同下部主有疯症；加羊火酒色之疾；加忌有耳目之忧。", "positive": "", "shadow": "少年脓血之厄"},
    ("疾厄", "廉贞"): {"classic": "廉贞在疾厄宫，襁褓灾疮腰足之疾；入庙加吉和平；遇贪狼同陷地眼疾灾多；七杀破军天府同灾少。", "vernacular": "襁褓灾疮腰足之疾；入庙加吉和平；遇贪狼同陷地眼疾灾多；七杀破军天府同灾少。", "positive": "入庙加吉和平", "shadow": "七杀破军天府同灾少。"},
    ("疾厄", "擎羊"): {"classic": "擎羊在疾厄宫，有头疯之症；或四肢欠力；头面破相延寿；加吉星灾少。", "vernacular": "有头疯之症；或四肢欠力；头面破相延寿；加吉星灾少。", "positive": "", "shadow": "或四肢欠力；头面破相延寿"},
    ("疾厄", "文昌"): {"classic": "文昌在疾厄宫，独守灾少；加羊陀火铃空劫灾多；同诸吉星一生无灾。", "vernacular": "独守灾少；加羊陀火铃空劫灾多；同诸吉星一生无灾。", "positive": "同诸吉星一生无灾。", "shadow": "独守灾少"},
    ("疾厄", "文曲"): {"classic": "文曲在疾厄宫，灾少；加吉星一世无灾；加羊陀火铃空劫，坐陷宫灾有。", "vernacular": "灾少；加吉星一世无灾；加羊陀火铃空劫，坐陷宫灾有。", "positive": "加吉星一世无灾", "shadow": "灾少；加羊陀火铃空劫，坐陷宫灾有。"},
    ("疾厄", "斗君"): {"classic": "斗君在疾厄宫，遇吉身心安宁其年无灾；遇凶杀本生人有畏忌其年多灾。", "vernacular": "遇吉身心安宁其年无灾；遇凶杀本生人有畏忌其年多灾。", "positive": "遇吉身心安宁其年无灾", "shadow": ""},
    ("疾厄", "武曲"): {"classic": "武曲在疾厄宫，襁褓灾迍手足头面有伤；羊陀同一生常有灾；天相同招暗疾；七杀同血疾；贪狼同庙旺无疾，陷地加四杀眼手足疾痔疾疯疮。", "vernacular": "襁褓灾迍手足头面有伤；羊陀同一生常有灾；天相同招暗疾；七杀同血疾；贪狼同庙旺无疾，陷地加四杀眼手足疾痔疾疯疮。", "positive": "", "shadow": "襁褓灾迍手足头面有伤"},
    ("疾厄", "火星铃星"): {"classic": "火星铃星在疾厄宫，主一生灾少；身体健旺伶俐。", "vernacular": "主一生灾少；身体健旺伶俐。", "positive": "身体健旺伶俐。", "shadow": "主一生灾少"},
    ("疾厄", "破军"): {"classic": "破军在疾厄宫，幼年疮癞脓血羸黄；武曲同目疾；紫微同灾少；廉贞同加羊火四肢有伤残。", "vernacular": "幼年疮癞脓血羸黄；武曲同目疾；紫微同灾少；廉贞同加羊火四肢有伤残。", "positive": "", "shadow": "紫微同灾少；廉贞同加羊火四肢有伤残。"},
    ("疾厄", "禄存"): {"classic": "禄存在疾厄宫，少年多灾；加吉星灾少；见羊陀火铃四肢必伤残；加空劫玫暗疾延生。", "vernacular": "少年多灾；加吉星灾少；见羊陀火铃四肢必伤残；加空劫玫暗疾延生。", "positive": "", "shadow": "见羊陀火铃四肢必伤残；加空劫玫暗疾延生。"},
    ("疾厄", "紫微"): {"classic": "紫微在疾厄宫，灾少；天府同亦少；天相同皮胎劳；加破军血气不和；同羊铃主有暗疾；加空劫主疢疾心气疾。", "vernacular": "灾少；天府同亦少；天相同皮胎劳；加破军血气不和；同羊铃主有暗疾；加空劫主疢疾心气疾。", "positive": "", "shadow": "灾少；天府同亦少"},
    ("疾厄", "贪狼"): {"classic": "贪狼在疾厄宫，庙旺无疾；陷地加四杀，眼手足疾痔疾疯疮。", "vernacular": "庙旺无疾；陷地加四杀，眼手足疾痔疾疯疮。", "positive": "庙旺无疾", "shadow": "陷地加四杀，眼手足疾痔疾疯疮。"},
    ("疾厄", "陀罗"): {"classic": "陀罗在疾厄宫，幼年灾；磨唇齿头面有伤破方可延寿。", "vernacular": "幼年灾；磨唇齿头面有伤破方可延寿。", "positive": "", "shadow": "磨唇齿头面有伤破方可延寿。"},
    ("福德", "七杀"): {"classic": "七杀在福德宫，入庙享福；陷地加羊陀火铃劳心费力；武曲同欠安；廉贞同辛勤；紫微同先劳后逸末年方如意。", "vernacular": "入庙享福；陷地加羊陀火铃劳心费力；武曲同欠安；廉贞同辛勤；紫微同先劳后逸末年方如意。", "positive": "入庙享福", "shadow": "陷地加羊陀火铃劳心费力；武曲同欠安"},
    ("福德", "右弼"): {"classic": "右弼在福德宫，享福；加吉星安乐；加羊陀火铃空劫多忧。", "vernacular": "享福；加吉星安乐；加羊陀火铃空劫多忧。", "positive": "加吉星安乐", "shadow": ""},
    ("福德", "天同"): {"classic": "天同在福德宫，快乐有福有寿；巨门同多忧少喜；太阴同享福；天梁同清闲快乐。", "vernacular": "快乐有福有寿；巨门同多忧少喜；太阴同享福；天梁同清闲快乐。", "positive": "快乐有福有寿", "shadow": ""},
    ("福德", "天府"): {"classic": "天府在福德宫，安静享福；紫微同快乐；廉贞同身安心忙；武曲同早年辛苦中晚安乐；加羊陀火铃空劫耗忌劳苦过日。", "vernacular": "安静享福；紫微同快乐；廉贞同身安心忙；武曲同早年辛苦中晚安乐；加羊陀火铃空劫耗忌劳苦过日。", "positive": "", "shadow": "加羊陀火铃空劫耗忌劳苦过日。"},
    ("福德", "天机"): {"classic": "天机在福德宫，先劳后逸；巨门同劳力欠安；天梁同享福；太阴同主快乐；加羊陀火铃空劫奔走不得宁静。", "vernacular": "先劳后逸；巨门同劳力欠安；天梁同享福；太阴同主快乐；加羊陀火铃空劫奔走不得宁静。", "positive": "", "shadow": "巨门同劳力欠安；加羊陀火铃空劫奔走不得宁静。"},
    ("福德", "天梁"): {"classic": "天梁在福德宫，享福清闲快乐；加羊陀火铃空劫劳心。", "vernacular": "享福清闲快乐；加羊陀火铃空劫劳心。", "positive": "", "shadow": "加羊陀火铃空劫劳心。"},
    ("福德", "天相"): {"classic": "天相在福德宫，安逸享福有寿；紫微同快乐；天机同忙中吉；太阳同福寿双全；加羊陀火铃空劫不得心静。", "vernacular": "安逸享福有寿；紫微同快乐；天机同忙中吉；太阳同福寿双全；加羊陀火铃空劫不得心静。", "positive": "天机同忙中吉", "shadow": "加羊陀火铃空劫不得心静。"},
    ("福德", "天魁天钺"): {"classic": "天魁天钺在福德宫，享福；加吉星有贵人助。", "vernacular": "享福；加吉星有贵人助。", "positive": "加吉星有贵人助。", "shadow": ""},
    ("福德", "太阳"): {"classic": "太阳在福德宫，忙中发福；太阴同快乐；巨门同费力欠安；天梁同快乐；女人会吉星招贤明之夫享福；加羊陀火铃空劫忌耗终身不美。", "vernacular": "忙中发福；太阴同快乐；巨门同费力欠安；天梁同快乐；女人会吉星招贤明之夫享福；加羊陀火铃空劫忌耗终身不美。", "positive": "女人会吉星招贤明之夫享福", "shadow": "巨门同费力欠安；加羊陀火铃空劫忌耗终身不美。"},
    ("福德", "太阴"): {"classic": "太阴在福德宫，入庙享福快乐；太阳同极美僧道亦清洁；天机同心忙；天同同安静无忧；加羊陀火铃空劫有忧有喜不得安静。", "vernacular": "入庙享福快乐；太阳同极美僧道亦清洁；天机同心忙；天同同安静无忧；加羊陀火铃空劫有忧有喜不得安静。", "positive": "入庙享福快乐", "shadow": ""},
    ("福德", "左辅"): {"classic": "左辅在福德宫，享福；加吉星快乐；加羊陀火铃空劫操心。", "vernacular": "享福；加吉星快乐；加羊陀火铃空劫操心。", "positive": "加吉星快乐", "shadow": "加羊陀火铃空劫操心。"},
    ("福德", "巨门"): {"classic": "巨门在福德宫，劳力不安；太阳同有忧有喜；天机同心忙不安；天同同享福；加羊陀火铃空劫生平多忧。", "vernacular": "劳力不安；太阳同有忧有喜；天机同心忙不安；天同同享福；加羊陀火铃空劫生平多忧。", "positive": "太阳同有忧有喜", "shadow": ""},
    ("福德", "廉贞"): {"classic": "廉贞在福德宫，独守忙中生福；天相同有福有寿；天府同安乐无忧；破军同不守静劳心费力；再加羊陀火铃劳苦终身末年如意。", "vernacular": "独守忙中生福；天相同有福有寿；天府同安乐无忧；破军同不守静劳心费力；再加羊陀火铃劳苦终身末年如意。", "positive": "天相同有福有寿", "shadow": "破军同不守静劳心费力"},
    ("福德", "擎羊陀罗"): {"classic": "擎羊陀罗在福德宫，劳心；加吉星劳碌有福；加空劫多忧。", "vernacular": "劳心；加吉星劳碌有福；加空劫多忧。", "positive": "加吉星劳碌有福", "shadow": ""},
    ("福德", "文昌"): {"classic": "文昌在福德宫，享福；加吉星清闲快乐；加羊陀火铃空劫劳心。", "vernacular": "享福；加吉星清闲快乐；加羊陀火铃空劫劳心。", "positive": "加吉星清闲快乐", "shadow": "加羊陀火铃空劫劳心。"},
    ("福德", "文曲"): {"classic": "文曲在福德宫，享福；加吉星有口福；加羊陀火铃空劫多忧。", "vernacular": "享福；加吉星有口福；加羊陀火铃空劫多忧。", "positive": "加吉星有口福", "shadow": ""},
    ("福德", "武曲"): {"classic": "武曲在福德宫，劳心费力，入庙安然享福；破军同东走西行不宁静；天相同老境安康；七杀同欠安康；贪狼同晚年享福见火铃安逸；加羊陀操心得力。", "vernacular": "劳心费力，入庙安然享福；破军同东走西行不宁静；天相同老境安康；七杀同欠安康；贪狼同晚年享福见火铃安逸；加羊陀操心得力。", "positive": "劳心费力，入庙安然享福；加羊陀操心得力。", "shadow": "破军同东走西行不宁静；七杀同欠安康"},
    ("福德", "火星铃星"): {"classic": "火星铃星在福德宫，操心；加吉星闹中享福；加空劫多忧。", "vernacular": "操心；加吉星闹中享福；加空劫多忧。", "positive": "加吉星闹中享福", "shadow": ""},
    ("福德", "破军"): {"classic": "破军在福德宫，劳心费力；武曲同欠安；廉贞同辛勤；紫微同安乐；加羊陀火铃空劫操心不得宁静。", "vernacular": "劳心费力；武曲同欠安；廉贞同辛勤；紫微同安乐；加羊陀火铃空劫操心不得宁静。", "positive": "", "shadow": "武曲同欠安；加羊陀火铃空劫操心不得宁静。"},
    ("福德", "禄存"): {"classic": "禄存在福德宫，享福；加吉星厚福；加羊陀火铃空劫操心。", "vernacular": "享福；加吉星厚福；加羊陀火铃空劫操心。", "positive": "加吉星厚福", "shadow": "加羊陀火铃空劫操心。"},
    ("福德", "紫微"): {"classic": "紫微在福德宫，福厚享福安乐；天府天相同终身获吉；破军同劳心费力不安；加羊陀铃空劫福薄；天机同享福终身。", "vernacular": "福厚享福安乐；天府天相同终身获吉；破军同劳心费力不安；加羊陀铃空劫福薄；天机同享福终身。", "positive": "天府天相同终身获吉", "shadow": "破军同劳心费力不安；加羊陀铃空劫福薄"},
    ("福德", "贪狼"): {"classic": "贪狼在福德，劳心不安。", "vernacular": "精神多欲，劳心。", "positive": "欲望、追求。", "shadow": "想太多，学放下。"},
    ("财帛", "七杀"): {"classic": "七杀在财帛宫，白手生财成家；见羊陀火铃空劫耗忌，成败不聚。", "vernacular": "白手生财成家；见羊陀火铃空劫耗忌，成败不聚。", "positive": "白手生财成家", "shadow": ""},
    ("财帛", "天同"): {"classic": "天同在财帛宫，白手生财晚发；巨门同财气进退；天梁同财大旺；加四杀空劫或九流人生财成家。", "vernacular": "白手生财晚发；巨门同财气进退；天梁同财大旺；加四杀空劫或九流人生财成家。", "positive": "天梁同财大旺", "shadow": ""},
    ("财帛", "天府"): {"classic": "天府在财帛宫，富足；见羊陀火铃空劫有成败；紫微同巨积；廉贞武曲同加权禄为富奢翁。", "vernacular": "富足；见羊陀火铃空劫有成败；紫微同巨积；廉贞武曲同加权禄为富奢翁。", "positive": "", "shadow": ""},
    ("财帛", "天机"): {"classic": "天机在财帛宫，劳心费力生财；巨门同闹中求取；天梁同机关巧计生外财；太阴同陷宫成败；加羊陀火铃空劫一生有成有败。", "vernacular": "劳心费力生财；巨门同闹中求取；天梁同机关巧计生外财；太阴同陷宫成败；加羊陀火铃空劫一生有成有败。", "positive": "", "shadow": ""},
    ("财帛", "天梁"): {"classic": "天梁在财帛宫，富足入庙上等富贵；陷宫辛勤求财度日；天同同白手生财胜祖；天机同劳心用力发财不多；加羊陀火铃空劫先难后易仅足度日。", "vernacular": "富足入庙上等富贵；陷宫辛勤求财度日；天同同白手生财胜祖；天机同劳心用力发财不多；加羊陀火铃空劫先难后易仅足度日。", "positive": "富足入庙上等富贵；天机同劳心用力发财不多", "shadow": "陷宫辛勤求财度日；加羊陀火铃空劫先难后易仅足度日。"},
    ("财帛", "天相"): {"classic": "天相在财帛宫，富足；紫微同财气横进；武曲同加四杀百工生财；廉贞同商贾生财；加羊陀火铃空劫耗忌，成败无积聚。", "vernacular": "富足；紫微同财气横进；武曲同加四杀百工生财；廉贞同商贾生财；加羊陀火铃空劫耗忌，成败无积聚。", "positive": "", "shadow": ""},
    ("财帛", "天魁天钺"): {"classic": "天魁天钺在财帛宫，主清高中生财一生遂意。", "vernacular": "主清高中生财一生遂意。", "positive": "主清高中生财一生遂意。", "shadow": ""},
    ("财帛", "太阳"): {"classic": "太阳在财帛宫，入庙丰足；陷宫劳碌不遂；太阴同加左右吉星发财不小；禄存同操心得财大富；巨门同早年成败中未充盈。", "vernacular": "入庙丰足；陷宫劳碌不遂；太阴同加左右吉星发财不小；禄存同操心得财大富；巨门同早年成败中未充盈。", "positive": "入庙丰足；太阴同加左右吉星发财不小", "shadow": ""},
    ("财帛", "太阴"): {"classic": "太阴在财帛宫，入庙富足仓箱；陷宫成败不聚；太阳同先少后多；天机同白手生财；天同同财旺生身；禄存兼左右同主大富。", "vernacular": "入庙富足仓箱；陷宫成败不聚；太阳同先少后多；天机同白手生财；天同同财旺生身；禄存兼左右同主大富。", "positive": "入庙富足仓箱；天同同财旺生身", "shadow": ""},
    ("财帛", "左辅右弼"): {"classic": "左辅右弼在财帛宫，诸宫富足；会诸吉星得贵人财；加羊陀火铃空劫耗忌，主成败而不聚。", "vernacular": "诸宫富足；会诸吉星得贵人财；加羊陀火铃空劫耗忌，主成败而不聚。", "positive": "会诸吉星得贵人财", "shadow": ""},
    ("财帛", "巨门"): {"classic": "巨门在财帛宫，白手生财成家宜闹中取；气高之人横破；太阳同入庙守见成家计；天机同财气生身；天同同白手成家九流人吉；加羊陀火铃空劫破财多端。", "vernacular": "白手生财成家宜闹中取；气高之人横破；太阳同入庙守见成家计；天机同财气生身；天同同白手成家九流人吉；加羊陀火铃空劫破财多端。", "positive": "白手生财成家宜闹中取；太阳同入庙守见成家计", "shadow": "气高之人横破"},
    ("财帛", "廉贞"): {"classic": "廉贞在财帛宫，在申寅宫闹中生财；陷宫先难后易；贪狼同横发横破；见羊火极生横进之财；七杀同闹中取；天相同富足仓箱；如耗劫天空常在官府中破财。", "vernacular": "在申寅宫闹中生财；陷宫先难后易；贪狼同横发横破；见羊火极生横进之财；七杀同闹中取；天相同富足仓箱；如耗劫天空常在官府中破财。", "positive": "", "shadow": "陷宫先难后易；贪狼同横发横破"},
    ("财帛", "擎羊"): {"classic": "擎羊在财帛宫，辰戌丑未宫闹中生财；陷地破祖不聚终不能发达；只鱼盐污垢中生财。", "vernacular": "辰戌丑未宫闹中生财；陷地破祖不聚终不能发达；只鱼盐污垢中生财。", "positive": "", "shadow": "陷地破祖不聚终不能发达"},
    ("财帛", "文昌"): {"classic": "文昌在财帛宫，富足仓箱；加吉星财气旺；巨门同富；陷地将同陀火铃空败寒儒辈。", "vernacular": "富足仓箱；加吉星财气旺；巨门同富；陷地将同陀火铃空败寒儒辈。", "positive": "加吉星财气旺", "shadow": "陷地将同陀火铃空败寒儒辈。"},
    ("财帛", "文曲"): {"classic": "文曲在财帛宫，入庙富足；加吉星得贵人财；加羊陀火铃空劫家忌；东来西去成败不遂。", "vernacular": "入庙富足；加吉星得贵人财；加羊陀火铃空劫家忌；东来西去成败不遂。", "positive": "入庙富足；加吉星得贵人财", "shadow": "加羊陀火铃空劫家忌"},
    ("财帛", "斗君"): {"classic": "斗君在财帛宫，遇吉其月发财；遇凶恶空劫耗忌星其月损财，招口舌官非为财而逃。", "vernacular": "遇吉其月发财；遇凶恶空劫耗忌星其月损财，招口舌官非为财而逃。", "positive": "遇吉其月发财", "shadow": "遇凶恶空劫耗忌星其月损财，招口舌官非为财而逃。"},
    ("财帛", "武曲"): {"classic": "武曲在财帛宫，丰足化吉有巨万家资，无吉加闹中进财；破军同东来西去先无后有；天相同财帛丰盈遇贵生财；七杀同白手生财；贪狼同三十年后方发财；加羊陀火铃不聚极怕空亡。", "vernacular": "丰足化吉有巨万家资，无吉加闹中进财；破军同东来西去先无后有；天相同财帛丰盈遇贵生财；七杀同白手生财；贪狼同三十年后方发财；加羊陀火铃不聚极怕空亡。", "positive": "丰足化吉有巨万家资，无吉加闹中进财；天相同财帛丰盈遇贵生财", "shadow": "破军同东来西去先无后有；加羊陀火铃不聚极怕空亡。"},
    ("财帛", "火星"): {"classic": "火星在财帛宫，独守横发横破；陷宫辛勤；加吉星财多遂志。", "vernacular": "独守横发横破；陷宫辛勤；加吉星财多遂志。", "positive": "加吉星财多遂志。", "shadow": "独守横发横破；陷宫辛勤"},
    ("财帛", "破军"): {"classic": "破军在财帛宫，在子午宫多有金银蓄积，辰戌旺宫亦财盛；陷宫破祖不聚；武曲同守巳亥东来西去；紫微同先去后生；廉贞同劳碌生财先难后遂；加空劫极贫。", "vernacular": "在子午宫多有金银蓄积，辰戌旺宫亦财盛；陷宫破祖不聚；武曲同守巳亥东来西去；紫微同先去后生；廉贞同劳碌生财先难后遂；加空劫极贫。", "positive": "在子午宫多有金银蓄积，辰戌旺宫亦财盛", "shadow": "陷宫破祖不聚；加空劫极贫。"},
    ("财帛", "禄存"): {"classic": "禄存在财帛宫，富足仓箱堆金积玉；加吉美不待劳而财自加；羊陀火铃空劫耗忌先无后有。", "vernacular": "富足仓箱堆金积玉；加吉美不待劳而财自加；羊陀火铃空劫耗忌先无后有。", "positive": "加吉美不待劳而财自加", "shadow": "羊陀火铃空劫耗忌先无后有。"},
    ("财帛", "紫微"): {"classic": "紫微在财帛，丰足仓箱。", "vernacular": "财靠地位、平台、管理，非纯经商暴富。", "positive": "稳定、高端、管理财。", "shadow": "别想暴富，面子开销。"},
    ("财帛", "贪狼"): {"classic": "贪狼在财帛宫，庙旺横发；陷地贫穷；紫微同守现成，家计自后更丰盈；见火星三十年前成败，三十年后横发。", "vernacular": "庙旺横发；陷地贫穷；紫微同守现成，家计自后更丰盈；见火星三十年前成败，三十年后横发。", "positive": "庙旺横发；紫微同守现成，家计自后更丰盈", "shadow": "陷地贫穷"},
    ("财帛", "铃星"): {"classic": "铃星在财帛宫，入庙独守横发；陷地孤寒辛苦度日。", "vernacular": "入庙独守横发；陷地孤寒辛苦度日。", "positive": "入庙独守横发", "shadow": "陷地孤寒辛苦度日。"},
    ("财帛", "陀罗"): {"classic": "陀罗在财帛宫，闹中生财；陷宫辛勤求财度日；加空劫东来西去。", "vernacular": "闹中生财；陷宫辛勤求财度日；加空劫东来西去。", "positive": "", "shadow": "陷宫辛勤求财度日；加空劫东来西去。"},
    ("迁移", "七杀"): {"classic": "七杀在迁移，在外日多在家日少。", "vernacular": "外出奔波，动中得吉。", "positive": "异地发展、开创。", "shadow": "太累，防意外。"},
    ("迁移", "右弼"): {"classic": "右弼在迁移宫，出外遇贵人扶持发达，不宜静守；加羊陀火铃空劫，在外与人有争竞。", "vernacular": "出外遇贵人扶持发达，不宜静守；加羊陀火铃空劫，在外与人有争竞。", "positive": "出外遇贵人扶持发达，不宜静守", "shadow": "加羊陀火铃空劫，在外与人有争竞。"},
    ("迁移", "天同"): {"classic": "天同在迁移宫，出外遇贵人扶持；巨门同劳心；太阴同辛苦；天梁同贵人见爱；加羊陀火铃空劫在外少遂志。", "vernacular": "出外遇贵人扶持；巨门同劳心；太阴同辛苦；天梁同贵人见爱；加羊陀火铃空劫在外少遂志。", "positive": "出外遇贵人扶持；天梁同贵人见爱", "shadow": ""},
    ("迁移", "天府"): {"classic": "天府在迁移宫，出外遇贵人扶持，同紫微发福；廉贞武曲闹中取财作巨商。", "vernacular": "出外遇贵人扶持，同紫微发福；廉贞武曲闹中取财作巨商。", "positive": "出外遇贵人扶持，同紫微发福", "shadow": ""},
    ("迁移", "天机"): {"classic": "天机在迁移宫，出外遇贵居家有是非；巨门同动中则吉；天梁同出外称意；太阴同忙中吉；加羊陀火铃在外多是非身不安静。", "vernacular": "出外遇贵居家有是非；巨门同动中则吉；天梁同出外称意；太阴同忙中吉；加羊陀火铃在外多是非身不安静。", "positive": "巨门同动中则吉；太阴同忙中吉", "shadow": ""},
    ("迁移", "天梁"): {"classic": "天梁在迁移宫，出外近贵贵人成就；天同同福厚；天机同艺术途中走。", "vernacular": "出外近贵贵人成就；天同同福厚；天机同艺术途中走。", "positive": "出外近贵贵人成就", "shadow": "天机同艺术途中走。"},
    ("迁移", "天相"): {"classic": "天相在迁移宫，出外贵人提撕；紫微同吉利；武曲同在外发财；廉贞同加羊陀火铃招是非小人不足。", "vernacular": "出外贵人提撕；紫微同吉利；武曲同在外发财；廉贞同加羊陀火铃招是非小人不足。", "positive": "出外贵人提撕；紫微同吉利", "shadow": "廉贞同加羊陀火铃招是非小人不足。"},
    ("迁移", "太阳"): {"classic": "太阳在迁移宫，宜出外发福不耐静守；太阴同出外忙中吉；巨门劳心；加羊陀火铃空劫在外心身不清闲。", "vernacular": "宜出外发福不耐静守；太阴同出外忙中吉；巨门劳心；加羊陀火铃空劫在外心身不清闲。", "positive": "太阴同出外忙中吉", "shadow": "加羊陀火铃空劫在外心身不清闲。"},
    ("迁移", "太阴"): {"classic": "太阴在迁移宫，入庙出外遇贵发财；陷宫招是非；太阳同极美；天同同在庙旺地出外白手生财成家。", "vernacular": "入庙出外遇贵发财；陷宫招是非；太阳同极美；天同同在庙旺地出外白手生财成家。", "positive": "入庙出外遇贵发财；天同同在庙旺地出外白手生财成家。", "shadow": "陷宫招是非"},
    ("迁移", "左辅"): {"classic": "左辅在迁移宫，动中贵人扶持发福；加羊陀火铃下人不足多招是非。", "vernacular": "动中贵人扶持发福；加羊陀火铃下人不足多招是非。", "positive": "动中贵人扶持发福", "shadow": ""},
    ("迁移", "巨门"): {"classic": "巨门在迁移宫，出外劳心不安，与人不足多是非；加羊陀火铃空劫愈甚。", "vernacular": "出外劳心不安，与人不足多是非；加羊陀火铃空劫愈甚。", "positive": "", "shadow": "加羊陀火铃空劫愈甚。"},
    ("迁移", "廉贞"): {"classic": "廉贞在迁移宫，出外通达近贵在家日少；贪狼同闹中立脚；七杀同在外广招财；天相同动中则吉；加羊陀并三方有凶杀死于外道。", "vernacular": "出外通达近贵在家日少；贪狼同闹中立脚；七杀同在外广招财；天相同动中则吉；加羊陀并三方有凶杀死于外道。", "positive": "天相同动中则吉", "shadow": "加羊陀并三方有凶杀死于外道。"},
    ("迁移", "擎羊"): {"classic": "擎羊在迁移宫，入庙在外衣禄遂心；加吉星闹中发财；陷地有成下人多不足。", "vernacular": "入庙在外衣禄遂心；加吉星闹中发财；陷地有成下人多不足。", "positive": "入庙在外衣禄遂心；加吉星闹中发财", "shadow": ""},
    ("迁移", "文昌"): {"classic": "文昌在迁移宫，出外遇贵发达，小人不足；加羊陀火铃空劫在外欠安宁。", "vernacular": "出外遇贵发达，小人不足；加羊陀火铃空劫在外欠安宁。", "positive": "出外遇贵发达，小人不足", "shadow": "加羊陀火铃空劫在外欠安宁。"},
    ("迁移", "文曲"): {"classic": "文曲在迁移宫，在外近贵；加吉星得财；加羊陀火铃少遂志。", "vernacular": "在外近贵；加吉星得财；加羊陀火铃少遂志。", "positive": "在外近贵；加吉星得财", "shadow": ""},
    ("迁移", "斗君"): {"classic": "斗君在迁移宫，过度遇吉动中吉；遇凶杀动中有口舌。", "vernacular": "过度遇吉动中吉；遇凶杀动中有口舌。", "positive": "过度遇吉动中吉", "shadow": "遇凶杀动中有口舌。"},
    ("迁移", "武曲"): {"classic": "武曲在迁移宫，闹忙中进不宜静守；贪狼同作巨商；七杀破军同身心不得静守；加羊陀火铃在外招是非。", "vernacular": "闹忙中进不宜静守；贪狼同作巨商；七杀破军同身心不得静守；加羊陀火铃在外招是非。", "positive": "", "shadow": "七杀破军同身心不得静守；加羊陀火铃在外招是非。"},
    ("迁移", "火星"): {"classic": "火星在迁移宫，独守出外不安；加吉星闹中进财；加羊陀空劫招是非在外少遂志。", "vernacular": "独守出外不安；加吉星闹中进财；加羊陀空劫招是非在外少遂志。", "positive": "加吉星闹中进财", "shadow": ""},
    ("迁移", "破军"): {"classic": "破军在迁移宫，出外劳心不宁；入庙在外峥嵘；加羊陀火铃奔驰巧艺走途中；加文昌文曲武曲相会优伶之人。", "vernacular": "出外劳心不宁；入庙在外峥嵘；加羊陀火铃奔驰巧艺走途中；加文昌文曲武曲相会优伶之人。", "positive": "入庙在外峥嵘；加文昌文曲武曲相会优伶之人。", "shadow": "加羊陀火铃奔驰巧艺走途中"},
    ("迁移", "禄存"): {"classic": "禄存在迁移宫，出外衣禄遂心；会羊陀火铃空劫与人多不足意。", "vernacular": "出外衣禄遂心；会羊陀火铃空劫与人多不足意。", "positive": "出外衣禄遂心", "shadow": ""},
    ("迁移", "紫微"): {"classic": "紫微在迁移宫，同左右出外贵人扶持发福；天府同出入通达；天相同在外发财；破军同贵人见爱小人不足；加羊陀火铃空劫在外不安静。", "vernacular": "同左右出外贵人扶持发福；天府同出入通达；天相同在外发财；破军同贵人见爱小人不足；加羊陀火铃空劫在外不安静。", "positive": "同左右出外贵人扶持发福", "shadow": "加羊陀火铃空劫在外不安静。"},
    ("迁移", "贪狼"): {"classic": "贪狼在迁移宫，独守在外劳碌闹中横进财；廉贞同加四杀在外艰难；武曲同作巨商；加羊陀火铃空劫耗杀流年遭兵劫。", "vernacular": "独守在外劳碌闹中横进财；廉贞同加四杀在外艰难；武曲同作巨商；加羊陀火铃空劫耗杀流年遭兵劫。", "positive": "", "shadow": "廉贞同加四杀在外艰难；加羊陀火铃空劫耗杀流年遭兵劫。"},
    ("迁移", "铃星"): {"classic": "铃星在迁移宫，有吉星同在外吉；加羊火铃空劫不足招是非。", "vernacular": "有吉星同在外吉；加羊火铃空劫不足招是非。", "positive": "有吉星同在外吉", "shadow": "加羊火铃空劫不足招是非。"},
    ("迁移", "陀罗"): {"classic": "陀罗在迁移宫，会吉星在外遇贵得财；陷地加羊火铃星空劫多招是非下人不足。", "vernacular": "会吉星在外遇贵得财；陷地加羊火铃星空劫多招是非下人不足。", "positive": "会吉星在外遇贵得财", "shadow": ""},
}


def get_interpretation(rule_id: str, chart_facts: dict | None = None) -> dict:
    """获取释义，支持条件判定。
    
    chart_facts可选，包含：
    - bright: 星曜亮度（庙旺利陷平）
    - has_煞: 是否加煞（羊陀火铃空劫）
    - has_吉: 是否加吉（左右昌曲魁钺禄存）
    - has_忌: 是否化忌冲破
    
    返回：
    - 无chart_facts: 原样返回四层
    - 有chart_facts: 做条件判定，只返回命中的那一面
    """
    chart_facts = chart_facts or {}
    
    result = None
    if rule_id in PATTERN_INTERPRETATION:
        result = dict(PATTERN_INTERPRETATION[rule_id])
    elif rule_id.startswith("PALACE-"):
        parts = rule_id.split("-")
        if len(parts) >= 3:
            palace = parts[1]
            star = parts[2]
            if (palace, star) in VERDICT_INTERPRETATION:
                v = VERDICT_INTERPRETATION[(palace, star)]
                result = {
                    "name": f"{star}在{palace}",
                    "dim": "性格",
                    "classic": v.get("classic", ""),
                    "vernacular": v.get("vernacular", ""),
                    "positive": v.get("positive", ""),
                    "shadow": v.get("shadow", ""),
                }
    if result is None:
        return {"name": rule_id, "dim": "四化体用", "classic": "", "vernacular": "", "positive": "", "shadow": ""}
    
    # 条件判定：按iztro实际亮度（庙/利/陷三档）
    bright = chart_facts.get("bright", "")
    has_煞 = chart_facts.get("has_煞", False)
    has_吉 = chart_facts.get("has_吉", False)
    has_忌 = chart_facts.get("has_忌", False)
    
    bad = has_煞 or has_忌
    
    # 四档亮度：庙/旺（好）、利（中）、陷（差）
    if bright in ("庙", "旺"):
        # 庙旺：正面为主，有煞忌时阴影
        is_shadow = bad
        is_positive = not bad
    elif bright == "陷":
        # 落陷：阴影为主，有吉且无煞忌时正面
        is_shadow = not (has_吉 and not bad)
        is_positive = has_吉 and not bad
    elif bright == "利":
        # 利：中等偏正面，有煞忌无吉则阴影
        is_shadow = bad and not has_吉
        is_positive = not is_shadow
    else:
        is_positive = False
        is_shadow = False
    
    if is_shadow and not is_positive:
        result["verdict"] = result.get("shadow", "")
        result["verdict_type"] = "shadow"
        result["vernacular"] = result.get("shadow", result.get("vernacular", ""))
    elif is_positive and not is_shadow:
        result["verdict"] = result.get("positive", "")
        result["verdict_type"] = "positive"
        result["vernacular"] = result.get("positive", result.get("vernacular", ""))
    else:
        result["verdict"] = result.get("vernacular", "")
        result["verdict_type"] = "mixed"
    
    return result
