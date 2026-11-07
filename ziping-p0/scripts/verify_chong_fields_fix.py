# -*- coding: utf-8 -*-
"""裁四十九甲 验收: 5 冲激字段取值源修正(月令行 vs 日主行)

★ 独立进程跑(禁 execute_code 持久 kernel)—— 双路径 import 陷阱。
  修正前: bazi_gate.py 用 _dmp(=_wpd[日主五行]) 读 5 冲激字段,
          而 transit_power.py:269 只在【月令五行】行赋值
          → 日主五行 != 月令五行的盘, 5 字段恒 None
  修正后: 改从 _dmp_month(=_wpd[月令五行]) 取
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]
CHONG_KEYS = ["chong_adjust", "chong_role", "chong_by",
              "library_open", "ling_state_eff"]


def main():
    st = collections.Counter()
    n = 0
    crash = 0
    lc_keys = collections.Counter()
    for bk in BOOKS:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            n += 1
            try:
                r = paipan(bz)
            except Exception as e:
                crash += 1
                if crash <= 3:
                    print("  崩溃 %s %s: %s" % (d["case_id"], bz, e))
                continue
            lc = r.get("l3_contract") or {}
            lc_keys[len(lc)] += 1
            dm = r.get("daymaster_element", "")
            mw = r.get("month_qi_element", "")
            st["日主==月令"] += (dm == mw)
            st["日主!=月令"] += (dm != mw)
            for k in CHONG_KEYS:
                v = lc.get(k, "__MISSING__")
                st["%s: None" % k] += (v is None)
                st["%s: MISSING" % k] += (v == "__MISSING__")
            # 关键: 日主!=月令的盘, 5 字段是否还有值
            if dm != mw:
                st["不等盘_5字段全有值"] += all(
                    lc.get(k) is not None for k in CHONG_KEYS)

    print("=" * 92)
    print("裁四十九甲 验收   六本 %d 盘   崩溃 %d" % (n, crash))
    print("=" * 92)

    print("\n【l3_contract 键数分布】")
    for k in sorted(lc_keys):
        print("    %d 键   %6d 盘" % (k, lc_keys[k]))

    print("\n【日主 vs 月令】")
    print("    日主==月令   %6d  (%.1f%%)" % (st["日主==月令"],
                                              st["日主==月令"] * 100.0 / n))
    print("    日主!=月令  %6d  (%.1f%%)" % (st["日主!=月令"],
                                              st["日主!=月令"] * 100.0 / n))

    print("\n【5 冲激字段: None / 缺键 计数】")
    for k in CHONG_KEYS:
        print("    %-16s None=%-6d 缺键=%d"
              % (k, st["%s: None" % k], st["%s: MISSING" % k]))

    print("\n【核心: 日主!=月令 的盘, 5 字段是否全有值】")
    print("    全有值 %d / %d  (%.1f%%)"
          % (st["不等盘_5字段全有值"], st["日主!=月令"],
             st["不等盘_5字段全有值"] * 100.0 / max(st["日主!=月令"], 1)))
    print("    ★ 修正前该比率为 0% (恒 None)")


if __name__ == "__main__":
    main()