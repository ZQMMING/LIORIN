# 架构裁决结果 — GPT 独立裁决

> **裁决来源**：基于 GitHub 仓库实际代码的逐项独立裁决
> **裁决时间**：2026-08-29
> **裁决依据**：ARCHITECTURE_DECISION.md + 仓库实际代码
> **裁决原则**：原典授权优先、确定性计算优先、不可逆边界优先、允许 UNRESOLVED

---

## 总裁决

**当前架构不能直接进入"实现 Canonical State → 接 Signal → 接 Assertion"的施工阶段。**

必须先做 **Calculation Integrity / Source Reconciliation**。否则只是把错误的计算结果换一个漂亮的架构包装。

---

## 五项正式裁决

### 裁决 1：strength_engine.py 的处理方式

**裁决结果：D — 新建独立 Canonical Calculation Engine，旧 strength_engine.py 隔离为 Legacy Reference**

**不批准原建议的 B（新建逐步替换）作为最终方案。**

**原因**：
当前 strength_engine.py 不是单纯"旧文件"，它已经把大量未经 Canonical 化的东西混在一起：
- `de_ling` / `de_di` / `de_shi`
- `support_count` / `drain_count`
- `de_ling_weight` / `de_di_weighted`
- `wang_score` / `WANG_SCORE_THRESHOLD`
- 调候
- 从强/从弱

代码自己明确写着 V2 加权评分制，最终身强判断依赖 `wang_score >= 2.0`。这与冻结原则"禁止评分 / 阈值 / 权重"直接冲突。

**正确结构**：
```
BaziChart → L1 Facts → Canonical Calculation → Canonical State
```

旧 `strength_engine.py` 改为：
- `LEGACY / REFERENCE ONLY`
- 不得再作为生产路径输入
- 旧评分结果可用于差异审计，不能作为新系统 ground truth

---

### 裁决 2：三套数据源谁权威？

**裁决结果：C — 先完整 Reconciliation，未经原典裁决不得指定唯一权威**

**当前状态：UNRESOLVED，暂不批准 A（以 bazi_l1_facts.py 为权威）**

**原因**：
`bazi_l1_facts.py` 自己已经明确声明：
```
IMPLEMENTATION_SOURCE = freddylamlc/bazi-patterns
canonical_source_status = NOT_CANONICAL_SOURCE
```

它自己也明确说 GitHub 开源库只是 implementation source，最终命理结论必须经过五部经典 Canonical Source Audit。

所以：
- `bazi_l1_facts.py` 可以成为工程上的候选数据源
- 但不能因为它是 P6.1-A 成果，就自动成为 Canonical Authority

三套表确实存在重复：
- `bazi_l1_facts.py`
- `reasoning/bazi_ten_gods.py`
- `reasoning/bazi_fixed_tables.py`

"一致"不能等于"已经完成权威认证"。

**必须先做**：
```
Implementation Source
    ↓
三套表逐项 diff
    ↓
差异分类
    ↓
原典验证
    ↓
Canonical Registry
    ↓
唯一生产来源
```

最终应该是：
```
Canonical Source Registry
    ↓
Generated / frozen deterministic tables
    ↓
所有 Engine import
```

而不是 `bazi_l1_facts.py` 直接被宣布为 Canonical。

---

### 裁决 3：Canonical State 放哪里？

**裁决结果：A — 批准，在 canonical/ 目录下新建**

**应该**：
```
src/tongshu/canonical/
    canonical_state.py
    canonical_state_engine.py
    canonical_validator.py
    composer.py
```

**不应该**把状态塞进 BaziChart。

**原因**：
目前 BaziChart 已经承担大量不同职责：
- 四柱、大运
- 配偶星、配偶星强度
- 冲害、合、三合、三刑、空亡
- 五行平衡、十神
- `spouse_star_strength` 本身又是一个评分阈值分类

继续把 Canonical State 塞进去，只会让 Calculation / State / Derived Interpretation 再次混在一起。

**Canonical State 应该是独立、封闭、可验证的状态对象**：
```
CanonicalState
├── facts
├── relationships
├── wangshuai
├── qiangruo
├── root_state
├── dangzhong
├── seasonal_state
├── special_pattern
├── qualifiers
└── unresolved_reasons
```

**重点**：`UNRESOLVED` 是合法状态，不是异常。

---

### 裁决 4：三套 Signal Engine 怎么处理？

**裁决结果：C — 先职责审计，再收敛为单一生产 Pipeline**

**最终目标不是"三套永久共存"**。

**原因**：
三套东西实际上不是完全相同的东西：
- `signal_engine.py` 是 Universal Signal / Rule Matching 路径
- `p3_signal_engine.py` 明确是 EngineEvidence → Rule → SemanticSignal，强调"一个 Rule 的 N 个 semantic atoms 必须产生 N 个 signals，不得压缩"
- `semantic_signal.py` 本身是数据契约，不应该被理解成第三套"计算引擎"

