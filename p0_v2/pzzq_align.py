# -*- coding: utf-8 -*-
"""PZZQ 案例喜忌对标脚本
加载 PZZQ_clean.jsonl, 逐条跑引擎, 从 analysis 提取喜忌, 对标格局层。
输出: p0_v2/case_audit/PZZQ_align_report.json + PZZQ_align_report.md

================================================================================
硬规则（Human Architect 裁决 2026-09-30）—— 任何喜忌判定前必须先核五行生克
================================================================================
禁止凭印象判「引擎多给/少给」。生克关系错一次，整轮结论作废。

缘起（已犯两次，皆因此）：
  1. 2026-09-30 PZ-0078：误判「庚金日主火=财」→ 实为 **火=官杀**（克我者）、
     **木=财**（我克者）。据此错报「引擎阳刃格多给喜神排除项（财）」，
     实际引擎 xi_wx=['土','火']=印+官杀，**完全正确**且已正确排除财（木），
     符合对照表「刃宜伏制，官煞皆宜，财印相随」「阳刃用财，格所不喜」。
  2. 更早一轮同类错误导致「原断说财为忌」等假象。

五行生克基准（务必先在纸上过一遍）：
  生我者=印    |  我生者=食伤  |  我克者=财    |  克我者=官杀  |  同我者=比劫
  （母→子）      （子→泄）      （我→妻财）    （官→克身）    （比劫）

  按日主五行速查（日主 → 印/食伤/财/官杀/比劫）：
    甲乙木 → 印=水  食伤=火  财=土  官杀=金  比劫=木
    丙丁火 → 印=木  食伤=土  财=金  官杀=水  比劫=火
    戊己土 → 印=火  食伤=金  财=水  官杀=木  比劫=土
    庚辛金 → 印=土  食伤=水  财=木  官杀=火  比劫=金
    壬癸水 → 印=金  食伤=木  财=火  官杀=土  比劫=水

复核方式：调用本文件 `ten_god_wx(day_stem, 十神名)` 取五行，
**禁止**手工默记或凭印象填写任何「某神=某五行」的结论。
================================================================================
"""
import sys, json, re
sys.path.insert(0, '.')
from pathlib import Path
from collections import defaultdict

K = ('year', 'month', 'day', 'hour')

