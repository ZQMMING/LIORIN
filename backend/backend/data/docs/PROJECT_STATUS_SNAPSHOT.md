# 顺天 / EXIS 项目状态快照

**保存时间**: 2026-08-29
**当前阶段**: CALCULATION INTEGRITY AUDIT（当前最高优先级 / 唯一施工区）
**项目执行主体**: 豆包

---

## 优先级声明（2026-08-29 重大更新）

### 项目重心切换：从"解"到"算"

**核心理念**：
> 算错 → 辨错 → 解再正确也没用
> 算准 → 辨准 → 解准 → 才是真正的顺天

**FROZEN ≠ PROVEN CORRECT**：
- P6.1 Canonical State 虽然冻结了，但不等于所有计算都正确
- Freeze 的意思是"不随便改"，不是"已经证明所有计算都正确"

**之前的日主 Bug 是严重信号**：
- Evaluation Runner 错误读取 chart.year_branch → AttributeError → except → 默认 Day Master = YI
- 结果：88% 案例 Day Master 错误，89.5% Ten-God 被污染
- 这说明：计算层错误 → Canonical State 错 → Semantic Signal 错 → Assertion Matcher 可能仍然正常 → 最终输出"逻辑正确地错"

**P6.5 证明的边界**：
- P6.5 证明了"当输入的事实正确时，断言资产可以被严格治理"
- 但没有证明"输入给断言层的 Canonical State 本身是正确的"
- 这是两个完全不同的问题

### 三层架构：算 → 辨 → 解

```
                    顺天
                     │
          ┌──────────┴──────────┐
          │                     │
         算                    解
          │                     │
    CALCULATION              INTERPRETATION
          │                     │
          ↓                     ↓
   Canonical State         Assertion Assets
          │                     │
          ↓                     ↓
   Semantic Signals       Executable Rules
          │                     │
          └──────────┬──────────┘
                     ↓
                   输出
```

中间明确加一个：算 → 辨 → 解
- CALCULATION → STATE / SIGNAL → ASSERTION

### 项目重新评级

| 层 | 当前成熟度 | 判断 | 优先级 |
|----|-----------|------|--------|
| 算 | ⚠️ 尚未完成最终证明 | 最高优先级 | 🔴 当前施工区 |
| 辨 | 🟡 架构已经建立，但应建立在稳定 Canonical State 上 | 第二优先 | ⏸️ 等待算层完成 |
| 解 | 🟢 治理已经非常严格，但资产量仍少 | 暂不扩产 | ⏸️ 冻结 |

### 当前正确状态

| 层 | 状态 |
|----|------|
| P6.1–P6.4 | 🔒 FROZEN（但 ≠ PROVEN CORRECT，需重新验证） |
| P6.5-A ～ B-R6 | ✅ COMPLETE / 封存 |
| Authorized Assertion Library | ✅ 现有资产保留 |
| P6.5-C | ⏸️ **BLOCKED_BY_CALCULATION_TRUTH**（冻结，不再扩充第二批断言） |
| **CALCULATION INTEGRITY AUDIT** | **🔴 当前最高优先级 / 唯一施工区** |
| CALCULATION_PROVEN | ❌ 尚未取得 |
| CALCULATION_FREEZE | ❌ 尚未取得 |
| SIGNAL | 🟡 BLOCKED_BY_CALC |
| OUTPUT | 🟡 暂不优化 |

### 当前禁止事项

- ❌ BATCH-0095 继续优化
- ❌ BATCH-0009 拆分
- ❌ Library 扩产
- ❌ 建第二批断言
- ❌ 用断言结果验证计算层
- ❌ 为了解释命中率修改 CALC
- ❌ **Assertion 反推修改 Canonical State**（严格禁止，否则会出现"自证循环"）

### 架构原则：解不能反过来改算

**只能**：
```
Canonical State → Signal → Assertion → Effect
```

**严格禁止**：
```
Assertion → 反推 → 修改 Canonical State
```

否则系统会出现危险的"自证循环"：
断言说应该有财 → 系统寻找财 → 找到一点类似财的结构 → 修改/解释 State → 断言命中 → 证明断言正确

这不是验证，这是循环论证。

**Canonical State 是事实层，必须真正成为不可逆的边界。**

