# -*- coding: utf-8 -*-
"""落码步2 验收: l3_contract 5 冲激字段 == six_dims 同名字段

★ 必须独立进程跑(禁 execute_code 持久 kernel)——
  双路径 import 陷阱会让 kernel 里缓存旧模块, 产出假差异。
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)          # ★ 与 tools/gate.py 同口径: 只插 ROOT
from p0_v2.bazi_gate import paipan

K5 = ["chong_adjust", "chong_role", "chong_by", "library_open", "ling_state_eff"]


def main():
    st = collections.Counter()
    samples = []
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
            lc = r.get("l3_contract") or {}
            six = (r.get("wangshuai_matrix") or {}).get("six_dims") or {}
            for k in K5:
                if k not in lc:
                    st["★%s 键缺失" % k] += 1
                elif lc.get(k) == six.get(k):
                    st["%s 一致" % k] += 1
                else:
                    st["★%s 不一致" % k] += 1
                    if len(samples) < 4:
                        samples.append((d["case_id"], bz, k,
                                        repr(six.get(k)), repr(lc.get(k))))
    print("=" * 92)
    print("落码步2  l3_contract 5字段 == six_dims 同名字段   六本 %d 盘" % n)
    print("=" * 92)
    for k in K5:
        print("  %-18s 一致 %5d   ★不一致 %4d   ★缺键 %4d"
              % (k, st["%s 一致" % k], st["★%s 不一致" % k], st["★%s 键缺失" % k]))
    tot = sum(st["★%s 不一致" % k] + st["★%s 键缺失" % k] for k in K5)
    print("\n  差异总数 = %d" % tot)
    for s in samples:
        print("   ", s)


if __name__ == "__main__":
    main()