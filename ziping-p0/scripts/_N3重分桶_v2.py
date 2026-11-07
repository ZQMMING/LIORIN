# -*- coding: utf-8 -*-
"""
分桶器 v2 (按裁令: ast + tokenize, 不用正则碰词)

引擎侧判据承载的判定 (彻底替代上轮"命中行含 if/return 关键词"的碰词):
  1. tokenize 生成每行的 kind: COMMENT / STRING / CODE
     (只认 CODE 行; 注释行、纯字符串文案行 一律不采信 —— 这是 v1 错根)
  2. ast 解析每个 .py, 收集"真判据承载行":
     - 函数/模块 docstring 所在行            -> DOC
     - 条件语句 If/While/Match 头 + Orel/Eq/NotIn/In 比较 + Call   -> BRANCH
     - 字典/列表赋值 (Dict/List 且 key 含目标词)                    -> TABLE
     - Append/Cast 分支输出                                            -> BRANCH
  3. 目标"概念词"(原典判据核心词) 落在 CODE 行的 BRANCH/TABLE 行   -> 真承载
     仅落在 COMMENT/STRING/DOC 行                                       -> 碰词/弱

输出三桶 (229 条重分):
  真必切   : 概念词 命中 至少 1 行 CODE BRANCH/TABLE
  弱承载   : 概念词 仅命中 CODE 里的表值/docstring, 无独立分支
  撤出碰词 : 概念词 只出现在 COMMENT/STRING/DOC 行 (引擎实无判据承载)
"""
import ast, tokenize, io, os, json, re, glob

ROOT   = r"D:/shuntian-ziping-p0"
ENG    = os.path.join(ROOT, "engines", "common")
OUTJSON= os.path.join(ROOT, "scripts", "_N3重分桶_v2.json")
IN     = os.path.join(ROOT, "scripts", "_N3重分桶_229.json")
# 输出/回显层: 判据词在这些文件里是 echo/track, 非判据入口 → 整文件不计承载
# (transit_power 是流年判据层, 保留; 只剔 纯回显/汇总)
OUTPUT_ONLY = {"meta_unified_output","dayun_summary","liunian_summary","execution_demo"}

