# 紫微 Runtime Trace 报告
**执行日期**: 2026-09-02  
**案例**: 毛泽东 1893-12-26 06:00 农历 癸巳年十一月十九日辰时  
**出生地**: 湖南湘潭 (112.9°E)  
**约束**: 不修改代码，仅审计现有引擎实际采用规则

---

## 一、固定案例排盘结果

### 1.1 输入参数
| 参数 | 值 |
|------|-----|
| 农历日期 | (1893, 11, 19) |
| 阳历日期 | (1893, 12, 26) |
| 时辰 | 6h (辰时) |
| 性别 | male |
| 出生地经度 | 112.9°E |

### 1.2 历法转换
| 项目 | 结果 | 来源 |
|------|------|------|
| 时辰index | 3 (辰时) | `time_index_from_hour(6)` |
| 真太阳时校正 | 3 (无变化) | `corrected_hour_index(6, 112.9, ...)` |
| 闰月 | False | 月=11 > 0 |
| 晚子时 | N/A | hour=6 ≠ 23 |

### 1.3 命盘定位
| 项目 | 结果 | 来源 |
|------|------|------|
| 命宫地支 | 酉 | iztro `earthlyBranchOfSoulPalace` |
| 身宫地支 | 卯 | iztro `earthlyBranchOfBodyPalace` |
| 五行局 | 木三局 | iztro `fiveElementsClass` |

### 1.4 十四主星落宫
| 宫位 | 地支 | 主星 |
|------|------|------|
| 命宫 | 酉 | 天机、巨门 |
| 兄弟 | 申 | 贪狼 |
| 夫妻 | 未 | 太阳、太阴 |
| 子女 | 午 | 武曲、天府 |
| 财帛 | 巳 | 天同 |
| 疾厄 | 辰 | 破军 |
| 迁移 | 卯 | (空宫) |
| 仆役 | 寅 | 廉贞 |
| 官禄 | 丑 | (空宫) |
| 田宅 | 子 | 七杀 |
| 福德 | 亥 | 天梁 |
| 父母 | 戌 | 紫微、天相 |

### 1.5 生年四化 (癸干)
| 四化 | 星曜 | 落宫 |
|------|------|------|
| 化禄 | 破军 | 疾厄宫 |
| 化权 | 巨门 | 命宫 |
| 化科 | 太阴 | 夫妻宫 |
| 化忌 | 贪狼 | 兄弟宫 |

### 1.6 大限系统
| 宫位 | 地支 | 大限范围 | 大限天干 |
|------|------|----------|----------|
| 命宫 | 酉 | 3-12岁 | 辛 |
| 兄弟 | 申 | 13-22岁 | 庚 |
| 夫妻 | 未 | 23-32岁 | 己 |
| 子女 | 午 | 33-42岁 | 戊 |
| 财帛 | 巳 | 43-52岁 | 丁 |
| 疾厄 | 辰 | 53-62岁 | 丙 |
| 迁移 | 卯 | 63-72岁 | 乙 |
| 仆役 | 寅 | 73-82岁 | 甲 |
| 官禄 | 丑 | 83-92岁 | 乙 |
| 田宅 | 子 | 93-102岁 | 甲 |
| 福德 | 亥 | 103-112岁 | 癸 |
| 父母 | 戌 | 113-122岁 | 壬 |

### 1.7 四时间尺度四化对比
| 尺度 | 触发源 | 四化结果 |
|------|--------|----------|
| 生年 | 癸干 | 破军、巨门、太阴、贪狼 |
| 大限 | iztro horoscope | 巨门、太阳、文曲、文昌 |
| 流年(1893) | iztro horoscope | 破军、巨门、太阴、贪狼 |
| 流月(2000-01) | iztro horoscope | 太阴、天同、天机、巨门 |
| 流日(2000-01-15) | iztro horoscope | 天梁、紫微、左辅、武曲 |

### 1.8 宫干自化
| 宫位 | 宫干 | 自化 |
|------|------|------|
| 命宫 | 辛 | 巨门→禄 |
| 夫妻 | 己 | 文曲→忌 |
| 财帛 | 丁 | 天同→权 |

---

## 二、CURRENT_IMPLEMENTED_ZIWEI_RULE_PROFILE

### 2.1 核心引擎
```
核心: iztro 2.6.0 (npm package)
调用: Node.js subprocess → byLunar() + horoscope()
数据: 农历输入，阳历输出
```

### 2.2 已确认的流派特征

