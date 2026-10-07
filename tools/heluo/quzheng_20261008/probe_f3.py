# -*- coding: utf-8 -*-
"""扫 guajie_data.json 找含取象字的真实爻辞。"""
import io
import json

d = json.load(io.open("data/heluo/guajie_data.json", encoding="utf-8"))
print("顶层类型:", type(d).__name__, "长度", len(d))
print("首元素:", json.dumps(d[0], ensure_ascii=False)[:400])

KEYS = ["龙", "马", "牛", "羊", "永", "鹤", "龟", "鸿", "鸟", "月",
        "木", "血", "忧", "泣", "甘", "苦", "金", "肉", "朋"]


def walk(obj, path=""):
    """产出 (path, text) 对，覆盖所有字符串叶子。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, path + "/%d" % i)
    elif isinstance(obj, str):
        yield path, obj


hits = {}
for path, text in walk(d):
    for c in KEYS:
        if c in text:
            hits.setdefault(c, []).append((path, text[:30]))

print()
for c in KEYS:
    v = hits.get(c, [])
    print("%s  命中 %3d 处  例: %s" % (c, len(v), v[0] if v else "-"))