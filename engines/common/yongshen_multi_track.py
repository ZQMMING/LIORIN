# -*- coding: utf-8 -*-
"""160-D2 用神四轨并行层 V1.0

四轨独立激活 + 冲突保留 + 多解输出，不强行统一。
轨道: ZPZQ格局轨 / QTBJ调候轨 / SFTK病药轨 / DTS体用轨
渊海子平、三命通会降级为基础事实校验层，不作为独立用神轨道。
不评分/不权重/不裁决，吉凶前端拦截。
"""
from typing import Any, Dict, List, Optional
from spec.yinyang_system import SHENG, KE, SHENG_ME, KE_ME

# 十干作用机制矩阵(合化检查用)
try:
    from engines.common.stem_interaction_matrix import get_he_relation
except ImportError:
    get_he_relation = None

WUXING = '木火土金水'
WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}




WINTER = ('亥','子','丑')
SUMMER = ('巳','午','未')
WANG_TIER = ('旺极','太旺','旺')
SHUAI_TIER = ('衰极','太衰','衰')


def _track_output(track_id, track_name, activated, candidates=None, evidence_grade='CANDIDATE', note=''):
    """统一轨道输出结构"""
    return {
        'track_id': track_id,
        'track_name': track_name,
        'activated': activated,
        'candidates': candidates or [],
        'evidence_grade': evidence_grade,
        'note': note,
    }


def _candidate(element, priority, evidence='', boundary='', stem_element=''):
    """统一候选结构. element=五行级别(向后兼容), stem_element=天干级别(十干升级)"""
    cand = {
        'element': element,
        'priority': priority,
        'evidence': evidence,
        'boundary': boundary,
    }
    if stem_element:
        cand['stem_element'] = stem_element  # 天干级别用神(如癸/戊/丙)
    return cand


# ============================================================
# 轨道1: ZPZQ 格局轨 (子平真诠 - 月令用神，顺逆用)
# ============================================================
def _track_zpzq(pillars, facts, wuxing_power, spectrum, special, climate):
    """格局轨: 月令本气透干且不杂，或月令藏干成格时激活。

    激活条件(保守): 月令本气透干 或 月令参与成格(三合三会/从格/专旺)
    不激活: 月令杂气不透且不成格
    """
    dm = facts['day_stem']
    dmw = WX[dm]
    mz = facts['month_branch']
    wpd = (wuxing_power or {}).get('wuxing_power', {})

    # 月令本气五行 (从facts获取hidden_stems)
    hidden_stems = facts.get('hidden_stems', {})
    month_hidden = hidden_stems.get('month', [])
    month_benqi = month_hidden[0] if month_hidden else None
    month_benqi_wx = WX.get(month_benqi) if month_benqi else None

    # 月令本气是否透干
    stems = [pillars[k][0] for k in ('year','month','day','hour')]
    benqi_tou = month_benqi in stems if month_benqi else False

    # 是否成格(从格/专旺/化气/两气)
    has_pattern = bool(special.get('cong_type') or special.get('zhuanwang')
                       or special.get('hua_qi') or special.get('liangqi'))

    # ★ V7.113 激活条件: 【主链已落格】或【成格】—— 不再要求"月令本气透干"
    #   原典 PZZQ L1113「用神专寻月令」: 月令本气即定格局, 不要求透干
    #   (同 V7.78 正官格 / V7.79 七煞格 之同类修正).
    #   原读法(须月令本气透干)致【月令不透干而成格】之盘(如 癸亥壬戌乙未壬午: 戌月戊土不透干,
    #   主链已判财格)在本轨恒不激活, 与主链 ge_cheng 两套格局判定相互矛盾.
    _gc_main = (facts.get('ge_cheng') or {}) if isinstance(facts, dict) else {}
    _ge_main = _gc_main.get('ge') or ''
    _shape_main = _gc_main.get('shape') or ''
    _ge_formed = bool(_ge_main)
    activated = _ge_formed or has_pattern or benqi_tou

    if not activated:
        return _track_output('ZPZQ', '格局轨', False, note='月令未成格且无成格结构')

    candidates = []
    # ★ V7.113 格局用神优先取【主链形态】所定的格神(形态单一数据源, V7.51);
    #   无形态时退回"月令本气对应十神"并标注 LEGACY(非原典口径, 勿据以立论).
    _shape_yongshen = {
        '用官': '官杀', '用官带伤食': '官杀',
        '用财': '财星', '用财印': '财星', '用财印同官格': '财星',
        '佩印': '印星', '旺生官': '官杀',
        '用食印': '食伤', '用食生': '食伤', '用食伤': '食伤',
        '生财': '财星', '食制': '食伤',
        '同官格': '官杀', '同财格': '财星', '同煞格': '官杀',
    }.get(_shape_main, '')
    if _shape_yongshen:
        _yx = {'官杀': KE_ME.get(dmw), '财星': KE.get(dmw), '印星': SHENG_ME.get(dmw),
               '食伤': SHENG.get(dmw)}.get(_shape_yongshen, '')
        if _yx:
            candidates.append(_candidate(
                _yx, 1,
                evidence=f'子平真诠: 格局用神专求月令, {_ge_main}·形态「{_shape_main}」以'
                         f'{_shape_yongshen}为用(PZZQ L1113/L3212/L1142-1143)',
                boundary='形态用神; 喜忌随形态与身轻身重而异(取运章), 不可与调候/病药混为总用神',
                stem_element=''))
            return _track_output('ZPZQ', '格局轨', True, candidates, 'DIRECT',
                                 note=f'主链格局={_ge_main}·形态「{_shape_main}」; 用神取形态所定格神')
    if month_benqi_wx:
        # 月令本气五行 vs 日主的十神关系
        if month_benqi_wx == dmw:
            tg_name = '比劫'
        elif SHENG[month_benqi_wx] == dmw:
            tg_name = '印星'
        elif SHENG[dmw] == month_benqi_wx:
            tg_name = '食伤'
        elif KE[dmw] == month_benqi_wx:
            tg_name = '财星'
        elif KE[month_benqi_wx] == dmw:
            tg_name = '官杀'
        else:
            tg_name = '未知'

        cand1 = _candidate(
            month_benqi_wx, 1,
            evidence=f'子平真诠: 八字用神专求月令，月令本气{month_benqi}({tg_name})为格神',
            boundary=f'顺用逆用视格神性质({tg_name})而定，需配合相神成败救应',
            stem_element=month_benqi  # 天干级别: 月令本气天干(如甲/丙/戊)
        )
        candidates.append(cand1)

    # 如果有特殊格局，格神可能不同
    if special.get('zhuanwang'):
        zw = special['zhuanwang']
        # 专旺格用神 = 食伤泄秀 或 官杀(逆用)
        # 十干细分: 同阴阳为食神, 异阴阳为伤官
        shi_wx = SHENG[dmw]
        shi_sd = wpd.get(shi_wx, {}).get('stem_detail', {}) if wpd else {}
        dm_yinyang = '阳' if dm in '甲丙戊庚壬' else '阴'
        if dm_yinyang == '阳':
            shi_stem = shi_sd.get('yang', {}).get('stem', '')  # 阳干食伤=食神(同阳)
            shi_type = '食神'
        else:
            shi_stem = shi_sd.get('yin', {}).get('stem', '')  # 阴干食伤=食神(同阴)
            shi_type = '食神'
        cand2 = _candidate(
            shi_wx, 2,
            evidence=f'专旺格({zw}): 顺用食伤泄秀，首选{shi_stem}({shi_type})' if shi_stem else f'专旺格({zw}): 顺用食伤泄秀',
            boundary='专旺格顺逆用视官杀财有气与否；食神泄秀纯和，伤官泄秀傲气',
            stem_element=shi_stem  # 天干级别: 首选食神天干
        )
        candidates.append(cand2)

    grade = 'DIRECT' if benqi_tou else 'INFERRED'
    return _track_output('ZPZQ', '格局轨', True, candidates, grade,
                         note=f'月令{mz}本气{month_benqi}，{"透干" if benqi_tou else "未透"}，{"成格" if has_pattern else "未成格"}')


