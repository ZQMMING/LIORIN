# -*- coding: utf-8 -*-
"""格局成格判定层.
PZZQ原文(255/258/241行): 八格成格/破格.
第一步已落地: 食神生财格成格+成格之神为喜.
第二步(第一步,可控): 伤官带煞无财格 -- 只标格体(伤官+煞), 不动病药层.
  PZZQ255: "伤官带煞而无财...伤官格成也". 杀是格体非破格; 身弱用印(第二步改).
双层属性: 格体(格局层) / 忌神(日主层) 并存, 第二步动病药层."""
from typing import Any, Dict
from engines.common.l0_fact_builder import HIDDEN

GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
YINYANG = {'甲':1,'乙':0,'丙':1,'丁':0,'戊':1,'己':0,'庚':1,'辛':0,'壬':1,'癸':0}
DM_LU = {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}
DM_WANG = {'甲':'卯','乙':'寅','丙':'午','丁':'巳','戊':'午','己':'巳','庚':'酉','辛':'申','壬':'子','癸':'亥'}
SHENG = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
KE = {'木':'土','土':'水','水':'火','火':'金','金':'木'}
CAI = {'正财','偏财'}
ZHI_WX = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}

# 阴干在阳令的借根剥离表(CASE_LEVEL才生效; 丁巳/辛申/癸亥 NO_EVIDENCE不启用)
# SFTK: 乙日寅月, 阳木得令阴木反弱. 寅是甲禄不是乙根.
_YIN_YANG_JIEGEN = {('乙','寅'): True}
# 地支本气干(禄=同阴阳日主根; 刃支本气=劫财, 异阴阳非日主根)
# ★ ARCHIVED_FALLBACK (2026-10-06): 支本气干已改消费排盘 facts['hidden_stems'],
# 本表仅兜底(非 gate 调用方). 备份: _legacy_relation_tables.
ZHI_BEN_GAN = {'子':'癸','丑':'己','寅':'甲','卯':'乙','辰':'戊','巳':'丙',
               '午':'丁','未':'己','申':'庚','酉':'辛','戌':'戊','亥':'壬'}

def dm_tier(wp, dg, month_zhi, pillars=None, kong_wang=None, facts=None):
    """日主视角旺衰tier: 冲拔拓扑后再判element_power_tier.
    根气判据(PZZQ L800「长生、禄、帝旺为重根, 墓库余气为轻根」;
      L1075「煞格逢刃, 日时逢刃, 取刃帮身以敌煞」; L1331「乙生寅月,
      月劫秉令」): 支本气五行同日主即比劫根——同阴阳为禄/比肩,
      异阴阳为帝旺/刃/劫财——**皆计日主根(帮身)**, 不按天干同字剥刃根.
      (旧判据"异阴阳本气支是比劫非日主根->剥"与 PZZQ「帝旺为重根、
       日时逢刃帮身」冲突, 2026-10-06 撤销. 刃虽不善、须官杀制, 但先帮身;
       "刃无官杀制/比劫争财"的凶归格局/病药层判, 不靠剥刃根误压身弱.)
    冲拔(得地层·五层拓扑算子, engines/common/root_clash.py): 冲对/根位/
      冲-根匹配/冲力/解冲——根方失时(休囚死)被紧贴冲且无合解 -> 拔;
      得时被冲 -> 发不拔; 隔柱旺冲衰亦拔; 遥冲/合解/空亡不扣.
      滴天髓「旺者冲衰衰者拔, 衰神冲旺旺神发」+ 禄神逢冲为破禄.
      (DT-0029 甲木戌月囚, 寅禄被申冲拔)
    临时补丁一/二的切换点: 修复后财格过滤改用此函数."""
    import copy
    from engines.common.transit_power import element_power_tier
    from engines.common.root_clash import build_root_clash_events, effective_ben
    wx = GAN_WX.get(dg, '')
    if not wx: return {'tier':0,'name':'衰'}
    wp2 = copy.deepcopy(wp)
    dm_e = wp2['wuxing_power'].get(wx, {})
    if pillars:
        _zhis = [pillars[_pos][1] for _pos in ('year','month','day','hour')]
        # 2026-10-06: 支本气干以排盘权威 facts['hidden_stems'] 为准(缺时兜底本地表)
        _hd_ = (facts or {}).get('hidden_stems') or {}
        _zhi_ben_gan = {}
        if _hd_:
            for _pos in ('year', 'month', 'day', 'hour'):
                _z_ = pillars.get(_pos, ['', ''])[1]
                if _z_:
                    _zhi_ben_gan[_z_] = (_hd_.get(_pos) or [''])[0]
        if not _zhi_ben_gan:
            _zhi_ben_gan = ZHI_BEN_GAN
        _ben_self = sum(1 for _z in _zhis if GAN_WX.get(_zhi_ben_gan.get(_z)) == wx)
        # 根气判据: PZZQ L800「长生禄帝旺为重根」+ L1075「日时逢刃帮身敌煞」
        #   + L1331「乙生寅月, 月劫秉令」——本气五行同日主即比劫根(禄/刃/
        #   比肩/劫财)皆计日主根, 不按天干同字剥刃根.
        # 得地层·冲拔拓扑算子 (五层: 冲对/根位/冲-根匹配/冲力/解冲)
        #   滴天髓「旺者冲衰衰者拔, 衰神冲旺旺神发」——根方失时(休囚死)被
        #   强冲且无合解 -> 拔; 根方得时被冲 -> 发, 不拔; 隔柱旺冲衰亦拔;
        #   遥冲/合解 -> 不扣. 禄神逢冲为破禄. (DT-0029 甲木戌月囚,
        #   申金相乘权冲寅禄, 年日隔位亦「冲去禄神其根已拔」)
        _ling = (wp2['wuxing_power'].get(wx, {}) or {}).get('ling_state', '休')
        dm_e['ben_n'] = effective_ben(
            _ben_self,
            build_root_clash_events(pillars, dg, _ling, wp2['wuxing_power'],
                                    kong_wang, (facts or {}).get('l0_chart') or None),
            _ling)
    # 同阴阳借根剥(乙寅)已撤销: PZZQ 刃/劫财为帮身重根, 不剥.
    # (旧 _YIN_YANG_JIEGEN 把乙在寅的帝旺根剥掉, 与 L800/L1075 冲突)
    return element_power_tier(wp2, wx)

def ten_god(dg, stem):
    if dg not in GAN_WX or stem not in GAN_WX:
        return ''
    dwx, swx = GAN_WX[dg], GAN_WX[stem]
    same = YINYANG[dg] == YINYANG[stem]
    if swx == dwx:
        return '比肩' if same else '劫财'
    if SHENG[dwx] == swx:
        return '食神' if same else '伤官'
    if KE[dwx] == swx:
        return '偏财' if same else '正财'
    if SHENG[swx] == dwx:
        return '偏印' if same else '正印'
    if KE[swx] == dwx:
        return '七杀' if same else '正官'
    return ''

def _gans(pillars):
    return [pillars[k][0] for k in ('year','month','day','hour') if k in pillars]

def _zhis(pillars):
    return [pillars[k][1] for k in ('year','month','day','hour') if k in pillars]

