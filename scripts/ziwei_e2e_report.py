#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紫微引擎端到端案例报告器（Z80-I）。

跑「真实案例」并输出**算层 → 辨层 → 解层**全链路整体结果，含：
  · 算层：命宫/身宫/五行局/命主/身主 + 十二宫主辅星亮度 + golden 校对
  · 辨层：南北两派 RuleGraph 命中/未命中 + 跨派一致事实观测
  · 解层：12 人生维度 / 12 宫逐宫 / 8 领域 / 体用层（格局·应期·四化体用）
  · 经典细则层：得地失陷诀 / 格局候选 / 女命 / 童限 / 限运进阶 / 太岁小限 / 辅煞断语
  · 时间层：大限表 / 流年 / 流月 / 流日 + 小限 / 斗君 / 流曜

用法：
    ./.venv/Scripts/python.exe scripts/ziwei_e2e_report.py            # 默认 3 例
    ./.venv/Scripts/python.exe scripts/ziwei_e2e_report.py --n 5
    ./.venv/Scripts/python.exe scripts/ziwei_e2e_report.py --out docs/audit/ziwei_e2e_report.md
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

from tongshu.engines.ziwei_engine import ZiweiEngine  # noqa: E402
from tongshu.engines.ziwei import (  # noqa: E402
    compute_multi_method_signals, build_life_reading, build_answer,
    build_domain_readings, build_classical_detail,
)

# 十二宫规范序（宫位层展示顺序）
PALACE_ORDER = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                "迁移", "仆役", "官禄", "田宅", "福德", "父母"]

# 内置案例（阳历）：(标签, 年, 月, 日, 时, 性别, 目标年)
BUILTIN = [
    ("紫微·黄金集首例", 1990, 3, 1, 0, "female", 2026),
    ("名人案例·毛泽东", 1893, 12, 26, 8, "male", 2026),
    ("边界案例·晚子时", 1983, 9, 29, 23, "female", 2026),
]


def _solar_to_lunar(y, m, d):
    from lunar_python import Solar
    lu = Solar.fromYmd(y, m, d).getLunar()
    return (lu.getYear(), lu.getMonth(), lu.getDay())


def _hour_from_shichen_index(idx: int) -> int:
    """golden 集 ``birth_hour`` 为**时辰索引**（0=子…11=亥），转代表钟点。

    子时(0)→0；丑(1)→2；寅(2)→4；卯(3)→6；…亥(11)→22。
    实测：idx=3 → 命宫子/火六局、idx=6 → 命宫酉/水二局、idx=9 → 命宫午/木三局，
    与 golden 期望逐项吻合。
    """
    return 0 if idx == 0 else idx * 2


def _fmt_transform(t):
    if isinstance(t, str):
        return t
    if isinstance(t, dict):
        return "".join(str(t.get(k, "")) for k in ("star", "sihua", "type"))
    return str(t)


def _print_chart(chart):
    print("  【算层 · 命盘】")
    print(f"    命宫支 {chart.soul_earthly_branch} | 身宫支 {chart.body_earthly_branch} "
          f"| 五行局 {chart.fiveElementsClass}")
    print(f"    命主 {chart.soul_star} | 身主 {chart.body_star} "
          f"| 生年 {chart.birth_year}({chart.natal_year_stem}) | 斗君 {chart.doujun_palace} "
          f"| 大限宫 {chart.decadal_palace}")
    print(f"    生年四化入命宫 {chart.soul_palace_sihua or '—'} "
          f"| 流日命宫 {chart.daily_luck_palace or '—'}")
    print("    十二宫：")
    for pn in PALACE_ORDER:
        p = chart.palaces.get(pn) or {}
        maj = "、".join(p.get("major", []) or []) or "（空宫）"
        mino = "、".join(p.get("minor", []) or [])
        br = p.get("brightness", {}) or {}
        brs = " ".join(f"{k}{v}" for k, v in br.items())
        body = "★身宫" if p.get("isBody") else ""
        print(f"      {pn}({p.get('branch','')}{p.get('stem','')}) {maj}"
              f"{(' + ' + mino) if mino else ''} {brs} {body}")


