# -*- coding: utf-8 -*-
"""病药/作用子层 (bingyao_layer)
命局病机药神枚举 + 应期去病添病.
只输出结构事实, 不判吉凶/成败/轻重.
原典依据: SFTK-008-001 病藥說, SFTK-009-002 雕枯旺弱四病.

设计原则:
- 病 = 对日主或格局有害的结构因素 (只识别存在, 不判轻重)
- 药 = 可以去病的结构因素 (只识别存在, 不判有效性)
- 病药配对 = 原典明确的对应关系 (不自行综合)
- 矛盾共存不裁, 多病多药并列保留
- 不判吉凶/成败/用神/身强弱
"""
from typing import Any, Dict, List, Optional
from spec.yinyang_system import SHENG, KE, SHENG_ME, KE_ME
from engines.common.severity import derive_severity  # L3 severity 序数(病机程度 0-4)


# 十神中文名称映射
TENGOD_CN = {
    'BIJIAN': '比肩', 'JIECAI': '劫财',
    'SHISHANG': '食神', 'SHANGGUAN': '伤官',
    'PIANCAI': '偏财', 'ZHENGCAI': '正财',
    'QISHA': '七杀', 'ZHENGGUAN': '正官',
    'PIANYIN': '偏印', 'ZHENGYIN': '正印',
}

# 五行生克: 日主五行→所克(财)→所生(食伤)→克我(官杀)→生我(印)

KE_WO = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}
SHENG_WO = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}

# 病类→药神五行 (单一数据源: check_qubing_level 岁运去病 + apply_yuanju_yao 原局药消病共用)
#   依据: PZZQ L957「除其病神, 即谓之药」(以抑为喜则去其抑者为病); SFTK L424 病药说
#   「用财见比肩为病喜官杀为药, 用食神伤官以印为病喜财为药」; DTS L240「格中如去病,财禄两相宜」。
BING_YAO_MAP = {
    'CAI_DUO_SHEN_RUO': ['木', '水'],  # 财多身弱, 药=印比(帮身任财)
    'SHA_ZHONG_SHEN_QING': ['火', '木', '水'],  # 煞重身轻, 药=食伤制煞/印化煞
    'XIE_QI_TAI_ZHONG': ['木', '水'],  # 泄气太重, 药=印比
    'SHANGGUAN_JIAN_GUAN': ['水', '土'],  # 伤官见官, 药=印财
    'XIAO_DUO_SHI': ['土'],  # 枭神夺食, 药=财(制枭)
    'BIJIE_DUO_CAI': ['金'],  # 比劫夺财, 药=官杀(制劫护财, SFTK「用财见比肩为病喜官杀为药」)
    'BIJIE_CHENG_DANG': ['金'],  # 比劫成党, 药=官杀
    'ZHI_SHA_TAI_GUO': [],  # 制杀太过: 按日主动态取(印=SHENG_WO, 财=KE), 见 _bing_yao_map()
}

def _bing_yao_map(daymaster_element: str) -> dict:
    """药表动态取: ZHI_SHA_TAI_GUO 按日主 印(制食护杀)/财(泄食生杀) 两路。"""
    m = dict(BING_YAO_MAP)
    if daymaster_element:
        m['ZHI_SHA_TAI_GUO'] = [SHENG_WO.get(daymaster_element, ''),
                                KE.get(daymaster_element, '')]
    return m

# 阴干在阳干当权月: 月令本气为同五行阳干(劫财), 非日主自身令(劫财当权,日主反弱).
# 证据分级(原著优先): 仅(乙,寅)有 SFTK 案例(第7812行"阳木得令阴木反弱")->CASE_LEVEL启用;
# 丁巳/辛申/癸亥 无同级古籍案例->NO_EVIDENCE, 登记不启用(宁漏勿错).
# 第0层表位/全局 wuxing_power 不动; 本表仅第1层判日主是否自己当令.
_YIN_YANG_DANGQUAN = {
    ('乙', '寅'): 'CASE_LEVEL',
    ('丁', '巳'): 'NO_EVIDENCE',
    ('辛', '申'): 'NO_EVIDENCE',
    ('癸', '亥'): 'NO_EVIDENCE',
}
_DM_LU = {'甲':'寅','丙':'巳','戊':'巳','庚':'申','壬':'亥',
          '乙':'卯','丁':'午','己':'午','辛':'酉','癸':'子'}
_DM_WANG = {'甲':'卯','丙':'午','戊':'午','庚':'酉','壬':'子',
            '乙':'寅','丁':'巳','己':'巳','辛':'申','癸':'亥'}

# 干支→五行 (统一计数)
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
ZHI_BEN_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
              '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
              '戌': '土', '亥': '水'}
# 成党离散阈值: 集中登记于工程推定区(待真实命例回归, 非原典精确数字)
from engines.common.engineering_assumptions import DANG_COMBO
# 复用辩层偏序口径(无循环导入: 辩层不导入本模块)
from engines.common.bing_debate import (
    month_order as _db_month_order, _counts as _db_counts,
    _dang_level as _db_dang_level)


