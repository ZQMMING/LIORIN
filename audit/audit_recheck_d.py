# -*- coding: utf-8 -*-
"""H17-D 裁决复核：反卦对五行关系 + 现有测试用例 + 锚点"""
import sys
sys.path.insert(0, r"D:\shuntian")
sys.path.insert(0, r"D:\shuntian\src")
from tongshu.engines.heluo.numbers import TRIGRAM_ELEMENT
from tongshu.engines.heluo.hua_gong import compute_huagong

# 五行生克：木克土、土克水、水克火、火克金、金克木
def relation(a, b):
    """a 对 b：'a生b' / 'a克b' / 'b生a' / 'b克a' / '比和' / '无关'"""
    el_a, el_b = TRIGRAM_ELEMENT[a], TRIGRAM_ELEMENT[b]
    sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    if el_a == el_b:
        return "比和"
    if sheng[el_a] == el_b:
        return "a生b"
    if sheng[el_b] == el_a:
        return "b生a"
    if ke[el_a] == el_b:
        return "a克b"
    if ke[el_b] == el_a:
        return "b克a"
    return "?"

print("=== 反卦对五行关系 ===")
for a, b in [("坎", "离"), ("兑", "震")]:
    print(f"{a}({TRIGRAM_ELEMENT[a]}) vs {b}({TRIGRAM_ELEMENT[b]}) → {relation(a, b)}")

print()
print("=== 现有测试用例 compute_huagong('震','坤','兑','坤','寅') ===")
r = compute_huagong("震", "坤", "兑", "坤", "寅")
print(f"state={r.state.value}  has_huagong={r.has_huagong} has_opposite={r.has_opposite}")
print(f"五行关系：震木 vs 兑金 → {relation('震','兑')}（化工卦=震，反卦=兑）")
print(f"坤土 vs 兑金 → {relation('坤','兑')}（第三卦）")

print()
print("=== 锚点复跑 ===")
for (pre_u, pre_l, post_u, post_l, branch, name) in [
    ("巽", "艮", "离", "巽", "戌", "1983-11-03 戌月"),
    ("坤", "坤", "艮", "坤", "亥", "2026-12-07 亥月"),
    ("坤", "坤", "艮", "坤", "子", "2000-12-25 子月"),
]:
    rr = compute_huagong(pre_u, pre_l, post_u, post_l, branch)
    print(f"{name}: {pre_u}{pre_l}→{post_u}{post_l} 当月令={rr.huagong_trigram} 状态={rr.state.value}")

print()
print("=== 枚举 has_H & has_O 组合（震当令/寅）===")
# 四卦中含震(H)和兑(O)的所有组合，第3/4卦位取坤/艮/乾/巽/离/坎 轮换
for extra1 in ["坤", "艮", "乾", "巽", "离", "坎"]:
    for extra2 in ["坤", "艮", "乾", "巽", "离", "坎"]:
        rr = compute_huagong(extra1, "震", "兑", extra2, "寅")
        if rr.has_huagong and rr.has_opposite:
            rel_H_O = relation("震", "兑")
            # 救应扫描：extra1/extra2 中任一 生H(震木) 或 克O(兑金)
            rescue = any(rel in ("a生b", "b克a") for rel in [relation(e, "震") for e in (extra1, extra2)]) or \
                     any(rel in ("a克b",) for rel in [relation(e, "兑") for e in (extra1, extra2)])
            print(f"卦={{震,兑,{extra1},{extra2}}} → {rr.state.value}  救应存在={rescue}")
