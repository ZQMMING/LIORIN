#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紫微引擎健康检查 — 三层架构接线与产出完整性。

目的
----
回答「紫微引擎是否真的搞好了」。不看 git 状态，只看引擎自身：
  算层（iztro 排盘） → 辨层（Signal/RuleGraph） → 解层（断语/文案）
三层是否真的串起来了，各层产出是否完整、非空、可被下游消费。

检查项
------
  A. 算层：排盘事实是否完整（宫/星/四化/自化）
  B. 辨层：南北两派信号是否产出
  C. 解层-宫位维：answer_layer 十二宫位维 + 体用层（格局/应期/四化体用）
  D. 解层-12维：interpretation 十二维断语
  E. 解层-领域：domain_reading 十二宫 + 领域聚合
  F. 接线：各层是否有生产调用方（防范「库里存在但无人调用」）
  G. 唯一入口：是否存在统一对外入口

用法
----
    D:/shuntian/.venv/Scripts/python.exe scripts/ziwei_engine_health.py
    D:/shuntian/.venv/Scripts/python.exe scripts/ziwei_engine_health.py --json out.json

设计约束
--------
- 只读：不修改引擎、不改规则、不写 Golden
- 可复跑：同一输入必得同一输出
- 不粉饰：发现问题如实列为 FAIL/WARN
"""
from __future__ import annotations

import argparse
import ast
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
sys.path.insert(0, str(SRC))
logging.disable(logging.CRITICAL)

SAMPLE_LUNAR = (1983, 9, 29)
SAMPLE_HOUR = 12
SAMPLE_GENDER = "female"

results: list[dict] = []


def check(section: str, name: str, ok: bool, detail: str = "",
          level: str = "FAIL") -> None:
    results.append({
        "section": section,
        "name": name,
        "status": "PASS" if ok else level,
        "detail": detail,
    })


# ── A. 算层 ────────────────────────────────────────────────────────────

def check_calculation() -> dict | None:
    from tongshu.engines.ziwei_engine import ZiweiEngine

    eng = ZiweiEngine()
    try:
        chart = eng.full_chart(SAMPLE_LUNAR, SAMPLE_HOUR, SAMPLE_GENDER)
    except Exception as e:
        check("A.算层", "排盘可执行", False, f"{type(e).__name__}: {e}")
        return None

    check("A.算层", "排盘可执行", True, f"source={chart.source}")

    palaces = chart.palaces
    check("A.算层", "十二宫齐全", len(palaces) == 12, f"实得 {len(palaces)} 宫")

    with_major = [p for p, d in palaces.items() if d.get("major")]
    check("A.算层", "有主星宫位", len(with_major) > 0, f"{len(with_major)} 宫有主星")

    star_detail_ok = all("starDetail" in d for d in palaces.values())
    check("A.算层", "starDetail 字段齐全", star_detail_ok)

    # 四化
    try:
        sihua = eng.get_sihua_palaces(chart, "癸")
        check("A.算层", "生年四化可取", len(sihua) > 0, f"{sihua}")
    except Exception as e:
        check("A.算层", "生年四化可取", False, str(e))

    # 自化
    try:
        zihua = eng.get_all_zihua(chart)
        check("A.算层", "自化可取", isinstance(zihua, dict), f"{len(zihua)} 宫有自化")
    except Exception as e:
        check("A.算层", "自化可取", False, str(e))

    return chart


# ── B. 辨层 ────────────────────────────────────────────────────────────

def check_signal(chart) -> dict | None:
    try:
        from tongshu.engines.ziwei.rules.multi_method import (
            compute_multi_method_signals,
        )
        sig = compute_multi_method_signals(chart)
    except Exception as e:
        check("B.辨层", "多方法信号可计算", False, f"{type(e).__name__}: {e}")
        return None

    check("B.辨层", "多方法信号可计算", True,
          f"matched={sig.total_matched_rules} "
          f"bundles={len(sig.bundles)} "
          f"status={sig.compute_status}")

    total = getattr(sig, "total_matched_rules", 0)
    check("B.辨层", "信号非空", total > 0, f"命中规则数={total}")

    bundles = getattr(sig, "bundles", []) or []
    check("B.辨层", "方法束产出", len(bundles) > 0, f"{len(bundles)} 束")

    consensus = getattr(sig, "cross_method_consensus", None)
    check("B.辨层", "跨方法共识字段存在", consensus is not None,
          f"共识={consensus if not isinstance(consensus, dict) else len(consensus)}",
          "WARN")
    return sig


# ── C. 解层-宫位维+体用层（Z80-E：12 宫位维 / 3 体用项分层）────────────

def check_answer_layer(chart) -> None:
    try:
        from tongshu.engines.ziwei.rules.answer_layer import (
            BODY_USE_KEYS,
            PALACE_DIMENSIONS,
            build_answer,
        )
        ans = build_answer(chart)
    except Exception as e:
        check("C.解层宫位维", "answer_layer 可执行", False,
              f"{type(e).__name__}: {e}")
        return

    check("C.解层宫位维", "answer_layer 可执行", True)
    check("C.解层宫位维", "维度数 == 12",
          len(ans.get("dimensions", [])) == 12,
          f"{ans.get('dimensions')}")
    check("C.解层宫位维", "维度名单 == 十二宫",
          list(ans.get("dimensions", [])) == PALACE_DIMENSIONS,
          f"{ans.get('dimensions')}")
    check("C.解层宫位维", "体用层字段存在",
          set(ans.get("body_use", {}).keys()) == set(BODY_USE_KEYS),
          f"{sorted(ans.get('body_use', {}).keys())}")

    counts = ans.get("summary", {}).get("dimension_counts", {})
    empty_dims = [d for d, c in counts.items() if c == 0]
    # Z80-E 验收：12 宫位维不得有空桶
    empty_palace = [d for d in PALACE_DIMENSIONS if counts.get(d, 0) == 0]
    check("C.解层宫位维", "12 宫位维均有答案", not empty_dims,
          f"空维度={empty_dims}" if empty_dims else f"计数={counts}", "WARN")
    check("C.解层宫位维", "12 宫位维无空桶", not empty_palace,
          f"空宫位维={empty_palace}" if empty_palace else "12/12 有内容", "FAIL")

    bcounts = ans.get("summary", {}).get("body_use_counts", {})
    empty_body = [k for k in BODY_USE_KEYS if bcounts.get(k, 0) == 0]
    check("C.解层宫位维", "体用层非空", not empty_body,
          f"空体用项={empty_body}" if empty_body else f"计数={bcounts}")

    # 接线：是否有生产调用方
    callers = _find_callers("build_answer")
    check("C.解层宫位维", "有生产调用方", bool(callers),
          f"调用方={callers}" if callers else
          "仅在测试中可达（库里存在但生产链路未接）", "FAIL")


# ── C2. 宫位维/十二维对齐（Z80-E）─────────────────────────────────────

def check_alignment(chart, sig) -> None:
    """检查 12 宫位维与 12 人生维度是否对齐（一宫一维，1:1 直连）。"""
    try:
        from tongshu.engines.ziwei.rules.answer_layer import build_answer
        from tongshu.engines.ziwei.rules.dimension_bridge import (
            align_answer_to_dimensions,
        )
        ans = build_answer(chart)
        al = align_answer_to_dimensions(ans)
    except Exception as e:
        check("C2.维度对齐", "对齐桥可执行", False,
              f"{type(e).__name__}: {e}")
        return

    check("C2.维度对齐", "对齐桥可执行", True)

    unmapped = al.coverage.get("unmapped_dimensions", [])
    check("C2.维度对齐", "12 宫位维全部有归宿", not unmapped,
          f"未归位={unmapped}" if unmapped else "12/12 归位")

    check("C2.维度对齐", "条目已投射", al.coverage.get("mapped_items", 0) > 0,
          f"mapped={al.coverage.get('mapped_items')} "
          f"cross={al.coverage.get('cross_items')}")

    # Z80-E 核心验收：12 维全覆盖，无空维
    empty = al.coverage.get("reading_dimensions_empty", [])
    check("C2.维度对齐", "12 维全覆盖无空维", not empty,
          f"空维={empty}" if empty else "12/12 覆盖", "FAIL")

    # 体用层内容须全部进跨维池（不丢信息）
    n_body = sum(len(v) for v in ans.get("body_use", {}).values())
    check("C2.维度对齐", "体用层内容进跨维池",
          al.coverage.get("cross_items", 0) == n_body,
          f"body_use={n_body} cross={al.coverage.get('cross_items')}")

    # 接线：reading 是否携带对齐结果
    try:
        from tongshu.engines.ziwei.rules.interpretation import build_life_reading
        reading = build_life_reading(chart, sig, target_year=2026)
        check("C2.维度对齐", "reading 已携带对齐结果",
              reading.answer_alignment is not None,
              f"覆盖 {len(al.coverage.get('reading_dimensions_covered', []))}/12 维")
    except Exception as e:
        check("C2.维度对齐", "reading 已携带对齐结果", False, str(e))


# ── D. 解层-12维 ───────────────────────────────────────────────────────

def check_interpretation(chart, sig) -> None:
    try:
        from tongshu.engines.ziwei.rules.interpretation import build_life_reading
        reading = build_life_reading(chart, sig, target_year=2026)
    except Exception as e:
        check("D.解层12维", "build_life_reading 可执行", False,
              f"{type(e).__name__}: {e}")
        return

    check("D.解层12维", "build_life_reading 可执行", True)

    dims = reading.dimensions
    check("D.解层12维", "维度数 == 12", len(dims) == 12, f"实得 {len(dims)}")

    empty = [d.dimension for d in dims if not (d.conclusion or "").strip()]
    check("D.解层12维", "十二维断语非空", not empty,
          f"空维度={empty}" if empty else "12/12 非空")

    with_zihua = [d for d in dims if "自化" in (d.conclusion or "")]
    check("D.解层12维", "自化解读已接入", len(with_zihua) > 0,
          f"{len(with_zihua)}/12 维含自化")

    check("D.解层12维", "min_method 大运表存在", bool(reading.decadal_table),
          f"{len(reading.decadal_table)} 步大运", "WARN")


# ── E. 解层-领域 ───────────────────────────────────────────────────────

def check_domain(chart) -> None:
    try:
        from tongshu.engines.ziwei.rules.domain_reading import (
            DOMAIN_PALACES,
            build_domain_readings,
        )
        from tongshu.engines.ziwei_engine import ZiweiEngine
        zm = ZiweiEngine().get_all_zihua(chart)
        out = build_domain_readings(chart, zm)
    except Exception as e:
        check("E.解层领域", "domain_reading 可执行", False,
              f"{type(e).__name__}: {e}")
        return

    check("E.解层领域", "domain_reading 可执行", True)
    check("E.解层领域", "十二宫逐宫解读", len(out.palace_readings) == 12,
          f"实得 {len(out.palace_readings)}")

    nd = len(out.domain_readings)
    check("E.解层领域", "领域聚合产出", nd >= 6, f"实得 {nd} 个领域")

    empty = [d.domain for d in out.domain_readings
             if not d.conclusion.strip()]
    check("E.解层领域", "领域结论非空", not empty,
          f"空领域={empty}" if empty else f"{nd}/{nd} 非空")

    # 十二宫是否全部归属领域
    canonical = {"命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                 "迁移", "官禄", "田宅", "福德", "父母", "仆役"}
    covered = set()
    from tongshu.engines.ziwei.rules.domain_reading import PALACE_ALIAS
    for palaces in DOMAIN_PALACES.values():
        for p in palaces:
            covered.add(PALACE_ALIAS.get(p, p))
    missing = canonical - covered
    check("E.解层领域", "十二宫全归属领域", not missing,
          f"未归属={sorted(missing)}" if missing else "12/12 覆盖")


# ── F/G. 接线与入口 ────────────────────────────────────────────────────

def _find_callers(func_name: str) -> list[str]:
    """在 src/ 下查找对 func_name 的调用（排除定义处与自文件）。"""
    callers = []
    for py in SRC.rglob("*.py"):
        if "__pycache__" in str(py):
            continue
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if re.search(rf"\b{re.escape(func_name)}\s*\(", text):
            # 排除定义行
            if re.search(rf"def\s+{re.escape(func_name)}\s*\(", text):
                others = [ln for ln in text.splitlines()
                          if re.search(rf"\b{re.escape(func_name)}\s*\(", ln)
                          and not re.match(rf"\s*def\s+{re.escape(func_name)}", ln)]
                if not others:
                    continue
            callers.append(str(py.relative_to(REPO)))
    return callers


def check_wiring() -> None:
    for fn, label in [
        ("build_answer", "answer_layer.build_answer"),
        ("build_life_reading", "interpretation.build_life_reading"),
        ("build_domain_readings", "domain_reading.build_domain_readings"),
        ("compute_multi_method_signals", "multi_method.compute_multi_method_signals"),
    ]:
        callers = [c for c in _find_callers(fn)
                   if "tests/" not in c and "scripts/" not in c]
        check("F.接线", f"{label} 有 src 调用方", bool(callers),
              f"→ {callers}" if callers else "无 src 内调用方", "WARN")

    # 统一入口
    init_f = SRC / "tongshu" / "engines" / "ziwei" / "__init__.py"
    if init_f.exists():
        content = init_f.read_text(encoding="utf-8")
        m = re.search(r"__all__\s*=\s*\[(.*?)\]", content, re.S)
        exported = re.findall(r'"([^"]+)"', m.group(1)) if m else []
        check("G.入口", "ziwei 子包有统一导出", len(exported) >= 4,
              f"导出 {len(exported)} 项: {exported}")
        # 三层各至少一个入口
        need = {"compute_multi_method_signals", "build_life_reading",
                "build_answer", "build_domain_readings"}
        missing = need - set(exported)
        check("G.入口", "三层入口齐备", not missing,
              f"缺={sorted(missing)}" if missing else "算/辨/解三层入口齐备")
    else:
        check("G.入口", "ziwei 子包存在", False)


# ── 主流程 ─────────────────────────────────────────────────────────────

def evaluate(json_out: str | None = None) -> int:
    print("=" * 66)
    print("紫微引擎健康检查 — 三层架构接线与产出完整性")
    print(f"样本盘: 农历{SAMPLE_LUNAR} {SAMPLE_HOUR}时 {SAMPLE_GENDER}")
    print("=" * 66)

    chart = check_calculation()
    sig = None
    if chart is not None:
        sig = check_signal(chart)
        check_answer_layer(chart)
        check_alignment(chart, sig)
        check_interpretation(chart, sig)
        check_domain(chart)
    check_wiring()

    # ── 输出 ──
    cur = None
    for r in results:
        if r["section"] != cur:
            cur = r["section"]
            print(f"\n【{cur}】")
        flag = {"PASS": "✓", "WARN": "△", "FAIL": "✗"}[r["status"]]
        detail = f"  — {r['detail']}" if r["detail"] else ""
        print(f"  {flag} {r['name']}{detail}")

    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_warn = sum(1 for r in results if r["status"] == "WARN")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)

    print("\n" + "=" * 66)
    print("汇总")
    print("=" * 66)
    print(f"  通过  ✓ PASS : {n_pass:>3}/{total}")
    print(f"  警告  △ WARN : {n_warn:>3}/{total}")
    print(f"  失败  ✗ FAIL : {n_fail:>3}/{total}")

    if n_fail:
        print("\n失败项（须修）:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  ✗ [{r['section']}] {r['name']} — {r['detail']}")
    if n_warn:
        print("\n警告项（建议关注）:")
        for r in results:
            if r["status"] == "WARN":
                print(f"  △ [{r['section']}] {r['name']} — {r['detail']}")

    if json_out:
        Path(json_out).write_text(
            json.dumps({
                "total": total, "pass": n_pass,
                "warn": n_warn, "fail": n_fail,
                "results": results,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nJSON 明细已写入: {json_out}")

    return 1 if n_fail else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="紫微引擎健康检查")
    ap.add_argument("--json", dest="json_out", default=None)
    args = ap.parse_args()
    return evaluate(args.json_out)


if __name__ == "__main__":
    raise SystemExit(main())
