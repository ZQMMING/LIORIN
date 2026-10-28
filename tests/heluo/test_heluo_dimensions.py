# -*- coding: utf-8 -*-
"""判词层**维度视图**守卫（2026-10-24 新增）。

背景
----
判词层的 ``evidence`` 此前是**平铺**的字符串列表 —— 下游若想知道某条判词属于
哪个人生领域（统一维度表：12 个 L1 领域 / 41 个 L2 子维度），只能**解析中文**。
这正是「维度视图」长期落不了地的根因。

本守卫钉死四件事：
  1. **维度表自身自洽**（id 唯一、domain 存在、12 域齐备、41 子维度）；
  2. **判据证据不得漏标**（``unclassified`` 必须为 0 —— 漏标要显式报出，
     不能让下游误以为「全部已归类」）；
  3. **by_dimension 与平铺 evidence 一一对应**（不重不漏、index 回指正确）；
  4. **口径/过程证据必须归 PROCESS**（不得冒充「人生领域判据」）。

⚠ 口径声明：子模块（``judge_ye_buye`` / ``judge_shu_xiong`` / ``judge_nayin_yuanqi``
等）各自的 ``evidence`` 列表**不带维度** —— 它们在**汇入主层**时统一定维度
（主层条目带前缀，如「数之凶吉：…」）。故维度视图以**主层**为准。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from heluo_engine.adapter import HeluoAdapter  # noqa: E402
from heluo_engine.engines.heluo.dimensions import (  # noqa: E402
    DIM_PROCESS, DIM_UNCLASSIFIED, DIMENSIONS, DOMAINS, KUOZHAN_DIM,
    coverage, is_known,
)

#: 统一维度表文档（维度的**唯一真源**）
DOC = _REPO / "docs" / "heluo" / "统一维度表_河洛细粒度落位_20261024.md"

#: 若干盘（覆盖不同证据分支）
CASES = [
    ((1975, 11, 22, 1), "male", "2026-10-23"),
    ((1980, 6, 22, 10), "male", "2026-09-15"),
    ((1983, 11, 3, 12), "female", "2026-01-03"),
]


def _results():
    ad = HeluoAdapter()
    for solar, gender, tgt in CASES:
        r = ad.compute(solar, gender=gender, target_date=tgt)
        yield tgt, r.guajie


class TestDimensionTable:
    """维度表自身。"""

    def test_domains_are_twelve_and_ids_unique(self):
        assert len(DOMAINS) == 12, f"L1 领域应为 12 个，实测 {len(DOMAINS)}"
        assert len(set(DOMAINS)) == len(DOMAINS), "L1 领域 id 重复"
        # 42 = 文档初版 41 + 2026-10-24 增补「正对反对（先后天卦）」
        # （诊断规则图需要 HL_POSTNATAL_HEXAGRAM 有维度可映射，否则该机制收不到证据）
        # 43 = 2026-10-25 增补「卦体（正体/互体/伏体）」
        # （同上：HL_HEXAGRAM_STRUCTURE 此前**证据被产出却未注册**，
        #   在诊断图里被静默丢弃；补维度后才有归属可映）
        assert len(DIMENSIONS) == 43, f"L2 子维度应为 43 个，实测 {len(DIMENSIONS)}"

    def test_every_dimension_has_known_domain(self):
        bad = [d for d, v in DIMENSIONS.items() if v[0] not in DOMAINS]
        assert not bad, f"维度领域 id 不在 DOMAINS：{bad}"

    def test_every_domain_has_at_least_one_dimension(self):
        hit = {v[0] for v in DIMENSIONS.values()}
        missing = sorted(set(DOMAINS) - hit)
        assert not missing, f"这些 L1 领域没有任何 L2 子维度：{missing}"

    def test_kuozhan_dim_map_covers_all_judge_keys(self):
        """扩展断法的 13 个判法 key 都要有维度（不得靠默认值兜底）。"""
        src = (_REPO / "src" / "heluo_engine" / "engines" / "heluo" / "guajie.py")
        txt = src.read_text(encoding="utf-8")
        keys = set(re.findall(r'\("([a-z_]+)",\s*lambda:', txt))
        missing = sorted(keys - set(KUOZHAN_DIM))
        assert not missing, f"扩展断法 key 未定维度：{missing}"

    def test_doc_and_code_agree_on_domain_count(self):
        """文档里的 L1 领域行数必须与代码一致（防止只改一边）。"""
        doc = DOC.read_text(encoding="utf-8")
        n = len(re.findall(r"^### L1-\d{2} ", doc, re.M))
        assert n == 12, f"文档 L1 领域行数应为 12，实测 {n}"
        for name in DOMAINS.values():
            assert name in doc, f"文档缺 L1 领域「{name}」"

    def test_all_dim_ids_used_in_code_are_known(self):
        """★ **静态**校验：源码里写下的每个维度 id 都必须在维度表内。

        **为什么要有这条**（2026-10-24 变异演练实测）
        变异 M1/M3 把某条证据的 dim 改掉（去掉 / 写成不存在的 id）——
        若那条证据**恰好不在测试盘上**，运行时守卫全绿 ⇒ **盲区**。
        ⇒ 补一条**静态**校验：直接扫源码里的 ``dim="..."`` 字面量，
        不依赖任何盘是否命中。写错 id / 漏登记的维度当场变红。
        """
        src = (_REPO / "src" / "heluo_engine" / "engines" / "heluo" / "guajie.py")
        ids = set(re.findall(r'dim="([^"]+)"', src.read_text(encoding="utf-8")))
        unknown = sorted(i for i in ids if not is_known(i))
        assert not unknown, f"源码用了未登记的维度 id：{unknown}"
        assert ids, "源码里一个 dim= 都没扫到 —— 扫描方式失效了"

    def test_source_dim_ids_cover_multiple_domains(self):
        """源码实际使用的维度应横跨**多个 L1 领域**（否则维度视图形同虚设）。"""
        src = (_REPO / "src" / "heluo_engine" / "engines" / "heluo" / "guajie.py")
        ids = set(re.findall(r'dim="([^"]+)"', src.read_text(encoding="utf-8")))
        # ⚠ 维度 id（如 TIMELINE.03）≠ 领域 id（如 TIMELINE）——
        #   必须先经 DIMENSIONS 取其 domain，再查 DOMAINS 取领域名。
        doms = {DOMAINS[DIMENSIONS[d][0]] for d in ids if d in DIMENSIONS}
        assert len(doms) >= 5, f"源码维度只覆盖 {len(doms)} 个 L1 领域：{sorted(doms)}"


class TestEvidenceDimensionCoverage:
    """判据证据的维度标注。"""

    def test_no_unclassified_evidence(self):
        """★ 判据证据**不得漏标**（漏标要显式报出，不得静默）。"""
        bad = []
        for tgt, gj in _results():
            assert isinstance(gj, dict) and "error" not in gj, f"{tgt} 判词层失败：{gj}"
            cov = gj["dimension_coverage"]
            if cov["unclassified"]:
                bad.append((tgt, cov["unclassified"]))
        assert not bad, f"以下盘的判据证据漏标维度：{bad}"

    def test_coverage_totals_match_evidence_length(self):
        for tgt, gj in _results():
            cov = gj["dimension_coverage"]
            assert cov["total"] == len(gj["evidence"]), (
                f"{tgt} coverage.total={cov['total']} "
                f"≠ len(evidence)={len(gj['evidence'])}")

    def test_all_dimension_ids_are_known(self):
        for tgt, gj in _results():
            for dim in gj["by_dimension"]:
                assert is_known(dim), f"{tgt} 出现未登记的维度 id：{dim!r}"

    def test_process_evidence_is_not_a_life_domain(self):
        """口径/过程类证据必须归 PROCESS —— 不得冒充人生领域判据。"""
        markers = ("历法口径", "流日口径", "计算跳过", "已剥离",
                   "占位推流年", "未取得出生月")
        for tgt, gj in _results():
            for dim, node in gj["by_dimension"].items():
                for it in node["items"]:
                    text = it["text"]
                    if any(m in text for m in markers):
                        assert dim == DIM_PROCESS, (
                            f"{tgt} 口径类证据被归到 {dim}：{text[:60]}")


class TestByDimensionConsistency:
    """by_dimension 与平铺 evidence 的一致性。"""

    def test_counts_and_indices_are_complete(self):
        for tgt, gj in _results():
            ev = gj["evidence"]
            bd = gj["by_dimension"]
            total = sum(n["count"] for n in bd.values())
            assert total == len(ev), (
                f"{tgt} by_dimension 合计 {total} ≠ evidence {len(ev)}")
            idx = sorted(it["index"] for n in bd.values() for it in n["items"])
            assert idx == list(range(len(ev))), (
                f"{tgt} by_dimension 的 index 不连续/有重复")

    def test_item_text_matches_source_evidence(self):
        for tgt, gj in _results():
            ev = gj["evidence"]
            for dim, node in gj["by_dimension"].items():
                for it in node["items"]:
                    assert it["text"] == ev[it["index"]], (
                        f"{tgt} {dim} 的条目文本与 evidence[{it['index']}] 不一致")

    def test_domain_nodes_carry_l3_l4_source(self):
        """领域维度的节点必须带 L3 载体与 L4 出处（否则无法回查原典）。"""
        for tgt, gj in _results():
            for dim, node in gj["by_dimension"].items():
                if dim in (DIM_PROCESS, DIM_UNCLASSIFIED):
                    continue
                assert node["carrier"], f"{tgt} {dim} 缺 L3 载体"
                assert node["source"], f"{tgt} {dim} 缺 L4 判据出处"
                assert node["domain"] in DOMAINS, (
                    f"{tgt} {dim} 的领域 id 不合法：{node['domain']}")

    def test_at_least_one_life_domain_hit(self):
        """一盘正常判词至少要落到 1 个人生领域（否则维度视图等于空转）。"""
        for tgt, gj in _results():
            cov = gj["dimension_coverage"]
            assert cov["domains_hit"], f"{tgt} 一个人生领域都未命中"


def test_coverage_helper_reports_unclassified():
    """coverage() 必须把未标注条数**显式报出**（不得静默）。"""
    c = coverage(["a", "b"], ["X", DIM_UNCLASSIFIED])
    assert c["total"] == 2 and c["tagged"] == 1 and c["unclassified"] == 1
    assert c["per_dimension"]["X"] == 1