| # | 特征 | 实现方式 | 来源 |
|---|------|----------|------|
| 1 | 四化表 | GAN_SIHUA dict | ziwei_engine.py:76-87 |
| 2 | 注释标注 | "中州派/王亭之主流版本" | 代码注释 |
| 3 | 闰月处理 | lunar_python 负月表示 | _compute_via_iztro:245 |
| 4 | 子时处理 | 0h=早子(index 0), 23h=晚子(index 12) | time_index_from_hour:94-104 |
| 5 | 真太阳时 | 有校正函数，默认不调用 | corrected_hour_index:949-971 |
| 6 | 命宫/身宫 | iztro byLunar() 计算 | _compute_via_iztro:254 |
| 7 | 五行局 | iztro fiveElementsClass | full_chart:888 |
| 8 | 十二宫顺序 | 固定数组 ZW_PALACES_ORDER | ziwei_engine.py:91 |
| 9 | 三方四正 | 本宫+对宫(+6)+三合(+4,+8) | get_sanfang_sizheng:572-629 |
| 10 | 大限 | iztro decadal.range + decadal.heavenlyStem | full_chart:899-901 |
| 11 | 流年/流月/流日 | horoscope('YYYY-M-D') 链式调用 | flow_years/month/day_mutagen |
| 12 | 空宫借星 | 命宫无主星时借对宫 | _compute_via_iztro:259-269 |
| 13 | 宫干自化 | GAN_SIHUA 查表实现 | palace_self_mutagen:928-947 |

### 2.3 无法确定的流派特征（黑盒）

| # | 特征 | 原因 |
|---|------|------|
| 1 | 紫微星安星法 | iztro 内部算法，未公开 |
| 2 | 十四主星安星法 | iztro 内部算法，未公开 |
| 3 | 辅星/煞星安星法 | iztro 内部算法，未公开 |
| 4 | 命宫计算公式 | iztro 内部算法，未公开 |
| 5 | 大限顺逆规则 | iztro 默认算法，未验证传统 |
| 6 | 起运年龄规则 | iztro 默认算法，未验证传统 |
| 7 | 流月算法细节 | iztro horoscope() 黑盒 |
| 8 | 流日算法细节 | iztro horoscope() 黑盒 |

### 2.4 架构问题（违反ea3574d裁决）

| # | 问题 | 位置 | 严重程度 |
|---|------|------|----------|
| 1 | native_direction() 已实现 | ziwei_engine.py:186-214 | 🔴 违反裁决 |
| 2 | SIHUA_EFFECT 语义映射 | ziwei_engine.py:47-52 | 🟡 不应冻结 |
| 3 | score_topic() 断事评分 | ziwei_engine.py:417-570 | 🟡 不应冻结 |
| 4 | 真太阳时未自动调用 | compute() 未传 longitude | 🟡 设计选择 |

---

## 三、关键发现

### 3.1 iztro 黑盒依赖
- **核心排盘逻辑完全依赖 iztro npm 包**
- 命宫/身宫/五行局/星曜分布均由 iztro 计算
- 代码中明确标注"紫微斗数传统使用农历输入"

### 3.2 四化表已显式声明流派
```python
# ziwei_engine.py:75
# 十干四化表（中州派/王亭之主流版本，禄权科忌）
GAN_SIHUA = {
    "甲": ("廉贞", "破军", "武曲", "太阳"),
    ...
}
```
**确认**: 采用中州派/王亭之主流版本

### 3.3 真太阳时校正存在但未启用
- `corrected_hour_index()` 函数已实现
- 但 `compute()` 调用时未传入 longitude
- 默认使用北京时间（120°E）

### 3.4 大限起运年龄
- 案例显示命宫大限从3岁开始（非传统2岁）
- **需验证**: 这是否是 iztro 默认规则或传统规则

### 3.5 架构违规项
1. **native_direction()** 已实现返回 opportunity/caution/neutral
   - 违反 ea3574d 裁决第③条
   - 应删除或标记为 deprecated
   
2. **SIHUA_EFFECT** 包含 INCREASE/DECREASE 语义映射
   - 违反 ea3574d 裁决第②条
   - 属于语义层，不应进入 Deterministic Core

3. **score_topic()** 断事评分系统已实现
   - 违反 ea3574d 裁决第②条
   - 评分 ≠ 排盘，不能一起冻结

---

## 四、建议

### 4.1 可冻结 (Deterministic Core 候选)
```
✅ 四化表 GAN_SIHUA (中州派/王亭之)
✅ 命宫/身宫定位 (iztro byLunar)
✅ 五行局 (iztro fiveElementsClass)
✅ 十二宫结构 (ZW_PALACES_ORDER)
✅ 三方四正公式 (idx+6, idx+4, idx+8)
✅ 空宫借星规则
✅ 宫干自化计算
✅ 四时间尺度四化 (生年/大限/流年/流月/流日)
```

### 4.2 暂不冻结 (Semantic Layer)
```
❌ native_direction() → 应删除
❌ SIHUA_EFFECT (INCREASE/DECREASE) → 应移至语义层
❌ score_topic() 断事评分 → 应移至决策层
❌ decadal_soul_effect() → 应移至语义层
```

### 4.3 待验证 (Black Box)
```
⏸️ 紫微星安星法 (iztro内部)
⏸️ 十四主星安星法 (iztro内部)
⏸️ 大限顺逆规则 (iztro内部)
⏸️ 起运年龄计算 (iztro内部)
⏸️ 流月/流日算法细节 (iztro内部)
```

---

**审计者**: Hermes Agent  
**状态**: Runtime Trace 完成，等待仲裁裁决
