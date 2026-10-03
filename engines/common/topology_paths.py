# -*- coding: utf-8 -*-
"""第4刀: 拓扑层 —— 源流骨架 / 方局混纯 / 通关 / 关拓扑

依据: DTS §十九 源流 L245 / §十一 方局 L183-L193 / §二十 通关 L250
契约: p0_v2/l3_contract_spec.md v1.4 §四、§5.x

★ 落法铁律(契约 §4.0):
  路径生成只准用现有 WX_SHENG / WX_KE 两张映射表逐步递推,
  【禁止】引入邻接矩阵 / 邻接表 / 节点类等显式图数据结构。
  DTS 无「图」, 只有散句; 算法可以是路径搜索, 图的表示不显式化。

★ 块间依赖(单向, 无循环):
      块1 常量 ──┬──> 块2 源流
                 ├──> 块3 方局混纯
                 └──> 块4 通关 ──> 块5 关拓扑判定
      块2/3/4/5 均为纯函数, relations 由调用方传入。

★ 下游只准调 __all__ 列出的函数; 未列出的为内部或对照版。
"""
from typing import Any, Dict, List, Optional

# ══════════════════════════════════════════════════════════════
# 块1  常量
# ══════════════════════════════════════════════════════════════

# ── 五行映射(复用现有 transit_power 表, 不新建) ──
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}   # 我生
WX_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}      # 我克
WX = ('木', '火', '土', '金', '水')

# ── 判据关键词表 ──
# ★ 本表与契约 §5.x「判据关键词表」同步; 契约改则此处改。
#   元教训(契约 §5.x): 关键词检索法使用前必核该词是【判据专有词】
#   还是【通用程度词】。「太过/太旺/中和/纯一」在任何命书都高频 → 不作判据证据。
#   「混局」「纯疵」是 §十一方局混纯的专名 → 才作证据。
FANG_JU_HUN_WORDS = ['混局', '纯疵']


# ══════════════════════════════════════════════════════════════
# 块2  源流 §十九 L245 (步骤 1-2)
# ══════════════════════════════════════════════════════════════
#
# DTS L245 原文:
#   「不必论当令不令, 只论取最多最旺, 而可以为满局之祖宗者, 为源头也。
#     看此源头, 流到何方, 流去之处, 是所喜之神, 即在此住了, 乃为好归路」
#
# ★ 步骤1 「满局之祖宗」= 「最多最旺」的同义改写, 非独立判据
#   (DTS 全文「祖宗」1 处 / 「源头」1 处, 均在 L245 同一句)
# ★ upstream_pending: 排序依据 _mass 是 ENGINE_DEFINED (契约 §2.2 第3条)
#     _mass = ben_n + zhong_n + yu_n + stem_n, 该加法 DTS 无明文


def find_yuan_tou(mass: Dict[str, int]) -> Optional[Dict[str, Any]]:
    """步骤1: 找源头 —— 满局力量最旺的五行

    mass: {五行: 力量}  ← 由调用方传入, 调用方负责 _mass 口径
    返回 None 当全部为 0 或字典为空。

    ⚠ upstream_pending: 此判据建立在 _mass(ENGINE_DEFINED) 之上,
      不与「DTS 明文」同级。见契约 §4.2。
    """
    if not mass:
        return None
    # 整数排序, 无浮点(架构 §1.2)。
    # 并列处理: 遍历 WX 序, 用 `>` 保留【首个遇到】的最旺者(「更大才替换」);
    #   其余并列者记入 tied_with。DTS L245「取最多最旺」在并列时本就无唯一解,
    #   `>`(首个)比 `>=`(末个)更自然 —— 两者都靠 tied_with 承载不确定性。
    best = None
    best_v = None
    for wx in WX:
        raw = mass.get(wx)
        v = int(raw) if raw is not None else 0    # 明判 is not None; 不用 `or 0`
        if best_v is None or v > best_v:
            best, best_v = wx, v
    if best_v is None or best_v <= 0:
        return None
    return {
        'yuan_wx': best,
        'mass': best_v,
        # 并列信息(如实记录, 不隐藏)
        'tied_with': sorted([w for w in WX
                             if (mass.get(w) is not None
                                 and int(mass[w]) == best_v) and w != best]),
        'evidence': 'DTS_CITED',          # 「取最多最旺...而为源头」L245
        'upstream_pending': '_mass_formula',  # ENGINE_DEFINED, 见契约 §2.2-3
        'zong_zu_note': ('「满局之祖宗」是「最多最旺」的同义改写, 非独立判据; '
                         'DTS 全文「祖宗」1 处 / 「源头」1 处, 均在 L245 同一句'),
    }


