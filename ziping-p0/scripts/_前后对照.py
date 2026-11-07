# -*- coding: utf-8 -*-
import os, json, sys, glob, re
ROOT = "D:/shuntian-ziping-p0"
live = json.load(open(os.path.join(ROOT, "scripts", "_引擎活死_运行时.json"), encoding="utf-8"))["live"]
arch = os.path.join(ROOT, "engines", "_archive")
arch_files = [f for f in os.listdir(arch) if f.endswith(".py")]

print("condition_normalizer 在活39?", "common.condition_normalizer" in live)
print("climate_producer_v2 在活39?", "common.climate_producer_v2" in live)
live_bns = {m.split(".")[-1] for m in live}
leak = arch_names = set(arch_files)
leak = leak.intersection(live_bns)
print(f"归档23件 与 活39 basename 交集 = {leak if leak else '0 (无误删活模块)'}")

TOP = {"cong_ge_predicate.py", "huaqi_predicate.py", "yongshen_v3.py", "zhuanwang_predicate.py",
       "ziping_engine_v2.py", "special_pan.py", "cong_ge_graph.py", "huaqi_graph.py", "zhuanwang_graph.py"}

def run_live():
    for k in [m for m in list(sys.modules) if m.startswith("engines")]:
        del sys.modules[k]
    p2 = os.path.join(ROOT, "p0_v2")
    if p2 in sys.path:
        sys.path.remove(p2)
    sys.path.insert(0, ROOT)
    from p0_v2.bazi_gate import paipan
    out = {}
    for bz in ["甲寅 丁卯 戊辰 己未", "辛巳 丁酉 丁酉 辛丑", "丁卯 壬寅 庚午 丙戌",
               "癸卯 甲寅 庚午 丙戌", "辛丑 丁酉 丁巳 丁未", "戊寅 甲寅 甲寅 庚午",
               "戊戌 丁巳 甲寅 己巳", "癸酉丁巳己卯甲戌"]:
        r = paipan(bz)
        out[bz] = {
            "ge": (r.get("ge_cheng", {}).get("ge") if isinstance(r.get("ge_cheng"), dict) else r.get("ge_cheng")),
            "ling": r.get("daymaster_power", {}).get("ling_state"),
            "bing": r.get("bing_yao", {}).get("bing_count"),
            "cong": r.get("special_pattern", {}).get("cong_type"),
        }
    return out

# 放回
for f in arch_files:
    target = os.path.join(ROOT, "engines", f) if f in TOP else os.path.join(ROOT, "engines", "common", f)
    if not os.path.exists(target):
        os.rename(os.path.join(arch, f), target)
before = run_live()
# 再归档
for f in arch_files:
    src = os.path.join(ROOT, "engines", f) if f in TOP else os.path.join(ROOT, "engines", "common", f)
    if os.path.exists(src):
        os.rename(src, os.path.join(arch, f))
after = run_live()

diff = {k: (before[k], after[k]) for k in before if before[k] != after[k]}
print("\n=== 前后对照(放回 vs 归档, 活链8盘) ===")
if not diff:
    print("零变化 ✓")
else:
    print(f"* 有 {len(diff)} 盘变化: {diff}")
for k in ["ge", "ling", "bing", "cong"]:
    same = all(before[x][k] == after[x][k] for x in before)
    print(f"  {k}: {'全同 ok' if same else '有异 NG'}")
# 最终留在归档
print("\n最终 engines/_archive/ :", sorted(os.listdir(arch)))
