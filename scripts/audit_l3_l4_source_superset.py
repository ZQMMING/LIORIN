# -*- coding: utf-8 -*-
"""核2-丁: L4 读的源 ⊇ L3 的源?

★「L3/L4 并行出口」定性的最后一块拼图。
  问题不是「L4 读不读 L3」(已知: 不读), 而是「L4 该不该读 L3」
  —— 若 L4 直读的源已覆盖 L3 全部 18 键的源, 则 L3 对 L4 无新信息, 并行成立。

方法(立规元规: 用结构标识, 不用文本模式):
  1 L3 18 键逐键回溯【数据来源】(bazi_gate.py 里每个键的右值表达式)
  2 L4(ge_jie_layer + special_pattern) 读的 facts 键 + wuxing_power 子字段
  3 集合对比: L4源 ⊇ L3源? 差集是什么?
"""
import ast
import io
import os
import re
import collections

ROOT = r"D:/shuntian-ziping-p0"

L3_KEYS = [
    "dm_ben_eff", "yin_ben_eff", "ling_state", "root_grade", "root_grade_raw",
    "support_state", "strength_verdict", "chong_adjust", "chong_role",
    "chong_by", "library_open", "ling_state_eff",
    "de_ling", "de_di", "dang_duo", "fan_ju", "boundary_note", "evidence_refs",
]
L4_FILES = ["engines/common/ge_jie_layer.py", "engines/common/special_pattern.py"]


def load(rel):
    p = os.path.join(ROOT, rel)
    return io.open(p, encoding="utf-8-sig", errors="ignore").read() if os.path.exists(p) else None