# ============================================================
# 轨道2: QTBJ 调候轨 (穷通宝鉴 - 气候所需)
# ============================================================
def _track_qtbj(pillars, facts, wuxing_power, spectrum, special, climate):
    """调候轨: 生于亥子丑/巳午未且调候为急时激活。

    激活条件(保守): 月支在冬夏(亥子丑/巳午未)
    不激活: 春秋月(寅卯辰/申酉戌)调候不急
    """
    mz = facts['month_branch']
    activated = mz in WINTER or mz in SUMMER

    if not activated:
        return _track_output('QTBJ', '调候轨', False, note=f'月令{mz}非冬夏，调候不急')

    # 从climate模块获取调候候选, 若为空则fallback直接调用build_climate_candidates
    cands_raw = (climate or {}).get('climate_candidates', [])
    if not cands_raw:
        try:
            from engines.common.qtbj_climate_candidates import build_climate_candidates
            _climate_result = build_climate_candidates(facts)
            if isinstance(_climate_result, dict):
                cands_raw = _climate_result.get('climate_candidates', [])
        except Exception:
            pass
    candidates = []
    for i, c in enumerate(cands_raw):
        stem = c.get('stem', '')
        wx = WX.get(stem, stem)
        if wx in WUXING:
            _cand = _candidate(
                wx, i + 1,
                evidence=f'穷通宝鉴: {facts["day_stem"]}生{mz}月调候用{stem}，原文次序第{i+1}',
                boundary='调候为急，权而用之；与格局用神互参，不混为总用神'
            )
            _cand['stem_element'] = stem  # 调候天干级别输出
            candidates.append(_cand)

    if not candidates:
        return _track_output('QTBJ', '调候轨', True, [], 'CANDIDATE',
                             note=f'{facts["day_stem"]}{mz}月调候候选未录入')

    return _track_output('QTBJ', '调候轨', True, candidates, 'DIRECT',
                         note=f'{mz}月{"冬令寒" if mz in WINTER else "夏令燥"}，调候为急')


# ============================================================
# 轨道3: SFTK 病药轨 (神峰通考 - 去病之药)
# ============================================================
def _track_sftk(pillars, facts, wuxing_power, spectrum, special, climate, bingyao=None):
    """病药轨: 存在明显病时激活(病药层已识别)。

    激活条件(保守): bingyao层识别到至少1个病
    不激活: 无病 或 bingyao层未构建
    药 = 克病的五行 (原著: 有病方为贵，去病之药为用)
    """
    if not bingyao:
        return _track_output('SFTK', '病药轨', False, note='病药层未构建')

    bing_list = bingyao.get('bing_list', []) or []

    if not bing_list:
        return _track_output('SFTK', '病药轨', False, note='病药层未识别到病')

    candidates = []
    # 获取十干级力量(用于天干细分)
    wp_data = wuxing_power.get('wuxing_power', wuxing_power) if isinstance(wuxing_power, dict) else {}
    for i, b in enumerate(bing_list[:5]):  # 最多取5个病
        bing_name = b.get('name', '')
        bing_id = b.get('bing_id', '')
        # 从病名/ID中推断病的五行
        bing_wx = _infer_bing_wuxing(bing_id, bing_name, facts)
        if bing_wx and bing_wx in WUXING:
            # ★ V7.114 药方取【病药层日主动态表】(单一数据源, V7.106)——
            #   原典 SFTK L129 病药配对逐病类而异, 非"药=克病五行"之单一简化式:
            #     财多身弱(病=财)->药=印比(帮身任财, 非克病); 印多埋子(病=印)->药=财(破印)+比劫(扶印);
            #     比劫夺财(病=比劫)->药=官杀(制劫护财); 杀重身轻(病=杀)->药=食伤(制)+印(化).
            #   旧式 yao_wx=KE_ME[bing_wx](药=克病)于"病=财"之盘误给官杀为药.
            _yao_list = []
            try:
                from engines.common.bingyao_layer import _bing_yao_map as _bym
                _dm_wx_sftk = WX.get(facts.get('day_stem'), '')
                _yao_list = [w for w in (_bym(_dm_wx_sftk).get(bing_id) or []) if w]
            except Exception:
                _yao_list = []
            _ke_yao = KE_ME.get(bing_wx, '')
            if _ke_yao and _ke_yao in _yao_list:
                yao_wx = _ke_yao          # 药方含克病一路(制/破), 以之为首选
            elif _yao_list:
                yao_wx = _yao_list[0]     # 否则取药方首位(帮身/扶印/制杀等)
            else:
                yao_wx = _ke_yao          # 无表项, 退回克病(旧口径)
            # 十干细分: 区分病的阳干/阴干力量, 确定主力病干
            # 原典: 壬水冲奔泛滥=病, 癸水渗透滋润=药; 同一五行阴阳干作用机制完全不同
            bing_sd = wp_data.get(bing_wx, {}).get('stem_detail', {}) if wp_data else {}
            bing_yang = bing_sd.get('yang', {})
            bing_yin = bing_sd.get('yin', {})
            bing_yang_gan = bing_yang.get('stem', '')
            bing_yin_gan = bing_yin.get('stem', '')
            bing_yang_total = bing_yang.get('total', 0)
            bing_yin_total = bing_yin.get('total', 0)
            # 确定主力病干(力量较大者)
            if bing_yang_total >= bing_yin_total and bing_yang_total > 0:
                main_bing_gan = bing_yang_gan
                main_bing_type = '阳干'
            elif bing_yin_total > 0:
                main_bing_gan = bing_yin_gan
                main_bing_type = '阴干'
            else:
                main_bing_gan = ''
                main_bing_type = ''
            # 药的天干: 阳干病用阳干药(阳克阳力大), 阴干病用阴干药(阴克阴力大)
            # 原典: 戊土克壬水(阳克阳), 己土克癸水(阴克阴)
            # 边界: 若病干与药干有天干五合, 则克变为合绊, 需降级并优先选另一阴阳药干
            yao_sd = wp_data.get(yao_wx, {}).get('stem_detail', {}) if wp_data else {}
            yao_yang_gan = yao_sd.get('yang', {}).get('stem', '')
            yao_yin_gan = yao_sd.get('yin', {}).get('stem', '')
            yao_yang_total = yao_sd.get('yang', {}).get('total', 0)
            yao_yin_total = yao_sd.get('yin', {}).get('total', 0)
            he_degraded = False
            he_relation_info = ''
            if main_bing_type == '阳干':
                # 阳干病首选阳干药(同气相克力大), 但必须力量>0才算存在
                if yao_yang_total > 0:
                    main_yao_gan = yao_yang_gan
                elif yao_yin_total > 0:
                    # 阳干药不存在, 替代选阴干药, 并检查合化
                    main_yao_gan = yao_yin_gan
                    if main_bing_gan and get_he_relation:
                        he = get_he_relation(main_bing_gan, main_yao_gan)
                        if he:
                            he_degraded = True
                            he_relation_info = f'阳干药不存在(力{yao_yang_total}), 替代选阴干药{main_yao_gan}(力{yao_yin_total}), 但{main_bing_gan}{main_yao_gan}合({he.get("he_name","")})化{he.get("huashen","")}, 克变为合绊降级'
                else:
                    main_yao_gan = ''
            elif main_bing_type == '阴干':
                # 阴干病首选阴干药(同气相克力大), 但必须力量>0才算存在
                if yao_yin_total > 0:
                    main_yao_gan = yao_yin_gan
                elif yao_yang_total > 0:
                    # 阴干药不存在, 替代选阳干药, 并检查合化
                    main_yao_gan = yao_yang_gan
                    if main_bing_gan and get_he_relation:
                        he = get_he_relation(main_bing_gan, main_yao_gan)
                        if he:
                            he_degraded = True
                            he_relation_info = f'阴干药不存在(力{yao_yin_total}), 替代选阳干药{main_yao_gan}(力{yao_yang_total}), 但{main_bing_gan}{main_yao_gan}合({he.get("he_name","")})化{he.get("huashen","")}, 克变为合绊降级'
                else:
                    main_yao_gan = ''
            else:
                main_yao_gan = ''
            # 构建evidence, 包含天干细分信息
            if main_bing_gan and main_yao_gan:
                he_note = f'，合化边界: {he_relation_info}' if he_degraded else ''
                force_note = '同气相克力大' if not he_degraded else '合绊降级后选干'
                evidence = (f'神峰通考: 有病方为贵，病在{bing_name}({bing_wx})，'
                          f'主力病干={main_bing_gan}({main_bing_type},力{bing_yang_total if main_bing_type=="阳干" else bing_yin_total})，'
                          f'药在{yao_wx}(病药层日主动态表; 药方多路: {"/".join(_yao_list) if _yao_list else yao_wx})，首选药干={main_yao_gan}({force_note}){he_note}')
                stem_detail = {
                    'bing_main_gan': main_bing_gan,
                    'bing_main_type': main_bing_type,
                    'bing_yang_total': bing_yang_total,
                    'bing_yin_total': bing_yin_total,
                    'yao_main_gan': main_yao_gan,
                    'he_degraded': he_degraded,
                    'he_relation': he_relation_info,
                }
            else:
                evidence = (f'神峰通考: 有病方为贵，病在{bing_name}({bing_wx})，'
                           f'药在{yao_wx}(病药层日主动态表; 药方多路: {"/".join(_yao_list) if _yao_list else yao_wx})')
                stem_detail = {}
            cand = _candidate(
                yao_wx, i + 1,
                evidence=evidence,
                boundary=f'药需得力方效；病轻药重/病重药轻皆非所宜；十干细分: {main_bing_gan or "未明确"}病/{main_yao_gan or "未明确"}药' + (f'；合化边界: {he_relation_info}' if he_degraded else '')
            )
            if stem_detail:
                cand['stem_detail'] = stem_detail
                yao_gan = stem_detail.get('yao_main_gan', '')
                if yao_gan:
                    cand['stem_element'] = yao_gan  # 天干级别: 首选药干
            candidates.append(cand)

    if not candidates:
        return _track_output('SFTK', '病药轨', True, [], 'CANDIDATE',
                             note=f'识别到{len(bing_list)}个病但药神未明确')

    # 按element去重(多病同药时保留优先级最高的), 保持原顺序
    seen = set()
    unique = []
    for c in candidates:
        el = c.get('element')
        if el not in seen:
            seen.add(el)
            unique.append(c)
    candidates = unique

    return _track_output('SFTK', '病药轨', True, candidates, 'DIRECT',
                         note=f'识别到{len(bing_list)}个病: {[b.get("name","") for b in bing_list[:5]]}')


