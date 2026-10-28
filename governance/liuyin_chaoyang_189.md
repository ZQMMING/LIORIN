# PATCH-189 六阴朝阳 Structural Entry（SEALED）

## 条件
辛日 AND 时柱==戊子 AND 天干官杀全无 AND 藏干官杀全无

## 复用 L0（不新造搜索器）
- any_stem_has_ten_god['官'] = 正官∪七杀 天干层
- target_root_facts['官'] = 正官∪七杀 藏干层

## Contract 语义锁死
- _CAT['官'] = {正官, 七杀}，是官杀联合存在性 key，≠"正官"十神语义
- 七杀≠正官 仍成立；G6/G7 证明仅正官或仅七杀都不立
- 两个 FALSE 是 L0 枚举后确定 FALSE，非 Rule 搜索不到压成 FALSE

## 锁死
- 仅结构入口出现，未定格局
- 不判月令无用/旺衰/从化/贵贱/喜忌/吉凶
- note 措辞避开祸福词扫描

## G1-G10 golden + 全量回归绿
