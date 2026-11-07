# -*- coding: utf-8 -*-
"""P2 冲突消解 + 用神层检查器 —— 六项核
  ① 结构: bing_debate 是否有域内主次 + 域间汇总
  ② 结构: yongyao 是否有by_domain 多味并列
  ③ 布尔: 安全检查是否干净(药==病/药生病应剔除; 克日主应剔)
  ④ 序数: compare_key 四项是否真整数(旺1..死5 / 成党0..不成2)
  ⑤ 拓扑: 离散图三边(制/化/帮)落位是否准   ← 重点
  ⑥ 优先级: 字典序最小者是否真为主病

用法:
  python scripts/check_P2.py                六本全跑
  python scripts/check_P2.py --book DTS
  python scripts/check_P2.py --sample 5 --dump
"""
import sys, os, io, json, argparse, collections

ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]
NAME = {"DTS": "滴天髓", "PZZQ": "子平真诠", "YHZP": "渊海子平",
        "QTBJ": "穷通宝鉴", "SFTK": "神峰通考", "SMTH": "三命通会"}
# 序数定义(自证用, 来自 bing_debate docstring)
LING_ORD = {"旺": 1, "相": 2, "休": 3, "囚": 4, "死": 5}
DANG_ORD = {"成党": 0, "成势": 1, "不成": 2}
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
KE_BACK = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}


