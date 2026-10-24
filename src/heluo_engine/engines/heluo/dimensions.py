# -*- coding: utf-8 -*-
"""统一维度表（河洛细粒度落位）的**可执行**版本（2026-10-24）。

依据文档：`docs/heluo/统一维度表_河洛细粒度落位_20261024.md`
（L1 人生领域 12 行 / L2 子维度 41 个 / L3 河洛载体 / L4 判据出处 / L5 事件类型落位）。

**本模块只落地河洛侧负责的 L3/L4**（机制/取法 + 判据出处）；
L1/L2 的最终裁定属平台，L5 事件类型落位见
《河洛机制到平台事件类型落位提案_20261024.md》——
河洛**不得**臆造跨引擎语义，也**不得**自定方向（ontology 把 direction 写死了，
而原典方向随卦/爻/叶不叶/岁运变 ⇒ 方向必须由判词层给）。

**两个非领域维度**（刻意与 12 域分开，避免「过程留痕」冒充「人生领域判据」）：
  · ``PROCESS``       —— 口径自检 / 计算跳过 / 边界说明等**过程与口径**留痕
  · ``UNCLASSIFIED``  —— **尚未标注**的判据证据（守卫须显式报告其数量，不得静默）
"""
from __future__ import annotations

#: 非领域维度
DIM_PROCESS = "PROCESS"
DIM_UNCLASSIFIED = "UNCLASSIFIED"

#: L1 人生领域（12 个）—— 平台维护，河洛只引用
DOMAINS: dict[str, str] = {
    "SELF": "自我与心性",
    "HEALTH": "身体与疾厄",
    "WEALTH": "财富与资源",
    "CAREER": "事业与功名",
    "MARRIAGE": "婚姻与配偶",
    "CHILDREN": "子女与晚辈",
    "PARENTS": "父母与长辈",
    "SIBLINGS": "手足与同辈",
    "SOCIAL": "人际与外部",
    "LIFESPAN": "寿元与灾厄",
    "PATTERN": "整体格局",
    "TIMELINE": "时间轴与岁运触发",
}

