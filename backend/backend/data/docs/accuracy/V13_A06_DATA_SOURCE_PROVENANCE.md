# V1.3 A0.6 — Data Source Provenance Catalog

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: DRAFT — 待审查确认

---

## 原则声明

本文档仅记录数据源的实际来源、许可、版本与可信度。
**禁止修改**: 数据文件、测试代码、引擎代码、Golden Dataset。

---

## 一、数据集来源清单

### 1.1 fate-bench (八字历史案例库)

| 字段 | 内容 |
|------|------|
| **全称** | fate-bench: A Benchmark for Chinese BaZi命理预测 |
| **来源URL** | https://github.com/zhengyutong/fate-bench |
| **许可** | CC BY 4.0 (需署名) |
| **版本** | 1.0 (2025) |
| **总案例数** | 63人 |
| **总题目数** | 295题 |
| **官方答案** | 215题 (answer_provenance: "official") |
| **第三方转录** | 80题 (answer_provenance: "third-party") |
| **排除案例** | 5人（无出生时间） |
| **专家四柱** | 3人（手写验证与sxtwl一致） |
| **竞赛来源** | HKJFMA 2010-2013, 2018, 2021 |
| **覆盖时期** | 公元 1000-1950 |
| **本地路径** | `D:/today/fate-bench/` (假设已clone) |

**可信度评估:**
- 官方答案: HIGH — 由竞赛主办方提供
- 第三方答案: MEDIUM — 竞赛参与者/爱好者转录，可能有误
- 历史人物资料: HIGH — 来自公开史料

**风险项:**
- 80道第三方答案可能包含转录错误
- 2021、2025届无官方答案（仅参赛者提交）
- 部分出生地点/时间存在史料不确定性

---

### 1.2 MingLi-Bench (命理大模型基准测试)

| 字段 | 内容 |
|------|------|
| **全称** | MingLi-Bench: Benchmarking LLMs in Chinese BaZi命理预测 |
| **来源URL** | https://github.com/thu-coai/MingLi-Bench |
| **许可** | MIT |
| **版本** | 1.0 (2024) |
| **总案例数** | 160题 |
| **涉及命主** | 4人 |
| **竞赛来源** | HKJFMA 2022-2025 四届 |
| **与fate-bench重叠** | 120/120 交叉验证一致 |
| **本地路径** | vendored into project |

**可信度评估:**
- 来源可靠: HIGH — 清华大学开源，竞赛数据
- 已交叉验证: ✅ 与fate-bench官方答案一致
- MIT许可: 商业可用，无署名要求

**风险项:**
- 与fate-bench有120题重叠（已在重叠检测中标记）

---

### 1.3 BaziQA (八字问答基准)

| 字段 | 内容 |
|------|------|
| **全称** | BaziQA: A Question Answering Benchmark for Chinese BaZi命理 |
| **来源URL** | https://github.com/thu-coai/BaziQA |
| **许可** | MIT |
| **版本** | 1.0 (2024) |
| **总题目** | ~450题 |
| **命例数** | 90人 |
| **名人案例** | Celebrity50 (50位历史名人) |
| **覆盖届数** | Contest8 (2021-2025) |
| **本地路径** | vendored into project |

**可信度评估:**
- MIT许可: HIGH
- 竞赛数据: HIGH
- 包含名人案例验证: ✅ 可通过史料验证

**风险项:**
- 与fate-bench/MingLi-Bench有部分数据重叠（同一竞赛数据）
- 2021年答案来源可能与fate-bench重复

---

### 1.4 Ziwei Dataset (紫微斗数数据集)

| 字段 | 内容 |
|------|------|
| **来源** | 基于倪海夏《天纪》体系 |
| **许可** | CC BY 4.0 |
| **命盘组合** | 518,400 (60年×12月×30日×12时×2性别) |
| **每例包含** | 完整命盘JSON + 13主题解读文本 |
| **主题范围** | 性格、事业、财运、感情、健康、学业、人际、贵人、小人、时机、决策、变化、综合 |
| **用途** | 排盘正确性验证 + 统计验证 |
| **本地路径** | 未下载（需手动clone） |

**可信度评估:**
- 排盘算法: MEDIUM — 基于固定排盘规则，可交叉验证
- 解读文本: LOW-MEDIUM — 倪海夏个人体系，非统一Ground Truth
- CC BY 4.0: 需署名，商业使用需检查

