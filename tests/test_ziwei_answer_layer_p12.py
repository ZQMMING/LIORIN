# -*- coding: utf-8 -*-
"""Z74d → Z80-E: 答案层组装测试（两派平行 → 12 宫位维 + 3 体用项）。

Z80-E：答案层分层输出 ——
  dimensions（12 宫位维，与 interpretation 12 人生维度 1:1 对齐）
  body_use（格局/应期/四化体用，体用层独立字段）
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.answer_layer import (
    BODY_USE_KEYS,
    PALACE_DIMENSIONS,
    build_answer,
)


@pytest.fixture(scope="module")
def engine():
    return ZiweiEngine()


class TestAnswerLayerZ74d:
    """答案层：两派规则命中 → 分维度平行答案。"""

    def test_twelve_palace_dimensions(self, engine):
        """12 宫位维齐备，两派并行输出。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male")
        ans = build_answer(ch)
        assert set(ans["dimensions"]) == set(PALACE_DIMENSIONS)
        assert ans["summary"]["sanhe_total"] > 0
        assert ans["summary"]["qintian_total"] > 0

    def test_body_use_layer_present(self, engine):
        """体用层独立存在（格局/应期/四化体用）。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male")
        ans = build_answer(ch)
        assert set(ans["body_use"].keys()) == set(BODY_USE_KEYS)
        for k in BODY_USE_KEYS:
            assert ans["body_use"][k], f"体用项 {k} 为空"

    def test_dimension_items_structured(self, engine):
        """每条维度答案有 source/rule_id/text。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male")
        ans = build_answer(ch)
        for dim in PALACE_DIMENSIONS:
            for it in ans["answer"][dim]:
                assert it["source"] in ("sanhe", "qintian")
                assert it["rule_id"]
                assert it["text"]

    def test_sihua_text_generated(self, engine):
        """生年四化入宫文本生成（SANHE-SIHUA-癸-化禄 → 生年癸干化禄入官禄宫）。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male")
        ans = build_answer(ch)
        found = False
        for it in ans["body_use"]["四化体用"]:
            if it["rule_id"] == "SANHE-SIHUA-癸-化禄":
                assert "生年癸干化禄入官禄宫" in it["text"]
                found = True
        assert found

    def test_parallel_no_vote(self, engine):
        """南北派各自保留：四化体用必两派，其余宫位维非空即可。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male")
        ans = build_answer(ch)
        # 四化体用（体用层）两派都在
        sources = {it["source"] for it in ans["body_use"]["四化体用"]}
        assert sources == {"sanhe", "qintian"}
        # 宫位维至少一方有内容
        for dim in ("命宫", "官禄", "财帛"):
            assert ans["answer"][dim], dim


class TestAnswerLayerZ74f:
    """答案层过滤：三方会照格局归「格局」体用项，坐命格局进宫位维。"""

    def test_sanfang_kept_out_of_main_dim(self, engine):
        """#38 车祸盘：官禄维度不再有「三方会照」贵格误报。"""
        ch = engine.full_chart((1954, 9, 30), 20, "male")
        ans = build_answer(ch)
        career = [it for it in ans["answer"]["官禄"] if it["source"] == "sanhe"]
        for it in career:
            assert "三方会照" not in it["text"]
        # 坐命断语在命宫维度
        joined = "".join(it["text"] for it in ans["answer"]["命宫"])
        assert "武府同宫" in joined or "武曲坐命" in joined or "天府坐命" in joined

    def test_sanfang_goes_to_geju(self, engine):
        """三方会照格局进「格局」体用项并标注（坐命单星格亦归此）。"""
        ch = engine.full_chart((1954, 9, 30), 20, "male")
        ans = build_answer(ch)
        geju = [it for it in ans["body_use"]["格局"] if it["source"] == "sanhe"]
        assert geju
        sanfang = [it for it in geju if "三方会照" in it["text"]]
        assert sanfang  # 至少有三方会照条目
        assert any("武曲坐命" in it["text"] for it in geju)  # 坐命单星格

    def test_flow_year_param(self, engine):
        """flow_year 参数化：#38 丙戌年(2006)流年应期可复现。"""
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_all_production
        ch = engine.full_chart((1954, 9, 30), 20, "male", flow_month=4, flow_year=2006)
        hits = detect_all_production(ch)
        c16 = next((c for c in hits if c.rule_id == "QTN-CMB-016"), None)
        assert c16 is not None
        assert c16.facts["flow_year"] == 2006
        assert c16.facts["flow_branch"] == "戌"
        assert c16.facts["flow_palace"] == "夫妻"
        assert c16.facts["flow_stem_used"] == "甲"
        c54 = next((c for c in hits if c.rule_id == "QTN-CMB-054"), None)
        assert c54 is not None
        # 钦天斗君（本命寅位宫）修正后：#38 四月 = 巳仆役宫 己干 文曲忌
        assert c54.facts["month_palace"] == "仆役"
        assert c54.facts["month_stem"] == "己"
        assert c54.facts["liuyue_sihua"]["ji"] == "文曲"


class TestBodyPalaceSixHomes:
    """A 项收尾：身宫只落六寄宫（命/财/官/迁/福/夫妻），非六寄宫物理不存在。"""

    def test_body_palace_only_six_homes(self, engine):
        """穷举 60×2 月×12 时步：身宫十二宫名恒在六处。"""
        from collections import Counter
        locs = Counter()
        for y in range(1960, 2020, 3):
            for m in (1, 6):
                for h in range(0, 24, 2):
                    ch = engine.full_chart((y, m, 1), h, "male")
                    bb = ch.bodyPalaceBranch
                    pn = next(p.palace_name for p in ch.palace_stems if p.branch == bb)
                    locs[pn] += 1
        assert len(locs) == 6
        assert set(locs) == {"命宫", "财帛", "官禄", "迁移", "福德", "夫妻"}
        assert len(set(locs.values())) == 1  # 均匀分布
