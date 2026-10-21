"""变异验证：H6 化工「相生救应」空断言是否真被抓住（2026-10-07）

锁的是本轮修掉的实质错误：旧实现命中「有化工卦 + 有反卦」就无条件判
RESCUED，而下游 `HUAGONG_DIRECTION` 把 RESCUED 映射为 SUPPORTIVE（吉），
于是原典 L582 明说「但忌克制，尤凶」的坎(水)克离(火)之盘被断成吉。

守卫全绿不等于「判成吉也会绿」——那才是要害。本套件逐条注入
「退回旧行为」「把克制当救应」「伪引文复现」，要求守卫**必须红**。
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
HG = ROOT / "src" / "tongshu" / "engines" / "heluo" / "hua_gong.py"
DRG = ROOT / "src" / "tongshu" / "engines" / "heluo" / "diagnosis_rule_graph.py"
#: 本模块全部守卫文件，必须一次跑完（只跑第一个会「假存活」）
TEST = ("tests/heluo/test_h6_hua_gong.py",
        "tests/heluo/test_full_pipeline.py",
        "tests/heluo/test_h12_diagnosis.py")

MUTATIONS = [
    # ── 要害：克制被当救应 ──
    (HG, "KEZHI 分支退回 RESCUED（原典「尤凶」又变吉）",
     "            state = HuaGongState.KEZHI",
     "            state = HuaGongState.RESCUED"),
    (HG, "五行相克表清空（水克火检测失效）",
     '_WU_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}',
     "_WU_KE: dict[str, str] = {}"),
    (HG, "相生判定整体失效（_wu_relation 恒返回空，克制也判不出）",
     '    if _WU_KE.get(elem_a) == elem_b or _WU_KE.get(elem_b) == elem_a:\n'
     '        return "克制"\n',
     '    if False:\n        return "克制"\n'),
    (HG, "相克表改错一行（水克火→水生木），坎离之反不再判克制",
     '_WU_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}',
     '_WU_KE = {"木": "土", "土": "水", "水": "木", "火": "金", "金": "木"}'),
    (HG, "相克判定退化为单向（只剩 A 克 B，漏 B 克 A）",
     '    if _WU_KE.get(elem_a) == elem_b or _WU_KE.get(elem_b) == elem_a:',
     '    if _WU_KE.get(elem_a) == elem_b:'),
    # ── 下游方向映射 ──
    (DRG, "KEZHI 在诊断规则图映射回 SUPPORTIVE（吉）",
     "    HuaGongState.KEZHI.value:    AssertionDirection.CAUTION,     # L582「忌克制，尤凶」",
     "    HuaGongState.KEZHI.value:    AssertionDirection.SUPPORTIVE,"),
    # ── 反卦表：必须是 L585–594 的四季对宫 ──
    (HG, "反卦表退回先天对宫（震↔巽/兑↔艮），与 L585–594 脱节",
     '    "兑": "震",   # L591\n    "震": "兑",   # L594\n}',
     '    "兑": "艮",\n    "震": "巽",\n    "艮": "兑",\n    "乾": "坤",\n    "坤": "乾",\n}'),
    (HG, "反卦表整体置空（反对检测完全失效）",
     'OPPOSITE_TRIGRAM: dict[str, str] = {\n'
     '    "坎": "离",   # L585\n',
     'OPPOSITE_TRIGRAM: dict[str, str] = {\n'),
    (HG, "L585 逐字出处「坎卦反离」被删（表对了但失去原典依据）",
     '#   L585「坎卦反离，主夏至以后秋分前。」\n', ''),
    (HG, "把两套对宫混为一谈（QIANXI_DUKONG 指回 OPPOSITE_TRIGRAM）",
     "QIANXI_DUKONG: dict[str, str] = {",
     "QIANXI_DUKONG: dict[str, str] = OPPOSITE_TRIGRAM or {"),
    # ── 月支映射 ──
    (HG, "寅月不再取震为化工卦（错一格，整季全偏）",
     '    "寅": "震", "卯": "震", "辰": "震",   # 春',
     '    "寅": "坎", "卯": "坎", "辰": "坎",   # 春'),
    (HG, "月支映射标为近似的说明被删（把近似当原典硬规则）",
     '# 四季 → 地支月 → 化工卦（**简化近似**，原典自己就反对此硬边界，见模块 docstring）',
     '# 四季 → 地支月 → 化工卦'),
    # ── 出处保真 ──
    (HG, "伪引文「三元纯正/生气充畅」复现",
     '  · L597「凡人根基不得化工者，灾重也。……**有化工之气者，艰难获福**。」',
     '  · L597「根基得三元纯正，生气充畅者，名曰元气足」'),
    (HG, "真实原句「艰难获福」被删（区块级：只查 docstring 出处清单）",
     '  · L597「凡人根基不得化工者，灾重也。……**有化工之气者，艰难获福**。」\n', ''),
    (HG, "原典对「拘于时气」的异议「气有浅深」被删",
     '「以予观之，春木夏火，秋金冬水，**气有浅深**。如十月立冬，水已司令，',
     '「以予观之，春木夏火，秋金冬水。如十月立冬，水已司令，'),
    (HG, "出处改回伪节名「起例卷下·论化工」",
     '**原典依据（2026-10-07 逐条核对，替换掉三处零命中的伪引）**：',
     '**原典依据：《河洛真数》起例卷下·论化工**：'),
    (HG, "反卦注释里「坎卦反离…震卦反兑」原典逐条被删",
     '#   L585「坎卦反离，主夏至以后秋分前。」\n'
     '#   L588「离卦反坎，主冬至以后春分前。」\n'
     '#   L591「兑卦反震，主春分以后夏至前。」\n'
     '#   L594「震卦反兑，主秋分以后冬至前。」\n',
     '#   （原典逐条出处已删）\n'),
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


cache_dir = tempfile.mkdtemp(prefix="hg_mutate_pycache_")
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


for p in {HG, DRG}:
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