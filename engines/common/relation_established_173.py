# -*- coding: utf-8 -*-
"""PATCH-173-A 食神生财 premise->成立 Relation Rule
原典: 月令食神, 四柱见财, 为食神生财; 且要求财有根。
成立=食神格入口+财同现+财有根; 位置/隔位/食神旺衰仍UNKNOWN。"""


def shisheng_shengcai_established(facts):
    """食神生财是否成立(三态); 不判格成。"""
    se = facts.get('shishen_entry', {})
    ah = facts.get('any_stem_has_ten_god', {})
    tr = facts.get('target_root_facts', {})
    # ①月令食神入口
    is_shishen = se.get('is_entry')
    # ②财同现
    has_cai = ah.get('财')
    # ③财有根(原典: 食神生财要求财有根)
    cai_root = tr.get('财')
    if is_shishen is not True:
        return {'relation': '食神生财', 'state': 'UNSATISFIED',
                'reason': '非食神格入口'}
    if has_cai is False or cai_root is False:
        return {'relation': '食神生财', 'state': 'UNSATISFIED',
                'reason': '无财或财无根'}
    if has_cai is True and cai_root is True:
        return {'relation': '食神生财', 'state': 'SATISFIED',
                'reason': '月令食神+见财+财有根',
                'note': '位置/隔位/食神旺衰仍UNKNOWN, 不等于格成'}
    return {'relation': '食神生财', 'state': 'UNKNOWN',
            'reason': '财同现或财根信息不全'}


def shishen_zhisha_established(facts):
    """食神制杀结构成立(三态); 有效性/身强/制化足量仍UNKNOWN, 不判美格。"""
    se = facts.get('shishen_entry', {})
    members = facts.get('ten_god_members', [])
    is_shishen = se.get('is_entry')
    has_sha = any(m.get('ten_god') == '七杀' for m in members)
    if is_shishen is not True:
        return {'relation': '食神制杀', 'state': 'UNSATISFIED',
                'reason': '非食神格入口'}
    if has_sha is False:
        return {'relation': '食神制杀', 'state': 'UNSATISFIED',
                'reason': '四柱不见七杀'}
    if has_sha is True:
        return {'relation': '食神制杀', 'state': 'SATISFIED',
                'reason': '月令食神+见七杀(结构前提)',
                'note': '仅结构前提具备; 身强(160未授权)/制化足量/财党杀/枭夺食仍UNKNOWN, 不等于制杀有效或美格'}
    return {'relation': '食神制杀', 'state': 'UNKNOWN',
            'reason': '七杀信息不全'}


def shangguan_shengcai_established(facts):
    """伤官生财结构成立(三态); 财有根/伤官旺/身强仍后续, 不判格成。
    原典(沈): 伤官生财=月令伤官+见财; "有根"指日主, 财有根为徐注质量条件非硬成立条件。"""
    sg = facts.get('shangguan_entry', {})
    ah = facts.get('any_stem_has_ten_god', {})
    is_sg = sg.get('is_entry')
    has_cai = ah.get('财')
    if is_sg is not True:
        return {'relation': '伤官生财', 'state': 'UNSATISFIED',
                'reason': '非伤官格入口'}
    if has_cai is False:
        return {'relation': '伤官生财', 'state': 'UNSATISFIED',
                'reason': '四柱不见财'}
    if has_cai is True:
        return {'relation': '伤官生财', 'state': 'SATISFIED',
                'reason': '月令伤官+见财',
                'note': '财有根(质量evidence)/日主有根身强/伤官旺/财旺/位置隔位仍后续UNKNOWN; 财无根不等于关系不存在; 不等于格成'}
    return {'relation': '伤官生财', 'state': 'UNKNOWN',
            'reason': '财信息不全'}