# 病类型定义 (原典依据)
# 字段:
#   slice_id      主切片ID(MD文库 canonical, 已用 slice_loader 验证存在)
#   slice_support 旁参切片ID列表
#   domain        病域(五域: GEJU格局/WANGSH旺衰气势/QIHOU调候/JIEGOU结构/SUIYUN岁运)
#                 —— 与喜忌五域契约(xiji_namespace)同口径
#   slice_id=None 表示 MD 文库暂未定位对口切片, 登记 UNVERIFIED(宁缺勿错, 不脑补)
BING_TYPES = {
    'CAI_DUO_SHEN_RUO': {
        'name': '财多身弱',
        'classic': 'SFTK-008-001',
        'slice_id': 'PATHOLOGY.QIANG_RUO.004',   # DTS 准(财多身弱)
        'slice_support': ['PATHOLOGY.QIANG_RUO.009', 'PATHOLOGY.QIANG_RUO.010'],
        'domain': 'WANGSH',
        'desc': '财星当令或成党, 日主失令无根/根轻',
    },
    'SHA_ZHONG_SHEN_QING': {
        'name': '杀重身轻',
        'classic': 'SFTK-008-001',
        'slice_id': 'PATHOLOGY.QIANG_RUO.005',   # DTS 准(杀重身轻)
        'slice_support': ['PATHOLOGY.QIANG_RUO.009', 'PATHOLOGY.QIANG_RUO.010'],
        'domain': 'WANGSH',
        'desc': '官杀当令或成党, 日主无根/根轻',
    },
    'XIE_QI_TAI_ZHONG': {
        'name': '泄气太重',
        'classic': 'PZZQ 食神本属泄气',
        'slice_id': 'PATHOLOGY.QIANG_RUO.020',   # SFTK 雕枯旺弱四病(旁参)
        'slice_support': ['STRUCTURE.GE_JU.SHI_SHEN.001'],  # PZZQ 食神本属泄气
        'domain': 'WANGSH',
        'desc': '食伤当令或成党, 日主泄气太过',
    },
    'SHANGGUAN_JIAN_GUAN': {
        'name': '伤官见官',
        'classic': 'YHZP 伤官见官为祸百端',
        'slice_id': 'STRUCTURE.GE_JU.JIU_YING.003',  # DTS 准(伤官格见官)
        'slice_support': ['STRUCTURE.GE_JU.SHANG_GUAN.001'],
        'domain': 'GEJU',
        'desc': '伤官与官杀同时透干/出现',
    },
    'XIAO_DUO_SHI': {
        'name': '枭神夺食',
        'classic': 'YHZP 枭神夺食',
        'slice_id': 'PATHOLOGY.JIE_GOU.018',   # SFTK 枭神夺食补曰(旁参)
        'slice_support': ['PATHOLOGY.JIE_GOU.016', 'PATHOLOGY.JIE_GOU.017'],
        'domain': 'JIEGOU',
        'desc': '偏印(枭)与食神同时出现, 枭克食',
    },
    'YONG_SHEN_BU_ZAI_JU': {
        'name': '用神不在局中',
        'classic': 'PZZQ241/255',
        'slice_id': None,                        # UNVERIFIED: MD文库未定位对口切片
        'slice_support': [],
        'domain': 'GEJU',
        'desc': '格局成格但所需用神(印)不在原局, 带病等岁运补',
    },
    'BIJIE_DUO_CAI': {
        'name': '比劫夺财',
        'classic': 'SFTK-008-001 用财见比肩为病',
        'slice_id': None,                        # UNVERIFIED: MD文库未定位对口切片
        'slice_support': [],
        'domain': 'GEJU',
        'desc': '比劫透干成党, 财星被夺',
    },
    'BIJIE_CHENG_DANG': {
        'name': '比劫成党',
        'classic': 'DTS 水多以水为病 / SFTK 比劫成党',
        'slice_id': 'PATHOLOGY.QIANG_RUO.001',   # DTS 三十二、众寡(强众) 准
        'slice_support': ['PATHOLOGY.QIANG_RUO.020'],
        'domain': 'WANGSH',
        'desc': '比劫数量达到3个或以上, 日主同类成势, 无论是否有财',
    },
    'YIN_DUO_MAI_ZI': {
        'name': '印多埋子',
        'classic': 'DTS 反局章 君赖臣生(行445) 土重金埋/金旺则水浊 同族',
        'slice_id': 'STATE.WANG_SHUAI.FAN_JU.001',  # DTS 反局总纲 准
        'slice_support': ['PATHOLOGY.ZHI_FA.010'],
        'domain': 'JIEGOU',
        'desc': '印星成党且力量远大于日主, 印多反埋日主, 需财星疏印',
        # 归属订正(2026-10):
        #   DTS 行449「木母也, 火子也, 太旺谓之慈母, 反使火炽百焚灭, 是谓灭子」属反局章
        #   【第三组 母慈灭子】, 其「母」= 生我之五行(木母火子), 与印星无关。
        #   本条讲【印星成党埋日主】, 归【第一组 君赖臣生】(行445):
        #   「土重金埋」「金旺则水浊」等, 病方为生君者太过, 药为克病方者。
        #   -> 病名不再用「母多灭子」, 避免与 DTS 第三组同形异指。
        },
    'ZHI_SHA_TAI_GUO': {
        'name': '制杀太过',
        'classic': 'PZZQ4106 制煞过重同样成病',
        'slice_id': 'SUI_YUN.RE_EVALUATION.DA_YUN_ZHI_YU.009',  # SFTK 制伏太过(旁参)
        'slice_support': [],
        'domain': 'GEJU',
        'desc': '食伤当令成党制杀, 七杀无根/根被冲(制尽)为病; 药=印(身弱制食护杀)/财(身旺泄食生杀)',
    },
}

# 药类型定义 (原典依据)
YAO_TYPES = {
    'YIN_BI_BANG_SHEN': {
        'name': '印比帮身',
        'classic': 'SFTK-009-002 日主太弱宜行身旺之地',
        'desc': '印星生身 + 比劫帮身',
    },
    'SHI_SHANG_ZHI_SHA': {
        'name': '食伤制杀',
        'classic': 'YHZP 食神制杀',
        'desc': '食神/伤官克制七杀',
    },
    'CAI_PO_YIN': {
        'name': '财破印',
        'classic': 'YHZP 财破印',
        'desc': '财星克制印星',
    },
    'GUAN_SHA_ZHI_BIJIE': {
        'name': '官杀制比劫',
        'classic': 'YHZP 官杀制比劫',
        'desc': '官杀克制比劫',
    },
    'YIN_HUA_SHA': {
        'name': '印化杀',
        'classic': 'YHZP 杀印相生',
        'desc': '印星化泄七杀',
    },
    'CAI_XIE_SHI_SHENG_SHA': {
        'name': '财泄食生杀',
        'classic': 'PZZQ4106 身旺者宜财',
        'desc': '财星泄食伤之气, 转生七杀(制杀太过, 身旺宜财)',
    },
}

# 病药配对 (原典明确的对应关系)
BING_YAO_PAIRS = {
    'CAI_DUO_SHEN_RUO': ['YIN_BI_BANG_SHEN'],
    'SHA_ZHONG_SHEN_QING': ['SHI_SHANG_ZHI_SHA', 'YIN_HUA_SHA', 'YIN_BI_BANG_SHEN'],
    'XIE_QI_TAI_ZHONG': ['YIN_BI_BANG_SHEN'],
    'SHANGGUAN_JIAN_GUAN': ['YIN_HUA_SHA', 'CAI_PO_YIN'],
    'XIAO_DUO_SHI': ['CAI_PO_YIN'],
    'BIJIE_DUO_CAI': ['GUAN_SHA_ZHI_BIJIE'],
    'BIJIE_CHENG_DANG': ['GUAN_SHA_ZHI_BIJIE'],
    'YIN_DUO_MAI_ZI': ['CAI_PO_YIN'],
    'YONG_SHEN_BU_ZAI_JU': ['YIN_HUA_SHA'],
    'ZHI_SHA_TAI_GUO': ['YIN_HUA_SHA', 'CAI_XIE_SHI_SHENG_SHA'],
}


def _get_query_state(queries: List[Dict], query_id_suffix: str) -> Optional[str]:
    """从query列表中获取指定query的state (按后缀匹配)."""
    for q in queries:
        qid = q.get('query_id', '')
        if qid.endswith(query_id_suffix) or qid == query_id_suffix:
            return q.get('state')
    return None


def _has_tengod(ten_god_members: List[Dict], tengod_cn_list: List[str], position: str = None) -> bool:
    """检查十神成员中是否有指定中文十神.
    tengod_cn_list: 中文十神名称列表, 如['伤官']
    position: stem/hidden, None=全部
    """
    for m in ten_god_members:
        tg = m.get('ten_god', '')
        if tg in tengod_cn_list:
            if position is None or m.get('type') == position:
                return True
    return False


def _count_tengod(ten_god_members: List[Dict], tengod_cn_list: List[str], position: str = None) -> int:
    """统计指定十神的数量."""
    count = 0
    for m in ten_god_members:
        tg = m.get('ten_god', '')
        if tg in tengod_cn_list:
            if position is None or m.get('type') == position:
                count += 1
    return count


