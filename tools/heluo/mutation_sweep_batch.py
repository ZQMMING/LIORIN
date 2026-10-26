# -*- coding: utf-8 -*-
"""变异扫描**批跑器** —— CI 的入口（2026-10-25 新增）。

为什么需要它
------------
``mutation_sweep.py`` 一次只扫一个模块。CI 需要的是：
  · 一次跑**多个**模块；
  · 产出一份**汇总**结果（JSON），供 CI 判定「有没有真盲区」；
  · 单个模块失败**不吞掉**（但要在汇总里如实记为「该模块未完成」）。

⚠ 三条纪律（都是 2026-10-25 实测踩出来的）：
  1. **一次只跑一个扫描进程** —— 扫描是**原地改 src/** 的，
     两个进程同时跑会互相污染（A 还原源码时 B 正在变异）⇒ 结果全错。
     ⇒ 本工具**串行**跑模块，绝不开并行。
  2. **绝不在扫描期间改 src/ 或提交** —— 否则会把残留变异提交进去。
  3. **还原必须校验** —— 每个模块跑完校验哈希；不通过 ⇒ 该模块记为失败。

模块清单的取法
--------------
``CORE_MODULES`` 是**判据核心**模块（判据语义最要紧、盲区最伤）。
新增判据层模块时**必须**加进来，否则扫描会漏掉它。
⚠ 别用「全部模块」代替：基础设施模块（``cli`` / ``adapter`` / ``paths``）
  变异噪声大、收益低，拖慢 CI。

退出码
------
* ``0`` —— 全部模块扫完且**无真盲区**；
* ``2`` —— **有真盲区**（CI 必须红）；
* ``3`` —— 有模块**未完成**（超时 / 崩溃 / 还原校验失败）。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SWEEP = ROOT / "tools" / "heluo" / "mutation_sweep.py"

#: ★ 判据核心模块清单（新增判据层模块时**必须**加进来）。
CORE_MODULES = [
    "hua_gong.py", "yue_ling_shu_ge.py", "canonical.py",
    "diagnosis_rule_graph.py", "canonical_signals.py", "dimensions.py",
    "gui_ming_liu_ju.py", "evidence_producer.py", "interpretation_pipeline.py",
    "metrics_v2.py", "calendar_guard.py", "frozen_state.py",
    "timeline_yun.py", "yuanqi_tables.py", "jiehhou.py", "jiegua.py",
    "numbers.py", "yuan_tang.py", "time_layer_judgment.py",
    "prenatal.py", "postnatal.py", "interpretation.py",
]


def _run_module(name: str, out_dir: Path, timeout: int,
                tests: str = "") -> dict:
    """跑一个模块的扫描，返回该模块的结果记录。

    Args:
        name:   模块文件名（如 ``hua_gong.py``）。
        out_dir: 逐模块结果 JSON 的输出目录。
        timeout: 单模块扫描超时秒数。
        tests:  **守卫生效范围**（传给扫描器的 ``--tests``）。
                ⚠ 必须显式传 —— 主仓与独立包的守卫目录**同名但内容不同**
                （主仓多了 ``tongshu`` 侧的接线守卫）⇒ 不能靠默认值。
    """
    out_json = out_dir / ("%s.json" % name.replace(".py", ""))
    cmd = [sys.executable, "-u", str(SWEEP), "--module", name,
           "--json-out", str(out_json)]
    if tests:
        cmd += ["--tests", tests]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout)
        rc = p.returncode
        stderr_tail = (p.stderr or "")[-800:]
    except subprocess.TimeoutExpired:
        rc = -1
        stderr_tail = "扫描进程整体超时（> %ds）" % timeout
    rec = {
        "module": name,
        "rc": rc,
        "seconds": round(time.time() - t0, 1),
        "result_file": str(out_json),
    }
    if out_json.exists():
        try:
            rec["result"] = json.loads(out_json.read_text(encoding="utf-8"))
        except Exception as exc:
            rec["error"] = "结果 JSON 解析失败: %s" % exc
    else:
        rec["error"] = stderr_tail or "扫描未产出结果文件"
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description="河洛变异扫描 批跑器")
    ap.add_argument("--out-dir", default="mutation_report",
                    help="结果输出目录（默认 mutation_report）")
    ap.add_argument("--timeout", type=int, default=3600,
                    help="单模块扫描超时秒数（默认 3600）")
    ap.add_argument("--modules", default="",
                    help="逗号分隔的模块名；缺省 = 全部核心模块")
    ap.add_argument("--tests", default="tests/heluo",
                    help="守卫生效范围（传给扫描器的 --tests；缺省 tests/heluo）")
    ap.add_argument("--summary-json", default="",
                    help="汇总 JSON 路径（默认 <out-dir>/summary.json）")
    args = ap.parse_args()

    modules = ([m.strip() for m in args.modules.split(",") if m.strip()]
               if args.modules else list(CORE_MODULES))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for i, name in enumerate(modules, 1):
        print("[%d/%d] 扫描 %s ..." % (i, len(modules), name), flush=True)
        rec = _run_module(name, out_dir, args.timeout, tests=args.tests)
        res = rec.get("result") or {}
        print("      → rc=%s 杀=%s 盲区=%s 等价=%s 还原=%s (%.0fs)"
              % (rec["rc"], res.get("killed", "?"),
                 len(res.get("blind_spots", [])), res.get("equivalent", "?"),
                 res.get("restore_ok", "?"), rec["seconds"]), flush=True)
        records.append(rec)

    # ── 汇总 ──
    total_killed = 0
    total_equiv = 0
    all_blind = []
    incomplete = []
    restore_fail = []
    for rec in records:
        res = rec.get("result")
        if not res:
            incomplete.append({"module": rec["module"], "reason": rec.get("error")})
            continue
        total_killed += int(res.get("killed", 0))
        total_equiv += int(res.get("equivalent", 0))
        for bs in res.get("blind_spots", []):
            all_blind.append(bs)
        if not res.get("restore_ok", False):
            restore_fail.append(rec["module"])

    summary = {
        "schema": 1,
        "modules_total": len(modules),
        "modules_completed": len(modules) - len(incomplete),
        "killed": total_killed,
        "equivalent": total_equiv,
        "blind_spots": all_blind,
        "blind_spot_count": len(all_blind),
        "incomplete": incomplete,
        "restore_failures": restore_fail,
        "records": records,
    }
    summary_path = Path(args.summary_json) if args.summary_json \
        else (out_dir / "summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    print("")
    print("=== 变异扫描汇总 ===")
    print("  模块完成      : %d / %d" % (summary["modules_completed"],
                                        summary["modules_total"]))
    print("  被守卫抓住    : %d" % total_killed)
    print("  等价变异      : %d" % total_equiv)
    print("  ★ 真盲区      : %d" % len(all_blind))
    print("  还原校验失败  : %s" % (restore_fail or "无"))
    print("  未完成模块    : %d" % len(incomplete))
    print("  汇总 JSON     : %s" % summary_path)

    if all_blind:
        print("")
        print("--- ★ 真盲区明细 ---")
        for bs in all_blind:
            print("  [%s] L%d  %s" % (bs.get("module"), bs.get("line", 0),
                                      bs.get("label")))
        return 2
    if incomplete or restore_fail:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
