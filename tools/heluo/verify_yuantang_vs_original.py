# -*- coding: utf-8 -*-
"""元堂算法深度核验：拿原典逐盘实例当测试用例。

用例来源：《河洛真数·起例卷》
  L222 爻位元堂式（总纲）  L231-252 定元堂式（七条）  L255-288 逐盘实例
  L291-318 乾坤卦元堂式（纯卦四条 + 冬夏分支）
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.numbers import (  # noqa: E402
    SIXTY_FOUR_HEXAGRAMS, TRIGRAM_LINES, build_six_lines,
)
from tongshu.engines.heluo.yuan_tang import (  # noqa: E402
    HOUR_NAMES, find_yuantang,
)

POS = ["初", "二", "三", "四", "五", "上"]
NAME2UL = {v: k for k, v in SIXTY_FOUR_HEXAGRAMS.items()}


def _full(gua: str) -> str:
    """简称（渐/小畜/讼）→ 全名（风山渐/风天小畜/天水讼）。"""
    if gua in NAME2UL:
        return gua
    hits = [v for v in NAME2UL if v.endswith(gua)]
    if len(hits) != 1:
        raise KeyError(f"卦名无法唯一解析：{gua} -> {hits}")
    return hits[0]


def lines_of(gua: str) -> list[int]:
    if gua in TRIGRAM_LINES:                 # 纯卦：乾/坤 直接给六爻
        v = list(TRIGRAM_LINES[gua])
        return v + v
    upper, lower = NAME2UL[_full(gua)]
    return build_six_lines(upper, lower)


def yao_name(idx: int, pol: int) -> str:
    t = "九" if pol == 1 else "六"
    return f"{POS[idx]}{t}" if idx in (0, 5) else f"{t}{POS[idx]}"


def table(gua: str, gender: str, phase: str) -> list[tuple[str, str]]:
    lines = lines_of(gua)
    out = []
    for h in HOUR_NAMES:
        y = find_yuantang(six_lines=lines, birth_hour=h, gender=gender,
                          xiantian_name=gua, solar_phase=phase)
        out.append((h, y.yuantang))
    return out


# ── 原典逐盘实例 ──────────────────────────────────────────────
# (卦, 时辰, 原典元堂, 整组原典断语, 备注)
CASES = [
    ("小畜", "亥", "九二",
     "午未同在六四，申九五，酉上九，戌初九，亥九二", "一阴卦·午未同爻→申起寄阳"),
    ("讼", "戌", "九四",
     "午初六，未六三，申复初六，酉复六三，戌九四", "二阴卦·两次往复→第五时寄阳"),
    ("咸", "亥", "上六", "亥在上六", "—"),
    ("明夷", "戌", "初九", "戌时得明夷，元堂初九", "—"),
    ("颐", "亥", "初九", "亥时得颐，元堂初九", "—"),
    ("升", "亥", "九三", "亥时得升，元堂九三", "—"),
    ("谦", "亥", "九三", "亥时得谦，元堂九三", "—"),
    ("屯", "巳", "六二", "巳时得屯，元堂六二", "—"),
    ("既济", "巳", "九五", "巳时得既济，元堂九五", "—"),
    ("大过", "巳", "初六", "巳时得大过，元堂在初六", "—"),
    ("遁", "巳", "六二", "巳时得遁，元堂在六二", "—"),
    ("渐", "申", "六四",
     "申时是第三个阴时，合在本卦第三阴爻…正是六四", "原典自释：第三阴时取第三阴爻"),
]

# 男女：阳时组（子..巳）男女同路径；阴时组看时辰
# 女命走阳时组 + 阴时组都按原典「阴时取阴爻」；男女差异仅在纯卦。


def main() -> None:
    print("=" * 76)
    print("一、原典逐盘实例验算（定元堂式 L255-288）")
    print("=" * 76)
    hit = 0
    for gua, hour, want, quote, note in CASES:
        lines = lines_of(gua)
        got = None
        for gender in ("male", "female"):
            for phase in ("winter", "summer"):
                y = find_yuantang(six_lines=lines, birth_hour=hour,
                                  gender=gender, xiantian_name=gua,
                                  solar_phase=phase)
                if y.yuantang == want:
                    got = (gender, phase, y.yuantang)
                    break
            if got:
                break
        ok = got is not None
        hit += ok
        six = "".join("▅" if l == 1 else "▁" for l in reversed(lines))
        mark = "OK  " if ok else "MISS"
        detail = (f"实测={got[2]}({got[0]},{got[1]})" if got
                  else "四种组合均不命中")
        print(f"  [{mark}] {gua} {hour}时  原典作「{want}」  {detail}")
        print(f"         六爻(上→下) {six}   {note}")
        print(f"         原典：{quote}")
    print()
    print(f"  合计：{hit}/{len(CASES)} 中")
    print()

    print("=" * 76)
    print("二、小畜 / 讼 两组全时辰展开（原典给了整组断语）")
    print("=" * 76)
    for gua in ("小畜", "讼", "渐"):
        lines = lines_of(gua)
        n_same = sum(1 for l in lines if l == -1)
        n_yang = sum(1 for l in lines if l == 1)
        print(f"  ── {gua}  阳爻{len([i for i,l in enumerate(lines) if l==1])}个 / "
              f"阴爻{len([i for i,l in enumerate(lines) if l==-1])}个")
        for h, name in table(gua, "male", "winter"):
            print(f"       {h}时 → {name}")
        print()

    print("=" * 76)
    print("三、纯卦四条 + solar_phase 分支（L306-315 / L297-300）")
    print("=" * 76)
    print("  L297 正文：女得乾，冬至后至夏至前自上而下；夏至后至冬至前自下而上")
    print("  L300 正文：男得坤，冬至后至夏至前自上而下；夏至后至冬至前自下而上")
    for gua, genders in (("乾", ("male", "female")), ("坤", ("male", "female"))):
        for g in genders:
            for phase in ("winter", "summer"):
                seq = " ".join(f"{h}={n}" for h, n in table(gua, g, phase))
                print(f"  {gua}/{g}/{phase:6s}: {seq}")
    print()

    print("=" * 76)
    print("四、L318 交叉检验：十一月冬至生乾卦「元堂居初九」")
    print("=" * 76)
    for g in ("male", "female"):
        seq = " ".join(f"{h}={n}" for h, n in table("乾", g, "winter"))
        print(f"  乾/{g}/winter: {seq}")
    print("  → 原典 L318 称冬至生乾卦元堂居初九；"
          "重数说下子时/卯时落初九，正文线性说下子时落初九。")
    print()


if __name__ == "__main__":
    main()
