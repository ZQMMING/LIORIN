# V1.3 A2.1 — Dataset Source Qualification

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档定义每个数据源的资格认证流程。
禁止修改任何代码或数据集。

---

## 一、资格认证字段模板

```yaml
source_qualification:
  # Required Fields
  source_id: "str"                    # 唯一标识符
  name: "str"                         # 来源名称
  original_url: "str"                 # 原始 URL 或文献出处
  data_owner: "str"                   # 数据所有者/机构
  publish_date: "YYYY-MM-DD"          # 发布时间
  event_date: "YYYY-MM-DD"            # 事件发生时间
  access_date: "YYYY-MM-DD"           # 数据获取时间
  
  # Classification Fields
  is_public: bool                     # 是否公开可用
  license: "str"                      # 许可证类型
  commercial_use_status: "allowed|restricted|prohibited"
  original_evidence_grade: "A|B|C|D|X"
  is_secondary_source: bool           # 是否二手/三手转载
  can_use_for_accuracy: bool          # 是否可用于 Accuracy 评估
  
  # Risk Assessment
  risk_level: "low|medium|high|critical"
  notes: "str"                        # 审核备注
```

---

## 二、已识别候选数据源

### 2.1 外部 Benchmark 数据源

| source_id | name | original_url | data_owner | publish_date | event_date | is_public | license | commercial_use_status | original_evidence_grade | is_secondary_source | can_use_for_accuracy | risk_level |
|-----------|------|-------------|------------|-------------|-----------|-----------|---------|---------------------|------------------------|---------------------|---------------------|------------|
| FB-OFFICIAL | fate-bench 官方答案 | https://github.com/zhengyutong/fate-bench | Zheng Yutong | 2024-01 | 1700-2020 | ✅ | CC BY 4.0 | ⚠️ restricted | A | ❌ | ✅ | low |
| FB-THIRD | fate-bench 第三方答案 | https://github.com/zhengyutong/fate-bench | Community | 2024-01 | 1700-2020 | ✅ | CC BY 4.0 | ⚠️ restricted | B | ❌ | ⚠️ | medium |
| MLB | MingLi-Bench | https://github.com/... | 社区 | 2024-03 | 1700-2000 | ✅ | MIT | ✅ allowed | A | ❌ | ✅ | low |
| BQ | BaziQA (去重后) | https://github.com/... | 社区 | 2024-02 | 1700-2020 | ✅ | MIT | ✅ allowed | A | ❌ | ✅ | low |
| CBDB | 中国历代人物传记资料库 | http://cbdb.fas.harvard.edu | Harvard/CBS | 持续更新 | 600-1900 | ✅ | CC BY-NC-SA | ❌ prohibited | A | ❌ | ❌ | critical |
| CHQ | chunqiu 春秋案例 | https://github.com/... | 社区 | 2023-11 | 722-481 BC | ✅ | CC BY 4.0 | ⚠️ restricted | A | ❌ | ⚠️ | medium |

### 2.2 自建数据源

| source_id | name | original_url | data_owner | publish_date | event_date | is_public | license | commercial_use_status | original_evidence_grade | is_secondary_source | can_use_for_accuracy | risk_level |
|-----------|------|-------------|------------|-------------|-----------|-----------|---------|---------------------|------------------------|---------------------|---------------------|------------|
| GOLDEN-V1 | Golden Dataset v1 | dataset/golden_v1/ | 项目自建 | 2026-08-21 | 1037-1949 | ❌ | 自建 | ✅ allowed | A-C | ❌ | ✅ | low |
| FB-LOCAL | fate-bench 本地化 | .tmp_cases/fate_bench/ | 项目自建 | 2026-08-20 | 1700-2020 | ❌ | CC BY 4.0 | ⚠️ restricted | A | ❌ | ✅ | low |
| BNDARY | Boundary Cases | tests/test_p014.py | 项目自建 | 2026-08-15 | 1900-2000 | ❌ | 自建 | ✅ allowed | B | ❌ | ✅ | low |

### 2.3 待评估数据源

| source_id | name | original_url | data_owner | publish_date | event_date | is_public | license | risk_level | can_use_for_accuracy | 备注 |
|-----------|------|-------------|------------|-------------|-----------|-----------|---------|------------|---------------------|------|
| ZW-DS | Ziwei Dataset | https://github.com/9sssss/iztro | iztro团队 | 2024-06 | 1900-2020 | ✅ | CC BY 4.0 | medium | ⚠️ | 518,400命盘，解读非GT |
| HK | 河洛理数原文 | 清代典籍 | 江本盛 | 1700s | N/A | ❌ | 公版 | low | ✅ | 经典原文，用于 O3 验证 |
| WL | 维基百科 | https://wikipedia.org | 社区 | 持续 | 历史 | ✅ | CC BY-SA | medium | ❌ | 二手来源，需交叉验证 |

---

## 三、资格判定规则

### 3.1 商业使用状态判定

```text
LICENSE TYPE DECISION:
├── CC BY 4.0 → commercial_use_status = "allowed" ✅
├── MIT → commercial_use_status = "allowed" ✅
├── CC BY-NC-SA → commercial_use_status = "prohibited" ❌
├── CC BY-NC → commercial_use_status = "prohibited" ❌
├── Custom/Proprietary → commercial_use_status = "restricted" ⚠️
└── Public Domain → commercial_use_status = "allowed" ✅
```

**CBDB 特别说明**:
- 许可: CC BY-NC-SA 4.0 (Non-Commercial)
- 商业使用: ❌ 禁止
- 风险等级: critical
- 建议: 禁止用于商业产品验证，仅限学术研究参考