def gen_liu_cheng(yuan_wx: str, max_len: int = 6) -> List[str]:
    """步骤2: 从源头沿 WX_SHENG 生成路径 —— 【只生成, 不判终点】

    DTS L245「看此源头, 流到何方」—— 「流到何方」的终点是步骤3
    「所喜之神即在此住了」, 依赖 L4 xi_wx, 本刀不落。

    ★ 本函数只做路径枚举, 返回节点序列。
      不判断「是否气泄为乱」(步骤4) / 「遇阻节」(步骤5) —— 都依赖步骤3。
    """
    if yuan_wx not in WX:
        return []
    path = [yuan_wx]
    cur = yuan_wx
    for _ in range(max_len - 1):
        cur = WX_SHENG[cur]
        path.append(cur)
        if cur == yuan_wx:      # 五行生链成环(木->火->土->金->水->木)
            break
    return path


def build_yuan_liu_skeleton(mass: Dict[str, int]) -> Dict[str, Any]:
    """源流骨架 = 步骤1 + 步骤2

    ★ 不落步骤3-6(依赖 L4 xi_wx), 见契约 §4.3。
    """
    yt = find_yuan_tou(mass)
    if yt is None:
        return {
            'yuan_tou': None, 'path': [], 'path_complete': False,
            'status': 'NO_YUAN_TOU',
            'note': '全部五行为 0 或 mass 为空, 无源头',
            'pending_steps': [3, 4, 5, 6],
        }
    path = gen_liu_cheng(yt['yuan_wx'])
    return {
        'yuan_tou': yt,
        'path': path,                     # 五行序列, 由源头沿 WX_SHENG 递推
        'path_complete': True,            # 路径已生成完(不等于路径已判定)
        'status': 'SKELETON_ONLY',
        # ★ 明确声明: 终点未判
        'endpoint': None,
        'endpoint_pending': 'L4_XI_WX',   # 「所喜之神即在此住了」依赖 xi_wx
        'pending_steps': [3, 4, 5, 6],
        'evidence': 'DTS_CITED',
        'note': ('步骤1-2 已落(源头+路径); 步骤3-6 未落。'
                 '路径终点 / 是否气泄为乱 / 遇阻节 / 流住之地 —— 均依赖 L4 xi_wx。'),
    }


