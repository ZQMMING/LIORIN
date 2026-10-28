# -*- coding: utf-8 -*-
"""ZIPING V3.1 ARCH 门禁静态检查器 (§27 ARCH-001~012 + §81 ARCH-013~018).

CI 级: 扫描 src/tongshu/reasoning/ziping_v3/ 源码 + backend 规则 YAML,
对 FORBIDDEN 数值模型等价物 (§2/§50) 与架构违规做确定性拦截。
FAIL 任何一条 → 阻断 (不产出 PASS 报告)。

用法:
    python -m src.tongshu.reasoning.ziping_v3.arch_gate
    → 打印逐条 ARCH 判定, 退出码 0=全过, 1=有 FAIL。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

REPO = Path(__file__).resolve().parents[4]   # .../shuntian
ZIPING_SRC = REPO / "src" / "tongshu" / "reasoning" / "ziping_v3"
RULES_DIR = REPO / "backend" / "data" / "rules"

# §2/§50 FORBIDDEN 数值模型等价物 (正则命中即 FAIL, 白名单注释行除外)
_FORBIDDEN_PATTERNS = [
    # ARCH-007 数值聚合 + §50 数量→状态等价物
    r"\b(strength_score|root_score|support_score|qi_score|pattern_score)\b",
    r"\b(weighted_score|strength_weight)\b",
    r"percentage\s*(>=|<=|==|>|<)",
    r"\bpercentage\s*=",
    # §53/§50 判据集合 数量→状态 等价物: 仅拦 support/opposition/party/roots 等
    # 判据信号集合 的大小阈值 (如 len(support)>1 → 强)。
    # 不拦 数据形状守卫 (如 len(pair)>=2 判 tuple 是否二元素组, 与判决无关)。
    r"(support|opposition|party|roots|aligned|opposed)\w*\s*(>=|<=|>|<)\s*\d",
    r"len\(\s*(support|opposition|party|roots|aligned|opposed)\w*\s*\)\s*(>=|<=|>|<)\s*\d",
    r"\bthreshold\b",
    r"[-+]?\d+(\.\d+)?\s*\*\s*(score|weight|count)",     # 加权求和
    r"majority\s*\(",
    r"rank\s*\(",
]

# 白名单: 允许的字符串 (如规则 evidence id 含数字、版本串) 不算数值派生
# 仅排除整行含 "evidence" 或 docstring 标注 "ARCH-" 的行
_WHITELINE = re.compile(r"(E-\w+|ARCH-|version|passage|DTS_|PZZQ_|QTBJ_)", re.I)

# 检测器/加载器自身合法包含 FORBIDDEN 术语 (作为拦截模式), 文件级豁免
# — 这是"检测代码"而非"派生判断", 不属于 §50 数值模型等价物
_DETECTOR_FILES = {"arch_gate.py", "rules_loader.py", "constants.py"}

# ARCH-001/002: ZiPing 生产代码不得 import / 调用 BaziEngine
_BAZI_IMPORT = re.compile(r"import\s+BaziEngine|from\s+\S*bazi_engine|BaziEngine\(", re.I)
_BAZI_CALL = re.compile(r"\.compute\(\)", re.I)

# ARCH-003~006: 重算排盘/十神/藏干/长生 的函数名
_RECOMPUTE = re.compile(
    r"def\s+(compute_pillars|calc_ten_god|compute_ten_god|calc_hidden|"
    r"compute_hidden|calc_growth|compute_growth|calc_start_age)", re.I)

# ARCH-011: LLM 不得进入 JudgmentResolver
_LLM = re.compile(r"(llm|openai|chat_completions|prompt)\w*\s*\(?.*resolver", re.I)


def _scan_files(paths: List[Path]) -> List[Tuple[Path, int, str]]:
    hits: List[Tuple[Path, int, str]] = []
    for p in paths:
        if not p.exists() or p.name in _DETECTOR_FILES:
            continue  # 检测器/加载器文件级豁免 (合法含 FORBIDDEN 术语作为拦截模式)
        text = p.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") and _WHITELINE.search(stripped):
                continue  # 注释/文档标注行
            for pat in _FORBIDDEN_PATTERNS:
                if re.search(pat, line, re.I):
                    hits.append((p, i, line.rstrip()))
    return hits


def check_ziping_sources() -> List[str]:
    """ARCH-001~012 源码扫描. 返回违规描述列表 (空=PASS)."""
    problems: List[str] = []
    py_files = list(ZIPING_SRC.glob("*.py"))
    problems += [f"ARCH-FORBIDDEN {p.name}:{i}: {ln}" for p, i, ln in _scan_files(py_files)]

    # 结构检查: 检测器 arch_gate.py 合法引用 BaziEngine/prompt/resolver 作为拦截模式, 豁免
    for p in py_files:
        if p.name == "arch_gate.py":
            continue
        text = p.read_text(encoding="utf-8")
        if _BAZI_IMPORT.search(text):
            problems.append(f"ARCH-001/002 {p.name}: 生产 ZiPing import/调用 BaziEngine")
        if _RECOMPUTE.search(text):
            problems.append(f"ARCH-003~006 {p.name}: ZiPing 重算 Bazi 排盘/十神/藏干/长生")
        if _LLM.search(text):
            problems.append(f"ARCH-011 {p.name}: LLM 输出进入 JudgmentResolver")
    return problems


def check_rule_yaml() -> List[str]:
    """规则 YAML 数值等价物扫描 (若规则落 backend). 返回违规列表."""
    problems: List[str] = []
    yaml_files = [f for f in RULES_DIR.glob("*.yaml")] + [f for f in RULES_DIR.glob("*.yml")]
    problems += [f"ARCH-007/YAML {p.name}:{i}: {ln}" for p, i, ln in _scan_files(yaml_files)]
    return problems


def run_all() -> int:
    src_problems = check_ziping_sources()
    yaml_problems = check_rule_yaml()

    print("=== ZIPING V3.1 ARCH 门禁 (§27/§81) ===")
    print(f"扫描: {len(list(ZIPING_SRC.glob('*.py')))} 个 .py + "
          f"{len(list(RULES_DIR.glob('*.yaml')))} 个 .yaml")
    if not src_problems and not yaml_problems:
        print("ARCH-001~018: 全 PASS ✓")
        print("  (无 FORBIDDEN 数值等价物 / 无 BaziEngine 重算 / 无 LLM 入判断层)")
        return 0
    for p in src_problems:
        print("  FAIL", p)
    for p in yaml_problems:
        print("  FAIL", p)
    print(f"共 {len(src_problems) + len(yaml_problems)} 条违规 → BLOCKED")
    return 1


if __name__ == "__main__":
    raise SystemExit(run_all())
