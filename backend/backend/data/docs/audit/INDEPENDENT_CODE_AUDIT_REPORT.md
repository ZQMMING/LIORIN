# 🔴 P0 BLOCKER: 独立代码审计报告

**审计日期**: 2026-08-31  
**审计者**: Claude (独立审计)  
**状态**: 🚨 BLOCKING - 必须立即处理

---

## 总裁决

**项目进入架构治理阶段，暂停所有新功能开发。**

当前最大风险：
> **Legacy Strength Engine 仍在生产链运行，与五经辨证架构并行，形成双轨系统。**

---

## P0 Blocker（必须立即修复）

### 问题1: strength_engine.py 生产调用未隔离

**证据**:
```
src/tongshu/annual_event_evaluator.py:207  ← 生产调用
src/tongshu/health_signals.py:99           ← 生产调用
src/tongshu/judgment_engine.py:41          ← 生产调用
```

**声明 vs 现实**:
| 文档声明 | 实际状态 |
|---------|---------|
| `LEGACY / DEPRECATED_IN_PROGRESS` | ❌ 仍在生产调用链 |
| `替代方案：CanonicalState + 五经辨证` | ⚠️ 旧引擎未断开 |
| `禁止 wang_score / root_score` | ❌ 代码仍在使用 |

**核心冲突**:
```python
# strength_engine.py:207
_WANG_SCORE_THRESHOLD = 2.0
if wang_score >= 2.0:
    verdict = "身强"
else:
    verdict = "身弱"
```

这直接违反治理原则：
> "禁止工程阈值定义命理概念"

---

### 问题2: 工程权重无五经授权

**发现的权重配置**:
| 权重项 | 值 | 授权来源 |
|--------|-----|---------|
| 本气 | 1.0 | ❌ 无原典依据 |
| 中气 | 0.5 | ❌ 无原典依据 |
| 余气 | 0.3 | ❌ 无原典依据 |
| 偏印 | 0.6 | ❌ 无原典依据 |
| 冲 | 1.2 | ❌ 无原典依据 |
| 月令 | 1.5 | ❌ 无原典依据 |
| 透干 | 0.8 | ❌ 无原典依据 |
| 阈值 | 2.0 | ❌ 无原典依据 |

**结论**:
- 这些权重最多是 RESEARCH/EXPERIMENTAL
- 不能是 CANONICAL
- 不能进入生产判断链路

---

## P1 Critical（必须审计后修复）

### 问题3: Governance Contract > Runtime Enforcement

**现状**:
- ✅ 文档已明确 Evidence ≠ Condition ≠ Judgment ≠ Conclusion
- ✅ 明确规定不投票、不计分、不用工程阈值
- ❌ 生产代码仍存在 Feature → weighted score → threshold → verdict

**风险**: 
- 新开发的五经辨证逻辑可能永远不会被执行
- 生产系统仍然走旧 wang_score 路径

---

### 问题4: Condition Evaluator 方向正确但不能证明语义成立

**正确部分**:
- Canonical State → Condition Evaluator → TRUE/FALSE/UNRESOLVED 架构正确
- Mapper 不会因命中就直接授权结论

**局限**:
- Evaluator 只能证明"条件执行机制成立"
- 不能证明"条件本身命理语义成立"
- 例如：有根 ≠ 根强 ≠ 身强（这是三层问题）

---

## P2 Important（建议改进）

### 问题5: FROZEN 状态含义模糊

**当前定义**:
```
P6.1 Canonical State FROZEN
P6.2 Assertion Admission FROZEN
P6.3 Cross-Domain FROZEN
P6.4 Asset Protocol FROZEN
```

**问题**:
- FROZEN ≠ PROVEN CORRECT（仓库自己承认）
- 但容易误解为"FROZEN = 已经可靠"
- 建议明确状态机：DESIGNED → IMPLEMENTED → TESTED → AUDITED → PROVEN → PRODUCTION_AUTHORIZED

---

### 问题6: 自写自审风险

**当前模式**:
```
Hermes: 设计 → 写代码 → 写测试 → 写报告 → 宣布PASS
```

**风险**:
- 语义模型错误最难自测发现
- 命理项目特殊性（非纯工程问题）
- 需要 Implementer ≠ Auditor

---

## 审计发现汇总

| ID | 域 | 发现 | 严重度 | 状态 | 建议操作 |
|----|-----|------|--------|------|---------|
| A01 | Runtime | strength_engine生产调用未断开 | P0 BLOCKER | 🔴 | 立即隔离 |
| A02 | Canonical | 工程权重无五经授权 | P0 BLOCKER | 🔴 | 降级为RESEARCH |
| A03 | Governance | Contract与Runtime不一致 | P1 CRITICAL | 🟡 | 统一执行 |
| A04 | Validation | Evaluator不能证明语义 | P2 IMPORTANT | ⚪ | 补充审计 |
| A05 | Architecture | FROZEN状态含义模糊 | P2 IMPORTANT | ⚪ | 重新定义 |
| A06 | Process | 自写自审风险 | P1 CRITICAL | 🟡 | 隔离角色 |

---

## 立即停止清单（STOP）

❌ 暂停扩充五经断言数量  
❌ 暂停Composite Judgment开发  
❌ 暂停大规模Batch Production  
❌ 暂停StrengthEvaluator新公式  
❌ 暂停修改wang_score  

---

## 必须执行清单（START）

✅ STEP 0: 冻结当前状态  
✅ STEP 1: Claude独立12域全审  
✅ STEP 2: Hermes裁定KEEP/FIX/REMOVE/RESEARCH/STALE  
✅ STEP 3: 派发P0任务单  
✅ STEP 4: OpenCode实现修复  
✅ STEP 5: Claude复审  
✅ STEP 6: 三层验证  
✅ STEP 7: BASELINE V1.4 FREEZE  

---

## 流程变更确认

**新治理模式**:
```
用户
  │
  ▼
Hermes（总调度/任务拆解）
  │
┌─┴──┐
▼    ▼
Claude  OpenCode
审计   实现
  │      │
  └──┬───┘
     ▼
    GPT
  架构裁决
     │
     ▼
  Hermes
整改合并
```

**铁律**:
- Hermes不得自己宣布PASS
- 至少需要：Implementer ≠ Auditor
- 任何 PASS/FROZEN/PRODUCTION_READY 必须经过独立审计

---

## 下一步

**等待GPT裁决**:
1. 是否接受独立审计结论？
2. 是否立即暂停新功能开发？
3. 是否启动STEP 0冻结+STEP 1 Claude审计？

---

**审计完成时间**: 2026-08-31  
**审计状态**: 🚨 P0 BLOCKER 确认，建议立即执行独立审计流程
