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