def build_ge_cheng(facts: Dict[str, Any]) -> Dict[str, Any]:
    pillars = facts.get('pillars', {}) or {}
    dg = facts.get('day_stem', '') or ''
    gans = _gans(pillars)
    zhis = _zhis(pillars)
    # 2026-10-06 权威源=排盘引擎: 支本气干从 facts['hidden_stems'][pos][0]
    #   (l0_fact_builder 已消费排盘 hidden_stems); 缺时兜底本地表(归档备份)
    _hd = facts.get('hidden_stems') or {}
    _zhi_ben_gan = {}
    if _hd:
        for _pos in ('year', 'month', 'day', 'hour'):
            _z = pillars.get(_pos, ['', ''])[1]
            if _z:
                _zhi_ben_gan[_z] = (_hd.get(_pos) or [''])[0]
    if not _zhi_ben_gan:
        _zhi_ben_gan = ZHI_BEN_GAN

    # PATCH-GAP11c (2026-10): 从格入口统一净化 —— special_pattern.py L572「从杀格」CANDIDATE
    #   不入正式格层。L572 条件含「日主无根或根极弱」, 「根极弱」是工程自造词, 全库无切片;
    #   dm_ben_eff<=1 / yin_ben_eff<=1 两个整数阈值亦无 primary 依据。
    #   准神 DTS L420(SHUAI.003)「日主孤立无气, 无地人元, 绝无一毫生扶之意, 财官强甚, 乃为真从也」
    #   只给「无气」定性, 未给量化门槛, 故不能据以定阈值。
    #   净化点必须在函数入口统一做: 本函数 L80(路径①) 与 L787(路径②) 各自重算
    #   build_special_patterns(跨层重复, 观察-4), 两处 sp 互不相干 ——
    #   只堵其中一处会漏: PZ-0129 丙戌辛丑壬午戊申 即由 L787 那条路径产出
    #   从格(从杀格) xi_wx=['火'], 绕过了 L803/L810 的过滤。
    #   CANDIDATE 项仍保留在 sp['patterns'] 候选层可查, 只是不进正式格层。
    # PATCH-GAP11d (2026-10): special 单一数据源。
    #   此前本函数在 L105(路径①) 与 L812(路径②) 各自重算 build_special_patterns,
    #   而 bazi_gate.paipan L159 另算第三份 —— 三份 sp 互不相干(跨层重复, 观察-4)。
    #   两处内部调用都是【三参】(pillars, facts, wp), 而签名第 4/5 参是
    #   tian_he=None / climate=None —— 默认 None 会让下游两段整段短路:
    #     special_pattern L238  if tian_he and ...  -> 化气格(含木化气四支局全门)整段不执行
    #     special_pattern L405  if not cong and climate and 'XU_SHI_HAN_TU' ... -> 虚湿寒土假从不执行
    #   故三参调用是【参数遗漏】, 不是刻意简写: 拿到的 sp 在化气/假从两路是残缺的。
    # 修法: 由 bazi_gate 把已算好的 special(四参, 含 tian_he) 写进 facts['special'],
    #   本函数两处改读 facts['special']; 缺失时(非 gate 调用方)才回退自行计算。
    #   climate 保持 None —— bazi_gate 未算 climate, 不在此凭空引入。
    def _special_of(spv):
        """已算好的 special 优先; 否则退回本函数自算(补 tian_he, 保持与 gate 同参)。"""
        if isinstance(spv, dict) and spv.get('patterns') is not None:
            return spv
        return build_special_patterns(pillars, facts,
                                       facts.get('wuxing_power', {}) or {},
                                       (facts.get('tian_he') or None))

    def _blocked(spv):
        return (isinstance(spv, dict)
                and spv.get('cong_type') == '从杀格'
                and spv.get('cong_state') == 'CANDIDATE')

    def _purge(spv):
        """把 L572 候选从「可进正式格层」降为候选层, 保留 patterns 供查。"""
        if not _blocked(spv):
            return spv
        spv = dict(spv)
        spv['cong_type'] = None
        spv['cong_state'] = None
        spv['cong_candidate_blocked'] = 'L572_CANDIDATE_NO_SLICE'
        return spv

    # 从格CONFIRMED优先(覆盖正格): 日主无根+印比虚浮无根+临绝(子平真诠'四柱无可扶抑')
    # CANDIDATE不覆盖, 走正格判定(v1/v2误报=无差别覆盖, 已回退)
    try:
        from engines.common.special_pattern import build_special_patterns
        _wp0 = facts.get('wuxing_power', {}) or {}
        _sp0 = _purge(_special_of(facts.get('special')))
        # [2026-10-05 PATCH-4c] 化气格定格(在从格分支前, 与 special_pattern 化气先判互斥一致)。
        #   依据原案:
        #     PZZQ L565(本案 PZ-0027)「丁壬相合, 生于卯月, 木旺秉令, 时逢辰, 木之原神透出,
        #           为丁壬化木格」—— 化气格独立成格, 化神(木)为格体。
        #     PZZQ L1034(孙岳造)「丁壬相合, 月时卯寅, 化气格真, 化神喜行旺地, 旺之极者, 亦喜其泄」
        #           —— 喜神=化神(行旺地); 化神极旺则喜泄(食伤)。
        #   ti_wx=化神五行(格体豁免); xi_wx=化神(主喜), 化神极旺喜泄(食伤)登记待专案。
        #   hua_state=CONFIRMED 才覆盖正格; CANDIDATE(假化/返象)只记结构不覆盖。
        if _sp0.get('hua_qi') and _sp0.get('hua_qi_state') == 'CONFIRMED':
            _hwx = _sp0['hua_qi'][1] if len(_sp0['hua_qi']) > 1 and _sp0['hua_qi'][0] == '化' else None
            if _hwx:
                facts['ge_cheng'] = {
                    'ge': _sp0['hua_qi'],
                    'ti_wx': [_hwx],
                    'xi_wx': [_hwx],
                    'xi_wx_status': 'DEFINED',
                    'overpower_combo': 6,
                    'zhi_wx': [], 'hua_wx': [],
                    'po_ge': [],
                    'rule': ('PZZQ L565: 日干与紧邻干五合+化神得月令+原神透出->化气格; '
                             '化神是格体; 喜神=化神(L1034化神喜行旺地); 化神极旺喜泄(食伤)登记待专案'),
                }
                return facts
        if _sp0.get('cong_type') and _sp0.get('cong_state') == 'CONFIRMED':
            _cwx_map = {'从杀格': None, '从官格': None, '从财格': None, '从儿格': None}
            _gs_wx = (facts.get('wuxing_power', {}) or {}).get('wuxing_power', {})
            _dm_wx = (facts.get('wuxing_power', {}) or {}).get('daymaster_element', '')
            _SH = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
            _KE = {'木':'土','土':'水','水':'火','火':'金','金':'木'}
            _KE_M = {'木':'金','金':'火','火':'水','水':'土','土':'木'}
            _ss_wx = _SH.get(_dm_wx,''); _cai_wx = _KE.get(_dm_wx,''); _gs0 = _KE_M.get(_dm_wx,'')
            _ct = _sp0['cong_type']
            _side = {'从杀格': _gs0, '从官格': _gs0, '从财格': _cai_wx, '从儿格': _ss_wx}.get(_ct)
            # 从格破格检查(PZZQ4936/4941/4943/4944):
            #   从财格: 比劫透干争财(无食伤化)破格; 印通根生身破格
            #   从杀格: 食伤制杀破格; 印泄杀气破格
            # 排除day干按位置(索引2), 不能按值(四干同值时按值排除会全滤掉)
            _g3 = [g for i, g in enumerate(gans) if i != 2]
            _bijie = [g for g in _g3 if ten_god(dg, g) in ('比肩','劫财')]
            _shishang = [g for g in _g3 if ten_god(dg, g) in ('食神','伤官')]
            _yin_tou = [g for g in _g3 if ten_god(dg, g) in ('正印','偏印')]
            _po = []
            _not_cong = False
            if _ct == '从财格':
                # 比劫有根=帮身任财(正格财格身弱用比, QT-0057甲木辰中乙木中气根"财旺用比富贵"), 非破格
                # 比劫无根=虚浮逆势(从财格忌比劫, DT-0032辛金卯月临绝"四金临绝岂无成立乎"), 破格报病
                if _bijie and not _shishang:
                    _dm_rd = ((facts.get('wuxing_power',{}).get('wuxing_power',{}) or {}).get(_dm_wx,{}) or {}).get('root_detail',{}) or {}
                    _dm_bn = int((facts.get('wuxing_power',{}).get('wuxing_power',{}) or {}).get(_dm_wx,{}).get('ben_n',0) or 0)
                    if not (_dm_rd or _dm_bn >= 1):
                        _po = [{'type':'组合','match':'ANY','required':['比肩','劫财']}]
                # 印透干+印原始本气根=不从(PZZQ4941"从财格而有印,须看印是否通根"): 不从->走正格(财格佩印), 非破格
                # 印虚透无根=假从仍从
                _YIN_WX = {v: k for k, v in _SH.items()}.get(_dm_wx, '')
                _yin_bn = int(((facts.get('wuxing_power',{}).get('wuxing_power',{}) or {}).get(_YIN_WX,{}) or {}).get('ben_n',0) or 0)
                if _yin_tou and _yin_bn >= 1:
                    _not_cong = True
            if _ct == '从杀格':
                # 从杀格破格(PZZQ"有弃命从煞者...若有伤食则煞受制而不从,有印则印以化煞而不从"):
                #   伤食透干+伤食有本气根(制煞有力)->破格报病; 伤食虚透无根=假从不破格(DT-0109己土伤官虚透无根)
                _hs0 = facts.get('hidden_stems', {}) or {}
                _ben_gans = [(_hs0.get(k) or [''])[0] for k in ('year','month','day','hour') if _hs0.get(k)]
                _ss_ben = any(g in _ben_gans for g in _shishang)
                if bool(_shishang) and _ss_ben:
                    _po = [{'type':'组合','match':'ANY','required':['食神','伤官']}]
                # 印透化煞=不从(PZZQ"有印则印以化煞而不从"): 不从->走正格(杀印相生), 非破格
                if _yin_tou:
                    _not_cong = True
            if _not_cong:
                pass
            else:
                # [2026-10-01 PATCH-3a] 从格 xi_wx 原为硬编码 [], 导致 compare 判"引擎无输出"
                # (PZ-0137 戊辰甲寅壬戌丙午: 从财格CONFIRMED, ti_wx=['火'] 正确, 但 xi_wx 空)。
                #
                # 按 DTS 原典明文分格处理, 不统一填:
                #   从财格 「如从财, 只以财为主」        -> 填财(_cai_wx)  DTS行415
                #   从儿格 「只取我生者为儿」              -> 填食伤(_ss_wx)
                #   从官格 DTS 无从官格喜用明文 -> xi_wx 留空, xi_wx_status=UNDEFINED(存疑)
                #   从杀格 DTS 0 命中(且本表写作"从煞格") -> 留空, UNDEFINED(存疑)
                #   从势格 cong_type 可为'从势格'(special_pattern 多方势均判从势, side=None)
                #          -> _side 本就为 None, 留空 UNDEFINED
                # 说明: 从旺格**不在本分支** —— special_pattern 只把它写进 out['patterns']
                #       候选层('ZP-SPECIAL-CONG', 'CANDIDATE'), 从不写 out['cong_type'];
                #       v1.6 §7.6 亦定「从旺」归专旺格类, 不列从格。枚举层做专旺时处理。
                # 铁律: 无原典明文则不编造, 缺省 UNDEFINED 而非臆测填值。
                _XI_FILLED = _ct in ('从财格', '从儿格')
                _xi_val = [_side] if (_XI_FILLED and _side) else []
                facts['ge_cheng'] = {
                    'ge': _ct if not _po else _ct + '(破格)',
                    'xi_wx': _xi_val,
                    'xi_wx_status': 'DEFINED' if _xi_val else 'UNDEFINED',
                    'ti_wx': [] if _po else ([_side] if _side else []),
                    'overpower_combo': 6,
                    'zhi_wx': [], 'hua_wx': [],
                    'po_ge': _po,
                    'rule': ('从格破格: 从财格比劫透干无根争财/从杀格伤食有根制煞->破格; 破格后ti_wx不豁免, 病药层照跑'
                             if _po else
                             '从格CONFIRMED优先(覆盖正格): 日主无根+印比虚浮无根+临绝->从格; ti_wx=所从之神'),
                }
                return facts
    except Exception:
        pass

    # 1) 食神生财格: 月令食神entry + 食神透 + 财透 + 日主本气禄旺根
    entry = facts.get('shishen_entry', {}) or {}
    if entry.get('is_entry'):
        shishen_gans = [g for g in gans if ten_god(dg, g) == '食神']
        cai_gans = [g for g in gans if ten_god(dg, g) in CAI]
        self_root = (DM_LU.get(dg) in zhis) or (DM_WANG.get(dg) in zhis)
        if shishen_gans and cai_gans and self_root:
            # 食神生财: 原典SHI_SHEN_001"食神生财美格, 财要有根, 身强食旺而财透大贵"
            # 喜神=食神(成格之神)+财(生财之美); 食神是格体
            _shishen_xi = [GAN_WX[shishen_gans[0]]] + [GAN_WX[c] for c in cai_gans]
            facts['ge_cheng'] = {
                'ge': '食神格',
                'xi_wx': sorted(set(_shishen_xi)),
                'xi_gan': sorted(set(shishen_gans+cai_gans)),
                'ti_wx': [GAN_WX[shishen_gans[0]]],  # 食神是格体
                'overpower_combo': 6,   # UNVERIFIED
                'zhi_wx': [],  # 制神: 枭(印)
                'hua_wx': [],  # 化神: 无
                'po_ge': [{'type':'组合','match':'ANY','required':['偏印']}, {'type':'组合','match':'ALL','required':['正财','偏财','七杀']}],  # PZZQ258: 食神逢枭(枭见即夺)/生财露煞(财且煞)
                'rule': 'PZZQ255: 食神生财+身旺 -> 食格成; 成格之神(食神)为喜, 财(生财)亦喜; 破格: 枭夺食/生财露煞',
            }
            return facts
        # 路径二: 食带煞无财弃食就煞透印. PZZQ255: "或食带煞而无财, 弃食就煞而透印, 食格成也"
        sha_gans = [g for g in gans if ten_god(dg, g) == '七杀']
        yin_gans = [g for g in gans if ten_god(dg, g) in ('正印', '偏印')]
        # "弃食"判据: 食神须虚透无根(四支本气无同干)才算弃食; 食神有本气根正在制杀=未弃, 不走此路径
        _shi_qishi = not any(_zhi_ben_gan.get(z) in shishen_gans for z in zhis)
        if shishen_gans and sha_gans and not cai_gans and yin_gans and _shi_qishi:
            facts['ge_cheng'] = {
                'ge': '食神格(带煞无财)',
                'xi_wx': sorted(set(GAN_WX[g] for g in yin_gans)),
                'ti_wx': sorted(set([GAN_WX[sha_gans[0]], GAN_WX[yin_gans[0]]])),
                'overpower_combo': 6,
                'zhi_wx': sorted(set(GAN_WX[g] for g in yin_gans)),  # 制神: 印(弃食就煞, 印制食伤为药)
                'hua_wx': [],
                'po_ge': [{'type':'组合','match':'ALL','required':['正财','偏财','七杀']}],  # PZZQ258: 生财露煞(财且煞, 财非单忌)
                'rule': 'PZZQ255: 食带煞无财弃食就煞透印 -> 食格成; 格体=煞+印; 喜神=印(弃食就煞); 破格: 生财露煞',
            }
            return facts

    # 1.5) 伤官佩印格: 月令伤官 + 印透. PZZQ255: "伤官佩印而伤官旺,印有根".
    # 伤官是格体, 不报泄气病(UNVERIFIED: 伤官旺/印有根判据).
    sg_entry0 = facts.get('shangguan_entry', {}) or {}
    if sg_entry0.get('is_entry'):
        yin_gans0 = [g for g in gans if ten_god(dg, g) in ('正印', '偏印')]
        shangguan_gans0 = [g for g in gans if ten_god(dg, g) == '伤官']
        if yin_gans0 and shangguan_gans0:
            sg_wx0 = facts.get('month_qi_element', '') or ''
            facts['ge_cheng'] = {
                'ge': '伤官格(佩印)', 'xi_wx': sorted(set(GAN_WX[g] for g in yin_gans0)),
                'ti_wx': [sg_wx0],
                'overpower_combo': 6,
                'zhi_wx': [], 'hua_wx': [],
                'po_ge': [{'type':'组合','match':'ALL','required':['正财','偏财','七杀']}],  # PZZQ258: 伤官生财带煞(财且煞, 财非单忌)
                'rule': 'PZZQ255: 伤官佩印伤旺印根->伤官格成; 伤官是格体不报泄气(UNVERIFIED: 伤官旺/印有根判据); 破格: 生财带煞',
            }
            return facts

    # 2) 伤官带煞无财格: 月令伤官entry + 七杀透 + 无财透. 只标格体, 不动病药层.
    sg_entry = facts.get('shangguan_entry', {}) or {}
    if sg_entry.get('is_entry'):
        qisha_gans = [g for g in gans if ten_god(dg, g) == '七杀']
        cai_gans = [g for g in gans if ten_god(dg, g) in CAI]
        yin_gans = [g for g in gans if ten_god(dg, g) in ('正印', '偏印')]
        if qisha_gans and not cai_gans:
            # 格体五行 = 伤官本气(月令) + 七杀透干
            sg_wx = facts.get('month_qi_element', '') or ''
            sha_wx = GAN_WX[qisha_gans[0]]
            facts['ge_cheng'] = {
                'ge': '伤官格(带煞无财)',
                'xi_wx': sorted(set(GAN_WX[g] for g in yin_gans)),
                'ti_wx': sorted(set([w for w in (sg_wx, sha_wx) if w])),
                'overpower_combo': 6,
                'zhi_wx': [], 'hua_wx': [GAN_WX[yin_gans[0]]] if yin_gans else [],
                'po_ge': [{'type':'组合','match':'ANY','required':['正财','偏财']}],  # PZZQ258: 财露(本路径已含带煞, 财单见即破)
                'rule': 'PZZQ255: 伤官带煞无财 -> 伤官格成; 杀是格体非破格; 身弱用印; 破格: 财露',
            }
            return facts

    # 3) 六格扩写: PZZQ255原文, 只定格体, 病药层不消费.
    #    纪律: ti_wx=[] 不触发格体过滤, 仅记录格名; 制化关系待格局层扩全后通用落.
    mqi_god = facts.get('month_qi_ten_god', '') or ''
    mqe = facts.get('month_qi_element', '') or ''
    # 金水伤官例外判定(原典SHANG_GUAN_005"金水伤官要见官"):
    #  日主金(庚辛)或水(壬癸) -> 金水伤官; 或伤官当令金/水(申酉亥子月)亦按金水论
    _dm_is_jinshui = dg in ('庚', '辛', '壬', '癸')
    _sg_dangling_jinshui = mqe in ('金', '水')
    _jinshui_shangguan = _dm_is_jinshui or _sg_dangling_jinshui

    def _has(g):
        return g in gans
    def _god_gans(god):
        return [g for g in gans if ten_god(dg, g) == god]

    # 正官格: 官逢财印又无刑冲破害. 官透 + 财印辅助 + 无伤官克
    if mqi_god == '正官':
        guan_gans = _god_gans('正官')
        if guan_gans:
            cai_gans = _god_gans('正财') + _god_gans('偏财')
            yin_gans = _god_gans('正印') + _god_gans('偏印')
            shangguan = _god_gans('伤官')
            # PZZQ258: 官逢刑冲破格. 官星受冲->不成格(破格).
            guan_chong = facts.get('target_relation_facts', {}).get('官星受冲', False)
            # PATCH-161b 官杀并见+食伤透 -> 食伤制官(优先于财印成格主路径):
            # ZHENG_GUAN_001 露官藏杀成杀气; DTS官杀章"一杀而遇食伤者";
            # PZ-0004 原断"官多同煞,以丙火制官为用"
            _all_gods = set()
            for _st in gans:
                _all_gods.add(ten_god(dg, _st))
            for _zz, _z in pillars.items():
                for _h in HIDDEN[_z[1]]:
                    _all_gods.add(ten_god(dg, _h))
            _officer_mixed = ('正官' in _all_gods) and ('七杀' in _all_gods)
            _shishen_gans = _god_gans('食神') + _god_gans('伤官')
            if _officer_mixed and _shishen_gans and not shangguan and not guan_chong:
                _zhi_xi = sorted(set(GAN_WX[g] for g in _shishen_gans))
                facts['ge_cheng'] = {
                    'ge': '正官格', 'xi_wx': _zhi_xi,
                    'ti_wx': [GAN_WX[guan_gans[0]]],
                    'overpower_combo': 6,
                    'zhi_wx': _zhi_xi, 'hua_wx': [],
                    'po_ge': [{'type':'组合','match':'ANY','required':['伤官']}, {'type':'地支','match':'ANY','branch_cond':'刑冲'}],
                    'rule': 'ZHENG_GUAN_001/DTS官杀章: 官杀并见成杀气,食伤透->食伤制官; 喜神=食伤',
                }
                return facts
            if (cai_gans or yin_gans) and not shangguan and not guan_chong:
                # 喜神按成格路径取(原典ZHENG_GUAN_002逐案, 非财印全并):
                #  官格喜生之护之: 财生官(财护官)/印护官; 官是格体不列喜
                _guan_xi = sorted(set(GAN_WX[g] for g in cai_gans+yin_gans))
                facts['ge_cheng'] = {
                    'ge': '正官格', 'xi_wx': _guan_xi,
                    'ti_wx': [GAN_WX[guan_gans[0]]],
                    'overpower_combo': 6,
                    'zhi_wx': [], 'hua_wx': [],
                    'po_ge': [{'type':'组合','match':'ANY','required':['伤官']}, {'type':'地支','match':'ANY','branch_cond':'刑冲'}],
                    'rule': 'PZZQ255: 官逢财印又无刑冲破害->官格成; 官是格体非杀病; 喜神=财印; 破格: 伤官克/刑冲',
                }
                return facts
            # 默认输出：月令正官+官透，但不满足成格条件（无财印辅助）
            # 败格条件：伤官克/刑冲——败格时不默认输出
            if not shangguan and not guan_chong:
                # 喜神按原典ZHENG_GUAN_004"喜身旺印绶": 身弱无财印辅助时, 喜比劫帮身+印生身
                dm_wx_default = GAN_WX.get(dg, '')
                _yin_gans_default = _god_gans('正印') + _god_gans('偏印')
                _guan_xi_default = [dm_wx_default]
                if _yin_gans_default:
                    _guan_xi_default.append(GAN_WX[_yin_gans_default[0]])
                facts['ge_cheng'] = {
                    'ge': '正官格', 'xi_wx': sorted(set(_guan_xi_default)),
                    'ti_wx': [GAN_WX[guan_gans[0]]],
                    'overpower_combo': 6,
                    'zhi_wx': [], 'hua_wx': [],
                    'po_ge': [{'type':'组合','match':'ANY','required':['伤官']}, {'type':'地支','match':'ANY','branch_cond':'刑冲'}],
                    'rule': 'PZZQ255: 正官格; 官是格体; 破格: 伤官克/刑冲',
                }
                return facts
        # 食神制杀格：月令正官+无正官透+透干七杀+食伤透
        # PZZQ255: 身强七煞逢制(食制)->煞格成; 食伤是制杀格体
        sha_gans_zhi = _god_gans('七杀')
        shi_gans_zhi = _god_gans('食神') + _god_gans('伤官')
        if sha_gans_zhi and shi_gans_zhi:
            ti_list = sorted(set([GAN_WX[sha_gans_zhi[0]], GAN_WX[shi_gans_zhi[0]]]))
            facts['ge_cheng'] = {
                'ge': '食神制杀格', 'xi_wx': [],
                'ti_wx': ti_list,
                'overpower_combo': 6,
                'zhi_wx': [GAN_WX[shi_gans_zhi[0]]],
                'hua_wx': [],
                'po_ge': [{'type':'组合','match':'ANY','required':['正财','偏财']}],  # PZZQ258: 财透无制(食制已立, 财单见即破)
                'rule': 'PZZQ255: 月令官+透杀+食伤透->食神制杀格成; 食伤+煞是格体; 破格: 财透无制',
            }
            return facts

    # 财格: 财生官旺/财逢食生身强带比/财格透印. 财透 + (官透|食透+身旺|印透)
    # 格体过滤前提: 身强(日主禄旺根). 身弱财格不成, 财病照报.
    if mqi_god in ('正财', '偏财'):
        cai_gans = _god_gans('正财') + _god_gans('偏财')
        guan_gans = _god_gans('正官')
        shi_gans = _god_gans('食神')
        yin_gans = _god_gans('正印') + _god_gans('偏印')
        self_root = (DM_LU.get(dg) in zhis) or (DM_WANG.get(dg) in zhis)
        # PZZQ1113: "财生官旺...月令星旺,四柱有官" -- 财当令+官透即可, 不要求财透(UNVERIFIED: 官无根/官杀混杂)
        if guan_gans or cai_gans or (shi_gans and self_root) or yin_gans:
                # PZZQ1113: 财生官旺/财格透印不要求身旺. 财格成->财过滤, 不要求dm_tier>=2.
                # 财透->ti_wx=[财透干五行]; 财不透(月令财)->ti_wx=[月令本气五行]
                if cai_gans:
                    _ti = [GAN_WX[cai_gans[0]]]
                else:
                    _ti = [facts.get('month_qi_element', '')]
                # 喜神按成格路径取(原典逐案, 非食伤/官/印全并):
                #  财生官(官透): 官是格体非喜神, 喜食(生财护官)+财(护官); 兼印透(化官/财滋弱官)喜印
                #  财格透印(印透): 喜印
                #  财逢食生(食透+身强根): 喜食伤(生财)
                #  财带七煞(煞透): 喜印(化煞) — ZHENG_CAI_003「财用煞印者, 党煞为忌, 印以化之」
                #  四路径全空: 喜神留空 — 徐注PZZQ1838「无财与印,不能用官; 无官或食,不能用财」
                #
                # 2026-10-02 修正: 原 L365 else 分支取「财本身」为喜神(注释称"财是成格喜神")。
                #   经 DTS 底本全文核验(623行): 「财格」命中 0 处, DTS 无财格喜神取法明文;
                #   L329(夫妻章)/L349(何知章) 虽有「要官星/要伤官/喜印财生官」, 但语境是
                #   六亲论(看妻星)与富贵论(何知其人富), 非财格建格之喜神取法 — 按 v1.8 §1.3
                #   「教义归位」不得移用。依 DTS-Arbiter 规则②(刘本未涉及->support 择优)采:
                #     PZZQ ZHENG_CAI_001「财为我克,使用之物也,以能生官,所以为美」
                #     PZZQ ZHENG_CAI_002 四贵局(财旺生官/财用食生/财格佩印/用食兼用印)
                #     PZZQ ZHENG_CAI_003 财用伤官/财带七煞/财用煞印
                #     徐注 PZZQ1836「相神又名喜神…主为用,佐其主者为相」
                #     徐注 PZZQ1838「无财与印,不能用官; 无官或食,不能用财」
                #   徐注1838 明言: 财格无官无食则财不能独用 -> 四路径全空时喜神留空,
                #   不取财本身。推理层须标「刘本未直接涉及,取旁参」。
                _sg_gans = _god_gans('食神') + _god_gans('伤官')
                _shishen_only = _god_gans('食神')
                _sha_gans = _god_gans('七杀')
                if guan_gans:
                    # 财生官旺: 原典ZHENG_CAI_002"身强而不透伤官,不混七煞" -- 伤官是破格忌, 不入喜
                    _cai_xi = list(_shishen_only) + list(cai_gans) + list(yin_gans)  # 喜食(生财)+财(护官)+印(滋官)
                elif yin_gans:
                    _cai_xi = list(yin_gans)                     # 财格透印: 喜印
                elif shi_gans and self_root:
                    _cai_xi = list(_shishen_only)                # 财逢食生: 喜食伤
                elif _sha_gans and yin_gans:
                    _cai_xi = list(yin_gans)                     # 财用煞印: 喜印(化煞)
                else:
                    # 四路径全空: 留空。徐注PZZQ1838「无官或食,不能用财」-> 财不独用为喜神
                    _cai_xi = []
                _xi = sorted(set(GAN_WX[g] for g in _cai_xi))
                facts['ge_cheng'] = {
                    'ge': '财格', 'xi_wx': _xi, 'ti_wx': _ti,
                    'overpower_combo': 6,
                    'zhi_wx': [GAN_WX.get(guan_gans[0],'')] if guan_gans else [],  # 制神: 官(财生官)
                    'hua_wx': [],
                    # PATCH-POGE-1 (2026-10): 删「财轻比重」。
                    #   此前 L434/L450 无条件写死 power_cond='财轻比重', 不判财之轻重 ——
                    #   财格 58 条中 39 条带此标签(观察-1 实测: 财格 39 条 100% 命中), 零筛选力。
                    #   实证反判: PZ-0022 癸酉癸亥戊子丁巳 水 ben=2 stem=2(财极旺)仍被判
                    #   「财轻比重」, 与原断「财向日主, 故为富格」明确不破格相左。
                    #   「财轻」在 PZZQ/SFTK 无可量化口径, 须案例反标定(见 TODO-17), 不落码。
                    'po_ge': [{'type':'组合','match':'ANY','required':['七杀']}],  # PZZQ258: 财透七煞
                    'rule': 'PZZQ1113: 财生官/财逢食生身强/财格透印->财格成; 财格成->财过滤不要求身旺; 破格: 财透煞(财轻比重无判据, 已撤, 见 TODO-17)',
                }
                return facts
        # 默认输出：月令财，但不满足成格条件
        # 败格条件：财轻比重/财透七煞——败格时不默认输出
        sha_gans_def = _god_gans('七杀')
        if not sha_gans_def:
            _ti_def = [facts.get('month_qi_element', '')]
            # 财未成格(无官/无财透/无食透身强/无印透): 喜=食伤(伤官制比劫护财, 原典"财不忌伤")
            _sg_gans_def = _god_gans('食神') + _god_gans('伤官')
            _xi_def = sorted(set(GAN_WX[g] for g in _sg_gans_def))
            facts['ge_cheng'] = {
                'ge': '财格', 'xi_wx': _xi_def, 'ti_wx': _ti_def,
                'overpower_combo': 6,
                'zhi_wx': [], 'hua_wx': [],
                'po_ge': [{'type':'组合','match':'ANY','required':['七杀']}],  # PATCH-POGE-1 同源, 见上
                'rule': 'PZZQ255: 财格; 财是格体; 喜食伤(财不忌伤, 伤官制比劫护财); 破格: 财透煞(财轻比重无判据, 已撤, 见 TODO-17)',
            }
            return facts

    # 印格: 印轻逢煞/官印双全/身印两旺用食伤泄气/印多逢财财透根轻
    # 先落官印双全路径: 月令印+官透+印透+官有根+无杀透.
    # 官无根=官虚浮生印无力(UNVERIFIED); 杀透=官杀混杂破格(PZZQ258).
    if mqi_god in ('正印', '偏印'):
        yin_gans = _god_gans('正印') + _god_gans('偏印')
        cai_gans = _god_gans('正财') + _god_gans('偏财')
        guan_gans = _god_gans('正官')
        sha_gans = _god_gans('七杀')

        # [2026-10-01 PATCH-3d] 段2「带伤食」路径判定(沈孝瞻 论印绶 + 徐注分野)。
        #   段2 原文: 「然亦有带伤食而贵者, 则如朱尚书命 丙戌戊戌辛未壬辰, 壬为戊制, 不伤官也。
        #             又如临淮侯命 乙亥己卯丁酉壬寅, 己为乙制, 己不碍官也。」
        #   段2 本质: 官伤并透, 食伤碍官, 须以印制伤兼护官 -> 用神=印(护官之具)。
        #   分野判据(徐注 L3571「而己土透出, 官星不见, 用神较为明显也」= 段3 分界):
        #     官杀透 + 食伤透 -> 段2(食伤碍官, 喜印制之护官)
        #     官杀不见 + 食伤透 -> 段3(食伤无官可碍, 泄秀为喜, 喜食伤)
        #   印克食伤(木克土等)为「己为乙制/壬为戊制」的机制, 是段2 必要条件。
        #   注意: 此处非天干五合 —— 乙己/戊壬皆不在五合表, 是五行印克食伤。
        #   段5「用煞而兼带伤食」(以食伤泄秀非制煞, 克与泄不并用) 需身强煞旺量化门,
        #   原典仅定性, TODO 待逐案, 暂不实现(不脑补判据)。
        _ss_gans = _god_gans('食神') + _god_gans('伤官')
        _gs_all = list(guan_gans) + list(sha_gans)
        _shi_chuang_gu = bool(_ss_gans) and bool(_gs_all)
        _yin_wx_p = GAN_WX[yin_gans[0]] if yin_gans else (facts.get('month_qi_element','') or '')
        _ss_wx_p = GAN_WX[_ss_gans[0]] if _ss_gans else ''
        # 印克食伤: 用引擎 GAN_WX 取五行, 克关系查模块内既有表
        _KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
        _yin_ke_ss = bool(_ss_wx_p) and (_KE.get(_yin_wx_p, '') == _ss_wx_p)
        _d2_dai_shangshi = bool(yin_gans) and _shi_chuang_gu and _yin_ke_ss

        # PZZQ1113: 官印双全=月令印+官透+官有根+无杀透. 印是格体.
        if guan_gans and not sha_gans:
            guan_wx = GAN_WX[guan_gans[0]]
            guan_root = any(ZHI_WX.get(z,'')==guan_wx for z in zhis)
            if guan_root:
                yin_wx = GAN_WX[yin_gans[0]] if yin_gans else (facts.get('month_qi_element','') or '')
                # [2026-10-01 PATCH-3c] 透官路径: 喜神只取官。
                #   ZHENG_YIN_001「有印而透官者, 正官不独取其生印, 而即可以为用」—— 喜神=官, 官生印。
                #   印是格体(ti_wx), 非喜神。旧码三项并集(印+官+食伤)把互斥路径混取, 已改。
                # [2026-10-01 PATCH-3d] 段2「带伤食」优先于段1: 官伤并透时食伤碍官, 须印制伤护官,
                #   喜神=印(护官之具)。原典「朱尚书命 壬为戊制, 不伤官 / 临淮侯命 己为乙制, 己不碍官」。
                if _d2_dai_shangshi:
                    _xi_gans = list(yin_gans)
                    _rule = ('PZZQ255: 印格带伤食(官杀透+食伤透+印制食伤)->印格成; '
                             '印是格体亦是用神(印制伤兼护官); 破格: 财破印')
                else:
                    _xi_gans = list(guan_gans)   # 命名债: 旧名 _guan_sheng 实为食伤, 已弃用
                    _rule = ('PZZQ255: 官印双全+官有根+无杀透->印格成; 印是格体; 喜神=官; 破格: 财破印')
                facts['ge_cheng'] = {
                    'ge': '印格(官印双全)', 'xi_wx': sorted(set(GAN_WX[g] for g in _xi_gans)),
                    'ti_wx': [yin_wx],
                    'overpower_combo': 6,
                    'zhi_wx': [], 'hua_wx': [],
                    'po_ge': [{'type':'组合','match':'ANY','required':['正财','偏财']}],  # PZZQ258: 印轻逢财(财破印, 财单见即忌)
                    'rule': _rule,
                }
                return facts
        # PZZQ1113: 印轻逢煞=月令印+煞透+印不透. 印是格体(UNVERIFIED: 印轻判据=印不透)
        if sha_gans and not yin_gans:
            yin_wx = facts.get('month_qi_element','') or ''
            # 喜神=煞(煞生印)+印(生身护印, 对照表印绶格喜神含印自身)
            facts['ge_cheng'] = {
                'ge': '印格(印轻逢煞)', 'xi_wx': sorted(set([GAN_WX[sha_gans[0]], yin_wx])),
                'ti_wx': [yin_wx],
                'overpower_combo': 6,
                'zhi_wx': [], 'hua_wx': [],
                'po_ge': [{'type':'组合','match':'ANY','required':['正财','偏财']}],  # PZZQ258: 印轻逢财(财破印, 财单见即忌)
                'rule': 'PZZQ255: 印轻逢煞+印不透->印格成; 印是格体; 喜神=煞(生印)+印(生身); 破格: 财破印',
            }
            return facts
        # PZZQ1113: 印多逢财财透根轻=月令印+财透. 印是格体, 不报印多埋子(UNVERIFIED: 财透根轻判据)
        # 喜神按印轻重分: 印重(财抑太过)=喜财; 印轻(财重无劫救)=贪财破印, 财为忌
        if cai_gans:
            yin_wx = GAN_WX[yin_gans[0]] if yin_gans else (facts.get('month_qi_element','') or '')
            # 印轻重判据: 印透干数>=2 或 印本气根(印五行ben_n)>=2 为印重; 否则印轻
            _yin_ben_n = int(((facts.get('wuxing_power',{}).get('wuxing_power',{}) or {}).get(yin_wx,{}) or {}).get('ben_n',0) or 0)
            _yin_shu = len(yin_gans)
            _yin_ren = (_yin_shu >= 2) or (_yin_ben_n >= 2)
            if _yin_ren:
                # 印重: 喜财(抑印太过). 对照表ZHENG_YIN_001"印多用财, 透财以抑太过, 只要根深, 无防财破"
                #   -> 财在此路径是救应之神, 不是破格忌, 不可列入 po_ge
                _yin_caixi = sorted(set(GAN_WX[g] for g in cai_gans))
                _yin_po = []
            else:
                # 印轻财重: 贪财破印, 财为忌; 喜比劫(制财救印, 对照表"无劫财以救则贪财破印")
                _yin_caixi = [GAN_WX.get(dg, '')]   # 比劫(日主自身五行)=制财救印
                _yin_po = [{'type': '组合', 'match': 'ANY',
                            'required': ['正财', '偏财']}]  # 印轻逢财, 财单见即破印
            facts['ge_cheng'] = {
                'ge': '印格(印多逢财)' if _yin_ren else '印格(印轻逢财)',
                'xi_wx': _yin_caixi,
                'ti_wx': [yin_wx],
                'overpower_combo': 6,
                'zhi_wx': [], 'hua_wx': [],
                'po_ge': _yin_po,
                'rule': ('PZZQ255: 印多重(印多用财抑太过, 无防财破)->喜财, 财不作破格忌'
                         if _yin_ren else
                         'PZZQ255: 印轻财重无劫救->贪财破印, 喜比劫制财救印; 破格: 财破印'),
            }
            return facts
        yin_wx_default = GAN_WX[yin_gans[0]] if yin_gans else (facts.get('month_qi_element','') or '')
        # 喜神按身印强弱分(原典ZHENG_YIN_001):
        #  身印两旺->食伤泄秀为喜; 印浅身轻->伤食层层泄身寒贫(伤食不入喜, 喜印护身)
        _yin_wx_pow = ((facts.get('wuxing_power',{}).get('wuxing_power',{}) or {}).get(yin_wx_default,{}) or {})
        _yin_ben_default = int(_yin_wx_pow.get('ben_n',0) or 0)
        _yin_tou = len(yin_gans)
        _yin_wang = (_yin_tou >= 1 and _yin_ben_default >= 1)   # 印旺=印透且通根
        if _yin_wang:
            _yin_xq = sorted(set(GAN_WX[g] for g in _god_gans('食神')+_god_gans('伤官')))  # 身印旺: 食伤泄秀
        else:
            _yin_xq = [yin_wx_default]   # 印浅身轻: 喜印本身(护身), 不喜伤食泄秀
        # [2026-10-01 PATCH-3d] 段2「带伤食」优先: 官伤并透时食伤碍官, 须印制伤护官, 喜神=印。
        #   原典「朱尚书命 壬为戊制, 不伤官也」—— 印为用神。段3(官星不见)才以食伤泄秀为喜。
        if _d2_dai_shangshi:
            _yin_xq = [yin_wx_default]
            _yin_rule = ('PZZQ255: 印格带伤食(官杀透+食伤透+印制食伤)->喜印(印制伤兼护官); 破格: 财破印')
        else:
            _yin_rule = 'PZZQ255: 印格成; 印是格体; 身印旺食伤泄秀为喜/印浅身轻喜印护身; 破格: 财破印'
        facts['ge_cheng'] = {
            'ge': '印格', 'xi_wx': _yin_xq, 'ti_wx': [yin_wx_default] if yin_wx_default else [],
            'overpower_combo': 6,
            'zhi_wx': [], 'hua_wx': [],
            'po_ge': [{'type':'组合','match':'ANY','required':['正财','偏财']}],
            'rule': _yin_rule,
        }
        return facts


    # 七煞格: 身强七煞逢制. 破格: 七煞逢财无制.
    # 制=食神制 OR 印化. 破格优先于成格.
    qisha_e = facts.get('qisha_entry', {}) or {}
    if qisha_e.get('is_entry'):
        sha_gans = _god_gans('七杀')
        if sha_gans:
            shi_gans = _god_gans('食神')
            yin_gans = _god_gans('正印') + _god_gans('偏印')
            cai_gans = _god_gans('正财') + _god_gans('偏财')
            has_zhi = bool(shi_gans or yin_gans)
            # 原典PI_GUAN_002: 七煞用印(印有情)/食制(煞旺食强身健)/财去印存食(食被制时) — 喜神按制化路径取
            def _qisha_xi():
                _x = []
                if shi_gans:
                    _x += shi_gans          # 食制杀
                if yin_gans:
                    _x += yin_gans          # 印化杀
                if cai_gans:
                    _x += cai_gans          # 财去印存食/借财清格
                return sorted(set(GAN_WX[g] for g in _x))
            # 破格: 财透+无制
            if cai_gans and not has_zhi:
                facts['ge_cheng'] = {
                    'ge': '七煞格(破格)', 'xi_wx': [], 'ti_wx': [],
                    'overpower_combo': 6,
                    'zhi_wx': [], 'hua_wx': [],
                    'po_ge': [{'type':'组合','match':'ANY','required':['正财','偏财']}],
                    'rule': 'PZZQ258: 七煞逢财无制->破格; 杀病照报',
                }
                return facts
            # 成格: 身强+制
            if has_zhi:
                _mz = pillars.get('month', ['',''])[1] if 'month' in pillars else ''
                _dt = dm_tier(facts.get('wuxing_power',{}), dg, _mz, pillars,
                              kong_wang=(facts.get('xunkong') or {}).get('kong_wang'),
                              facts=facts)
                if _dt['tier'] >= 2:
                    sha_wx = GAN_WX[sha_gans[0]]
                    # 成格时按成格路径收窄喜神(原典PI_GUAN_001/002逐案):
                    #  食制路径: 喜神=食(制煞); 印化路径: 喜神=印(化煞);
                    #  食被印制时借财去印存食, 财亦入喜(对照表"煞用财: 财以去印存食")
                    if shi_gans:
                        _qisha_xi = list(shi_gans) + list(cai_gans)   # 食制: 喜食, 兼财(去印存食)
                    else:
                        _qisha_xi = list(yin_gans) + list(cai_gans)   # 印化: 喜印, 兼财(借财清格)
                    facts['ge_cheng'] = {
                        'ge': '七煞格(逢制)', 'xi_wx': sorted(set(GAN_WX[g] for g in _qisha_xi)),
                        'ti_wx': [sha_wx],
                        'overpower_combo': 6,
                        'zhi_wx': [GAN_WX[shi_gans[0]]] if shi_gans else [],
                        'hua_wx': [GAN_WX[yin_gans[0]]] if yin_gans else [],
                        'po_ge': [{'type':'组合','match':'ANY','required':['正财','偏财']}],  # PZZQ258: 财透无制(印化已立, 财单见即破)
                        'rule': 'PZZQ255: 身强七煞逢制(食制/印化)->煞格成; 煞是格体不报杀重病; 破格: 财透无制',
                    }
                    return facts
            # 不成格: 哑巴标签
            # 喜神按原典PI_GUAN_002逐案收窄: 食制喜食(不并财印, 对照表"煞用食制不要露财透印");
            # 无食时印化喜印; 财是破格忌(七煞逢财无制), 不入喜
            _qisha_def_xi = shi_gans if shi_gans else yin_gans
            facts['ge_cheng'] = {
                'ge': '七煞格', 'xi_wx': sorted(set(GAN_WX[g] for g in _qisha_def_xi)),
                'ti_wx': [GAN_WX[sha_gans[0]]] if sha_gans else [],
                'overpower_combo': 6,
                'zhi_wx': [], 'hua_wx': [],
                'po_ge': [{'type':'组合','match':'ANY','required':['正财','偏财']}],  # PZZQ258: 财透无制(财单见即忌)
                'rule': 'PZZQ255: 七煞格; 煞是格体; 喜神=食(制)/印(化); 财是破格忌不入喜; 破格: 财透无制',
            }
            return facts

    # 阳刃格: 阳刃透官煞而露财印, 不见伤官. 刃entry + 官杀透
    # 配合神(官煞)入ti_wx: 官煞制刃是喜神不报杀重病. 比劫不入ti_wx, 比劫夺财病照报.
    yr_e = facts.get('yangren_entry', {}) or {}
    if yr_e.get('is_entry'):
        ks_gans = _god_gans('正官') + _god_gans('七杀')
        sg = _god_gans('伤官')
        if ks_gans and not sg:
            ks_wx = sorted(set([GAN_WX[g] for g in ks_gans]))
            _yr_cai = _god_gans('正财')+_god_gans('偏财')
            _yr_yin = _god_gans('正印')+_god_gans('偏印')
            # 阳刃喜神按原典JIAN_LU_YANG_REN_002/003逐案收窄:
            #  官煞制刃为喜(格体); 印护刃亦喜; 财单用"阳刃用财格所不喜"不入喜
            _yr_xi = list(ks_gans) + list(_yr_yin)
            facts['ge_cheng'] = {
                'ge': '阳刃格', 'xi_wx': sorted(set(GAN_WX[g] for g in _yr_xi)),
                'ti_wx': ks_wx,
                'overpower_combo': 6,
                'zhi_wx': ks_wx,  # 制神: 官煞
                'hua_wx': [],
                'po_ge': [{'type':'缺失','match':'ANY','forbidden':['正官','七杀']}],  # PZZQ258: 阳刃无官煞(缺失才破, 非忌神)
                'rule': 'PZZQ255: 阳刃透官煞露财印不见伤官->刃格成; 官煞制刃是喜神, 印护刃亦喜, 财单用所不喜; 破格: 无官煞',
            }
            return facts

    # 建禄月劫格: 透官逢财印/透财逢食伤/透煞遇制伏.
    # 配合神(官/财食伤/煞)入ti_wx: 配合神是喜神不报病. 比劫不入ti_wx.
    jl_e = facts.get('jianlu_yuejie_entry', {}) or {}
    if jl_e.get('is_entry'):
        guan = _god_gans('正官')
        cai = _god_gans('正财') + _god_gans('偏财')
        shi = _god_gans('食神') + _god_gans('伤官')
        sha = _god_gans('七杀')
        yin = _god_gans('正印') + _god_gans('偏印')
        ti_wx = []
        _jl_xi = []   # 建禄月劫喜神按成格路径逐格取(原典JIAN_LU_YANG_REN_004), 不笼统全并
        if guan and (cai or yin):
            # 禄格用官: 喜官, 又喜财印相随
            ti_wx.append(GAN_WX[guan[0]])
            _jl_xi.extend(cai + yin)
        if cai and shi:
            # 禄劫用财: 须带食伤转劫生财, 喜财+食伤
            for g in cai + shi:
                if GAN_WX[g] not in ti_wx:
                    ti_wx.append(GAN_WX[g])
            _jl_xi.extend(cai + shi)
        if sha and shi:
            # 禄劫用煞: 必须制伏, 喜食伤(制煞)
            if GAN_WX[sha[0]] not in ti_wx:
                ti_wx.append(GAN_WX[sha[0]])
            _jl_xi.extend(shi)
        # 无财官无煞: 原典"无财官而用伤食泄其太过亦为秀气(春木秋金)"-- 喜食伤(泄秀)
        if not guan and not cai and not sha and shi:
            _jl_xi.extend(shi)
        if ti_wx or _jl_xi:
            facts['ge_cheng'] = {
                'ge': '建禄月劫格', 'xi_wx': sorted(set(GAN_WX[g] for g in _jl_xi)),
                'ti_wx': sorted(set(ti_wx)),
                'overpower_combo': 6,
                'zhi_wx': [], 'hua_wx': [],
                'po_ge': [{'type':'缺失','match':'ANY','forbidden':['正官','正财','偏财']}],  # PZZQ258: 无财官/透煞印(缺失才破, 非忌神)
                'rule': 'PZZQ255: 建禄月劫透官逢财印/透财逢食伤/透煞遇制伏/无财官用伤食泄秀->成; 配合神入ti_wx; 破格: 无财官',
            }
            return facts

    # 食神格默认: 月令食神entry但没生财/没带煞 -> 食神格成, 食神是格体
    # 喜神按原典SHI_SHEN_002"单用食神,有财运则富"取透干财; 财不透则喜空(食神自身是格体, 不列喜)
    ss_entry_def = facts.get('shishen_entry', {}) or {}
    if ss_entry_def.get('is_entry'):
        ss_wx_def = facts.get('month_qi_element', '') or ''
        # 制杀太过检查(PZZQ4106"制煞过重同样成病"): 杀透 + 食伤当令(前提) + 杀无本气根/根被六冲 -> 格不成
        # 格不成则ti/xi清空, 由bingyao层判"制杀太过"(有印药则降级); 杀有根能任 -> 正常成格
        # 2026-10-06: 六冲/本气干以排盘权威 facts 为准(combination_facts.liuchong /
        #   hidden_stems[0]), 不再本地查表
        _qs_def = _god_gans('七杀')
        _zhi_list = list(zhis)
        if _qs_def:
            _hd = facts.get('hidden_stems') or {}
            _zhi_ben = {pillars[_pos][1]: (_hd.get(_pos) or [''])[0]
                        for _pos in ('year', 'month', 'day', 'hour')}
            _sha_ben_zhis = [z for z in _zhi_list
                             if ten_god(dg, _zhi_ben.get(z, '')) == '七杀']
            _ch_pairs = [frozenset(_p)
                         for _p in (facts.get('combination_facts', {}).get('liuchong') or [])
                         if len(_p) == 2]
            _sha_root_chong = any(any(z in _k for _k in _ch_pairs)
                                  for z in _sha_ben_zhis)
            # 仅"杀根被六冲(制尽)"判格不成; "杀无根"仍论格成(虚杀/中余气, 层次问题非原局病)
            if _sha_root_chong:
                facts['ge_cheng'] = None
                return facts
        # 喜神按原典逐案取:
        #  食带煞无财->就煞印, 喜煞+印(SHI_SHEN_002"不用财而就煞印, 最为威权显赫")
        #  有财->喜财(SHI_SHEN_002"有财运则富"); 兼官(护食/合煞存财)->喜官
        #  仅煞无财无印->喜煞; 都不透->喜空
        _ss_xi_cai = list(_god_gans('正财')) + list(_god_gans('偏财'))
        _qs_def_xi = _god_gans('七杀')
        _yin_def_xi = _god_gans('正印') + _god_gans('偏印')
        _guan_def_xi = _god_gans('正官')
        # DTS L215(体用章, 准神primary):「提纲食伤财官太旺, 则取年月时上印比为喜神」
        #   -> 提纲(月令)当令之神为食伤 且 食伤成势(本气根>=2 或成局) + 印透干 -> 喜神取印比。
        #   食伤 = 日主所生(_SH: 金生水), 印 = 生日主者。
        #   PZ-0005(戊子癸亥庚寅戊寅) 日主庚金->食伤水; 月令亥=水为食伤当令;
        #     食伤(水)ben_n=2(子亥双本气)成势; 戊偏印两透 -> 喜神=印(土),
        #     与原断「以戊土扶身制伤为用」一致(改前 xi_wx 为空 = 断点)。
        #   注: 枭夺食破格条件不因本条改动 —— 偏印格破格属 GAP-001(DTS「枭」0条/「偏印」0条),
        #   GAP-001 明文「不得因缺primary而在引擎中提升偏印格结论的权威等级」, 故 po_ge 保持原样。
        _SHENG_MAP = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
        _sswx = _SHENG_MAP.get(GAN_WX.get(dg, ''), '')
        _ss_pw = ((facts.get('wuxing_power', {}).get('wuxing_power', {}) or {})
                  .get(_sswx, {}) or {})
        _shi_chengshi = (int(_ss_pw.get('ben_n', 0) or 0) >= 2
                         or int(_ss_pw.get('ju_n', 0) or 0) >= 1)
        # 提纲当令者须是食伤(与日主五行相同的比劫不算「食伤太旺」)
        _ti_gang_tai_wang = bool(ss_wx_def) and _shi_chengshi and (ss_wx_def == _sswx)
        if _qs_def_xi and not _ss_xi_cai:
            # 食带煞无财: 喜煞+印(就煞印, 弃食就煞)
            # 对照表SHI_SHEN_002"不用财而就煞印, 最为威权显赫" -> 印是成格之神;
            #   食既已弃, 枭无所夺, 故此路径不设枭夺食破格
            _ss_xi = sorted(set(GAN_WX[g] for g in _qs_def_xi + _yin_def_xi))
            _ss_po = []
        elif _ti_gang_tai_wang and _yin_def_xi:
            # DTS L215「提纲食伤财官太旺, 则取年月时上印比为喜神」(准神primary)
            _ss_xi = sorted(set(GAN_WX[g] for g in _yin_def_xi))
            _ss_po = [{'type': '组合', 'match': 'ANY', 'required': ['偏印']}]
        elif _ss_xi_cai or _guan_def_xi:
            # 有财或官: 喜财(生财)+官(护食/合煞存财); 食仍为格体, 枭夺食成立
            _ss_xi = sorted(set(GAN_WX[g] for g in _ss_xi_cai + _guan_def_xi))
            _ss_po = [{'type': '组合', 'match': 'ANY', 'required': ['偏印']}]
        elif _qs_def_xi:
            _ss_xi = sorted(set(GAN_WX[g] for g in _qs_def_xi))
            _ss_po = [{'type': '组合', 'match': 'ANY', 'required': ['偏印']}]
        else:
            _ss_xi = []
            _ss_po = [{'type': '组合', 'match': 'ANY', 'required': ['偏印']}]
        facts['ge_cheng'] = {
            'ge': '食神格', 'xi_wx': _ss_xi,
            'ti_wx': [ss_wx_def] if ss_wx_def else [],
            'overpower_combo': 6,
            'zhi_wx': [], 'hua_wx': [],
            'po_ge': _ss_po,  # 枭夺食: 偏印见即夺(就煞印路径除外, 食已弃)
            'rule': 'PZZQ255: 食神格成; 食神是格体; 喜神=财(有财则富)/煞印(带煞就煞印)/官(护食); 破格: 枭夺食',
        }
        return facts

    # 伤官格默认: 月令伤官entry但没佩印/没带煞 -> 伤官格成, 伤官是格体
    # 喜神按原典SHANG_GUAN_005"伤官用财"取透干财; 伤官见官(非金水)原断无喜忌时跳过
    sg_entry_def = facts.get('shangguan_entry', {}) or {}
    if sg_entry_def.get('is_entry'):
        sg_wx_def = facts.get('month_qi_element', '') or ''
        # 喜神按原典SHANG_GUAN_005逐案取:
        #  伤官用财->喜财; 金水伤官要见官->喜官; 身弱用印->喜印; 伤多用煞印->喜煞+印
        _sg_cai = list(_god_gans('正财')) + list(_god_gans('偏财'))
        _sg_guan = _god_gans('正官')
        _sg_sha = _god_gans('七杀')
        _sg_yin = _god_gans('正印') + _god_gans('偏印')
        _jsshui_sg = (dg in ('庚','辛','壬','癸')) or (sg_wx_def in ('金','水'))
        _sg_xi = list(_sg_cai)
        if _sg_guan and _jsshui_sg:
            _sg_xi += list(_sg_guan)   # 金水伤官要见官, 官亦入喜
        if _sg_sha and _sg_yin:
            _sg_xi += list(_sg_sha) + list(_sg_yin)   # 伤多用煞印: 喜煞+印
        elif _sg_yin:
            _sg_xi += list(_sg_yin)   # 伤官用印(身弱): 喜印
        _sg_xi = sorted(set(GAN_WX[g] for g in _sg_xi))
        # 破格两条(对照表SHANG_GUAN_003/004/006/007):
        #  1) 非金水而见官 -> 伤官见官(正官单见即破, 金水伤官例外见官为喜)
        #  2) 生财带煞 -> 财且煞并见才破(财本身是"伤官用财"之喜, 单见不破)
        _sg_po = []
        if _sg_guan and not _jsshui_sg:
            _sg_po.append({'type': '组合', 'match': 'ANY', 'required': ['正官']})
        _sg_po.append({'type': '组合', 'match': 'ALL', 'required': ['正财', '偏财', '七杀']})
        facts['ge_cheng'] = {
            'ge': '伤官格', 'xi_wx': _sg_xi,
            'ti_wx': [sg_wx_def] if sg_wx_def else [],
            'overpower_combo': 6,
            'zhi_wx': [], 'hua_wx': [],
            'po_ge': _sg_po,  # 破格: 伤官见官(非金水)/生财带煞
            'rule': 'PZZQ255: 伤官格成; 伤官是格体; 喜神=财(用财)/官(金水见官)/印(身弱)/煞印(伤多用煞印); 破格: 伤官见官(非金水)/生财带煞',
        }
        return facts


    # ---- 以下为原行 443-501「专旺/从格兜底段」，PATCH-GAP11 已移至函数末尾（所有正格分支之后、最终 None 兜底之前）----
    # 专旺/从格兜底(P0接线v3): 正格不成时才看专旺/从格
    if not facts.get('ge_cheng') or facts['ge_cheng'].get('ge','') == '无格':
        try:
            from engines.common.special_pattern import build_special_patterns
            wp = facts.get('wuxing_power', {}) or {}
            sp = _purge(_special_of(facts.get('special')))
            if sp.get('zhuanwang'):
                dm_wx = GAN_WX.get(dg, '')
                facts['ge_cheng'] = {
                    'ge': sp['zhuanwang'], 'xi_wx': [],
                    'ti_wx': [dm_wx],
                    'overpower_combo': 6,
                    'zhi_wx': [], 'hua_wx': [],
                    'po_ge': [],
                    'rule': '专旺/从格兜底(P0): 正格不成->专旺格; ti_wx=[日主五行]',
                }
                return facts
            # PATCH-GAP11 (2026-09-30): 从格兜底原读 sp['cong_type']/sp['cong_state']，
            # 但 build_special_patterns 只把结果放进 out['patterns'] 数组(每项含 name/state)，
            # 从未写顶层 cong_type/cong_state —— 恒为 None，致本段永不执行、ge_cheng 落 None。
            # 改为从 patterns 数组取首条「从*」且 state 为 CONFIRMED/CANDIDATE 的项。
            # PATCH-GAP11b (2026-10): 排除 special_pattern.py L572「从杀格」CANDIDATE。
            #   L572 条件含「日主无根或根极弱」——「根极弱」是工程自造词, 全库无切片,
            #     且 dm_ben_eff<=1 / yin_ben_eff<=1 两个整数阈值亦无 primary 依据(程度分级需案例反标定)。
            #   L565「从旺格」CANDIDATE 与 L389/402/408 各路有结构化条件, 不在此排除范围。
            #   => L572 产出的 CANDIDATE 仍留在 sp['patterns'] 候选层可查, 但不进正式格层。
            # 准神依据: DTS L420(SHUAI.003)「日主孤立无气, 无地人元, 绝无一毫生扶之意, 财官强甚, 乃为真从也」
            #   —— 只给「无气」定性, 未给「根极弱」量化门槛, 故不能据以定阈值。
            # 同族 TODO: 9a(阈值无据) / 9b(本处准入) / 9c(GAP11 来源), 三者耦合。
            _cong_pat = next((p for p in (sp.get('patterns') or [])
                             if p.get('state') in ('CONFIRMED', 'CANDIDATE')
                             and str(p.get('name', '')).startswith('从')
                             and not (p.get('state') == 'CANDIDATE'
                                      and p.get('name') == '从杀格')), None)
            if _cong_pat and not sp.get('cong_type'):
                sp = dict(sp)
                sp['cong_type'] = _cong_pat.get('name')
                sp['cong_state'] = _cong_pat.get('state')
            if sp.get('cong_type') and sp.get('cong_state') in ('CONFIRMED', 'CANDIDATE'):
                # PATCH-GAP11b 同源: 顶层直写的从杀格 CANDIDATE 同样不入正式格层(L572 来源无切片依据)
                if sp.get('cong_type') == '从杀格' and sp.get('cong_state') == 'CANDIDATE':
                    sp = dict(sp)
                    sp['cong_type'] = None
                    sp['cong_state'] = None
            if sp.get('cong_type') and sp.get('cong_state') in ('CONFIRMED', 'CANDIDATE'):
                # 从格格体五行=所从之神
                _cong_wx_map = {'从杀格': 'gs_wx', '从官格': 'gs_wx',
                                '从财格': 'cai_wx', '从儿格': 'ss_wx'}
                _cong_key = _cong_wx_map.get(sp['cong_type'], '')
                _cong_wx = ''
                if _cong_key == 'gs_wx':
                    _cong_wx = facts.get('wuxing_power', {}).get('_gs_wx', '')
                elif _cong_key == 'cai_wx':
                    _cong_wx = facts.get('wuxing_power', {}).get('_cai_wx', '')
                elif _cong_key == 'ss_wx':
                    _cong_wx = facts.get('wuxing_power', {}).get('_ss_wx', '')
                # 从格所从五行从wp反推
                _wp = facts.get('wuxing_power', {}) or {}
                _dm_wx0 = GAN_WX.get(dg, '')
                _sh, _ke = {'木':'火','火':'土','土':'金','金':'水','水':'木'}, {'木':'土','土':'水','水':'火','火':'金','金':'木'}
                _sheng_me, _ke_me = {'木':'水','火':'木','土':'火','金':'土','水':'金'}, {'木':'金','金':'火','火':'水','水':'土','土':'木'}
                if sp['cong_type'] in ('从杀格','从官格'):
                    _cong_wx = _ke_me.get(_dm_wx0, '')
                    # PZZQ5000"从杀忌食伤"; 财生煞顺旺势为喜
                    _xi_cong = [_ke.get(_dm_wx0, '')]
                elif sp['cong_type'] == '从财格':
                    _cong_wx = _ke.get(_dm_wx0, '')
                    # PZZQ4943"原有食伤则能化比劫而生财": 食伤化劫生财为喜
                    _xi_cong = [_sh.get(_dm_wx0, '')]
                elif sp['cong_type'] == '从儿格':
                    _cong_wx = _sh.get(_dm_wx0, '')
                    # PZZQ4960"以见财为美": 财为喜
                    _xi_cong = [_ke.get(_dm_wx0, '')]
                else:
                    _xi_cong = []
                facts['ge_cheng'] = {
                    'ge': '从格(' + sp['cong_type'] + ')', 'xi_wx': sorted(set(w for w in _xi_cong if w)),
                    'ti_wx': [_cong_wx] if _cong_wx else [],
                    'overpower_combo': 6,
                    'zhi_wx': [], 'hua_wx': [],
                    'po_ge': [],
                    'rule': '专旺/从格兜底(P0): 正格不成->从格; ti_wx=所从之神五行; 喜神=从财食伤/从杀从官从儿财(PZZQ4943/4960)',
                }
                return facts
        except Exception:
            pass
    facts['ge_cheng'] = None
    return facts

