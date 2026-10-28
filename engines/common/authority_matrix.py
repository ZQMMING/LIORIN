# -*- coding: utf-8 -*-
"""六经典 Authority Matrix v0.2.
定义每个命理元的 Primary/Secondary/Alternate 轨道归属.
v0.2增强: 每个元增加 judgment_criteria(判定依据原文引用) + independent_method_systems(独立方法体系分析).
Authority Matrix 只做轨道归属, 不做综合裁决.
3条铁律:
1. Authority Matrix 只做轨道归属, 不做综合裁决
2. 旺衰/强弱保持结构事实+证据+规则, 不擅自形成综合裁决
3. wangshuai_multidim 标记为 Legacy/Reference, 不立即删除
"""
from typing import Dict, List, Any, Optional


# 六经典标识
CLASSIC_BOOKS = {
    'PZZQ': '子平真诠',
    'YHZP': '渊海子平',
    'DTS': '滴天髓',
    'QTBJ': '穷通宝鉴',
    'SFTK': '神峰通考',
    'SMTH': '三命通会',
}


# 命理元定义
META_DEFINITIONS = {
    'WANG_SHUAI': {
        'meta_id': 'WANG_SHUAI',
        'meta_name': '旺衰',
        'definition': '日主是否得时/失时, 即月令维度的五行之气状态. '
                      '《子平真诠》: "得时为旺, 失时为衰". '
                      '旺衰 ≠ 强弱, 可以"虽旺而弱", 也可以"虽衰而强".',
        'primary_track': 'PZZQ',
        'secondary_tracks': ['YHZP'],
        'alternate_tracks': ['DTS'],
        'activation_condition': 'always',
        'boundary_note': '旺衰只回答得令/失令, 不回答身强/身弱. '
                         '不得旺→自动强, 衰→自动弱. '
                         '最终强弱裁决 NOT_AUTHORIZED.',
        # v0.2新增: 判定依据原文引用
        'judgment_criteria': {
            'PZZQ': [
                '得时为旺, 失时为衰',
                '论十干得时不旺失时不弱: 得时俱为旺论, 失时便作衰看, 虽是至理, 亦死法也',
                '得时衰旺须浑参四柱, 不可执一',
            ],
            'YHZP': [
                '得令即旺的朴素体系: 日干在月令得长生禄旺即为旺',
            ],
            'DTS': [
                '旺衰篇: 五行流通配合, 旺衰须参全局',
                '比劫之旺衰视提纲财神喜神轻重',
            ],
        },
        # v0.2新增: 独立方法体系分析
        'independent_method_systems': {
            'PZZQ': {
                'has_independent_system': True,
                'system_name': '得时不旺失时不弱专章',
                'core_idea': '旺衰是月令维度, 须浑参四柱, 不可执一',
                'boundary': '只论得令/失令, 不论身强/身弱',
            },
            'YHZP': {
                'has_independent_system': True,
                'system_name': '得令即旺朴素体系',
                'core_idea': '日干在月令得长生禄旺即为旺',
                'boundary': '朴素判断, 未区分旺衰与强弱',
            },
            'DTS': {
                'has_independent_system': True,
                'system_name': '五行流通配合旺衰',
                'core_idea': '旺衰须参全局五行流通, 非独看月令',
                'boundary': '旺衰与体用扶抑结合论述',
            },
        },
        'evidence_refs': [
            'PZZQ-论十干得时不旺失时不弱',
            'YHZP-论旺衰',
            'DTS-旺衰篇',
        ],
    },
    'QIANG_RUO': {
        'meta_id': 'QIANG_RUO',
        'meta_name': '强弱',
        'definition': '日主的力量结构, 即党众/助寡维度. '
                      '《子平真诠》: "党众为强, 助寡为弱". '
                      '强弱 = 得地(根气) + 得势(帮扶) + 泄耗 + 克制 的多维结构. '
                      '强弱 ≠ 旺衰, 可以"虽旺而弱", 也可以"虽衰而强".',
        'primary_track': 'PZZQ',
        'secondary_tracks': ['YHZP'],
        'alternate_tracks': ['DTS'],
        'activation_condition': 'always',
        'boundary_note': '强弱输出多维结构事实(得地/得势/泄耗/克制), '
                         '不输出单一的身强/身弱综合裁决. '
                         'Strength Resolver (160-B) NOT_AUTHORIZED. '
                         'wangshuai_multidim 标记为 Legacy/Reference, 待 Authority Matrix 验证.',
        'judgment_criteria': {
            'PZZQ': [
                '党众为强, 助寡为弱',
                '日主不必月令禄旺, 四柱得长生禄刃库根即不弱',
                '长生禄刃根重墓库余气根轻, 干多不如根重',
                '阳干逢库即通根身库, 不必求冲开',
            ],
            'DTS': [
                '壬水通根申子辰又透癸则奔冲',
                '木逢火多须辰为湿根, 水多须寅为纳根',
                '乙木得丙丁火, 则不畏申酉金',
                '冬木虚湿又被金水交伤, 虽坐午火难发生',
            ],
            'YHZP': [
                '身强身弱的朴素判断: 得地得势为强, 失地失势为弱',
            ],
        },
        'independent_method_systems': {
            'PZZQ': {
                'has_independent_system': True,
                'system_name': '旺衰强弱分别论',
                'core_idea': '强弱是党众/助寡维度, 与旺衰(得令/失令)分离',
                'boundary': '只论结构事实, 不论综合裁决',
            },
            'DTS': {
                'has_independent_system': True,
                'system_name': '体用扶抑体系',
                'core_idea': '强弱须参通根透干、气势流通、泄耗克制',
                'boundary': '强弱与体用扶抑结合论述',
            },
            'YHZP': {
                'has_independent_system': False,
                'system_name': '朴素身强身弱',
                'core_idea': '得地得势为强, 失地失势为弱',
                'boundary': '朴素判断, 未与旺衰严格分离',
            },
        },
        'evidence_refs': [
            'PZZQ-论旺衰强弱分别',
            'YHZP-论身强身弱',
            'DTS-体用篇',
        ],
    },
    'GE_JU': {
        'meta_id': 'GE_JU',
        'meta_name': '格局',
        'definition': '月令定格, 以月令之财官印食杀伤六神分六格. '
                      '《子平真诠》: "八字用神, 专求月令". '
                      '格局是结构识别, 不等于格局成立, 不等于格局高低.',
        'primary_track': 'PZZQ',
        'secondary_tracks': ['YHZP'],
        'alternate_tracks': ['SMTH'],
        'activation_condition': '月令有可用之神(月令藏干透干或成格)',
        'boundary_note': '格局只输出格神候选和结构识别, '
                         '不输出格局成立/格局高低/富贵贫贱. '
                         '格清/配合保持 PLACEHOLDER. '
                         '相神暂不实现, 保留为后续独立刀.',
        'judgment_criteria': {
            'PZZQ': [
                '八字用神, 专求月令',
                '八字用神专求月令, 顺用财官印食逆用煞伤刃劫',
                '财官印食为用神之善者, 当顺而用之; 煞伤刃劫为用神之不善者, 当逆而用之',
                '格局高低在有情无情有力无力, 非成格即贵',
                '成败可逆: 因成得败/因败得成',
                '格局成败须参气候寒暖, 调候急则权用',
                '杂气格在透干会支取清; 合而有情吉无情不吉',
            ],
            'YHZP': [
                '格局基础分类: 内格外格正格变格',
            ],
            'SMTH': [
                '月令取格, 六格大纲',
                '财官印绶分偏正兼食神以定八格',
            ],
        },
        'independent_method_systems': {
            'PZZQ': {
                'has_independent_system': True,
                'system_name': '八格体系(格局成败救应变化纯杂)',
                'core_idea': '月令定格, 顺用逆用, 格局成败救应变化纯杂六维论格',
                'boundary': '只论格神候选和结构识别, 不论格局成立/高低',
            },
            'YHZP': {
                'has_independent_system': True,
                'system_name': '格局基础分类',
                'core_idea': '内格外格正格变格的基础分类',
                'boundary': '分类较粗, 未深入成败救应',
            },
            'SMTH': {
                'has_independent_system': True,
                'system_name': '月令取格六格大纲',
                'core_idea': '月令取格, 六格大纲, 兼论纳音格局',
                'boundary': '格局分类与子平真诠略有不同',
            },
        },
        'evidence_refs': [
            'PZZQ-论八格',
            'PZZQ-论用神成败救应',
            'PZZQ-论用神变化',
            'PZZQ-论用神纯杂',
            'YHZP-论格局',
            'SMTH-六格大纲',
        ],
    },
    'DIAO_HOU': {
        'meta_id': 'DIAO_HOU',
        'meta_name': '调候',
        'definition': '月令气候寒暖燥湿与日干所需调候. '
                      '《穷通宝鉴》: 通篇以月令气候定取用先后. '
                      '调候是气候所需, 不等于用神最终裁决.',
        'primary_track': 'QTBJ',
        'secondary_tracks': ['SMTH'],
        'alternate_tracks': [],
        'activation_condition': '生于亥子丑或巳午未, 且原局气候极端(调候所需五行极弱或无)',
        'boundary_note': '调候只输出调候候选和气候修正, '
                         '不输出用神最终裁决. '
                         'D5/T16 月令效力修正已接入, 修正月令效力未做.',
        'judgment_criteria': {
            'QTBJ': [
                '五行调候贵在寒暖燥湿相济得所, 戒太过与不及',
                '水性寒润, 阴极生寒而成水; 火性温热, 阳极生热而成火',
                '木赖水滋润, 水少则滋养得当',
                '春木余寒, 喜火温暖则无盘屈',
                '九月乙木, 根枯叶落, 必赖癸水滋养',
            ],
            'PZZQ': [
                '论命惟以月令用神为主, 然亦须配气候而互参之',
                '木逢冬水虽透官星亦难准贵, 盖金寒而水益冻, 冻水不生木',
                '气有衰旺, 取用不同; 春木逢火不利见官, 秋金遇水见官无碍',
                '春木逢火则为木火通明, 夏木不作此论; 秋金遇水则为金水相涵, 冬金不作此论',
            ],
            'SMTH': [
                '调候基础: 寒暖燥湿得中',
            ],
        },
        'independent_method_systems': {
            'QTBJ': {
                'has_independent_system': True,
                'system_name': '四时调候体系(按干按月论述)',
                'core_idea': '十干十二月令逐干逐月论调候取用, 寒暖燥湿相济得所',
                'boundary': '只论调候候选, 不论用神最终裁决',
            },
            'PZZQ': {
                'has_independent_system': False,
                'system_name': '气候互参',
                'core_idea': '月令用神为主, 须配气候互参',
                'boundary': '调候是辅助维度, 非独立体系',
            },
            'SMTH': {
                'has_independent_system': False,
                'system_name': '调候基础',
                'core_idea': '寒暖燥湿得中的基础论述',
                'boundary': '基础论述, 未形成系统方法',
            },
        },
        'evidence_refs': [
            'QTBJ-四时调候',
            'QTBJ-十干十二月令调候取用',
            'PZZQ-论用神配气候得失',
            'SMTH-论调候',
        ],
    },
    'BING_YAO': {
        'meta_id': 'BING_YAO',
        'meta_name': '病药',
        'definition': '命局中存在的破坏平衡的有害之神(病), '
                      '以及能够克制去除病神的字(药). '
                      '《神峰通考》: "有病方为贵, 无伤不是奇". '
                      '病药是病机诊断, 不等于用神最终裁决.',
        'primary_track': 'SFTK',
        'secondary_tracks': ['DTS'],
        'alternate_tracks': [],
        'activation_condition': '存在明显病(伤官见官/七杀攻身/枭神夺食/财多身弱/比劫夺财), 且病无制无化',
        'boundary_note': '病药只输出病机和药神候选, '
                         '不输出用神最终裁决. '
                         'bingyao_layer 已实现(命局病机药神枚举+应期去病添病).',
        'judgment_criteria': {
            'SFTK': [
                '有病方為貴、無傷不是奇；格中如去病，財祿兩相隨',
                '病者八字中本來損害全局之神',
                '藥者得一字以去其病之字',
                '用財格見比劫奪財, 以官殺制比劫為藥',
                '用食傷而印奪食, 以財破印為藥',
                '七杀须食伤制伏，制过犹不及',
                '若病重而得藥，為大富大貴之人',
                '雕猶玉未琢金未煉, 官星未見傷官財星未見比劫之純全狀',
                '弱謂氣虧而有根, 弱則有旺之基; 旺謂類聚而氣專, 非泛泛之旺',
            ],
            'DTS': [
                '病药相关论述: 忌神展转相攻为结构受害之象',
                '忌神深固入脏位为最重之克',
            ],
        },
        'independent_method_systems': {
            'SFTK': {
                'has_independent_system': True,
                'system_name': '病药体系(张楠核心思想)',
                'core_idea': '有病方为贵, 无伤不是奇; 病=损害全局之神, 药=去其病之字; 四病(雕/枯/弱/旺)分类',
                'boundary': '只论病机和药神候选, 不论用神最终裁决',
            },
            'DTS': {
                'has_independent_system': False,
                'system_name': '病药相关论述',
                'core_idea': '忌神为病, 制忌之神为药的相关论述',
                'boundary': '散见各篇, 未形成独立病药体系',
            },
        },
        'evidence_refs': [
            'SFTK-病药说',
            'SFTK-四病分类(雕枯弱旺)',
            'DTS-病药相关',
        ],
    },
    'YONG_SHEN': {
        'meta_id': 'YONG_SHEN',
        'meta_name': '用神',
        'definition': '用神有多种, 不能混为一谈: '
                      '格局用神(子平真诠月令定格)、调候用神(穷通宝鉴气候所需)、'
                      '病药用神(神峰通考去病之药)、扶抑用神(滴天髓体用扶抑). '
                      '用神是多轨并行, 不是单一答案.',
        'primary_track': 'PZZQ',
        'secondary_tracks': ['QTBJ'],
        'alternate_tracks': ['SFTK', 'DTS'],
        'activation_condition': '格局轨/调候轨/病药轨/体用轨任一激活',
        'boundary_note': '用神四轨并行, 冲突保留不裁决. '
                         '不输出单一的最终用神. '
                         'yongshen_multi_track 已实现, 命中率@K 100%. '
                         '渊海子平/三命通会降级为基础事实校验层, 不作为独立用神轨道.',
        'judgment_criteria': {
            'PZZQ': [
                '八字用神专求月令, 顺用财官印食逆用煞伤刃劫',
                '八字用神专求月令，以日干配月令地支而生克不同',
                '财官印食为用神之善者，当顺而用之; 煞伤刃劫为用神之不善者，当逆而用之',
                '不统归月令即混格同论, 执假失真',
                '月令本主不透而透他藏则用神变化',
                '当顺而顺当逆而逆，配合得宜皆成贵格结构',
                '互用两相得为纯, 两不相谋为杂',
            ],
            'QTBJ': [
                '调候用神: 四时调候, 气候所需之神',
                '九月乙木, 根枯叶落, 必赖癸水滋养',
            ],
            'SFTK': [
                '病药用神: 去病之药即为用神',
                '若病重而得藥，為大富大貴之人',
            ],
            'DTS': [
                '扶抑用神: 体用扶抑, 日主乘用神驰骋无私意牵制',
                '用神多现则气不专',
                '忌神展转相攻为结构受害之象',
            ],
        },
        'independent_method_systems': {
            'PZZQ': {
                'has_independent_system': True,
                'system_name': '格局用神(月令用神)',
                'core_idea': '八字用神专求月令, 顺用逆用, 用神成败救应变化纯杂',
                'boundary': '只论格局用神, 非最终用神',
            },
            'QTBJ': {
                'has_independent_system': True,
                'system_name': '调候用神(气候用神)',
                'core_idea': '四时调候, 气候所需之神即为调候用神',
                'boundary': '只论调候用神, 非最终用神',
            },
            'SFTK': {
                'has_independent_system': True,
                'system_name': '病药用神(去病之药)',
                'core_idea': '有病方为贵, 去病之药即为用神',
                'boundary': '只论病药用神, 非最终用神',
            },
            'DTS': {
                'has_independent_system': True,
                'system_name': '扶抑用神(体用扶抑)',
                'core_idea': '体用扶抑, 日主乘用神驰骋, 用神多现则气不专',
                'boundary': '只论扶抑用神, 非最终用神',
            },
        },
        'evidence_refs': [
            'PZZQ-论用神',
            'PZZQ-论用神成败救应',
            'QTBJ-调候用神',
            'SFTK-病药用神',
            'DTS-扶抑用神',
        ],
    },
}


