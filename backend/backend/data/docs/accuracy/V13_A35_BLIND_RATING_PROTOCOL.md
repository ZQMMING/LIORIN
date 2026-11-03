# V1.3 A3.5.3 Blind Rating Protocol

**日期**: 2026-08-22
**状态**: ✅ FROZEN
**版本**: A3.5.3-v1

---

## 一、Rater 独立性

### 1.1 Rater 配置

```text
Rater A (独立评价者 1)
Rater B (独立评价者 2)
     ↓
独立评分 (互不可见)
     ↓
Inter-Rater Agreement
     ↓
Disagreement Set (差异 ≥ 2 分)
     ↓
Adjudicator (第三方裁决)
```

### 1.2 Rater 不得看到

| 禁止访问 | 原因 |
|----------|------|
| 另一个 Rater 的评分 | 保证独立性 |
| 系统内部计算链 | 避免确认偏误 |
| 系统 confidence 值 | 避免锚定效应 |
| 其他专家评价 | 避免从众效应 |
| 最终事件结果 | 避免事后偏差 |
| 系统开发者注释 | 避免设计偏误 |
| 评分汇总结果 | 避免调整倾向 |

### 1.3 Rater 可以访问

| 允许访问 | 说明 |
|----------|------|
| 出生信息 | 输入参数 |
| 系统最终输出 | STATE/OPPORTUNITY/RISK/REMEDIATION/ACTION |
| 经典原文 | 用于验证引用 |
| Rubric 评分标准 | 统一评分尺度 |
| 评分工具 | 标准化记录 |

---

## 二、盲评流程

### 2.1 流程步骤

```text
Step 1: 样本准备
  ├── 从样本池随机抽取
  ├── 去除个人标识（匿名化）
  └── 随机排序

Step 2: 分发评分
  ├── Rater A 收到样本集 A
  ├── Rater B 收到样本集 B (相同样本，不同顺序)
  └── 两者互不知晓

Step 3: 独立评分
  ├── Rater A 按 Rubric 评分
  ├── Rater B 按 Rubric 评分
  └── 限时：每样本 15-30 分钟

Step 4: 收集结果
  ├── 收集 Rater A 评分
  ├── 收集 Rater B 评分
  └── 不透露对方结果

Step 5: 计算一致性
  ├── Cohen's κ
  ├── Weighted κ
  └── 差异分析

Step 6: 裁决分歧
  ├── 识别差异 ≥ 2 分的样本
  ├── Adjudicator 独立评分
  └── 最终评分 = 多数决定
```

### 2.2 时间控制

| 阶段 | 时间 | 说明 |
|------|------|------|
| 评分准备 | 30 min | 熟悉 Rubric |
| 单样本评分 | 15-30 min | 视复杂度 |
| 总计 (30 样本) | 8-15 hr | 可分多次 |
| 一致性计算 | 1 hr | 自动化 |
| 裁决分歧 | 2-4 hr | Adjudicator |

---

## 三、匿名化协议

### 3.1 去除信息

```text
去除:
  ├── 系统内部 ID
  ├── 开发者注释
  ├── confidence 值
  ├── 计算链细节
  └── 其他 Rater 标识

保留:
  ├── 出生信息 (匿名化)
  ├── 系统最终输出
  ├── 经典引用
  └── 样本编号 (随机)
```

### 3.2 匿名化示例

```text
原始:
  case_id: GOLDEN-001
  developer_note: "纪晓岚案例，用于验证后天卦"
  confidence: 0.85
  internal_state: {...}

匿名化后:
  sample_id: SAMPLE_017
  birth_info: {year: 1724, month: 8, day: 3, hour: 巳, gender: male}
  system_output: {STATE: "...", OPPORTUNITY: "...", ...}
```

---

## 四、评分工具

### 4.1 评分表格式

```json
{
  "rater_id": "RATER_A",
  "sample_id": "SAMPLE_017",
  "timestamp": "2026-08-22T10:30:00Z",
  "scores": {
    "state": {"score": 2, "reason": "准确引用卦名和体用关系"},
    "opportunity": {"score": 1, "reason": "识别机会但缺乏经典依据"},
    "risk": {"score": 2, "reason": "识别风险，符合体用关系"},
    "remediation": {"status": "NOT_EVALUABLE", "reason": "MISSING"},
    "action": {"score": 1, "reason": "建议可操作但与 STATE 关联不强"},
    "temporal_alignment": {"score": 2, "reason": "正确映射流日状态"},
    "evidence_grounding": {"score": 1, "reason": "有引用但不够具体"}
  },
  "total_score": 8,
  "evaluable_dimensions": 6,
  "normalized_score": 66.7,
  "comments": "整体质量中等，STATE 和 RISK 识别准确，但 REMEDIATION 缺失"
}
```

### 4.2 评分约束

```text
✅ 必须为每个维度提供 reason
✅ 必须标记 NOT_EVALUABLE（不强迫给分）
✅ 必须在 30 分钟内完成单样本
❌ 不得查看其他 Rater 评分
❌ 不得查看系统内部信息
❌ 不得修改已提交评分
```

---

## 五、分歧处理

### 5.1 分歧定义

```text
分歧 = |Rater_A_score - Rater_B_score| ≥ 2 (单维度)
或
分歧 = |Rater_A_total - Rater_B_total| ≥ 4 (总分)
```

### 5.2 分歧处理流程

```text
1. 识别分歧样本
2. 去除个人标识后提交 Adjudicator
3. Adjudicator 独立评分
4. 最终评分 = 多数决定 (2/3)
5. 记录分歧原因
```

### 5.3 Adjudicator 资质

| 要求 | 说明 |
|------|------|
| 独立于 Rater A/B | 不得是同一人 |
| 符合 O4 资质 | 见 A3.5.1 |
| 不知晓分歧原因 | 盲评 |

---

## 六、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│              A3.5.3 BLIND RATING PROTOCOL                      │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ FROZEN                                           │
│                                                              │
│  Rater Configuration:                                        │
│    Rater A + Rater B → Independent Rating                    │
│    → Inter-Rater Agreement → Adjudicator                     │
│                                                              │
│  Blind Protocol:                                             │
│    ✅ Rater 互不可见                                          │
│    ✅ 不得访问系统内部信息                                     │
│    ✅ 匿名化样本                                             │
│    ✅ 标准化评分工具                                          │
│                                                              │
│  Disagreement Handling:                                      │
│    ✅ 差异 ≥ 2 分 → Adjudicator                              │
│    ✅ 多数决定 (2/3)                                         │
│                                                              │
│  Next: A3.5.4 Sample Protocol                                │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.5.3-v1
