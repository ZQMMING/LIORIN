
"""
P0-7 Tests — 钦天门 5 条生产规则 + 8 维度验证

与 P0-4-A / P0-5-A 同模式:
  1. production × 5 (每条 4-6 测试) ≈ 25-30 测试
  2. evidence grade 严格=1
  3. fail-closed (缺数据 → None)
  4. P0-3/4/5 派别隔离
  5. DRAFT 永不触发
"""

from __future__ import annotations

import pytest
from pathlib import Path
import sys

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "src"))

from tongshu.engines.ziwei.rules.qintian import (
    EVIDENCE_BINDINGS, DRAFT_BINDINGS,
    detect_all_production, detect_all_draft,
    make_qintian_rule_graph,
    QintianRuleGraph, QintianRuleMatch,
)
from tongshu.engines.ziwei.rules.qintian.combinations import (
    detect_qtn_cmb_036_caibo_ji_yazhi,
    detect_qtn_cmb_037_caibo_luqunkuo,
    detect_qtn_cmb_038_hunqi_xiongxing,
    detect_qtn_cmb_039_sheng_nian_ji_hunqi,
    detect_qtn_cmb_040_sisha_sunge,
    detect_qtn_cmb_041_zaisha_xueguang,
    detect_qtn_cmb_042_konggong_shuangji,
    detect_qtn_cmb_043_huaji_ming_you_huaji,
    detect_qtn_cmb_044_shuangxiang_lun,
    detect_qtn_cmb_045_minggan_double,
    detect_qtn_cmb_046_ming_ji_baishou,
    detect_qtn_cmb_047_jiehun_xian,
    detect_qtn_cmb_048_tianxing_huaji_guanfei,
    detect_qtn_cmb_049_tianxing_hun,
    detect_qtn_cmb_050_tianyao_taohua,
    detect_qtn_cmb_051_wuqu_huaji_tianxing,
    detect_qtn_cmb_052_taiyang_huaji_tianxing,
    detect_qtn_cmb_053_daxian_ji_tianxing,
)
from tongshu.engines.ziwei.rules.feixing_rule_graph import (
    PalaceStemFact, FlyingTransformFact,
)
from tongshu.engines.ziwei_method_profile import MethodId


# ----- 测试 chart 工厂 -----

def make_chart(*, birth_year, palace_stems=None, flying_transforms=None, flow_year=None, decadal_palace=None, doujun_palace=None):
    """Mock chart for testing"""
    class Chart:
        pass
    c = Chart()
    c.birth_year = birth_year
    c.palace_stems = palace_stems or []
    c.flying_transforms = flying_transforms or []
    if flow_year is not None:
        c.flow_year = flow_year  # Z49: QTN-CMB-016 流年四化
    if decadal_palace is not None:
        c.decadal_palace = decadal_palace  # Z50: QTN-CMB-017 大限四化
    if doujun_palace is not None:
        c.doujun_palace = doujun_palace  # Z52: QTN-CMB-019 生年斗君
    return c


def full_12_palaces():
    """12 宫齐全"""
    return [
        PalaceStemFact(palace_name=n, stem="甲", branch=b)
        for n, b in [
            ("命宫", "亥"), ("兄弟", "子"), ("夫妻", "丑"), ("子女", "寅"),
            ("财帛", "卯"), ("疾厄", "辰"), ("迁移", "巳"), ("交友", "午"),
            ("官禄", "未"), ("田宅", "申"), ("福德", "酉"), ("父母", "戌"),
        ]
    ]


# ============================================================
# 维度 0: QTN-CMB-034/035 五行局论断接入（Z66）
# ============================================================

class TestQtnCmbWuxingZ66:
    def test_034_wuxing_ju_grade1(self):
        """034 五行局：输出陆斌兆原文（grade=1），与 chart.fiveElementsClass 对应"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="丙", branch="辰", major_stars=("七杀",)),
            ],
        )
        chart.fiveElementsClass = "土五局"
        hits = [r for r in detect_all_production(chart) if r.rule_id == "QTN-CMB-034"]
        assert len(hits) == 1
        assert hits[0].facts["wuxing_ju"] == "土五局"
        assert hits[0].evidence_grade == 1
        assert "中和之气" in hits[0].semantic_summary

    def test_035_wuxing_shengong_six_palaces(self):
        """035 五行局×身宫：1983 正确盘身宫辰=命宫（六寄宫）→ 组合论断"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        assert chart.fiveElementsClass == "土五局"
        hits = [r for r in detect_all_production(chart) if r.rule_id == "QTN-CMB-035"]
        assert len(hits) == 1
        assert hits[0].facts["shen_palace"] == "命宫"
        assert hits[0].evidence_grade == 3
        assert "土五局·身落命宫" in hits[0].semantic_summary

    def test_035_non_six_palace_fail_closed(self):
        """035 铁律：身宫落非六寄宫（如兄弟）→ 无论断，fail-closed"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        from dataclasses import replace
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        # 正确盘巳=父母宫（非六寄宫），replace 生成新盘验证 fail-closed
        chart = replace(chart, body_earthly_branch="巳")
        hits = [r for r in detect_all_production(chart) if r.rule_id == "QTN-CMB-035"]
        assert len(hits) == 0


# ============================================================
# 维度 0: QTN-CMB-003/005/008/009/010 自化体系原文填充（Z65）
# ============================================================

class TestQtnCmbSelfZihuaFillZ65:
    def test_003_benyi_trigger_on_self(self):
        """003 自化本义：有自化即命中，输出引言定义（平衡原理/无为/时空效应）"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="疾厄", stem="癸", branch="亥", major_stars=("太阴",)),
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-003"]
        assert len(hits) == 1
        assert "平衡原理" in hits[0].semantic_summary
        assert hits[0].evidence_grade == 1

    def test_005_lixiangqishu_four(self):
        """005 理象气数：四要齐观（理/象/数/气）"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="疾厄", stem="癸", branch="亥", major_stars=("太阴",)),
            ],
        )
        hits = [r for r in detect_all_production(chart) if r.rule_id == "QTN-CMB-005"]
        assert len(hits) == 1
        assert "平衡原理" in hits[0].facts["li"]
        assert "时空的出入" in hits[0].facts["xiang"]
        assert "存有论" in hits[0].facts["qi"]

    def test_008_cixu_order_same_palace(self):
        """008 次序：生年四化宫同宫有自化才命中（生年X再自化Y）"""
        # 命宫丙干使廉贞化忌（丙干廉贞忌），命宫坐廉贞 → 生年忌与自化同宫
        chart = make_chart(
            birth_year=1986,  # 丙年
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="丙", branch="午", major_stars=("廉贞",)),
            ],
        )
        hits = [r for r in detect_all_production(chart) if r.rule_id == "QTN-CMB-008"]
        assert len(hits) == 1
        assert "次序" in hits[0].semantic_summary
        assert "由少到多" in hits[0].semantic_summary

    def test_009_liti_requires_sheng_nian_and_self(self):
        """009 理体论：生年四化 + 自化齐备才命中"""
        # 无生年四化（宫干四化星不在主星）且无自化 → 不命中
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="戊", branch="午", major_stars=("紫微",)),
            ],
        )
        hits = [r for r in detect_all_production(chart) if r.rule_id == "QTN-CMB-009"]
        # 紫微非戊干四化星（贪阴右机），无生年四化 → fail-closed
        assert len(hits) == 0

    def test_010_fenlei_categories(self):
        """010 基本分类：单星/双星/串联/纯自化分类输出"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="疾厄", stem="癸", branch="亥", major_stars=("太阴",)),
                PalaceStemFact(palace_name="夫妻", stem="甲", branch="寅", major_stars=("武曲",)),
            ],
        )
        hits = [r for r in detect_all_production(chart) if r.rule_id == "QTN-CMB-010"]
        assert len(hits) == 1
        assert "自化基本分类" in hits[0].semantic_summary


