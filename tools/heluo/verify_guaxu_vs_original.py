# -*- coding: utf-8 -*-
"""独立核验：原典自述的六十四卦「上X下Y」 vs 代码卦表。

不依赖代码的六合十四卦表来验证元堂实例——先证明卦表本身站得住。
原典来源：卷下「六十四卦断」章，每卦释义句里明写「上X下Y，中存…」。
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.numbers import SIXTY_FOUR_HEXAGRAMS  # noqa: E402

TXT = Path(r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
           r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6"
           r"_07333092-河洛真数——原著.txt")

TRIG = "乾兑离震巽坎艮坤"
PAT = re.compile(rf"上([{TRIG}])下([{TRIG}])")

# 元堂实例里出现的 12 卦（原典「定元堂式」L255-288）
YT_GUAS = ["小畜", "讼", "咸", "明夷", "颐", "升", "谦", "屯", "既济", "大过",
           "遁", "渐"]


def main() -> None:
    lines = TXT.read_text(encoding="utf-8").splitlines()

    # 代码卦表：全名 -> (upper, lower)，再压成简称便于与原典对撞
    # 全名格式 = 上卦名 + 下卦名 + 简称（如「风天小畜」=巽+乾+小畜）；
    # 纯卦为「乾为天」「坤为地」，简称取首字。
    full2ul = {v: k for k, v in SIXTY_FOUR_HEXAGRAMS.items()}
    code = {}
    for _full, _ul in full2ul.items():
        _short = _full[2:] if not _full[2:].startswith("为") else _full[0]
        code[_short] = _ul
    # 按长度降序，保证「小畜」优先于「畜」这类前缀误配
    shorts = sorted(code, key=len, reverse=True)

    found: list[tuple[int, str, str, str, str]] = []
    for i, ln in enumerate(lines, 1):
        m = PAT.search(ln)
        if not m:
            continue
        upper, lower = m.group(1), m.group(2)
        head = ln[:m.start()]
        # 卦名 = 「上X下Y」之前出现的最靠右的已知卦名简称
        name, best = None, -1
        for s in shorts:
            idx = head.rfind(s)
            if idx > best:
                name, best = s, idx
        found.append((i, name or "?", upper, lower, ln[:46]))

    print("=" * 78)
    print(f"原典自述卦序条目：{len(found)} 条")
    print("=" * 78)

    match = mismatch = unknown = 0
    bad_lines: list[tuple] = []
    for ln_no, name, upper, lower, snippet in found:
        if name not in code:
            unknown += 1
            continue
        c_up, c_lo = code[name]
        ok = (c_up == upper and c_lo == lower)
        if ok:
            match += 1
        else:
            mismatch += 1
            bad_lines.append((ln_no, name, (upper, lower), (c_up, c_lo), snippet))

    print(f"  与代码卦表一致 : {match}")
    print(f"  与代码卦表不一致: {mismatch}")
    print(f"  卦名未能解析   : {unknown}")
    print()

    print("=" * 78)
    print("未能解析的条目（供人工判读）")
    print("=" * 78)
    for ln_no, name, upper, lower, snippet in found:
        if name not in code:
            print(f"  L{ln_no}  识别为「{name}」  原典：上{upper}下{lower}")
            print(f"     {snippet}…")
    print()

    print("=" * 78)
    print("不一致明细")
    print("=" * 78)
    if not bad_lines:
        print("  （无）")
    for ln_no, name, orig, cod, snippet in bad_lines:
        print(f"  L{ln_no}  {name}")
        print(f"     原典：上{orig[0]}下{orig[1]}   代码：上{cod[0]}下{cod[1]}")
        print(f"     原文：{snippet}…")
    print()

    print("=" * 78)
    print("元堂实例所用 12 卦：原典卦序 vs 代码卦表")
    print("=" * 78)
    orig_map = {}
    for ln_no, name, upper, lower, snippet in found:
        if name in YT_GUAS:
            orig_map[name] = (ln_no, upper, lower)
    for g in YT_GUAS:
        c_up, c_lo = code.get(g, ("?", "?"))
        if g in orig_map:
            ln_no, o_up, o_lo = orig_map[g]
            flag = "✓" if (o_up, o_lo) == (c_up, c_lo) else "✗"
            print(f"  {flag} {g:4s} 原典L{ln_no}: 上{o_up}下{o_lo}"
                  f"   代码: 上{c_up}下{c_lo}")
        else:
            print(f"  - {g:4s} 原典释义章未见   代码: 上{c_up}下{c_lo}")
    print()

    print("=" * 78)
    print("交叉裁决：元堂实例本身能否定住卦序？")
    print("=" * 78)
    print("  小畜（L255）：午未同在六四，申九五，酉上九，戌初九，亥九二")
    for up, lo in (("巽", "乾"), ("巽", "坤")):
        from tongshu.engines.heluo.numbers import TRIGRAM_LINES, build_six_lines
        lines6 = list(TRIGRAM_LINES[lo]) + list(TRIGRAM_LINES[up])
        yin = [i for i, l in enumerate(lines6) if l == -1]
        POS = ["初", "二", "三", "四", "五", "上"]
        if len(yin) == 1:
            # 一阴卦：午未同爻，第三时起寄位，回绕
            opp = [i for i, l in enumerate(lines6) if l == 1]
            seq = [i for i in opp if i > yin[0]] + [i for i in opp if i <= yin[0]]
            got = [yin[0], yin[0]] + seq[:4]
        else:
            got = yin[:2] + [None] * 4
        names = []
        for g in got:
            if g is None:
                names.append("?")
            else:
                pol = "九" if lines6[g] == 1 else "六"
                names.append(f"{POS[g]}{pol}" if g in (0, 5) else f"{pol}{POS[g]}")
        want = ["六四", "六四", "九五", "上九", "初九", "九二"]
        ok = names == want
        print(f"    上{up}下{lo} → 阴爻 idx={yin}  推得 {' '.join(names)}  "
              f"{'✓ 与原典吻合' if ok else '✗ 与原典不符'}")

    print()
    print("=" * 78)
    print("爻画独立反证：用原典实例的爻名反推八卦三画")
    print("=" * 78)
    print("  逻辑：原典实例直接点了爻名（如「渐卦第三阴爻正是六四」），")
    print("        配合已验证的上下卦，即可反推该三画的阴阳排布，")
    print("        与代码 TRIGRAM_LINES 无关。")
    from tongshu.engines.heluo.numbers import TRIGRAM_LINES
    POS = ["初", "二", "三", "四", "五", "上"]
    probes = [
        # (说明, 上卦, 下卦, 断言：某 index 的阴阳及爻名)
        ("L255 小畜「午未同在六四」→ 上巽初爻为阴",
         "巽", "乾", {3: (-1, "六四"), 4: (1, "九五"), 5: (1, "上九")}),
        ("L258 讼「午初六，未六三」→ 下坎初/三位为阴、二位为阳",
         "乾", "坎", {0: (-1, "初六"), 1: (1, "九二"), 2: (-1, "六三")}),
        ("L288 渐「第三阴爻正是六四」→ 上巽初爻为阴",
         "巽", "艮", {3: (-1, "六四")}),
        ("L261 咸「亥在上六」→ 上兑上爻为阴",
         "兑", "艮", {5: (-1, "上六")}),
        ("L282 大过「巳时…初六」→ 下巽初爻为阴",
         "兑", "巽", {0: (-1, "初六")}),
        ("L264 明夷「戌时…初九」→ 下离初爻为阳",
         "坤", "离", {0: (1, "初九")}),
    ]
    all_ok = True
    for desc, up, lo, asserts in probes:
        lines6 = list(TRIGRAM_LINES[lo]) + list(TRIGRAM_LINES[up])
        bits = []
        for idx, (pol, nm) in sorted(asserts.items()):
            got_pol = lines6[idx]
            t = "九" if got_pol == 1 else "六"
            got_nm = (f"{POS[idx]}{t}" if idx in (0, 5) else f"{t}{POS[idx]}")
            ok = (got_pol == pol and got_nm == nm)
            all_ok &= ok
            bits.append(f"{idx}:{got_nm}{'✓' if ok else '✗'}")
        print(f"  {'✓' if all(b.endswith('✓') for b in bits) else '✗'} {desc}")
        print(f"      {'  '.join(bits)}")
    print()
    print(f"  结论：{'代码 TRIGRAM_LINES 全部通过原典爻名反证' if all_ok else '存在不符'}")
    print()
    for t in "乾兑离震巽坎艮坤":
        v = TRIGRAM_LINES[t]
        bar = "".join("▅" if x == 1 else "▁" for x in v)
        pol = "".join("阳" if x == 1 else "阴" for x in v)
        print(f"    {t} = {bar}  自下而上 {pol}")


if __name__ == "__main__":
    main()
