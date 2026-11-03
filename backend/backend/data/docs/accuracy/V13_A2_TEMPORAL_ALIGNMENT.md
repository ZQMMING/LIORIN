# V1.3 A2.3 — Temporal Alignment

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档定义事件时间对齐标准，确保时间精度声明准确。
禁止修改任何代码或数据集。

---

## 一、时间精度定义

```text
TIME PRECISION LEVELS:
├── EXACT (DAY): 精确到日
│   └── 示例: 1998-07-01 (公历), 乾隆二十五年六月初一 (农历)
│
├── MONTH: 精确到月
│   └── 示例: 1998-07 (公历), 乾隆二十五年六月 (农历)
│
├── YEAR: 精确到年
│   └── 示例: 1998 (公历), 乾隆二十五年 (农历)
│
└── UNKNOWN: 时间未知
    └── 示例: event_date = null, event_date_precision = "UNKNOWN"
```

---

## 二、时间字段定义

```yaml
temporal_field:
  event_date_exact: "YYYY-MM-DD" or null    # 精确日期
  event_date_month: "YYYY-MM" or null       # 月份精度
  event_date_year: "YYYY" or null           # 年份精度
  date_precision: "DAY" | "MONTH" | "YEAR" | "UNKNOWN"
  timezone: "IANA/Timezone" or null         # 时区 (如 Asia/Shanghai)
  calendar_system: "GREGORIAN" | "LUNAR"   # 历法系统
  source_date: "str"                        # 来源中记录的原始日期
  source_calendar: "GREGORIAN" | "LUNAR" | "UNKNOWN"  # 来源历法
  prediction_cutoff: "YYYY-MM-DD" or null   # 预测截止时间
```

---

## 三、时间对齐规则

### 3.1 公历 ↔ 农历转换

```text
CONVERSION RULES:
├── 已知公历日期 → 可转换为农历 (使用 sxtwl)
├── 已知农历日期 → 可转换为公历 (使用 sxtwl)
├── 只有年份 → event_date_year 填充，精确度 = YEAR
└── 无法转换 → 保留原始日期，标注 source_calendar
```

### 3.2 时区处理

```text
TIMEZONE RULES:
├── 中国历史人物 → Asia/Shanghai (backfill)
├── 有明确出生地点 → 使用当地时区
├── 无时区信息 → 默认 Asia/Shanghai (中国) 或 UTC (其他地区)
└── 必须记录实际使用的时区
```

### 3.3 预测截止时间 (Prediction Cutoff)

```text
PREDICTION CUTOFF DETERMINATION:
├── PRE_EVENT 数据集:
│   └── prediction_cutoff = event_date - margin (如 30天)
│
├── HISTORICAL_BLIND 数据集:
│   └── prediction_cutoff = 预测生成时间
│   └── 模型只能使用 ≤ prediction_cutoff 的信息
│
└── POST_HOC 数据集:
    └── prediction_cutoff = N/A (事后验证)
```

---

## 四、时间精度声明示例

### 4.1 高精确度案例

```text
案例: 纪晓岚
├── 出生: 1724-08-03 (公历)
│   ├── event_date_exact: "1724-08-03"
│   ├── date_precision: "DAY"
│   ├── calendar_system: "GREGORIAN"
│   └── source: 《纪晓岚年谱》
│
├── 进士及第: 1754-07 (农历五月)
│   ├── event_date_exact: null
│   ├── event_date_month: "1754-05"
│   ├── date_precision: "MONTH"
│   ├── calendar_system: "LUNAR"
│   └── 转换公历: 1754-06-xx (需 sxtwl 验证)
│
└── 逝世: 1805-03-14 (公历)
    ├── event_date_exact: "1805-03-14"
    ├── date_precision: "DAY"
    └── source: 清史稿
```

### 4.2 低精确度案例

```text
案例: 某宋代文人
├── 出生: "约 1020 年"
│   ├── event_date_exact: null
│   ├── event_date_year: "1020"
│   ├── date_precision: "YEAR"
│   └── source: 《宋史》(无精确日期)
│
└── 逝世: "约 1080 年"
    ├── event_date_exact: null
    ├── event_date_year: "1080"
    └── date_precision: "YEAR"
```

### 4.3 禁止伪造精度的案例

```text
❌ 错误做法:
   来源: "某人在 1998 年进入某公司"
   错误记录: event_date_exact = "1998-03-15"
   
✅ 正确做法:
   来源: "某人在 1998 年进入某公司"
   正确记录:
     event_date_exact = null
     event_date_year = "1998"
     date_precision = "YEAR"
     source_date = "1998年"
```

---

## 五、时间边界检查

### 5.1 合理性检查

```text
REASONABILITY CHECKS:
├── event_date 必须在 birth_date 之后
├── event_date 必须在 death_date 之前 (如已知)
├── event_date 不能超过 source_publication_date
└── prediction_cutoff 必须在 event_date 之前 (对于 PRE_EVENT)
```

### 5.2 一致性检查

```text
CONSISTENCY CHECKS:
├── event_date_exact 必须与 event_date_month 一致
├── event_date_month 必须与 event_date_year 一致
├── source_calendar 必须与 calendar_system 匹配
└── 所有时间字段必须逻辑一致
```

---

## 六、Temporal Alignment 验证流程

```text
TEMPORAL VALIDATION WORKFLOW:
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: Extract Raw Date                                          │
│   ├── 从来源提取原始日期字符串                                        │
│   └── 记录 source_date                                              │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 2: Parse Date                                               │
│   ├── 识别历法系统 (公历/农历)                                       │
│   ├── 解析年月日                                                     │
│   └── 识别精度 (DAY/MONTH/YEAR/UNKNOWN)                            │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 3: Convert & Standardize                                    │
│   ├── 农历 → 公历转换 (使用 sxtwl)                                   │
│   ├── 应用时区                                                      │
│   └── 填充 temporal_field                                          │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 4: Validation                                               │
│   ├── 合理性检查                                                     │
│   ├── 一致性检查                                                     │
│   └── 边界检查                                                       │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 5: Record                                                   │
│   ├── 保存 temporal_field                                          │
│   ├── 标注 date_precision                                         │
│   └── 更新 event_record.status                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 七、关键风险

### 7.1 时间伪造风险

```text
RISK: 伪造精确日期
IMPACT: 高 — 导致错误的时间对齐评估
MITIGATION:
├── 严格禁止伪造
├── 必须保留原始日期字符串
└── 只有明确来源才能标注 DAY 精度
```

### 7.2 历法混淆风险

```text
RISK: 农历/公历混淆
IMPACT: 中 — 导致日期计算错误
MITIGATION:
├── 必须标注 calendar_system
├── 使用 sxtwl 进行转换
└── 转换后记录 source_calendar
```

### 7.3 时区错误风险

```text
RISK: 时区设置错误
IMPACT: 低 — 对历史日期影响较小
MITIGATION:
├── 统一使用 Asia/Shanghai (中国)
├── 有明确地点时调整时区
└── 记录实际使用的时区
```

---

**报告结束**
**下一步**: A2.4 Leakage Classification
