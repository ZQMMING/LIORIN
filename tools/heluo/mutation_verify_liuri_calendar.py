# -*- coding: utf-8 -*-
"""变异演练：把「流日日历口径」修复逐个改坏，验证守卫必然变红。

⚠ 运行期间会原地改 src/ —— 运行中不得编辑/提交 src。
用法：python tools/heluo/_mutation_liuri.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ADAPTER = REPO / "src" / "heluo_engine" / "adapter.py"
CANON = REPO / "src" / "heluo_engine" / "engines" / "heluo" / "canonical.py"
GUJIE = REPO / "src" / "heluo_engine" / "engines" / "heluo" / "guajie.py"
GUARD = "tests/heluo/test_heluo_liuri_calendar.py"

#: (名称, 文件, 原文, 变坏文本)
MUTATIONS = [
    (
        "M1 退回公历月日（还原原缺陷）",
        ADAPTER,
        "        if _win.get(\"ok\"):\n"
        "            target_month = int(_win[\"month\"])\n"
        "            target_day = int(_win[\"day\"])\n"
        "            target_jie_year = int(_win[\"year\"])\n",
        "        if _win.get(\"ok\"):\n"
        "            target_month = int(_tm)\n"
        "            target_day = int(_td)\n"
        "            target_jie_year = int(_win[\"year\"])\n",
    ),
    (
        "M2 日序差一（节后日序 −1）",
        CANON,
        "                    \"day\": (_d - _a.date()).days + 1,\n",
        "                    \"day\": (_d - _a.date()).days,\n",
    ),
    (
        "M3 跨年边界丢失（窗口年一律用本年）",
        CANON,
        "                            and int(target_jie_year) != int(y.year)):\n"
        "                        _jie_year = int(target_jie_year)\n",
        "                            and False):\n"
        "                        _jie_year = int(target_jie_year)\n",
    ),
    (
        "M4 公历记录被伪日期覆盖",
        CANON,
        "                (target_solar_date\n"
        "                 if target_solar_date\n",
        "                ((f\"{target_year:04d}-{target_month:02d}-{target_day:02d}\")\n"
        "                 if True\n",
    ),
]


def run_guard() -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", GUARD, "-q", "--no-header", "-x"],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    tail = "\n".join((p.stdout or "").strip().splitlines()[-4:])
    return p.returncode, tail


def main() -> int:
    backups = {}
    for _n, f, _o, _m in MUTATIONS:
        backups.setdefault(f, f.read_text(encoding="utf-8"))
    results = []
    try:
        for name, path, old, new in MUTATIONS:
            src = backups[path]
            if old not in src:
                results.append((name, "SKIP", "未找到变异锚点（源码已变？）"))
                print(f"[SKIP] {name} —— 未找到锚点")
                continue
            path.write_text(src.replace(old, new, 1), encoding="utf-8")
            rc, tail = run_guard()
            results.append((name, "RED" if rc != 0 else "GREEN", tail))
            print(f"[{'RED ✔' if rc != 0 else 'GREEN ✘'}] {name}\n    {tail}")
            path.write_text(src, encoding="utf-8")   # 还原
    finally:
        for f, txt in backups.items():
            f.write_text(txt, encoding="utf-8")
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
