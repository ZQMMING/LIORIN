# -*- coding: utf-8 -*-
"""修复后验证：化工五行判定矩阵 + 流月锚对齐"""
import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from tongshu.engines.heluo.hua_gong import compute_huagong, HuaGongState
from tongshu.engines.heluo.canonical import _jie_datetime_for_lunar_month

print("=== 化工 has_H & has_O 五行判定（修复后） ===")
cases = [
    # (四卦, 月支, 说明, 期望)
    (("震", "坤", "兑", "坤"), "寅", "春震含兑：兑克震无救", HuaGongState.RESTRAINED),
    (("震", "坤", "兑", "坎"), "寅", "春震含兑+坎水生震：有救", HuaGongState.RESCUED),
    (("震", "坤", "兑", "离"), "寅", "春震含兑+离火克兑：有救", HuaGongState.RESCUED),
    (("坎", "坤", "离", "坤"), "子", "冬坎含离：坎克离化工得势", HuaGongState.RESCUED),
    (("坎", "坤", "离", "震"), "子", "冬坎含离+震木无救（震不克离不生坎）", HuaGongState.RESCUED),
    (("离", "坤", "坎", "坤"), "午", "夏离含坎+坤土克坎水（救应）", HuaGongState.RESCUED),
    (("离", "乾", "坎", "乾"), "午", "夏离含坎+乾金生坎水（助反卦，无救）", HuaGongState.RESTRAINED),
    (("离", "兑", "坎", "兑"), "午", "夏离含坎+兑金（不生离不克坎，无救）", HuaGongState.RESTRAINED),
    (("离", "坤", "坎", "巽"), "午", "夏离含坎+巽木生离：有救", HuaGongState.RESCUED),
    (("离", "坤", "坎", "艮"), "午", "夏离含坎+艮土克坎：有救", HuaGongState.RESCUED),
    (("兑", "坤", "震", "坤"), "酉", "秋兑含震：兑克震化工得势", HuaGongState.RESCUED),
    (("震", "兑", "震", "兑"), "寅", "仅震兑：兑克震无救", HuaGongState.RESTRAINED),
    (("坎", "离", "坎", "离"), "子", "仅坎离：坎克离化工得势", HuaGongState.RESCUED),
]
for (t1, t2, t3, t4), branch, desc, exp in cases:
    r = compute_huagong(t1, t2, t3, t4, branch)
    flag = "OK " if r.state == exp else "**FAIL**"
    print(f"[{flag}] {desc} → {r.state.value} (期望 {exp.value})")
    print(f"       {r.evidence[-1]}")

print()
print("=== 流月节锚对齐（修复后）===")
EXPECT = {1: "12-07大雪", 2: "01-05小寒", 3: "02-04立春", 4: "03-05惊蛰", 5: "04-05清明",
          6: "05-05立夏", 7: "06-05芒种", 8: "07-07小暑", 9: "08-07立秋", 10: "09-07白露",
          11: "10-08寒露", 12: "11-07立冬"}
ok = True
for lm in range(1, 13):
    dt = _jie_datetime_for_lunar_month(2026, lm)
    exp = EXPECT[lm]
    exp_m, exp_d = exp.split("-")[0], exp.split("-")[1][:2]
    got_m, got_d = dt[5:7], dt[8:10]
    flag = "OK " if (got_m == exp_m and got_d == exp_d) else "**FAIL**"
    if flag != "OK ":
        ok = False
    print(f"[{flag}] month={lm:2d} → {dt} (期望 {exp})")
print("ALL JIE ANCHORS PASS" if ok else "JIE ANCHORS FAILED")
