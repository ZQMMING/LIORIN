"""子平规则级对账：原典判据核验器 vs p0 引擎。

用法:
    python scripts/ziping_rule_audit.py [N]

对账口径（按子平原典，不按盲派回放）:
    取格  — 《子平真诠》月令提纲取格（YUE_LING_GE_JU.001~.014）
    成败  — 《子平真诠》八格成/败（CHENG_BAI.007/.008）

输出:
    ① 原典 12 案：核验器 vs 引擎（ge / cheng_bai）
    ② N 个随机盘：取格不一致、成败不一致计数与样例
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.reasoning.ziping_classic_check import derive_ge, judge_cheng_bai
from engines.production_entry import FrozenCanonicalBaziChart, production_entry

CASES = [
    ("刘镇华", "癸未 辛酉 甲申 丙寅"),
    ("洗冠生", "戊子 癸亥 庚寅 戊寅"),
    ("龙济光", "丁卯 丙午 丙子 壬辰"),
    ("张耀曾", "乙酉 甲申 丁巳 庚戌"),
    ("王士珍", "辛酉 丙申 庚子 丙戌"),
    ("壬寅案", "壬寅 戊申 丙寅 癸巳"),
    ("林森", "戊辰 甲寅 丁卯 己酉"),
    ("乾隆", "辛卯 丁酉 庚午 丙子"),
    ("朱家骅", "癸巳 丁巳 丁卯 丙午"),
    ("王克敏", "丙子 壬辰 壬申 乙巳"),
    ("蔡元培", "丁卯 癸丑 丙申 戊子"),
    ("谭延闿", "己卯 丁丑 癸丑 乙卯"),
]

POS = ("year", "month", "day", "hour")

# 成败等价类(2026-11-10): 核验器 BAI 与引擎 PO/CHENG_ZHONG_YOU_PO 是同一判定族
# (败格, 格名仍存, PZZQ L1149「败者犯格之忌也」); NOT_EVALUABLE 双方一致; CHENG=成。
CB_EQUIV = {
    "BAI": {"BAI", "PO", "CHENG_ZHONG_YOU_PO"},
    "PO": {"BAI", "PO", "CHENG_ZHONG_YOU_PO"},
    "CHENG_ZHONG_YOU_PO": {"BAI", "PO", "CHENG_ZHONG_YOU_PO"},
    "CHENG": {"CHENG"},
    "NOT_EVALUABLE": {"NOT_EVALUABLE"},
}


def cb_agree(a: str, b: str) -> bool:
    return b in CB_EQUIV.get(a, {a})


# 特格族: 化气/从格/专旺等核验器无判据的格名前缀 → 归特格族单独计数, 不算取格差异
SPECIAL_GE_PREFIXES = ("化", "从", "专旺", "曲直", "炎上", "稼穑", "从革", "润下")


def ge_base(name) -> str:
    """剥离括号后缀(印格(官印双全)≡印格)并识别特格族。"""
    if not isinstance(name, str):
        return ""
    return name.split("(")[0]


def is_special_ge(name) -> bool:
    base = ge_base(name)
    return any(base.startswith(pre) for pre in SPECIAL_GE_PREFIXES)


def to_pillars(bazi: str) -> dict:
    parts = bazi.split()
    return {POS[i]: [parts[i][0], parts[i][1]] for i in range(4)}


def engine_ge(pillars: dict) -> dict:
    r = production_entry(FrozenCanonicalBaziChart(pillars=pillars))
    gc = (r.get("engine_result") or {}).get("ge_cheng") or {}
    return {"ge": gc.get("ge"), "state": gc.get("cheng_bai"),
            "gate": r.get("gate"), "rule": gc.get("rule")}


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40

    print("== 原典 12 案：核验器 vs 引擎 ==")
    for name, bazi in CASES:
        p = to_pillars(bazi)
        c_ge = derive_ge(p)
        c_cb = judge_cheng_bai(p)
        e = engine_ge(p)
        mark = "  " if (ge_base(c_ge["ge"]) == ge_base(e["ge"])
                        and cb_agree(c_cb["state"], e["state"])) else "!!"
        print(f"{mark} {name:6s} {bazi} | 核验={c_ge['ge']}/{c_cb['state']} 引擎={e['ge']}/{e['state']}")
        if ge_base(c_ge["ge"]) != ge_base(e["ge"]):
            print(f"      取格差异: 核验={c_ge['detail']} | 引擎 rule={e['rule']}")

    random.seed(20261107)
    ge_diff = 0
    cb_diff = 0
    special_diff = 0
    special_cb_diff = 0
    ge_samples = []
    cb_samples = []
    special_samples = []
    special_cb_samples = []
    total = 0
    for i in range(n):
        y = random.randint(1950, 2005)
        m = random.randint(1, 12)
        d = random.randint(1, 28)
        h = random.choice([0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22])
        chart = BaziEngine().compute((y, m, d, h), gender="male")
        p = {k: [v[0], v[1]] for k, v in chart.get_pillars_chinese().items()}
        c_ge = derive_ge(p)
        c_cb = judge_cheng_bai(p)
        e = engine_ge(p)
        total += 1
        bazi = " ".join(p[k][0] + p[k][1] for k in POS)
        if ge_base(c_ge["ge"]) != ge_base(e["ge"]):
            if is_special_ge(c_ge["ge"]) or is_special_ge(e["ge"]):
                # 特格族(化气/从格/专旺): 核验器无判据, 登记族计数不算差异
                special_diff += 1
                if len(special_samples) < 6:
                    special_samples.append((bazi, c_ge["ge"], e["ge"]))
            else:
                ge_diff += 1
                if len(ge_samples) < 6:
                    ge_samples.append((bazi, c_ge["ge"], e["ge"], c_ge["detail"]))
        if not cb_agree(c_cb["state"], e["state"]):
            if is_special_ge(c_ge["ge"]) or is_special_ge(e["ge"]):
                # A2 特格族成败(化气/从格/专旺): 核验器无判据, 成败不可比, 登记族计数
                special_cb_diff += 1
                if len(special_cb_samples) < 6:
                    special_cb_samples.append((bazi, c_cb["state"], e["state"], c_ge["ge"], e["ge"]))
            else:
                cb_diff += 1
                if len(cb_samples) < 6:
                    cb_samples.append((bazi, c_cb["state"], e["state"], c_cb["ge"], [c["clause"] for c in c_cb["clauses"]]))

    print(f"\n== 随机 {total} 盘 ==")
    print(f"取格不一致 {ge_diff}/{total}（特格族另计 {special_diff}）")
    for s in ge_samples:
        print(f"  {s[0]} 核验={s[1]} 引擎={s[2]} | {s[3]}")
    for s in special_samples:
        print(f"  [特格族] {s[0]} 核验={s[1]} 引擎={s[2]}")
    print(f"成败不一致 {cb_diff}/{total}（特格族成败另计 {special_cb_diff}）")
    for s in cb_samples:
        print(f"  {s[0]} 核验={s[1]} 引擎={s[2]} | 格={s[3]} | {s[4]}")
    for s in special_cb_samples:
        print(f"  [特格族成败] {s[0]} 核验={s[1]}({s[3]}) 引擎={s[2]}({s[4]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
