# 紫微 Rule Provenance Matrix 审计报告

**执行日期**: 2026-09-02  
**目标**: 逐项反查 iztro 2.6.0 各规则与传统紫微流派的对应关系

---

## 一、核心发现

### 1.1 iztro 支持两种算法配置

```javascript
// iztro/lib/astro/astro.js line 46-49
var _algorithm = 'default';  // 默认算法

/**
 * 排盘派别设置。
 * @version v2.5.0
 * @default 'default'
 *
 * default: 以《紫微斗数全书》为基础安星
 * zhongzhou: 以中州派安星法为基础安星
 */
```

**关键发现**: iztro 明确支持两种算法模式，默认使用 `default`（通行派），非中州派。

### 1.2 四化表完全一致

| 天干 | iztro 默认四化表 | 顺天 GAN_SIHUA | 一致? |
|------|------------------|----------------|-------|
| 甲   | 廉贞、破军、武曲、太阳 | 廉贞、破军、武曲、太阳 | ✅ |
| 乙   | 天机、天梁、紫微、太阴 | 天机、天梁、紫微、太阴 | ✅ |
| 丙   | 天同、天机、文昌、廉贞 | 天同、天机、文昌、廉贞 | ✅ |
| 丁   | 太阴、天同、天机、巨门 | 太阴、天同、天机、巨门 | ✅ |
| 戊   | 贪狼、太阴、右弼、天机 | 贪狼、太阴、右弼、天机 | ✅ |
| 己   | 武曲、贪狼、天梁、文曲 | 武曲、贪狼、天梁、文曲 | ✅ |
| 庚   | 太阳、武曲、太阴、天同 | 太阳、武曲、太阴、天同 | ✅ |
| 辛   | 巨门、太阳、文曲、文昌 | 巨门、太阳、文曲、文昌 | ✅ |
| 壬   | 天梁、紫微、左辅、武曲 | 天梁、紫微、左辅、武曲 | ✅ |
| 癸   | 破军、巨门、太阴、贪狼 | 破军、巨门、太阴、贪狼 | ✅ |

**结论**: 四化表与中州派/王亭之主流版本一致，但 iztro 默认算法为 `default`（通行派）。

### 1.3 命主/身主计算差异

```javascript
// iztro/lib/astro/astro.js line 210-212
// 中州派地支以年支找命主
// 通用派别以命宫地支找命主
var soul = (0, i18n_1.t)(data_1.earthlyBranches[
    (0, exports.getConfig)().algorithm === 'zhongzhou' 
        ? earthlyBranchOfYear   // 中州派: 用年支
        : earthlyBranchOfSoulPalace  // 通行派: 用命宫地支
].soul);
```

**关键发现**: 
- `default` 算法：命主/身主由**命宫地支**决定（通行派）
- `zhongzhou` 算法：命主/身主由**年支**决定（中州派）

---

## 二、ZIWEI_RULE_PROVENANCE_MATRIX

### 2.1 完整规则矩阵

| # | 规则项 | 来源 | 公式/算法 | 传统出处 | iztro算法 | 验证状态 | 备注 |
|---|--------|------|----------|----------|-----------|----------|------|
| 1 | 命宫定位 | iztro palace.getSoulAndBody() | 寅起正月，顺数至生月，逆数生时为命宫 | 《紫微斗数全书》 | default | ✅ 白盒可验证 | 通行派标准算法 |
| 2 | 身宫定位 | iztro palace.getSoulAndBody() | 寅起正月，顺数至生月，顺数生时为身宫 | 《紫微斗数全书》 | default | ✅ 白盒可验证 | 通行派标准算法 |
| 3 | 五行局 | iztro palace.getFiveElementsClass() | 纳音五行，干支相加取余 (木1金2水3火4土5) | 《紫微斗数全书》 | default | ✅ 白盒可验证 | 命宫干支起局 |
| 4 | 紫微星安星法 | iztro star.location.getStartIndex() | 六五四三二，酉午亥辰丑... | 《紫微斗数全书》 | default | ✅ 白盒可验证 | 命宫干支起局 |
| 5 | 十四主星分布 | iztro star.location (大循环) | 依紫微星位置循环安星 | 《紫微斗数全书》 | default | ✅ 与顺天一致 | 白盒验证通过 |
| 6 | 辅星/煞星安星法 | iztro star.location.*Index() | 按年干支、月日等规则安星 | 《紫微斗数全书》 | default | ✅ 白盒可验证 | 禄存、擎羊、陀罗、天马等 |
| 7 | 大限起运年龄 | iztro palace.getHoroscope() | 传统规则: 男顺女逆，起运2岁 | 传统规则 | default (ageDivide=normal) | ⚠️ 需验证传统 | 案例显示3岁起 |
| 8 | 大限顺逆行 | iztro palace.getHoroscope() | 阳男阴女顺行，阴男阳女逆行 | 传统规则 | default | ⚠️ 需验证传统 | 源码中有阴阳判断逻辑 |
| 9 | 流年四化 | iztro horoscope('YYYY-6-15') | 以农历六月十五为基准 | 《紫微斗数全书》 | default | ✅ 与顺天一致 | 使用顺天GAN_SIHUA覆盖 |
| 10 | 流月四化 | iztro horoscope('YYYY-M-15') | 以每月十五为基准 | 《紫微斗数全书》 | default | ✅ 与顺天一致 | 使用顺天GAN_SIHUA覆盖 |
| 11 | 流日四化 | iztro horoscope('YYYY-M-D') | 以当日为基准 | 《紫微斗数全书》 | default | ✅ 与顺天一致 | 使用顺天GAN_SIHUA覆盖 |
| 12 | 三方四正 | 顺天 get_sanfang_sizheng() | 本宫 + 对宫(idx+6) + 三合(idx+4, idx+8) | 《紫微斗数全书》 | N/A (顺天实现) | ✅ 白盒可验证 | 纯拓扑计算 |
| 13 | 真太阳时 | 顺天 corrected_hour_index() | 北京时间 + 经度差 + 均时差 | 传统规则 | N/A (iztro不支持) | ✅ 白盒可验证 | 存在但未自动调用 |
| 14 | 四化表 | 顺天 GAN_SIHUA | 注释声明为中州派/王亭之 | 中州派 | 可配置 (config.mutagens) | ✅ 白盒可验证 | 与iztro默认表一致 |
| 15 | 子时/晚子时 | iztro dayDivide配置 | forward: 晚子时算次日; current: 晚子时算当日 | 通行规则: 晚子时算次日 | default (dayDivide=forward) | ✅ 可配置 | 顺天默认使用index 12 |
| 16 | 闰月处理 | iztro fixLeap参数 | fixLeap=true: 前半月算上月，后半月算下月 | 通行规则 | default (fixLeap=true) | ✅ 可配置 | 顺天通过lunar_python负月表示 |
| 17 | 命主/身主 | iztro algorithm配置 | default: 命宫地支找命主; zhongzhou: 年支找命主 | 中州派用年支，通行派用命宫 | default (非中州) | ✅ 可配置 | 源码第212行有注释 |
| 18 | 流年岁前12神 | iztro star.getYearly12() | 安岁前12神规则 | 《紫微斗数全书》 | default | ✅ 白盒可验证 | 岁建、晦气、丧门等 |