def _infer_bing_wuxing(bing_id, bing_name, facts):
    """从病ID/名称推断病的五行。"""
    dmw = WX.get(facts.get('day_stem', ''), '')
    # 财多身弱: 病=财(克日主的五行)
    if 'CAI_DUO' in bing_id or '财多' in bing_name:
        return KE.get(dmw)
    # 杀重身轻: 病=官杀(克日主的五行)
    if 'SHA_ZHONG' in bing_id or '杀重' in bing_name or '煞重' in bing_name:
        return KE.get(dmw)
    # 伤官见官: 病=官(克日主的五行)
    if 'SHANGGUAN' in bing_id or '伤官' in bing_name:
        return KE.get(dmw)
    # 枭神夺食: 病=印(生日主的五行)
    if 'XIAO_SHEN' in bing_id or '枭神' in bing_name or '枭印' in bing_name:
        return [x for x in WUXING if SHENG[x] == dmw][0] if dmw else None
    # 印多埋子/母多灭子: 病=印(生日主的五行), 药=财(克印)
    if 'YIN_DUO' in bing_id or '印多' in bing_name or '母多灭子' in bing_name or '土多金埋' in bing_name:
        return [x for x in WUXING if SHENG[x] == dmw][0] if dmw else None
    # 比劫夺财: 病=比劫(日主同类)
    if 'BIJIE' in bing_id or '比劫' in bing_name or '劫财' in bing_name:
        return dmw
    # 默认: 从病名中找五行
    for wx in WUXING:
        if wx in bing_name:
            return wx
    return None


