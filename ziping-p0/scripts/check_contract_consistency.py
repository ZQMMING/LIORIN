# -*- coding: utf-8 -*-
"""契约文档提交前一致性检查 (裁七十丙)

★ 脚本职责 = 「把散落的同主题记录聚到一处给人看」,【不自动判冲突】。
  理由: 「数字不同」可能是「口径不同」(13 是三组合计 / 18 是实测键数),
        自动判定必然误报。判断仍由人做 —— 与「契约是事实声明, 核验靠人工」一致。

起因: v1.6 同一次 commit 内并存两个数字 —— §2.7.5「合计 = 13 个」
      与 §4.14「实测键数 = 18」。提交前无检查, 数字漂移。详见契约 §8.2。

检查三类: 数字 / 标签 / 表标题。
输出格式: 关键词 | 出现节 | 行号 | 上下文行（按关键词分组, 组内按行号排）。
"""
import io
import os
import re
import sys

DOC = r"D:/shuntian-ziping-p0/p0_v2/l3_contract_spec.md"

# ── 关键词表（可扩: 首版跑完看漏了什么再补）────────────────────
KEYWORDS = {
    "l3_contract键数": [
        r"合计\s*=\s*\d+\s*个", r"实测键数\s*=\s*\d+", r"l3_contract\s*\d+\s*键",
        r"\d+\s*键\s*\(",
    ],
    "compare_key四档标签": [
        r"第1位\s+mo", r"第2位\s+dang", r"第3位\s+-tou", r"第4位\s+-ben",
        r"字典序顺序本身",
    ],
    "六本盘数": [
        r"六本\s*\d+\s*盘", r"2106\s*盘", r"盘数\s*=\s*\d+",
        r"\d{4}\s*/\s*\d{4}\s*盘",
    ],
    "compare_key分级表": [
        r"\|\s*`mo`\s*\|", r"\|\s*`dang`\s*\|", r"\|\s*`-tou`\s*\|",
        r"\|\s*`-ben`\s*\|",
    ],
    "L215条件互斥": [
        r"条件互斥优先级型", r"此二者，乃体用之正法", r"usable_as_criteria\s*=\s*False",
    ],
    "5冲激字段": [
        r"冲激字段", r"chong_adjust", r"ling_state_eff",
    ],
    "判层措辞": [
        r"判层归属", r"接口存在, 但被禁止出值", r"判层【暂不存在】",
    ],
}

# 标签扫描（单独一类, 因为它跨节漂移最频繁）
TAGS = ["DTS_CITED", "ENGINE_DEFINED_CONFLICT", "ENGINE_DEFINED",
        "ENGINEERING_UNVERIFIED", "NOT_AUTHORIZED", "UNDETERMINED",
        "usable_as_criteria", "condition_2_pending", "inert",
        "SAME_KEYS_DUAL", "NOT_MEASURED"]

SKIP_DIR = {"__pycache__", ".git"}


def load_sections(lines):
    """[(起始行号, 节标题)]"""
    secs = []
    cur = (1, "(文件头)")
    for i, l in enumerate(lines, 1):
        m = re.match(r"^(#{2,4})\s+(.*)", l)
        if m:
            secs.append(cur)
            cur = (i, m.group(2).strip())
    secs.append(cur)
    return secs


def section_of(secs, lineno):
    name = "(文件头)"
    for start, title in secs:
        if start <= lineno:
            name = title
        else:
            break
    return name


def main():
    if not os.path.exists(DOC):
        print("契约文档不存在: %s" % DOC)
        return 1
    with io.open(DOC, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    secs = load_sections(lines)

    print("=" * 96)
    print("契约一致性检查 (裁七十丙)  —— %s" % os.path.basename(DOC))
    print("  总行数 %d / 节数 %d" % (len(lines), len(secs) - 1))
    print("=" * 96)
    print("★ 脚本只聚合同主题记录, 不自动判冲突 —— 判断由人做。")

    total = 0
    # ── 一、数字 + 表标题 ──
    for topic, pats in KEYWORDS.items():
        hits = []
        for i, l in enumerate(lines, 1):
            for pat in pats:
                m = re.search(pat, l)
                if m:
                    hits.append((i, m.group(0), l.strip()))
                    break
        if not hits:
            continue
        print("\n" + "-" * 96)
        print("【%s】 命中 %d 行 / 分布 %d 节"
              % (topic, len(hits), len(set(section_of(secs, h[0]) for h in hits))))
        print("-" * 96)
        print("  %-46s %-5s %s" % ("节", "行号", "上下文"))
        for i, g, txt in hits:
            print("  %-46s L%-5d %s" % (section_of(secs, i)[:44], i, txt[:74]))
        total += len(hits)

    # ── 二、标签 ──
    print("\n" + "=" * 96)
    print("【标签扫描】")
    print("=" * 96)
    for tag in TAGS:
        hits = []
        for i, l in enumerate(lines, 1):
            if tag in l:
                hits.append((i, l.strip()))
        if not hits:
            continue
        secs_hit = sorted(set(section_of(secs, h[0]) for h in hits))
        flag = "  ★ 跨 %d 节 —— 检查是否同一事实多处各记一份" % len(secs_hit) if len(secs_hit) > 1 else ""
        print("\n  %-26s %3d 行 / %d 节%s"
              % (tag, len(hits), len(secs_hit), flag))
        for i, txt in hits[:6]:
            print("      %-40s L%-5d %s" % (section_of(secs, i)[:38], i, txt[:60]))
        if len(hits) > 6:
            print("      …另 %d 行" % (len(hits) - 6))
        total += len(hits)

    # ── 三、表标题 ──
    print("\n" + "=" * 96)
    print("【表标题扫描】同一表头在几节各存一份")
    print("=" * 96)
    heads = {}
    for i, l in enumerate(lines, 1):
        s = l.strip()
        if not s.startswith("|") or set(s) <= set("|-: "):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        key = " | ".join(cells)
        heads.setdefault(key, []).append(i)
    dup = 0
    for key, locs in sorted(heads.items(), key=lambda kv: -len(kv[1])):
        if len(locs) > 1:
            dup += 1
            secset = sorted(set(section_of(secs, x) for x in locs))
            print("\n  ★ 表头 %s" % key[:74])
            print("      出现 %d 行 / %d 节: %s"
                  % (len(locs), len(secset), ", ".join(s[:26] for s in secset)))
            for x in locs:
                print("        %-42s L%d" % (section_of(secs, x)[:40], x))
    if not dup:
        print("  (无重复表头)")
    total += dup

    print("\n" + "=" * 96)
    print("汇总: 命中 %d 处。★ 逐条人工判「同主题记录是否分散 / 数字标签是否冲突」。" % total)
    print("=" * 96)
    return 0


if __name__ == "__main__":
    sys.exit(main())