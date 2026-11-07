# -*- coding: utf-8 -*-
"""run_case.py —— 单盘调试器(四柱 -> 引擎全层 -> 逐范式体检)

用法:
    python scripts/run_case.py 癸亥壬戌乙未壬午
    python scripts/run_case.py 癸亥壬戌乙未壬午 --full     # 打印全部原始键
    python scripts/run_case.py --batch PZ-0012,PZ-0023      # 批量对照

铁律: 只 sys.path.insert 仓库根, 一律 p0_v2.bazi_gate 完整路径(禁双模块实例)。
"""
import sys, os, json, argparse

ROOT = r"D:/shuntian-ziping-p0"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

from p0_v2.bazi_gate import paipan  # noqa: E402


def dump(bazi, full=False):
    r = paipan(bazi)
    P = print
    P("=" * 96)
    P("四柱 %s" % bazi)
    P("=" * 96)

    P("\n[L0 事实层]")
    for k in ("day_stem", "daymaster_element", "month_branch",
              "month_qi_element", "month_qi_ten_god"):
        P("  %-22s %s" % (k, r.get(k)))
    P("  pillars                %s" % json.dumps(
        r.get("pillars"), ensure_ascii=False))
    P("  hidden (藏干)          %s" % json.dumps(
        r.get("hidden"), ensure_ascii=False))

    P("\n[L1 五行层]  日主状态")
    P("  daymaster_power        %s" % json.dumps(
        r.get("daymaster_power"), ensure_ascii=False, default=str))
    P("  wuxing_power 全部五行   %s" % json.dumps(
        {k: (v or {}).get("ling_state") for k, v in
         (r.get("wuxing_power") or {}).items()}, ensure_ascii=False))

    P("\n[L2 十神层]")
    P("  ten_god                %s" % json.dumps(
        r.get("ten_god"), ensure_ascii=False))

    P("\n[L3 旺衰层 · §2.5 契约字段]")
    P("  l3_contract            %s" % json.dumps(
        {k: v for k, v in (r.get("l3_contract") or {}).items()
         if k not in ("boundary_note", "evidence_refs")}, ensure_ascii=False))

    P("\n[L4 格局层]")
    gc = r.get("ge_cheng") or {}
    for k in ("ge", "ti_wx", "xi_wx", "zhi_wx", "hua_wx",
              "overpower_combo", "rule"):
        P("  %-22s %s" % (k, json.dumps(gc.get(k), ensure_ascii=False, default=str)))
    P("  %-22s %s" % ("po_ge", json.dumps(gc.get("po_ge"), ensure_ascii=False, default=str)))

    P("\n[离散拓扑 · special]")
    sp = r.get("special") or {}
    for k, v in sp.items():
        P("  %-22s %s" % (k, json.dumps(v, ensure_ascii=False, default=str)[:110]))
    P("  %-22s %s" % ("tian_he", json.dumps(
        {k: v for k, v in (r.get("tian_he") or {}).items()
         if k in ("he_pairs", "sanhe_ju", "sanhui_ju")},
        ensure_ascii=False, default=str)[:220]))
    rs = ((r.get("combination_facts") or {}).get("resolved") or {})
    P("  %-22s %s" % ("chong_survive", rs.get("chong_survive")))
    P("  %-22s %s" % ("liuhe_canceled", rs.get("liuhe_canceled")))

    P("\n[P1 病药层]")
    for b in (r.get("bing_list") or []):
        P("  %-22s %-10s 域=%-8s 五行=%-3s 切片=%-28s 依据=%s" % (
            b.get("bing_id"), b.get("name"), b.get("bing_domain", "缺"),
            b.get("bing_wx", "缺"), b.get("slice_id", "缺"),
            str(b.get("classic"))[:34]))
    P("  病机数 %d" % len(r.get("bing_list") or []))

    P("\n[P2 消解 / 用神]")
    P("  bing_debate           %s" % json.dumps(
        r.get("bing_debate"), ensure_ascii=False, default=str)[:300])
    P("  yongyao               %s" % json.dumps(
        r.get("yongyao"), ensure_ascii=False, default=str)[:300])

    P("\n[四范式体检]")
    check_paradigms(r)

    if full:
        P("\n[顶层全部键]")
        for k in sorted(r.keys()):
            P("  %-22s %s" % (k, json.dumps(
                r.get(k), ensure_ascii=False, default=str)[:150]))
    return r


