# -*- coding: utf-8 -*-
"""外格规则：從殺/曲直/炎上/潤下/從兒/從勢/從革 判定

★ DEMO 状态(非生产, V7.125 标注):
  本模块未被主链 bazi_gate 引用。主链外格/从格判定走 engines/common/special_pattern.py
  (从杀格 CANDIDATE 状态机 L741-748 / 专旺格 ZHUANWANG_NAME L27 / 从格破格 ge_jie_layer L326+),
  与本模块是两套不同步口径。本模块自包含 HIDDEN 表 + 依赖 gc002_builder(非主链 l0_fact_builder),
  属独立演示; 待接入主链时须与 special_pattern.py 口径归一(AGENTS.md 第四节「同一层不设两套裁决」)。
  与 six_relative_full.py(六亲 demo) 同列, 均登记为「已实现未接主链」."""
import sys
sys.path.insert(0, r'engines\common')
from gc002_builder import paipan, HIDDEN

ELEM = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
        '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
GAN = '甲乙丙丁戊己庚辛壬癸'
BENQI = {k: v[0] for k, v in HIDDEN.items()}
gen = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
ke = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}


def ten_lists(day):
    de = ELEM[day]
    me_ke = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '木'}[de]
    yang_day = GAN.index(day) % 2 == 0
    def li(elem, same):
        return [s for s in GAN if ELEM[s] == elem and (GAN.index(s) % 2 == 0) == same]
    return {'sha': li(me_ke, yang_day), 'guan': li(me_ke, not yang_day),
            'cai': [s for s in GAN if ELEM[s] == ke[de]],
            'shi_shang': [s for s in GAN if ELEM[s] == gen[de]],
            'sha_elem': me_ke}


def cong_sha_rule(c):
    day = c['dm']; stems = c['stems']; br = c['br']
    tl = ten_lists(day); de = ELEM[day]
    yin = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}[de]
    rootless = all(ELEM[h] != de for b in br for h in HIDDEN[b])
    no_fu = all(ELEM[s] not in (de, yin) for s in stems)
    benqi = BENQI[c['month']]
    sha_dang = benqi in tl['sha'] or benqi in tl['guan']
    no_shang = not any(s in tl['shi_shang'] for s in stems)
    sha_root = any(ELEM[h] == tl['sha_elem'] for b in br for h in HIDDEN[b])
    mixed = any(s in tl['guan'] for s in stems) and any(s in tl['sha'] for s in stems)
    # ★ V7.125 官杀混杂矛盾修正: PZZQ「弃命从杀, 杀无制化, 有官星杂之则不纯」——
    #   官杀混杂(mixed)时不成【纯】从杀(须杀独成势/官留杀制), 旧判把官吞进从杀是口径反.
    #   仅【纯杀】(月令本气属杀, 天干无官)方成立; 官杀混杂 -> 留 boundary, 不报从杀格.
    guan_in_stems = any(s in tl['guan'] for s in stems)
    sha_in_stems = any(s in tl['sha'] for s in stems)
    pure_sha = (not guan_in_stems) and (sha_in_stems or benqi in tl['sha'])
    if rootless and no_fu and sha_dang and no_shang and sha_root and pure_sha:
        return {'pattern_state': 'DETERMINED(從殺格)', 'pattern_success_state': 'SUCCESS(棄命從殺)',
                'condition_context': '日主无根无食制，纯杀成势(官星不杂)',
                'evidence': ['SFTK-012-002'], 'note': '從殺成：舍命從殺；忌根運制殺運'}
    if rootless and no_fu and sha_dang and mixed:
        return {'pattern_state': 'INCOMPLETE(官殺混雜不成純從殺)', 'pattern_success_state': 'NA',
                'condition_context': '日主无根但官杀混杂(官星杂之, PZZQ「有官星杂之则不纯」), 须杀独成势方论从杀',
                'evidence': ['SFTK-012-002'], 'note': '官杀混杂边界: 不报纯从杀, 留待主链 special_pattern 裁定'}
    return None


def quzhi_rule(c):
    day = c['dm']; stems = c['stems']; br_set = set(c['br'])
    if ELEM[day] != '木':
        return None
    sanhe = all(x in br_set for x in ['亥', '卯', '未'])
    sanhui = all(x in br_set for x in ['寅', '卯', '辰'])
    no_gengxin = not any(s in ('庚', '辛') for s in stems)
    if (sanhe or sanhui) and no_gengxin:
        return {'pattern_state': 'DETERMINED(曲直格)', 'pattern_success_state': 'SUCCESS(木局從木)',
                'condition_context': '甲乙日木局/木方全，不见庚辛',
                'evidence': ['YHZP-101-010'], 'note': '曲直成：從木運；忌西方金運'}
    return None


def yan_shang_rule(c):
    day = c['dm']; br_set = set(c['br'])
    if ELEM[day] != '火':
        return None
    sanhe = all(x in br_set for x in ['寅', '午', '戌'])
    sanhui = all(x in br_set for x in ['巳', '午', '未'])
    if sanhe or sanhui:
        return {'pattern_state': 'DETERMINED(炎上格)', 'pattern_success_state': 'SUCCESS(火局從火)',
                'condition_context': '丙丁日火局/火方全',
                'evidence': ['YHZP-101-006'], 'note': '炎上成：從火運；忌水鄉金地'}
    return None


