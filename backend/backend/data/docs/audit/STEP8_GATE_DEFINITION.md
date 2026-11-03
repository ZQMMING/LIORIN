# Step 8: Judgment Production - 门禁定义

**时间**: 2026-08-31  
**阶段**: Step 8规划  
**依据**: GPT裁决 f20d6ff  
**状态**: 🟢 APPROVED

---

## Step 8目标

将8个已授权的Judgment正式写入Production，形成可执行的断言输出。

---

## 门禁定义

### 门禁1: 授权验证
```
输入: 8个Red-Team APPROVED Judgment
验证项:
• 原典明确授权（ORIGINAL_TEXT）✅
• Condition→Judgment因果链完整 ✅
• 无L4风险（不涉及旺衰判断） ✅
• 无工程推断 ✅
• 无任注混入 ✅
• 无重复条目 ✅
输出: 授权清单（8/8 APPROVED）
```

### 门禁2: Schema合规
```
验证项:
• judgment_id唯一且连续 ✅
• source_book正确 ✅
• original_text与原典一致 ✅
• text_layer = "ORIGINAL_TEXT" ✅
• condition_authority独立验证 ✅
• judgment_authority独立验证 ✅
• provenance可追溯 ✅
输出: Schema合规报告
```

### 门禁3: 生产冻结
```
验证项:
• 不得新增Judgment（除非重新走Pipeline）
• 不得修改已授权Judgment（除非重新走Pipeline）
• 不得从Condition自动推导Judgment
• 不得从Primitive组合推导Judgment
输出: 生产冻结声明
```

---

## 生产授权要求

### 三级权威分离验证
```
Primitive Authority:
• 35个Approved ✅
• 已全部写入primitive_registry.json ✅
• 状态: FROZEN ✅

Condition Authority:
• 9个Authorized ✅
• 已全部写入condition_registry.json ✅
• 状态: AUTHORIZED ✅

Judgment Authority:
• 8个Red-Team APPROVED ✅
• 需写入judgment_registry.json ✅
• 状态: PENDING_PRODUCTION（待Step 8完成）
```

### 禁止行为
```
❌ 从Condition自动推导Judgment
   例: Condition A成立 → 因此Judgment B成立（禁止）

❌ 从Primitive组合推导Judgment
   例: Primitive X + Primitive Y → Judgment Z（禁止）

❌ 使用"宜/忌/建议"替代明确Judgment
   例: "宜用金" → "必主贵"（禁止）

❌ 跨层直接推导
   例: Primitive Authority → Judgment Authority（禁止）

✅ 唯一路径:
   Primitive Authority → Condition Authority → Judgment Authority → GPT裁决
```

---

## 生产输出要求

### 输出1: judgment_registry.json
```json
{
  "judgment_id": "DTS-JUDG-001",
  "source_book": "滴天髓",
  "original_text": "有病方为贵，无伤不是奇。",
  "condition_part": "有病",
  "judgment_part": "方为贵",
  "causal_relationship": "原典明确说'有病→贵'",
  "text_layer": "ORIGINAL_TEXT",
  "primitive_authority": "PENDING",
  "condition_authority": "PENDING",
  "judgment_authority": "APPROVED",
  "redteam_verdict": "APPROVED",
  "claude_audit_verdict": "PENDING",
  "gpt_ruling": "PENDING",
  "provenance": {
    "step7_commit": "f20d6ff",
    "redteam_report": "STEP7_REDTTEAM_REPORT_FIXED.md",
    "claude_audit": "PENDING",
    "gpt_ruling": "PENDING"
  }
}
```

### 输出2: production_governance.json
```json
{
  "step": 8,
  "phase": "Judgment Production",
  "timestamp": "2026-08-31",
  "authorized_judgments": 8,
  "frozen": true,
  "rules": [
    "不得新增Judgment（除非重新走Pipeline）",
    "不得修改已授权Judgment（除非重新走Pipeline）",
    "禁止从Condition自动推导Judgment",
    "禁止从Primitive组合推导Judgment",
    "三级权威必须分别验证"
  ]
}
```

### 输出3: Step 8执行报告
```
Step 8完成报告:
• 生产Judgment数量: 8
• 授权来源: Red-Team APPROVED (8/8)
• 生产状态: FROZEN
• 下一步: Claude独立审计
```

---

## 执行流程

### Phase 1: 定义门禁（当前阶段）
- [x] 门禁1: 授权验证
- [x] 门禁2: Schema合规
- [x] 门禁3: 生产冻结
- [x] 生产授权要求
- [x] 生产输出要求

### Phase 2: OpenCode实施（待启动）
- [ ] 创建judgment_registry.json
- [ ] 写入8个授权Judgment
- [ ] 创建production_governance.json
- [ ] 验证Schema合规

### Phase 3: Claude独立审计（待启动）
- [ ] 审计原始授权是否有效
- [ ] 审计生产输出是否符合门禁
- [ ] 审计无跨层推导
- [ ] 审计无L4风险回流

### Phase 4: GPT最终裁决（待启动）
- [ ] 裁决哪些Judgment进入Production
- [ ] 确认生产冻结
- [ ] 输出Final Ruling

---

## 核心原则

> **不因为Step 7通过就放松要求**
> 
> **Step 8与Step 7遵循同一治理原则：**
> - 先定义门禁
> - OpenCode实施
> - Claude独立审计
> - GPT裁决

> **原典Evidence和Judgment授权要求保持不变**
> 
> **生产冻结 = 不再修改，除非重新走Pipeline**

---

## 等待执行

**Step 8门禁已定义**
**下一步**: 启动Phase 2 OpenCode实施（根据用户指示）