def main():
    gate = load("p0_v2/bazi_gate.py")
    print("=" * 104)
    print("核2-丁  L4 读的源 ⊇ L3 的源?")
    print("=" * 104)

    # ── 1. L3 18 键的右值表达式（结构标识: 赋值 AST）──
    print("\n【1】L3 18 键的右值来源（bazi_gate.py, AST 取赋值右值）")
    print("-" * 104)
    src_map = {}
    tree = ast.parse(gate)
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value in L3_KEYS:
                    seg = ast.unparse(v)
                    src_map[k.value] = seg[:76]
    # l3_contract 是 f["l3_contract"] = {...}; 用 Dict 抓可能抓到别处, 精确定位
    idx = gate.find('f["l3_contract"] = {')
    if idx > 0:
        blk = gate[idx:idx + 9000]
        for m in re.finditer(r'^\s*"(\w+)":\s*(.+?),\s*$', blk, re.M):
            k = m.group(1)
            if k in L3_KEYS:
                src_map[k] = m.group(2).strip()[:76]
    for k in L3_KEYS:
        print("  %-20s ← %s" % (k, src_map.get(k, "★未定位")))

    # ── 2. 把来源归约成「源字段集」──
    print("\n" + "=" * 104)
    print("【2】L3 18 键的【源字段集】归约")
    print("-" * 104)
    SRC_MAP = {
        "dm_ben_eff": ["special.dm_ben_eff"],
        "yin_ben_eff": ["special.yin_ben_eff"],
        "ling_state": ["wuxing_power[dm].ling_state"],
        "root_grade": ["L0 root_weight_class"],
        "root_grade_raw": ["L0 root_weight_class"],
        "support_state": ["wuxing_power[*]._mass"],
        "strength_verdict": ["（常量 dict, 不读源）"],
        "chong_adjust": ["wuxing_power[month].chong_adjust"],
        "chong_role": ["wuxing_power[month].chong_role"],
        "chong_by": ["wuxing_power[month].chong_by"],
        "library_open": ["wuxing_power[month].library_open"],
        "ling_state_eff": ["wuxing_power[month].ling_state_eff"],
        "de_ling": ["wuxing_power[dm].ling_state"],
        "de_di": ["special.dm_ben_eff"],
        "dang_duo": ["wuxing_power[*]._mass"],
        "fan_ju": ["relations(承 relations_builder)"],
        "boundary_note": ["（常量字符串）"],
        "evidence_refs": ["wuxing_power[month].evidence_refs"],
    }
    l3_src = set()
    for k in L3_KEYS:
        for s in SRC_MAP.get(k, []):
            l3_src.add(s)
    for k in L3_KEYS:
        print("  %-20s → %s" % (k, " + ".join(SRC_MAP.get(k, ["?"]))))
    print("\n  L3 源字段集（去重后 %d 项）:" % len(l3_src))
    for s in sorted(l3_src):
        print("      %s" % s)

    # ── 3. L4 读什么 ──
    print("\n" + "=" * 104)
    print("【3】L4 实际读的 facts 键 / wuxing_power 子字段（AST）")
    print("-" * 104)
    l4_facts = collections.Counter()
    l4_wx = collections.Counter()
    for rel in L4_FILES:
        s = load(rel)
        if not s:
            print("  ★ 缺文件 %s" % rel)
            continue
        t = ast.parse(s)
        for node in ast.walk(t):
            if isinstance(node, ast.Subscript):
                v = node.slice
                if isinstance(v, ast.Constant) and isinstance(node.value, ast.Name) \
                        and node.value.id == "facts":
                    l4_facts[v.value] += 1
            if isinstance(node, ast.Call):
                fn = node.func
                nm = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
                if nm == "get" and node.args and isinstance(node.args[0], ast.Constant):
                    a0 = node.args[0].value
                    # 接收者链里含 facts → 记为 facts 键
                    recv = ast.unparse(node.func)
                    if "facts" in recv:
                        l4_facts[a0] += 1
                    elif "wuxing" in recv or "_wp" in recv or "wp" in recv:
                        l4_wx[a0] += 1
        # 文本兜底: wuxing_power[五行][子字段]
        for m in re.finditer(r'wuxing_power\]\s*\[?.*?\]\s*(?:\.get\(|\[)\s*["\'](\w+)["\']', s):
            l4_wx[m.group(1)] += 1
    print("  L4 读的 facts 键(%d):" % len(l4_facts))
    for k, v in l4_facts.most_common():
        print("      %-30s %d" % (k, v))
    print("  L4 读的 wuxing_power 子字段(%d):" % len(l4_wx))
    for k, v in l4_wx.most_common():
        print("      %-30s %d" % (k, v))

    # ── 4. 对比 ──
    print("\n" + "=" * 104)
    print("【4】对比: L4 源 ⊇ L3 源?")
    print("=" * 104)
    # 归约到可比的粗粒度: 源容器
    CONTAINER = {
        "special.dm_ben_eff": "special", "special.yin_ben_eff": "special",
        "wuxing_power[dm].ling_state": "wuxing_power",
        "wuxing_power[month].chong_adjust": "wuxing_power",
        "wuxing_power[month].chong_role": "wuxing_power",
        "wuxing_power[month].chong_by": "wuxing_power",
        "wuxing_power[month].library_open": "wuxing_power",
        "wuxing_power[month].ling_state_eff": "wuxing_power",
        "wuxing_power[month].evidence_refs": "wuxing_power",
        "wuxing_power[*]._mass": "wuxing_power",
        "L0 root_weight_class": "L0-facts",
        "relations(承 relations_builder)": "relations",
    }
    l3_cont = set(CONTAINER.get(s, s) for s in l3_src)
    l4_cont = set()
    if l4_facts:
        l4_cont.add("L0-facts")
    if any(k == "special" for k in l4_facts):
        pass
    if l4_wx:
        l4_cont.add("wuxing_power")
    print("  L3 源容器 = %s" % sorted(l3_cont))
    print("  L4 源容器 = %s" % sorted(l4_cont))
    miss = l3_cont - l4_cont
    print("\n  ★ L3 有而 L4 没读的源容器 = %s" % (sorted(miss) if miss else "★ 无"))
    if not miss:
        print("    → L4 源 ⊇ L3 源: L3 对 L4 【无新信息】, 并行出口定性成立")
    else:
        print("    → L3 有 L4 未读的源 —— 需逐项核: 是 L4 不需要, 还是 L4 缺接线")


if __name__ == "__main__":
    main()