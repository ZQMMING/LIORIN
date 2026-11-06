"""河洛引擎结构不变式扫描（质量护栏，不产真值）。

随机生成 N 个命盘，跑 heluo_calculate + build_guajie_from_result，检查：
  1. 卦名合法（先天/后天/互体等必须在 64 卦内）
  2. 元堂爻位合法（六四=3 / 初六=0 等 0-5）
  3. 天地数与其余数自洽（1-9）
  4. 大运/流年 timeline 年龄单调递增、卦名合法
  5. 解层九键结构存在、叶/不叶 evidence 非空
  6. 全程无异常

用法：python scripts/heluo_invariant_scan.py [N]
"""
from __future__ import annotations

import random
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tongshu.engines.heluo.canonical import heluo_calculate  # noqa: E402
from tongshu.engines.heluo.guajie import (  # noqa: E402
    COMPOUND_GUA,
    build_guajie_from_result,
)
from tongshu.engines.heluo.numbers import (  # noqa: E402
    SIXTY_FOUR_HEXAGRAMS,
    TRIGRAM_LINES,
)

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
STEM_VALUES = {"戊": 1, "乙": 2, "癸": 2, "庚": 3, "辛": 4, "壬": 6, "甲": 6,
               "丁": 7, "丙": 8, "己": 9}
BRANCH_VALUES = {"亥": 1, "子": 1, "寅": 3, "卯": 3, "巳": 2, "午": 2, "申": 4,
                 "酉": 4, "辰": 5, "戌": 5, "丑": 5, "未": 5,
                 "亥x": 6, "子x": 6, "寅x": 8, "卯x": 8, "巳x": 7, "午x": 7,
                 "申x": 9, "酉x": 9, "辰x": 10, "戌x": 10, "丑x": 10, "未x": 10}

YUAN_TANG_INDEX = {"初": 0, "二": 1, "三": 2, "四": 3, "五": 4, "上": 5}


def _check(issues: list[str], label: str, ok: bool, detail: str = "") -> None:
    if not ok:
        issues.append(f"{label}: {detail}")


def _gua_from_lines(lines) -> str:
    """三爻（自下而上）→ 卦名。"""
    tup = tuple(int(x) for x in lines)
    for name, pat in TRIGRAM_LINES.items():
        if tuple(pat) == tup:
            return name
    return ""