---

## 一、总体原则（已冻结）

### 核心治理原则
- **原典才是 Canonical Authority**
- GitHub / JSON / 开源库 = implementation source / candidate index，不是授权来源
- 候选关系必须经过：候选索引 → 原典定位 → 原文核验 → Evidence Contract → 才能进入引擎
- 不为提高通过率强行授权
- 允许：SOURCE_SUPPORTED / SOURCE_SUPPORTED_WITH_QUALIFIER / SOURCE_MAPPED_NON_PROOF / INSUFFICIENT_SOURCE / SOURCE_CONTESTED

### 禁止项
- 禁止把传统命理语义偷偷转换成未经原典授权的：score / weight / threshold / 五行计分 / 强弱百分比 / 关键词强制判定
- 禁止：五行数量→score / 长生数量→score / 藏干数量→score / 党众→+10 / 助寡→-10 / 财多→身弱 / 印多→身强 / 合→强 / 冲→弱 / 刑→凶 / 空亡→力量×0.5
- 禁止：关键词→结论（如官杀多→从杀、财多→身弱、水多→身强/身弱、长生→根重）
- 禁止：MATCHED → 自动授权结论
- 禁止：原典关系成立 ≠ 最终命理结论成立

### 核心架构
```
L1 FACTS → L2 RELATIONS → L3 COMBINATIONS → L4 MODIFIERS → Canonical State → Assertion Preconditions → Matcher → Effect → Conclusion
```

### 三层状态永久分离
- EVIDENCE_STATUS ≠ MATCH_STATUS ≠ CONCLUSION_STATUS

---

## 二、P6.1 Canonical State（FROZEN）

### Authority Matrix：32 条
- FACT：8 条
- RELATION：16 条
- COMBINATION：4 条
- MODIFIER：4 条

### Canonical State 核心结构
```
wangshuai: 旺 / 衰 / UNRESOLVED
qiangruo: 强 / 弱 / UNRESOLVED
root_state: ROOT_HEAVY / ROOT_LIGHT / ROOT_PRESENT / ROOT_NONE / ROOT_UNRESOLVED
dangzhong: CONFIRMED / QUALIFIED / CANDIDATE / NOT_ESTABLISHED / UNRESOLVED
seasonal_remedy: 独立调候状态
special_pattern: candidate / confirmed / rejected / unresolved
qualifiers: [...]
unresolved_reasons: [...]
```

### 关键原则
- 旺衰 ≠ 强弱
- 《子平真诠》：得时为旺，失时为衰；党众为强，助寡为弱
- 存在：虽旺而弱 / 虽衰而强
- 根的层级：根之重（长生禄旺）/ 根之轻（墓库余气）/ 无根
- 干多不如根重

### 1983 命例 Resolver（8/8 PASS）
- 八字：癸亥 壬戌 乙未 壬午
- wangshuai = 衰
- root_state = ROOT_LIGHT / 部分 UNRESOLVED
- dangzhong = QUALIFIED
- qiangruo = UNRESOLVED

---

## 三、P6.2 Assertion Engine（FROZEN）

### 五层架构
Evidence → Preconditions → Matcher → Effect → Conclusion

### 7-Layer Admission Gate
1. Evidence
2. Precondition
3. Matcher
4. Effect
5. Conclusion
6. Reverse Condition
7. Test Coverage

### 当前 Library 状态
| ID | 断言 | 状态 |
|----|------|------|
| ASSERT-001 | 财星透干，逢流年合之，主进财 | POSTERIOR（NOT_AUTHORIZED） |
| ASSERT-002 | 身强杀浅，假杀为权 | AUTHORIZED_WITH_QUALIFIER |
| ASSERT-003 | 杀重身轻，终身有损 | AUTHORIZED_WITH_QUALIFIER |
| ASSERT-004 | 财多身弱，富屋贫人 | AUTHORIZED_WITH_QUALIFIER |
| ASSERT-005 | 伤官见官，为祸百端 | AUTHORIZED_WITH_QUALIFIER |

### 关键示范
- ASSERT-001：能算出来 ≠ 有资格下结论（EVIDENCE = SOURCE_MAPPED_NON_PROOF，CONCLUSION = NOT_AUTHORIZED）
- 五合 ≠ 合化
- 关系词（见、生、合、制、化、逢）不能简化成 boolean

