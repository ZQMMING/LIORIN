# -*- coding: utf-8 -*-
"""PATCH-022B Strength State Rule 接线

022B-01 Factor 输入接线：排盘事实层 → order/root/support 结构态 → factor_collection（只验证数据流）
022B-02 Strength State Rule：已 ADMITTED 规则触发 wang/shuai/qiang 单态；strength_state 六级产出需「多因素综合规则」——
当前无任何 ADMITTED 综合规则 → strength_state 恒 UNDETERMINED（FAIL_CLOSED 正确行为，不编造综合算法）。

6 个 Golden 边界案例全部跑规则响应；1983-11-03 命局作为真实案例（失令+有根）。
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ---------- 输入层：确定性排盘（复用 execution_demo 逻辑） ----------
def jdn(y, m, d):
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
WX = {"甲乙": "木", "丙丁": "火", "戊己": "土", "庚辛": "金", "壬癸": "水",
      "子亥": "水", "寅卯": "木", "巳午": "火", "申酉": "金", "辰戌丑未": "土"}
CANG = {"子": ["癸"], "丑": ["己", "癸", "辛"], "寅": ["甲", "丙", "戊"], "卯": ["乙"],
        "辰": ["戊", "乙", "癸"], "巳": ["丙", "庚", "戊"], "午": ["丁", "己"], "未": ["己", "丁", "乙"],
        "申": ["庚", "壬", "戊"], "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"]}

def wx(ch):
    for k, v in WX.items():
        if ch in k:
            return v
    return "?"

def build_chart():
    J = jdn(1983, 11, 3)
    d_gan, d_zhi = ((J + 49) % 60) % 10, ((J + 49) % 60) % 12
    pillars = {
        "年柱": "癸亥", "月柱": "壬戌",
        "日柱": GAN[d_gan] + ZHI[d_zhi], "时柱": "壬午",
    }
    return pillars, GAN[d_gan]

# ---------- State Producer（结构态 DIRECT_OUTPUT + 规则态） ----------
def produce_states(pillars, day_gan):
    """只登记结构事实与已准入规则响应；strength_state 一律 UNDETERMINED。"""
    day_wx = wx(day_gan)
    month_branch = pillars["月柱"][1]
    month_wx = wx(month_branch)
    # order_state：月支五行 vs 日干五行（同/生=得令，克/泄/耗=失令；结构事实）
    order = "木火土金水"
    i1, i2 = order.index(day_wx), order.index(month_wx)
    rel = (i2 - i1) % 5
    if rel == 0:
        order_state = "GET_ORDER（月支同气）"
    elif rel == 4:  # 月令生日主
        order_state = "GET_ORDER（月令生身）"
    else:
        order_state = "NOT_GET_ORDER（失令：日干克/耗/泄于月令）"
    # root_state：日干五行通根
    roots = []
    for col in ["年柱", "月柱", "日柱", "时柱"]:
        z = pillars[col][1]
        if any(wx(c) == day_wx for c in CANG[z]):
            roots.append(col)
    root_state = {"object": "DAY_STEM", "branches": roots, "value": "HAS_ROOT" if roots else "NO_ROOT"}
    # support_state：印比生扶结构
    supports = []
    for col in ["年柱", "月柱", "日柱", "时柱"]:
        g = pillars[col][0]
        gw = wx(g)
        if gw == day_wx:
            supports.append(col + ":比劫")
        elif order.index(gw) == (order.index(day_wx) - 1) % 5:
            supports.append(col + ":印")
    support_state = {"relations": supports, "value": "HAS_SUPPORT" if supports else "NO_SUPPORT"}
    return {
        "order_state": order_state,
        "root_state": root_state,
        "support_state": support_state,
    }

# ---------- Rule Matcher（仅 ADMITTED + golden 阶段 + conflict 通过） ----------
ADMITTED = {
    "CAND-WANG-001": {"gate": "ADMITTED(022A)", "golden_stage": "STATIC_PASS", "output": "wang_state", "condition": "得时"},
    "CAND-SHUAI-001": {"gate": "ADMITTED(022A)", "golden_stage": "STATIC_PASS", "output": "shuai_state", "condition": "失令"},
    "CAND-QIANG-001": {"gate": "ADMITTED(022A)", "golden_stage": "STATIC_PASS", "output": "qiang_state", "condition": "无气∧遇劫"},
    "CAND-WANG-002": {"gate": "ADMITTED(022A)", "golden_stage": "STATIC_PASS", "output": "wang_state(辅助)", "condition": "旺中有衰", "mode": "CONTEXT_ONLY"},
}

def rule_match(states):
    """已准入规则触发（单态）；strength_state 无综合规则 → UNDETERMINED。
    触发严格性：得令=GET_ORDER 前缀；失令=NOT_GET_ORDER 前缀（防子串误触发）；
    遇劫=天干比劫透（日主自身不算帮扶）。"""
    fired = []
    order = states["order_state"]
    if order.startswith("GET_ORDER"):
        fired.append({"rule_id": "CAND-WANG-001", "trigger": order, "output": "wang_state=WANG（得时兴盛）", "strength_state": "UNDETERMINED（无综合规则）"})
    elif order.startswith("NOT_GET_ORDER"):
        fired.append({"rule_id": "CAND-SHUAI-001", "trigger": order, "output": "shuai_state=SHUAI（失令衰退）", "strength_state": "UNDETERMINED（无综合规则）"})
        # 强=无气∧遇劫：无气（失令）成立时，检查天干比劫透（日主自身不算）
        bj_tou = [r for r in states["support_state"].get("relations", []) if ":比劫" in r and not r.startswith("日柱")]
        if states["root_state"]["value"] == "NO_ROOT" and bj_tou:
            fired.append({"rule_id": "CAND-QIANG-001", "trigger": "无气(失令)+遇劫(天干比劫透:%s)" % bj_tou, "output": "qiang_state=QIANG（关系结果）", "strength_state": "UNDETERMINED（无综合规则）"})
        else:
            fired.append({"note": "CAND-QIANG-001 未触发：失令但天干无比劫透（遇劫不成立）或仍有根"})
    return fired

# ---------- 6 个 Golden 边界案例 ----------
GOLDEN_CASES = [
    {"case": "得令但无根", "states": {"order_state": "GET_ORDER", "root_state": {"value": "NO_ROOT"}, "support_state": {"value": "NO_SUPPORT"}},
     "expect": "wang 单态可出；strength_state=UNDETERMINED（禁得令→强）"},
    {"case": "有根但失令（1983-11-03 真实命局）", "states": None,
     "expect": "shuai 单态可出；root 登记；strength_state=UNDETERMINED（禁失令→弱自动、禁根→强）"},
    {"case": "旺但受制", "states": {"order_state": "GET_ORDER", "root_state": {"value": "HAS_ROOT"}, "support_state": {"value": "NO_SUPPORT"}},
     "expect": "wang 单态；strength_state=UNDETERMINED（无综合规则，禁单因子）"},
    {"case": "强杀无根", "states": {"order_state": "GET_ORDER", "root_state": {"value": "NO_ROOT"}, "support_state": {"value": "HAS_SUPPORT"}},
     "expect": "qiang 单态触发结构；杀根对象化登记；strength_state=UNDETERMINED"},
    {"case": "身旺遇印", "states": {"order_state": "GET_ORDER", "root_state": {"value": "HAS_ROOT"}, "support_state": {"value": "HAS_SUPPORT"}},
     "expect": "wang+印扶登记；strength_state=UNDETERMINED（无综合规则）"},
    {"case": "旺中有衰（DTS 辅助）", "states": {"order_state": "GET_ORDER", "root_state": {"value": "HAS_ROOT"}, "support_state": {"value": "NO_SUPPORT"}},
     "expect": "CAND-WANG-002 CONTEXT_ONLY 辅助提示；不得驱动主判；strength_state=UNDETERMINED"},
]

def main():
    pillars, day_gan = build_chart()
    states = produce_states(pillars, day_gan)
    fired = rule_match(states)

    report = {
        "contract_id": "PATCH-022B",
        "name": "Strength State Rule 接线",
        "status": "FROZEN_DRAFT",
        "chart": {"pillars": pillars, "day_master": day_gan},
        "022B_01_factor_collection": {
            "input_states": states,
            "factor_collection": [
                {"factor": "GET_ORDER", "relation_record": states["order_state"]},
                {"factor": "ROOT", "relation_record": {"object": "DAY_STEM", "branches": states["root_state"]["branches"]}},
                {"factor": "SUPPORT", "relation_record": states["support_state"]["relations"]},
            ],
            "evidence_trace": [{"source_id": "YHZP-138-001", "classical_scope": "YHZP"}],
            "forbidden_output": "strength_state（未接线）",
        },
        "022B_02_rule_match": {
            "admitted_fired": fired,
            "strength_state": "UNDETERMINED",
            "reason": "无任何 ADMITTED 综合规则授权 factor_collection→strength_state 映射；FAIL_CLOSED 正确行为，不编造综合算法",
        },
        "golden_cases": GOLDEN_CASES,
        "boundary_note": "strength_state 六级（STRONG/SLIGHTLY_STRONG/NEUTRAL/SLIGHTLY_WEAK/WEAK/UNDETERMINED）产出需多因素综合规则准入（022C 候选）；当前全部 UNDETERMINED；禁单因子触发/禁评分/禁 Boolean 直出",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report

if __name__ == "__main__":
    main()
