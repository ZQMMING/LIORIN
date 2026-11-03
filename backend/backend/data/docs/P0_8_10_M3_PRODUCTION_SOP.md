# Assertion 生产SOP（标准作业程序）

**版本**: v1.0  
**日期**: 2026-08-31  
**阶段**: P0-8.10 M3

---

## 一、生产流程（六步）

```
Step 1: 原典Evidence定位
   ↓
Step 2: 最小命题提取
   ↓
Step 3: Semantic Relation判定
   ↓
Step 4: Condition推导
   ↓
Step 5: Primitive提取
   ↓
Step 6: 真实执行验证
   ↓
Step 7: 四问裁决
   ↓
Step 8: 最终裁决（COMPLETE/REJECT）
```

---

## 二、Step 1: 原典Evidence定位

### 要求
- 必须来自五书原典原文
- 禁止使用后世整理表格
- 禁止使用现代解释
- 禁止使用英文资料

### 检查项
- [ ] 书名正确（PZZQ/YHZP/DTS/QTBJ/SMTH）
- [ ] 章节正确
- [ ] 行号精确
- [ ] 上下文≥50字
- [ ] 是原典原文（非表格/非注释）

### 输出格式
```json
{
  "source": "PZZQ",
  "chapter": "论食神格",
  "line": "~1200",
  "context": ">50字原文",
  "evidence_span": "具体原文片段",
  "raw_text": "完整原文引用"
}
```

---

## 三、Step 2: 最小命题提取

### 要求
- 必须是原子命题（不可再分）
- 不能合并多个独立条件
- 不能包含多个结论
- 原典真值结构必须完整

### 判断标准
```
Atomic = 
在不改变原典真值条件的前提下，
不可进一步拆分的最小语义命题。
```

### 禁止行为
- ❌ 把"A∧B∧C→结论"拆成"A→结论"、"B→结论"、"C→结论"
- ❌ 把多个条件组合压缩成一个简单命题
- ❌ 把多个结论合并成一个命题

### 输出格式
```json
{
  "minimal_proposition": "完整命题表述",
  "is_atomic": true,
  "atomic_justification": "为什么不可再分"
}
```

---

## 四、Step 3: Semantic Relation判定

### 要求
- 必须明确关系类型
- 必须明确关系方向
- 必须评估证据强度

### 关系类型
- 成格条件
- 败格条件
- 理论原则（→ SEMANTIC_ONLY，REJECT）
- 评价性命题（→ SEMANTIC_ONLY，REJECT）

### 输出格式
```json
{
  "relation_type": "成格条件",
  "relation_direction": "正向",
  "evidence_strength": "强/中/弱",
  "is_semantic_only": false
}
```

---

## 五、Step 4: Condition推导

### 要求
- 必须从Evidence Span独立推导
- 不得参考现有Primitive/Condition反向证明
- 不得引入外部知识

### 检查项
- [ ] Condition在Evidence Span中有明确依据
- [ ] Condition没有超出Evidence范围
- [ ] Condition不包含未提及的条件

### 输出格式
```json
{
  "condition": "条件表述",
  "condition_source": "Evidence Span中的具体位置",
  "is_supported": true
}
```

---

## 六、Step 5: Primitive提取

### 要求
- 必须忠实于Condition
- 不得扩张语义
- 不得压缩语义

### 检查项
- [ ] Primitive与Condition语义等价
- [ ] Primitive不包含额外信息
- [ ] Primitive缺少必要信息

### 输出格式
```json
{
  "primitive": "Primitive表述",
  "primitive_match": "与Condition是否一致",
  "semantic_overreach": false
}
```

---

## 七、Step 6: 真实执行验证

### 要求
**这是最关键的新增步骤！**

必须通过真实的Canonical State执行，验证Primitive/Condition是否能正确产生Expected Result。

