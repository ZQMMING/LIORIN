# -*- coding: utf-8 -*-
"""L2 切片条件注册表 slice_conditions.py —— 病机 → 切片条件(布尔/序数/离散)

方法论铁律: 禁浮点/乘除加权; 只布尔(eq/ne/in/exists)+序数(gte/lte, 双方int)
              + 离散计数(combo, 他干透干+本气根+局票, 与 bing_debate._counts 同源)。

形态: 每病机 (slice_id, 条件组列表, hook 名列表)
  - 条件组: {"logic": AND/OR, "conditions": [Condition三元组]}  -> condition_evaluator 三态求值
  - hook  : 复合计数判定(combo_ge4 / dm_no_heavy), 同源防偏, 返回 True/False
  - 最终: 任一条件组 MATCHED 且全部 hook 成立 -> MATCHED; 组全 NOT_MATCHED -> NOT_MATCHED;
          ABSTAIN 向上传播(缺事实不裁决)。
  - 状态字段: "并行校验不改判定" —— 只挂 bing_list.slice_condition, 不替代硬编码触发。
"""
from typing import Any, Dict, List, Optional, Tuple


def _combo(facts: Dict[str, Any], wx: str) -> int:
    """离散计数(他干透干+本气根+局票 ju*2+banhe*1), 与 bing_debate._counts 同源."""
    try:
        from engines.common.bing_debate import _counts
        c = _counts(facts.get("pillars") or {}, wx, facts.get("transit_extra"))
        tou_ben = c["tou"] + c["ben"]
    except Exception:
        tou_ben = 0
    wp = ((facts.get("wuxing_power") or {}).get("wuxing_power") or {})
    e = wp.get(wx) or {}
    try:
        return tou_ben + int(e.get("ju_n", 0) or 0) * 2 + int(e.get("banhe_n", 0) or 0) * 1
    except Exception:
        return tou_ben


def _dm_no_heavy(facts: Dict[str, Any]) -> bool:
    """日主无重根: root_weight_class_facts 无任何 HEAVY 根(与验证器同源)."""
    rw = facts.get("root_weight_class_facts") or {}
    try:
        return not any(v.get("class") == "HEAVY" for v in rw.values())
    except Exception:
        return False


# hook 注册表(同源计数)
HOOKS = {
    "combo_ge4": lambda facts, wx: _combo(facts, wx) >= 4,
    "dm_no_heavy": lambda facts, wx: _dm_no_heavy(facts),
    # 2026-10-17 BIJIE_DUO_CAI 触发对齐 bingyao L617 "财明(透干或本气根, 非仅藏中气)":
    #   病五行=财(dm 所克), 明=财干透>=1 或 财本气根ben_n>=1
    "cai_visible": lambda facts, wx: _cai_visible(facts, _dm(facts)),
}

# 占位: {wx}=病五行(来自 bing_wx), {dm}=日主五行
_WX = "{wx}"


def _dm(facts: Dict[str, Any]) -> str:
    return facts.get("daymaster_element") or ""

# 十神五行动作表: 我克=财
_KE_WO = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}

def _cai_visible(facts: Dict[str, Any], dm: str) -> bool:
    """财明: 财干透>=1 或 财本气根ben_n>=1 (与 bingyao_layer L617-621 触发同判).
    透干读 facts['pillars'] 年/月/时干(不含日干, 日主非财), 本气根读四支本气.
    GAN_WX/ZHI_BEN_WX 与 bingyao_layer/bing_debate 同源本地表(引擎惯例: 各层自带)."""
    cai_wx = _KE_WO.get(dm, "")
    if not cai_wx:
        return False
    _GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    _ZHI_BEN_WX = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
    pillars = facts.get("pillars") or {}
    tou = sum(1 for pos in ("year", "month", "hour")
              if _GAN_WX.get((pillars.get(pos) or [None, None])[0]) == cai_wx)
    ben = sum(1 for pos in ("year", "month", "day", "hour")
              if _ZHI_BEN_WX.get((pillars.get(pos) or [None, None])[1]) == cai_wx)
    return tou >= 1 or ben >= 1