# ============================================================
# 轨道4: DTS 体用轨 (滴天髓 - 扶抑得其宜)
# ============================================================
def _track_dts(pillars, facts, wuxing_power, spectrum, special, climate):
    """体用轨: 日主明显偏离中和时激活。

    激活条件(布尔+枚举, 不依赖ratio):
      旺局: qiang_ruo.has_heavy_root 且 (得令 或 印比透干>=2)
      衰局: qiang_ruo.root_class==NONE 且 (失令 或 食伤财官透干>=2)
      中和: 不满足以上, 全五行候选
    原spectrum tier保留为LEGACY_REFERENCE
    """
    dm = facts['day_stem']
    dmw = WX[dm]

    # ★ V7.110 读取【结构轴】(build_power_structure 的实际结构; 旧读键 'wang_shuai'/'qiang_ruo'/'spectrum'
    #   均不存在 -> in_season 恒 False、root_class 恒 'NONE' -> is_shuai_ju 恒 True -> 全盘皆判"衰局",
    #   DTS L215/L235「旺则抑之」分支(官杀/食伤)从未生效, 且文案恒写"日主None").
    #   现读 seasonal_axis(得令) / root_axis(根气) 两结构轴, 依 AGENTS.md 公理二只组织结构,
    #   不造"身强/身弱"单极布尔(沿用「旺局/衰局/中和」三态表述).
    _sp = spectrum if isinstance(spectrum, dict) else {}
    _sea = _sp.get('seasonal_axis') or {}
    _root_ax = _sp.get('root_axis') or {}
    in_season = bool(_sea.get('in_season'))
    root_class = _root_ax.get('root_weight_class') or 'NONE'
    _rwc = _root_ax.get('per_pillar') or {}
    # 根气轻重: per_pillar 之类字段键为 'class'(非 'root_class'); HEAVY*=重根, LIGHT*=有根
    has_heavy = any(str((v or {}).get('class') or '').startswith('HEAVY')
                    for v in _rwc.values() if isinstance(v, dict))
    has_root = has_heavy or any(str((v or {}).get('class') or '').startswith('LIGHT')
                                for v in _rwc.values() if isinstance(v, dict))
    # 党众计数: support/drain/control 各组为 {十神名: {stem_present, stem_count, root_present,...}},
    #   故计数取各组 stem_count 之和(印比=生扶, 食伤财=泄, 官杀=克)
    def _grp_count(_g):
        _t = 0
        for _v in (_g or {}).values():
            if isinstance(_v, dict):
                _t += int(_v.get('stem_count') or 0)
        return _t
    _sg = _sp.get('support_group') or {}
    _dg = _sp.get('drain_group') or {}
    _cg = _sp.get('control_group') or {}
    support_n = _grp_count(_sg)
    drain_n = _grp_count(_dg)
    oppose_n = _grp_count(_cg) + drain_n
    if not support_n:
        support_n = sum(1 for _k in ('year', 'month', 'day', 'hour')
                        if _k in _rwc and str((_rwc.get(_k) or {}).get('class') or '').startswith('HEAVY'))
    # 文案档位(结构三态, 非身强弱)
    legacy_tier = '旺局' if (has_heavy and (in_season or support_n >= 2)) else (
        '衰局' if (not has_root and support_n == 0 and (not in_season)) else '中和')

    # 旺局/衰局判断 (布尔+枚举组合, 不依赖ratio)
    # ★ V7.112 衰局要件补【无生扶党众】: 原典 PZZQ L799「失令为衰; 若比劫印绶重叠, 年日时又通根,
    #   则失令而不弱」/ L762「秋木虽弱, 木根深而木亦强」—— 失令而有印比党众者不得判衰,
    #   否则轨内只出"宜扶"候选, 抹去原典"失令而不弱"之别.
    is_wang_ju = has_heavy and (in_season or support_n >= 2)
    is_shuai_ju = (not has_root) and (support_n == 0) and (not in_season)

    # 中和: 不满足旺局也不满足衰局
    if not is_wang_ju and not is_shuai_ju:
        all_candidates = []
        for i, wx in enumerate(WUXING):
            all_candidates.append(_candidate(
                wx, i + 1,
                evidence=f'日主中和(得令={in_season},根={root_class},印比={support_n},克泄={oppose_n})，用神不明确，{wx}为候选之一',
                boundary='中和需配合格局/调候/病药综合判断；不单独裁决'
            ))
        return _track_output('DTS', '体用轨', True, all_candidates, 'CANDIDATE',
                             note=f'日主中和(结构枚举: 得令={in_season}, 根={root_class}, 印比={support_n}, 克泄={oppose_n}), 全五行候选(需配合其他轨道综合判断)')

    activated = is_wang_ju or is_shuai_ju

    if not activated:
        return _track_output('DTS', '体用轨', False,
                             note=f'日主状态不明显偏离中和(结构枚举: 得令={in_season}, 根={root_class}, 印比={support_n}, 克泄={oppose_n})')

    candidates = []
    if is_wang_ju:
        # 旺则抑: 克(官杀=KE_ME克我者) 或 泄(食伤=SHENG我生者)
        guan_wx = KE_ME.get(dmw)  # 克日主 = 官杀 (KE_ME是克我的五行)
        shi_wx = SHENG[dmw]  # 日主生 = 食伤
        wp_data = wuxing_power.get('wuxing_power', wuxing_power) if isinstance(wuxing_power, dict) else {}
        # 十干细分: 官杀区分阳杀(七杀/偏官)和阴官(正官)
        # 原典: 同阴阳为七杀(偏官), 异阴阳为正官; 七杀力猛需制, 正官力纯需护
        # 如甲木日主: 庚金=七杀(同阳), 辛金=正官(异阴阳)
        guan_sd = wp_data.get(guan_wx, {}).get('stem_detail', {}) if wp_data else {}
        dm_yinyang = '阳' if dm in '甲丙戊庚壬' else '阴'
        # 阳杀=与日主同阴阳的克我者, 阴官=与日主异阴阳的克我者
        if dm_yinyang == '阳':
            yang_guan = guan_sd.get('yang', {})  # 阳干官杀=七杀(同阳)
            yin_guan = guan_sd.get('yin', {})    # 阴干官杀=正官(异阴阳)
            yang_guan_type = '七杀(偏官)'
            yin_guan_type = '正官'
        else:
            yang_guan = guan_sd.get('yang', {})  # 阳干官杀=正官(异阴阳)
            yin_guan = guan_sd.get('yin', {})    # 阴干官杀=七杀(同阴)
            yang_guan_type = '正官'
            yin_guan_type = '七杀(偏官)'
        yang_guan_gan = yang_guan.get('stem', '')
        yin_guan_gan = yin_guan.get('stem', '')
        yang_guan_total = yang_guan.get('total', 0)
        yin_guan_total = yin_guan.get('total', 0)
        # 确定主力官杀干
        if yang_guan_total >= yin_guan_total and yang_guan_total > 0:
            main_guan_gan = yang_guan_gan
            main_guan_type = yang_guan_type
        elif yin_guan_total > 0:
            main_guan_gan = yin_guan_gan
            main_guan_type = yin_guan_type
        else:
            main_guan_gan = ''
            main_guan_type = ''
        guan_stem_desc = ''
        if main_guan_gan:
            guan_stem_desc = f'主力官杀干={main_guan_gan}({main_guan_type},力{yang_guan_total if main_guan_type==yang_guan_type else yin_guan_total})，阳{yang_guan_gan}({yang_guan_type})力{yang_guan_total}/阴{yin_guan_gan}({yin_guan_type})力{yin_guan_total}'
        # 十干细分: 食伤区分阳食(食神)和阴伤(伤官)
        # 原典: 同阴阳为食神, 异阴阳为伤官; 食神泄秀纯和, 伤官泄秀傲气
        shi_sd = wp_data.get(shi_wx, {}).get('stem_detail', {}) if wp_data else {}
        if dm_yinyang == '阳':
            yang_shi = shi_sd.get('yang', {})  # 阳干食伤=食神(同阳)
            yin_shi = shi_sd.get('yin', {})    # 阴干食伤=伤官(异阴阳)
            yang_shi_type = '食神'
            yin_shi_type = '伤官'
        else:
            yang_shi = shi_sd.get('yang', {})  # 阳干食伤=伤官(异阴阳)
            yin_shi = shi_sd.get('yin', {})    # 阴干食伤=食神(同阴)
            yang_shi_type = '伤官'
            yin_shi_type = '食神'
        yang_shi_gan = yang_shi.get('stem', '')
        yin_shi_gan = yin_shi.get('stem', '')
        yang_shi_total = yang_shi.get('total', 0)
        yin_shi_total = yin_shi.get('total', 0)
        if yang_shi_total >= yin_shi_total and yang_shi_total > 0:
            main_shi_gan = yang_shi_gan
            main_shi_type = yang_shi_type
        elif yin_shi_total > 0:
            main_shi_gan = yin_shi_gan
            main_shi_type = yin_shi_type
        else:
            main_shi_gan = ''
            main_shi_type = ''
        shi_stem_desc = ''
        if main_shi_gan:
            shi_stem_desc = f'主力食伤干={main_shi_gan}({main_shi_type},力{yang_shi_total if main_shi_type==yang_shi_type else yin_shi_total})，阳{yang_shi_gan}({yang_shi_type})力{yang_shi_total}/阴{yin_shi_gan}({yin_shi_type})力{yin_shi_total}'
        # 官杀候选(带天干细分)
        guan_cand = _candidate(
            guan_wx, 1,
            evidence=f'滴天髓: 旺则抑之，{legacy_tier}用官杀({guan_wx})克身。{guan_stem_desc}',
            boundary='旺极宜泄不宜克；太旺/旺可克可泄，视结构而定；七杀力猛需食伤制，正官力纯需财生'
        )
        if main_guan_gan:
            guan_cand['stem_detail'] = {
                'main_guan_gan': main_guan_gan,
                'main_guan_type': main_guan_type,
                'yang_guan_total': yang_guan_total,
                'yin_guan_total': yin_guan_total,
            }
            # 旺则抑用官杀: 七杀(同阴阳)力猛优先, 正官(异阴阳)力纯次之
            guan_cand['stem_element'] = yang_guan_gan if yang_guan_total > 0 else main_guan_gan
        candidates.append(guan_cand)
        # 食伤候选(带天干细分)
        shi_cand = _candidate(
            shi_wx, 2,
            evidence=f'滴天髓: 旺则泄之，{legacy_tier}用食伤({shi_wx})泄秀。{shi_stem_desc}',
            boundary='泄秀需食伤得地有源；旺极尤宜泄；食神泄秀纯和，伤官泄秀傲气需配印'
        )
        if main_shi_gan:
            shi_cand['stem_detail'] = {
                'main_shi_gan': main_shi_gan,
                'main_shi_type': main_shi_type,
                'yang_shi_total': yang_shi_total,
                'yin_shi_total': yin_shi_total,
            }
            # 旺则泄用食伤: 食神(同阴阳)纯和优先, 伤官(异阴阳)傲气次之
            shi_cand['stem_element'] = yang_shi_gan if yang_shi_total > 0 else main_shi_gan
        candidates.append(shi_cand)
        # 第三候选: 印(生) - 仅日主虚嫩/根轻时适用(如丙火寅月火虚)
        # 原典: 旺而虚嫩仍需印生身; 但普通身旺/旺极印为忌神, 不输出
        yin_wx = SHENG_ME.get(dmw)
        dm_power_p3 = wp_data.get(dmw, {}) if wp_data else {}
        dm_heavy_p3 = dm_power_p3.get('ben_n', 0)
        dm_light_p3 = dm_power_p3.get('zhong_n', 0) + dm_power_p3.get('yu_n', 0)
        dm_xunen = (dm_heavy_p3 == 0 and dm_light_p3 <= 1)  # 无根或仅一轻根=虚嫩
        if yin_wx and yin_wx != guan_wx and yin_wx != shi_wx and dm_xunen:
            candidates.append(_candidate(
                yin_wx, 3,
                evidence=f'滴天髓: 旺而虚嫩仍需印({yin_wx})生身(日主根虚浮)',
                boundary='仅日主虚嫩/印源不足时适用；普通身旺/旺极印为忌'
            ))
        # 第四候选: 财(我克) - 仅身旺财有根时适用(身旺任财)
        cai_wx = KE.get(dmw)
        cai_power = wp_data.get(cai_wx, {}) if wp_data else {}
        cai_has_root = (cai_power.get('ben_n', 0) + cai_power.get('zhong_n', 0) + cai_power.get('yu_n', 0)) >= 1
        if cai_wx and cai_wx not in [guan_wx, shi_wx, yin_wx] and cai_has_root:
            candidates.append(_candidate(
                cai_wx, 4,
                evidence=f'渊海子平/子平真诠: 身旺任财({cai_wx})，身强财星有根可用',
                boundary='仅身旺财有根时适用；财多身弱/财无根不宜'
            ))
        # 第五候选: 比劫(日主同类) - 仅专旺格/气势极端(V7.115「太旺/太衰」)时适用
        bi_wx = dmw
        bi_power = wp_data.get(bi_wx, {}) if wp_data else {}
        bi_ben = bi_power.get('ben_n', 0) + bi_power.get('zhong_n', 0)
        # 专旺/太旺气势: 比劫本气>=2 且 官杀/食伤/财星均无力(须无克泄耗)
        guan_power_p5 = wp_data.get(guan_wx, {}) if wp_data else {}
        shi_power_p5 = wp_data.get(shi_wx, {}) if wp_data else {}
        cai_power_p5 = wp_data.get(cai_wx, {}) if wp_data else {}
        guan_weak_p5 = (guan_power_p5.get('ben_n', 0) + guan_power_p5.get('zhong_n', 0)) == 0
        shi_weak_p5 = (shi_power_p5.get('ben_n', 0) + shi_power_p5.get('zhong_n', 0) + shi_power_p5.get('stem_n', 0)) == 0
        cai_weak_p5 = (cai_power_p5.get('ben_n', 0) + cai_power_p5.get('zhong_n', 0) + cai_power_p5.get('stem_n', 0)) == 0
        is_congqiang = (bi_ben >= 2 and guan_weak_p5 and shi_weak_p5 and cai_weak_p5)
        if bi_wx and bi_wx not in [guan_wx, shi_wx, yin_wx, cai_wx] and is_congqiang:
            candidates.append(_candidate(
                bi_wx, 5,
                evidence=f'滴天髓/子平真诠: 专旺格/太旺气势用比劫({bi_wx})，比劫成势({bi_ben}个)官杀无力',
                boundary='仅比劫成势/专旺(太旺)时适用；普通身旺比劫为忌'
            ))
    elif is_shuai_ju:
        # 衰则扶: 生(印) 或 助(比劫)
        # 原典修正: 印星过旺时(水多木浮/母多灭子), 第一候选改为财星(克印)
        # 依据: 滴天髓"水多木浮，土克水则生木"; 穷通宝鉴"木枯用水，水多用戊"
        yin_wx = SHENG_ME_WX = [x for x in WUXING if SHENG[x] == dmw][0]
        bi_wx = dmw
        cai_wx = KE.get(dmw)
        # 印星力量分级: L1偏旺(标注注意, 印星降级但不排除) / L2过旺(水泛木浮, 首选财星制印)
        # 原典校正: 不能把"五行数量多"直接等同于"成灾", 需区分临界状态
        # L2条件: 透干>=3 + 地支合印局 或 本气>=2 + 日主根虚浮(无根或仅余气)
        # L1条件: 透干>=3 或 本气>=1, 但未达L2
        wp_data = wuxing_power.get('wuxing_power', wuxing_power) if isinstance(wuxing_power, dict) else {}
        yin_power = wp_data.get(yin_wx, {}) if wp_data else {}
        yin_stem_count = yin_power.get('stem_n', 0)
        yin_ben_zhong = yin_power.get('ben_n', 0) + yin_power.get('zhong_n', 0)
        # 日主根气: 判断是否虚浮
        dm_power = wp_data.get(dmw, {}) if wp_data else {}
        dm_heavy_root = dm_power.get('ben_n', 0)  # 重根(本气)
        dm_light_root = dm_power.get('zhong_n', 0) + dm_power.get('yu_n', 0)  # 轻根(中气余气)
        dm_root_floating = (dm_heavy_root == 0 and dm_light_root <= 1)  # 无根或仅一个轻根=虚浮
        # 检查是否有印局(三合/三会印局) - 通过ju_n判断
        yin_ju = yin_power.get('ju_n', 0)
        # L2: 印星过旺/水泛木浮
        yin_L2 = ((yin_stem_count >= 3 and yin_ju >= 1) or
                  (yin_ben_zhong >= 2 and dm_root_floating))
        # L1: 印星偏旺(临界状态)
        yin_L1 = (yin_stem_count >= 3 or yin_ben_zhong >= 1) and not yin_L2

        # 十干细分: 印星区分阳印(偏印/枭神)和阴印(正印)
        # 原典: 阳印过旺=枭神夺食, 阴印过旺=母多灭子, 机制不同
        # 如乙木日主: 壬水=阳印(偏印/枭神), 癸水=阴印(正印)
        yin_sd = yin_power.get('stem_detail', {})
        yin_yang = yin_sd.get('yang', {})
        yin_yin = yin_sd.get('yin', {})
        yang_yin_gan = yin_yang.get('stem', '')  # 阳印天干(如壬)
        yin_yin_gan = yin_yin.get('stem', '')    # 阴印天干(如癸)
        yang_yin_total = yin_yang.get('total', 0)
        yin_yin_total = yin_yin.get('total', 0)
        # 确定主力印干
        if yang_yin_total >= yin_yin_total and yang_yin_total > 0:
            main_yin_gan = yang_yin_gan
            main_yin_type = '阳印(偏印/枭神)'
        elif yin_yin_total > 0:
            main_yin_gan = yin_yin_gan
            main_yin_type = '阴印(正印)'
        else:
            main_yin_gan = ''
            main_yin_type = ''
        # 天干细分描述
        yin_stem_desc = ''
        if main_yin_gan:
            yin_stem_desc = f'主力印干={main_yin_gan}({main_yin_type},力{yang_yin_total if "阳印" in main_yin_type else yin_yin_total})，阳印{yang_yin_gan}力{yang_yin_total}/阴印{yin_yin_gan}力{yin_yin_total}'

        if yin_L2:
            # L2印多为病/水泛木浮: 第一候选=财星(克印), 原典"水多用戊, 土克水则生木"
            candidates.append(_candidate(
                cai_wx, 1,
                evidence=f'滴天髓: 水多木浮，土克水则生木。印星({yin_wx})过旺(L2: 透干{yin_stem_count}个/本气中气{yin_ben_zhong}个/印局{yin_ju}个/日主根虚浮={dm_root_floating})，用财星({cai_wx})克印去病',
                boundary='印多为病时用财克印；财需有根方效；忌再增印星'
            ))
            candidates.append(_candidate(
                bi_wx, 2,
                evidence=f'滴天髓: 衰则助之，{legacy_tier}用比劫({bi_wx})帮身分印之壅',
                boundary='比劫帮身需有根；印多时比劫可分印'
            ))
            # 印星标注为忌(第三候选位置但标注忌)
            l2_yin_cand = _candidate(
                yin_wx, 3,
                evidence=f'印星({yin_wx})已过旺(L2)，为病非用。{yin_stem_desc}',
                boundary=f'印多为病，忌再增印；阳印过旺防枭神夺食，阴印过旺防母多灭子；此候选仅作结构标注，非推荐用神'
            )
            if main_yin_gan:
                l2_yin_cand['stem_detail'] = {
                    'main_yin_gan': main_yin_gan,
                    'main_yin_type': main_yin_type,
                    'yang_yin_total': yang_yin_total,
                    'yin_yin_total': yin_yin_total,
                }
                l2_yin_cand['stem_element'] = main_yin_gan  # 天干级别: 主力印干(忌)
            candidates.append(l2_yin_cand)
        elif yin_L1:
            # L1印星偏旺(临界状态): 印星降级但不排除, 首选印星(标注需注意), 第二候选财星(制印)
            # 原典: 此局是"水偏旺但未成灾", 不是"水泛木浮"; 癸水润燥是吉, 壬水泛滥才是病
            l1_yin_cand = _candidate(
                yin_wx, 1,
                evidence=f'滴天髓: 衰则扶之，{legacy_tier}用印星({yin_wx})生身。印星偏旺(L1: 透干{yin_stem_count}个/本气中气{yin_ben_zhong}个)，需注意印星壅塞，但未成灾。{yin_stem_desc}',
                boundary=f'印星偏旺需注意；润燥阴印可用，泛滥阳印宜制；阳印过旺防枭神夺食，阴印过旺防母多灭子'
            )
            if main_yin_gan:
                l1_yin_cand['stem_detail'] = {
                    'main_yin_gan': main_yin_gan,
                    'main_yin_type': main_yin_type,
                    'yang_yin_total': yang_yin_total,
                    'yin_yin_total': yin_yin_total,
                }
                # L1印星偏旺: 润燥阴印(正印)可用, 泛滥阳印(偏印)宜制
                # 所以用神天干优先选阴印(如癸水润燥), 而非阳印(如壬水泛滥)
                l1_yin_cand['stem_element'] = yin_yin_gan if yin_yin_total > 0 else main_yin_gan
            candidates.append(l1_yin_cand)
            candidates.append(_candidate(
                cai_wx, 2,
                evidence=f'滴天髓: 印星偏旺时可用财星({cai_wx})制印防壅；土克水则生木',
                boundary='财星制印需有根；印星未成灾时财为辅助非首选'
            ))
            candidates.append(_candidate(
                bi_wx, 3,
                evidence=f'滴天髓: 衰则助之，{legacy_tier}用比劫({bi_wx})帮身',
                boundary='比劫帮身需有根；衰极尤宜印生'
            ))
        else:
            # 印星正常: 首选印星, 第二候选比劫
            normal_yin_cand = _candidate(
                yin_wx, 1,
                evidence=f'滴天髓: 衰则扶之，{legacy_tier}用印星({yin_wx})生身。{yin_stem_desc}',
                boundary='衰极宜生不宜助；太衰/衰可生可助，视印源而定；阳印偏印/阴印正印机制不同'
            )
            if main_yin_gan:
                normal_yin_cand['stem_detail'] = {
                    'main_yin_gan': main_yin_gan,
                    'main_yin_type': main_yin_type,
                    'yang_yin_total': yang_yin_total,
                    'yin_yin_total': yin_yin_total,
                }
                # 印星正常: 优先阴印(正印,温和生身), 阳印(偏印)力猛易枭神夺食
                normal_yin_cand['stem_element'] = yin_yin_gan if yin_yin_total > 0 else main_yin_gan
            candidates.append(normal_yin_cand)
            candidates.append(_candidate(
                bi_wx, 2,
                evidence=f'滴天髓: 衰则助之，{legacy_tier}用比劫({bi_wx})帮身',
                boundary='比劫帮身需有根；衰极尤宜印生'
            ))
        # 第三候选: 官杀(克) - 仅从杀格/杀印相生时适用(官杀成势且日主无根/印化杀)
        guan_wx = KE_ME.get(dmw)
        guan_power_p3 = wp_data.get(guan_wx, {}) if wp_data else {}
        guan_ben_p3 = guan_power_p3.get('ben_n', 0) + guan_power_p3.get('zhong_n', 0)
        # 从杀格: 官杀本气>=2 且 日主无根 且 印星无力(不化杀)
        yin_power_p3 = wp_data.get(yin_wx, {}) if wp_data else {}
        yin_weak_p3 = (yin_power_p3.get('ben_n', 0) + yin_power_p3.get('zhong_n', 0) + yin_power_p3.get('stem_n', 0)) == 0
        is_congsha = (guan_ben_p3 >= 2 and dm_root_floating and yin_weak_p3)
        # 杀印相生: 官杀有根 且 印星有力(化杀生身)
        yin_strong_p3 = (yin_power_p3.get('ben_n', 0) + yin_power_p3.get('zhong_n', 0)) >= 1
        is_shayin = (guan_ben_p3 >= 1 and yin_strong_p3)
        if guan_wx and guan_wx != yin_wx and guan_wx != bi_wx and (is_congsha or is_shayin):
            candidates.append(_candidate(
                guan_wx, 3,
                evidence=f'滴天髓/子平真诠: {"从杀格" if is_congsha else "杀印相生"}用官杀({guan_wx})，官杀成势({guan_ben_p3}个)',
                boundary='仅从杀格/杀印相生时适用；普通身衰官杀为忌'
            ))
        # 第四候选: 食伤(我生) - 仅从儿格时适用(食伤成势且日主无根)
        shi_wx = SHENG.get(dmw)
        shi_power_p4 = wp_data.get(shi_wx, {}) if wp_data else {}
        shi_ben_p4 = shi_power_p4.get('ben_n', 0) + shi_power_p4.get('zhong_n', 0)
        # 从儿格: 食伤本气>=2 且 日主无根 且 官杀无力(不制食伤)
        guan_weak_p4 = (guan_power_p3.get('ben_n', 0) + guan_power_p3.get('zhong_n', 0) + guan_power_p3.get('stem_n', 0)) == 0
        is_conger = (shi_ben_p4 >= 2 and dm_root_floating and guan_weak_p4)
        if shi_wx and shi_wx not in [yin_wx, bi_wx, guan_wx] and is_conger:
            candidates.append(_candidate(
                shi_wx, 4,
                evidence=f'滴天髓/子平真诠: 从儿格用食伤({shi_wx})泄秀，食伤成势({shi_ben_p4}个)',
                boundary='仅食伤成势/从儿格时适用；普通身衰食伤为忌'
            ))
        # 第五候选: 财(我克) - 仅从财格时适用(财星成势且日主无根)
        cai_wx = KE.get(dmw)
        cai_power_p5 = wp_data.get(cai_wx, {}) if wp_data else {}
        cai_ben_p5 = cai_power_p5.get('ben_n', 0) + cai_power_p5.get('zhong_n', 0)
        # 从财格: 财本气>=2 且 日主无根 且 比劫无力(不夺财)
        bi_power_p5 = wp_data.get(bi_wx, {}) if wp_data else {}
        bi_weak_p5 = (bi_power_p5.get('ben_n', 0) + bi_power_p5.get('zhong_n', 0) + bi_power_p5.get('stem_n', 0)) == 0
        is_congcai = (cai_ben_p5 >= 2 and dm_root_floating and bi_weak_p5)
        if cai_wx and cai_wx not in [yin_wx, bi_wx, guan_wx, shi_wx] and is_congcai:
            candidates.append(_candidate(
                cai_wx, 5,
                evidence=f'滴天髓/子平真诠: 从财格用财({cai_wx})，财星成势({cai_ben_p5}个)',
                boundary='仅财星成势/从财格时适用；普通身衰财为忌'
            ))

    grade = 'DIRECT' if legacy_tier in ('旺局', '衰局') else 'INFERRED'
    return _track_output('DTS', '体用轨', True, candidates, grade,
                         note=f'日主{legacy_tier}，{"宜抑" if is_wang_ju else "宜扶"}')


