# V1.3 A3.5.4 Sample Protocol

**日期**: 2026-08-22
**状态**: ✅ FROZEN
**版本**: A3.5.4-v1

---

## 一、Expert Validation Pilot

### 1.1 样本规模

```text
目标: 30-50 cases
原因:
  ├── 足够计算 Inter-Rater Agreement
  ├── 不会过度消耗专家时间
  └── 可覆盖主要维度
```

### 1.2 分层抽样

| 维度 | 分层 | 目标数量 |
|------|------|---------|
| **Event Type** | Career / Education / Family / Life Event | 各 5-8 |
| **Evidence Level** | A / B / C | 各 10-15 |
| **Temporal Precision** | Yearly / Monthly / Daily | 各 10 |
| **Output Quality** | High / Medium / Low | 各 10 |
| **NOT_EVALUABLE** | 包含缺失维度 | 5-10 |

### 1.3 必须包含

```text
✅ 正例: 高质量输出 (预期 2 分)
✅ 中等例: 合格输出 (预期 1 分)
✅ 负例: 不合格输出 (预期 0 分)
✅ 模糊例: NOT_EVALUABLE (测试标记能力)
✅ 边界例: 争议性输出 (测试一致性)
```

### 1.4 禁止行为

```text
❌ 只挑容易解释的案例
❌ 只挑系统表现好的案例
❌ 根据评分结果调整样本
❌ 事后添加/删除样本
```

---

## 二、样本来源

### 2.1 可用来源

| 来源 | 数量 | 说明 |
|------|------|------|
| Pilot BLIND | 85 | 已验证出生信息 |
| Historical | 270 | O2 历史记录 |
| Golden | 518 | 已用于开发 |

### 2.2 推荐来源

```text
Primary: Pilot BLIND (85 cases)
  ├── 已验证出生信息
  ├── 已验证事件方向
  └── 独立于 Golden (未用于开发)

Secondary: Historical (部分)
  ├── 选择有完整出生信息的
  └── 避免与 Pilot 重叠
```

### 2.3 禁止来源

```text
❌ Golden Dataset (已用于开发，有污染风险)
❌ 系统开发者自己选择的案例
❌ 根据 A3.2 结果挑选的"有趣"案例
```

---

## 三、样本选择流程

### 3.1 流程

```text
Step 1: 定义分层标准
  └── 见 1.2 分层抽样

Step 2: 随机抽样
  ├── 从 Pilot BLIND 随机抽取
  └── 确保各层覆盖

Step 3: 质量检查
  ├── 检查出生信息完整性
  ├── 检查系统输出完整性
  └── 去除无效样本

Step 4: 匿名化
  ├── 去除个人标识
  ├── 随机编号
  └── 见 A3.5.3 匿名化协议

Step 5: 冻结样本
  ├── 生成样本清单
  ├── Git commit 冻结
  └── 禁止后续修改
```

### 3.2 冻结协议

```text
样本冻结后:
  ✅ 不得添加新样本
  ✅ 不得删除已有样本
  ✅ 不得修改样本内容
  ✅ 不得根据评分结果调整
  
原因: 防止 post-hoc sample selection
```

---

## 四、样本记录格式

### 4.1 样本清单

```json
{
  "metadata": {
    "version": "A3.5.4-Sample-v1",
    "created_at": "2026-08-22T12:00:00Z",
    "total_samples": 40,
    "source": "Pilot BLIND",
    "frozen": true
  },
  "samples": [
    {
      "sample_id": "SAMPLE_001",
      "original_case_id": "PB-0001",
      "birth_info": {
        "year": 1982,
        "month": 9,
        "day": 27,
        "hour": "申",
        "gender": "male"
      },
      "stratification": {
        "event_type": "Career",
        "evidence_level": "A",
        "temporal_precision": "Yearly",
        "expected_quality": "Medium"
      },
      "system_output": {
        "state": "天火同人卦...",
        "opportunity": "...",
        "risk": "...",
        "remediation": "...",
        "action": "...",
        "source_references": ["周易·天火同人"]
      }
    }
  ]
}
```

---

## 五、NOT_EVALUABLE 样本

### 5.1 必须包含

```text
目标: 5-10 个 NOT_EVALUABLE 样本

目的:
  ├── 测试 Rater 标记能力
  ├── 验证 Rubric 完整性
  └── 确保 NOT_EVALUABLE 与 FAIL 分离
```

### 5.2 示例

```text
样本 A: 系统输出 "需结合具体领域分析"
  → STATE: NOT_EVALUABLE (INSUFFICIENT_EVIDENCE)

样本 B: 系统未输出 ACTION
  → ACTION: NOT_EVALUABLE (MISSING)

样本 C: 系统输出 "可能有机会也可能有风险"
  → OPPORTUNITY: NOT_EVALUABLE (AMBIGUOUS)
```

---

## 六、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│                 A3.5.4 SAMPLE PROTOCOL                         │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ FROZEN                                           │
│                                                              │
│  Sample Size: 30-50 cases                                    │
│                                                              │
│  Stratification:                                             │
│    ✅ Event Type (Career/Education/Family/Life Event)        │
│    ✅ Evidence Level (A/B/C)                                 │
│    ✅ Temporal Precision (Yearly/Monthly/Daily)              │
│    ✅ Output Quality (High/Medium/Low)                       │
│    ✅ NOT_EVALUABLE (5-10 cases)                             │
│                                                              │
│  Source:                                                     │
│    ✅ Pilot BLIND (primary)                                  │
│    ❌ Golden Dataset (forbidden)                             │
│                                                              │
│  Frozen:                                                     │
│    ✅ 样本冻结后不得修改                                     │
│    ✅ 防止 post-hoc sample selection                         │
│                                                              │
│  Next: A3.5.5 Inter-Rater Protocol                           │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.5.4-v1
