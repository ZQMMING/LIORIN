# V1.3 A2.2 — Event Schema & Normalization

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档定义事件标准化模型和 G1 本体映射规则。
禁止修改任何代码或数据集。

---

## 一、PERSON 模型定义

```yaml
person_schema:
  # Required Fields
  person_id: "str"                    # 唯一标识符
  name: "str"                         # 人物姓名 (原始语言)
  name_aliases: ["str"]               # 别名/字号
  birth_date: "YYYY-MM-DD"            # 出生日期 (精确度需声明)
  birth_time: "HH:MM" or null         # 出生时间 (如已知)
  gender: "male" | "female"           # 性别
  death_date: "YYYY-MM-DD" or null    # 逝世日期
  
  # Source Fields
  birth_source: "str"                 # 出生信息来源
  death_source: "str" or null         # 逝世信息来源
  evidence_grade: "A" | "B" | "C" | "D" | "X"
  
  # Event References
  events: [event_record]              # 关联事件列表
  
  # Metadata
  created_at: "ISO8601"               # 记录创建时间
  last_verified: "ISO8601" or null    # 最后验证时间
  verified_by: "str" or null          # 验证者
```

---

## 二、EVENT_RECORD 模型定义

```yaml
event_record:
  # Identity
  event_id: "str"                     # 唯一事件标识符
  person_id: "str"                    # 关联人物
  
  # Event Information
  event_type: "str"                   # 事件类型 (见 G1 17类型)
  domain: "str"                       # 领域 (见 G1 4域)
  event_date: "YYYY-MM-DD" or null    # 事件发生日期
  event_date_precision: "YEAR" | "MONTH" | "DAY"  # 日期精度
  event_direction: "POSITIVE" | "NEGATIVE" | "NEUTRAL" | "UNKNOWN"
  severity: int (1-5)                 # 严重程度
  
  # Description
  description: "str"                  # 事件描述 (原始语言)
  description_en: "str" or null       # 英文翻译
  
  # Source & Evidence
  source_url: "str" or null           # 来源 URL
  source_reference: "str" or null     # 文献引用
  source_publication_date: "YYYY-MM-DD" or null  # 来源发布时间
  evidence_grade: "A" | "B" | "C" | "D" | "X"
  is_primary_source: bool             # 是否一手来源
  
  # Leakage Classification
  leakage_class: "CLEAN" | "REVIEWED" | "CONTAMINATED"
  leakage_reason: "str" or null       # 泄漏原因 (如适用)
  prediction_cutoff: "YYYY-MM-DD"     # 预测截止时间 (用于 PRE_EVENT 判定)
  
  # Ontology Mapping
  mapped_to_event_type: "str"         # 映射到 G1 Event Type
  mapped_to_domain: "str"             # 映射到 G1 Domain
  mapping_confidence: float (0-1)     # 映射置信度
  single_parent_verified: bool        # 是否验证单一父域
  
  # Status
  status: "DRAFT" | "REVIEWED" | "APPROVED" | "REJECTED"
  reviewed_at: "ISO8601" or null
  reviewed_by: "str" or null
```

---

## 三、G1 4 Domains + 17 Event Types 映射规则

### 3.1 Domain 定义

```text
Domain ENUM:
├── EDUCATION: 学习、考试、学业相关
├── CAREER: 职业、工作、事业相关
├── FAMILY: 家庭、婚姻、生育相关
└── LIFE_EVENT: 其他人生重大事件
```

### 3.2 Event Type 定义

```text
Event Type ENUM (17 types):
├── EDUCATION:
│   ├── EDUCATION_START (入学)
│   ├── EDUCATION_GRADUATE (毕业)
│   └── EDUCATION_ACHIEVE (学业成就)
│
├── CAREER:
│   ├── CAREER_START (入职)
│   ├── CAREER_CHANGE (转职)
│   ├── CAREER_PROMOTE (晋升)
│   ├── CAREER_DEMOTE (降职)
│   ├── CAREER_RETIRE (退休)
│   └── CAREER_END (职业终结)
│
├── FAMILY:
│   ├── CHILD_BIRTH (出生)
│   ├── MARRIAGE (结婚)
│   ├── DIVORCE (离婚)
│   ├── DEATH (逝世)
│   └── FAMILY_REUNION (团聚)
│
└── LIFE_EVENT:
    ├── HEALTH_CRISIS (健康危机)
    ├── WEALTH_CHANGE (财富变化)
    ├── MIGRATION (迁移)
    ├── LEGAL_ISSUE (法律事件)
    ├── SOCIAL_ACHIEVE (社会成就)
    └── TRAUMA (重大创伤)
```

