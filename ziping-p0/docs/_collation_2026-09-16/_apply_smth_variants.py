# -*- coding: utf-8 -*-
import json, io

p = r'D:\shuntian-ziping-p0\registries\source\sources.smth.jsonl'
WIKI = "https://zh.wikisource.org/zh-hans/三命通会/卷七"

# target: SMTH-026-015 (論疾病先知五臟六腑所屬干支)
new_variants = [
    {
        "text_status": "TEXT_VARIANT",
        "canonical_for_engine": "PROJECT_BASE_TEXT",
        "human_verdict": "PENDING",
        "loc": "論疾病先知五臟六腑所屬干支·相尅首組組合（金水相尅句）",
        "project_base_text": "金水相尅",
        "variant": "金火相克",
        "variant_sources": [WIKI],
        "note": "字差：底本（國圖掃描版）作「金水相尅」，維基通行本作「金火相克」。金生水為相生、火克金為相克，與篇題「有相尅而成疾」之語境相關；影響疾病規則——何組五行相剋致死絕癆瘵嘔血。"
    },
    {
        "text_status": "TEXT_VARIANT",
        "canonical_for_engine": "PROJECT_BASE_TEXT",
        "human_verdict": "PENDING",
        "loc": "論疾病先知五臟六腑所屬干支·相尅首組生旺症（生旺則句）",
        "project_base_text": "生旺則瘡疥癲狂",
        "variant": "生旺则疡疮瘫肿",
        "variant_sources": [WIKI],
        "note": "字差：底本「瘡疥癲狂」vs 通行本「瘍瘡癱腫」。生旺所主病症不同（瘡疥/癲狂 vs 瘍瘡/癱腫），影響疾病規則語義。"
    },
    {
        "text_status": "TEXT_VARIANT",
        "canonical_for_engine": "PROJECT_BASE_TEXT",
        "human_verdict": "PENDING",
        "loc": "論疾病先知五臟六腑所屬干支·金木相尅死絕句",
        "project_base_text": "死絕主氣虛精脫勞瘵癱瘓之疾",
        "variant": "死绝主气虚精脱、痨疾瘫痪之疾",
        "variant_sources": [WIKI],
        "note": "字差：底本「勞瘵」vs 通行本「癆疾」（勞瘵/癆疾異文）。此句通行本作「癆疾」，與同段首組死絕句「癆瘵嘔血」互文；5.1「勞疾嘔血」之「勞疾」對應此異文。"
    },
]

lines = open(p, encoding='utf-8').read().splitlines()
out = []
hit = False
for ln in lines:
    if not ln.strip():
        out.append(ln); continue
    rec = json.loads(ln)
    if rec.get('source_id') == 'SMTH-026-015':
        rec.setdefault('text_variants', [])
        rec['text_variants'].extend(new_variants)
        hit = True
    out.append(json.dumps(rec, ensure_ascii=False))

assert hit, 'SMTH-026-015 not found'
with io.open(p, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out) + '\n')

# verify: re-read, every line json.loads, count variants on target
recs = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
print('total lines:', len(recs))
for r in recs:
    if r['source_id'] == 'SMTH-026-015':
        print('SMTH-026-015 text_variants count:', len(r.get('text_variants', [])))
        for v in r['text_variants']:
            print(' -', v['loc'], '|', v['project_base_text'], 'vs', v['variant'])
print('VERIFY OK: all lines parse')