# ══════════════════════════════════════════════════════════════
# 块3  方局混纯 §十一 L183-L193
#     (裁二十五丙 + 裁二十八甲精确化 + 裁三十三丙定口径 + 裁三十八甲命名)
# ══════════════════════════════════════════════════════════════
#
# DTS 原文:
#   L183 「方是方兮局是局, 要得方, 莫混局。」
#   L185 「寅、卯、辰, 东方也, 搭一亥或卯或未, 则太过, 岂不为混局哉！」
#   L187 「局混方兮有纯疵, 行运喜南或喜北。」
#   L189 「亥卯未木局, 混一寅辰, 则太强, 行运南北, 则有纯疵, 不能俱利。」
#   L191 「若然方局一齐来, 须是干头无反复。」
#   L193 「木局木方全者, 须要天干全顺得序, 行运不背乃好。」
#
# ★★ 判据内核(裁二十八甲精确化 —— 「完整组 + 额外一支」):
#
#   方混局 (L185): 盘里有【完整三会 {a,b,c}】(relations 有 HUI relation, 三支齐)
#                + 第4支 d, d ∈ 【另一类型的某组】, 且 d ∉ {a,b,c}
#   局混方 (L189): 盘里有【完整三合 {a,b,c}】(relations 有 SANHE relation, 三支齐)
#                + 第4支 d, d ∈ 【另一类型的某组】, 且 d ∉ {a,b,c}
#
#   ★ 「搭一」「混一」的「一」= 【额外的一支】, 量词, 不是「三元组重叠」。
#     L189「混一寅辰」的「寅辰」用顿号分隔 = 「或寅或辰」, 同 L185「亥或卯或未」句式。
#   ★ 【完整组存在】用 relations(需三支齐); 【额外一支的成员资格】用常量表。
#     两侧数据源不同: relations 判「组齐」, 常量表判「成员资格」。
#
# ★★ 甲版 vs 乙版(裁三十三丙定口径 —— 落甲版):
#     甲版 same_wx : 额外一支须属【同五行】的另一类型组  → 2106 盘命中 54
#     乙版 loose   : 额外一支只须属【任一】另一类型组(并集) → 2106 盘命中 227
#     差异 173 盘, 案例断语含「混局/纯疵」者 0 盘 → 乙版过宽(实测证据)。
#     ★ 「同五行」这个限制 DTS 未明说(L183 总纲无五行限制语), 标 ENGINE_DEFINED。
#     ★ 下游只准调 check_fang_ju_ming_same_wx; loose 版仅供对比, 不供判定。

SANHE_GROUPS = [
    ('申', '子', '辰'), ('亥', '卯', '未'),
    ('寅', '午', '戌'), ('巳', '酉', '丑'),
]
HUI_GROUPS = [
    ('寅', '卯', '辰'), ('巳', '午', '未'),
    ('申', '酉', '戌'), ('亥', '子', '丑'),
]

# ★ L185「搭一亥或卯或未」中的「卯」: 卯已在寅卯辰组内, 语义歧义
#   (可能是笔误, 也可能指重复支盘「寅卯辰卯」)
#   六本底本逐本核(2026-10-03): 【无第二来源】—— PZZQ/SMTH/QTBJ/YHZP/SFTK 均无
#   DTS 此段的对应句(「搭一」「莫混局」全文各 1 处, 都在 L185/L183)
#   → 记 pending, 只落「亥」「未」两项。
L185_EXTRA_BRANCHES = ('亥', '未')
L185_MAO_PENDING = '卯'

# ── 甲版(同五行)配对表 ──
#   ★ evidence 分级(裁三十一):
#     木组 DTS_CITED       —— L185/L189 两例明文都是木(寅卯辰↔亥卯未)
#     火/金/水 ENGINE_DEFINED —— 五行推, DTS 未举此三组例
#
#   ★ 输出接口(裁三十四甲 —— 显示与判断分离):
#       peer_group_display  标准序字符串  '巳午未'   供显示/日志
#       peer_group_set      frozenset              供程序判断
#     与 relations.positions(结构序) / branch_relations(集合语义)同类处理。
#   ★ 键用【标准序 tuple】而非 frozenset —— relations 的 branches 是标准序,
#     直接 tuple 查表即可, 省去每次 frozenset 构造; 顺序即语义(标准序)。

_PAIR_MAP = {
    # 完整HUI组(标准序) -> (同五行 SANHE 组标准序, evidence)
    ('寅', '卯', '辰'): (('亥', '卯', '未'), 'DTS_CITED'),       # 木, L185/L189
    ('巳', '午', '未'): (('寅', '午', '戌'), 'ENGINE_DEFINED'),  # 火, 五行推
    ('申', '酉', '戌'): (('巳', '酉', '丑'), 'ENGINE_DEFINED'),  # 金, 五行推
    ('亥', '子', '丑'): (('申', '子', '辰'), 'ENGINE_DEFINED'),  # 水, 五行推
}
# 反向索引(SANHE 组标准序 -> 同五行 HUI 组标准序), 由 _PAIR_MAP 派生, 不手写
_PAIR_MAP_REV = {v[0]: (k, v[1]) for k, v in _PAIR_MAP.items()}


