# -*- coding: utf-8 -*-
"""布尔层逐字段 × 案例命中率统计.

字段值: 引擎真实输出(paipan raw_facts / l3_contract / root_weight_class).
案例对照: 断语探针(单向"案例说真"关键词) —— 中文否定不可靠, 不做"说假",
         避免验证器搞偏; 每字段自动抽漏判案例供人工核对探针.
口径: 全量 2106 盘(含无 label 案例).
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
CA = os.path.join(ROOT, "p0_v2", "case_audit")
from p0_v2.bazi_gate import paipan
BOOKS = [sys.argv[1].upper()] if len(sys.argv) > 1 else ["PZZQ", "DTS", "QTBJ", "SFTK", "YHZP", "SMTH"]

# 字段: name -> (取值函数(r)->bool, "案例说真"探针正则)
import re
def _lc(r, k):
    return bool((r.get("l3_contract") or {}).get(k))
def _rf(r, k):
    return bool((r.get("raw_facts") or {}).get(k))
def _has_heavy(r):
    rw = r.get("root_weight_class") or {}
    return any((v or {}).get("class") == "HEAVY" for v in rw.values())
def _ren_root(r):
    # 异阴阳本气根(刃/劫财)
    dg = r.get("day_stem", "")
    from engines.common.ge_jie_layer import GAN_WX, YINYANG
    dwx = GAN_WX.get(dg)
    hd = r.get("hidden") or {}
    for pos in ("year","month","day","hour"):
        bg = (hd.get(pos) or [""])[0]
        if bg and GAN_WX.get(bg) == dwx and YINYANG.get(bg) != YINYANG.get(dg):
            return True
    return False

# 探针 v2: 角色绑定(主语须日主/身/我) + 排理论通则句(含 则/云/凡/者/为贵/为贱)
def _says(txt, pat, need_role=False):
    for seg in re.split(r"[。；;\n]", txt):
        if re.search(r"则|云|凡|为贵|为贱|所谓|故曰|故云|若|如[^何]|不得令|不逢令|不逢时|大运|流年|岁运|行运|运中|至[^。；]{0,4}运|^运|，运", seg):
            continue  # 理论/假设/否定/岁运句, 非本命原局事件
        if re.search(pat, seg):
            if not need_role or re.search(r"日主|日干|日元|身|我|本命", seg):
                return True
    return False

FIELDS = [
    ("de_ling 得令",      lambda r: _lc(r, "de_ling"),  r"(日主|日干|日元|身|我)[^，。；]{0,4}(得令|当令|秉令|司令|当权|得时|得旺)"),
    ("de_di 得地",        lambda r: _lc(r, "de_di"),    r"(日主|日干|日元|身|我)[^，。；]{0,4}(通根|得地|有根|根气|根深|坐根|根重|得根)|(通根|有根|根深)[^，。；]{0,4}身(旺|强)"),
    ("dang_duo 党多",     lambda r: _lc(r, "dang_duo"), r"(比劫|劫财|比肩|印绶|党)[^。；]{0,6}(成党|成林|成群|林立|成势|党众|党多|太多)"),
    ("heavy_root 重根",   lambda r: _has_heavy(r),      r"日坐(长生|禄|刃|帝旺)|(日主|身|日元)[^。；]{0,6}(长生|禄|刃|帝旺|重根)"),
    ("blade_root 刃根",   lambda r: _ren_root(r),       r"(阳刃|劫财格|帝旺|刃格|逢刃|坐刃)"),
    ("month_supp 月令生扶", lambda r: _rf(r, "month_supports_daymaster"), r"(月令|提纲|月建)(直接)?(生|扶|帮)|印绶秉令|官星秉令|月令乃印|提纲为印|月建乃印"),
    ("guan_he 官星被合",  lambda r: bool(((r.get("raw_facts") or {}).get("target_relation_facts") or {}).get("官星被合")), r"(官星|正官|官)[^。；]{0,4}(被合|合去|逢合|合住)"),
    ("guan_chong 官星受冲", lambda r: bool(((r.get("raw_facts") or {}).get("target_relation_facts") or {}).get("官星受冲")), r"(官星|正官|官)[^。；]{0,4}(被冲|逢冲|冲去|冲拔|冲坏)"),
]
NEED_ROLE = {"de_ling 得令", "de_di 得地"}

stats = {name: collections.Counter() for name, _, _ in FIELDS}
miss_samples = {name: [] for name, _, _ in FIELDS}
N = 0
for bk in BOOKS:
    p = os.path.join(CA, bk + "_clean.jsonl")
    if not os.path.exists(p):
        continue
    for c in (json.loads(l) for l in open(p, encoding="utf-8-sig") if l.strip()):
        bz = (c.get("bazi") or "").replace(" ", "")
        if len(bz) != 8:
            continue
        N += 1
        txt = (c.get("raw") or "") + " " + (c.get("analysis") or "")
        r = paipan(bz)
        for name, fn, probe in FIELDS:
            v = bool(fn(r))
            says = _says(txt, probe, need_role=(name in NEED_ROLE))
            stats[name]["T" if v else "F"] += 1
            if says:
                stats[name]["sayT"] += 1
                if v:
                    stats[name]["hit"] += 1
                else:
                    stats[name]["miss"] += 1
                    if len(miss_samples[name]) < 5:
                        miss_samples[name].append((c.get("case_id"), bz))

print("总盘=%d\n" % N)
print("%-22s %5s %5s %6s %6s %6s %8s" % ("字段", "True", "False", "说真", "命中", "漏判", "说真命中"))
for name, _, _ in FIELDS:
    s = stats[name]
    rate = (100.0*s["hit"]/s["sayT"] if s["sayT"] else 0)
    print("%-22s %5d %5d %6d %6d %6d %7.0f%%" % (name, s["T"], s["F"], s["sayT"], s["hit"], s["miss"], rate))

print("\n=== 漏判抽样(案例说真/字段假), 用于核对探针 ===")
for name, _, _ in FIELDS:
    if miss_samples[name]:
        print("%-20s %s" % (name, miss_samples[name]))