def all_plates():
    for bk in BOOKS:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        if not os.path.exists(fp):
            continue
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) == 8:
                yield bk, d["case_id"], bz


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--dump", action="store_true")
    a = ap.parse_args()

    from p0_v2.bazi_gate import paipan
    # 注意: bazi_gate 只投影 yongyao 的 primary/ji_shen 两键,
    #   all_edges/medicine_blocked/auxiliary_medicine 在 yongyao_resolve 内部
    #   才有 —— 为核拓扑(⑤)与布尔安全检查(③), 必须走内部 resolve_yongyao,
    #   不能只读 bazi_gate 顶层投影(否则 edges 恒为空, 检查器会假报全通过)。
    from p0_v2.bazi_gate import _pillars
    from engines.common.l0_fact_builder import build as _l0
    from engines.common.wuxing_power import build_wuxing_power
    from engines.common.daymaster_tian_he import build_tian_he
    from engines.common.ge_jie_layer import build_ge_cheng, apply_he_po_ge, normalize_ti_wx
    from engines.common.bingyao_layer import build_bingyao_layer
    from engines.common.bing_debate import resolve_primary_bing
    from engines.common.yongyao_resolve import resolve_yongyao

    def full_p2(bz):
        """跑完整 P2, 返回 (debate, yongyao_full, bing_list)"""
        p = _pillars(bz)
        f = _l0(p)
        f["pillars"] = p
        f["wuxing_power"] = build_wuxing_power(p, f)
        th = build_tian_he(p, f)
        f["tian_he"] = th
        build_ge_cheng(f)
        apply_he_po_ge(f)
        normalize_ti_wx(f)
        bl = build_bingyao_layer(f, []).get("bing_list") or []
        db = resolve_primary_bing(f, bl)
        yy = resolve_yongyao(f, db, {})
        return db, yy, bl

    stat = collections.Counter()
    debate_keys = collections.Counter()
    yy_keys = collections.Counter()
    edge_kinds = collections.Counter()
    bad_bool = []      # ③
    bad_ord = []       # ④
    bad_topo = []      # ⑤
    bad_prio = []      # ⑥
    crash = []
    dumps = []
    n = 0

    for bk, cid, bz in all_plates():
        if a.book and bk != a.book.upper():
            continue
        if a.sample and stat["n"] >= a.sample:
            break
        try:
            db, yy, bl = full_p2(bz)
        except Exception as e:
            crash.append((cid, bz, "%s: %s" % (type(e).__name__, str(e)[:70])))
            continue
        n += 1
        stat["n"] += 1
        for k in db:
            debate_keys[k] += 1
        for k in yy:
            yy_keys[k] += 1
        for b in bl:
            if b.get("bing_domain") is None:
                stat["bing_domain=None"] += 1
            else:
                stat["bing_domain=有值"] += 1

        if not bl:
            stat["无病"] += 1
            continue
        stat["有病"] += 1

        # ---------- ① 结构 ----------
        if db:
            if "by_domain" in db or "domains" in db:
                stat["①有域内主次结构"] += 1
            else:
                stat["①无域内主次"] += 1
            if db.get("primary"):
                stat["①单primary"] += 1
        # ---------- ② 结构 ----------
        if yy and yy.get("primary"):
            if "by_domain" in yy:
                stat["②用神多味并列"] += 1
            else:
                stat["②用神单值"] += 1

        # ---------- ⑥ 优先级 ----------
        cand = db.get("candidates") or db.get("ranked") or []
        if isinstance(cand, list) and len(cand) >= 2:
            p = db.get("primary")
            if p:
                if isinstance(p, dict):
                    pid = p.get("bing_id") or p.get("id")
                else:
                    pid = p
                first = cand[0]
                fid = first.get("bing_id") or first.get("id") if isinstance(first, dict) else first
                if pid == fid:
                    stat["⑥优先级首位一致"] += 1
                else:
                    stat["⑥★首位≠primary"] += 1
                    if len(bad_prio) < 5:
                        bad_prio.append((cid, bz, "primary=%s 首位=%s" % (pid, fid)))

        # ---------- ⑤ 拓扑 + ③ 布尔安全检查 ----------
        # 检查器教训(2026-10-03): 初版把「制边正确条件」写成 KE[病]==药,
        #   方向写反 -> 误报「制边错 1159」。正解 KE_BACK[病]==药, 即药克病
        #   (木病->药金/水病->药土/水病->? ) 引擎实跑 1159/1159 全对。
        #   另一误报: ③ 把不同 kind 的边混在一起比「药==病」, 拿帮边的水去
        #   对制边的土。安全检查必须【按 kind 分别核】, 不能跨边混比。
        edges = yy.get("all_edges") or []
        pbw = (yy.get("primary_bing") or {}).get("wuxing")
        blocked = yy.get("medicine_blocked") or []
        for e in edges:
            if not isinstance(e, dict):
                continue
            k = e.get("kind")
            med = e.get("wuxing")
            fn = str(e.get("function") or "")
            if not med or not pbw:
                continue
            # ⑤ 拓扑: 按 kind 分别核
            if k == "制":
                if KE_BACK.get(pbw) == med:
                    stat["⑤制边正确"] += 1
                else:
                    stat["⑤★制边错"] += 1
                    if len(bad_topo) < 5:
                        bad_topo.append((cid, bz, "制: 病%s 应由%s克, 引擎给药%s"
                                        % (pbw, med, med)))
            elif k == "化":
                if SHENG.get(pbw) == med:
                    stat["⑤化边正确"] += 1
                else:
                    stat["⑤★化边错"] += 1
                    if len(bad_topo) < 5:
                        bad_topo.append((cid, bz, "化: 病%s 所生%s, 引擎给药%s"
                                        % (pbw, SHENG.get(pbw), med)))
            elif k == "帮":
                # 帮 = 比劫(dm) 或 印(生dm)。引擎已算好, 只核它不等于病五行
                if med != pbw:
                    stat["⑤帮边合理"] += 1
                else:
                    stat["⑤★帮边药==病"] += 1
            elif k == "暖":
                stat["⑤暖边(调候)"] += 1
            else:
                stat["⑤未知kind:%s" % k] += 1

            # ③ 布尔安全检查 —— 按 edges 的 accepted/reject_reason 读,
            #   不用 medicine_blocked。medicine_blocked 专指「药被天干合绊」
            #   (L129-142), 与「帮病剔除」是两条不同路径; 前一版拿它当剔除表
            #   读错字段, 误报「帮药未剔349 条」。现直接读 accepted。
            if e.get("accepted") is False:
                stat["③已剔(accepted=False)"] += 1
                _rs = str(e.get("reject_reason") or "")
                if "帮病" in _rs:
                    stat["③剔-帮病"] += 1
                    # 复核: 帮病应恰是 wx==bw 或 SHENG[wx]==bw
                    if med == pbw or SHENG.get(med) == pbw:
                        stat["③剔-帮病判据正确"] += 1
                    else:
                        stat["③★剔-帮病但判据不符"] += 1
                        if len(bad_bool) < 5:
                            bad_bool.append((cid, bz, "reject_reason=帮病 但 药%s 病%s 不构成帮病"
                                            % (med, pbw)))
                elif "帮次病" in _rs:
                    stat["③剔-帮次病"] += 1
                elif "反克日主" in _rs:
                    stat["③剔-化反克日主"] += 1
                elif "无本气根" in _rs:
                    stat["③剔-化财无根"] += 1
                else:
                    stat["③剔-其他"] += 1
            elif e.get("accepted") is True:
                # 真正的安全违规: 药帮病却 accepted=True
                if k in ("帮", "化") and (med == pbw or SHENG.get(med) == pbw):
                    stat["③★帮病却accepted"] += 1
                    if len(bad_bool) < 5:
                        bad_bool.append((cid, bz, "kind=%s 药%s帮病%s 却 accepted=True"
                                        % (k, med, pbw)))
                else:
                    stat["③安全通过"] += 1
            else:
                stat["③★无accepted字段"] += 1

            # medicine_blocked 实际剔了什么
            for b in blocked:
                stat["blocked条目"] += 1

        if a.dump and len(dumps) < 6 and bl:
            dumps.append((cid, bz, db, yy, bl))

    print("=" * 92)
    print("P2 检查器 六项核   盘数 %d   崩溃 %d" % (n, len(crash)))
    print("=" * 92)
    for c in crash[:5]:
        print("  ★崩溃 %-9s %-17s %s" % c)
    print("\n桶: %s" % " | ".join("%s=%d" % (k, v) for k, v in sorted(stat.items())))
    print("\n① bing_debate 输出键: %s"
          % ", ".join("%s=%d" % (k, v) for k, v in debate_keys.most_common()))
    print("② yongyao 输出键:      %s"
          % ", ".join("%s=%d" % (k, v) for k, v in yy_keys.most_common()))
    print("⑤ 拓扑边类型:          %s"
          % (", ".join("%s=%d" % (k, v) for k, v in edge_kinds.most_common()) or "(无 all_edges)"))
    for tag, lst in [("③ 布尔", bad_bool), ("⑤ 拓扑", bad_topo), ("⑥ 优先级", bad_prio)]:
        print("\n%s 问题样本(最多5): %s" % (tag, "无" if not lst else ""))
        for c in lst:
            print("   %-9s %-17s %s" % c)
    if a.dump:
        print("\n--- 抽样 6 盘(规则: 首个有病盘, 案例表原序) ---")
        for cid, bz, db, yy, bl in dumps:
            print("\n  %s %s" % (cid, bz))
            print("    bing_list: %s" % ", ".join(
                "%s(%s)" % (b.get("name"), b.get("bing_id")) for b in bl))
            print("    bing_debate keys: %s" % sorted(db.keys()))
            print("      primary=%r state=%r" % (db.get("primary"), db.get("state")))
            print("    yongyao keys: %s" % sorted(yy.keys()))
            print("      primary=%r ji_shen=%r" % (yy.get("primary"), yy.get("ji_shen")))
            print("      edges=%r" % (yy.get("all_edges"),))
            print("      blocked=%r" % (yy.get("medicine_blocked"),))


if __name__ == "__main__":
    main()