def _complete_groups(relations, rtype):
    """取 relations 里已生成的完整组(三支齐才算已生成)"""
    return [list(r.get("branches") or []) for r in (relations or [])
            if r.get("type") == rtype]


def _findings_row(group_type, grp, d, peer_display, peer_set, evidence):
    """统一 findings 行结构 —— 显示与判断分离(裁三十四甲)"""
    return {
        'group_type': group_type,
        'complete_group_display': ''.join(grp),
        'complete_group_set': frozenset(grp),
        'extra_branch': d,
        'peer_group_display': peer_display,
        'peer_group_set': peer_set,
        'evidence': evidence,
    }


def check_fang_ju_ming_same_wx(relations: List[Dict[str, Any]],
                               pan_zhi: List[str]) -> Dict[str, Any]:
    """★ 主判据(甲版·同五行) 判方局混局 —— DTS L183-L193

    判据: 完整组(relations 三支齐) + 额外一支(属【同五行】的另一类型组)

    ⚠ 同五行限制为 ENGINE_DEFINED —— DTS 只给木组两例(L185/L189),
      L183 总纲「要得方, 莫混局」无五行限制语。木组 DTS_CITED,
      火/金/水三组 ENGINE_DEFINED(五行推)。函数名保留 _same_wx 后缀
      即为让此限制显式化 —— 不改名为 check_fang_ju_ming(见裁三十八)。

    2106 盘实测: 命中 54(FANG_HUN_JU 24 / JU_HUN_FANG 30)
    """
    findings = []
    # ① 方混局 (L185): 完整三会 + 额外一支属【同五行】的 SANHE 组
    for grp in _complete_groups(relations, 'HUI'):
        pair = _PAIR_MAP.get(tuple(grp))
        if pair is None:
            continue
        sanhe_grp, ev = pair
        for d in (pan_zhi or []):
            if d in grp:
                continue                              # 排除已在组内(这才是「搭一」)
            if d in sanhe_grp:
                findings.append(_findings_row(
                    'FANG_HUN_JU', grp, d, ''.join(sanhe_grp),
                    frozenset(sanhe_grp), ev))
    # ② 局混方 (L189): 完整三合 + 额外一支属【同五行】的 HUI 组
    for grp in _complete_groups(relations, 'SANHE'):
        rev = _PAIR_MAP_REV.get(tuple(grp))
        if rev is None:
            continue
        hui_grp, ev = rev
        for d in (pan_zhi or []):
            if d in grp:
                continue
            if d in hui_grp:
                findings.append(_findings_row(
                    'JU_HUN_FANG', grp, d, ''.join(hui_grp),
                    frozenset(hui_grp), ev))
    return {
        'variant': 'JIA_SAME_WUXING',
        'jun_za_ming': bool(findings),
        'group_type': findings[0]['group_type'] if findings else None,
        'findings': findings,
        'findings_count': len(findings),
        'degree': None,                          # ★ 显式 None = 程度未落
        'degree_pending': ('「太过」(L185)「纯疵」(L187/L189)「太强」(L189) '
                           '三词原典有, 无档位/阈值 -> 程度另立待核'),
        'mao_pending': ('L185「搭一亥或卯或未」中「卯」语义歧义(卯已在寅卯辰组内); '
                        '六本底本逐本核无第二来源 -> 只落亥/未, 卯记 pending'),
        'criterion_status': 'JIA_APPROVED',
        'criterion_note': ('DTS 总纲无五行限制语, 「同五行」为 ENGINE_DEFINED; '
                           '木组 DTS_CITED(L185/L189), 火金水 ENGINE_DEFINED'),
        'evidence': 'DTS_CITED',                # 判据来源(L183 总纲)
        'pair_map_evidence': '木组 DTS_CITED / 火金水 ENGINE_DEFINED',
        'keyword_table': 'FANG_JU_HUN_WORDS(契约 §5.x)',
        'line': 'L183-L193',
    }


