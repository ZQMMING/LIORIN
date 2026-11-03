# -*- coding: utf-8 -*-
"""
PATCH-054 大运流年排盘（SMTH 岁运体系）
- 阳男阴女顺排，阴男阳女逆排
- 大运从月柱起
- 起运数: 生日到节令天数/3
"""
import sys
sys.path.insert(0, r'engines\common')
from gc002_builder import paipan

GAN = '甲乙丙丁戊己庚辛壬癸'
ZHI = '子丑寅卯辰巳午未申酉戌亥'
# 月柱表（五虎遁）
YEAR_TO_MONTH_START = {'甲': '丙寅', '己': '丙寅', '乙': '戊寅', '庚': '戊寅',
                       '丙': '庚寅', '辛': '庚寅', '丁': '壬寅', '壬': '壬寅',
                       '戊': '甲寅', '癸': '甲寅'}


def dayun(dayun_count):
    """从月柱起，顺/逆推 dayun_count 步"""
    pass


def qiyun(y, m, d, hour, gender, year_gan):
    """
    起运：阴阳年+性别定顺逆
    阳年(甲丙戊庚壬)男/阴年(乙丁己辛癸)女=顺排
    阴年男/阳年女=逆排
    返回大运列表(每柱10年)
    """
    # 年干阴阳
    yang_year = GAN.index(year_gan) % 2 == 0
    male = (gender == '男')
    shun = yang_year == male  # 阳男阴女顺
    return shun


if __name__ == '__main__':
    print("=== 054 大运排盘测试 ===")
    # GC-001: 1983-11-03 11:30 男 癸亥年
    p = paipan(1983, 11, 3, 11)
    print(f'GC-001: {p["pillars"]}')
    year_gan = p['stems']['年']
    shun = qiyun(1983, 11, 3, 11, '男', year_gan)
    print(f'年干{year_gan}({"阳" if GAN.index(year_gan)%2==0 else "阴"}) 男 → {"顺排" if shun else "逆排"}')
    # 月柱 壬戌，逆排大运：辛酉 庚申 己未 戊午 丁巳...
    month_gz = p['stems']['月'] + p['month_order']
    gi = GAN.index(p['stems']['月'])
    zi = ZHI.index(p['month_order'])
    direction = 1 if shun else -1
    dayuns = []
    for i in range(1, 9):
        g = GAN[(gi + direction * i) % 10]
        z = ZHI[(zi + direction * i) % 12]
        dayuns.append(f'{g}{z}')
    print(f'月柱{month_gz} → 大运: {" ".join(dayuns)}')
    print(f'起运方向: {"顺" if shun else "逆"}')