#: L2 子维度 → (领域 id, 子维度名, L3 河洛载体, L4 判据出处)
DIMENSIONS: dict[str, tuple[str, str, str, str]] = {
    # L1-01 自我与心性
    "SELF.01": ("SELF", "先天气质", "先天卦", "《起例卷之上》先天卦取法"),
    "SELF.02": ("SELF", "元堂定命", "元堂爻", "《起例卷之上》元堂取法"),
    "SELF.03": ("SELF", "元气体", "天元气/地元气/元气相反", "yuan_qi.py；原典「元气相反图」"),
    "SELF.04": ("SELF", "卦体性质", "卦体（纳甲/卦气月/宫位）", "判词库卦体段"),
    # L1-02 身体与疾厄
    "HEALTH.01": ("HEALTH", "体质根基", "纳音五行", "原典「纳音」"),
    "HEALTH.02": ("HEALTH", "形神", "卦爻病象 + 爻辞/小象", "yao_xiang.py；判词库爻辞/小象"),
    "HEALTH.03": ("HEALTH", "夭折横夭", "爻辞断语（夭/横/克父母子孙）", "判词库断语"),
    # L1-03 财富与资源
    "WEALTH.01": ("WEALTH", "财源厚薄", "地元气 + 财禄", "yuan_qi.py；原典「财禄」"),
    "WEALTH.02": ("WEALTH", "财意象", "断语意象（金玉龍麟、桂蘭星斗）",
                  "《崇祯五年刻本·卷六·识典整理》"),
    "WEALTH.03": ("WEALTH", "份额层次", "十体分级", "《起例卷之上》原书 L1145"),
    "WEALTH.04": ("WEALTH", "田产", "断语（田产/产业）", "判词库断语"),
    # L1-04 事业与功名
    "CAREER.01": ("CAREER", "功名科名", "化工（先天）+ 天元气", "原典「化工」「功名」"),
    "CAREER.02": ("CAREER", "官禄", "断语（官禄/爵命/高官）", "判词库断语"),
    "CAREER.03": ("CAREER", "位阶", "十体分级 + 六位贵贱", "《起例卷之上》贵命十体"),
    # L1-05 婚姻与配偶
    "MARRIAGE.01": ("MARRIAGE", "配偶宫位", "天地数 + 元堂阴阳配", "《起例卷》天地数取法"),
    "MARRIAGE.02": ("MARRIAGE", "配偶征象", "断语（婚嫁/结亲/娶妻/妻财）", "判词库断语"),
    "MARRIAGE.03": ("MARRIAGE", "琴瑟不和", "断语（琴瑟不调/婚姻乖戾）", "判词库断语"),
    "MARRIAGE.04": ("MARRIAGE", "合婚", "（原典有载，引擎未实现）",
                    "《河洛理数·卷一》目次「詳河洛合婚例」"),
    # L1-06 子女与晚辈
    "CHILDREN.01": ("CHILDREN", "子息", "断语（予息/子息/生男）", "判词库断语"),
    "CHILDREN.02": ("CHILDREN", "化工后天", "化工（后天）", "原典「化工」"),
    "CHILDREN.03": ("CHILDREN", "六亲·子孙爻", "爻位六亲（子孙爻）", "《起例卷之上》"),
    # L1-07 父母与长辈
    "PARENTS.01": ("PARENTS", "六亲·父母爻", "爻位六亲（父母爻）", "《起例卷之上》父母爻断语"),
    "PARENTS.02": ("PARENTS", "克父母", "元气相反 + 断语「克父母」",
                   "原典「元气反悖…克父母子孙」"),
    "PARENTS.03": ("PARENTS", "祖上", "（原典不用此语）", "—"),
    # L1-08 手足与同辈
    "SIBLINGS.01": ("SIBLINGS", "六亲·兄弟爻", "爻位六亲（兄弟爻）", "《起例卷之上》兄弟爻断语"),
    "SIBLINGS.02": ("SIBLINGS", "同辈争财", "断语（比劫分财类）", "判词库断语"),
    # L1-09 人际与外部
    "SOCIAL.01": ("SOCIAL", "宾位（外缘）", "年月时柱 + 纳甲宾位", "《起例卷之上》宾位"),
    "SOCIAL.02": ("SOCIAL", "驿马", "年支/日支驿马", "判词层"),
    "SOCIAL.03": ("SOCIAL", "刑害", "（原典有载，引擎未实现）", "《河洛理数·卷一》「三刑六列」"),
    # L1-10 寿元与灾厄
    "LIFESPAN.01": ("LIFESPAN", "大运空无字", "大运段「空无字」判据",
                    "参评诗断「空无字…重者损寿，轻者破耗刑克」"),
    "LIFESPAN.02": ("LIFESPAN", "旺衰", "纳音身旺衰 / 卦爻得时", "原典「生于二月至八月得时」"),
    "LIFESPAN.03": ("LIFESPAN", "夭横", "断语（夭/横/凶终/短寿）", "判词库断语"),
    "LIFESPAN.04": ("LIFESPAN", "空亡", "旬空/空亡", "判词层"),
    # L1-11 整体格局
    "PATTERN.01": ("PATTERN", "定局机制", "元堂取法 + 纳甲 + 天元/地元/元气",
                   "《起例卷之上》全卷"),
    "PATTERN.04": ("PATTERN", "正对反对（先后天卦）", "先天卦/后天卦正对反对判定",
                   "《起例卷之上》换后天卦例"),
    "PATTERN.02": ("PATTERN", "格局结论", "断语（富贵/贫贱/贤愚/寿夭）", "判词库断语"),
    "PATTERN.03": ("PATTERN", "位阶层次", "十体分级（贵命十体/下十体）", "原书 L1145"),
    # L1-12 时间轴与岁运触发
    "TIMELINE.01": ("TIMELINE", "大运", "大运段（元堂爻/爻位值运）", "《起例卷之上》先天换后天"),
    "TIMELINE.02": ("TIMELINE", "流年", "流年卦 + 流年断爻取小象行年爻",
                    "《起例卷之上》小象行年卦气"),
    "TIMELINE.03": ("TIMELINE", "流月", "流月卦（就年卦中前一位起）", "《起例卷之上》起月卦例"),
    "TIMELINE.04": ("TIMELINE", "流日", "流日卦（流月卦前一爻为初一日）", "《起例卷之上》起日卦例"),
    "TIMELINE.05": ("TIMELINE", "节候", "节候卦（四正节卦每卦 90 日）", "《起例卷之下》节候卦说"),
}

