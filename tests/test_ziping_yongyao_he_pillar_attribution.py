# -*- coding: utf-8 -*-
"""V7.206 病药合对柱位归属回归（用户 2026-11-11 修复 yongyao_resolve L1252）。

修复语义：药受制（合绊）检查由「只按干字匹配」改为「干字匹配 + 参与柱位核对」，
同一天干出现在不同柱时，某柱的合对不再错误归到其他同字天干。
反例：药=木（年甲+月甲双外柱透干），注入合对 甲己(pillars=['year','hour'])：
  旧码 -> 年甲、月甲都记合绊（月甲被错归到年柱的合对）；
  修复后 -> 仅年甲。
边缘登记：pairs 缺 'pillars' 键（旧格式部分数据）时不再阻挡任何药（fail-open），
属用户自主裁决——归属正确优先于覆盖；真实生产 pairs 恒带柱位
（engines/common/daymaster_tian_he.py:89 'pillars': [keys[i], keys[j]]），
构造/旧格式数据才有此差异。构造数据不证明完整命盘合化判定（用户自注），
真盘侧另由不变式测试（blocked.pos ⊆ he_pairs pillars 并集）兜底。
注：GE_FALLBACK 等格局路径早于病药层返回，medicine_blocked 仅病药路径产出，
故单元构造用最小 facts + debate['primary_bing']（同 tests/test_ziping_medicine_he_positions.py）。
"""
from engines.common.yongyao_resolve import resolve_yongyao
from engines.production_entry import FrozenCanonicalBaziChart, production_entry

# 庚日主、病=土 -> 制药=木（甲透年+月双柱）；时柱己与甲成五合对。
_SHUANG_JIA = {'year': ['甲', '寅'], 'month': ['甲', '申'],
               'day': ['庚', '午'], 'hour': ['己', '卯']}
_PAIR_JIA_JI = {'stems': ['甲', '己'], 'pillars': ['year', 'hour'],
                'huashen_on_month_qi': False, 'huashen_wuxing': '土'}
_DEBATE = {'primary_bing': {'bing_wx': '土', 'bing_id': 'test'}}


def _facts(pillars, he_pairs):
  return {'day_stem': pillars['day'][0], 'pillars': pillars,
          'tian_he': {'he_pairs': he_pairs}}


def test_same_char_stem_at_other_pillar_not_blocked():
  # 年甲在合对柱位（year）-> 记合绊；月甲不在该合对柱位 -> 不记（旧码会错记）。
  result = resolve_yongyao(_facts(_SHUANG_JIA, [_PAIR_JIA_JI]), dict(_DEBATE))
  blocked = result['medicine_blocked']
  got = [(b['gan'], b['pos']) for b in blocked if b['wuxing'] == '木']
  assert got == [('甲', 'year')], '柱位归属错误: %r' % (got,)


def test_blocked_evidence_attributes_participating_pair():
  result = resolve_yongyao(_facts(_SHUANG_JIA, [_PAIR_JIA_JI]), dict(_DEBATE))
  blocked = [b for b in result['medicine_blocked'] if b['wuxing'] == '木']
  assert len(blocked) == 1
  entry = blocked[0]
  assert entry['gan'] == '甲'
  assert entry['pos'] == 'year'
  assert entry['with'] == '己'
  assert entry['state'] == '合绊(合而不化)'


def test_pairs_without_pillars_do_not_block():
  # 旧格式 pairs（无 'pillars' 键）: 无法核对柱位 -> 不阻挡任何药（fail-open 登记）。
  pair = {'stems': ['甲', '己'], 'huashen_on_month_qi': False, 'huashen_wuxing': '土'}
  result = resolve_yongyao(_facts(_SHUANG_JIA, [pair]), dict(_DEBATE))
  assert result['medicine_blocked'] == [], \
      '缺柱位数据的 pairs 不应产生合绊记录: %r' % (result['medicine_blocked'],)


def test_real_chart_blocked_positions_inside_pair_pillars():
  # 真盘不变式：任何 blocked.pos 必须落在该盘 he_pairs pillars 并集内，
  # 且真实生产 pairs 恒带 'pillars'（daymaster_tian_he.py:89）。
  charts = [
    {'year': ['甲', '寅'], 'month': ['甲', '申'], 'day': ['庚', '午'], 'hour': ['己', '卯']},
    {'year': ['甲', '午'], 'month': ['乙', '亥'], 'day': ['甲', '申'], 'hour': ['己', '巳']},
    {'year': ['癸', '酉'], 'month': ['癸', '亥'], 'day': ['戊', '子'], 'hour': ['丁', '巳']},
  ]
  for pillars in charts:
    r = production_entry(FrozenCanonicalBaziChart(pillars=pillars))
    th = (r['engine_result'].get('tian_he') or {})
    pairs = th.get('he_pairs', [])
    assert pairs, '真盘应产出天干五合对: %r' % (pillars,)
    for p in pairs:
      assert isinstance(p.get('pillars'), list) and p['pillars'], \
          '生产 pairs 缺柱位: %r' % (p,)
    union = set()
    for p in pairs:
      union.update(p['pillars'])
    blocked = (r['zhenglun'].get('yongyao') or {}).get('medicine_blocked') or []
    for b in blocked:
      assert b.get('pos') in union, \
          'blocked 柱位 %r 落在合对柱位并集 %r 之外: %r' % (b.get('pos'), union, b)
