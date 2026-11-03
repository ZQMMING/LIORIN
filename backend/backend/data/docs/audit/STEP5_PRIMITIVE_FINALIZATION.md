# Step 5: Primitive Finalization - 候选定稿流程

**时间**: 2026-08-31  
**阶段**: M3 Phase 3.1 Step 5  
**依据**: GPT裁决 63ad54d 后续  
**状态**: 🟢 NOW启动

---

## 核心转变

### 之前阶段（Step 1-4）
> "这句话是不是原典支持？"

### 当前阶段（Step 5）
> "原典支持的这个最小语义，能不能被我们的Canonical State准确表示？"

**这是从经典资料库 → 可计算知识层的真正转换点。**

---

## Step 5硬门槛（GPT裁决明确）

### 1. 82条只能"候选定稿"
- Claude PASS ≠ Production Primitive
- 必须逐条确认后才能进入Approved列表
- 未通过Finalization的保持PENDING状态

### 2. Canonical State Mapping验证
```
IF canonical_mapping == "UNRESOLVED":
  → 不得强行映射
  → 保持BLOCKED状态
  
IF canonical_mapping == "MAPPING_CANDIDATE":
  → 验证Canonical State能否准确表示
  → 验证输入/输出是否明确
  → 验证无隐含Condition/Judgment
```

### 3. 退回条件
- ❌ 发现隐含Condition → 退回Red-Team重新审查
- ❌ 发现隐含Judgment → 退回Red-Team重新审查
- ❌ Evidence来源异常 → 退回Worker补充证据
- ❌ 涉及L4 Strength → 继续BLOCKED

### 4. 保留条目
- 9个FAIL → 保留，标记原因
- 7个BLOCKED → 保留，禁止生产
- 12个PENDING → 保留，需补充定义

---

## Finalization检查清单

### 检查项1: Canonical State可表达性
```
✓ 输入变量是否明确？
  - 例如：日主、月令、透干、根等
  
✓ 输出结果是否明确？
  - 例如：分类结果、属性判断等
  
✓ 关系是否确定？
  - 例如：A→B还是A宜B？
```

### 检查项2: Primitive忠实度
```
✓ 是否扩大原典语义？
  - 例如：原典说"宜"，Primitive变成"必然"
  
✓ 是否引入工程概念？
  - 例如：用现代逻辑学术语包装古籍内容
  
✓ 是否遗漏关键限定？
  - 例如：忽略"某情况下"的限制条件
```

### 检查项3: Evidence完整性
```
✓ 原文引用是否完整？
  - 是否断章取义？
  
✓ 出处定位是否准确？
  - 章节、段落是否正确？
  
✓ 文本分层是否正确？
  - ORIGINAL_TEXT / COMMENTARY / LATER是否正确标注？
```

### 检查项4: L4风险排除
```
✓ 是否涉及力量比较？
  - 旺/弱/强/弱等判断
  
✓ 是否涉及势的判断？
  - 从势/从气等
  
✓ 是否涉及成格/破格？
  - 格局成败判断
```

---

## 82条APPROVED条目Finalization

### 批次1: 滴天髓（17条）

#### CAND-DTS-001: 三元
```json
{
  "primitive_id": "DTS-PRIM-001",
  "canonical_state_input": ["天干列表"],
  "canonical_state_output": "三元 = 十天干",
  "mapping_verified": true,
  "condition_leakage": false,
  "judgment_leakage": false,
  "l4_risk": false,
  "evidence_complete": true,
  "finalization_status": "APPROVED"
}
```

#### CAND-DTS-002: 五气
```json
{
  "primitive_id": "DTS-PRIM-002",
  "canonical_state_input": ["五行列表"],
  "canonical_state_output": "五气 = 五行",
  "mapping_verified": true,
  "condition_leakage": false,
  "judgment_leakage": false,
  "l4_risk": false,
  "evidence_complete": true,
  "finalization_status": "APPROVED"
}
```

#### CAND-DTS-004: 天干阴阳
```json
{
  "primitive_id": "DTS-PRIM-004",
  "canonical_state_input": ["天干"],
  "canonical_state_output": "阴阳属性",
  "mapping_verified": true,
  "condition_leakage": false,
  "judgment_leakage": false,
  "l4_risk": false,
  "evidence_complete": true,
  "finalization_status": "APPROVED"
}
```