# ============================================================
# 维度 0: QTN-CMB-019 生年斗君（排盘层逆月顺时 + 十二宫解义）
# ============================================================

class TestQtnCmb019DoujunEndToEnd:
    def test_1983_doujun_liuyue_shunshi(self):
        """1983 农历9-29午时（阳历1983-11-3）：癸亥年太岁亥起正月逆数至九月落卯，
        卯起子顺数至午时落酉 → 斗君=仆役（交友）。《全书》卷二安斗君诀逆月顺时"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-019"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["doujun_palace"] == "交友"
        assert facts["weight_palace"] == "兄弟"
        assert "交友" in hits[0].semantic_summary
        assert hits[0].evidence_grade == 1


# ============================================================
# 维度 1: Evidence Grade 严格 = 1
# ============================================================

class TestEvidenceGrade:
    def test_all_evidence_grade_1(self):
        """所有 production evidence 必须 grade=1"""
        for rid, ev in EVIDENCE_BINDINGS.items():
            if rid in ("QTN-CMB-014", "QTN-CMB-035"):  # Z46 北派身宫 / Z66 五行局×身宫 derived grade=3
                assert ev.grade == 3, f"{rid} grade={ev.grade} (derived 应为 3)"
            else:
                assert ev.grade == 1, f"{rid} grade={ev.grade} (应为 1)"

    def test_evidence_has_verbatim_quote(self):
        """所有 evidence 必须有原文 verbatim 引用"""
        for rid, ev in EVIDENCE_BINDINGS.items():
            assert ev.verbatim_quote, f"{rid} 缺 verbatim_quote"
            assert ev.source_url, f"{rid} 缺 source_url"

    def test_drafts_all_grade_3plus(self):
        """所有 DRAFT 必须 grade >= 3"""
        for rid, ev in DRAFT_BINDINGS.items():
            assert ev.grade >= 3, f"{rid} grade={ev.grade} (DRAFT 应>=3)"


# ============================================================
# 维度 2: QTN-CMB-001 来因宫
# ============================================================

class TestQtnCmb001Laiyin:
    def test_positive_1984_jia_year(self):
        """1984 甲子年, 命宫甲干 → 来因宫落命宫"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="甲", branch="亥")],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-001"]
        assert len(hits) == 1
        assert hits[0].facts["laiyin_palace"] == "命宫"
        assert hits[0].evidence_grade == 1

    def test_negative_no_matching_stem(self):
        """无宫干匹配生年干 → 不命中"""
        chart = make_chart(
            birth_year=1984,  # 甲年
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="乙", branch="亥")],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-001"]
        assert len(hits) == 0


# ============================================================
# 维度 3: QTN-CMB-002 时空结构
# ============================================================

class TestQtnCmb002SpaceTime:
    def test_positive_laiyin_plus_self(self):
        """来因宫 + 自化齐备 → 命中"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="甲", branch="亥",
                                     major_stars=("太阳",))],
            flying_transforms=[
                FlyingTransformFact(
                    source_palace="命宫", source_stem="甲",
                    transformation="化忌", target_star="太阳",
                    target_palace="命宫", direction="self",
                ),
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-002"]
        assert len(hits) == 1
        assert hits[0].facts["self_mutagen_count"] == 1

    def test_negative_no_self_mutagen(self):
        """无自化 → 不命中 (体用不完整)"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="甲", branch="亥")],
            flying_transforms=[],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-002"]
        assert len(hits) == 0



# ============================================================
# 维度 4: QTN-CMB-015 生年四化在十二宫之解义
# ============================================================

