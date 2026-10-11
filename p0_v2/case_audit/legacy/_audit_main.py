# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""神峰通考 五关验证主脚本 v2"""
import json, re, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

JL = r'D:\顺天系统资料\六部经典独立案例\神峰通考\神峰通考.jsonl'
CAN = r'D:\shuntian\data\classics\canonical\SFTK_神峰通考.txt'
OUTDIR = r'D:\shuntian-ziping-p0\p0_v2\case_audit'

cases = [json.loads(l) for l in open(JL, encoding='utf-8') if l.strip()]
canon = open(CAN, encoding='utf-8').read()

GAN60 = set("甲子 乙丑 丙寅 丁卯 戊辰 己巳 庚午 辛未 壬申 癸酉 甲戌 乙亥 丙子 丁丑 戊寅 己卯 庚辰 辛巳 壬午 癸未 甲申 乙酉 丙戌 丁亥 戊子 己丑 庚寅 辛卯 壬辰 癸巳 甲午 乙未 丙申 丁酉 戊戌 己亥 庚子 辛丑 壬寅 癸卯 甲辰 乙巳 丙午 丁未 戊申 己酉 庚戌 辛亥 壬子 癸丑 甲寅 乙卯 丙辰 丁巳 戊午 己未 庚申 辛酉 壬戌 癸亥".split())
YANG_STEM = set("甲丙戊庚壬"); YIN_STEM = set("乙丁己辛癸")
YANG_BR = set("子寅辰午申戌"); YIN_BR = set("丑卯巳未酉亥")
STEM2EL = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
EL_CTRL  = {"木":"土","土":"水","水":"火","火":"金","金":"木"}
BR_HIDDEN = {
 "子":[("癸",1.0)],"丑":[("己",1.0),("癸",0.5),("辛",0.3)],
 "寅":[("甲",1.0),("丙",0.5),("戊",0.3)],"卯":[("乙",1.0)],
 "辰":[("戊",1.0),("乙",0.5),("癸",0.3)],"巳":[("丙",1.0),("戊",0.5),("庚",0.3)],
 "午":[("丁",1.0),("己",0.5)],"未":[("己",1.0),("丁",0.5),("乙",0.3)],
 "申":[("庚",1.0),("壬",0.5),("戊",0.3)],"酉":[("辛",1.0)],
 "戌":[("戊",1.0),("辛",0.5),("丁",0.3)],"亥":[("壬",1.0),("甲",0.5)],
}

def pillars(b): return [p for p in re.split(r'\s+', (b or '').strip()) if p]
def norm(s): return re.sub(r'\s+', '', s or '')
CN = norm(canon)

def el_strength(bs):
    sc = collections.Counter()
    for p in bs:
        g, z = p[0], p[1]
        sc[STEM2EL[g]] += 1.0
        for h, w in BR_HIDDEN[z]:
            sc[STEM2EL[h]] += w
    return sc

def extract_chart_prose(raw):
    """提取与本造直接相关的散文段落(剔除诗诀、公式套话、注释)"""
    lines = raw.split('\n')
    body_lines = []
    for ln in lines:
        s = ln.strip()
        if not s: continue
        body_lines.append(s)
    # body_lines[0] 含 bazi+标题/散文, 去掉开头四柱
    first = body_lines[0] if body_lines else ''
    first = re.sub(r'^\s*(?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s*){1,4}', '', first).strip()
    rest = body_lines[1:]
    prose_parts = []
    if first and not first.startswith('注释'):
        # 首行若已是公式短句则丢弃
        if len(first) > 18 or re.search(r'此(造|命|八字|日|人)|楠曰|日主|生于|予|吾|某|公|夫人', first):
            prose_parts.append(first)
    in_poem = False
    for s in rest:
        if s.startswith('注释'): break
        if s.startswith('楠曰') or s.startswith('诗曰') or s.startswith('歌曰') or s.startswith('《'):
            in_poem = True; continue
        if in_poem:
            # 诗诀后续行: 含指代词的为散文, 否则为公式/歌括
            if re.search(r'此(造|命|日|八字|人)|日主|生于|予|吾|公|夫人|其|果|大富|大贵|夭|贫|富|贵|予|吾邑', s):
                prose_parts.append(s); in_poem = False
            continue
        if len(s) <= 18 and not re.search(r'此(造|命|日|八字|人)|日主|生于|予|吾|公|夫人|此造|其|果|大富|大贵|夭|贫|富|贵', s):
            break
        prose_parts.append(s)
    return ''.join(prose_parts)

