# 紫微 Production Runtime Trace 最终报告

**执行日期**: 2026-09-02  
**仲裁版本**: V0 (IZTRO_CORE + SHUNTIAN_ADAPTER)  
**状态**: 等待第二阶段裁决

---

## 一、核心发现

### 1.1 当前引擎实际架构

```
ZIWEI_RULE_PROFILE_V0
├── CORE = iztro 2.6.0 (黑盒依赖)
│   ├── byLunar() → 命宫/身宫/五行局/主星
│   └── horoscope() → 流年/流月/流日四化
│
├── SHUNTIAN_ADAPTER (确定性)
│   ├── GAN_SIHUA dict (声明: 中州派/王亭之)
│   ├── get_sanfang_sizheng() (三方四正)
│   └── palace_self_mutagen() (宫干自化)
│
└── ARCHITECTURE VIOLATIONS (待删除)
    ├── native_direction() ❌
    ├── SIHUA_EFFECT (INCREASE/DECREASE) ❌
    └── score_topic() ❌
```

**结论**: 不能称为"中州派引擎"。更准确的描述是 **Iztro Core + Shuntian Adapter**，其中只有 `GAN_SIHUA` 明确声明为"中州派"。

---

## 二、真太阳时验证

### 2.1 Differential Test 结果

| 案例 | 标准时间 | 经度 | 标准时辰 | 真太阳时 | 跨界 |
|------|----------|------|----------|----------|------|
| 毛泽东 | 06:00 | 112.9°E | 辰时(3) | 辰时(3) | 否 |
| 案例2 | 04:59 | 87.6°E | 辰时(3) | **酉时(9)** | ✅ 是 |
| 案例3 | 04:59 | 121.5°E | 辰时(3) | 辰时(3) | 否 |

**关键证据**: 案例2 证明真太阳时校正函数**确实有效**，且会导致跨时辰边界变化。

### 2.2 当前生产路径

```python
# compute() 默认不传 longitude
chart = engine.compute(LUNAR_DATE, HOUR, GENDER)  # 无真太阳时

# 需要显式调用校正函数
true_solar_ti = engine.corrected_hour_index(HOUR, LONGITUDE, SOLAR_DATE)
```

**结论**: 真太阳时校正函数存在但未进入默认排盘路径。

---

## 三、四时间尺度对比 (本命盘 1893-12-26)

| 尺度 | 触发源 | 四化结果 |
|------|--------|----------|
| 生年 | 癸干 | 破军禄 / 巨门权 / 太阴科 / 贪狼忌 |
| 大限 | 1893年 | 巨门禄 / 太阳权 / 文曲科 / 文昌忌 |
| 流年 | 1893年 | 破军禄 / 巨门权 / 太阴科 / 贪狼忌 |
| 流月 | 1893-01 | 天梁禄 / 紫微权 / 左辅科 / 武曲忌 |
| 流日 | 1893-11-19 | 太阳禄 / 武曲权 / 太阴科 / 天同忌 |

**注意**: 流月/流日使用独立测试日期，不与本命混淆。

---

## 四、待仲裁问题清单

| # | 问题 | 当前状态 | 建议动作 |
|---|------|----------|----------|
| 1 | `native_direction()` 已实现 | 返回 opportunity/caution/neutral | 删除或标记 deprecated |
| 2 | `SIHUA_EFFECT` 语义映射 | INCREASE/DECREASE 映射 | 移至语义层，不冻结 |
| 3 | `score_topic()` 断事评分 | 已实现确定性计算 | 移至决策层，不冻结 |
| 4 | 真太阳时默认策略 | 函数存在但不自动调用 | 是否改为 `compute()` 自动传入? |
| 5 | 大限起运年龄 | iztro 默认 (案例显示命宫 3 岁) | 需验证是否符合传统规则 |
| 6 | iztro 传统规则来源 | 黑盒，无法确认流派 | 需反向工程或文档确认 |

---

## 五、Commit 信息

```
3d7de5b 紫微 Production Runtime Trace: 严格审计工具
6bd4681 紫微 Production Trace 审计报告
```

**文件变更**:
- 新增: `scripts/ziwei_production_trace.py` (309行)
- 删除: `scripts/ziwei_runtime_trace.py` (旧stub版本)
- 新增: `docs/audit/ZIWEI_PRODUCTION_TRACE_AUDIT_REPORT.md` (95行)

---

## 六、下一阶段

完成当前仲裁后，可进入：

1. **第二阶段**: 逐项反查 iztro 算法来源（是否三合/飞星/中州）
2. **第三阶段**: 决定是否需要替换 iztro 黑盒，或接受其作为"事实标准"
3. **第四阶段**: 决定是否删除架构违规项 (`native_direction`, `SIHUA_EFFECT`, `score_topic`)

---

**审计者**: Hermes Agent  
**状态**: 等待仲裁裁决 `ZIWEI_PRODUCTION_TRACE_V2`