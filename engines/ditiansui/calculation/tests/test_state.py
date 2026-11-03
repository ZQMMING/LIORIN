"""DTS 基础态势派生测试（Phase 6 §65 ·《滴天髓》001-009/018-019）。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.common.facts_builder import FactsBuilder  # noqa: E402
from engines.ditiansui.calculation.state import derive_state  # noqa: E402


def build(chart):
    return FactsBuilder(engine="dts").build(chart)


def vals(res, field):
    return {f["value"] for f in res.facts.basic_structure_facts if f["field"] == field}


BASE = {
    "canonical_input": {"ref": "t", "hash": "x" * 12},
    "gender": "男", "xunkong": {"xun": "甲午旬"},
    "shishen": {}, "changsheng": {}, "nayin": {}, "hidden_stems": {},
    "relations": {},
}


def chart(pillars, relations=None, hidden_stems=None):
    c = dict(BASE)
    c["pillars"] = pillars
    c["relations"] = relations or {}
    if hidden_stems is not None:
        c["hidden_stems"] = hidden_stems
    return c


def test_derive_state_stem():
    out = derive_state(day_stem="丙", month_branch="寅")
    assert out["stem"] == "丙" and out["stem_yinyang"] == "陽"
    out2 = derive_state(day_stem="癸", month_branch="卯")
    assert out2["stem_yinyang"] == "陰"
    assert derive_state(day_stem="甲", month_branch="寅")["branch_yinyang"] == "陽"


def test_dts_001_002_yinyang_extremity():
    """丙→陽之至；癸→陰之至（《滴天髓·天干》）"""
    res = build(chart({
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "丙", "branch": "申"},
        "hour": {"stem": "庚", "branch": "寅"},
    }))
    assert "陽之至" in vals(res, "stem_yang_extremity")
    res2 = build(chart({
        "year": {"stem": "壬", "branch": "申"},
        "month": {"stem": "癸", "branch": "亥"},
        "day": {"stem": "癸", "branch": "卯"},
        "hour": {"stem": "乙", "branch": "未"},
    }))
    assert "陰之至" in vals(res2, "stem_yin_extremity")


def test_dts_003_004_stem_behavior():
    """阳干從氣不從勢；阴干從勢（《滴天髓·天干》）"""
    res = build(chart({
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "甲", "branch": "申"},
        "hour": {"stem": "庚", "branch": "寅"},
    }))
    assert "從氣不從勢" in vals(res, "stem_behavior")
    res2 = build(chart({
        "year": {"stem": "壬", "branch": "申"},
        "month": {"stem": "癸", "branch": "亥"},
        "day": {"stem": "乙", "branch": "卯"},
        "hour": {"stem": "辛", "branch": "未"},
    }))
    assert "從勢" in vals(res2, "stem_behavior")


def test_dts_005_006_branch_behavior():
    """阳支動強速達；阴支靜專否泰（《滴天髓·地支》；口径：月支）"""
    res = build(chart({
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "甲", "branch": "申"},
        "hour": {"stem": "庚", "branch": "寅"},
    }))
    assert "動強速達" in vals(res, "branch_behavior")
    res2 = build(chart({
        "year": {"stem": "壬", "branch": "申"},
        "month": {"stem": "癸", "branch": "卯"},
        "day": {"stem": "癸", "branch": "亥"},
        "hour": {"stem": "乙", "branch": "未"},
    }))
    assert "靜專否泰經年" in vals(res2, "branch_behavior")


def test_dts_007_shengsheng_ji_chong():
    """寅申巳亥生方 + 沖 → 生方忌沖動（《滴天髓·地支》）。

    注：CAND-DTS-007 为 suppress 规则（RuleEngine 只消费 emit），此处验证
    前置字段注入（relation=沖）正确 + suppress 规则被正确忽略（不产 fact）。
    """
    chart_ = chart({
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "甲", "branch": "申"},
        "hour": {"stem": "庚", "branch": "子"},
    }, relations={"liu_chong": ["寅申"]})
    res = build(chart_)
    assert res.metadata["view"]["relation"] == "沖"
    # suppress 不产 fact（预期行为；suppress 语义待审批裁决）
    assert "生方忌沖動" not in vals(res, "branch_phase")


def test_dts_008_ku_chong_kai():
    """辰戌丑未墓库 → 庫宜沖則開（《滴天髓·地支》）"""
    res = build(chart({
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "丙", "branch": "辰"},
        "day": {"stem": "甲", "branch": "申"},
        "hour": {"stem": "庚", "branch": "戌"},
    }))
    assert "庫宜沖則開" in vals(res, "branch_phase")


def test_dts_009_relation_weight():
    """沖 → 关系权重重"""
    res = build(chart({
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "甲", "branch": "申"},
        "hour": {"stem": "庚", "branch": "子"},
    }, relations={"liu_chong": ["寅申"]}))
    assert "重" in vals(res, "relation_weight")


def test_dts_018_019_pillar_nature():
    """甲申/戊寅 殺印相生；癸丑/庚寅 坐兩神興旺（《滴天髓·干支总论》）"""
    res = build(chart({
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "甲", "branch": "申"},
        "hour": {"stem": "庚", "branch": "寅"},
    }))
    assert "殺印相生" in vals(res, "pillar_nature")
    res2 = build(chart({
        "year": {"stem": "壬", "branch": "申"},
        "month": {"stem": "癸", "branch": "亥"},
        "day": {"stem": "癸", "branch": "丑"},
        "hour": {"stem": "乙", "branch": "未"},
    }))
    assert "坐兩神興旺" in vals(res2, "pillar_nature")


def test_dts_012_tian_quan_yiqi():
    """天全一氣 注入（《滴天髓·干支总论》DTS-010-004）。

    注：CAND-DTS-012 为 require 规则（RuleEngine 只消费 emit），facts 不产出；
    require 语义（莫之載為逆 警示）供上层 judgment 消费，V2.22 未定义消费机制，
    已记录待审批裁决。此处验证派生字段注入正确。
    """
    # 四天干全木（甲/乙 同木）：甲子 乙丑 甲寅 乙卯
    res = build(chart({
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "乙", "branch": "丑"},
        "day": {"stem": "甲", "branch": "寅"},
        "hour": {"stem": "乙", "branch": "卯"},
    }))
    assert res.metadata["view"]["pending"]["tian_status"] == "全一氣"
    assert "莫之載為逆" not in vals(res, "di_de")


def test_dts_013_di_quan_sanwu():
    """地全三物 注入（《滴天髓·干支总论》DTS-010-006/007 注：寅卯辰、亥卯未）。

    注：CAND-DTS-013 为 require 规则，facts 不产出；同上记录待审批。
    """
    # 地支含 寅卯辰（三会东方木）
    res = build(chart({
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "丙", "branch": "卯"},
        "day": {"stem": "甲", "branch": "辰"},
        "hour": {"stem": "庚", "branch": "午"},
    }))
    assert res.metadata["view"]["pending"]["di_status"] == "全三物"
    assert "莫之容為逆" not in vals(res, "tian_dao")


def test_dts_014_015_stem_position():
    """陽乘陽位→陽者昌；陰乘陰位→陰氣盛（《滴天髓·干支总论》DTS-010-008/010）"""
    # 甲（阳）坐 午（阳）
    res = build(chart({
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "甲", "branch": "午"},
        "hour": {"stem": "庚", "branch": "寅"},
    }))
    assert res.metadata["view"]["pending"]["stem_position"] == "陽乘陽位"
    # 癸（阴）坐 丑（阴）
    res2 = build(chart({
        "year": {"stem": "壬", "branch": "申"},
        "month": {"stem": "癸", "branch": "亥"},
        "day": {"stem": "癸", "branch": "丑"},
        "hour": {"stem": "乙", "branch": "未"},
    }))
    assert res2.metadata["view"]["pending"]["stem_position"] == "陰乘陰位"


def test_dts_023_024_xing_state():
    """形全→損其有餘；形缺→補其不足（《滴天髓·形象论》DTS-011-008）。"""
    # 形全盘：四柱干支覆盖全五行（甲寅木 丙午火 庚申金 戊子水土）
    res = build(chart({
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "庚", "branch": "申"},
        "hour": {"stem": "戊", "branch": "子"},
    }))
    assert "損其有餘" in vals(res, "yi")
    # 形缺盘：缺土（甲寅木 丙午火 庚申金 壬子水）
    res2 = build(chart({
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "庚", "branch": "申"},
        "hour": {"stem": "壬", "branch": "子"},
    }))
    assert "補其不足" in vals(res2, "yi")


def test_dts_020_liangqi_chengxiang():
    """兩氣合而成象 → 象不可破（《滴天髓·形象论》DTS-011-001/002）。

    注：天干属一行（木）、地支属一行（火），木火相生，其象属一。
    """
    # 干全木（甲乙甲乙）+ 支全火（午巳午巳）→ 木生火 → 兩氣合而成象
    res = build(chart({
        "year": {"stem": "甲", "branch": "午"},
        "month": {"stem": "乙", "branch": "巳"},
        "day": {"stem": "甲", "branch": "午"},
        "hour": {"stem": "乙", "branch": "巳"},
    }))
    assert res.metadata["view"]["pending"]["pattern"] == "兩氣合而成象"
    # 反例：干木 + 支火 + 透金干（庚）→ 非全一行 → 不成象
    res2 = build(chart({
        "year": {"stem": "甲", "branch": "午"},
        "month": {"stem": "乙", "branch": "巳"},
        "day": {"stem": "甲", "branch": "午"},
        "hour": {"stem": "庚", "branch": "巳"},
    }))
    assert res2.metadata["view"].get("pending", {}).get("pattern") != "兩氣合而成象"


def test_dts_051_052_zhan():
    """天戰猶自可；地戰急如火（《滴天髓·战局》DTS-046-001/002 注）。"""
    # 天戰：干头甲乙（木）+ 庚辛（金）
    res = build(chart({
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "庚", "branch": "午"},
        "day": {"stem": "甲", "branch": "申"},
        "hour": {"stem": "辛", "branch": "寅"},
    }))
    assert res.metadata["view"]["pending"]["zhan_state"] == "天戰"
    # 地戰：地支寅申并存（干头无甲乙庚辛混战）
    res2 = build(chart({
        "year": {"stem": "丙", "branch": "寅"},
        "month": {"stem": "戊", "branch": "午"},
        "day": {"stem": "壬", "branch": "申"},
        "hour": {"stem": "庚", "branch": "子"},
    }))
    assert res2.metadata["view"]["pending"]["zhan_state"] == "地戰"


def test_dts_053_056_xiang():
    """君亢/臣過/母旺子孤/子衆母衰（《滴天髓》君象/臣象/母象/子象篇注）。"""
    # 君亢：甲乙日主满盘木（6），土（财）一二 → 損上以益下
    res = build(chart({
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "乙", "branch": "卯"},
        "day": {"stem": "甲", "branch": "辰"},
        "hour": {"stem": "乙", "branch": "未"},
    }))
    assert res.metadata["view"]["pending"]["xiang_state"] == "君亢"
    # 臣過：甲乙日主满盘木（5），金（官）一二、无财土 → 損下以益上
    res2 = build(chart({
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "乙", "branch": "卯"},
        "day": {"stem": "甲", "branch": "申"},
        "hour": {"stem": "辛", "branch": "巳"},
    }))
    assert res2.metadata["view"]["pending"]["xiang_state"] == "臣過"
    # 母旺子孤：甲乙日主满盘木（6），火（食伤）一二、无财土 → 多方生子孫
    res3 = build(chart({
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "乙", "branch": "卯"},
        "day": {"stem": "甲", "branch": "午"},
        "hour": {"stem": "乙", "branch": "巳"},
    }))
    assert res3.metadata["view"]["pending"]["xiang_state"] == "母旺子孤"
    # 子衆母衰：甲乙日主满盘木（5），水（印）多（3）→ 多方安母
    res4 = build(chart({
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "癸", "branch": "亥"},
        "day": {"stem": "甲", "branch": "寅"},
        "hour": {"stem": "乙", "branch": "卯"},
    }))
    assert res4.metadata["view"]["pending"]["xiang_state"] == "子衆母衰"


def test_dts_021_022_duxang_quanxiang():
    """獨象喜行化地；全象喜行財地（《滴天髓·形象論》DTS-011-004/006 注）。
    [PENDING_VERIFY] 量化阈值（獨象≥6/全象恰三行且主≥3）为暂定口径，待多源验证。"""
    # 獨象：甲乙日主 8 字木 6（曲直炎上之類）
    res = build(chart({
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "乙", "branch": "卯"},
        "day": {"stem": "甲", "branch": "辰"},
        "hour": {"stem": "乙", "branch": "未"},
    }))
    assert res.metadata["view"]["pending"]["pattern"] == "獨象"
    # 规则 CAND-DTS-021/022 依赖 pattern（PENDING 隔离）→ 不再断言规则输出；pattern 派生值已断言
    # 全象：主（木）3 + 食伤（火）2 + 财（土）3，恰三行
    res2 = build(chart({
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "甲", "branch": "辰"},
        "hour": {"stem": "己", "branch": "未"},
    }))
    assert res2.metadata["view"]["pending"]["pattern"] == "全象"


def test_dts_strength_min():
    """strength 最小可用版（Human 裁决 2026-09-16）：日主旺/衰/均衡 + 喜用方向。
    清浊（029/086/087）依赖 strength，本字段为清浊挂载最低门槛。
    [PENDING_VERIFY] 得令/得地（本气）/得势布尔组合近似；藏干权重与制化维度待迭代。"""
    # 身旺：甲日得令（月支寅木）∧得地（寅/卯藏干本气木）∧得势（年干甲比劫）→ WANG
    # 喜用＝财土/官杀金/食伤火
    res = build(chart({
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "丙", "branch": "寅"},
        "day": {"stem": "甲", "branch": "寅"},
        "hour": {"stem": "丁", "branch": "卯"},
    }))
    assert res.metadata["view"]["day_strength_classic"] == "WANG"
    assert res.metadata["view"]["day_strength_state"] == "STRONG"
    assert res.metadata["view"]["yong_shen_ten_god"] == ["财", "官杀", "食伤"]
    assert "土" in res.metadata["view"]["yong_shen_el"]
    # 身弱：甲日失令（月支申金）∧无木根（藏干本气金）∧天干无帮扶 → SHUAI
    # 喜用＝比劫木/印水
    res2 = build(chart({
        "year": {"stem": "庚", "branch": "申"},
        "month": {"stem": "庚", "branch": "申"},
        "day": {"stem": "甲", "branch": "申"},
        "hour": {"stem": "庚", "branch": "申"},
    }))
    assert res2.metadata["view"]["day_strength_classic"] == "SHUAI"
    assert res2.metadata["view"]["day_strength_state"] == "WEAK"
    assert res2.metadata["view"]["yong_shen_ten_god"] == ["印", "比劫"]
    assert "木" in res2.metadata["view"]["yong_shen_el"] and "水" in res2.metadata["view"]["yong_shen_el"]
    # 均衡：甲日失令（月支午火）但得地（日支寅藏干本气甲木）→ JUN_HENG（中和无定喜）
    res3 = build(chart({
        "year": {"stem": "丙", "branch": "午"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "甲", "branch": "寅"},
        "hour": {"stem": "丙", "branch": "午"},
    }, hidden_stems={"寅": ["甲", "丙", "戊"]}))
    assert res3.metadata["view"]["day_strength_classic"] == "JUN_HENG"
    assert res3.metadata["view"]["day_strength_state"] == "NEUTRAL"
    assert res3.metadata["view"]["yong_shen_el"] == []


def test_dts_047_050_cong_hua():
    """真从/假从/真化/假化（《滴天髓》從象/化象/假象/假化篇注）。
    [PENDING_VERIFY] 独象/全象阈值与假化缺龙口径为暂定，待多源验证。
    Human 裁决 2026-09-15：从格不量化——cai_guan_state/support_state 为状态枚举。
    Human 最终裁决 2026-09-16：化从互斥——合化成则论化（TRUE_HUA）、合化不成再论从
    （TRUE_CONG）、均不成立 NONE；special_state 单一输出，hua/cong_candidate 审计。"""
    # 真从：财官得令（申金）且透干（戊庚辛）→STRONG；干支+藏干无比劫印 →NONE
    res = build(chart({
        "year": {"stem": "戊", "branch": "戌"},
        "month": {"stem": "庚", "branch": "申"},
        "day": {"stem": "甲", "branch": "戌"},
        "hour": {"stem": "辛", "branch": "酉"},
    }))
    assert res.metadata["view"]["cai_guan_state"] == "STRONG"
    assert res.metadata["view"]["cong_support_state"] == "NONE"
    assert res.metadata["view"]["special_state"] == "TRUE_CONG"
    assert res.metadata["view"]["cong_candidate"] == "真"
    assert "只論從神" in vals(res, "method")
    assert "假化亦多貴" not in vals(res, "method")
    # 假从：财官 STRONG，时支寅木（比劫微根）→HAS_SUPPORT
    res2 = build(chart({
        "year": {"stem": "戊", "branch": "戌"},
        "month": {"stem": "庚", "branch": "申"},
        "day": {"stem": "甲", "branch": "戌"},
        "hour": {"stem": "辛", "branch": "寅"},
    }))
    assert res2.metadata["view"]["cai_guan_state"] == "STRONG"
    assert res2.metadata["view"]["cong_support_state"] == "HAS_SUPPORT"
    assert res2.metadata["view"]["special_state"] == "TRUE_CONG"
    assert res2.metadata["view"]["cong_candidate"] == "假"
    assert "假從亦可發其身" in vals(res2, "method")
    # 不量化检查：派生 view 不得出现数字计数字段
    view = res.metadata["view"]
    assert not any(k in view for k in ("cai_guan_strength", "support_count", "zhu_wo"))
    # 真化：甲己合于时，单透己、不遇壬癸甲乙戊己、有辰、月支辰土（化神得令）
    res3 = build(chart({
        "year": {"stem": "丙", "branch": "辰"},
        "month": {"stem": "丙", "branch": "辰"},
        "day": {"stem": "甲", "branch": "子"},
        "hour": {"stem": "己", "branch": "巳"},
    }))
    assert res3.metadata["view"]["special_state"] == "TRUE_HUA"
    assert res3.metadata["view"]["pending"]["hua_candidate"] == "真"
    assert "只論化神" in vals(res3, "method")
    # 互斥：真化成立虽财官 STRONG（cong_candidate=假），不得再论从
    assert "假從亦可發其身" not in vals(res3, "method")
    # 假化：甲己合于时，单透己，但无辰（无龙）→ 合而不化，special_state 落 NONE
    res4 = build(chart({
        "year": {"stem": "庚", "branch": "午"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "甲", "branch": "子"},
        "hour": {"stem": "己", "branch": "巳"},
    }))
    assert res4.metadata["view"]["pending"]["hua_candidate"] == "假"
    assert res4.metadata["view"]["special_state"] == "NONE"
    # CAND-DTS-050 依赖 hua_state（PENDING 隔离 2026-09-16）→ 规则不触发，'假化亦多貴' 不输出；
    # 假化派生值 hua_candidate=假 已断言，special_state=NONE（合而不化不终止从格判断）已断言
    # 乙庚真化（四合不检查「不遇」[DIRECT_TEXT]）：乙庚合于月、单透庚、有辰、月支申金（得令）
    # ——壬（印）在干亦不阻断（Human 裁决：乙庚等四合原文未列不遇集，不套用甲己例）
    res5 = build(chart({
        "year": {"stem": "壬", "branch": "辰"},
        "month": {"stem": "庚", "branch": "申"},
        "day": {"stem": "乙", "branch": "丑"},
        "hour": {"stem": "丁", "branch": "巳"},
    }))
    assert res5.metadata["view"]["special_state"] == "TRUE_HUA"
    assert "只論化神" in vals(res5, "method")
    assert "假從亦可發其身" not in vals(res5, "method")
    # 合而不化 + 从格成立（甲己合、无辰、财官 STRONG）：继续判从 → TRUE_CONG，
    # 050 假化因 special_state≠NONE 不输出（论从不论化）
    res6 = build(chart({
        "year": {"stem": "甲", "branch": "午"},
        "month": {"stem": "己", "branch": "丑"},
        "day": {"stem": "甲", "branch": "戌"},
        "hour": {"stem": "辛", "branch": "巳"},
    }))
    assert res6.metadata["view"]["pending"]["hua_candidate"] == "假"
    assert res6.metadata["view"]["cong_candidate"] == "假"
    assert res6.metadata["view"]["special_state"] == "TRUE_CONG"
    assert "假從亦可發其身" in vals(res6, "method")
    assert "假化亦多貴" not in vals(res6, "method")
    assert "只論化神" not in vals(res6, "method")
    # 普通格局：无合无从 → NONE，无特殊格局 method
    res7 = build(chart({
        "year": {"stem": "丙", "branch": "午"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "甲", "branch": "寅"},
        "hour": {"stem": "丙", "branch": "午"},
    }))
    assert res7.metadata["view"]["special_state"] == "NONE"
    assert "hua_candidate" not in res7.metadata["view"].get("pending", {})
    assert "cong_candidate" not in res7.metadata["view"]
    assert not vals(res7, "method")


def test_dts_qingxing_basic():
    """情性篇初版（DTS-052）：059 火烈金水激 / 060 木奔南 / 061 金見水。
    [PENDING_VERIFY] 结构事实近似（同现判定）；旺衰维度待 strength 精度迭代。
    057/058（清和/乖逆）结构事实不足，登记待裁决，未实现。"""
    # 火烈 + 金水之激：丙日（火）月支午（火当令）透丙，盘有金（庚/申）水（癸/子）→ 性燥
    res = build(chart({
        "year": {"stem": "庚", "branch": "子"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "丙", "branch": "申"},
        "hour": {"stem": "癸", "branch": "巳"},
    }))
    v = res.metadata["view"]
    assert v.get("pending", {}).get("fire_state") == "烈"
    assert v.get("pending", {}).get("stimulus") == "金水之激"
    # CAND-DTS-059 依赖 fire_state/stimulus（PENDING 隔离 2026-09-16）→ 规则不触发；
    # 火烈派生值 pending.fire_state/stimulus 已断言
    # 金見水：金水同现 → 流通
    assert v.get("pending", {}).get("gold_meets") == "水"
    # CAND-DTS-061 依赖 gold_meets（PENDING 隔离 2026-09-16）→ 规则不触发；
    # 金見水派生值 pending.gold_meets 已断言
    # 木奔南：木火同现 → 軟怯（独立木火盘：甲午 丙午 甲寅 丙午）
    res_mu = build(chart({
        "year": {"stem": "甲", "branch": "午"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "甲", "branch": "寅"},
        "hour": {"stem": "丙", "branch": "午"},
    }))
    assert res_mu.metadata["view"].get("pending", {}).get("wood_flow") == "奔南"
    # CAND-DTS-060 依赖 wood_flow（PENDING 隔离 2026-09-16）→ 规则不触发；
    # 木奔南派生值 pending.wood_flow 已断言
    # 反例：无火当令（月支非火）→ fire_state=不烈；无金水同现 → stimulus=非激/gold_meets=非水
    res2 = build(chart({
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "丙", "branch": "辰"},
        "day": {"stem": "甲", "branch": "寅"},
        "hour": {"stem": "丁", "branch": "卯"},
    }))
    v2 = res2.metadata["view"]
    # 2026-09-16 三态化：单值枚举补反态，恒输出
    assert v2.get("pending", {}).get("fire_state") == "不烈"
    assert v2.get("pending", {}).get("stimulus") == "非激"
    assert v2.get("pending", {}).get("gold_meets") == "非水"


def test_dts_climate():
    """寒热燥湿（DTS-026 寒溫濕燥論）——Human 裁决 2026-09-16：结构事实判定，禁量化阈值。
    假寒/假热局（占比≥3）、EXTREME（≥7）、DRY_BURNT/WITHOUT_STAGNATION 等全部挂起不实现。
    [PENDING_VERIFY] 证据链待重绑，不得 Admission 为最终古典规则集。"""
    # 寒局：甲子 壬申 庚子 丁亥？——丁透火 → 有暖。造无火寒局：
    # 庚子 壬午? 不行。用：癸亥 癸亥 庚子 癸丑（冬三月亥子丑，无丙丁，无巳午）→ 寒
    res = build(chart({
        "year": {"stem": "癸", "branch": "亥"},
        "month": {"stem": "癸", "branch": "亥"},
        "day": {"stem": "庚", "branch": "子"},
        "hour": {"stem": "癸", "branch": "丑"},
    }))
    v = res.metadata["view"]
    assert v.get("is_cold") is True
    assert v.get("pending", {}).get("cold_level") == "COLD_NO_WARM"
    assert v.get("climate") == "寒"
    assert v.get("climate_type") == "COLD_WET"   # 亥子丑水月亦 is_wet（辰丑亥子）→ 寒湿
    # 寒而有暖：同盘时支加午（火根）
    res2 = build(chart({
        "year": {"stem": "癸", "branch": "亥"},
        "month": {"stem": "癸", "branch": "亥"},
        "day": {"stem": "庚", "branch": "子"},
        "hour": {"stem": "丁", "branch": "午"},
    }))
    v2 = res2.metadata["view"]
    assert v2.get("is_cold") is True
    assert v2.get("pending", {}).get("cold_level") == "COLD_WITH_WARM"
    # 热局：丙午 丙午 甲午 丙辰？辰湿土→is_wet？月令午∈{巳午未}→is_hot 需无壬癸无亥子
    # 丙午 丙午 甲午 丙戌（火土，无壬癸、无亥子、无湿）→ 热+燥（月令午、无亥子丑辰）
    res3 = build(chart({
        "year": {"stem": "丙", "branch": "午"},
        "month": {"stem": "丙", "branch": "午"},
        "day": {"stem": "甲", "branch": "午"},
        "hour": {"stem": "丙", "branch": "戌"},
    }))
    v3 = res3.metadata["view"]
    assert v3.get("is_hot") is True
    assert v3.get("pending", {}).get("hot_level") == "HOT_NO_COOL"
    assert v3.get("is_dry") is True
    assert v3.get("pending", {}).get("dry_level") == "DRY_NO_MOIST"
    assert v3.get("climate") == "熱"
    assert v3.get("climate_type") == "HOT_DRY"
    # 不量化检查：不得出现量化阈值产物
    assert "is_cold" not in {f["field"] for f in res.facts.basic_structure_facts}  # 布尔/枚举为 derived view 字段
    assert all(not any(k in v for k in ("water_count", "fire_count", "extreme"))
               for v in (res.metadata["view"], res2.metadata["view"], res3.metadata["view"]))
