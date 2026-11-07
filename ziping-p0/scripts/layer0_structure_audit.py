# 第0批 结构层全核: 28条关系类型 l0_chart/combination_facts 完备性
import sys,glob,json,re,collections
sys.path.insert(0,"p0_v2");sys.path.insert(0,"engines/common");sys.path.insert(0,"engines")
from bazi_gate import paipan

# 理论结构表(四支全集存在即应有, 与化/力无关)
SANHE_SETS=[frozenset('申子辰'),frozenset('亥卯未'),frozenset('寅午戌'),frozenset('巳酉丑')]
SANHUI_SETS=[frozenset('寅卯辰'),frozenset('巳午未'),frozenset('申酉戌'),frozenset('亥子丑')]
LIUHE_SETS=[frozenset('子丑'),frozenset('寅亥'),frozenset('卯戌'),frozenset('辰酉'),frozenset('巳申'),frozenset('午未')]
LIUHAI_SETS=[frozenset('子未'),frozenset('丑午'),frozenset('寅巳'),frozenset('卯辰'),frozenset('申亥'),frozenset('酉戌')]
LIUPO_SETS=[frozenset('子酉'),frozenset('丑辰'),frozenset('寅亥'),frozenset('卯午'),frozenset('巳申'),frozenset('未戌')]
SANXING_SETS=[frozenset('寅巳申'),frozenset('丑戌未'),frozenset('子卯')]
LIUCHONG_SETS=[frozenset('子午'),frozenset('丑未'),frozenset('寅申'),frozenset('卯酉'),frozenset('辰戌'),frozenset('巳亥')]
BANHE_SETS=[frozenset('申子'),frozenset('亥卯'),frozenset('寅午'),frozenset('巳酉'),
            frozenset('子辰'),frozenset('卯未'),frozenset('午戌'),frozenset('酉丑')]

def pairs_exist(zset, sets):
    return [''.join(sorted(s)) for s in sets if s.issubset(zset)]

def check(b):
    o=paipan(b)
    rf=o.get("raw_facts") or {}
    cf=rf.get("combination_facts") or {}
    l0=rf.get("l0_chart") or {}
    zhis=[o["pillars"][p][1] for p in ["year","month","day","hour"]]
    zset=set(zhis)
    expect={
        "sanhe":pairs_exist(zset,SANHE_SETS),
        "sanhui":pairs_exist(zset,SANHUI_SETS),
        "liuhe":pairs_exist(zset,LIUHE_SETS),
        "liuhai":pairs_exist(zset,LIUHAI_SETS),
        "liupo":pairs_exist(zset,LIUPO_SETS),
        "sanxing":pairs_exist(zset,SANXING_SETS),
        "liuchong":pairs_exist(zset,LIUCHONG_SETS),
        "banhe":pairs_exist(zset,BANHE_SETS),
    }
    got={
        "sanhe":sorted(set(re.sub(r"合.*","",x) for x in (cf.get("sanhe") or []))),
        "sanhui":sorted(set(re.sub(r"三会.*","",x) for x in (cf.get("sanhui") or []))),
        "liuhe":sorted(''.join(sorted(p)) for p in (cf.get("liuhe") or [])),
        "liuhai":sorted(re.sub(r"相害","",x) for x in (cf.get("liuhai") or [])),
        "liupo":sorted(re.sub(r"相破","",x) for x in (cf.get("liupo") or [])),
        "sanxing":sorted(re.sub(r"(三刑|相刑)","",x) for x in (cf.get("sanxing") or [])),
        "liuchong":sorted(''.join(sorted(p)) for p in (cf.get("liuchong") or [])),
        "banhe":sorted(''.join(sorted(p.get("pair",[]))) for p in (cf.get("banhe") or [])),
    }
    miss={}
    for k in expect:
        exp_sets={frozenset(s) for s in expect[k]}
        got_sets={frozenset(s) for s in got[k]}
        if exp_sets and not exp_sets.issubset(got_sets):
            miss[k]=(expect[k],got[k])
    # l0_chart map 键存在性
    l0keys=[k for k in l0 if k.startswith("branch_")]
    return miss,l0keys

seen=set();tot=0;miss_stat=collections.Counter();l0key_stat=collections.Counter()
examples={}
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for line in open(f,encoding="utf-8"):
        d=json.loads(line);cid=d["case_id"]
        if cid in seen:continue
        seen.add(cid);tot+=1
        try:miss,l0keys=check(d["bazi"])
        except Exception as e:
            miss_stat["CRASH"]+=1;continue
        for k,v in miss.items():
            miss_stat[k]+=1
            if k not in examples:examples[k]=(cid,d["bazi"],v)
        for k in l0keys:l0key_stat[k]+=1
print("总盘",tot)
print("结构层缺失统计(理论该有但输出无):")
for k,n in miss_stat.most_common():print("  %s: %d"%(k,n))
print("示例(首个缺失):")
for k,v in examples.items():print("  %s: %s %s exp=%s got=%s"%(k,v[0],v[1],v[2][0],v[2][1]))
print("l0_chart branch_* 键出现频次:")
for k,n in l0key_stat.most_common():print("  %s: %d"%(k,n))