def shangguan_peiyin_established(facts):
    """伤官佩印结构成立(三态); 伤官旺/印有根/身强弱后续, 不判格成。
    原典: 伤官佩印=月令伤官+见印; 伤官旺/印有根为格成后续非结构硬条件。"""
    sg = facts.get('shangguan_entry', {})
    ah = facts.get('any_stem_has_ten_god', {})
    is_sg = sg.get('is_entry')
    has_yin = ah.get('印')
    if is_sg is not True:
        return {'relation': '伤官佩印', 'state': 'UNSATISFIED',
                'reason': '非伤官格入口'}
    if has_yin is False:
        return {'relation': '伤官佩印', 'state': 'UNSATISFIED',
                'reason': '四柱不见印'}
    if has_yin is True:
        return {'relation': '伤官佩印', 'state': 'SATISFIED',
                'reason': '月令伤官+见印',
                'note': '伤官旺/印有根/身强弱/制化有效仍后续UNKNOWN, 不等于格成'}
    return {'relation': '伤官佩印', 'state': 'UNKNOWN',
            'reason': '印信息不全'}


def cai_shengguan_established(facts):
    """财生官结构成立(三态); 仅正官(七杀≠正官,166.1); 财官旺/位置有效/破坏后续。"""
    ah = facts.get('any_stem_has_ten_god', {})
    members = facts.get('ten_god_members', [])
    has_cai = ah.get('财')
    has_zhengguan = any(m.get('ten_god') == '正官' for m in members)
    if has_cai is False or has_zhengguan is False:
        return {'relation': '财生官', 'state': 'UNSATISFIED',
                'reason': '无财或无正官(七杀≠正官)'}
    if has_cai is True and has_zhengguan is True:
        return {'relation': '财生官', 'state': 'SATISFIED',
                'reason': '见财+见正官(结构关系)',
                'note': '仅结构关系具备; 财旺/官旺/力量关系/位置是否有效生扶/是否被伤杀破坏仍后续UNKNOWN; 不等于财旺生官成立或格成'}
    return {'relation': '财生官', 'state': 'UNKNOWN',
            'reason': '财或正官信息不全'}


def yin_huasha_established(facts):
    """印化杀结构关系(三态); 印+七杀; 印+正官≠印化杀; 身强弱/印旺弱后续。"""
    ah = facts.get('any_stem_has_ten_god', {})
    members = facts.get('ten_god_members', [])
    has_yin = ah.get('印')
    has_sha = any(m.get('ten_god') == '七杀' for m in members)
    if has_yin is False or has_sha is False:
        return {'relation': '印化杀', 'state': 'UNSATISFIED',
                'reason': '无印或无七杀(印+正官≠印化杀)'}
    if has_yin is True and has_sha is True:
        return {'relation': '印化杀', 'state': 'SATISFIED',
                'reason': '见印+见七杀(结构关系)',
                'note': '仅结构关系具备; 身强弱/印旺弱/杀旺弱/印是否真承杀化杀/月令归属/财破印仍后续UNKNOWN; 不等于化杀有效或格成'}
    return {'relation': '印化杀', 'state': 'UNKNOWN',
            'reason': '印或七杀信息不全'}


def cai_yin_xiangsui_established(facts):
    """财印三者同现结构(三态); 财+正官+印; 同现≠护官成立。"""
    ah = facts.get('any_stem_has_ten_god', {})
    members = facts.get('ten_god_members', [])
    has_cai = ah.get('财')
    has_yin = ah.get('印')
    has_zhengguan = any(m.get('ten_god') == '正官' for m in members)
    if has_cai is False or has_yin is False or has_zhengguan is False:
        return {'relation': '财印三者同现', 'state': 'UNSATISFIED',
                'reason': '缺财/印/正官其一(七杀≠正官)'}
    if has_cai is True and has_yin is True and has_zhengguan is True:
        return {'relation': '财印三者同现', 'state': 'SATISFIED',
                'reason': '见财+见正官+见印(结构同现)',
                'note': '仅结构同现; 财印相随有效/财印护官/官得保护/财印是否不相碍仍后续UNKNOWN; 不等于护官成立或格成'}
    return {'relation': '财印三者同现', 'state': 'UNKNOWN',
            'reason': '财/印/正官信息不全'}