---

## 四、P6.3 Cross-Domain Integration（FROZEN）

### 8/8 Integration Audit PASS
- C1：不重新计算（Assertion Engine 不得计算身强/身弱/旺衰/通根/十神/格局）
- C2：UNRESOLVED 传播（qiangruo=UNRESOLVED 必须阻断 ASSERT-002/003/004）
- C3：关系不能制造状态（财多≠身弱、伤官+官星≠伤官见官、食神+财星≠食神生财）
- C4：ASSERT-005 的「见官」语义必须保留（不能退化成 has_shangguan AND has_officer）
- C5：QUALIFIER 不得升级（AUTHORIZED_WITH_QUALIFIER 永远不能因为 Matcher 命中而变成 AUTHORIZED）
- C6：POSTERIOR 不得输出 Effect（ASSERT-001 即使 MATCHED 仍然 NOT_AUTHORIZED）
- C7：Reverse Condition 有效（伤官格+官星但伤官伤尽→不得输出为祸百端；财多+身强→不得输出富屋贫人）
- C8：输出层只消费最终授权状态（不能直接读取 raw_match/effect_text/evidence_text）

### P6.3-B-R Mutation / Semantic Regression（FROZEN）
- 故障注入测试证明 Matcher 没有语义退化
- 伤官存在 ≠ 伤官格
- 官星存在 ≠ 「见官」成立
- 伤官格 + 官星 ≠ 「为祸百端」

---

## 五、P6.4 Asset Production Protocol（FROZEN）

### 生产流水线
```
SOURCE → EXTRACTION → SEMANTIC_NORMALIZATION → EVIDENCE_CONTRACT → PRECONDITION_CONTRACT → MATCHER_CONTRACT → EFFECT_CONTRACT → REVERSE_CONDITION → QUALIFIER → TEST_MATRIX → ADMISSION_GATE → AUTHORIZED / AUTHORIZED_WITH_QUALIFIER / CANDIDATE / POSTERIOR / REJECTED
```

### 权限边界
- 豆包可以：搜索五部经典、定位原文、保存上下文、提取候选断语、标注关系词、提取前置条件/反向条件/qualifier、形成 AssertionCandidate
- 豆包不可以：自行把古文解释成现代规则、自行定义 STRONG/WEAK、自行定义杀浅/杀重/财多、自行把关系词简化成 boolean、自行授权 Effect、自行决定 AUTHORIZED、自行写入 Authorized Assertion Library

### ASSERT-006 状态
- 「食神生财，富贵自天来」
- EVIDENCE：CANDIDATE（食神生财结构有原典依据，但「富贵自天来」Effect 无直接原典授权）
- 结论：结构成立 ≠ Effect 获得授权

---

## 六、P6.5 Batch Assertion Production（进行中）

### P6.5-A Batch Production（COMPLETE）
- 100 条候选断言提取

### P6.5-A-R Verification Audit（COMPLETE）
- 发现批量语义退化问题
- 32 条原始授权 → 16 条最终授权

### P6.5-B Producer Hardening（COMPLETE / 8-8 PASS）
- 修复三个结构缺陷：
  1. Effect Extraction 结构化（区分 CONDITION / RELATION / QUALIFIER / EFFECT / CASE_CONTEXT）
  2. Assertion Type 硬门槛（CASE_COMMENTARY / THEORY_OVERVIEW / EXAMPLE / DESCRIPTIVE 不得进入 Admission）
  3. Admission 与 Score 完全解耦（score 只是 prioritization signal，不是授权条件）

### P6.5-B-R Integrity Audit（COMPLETE）
- 对 15 条 AUTHORIZED 逐条审计

