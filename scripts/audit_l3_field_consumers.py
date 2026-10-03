# -*- coding: utf-8 -*-
"""L3 全 18 键「生产层 vs 验收层」消费统计 (裁五十二补)

★ 纯 Python 扫描, 不调外部 grep。
  理由(实测踩坑两次): MSYS grep 的 -E 对 ["\\'] 字符类处理与 bash 直跑不一致,
  subprocess 传参时引号被吃掉 -> 正则失配 -> 全表静默报「消费 0」假象。
  「结论是 0」这种审计必须自包含, 不能依赖外部工具的引号语义。

两种消费形态都核:
  显式  .get("key")  /  ["key"]
  间接  整块 dict 遍历 items()/values()/keys() / **整块展开 / 整块传参

层次划分:
  生产层 engines/ + p0_v2/ + spec/   判定链路的真实消费方
  验收层 scripts/ + tests/           审计/回归脚本
构造层 p0_v2/bazi_gate.py 的 f["l3_contract"] = {...} 不算消费。
"""
import io
import os
import re
import collections

ROOT = r"D:/shuntian-ziping-p0"

L3_KEYS = [
    "ling_state", "root_grade", "root_grade_raw", "support_state",
    "strength_verdict",
    "dm_ben_eff", "yin_ben_eff",
    "chong_adjust", "chong_role", "chong_by", "library_open", "ling_state_eff",
    "de_ling", "de_di", "dang_duo",
    "fan_ju", "boundary_note", "evidence_refs",
]

LAYERS = [
    ("生产层", ["engines", "p0_v2", "spec"]),
    ("验收层", ["scripts", "tests"]),
]

CONSTRUCT_FILE = "p0_v2/bazi_gate.py"
SKIP_DIR = {"__pycache__", ".git", "node_modules"}

# 间接消费形态(对 l3_contract 整块)
INDIRECT = [
    ("整块遍历 .items()/.values()/.keys()",
     re.compile(r"l3_contract\s*\)?\s*\.\s*(items|values|keys)\s*\(")),
    ("for k,v in l3_contract",
     re.compile(r"for\s+\w+\s*,\s*\w+\s+in\s+[\w\.]*l3_contract")),
    ("**l3_contract 整块展开",
     re.compile(r"\*\*\s*[\w\.]*l3_contract")),
    ("整块作函数入参",
     re.compile(r"def\s+\w+\s*\([^)]*l3_contract")),
]


def iter_py(layer_roots):
    for root in layer_roots:
        base = os.path.join(ROOT, root)
        if os.path.isfile(base) and base.endswith(".py"):
            yield base
            continue
        if not os.path.isdir(base):
            continue
        for dp, dn, fn in os.walk(base):
            dn[:] = [d for d in dn if d not in SKIP_DIR]
            for f in fn:
                if f.endswith(".py"):
                    yield os.path.join(dp, f)


def load_files(layer_roots):
    """读入 [(relpath, [line...])]"""
    out = []
    seen = set()
    for path in iter_py(layer_roots):
        real = os.path.normcase(os.path.abspath(path))
        if real in seen:
            continue
        seen.add(real)
        try:
            with io.open(path, encoding="utf-8-sig", errors="ignore") as fh:
                lines = fh.read().split("\n")
        except Exception:
            continue
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        out.append((rel, lines))
    return out


def main():
    print("=" * 96)
    print("L3 全 18 键 消费统计 (裁五十二补)  —— 生产层 vs 验收层")
    print("=" * 96)

    layer_files = {name: load_files(roots) for name, roots in LAYERS}
    for name, files in layer_files.items():
        print("  扫描 %s: %d 个 .py" % (name, len(files)))

    # ---------- 前置: 自检 ----------
    print("\n【前置1】自检 —— 已知应命中的探针(验收层读 ling_state)")
    probe_hits = 0
    for rel, lines in layer_files["验收层"]:
        for ln, txt in enumerate(lines, 1):
            if "ling_state" in txt and ".get(" in txt:
                probe_hits += 1
                if probe_hits <= 3:
                    print("   探针命中 %s:%d  %s" % (rel, ln, txt.strip()[:70]))
    print("   探针共命中 %d 处 —— %s"
          % (probe_hits, "扫描器工作正常" if probe_hits else "★ 扫描器失效, 结果不可信"))

    # ---------- 间接消费 ----------
    print("\n【前置2】间接消费形态（整块 dict）")
    ind = collections.Counter()
    ind_ex = {}
    for layer, files in layer_files.items():
        for rel, lines in files:
            for ln, txt in enumerate(lines, 1):
                s = txt.strip()
                if s.startswith("#"):
                    continue
                for label, rx in INDIRECT:
                    if rx.search(txt):
                        if rel == CONSTRUCT_FILE and ("=" in s):
                            continue        # 构造赋值不算消费
                        ind[(label, layer)] += 1
                        ind_ex.setdefault((label, layer), "%s:%d" % (rel, ln))
    if ind:
        for (label, layer), n in sorted(ind.items()):
            print("   %-34s [%-6s] %3d 处   例: %s"
                  % (label, layer, n, ind_ex[(label, layer)]))
    else:
        print("   (零命中 —— 无任何间接消费形态)")

    # ---------- 逐键显式消费 ----------
    print("\n" + "=" * 96)
    print("逐键显式消费数（ .get(\"key\")  /  [\"key\"] ）")
    print("=" * 96)
    print("%-20s %-8s %-8s %s" % ("键", "生产层", "验收层", "定性"))
    rows = []
    for key in L3_KEYS:
        prod, ver = [], []
        for layer, files in layer_files.items():
            for rel, lines in files:
                for ln, txt in enumerate(lines, 1):
                    s = txt.strip()
                    if s.startswith("#"):
                        continue
                    if ('"%s"' % key) not in txt and ("'%s'" % key) not in txt:
                        continue
                    # 排除构造: bazi_gate 里 "key": 形式
                    if rel == CONSTRUCT_FILE and ('"%s":' % key) in txt:
                        continue
                    (prod if layer == "生产层" else ver).append((rel, ln))
        np_, nv = len(prod), len(ver)
        if np_ == 0 and nv == 0:
            v = "★ 生产0 / 验收也0"
        elif np_ == 0:
            v = "★ 生产0 / 验收有"
        else:
            v = "已接生产"
        rows.append((key, np_, nv, v, prod, ver))

    for key, np_, nv, v, _, _ in rows:
        print("%-20s %-8d %-8d %s" % (key, np_, nv, v))

    zero = [r for r in rows if r[1] == 0]
    zero_both = [r for r in zero if r[2] == 0]
    print("\n【生产层 0 消费：%d / %d 键】" % (len(zero), len(rows)))
    for key, np_, nv, v, prod, ver in zero:
        ex = ", ".join("%s:%s" % (f, l) for f, l in ver[:3]) or "—"
        print("   %-20s 验收 %-3d 处  %s" % (key, nv, ex))

    print("\n【结论】")
    print("   生产0 且 验收0 : %d 个  -> %s"
          % (len(zero_both), [r[0] for r in zero_both] or "无"))
    print("   生产0 但 验收有 : %d 个  -> %s"
          % (len(zero) - len(zero_both), [r[0] for r in zero if r[2] > 0] or "无"))


if __name__ == "__main__":
    main()