#: 非领域维度的展示名
_PSEUDO_LABELS = {
    DIM_PROCESS: "过程与口径留痕",
    DIM_UNCLASSIFIED: "未标注（须显式报告，不得静默）",
}


#: 扩展断法 key → 维度 id（2026-10-24）
#:
#: 依据：各 judge 函数的原典出处 + 维度表 L3「河洛载体」。
#: 例：``xiang_sheng_wei_fu`` 是「得体/得局/生气」的**五行配合**判法（起例卷之上
#: L161/L235），属「定局机制」而非六亲 —— 不可因名字像「为父」就归到父母爻。
KUOZHAN_DIM: dict[str, str] = {
    "siti_bati": "PATTERN.01",          # 四体八体（互体/伏体/八体）
    "fu_li": "PATTERN.03",              # 福力（富贵力 ⇒ 位阶层次）
    "wuming_de_gua": "PATTERN.01",      # 五命得卦（取卦机制）
    "suoshu_ji_xiong": "PATTERN.02",    # 缩筮集凶（凶格汇总 ⇒ 格局结论）
    "yue_ling_fei_shi": "LIFESPAN.02",  # 月令非时（旺衰）
    "shu_ji": "PATTERN.02",             # 数极（数之极断）
    "liu_wei_gui_jian": "CAREER.03",    # 六位贵贱（位阶）
    "gui_ming_shi_ti": "PATTERN.02",    # 鬼名拾题（取爻定名之凶名）
    "jian_ming_shi_ti": "PATTERN.02",   # 剑名拾题（取爻定名之吉名）
    "yao_ci_bi_li": "PATTERN.02",       # 爻辞比类（吉凶爻辞比例断命）
    "xiang_sheng_wei_fu": "PATTERN.01", # 相生为福·得体·得局生气（五行配合）
    "yun_liunian_shu_fan": "TIMELINE.01",   # 运反/流年反/数反（大运与流年）
    "xian_tian_hou_tian_yuan_qi": "SELF.03",  # 先后天元气（天元/地元）
}


