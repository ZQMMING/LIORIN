# -*- coding: utf-8 -*-
"""六亲/婚育/寿夭**维度接入**守卫（2026-10-24 新增）。

背景
----
统一维度表有 41 个 L2 子维度，但判词层此前只产出 13 个 ——
「婚姻与配偶」「子女与晚辈」「父母与长辈」「手足与同辈」几格
**原典就在判词库里**（「免克绝子孙」「亲眷刑伤，婚嗣孤克」「或生子孙」
「兄弟之忧」…），却因「只按卦名归位、不断语归位」而从未进证据链。

本守卫钉死：
  1. 关键词表只用**判词库实际用字**（不臆造同义词）；
  2. 命中的**原句连同条件前缀**一并留证（条件式断语不得脱离条件引用）；
  3. 标注**不得**改写断语文本；
  4. 接入后这些维度**确实出现在** by_dimension 里；
  5. 维度覆盖不得**倒退**（回退即须说明）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from heluo_engine.adapter import HeluoAdapter  # noqa: E402
from heluo_engine.engines.heluo.dimensions import DIMENSIONS  # noqa: E402
from heluo_engine.engines.heluo.liuqin_tagger import (  # noqa: E402
    KEYWORDS, collect_from_yao, scan_duan,
)

#: 判词库实际用字 → 期望命中的维度（抽样实测，2026-10-24）
EXPECTED_KEYWORDS = {
    "父母": "PARENTS.01",
    "孝服": "PARENTS.01",
    "子孙": "CHILDREN.01",
    "子息": "CHILDREN.01",
    "得子": "CHILDREN.01",
    "生男": "CHILDREN.01",
    "兄弟": "SIBLINGS.01",
    "手足": "SIBLINGS.01",
    "婚": "MARRIAGE.02",
    "嫁": "MARRIAGE.02",
    "妾": "MARRIAGE.02",
    "妻": "MARRIAGE.02",
    "亲眷": "MARRIAGE.02",
    "琴瑟": "MARRIAGE.03",
}


class TestKeywordTable:
    def test_keyword_dims_are_known(self):
        for kw, (dim, _cat) in KEYWORDS.items():
            assert dim in DIMENSIONS, f"关键词 {kw} 指向未登记维度 {dim}"

    def test_expected_keywords_map_to_expected_dims(self):
        for kw, dim in EXPECTED_KEYWORDS.items():
            assert kw in KEYWORDS, f"关键词表缺 {kw}"
            assert KEYWORDS[kw][0] == dim, f"{kw} 的维度应为 {dim}"

    def test_scan_is_deduped_per_dimension(self):
        hits = scan_duan("兄弟之忧，兄弟争财，兄弟")
        dims = [h[0] for h in hits]
        assert len(dims) == len(set(dims)), "同一维度被重复报出"


class TestAgainstRealLibrary:
    """对**判词库真实数据**验证。"""

    @pytest.fixture(scope="class")
    def lib(self):
        raw = json.loads((_REPO / "src" / "heluo_engine" / "data" /
                          "guajie_data.json").read_text(encoding="utf-8"))
        return raw

    def test_library_contains_matching_duans(self, lib):
        n = 0
        for g in lib:
            for y in (g.get("yaos") or []):
                for d in (y.get("duans") or []):
                    if scan_duan(d):
                        n += 1
        assert n >= 50, f"判词库命中的六亲/婚育断语过少：{n}"

    def test_collect_from_yao_reads_gua_lines(self, lib):
        """卦级断语（gua_lines）也要被扫到（命卦层）。"""
        found = 0
        for g in lib:
            hits = collect_from_yao({
                "gua_lines": g.get("lines") or [],
            })
            if hits:
                found += 1
        assert found >= 1, "卦级断语（gua_lines）未被扫描"

    def test_quote_is_verbatim(self, lib):
        """证据里的原句必须**逐字**来自断语（不得改写）。"""
        for g in lib:
            for y in (g.get("yaos") or []):
                duans = y.get("duans") or []
                for h in collect_from_yao({"duans": duans}):
                    assert h["quote"] in duans, "原句被改写"


class TestDimensionsNowAppear:
    """接入后这些维度**确实**出现在 by_dimension 里。"""

    @pytest.mark.parametrize("solar", [
        (1975, 11, 22, 1), (1990, 8, 8, 20), (1980, 6, 22, 10),
    ])
    def test_family_dimensions_present_in_some_case(self, solar):
        """六亲/婚育维度在**多盘合计**上必须出现。

        ⚠ 不是每一盘都该有 —— 断语取决于该盘的**命卦/流年卦**，
        某一盘没有「父母/子孙/婚」类断语是正常的。
        ⇒ 断言取「多盘合计」，不逐盘强求。
        """
        ad = HeluoAdapter()
        got: set[str] = set()
        for s in ((1975, 11, 22, 1), (1990, 8, 8, 20), (1980, 6, 22, 10),
                  (1965, 3, 15, 8), (1992, 2, 2, 2)):
            r = ad.compute(s, gender="male", target_date="2026-10-23")
            bd = (r.guajie or {}).get("by_dimension") or {}
            got |= {d for d in bd
                    if d.startswith(("MARRIAGE.", "CHILDREN.", "PARENTS.",
                                     "SIBLINGS."))}
        assert len(got) >= 3, (
            f"多盘合计只产出 {len(got)} 个六亲/婚育维度：{sorted(got)}"
            "（接入失效？）")

    def test_coverage_not_regressed(self):
        """维度覆盖不得倒退（回退 ⇒ 必须说明并改这张断言）。"""
        r = HeluoAdapter().compute((1990, 8, 8, 20), gender="male",
                                   target_date="2026-10-23")
        bd = (r.guajie or {}).get("by_dimension") or {}
        assert len(bd) >= 14, f"维度覆盖回退到 {len(bd)}（曾达 15）"