# ─────────────────────────────────────────────
# Step 1: 引擎源码 tokenize (每行 kind) + ast (判据承载行)
# 一次算好, 后续 229 条直接查
# ─────────────────────────────────────────────
def parse_one(path):
    raw   = open(path, encoding="utf-8", errors="replace").read()
    src   = raw.lstrip("\ufeff")   # 去 BOM, 否则 ast.parse 报 U+FEFF
    # 1a. tokenize 每行 kind
    line_kind = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                            tokenize.DEDENT, tokenize.COMMENT, tokenize.ENCODING):
                continue
            # COMMENT 行号
            ln = tok.start[0]
            if tok.type == tokenize.STRING:
                line_kind.setdefault(ln, "CODE")
                # 若该行 只有 字符串 + 空白 (纯文案赋值/表值)
                # 保守: 仍 CODE, 但 判 "承载" 需落在 ast 收集的行
            elif tok.type not in (tokenize.NAME, tokenize.OP):
                line_kind.setdefault(ln, "CODE")
        for ln, t in []: pass  # 注释行单独处理:
    except Exception as e:
        print(f"[tokenize fail] {os.path.basename(path)}: {e}")

    # 1b. 注释行识别 (tokenize.COMMENT token)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                line_kind[tok.start[0]] = "COMMENT"
    except Exception:
        pass

    # 1c. ast: 判据承载行 (按 ast 结构判定, 不用变量名碰词)
    bear = {}  # line_no -> {"type":...}
    # 溯源/元数据表 结构特征: dict 值里 带 condition_id/evidence_refs/authorization
    META_VAL_KEYS = {"condition_id","evidence_refs","authorization","condition_name","slice_id"}
    def is_meta_table(val):
        if not isinstance(val, ast.Dict):
            return False
        for v in val.values:
            if isinstance(v, ast.Dict):
                for vk in v.keys:
                    if isinstance(vk, ast.Constant) and isinstance(vk.value, str) and vk.value in META_VAL_KEYS:
                        return True
            if isinstance(v, ast.List):
                for e in v.elts:
                    if isinstance(e, ast.Constant) and isinstance(e.value, str) and e.value in META_VAL_KEYS:
                        return True
        return False
    # 被 If 比较消费的 Name (判据表变量名)
    consumed_names = set()
    try:
        tree = ast.parse(src)
    except Exception as e:
        print(f"[ast fail] {os.path.basename(path)}: {e}")
        tree = None
    if tree:
        # docstrings
        for fn in [n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]:
            if fn.body and isinstance(fn.body[0], ast.Expr) and isinstance(fn.body[0].value, ast.Constant) and isinstance(fn.body[0].value.value, str):
                bear.setdefault(fn.body[0].lineno, {"type":"DOC","text":""})
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
            bear.setdefault(tree.body[0].lineno, {"type":"DOC","text":tree.body[0].value.value})
        # 收集 被 If/While 的 比较(==,in,NotIn,Orel) 消费的 Name
        for n in ast.walk(tree):
            if isinstance(n,(ast.If,ast.While,ast.Match)):
                sub = n.test if isinstance(n,(ast.If,ast.While)) else getattr(n,'case',None)
                if sub is None: continue
                for c in ast.walk(sub):
                    if isinstance(c, ast.Name):
                        consumed_names.add(c.id)
        # 节点级
        for n in ast.walk(tree):
            if isinstance(n,(ast.If, ast.While, ast.Match)):
                test = getattr(n, "test", None) or getattr(n, "case", None)
                text = ast.get_source_segment(src, test) if test else ""
                words = set(re.findall(r"[\u4e00-\u9fa5A-Z_]{2,}", text or ""))
                words.discard("None")
                bear.setdefault(n.lineno, {"type":"BRANCH","text":text,"words":words})
            elif isinstance(n, ast.Assign):
                val = n.value
                tgt_names = []
                for t in n.targets:
                    if isinstance(t, ast.Name): tgt_names.append(t.id)
                    elif isinstance(t, (ast.List, ast.Tuple)):
                        for e in t.elts:
                            if isinstance(e, ast.Name): tgt_names.append(e.id)
                tgtid = " ".join(tgt_names)
                if isinstance(val, ast.Dict):
                    key_ws = set()
                    for k, v in zip(val.keys, val.values):
                        if k is None: continue
                        kt = ast.get_source_segment(src, k) or ""
                        key_ws |= set(re.findall(r"[\u4e00-\u9fa5A-Z_]{2,}", kt))
                    key_ws.discard("None")
                    if is_meta_table(val):
                        ttype = "META"        # 溯源/元数据表, 非判据
                    elif any(tid in consumed_names for tid in tgt_names if tid):
                        ttype = "JUDGE_TABLE"  # 表变量被 If 比较消费 = 判据表
                    else:
                        ttype = "TABLE_CONST"  # 普通常量表 (值枚举, 弱)
                    bear.setdefault(n.lineno, {"type":ttype,"text":"","keys":key_ws,"names":tgt_names})
                elif isinstance(val,(ast.List, ast.Tuple)):
                    ws = set()
                    for c in ast.walk(val):
                        if isinstance(c, ast.Constant) and isinstance(c.value,(str,int)):
                            ws |= set(re.findall(r"[\u4e00-\u9fa5A-Z_]{2,}", str(c.value)))
                    ws.discard("None")
                    ttype = "JUDGE_TABLE" if any(tid in consumed_names for tid in tgt_names if tid) else "TABLE_CONST"
                    bear.setdefault(n.lineno, {"type":ttype,"text":"","keys":ws,"names":tgt_names})
                elif isinstance(val, ast.Call):
                    text = ast.get_source_segment(src, val) or ""
                    words = set(re.findall(r"[\u4e00-\u9fa5A-Z_]{2,}", text))
                    words.discard("None")
                    bear.setdefault(n.lineno, {"type":"BRANCH","text":text,"words":words,"keys":words})
                else:
                    text = ast.get_source_segment(src, n) or ""
                    words = set(re.findall(r"[\u4e00-\u9fa5A-Z_]{2,}", text))
                    words.discard("None")
                    bear.setdefault(n.lineno, {"type":"TABLE_CONST","text":text,"keys":set(),"names":tgt_names})
            elif isinstance(n, ast.Call):
                fnm = n.func
                if isinstance(fnm, ast.Attribute) and fnm.attr in ("append","add","setdefault"):
                    text = ast.get_source_segment(src, n) or ""
                    words = set(re.findall(r"[\u4e00-\u9fa5A-Z_]{2,}", text))
                    words.discard("None")
                    bear.setdefault(n.lineno, {"type":"APPEND","text":text,"words":words})

    # 非承载行(注释/字符串文案) 的 CJK 词 → 撤出碰词证据 (ast 不收这些行)
    bear_lines = set(bear.keys())
    lines_arr = src.splitlines()
    nonbear = {}
    for idx, ln in enumerate(lines_arr, 1):
        if idx in bear_lines:
            continue
        ws = set(re.findall(r"[\u4e00-\u9fa5]{2,}", ln))
        if ws:
            nonbear[idx] = ws
    return line_kind, bear, lines_arr, nonbear

