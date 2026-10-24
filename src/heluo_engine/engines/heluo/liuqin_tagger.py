# -*- coding: utf-8 -*-
"""爻辞断语中的**六亲 / 婚育 / 寿夭**意象标注（2026-10-24 新增）。

为什么需要
----------
统一维度表里有 41 个 L2 子维度，但**判词层只产出了 13 个** ——
「婚姻与配偶」「子女与晚辈」「父母与长辈」「手足与同辈」「夭折横夭」
这几格的判据**原典就在判词库里**（如「免克绝子孙」「亲眷刑伤，婚嗣孤克」
「或生子孙」「兄弟之忧」），却因「只按卦名归位、不断语归位」而从未进入证据链。

本模块做的是**有据的最小接入**：
  · 只在**判词库原句**上匹配（不生成任何新断语、不改一个字）；
  · 命中的**原句连同其条件前缀**（「岁运逢之…」「数卦不叶…」）一并带出 ——
    这些断语是**条件式**的，脱离条件引用即失真；
  · 只给出「维度 + 命中原句」，**不给方向、不给分数**
    （方向与吉凶的判定由 :mod:`dimensions.helio_direction` 依名目给出）。

⚠ 关键词表以**判词库实际用字**为准（不臆造同义词），改动须同时更新
``tests/heluo/test_heluo_liuqin_tagger.py`` 的对照。
"""
from __future__ import annotations

#: 关键词 → (维度 id, 类别名)
#: ⚠ 关键词取自判词库**实际用字**（实测抽样见报告）；
#:   「孝服」「丁艰」为丧亲语，「亲眷」「婚嗣」为六亲语。
KEYWORDS: dict[str, tuple[str, str]] = {
    # ── 父母与长辈 ──
    "父母": ("PARENTS.01", "六亲·父母爻"),
    "孝服": ("PARENTS.01", "六亲·父母爻"),
    "丁艰": ("PARENTS.01", "六亲·父母爻"),
    # ── 子女与晚辈 ──
    "子孙": ("CHILDREN.01", "子息"),
    "子息": ("CHILDREN.01", "子息"),
    "得子": ("CHILDREN.01", "子息"),
    "生男": ("CHILDREN.01", "子息"),
    "生女": ("CHILDREN.01", "子息"),
    "进人口": ("CHILDREN.01", "子息"),
    # ── 手足与同辈 ──
    "兄弟": ("SIBLINGS.01", "六亲·兄弟爻"),
    "手足": ("SIBLINGS.01", "六亲·兄弟爻"),
    # ── 婚姻与配偶 ──
    "婚": ("MARRIAGE.02", "配偶征象"),
    "嫁": ("MARRIAGE.02", "配偶征象"),
    "妾": ("MARRIAGE.02", "配偶征象"),
    "妻": ("MARRIAGE.02", "配偶征象"),
    "亲眷": ("MARRIAGE.02", "配偶征象"),
    "婚嗣": ("MARRIAGE.02", "配偶征象"),
    "成亲姻": ("MARRIAGE.02", "配偶征象"),
    "琴瑟": ("MARRIAGE.03", "琴瑟不和"),
    "乖戾": ("MARRIAGE.03", "琴瑟不和"),
    # ── 寿元与灾厄 ──
    "夭": ("HEALTH.03", "夭折横夭"),
    "短寿": ("HEALTH.03", "夭折横夭"),
    "凶终": ("HEALTH.03", "夭折横夭"),
}


def scan_duan(text: str) -> list[tuple[str, str, str]]:
    """在一条断语里扫六亲/婚育/寿夭意象。

    Returns:
        ``[(维度 id, 类别名, 命中的词)]``；同一维度只报一次（避免重复刷屏）。
    """
    if not text:
        return []
    hits: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for kw, (dim, cat) in KEYWORDS.items():
        if kw in text and dim not in seen:
            seen.add(dim)
            hits.append((dim, cat, kw))
    return hits


def scan_yao_duans(yao_duans: list[str]) -> list[dict]:
    """扫描一个爻的全部断语，产出可入证据链的条目。

    Returns:
        ``[{"dimension", "category", "keyword", "quote"}]``
        —— ``quote`` 是**带条件前缀的原句**（条件式断语不得脱离条件引用）。
    """
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for d in (yao_duans or []):
        for dim, cat, kw in scan_duan(d):
            key = (dim, d[:24])
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "dimension": dim, "category": cat, "keyword": kw,
                "quote": d,
            })
    return out


def collect_from_yao(yao: object) -> list[dict]:
    """从一个 ``YaoDuan``（或同形 dict）收集上述条目。

    覆盖两类载体：
      · **爻级**断语：``ye`` / ``buye`` / ``suiyun`` / ``shao`` / ``duans``；
      · **卦级**断语：``gua_lines``（命卦的卦头断语列表）——
        命卦层是**本命**而非流年，但落在的**人生领域**不变。
    """
    if yao is None:
        return []
    get = (lambda k: getattr(yao, k, None)) if not isinstance(yao, dict) \
        else (lambda k: yao.get(k))
    duans: list[str] = []
    for fld in ("ye", "buye", "suiyun", "shao"):
        v = get(fld)
        if isinstance(v, str) and v:
            duans.append(v)
    d = get("duans")
    if isinstance(d, list):
        duans.extend([x for x in d if isinstance(x, str)])
    gl = get("gua_lines")
    if isinstance(gl, list):
        duans.extend([x for x in gl if isinstance(x, str)])
    return scan_yao_duans(duans)