### 3.2 证据等级判定

```text
EVIDENCE GRADE CRITERIA:
├── Grade A (HIGH):
│   ├── 单一可靠来源 + 多源交叉验证
│   ├── 原始文献记载 (古籍、官方档案)
│   ├── 官方 published benchmark 答案
│   └── 时间戳明确，无歧义
│
├── Grade B (MEDIUM):
│   ├── 单一可靠来源
│   ├── 权威出版物引用
│   ├── 可追溯但不完全独立
│   └── 时间戳较明确
│
├── Grade C (MODERATE):
│   ├── 二手/三手转载
│   ├── 现代研究论文引用
│   ├── 部分来源不透明
│   └── 时间戳需推断
│
├── Grade D (LOW):
│   ├── 网络文章、博客
│   ├── 民间记载、传说
│   ├── 无明确来源
│   └── 时间戳模糊
│
└── Grade X (UNSUITABLE):
    ├── 合成数据
    ├── 自证循环
    ├── 算法生成案例
    └── 无可靠证据
```

### 3.3 can_use_for_accuracy 判定

```text
ACCURACY USE DECISION:
├── ✅ ALLOWED:
│   ├── evidence_grade = A
│   ├── commercial_use_status = allowed
│   ├── leakage_classification = CLEAN
│   └── is_secondary_source = false (primary or verified)
│
├── ⚠️ CONDITIONAL:
│   ├── evidence_grade = A-B
│   ├── commercial_use_status = restricted
│   ├── leakage_classification = REVIEWED
│   └── is_secondary_source = true (cross-verified)
│
└── ❌ PROHIBITED:
    ├── evidence_grade = C-D
    ├── commercial_use_status = prohibited
    ├── leakage_classification = CONTAMINATED
    ├── is_secondary_source = true (unverified)
    └── 命理"预测"作为 Oracle
```

---

## 四、Source Qualification 决策矩阵

| source_id | evidence_grade | commercial_use | leakage_status | can_use_for_accuracy | 决策 |
|-----------|---------------|----------------|----------------|---------------------|------|
| FB-OFFICIAL | A | ⚠️ restricted | CLEAN | ✅ | ✅ 有条件使用 |
| FB-THIRD | B | ⚠️ restricted | CLEAN | ✅ | ✅ 降权使用 (weight=0.7) |
| MLB | A | ✅ allowed | CLEAN | ✅ | ✅ 直接使用 |
| BQ | A | ✅ allowed | CLEAN | ✅ | ✅ 直接使用 |
| CBDB | A | ❌ prohibited | REVIEWED | ❌ | ❌ 禁止商业使用 |
| CHQ | A | ⚠️ restricted | CLEAN | ✅ | ✅ 有条件使用 |
| GOLDEN-V1 | A-C | ✅ allowed | CLEAN | ✅ | ✅ 作为 Tier 1 基础 |
| FB-LOCAL | A | ⚠️ restricted | CLEAN | ✅ | ✅ 本地化备份 |
| BNDARY | B | ✅ allowed | CLEAN | ✅ | ✅ 边界案例验证 |
| ZW-DS | B | ✅ allowed | REVIEWED | ⚠️ | ⚠️ 仅排盘部分 |
| HK | N/A | N/A | N/A | ✅ | ✅ 用于 O3 验证 |
| WL | C-D | ✅ allowed | REVIEWED | ❌ | ❌ 二手来源，需交叉 |

---

## 五、资格认证流程

```text
SOURCE QUALIFICATION WORKFLOW:
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: Source Identification                                     │
│   ├── 确定数据来源                                                   │
│   ├── 记录原始 URL/文献出处                                            │
│   └── 提取元数据 (author, date, publisher)                          │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 2: License Verification                                      │
│   ├── 确认许可证类型                                                  │
│   ├── 判定商业使用状态                                                  │
│   └── 标注风险等级                                                    │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 3: Evidence Grade Assessment                                 │
│   ├── 判定证据等级 (A/B/C/D/X)                                       │
│   ├── 确认是否为二手/三手转载                                          │
│   └── 检查是否有独立验证                                                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 4: Leakage Screening                                         │
│   ├── 检查 event_date vs publication_date                           │
│   ├── 检查 prediction_cutoff 是否合理                                 │
│   └── 标注 leakage 风险                                               │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Step 5: Final Decision                                            │
│   ├── can_use_for_accuracy = true/false/conditional                 │
│   ├── 记录审核备注                                                    │
│   └── Gate Keeper 签字确认                                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 六、CBDB 特别处理

```text
CBDB (中国历代人物传记资料库) Special Handling:
├── 数据来源: Harvard-Yenching Library + CBS
├── 许可: CC BY-NC-SA 4.0
├── 商业使用: ❌ 禁止
├── 数据量: 649,533 人物记录
├── 时间范围: 600 BC - 1900 AD
├── 价值: 极高的历史人物传记覆盖
└── 使用限制:
    ├── ✅ 学术研究参考
    ├── ⚠️ 需法律审查后方可用于商业产品
    └── ❌ 不可直接进入生产数据集
```

**建议**: CBDB 数据仅作为 Research Reference，不进入 Accuracy Evaluation Dataset。

---

## 七、Source Qualification 交付物

```text
docs/accuracy/
├── V13_A21_SOURCE_QUALIFICATION_REGISTRY.md  (本文件)
├── V13_A21_LEASED_DATA_RECORD.md             (CBDB等受限数据记录)
└── V13_A21_SOURCE_INVENTORY.md               (完整数据源清单)
```

---

**报告结束**
**下一步**: A2.2 Event Schema / Normalization
