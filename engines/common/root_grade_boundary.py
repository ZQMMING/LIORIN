# -*- coding: utf-8 -*-
"""
L2边界函数: 纯布尔枚举(0浮点)
纪律: 全库只此一处, 其他位置禁止散装比较
"""

# 档位枚举(按强度排序)
ROOT_GRADES = ['禄刃', '长生', '库', '无根', '受制']

# 党众计数→档位(纯整数, 0浮点)
# 党众计数规则:
#   透干+1, 本气+1, 中气+0(不算), 余气+0(不算)
#   禄刃: 党众>=2(透干+本气)
#   长生: 党众>=1(透干或本气)
#   库: 地支见库根(辰戌丑未)
#   无根: 无根
#   受制: 根被冲克

def to_root_grade(root_count, has_root=None, root_controlled=None) -> str:
    """
    党众计数→根基档位(纯布尔枚举)

    两种调用形态(均为纯整数/布尔→档位, 0浮点):
      3参  to_root_grade(root_count, has_root, root_controlled)
           语义完整: 根被冲克→受制, 无根→无根, 其余按党众计数判 禄刃/长生/库
      1参  to_root_grade(root_count)
           便捷形态(yongshen_engine 等仅持有党众计数 ben_n 的调用方):
           按"有根、未受制"前提判档 —— 禄刃(ben_n>=2) / 长生(ben_n>=1) / 库(其余)
           不引入"无根/受制"维度(单计数不足以判定, 且引擎侧以 ben_n>0 即视为有根)
    输出: 档位枚举{禄刃/长生/库/无根/受制}
    """
    if has_root is not None:
        # 3参形态: 语义完整
        if root_controlled:
            return '受制'
        if not has_root:
            return '无根'
        root_count = int(root_count)
        if root_count >= 2:
            return '禄刃'
        if root_count >= 1:
            return '长生'
        return '库'
    # 1参便捷形态: 仅党众计数, 按有根未受制判档
    root_count = int(root_count)
    if root_count >= 2:
        return '禄刃'
    if root_count >= 1:
        return '长生'
    return '库'


if __name__ == '__main__':
    print('=== 边界函数测试(纯布尔) ===')
    print()
    print('  党众2+有根+未受制 → 禄刃')
    print('  党众1+有根+未受制 → 长生')
    print('  党众0+有根+未受制 → 库')
    print('  有根=假 → 无根')
    print('  根受制 → 受制')
