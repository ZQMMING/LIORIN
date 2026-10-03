# -*- coding: utf-8 -*-
"""同名字段双源专核 (裁五十三甲)

★ 问题: l3_contract 的键与 wuxing_power[五行] 行的键【同名】,
  「按键名 grep 统计消费者」无法区分读的是哪个源。
  本脚本按【变量来源】追踪, 产出两份真实消费者清单。

判据规则(用户裁定 §三):
  facts['l3_contract']['X'] / l3c.get('X') / lc.get('X')  → l3_contract 消费
  wp.get('X') / _dmp.get('X') / _dmp_month.get('X') / d(w).get('X')
  / (wp.get(...) or {}).get('X')                             → wuxing_power 消费

变量来源判定: 读键那行所在的表达式里, 接收者变量的定义链。
本脚本做「机械可判」的部分: 识别接收者变量名 + 该变量在同文件内的赋值语句;
来源不明的标 UNRESOLVED 交人工。
"""
import io
import os
import re
import collections

ROOT = r"D:/shuntian-ziping-p0"
SKIP = {"__pycache__", ".git", "node_modules"}

# l3_contract 实际 18 键(实测, 契约 §4.14)
L3_KEYS = [
    "ling_state", "root_grade", "root_grade_raw", "support_state",
    "strength_verdict", "dm_ben_eff", "yin_ben_eff",
    "chong_adjust", "chong_role", "chong_by", "library_open", "ling_state_eff",
    "de_ling", "de_di", "dang_duo", "fan_ju",
]
# wuxing_power[五行] 行的键(实测 transit_power.py L258-L284)
WP_KEYS = [
    "ling_state", "ben_n", "zhong_n", "yu_n", "ju_n", "banhe_n",
    "stem_n", "root_detail", "chong_adjust", "chong_role", "chong_by",
    "library_open", "chong_note", "ling_state_eff",
]
# 同名键(双源)
SAME = [k for k in L3_KEYS if k in WP_KEYS]

LAYERS = [
    ("生产层", ["engines", "p0_v2", "spec"]),
    ("验收层", ["scripts", "tests"]),
]

# 接收者变量 → 数据源标记
L3_VARS = ["l3c", "lc", "l3", "_l3", "l3contract", "_l3c", "l3_contract"]
WP_VARS = ["_dmp", "_dmp_month", "_wp", "_wpd", "wp", "wpd", "_wpd2",
           "row", "_row", "dmp", "_wp_row", "_wu", "wu"]

RX_READ = re.compile(r"([A-Za-z_][\w\.]*)\s*(?:\)?\s*\.\s*(?:get|setdefault)\s*\(\s*"
                     r"['\"]([A-Za-z_]\w*)['\"]|"
                     r"\[\s*['\"]([A-Za-z_]\w*)['\"]\s*\])")


def load():
    out = {}
    for layer, roots in LAYERS:
        files = []
        seen = set()
        for root in roots:
            base = os.path.join(ROOT, root)
            if os.path.isfile(base) and base.endswith(".py"):
                cand = [base]
            elif os.path.isdir(base):
                cand = []
                for dp, dn, fn in os.walk(base):
                    dn[:] = [d for d in dn if d not in SKIP]
                    for f in fn:
                        if f.endswith(".py"):
                            cand.append(os.path.join(dp, f))
            else:
                continue
            for p in cand:
                rk = os.path.normcase(os.path.abspath(p))
                if rk in seen:
                    continue
                seen.add(rk)
                try:
                    lines = io.open(p, encoding="utf-8-sig",
                                    errors="ignore").read().split("\n")
                except Exception:
                    continue
                files.append((os.path.relpath(p, ROOT).replace("\\", "/"), lines))
        out[layer] = files
    return out


def classify(recv, key, file_lines, lineno):
    """判定一个读取点的数据源"""
    base = recv.split(".")[0] if "." in recv else recv
    # 直接字面量来源
    m = re.search(r"['\"]l3_contract['\"]", recv)
    if m:
        return "L3_CONTRACT"
    # 变量名直接命中
    if base in L3_VARS:
        return "L3_CONTRACT"
    if base in WP_VARS:
        return "WUXING_POWER"
    # 回溯: 该变量在本文件内的赋值
    for k in range(lineno - 2, -1, -1):
        s = file_lines[k].strip()
        if not s:
            continue
        m = re.match(r"(?:const\s+)?([A-Za-z_]\w*)\s*=\s*(.+)", s)
        if not m:
            if re.match(r"(?:def|class|for|if|while)\b", s):
                break
            continue
        var, rhs = m.group(1), m.group(2)
        if var != base:
            continue
        if "l3_contract" in rhs:
            return "L3_CONTRACT"
        if "wuxing_power" in rhs:
            return "WUXING_POWER"
        if "daymaster_power" in rhs:
            return "DAYMASTER_POWER"
        return "UNRESOLVED(%s)" % rhs.strip()[:40]
    return "UNRESOLVED"


def main():
    print("=" * 96)
    print("同名字段双源专核 (裁五十三甲)  —— 按变量来源追踪, 非按键名 grep")
    print("=" * 96)
    layers = load()
    for k, v in layers.items():
        print("  扫描 %s: %d 个 .py" % (k, len(v)))

    print("\n【同名键清单】(l3_contract ∩ wuxing_power[五行]行)")
    print("   " + ", ".join(SAME))
    print("   共 %d 个" % len(SAME))

    hits = []
    for layer, files in layers.items():
        for rel, lines in files:
            for i, txt in enumerate(lines, 1):
                s = txt.strip()
                if not s or s.startswith("#") or s.startswith('"'):
                    continue
                for m in RX_READ.finditer(txt):
                    recv = m.group(1)
                    key = m.group(2) or m.group(3)
                    if key not in SAME and key not in L3_KEYS:
                        continue
                    src = classify(recv, key, lines, i)
                    hits.append((layer, rel, i, recv, key, src, s))

    c = collections.Counter((h[0], h[5]) for h in hits)
    print("\n【同名键读取点 · 按数据源分类】")
    for (layer, src), n in sorted(c.items()):
        print("   %-6s %-28s %4d" % (layer, src, n))

    for tag, want in [("L3_CONTRACT", "l3_contract 真实消费者"),
                      ("WUXING_POWER", "wuxing_power 真实消费者")]:
        print("\n" + "=" * 96)
        print("【%s】" % want)
        print("=" * 96)
        bykey = collections.defaultdict(list)
        for layer, rel, i, recv, key, src, s in hits:
            if src != tag:
                continue
            bykey[key].append("%s:%d" % (rel, i))
        for key in sorted(bykey):
            locs = bykey[key]
            prod = [x for x in locs
                    if x.split(":")[0] in ("engines", "p0_v2", "spec")]
            print("   %-18s 共 %-3d 处 (生产 %d / 验收 %d)"
                  % (key, len(locs), len(prod), len(locs) - len(prod)))
            for x in locs[:6]:
                print("        %s" % x)
            if len(locs) > 6:
                print("        …另 %d 处" % (len(locs) - 6))

    unres = [h for h in hits if h[5].startswith("UNRESOLVED")]
    print("\n【需人工判定】UNRESOLVED %d 处（同名前 %d 处）"
          % (len(unres), sum(1 for h in unres if h[4] in SAME)))
    seen = set()
    for layer, rel, i, recv, key, src, s in unres:
        sig = (rel, recv, key)
        if sig in seen:
            continue
        seen.add(sig)
        print("   %-38s L%-5d %-28s %s" % (rel, i, recv + ".get(" + key + ")", src[11:]))


if __name__ == "__main__":
    main()