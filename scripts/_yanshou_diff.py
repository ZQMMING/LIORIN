# 盘级验收判定 dump: 新旧双跑找差盘
import json,sys,collections
sys.path.insert(0,"p0_v2");sys.path.insert(0,"engines/common");sys.path.insert(0,"engines")
from bazi_gate import paipan
import sys as _s
sys.path.insert(0,"scripts")
import yanshou_layer as Y

out={}
for book in ["DTS","PZZQ","QTBJ","SFTK","SMTH","YHZP"]:
    for l in open("p0_v2/case_audit/%s_clean.jsonl"%book,encoding="utf-8-sig"):
        c=json.loads(l);lab=c.get("label")
        if lab not in ("good","bad"):continue
        cid=c["case_id"]
        try:
            v,why=Y.verdict(paipan(c["bazi"]))
        except Exception as e:
            v,why="CRASH",str(e)[:40]
        out[cid]={"bazi":c["bazi"],"label":lab,"v":v,"why":why}
json.dump(out,open(_s.argv[1],"w",encoding="utf-8"),ensure_ascii=False)
tot=len(out);agree=sum(1 for x in out.values() if x["v"]==x["label"])
print("盘数%d 一致%d 率%.1f%% 崩溃%d"%(tot,agree,100*agree/tot,sum(1 for x in out.values() if x["v"]=="CRASH")))