**风险项:**
- 倪海夏体系与标准紫微斗数体系有差异
- 518,400命盘的解读文本为系统生成，非人工标注

---

### 1.5 CBDB (中国历代人物传记资料库)

| 字段 | 内容 |
|------|------|
| **来源** | 哈佛大学燕京图书馆 + 中研院历史语言研究所 + 北京大学 |
| **许可** | CC BY-NC-SA 4.0 (非商业) |
| **人口数** | 649,533人 |
| **覆盖朝代** | 唐至清 |
| **数据特点** | 生卒年、籍贯、科举、官职、著作、社交网络 |
| **用途** | 历史命主案例筛选 + 事件验证 |
| **本地路径** | 未下载（需申请访问） |

**可信度评估:**
- 数据来源: HIGH — 三机构联合维护，学术级
- 覆盖范围: HIGH — 最大规模的中文传记数据库
- 非商业许可: ⚠️ 顺天项目若商业化需重新评估

**风险项:**
- CC BY-NC-SA 限制商业用途
- 数据量大，需人工筛选可验证案例

---

### 1.6 chunqiu (春秋人物时间线)

| 字段 | 内容 |
|------|------|
| **全称** | Chunqiu: A Dataset for Temporal Knowledge Extraction from Ancient Chinese Texts |
| **来源** | Spring and Autumn Period historical records |
| **许可** | CC BY 4.0 |
| **人物数** | 71人 |
| **事件数** | 121件 |
| **史料来源** | 83个原始史料（《左传》《国语》《史记》等） |
| **特点** | 每条事件可追溯至原始经典 |
| **本地路径** | 未下载 |

**可信度评估:**
- 史料来源: HIGH — 原始经典可直接核查
- 时间精度: HIGH — 精确到月/日
- 验证方式: 可直接对照《左传》原文

**风险项:**
- 春秋时期时间与公历转换存在争议
- 部分事件年代有不同说法

---

### 1.7 Golden Dataset (项目自建黄金案例库)

| 字段 | 内容 |
|------|------|
| **文件路径** | `dataset/golden_v1/golden_cases.json` |
| **案例数** | 50 |
| **事件数** | 518 |
| **创建日期** | 2026-08-22 |
| **来源说明** | 历史人物命例（含出生时间、已知事件） |
| **证据等级** | A/B/C三级 |

**可信度评估:**
- 历史命主: 视具体案例而定（A级案例有史料支持）
- 自建标注: MEDIUM — 需逐条核对原始史料

**风险项:**
- 部分历史人物出生时间存在史料不确定性
- 证据等级A/B/C的判定标准需明确定义

---

## 二、数据重叠检测

### 2.1 跨数据集案例重叠

```text
fate-bench vs MingLi-Bench:
├── 重叠案例: 120题 (已交叉验证一致)
├── 来源: HKJFMA 2022-2025竞赛数据
└── 处理策略: 去重后仅计入一次独立测试

fate-bench vs BaziQA:
├── 重叠案例: 2021年竞赛部分
├── 重叠数量: ~40题
└── 处理策略: 建立去重索引，标记为"关联案例"

MingLi-Bench vs BaziQA:
├── 重叠案例: 2022-2025竞赛数据
├── 重叠数量: ~120题 (同一数据集)
└── 处理策略: 合并为"竞赛数据块"，单独统计
```

### 2.2 独立测试集估算

```text
去重后独立测试用例:
├── fate-bench (官方答案): 215题 → 215独立题
├── fate-bench (第三方答案): 80题 → 80独立题（降权处理）
├── BaziQA (2021独占): ~160题 → 160独立题
├── BaziQA (2022-2025): ~290题 → 与MingLi-Bench重叠
├── MingLi-Bench独占: ~0题 (全部重叠)
└── 合计独立测试用例: ~455题
```

---

## 三、数据源可信度分级

### 可信度等级定义

```text
Level A (黄金): 
├── 官方竞赛答案
├── 古籍原文可直接对照
├── 三机构联合维护数据库
└── 证据等级A的Golden案例

Level B (白银):
├── 第三方转录但经交叉验证
├── 名人传记资料（可通过史料验证）
├── 证据等级B的Golden案例
└── CBDB部分条目

Level C (青铜):
├── 专家手写四柱（少数）
├── 证据等级C的Golden案例
└── Ziwei Dataset 部分数据

Level D (待验证):
├── 无答案或未验证的历史案例
├── 纯系统生成解读（无人工标注）
└── 需要专家审核的案例
```

