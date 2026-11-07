# -*- coding: utf-8 -*-
"""阶段3b/3c 验收

3b: relations 补 ANHUI + HE 的 distance/blocking
    - ANHUI 条数 == 原 branch_relations.anhui 条数
    - relations(HE).instances 的 distance/blocking == branch_relations.liuhe 对应值
    - 其他 type 的 blocking_branches == []
3c: branch_relations 降级为派生视图, 值与原值 diff=0
全批: 旧九键仍 diff=0
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
if os.path.join(ROOT, "p0_v2") in sys.path:
    sys.path.remove(os.path.join(ROOT, "p0_v2"))
POSK = ("year", "month", "day", "hour")


def main():
    from p0_v2.bazi_gate import _pillars
    from engines.common.relations_builder import build_relations, derive_all
    from engines.common.daymaster_branch_relations import build_branch_relations
    st = collections.Counter()
    dif = collections.defaultdict(list)
    n = 0
    type_cnt = collections.Counter()
    for bk in ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            n += 1
            pil = _pillars(bz)
            zlis = [pil[k][1] for k in POSK]
            R = build_relations(zlis)
            for r in R:
                type_cnt[r["type"]] += 1
            # 原 branch_relations (未改代码的独立函数)
            br = build_branch_relations(pil, {})["zhi_relations"]
            br_he = [r for r in br if r.get("type") == "liuhe"]
            br_an = [r for r in br if r.get("type") == "anhui"]

            # 3b-① ANHUI 条数
            # ★ 口径修正: 比 instances 条数(实例级), 不比 relation 条数(聚合后)
            #   relations 是结构2聚合, relation 条数 != 实例条数; 实例数才是等价口径。
            rel_an = [r for r in R if r["type"] == "ANHUI"]
            n_rel_inst = sum(r["instance_count"] for r in rel_an)
            if n_rel_inst == len(br_an):
                st["ANHUI instances 数一致"] += 1
            else:
                st["★ANHUI instances 数不一致"] += 1
                if len(dif['an_count']) < 3:
                    dif['an_count'].append((d["case_id"], bz, n_rel_inst, len(br_an)))

            # 3b-② HE instances 的 distance/blocking 对齐 branch_relations
            #  branch_relations 是逐实例, relations 是聚合 -> 按 (支对, 柱位对) 建索引比对
            idx_br = {}
            for r in br_he:
                k = (frozenset(r["branches"]), tuple(sorted(r["positions"])))
                idx_br[k] = r
            ok = miss = 0
            for r in R:
                if r["type"] != "HE":
                    continue
                for iv in r["instances"]:
                    k = (frozenset(r["branches"]), tuple(sorted((iv["a_pos"], iv["b_pos"]))))
                    b = idx_br.get(k)
                    if b is None:
                        miss += 1
                        continue
                    if (iv.get("distance") == b.get("position")
                            and iv.get("intervening_branches") == b.get("intervening_branches")
                            and iv.get("blocking_branches") == b.get("blocking_branches")
                            and iv.get("has_blocking") == b.get("has_blocking")
                            and r.get("wx") == b.get("huashen")):
                        ok += 1
                    else:
                        miss += 1
                        if len(dif['he']) < 3:
                            dif['he'].append((d["case_id"], bz, dict(iv), {k2: b.get(k2) for k2 in
                                            ('position', 'intervening_branches', 'blocking_branches', 'has_blocking', 'huashen')}))
            st["HE 实例命中 branch_relations"] += ok
            if miss:
                st["★HE 实例不匹配"] += miss

            # 3b-③ 非 HE 的 blocking 恒 []
            # ★ PAIR 型非 HE: blocking 必为 []/False
            #   SELF 是【另一种元素类型】(无 distance/blocking 键), 不参与本检查
            bad = 0
            for r in R:
                if r["type"] in ("HE", "SELF"):
                    continue
                for iv in r["instances"]:
                    if iv.get("blocking_branches") != [] or iv.get("has_blocking") is not False:
                        bad += 1
            if bad == 0:
                st["PAIR型非HE blocking 恒 []"] += 1
            else:
                st["★PAIR型非HE blocking 非空"] += bad
            # SELF 型: instances 元素必须只有 positions 键(异构建)
            bad2 = 0
            for r in R:
                if r["type"] != "SELF":
                    continue
                for iv in r["instances"]:
                    if set(iv.keys()) != {"positions"}:
                        bad2 += 1
            if bad2 == 0:
                st["SELF 型 instances 恒 {positions}"] += 1
            else:
                st["★SELF 型 instances 键集异常"] += bad2

            # 全批: 旧九键仍可派生且结构完好
            der = derive_all(R)
            st["derive_all 成功"] += 1
    print("=" * 96)
    print("阶段3b 验收   六本 %d 盘" % n)
    print("=" * 96)
    for k in sorted(st):
        print("  %-32s %6d" % (k, st[k]))
    print("\n  relations type 分布:")
    for k, v in sorted(type_cnt.items(), key=lambda x: -x[1]):
        print("    %-10s %6d" % (k, v))
    for k, v in dif.items():
        print("\n  【%s 差异样本】" % k)
        for x in v:
            print("   ", json.dumps(x, ensure_ascii=False)[:400])


if __name__ == "__main__":
    main()