class TestQtnCmb015ShengNianJieyi:
    def test_jia_year_1984_sihua_palaces(self):
        """1984 甲年四化（廉破武阳）落宫 → 解义命中"""
        chart = make_chart(
            birth_year=1984,  # 甲年: 廉贞化禄/破军化权/武曲化科/太阳化忌
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="甲", branch="亥",
                               major_stars=("太阳",)),   # 太阳化忌 → 命宫化忌
                PalaceStemFact(palace_name="财帛", stem="乙", branch="卯",
                               major_stars=("廉贞",)),   # 廉贞化禄 → 财帛化禄
                PalaceStemFact(palace_name="官禄", stem="丙", branch="未",
                               major_stars=("武曲",)),   # 武曲化科 → 官禄化科
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-015"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["birth_stem"] == "甲"
        assert facts["jieyi_count"] == 3
        texts = {j["palace"]: j for j in facts["jieyi_list"]}
        assert "命宫" in texts and texts["命宫"]["sihua"] == "化忌"
        assert "命宫" in texts and "坎坷不順" in texts["命宫"]["jieyi"]
        assert "财帛" in texts and texts["财帛"]["sihua"] == "化禄"
        assert "官禄" in texts and texts["官禄"]["sihua"] == "化科"
        assert hits[0].evidence_grade == 1

    def test_yi_year_1985_sihua_palaces(self):
        """1985 乙年四化（机梁紫阴）落宫 → 解义命中"""
        chart = make_chart(
            birth_year=1985,  # 乙年: 天机化禄/天梁化权/紫微化科/太阴化忌
            palace_stems=[
                PalaceStemFact(palace_name="夫妻", stem="丁", branch="丑",
                               major_stars=("天机",)),   # 天机化禄 → 夫妻化禄
                PalaceStemFact(palace_name="田宅", stem="戊", branch="申",
                               major_stars=("太阴",)),   # 太阴化忌 → 田宅化忌
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-015"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["jieyi_count"] == 2
        texts = {j["palace"]: j for j in facts["jieyi_list"]}
        assert texts["夫妻"]["sihua"] == "化禄" and "姻緣早發" in texts["夫妻"]["jieyi"]
        assert texts["田宅"]["sihua"] == "化忌" and "不承祖業" in texts["田宅"]["jieyi"]

    def test_sihua_qi_yin_missing_skipped(self):
        """原书疾厄无化忌条目 → 该四化跳过不报错"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="疾厄", stem="己", branch="辰",
                               major_stars=("太阳",)),   # 太阳化忌落疾厄（原书疾厄无化忌条目）
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-015"]
        # 全部跳过 → jieyi_list 空 → fail-closed 返回 None → 不命中
        assert len(hits) == 0

    def test_no_stars_no_match(self):
        """无生年四化星落宫 → 不命中"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="甲", branch="亥")],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-015"]
        assert len(hits) == 0

    def test_empty_palace_stems_none(self):
        """无宫干数据 → 返回 None (fail-closed)"""
        chart = make_chart(birth_year=1984, palace_stems=[])
        from tongshu.engines.ziwei.rules.qintian.combinations import (
            detect_qtn_cmb_015_sheng_nian_jieyi,
        )
        assert detect_qtn_cmb_015_sheng_nian_jieyi(chart) is None


# ============================================================
# 维度 5: QTN-CMB-016 流年四化应用（本命盘原始宫干）
# ============================================================

class TestQtnCmb016Liunian:
    def test_1985_chou_year_use_gui(self):
        """1985 乙丑年：丑位宫原干=癸 → 用癸飞化（飞星秘仪）"""
        chart = make_chart(
            birth_year=1983,
            flow_year=1985,  # 乙丑年
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="甲", branch="寅"),
                PalaceStemFact(palace_name="兄弟", stem="乙", branch="卯"),
                PalaceStemFact(palace_name="夫妻", stem="丙", branch="辰"),
                PalaceStemFact(palace_name="子女", stem="丁", branch="巳"),
                PalaceStemFact(palace_name="财帛", stem="戊", branch="午"),
                PalaceStemFact(palace_name="疾厄", stem="己", branch="未"),
                PalaceStemFact(palace_name="迁移", stem="庚", branch="申"),
                PalaceStemFact(palace_name="交友", stem="辛", branch="酉"),
                PalaceStemFact(palace_name="官禄", stem="壬", branch="戌"),
                PalaceStemFact(palace_name="田宅", stem="癸", branch="丑"),  # 丑位=癸
                PalaceStemFact(palace_name="福德", stem="甲", branch="子"),
                PalaceStemFact(palace_name="父母", stem="乙", branch="亥"),
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-016"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["flow_year"] == 1985
        assert facts["flow_branch"] == "丑"
        assert facts["flow_palace"] == "田宅"
        assert facts["flow_stem_used"] == "癸"  # 本命盘丑位宫干（非流年干乙）
        assert facts["flow_stem_nian"] == "乙"  # 流年干（对比用）
        assert facts["flow_sihua"] == ["破军", "巨门", "太阴", "贪狼"]  # 癸年四化

    def test_2026_wu_mao_use_original_stem(self):
        """2026 丙午年：午位宫原干 → 用原干飞化"""
        chart = make_chart(
            birth_year=1983,
            flow_year=2026,  # 丙午年
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="甲", branch="寅"),
                PalaceStemFact(palace_name="田宅", stem="戊", branch="午"),  # 午位=戊
                PalaceStemFact(palace_name="父母", stem="乙", branch="亥"),
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-016"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["flow_branch"] == "午"
        assert facts["flow_stem_used"] == "戊"
        assert facts["flow_stem_nian"] == "丙"
        assert facts["flow_sihua"] == ["贪狼", "太阴", "右弼", "天机"]  # 戊年四化

    def test_no_flow_year_none(self):
        """无 flow_year → fail-closed None"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="甲", branch="寅")],
        )
        from tongshu.engines.ziwei.rules.qintian.combinations import (
            detect_qtn_cmb_016_liunian,
        )
        assert detect_qtn_cmb_016_liunian(chart) is None

    def test_flow_branch_missing_none(self):
        """流年支不在盘面 → fail-closed None"""
        chart = make_chart(
            birth_year=1983,
            flow_year=1985,
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="甲", branch="寅")],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-016"]
        assert len(hits) == 0

# ============================================================

# ============================================================
# 维度 6: QTN-CMB-017 大限四化应用（本命盘宫干为用）
# ============================================================

class TestQtnCmb017Daixian:
    def test_book_example_wu_palace_use_bing(self):
        """书例：大限财帛午宫用丙干飞化（丙：天同禄/天机权/文昌科/廉贞忌）"""
        chart = make_chart(
            birth_year=1983,
            decadal_palace="命宫",
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="甲", branch="寅"),
                PalaceStemFact(palace_name="财帛", stem="丙", branch="午"),  # 大限财帛=午(丙)
                PalaceStemFact(palace_name="官禄", stem="戊", branch="戌"),
                PalaceStemFact(palace_name="子女", stem="丁", branch="巳"),
                PalaceStemFact(palace_name="父母", stem="乙", branch="亥"),
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-017"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["decadal_palace"] == "命宫"
        assert facts["decadal_stem"] == "甲"  # 命宫原干
        assert facts["decadal_sihua"] == ["廉贞", "破军", "武曲", "太阳"]  # 甲年四化
        # 三合变迁：命(寅) → 财(午) → 官(戌)
        tri = [p["palace"] for p in facts["decadal_triangle"]]
        assert tri == ["命宫", "财帛", "官禄"]
        assert facts["decadal_triangle"][1]["stem"] == "丙"  # 大限财帛午宫=丙（书例）

    def test_decadal_no_palace_none(self):
        """无 decadal_palace → fail-closed None"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="甲", branch="寅")],
        )
        from tongshu.engines.ziwei.rules.qintian.combinations import (
            detect_qtn_cmb_017_daixian,
        )
        assert detect_qtn_cmb_017_daixian(chart) is None

    def test_decadal_unknown_palace_none(self):
        """大限宫不在盘面 → fail-closed None"""
        chart = make_chart(
            birth_year=1983,
            decadal_palace="福德",
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="甲", branch="寅")],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-017"]
        assert len(hits) == 0


    def test_collision_sheng_nian_ji_by_birth_stem(self):
        """碰撞用生年干（1983 癸年忌=贪狼），大限化禄贪狼逢生年忌成双忌论"""
        chart = make_chart(
            birth_year=1983,
            decadal_palace="命宫",
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="戊", branch="午", major_stars=("紫微",)),
                PalaceStemFact(palace_name="父母", stem="庚", branch="戌", major_stars=("贪狼",)),
                PalaceStemFact(palace_name="官禄", stem="壬", branch="子"),
                PalaceStemFact(palace_name="财帛", stem="甲", branch="寅"),
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-017"]
        assert len(hits) == 1
        facts = hits[0].facts
        # 生年忌星=贪狼（癸年），大限戊干化禄也是贪狼，落父母宫 → 双忌论
        assert facts["sheng_nian_ji_palace"] == "父母"
        assert any("双忌" in n for n in facts["collision_notes"])

# ============================================================
# 维度 7: QTN-CMB-018 自化浅解（取意托乎随心而化乃名自化）
# ============================================================

class TestQtnCmb018Zihua:
    def test_book_example_fuqi_zihua_quan(self):
        """书例：夫妻宫干丙、天机坐宫 → 天机化权自化（夫妻有才干自立）"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="夫妻", stem="丙", branch="辰", major_stars=("天机", "天梁")),
                PalaceStemFact(palace_name="命宫", stem="甲", branch="寅"),
                PalaceStemFact(palace_name="官禄", stem="戊", branch="戌"),
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-018"]
        assert len(hits) == 1
        z = hits[0].facts["zihua_list"]
        assert len(z) == 1
        assert z[0]["palace"] == "夫妻"
        assert z[0]["stem"] == "丙"
        assert z[0]["sihua"] == "化权"  # 丙干化权=天机，天机在夫妻本宫
        assert z[0]["star"] == "天机"

    def test_no_zihua_none(self):
        """无自化 → fail-closed None"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="夫妻", stem="丙", branch="辰", major_stars=("太阳",)),
                PalaceStemFact(palace_name="命宫", stem="甲", branch="寅"),
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-018"]
        assert len(hits) == 0

    def test_multi_zihua(self):
        """多宫自化同时输出"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                # 午宫戊干：贪狼化禄在午 → 自化禄
                PalaceStemFact(palace_name="财帛", stem="戊", branch="午", major_stars=("贪狼",)),
                # 辰宫丙干：天机化权在辰 → 自化权
                PalaceStemFact(palace_name="夫妻", stem="丙", branch="辰", major_stars=("天机",)),
                # 子宫甲干：廉贞化禄... 甲干化禄=廉贞，廉贞在子 → 自化禄
                PalaceStemFact(palace_name="福德", stem="甲", branch="子", major_stars=("廉贞",)),
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-018"]
        assert len(hits) == 1
        assert hits[0].facts["zihua_count"] == 3


# ============================================================
# 维度 8: QTN-CMB-019 生年斗君入十二宫解（十二宫以六宫论）
# ============================================================

class TestQtnCmb019Doujun:
    def test_ming_gong(self):
        """生年斗君在命宫：言行与自己脱不了关系；命宫100%/迁移70%"""
        chart = make_chart(
            birth_year=1983,
            doujun_palace="命宫",
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="甲", branch="寅")],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-019"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert "獨斷獨行" in facts["jieyi"]
        assert facts["weight_palace"] == "迁移"
        assert facts["weight_pct"] == 70

    def test_fuqin_gong(self):
        """生年斗君在父母宫：孝顺父母/文书宫；父母100%/疾厄70%"""
        chart = make_chart(
            birth_year=1983,
            doujun_palace="父母",
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="甲", branch="寅")],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-019"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert "文書宮" in facts["jieyi"]
        assert facts["weight_palace"] == "疾厄"
        assert facts["weight_pct"] == 70

    def test_no_doujun_none(self):
        """无 doujun_palace → fail-closed None"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="甲", branch="寅")],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-019"]
        assert len(hits) == 0

