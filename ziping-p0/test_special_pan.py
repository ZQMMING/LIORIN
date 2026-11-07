#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一主入口测试"""
import sys
sys.path.insert(0, '.')

from engines.special_pan import special_pan


def run(name, day_stem, branches, stems):
    result = special_pan(stems, branches, day_stem)
    print(f"{name}: {result}")
    return result


print("=== 统一主入口测试 ===")
print("\n--- 化气族 ---")
run("甲己化土", "甲", ["辰", "未", "辰", "巳"], ["戊", "己", "甲", "己"])
run("乙庚化金", "乙", ["酉", "申", "酉", "辰"], ["乙", "甲", "乙", "庚"])

print("\n--- 专旺族 ---")
run("曲直格", "甲", ["寅", "卯", "寅", "亥"], ["甲", "丁", "甲", "乙"])
run("炎上格", "丙", ["巳", "午", "午", "午"], ["丙", "甲", "丙", "甲"])

print("\n--- 从格族 ---")
run("李侍郎从杀", "乙", ["酉", "酉", "酉", "申"], ["乙", "乙", "乙", "甲"])
run("一品夫人从儿", "癸", ["卯", "卯", "卯", "卯"], ["甲", "丁", "癸", "乙"])

print("\n--- 正格族（待接入） ---")
run("普通正格", "甲", ["子", "寅", "辰", "午"], ["甲", "丙", "甲", "庚"])
