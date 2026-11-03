# V1.3 A3.6.4 Sample Freeze

**日期**: 2026-08-22
**状态**: ✅ FROZEN
**版本**: A3.6.4-v1

---

## 一、样本来源

```text
来源: Pilot BLIND (85 个有效事件)
排除: Golden Dataset (已用于开发)
排除: Historical (O2 记录，非 O1 Oracles)
样本数: 40 (分层抽样)
```

---

## 二、分层抽样

### 2.1 分层标准

| 维度 | 分层 | 目标数量 |
|------|------|---------|
| **Event Type** | CAREER / EDUCATION / FAMILY / LIFE_EVENT | 各 8-10 |
| **Evidence Level** | A / B / C | 各 10-15 |
| **Temporal Precision** | EXACT_YEAR / YEAR_RANGE | 各 20 |
| **Output Quality** | 高 / 中 / 低 | 各 10-13 |
| **NOT_EVALUABLE** | 包含缺失维度 | 5-10 |

### 2.2 抽样流程

```text
Step 1: 从 Pilot BLIND 中筛选有效事件
Step 2: 按分层标准分组
Step 3: 从每组随机抽取
Step 4: 合并为 40 个样本
Step 5: 匿名化
Step 6: 随机排序
Step 7: 冻结
```

---

## 三、冻结协议

### 3.1 冻结后禁止

```text
❌ 添加新样本
❌ 删除已有样本
❌ 修改样本内容
❌ 根据评分结果调整
❌ 根据 A3.2 结果挑选
```

### 3.2 冻结样本格式

```json
{
  "metadata": {
    "version": "A3.6.4-Sample-Freeze-v1",
    "created_at": "2026-08-22T12:00:00Z",
    "total_samples": 40,
    "source": "Pilot BLIND",
    "frozen": true,
    "frozen_by": "Hermes"
  },
  "samples": [
    {
      "sample_id": "SAMPLE_001",
      "birth_info": {
        "year": 1982,
        "month": 9,
        "day": 27,
        "hour": "申",
        "gender": "male"
      },
      "system_output": {
        "state": "卦象状态描述（来自系统输出）",
        "opportunity": "机会识别（来自系统输出）",
        "risk": "风险识别（来自系统输出）",
        "remediation": "化解建议（来自系统输出）",
        "action": "行动建议（来自系统输出）",
        "source_references": ["周易·卦名", "说卦传"]
      }
    }
  ]
}
```

---

## 四、当前状态

```text
Sample Freeze:
  ├── 样本数量: 40
  ├── 来源: Pilot BLIND
  ├── 状态: FROZEN
  └── 文件: dataset/accuracy/expert_pilot/frozen_sample.json
```

---

## 五、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│                A3.6.4 SAMPLE FREEZE                            │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ FROZEN                                           │
│                                                              │
│  Sample: 40 cases from Pilot BLIND                           │
│  Stratification: Event Type / Evidence / Temporal / Quality  │
│                                                              │
│  Frozen:                                                     │
│    ✅ 样本冻结后不得修改                                     │
│    ✅ 防止 post-hoc sample selection                         │
│    ✅ 防止根据 A3.2 结果挑选                                  │
│                                                              │
│  Next: A3.6.5 Rating Form                                    │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.6.4-v1