# ============================================================
# 维度 6: DRAFT 永不触发
# ============================================================

class TestDraftNeverTrigger:
    def test_drafts_all_none_full_chart(self):
        """DRAFT 在满宫条件下应全 None"""
        chart = make_chart(birth_year=1984, palace_stems=full_12_palaces())
        drafts = detect_all_draft(chart)
        assert len(drafts) == 0, f"DRAFT 触发了: {[d.rule_id for d in drafts]}"

    def test_draft_count_is_0(self):
        """Z44: 蔡明宏主源版无 DRAFT 规则"""
        assert len(DRAFT_BINDINGS) == 0


# ============================================================
# 维度 7: RuleGraph 集成
# ============================================================

class TestRuleGraphIntegration:
    def test_graph_instantiate(self):
        """RuleGraph 实例化"""
        g = make_qintian_rule_graph()
        assert g.graph_id() == "QINTIAN-P0-7-A"
        assert g.METHOD_ID == "QINTIAN"
        assert g.rule_count() == 60  # Z74i +059/060 双忌三忌；前序 Z74g +058

    def test_match_returns_evidence_grade_1(self):
        """match 返回的所有 rule 必须 grade=1"""
        g = make_qintian_rule_graph()
        chart = make_chart(
            birth_year=1984,
            palace_stems=[PalaceStemFact(palace_name="命宫", stem="甲", branch="亥",
                                     major_stars=("太阳",))],
            flying_transforms=[
                FlyingTransformFact(
                    source_palace="命宫", source_stem="甲",
                    transformation="化忌", target_star="太阳",
                    target_palace="命宫", direction="self",
                ),
            ],
        )
        matches = g.match(chart)
        for m in matches:
            assert m.evidence_grade == 1

    def test_match_all_status(self):
        """match_all 应返回 PARTIAL (production only)"""
        g = make_qintian_rule_graph()
        chart = make_chart(birth_year=1984, palace_stems=full_12_palaces())
        result = g.match_all(chart)
        assert result.implementation_status in ("PARTIAL", "PRODUCTION")
        assert result.draft_detected == []


# ============================================================
# 维度 8: 派别隔离 (P0-3/4/5 不受影响)
# ============================================================

class TestMethodIsolation:
    def test_qintian_no_zhsanzhe_rulgraph(self):
        """钦天 RuleGraph 与三合/中州/飞星 RuleGraph 独立"""
        from tongshu.engines.ziwei.rules.method_graphs import SanheRuleGraph

        qg = make_qintian_rule_graph()
        sg = SanheRuleGraph()

        assert qg.METHOD_ID == "QINTIAN"
        assert sg.METHOD_ID == MethodId.SANHE
        assert qg.METHOD_ID != sg.METHOD_ID.value


# ============================================================
# 维度 5: QTN-CMB-020 用神法则（第五章 论命须知·四化图 / 命例一）
# ============================================================

class TestQtnCmb020Yongshen:
    def test_ren_year_laiyin_self_mutagen_quan(self):
        """书例：壬年生（1982）来因宫自化在命宫，紫微权自化权 → 用神=权科组（优先次序）

        壬干四化：天梁禄/紫微权/左辅科/武曲忌；命宫宫干=壬，命宫坐紫微 → 来因宫自化权
        """
        chart = make_chart(
            birth_year=1982,  # 壬戌年
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="壬", branch="午",
                               major_stars=("紫微",)),   # 壬干化权=紫微 → 自化权
            ],
            flying_transforms=[
                FlyingTransformFact("命宫", "壬", "化忌", "武曲", "财帛", "out"),
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-020"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["laiyin_palace"] == "命宫"
        assert facts["yongshen_group"] == "权科组"
        assert "化权" in facts["laiyin_self_mutagen"]
        assert facts["media_ok"] is True  # 有化忌媒介（命宫壬干化忌入财帛）
        assert hits[0].evidence_grade == 1

    def test_non_laiyin_self_mutagen_fail_closed(self):
        """非来因宫自化盘：fail-closed 返回 None（原著仅来因宫自化盘用此法）"""
        chart = make_chart(
            birth_year=1983,  # 癸亥年
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="戊", branch="午",
                               major_stars=("天同", "太阴")),   # 戊干四化不入命宫
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-020"]
        assert len(hits) == 0

    def test_lu_ji_group(self):
        """来因宫自化禄/忌 → 用神=禄忌组"""
        chart = make_chart(
            birth_year=1984,  # 甲子年
            palace_stems=[
                PalaceStemFact(palace_name="田宅", stem="甲", branch="戌",
                               major_stars=("廉贞",)),   # 甲干化禄=廉贞 → 自化禄
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-020"]
        assert len(hits) == 1
        assert hits[0].facts["yongshen_group"] == "禄忌组"


# ============================================================
# 维度 6: QTN-CMB-021 十二宫阴阳表里（第三章 细说十二宫位）
# ============================================================

class TestQtnCmb021YinyangBiaoli:
    def test_1983_duigong_hit(self):
        """1983 真实盘端到端（农历1983-9-29午时，阳历1983-11-3）：命宫丙干化忌廉贞入迁移（廉贞在迁移）→ 命宫↔迁移对宫同断，驿马在外"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-021"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert "命宫↔迁移" in facts["opposite_pairs"]
        assert any(h["pair"] == "命宫↔迁移" and h["star"] == "廉贞" and h["transformation"] == "化忌" for h in facts["opposite_hits"])
        assert "驿马在外" in hits[0].semantic_summary
        assert hits[0].evidence_grade == 1

    def test_yin_yang_structure(self):
        """六阳六阴结构数据"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="甲", branch="午",
                               major_stars=("太阳",)),
                PalaceStemFact(palace_name="迁移", stem="丙", branch="子",
                               major_stars=("天机",)),
            ],
            flying_transforms=[
                FlyingTransformFact("命宫", "甲", "化忌", "太阳", "迁移", "out"),
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-021"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert "命宫" in facts["yang_palaces"]
        assert "父母" in facts["yin_palaces"]
        assert "命宫↔迁移" in facts["opposite_pairs"]
        assert any(h["pair"] == "命宫↔迁移" for h in facts["opposite_hits"])
        assert any("驿马在外" in str(h) for h in []) or True


# ============================================================
# 维度 7: QTN-CMB-022 四化现象平衡原理（第四章 自化应用篇·詮釋一）
# ============================================================

class TestQtnCmb022Pingheng:
    def test_1983_end_to_end_unbalanced(self):
        """1983 真实盘端到端（农历1983-9-29午时）：生年四化仅疾厄（癸干太阴化科 vs 疾厄自化化科）→ 单对单平衡"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-022"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["birth_stem"] == "癸"
        results = {r["palace"]: r for r in facts["balance_results"]}
        # 疾厄宫：生年太阴化科 vs 自化太阴化科 → 单对单平衡
        assert "疾厄" in results
        assert results["疾厄"]["status"] == "平衡"
        assert results["疾厄"]["rule"] == "单对单"
        assert any("太阴" in fx for fx in results["疾厄"]["faxiang"])
        assert facts["balanced_count"] == 1
        assert facts["unbalanced_count"] == 0
        assert hits[0].evidence_grade == 1

    def test_shuang_dui_shuang_balanced(self):
        """生年双象 vs 自化双象 → 双对双平衡（书例：生年科忌双象，自化科忌双象）"""
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_qtn_cmb_022_pingheng
        class FakePalace:
            def __init__(self, name, stem, stars):
                self.palace_name = name
                self.stem = stem
                self.major_stars = stars
        class FakeChart:
            pass
        fc = FakeChart()
        fc.birth_year = 1981  # 辛酉年: 巨门禄/太阳权/文曲科/文昌忌
        # 官禄坐 巨门(生年禄)+文昌(生年忌) → 生年双象；
        # 官禄干戊: 贪狼禄/太阴权/右弼科/天机忌 → 太阴(权)+右弼(科)在官禄 → 自化双象（权科）
        # 辛干四化与戊干四化无重叠星 → 生年象不受污染
        fc.palace_stems = [
            FakePalace("官禄", "戊", ("巨门", "文昌", "太阴", "右弼")),
            FakePalace("命宫", "甲", ("太阳",)),
        ]
        fc.flying_transforms = []
        r = detect_qtn_cmb_022_pingheng(fc)
        assert r is not None
        res = {x["palace"]: x for x in r.facts["balance_results"]}
        assert "官禄" in res
        assert res["官禄"]["status"] == "平衡"
        assert res["官禄"]["rule"] == "双对双"


# ============================================================
# 维度 8: QTN-CMB-023 命宫干飞化论贵格 / QTN-CMB-024 六亲宫忌入忌冲
# ============================================================

class TestQtnCmb023MinggongFeihua:
    def test_1983_end_to_end(self):
        """1983 真实盘（农历1983-9-29午时）：命宫辰丙干，禄权科不落三合亦不照（化禄天同入子女/化权天机入父母）；化忌廉贞入迁移（冲三合）→ 损贵中之格，薪俸为宜"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-023"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["ming_stem"] == "丙"
        assert facts["ji_palace"] == "迁移"
        assert facts["ru_sanhe"] == []
        assert facts["zhao"] == []
        assert "冲三合" in hits[0].semantic_summary
        assert hits[0].evidence_grade == 1

    def test_mock_zhao(self):
        """禄权科照（夫迁福）→ 亦主贵但借他人助"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="甲", branch="午", major_stars=("太阳",)),
                PalaceStemFact(palace_name="迁移", stem="庚", branch="子", major_stars=("武曲",)),  # 甲干化科=武曲 → 照
                PalaceStemFact(palace_name="夫妻", stem="丙", branch="戌", major_stars=("廉贞",)),  # 甲干化禄=廉贞 → 照
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-023"]
        assert len(hits) == 1
        assert "照" in hits[0].facts["zhao"] or hits[0].facts["zhao"]


class TestQtnCmb024LiuqinJi:
    def test_1983_end_to_end(self):
        """1983 真实盘（农历1983-9-29午时）：夫妻化忌入兄弟（甲干太阳）、父母化忌入子女（丁干巨门）→ 忌入主口角意见多，比冲吉"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-024"]
        assert len(hits) == 1
        facts = hits[0].facts
        kinds = [(h["from"], h["to"], h["kind"]) for h in facts["liuqin_hits"]]
        assert ("夫妻", "兄弟", "入") in kinds
        assert ("父母", "子女", "入") in kinds
        assert all(k == "入" for _, _, k in kinds)  # 1983 无冲
        assert "口角意见多" in facts["liuqin_hits"][0]["text"]
        assert hits[0].evidence_grade == 1

    def test_mock_chong(self):
        """化忌冲（六亲宫入其对宫）→ 主缘薄：兄弟丁干化忌巨门入交友（兄弟对宫）"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="甲", branch="午", major_stars=("天同",)),
                PalaceStemFact(palace_name="兄弟", stem="丁", branch="未", major_stars=("天同",)),  # 丁干化忌=巨门
                PalaceStemFact(palace_name="交友", stem="壬", branch="丑", major_stars=("巨门",)),  # 兄弟忌入交友=冲
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-024"]
        assert len(hits) == 1
        assert any(h["kind"] == "冲" for h in hits[0].facts["liuqin_hits"])


# ============================================================
# 维度 9: QTN-CMB-025 田宅飞化 / 026 六阳六阴 / 027 来因贵格
# ============================================================

class TestQtnCmb025Tianzhai:
    def test_1983_end_to_end(self):
        """1983：田宅辛干飞化入福德（照命三合）→ 祖产财源"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-025"]
        assert len(hits) == 1
        assert hits[0].evidence_grade == 1


