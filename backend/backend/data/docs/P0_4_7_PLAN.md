# P0-4.7 工作计划：五经 Semantic Feature Ontology 审计

**目标**: 建立"原典语言"与"工程 Feature"的语义桥梁，逐条判断映射可行性

---

## 一、背景

P0-4.6 发现：Feature 映射不明确是当前主要瓶颈。

**核心问题**：
- "得二三人之气" ≠ support_count > drain_count
- "畏土之埋" ≠ wu_element_wang < threshold
- "火炽" ≠ fire_score > X

**关键洞察**：
> 古人描述的到底是什么状态？然后才问：这个状态能否由 Canonical Calculation 精确计算？

---

## 二、语义桥梁框架

### Phase 1: 原典语言分析
1. 提取原典中的描述性语言
2. 分析语言的实际含义
3. 识别是否包含数量阈值/程度标准

### Phase 2: 工程 Feature 映射
1. 当前 Feature 是什么？
2. Feature 是否与原典语义对齐？
3. 差异在哪里？

### Phase 3: 三种状态分类
| 状态 | 定义 | 示例 |
|------|------|------|
| CANONICAL_FEATURE | 已有确定性计算可以表达 | de_ling（得令） |
| DERIVABLE_FEATURE | 需要增加确定性计算，但定义可证明 | 二三人之气 → 需要新计算 |
| SEMANTIC_ONLY | 目前只能保留经典语义，不能硬算 | 畏土之埋（程度未明确） |

---

## 三、审计清单

对 6 条 SEMANTIC_ONLY 逐条分析：

### graph_001: 生克制化
**原典语言**
> "生克制化，须制中有生，生中有制。太过者宜损之，不及者宜益之。"

**当前 Feature 映射**
- support_count, drain_count
- wang_score, shang_score

**问题分析**
- "生"对应什么 Feature？support_count？
- "制"对应什么 Feature？drain_count？
- "太过"的阈值是多少？
- "不及"的阈值是多少？

**分类**
- 待审计...

---

### graph_002: 一行得二三人之气
**原典语言**
> "一行得二三人之气，则党众而专，须从其势。"

**当前 Feature 映射**
- support_count > drain_count（推论）

**问题分析**
- "二三人"是否明确数量阈值？
- 是约数（多数）还是确数（≥2）？
- "党众而专"的判定标准？

**分类**
- 待审计...

---

### graph_004: 辛金软弱
**原典语言**
> "辛金软弱，温润而清，畏土之埋，乐水之盈。"

**当前 Feature 映射**
- wu_element_wang（土旺程度）
- shui_element_wang（水旺程度）

**问题分析**
- "畏土之埋"的"埋"是程度概念还是存在概念？
- "乐水之盈"的"盈"是多少？
- 原典是否有明确阈值？

**分类**
- 待审计...

---

### graph_005: 戊己愁逢甲乙
**原典语言**
> "戊己愁逢甲乙，干头须要庚辛。"

**当前 Feature 映射**
- jia_yi_transparent（甲乙透干）
- geng_xin_transparent（庚辛透干）

**问题分析**
- "愁逢"是条件还是结果？
- "须要庚辛"是否明确？
- 原典是否有其他相关论述？

**分类**
- 待审计...

---

### graph_008: 火炽乘龙
**原典语言**
> "火炽乘龙，水荡骑虎。"

**当前 Feature 映射**
- huo_element_wang（火旺）
- shui_element_wang（水旺）
- chen_earth_present（辰土存在）
- yin_wood_present（寅木存在）

**问题分析**
- "火炽"的程度标准？
- "水荡"的程度标准？
- "乘龙""骑虎"是否明确条件？

**分类**
- 待审计...

---

### graph_009: 戊土固重
**原典语言**
> "戊土固重，既中且正。静翕动辟，万物司命。水润物生，火燥物病。"

**当前 Feature 映射**
- wu_element_heavy（土重）
- shui_moistening（水润）
- huo_drying（火燥）

**问题分析**
- "固重"的程度标准？
- "水润"的程度标准？
- "火燥"的程度标准？

**分类**
- 待审计...

---

## 四、输出物

1. `docs/P0_4_7_SEMANTIC_FEATURE_ONTOLOGY.md` - Ontology 定义
2. `data/p0_4_7_feature_audit.json` - 逐条审计结果
3. `docs/P0_4_7_VERIFICATION_REPORT.md` - 验证报告

---

## 五、禁止事项

❌ 不得为了通过而强行映射  
❌ 不得假设"二三人"=支持数≥2  
❌ 不得假设"火炽"=火元素分数>X  
❌ 不得进入 Composite Judgment  
❌ 不得扩大 D1FeatureResult

---

## 六、成功标准

✅ 每条原典都有明确的语言分析  
✅ 每条原典都有准确的 Feature 映射评估  
✅ 分类准确：CANONICAL_FEATURE / DERIVABLE_FEATURE / SEMANTIC_ONLY  
✅ UNKNOWN 类型保持保守

---

**开始执行**
