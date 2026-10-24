# -*- coding: utf-8 -*-
"""变异演练：把「解读层接线」逐个改坏，验证守卫必然变红。

⚠ 运行期间会原地改 src/ —— 运行中不得编辑/提交 src。
用法：python tools/heluo/mutation_verify_interpretation.py
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PIPE = REPO / "src" / "heluo_engine" / "engines" / "heluo" / "interpretation_pipeline.py"
ADPT = REPO / "src" / "heluo_engine" / "adapter.py"
DRG = REPO / "src" / "heluo_engine" / "engines" / "heluo" / "diagnosis_rule_graph.py"
DIM = REPO / "src" / "heluo_engine" / "engines" / "heluo" / "dimensions.py"
GUARD = "tests/heluo/test_heluo_interpretation_pipeline.py"

MUTATIONS = [
    ("M1 接线被拆（adapter 不再调解读层编排）",
     ADPT,
     "            result = replace(result, interpretation=build_interpretation(result))",
     "            result = replace(result, interpretation=None)"),
    ("M2 复活已作废的自拟分数（改调 calculate_hexagram_state）",
     PIPE,
     "    try:\n        from .gui_ming_liu_ju import judge_liu_ju",
     "    try:\n        from .hexagram_state import calculate_hexagram_state\n"
     "        calculate_hexagram_state(gua)\n"
     "        from .gui_ming_liu_ju import judge_liu_ju"),
    ("M3 维度→机制映射少一条（该机制永远收不到证据）",
     DIM,
     '    "TIMELINE.04": "HL_RIGUA",\n',
     ''),
    ("M4 诊断规则注册表被清空（授权面消失）",
     DRG,
     '    "HL_RIGUA": RuleNode(',
     '    "HL_RIGUA_DISABLED": RuleNode('),
    ("M5 六项判据改给数值分数（违背「不臆造分数」）",
     PIPE,
     '        block["liu_ju"] = {k: _plain(v) for k, v in j.items()}',
     '        block["liu_ju"] = {k: {**(_plain(v) if isinstance(v, dict) else _plain(v.__dict__)),\n'
     '                             "score": 0.5} for k, v in j.items()}'),
]


def run_guard() -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", GUARD, "-q", "--no-header", "-x"],
        cwd=REPO, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    tail = "\n".join((p.stdout or "").strip().splitlines()[-3:])
    return p.returncode, tail


def main() -> int:
    backups: dict[Path, str] = {}
    for _n, f, _o, _m in MUTATIONS:
        backups.setdefault(f, f.read_text(encoding="utf-8"))
    results = []
    try:
        for name, path, old, new in MUTATIONS:
            src = backups[path]
            if old not in src:
                results.append((name, "SKIP", "未找到变异锚点"))
                print(f"[SKIP] {name} —— 未找到锚点")
                continue
            path.write_text(src.replace(old, new, 1), encoding="utf-8", newline="\n")
            rc, tail = run_guard()
            results.append((name, "RED" if rc != 0 else "GREEN", tail))
            print(f"[{'RED ✔' if rc != 0 else 'GREEN ✘'}] {name}\n    {tail}")
            path.write_text(src, encoding="utf-8", newline="\n")
    finally:
        for f, txt in backups.items():
            f.write_text(txt, encoding="utf-8", newline="\n")
        print("\n已还原全部被改动的源文件。")

    rc, tail = run_guard()
    print(f"\n还原后回归：{'PASS ✔' if rc == 0 else 'FAIL ✘'}\n    {tail}")
    bad = [r for r in results if r[1] != "RED"]
    if bad:
        print("\n✘ 存在未变红的变异 —— 守卫有盲区：")
        for r in bad:
            print(f"   - {r[0]} → {r[1]}")
        return 1
    print(f"\n✔ 全部 {len(results)} 项变异均被守卫抓住。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