def gp(s):
    s = s.replace(' ', '')
    return {K[i//2]: [s[i], s[i+1]] for i in range(0, 8, 2)}

from engines.common.l0_fact_builder import build as l0build
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.wuxing_power import build_wuxing_power
from engines.common.special_pattern import build_special_patterns
from engines.common.ge_jie_layer import build_ge_cheng, normalize_ti_wx
from engines.common.daymaster_power_structure import build_power_structure
from engines.common.daymaster_root_class import build_root_classes
from engines.common.daymaster_tou_cang import build_tou_cang
from engines.common.daymaster_wang_xiang import build_wang_xiang
from engines.common.daymaster_root_relations import build_root_relations
from engines.common.daymaster_two_side import build_two_side
from engines.common.daymaster_branch_tier import build_branch_tiers
from engines.common.daymaster_power_network import build_power_network
from engines.common.daymaster_power_queries import run_queries
from engines.common.bingyao_layer import build_bingyao_layer
from engines.common.bing_debate import resolve_primary_bing
from engines.common.zhuangui_layer import resolve_zhuangui
from engines.common.qtbj_climate_candidates import build_climate_candidates
from engines.common.yongyao_resolve import resolve_yongyao
from p0_v2.domain_extract import extract_marked

GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
WUXING = ('木','火','土','金','水')
from engines.common.ge_jie_layer import GAN_WX as _GW, YINYANG as _YY, SHENG as _SH, KE as _KE
_SHENG_ME = {v:k for k,v in _SH.items()}
_KE_ME = {v:k for k,v in _KE.items()}

def ten_god_wx(day_stem, ten_god):
    dm_wx = GAN_WX.get(day_stem, '')
    if not dm_wx:
        return []
    # 十神简写 + 全名 统一映射
    if ten_god in ('印', '正印', '偏印'):
        return [_SHENG_ME.get(dm_wx, '')]
    elif ten_god in ('财', '正财', '偏财'):
        return [_KE.get(dm_wx, '')]
    elif ten_god in ('官', '正官'):
        return [_KE_ME.get(dm_wx, '')]
    elif ten_god in ('食伤', '食神', '伤官'):
        return [_SH.get(dm_wx, '')]
    elif ten_god in ('比劫', '比肩', '劫财'):
        return [dm_wx]
    elif ten_god in ('杀', '七杀', '偏官'):
        return [_KE_ME.get(dm_wx, '')]
    return []

# 岁运语境: 句中出现即判定该句说的是"运上如何", 不是原局格局喜忌
# 命中此类语境且带喜忌词的句, 其喜忌单列 yun_hits, 不进原局对标
_GZ = '甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥'
DAYUN_CTX = re.compile(
    r'行\s*[%s]{1,2}\s*[运年]|[%s]{1,2}\s*运(?:为|主|最|亦|喜|忌|行|不|方|至|逢)|'
    r'运(?:为|主|至|逢|喜|忌|不|亦|行|程|局|地|岁|来|去|上|下|中|美|间)|'
    r'年(?:为|至|主|喜|忌)|大运|流年|行运|运中|运美|运上|运下|运间|运来|运去|'
    # 运境术语: "比劫乡/财乡"(乡=运境) 与 "印地/行财地/食伤生财之地"(地=运境)
    r'[财印杀食比劫官伤枭](?:生[财印杀食比劫官伤枭])?乡|'
    r'行\s*%s{1,2}?地|[财印杀食比劫官伤枭](?:生[财印杀食比劫官伤枭])?之地'
    % (_GZ, _GZ, _GZ))

# 喜忌关键词模式 (按优先级, 先匹配先命中)
XIJIKUANG = [
    (r'喜[\s]*火|需火|寒木向阳|解冻|暖局', ['火'], '喜'),
    (r'喜[\s]*水|需水|润燥|寒凝', ['水'], '喜'),
    (r'喜[\s]*木|木为喜', ['木'], '喜'),
    (r'喜[\s]*金|金为喜', ['金'], '喜'),
    (r'喜[\s]*土|土为喜', ['土'], '喜'),
    # 忌财: "财重" 须带破印语境才算忌(对照表印绶格"印轻财重, 又无劫财以救, 则为贪财破印");
    #   裸"财重"是格局轻重描述("食轻财重"), 且对照表明言"印多用财, 透财以抑太过, 无防财破" -> 财反为喜
    (r'忌财|财为忌|贪财(?:破|坏)印|财(?:为)?病神', ['财'], '忌'),
    (r'财重.{0,6}(?:破印|坏印|病神|为病)', ['财'], '忌'),
    (r'忌比|比劫为忌|比劫争财|比劫夺财', ['比劫'], '忌'),
    # 忌官: 岁运引动由句级门控拦截(DAYUN_CTX), 此处只管原局
    (r'忌官|官为忌|伤官见官', ['官'], '忌'),
    (r'忌杀|杀为忌', ['杀'], '忌'),
    (r'忌食|食为忌', ['食伤'], '忌'),
    (r'忌木|木为忌', ['木'], '忌'),
    (r'忌金|金为忌', ['金'], '忌'),
    (r'忌土|土为忌', ['土'], '忌'),
    (r'忌水|水为忌', ['水'], '忌'),
    (r'忌火|火为忌', ['火'], '忌'),
    (r'用印|印为用|取印|喜印', ['印'], '喜'),
    # 印重/身旺印强 = 印绶格成格条件, 非忌(对照表ZHENG_YIN_001"身旺印强, 不愁太过"; 破格是"印轻逢财")
    (r'印重|身旺印强|印绶喜其生身', ['印'], '喜'),
    (r'用财|喜财|财为用|取财|财为喜', ['财'], '喜'),
    (r'用官|喜官|官为用|取官|用官杀|官杀为用', ['官'], '喜'),
    (r'用食|喜食|食为用|食伤为用|食神制杀|制杀|食伤制杀|食制杀', ['食伤'], '喜'),
    (r'用比|比劫为用|比劫帮身', ['比劫'], '喜'),
]

ZHI_BEN = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火',
           '未':'土','申':'金','酉':'金','戌':'土','亥':'水'}

# 喜神排除项已知清单(裁决 2026-09-30 短期方案 b)
# 来源: governance/PZZQ_八格成破对照表.md —— 该表原文明言"XX格所不喜"者
# 语义: 该五行**出现则不入喜**(与 po_ge 破格触发条件不同 —— po_ge 是"出现则破格",
#       本表是"出现也不许作喜神"). 例: 阳刃用财"格所不喜" -> 财不作阳刃格喜神,
#       但财出现并不使阳刃格破格.
# 用途: 短期供人工复核清单(指标不可见); 中期建模为引擎 ge_jie_layer[].ji_exclude
JI_EXCLUDE_KNOWN = {
    '阳刃格': [  # 对照表 JIAN_LU_YANG_REN_002: "阳刃用财, 格所不喜(刃与财相搏不成局)"
        ('_cai_wx', '对照表明言"阳刃用财, 格所不喜"; 财根深而用伤食转刃生财方就富'),
    ],
    '建禄月劫格': [  # 对照表 JIAN_LU_YANG_REN_004: "无财官, 透煞印" -> 煞印不作喜
        ('_sha_wx', '对照表破格"无财官, 透煞印"; 煞印出现即破, 不作喜神'),
    ],
}
# 更正记录(2026-09-30):
#   初版曾把 PZ-0078 当作"指标掩盖真错误"的实例 —— **该判断错误**。
#   庚金日主: 克我者为火(官杀), 我克者为木(财)。引擎 阳刃格 xi_wx = 官煞(火)+印(土)
#   完全符合对照表"刃宜伏制, 官煞皆宜, 财印相随", 且未给财(木)。
#   PZ-0078 **无引擎错误**, 系"引擎给该格全部喜神(官煞+印) / 原断只提救应焦点(印)"的
#   正常粒度差, 应记「方向一致粒度不同」而非「不一致（多给）」。
#   本清单保留, 但**当前无命中案例**; ji_exclude 建模的价值转为"防御性完备", 非补救已知错误。

def _ji_exclude_wx(ge, day_master):
    """把 JI_EXCLUDE_KNOWN 的占位符解析为实际五行集合"""
    GAN_WX_ = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土',
               '庚':'金','辛':'金','壬':'水','癸':'水'}
    SHENG = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
    KE = {'木':'土','土':'水','水':'火','火':'金','金':'木'}
    KE_M = {'木':'金','火':'水','土':'木','金':'火','水':'土'}
    dm = GAN_WX_.get(day_master, '')
    m = {'_cai_wx': [KE.get(dm, '')], '_sha_wx': [KE_M.get(dm, '')],
         '_ss_wx': [SHENG.get(dm, '')]}
    out = []
    for ph, why in JI_EXCLUDE_KNOWN.get(ge, []):
        for w in m.get(ph, []):
            if w:
                out.append((w, why))
    return out