def check_paradigms(r):
    """逐范式实跑体检, 只报引擎实际输出里的事实, 不推断。"""
    P = print
    bad = []

    # 范式1 布尔: 禁浮点/置信度
    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                yield from walk(v, path + "." + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from walk(v, path + "[%d]" % i)
        else:
            yield path, o
    fl = [(p, v) for p, v in walk(r)
          if isinstance(v, float) and any(
              w in p.lower() for w in ("confid", "weight", "score", "prob", "ratio"))]
    P("  1 布尔枚举  浮点/权重类字段: %s" % (fl if fl else "无 ✓"))
    if fl:
        bad.append("浮点/权重字段 %s" % fl[:3])

    # 范式2 序数等级 0-4
    sev = [(p, v) for p, v in walk(r) if "severity" in p.lower()]
    P("  2 序数等级  severity 字段: %s" % (sev if sev else "★ 0 处(§2.8.3 未实现)"))
    if not sev:
        bad.append("severity 未实现(§2.8.3 域内主次序数 0-4)")

    # 范式3 离散拓扑
    nodes = {}
    for k in ("day_stem", "month_branch"):
        nodes[k] = r.get(k)
    pairs = (r.get("tian_he") or {}).get("he_pairs") or []
    chong = ((r.get("combination_facts") or {}).get("resolved") or {}).get("chong_survive") or []
    P("  3 离散拓扑  节点 month_branch=%s 日主=%s | 边: 合%d 冲%d"
      % (nodes["month_branch"], nodes["day_stem"], len(pairs), len(chong)))
    if not nodes["month_branch"]:
        bad.append("month_branch 缺失 -> 拓扑无节点")

    # 范式4 规则优先级: 消解依据可追
    db = r.get("bing_debate") or {}
    P("  4 规则优先级  主病=%s 依据键=%s"
      % (db.get("primary"), sorted(db.keys())))
    if db.get("primary") and not (db.get("key") or db.get("compare_key")):
        bad.append("选了主病但无排序依据")

    # 范式5 切片依据链
    noev = [b.get("bing_id") for b in (r.get("bing_list") or []) if not b.get("evidence")]
    no_slice = [b.get("bing_id") for b in (r.get("bing_list") or [])
                if not (str(b.get("slice_id") or "").count(".") >= 2)]
    P("  5 切片依据链  病机无证据=%s 无切片ID=%s" % (noev or "无", no_slice or "无"))
    if no_slice:
        bad.append("%d 条病机未挂切片ID(§2.7 要求依据链指到切片 ID)" % len(no_slice))

    P("")
    if bad:
        P("  ★ 本盘查出 %d 个问题:" % len(bad))
        for x in bad:
            P("     ✗ %s" % x)
    else:
        P("  ✓ 本盘四范式未查出问题")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bazi", nargs="?", help="四柱, 如 癸亥壬戌乙未壬午")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--batch", help="逗号分隔 case_id, 从 *_clean.jsonl 取")
    a = ap.parse_args()

    if a.batch:
        import glob
        ids = [x.strip() for x in a.batch.split(",") if x.strip()]
        found = {}
        for fp in glob.glob(os.path.join(ROOT, "p0_v2/case_audit/*_clean.jsonl")):
            for line in open(fp, encoding="utf-8-sig"):
                if not line.strip():
                    continue
                d = json.loads(line)
                if d.get("case_id") in ids:
                    found[d["case_id"]] = d
        for cid in ids:
            d = found.get(cid)
            if not d:
                print("!! %s 不在 *_clean.jsonl" % cid)
                continue
            print("\n" + "#" * 96)
            print("## %s  [%s]  %s" % (cid, d.get("book"), d.get("bazi")))
            print("## 原断: %s" % str(d.get("raw"))[:160].replace("\n", " "))
            dump(d["bazi"], a.full)
        return

    if not a.bazi:
        ap.error("给四柱 或 --batch")
    dump(a.bazi, a.full)


if __name__ == "__main__":
    main()