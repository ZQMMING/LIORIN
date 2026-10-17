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


def _yongshen_routing(facts: Dict[str, Any], climate: Dict[str, Any]) -> Dict[str, Any]:
    """★ 第4层程级(喜用神路由)·A′ 消解 (User 裁定 2026-10-16):
    准神 DTS 有两处明文程级 —— ①硬情形优先(L295-298「寒之甚/过于燥皆偏枯, 必无好处」)
    ②病药优先(L240「有病方为贵, 无伤不是奇」)。消解序:
      1. 硬情形(从格/寒燥极)命中 → 该路优先, DTS_CITED
      2. 多路有病(P1 bing severity>=3) → 哪路判病那路优先, 取克泄病之药, DTS_CITED
      3. 无病 → 各路并行不压序(架构§2.8.2 五域并行), 扶抑 primary 为准
    依据级: 明文→DTS_CITED(不标 PENDING); 推的→ENGINE_DEFINED."""
    sv = (facts.get("l3_contract") or {}).get("strength_verdict") or {}
    dirn = sv.get("value") or []
    cong = (facts.get("special") or {}).get("cong_type")
    yl = _yuanliu_yongshen(facts)
    th = _tiaohou_yongshen(facts, climate)
    # P1 病药 severity(病五行->0-4序数), 供病药优先判定
    p1 = facts.get("p1_bing") or {}
    bings = p1.get("bing_list") or []
    def _sev(bx):
        return max((int((x.get("severity") or 0)) for x in bings if (x.get("bing_wx") == bx)), default=0)
    # 克/泄 病五行之神(药): 克病(泄病气)优先, 再泄病
    _ke_wx = {"木": "金", "火": "水", "土": "水", "金": "火", "水": "土"}
    _sheng_wx = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

    routes = []
    # ── 1. 硬情形层 (DTS L420 从格 / L298 寒燥极) → 优先 DTS_CITED ──
    hard_winner = None
    if cong:
        hard_winner = {"route": "从格", "shen": None,
                       "basis": "DTS L420「既从矣当论所从之神, 从财只以财为主」",
                       "note": "喜用=所从之神(由L4格判)"}
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
    _th_bias = ("调候" in dirn) and th.get("enabled") and (_hou_wx != "") and (_hou_mass < _max_mass)
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
        _yao = _ke_wx.get(_bx, "") or _sheng_wx.get(_bx, "")
        bing_winner = {"route": "病药", "shen": _yao,
                       "bing": _bx, "bing_sev": int(_main.get("severity") or 0),
                       "basis": "DTS L240「有病方为贵, 无伤不是奇」; 克泄病之为药",
                       "note": "病=%s(sev%s), 药=%s" % (_bx, _main.get("severity"), _yao)}
        routes.append(bing_winner)
    # ── 3. 普通层: 各路并列候选(不压序) ──
    if yl.get("enabled"):
        routes.append({"route": "源流", "shen": yl.get("hui_lu"), "status": "ENGINE_DEFINED",
                       "basis": "DTS L245 源流(并列取用)", "note": "源流归路"})
    if "通关" in dirn:
        routes.append({"route": "通关", "shen": None, "status": "ENGINE_DEFINED",
                       "basis": "DTS L250 两神相战需通", "note": "通关神"})
    for _d in ("帮身", "泄伤"):
        if _d in dirn:
            routes.append({"route": _d, "shen": None, "status": "ENGINE_DEFINED",
                           "basis": "DTS L215 体用 + L230/L235", "note": "扶抑路, primary 已算"})
            break
    # 给每条 route 标 status(病药/硬情形= DTS_CITED, 其余默认)
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
    return {"routes": routes,
            "winner_route": winner_route,
            "winner_shen": winner_shen,
            "winner_basis": _basis,
            "route_count": len(routes),
            "pending_count": 0,
            "basis": "第4层程级·A′: 硬情形(L420/L298)→病药(L240)→并行; 依据级 DTS_CITED"}