def _std(wx_list, day_master):
    """十神/干/支/五行 统一标准化为五行集合"""
    out = set()
    for w in wx_list:
        if w.startswith(('SHISHEN:', 'GAN:', 'ZHI:', 'WX:')):
            kind, name = w.split(':', 1)
            if kind == 'SHISHEN':
                for wx in ten_god_wx(day_master, name):
                    out.add(wx)
            elif kind == 'GAN':
                if name in GAN_WX:
                    out.add(GAN_WX[name])
            elif kind == 'ZHI':
                if name in ZHI_BEN:
                    out.add(ZHI_BEN[name])
            else:
                if name in WUXING:
                    out.add(name)
            continue
        if w in ('印','财','官','食伤','比劫','杀','正印','偏印','正财','偏财','正官','食神','伤官','比肩','劫财','七杀','偏官'):
            for wx in ten_god_wx(day_master, w):
                out.add(wx)
        elif w in GAN_WX:
            out.add(GAN_WX[w])
        elif w in WUXING:
            out.add(w)
    return out

def extract_xi_ji(analysis, day_master):
    """从 analysis 提取喜忌, 分离原断与评注(林注/徐注为旁证级, 不入格局层对标)
    返回: {'xi_wx': [...], 'ji_wx': [...], 'source': '原断'|'混合'|'纯评注'|'无',
           'commentary_xi': [...], 'commentary_ji': [...], 'raw': [原断匹配句],
           'commentary_raw': [评注匹配句]}
    """
    if not analysis:
        return {'xi_wx': [], 'ji_wx': [], 'source': '无', 'raw': [],
                'commentary_xi': [], 'commentary_ji': [], 'commentary_raw': []}

    # 句级语境门控(先于句内正则):
    # 岁运句说的是"运上如何", 不是原局格局喜忌 -> 不作原局喜忌提取
    # 轻重句说的是"某神多重", 不是"某神为忌" -> 交由句内正则按上下文判定
    def _gate(text):
        keep = []
        for s in re.split(r'[。；;！!？?\n]', text):
            s = s.strip()
            if not s:
                continue
            if DAYUN_CTX.search(s):
                keep.append(('yun', s))
            else:
                keep.append(('yuan', s))
        return keep

    def _scan(text):
        """对一段文本跑喜忌关键词, 返回 (xi_wx, ji_wx, raw_hits)
        只扫 'yuan' 句; 'yun' 句的命中不计入原局喜忌(但记录以备岁运域参考)"""
        xi, ji, hits, yun_hits = [], [], [], []
        gated = _gate(text)
        for kind, s in gated:
            for pattern, wx_list, k in XIJIKUANG:
                for m in re.finditer(pattern, s):
                    tgt = yun_hits if kind == 'yun' else hits
                    for w in wx_list:
                        if kind == 'yun':
                            if m.group() not in tgt:
                                tgt.append(m.group())
                        elif k == '喜':
                            if w not in xi:
                                xi.append(w)
                                tgt.append(m.group())
                        else:
                            if w not in ji:
                                ji.append(w)
                                tgt.append(m.group())
        return xi, ji, hits, yun_hits

    # 剥评注: 林注是括号内 "(林注：...)", 徐注是 "【徐注】..." 到下一个八字/原断段为止
    lin_note = re.findall(r'\(\s*林注[：:][^)]*\)', analysis)
    xu_note = re.findall(r'【徐注】.*?(?=(?:甲|乙|丙|丁|戊|己|庚|辛|壬|癸)\s*(?:子|丑|寅|卯|辰|巳|午|未|申|酉|戌|亥)\s*$|(?:甲|乙|丙|丁|戊|己|庚|辛|壬|癸)\s*(?:子|丑|寅|卯|辰|巳|午|未|申|酉|戌|亥)\s*[\u4e00-\u9fa5]|$)', analysis, re.DOTALL)
    yuandu = analysis
    for ln in lin_note:
        yuandu = yuandu.replace(ln, '')
    for xn in xu_note:
        yuandu = yuandu.replace(xn, '')

    has_commentary = bool(lin_note or xu_note)
    if has_commentary and not yuandu.strip():
        source = '纯评注'
    elif has_commentary:
        source = '混合'
    else:
        source = '原断'

    xi_wx, ji_wx, raw_hits, yun_hits = _scan(yuandu)
    # 评注部分的喜忌单独收集(不并入格局层对标, 供调候/病药域参考)
    com_text = '\n'.join(lin_note + xu_note)
    com_xi, com_ji, com_hits, _ = _scan(com_text)

    # v1.7 分域提取: 实现《案例执行方案》§4.2 标准化表未覆盖的句式
    # ("以X…为用/取X为用/X为病/X为药/X为救应"), 每条强制带病域归属
    # 岁运句独立成 SUI_YUN.RE_EVALUATION 层(裁决: 不混入原局层喜忌一致率)
    marked = []
    marked_yun = []
    for s in re.split(r'[。；;！!？?\n]', yuandu):
        s = s.strip()
        if not s:
            continue
        if DAYUN_CTX.search(s):
            for h in extract_marked(s):
                h['clause'] = s[:60]
                h['layer'] = 'SUI_YUN.RE_EVALUATION'
                marked_yun.append(h)
            continue
        for h in extract_marked(s):
            h['clause'] = s[:60]
            h['layer'] = 'ORIGINAL'
            marked.append(h)
    # 十神/干/支 统一标准化为十神名(再由 _std 转五行)
    for h in marked:
        kind, w = h['kind'].split(':', 1)
        h['wx_kind'] = kind
        h['wx_name'] = w
    # 域桶: domain -> {'xi':[...], 'ji':[...]}
    domain_buckets = {}
    for h in marked:
        b = domain_buckets.setdefault(h['domain'], {'xi': [], 'ji': []})
        key = h['wx_kind'] + ':' + h['wx_name']
        tgt = b['xi'] if h['polarity'] == '喜' else b['ji']
        if key not in tgt:
            tgt.append(key)

    return {'xi_wx': xi_wx, 'ji_wx': ji_wx, 'source': source, 'raw': raw_hits,
            'yun_hits': yun_hits, 'marked': marked, 'marked_yun': marked_yun,
            'domain_buckets': domain_buckets,
            'commentary_xi': com_xi, 'commentary_ji': com_ji, 'commentary_raw': com_hits}