# ============================================================
# 冲突保留层 (不裁决，只识别+标注)
# ============================================================
def _conflict_layer(tracks: List[Dict]) -> Dict:
    """冲突保留层: 识别多轨候选冲突，不裁决。"""
    activated = [t for t in tracks if t['activated'] and t['candidates']]

    if len(activated) <= 1:
        return {
            'has_conflict': False,
            'conflict_type': None,
            'tracks_involved': [],
            'resolution': '单轨或无冲突',
            'display_note': '',
        }

    # 收集各轨首选候选
    primary_elements = {}
    for t in activated:
        first = t['candidates'][0]['element'] if t['candidates'] else None
        if first:
            primary_elements.setdefault(first, []).append(t['track_id'])

    # 冲突判定: 首选候选五行不同
    unique_elements = list(primary_elements.keys())
    if len(unique_elements) <= 1:
        # 检查是否为调候=格局用神合一情形
        track_ids_all = [t['track_id'] for t in activated]
        is_heyi = ('ZPZQ' in track_ids_all and 'QTBJ' in track_ids_all and
                   len(unique_elements) == 1)
        if is_heyi:
            return {
                'has_conflict': False,
                'conflict_type': '合一',
                'tracks_involved': track_ids_all,
                'resolution': '调候=格局用神，合一无冲突',
                'display_note': f'调候轨与格局轨首选一致({unique_elements[0]})，两者合一，无需取舍',
                'heyi': True,
            }
        return {
            'has_conflict': False,
            'conflict_type': None,
            'tracks_involved': [t['track_id'] for t in activated],
            'resolution': '多轨首选一致',
            'display_note': f'多轨均指向{unique_elements[0]}',
        }

    # 有冲突
    track_ids = [t['track_id'] for t in activated]
    # 冲突类型
    if 'ZPZQ' in track_ids and 'QTBJ' in track_ids:
        ctype = '格局vs调候'
    elif 'QTBJ' in track_ids and 'SFTK' in track_ids:
        ctype = '调候vs病药'
    elif 'SFTK' in track_ids and 'DTS' in track_ids:
        ctype = '病药vs体用'
    elif 'ZPZQ' in track_ids and 'DTS' in track_ids:
        ctype = '格局vs体用'
    else:
        ctype = '多轨冲突'

    detail = '; '.join([f"{t['track_name']}首选{t['candidates'][0]['element']}" for t in activated if t['candidates']])

    return {
        'has_conflict': True,
        'conflict_type': ctype,
        'tracks_involved': track_ids,
        'resolution': '保留多解，不裁决',
        'display_note': f'{ctype}冲突: {detail}。请结合命局整体判断，各轨有独立原文依据。',
    }


