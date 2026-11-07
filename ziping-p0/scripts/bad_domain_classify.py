# -*- coding: utf-8 -*-
"""bad 盘断语五域分类（不碰 label 口径，只对断语原文做关键词归因）

用途: 定位 bad 盘病因在 P1 五域 / 岁运综合的分布, 指导建域优先级。
注意: 关键词法有噪声（寒/燥/枯 等常出现在岁运句）, 数字须人工净核, 不作终判。
运行: p0_v2 目录, python scripts/bad_domain_classify.py
"""
import json, re, collections, os

DOM = {
    "special": r"从财|从杀|从儿|从官|从势|从旺|从化|化气|化神|曲直|炎上|稼穑|从革|润下|顺局|专旺|从象",
    "结构": r"破印|坏印|夺食|枭神|偏印夺|伤官见官|官杀混杂|混杂|争财|夺财|留官|留杀|去杀|财党煞",
    "格局": r"用神被|喜神被|破格|成中有败|成中之败|孤官|无辅|辅佐|官被合|官被冲|官被伤",
    "气候": r"寒|暖|燥|湿|调候|冻|炎|枯|水冷|火炎",
    "五行": r"独旺|全无|相战|源流|通关|一行|两神|战克",
}


def main():
    cnt = collections.Counter()
    ex = collections.defaultdict(list)
    none = []
    base = os.path.join(os.path.dirname(__file__), "..", "p0_v2", "case_audit")
    for book in ["DTS", "PZZQ", "QTBJ", "SFTK", "SMTH", "YHZP"]:
        for l in open(os.path.join(base, "%s_clean.jsonl" % book), encoding="utf-8-sig"):
            c = json.loads(l)
            if c.get("label") != "bad":
                continue
            a = c.get("analysis") or c.get("raw") or ""
            hit = [d for d, p in DOM.items() if re.search(p, a)]
            if not hit:
                none.append(c["case_id"])
                continue
            d = hit[0]
            cnt[d] += 1
            if len(ex[d]) < 5:
                ex[d].append((c["case_id"], a.replace("\n", " ")[:80]))
    print("bad 盘断语五域分布:", dict(cnt), " 未归类(岁运/综合)%d" % len(none))
    for d in ["special", "结构", "格局", "气候", "五行"]:
        print("【%s】%d" % (d, cnt[d]))
        for cid, a in ex[d]:
            print("   ", cid, a)
    print("未归类抽样:", none[:15])


if __name__ == "__main__":
    main()