### 验证方法
1. 构造测试用例（输入 Canonical State）
2. 执行Assertion逻辑
3. 对比预期结果与实际结果
4. 记录验证结果

### 示例
```
Input: 日干甲，月令寅，时干丙（食神生财格）
Expected: 成格
Actual: 成格
Verification: PASS
```

### 输出格式
```json
{
  "test_case": "测试用例描述",
  "input_state": "输入Canonical State",
  "expected_result": "预期结果",
  "actual_result": "实际结果",
  "verification": "PASS/FAIL",
  "verification_detail": "详细说明"
}
```

---

## 八、Step 7: 四问裁决

### 问题1: 原典到底说什么？
- 回到Evidence Span，逐字核对
- 不被现有Primitive/Condition影响
- 独立判断原典真实含义

### 问题2: 最小语义命题是什么？
- 能否进一步精简？
- 是否合并了多个条件？
- 是否包含了多个结论？

### 问题3: semantic_relation是否完整？
- 关系类型是否正确？
- 关系方向是否明确？
- 证据强度是否足够？

### 问题4: Condition Primitive是否忠实？
- Condition是否有Evidence支持？
- Primitive是否与Condition等价？
- 是否存在语义扩张或压缩？

### 输出格式
```json
{
  "question_1": "原典到底说什么？",
  "answer_1": "独立判断结果",
  "question_2": "最小命题是什么？",
  "answer_2": "独立判断结果",
  "question_3": "semantic_relation是否完整？",
  "answer_3": "独立判断结果",
  "question_4": "Condition Primitive是否忠实？",
  "answer_4": "独立判断结果",
  "all_pass": true/false
}
```

---

## 九、Step 8: 最终裁决

### 裁决标准
```
COMPLETE = 所有七步验证通过
REJECT = 任一步骤失败或证据不足
```

### 禁止行为
- ❌ 产生PARTIAL状态
- ❌ 因为数量压力降低标准
- ❌ 因为已有Assertion而放松验证

### 输出格式
```json
{
  "passage_id": "唯一标识符",
  "final_verdict": "COMPLETE/REJECT",
  "verdict_justification": "裁决依据",
  "timestamp": "ISO 8601时间戳"
}
```

---

## 十、质量控制

### 一致性检查清单

#### Evidence层
- [ ] 来源是五书原典原文
- [ ] 书名/章节/行号正确
- [ ] 上下文≥50字
- [ ] 不包含现代解释/英文

#### 命题层
- [ ] 是原子命题（不可再分）
- [ ] 原典真值结构完整
- [ ] 主体一致（十神名称无替换）
- [ ] 条件一致（无遗漏/无添加）
- [ ] 结论一致（格局名称无替换）

#### 关系层
- [ ] 关系类型明确
- [ ] 关系方向明确
- [ ] 证据强度评估合理

#### 执行层
- [ ] 真实Canonical State验证通过
- [ ] 预期结果与实际结果一致
- [ ] 验证用例覆盖边界情况

#### 裁决层
- [ ] 四问裁决全部通过
- [ ] 不参考现有Assertion反向证明
- [ ] 独立原典判断

---

## 十一、REJECT标准

### 必须REJECT的情况
1. Evidence来源不是原典原文
2. 无法精确定位原典位置
3. 是理论原则/评价性命题（SEMANTIC_ONLY）
4. 主体不一致（十神名称被替换）
5. 条件/结论不一致
6. 执行验证失败
7. 四问裁决有FAIL

### REJECT处理
- 记录REJECT原因
- 不进入资产库
- 可作为案例学习

---

## 十二、交付要求

### 每条Assertion必须输出
1. Evidence Span原文
2. 最小命题
3. Semantic Relation
4. Condition
5. Primitive
6. 执行验证结果
7. 四问裁决记录
8. 最终裁决

### 完整审计链
必须能追溯到原始原典，不得断链。

---

**状态**: SOP v1.0 已建立，适用于M3生产流程
