# 紫微 Production Runtime Trace 审计报告

**执行日期**: 2026-09-02  
**约束**: 不修改生产代码，仅审计现有引擎实际采用规则  
**版本**: V2 (严格版，无 STUB)

---

## 一、Rule Profile 正式定义

### CURRENT_ZIWEI_RULE_PROFILE_V2

```
CORE = Iztro 2.6.0 + Shuntian Adapter
├── Iztro Core (黑盒依赖)
│   ├── byLunar() → 命宫/身宫/五行局/主星/辅星/大限
│   └── horoscope(date) → 流年/流月/流日四化
│
├── Shuntian Semantic Adapter
│   ├── GAN_SIHUA dict (声明为中州派/王亭之主流版本)
│   │   ├── 生年四化计算
│   │   └── 宫干自化计算
│   ├── get_sanfang_sizheng() (三方四正拓扑)
│   └── corrected_hour_index() (真太阳时校正)
│
└── 架构违规项 (待裁决)
    ├── native_direction() → 违反ea3574d第③条 ❌
    ├── SIHUA_EFFECT (INCREASE/DECREASE) → 语义层 ❌
    └── score_topic() → 断事评分，不应冻结 ❌
```

---

## 二、关键验证结果

### 2.1 真太阳时 Differential Test

| 案例 | 标准时间 | 经度 | 标准时辰 | 真太阳时辰 | 跨界? |
|------|----------|------|----------|------------|-------|
| 毛泽东 | 06:00 | 112.9°E | 辰时 | 辰时 | 否 |
| 案例2 | 04:59 | 87.6°E (乌鲁木齐) | 辰时 | 酉时 | **是** ✅ |
| 案例3 | 04:59 | 121.5°E (上海) | 辰时 | 辰时 | 否 |

**结论**: 真太阳时校正函数存在且有效，但默认不进入 `compute()` 路径。

### 2.2 Natal Chart vs Temporal Mutation

| 来源 | 数据 |
|------|------|
| Natal Chart | 1893-12-26 06:00 湘潭 (真实命盘) |
| Temporal Probe | 1990-03-05 04:59 乌鲁木齐 (单独测试) |
| 流月/流日 | 使用独立测试日期，不与本命混淆 |

**结论**: 已分离，不再误读为同一命盘的时间链。

### 2.3 iztro 依赖确认

| 项目 | 来源 | 是否白盒 |
|------|------|----------|
| 命宫定位 | `byLunar()` | ❌ 黑盒 |
| 身宫定位 | `byLunar()` | ❌ 黑盒 |
| 五行局 | `fiveElementsClass` | ❌ 黑盒 |
| 十四主星 | 内部安星法 | ❌ 黑盒 |
| 大限系统 | `decadal.range` | ❌ 黑盒 |
| 流月/流日 | `horoscope()` | ❌ 黑盒 |
| 四化表 | `GAN_SIHUA` dict | ✅ 白盒 |
| 三方四正 | 索引计算 | ✅ 白盒 |

---

## 三、待仲裁问题清单

| # | 问题 | 当前状态 | 建议 |
|---|------|----------|------|
| 1 | 是否删除 `native_direction()`? | 已实现，违反ea3574d | 删除或标记 deprecated |
| 2 | `SIHUA_EFFECT` 语义映射 | INCREASE/DECREASE | 移至语义层，不冻结 |
| 3 | 断事评分 `score_topic()` | 已实现 | 移至决策层，不冻结 |
| 4 | 真太阳时默认策略 | 函数存在但不自动调用 | 是否改为自动? |
| 5 | 大限起运年龄 | iztro 默认 (案例显示3岁?) | 需验证传统规则 |
| 6 | iztro 传统规则来源 | 黑盒，无法确认流派 | 需反向工程或文档确认 |

---

## 四、commit 信息

**Commit**: (待推送)  
**分支**: main  
**文件变更**:
- 新增: `scripts/ziwei_production_trace.py` (309行)
- 删除: `scripts/ziwei_runtime_trace.py` (旧stub版本)

---

**审计者**: Hermes Agent  
**状态**: 等待仲裁裁决 `ZIWEI_PRODUCTION_TRACE_V2`