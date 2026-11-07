
# PATCH-034：strength_state 综合裁决（RULE-034-01）— 2026-09-16

## 里程碑
**strength_state 首次出值（SLIGHTLY_WEAK）**——024 契约 authorized producers 0→1，身强身弱判定正式接线。

## 证据链（COMPOSITE，无单经典直产）
- YHZP-138-001（A）：得時俱為旺論／失令便作衰看／日干無氣遇劫為強
- SFTK-008-001（A）：財多身弱（木日干四柱土重，异文 S1 采信）
- DTS-016-002（B1 辅助）：旺中有衰／衰中有旺者存
- DTS-017-001/002（A+B1，RULE-022C-05 中和原则）

## 裁决谓词（无评分/权重/计数）
1. qiang=強（無氣+遇劫双条件）→ STRONG 方向
2. wang=旺+根强+帮身 → STRONG 方向
3. shuai=SHUAI+帮身充足+有根 → 「衰中有旺」→ **SLIGHTLY_WEAK**
4. shuai=SHUAI+无帮身+无根 → WEAK
5. 病药財多身弱 → 佐证身弱方向
6. 其他 → UNDETERMINED（FAIL_CLOSED）

## 1983-1103 裁决
失令衰（YHZP）+印透三帮身（SFTK 財多身弱佐证）+有根（亥甲/未乙）+DTS 衰中有旺不极弱 → **strength=SLIGHTLY_WEAK（偏弱）**
禁 shuai→WEAK 直映射 ✓；无单因子触发 ✓

## BUG 修复（Golden 回归抓出）
FORBIDDEN 检查用子串包含匹配——「WEAK」in「SLIGHTLY_WEAK」误报越权。改为**精确匹配核心值**（split('(') 取前缀），防 SLIGHTLY_WEAK 误含 WEAK（与 022B BUG-01 NOT_GET_ORDER 同类）。

## 授权登记
authorized strength producers：0 → RULE-034-01（YHZP+SFTK+DTS COMPOSITE）
PZZQ.strength_condition / SMTH.time_modifier 本局未触发（路径C財格透印非身強帶比；无大运输入），不算违规（COMPOSITE 不需每次全域参与）。

## 1983 全状态（GC-001 v4）
pattern=DETERMINED(财格)｜use_god=CANDIDATE(财)｜qu_yong=DETERMINED(病=财多身弱,药=印比帮身)｜climate_use=DETERMINED(癸水)+壬多降级｜**strength=SLIGHTLY_WEAK(偏弱)**
9 状态中 5 个出值，4 个（wang/qiang/climate_state/trend）合理保持 UNKNOWN/UNDETERMINED。

## 验证
Golden GC-001 v4 回归通过（forbidden 精确匹配修复后）；枚举 22/22 缺口=0。

## 产物
- engines/common/strength_rules.py（RULE-034-01）
- engines/common/golden_cases.py（GC-001 v4 + forbidden 精确匹配修复）
