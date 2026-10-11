# -*- coding: utf-8 -*-
"""反局层 (fan_ju) —— DTS 准神《反局》章四句

准神来源: DTS 京图撰刘基原注 L442-L451「### 十七、反局」
切片来源: STATE.WANG_SHUAI.FAN_JU.001~004 (文库已建, 已校验)

四句互为镜像, 全部整数/枚举判据, 无浮点:
  君赖臣生  日主(君)被克极弱将亡, 克我之神(臣)反以救君为生 -> 药=臣
  儿能救母  生我之神(母)被克者所伤, 我生者(儿)克伤母者以救母 -> 药=儿
  母慈灭子  生我之神(母)太旺, 反使我(子)炽盛焚灭 -> 母旺为病非药
  夫健怕妻  日主(夫/主)虽旺, 妻(生克我之神)能生克我者反制我

触发为布尔: 成局 / 不成局。不引入程度, 不改 L3 既有字段。

★ 交叉引用(2026-10-03, 已知风险, 本轮只记录不统一):
  本模块 _you_qi 与 yongshen_engine.py:643 的 `_cai_youqi_b6`
  (`to_root_grade(ben(cai)) in [禄刃,长生,库] or stem(cai)>=1`) 同判「财有气」,
  但口径不同 —— 本模块多了「根有效性层」(B1~B6: 合绊即失效/冲只损本气/中余气看生助),
  引擎 643 无此层。当 ben>=1 且该根被六合/三合/半合绊住时,
  FAN_JU 判无气、引擎 643 判有气, 结论相反。
  全仓共有六处「有气/无气」定义(本模块 / dts_yuanliu:19 / yongshen_engine:643,717 /
  yongshen_geju:331 / strength_pipeline:100), 互不引用, 六套口径。
  本模块为 FAN_JU 私有口径, 改它波及面为零; 六定义统一是独立工程
  (一合并 643+717 / 两改名 语义隔离 / 一对齐 dts_yuanliu), 不搭车本轮。
"""
from typing import Any, Dict, List

GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}   # 我生 = 食伤 = 儿
SHENG_BACK = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}  # 生我 = 印 = 母
KE_BACK = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}   # 克我 = 官杀
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}      # 我克 = 财 = 妻

FAN_JU_TYPES = {
    'JUN_LAI_CHEN_SHENG': '君赖臣生',
    'ER_NENG_JIU_MU': '儿能救母',
    'MU_CI_MIE_ZI': '母慈灭子',
    'FU_JIAN_PA_QI': '夫健怕妻',
}

# ===== 实变量定义(依 DTS/PZZQ 原文, 全整数/枚举, 无浮点) =====
# ★ B6(核心语义, 锁死): 合绊本气根 / 冲损本气; 中气·余气根【两者都不损】, 只看是否得生助。
#   B1 合 = 六合(liuhe) + 三合(sanhe) + 半合(banhe), 暗合不算 —— 明合有绊力, 暗合无。
#   B2 合绊【即失效】, 不要求合化成 —— PZ-0194 巳申合未化仍判无财(徐注「四柱无财以破印」)。
#   B3 冲【只损被冲支的本气】, 不损中气/余气 —— DT-0365 巳亥冲, 亥水本气被冲,
#      而财根是亥中甲木(中气), 未损, 故木根有效。
#   B4 只算【相邻支】(年月日/月日/日时), 隔位不算 —— 否则全盘互生, 判定失控。
#   B5 传导链【两跳且写死路径, 不递归】: 邻支 → 生本支 / 本支 → 生根,
#      即「邻支生本支, 本支生藏干根」。DT-0365 即「酉金生亥水, 亥水生甲木」。
_BZ_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
          '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
          '戌': '土', '亥': '水'}
# 藏干成分(成分表, 不含次序; 力量级别由 wuxing_power 的 ben/zhong/yu 给出)
_CANG = {'子': ['癸'], '丑': ['己', '辛', '癸'], '寅': ['甲', '丙', '戊'],
        '卯': ['乙'], '辰': ['戊', '乙', '癸'], '巳': ['丙', '戊', '庚'],
        '午': ['丁', '己'], '未': ['己', '丁', '乙'], '申': ['庚', '壬', '戊'],
        '酉': ['辛'], '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲']}
