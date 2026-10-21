"""变异验证：H11 节候卦保真度守卫是否真能抓住错误（2026-10-07）

锁的是本轮把 jiehhou.py 从卦气歌体系改回《河洛真数》原典节卦体系这件事。
守卫全绿不等于「回退到卦气歌也会绿」——那才是真问题：旧表与新表在
字段结构上都是 (卦名, 爻位, 卦名)，形状高度相似，断言稍松就一起放行。

故本套件逐条注入「退回旧体系」的变异，要求守卫**必须红**：

  · JIEHOU_GUA 不再派生 jiegua（改回内联旧卦气歌字面量）
  · 派生表达式取错字段（trigram→jq_name，yao_name→yao_index）
  · SOLAR_TERMS 与 jiegua 的节气表脱钩
  · evidence 把出处改回伪节名「定节候卦说」
  · SIXTY_GUA 退回 48 项含重复的老表
  · SIZHENG_GUA 的两套体系澄清注释被删

同样用 PYTHONPYCACHEPREFIX 隔离字节码——否则「还原后复跑」可能因陈旧
.pyc 假红（先天策数与数格两次验证都栽在这）。
"""
from __future__ import annotations

import hashlib
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JH = ROOT / "src" / "tongshu" / "engines" / "heluo" / "jiehhou.py"
JG = ROOT / "src" / "tongshu" / "engines" / "heluo" / "jiegua.py"
#: 本模块的全部守卫文件。**必须一次跑完**——只跑第一个时，
#: 其余文件里的新守卫会「假存活」（第二轮已在数格套件踩过）。
TEST = ("tests/heluo/test_jiehhou_original_fidelity.py",
        "tests/heluo/test_jiegua_vs_original.py",
        "tests/heluo/test_h11_jiehhou.py",
        "tests/heluo/test_h11_jiehhou_coverage.py")