现在直接合并，会破坏已经形成的 P3/P4 边界。

**正确理解**：
```
Calculation
    ↓
Canonical State
    ↓
Semantic Signal Extraction
    ↓
SemanticSignal[]
    ↓
Context
    ↓
Assertion
```

而不是三个 Signal Engine 各自重新计算命理。

**尤其必须禁止**：
```
Signal Engine → 重新算强弱
```

Signal 只能：从 Canonical State 提取语义，不创造 Canonical State。

---

### 裁决 5：Legacy 怎么处理？

**裁决结果：A — Deprecated → 隔离 → 迁移 → 删除（比原建议更严格）**

**不批准**：新旧系统长期并行生产。

**原因**：
如果 Legacy + New 同时产生生产结果，那么最终一定会重新出现"哪个结果是真的？"这实际上又回到了"比较 / 投票"错误架构。

**迁移必须遵循**：
```
Legacy
    ↓
仅用于 Regression / Differential Audit
    ↓
Canonical
    ↓
Production
```

Legacy 不能参与：授权、投票、融合、fallback。

**特别是**：
```
old strength_score
绝不能：
Canonical State 不确定 → 调用旧评分 → 得到强/弱
```

这种 fallback 必须禁止。

---

## 五项裁决汇总表

| 决策点 | 裁决结果 | 状态 |
|--------|----------|------|
| 1. strength_engine.py | D：全新 Canonical Calculation，旧引擎仅 Legacy Reference | ✅ |
| 2. 数据源 | C：先 Reconciliation，暂不授权任何一套为 Canonical | ⚠️ UNRESOLVED |
| 3. Canonical State 位置 | A：canonical_state + canonical_state_engine | ✅ |
| 4. Signal Engine | C：先职责审计，再收敛为单一生产 Pipeline | ✅ |
| 5. Legacy 处理 | A：Deprecated → 隔离 → 迁移 → 删除 | ✅ |

---

## 更严重的发现：不只是 strength_engine.py 有评分问题

**bazi_engine.py 自己也存在这种结构**：

- `spouse_star`
- `spouse_star_strength`
- `five_element_balance`
- `five_element_imbalance`

其中 `spouse_star_strength` 直接计算：
```
score
    ↓
>= 1.0 → strong
>= 0.3 → weak
else  → rootless
```

这是典型的：**数值评分 → 阈值 → 语义状态**

而项目冻结原则明确禁止这种模式。

所以如果只修 `strength_engine.py` 不够，否则会变成：
```
strength_engine ❌
bazi_engine    ❌
       ↓
canonical_state
```

Canonical State 仍然被污染。

---

## 更高一级的总裁决

**当前不能直接进入 P6.6 / 断言生产。**

必须先建立：**P6-CALC INTEGRITY**

完整通过后才能：
```
Calculation → Canonical State → Signal → Assertion
```

这是因为 AUDIT_GUIDE.md 自己已经把 Calculation Audit 放在高优先级，而且明确要求不能把 FROZEN 当成 PROVEN CORRECT。

---

## 建议立刻执行的顺序

### P0 — Calculation Source Reconciliation

逐项审：
- 四柱、日主、十神
- 十二长生、藏干
- 冲、合、刑、害、三合、三刑、空亡

建立：`SOURCE_DIFF_REPORT`

### P0 — 删除所有隐性评分进入 Canonical 的路径

全仓扫描：
- `score` / `weight` / `threshold`
- `strong` / `weak` / `strength`
- `balance` / `imbalance`

逐项判断：
- 这是 L1 Fact？
- Relationship？
- 还是未经授权的 Semantic Judgment？

不能只查 `strength_engine.py`。

### P0 — Canonical State 最小闭环

先不要一次写一大堆状态。先做到：
```
BaziChart → L1 Facts → Relationships → CanonicalState
```

并且：
```
无法确定 → UNRESOLVED
```

绝不 fallback 到旧算法。

### P1 — Signal 收敛

确认：
```
CanonicalState → Signal Extraction → SemanticSignal
```

Signal 不再重新计算命理事实。

### P1 — Calculation Golden Dataset

1983 这个案例只能作为一个 reference，不能叫"Calculation Correctness 已证明"。

至少要覆盖：
- 阴阳日主
- 四季
- 四土月
- 节气边界
- 子初
- 真太阳时边界
- 农历/公历
- 藏干完整组合
- 合冲刑害
- 多种日主
- 强弱存在争议的案例
- 应该得到 UNRESOLVED 的案例

---

## 最终一句话

这次真正的裁决不是"选 B 还是 A？"，而是：

> **先把"计算事实"和"命理判断"彻底拆开；未经原典授权的评分、权重、阈值全部不能进入 Canonical State；无法确定就 UNRESOLVED。**

这才和之前定下的"算 → 辨 → 解、互补不比较、反方向=算法错误"是一致的。

---

*本裁决基于 GitHub 仓库实际代码逐项独立核对，不是根据 agent 的汇报判断。*
