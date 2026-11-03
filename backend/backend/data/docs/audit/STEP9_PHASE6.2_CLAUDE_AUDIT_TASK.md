# Step 9 Phase 6.2: Claude独立代码审计任务

**时间**: 2026-08-31  
**阶段**: Phase 6.2 Claude独立代码审计  
**依据**: GPT裁决 11b0d92  
**状态**: 🟢 APPROVED TO START

---

## 审计范围

### 输入文件
- `src/tongshu/assertion/judgment_production.py` (338行)
- `tests/test_judgment_production.py` (220行)
- `data/canonical/judgment_registry_v2.json` (8个Judgment)

### 输出文件
- `docs/audit/CLAUDE_CODE_AUDIT_STEP9_RESULT.md`
- `data/canonical/claude_code_audit_step9_result.json`

---

## 审计维度

### 维度1: 授权验证
```
验证项:
• 仅实现4条APPROVED Judgment？
• 是否引用了HOLD或REJECTED的Judgment？
• 是否引入了未经授权的五经断言？
• 测试是否仅覆盖4个APPROVED Judgment？
```

### 维度2: Legacy回流检查
```
验证项:
• 是否调用evaluate_strength生产路径？
• 是否引用wang_score阈值？
• 是否使用Legacy Strength逻辑？
• 是否存在旧版代码路径？
```

### 维度3: L4风险检查
```
验证项:
• 是否涉及旺衰判定？
• 是否使用数值阈值？
• 是否绕过三层权威验证？
• 是否从Primitive/Condition自动推导Judgment？
```

### 维度4: Schema合规性
```
验证项:
• judgment_id是否唯一且连续？
• source_book是否正确？
• original_text是否与原典一致？
• text_layer是否为ORIGINAL_TEXT？
• production_status是否符合GPT裁决？
```

### 维度5: 测试完整性
```
验证项:
• 是否覆盖所有4个APPROVED Judgment？
• 是否验证禁止的Judgment被正确拦截？
• 是否验证无Legacy回流？
• 是否验证无L4风险？
```

---

## 审计标准

### APPROVED标准
```
必须同时满足:
✅ 仅实现4条APPROVED Judgment
✅ 无Legacy回流（无evaluate_strength调用）
✅ 无L4风险（无旺衰判定）
✅ 测试全部通过
✅ Schema合规
```

### REJECTED标准
```
满足任一即拒绝:
❌ 实现了HOLD或REJECTED的Judgment
❌ 存在Legacy回流
❌ 存在L4风险
❌ 测试失败
❌ Schema不合规
```

---

## 执行流程

### Phase 6.2.1: 审计准备
- [x] 加载judgment_production.py
- [x] 加载test_judgment_production.py
- [x] 加载judgment_registry_v2.json
- [x] 确认审计范围

### Phase 6.2.2: Claude独立审计
- [ ] 逐条审计生产代码
- [ ] 验证授权范围
- [ ] 检查Legacy回流
- [ ] 检查L4风险
- [ ] 验证Schema合规
- [ ] 验证测试完整性
- [ ] 输出审计结果

### Phase 6.2.3: 审计报告
- [ ] 创建CLAUDE_CODE_AUDIT_STEP9_RESULT.md
- [ ] 创建claude_code_audit_step9_result.json
- [ ] 统计APPROVED/REJECTED数量

---

## 核心原则

> **Claude独立代码审计 ≠ Hermes自审**
> 
> **必须使用真实Claude CLI进行独立审计**
> 
> **审计标准保持不变，不因Phase 6.1通过而放松**
> 
> **发现Legacy或L4风险立即拒绝**