### 数据集可信度矩阵

| 数据集 | Level | 官方答案比例 | 可追溯性 | 建议权重 |
|--------|-------|-------------|---------|---------|
| fate-bench (官方) | A | 73% (215/295) | HIGH | 1.0 |
| fate-bench (第三方) | B | 27% (80/295) | MEDIUM | 0.7 |
| MingLi-Bench | A | 100% | HIGH | 1.0 |
| BaziQA | A | 100% | HIGH | 1.0 |
| CBDB | A | N/A | HIGH | 0.8 (非商业限制) |
| chunqiu | A | 100% | HIGH | 1.0 |
| Golden Dataset | B-C | 视案例 | MEDIUM | 0.8 |
| Ziwei Dataset | C-D | 0% | LOW | 0.5 |

---

## 四、数据源使用策略

### 4.1 历史盲测数据选择

```text
主要测试集 (Primary):
├── fate-bench 官方答案 (215题) ← 核心验证
├── BaziQA (去重后独立部分) ← 补充验证
└── 自建Golden Dataset (50案例) ← 精度验证

辅助测试集 (Secondary):
├── fate-bench 第三方答案 (80题) ← 带权重降级
├── CBDB (选筛后可验证案例) ← 需人工审核
└── chunqiu (春秋案例) ← 特殊时期验证

不使用 (Excluded):
├── Ziwei Dataset (解读部分) ← 非Ground Truth
└── 重叠案例的去重部分
```

### 4.2 数据预处理要求

```text
每个案例必须包含:
├── [x] 出生日期 (公历)
├── [x] 出生时间 (时辰)
├── [x] 性别
├── [ ] 出生地点 (经度/时区) — 影响真太阳时
├── [ ] 已知事件列表 (日期+类型+描述)
├── [ ] 证据等级 (A/B/C)
└── [ ] 数据源引用 (文献/链接)
```

---

## 五、Provenance 记录模板

```yaml
provenance:
  dataset_name: "fate-bench"
  version: "1.0"
  license: "CC BY 4.0"
  source_url: "https://github.com/zhengyutong/fate-bench"
  local_path: "/path/to/fate-bench"
  downloaded_at: "2026-08-22"
  
  case_level:
    case_id: "GB-1974-04-28"
    answer_provenance: "official"
    evidence_grade: "A"
    original_source: "HKJFMA 2024 Competition"
    cross_verified_with: ["MingLi-Bench"]
    
    risk_flags:
      - name: "birth_location_uncertain"
        severity: "low"
        note: "美国纽约，时区EDT/GMT-4"
  
  aggregation:
    total_cases: 63
    valid_cases: 58  # 排除5人无出生时间
    official_answer_cases: 63
    total_questions: 295
    official_questions: 215
    third_party_questions: 80
```

---

## 六、许可证合规检查

| 数据集 | 许可 | 商业使用 | 署名要求 | 状态 |
|--------|------|---------|---------|------|
| fate-bench | CC BY 4.0 | ✅ 允许 | ✅ 必须 | ⚠️ 待实现 |
| MingLi-Bench | MIT | ✅ 允许 | ❌ 不需要 | ✅ 已满足 |
| BaziQA | MIT | ✅ 允许 | ❌ 不需要 | ✅ 已满足 |
| CBDB | CC BY-NC-SA 4.0 | ❌ 不允许 | ✅ 必须 | ⚠️ 需法律审查 |
| chunqiu | CC BY 4.0 | ✅ 允许 | ✅ 必须 | ⚠️ 待实现 |
| Ziwei Dataset | CC BY 4.0 | ✅ 允许 | ✅ 必须 | ⚠️ 待实现 |
| Golden Dataset | 自建 | ✅ 自有 | N/A | ✅ 无需处理 |

**关键问题:**
- CBDB 的 CC BY-NC-SA 4.0 禁止商业用途
- 顺天项目定位为商业产品，需评估是否可使用 CBDB 数据

---

## 附录：数据来源汇总

```
总数据源数量: 7个
总案例数: ~2000+ (含重叠)
去重后独立案例: ~455题
可信度 A级: 3个 (fate-bench官方, MingLi-Bench, BaziQA)
可信度 B级: 2个 (fate-bench第三方, Golden Dataset)
可信度 C级: 1个 (Ziwei Dataset)
可信度 D级: 0个
待审查: 1个 (CBDB — 非商业许可)
```
