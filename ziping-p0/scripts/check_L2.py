# -*- coding: utf-8 -*-
"""L2 十神层核验

§2.4 契约:
  输出: ten_god(dg, stem) 函数 + ten_god_members 结构
  契约: 十神判定只此一处。ge_jie_layer._god_gans 是读取器, 不重算。

判据来源(不凭印象):
  十神规则 = 五行关系(同我/我生/我克/克我/生我) × 阴阳同异 -> 10 种
  通行对照:
    同我   同阴阳=比肩  异阴阳=劫财
    我生   同阴阳=食神  异阴阳=伤官
    我克   同阴阳=偏财  异阴阳=正财
    克我   同阴阳=七杀(偏官) 异阴阳=正官
    生我   同阴阳=偏印  异阴阳=正印

核:
  1 唯一性: 全仓 ten_god 定义点 + _god_gans 是否读取器
  2 判定: 10x10=100 组合全枚举, 每个实现 vs 通行规则
  3 结构: ten_god_members 与 L0 契约一致

用法:
  python scripts/check_L2.py            全量
  python scripts/check_L2.py --uniq     只查唯一性
"""
import sys, os, re, io, json, glob, collections, importlib

ROOT = r"D:/shuntian-ziping-p0"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

GAN = list("甲乙丙丁戊己庚辛壬癸")
WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
      '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
YANG = set('甲丙戊庚壬')
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}

# 通行十神对照(判据表)
REF = {}
for dg in GAN:
    for o in GAN:
        if dg == o:
            REF[(dg, o)] = '比肩'; continue
        d, ov = WX[dg], WX[o]
        same = (dg in YANG) == (o in YANG)
        if ov == d:
            REF[(dg, o)] = '比肩' if same else '劫财'
        elif SHENG[d] == ov:
            REF[(dg, o)] = '食神' if same else '伤官'
        elif KE[d] == ov:
            REF[(dg, o)] = '偏财' if same else '正财'
        elif KE[ov] == d:
            REF[(dg, o)] = '七杀' if same else '正官'
        elif SHENG[ov] == d:
            REF[(dg, o)] = '偏印' if same else '正印'
        else:
            REF[(dg, o)] = '?'


def check_uniq():
    print("=" * 88)
    print("[1] 唯一性核查  §2.4「十神判定只此一处」")
    print("=" * 88)
    defs = []
    for root, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs
                   if d not in (".git", "__pycache__", "_archive_20261003",
                                "六部经典MD文库", "vendor", "node_modules")]
        for f in fs:
            if not f.endswith(".py"):
                continue
            p = os.path.join(root, f)
            try:
                t = io.open(p, encoding="utf-8-sig", errors="ignore").read()
            except Exception:
                continue
            for i, l in enumerate(t.split("\n"), 1):
                if re.match(r"\s*def\s+ten_god\s*\(", l):
                    sig = l.strip()
                    defs.append((os.path.relpath(p, ROOT), i, sig))
    print("  引擎内 def ten_god: %d 处" % len(defs))
    for rel, ln, sig in defs:
        star = ""
        if "ge_jie_layer" in rel:
            star = "  ★ 违反 §2.4(契约禁止重算)"
        elif "execution_demo" in rel or "multifactor_eval" in rel:
            star = "  ★ 单参签名, 判定不可能正确"
        print("    %-40s L%-5d %s%s" % (rel, ln, sig[:58], star))

    print("\n  _god_gans 实现:")
    p = os.path.join(ROOT, "engines/common/ge_jie_layer.py")
    L = io.open(p, encoding="utf-8-sig").read().split("\n")
    for i, l in enumerate(L, 1):
        if l.startswith("    def _god_gans"):
            for j in range(i - 1, min(i + 9, len(L))):
                print("    L%-5d %s" % (j + 1, L[j].rstrip()[:104]))
            break
    return defs


