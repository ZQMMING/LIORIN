# -*- coding: utf-8 -*-
"""用药裁决层 (yongyao_resolve) —— "算→辩→解"之"解".
辩层定主病, 本层按【离散图三边: 制/化/帮】列全药方, 并做友敌安全检查.

三边(全为五行确定性关系):
- 制: 克病五行者 KE_BACK[bw]          (如 食伤制杀/财破印/官杀制比劫)
- 化: 病五行所生 SHENG[bw] (泄病之气) (如 印化杀生身); 反生杀克身则剔除
- 帮: 比劫 dm + 印 SHENG_BACK[dm] 帮身 (如 比劫帮身/印生身); 是病则剔除

安全检查(布尔):
- 药==病五行, 或 药生病五行(帮病) → 剔除
- 化: 药克日主(化财生杀/化食伤生财反耗) → 剔除或降级
- 水泛木浮(bw水)特殊: 加火暖化寒湿 (DTS QI_HOU.008)

只裁决用药方向, 不判吉凶寿夭.
"""
from typing import Any, Dict, List

GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
SHENG_BACK = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
KE_BACK = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}
WX_GAN = {'木': ('甲', '乙'), '火': ('丙', '丁'), '土': ('戊', '己'),
          '金': ('庚', '辛'), '水': ('壬', '癸')}
ZHI_BEN_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
              '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
              '戌': '土', '亥': '水'}

# ★ V7.180 格局用神(源2 fallback): 原典「透官而逢财印即同官格」等——格体喜神(xi_wx)
#   是同格之喜神, 不等于用神; 源1无病时以格之用神主药, 财印等喜神作辅。
#   出处: PZZQ 建禄月劫 L1142-1143「透官而逢财印即同官格; 透财而逢食伤即同财格;
#   透煞而遇制伏即同煞格」; 阳刃 L1140-1141/L4579-4582「以官煞制刃」。
#   仅用于原典明文给定「格之所同」的建禄月劫/阳刃形态; 其余八格的多喜神候选
#   仍按「无授权排序」记 NOT_EVALUABLE(不因列表首项而升格)。
_GE_YONG_BY_SHAPE = {
    '建禄月劫格': {'同官格': '官杀', '同财格': '财', '同煞格': '官杀'},
    '阳刃格': {'用官': '官杀', '用食伤': '食伤'},
}
_GE_YONG_CAT_WX = {'官杀': KE_BACK, '财': KE, '印': SHENG_BACK, '食伤': SHENG}


def _ge_medicine(facts):
    """无病时以格之用神为主药(源2); 无原典可裁的格返回 None(不猜)."""
    wx = derive_ge_yong_wx(facts)
    if not wx:
        return None
    return {'wuxing': wx, 'gan': list(WX_GAN.get(wx, ())),
            'function': '源2:格局用神(无病时格之用神为主药)',
            'kind': '格局用神',
            'classic': 'PZZQ 论用神/论八格: 格之用神(官多同煞用食伤/煞用食制/财官印食各依格取)',
            'blocked': None}


def _ge_base_name(ge):
    g = (ge or '').strip()
    for sep in ('(', '（', '[', '·'):
        if sep in g:
            g = g.split(sep)[0]
            break
    return g.strip()


def _ge_god_counts(facts):
    """按十神归类统计局中成员数(含透干与藏干); 用于八格用神的原典条件判定."""
    cnt = {'官杀': 0, '财': 0, '印': 0, '食伤': 0, '比劫': 0}
    for m in (facts.get('ten_god_members') or []):
        c = _ZHI_WX.get((m.get('ten_god') or '').strip(), '')
        if c in cnt:
            cnt[c] += 1
    return cnt


def _ge_trans_gods(facts):
    """透干十神集合(仅 type=='stem'; 日干本身不计)."""
    return {m.get('ten_god') for m in (facts.get('ten_god_members') or [])
            if m.get('type') == 'stem' and m.get('ten_god')}


def derive_ge_yong_wx(facts):
    """按格名(+形态/透干/藏干)派生格之用神五行; 无法从原典确定时返回空串(不猜).

    判据出处(沈孝瞻《子平真诠》论用神/论八格):
      - 正官格: 官多同煞 -> 食伤制官; 官轻 -> 财(生官)/印(护官)
      - 七煞格: 食伤制煞 / 印化煞
      - 财格: 财逢官则官为用; 印重(印夺财)则取财损印; 财生食伤
      - 印格: 印重用财损印; 官印双全用官
      - 食神格: 食神生财; 带煞用食伤制煞
      - 伤官格: 伤官佩印; 伤官见官用比劫/印; 伤官生财
      - 建禄月劫: 透官/透煞 -> 官杀; 透财 -> 财; 透食伤 -> 食伤
      - 阳刃格: 以官煞制刃; 无官煞用食伤泄秀
    """
    gc = facts.get('ge_cheng') or {}
    base = _ge_base_name(gc.get('ge'))
    shape = gc.get('shape') or ''
    if not (facts.get('pillars') or {}).get('day'):
        # 无四柱实体(合成/单元级 facts)时, 不能据格名凭空派生用神。
        return ''
    if gc.get('special_detected') or gc.get('special_candidates'):
        return ''
    _sp = facts.get('special') or {}
    if _sp.get('zhuanwang') or _sp.get('zhuanwang_state') or _sp.get('patterns'):
        # 特殊格(专旺/从格)候选未核验时, 不得以八格用神替代。
        return ''
    ts = _ge_trans_gods(facts)
    cnt = _ge_god_counts(facts)
    # V7.191: 天干五合事实(闲神合煞/日主合财)参与格用神判定
    _wuhe_stems = set()
    for _p in ((facts.get('stem_combination_facts') or {}).get('wuhe') or []):
        for _s in _p:
            _wuhe_stems.add(_s)
    _cai_stems = [m.get('stem') for m in (facts.get('ten_god_members') or [])
                  if m.get('type') == 'stem' and _ZHI_WX.get(m.get('ten_god'), '') == '财']
    cat = ''
    if base in _GE_YONG_BY_SHAPE:
        cat = _GE_YONG_BY_SHAPE[base].get(shape, '')
    if not cat:
        if base == '正官格':
            # V7.191: 官杀并透而煞被合去(闲神合煞) -> 留官为用(PZZQ「合煞留官,无减福」高太尉案)
            _sha_trans = [m.get('stem') for m in (facts.get('ten_god_members') or [])
                          if m.get('type') == 'stem' and m.get('ten_god') == '七杀']
            _guan_members = [m for m in (facts.get('ten_god_members') or [])
                             if m.get('ten_god') == '正官']
            if _sha_trans and _guan_members and all(_s in _wuhe_stems for _s in _sha_trans):
                cat = '官杀'
            else:
                cat = '食伤' if cnt['官杀'] >= 3 else ('财' if cnt['财'] >= 1 else '印')
        elif base == '七煞格':
            cat = '食伤' if cnt['食伤'] >= 1 else ('印' if cnt['印'] >= 1 else '食伤')
        elif base == '财格':
            # V7.191: 财透干与日主五合 -> 财之情专向日主, 财为用
            # (PZZQ「甲用己财;甲己相合,己土之财,专向日主也」)
            # V7.200 尝试: 「佩印->印」blanket gate 已回退 —— pzzq-004 张耀曾(财格佩印+印乙被财庚
            #   五合去+庚劈甲引丁 L495) 亲证佩印可裁用财; 与朱有卿(L486 间乙不合->用印)/王某
            #   (L543 禄比分财->用印火) 的判别=「印是否被财合去」, 而遥隔合终裁(L480-495
            #   「制于势/各视其格局配合」)机器缺判 —— stem_combination_facts.wuhe 不分间隔/遥隔,
            #   单 gate 会翻 004。维持配合级登记, 详见 ZIPING_CLASSIC_RULES §二十六。
            # V7.203 判据层落地（§二十六.3）:
            #   ①争合修正(PZZQ L541-543 王某案「两癸合戊, 虽不以合论, 而终有合意。
            #     为财格用禄比…时逢归禄」): 与日主五合的财>1=争合妒合(L545 两壬夹丁),
            #     不作「专向日主」论 → 不走单财专向, 归禄在时(禄支==时支)则用禄
            #     (L543「时逢归禄」亲证: 戊禄巳=火); 争合而禄不在时不猜。
            #   ②佩印合去终裁(PZZQ L476-496): 佩印形态+印财五合对存在时, 按三态
            #     裁「印是否被财合去」——合去(adjacent/remote_he)→用财(张耀曾 L495);
            #     未合(blocked/remote_no)→财局可以用印(朱有卿 L486)。
            _dg0 = ((facts.get('pillars') or {}).get('day') or ['', ''])[0]
            _he_dm = [_s for _s in _cai_stems
                      if _s and (_s == _dg0 or STEM_HE_F.get(_s) == _dg0)]
            if len(_he_dm) == 1:
                # ★ V7.205 财专向×佩印并存时用神归印 (PZZQ L530-531 亲证: 己酉丙子戊辰
                #   癸亥「丙火调候为用, 无如戊癸相合, 日主之情, 向财不向印」——戊癸合
                #   仅致「用神之情不专」之瑕(L533), 用神仍是丙火印; L3341「孤财不贵,
                #   佩印帮身, 即印取贵」+L3344「需要佩印, 必是身弱」)。印被财合去之佩印
                #   另经下方终裁裁用财(张耀曾 004, 印乙被庚五合去 L495)。非佩印仍用财
                #   (015 甲用己财专向 L521)。
                if shape != '佩印':
                    cat = '财'
                # 佩印形态: 不即裁, 落入下方佩印终裁(无印财五合对/未合去→印)。
            elif len(_he_dm) > 1:
                _hr = ((facts.get('pillars') or {}).get('hour') or ['', ''])[1]
                if _hr and _LU_ZHI.get(_dg0) == _hr:
                    cat = _LU_WX.get(_dg0, '')
            if not cat and shape == '佩印':
                _yin_stems = [m.get('stem') for m in (facts.get('ten_god_members') or [])
                              if m.get('type') == 'stem' and _ZHI_WX.get(m.get('ten_god'), '') == '印']
                _hequ = False
                for _y in _yin_stems:
                    for _c in _cai_stems:
                        if not _y or not _c or STEM_HE_F.get(_y) != _c:
                            continue
                        _st = _wuhe_span_state(facts, _y, _c)
                        if _st[0] in ('adjacent', 'remote_he'):
                            _hequ = True
                if _hequ:
                    cat = '财'
                elif _yin_stems:
                    cat = '印'
            if not cat:
                if cnt['官杀'] >= 2:
                    cat = '官杀'
                elif cnt['印'] >= 2:
                    cat = '财'
                elif cnt['官杀'] >= 1:
                    cat = '官杀'
                elif cnt['食伤'] >= 1:
                    cat = '食伤'
                else:
                    cat = '财'
        elif base == '印格':
            cat = '财' if (cnt['财'] >= 1 or cnt['印'] >= 3) else '官杀'
        elif base == '食神格':
            cat = '财' if cnt['财'] >= 1 else ('食伤' if cnt['官杀'] >= 1 else '财')
        elif base == '伤官格':
            if cnt['印'] >= 1 and cnt['官杀'] >= 1:
                cat = '印'
            elif cnt['比劫'] >= 1 and cnt['官杀'] >= 1:
                cat = '比劫'
            elif cnt['财'] >= 1:
                cat = '财'
            elif cnt['印'] >= 1:
                cat = '印'
            else:
                cat = '食伤'
        elif base == '建禄月劫格':
            if '七杀' in ts or '正官' in ts:
                cat = '官杀'
            elif cnt['财'] >= 1:
                cat = '财'
            elif cnt['食伤'] >= 1:
                cat = '食伤'
        elif base == '阳刃格':
            cat = '官杀' if cnt['官杀'] >= 1 else ('食伤' if cnt['食伤'] >= 1 else '')
    if not cat:
        return ''
    pl = facts.get('pillars') or {}
    dg = (pl.get('day') or ['', ''])[0]
    dmwx = facts.get('daymaster_element') or GAN_WX.get(dg, '')
    return _GE_YONG_CAT_WX.get(cat, {}).get(dmwx, '')


# V7.191: 天干五合伙伴表(甲己/乙庚/丙辛/丁壬/戊癸)
STEM_HE_F = {'甲': '己', '己': '甲', '乙': '庚', '庚': '乙', '丙': '辛',
             '辛': '丙', '丁': '壬', '壬': '丁', '戊': '癸', '癸': '戊'}