def apply_he_po_ge(facts: Dict[str, Any]) -> Dict[str, Any]:
    """规则2(冲解合破格): 月令支被"存活的相邻六冲"所冲, 且月令五行∈ti_wx∪xi_wx(格体/喜)
    -> 破格: ti_wx/xi_wx清空(不重新定格; 重新定格属格局回溯链, 登记下一轮).
    判据边界: 仅冲月令核心才破格; 冲非月令边缘支(归规则3/4)、被暗合解之冲(chong_canceled)不破.
    原典: DT-0380 卯酉冲破亥卯未印局=凶; PZ-0034/PZ-0279 月令未被真正冲, 不破."""
    gc = facts.get('ge_cheng')
    if not gc:
        return facts
    cf = facts.get('combination_facts') or {}
    rs = cf.get('resolved') or {}
    mz = facts.get('month_branch', '')
    mwx = facts.get('month_qi_element', '')
    ti = set(gc.get('ti_wx') or [])
    xi = set(gc.get('xi_wx') or [])
    if mwx in (ti | xi) and any(mz in p for p in rs.get('chong_survive', [])):
        gc['ti_wx'] = []
        gc['xi_wx'] = []
        gc.setdefault('po_ge', []).append({'type': '冲月令破格', 'match': 'ANY', 'required': [mwx]})
    return facts