def run_engine(bazi_str):
    p = gp(bazi_str)
    f = l0build(p)
    f['pillars'] = p
    try:
        f['wuxing_power'] = build_wuxing_power(p, f)
    except Exception:
        f['wuxing_power'] = {}
    th = build_tian_he(p, f)
    wp = f.get('wuxing_power', {})
    build_ge_cheng(f)
# STEP-DBG-4 (2026-10-03) ti_wx 规则归位: 本路径不调 apply_he_po_ge(破格执行器),
#   故归位直接跟在 build_ge_cheng 之后。破格盘 build_ge_cheng 内各分支已给 ti_wx=[],
#   归位层遇 '(破格)' 会跳过, 不重新赋格体。规则见 ge_jie_layer.normalize_ti_wx 注释
#   (DTS L210 准神 + PZZQ L4652 同向)。
    normalize_ti_wx(f)
    spp = build_special_patterns(p, f, wp, th)
    gc = f.get('ge_cheng')
    # 主链用药裁决层 (喜=主药, 忌=ji_shen)
    hst = {p[k][1]: f['hidden_stems'][k] for k in K}
    pa = build_power_structure(p)
    rc = build_root_classes(p, hst)
    tc = build_tou_cang(f)
    wx = build_wang_xiang(f, f['day_stem'])
    rr = build_root_relations(rc, f['combination_facts'])
    ts = build_two_side(rc, tc, rr)
    bt = build_branch_tiers(p, f)
    net = build_power_network(pa, rc, tc, wx, rr, ts, branch_tier=bt, tian_he=th, facts=f)
    queries = run_queries(net)
    by = build_bingyao_layer(f, queries)
    deb = resolve_primary_bing(f, by['bing_list'])
    zg = resolve_zhuangui(f, deb)
    cli = build_climate_candidates(f)
    yy = resolve_yongyao(f, zg, cli)
    return {
        'ge_cheng': gc,
        'cong_type': spp.get('cong_type'),
        'cong_state': spp.get('cong_state'),
        'zhuanwang': spp.get('zhuanwang'),
        'hua_qi': spp.get('hua_qi'),
        'liangqi': spp.get('liangqi'),
        'yongyao_medicine': (yy.get('primary_medicine') or {}).get('wuxing', ''),
        'yongyao_ji_shen': yy.get('ji_shen', []),
        # [2026-10-01 拓扑补齐 4 键] 干支关系事实层, 原 run_engine 未透传,
        # 导致对标时无法核 L0 冲合结构。现补, 值为 facts 原样透传, 不新增判断。
        # 已 grep 确认: 全仓无 eng/engine_out 遍历, 调用方均按 key 取, 加键不改下游行为。
        'branch_relations': f.get('branch_relations', []),
        'combination_facts': f.get('combination_facts', {}),
        'stem_combination_facts': f.get('stem_combination_facts', {}),
        'target_relation_facts': f.get('target_relation_facts', {}),
    }

