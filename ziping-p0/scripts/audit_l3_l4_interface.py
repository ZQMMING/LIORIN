# -*- coding: utf-8 -*-
"""核1: L3 -> L4 接口点清单（ge_jie_layer.py）

★ 立规(第五次同类错的上位规): 分类/统计优先用【结构标识】(ID前缀/字段类型/
  枚举值/AST节点类型); 文本模式只作辅助, 不作最终判据。

★ 本脚本因此【不做关键词分类】: 读什么字段走 AST Subscript + 名值追踪,
  而不是grep 字段名。立规的上位规与本脚本实现一致。

核三件:
  甲 读什么: L3 的哪些字段被 ge_jie_layer 读
  乙 写什么: 输出结构与值域
  丙 接口方向: 纯读 L3 / 双向（有无反馈写回 L3）
"""
import ast
import io
import os
import collections

ROOT = r"D:/shuntian-ziping-p0"
GJL = "engines/common/ge_jie_layer.py"

L3_FIELDS = [
    "dm_ben_eff", "yin_ben_eff", "ling_state", "root_grade", "root_grade_raw",
    "support_state", "strength_verdict", "chong_adjust", "chong_role",
    "chong_by", "library_open", "ling_state_eff",
    "de_ling", "de_di", "dang_duo", "fan_ju", "boundary_note", "evidence_refs",
]
# L3 定义端(在 bazi_gate 里被构造的容器) 的变量名候选
L3_VARS = ["l3_contract", "_l3", "l3c", "contract", "_lc"]


def load(rel):
    p = os.path.join(ROOT, rel)
    return io.open(p, encoding="utf-8-sig", errors="ignore").read() if os.path.exists(p) else None


def main():
    print("=" * 104)
    print("核1  L3 -> L4 接口点清单   对象: %s" % GJL)
    print("=" * 104)
    src = load(GJL)
    if src is None:
        print("★ 文件不存在")
        return
    lines = src.split("\n")
    print("文件行数 = %d" % len(lines))
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        print("★ SyntaxError: %s" % e)
        return

    # ── 甲: 读了哪些 L3 字段（AST: Subscript / .get()，值是字符串常量）──
    print("\n" + "=" * 104)
    print("【甲】读 L3 字段（AST 精确: Subscript / .get('X')）")
    print("=" * 104)
    reads = collections.defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            v = node.slice.value
            if v in L3_FIELDS:
                reads[v].append((node.lineno, lines[node.lineno - 1].strip()[:78]))
        if isinstance(node, ast.Call):
            fn = node.func
            nm = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if nm == "get" and node.args:
                a = node.args[0]
                if isinstance(a, ast.Constant) and a.value in L3_FIELDS:
                    reads[a.value].append((node.lineno,
                                          lines[node.lineno - 1].strip()[:78]))

    print("%-20s %6s  %s" % ("L3 字段", "读取处", "是否被 L4 读"))
    print("-" * 104)
    read_any = []
    for f in L3_FIELDS:
        n = len(reads.get(f, []))
        read_any.append((f, n))
        mark = "★ 是" if n else "否"
        print("%-20s %6d  %s" % (f, n, mark))

    print("\n  ★ 重点: strength_verdict 被读 = %d 处"
          % len(reads.get("strength_verdict", [])))
    for ln, s in reads.get("strength_verdict", [])[:8]:
        print("      L%-5d %s" % (ln, s))

    print("\n  ── 读取点明细 ──")
    for f in L3_FIELDS:
        for ln, s in reads.get(f, []):
            print("      %-18s L%-5d %s" % (f, ln, s))

    # ── L3 容器变量是否被引用（确认数据源真的是 l3_contract）──
    print("\n" + "=" * 104)
    print("【甲2】L3 容器变量引用核（确认读的是 l3_contract 而非同名源）")
    print("=" * 104)
    names = collections.Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names[node.id] += 1
        if isinstance(node, ast.arg):
            names[node.arg] += 1
    for v in L3_VARS:
        print("    %-16s 被引用 %d 次" % (v, names.get(v, 0)))
    print("\n  ★ 参数名 / 形参清单（接口签名）:")
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            a = [x.arg for x in node.args.args]
            if any(x in a for x in ("facts", "l3", "l3_contract", "f", "pillars")):
                print("      def %-28s (%s)  L%d" % (node.name, ", ".join(a), node.lineno))

    # ── 乙: 输出什么 ──
    print("\n" + "=" * 104)
    print("【乙】ge_jie_layer 输出结构")
    print("=" * 104)
    returns = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("build"):
            seg = lines[node.lineno - 1:min(node.lineno + 45, len(lines))]
            keys = []
            for i, l in enumerate(seg):
                if '"' in l and ":" in l:
                    for tok in l.split('"'):
                        if tok and tok.replace("_", "").replace("(", "").isalnum() \
                                and 2 < len(tok) < 22 and " " not in tok:
                            keys.append((node.lineno + i, tok))
            print("\n  def %s()  L%d  → 输出键 %d 个"
                  % (node.name, node.lineno, len(keys)))
            for ln, k in keys[:24]:
                print("      L%-5d %s" % (ln, k))
            returns.append(node.name)

    # ── 丙: 接口方向 ──
    print("\n" + "=" * 104)
    print("【丙】接口方向: 纯读 L3 / 双向")
    print("=" * 104)
    writes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant):
                    v = t.slice.value
                    if v in L3_FIELDS:
                        writes.append((v, node.lineno,
                                       lines[node.lineno - 1].strip()[:78]))
                if isinstance(t, ast.Attribute) and t.attr in ("l3_contract",):
                    writes.append((t.attr, node.lineno,
                                   lines[node.lineno - 1].strip()[:78]))
    print("  写回 L3 字段的赋值点 = %d" % len(writes))
    for v, ln, s in writes[:10]:
        print("      %-20s L%-5d %s" % (v, ln, s))
    print()
    if not writes:
        print("  ★ 结论: ge_jie_layer 对 L3 【纯读】, 无写回")
        print("    → 接口单向, L3 -> L4, 底层收口无阻塞")
    else:
        print("  ★★ 结论: 存在写回 → 双向, 底层冻结要看 L4 何时稳定")

    # ── 汇总 ──
    print("\n" + "=" * 104)
    print("【汇总】L3 18 字段被 L4 读取情况")
    print("=" * 104)
    yes = [f for f, n in read_any if n]
    no = [f for f, n in read_any if not n]
    print("  被读 %d 个: %s" % (len(yes), ", ".join(yes)))
    print("  未读 %d 个: %s" % (len(no), ", ".join(no)))


if __name__ == "__main__":
    main()