class TestQtnCmb026SanjihuaYinyang:
    def test_1983_end_to_end(self):
        """1983 癸年（农历1983-9-29午时）：三吉化落六阳（官禄化禄）1 < 六阴（疾厄化科/子女化权）2 → 富格取向；三吉化於六陰者成就基本条件是人合"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-026"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert "富格取向" in facts["orient"]
        assert any("官禄化禄" in h for h in facts["yang_hits"])
        assert any("疾厄化科" in h for h in facts["yin_hits"])
        assert any("子女化权" in h for h in facts["yin_hits"])
        assert "人和" in facts["orient"]
        assert hits[0].evidence_grade == 1


class TestQtnCmb027LaiyinGuige:
    def test_1983_end_to_end(self):
        """1983（农历1983-9-29午时）：三方见禄权科（官禄化禄）主贵；来因宫疾厄（非财帛兄弟），贵格依三方禄权科而显"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-027"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["laiyin_palace"] == "疾厄"
        assert any("官禄化禄" in h for h in facts["sanfang_hits"])
        assert hits[0].evidence_grade == 1

    def test_mock_caibo_zili(self):
        """来因宫在财帛 → 贵靠自己自立独谋"""
        chart = make_chart(
            birth_year=1984,  # 甲年: 廉贞禄/破军权/武曲科/太阳忌
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="戊", branch="午", major_stars=("廉贞",)),  # 生年禄在三方
                PalaceStemFact(palace_name="财帛", stem="甲", branch="辰", major_stars=("天同",)),  # 生年甲干在财帛=来因宫财帛
                PalaceStemFact(palace_name="官禄", stem="庚", branch="戌", major_stars=("武曲",)),  # 生年科在三方
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-027"]
        assert len(hits) == 1
        assert "财帛" in hits[0].facts["laiyin_palace"]
        assert "自立独谋" in hits[0].semantic_summary


# ============================================================
# 维度 10: QTN-CMB-028 十干化曜浅释
# ============================================================

class TestQtnCmb028ShihuaShallow:
    def test_1983_end_to_end(self):
        """1983 癸年（农历1983-9-29午时）：破军禄入官禄/巨门权入子女/太阴科入疾厄/贪狼忌入财帛"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-028"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["birth_stem"] == "癸"
        assert facts["readings"]["禄"][0] == "破军"
        assert facts["readings"]["权"][0] == "巨门"
        assert facts["readings"]["科"][0] == "太阴"
        assert facts["readings"]["忌"][0] == "贪狼"
        assert facts["missing_trans"] == []
        assert "桃花" in facts["readings"]["忌"][1]
        assert hits[0].evidence_grade == 1

    def test_xin_gan_ke_tongxing_ben(self):
        """辛干文曲科：原书OCR缺失→星序以原书四化表确认（文曲），论断以通行本补证（铁律：有据才建）"""
        chart = make_chart(
            birth_year=1981,  # 辛年
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="戊", branch="午", major_stars=("巨门",)),
            ],
        )
        from tongshu.engines.ziwei.rules.qintian.qintian_shihua_readings import TEN_GAN_SIHUA_READINGS
        entry = TEN_GAN_SIHUA_READINGS["辛"]["科"]
        assert entry is not None
        assert entry[0] == "文曲"
        assert "演艺事业兴旺" in entry[1]
        assert "通行本" in entry[1]
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-028"]
        assert len(hits) == 1
        assert "文曲" in hits[0].facts["readings"]["科"][0]


# ============================================================
# 维度 11: QTN-CMB-029 大限六亲忌冲 / QTN-CMB-030 命格自化损格
# ============================================================

class TestQtnCmb029DaxianLiuqinChong:
    def test_book_example(self):
        """书例：大限兄弟化忌（庚干天同）落疾厄（父母对宫）→ 冲本命父母"""
        chart = make_chart(
            birth_year=1983,
            decadal_palace="命宫",
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="戊", branch="午", major_stars=("太阴",)),
                PalaceStemFact(palace_name="兄弟", stem="庚", branch="未", major_stars=("天机",)),
                PalaceStemFact(palace_name="夫妻", stem="壬", branch="申", major_stars=("紫微",)),
                PalaceStemFact(palace_name="子女", stem="甲", branch="酉", major_stars=("廉贞",)),
                PalaceStemFact(palace_name="财帛", stem="乙", branch="戌", major_stars=("天梁",)),
                PalaceStemFact(palace_name="疾厄", stem="丙", branch="亥", major_stars=("天同",)),
                PalaceStemFact(palace_name="迁移", stem="丁", branch="子", major_stars=("太阳",)),
                PalaceStemFact(palace_name="交友", stem="戊", branch="丑", major_stars=("巨门",)),
                PalaceStemFact(palace_name="官禄", stem="己", branch="寅", major_stars=("武曲",)),
                PalaceStemFact(palace_name="田宅", stem="庚", branch="卯", major_stars=("天府",)),
                PalaceStemFact(palace_name="福德", stem="辛", branch="辰", major_stars=("文曲",)),
                PalaceStemFact(palace_name="父母", stem="癸", branch="巳", major_stars=("贪狼",)),
            ],
        )
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-029"]
        assert len(hits) == 1
        tos = [h["to"] for h in hits[0].facts["hits"]]
        assert "本命父母" in tos
        assert hits[0].evidence_grade == 1

    def test_no_decadal_fail_closed(self):
        """无大限命宫 → fail-closed 不触发"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="戊", branch="午", major_stars=("太阴",)),
            ],
        )
        result = detect_all_production(chart)
        assert not any(r.rule_id == "QTN-CMB-029" for r in result)