### 3.3 历史事件 → G1 映射规则

```text
MAPPING RULES:
├── 单一父域原则 (Single-Parent Ontology):
│   └── 每个事件只属于一个 Domain，即使可从多个角度解释
│
├── 优先级规则 (当事件可归入多个 Domain 时):
│   1. EDUCATION > 学术成就
│   2. CAREER > 职业发展
│   3. FAMILY > 家庭生活
│   4. LIFE_EVENT > 其他
│
├── 明确映射表:
│   ├── 出生/逝世 → FAMILY.CHILD_BIRTH / FAMILY.DEATH
│   ├── 入学/毕业 → EDUCATION.*
│   ├── 入职/晋升/退休 → CAREER.*
│   ├── 结婚/离婚 → FAMILY.MARRIAGE / FAMILY.DIVORCE
│   ├── 迁居 → LIFE_EVENT.MIGRATION
│   ├── 重病/受伤 → LIFE_EVENT.HEALTH_CRISIS
│   └── 获奖/荣誉 → 按性质归入相应 Domain
│
└── 禁止映射:
    └── 禁止同一事件复制进多个 Domain
```

---

## 四、事件类型判断矩阵

### 4.1 历史人物事件示例映射

| 历史事件 | 原始描述 | 映射 Domain | 映射 Event Type | 理由 |
|---------|---------|------------|----------------|------|
| 纪晓岚出生 | 乾隆甲申年八月初三 | FAMILY | CHILD_BIRTH | 明确出生 |
| 纪晓岚进士及第 | 乾隆丙戌科进士 | EDUCATION | EDUCATION_GRADUATE | 科举=教育成就 |
| 纪晓岚官至协办大学士 | 历任多个官职，最高协办大学士 | CAREER | CAREER_PROMOTE | 晋升 |
| 纪晓岚编纂《四库全书》 | 任总纂官 | CAREER | CAREER_START | 职业任务 |
| 纪晓岚逝世 | 乾隆五十年六月十九日 | FAMILY | DEATH | 明确逝世 |
| 王安石变法 | 熙宁变法 | CAREER | CAREER_CHANGE | 政治变革 |
| 苏轼贬谪黄州 | 元丰三年谪黄州 | CAREER | CAREER_DEMOTE | 降职 |
| 司马光逝世 | 元祐元年 | FAMILY | DEATH | 明确逝世 |

### 4.2 模糊事件处理

```text
AMBIGUOUS EVENT HANDLING:
├── 无法确定时间 → event_date = null, event_date_precision = "UNKNOWN"
├── 无法确定方向 → event_direction = "UNKNOWN"
├── 无法确定类型 → 保持 DRAFT 状态，等待人工审核
├── 多来源冲突 → 标注冲突来源，取交叉验证后的版本
└── 无法判定 Domain → 归入 LIFE_EVENT (fallback)
```

---

## 五、Event Schema 验证规则

### 5.1 必填字段验证

```text
REQUIRED FIELD CHECKS:
├── person_id: 必须非空
├── event_type: 必须属于 17 种类型之一
├── domain: 必须属于 4 个域之一
├── evidence_grade: 必须为 A/B/C/D/X 之一
├── leakage_class: 必须为 CLEAN/REVIEWED/CONTAMINATED 之一
├── status: 必须为 DRAFT/REVIEWED/APPROVED/REJECTED 之一
└── single_parent_verified: 必须为 true/false
```

### 5.2 完整性验证

```text
COMPLETENESS CHECKS:
├── 每个 APPROVED 事件必须有:
│   ├── evidence_grade (A/B)
│   ├── source_reference
│   ├── event_date 或 event_date_precision = "UNKNOWN"
│   └── single_parent_verified = true
│
├── 每个 DRAFT 事件必须有:
│   ├── minimum required fields
│   └── review_deadline (optional)
│
└── 禁止:
    ├── 未经审核的事件进入 BLIND 数据集
    ├── 标记为 CONTAMINATED 的事件进入任何评估
    └── 伪造精确日期
```

---

## 六、Schema 文档结构

```text
docs/accuracy/
├── V13_A22_EVENT_SCHEMA.md               (本文件)
├── V13_A22_MAPPING_RULES.md              (详细映射规则)
└── V13_A22_EVENT_REGISTRY.md             (已审核事件列表)
```

---

**报告结束**
**下一步**: A2.3 Temporal Alignment
