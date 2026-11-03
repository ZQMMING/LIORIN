# T2 重构计划：strength_engine 隔离 + 调用方改造

**目标**: 禁止 wang_score/verdict 进入生产 Judgment，改用 CanonicalState / Feature Evidence

---

## 一、设计原则

1. **strength_engine 降级为"计算实验层"**
   - 只计算原始特征（de_ling/de_di/de_shi/support_count/drain_count/climate）
   - 不输出 verdict（最终强弱结论）
   - 保留 wang_score 作为历史记录，不参与判定

2. **调用方消费 CanonicalState / Feature Evidence**
   - 从 CanonicalState 提取 L1 事实（天干/地支/五行/十神）
   - 从 FiveClassics Corpus 提取 Primitive 规则
   - 组合推导 verdict（如有原典授权）

3. **verdict 授权链**
   ```
   BaziChart → CanonicalState → Evidence → Primitive → verdict (如有原典授权)
                                      ↓
                                UNRESOLVED (如无授权)
   ```

---

## 二、改造清单

### 2.1 strength_engine.py 改造

**当前**: 返回 D1StrengthResult（含 verdict）  
**目标**: 返回 D1FeatureResult（仅原始特征）

```python
@dataclass
class D1FeatureResult:
    """D1 原始计算特征 — 仅供辨证层消费，不授权最终结论。"""
    month_command: str
    day_master_element: str
    day_master_polarity: str
    
    # 得令/得地/得势
    de_ling: bool
    de_ling_weight: float
    de_di: int
    de_di_weighted: float
    de_shi: int
    
    # 生扶泄耗
    support_count: float
    drain_count: float
    
    # 气候
    climate: str
    
    # 其他
    month_clashed: bool
    wang_score: float  # 仅记录，不用于判定

# 移除 verdict 相关字段和方法
```

### 2.2 调用方改造

#### annual_event_evaluator.py:207
**当前**:
```python
strength = evaluate_strength(chart)
verdict = strength.verdict
return dm, fourb, chart, verdict
```

**目标**:
```python
features = evaluate_strength_features(chart)  # 返回 D1FeatureResult
canonical = CanonicalStateProducer().produce(chart)
# 从 canonical 和 rules 推导 verdict（如有原典授权）
verdict = derive_verdict_from_evidence(features, canonical)
return dm, fourb, chart, verdict
```

#### health_signals.py:99
**当前**:
```python
d1: D1StrengthResult = evaluate_strength(chart)
# 使用 d1.verdict, d1.support_count, d1.drain_count
```

**目标**:
```python
features = evaluate_strength_features(chart)
canonical = CanonicalStateProducer().produce(chart)
# 从 features 和 canonical 推导健康信号
# 不再依赖 verdict，而是基于证据组合
```

#### event_topic.py:442
**当前**:
```python
d1 = evaluate_strength(chart)
# 使用 d1.verdict, d1.climate, d1.support_count
```

**目标**: 同 health_signals.py

---

## 三、实施步骤

1. 创建 D1FeatureResult dataclass（无 verdict）
2. 修改 evaluate_strength 返回 D1FeatureResult
3. 创建 derive_verdict_from_evidence() 函数（从规则推导）
4. 改造 4 个调用方
5. 更新测试

---

## 四、风险控制

- 保持 D1StrengthResult 向后兼容（deprecated warning）
- 渐进式迁移，不破坏现有测试
- 所有变更在同一 commit 提交
