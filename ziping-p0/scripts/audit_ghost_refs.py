# -*- coding: utf-8 -*-
"""裁八十二丙: 211 条虚引用的「消费核」三步走

★ 关键: 按【数据流】定性, 不按字符串出现。
  「在库里找不到」是已知事实, 但后果取决于是否被消费:
    甲类 纯元数据标记(注释/日志, 无代码消费)        → 影响面 0
    乙类 被代码消费(查库/比较/索引) 但从未命中       → P1 断链
    丙类 被消费但容忍不存在(.get默认/try吞)        → P1 静默容错隐患

三步:
  1 所在位置: 该 ID 出现在什么上下文(注释/字符串字面/字典值/...)
  2 变量流:   该值所在字典/列表被谁读, 读后传给谁
  3 消费分类: 沿数据流看最终用途

同时核反向: 引擎是否有任何代码按「切片ID」寻址切片内容。
"""
import io
import os
import re
import ast
import collections

ROOT = r"D:/shuntian-ziping-p0"
SCAN = ["engines", "p0_v2", "spec", "scripts", "tests"]
SKIP = {"__pycache__", ".git", "node_modules"}

RX = re.compile(r"\b(DTS|PZZQ|QTBJ|SFTK|SMTH|YHZP)-(\d{3})-(\d{3})\b")

# 消费型函数名(在这些上下文里出现 ID 才算「被消费」)
CONSUME_CTX = [
    ("SLICE_LOOKUP", re.compile(
        r"(read_slice|load_slices|_parse_slice|read_slice_full|slice_authority)")),
    ("COMPARE_INDEX", re.compile(
        r"(==\s*['\"]%s|\bin\s+.*%s|idx\[.*\]|\.index\(|%s\s+in\s)" % ("", "", ""))),
    ("DICT_KEY", re.compile(r"[\[(]\s*['\"](DTS|PZZQ|QTBJ|SFTK|SMTH|YHZP)-\d{3}-\d{3}['\"]")),
    ("GET_DEFAULT", re.compile(r"\.get\(\s*['\"](DTS|PZZQ|QTBJ|SFTK|SMTH|YHZP)-\d{3}-\d{3}")),
]


def scan():
    """扫出每条 ID 的所有出现点"""
    hits = collections.defaultdict(list)
    for base in SCAN:
        bp = os.path.join(ROOT, base)
        if not os.path.isdir(bp):
            continue
        for dp, dn, fn in os.walk(bp):
            dn[:] = [d for d in dn if d not in SKIP]
            for f in fn:
                if not f.endswith(".py"):
                    continue
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                try:
                    src = io.open(p, encoding="utf-8-sig", errors="ignore").read()
                except Exception:
                    continue
                for i, l in enumerate(src.split("\n"), 1):
                    for m in RX.finditer(l):
                        hits[m.group(0)].append((rel, i, l.rstrip()))
    return hits


def ctx_kind(line):
    """第一步: 该行上下文类型"""
    s = line.strip()
    if s.startswith("#"):
        return "COMMENT"
    # 字符串字面量里的 ID(非 dict key / 非 get 参数)
    for _, rx in CONSUME_CTX[2:]:
        if rx.search(line):
            return "DICT_KEY"
    for _, rx in CONSUME_CTX[3:]:
        if rx.search(line):
            return "GET_DEFAULT"
    if re.search(r"['\"][^'\"]*%s[^'\"]*['\"]" % RX.pattern.replace(r"\b(", "(")
                 .replace(r"\d{3}", r"\d{3}"), line):
        return "STRING_LITERAL"
    if re.search(r"^\s*(#\s*)?[\"'].*%s" % RX.pattern.replace(r"\b(", "(")
                 .replace(r"\d{3}", r"\d{3}"), line):
        return "STRING_LITERAL"
    return "CODE_OTHER"