MUTATIONS = [
    (JH, "JIEHOU_GUA 退回内联卦气歌表（不再派生原典表）",
     "JIEHOU_GUA: dict[int, tuple[str, int, str]] = {\n"
     "    e.jq_index: (e.trigram, e.yao_index, e.yao_name) for e in _JIE_GUA_SRC\n"
     "}",
     "JIEHOU_GUA: dict[int, tuple[str, int, str]] = {\n"
     "    0: (\"山雷颐\", 4, \"地雷复\"), 1: (\"水风井\", 3, \"风山渐\"),\n"
     "    2: (\"风山渐\", 4, \"地天泰\"), 3: (\"地天泰\", 3, \"雷水解\"),\n"
     "    4: (\"天山遁\", 2, \"泽天夬\"), 5: (\"水泽节\", 1, \"雷天大壮\"),\n"
     "    6: (\"泽天夬\", 2, \"山泽损\"), 7: (\"雷天大壮\", 3, \"火泽睽\"),\n"
     "    8: (\"火风鼎\", 1, \"风雷益\"), 9: (\"火山旅\", 5, \"山天大畜\"),\n"
     "    10: (\"地火明夷\", 5, \"水地比\"), 11: (\"地水师\", 5, \"天地否\"),\n"
     "    12: (\"水地比\", 4, \"山地剥\"), 13: (\"风地观\", 5, \"泽地萃\"),\n"
     "    14: (\"山地剥\", 5, \"火地晋\"), 15: (\"火泽睽\", 4, \"坎为水\"),\n"
     "    16: (\"天泽履\", 3, \"离为火\"), 17: (\"风火家人\", 5, \"乾为天\"),\n"
     "    18: (\"雷火丰\", 4, \"天山遁\"), 19: (\"泽火革\", 3, \"泽山咸\"),\n"
     "    20: (\"火水未济\", 5, \"山水蒙\"), 21: (\"山水蒙\", 5, \"天水讼\"),\n"
     "    22: (\"水山蹇\", 4, \"水天需\"), 23: (\"水天需\", 4, \"坎为水\"),\n"
     "}"),
    (JH, "JIEHOU_GUA 派生时取错字段（trigram→jq_name）",
     "e.jq_index: (e.trigram, e.yao_index, e.yao_name) for e in _JIE_GUA_SRC",
     "e.jq_index: (e.jq_name, e.yao_index, e.yao_name) for e in _JIE_GUA_SRC"),
    (JH, "JIEHOU_GUA 派生时取错字段（yao_name→yao_index）",
     "e.jq_index: (e.trigram, e.yao_index, e.yao_name) for e in _JIE_GUA_SRC",
     "e.jq_index: (e.trigram, e.yao_index, e.yao_index) for e in _JIE_GUA_SRC"),
    (JH, "JIEHOU_GUA 字典推导被抽空（只查字段存在会漏）",
     "JIEHOU_GUA: dict[int, tuple[str, int, str]] = {\n"
     "    e.jq_index: (e.trigram, e.yao_index, e.yao_name) for e in _JIE_GUA_SRC\n"
     "}",
     "JIEHOU_GUA: dict[int, tuple[str, int, str]] = {\n"
     "    e.jq_index: (e.trigram, e.yao_index, e.yao_name) for e in _JIE_GUA_SRC if False\n"
     "}"),
    (JH, "evidence 把出处改回伪节名「定节候卦说」",
     '"原典依据: 《河洛真数》起例卷之下·节候卦爻 L1492",',
     '"原典依据: 《河洛真数》起例卷下·定节候卦说",'),
    (JH, "evidence 删掉原典逐字引文",
     '        f"原典节卦段: {JIE_GUA_QUOTE}",\n', ''),
    (JH, "evidence 不再声明体系（不再与卦气歌划清界限）",
     '        "体系说明: 本条为原典四正卦节卦表（坎震离兑×六爻×15日），"\n'
     '        "非卦气歌/京房六日七分口径；后者属另一体系，见本模块 docstring 取证。",\n',
     ''),
    (JH, "result_gua 回填成卦名而非原典爻名",
     "        result_gua=yao_name,", "        result_gua=main_gua,"),
    (JH, "main_gua 回填成爻名（卦名与爻名对调）",
     "        main_gua=main_gua,", "        main_gua=yao_name,"),
    (JH, "SOLAR_TERMS 与 jiegua 的节气表脱钩（立春/惊蛰对调）",
     '    "春分", "清明", "谷雨", "立夏", "小满", "芒种",',
     '    "春分", "清明", "谷雨", "立夏", "小满", "惊蛰",'),
    (JH, "SIXTY_GUA 退回 48 项含重复的老表",
     'SIXTY_GUA: list[str] = [g for jqs in SIXTY_GUA_BY_JIEQI.values() for g in jqs]',
     'SIXTY_GUA: list[str] = ["中孚", "讼", "履", "节", "損", "兑", "困", "萃",\n'
     '    "咸", "否", "谦", "豫", "升", "鼎", "大过", "姤"]'),
    (JH, "SIXTY_GUA 混回非卦名「宜」",
     'SIXTY_GUA: list[str] = [g for jqs in SIXTY_GUA_BY_JIEQI.values() for g in jqs]',
     'SIXTY_GUA: list[str] = [g for jqs in SIXTY_GUA_BY_JIEQI.values() for g in jqs]\n'
     'SIXTY_GUA.insert(0, "宜")'),
    (JH, "SIXTY_GUA_BY_JIEQI 漏掉大雪一节（名实不再相符）",
     '    23: ("观", "比", "剥"),                      # 大雪\n}',
     '}'),
    (JH, "SIZHENG_GUA 改成京房四正卦（乾坤坎离）而与本卷节卦混称",
     'SIZHENG_GUA = {"坎", "离", "震", "兑"}',
     'SIZHENG_GUA = {"乾", "坤", "坎", "离"}'),
    (JG, "原典节卦表把大暑之爻改错（离九二→离六二）",
     'JieGuaEntry(14, "大暑", "离", 2, "九二"),',
     'JieGuaEntry(14, "大暑", "离", 1, "六二"),'),
    (JG, "原典节卦表把霜降之爻改错（兑九三→兑六三）",
     'JieGuaEntry(20, "霜降", "兑", 2, "九三"),',
     'JieGuaEntry(20, "霜降", "兑", 2, "六三"),'),
    (JG, "原典节卦表把冬至错派给震（坎→震）",
     'JieGuaEntry(0,  "冬至", "坎", 0, "初六"),',
     'JieGuaEntry(0,  "冬至", "震", 0, "初九"),'),
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


cache_dir = tempfile.mkdtemp(prefix="jh_mutate_pycache_")
ENV = dict(os.environ)
ENV.update({
    "PYTHONPATH": "src",
    "PYTHONIOENCODING": "utf-8",
    "PYTHONPYCACHEPREFIX": cache_dir,
    "TONGSHU_ALLOW_ZIWEI_STUB": "1",
    "TONGSHU_AUTHORITY_CREDENTIALS": ("architecture-governance:schema-v1-arch-gov-2026;"
                                     "admission_registry:test-cred-hash"),
})

originals: dict[Path, str] = {}


def read(p: Path) -> str:
    raw = io.open(p, encoding="utf-8", newline="").read()
    return raw.replace("\r\n", "\n") if "\r\n" in raw else raw


def write(p: Path, text: str) -> None:
    nl = "\r\n" if "\r\n" in io.open(p, encoding="utf-8", newline="").read() else "\n"
    io.open(p, "w", encoding="utf-8", newline="").write(text.replace("\n", nl))


for p in {JH, JG}:
    originals[p] = read(p)
base = {p: sha(t) for p, t in originals.items()}


def run() -> tuple[bool, str]:
    pr = subprocess.run(
        [sys.executable, "-m", "pytest", *TEST, "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8")
    lines = [ln for ln in pr.stdout.strip().splitlines() if ln.strip()]
    return pr.returncode == 0, (lines[-1] if lines else pr.stdout[-200:])


print("=" * 76)
problems: list[str] = []

ok0, msg0 = run()
print(f"[基线 ] 未变异应全绿 → {'OK  ' if ok0 else 'FAIL'}  {msg0}")
if not ok0:
    problems.append("基线未绿")

for target, name, old, new in MUTATIONS:
    src = originals[target]
    if old not in src:
        print(f"[SKIP ] {name} —— 锚点未命中")
        problems.append(f"{name}（锚点未命中）")
        continue
    write(target, src.replace(old, new, 1))
    try:
        green, msg = run()
    finally:
        write(target, originals[target])
    if sha(read(target)) != base[target]:
        problems.append(f"{name}（还原失败）")
        print(f"[BROKEN] {name} —— 还原失败！")
        continue
    caught = not green
    print(f"[{'CAUGHT' if caught else 'MISSED'}] {name}"
          + ("" if caught else f"   ← 变异存活！{msg}"))
    if not caught:
        problems.append(f"{name}（变异存活）")

print("=" * 76)
if problems:
    print("问题：" + "；".join(problems))
    raise SystemExit(1)
print(f"\n✅ {len(MUTATIONS)} 条变异全部被守卫抓住，还原后基线一致")
raise SystemExit(0)