# ★ V7.203 五合终裁判据层(PZZQ 论十干配合性情 L476-496):
#   合之成立分三态——紧贴作合(span=1); 间一位而间干克其配偶=「制于势然也,
#   合而不敢合, 有若无」(L481), 间干不克=「间隔非必克制也」仍作合论(L482 徐注
#   杨增新 甲己间丁 以印化官); 遥隔(年↔时, span=3)=「合而不能合也, 半合也」,
#   「或虽遥隔而仍作合论, 各视其格局配合而已」——亲证成立条件=配偶得禄或刃
#   于月令「通月令之气」(L495 张耀曾 庚禄在申 → 乙庚遥隔仍合), 反证=朱有卿
#   戊墓在戌(禄巳/刃午不在月支)且间乙克戊 → 不合(L486)。
_LU_ZHI = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
           '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}
_REN_ZHI = {'甲': '卯', '丙': '午', '戊': '午', '庚': '酉', '壬': '子'}
_LU_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '火',
          '己': '火', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}


def _wuhe_span_state(facts, a, b):
    """五合终裁三态(PZZQ L476-496). 返回 (state, reason);
    state ∈ adjacent/blocked/remote_he/remote_no/unknown."""
    pl = facts.get('pillars') or {}
    _pos = {}
    for _i, _p in enumerate(('year', 'month', 'day', 'hour')):
        _g = ((pl.get(_p) or ['', ''])[0])
        if _g:
            _pos[_g] = _i
    if a not in _pos or b not in _pos:
        return ('unknown', '位置缺失不猜')
    _span = abs(_pos[a] - _pos[b])
    if _span == 0:
        return ('unknown', '同干非合对')
    if _span == 1:
        return ('adjacent', '紧贴作合')
    if _span == 2:
        _mids = [g for g, i in _pos.items()
                 if min(_pos[a], _pos[b]) < i < max(_pos[a], _pos[b])]
        for _m in _mids:
            if KE.get(GAN_WX.get(_m, '')) == GAN_WX.get(a, '') or \
               KE.get(GAN_WX.get(_m, '')) == GAN_WX.get(b, ''):
                return ('blocked', '制于势然也, 合而不敢合(L481)')
        return ('adjacent', '间隔非必克制, 仍作合论(L482)')
    # span==3 遥隔(年↔时)
    _mb = ((pl.get('month') or ['', ''])[1])
    if _mb and (_REN_ZHI.get(a) == _mb or _REN_ZHI.get(b) == _mb or
                _LU_ZHI.get(a) == _mb or _LU_ZHI.get(b) == _mb):
        return ('remote_he', '通月令之气, 虽遥隔而仍合(L495)')
    return ('remote_no', '遥隔合而不能合, 各视其格局配合(L488-491)')


_ZHI_WX = {'正财': '财', '偏财': '财', '财': '财',
           '正官': '官杀', '七杀': '官杀', '官杀': '官杀', '官': '官杀',
           '正印': '印', '偏印': '印', '印': '印', '枭': '印',
           '食神': '食伤', '伤官': '食伤', '食伤': '食伤',
           '比肩': '比劫', '劫财': '比劫', '比劫': '比劫'}
# PZZQ L3208 十神相对格喜忌查表(接 daymaster_power_queries._geju_xiji_map 同表):
#   月令十神 → (喜神十神, 忌神十神). 喜=生助用神/制忌者, 忌=克破用神/助病者.
# ★ V7.51 喜忌查表重建: 按 PZZQ 各格「取运」章原典口径.
#   原典结构: 「以某格所成之局, 分而配之」—— 先分【格局形态】(用神结构), 再分【身轻身重】.
#   不可用"十神×旺衰"二元表代替(那是自造, 非原典). 各形态出处见下表行号.
#   表值: (喜十神名列表, 忌十神名列表) —— 十神名相对日主, 转为五行后即"运之喜忌".
#   形态判别由 _geju_shape() 依 ge_cheng 格名 + 天干十神配置派生(表驱动).
_GEJU_XIJI_SHAPE = {
    # ── 正官格 (PZZQ L3212-3260) ──
    '正官格': {
        '用财印': {  # L3212-3217 正官兼用财印: 身稍轻取助身, 官稍轻取助官
            'weak':  (['印', '比劫'], ['官杀']),      # 身稍轻->取助身(印比); 忌混杂煞
            'strong': (['财', '印'], ['伤官']),        # 官稍轻->取助官(财印)
        },
        '用财': {    # L3231-3232 正官用财: 身弱喜印绶身旺, 切忌食伤
            'weak':  (['印', '比劫'], ['食伤']),        # 身弱: 喜印绶身旺, 忌食伤
            'strong': (['财', '官杀'], ['食伤']),      # 身旺财轻官弱: 仍行财官运, 忌食伤
        },
        '佩印': {    # L3235-3237 正官佩印: 身旺印重喜财损印, 官重身轻喜比劫印绶
            'weak':  (['比劫', '印'], ['财']),        # 官重身轻: 喜比劫印绶, 财运破印为忌
            'strong': (['财', '食伤'], []),            # 身旺印重: 喜财运损印, 伤食亦吉
        },
        '带伤食': {  # L3244-3247 正官带伤食而用印: 喜官旺印旺, 伤食为害
            'weak':  (['官杀', '印'], ['食伤']),
            'strong': (['官杀', '印'], ['食伤']),
        },
        '带煞': {    # L3254-3260 正官带煞: 伤食不忌(取其制煞), 唯复露七煞不宜
            'weak':  (['财', '食伤', '印'], ['官杀']),
            'strong': (['财', '食伤', '印'], ['官杀']),
        },
    },
    # ── 财格 (PZZQ L3425-3459) ──
    '财格': {
        '旺生官': {  # L3425-3428 财旺生官: 财官旺身轻喜身旺印绶, 不利七煞伤官
            'weak':  (['印', '比劫'], ['官杀', '食伤']),
            'strong': (['财', '官杀'], ['官杀', '食伤']),
        },
        '用食生': {  # L3438-3440 财用食生: 财食重身轻喜助身, 财食轻身重行财食
            'weak':  (['比劫', '印'], ['官杀', '印']),
            'strong': (['财', '食伤'], ['官杀', '印']),
        },
        '佩印': {    # L3447-3452 财格佩印: 最喜印旺; 财印相碍则以劫为用
            'weak':  (['印'], ['财']),
            'strong': (['印', '比劫'], ['财']),
        },
        '用食印': {  # L3459 财用食印: 财轻喜财食, 身轻喜比印, 官运有碍
            'weak':  (['比劫', '印'], ['官杀']),
            'strong': (['财', '食伤'], ['官杀']),
        },
        '用财': {    # ★ V7.109 财格「用财」形态(原表缺, 致查表落空按默认档)
            # L3425「财格取运, 即以财格所就之局, 分而配之」/ L3428「财旺生官者, 运喜身旺印绶, 不利七煞伤官」:
            #   身弱财重 -> 喜印比帮身任财(忌官杀混杂/伤官招非); 身旺财轻 -> 喜财运(财为格体, 顺其势).
            'weak':  (['印', '比劫'], ['官杀', '食伤']),
            'strong': (['财', '食伤'], ['官杀']),
        },
    },
    # ── 印格 (PZZQ L3658-3671) ──
    '印格': {
        '用官': {    # L3658-3665 印绶用官: 官露印重, 财运反吉, 伤食之方亦为最利
            'weak':  (['印', '比劫'], ['财']),
            'strong': (['财', '食伤'], []),
        },
        '用官带伤食': {  # L3667-3671 用官而带伤食: 喜官旺印绶, 伤食为害, 逢煞不忌
            'weak':  (['官杀', '印'], ['食伤']),
            'strong': (['官杀', '印'], ['食伤']),
        },
        '用食伤': {  # L1927/L3751 印格以食伤为用(身旺印旺泄秀), 财运反吉
            'weak':  (['印'], ['财']),
            'strong': (['食伤', '财'], []),
        },
        '印绶': {    # ★ V7.109 印格「印绶」形态(原表缺, 致查表落空按默认档)
            # L3658「印格取运, 即以印格所成之局, 分而配之」/ L3658-3665「其印绶用官者...」;
            #   母旺身弱 -> 喜比劫帮身(印为生扶); 身旺印重 -> 喜财损印(L1129「印太多, 则须以损印为用」).
            'weak':  (['印', '比劫'], ['财']),
            'strong': (['财', '食伤'], []),
        },
    },
    # ── 食神格 (PZZQ L3910-3912) ──
    '食神格': {
        '生财': {    # L3910-3912 食神生财: 财食轻身重行财食, 财食重身轻喜帮身, 官煞俱不美
            'weak':  (['比劫', '印'], ['官杀']),
            'strong': (['财', '食伤'], ['官杀']),
        },
    },
    # ── 伤官格 (PZZQ L4374-4397) ──
    '伤官格': {
        '用财': {    # L4374-4376 伤官用财: 财旺身轻利印比, 身强财浅喜财运, 伤官亦宜
            'weak':  (['印', '比劫'], []),
            'strong': (['财', '食伤'], []),
        },
        '佩印': {    # L4395-4397 伤官佩印: 官煞为宜, 印运亦吉, 伤食不碍, 财地则凶
            'weak':  (['官杀', '印', '食伤'], ['财']),
            'strong': (['官杀', '印', '食伤'], ['财']),
        },
    },
    # ── 七煞格 (PZZQ L4148-4153) ──
    '七煞格': {
        '食制': {    # L4148-4153 煞用食制: 身强第一; 煞重食轻喜食伤, 忌官混杂/畏印夺食/忌财生煞
            'weak':  (['印'], ['食伤']),               # 身弱: 非用印以制食化煞不可
            'strong': (['食伤'], ['官杀', '印', '财']), # 身强: 喜食伤制煞, 忌混杂/畏印夺食/忌财生煞
        },
    },
    # ── 建禄月劫 (PZZQ L1142-1143 三形态: 透官逢财印即同官格, 透财逢食伤即同财格, 透煞遇制伏即同煞格)
    '建禄月劫格': {
        '同官格': {'weak': (['印', '比劫'], ['官杀']), 'strong': (['财', '印'], ['伤官'])},
        '同财格': {'weak': (['印', '比劫'], ['官杀']), 'strong': (['财', '食伤'], ['官杀'])},
        '同煞格': {'weak': (['印'], ['食伤']), 'strong': (['食伤'], ['官杀', '印', '财'])},
    },
    # ── 阳刃 (PZZQ L4579-4582 取运章: 阳刃用官则运喜助官, 官星根深则印绶比劫反为美运;
    #   L4580「非用官煞克之, 即用食伤泄之」; L1140「以财印并见为吉, 但须不相碍」)
    '阳刃格': {
        '用官': {'weak': (['印', '比劫'], ['官杀']), 'strong': (['财', '印'], ['伤官'])},
        '用食伤': {'weak': (['印', '比劫'], ['官杀']), 'strong': (['食伤'], ['官杀'])},
        '用财印': {'weak': (['印', '比劫'], ['官杀']), 'strong': (['财', '印'], ['伤官'])},
    },
}
# 兼容别名: 格名带后缀档(印格(印多逢财) 等) 先剥后缀再查
_GEJU_XIJI_WS = _GEJU_XIJI_SHAPE  # 旧名保留(外部引用)
_GEJU_XIJI = {}  # 旧静态表已撤(V7.47), 兼容别名置空


def _geju_base_name(ge):
    """格名归基名: 印格(印多逢财)->印格; 正官格->正官格; 七煞格(逢制)->七煞格."""
    g = (ge or '').strip()
    for sep in ('(', '（', '[', '·'):
        if sep in g:
            g = g.split(sep)[0]
            break
    return g.strip()


def _zhuanwang_name_conflict(facts):
    """两个来源都给出专旺格名时，不将不同格名视为同一确认事实。"""
    gc = facts.get('ge_cheng')
    special = facts.get('special')
    if not isinstance(gc, dict) or not isinstance(special, dict):
        return False
    ge_name = gc.get('ge')
    zw_name = special.get('zhuanwang')
    if not isinstance(ge_name, str) or not isinstance(zw_name, str):
        return False
    known = {'曲直格', '炎上格', '稼穑格', '从革格', '润下格'}
    base = _geju_base_name(ge_name)
    return (special.get('zhuanwang_state') == 'CONFIRMED' and
            base in known and zw_name in known and base != zw_name)