# ---------------------------------------------------------------- 注册表
# 与 scripts/slice_condition_calib.py::SLICE_MAP 同源(谓词 → 三元组+hook)。
# 每组自带 hooks(组命中=三元组MATCHED且该组hooks全真); 任一组命中 -> MATCHED。
# 错位/缺切片病机(SGGJ/XDS)注册为 UNVERIFIED: 条件组空 → 恒 ABSTAIN, 不裁不报。
BID_CONDITIONS: Dict[str, Dict[str, Any]] = {
    "CAI_DUO_SHEN_RUO": {
        "slice_id": "PATHOLOGY.QIANG_RUO.004",
        "status": "触发切片·已校准L7-1",
        "groups": [
            # 组A 财当令+日主无重根(effective_rwc!=HEAVY): 不要求combo
            {"logic": "AND", "conditions": [
                {"fact": "month_qi_element", "op": "eq", "value": _WX},
            ], "hooks": ["dm_no_heavy"]},
            # 组B 财成党(combo>=4)+日主无重根
            {"logic": "AND", "conditions": [
                {"fact": "day_stem", "op": "exists"},
            ], "hooks": ["combo_ge4", "dm_no_heavy"]},
        ],
    },
    "SHA_ZHONG_SHEN_QING": {
        "slice_id": "PATHOLOGY.QIANG_RUO.005",
        "status": "触发切片·OK",
        "groups": [
            {"logic": "AND", "conditions": [
                {"fact": "month_qi_element", "op": "eq", "value": _WX},
            ], "hooks": ["dm_no_heavy"]},
            {"logic": "AND", "conditions": [
                {"fact": "day_stem", "op": "exists"},
            ], "hooks": ["combo_ge4", "dm_no_heavy"]},
        ],
    },
    "XIE_QI_TAI_ZHONG": {
        "slice_id": "PATHOLOGY.QIANG_RUO.020",
        "status": "总纲(旺病四类)·切片归属待核(020为旺病总纲, 泄气病无专条)",
        "groups": [
            {"logic": "AND", "conditions": [
                {"fact": "month_qi_element", "op": "eq", "value": _WX},
            ], "hooks": ["dm_no_heavy"]},
            {"logic": "AND", "conditions": [
                {"fact": "day_stem", "op": "exists"},
            ], "hooks": ["combo_ge4", "dm_no_heavy"]},
        ],
    },
    "BIJIE_CHENG_DANG": {
        "slice_id": "PATHOLOGY.QIANG_RUO.001",
        "status": "总纲(众寡)·比劫成党=日主同类combo>=4",
        "groups": [
            {"logic": "AND", "conditions": [
                {"fact": "day_stem", "op": "exists"},
            ], "hooks": ["combo_ge4"]},
        ],
    },
    "SHANGGUAN_JIAN_GUAN": {
        "slice_id": "STRUCTURE.GE_JU.JIU_YING.003",
        "status": "UNVERIFIED·错位登记: 该切片为救应条件非触发; 触发切片(YHZP伤官见官为祸)缺",
        "groups": [],
    },
    "XIAO_DUO_SHI": {
        "slice_id": "PATHOLOGY.JIE_GOU.018",
        "status": "UNVERIFIED·错位登记: 该切片为岁运应期非原局触发; 触发切片缺",
        "groups": [],
    },
    "YIN_DUO_MAI_ZI": {
        "slice_id": "STATE.WANG_SHUAI.FAN_JU.001",
        "status": "触发(反局总纲)·印成党/当令埋日主(土重金埋同构)",
        "groups": [
            {"logic": "AND", "conditions": [
                {"fact": "month_qi_element", "op": "eq", "value": _WX},
            ], "hooks": ["dm_no_heavy"]},
            {"logic": "AND", "conditions": [
                {"fact": "day_stem", "op": "exists"},
            ], "hooks": ["combo_ge4", "dm_no_heavy"]},
        ],
    },
    "BIJIE_DUO_CAI": {
        "slice_id": "PATHOLOGY.QIANG_RUO.001",  # DTS 三十二、众寡「强众而敌寡者, 势在去其寡」准
        "status": "触发切片·2026-10-17准神探针: 众寡章强众敌寡=比劫成众夺财孤寡; 旁参SFTK劫财羊刃辅证",
        "groups": [
            # 组A 比劫成党(combo>=4) + 财明(透干或本气根, 非仅藏中气) + 日主无重根
            {"logic": "AND", "conditions": [
                {"fact": "day_stem", "op": "exists"},
            ], "hooks": ["combo_ge4", "cai_visible"]},
        ],
    },
    "ZHI_SHA_TAI_GUO": {
        "slice_id": "SUI_YUN.RE_EVALUATION.DA_YUN_ZHI_YU.009",
        "status": "旁参·唯一提制伏太过之切片, 为命例非通则",
        "groups": [
            {"logic": "AND", "conditions": [
                {"fact": "day_stem", "op": "exists"},
            ], "hooks": ["combo_ge4", "dm_no_heavy"]},
        ],
    },
}