def _print_golden_check(chart, exp):
    if not exp:
        print("  【算层 · golden 校对】无期望值")
        return
    ok_m = chart.soul_earthly_branch == exp.get("ming_gong_branch")
    ok_s = chart.body_earthly_branch == exp.get("shen_gong_branch")
    ok_w = chart.fiveElementsClass == exp.get("wuxing_ju")
    print(f"  【算层 · golden 校对】命宫 {chart.soul_earthly_branch}"
          f"{'✓' if ok_m else '✗ 期望' + str(exp.get('ming_gong_branch'))} | "
          f"身宫 {chart.body_earthly_branch}{'✓' if ok_s else '✗'} | "
          f"五行局 {chart.fiveElementsClass}{'✓' if ok_w else '✗ 期望' + str(exp.get('wuxing_ju'))}")


def _print_signal(sig):
    print("  【辨层 · 南北两派】")
    print(f"    状态 {sig.compute_status} | 命中合计 {sig.total_matched_rules} "
          f"| 未命中合计 {sig.total_unmatched_production}")
    for mid, b in sig.bundles.items():
        print(f"    {mid}: {b.implementation_status} 命中 {len(b.matched_rules)}/{b.rule_count} "
              f"未命中 {len(b.unmatched_production_rules)}")
    if sig.cross_method_consensus:
        print(f"    跨派一致事实（观测性，不加权）{len(sig.cross_method_consensus)} 条："
              f"{'、'.join(sig.cross_method_consensus[:6])}"
              f"{'…' if len(sig.cross_method_consensus) > 6 else ''}")


def _print_reading(rd):
    print("  【解层 · 12 人生维度】")
    for d in rd.dimensions:
        concl = (d.conclusion or "").replace("\n", " ")
        print(f"    ▸ {d.dimension}｜{d.palace}({d.branch}) "
              f"星:{'、'.join(d.natal_stars) or '—'}｜{concl[:110]}"
              f"{'…' if len(concl) > 110 else ''}")


def _print_domains(dm):
    print("  【解层 · 8 领域聚合】")
    for dr in dm.domain_readings:
        concl = (dr.conclusion or "").replace("\n", " ")
        print(f"    ▸ {dr.domain}｜{concl[:110]}{'…' if len(concl) > 110 else ''}")
    print("  【解层 · 12 宫逐宫】")
    for pr in dm.palace_readings:
        concl = (pr.conclusion or "").replace("\n", " ")
        print(f"    ▸ {pr.palace}｜{'、'.join(pr.stars) or '（空宫借对）'}｜{concl[:100]}"
              f"{'…' if len(concl) > 100 else ''}")


def _print_answer(ans):
    print("  【解层 · 体用层 + 经典细则层】")
    for k, items in ans["body_use"].items():
        print(f"    ▸ 体用·{k}：{len(items)} 条")
    cd = ans.get("classical_detail", {}) or {}
    s = cd.get("summary", {})
    print(f"    ▸ 细则·十二宫得地失陷诀：{s.get('palace_jue',0)} 条")
    for e in cd.get("palace_jue", []):
        print(f"        [{e['kind']} {e['rule_id']}] {e['verbatim'][:60]}…")
    print(f"    ▸ 细则·经典格局候选：{s.get('classical_patterns',0)} 条"
          f"（{'、'.join(x['pattern_name'] for x in cd.get('classical_patterns',[])) or '—'}）")
    if cd.get("nvming"):
        print(f"    ▸ 细则·女命专条：{s.get('nvming',0)} 条"
              f"（{'、'.join(x['rule_id']+':'+x['polarity'] for x in cd['nvming'])}）")
    print(f"    ▸ 细则·童限/十二宫强弱：{s.get('child_limit',0)} 条"
          f"（{'、'.join(x['rule_id'] for x in cd.get('child_limit',[])) or '—'}）")
    print(f"    ▸ 细则·限运进阶：{s.get('limit_advanced',0)} 条"
          f"（{'、'.join(x['rule_id'] for x in cd.get('limit_advanced',[])) or '—'}）")
    print(f"    ▸ 细则·太岁小限：{s.get('temporal_rules',0)} 条")
    print(f"    ▸ 细则·辅煞杂曜断语：{s.get('aux_verdicts',0)} 条")
    tf = cd.get("temporal_facts", {}) or {}
    if tf:
        print(f"    ▸ 细则·时间层 Fact：生年{tf.get('birth_year_ganzhi','')} "
              f"流年{tf.get('flow_year_ganzhi','')} 太岁宫{tf.get('taisui_palace','—')} "
              f"小限宫{tf.get('xiaoxian_palace','—')} 斗君{tf.get('doujun_palace','—')} "
              f"流曜{tf.get('flow_stars','')}")


