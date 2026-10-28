
# PATCH-037：Golden Case 扩展（GC-003 官格命局）— 2026-09-16

## 里程碑
**Golden Case 三例**——GC-003 激活 RULE-035-04 官格成败分支（财/印/官三格实判）。

## GC-003（V1 锁定）
1992-07-15 12:00 → **壬申 丁未 壬辰 丙午**（壬日主，未月己土正官当令 → 官格）
- 排盘由 gc002_builder 复算；**四支零刑冲破害**（扫描工具 gc003_scan 过滤，含刑冲破害判定表）

## 判定（RULE-035-04，PZZQ-005-008 逐字）
- **pattern_success_state = SUCCESS(官逢財印又無刑衝破害)**：官当令（未中己）+财透（丁丙生官）+印有根（申中庚本气）+零刑冲破害 → 官格成也
- **官伤同宫（藏干）登记为 condition_context**——未中藏乙伤官+己官同宫，但伤官未透干不直接败格（PZZQ 成败以透干为准）
- 败格未触发：伤官不透、无刑冲破害
- daiji=NO_DAIJI｜rescue=NO_RESCUE_NEEDED｜相神=PRESENT(财印双辅)

## 新增能力
- **地支刑冲破害判定表**（六冲/六害/六破两支即论；三刑三支齐、子卯两支论）——PZZQ「無刑衝破害/官逢傷剋刑衝」工程化
- 官杀/财/伤官按日主阴阳动态判定（修复「我克=财」方向 bug——壬之财=火非土）

## 验证
GC-001（财格）+ GC-002（印格）+ GC-003（官格）三 Golden 全通过；枚举 22/22。

## 产物
- engines/common/pattern_success_rules.py（RULE-035-04 + 刑冲破害表 + 动态十神判定）
- engines/common/gc003_scan.py（零刑冲破害官格扫描）
- engines/common/gc003_check.py（GC-003 判定复算）
- engines/common/golden_cases.py（GC-003 校验）