_POS = ('year', 'month', 'day', 'hour')


def _row(facts: Dict[str, Any], wx: str) -> Dict[str, Any]:
    wp = (facts.get('wuxing_power') or {}).get('wuxing_power') or {}
    return dict(wp.get(wx) or {})


def _mass(facts: Dict[str, Any], wx: str) -> int:
    """离散力量 = 本气+中气+余气+透干(全整数, 无浮点)"""
    if not wx:
        return 0
    r = _row(facts, wx)
    return (int(r.get('ben_n', 0) or 0) + int(r.get('zhong_n', 0) or 0)
            + int(r.get('yu_n', 0) or 0) + int(r.get('stem_n', 0) or 0))


def _is_wang(facts: Dict[str, Any], wx: str) -> bool:
    """旺: ling_state ∈ {旺, 相}。DTS L357「伤重印轻身弱」等全用相对旺衰, 非绝对阈值。"""
    return str(_row(facts, wx).get('ling_state') or '') in ('旺', '相')


def _cheng_dang(facts: Dict[str, Any], wx: str) -> bool:
    """成党: 离散力量 >= 4 (工程整数档, 非原典明文, 标 source)"""
    return _mass(facts, wx) >= 4


def _zhi_list(facts: Dict[str, Any]) -> list:
    """四支按 年月日时 顺序"""
    pl = facts.get('pillars') or {}
    return [(pl.get(_p) or [None, None])[1] for _p in _POS]


def _he_pairs(facts: Dict[str, Any]) -> set:
    """B1: 六合 + 三合 + 半合, 暗合不算。返回 无序对 的 frozenset 集合。"""
    cmb = facts.get('combination_facts') or {}
    out = set()
    for key in ('liuhe', 'sanhe'):
        for pair in (cmb.get(key) or []):
            try:
                out.add(frozenset((pair[0], pair[1])))
            except Exception:
                pass
    for d in (cmb.get('banhe') or []):
        pr = (d or {}).get('pair')
        if pr and len(pr) >= 2:
            out.add(frozenset((pr[0], pr[1])))
    return out


def _chong_pairs(facts: Dict[str, Any]) -> set:
    cmb = facts.get('combination_facts') or {}
    out = set()
    for pair in (cmb.get('liuchong') or []):
        try:
            out.add(frozenset((pair[0], pair[1])))
        except Exception:
            pass
    return out


def _he_ban(facts: Dict[str, Any], zhi: str) -> bool:
    """B2: 该支是否被六合/三合/半合「绊住」—— 合绊即失效, 不要求合化。"""
    return any(zhi in pr for pr in _he_pairs(facts))


def _chong_ben(facts: Dict[str, Any], zhi: str) -> bool:
    """B3: 该支【本气】是否被六冲—— 只损本气, 不损中气/余气。"""
    return any(zhi in pr for pr in _chong_pairs(facts))


def _neighbors(zhis: list, i: int) -> list:
    """B4: 只算相邻支(年月/月日/日时), 隔位不算"""
    return [zhis[j] for j in (i - 1, i + 1) if 0 <= j < len(zhis)]


def _roots_in(facts: Dict[str, Any], wx: str):
    """列出含 wx 藏干的 (支, 级别) —— 级别由 root_detail 的 BEN/ZHONG/YU 判定。"""
    zhis = _zhi_list(facts)
    out = []
    for i, z in enumerate(zhis):
        if not z:
            continue
        rd = (_row(facts, wx).get('root_detail') or {})
        lv = rd.get(z)
        if lv in ('BEN', 'ZHONG', 'YU'):
            out.append((i, z, lv))
    return out


