# -*- coding: utf-8 -*-
"""HUA_SHEN键序回归测试

sorted(['己','甲'])在Unicode下是['己','甲']，不是['甲','己']
所以HUA_SHEN必须双向key，不能靠sorted生成
"""
import sys
sys.path.insert(0, '.')
from engines.axis_xiuqi import HUA_SHEN

PAIRS = [
    ('甲', '己', '土'),
    ('乙', '庚', '金'),
    ('丙', '辛', '水'),
    ('丁', '壬', '木'),
    ('戊', '癸', '火'),
]

def test_hua_shen_key_canonical():
    for a, b, ele in PAIRS:
        # 正向
        key1 = a + b
        assert HUA_SHEN.get(key1) == ele, f"{key1}应为{ele}，实际{HUA_SHEN.get(key1)}"
        # 逆序（sorted的死亡路径）
        key2 = b + a
        assert HUA_SHEN.get(key2) == ele, f"{key2}应为{ele}，实际{HUA_SHEN.get(key2)}"
    print("✅ HUA_SHEN双向键序全部通过")

if __name__ == "__main__":
    test_hua_shen_key_canonical()
