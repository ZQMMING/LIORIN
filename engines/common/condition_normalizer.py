# -*- coding: utf-8 -*-
"""PATCH-135 QTBJ condition normalizer v1
只做: 同物异文去重 + context/trigger分流. 不映射L0, 不选primary.
"""
import json
from pathlib import Path
from climate_producer_v2 import _extract

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / 'registries' / 'qtbj_condition_phrase_registry_v2.json'
_BUCKET = {'requires':'primary','secondary_requires':'secondary','needs':'primary',
           'prefers':'preference','controls':'control','balances':'balance',
           'avoids':'avoid','rejects':'avoid'}


class ConditionNormalizer:
    def __init__(self, path=REG):
        r=json.load(open(path,encoding='utf-8'))
        self.ctx=r.get('context_keywords',[])
        self.trg=(r.get('trigger_keywords',[])
                  + r.get('trigger_excess',[])
                  + r.get('trigger_deficiency',[])
                  + r.get('trigger_relationship',[]))

    def _kind(self, phrase):
        if not phrase: return 'context'
        if any(k in phrase for k in self.trg): return 'trigger'
        if any(k in phrase for k in self.ctx): return 'context'
        return 'unclassified'

    def normalize(self, activated):
        prim={}; sec={}; cond=[]; avoid=[]
        for aa in activated:
            b=_BUCKET.get(aa['predicate'],'other')
            cnd=aa.get('condition',{})
            phrase=cnd.get('positive','') if isinstance(cnd,dict) else (cnd or '')
            kind=self._kind(phrase)
            stems,wx=_extract(aa['object'])
            key=stems[0] if stems else (wx[0] if wx else aa['object'])
            rec={'object':aa['object'],'source_assertions':[aa['assertion_id']],
                 'evidence':aa.get('source_evidence',[])}
            if b=='primary' and kind=='trigger':
                rec['trigger_phrase']=phrase
                cond.append(rec)
            elif b=='primary':
                if key in prim: prim[key]['source_assertions'].append(aa['assertion_id'])
                else: prim[key]=rec
            elif b=='secondary':
                if key in sec: sec[key]['source_assertions'].append(aa['assertion_id'])
                else: sec[key]=rec
            elif b=='avoid':
                avoid.append(rec)
        out={'primary_candidates':list(prim.values()),
             'secondary_candidates':list(sec.values()),
             'conditional_candidates':cond,
             'avoid':avoid}
        if len(out['primary_candidates'])==1: out['status']='PRODUCED'
        elif len(out['primary_candidates'])==0: out['status']='ABSTAIN_NO_PRIMARY'
        else: out['status']='MULTIPLE_CANDIDATES'
        return out