_L2_PROBE = r"""
import sys, json
sys.path.insert(0, r"D:/shuntian-ziping-p0")
GAN = list("甲乙丙丁戊己庚辛壬癸")
WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土',
      '庚':'金','辛':'金','壬':'水','癸':'水'}
YANG = set('甲丙戊庚壬')
SHENG = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
KE = {'木':'土','火':'金','土':'水','金':'木','水':'火'}
REF = {}
for dg in GAN:
    for o in GAN:
        if dg == o: REF[(dg,o)]='比肩'; continue
        d, ov = WX[dg], WX[o]; same = (dg in YANG)==(o in YANG)
        if ov==d: REF[(dg,o)]='比肩' if same else '劫财'
        elif SHENG[d]==ov: REF[(dg,o)]='食神' if same else '伤官'
        elif KE[d]==ov: REF[(dg,o)]='偏财' if same else '正财'
        elif KE[ov]==d: REF[(dg,o)]='七杀' if same else '正官'
        elif SHENG[ov]==d: REF[(dg,o)]='偏印' if same else '正印'
        else: REF[(dg,o)]='?'
name = sys.argv[1]
mod = __import__("engines.common."+name, fromlist=["ten_god"])
fn = mod.ten_god
import inspect
try:
    nargs = len(inspect.signature(fn).parameters)
except Exception:
    nargs = -1
print("签名参数数: %d" % nargs)
bad, crash = [], 0
for dg in GAN:
    for o in GAN:
        try:
            got = fn(dg, o)
        except Exception:
            crash += 1; continue
        want = REF[(dg,o)]
        if str(got) != want: bad.append((dg,o,str(got),want))
print("调用异常: %d   判定错: %d/100" % (crash, len(bad)))
for dg,o,g,w in bad[:10]:
    print("  日主%s vs %s: 得 %s 应 %s" % (dg,o,g,w))
"""


def check_rules():
    print()
    print("=" * 88)
    print("[2] 判定核查  10x10=100 组合全枚举")
    print("=" * 88)
    # 注意: engines.common.l0_fact_builder 导入时有模块级副作用(打印整篇 + 重定向
    #   stdout), 会污染本进程输出。判定核查必须在【独立子进程】里做。
    import subprocess, tempfile
    runner = os.path.join(ROOT, "scripts", "_l2_probe.py")
    io.open(runner, "w", encoding="utf-8", newline="").write(_L2_PROBE)
    for name in ["l0_fact_builder", "ge_jie_layer", "multifactor_eval",
                 "execution_demo"]:
        r = subprocess.run([sys.executable, runner, name],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        out = (r.stdout or "").strip()
        print("\n  --- %s ---" % name)
        if not out:
            print("    (无输出, exit=%s) stderr头: %s"
                  % (r.returncode, (r.stderr or "")[:160].replace("\n", " ")))
        else:
            for ln in out.split("\n")[:14]:
                print("    " + ln)
    try:
        os.remove(runner)
    except Exception:
        pass


def check_struct():
    print()
    print("=" * 88)
    print("[3] 结构核查  ten_god_members (§2.2 L0 契约字段)")
    print("=" * 88)
    from p0_v2.bazi_gate import paipan
    r = paipan("癸亥壬戌乙未壬午")
    raw = r.get("raw_facts") or {}
    tm = raw.get("ten_god_members")
    print("  ten_god_members 存在: %s" % ("✓" if tm is not None else "✗"))
    print("  类型: %s" % type(tm).__name__)
    print("  内容: %s" % json.dumps(tm, ensure_ascii=False)[:400])
    # 十神是否覆盖四柱
    tg = raw.get("ten_god_members") or {}
    for pos in ("year", "month", "day", "hour"):
        v = tg.get(pos) if isinstance(tg, dict) else None
        print("    %-6s %s" % (pos, json.dumps(v, ensure_ascii=False)[:90]))
    # 顶层 ten_god 是否与 L0 一致
    top = r.get("ten_god") or {}
    print("\n  顶层 ten_god(投影): %s" % json.dumps(top, ensure_ascii=False)[:200])


def main():
    if "--uniq" in sys.argv:
        check_uniq()
        return 0
    check_uniq()
    check_rules()
    check_struct()
    return 0


if __name__ == "__main__":
    sys.exit(main())
