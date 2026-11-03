# -*- coding: utf-8 -*-
"""PATCH-091~097 六经典结构深化七模块"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 091 格局层次(非评分)
def pattern_level(success, qingzao, xiangshen_ok):
    if success and qingzao and xiangshen_ok:
        level = "HIGH"
    elif success and (qingzao or xiangshen_ok):
        level = "MEDIUM"
    elif success:
        level = "LOW"
    else:
        level = "UNDETERMINED"
    return {"state": "pattern_level_state", "namespace": "PZZQ.pattern_level",
            "value": level, "note": "层次=成败+清浊+相神, 非评分, 非成功=贵"}


# 092 格局救应runtime
def rescue_runtime(break_factor, rescue_factor):
    if not break_factor:
        return {"state": "rescue_state", "namespace": "PZZQ.rescue", "result": "NO_BREAK"}
    if rescue_factor:
        return {"state": "rescue_state", "namespace": "PZZQ.rescue",
                "result": "RESCUED", "note": "破格因素+救应因素=结构恢复, 非吉凶"}
    return {"state": "rescue_state", "namespace": "PZZQ.rescue", "result": "UNRESCUED"}


# 093 五行形气
def qi_shape_broken(elements_present, full=False):
    return {"state": "qi_shape_state", "namespace": "DTS.qi_shape",
            "full": full, "note": "形全损有余/形缺补不足; 非力量评分"}


# 094 顺逆趋势
def trend_direction(follow_strength, against_order):
    if follow_strength:
        return {"state": "trend_direction", "namespace": "DTS.trend", "value": "顺势"}
    if against_order:
        return {"state": "trend_direction", "namespace": "DTS.trend", "value": "逆势"}
    return {"state": "trend_direction", "namespace": "DTS.trend", "value": "待定"}


# 095 调候制化runtime
def climate_balance(cold, dry):
    if cold:
        return {"state": "climate_balance", "namespace": "QTBJ.climate_balance", "change": "寒→待温", "note": "状态变化, 非好运"}
    if dry:
        return {"state": "climate_balance", "namespace": "QTBJ.climate_balance", "change": "燥→待润", "note": "状态变化, 非好运"}
    return {"state": "climate_balance", "namespace": "QTBJ.climate_balance", "change": "平衡"}


# 096 病药有效性
def medicine_effectiveness(medicine_strength, medicine_blocked):
    if medicine_blocked:
        return {"state": "medicine_effectiveness", "namespace": "SFTK.bingyao", "value": "被制"}
    if medicine_strength in ("STRONG", "NORMAL"):
        return {"state": "medicine_effectiveness", "namespace": "SFTK.bingyao", "value": "有力"}
    return {"state": "medicine_effectiveness", "namespace": "SFTK.bingyao", "value": "无力"}


# 097 六亲完整state
def six_relative_full(gender):
    rel = {"父": "偏财/年柱", "母": "正印/月柱"}
    if gender == "男":
        rel["妻"] = "财星/日支夫妻宫"
    else:
        rel["夫"] = "官杀/日支夫妻宫"
    return {"state": "six_relative_state", "namespace": "SIX_RELATIVE",
            "gender": gender, "map": rel, "note": "六亲=星+宫+关系, 非简单财=妻印=母"}


if __name__ == '__main__':
    print("091格局层次:", pattern_level(True, True, True)["value"])
    print("092救应:", rescue_runtime("财被劫", "官护财")["result"])
    print("093形气:", qi_shape_broken([])["note"][:10])
    print("094顺逆:", trend_direction(True, False)["value"])
    print("095调候制化:", climate_balance(True, False)["change"])
    print("096药有效性:", medicine_effectiveness("NORMAL", False)["value"])
    print("097六亲(男):", six_relative_full("男"))