# ============================================================
# 主入口: 四轨并行 + 冲突保留 + 多解输出
# ============================================================
def build_yongshen_multi_track(pillars, facts, wuxing_power, spectrum, special, climate, bingyao=None):
    """用神四轨并行层主入口。

    Args:
        pillars: 四柱 dict
        facts: L0 facts
        wuxing_power: 五行力量
        spectrum: 日主旺衰谱
        special: 特殊格局
        climate: 调候候选
        bingyao: 病药层(可选)

    Returns:
        四轨输出 + 冲突层 + 多解候选集
    """
    # 四轨独立计算
    track_zpzq = _track_zpzq(pillars, facts, wuxing_power, spectrum, special, climate)
    track_qtbj = _track_qtbj(pillars, facts, wuxing_power, spectrum, special, climate)
    track_sftk = _track_sftk(pillars, facts, wuxing_power, spectrum, special, climate, bingyao)
    track_dts = _track_dts(pillars, facts, wuxing_power, spectrum, special, climate)

    tracks = [track_zpzq, track_qtbj, track_sftk, track_dts]

    # 冲突保留层
    conflict = _conflict_layer(tracks)

    # 多解候选集 (所有激活轨道候选并集)
    all_candidates = []
    for t in tracks:
        if t['activated']:
            for c in t['candidates']:
                all_candidates.append({
                    'element': c['element'],
                    'track_id': t['track_id'],
                    'track_name': t['track_name'],
                    'priority_in_track': c['priority'],
                    'evidence': c['evidence'],
                    'boundary': c['boundary'],
                })

    # 去重 (同一五行可能多轨都输出)
    seen = set()
    unique_candidates = []
    for c in all_candidates:
        key = c['element']
        if key not in seen:
            seen.add(key)
            unique_candidates.append(c)

    # display层
    activated_tracks = [t for t in tracks if t['activated'] and t['candidates']]
    if not conflict['has_conflict'] and activated_tracks:
        # 无冲突: primary = 唯一首选
        primary = activated_tracks[0]['candidates'][0]['element']
        display = {
            'primary': primary,
            'primary_track': activated_tracks[0]['track_name'],
            'all_candidates': unique_candidates,
            'note': conflict.get('display_note', ''),
        }
    else:
        # 有冲突: 不设primary，所有候选并列
        display = {
            'primary': None,
            'primary_track': None,
            'all_candidates': unique_candidates,
            'note': conflict.get('display_note', '多轨结论不同，保留多解'),
        }

    return {
        'module': 'YONGSHEN_MULTI_TRACK_V1.0',
        'namespace': 'daymaster_yongshen_multi_track',
        'version': '1.0',
        'tracks': {
            'ZPZQ': track_zpzq,
            'QTBJ': track_qtbj,
            'SFTK': track_sftk,
            'DTS': track_dts,
        },
        'conflict': conflict,
        'all_candidates': unique_candidates,
        'candidate_elements': [c['element'] for c in unique_candidates],
        'display': display,
        'boundary_note': (
            '四轨并行，冲突保留不裁决; 渊海子平/三命通会降级为基础事实校验层; '
            '不评分/不权重/不强行统一; 命中率@K评价; 吉凶前端拦截'
        ),
    }