#: 维度 id → **诊断规则图的机制 rule_id**（2026-10-24）
#:
#: ⚠ 维度（L2 子维度）与 rule_id（**机制**）**不是一回事**：
#:   rule_id 回答「这条结论由哪条机制算出」，维度回答「它落在哪个人生领域」。
#:   ⇒ 诊断图的**节点是机制**，维度放在 ``EngineEvidence.attributes`` 里。
#:
#: 映射依据：各判据的实际计算来源（见统一维度表 L3 河洛载体列）。
#: 留空 = 该维度暂无对应机制规则 ⇒ 其证据**不进诊断图**
#:（由 diagnosis_rule_graph 的 dropped_rules 留痕，不硬塞）。
DIM_TO_RULE: dict[str, str] = {
    "SELF.01": "HL_PRENATAL_HEXAGRAM",
    "SELF.02": "HL_YUANTANG",
    "SELF.03": "HL_HUA_GONG",
    "SELF.04": "HL_PRENATAL_HEXAGRAM",
    "HEALTH.01": "HL_TIAN_DI_SHU",
    "HEALTH.02": "HL_PRENATAL_HEXAGRAM",
    "HEALTH.03": "HL_TIAN_DI_SHU",
    "WEALTH.01": "HL_HUA_GONG",
    "WEALTH.02": "HL_PRENATAL_HEXAGRAM",
    "WEALTH.03": "HL_TIAN_DI_SHU",
    "WEALTH.04": "HL_PRENATAL_HEXAGRAM",
    "CAREER.01": "HL_HUA_GONG",
    "CAREER.02": "HL_PRENATAL_HEXAGRAM",
    "CAREER.03": "HL_YUANTANG",
    "MARRIAGE.01": "HL_TIAN_DI_SHU",
    "MARRIAGE.02": "HL_PRENATAL_HEXAGRAM",
    "MARRIAGE.03": "HL_PRENATAL_HEXAGRAM",
    "CHILDREN.01": "HL_PRENATAL_HEXAGRAM",
    "CHILDREN.02": "HL_HUA_GONG",
    "CHILDREN.03": "HL_YUANTANG",
    "PARENTS.01": "HL_YUANTANG",
    "PARENTS.02": "HL_HUA_GONG",
    "SIBLINGS.01": "HL_YUANTANG",
    "SIBLINGS.02": "HL_PRENATAL_HEXAGRAM",
    "SOCIAL.01": "HL_TIAN_DI_SHU",
    "SOCIAL.02": "HL_TIAN_DI_SHU",
    "SOCIAL.03": "",          # 三刑六列：原典有载、引擎未实现 ⇒ 无机制规则
    "LIFESPAN.01": "HL_DAYUN",
    "LIFESPAN.02": "HL_JIEHOU_GUA",
    "LIFESPAN.03": "HL_DAYUN",
    "LIFESPAN.04": "HL_DAYUN",
    "PATTERN.01": "HL_TIAN_DI_SHU",
    "PATTERN.04": "HL_POSTNATAL_HEXAGRAM",
    "PATTERN.02": "HL_TIAN_DI_SHU",
    "PATTERN.03": "HL_TIAN_DI_SHU",
    "TIMELINE.01": "HL_DAYUN",
    "TIMELINE.02": "HL_LIUNIAN_GUA",
    "TIMELINE.03": "HL_YUEGUA",
    "TIMELINE.04": "HL_RIGUA",
    "TIMELINE.05": "HL_JIEHOU_GUA",
}