### P6.5-B-R2 Semantic Boundary Hardening（COMPLETE）
- 6 种断言类型：EXECUTABLE_ASSERTION / STRUCTURAL_ASSERTION / PRESCRIPTIVE_ASSERTION / THEORY_OVERVIEW / CASE_COMMENTARY / DESCRIPTIVE
- 6 种 Effect 类型：INTERMEDIATE_REASONING / RELATION / QUALIFIER / PRESCRIPTION / CASE_RESULT / ASSERTION_EFFECT
- STRUCTURAL_ASSERTION 进入 Structural Knowledge Library，不伪装成断事 Effect Rule
- 互斥路由：EXECUTABLE_ASSERTION→EXECUTABLE_LIBRARY / STRUCTURAL_ASSERTION→STRUCTURAL_LIBRARY / PRESCRIPTIVE_ASSERTION→NON_EXECUTABLE / 其他→REJECTED

### P6.5-B-R3 Executable Asset Integrity Audit（COMPLETE）
- 12 项完整性审计
- 发现 BATCH-0007 分类冲突（PRESCRIPTIVE_ASSERTION vs STRUCTURAL）
- 发现 UNCLASSIFIED 仍存在于 Effect 分类

### P6.5-B-R4 Provenance + Extraction Closure Repair（COMPLETE）
- 修复三个根问题：
  1. **Effect Classification 闭集**：禁止 UNCLASSIFIED，无法归入 6 类的 → EFFECT_CLASSIFICATION_FAILED → 不得进入 EXECUTABLE_LIBRARY
  2. **Condition Extraction 完整性**：支持无显式条件连接词的并列条件链，修复 BATCH-0079（劫刃重+财星轻+有食伤+逢枭印）和 BATCH-0080（杀重身轻+财星党杀+...+财星得局者）
  3. **Effect Provenance 完整性**：classic → source_file → chapter/section → source_span → source_text
- V3 回归结果（100 条）：EXECUTABLE_LIBRARY 7 条 / STRUCTURAL_LIBRARY 23 条 / NON_EXECUTABLE 1 条 / REJECTED 69 条
- Classification Consistency：100/100 CONSISTENT，0 INCONSISTENT
- UNCLASSIFIED = 0（闭集已闭合）

### P6.5-B-R5 Executable Provenance Closure Audit（COMPLETE）
- 对 7 条 EXECUTABLE 逐条定位原典
- 新增 Provenance Integrity Gate（9 项）
- 结果：
  - **PROVEN_EXECUTABLE：6 条**（9/9 Provenance Gate PASS + 12/12 Integrity Audit PASS）
  - PROVEN_EXECUTABLE_WITH_QUALIFIER：1 条（BATCH-0009，原典中未找到精确匹配）
- 6 条 PROVEN_EXECUTABLE 明细：
  - BATCH-0054：柱中有官星相制，必得贤贵之解（十九、源流章，char_position=45071）
  - BATCH-0055：如阴节是财星，必遭妻妾之祸（十九、源流章，char_position=45100）
  - BATCH-0056：有财星之化，必得美妻，或中馈多能（十九、源流章，char_position=45188）
  - BATCH-0057：如阻节是官煞，必遭官刑之祸（十九、源流章，char_position=45205）
  - BATCH-0079：劫刃重，财星轻，有食伤，逢枭印，主妻遭凶死（一、夫妻章，char_position=70467，4 条件）
  - BATCH-0080：杀重身轻，财星党杀，官多用印，财星坏印，伤官佩印，财星得局者，主妻不贤而陋（一、夫妻章，char_position=70591，6 条件）

### P6.5-B-R6 Authorized Library Admission & Identity Integrity Audit（COMPLETE）✅ 当前最新
- 一次性做四件事：
  1. **Identity / ID consistency**：检查并修正 BATCH-0009 vs BATCH-0095 的分类错误
  2. **Provenance final verification**：6 条 PROVEN_EXECUTABLE 的最终验证
  3. **12-item Integrity recheck**：重新跑 12 项 Integrity Audit
  4. **Authorization admission**：正式授权入库

- **重大发现：P6.5-B-R4 存在两个分类错误**
  - **BATCH-0009**："壬午己巳此造以俗论之..."包含"此造"，是 CASE_COMMENTARY，不应进入 EXECUTABLE_LIBRARY
  - **BATCH-0095**："如见官星，则曾祖必受其伤..."是真正的可执行断言，不应被 REJECTED 为 DESCRIPTIVE

- **6 条真正的 PROVEN_EXECUTABLE 全部通过最终验证**
  - 7/7 Provenance PASS + 12/12 Integrity PASS，0 WARNING
  - 全部 AUTHORIZED（无 QUALIFIER）