def _root_supported(facts: Dict[str, Any], zhis: list, i: int, wx: str) -> bool:
    """B5: 该中气/余气根是否得生助 —— 允许两跳且写死路径(不递归):
       邻支 生 本支(B4相邻)  或  本支 生 该藏干根。"""
    z = zhis[i]
    for nz in _neighbors(zhis, i):
        if SHENG.get(_BZ_WX.get(nz, '')) == _BZ_WX.get(z, ''):   # 邻支生本支
            return True
        if SHENG.get(_BZ_WX.get(z, '')) == wx:                    # 本支生该根
            return True
    return False


def _you_qi(facts: Dict[str, Any], wx: str) -> bool:
    """有气(B1~B6 锁死; 见文件上方边界定义):
       ① 透干即有气            stem_n >= 1
       ② 本气根【未被合绊、未被六冲】即有气
       ③ 中气/余气根【不被合绊冲损】, 但得邻支/本支生助即有气
       全不满足 -> 无气
    ★ 本定义是 FAN_JU 私有口径, 不与其他层的「有气」共享(见 yongshen_engine:643
      的同名变量, 语义相近口径不同, 已知风险, 本轮只记录不统一)。"""
    r = _row(facts, wx)
    if not wx:
        return False
    if int(r.get('stem_n', 0) or 0) >= 1:                      # ① 透干即有气
        return True
    zhis = _zhi_list(facts)
    for i, z, lv in _roots_in(facts, wx):
        if _he_ban(facts, z):                                 # B1+B2 合绊即失效
            continue
        if lv == 'BEN':                                       # ② 本气根
            if not _chong_ben(facts, z):                      # B3 冲只损本气
                return True
        else:                                                 # ③ 中气/余气根
            # B6 中/余气不被合冲直接损, 只看生助; B5 两跳写死不递归
            if _root_supported(facts, zhis, i, wx):
                return True
    return False


def _wu_qi(facts: Dict[str, Any], wx: str) -> bool:
    """无气 = NOT 有气"""
    return not _you_qi(facts, wx)


# -*- coding: utf-8 -*-
"""反局层 (fan_ju) —— DTS 准神《反局》章四句

准神来源: DTS 京图撰刘基原注 L442-L451「### 十七、反局」
切片来源: STATE.WANG_SHUAI.FAN_JU.001~004 (文库已建, 已校验)

四句互为镜像, 全部整数/枚举判据, 无浮点:
  君赖臣生  日主(君)被克极弱将亡, 克我之神(臣)反以救君为生 -> 药=臣
  儿能救母  生我之神(母)被克者所伤, 我生者(儿)克伤母者以救母 -> 药=儿
  母慈灭子  生我之神(母)太旺, 反使我(子)炽盛焚灭 -> 母旺为病非药
  夫健怕妻  日主(夫/主)虽旺, 妻(生克我之神)能生克我者反制我

触发为布尔: 成局 / 不成局。不引入程度, 不改 L3 既有字段。

★ 交叉引用(2026-10-03, 已知风险, 本轮只记录不统一):
  本模块 _you_qi 与 yongshen_engine.py:643 的 `_cai_youqi_b6`
  (`to_root_grade(ben(cai)) in [禄刃,长生,库] or stem(cai)>=1`) 同判「财有气」,
  但口径不同 —— 本模块多了「根有效性层」(B1~B6: 合绊即失效/冲只损本气/中余气看生助),
  引擎 643 无此层。当 ben>=1 且该根被六合/三合/半合绊住时,
  FAN_JU 判无气、引擎 643 判有气, 结论相反。
  全仓共有六处「有气/无气」定义(本模块 / dts_yuanliu:19 / yongshen_engine:643,717 /
  yongshen_geju:331 / strength_pipeline:100), 互不引用, 六套口径。
  本模块为 FAN_JU 私有口径, 改它波及面为零; 六定义统一是独立工程
  (一合并 643+717 / 两改名 语义隔离 / 一对齐 dts_yuanliu), 不搭车本轮。
"""
from typing import Any, Dict, List

GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}   # 我生
SHENG_BACK = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}  # 生我
KE_BACK = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}   # 克我
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}      # 我克 = 财 = 妻