def guansha_zhiren_established(facts):
    """官杀制刃候选结构(三态); 阳刃入口+见正官或七杀; 真制刃/七杀被合后续UNKNOWN。"""
    yr = facts.get('yangren_entry', {})
    members = facts.get('ten_god_members', [])
    is_yr = yr.get('is_entry')
    has_guan = any(m.get('ten_god') == '正官' for m in members)
    has_sha = any(m.get('ten_god') == '七杀' for m in members)
    if is_yr is not True:
        return {'relation': '官杀制刃', 'state': 'UNSATISFIED',
                'reason': '非阳刃格入口'}
    if has_guan is False and has_sha is False:
        return {'relation': '官杀制刃', 'state': 'UNSATISFIED',
                'reason': '不见官杀'}
    if has_guan is True or has_sha is True:
        return {'relation': '官杀制刃', 'state': 'SATISFIED',
                'reason': '阳刃入口+见正官或七杀(候选结构)',
                'note': '仅候选结构; 官杀是否真制刃/官杀得力/刃当令旺/七杀被合/官杀受冲破害仍后续UNKNOWN; 不等于制刃有效或刃格成'}
    return {'relation': '官杀制刃', 'state': 'UNKNOWN',
            'reason': '官杀信息不全'}


def caiyin_peiyangren_established(facts):
    """财印配合阳刃候选结构(三态); 阳刃+见财+见印; 财印不相碍后续UNKNOWN。"""
    yr = facts.get('yangren_entry', {})
    ah = facts.get('any_stem_has_ten_god', {})
    is_yr = yr.get('is_entry')
    has_cai = ah.get('财')
    has_yin = ah.get('印')
    if is_yr is not True:
        return {'relation': '财印配合阳刃', 'state': 'UNSATISFIED',
                'reason': '非阳刃格入口'}
    if has_cai is False or has_yin is False:
        return {'relation': '财印配合阳刃', 'state': 'UNSATISFIED',
                'reason': '缺财或印'}
    if has_cai is True and has_yin is True:
        return {'relation': '财印配合阳刃', 'state': 'SATISFIED',
                'reason': '阳刃入口+见财+见印(候选结构)',
                'note': '仅候选结构; 财生杀/印滋刃/财印不相碍/配合有效仍后续UNKNOWN; 不等于贵显或格成'}
    return {'relation': '财印配合阳刃', 'state': 'UNKNOWN',
            'reason': '财或印信息不全'}


def shishang_xieren_established(facts):
    """食伤泄刃候选结构(三态); 阳刃+见食神或伤官; 刃旺/已走官杀路径后续UNKNOWN。"""
    yr = facts.get('yangren_entry', {})
    members = facts.get('ten_god_members', [])
    is_yr = yr.get('is_entry')
    has_shishang = any(m.get('ten_god') in ('食神','伤官') for m in members)
    if is_yr is not True:
        return {'relation': '食伤泄刃', 'state': 'UNSATISFIED',
                'reason': '非阳刃格入口'}
    if has_shishang is False:
        return {'relation': '食伤泄刃', 'state': 'UNSATISFIED',
                'reason': '不见食伤'}
    if has_shishang is True:
        return {'relation': '食伤泄刃', 'state': 'SATISFIED',
                'reason': '阳刃入口+见食神或伤官(泄刃候选结构)',
                'note': '仅候选结构; 刃是否旺/食伤真泄刃/是否已走官杀制刃路径/其他破坏仍后续UNKNOWN; 不等于泄秀成立或格成'}
    return {'relation': '食伤泄刃', 'state': 'UNKNOWN',
            'reason': '食伤信息不全'}
