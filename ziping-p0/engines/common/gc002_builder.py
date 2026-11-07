# -*- coding: utf-8 -*-
"""GC-002 命局构造工具：标准干支排盘（用于 Golden Case 输入，不进核心引擎）

- 日柱：儒略日(JDN) mod 60，以 1900-01-01=甲戌 为锚
- 年柱：立春分界（year-4 干支；立春前=上一年）
- 月柱：五虎遁（节气分界，简化节气表；扫描避开边界日）
- 时柱：五鼠遁（日干起子时）
- 校验锚：1983-11-03 11:30 → 癸亥 壬戌 乙未 壬午（用户已验证 GC-001）
"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 2026-09-30: 藏干表改读 LIORIN 权威源（engines.l0_paipan）。
#   原硬编码 "巳":["丙","庚","戊"] 把中气/余气颠倒（应 丙本/戊中/庚余），
#   而本文件 BENQI = v[0] 判月令本气，改错会静默给错月令。
#   本仓不再维护独立副本；新排盘请走 engines.l0_paipan.facts_from_birth()。
from engines.l0_paipan import branch_hidden_stems as _bhs

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
# 藏干（本气,中气,余气）
HIDDEN = _bhs()
# 节气近似日（月支分界，扫描避开 ±3 日边界）
JIEQI = [("寅", 2, 4), ("卯", 3, 6), ("辰", 4, 5), ("巳", 5, 6), ("午", 6, 6), ("未", 7, 7),
         ("申", 8, 8), ("酉", 9, 8), ("戌", 10, 8), ("亥", 11, 8), ("子", 12, 7), ("丑", 1, 6)]


def jdn(y, m, d):
    a = (14 - m) // 12
    yy, mm = y + 4800 - a, m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


def day_ganzhi(y, m, d):
    diff = (jdn(y, m, d) - jdn(1900, 1, 1)) % 60   # 1900-01-01 = 甲戌日(索引10)
    idx = (10 + diff) % 60
    return GAN[idx % 10] + ZHI[idx % 12]


def month_branch(y, m, d):
    if m == 1:
        return "丑"          # 1 月整月为丑月（腊月）
    mb = "丑"
    for zi, mm, dd in JIEQI:
        if mm == 1:
            continue
        if (m > mm) or (m == mm and d >= dd):
            mb = zi
    return mb


def year_ganzhi(y, m, d):
    mb = month_branch(y, m, d)
    yy = y - 1 if mb == "丑" else y   # 丑月（腊月）干支属上一年
    return GAN[(yy - 4) % 10] + ZHI[(yy - 4) % 12]


def month_gan(yg, mb):
    # 五虎遁（偏移=寅月天干索引）：甲己→丙(2) 乙庚→戊(4) 丙辛→庚(6) 丁壬→壬(8) 戊癸→甲(0)
    yi = {"甲": 2, "己": 2, "乙": 4, "庚": 4, "丙": 6, "辛": 6, "丁": 8, "壬": 8, "戊": 0, "癸": 0}[yg]
    zhi_i = ZHI.index(mb)
    g = (yi + zhi_i - 2) % 10
    return GAN[g] + mb


def hour_gan(dg, h):
    # 五鼠遁（偏移=子时天干索引）：甲己→甲(0) 乙庚→丙(2) 丙辛→戊(4) 丁壬→庚(6) 戊癸→壬(8)
    yi = {"甲": 0, "己": 0, "乙": 2, "庚": 2, "丙": 4, "辛": 4, "丁": 6, "壬": 6, "戊": 8, "癸": 8}[dg]
    hz = (h + 1) // 2 % 12
    g = (yi + hz) % 10
    return GAN[g], ZHI[hz]


# PATCH-057 大运/起运辅助(排盘输出字段)
_JIEQI = [(2,4),(3,6),(4,5),(5,6),(6,6),(7,7),(8,8),(9,8),(10,8),(11,7),(12,7),(1,6)]

def _to_doy(m, d, y):
    md = [31,28,31,30,31,30,31,31,30,31,30,31]
    if (y % 4 == 0 and y % 100 != 0) or y % 400 == 0:
        md[1] = 29
    return sum(md[:m-1]) + d

def _dayun_qiyun(y, m, d, year_gan, month_gan, month_zhi, gender):
    yang = GAN.index(year_gan) % 2 == 0
    shun = yang == (gender == '男')
    direction = 1 if shun else -1
    gi = GAN.index(month_gan); zi = ZHI.index(month_zhi)
    dayuns = [GAN[(gi+direction*i)%10] + ZHI[(zi+direction*i)%12] for i in range(1, 9)]
    # 起运: 数到节令天数/3
    target = _to_doy(m, d, y)
    jies = [(_to_doy(jm, jd, y), jm, jd) for jm, jd in _JIEQI]
    jies.sort()
    if shun:
        nxt = [x for x in jies if x[0] > target]
        nd, jm, jd = (nxt[0] if nxt else (_to_doy(_JIEQI[0][0],_JIEQI[0][1],y+1), _JIEQI[0][0], _JIEQI[0][1]))
        diff = abs(nd - target) if nxt else (_to_doy(12,31,y)-target)+nd
    else:
        prv = [x for x in jies if x[0] < target]
        nd, jm, jd = (prv[-1] if prv else (_to_doy(_JIEQI[-1][0],_JIEQI[-1][1],y-1), _JIEQI[-1][0], _JIEQI[-1][1]))
        diff = abs(target - nd) if prv else target + (365 if y%4 else 366) - nd
    age = round(diff/3.0, 1)
    return dayuns, {"direction": "順" if shun else "逆", "jie": f"{jm}月{jd}日",
                    "days": diff, "age": age,
                    "text": f"{int(age)}歲{int((age%1)*12)}月起運"}


def paipan(y, m, d, h, gender='男'):
    yg, yz = year_ganzhi(y, m, d)[0], year_ganzhi(y, m, d)[1]
    mb = month_branch(y, m, d)
    mg = month_gan(yg, mb)[0]
    dg, dz = day_ganzhi(y, m, d)
    hg, hz = hour_gan(dg, h)
    stems = {"年": yg, "月": mg, "日": dg, "时": hg}
    branches = {"年": yz, "月": mb, "日": dz, "时": hz}
    hidden = {k: HIDDEN[v] for k, v in branches.items()}
    # PATCH-057 大运/起运整合进排盘输出(下游直接消费)
    dayun, qiyun = _dayun_qiyun(y, m, d, yg, mg, mb, gender)
    return {"pillars": f"{yg}{yz} {mg}{mb} {dg}{dz} {hg}{hz}", "stems": stems, "branches": branches,
            "hidden": hidden, "month_order": mb, "day_master": dg,
            "dayun": dayun, "qiyun": qiyun}


if __name__ == "__main__":
    print("==== 排盘自校验（GC-001 锚：1983-11-03 11:30 → 癸亥 壬戌 乙未 壬午） ====")
    r = paipan(1983, 11, 3, 11)
    print("  ", r["pillars"], "→", "PASS ✓" if r["pillars"] == "癸亥 壬戌 乙未 壬午" else f"FAIL ✘ {r['pillars']}")
    print("\n==== 扫描印格命局（1990-1995 每月 15 日，避节气边界） ====")
    ELEM = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
    BENQI_TG = {k: v[0] for k, v in HIDDEN.items()}
    found = []
    for y in range(1990, 1996):
        for m in range(1, 13):
            p = paipan(y, m, 15, 10)
            dm, mb = p["day_master"], p["month_order"]
            bq = BENQI_TG[mb]
            gd, gb = ELEM[dm], ELEM[bq]
            gen = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
            if gen[gb] == gd:  # 月令本气生日主 = 印格
                found.append((p, "印格"))
    for p, g in found[:6]:
        print(f"  {p['pillars']}  日主={p['day_master']} 月={p['month_order']} → {g}")
    print(f"\n  印格候选共 {len(found)} 个，取第一个作 GC-002")
