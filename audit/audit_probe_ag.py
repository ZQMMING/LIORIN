# -*- coding: utf-8 -*-
"""边界回归测试断言探测：大运连续性 + 同人九三流年序列 + sanyuan"""
import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from tongshu.engines.heluo.timeline_yun import compute_dayun_liyao, compute_liunian
from tongshu.engines.heluo.numbers import build_six_lines
from tongshu.engines.heluo_adapter import sanyuan

print("=== sanyuan 边界 ===")
for y in [1502, 1503, 1504, 1505, 1563, 1564, 1565, 1623, 1624, 1625, 1683, 1684, 1864, 1924, 1984, 2044]:
    print(f"{y} → {sanyuan(y)}")

print()
print("=== 同人九三阳段流年（birth_year=2024 阳年，age 1-9）===")
tongren = build_six_lines("乾", "离")  # 同人 [1,-1,1,1,1,1]
print("同人六爻 =", tongren)
r = compute_liunian(tongren, 2, tongren, 2, birth_year=2024, age_from=1, age_to=9)
for yr in r.years:
    print(f"  age={yr.age} year={yr.year} {yr.ganzhi} yang={yr.yang_year} → {yr.hexagram_name} [{yr.rule}]")

print()
print("=== 乾为天 大运（yt=3 九四）===")
qian = build_six_lines("乾", "乾")
d = compute_dayun_liyao(qian, 3, qian, 3)
prev_end = 0
for i, e in enumerate(d.sequence):
    cont = "OK " if (i == 0 and e.age_start == 1) or (i > 0 and e.age_start == prev_end + 1) else "**GAP**"
    print(f"[{cont}] {e.age_start:3d}-{e.age_end:3d} {e.hexagram_name} 爻{['初','二','三','四','五','上'][e.line_index]}{e.line_nature} 段{i+1}")
    prev_end = e.age_end

print()
print("=== 复卦纯阴 大运（yt=0 初九→阴爻6年*6=36）===")
fu = build_six_lines("坤", "震")
d2 = compute_dayun_liyao(fu, 0, fu, 0)
for e in d2.sequence:
    print(f"  {e.age_start:3d}-{e.age_end:3d} {e.hexagram_name} 段")
print("最后一段 age_end =", d2.sequence[-1].age_end)
