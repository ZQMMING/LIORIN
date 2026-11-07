# -*- coding: utf-8 -*-
"""Probe script saved for audit trail."""
import sys
sys.path.insert(0, 'D:/shuntian-ziping-p0')
from p0_v2.bazi_gate import paipan

# Probe 1
print("=== Probe 1: 癸酉丁巳己卯甲戌 ===")
r1 = paipan('癸酉丁巳己卯甲戌')
print('Keys count:', len(r1.keys()))
print('Top-level keys:', sorted(r1.keys()))
bl = r1.get('bing_list')
print('bing_list count:', len(bl) if bl else 0)
lc = r1.get('l3_contract')
print('l3_contract keys:', list(lc.keys())[:15] if lc else 'None')
print('ge_cheng:', r1.get('ge_cheng'))
print('special:', r1.get('special'))
print('yongyao:', r1.get('yongyao'))

# Probe 2
print("\n=== Probe 2: 乙酉庚辰丁巳辛亥 ===")
r2 = paipan('乙酉庚辰丁巳辛亥')
bl2 = r2.get('bing_list', [])
print('bing_list count:', len(bl2))
for b in bl2:
    print(f'  id={b.get("bing_id")} name={b.get("name")} domain={b.get("bing_domain")} severity={b.get("severity")} slice_id={b.get("slice_id")}')

# Probe 3
print("\n=== Probe 3: 辛卯丁酉庚午丙子 ===")
r3 = paipan('辛卯丁酉庚午丙子')
bl3 = r3.get('bing_list', [])
print('bing_list count:', len(bl3))
for b in bl3:
    print(f'  id={b.get("bing_id")} name={b.get("name")}')
print('bing_debate state:', (r3.get('bing_debate') or {}).get('state'))
lc3 = r3.get('l3_contract') or {}
print('de_ling:', lc3.get('de_ling'))
print('de_di:', lc3.get('de_di'))
print('dang_duo:', lc3.get('dang_duo'))
print('strength_verdict:', lc3.get('strength_verdict'))