- **正式 Authorized Assertion Library 建立（P6.5 批次）**
  | 正式 ID | 原文 | 章节 | 条件数 | 授权状态 |
  |---------|------|------|--------|----------|
  | ASSERTION-0054 | 柱中有官星相制，必得贤贵之解 | 十九、源流 / 通神论 | 1 | AUTHORIZED |
  | ASSERTION-0055 | 如阴节是财星，必遭妻妾之祸 | 十九、源流 / 通神论 | 1 | AUTHORIZED |
  | ASSERTION-0056 | 有财星之化，必得美妻，或中馈多能 | 十九、源流 / 通神论 | 1 | AUTHORIZED |
  | ASSERTION-0057 | 如阻节是官煞，必遭官刑之祸 | 十九、源流 / 通神论 | 1 | AUTHORIZED |
  | ASSERTION-0079 | 劫刃重，财星轻，有食伤，逢枭印，主妻遭凶死 | 一、夫妻 / 六亲论 | 4 | AUTHORIZED |
  | ASSERTION-0080 | 杀重身轻，财星党杀，官多用印，财星坏印，伤官佩印，财星得局者，主妻不贤而陋 | 一、夫妻 / 六亲论 | 6 | AUTHORIZED |

- **隔离区（UNRESOLVED_PROVENANCE）**
  - BATCH-0009：CASE_COMMENTARY（包含"此造"），移出 EXECUTABLE_LIBRARY
  - BATCH-0095：MISCLASSIFIED（被错误分类为 DESCRIPTIVE），需重新做 Provenance 审计

- **EXECUTABLE ASSET PROVENANCE CLOSURE（修正后）**
  - PROVEN_EXECUTABLE：6 条
  - PROVEN_EXECUTABLE_WITH_QUALIFIER：0 条
  - UNRESOLVED_PROVENANCE：2 条（BATCH-0009, BATCH-0095）
  - **STATUS = PARTIALLY PROVEN**（6 条正式授权，2 条隔离待处理）

- **治理修正**
  - 原表述"Executable Asset Provenance Closure = PROVEN（6/7）"修正为
  - "STATUS = PARTIALLY PROVEN（6 条正式授权，2 条隔离待处理）"
  - 因为 7/7 并没有完成 provenance closure，只有 6/7 完整闭环（且 BATCH-0009 是分类错误）

### P6.5-C 第二批批量生产（BLOCKED）
- **BLOCKED 原因**：
  1. BATCH-0009/BATCH-0095 待处理
  2. 正式 Library 刚建立需稳定
  3. 第二批生产必须继承 R2/R4/R5/R6 全部 Gate，不能因为第一批通过就放宽标准
- **解除条件**：
  1. BATCH-0009/BATCH-0095 处理完毕
  2. 正式 Library 稳定运行
  3. 第二批生产协议确认继承全部 Gate 标准

---

## 七、当前完整 Authorized Assertion Library（汇总）

### 来自 P6.2 的授权断言（4 条 AUTHORIZED_WITH_QUALIFIER）
| ID | 断言 | 状态 |
|----|------|------|
| ASSERT-002 | 身强杀浅，假杀为权 | AUTHORIZED_WITH_QUALIFIER |
| ASSERT-003 | 杀重身轻，终身有损 | AUTHORIZED_WITH_QUALIFIER |
| ASSERT-004 | 财多身弱，富屋贫人 | AUTHORIZED_WITH_QUALIFIER |
| ASSERT-005 | 伤官见官，为祸百端 | AUTHORIZED_WITH_QUALIFIER |

### 来自 P6.5-B-R6 的授权断言（6 条 AUTHORIZED）
| ID | 断言 | 状态 |
|----|------|------|
| ASSERTION-0054 | 柱中有官星相制，必得贤贵之解 | AUTHORIZED |
| ASSERTION-0055 | 如阴节是财星，必遭妻妾之祸 | AUTHORIZED |
| ASSERTION-0056 | 有财星之化，必得美妻，或中馈多能 | AUTHORIZED |
| ASSERTION-0057 | 如阻节是官煞，必遭官刑之祸 | AUTHORIZED |
| ASSERTION-0079 | 劫刃重，财星轻，有食伤，逢枭印，主妻遭凶死 | AUTHORIZED |
| ASSERTION-0080 | 杀重身轻，财星党杀，官多用印，财星坏印，伤官佩印，财星得局者，主妻不贤而陋 | AUTHORIZED |

