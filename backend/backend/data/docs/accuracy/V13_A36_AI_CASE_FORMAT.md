# V1.3 A3.6-A AI Case Format

**日期**: 2026-08-22
**状态**: ✅ FROZEN
**版本**: A3.6-A-CaseFormat-v1

---

## 一、Case 文件结构

### 1.1 文件名

```text
CASE_0001_BLIND.md
CASE_0002_BLIND.md
...
CASE_0040_BLIND.md
```

### 1.2 文件内容

```markdown
# CASE_0001 — Blind Evaluation

## 人物基本信息

- **人物ID**: PB-0001
- **性别**: 男
- **出生年**: 1982
- **出生月**: 9
- **出生日**: 27
- **出生时**: 申时 (15:00-17:00)

## 系统输入

```json
{
  "birth_info": {
    "year": 1982,
    "month": 9,
    "day": 27,
    "hour": "申",
    "gender": "male"
  },
  "target_date": "2015-06-15",
  "temporal_context": {
    "yearly": "乙未年",
    "monthly": "壬午月",
    "daily": "丙戌日"
  }
}
```

## 系统原始输出

### STATE

天火同人卦，体用关系：用克体（凶）

### OPPORTUNITY

同人卦象征与人合作，利于团队协作

### RISK

用克体表示外部压力，需防小人

### REMEDIATION

以诚待人，保持谦逊

### ACTION

本周宜主动沟通，避免独断

### SOURCE_REFERENCES

- 周易·天火同人
- 说卦传

---

## 评分任务

请按照以下 Rubric 对系统输出进行评分：

### 评分维度 (0-2 分)

| Dimension | 2分 (优秀) | 1分 (合格) | 0分 (不合格) |
|-----------|-----------|-----------|-------------|
| STATE | 准确引用卦名、卦象、体用关系 | 基本正确但有遗漏 | 错误或缺失 |
| OPPORTUNITY | 识别具体机会，有经典依据 | 识别但缺乏依据 | 未识别或错误 |
| RISK | 识别具体风险，有经典依据 | 识别但缺乏依据 | 未识别或错误 |
| REMEDIATION | 建议与RISK对应，符合易理 | 建议合理但不具体 | 矛盾或缺失 |
| ACTION | 建议具体可执行 | 建议可操作但关联不强 | 不可操作或矛盾 |
| TEMPORAL | 正确映射时间状态 | 基本正确但有偏差 | 错误或缺失 |
| EVIDENCE | 引用具体经典 | 有引用但不具体 | 无引用或错误 |

### NOT_EVALUABLE

如果某维度无法评估，标记为 NOT_EVALUABLE 并说明原因：
- INSUFFICIENT_EVIDENCE: 系统未提供足够信息
- AMBIGUOUS: 输出模糊无法判断
- NOT_APPLICABLE: 该维度不适用
- MISSING: 维度完全缺失

### 输出格式

```json
{
  "case_id": "CASE_0001",
  "rater": "GPT",
  "timestamp": "2026-08-22T10:00:00Z",
  "scores": {
    "state": {
      "status": "SCORED",
      "score": 2,
      "reason": "准确引用卦名和体用关系",
      "evidence_reference": "周易·天火同人",
      "confidence": "HIGH"
    },
    "opportunity": {
      "status": "SCORED",
      "score": 1,
      "reason": "识别合作机会，符合卦象",
      "evidence_reference": "说卦传",
      "confidence": "MEDIUM"
    },
    "risk": {
      "status": "SCORED",
      "score": 2,
      "reason": "识别外部压力，符合体用关系",
      "evidence_reference": "周易·同人卦辞",
      "confidence": "HIGH"
    },
    "remediation": {
      "status": "SCORED",
      "score": 1,
      "reason": "建议合理但缺乏经典依据",
      "evidence_reference": "",
      "confidence": "MEDIUM"
    },
    "action": {
      "status": "SCORED",
      "score": 2,
      "reason": "具体可操作",
      "evidence_reference": "",
      "confidence": "HIGH"
    },
    "temporal": {
      "status": "SCORED",
      "score": 1,
      "reason": "'本周'映射不够精确",
      "evidence_reference": "",
      "confidence": "MEDIUM"
    },
    "evidence": {
      "status": "SCORED",
      "score": 1,
      "reason": "有引用但不够具体",
      "evidence_reference": "周易·天火同人",
      "confidence": "MEDIUM"
    }
  },
  "evaluable_dimensions": 7,
  "total_score": 10,
  "normalized_score": 71.4,
  "comments": "整体质量中等偏上，STATE和RISK识别准确，但REMEDIATION缺乏经典依据。"
}
```

---

## 禁止信息

本文件**不包含**：
- ❌ Ground Truth (历史事件结果)
- ❌ 其他 Rater 评分
- ❌ 系统内部计算链
- ❌ 系统 confidence 值

---

**生成者**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.6-A-CaseFormat-v1
