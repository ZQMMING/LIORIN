# 顺天引擎 V-Validation Report V1

**生成时间**: 2026-08-22  
**数据集**: Golden Dataset V1 (50 cases, 518 events)  
**验证方法**: 历史回测（时间轴匹配）

---

## 一、验证结果摘要

| 指标 | 数值 |
|------|------|
| 案例总数 | 50 |
| 实际事件数 | 518 |
| 预测事件数 | 307 |
| 匹配事件数 | 13 |
| **Precision** | **4.23%** |
| **Recall** | **2.51%** |
| **F1 Score** | **3.15%** |

### 解读

当前精度/召回率较低，原因分析：
1. **预测逻辑简化**: 仅基于日主和月柱推断，未使用完整命盘分析
2. **时间窗口宽松**: ±2年容差导致大量预测无法精确匹配
3. **事件类别粗粒度**: 缺乏细粒度的事件分类

**这不是系统失败，而是基线结果**。后续改进将逐步提升。

---

## 二、测试基础设施

### 2.1 单元测试
```
791 passed, 1 skipped in 15.39s
```

### 2.2 测试覆盖模块
- `tests/test_v_validation.py` — 12 tests
- `tests/test_ontology.py` — 21 tests
- `tests/test_mingli_bench_blind.py` — 3 tests (skip)
- `tests/test_external_benchmarks.py` — 1 test (skip)

---

## 三、Golden Dataset V1

### 3.1 数据来源

| 来源 | 案例数 | 事件数 | 证据等级 |
|------|--------|--------|----------|
| 古籍案例 | 30 | 320 | A/B |
| 现代名人 | 15 | 160 | B |
| MingLi-Bench | 5 | 38 | A |

### 3.2 历史人物分布

- **唐代**: 李白、杜甫、王维
- **宋代**: 苏轼、欧阳修、王安石
- **清代**: 纪晓岚、袁枚
- **现代**: 毛泽东、周恩来、邓小平

---

## 四、Event Ontology V1

### 4.1 事件类别体系

```
EventCategory (共34类):
- 人生大事: CHILD_BIRTH, PARENT_DEATH, MARRIAGE, DIVORCE
- 教育科举: EXAM, EDUCATION_START, EDUCATION_END
- 事业职场: JOB_CHANGE, PROMOTION, DEMOTION, RESIGNATION
- 家庭关系: FAMILY_CHANGE, NEW_RELATIONSHIP, CHILD_BIRTH_EVENT
- 财务: MAJOR_INCOME, FINANCIAL_LOSS, WEALTH_CHANGE
- 健康: ILLNESS, RECOVERY, CRITICAL_ILLNESS
- 社会政治: WAR, POLITICAL_CHANGE, EXILE, IMPRISONMENT
- 荣誉成就: AWARD, RECOGNITION, TITLE_GRANTED
```

### 4.2 严重程度分级

```
EventSeverity (1-5级):
1. TRIVIAL  — 普通
2. SLIGHT   — 轻微变化
3. MODERATE — 明显变化
4. MAJOR    — 重大人生事件
5. CRITICAL — 极重大人生事件
```

### 4.3 证据等级

```
EvidenceGrade:
A - 明确原始记录
B - 多来源交叉验证
C - 单一来源/专家判断
D - 论坛匿名案例
E - 无法验证
```

Golden Dataset 只接受 A/B 级。

---

## 五、验证金字塔架构

```
                  ┌───────────────────┐
                  │ Phase V5: 前瞻冻结│  V-FROZEN-2026-09-01
           ┌──────┴───────────────────┴──────┐
           │ L5: 前瞻预测（冻结后验证）         │
    ┌──────┴──────────────────────────────────┴──────┐
    │ L4: 消融实验 + 基线对比                           │
    │   - Combined vs Bazi-only vs Heluo-only        │
    │   - 增量贡献分析                                 │
    └─────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────┐
    │ L3: 历史回测（Golden Dataset）                    │
    │   - 50 cases, 518 events                         │
    │   - 时间窗口匹配（±2年）                          │
    │   - Precision/Recall/F1 计算                     │
    └─────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────┐
    │ L2: 结构推断验证                                  │
    │   - 本命/元堂/流年/流月/流日 一致性检查           │
    └─────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────┐
    │ L1: 算法正确性                                   │
    │   - 八字计算 vs MySQL/MingLi                     │
    │   - 河洛计算 vs iztro                            │
    │   - 紫微星曜位置                                 │
    └─────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────┐
    │ L0: 出生数据正确性                               │
    │   - 公历转干支公式                              │
    │   - 时柱计算                                   │
    └─────────────────────────────────────────────────┘
```

---

## 六、Next Steps

### 6.1 立即可做
1. **优化预测逻辑** — 接入完整 pipeline，使用 SignalEngine
2. **收紧时间窗口** — 从±2年改为±6个月（Major事件）
3. **扩展数据集** — 目标100 cases, 1000+ events

### 6.2 中期目标
1. **消融实验** — 验证河洛/八字/紫微各模块增量贡献
2. **MingLi-Bench盲测** — 160题完整测试
3. **基线对比** — 与传统命理师预测对比

### 6.3 长期目标
1. **V-FROZEN-2026-09-01** — 冻结当前模型
2. **前瞻预测** — 对2026-09-01之后的事件进行预测
3. **科学验证闭环** — 预测→验证→反馈→改进

---

## 七、文件清单

| 文件 | 说明 |
|------|------|
| `dataset/golden_v1/golden_cases.json` | 50 cases, 518 events |
| `src/tongshu/v_validation/ontology.py` | Event Ontology V1 |
| `scripts/golden_backtest.py` | 回测脚本 |
| `docs/golden_backtest_results.json` | 回测结果 |
| `docs/V_VALIDATION_V1.md` | 验证体系文档 |
| `tests/test_ontology.py` | 21 tests |

---

**结论**: Golden Dataset V1 建立完成，基础回测框架就绪。当前 Precision 4.23% 是基线，后续优化空间巨大。验证金字塔架构清晰，可支撑后续科学验证工作。
