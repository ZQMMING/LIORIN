# -*- coding: utf-8 -*-
"""STEP-DBG-1 回归: 破格 xi_wx 改动前后对比
MODE=pre  还原改动 (xi_wx=_xi_val 无门控)
MODE=post 现状
"""
import sys, os, json, glob, io

D = r"D:/shuntian-ziping-p0"
sys.path.insert(0, D)
sys.path.insert(0, os.path.join(D, "tools"))
MODE = sys.argv[1]
OUT = os.path.join(D, "scripts", "_dbg1_%s.json" % MODE)

if MODE == "pre":
    # 独立进程重跑一遍 pre: 用 monkeypatch 恢复旧行为做不到(在函数体内),
    # 改为直接改文件副本太重 —— 这里用 git HEAD 版本跑
    import subprocess, shutil
    src = os.path.join(D, "engines/common/ge_jie_layer.py")
    bak = src + ".dbg1bak"
    txt = io.open(src, encoding="utf-8-sig").read()
    new = "'xi_wx': [] if _po else _xi_val,\n" + " " * 27 + \
          "'xi_wx_status': ('UNVERIFIED' if _po\n" + " " * 40 + \
          "else ('DEFINED' if _xi_val else 'UNDEFINED')),"
    # 定位我加的那块(从 STEP-DBG-1 注释起)
    i = txt.find("                                           # STEP-DBG-1")
    j = txt.find("'ti_wx': [] if _po else", i)
    old_block = ("'xi_wx': _xi_val,\n" + " " * 27 +
                 "'xi_wx_status': 'DEFINED' if _xi_val else 'UNDEFINED',\n" + " " * 27)
    shutil.copy(src, bak)
    txt2 = txt[:i] + old_block + txt[j:]
    io.open(src, "w", encoding="utf-8", newline="").write(txt2)
    import ast
    ast.parse(txt2)
    print("[pre] 已临时还原 STEP-DBG-1")

from p0_v2.bazi_gate import paipan

CA = os.path.join(D, "p0_v2", "case_audit")
cases = {}
for fp in glob.glob(CA + "/*_clean.jsonl"):
    for l in open(fp, encoding="utf-8-sig"):
        if l.strip():
            d = json.loads(l)
            cases[d["case_id"]] = d

rows = {}
for cid, d in sorted(cases.items()):
    bz = (d.get("bazi") or "").replace(" ", "")
    if not bz:
        continue
    try:
        r = paipan(bz)
    except Exception as e:
        rows[cid] = {"bazi": bz, "ERROR": type(e).__name__}
        continue
    gc = r.get("ge_cheng") or {}
    rows[cid] = {
        "bazi": bz,
        "ge": gc.get("ge"),
        "ti": gc.get("ti_wx") or [],
        "xi": gc.get("xi_wx") or [],
        "xi_status": gc.get("xi_wx_status"),
        "po_n": len(gc.get("po_ge") or []),
        "bing_n": len(r.get("bing_list") or []),
        "bing_ids": sorted(b.get("bing_id") for b in (r.get("bing_list") or [])),
    }

json.dump(rows, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("[%s] 跑完 %d 盘 -> %s" % (MODE, len(rows), OUT))

if MODE == "pre":
    import shutil
    shutil.move(src + ".dbg1bak", src)
    print("[pre] 已恢复 STEP-DBG-1")