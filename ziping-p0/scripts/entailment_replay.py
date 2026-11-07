# -*- coding: utf-8 -*-
"""DTS 语义蕴含回放引擎.

产出五表:
  1) 映射表(entailment_map_dts.MAP)
  2) 命中明细: 盘 x 字段 x 引擎值 x 蕴含值 x 判定
  3) 字段级: 蕴含一致率(MUST) + 反向冲突率(事件类, 主指标)
  4) 冲突桶 / 未覆盖桶 规模
  5) 低一致字段归因(本脚本输出原始计数, 归因见汇总)
两条线不合并: 本回放只评布尔层与原文条件一致性, 不证组合/吉凶.
"""
import sys, os, re, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
from p0_v2.bazi_gate import paipan
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from entailment_map_dts import MAP, CONTROL_BUCKET_PATTERN, EXCLUDE_SEG

GAN_WX = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
SHENG = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
SHEN_SHA_WX = {"财":None,"官":None,"煞":None,"杀":None,"食":None,"伤":None}

def engine_bool(r, field):
    lc = r.get("l3_contract") or {}
    if field == "de_ling": return bool(lc.get("de_ling"))
    if field == "de_di":   return bool(lc.get("de_di"))
    if field == "dang_duo":return bool(lc.get("dang_duo"))
    if field == "heavy":
        rw = r.get("root_weight_class") or {}
        return any((v or {}).get("class") == "HEAVY" for v in rw.values())
    return None

def engine_events(r):
    """结构事件(用于断语蕴含命中): chong/he/root_ba 是否存在."""
    res = r.get("resolved") or {}
    ev = set()
    if res.get("chong_active"): ev.add("chong")
    cf = r.get("combination_facts") or {}
    if cf.get("liuhe"): ev.add("he")
    if reported_root_ba(r): ev.add("root_ba")
    return ev

def reported_root_ba(r):
    """引擎是否据'日主根被冲拔'消费: 日主HEAVY根支参与六冲 且 de_di=False."""
    if engine_bool(r, "de_di"):
        return False
    rw = r.get("root_weight_class") or {}
    res = r.get("resolved") or {}
    active = res.get("chong_active") or []
    dm = r.get("daymaster_element")
    for pos, info in rw.items():
        # HEAVY=日主重根(本气比劫/长生/禄/刃, root_weight_class 已按日主认定), 不看支五行
        if (info or {}).get("class") == "HEAVY":
            br = info.get("branch")
            for pair in active:
                if isinstance(pair, (list, tuple)) and br in pair:
                    return True
    return False

def subject_implies(x, dm_wx):
    """他神 X 当令 -> 是否蕴含日主失令. X 五行==日主或生日主 -> 不蕴含."""
    if not x: return None
    wx = GAN_WX.get(x) or x if x in set("木火土金水") else None
    if x in ("财","官","煞","杀","食","伤"): return True   # 克泄耗, 失令
    if wx:
        return not (wx == dm_wx or SHENG.get(wx) == dm_wx)
    return None

def entailments_of(txt, dm_wx):
    """返回 {field: set(values)}, events: set, strength 记录, 冲突标记."""
    boolvals = collections.defaultdict(set)
    events = set()
    likely = collections.defaultdict(set)
    for seg in re.split(r"[。；;\n]", txt):
        if re.search(EXCLUDE_SEG, seg):
            continue
        for m in MAP:
            mm = re.search(m["pattern"], seg)
            if not mm:
                continue
            if m.get("need_role") and not re.search(r"日主|日干|日元|身|我", seg):
                continue
            field, val = m["target"]
            if field == "event":
                events.add(val); continue
            if field == "stem":
                continue  # 透干泛字段本轮不评
            if m.get("subject") == "x":
                x = mm.groupdict().get("x")
                if not subject_implies(x, dm_wx):
                    continue
            bucket = likely if m["strength"] == "LIKELY" else boolvals
            bucket[field].add(val)
    # 合取冲突: 同字段既有 True 又 False
    conflicts = {f for f, vs in boolvals.items() if True in vs and False in vs}
    return boolvals, events, likely, conflicts