def _zhuanwang_element_conflict(facts):
    """专旺格名与明确日主五行矛盾时，不推断用药。"""
    from engines.common.special_pattern import ZHUANWANG_NAME

    special = facts.get('special')
    gc = facts.get('ge_cheng')
    names = []
    if isinstance(gc, dict) and isinstance(gc.get('ge'), str):
        names.append(_geju_base_name(gc['ge']))
    if isinstance(special, dict) and special.get('zhuanwang_state') == 'CONFIRMED':
        names.append(special.get('zhuanwang'))
    stated = facts.get('daymaster_element')
    stem_element = GAN_WX.get(facts.get('day_stem'))
    return any(value and value != wx for wx, name in ZHUANWANG_NAME.items() if name in names
               for value in (stated, stem_element))


def _usable_ge_cheng(facts):
    """明确未核验的格局只保留作候选，不作为用药或喜忌事实。"""
    gc = facts.get('ge_cheng')
    from engines.common.rescue import break_state_conflicts, is_special_rescue_scope
    if (not isinstance(gc, dict) or gc.get('ge_rule_verification') == 'NOT_EVALUABLE'
            or _zhuanwang_name_conflict(facts) or
            (is_special_rescue_scope(gc) and _zhuanwang_element_conflict(facts))):
        return {}
    ge_name = gc.get('ge')
    if (is_special_rescue_scope(gc) and isinstance(ge_name, str)
            and '候选' in ge_name):
        return {}
    if (('po_ge_evaluation_complete' in gc and gc['po_ge_evaluation_complete'] is not True) or
            ('cheng_bai' in gc and gc['cheng_bai'] not in
             ('CHENG', 'NO_GE', 'PO', 'CHENG_ZHONG_YOU_PO')) or
            break_state_conflicts(gc)):
        return {}
    return gc


def _geju_shape(facts):
    """格局形态读取(单一数据源): 读格局层产出的 ge_cheng.shape.
    ★ V7.52: 形态由 ge_jie_layer.derive_ge_shape 统一派生并落盘, 本层不再自行反推
      (原两处各自判形态, 口径可能漂移). 缺字段时回退调用格局层派生(不重复实现规则)."""
    gc = _usable_ge_cheng(facts)
    if not gc:
        return '', None
    base = gc.get('shape_base') or _geju_base_name(gc.get('ge') or '')
    shape = gc.get('shape')
    if shape:
        return base, shape
    try:
        from engines.common.ge_jie_layer import derive_ge_shape
        return derive_ge_shape(facts)
    except Exception:
        return base, None


def _ws_dirn(facts):
    """旺衰方向: 身弱=weak(帮身), 身旺=strong(泄伤). 读 l3 strength_verdict."""
    verdict = (facts.get('l3_contract') or {}).get('strength_verdict') or {}
    if verdict.get('status') in ('NOT_EVALUABLE', 'NOT_AUTHORIZED'):
        return None
    sv = verdict.get('value') or []
    if not isinstance(sv, (list, tuple, set)):
        return None
    if '帮身' in sv and '泄伤' not in sv:
        return 'weak'
    if '泄伤' in sv and '帮身' not in sv:
        return 'strong'
    return None


def _geju_xiji_ws(facts, tg):
    """V7.51 格局形态×身轻身重 二维喜忌查表(按 PZZQ 取运章). 返回 (喜十神列表, 忌十神列表)."""
    base, shape = _geju_shape(facts)
    row = _GEJU_XIJI_SHAPE.get(base)
    if not row:
        return ([], [])
    if shape is None or shape not in row:
        return ([], [])
    sub = row.get(shape) or {}
    d = _ws_dirn(facts)
    return sub.get(d, ([], []))


# 十神名 → 日主相对五行: 财=KE[日主], 官杀=KE_BACK[日主], 印=SHENG_BACK[日主],
#   食伤=SHENG[日主], 比劫=日主本身, 枭=印(偏印), 印比=印+比劫. 查表依据全在既有五行表.
#   十神名键须覆盖 _GEJU_XIJI 全部喜/忌值(正官/七杀/正印/偏印/正财/偏财/食神/伤官/比肩/劫财),
#   否则该格查表忌/喜失算(如正官格忌=伤官, 漏键则盘9 忌桶空).
_TEN_GOD_WX = {'财': lambda d: KE.get(d, ''), '正财': lambda d: KE.get(d, ''),
               '偏财': lambda d: KE.get(d, ''), '官杀': lambda d: KE_BACK.get(d, ''),
               '官': lambda d: KE_BACK.get(d, ''), '正官': lambda d: KE_BACK.get(d, ''),
               '七杀': lambda d: KE_BACK.get(d, ''), '杀': lambda d: KE_BACK.get(d, ''),
               '印': lambda d: SHENG_BACK.get(d, ''), '正印': lambda d: SHENG_BACK.get(d, ''),
               '偏印': lambda d: SHENG_BACK.get(d, ''), '枭': lambda d: SHENG_BACK.get(d, ''),
               '食神': lambda d: SHENG.get(d, ''), '伤官': lambda d: SHENG.get(d, ''),
               '食伤': lambda d: SHENG.get(d, ''),
               '比劫': lambda d: d, '比肩': lambda d: d, '劫财': lambda d: d,
               '印比': lambda d: [SHENG_BACK.get(d, ''), d]}


def _tg_wx(cat, dmwx):
    """十神类别 → 日主相对五行(可多个). 查表派生, 非 case 特判."""
    f = _TEN_GOD_WX.get(cat)
    if not f:
        return []
    r = f(dmwx)
    return r if isinstance(r, list) else ([r] if r else [])


def _is_enemy_to_dm(wx: str, dm: str) -> bool:
    """药五行是否克/泄/耗日主(弱日主不宜): 克日主=官杀, 日主生=食伤, 日主克=财."""
    return KE_BACK.get(dm) == wx or SHENG.get(dm) == wx or KE.get(dm) == wx


def _safe(wx: str, bw: str) -> bool:
    """药是否帮病: 同病 或 生病."""
    if not wx or wx == bw:
        return False
    if SHENG.get(wx) == bw:      # wx 生 bw
        return False
    return True


def _yuanliu_yongshen(facts: Dict[str, Any]) -> Dict[str, Any]:
    """★ 第2层 yuanliu_yongshen (DTS L245 源流, 不动 primary).
    取满局最旺为源头, 源头所生之归路为喜. 多步流通精化归第4层程级.
    basis=DTS_CITED L245."""
    wpd = (facts.get("wuxing_power") or {}).get("wuxing_power", {}) or {}
    wxs = ["木", "火", "土", "金", "水"]

    def _mass(wx):
        v = wpd.get(wx, {})
        return (int(v.get("ben_n", 0) or 0) + int(v.get("zhong_n", 0) or 0)
                + int(v.get("yu_n", 0) or 0) + int(v.get("stem_n", 0) or 0))

    masses = {w: _mass(w) for w in wxs}
    total = sum(masses.values())
    if total <= 0:
        return {"enabled": False, "source": None, "hui_lu": None,
                "basis": "DTS L245", "note": "无五行量, 源流不出"}
    source = max(wxs, key=lambda w: masses[w])
    hui_lu = SHENG.get(source, "")
    return {"enabled": bool(hui_lu), "source": source, "hui_lu": hui_lu,
            "masses": masses,
            "basis": "DTS L245「取最多最旺为源头, 流去之处是所喜之神」",
            "note": "归路=源头直接所生; 多步流通(如火→土→金)精化归第4层程级"}


def _tiaohou_yongshen(facts: Dict[str, Any], climate: Dict[str, Any]) -> Dict[str, Any]:
    """★ 第3层 tiaohou_yongshen (DTS L295/L300 寒暖燥湿).
    候神取 cli=climate.candidates(QTBJ build_climate_candidates, 已建≥12条, 字段 stem). 不动 primary."""
    cands = (climate or {}).get("climate_candidates", []) or []
    stems = [c.get("stem", "") for c in cands if c.get("stem")]
    wux = [GAN_WX.get(s, "") for s in stems]
    wux = [w for w in wux if w]
    mb = facts.get("month_branch", "")
    mw = facts.get("month_qi_element", "")
    cold = mw in ("金", "水") and mb in ("亥", "子", "丑")
    dry = mw in ("火", "土") and mb in ("巳", "午", "未")
    return {"enabled": bool(stems), "hou_stems": stems, "hou_wuxing": sorted(set(wux)),
            "primary_hou": wux[0] if wux else None,
            "climate_state": ("寒" if cold else ("燥" if dry else "中")),
            "basis": "DTS L295/L300 寒暖燥湿; 候神=QTBJ climate candidates(build_climate_candidates)",
            "note": "候神按 QTBJ 原文次序; 精化/程级归第4层"}