def get_meta_definition(meta_id: str) -> Optional[Dict[str, Any]]:
    """获取命理元定义."""
    return META_DEFINITIONS.get(meta_id)


def get_all_meta_ids() -> List[str]:
    """获取所有命理元ID."""
    return list(META_DEFINITIONS.keys())


def get_tracks_for_meta(meta_id: str) -> Dict[str, Any]:
    """获取命理元的轨道归属."""
    meta = META_DEFINITIONS.get(meta_id)
    if not meta:
        return {}
    return {
        'primary': meta['primary_track'],
        'secondary': meta['secondary_tracks'],
        'alternate': meta['alternate_tracks'],
    }


def get_judgment_criteria(meta_id: str, classic: str = None) -> Dict[str, List[str]]:
    """获取命理元的判定依据原文引用."""
    meta = META_DEFINITIONS.get(meta_id)
    if not meta:
        return {}
    criteria = meta.get('judgment_criteria', {})
    if classic:
        return {classic: criteria.get(classic, [])}
    return criteria


def get_independent_method_systems(meta_id: str) -> Dict[str, Any]:
    """获取命理元的独立方法体系分析."""
    meta = META_DEFINITIONS.get(meta_id)
    if not meta:
        return {}
    return meta.get('independent_method_systems', {})


def is_track_activated(meta_id: str, facts: Dict[str, Any]) -> bool:
    """检查轨道是否激活(简化版, 后续细化)."""
    meta = META_DEFINITIONS.get(meta_id)
    if not meta:
        return False
    if meta['activation_condition'] == 'always':
        return True
    return True


