# -*- coding: utf-8 -*-
"""④旺衰 件1: L3 契约键 底层断点核 (键在?/值None?/None根因)
跑 4 盘(旺/衰/反局/从 各代表) dump l3_contract + daymaster_power, 只读输出, 不动引擎。"""
import sys, os, json
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

# ④旺衰 代表盘 (挑不同旺衰档)
plates = [
    ("旺·建禄当令",  "戊午 戊戌 戊午 戊午"),
    ("衰·财多身弱",  "壬寅 辛亥 丙寅 戊戌"),
    ("反局·专旺",    "乙巳 丁巳 甲子 甲子"),
    ("从·极弱",      "癸酉 丁巳 己卯 甲戌"),
]
l3_keys = ["dm_ben_eff","yin_ben_eff","ling_state","root_grade","root_grade_raw",
           "support_state","strength_verdict","chong_adjust","chong_role","chong_by",
           "library_open","ling_state_eff","de_ling","de_di","dang_duo","fan_ju"]
print("═══ ④旺衰 件1: L3 契约键 底层断点核 ═══")
for lab,bz in plates:
    r=paipan(bz)
    l3=r.get("l3_contract",{})
    print(f"\n[{lab}] {bz}")
    print(f"  l3_contract 实际键({len(l3)}): {list(l3.keys())}")
    for k in l3_keys:
        v=l3.get(k,"<键缺失>")
        tag = "None" if v is None else ("缺键" if v=="<键缺失>" else "有值")
        print(f"    {k:<16} = {str(v)[:34]:<36} [{tag}]")
    # daymaster_power(量层)
    dp=r.get("daymaster_power",{})
    print(f"  daymaster_power: " + " ".join(f"{k}={v}" for k,v in dp.items() if k!='root_detail'))
    st=r.get("structure",{})
    print(f"  structure.comprehensive_verdict = {st.get('comprehensive_verdict')}")