def identify_bing(facts: Dict[str, Any], queries: List[Dict]) -> List[Dict]:
    """识别命局中的病 (只识别存在, 不判轻重)."""
    bing_list = []
    ten_god_members = facts.get('ten_god_members', [])
    daymaster_element = facts.get('daymaster_element', '')
    dm_wx = GAN_WX.get(facts.get('day_stem', ''), daymaster_element)
    month_qi_element = facts.get('month_qi_element', '')
    root_weight = facts.get('root_weight_class_facts', {})
    has_heavy_root = any(v.get('class') == 'HEAVY' for v in root_weight.values())
    has_light_root = any(v.get('class') == 'LIGHT' for v in root_weight.values())
    has_root = has_heavy_root or has_light_root

    # 五行力量(供各病识别使用, facts中可能已注入wuxing_power)
    wp = facts.get('wuxing_power', {})
    wp_data = wp.get('wuxing_power', wp) if isinstance(wp, dict) else {}

    # 统一计数(收紧门槛): 他干透干(排除日干) + 本气根(不含中气余气)
    pillars = facts.get('pillars')

    def _tou_ben(wx):
        if not pillars:
            return (0, 0)
        tou = sum(1 for pos in ('year', 'month', 'hour')
                  if GAN_WX.get(pillars[pos][0]) == wx)
        ben = sum(1 for pos in ('year', 'month', 'day', 'hour')
                  if ZHI_BEN_WX.get(pillars[pos][1]) == wx)
        for _eg, _ez in facts.get('transit_extra', []):
            if GAN_WX.get(_eg) == wx:
                tou += 1
            if ZHI_BEN_WX.get(_ez) == wx:
                ben += 1
        return (tou, ben)

    def _ju_piao(wx):
        # PATCH-GE-02 局票: 全合(三合/三会)+2, 半合(两支)+1; 读wp的ju_n/banhe_n
        e = wp_data.get(wx, {}) if isinstance(wp_data, dict) else {}
        try:
            return int(e.get('ju_n', 0) or 0) * 2 + int(e.get('banhe_n', 0) or 0) * 1
        except Exception:
            return 0

    def _x_overpowers(x_wx):
        """克泄耗五行 X 是否相对压过日主(身弱受 X 害 → 病).
        比 X 与日主两行的辩层键(月令序数,成党级别,-透干,-本根):
        X 键更小(X 更旺)→True; 日主不弱、能任克泄耗→False(泄秀/财官为喜)."""
        if not pillars:
            return False
        mm = facts.get('month_qi_element', '')
        dm_wx = GAN_WX.get(facts.get('day_stem', ''), '')
        extra = facts.get('transit_extra')
        cx = _db_counts(pillars, x_wx, extra)
        cd = _db_counts(pillars, dm_wx, extra)
        kx = (_db_month_order(x_wx, mm) if mm else 9,
              _db_dang_level(cx['tou'] + cx['ben'] + _ju_piao(x_wx)),
              -cx['tou'], -cx['ben'])
        kd = (_db_month_order(dm_wx, mm) if mm else 9,
              _db_dang_level(cd['tou'] + cd['ben'] + _ju_piao(dm_wx)),
              -cd['tou'], -cd['ben'])
        return kx < kd

    def _dm_self_ling_ok():
        """日主(含阴阳)是否【自己禄旺当令】. 阴干在阳干当权月仅 CASE_LEVEL(乙寅)
        判为非日主自己令; NO_EVIDENCE 不降级. 其余月令为日主禄/旺即当令."""
        dm = facts.get('day_stem', '')
        pl = facts.get('pillars') or {}
        m = pl.get('month', [None, None])[1] if isinstance(pl.get('month'), (list, tuple)) else None
        if (dm, m) in _YIN_YANG_DANGQUAN and _YIN_YANG_DANGQUAN[(dm, m)] == 'CASE_LEVEL':
            return False
        return (m == _DM_LU.get(dm)) or (m == _DM_WANG.get(dm))

    def _kexie_trigger(wx, query_suffix, check_overpower=False):
        """克泄类病统一触发.
        check_overpower=True(财/杀/食伤): X 有力(当令/成党/query)且相对压过日主才为病;
          日主不弱(能任)→X 是泄秀/财官之喜, 不报.
        check_overpower=False(印·生扶): X 有力且日主无重根(母多灭子)才为病.
        无根/根轻仅在触发后补充, 不单独触发."""
        tou, ben = _tou_ben(wx)
        qsup = _get_query_state(queries, query_suffix) == 'SUPPORTED'
        dangling = (month_qi_element == wx)
        cheng = (tou + ben + _ju_piao(wx)) >= DANG_COMBO

        strong = []
        if qsup:
            strong.append('%s query=SUPPORTED' % query_suffix)
        if dangling:
            strong.append('当令')
        if cheng:
            strong.append('成党(他干%d+本根%d=%d)' % (tou, ben, tou + ben))

        hit = []
        if check_overpower:
            if strong and _x_overpowers(wx):
                hit = strong
        else:
            # 印(母)病: 母成党(太旺)时, 看日主【本气真根】(本气禄旺, 非长生虚根)——
            #   母成党而子无本气真根 -> 母多灭子(长生在母本气地是虚根救不了;
            #   DTS"太旺谓慈母, 反使焚灭, 是谓灭子"; 明通赋"金多水浊");
            # 母未成党(仅当令/有力) -> 沿用"日主无重根".
            if cheng:
                _, _dm_ben = _tou_ben(daymaster_element)
                if strong and _dm_ben == 0:
                    hit = strong
            elif strong and not has_heavy_root:
                hit = strong
        if hit:   # 闸门命中后才追加根气说明
            if not has_root:
                hit.append('日主无根')
            elif not has_heavy_root:
                hit.append('日主根轻')
        return (bool(hit), hit)

    # 1. 财多身弱 (统一收紧触发: 财当令/成党 + 财相对压过日主 + 日主无根/根轻)
    cai_wx = KE.get(daymaster_element, '')
    ok, matched = _kexie_trigger(cai_wx, 'CAIDUO-SHENRUAN', True)
    _cai_combo = 0
    if not ok:
        # 根轻但财当令/本气根: 原典"财星当令或成党, 日主失令无根/根轻" — 根轻(LIGHT/NONE)亦报病
        _caiT, _caiB = _tou_ben(cai_wx)
        _cai_combo = _caiT + _caiB + _ju_piao(cai_wx)
        _mm_q = facts.get('month_qi_element', '')
        _cai_dangling = (_mm_q == cai_wx)
        _cai_benshi = (_caiB >= 1)
        _no_heavy = not has_heavy_root
        # STEP-L7-1 (2026-10, 切片校准): 兜底分支对齐 PATHOLOGY.QIANG_RUO.004
        #   原文「财旺身弱」= 财神【太旺】+ 日主衰弱。仅"财有本气根"≠"财旺"
        #   (如亥月辰戌土, 囚死之地有根而无力)。故:
        #   - 财当令(旺) + 日主无重根  -> 财旺身弱, 报
        #   - 财有本气根(非当令) + 日主无重根 -> 须财相对压过日主(_x_overpowers)才算旺, 否则不报
        if _no_heavy and _cai_dangling:
            ok = True
            matched = ['财当令(旺)+日主无HEAVY根']
        elif _no_heavy and _cai_benshi and _x_overpowers(cai_wx):
            ok = True
            matched = ['财有本气根且压过日主(旺), 日主无HEAVY根']
        if ok:
            matched = matched + ['财(他干%d+本根%d+局票%d=%d, 当令=%s)' % (_caiT, _caiB, _ju_piao(cai_wx), _cai_combo, _cai_dangling)]
    else:
        # _kexie_trigger 已触发, 算 combo 供 overwang_exempt 用
        _cai_combo = _tou_ben(cai_wx)[0] + _tou_ben(cai_wx)[1] + _ju_piao(cai_wx)
    if ok:
        b = BING_TYPES['CAI_DUO_SHEN_RUO']
        bing_list.append({
            'bing_id': 'CAI_DUO_SHEN_RUO',
            'name': b['name'], 'desc': b['desc'], 'classic': b['classic'],
            'evidence': [b['classic']], 'matched_facts': matched,
            'overwang_exempt': (_cai_combo >= DANG_COMBO),  # 财成党病: 喜神过滤过旺例外(combo>=4保留)
        })

    # 2. 杀重身轻 (统一收紧触发)
    sha_wx = KE_WO.get(daymaster_element, '')
    ok, matched = _kexie_trigger(sha_wx, 'SHAZHONG-SHENQING', True)
    # 格体过滤: 杀是伤官带煞格体, 不报杀重病(双层属性: 格体非破格)
    if ok:
        _gc = facts.get('ge_cheng') or {}
        if sha_wx in (_gc.get('ti_wx') or []):
            ok = False
    # 制化闸门: 杀有食制(食神透)或印化(印透)则不报杀重病(UNVERIFIED: 食神无根/印克食神待校)
    if ok:
        shi_wx = SHENG.get(daymaster_element, '')
        yin_wx = SHENG_WO.get(daymaster_element, '')
        _st, _sb = _tou_ben(shi_wx)
        _yt, _yb = _tou_ben(yin_wx)
        if _st > 0 or _yt > 0:
            ok = False
    # 用神不在局中: 伤官带煞格成 + 印(生我)透根皆无 -> 带病等岁运补
    _gc = facts.get('ge_cheng') or {}
    if _gc.get('ge') == '伤官格(带煞无财)':
        _yin = SHENG_WO.get(daymaster_element, '')
        if _yin:
            _yt, _yb = _tou_ben(_yin)
            if _yt == 0 and _yb == 0:
                b = BING_TYPES['YONG_SHEN_BU_ZAI_JU']
                bing_list.append({'bing_id': 'YONG_SHEN_BU_ZAI_JU', 'name': b['name'],
                    'desc': b['desc'], 'classic': b['classic'],
                    'evidence': [b['classic']], 'matched_facts': [f'印{_yin}透根皆无']})
    if ok:
        b = BING_TYPES['SHA_ZHONG_SHEN_QING']
        bing_list.append({
            'bing_id': 'SHA_ZHONG_SHEN_QING',
            'name': b['name'], 'desc': b['desc'], 'classic': b['classic'],
            'evidence': [b['classic']], 'matched_facts': matched,
        })

    # 3. 泄气太重 (统一收紧触发)
    xie_wx = SHENG.get(daymaster_element, '')
    ok, matched = _kexie_trigger(xie_wx, 'XIEQI-TAIZHONG', True)
    # 成格喜神过滤: 食神生财格成, 食神为成格喜神, 泄气病不报; 过旺(combo>=阈值)例外仍报
    if ok:
        from engines.common.ge_jie_layer import is_xix_shen
        _xt, _xb = _tou_ben(xie_wx)
        if is_xix_shen(facts, xie_wx, _xt + _xb + _ju_piao(xie_wx)):
            ok = False
    # 财透闸门: 食伤生财泄秀, 财透则不报泄气病(UNVERIFIED: 财无根/印克食伤待校)
    if ok:
        cai_wx = KE.get(daymaster_element, '')
        _ct, _cb = _tou_ben(cai_wx)
        if _ct > 0:
            ok = False
    # 印药季节降级: 食伤当令成党 + 印透且印在月令季节旺/相(制食护食伤有力) -> 不报
    # (与"制杀太过"同判据; 印失令/死囚则制不住食伤, 照报)
    if ok:
        _yin_wx_qx = SHENG_WO.get(daymaster_element, '')
        _yt_qx, _yb_qx = _tou_ben(_yin_wx_qx)
        if _yt_qx > 0:
            _SEASON_QX = {'寅':('木','火'),'卯':('木','火'),'辰':('木','火'),
                          '巳':('火','土'),'午':('火','土'),'未':('火','土'),
                          '申':('金','水'),'酉':('金','水'),'戌':('金','水'),
                          '亥':('水','木'),'子':('水','木'),'丑':('水','木')}
            _mz_qx = pillars['month'][1]
            _w_qx, _x_qx = _SEASON_QX[_mz_qx]
            if _yin_wx_qx in (_w_qx, _x_qx):
                ok = False
    if ok:
        b = BING_TYPES['XIE_QI_TAI_ZHONG']
        bing_list.append({
            'bing_id': 'XIE_QI_TAI_ZHONG',
            'name': b['name'], 'desc': b['desc'], 'classic': b['classic'],
            'evidence': [b['classic']], 'matched_facts': matched,
        })

    # 4. 伤官见官 (收紧: 伤官与官杀皆须【透干】, 藏干共现不触发)
    sg_tou = _has_tengod(ten_god_members, ['伤官'], 'stem')
    gs_tou = _has_tengod(ten_god_members, ['正官', '七杀'], 'stem')
    if sg_tou and gs_tou:
        b = BING_TYPES['SHANGGUAN_JIAN_GUAN']
        bing_list.append({
            'bing_id': 'SHANGGUAN_JIAN_GUAN',
            'name': b['name'], 'desc': b['desc'], 'classic': b['classic'],
            'evidence': [b['classic']],
            'matched_facts': ['伤官透干', '官杀透干'],
        })

    # 5. 枭神夺食 (力量闸门, 非字面共现):
    # 须 偏印旺(透干>=2 或 偏印当令) AND 食神弱(食神五行无本气禄旺根)
    # 原典: 枭神夺食需偏印成势克食神; 两字共现、食神有根则不夺
    pianyin_stem_n = _count_tengod(ten_god_members, ['偏印'], 'stem')
    pianyin_wx = SHENG_WO.get(daymaster_element, '')   # 生我=印五行, 乙木→水
    pianyin_dangling = (month_qi_element == pianyin_wx)
    pianyin_wang = pianyin_stem_n >= 2 or pianyin_dangling
    shishen_wx = SHENG.get(daymaster_element, '')      # 我生=食伤五行, 乙木→火
    shishen_ben_n = (wp_data.get(shishen_wx, {}) or {}).get('ben_n', 0)
    shishen_ruo = shishen_ben_n == 0
    # 食神须"成用": 透干 或 有本气禄旺根; 仅藏余气、被本气印盖头压制者不成食神用(属印格), 无可夺
    shishen_tou = _has_tengod(ten_god_members, ['食神'], 'stem')
    shishen_exists = shishen_tou or shishen_ben_n >= 1
    if pianyin_wang and shishen_exists and shishen_ruo:
        b = BING_TYPES['XIAO_DUO_SHI']
        bing_list.append({
            'bing_id': 'XIAO_DUO_SHI',
            'name': b['name'],
            'desc': b['desc'],
            'classic': b['classic'],
            'evidence': [b['classic']],
            'matched_facts': ['偏印旺(透干%d个/当令%s)' % (pianyin_stem_n, pianyin_dangling),
                              '食神弱(无本气禄旺根)'],
        })

    # 5b. 制杀太过 (PZZQ4106"制煞过重同样成病"):
    # 食伤当令/成党 + 杀透 + 杀无本气根/根被六冲(制尽) -> 病
    # 印药降级: 印透且印在月令季节旺/相(制食护杀有力) -> 不报; 药无力照报
    sha_tou_5b = _has_tengod(ten_god_members, ['七杀'], 'stem')
    if sha_tou_5b:
        _zss_t, _zss_b = _tou_ben(xie_wx)
        _ss_dang = (month_qi_element == xie_wx)
        _ss_cheng = (_zss_t + _zss_b + _ju_piao(xie_wx)) >= DANG_COMBO
        if _ss_dang or _ss_cheng:
            _all_zhis_5b = [pillars[pos][1] for pos in ('year', 'month', 'day', 'hour')]
            _zsha_zhis = [z for z in _all_zhis_5b if ZHI_BEN_WX.get(z) == sha_wx]
            _LIUCHONG_5b = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅',
                            '卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}
            _zsha_chong = any(_LIUCHONG_5b.get(z) in _all_zhis_5b for z in _zsha_zhis)
            # 仅"杀根被冲(制尽)"论制杀太过; "杀无根"仍论格成(层次/岁运问题)
            if _zsha_chong:
                # 印药季节旺相表(三合月: 寅卯辰春木旺火相...): 印旺/相=制食护杀有力
                _SEASON_WX = {'寅':('木','火'),'卯':('木','火'),'辰':('木','火'),
                              '巳':('火','土'),'午':('火','土'),'未':('火','土'),
                              '申':('金','水'),'酉':('金','水'),'戌':('金','水'),
                              '亥':('水','木'),'子':('水','木'),'丑':('水','木')}
                _yin_tou_5b = _has_tengod(ten_god_members, ['正印', '偏印'], 'stem')
                _mz_5b = pillars['month'][1]
                _wang_5b, _xiang_5b = _SEASON_WX[_mz_5b]
                _yin_wx_5b = SHENG_WO.get(daymaster_element, '')
                _yin_youli = _yin_tou_5b and (_yin_wx_5b in (_wang_5b, _xiang_5b))
                if not _yin_youli:
                    b = BING_TYPES['ZHI_SHA_TAI_GUO']
                    bing_list.append({
                        'bing_id': 'ZHI_SHA_TAI_GUO',
                        'name': b['name'], 'desc': b['desc'], 'classic': b['classic'],
                        'evidence': [b['classic']],
                        'matched_facts': ['食伤当令/成党(他干%d+本根%d)' % (_zss_t, _zss_b),
                                          '杀透', '杀无根/根冲(制尽)', '印药无力'],
                    })

    # 6. 比劫夺财 (收紧: 比劫combo>=4 且 财明[透干或本气根, 非仅藏中气])
    bj_tou, bj_ben = _tou_ben(daymaster_element)
    if (bj_tou + bj_ben + _ju_piao(daymaster_element)) >= DANG_COMBO and _dm_self_ling_ok():
        cai_tou, cai_ben = _tou_ben(cai_wx)
        if cai_tou >= 1 or cai_ben >= 1:
            b = BING_TYPES['BIJIE_DUO_CAI']
            bing_list.append({
                'bing_id': 'BIJIE_DUO_CAI',
                'name': b['name'], 'desc': b['desc'], 'classic': b['classic'],
                'evidence': [b['classic']],
                'matched_facts': ['比劫成党(他干%d+本根%d=%d)' % (bj_tou, bj_ben, bj_tou + bj_ben),
                                  '财明(透干%d/本根%d)' % (cai_tou, cai_ben)],
            })

    # 7. 比劫成党 (收紧: 他干+本根 combo>=4; 日主同类本旺, 不设无重根条件)
    if (bj_tou + bj_ben + _ju_piao(daymaster_element)) >= DANG_COMBO and _dm_self_ling_ok():
        b = BING_TYPES['BIJIE_CHENG_DANG']
        bing_list.append({
            'bing_id': 'BIJIE_CHENG_DANG',
            'name': b['name'],
            'desc': b['desc'],
            'classic': b['classic'],
            'evidence': [b['classic']],
            'matched_facts': ['比劫成党(他干%d/本根%d=%d)' % (bj_tou, bj_ben, bj_tou + bj_ben)],
        })

    # 8. 印多埋子/母多灭子 (统一触发: 当令或成党, 无重根)
    yin_wx = SHENG_WO.get(daymaster_element, '')
    ok, yin_matched = _kexie_trigger(yin_wx, 'YINDUO-MAIZI', False)
    if ok:
        b = BING_TYPES['YIN_DUO_MAI_ZI']
        bing_list.append({
            'bing_id': 'YIN_DUO_MAI_ZI',
            'name': b['name'], 'desc': b['desc'], 'classic': b['classic'],
            'evidence': [b['classic']], 'matched_facts': yin_matched,
        })

    # STEP-1 (2026-10) L4→P1 接口解耦:
    #   依《架构层规范》§2.7 铁律1「病分五域, 跨域不冲突」——
    #   格局域的 xi_wx/ti_wx 只能否决格局域的病, 不得否决旺衰域的病。
    #   原实现用 L4 的 xi_wx/ti_wx 跨域过滤全部病类, 使 L4 一旦判错 xi_wx,
    #   其错误会顺带删掉其他域已成立的病机(如: 财格 xi_wx=['水'] 删掉 YIN_DUO_MAI_ZI
    #   印多埋子 —— 而该盘水已泛滥, 正是 DTS FAN_JU.001 行445「水泛木浮」之病)。
    #   本 step【不删判定, 只解耦】: 过滤仍按域生效, 但仅限格局域病类;
    #   旺衰域病不受 L4 过滤。Step 2 落病域字段后, 改为按 病域 字段判定, 不再硬编码。
    #   boundary: 本 step 不引入新判据, 不改任何触发门槛, 只改过滤的作用域。
    _WS_DOMAIN = {
        'CAI_DUO_SHEN_RUO', 'SHA_ZHONG_SHEN_QING', 'XIE_QI_TAI_ZHONG',
        'BIJIE_CHENG_DANG', 'YIN_DUO_MAI_ZI',
    }

    # 格体过滤: 伤官带煞格的格体五行(伤官+煞)全病类过滤; 过旺例外(combo>=6)保留
    # 财格: 财是格体, 但财成党(combo>=DANG_COMBO)时反为"财多身弱"病须保留
    # 其他格体五行 combo>=6 保留
    _gc = facts.get('ge_cheng') or {}
    _ti_wx = _gc.get('ti_wx') or []
    if _ti_wx:
        _bwx = {'CAI_DUO_SHEN_RUO': cai_wx, 'SHA_ZHONG_SHEN_QING': sha_wx,
                'XIE_QI_TAI_ZHONG': xie_wx, 'YIN_DUO_MAI_ZI': yin_wx,
                'BIJIE_CHENG_DANG': dm_wx, 'BIJIE_DUO_CAI': dm_wx,
                'SHANGGUAN_JIAN_GUAN': sha_wx}
        _kept = []
        for _b in bing_list:
            if _b.get('bing_id') in _WS_DOMAIN:   # STEP-1: 旺衰域不受 L4 过滤
                _kept.append(_b)
                continue
            _bw = _bwx.get(_b['bing_id'], '')
            if _bw and _bw in _ti_wx:
                _bt, _bb = _tou_ben(_bw)
                _combo = _bt + _bb + _ju_piao(_bw)
                # 财多身弱: 财当令/本气根+日主无HEAVY根 即保留(原典"财星当令或成党,日主失令无根/根轻")
                _mm_q = facts.get('month_qi_element', '')
                _cai_caibi = (_bw == cai_wx) and (_combo >= 2 or _mm_q == cai_wx)
                _no_heavy = not has_heavy_root
                if _b.get('overwang_exempt') or (_cai_caibi and _no_heavy):
                    pass  # 财成党/当令病: 保留
                elif _combo < 6:
                    continue
                _kept.append(_b)
        bing_list = _kept

    # 喜神过滤(与ti_wx并列): xi_wx=成格路径喜神五行; 病五行∈xi_wx 且非过旺例外(combo<6) -> 不报
    # 破格时格局层同时清空ti_wx/xi_wx(同失效); 过旺例外(combo>=6)保留, 独立生效
    # 财成党病(财多身弱/财格喜神过旺): overwang_exempt=True 时按过旺例外(combo>=DANG_COMBO保留), 不被喜神过滤清掉
    _xi_wx = _gc.get('xi_wx') or []
    if _xi_wx:
        _xwx = {'CAI_DUO_SHEN_RUO': cai_wx, 'SHA_ZHONG_SHEN_QING': sha_wx,
                'XIE_QI_TAI_ZHONG': xie_wx, 'YIN_DUO_MAI_ZI': yin_wx,
                'BIJIE_CHENG_DANG': dm_wx, 'BIJIE_DUO_CAI': dm_wx,
                'SHANGGUAN_JIAN_GUAN': sha_wx, 'XIAO_DUO_SHI': yin_wx}
        _kept = []
        for _b in bing_list:
            if _b.get('bing_id') in _WS_DOMAIN:   # STEP-1: 旺衰域不受 L4 喜神过滤
                _kept.append(_b)
                continue
            _bw = _xwx.get(_b['bing_id'], '')
            if _bw and _bw in _xi_wx:
                _bt, _bb = _tou_ben(_bw)
                _combo = _bt + _bb + _ju_piao(_bw)
                if _b.get('overwang_exempt') and _combo >= DANG_COMBO:
                    pass  # 财成党病: 保留
                elif _combo < 6:
                    continue
                _kept.append(_b)
            else:
                _kept.append(_b)
        bing_list = _kept

    # 制化过滤: zhi_wx(制神)克候选病五行→降级; hua_wx(化神)被候选病五行生→降级
    # 独立于过旺例外(制神仍在, 不随过旺例外失效)
    _zhi_wx = _gc.get('zhi_wx') or []
    _hua_wx = _gc.get('hua_wx') or []
    if _zhi_wx or _hua_wx:
        _KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
        _WO_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
        _bwx = {'CAI_DUO_SHEN_RUO': cai_wx, 'SHA_ZHONG_SHEN_QING': sha_wx,
                'XIE_QI_TAI_ZHONG': xie_wx, 'YIN_DUO_MAI_ZI': yin_wx,
                'BIJIE_CHENG_DANG': dm_wx, 'BIJIE_DUO_CAI': dm_wx,
                'SHANGGUAN_JIAN_GUAN': sha_wx}
        _kept = []
        for _b in bing_list:
            _bw = _bwx.get(_b['bing_id'], '')
            if _bw:
                if any(_KE.get(_z) == _bw for _z in _zhi_wx):
                    continue
                if any(_WO_SHENG.get(_bw) == _h for _h in _hua_wx):
                    continue
            _kept.append(_b)
        bing_list = _kept

    # STEP-L4-1 (2026-10): 病机挂 canonical 切片/域/五行/severity 四字段。
    #   slice_id/slice_support/bing_domain 取自 BING_TYPES(MD文库已验证存在);
    #   bing_wx  病机五行(与 ti_wx/xi_wx 过滤同一映射);
    #   severity 病机程度 0-4(severity.derive_severity, 分层判定不加权);
    #   bing_wx=None 的病机(未映射) 不派 severity(不臆断)。
    _BID_WX = {
        'CAI_DUO_SHEN_RUO': cai_wx, 'SHA_ZHONG_SHEN_QING': sha_wx,
        'XIE_QI_TAI_ZHONG': xie_wx, 'SHANGGUAN_JIAN_GUAN': sha_wx,
        'XIAO_DUO_SHI': pianyin_wx, 'YIN_DUO_MAI_ZI': yin_wx,
        'BIJIE_CHENG_DANG': dm_wx, 'BIJIE_DUO_CAI': dm_wx,
        'ZHI_SHA_TAI_GUO': xie_wx,
    }
    for _b in bing_list:
        _t = BING_TYPES.get(_b.get('bing_id'), {})
        _b['slice_id'] = _t.get('slice_id')
        _b['slice_support'] = list(_t.get('slice_support') or [])
        _b['bing_domain'] = _t.get('domain')
        _bw = _BID_WX.get(_b.get('bing_id'))
        _b['bing_wx'] = _bw
        if _bw:
            _sev = derive_severity(_bw, facts)
            _b['severity'] = _sev['level']
            _b['severity_basis'] = _sev['basis']
        else:
            _b['severity'] = None
            _b['severity_basis'] = None
        # STEP-L2-1 (2026-10): 切片条件三态求值挂载(并行校验, 不改硬编码判定)。
        #   L1/L2 生产链 0 引用实锤修复 —— 病机触发的同时用 MD 切片条件求值,
        #   输出 MATCHED/NOT_MATCHED/ABSTAIN + 逐组依据, 供逐书矫正抽核,
        #   不替代现有触发(无回归); 错位/缺切片病机恒 ABSTAIN(UNVERIFIED)。
        try:
            from engines.common.slice_conditions import eval_slice_conditions
            _sc = eval_slice_conditions(_b.get('bing_id'), _bw, facts)
            _b['slice_condition'] = {
                'state': _sc['state'],
                'slice_id': _sc['slice_id'],
                'status': _sc['status'],
                'reasons': _sc['reasons'],
                'hooks': _sc['hooks'],
                'mode': '并行校验不改判定',
            }
        except Exception as _sce:
            _b['slice_condition'] = {'state': 'ABSTAIN', 'slice_id': _b.get('slice_id'),
                                     'status': 'L2求值异常', 'reasons': [str(_sce)],
                                     'hooks': {}, 'mode': '并行校验不改判定'}

    return bing_list