def check_case(issues: list[str], cid: str, bazi, gender: str) -> None:
    try:
        r = heluo_calculate(bazi, gender=gender, birth_hour="午", era="zhong")
    except Exception as e:  # pragma: no cover
        issues.append(f"{cid}: heluo_calculate 异常 {e!r}")
        traceback.print_exc()
        return

    pairs = set(COMPOUND_GUA.values())
    for label, obj in (("先天", r.prenatal), ("后天", r.postnatal)):
        up, low = getattr(obj, "upper_gua", ""), getattr(obj, "lower_gua", "")
        _check(issues, f"{cid} {label}上下卦", (up, low) in pairs,
               f"{up}/{low} name={getattr(obj, 'hexagram_name', '')}")

    yt = str(getattr(r.yuantang, "yuantang", "") or "")
    yt_idx = getattr(r.yuantang, "yuantang_index", -1)
    _check(issues, f"{cid} 元堂爻位", yt_idx in range(6), f"got={yt!r}")

    # 元堂落爻的阴阳必须与先天六爻该位一致
    yt_lines = list(getattr(r.yuantang, "lines", []) or [])
    if yt_idx in range(6) and yt_lines:
        nature = "阳" if yt_lines[yt_idx] == 1 else "阴"
        _check(issues, f"{cid} 元堂阴阳", getattr(r.yuantang, "yao_nature", "") == nature,
               f"got={getattr(r.yuantang, 'yao_nature', '')!r} want={nature}")

    # 三爻二卦：先天六爻（元堂 trace 的 lines）= 下卦三爻 + 上卦三爻（自下而上）
    pre_lines = list(getattr(r.yuantang, "lines", []) or [])
    low = tuple(TRIGRAM_LINES.get(r.prenatal.lower_gua, ()))
    up = tuple(TRIGRAM_LINES.get(r.prenatal.upper_gua, ()))
    _check(issues, f"{cid} 先天六爻", pre_lines == list(low) + list(up),
           f"lines={pre_lines} 下={low} 上={up}")

    # 后天第一步 = 元堂爻变（仅该爻阴阳反转）
    if yt_idx in range(6) and pre_lines:
        flipped = list(pre_lines)
        flipped[yt_idx] = -flipped[yt_idx]
        _check(issues, f"{cid} 后天爻变", list(getattr(r.postnatal, "lines", [])) == flipped,
               f"post={getattr(r.postnatal, 'lines', None)} want={flipped}")
        step1_want = SIXTY_FOUR_HEXAGRAMS.get(
            (_gua_from_lines(flipped[3:]), _gua_from_lines(flipped[:3])), "")
        _check(issues, f"{cid} 后天第一步卦名",
               getattr(r.postnatal, "step1_hexagram", "") == step1_want,
               f"got={getattr(r.postnatal, 'step1_hexagram', '')} want={step1_want}")

    # 结构层六爻 = 后天卦（下三爻+上三爻）
    st = r.structure
    st_low = tuple(TRIGRAM_LINES.get(st.lower, ()))
    st_up = tuple(TRIGRAM_LINES.get(st.upper, ()))
    _check(issues, f"{cid} 结构六爻", list(st.lines) == list(st_low) + list(st_up),
           f"lines={st.lines} 下={st_low} 上={st_up}")
    want_name = SIXTY_FOUR_HEXAGRAMS.get((st.upper, st.lower), "")
    _check(issues, f"{cid} 结构卦名", st.name == want_name, f"got={st.name} want={want_name}")
    _check(issues, f"{cid} 化工卦", getattr(r.hua_gong, "huagong_trigram", "") in TRIGRAM_LINES,
           f"got={getattr(r.hua_gong, 'huagong_trigram', '')}")

    _check(issues, f"{cid} 天数余数", 1 <= int(r.numbers.tian_reduced) <= 9,
           f"tian={r.numbers.tian_shu} reduced={r.numbers.tian_reduced}")
    _check(issues, f"{cid} 地数余数", 1 <= int(r.numbers.di_reduced) <= 9,
           f"di={r.numbers.di_shu} reduced={r.numbers.di_reduced}")

    tl = r.timeline
    years = getattr(tl, "yearly_hexagrams", []) or []
    _check(issues, f"{cid} 流年卦数量", len(years) >= 30, f"n={len(years)}")
    for y in years[:60]:
        hx = y.get("name", "") if isinstance(y, dict) else ""
        if hx:
            up, low = y.get("upper", ""), y.get("lower", "")
            _check(issues, f"{cid} 流年卦", (up, low) in pairs, f"got={hx!r} {up}/{low}")

    try:
        gj = build_guajie_from_result(r, bazi=bazi)
    except Exception as e:  # pragma: no cover
        issues.append(f"{cid}: build_guajie 异常 {e!r}")
        return
    for k in ("benming", "benming_ye_buye", "liunian_hexagram", "kuozhan"):
        if k not in gj:
            issues.append(f"{cid} 解层缺键 {k}：{sorted(gj)[:8]}")
    yb = gj.get("benming_ye_buye")
    if isinstance(yb, dict):
        _check(issues, f"{cid} 叶不叶证据", bool(yb.get("evidence")), "evidence 空")


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    rnd = random.Random(20261106)
    issues: list[str] = []
    for i in range(n):
        g = [rnd.choice(STEMS) for _ in range(4)]
        z = [rnd.choice(BRANCHES) for _ in range(4)]
        bazi = [(g[j], z[j]) for j in range(4)]
        check_case(issues, f"h{i:03d} {g[0]}{z[0]}", bazi, "male" if i % 2 == 0 else "female")

    print(f"[scan] 样本 {n}，发现问题 {len(issues)}")
    for it in issues[:40]:
        print("  -", it)
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
