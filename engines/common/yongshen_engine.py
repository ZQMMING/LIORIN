# -*- coding: utf-8 -*-
"""160-D 用神病机收敛引擎 V2.4(布尔+多态枚举决策树, 非 score/非黑盒裁决)。

primary 主用神(1行)+secondary 喜神/相神+avoid 忌神。
特殊格局顺逆分流 / CANDIDATE 真假从(印叠透或得载留正格, 无根从顺; 从儿归财、火财吐秀、水财寒湿顺财)
> 仲冬仲夏调候(制杀调候合一; 夏水透看印源/库根, 水涸培金) > 官杀制化(中和杀印相生/身根足食制)
> 通关(成势×成势, 财印战放宽到透根) > 专旺日支归垣用财 > 印重财破(官杀不透)
> 衰极印绝食伤财成势顺生(类从儿) > 财重分财/食伤泄过 > 扶抑(财当令滋弱杀、官透用官、虚杀食制)。
cs 成势=当令旺/本气>=2/成局/透干>=2且有气; 专旺食伤顺泄须得比劫成势之生。
吉凶前端拦截, 本层只给真实取用结构; 不接 production_entry。
"""
import re
from engines.common.root_grade_boundary import to_root_grade
WUXING='木火土金水'
SHENG={'木':'火','火':'土','土':'金','金':'水','水':'木'}
KE={'木':'土','土':'水','水':'火','火':'金','金':'木'}
SHENG_ME={v:k for k,v in SHENG.items()}; KE_ME={v:k for k,v in KE.items()}
WX={'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
WANG_TIER=('旺极','太旺','旺'); SHUAI_TIER=('衰极','太衰','衰')
# V7.5 tier2五档集合(从原著推导, 档位数由下游需求决定)
WANG_TIER2=('从强','旺'); SHUAI_TIER2=('衰','从弱')
WINTER=('亥','子','丑'); SUMMER=('巳','午','未'); DRY_BRANCH=('午','未','戌'); MIDWINTER=('亥','子'); MIDSUMMER=('巳','午')
BRANCH_WX={'子':'水','亥':'水','寅':'木','卯':'木','巳':'火','午':'火','申':'金','酉':'金','辰':'土','戌':'土','丑':'土','未':'土'}

def _ten_wx(dmw):
    return {'bi': dmw,
            'yin': [x for x in WUXING if SHENG[x]==dmw][0],
            'shi': SHENG[dmw], 'cai': KE[dmw],
            'guan': [x for x in WUXING if KE[x]==dmw][0]}

def build_yongshen_engine(pillars, facts, wuxing_power, spectrum, special, climate):
    dm=facts['day_stem']; dmw=WX[dm]; t=_ten_wx(dmw)
    tier=spectrum.get('spectrum') if isinstance(spectrum,dict) else spectrum
    # V7.0 tier2: 从wang_shuai(月令维度)+qiang_ruo(根气+党众维度)布尔枚举推导, 不替换旧tier(LEGACY_REFERENCE)
    _ws = spectrum.get('wang_shuai') if isinstance(spectrum,dict) else None
    _qr = spectrum.get('qiang_ruo') if isinstance(spectrum,dict) else None
    if _ws and _qr:
        _in_season = bool(_ws.get('in_season'))
        _qr_eff = _qr.get('effective') or _qr.get('raw') or '弱'
        _qr_strong = _qr_eff in ('强',)
        _failure = _qr.get('failure_reasons') or []
        _root_class = _qr.get('root_class') or 'NONE'
        _support_count = _qr.get('support_stem_count') or 0
        _has_heavy_root = _root_class == 'HEAVY'
        _has_any_root = _root_class in ('HEAVY', 'LIGHT')
        # V7.4 tier2五档映射表(从原著推导, 档位数由下游需求决定):
        # 从强/专旺: 得令+重根+党众>=2(《子平真诠》得时为旺党众为强, 旺极/太旺合并)
        # 旺: 得令+强(普通)
        # 中和: 得令+弱(普通) 或 失令+强(衰而强)
        # 衰: 失令+弱(有根) 或 得令+水旺木浮(根被漂浮)
        # 从弱/从格: 失令+无根+无帮扶(衰极/太衰合并)
        # V7.9 细化映射表: 用support_count区分"旺而弱""衰而强"边界
        # 得令+弱+党众>=2 -> 旺(得令+党众多能撑, 虽根轻)
        # 失令+强+党众>=2 -> 旺(失令但重根+党众多, 衰而强接近旺)
        if _in_season and _qr_strong and _has_heavy_root and _support_count >= 2:
            tier2 = '从强'
        elif _in_season and _qr_strong:
            tier2 = '旺'
        elif _in_season and not _qr_strong and 'D水旺木浮' in _failure:
            tier2 = '衰'
        elif _in_season and not _qr_strong and _support_count >= 2:
            tier2 = '旺'  # 得令+党众多, 虽根轻但党众能撑
        elif _in_season and not _qr_strong:
            tier2 = '中和'
        elif not _in_season and _qr_strong:
            tier2 = '中和'  # V7.9 回退: 失令+强保持中和, 衰而强不强行判旺
        elif not _in_season and not _qr_strong and not _has_heavy_root:
            tier2 = '从弱'
        else:
            tier2 = '衰'
    else:
        tier2 = tier
    wpd=(wuxing_power or {}).get('wuxing_power',{})
    def d(w): return wpd.get(w) or {}
    def ben(w): return d(w).get('ben_n',0)
    def stem(w): return d(w).get('stem_n',0)
    def ling(w): return d(w).get('ling_state')
    def cs(w):
        return ling(w)=='旺' or to_root_grade(ben(w)) in ['禄刃','长生'] or d(w).get('ju_n',0)>=1 or (stem(w)>=2 and (ling(w) in ('旺','相') or to_root_grade(ben(w)) in ['禄刃','长生','库']))
    def qi(w):
        return to_root_grade(ben(w)) in ['禄刃','长生','库'] or stem(w)>=1 or ling(w) in ('旺','相')

    cong=(special.get('cong_type') or '').strip(); cong_state=(special.get('cong_state') or '').strip()
    zw_raw=(special.get('zhuanwang') or '').strip(); zw_state=(special.get('zhuanwang_state') or '').strip()
    zw=zw_raw  # 顺用/逆用不按CONFIRMED标签, 而按官杀财'有气与否'在专旺块内逐格分流(虚透根绝=激旺顺用, 坐库/长生有根或财生=逆用官杀)
    hua=(special.get('hua_qi') or '').strip()
    hua_state=(special.get('hua_qi_state') or '').strip(); hua_conf=bool(hua) and hua_state=='CONFIRMED'
    lq=special.get('liangqi') or None
    # V5.7: 如果zw为None，但lq.get('name')包含专旺格类型，则设置zw(专旺格识别在格局层, 不在special.zhuanwang)
    if not zw and lq and lq.get('name'):
        _zw_names = ['曲直', '炎上', '稼穑', '从革', '润下']
        for _zn in _zw_names:
            if _zn in lq.get('name'):
                zw = lq.get('name')
                break
    conf_cong=bool(cong) and 'CONFIRMED' in cong_state
    cand_cong=bool(cong) and not conf_cong
    spec_name=cong or zw or hua or (lq.get('name') if lq else '正格')

    primary=None; secondary=[]; avoid=[]; paths=[]; notes={}; _bijie_cai_avoid=False
    def P(w,path,note):
        nonlocal primary
        if w and w in WUXING and primary is None:
            primary=w; paths.append(path); notes[w]=note
    def S(w,note=''):
        if w and w in WUXING and w!=primary and w not in secondary:
            secondary.append(w); notes.setdefault(w,note)
    def A(*ws):
        for w in ws:
            if w and w in WUXING and w not in avoid: avoid.append(w)
    # V7.23 PATCH: 保留十干级调候候选（不降级为五行），同时派生五行级hou（保持现有逻辑）
    # 十干是Fact，五行是Projection。stem不允许被element覆盖。
    _climate_candidates_raw = climate.get('climate_candidates') or []
    hou_stem = [{'stem': c.get('stem'), 'element': WX.get(c.get('stem'), ''), 'priority': c.get('order', 99)}
                for c in _climate_candidates_raw if c.get('stem') in WX]
    hou = [c['element'] for c in hou_stem]  # 原hou逻辑不变，保持向后兼容
    # V7.23 P2: 给调候候选增加applicability字段(区分"冲突"与"不适用")
    _ZW_WX = {'炎上':'火','曲直':'木','从革':'金','润下':'水','稼穑':'土'}
    _KE = {'火':'水','木':'金','金':'火','水':'土','土':'木'}
    for _c in hou_stem:
        _wx = _c.get('element', '')
        _ap = 'APPLICABLE'
        _ap_r = '正格/普通命局, 调候轨适用'
        for _zn, _zw in _ZW_WX.items():
            if _zn in (zw or ''):
                if _KE.get(_zw) == _wx:
                    _ap = 'INAPPLICABLE'
                    _ap_r = _zn + '格可顺不可逆, ' + _wx + '为忌(调候不适用)'
                elif _zw == _wx:
                    _ap = 'CONDITIONAL'
                    _ap_r = _zn + '格, ' + _wx + '需泄秀(条件适用)'
                break
        if _ap == 'APPLICABLE':
            if '从财' in (cong or ''):
                if _wx in ('木', '火'):
                    _ap = 'INAPPLICABLE'
                    _ap_r = '从财格忌印比帮身(调候不适用)'
            elif '从杀' in (cong or ''):
                _ap = 'INAPPLICABLE'
                _ap_r = '从杀格忌食伤制杀(调候不适用)'
            elif '从儿' in (cong or ''):
                _ap = 'INAPPLICABLE'
                _ap_r = '从儿格忌印克食伤(调候不适用)'
        _c['applicability'] = _ap
        _c['applicability_reason'] = _ap_r
    mz=pillars['month'][1]; dz=pillars['day'][1]
    brs=[pillars[k][1] for k in ('year','month','day','hour')]
    cold=(mz in WINTER) or (ling('水')=='旺' and not qi('火'))
    hot=(mz in SUMMER) or (ling('火')=='旺' and not qi('水'))
    fire_branches=sum(1 for b in brs if b in ('巳','午','未','戌'))
    dry=(dmw=='土' and fire_branches>=2 and ben('水')==0 and mz not in ('亥','子','丑'))
    chong_branches=set()
    for pr in (facts.get('combination_facts',{}) or {}).get('liuchong',[]):
        if len(pr)==2: chong_branches.update(pr)
    # 假化有情: 合神真(化气门已判) 且 化神当令(月令本气=化神) 或 化神成势(ben>=2 且透化神或透生化之神)
    hua_hwx=next((w for w in WUXING if hua and (('化'+w) in hua or w in hua)), None)
    hua_youqing=False
    if hua_hwx and not hua_conf:
        _sh=SHENG_ME.get(hua_hwx)
        # V4.4: 化神被克制则不判假化有情(如QT-0040戊子庚申乙丑壬午: 化神金但地支午火克金)
        # 注意: ben()/cs()/ling()参数是十神类型不是五行，改用wuxing_power检查克化神的五行力量
        _ke_hua = KE.get(hua_hwx)
        _ke_hua_pow = wuxing_power.get('wuxing_power', {}).get(_ke_hua, {}) if _ke_hua else {}
        _hua_suppressed = bool(_ke_hua) and (
            int(_ke_hua_pow.get('ben_n', 0)) >= 1 or
            int(_ke_hua_pow.get('ju_n', 0)) >= 1 or
            _ke_hua_pow.get('ling_state', '') in ('旺', '相') or
            int(_ke_hua_pow.get('stem_n', 0)) >= 1
        )
        if not _hua_suppressed:
            if (BRANCH_WX.get(mz)==hua_hwx) or \
               (to_root_grade(ben(hua_hwx)) in ['禄刃','长生'] and (stem(hua_hwx)>=1 or (_sh and stem(_sh)>=1))) or \
               (stem(hua_hwx)>=1 and to_root_grade(ben(hua_hwx)) in ['禄刃','长生','库'] and ben(dmw)==0 and ben(t['yin'])==0):
                hua_youqing=True

    yin_load = stem(t['yin'])>=2 or (stem(t['yin'])>=1 and (to_root_grade(ben(t['yin'])) in ['禄刃','长生','库'] or to_root_grade(ben(t['guan'])) in ['禄刃','长生','库'])) \
               or (stem(t['yin'])>=1 and stem(t['guan'])>=2)
    # 假从回正格: 日主有原始本气同字根(真从须无根)。用l0原始藏干本气判定, 三合三会/六合归化
    # 不抹煞日主自坐身库本根(申酉戌会金不夺戊土坐戌身库), 避免身库被会局误判真从。
    _ganwx={}
    for _gs,_wx in [('甲乙','木'),('丙丁','火'),('戊己','土'),('庚辛','金'),('壬癸','水')]:
        for _c in _gs: _ganwx[_c]=_wx
    _pks=('year','month','day','hour')
    # 完整三合/三会化神为财或官杀时, 局内他柱(非日支自坐)日主本气根从合化, 不回正格
    _hhbr=set()
    _cfy=facts.get('combination_facts',{}) or {}
    for _items in (_cfy.get('sanhe',[]),_cfy.get('sanhui',[])):
        for _it in _items:
            _mm=re.match(r'^([子丑寅卯辰巳午未申酉戌亥])([子丑寅卯辰巳午未申酉戌亥])([子丑寅卯辰巳午未申酉戌亥]).*?([金木水火土])',str(_it))
            if not _mm: continue
            _gg=_mm.groups()
            if _gg[3] in (t['cai'],t['guan']):
                for _br in _gg[:3]:
                    if BRANCH_WX.get(_br)==dmw: _hhbr.add(_br)
    raw_ben_branch=[]
    for _i,_k in enumerate(_pks):
        _hs=facts.get('hidden_stems',{}).get(_k) or []
        _br=brs[_i]
        if _hs and _ganwx.get(_hs[0])==dmw and (_k=='day' or _br not in _hhbr):
            raw_ben_branch.append(_br)
    dm_ben_real=bool(raw_ben_branch)
    if dmw=='土':
        # 辰丑湿土蓄水藏金: 本气根仅在辰丑湿土、满盘亥子/壬癸水、无丙丁巳午火印与未戌燥土,
        # 则湿土从水势(从财)不作日主根; 未戌燥土/火印帮身方为真根(辰丑湿土从水, 未戌燥土帮身)。
        zao=any(b in ('未','戌') for b in raw_ben_branch) or any(b in ('巳','午') for b in brs)
        huo=stem('火')>=1 or any(b in ('巳','午') for b in brs)
        water=stem('水')>=1 or any(b in ('亥','子') for b in brs)
        if not zao and not huo and water: dm_ben_real=False
    # 月令本气为印且当令有本气根=提纲托身, 印虽不透亦不从(待运透比劫; L1436丙生卯月卯印本气, 丙午比劫破酉封诰吉, 不从官)
    _yueyin_tuoshen = BRANCH_WX.get(mz)==t['yin'] and to_root_grade(ben(t['yin'])) in ['禄刃','长生','库']
    gen_zheng = yin_load or dm_ben_real or _yueyin_tuoshen or stem(t['bi'])>=1  # 比劫透干帮身亦不从
    zw_conf = bool(zw) and 'CONFIRMED' in (zw_state or '')
    zw_active = zw and (zw_conf or not gen_zheng)  # 真专旺或假专旺无印比帮身才触发专旺路径

    # 印比双透但皆虚透(无本气、无中余气根)而财成势(ben>=3/成局)克尽者, 虚印比不能留正格(L1618)
    _yin_bi_xu = stem(t['yin'])>=1 and stem(t['bi'])>=1 and ben(t['yin'])==0 \
        and d(t['yin'])['zhong_n']+d(t['yin'])['yu_n']==0 and ben(t['bi'])==0 \
        and d(t['bi'])['zhong_n']+d(t['bi'])['yu_n']==0 and (to_root_grade(ben(t['cai'])) == '禄刃' or cs(t['cai']))
    cong_shun = (conf_cong or (cand_cong and not gen_zheng)) and stem(t['yin'])<2 \
        and (not (stem(t['yin'])>=1 and stem(t['bi'])>=1) or _yin_bi_xu)
    zheng=(not zw_active) and (not lq) and (not hua_conf) and (not hua_youqing) and (not cong_shun)

    # ---------- A 化气 / 从顺 / 专旺 / 成象 ----------
    # V4.7: 直接用BRANCH_WX检查地支中是否有克化神的五行(QT-0040化金气格但午火克金)
    _hua_ke = KE.get(hua_hwx) if hua_hwx else None
    _hua_suppressed = bool(_hua_ke) and any(BRANCH_WX.get(b) == _hua_ke for b in brs)
    if hua:  # V7.1 化气格识别即触发(真化/假化均走化气路径, 原典一格一议; 克化神者在路径内作忌, 不阻断化气格成立)
        hwx=hua_hwx if hua_hwx else next((w for w in WUXING if ('化'+w) in hua or w in hua), None)
        if hwx:
            # 《子平真诠》化气: 唯真化(CONFIRMED, 日主无根无印、化神当令成局)方以化神为用;
            # 喜化神与生扶化神(化神之印), 化神旺顺泄其秀; 忌克化神者与生日主返本之印;
            # 严禁把化神(甲己化土则土为日主财、戊癸化火则火为日主财等)误列忌神
            P(hwx,'HUA_QI','真化气格以化神为用')
            _yh=SHENG_ME.get(hwx)
            if _yh and _yh!=hwx: S(_yh,'生扶化神(化神之印)')
            if SHENG.get(hwx) not in (hwx,_yh): S(SHENG[hwx],'化神旺顺泄其秀')
            for _w in (KE.get(hwx), SHENG_ME.get(dmw)):
                if _w and _w!=hwx and _w!=_yh: A(_w)
    # V4.30: 从财/从官/从杀格有印比透干且有根(本气/中气/余气)时不走从格(假从真不化)，从儿格不受此限
    _yinbi_rooted = (stem(t['yin'])>=1 and (to_root_grade(ben(t['yin'])) in ['禄刃','长生','库'] or cs(t['yin']) or ling(t['yin']) in ('旺','相') or int(d(t['yin']).get('zhong_n',0))+int(d(t['yin']).get('yu_n',0))>=1)) \
                     or (stem(t['bi'])>=1 and (to_root_grade(ben(t['bi'])) in ['禄刃','长生','库'] or cs(t['bi']) or ling(t['bi']) in ('旺','相') or int(d(t['bi']).get('zhong_n',0))+int(d(t['bi']).get('yu_n',0))>=1))
    _skip_cong = _yinbi_rooted and cong and ('从财' in cong or '从官' in cong or '从杀' in cong or '从煞' in cong)
    if (cong or cong_shun) and not _skip_cong:
        if '从财' in cong:
            # 从财格：顺财为用，喜财+食伤，忌印比+官杀(官杀泄财生印逆势)
            # 原典L250辛卯辛卯辛卯辛卯: 从财格丁亥运生火克金即亡其师, 官杀为忌
            if t['cai']=='水' and (mz in ('亥','子','丑','辰') or cold):
                P(t['cai'],'CONG_SHUN','寒湿虚身从水财，顺其寒湿水势'); S(t['shi'],'金食伤生水')
            elif qi(t['shi']):
                P(t['shi'],'CONG_SHUN','从财喜食伤吐秀生财(从财必要食伤)'); S(t['cai'],'顺财')
            else:
                P(t['cai'],'CONG_SHUN','从财无食伤，顺财'); S(t['shi'],'食伤生财')
            # V7.13 从财格官杀忌神: 真从财格(日主完全无根无印无透干印)+食伤无力时, 官杀泄财生印逆势为忌(原典L250丁亥运生火克金即亡其师; 假从财格如L1122日主有微根, 官杀不为忌)
            # V7.26: 从special中提取根气有效字段, 避免裸引用
            _dm_ben_eff = (special or {}).get('dm_ben_eff', 0)
            _yin_ben_eff = (special or {}).get('yin_ben_eff', 0)
            _yin_stem = (special or {}).get('yin_stem', 0)
            if _dm_ben_eff == 0 and _yin_ben_eff == 0 and _yin_stem == 0 and not qi(t['shi']) and not cs(t['shi']):
                A(t['guan'], '真从财格无食伤制官杀，官杀泄财生印逆势为忌(原典L250丁亥运生火克金)')
        elif '从官' in cong or '从杀' in cong or '从煞' in cong:
            P(t['guan'],'CONG_SHUN','从官杀顺官杀'); S(t['cai'],'财生官杀')
        elif '从儿' in cong:
            # 从儿格：财星有根/透干用财，财星太弱用食伤顺泄; 忌官杀(官杀克食伤儿)
            _cai_usable = to_root_grade(ben(t['cai'])) in ['禄刃','长生','库'] or stem(t['cai'])>=1 or cs(t['cai'])
            if _cai_usable:
                P(t['cai'],'CONG_SHUN','从儿儿又见儿，食伤生财，以财为用'); S(t['shi'],'顺食伤格神')
            else:
                P(t['shi'],'CONG_SHUN','从儿格财星太弱(无根无透)，顺食伤泄秀为用'); S(t['cai'],'食伤生财(待运)')
            A(t['guan'],'从儿格忌官杀(官杀克食伤儿, 如L2080亥运水不敌火反生木助火吐血而亡)')
        elif '从势' in cong or '从强' in cong:
            P(t['cai'],'CONG_SHUN','从势顺势')
        A(t['yin'],t['bi'])
    zw_conf = bool(zw) and 'CONFIRMED' in (zw_state or '')
    if zw:  # 专旺格识别即触发(真专旺/假专旺均走专旺路径, 原典一格一议)
        gw=t['guan']; cw=t['cai']; sw=t['shi']; yw=t['yin']
        og=[pillars[k][0] for k in ('year','month','hour')]
        gan_yang = dm in '甲丙戊庚壬'
        _yang='甲丙戊庚壬'; _yin='乙丁己辛癸'; _seq='木火土金水'
        sha_gan = _yang[_seq.index(gw)] if gan_yang else _yin[_seq.index(gw)]
        has_sha = sha_gan in og
        guan_rooted = to_root_grade(ben(gw)) in ['禄刃','长生','库'] or cs(gw) or ling(gw) in ('旺','相')
        cai_zai = has_sha and stem(gw)>=1 and (to_root_grade(ben(cw)) in ['禄刃','长生','库'] or any(BRANCH_WX.get(b)==cw for b in brs))   # 阳杀得财方支归垣之载(曲直庚得辰载, 辰会木方仍载)
        if '曲直' in zw:
            if cai_zai:
                P(gw,'WANG_KE','曲直春木，阳杀(庚)得财星本气之载，力足以修旺木，用杀')
            elif stem(gw)>=1 and stem(cw)>=1 and (to_root_grade(ben(cw)) in ['禄刃','长生','库'] or cs(cw)):
                P(gw,'WANG_KE','曲直木旺成方，官杀透且财星透干通根以生官(财滋弱官)，运至官杀得地则贵，逆用官杀'); S(cw,'财生官杀')
            elif not guan_rooted and ben(cw)==0 and not cs(cw) and (BRANCH_WX.get(mz)==yw or ling(yw)=='旺') and stem(gw)>=1 and stem(sw)>=1:
                P(sw,'ZHUANWANG','曲直官杀根绝(临绝、财虚不生官)而印星当令旺，食伤火透寒木向阳顺泄；比劫化印(卯泄水生火)为喜，不忌比劫'); S(t['bi'],'比劫化印')
            elif not guan_rooted and stem(gw)>=1 and stem(sw)>=1:
                P(sw,'WANG_KE','曲直官杀虚透临绝(木旺金缺)，食伤火透泄秀兼制虚杀，寒木向阳')
            elif not guan_rooted and stem(gw)>=1 and stem(sw)==0 and stem(yw)>=1:
                P(yw,'ZHUANWANG','曲直官杀虚、食伤不透，印星透干顺性滋木(存君之子)')
            elif stem(gw)==0 and sum(1 for b in brs if BRANCH_WX.get(b)==cw)>=2 and stem(sw)>=1:
                P(cw,'ZHUANWANG','曲直无官杀、财方支叠见归垣而食伤透以生财，身旺任财'); S(sw,'食伤生财')
            else:
                P(sw,'ZHUANWANG','曲直格顺食伤火泄秀(木火通明)'); S(yw,'水生木(印生助, 曲直格喜水如癸丑湿土作水论登科发甲)')
        elif '炎上' in zw:
            # 官杀水须有根/成局/得本气财金生, 方论"水济炎"; 虚透根绝(癸坐巳午绝、无亥子申酉)为弱杀激旺,
            # 不可逆(任注: 炎上逢水运激火之烈而亡、逢木运名利两全) -> 顺用木火土、忌水逆局
            # 财在支得本气(酉)/成局即可滋弱杀, 不必透干; 官得根(亥子)/成局亦算有力
            gs_rooted = to_root_grade(ben(gw)) in ['禄刃','长生','库'] or cs(gw) or to_root_grade(ben(cw)) in ['禄刃','长生','库'] or cs(cw) \
                or (stem(gw)>=1 and (int(d(gw).get('zhong_n',0))+int(d(gw).get('yu_n',0)))>=1)  # 官杀透而坐库/余气根(如癸坐丑辰)亦算有气, 得令尤力
            if stem(gw)>=1 and d(dmw).get('ju_n',0)>=1 and stem(cw)>=1:
                # 火局(寅午戌)成则官杀被困而弱, 财透干(坐库/中余气微根亦可)即滋弱杀, 不要求财官本气根(任注: 更喜财滋弱杀)
                P(cw,'WANG_KE','炎上火局成、官杀透而受困，财透干滋弱杀为用(财滋弱杀)'); S(gw)
            elif stem(gw)>=1 and gs_rooted:
                P(gw,'WANG_KE','炎上火旺，官星透得财生/根气，以官为用(火炎水制)'); S(cw,'财金滋水')
            elif stem(sw)>=2 or cs(sw):
                P(sw,'ZHUANWANG','炎上水绝而食伤土成势透干，火土伤官泄秀为用'); S(cw,'财星得用')
            elif stem(gw)>=1:
                if stem(sw)>=1:
                    P(sw,'ZHUANWANG','炎上格成而官杀水虚透根绝无金生，弱杀激旺不可逆，顺泄食伤土为用'); S(yw,'木生火')
                elif stem(yw)>=1:
                    P(yw,'ZHUANWANG','炎上格成、官杀水虚透根绝，顺性用印木滋火(存君之子)，忌水激旺'); S(t['bi'],'顺比劫')
                else:
                    P(t['bi'],'ZHUANWANG','炎上格成、官杀虚浮无根，顺比劫火，忌水逆局激旺'); S(sw,'食伤顺泄')
            else:
                if stem(sw)>=1 or cs(sw):
                    P(sw,'ZHUANWANG','炎上格纯无官杀透，食伤透干成势，顺食伤土泄秀导势'); S(yw,'顺印')
                else:
                    P(t['bi'],'ZHUANWANG','炎上格纯无官杀透、食伤未透，顺比劫火为用(顺势不取制衡)'); S(sw,'食伤顺泄'); S(yw,'印生扶')
        elif '稼' in zw:
            # V6.0原著修正: 滴天髓"独象喜行化地, 化神要昌" -> 专旺格首选食伤(化神)
            # 财星需原局有食伤化劫才可用(滴天髓"行财地, 有食伤化劫之功"); 原局无食伤时财星耗土激旺为忌
            if to_root_grade(ben(sw)) in ['禄刃','长生','库'] or stem(sw)>=1:
                # 原局有金(食伤) -> 金泄土秀为用, 水(财)有食伤化劫可用
                P(sw,'ZHUANWANG','稼穑食伤金透干或见本气根(申酉)，金泄土秀为用(独象喜行化地)'); S(cw,'食伤生财')
            else:
                # 原局无金(食伤) -> 首选金(化神)运, 水(财)无食伤化劫为忌
                P(sw,'ZHUANWANG','稼穑格原局无金(食伤), 独象喜行化地, 首选金(食伤)泄秀为用; 水(财)无食伤化劫为忌(耗土激旺)'); S(yw,'印生助')
        elif '从革' in zw:
            if stem(sw)>=2:
                P(sw,'ZHUANWANG','从革金旺而食伤并透，金白水清/泄其精英为用'); S(cw,'食伤生财')
            elif mz in ('申','酉') and stem(gw)>=1:
                P(gw,'WANG_KE','从革秋金当令旺极，官杀火透炼金成器(金旺喜火)，根弱待运'); S(cw,'财木生火')
            elif stem(gw)>=1 and ben(gw)==0 and to_root_grade(ben(cw)) in ['禄刃','长生','库']:
                P(cw,'WANG_KE','从革官杀火透无根，财星本气生杀(木火两字)，用财滋杀'); S(gw)
            elif cold and not qi(gw):
                P(gw,'QIHOU','从革金寒水冷无火，火暖局调候为急')
            elif stem(gw)==0 and stem(sw)>=1:
                P(sw,'ZHUANWANG','从革金成局而官杀火不透无根，顺食伤水泄秀(金白水清)，虚火犯旺待运透根'); S(cw,'食伤生财')
            elif stem(gw)==0:
                P(t['bi'],'ZHUANWANG','从革金成局、火不透不逆炼，顺金'); S(sw,'食伤泄秀')
            else:
                P(gw,'WANG_KE','从革金旺、官杀火透，火炼秋金'); S(cw)
        elif '润下' in zw:
            if stem(sw)>=1:
                P(sw,'ZHUANWANG','润下水旺极，食伤木透泄秀(水生木)为奋发之机'); S(cw,'木生火暖局')
            elif stem(cw)>=1:
                P(cw,'QIHOU','润下冬水寒凝，财火透干敌寒解冻/暖局为急'); S(sw)
            else:
                P(sw,'ZHUANWANG','润下顺食伤木泄秀，喜火暖'); S(cw)
        else:
            if dmw=='土' and dry:
                P(cw,'QIHOU','专旺燥烈，财润燥为急')
            elif stem(gw)>=2 and guan_rooted:
                P(gw,'WANG_KE','专旺官杀叠透有气，太旺可克以修旺')
            elif BRANCH_WX.get(dz)==cw and dz not in chong_branches and stem(gw)==0:
                P(cw,'ZHUANWANG','专旺日支财星归垣不被冲，身旺用财'); S(sw,'食伤生财')
            elif stem(sw)>=1 and (to_root_grade(ben(sw)) in ['禄刃','长生','库'] or cs(sw) or cs(dmw)):
                P(sw,'ZHUANWANG','专旺食伤透干得比劫成势之生，顺泄为用')
            elif to_root_grade(ben(cw)) in ['禄刃','长生','库'] or cs(cw):
                P(cw,'ZHUANWANG','专旺财有根，用财(滋杀/润燥)')
            else:
                P(sw,'ZHUANWANG','格纯专旺，食伤泄秀导其气势')
        _lp=paths[-1] if paths else ''
        if _lp=='WANG_KE':
            # 逆用官杀/财修旺(实=正格身旺, 克泄耗为用): 忌印比帮身, 喜食伤泄秀、财(身旺任财/财生官杀)
            A(yw,t['bi'])
            S(sw,'身旺食伤泄秀'); S(cw,'身旺任财/财生官杀')
            if primary==cw: S(gw,'官杀得财滋')
        elif _lp=='QIHOU':
            # 调候(润燥暖局): 喜忌由分支显式给出, 块尾不默认顺印比、不笼统忌财官
            pass
        else:
            # 顺用ZHUANWANG: 顺比劫、顺食伤; 官杀岁运至犯旺恒忌。财喜忌看官杀透否:
            # 官杀透干(虽虚)则财生官杀逆局, 忌财; 官杀不透则财顺食伤生(顺泄生财/身旺任财), 喜财。
            # 印不默认喜(专旺气壅、且印克食伤断秀), 仅在分支显式用印时喜。
            S(t['bi'],'顺性喜比劫')
            if stem(gw)>=1:
                A(gw,cw)
            else:
                A(gw)
                # V6.1原著修正: 原局有食伤(透干/本气根/成势)时, 财顺食伤生为喜(滴天髓"行财地, 有食伤化劫之功");
                # 原局无食伤时, 财无化劫耗日主激旺为忌(如L244稼穑格原局无金, 壬戌水运"水不通根, 暗拱火局, 遭祝融之变")
                if stem(sw)>=1 or to_root_grade(ben(sw)) in ['禄刃','长生','库'] or cs(sw):
                    S(cw,'食伤生财/身旺任财')
                else:
                    A(cw,'原局无食伤化劫, 财星耗日主激旺为忌')
    if lq and lq.get('relation')=='相生':
        # 相生两气成象(w1->w2): 顺其势喜chain两神+w2顺泄(食伤); 忌克w2(官杀犯旺)、克w1(财断源)
        ws=[w for w in (lq.get('wuxing') or []) if w]
        w1=w2=None
        for _a in ws:
            for _b in ws:
                if SHENG.get(_a)==_b: w1,w2=_a,_b
        if lq.get('xiu'): P(lq['xiu'],'LIANGQI','两气成象顺其相生之势, 取秀神')
        for _w in ws: S(_w,'成象顺神')
        if w2:
            S(SHENG.get(w2),'顺chain泄秀')
            for _w in (KE_ME.get(w2),KE_ME.get(w1)):
                if _w: A(_w,'逆chain犯旺/断源')
    elif lq:
        if lq.get('xiu'): P(lq['xiu'],'LIANGQI','两气成象顺秀神'); S(t['bi'],'成象顺本方')

    # ---------- B-1 明显病药结构识别(优先于调候，SFTK"有病方为贵") ----------
    # V4.31: 枭印夺食: 印星极旺(ben>=3或当令ben>=2)且食伤当令(月令本气)被印克，病药用食伤泄秀
    if primary is None and (to_root_grade(ben(t['yin'])) == '禄刃' or (ling(t['yin'])=='旺' and to_root_grade(ben(t['yin'])) in ['禄刃','长生'])) \
            and BRANCH_WX.get(mz)==t['shi'] and to_root_grade(ben(t['shi'])) in ['禄刃','长生','库']:
        P(t['shi'],'BINGYAO','枭印夺食: 印星极旺克当令食伤，病在印、药在食，用食伤泄秀卫食')
        S(t['cai'],'食伤生财'); A(t['yin'],'印旺克食为病')
    # V4.32: 伤官制杀: 官杀透干有力(stem>=2或当令)且食伤透干有根，病药用食伤制杀
    if primary is None and (stem(t['guan'])>=2 or ling(t['guan'])=='旺') \
            and stem(t['shi'])>=1 and (to_root_grade(ben(t['shi'])) in ['禄刃','长生','库'] or d(t['shi']).get('zhong_n',0)+d(t['shi']).get('yu_n',0)>=1):
        P(t['shi'],'BINGYAO','伤官制杀: 官杀有力透干，食伤透干有根制官杀为用')
        S(t['cai'],'食伤生财'); A(t['guan'],'官杀为病被制'); A(t['yin'],'印克食伤破格')

    # V6.3: 比劫旺无食伤通关: 比劫成势且食伤不透干(无通关), 病在比劫、药在官杀制比劫
    # 原典: L1808壬申壬寅壬申辛丑"丙午群比争财, 天干无木之化, 家破身亡"
    # 无食伤通关时财为忌(群比争财); 食伤待运透干则通关为喜
    # V7.15: 增加not cs(t['cai'])——财星成势时是财多身弱而非群比争财(原典L1473财多身弱兼官星又旺)
    if primary is None and cs(t['bi']) and stem(t['shi'])==0 and not cs(t['cai']):
        P(t['guan'],'BINGYAO','比劫成势无食伤通关, 病在比劫、药在官杀制比劫(原典群比争财无木之化)')
        S(t['shi'],'食伤待运透干通关(比劫生食神生财)')
        if ben(t['cai'])==0 and stem(t['cai'])==0:
            A(t['cai'],'财极弱无食伤通关, 群比争财为忌'); _bijie_cai_avoid=True
        A(t['bi'],'比劫旺为病')
    # V4.33: 印旺用财: 印星成势(stem>=2且ben>=2)且财星透干，病药用财破印
    if primary is None and stem(t['yin'])>=2 and to_root_grade(ben(t['yin'])) in ['禄刃','长生'] and stem(t['cai'])>=1:
        P(t['cai'],'BINGYAO','印旺用财: 印星成势透干有根，财星透干破印为用')
        S(t['shi'],'食伤生财'); A(t['yin'],'印旺为病被破'); A(t['guan'],'官杀生印助病')


    # ---------- B0a 水旺木浮特殊路径(V7.11, 原典L1016壬子辛亥乙亥丙子) ----------
    # 水势极旺+日主木根虚浮时, 普通调候(亥月乙木需火暖局)失效
    # 原典: "壬水乘权坐亥子, 昆仑之水冲奔无情...乙卯甲寅顺其流纳其气...一交丙运水火交战刑妻克子"
    # 喜: 木(比劫顺水势), 忌: 火(食伤水火交战), 喜: 水(印星顺水势)
    _shui_wang_mu_fu = (
        dm in ('甲', '乙') and  # 日主木(天干, dm是日主天干, dmw是日主五行)
        mz in ('亥', '子') and  # 冬月
        (stem('水') >= 3 or ben('水') >= 3 or (ben('水') >= 2 and stem('水') >= 2)) and  # 水势极旺
        _qr.get('root_class') in ('NONE', 'LIGHT') and  # 日主根虚浮
        stem('火') <= 1 and ben('火') == 0  # 火被水克绝或极弱
    )
    if primary is None and _shui_wang_mu_fu:
        P(t['bi'], 'CONG_SHUN', '水旺木浮: 水势冲奔无情, 木根虚浮, 顺其水势用木比劫纳气(原典L1016乙卯甲寅顺其流)')
        S(t['yin'], '水印顺水势')
        A(t['shi'], '火食伤与水交战为忌(原典L1016丙运水火交战刑妻克子)')
        paths.append('SHUI_WANG_MU_FU')

    # ---------- B0 通用调候(QTBJ穷通宝鉴覆盖所有月份，正格适用) ----------
    # 有明确调候候选hou时直接用第一优先(QTBJ调候是月令核心需求，优先级最高)
    # 排除: 从格(cong or cong_shun)和专旺格(zw, 如炎上/曲直/稼穑/从革/润下)不走通用调候，应该走各自路径
    # V4.27: B0调候路径只排除真从(CONFIRMED)和cong_shun，不排除假从(CANDIDATE)
    # V5.6: 增加专旺格排除 - 专旺格"可顺不可逆", 调候用神(如炎上格用水)会激旺为忌
    _cong_confirmed = bool(cong) and (cong_state or '') == 'CONFIRMED'
    if primary is None and hou and hou[0] and not (_cong_confirmed or cong_shun or zw):
        # V4.38: 身旺命局中, 若调候用神是印星(生扶日主), 则跳过调候路径(扶抑用神应为克泄)
        # 原典: 身旺喜克泄, 调候用神若为生扶则与扶抑冲突, 应以扶抑为主
        _is_yin = hou[0] == SHENG_ME.get(dmw)
        _is_bijie = hou[0] == dmw
        _is_shengfu = _is_yin or _is_bijie
        _is_shenwang = tier in ('旺', '旺极', '太旺')
        if not (_is_shenwang and _is_shengfu):
            P(hou[0],'QIHOU','通用调候候神(《穷通宝鉴》月令调候第一优先)')
            # V4.36: 调候路径同步设置忌神(克调候用神的五行为忌), 避免avoid为空导致大运喜忌误判
            # V5.4引擎层: 冬夏/非冬夏仲裁 - 冬夏调候绝对优先; 非冬夏日主强弱优先, 克调候用神若为印比(生扶日主)则不忌
            _ke_of_hou = KE_ME.get(hou[0])
            if _ke_of_hou:
                _is_dongxia = mz in ('亥','子','丑','巳','午','未')
                _ke_is_yinbi = _ke_of_hou in (dmw, SHENG_ME.get(dmw))  # 克调候用神是比劫或印(生扶日主)
                if _is_dongxia or not _ke_is_yinbi:
                    A(_ke_of_hou,'克调候用神为忌' if _is_dongxia else '克调候用神为忌(非冬夏, 非印比)')
                # 非冬夏且克调候用神为印比: 不加入avoid(印比生扶日主益处大于克调候害处)
    # ---------- B 正格 ----------
    if zheng:
        # 财星破印可用性: 透干有藏干根(本气/中气/余气), 且不被阳日干五合合走而失令
        YANG_HE={'甲':'己','丙':'辛','戊':'癸','庚':'乙','壬':'丁'}
        other_gan=[pillars[k][0] for k in ('year','month','hour')]
        cai_gan_he=(dm in YANG_HE) and (YANG_HE[dm] in other_gan)
        cai_root=to_root_grade(ben(t['cai'])) in ['禄刃','长生','库'] or (stem(t['cai'])>=1 and any(BRANCH_WX.get(b)==t['cai'] for b in brs))  # 本气根; 或财透干坐财方支(己透坐丑虽会水方仍通根位)
        cai_usable=bool(cai_root) and stem(t['cai'])>=1 and not (cai_gan_he and ling(t['cai']) in ('囚','死'))
        # 官星当令为真神、孤而无辅(无财生), 食伤众透有气克官破格 -> 印制食伤护官(L232)
        if primary is None and BRANCH_WX.get(mz)==t['guan'] and to_root_grade(ben(t['guan'])) in ['禄刃','长生','库'] \
                and stem(t['shi'])>=2 and (to_root_grade(ben(t['shi'])) in ['禄刃','长生','库'] or cs(t['shi']) or d(t['shi']).get('zhong_n',0)>=1) \
                and ben(t['cai'])==0 and stem(t['cai'])==0:
            P(t['guan'],'BINGYAO','官星当令为真神、孤而无辅，食伤众透有气克官破格，护官为急')
            S(t['yin'],'印制食伤护官'); A(t['shi'],'食伤克官为病')
        # 官星虚透无根被合化、三重以上湿土晦光(寒湿): 官不真, 舍官从湿(L1046)
        if primary is None and stem(t['guan'])>=1 and ben(t['guan'])==0 \
                and d(t['guan']).get('zhong_n',0)==0 and d(t['guan']).get('yu_n',0)==0 \
                and sum(1 for b in brs if b in ('辰','丑'))>=3 and cold:
            _he_ou={'丙':'辛','丁':'壬','甲':'己','乙':'庚','戊':'癸','己':'甲','庚':'乙','辛':'丙','壬':'丁','癸':'戊'}
            _gg=[gg for k in _pks for gg in [pillars[k][0]] if WX.get(gg)==t['guan']]
            if any(_he_ou.get(gg) in [pillars[k][0] for k in _pks] for gg in _gg):
                P(t['shi'],'BINGYAO','官星虚透无根、被合化，重重湿土晦光，官不真，舍官从湿，食伤制土卫水')
                S(t['cai'],'财破湿土印'); A(t['guan'],'虚官无根被合化、火运虚激反凶'); A(t['yin'],'湿土晦光为病')
        # B1 仲冬调候(火透: 杀重则制杀调候合一, 否则身有气寒木向阳; 印重破印让位)
        # 排除: 伤官太旺且日主有根/帮身, 此时调候火被水克反激, 应用印制食伤或比劫帮身(原文"用神在土不在火也")
        _shui_zw_noqihou = dmw=='水' and (to_root_grade(ben(t['bi'])) == '禄刃' or (to_root_grade(ben(t['bi'])) in ['禄刃','长生'] and stem(t['bi'])>=1)) and stem(t['shi'])>=1
        if primary is None and mz in MIDWINTER and stem('火')>=1 \
                and not (cs(t['yin']) and not cs(t['guan']) and stem(t['guan'])==0 and cai_usable) \
                and not (cs(t['shi']) and (cs(dmw) or to_root_grade(ben(dmw)) in ['禄刃','长生','库'] or stem(dmw)>=1)) \
                and not _shui_zw_noqihou \
                and ('火' in (t['shi'],t['yin']) or tier2 in WANG_TIER2 or cs(dmw) or cs(t['guan'])):  # V7.7 切换tier2
            P('火','QIHOU','仲冬火透为我生/生我之候神，制杀调候/寒木向阳为急(印重无杀财破印除外; 伤官太旺有根不用调候火)')
        # B1b 仲夏调候(水透: 有根/多透/水库/金印源则用水, 单透涸绝培金生水)
        if primary is None and mz in MIDSUMMER and stem('水')>=1:
            if to_root_grade(ben('水')) in ['禄刃','长生','库'] or stem('水')>=2 or ('辰' in brs or '丑' in brs) or to_root_grade(ben('金')) in ['禄刃','长生','库']:
                P('水','QIHOU','仲夏火炎，水透有根/库/金生，水制火调候')
            else:
                P('金','QIHOU','仲夏水单透根涸金无根，培金印生水为源')
        # B2 官杀制化
        if primary is None:
            gs_rooted = cs(t['guan']) or (stem(t['guan'])>=1 and to_root_grade(ben(t['guan'])) in ['禄刃','长生','库'])
            yin_cheng = cs(t['yin']) or to_root_grade(ben(t['yin'])) in ['禄刃','长生']
            cai_yin_chong=False
            for _pr in ((facts.get('combination_facts',{}) or {}).get('liuchong',[]) or []):
                if len(_pr)==2 and {BRANCH_WX.get(_pr[0]),BRANCH_WX.get(_pr[1])}=={t['cai'],t['yin']}:
                    cai_yin_chong=True   # 财成势冲克印支(如申金冲寅木), 官杀是泄财生印通关枢纽, 非攻身
            gs_bing = gs_rooted or (stem(t['guan'])>=1
                       and (ling(t['yin'])=='旺' or cs(t['yin']) or to_root_grade(ben(t['yin'])) in ['禄刃','长生','库'] or stem(t['yin'])>=1)
                       and not (tier2 in WANG_TIER2 and not gs_rooted and yin_cheng)  # V7.7 切换tier2
                       and not (cs(t['cai']) and cai_yin_chong and stem(t['yin'])>=1 and to_root_grade(ben(t['yin'])) in ['禄刃','长生','库']))
            if gs_bing:
                _chong_dui={'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅','卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}
                _dm_root_b=[brs[_i] for _i,_k in enumerate(_pks)
                            if ((facts.get('hidden_stems',{}).get(_k) or []) and _ganwx.get((facts.get('hidden_stems',{}).get(_k) or [None])[0])==dmw)]
                _dm_root_ok=any(_chong_dui.get(b) not in brs for b in _dm_root_b)  # 日主至少一原始本气根不被六冲拔
                # 食伤制杀(身弱杀重)成立两路: ①食伤自有本气根/成势(儿能救母, 如丙坐午临旺制坚金);
                # ②日主有不被冲拔本气根、食伤透有气(身能任制); 两者俱无(食伤虚、日主根拔)则取印化杀
                zhi_ok=stem(t['shi'])>=1 and qi(t['shi']) and (tier2 in WANG_TIER2 or to_root_grade(ben(t['shi'])) in ['禄刃','长生','库'] or cs(t['shi']) or _dm_root_ok  # V7.7 切换tier2
                         or (stem(t['shi'])>=1 and d(t['shi']).get('zhong_n',0)>=1 and to_root_grade(ben(dmw)) in ['禄刃','长生','库']))
                yin_he = d(t['yin']).get('banhe_n',0)>=1 or BRANCH_WX.get(dz)==t['yin']
                hua_ok=stem(t['yin'])>=1 or ling(t['yin'])=='旺' or to_root_grade(ben(t['yin'])) in ['禄刃','长生'] or (to_root_grade(ben(t['yin'])) in ['禄刃','长生','库'] and yin_he)
                _zhuan_shi=False
                # 提纲不照: 月干不是月令本气五行, 印星透干有根(庚申戊寅壬子甲辰: 寅月本气甲木不透(月干戊), 庚金透干为用)
                _month_stem_tg = pillars['month'][0]
                _month_benqi_wx_tg = BRANCH_WX.get(mz)
                _tigang_buzhao = bool(_month_benqi_wx_tg) and _ganwx.get(_month_stem_tg)!=_month_benqi_wx_tg and stem(t['yin'])>=1 and (to_root_grade(ben(t['yin'])) in ['禄刃','长生','库'] or ling(t['yin']) in ('旺','相'))
                if tier2 in WANG_TIER2:  # V7.7 切换tier2
                    if _tigang_buzhao:
                        P(t['yin'],'BINGYAO','提纲不照：月令本气不透，印星透干有根为用(透金为用神)'); S(t['bi'],'比劫帮身'); _zhuan_shi=True
                    elif zhi_ok and ben(t['guan'])==0 and ling(t['shi'])=='旺':
                        # 身旺(旺极/太旺)+食伤当令+官杀虚透无根=伤官去官/食伤泄秀(L1080戊午壬戌丁卯癸卯):
                        # 比劫生食伤顺泄帮身、食伤生财为喜; 虚官被去岁运犯旺、印克食伤(莫作用印)为忌
                        P(t['shi'],'BINGYAO','身旺食伤当令、官杀虚透无根，伤官去官、食伤泄秀生财'); S(t['bi'],'比劫生食伤帮身任泄'); S(t['cai'],'食伤生财'); A(t['guan'],'虚官被去、岁运犯旺凶'); A(t['yin'],'印克食伤、莫作用印'); _zhuan_shi=True
                    elif zhi_ok:
                        P(t['shi'],'BINGYAO','官杀成势身旺，食伤制杀')
                    elif gs_rooted and hua_ok and (cs(t['guan']) or stem(t['guan'])>=2):
                        P(t['yin'],'BINGYAO','身旺而官杀成势有根、印透有气，杀印相生权自我操'); S(t['guan'])
                    elif stem(t['guan'])==1 and cs(t['cai']) and stem(t['bi'])>=2:
                        P(t['cai'],'FUYI','身旺比劫成众、官杀独透根浅而财星当令，财滋弱杀'); S(t['guan'])
                    else:
                        if _tigang_buzhao:
                            P(t['yin'],'BINGYAO','提纲不照：月令本气不透，印星透干有根为用(透金为用神)'); S(t['bi'],'比劫帮身')
                        elif ben(t['guan'])==0 and (d(t['guan'])['zhong_n']>=1 or d(t['guan'])['yu_n']>=1)                                 and (cs(t['bi']) or to_root_grade(ben(t['bi'])) in ['禄刃','长生'] or (to_root_grade(ben(t['bi'])) in ['禄刃','长生','库'] and stem(t['bi'])>=1))                                 and (d(t['cai'])['zhong_n']>=1 or d(t['cai'])['yu_n']>=1 or to_root_grade(ben(t['cai'])) in ['禄刃','长生','库']):
                            # 比劫成势+官杀虚透只有余气根+财星有藏干根: 用财泄比劫生官杀(丁巳癸丑丁卯丙午: 必以丑中辛金为用, 泄劫生财)
                            P(t['cai'],'BINGYAO','比劫成势官杀虚透只有余气根，财星有藏干根，用财泄比劫生官杀(丑中辛金为用)'); S(t['guan'],'财生官杀'); S(t['shi'],'食伤生财')
                        else:
                            P(t['guan'],'BINGYAO','身旺官杀透，任官杀克身成权(待根/财滋)'); S(t['cai'],'财滋官杀')
                elif to_root_grade(ben(dmw)) in ['禄刃','长生'] and not hua_ok and ling(t['shi'])=='旺' and stem(t['cai'])>=1 \
                        and (dry or to_root_grade(ben(t['cai'])) in ['禄刃','长生','库'] or cs(t['cai'])):
                    # 伤官当令身旺(燥厚)、财透有根: 伤官生财顺用, 财泄食伤生官、润燥通关(L887 壬水润土泄金生木用官)
                    P(t['shi'],'BINGYAO','伤官当令身旺、财透，伤官生财、财生官流通(燥厚喜财润燥)')
                    S(t['cai'],'伤官生财、润燥'); S(t['guan'],'财生官'); _zhuan_shi=True
                elif to_root_grade(ben(dmw)) in ['禄刃','长生'] and not hua_ok:
                    P(t['shi'],'BINGYAO','官杀重而身有重根、印无气，食伤制杀为美(生局须食)'); S(t['yin'])
                elif hua_ok and (cs(t['guan']) or stem(t['guan'])>=2 or (stem(t['guan'])>=1 and to_root_grade(ben(t['guan'])) in ['禄刃','长生','库'])):
                    # 官杀重+印透有气: 印化杀生身(杀印相生)
                    P(t['yin'],'BINGYAO','官杀重身弱/中和，印化杀生身(杀印相生)'); S(t['bi'])
                # V7.6 切换tier2
                elif zhi_ok and (to_root_grade(ben(t['shi'])) in ['禄刃','长生','库'] or cs(t['shi'])) and tier2 in SHUAI_TIER2 and ben(dmw)==0 \
                        and (to_root_grade(ben(t['guan'])) in ['禄刃','长生'] or cs(t['guan']) or (stem(t['guan'])>=2 and to_root_grade(ben(t['guan'])) in ['禄刃','长生','库'])):
                    # 身弱(无本气根)杀成局、食伤制杀: 制化并行, 印化杀扶身同为喜(不夺食), 比劫帮身(L756 戊土制杀、乙卯印杀印相生仕郡守)
                    P(t['shi'],'BINGYAO','身弱杀成局、食伤制杀，制化并行'); S(t['yin'],'印化杀扶身(制化并行不夺食)')
                    S(t['bi'],'帮身任制'); S(t['cai'],'食伤生财'); _zhuan_shi=True
                elif zhi_ok and (to_root_grade(ben(t['shi'])) in ['禄刃','长生','库'] or cs(t['shi'])) and not (cs(t['guan']) and to_root_grade(ben(dmw)) in ['禄刃','长生','库'] and stem(t['bi'])==0) and not (not cs(t['guan']) and (to_root_grade(ben(t['shi'])) == '禄刃' or (to_root_grade(ben(t['shi'])) in ['禄刃','长生'] and ling(t['shi'])=='旺'))):
                    # 食伤自有本气根/成势, 制杀有力专美(儿能救母 L1744甲申丙寅甲申庚午): 枭印夺食破格忌印, 食伤生财喜财, 比劫帮身任制
                    # 排除1: 官杀成势且日主有本气根但无比劫透干, 此时应优先比劫帮身任官杀(原文"用神必在酉金")
                    # 排除2: 官杀不成势且食伤太旺(ben>=3), 此时应用印制食伤扶身(原文"用神在土不在火也" 丁亥壬子庚子辛巳)
                    P(t['shi'],'BINGYAO','食伤透根制杀有力(儿能救母)，专食伤制杀'); S(t['cai'],'食伤生财、制杀后官为用'); S(t['bi'],'帮身任制'); A(t['yin'],'枭印夺食破格'); _zhuan_shi=True
                elif zhi_ok and not cs(t['guan']) and (to_root_grade(ben(t['shi'])) == '禄刃' or (to_root_grade(ben(t['shi'])) in ['禄刃','长生'] and ling(t['shi'])=='旺')):
                    # 官杀不成势+食伤太旺(ben>=3): 印制食伤扶身为用(原文"用神在土，不在火也" 丁亥壬子庚子辛巳)
                    P(t['yin'],'BINGYAO','官杀不成势食伤太旺，印制食伤扶身为用'); S(t['bi'],'比劫帮身'); A(t['shi'],'食伤太旺为病'); A(t['cai'],'财生官杀')
                elif zhi_ok and cs(t['guan']) and to_root_grade(ben(dmw)) in ['禄刃','长生','库'] and stem(t['bi'])==0:
                    # 官杀成势+日主有本气根+无比劫透干: 比劫帮身任官杀为用(原文"用神必在酉金" 丁巳壬子辛巳丁酉)
                    P(t['bi'],'BINGYAO','官杀成势日主有根但无比劫透干，比劫帮身任官杀为用'); S(t['yin'],'印化杀生身'); S(t['shi'],'食伤制杀为喜'); A(t['cai'],'财生官杀助旺')
                elif zhi_ok:
                    P(t['shi'],'BINGYAO','印无力而食伤无根，食伤制杀待印化'); S(t['yin'])
                elif cs(t['guan']) or to_root_grade(ben(t['guan'])) in ['禄刃','长生'] or (stem(t['guan'])>=1 and (to_root_grade(ben(t['guan'])) in ['禄刃','长生','库'] or ling(t['guan']) in ('旺','相'))):
                    P(t['yin'],'BINGYAO','官杀重身轻印无气，取印化杀待运'); S(t['bi'])
                    if tier2 in SHUAI_TIER2: A(t['guan'],'杀重身轻印未到位，官杀再旺攻身忌')  # V7.6 切换tier2
                # 官杀虚透无根不重: 不印化杀, primary保持None继续走后面路径(案例5丙申己亥庚辰戊寅官杀虚透+印旺用财破印)
                if primary!=t['cai'] and not _zhuan_shi: A(t['cai'])  # 财滋弱杀以财为用不忌财; 制杀专食伤/伤官去官则食伤生财喜财; 余制化忌财坏印生杀
        # B4 印重成病(官杀不透)→财破印(优先于通关: 印重为病, 通关官杀生印反助病)
        if primary is None and cs(t['yin']) and stem(t['guan'])==0 and cai_usable:
            P(t['cai'],'BINGYAO','印重成势官杀不透而财有本气根，财破印去壅塞'); S(t['shi']); A(t['yin'])
        # 印重无官杀、财不透而食伤有本气根: 食伤生财、就财破印(财待运透), 同党顺泄
        # 排除: 印星当令且日主有气(原文"印星当令，金亦有气，用神在水"), 此时应用食伤泄秀而非财破印
        if primary is None and cs(t['yin']) and stem(t['guan'])==0 and not cai_usable \
                and stem(t['cai'])==0 and to_root_grade(ben(t['shi'])) in ['禄刃','长生','库'] \
                and not (ling(t['yin'])=='旺' and (cs(dmw) or to_root_grade(ben(dmw)) in ['禄刃','长生','库'] or stem(dmw)>=1 or cs(t['yin']) or stem(t['yin'])>=1)):
            P(t['cai'],'BINGYAO','印重成势无官杀、财不透而食伤有本气根，食伤生财就财破印(财待透)'); S(t['shi'],'食伤泄秀生财'); A(t['yin'])
        # 印星当令且日主有气、食伤透有根: 食伤泄秀为用(原文"印星当令，金亦有气，用神在水，不在火也")
        if primary is None and ling(t['yin'])=='旺' and (cs(dmw) or to_root_grade(ben(dmw)) in ['禄刃','长生','库'] or stem(dmw)>=1 or cs(t['yin']) or stem(t['yin'])>=1) \
                and stem(t['guan'])==0 and stem(t['shi'])>=1 and qi(t['shi']):
            P(t['shi'],'BINGYAO','印星当令且日主有气、食伤透有根，食伤泄秀为用(非印重成病)'); S(t['cai'],'食伤生财'); A(t['guan'],'官杀生印助壅')
        # B3 通关
        if primary is None and cs(t['guan']) and cs(t['bi']):
            P(t['yin'],'TONGGUAN','官杀与比劫两神成势相战，印通关')
        if primary is None and cs(t['cai']) and (cs(t['yin']) or (stem(t['yin'])>=1 and to_root_grade(ben(t['yin'])) in ['禄刃','长生','库'])):
            P(t['guan'],'TONGGUAN','财印成势相战(或印透根被财克)，官杀通关(财生官生印)')
        if primary is None and cs(t['shi']) and cs(t['guan']):
            P(t['cai'],'TONGGUAN','食伤与官杀两神成势相战，财通关')
        # B4b 衰极印绝、食伤+财成势顺生(日支根被合化, 类从儿)→顺财
        if primary is None and tier=='衰极' and ben(t['yin'])==0 and stem(t['yin'])==0 \
                and cs(t['shi']) and cs(t['cai']):
            P(t['cai'],'CONG_SHUN','衰极印绝、食伤生财成势顺生(类从儿)，顺财'); S(t['shi'],'食伤吐秀')
        # B5 财重身弱 / 食伤泄过
        if primary is None and cs(t['cai']) and tier2 in SHUAI_TIER2:  # V7.5 切换tier2
            if to_root_grade(ben(t['bi'])) in ['禄刃','长生','库']:
                P(t['bi'],'BINGYAO','财重身弱、比劫有根，比劫分财'); S(t['yin'])
            elif qi(t['yin']):
                P(t['yin'],'BINGYAO','财重身弱而比劫虚透无根(干多不如根重)，印化财生身'); S(t['bi'])
            elif qi(t['bi']):
                P(t['bi'],'BINGYAO','财重身弱，比劫分财'); S(t['yin'])
            else:
                P(t['yin'],'BINGYAO','财重身弱无比劫，印扶身泄财'); S(t['bi'])
            A(t['cai'],t['guan'])
        if primary is None and cs(t['shi']) and tier2 in SHUAI_TIER2 and not (cs(t['yin']) or to_root_grade(ben(t['yin'])) in ['禄刃','长生']):  # V7.5 切换tier2
            P(t['yin'],'BINGYAO','食伤泄气太过，印制食伤扶身'); S(t['bi']); A(t['shi'],t['cai'])
        # 印星已旺时不印制食伤(印更壅塞), primary保持None继续走身弱扶抑财破印(案例5丙申己亥庚辰戊寅印旺用木破印)
        # B6 调候兜底 / 扶抑
        # 水专旺(比劫成势+食伤透干)时用木泄秀(甲申丙子癸亥癸亥润下格用甲木泄秀, 仲冬调候已排除)
        _shui_zhuanwang = (to_root_grade(ben(t['bi'])) == '禄刃' or (to_root_grade(ben(t['bi'])) in ['禄刃','长生'] and stem(t['bi'])>=1)) and stem(t['shi'])>=1 and dmw=='水'
        if primary is None and _shui_zhuanwang:
            P(t['shi'],'ZHUANWANG','润下水专旺成势，食伤木透干顺泄秀为奋发之机(水生木)'); S(t['cai'],'木生火暖局')
        # 印旺+财有气时优先财破印, 优先于仲冬调候(案例5丙申己亥庚辰戊寅亥月印旺用木破印, 不走调候火)
        # 仅限仲冬! 其他月份不走(避免辛亥庚寅丙子乙未寅月印绶格火虚木嫩用印护格被误伤)
        _yin_wang_b6 = (to_root_grade(ben(t['yin'])) in ['禄刃','长生']) or (to_root_grade(ben(t['yin'])) in ['禄刃','长生','库'] and stem(t['yin'])>=2)
        _cai_youqi_b6 = (to_root_grade(ben(t['cai'])) in ['禄刃','长生','库']) or (stem(t['cai'])>=1)  # 财有气必须透干或有本气根, 仅ling=相不算(避免案例9误伤)
        if primary is None and mz in MIDWINTER and _yin_wang_b6 and _cai_youqi_b6:
            P(t['cai'],'BINGYAO','印旺成势反为病，财星有气破印为用(优先于调候)'); S(t['shi'],'食伤生财'); A(t['yin'],'印旺为病')
        elif primary is None and mz in MIDWINTER and (to_root_grade(ben('火')) in ['禄刃','长生','库'] or ling('火') in ('旺','相') or d('火')['zhong_n']+d('火')['yu_n']>=1 or stem('火')>=2):
            P('火','QIHOU','仲冬寒凝无制化，取火调候待运(火有根/有气)')
        # V7.2 仲夏调候: 原局官杀透干有根时水为忌, 不强制调候, 走扶抑路径(L1473财多身弱官杀旺)
        _gs_youqi_midsummer = stem(t['guan'])>=1 and (to_root_grade(ben(t['guan'])) in ['禄刃','长生','库'] or cs(t['guan']))
        if primary is None and mz in MIDSUMMER and not _gs_youqi_midsummer:
            P('水','QIHOU','仲夏炎燥无制化，取水调候待运')
        if primary is None and tier2 in WANG_TIER2:  # V7.5 切换tier2
            _zhuan_shi=False
            _gy=dm in '甲丙戊庚壬'; _yg='甲丙戊庚壬' if _gy else '乙丁己辛癸'
            _py_tou=any(_ganwx.get(g)==t['yin'] for g in other_gan if g in _yg)  # 偏印(生我同阴阳)透干
            _xiao_duo_shi=_py_tou and stem(t['shi'])>=1 and ben(t['shi'])==0  # 偏印透、食伤透无本气根=枭神夺食, 食伤被夺不可用
            # 比劫成势+食伤透干优先食伤泄秀(辛未辛丑戊辰壬戌: 土比劫极旺四库全+辛金双透, 用金泄秀吐精英)
            _bijie_chengshi = (cs(t['bi']) or to_root_grade(ben(t['bi'])) == '禄刃' or (to_root_grade(ben(t['bi'])) in ['禄刃','长生'] and stem(t['bi'])>=1))
            if _bijie_chengshi and stem(t['shi'])>=1 and not _xiao_duo_shi and stem(t['guan'])==0:
                P(t['shi'],'ZHUANWANG','比劫成势食伤透干，顺泄吐秀为用(辛金吐秀泄其精英)'); S(t['cai'],'食伤生财')
            # 印绶格护印: 印当令透干、财虚透无根失令坏印为病, 用印护格(辛亥庚寅丙子乙未朱中堂造: 火虚木嫩用神在木忌神在金)
            if BRANCH_WX.get(mz)==t['yin'] and (stem(t['yin'])>=1 or ling(t['yin'])=='旺')                     and stem(t['cai'])>=1 and ben(t['cai'])==0 and ling(t['cai']) in ('休','囚','死')                     and ben(t['yin'])<=2 and stem(t['guan'])==0:
                P(t['yin'],'BINGYAO','印绶格印当令透干、财虚透无根失令坏印为病，用印护格(火虚木嫩用神在木)'); S(t['bi'],'比劫制财护印(药)'); A(t['cai'],'虚财坏印为病'); _zhuan_shi=True
            elif stem(t['guan'])>=2 and stem(t['shi'])>=1 and ben(t['guan'])==0 and ling(t['shi'])=='旺':
                # 身旺+食伤当令+官杀众透无根=伤官去官/食伤泄秀(L1080): 比劫生食伤顺泄、食伤生财为喜, 虚官犯旺、印克食伤为忌
                _zhuan_shi=True; P(t['shi'],'BINGYAO','身旺食伤当令、官杀众透无根，伤官去官、食伤泄秀生财'); S(t['bi'],'比劫生食伤帮身任泄'); S(t['cai'],'食伤生财'); A(t['guan'],'虚官被去、岁运犯旺凶'); A(t['yin'],'印克食伤、莫作用印')
            elif stem(t['guan'])>=2 and stem(t['shi'])>=1: P(t['shi'],'BINGYAO','身旺官杀众透，食伤制杀兼泄秀')
            elif cs(t['cai']) and qi(t['guan']) and stem(t['guan'])<2: P(t['cai'],'FUYI','身旺财当令而官杀浅，财滋弱杀/用财')
            elif stem(t['guan'])==1 and ben(t['guan'])==0 and ling(t['guan']) in ('休','囚','死') \
                    and stem(t['cai'])>=1 and to_root_grade(ben(t['cai'])) in ['禄刃','长生','库']:
                P(t['cai'],'FUYI','身旺官杀独透无根失令不足任，财星透干有根(财来就我)，用财'); S(t['shi'],'食伤生财')
            elif (cs(t['yin']) or to_root_grade(ben(t['yin'])) in ['禄刃','长生']) and ben(t['guan'])==0 and not cs(t['guan']) \
                    and stem(t['shi'])>=1 and qi(t['shi']) and not _xiao_duo_shi:
                P(t['shi'],'FUYI','身旺印重成势、官杀虚透无根只生印不制身，食伤泄秀生财破印'); S(t['cai'],'财破印'); A(t['guan'],'官杀生印助壅')
            elif to_root_grade(ben(t['yin'])) == '禄刃' and ben(t['bi'])<=1 and ben(t['cai'])==0 and stem(t['cai'])==0 \
                    and stem(t['shi'])==0 and ben(t['shi'])==0 and ben(t['guan'])==0:
                # 母多灭子(土多金埋类): 印本气极重埋身、日主本气根弱, 财破印/食伤泄皆不可得、官杀无根(生印反埋);
                # 正治取比劫分印之壅、帮身出土(任注 L1763 辛酉比劫拱保辰丑出仕), 忌印、官杀生印。# PCT-MARK 印/日本气党众
                P(t['bi'],'BINGYAO','母多灭子印重埋身，财破印与食伤泄俱不可得，比劫分印之壅、帮身出土'); S(t['shi'],'食伤待运泄秀'); S(t['cai'],'财待运破印'); A(t['yin'],'印重埋身'); A(t['guan'],'官杀生印助埋')
            elif stem(t['guan'])>=1 and ben(t['guan'])==0 and (d(t['guan'])['zhong_n']>=1 or d(t['guan'])['yu_n']>=1)                     and (cs(t['bi']) or to_root_grade(ben(t['bi'])) in ['禄刃','长生'] or (to_root_grade(ben(t['bi'])) in ['禄刃','长生','库'] and stem(t['bi'])>=1))                     and (d(t['cai'])['zhong_n']>=1 or d(t['cai'])['yu_n']>=1 or to_root_grade(ben(t['cai'])) in ['禄刃','长生','库']):
                # 比劫成势+官杀虚透只有余气根+财星有藏干根: 用财泄比劫生官杀(丁巳癸丑丁卯丙午: 必以丑中辛金为用, 泄劫生财)
                P(t['cai'],'BINGYAO','比劫成势官杀虚透只有余气根，财星有藏干根，用财泄比劫生官杀(丑中辛金为用)'); S(t['guan'],'财生官杀'); S(t['shi'],'食伤生财')
            elif stem(t['guan'])>=1 and (to_root_grade(ben(t['guan'])) in ['禄刃','长生','库'] or ling(t['guan']) in ('旺','相') or d(t['guan'])['zhong_n']+d(t['guan'])['yu_n']>=1):
                P(t['guan'],'FUYI','身旺官杀透干有根/有气，用官杀克身成权')
            elif stem(t['guan'])>=1 and stem(t['shi'])>=1: P(t['shi'],'FUYI','身旺官杀虚透无根，食伤制杀兼泄秀(案例9己丑丙子辛酉壬辰虚火无根必以水为用)')
            elif stem(t['guan'])>=1: P(t['guan'],'FUYI','身旺官杀透干，用官杀克身成权(待根)')
            elif BRANCH_WX.get(mz)==t['yin'] and (stem(t['yin'])>=1 or ling(t['yin'])=='旺') \
                    and stem(t['cai'])>=1 and ben(t['cai'])==0 and ling(t['cai']) in ('休','囚','死') \
                    and ben(t['yin'])<=2:
                # 印绶格印当令透干、财虚透无根失令反坏印为病, 用印护格、比劫制财护印(财有根破壅归B4不在此)
                P(t['yin'],'BINGYAO','印绶格印当令透干、财虚透无根失令坏印为病，用印护格'); S(t['bi'],'比劫制财护印(药)'); A(t['cai'],'虚财坏印为病'); _zhuan_shi=True
            elif qi(t['cai']): P(t['cai'],'FUYI','身旺用财，我克为财')
            else: P(t['shi'],'FUYI','身旺无官杀财，食伤吐秀')
            if not _zhuan_shi:
                S(t['cai'] if primary==t['guan'] else t['shi'],''); A(t['yin'],t['bi'])
            if cs(t['yin']) or to_root_grade(ben(t['yin'])) in ['禄刃','长生']: A(t['guan'],'身旺印重，官杀生印助壅(印重不劳官生)')
        if primary is None and tier2 in SHUAI_TIER2:  # V7.8 切换tier2
            if (cs(t['yin']) or to_root_grade(ben(t['yin'])) in ['禄刃','长生']) and qi(t['cai']):
                P(t['cai'],'BINGYAO','身弱印旺成势反为病，财星有气破印为用(案例5丙申己亥庚辰戊寅印旺用木破印)'); S(t['shi'],'食伤生财'); A(t['yin'],'印旺为病')
            elif qi(t['yin']): P(t['yin'],'FUYI','身弱用印，生我扶身')
            elif qi(t['bi']): P(t['bi'],'FUYI','身弱用比劫帮身')
            else: P(t['yin'],'FUYI','身弱印比微，取印待运扶身')
            S(t['bi'] if primary==t['yin'] else t['yin'],''); A(t['cai'],t['guan'],t['shi'])
        if primary is None and tier=='中和':
            if stem(t['guan'])>=1 and to_root_grade(ben(t['guan'])) in ['禄刃','长生','库'] and (ling(t['yin'])=='旺' or cs(t['yin'])):
                P(t['yin'],'BINGYAO','中和官杀透根、印当令，杀印相生用印')
            elif hou: P(hou[0],'QIHOU','中和取调候/相神，扶抑不强(取调候候选第一优先)')
        for w in hou:
            if w!=primary: S(w,'调候候神(《穷通宝鉴》次序)')
        # 兜底前双重保险: 印旺+财有气时优先财破印(案例5丙申己亥庚辰戊寅印旺用木破印)
        if primary is None and (cs(t['yin']) or to_root_grade(ben(t['yin'])) in ['禄刃','长生']) and qi(t['cai']):
            P(t['cai'],'BINGYAO','印旺成势反为病，财星有气破印为用(兜底前保险)'); S(t['shi'],'食伤生财'); A(t['yin'],'印旺为病')
        # 兜底: 所有路径都不满足时, 确保有primary输出(避免None)
        if primary is None:
            # 最优先: 印旺+财有气时财破印(案例5丙申己亥庚辰戊寅印旺用木破印, 不走调候火)
            _yin_wang = (to_root_grade(ben(t['yin'])) in ['禄刃','长生']) or (to_root_grade(ben(t['yin'])) in ['禄刃','长生','库'] and stem(t['yin'])>=2)
            _cai_youqi = (to_root_grade(ben(t['cai'])) in ['禄刃','长生','库']) or (stem(t['cai'])>=1) or (ling(t['cai']) in ('旺','相'))
            if _yin_wang and _cai_youqi:
                P(t['cai'],'BINGYAO','印旺成势反为病，财星有气破印为用(兜底最优先)'); S(t['shi'],'食伤生财'); A(t['yin'],'印旺为病')
            elif hou:
                P(hou[0],'QIHOU','兜底取调候候神(所有结构化路径未命中，取调候候选第一优先)')
            elif tier2 in WANG_TIER2:  # V7.8 切换tier2
                P(t['shi'],'FUYI','兜底身旺食伤泄秀')
            elif tier2 in SHUAI_TIER2:  # V7.8 切换tier2
                P(t['yin'],'FUYI','兜底身弱用印扶身')
            else:
                P(t['shi'],'FUYI','兜底中和取食伤泄秀')

    # 喜忌互斥收敛(防御): primary用神绝不可入忌神; avoid为病机明确忌, 优先于撒网secondary
    if primary:
        avoid=[w for w in avoid if w!=primary]
    # V5.4引擎层统一过滤: QIHOU路径非冬夏月, 印比(生扶日主)从avoid移除并加入secondary(日主强弱优先于调候忌)
    if 'QIHOU' in paths and mz not in ('亥','子','丑','巳','午','未'):
        _yinbi_set = {dmw, SHENG_ME.get(dmw)}
        _yinbi_in_avoid = [w for w in avoid if w in _yinbi_set]
        avoid = [w for w in avoid if w not in _yinbi_set]
        for w in _yinbi_in_avoid:
            if w and w not in secondary and w != primary:
                secondary.append(w)
                notes.setdefault(w, '非冬夏QIHOU: 印比生扶日主优先于调候忌, 升为喜')
    # V5.3引擎层: 身旺时克泄耗(食伤/财/官杀)从avoid移除并加入secondary(身旺需克泄耗, 官杀制旺身为吉)
    # 排除从格/专旺/化气/两气路径(喜忌逻辑与普通格不同)
    WANG_TIERS_V53 = ('旺', '太旺', '旺极')
    _SPECIAL_PATHS = ('CONG_SHUN', 'CONG_NI', 'ZHUANWANG', 'HUA_QI', 'LIANGQI')
    if tier2 in WANG_TIER2 and not any(p in _SPECIAL_PATHS for p in paths):  # V7.8 切换tier2
        _kexiehao_set = {SHENG.get(dmw), KE.get(dmw), KE_ME.get(dmw)}  # 食伤/财/官杀
        _bijie_cai = t['cai'] if _bijie_cai_avoid else None
        _kxh_in_avoid = [w for w in avoid if w in _kexiehao_set and w != _bijie_cai]
        avoid = [w for w in avoid if w not in _kexiehao_set or w == _bijie_cai]
        for w in _kxh_in_avoid:
            if w and w not in secondary and w != primary:
                secondary.append(w)
                notes.setdefault(w, f'V5.3身旺({tier}): 克泄耗制旺身为吉, 从忌升为喜')
    secondary=[w for w in secondary if w not in avoid]
    cand=[w for w in ([primary]+secondary) if w]
    # V4.1: 理论来源标签 (基于primary用神的路径标签映射到理论来源)
    # Authority Matrix v0.2验证(2026-09-21): 引擎三轨(格局/调候/病药)与矩阵完全一致
    # 扶抑归ZIPING: 消费的是PZZQ体系的wang_shuai+qiang_ruo+tier2, 数据来源是PZZQ
    # DTS体用轨: 矩阵判DTS有独立扶抑体系, 但独立实现验证失败(四轨并行V1-V3: 57.7%/55.3%/58.2%)
    # 未来若做DTS体用轨, 需先统一数据源(V7.x已修复), 保留接口定义和失败记录
    # 路径标签 -> 理论来源映射
    PATH_TO_THEORY = {
        'HUA_QI': 'THEORY_ZIPING',      # 化气格 -> 子平真诠
        'CONG_SHUN': 'THEORY_ZIPING',   # 从格顺用 -> 子平真诠
        'WANG_KE': 'THEORY_ZIPING',     # 旺极克泄 -> 子平真诠
        'ZHUANWANG': 'THEORY_ZIPING',   # 专旺格 -> 子平真诠
        'QIHOU': 'THEORY_QIONGTONG',    # 调候 -> 穷通宝鉴
        'LIANGQI': 'THEORY_ZIPING',     # 两气格 -> 子平真诠
        'BINGYAO': 'THEORY_SHENFENG',   # 病药 -> 神峰通考
        'FUYI': 'THEORY_ZIPING',        # 扶抑 -> 子平真诠(主) + 滴天髓(理论来源, Authority Matrix判DTS有独立体用扶抑体系)
        'TONGGUAN': 'THEORY_ZIPING',    # 通关 -> 子平真诠
    }
    primary_path = paths[0] if paths else ''
    theory_source = PATH_TO_THEORY.get(primary_path, 'THEORY_ZIPING')  # 默认子平真诠
    # V4.39: 最终兜底 - 若avoid为空且primary不为空, 自动设置忌神为克primary的五行(保证大运喜忌有忌神可识别)
    # V5.4修正: 若克primary的五行是印比(生扶日主, 已被V5.4判定为喜/中性), 则不加入avoid兜底
    if not avoid and primary and primary in WUXING:
        _ke_of_primary = KE_ME.get(primary)
        _yinbi_set_v439 = {dmw, SHENG_ME.get(dmw)}
        if _ke_of_primary and _ke_of_primary not in _yinbi_set_v439:
            avoid.append(_ke_of_primary)
    
    # V7.23 P3-001: 生成QTBJ_STEM_ASSERTION结构(只做结构落地, 不进入Judgment)
    _qtbj_assertions = []
    for _i, _c in enumerate(hou_stem):
        _ap = _c.get('applicability', 'APPLICABLE')
        _stem = _c.get('stem', '')
        _el = _c.get('element', '')
        _pri = _c.get('priority', 99)
        _rid = 'QTBJ-' + mz + _stem
        _rt = _stem + '为' + mz + '月调候用'
        _cond = _c.get('applicability_reason', '')
        _prov = 'DIRECT(穷通宝鉴原文)' if _ap == 'APPLICABLE' else 'ENGINEERING_DERIVED'
        _valid = _ap == 'APPLICABLE'
        _qtbj_assertions.append({
            'assertion_id': 'QTBJ-STEM-' + dm + '-' + str(_i+1).zfill(2),
            'track': 'QTBJ',
            'stem': _stem,
            'element': _el,
            'priority': _pri,
            'source_id': _rid,
            'source_text': _rt,
            'assertion_type': 'CLIMATE_STEM',
            'applicability': _ap,
            'condition': _cond,
            'provenance': _prov,
            'valid': _valid,
        })

    return {'module':'YONGSHEN_ENGINE_V4.1','namespace':'daymaster_yongshen_engine',
            'day_master':dm,'daymaster_wuxing':dmw,'spectrum_tier':tier,'spectrum_tier2':tier2,'special':spec_name,
            'wang_shuai':spectrum.get('wang_shuai',{}) if isinstance(spectrum,dict) else {},
            'qiang_ruo':spectrum.get('qiang_ruo',{}) if isinstance(spectrum,dict) else {},
            'theory_source':theory_source,  # 理论来源标签 (ZIPING/QIONGTONG/SHENFENG)
            'yongshen_primary':primary,'yongshen_secondary':secondary,'yongshen_avoid':avoid,
            'yongshen_paths':paths,
            'yongshen_candidates':[{'wuxing':w,'path':(paths[0] if w==primary else 'SECONDARY'),
                                    'note':notes.get(w,'')} for w in cand],
            'candidate_wuxing':sorted(set(cand)),
            'climate_stem_candidates': hou_stem,  # V7.23 PATCH: 十干级调候候选(不降级为五行)
            'qtbj_stem_assertions': _qtbj_assertions,  # V7.23 P3-001: 十干级调候Assertion结构
            'judgment_status':'YONGSHEN_PRIMARY_STRUCTURE' if primary else 'YONGSHEN_PENDING',
            'boundary_note':'病机决策树收敛主用神(布尔+多态枚举, 无score/winner); primary为结构取用推演非富贵吉凶裁决, '
                           '假从/湿土/会方归垣等边界保留secondary; 吉凶前端拦截; 成败有力待作用层; 不接production_entry'}

