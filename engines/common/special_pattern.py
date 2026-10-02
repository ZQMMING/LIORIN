# -*- coding: utf-8 -*-
import re
import sys
sys.path.insert(0, ".")
from engines.common.mumie_checker import check_mumie
"""特殊格局结构识别（task#47）。

只做**结构定性标签**，不改变七档客观力量谱，不输出用神/吉凶/成败。
- 化气格：日干与【紧邻】(月干/时干)五合、化神得月令或成势(本气>=2/会局)；
  日主无根无印=真化(CONFIRMED)，带一微根/微印=假化(CANDIDATE)；隔位遥合、化神不当令不成势=合而不化(不判)。
  他干合化、地支合化、大运合化不在此列(交 ACTIVITY 合去 / task#50 归化)。
- 从格：日主无本气根、无有根印比、对立一方成势顺其势；虚透印比地支不载=假从(CANDIDATE)。
  **孤根被冲拔(T30)**: 身/印本气仅一支且被六冲、对立成势而日主不当令 -> 根拔, 冲拔之从为CANDIDATE(不作真从)。
  **财生杀**: 官杀透干而得本气财生(申金生壬杀)亦成杀势。
  食伤生财分界(#PCT-MARK): 财成局明透/当令党众主导->从财(丙寅庚寅「从财格真」);
    食伤当令本气压财、或叠透而财藏(儿会财局,吾儿又见儿)->从儿。
  **从儿不论身强弱**(甲午丁丑「格取从儿,虽逢禄比帮身,非身弱论」): 官杀无、食伤成势、无印逆局、
    日主非比劫当令即可, 允许日主带一禄根(CANDIDATE)。
- 专旺/一行得气(曲直/炎上/稼穡/从革/润下): 本方成局/本气重, 无官杀本气克、无财破;
  官杀虚透无根须被合化为本方(戊癸合火助刃)方不破局。
- 母多灭子/印势漂没(CANDIDATE): 印成势而日主无根不受生; pair反转(木火通明vs土重金埋)交气候/天干性情层。

方法论: 布尔 + 多态枚举 + 客观本气支数比较(#PCT-MARK, 非权重评分)。
原典: 《滴天髓·从象》《化象》《一行得气》; 「从儿不论身强弱」「干多不如根重」「旺者冲衰衰者拔」。
"""

ZHUANWANG_NAME = {'木': '曲直格', '火': '炎上格', '土': '稼穑格', '金': '从革格', '水': '润下格'}
WUHE_HUASHEN = {('甲', '己'): '土', ('己', '甲'): '土', ('乙', '庚'): '金', ('庚', '乙'): '金',
                ('丙', '辛'): '水', ('辛', '丙'): '水', ('丁', '壬'): '木', ('壬', '丁'): '木',
                ('戊', '癸'): '火', ('癸', '戊'): '火'}
# 本气级根标签(计 ben_n)
_BEN_TAGS = ('BEN', 'BEN_LU', 'BEN_CS')

# 五行生克常量（替代已删wuxing_power）
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
SHENG_ME = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
KE_ME = {'木': '金', '金': '火', '火': '水', '水': '土', '土': '木'}
BRANCH_WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火', '午': '火', '申': '金', '酉': '金', '辰': '土', '戌': '土', '丑': '土', '未': '土'}


def _shi(d):
    if not d:
        return False
    ben = int(d.get('ben_n', 0)); stem = int(d.get('stem_n', 0))
    ju = int(d.get('ju_n', 0)); ling = d.get('ling_state', '')
    return (stem >= 1 and ben >= 1) or ben >= 2 or ju >= 1 or (ling == '旺' and ben >= 1)


def _fkey(d):
    """#PCT-MARK: 成势归宿定性排序键(局 > 本气+半合支数 > 透干)。"""
    if not d:
        return (0, 0, 0)
    return (int(d.get('ju_n', 0)), int(d.get('ben_n', 0)) + int(d.get('banhe_n', 0)), int(d.get('stem_n', 0)))


def _pat(pid, name, state, side, note, facts=None):
    return {'pattern_id': pid, 'name': name, 'state': state, 'side': side,
            'boundary_note': note, 'source_fact_ids': list(facts or [])}


def _ben_branches(pw, wx):
    rd = (pw.get(wx, {}) or {}).get('root_detail', {}) or {}
    return {br for br, v in rd.items() if v in _BEN_TAGS}