def runxia_rule(c):
    day = c['dm']; br_set = set(c['br'])
    if ELEM[day] != '水':
        return None
    sanhe = all(x in br_set for x in ['申', '子', '辰'])
    sanhui = all(x in br_set for x in ['亥', '子', '丑'])
    if sanhe or sanhui:
        return {'pattern_state': 'DETERMINED(潤下格)', 'pattern_success_state': 'SUCCESS(水局從水)',
                'condition_context': '壬癸日水局/水方全',
                'evidence': ['YHZP-101-007'], 'note': '潤下成：從水運；忌土運淹滯'}
    return None


def conger_rule(c):
    day = c['dm']; stems = c['stems']; br_set = set(c['br'])
    er = gen[ELEM[day]]
    ju_map = {'火': ['寅', '午', '戌'], '水': ['申', '子', '辰'],
              '金': ['巳', '酉', '丑'], '木': ['亥', '卯', '未'], '土': ['巳', '酉', '丑']}
    hui_map = {'火': ['巳', '午', '未'], '水': ['亥', '子', '丑'],
               '金': ['申', '酉', '戌'], '木': ['寅', '卯', '辰'], '土': ['申', '酉', '戌']}
    ju_ok = all(x in br_set for x in ju_map[er])
    hui_ok = all(x in br_set for x in hui_map[er])
    cai = gen[er]
    cai_vis = any(ELEM[s] == cai for s in stems)
    if ju_ok or hui_ok:
        ctx = '食伤成局+财透(儿又生儿)' if cai_vis else '食伤成局(财未透)'
        return {'pattern_state': 'DETERMINED(從兒格)', 'pattern_success_state': 'SUCCESS(食伤成勢)',
                'condition_context': ctx, 'evidence': ['DTS-044-001'],
                'note': '從兒成：不論身強弱；忌印奪食'}
    return None


def congshi_rule(c):
    """從勢格 DTS-008-003 A：五陰日+日主无根+财官伤皆透成勢"""
    day = c['dm']; stems = c['stems']; br = c['br']
    if GAN.index(day) % 2 == 0:
        return None
    tl = ten_lists(day); de = ELEM[day]
    yin = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}[de]
    rootless = all(ELEM[h] != de for b in br for h in HIDDEN[b])
    no_fu = all(ELEM[s] not in (de, yin) for s in stems)
    has_cai = any(s in tl['cai'] for s in stems)
    has_guan = any(s in (tl['guan'] + tl['sha']) for s in stems)
    has_shi = any(s in tl['shi_shang'] for s in stems)
    if rootless and no_fu and has_cai and has_guan and has_shi:
        return {'pattern_state': 'DETERMINED(從勢格)', 'pattern_success_state': 'SUCCESS(陰日從勢)',
                'condition_context': '五陰日日主无根+财官伤皆透成勢',
                'evidence': ['DTS-008-003'], 'note': '從勢成：從財官食傷之勢；忌日主根運'}
    return None


def conge_rule(c):
    """從革格 YHZP-121-003 B：庚辛日金局/金方"""
    day = c['dm']; br_set = set(c['br'])
    if ELEM[day] != '金':
        return None
    sanhe = all(x in br_set for x in ['巳', '酉', '丑'])
    sanhui = all(x in br_set for x in ['申', '酉', '戌'])
    if sanhe or sanhui:
        return {'pattern_state': 'DETERMINED(從革格)', 'pattern_success_state': 'SUCCESS(金局從金)',
                'condition_context': '庚辛日金局/金方全',
                'evidence': ['YHZP-121-003'], 'note': '從革成：從金運；B級注層'}
    return None


def jiase_rule(c):
    """稼穡格 YHZP-101-009 A：戊己日辰戌丑未四库全"""
    day = c['dm']; br_set = set(c['br'])
    if ELEM[day] != '土':
        return None
    if all(x in br_set for x in ['辰', '戌', '丑', '未']):
        return {'pattern_state': 'DETERMINED(稼穡格)', 'pattern_success_state': 'SUCCESS(土局從土)',
                'condition_context': '戊己日辰戌丑未四库全',
                'evidence': ['YHZP-101-009'], 'note': '稼穡成：從土運；忌東方木運'}
    return None


if __name__ == '__main__':
    cases = [
        ('GC-009 從殺', 1983, 12, 0, cong_sha_rule),
        ('GC-010 曲直', 1985, 7, 22, quzhi_rule),
        ('GC-011 炎上', 1989, 2, 14, yan_shang_rule),
        ('GC-012 潤下', 1984, 11, 0, runxia_rule),
        ('GC-013 從兒', 1981, 7, 10, conger_rule),
        ('GC-014 從勢', 1968, 5, 10, congshi_rule),
        ('GC-015 從革', 1969, 4, 20, conge_rule),
    ]
    for name, y, m, h, rule in cases:
        p = paipan(y, m, 15, h)
        c = {'dm': p['day_master'], 'stems': [p['stems']['年'], p['stems']['月'], p['stems']['时']],
             'br': list(p['branches'].values()), 'month': p['month_order']}
        r = rule(c)
        print(f'{name}: {p["pillars"]} 日主={p["day_master"]}')
        print(f'  → {r}')