def identify_yao(facts: Dict[str, Any], queries: List[Dict],
                 bing_ids: List[str] = None) -> List[Dict]:
    """识别命局中的药 (只识别存在, 不判有效性).
    bing_ids: 已识别病机id列表, 用于药方矛盾消解(剔除与病机反向的药).
    """
    yao_list = []
    ten_god_members = facts.get('ten_god_members', [])
    bing_ids = bing_ids or []

    # 药方矛盾守卫: 印重(印多埋子)或比劫成党为病时, "印比帮身"为反向药, 不列
    yinbi_contradicted = ('YIN_DUO_MAI_ZI' in bing_ids) or ('BIJIE_CHENG_DANG' in bing_ids)

    # 1. 印比帮身 (query驱动 + 结构驱动)
    yin_party = _get_query_state(queries, 'YIN-PARTY') == 'SUPPORTED'
    bijie_party = _get_query_state(queries, 'BIJIE-PARTY') == 'SUPPORTED'
    has_yin = _has_tengod(ten_god_members, ['正印', '偏印'])
    has_bijie = _has_tengod(ten_god_members, ['比肩', '劫财'])
    if (not yinbi_contradicted) and (yin_party or bijie_party or has_yin or has_bijie):
        y = YAO_TYPES['YIN_BI_BANG_SHEN']
        matched = []
        if yin_party:
            matched.append('印星成党')
        if bijie_party:
            matched.append('比劫成党')
        if has_yin and not yin_party:
            matched.append('印星出现')
        if has_bijie and not bijie_party:
            matched.append('比劫出现')
        yao_list.append({
            'yao_id': 'YIN_BI_BANG_SHEN',
            'name': y['name'],
            'desc': y['desc'],
            'classic': y['classic'],
            'evidence': [y['classic']],
            'matched_facts': matched,
        })

    # 2. 食伤制杀 (结构驱动: 食伤+七杀同时出现)
    has_shishang = _has_tengod(ten_god_members, ['食神', '伤官'])
    has_qisha = _has_tengod(ten_god_members, ['七杀'])
    if has_shishang and has_qisha:
        y = YAO_TYPES['SHI_SHANG_ZHI_SHA']
        yao_list.append({
            'yao_id': 'SHI_SHANG_ZHI_SHA',
            'name': y['name'],
            'desc': y['desc'],
            'classic': y['classic'],
            'evidence': [y['classic']],
            'matched_facts': ['食伤出现', '七杀出现'],
        })

    # 3. 财破印 (结构驱动: 财+印同时出现)
    has_cai = _has_tengod(ten_god_members, ['正财', '偏财'])
    has_yin = _has_tengod(ten_god_members, ['正印', '偏印'])
    if has_cai and has_yin:
        y = YAO_TYPES['CAI_PO_YIN']
        yao_list.append({
            'yao_id': 'CAI_PO_YIN',
            'name': y['name'],
            'desc': y['desc'],
            'classic': y['classic'],
            'evidence': [y['classic']],
            'matched_facts': ['财星出现', '印星出现'],
        })

    # 4. 官杀制比劫 (结构驱动: 官杀+比劫同时出现)
    has_guansha = _has_tengod(ten_god_members, ['正官', '七杀'])
    has_bijie = _has_tengod(ten_god_members, ['比肩', '劫财'])
    if has_guansha and has_bijie:
        y = YAO_TYPES['GUAN_SHA_ZHI_BIJIE']
        yao_list.append({
            'yao_id': 'GUAN_SHA_ZHI_BIJIE',
            'name': y['name'],
            'desc': y['desc'],
            'classic': y['classic'],
            'evidence': [y['classic']],
            'matched_facts': ['官杀出现', '比劫出现'],
        })

    # 5. 印化杀 (结构驱动: 印+七杀同时出现)
    if has_yin and has_qisha:
        y = YAO_TYPES['YIN_HUA_SHA']
        yao_list.append({
            'yao_id': 'YIN_HUA_SHA',
            'name': y['name'],
            'desc': y['desc'],
            'classic': y['classic'],
            'evidence': [y['classic']],
            'matched_facts': ['印星出现', '七杀出现'],
        })

    return yao_list


