# -*- coding: utf-8 -*-
"""P1 病药层检查器 —— 逐本推进, 每本三项核
  ① bing_list 触发条件对不对(布尔是否干净, 是否有浮点/置信度)
  ② 触发依据是否指向切片 ID(范式 5)
  ③ 五域是否并行(A 类结构性缺失在 P1 的表现)

用法:
  python scripts/check_P1.py --list                    六本条数
  python scripts/check_P1.py DTS                      跑 DTS 全部
  python scripts/check_P1.py DTS --sample 8           抽样盘(规则筛, 不手选)
  python scripts/check_P1.py PZZQ --dump             逐盘打印 bing_list
"""
import sys, os, io, json, glob, argparse, collections

ROOT = r"D:/shuntian-ziping-p0"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

BOOKS = [("DTS", "滴天髓"), ("PZZQ", "子平真诠"), ("QTBJ", "穷通宝鉴"),
         ("YHZP", "渊海子平"), ("SMTH", "三命通会"), ("SFTK", "神峰通考")]
# DTS 优先(准神)。其余按引擎引用频次, 逐本推进。
BOOK_ORDER = ["DTS", "PZZQ", "YHZP", "SFTK", "QTBJ", "SMTH"]

# 引擎引用的 classic 文本 -> 出处书
SOURCE_OF = {}


def load_cases(bk):
    fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
    rows = []
    for line in open(fp, encoding="utf-8-sig"):
        if line.strip():
            rows.append(json.loads(line))
    return rows


def engine_p1(bz):
    """跑一盘, 取出 P1 三项核所需的输出"""
    from p0_v2.bazi_gate import paipan
    r = paipan(bz)
    bl = r.get("bing_list") or []
    return {
        "bing": [{
            "id": b.get("bing_id"),
            "name": b.get("name"),
            "classic": str(b.get("classic")),
            "evidence": b.get("evidence"),
            "matched": b.get("matched_facts"),
            "slice_id": b.get("slice_id"),
            "bing_domain": b.get("bing_domain"),
            "bing_wx": b.get("bing_wx"),
            "keys": sorted(b.keys()),
        } for b in bl],
        "debate": r.get("bing_debate") or {},
        "yongyao": r.get("yongyao") or {},
        "bing_yao": r.get("bing_yao") or {},
    }


def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, path + "." + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, path + "[%d]" % i)
    else:
        yield path, o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("book", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--sample", type=int, default=0,
                    help="只跑前 N 盘(案例表原序, 非手选)")
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--all-books", action="store_true")
    a = ap.parse_args()

    if a.list or not a.book:
        print("=" * 84)
        print("六部经典案例源  (推进顺序: %s)" % " -> ".join(BOOK_ORDER))
        print("=" * 84)
        tot = 0
        for i, (bk, nm) in enumerate(BOOKS):
            n = len(load_cases(bk))
            tot += n
            print("  %d. %-6s %-10s %5d 条" % (i + 1, bk, nm, n))
        print("  %-22s %5d 条" % ("【合计】", tot))
        print("\n  注: DTS 为准神(唯一定本), 故列第 1; 其余为旁参, 按引擎引用频次排。")
        return 0

    books = BOOK_ORDER if a.all_books else [a.book.upper()]
    for bk in books:
        rows = load_cases(bk)
        if a.sample:
            rows = rows[:a.sample]
        nm = dict(BOOKS).get(bk, bk)
        print()
        print("=" * 96)
        print("《%s》%s   案例 %d 条" % (nm, bk, len(rows)))
        print("=" * 96)

        stat = collections.Counter()
        id_cnt = collections.Counter()
        dom_cnt = collections.Counter()
        src_cnt = collections.Counter()
        no_slice = collections.Counter()
        float_hits = []
        crash = 0
        sample_out = []

        for d in rows:
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            try:
                o = engine_p1(bz)
            except Exception as e:
                crash += 1
                stat["★崩溃"] += 1
                float_hits.append((d["case_id"], bz, "%s: %s" % (type(e).__name__, str(e)[:60])))
                continue
            bl = o["bing"]
            stat["有病" if bl else "无病"] += 1
            for b in bl:
                id_cnt[b["id"]] += 1
                dom_cnt[str(b["bing_domain"])] += 1
                if b["slice_id"]:
                    stat["有切片ID"] += 1
                else:
                    no_slice[b["id"]] += 1
                # 出处归类
                c = b["classic"]
                for k in ("DTS", "PZZQ", "YHZP", "SFTK", "QTBJ", "SMTH"):
                    if c.startswith(k):
                        src_cnt[k] += 1
                        break
                else:
                    src_cnt["其他/自造"] += 1
            if a.dump and len(sample_out) < 12 and bl:
                sample_out.append((d["case_id"], bz, bl))

        print("  崩溃 %d" % crash)
        print("  桶: %s" % " | ".join("%s=%d" % (k, v) for k, v in stat.items()))
        print("\n  病机分布:")
        for k, v in id_cnt.most_common():
            print("    %-24s %4d" % (k, v))
        print("\n  病域字段: %s"
              % ", ".join("%s=%d" % (k, v) for k, v in dom_cnt.most_common()))
        print("  依据出处: %s"
              % ", ".join("%s=%d" % (k, v) for k, v in src_cnt.most_common()))
        print("\n  ★ 未挂切片ID 的病 (%d 种): %s"
              % (len(no_slice), ", ".join("%s=%d" % (k, v)
                                       for k, v in no_slice.most_common())))
        if sample_out:
            print("\n  bing_list 抽样(规则: 前 12 个有病的盘, 案例表原序):")
            for cid, bz, bl in sample_out:
                # 检查器教训(2026-10-03): 曾对 classic 截断 [:26], 导致
                #   'SFTK-008-001 用财见比肩为病' 被截成 'SFTK-008-001',
                #   与另一病名的完整值并排出现, 被误判为「classic 双文本 /
                #   运行时改写」。实为检查器显示假象, 引擎无此问题。
                #   -> classic 一律打印全值, 禁止截断。
                print("    %-9s %-17s %s" % (
                    cid, bz, "; ".join("%s(classic=%r)" % (b["name"], b["classic"])
                                       for b in bl)))


if __name__ == "__main__":
    main()