def get_authority_matrix_summary() -> Dict[str, Any]:
    """获取 Authority Matrix 摘要."""
    summary = {}
    for meta_id, meta in META_DEFINITIONS.items():
        summary[meta_id] = {
            'name': meta['meta_name'],
            'primary': CLASSIC_BOOKS.get(meta['primary_track'], meta['primary_track']),
            'secondary': [CLASSIC_BOOKS.get(t, t) for t in meta['secondary_tracks']],
            'alternate': [CLASSIC_BOOKS.get(t, t) for t in meta['alternate_tracks']],
            'activation': meta['activation_condition'],
            'has_judgment_criteria': bool(meta.get('judgment_criteria')),
            'has_independent_method_systems': bool(meta.get('independent_method_systems')),
        }
    return summary


# Authority Matrix 版本
AUTHORITY_MATRIX_VERSION = 'v0.2'
AUTHORITY_MATRIX_BOUNDARY_NOTE = (
    'Authority Matrix 只做轨道归属, 不做综合裁决. '
    '旺衰/强弱保持结构事实+证据+规则, 不擅自形成综合裁决. '
    'wangshuai_multidim 标记为 Legacy/Reference, 待 Authority Matrix 验证.'
    'v0.2增强: 每个元增加 judgment_criteria(判定依据原文引用) + '
    'independent_method_systems(独立方法体系分析).'
)
