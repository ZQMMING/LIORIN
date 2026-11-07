
## PATCH-005A 旺/强/衰/弱 Concept Boundary Registry（commit 待）

### Human 裁决
启动 005A：建立《旺/强/衰/弱 Concept Boundary Registry》，只做概念定义/Source绑定/Object绑定/Relation绑定/Allowed-Forbidden Transition；暂不允许生成身强/身弱/喜忌/用神结论。流程：Classical Evidence → Concept → State/Factor → Rule Candidate → Golden Validation → Executable Rule。

### 005 全局禁止 4 项
1. 旺数量统计（旺因素5个/弱因素2个→身强）
2. 五行力量百分比（木40%）
3. 得令直接进入 strength_state（if get_order: STRONG）
4. 单经典覆盖全部旺衰（DTS=全部子平旺衰）

### 首批 12 个 Rule Candidate（全部 source 可回查）
| Candidate | 概念 | Scope | 输出 | 禁转换 |
|---|---|---|---|---|
| CAND-WANG-001 | 旺（得时俱为旺论） | YHZP-138-001 | wang_state | →STRONG |
| CAND-WANG-002 | 旺中有衰（原注B1辅助） | DTS-016-002 | wang_state | CONTAINED→STRONG |
| CAND-SHUAI-001 | 衰（失令便作衰看） | YHZP-138-001 | shuai_state | →WEAK自动 |
| CAND-QIANG-001 | 强（遇劫为强） | YHZP-138-001 | qiang_state | →STRONG |
| CAND-RUO-001 | 弱（无单锚） | — | strength_state（待005C） | 日干无气→WEAK直接 |
| CAND-ORDER-001 | 得令（月提得令） | YHZP-138-001/PZZQ-005-007/SFTK-120-004 | order_state | →STRONG |
| CAND-TIME-001 | 得时（四柱无根得时为旺） | YHZP-138-001 | order_state(TIME) | GET_TIME→STRONG |
| CAND-ROOT-001 | 根（对象化） | YHZP-123-003/PZZQ-007-021/QTBJ-011-001/SFTK-020-014 | root_state | →STRONG/favorable |
| CAND-TREND-001 | 势（五阳从气） | DTS-008-003/008-022 | trend_state | →strength |
| CAND-SEASONAL-001 | 季节（QTBJ） | QTBJ-018-001（⚠️CANDIDATE级） | seasonal_state | →STRONG/统一公式 |
| CAND-SFTK-ROOT-001 | 强杀无根（对象化） | SFTK-129-038/020-014 | root_state | 杀无根→身强 |
| CAND-DTS-ZHENJIA-001 | 真神得令 | DTS-023-004 | order_state(真神) | 真神得令→身强 |

### ⚠️ 发现并标注：QTBJ-018-001 为 CANDIDATE_RULE 级
不在 111 条 CORE_RULE_ELIGIBLE 内。已标注 source_level_note：005B 必须先升格核验（或换 QTBJ-060-001/QTBJ-109-001 调候 CORE 来源），否则 FAIL_CLOSED。不静默换源。

### 验收
概念不产身强/身弱/喜忌/用神结论；source 可回查；Object/Relation 绑定；Forbidden 全登记；005 全局禁止 4 项冻结。

### 产物
governance/patch_005a_concept_boundary_registry.json（12 candidates + 4 禁止 + 6 验收）
