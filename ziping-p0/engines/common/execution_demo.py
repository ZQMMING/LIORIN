# -*- coding: utf-8 -*-
"""PATCH-020 Engine Execution 沙盘：八字排盘 + 事实层（确定性计算，不产业务判断）
输入：1983-11-03 11:30 男 广东中山（东经113.4°）
输出：四柱/藏干/十神/Boolean 事实白名单（004B 允许 DIRECT_OUTPUT 的结构事实）
边界：不产身强/喜忌/富贵等判断（Rule 层 ADMITTED=0）；规则命中仅为 PENDING 候选清单。"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ---------- 1. 天文排盘（确定性） ----------
def jdn(y, m, d):
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045

def ganzhi_from_jdn(j):
    idx = (j + 49) % 60  # 锚点：2000-01-01 戊午
    gan = idx % 10
    zhi = idx % 12
    return gan, zhi

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
WX = {"甲乙": "木", "丙丁": "火", "戊己": "土", "庚辛": "金", "壬癸": "水",
      "子亥": "水", "寅卯": "木", "巳午": "火", "申酉": "金", "辰戌丑未": "土"}

def wx(ganzhi_char):
    if ganzhi_char in WX:
        return WX[ganzhi_char]
    for k, v in WX.items():
        if ganzhi_char in k:
            return v
    return "?"

# 年柱：1983 立春后 → 癸亥
y_gan, y_zhi = (9, 11)  # 癸亥
# 月柱：11月3日（寒露后立冬前=戌月）；癸年九月壬戌（五虎遁）
m_gan, m_zhi = (8, 10)  # 壬戌
# 日柱：计算
J = jdn(1983, 11, 3)
d_gan, d_zhi = ganzhi_from_jdn(J)
# 时柱：11:30 午时；五鼠遁（日干定子时干）
WU_SHUN = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8}  # 甲己→甲子(0)、乙庚→丙子(2)、丙辛→戊子(4)、丁壬→庚子(6)、戊癸→壬子(8)
h_gan = (WU_SHUN[d_gan] + 6) % 10  # 午时=子时+6
h_zhi = 6  # 午

pillars = {
    "年柱": GAN[y_gan] + ZHI[y_zhi],
    "月柱": GAN[m_gan] + ZHI[m_zhi],
    "日柱": GAN[d_gan] + ZHI[d_zhi],
    "时柱": GAN[h_gan] + ZHI[h_zhi],
}
day_master = GAN[d_gan]

# ---------- 2. 地支藏干（YHZP 人元用事表 A 级；此处只列主气/藏干，不涉用事分段） ----------
CANG = {
    "子": ["癸"], "丑": ["己", "癸", "辛"], "寅": ["甲", "丙", "戊"],
    "卯": ["乙"], "辰": ["戊", "乙", "癸"], "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"], "未": ["己", "丁", "乙"], "申": ["庚", "壬", "戊"],
    "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"],
}

# ---------- 3. 十神（日干天干 vs 各柱天干；六部基础映射） ----------
def ten_god(g):
    """g=该柱天干；日主=day_master。同我比劫、我生食伤、我克财、克我官杀、生我印（阴阳分正偏）。"""
    gw = wx(g)
    zw = wx(GAN[d_gan])
    same_sex = (GAN.index(g) % 2) == (GAN.index(GAN[d_gan]) % 2)  # 奇数索引=阴
    order = "木火土金水"
    i1, i2 = order.index(gw), order.index(zw)
    rel = (i1 - i2) % 5  # 以日主为参照：g 相对日主
    if rel == 0:
        return "比肩" if same_sex else "劫财"   # 同我
    if rel == 1:
        return "食神" if same_sex else "伤官"   # 我生
    if rel == 2:
        return "偏财" if same_sex else "正财"   # 我克
    if rel == 3:
        return "七杀" if same_sex else "正官"   # 克我
    if rel == 4:
        return "偏印" if same_sex else "正印"   # 生我
    return "?"

# ---------- 4. Boolean 事实白名单（004B：has_root/has_hidden_stem/has_combination/has_clash/has_support_relation） ----------
# 通根：日干五行在地支藏干中有同五行
root_branches = []
for br in ["年柱", "月柱", "日柱", "时柱"]:
    z = pillars[br][1]
    if wx(z) == wx(GAN[d_gan]) or any(wx(c) == wx(GAN[d_gan]) for c in CANG[z]):
        root_branches.append(br)
has_root = len(root_branches) > 0

# 合（六合）：子丑 寅亥 卯戌 辰酉 巳申 午未
LIU_HE = {"子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未"}
branches = [pillars["年柱"][1], pillars["月柱"][1], pillars["日柱"][1], pillars["时柱"][1]]
he_pairs = []
for i in range(4):
    for j in range(i + 1, 4):
        pair = frozenset([branches[i], branches[j]])
        if any(set(p) == set(pair) for p in LIU_HE):
            he_pairs.append((branches[i], branches[j]))
has_combination = len(he_pairs) > 0

# 冲（六冲）：子午 丑未 寅申 卯酉 辰戌 巳亥
LIU_CHONG = {"子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥"}
chong_pairs = []
for i in range(4):
    for j in range(i + 1, 4):
        pair = frozenset([branches[i], branches[j]])
        if any(set(p) == set(pair) for p in LIU_CHONG):
            chong_pairs.append((branches[i], branches[j]))
has_clash = len(chong_pairs) > 0

# 生扶关系（日干与四柱干支的生克）：印生身/比劫扶
order = "木火土金水"
support_list = []
for col in ["年柱", "月柱", "日柱", "时柱"]:
    g = pillars[col][0]
    gw = wx(g)
    if gw == wx(GAN[d_gan]):
        support_list.append(col + "比劫")
    elif (wx(GAN[d_gan]) in "木火土金水" and order.index(gw) == (order.index(wx(GAN[d_gan])) - 1) % 5):
        support_list.append(col + "印")
has_support_relation = len(support_list) > 0

order = "木火土金水"
result = {
    "input": "1983-11-03 11:30 男 广东中山（东经约113.4°，真太阳时仍在午时）",
    "pillars": pillars,
    "day_master": day_master + "（" + wx(GAN[d_gan]) + "）",
    "cang_gan": {k: CANG[v[1]] for k, v in pillars.items()},
    "ten_gods": {col: ten_god(pillars[col][0]) for col in pillars},
    "boolean_facts_004b_whitelist": {
        "has_root": has_root, "root_branches": root_branches,
        "has_hidden_stem": True, "has_combination": has_combination, "he_pairs": [list(p) for p in he_pairs],
        "has_clash": has_clash, "chong_pairs": [list(p) for p in chong_pairs],
        "has_support_relation": has_support_relation, "support_detail": support_list,
    },
    "boundary_note": "以上仅 004B Boolean 白名单结构事实（DIRECT_OUTPUT 层）；不产出任何身强/喜忌/格局/富贵判断；Rule 层 ADMITTED=0，规则命中需单独跑 validation 管线（PENDING）。",
}
print(json.dumps(result, ensure_ascii=False, indent=2))
