# V1.3 A3.5.1 Expert Oracle Specification

**日期**: 2026-08-22
**状态**: ✅ FROZEN
**版本**: A3.5.1-v1

---

## 一、Expert Oracle 定义

### 1.1 职责

Expert Oracle (O4) 负责评估顺天系统的 **Relational Interpretation** 输出质量。

评估对象：
```text
YiEngine 输出:
├── STATE (卦象状态描述)
├── OPPORTUNITY (机会识别)
├── RISK (风险识别)
├── REMEDIATION (化解建议)
├── ACTION (行动建议)
└── SOURCE_REFERENCES (经典引用)
```

### 1.2 可以评分

| 维度 | 说明 |
|------|------|
| STATE 准确性 | 卦象状态描述是否符合经典规则 |
| OPPORTUNITY 合理性 | 机会识别是否与卦象一致 |
| RISK 合理性 | 风险识别是否与卦象一致 |
| REMEDIATION 一致性 | 化解建议是否与状态匹配 |
| ACTION 可操作性 | 行动建议是否具体可行 |
| TEMPORAL ALIGNMENT | 时间状态是否正确映射 |
| EVIDENCE GROUNDING | 是否引用具体经典来源 |

### 1.3 不可以评分

| 禁止项 | 原因 |
|--------|------|
| 预测准确率 | 系统不是事件预测器 |
| 吉凶判断 | 系统输出结构化解释，不是吉凶标签 |
| 用户满意度 | 需要独立 UX 评估 |
| 商业价值 | 超出技术评估范围 |

---

## 二、Oracle 与系统输出的隔离

### 2.1 隔离原则

```text
系统输出 (YiEngine)
        │
        ▼
   ┌─────────┐
   │  隔离层  │ ← Oracle 不得访问
   └─────────┘
        │
        ▼
Expert Oracle (O4)
        │
        ▼
   评分结果
```

### 2.2 Oracle 不得访问

| 禁止访问 | 原因 |
|----------|------|
| 系统内部计算链 | 避免确认偏误 |
| 系统 confidence 值 | 避免锚定效应 |
| 其他 Rater 评分 | 保证独立性 |
| 最终事件结果 | 避免事后偏差 |
| 系统开发者注释 | 避免设计偏误 |

### 2.3 Oracle 可以访问

| 允许访问 | 说明 |
|----------|------|
| 出生信息 | 输入参数 |
| 系统最终输出 | STATE/OPPORTUNITY/RISK/REMEDIATION/ACTION |
| 经典原文 | 用于验证引用 |
| Rubric 评分标准 | 统一评分尺度 |

---

## 三、Ground Truth / Evidence / Interpretation 边界

### 3.1 三层定义

| 层级 | 定义 | 来源 |
|------|------|------|
| **Ground Truth** | 客观事实 | 历史记录、天文数据 |
| **Evidence** | 经典依据 | 周易、说卦传、注疏 |
| **Interpretation** | 系统解释 | YiEngine 输出 |

### 3.2 Oracle 评估范围

```text
Oracle 评估: Interpretation 层
  ├── 是否正确使用 Evidence
  ├── 是否符合经典规则
  └── 是否逻辑自洽

Oracle 不评估: Ground Truth 层
  └── 事件是否真的发生（这是 Track A 的任务）
```

---

## 四、O4_EXPERT Qualification Criteria

### 4.1 最低资质

| 要求 | 说明 |
|------|------|
| 经典知识 | 熟悉周易、说卦传、至少一家注疏 |
| 术数基础 | 理解八字/河洛/紫微基本概念 |
| 独立判断 | 能够独立评估解释质量 |
| 无利益冲突 | 不是系统开发者、不是项目成员 |

### 4.2 推荐资质

| 要求 | 说明 |
|------|------|
| 学术背景 | 易学、哲学、汉学相关专业 |
| 实践经验 | 5年以上术数实践 |
| 评估经验 | 参与过类似评估项目 |

### 4.3 禁止资格

| 禁止 | 原因 |
|------|------|
| 系统开发者 | 自我认证循环 |
| 项目投资者 | 利益冲突 |
| 系统用户（当前） | 使用偏误 |

---

## 五、禁止使用系统预测结果反推评分标准

### 5.1 禁止行为

```text
❌ 查看系统输出 → 调整 Rubric 使系统得分更高
❌ 查看评分结果 → 修改评分标准使结果更"合理"
❌ 查看事件结果 → 回溯调整解释评分
```

### 5.2 正确流程

```text
1. 冻结 Rubric (本文档)
2. 冻结样本 (A3.5.5)
3. 独立评分 (A3.5.4)
4. 计算一致性 (A3.5.6)
5. 报告结果 (不改标准)
```

---

## 六、Oracle 输出格式

### 6.1 评分记录

```json
{
  "rater_id": "RATER_A",
  "case_id": "CASE_001",
  "timestamp": "2026-08-22T10:00:00Z",
  "scores": {
    "state": 2,
    "opportunity": 1,
    "risk": 2,
    "remediation": 1,
    "action": 2,
    "temporal_alignment": 2,
    "evidence_grounding": 1
  },
  "total": 11,
  "not_evaluable": [],
  "comments": "STATE 准确引用天火同人卦辞，OPPORTUNITY 识别合理但缺乏经典依据..."
}
```

### 6.2 不可评分标记

```json
{
  "not_evaluable": ["opportunity"],
  "reason": "INSUFFICIENT_EVIDENCE: 系统未提供具体机会识别"
}
```

---

## 七、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│           A3.5.1 EXPERT ORACLE SPECIFICATION                  │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ FROZEN                                           │
│                                                              │
│  Key Decisions:                                              │
│    ✅ Oracle 评估 Relational Interpretation                  │
│    ✅ Oracle 不评估 Prediction Accuracy                      │
│    ✅ 严格隔离系统内部信息                                     │
│    ✅ 禁止自我认证                                            │
│    ✅ 禁止反推评分标准                                        │
│                                                              │
│  Qualification:                                              │
│    ✅ 经典知识 + 术数基础 + 独立判断                          │
│    ❌ 系统开发者 / 项目投资者                                 │
│                                                              │
│  Next: A3.5.2 Relational Rubric                              │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.5.1-v1