def _sub(cond: Dict[str, Any], wx: str, dm: str) -> Dict[str, Any]:
    """占位符替换: {wx}->病五行, {dm}->日主五行."""
    out = dict(cond)
    v = out.get("value")
    if isinstance(v, str):
        out["value"] = v.replace(_WX, wx).replace("{dm}", dm)
    return out


def eval_slice_conditions(bid: str, bing_wx: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    """L2 三态求值(生产接线, 并行校验不改判定).

    返回: {"state": MATCHED/NOT_MATCHED/ABSTAIN, "slice_id", "status",
           "reasons": [逐组依据], "hooks": {名: bool}}
    """
    reg = BID_CONDITIONS.get(bid)
    if not reg:
        return {"state": "ABSTAIN", "slice_id": None, "status": "UNVERIFIED·未注册",
                "reasons": ["无注册条件"], "hooks": {}}
    wx = bing_wx or ""
    dm = _dm(facts)
    reasons: List[str] = []
    hook_vals_all: Dict[str, bool] = {}

    try:
        from engines.common.condition_evaluator import evaluate_group
    except Exception:
        return {"state": "ABSTAIN", "slice_id": reg["slice_id"], "status": reg["status"],
                "reasons": ["condition_evaluator 不可用"], "hooks": {}}

    groups = reg.get("groups") or []
    if not groups:
        return {"state": "ABSTAIN", "slice_id": reg["slice_id"], "status": reg["status"],
                "reasons": ["错位/缺切片·无触发条件(UNVERIFIED)"], "hooks": {}}

    # 条件组求值: 组命中=三元组MATCHED且该组hooks全真; 任一组命中 -> MATCHED
    matched = False
    abstain_seen = False
    for g in groups:
        logic = g.get("logic", "AND")
        conds = [_sub(c, wx, dm) for c in g.get("conditions", [])]
        try:
            st, why, details = evaluate_group(conds, facts, logic)
        except Exception as exc:
            reasons.append("组求值异常: %s" % exc)
            st = "ABSTAIN"
        # 该组 hook(存在性)求值
        g_hooks = g.get("hooks") or []
        g_hook_vals: Dict[str, bool] = {}
        for h in g_hooks:
            fn = HOOKS.get(h)
            g_hook_vals[h] = bool(fn(facts, wx)) if fn else False
        hook_vals_all.update(g_hook_vals)
        g_ok = all(g_hook_vals.values()) if g_hook_vals else True
        if st == "MATCHED" and g_ok:
            matched = True
            reasons.append("组[%s] MATCHED(hooks%s): %s" % (logic, g_hook_vals or '', why))
        elif st == "ABSTAIN":
            abstain_seen = True
            reasons.append("组[%s] ABSTAIN: %s" % (logic, why))
        else:
            reasons.append("组[%s] NOT_MATCHED(hooks%s): %s" % (logic, g_hook_vals or '', why))

    if matched:
        state = "MATCHED"
    elif abstain_seen and not matched:
        state = "ABSTAIN"
    else:
        state = "NOT_MATCHED"

    return {
        "state": state,
        "slice_id": reg["slice_id"],
        "status": reg["status"],
        "reasons": reasons,
        "hooks": hook_vals_all,
    }


if __name__ == "__main__":
    import io
    import os
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from p0_v2.bazi_gate import paipan
    r = paipan("癸亥壬戌乙未壬午")
    print("盘: 癸亥壬戌乙未壬午")
    for b in r.get("bing_list") or []:
        sc = eval_slice_conditions(b.get("bing_id"), b.get("bing_wx"), r)
        print("  %-20s wx=%-2s -> %-12s %s" % (b.get("bing_id"), b.get("bing_wx"), sc["state"], sc["status"]))
        for rr in sc["reasons"]:
            print("       %s" % rr)