def is_xix_shen(facts: Dict[str, Any], wx: str, combo: int) -> bool:
    """wx五行是否为成格喜神且未过旺. 是->泄气/克泄病应过滤(不报).
    过旺例外: combo>=overpower_combo 仍可报."""
    gc = facts.get('ge_cheng')
    if not gc:
        return False
    if wx not in (gc.get('xi_wx') or []):
        return False
    thr = int(gc.get('overpower_combo', 6))
    if combo >= thr:
        return False
    return True


# ==========================================================================
# ti_wx 归位层  (L4 顺序: build_ge_cheng -> apply_he_po_ge -> normalize_ti_wx)
# 规则钉死, 同源 scripts/ti_wx_impact.rule_ti_wx (DTS L210 准神 + PZZQ L4652)
# ==========================================================================
_GE_BODY_SHEN = {
    '正官格': {'正官'},
    '七煞格': {'七杀'}, '七煞格(逢制)': {'七杀'},
    '财格': {'正财', '偏财'},
    '印格': {'正印', '偏印'}, '印格(官印双全)': {'正印', '偏印'},
    '印格(印轻逢煞)': {'正印', '偏印'}, '印格(印多逢财)': {'正印', '偏印'},
    '印格(印轻逢财)': {'正印', '偏印'},
    '食神格': {'食神'}, '食神格(带煞无财)': {'食神'},
    '伤官格': {'伤官'}, '伤官格(佩印)': {'伤官'}, '伤官格(带煞无财)': {'伤官'},
}
_TRANSPARENT_GE = {'建禄月劫格', '阳刃格'}
_TOUGAN_SHEN = {'正官', '七杀', '正财', '偏财', '食神', '伤官'}