def _yongshen_routing(facts: Dict[str, Any], climate: Dict[str, Any],
                     debate: Dict[str, Any] = None) -> Dict[str, Any]:
    """★ 第4层程级(喜用神路由)·A′ 消解 (User 裁定 2026-10-16):
    准神 DTS 有两处明文程级 —— ①硬情形优先(L295-298「寒之甚/过于燥皆偏枯, 必无好处」)
    ②病药优先(L240「有病方为贵, 无伤不是奇」)。消解序:
      1. 硬情形(从格/寒燥极)命中 → 该路优先, DTS_CITED
      2. 主病 severity>=3 → 病药路优先, 取克泄病之药; 阈值为 ENGINE_DEFINED
      3. 无病 → 各路并行不压序(架构§2.8.2 五域并行), 扶抑 primary 为准
    依据级: 明文→DTS_CITED(不标 PENDING); 推的→ENGINE_DEFINED."""
    sv = (facts.get("l3_contract") or {}).get("strength_verdict") or {}
    dirn = sv.get("value") or []
    if sv.get('status') in ('NOT_EVALUABLE', 'NOT_AUTHORIZED') or not isinstance(dirn, (list, tuple, set)):
        dirn = []
    special = facts.get("special") or {}
    from engines.common.rescue import is_special_rescue_scope
    gc = facts.get('ge_cheng')
    ge_name = gc.get('ge') if isinstance(gc, dict) else None
    special_conflicts = []
    if _zhuanwang_name_conflict(facts):
        special_conflicts.append('ZHUANWANG_NAME_CONFLICT')
    if _zhuanwang_element_conflict(facts):
        special_conflicts.append('ZHUANWANG_ELEMENT_CONFLICT')
    if is_special_rescue_scope(gc):
        if gc.get('ge_rule_verification') == 'NOT_EVALUABLE':
            special_conflicts.append('SPECIAL_GE_UNVERIFIED')
        if isinstance(ge_name, str) and '候选' in ge_name:
            special_conflicts.append('SPECIAL_GE_CANDIDATE')
    special_conflict = bool(special_conflicts)
    cong = (special.get("cong_type") if special.get("cong_state") == "CONFIRMED"
            and not special_conflict else None)
    yl = _yuanliu_yongshen(facts)
    th = _tiaohou_yongshen(facts, climate)
    # P1 病药 severity(病五行->0-4序数), 供病药优先判定
    p1 = facts.get("p1_bing") or {}
    bings = p1.get("bing_list") or []
    if isinstance(debate, dict) and 'primary_bing' in debate:
        primary = debate.get('primary_bing')
        bings = [primary] if isinstance(primary, dict) and primary else []
    # 克/泄 病五行之神(药): 克病(泄病气)优先, 再泄病
    _sheng_wx = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

    # ★ V7.46 喜忌闲三桶(DTS L404「自喜忌之外皆闲神」+ PZZQ L3208 十神相对格):
    #   十神喜忌查表(接 daymaster_power_queries._geju_xiji_map, PZZQ 八格喜忌十神对照),
    #   十神名 → 日主五行相对: 财=日主所克, 官杀=克日主者, 印=生日主者, 食伤=日主所生, 比劫=日主。
    _dmwx_r = facts.get("daymaster_element", "") or ""
    _tg = facts.get("month_qi_ten_god", "") or ""
    # V7.47: 格局×旺衰二维查表 (撤静态八格写死)
    _x_tg, _j_tg = _geju_xiji_ws(facts, _tg)
    _x_cat_wx = []
    for _c in _x_tg:
        for _w in _tg_wx(_c, _dmwx_r):
            if _w and _w not in _x_cat_wx:
                _x_cat_wx.append(_w)
    _j_cat_wx = []
    for _c in _j_tg:
        for _w in _tg_wx(_c, _dmwx_r):
            if _w and _w not in _j_cat_wx:
                _j_cat_wx.append(_w)

    routes = []
    # ── 1. 硬情形层 (DTS L420 从格 / L298 寒燥极) → 优先 DTS_CITED ──
    hard_winner = None
    if cong:
        hard_winner = {"route": "从格", "shen": None,
                       "basis": "DTS L420「既从矣当论所从之神, 从财只以财为主」",
                       "note": "喜用=所从之神(由L4格判)"}
        routes.append(hard_winner)
    # ★ V7.174 专旺硬情形(PZZQ 用神五法 L960「(四)专旺。四柱之气势, 偏于一方其势不可逆,
    #   惟有顺其气势为用」+ L4882 徐注「只可顺其气势, 引其性情以取用, 若强制之, 反激而成患」
    #   + DTS L170-172「独象喜行化地」【原注】「所生者为化神, 化神宜旺」):
    #   special 层已判 zhuanwang(曲直/炎上/稼穑/从革/润下) 且 日主旺极(当令+根气厚)
    #   -> 顺气势取【日主所生=化神】为用, 压过调候(逆势候神=「强制之反激而成患」).
    #   真值: DT盘 癸酉甲子癸亥辛酉(润下水旺极) 原断「大取金水运, 不取火土」——
    #   旧链调候取丙火(逆势)与原断相反; 专旺通道顺化神(木)与顺势金水不悖(金生水亦顺).
    _sp_zw = (facts.get("special") or {})
    _zw_name = _sp_zw.get("zhuanwang") or ""
    _dm_wx_zw = facts.get("daymaster_element", "") or ""
    _dm_row_zw = (_wp_el_pre := ((facts.get("wuxing_power") or {}).get("wuxing_power") or {})).get(_dm_wx_zw) or {}
    _dm_ling_zw = _dm_row_zw.get("ling_state") == "旺"
    _dm_mass_zw = sum(int(_dm_row_zw.get(k, 0) or 0) for k in ("ben_n", "zhong_n", "yu_n", "stem_n"))
    if (_zw_name and _sp_zw.get("zhuanwang_state") == "CONFIRMED" and not special_conflict
            and _dm_ling_zw and _dm_mass_zw >= 3 and not hard_winner):
        _hua_zw = SHENG.get(_dm_wx_zw, "")   # 化神=日主所生(DTS L172)
        hard_winner = {"route": "专旺", "shen": _hua_zw,
                       "basis": "PZZQ L960「(四)专旺。四柱之气势偏于一方其势不可逆, 惟有顺其气势为用」+ L4882 徐注「若强制之, 反激而成患」+ DTS L170-172「独象喜行化地」",
                       "note": "专旺势成, 顺气势取化神(%s所生=%s); 逆势候神/克泄皆忌" % (_dm_wx_zw, _hua_zw)}
        routes.append(hard_winner)
    # 寒燥极偏枯: 调候方向命中 且 局偏枯 → DTS L298 明文硬情形
    #   偏枯判据(DTS L298「过于燥/湿皆偏枯」): 候神 mass 小于局最旺五行 → 候神被压需调候;
    #   候神=局最旺(不偏枯)则不判调候(如 DT-0437 局火旺, 归格局/扶抑), 防调候抢格局
    _hou_wx = th.get("primary_hou") or ""
    _wp_el = (facts.get("wuxing_power") or {}).get("wuxing_power") or {}
    def _wx_mass(_wx):
        _h = _wp_el.get(_wx) or {}
        return sum(int(_h.get(k, 0) or 0) for k in ("ben_n", "zhong_n", "yu_n", "stem_n"))
    _hou_mass = _wx_mass(_hou_wx) if _hou_wx else -1
    _max_mass = max((_wx_mass(_w) for _w in ("金", "木", "水", "火", "土")), default=0)
    # V7.42 调候路线判定扩展(原典 QTBJ 十干逐月调候 + DTS L295/L300 寒暖燥湿):
    #   候神(调候用神)=原局喜神第一顺位。候神被局压制(候神 mass 小于局最旺五行)
    #   且日主当令者(候神=日主五行, 调候即顺局), 候神虽被局最旺者压仍为喜(身旺顺调候)。
    #   例: 盘1 壬亥(水38局最旺, 候神=水=日主当令), 调候路 winner=水(顺局调候, 不取木泄)。
    _dmwx_routing = facts.get("daymaster_element", "") or ""
    _hou_is_dm = (_hou_wx == _dmwx_routing)
    # V7.43 调候喜用神判据重构(原典 DTS L295/L300 + QTBJ 调候, 彻底修, 非补丁):
    #   调候用神=原局喜神第一顺位。候神被局压(候神 mass<局最旺 mass, 偏枯)或
    #   候神=日主当令(顺局调候, 候神即喜)时, 候神置调候路 winner。
    _th_bias = ("调候" in dirn) and th.get("enabled") and (_hou_wx != "") and (
        _hou_mass < _max_mass or _hou_is_dm)
    if _th_bias and not hard_winner:
        hard_winner = {"route": "调候", "shen": th.get("primary_hou"),
                       "basis": "DTS L298「过于湿者过于燥者皆偏枯」/L295「寒之甚暖之至必无好处」",
                       "note": "寒燥极, 调候候神优先(先解冻/润燥, 再谈他)"}
        routes.append(hard_winner)
    # ── 2. 病药层 (DTS L240「有病方为贵」) → 哪路判病哪路优先 ──
    _bing_heavy = [b for b in bings if int(b.get("severity") or 0) >= 3 and b.get("bing_wx")]
    bing_winner = None
    if _bing_heavy and not hard_winner:
        _main = max(_bing_heavy, key=lambda x: int(x.get("severity") or 0))
        _bx = _main.get("bing_wx")
        _yao = KE_BACK.get(_bx, "") or _sheng_wx.get(_bx, "")
        bing_winner = {"route": "病药", "shen": _yao,
                       "bing": _bx, "bing_sev": int(_main.get("severity") or 0),
                       "status": "ENGINE_DEFINED",
                       "basis": "DTS L240「有病方为贵, 无伤不是奇」; 克泄病之为药",
                       "note": "病=%s(sev%s), 药=%s; severity>=3 为工程门槛" % (_bx, _main.get("severity"), _yao)}
        routes.append(bing_winner)
    # ── 3. 普通层: 各路并列候选(不压序) ──
    if yl.get("enabled"):
        routes.append({"route": "源流", "shen": yl.get("hui_lu"), "status": "ENGINE_DEFINED",
                       "basis": "DTS L245 源流(并列取用)", "note": "源流归路"})
    if "通关" in dirn:
        routes.append({"route": "通关", "shen": None, "status": "ENGINE_DEFINED",
                       "basis": "DTS L250 两神相战需通", "note": "通关神"})
    _strength_direction = _ws_dirn(facts)
    if _strength_direction:
        _d = '帮身' if _strength_direction == 'weak' else '泄伤'
        routes.append({"route": _d, "shen": None, "status": "ENGINE_DEFINED",
                       "basis": "DTS L215 体用 + L230/L235", "note": "扶抑路, primary 已算"})
    # 明确标记工程阈值；未单独标注的路线沿用既有依据级。
    for r in routes:
        r.setdefault("status", "DTS_CITED" if r.get("route") in ("从格", "病药") and (r is hard_winner or r is bing_winner) else "ENGINE_DEFINED")
    # ── 消解: 赢的那路 + 喜用神 ──
    winner = hard_winner or bing_winner
    winner_route = (winner or {}).get("route", "")
    winner_shen = (winner or {}).get("shen")
    if winner_shen:
        _basis = (winner or {}).get("basis", "")
    else:
        # 无硬情形/无病 → 扶抑 primary 为准(第1层已算), 源流/调候并列不压
        _basis = "无硬情形无病, 各路并行(§2.8.2); 扶抑 primary 为准, 调候/源流并列"
    return {
        "routes": routes,
        "special_conflicts": special_conflicts,
        "winner_route": winner_route,
        "winner_shen": winner_shen,
        "winner_basis": _basis,
        "route_count": len(routes),
        "pending_count": 0,
        # ★ V7.46 喜忌闲三桶(DTS L404 + PZZQ L3208 十神相对格, 查表派生, 非单五行生克)
        "xiji_xian": {"xi_wx": _x_cat_wx, "ji_wx": _j_cat_wx,
                      "basis": "PZZQ L3208 十神喜忌查表(_geju_xiji_map) + DTS L404「自喜忌之外皆闲神」; 闲=局中余集(中性)"},
        "basis": "第4层程级·A′: 硬情形(L420/L298)→病药(L240)→并行; 病药阈值为工程定义"}


