# -*- coding: utf-8 -*-
"""裁补1: 扫跨文件「被填充但从不被消费」的同类字段

★ 判据(裁八十三甲确立): 【出现次数 ≠ 消费】
  被写入 ≠ 被消费。只有值流向【计算 / 比较 / 索引 / 寻址】才算消费。

核法(数据流, 非出现次数):
  1 写入点: `key: value` 或 `key = value` 里 key 命中目标字段名
  2 读取点: `.get(key)` / `[key]` / `key in x` / getattr 等【读该 key】的表达式
  3 判定:
     无写入 / 无读取        → 未用
     有写入 / 无读取        → ★仅标记(与 evidence_refs 同款)
     有写入 / 有读取        → 需再核读取处是否流向计算
"""
import io
import os
import re
import collections

ROOT = r"D:/shuntian-ziping-p0"
SCAN = ["engines", "p0_v2", "spec", "scripts", "tests"]
SKIP = {"__pycache__", ".git", "node_modules"}

# 候选「标记型」字段名(按你的 grep 清单 + 同类)
CAND = re.compile(r"\b([a-z][a-z0-9_]{2,24})\b")
KEYWORD = re.compile(r"(refs?|sources?|notes?|tags?|labels?|evidence|classic|"
                     r"trace|chain|quote|quotation|citation|cite|origin|provenance|"
                     r"authority|canonical|upstream|basis)")
# 计算型下游函数(读取点若流向这些, 算真消费)
COMPUTE = re.compile(
    r"(read_slice|load_slices|slice_authority|read_slice_full|_parse_slice|"
    r"\bif\b|\bassert\b|==|!=|in\s|\bfor\b|\bwhile\b|append\(|sort\(|sorted\(|"
    r"\.count\(|\bmax\(|\bmin\(|\bsum\(|len\()")


def load():
    files = []
    for base in SCAN:
        bp = os.path.join(ROOT, base)
        if not os.path.isdir(bp):
            continue
        for dp, dn, fn in os.walk(bp):
            dn[:] = [d for d in dn if d not in SKIP]
            for f in fn:
                if f.endswith(".py"):
                    p = os.path.join(dp, f)
                    files.append((os.path.relpath(p, ROOT).replace("\\", "/"),
                                  io.open(p, encoding="utf-8-sig",
                                          errors="ignore").read().split("\n")))
    return files


def main():
    files = load()
    print("=" * 100)
    print("裁补1  跨文件「被填充但从不被消费」同类字段扫描")
    print("=" * 100)
    print("扫描 %d 个 .py   判据: 出现次数 ≠ 消费, 只认【值流向计算/比较/索引/寻址】" % len(files))

    writes = collections.defaultdict(list)   # key -> [(file, line)]
    reads = collections.defaultdict(list)
    read_ctx = collections.defaultdict(list)

    for rel, lines in files:
        for i, l in enumerate(lines, 1):
            s = l.strip()
            if s.startswith("#"):
                continue
            # 写入: 'key': ...  或  key = ...  或  key.append(
            for m in re.finditer(r"['\"]([a-z][a-z0-9_]{2,24})['\"]\s*:", l):
                writes[m.group(1)].append((rel, i))
            for m in re.finditer(r"\b([a-z][a-z0-9_]{2,24})\s*=(?!=)", l):
                writes[m.group(1)].append((rel, i))
            # 读取: .get('key') / ['key'] / 'key' in x
            for m in re.finditer(r"\.get\(\s*['\"]([a-z][a-z0-9_]{2,24})['\"]", l):
                reads[m.group(1)].append((rel, i))
                read_ctx[m.group(1)].append(l)
            for m in re.finditer(r"\[\s*['\"]([a-z][a-z0-9_]{2,24})['\"]\s*\]", l):
                reads[m.group(1)].append((rel, i))
                read_ctx[m.group(1)].append(l)
            for m in re.finditer(r"['\"]([a-z][a-z0-9_]{2,24})['\"]\s+in\s", l):
                reads[m.group(1)].append((rel, i))
                read_ctx[m.group(1)].append(l)
            for m in re.finditer(r"hasattr\(\s*[^,]+,\s*['\"]([a-z][a-z0-9_]{2,24})['\"]", l):
                reads[m.group(1)].append((rel, i))

    rows = []
    for key in sorted(set(list(writes.keys()) + list(reads.keys()))):
        if not KEYWORD.search(key):
            continue
        nw = len(set(writes.get(key, [])))
        nr = len(set(reads.get(key, [])))
        if nw == 0:
            verdict = "未用(只读不写)"
        elif nr == 0:
            verdict = "★仅标记(有写入无读取)"
        else:
            # 有读取 → 核读取处是否流向计算
            flows = sum(1 for c in read_ctx.get(key, []) if COMPUTE.search(c))
            verdict = "被消费(读取处流入计算 %d/%d)" % (flows, nr) if flows else "★读取但未流入计算"
        rows.append((key, nw, nr, verdict))

    rows.sort(key=lambda r: (-r[1], r[0]))
    print("\n%-26s %6s %6s  %s" % ("字段名", "写入", "读取", "判定"))
    print("-" * 100)
    only_mark = [r for r in rows if r[3].startswith("★")]
    for key, nw, nr, v in rows:
        flag = "  ★★" if v.startswith("★仅标记") else ""
        print("%-26s %6d %6d  %s%s" % (key, nw, nr, v, flag))

    print("\n" + "=" * 100)
    print("【与 evidence_refs 同款: 仅标记、从不消费】共 %d 个字段" % len(only_mark))
    print("=" * 100)
    for key, nw, nr, v in only_mark:
        loc = writes[key][0] if writes[key] else ("?", 0)
        print("   %-26s 写入 %d 处, 读取 0   例: %s:L%d"
              % (key, nw, loc[0].split("/")[-1][:24], loc[1]))

    print("\n  ★ 这类字段的特征: 写入即终点 —— 值存进 dict 后再没人取过。")
    print("    与 evidence_refs(176 条虚 ID)同款, 也与 kernel 污染/键名 grep 同款:")
    print("    「看起来有结构」不等于「结构被用」。")


if __name__ == "__main__":
    main()