# 五行->天干/地支根映射 (用于透出得地检查)
_WUXING_TO_STEMS = {
    '木': ['甲', '乙'], '火': ['丙', '丁'], '土': ['戊', '己'],
    '金': ['庚', '辛'], '水': ['壬', '癸'],
}
_WUXING_TO_ROOTS = {
    '木': ['寅', '卯'], '火': ['巳', '午'], '土': ['辰', '戌', '丑', '未'],
    '金': ['申', '酉'], '水': ['亥', '子'],
}


def check_yongshen_tou_de(pillars: Dict[str, Any], candidates: List[Dict]) -> Dict[str, Any]:
    """用神透出得地结构化检查 (YONGSHEN-TOUGAN-001).

    只做: 检查每个用神候选五行是否透出天干/在地支有根
    不做: 用神最终裁决/吉凶/成败/有力无力

    原典: 用神得地得势, 富贵双全; 用神无根无气, 虚而不实.
    """
    all_stems = [pillars[k][0] for k in ('year', 'month', 'day', 'hour')]
    all_branches = [pillars[k][1] for k in ('year', 'month', 'day', 'hour')]

    results = []
    for c in candidates:
        element = c.get('element', '')
        # 提取五行 (候选可能是"火"或"庚"或"病=泄气太重"等)
        wuxing = None
        for wx in ['木', '火', '土', '金', '水']:
            if wx in element:
                wuxing = wx
                break
        if wuxing is None:
            # 尝试从天干提取五行
            stem_to_wx = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
                          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
            for stem, wx in stem_to_wx.items():
                if stem in element:
                    wuxing = wx
                    break

        if wuxing:
            target_stems = _WUXING_TO_STEMS.get(wuxing, [])
            target_roots = _WUXING_TO_ROOTS.get(wuxing, [])
            tou_stems = [s for s in all_stems if s in target_stems]
            de_branches = [b for b in all_branches if b in target_roots]
            has_tou = len(tou_stems) > 0
            has_de = len(de_branches) > 0
        else:
            tou_stems = []
            de_branches = []
            has_tou = False
            has_de = False

        results.append({
            'candidate_element': element,
            'wuxing': wuxing,
            'has_tou_gan': has_tou,
            'tou_gan_stems': tou_stems,
            'has_de_di': has_de,
            'de_di_branches': de_branches,
            'tou_de_status': 'TOU_AND_DE' if (has_tou and has_de) else
                             ('TOU_ONLY' if has_tou else
                              ('DE_ONLY' if has_de else 'NO_TOU_NO_DE')),
        })

    return {
        'module': 'YONGSHEN_TOU_DE_CHECK',
        'namespace': 'daymaster_yongshen.tou_de',
        'check_results': results,
        'candidate_count': len(results),
        'tou_and_de_count': sum(1 for r in results if r['tou_de_status'] == 'TOU_AND_DE'),
        'boundary_note': (
            '用神透出得地仅为结构化检查; 只报告候选五行是否透出天干/在地支有根, '
            '不做用神最终裁决/吉凶/成败/有力无力; 透出得地≠用神成立'
        ),
        'evidence_refs': ['YHZP 用神得地得势', 'PZZQ 用神透干得地'],
    }



