# -*- coding: utf-8 -*-
"""天干强弱修正(V7.24第一步)
原著依据: 《滴天髓·天干》"五阳皆阳丙为最, 五阴皆阴癸为至"
性质: 修正层, 不是替换层. 原五行级力量评估不变, 增加天干强弱修正作为辅助输出
"""
import sys
sys.path.insert(0, '.')

# 十天干强弱质性表(从《滴天髓·天干》章提取)
STEM_STRENGTH = {
    '甲': {'modifier': +1, 'description': '甲木参天, 脱胎要火', 'provenance': 'DIRECT(滴天髓)'},
    '乙': {'modifier': -1, 'description': '乙木虽柔, 刲羊解牛', 'provenance': 'DIRECT(滴天髓)'},
    '丙': {'modifier': +2, 'description': '丙火猛烈, 欺霜侮雪, 五阳皆阳丙为最', 'provenance': 'DIRECT(滴天髓)'},
    '丁': {'modifier': -1, 'description': '丁火柔中, 内性昭融', 'provenance': 'DIRECT(滴天髓)'},
    '戊': {'modifier': +1, 'description': '戊土固重, 既中且正', 'provenance': 'DIRECT(滴天髓)'},
    '己': {'modifier': -1, 'description': '己土卑湿, 中正蓄藏', 'provenance': 'DIRECT(滴天髓)'},
    '庚': {'modifier': +1, 'description': '庚金带煞, 刚健为最', 'provenance': 'DIRECT(滴天髓)'},
    '辛': {'modifier': -1, 'description': '辛金软弱, 温润而清', 'provenance': 'DIRECT(滴天髓)'},
    '壬': {'modifier': +1, 'description': '壬水通河, 能泄金气', 'provenance': 'DIRECT(滴天髓)'},
    '癸': {'modifier': -2, 'description': '癸水至弱, 达于天津, 五阴皆阴癸为至', 'provenance': 'DIRECT(滴天髓)'},
}

def get_stem_strength_modifier(daymaster_stem: str) -> dict:
    """获取天干强弱修正"""
    info = STEM_STRENGTH.get(daymaster_stem, {'modifier': 0, 'description': '未知天干', 'provenance': 'UNKNOWN'})
    return {
        'stem': daymaster_stem,
        'modifier': info['modifier'],
        'description': info['description'],
        'provenance': info['provenance'],
        'note': '修正层, 不改变原五行级力量评估',
    }

if __name__ == '__main__':
    # 测试
    for stem in ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']:
        result = get_stem_strength_modifier(stem)
        print(f"{stem}: modifier={result['modifier']:+d} | {result['description']}")