#: 平台 17 类事件本体（**镜像**，2026-10-24）
#:
#: ⚠ 这是平台本体 ``src/tongshu/spec/event_ontology_v1.py`` 的**只读镜像** ——
#: 河洛包**不得** import 主仓（独立包原则），故在此镜像一份。
#: **本表只用于「候选证据」的分组**，不构成裁定：
#:   · 平台的 ``direction`` 是**默认方向**；原典方向随卦/爻/叶不叶/岁运变
#:     ⇒ **方向由河洛判词层另给**（见 :func:`build_event_candidates` 的
#:     ``heluo_direction``），两者可能不同（不同即留痕，不强行对齐）。
#:   · 「河洛不得臆造跨引擎语义、不得自定方向」是硬纪律。
EVENT_TYPES: dict[str, dict[str, str]] = {
    # EDUCATION (4)
    "EXAM": {"domain": "EDUCATION", "default_direction": "NEUTRAL", "granularity": "MONTHLY"},
    "ADMISSION": {"domain": "EDUCATION", "default_direction": "POSITIVE", "granularity": "YEARLY"},
    "GRADUATION": {"domain": "EDUCATION", "default_direction": "POSITIVE", "granularity": "YEARLY"},
    "DEGREE": {"domain": "EDUCATION", "default_direction": "POSITIVE", "granularity": "YEARLY"},
    # CAREER (5)
    "PROMOTION": {"domain": "CAREER", "default_direction": "POSITIVE", "granularity": "YEARLY"},
    "JOB_CHANGE": {"domain": "CAREER", "default_direction": "CHANGE", "granularity": "YEARLY"},
    "RESIGNATION": {"domain": "CAREER", "default_direction": "CHANGE", "granularity": "YEARLY"},
    "DEMOTION": {"domain": "CAREER", "default_direction": "NEGATIVE", "granularity": "YEARLY"},
    "MAJOR_INCOME": {"domain": "CAREER", "default_direction": "POSITIVE", "granularity": "YEARLY"},
    # FAMILY (5)
    "MARRIAGE": {"domain": "FAMILY", "default_direction": "POSITIVE", "granularity": "YEARLY"},
    "DIVORCE": {"domain": "FAMILY", "default_direction": "NEGATIVE", "granularity": "YEARLY"},
    "CHILD_BIRTH": {"domain": "FAMILY", "default_direction": "POSITIVE", "granularity": "YEARLY"},
    "PARENT_DEATH": {"domain": "FAMILY", "default_direction": "NEGATIVE", "granularity": "YEARLY"},
    "FAMILY_HARMONY": {"domain": "FAMILY", "default_direction": "POSITIVE", "granularity": "YEARLY"},
    # LIFE_EVENT (3)
    "RELOCATION": {"domain": "LIFE_EVENT", "default_direction": "CHANGE", "granularity": "YEARLY"},
    "HEALTH_ISSUE": {"domain": "LIFE_EVENT", "default_direction": "NEGATIVE", "granularity": "YEARLY"},
    "LEGAL_ISSUE": {"domain": "LIFE_EVENT", "default_direction": "NEGATIVE", "granularity": "YEARLY"},
}

#: 维度 → 平台 17 类**候选**（依据《统一维度表》L5 列；空 = 无候选）
#: ``ALL`` = 时间轴维度（**触发器**，不作独立事件候选，只作时间上下文）
DIM_TO_EVENT: dict[str, tuple[str, ...]] = {
    "SELF.01": ("DEGREE",),
    "SELF.03": ("HEALTH_ISSUE",),
    "HEALTH.01": ("HEALTH_ISSUE",),
    "HEALTH.02": ("HEALTH_ISSUE",),
    "HEALTH.03": ("HEALTH_ISSUE",),
    "WEALTH.01": ("MAJOR_INCOME",),
    "WEALTH.02": ("MAJOR_INCOME",),
    "WEALTH.03": ("MAJOR_INCOME",),
    "WEALTH.04": ("MAJOR_INCOME",),
    "CAREER.01": ("ADMISSION", "DEGREE"),
    "CAREER.02": ("PROMOTION",),
    "CAREER.03": ("PROMOTION",),
    "MARRIAGE.01": ("MARRIAGE",),
    "MARRIAGE.02": ("MARRIAGE",),
    "MARRIAGE.03": ("DIVORCE",),
    "CHILDREN.01": ("CHILD_BIRTH",),
    "CHILDREN.03": ("CHILD_BIRTH",),
    "PARENTS.01": ("PARENT_DEATH",),
    "PARENTS.02": ("PARENT_DEATH",),
    "SOCIAL.02": ("RELOCATION",),
    "LIFESPAN.01": ("HEALTH_ISSUE",),
    "LIFESPAN.02": ("HEALTH_ISSUE",),
    "LIFESPAN.03": ("HEALTH_ISSUE",),
    "LIFESPAN.04": ("HEALTH_ISSUE",),
    "PATTERN.03": ("PROMOTION", "MAJOR_INCOME"),
    "TIMELINE.01": ("ALL",),
    "TIMELINE.02": ("ALL",),
    "TIMELINE.03": ("ALL",),
    "TIMELINE.04": ("ALL",),
    "TIMELINE.05": ("ALL",),
}

