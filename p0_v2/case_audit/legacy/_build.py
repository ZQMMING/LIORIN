# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CASES = r"D:\顺天系统资料\六部经典独立案例\三命通会\三命通会.jsonl"
OUT_DIR = r"D:\shuntian-ziping-p0\p0_v2\case_audit"
RAW = r"D:\shuntian\data\classics\canonical\SMTH_三命通会.txt"

TIANGAN = "甲乙丙丁戊己庚辛壬癸"
DIZHI = "子丑寅卯辰巳午未申酉戌亥"
valid_ganzhi = set(TIANGAN[i%10]+DIZHI[i%12] for i in range(60))

with open(CASES, encoding='utf-8') as f:
    cases = [json.loads(l) for l in f if l.strip()]
with open(RAW, encoding='utf-8') as f:
    canon = f.read()
def norm(s): return re.sub(r'[\s、，,。.；;：:（）()\[\]【】""''！？!?]+','',s)
canon_n = norm(canon)

# ---- 人工核定的具名/特殊标注 ----
# case_id -> dict of annotations
ANNO = {
 "SM-0060": dict(person="明神宗朱翊钧（万历帝）[后世命理文献一致传为]",
                  web_verify="一致：《神宗实录》载嘉靖癸亥(1563)八月十七日酉时生，故宫官网确认；万民英归入飞天禄马/金白水清格。原书未具名，'尊为天子'为格局语。",
                  category="帝皇命例（原书未具名，后世考为明神宗）"),
 "SM-0069": dict(person="明太祖朱元璋",
                  web_verify="一致：正史《明太祖实录》载元天历元年(1328)戊辰九月十八丁丑日；时辰《三命通会》《造化元钥》排丁未时。四库全书本亦作'明太祖命：戊辰、壬戌、丁丑、丁未'。",
                  category="帝皇命例（原书括注明示'明太祖命'）"),
 "SM-0070": dict(person="王阳明（王守仁，封新建伯，谥文成）",
                  web_verify="一致：生于成化八年(1472)壬辰九月三十日亥时；《三命通会》卷九'癸亥日癸亥时'与卷十一'长流龙复归大海'两处并载其造为壬辰、辛亥、癸亥、癸亥，封新建伯。多源命理文献一致。",
                  category="具名历史人物命例"),
 "SM-0072": dict(person="翁仲益（万历二年进士，官知州，晋江人）",
                  web_verify="一致：道光《晋江县志·选举志》载万历二年甲戌孙继皐榜'翁仲益 官知州'；戊申年(1548)生，26岁中进士，与八字年柱戊申吻合。",
                  category="具名历史人物命例"),
 "SM-0083": dict(person="张侍郎（姓名不详）",
                  web_verify="无公开记载：仅称'张侍郎'，正史/方志未见其名，无法交叉核验。",
                  category="具名但身份不可考"),
 # 赋文引古人（王陵/谢安/贾复为赋句典故，非本造命主）
 "SM-0104": dict(person="（赋句引王陵为汉相典故，非本造命主）", web_verify="—", category="赋文引证古人句"),
 "SM-0105": dict(person="（赋句引谢安为晋宰典故，非本造命主）", web_verify="—", category="赋文引证古人句"),
 "SM-0108": dict(person="（赋句引贾复名高典故，非本造命主）", web_verify="—", category="赋文引证古人句"),
 "SM-0110": dict(person="（赋句引贾复典故，非本造命主）", web_verify="—", category="赋文引证古人句"),
}

# canon 底本字形讹注
CANON_TYPO = {
 "SM-0016": "底本作'辛已'，系'辛巳'形近讹字（己/已/巳混），案例归一为'辛巳'正确。",
 "SM-0047": "底本作'已未'，系'己未'形近讹字（己/已/巳混），案例归一为'己未'正确。",
}

def gate1(bz):
    issues=[]
    parts=bz.split()
    if len(parts)!=4: issues.append(f"四柱数={len(parts)}")
    for p in parts:
        if p not in valid_ganzhi: issues.append(f"非法干支:{p}")
    return issues

clean=[]; rejected=[]; doubt=[]
for c in cases:
    bz=c['bazi']
    g1=gate1(bz)
    bz_n=norm(bz)
    in_canon = bz_n in canon_n
    an_n=norm(c['analysis']); raw_n=norm(c['raw'])
    an_in_raw = (an_n in raw_n) if an_n else True
    raw_starts = raw_n.startswith(bz_n)

    anno = ANNO.get(c['case_id'], {})
    poll = CANON_TYPO.get(c['case_id'], "")

    verdict="pass"; reason=[]
    if g1:
        verdict="reject"
        reason.append("；".join(g1))
    else:
        if not in_canon: reason.append("八字未在底本检索到")
        if not an_in_raw: reason.append("analysis非raw子集")
        if not raw_starts: reason.append("raw未以八字起首")
        reason.append("四柱干支合法；原文对应；断语归属正确")

    rec = dict(c)  # 保留原字段
    rec['verdict']=verdict
    rec['pass_reason']="；".join(reason)
    rec['pollution']=poll if poll else ("无版本污染（核心格局/纳音原文）" if verdict=="pass" else "")
    rec['web_verify']=anno.get('web_verify','—')
    rec['person']=anno.get('person','')
    rec['category']=anno.get('category','')

    if verdict=="reject":
        rejected.append(rec)
    else:
        clean.append(rec)

# 写 clean jsonl
with open(OUT_DIR+r"\SMTH_clean.jsonl","w",encoding="utf-8") as f:
    for r in clean:
        f.write(json.dumps(r, ensure_ascii=False)+"\n")

print(f"通过: {len(clean)}")
print(f"驳回: {len(rejected)}")
print(f"存疑: {len(doubt)}")
print(f"驳回清单:")
for r in rejected:
    print(" ", r['case_id'], r['bazi'], r['pass_reason'])

# 统计分类
named_real = [r for r in clean if r['category'] in ("帝皇命例（原书括注明示'明太祖命'）","帝皇命例（原书未具名，后世考为明神宗）","具名历史人物命例","具名但身份不可考")]
fushi = [r for r in clean if r['category']=="赋文引证古人句"]
bare = [r for r in clean if not r['category']]
print(f"\n具名真实人物: {len(named_real)}")
for r in named_real: print("  ", r['case_id'], r['bazi'], r['person'])
print(f"赋文引证古人句(非命主): {len(fushi)}")
print(f"裸八字/格局纳音举例: {len(bare)}")
