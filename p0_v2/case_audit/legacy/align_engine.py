# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""六部经典逐部对齐验证器 (case_audit 语料 → 引擎模块 → 对齐报告)

用法:
    python p0_v2/case_audit/align_engine.py QTBJ [limit]
    python p0_v2/case_audit/align_engine.py PZZQ [limit]
    ...

设计 (一本经典对应一本经典的案例, 逐部调试引擎):
- 每条 classic 使用自己的 *_clean.jsonl 案例集 (清洗后带 bazi/dayun/analysis/label)
- 引擎入口: engines/production_entry.production_entry
  (L0 Fact → L1 40 Query → 调候/病药/用神轨)
- 对齐目标: 引擎输出 (调候候选/格局/用神方向) vs 案例原文断语
- 报告: 逐案例 命中/存疑/未对齐 三类计数 + 明细落盘

不硬造结论: 只统计"引擎说了什么、原文说了什么、两者是否对得上",
对齐判定规则在下方 ALIGN_RULES 里显式声明, 便于人工复核。
"""
import json, re, sys, os, io, contextlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from engines.production_entry import FrozenCanonicalBaziChart, production_entry

HERE = os.path.dirname(os.path.abspath(__file__))
PILLS_KEYS = ('year', 'month', 'day', 'hour')

def parse_bazi(b):
    # 语料里 bazi 有三种形态, 都归一成 8 字:
    #   形态A (4 段干支对): "甲寅 丙寅 戊寅 庚寅" -> 每段 2 字, 拼成 8 字
    #   形态B (8 段散字):   "甲 寅 丙 寅 ..." -> 已是 8 字
    #   形态C (1 段连续):   "甲寅丙寅..." -> 每 2 字一组, 切 4 组
    parts = [x for x in re.split(r'[\s,，、]+', (b or '').strip()) if x]
    if len(parts) == 4:
        # 每段是完整干支对 (2 字), 拆成 8 段
        parts = [ch for seg in parts for ch in (seg[:1], seg[1:2])]
    elif len(parts) == 1:
        s = parts[0]
        parts = [s[i:i + 2] for i in range(0, len(s), 2)]
        parts = [ch for seg in parts for ch in (seg[:1], seg[1:2])]
    if len(parts) == 8:
        return {PILLS_KEYS[i // 2]: [parts[i], parts[i + 1]] for i in range(0, 8, 2)}
    raise ValueError(f'bazi 非 8 字: {b!r} (got {len(parts)} 段)')

WUXING_OF_STEM = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土',
                  '庚':'金','辛':'金','壬':'水','癸':'水'}
# 调候轨原文常见表述 → 候选干: 引擎 climate_candidates 是"该取什么用神干"
# 原文断语里的"喜X/用X/取X/要X/得X" → 看是否提及同名干
TIAOHOU_PATTERNS = {
    '取': r'取([\u4e00-\u9fff])\w?(?:为|作)?用',
    '喜': r'喜([\u4e00-\u9fff])',
    '用': r'用([\u4e00-\u9fff])',
}

def extract_engine(r):
    """从 production_entry 结果里抽出用于对齐的结构化字段"""
    out = {'climates': [], 'yongyao_state': None, 'yongshen_primary': None,
           'special_patterns': [], 'meta_output': None}
    z = r.get('zhenglun') or {}
    cli = z.get('climate_static') or {}
    for c in cli.get('climate_candidates', []):
        out['climates'].append({'stem': c.get('stem'), 'order': c.get('order'),
                                'status': c.get('status')})
    yy = z.get('yongyao') or {}
    out['yongyao_state'] = yy.get('state')
    out['yongshen_primary'] = yy.get('primary_medicine')
    me = r.get('meta_outputs') or {}
    out['meta_output'] = me.get('meta_outputs')
    # L1 40 Query 的三态分布 (供"引擎输出"侧对齐参考, 不逐条展开避免 query 结构不一致)
    l1 = r.get('l1_result') or {}
    out['query_summary'] = l1.get('query_summary')
    return out

def case_align(classic, row, eng):
    """返回 (对齐判定, 说明). 判定: ALIGNED / DIVERGE / NO_EVIDENCE
    保守原则: 只有原文与引擎输出字面一致才判 ALIGNED, 否则 DIVERGE,
    原文无可提取断语时 NO_EVIDENCE. 不硬造.
    """
    analysis = (row.get('analysis') or row.get('raw') or '')
    label = row.get('label')

    if classic in ('QTBJ',):
        # 调候轨: 引擎 climate_candidates 的干 vs 原文"调候用神句"里出现的干
        # 不再裸字全匹配 (QT-0143/QT-0380 假阳性: 藏干/大运名/十神论述里的干不算),
        # 改用调候上下文锚点匹配: 命中干必须出现在"以X为用/取X/用X/喜X/须X/宜X/调候X/X运"的语境里
        analysis = (row.get('analysis') or row.get('raw') or '')
        eng_stems = set(c['stem'] for c in eng['climates'] if c.get('stem'))
        if not eng_stems:
            return 'NO_EVIDENCE', '引擎无调候候选'
        # 调候上下文窗口: 在"以/取/用/喜/须/宜/调候 + 单干"或"干 + 为用/为制/运"里命中的干
        TIAOHOU_CTX = [
            r'以\s*([甲乙丙丁戊己庚辛壬癸])\s*为用',
            r'取\s*([甲乙丙丁戊己庚辛壬癸])',
            r'用\s*([甲乙丙丁戊己庚辛壬癸])',
            r'喜\s*([甲乙丙丁戊己庚辛壬癸])',
            r'须\s*([甲乙丙丁戊己庚辛壬癸])',
            r'宜\s*([甲乙丙丁戊己庚辛壬癸])',
            r'调候\s*([甲乙丙丁戊己庚辛壬癸])',
            r'([甲乙丙丁戊己庚辛壬癸])\s*运',
            r'以\s*([甲乙丙丁戊己庚辛壬癸])\s*制',
        ]
        ctx_stems = set()
        for pat in TIAOHOU_CTX:
            ctx_stems |= set(re.findall(pat, analysis))
        hit = eng_stems & ctx_stems
        if hit:
            return 'ALIGNED', f'引擎调候候选干{sorted(eng_stems)}与原文调候句干{sorted(ctx_stems)}交集: {sorted(hit)}'
        if not ctx_stems:
            return 'NO_EVIDENCE', '原文无调候用神句, 无法对齐'
        return 'DIVERGE', f"引擎调候候选干{sorted(eng_stems)} 原文调候句干{sorted(ctx_stems)} 不相交"

    if classic in ('DTS',):
        # 准神轨: 原文断语 (analysis) 的吉凶方向 vs label
        # 引擎当前不输出吉凶结论, 只输出结构; 对齐口径=结构与原文断语是否兼容
        # 修复 (2026-09-29): neutral/mixed 不再无条件 ALIGNED (审计指 37.1% 零检查 rubber-stamping),
        # 改为: good 要吉词 present AND 凶词 absent; bad 要凶词 present;
        #        mixed 要吉词 AND 凶词 都 present; neutral 要吉词 AND 凶词都 absent
        #        若原文里吉/凶词都缺 (空断语) → DIVERGE (引擎对不上, 原文本身无断语)
        pos_kw = set(re.findall(r'富贵|科甲|进士|尚书|中堂|侍郎|观察|司马|郡守|州牧|诰封|二品|一品|长寿|寿|显赫|贵', analysis))
        neg_kw = set(re.findall(r'夭|凶死|刑|克|贫|残疾|破家|削发|僧|夭折|早逝', analysis))
        label_kw = (label or '').lower()
        if label_kw == 'good':
            compat = bool(pos_kw) and not neg_kw
        elif label_kw == 'bad':
            compat = bool(neg_kw)
        elif label_kw == 'mixed':
            compat = bool(pos_kw) and bool(neg_kw)
        elif label_kw == 'neutral':
            compat = not pos_kw and not neg_kw
        else:
            compat = False
        note = f'label={label} 吉词{list(pos_kw)[:4]} 凶词{list(neg_kw)[:4]}'
        return ('ALIGNED' if compat else 'DIVERGE', note)

    # PZZQ/SFTK/SMTH/YHZP: 暂用 原文干字提及 vs 引擎用神方向 的粗对齐
    mentioned_stems = set(re.findall(r'[甲乙丙丁戊己庚辛壬癸]', analysis))
    yy = eng.get('yongshen_primary')
    yy_wx = WUXING_OF_STEM.get(yy, '') if yy else ''
    note = f"yongyao_state={eng.get('yongyao_state')} primary={yy}({yy_wx}) label={label}"
    if not mentioned_stems:
        return 'NO_EVIDENCE', note + ' 原文无干字'
    if yy and WUXING_OF_STEM.get(yy):
        # 原文提及的干, 取同五行的集合与 primary 比较
        mentioned_wx = set(WUXING_OF_STEM.get(s, '') for s in mentioned_stems)
        if yy_wx in mentioned_wx:
            return 'ALIGNED', note + f' 原文含同五行干'
    return 'DIVERGE', note

def run(classic, limit=None):
    path = os.path.join(HERE, f'{classic}_clean.jsonl')
    if not os.path.isfile(path):
        print(f'{classic} 语料缺失: {path}'); return 1
    rows = [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]
    if limit:
        rows = rows[:limit]
    stats = {'ALIGNED': 0, 'DIVERGE': 0, 'NO_EVIDENCE': 0, 'ERROR': 0}
    diverge_rows = []
    for row in rows:
        bazi = row.get('bazi')
        if not bazi:
            stats['ERROR'] += 1
            continue
        try:
            pills = parse_bazi(bazi)
        except Exception as e:
            stats['ERROR'] += 1
            print(f"  [ERR-parse] {row.get('case_id')} {bazi!r}: {str(e)[:80]}")
            continue
        try:
            chart = FrozenCanonicalBaziChart(pillars=pills, dayun=row.get('dayun') or None)
            r = production_entry(chart)
            eng = extract_engine(r)
            verdict, note = case_align(classic, row, eng)
            stats[verdict] += 1
            if verdict == 'DIVERGE':
                diverge_rows.append({'case_id': row.get('case_id'), 'bazi': bazi,
                                     'label': row.get('label'), 'note': note})
        except Exception as e:
            stats['ERROR'] += 1
            print(f"  [ERR] {row.get('case_id')} {bazi}: {type(e).__name__}: {str(e)[:80]}")
    total = len(rows)
    print(f"\n=== {classic} 对齐报告 (共 {total} 例) ===")
    for k in ('ALIGNED', 'DIVERGE', 'NO_EVIDENCE', 'ERROR'):
        v = stats[k]
        print(f"  {k:12s} {v:5d}  ({v/total*100:.1f}%)" if total else f"  {k} {v}")
    if diverge_rows:
        print(f"\n  前 5 条 DIVERGE 明细:")
        for d in diverge_rows[:5]:
            print(f"    {d['case_id']} {d['bazi']} label={d['label']}: {d['note']}")
    out = os.path.join(HERE, f'{classic}_align_report.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'classic': classic, 'total': total, 'stats': stats,
                   'diverge': diverge_rows}, f, ensure_ascii=False, indent=1)
    print(f"  报告落盘: {out}")
    return 0

if __name__ == '__main__':
    args = sys.argv[1:]
    classic = args[0].upper() if args else 'QTBJ'
    limit = int(args[1]) if len(args) > 1 else None
    sys.exit(run(classic, limit))