print("解析引擎 .py ...")
ENG_META = {}   # basename -> {kind,bear,lines,nonbear,path}
for path in glob.glob(os.path.join(ENG, "*.py")):
    base = os.path.basename(path)
    kind, bear, lines_arr, nonbear = parse_one(path)
    ENG_META[base] = {"kind":kind, "bear":bear, "lines":lines_arr,
                      "nonbear":nonbear, "path":path}

# ─────────────────────────────────────────────
# Step 2: 229 条 重分桶
# 概念词: 用 原典判据句里 "≥3字非干支非虚词" 的实词 (保留 v1 已抽的 concept 字段,
#         但 用 ast 的 words 集 替代 v1 的"关键词碰字")
# 规则:
#   真必切  : 某概念词 ∈ bear[line].words 且 该 line 是 BRANCH/TABLE 且 kind=line_kind 不是 COMMENT
#   弱承载  : 某概念词 仅出现在 TABLE 的 value 里(不 key) 或 DOC 里
#   撤出碰词: 某概念词 只出现在 COMMENT/STRING 行, 没有任何 BRANCH/TABLE 行
# ─────────────────────────────────────────────
data = json.load(open(IN, encoding="utf-8"))
def norm(w): return re.sub(r"\s+","",w)

def bucket_for(entry):
    book, line, sent, concept = entry["book"], entry["line"], entry["sent"], entry["concept"]
    refs  = entry.get("engine_refs", [])  # v1 的 file:LNN 碰词引用, 作"候选线索"
    # 先做 ast 全库扫描: 哪些 概念词 落在 真承载行
    concept_set = set(norm(c) for c in concept)
    # 扩展: 原典句 取 实词 (排除单字/干支/虚词), 供 ast words 匹配
    real_words = set(re.findall(r"[\u4e00-\u9fa5]{3,}", re.sub(
        r"[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]", "", sent)))
    all_c = concept_set | real_words

    # 遍历引擎 承载行 (ast 分类) —— 强承载 vs 弱承载 (输出/回显层整文件不计)
    strong=[]   # BRANCH(IF判据) / JUDGE_TABLE(判据表被If消费)  = 判据入口
    weak=[]     # TABLE_CONST / APPEND / DOC / META(溯源表)      = 非判据入口
    nb=[]       # 仅注释/文案行 (撤出证据)
    for base, meta in ENG_META.items():
        if os.path.splitext(base)[0] in OUTPUT_ONLY:   # echo/track 层, 判据词不算承载
            continue
        bear = meta["bear"]; nonbear = meta["nonbear"]
        for ln, b in bear.items():
            t = b["type"]
            words = b.get("words") or b.get("keys",())
            ov = {norm(w) for w in words} & all_c
            if not ov:
                continue
            if t in ("BRANCH","JUDGE_TABLE","TABLE_ENUM"):
                strong.append((base, ln, t, sorted(ov)))
            else:  # TABLE_CONST / APPEND / DOC / META
                weak.append((base, ln, t, sorted(ov)))
        for ln, ws in nonbear.items():
            ov = {norm(w) for w in ws} & all_c
            if ov:
                nb.append((base, ln, sorted(ov)))
    # 分类 (ast 语义类型):
    #   真必切 = 有 强承载 (IF 判据分支 或 枚举表 KEY)
    #   弱承载 = 仅 弱承载 (常量/append文案/docstring)
    #   撤出碰词 = 无任何 ast 承载, 词仅在 注释/文案
    #   未命中 = 引擎全库 ast+注释 均无
    if strong:
        return "真必切(引擎判据入口)", [tuple(h) for h in strong[:4]], "ast IF判据分支/枚举表KEY 命中"
    if weak:
        return "弱承载(仅常量/文案/docstring)", [tuple(h) for h in weak[:4]], "仅 常量赋值/append文案/docstring, 非判据入口"
    if nb:
        return "撤出碰词(仅注释/文案)", [tuple(h) for h in nb[:4]], "词仅在注释/文案, 引擎实无判据承载"
    return "未命中", [], "引擎全库 ast+注释 均无该词"