def resolve_yongyao(facts: Dict[str, Any], debate: Dict[str, Any],
                    climate: Dict[str, Any] = None) -> Dict[str, Any]:
    ge = facts.get('ge_cheng')
    if (isinstance(ge, dict) and ge.get('ge_rule_verification') == 'NOT_EVALUABLE'
            and ge.get('unresolved_pattern')):
        return {'layer': 'YONGYAO_RESOLVE', 'state': 'PATTERN_CONFLICT_NOT_EVALUABLE',
                'primary_medicine': None, 'auxiliary_medicine': [], 'ji_shen': [],
                'all_edges': [], 'rejected_climate': [],
                'xiji_xian': {'xi_wx': [], 'ji_wx': [], 'xian_wx': [], 'conflict_wx': []},
                'unresolved_pattern': ge['unresolved_pattern'],
                'boundary_note': '特殊格候选与普通格关系未裁定，不能据普通格确定主药或喜忌。'}
    if debate.get('selection_verification') == 'NOT_EVALUABLE':
        return {'layer': 'YONGYAO_RESOLVE', 'state': 'PRIMARY_BING_NOT_EVALUABLE',
                'primary_medicine': None, 'auxiliary_medicine': [], 'ji_shen': [],
                'all_edges': [], 'rejected_climate': [],
                'xiji_xian': {'xi_wx': [], 'ji_wx': [], 'xian_wx': [], 'conflict_wx': []},
                'boundary_note': '主病排序输入不完整，不能据兼容排序确定用药。'}
    primary = debate.get('primary_bing') or {}
    _yl = _yuanliu_yongshen(facts)   # ★ 第2层 源流(不动 primary)
    _th = _tiaohou_yongshen(facts, climate)   # ★ 第3层 调候(不动 primary)
    _rt = _yongshen_routing(facts, climate, debate)   # 使用辩论、转归后的主病。
    bw = primary.get('bing_wx', '')
    bid = primary.get('bing_id', '')
    _sec_wx = {s2.get('bing_wx') for s2 in (debate.get('secondary_bing') or []) if s2.get('bing_wx')}
    _unresolved_bing_wx = {s2.get('bing_wx') for s2 in (debate.get('unresolved_bing') or [])
                           if s2.get('bing_wx')}
    dm = GAN_WX.get(facts.get('day_stem', ''), '')
    _pl = facts.get('pillars')
    dm_ben = sum(1 for pos in ('year', 'month', 'day', 'hour')
                 if _pl and ZHI_BEN_WX.get(_pl[pos][1]) == dm) if _pl else 0

    rejected_climate = []
    deferred_climate_rejections = []
    # V7.49 候神不拒: 候干表=日干×月令原典用神(QTBJ, 如六月庚金「专用丁火」).
    #   候神已升 primary 时, 该候干不得再被判"病之源"剔除(自相矛盾: 药不可既是主用神又为病源).
    _hou_wx_pre = ''
    if climate:
        from engines.common import tiaohou_rank as _thr
        _rk_pre = _thr._tiaohou_primary_rank(climate, bw, dm, _pl)
        if _rk_pre.get('rank') == 'PROMOTE':
            _hou_wx_pre = _rk_pre.get('wx') or ''
    if climate:
        for c in climate.get('climate_candidates', []):
            stem = c.get('stem', '')
            cwx = GAN_WX.get(stem, '')
            reason = None
            if cwx == bw:
                reason = '与主病同五行(%s), 用之添病' % bw
            elif SHENG_BACK.get(bw) == cwx:
                reason = '%s生%s(病), 为病之源' % (cwx, bw)
            if reason and cwx == _hou_wx_pre:
                # 预排名不等于已经升为主药，待后续实际路由确定。
                deferred_climate_rejections.append({'stem': stem, 'wuxing': cwx, 'reason': reason})
                continue
            if reason:
                rejected_climate.append({'stem': stem, 'wuxing': cwx, 'reason': reason})

    if not bw:
        # ★ V7.168 调候硬情形优先(修 38/2106 盘「路由判调候赢而 primary 空」断层):
        #   _yongshen_routing L362 已依 DTS L298/L295 判「寒燥极偏枯」为硬情形, winner_route=调候,
        #   但本无病分支原先不消费该 winner, 直接掉进格体喜神→查表→源5, 而 source5 只认
        #   帮身/泄伤方向 —— 调候硬情形盘 primary_medicine 空手而归(顶层 yongyao.primary='')。
        #   A 级依据: DTS L298「过于湿者过于燥者皆偏枯」+ QTBJ 十干逐月候干表(调候=第一顺位用神);
        #   架构§2.8.2 无病各路并行时, 硬情形 winner 应落实为用药方向。
        #   修法: 无病分支最前查 _rt.winner_route=='调候' 且 winner_shen 非空
        #     -> 候神升 primary_medicine(kind=调候), 喜忌闲三桶照 _rt 派生(不另造)。
        _rt_wr = (_rt.get('winner_route') or '')
        _rt_ws = (_rt.get('winner_shen') or '')
        if _rt_wr == '调候' and _rt_ws:
            _xjj_th = _rt.get('xiji_xian') or {}
            _xi_bkt_th = [w for w in (_xjj_th.get('xi_wx') or []) if w]
            if _rt_ws not in _xi_bkt_th:
                _xi_bkt_th.append(_rt_ws)
            _ji_bkt_th = [w for w in (_xjj_th.get('ji_wx') or []) if w]
            if _rt_ws in _ji_bkt_th:
                _ji_bkt_th = [x for x in _ji_bkt_th if x != _rt_ws]  # 药不入忌(用神不自相矛盾)
            _conflict_th = [w for w in _ji_bkt_th if w in _xi_bkt_th]
            _xi_bkt_th = [w for w in _xi_bkt_th if w not in _conflict_th]
            _ji_bkt_th = [w for w in _ji_bkt_th if w not in _conflict_th]
            _xian_bkt_th = []
            _wp_el_th = (facts.get('wuxing_power') or {}).get('wuxing_power') or {}
            _present_th = [w for w in ('木', '火', '土', '金', '水')
                           if (_wp_el_th.get(w) or {}).get('stem_n', 0)
                           or (_wp_el_th.get(w) or {}).get('ben_n', 0)
                           or (_wp_el_th.get(w) or {}).get('zhong_n', 0)
                           or (_wp_el_th.get(w) or {}).get('yu_n', 0)]
            for w in _present_th:
                if w in _xi_bkt_th or w in _ji_bkt_th or w in _xian_bkt_th or w in _conflict_th or w == _rt_ws:
                    continue
                _xian_bkt_th.append(w)
            return {'layer': 'YONGYAO_RESOLVE', 'state': 'TIAOHOU_HARD_WINNER',
                    'primary_medicine': {'wuxing': _rt_ws, 'gan': list(WX_GAN.get(_rt_ws, ())),
                                          'function': '调候硬情形用药(寒燥极偏枯, 候神为第一顺位)',
                                          'kind': '调候',
                                          'classic': 'DTS L298「过于湿者过于燥者皆偏枯」/L295「寒之甚暖之至必无好处」+ QTBJ 候干表',
                                          'blocked': None},
                    'auxiliary_medicine': [],
                    'ji_shen': _ji_bkt_th,
                    'xiji_xian': {'xi_wx': _xi_bkt_th, 'ji_wx': _ji_bkt_th, 'xian_wx': _xian_bkt_th, 'conflict_wx': _conflict_th,
                                  'basis': 'PZZQ L3208/L2319 格局×旺衰喜忌查表(_GEJU_XIJI_WS)+破格忌; DTS L404「自喜忌之外皆闲神」闲=局中余集(中性)'},
                    'rejected_climate': rejected_climate,
                    'yuanliu_yongshen': _yl,   # ★ 第2层 源流(不动 primary)
                    'tiaohou_yongshen': _th,   # ★ 第3层 调候(不动 primary)
                    'routing': _rt,   # ★ 第4层 程级路由
                    'boundary_note': 'V7.168: 无病盘路由层已判调候硬情形赢(DTS L298/L295), 候神升 primary; 喜忌闲三桶照 _rt 派生; 源2/3/4/5 不再走(调候硬情形优先于格体喜神)'}
        # ★ V7.174 专旺硬情形消费(路由层 winner_route=='专旺', 化神须落 primary):
        #   无病分支同调候一样消费专旺 winner —— 顺气势化神升 primary(kind=专旺),
        #   忌桶=克泄日主与克化神者(逆势=「强制之反激而成患」, PZZQ L4882);
        #   喜桶=化神+日主同类(顺气势); 三桶照 _rt 派生不另造.
        if _rt_wr == '专旺' and _rt_ws:
            _dm_zw = facts.get('daymaster_element', '') or ''
            _xjj_zw = _rt.get('xiji_xian') or {}
            _xi_bkt_zw = [w for w in (_xjj_zw.get('xi_wx') or []) if w]
            if _rt_ws not in _xi_bkt_zw:
                _xi_bkt_zw.append(_rt_ws)
            if _dm_zw and _dm_zw not in _xi_bkt_zw:
                _xi_bkt_zw.append(_dm_zw)   # 日主同类亦顺势(从旺喜比劫禄刃)
            _ji_bkt_zw = [w for w in (_xjj_zw.get('ji_wx') or []) if w]
            _ji_bkt_zw = [w for w in _ji_bkt_zw if w != _rt_ws]
            # 逆势忌: 克日主者(KE_BACK[dm]) + 克化神者(KE_BACK[hua]) 入忌
            for _bad_zw in (KE_BACK.get(_dm_zw, ''), KE_BACK.get(_rt_ws, '')):
                if _bad_zw and _bad_zw not in _ji_bkt_zw and _bad_zw != _rt_ws and _bad_zw != _dm_zw:
                    _ji_bkt_zw.append(_bad_zw)
            _conflict_zw = [w for w in _ji_bkt_zw if w in _xi_bkt_zw]
            _xi_bkt_zw = [w for w in _xi_bkt_zw if w not in _conflict_zw]
            _ji_bkt_zw = [w for w in _ji_bkt_zw if w not in _conflict_zw]
            _xian_bkt_zw = []
            _wp_el_zw = (facts.get('wuxing_power') or {}).get('wuxing_power') or {}
            _present_zw = [w for w in ('木', '火', '土', '金', '水')
                           if (_wp_el_zw.get(w) or {}).get('stem_n', 0)
                           or (_wp_el_zw.get(w) or {}).get('ben_n', 0)
                           or (_wp_el_zw.get(w) or {}).get('zhong_n', 0)
                           or (_wp_el_zw.get(w) or {}).get('yu_n', 0)]
            for w in _present_zw:
                if w in _xi_bkt_zw or w in _ji_bkt_zw or w in _xian_bkt_zw or w in _conflict_zw or w == _rt_ws:
                    continue
                _xian_bkt_zw.append(w)
            return {'layer': 'YONGYAO_RESOLVE', 'state': 'ZHUANWANG_HARD_WINNER',
                    'primary_medicine': {'wuxing': _rt_ws, 'gan': list(WX_GAN.get(_rt_ws, ())),
                                          'function': '专旺顺气势化神(独象喜行化地, 化神要昌)',
                                          'kind': '专旺',
                                          'classic': 'PZZQ L960「(四)专旺。四柱之气势偏于一方其势不可逆, 惟有顺其气势为用」+ L4882「若强制之, 反激而成患」+ DTS L170-172「独象喜行化地」',
                                          'blocked': None},
                    'auxiliary_medicine': [],
                    'ji_shen': _ji_bkt_zw,
                    'xiji_xian': {'xi_wx': _xi_bkt_zw, 'ji_wx': _ji_bkt_zw, 'xian_wx': _xian_bkt_zw, 'conflict_wx': _conflict_zw,
                                  'basis': 'PZZQ L960 专旺顺气势 + L3208/L2319 查表; DTS L404 闲=局中余集'},
                    'rejected_climate': rejected_climate,
                    'yuanliu_yongshen': _yl,
                    'tiaohou_yongshen': _th,
                    'routing': _rt,
                    'boundary_note': 'V7.174: 专旺势成, 路由层顺气势取化神赢(PZZQ L960), 化神升 primary; 忌=克日主/克化神(逆势); 源2/3/4/5 不再走'}
        # [2026-10-08 PATCH-GE2YO] 源1(病药主病)空 → fallback 源2(格体喜神 xi_wx) + 源3(格局所需神)
        #   架构 §2.9: 用神层 = 五域药方 + L4 格体喜神 取用神。
        #   源1 空(病0→无主病)时, 走 ge_cheng.xi_wx(格成喜神) / ge_cheng.zhi_wx(格破救应神)。
        #   [2026-10-08 PATCH-SRC4] 源4: 破格盘 xi_wx 被清空, 改读 jiu_ying.rescue_wx(破格救应药)
        #   + ge_cheng.hua_wx(专旺化神)。不替代源1, 仅在源1 无产出时补, 防"无主病→用神全空"静默丢。
        _gc = _usable_ge_cheng(facts)
        _invalid_ge_elements = [key for key in ('xi_wx', 'zhi_wx', 'hua_wx')
                                if _gc.get(key) is not None and
                                (not isinstance(_gc[key], list) or
                                 any(not isinstance(wx, str) or wx not in ('木', '火', '土', '金', '水')
                                     for wx in _gc[key]))]
        if _invalid_ge_elements:
            return {'layer': 'YONGYAO_RESOLVE', 'state': 'PATTERN_ELEMENTS_NOT_EVALUABLE',
                    'primary_medicine': None, 'auxiliary_medicine': [], 'ji_shen': [],
                    'xiji_xian': {'xi_wx': [], 'ji_wx': [], 'xian_wx': [], 'conflict_wx': []},
                    'invalid_pattern_element_fields': _invalid_ge_elements,
                    'rejected_climate': rejected_climate, 'yuanliu_yongshen': _yl,
                    'tiaohou_yongshen': _th, 'routing': _rt,
                    'boundary_note': '格局五行候选格式无效，不能依据该格局确定用药或喜忌。'}
        _xi = _gc.get('xi_wx') or []
        _zhi = _gc.get('zhi_wx') or []
        _hua = _gc.get('hua_wx') or []
        # 原格局的制化字段描述既有结构；破格后不能直接冒充已核验的救应。
        if _gc.get('cheng_bai') in ('PO', 'CHENG_ZHONG_YOU_PO'):
            _zhi = []
            _hua = []
        _jy = facts.get('jiu_ying') or {}
        # 若提供了格局上下文，救应主药必须与同一格局的救应适用范围一致。
        from engines.common.rescue import assess_rescue_scope
        _scope_ok = ('ge_cheng' not in facts or
                     assess_rescue_scope(facts['ge_cheng'])['triggered'] is True)
        if 'jiu_ying_scope' in facts:
            _scope = facts['jiu_ying_scope']
            _scope_ok = (_scope_ok and isinstance(_scope, dict) and
                         _scope.get('triggered') is True and
                         _scope.get('success') not in ('NA', 'NA_NOT_IN_SCOPE'))
        # 只消费明确计算成功的救应；候选、失败、缺失状态不能变成用药。
        _rescue = (_jy.get('rescue_wx') or []) if (
            isinstance(_jy, dict) and facts.get('jiu_ying_status') == 'EVALUATED'
            and facts.get('jiu_ying_source_verification') != 'LEGACY_UNVERIFIED'
            and _scope_ok
            and _jy.get('success') == 'SUCCESS'
        ) else []
        if not isinstance(_rescue, list) or any(
                not isinstance(wx, str) or wx not in ('木', '火', '土', '金', '水')
                for wx in _rescue):
            _rescue = []
        _rescue = list(dict.fromkeys(_rescue))
        if not _zhi and not _xi and len(_rescue) > 1:
            return {'layer': 'YONGYAO_RESOLVE', 'state': 'RESCUE_CONFLICT',
                    'primary_medicine': None, 'auxiliary_medicine': [], 'ji_shen': [],
                    'rescue_candidates': _rescue,
                    'xiji_xian': {'xi_wx': [], 'ji_wx': [], 'xian_wx': [],
                                  'basis': '救应候选存在多种五行，尚无授权排序'},
                    'rejected_climate': rejected_climate,
                    'yuanliu_yongshen': _yl, 'tiaohou_yongshen': _th, 'routing': _rt,
                    'boundary_note': '保留多个救应候选；不依据列表顺序选取主药。'}
        _source = None
        _w = ''
        if _zhi:
            _w = _zhi[0]
            _source = '源3:格破救应神(zhi_wx)'
        elif _xi:
            _w = _xi[0]
            _source = '源2:格体喜神(xi_wx)'
        elif _rescue:
            _w = _rescue[0]
            _source = '源4:破格救应药(jiu_ying.rescue_wx, PZZQ L1226)'
        elif _hua:
            _w = _hua[0]
            _source = '源4:专旺化神(ge_cheng.hua_wx, PZZQ L170 独象喜行化地)'
        # 上游格局候选常由 sorted(set(...)) 构造，首项顺序不代表主药排序。
        _selection_candidates = (_zhi if _zhi else _xi if _xi else
                                 _rescue if _rescue else _hua)
        _selection_candidates = list(dict.fromkeys(_selection_candidates))
        _selection_status = ('NOT_EVALUABLE' if len(_selection_candidates) > 1
                             else 'SINGLE_CANDIDATE')
        # ★ V7.180 格体喜神多候选时, 按原典格之用神立主药(喜神仍入 xi_wx 作辅),
        #   不把「喜神无序」误判成「用神无解」。
        _ge_yong_wx = derive_ge_yong_wx(facts)
        if _selection_status == 'NOT_EVALUABLE' and _ge_yong_wx:
            _selection_status = 'SINGLE_CANDIDATE'
        # ★ V7.46 忌桶撤 V7.45 机械派生(KE[用神]+日主), 改十神查表+破格忌(DTS L404/PZZQ L3208)
        #   按 month_qi_ten_god + _GEJU_XIJI 查表派生喜忌(独立于 _w 是否非空):
        #   喜桶 = 查表喜十神→五行 + 格喜(xi_wx) + 用神(_w); 忌桶 = 查表忌十神→五行 + 破格忌(po_ge)
        _dmwx_fb = facts.get('daymaster_element') or dm
        _tg_fb = facts.get('month_qi_ten_god', '') or ''
        _x_tg_fb, _j_tg_fb = _geju_xiji_ws(facts, _tg_fb)
        _ji_bkt_fb = []
        for _c_fb in _j_tg_fb:
            for _gw_fb in _tg_wx(_c_fb, _dmwx_fb):
                if _gw_fb and _gw_fb not in _ji_bkt_fb:
                    _ji_bkt_fb.append(_gw_fb)
        for _p_fb in (_gc.get('po_ge') or []):
            if (_p_fb.get('type') == '阳刃无官煞透' or
                    _p_fb.get('condition_id') == 'WEALTH_AND_SHA' or
                    (_p_fb.get('match') == 'ALL' and len(_p_fb.get('required') or []) > 1)):
                continue  # 缺失条件及财煞合取条件不能逐项推为忌神。
            for _g_fb in (_p_fb.get('required') or []):
                for _gw_fb in _tg_wx(_g_fb, _dmwx_fb):
                    if _gw_fb and _gw_fb not in _ji_bkt_fb:
                        _ji_bkt_fb.append(_gw_fb)
        _xi_bkt_fb = []
        for _c_fb in _x_tg_fb:
            for _gw_fb in _tg_wx(_c_fb, _dmwx_fb):
                if _gw_fb and _gw_fb not in _xi_bkt_fb:
                    _xi_bkt_fb.append(_gw_fb)
        for _wgb in (_gc.get('xi_wx') or []):
            if _wgb and _wgb not in _xi_bkt_fb:
                _xi_bkt_fb.append(_wgb)
        if _w and _selection_status == 'SINGLE_CANDIDATE' and _w not in _xi_bkt_fb:
            _xi_bkt_fb.append(_w)
        # 仅已确定的单一药可按药优先解冲突；多候选首项无排序依据。
        _yao_wx_fb = {_w} if _w and _selection_status == 'SINGLE_CANDIDATE' else set()
        _conflict_fb = [w for w in _ji_bkt_fb if w in _xi_bkt_fb]
        _unresolved_fb = []
        for _conflict_w in list(_conflict_fb):
            if bw and _conflict_w == bw:
                _xi_bkt_fb = [x for x in _xi_bkt_fb if x != _conflict_w]
            elif _conflict_w in _yao_wx_fb:
                _ji_bkt_fb = [x for x in _ji_bkt_fb if x != _conflict_w]
            else:
                _unresolved_fb.append(_conflict_w)
                _xi_bkt_fb = [x for x in _xi_bkt_fb if x != _conflict_w]
                _ji_bkt_fb = [x for x in _ji_bkt_fb if x != _conflict_w]
        _xian_bkt_fb = []
        _wp_el_fb = (facts.get('wuxing_power') or {}).get('wuxing_power') or {}
        _present_fb = [w for w in ("木", "火", "土", "金", "水") if (_wp_el_fb.get(w) or {}).get('stem_n', 0) or (_wp_el_fb.get(w) or {}).get('ben_n', 0) or (_wp_el_fb.get(w) or {}).get('zhong_n', 0) or (_wp_el_fb.get(w) or {}).get('yu_n', 0)]
        for w in _present_fb:
            if w in _xi_bkt_fb or w in _ji_bkt_fb or w in _xian_bkt_fb or w in _unresolved_fb or w in _selection_candidates:
                continue
            _xian_bkt_fb.append(w)
        if _w:
            return {'layer': 'YONGYAO_RESOLVE', 'state': 'GE_FALLBACK',
                    'primary_medicine': None if _selection_status == 'NOT_EVALUABLE' else {
                        'wuxing': _ge_yong_wx or _w,
                        'gan': list(WX_GAN.get(_ge_yong_wx or _w, ())),
                        'function': ('源2:格局用神(格体喜神仅为喜)' if _ge_yong_wx else _source),
                        'kind': '格局用神(喜神为辅)' if _ge_yong_wx else '格体喜神/救应神',
                        'classic': ('PZZQ 建禄月劫「透官而逢财印即同官格」/阳刃「以官煞制刃」: '
                                    '格之用神主药, 财印食伤等喜神为运喜' if _ge_yong_wx else
                                    '架构§2.9 用神层=L4格体喜神+P1格局病域救应'),
                        'blocked': None},
                    'auxiliary_medicine': [],
                    'ji_shen': _ji_bkt_fb,
                    'xiji_xian': {'xi_wx': _xi_bkt_fb, 'ji_wx': _ji_bkt_fb, 'xian_wx': _xian_bkt_fb, 'conflict_wx': _unresolved_fb,
                                  'basis': 'PZZQ L3208/L2319 格局×旺衰喜忌查表(_GEJU_XIJI_WS)+破格忌; DTS L404「自喜忌之外皆闲神」闲=局中余集(中性)'},
                    'rejected_climate': rejected_climate,
                    'ge_fallback_source': _source,
                    'primary_selection_status': _selection_status,
                    'primary_selection_candidates': _selection_candidates,
                    'ge_yong_wx': _ge_yong_wx,
                    'yuanliu_yongshen': _yl,   # ★ 第2层 源流(不动 primary)
                    'tiaohou_yongshen': _th,   # ★ 第3层 调候(不动 primary)
                    'routing': _rt,   # ★ 第4层 程级路由
                    'boundary_note': '源1无主病, 走格体喜神/救应神 fallback(架构§2.9 五源); 喜忌闲=DTS L404 + PZZQ L3208 十神查表(撤 V7.45 机械 KE[用神]+日主)'}
        # ★ 无格 fallback: 有查表喜忌但无用神(无格体喜神/救应神) → 仍出喜忌闲三桶
        if _xi_bkt_fb or _ji_bkt_fb or _unresolved_fb:
            return {'layer': 'YONGYAO_RESOLVE', 'state': 'NO_BING_GE_XIJI',
                    'primary_medicine': _ge_medicine(facts), 'auxiliary_medicine': [],
                    'ji_shen': _ji_bkt_fb,
                    'xiji_xian': {'xi_wx': _xi_bkt_fb, 'ji_wx': _ji_bkt_fb, 'xian_wx': _xian_bkt_fb, 'conflict_wx': _unresolved_fb,
                                  'basis': 'PZZQ L3208/L2319 格局×旺衰喜忌查表(_GEJU_XIJI_WS)+破格忌; DTS L404「自喜忌之外皆闲神」闲=局中余集(中性)'},
                    'rejected_climate': rejected_climate,
                    'yuanliu_yongshen': _yl,   # ★ 第2层 源流(不动 primary)
                    'tiaohou_yongshen': _th,   # ★ 第3层 调候(不动 primary)
                    'routing': _rt,   # ★ 第4层 程级路由
                    'boundary_note': '源1无主病+无格体喜神/救应神, 但十神查表有喜忌(PZZQ L3208), 仍出喜忌闲三桶; 不裁决用神'}
        # ★ 源5: 无病无格 → 按 L3 方向出旺衰喜用神(DTS L215 体用正法 + L235 衰帮旺泄)
        #   V7.43 补源5取神规则(彻底修, 非 case 特判): 原典 DTS L215 体用正法——
        #   「日主弱, 则提纲有物, 帮身以制其神者, 亦皆为我用;
        #    提纲食伤财官太旺, 则取年月时上印比为喜神;
        #    提纲印比太旺, 则取年月时上食伤财官为喜神而用之」
        #   帮身(身弱) → 喜印(生我 SHENG_BACK)主, 比(我 dm)辅 —— 双喜
        #   泄伤(身旺) → 喜食伤(我生 SHENG)主, 官(克我 KE_BACK)辅 —— 双喜
        #   取神依据=L3 旺衰方向(dmn5) + 日主五行(dmwx5) 查表派生, 非 case 特判。
        _dmwx5 = facts.get('daymaster_element') or dm
        if _ws_dirn(facts) == 'weak':
            # 身弱 → 喜印(生我)主, 比(我)辅
            _w5 = SHENG_BACK.get(_dmwx5, '') or _dmwx5
            _aux5 = [_dmwx5] if _dmwx5 != _w5 else []
            _src5 = '源5:旺衰喜用神(身弱喜印帮身, DTS L215 体用)'
        elif _ws_dirn(facts) == 'strong':
            # 身旺 → 喜食伤(我生)主, 官(克我)辅
            _w5 = SHENG.get(_dmwx5, '') or _dmwx5
            _aux5 = [KE_BACK.get(_dmwx5, '')] if KE_BACK.get(_dmwx5, '') else []
            _src5 = '源5:旺衰喜用神(身旺喜食伤克泄, DTS L215 体用)'
        else:
            _w5 = ''; _aux5 = []; _src5 = ''
        _gy5 = derive_ge_yong_wx(facts)
        if _gy5:
            # 源2 格之用神优先于源5 旺衰喜用神(PZZQ 论用神/论八格 原典判据)
            _w5 = _gy5
            _aux5 = []
            _src5 = '源2:格局用神(无病时取格用神, 优于源5旺衰喜用神)'
        if _w5:
            # ★ V7.46 忌桶撤 V7.45 机械派生(KE[用神]+日主), 改十神查表忌(DTS L404/PZZQ L3208)
            _xjj5 = _rt.get("xiji_xian") or {}
            _xi_bkt5 = [w for w in (_xjj5.get("xi_wx") or []) if w]
            if _w5 and _w5 not in _xi_bkt5:
                _xi_bkt5.append(_w5)
            _ji_bkt5 = [w for w in (_xjj5.get("ji_wx") or []) if w]
            # 互斥(DTS L404): 喜∩忌 冲突五行归闲桶(既非明确喜亦非明确忌)
            _conflict5 = [w for w in _ji_bkt5 if w in _xi_bkt5]
            _xi_bkt5 = [w for w in _xi_bkt5 if w not in _conflict5]
            _ji_bkt5 = [w for w in _ji_bkt5 if w not in _conflict5]
            _xan_bkt5 = list(_conflict5)
            _wp_el5 = (facts.get("wuxing_power") or {}).get("wuxing_power") or {}
            _present5 = [w for w in ("木", "火", "土", "金", "水") if (_wp_el5.get(w) or {}).get('stem_n', 0) or (_wp_el5.get(w) or {}).get('ben_n', 0) or (_wp_el5.get(w) or {}).get('zhong_n', 0) or (_wp_el5.get(w) or {}).get('yu_n', 0)]
            for w in _present5:
                if w in _xi_bkt5 or w in _ji_bkt5 or w in _xan_bkt5 or w == _w5:
                    continue
                _xan_bkt5.append(w)
            return {'layer': 'YONGYAO_RESOLVE', 'state': 'GE_FALLBACK',
                    'primary_medicine': {'wuxing': _w5, 'gan': list(WX_GAN.get(_w5, ())),
                                          'function': _src5,
                                          'kind': ('格局用神' if _gy5 else '旺衰喜用神'),
                                          'classic': 'DTS L215 体用 + L235 衰喜帮/旺宜泄', 'blocked': None},
                    'auxiliary_medicine': [{'wuxing': a, 'gan': list(WX_GAN.get(a, ()))} for a in _aux5],
                    'ji_shen': _ji_bkt5,
                    'xiji_xian': {'xi_wx': _xi_bkt5, 'ji_wx': _ji_bkt5, 'xian_wx': _xan_bkt5,
                                  'basis': 'PZZQ L3208/L2319 格局×旺衰喜忌查表(_GEJU_XIJI_WS); DTS L404「自喜忌之外皆闲神」闲=局中余集(中性)'},
                    'rejected_climate': rejected_climate,
                    'ge_fallback_source': _src5,
                    'yuanliu_yongshen': _yl, 'tiaohou_yongshen': _th, 'routing': _rt,
                    'boundary_note': '源1无主病+无格, 走源5旺衰喜用神(身弱喜印/身旺喜食伤, DTS L215); 喜忌闲=DTS L404 + PZZQ L3208 十神查表(撤 V7.45 机械 KE[用神]+日主)'}
        _xjj0 = _rt.get("xiji_xian") or {}
        return {'layer': 'YONGYAO_RESOLVE', 'state': 'NO_BING',
                'primary_medicine': _ge_medicine(facts), 'auxiliary_medicine': [],
                'ji_shen': [],
                'xiji_xian': {'xi_wx': _xjj0.get("xi_wx") or [], 'ji_wx': _xjj0.get("ji_wx") or [], 'xian_wx': [],
                              'basis': 'PZZQ L3208 十神喜忌查表 + DTS L404「自喜忌之外皆闲神」'},
                'rejected_climate': rejected_climate,
                'yuanliu_yongshen': _yl,   # ★ 第2层 源流(不动 primary)
                'tiaohou_yongshen': _th,   # ★ 第3层 调候(不动 primary)
                'routing': _rt,   # ★ 第4层 程级路由
                'boundary_note': '无主病且无格体喜神/救应神, 不裁决用药'}

    edges = []   # 每条: 五行/gan/边类型/功能/是否采纳/剔除理由

    # V7.48 旺衰方向(帮/泄 取舍据 DTS L235「衰则喜帮喜助/旺则宜泄宜伤」):
    #   身旺(strength_verdict 含'泄伤')→"帮"边(比劫助身)剔除, 助旺非疏病;
    #   身弱(含'帮身')→"帮"边保留. 读 l3_contract, 非 case 特判.
    _shen_wang = _ws_dirn(facts) == 'strong'
    def add(wx, kind, func):
        gan = list(WX_GAN.get(wx, ()))
        ok = _safe(wx, bw)
        note = ''
        if not ok:
            note = '帮病(同病或生病), 剔除'
        elif wx in _unresolved_bing_wx or SHENG.get(wx, '') in _unresolved_bing_wx:
            ok = False
            note = '次病转归未核验，暂不确认用药'
        elif wx in _sec_wx or SHENG.get(wx, '') in _sec_wx:
            ok = False
            _hit = sorted(x for x in (wx, SHENG.get(wx, '')) if x in _sec_wx)
            note = '帮次病(%s), 剔除' % '/'.join(_hit)
        elif kind == '化' and KE_BACK.get(dm) == wx:
            ok = False
            note = '化反克日主(生杀), 剔除'
        elif kind == '化' and KE.get(dm) == wx and dm_ben == 0:
            ok = False
            note = '化财而日主无本气根, 任不起财反成财多身弱, 剔除'
        elif kind == '帮' and _shen_wang:
            # DTS L235 旺则宜泄宜伤: 身旺时比劫帮身=助旺非疏病, 剔除(印生身同类, 见下)
            ok = False
            note = '身旺帮边剔除(DTS L235 旺宜泄, 比劫助身非疏病)'
        elif kind == '帮' and wx == SHENG_BACK.get(dm, '') and _shen_wang:
            # 身旺时印生身(印=SHENG_BACK[dm])亦助旺, 剔除
            ok = False
            note = '身旺印生身剔除(DTS L235 旺宜泄)'
        edges.append({'wuxing': wx, 'gan': gan, 'kind': kind,
                      'function': func, 'accepted': ok, 'reject_reason': note})

    # 制
    add(KE_BACK.get(bw, ''), '制', '克病(%s)' % bw)
    # 化 (病所生, 泄病)
    add(SHENG.get(bw, ''), '化', '泄病之气(%s生? )' % bw)
    # ★ V7.201 印病食伤泄边: 病=印(生我)时食伤(我生)=泄身之旺。
    #   原典: PZZQ L1146 成句「身印两旺, 用食伤泄」; L543 朱家宝造(庚申乙酉癸未乙卯)
    #   「印格用食」亲证——印重而财不透, 用食非用财。仅印病加此边:
    #   泄气太重之病源即食伤不可再泄; 官杀/财/比劫病各有对位边(杀重药=食伤制煞等)。
    if bw == SHENG_BACK.get(dm, ''):
        add(SHENG.get(dm, ''), '泄', '食伤泄身之旺(身印两旺用食伤泄)')
    # 帮 (比劫 + 印)
    add(dm, '帮', '比劫帮身')
    add(SHENG_BACK.get(dm, ''), '帮', '印生身')
    # 水泛木浮特殊: 火暖化
    if bw == '水':
        add('火', '暖', '丙丁暖化寒湿')

    # ★ V7.204 扶抑扶边(DTS L215 体用正法+PZZQ 扶抑章两案亲证):
    #   「日主弱, 则提纲有物, 帮身以制其神者亦皆为我用; 提纲食伤财官太旺,
    #    则取年月时上印比为喜神」——身弱(得令得地双失: 日主 ben_n==0 且
    #   ling_state∈休/囚/死)且病∈{官杀/食伤/财}(印病走泄损 V7.201、比劫病
    #   走制, 均不在此列)时, 扶边(印/劫)入局, 透干有力者优先
    #   (蔡孑民 丁劫透年干, PZZQ L975「水旺火弱, 用劫帮身」; 伍朝枢
    #   财官两旺身弱用印 L971); 同档印主比辅(DTS L215 喜印主比辅)。
    #   扶边不受 _safe 帮病剔除约束: L215 该款为身弱取喜神的明文规则,
    #   印比扶身不因兼生次病而废(蔡造火生土伤官, 沈仍用劫)。
    if bw in (KE_BACK.get(dm, ''), SHENG.get(dm, ''), KE.get(dm, '')) and bw:
        _dm_p = ((facts.get('wuxing_power') or {}).get('wuxing_power') or {}).get(dm) or {}
        if _dm_p.get('ben_n') == 0 and _dm_p.get('ling_state') in ('休', '囚', '死'):
            _fu_cands = []
            for _fwx, _ftag in ((SHENG_BACK.get(dm, ''), '印'), (dm, '劫')):
                if not _fwx:
                    continue
                _tier = None  # 0=透干(年月时干), 1=藏支(年月时支); None=年月时不见
                if _pl:
                    if any(GAN_WX.get(_pl[p][0]) == _fwx for p in ('year', 'month', 'hour')):
                        _tier = 0
                    elif any(ZHI_BEN_WX.get(_pl[p][1]) == _fwx for p in ('year', 'month', 'hour')):
                        _tier = 1
                if _tier is not None:
                    _fu_cands.append((_tier, 0 if _ftag == '印' else 1, _fwx, _ftag))
            if _fu_cands:
                _tier, _yin, _fwx, _ftag = min(_fu_cands)
                edges.append({'wuxing': _fwx, 'gan': list(WX_GAN.get(_fwx, ())),
                              'kind': '扶',
                              'function': '%s%s扶身(身弱印比喜神, DTS L215/PZZQ L971·L975)' % (_ftag, _fwx),
                              'accepted': True, 'reject_reason': ''})

    accepted = [e for e in edges if e['accepted']]
    # 去重(同五行保留kind最优: 制>化>帮/暖)
    seen = {}
    for e in accepted:
        if e['wuxing'] not in seen:
            seen[e['wuxing']] = e
    uniq = list(seen.values())

    # 药受制检查: 采纳药的天干是否被天干五合合绊(合而不化)
    th = facts.get('tian_he') or {}
    _pairs = th.get('he_pairs', [])

    def _gan_positions(wx):
        out = []
        if _pl:
            for pos in ('year', 'month', 'hour'):
                g = _pl[pos][0]
                if GAN_WX.get(g) == wx:
                    out.append((pos, g))
        return out

    medicine_blocked = []
    for e in uniq:
        for pos, g in _gan_positions(e['wuxing']):
            for pair in _pairs:
                if g in pair['stems'] and pos in pair.get('pillars', []):
                    other = pair['stems'][0] if pair['stems'][1] == g else pair['stems'][1]
                    if pair['huashen_on_month_qi'] or th.get('has_long_chen'):
                        medicine_blocked.append({'wuxing': e['wuxing'], 'gan': g, 'pos': pos,
                            'with': other, 'state': '合而化', 'huashen': pair['huashen_wuxing'],
                            'note': '与%s合化%s, 不简单作绊' % (other, pair['huashen_wuxing'])})
                    else:
                        medicine_blocked.append({'wuxing': e['wuxing'], 'gan': g, 'pos': pos,
                            'with': other, 'state': '合绊(合而不化)', 'huashen': pair['huashen_wuxing'],
                            'note': '药%s被%s合绊, 制病力失; 需岁运解合, 或改取印化/比劫帮' % (g, other)})

    zhu = next((e for e in uniq if e['kind'] == '制'), None)
    # ★ V7.201 印病泄主裁决(透干/本气根判别): 制药(财)全无透干且无本气根(仅藏中余
    #   =虚财, PZZQ L1130「财无根气不能用财破印」)而食伤泄透干或本气根在局时,
    #   泄升主——朱家宝 L543「印格用食」亲证(财不透用食);
    #   pzzq-007 财坐酉本气根→制保持不受影响; 制无根而泄亦无根→维持原主药不猜。
    if zhu is not None and bw == SHENG_BACK.get(dm, ''):
        _wp_el = (facts.get('wuxing_power') or {}).get('wuxing_power') or {}

        def _tou_ben(wx):
            _e = _wp_el.get(wx) or {}
            return int(_e.get('stem_n') or 0), int(_e.get('ben_n') or 0)

        _zt, _zb = _tou_ben(zhu['wuxing'])
        if _zt == 0 and _zb == 0:
            _xie = next((e for e in uniq if e['kind'] == '泄'), None)
            if _xie is not None:
                _xt, _xb = _tou_ben(_xie['wuxing'])
                if _xt >= 1 or _xb >= 1:
                    zhu = _xie
    # ★ V7.204 扶升主: 身弱+食伤财官病 → 扶边(印/劫)优先于制(DTS L215「提纲食伤
    #   财官太旺, 取年月时上印比为喜神」; 蔡孑民 L975 用劫帮身/伍朝枢 L971 用印,
    #   病药制边让位)。扶边被天干五合合绊(medicine_blocked)则不升, 维持原主不猜。
    _fu_zhu = next((e for e in uniq if e['kind'] == '扶'
                    and not any(m.get('wuxing') == e['wuxing'] for m in medicine_blocked)), None)
    if _fu_zhu is not None:
        zhu = _fu_zhu
    if zhu is None and uniq:
        zhu = uniq[0]
    fu = [e for e in uniq if e is not zhu]

    # V7.25 候神集中裁决源(tiaohou_rank): 候干查表(职能=食伤泄秀/制药 且 有气且未刑)
    #   -> 候干升 primary; 候干=生我(印=主病源) 或 职能不中 -> 让位寒燥交互候食伤
    #   (寒燥月令 × 局内食伤有气, DTS L295/L300). 替换 case-by-case if(原 T3/候神消解 分支).
    from engines.common import tiaohou_rank
    _rank = tiaohou_rank._tiaohou_primary_rank(climate or {}, bw, dm, _pl)
    _climate_promoted = False
    if zhu and _rank['rank'] == 'PROMOTE':
        _sh_wx = _rank['wx']
        _he_ban = any(m.get('wuxing') == _sh_wx and m.get('state', '').startswith('合绊')
                      for m in medicine_blocked)
        if (not _he_ban and _sh_wx not in _unresolved_bing_wx and
                SHENG.get(_sh_wx, '') not in _unresolved_bing_wx):
            zhu = {'wuxing': _sh_wx, 'gan': list(WX_GAN.get(_sh_wx, ())),
                   'function': '调候候神(%s)' % '/'.join(_rank['reason']),
                   'kind': '调候',
                   'classic': '+ '.join(_rank['refs']),
                   'blocked': None}
            _climate_promoted = True
            fu = [e for e in uniq if e['wuxing'] != _sh_wx]

    if not _climate_promoted:
        rejected_climate.extend(deferred_climate_rejections)

    ji = [bw]
    sb = SHENG_BACK.get(bw, '')
    if sb:
        ji.append(sb)
    # V7.25 比劫争财入忌神表: 财主病(主病=日主所克=财) 且 比劫成众(透>=2 或 坐旺) ->
    #   比劫入忌(争财破官, 原典"群比争财" L1808). 真值 丁卯庚戌庚戌庚辰: 忌金(三庚比劫争财), 不只忌土(主病).
    _KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
    _bi_wx = dm
    _cai_wx = _KE.get(dm, '')
    if bw == _cai_wx and _bi_wx not in ji:
        _bi_brs = [p[1] for p in _pl.values()] if _pl else []
        _bi_pen = any(GAN_WX.get(_pl[pos][0]) == _bi_wx for pos in ('year', 'month', 'hour') if _pl)
        # ★ V7.103 修正: 土之旺地为【禄巳、帝旺午】(十二长生: 长生申/禄巳/帝旺午/墓辰);
        #   旧表以四库(墓库=轻根, PZZQ L800-801)为坐旺, 致土之比劫坐四库被误判得势而入忌(群比争财).
        #   与 V7.94 evil_offset._WANG_BR / V7.102 tiaohou_rank._WANG_ZHI 三处口径统一.
        _bi_wang = any(ZHI_BEN_WX.get(b) == _bi_wx and b in
                       ({'木': ('寅', '卯'), '火': ('巳', '午'), '土': ('巳', '午'),
                          '金': ('申', '酉'), '水': ('亥', '子')}.get(_bi_wx, ())) for b in _bi_brs)
        if _bi_pen or _bi_wang:
            ji.append(_bi_wx)
    # 候神剔除忌神: 候神(炼金/泄秀/制药)是药不是忌. 土重金埋=候火炼金, 火不入忌.
    from engines.common import tiaohou_rank
    _rank_ji = tiaohou_rank._tiaohou_primary_rank(climate or {}, bw, dm, _pl)
    if _climate_promoted and _rank_ji['rank'] == 'PROMOTE':
        _promote_wx = _rank_ji['wx']
        if _promote_wx in ji:
            ji.remove(_promote_wx)
    # ★ V7.46 喜忌闲三桶(DTS L404「自喜忌之外皆闲神」+ PZZQ L3208 十神相对格):
    #   喜桶 = 十神喜查表(PZZQ 八格, _geju_xiji_map 同表) + 格喜(xi_wx) + 病药喜药(制/化/帮)
    #   忌桶 = 十神忌查表 + 破格忌(po_ge) + 病根(bw) + 生病者(SHENG_BACK[bw])
    #   闲桶 = 局中实际五行(wuxing_power) − 喜 − 忌 − 用神(primary) 的余集(DTS L404 中性不预派吉凶)
    #   喜忌查表依据: month_qi_ten_god(PZZQ L3208 十神相对格) → 喜忌十神名 → 日主相对五行(_tg_wx)
    _dmwx_r = dm
    _tg = facts.get("month_qi_ten_god", "") or ""
    _x_tg, _j_tg = _geju_xiji_ws(facts, _tg)
    _x_cat_wx = []
    for _c in _x_tg:
        for _cw in _tg_wx(_c, _dmwx_r):
            if _cw and _cw not in _x_cat_wx:
                _x_cat_wx.append(_cw)
    _j_cat_wx = []
    for _c in _j_tg:
        for _cw in _tg_wx(_c, _dmwx_r):
            if _cw and _cw not in _j_cat_wx:
                _j_cat_wx.append(_cw)
    _xian_wx = []
    _xi_cat = [w for w in _x_cat_wx if w]
    _po_req_wx = []
    _gc_r = _usable_ge_cheng(facts)
    for _p in (_gc_r.get('po_ge') or []):
        if (_p.get('type') == '阳刃无官煞透' or
                _p.get('condition_id') == 'WEALTH_AND_SHA' or
                (_p.get('match') == 'ALL' and len(_p.get('required') or []) > 1)):
            continue  # 条件性财煞组合不能逐项推为无条件的忌神。
        for _g in (_p.get('required') or []):
            for _gw in _tg_wx(_g, _dmwx_r):
                if _gw and _gw not in _po_req_wx:
                    _po_req_wx.append(_gw)
    # 拼接后去重(十神查表值 + 格喜 + 病药喜药 可能重叠同一五行, 桶内不重复)
    _xi_bkt = []
    for _w in list(_xi_cat) + list(_gc_r.get('xi_wx') or []):
        if _w and _w not in _xi_bkt:
            _xi_bkt.append(_w)
    for _m in uniq:
        if _m['wuxing'] and _m['wuxing'] not in _xi_bkt:
            _xi_bkt.append(_m['wuxing'])
    _ji_bkt = []
    for _w in list(_j_cat_wx) + _po_req_wx:
        if _w and _w not in _ji_bkt:
            _ji_bkt.append(_w)
    if bw and bw not in _ji_bkt:
        _ji_bkt.append(bw)
    _sb_bw = SHENG_BACK.get(bw, '')
    if _sb_bw and _sb_bw not in _ji_bkt:
        _ji_bkt.append(_sb_bw)
    # ★ V7.49 候神不入忌桶(同 ji_shen 原则, L598-604): 候神=原典用神(QTBJ 候干表),
    #   既是 primary 用神, 不得同时列忌(自相矛盾). 生病者(火生土病)让位炼金候神.
    _hou_wx_bkt = (zhu or {}).get('wuxing', '') if (zhu or {}).get('kind') == '调候' else ''
    if _hou_wx_bkt and _hou_wx_bkt in _ji_bkt:
        _ji_bkt.remove(_hou_wx_bkt)
    # ★ V7.51 互斥裁决优先级(病/药优先于查表喜忌):
    #   喜忌来源冲突时，未裁决不等于已证明为闲神。
    #   ① 病根(bw)=原典主病 -> 忌(V7.50: 病明确为忌, 不降级归闲)
    #   ② 药(制/化/帮/暖 accepted)=原典病药层用药 -> 喜, 优先于查表喜忌
    #      (PZZQ L3717-3718「财轻印多, 用财损印, 喜财乡」: 财(药)与印(病)轻重决, 非一刀切互斥)
    #   ③ 查表喜忌(PZZQ 取运章)/破格忌: 与①②冲突时让位
    #   ④ 其余冲突五行 -> conflict_wx，保留待裁决。
    _yao_wx = set(m.get('wuxing') for m in uniq if m.get('wuxing'))
    _conflict = [w for w in _ji_bkt if w in _xi_bkt]
    _unresolved = []
    for _w in list(_conflict):
        if bw and _w == bw:
            # ① 病根: 留忌桶, 喜桶剔除(不归闲)
            _xi_bkt = [x for x in _xi_bkt if x != _w]
        elif _w in _yao_wx:
            # ② 药: 留喜桶, 忌桶剔除(药优先于查表喜忌)
            _ji_bkt = [x for x in _ji_bkt if x != _w]
        else:
            # 无病药优先依据时保留冲突，不能直接认定为闲神。
            _unresolved.append(_w)
            _xi_bkt = [x for x in _xi_bkt if x != _w]
            _ji_bkt = [x for x in _ji_bkt if x != _w]
    _pm_wx = (zhu or {}).get('wuxing', '')
    _wp_el = (facts.get('wuxing_power') or {}).get('wuxing_power') or {}
    _present = [w for w in ("木", "火", "土", "金", "水") if (_wp_el.get(w) or {}).get('stem_n', 0) or (_wp_el.get(w) or {}).get('ben_n', 0) or (_wp_el.get(w) or {}).get('zhong_n', 0) or (_wp_el.get(w) or {}).get('yu_n', 0)]
    _xian_wx = []
    for w in _present:
        if w in _xi_bkt or w in _ji_bkt or w in _xian_wx or w in _unresolved or w == _pm_wx:
            continue
        _xian_wx.append(w)

    primary_medicine = None
    if zhu:
        _zb = [b for b in medicine_blocked if b['wuxing'] == zhu['wuxing']
               and b['state'].startswith('合绊')]
        # kind/classic 取自 zhu 边(候神升 primary 时 kind=调候/classic=候神原典; 默认=制/相克)
        primary_medicine = {'wuxing': zhu['wuxing'], 'gan': zhu['gan'],
                            'function': zhu['function'],
                            'kind': zhu.get('kind', '制'),
                            'classic': zhu.get('classic', '五行相克为基础关系; DTS FAN_JU.001'),
                            'blocked': _zb[0] if _zb else None}
        if _climate_promoted and _rank.get('candidate_stem'):
            primary_medicine['candidate_stem'] = _rank['candidate_stem']
            primary_medicine['candidate_stem_visible'] = _rank['candidate_stem_visible']
            primary_medicine['stem_equivalence_status'] = _rank['stem_equivalence_status']
            primary_medicine['candidate_source_verification'] = _rank.get('candidate_source_verification', 'NOT_VERIFIED')
    aux = [{'wuxing': e['wuxing'], 'gan': e['gan'], 'kind': e['kind'],
            'function': e['function'],
            'classic': 'DTS QI_HOU.008 丙丁暖化/化杀生身为原典通例' if e['kind'] in ('暖',)
            else '原典病药通例(化/帮)'} for e in fu]

    return {
        'layer': 'YONGYAO_RESOLVE', 'state': 'YONGYAO_RESOLVED',
        'primary_bing': {'bing_id': bid, 'wuxing': bw},
        'primary_medicine': primary_medicine,
        'auxiliary_medicine': aux,
        'all_edges': edges,
        'medicine_blocked': medicine_blocked,
        'ji_shen': ji,
        # ★ V7.46 喜忌闲三桶(DTS L404 + PZZQ L3208 十神相对格, 查表派生):
        #   喜桶=十神喜查表+格喜+病药喜药; 忌桶=十神忌查表+破格忌+病根+生病者; 闲桶=局中余集(DTS L404 中性)
        'xiji_xian': {'xi_wx': _xi_bkt, 'ji_wx': _ji_bkt, 'xian_wx': _xian_wx, 'conflict_wx': _unresolved,
                      'basis': 'PZZQ L3208 十神喜忌查表(_geju_xiji_map)+破格忌+病根; DTS L404「自喜忌之外皆闲神」闲=局中余集(中性, 不预派吉凶)'},
        'rejected_climate': rejected_climate,
        'rule': '制=克病; 化=泄病(克身则剔); 帮=比劫印帮身(是病则剔); 水泛加火暖',
        'boundary_note': '离散三边全列按主辅; 只裁用药方向不判吉凶; 化/帮为原典通例, 须看命局分寸',
        # 不能把特定乙木寒湿切片固定套用于所有日主及病药路径。
        # 主药条件到原典切片的逐条绑定尚未完成，保留计算结果但不伪造证据。
        'evidence_refs': [],
        'evidence_status': 'NOT_EVALUABLE',
        'yuanliu_yongshen': _yl,   # ★ 第2层 源流(不动 primary)
        'tiaohou_yongshen': _th,   # ★ 第3层 调候(不动 primary)
        'routing': _rt,   # ★ 第4层 程级路由
    }
