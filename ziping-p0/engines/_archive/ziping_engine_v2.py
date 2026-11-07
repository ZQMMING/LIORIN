# -*- coding: utf-8 -*-
"""
子平引擎 v2.0 完整版
纯布尔枚举, 0浮点
完整八字排盘+旺衰+格局+用神
"""
from typing import Dict, List, Any

# 五行生克
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

# 天干
GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
GAN_YANG = {'甲':True,'乙':False,'丙':True,'丁':False,'戊':True,'己':False,'庚':True,'辛':False,'壬':True,'癸':False}

# 地支
ZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
ZHI_WX = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}

# 地支藏干
ZHI_CANG = {
    '子': ['癸'],
    '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '庚', '戊'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲'],
}

# 六合
LIU_HE = {
    '甲': '己', '己': '甲',
    '乙': '庚', '庚': '乙',
    '丙': '辛', '辛': '丙',
    '丁': '壬', '壬': '丁',
    '戊': '癸', '癸': '戊',
}

# 六冲
LIU_CHONG = {
    '子': '午', '午': '子',
    '丑': '未', '未': '丑',
    '寅': '申', '申': '寅',
    '卯': '酉', '酉': '卯',
    '辰': '戌', '戌': '辰',
    '巳': '亥', '亥': '巳',
}


def get_shi_shen(day_master: str, other_gan: str) -> str:
    """十神判定"""
    dm_wx = GAN_WX[day_master]
    ot_wx = GAN_WX[other_gan]
    dm_yang = GAN_YANG[day_master]
    ot_yang = GAN_YANG[other_gan]
    
    if ot_wx == dm_wx:
        return '比肩' if (dm_yang == ot_yang) else '劫财'
    elif SHENG.get(ot_wx) == dm_wx:
        return '正印' if (dm_yang != ot_yang) else '偏印'
    elif SHENG.get(dm_wx) == ot_wx:
        return '食神' if (dm_yang == ot_yang) else '伤官'
    elif KE.get(dm_wx) == ot_wx:
        return '偏财' if (dm_yang == ot_yang) else '正财'
    elif KE.get(ot_wx) == dm_wx:
        return '七杀' if (dm_yang == ot_yang) else '正官'
    return '未知'


def check_root(day_master: str, branches: List[str]) -> Dict[str, Any]:
    """通根检查(纯布尔)"""
    dm_wx = GAN_WX[day_master]
    roots = []
    for zhi in branches:
        cang = ZHI_CANG.get(zhi, [])
        if day_master in cang:
            roots.append({'branch': zhi, 'type': '本气' if cang[0] == day_master else '余气'})
    return {
        'has_root': len(roots) > 0,
        'root_count': len(roots),
        'roots': roots,
    }


def check_zhuanwang(day_master: str, branches: List[str]) -> Dict[str, Any]:
    """专旺格检查"""
    dm_wx = GAN_WX[day_master]
    
    # 三合局
    sanhe_map = {
        '木': ['亥', '卯', '未'],
        '火': ['寅', '午', '戌'],
        '金': ['巳', '酉', '丑'],
        '水': ['申', '子', '辰'],
    }
    
    # 三会局
    sanhui_map = {
        '木': ['寅', '卯', '辰'],
        '火': ['巳', '午', '未'],
        '金': ['申', '酉', '戌'],
        '水': ['亥', '子', '丑'],
    }
    
    for wx, ju in sanhe_map.items():
        if all(b in branches for b in ju):
            return {'is_zhuanwang': True, 'type': '三合', 'wuxing': wx}
    
    for wx, ju in sanhui_map.items():
        if all(b in branches for b in ju):
            return {'is_zhuanwang': True, 'type': '三会', 'wuxing': wx}
    
    return {'is_zhuanwang': False}