FAN_JU_TYPES = {
    'JUN_LAI_CHEN_SHENG': '君赖臣生',
    'ER_NENG_JIU_MU': '儿能救母',
    'MU_CI_MIE_ZI': '母慈灭子',
    'FU_JIAN_PA_QI': '夫健怕妻',
}


def _mass(facts: Dict[str, Any], wx: str) -> int:
    """某五行的离散力量: 本气+中气+余气+透干(全整数)"""
    if not wx:
        return 0
    wp = (facts.get('wuxing_power') or {}).get('wuxing_power') or {}
    row = wp.get(wx) or {}
    return (int(row.get('ben_n', 0) or 0) + int(row.get('zhong_n', 0) or 0)
            + int(row.get('yu_n', 0) or 0) + int(row.get('stem_n', 0) or 0))


def _ling(facts: Dict[str, Any], wx: str) -> str:
    wp = (facts.get('wuxing_power') or {}).get('wuxing_power') or {}
    return str((wp.get(wx) or {}).get('ling_state') or '')


_BZ_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
          '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
          '戌': '土', '亥': '水'}


def _chong_hit(facts: Dict[str, Any], wx: str) -> bool:
    """日主五行所在之支是否被六冲(被冲则根拔/气伤)"""
    cmb = facts.get('combination_facts') or {}
    lc = cmb.get('liuchong') or []
    for pair in lc:
        try:
            a, b = pair[0], pair[1]
        except Exception:
            continue
        # 直接查该支本气五行
        if _BZ_WX.get(a) == wx or _BZ_WX.get(b) == wx:
            return True
    return False


def _row(facts: Dict[str, Any], wx: str) -> Dict[str, Any]:
    wp = (facts.get('wuxing_power') or {}).get('wuxing_power') or {}
    return dict(wp.get(wx) or {})


def _mass(facts: Dict[str, Any], wx: str) -> int:
    """离散力量 = 本气+中气+余气+透干(全整数, 无浮点)"""
    if not wx:
        return 0
    r = _row(facts, wx)
    return (int(r.get('ben_n', 0) or 0) + int(r.get('zhong_n', 0) or 0)
            + int(r.get('yu_n', 0) or 0) + int(r.get('stem_n', 0) or 0))


# ===== 实变量定义(依 DTS/PZZQ 原文, 全整数/枚举, 无浮点) =====
# 「旺」: 旺相二态。 DTS L357「伤重印轻身弱」等全用相对旺衰, 非绝对阈值。
# 「有气」: 命理术语 = 得令或得地/透干, 非数量。 任氏「柱中财星有气」即此。
# 「成党」: 党众成势(工程整数档, 非原典明文, 标 source)。
def _is_wang(facts: Dict[str, Any], wx: str) -> bool:
    """旺: ling_state ∈ {旺, 相}"""
    return str(_row(facts, wx).get('ling_state') or '') in ('旺', '相')


def _you_qi(facts: Dict[str, Any], wx: str) -> bool:
    """有气: 透干 或 有本气根(得地)。无透干且无本气根 = 无气。"""
    r = _row(facts, wx)
    return int(r.get('stem_n', 0) or 0) >= 1 or int(r.get('ben_n', 0) or 0) >= 1


def _wu_qi(facts: Dict[str, Any], wx: str) -> bool:
    """无气: 无透干 且 无本气根"""
    return not _you_qi(facts, wx)


def _cheng_dang(facts: Dict[str, Any], wx: str) -> bool:
    """成党: 离散力量 >= 4 (工程整数档, 非原典明文)"""
    return _mass(facts, wx) >= 4


def _chong_hit(facts: Dict[str, Any], wx: str) -> bool:
    """日主五行所在之支是否被六冲"""
    cmb = facts.get('combination_facts') or {}
    for pair in (cmb.get('liuchong') or []):
        try:
            a, b = pair[0], pair[1]
        except Exception:
            continue
        if _BZ_WX.get(a) == wx or _BZ_WX.get(b) == wx:
            return True
    return False


