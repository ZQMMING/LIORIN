# -*- coding: utf-8 -*-
"""PATCH-022D 引擎接线：1983-11-03 命局 × 12 条 ADMITTED 规则 条件评估矩阵
- 已准入规则（12）：022A 单态 4 + 022D 多因素 8
- 对命局逐条评估条件满足度：可判定（结构事实）/ 需消费身弱（PENDING）→ UNDETERMINED / 条件不满足
- strength_state：六部无综合授权 → 保持 UNDETERMINED（FAIL_CLOSED 正确行为）
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

# ---- 排盘 ----
J = jdn(1983, 11, 3)
di = (J + 49) % 60
d_gan, d_zhi = di % 10, di % 12
pillars = {"年柱": "癸亥", "月柱": "壬戌", "日柱": GAN[d_gan] + ZHI[d_zhi], "时柱": "壬午"}
day_gan = GAN[d_gan]
order = "木火土金水"
day_wx = wx(day_gan)
month_wx = wx(pillars["月柱"][1])
i1, i2 = order.index(day_wx), order.index(month_wx)
rel = (i2 - i1) % 5
order_state = "GET_ORDER" if (rel == 0 or rel == 4) else "NOT_GET_ORDER"

roots = [col for col in pillars if any(wx(c) == day_wx for c in CANG[pillars[col][1]])]
root_state = "HAS_ROOT" if roots else "NO_ROOT"

supports = []
for col in pillars:
    g = pillars[col][0]
    gw = wx(g)
    if gw == day_wx:
        supports.append(col + ":比劫")
    elif order.index(gw) == (order.index(day_wx) - 1) % 5:
        supports.append(col + ":印")
bj_tou = [r for r in supports if ":比劫" in r and not r.startswith("日柱")]

# 十神（天干）
def ten_god(g):
    gw = wx(g); zw = day_wx
    same = (GAN.index(g) % 2) == (GAN.index(GAN[d_gan]) % 2)
    r = (order.index(gw) - order.index(zw)) % 5
    if r == 0: return "比肩" if same else "劫财"
    if r == 1: return "食神" if same else "伤官"
    if r == 2: return "偏财" if same else "正财"
    if r == 3: return "七杀" if same else "正官"
    return "偏印" if same else "正印"

tgs = {col: ten_god(pillars[col][0]) for col in pillars}
# 财星（日主所克）=土：地支戌未午（三支土）+天干无财透
cai_count_dizhi = sum(1 for col in pillars if wx(pillars[col][1]) == "土")
cai_tou = [col for col in pillars if ten_god(pillars[col][0]) in ("正财", "偏财")]
sha_tou = [col for col in pillars if ten_god(pillars[col][0]) in ("七杀", "正官")]
yin_tou = [col for col in pillars if "印" in ten_god(pillars[col][0])]

# ---- 12 条 ADMITTED 条件评估 ----
chart = {
    "order_state": order_state,
    "root_state": root_state,
    "root_branches": roots,
    "supports": supports,
    "bj_tou": bj_tou,
    "cai_dizhi_count": cai_count_dizhi,
    "cai_tou": cai_tou,
    "sha_tou": sha_tou,
    "yin_tou": yin_tou,
    "tgs": tgs,
}
print("排盘:", json.dumps(pillars, ensure_ascii=False))
print("日主:", day_gan, "| order:", order_state, "| root:", root_state, roots, "| 印透:", yin_tou, "| 财透:", cai_tou, "| 官杀透:", sha_tou, "| 地支土(财)数:", cai_count_dizhi)

ADMITTED_EVAL = [
    ("CAND-WANG-001", "得时俱为旺论", lambda c: c["order_state"] == "GET_ORDER", "得令"),
    ("CAND-SHUAI-001", "失令便作衰看", lambda c: c["order_state"] == "NOT_GET_ORDER", "失令"),
    ("CAND-QIANG-001", "日干无气遇劫为强", lambda c: c["order_state"] == "NOT_GET_ORDER" and len(c["bj_tou"]) > 0, "无气∧遇劫"),
    ("RULE-022C-01", "财多生官须身健/财多盗气自柔（wealth_relation_state）", lambda c: False, "财星结构登记（非数量判定）"),
    ("RULE-022C-02", "身强杀浅假杀为权", lambda c: False, "需身强断言（未产生）"),
    ("RULE-022C-03", "杀旺运纯身旺→清贵/七杀全彰→极贫", lambda c: len(c["sha_tou"]) >= 1, "官杀透（运纯/全彰分支待定）"),
    ("RULE-022C-04", "七杀格喜忌", lambda c: len(c["sha_tou"]) >= 1, "官杀透→格内条件"),
    ("RULE-022C-05", "中和原则（DTS）", lambda c: True, "原则登记（DTS 域，禁→NEUTRAL）"),
    ("RULE-022C-06", "伤官财格双向", lambda c: False, "伤官格未确认"),
    ("RULE-022C-07", "煞食均根轻助身", lambda c: len(c["sha_tou"]) >= 1, "官杀透；煞食均/根轻待核"),
    ("RULE-022C-08", "身旺身弱月令入口", lambda c: True, "语境锚（月令入口登记）"),
]

print("\n==== 条件评估矩阵（12 ADMITTED）====")
print("（RULE-022C-01 已改为 wealth_relation_state 登记：财星结构/日主关系/泄耗关系/条件限制，非数量判定）")
for rid, name, cond, trigger_note in ADMITTED_EVAL:
    hit = cond(chart)
    status = "条件满足→规则可消费" if hit else "条件不满足/未断言"
    print(f"  {rid} | {name}")
    print(f"     触发线索: {trigger_note} | 评估: {status}")

print("\n==== wealth_relation_state（R1-01 对象化）====")
print("  wealth_structure : 地支戌未土=2（得地无透）；天干无财透")
print("  daymaster_relation: 未断言（日主失令但通根+印三透，泄身关系未逐支确认）")
print("  drain_relation   : UNDETERMINED（财不干透，盗气程度未断言）")
print("  condition_limits : 身健/身弱未断言（CAND-RUO-001 PENDING）")
print("  status           : UNDETERMINED（财多不作数量结论）")

print("\n==== strength_state 产出权限（R1-02）====")
print("  authorized_rules = []（当前 0 条 ADMITTED 登记 output=strength_state）")
print("  禁止: relationship_result/context_marker/wang/shuai/qiang/single_factor/factor_count/中和 → strength_state")
print("  解锁条件: 多因素输入 + scope 匹配 + 无单因子 + Golden 全过 + Admission 登记产出权限")

print("\n==== strength_state ====")
print("  UNDETERMINED")
print("  原因: strength_state=RELATIONAL_RESULT 需消费端状态齐备；身弱概念 PENDING（CAND-RUO-001 无单锚）；")
print("        身旺未断言（无得时）；六部无 factor_collection→strength_state 综合授权 → FAIL_CLOSED 正确行为")
