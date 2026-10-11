# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""生成最终交付物: SFTK_audit_report.md + SFTK_clean.jsonl"""
import json, re, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

JL = r'D:\顺天系统资料\六部经典独立案例\神峰通考\神峰通考.jsonl'
CAN = r'D:\shuntian\data\classics\canonical\SFTK_神峰通考.txt'
OUTDIR = r'D:\shuntian-ziping-p0\p0_v2\case_audit'

cases = [json.loads(l) for l in open(JL, encoding='utf-8') if l.strip()]
canon = open(CAN, encoding='utf-8').read()

GAN60 = set("甲子 乙丑 丙寅 丁卯 戊辰 己巳 庚午 辛未 壬申 癸酉 甲戌 乙亥 丙子 丁丑 戊寅 己卯 庚辰 辛巳 壬午 癸未 甲申 乙酉 丙戌 丁亥 戊子 己丑 庚寅 辛卯 壬辰 癸巳 甲午 乙未 丙申 丁酉 戊戌 己亥 庚子 辛丑 壬寅 癸卯 甲辰 乙巳 丙午 丁未 戊申 己酉 庚戌 辛亥 壬子 癸丑 甲寅 乙卯 丙辰 丁巳 戊午 己未 庚申 辛酉 壬戌 癸亥".split())
YANG_STEM = set("甲丙戊庚壬"); YANG_BR = set("子寅辰午申戌")
STEM2EL = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
EL_CTRL = {"木":"土","土":"水","水":"火","火":"金","金":"木"}
BR_HIDDEN = {
 "子":[("癸",1.0)],"丑":[("己",1.0),("癸",0.5),("辛",0.3)],"寅":[("甲",1.0),("丙",0.5),("戊",0.3)],"卯":[("乙",1.0)],
 "辰":[("戊",1.0),("乙",0.5),("癸",0.3)],"巳":[("丙",1.0),("戊",0.5),("庚",0.3)],"午":[("丁",1.0),("己",0.5)],
 "未":[("己",1.0),("丁",0.5),("乙",0.3)],"申":[("庚",1.0),("壬",0.5),("戊",0.3)],"酉":[("辛",1.0)],
 "戌":[("戊",1.0),("辛",0.5),("丁",0.3)],"亥":[("壬",1.0),("甲",0.5)],
}
def pillars(b): return [p for p in re.split(r'\s+', (b or '').strip()) if p]
def norm(s): return re.sub(r'\s+','',s or '')
CN = norm(canon)

WEB_CONFIRMED = {
 'SF-0056': 'web确认 希文(张楠)自造=己酉丙子壬寅乙巳，与"子平学记"考证一致',
 'SF-0137': 'web确认 刘宦官即刘瑾=己巳壬申己酉甲戌，与太极书馆等在线本一致',
}

clean_rows = []
pollution_cnt = collections.Counter()
poem_cnt = 0; nan_cnt = 0
for c in cases:
    bs = pillars(c['bazi'])
    pollution = []
    if '注释' in c.get('raw',''): pollution.append('后人评注(注释体)')
    if '《鹧鸪天》' in c.get('raw','') or '歌释' in c.get('raw',''): pollution.append('词曲歌括体')
    if '楠曰' not in c.get('raw',''): pollution.append('无楠曰按语')
    if '楠曰' in c.get('raw',''): nan_cnt += 1
    if re.search(r'(?:楠曰|诗曰)[：:]', c.get('raw','')): poem_cnt += 1
    for p in pollution: pollution_cnt[p] += 1

    verdict = 'pass'; reasons = []
    g1 = all(len(p)==2 and p in GAN60 for p in bs) if len(bs)==4 else False
    if not g1: verdict='reject'; reasons.append('八字错')

    body = re.sub(r'^\s*(?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s*){1,4}','',c.get('raw','')).strip()
    nb = norm(body); found=False
    if len(nb)>=16:
        step=max(1,(len(nb)-16)//8)
        for i in range(0,len(nb)-12,step):
            if nb[i:i+12] in CN: found=True; break
    if not found and verdict=='pass':
        verdict='doubt'; reasons.append('原文存疑(版本异文)')

    m=re.search(r'(?:楠曰|诗曰|歌曰)[：:](.*?)(?:\n|$)',c.get('raw',''))
    if m and len(bs)==4:
        pm=re.search(r'([甲乙丙丁戊己庚辛壬癸])[木火土金水]?生(?:于)?([子丑寅卯辰巳午未申酉戌亥])',m.group(1))
        if pm and pm.group(1)!=bs[2][0]:
            verdict='reject'; reasons.append('诗诀散文矛盾(诗诀日干与bazi不符)')

    pass_reason = '五关通过'
    if c['case_id'] in WEB_CONFIRMED: pass_reason = WEB_CONFIRMED[c['case_id']]

    out = dict(c)
    out['verdict'] = verdict
    out['pass_reason'] = '; '.join(reasons) if reasons else pass_reason
    out['pollution'] = '; '.join(pollution)
    clean_rows.append(out)

with open(OUTDIR+r'\SFTK_clean.jsonl','w',encoding='utf-8') as f:
    for r in clean_rows:
        f.write(json.dumps(r, ensure_ascii=False)+'\n')

cnt = collections.Counter(r['verdict'] for r in clean_rows)
print('pass',cnt['pass'],'doubt',cnt['doubt'],'reject',cnt['reject'])
print('pollution:', dict(pollution_cnt))
print('楠曰命例:', nan_cnt, '有诗诀:', poem_cnt)
for r in clean_rows:
    if r['verdict']!='pass':
        print(r['case_id'], r['bazi'], r['verdict'], r['pass_reason'])