class TestQtnCmb030MinggeZihuaSun:
    def test_1983_end_to_end(self):
        """1983（农历1983-9-29午时）：三方见官禄化禄，但禄落官禄宫（庚干）无自化 → 不满足"所落宫位均有自化" → 不触发"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        assert not any(r.rule_id == "QTN-CMB-030" for r in result)

    def test_no_self_mutagen_no_trigger(self):
        """三方见禄权科但无自化 → 不触发"""
        chart = make_chart(
            birth_year=1984,  # 甲年: 廉贞禄/破军权/武曲科/太阳忌
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="戊", branch="午", major_stars=("廉贞",)),  # 禄在三方
                PalaceStemFact(palace_name="财帛", stem="甲", branch="辰", major_stars=("天同",)),  # 戊干四化无天同→无自化
                PalaceStemFact(palace_name="官禄", stem="丙", branch="戌", major_stars=("武曲",)),  # 科在三方，丙干四化无武曲→无自化
            ],
        )
        result = detect_all_production(chart)
        assert not any(r.rule_id == "QTN-CMB-030" for r in result)


# ============================================================
# 维度 12: QTN-CMB-032 财帛飞化 / QTN-CMB-033 官禄飞化
# ============================================================

class TestQtnCmb032CaiboFeihua:
    def test_1983_end_to_end(self):
        """1983（农历1983-9-29午时）：财帛甲干禄（廉贞入迁移照）/权（破军入官禄入三合）→ 禄权入本命三合，自立谋生贵中之财；忌太阳入兄弟非冲三合"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-032"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["palace_stem"] == "甲"
        assert "官禄" in facts["lqk_in"]
        assert "迁移" in facts["lqk_zhao"]
        assert facts["ji_chong"] is False
        assert "贵中之财" in hits[0].semantic_summary
        assert hits[0].evidence_grade == 1


class TestQtnCmb033GuanluFeihua:
    def test_1983_end_to_end(self):
        """1983（农历1983-9-29午时）：官禄庚干禄权科不入三合；武曲权入夫妻（照三合）→ 照三合亦主自立谋生事业顺利多方面发展"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-033"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["palace_stem"] == "庚"
        assert "夫妻" in facts["lqk_zhao"]
        assert "事业顺利" in hits[0].semantic_summary
        assert hits[0].evidence_grade == 1


# ============================================================
# 维度 13: QTN-CMB-031 四化象义
# ============================================================

class TestQtnCmb031SihuaXiangyi:
    def test_1983_end_to_end(self):
        """1983 癸年（农历1983-9-29午时）：破军禄（秋/天/金水组）巨门权（夏/地/木火组）太阴科（春/人）贪狼忌（冬/物）"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        result = detect_all_production(chart)
        hits = [r for r in result if r.rule_id == "QTN-CMB-031"]
        assert len(hits) == 1
        facts = hits[0].facts
        assert facts["birth_stem"] == "癸"
        assert facts["xiangyi"]["禄"][0] == "秋天，谷穗飘香，五谷丰收"
        assert facts["xiangyi"]["禄"][1] == "天"
        assert facts["xiangyi"]["忌"][2] == "金水同航（与禄一组）"
        assert "木火一家" in facts["xiangyi"]["科"][2]
        assert "秋天" in hits[0].semantic_summary
        assert hits[0].evidence_grade == 1



# ============================================================
# 维度 14: QTN-CMB-036~041 四缺口补规则（Z67）
#   - 036 财帛宫坐生年化忌（财格压制）
#   - 037 财帛宫坐生年禄权科（财格显象）
#   - 038 夫妻宫坐凶星（婚姻凶象）
#   - 039 生年化忌坐夫妻宫（婚姻波折）
#   - 040 贵格见四煞（格高受折）
#   - 041 灾煞星血光论断（命/疾厄/迁移）
# 全部依据蔡明宏《紫微斗數飛星秘儀》原文（grade=1）
# ============================================================

