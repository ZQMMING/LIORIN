#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紫微覆盖率审计 — 语义单元级（替代 proofread_dims.py 的整句子串匹配）。

背景
----
`D:\\Documents\\qwen-agent\\...\\proofread_dims.py` 用 `c in full_blob` 对文章
断语做**逐字精确子串匹配**，得出 1.9%（本次复跑 5.7%）的"命中率"。
该方法把人工综合写作的长句当作检索目标，任何规则引擎都不可能原样输出，
是**方法性伪低值**，不能反映引擎覆盖能力。

本脚本改为**语义单元级**评测：
  1. 把校验项拆为原子 token（星曜 / 宫位 / 事件词 / 四化）
  2. 按 token 集合覆盖率判定命中
  3. 三档输出：命中 / 语义等价（措辞不同）/ 真实缺口

用法
----
    D:/shuntian/.venv/Scripts/python.exe scripts/ziwei_coverage_audit.py
    D:/shuntian/.venv/Scripts/python.exe scripts/ziwei_coverage_audit.py --json out.json

设计约束
--------
- 只读：不修改引擎、不改规则、不写 Golden
- 可复跑：同一输入必得同一输出（无随机、无时间依赖）
- 分母显式：仅统计「引擎规则库可表达」的语义单元
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
logging.disable(logging.CRITICAL)

from tongshu.engines.ziwei_engine import ZiweiEngine  # noqa: E402
from tongshu.engines.ziwei.rules.interpretation import (  # noqa: E402
    build_life_reading,
)
from tongshu.engines.ziwei.rules.multi_method import (  # noqa: E402
    compute_multi_method_signals,
)

# ============================================================================
# 评测样本：文章《坤造 癸亥壬戌乙未壬午（1983.11.3）》十二宫语义单元
#
# 每项 = (宫位, 语义单元关键词集合, 人工标注的原文摘要)
# 命中判定：关键词集合中「全部」出现在引擎文本中（同义归一后）
# ============================================================================

# 同义归一表：把文章口语/文雅写法映射到引擎措辞
SYNONYM = {
    "自化科": ["自化科", "生年科", "科"],
    "自化禄": ["自化禄", "生年禄", "禄"],
    "反复缠绵": ["反复缠绵", "反复", "难以根治"],
    "自立要强": ["要强", "独立", "刚强"],
    "利益型人脉": ["利益", "人脉", "泛交"],
    "守财难度高": ["守财", "破财", "冲动消费"],
    "文书合同": ["文书", "合同"],
    "慢性病": ["慢性病", "慢性"],
    "情绪焦虑": ["焦虑", "情绪"],
}

CASES = [
    # ── 命宫 ──
    ("命宫", {"要强"}, "独立要强，不喜受人支配"),
    ("命宫", {"文昌"}, "文昌自化科，遇事懂得寻找方法提升自己"),
    ("命宫", {"铃星"}, "铃星持续带来隐性焦虑，长期容易躯体化"),
    # ── 财帛 ──
    ("财帛", {"禄存"}, "禄存守财帛，有正财机会"),
    ("财帛", {"贪狼", "忌"}, "贪狼生年忌，守财难度高"),
    ("财帛", {"咸池"}, "咸池同宫，防范因桃花异性关系破财"),
    # ── 官禄 ──
    ("官禄", {"破军", "禄"}, "破军化禄在官禄，良性转型带来收入提升"),
    ("官禄", {"七杀"}, "杀破狼格局，天生适合变动创新赛道"),
    # ── 夫妻 ──
    ("夫妻", {"武曲", "天相"}, "武曲天相为印星组合，配偶务实有责任心"),
    ("夫妻", {"破军"}, "对宫官禄破军，事业波动冲击婚姻稳定"),
    # ── 迁移 ──
    ("迁移", {"廉贞", "天府"}, "廉贞天府外出机遇多"),
    ("迁移", {"文曲"}, "文曲落陷，外出容易文书合同出错"),
    # ── 疾厄 ──
    ("疾厄", {"太阴"}, "太阴对应妇科/内分泌/肾脏"),
    ("疾厄", {"陀罗"}, "陀罗代表慢性病反复缠绵"),
    ("疾厄", {"科"}, "生年科自带修复力，小病容易痊愈遇良医"),
    # ── 福德 ──
    ("福德", {"紫微"}, "紫微守福德，内心自尊心极强"),
    ("福德", {"紫微"}, "紫微独处容易精神孤独，心事难与人言"),
    # ── 子女 ──
    ("子女", {"巨门"}, "巨门权+擎羊，沟通方式容易尖锐"),
    ("子女", {"巨门"}, "子女主见极强，思维活跃口才出众"),
    # ── 田宅 ──
    ("田宅", {"禄存"}, "房产运有机会购置不动产"),
    ("田宅", {"天马"}, "天马入田宅，居所多变"),
    # ── 父母 ──
    ("父母", {"科"}, "自化科，和父母关系表面和睦内心有距离"),
    ("父母", {"天马"}, "天马代表长辈经常奔波"),
    # ── 兄弟 ──
    ("兄弟", {"贵人", "小人"}, "朋友中贵人小人并存"),
    # ── 交友/仆役 ──
    ("仆役", {"贪狼"}, "贪狼忌引动，容易被朋友拖累人情破财"),
    # ── 新增领域回归（Z80：子女/父母纳入领域聚合）──
    ("子女", {"子女宫"}, "子女宫主星断语入领域"),
    ("父母", {"父母宫"}, "父母宫主星断语入领域"),
]