def build_special_patterns(pillars, facts, wp, tian_he=None, climate=None):
    pw = (wp or {}).get('wuxing_power', {})
    dm_wx = (wp or {}).get('daymaster_element')
    day_stem = (pillars.get('day') or [''])[0]
    out = {'patterns': [], 'cong_type': None, 'cong_state': None, 'zhuanwang': None,
           'hua_qi': None, 'mu_mie': None, 'mu_mie_state': None, 'liangqi': None,
           'zhuanwang_state': None,
           'judgment_status': 'STRUCTURE_ONLY'}
    if not dm_wx or dm_wx not in pw:
        out['judgment_status'] = 'INSUFFICIENT_INPUT'
        return out

    yin_wx, ss_wx, cai_wx, gs_wx = SHENG_ME[dm_wx], SHENG[dm_wx], KE[dm_wx], KE_ME[dm_wx]
    dm, yin = pw[dm_wx], pw.get(yin_wx, {})
    ss, cai, gs = pw.get(ss_wx, {}), pw.get(cai_wx, {}), pw.get(gs_wx, {})

    dm_ben = int(dm.get('ben_n', 0)); dm_stem = int(dm.get('stem_n', 0)); dm_ju = int(dm.get('ju_n', 0))
    yin_ben = int(yin.get('ben_n', 0)); yin_stem = int(yin.get('stem_n', 0)); yin_ju = int(yin.get('ju_n', 0))
    gs_ben = int(gs.get('ben_n', 0)); gs_stem = int(gs.get('stem_n', 0)); gs_ju = int(gs.get('ju_n', 0))
    cai_ben = int(cai.get('ben_n', 0)); cai_stem = int(cai.get('stem_n', 0))
    cai_ju = int(cai.get('ju_n', 0)); cai_banhe = int(cai.get('banhe_n', 0))
    ss_ben = int(ss.get('ben_n', 0)); ss_stem = int(ss.get('stem_n', 0)); ss_ju = int(ss.get('ju_n', 0))
    gs_ling = gs.get('ling_state') == '旺'; cai_ling = cai.get('ling_state') == '旺'; ss_ling = ss.get('ling_state') == '旺'
    dm_ling = dm.get('ling_state') == '旺'

    # ---- L2母灭判定(接入L2-3修正版) ----
    branches = [p[1] if len(p) > 1 else '' for p in [pillars.get('year', []), pillars.get('month', []), pillars.get('day', []), pillars.get('hour', [])]]
    stems = [p[0] if p else '' for p in [pillars.get('year', []), pillars.get('month', []), pillars.get('day', []), pillars.get('hour', [])]]
    mumie = check_mumie(branches, stems, day_stem)
    if mumie['status'] == '母灭':
        out['mu_mie'] = mumie['taishi']
        out['mu_mie_state'] = mumie['state']
        out['judgment_status'] = 'PURE_RULE'
        return out

    # ---- 孤根被冲拔(T30): 身/印本气仅一支、被六冲、对立成势而日主不当令 ----
    chong = (facts.get('combination_facts', {}) or {}).get('liuchong', [])
    chong_map = {}
    for pair in chong:
        if len(pair) == 2:
            chong_map[pair[0]] = pair[1]; chong_map[pair[1]] = pair[0]
    self_br = _ben_branches(pw, dm_wx) | _ben_branches(pw, yin_wx)
    struck = set()
    opp_ben = cai_ben + gs_ben + ss_ben
    if len(self_br) <= 1:
        for r in self_br:
            if r in chong_map:
                r2_wx = BRANCH_WX.get(chong_map[r])
                opp_dom = gs_ling or gs_ju >= 1 or cai_ju >= 1 or opp_ben >= 2 \
                    or int(pw.get(r2_wx, {}).get('ben_n', 0)) >= 1
                self_dom = dm_ling or dm_ju >= 1
                if opp_dom and not self_dom:
                    struck.add(r)
    dm_ben_eff = max(0, dm_ben - len(_ben_branches(pw, dm_wx) & struck))
    yin_ben_eff = max(0, yin_ben - len(_ben_branches(pw, yin_wx) & struck))
    root_struck = bool(struck)
    # 合局化去身根/印根: 入完整三合/三会、化神为财或官杀(克泄方)的支, 该根从化神
    #   覆盖本气(BEN)/中气(ZHONG)/余气(YU)三级 —— 依据:
    #     DT-0348(癸亥乙卯己未丁卯, DTS准神)「未土又会木局, 不得不从杀矣」
    #       印火在未为中气根, 未入亥卯未木局 -> 印根被化 -> 从杀
    #     PZ-0232(癸卯丁巳庚寅庚辰) 印土辰为本气根, 辰/寅入寅卯辰木局 -> 从杀
    #     PZ-0137(戊辰甲寅壬戌丙午) 印金戌为中气根, 戌入寅午戌火局(火克金) -> 从财
    #   反证(不入局则不算被化):
    #     PZ-0002(丁卯丙午庚午己卯) 印土午中气根, 无三合三会 -> 不从(沈孝瞻L187原案)
    #     PZ-0001(癸酉辛酉乙丑辛巳) 印水丑中气根, 丑入巳酉丑金局, 金为官杀亦化 ->
    #       该盘判据另有争点(见 rootless 注释), 但化根机制本身按本条统一处理。
    _hh_dm, _hh_yin = set(), set()
    _ROOT_TAGS = ('BEN', 'ZHONG', 'YU')   # 本气/中气/余气 三级均会被合局化去
    _cf0 = facts.get('combination_facts', {}) or {}
    for _items in (_cf0.get('sanhe', []), _cf0.get('sanhui', [])):
        for _it in _items:
            _mm = re.match(r'^([子丑寅卯辰巳午未申酉戌亥])([子丑寅卯辰巳午未申酉戌亥])([子丑寅卯辰巳午未申酉戌亥]).*?([金木水火土])', str(_it))
            if not _mm: continue
            _g = _mm.groups(); _jwx = _g[3]
            if _jwx not in (cai_wx, gs_wx): continue
            for _br in _g[:3]:
                _tag = str((dm.get('root_detail', {}) or {}).get(_br, ''))
                if BRANCH_WX.get(_br) == dm_wx and _tag in _ROOT_TAGS:
                    _hh_dm.add(_br)
                _ytag = str((yin.get('root_detail', {}) or {}).get(_br, ''))
                if BRANCH_WX.get(_br) == yin_wx and _ytag in _ROOT_TAGS:
                    _hh_yin.add(_br)
    # 化根后重算各级根数(中气/余气同样被扣)
    _hh_cnt_yin = len(_hh_yin)
    _yin_zhong_eff = max(0, int(yin.get('zhong_n', 0)) - sum(
        1 for _b in _hh_yin if str((yin.get('root_detail', {}) or {}).get(_b, '')) == 'ZHONG'))
    _yin_yu_eff = max(0, int(yin.get('yu_n', 0)) - sum(
        1 for _b in _hh_yin if str((yin.get('root_detail', {}) or {}).get(_b, '')) == 'YU'))
    if _hh_dm or _hh_yin:
        dm_ben_eff = max(0, dm_ben_eff - sum(
            1 for _b in _hh_dm if str((dm.get('root_detail', {}) or {}).get(_b, '')) in _ROOT_TAGS))
        yin_ben_eff = max(0, yin_ben_eff - _hh_cnt_yin)
        root_struck = root_struck or bool(_hh_dm or _hh_yin)
    # V7.17: 增加yin_stem==0——印星透干即使根被冲仍有用(原典L1430癸生卯月酉被卯冲, 辛金透干以印为夫, 不应从财)
    # V7.17(b): rootless门槛保守——印透即不走从格(正格优先: 印是正格常见用神, 财格用印/阳刃制刃/财旺生官等)
    #          PZZQ4941"印须通根才不从"是从格成立后内部的破格判定(ge_jie_layer印不从fallthrough), 非rootless门槛
    #          V7.19曾放宽(印虚透无根->进从格), 引入4条正格被抢误报(PZ-0260财格用印/QT-0486阳刃制刃/QT-bare-022财旺生官), 已回退
    #
    # [2026-10-01 PATCH-3b] 按 Human 裁决(原典统一标准: 印星通根则不从, 仅透干无根则假从仍从) 放宽:
    #   沈孝瞻《论杂格》「若透印则身赖印生而不从」的完整含义是「印星有根能生身则不从」,
    #   而非「印星在天干出现即不从」。PZZQ4941「从财格而有印, 须看印是否通根」是补充判据。
    #   ge_jie_layer 从格分支已按 `_yin_tou and _yin_bn >= 1 -> _not_cong` 实现同一标准(ben_n>=1 本气根),
    #   两层规则原不一致, 此处对齐。
    #   印(土)带本气根(ben_n>=1)或被合去根(_hh_yin)仍走 yin_ben_eff; 纯虚透(ben_n=0)放行进从格段。
    # 印透干 + 有根(化根后仍存) -> 不进从格段(真从格定义 SHUAI.003/DTS 从象章)
    #   依据 PZZQ L187(沈孝瞻原案 丁卯丙午庚午己卯)「庚金虽弱, 透印有根, 即不能从」
    #        PZZQ L4936《论杂格》「若透印则身赖印生而不从」
    #        DTS  DT-0235「嫌其甲木透干, 不能弃命从杀, 只得杀重用印」
    #        SFTK SF-0032「身主有气, 又不能从杀也」
    #        QTBJ QT-0508「庚金阳干, 不易言从」
    #   关键: 「有根」按【化根后】的三级(本气/中气/余气)余量计, 不只看本气。
    #     中气根同样算有根 —— 但若该支被三合/三会化掉则不算(见 L123-156 化根机制)。
    #     正面: PZ-0002(印午中气, 无局) 不从; DT-0348(印未中气, 入亥卯未木局) 从;
    #            PZ-0232(印辰本气, 入寅卯辰木局) 从; PZ-0137(印戌中气, 入寅午戌火局) 从;
    #            PZ-0001(印丑中气, 入巳酉丑金局, 金为官杀亦化) -> 从(与沈孝瞻原断有争, 见下)
    #     反面: 印透干但完全无根 -> 仍从(PZ-0260 丁酉己酉戊子壬子 / QT-bare-022, 印 root={})
    #   与 V7.17 旧版区别: 旧版「印透即不从」漏「有根」半, 会误伤无根印盘; 本版要求透干 AND 有余根。
    _yin_block = (yin_stem >= 1
                  and (yin_ben_eff >= 1 or _yin_zhong_eff >= 1 or _yin_yu_eff >= 1))
    rootless = (dm_ben_eff == 0 and yin_ben_eff == 0 and not _yin_block)
    # 从格判据(综合版): 印比虚浮无根不算扶抑(子平真诠'印无根不得相从'、滴天髓'绝无一毫生扶之意')
    # 透干且有本气根才算support; 透干无根=虚浮(如DT-0032辛金透干x4地支无根)
    virtual_support = (dm_stem >= 1 and dm_ben >= 1) or (yin_stem >= 1 and yin_ben >= 1)
    _light_tags = ('YU', 'MU_KU', 'SPECIAL', 'LONGSHENG_YIN')
    party = dm_ben_eff + yin_ben_eff + dm.get('banhe_n', 0)   # #PCT-MARK 专旺党众=日主本气+印本气+半合本方(印生身/半局助党)

    # 官杀成势(含财本气生透干杀) / 食伤成势(提前供救应判断)
    gs_pow_pre = _shi(gs)   # 食神制杀救应只认官杀本气真成势; 财生杀归从杀分类, 不在此封从财
    _dmrd = dm.get('root_detail', {}) or {}
    dm_light = any(any(t in str(v) for t in _light_tags) for v in _dmrd.values())
    _ss_gen = len((ss.get('root_detail', {}) or {})) > 0
    _ss_youli = (ss_ben >= 1) or (ss_stem >= 1 and _ss_gen) or (ss_stem >= 2)
    # 制杀救应(逆局): 食伤有力且财不透(无财通关, 食伤直克官杀), 或食伤叠透力足制杀;
    # 单透又有财透=伤官生财生官顺局(丙戌壬辰), 不救
    zhi_sha_save = (dm_ben_eff == 0 and dm_light and gs_pow_pre and _ss_youli
                    and (cai_stem == 0 or ss_stem >= 2))

    # E 孤根无冲而被当令成势官杀克拔(乙卯己卯): 日主仅一孤本气根、无印、官杀当令ben>=2成势、无食伤制杀
    ke_struck = (dm_ben_eff == 1 and yin_ben_eff == 0 and (gs_ling or gs_ju >= 1) and gs_ben >= 2
                 and ss_ben == 0 and ss_stem == 0)
    # F 日主真无根(含无轻根)、仅一孤印, 被当令成势之神反侮/克没(壬寅辛亥辰土孤印被当令旺水反侮, 辰为水库同化)
    _yin_ke = KE[yin_wx]
    _yk = pw.get(_yin_ke, {}) or {}
    yin_fanwu = (dm_ben_eff == 0 and not dm_light and yin_ben_eff == 1
                 and ((ss_ling and ss_ben >= 2)
                      or (_yk.get('ling_state') == '旺' and int(_yk.get('ben_n', 0)) >= 2)))
    yin_ke2 = (dm_ben_eff == 0 and yin_ben_eff == 1 and gs_ling and gs_ben >= 2 and cai_ben >= 1)
    # G 寄生宫/长生根而无同五行本气支根(土寄禄火宫: 戊禄巳旺午本气是火印、长生寅本气是甲杀),
    #   官杀当令本气成势且透干、印完全不透(化杀不力/虚不纳印)、食伤全不制 -> 假从杀, 寄宫根待运拔 CANDIDATE
    dm_true_ben = sum(1 for _v in _dmrd.values() if _v == 'BEN')
    jia_xu_sha = (dm_true_ben == 0 and dm_ben_eff >= 1
                  and gs_ling and (gs_ben + int(gs.get('banhe_n', 0))) >= 2 and gs_stem >= 1
                  and yin_stem == 0 and ss_ben == 0 and ss_stem == 0)
    # V7.14: 得令日主不从(原典: 得时俱为旺论, 月令本气根是日主根, V7.10排除月令根不应影响从格识别)
    rootless_entry = (not dm_ling) and (rootless or ke_struck or yin_fanwu or yin_ke2 or jia_xu_sha)

    # ---------- 化气格(日干与紧邻月/时干合, 化神得令成势; 先判, 与从格互斥)----------
    # [2026-10-01 PATCH-3e] 恢复化气格独立判定(原第158-215行, 自 87a8022c 取回)。
    #   依据: 沈孝瞻《子平真诠·论杂格》「有从化取格者, 要化出之物, 得时乘令, 四支局全。
    #          如丁壬化木, 地支全亥卯未、寅卯辰, 而又生于春月, 方为大贵。」(canonical L4896-4898)
    #   原案 PZ-0317 甲戌丁卯壬寅甲辰(pollution=沈孝瞻原案) 四条件全中, 引擎此前误判伤官格。
    #   四条件: ①日干与紧邻(月/时)干五合 ②化神得月令 ③化神成势 ④四支局全。
    #
    #   化气格地位: 沈孝瞻原文「有从化取格者」列为独立格局;
    #     徐乐吾注(canonical L4883)「故统归之专旺一类」为旁证, 引擎采沈孝瞻原文独立判定。
    #   四支局全口径: 木有明文(亥卯未 / 寅卯辰), 已实装;
    #     TODO(待原典逐案): 火(寅午戌)/金(申子辰三合)/水(无局)/土(辰戌丑未杂气)
    #     的「局全」定义原典未给, 暂沿用旧判据不设门, 待专案裁决。
    hua_name = None; hua_state = None
    if tian_he and dm_ben_eff <= 8 and yin_ben_eff <= 6:
        for hp in tian_he.get('he_pairs', []):
            pls = hp.get('pillars', [])
            if 'day' not in pls:
                continue
            if not any(q in pls for q in ('month', 'hour')):
                continue   # 年干与日干隔月干=遥合, 不化
            stems_hp = hp.get('stems', [])
            if day_stem not in stems_hp:
                continue
            other = [s for s in stems_hp if s != day_stem]
            if not other:
                continue
            hs = WUHE_HUASHEN.get((day_stem, other[0]))
            if not hs or hs not in pw:
                continue
            # PATCH-3e: 四支局全门(沈孝瞻《论杂格》「有从化取格者…四支局全」)。
            #   木有原文明文列举(亥卯未 / 寅卯辰), 已实装。
            #   该门同时排除 ①临淮侯乙亥己卯丁酉壬寅(有酉金破木, 沈孝瞻段2 明文归印格·带伤食)
            #   ②孙岳戊寅乙卯丁未壬寅(徐注旁证, 局不全) —— 防止化气判掉印格段2 三条原典案例。
            # PATCH-3f: 非木化神一律 continue —— 沈孝瞻未给火/金/水/土的「局全」口径,
            #   无原典依据不设门即等于放行 10 条全为徐注旁证的化气盘(土8/火2/金1)。
            #   木化气有原案(PZ-0307/0317, pollution=沈孝瞻原案)验证, 方准判定。
            if hs != '木':
                continue
            _allz = frozenset(z for z in (pillars[k][1] for k in ('year','month','day','hour')) if z)
            _JU_MU = (frozenset(('亥', '卯', '未')), frozenset(('寅', '卯', '辰')))
            if not any(_j <= _allz for _j in _JU_MU):
                continue
            # V4.7: 化神被克制时只能是CANDIDATE(假化)，不能是CONFIRMED(真化)
            _KE_HUA = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}
            _ke_hs = _KE_HUA.get(hs)
            _all_branches = [pillars[k][1] for k in ('year','month','day','hour')]
            _hs_suppressed = bool(_ke_hs) and any(BRANCH_WX.get(b) == _ke_hs for b in _all_branches)
            hd = pw[hs]
            on_qi = bool(hp.get('huashen_on_month_qi')) or (wp.get('month_element') == hs)
            hb, hju, hs_t = int(hd.get('ben_n', 0)), int(hd.get('ju_n', 0)), int(hd.get('stem_n', 0))
            chengshi = (on_qi or hju >= 1 or hb >= 2
                        or (hs_t >= 1 and hb >= 1 and dm_ben_eff == 0 and yin_ben_eff == 0 and yin_stem == 0))
            if not chengshi:
                # 返象化气格: 日干与紧邻干五合、化神不得令不成势、日主无根、印不重、官杀极弱
                if (dm_ben_eff == 0 and yin_ben_eff <= 1 and not _shi(dm) and not _shi(yin)
                        and gs_ben == 0 and gs_stem <= 1):
                    hua_name = '化%s气格' % hs
                    hua_state = 'CANDIDATE'
                    out['patterns'].append(_pat('ZP-SPECIAL-HUAQI', hua_name, hua_state, hs,
                        '日干与紧邻(月/时)干五合但化神不得令不成势=返象/合而不化(CANDIDATE); 真化须化神得令成势且日主无根无印; 成败取用交化气专审, 不判吉凶',
                        ['tian_he', 'wuxing_power']))
                    out['hua_qi'] = hua_name
                    out['hua_qi_state'] = hua_state
                    break
                continue                                # 合而不化(冬令戊癸不化)
            _GWX_H = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
            _gs_he = 1 if (other and _GWX_H.get(other[0]) == gs_wx) else 0
            if (gs_stem - _gs_he) >= 1 and gs_ben >= 1:
                continue   # 合神外官杀有根透干方为牵挂, 不真化
            hua_name = '化%s气格' % hs
            # V4.7: 化神被克制时不能是CONFIRMED，只能是CANDIDATE(假化)
            if on_qi and dm_ben_eff == 0 and yin_ben_eff == 0 and yin_stem == 0 and (hb >= 1 or hju >= 1 or hs_t >= 1) and not _hs_suppressed:
                hua_state = 'CONFIRMED'
            else:
                hua_state = 'CANDIDATE'                 # 微根/微印/化神被克制=假化
            out['patterns'].append(_pat('ZP-SPECIAL-HUAQI', hua_name, hua_state, hs,
                '日干与紧邻(月/时)干五合、化神得令或成势；真化须日主无根无印，微根/微印为假化(CANDIDATE)；隔位合、化神不当令不成势为合而不化；化神=木另须四支局全(亥卯未/寅卯辰, 沈孝瞻原文明举)；成败取用交化气专审, 不判吉凶',
                ['tian_he', 'wuxing_power']))
            out['hua_qi'] = hua_name
            out['hua_qi_state'] = hua_state
            break

    # 官杀成势(含财本气生透干杀)
    gs_pow = _shi(gs) or (gs_stem >= 1 and cai_ben >= 1)
    # 财明透成局主导(压食伤, 使从财而非从儿)
    cai_lead = ((cai_ju >= 1 and cai_stem >= 1)
                or (cai_banhe >= 2 and cai_stem >= 1 and ss_stem <= 1)
                or (cai_ling and _shi(cai) and cai_stem >= 1))
    ss_pow = _shi(ss)

    # ---------- 从格 ----------
    cong = None; side = None; cstate = None
    if rootless_entry and not zhi_sha_save:  # P0-b: 移除not hua_name互斥分支
        sides = {'食伤': (ss, ss_wx), '财': (cai, cai_wx), '官杀': (gs, gs_wx)}
        shi_sides = {k: (v, wx) for k, (v, wx) in sides.items()
                     if (k == '官杀' and gs_pow) or (k != '官杀' and _shi(v))}
        if shi_sides:
            if ss_ling and ss_pow and gs_stem >= 1 and gs_ben >= 1 and ss_ben > gs_ben and cai_stem >= 1:
                # 食伤当令成势、制去有根透干之孤官杀(制杀太过/去杀存财)、财透承接 -> 从财
                cong, side = '从财格', cai_wx
            elif gs_pow and (gs_ben >= 1 or gs_stem >= 2) and gs_stem >= 1 and cai_ben >= 1 and not ss_ling and ss_stem == 0 and ss_ju == 0:
                # 财(有本气)生透干之杀、食伤不当令不逆局, 气归于杀 -> 从杀用财
                # [2026-10-01 PATCH-3b] 官杀成势门槛: 本气根(gs_ben>=1) 或 双透(gs_stem>=2)。
                #   依 PZZQ《论杂格》「四柱皆煞,而日主无根,舍而从之」——「皆」字要求官杀成势,
                #   中气/余气根(gs_zhong>0)是「有根」非「成势」, 单透+中气不成势, 不得气归于杀。
                #   PZ-0136(甲寅丙寅庚寅戊寅): 丙一透+寅中气, 财四寅本气极旺 -> 落 order 兜底 -> 从财。
                #   golden 丁卯丙寅辛亥庚寅: 丙丁双透成势, 财寅卯亥 -> 仍从杀。
                cong, side = '从杀格', gs_wx
            elif gs_ling and gs_pow:
                # 官杀当令成势(不论食伤) -> 从杀用财
                cong, side = '从杀格', gs_wx
            elif ss_ling and ss_pow and not gs_pow:
                if gs_stem >= 1 and gs_ben >= 1 and ss_ben > gs_ben and cai_stem >= 1:
                    # 食伤当令制去孤官杀、财透承接(去杀存财), 日主无根 -> 从财
                    cong, side = '从财格', cai_wx
                elif cai_lead or (cai_ling and _shi(cai)):
                    cong, side = '从财格', cai_wx
                elif ss_stem >= 2 and cai_stem == 0:
                    cong, side = '从儿格', ss_wx
                elif ss_ben > cai_ben:
                    cong, side = '从儿格', ss_wx
                elif ss_ben == cai_ben and cai_stem >= 1:
                    cong, side = '从财格', cai_wx
                elif ss_ben == cai_ben:
                    cong, side = '从儿格', ss_wx
                else:
                    cong, side = '从财格', cai_wx
            elif cai_ling and ss_stem >= 2 and ss_ben >= 1 and cai_stem == 0:
                # 财虽当令, 食伤叠透通根、财藏不透, 发泄在食伤 -> 顺局从儿
                cong, side = '从儿格', ss_wx
            elif cai_ling and _shi(cai):
                cong, side = '从财格', cai_wx
            elif gs_pow and (gs_ben >= 1 or gs_stem >= 2) and gs_stem >= 1 and cai_ben >= 1 and not ss_ling and ss_stem == 0 and ss_ju == 0:
                # 丁丑壬寅: 壬杀透干、申金财生杀、丑辰湿土通关(食伤不当令不逆局), 气归于杀 -> 从杀用财
                # [2026-10-01 PATCH-3b] 同一成势门槛(gs_ben>=1 or gs_stem>=2), 理由见 L214 注释。
                cong, side = '从杀格', gs_wx
            else:
                order = sorted(shi_sides.items(),
                               key=lambda kv: (_fkey(kv[1][0]) if kv[0] != '官杀' else _fkey(gs)),
                               reverse=True)
                top_name, (top_d, top_wx) = order[0]
                if top_name == '官杀':
                    cong, side = ('从杀格' if (gs_ben >= 2 or gs_ju >= 1 or gs_ling or cai_ben >= 1) else '从官格'), gs_wx
                elif top_name == '财':
                    # 食伤叠透而财藏不透=从儿(儿会财局); 财明透成局=从财
                    if ss_pow and ss_stem >= 2 and cai_stem == 0 and not cai_lead:
                        cong, side = '从儿格', ss_wx
                    else:
                        cong, side = '从财格', cai_wx
                elif top_name == '食伤':
                    if cai_lead:
                        cong, side = '从财格', cai_wx
                    elif ss_stem >= 2 and cai_stem == 0 and ss_pow:
                        cong, side = '从儿格', ss_wx
                    elif (cai_ben >= 1 or cai_ju >= 1) and not (ss_stem >= 2 and cai_stem == 0):
                        cong, side = '从财格', cai_wx
                    else:
                        cong, side = '从儿格', ss_wx
                else:
                    cong, side = '从势格', top_wx
                if cong in ('从财格', '从杀格', '从官格', '从儿格') and len(shi_sides) >= 2:
                    keys = sorted(((9, 0, 0) if k == '官杀' else _fkey(v[0]) for k, v in shi_sides.items()),
                                  reverse=True)
                    if keys[0][0] == keys[1][0] and keys[0][1] == keys[1][1] and not (gs_ling or cai_ling or ss_ling):
                        cong, side = '从势格', None
            cstate = 'CANDIDATE' if (virtual_support or ke_struck or yin_fanwu or yin_ke2 or jia_xu_sha) else 'CONFIRMED'

    # ---------- 从儿不论身强弱(日主非比劫当令、可带一禄根; 官杀无、食伤成势、无印逆局)----------
    if not cong:  # P0-b: 移除not hua_name互斥分支
        if (gs_ben == 0 and gs_stem == 0 and yin_ben_eff == 0 and ss_pow and not dm_ling
                and not cai_lead and dm_ben_eff <= 1):
            if cai_stem >= 2 and cai_ben >= 1 and ss_stem >= 1 and ss_ben <= cai_ben + 1:
                # 食伤透干泄身太过(干支同党)、财复透干成众有根, 食伤+财并旺顺克泄 -> 从势
                # (戊戌丁巳火旺木焚顺火土); 食伤当令而不透干(丁巳癸卯木在支)未焚身, 仍专从儿
                # 食伤与财两神并旺、财透干成众(食伤生财顺局), 衰极从其势 -> 从势(戊戌丁巳顺火土)
                cong, side = '从势格', None
            else:
                cong, side = '从儿格', ss_wx
            cstate = 'CONFIRMED' if dm_ben_eff == 0 else 'CANDIDATE'

    # ---------- 气候虚湿寒土假从(辰丑湿土寒冻、火印全无, 土虚不能用, 反顺旺水之财; 见火暖则土能任财而翻转, 故只CANDIDATE)----------
    if not cong and climate and 'XU_SHI_HAN_TU' in (climate.get('structure_flags') or []):  # P0-b: 移除not hua_name互斥分支
        if _shi(cai) or cai_ju >= 1 or (cai_ben >= 1 and cai_stem >= 1):
            cong, side = '从财格', cai_wx
            cstate = 'CANDIDATE'

    if cong == '从杀格':
        GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
        _YG = set('甲丙戊庚壬'); _dm_y = day_stem in _YG
        def _sha(g):  # 与日主同阴阳=七杀, 异=正官
            return (g in _YG) == _dm_y
        _zg = _zs = _tg = _ts = 0
        _hs = facts.get('hidden_stems', {}) or {}
        for _k in ('year', 'month', 'day', 'hour'):
            _hg = (_hs.get(_k) or [''])[0]
            if _hg and GAN_WX.get(_hg) == gs_wx:
                if _sha(_hg): _zs += 1
                else: _zg += 1
            _tg0 = pillars[_k][0]
            if _k != 'day' and GAN_WX.get(_tg0) == gs_wx:
                if _sha(_tg0): _ts += 1
                else: _tg += 1
        if _zg > _zs or (_zg == _zs and _tg > _ts):
            cong = '从官格'   # 正官(异阴阳)本气支占优, 或支均而正官透干占优; 滴天髓官杀多混称, 否则仍从杀
    if cong:
        note = '日主无本气根、无有根印比，对立方成势顺其势；虚透印比地支不载/孤根被冲拔为假从(CANDIDATE)；从儿不论身强弱；虚湿寒土(辰丑寒冻、火印全无)虽带湿土本气根而寒冻不能用、反顺旺水之财为气候假从(CANDIDATE, 见火暖翻转)；只记结构定性，不判用神成败吉凶'
        out['patterns'].append(_pat('ZP-SPECIAL-CONG', cong, cstate, side, note,
            ['daymaster_root', 'wuxing_power', 'combination_facts']))
        out['cong_type'], out['cong_state'] = cong, cstate

    # ---------- 专旺/一行得气（P0-b重构：月令当旺降级为置信度加权项） ----------
    # P0-b: 月令当旺从硬门槛降级为置信度加权项（《碧渊赋》未要求月令当旺，只要求局全透干不见官杀）
    _month_branch = pillars['month'][1]
    _month_wx = BRANCH_WX.get(_month_branch)
    _is_ling = (_month_wx == dm_wx)  # 月令当旺（现仅作置信度加权，不入硬闸门）
    # 土特殊: 四季月辰戌丑未都是土旺
    if dm_wx == '土' and _month_branch in ('辰', '戌', '丑', '未'):
        _is_ling = True
    
    # 本方三合/三会成局: 局内支本气若为官杀/财, 被合化为本方(官杀化比劫), 专旺判定扣除(合局化破)
    gs_ben_zw, cai_ben_zw = gs_ben, cai_ben
    _cf = facts.get('combination_facts', {}) or {}
    for _items in (_cf.get('sanhe', []), _cf.get('sanhui', [])):
        for _it in _items:
            _m = re.match(r'^([子丑寅卯辰巳午未申酉戌亥])([子丑寅卯辰巳午未申酉戌亥])([子丑寅卯辰巳午未申酉戌亥]).*?([金木水火土])', str(_it))
            if not _m: continue
            _b1, _b2, _b3, _jwx = _m.groups()
            if _jwx != dm_wx: continue
            for _br in (_b1, _b2, _b3):
                _bw = BRANCH_WX.get(_br)
                if _bw == KE_ME[dm_wx] and str(gs.get('root_detail', {}).get(_br, '')).startswith(('BEN',)):
                    gs_ben_zw -= 1
                elif _bw == KE[dm_wx] and str(cai.get('root_detail', {}).get(_br, '')).startswith(('BEN',)):
                    cai_ben_zw -= 1
    gs_ben_zw = max(0, gs_ben_zw); cai_ben_zw = max(0, cai_ben_zw)
    
    # P0-b.3: 天干合化财星扣除（乙庚合化金，乙不再算财星透干）
    cai_stem_zw = cai_stem  # 财星透干数（扣除合化后）
    gs_stem_zw = gs_stem    # 官杀透干数（扣除合化后）
    if tian_he:
        for hp in tian_he.get('he_pairs', []):
            # 合化神为日主五行 = 合化成功，该合化的干不再算财星/官杀
            if hp.get('huashen_wuxing') == dm_wx:
                he_stems = hp.get('stems', [])
                for gan in he_stems:
                    # 如果合化神是日主五行，那两个干都不再算对立方
                    # 但我们只需要扣财星/官杀透干
                    # 财星五行是KE[dm_wx]（克我者为官杀，我克者为财）
                    # 不对：我克者为财，克我者为官杀
                    # dm_wx的财星是KE[dm_wx]（我克），官杀是KE_ME[dm_wx]（克我）
                    gan_wx = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
                              '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}.get(gan)
                    if gan_wx == cai_wx:  # 该干是财星
                        cai_stem_zw = max(0, cai_stem_zw - 1)
                    elif gan_wx == gs_wx:  # 该干是官杀
                        gs_stem_zw = max(0, gs_stem_zw - 1)
    
    guo_xie = (ss_stem >= 2 and ss_ben >= 1 and dm_ben_eff <= 3)   # #PCT-MARK 食伤透干有根成党=过泄/两气成象, 不判纯一行专旺; 但日主本气根>=4(如四库全)时食伤只是泄秀仍判专旺(辛未辛丑戊辰壬戌稼穑格用辛金吐秀)

    _dm_ben_pure = sum(1 for _k in ('year','month','day','hour') if BRANCH_WX.get(pillars[_k][1])==dm_wx) + dm_ju
    # 印旺非专旺: 无比劫方局、比劫纯本气(不含寄于印官本位的长生根BEN_CS)<=1、而印本气成势(>=3)=母旺子相、印旺正格身旺任官,
    # 非一行专旺(阳干长生在印母之宫, 如壬生申, 申本气庚金是印, 不作水比劫成方); DTS L2251 金印3/水纯根1, 任注喜土火官杀科甲, 非润下
    _yin_wang_not_zw = (dm_ju == 0 and _dm_ben_pure <= 1 and yin_ben_eff >= 3)
    
    # P0-b: kepo破格检测（局不被冲克破）——《滴天髓》"象不可破"
    # 检测：官杀/财是否有本气透干成势（真破局）
    kepo_zw = (gs_ben_zw >= 1 and gs_stem_zw >= 1) or (cai_ben_zw >= 2 and cai_stem_zw >= 1)  # P0-b.6: 使用zw版本
    
    # P0-b: ganhe_tight（天干五合紧邻）——《渊海·论运化气》"天干化合者秀气"
    ganhe_tight = False
    if tian_he:
        for hp in tian_he.get('he_pairs', []):
            if hp.get('huashen_wuxing') == dm_wx:
                ganhe_tight = True
                break
    
    # P0-b: 硬闸门（任一不满足 → REJECTED）
    # 1. 官杀无本气、不透、不成局
    # 2. 财至多一余气、不透、不成局
    # 3. 局不被冲克破
    gate_ok = (
        (gs_ben_zw == 0 and gs_stem_zw == 0 and gs_ju == 0)
        and (cai_ben_zw <= 1 and cai_stem_zw == 0 and cai_ju == 0)
    )
    
    # P0-b: 成格核心（CONFIRMED_ZW）
    # 条件：支局全（dm_ju >= 1）+ 透干含本行 + 日主属该行（day_in_row）
    tougan_row = (dm_stem >= 1)  # 本行透干
    day_in_row = (day_stem in ['甲', '乙'] and dm_wx == '木') or \
                 (day_stem in ['丙', '丁'] and dm_wx == '火') or \
                 (day_stem in ['戊', '己'] and dm_wx == '土') or \
                 (day_stem in ['庚', '辛'] and dm_wx == '金') or \
                 (day_stem in ['壬', '癸'] and dm_wx == '水')
    
    confirmed_zw = gate_ok and (dm_ju >= 1) and tougan_row and day_in_row 
    
    # P0-b: 候选（CANDIDATE_ZW，半局未全）
    candidate_zw = gate_ok and (party >= 4 and dm_ben_eff >= 2) and tougan_row 
    
    if dm_ben_eff >= 1 and not _yin_wang_not_zw:
        if confirmed_zw:
            zw = ZHUANWANG_NAME.get(dm_wx)
            out['patterns'].append(_pat('ZP-SPECIAL-ZHUANWANG', zw, 'CONFIRMED', dm_wx,
                '支局全、透干含本行、日主属该行，官杀财无本气不透，一行得气',
                ['combination_facts', 'wuxing_power', 'tian_he']))
            out['zhuanwang'] = zw
            out['zhuanwang_state'] = 'CONFIRMED'
        elif candidate_zw:
            zw = ZHUANWANG_NAME.get(dm_wx)
            out['patterns'].append(_pat('ZP-SPECIAL-ZHUANWANG', zw, 'CANDIDATE', dm_wx,
                '党众成势、透干含本行、日主属该行，官杀/财仅虚透无根；支局未全为候选',
                ['wuxing_power', 'tian_he']))
            out['zhuanwang'] = zw
            out['zhuanwang_state'] = 'CANDIDATE'
    # P0-b: _gate_debug 调试信息（记录哪一道闸门拒收）
    gate_debug = []
    if not gate_ok:
        if not (gs_ben_zw == 0 and gs_stem_zw == 0 and gs_ju == 0):  # P0-b.6: 使用zw版本
            gate_debug.append(f"官杀闸: gs_ben_zw={gs_ben_zw}, gs_stem_zw={gs_stem_zw}, gs_ju={gs_ju}")
        if not (cai_ben_zw <= 1 and cai_stem_zw == 0 and cai_ju == 0):  # P0-b.6: 使用zw版本
            gate_debug.append(f"财星闸: cai_ben_zw={cai_ben_zw}, cai_stem_zw={cai_stem_zw}, cai_ju={cai_ju}")
    if not day_in_row:
        gate_debug.append(f"day_in_row: day_stem={day_stem}, dm_wx={dm_wx}")
    if not tougan_row:
        gate_debug.append(f"tougan_row: dm_stem={dm_stem}")
    if dm_ju < 1:
        gate_debug.append(f"dm_ju: {dm_ju} < 1")

    # P0-b: _gate_debug补充中间量
    gate_debug.append(f"score={score if 'score' in dir() else 'N/A'}")
    gate_debug.append(f"party={party}, dm_ben_eff={dm_ben_eff}, ganhe_tight={ganhe_tight}")
    
    # P0-b: 输出_gate_debug调试信息
    out['_gate_debug'] = gate_debug

    # ---------- 从格并列候选(从旺/从杀, 仅当主从格不是该类型时添加, 供经典多解参考)----------
    _existing_cong = set(p['name'] for p in out['patterns'] if p.get('pattern_id') == 'ZP-SPECIAL-CONG')
    # 从旺格: 日主旺极+有印+官杀极弱+财不透干(不要求地支成方局, 区别于专旺格)
    if '从旺格' not in _existing_cong and not out['zhuanwang']:
        if (_shi(dm) and (yin.get('ben_n',0) >= 1 or yin.get('stem_n',0) >= 1)
                and gs_ben_zw == 0 and gs_stem_zw <= 1 and cai_stem_zw == 0 and not ss_ling):  # P0-b.7: 使用zw版本
            out['patterns'].append(_pat('ZP-SPECIAL-CONG', '从旺格', 'CANDIDATE', dm_wx,
                '日主旺极、印比成势、官杀财极弱=从旺/从强格候选(CANDIDATE); 区别于专旺格(不要求地支成方局); 只记结构定性, 不判用神成败吉凶',
                ['daymaster_root', 'wuxing_power']))
    # 从杀格并列: 官杀透干+财生官杀+食伤不当令+日主无根或根极弱(允许与化气格共存, 经典多解)
    if '从杀格' not in _existing_cong:
        if (gs_stem_zw >= 1 and cai_ben_zw >= 1 and not ss_ling  # P0-b.7: 使用zw版本
                and ss_stem <= 2 and dm_ben_eff <= 1 and yin_ben_eff <= 1):
            out['patterns'].append(_pat('ZP-SPECIAL-CONG', '从杀格', 'CANDIDATE', gs_wx,
                '官杀透干、财生官杀、食伤不当令不逆局、日主无根或根极弱=从杀格候选(CANDIDATE); 只记结构定性, 不判用神成败吉凶',
                ['daymaster_root', 'wuxing_power']))

    # ---------- 两气成象(天干地支本气仅两行、各成势、相生成象; 顺食伤秀神, 不判吉凶) ----------
    if not out['cong_type'] and not out['zhuanwang']:  # P0-b: 移除not hua_name互斥分支
        _GW2={'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
        _seq=[_GW2[pillars[_k][0]] for _k in ('year','month','day','hour')] \
            + [BRANCH_WX[pillars[_k][1]] for _k in ('year','month','day','hour')]
        _cnt={}
        for _w in _seq: _cnt[_w]=_cnt.get(_w,0)+1
        _pres=[w for w in ('木','火','土','金','水') if _cnt.get(w,0)>0]
        # 假两气排除(DTS L862癸亥甲寅): 月令食伤当令, 且日主本气根支被六合化为食伤(寅亥合木、水根化木),
        # 食伤太重泄身(任注'寅亥化木,伤官太重'), 乃正格伤官用印(喜印官、逢克方反吉), 非两气成象(真两气逢克泄必凶)
        _LIUHE_HS={('子','丑'):'土',('丑','子'):'土',('寅','亥'):'木',('亥','寅'):'木',('卯','戌'):'火',('戌','卯'):'火',
                   ('辰','酉'):'金',('酉','辰'):'金',('巳','申'):'水',('申','巳'):'水',('午','未'):'土',('未','午'):'土'}
        _ss_lin = BRANCH_WX.get(pillars['month'][1])==SHENG.get(dm_wx)
        _gen_hua_ss = False
        for _pr in (facts.get('combination_facts', {}) or {}).get('liuhe', []):
            if _LIUHE_HS.get((_pr[0], _pr[1]))==SHENG.get(dm_wx) \
                    and (BRANCH_WX.get(_pr[0])==dm_wx or BRANCH_WX.get(_pr[1])==dm_wx):
                _gen_hua_ss = True
        _not_lq = _ss_lin and _gen_hua_ss
        if len(_pres)==2 and _cnt[_pres[0]]>=3 and _cnt[_pres[1]]>=3 \
                and (SHENG.get(_pres[0])==_pres[1] or SHENG.get(_pres[1])==_pres[0]) and not _not_lq:
            _a,_b=_pres
            _xiu=SHENG.get(dm_wx) if SHENG.get(dm_wx) in (_a,_b) \
                else (SHENG_ME.get(dm_wx) if SHENG_ME.get(dm_wx) in (_a,_b) else None)
            _nm='两气成象(%s%s)'%(_a,_b)
            out['patterns'].append(_pat('ZP-SPECIAL-LIANGQI',_nm,'CONFIRMED',dm_wx,
                '八字天干地支本气仅含%s%s两行、各成势且相生为成象，日主生他者顺食伤秀神、他生日主顺印比；只记结构不判吉凶；相克成象/夹第三行不入'%(_a,_b),
                ['pillars','wuxing_power']))
            out['liangqi']={'name':_nm,'wuxing':[_a,_b],'relation':'相生','xiu':_xiu,'state':'CONFIRMED'}

    # ---------- 母多灭子/生多为克(两级: CONFIRMED真灭 / CANDIDATE印重为病, 不反转方向)----------
    if dm_ben_eff == 0 and not out['cong_type'] and not out['zhuanwang']:  # P0-b: 移除not hua_name互斥分支
        GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
        _pidx = ('year', 'month', 'day', 'hour')
        _b2i = {}
        for _i, _k in enumerate(_pidx):
            _b2i.setdefault(pillars[_k][1], []).append(_i)
        _cfm = facts.get('combination_facts', {}) or {}
        _he = set()
        for _pr in _cfm.get('liuhe', []):
            _he.add(_pr[0]); _he.add(_pr[1])
        for _ju in list(_cfm.get('sanhe', [])) + list(_cfm.get('sanhui', [])):
            for _ch in str(_ju):
                if _ch in BRANCH_WX: _he.add(_ch)
        yin_party_all = yin_ben + int(yin.get('zhong_n', 0)) + int(yin.get('yu_n', 0)) + int(yin.get('banhe_n', 0))
        yin_dom = (yin_ju >= 1 or yin_ben_eff >= 3 or (yin_ben >= 1 and yin_party_all >= 4))
        # 食伤孤本气(不透干、无同类半合/局助)被当令印党(>=3, 印克食伤)围克且无合解 -> 孤泄被夺(厚土埋金克孤亥水)
        ss_ben_e = ss_ben
        _ss_br = _ben_branches(pw, ss_wx)
        if (ss_ben == 1 and ss_stem == 0 and int(ss.get('banhe_n', 0)) == 0 and ss_ju == 0
                and gs_stem == 0 and yin_ben_eff >= 3 and KE.get(yin_wx) == ss_wx
                and not (_ss_br & _he)):
            ss_ben_e = 0
        # 官杀湿土(辰丑)寒冻、无未戌燥土、财(火)食伤(木)无本气 -> 湿土不制水反生印(金多水浊, 三丑生金)
        _zao = sum(1 for _k in _pidx if pillars[_k][1] in ('未', '戌'))
        gs_ben_e = gs_ben
        shi_han = False
        if gs_wx == '土':
            shi_han = (_zao == 0 and cai_ben == 0 and ss_ben_e == 0)
            if shi_han:
                gs_ben_e = 0   # 辰丑湿土寒冻、无火木, 不制水反生印(金多水浊)
        # 三端"真有力"(有则印不埋身): 食伤泄秀 / 官杀制身(官印相生任官) / 财破印
        ss_youli = (ss_ben_e >= 1) or (ss_stem >= 1 and (ss_ben_e >= 1 or yin_stem == 0))
        gs_youli = (gs_ben_e >= 1) or (gs_stem >= 1 and gs_ben_e >= 1) or (gs_ling and not shi_han)
        cai_youli = (cai_ben >= 1 and yin_ju == 0) or (cai_stem >= 1 and cai_ben >= 1 and yin_ju == 0)
        # 成方/成局印被紧邻六冲冲破(卯酉冲印局) -> 非灭
        ju_po = False
        for _pair in _cfm.get('liuchong', []):
            if any(abs(i1 - i2) == 1 for i1 in _b2i.get(_pair[0], []) for i2 in _b2i.get(_pair[1], [])):
                if (_pair[0] in _he) or (_pair[1] in _he):
                    ju_po = True
        # 水冲奔清纯从印(日主木、地支本气全亥子水、无火土克泄本气) -> 从印/润下, 非灭
        _ben_wx = [BRANCH_WX[pillars[_k][1]] for _k in _pidx]
        cong_yin = (dm_wx == '木' and all(w == '水' for w in _ben_wx))
        # 湿土重金埋(金命、印土本气>=3、官火财木无本气、燥土<=1)
        shi_tu_mai = (dm_wx == '金' and yin_ben >= 3 and cai_ben == 0 and gs_ben == 0
                      and not ss_ling
                      and sum(1 for _k in _pidx if pillars[_k][1] in ('未', '戌')) <= 1)
        # 水方局孤泄(食伤孤本气+透干)被成局印党克、印又透干克食伤 -> 水多木漂为病(待病药层分有药无药)
        shui_piao = (yin_ju >= 1 and ss_ben == 1 and KE.get(yin_wx) == ss_wx
                     and int(ss.get('banhe_n', 0)) == 0 and ss_stem >= 1 and yin_stem >= 1)
        if yin_dom and not ju_po and not cong_yin:
            if (not ss_youli and not gs_youli and not cai_youli) or shi_tu_mai:
                mm_state = 'CONFIRMED'
            elif shui_piao:
                mm_state = 'CANDIDATE'
            else:
                mm_state = None
            if mm_state:
                out['patterns'].append(_pat('ZP-SPECIAL-MUMIE', '母多灭子/印势漂没', mm_state, yin_wx,
                    '印绶成势日主无本气根不受生(土重金埋/木多火塞/金多水浊/水多木漂); CONFIRMED=食伤财官三端真有力通道全断(湿土寒冻不制、孤泄被围克夺); 官杀当令化杀/官印相生任官/食伤当令吐秀/财破印/水冲奔从印/成局被冲均非灭; CANDIDATE=水方局孤泄被克漂没为病, 待病药作用层; 不据印多直接判身旺弱, 不判吉凶',
                    ['wuxing_power', 'combination_facts']))
                out['mu_mie'] = '母多灭子/印势漂没'
                out['mu_mie_state'] = mm_state

    # V7.26: 输出根气有效字段供下游yongshen_engine使用
    out['dm_ben_eff'] = dm_ben_eff
    out['yin_ben_eff'] = yin_ben_eff
    out['yin_stem'] = yin_stem

    # V7.26: 输出根气有效字段供下游yongshen_engine使用
    out['dm_ben_eff'] = dm_ben_eff
    out['yin_ben_eff'] = yin_ben_eff
    out['yin_stem'] = yin_stem

    return out