buckets = {"真必切(引擎判据入口)":0, "弱承载(仅常量/文案/docstring)":0,
           "撤出碰词(仅注释/文案)":0, "未命中":0}
out = []
for e in data:
    bk, hits, why = bucket_for(e)
    buckets[bk] = buckets.get(bk, 0) + 1
    out.append({**e, "v2_bucket":bk, "v2_hits":hits, "v2_why":why})

print("\n═══ v2 三桶 (ast 全库真承载扫描) ═══")
for k,v in buckets.items():
    print(f"  {k:24s} = {v}")
print(f"  合计 = {sum(buckets.values())} (输入 229)")

json.dump(out, open(OUTJSON,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nSaved {OUTJSON}")

# ── fanout 检测: 多少条 判据句 共撞 同一 引擎行 → 撞成 catchall 的 降回 弱(需逐条核) ──
# 词粒度碰的本质: N 条不同判据句 命中同一 引擎 if/表 行, 说明该行是"笼统词共享",
# 没有任何一条 被 它 独立 承载. 独享行(1条) 或 低 fanout(≤2条) 才是 真 判据入口.
from collections import defaultdict
true_items = [o for o in out if o["v2_bucket"].startswith("真必切")]
line_fanout = defaultdict(set)   # (base,ln,type) -> set of classic (book,clsicline)
for o in true_items:
    for h in o["v2_hits"]:
        key = (h[0], h[1], h[2])
        line_fanout[key].add((o["book"], o["line"]))
FANOUT_CAP = 2   # 独享(1) / 低(2) = 真承载; ≥3 = catchall, 降回 弱(需逐条核)
def reclassify(o):
    strong = [h for h in o["v2_hits"] if h[2] in ("BRANCH","JUDGE_TABLE","TABLE_ENUM")]
    # 保留 独享/低fanout 的 strong; catchall 的 strong 降 弱
    keep = [h for h in strong if len(line_fanout[(h[0],h[1],h[2])]) <= FANOUT_CAP]
    if keep:
        return "真必切(独享判据行)", [tuple(h) for h in keep[:4]]
    return "弱承载(catchall共享行, 需逐条核)", [tuple(h) for h in strong[:4]]
rebucket = {"真必切(独享判据行)":0, "弱承载(catchall共享行, 需逐条核)":0}
for o in true_items:
    newbk, hits = reclassify(o)
    o["v2_bucket"] = newbk; o["v2_hits"] = hits
    rebucket[newbk] += 1
buckets["真必切(引擎判据入口)"] = 0   # 旧桶并入 上面两细分
buckets["真必切(独享判据行)"] = rebucket["真必切(独享判据行)"]
buckets["弱承载(catchall共享行, 需逐条核)"] = rebucket["弱承载(catchall共享行, 需逐条核)"]

print("\n═══ v2 终桶 (ast 结构 + fanout 剔词粒度碰) ═══")
for k,v in buckets.items():
    if v: print(f"  {k:30s} = {v}")
print(f"  合计 = {sum(v for v in buckets.values() if v)} (含 0 桶前 229)")
json.dump(out, open(OUTJSON,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"Saved {OUTJSON}")

# ── 抽样判对率: 独享真必切 逐条 命中行 是"该判据句专属"还是"仍笼统" ──
uniq = [o for o in out if o["v2_bucket"]=="真必切(独享判据行)"]
print(f"\n═══ 独享真必切 {len(uniq)} 条 · 抽样核 (命中行是否专属承载该判据句) ═══")
from collections import Counter
bybook = Counter(o["book"] for o in uniq)
print("  分本: " + ", ".join(f"{k}={v}" for k,v in bybook.most_common()))
for o in uniq[:12]:
    h = o["v2_hits"][0]
    srcline = ENG_META[h[0]]["lines"][h[1]-1].rstrip()
    print(f"  {o['book']} L{o['line']:<5} {o['concept'][:2]} → {h[0]}:L{h[1]} [{h[2]}]")
    print(f"     判据: {o['sent'][:24]}  引擎: {srcline[:40]}")