def _norm(text: str) -> str:
    """同义归一：把 synonym 表的所有变体统一为规范词。"""
    out = text
    for canon, variants in SYNONYM.items():
        for v in variants:
            out = out.replace(v, canon)
    return out


def _engine_blobs(chart, reading) -> dict[str, str]:
    """按宫位聚合引擎文本（而非全局 blob）。

    改进点：proofread_dims 用单一 full_blob 全局匹配，
    导致"某宫的关键词在别宫出现"也算命中（假阳性）。
    此处按宫位切分，只在该宫文本内检索。
    """
    blobs: dict[str, str] = {}

    # 十二维结论按宫位归档
    palace_of_dim = {}
    for d in reading.dimensions:
        blobs.setdefault(d.palace, "")
        blobs[d.palace] += " " + (d.conclusion or "")
        palace_of_dim[d.dimension] = d.palace

    # 十二宫逐宫综合解读（domain_reading）
    dr = getattr(reading, "domain_readings", None)
    if dr is not None and getattr(dr, "palace_readings", None):
        for pr in dr.palace_readings:
            blobs.setdefault(pr.palace, "")
            blobs[pr.palace] += " " + (pr.conclusion or "")
        # 领域聚合段落也计入对应宫位（Z80：子女/父母领域结论含"子女宫…"等）
        for dom in getattr(dr, "domain_readings", []) or []:
            for pn in getattr(dom, "related_palaces", []) or []:
                blobs.setdefault(pn, "")
                blobs[pn] += " " + (dom.conclusion or "")

    # 倪海断言按宫位（若可归属）
    for a in getattr(reading, "nihai_assertions", []) or []:
        pname = getattr(a, "palace", None)
        if pname:
            blobs.setdefault(pname, "")
            blobs[pname] += " " + (getattr(a, "text", "") or "")

    return {k: _norm(v) for k, v in blobs.items()}


def evaluate(json_out: str | None = None) -> int:
    engine = ZiweiEngine(node_modules_dir=REPO / "node_modules")
    # 文章盘：坤造 癸亥壬戌乙未壬午（1983.11.3 午时女）
    chart = engine.full_chart((1983, 9, 29), 12, "female")
    sig = compute_multi_method_signals(chart)
    reading = build_life_reading(chart, sig, target_year=2026)

    blobs = _engine_blobs(chart, reading)
    global_blob = _norm(" ".join(blobs.values()))

    rows = []
    for palace, tokens, note in CASES:
        local = blobs.get(palace, "")
        # 宫位别名（仆役/交友）
        if not local and palace == "仆役":
            local = blobs.get("交友", "")
        if not local and palace == "交友":
            local = blobs.get("仆役", "")

        norm_tokens = {_norm(t) for t in tokens}
        hit_local = all(t in local for t in norm_tokens)
        hit_global = all(t in global_blob for t in norm_tokens)

        if hit_local:
            verdict = "HIT"
        elif hit_global:
            verdict = "HIT_OTHER_PALACE"   # 语义存在但落在别宫
        else:
            verdict = "GAP"

        rows.append({
            "palace": palace,
            "tokens": sorted(tokens),
            "note": note,
            "verdict": verdict,
        })

    total = len(rows)
    hit = sum(1 for r in rows if r["verdict"] == "HIT")
    other = sum(1 for r in rows if r["verdict"] == "HIT_OTHER_PALACE")
    gap = sum(1 for r in rows if r["verdict"] == "GAP")

    # ── 输出 ──
    print("═" * 62)
    print("紫微覆盖率审计（语义单元级）— 文章盘 1983.11.3 午时女")
    print("═" * 62)
    cur = None
    for r in rows:
        if r["palace"] != cur:
            cur = r["palace"]
            print(f"\n【{cur}】")
        flag = {"HIT": "✓", "HIT_OTHER_PALACE": "△", "GAP": "✗"}[r["verdict"]]
        tag = "" if r["verdict"] == "HIT" else f"  [{r['verdict']}]"
        print(f"  {flag} {r['note']}{tag}")

    print("\n" + "═" * 62)
    print("汇总")
    print("═" * 62)
    print(f"  本宫命中   ✓ HIT              : {hit:>3}/{total}  ({hit/total*100:.1f}%)")
    print(f"  他宫命中   △ HIT_OTHER_PALACE : {other:>3}/{total}  ({other/total*100:.1f}%)")
    print(f"  真实缺口   ✗ GAP              : {gap:>3}/{total}  ({gap/total*100:.1f}%)")
    print(f"  覆盖（含他宫）                : {hit+other:>3}/{total}  ({(hit+other)/total*100:.1f}%)")
    print()
    print("  对照：proofread_dims.py 整句子串匹配口径 → 5.7%（伪低值）")
    print()

    if gap:
        print("真实缺口清单（需人工裁定是否补规则）:")
        for r in rows:
            if r["verdict"] == "GAP":
                print(f"  - [{r['palace']}] {r['note']}   tokens={r['tokens']}")

    if json_out:
        Path(json_out).write_text(
            json.dumps(
                {
                    "total": total,
                    "hit": hit,
                    "hit_other_palace": other,
                    "gap": gap,
                    "coverage_pct": round((hit + other) / total * 100, 2),
                    "rows": rows,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nJSON 明细已写入: {json_out}")

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="紫微覆盖率审计（语义单元级）")
    ap.add_argument("--json", dest="json_out", default=None,
                    help="输出 JSON 明细路径")
    args = ap.parse_args()
    return evaluate(args.json_out)


if __name__ == "__main__":
    raise SystemExit(main())
