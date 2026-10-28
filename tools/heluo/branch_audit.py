# -*- coding: utf-8 -*-
"""元堂分支的原典支撑度盘点：每个 action 档位有多少原典实例、覆盖多少卦。"""
import io
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.numbers import (  # noqa: E402
    SIXTY_FOUR_HEXAGRAMS, TRIGRAM_LINES, build_six_lines,
)
from heluo_engine.engines.heluo.yuan_tang import HOUR_NAMES, find_yuantang  # noqa: E402

NAME2UL = {v: k for k, v in SIXTY_FOUR_HEXAGRAMS.items()}
ALL = {}
for name, (up, lo) in NAME2UL.items():
    ALL[name] = build_six_lines(up, lo)
for t in TRIGRAM_LINES:
    v = list(TRIGRAM_LINES[t])
    ALL[t + "为" + t] = v + v

# 原典实例：卦 → {时辰: 元堂}
INSTANCES = {
    "小畜": {"午": "六四", "未": "六四", "申": "九五", "酉": "上九",
             "戌": "初九", "亥": "九二"},
    "讼": {"午": "初六", "未": "六三", "申": "初六", "酉": "六三", "戌": "九四"},
    "咸": {"亥": "上六"},
    "明夷": {"戌": "初九"},
    "颐": {"亥": "初九"},
    "升": {"亥": "九三"},
    "谦": {"亥": "九三"},
    "屯": {"巳": "六二"},
    "既济": {"巳": "九五"},
    "大过": {"巳": "初六"},
    "遁": {"巳": "六二"},
    "渐": {"申": "六四"},
}

SHORT2FULL = {}


def full(short: str) -> str:
    if short in ALL:
        return short
    hits = [v for v in ALL if v.endswith(short)]
    if len(hits) != 1:
        raise KeyError(f"{short} -> {hits}")
    return hits[0]


def action_of(gua_full: str, hour: str) -> str:
    lines = ALL[gua_full]
    y = find_yuantang(six_lines=lines, birth_hour=hour, gender="male",
                      xiantian_name=gua_full, solar_phase="winter")
    return y.trace[0]["action"]


def main() -> None:
    print("=" * 78)
    print("A. 原典实例验算 + 命中的 action 档位")
    print("=" * 78)
    hit = tot = 0
    hit_actions: Counter = Counter()
    for short, table_ in INSTANCES.items():
        g = full(short)
        for h, want in table_.items():
            tot += 1
            y = find_yuantang(six_lines=ALL[g], birth_hour=h, gender="male",
                              xiantian_name=g, solar_phase="winter")
            act = y.trace[0]["action"]
            ok = y.yuantang == want
            hit += ok
            hit_actions[act] += ok
            flag = "OK " if ok else "MISS"
            print(f"  [{flag}] {short:4s} {h}时  原典「{want}」  "
                  f"实测「{y.yuantang}」  {act}")
    print(f"\n  合计 {hit}/{tot} 中\n")

    print("=" * 78)
    print("B. 全部 64 卦 × 12 时的 action 分布（无性别/节气差异：非纯卦）")
    print("=" * 78)
    all_actions: Counter = Counter()
    guas_by_action: dict = defaultdict(set)
    for g in sorted(ALL):
        for h in HOUR_NAMES:
            a = action_of(g, h)
            all_actions[a] += 1
            guas_by_action[a].add(g)
    for a, c in all_actions.most_common():
        print(f"  {a:20s} {c:5d} 次  覆盖 {len(guas_by_action[a]):2d} 卦  "
              f"| 原典实例命中 {hit_actions[a]:2d} 次")
    print()

    print("=" * 78)
    print("C. 无原典实例支撑的分支（重点）")
    print("=" * 78)
    for a in sorted(all_actions):
        if hit_actions[a] == 0:
            print(f"  ⚠ {a}：覆盖 {len(guas_by_action[a])} 卦 / {all_actions[a]} 次，"
                  f"原典实例 0")
            for g in sorted(guas_by_action[a]):
                lines = ALL[g]
                yang = [i for i, l in enumerate(lines) if l == 1]
                yin = [i for i, l in enumerate(lines) if l == -1]
                print(f"      {g:8s} 阳{len(yang)}{yang} 阴{len(yin)}{yin}")
    print()

    print("=" * 78)
    print("D. n_same 档位 × 卦数")
    print("=" * 78)
    dist: Counter = Counter()
    for g in sorted(ALL):
        lines = ALL[g]
        ny = sum(1 for l in lines if l == 1)
        nyy = 6 - ny
        dist[(ny, nyy)] += 1
    for (ny, nyy), c in sorted(dist.items()):
        print(f"  阳{ny}阴{nyy}: {c} 卦")
    print()

    print("=" * 78)
    print("E. 纯卦：solar_phase 冬/夏两版输出（是否同族规则）")
    print("=" * 78)
    for g in ("乾为天", "坤为地"):
        for gender in ("male", "female"):
            seqs = {}
            for phase in ("winter", "summer"):
                rows = []
                for h in HOUR_NAMES:
                    y = find_yuantang(six_lines=ALL[g], birth_hour=h,
                                      gender=gender, xiantian_name=g,
                                      solar_phase=phase)
                    rows.append(y.yuantang_index)
                seqs[phase] = rows
            same = seqs["winter"] == seqs["summer"]
            print(f"  {g}/{gender}: winter={seqs['winter']}")
            print(f"  {' ' * len(g)}   summer={seqs['summer']}"
                  f"   {'【相同】' if same else '【不同 → 两套异族规则】'}")
    print()


if __name__ == "__main__":
    main()
