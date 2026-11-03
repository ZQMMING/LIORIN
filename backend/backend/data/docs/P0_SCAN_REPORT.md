# P0 扫描报告 — 隐性评分进入 Canonical 的路径

> **扫描时间**：2026-08-29
> **扫描范围**：`src/tongshu/engines/` 核心计算引擎
> **扫描依据**：架构裁决结果（ARCHITECTURE_DECISION_RESULT.md）
> **扫描目标**：找出所有"数值评分 → 阈值 → 语义状态"的隐性路径

---

## 扫描总结

| 引擎文件 | 评分问题数 | 严重程度 |
|----------|-----------|----------|
| `strength_engine.py` | 完整评分系统 | 🔴 高 |
| `bazi_engine.py` | 2 处评分/阈值 | 🔴 高 |
| `blind_bazi_engine.py` | 待详细扫描 | ⚠️ 中 |
| `judgment_engine.py` | 待详细扫描 | ⚠️ 中 |
| `annual_event_evaluator.py` | 待详细扫描 | ⚠️ 中 |

**全仓扫描**：92 个文件包含 score/weight/threshold/strong/weak/strength/balance/imbalance 等关键词。

---

## 已确认的评分问题

### 🔴 问题 1：`strength_engine.py` — 完整加权评分系统

**位置**：`src/tongshu/engines/strength_engine.py`

**问题描述**：
整个引擎基于加权评分制，最终身强判断依赖 `wang_score >= 2.0`。

**具体评分/阈值/权重代码**：

| 代码 | 行号 | 类型 | 问题 |
|------|------|------|------|
| `_ROOT_QUALITY = {"main": 1.0, "middle": 0.5, "residual": 0.3}` | 46 | 权重 | 通根质量权重 |
| `_PILLAR_YIN_FACTOR = 0.6` | 50 | 系数 | 偏印生扶打折系数 |
| `_CLASH_ACTIVATE_FACTOR = 1.2` | 55 | 系数 | 地支相冲激发藏干力量系数 |
| `_CLIMATE_FACTOR` | 59-64 | 系数 | 气候修正系数（调候→强弱） |
| `_WANG_SCORE_THRESHOLD = 2.0` | 69 | 阈值 | 旺衰评分阈值 |
| `_STRONG_STAGES = {"临官", "帝旺"}` | 42 | 限定 | 得令判定（这个可能是合理的 L1 Fact） |

**输出字段**：
- `de_ling` / `de_di` / `de_shi`
- `support_count` / `drain_count`
- `de_ling_weight` / `de_di_weighted`
- `wang_score`
- `verdict`: 身强 / 身弱 / 从强 / 从弱

**违反原则**：
- ❌ 禁止评分 / 阈值 / 权重
- ❌ 禁止调候→强弱
- ❌ 禁止五行计分→强弱

**裁决结果**：D — 新建独立 Canonical Calculation Engine，旧引擎隔离为 Legacy Reference。

---

### 🔴 问题 2：`bazi_engine.py` — `calc_spouse_star_strength`

**位置**：`src/tongshu/engines/bazi_engine.py` 第 422-434 行

**问题代码**：
```python
def calc_spouse_star_strength(chart: BaziChart) -> str:
    """配偶星强度档位: 'strong' / 'weak' / 'rootless'."""
    ss = chart.spouse_star
    if chart.gender == "male":
        score = ss.get("正财", 0) + ss.get("偏财", 0) + ss.get("branch_root", 0)
    else:
        score = ss.get("正官", 0) + ss.get("七杀", 0) + ss.get("branch_root", 0)

    if score >= 1.0:
        return "strong"
    if score >= 0.3:
        return "weak"
    return "rootless"
```

**问题分析**：
1. `score`：数值评分（正财+偏财+branch_root 简单相加）
2. `>= 1.0`：阈值 → strong
3. `>= 0.3`：阈值 → weak
4. `else`：rootless
5. 这是典型的"数值评分 → 阈值 → 语义状态"模式

**违反原则**：
- ❌ 禁止评分 / 阈值
- ❌ 未经授权的 Semantic Judgment（strong/weak/rootless 没有原典授权的量化标准）

**BaziChart 字段**：
- `spouse_star_strength: str = "weak"`（第 218 行）

---

### 🔴 问题 3：`bazi_engine.py` — `calc_five_element_balance`

**位置**：`src/tongshu/engines/bazi_engine.py` 第 551-561 行

