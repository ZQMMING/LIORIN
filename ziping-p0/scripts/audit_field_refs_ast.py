# -*- coding: utf-8 -*-
"""裁八十五丙(换AST) + 裁八十六丙: 精确核 evidence_refs 等 4 字段的读取点

★ 为什么用 AST 而不是正则(裁八十五):
  正则 `key =` 会把局部变量/形参/推导式变量/self 属性全算成「字典字段写入」。
  三次同类错的共享根: 用文本模式判断语义/数据流。
  ast 能区分 Subscript(真字典字段) vs Name(局部变量) vs Attribute(self.x)。

★ 裁八十六: evidence_refs 的读取点分三类
  甲类 验收脚本(scripts/, tests/)读 → 不算生产消费
  乙类 生产代码读, 读后只写日志/元数据 → 弱消费
  丙类 生产代码读, 读后寻址/比较/索引 → 真消费
"""
import ast
import io
import os
import collections

ROOT = r"D:/shuntian-ziping-p0"
TARGETS = ["evidence_refs", "pair_map_evidence", "classic_source",
            "classic_line", "evidence_chain", "chain"]
SKIP = {"__pycache__", ".git", "node_modules"}


def classify_path(rel):
    if rel.startswith("scripts/") or rel.startswith("tests/"):
        return "甲_验收脚本"
    if "audit" in rel or "verify" in rel or "check" in rel:
        return "甲_验收脚本"
    return "丙_生产代码"


def scan():
    writes = collections.defaultdict(list)   # key -> [(rel, line, snippet)]
    reads = collections.defaultdict(list)
    for base in ["engines", "p0_v2", "spec", "scripts", "tests"]:
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
                src = io.open(p, encoding="utf-8-sig", errors="ignore").read()
                try:
                    tree = ast.parse(src)
                except SyntaxError:
                    continue
                lines = src.split("\n")
                for node in ast.walk(tree):
                    # 写入: dict['key'] = v  或  {'key': v}
                    if isinstance(node, ast.Assign):
                        for t in node.targets:
                            if (isinstance(t, ast.Subscript)
                                    and isinstance(t.slice, ast.Constant)
                                    and t.slice.value in TARGETS):
                                writes[t.slice.value].append(
                                    (rel, node.lineno,
                                     lines[node.lineno - 1].strip()[:70]))
                    if isinstance(node, ast.Dict):
                        for k in node.keys:
                            if isinstance(k, ast.Constant) and k.value in TARGETS:
                                writes[k.value].append(
                                    (rel, node.lineno,
                                     lines[node.lineno - 1].strip()[:70]))
                    # 读取: x['key']  或  x.get('key')
                    if isinstance(node, ast.Subscript):
                        s = node.slice
                        if isinstance(s, ast.Constant) and s.value in TARGETS:
                            reads[s.value].append(
                                (rel, node.lineno,
                                 lines[node.lineno - 1].strip()[:90]))
                    if isinstance(node, ast.Call):
                        fn = node.func
                        nm = (fn.attr if isinstance(fn, ast.Attribute)
                              else getattr(fn, "id", ""))
                        if nm == "get" and node.args:
                            a = node.args[0]
                            if isinstance(a, ast.Constant) and a.value in TARGETS:
                                reads[a.value].append(
                                    (rel, node.lineno,
                                     lines[node.lineno - 1].strip()[:90]))
    return writes, reads


def main():
    writes, reads = scan()
    print("=" * 100)
    print("裁八十五丙(AST) + 裁八十六丙  4+ 字段的写入/读取精确核")
    print("=" * 100)
    print("方法: ast 遍历, 只认 Subscript(真字典字段) 与 Dict 字面量 key")
    print("      排除 Name(局部变量) / 形参 / 推导式变量 —— 三次同类错的修法")
    print("探针自检: evidence_refs 必须既有写入又有读取(若为 0 说明 AST 没抓到)")

    for key in TARGETS:
        w = writes.get(key, [])
        r = reads.get(key, [])
        print("\n" + "-" * 100)
        print("【%s】写入 %d 处 / 读取 %d 处" % (key, len(w), len(r)))
        print("-" * 100)
        if not w and not r:
            print("   ★ AST 未抓到任何点 —— 该字段可能不存在于这批文件")
        cats = collections.Counter(classify_path(x[0]) for x in r)
        if r:
            print("   读取点分类: %s" % dict(cats))
        print("   ── 读取点明细 ──")
        for rel, ln, sn in r[:24]:
            print("      [%s] %-40s L%-5d %s"
                  % (classify_path(rel)[0], rel.split("/")[-1][:26], ln, sn))
        if len(r) > 24:
            print("      ... 共 %d 处" % len(r))
        if w:
            print("   ── 写入样例(3) ──")
            for rel, ln, sn in w[:3]:
                print("      %-40s L%-5d %s" % (rel.split("/")[-1][:26], ln, sn))

    print("\n" + "=" * 100)
    print("【裁八十六结论】evidence_refs 读取点是否落在生产代码")
    print("=" * 100)
    r = reads.get("evidence_refs", [])
    prod = [x for x in r if classify_path(x[0]) == "丙_生产代码"]
    scr = [x for x in r if classify_path(x[0]).startswith("甲")]
    print("   总读取 %d = 生产 %d + 验收 %d" % (len(r), len(prod), len(scr)))
    if not prod:
        print("   ★ 全为验收脚本读取 → 上轮「211 条从不消费」结论对生产层成立")
    else:
        print("   ★★ 有 %d 处在生产代码读取 → 上轮结论需更正, 逐条核:" % len(prod))
        for rel, ln, sn in prod[:12]:
            print("      %-44s L%-5d %s" % (rel[:42], ln, sn))


if __name__ == "__main__":
    main()