### POSTERIOR（1 条）
| ID | 断言 | 状态 |
|----|------|------|
| ASSERT-001 | 财星透干，逢流年合之，主进财 | POSTERIOR（NOT_AUTHORIZED） |

### CANDIDATE（1 条）
| ID | 断言 | 状态 |
|----|------|------|
| ASSERT-006 | 食神生财，富贵自天来 | CANDIDATE（Effect 无原典授权） |

### 隔离区（UNRESOLVED_PROVENANCE，2 条）
| ID | 原文 | 隔离类别 |
|----|------|----------|
| BATCH-0009 | 壬午己巳此造以俗论之，干透三奇之美... | CASE_COMMENTARY |
| BATCH-0095 | 如见官星，谓孙又生儿，则曾祖必受其伤... | MISCLASSIFIED |

---

## 八、本地资料路径

### 五部经典完整数据
- `D:\today\Canonical-Mining\五部经典完整数据\`
  - DTS_滴天髓_完整全文.md
  - DTS_滴天髓_段落数据.json（719 段）
  - 其他经典文件...

### 完整原典补充
- `D:\today\Canonical-Mining\完整原典补充\`
  - 滴天髓阐微_garychowcmu.txt（139556 字符，P6.5 批次 6 条 AUTHORIZED 的来源）

### FOR-BAZI 五书 JSON
- `D:\today\Canonical-Mining\FOR-BAZI五书JSON\`
  - 关系候选生成器 + 知识点索引（不是原典证据）
  - 穷通宝鉴 120 条调候用神表（候选知识）
  - 子平真诠格局结构模板（参考格式）

### 五部经典断语库
- `D:\today\五部经典断语库\`

---

## 九、项目文件路径

### 脚本
- `D:\shuntian\backend\scripts\str001a_p6_5_b_r4_closure_repair.py`
- `D:\shuntian\backend\scripts\str001a_p6_5_b_r5_provenance_closure.py`
- `D:\shuntian\backend\scripts\str001a_p6_5_b_r6_authorized_library.py`

### 数据
- `D:\shuntian\backend\data\p6_5_batch_results.json`（原始 100 条候选）
- `D:\shuntian\backend\data\p6_5_b_r4_closure_repair_results.json`
- `D:\shuntian\backend\data\p6_5_b_r5_provenance_closure_results.json`
- `D:\shuntian\backend\data\p6_5_b_r6_authorized_library_results.json`（当前最新）

---

## 十、当前唯一施工阶段：CALCULATION INTEGRITY AUDIT

**CALCULATION INTEGRITY AUDIT 是当前最高优先级 / 唯一施工区。完成后停下来人工审，不自动跳阶段。**

### 整体路线

```
CALCULATION INTEGRITY AUDIT
    ↓
C0 输入层（公历/农历/时区/DST/真太阳时/换日规则）
C1 四柱计算（年柱/月柱/日柱/时柱）
C2 日主与藏干（Day Master / Hidden Stems）
C3 十神计算（Ten Gods）
C4 月令与五行（Month Order / Wu Xing）
C5 旺衰计算（Wang Shuai）
C6 关系计算（天干五合/地支六合/三合/三会/冲/刑/害/破）
C7 时间展开（大运/流年/流月/流日/起运/交运/节气边界）
C8 紫微（农历转换/命宫/身宫/十二宫/主星/辅星/四化/大限/流年）
C9 河洛（本命/元堂/后天/年/月/日/时/节候/卦气）
C10 Canonical State 整合验证
    ↓
CALCULATION_PROVEN
    ↓
CALCULATION_FREEZE
    ↓
解除 P6-SIGNAL BLOCK
    ↓