**问题代码**：
```python
def calc_five_element_balance(chart: BaziChart):
    """五行分布(归一化) + 失衡标记 (max > 0.40 或 min < 0.05)."""
    counts = {"WOOD": 0, "FIRE": 0, "EARTH": 0, "METAL": 0, "WATER": 0}
    for s in chart.four_stems():
        counts[STEM_ELEMENT[s]] += 1
    for b in chart.four_branches():
        counts[_branch_element(b)] += 1
    total = sum(counts.values()) or 1
    balance = {k: v / total for k, v in counts.items()}
    imbalance = (max(balance.values()) > 0.40) or (min(balance.values()) < 0.05)
    return balance, imbalance
```

**问题分析**：
1. `counts`：五行计数（这是 L1 Fact，可以保留）
2. `balance`：归一化比例（计算结果，可能可以保留作为 Fact）
3. `imbalance`：使用阈值 `> 0.40` 或 `< 0.05` 判定失衡（这是未经授权的 Semantic Judgment）
4. 只统计天干+地支本气，不统计藏干，计数本身不完整

**违反原则**：
- ❌ 禁止阈值→语义状态（imbalance 标记没有原典授权）
- ⚠️ 五行计数不完整（只统计本气，不统计藏干）

**BaziChart 字段**：
- `five_element_balance: dict`（第 244 行）
- `five_element_imbalance: bool = False`（第 246 行）

---

## 待详细扫描的文件

以下文件包含相关关键词，需要进一步详细扫描：

| 文件 | 行数 | 初步判断 |
|------|------|----------|
| `blind_bazi_engine.py` | 580 | 盲派八字引擎，可能有评分 |
| `blind_yingqi.py` | 391 | 盲派运气，可能有评分 |
| `judgment_engine.py` | 467 | 判断引擎，可能有评分 |
| `annual_event_evaluator.py` | 614 | 年度事件评估器，可能有评分 |
| `tiaohou_loader.py` | 87 | 调候加载器，可能影响强弱 |
| `ziwei_engine.py` | 933 | 紫微引擎（当前非重点，但可能有评分） |

---

## 分类标准

扫描时按以下标准分类每个发现：

### ✅ L1 Fact（可以保留）
- 四柱、日主、藏干、十神
- 十二长生状态
- 冲、合、刑、害、三合、三刑、空亡的存在性
- 五行计数（原始计数，不归一化、不判定失衡）

### ⚠️ Relationship（需要原典授权）
- 通根（藏干匹配日主）
- 得令/失令（月令与日主关系）
- 生扶/克泄耗的存在性
- 合化、冲解等组合关系

### ❌ Semantic Judgment（必须移除或隔离）
- 身强/身弱（未经原典授权的评分推导）
- strong/weak/rootless（数值评分→阈值→语义状态）
- imbalance（阈值判定失衡）
- 任何 score/weight/threshold 驱动的语义状态
- 调候→强弱
- 五行计分→强弱

---

## 下一步行动

### P0-1：完成全引擎详细扫描
- [ ] 详细扫描 `blind_bazi_engine.py`
- [ ] 详细扫描 `blind_yingqi.py`
- [ ] 详细扫描 `judgment_engine.py`
- [ ] 详细扫描 `annual_event_evaluator.py`
- [ ] 扫描 `reasoning/` 目录中的评分路径
- [ ] 扫描 `signal/` 目录中的评分路径

### P0-2：建立 Canonical State 最小闭环
- [ ] 在 `canonical/` 目录下新建 `canonical_state.py`
- [ ] 定义封闭枚举状态（wangshuai/qiangruo/root_state/dangzhong 等）
- [ ] 新建 `canonical_state_engine.py`
- [ ] 实现从 BaziChart → L1 Facts → Relationships → CanonicalState
- [ ] 无法确定 → UNRESOLVED，绝不 fallback 到旧算法

### P0-3：隔离旧评分引擎
- [ ] `strength_engine.py` 标记为 Legacy Reference
- [ ] `calc_spouse_star_strength` 标记为 Legacy
- [ ] `calc_five_element_balance` 的 imbalance 部分标记为 Legacy
- [ ] 确保新 Canonical State 引擎不 import 旧评分函数

---

## 重要提醒

1. **不能只修 strength_engine.py**：bazi_engine.py 中也有评分问题，必须一并处理。
2. **不能把旧评分结果当 ground truth**：旧评分结果只能用于差异审计，不能作为新系统的验证标准。
3. **UNRESOLVED 是合法状态**：新引擎中无法确定的状态必须标记为 UNRESOLVED，不能 fallback 到旧算法。
4. **全仓扫描范围**：92 个文件包含相关关键词，不能只扫描 engines/ 目录。

---

*本报告是 P0 扫描的初步结果，后续将补充详细扫描发现。*