def _print_time_layer(rd):
    print("  【时间层 · 大限/流年/流月/流日】")
    dt = getattr(rd, "decadal_table", None)
    if dt:
        print(f"    大限表 {len(dt)} 步：")
        for x in dt:
            pn = getattr(x, "palace_name", "?")
            sa = getattr(x, "start_age", "?")
            ea = getattr(x, "end_age", "?")
            st = getattr(x, "stem", "")
            br = getattr(x, "branch", "")
            stars = "、".join(getattr(x, "stars", []) or [])
            print(f"      {sa:>2}-{ea:>2}岁 {pn}({br}{st}) {stars}")
    # 流年四化：{year: [禄,权,科,忌]}
    at = getattr(rd, "annual_transforms", None)
    if isinstance(at, dict) and at:
        for y, stars in at.items():
            labels = ["禄", "权", "科", "忌"]
            s = "、".join(
                f"{st}化{labels[i] if i < 4 else '?'}" for i, st in enumerate(stars))
            print(f"    流年 {y} 四化: {s}")
    elif at:
        print(f"    流年四化: {at}")
    for name, attr in (("流月四化", "monthly_transforms"),
                       ("流日四化", "daily_transforms")):
        v = getattr(rd, attr, None)
        if v:
            s = "；".join(_fmt_transform(x) for x in (v if isinstance(v, list) else [v]))
            print(f"    {name}: {s[:120]}")


def run_case(engine, tag, y, m, d, h, gender, target_year, expected=None):
    print("=" * 78)
    print(f"案例：{tag}｜阳历 {y}-{m:02d}-{d:02d} {h:02d}时｜{gender}｜目标年 {target_year}")
    print("=" * 78)
    lunar = _solar_to_lunar(y, m, d)
    print(f"  （农历 {lunar[0]}-{lunar[1]:02d}-{lunar[2]:02d}）")
    chart = engine.full_chart(lunar, h, gender, flow_year=target_year)
    _print_chart(chart)
    _print_golden_check(chart, expected)
    sig = compute_multi_method_signals(chart)
    _print_signal(sig)
    rd = build_life_reading(chart, sig, target_year=target_year)
    _print_reading(rd)
    _print_time_layer(rd)
    dm = build_domain_readings(chart, engine.get_all_zihua(chart))
    _print_domains(dm)
    ans = build_answer(chart)
    _print_answer(ans)
    print()


