# -*- coding: utf-8 -*-
"""BUG1 验证：canonical._LUNAR_MONTH_JIE 与 compute_liuyue 月编号语义错位"""
import sys
sys.path.insert(0, r"D:\shuntian")
sys.path.insert(0, r"D:\shuntian\src")
from tongshu.engines.heluo.timeline_yun import compute_liuyue
from tongshu.engines.heluo.numbers import build_six_lines
from tongshu.engines.heluo.canonical import _jie_datetime_for_lunar_month

# 取一个流年卦序列（观卦上九元堂示例：H16 已验证 子月=风雷益）
lines = build_six_lines("巽", "坤")  # 风地观
ry = compute_liuyue(lines, 5)
print("流月卦月份编号语义（阳月=奇数月=子寅辰午申戌）：")
for m in ry.months:
    print(f"  month={m['month']:2d} kind={m['kind']} {m['name']}")
print()
print("_LUNAR_MONTH_JIE 当前映射（正月=立春口径）：")
for lm in range(1, 13):
    dt = _jie_datetime_for_lunar_month(2026, lm)
    print(f"  month={lm:2d} → 节锚={dt}")
print()
print("期望（子月首口径：month=1 子月应锚大雪23，month=12 亥月应锚立冬21）：")
EXPECT = {1: "大雪", 2: "小寒", 3: "立春", 4: "惊蛰", 5: "清明", 6: "立夏",
          7: "芒种", 8: "小暑", 9: "立秋", 10: "白露", 11: "寒露", 12: "立冬"}
JIE_DATE = {
    "冬至": "12-21/22", "小寒": "01-05/06", "大寒": "01-20/21", "立春": "02-03/04",
    "雨水": "02-18/19", "惊蛰": "03-05/06", "春分": "03-20/21", "清明": "04-04/05",
    "谷雨": "04-19/20", "立夏": "05-05/06", "小满": "05-20/21", "芒种": "06-05/06",
    "夏至": "06-21/22", "小暑": "07-07/08", "大暑": "07-22/23", "立秋": "08-07/08",
    "处暑": "08-22/23", "白露": "09-07/08", "秋分": "09-22/23", "寒露": "10-07/08",
    "霜降": "10-23/24", "立冬": "11-07/08", "小雪": "11-22/23", "大雪": "12-07/08",
}
for lm in range(1, 13):
    print(f"  month={lm:2d} → 应锚 {EXPECT[lm]}（{JIE_DATE[EXPECT[lm]]}）")
