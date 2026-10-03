# -*- coding: utf-8 -*-
"""第3刀: 源流骨架(步骤1-2) + 通关映射

依据: DTS §十九 源流 L245 / §二十 通关 L250
契约: p0_v2/l3_contract_spec.md v1.3 §四

★ 落法铁律(契约 §4.0):
  路径生成只准用现有 WX_SHENG / WX_KE 两张映射表逐步递推,
  【禁止】引入邻接矩阵 / 邻接表 / 节点类等显式图数据结构。
  DTS 无「图」, 只有散句; 算法可以是路径搜索, 图的表示不显式化。
"""
from typing import Any, Dict, List, Optional, Tuple

# ── 五行映射(复用现有 transit_power 表, 不新建) ──
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}   # 我生
WX_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}      # 我克
WX = ('木', '火', '土', '金', '水')

# ══════════════════════════════════════════════════════════════
# 一、源流 §十九 L245 (步骤 1-2)
# ══════════════════════════════════════════════════════════════

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
# 二、通关 §二十 L250
# ══════════════════════════════════════════════════════════════

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


# ── 关的拓扑条件 ──
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

# ★ 拓扑断点三类(L250 原文并列, 本刀可算的两类):
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


def list_chong_xing_in_chart(relations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """盘级列举: 列出盘里所有 CHONG / XING 关系的实例。

    ⚠ 此函数【不判】"两个地支 a_zhi/b_zhi 之间是否成关"。
      它只做盘级事实列举 —— 参数里没有 a_zhi/b_zhi, 因为这个判定尚未实现。

    ★ TODO(契约 §4.5): 两支判定待实现
        需 relations.instances[k].positions(柱位) + 柱位→地支映射,
        才能判「这两支之间有没有刑冲」而非「盘里有没有刑冲」。
        触发条件: topology_paths 接入 L3/L4 时。

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
        "two_branch_verdict": None,          # ← 显式声明未实现
        "pending": ["JIE_ZHAN", "TWO_BRANCH_VERDICT"],
        "note": ("仅盘级列举; 两支成关判定未实现(需 positions + 柱位映射)。"
                 "劫占(JIE_ZHAN)为 INFERRED, PENDING。"),
    }