results = []
for c in cases:
    bid = c['case_id']; bazi = c['bazi']; raw = c.get('raw','') or ''; ana = c.get('analysis','') or ''
    bs = pillars(bazi)
    rej = []; doubt = []; pollution = []

    # ===== 第1关 =====
    g1 = True
    if len(bs) != 4:
        rej.append(("八字错", f"四柱数={len(bs)}: {bazi}")); g1 = False
    else:
        for p in bs:
            if len(p) != 2 or p not in GAN60:
                rej.append(("八字错", f"非法干支:{p}")); g1 = False; continue
            s, z = p[0], p[1]
            if (s in YANG_STEM) != (z in YANG_BR):
                rej.append(("八字错", f"阴阳不配:{p}")); g1 = False

    # ===== 第2关 原文存在 (多段容差匹配) =====
    n_ana = norm(ana); n_raw = norm(raw)
    if n_ana and n_ana not in n_raw:
        if n_ana[:16] not in n_raw:
            rej.append(("原文拼接", "analysis与raw正文不一致"))
    # canonical 多段匹配: 跨正文均匀取样
    body = re.sub(r'^\s*(?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s*){1,4}', '', raw).strip()
    nb = norm(body)
    found = False
    if len(nb) >= 16:
        # 均匀取8段
        step = max(1, (len(nb)-16)//8)
        for i in range(0, len(nb)-12, step):
            if nb[i:i+12] in CN:
                found = True; break
    if not found:
        doubt.append(("原文存在", "正文未在canonical底本定位到(版本异文/段损)"))

    # ===== 第3关 =====
    day_stem = bs[2][0] if len(bs)==4 else ''
    day_el = STEM2EL.get(day_stem,'')
    month_br = bs[1][1] if len(bs)==4 else ''

    # 诗诀 (楠曰 / 鹧鸪天 / 诗曰)
    poem = ''
    m = re.search(r'(?:楠曰|诗曰|歌曰|《鹧鸪天》[云：:])(.*?)(?:\n|$)', raw)
    if m: poem = m.group(1)
    poem_day = None; poem_month = None
    # 鹧鸪天等词中找日干
    pm = re.search(r'([甲乙丙丁戊己庚辛壬癸])[木火土金水]?临?[子丑寅卯辰巳午未申酉戌亥]?位?日?时?', raw)
    if poem:
        pm = re.search(r'([甲乙丙丁戊己庚辛壬癸])[木火土金水]?生(?:于)?([子丑寅卯辰巳午未申酉戌亥])', poem)
        if pm:
            poem_day, poem_month = pm.group(1), pm.group(2)
            if poem_day != day_stem:
                rej.append(("诗诀散文矛盾", f"诗诀日干{poem_day} vs bazi日干{day_stem}"))
            if poem_month != month_br:
                doubt.append(("诗诀散文矛盾", f"诗诀月支{poem_month} vs bazi月支{month_br}"))
    # 鹧鸪天 "甲临子位日时全" 式
    if poem_day is None:
        pm2 = re.search(r'([甲乙丙丁戊己庚辛壬癸])临([子丑寅卯辰巳午未申酉戌亥])位', raw)
        if pm2:
            poem_day = pm2.group(1); poem_month = pm2.group(2)
            if poem_day != day_stem:
                rej.append(("诗诀散文矛盾", f"词中日干{poem_day} vs bazi日干{day_stem}"))

    # 断语归属: 仅当散文开头以"别的日干"起论时判串位; 内部十神/藏干"X生Y"不判
    prose = extract_chart_prose(raw)
    if day_stem and bs and prose:
        head = prose[:14]
        hm = re.match(r'^([甲乙丙丁戊己庚辛壬癸])[木火土金水]?生', head)
        if hm and hm.group(1) != day_stem:
            doubt.append(("断语串位", f"散文以{hm.group(1)}起论生月, bazi日干={day_stem}"))
        # 显式"X日主/日干"为异造
        for ss in re.findall(r'([甲乙丙丁戊己庚辛壬癸])[木火土金水]?(?:日主|日干)', prose):
            if ss != day_stem:
                doubt.append(("断语串位", f"散文以{ss}为日主, bazi日干={day_stem}"))

    # 病药判定 (仅对本造散文)
    chart_prose = extract_chart_prose(raw)
    if len(bs)==4 and chart_prose:
        sc = el_strength(bs)
        el_names = ['木','火','土','金','水']
        bing_els = set()
        for en in el_names:
            if re.search(en + r'(太|叠叠|重重|太多|太重|太旺|太盛|太过|四重|叠)', chart_prose):
                bing_els.add(en)
        # 病元素若在bazi完全缺席 -> 存疑
        for be in bing_els:
            if sc.get(be, 0) < 0.3:
                doubt.append(("病药不符", f"散文称{be}为病/太重, 然bazi几无{be}({sc.get(be,0):.1f})"))
        # 药克病校验
        yao_els = set()
        for en in el_names:
            if re.search(r'(喜|用|得|取|赖)[^\u4e00-\u9fa5]{0,2}' + en, chart_prose):
                yao_els.add(en)
        for be in bing_els:
            for ye in yao_els:
                if EL_CTRL.get(be) == ye and EL_CTRL.get(ye) != be:
                    # 病克药: 药反被病克
                    doubt.append(("病药不符", f"病={be}药={ye}, 然{be}克{ye}, 药无力治之"))

    # ===== 第4关 版本污染 =====
    if '注释' in raw: pollution.append('后人评注(注释体混入)')
    if '《鹧鸪天》' in raw or '歌释' in raw: pollution.append('词曲/歌括体(非张楠亲著命例)')
    if '楠曰' not in raw: pollution.append('无楠曰按语(出自歌诀/赋文章节)')

    if rej:
        verdict = 'reject'; reasons = rej
    elif doubt:
        verdict = 'doubt'; reasons = doubt
    else:
        verdict = 'pass'; reasons = []

    results.append({
        'case_id': bid, 'bazi': bazi, 'verdict': verdict,
        'reasons': reasons, 'pollution': pollution,
        'g1_ok': g1, 'found_canon': found,
        'day_stem': day_stem, 'month_br': month_br,
        'poem_day': poem_day, 'poem_month': poem_month,
        'has_poem': bool(poem), 'chart_prose': chart_prose[:80],
    })

cnt = collections.Counter(r['verdict'] for r in results)
print('=== 汇总 ===')
print('total:', len(results), 'pass:', cnt['pass'], 'doubt:', cnt['doubt'], 'reject:', cnt['reject'])

rcat = collections.Counter()
for r in results:
    if r['verdict']=='reject':
        for cat,msg in r['reasons']: rcat[cat]+=1
print('\n=== 驳回原因分类 ===')
for k,v in rcat.most_common(): print(f'  {k}: {v}')

print('\n=== 驳回清单 ===')
for r in results:
    if r['verdict']=='reject':
        print(r['case_id'], r['bazi'], '->', r['reasons'])

print('\n=== 存疑清单(全量) ===')
for r in results:
    if r['verdict']=='doubt':
        print(r['case_id'], r['bazi'], '->', r['reasons'])

with open(OUTDIR+r'\_audit_raw.json','w',encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print('\nsaved.')