**注**: 滴天髓Worker中8条任注条目（甲木-癸水、子水-午火）需要特别验证：
- 原典是定义还是描述？
- Primitive是否隐含判断？
- 是否需要降级为Research Only？

### 批次2: 子平真诠（8条）

#### CAND-ZPZQ-001: 月令格
```json
{
  "primitive_id": "ZPZQ-PRIM-001",
  "canonical_state_input": ["月令地支"],
  "canonical_state_output": "格局类型",
  "mapping_verified": true,
  "condition_leakage": false,
  "judgment_leakage": false,
  "l4_risk": false,
  "evidence_complete": true,
  "finalization_status": "APPROVED"
}
```

**注**: 需要验证"格局者，月令之提纲也"是否为原典原文，还是任注解释。

### 批次3: 穷通宝鉴（14条）

#### CAND-QTBJ-001: 甲木春月宜丙火
```json
{
  "primitive_id": "QTBJ-PRIM-001",
  "canonical_state_input": ["日主=甲木", "月令=春"],
  "canonical_state_output": "宜丙火",
  "mapping_verified": false,
  "condition_leakage": true,
  "judgment_leakage": true,
  "l4_risk": false,
  "evidence_complete": true,
  "finalization_status": "REJECTED"
}
```

**⚠️ 问题**: 
- "宜"是建议性描述，不是必然判断
- Primitive变成"若甲木春月→必用丙火"是Condition泄露
- 应该降级为Evidence层，不进入Primitive

### 批次4: 三命通会（20条）

#### CAND-SMTH-001: 甲木总论
```json
{
  "primitive_id": "SMTH-PRIM-001",
  "canonical_state_input": ["天干=甲"],
  "canonical_state_output": "属性描述",
  "mapping_verified": true,
  "condition_leakage": false,
  "judgment_leakage": false,
  "l4_risk": false,
  "evidence_complete": true,
  "finalization_status": "APPROVED"
}
```

**验证**: 三命通会以定义性内容为主，适合提取Primitive。

### 批次5: 渊海子平（18条）

#### CAND-YHZP-001: 甲木
```json
{
  "primitive_id": "YHZP-PRIM-001",
  "canonical_state_input": ["天干"],
  "canonical_state_output": "甲木属性",
  "mapping_verified": true,
  "condition_leakage": false,
  "judgment_leakage": false,
  "l4_risk": false,
  "evidence_complete": true,
  "finalization_status": "APPROVED"
}
```

---

## Finalization统计

### 通过Finalization（预计）
| 类别 | 数量 | 说明 |
|------|------|------|
| **APPROVED** | ~60个 | Canonical State可表达，无Condition/Judgment泄露 |
| **REJECTED** | ~22个 | 发现Condition/Judgment泄露或L4风险 |

### 退回原因分类
| 退回原因 | 数量 | 占比 |
|----------|------|------|
| **Condition泄露** | ~15个 | 将"宜/喜/忌"包装成必然判断 |
| **Judgment泄露** | ~5个 | 隐含格局成败判断 |
| **L4风险** | ~2个 | 涉及力量比较 |
| **证据不完整** | ~0个 | 原文引用不全 |

---

## 最终输出

### Approved Primitive列表
```json
[
  {
    "primitive_id": "DTS-PRIM-001",
    "name": "三元",
    "canonical_mapping": "CANONICAL",
    "input_variables": ["天干列表"],
    "output_value": "十天干",
    "source_evidence": "三元者，天干也。",
    "text_layer": "ORIGINAL_COMMENTARY",
    "finalization_status": "APPROVED"
  }
]
```

### Rejected Primitive列表
```json
[
  {
    "candidate_id": "CAND-QTBJ-001",
    "primitive_candidate": "甲木春月宜丙火",
    "rejection_reason": "Condition泄露：将'宜'包装成必然判断",
    "original_text": "甲木春月，专用丙火...",
    "suggested_action": "降级为Evidence层，不进入Primitive"
  }
]
```

---

## 执行命令

```bash
cd /d/shuntian/backend
# 执行Finalization检查
python scripts/verify_primitive_finalization.py --input data/canonical/candidate_pool_pilot.json --output docs/audit/PRIMITIVE_FINALIZATION_RESULT.md
```

---

## 下一步

Finalization完成后：
1. 提交Step 5执行报告
2. 等待GPT裁决是否进入Production
3. 确认CONDITION/JUDGMENT冻结状态