# 病类→病神五行 (动态按日主; 供药有效性「病重/病轻」判据)
#   依据: SFTK L424「四柱纯土水日干则为杀重身轻…土为诸格之病」+「用财见比肩为病喜官杀为药」
def _bing_shen_wx(bing_id: str, dm_wx: str) -> str:
    m = {
        'CAI_DUO_SHEN_RUO': KE.get(dm_wx, ''),        # 财
        'SHA_ZHONG_SHEN_QING': KE_WO.get(dm_wx, ''),  # 杀
        'XIE_QI_TAI_ZHONG': SHENG.get(dm_wx, ''),     # 食伤(泄)
        'YIN_DUO_MAI_ZI': SHENG_WO.get(dm_wx, ''),    # 印
        'BIJIE_CHENG_DANG': dm_wx,                    # 比劫
        'BIJIE_DUO_CAI': dm_wx,                       # 比劫
        'XIAO_DUO_SHI': SHENG_WO.get(dm_wx, ''),      # 枭印
        'SHANGGUAN_JIAN_GUAN': KE_WO.get(dm_wx, ''),  # 官杀
        'ZHI_SHA_TAI_GUO': KE_WO.get(dm_wx, ''),      # 杀(被制太过)
    }
    return m.get(bing_id, '')


def apply_yuanju_yao(bing_list: List[Dict], facts: Dict[str, Any]) -> tuple:
    """原局药消病 (甲路 + 药有效性三判据, 2026-10-06 定稿)。

    依据(原著优先, 各判据带原文):
      - 消的明文: PZZQ L957「除其病神, 即谓之药」; SFTK L424「原有所害之字而
        得一字以去之」; DTS L240「格中如去病, 财禄两相宜」。
      - 药有效性三判据:
        1. 合判据 (DTS L250 通关「必得引用无合之神及刑冲所间之物」):
           药天干被天干五合合住 → 不能援引 → 药无效。
           实证: DT-0007 甲日主比劫病, 药=庚金官杀, 庚被乙妹合去
           (原断「甲以乙妹妻庚, 凶为吉兆, 含合忘冲」) → 官不能制劫 → 病不消。
        2. 根判据 (SFTK L424「或本身病重而药少…又宜行运以取其中和」):
           病重(病神当令或成党) 且 药无本气根(虚透) → 药少, 原局不消, 待运。
        3. 势判据 (PZZQ L3977「透己土财以解之, 惜病重药轻」/ QTBJ L774
           「己土不能制壬, 病重药轻」): 病神 combo > 药 combo → 病重药轻, 不消。
    判据(布尔): 药在局(透干或本气根) 且 未触三判据任一 → 病消(REMOVED)。
    边界: ① 不重复杀重身轻制化闸门(源头 ok=False 已拦); ② 过旺例外(combo>=4
          财成党)不跳过——药消病=病可治性, 与格体豁免(属性)是两独立机制;
          ③ PZ-0011 财格佩印(印透药在但无根)类 = 源头闸门(格成佩印不报 CAI_DUO),
          登记另立, 不在本函数。
    """
    if not bing_list or not facts:
        return bing_list, []
    pillars = facts.get('pillars') or {}
    if not pillars:
        return bing_list, []
    dm = facts.get('day_stem', '') or ''
    dm_wx = GAN_WX.get(dm, '')
    yao_map = _bing_yao_map(dm_wx)
    wp = facts.get('wuxing_power', {}) or {}
    wp_data = wp.get('wuxing_power', wp) if isinstance(wp, dict) else {}
    WUHE = {'甲': '己', '己': '甲', '乙': '庚', '庚': '乙', '丙': '辛', '辛': '丙',
            '丁': '壬', '壬': '丁', '戊': '癸', '癸': '戊'}

    def _tou_ben(wx):
        tou = sum(1 for pos in ('year', 'month', 'hour')
                  if GAN_WX.get(pillars[pos][0]) == wx)
        ben = sum(1 for pos in ('year', 'month', 'day', 'hour')
                  if ZHI_BEN_WX.get(pillars[pos][1]) == wx)
        return (tou, ben)

    def _combo(wx):
        t, b = _tou_ben(wx)
        e = wp_data.get(wx, {}) if isinstance(wp_data, dict) else {}
        try:
            ju = int(e.get('ju_n', 0) or 0) * 2 + int(e.get('banhe_n', 0) or 0) * 1
        except Exception:
            ju = 0
        return t + b + ju

    kept, removed = [], []
    for bing in bing_list:
        bid = bing.get('bing_id', '')
        yao_wx = [w for w in (yao_map.get(bid, []) or []) if w]
        if not yao_wx:
            kept.append(bing)
            continue
        # 药在局(任一药五行透干或本气根)
        yao_in = any(t >= 1 or b >= 1 for wx in yao_wx
                     for t, b in [_tou_ben(wx)])
        if not yao_in:
            kept.append(bing)
            continue
        # ① 合判据: 药透干字被天干五合合住 -> 无效 (DTS L250 无合之神)
        yao_stems = [pillars[pos][0] for pos in ('year', 'month', 'hour')
                     if GAN_WX.get(pillars[pos][0]) in yao_wx]
        he_jia = any(WUHE.get(s) in {pillars[p][0] for p in ('year', 'month', 'hour')}
                     for s in yao_stems)
        if he_jia:
            bing['yao_yuanju'] = 'INVALID_HE'  # 药被合, 不能援引
            bing['yao_note'] = ('药(%s)被天干五合合住 -> 不能援引, 病不消 '
                                '(DTS L250 通关必得引用无合之神)' % '、'.join(yao_wx))
            kept.append(bing)
            continue
        # 病神五行 + 病重/病轻
        bs_wx = _bing_shen_wx(bid, dm_wx)
        bing_combo = _combo(bs_wx) if bs_wx else 0
        mm = facts.get('month_qi_element', '')
        bing_dang = (bs_wx == mm)  # 病神当令
        bing_zhong = bing_dang or bing_combo >= 2  # 病重 = 当令 或 成党(combo>=2)
        # ② 根判据: 病重 且 药无本气根(虚透) -> 药少, 待运 (SFTK 病重而药少宜行运)
        yao_you_root = any(b >= 1 for wx in yao_wx for _, b in [_tou_ben(wx)])
        if bing_zhong and not yao_you_root:
            bing['yao_yuanju'] = 'INVALID_ROOT'  # 药虚透, 病重药少
            bing['yao_note'] = ('病重(病神%s当令=%s combo=%d) 而 药(%s)无本气根 '
                                '-> 病重药少, 原局不消待运 (SFTK 病重而药少宜行运)'
                                % (bs_wx, bing_dang, bing_combo, '、'.join(yao_wx)))
            kept.append(bing)
            continue
        # ③ 势判据: 病 combo > 药 combo -> 病重药轻 (PZZQ L3977 惜病重药轻)
        yao_combo = max((_combo(wx) for wx in yao_wx), default=0)
        if bs_wx and bing_combo > yao_combo:
            bing['yao_yuanju'] = 'INVALID_POTENTIAL'  # 药力不足
            bing['yao_note'] = ('病神%s combo=%d > 药 combo=%d -> 病重药轻, 不消 '
                                '(PZZQ L3977 惜病重药轻)' % (bs_wx, bing_combo, yao_combo))
            kept.append(bing)
            continue
        # 药有效 -> 消
        bing['yao_yuanju'] = 'REMOVED'
        bing['yao_note'] = ('原局药在(透干/本气根) 且未触合/根/势三判据, 病消 '
                            '(PZZQ L957 除其病神即谓之药; SFTK L424 得一字以去之; '
                            'DTS L240 格中如去病财禄两相宜)')
        removed.append(bing)
    return kept, removed


