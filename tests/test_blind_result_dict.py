# -*- coding: utf-8 -*-
"""BlindBaziResult.to_dict() 字段完整性守护。

背景（㊻s132）：to_dict() 曾漏 37 个字段，其中 shi_direction/shi_zhi_jing/
liyi_risk/zhenfu_risk/lu_dangcai/root_provenance/xunkong_branches/yima_branches
正在被 adapters/themes/验证脚本消费 —— 漏输出时下游静默读到 None。
"""
import dataclasses

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.engines.blind_bazi_engine import BlindBaziEngine, BlindBaziResult


def test_to_dict_covers_all_fields():
    r = BlindBaziResult()
    declared = {f.name for f in dataclasses.fields(r)}
    produced = set(r.to_dict().keys())
    missing = sorted(declared - produced)
    assert not missing, f"to_dict 漏字段(下游会读到 None): {missing}"


def test_to_dict_extra_keys_only_compat_alias():
    # 'yin_mie_yang_present' 是 crime_present 的兼容别名, 允许存在; 其余键必须与字段同名。
    r = BlindBaziResult()
    declared = {f.name for f in dataclasses.fields(r)}
    extra = sorted(set(r.to_dict().keys()) - declared)
    assert extra == ["yin_mie_yang_present"], extra


def test_shi_fields_present_1980():
    """1980 案例定势为火土燥势制金水, 势字段必须出现在 to_dict 且非空。"""
    be = BaziEngine()
    bl = BlindBaziEngine(bazi_engine=be)
    r = bl.compute((1980, 6, 22, 10), gender="male")
    d = r.to_dict()
    assert d["shi_direction"] == "FIRE_EARTH→METAL_WATER", d["shi_direction"]
    assert d["shi_zhi_jing"] in ("ZHI_JING", "ZHI_BU_JING")
    assert d["shi_party"] == ["FIRE", "EARTH"]
    assert d["shi_controlled"] == ["METAL", "WATER"]
    # ㊻s128 后 1980 的比劫制财走宾位「劫财夺财=财归我」EFFECTIVE 口径, 争夫降为轻(第三者),
    # 但婚姻仍不得判 HARMONIOUS(宫被冲穿+星弱)。
    assert d["zhenfu_risk"] in ("DIVORCE", "THIRD_PARTY"), d["zhenfu_risk"]
    # 自洽闸（㊻s132）：争夫重 → 婚姻不得判 HARMONIOUS
    assert d["marriage_event_structure"]["marriage_state"] != "HARMONIOUS"
