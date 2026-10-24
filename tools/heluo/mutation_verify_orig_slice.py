# -*- coding: utf-8 -*-
"""变异演练：把「年卦月卦切片」及其校记逐个改坏，验证守卫必然变红。

⚠ 运行期间会原地改 orig/ 与 tests/ —— 运行中不得编辑/提交。
用法：python tools/heluo/mutation_verify_orig_slice.py
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SLICE = REPO / "src" / "heluo_engine" / "orig" / "河洛理数_年卦月卦切片.txt"
NOTE = REPO / "src" / "heluo_engine" / "orig" / "河洛理数_年卦月卦切片_校记.md"
GUARD = "tests/heluo/test_heluo_orig_slices.py"

#: (名称, 文件, 原文, 变坏文本)
MUTATIONS = [
    ("M1 删掉「刻七分六目数過一時」（每日添一刻七分天本句）",
     SLICE, "刻七分六目数過一時是也凡看國連只简正\n",
     "\n"),
    ("M2 段头行号区间被改（切片与底本脱钩）",
     SLICE, "# 【S1 河洛理数_1632笔写本_K3-448_修正版.txt L2878-L3165】",
     "# 【S1 河洛理数_1632笔写本_K3-448_修正版.txt L2879-L3165】"),
    ("M3 删掉「年卦」篇目（判据出处丢失）",
     SLICE, "月日卦\n年卦\n理数本源\n", "月日卦\n理数本源\n"),
    ("M4 校记里的影印核定记录被删",
     NOTE, "## 一、影印核定结果", "## 一、（记录已移除）"),
    ("M5 校记里的 P1 定位订正被删",
     NOTE, "## 三、本批次对**《河洛理数》体例定位**的订正",
     "## 三、（订正已移除）"),
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
            path.write_text(src.replace(old, new, 1), encoding="utf-8")
            rc, tail = run_guard()
            results.append((name, "RED" if rc != 0 else "GREEN", tail))
            print(f"[{'RED ✔' if rc != 0 else 'GREEN ✘'}] {name}\n    {tail}")
            path.write_text(src, encoding="utf-8")
    finally:
        for f, txt in backups.items():
            f.write_text(txt, encoding="utf-8")
        print("\n已还原全部被改动的文件。")

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
