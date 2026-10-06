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
    # [2026-10-07 PATCH-YS-1] 结构态×验收映射: "special 非空即 good"废止(SF-0151 证伪:
    #   zhuanwang CONFIRMED 结构对、断语"此命无财可倚金水太旺卖尽田园而贫"——结构识别≠吉凶)
    #   规则:
    #     CANDIDATE 态(假从/候选)或两气: 结构上格未成/未定, 不得直接 good -> 落常规病药路径
    #     CONFIRMED 态: 结构成立但吉凶须读用神(从格读财官/化气读化神/母灭读救应),
    #          P2 用神读取层未建 -> 返回 PENDING_SPECIAL 不判, 移出本口径统计(验收层留数)
    #   依据: 前裁「结构事件 vs 吉凶分离」「SF-0151 型=验收层, 非 special_pattern 识别错」
    _sp_any = sp.get("cong_type") or sp.get("zhuanwang") or sp.get("hua_qi") or sp.get("mu_mie") or sp.get("liangqi")
    if _sp_any:
        _st = (sp.get("cong_state") or sp.get("zhuanwang_state") or sp.get("hua_qi_state")
               or sp.get("mu_mie_state")) or ""
        if "CANDIDATE" in _st or sp.get("liangqi"):
            bing = r.get("bing_list") or []
            if not bing:
                return "good", "特殊格CANDIDATE-无病"
            unresolved = [b for b in bing if not bing_resolved(b)]
            if not unresolved:
                return "good", "特殊格CANDIDATE-病得药"
            return "bad", "特殊格CANDIDATE-病无药/药轻"
        return "PENDING_SPECIAL", "特殊格CONFIRMED-待P2用神读取(从读财官/化读化神/母灭读救应)"
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
            try: v,why = verdict(paipan(c["bazi"]))
            except Exception:
                crash+=1; continue
            tot+=1   # 分母=全量有label盘(口径乙 1459), PENDING 计入分母但不计对错
            if v not in ("good","bad"):
                grid[("PENDING_SPECIAL", v)][0]+=1
                if lab=="good": grid[("PENDING_SPECIAL", v)][1]+=1
                continue   # 特殊格CONFIRMED 待 P2 用神读取, 标 PENDING 单列
            if v==lab: agree+=1
            grid[(why,v)][0]+=1
            if lab=="good": grid[(why,v)][1]+=1
    print("验收层公式: 总%d 一致%d 一致率%.1f%% 崩溃%d (PENDING_SPECIAL %d盘计分母不计对错, 待P2用神读取)"%(tot,agree,100*agree/tot,crash,
          sum(g[0] for k,g in grid.items() if k[0]=="PENDING_SPECIAL")))
    print("\n格(理由×判定) | 盘 | 其中label-good")
    for k in sorted(grid):
        n,g=grid[k]; print(" %s | %d | %d"%(k,n,g))


if __name__ == "__main__":
    main()
