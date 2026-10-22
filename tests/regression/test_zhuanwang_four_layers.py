# -*- coding: utf-8 -*-
"""
专旺格重构四层单测（V7.25 P0）

层0：ID与口径不变量
层1：else/default守卫
层2：账B专旺幻觉基线（108条）
层3：账A专旺真例基线（19条）
层4：全局底线（零empty special、零error）

闸门：
- 硬闸门：账B专旺条数下降，且下降的主要流向正格
- 软观察：账A一致率不低于40%
- 全局底线：零empty special、零error、零default
"""
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'scripts')
import json
from collections import Counter

# 加载基线
baseline = json.load(open('baseline_special_20260922.json', encoding='utf-8'))

# 专旺格判断
def is_zhuanwang(special):
    return any(x in special for x in ['曲直格', '炎上格', '稼穑格', '从革格', '润下格'])

# ============================================================
# 层0：ID与口径不变量
# ============================================================
print('=== 层0：ID与口径不变量 ===')

# 检查条数
assert len(baseline) == 509, f"基线条数应为509，实际{len(baseline)}"
print(f"✅ 基线条数: {len(baseline)}")

# 检查key存在
assert all('key' in b for b in baseline), "存在缺少key的案例"
print(f"✅ key二次键: 全部存在")

# 检查li唯一
li_set = set(b['li'] for b in baseline)
assert len(li_set) == len(baseline), "li不唯一"
print(f"✅ li唯一: {len(li_set)}")

# 检查key重复情况（同八字不同大运是正常的）
key_set = set(b['key'] for b in baseline)
duplicate_count = len(baseline) - len(key_set)
print(f"ℹ️ 唯一八字数: {len(key_set)} (重复{duplicate_count}条，同八字不同大运是正常的)")

print()

# ============================================================
# 层1：else/default守卫
# ============================================================
print('=== 层1：else/default守卫 ===')

# 检查没有empty special或error
empty_special = [b for b in baseline if b.get('special') == '' and not b.get('error')]
errors = [b for b in baseline if b.get('error')]

assert len(empty_special) == 0, f"存在{len(empty_special)}条empty special"
assert len(errors) == 0, f"存在{len(errors)}条error"

print(f"✅ empty special: {len(empty_special)}")
print(f"✅ error: {len(errors)}")

# 检查special不为空且不为default
default_cases = [b for b in baseline if b.get('special') in ('default', 'DEFAULT', '')]
assert len(default_cases) == 0, f"存在{len(default_cases)}条default"
print(f"✅ default命中: {len(default_cases)}")

print()

# ============================================================
# 层2：账B专旺幻觉基线（应下降）
# ============================================================
print('=== 层2：账B专旺幻觉基线（硬闸门）===')

# 当前专旺格总数
zhuanwang_total = sum(1 for b in baseline if is_zhuanwang(b.get('special', '')))
print(f"当前专旺格总数: {zhuanwang_total}")

# 按子格拆分
zhuanwang_dist = Counter(b['special'] for b in baseline if is_zhuanwang(b.get('special', '')))
print(f"专旺格分布:")
for sp, count in zhuanwang_dist.most_common():
    print(f"  {sp}: {count}")

print()
print("硬闸门验收标准（改完规则后对比）:")
print("  - 专旺格总数应下降（预期从132→~70-80）")
print("  - 下降的案例主要流向正格（而非报错或空值）")
print()

# ============================================================
# 层3：账A专旺真例基线（软观察）
# ============================================================
print('=== 层3：账A专旺真例基线（软观察）===')

# 这里我们用账A的19条（原文自述专旺）
# 但我们没有原文标注，所以用当前基线作为基线
# 改完规则后，专旺格中的真例不应大量流失

# 专旺格中的真例种子（之前盲核确认真例的）
# 注意：这些key需要从原文标注获取，暂时用占位
# 改完规则后，这些案例仍应判为专旺

print("软观察验收标准（改完规则后对比）:")
print("  - 专旺格真例不应大量流失（一致率不低于40%）")
print("  - 若跌破40%，说明规则矫枉过正，需回退调整")
print()

# ============================================================
# 层4：全局底线
# ============================================================
print('=== 层4：全局底线 ===')

# 1. 零empty special
print(f"✅ 零empty special: {len(empty_special)}")

# 2. 零error
print(f"✅ 零error: {len(errors)}")

# 3. 零default
print(f"✅ 零default: {len(default_cases)}")

# 4. special分布合理性
zhengge_count = sum(1 for b in baseline if b.get('special') == '正格')
congge_count = sum(1 for b in baseline if any(x in b.get('special', '') for x in ['从财格', '从杀格', '从儿格', '从势格']))  # V7.158 从官格并入从杀格
huaqi_count = sum(1 for b in baseline if '化' in b.get('special', '') and '气格' in b.get('special', ''))
liangge_count = sum(1 for b in baseline if '两气成象' in b.get('special', ''))

print(f"✅ 正格: {zhengge_count}")
print(f"✅ 从系格: {congge_count}")
print(f"✅ 化气格: {huaqi_count}")
print(f"✅ 两气成象: {liangge_count}")
print(f"✅ 专旺格: {zhuanwang_total}")

print()
print("=" * 50)
print("✅ 四层单测基线建立完成")
print("=" * 50)
print()
print("下一步：改专旺格规则，然后重跑本脚本对比")
print("验收标准：")
print("  1. 专旺格总数下降（硬闸门）")
print("  2. 下降案例主要流向正格（硬闸门）")
print("  3. 真例一致率不低于40%（软观察）")
print("  4. 零empty special、零error、零default（全局底线）")