def compare(engine_out, xi_ji_extracted, day_master):
    gc = engine_out.get('ge_cheng') or {}
    # 分域(v1.7 §0.3): 格局域 = ge_cheng.xi_wx + po_ge(破格局层); 旺衰域 = yongyao 主药/忌神.
    # 跨域不冲突, 同一五行在两域角色可相反(财格喜财 vs 财多身弱忌财), 故矛盾只在域内判.
    eng_xi_ge = list(gc.get('xi_wx', []))
    yy_med = engine_out.get('yongyao_medicine', '')
    yy_ji = engine_out.get('yongyao_ji_shen', [])
    eng_ji_ge, eng_ji_ys, po_cond = [], list(yy_ji), []
    # 破格条件 → 格局域忌神 (按对照表, 用 ten_god_wx 转)
    # po_ge.match 语义(ge_jie_layer 落盘):
    #   ANY  = required 任一神即破格, 该神本身是忌神 -> 可作格局域忌神
    #   ALL  = required 全部齐备才破格, 是组合条件; 单神可能正是成格喜神(伤官用财) -> 不可作忌
    #   缺失 = forbidden 缺失才破格, 该神是喜神 -> 不参与
    if day_master:
        for pg in gc.get('po_ge', []):
            if pg.get('type') != '组合':
                if pg.get('type') == '缺失':
                    po_cond.append({'type': '缺失', 'forbidden': pg.get('forbidden', [])})
                else:
                    po_cond.append({'type': pg.get('type'), 'cond': pg.get('power_cond') or pg.get('branch_cond') or ''})
                continue
            req = pg.get('required', [])
            if pg.get('match') == 'ALL':
                po_cond.append({'type': '组合ALL', 'required': list(req)})
                continue
            for god in req:
                for w in ten_god_wx(day_master, god):
                    if w not in eng_ji_ge:
                        eng_ji_ge.append(w)
    # 喜: 格局域优先; 格局域无输出时回落旺衰域主药
    eng_xi = eng_xi_ge or ([yy_med] if yy_med else [])
    eng_xi_domain = '格局域' if eng_xi_ge else ('旺衰域' if yy_med else '无')
    eng_ji = sorted(set(eng_ji_ge) | set(eng_ji_ys))
    
    ori_xi = xi_ji_extracted.get('xi_wx', [])
    ori_ji = xi_ji_extracted.get('ji_wx', [])
    
    eng_xi_std = _std(eng_xi, day_master)
    eng_ji_std = _std(eng_ji, day_master)
    ori_xi_std = _std(ori_xi, day_master)
    ori_ji_std = _std(ori_ji, day_master)
    
    if not ori_xi_std and not ori_ji_std:
        status = '原断无喜忌表述'
    elif not eng_xi_std and not eng_ji_std:
        status = '引擎无输出'
    else:
        xi_match = bool(eng_xi_std & ori_xi_std) if ori_xi_std else True
        ji_match = bool(eng_ji_std & ori_ji_std) if ori_ji_std else True
        if xi_match and ji_match:
            status = '一致'
        elif (eng_xi_std & ori_xi_std) or (eng_ji_std & ori_ji_std):
            status = '方向一致粒度不同'
        else:
            status = '不一致'
    
    # ---- 格局域口径(v1.7 §0.3 域前置: 指标只算 GEJU 桶) ----
    # 原断 GEJU 喜忌 来自分域提取器; 引擎 GEJU 喜忌 来自 ge_cheng
    buckets = xi_ji_extracted.get('domain_buckets') or {}
    geju = buckets.get('GEJU') or {'xi': [], 'ji': []}
    ori_xi_ge = _std(geju.get('xi', []), day_master)
    ori_ji_ge = _std(geju.get('ji', []), day_master)
    _over, _miss = [], []
    if not ori_xi_ge and not ori_ji_ge:
        other = sorted(k for k in buckets if k != 'GEJU' and buckets[k])
        status_geju = '原断喜忌非格局域' if other else '原断无喜忌表述'
        if not other:
            status_geju = '原断无喜忌表述'
    elif not eng_xi_ge and not eng_ji_ge:
        status_geju = '引擎无输出'
    else:
        # 裁决(2026-09-30): 加"不一致(多给/漏给/相反)"三子类.
        # 定义必须**可计算**, 否则指标不可复现:
        #   多给 = 引擎喜神 ∩ 引擎自身破格忌神(po_ge match=ANY) ≠ ∅  -> 引擎自相矛盾
        #   相反 = 引擎喜神与原断喜神完全无交集, 且引擎喜神落在自己破格忌神里
        #   漏给 = 原断喜神与引擎喜神完全无交集, 但引擎未自相矛盾
        #   粒度不同 = 有交集但不相等
        # 注意: "原断没提到的喜神"**不算**多给 —— 原断通常只提救应之神这一个焦点,
        #   引擎给该格全部喜神是正常的粒度差(PZ-0078 等 6 条均属此类, 不可误判)
        ex, ej = set(eng_xi_ge), set(eng_ji_ge)
        ox, oj = set(ori_xi_ge), set(ori_ji_ge)
        po_ji = set(eng_ji_ge)            # 引擎自身判定的破格忌神(仅 match=ANY 的才进来)
        self_conflict = ex & po_ji        # 引擎自相矛盾: 喜神同时是破格忌
        hit = bool((ex & ox) or (ej & oj))
        if self_conflict:
            status_geju = '不一致（多给）'
        elif not hit:
            status_geju = '不一致（漏给）' if not (ox or oj) else '不一致（相反）'
        elif (ex & ox) == ox and (ej & oj) == oj and ex == ox and ej == oj:
            status_geju = '一致'
        else:
            status_geju = '方向一致粒度不同'
        _over = sorted(self_conflict)
        _miss = sorted((ox - ex) | (oj - ej)) if not hit else []
    orig_domain = 'GEJU' if (geju.get('xi') or geju.get('ji')) else (
        ','.join(sorted(k for k in buckets if k != 'GEJU' and buckets[k])) or '无')

    xige = _std(eng_xi_ge, day_master)
    jige = _std(eng_ji_ge, day_master)
    jiy  = _std(eng_ji_ys, day_master)
    # 域内矛盾才是引擎错; 跨域重叠是 v1.7 允许的并行(如财格喜财 vs 财多身弱忌财)
    conflict_ge = sorted(xige & jige)
    conflict_ys = sorted(xige & jiy) if eng_xi_domain == '旺衰域' else []
    cross = sorted((xige & jiy) if eng_xi_domain == '格局域' else set())

    # ---- 特殊模式人工复核清单(裁决 2026-09-30 短期方案 b) ----
    # "引擎多给喜神排除项"这类错误, 判据是**原典对照表的排除项**,
    # 而该排除项尚未在引擎建模(无 ji_exclude 字段), 故指标算不出 -> 指标不可见.
    # 本清单单列, **不混入一致率**, 仅供人工复核. 中期建模 ji_exclude 后可自动化.
    manual_review = []
    if gc and ori_xi_ge:
        for wx, why in _ji_exclude_wx(gc.get('ge', ''), day_master):
            if wx in xige and wx not in ori_xi_ge:
                manual_review.append({
                    'kind': '引擎多给喜神排除项',
                    'wuxing': wx,
                    'exclude_reason': why,
                    'note': '指标暂不可见(无 ji_exclude 建模); 不计入一致率',
                })
    return {
        'status': status,
        'engine_xi': sorted(eng_xi_std),
        'engine_ji': sorted(eng_ji_std),
        'original_xi': sorted(ori_xi_std),
        'original_ji': sorted(ori_ji_std),
        'ge': gc.get('ge', '无格'),
        'po_cond': po_cond,
        'xi_domain': eng_xi_domain,
        'status_geju': status_geju,
        'geju_over_given': _over,
        'geju_miss_given': _miss,
        'manual_review': manual_review,
        'orig_domain': orig_domain,
        'orig_xi_geju': sorted(ori_xi_ge),
        'orig_ji_geju': sorted(ori_ji_ge),
        'eng_xi_geju': sorted(eng_xi_ge),
        'eng_ji_geju': sorted(eng_ji_ge),
        'conflict_same_domain': conflict_ge,
        'conflict_cross_domain': cross,
        'conflict_wangshuai': conflict_ys,
    }