def build_bingyao_layer(facts: Dict[str, Any], queries: List[Dict],
                        apply_yuanju_yao_enabled: bool = True) -> Dict[str, Any]:
    """构建病药/作用子层.
    输入: L0 facts + L1 queries
    输出: 病药结构 (只识别存在, 不判吉凶/成败/轻重)

    原局药消病(甲路+药有效性三判据): apply_yuanju_yao_enabled 默认 True。
      2026-10-06: 三判据(合/根/势)各有原文(DTS L250 无合之神 / SFTK L424 病重而药少 /
      PZZQ L3977+QTBJ L774 病重药轻), 已落; 干run见 apply_yuanju_yao 注释。
    """
    bing_list = identify_bing(facts, queries)
    yao_removed = []
    if apply_yuanju_yao_enabled:
        # 原局药消病 (甲路): 药在局且有效(未触合/根/势) -> 病消。PZ-0011 财局佩印类缺口
        bing_list, yao_removed = apply_yuanju_yao(bing_list, facts)
    bing_ids = [b['bing_id'] for b in bing_list]
    yao_list = identify_yao(facts, queries, bing_ids)

    # 病药配对 (原典明确的对应关系)
    bing_yao_pairs = []
    for bing in bing_list:
        bing_id = bing['bing_id']
        if bing_id in BING_YAO_PAIRS:
            for yao_id in BING_YAO_PAIRS[bing_id]:
                yao_exists = any(y['yao_id'] == yao_id for y in yao_list)
                bing_yao_pairs.append({
                    'bing_id': bing_id,
                    'yao_id': yao_id,
                    'yao_present': yao_exists,
                    'classic': '原典病药对应',
                    'note': '药在局中存在' if yao_exists else '药不在局中, 宜行药运',
                })

    return {
        'layer': 'BINGYAO',
        'state': 'STRUCTURE_IDENTIFIED',
        'bing_count': len(bing_list),
        'yao_count': len(yao_list),
        'bing_list': bing_list,
        'yao_list': yao_list,
        'bing_yao_pairs': bing_yao_pairs,
        'yao_removed_yuanju': len(yao_removed),
        'yao_removed_note': ('原局药消病(甲路): 判据「药透干/本气根即消」dry run 误伤 139 bad, '
                             '默认关闭; 药有效性(被合/无力/病重药少)待核 SFTK L424/PZZQ L957 原文; '
                             'BING_YAO_PAIRS.yao_present 保留「药在局」结构事实'),
        'boundary_note': '只识别病药结构存在, 不判吉凶/成败/轻重/有效性; 多病多药并列保留, 矛盾共存不裁',
    }



