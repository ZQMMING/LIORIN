# -*- coding: utf-8 -*-
"""步3+4 验收: six_dims 已删 / l3_contract 5+3 字段仍在 / diag 脚本可跑

★ 独立进程跑(禁 execute_code 持久 kernel)—— 双路径 import 陷阱。
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

L3K = ["chong_adjust", "chong_role", "chong_by", "library_open", "ling_state_eff"]
B3 = ["de_ling", "de_di", "dang_duo"]
BYELEM = ["root_detail", "ben_n", "zhong_n", "yu_n", "ju_n", "banhe_n", "stem_n", "ling_state"]


def main():
    st = collections.Counter()
    n = 0
    for bk in ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            n += 1
            r = paipan(bz)
            wm = r.get("wangshuai_matrix") or {}
            lc = r.get("l3_contract") or {}
            # ① six_dims 键必须消失
            st["six_dims 已消失" if "six_dims" not in wm else "★six_dims 仍在"] += 1
            st["note 已消失" if "note" not in wm else "★note 仍在"] += 1
            # ② L1 出口仍在
            for k in ("dm_row", "yin_row", "by_element", "branch_chong", "month_chong"):
                st["保留 %s" % k if k in wm else "★%s 丢失" % k] += 1
            # ③ l3_contract 8 字段仍在
            for k in L3K + B3:
                st["l3 有 %s" % k if k in lc else "★l3 缺 %s" % k] += 1
            # ④ by_element[日主] 含 diag 脚本要读的 8 字段
            dmwx = wm.get("daymaster_element") or ""
            row = (wm.get("by_element") or {}).get(dmwx) or {}
            for k in BYELEM:
                st["by_element 有 %s" % k if k in row else "★by_element 缺 %s" % k] += 1
    print("=" * 92)
    print("步3+4 验收   六本 %d 盘" % n)
    print("=" * 92)
    for k in sorted(st):
        mark = "" if not k.startswith("★") else "   <<<"
        print("    %-30s %6d%s" % (k, st[k], mark))
    bad = sum(v for k, v in st.items() if k.startswith("★"))
    print("\n  异常总数 = %d" % bad)

    # ⑤ diag_base_matrix.py 可跑
    print("\n" + "=" * 92)
    print("⑤ diag_base_matrix.py 实跑 (six_dims 已删, 改读 by_element[dwx])")
    print("=" * 92)
    import subprocess
    PY = r"C:/Users/ming/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe"
    pr = subprocess.run([PY, os.path.join(ROOT, "scripts", "diag_base_matrix.py")],
                        cwd=ROOT, capture_output=True, text=True, timeout=900)
    tail = [x for x in pr.stdout.strip().split("\n") if x.strip()][-12:]
    print("\n".join("    " + x for x in tail))
    if pr.returncode != 0:
        print("    ★ 退出码 %d" % pr.returncode)
        print("    " + (pr.stderr or "")[-500:])
    else:
        print("    ✓ 退出码 0")
    print("\n  ★ _v12.py 是否已删: %s" % ("已删" if not os.path.exists(
        os.path.join(ROOT, "scripts", "_v12.py")) else "★仍在"))


if __name__ == "__main__":
    main()