def resolve_fan_ju(facts: Dict[str, Any]) -> Dict[str, Any]:
    """判反局四句。DTS 准神 L442-L451 + 任氏「印旺/财星有气」分野 + PZZQ L3574-3577。
    判据方向按原典五行生克链, 非「强弱对比」(2026-10-03 两轮方向错误已纠正)。
    全部整数/枚举, 无浮点; 触发为布尔, 不判程度。"""
    dm = facts.get('day_stem', '')
    dwx = GAN_WX.get(dm, '')
    if not dwx:
        return {'layer': 'FAN_JU', 'state': 'NO_DAYMASTER', 'types': [],
                'types_by_id': {}, 'detail': [], 'count': 0,
                'rule': '日主缺失, 不判反局', 'evidence_refs': []}

    yin = SHENG_BACK.get(dwx, '')    # 生我 = 印 = 母
    zi = SHENG.get(dwx, '')          # 我生 = 食伤 = 儿
    chen = KE_BACK.get(dwx, '')      # 克我 = 官杀 = 伤母者
    cai = KE.get(dwx, '')            # 我克 = 财 = 妻

    m_dm = _mass(facts, dwx)
    m_yin = _mass(facts, yin)
    m_zi = _mass(facts, zi)
    m_chen = _mass(facts, chen)
    m_cai = _mass(facts, cai)

    yin_wang = _is_wang(facts, yin)
    yin_dang = _cheng_dang(facts, yin)
    cai_youqi = _you_qi(facts, cai)
    chen_wang = _is_wang(facts, chen)
    chen_dang = _cheng_dang(facts, chen)

    out: List[Dict[str, Any]] = []

    # ---- ① 君赖臣生 DTS L445 + 任氏: 印旺 + 财有气 -> 用财破印 ----
    if (yin_wang or yin_dang) and cai_youqi:
        out.append({
            'fan_ju_id': 'JUN_LAI_CHEN_SHENG', 'name': FAN_JU_TYPES['JUN_LAI_CHEN_SHENG'],
            'role': '君(日主)=%s / 臣(生我之神·印)=%s' % (dwx, yin),
            'disease_wx': yin, 'yao_wx': cai,
            'logic': ('印(%s)%s + 财(%s)有气(透干或有本气根) -> 药=财, 破印救君'
                      % (yin, '当令旺相' if yin_wang else '成党(工程档>=4)', cai)),
            'slice_id': 'STATE.WANG_SHUAI.FAN_JU.001',
            'classic_line': 'DTS L445「水泛木浮, 土止水则生木……皆君赖臣生也」; 任氏「君赖臣生, 局中印绶虽旺, 柱中财星有气, 可用财破印也」',
        })

    # ---- ② 母慈灭子 DTS L449 + 任氏: 印旺 + 财无气 -> 顺母之性, 不可财破印 ----
    if (yin_wang or yin_dang) and _wu_qi(facts, cai):
        out.append({
            'fan_ju_id': 'MU_CI_MIE_ZI', 'name': FAN_JU_TYPES['MU_CI_MIE_ZI'],
            'role': '慈母(生我之神·印)=%s / 子(日主)=%s' % (yin, dwx),
            'disease_wx': yin, 'yao_wx': '',
            'logic': ('印(%s)%s + 财(%s)无气(无透干且无本气根) -> 不得用财破印, '
                      '只得顺母之性, 助其子(日主%s)'
                      % (yin, '当令旺相' if yin_wang else '成党(工程档>=4)', cai, dwx)),
            'slice_id': 'STATE.WANG_SHUAI.FAN_JU.003',
            'classic_line': 'DTS L449「木母也, 火子也, 太旺谓之慈母, 反使火炽百焚灭, 是谓灭子」; 任氏「母慈灭子, 纵有财星无气, 未可以财星破印也」',
        })

    # ---- ③ 儿能救母 DTS L447 链式: 伤母者(官杀)有气 + 儿(食伤)能克之 ----
    chen_youqi = _you_qi(facts, chen)
    if chen_youqi and m_zi >= 1:
        out.append({
            'fan_ju_id': 'ER_NENG_JIU_MU', 'name': FAN_JU_TYPES['ER_NENG_JIU_MU'],
            'role': '母(日主)=%s / 伤母者(克我之神)=%s / 儿(我生之神)=%s' % (dwx, chen, zi),
            'disease_wx': chen, 'yao_wx': zi,
            'logic': ('伤母者(%s)%s, 儿(%s)克之 -> 母(%s)得救'
                      % (chen, '有气(透干或根未被合冲)', zi, dwx)),
            'slice_id': 'STATE.WANG_SHUAI.FAN_JU.002',
            'classic_line': 'DTS L447「木被金伤, 火克金则生木; 火遭水克, 土克水则生火……皆儿能生母之意」',
        })

    # ---- ④ 夫健怕妻 DTS L451 + DT-0375: 妻(我克)旺而生我克者 -> 反制我 ----
    if m_cai >= 5 and m_dm >= 3:
        out.append({
            'fan_ju_id': 'FU_JIAN_PA_QI', 'name': FAN_JU_TYPES['FU_JIAN_PA_QI'],
            'role': '夫(日主)=%s / 妻(我克之神)=%s' % (dwx, cai),
            'disease_wx': dwx, 'yao_wx': chen,
            'logic': ('妻(财,%s)成党(力量%d>=5), 生我克者(%s)而反制夫(日主%s, 力量%d>=3)'
                      % (cai, m_cai, chen, dwx, m_dm)),
            'slice_id': 'STATE.WANG_SHUAI.FAN_JU.004',
            'classic_line': 'DTS L451「木是夫也, 土是妻也。木虽旺, 土能生金而克木, 是谓夫健而怕妻」; DT-0375「四柱土多, 时透辛金, 土生金, 金克木, 谓夫健怕妻」',
        })

    return {
        'layer': 'FAN_JU',
        'state': 'FAN_JU_RESOLVED' if out else 'NO_FAN_JU',
        'types': [o['fan_ju_id'] for o in out],
        'types_by_id': {o['fan_ju_id']: o for o in out},
        'detail': out,
        'count': len(out),
        'role_map': {'君/夫(日主)': dwx, '母/妻(印·生我)': yin,
                     '儿(食伤·我生)': zi, '臣/伤母者(官杀·克我)': chen, '妻(财·我克)': cai},
        'power_map': {dwx: m_dm, yin: m_yin, zi: m_zi, chen: m_chen, cai: m_cai},
        'flag_map': {
            'yin_wang': yin_wang, 'yin_chengdang': yin_dang,
            'cai_youqi': cai_youqi, 'cai_wuqi': _wu_qi(facts, cai),
            'chen_wang': chen_wang, 'chen_chengdang': chen_dang,
            'chen_youqi': chen_youqi,
        },
        'dm_chong': _chong_hit(facts, dwx),
        'rule': ('DTS 反局章 L442-L451 四句(君赖臣生/儿能救母/母慈灭子/夫健怕妻), '
                 '互为镜像; 判据按原典五行生克链, 非强弱对比; '
                 '「旺」=ling_state∈(旺,相)「有气」=B1~B6(透干/本气根未被合冲/中余气根得生助) '
                 '「成党」=mass>=4(工程档); '
                 '全整数/枚举, 无浮点; 触发为布尔, 不判程度'),
        'boundary_note': ('反局是旺衰层结构判断(DTS「### 十七、反局」), 不是格名也不是病名; '
                          '本模块只判是否成局, 不改 L3 既有字段, 不出强/弱单极结论; '
                          '阈值「成党>=4」为工程整数档, 非原典明文。'),
        'evidence_refs': ['DTS L442 反局章标题', 'DTS L445 君赖臣生',
                          'DTS L447 儿能救母', 'DTS L449 母慈灭子', 'DTS L451 夫健怕妻',
                          'PZZQ L3574-3577 身印三元', '任氏 印旺/财星有气分野'],
    }


if __name__ == '__main__':
    print('FAN_JU 模块加载正常, 判据全整数/枚举, 无浮点')
    print('  四句: %s' % list(FAN_JU_TYPES.values()))