def get_yongshen(day_master: str, wx_count: Dict[str, int], root: Dict, zhuanwang: Dict) -> Dict[str, Any]:
    """用神忌神判定(纯布尔枚举)"""
    dm_wx = GAN_WX[day_master]
    
    # 专旺格
    if zhuanwang['is_zhuanwang']:
        zw_wx = zhuanwang['wuxing']
        return {
            'pattern': '专旺格',
            'yongshen': zw_wx,
            'xishen': SHENG.get(zw_wx),
            'jishen': KE.get(zw_wx),
            'reason': '专旺格, 顺其气势',
        }
    
    root_count = root['root_count']
    
    # 印旺身弱判定
    REVERSE_SHENG = {v: k for k, v in SHENG.items()}
    yin_wx = REVERSE_SHENG.get(dm_wx)
    yin_count = wx_count.get(yin_wx, 0)
    
    if yin_count >= 3 and root_count <= 1:
        # 印过旺, 身弱 → 水多木漂
        return {
            'pattern': '印旺身弱',
            'yongshen': KE.get(yin_wx),  # 制印=财
            'xishen': dm_wx,  # 比劫
            'jishen': yin_wx,  # 印
            'reason': f'印({yin_wx})过旺, 身弱, 用财制印',
        }
    
    if root_count == 0:
        return {
            'pattern': '身弱',
            'yongshen': yin_wx,
            'xishen': dm_wx,
            'jishen': KE.get(dm_wx),
            'reason': '无根身弱, 用印比',
        }
    elif root_count >= 2:
        return {
            'pattern': '身强',
            'yongshen': KE.get(dm_wx),
            'xishen': SHENG.get(KE.get(dm_wx)),
            'jishen': yin_wx,
            'reason': '有根身强, 用财官',
        }
    else:
        return {
            'pattern': '中和',
            'yongshen': '待定',
            'xishen': '待定',
            'jishen': '待定',
            'reason': '中和, 需细判',
        }


def analyze_bazi(year: str, month: str, day: str, hour: str) -> Dict[str, Any]:
    """完整八字分析"""
    day_master = day[0]
    branches = [year[1], month[1], day[1], hour[1]]
    
    # 1. 五行统计(纯计数)
    wx_count = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}
    for g in [year[0], month[0], day[0], hour[0]]:
        wx_count[GAN_WX[g]] += 1
    for z in branches:
        wx_count[ZHI_WX[z]] += 1
    
    # 2. 十神统计
    shi_shen = {}
    for g in [year[0], month[0], hour[0]]:
        ss = get_shi_shen(day_master, g)
        shi_shen[ss] = shi_shen.get(ss, 0) + 1
    
    # 3. 通根
    root = check_root(day_master, branches)
    
    # 4. 专旺格
    zw = check_zhuanwang(day_master, branches)
    
    # 5. 用神忌神
    yongshen = get_yongshen(day_master, wx_count, root, zw)
    
    return {
        'day_master': day_master,
        'day_master_wuxing': GAN_WX[day_master],
        'wuxing_count': wx_count,
        'shi_shen_count': shi_shen,
        'root': root,
        'zhuanwang': zw,
        'yongshen': yongshen,
    }


if __name__ == '__main__':
    # 测试: 1983-11-3 12点男中山 = 癸亥 壬戌 乙未 壬午
    result = analyze_bazi('癸亥', '壬戌', '乙未', '壬午')
    print('=== 八字分析 ===')
    print(f"日主: {result['day_master']} ({result['day_master_wuxing']})")
    print(f"五行计数: {result['wuxing_count']}")
    print(f"十神计数: {result['shi_shen_count']}")
    print(f"通根: {result['root']}")
    print(f"专旺: {result['zhuanwang']}")
    print()
    print('=== 用神忌神 ===')
    ys = result['yongshen']
    print(f"格局: {ys['pattern']}")
    print(f"用神: {ys['yongshen']}")
    print(f"喜神: {ys['xishen']}")
    print(f"忌神: {ys['jishen']}")
    print(f"理由: {ys['reason']}")
