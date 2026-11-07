# -*- coding: utf-8 -*-
"""test_slices.py —— 切片文库校验(915 条 MD)

校验项:
  A 切片ID 格式 [DOMAIN.SUB.CONCEPT.NNN] 且全局唯一
  B 元数据齐全: 来源/版本/页码行号/G1-A Category/切片类型/准神归属/适用范围/校验状态
  C 准神归属取值在枚举内(准/旁参/被DTS否决)
  D 原文段非空
  E 原文重复: 同 ID 不同文件 / 文件内容完全相同 / 原文正文相同但 ID 不同(分三类报)

用法:
    python scripts/test_slices.py            # 全量
    python scripts/test_slices.py --domain STRUCTURE
    python scripts/test_slices.py --dup      # 只看重复明细
"""
import sys, os, re, io, hashlib, argparse, collections

ROOT = r"D:/shuntian-ziping-p0"
LIB = os.path.join(ROOT, "p0_v2", "六部经典MD文库")

ID_RE = re.compile(r"切片ID\*{0,2}\s*[:：]\s*\*{0,2}\s*([A-Za-z0-9_.]+)")
# 切片ID 实测段数分布: 4 段 794 条 / 3 段 121 条(如 PATHOLOGY.GE_JU_BING.001)。
# 两种都在用, 均视为合规 —— 判据是「末段三位序号 + 全大写 + 点分隔」, 不强求子域层数。
FMT_RE = re.compile(r"^[A-Z][A-Z0-9_]*(\.[A-Z0-9_]+)+\.\d{3}$")
META_KEYS = ("来源", "版本", "页码/行号", "G1-A Category",
             "切片类型", "准神归属", "适用范围", "校验状态")
AUTH_OK = {"准", "旁参", "被DTS否决", "被DTS否决/替代", "旁参级"}


def parse(fp):
    t = io.open(fp, encoding="utf-8-sig", errors="ignore").read()
    m = ID_RE.search(t)
    meta = {}
    for k in META_KEYS:
        mm = re.search(re.escape(k) + r"\*{0,2}\s*[:：]\s*\*{0,2}\s*(.+)", t)
        meta[k] = mm.group(1).strip() if mm else ""
    o = re.search(r"^##\s*原文\s*$", t, re.M)
    body = ""
    if o:
        seg = t[o.end():]
        j = re.search(r"^##\s*语义解析", seg, re.M)
        if j:
            seg = seg[:j.start()]
        body = re.sub(r"\s+", "", seg)
    return (m.group(1) if m else ""), meta, body, t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", help="只看某域前缀, 如 STRUCTURE")
    ap.add_argument("--dup", action="store_true", help="只打重复明细")
    a = ap.parse_args()

    files = []
    for root, _d, fs in os.walk(LIB):
        for f in fs:
            if f.endswith(".md"):
                files.append(os.path.join(root, f))
    files.sort()

    ids = collections.defaultdict(list)
    full = collections.defaultdict(list)
    body = collections.defaultdict(list)
    no_id, bad_fmt, miss_meta, bad_auth, empty_body = [], [], [], [], []

    for fp in files:
        sid, meta, bd, raw = parse(fp)
        rel = os.path.relpath(fp, LIB)
        if not sid:
            no_id.append(rel)
            continue
        if not FMT_RE.match(sid):
            bad_fmt.append((sid, rel))
        miss = [k for k in META_KEYS if not meta.get(k)]
        if miss:
            miss_meta.append((sid, miss))
        if meta.get("准神归属") and meta["准神归属"] not in AUTH_OK:
            bad_auth.append((sid, meta["准神归属"]))
        if len(bd) <= 20:
            empty_body.append((sid, len(bd)))
        ids[sid].append(rel)
        full[hashlib.md5(raw.encode()).hexdigest()].append((sid, rel))
        if bd:
            body[hashlib.md5(bd.encode()).hexdigest()].append((sid, rel))

    d_id = {k: v for k, v in ids.items() if len(v) > 1}
    d_full = {k: v for k, v in full.items() if len(v) > 1}
    d_body = {k: v for k, v in body.items() if len(v) > 1}

    print("=" * 88)
    print("切片文库校验  %s" % LIB)
    print("=" * 88)
    print("  切片文件总数            %d" % len(files))
    print("  有切片ID                %d" % len(ids))
    print("  唯一切片ID              %d" % len(set(ids)))
    print("  按域: %s" % ", ".join(
        "%s=%d" % (k, v) for k, v in sorted(
            collections.Counter(s.split(".")[0] for s in ids).items())))

    print()
    print("A 切片ID 格式 [DOMAIN.SUB.CONCEPT.NNN]")
    print("  不合规 %d" % len(bad_fmt))
    for s, r in bad_fmt[:10]:
        print("     %-40s %s" % (s, r))

    print()
    print("B 元数据齐全(8 项)")
    print("  缺项 %d" % len(miss_meta))
    for s, m in miss_meta[:10]:
        print("     %-40s 缺 %s" % (s, m))

    print()
    print("C 准神归属取值合法")
    print("  越界 %d  (合法值: %s)" % (len(bad_auth), "/".join(sorted(AUTH_OK))))
    for s, v in bad_auth[:10]:
        print("     %-40s '%s'" % (s, v))

    print()
    print("D 原文段非空")
    print("  空原文 %d" % len(empty_body))
    for s, n in empty_body[:10]:
        print("     %-40s 长度 %d" % (s, n))

    print()
    print("E 重复")
    print("  ① 切片ID 重复(真重复)              %d 组" % len(d_id))
    for k, v in list(d_id.items())[:10]:
        print("       %s" % k)
    print("  ② 文件内容完全相同(真重复)          %d 组" % len(d_full))
    for k, v in list(d_full.items())[:10]:
        print("       %s" % [x[1] for x in v])
    print("  ③ 原文正文相同 ID 不同(设计使然)     %d 组" % len(d_body))
    for k, v in list(d_body.items())[:12]:
        print("       %s" % [x[0] for x in v])
    print("     ↑ 一句条文切多段归不同域, 非重复。但需核各自『语义解析』是否也照抄。")

    print()
    print("F 无切片ID 的文件(应为报告/清单, 非切片) %d 个" % len(no_id))
    for r in no_id[:30]:
        print("     %s" % r)

    hard = len(bad_fmt) + len(miss_meta) + len(bad_auth) + len(empty_body) + len(d_id) + len(d_full)
    print()
    print("=" * 88)
    print("硬失败(需修): %d      无ID文件(不计失败): %d" % (hard, len(no_id)))
    print("=" * 88)
    return 0 if hard == 0 else 1


if __name__ == "__main__":
    sys.exit(main())