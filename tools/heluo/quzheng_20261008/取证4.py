# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "src")
import io
import tongshu.engines.heluo.yuanqi_tables as t

O = io.open("取证_自校验结果.txt", "w", encoding="utf-8")
O.write("导入自校验：通过\n\n")
O.write("干支纳卦表覆盖：%d 项\n" % len(t.GANZHI_TO_GUA))
for g in ("乾", "坤", "坎", "离", "震", "巽", "艮", "兑"):
    a = t.gua_of_ganzhi_table_a(g)
    b = t.gua_of_ganzhi_table_b(g)
    sym, part = t.yuanqi_fan_suffering(g)
    O.write("%s  纳表干支=%-8s 又云干支=%-8s(%s)  反者=%-10s 反之病=%s %s\n"
            % (g, a[0] + a[1], b.gan + b.zhi, b.nayin_element,
               "/".join(t.yuanqi_fan_ganzhi(g)), sym, part))
O.write("\n两说分歧的干支组：\n")
n_conf = 0
for g in ("乾", "坤", "坎", "离", "震", "巽", "艮", "兑"):
    gan, zhi = t.gua_of_ganzhi_table_a(g)
    c = t.yuanqi_ganzhi_conflict(gan, zhi)
    if c[0]:
        n_conf += 1
        O.write("  %-4s+%s  说一归 %s，说二归 %s\n" % (gan, zhi, c[0], c[1]))
O.write("  共 %d 组分歧\n" % n_conf)
O.write("\n相反关系对照（说一对宫 / 说二纳音相克）：\n")
for g in ("乾", "坎", "震", "艮"):
    duo = t.yuanqi_fan_by_dui(g)
    b2 = t.gua_of_ganzhi_table_b(g)
    O.write("  %s：说一 %s ↔ %s ；说二 %s ↔ %s\n" % (g, g, duo, g, b2.opposite_gua))
O.write("\n干支纳卦抽样：\n")
for gz in ("甲子", "甲寅", "甲辰", "丙辰", "戊辰", "癸酉"):
    O.write("  %s → 卦 %s，五行 %s\n" % (gz, t.ganzhi_guas(gz), t.ganzhi_element(gz)))
O.close()
print("ok")