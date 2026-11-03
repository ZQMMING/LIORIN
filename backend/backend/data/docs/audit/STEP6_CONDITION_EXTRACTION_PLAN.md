# Step 6 Condition Extraction Plan - 严格限制版

**时间**: 2026-08-31  
**阶段**: Step 6准备  
**依据**: GPT裁决 e93f74d  
**状态**: 🟡 PENDING（等待Registry稳定后启动）

---

## 核心原则（GPT裁决明确）

### 1. Primitive ≠ Condition
```
Primitive: 天干有阴阳属性（事实描述）
Condition: 若天干为阳 + 月令为春 → 用丙火（条件判断）

禁止从Primitive自动推导Condition
```

### 2. 必须经过Registry验证
```
❌ 35 Approved Primitive → Condition Engine
✅ 35 Approved Primitive → Registry → Canonical State Mapping → Schema Validation → Condition Extraction
```

### 3. "辨规律"比"辨事实"更严格
```
Primitive层: 原典说了什么事实？
Condition层: 原典在什么条件下说这个事实成立？

Condition层需要更多证据支撑
```

---

## 提取规范

### 允许的Condition类型
1. **定义性Condition**
   - 原典明确定义的条件
   - 例如："若A且B且C，则D"
   
2. **分类性Condition**
   - 原典明确的分类标准
   - 例如："属于X类的特征为Y"

### 禁止的Condition类型
1. **工程推断Condition**
   - 从多个Primitive组合推导
   - 例如："若天干为阳 + 月令为春 → 用丙火"
   
2. **建议性Condition**
   - 原典说"宜/喜/忌"，不是"必"
   - 例如："甲木春月宜丙火" ≠ "若甲木春月→必用丙火"
   
3. **格局成败Condition**
   - 涉及成格/破格判断
   - 涉及L4力量比较
   
4. **任注Condition**
   - 来自任铁樵注释的条件
   - 不是原典明确授权

---

## 提取流程

### Phase 1: Registry验证（当前）
- [ ] 35个Primitive全部注册为ACTIVE
- [ ] Provenance链路完整
- [ ] Schema校验通过

### Phase 2: Canonical State Mapping验证
对每个Primitive验证：
- [ ] 输入变量是否明确？
- [ ] 输出结果是否明确？
- [ ] 关系是否确定（非建议性）？

### Phase 3: Condition Extraction（待启动）
**只允许提取：**
- 原典明确定义的Condition
- 原典明确分类的Condition

**禁止提取：**
- 工程推断的Condition
- 建议性Condition（"宜/喜/忌"）
- 格局成败Condition
- 任注Condition

### Phase 4: Red-Team审查
- [ ] 检查是否把描述变成判断
- [ ] 检查是否隐含Condition
- [ ] 检查是否触碰L4
- [ ] 检查是否使用任注条件

### Phase 5: Claude独立审计
- [ ] 验证原典是否真正授权这个Condition
- [ ] 验证Condition是否忠实于原典
- [ ] 验证无工程推断

### Phase 6: GPT裁决
- [ ] 最终裁决哪些Condition进入Production

---

## 提取示例

### ✅ 允许提取
```
Primitive: 天干阴阳属性（DTS-PRIM-004）
Condition: 若天干属于"阳干"列表 → 阴阳属性 = 阳

理由: 原典明确定义"阳干者，甲丙戊庚壬也"
```

### ❌ 禁止提取
```
Primitive: 天干阴阳属性（DTS-PRIM-004）
Condition: 若天干为阳 + 月令为春 → 用丙火

理由: 这是工程推断，原典没说"必须用丙火"
```

---

## 时间线

### 当前（Step 5完成）
- ✅ 35个Primitive注册
- ⏳ Registry验证中

### 下一步（Step 6准备）
- ⏳ Canonical State Mapping验证
- ⏳ Schema/Provenance Validation

### 未来（Step 6执行）
- 🔴 Condition Extraction（待Registry稳定后）
- 🔴 Red-Team审查
- 🔴 Claude审计
- 🔴 GPT裁决

---

## 关键约束

### 1. 禁止跳过Registry
```
❌ Primitive → Condition
✅ Primitive → Registry → Condition
```

### 2. 禁止自动推导
```
❌ 因为Primitive A和B存在 → 推导Condition C
✅ 只有原典明确说出"A + B → C"才能提取Condition C
```

### 3. 禁止扩大语义
```
❌ 原典说"宜" → 包装成"必"
✅ 原典说"宜" → 保持"宜"，不进入Condition
```

---

## 输出文件

### 1. Registry验证报告
```
docs/audit/REGISTRY_VALIDATION_REPORT.md
```

### 2. Canonical State Mapping验证
```
docs/audit/CANONICAL_STATE_MAPPING_VALIDATION.md
```

### 3. Step 6启动报告
```
docs/audit/STEP6_CONDITION_EXTRACTION_START.md
```

---

## 核心原则重申

> **Primitive → Condition 是"辨规律"的开始**
> 
> 从这里开始比Primitive层更严格
> 
> 因为要回答："原典说的这个事实，在什么条件下成立？"

**当前状态**:
- ✅ 35个Primitive注册完成
- ⏳ Registry验证中
- 🔴 Condition Extraction禁止（等Registry稳定）