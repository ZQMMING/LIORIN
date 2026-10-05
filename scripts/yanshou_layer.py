"""验收层(验证脚本, 不进paipan生产): 格局成败×病×药 -> good/bad
组件依据 BOOK_CITED: DTS L240去病/ SFTK L424病得药/ QTBJ有病无药; 公式组合 ENGINE_DEFINED。"""
import json,sys,collections
sys.path.insert(0,"p0_v2")
from bazi_gate import paipan


def bing_resolved(b):
    """病是否得药消解。读病条药字段。"""
    note = b.get("yao_note", "") or ""
    yy = b.get("yao_yuanju", "") or ""
    if yy == "INVALID_POTENTIAL" or "不消" in note or "病重药轻" in note or "力不足" in note:
        return False            # 病重药轻/药无效
    if "消" in note or "得药" in note or yy in ("EFFECTIVE", "RESOLVED"):
        return True
    return False               # 无药/未标 -> 不消


def verdict(r):
    rf = r.get("raw_facts") or {}
    sp = rf.get("special", {}) or {}
    # 从象/专旺成立 -> good
    if sp.get("cong_type") or sp.get("zhuanwang") or sp.get("hua_qi"):
        return "good", "从/专/化"
    bing = r.get("bing_list") or []
    if not bing:
        return "good", "无病"
    unresolved = [b for b in bing if not bing_resolved(b)]
    if not unresolved:
        return "good", "病得药"
    return "bad", "病无药/药轻"


def main():
    agree = tot = crash = 0
    grid = collections.defaultdict(lambda: [0, 0])   # 理由×判 -> [盘,good?]
    for book in ["DTS","PZZQ","QTBJ","SFTK","SMTH","YHZP"]:
        for l in open("p0_v2/case_audit/%s_clean.jsonl"%book,encoding="utf-8-sig"):
            c=json.loads(l); lab=c.get("label")
            if lab not in ("good","bad"): continue
            tot+=1
            try: v,why = verdict(paipan(c["bazi"]))
            except Exception:
                crash+=1; continue
            if v==lab: agree+=1
            grid[(why,v)][0]+=1
            if lab=="good": grid[(why,v)][1]+=1
    print("验收层公式: 总%d 一致%d 一致率%.1f%% 崩溃%d"%(tot,agree,100*agree/tot,crash))
    print("\n格(理由×判定) | 盘 | 其中label-good")
    for k in sorted(grid):
        n,g=grid[k]; print(" %s | %d | %d"%(k,n,g))


if __name__ == "__main__":
    main()