def normalize_ti_wx(facts: Dict[str, Any]) -> Dict[str, Any]:
    """ti_wx 归位 (必须接在 apply_he_po_ge 之后; 顺序反了会给破格执行器喂新输入).

    ① 六格: 月令本气十神属格体 -> ti_wx=[月令五行]; 不属 -> 不动(保持 build_ge_cheng).
    ② 建禄月劫/阳刃: ti_wx=月令透干(年/日/时)之 官/财/食伤/煞 五行; 无透干 -> [].
       依据 DTS L210「建禄月劫羊刃, 当看月令中人元透于天干者取格」+ PZZQ L4652 同向.
    ③ 从格/化气/专旺/食神制杀: 本层不动(现状已赋所从之神/格体).
    破格盘(ge 含 '(破格)')一律跳过, 不重赋格体.
    """
    gc = facts.get('ge_cheng')
    if not isinstance(gc, dict):
        return facts
    ge = gc.get('ge') or ''
    if '(破格)' in ge:
        return facts
    pillars = facts.get('pillars') or {}
    dg = facts.get('day_stem') or ''
    if not dg or not all(k in pillars for k in ('year', 'month', 'day', 'hour')):
        return facts

    if ge in _TRANSPARENT_GE:
        gods = []
        for k in ('year', 'day', 'hour'):       # 月干=月令本气已含, 不取
            g = pillars[k][0]
            if g == dg:
                continue
            if ten_god(dg, g) in _TOUGAN_SHEN:
                gods.append(GAN_WX[g])
        gc['ti_wx'] = sorted(set(gods))
        return facts

    body = _GE_BODY_SHEN.get(ge)
    if body is None:
        return facts                            # 从/化/专旺/食神制杀等, 不动
    # 2026-10-06: 月支本气干以排盘权威 facts['hidden_stems'] 为准(缺时兜底本地表)
    _hd = facts.get('hidden_stems') or {}
    _mzh = pillars['month'][1]
    _mhd = _hd.get('month') or []
    mben = _mhd[0] if _mhd else ZHI_BEN_GAN.get(_mzh, '')
    if mben and ten_god(dg, mben) in body:
        gc['ti_wx'] = [GAN_WX[mben]]
    return facts
