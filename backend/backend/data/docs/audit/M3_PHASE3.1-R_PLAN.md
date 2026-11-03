# M3 Phase 3.1-R 原典重建计划

**时间**: 2026-08-31  
**依据**: GPT Final Ruling (4762e19)  
**状态**: 🟢 批准启动

---

## 背景

### 第1批失败样本分析

**DTS-GEJU-001 ~ 005 全部 DENIED**

**核心问题**:
```
我们不能从经典中看到几个相关概念，就自行把它们组合成现代程序条件。
```

**具体表现**:
- DTS-GEJU-001/002: 原典谈旺衰/根气，但没证明"得令+透干+生扶→成格"
- DTS-GEJU-003/004: Evidence是简化描述，没证明AND Composite授权
- DTS-GEJU-005: 涉及L4力量问题（KE_XIE_HAO_DOMINANT），高风险

**价值**: 这5条失败样本暴露了我们真正的问题——生产规范有误。

---

## 新路线：M3 Phase 3.1-R（原典重建）

### 核心理念转变

**旧路线（错误）**:
```
经典原文 → 找现成规则 → 翻译成if/else → 生产断言
```

**新路线（正确）**:
```
经典原文
  ↓
辨认它究竟描述的是：
  - 事实？
  - 关系？
  - 条件？
  - 判断？
  - 经验性结论？
  ↓
只有能被Canonical State确定表达的
  → 进入计算链
否则
  → 进入RESEARCH_ONLY
```

### 生产规范修正

**必须建立**:
```
原典原句
  ↓
原典语义单元
  ↓
Primitive
  ↓
原典明确关系（必须是原典明确说"A且B则C"）
  ↓
允许的Condition
  ↓
允许的Judgment
```

**禁止**:
```
❌ 看到几个相关概念就组合
❌ 工程推断"A+B+C→成格"
❌ 用paraphrase代替原文
❌ 用classical_authorization字段代替原典授权
```

---

## 执行步骤

### Step 1: 原典重建规范制定（预计30分钟）

**目标**: 建立Evidence → Primitive → Condition → Judgment的生产规范

**规范内容**:
```
1. Evidence规范
   - 必须是逐字原文（非paraphrase）
   - 必须标注text_layer（ORIGINAL_TEXT/ORIGINAL_COMMENTARY/LATER_COMMENTARY）
   - 必须标注verification_status（UNVERIFIED/EXACT_MATCH/PARTIAL_MATCH/NOT_FOUND/CONFLICT）
   - pending_verification是合法中间状态，不能自动升级

2. Primitive规范
   - 必须是原典明确描述的最小语义单元
   - 必须有classical_source绑定
   - 不能有工程推断的Primitive

3. Condition规范
   - 必须能从Canonical State直接得出
   - 不能涉及L4力量问题（旺衰/得势等）
   - 不能偷偷重新计算命理

4. Composite规范
   - 必须有原典明确授权（原典说"若A且B则C"）
   - 不能工程推断"A+B→C"
   - classical_authorization字段必须引用真实原文

5. Judgment规范
   - 不能超出原典授权范围
   - 原典讨论旺衰，就不能直接跳到"成格"
   - 必须保持语义忠实
```

### Step 2: 重新核验5条失败断言（预计60分钟）

**目标**: 用新规范重新审视DTS-GEJU-001~005

**方法**:
1. 获取《滴天髓·通神论》完整原文（任铁樵《滴天髓阐微》通行本）
2. 逐句定位：原典到底在说什么？
3. 辨认语义单元：这是事实？关系？条件？判断？
4. 重新评估：哪些能进入计算链？哪些必须RESEARCH_ONLY？

### Step 3: 重建生产代码（预计90分钟）

**目标**: 根据新规范重写DTS-GEJU-001~005

**原则**:
- 能找到原典明确授权的 → 进入Production
- 找不到原典明确授权的 → RESEARCH_ONLY
- 宁可少，不能错

### Step 4: Claude独立审计（预计30分钟）

**目标**: 验证重建后的断言是否符合新规范

**检查项**:
- Evidence是否是逐字原文
- Primitive是否忠实原典语义
- Composite是否有原典明确授权
- Judgment是否超出原典范围
- 是否涉及L4力量问题

### Step 5: GPT裁决（预计10分钟）

**目标**: 裁决哪些断言可以获得Production Authorization

---

## 质量门禁（修正版）

### 单条断言标准

```
✅ Evidence: 逐字原文，非paraphrase
✅ text_layer: 正确标注（ORIGINAL_TEXT/ORIGINAL_COMMENTARY/LATER_COMMENTARY）
✅ verification_status: 已核验（EXACT_MATCH/PARTIAL_MATCH），不是pending
✅ Primitive: 原典明确描述的最小语义单元
✅ Condition: 可从Canonical State直接得出，不涉及L4
✅ Composite: 原典明确授权AND关系（原典说"若A且B则C"）
✅ Judgment: 不超出原典授权范围
✅ classical_authorization: 引用真实原文，不是字段自证
```

### 批量标准（每5条）

```
✅ Claude独立审计：全部通过
✅ GPT裁决：授权进入Production
✅ 测试通过：1797+新测试，0 failed
✅ 无Legacy调用：verify_legacy_calls.py 0
✅ 无XPassed：pytest --tb=short 0 xpassed
✅ 可追溯链：每条断言完整trace
```

---

## 禁止行为（铁律）

```
🔴 禁止从经典中看到几个相关概念就组合
🔴 禁止工程推断"A+B+C→成格"
🔴 禁止用paraphrase代替原文
🔴 禁止用classical_authorization字段代替原典授权
🔴 禁止跳过Evidence核验直接生产
🔴 禁止涉及L4力量问题的断言进入Production
🔴 禁止恢复Legacy调用
🔴 禁止使用wang_score阈值
🔴 禁止无审计批量生产
```

---

## 预期结果

**可能情况**:
- 5条断言中0~2条能通过重建获得Production Authorization
- 其余必须降级为RESEARCH_ONLY
- 这是正常结果——准确性优先于数量

**成功标准**:
- 不是"5条全部通过"
- 而是"通过的都是真正有原典授权的"
- 宁可100条高可信，不要1000条无法核验

---

## Git提交计划

```
[当前] 4762e19 Claude独立语义审计报告
[下一步] M3_PHASE3.1-R_PLAN.md - 原典重建计划
[后续] 每次重建后提交commit
[最终] GPT_RULING_M3_PHASE3.1-R.md - GPT裁决
```

---

**等待Hermes执行新路线。**

不是坏结果，反而是一次非常有价值的审计。