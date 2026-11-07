# -*- coding: utf-8 -*-
"""L4 引用行号修正 —— pre/post 基线对比
只改 classic/注释里的行号字符串, 判定逻辑一行不动。
MODE=pre|post 跑全量 2106, 落 ge_cheng/ge/ti_wx/xi_wx/po_ge + 病机数
"""
import sys, os, io, json, glob

ROOT = r"D:/shuntian-ziping-p0"
MODE = sys.argv[1]
OUT = os.path.join(ROOT, "scripts", "_l4_%s.json" % MODE)

sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan  # noqa: E402

CA = os.path.join(ROOT, "p0_v2", "case_audit")
rows = {}
for bk in ["DTS", "PZZQ", "QTBJ", "YHZP", "SMTH", "SFTK"]:
    fp = os.path.join(CA, bk + "_clean.jsonl")
    if not os.path.exists(fp):
        continue
    for line in open(fp, encoding="utf-8-sig"):
        if not line.strip():
            continue
        d = json.loads(line)
        bz = (d.get("bazi") or "").replace(" ", "")
        if len(bz) != 8:
            continue
        try:
            r = paipan(bz)
        except Exception as e:
            rows[d["case_id"]] = {"bazi": bz, "ERROR": type(e).__name__}
            continue
        gc = r.get("ge_cheng") or {}
        sp = r.get("special") or {}
        rows[d["case_id"]] = {
            "bazi": bz,
            "ge": gc.get("ge"),
            "ti": gc.get("ti_wx") or [],
            "xi": gc.get("xi_wx") or [],
            "xi_status": gc.get("xi_wx_status"),
            "po_n": len(gc.get("po_ge") or []),
            "cong": sp.get("cong_type"),
            "cong_state": sp.get("cong_state"),
            "zw": sp.get("zhuanwang"),
            "bing_n": len(r.get("bing_list") or []),
            "bing_ids": sorted(b.get("bing_id") for b in (r.get("bing_list") or [])),
            "rule": str(gc.get("rule"))[:400],
        }
json.dump(rows, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("[%s] %d 盘 -> %s" % (MODE, len(rows), OUT))