def main():
    hits = scan()
    print("=" * 100)
    print("裁八十二丙  虚引用消费核 · 三步   命中 ID %d 条" % len(hits))
    print("=" * 100)

    # ── 第一步: 位置分布 ──
    kinds = collections.Counter()
    per_id_kind = {}
    for i, locs in hits.items():
        ks = set()
        for rel, ln, line in locs:
            k = ctx_kind(line)
            kinds[k] += 1
            ks.add(k)
        per_id_kind[i] = ks

    print("\n【第一步】出现点上下文类型（按出现次数）")
    for k, v in kinds.most_common():
        print("    %-18s %4d 处" % (k, v))

    # ── 第二步+第三步: 变量流与消费分类 ──
    # 对每条 ID, 找它所在容器的字段名, 再找该容器字段被谁读
    print("\n【第二步】字段名提取 → 查该字段是否被下游读")
    FIELD_RX = re.compile(r"['\"]([a-z_]{3,20})['\"]\s*:\s*[^,]*%s" % RX.pattern)
    field_hits = collections.Counter()
    for i, locs in hits.items():
        fs = set()
        for rel, ln, line in locs:
            m = FIELD_RX.search(line)
            if m:
                fs.add(m.group(1))
                field_hits[m.group(1)] += 1
        per_id_kind[i] = (per_id_kind[i], fs)

    print("    出现在字典字段的 ID, 字段名 TOP20:")
    for k, v in field_hits.most_common(20):
        print("        %-24s %4d 条 ID" % (k, v))

    # ── 消费核: 关键字段是否被代码读 ──
    CONSUMED_FIELDS = ["evidence", "evidence_refs", "slice_id", "evidence_chain",
                       "classic_line", "classic_source", "sources", "evidence_chain"]
    print("\n【第三步】消费分类")
    cats = collections.defaultdict(list)
    for i, locs in hits.items():
        fs = per_id_kind[i][1]
        ks = per_id_kind[i][0]
        if "COMMENT" in ks and len(ks) == 1:
            cats["甲_纯注释"].append(i)
            continue
        hit_fields = fs & set(CONSUMED_FIELDS)
        if hit_fields:
            # 该字段是否被下游读? 全仓搜 field 名的读取
            consumed = False
            for f in hit_fields:
                r = subprocess_count(f)
                if r > 1:
                    consumed = True
            cats["乙_字典值被消费" if consumed else "甲_字典值无消费"].append(i)
        elif "GET_DEFAULT" in ks:
            cats["丙_静默容错(.get默认)"].append(i)
        else:
            cats["甲_字符串字面量"].append(i)

    total = len(hits)
    print("    %-22s %4d 条" % ("甲 纯元数据(影响面0)", len(cats["甲_纯注释"]
                                    + cats["甲_字符串字面量"] + cats["甲_字典值无消费"])))
    print("    %-22s %4d 条" % ("乙 被消费(真断链)", len(cats["乙_字典值被消费"])))
    print("    %-22s %4d 条" % ("丙 静默容错(.get)", len(cats["丙_静默容错(.get默认)"])))
    print("    合计 %d" % total)

    for k in ["乙_字典值被消费", "丙_静默容错(.get默认)"]:
        print("\n  ★ %s —— 前 8 条样例:" % k)
        for x in cats[k][:8]:
            loc = hits[x][0]
            print("      %-16s %s:L%d  %s"
                  % (x, loc[0].split("/")[-1][:22], loc[1], loc[2].strip()[:52]))

    # ── 反向: 引擎是否需要按切片ID寻址 ──
    print("\n" + "=" * 100)
    print("【反向核】引擎是否需要按切片ID 寻址切片内容")
    print("=" * 100)
    LOOKUP = re.compile(r"(read_slice|load_slices|slice_authority|read_slice_full)\s*\(")
    n_lookup = 0
    for base in ["engines", "p0_v2", "spec"]:
        bp = os.path.join(ROOT, base)
        for dp, dn, fn in os.walk(bp):
            dn[:] = [d for d in dn if d not in SKIP]
            for f in fn:
                if not f.endswith(".py"):
                    continue
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                for i, l in enumerate(io.open(p, encoding="utf-8-sig",
                                              errors="ignore").read().split("\n"), 1):
                    if LOOKUP.search(l) and not l.strip().startswith("#"):
                        n_lookup += 1
                        if n_lookup <= 12:
                            print("   %-44s L%-5d %s" % (rel[:42], i, l.strip()[:62]))
    print("\n   切片寻址调用点 = %d 处" % n_lookup)
    print("   → 有调用点 = 引擎设计上需要寻址 → 反向成立")
    print("   → 无调用点 = 仅作标记 → 反向不成立")


def subprocess_count(field):
    """某字段名在全仓 .py 里的出现次数(粗略)"""
    n = 0
    for base in ["engines", "p0_v2"]:
        bp = os.path.join(ROOT, base)
        for dp, dn, fn in os.walk(bp):
            dn[:] = [d for d in dn if d not in SKIP]
            for f in fn:
                if not f.endswith(".py"):
                    continue
                try:
                    s = io.open(os.path.join(dp, f), encoding="utf-8-sig",
                                errors="ignore").read()
                except Exception:
                    continue
                n += len(re.findall(r"['\"]%s['\"]" % re.escape(field), s))
    return n


if __name__ == "__main__":
    main()