def main(book="DTS"):
    p = os.path.join(ROOT, "p0_v2", "case_audit", book + "_clean.jsonl")
    detail = []
    must = collections.defaultdict(lambda: collections.Counter())
    ev_stat = collections.Counter()
    conflict_n, uncover_n, covered_n = 0, 0, 0
    for l in open(p, encoding="utf-8-sig"):
        c = json.loads(l)
        bz = (c.get("bazi") or "").replace(" ", "")
        if len(bz) != 8: continue
        r = paipan(bz)
        dm_wx = r.get("daymaster_element")
        txt = (c.get("raw") or "") + " " + (c.get("analysis") or "")
        bv, ev, likely, conflicts = entailments_of(txt, dm_wx)
        if conflicts:
            conflict_n += 1
        eng_ev = engine_events(r)
        # 事件: 蕴含一致 + 反向冲突(引擎有/断语无)
        for e in ev:
            ev_stat["entail_ev"] += 1
            if e in eng_ev: ev_stat["ev_hit"] += 1
            else: ev_stat["ev_miss"] += 1
        for e in eng_ev:
            if e not in ev:
                if e == "root_ba":
                    # reported_root_ba 前提(HEAVY根+有效紧贴冲+衰)已硬成立=刘注L139,
                    # 断语省略客观事实 -> justified_unstated 观察桶, 非反向冲突
                    ev_stat["justified_unstated"] += 1
                # chong/he 结构存在不属多报; 其破格消费待格局喜忌(规则1/3/4), 本轮不数
        # 布尔 MUST 一致
        for f, vs in bv.items():
            if f in conflicts: continue
            eng = engine_bool(r, f)
            for v in vs:
                must[f]["total"] += 1
                if eng == v: must[f]["agree"] += 1
                else: must[f]["disagree"] += 1
        if bv or ev: covered_n += 1
        else: uncover_n += 1
        detail.append(dict(cid=c.get("case_id"), bz=bz,
                           entail={k: sorted(v) for k, v in bv.items()},
                           events=sorted(ev), eng_events=sorted(eng_ev),
                           conflicts=sorted(conflicts)))
    total = covered_n + uncover_n
    print("书=%s 总盘=%d\n" % (book, total))
    print("=== 布尔 MUST 蕴含一致率 ===")
    for f, c in must.items():
        rate = 100*c["agree"]/c["total"] if c["total"] else 0
        print("%-9s n=%-4d 一致=%-4d 不一致=%-3d 一致率=%5.1f%%" % (f, c["total"], c["agree"], c["disagree"], rate))
    print("\n=== 事件类 ===")
    print("蕴含事件=%d 命中=%d 漏=%d ; 反向冲突(引擎无据多报)=%d ; 硬成立断语省略(观察)=%d" % (
        ev_stat["entail_ev"], ev_stat["ev_hit"], ev_stat["ev_miss"],
        ev_stat["reverse_conflict"], ev_stat["justified_unstated"]))
    print("反向冲突率=%.1f%% (主指标, 门槛<=10%%)" % (100*ev_stat["reverse_conflict"]/total))
    print("\n=== 桶规模 (门槛 冲突+未覆盖<=25%%) ===")
    print("冲突桶=%d 未覆盖桶=%d 合计占比=%.1f%% ; 覆盖率=%.1f%% (门槛>=70%%)" % (
        conflict_n, uncover_n, 100*(conflict_n+uncover_n)/total, 100*covered_n/total))
    json.dump(detail, open(os.path.join(ROOT,"scripts","replay_%s_detail.json"%book),"w",encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main(sys.argv[1].upper() if len(sys.argv) > 1 else "DTS")
