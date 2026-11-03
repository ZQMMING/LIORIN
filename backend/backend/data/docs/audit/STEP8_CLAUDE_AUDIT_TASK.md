# Step 8 Phase 3: Claude独立审计任务

**时间**: 2026-08-31  
**阶段**: Phase 3 Claude独立审计  
**依据**: GPT裁决 f20d6ff + STEP8_GATE_DEFINITION.md  
**状态**: 🟢 APPROVED TO START

---

## 审计范围

### 输入
- **judgment_registry_v1.json**: 8个PENDING_PRODUCTION Judgment
- **STEP7_REDTTEAM_REPORT_FIXED.md**: Red-Team审查报告
- **STEP8_GATE_DEFINITION.md**: 门禁定义

### 输出
- Claude独立审计结果
- 审计 verdict（APPROVED/REJECTED/PENDING）
- 审计理由
- 风险提示

---

## 审计维度

### 维度1: 原典授权有效性
```
验证项:
• original_text是否与原典一致？
• text_layer是否为ORIGINAL_TEXT？
• 是否有原典明确授权"条件→结果"？
• 是否只是建议性描述（宜/忌）？
```

### 维度2: Condition→Judgment因果链
```
验证项:
• 因果链是否完整？
• 是否是原典直接说出的"若X则Y"？
• 还是工程人员推导的"如果X成立，应该Y"？
• 是否存在"因此""所以"等隐含推导？
```

### 维度3: L4风险检查
```
验证项:
• 是否涉及"旺/弱/强/弱"力量判定？
• 是否重新引入Strength Engine逻辑？
• 是否用数值阈值替代原典判断？
• 是否存在L4污染风险？
```

### 维度4: 三级权威分离
```
验证项:
• Primitive Authority是否独立验证？
• Condition Authority是否独立验证？
• Judgment Authority是否独立验证？
• 是否存在跨层直接推导？
```

### 维度5: 重复与混淆
```
验证项:
• 是否存在重复条目？
• 是否混入任注或后人评注？
• 是否与其他Registry冲突？
```

---

## 审计清单

### 滴天髓（4个）
| # | Judgment ID | 原典原文 | 审计要点 |
|---|-------------|----------|----------|
| 1 | DTS-JUDG-001 | "有病方为贵，无伤不是奇" | ✅ 原典明确授权 |
| 2 | DTS-JUDG-002 | "格中如去病，财禄两相随" | ✅ 原典明确授权 |
| 3 | DTS-JUDG-003 | "真神得用平生贵，用假终为碌碌人" | ⚠️ 需验证"真神"定义 |
| 4 | DTS-JUDG-004 | "真神得用平生贵，用假终为碌碌人" | ⚠️ 需验证"用假"定义 |

### 子平真诠（4个）
| # | Judgment ID | 原典原文 | 审计要点 |
|---|-------------|----------|----------|
| 5 | ZPZQ-JUDG-001 | "配合得宜，皆为贵格" | ✅ 原典明确授权 |
| 6 | ZPZQ-JUDG-002 | "合伤存官，遂成贵格" | ✅ 原典明确授权 |
| 7 | ZPZQ-JUDG-003 | "相神无破，贵格已成" | ✅ 原典明确授权 |
| 8 | ZPZQ-JUDG-004 | "相神有伤，立败其格" | ✅ 原典明确授权 |

---

## 关键审计问题

### 问题1: DTS-JUDG-003/004 "真神得用"的定义
```
审计要点:
• "真神"在原典中是否有明确定义？
• "得用"在原典中是否有明确标准？
• 是否存在工程人员自行定义的风险？
• 是否需要回查《滴天髓》原文确认？
```

### 问题2: ZPZQ-JUDG-001 "配合得宜"的定义
```
审计要点:
• "配合得宜"在原典中是否有明确定义？
• 是否有具体的判断标准？
• 还是只是原则性描述？
```

### 问题3: 三级权威是否真正分离
```
审计要点:
• Primitive Registry已授权35条，是否影响Judgment判断？
• Condition Registry已授权9条，是否影响Judgment判断？
• Judgment Authority是否真正独立验证？
```

---

## 审计标准

### APPROVED标准
```
必须同时满足:
✅ 原典明确授权"条件→结果"结构
✅ 因果链完整，无隐含推导
✅ 无L4风险
✅ 三级权威独立验证
✅ 无重复条目
```

### REJECTED标准
```
满足任一即拒绝:
❌ 原典无明确授权
❌ 因果链不完整
❌ 涉及L4风险
❌ 存在跨层推导
❌ 与已有Registry冲突
❌ 任注混入原文
```

### PENDING标准
```
满足任一即暂停:
⚠️ 需要回查原文确认
⚠️ 定义不够明确
⚠️ 需要更多上下文
```

---

## 执行流程

### Phase 3.1: 审计准备
- [x] 加载judgment_registry_v1.json
- [x] 加载STEP7_REDTTEAM_REPORT_FIXED.md
- [x] 确认审计范围

### Phase 3.2: Claude独立审计
- [ ] 逐条审计8个Judgment
- [ ] 验证原典授权有效性
- [ ] 检查L4风险
- [ ] 确认三级权威分离
- [ ] 输出审计结果

### Phase 3.3: 审计报告
- [ ] 创建CLAUDE_AUDIT_STEP8_RESULT.md
- [ ] 创建claude_audit_step8_result.json
- [ ] 统计APPROVED/REJECTED/PENDING数量

---

## 核心原则

> **Claude独立审计 ≠ Hermes自审**
> 
> **必须使用真实Claude CLI进行独立审计**
> 
> **审计标准保持不变，不因Step 7通过而放松**

---

## 等待执行

**Step 8 Phase 3 Claude独立审计已准备就绪**
**下一步: 启动Claude独立审计（需要用户指示）**