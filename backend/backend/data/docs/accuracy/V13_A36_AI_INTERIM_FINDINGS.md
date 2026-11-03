# V1.3 A3.6-A AI Expert Simulation Pilot — Interim Findings

**日期**: 2026-08-22
**状态**: ⏳ IN PROGRESS (3/40 cases completed)
**版本**: A3.6-A-Interim-v1

---

## 一、核心发现

### 1.1 Yi Engine 输出为占位符

**问题**: Yi Engine 的 `relational_interpretation` 函数返回的是占位输出，不是完整的解释。

**代码位置**: `src/tongshu/engines/yi/relational_interpretation.py`

**当前输出**:
```python
return InterpretationOutput(
    state=f"{input.hexagram_symbol.name}卦，体用关系：{input.hexagram_symbol.ti_yong_relation}",
    opportunity="需结合具体人生领域分析",
    attention="参考爻辞与经典注解",
    suggestion="咨询专业易学顾问",
    source_references=[
        f"周易·{input.hexagram_symbol.name}",
        f"说卦传",
        f"元堂：{input.line_symbol.yuantang}",
    ],
    confidence=0.7,
)
```

**代码注释**: "返回占位输出，完整实现需要接入 LLM"

### 1.2 Rater 评估准确

三个 Rater 都正确识别出 Yi Engine 输出是占位符，给出低分。

**示例评分 (SAMPLE_001, Rater A: deepseek-v4-pro)**:

| Dimension | Score | Status | Reason |
|-----------|-------|--------|--------|
| Temporal Alignment | 0 | FAIL | 输出中完全没有提及任何时间窗口、大运流年或时间对应关系 |
| Event Correspondence | 0 | FAIL | 没有任何具体事件的对应，仅以"需结合具体人生领域分析"作为占位符 |
| Relational Coherence | 1 | WEAK | 仅提及"体生用（泄）"这一基础状态，但缺乏对关系链的展开 |
| Evidence Support | 0 | FAIL | 除了列出卦名和元堂外，核心判断缺乏具体的爻辞、卦象或五行生克证据支持 |
| Directionality | 0 | FAIL | 没有指出任何明确的发展方向、吉凶趋势或行动建议 |
| Specificity | 0 | FAIL | 内容高度泛化，完全属于通用套话和系统占位符 |
| Overall Interpretability | 0 | FAIL | 输出退化为模板提示，缺乏实质性的命理或易学分析 |

**Total**: 1/21

**Overall Assessment**: "系统输出的关系式解释严重缺失实质性内容，完全退化为通用模板和占位符。除了提及卦名和基础的'体生用'状态外，没有任何具体的分析、事件对应或时间窗口。该输出无法提供任何有效的解释或指导，属于生成失败或严重降级。"

---

## 二、当前评分结果 (3/40 cases)

| Case | Rater A | Rater B | Rater C |
|------|---------|---------|---------|
| SAMPLE_001 | 0/21 | 0/21 | 0/21 |
| SAMPLE_002 | 1/21 | 0/21 | 1/21 |
| SAMPLE_003 | 1/21 | 1/21 | (pending) |

**平均分**: ~0.7/21 (3.3%)

---

## 三、问题诊断

### 3.1 架构层面

```text
Heluo Engine (计算层)
    ↓
卦象结构 (先天卦/后天卦/元堂/天地数)
    ↓
Yi Engine (解释层) ← 问题在这里
    ↓
占位输出 (不是完整解释)
    ↓
Rater 评分 (0-1/21)
```

### 3.2 根因

1. **Yi Engine 未接入 LLM**: `relational_interpretation` 函数是硬编码的占位输出
2. **缺少 STATE/OPPORTUNITY/RISK/REMEDIATION/ACTION 结构**: 只有 STATE 和泛化的 OPPORTUNITY/ATTENTION/SUGGESTION
3. **没有时间维度**: 没有流日/流月/流年的状态映射
4. **没有事件对应**: 没有与具体人生领域的关联

### 3.3 这不是评分问题

Rater 的评分是准确的。问题在于系统本身没有生成完整的解释。

---

## 四、下一步选项

### 选项 1: 继续评分，记录现状

```text
让评分进程完成 40 cases
生成最终报告
记录: AI-Simulation Score = 0.7/21 (3.3%)
标记: Yi Engine 需要接入 LLM
```

### 选项 2: 暂停评分，先修复 Yi Engine

```text
停止评分进程
接入 LLM 到 Yi Engine
生成完整解释
重新评分
```

### 选项 3: 调整评估目标

```text
当前评估的是"完整解释的质量"
但系统只能输出"卦象结构"
调整 Rubric 评估"卦象结构的准确性"
而不是"解释的质量"
```

---

## 五、当前冻结状态

```text
V1.2 Architecture       FROZEN
A3.2 Event Direction    DIAGNOSTIC ONLY (Micro-F1 = 0.567)
O4 Expert Oracle        NOT QUALIFIED
AI-Simulation           ⏳ IN PROGRESS (发现 Yi Engine 占位符问题)
Formal Accuracy         NOT CERTIFIED
```

---

## 六、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│           A3.6-A AI EXPERT SIMULATION PILOT                    │
├─────────────────────────────────────────────────────────────┤
│  Status:  ⏳ IN PROGRESS (3/40 cases)                        │
│                                                              │
│  Key Finding:                                                │
│    ❌ Yi Engine 输出为占位符，不是完整解释                    │
│    ❌ 缺少 STATE/OPPORTUNITY/RISK/REMEDIATION/ACTION 结构    │
│    ❌ 没有时间维度和事件对应                                  │
│    ✅ Rater 评估准确，正确识别问题                           │
│                                                              │
│  Current Scores:                                             │
│    Average: 0.7/21 (3.3%)                                    │
│    Range: 0-1/21                                             │
│                                                              │
│  Root Cause:                                                 │
│    Yi Engine relational_interpretation() 是硬编码占位输出    │
│    需要接入 LLM 才能生成完整解释                             │
│                                                              │
│  Options:                                                    │
│    1. 继续评分，记录现状                                     │
│    2. 暂停评分，先修复 Yi Engine                             │
│    3. 调整评估目标                                           │
│                                                              │
│  Process: proc_490fb2614668 (running)                        │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.6-A-Interim-v1
