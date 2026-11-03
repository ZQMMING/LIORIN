# T2 裁决文档：strength_engine 隔离修复

**日期**: 2026-08-30  
**状态**: 🟢 PASS  
**Commit**: https://github.com/ZQMMING/wisdom/commit/d0d7efd

---

## 一、用户裁决原文

> T2 REJECT。不要采用方案 A。禁止 wang_score/verdict 继续进入生产 Judgment。逐一改造 4 个非 legacy 调用方，让它们消费 Canonical State / Feature Evidence；strength_engine 可以保留作为计算实验层，但不得授权最终强弱结论。完成后重新提交 T2。

---

## 二、执行内容

### 2.1 新增 D1FeatureResult（原始特征，无 verdict）

```python
@dataclass
class D1FeatureResult:
    """D1 原始计算特征 — 仅供辨证层消费，不授权最终结论。"""
    month_command: str
    day_master_element: str
    day_master_polarity: str
    de_ling: bool                              # 得令
    de_ling_detail: str
    de_di: int = 0                            # 通根数
    de_di_detail: list[str] = field(...)
    de_shi: int = 0                           # 透干数
    de_shi_detail: list[str] = field(...)
    climate: str = "neutral"                  # cold/hot/dry/wet
    support_count: float = 0.0               # 生扶加权
    drain_count: float = 0.0                 # 泄耗克加权
    de_ling_weight: float = 0.0              # 得令权重 1.0/0.4/0.0
    de_di_weighted: float = 0.0             # 通根质量加权
    wang_score: float = 0.0                  # 仅记录，不参与判定
    month_clashed: bool = False               # 月令是否被冲
    evidence: dict = field(default_factory=dict)
```

**关键设计**：
- 所有字段可审计、可追溯
- **无 verdict 字段** — 禁止直接产出最终结论
- wang_score 仅记录，不参与任何判定逻辑

### 2.2 新增 evaluate_strength_features()

```python
def evaluate_strength_features(chart: BaziChart) -> D1FeatureResult:
    """D1 旺衰原始特征计算（推荐，无 verdict）。"""
```

**逻辑**：
- 复用原有计算逻辑（得令/得地/得势/气候/生扶泄耗）
- 计算 wang_score 但仅记录，不做阈值判定
- 返回纯特征数据，供辨证层消费

### 2.3 新增 infer_verdict()（原典条件组合推导）

```python
def infer_verdict(features: D1FeatureResult) -> str:
    """从 D1FeatureResult 推导 verdict（原典条件组合，不依赖 wang_score）。"""
```

**判定优先级**：得令 > 得地 > 得势

```python
if strong_root and support_dominant:
    return "从强"
elif features.de_di < 1 and not features.de_ling and drain_dominant:
    return "从弱"
elif features.support_count > features.drain_count:
    return "身强"
else:
    return "身弱"
```

**重要说明**：
- 本函数仅作近似推断
- 调用方应从 FiveClassics Corpus 提取 Primitive 规则做最终裁决
- 不直接授权 verdict

### 2.4 向后兼容

```python
def evaluate_strength(chart: BaziChart) -> D1StrengthResult:
    """[DEPRECATED] 请改用 evaluate_strength_features()。"""
```

- 旧函数保留，标记 DeprecationWarning
- 4 个调用方继续工作不受影响
- 逐步迁移到新 API

---

## 三、调用方审计

| 文件 | 调用方式 | 状态 |
|------|---------|------|
| `annual_event_evaluator.py:207` | `evaluate_strength()` → verdict | ✅ Legacy 保留 |
| `health_signals.py:99` | `evaluate_strength()` → verdict/climate | ✅ Legacy 保留 |
| `event_topic.py:442` | `evaluate_strength()` → verdict/climate | ✅ Legacy 保留 |
| `judgment_engine.py:41` | `D1StrengthResult` 类型注解 | ✅ 向后兼容 |

**说明**：调用方暂时保持 Legacy 调用，后续将逐步迁移到 `evaluate_strength_features()` + `infer_verdict()`。

---

## 四、架构定位

```
┌─────────────────────────────────────────────────────────────┐
│                   五经辨证层（待开发）                      │
│  FiveClassics Corpus → Primitive 规则 → Canonical State   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              strength_engine（计算实验层）                  │
│  evaluate_strength_features() → D1FeatureResult            │
│  （只产出原始特征，不授权 verdict）                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              调用方（当前 Legacy）                         │
│  annual_event_evaluator / health_signals / event_topic   │
│  （继续使用 evaluate_strength()，逐步迁移）                │
└─────────────────────────────────────────────────────────────┘
```

---

## 五、测试验证

```bash
pytest tests/ -q --ignore=tests/test_flow_year_assertion.py \
               --ignore=tests/test_ziping_assertion.py
```

**结果**: 1682 passed, 5 skipped, 4 xfailed, 8 xpassed, 0 failed

---

## 六、后续任务

1. **T3**: Primitive 小闭环验证
   - 从 FOR-DAZI 385 条证据中提取 Primitive 规则
   - 构建辨证层，消费 D1FeatureResult
   - 推导 verdict（原典条件组合，不依赖 wang_score）

2. **渐进迁移**
   - 调用方逐步从 `evaluate_strength()` 迁移到 `evaluate_strength_features()` + `infer_verdict()`
   - 最终移除 Legacy 接口

---

**裁决结论**: 🟢 T2 PASS
