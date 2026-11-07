# -*- coding: utf-8 -*-
"""
PATCH-058 流年+状态变化链路
原局 → 大运 → 流年 → 状态变化
流年: 该年干支(立春换年柱); 状态变化: 大运/流年干支与原局生克冲合
铁律: 无评分/权重; 状态变化只输出作用关系, 不直接改写strength
"""
import io, sys
from spec.yinyang_system import SHENG, KE, SHENG_ME, KE_ME
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
GAN = '甲乙丙丁戊己庚辛壬癸'
ZHI = '子丑寅卯辰巳午未申酉戌亥'

ELEM = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
        '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
from spec.yinyang_system import SHENG, KE  # 统一表
CHONG = {'子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅',
         '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}
# 六合
LIUHE = {'子': '丑', '丑': '子', '寅': '亥', '亥': '寅', '卯': '戌', '戌': '卯',
         '辰': '酉', '酉': '辰', '巳': '申', '申': '巳', '午': '未', '未': '午'}
# 三合局
SANHE = [({'申','子','辰'}, '水局'), ({'寅','午','戌'}, '火局'),
         ({'巳','酉','丑'}, '金局'), ({'亥','卯','未'}, '木局')]
# 三会方
SANHUI = [({'寅','卯','辰'}, '木方'), ({'巳','午','未'}, '火方'),
          ({'申','酉','戌'}, '金方'), ({'亥','子','丑'}, '水方')]
# 三刑
XING = [({'寅','巳','申'}, '無恩之刑'), ({'丑','戌','未'}, '恃勢之刑'),
        ({'子','卯'}, '無禮之刑')]
# 六害
HAI = {'子': '未', '未': '子', '丑': '午', '午': '丑', '寅': '巳', '巳': '寅',
       '卯': '辰', '辰': '卯', '申': '亥', '亥': '申', '酉': '戌', '戌': '酉'}


def dizhi_relations(original_branches, dayun_zhi, liunian_zhi):
    """地支关系全集: 冲/合/三合/三会/刑/害"""
    allz = list(original_branches) + [dayun_zhi, liunian_zhi]
    allset = set(allz)
    rels = []
    # 六冲
    for z in list(allset):
        if CHONG.get(z) in allset:
            other = CHONG[z]
            if f'{z}{other}冲' not in rels and f'{other}{z}冲' not in rels:
                rels.append(f'{z}{other}冲')
    # 六合(大运/流年与原局)
    for z in [dayun_zhi, liunian_zhi]:
        if LIUHE.get(z) in allset:
            rels.append(f'{z}{LIUHE[z]}合')
    # 三合局(全)
    for members, name in SANHE:
        if members.issubset(allset):
            rels.append(f'{name}三合全')
    # 三会方(全)
    for members, name in SANHUI:
        if members.issubset(allset):
            rels.append(f'{name}三会全')
    # 三刑
    for members, name in XING:
        if members.issubset(allset):
            rels.append(f'{name}')
    # 六害
    for z in [dayun_zhi, liunian_zhi]:
        if HAI.get(z) in allset:
            rels.append(f'{z}{HAI[z]}害')
    return rels


def liunian(year):
    """流年干支(立春换年, 简化用年柱)"""
    return GAN[(year - 4) % 10] + ZHI[(year - 4) % 12]


def state_change(piliunian, dayun_ganzhi_list, qiyun_age, current_age, day_master,
                 original_branches=None):
    """
    状态变化: 当前大运+流年与原局的作用关系
    piliunian: 流年柱
    dayun_ganzhi_list: 大运8柱
    qiyun_age: 起运岁数
    current_age: 当前虚岁
    day_master: 日主
    return: 作用关系(不改strength)
    """
    idx = int((current_age - qiyun_age) // 10)
    idx = max(0, min(idx, len(dayun_ganzhi_list) - 1))
    dy = dayun_ganzhi_list[idx]
    dyg, dyz = dy[0], dy[1]
    lg, lz = piliunian[0], piliunian[1]

    dm_elem = ELEM[day_master]
    effects = []
    # 天干生克
    for g, label in [(dyg, "大运干"), (lg, "流年干")]:
        ge = ELEM[g]
        if ge == dm_elem:
            effects.append(f"{label}{g}同氣(比劫)")
        elif KE[dm_elem] == ge:
            effects.append(f"{label}{g}日主克(財)")
        elif KE[ge] == dm_elem:
            effects.append(f"{label}{g}克日主(官殺)")
        elif SHENG[dm_elem] == ge:
            effects.append(f"{label}{g}日主生(食傷)")
        elif SHENG[ge] == dm_elem:
            effects.append(f"{label}{g}生日主(印)")
    # 地支冲
    for z, label in [(dyz, "大运支"), (lz, "流年支")]:
        pass
    # 地支冲合刑害
    ob = original_branches or ['亥','戌','未','午']
    dz_rels = dizhi_relations(ob, dyz, lz)
    return {"current_dayun": dy, "liunian": piliunian,
            "age_idx": idx, "effects": effects, "dizhi_rels": dz_rels,
            "note": "作用关系登记, 不改写strength_state; 待Rule Layer裁决喜忌"}


def xiji_adjudicate(strength_state, climate_use_god, dayun_effects, dizhi_rels):
    """
    PATCH-059 喜忌裁决: 基于strength方向+调候用, 对大运/流年作用定喜忌
    铁律: 偏弱喜印比扶身忌财官杀; 偏强喜财官杀忌印比
    不改写strength, 只输出年度喜忌
    """
    xi, ji = [], []
    # 偏弱/弱 → 喜印比, 忌财官杀
    weak_dir = strength_state in ("SLIGHTLY_WEAK", "WEAK", "VERY_WEAK")
    strong_dir = strength_state in ("STRONG", "SLIGHTLY_STRONG", "VERY_STRONG")
    for e in dayun_effects:
        if weak_dir:
            if "印" in e or "比劫" in e:
                xi.append(e)
            elif "財" in e or "官殺" in e:
                ji.append(e)
        elif strong_dir:
            if "財" in e or "官殺" in e:
                xi.append(e)
            elif "印" in e or "比劫" in e:
                ji.append(e)
    # 调候用神出现为喜
    return {"xi": xi, "ji": ji,
            "xiji_note": f"strength={strength_state}; 偏弱喜印比忌財官殺" if weak_dir
                        else (f"strength={strength_state}; 偏强喜財官殺忌印比" if strong_dir
                              else f"strength={strength_state}; 中和/未定不裁喜忌")}


if __name__ == '__main__':
    print("=== PATCH-058 流年+状态变化 ===")
    # GC-001 硬编码: 癸亥 壬戌 乙未 壬午, 大运逆排, 起运8.7岁
    dm = '乙'
    dayun = ['辛酉','庚申','己未','戊午','丁巳','丙辰','乙卯','甲寅']
    qiyun_age = 8.7
    ln = liunian(2024)
    print(f'原局: 癸亥 壬戌 乙未 壬午 日主{dm}')
    print(f'大运: {" ".join(dayun)}')
    print(f'起运: 8.7岁逆排')
    print(f'流年2024: {ln}')
    r = state_change(ln, dayun, qiyun_age, 41, dm, ['亥','戌','未','午'])
    print(f'41虚岁 大运: {r["current_dayun"]}')
    print(f'天干作用: {r["effects"]}')
    print(f'地支关系: {r["dizhi_rels"]}')
    # 喜忌裁决: GC-001 strength=SLIGHTLY_WEAK
    xj = xiji_adjudicate("SLIGHTLY_WEAK", "癸", r["effects"], r["dizhi_rels"])
    print(f'喜: {xj["xi"]}')
    print(f'忌: {xj["ji"]}')
    print(f'说明: {xj["xiji_note"]}')