def check_yongshen_chun_za(candidates: List[Dict]) -> Dict[str, Any]:
    """用神清纯混杂结构化检查 (YONGSHEN-CHUNZA-001).

    只做: 统计用神候选五行种类, 判断清纯/混杂
    不做: 用神最终裁决/吉凶/成败/贵贱

    原典: 用神清纯则贵, 用神混杂则贱.
    """
    # 提取每个候选的五行
    wuxing_list = []
    for c in candidates:
        element = c.get('element', '')
        wuxing = None
        for wx in ['木', '火', '土', '金', '水']:
            if wx in element:
                wuxing = wx
                break
        if wuxing is None:
            stem_to_wx = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
                          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
            for stem, wx in stem_to_wx.items():
                if stem in element:
                    wuxing = wx
                    break
        if wuxing:
            wuxing_list.append(wuxing)

    unique_wuxing = list(set(wuxing_list))
    wuxing_count = {}
    for wx in wuxing_list:
        wuxing_count[wx] = wuxing_count.get(wx, 0) + 1

    if len(unique_wuxing) == 0:
        status = 'UNKNOWN'
    elif len(unique_wuxing) == 1:
        status = 'CHUN'  # 清纯
    elif len(unique_wuxing) == 2:
        status = 'WEAK_ZA'  # 微杂
    else:
        status = 'ZA'  # 混杂

    return {
        'module': 'YONGSHEN_CHUN_ZA_CHECK',
        'namespace': 'daymaster_yongshen.chun_za',
        'candidate_count': len(candidates),
        'wuxing_kinds': len(unique_wuxing),
        'wuxing_distribution': wuxing_count,
        'chun_za_status': status,
        'boundary_note': (
            '用神清纯混杂仅为结构化检查; 只统计候选五行种类, 不做用神最终裁决/吉凶/成败/贵贱; '
            '清纯≠贵, 混杂≠贱(原典断语需结合整体命局)'
        ),
        'evidence_refs': ['PZZQ 用神清纯则贵', 'DTS 清气浊气'],
    }



def check_yongshen_priority(pillars: Dict[str, Any], tracks: Dict[str, Any]) -> Dict[str, Any]:
    """用神优先级仲裁结构化检查 (YONGSHEN-PRIORITY-001 / DIAOHOU-PRIORITY-001).

    只做: 根据原典规则检查调候/格局优先级
    不做: 用神最终裁决/强行统一/吉凶

    原典规则:
      1. 调候=格局用神 -> 合一, 无冲突
      2. 冬夏生人(亥子丑/巳午未)且调候与格局冲突 -> 调候优先
      3. 非冬夏且冲突 -> 格局优先
    """
    month_branch = pillars.get('month', ['?', '?'])[1] if isinstance(pillars.get('month'), list) else '?'
    is_dongxia = month_branch in ['亥', '子', '丑', '巳', '午', '未']

    zpzq_track = tracks.get('ZPZQ', {})
    qtbj_track = tracks.get('QTBJ', {})

    zpzq_activated = zpzq_track.get('activated', False)
    qtbj_activated = qtbj_track.get('activated', False)

    zpzq_candidates = zpzq_track.get('candidates', [])
    qtbj_candidates = qtbj_track.get('candidates', [])

    zpzq_first = zpzq_candidates[0].get('element', '') if zpzq_candidates else ''
    qtbj_first = qtbj_candidates[0].get('element', '') if qtbj_candidates else ''

    # 提取五行
    def _extract_wuxing(element):
        for wx in ['木', '火', '土', '金', '水']:
            if wx in element:
                return wx
        stem_to_wx = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
                      '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
        for stem, wx in stem_to_wx.items():
            if stem in element:
                return wx
        return None

    zpzq_wx = _extract_wuxing(zpzq_first)
    qtbj_wx = _extract_wuxing(qtbj_first)

    # 合一情形
    if zpzq_activated and qtbj_activated and zpzq_wx and qtbj_wx and zpzq_wx == qtbj_wx:
        priority_result = 'HEYI'
        priority_note = '调候=格局用神, 合一, 无冲突'
        primary_track = 'BOTH'
    # 冬夏且冲突 -> 调候优先
    elif is_dongxia and zpzq_activated and qtbj_activated and zpzq_wx and qtbj_wx and zpzq_wx != qtbj_wx:
        priority_result = 'DIAOHOU_PRIORITY'
        priority_note = '冬夏生人且调候与格局冲突, 调候优先(依栏江网)'
        primary_track = 'QTBJ'
    # 非冬夏且冲突 -> 格局优先
    elif not is_dongxia and zpzq_activated and qtbj_activated and zpzq_wx and qtbj_wx and zpzq_wx != qtbj_wx:
        priority_result = 'GEJU_PRIORITY'
        priority_note = '非冬夏且调候与格局冲突, 格局优先(子平真诠)'
        primary_track = 'ZPZQ'
    # 单轨激活
    elif zpzq_activated and not qtbj_activated:
        priority_result = 'GEJU_ONLY'
        priority_note = '仅格局轨激活'
        primary_track = 'ZPZQ'
    elif qtbj_activated and not zpzq_activated:
        priority_result = 'DIAOHOU_ONLY'
        priority_note = '仅调候轨激活'
        primary_track = 'QTBJ'
    else:
        priority_result = 'UNKNOWN'
        priority_note = '无法判断优先级'
        primary_track = None

    return {
        'module': 'YONGSHEN_PRIORITY_CHECK',
        'namespace': 'daymaster_yongshen.priority',
        'month_branch': month_branch,
        'is_dongxia': is_dongxia,
        'zpzq_first_element': zpzq_first,
        'qtbj_first_element': qtbj_first,
        'zpzq_wuxing': zpzq_wx,
        'qtbj_wuxing': qtbj_wx,
        'priority_result': priority_result,
        'primary_track': primary_track,
        'priority_note': priority_note,
        'boundary_note': (
            '用神优先级仅为结构化检查; 只根据原典规则报告优先级, '
            '不做用神最终裁决/强行统一/吉凶; 优先级建议≠最终用神'
        ),
        'evidence_refs': ['QTBJ 调候用神喜忌为第一', 'PZZQ 八字用神专求月令'],
    }
