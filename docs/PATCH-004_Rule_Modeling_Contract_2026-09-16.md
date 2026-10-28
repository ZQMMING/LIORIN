# PATCH-004 Rule Modeling Contract（规则建模契约）

- 日期：2026-09-16
- 状态：FROZEN_DRAFT（契约冻结草稿，不实现任何算法）
- 依据：Human 裁决「003B 通过，下一步不直接写旺衰公式，先建立 PATCH-004 Rule Modeling Contract」
- 契约文件：`governance/patch_004_rule_modeling_contract.json`

## 一、总则

当前状态：

| 层 | 状态 |
|---|---|
| Evidence Layer | PASS（PATCH-003B） |
| Classical Scope | PASS |
| Scope Boundary | PASS |
| Rule Admission | PASS（Pending Rule Layer） |
| **Algorithm Layer** | **NOT STARTED** |

现在拥有的是「经典证据许可库」（111 条 ADMISSIBLE_PENDING_RULE），不是「命理判断算法库」。

**核心铁律（9 条）**：

1. ADMISSIBLE_PENDING_RULE ≠ RULE：证据许可库 ≠ 算法规则库
2. Boolean 禁止作业务裁决（PATCH-001 铁律延续）
3. 禁止旺=STRONG、得令=强、有根=强（003B-03 固化扫描 0 违规延续）
4. 任何旺衰变量必须携带 OBJECT + SOURCE + RELATION + CLASSICAL_SCOPE 四维
5. 未登记状态变量/枚举 FAIL_CLOSED（enum_registry 联动）
6. **PZZQ 清杂 ≠ DTS 清浊**：禁止合并（PZZQ-007-005 取用神层面纯杂 / DTS 气象格局清浊）
7. **DTS 病药 ≠ SFTK 病药**：禁止 `if DTS_bing: use_SFTK_bingyao()`（DTS-017-002 命局缺陷去病思想 / SFTK-008-001 病药诊断体系）
8. 概念交叉验证与具体算法交叉验证分离
9. 证据未钉死一律 FAIL_CLOSED，不得模型自行补全

## 二、4.1 状态变量定义（候选注册表，11 个）

| 变量 | 域 | 值域（候选） | 核心来源 | 注 |
|---|---|---|---|---|
| strength_state | 旺强衰 | STRONG/SLIGHTLY_STRONG/NEUTRAL/SLIGHTLY_WEAK/WEAK/UNDETERMINED | YHZP-138-001/DTS-016-001/DTS-016-002/SFTK-129-038 | PATCH-001 冻结六级；工程容器，非六部统一判定 |
| wang_state | 旺强衰 | WANG/NOT_WANG/CONTAINED_WANG/UNDETERMINED | YHZP-138-001/DTS-016-002 | 对象时令兴盛；非 STRONG 同义词 |
| qiang_state | 旺强衰 | QIANG/NOT_QIANG/UNDETERMINED | YHZP-138-001/SFTK-120-004 | 关系结果（得时/遇劫/党众）；旺≠强 |
| shuai_state | 旺强衰 | SHUAI/NOT_SHUAI/UNDETERMINED | YHZP-138-001/DTS-016-002 | 对象时令衰退；≠WEAK |
| order_state | 令时地根 | GET_ORDER/NOT_GET_ORDER/UNDETERMINED | YHZP-030-001/PZZQ-005-007/SFTK-120-004 | 对象↔月令；对象可为日主/气象/喜神/真神 |
| root_state | 根气 | NONE/WEAK/NORMAL/STRONG/EXCESSIVE/UNDETERMINED | YHZP-123-003/PZZQ-007-021/DTS-010-003/QTBJ-011-001/SFTK-020-014 | 对象化通根；ROOT≠DAY_MASTER_ONLY |
| support_state | 党众 | NONE/WEAK/NORMAL/STRONG/EXCESSIVE/UNDETERMINED | PZZQ-007-027/DTS-057-001 | 群体支撑；禁数量阈值 |
| seasonal_state | 令时地根 | IN_COMMAND/OUT_OF_COMMAND/TRANSITION/UNDETERMINED | QTBJ-018-001 | QTBJ 季节主气 |
| trend_state | 势 | TREND_TO/BURST/GROUP/HOLD/UNDETERMINED | DTS-008-003/SMTH-035-001/SFTK-129-038 | TREND≠STRENGTH |
| qi_state | 气势 | HAS_QI/NO_QI/UNDETERMINED | DTS-035-001/QTBJ-002-002/SFTK-133-001 | 干支流通/气势 |
| momentum_state | 气势 | GAINED/NOT_GAINED/UNDETERMINED | （无） | 无来源 FAIL_CLOSED |