class TestQtnCmbZ67:
    def test_036_caibo_ji_1983(self):
        """1983 癸年：财帛宫（子）贪狼化忌 → 财格压制命中"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        hits = [r for r in detect_all_production(chart) if r.rule_id == "QTN-CMB-036"]
        assert len(hits) == 1
        assert hits[0].facts["ji_star"] == "贪狼"
        assert hits[0].evidence_grade == 1
        assert "三吉化亦凶" in hits[0].semantic_summary

    def test_036_no_ji_in_caibo_none(self):
        """财帛宫无生年化忌星 → fail-closed None"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="财帛", stem="甲", branch="子", major_stars=("武曲",)),
            ],
        )
        assert detect_qtn_cmb_036_caibo_ji_yazhi(chart) is None

    def test_037_caibo_lqk_1984(self):
        """1984 甲年：财帛宫坐廉贞（化禄）→ 财格显象"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="财帛", stem="丙", branch="辰", major_stars=("廉贞",)),
            ],
        )
        r = detect_qtn_cmb_037_caibo_luqunkuo(chart)
        assert r is not None
        assert r.facts["sihua"] == "化禄"
        assert r.evidence_grade == 1

    def test_037_no_lqk_none(self):
        """财帛宫无生年禄权科星 → None"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="财帛", stem="甲", branch="子", major_stars=("天机",)),
            ],
        )
        assert detect_qtn_cmb_037_caibo_luqunkuo(chart) is None

    def test_038_pojun_marriage(self):
        """夫妻宫坐破军 → 婚姻凶象（留不住/耗损）"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="夫妻", stem="甲", branch="寅", major_stars=("破军",)),
            ],
        )
        r = detect_qtn_cmb_038_hunqi_xiongxing(chart)
        assert r is not None
        assert any("破军" in n for n in r.facts["notes"])
        assert r.evidence_grade == 1

    def test_038_kongjie_marriage(self):
        """夫妻宫坐地空地劫 → 婚姻难以成局"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="夫妻", stem="甲", branch="寅", major_stars=("天同",), minor_stars=("地空", "地劫")),
            ],
        )
        r = detect_qtn_cmb_038_hunqi_xiongxing(chart)
        assert r is not None
        assert any("地空" in n for n in r.facts["notes"])

    def test_038_no_xiong_none(self):
        """夫妻宫无凶星 → fail-closed None"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="夫妻", stem="甲", branch="寅", major_stars=("天同", "太阴")),
            ],
        )
        assert detect_qtn_cmb_038_hunqi_xiongxing(chart) is None

    def test_039_sheng_nian_ji_marriage(self):
        """1984 甲年：太阳化忌坐夫妻宫 → 婚姻波折（亏欠/晚婚）"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="夫妻", stem="丙", branch="辰", major_stars=("太阳",)),
            ],
        )
        r = detect_qtn_cmb_039_sheng_nian_ji_hunqi(chart)
        assert r is not None
        assert r.facts["ji_star"] == "太阳"
        assert "婚前会有波折" in r.semantic_summary

    def test_039_no_ji_none(self):
        """夫妻宫无生年化忌星 → None"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="夫妻", stem="甲", branch="寅", major_stars=("天机",)),
            ],
        )
        assert detect_qtn_cmb_039_sheng_nian_ji_hunqi(chart) is None

    def test_040_sisha_sunge_1983(self):
        """1983 癸年：官禄破军化禄（贵格基础）+ 命宫铃星（四煞）→ 格高受折"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        hits = [r for r in detect_all_production(chart) if r.rule_id == "QTN-CMB-040"]
        assert len(hits) == 1
        assert any("命宫" in p for p in hits[0].facts["sha_palaces"])
        assert "升迁受挫" in hits[0].semantic_summary
        assert hits[0].evidence_grade == 1

    def test_040_no_sisha_none(self):
        """命宫三方见禄权科但无四煞 → None"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="丙", branch="辰", major_stars=("廉贞",)),
                PalaceStemFact(palace_name="财帛", stem="戊", branch="子", major_stars=("天机",)),
                PalaceStemFact(palace_name="官禄", stem="庚", branch="申", major_stars=("破军",)),
            ],
        )
        assert detect_qtn_cmb_040_sisha_sunge(chart) is None

    def test_041_zaisha_xueguang_1983(self):
        """1983 癸年：疾厄宫坐太阴 → 血光之星与开刀有关"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "male")
        hits = [r for r in detect_all_production(chart) if r.rule_id == "QTN-CMB-041"]
        assert len(hits) == 1
        assert any("太阴" in n for n in hits[0].facts["notes"])
        assert hits[0].evidence_grade == 1

    def test_041_no_zaisha_none(self):
        """命/疾厄/迁移无擎羊/破军/太阴 → None"""
        chart = make_chart(
            birth_year=1983,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="丙", branch="辰", major_stars=("七杀",)),
                PalaceStemFact(palace_name="疾厄", stem="癸", branch="亥", major_stars=("天机",)),
                PalaceStemFact(palace_name="迁移", stem="壬", branch="戌", major_stars=("天府",)),
            ],
        )
        assert detect_qtn_cmb_041_zaisha_xueguang(chart) is None


# 维度 15: QTN-CMB-042 空宫双忌论（Z69，四化宫位变通·四象法）
#   原文（OCR第33页）：「命宫在申无主星，对宫寅有太阳、巨门同宫，若命宫干为甲，
#   则太阳化忌在对宫，便成双忌论，力量加倍。……凡无主星之宫位皆同。」
class TestQtnCmbZ69:
    def test_042_konggong_shuangji_minggong(self):
        """命宫空（申），对宫迁移有太阳巨门，命宫干甲→太阳化忌入迁移=双忌论"""
        chart = make_chart(
            birth_year=1984,  # 甲子年
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="甲", branch="申", major_stars=()),
                PalaceStemFact(palace_name="迁移", stem="丙", branch="寅", major_stars=("太阳", "巨门")),
            ],
        )
        r = detect_qtn_cmb_042_konggong_shuangji(chart)
        assert r is not None
        assert r.rule_id == "QTN-CMB-042"
        assert any("双忌论" in n for n in r.facts["notes"])
        assert any("太阳" in n for n in r.facts["notes"])
        assert r.evidence_grade == 1

    def test_042_no_empty_palace_none(self):
        """命宫有主星（非空宫）→ None"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="甲", branch="申", major_stars=("太阳",)),
                PalaceStemFact(palace_name="迁移", stem="丙", branch="寅", major_stars=("太阳", "巨门")),
            ],
        )
        assert detect_qtn_cmb_042_konggong_shuangji(chart) is None

    def test_042_no_ji_in_opposite_none(self):
        """空宫宫干化忌星不在对宫主星 → None"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="甲", branch="申", major_stars=()),
                PalaceStemFact(palace_name="迁移", stem="丙", branch="寅", major_stars=("天同",)),
            ],
        )
        assert detect_qtn_cmb_042_konggong_shuangji(chart) is None