def check_fang_ju_ming_loose(relations: List[Dict[str, Any]],
                            pan_zhi: List[str]) -> Dict[str, Any]:
    """对照版(乙版·任意) 判方局混局 —— 【不供下游判定, 仅供对比】

    与主判据的唯一差别: 额外一支只须属【任一】另一类型组(12 支并集),
    不限同五行。

    2106 盘实测: 命中 227 —— 比甲版多 173, 而这 173 盘案例断语
    含「混局/纯疵」者 0 盘 -> 实测过宽。故不供判定, 保留仅供对照。

    ⚠ 原名 check_fang_ju_ming 已于裁三十八改为 _loose 后缀, 旧名不再存在。
    """
    all_hui_members = set(b for g in HUI_GROUPS for b in g)
    all_sanhe_members = set(b for g in SANHE_GROUPS for b in g)
    findings = []
    # ① 方混局 (L185): 完整三会 + 额外一支属任一三合组
    for grp in _complete_groups(relations, 'HUI'):
        for d in (pan_zhi or []):
            if d in grp:
                continue                       # ★ 排除已在组内(这才是「搭一」)
            if d in all_sanhe_members:
                hits = [''.join(g) for g in SANHE_GROUPS if d in g]
                findings.append(_findings_row(
                    'FANG_HUN_JU', grp, d, '/'.join(hits),
                    frozenset(d), 'DTS_CITED'))
    # ② 局混方 (L189): 完整三合 + 额外一支属任一三会组
    for grp in _complete_groups(relations, 'SANHE'):
        for d in (pan_zhi or []):
            if d in grp:
                continue
            if d in all_hui_members:
                hits = [''.join(g) for g in HUI_GROUPS if d in g]
                findings.append(_findings_row(
                    'JU_HUN_FANG', grp, d, '/'.join(hits),
                    frozenset(d), 'DTS_CITED'))
    return {
        'variant': 'YI_ANY',
        'jun_za_ming': bool(findings),
        'group_type': findings[0]['group_type'] if findings else None,
        'findings': findings,
        'findings_count': len(findings),
        'usable_as_criteria': False,   # ★ 显式禁用(同 EXTREME_STRONG 处理)
        'criterion_status': 'LOOSE_COMPARISON_ONLY',
        'degree': None,
        'degree_pending': '同甲版',
        'mao_pending': '同甲版',
        'evidence': 'DTS_CITED',
        'line': 'L183-L193',
    }


# ══════════════════════════════════════════════════════════════
# 块4  通关 §二十 L250
# ══════════════════════════════════════════════════════════════
#
# DTS L250 原文:
#   「天气欲不降, 地气欲上升, 欲相和相生也。
#     木土而要火, 火金而要土, 土水而要金, 金水而要水, 皆是牛郎织女之有情也。
#     中间上下远隔, 为物所间; 前后远绝, 或被刑冲, 或被劫占, 或隔一物, 皆谓之关也。
#     必得引用无合之神及刑冲所间之物, 前后上下, 援引得来, 能胜劫占之神,
#     能补所缺之物, 明见暗会, 岁运相逢, 乃为通关也。」
#
# ★ 原文核证(六本底本逐本核, 2026-10-03):
#     DTS  木土而要火×1  火金而要土×1  土水而要金×1  金水而要水×1  ← 底本原样
#     PZZQ 通关×36 但【无映射表】(L1100「引入第三方五行居中调和」/ L4566「以第三方食伤疏导」)
#     其余四本 零映射
#   → 「金水而要水」非 OCR 错(若 OCR 错, PZZQ 会有同句可比), 是底本原样。

