# -*- coding: utf-8 -*-
"""L2.5 12 主题聚合层（THEME-OUTPUT-001~012）契约测试。

验收标准：12 主题齐全、状态枚举合法、数据源非空、1980 案例关键主题与
L1e/L2 事实一致（全布尔，禁评分）。
"""
import pytest

from src.tongshu.engines.bazi_engine import BaziEngine
from src.tongshu.engines.blind_bazi_engine import BlindBaziEngine
from src.tongshu.engines.blind_yingqi import BlindYingqiEngine
from src.tongshu.engines.blind_judgment import BlindJudgmentEngine
from src.tongshu.engines.blind_themes import BlindThemeEngine, THEME_DEFS

VALID_STATES = {"ESTABLISHED", "CANDIDATE", "UNDETERMINED", "NOT_APPLICABLE"}

CASE_1980 = (1980, 6, 22, 10)  # 庚申 壬午 丙寅 癸巳 男


@pytest.fixture(scope="module")
def theme_result():
    be = BaziEngine()
    bb = BlindBaziEngine(be)
    by = BlindYingqiEngine(be)
    jd = BlindJudgmentEngine()
    th = BlindThemeEngine()
    ch = be.compute(CASE_1980, gender="male")
    br = bb.compute(CASE_1980, gender="male")
    yr = by.analyze(CASE_1980, gender="male", target_age=46)
    jr = jd.judge(ch, br, yr)
    return th.aggregate(ch, br, yr, jr).to_dict()


class TestThemeContract:
    def test_12_themes_present(self, theme_result):
        ids = [t["theme_id"] for t in theme_result["themes"]]
        assert len(ids) == 12
        assert set(ids) == {tid for tid, _, _ in THEME_DEFS}

    def test_states_in_whitelist(self, theme_result):
        for t in theme_result["themes"]:
            assert t["state"] in VALID_STATES, f"{t['theme_id']}: {t['state']}"

    def test_entries_non_empty(self, theme_result):
        for t in theme_result["themes"]:
            assert t["entries"], f"{t['theme_id']}: entries 为空"
            for e in t["entries"]:
                assert e["source"] and e["value"], f"{t['theme_id']}: 空条目"

    def test_rule_ids_present(self, theme_result):
        for t in theme_result["themes"]:
            assert t["rule_ids"], f"{t['theme_id']}: rule_ids 为空"

    def test_method_scope(self, theme_result):
        assert theme_result["method_scope"] == "DUAN_JIANYE"


class TestTheme1980Facts:
    def test_marriage_broken(self, theme_result):
        t = next(x for x in theme_result["themes"] if x["theme_id"] == "THEME-003")
        assert t["state"] == "ESTABLISHED"
        v = next(e["value"] for e in t["entries"] if e["source"].endswith("marriage_state"))
        assert v == "BROKEN"

    def test_wealth_directed_established(self, theme_result):
        t = next(x for x in theme_result["themes"] if x["theme_id"] == "THEME-005")
        v = next(e["value"] for e in t["entries"] if e["source"].endswith("wealth_state"))
        # ㊻s128 口径修正后为 DIRECTED_PARTIAL：本盘主位丙(日主之根, 寅中藏丙)制庚偏财
        # 由"比劫夺财 NEGATIVE"改判"身制财求财 NEUTRAL"(非他字比劫克财, 原书只认他字),
        # 夺财风险消除(robbed=False)；但工作效能 SMALL(禄神受穿 NEGATIVE 压档) → 取财
        # 有功而层次不高, 按 wealth 分支落 PARTIAL。旧值 DIRECTED_AND_ESTABLISHED 是
        # V3.4.2 引擎自身 dump(非原书), 不再作为自证基准。
        assert v == "DIRECTED_PARTIAL"

    def test_official_controlled_clean(self, theme_result):
        t = next(x for x in theme_result["themes"] if x["theme_id"] == "THEME-008")
        v = next(e["value"] for e in t["entries"] if e["source"].endswith("official_state"))
        assert v == "CONTROLLED_AND_CLEAN"

    def test_children_rule_male_with_cai(self, theme_result):
        # 男命有财(庚偏财透干)→官杀为子女星（段建业口诀）
        t = next(x for x in theme_result["themes"] if x["theme_id"] == "THEME-004")
        star = next(e["value"] for e in t["entries"] if e["source"].endswith("star"))
        assert "官杀为子女星" in star

    def test_yima_present(self, theme_result):
        # 年支申→马在寅（日支寅）→驿马成立
        t = next(x for x in theme_result["themes"] if x["theme_id"] == "THEME-007")
        v = next(e["value"] for e in t["entries"] if e["source"].endswith("present"))
        assert v != "NONE"

    def test_fude_shishen_yin(self, theme_result):
        t = next(x for x in theme_result["themes"] if x["theme_id"] == "THEME-010")
        assert t["state"] in ("ESTABLISHED", "CANDIDATE")

    def test_talent_learning(self, theme_result):
        t = next(x for x in theme_result["themes"] if x["theme_id"] == "THEME-012")
        assert t["state"] in ("ESTABLISHED", "CANDIDATE")

    def test_parents_present(self, theme_result):
        t = next(x for x in theme_result["themes"] if x["theme_id"] == "THEME-011")
        father = next(e["value"] for e in t["entries"] if "father" in e["source"])
        mother = next(e["value"] for e in t["entries"] if "mother" in e["source"])
        assert father == "PRESENT" and mother == "PRESENT"