def main():
    case_file = Path('p0_v2/case_audit/PZZQ_clean.jsonl')
    records = []
    with open(case_file, 'r', encoding='utf-8-sig') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    
    print(f'加载 {len(records)} 条 PZZQ 案例')
    
    results = []
    status_counts = defaultdict(int)
    geju_counts = defaultdict(int)
    dom_counts = defaultdict(int)

    for i, r in enumerate(records):
        bazi = r.get('bazi', '').replace(' ', '')
        if len(bazi) != 8:
            status_counts['八字格式异常'] += 1
            continue

        dm = r.get('day_master', '')
        analysis = r.get('analysis', '')

        xj = extract_xi_ji(analysis, dm)

        try:
            eng = run_engine(bazi)
        except Exception as e:
            status_counts['引擎崩溃'] += 1
            results.append({
                'case_id': r.get('case_id', ''),
                'bazi': bazi,
                'day_master': dm,
                'error': str(e),
                'status': '引擎崩溃',
            })
            continue

        cmp = compare(eng, xj, dm)
        cmp['case_id'] = r.get('case_id', '')
        cmp['bazi'] = bazi
        cmp['day_master'] = dm
        cmp['xi_source'] = xj.get('source', '')
        cmp['xi_raw'] = xj.get('raw', [])
        cmp['yun_hits'] = xj.get('yun_hits', [])
        cmp['marked'] = [{k: v for k, v in h.items() if k != 'seg'} for h in xj.get('marked', [])]
        cmp['marked_yun'] = [{k: v for k, v in h.items() if k != 'seg'} for h in xj.get('marked_yun', [])]
        cmp['commentary_xi'] = xj.get('commentary_xi', [])
        cmp['commentary_ji'] = xj.get('commentary_ji', [])
        cmp['commentary_raw'] = xj.get('commentary_raw', [])
        cmp['cong_type'] = eng.get('cong_type')
        cmp['cong_state'] = eng.get('cong_state')
        cmp['zhuanwang'] = eng.get('zhuanwang')
        results.append(cmp)
        status_counts[cmp['status']] += 1
        geju_counts[cmp['status_geju']] += 1
        dom_counts[cmp['orig_domain']] += 1

    total = len(records)
    alignable = total - status_counts.get('原断无喜忌表述', 0) - status_counts.get('八字格式异常', 0) - status_counts.get('引擎崩溃', 0)
    alignable = max(alignable, 1)
    xi_rate = status_counts.get('一致', 0) / alignable * 100
    partial_rate = status_counts.get('方向一致粒度不同', 0) / alignable * 100
    mis_rate = status_counts.get('不一致', 0) / alignable * 100

    # 格局域口径(推荐指标): 分母 = 全部案例 减去 原断无喜忌/跨域
    g_base = total - geju_counts.get('原断无喜忌表述', 0) \
                    - geju_counts.get('原断喜忌非格局域', 0) \
                    - status_counts.get('八字格式异常', 0) \
                    - status_counts.get('引擎崩溃', 0)
    g_base = max(g_base, 1)

    print(f'\n=== PZZQ 格局层喜忌对标结果 ===')
    print(f'总案例: {total}')
    print(f'\n[全域口径·历史对照]')
    print(f'  可对标: {alignable}')
    print(f'  一致: {status_counts.get("一致", 0)} ({xi_rate:.1f}%)')
    print(f'  方向一致粒度不同: {status_counts.get("方向一致粒度不同", 0)} ({partial_rate:.1f}%)')
    print(f'  不一致: {status_counts.get("不一致", 0)} ({mis_rate:.1f}%)')
    print(f'  引擎无输出: {status_counts.get("引擎无输出", 0)}')
    print(f'  原断无喜忌表述: {status_counts.get("原断无喜忌表述", 0)}')
    print(f'\n[格局域口径·v1.7 域前置·推荐指标]')
    print(f'  可对标(原断喜忌落在格局域): {g_base}')
    for _k in ('一致', '方向一致粒度不同', '不一致（多给）', '不一致（漏给）',
               '不一致（相反）', '引擎无输出'):
        if geju_counts.get(_k):
            print(f'  {_k}: {geju_counts.get(_k)} ({geju_counts.get(_k)/g_base*100:.1f}%)')
    _mis = sum(geju_counts.get(_k, 0) for _k in
               ('不一致（多给）', '不一致（漏给）', '不一致（相反）'))
    print(f'  不一致(小计): {_mis} ({_mis/g_base*100:.1f}%)')
    print(f'  原断喜忌非格局域(跨域, 不计入): {geju_counts.get("原断喜忌非格局域", 0)}')
    print(f'\n[原断喜忌域分布]')
    for k, v in sorted(dom_counts.items(), key=lambda x: -x[1]):
        print(f'  {k:24s} {v}')
    print(f'\n引擎崩溃: {status_counts.get("引擎崩溃", 0)}')
    print(f'八字格式异常: {status_counts.get("八字格式异常", 0)}')
    
    report = {
        'book': 'PZZQ',
        'total_cases': total,
        'alignable': alignable,
        'status_counts': dict(status_counts),
        'xi_rate': round(xi_rate, 1),
        'partial_rate': round(partial_rate, 1),
        'mis_rate': round(mis_rate, 1),
        'geju_status_counts': dict(geju_counts),
        'geju_alignable': g_base,
        'geju_xi_rate': round(geju_counts.get('一致', 0) / g_base * 100, 1),
        'geju_partial_rate': round(geju_counts.get('方向一致粒度不同', 0) / g_base * 100, 1),
        'geju_mis_rate': round(geju_counts.get('不一致', 0) / g_base * 100, 1),
        'orig_domain_counts': dict(dom_counts),
        'results': results,
    }
    out_json = Path('p0_v2/case_audit/PZZQ_align_report.json')
    with open(out_json, 'w', encoding='utf-8') as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    
    md_lines = ['# PZZQ 格局层喜忌对标报告', '']
    md_lines.append('> 口径二: **格局域口径**(v1.7 §0.3 域前置, 推荐指标) —— 分母只算原断喜忌落在格局域的案例。')
    md_lines.append('> 口径一: 全域口径(历史对照) —— 未做域前置, 混入了调候/病药/五行域案例。')
    md_lines.append('')
    md_lines.append('## 一、格局域口径（推荐指标）')
    md_lines.append('')
    md_lines.append('| 指标 | 值 |')
    md_lines.append('|---|---|')
    md_lines.append(f'| 总案例 | {total} |')
    md_lines.append(f'| 可对标（原断喜忌在格局域） | {g_base} |')
    md_lines.append(f'| 一致 | {geju_counts.get("一致", 0)} ({geju_counts.get("一致", 0)/g_base*100:.1f}%) |')
    md_lines.append(f'| 方向一致粒度不同 | {geju_counts.get("方向一致粒度不同", 0)} ({geju_counts.get("方向一致粒度不同", 0)/g_base*100:.1f}%) |')
    md_lines.append(f'| 不一致 | {geju_counts.get("不一致", 0)} ({geju_counts.get("不一致", 0)/g_base*100:.1f}%) |')
    md_lines.append(f'| 引擎无输出 | {geju_counts.get("引擎无输出", 0)} |')
    md_lines.append(f'| 原断喜忌非格局域（跨域，不计入） | {geju_counts.get("原断喜忌非格局域", 0)} |')
    md_lines.append('')
    md_lines.append('## 二、原断喜忌域分布')
    md_lines.append('')
    md_lines.append('| 域 | 案例数 |')
    md_lines.append('|---|---|')
    for k, v in sorted(dom_counts.items(), key=lambda x: -x[1]):
        md_lines.append(f'| {k} | {v} |')
    md_lines.append('')
    md_lines.append('## 三、全域口径（历史对照）')
    md_lines.append('')
    md_lines.append('| 指标 | 值 |')
    md_lines.append('|---|---|')
    md_lines.append(f'| 可对标 | {alignable} |')
    md_lines.append(f'| 一致 | {status_counts.get("一致", 0)} ({xi_rate:.1f}%) |')
    md_lines.append(f'| 方向一致粒度不同 | {status_counts.get("方向一致粒度不同", 0)} ({partial_rate:.1f}%) |')
    md_lines.append(f'| 不一致 | {status_counts.get("不一致", 0)} ({mis_rate:.1f}%) |')
    md_lines.append(f'| 原断无喜忌表述 | {status_counts.get("原断无喜忌表述", 0)} |')
    md_lines.append(f'| 引擎崩溃 | {status_counts.get("引擎崩溃", 0)} |')
    md_lines.append('')
    md_lines.append('## 四、特殊模式人工复核清单（不计入一致率）')
    md_lines.append('')
    md_lines.append('> 判据为**原典对照表的喜神排除项**（如对照表明言「阳刃用财，格所不喜」），')
    md_lines.append('> 该排除项尚未在引擎建模（无 `ji_exclude` 字段），故一致率指标**算不出**此类错误。')
    md_lines.append('> 本清单单列，仅供人工复核。中期建模 `ji_exclude` 后可自动化。')
    md_lines.append('')
    _mr = [r for r in results if r.get('manual_review')]
    if not _mr:
        md_lines.append('（本轮无命中）')
    else:
        md_lines.append('| case | 引擎格 | 类型 | 五行 | 排除依据 |')
        md_lines.append('|---|---|---|---|---|')
        for r in _mr:
            for h in r['manual_review']:
                md_lines.append('| %s | %s | %s | %s | %s |' % (
                    r.get('case_id'), r.get('ge'), h.get('kind'),
                    h.get('wuxing'), h.get('exclude_reason')))
    md_lines.append('')
    md_lines.append('## 五、格局域不一致明细')
    md_lines.append('')
    for r in results:
        if r.get('status_geju') == '不一致':
            md_lines.append(f"### {r.get('case_id', '')} ({r.get('bazi', '')}, 日主 {r.get('day_master', '')})")
            md_lines.append(f"- 引擎格局域 喜: {r.get('eng_xi_geju', [])} 忌: {r.get('eng_ji_geju', [])} 格: {r.get('ge', '')}")
            md_lines.append(f"- 原断格局域 喜: {r.get('orig_xi_geju', [])} 忌: {r.get('orig_ji_geju', [])}")
            mk = [{'主语': h.get('subj'), '极性': h.get('polarity'), '域': h.get('domain'),
                   '依据': h.get('domain_src'), '句': h.get('clause', '')[:34]} for h in r.get('marked', [])]
            if mk:
                md_lines.append(f"- 提取明细: {mk}")
            md_lines.append('')
    md_lines.append('## 六、全域口径不一致明细')
    md_lines.append('')
    for r in results:
        if r.get('status') == '不一致':
            md_lines.append(f"### {r.get('case_id', '')} ({r.get('bazi', '')}, 日主 {r.get('day_master', '')})")
            md_lines.append(f"- 引擎喜: {r.get('engine_xi', [])} 忌: {r.get('engine_ji', [])} 格: {r.get('ge', '')}")
            md_lines.append(f"- 原断喜: {r.get('original_xi', [])} 忌: {r.get('original_ji', [])} 来源: {r.get('xi_source', '')}")
            md_lines.append(f"- 原始匹配: {r.get('xi_raw', [])}")
            com_xi, com_ji = r.get('commentary_xi', []), r.get('commentary_ji', [])
            if com_xi or com_ji:
                md_lines.append(f"- 评注喜(旁证级, 不入格局对标): {com_xi} 忌: {com_ji} 匹配: {r.get('commentary_raw', [])}")
            md_lines.append('')
    md_path = Path('p0_v2/case_audit/PZZQ_align_report.md')
    with open(md_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(md_lines))
    
    print(f'\n报告写入: {out_json}, {md_path}')

if __name__ == '__main__':
    main()
