# -*- coding: utf-8 -*-
"""基线更新(判据修正后): 100盘基线快照 + 变更明细留档."""
import sys, os, json, io
ROOT = r"D:\shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_p0 = os.path.join(ROOT, "p0_v2")
if _p0 in sys.path:
    sys.path.remove(_p0)
from p0_v2.bazi_gate import paipan

CA = os.path.join(ROOT, "p0_v2", "case_audit")
bp = os.path.join(CA, "_100盘_base_regen2.json")
old = json.load(open(bp, encoding="utf-8"))
chg = []
for c in old["cases"]:
    r = paipan(c["bazi"])
    gc = r.get("ge_cheng") or {}
    ysd = r.get("yongshen_decision") or {}
    if gc.get("ge") != c.get("ge"):
        chg.append((c["bazi"], c.get("ge"), gc.get("ge")))
    c["ge"] = gc.get("ge")
    c["xi_wx"] = gc.get("xi_wx")
    c["winner_shen"] = ysd.get("winner_shen")
json.dump(old, open(bp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with io.open(os.path.join(CA, "_100盘基线变更_V786.txt"), "w", encoding="utf-8") as f:
    f.write("V7.106 基线更新: 病药药方按日主派生(旧固定字面仅对木日主成立)\n")
    f.write("  依据 SFTK L129「何以为之药? ...八字原有所害之一字, 而得一字以去之」—— 药五行随日主而变\n")
    f.write("  影响: 财多身弱/泄气太重等病之药方修正后, 原被误消之病复现(病数上升属正确方向)\n")
    f.write("\n逐盘变更:\n")
    for bz, o, n in chg:
        f.write("  %-20s %s -> %s\n" % (bz, o, n))
    f.write("共 %d 盘\n" % len(chg))
print("基线已更新, 变更 %d 盘" % len(chg))