def check_qubing_level(original_bing_list: List[Dict], dayun_stems: List[str] = None,
                        liunian_stem: str = None, daymaster_element: str = '') -> Dict[str, Any]:
    """去病程度结构化检查 (BINGYAO-DUIYING-002).

    只做: 检查大运/流年对原局病的去除程度
    不做: 吉凶/成败/最终裁决

    原典: 去尽病根, 位入台阁; 去病不净, 仍有后患.
    """
    if dayun_stems is None:
        dayun_stems = []
    if liunian_stem:
        all_stems = dayun_stems + [liunian_stem]
    else:
        all_stems = dayun_stems

    # 五行映射
    stem_to_wx = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
                  '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
    # 克关系: A克B
    ke_relation = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
    # 生关系: A生B
    sheng_relation = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}

    dayun_wuxing = [stem_to_wx.get(s, '') for s in all_stems if stem_to_wx.get(s)]

    results = []
    total_bing = len(original_bing_list)
    fully_removed = 0
    partially_removed = 0
    not_removed = 0
    added_bing = 0

    for bing in original_bing_list:
        bing_id = bing.get('bing_id', '')
        bing_name = bing.get('name', '')
        matched_facts = bing.get('matched_facts', [])

        # 简化: 根据病的类型判断对应的药神五行 (单一数据源: 模块级 BING_YAO_MAP/_bing_yao_map)
        bing_yao_map = _bing_yao_map(daymaster_element)

        yao_wuxing = bing_yao_map.get(bing_id, [])

        # 检查大运/流年是否包含药神五行
        yao_in_dayun = [wx for wx in yao_wuxing if wx in dayun_wuxing]
        has_yao = len(yao_in_dayun) > 0

        # 检查是否添病(大运/流年增加病的五行)
        # 简化: 比劫成党病, 大运再逢比劫(水)则添病
        bing_wuxing_map = {
            'BIJIE_CHENG_DANG': ['水'],  # 比劫=水(癸日主)
            'CAI_DUO_SHEN_RUO': ['土'],  # 财=土(癸日主)
        }
        bing_wx = bing_wuxing_map.get(bing_id, [])
        bing_added = any(wx in dayun_wuxing for wx in bing_wx)

        if has_yao and not bing_added:
            level = 'FULLY_REMOVED'
            fully_removed += 1
            level_note = '大运/流年含药神, 去病'
        elif has_yao and bing_added:
            level = 'PARTIALLY_REMOVED'
            partially_removed += 1
            level_note = '大运/流年含药神但也添病, 去病不净'
        elif not has_yao and bing_added:
            level = 'ADDED_BING'
            added_bing += 1
            level_note = '大运/流年添病'
        else:
            level = 'NOT_REMOVED'
            not_removed += 1
            level_note = '大运/流年不含药神, 病未去'

        results.append({
            'bing_id': bing_id,
            'bing_name': bing_name,
            'yao_wuxing': yao_wuxing,
            'yao_in_dayun': yao_in_dayun,
            'bing_added': bing_added,
            'qubing_level': level,
            'level_note': level_note,
        })

    if total_bing > 0:
        if fully_removed == total_bing:
            overall = 'ALL_FULLY_REMOVED'
            overall_note = '所有病均被去除, 去尽病根'
        elif fully_removed > 0 or partially_removed > 0:
            overall = 'PARTIALLY_REMOVED'
            overall_note = '部分病被去除, 去病不净'
        elif added_bing > 0:
            overall = 'ADDED_BING'
            overall_note = '大运/流年添病'
        else:
            overall = 'NOT_REMOVED'
            overall_note = '病未被去除'
    else:
        overall = 'NO_BING'
        overall_note = '原局无病'

    return {
        'module': 'BINGYAO_QUBING_LEVEL_CHECK',
        'namespace': 'bingyao.qubing_level',
        'total_bing': total_bing,
        'fully_removed': fully_removed,
        'partially_removed': partially_removed,
        'not_removed': not_removed,
        'added_bing': added_bing,
        'overall_level': overall,
        'overall_note': overall_note,
        'check_results': results,
        'boundary_note': (
            '去病程度仅为结构化检查; 只报告大运/流年对原局病的去除程度, '
            '不做吉凶/成败/最终裁决; 去尽病根≠大贵, 去病不净≠不吉'
        ),
        'evidence_refs': ['SFTK 去尽病根位入台阁', 'SFTK 有病方为贵'],
    }
