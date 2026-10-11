# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""
第一步：关键词初步分四类
good: 富贵/科甲/仕路显赫/长寿/富
bad: 凶死/贫夭/残疾/刑克/破家
mixed: 贵但短寿/先凶后吉/吉凶并存
neutral: 中性/无明确吉凶
"""
import json, os, re
from collections import Counter

OUT = r"D:\shuntian-ziping-p0\p0_v2\case_audit"
books = ["DTS","PZZQ","QTBJ","YHZP","SFTK","SMTH"]

# 贵词/好词
GOOD_WORDS = [
    "富贵","荣华","显达","显贵","科甲","科第","登科","及第","中举","进士","状元","榜眼","探花",
    "尚书","侍郎","中丞","御史","巡抚","总督","布政","知府","知县","县令","中堂","相国","宰辅",
    "仕至","仕路","仕途","宦海","为官","出仕","登仕","仕宦","功名","名登","金榜",
    "长寿","高寿","耄耋","期颐","遐龄","颐养","寿考","寿元","不夭","无疾而终",
    "富","发财","巨富","万金","千金","致富","饶裕","殷实","丰盈","大富","富厚",
    "贵","贤","德","才子","文章","才名","名世","大儒","学者",
    "太平","福泽","享福","安乐","顺遂","无忧","亨通","荣昌","隆盛",
    "不禄","考终","正寝","善终","令终"  # 善终类
]
# 凶词/坏词
BAD_WORDS = [
    "凶死","恶死","横死","非命","短折","夭","夭折","早亡","早逝","早卒",
    "贫","寒","贱","孤","寡","独","穷","困","蹇","滞","不达","不遇",
    "刑","克","伤","伤妻","克妻","克夫","克子","克父","克母","刑妻","刑夫","刑子",
    "破","败","荡","倾","覆","破产","败家","荡产","破家","祖业",
    "残疾","废","疯","癫","聋","哑","盲","跛","瘸",
    "凶","祸","灾","厄","难","危","危亡","祸患",
    "无子","无后","绝嗣","无儿","无女",
    "下贱","伶仃","孤苦","零丁","漂泊","流落",
    "不禄"  # 这个其实中性,但和早死相关,先放这里观察
]

def has_word(text, words):
    return [w for w in words if w in text]

for book in books:
    f = os.path.join(OUT, f"{book}_clean.jsonl")
    recs = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
    ambiguous = []
    for r in recs:
        text = r.get("raw","") + r.get("analysis","")
        good_hits = has_word(text, GOOD_WORDS)
        bad_hits = has_word(text, BAD_WORDS)
        r["_good_hits"] = good_hits
        r["_bad_hits"] = bad_hits
        if good_hits and bad_hits:
            ambiguous.append(r)
    print(f"{book}: {len(recs)} total, {len(ambiguous)} ambiguous (both good+bad)")

# Save ambiguous list for review
amb_all = []
for book in books:
    f = os.path.join(OUT, f"{book}_clean.jsonl")
    recs = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
    for r in recs:
        text = r.get("raw","") + r.get("analysis","")
        gh = has_word(text, GOOD_WORDS)
        bh = has_word(text, BAD_WORDS)
        if gh and bh:
            amb_all.append({"book": book, "case_id": r["case_id"], "bazi": r["bazi"],
                           "good_hits": gh, "bad_hits": bh,
                           "raw_head": r.get("raw","")[:400].replace("\n"," ")})

with open(os.path.join(OUT, "_ambiguous_cases.json"), "w", encoding="utf-8") as f:
    json.dump(amb_all, f, ensure_ascii=False, indent=2)
print(f"\nTotal ambiguous: {len(amb_all)}")
print(f"Saved to _ambiguous_cases.json")