## 三、4.2 旺/强/衰/弱分离模型

- 旺 = 对象时令兴盛（状态）；强 = 关系结果（结构）；衰 = 对象时令衰退（状态）；弱 = 强度体系端
- 禁止四者互转。YHZP-138-001「得時俱為旺論→wang_state；遇劫為強→qiang_state；失令便作衰看→shuai_state」逐条映射

## 四、4.3 得令/得地/得势/根气关系模型

| 关系 | 对象 | 来源 | 注 |
|---|---|---|---|
| GET_ORDER | 日主/五神/气象 | YHZP-030-001/PZZQ-005-007/SFTK-120-004 | 得令≠强 |
| GET_TIME | 日主 | YHZP-138-001 | 得时≠得令 |
| ROOTED_IN | 日主/官/财/杀/印 | YHZP-123-003/PZZQ-007-021/DTS-010-003/SFTK-020-014 | 根≠得地 |
| TREND_TO | 五行群体 | DTS-008-003/SMTH-035-001/SFTK-129-038 | 势≠强弱 |
| RULING_SCHEDULE | 地支藏干 | DTS-015-004/DTS-015-006/YHZP-056-001 | 禁转 WEIGHT |

## 五、4.4 布尔+枚举规则设计

- Boolean 仅技术属性；业务裁决必须 Tri-State/Multi-State
- 禁止业务 Boolean：is_strong/is_weak/is_useful/is_pattern/is_successful/is_effective/is_disease/is_medicine/is_favorable/is_unfavorable
- 未注册枚举 FAIL_CLOSED；状态类型分层（EXISTENCE/CONDITION/EFFECT/STRENGTH/ROLE/PATTERN/RESULT）

## 六、4.5 冲突处理机制（Conflict Resolver）

- 冲突输入 → 主判选择（CONCEPT_SCOPE_MATCH）→ 独立登记（不合并/不平均/不投票）→ CONFLICT≠ERROR → 无法裁决 UNDETERMINED/FAIL_CLOSED
- 示例：日主得令+无根+被制 → 禁止 `order_state=GET_ORDER → strength=STRONG`；必须走 resolver

## 七、4.6 Golden Case 测试（结构定义，本轮不实现）

- case_id/pillars/expected_states/evidence_chain/classical_scope/verdict_status
- 命例仅 REFERENCE_ONLY，禁反推规则

## 八、4.7 六经典 Concept Scope Match 优先（非书间排序）

| 概念 | 主判 | 域 | 注 |
|---|---|---|---|
| 用神 | PZZQ | yong_shen | PZZQ-005-007 |
| 调候 | QTBJ | tiao_hou | PZZQ-007-003 CONTEXTUAL |
| 通关 | DTS | tong_guan | DTS_SCOPE_ONLY |
| 日时断语 | SMTH | ganzhi_zuhe/ming_li | 仅日时语境 |
| 病药 | SFTK | bing_yao | DTS-017-002 仅 SUPPORTING |
| 清浊 | DTS(结构) | qing_zhuo | PZZQ 清杂 CONTEXTUAL |
| 相神 | PZZQ | xiang_shen | PZZQ_ONLY |
| 顺逆 | DTS | shun_ni | DTS_PRIMARY |
| 格局成败 | PZZQ | geju_chengbai | PZZQ-005-008 |
| 神煞 | EXCLUDED | shen_sha | 仅文献检索 |
| 命例 | REFERENCE_ONLY | ming_li | 禁反推 |

## 九、下一步

4.1–4.3 契约冻结后，才允许进入 4.4 规则设计与旺衰/强弱/用神/格局算法建模。