#: 河洛侧**有据**的方向判定（来源可回查，不给自拟分数）
#:   · 遇元气/遇化工 → 吉（原典「遇元气必然得财利」「遇化工中举中进士生贵子」）
#:   · 数凶 → 凶（原典「数凶则当以不吉祥断」；「若数凶，寿何可久」）
#:   · 叶 / 不叶 → 吉 / 凶（叶 = 卦气相合，不叶 = 不合）
#:   · 死断命中 → **条件式**（阴骘两支并陈，不得径取一支）⇒ 不给确定方向
def heluo_direction(guajie: dict) -> tuple[str, str]:
    """从判词层给**有据**方向。

    Returns:
        ``(direction, basis)``；direction ∈ POSITIVE / NEGATIVE / NEUTRAL /
        UNKNOWN；``basis`` 写明依据（可回查原典）。
        ⚠ 判不出就返回 ``UNKNOWN`` —— **不给「看起来有结果」的猜测**。
    """
    if not isinstance(guajie, dict) or not guajie:
        return "UNKNOWN", "无判词层结果"
    hits = []
    if guajie.get("hua_gong_hit"):
        hits.append(("POSITIVE", "流年遇化工（原典：遇化工中举中进士生贵子）"))
    if guajie.get("yuan_qi_hit"):
        hits.append(("POSITIVE", "流年遇元气（原典：遇元气必然得财利）"))
    sx = guajie.get("shu_xiong") or {}
    if isinstance(sx, dict) and sx.get("shu_xiong"):
        hits.append(("NEGATIVE", "数凶（原典：数凶则当以不吉祥断）"))
    yb = guajie.get("liunian_ye_buye") or {}
    if isinstance(yb, dict):
        if yb.get("ye"):
            hits.append(("POSITIVE", "流年卦叶（叶 = 卦气相合）"))
        elif yb.get("buye"):
            hits.append(("NEGATIVE", "流年卦不叶（不叶 = 卦气不合）"))
    if guajie.get("si_duan"):
        hits.append(("UNKNOWN",
                     "命中死断条 —— 原典为**条件式立断**（阴骘两支并陈），"
                     "不得径取一支作方向"))
    if not hits:
        return "UNKNOWN", "判词层未给出可判方向的名目"
    pos = [h for h in hits if h[0] == "POSITIVE"]
    neg = [h for h in hits if h[0] == "NEGATIVE"]
    unk = [h for h in hits if h[0] == "UNKNOWN"]
    if unk and not (pos or neg):
        return "UNKNOWN", unk[0][1]
    if pos and not neg:
        return "POSITIVE", pos[0][1]
    if neg and not pos:
        return "NEGATIVE", neg[0][1]
    return "UNKNOWN", "多判据方向相冲（" + "；".join(h[1] for h in hits) + "）"


def build_event_candidates(by_dimension: dict, guajie: dict) -> dict:
    """按平台 17 类归组河洛的**候选证据**（不裁定、不给分数）。

    Args:
        by_dimension: 判词层的 ``by_dimension`` 视图（维度 → items）。
        guajie: 判词层结果（用于给**有据**方向）。

    Returns:
        ``{"candidates": {event_type: {...}}, "coverage": {...},
        "heluo_direction": (direction, basis)}``
    """
    direction, basis = heluo_direction(guajie)
    cands: dict[str, dict] = {}
    for dim, node in (by_dimension or {}).items():
        if dim in (DIM_PROCESS, DIM_UNCLASSIFIED):
            continue
        for et in DIM_TO_EVENT.get(dim, ()):
            if et == "ALL":
                continue          # 时间轴维度只作上下文，不作独立事件候选
            if et not in EVENT_TYPES:
                continue
            c = cands.setdefault(et, {
                "event_type": et,
                "domain": EVENT_TYPES[et]["domain"],
                "platform_default_direction": EVENT_TYPES[et]["default_direction"],
                "heluo_direction": direction,
                "heluo_direction_basis": basis,
                "strength_note": "以「证据条数 + 判据出处」表达，**不给 0–1 分数**"
                                 "（原典只给吉凶不给数值）",
                "dimensions": [],
                "items": [],
            })
            c["dimensions"].append(dim)
            for it in node.get("items", []):
                c["items"].append({
                    "index": it.get("index"),
                    "dimension": dim,
                    "dimension_label": node.get("label", ""),
                    "text": it.get("text", ""),
                })
    hit = sorted(cands)
    return {
        "candidates": cands,
        "heluo_direction": {"direction": direction, "basis": basis},
        "coverage": {
            "event_types_total": len(EVENT_TYPES),
            "event_types_with_candidate": len(hit),
            "event_types_without_candidate": sorted(set(EVENT_TYPES) - set(hit)),
            "note": "「无候选」= 河洛判词层**未产出**该类证据（能力缺口），"
                    "不等于该类事件不可能发生。",
        },
    }


