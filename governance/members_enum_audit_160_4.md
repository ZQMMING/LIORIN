# PATCH-160.4 十神成员枚举L0边界裁决 = CONDITIONAL(可解除)

## 现状
- 天干十神: stem_relations[k]={stem,ten_god,柱位}, 完整可枚举
- 藏干十神: 已算但all_hidden收成set, 丢branch+本/中/中气provenance
- target_root_facts/any_stem_has_ten_god 不能承担成员枚举

## 160.5实现
恢复每个藏干原始定位, 产ten_god_members:
{pillar, type(stem/branch/hidden), stem, branch, hidden_index, qi_position(本/中/余), ten_god}
纯枚举分组: supporting(印比)/draining(财官杀食伤)/target。

## 禁止
count->旺; count->财多; supporting>draining->身强; 本/中/余气权重;
强弱评分; daymaster_strong; wealth_strong; 改157-159。
本/中/余气只存provenance不赋权重。