再恢复 P6.5-C
```

### 核心交付物：CALCULATION_GOLDEN_DATASET

每个案例记录**整个计算状态**，而不只是 expected 断事：

```
CASE
 ├─ input（公历/农历/出生时间/地点/时区/DST/真太阳时）
 ├─ calendar（历法转换）
 ├─ timezone（时区处理）
 ├─ solar_time（真太阳时）
 ├─ pillars（年柱/月柱/日柱/时柱）
 ├─ day_master（日主）
 ├─ hidden_stems（藏干）
 ├─ ten_gods（十神）
 ├─ wuxing（五行）
 ├─ strength（旺衰/强弱）
 ├─ relations（天干五合/地支六合/三合/三会/冲/刑/害/破）
 ├─ dayun（大运）
 ├─ liunian（流年）
 ├─ liuyue（流月）
 ├─ liuri（流日）
 ├─ ziwei（紫微）
 ├─ heluo（河洛）
 └─ canonical_state（最终状态）
```

这样以后任何 Bug 都可以精确定位：输入错？历法错？四柱错？日主错？十神错？关系错？大运错？紫微错？河洛错？

### Boundary Cases（真正要打的）

普通案例反而不是最危险的，真正要打的是：

- 子初前 / 子初后
- 节气前 / 节气后
- 立春前 / 立春后
- 真太阳时跨时辰
- 时区跨日
- DST
- 农历闰月
- 年柱切换
- 月柱切换
- 日柱切换
- 大运交界

### 第一步：C0-C3 基础计算验证

从最基础、最容易出错的部分开始（也是之前日主 Bug 直接暴露的层级）：

**C0 输入层 + C1 四柱计算 + C2 日主与藏干 + C3 十神计算**

#### 第一步具体任务

1. **盘点当前已有的计算引擎代码**
   - 排盘系统（bazi-patterns 等开源库）的输出结构
   - 当前 Canonical State Resolver 使用的计算逻辑
   - 之前日主 Bug 的具体位置和修复状态

2. **建立 CALCULATION_GOLDEN_DATASET 的基础结构**
   - 定义 C0-C3 的字段结构
   - 准备 10-20 个基础案例（包括 Boundary Cases）
   - 人工标注 expected 结果（作为 Golden Truth）

3. **运行当前计算引擎，对比 Golden Truth**
   - 逐字段对比
   - 记录每个字段的 PASS/FAIL
   - 精确定位错误来源

4. **生成 C0-C3 计算完整性报告**
   - 通过率统计
   - 错误分类
   - 修复建议

#### 第一步验收标准

- CALCULATION_GOLDEN_DATASET 基础结构建立
- 10-20 个案例（含 Boundary Cases）的 Golden Truth 标注
- 当前计算引擎的逐字段对比结果
- C0-C3 计算完整性报告
- 错误精确定位到具体计算模块

### 断言资产后续处理（待 CALC 完成后）

1. 处理 BATCH-0095 的重新审计（可能成为第 7 条 AUTHORIZED）
2. 处理 BATCH-0009 的拆分（提取"官星得用，主名利双收"）
3. 整合 P6.2 的 4 条 AUTHORIZED_WITH_QUALIFIER 到正式 Library
4. 建立正式 Authorized Assertion Library 的持久化存储（JSON/YAML）
5. 解除 P6.5-C BLOCKED，启动第二批批量生产

---

## 十一、关键治理契约（永久有效）

1. **原典才是 Canonical Authority**，GitHub/JSON/开源库只是 implementation source / candidate index
2. **原典关系成立 ≠ 最终命理结论成立**，EVIDENCE_STATUS ≠ MATCH_STATUS ≠ CONCLUSION_STATUS
3. **结构成立 ≠ Effect 获得授权**（如 ASSERT-006 食神生财结构成立，但"富贵自天来"Effect 无原典授权）
4. **能算出来 ≠ 有资格下结论**（如 ASSERT-001 条件可匹配，但结论 NOT_AUTHORIZED）
5. **任何 provenance 缺失都不得称为 PROVEN_EXECUTABLE**
6. **第二批生产必须继承全部 Gate 标准**，不能因为第一批通过就放宽
7. **豆包无权自行授权断言**，所有断言必须经过独立的 Evidence / Admission / Reverse / Test 审核
8. **不修改已冻结的 P6.1-P6.4**

---

**快照保存完成。后续直接从"下一步建议"继续，不再重复前面的长上下文。**
