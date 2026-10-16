# -*- coding: utf-8 -*-
"""H17-B/C 裁决复核：验证萃/旅卦象构造与元堂落点"""
import sys
sys.path.insert(0, r"D:\shuntian")
sys.path.insert(0, r"D:\shuntian\src")
from tongshu.engines.heluo.numbers import build_six_lines
from tongshu.engines.heluo.yuan_tang import find_yuantang

print("泽地萃(上兑下坤) =", build_six_lines("兑", "坤"))
print("地泽临(上坤下兑) =", build_six_lines("坤", "兑"))
print("火山旅(上离下艮) =", build_six_lines("离", "艮"))
print("山火贲(上艮下离) =", build_six_lines("艮", "离"))
print("天水讼(上乾下坎) =", build_six_lines("乾", "坎"))
print()
# 萃卦子时男（N=2）
for hour in ["子", "丑", "寅", "卯", "辰", "巳"]:
    r = find_yuantang(build_six_lines("兑", "坤"), hour, "male", "泽地萃")
    print(f"萃卦{hour}时男 → {r.yuantang} (idx={r.yuantang_index}) {r.yao_nature} [{r.trace[0]['action']}]")
print()
# 旅卦各时男（N=3）
for hour in ["子", "午", "酉", "戌"]:
    r = find_yuantang(build_six_lines("离", "艮"), hour, "male", "火山旅")
    print(f"旅卦{hour}时男 → {r.yuantang} (idx={r.yuantang_index}) {r.yao_nature} [{r.trace[0]['action']}]")
print()
# 天水讼阴时六行（原典:85 戌时生得讼 午初六未六三申复初六酉复六三戌九四）
print("=== 原典讼卦金例：午未申酉戌亥（阴时）男 ===")
for hour in ["午", "未", "申", "酉", "戌", "亥"]:
    r = find_yuantang(build_six_lines("乾", "坎"), hour, "male", "天水讼")
    print(f"讼卦{hour}时男 → {r.yuantang} (idx={r.yuantang_index})")