def run_golden_all(engine, out_lines=None):
    """跑全部 golden 案例，统计算层三项（命宫/身宫/五行局）+ 十二宫主星匹配率。"""
    import json
    gs_path = REPO / "cases" / "golden" / "ziwei_golden_set.json"
    if not gs_path.exists():
        print("未找到 golden 集")
        return
    gs = json.loads(gs_path.read_text(encoding="utf-8"))
    print("=" * 78)
    print(f"golden 全量校对：{len(gs)} 例（算层三项 + 十二宫主星）")
    print("=" * 78)
    ok = {"ming": 0, "shen": 0, "wuxing": 0, "palaces": 0}
    total = len(gs)
    fails = []
    for case in gs:
        inp = case["input"]
        exp = case.get("expected_calculation") or {}
        lunar = _solar_to_lunar(inp["birth_year"], inp["birth_month"], inp["birth_day"])
        try:
            ch = engine.full_chart(
                lunar, _hour_from_shichen_index(inp["birth_hour"]), inp["gender"])
        except Exception as e:
            fails.append((case["case_id"], f"计算异常 {type(e).__name__}"))
            continue
        m_ok = ch.soul_earthly_branch == exp.get("ming_gong_branch")
        s_ok = ch.body_earthly_branch == exp.get("shen_gong_branch")
        w_ok = ch.fiveElementsClass == exp.get("wuxing_ju")
        ok["ming"] += m_ok
        ok["shen"] += s_ok
        ok["wuxing"] += w_ok
        # 十二宫主星
        p_ok = True
        for ep in exp.get("palaces", []):
            got = ch.palaces.get(ep["name"]) or {}
            if sorted(got.get("major", []) or []) != sorted(ep.get("major_stars", []) or []):
                p_ok = False
                break
        ok["palaces"] += p_ok
        if not (m_ok and s_ok and w_ok and p_ok):
            fails.append((case["case_id"],
                          f"命宫{'✓' if m_ok else '✗'} 身宫{'✓' if s_ok else '✗'} "
                          f"五行局{'✓' if w_ok else '✗'} 十二宫{'✓' if p_ok else '✗'}"))
    print(f"  命宫地支   {ok['ming']}/{total}")
    print(f"  身宫地支   {ok['shen']}/{total}")
    print(f"  五行局     {ok['wuxing']}/{total}")
    print(f"  十二宫主星 {ok['palaces']}/{total}")
    print(f"  四项全对   {total - len(fails)}/{total}")
    if fails:
        print("  ── 未全对案例（前 10）──")
        for cid, why in fails[:10]:
            print(f"    {cid}: {why}")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3, help="运行案例数（取自内置 + golden 集）")
    ap.add_argument("--golden-all", action="store_true", help="跑 golden 全量校对")
    ap.add_argument("--out", type=str, default="", help="同时写入 markdown 报告")
    args = ap.parse_args()

    engine = ZiweiEngine()
    lines: list = []

    class _Tee:
        def __init__(self, *streams):
            self._streams = streams

        def write(self, s):
            for st in self._streams:
                st.write(s)
            lines.append(s)

        def flush(self):
            for st in self._streams:
                st.flush()

    old_stdout = sys.stdout
    sys.stdout = _Tee(old_stdout)
    try:
        print("#" * 78)
        print("# 紫微引擎端到端案例报告 — 算层 → 辨层 → 解层 全链路")
        print("#" * 78)
        print()

        # 1) 内置案例
        for tag, y, m, d, h, g, ty in BUILTIN[:args.n]:
            run_case(engine, tag, y, m, d, h, g, ty)

        # 2) golden 集（带期望值，做算层校对）
        gs_path = REPO / "cases" / "golden" / "ziwei_golden_set.json"
        if gs_path.exists() and args.n > len(BUILTIN):
            import json
            gs = json.loads(gs_path.read_text(encoding="utf-8"))
            need = args.n - len(BUILTIN)
            for case in gs[:need]:
                inp = case["input"]
                run_case(engine, case["case_id"], inp["birth_year"], inp["birth_month"],
                         inp["birth_day"], _hour_from_shichen_index(inp["birth_hour"]),
                         inp["gender"], 2026, expected=case.get("expected_calculation"))

        # 3) golden 全量校对
        if args.golden_all:
            run_golden_all(engine)
    finally:
        sys.stdout = old_stdout

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = REPO / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        body = "".join(lines)
        md = ("---\ntitle: 紫微引擎端到端案例报告\n---\n\n```\n" + body + "```\n")
        out_path.write_text(md, encoding="utf-8")
        print(f"\n[已写入] {out_path}")


if __name__ == "__main__":
    main()
