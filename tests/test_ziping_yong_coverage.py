"""子平用神覆盖率锚点：原典 21 案回放（PZZQ 沈孝瞻断语为真值）。

V7.182 起，格用神按八格原典判据派生（透干十神 + 藏干计数），
用神覆盖率由 2/12 提升到 11/12；本测试把该数字固化为护栏，
并逐案锁定原典明文可裁的用神五行，防止回退。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from engines.production_entry import FrozenCanonicalBaziChart, production_entry

REPO = Path(__file__).resolve().parent.parent

CASES = [
    (["癸未", "辛酉", "甲申", "丙寅"], "火"),  # 官多同煞，以丙火制官
    (["丁卯", "丙午", "丙子", "壬辰"], "水"),  # 煞刃格以煞制刃
    (["乙酉", "甲申", "丁巳", "庚戌"], "金"),  # 以庚劈甲引丁
    (["辛酉", "丙申", "庚子", "丙戌"], "火"),  # 煞刃格合一留一
    (["丙子", "壬辰", "壬申", "乙巳"], "木"),  # 乙木余气透干泄秀
    (["戊辰", "甲寅", "丁卯", "己酉"], "金"),  # 印旺取财损印
    (["辛卯", "丁酉", "庚午", "丙子"], "火"),  # 丁火制辛
    (["癸巳", "丁巳", "丁卯", "丙午"], "水"),  # 取年上癸水抑制
    (["己卯", "丁丑", "癸丑", "乙卯"], "木"),  # 食神制煞
    (["壬寅", "戊申", "丙寅", "癸巳"], "水"),  # 合官留煞
    (["甲子", "丁卯", "己亥", "戊辰"], "火"),  # 以印化官(杨增新) V7.191 扩案
    (["戊戌", "甲子", "己巳", "戊辰"], "木"),  # 用官制劫护财 V7.191 扩案
    (["戊寅", "己未", "甲寅", "乙亥"], "土"),  # 甲用己财(日主合财) V7.191 扩案
    (["庚午", "乙酉", "甲子", "乙亥"], "金"),  # 合煞留官(高太尉) V7.191 扩案
    (["庚申", "乙酉", "癸未", "乙卯"], "木"),  # 印格用食(朱家宝) V7.201 扩案
    (["癸巳", "壬戌", "乙巳", "戊寅"], "水"),  # 财局可以用印(朱有卿) V7.203 扩案
    (["癸酉", "癸亥", "戊子", "丁巳"], "火"),  # 争合用禄比, 时逢归禄(王某) V7.203 扩案
    (["丁卯", "癸丑", "丙申", "戊子"], "火"),  # 水旺火弱用劫帮身(蔡孑民) V7.204 扩案
    (["己酉", "丙子", "戊辰", "癸亥"], "火"),  # 佩印×财专向->用印(L531 丙火调候) V7.205 扩案
]


def _medicine(pillars):
    pl = {pos: [p[0], p[1]] for pos, p in zip(("year", "month", "day", "hour"), pillars)}
    result = production_entry(FrozenCanonicalBaziChart(pillars=pl))
    return ((result.get("zhenglun") or {}).get("yongyao") or {})


@pytest.mark.parametrize("pillars,expected_wuxing", CASES)
def test_yong_wuxing_matches_classic_case(pillars, expected_wuxing):
    yy = _medicine(pillars)
    pm = yy.get("primary_medicine") or {}
    assert pm.get("wuxing") == expected_wuxing


def test_qisha_jiuying_baizhongyoucheng_tan_yankai():
    """V7.199 救应篇明文(PZZQ L1210/L1212 谭延闿案亲证): 食神制煞而中隔以财,
    「财逢煞而食神制煞以生, 有救应, 即是败中有成, 为贵也」——V7.198 曾因
    tier<2 不满足 .007 成句落 NOT_EVALUABLE 断用神链路(NE 被 _usable_ge_cheng
    拒绝); 现按救应通道判 CZP, 用神=食神(木)恢复。"""
    pl = {pos: [s, b] for pos, (s, b) in zip(
        ("year", "month", "day", "hour"),
        (("己", "卯"), ("丁", "丑"), ("癸", "丑"), ("乙", "卯")))}
    result = production_entry(FrozenCanonicalBaziChart(pillars=pl))
    gc = (result.get("engine_result") or {}).get("ge_cheng") or {}
    assert gc.get("ge") == "七煞格(败中有成)", gc
    assert gc.get("cheng_bai") == "CHENG_ZHONG_YOU_PO", gc
    assert "败中有成" in (gc.get("rule") or "")
    yy = (result.get("zhenglun") or {}).get("yongyao") or {}
    pm = yy.get("primary_medicine") or {}
    assert pm.get("wuxing") == "木", pm


def test_yinzhong_liangshuo_discriminator_preserves_cai_side():
    """V7.201 印重两说判别式护栏: 制药(财)透干或本气根在→用财损印不变;
    财不透无本气根而食伤透/本气根在→泄升主(朱家宝 L543/L1146)。
    pzzq-007 财坐酉本气根 → 用金(财)不受泄边影响。"""
    yy = _medicine(["戊辰", "甲寅", "丁卯", "己酉"])
    pm = yy.get("primary_medicine") or {}
    assert pm.get("wuxing") == "金", pm
    edges = yy.get("all_edges") or []
    jin = [e for e in edges if e.get("wuxing") == "金"]
    assert jin and jin[0].get("accepted"), edges


def test_wuhe_span_state_three_states():
    """V7.203 五合终裁三态(PZZQ L476-496): 紧贴作合/间干克其配偶=制于势不敢合(L481)/
    遥隔得禄刃于月令仍合(L495 张耀曾 庚禄在申, 反证朱有卿 戊墓在戌 L486)。"""
    from engines.common.yongyao_resolve import _wuhe_span_state

    def F(*ps):
        return {'pillars': {p: list(q) for p, q in zip(
            ("year", "month", "day", "hour"), ps)}}

    assert _wuhe_span_state(
        F(("甲", "子"), ("己", "丑"), ("丙", "寅"), ("庚", "卯")), "甲", "己")[0] == "adjacent"
    assert _wuhe_span_state(
        F(("甲", "子"), ("庚", "丑"), ("己", "寅"), ("丙", "卯")), "甲", "己")[0] == "blocked"
    assert _wuhe_span_state(
        F(("甲", "子"), ("丙", "丑"), ("己", "寅"), ("丙", "卯")), "甲", "己")[0] == "adjacent"
    assert _wuhe_span_state(
        F(("乙", "酉"), ("甲", "申"), ("丁", "巳"), ("庚", "戌")), "乙", "庚")[0] == "remote_he"
    assert _wuhe_span_state(
        F(("癸", "巳"), ("壬", "戌"), ("乙", "巳"), ("戊", "寅")), "癸", "戊")[0] == "remote_no"


def test_peiyin_cai_special_toward_still_uses_yin():
    """V7.205 佩印×财专向并存→用神归印(PZZQ L530-531: 戊癸相合仅致「日主之情向财
    不向印」=用神之情不专之瑕 L533, 用神仍是丙火印; L3341 孤财不贵佩印帮身即印取贵);
    印被财合去之佩印仍用财(张耀曾 004 V7.203 终裁); 非佩印财专向仍用财(015)。"""
    from engines.production_entry import FrozenCanonicalBaziChart, production_entry

    def _got(pillars):
        pl = {pos: [p[0], p[1]] for pos, p in zip(
            ("year", "month", "day", "hour"), pillars)}
        result = production_entry(FrozenCanonicalBaziChart(pillars=pl))
        yy = ((result.get("zhenglun") or {}).get("yongyao") or {})
        return ((yy.get("primary_medicine") or {}).get("wuxing") or "")

    assert _got(["己酉", "丙子", "戊辰", "癸亥"]) == "火"   # 021 佩印+戊癸合->印
    assert _got(["戊寅", "己未", "甲寅", "乙亥"]) == "土"   # 015 非佩印专向->财
    assert _got(["乙酉", "甲申", "丁巳", "庚戌"]) == "金"   # 004 印被合去->财


def test_yin_cong_tonggen_month_still_cong_wu_tingfang():
    """V7.207 阴干从势通道(徐注 L182「己土虽通根月令, 而见木之势盛, 即从木」):
    018 伍廷芳造 壬寅丁未己卯乙亥——阴干+势盛(亥卯未三合木局)+印透被财合去
    (丁月印↔壬年财 span=1 adjacent) → 从杀格 CONFIRMED + ge=从格(从杀格)/CHENG;
    禄劫 NE 占位让位从格兜底(V7.207 消费门, 特格优先于禄劫名)。"""
    from engines.production_entry import FrozenCanonicalBaziChart, production_entry

    pl = {"year": ["壬", "寅"], "month": ["丁", "未"],
          "day": ["己", "卯"], "hour": ["乙", "亥"]}
    result = production_entry(FrozenCanonicalBaziChart(pillars=pl))
    sp = result.get("engine_result", {}).get("special") or {}
    gc = result.get("engine_result", {}).get("ge_cheng") or {}
    assert sp.get("cong_type") == "从杀格" and sp.get("cong_state") == "CONFIRMED"
    assert gc.get("ge") == "从格(从杀格)" and gc.get("cheng_bai") == "CHENG"


def test_yin_cong_yin_tou_not_he_keeps_zhengge():
    """V7.207b 印通道 span 终裁护栏(PZZQ L476-496; V7.203 _wuhe_span_state 复用):
    印透未被财合去(阎锡山 癸年印无戊配/遥隔 remote_no 朱有卿式) → 不从, 正格保持;
    PZZQ L183 阎锡山「印通根不怕身弱, 煞透有制贵格」/L184 许世英「十九误作从煞」。"""
    from engines.production_entry import FrozenCanonicalBaziChart, production_entry

    def _ge(pillars):
        pl = {pos: [p[0], p[1]] for pos, p in zip(
            ("year", "month", "day", "hour"), pillars)}
        result = production_entry(FrozenCanonicalBaziChart(pillars=pl))
        sp = result.get("engine_result", {}).get("special") or {}
        gc = result.get("engine_result", {}).get("ge_cheng") or {}
        return sp.get("cong_type"), gc.get("ge")

    ct, ge = _ge(["癸未", "辛酉", "乙酉", "丁亥"])   # 阎锡山: 印透未合->不从
    assert ct is None and ge == "七煞格"
    ct, ge = _ge(["癸酉", "辛酉", "乙丑", "辛巳"])   # 许世英: 印透未合->不从
    assert ct is None and ge == "七煞格"


def test_yong_coverage_at_least_10_of_12():
    """原典 21 案（含 6 案已知口径冲突/配合分歧）整体覆盖率护栏。"""
    spec = importlib.util.spec_from_file_location(
        "ziping_pzzq_replay", REPO / "scripts" / "ziping_pzzq_replay.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.run(verbose=False) >= 20