TONG_GUAN_MAP = [
    {
        'guan': ('木', '土'), 'tong': '火',
        'trigger': 'KE',           # 木克土 -> 成关
        'verify': WX_KE.get('木') == '土' and WX_SHENG.get('火') == '土' and WX_SHENG.get('木') == '火',
        'evidence': 'DTS_CITED', 'line': 'L250',
        'note': '木生火, 火生土 —— 木克土成关, 火通关',
    },
    {
        'guan': ('火', '金'), 'tong': '土',
        'trigger': 'KE',           # 火克金 -> 成关
        'verify': WX_KE.get('火') == '金' and WX_SHENG.get('火') == '土' and WX_SHENG.get('土') == '金',
        'evidence': 'DTS_CITED', 'line': 'L250',
        'note': '火生土, 土生金 —— 火克金成关, 土通关',
    },
    {
        'guan': ('土', '水'), 'tong': '金',
        'trigger': 'KE',           # 土克水 -> 成关
        'verify': WX_KE.get('土') == '水' and WX_SHENG.get('土') == '金' and WX_SHENG.get('金') == '水',
        'evidence': 'DTS_CITED', 'line': 'L250',
        'note': '土生金, 金生水 —— 土克水成关, 金通关',
    },
    {
        'guan': ('金', '水'), 'tong': '水',
        'trigger': 'KE',           # ★ 金【不】克水 -> 此条 inert
        # ★ 金克木(木), 不是克水 -> 成关条件不成立
        #   写成 WX_KE.get('金') == '木' 会被读成「金克木所以verify通过」, 实为 True, 是 bug。
        #   正确: verify 应为「金克水」, 即 WX_KE['金'] == '水' -> False。
        'verify': WX_KE.get('金') == '水',   # 金不克水 -> False (inert 的判据)
        'evidence': 'DTS_CITED', 'line': 'L250',
        'inert': True,
        'conflict_note': ('前三组两两相克(木克土/火克金/土克水), 构造一致; '
                          '第四组「金水」是【相生】(金生水), 水非第三方, 构造不通。'
                          '疑底本讹字。'),
        'emendation_candidate': '「金木而要水」(金克木成关, 水通关) / 未采纳 —— 无第二来源可对照(PZZQ 等五本零映射)',
        'note': ('按 DTS L250 底本原样落, 一字不改。'
                 '因触发条件为「相克」, 金水不相克 -> 此条【永不触发】(inert)。'
                 'inert 与 condition_2_pending / usable_as_criteria 同款处理: '
                 '规则在表里, 但不执行, 且冲突显式标注。'),
    },
]


def find_tong_guan(guan_a: str, guan_b: str) -> Optional[Dict[str, Any]]:
    """查通关映射。

    ★ 触发条件统一为 KE(相克) —— 前三组 DTS 明文成关, 第四组因不相克而 inert。
    """
    for m in TONG_GUAN_MAP:
        if set(m['guan']) == {guan_a, guan_b}:
            return m
    return None