def is_known(dim: str) -> bool:
    """维度 id 是否在表内（含两个非领域维度）。"""
    return dim in DIMENSIONS or dim in _PSEUDO_LABELS


def label_of(dim: str) -> str:
    """维度 id → 展示名（未知 id 原样返回，便于暴露脏数据）。"""
    if dim in DIMENSIONS:
        return DIMENSIONS[dim][1]
    return _PSEUDO_LABELS.get(dim, dim)


def domain_of(dim: str) -> str:
    """维度 id → 所属 L1 领域 id（非领域维度返回空串）。"""
    if dim in DIMENSIONS:
        return DIMENSIONS[dim][0]
    return ""


def domain_label_of(dim: str) -> str:
    """维度 id → 所属 L1 领域名。"""
    d = domain_of(dim)
    return DOMAINS.get(d, "")


def describe(dim: str) -> dict:
    """维度 id → 可直接下发的说明字典（L3 载体 + L4 出处）。"""
    if dim in DIMENSIONS:
        dom, lab, carrier, source = DIMENSIONS[dim]
        return {
            "id": dim, "domain": dom, "domain_label": DOMAINS.get(dom, ""),
            "label": lab, "carrier": carrier, "source": source,
        }
    return {
        "id": dim, "domain": "", "domain_label": "",
        "label": _PSEUDO_LABELS.get(dim, dim), "carrier": "", "source": "",
    }


def build_by_dimension(evidence: list[str], dims: list[str]) -> dict:
    """按维度归组证据。

    Args:
        evidence: 判词层证据（list[str]，索引与 dims 一一对应）。
        dims:    与 evidence **等长**的维度 id 列表。

    Returns:
        ``{维度 id: {"id","domain","domain_label","label","carrier","source",
        "count", "items": [{"index": i, "text": str}]}}``
        —— ``items`` 只带 **index** 与 **text 摘要**，不复制全文，
        以免与 ``evidence`` 双份存储而失同步。
    """
    out: dict = {}
    for i, (text, dim) in enumerate(zip(evidence, dims)):
        node = out.get(dim)
        if node is None:
            node = dict(describe(dim))
            node["count"] = 0
            node["items"] = []
            out[dim] = node
        node["count"] += 1
        node["items"].append({"index": i, "text": text})
    return out


def coverage(evidence: list[str], dims: list[str]) -> dict:
    """维度覆盖率报告（守卫与披露用）。

    ⇒ 「未标注」条数**显式报出**，不静默 —— 判据证据若无法归位，
    下游须知道有几条没有维度标签（否则会误以为「全部已归类」）。
    """
    total = len(evidence)
    tagged = sum(1 for d in dims if d and d != DIM_UNCLASSIFIED)
    unclassified = sum(1 for d in dims if d == DIM_UNCLASSIFIED)
    per_dim: dict[str, int] = {}
    for d in dims:
        per_dim[d] = per_dim.get(d, 0) + 1
    return {
        "total": total,
        "tagged": tagged,
        "unclassified": unclassified,
        "process": per_dim.get(DIM_PROCESS, 0),
        "per_dimension": per_dim,
        "domains_hit": sorted({domain_of(d) for d in dims if domain_of(d)}),
    }