def resolve_yongyao(facts: Dict[str, Any], debate: Dict[str, Any],
                    climate: Dict[str, Any] = None) -> Dict[str, Any]:
    primary = debate.get('primary_bing') or {}
    _yl = _yuanliu_yongshen(facts)   # ★ 第2层 源流(不动 primary)
    _th = _tiaohou_yongshen(facts, climate)   # ★ 第3层 调候(不动 primary)
    _rt = _yongshen_routing(facts, climate)   # ★ 第4层 程级路由(该盘适用哪路)
    bw = primary.get('bing_wx', '')
    bid = primary.get('bing_id', '')
    _sec_wx = {s2.get('bing_wx') for s2 in (debate.get('secondary_bing') or []) if s2.get('bing_wx')}
    dm = GAN_WX.get(facts.get('day_stem', ''), '')
    _pl = facts.get('pillars')
    dm_ben = sum(1 for pos in ('year', 'month', 'day', 'hour')
                 if _pl and ZHI_BEN_WX.get(_pl[pos][1]) == dm) if _pl else 0

    rejected_climate = []
    if climate:
        for c in climate.get('climate_candidates', []):
            stem = c.get('stem', '')
            cwx = GAN_WX.get(stem, '')
            reason = None
            if cwx == bw:
                reason = '与主病同五行(%s), 用之添病' % bw
            elif SHENG_BACK.get(bw) == cwx:
                reason = '%s生%s(病), 为病之源' % (cwx, bw)
            if reason:
                rejected_climate.append({'stem': stem, 'wuxing': cwx, 'reason': reason})

    if not bw:
        # [2026-10-08 PATCH-GE2YO] 源1(病药主病)空 → fallback 源2(格体喜神 xi_wx) + 源3(格局所需神)
        #   架构 §2.9: 用神层 = 五域药方 + L4 格体喜神 取用神。
        #   源1 空(病0→无主病)时, 走 ge_cheng.xi_wx(格成喜神) / ge_cheng.zhi_wx(格破救应神)。
        #   [2026-10-08 PATCH-SRC4] 源4: 破格盘 xi_wx 被清空, 改读 jiu_ying.rescue_wx(破格救应药)
        #   + ge_cheng.hua_wx(专旺化神)。不替代源1, 仅在源1 无产出时补, 防"无主病→用神全空"静默丢。
        _gc = facts.get('ge_cheng') or {}
        _xi = _gc.get('xi_wx') or []
        _zhi = _gc.get('zhi_wx') or []
        _hua = _gc.get('hua_wx') or []
        _jy = facts.get('jiu_ying') or {}
        _rescue = _jy.get('rescue_wx') or []
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
        if _w:
            return {'layer': 'YONGYAO_RESOLVE', 'state': 'GE_FALLBACK',
                    'primary_medicine': {'wuxing': _w, 'gan': list(WX_GAN.get(_w, ())),
                                          'function': _source, 'kind': '格体喜神/救应神',
                                          'classic': '架构§2.9 用神层=L4格体喜神+P1格局病域救应',
                                          'blocked': None},
                    'auxiliary_medicine': [],
                    'ji_shen': [bm for bm in (_gc.get('ti_wx') or []) if bm != _w],
                    'rejected_climate': rejected_climate,
                    'ge_fallback_source': _source,
                    'yuanliu_yongshen': _yl,   # ★ 第2层 源流(不动 primary)
                    'tiaohou_yongshen': _th,   # ★ 第3层 调候(不动 primary)
                    'routing': _rt,   # ★ 第4层 程级路由
                    'boundary_note': '源1无主病, 走格体喜神/救应神 fallback(架构§2.9 五源)'
                    }
        # ★ 源5: 无病无格 → 按 L3 方向出旺衰喜用神(DTS L215 体用 + L235 衰帮旺泄)
        #   帮身→喜印(生我)/比; 泄伤→喜食伤(我生)/财。防"无主病无格→用神全空"静默丢
        _dirn5 = ((facts.get('l3_contract') or {}).get('strength_verdict') or {}).get('value') or []
        _dmwx5 = facts.get('daymaster_element') or dm
        _w5 = SHENG_BACK.get(_dmwx5, '') if '帮身' in _dirn5 else (SHENG.get(_dmwx5, '') if '泄伤' in _dirn5 else '')
        if _w5:
            _aux5 = [_dmwx5] if '帮身' in _dirn5 else ([KE.get(_dmwx5, '')] if KE.get(_dmwx5, '') else [])
            return {'layer': 'YONGYAO_RESOLVE', 'state': 'GE_FALLBACK',
                    'primary_medicine': {'wuxing': _w5, 'gan': list(WX_GAN.get(_w5, ())),
                                          'function': '源5:旺衰喜用神', 'kind': '旺衰喜用神',
                                          'classic': 'DTS L215 体用 + L235 衰喜帮/旺宜泄', 'blocked': None},
                    'auxiliary_medicine': [{'wuxing': a, 'gan': list(WX_GAN.get(a, ()))} for a in _aux5],
                    'ji_shen': [], 'rejected_climate': rejected_climate,
                    'ge_fallback_source': '源5:旺衰喜用神(无病无格, DTS L215)',
                    'yuanliu_yongshen': _yl, 'tiaohou_yongshen': _th, 'routing': _rt,
                    'boundary_note': '源1无主病+无格, 走源5旺衰喜用神(帮身喜印/泄伤喜食伤, DTS L215)'}
        return {'layer': 'YONGYAO_RESOLVE', 'state': 'NO_BING',
                'primary_medicine': None, 'auxiliary_medicine': [],
                'ji_shen': [], 'rejected_climate': rejected_climate,
                'yuanliu_yongshen': _yl,   # ★ 第2层 源流(不动 primary)
                'tiaohou_yongshen': _th,   # ★ 第3层 调候(不动 primary)
                'routing': _rt,   # ★ 第4层 程级路由
                'boundary_note': '无主病且无格体喜神/救应神, 不裁决用药'}

    edges = []   # 每条: 五行/gan/边类型/功能/是否采纳/剔除理由

    def add(wx, kind, func):
        gan = list(WX_GAN.get(wx, ()))
        ok = _safe(wx, bw)
        note = ''
        if not ok:
            note = '帮病(同病或生病), 剔除'
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
        edges.append({'wuxing': wx, 'gan': gan, 'kind': kind,
                      'function': func, 'accepted': ok, 'reject_reason': note})

    # 制
    add(KE_BACK.get(bw, ''), '制', '克病(%s)' % bw)
    # 化 (病所生, 泄病)
    add(SHENG.get(bw, ''), '化', '泄病之气(%s生? )' % bw)
    # 帮 (比劫 + 印)
    add(dm, '帮', '比劫帮身')
    add(SHENG_BACK.get(dm, ''), '帮', '印生身')
    # 水泛木浮特殊: 火暖化
    if bw == '水':
        add('火', '暖', '丙丁暖化寒湿')

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
                if g in pair['stems']:
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
    if zhu is None and uniq:
        zhu = uniq[0]
    fu = [e for e in uniq if e is not zhu]

    ji = [bw]
    sb = SHENG_BACK.get(bw, '')
    if sb:
        ji.append(sb)

    primary_medicine = None
    if zhu:
        _zb = [b for b in medicine_blocked if b['wuxing'] == zhu['wuxing']
               and b['state'].startswith('合绊')]
        primary_medicine = {'wuxing': zhu['wuxing'], 'gan': zhu['gan'],
                            'function': zhu['function'], 'kind': '制',
                            'classic': '五行相克为基础关系; DTS FAN_JU.001',
                            'blocked': _zb[0] if _zb else None}
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
        'rejected_climate': rejected_climate,
        'rule': '制=克病; 化=泄病(克身则剔); 帮=比劫印帮身(是病则剔); 水泛加火暖',
        'boundary_note': '离散三边全列按主辅; 只裁用药方向不判吉凶; 化/帮为原典通例, 须看命局分寸',
        'evidence_refs': ['DTS PATHOLOGY_QI_HOU.008', 'DTS FAN_JU.001'],
        'yuanliu_yongshen': _yl,   # ★ 第2层 源流(不动 primary)
        'tiaohou_yongshen': _th,   # ★ 第3层 调候(不动 primary)
        'routing': _rt,   # ★ 第4层 程级路由
    }
