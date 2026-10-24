# -*- coding: utf-8 -*-
"""变异演练：把「判词层维度视图」逐个改坏，验证守卫必然变红。

⚠ 运行期间会原地改 src/ —— 运行中不得编辑/提交 src。
用法：python tools/heluo/mutation_verify_dimensions.py

⚠ 锚点选取纪律（2026-10-24 第一轮演练的教训）：
  变异必须打在**测试盘上必然出现**的代码路径，或**静态可检**的位置 ——
  否则「该盘本来就不产生这条证据」，变异等于没做（会误判成守卫盲区）。
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GJ = REPO / "src" / "heluo_engine" / "engines" / "heluo" / "guajie.py"
DIM = REPO / "src" / "heluo_engine" / "engines" / "heluo" / "dimensions.py"
GUARD = "tests/heluo/test_heluo_dimensions.py"

#: (名称, 文件, 原文, 变坏文本)
MUTATIONS = [
    ("M1 判据证据漏标（去掉「流年卦…」的 dim；该证据三盘必现）",
     GJ,
     'ev.append(f"流年卦{liunian_hexagram} {liunian_yao}爻：{y.ci}",\n'
     '                      dim="TIMELINE.02")',
     'ev.append(f"流年卦{liunian_hexagram} {liunian_yao}爻：{y.ci}")'),
    ("M2 by_dimension 漏收一条（吞掉末条）",
     DIM,
     "    for i, (text, dim) in enumerate(zip(evidence, dims)):\n"
     "        node = out.get(dim)",
     "    for i, (text, dim) in enumerate(zip(evidence, dims)):\n"
     "        if i == len(evidence) - 1:\n"
     "            continue\n"
     "        node = out.get(dim)"),
    ("M3 维度 id 非法（写成不存在的域；静态校验可抓）",
     GJ,
     'ev.append(f"流年卦{liunian_hexagram} {liunian_yao}爻：{y.ci}",\n'
     '                      dim="TIMELINE.02")',
     'ev.append(f"流年卦{liunian_hexagram} {liunian_yao}爻：{y.ci}",\n'
     '                      dim="TIMELINE.99")'),
    ("M4 L4 判据出处被清空（节点缺原典回源）",
     DIM,
     '"SELF.03": ("SELF", "元气体", "天元气/地元气/元气相反", "yuan_qi.py；原典「元气相反图」"),',
     '"SELF.03": ("SELF", "元气体", "天元气/地元气/元气相反", ""),'),
    ("M5 维度表少一个子维度（41 → 40）",
     DIM,
     '    "TIMELINE.05": ("TIMELINE", "节候", "节候卦（四正节卦每卦 90 日）", "《起例卷之下》节候卦说"),\n',
     ''),
    ("M6 扩展断法 key 映射表少一项",
     DIM,
     '    "yue_ling_fei_shi": "LIFESPAN.02",  # 月令非时（旺衰）\n',
     ''),
    ("M7 by_dimension 的条目文本与平铺 evidence 不一致",
     DIM,
     '        node["items"].append({"index": i, "text": text})',
     '        node["items"].append({"index": i, "text": text + "（改）"})'),
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
