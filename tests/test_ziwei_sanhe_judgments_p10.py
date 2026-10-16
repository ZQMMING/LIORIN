# -*- coding: utf-8 -*-
"""Z74: 南派断语层测试（SANHE-JUDG 星曜论）"""

import sys

sys.path.insert(0, r"D:\shuntian-ziwei-v2\src")

import pytest

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.method_graphs import SanheRuleGraph
from tongshu.engines.ziwei.rules.sanhe_judgments import STAR_JUDGMENTS, JUDG_RULE_PREFIX


@pytest.fixture(scope="module")
def engine():
    return ZiweiEngine()


def _sanhe_matches(engine, chart):
    return SanheRuleGraph().match_all(chart)


class TestSanheJudgmentsZ74:
    """南派坐命断语层——《紫微斗数全书》星曜论原文级。"""

    def test_judgment_table_full_14_stars(self):
        """14 主星断语表齐全（紫微/天机/太阳/武曲/天同/廉贞/天府/太阴/贪狼/巨门/天相/天梁/七杀/破军）。"""
        stars = ["紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府",
                 "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"]
        assert set(STAR_JUDGMENTS.keys()) == set(stars)
        for st in stars:
            j = STAR_JUDGMENTS[st]
            assert j["verbatim"], f"{st} 缺原文"
            assert j["character"] and j["fortune"] and j["trend"], f"{st} 断语不完整"

    def test_1983_qisha_ming_palace_judgment(self, engine):
        """1983 标准盘命宫七杀 → 断语层输出 SANHE-JUDG-七杀。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male")
        r = _sanhe_matches(engine, ch)
        judgs = [m for m in r.matched_rules
                 if m.rule_spec.rule_id == f"{JUDG_RULE_PREFIX}-七杀"]
        assert len(judgs) == 1
        j = judgs[0]
        assert j.rule_spec.operation["action"] == "output_judgment"
        assert "坐命" in j.rule_spec.operation["description"]
        assert "威猛刚烈" in j.rule_spec.operation["description"]  # 七杀断语
        assert j.rule_spec.evidence_refs[0].source_work == "紫微斗数全书"

    def test_sitting_vs_sanfang_separated(self, engine):
        """坐命/三方会照分离：1983 盘七杀朝斗=坐命，其余同宫格=三方会照。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male")
        r = _sanhe_matches(engine, ch)
        sits = [m for m in r.matched_rules if m.facts.get("scope") == "坐命"]
        huiz = [m for m in r.matched_rules if m.facts.get("scope") == "三方会照"]
        assert any("七杀朝斗" in m.rule_spec.rule_id for m in sits)
        assert len(huiz) > 0
        # 坐命格局的星必须真在命宫
        ming = ch.palaces["命宫"].get("major", [])
        for m in sits:
            required = set(m.rule_spec.condition.get("stars", []))
            assert required <= set(ming), f"{m.rule_spec.rule_id} 报坐命但星不在命宫"

    def test_mangpai_case42_taiyin_fortune(self, engine):
        """#42 亿万富翁：太阴坐命 → 化富主田宅财断语（富格）。"""
        ch = engine.full_chart((1947, 12, 25), 18, "male")  # 1948-2-4 酉时 → 农历1947-12-25（丁亥 癸丑 己未 癸酉）
        r = _sanhe_matches(engine, ch)
        judgs = [m for m in r.matched_rules if "太阴" in m.rule_spec.rule_id and "JUDG" in m.rule_spec.rule_id]
        assert len(judgs) == 1
        assert "化富" in judgs[0].rule_spec.operation["description"]

    def test_mangpai_case9_jumen_marriage(self, engine):
        """#9 三嫁女：巨门坐命 → 婚姻隔角断语。"""
        ch = engine.full_chart((1906, 1, 4), 20, "female")  # 1906-1-28 戌时 → 农历1906-1-4（乙巳 己丑 壬申 庚戌）
        r = _sanhe_matches(engine, ch)
        judgs = [m for m in r.matched_rules if "巨门" in m.rule_spec.rule_id and "JUDG" in m.rule_spec.rule_id]
        assert len(judgs) == 1
        assert "隔角" in judgs[0].rule_spec.operation["description"]
        assert "生离死别" in judgs[0].rule_spec.operation["description"]

    # ---------- Z74b 格局断语层 ----------

    def test_pattern_judgments_full_coverage(self):
        """41 个格局的星组全部有断语条目（PATTERN_JUDGMENTS 全覆盖，fail-closed 反查）。"""
        from tongshu.engines.ziwei.rules.rule_graph import PATTERN_DEFS
        from tongshu.engines.ziwei.rules.sanhe_pattern_judgments import PATTERN_JUDGMENTS, _PATTERN_INDEX
        seen = set()
        for name, stars, desc in PATTERN_DEFS:
            key = frozenset(stars)
            seen.add(key)
            assert key in _PATTERN_INDEX, f"{name} {stars} 无格局断语"
        # 表条目 status 合法
        for k, v in PATTERN_JUDGMENTS.items():
            assert v["status"] in ("canonical", "candidate"), f"{v['name']} status 非法"
            assert v["verbatim"] and v["judgment"] and v["trend"], f"{v['name']} 断语不完整"

    def test_1983_qisha_pattern_judgment(self, engine):
        """1983 盘七杀朝斗坐命 → 格局断语（canonical，威猛刚烈）。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male")
        r = _sanhe_matches(engine, ch)
        pats = [m for m in r.matched_rules
                if "PATTERN" in m.rule_spec.rule_id and m.facts.get("scope") == "坐命"]
        assert len(pats) == 1
        pj = pats[0].facts["pattern_judgment"]
        assert pj["status"] == "canonical"
        assert "威猛刚烈" in pj["judgment"]

    def test_case14_wupo_xingming_judgment(self, engine):
        """#14 黑社会：武破同宫格局断语 → 刑名之权（原文级）。"""
        ch = engine.full_chart((1972, 10, 20), 12, "male")  # 壬子 己酉 辛酉 己丑
        r = _sanhe_matches(engine, ch)
        wupo = [m for m in r.matched_rules
                if "武破" in m.rule_spec.rule_id and m.facts.get("scope") == "坐命"]
        assert len(wupo) == 1
        pj = wupo[0].facts["pattern_judgment"]
        assert pj["status"] == "canonical"
        assert "刑名" in pj["judgment"]
        assert pj["verbatim"].startswith("擎羊陀罗火铃星武曲破军")

    def test_case26_liantan_e_ge(self, engine):
        """#26 林彪：廉贪同宫恶格断语（全书'贪狼廉贞破军恶'原文）。"""
        ch = engine.full_chart((1907, 1, 15), 18, "male")  # 丁未 辛亥 戊子 庚申
        r = _sanhe_matches(engine, ch)
        lt = [m for m in r.matched_rules if "廉贪" in m.rule_spec.rule_id]
        assert len(lt) == 1
        pj = lt[0].facts["pattern_judgment"]
        assert "恶" in pj["verbatim"] or "恶" in pj["judgment"]
        assert pj["status"] == "canonical"
