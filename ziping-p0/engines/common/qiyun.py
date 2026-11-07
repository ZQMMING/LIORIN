# -*- coding: utf-8 -*-
"""
PATCH-057 起运岁数精确化
规则(子平): 阳男阴女顺数到下一節令, 阴男阳女逆数到上一節令; 3天=1歲, 1天=4月, 1时辰=10天
"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 24节气公历近似日(月,日)
JIEQI = [
    (2,4),(2,19),(3,6),(3,21),(4,5),(4,20),(5,6),(5,21),(6,6),(6,21),
    (7,7),(7,23),(8,8),(8,23),(9,8),(9,23),(10,8),(10,23),(11,7),(11,22),
    (12,7),(12,22),(1,6),(1,20)
]
# 节令(非中气)表: 立春惊蛰清明立夏芒种小暑立秋白露寒露立冬大雪小寒
JIE = [(2,4),(3,6),(4,5),(5,6),(6,6),(7,7),(8,8),(9,8),(10,8),(11,7),(12,7),(1,6)]


def to_doy(m, d, y):
    """月日→当年积日"""
    md = [31,28,31,30,31,30,31,31,30,31,30,31]
    if (y % 4 == 0 and y % 100 != 0) or y % 400 == 0:
        md[1] = 29
    return sum(md[:m-1]) + d


def nearest_jie(y, m, d, direction):
    """direction=1 下一節, -1 上一節"""
    target = to_doy(m, d, y)
    # 列本年+跨年的節日积日
    jie_list = []
    for jm, jd in JIE:
        jie_list.append((to_doy(jm, jd, y), jm, jd))
    jie_list.sort()
    if direction == 1:
        nxt = [x for x in jie_list if x[0] > target]
        if not nxt:
            return (to_doy(JIE[0][0], JIE[0][1], y+1), JIE[0][0], JIE[0][1], 1)
        return (nxt[0][0], nxt[0][1], nxt[0][2], 0)
    else:
        prv = [x for x in jie_list if x[0] < target]
        if not prv:
            # 上一年最后一節小寒
            prev_jie = (to_doy(JIE[-1][0], JIE[-1][1], y-1), JIE[-1][0], JIE[-1][1], -1)
            return prev_jie
        return (prv[-1][0], prv[-1][1], prv[-1][2], 0)


def qiyun_age(y, m, d, gender, year_gan):
    """起运岁数"""
    GAN = '甲乙丙丁戊己庚辛壬癸'
    yang_year = GAN.index(year_gan) % 2 == 0
    shun = yang_year == (gender == '男')
    direction = 1 if shun else -1
    nd, jm, jd, cross = nearest_jie(y, m, d, direction)
    target = to_doy(m, d, y)
    diff = abs(nd - target)
    if cross == 1:
        diff = (to_doy(12, 31, y) - target) + nd
    elif cross == -1:
        diff = (to_doy(12, 31, y-1) - to_doy(12, 31, y-1)) + (target - nd)
    years = diff / 3.0
    return {"direction": "順" if shun else "逆", "jie": f"{jm}月{jd}日",
            "days_to_jie": diff, "qiyun_age": round(years, 1),
            "qiyun_str": f"{int(years)}歲{int((years%1)*12)}月起運"}


if __name__ == '__main__':
    print("=== PATCH-057 起运岁数 ===")
    # GC-001: 1983-11-03 男 癸亥(阴)→阴男逆排
    r = qiyun_age(1983, 11, 3, '男', '癸')
    print(f"GC-001 1983-11-03 男 癸亥阴年:")
    for k, v in r.items():
        print(f"  {k}: {v}")