### 2.2 汇总统计

```
总规则项: 18
白盒可验证: 16 (88.9%)
需验证传统: 2 (11.1%)

iztro默认算法: default (通行派)
iztro支持中州: True
四化表一致: ✅
```

---

## 三、Rule Profile 正式定义

### CURRENT_ZIWEI_RULE_PROFILE_V1

```
CORE = Iztro 2.6.0 (default算法)
├── Calendar/Input Policy
│   ├── yearDivide: 'normal' (正月初一分界)
│   ├── ageDivide: 'normal' (不考虑生日)
│   ├── dayDivide: 'forward' (晚子时算次日)
│   ├── horoscopeDivide: 'normal' (农历分界)
│   └── algorithm: 'default' (通行派)
│
├── Iztro Core (白盒依赖)
│   ├── byLunar()/bySolar() → 命宫/身宫/五行局/主星
│   └── horoscope(date) → 流年/流月/流日四化
│
├── Shuntian Adapter (确定性)
│   ├── GAN_SIHUA dict (中州派/王亭之声明)
│   ├── get_sanfang_sizheng() (三方四正)
│   └── palace_self_mutagen() (宫干自化)
│
└── Architecture Violations (待删除)
    ├── native_direction() ❌
    ├── SIHUA_EFFECT (INCREASE/DECREASE) ❌
    └── score_topic() ❌
```

---

## 四、关键结论

### 4.1 不能称为"中州派引擎"

虽然 `GAN_SIHUA` 四化表声明为中州派，但：

1. **iztro 默认算法是 `default`（通行派）**，不是 `zhongzhou`
2. **命主/身主计算使用通行派规则**（命宫地支），而非中州派（年支）
3. **四化表只是配置项之一**，不能代表整个引擎流派

### 4.2 更准确的描述

```
IZTRO_DEFAULT + ZHONGZHOU_SIHUA_ADAPTER
```

即：
- **排盘核心**: iztro 默认算法（通行派）
- **四化表**: 中州派/王亭之版本
- **其他适配**: 顺天实现的三方四正、宫干自化等

### 4.3 下一步建议

1. **决策点**: 是否将 `algorithm` 配置改为 `zhongzhou`？
   - 如果是，需验证命主/身主计算是否符合预期
   - 如果不是，需明确标注"四化表中州，排盘通行"

2. **待验证项**:
   - 大限起运年龄是否符合传统（2岁 vs 3岁）
   - 大限顺逆行规则是否与经典一致

3. **架构清理**:
   - 删除 `native_direction()`
   - 移除 `SIHUA_EFFECT` 语义映射
   - 将 `score_topic()` 移至决策层

---

## 五、Commit 信息

```
Commit: (待推送)
Branch: main
Files:
  - scripts/generate_provenance_matrix.py (新增)
  - docs/audit/ZIWEI_RULE_PROVENANCE_MATRIX.json (新增)
  - docs/audit/ZIWEI_RULE_PROVENANCE_MATRIX_REPORT.md (新增)
```

---

**审计者**: Hermes Agent  
**状态**: 等待仲裁裁决 `ZIWEI_RULE_PROVENANCE_MATRIX`