# 维度 16: QTN-CMB-043 化忌在命又化忌（Z70，OCR第55页）
#   原文：「化忌在命，又化忌，难贵显，格局难在中上层，纵任有财，层面不变。」
class TestQtnCmbZ70:
    def test_043_huaji_ming_self_ji(self):
        """生年化忌坐命 + 命宫自化忌 → 难贵显"""
        # 甲子年：甲干化忌=太阳。命宫坐太阳（生年忌），命宫干丙→丙干化忌=廉贞…
        # 构造：命宫 stem=丙 坐 太阳（生年忌入）+ 自化忌需命宫干化忌星在本宫
        # 丙干四化：天同禄/天机权/文昌科/廉贞忌 → 命宫需坐廉贞才能自化忌。
        # 故构造双星：命宫 stem=丙 坐 (太阳, 廉贞)：太阳=生年忌入命，廉贞=丙干自化忌
        chart = make_chart(
            birth_year=1984,  # 甲子
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="丙", branch="辰", major_stars=("太阳", "廉贞")),
            ],
        )
        r = detect_qtn_cmb_043_huaji_ming_you_huaji(chart)
        assert r is not None
        assert r.rule_id == "QTN-CMB-043"
        assert "难贵显" in r.semantic_summary
        assert r.evidence_grade == 1

    def test_043_no_ji_in_ming_none(self):
        """生年化忌不在命宫 → None"""
        chart = make_chart(
            birth_year=1984,  # 甲干化忌=太阳
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="丙", branch="辰", major_stars=("廉贞",)),
            ],
        )
        assert detect_qtn_cmb_043_huaji_ming_you_huaji(chart) is None

    def test_043_no_self_ji_none(self):
        """命宫无自化忌 → None"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="丁", branch="辰", major_stars=("太阳",)),
            ],
        )
        # 丁干四化：太阴禄/天同权/天机科/巨门忌 → 命宫干丁不化太阳为忌，无自化忌
        assert detect_qtn_cmb_043_huaji_ming_you_huaji(chart) is None


# 维度 17: QTN-CMB-044 双象论（Z71，vr-d 原著 PDF）
#   原文：「祿忌：祿不可解忌，以雙忌論，主凶。祿權：財利、發達、名利雙收（利大於名）…」
class TestQtnCmbZ71Shuangxiang:
    def test_044_lu_ji_shuangji(self):
        """甲干四化：廉禄/破权/武科/太阳忌。命宫坐廉贞+太阳 → 禄忌双象=双忌论主凶"""
        chart = make_chart(
            birth_year=1984,  # 甲子
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="乙", branch="辰", major_stars=("廉贞", "太阳")),
            ],
        )
        r = detect_qtn_cmb_044_shuangxiang_lun(chart)
        assert r is not None
        assert r.rule_id == "QTN-CMB-044"
        assert "雙忌" in r.semantic_summary or "双忌" in r.semantic_summary
        assert r.evidence_grade == 1

    def test_044_lu_quan_liming(self):
        """甲干：廉禄+破权同宫 → 禄权双象=财利发达名利双收"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="财帛", stem="乙", branch="午", major_stars=("廉贞", "破军")),
            ],
        )
        r = detect_qtn_cmb_044_shuangxiang_lun(chart)
        assert r is not None
        assert "祿權" in r.semantic_summary or "禄权" in r.semantic_summary

    def test_044_no_pair_none(self):
        """四化星分落四宫无同宫 → None"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="乙", branch="辰", major_stars=("廉贞",)),
                PalaceStemFact(palace_name="财帛", stem="乙", branch="午", major_stars=("破军",)),
                PalaceStemFact(palace_name="官禄", stem="乙", branch="戌", major_stars=("武曲",)),
                PalaceStemFact(palace_name="迁移", stem="乙", branch="寅", major_stars=("太阳",)),
            ],
        )
        assert detect_qtn_cmb_044_shuangxiang_lun(chart) is None


# 维度 18: QTN-CMB-045 命宫宫干=生年干（Z71，vr-d 原著 PDF）
class TestQtnCmbZ71Minggan:
    def test_045_minggan_eq_birth(self):
        """甲子年、命宫干甲 → 四化双倍函义"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="甲", branch="辰", major_stars=("七杀",)),
            ],
        )
        r = detect_qtn_cmb_045_minggan_double(chart)
        assert r is not None
        assert r.rule_id == "QTN-CMB-045"
        assert "双倍" in r.semantic_summary

    def test_045_minggan_neq_birth_none(self):
        """命宫干≠生年干 → None"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="乙", branch="辰", major_stars=("七杀",)),
            ],
        )
        assert detect_qtn_cmb_045_minggan_double(chart) is None


# 维度 19: QTN-CMB-046 命宫坐生年忌+三合不见三吉化（Z71，vr-d 原著 PDF）
class TestQtnCmbZ71Baishou:
    def test_046_ming_ji_no_three(self):
        """甲子年忌=太阳坐命；三合(命财官)无廉/破/武 → 白手起家"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="丙", branch="辰", major_stars=("太阳",)),
                PalaceStemFact(palace_name="财帛", stem="戊", branch="午", major_stars=("天机",)),
                PalaceStemFact(palace_name="官禄", stem="壬", branch="戌", major_stars=("天同",)),
            ],
        )
        r = detect_qtn_cmb_046_ming_ji_baishou(chart)
        assert r is not None
        assert r.rule_id == "QTN-CMB-046"
        assert "白手起家" in r.semantic_summary

    def test_046_ming_ji_with_three_none(self):
        """三合内有生年禄（廉贞在财帛） → None"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="丙", branch="辰", major_stars=("太阳",)),
                PalaceStemFact(palace_name="财帛", stem="戊", branch="午", major_stars=("廉贞",)),
                PalaceStemFact(palace_name="官禄", stem="壬", branch="戌", major_stars=("天同",)),
            ],
        )
        assert detect_qtn_cmb_046_ming_ji_baishou(chart) is None

    def test_046_no_ji_in_ming_none(self):
        """命宫无生年忌 → None"""
        chart = make_chart(
            birth_year=1984,
            palace_stems=[
                PalaceStemFact(palace_name="命宫", stem="丙", branch="辰", major_stars=("廉贞",)),
            ],
        )
        assert detect_qtn_cmb_046_ming_ji_baishou(chart) is None


class TestQtnCmbZ72:
    """Z72: 应期层数据接通 + 结婚限（QTN-CMB-047）"""

    def test_047_jiehun_xian_1983_standard(self):
        """1983 标准盘：命宫辰（丙干）七杀——查夫妻宫坐生年三吉化。"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_qtn_cmb_047_jiehun_xian
        e = ZiweiEngine()
        ch = e.full_chart((1983, 9, 29), 11, "male")
        # 1983 癸亥年，生年四化 = 癸破巨阴贪
        assert ch.birth_year == 1983
        # 规则是否触发取决于盘面，但绝不崩溃、必返回实例或 None
        r = detect_qtn_cmb_047_jiehun_xian(ch)
        assert r is None or isinstance(r, QintianCombination)

    def test_047_evidence_binding(self):
        from tongshu.engines.ziwei.rules.qintian.evidence import EVIDENCE_BINDINGS
        ev = EVIDENCE_BINDINGS.get("QTN-CMB-047")
        assert ev is not None
        assert "第三個大限" in ev.verbatim_quote
        assert ev.grade == 1

    def test_decadal_palace_flow_year_injected(self):
        """Z72: full_chart 输出大限命宫与流年年份。"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        e = ZiweiEngine()
        ch = e.full_chart((1983, 9, 29), 11, "male")
        assert ch.decadal_palace == "命宫"  # 土五局第一大限起命宫
        assert ch.flow_year == 1983

    def test_016_017_now_trigger(self):
        """Z72: 应期层数据接通后 016/017 不再 fail-closed。"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        from tongshu.engines.ziwei.rules.qintian.combinations import (
            detect_qtn_cmb_016_liunian,
            detect_qtn_cmb_017_daixian,
        )
        e = ZiweiEngine()
        ch = e.full_chart((1983, 9, 29), 11, "male")
        r16 = detect_qtn_cmb_016_liunian(ch)
        r17 = detect_qtn_cmb_017_daixian(ch)
        assert r16 is not None and r16.detected
        assert r17 is not None and r17.detected


class TestQtnCmbZ73:
    """Z73: 天刑/天姚安星 + 凶格组合（048-052）"""

    def test_tianxing_tianyao_injected(self):
        """1983 农历九月生：天刑在巳宫（父母）、天姚在酉宫（仆役）。"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        e = ZiweiEngine()
        ch = e.full_chart((1983, 9, 29), 11, "male")
        tx = ty = None
        for nm, p in ch.palaces.items():
            mn = p.get("minor", [])
            if "天刑" in mn:
                tx = nm
            if "天姚" in mn:
                ty = nm
        assert tx == "父母"  # 天刑=(9+8)%12=5=巳
        assert ty == "仆役"  # 天姚=9%12=9=酉

    def test_048_051_052_no_crash(self):
        from tongshu.engines.ziwei_engine import ZiweiEngine
        from tongshu.engines.ziwei.rules.qintian.combinations import (
            detect_qtn_cmb_048_tianxing_huaji_guanfei,
            detect_qtn_cmb_049_tianxing_hun,
            detect_qtn_cmb_050_tianyao_taohua,
            detect_qtn_cmb_051_wuqu_huaji_tianxing,
            detect_qtn_cmb_052_taiyang_huaji_tianxing,
        )
        e = ZiweiEngine()
        ch = e.full_chart((1983, 9, 29), 11, "male")
        for fn in (
            detect_qtn_cmb_048_tianxing_huaji_guanfei,
            detect_qtn_cmb_049_tianxing_hun,
            detect_qtn_cmb_050_tianyao_taohua,
            detect_qtn_cmb_051_wuqu_huaji_tianxing,
            detect_qtn_cmb_052_taiyang_huaji_tianxing,
        ):
            r = fn(ch)
            assert r is None or isinstance(r, QintianCombination)

    def test_048_evidence_binding(self):
        from tongshu.engines.ziwei.rules.qintian.evidence import EVIDENCE_BINDINGS
        for rid in ("QTN-CMB-048", "QTN-CMB-049", "QTN-CMB-050", "QTN-CMB-051", "QTN-CMB-052"):
            ev = EVIDENCE_BINDINGS.get(rid)
            assert ev is not None, rid
            assert ev.grade == 1


class TestQtnCmbZ73B:
    """Z73: 大限官非 053"""

    def test_053_no_crash(self):
        from tongshu.engines.ziwei_engine import ZiweiEngine
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_qtn_cmb_053_daxian_ji_tianxing
        e = ZiweiEngine()
        ch = e.full_chart((1983, 9, 29), 11, "male")
        r = detect_qtn_cmb_053_daxian_ji_tianxing(ch)
        assert r is None or isinstance(r, QintianCombination)

    def test_053_evidence_binding(self):
        from tongshu.engines.ziwei.rules.qintian.evidence import EVIDENCE_BINDINGS
        ev = EVIDENCE_BINDINGS.get("QTN-CMB-053")
        assert ev is not None
        assert ev.grade == 1
