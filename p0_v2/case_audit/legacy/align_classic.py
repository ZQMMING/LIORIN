# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""
按部经典（classic-by-classic）引擎调试器 v0.1
==============================================

每部经典用自己的 case_audit/*_clean.jsonl 逐部验证引擎，六部各对应一个
引擎主战场（取材密度表，六部经典切片规范第十四章）：

    DTS  → 旺衰/病药（准神层）        510 例
    PZZQ → 格局体系                   319 例
    QTBJ → 调候用神                   802 例
    SFTK → 病药                       155 例
    SMTH → 岁运+人事                  114 例
    YHZP → 基础+格局+赋论             206 例

用法：
    python align_classic.py QTBJ      # 跑一部
    python align_classic.py DTS       # 另一部
    python align_classic.py ALL       # 六部全跑（生成报告）

对齐目标（每部不同）：
    DTS  : 旺衰+病药  -> 引擎 wuxing_power 档位 + bingyao_layer 病位 对照 analysis
    PZZQ : 格局名称  -> 引擎 special_pattern + zhengge_quge 对照 analysis 里格名
    QTBJ : 调候用神  -> 引擎 qtbj_climate_candidates 干序 对照 analysis 里"喜X用Y"
    SFTK : 病药     -> 引擎 bingyao_layer 主病 对照 analysis 里"病在X"
    SMTH : 岁运     -> 引擎 dayun_summary/liunian_summary 对照 analysis 里大运判词
    YHZP : 基础+格局 -> 引擎 L0 结构事实 对照 analysis 里格局/六亲表述

本脚本只做：读案例 -> 跑引擎 -> 提取 analysis 里关键结论 -> 输出对齐/分歧 三态报告。
不动引擎逻辑，不改 golden，不替原典下结论。对齐率与分歧清单是"调试引擎"的输入。
"""
import sys, os, json, re, collections, io, argparse
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build as l0b
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.special_pattern import build_special_patterns
from engines.common.qtbj_climate_candidates import build_climate_candidates
from engines.common.bingyao_layer import build_bingyao_layer

DATA = r'D:\wisdom-main\shuntian-ziping-p0\p0_v2\case_audit'
CLASSICS = {
    'DTS':  {'file':'DTS_clean.jsonl',  'layer':'旺衰/病药(准神)', 'count':510},
    'PZZQ': {'file':'PZZQ_clean.jsonl', 'layer':'格局体系',       'count':319},
    'QTBJ': {'file':'QTBJ_clean.jsonl', 'layer':'调候用神',       'count':802},
    'SFTK': {'file':'SFTK_clean.jsonl', 'layer':'病药',           'count':155},
    'SMTH': {'file':'SMTH_clean.jsonl', 'layer':'岁运+人事',       'count':114},
    'YHZP': {'file':'YHZP_clean.jsonl', 'layer':'基础+格局+赋论',  'count':206},
}

def parse_pillars(bazi_str):
    """'庚申 戊寅 甲寅 丙寅' -> pillars dict; 失败返回 None"""
    pairs = [x for x in re.split(r'[\s,，、]+', (bazi_str or '').strip()) if x]
    if len(pairs) != 4:
        return None
    K=('year','month','day','hour')
    pillars={K[i]:(pairs[i][0],pairs[i][1]) for i in range(4)}
    for k,v in pillars.items():
        if len(v)!=2 or not v[0] or not v[1]:
            return None
    return pillars

def run_engine(pillars, classic_code='QTBJ'):
    """跑引擎, 返回结构化结果 (含异常捕获)。按部经典主战场挂对应模块。"""
    out={'error':None}
    try:
        facts=l0b(pillars)
        th=build_tian_he(pillars,facts)
        wp=build_wuxing_power(pillars,facts,th)
        sp=build_special_patterns(pillars,facts,wp,th)
        out['facts']=facts
        out['wuxing_power']=wp
        out['special']=sp
        out['day_stem']=facts.get('day_stem')
        # 各部主战场模块
        if classic_code in ('QTBJ',):
            out['climate']=build_climate_candidates(facts)
        if classic_code in ('DTS','SFTK'):
            by=build_bingyao_layer(facts, [])
            out['bingyao']={'bing_list':[b.get('name') or b.get('bing_type') for b in by.get('bing_list',[])] if isinstance(by,dict) else []}
    except Exception as e:
        import traceback
        out['error']=str(e)+'\n'+traceback.format_exc()
    return out

# ---------- 各部 conclusion 提取器（从 analysis 文本提取该部关注的关键结论） ----------
# 只提取"关键词命中的短片段", 不判引擎对不对; 是否对齐由调用方/原典裁决

def extract_dts(analysis):
    """DTS: 旺衰/病药关键词命中"""
    text=analysis or ''
    kw={'旺':'身旺|旺论|偏旺','衰':'身衰|衰论|偏弱','中和':'中和|得中和','病':'病|忌神|破格','药':'药|救应|通关','从':'从格|专旺|化气'}
    hits={k for k,p in kw.items() if re.search(p,text)}
    return {'hits':hits,'keywords_matched':list(hits)}

def extract_pzzq(analysis):
    """PZZQ: 格局名称"""
    text=analysis or ''
    ge_names=['正官','七杀','偏官','正财','偏财','正印','偏印','食神','伤官',
              '建禄','阳刃','月劫','从财','从杀','从儿','从势','从官','化气',
              '曲直','炎上','稼穑','从革','润下','杂气','财官','食伤']
    found=re.findall('|'.join(ge_names), text)
    return {'ge_mentions':found,'unique_ge':list(dict.fromkeys(found))}

def extract_qtbj(analysis):
    """QTBJ: 调候用神 (喜X / 用X / 取X为用)"""
    text=analysis or ''
    # 匹配 "喜庚用癸" / "用丙癸" / "取庚为用" / "喜X" 等
    m_xi=re.findall(r'喜([甲乙丙丁戊己庚辛壬癸])', text)
    m_yong=re.findall(r'(?:取|用)([甲乙丙丁戊己庚辛壬癸])(?:为用|调候)?', text)
    return {'xi_gan':m_xi,'yong_gan':m_yong}

def extract_sftk(analysis):
    """SFTK: 病/药"""
    text=analysis or ''
    m_bing=re.findall(r'病(?:在|源)?([木火土金水])', text)
    m_yao=re.findall(r'药(?:用|宜)?([木火土金水])', text)
    return {'bing_wx':m_bing,'yao_wx':m_yao}

def extract_smth(analysis):
    """SMTH: 岁运/六亲"""
    text=analysis or ''
    m_liu=re.findall(r'(父|母|妻|夫|子|女|兄弟|寿夭|富贵|刑克)', text)
    return {'liuqin_mentions':list(dict.fromkeys(m_liu))}

def extract_yhzp(analysis):
    """YHZP: 基础/格局/赋论"""
    text=analysis or ''
    m_ge=re.findall(r'(?:格|局)(?:?:成|破|败|全)?', text)
    # 六亲/格局名
    ge_names=['正官','七杀','偏官','正财','偏财','正印','偏印','食神','伤官']
    found=re.findall('|'.join(ge_names), text)
    return {'ge_mentions':found}

EXTRACTORS={'DTS':extract_dts,'PZZQ':extract_pzzq,'QTBJ':extract_qtbj,
            'SFTK':extract_sftk,'SMTH':extract_smth,'YHZP':extract_yhzp}

def run_classic(code, limit=None, out_md=None):
    spec=CLASSICS[code]
    path=os.path.join(DATA, spec['file'])
    rows=[]
    with open(path, encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if line:
                rows.append(json.loads(line))
    if limit: rows=rows[:limit]
    total=len(rows)
    parse_fail=0; engine_err=0
    conclusion_rows=[]
    label_dist=collections.Counter()
    mismatch_hint=0
    for r in rows:
        label_dist[r.get('label','')]+=1
        p=parse_pillars(r.get('bazi',''))
        if p is None:
            parse_fail+=1
            conclusion_rows.append({'case_id':r.get('case_id'),'bazi':r.get('bazi'),
                                   'status':'PARSE_FAIL','label':r.get('label')})
            continue
        er=run_engine(p, code)
        if er.get('error'):
            engine_err+=1
            conclusion_rows.append({'case_id':r.get('case_id'),'bazi':r.get('bazi'),
                                   'status':'ENGINE_ERROR','label':r.get('label'),
                                   'error':er['error'][:120]})
            continue
        ext=EXTRACTORS[code](r.get('analysis',''))
        eng_view={'day_stem':er.get('day_stem'),
                  'special':{k:er['special'].get(k) for k in
                                ('cong_type','cong_state','zhuanwang','zhuanwang_state',
                                 'mu_mie','mu_mie_state','liangqi') if er['special'].get(k)}}
        if code=='QTBJ':
            cl=er.get('climate') or {}
            eng_view['climate_candidates']=[c['stem'] for c in cl.get('climate_candidates',[])]
            eng_view['climate_state']=cl.get('state')
        if code in ('DTS','SFTK'):
            eng_view['bingyao']=er.get('bingyao')
        row={'case_id':r.get('case_id'),'bazi':r.get('bazi'),
             'label':r.get('label'),'verdict':r.get('verdict'),
             'engine_view':eng_view,
             'text_extraction':ext,
             'status':'OK'}
        conclusion_rows.append(row)
    # 输出 markdown 报告
    report_lines=[]
    report_lines.append(f'# {code} 引擎对齐报告 v0.1')
    report_lines.append(f'')
    report_lines.append(f'- 经典: **{code}** — 引擎主战场: {spec["layer"]}')
    report_lines.append(f'- 案例总数: {total}  (已跑 {len(conclusion_rows)})')
    report_lines.append(f'- 八字解析失败: {parse_fail}')
    report_lines.append(f'- 引擎运行异常: {engine_err}')
    report_lines.append(f'- label 分布: {dict(label_dist)}')
    report_lines.append(f'')
    report_lines.append(f'## 引擎输出侧（结构化）')
    report_lines.append(f'')
    report_lines.append(f'每例记录 `engine_day_stem` + `engine_special`（cong/zhuanwang/huaqi/mumie/liangqi）。')
    report_lines.append(f'')
    report_lines.append(f'## 文本结论侧（该部 analysis 提取）')
    report_lines.append(f'')
    report_lines.append(f'按 {code} 主战场提取器产出。')
    report_lines.append(f'')
    # 打印前 15 条供人工抽查
    report_lines.append(f'## 前 15 例对齐数据（JSON）')
    report_lines.append(f'```json')
    report_lines.append(json.dumps(conclusion_rows[:15], ensure_ascii=False, indent=1))
    report_lines.append(f'```')
    md='\n'.join(report_lines)
    if out_md:
        with open(out_md, 'w', encoding='utf-8') as f:
            f.write(md)
    print(md[:4000])
    print(f'... (完整报告已写至 {out_md})' if out_md else '')
    return {'total':total,'parse_fail':parse_fail,'engine_err':engine_err,
            'label_dist':dict(label_dist),'rows':conclusion_rows}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('code', help='DTS/PZZQ/QTBJ/SFTK/SMTH/YHZP 或 ALL')
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--out', default=None)
    a=ap.parse_args()
    codes=['DTS','PZZQ','QTBJ','SFTK','SMTH','YHZP'] if a.code=='ALL' else [a.code]
    for c in codes:
        out=a.out or os.path.join(DATA, f'align_report_{c}.md')
        print('='*20, c, '='*20)
        run_classic(c, limit=a.limit, out_md=out)

if __name__=='__main__':
    main()