def list_chong_xing_in_chart(relations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """盘级列举: 列出盘里所有 CHONG / XING 关系的实例。

    ⚠ 此函数【不判】"两个地支 a_zhi/b_zhi 之间是否成关"。
      它只做盘级事实列举 —— 参数里没有 a_zhi/b_zhi, 因为这个判定在
      check_guan_topology(块5), 需柱位映射才能做。

    ★ 块5 落码后, 本函数仍只做盘级列举; 两支判定走 check_guan_topology。

    DTS L250 原文: 「或被刑冲, 或被劫占, 或隔一物, 皆谓之关也」
    """
    reasons = []
    for rel in (relations or []):
        if rel.get("type") not in ("CHONG", "XING"):
            continue
        for iv in rel.get("instances") or []:
            if "a_pos" not in iv:
                continue                      # SELF 型不成对, 不属刑冲
            reasons.append({
                "key": "XING_CHONG",
                "type": rel["type"],
                "positions": [iv["a_pos"], iv["b_pos"]],
            })
    return {
        "items": reasons,
        "count": len(reasons),
        "scope": "CHART_LEVEL_ONLY",
        "two_branch_verdict": None,          # ← 显式声明本函数不判
        "pending": ["JIE_ZHAN"],
        "note": ("仅盘级列举; 两支成关判定见 check_guan_topology(块5)。"
                 "劫占(JIE_ZHAN)为 INFERRED, PENDING。"),
    }


# ── 关的拓扑条件常量 ──
# DTS L250「中间上下远隔, 为物所间; 前后远绝, 或被刑冲, 或被劫占, 或隔一物」
#
# ★ distance 档位映射 (ENGINE_DEFINED —— DTS 三词 vs 引擎三档, 非一一对等):
#     span_one  ← 两处明文: 「中间上下远隔, 为物所间」+「或隔一物」
#                 (两者在 L250 上下文指同一现象: 中间有物)
#     remote    ← 一处明文: 「前后远绝」
#     adjacent  ← DTS 未列为关(两支相邻不构成阻隔)

GUAN_DISTANCE_MAP = [
    {
        'distance': 'span_one',
        'dts_words': ['中间上下远隔，为物所间', '或隔一物'],
        'evidence': 'DTS_CITED', 'line': 'L250',
        'mapping': 'ENGINE_DEFINED',
        'note': '两处明文指同一现象(中间有物隔断); 非逐档一一对应',
    },
    {
        'distance': 'remote',
        'dts_words': ['前后远绝'],
        'evidence': 'DTS_CITED', 'line': 'L250',
        'mapping': 'ENGINE_DEFINED',
        'note': '前后隔断',
    },
]

# ★ 拓扑断点三类(L250 原文并列):
#     刑冲  → relations 已有 CHONG / XING        ✓
#     隔一物 → distance 档位(上表)              ✓
#     劫占  → 【INFERRED, 不落】(见契约 §4.4)
GUAN_TOPO_CONDITIONS = [
    {'key': 'XING_CHONG', 'dts': '或被刑冲', 'source': 'relations',
     'types': ['CHONG', 'XING'], 'status': 'READY'},
    {'key': 'GE_YI_WU', 'dts': '或隔一物', 'source': 'distance',
     'types': ['span_one', 'remote'], 'status': 'READY'},
    {'key': 'JIE_ZHAN', 'dts': '或被劫占', 'source': 'INFERRED',
     'types': [], 'status': 'PENDING',
     'note': ('L250 未指明「劫」是月劫还是劫财; L353「忌劫而官能去劫」提示劫=劫财(十神), '
              '但属跨语境推断。evidence: INFERRED, 不进 relations.type 枚举。'
              '「占」= 位置被占(与「隔一物」同层), 非力量比较 —— L250 三项并列可证。')},
]


# ══════════════════════════════════════════════════════════════
# 块5  关拓扑判定 (裁三十七丙 —— distance/blocked 已落, jie_zhan 未落)
# ══════════════════════════════════════════════════════════════

# engine distance 档 -> 块5 verdict 用的档名(DTS 三词 vs 三档, mapping ENGINE_DEFINED)
_DISTANCE_TIER = {'span_one': 'SPAN_ONE', 'remote': 'REMOTE'}
_TIER_ORDER = {'SPAN_ONE': 1, 'REMOTE': 2}


def _pair_instances(relations, pos_a, pos_b):
    """取 relations 里恰好连接 pos_a <-> pos_b 的成对实例。

    成对实例含 a_pos/b_pos; SELF 型无此字段, 自动跳过。
    返回 [(rel_type, instance), ...]。
    """
    out = []
    for rel in (relations or []):
        for iv in (rel.get("instances") or []):
            a, b = iv.get("a_pos"), iv.get("b_pos")
            if a is None or b is None:
                continue                       # SELF 型不成对
            if {a, b} == {pos_a, pos_b}:
                out.append((rel.get("type"), iv))
    return out


def check_guan_topology(relations: List[Dict[str, Any]],
                        guan_a: str, guan_b: str,
                        pos_of: Optional[Dict[str, List[int]]] = None
                        ) -> Dict[str, Any]:
    """判两支之间是否成关 —— DTS L250「皆谓之关也」

    接口(裁三十七定死):
        {
          'topo_ok':   bool | None,   综合判定; 有 None 项 -> None
          'conditions': {
            'distance': 'SPAN_ONE' | 'REMOTE' | None,   DTS L250 远隔/远绝/隔一物
            'blocked':  bool | None,                    刑冲阻断
            'jie_zhan': None,                           ★ PENDING 待劫占核清
          },
          'verdict':   'PASS' | 'FAIL' | 'INCOMPLETE',  有 None 项即 INCOMPLETE
          'pending':   [...],
        }

    ★ 「判不了」≠「判了为否」: 任一条件为 None 则 verdict='INCOMPLETE',
      绝不因未判而输出 FAIL。同 condition_2_pending / usable_as_criteria 处理。

    ★ pos_of: {支名: [柱位, ...]}, 由调用方传入(本层不重算四柱)。
      不传 -> distance/blocked 无法定位实例, 两者显式 None + pending。
      重复支盘取全部柱位的两两组合, 逐组判。
    """
    conditions: Dict[str, Any] = {'distance': None, 'blocked': None, 'jie_zhan': None}
    detail = {'pairs': [], 'pos_of_missing': pos_of is None}

    if pos_of is not None:
        pa_list = pos_of.get(guan_a) or []
        pb_list = pos_of.get(guan_b) or []
        tiers = []
        blocked_any = False
        for pa in pa_list:
            for pb in pb_list:
                if pa == pb:
                    continue
                lo, hi = (pa, pb) if pa < pb else (pb, pa)
                insts = _pair_instances(relations, lo, hi)
                for rtype, iv in insts:
                    if rtype in ('CHONG', 'XING'):
                        blocked_any = True
                    d = iv.get('distance')
                    if d in _DISTANCE_TIER:
                        tiers.append(_DISTANCE_TIER[d])
                detail['pairs'].append({'pos': [lo, hi], 'count': len(insts)})
        # 多柱位组合时取「最远」档(阻隔强度), 全部相等则取该值
        if tiers:
            conditions['distance'] = max(tiers, key=lambda t: _TIER_ORDER[t])
        # ★ blocked: 有实例查过才判 False; 无实例 -> None(「判不了」)
        conditions['blocked'] = blocked_any if detail['pairs'] else None

    pending = [k for k, v in conditions.items() if v is None]
    if 'jie_zhan' in pending:
        topo_ok, verdict = None, 'INCOMPLETE'
    else:
        topo_ok = bool(conditions['distance']) or bool(conditions['blocked'])
        verdict = 'PASS' if topo_ok else 'FAIL'
    return {
        'topo_ok': topo_ok,
        'conditions': conditions,
        'verdict': verdict,
        'pending': pending,
        'detail': detail,
        'evidence': 'DTS_CITED',               # 判据来源 L250
        'note': ('distance/blocked 已落(需 pos_of 柱位映射); '
                 'jie_zhan 劫占 INFERRED 未核 -> verdict 恒为 INCOMPLETE。'
                 '裁决链见契约 §4.6。'),
        'line': 'L250',
    }


# ══════════════════════════════════════════════════════════════
# 导出
# ══════════════════════════════════════════════════════════════
# ★ 下游只准调本表列出的函数。
#   check_fang_ju_ming_loose 不在表内 —— 对照版, 不供判定(裁三十八甲).
__all__ = [
    # 块2 源流
    'find_yuan_tou', 'gen_liu_cheng', 'build_yuan_liu_skeleton',
    # 块3 方局混纯 —— 只导主判据
    'check_fang_ju_ming_same_wx',
    # 块4 通关
    'find_tong_guan', 'list_chong_xing_in_chart',
    # 块5 关拓扑
    'check_guan_topology',
]