# 顺天项目 Agent 权限边界协议

> 制定时间: 2026-09-01
> 目标: 明确各 Agent 职责边界，防止职责越界

---

## 一、三条并行轨道

```text
                    顺天 / Shuntian
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
     代码架构轨道      经典证据轨道       前端产品轨道
   Claude / OpenCode   Hermes + 5子代理     Codex
          │              │              │
     Runtime/Pipeline   五经 Evidence     LIORIN UI
     Signal/Contract    → Rule/Atom       → API Contract
          │              ↓              │
          │        Asset Governance      │
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                    GPT 最终裁决
```

---

## 二、Agent 权限矩阵

| Agent | 可以做 | 禁止做 |
|-------|--------|--------|
| **Hermes** | 调度、拆任务、QA 汇总、状态追踪 | 最终定义经典规则、自行裁决生产状态 |
| **五经 Agent** | 原典证据提取、规则提炼、语义解析、生成 Assertion Candidate | 自行入库生产、跳过 provenance 链条、为通过率强行授权 |
| **Mimocode/OpenCode** | 后端代码、测试、重构、Signal Contract | 自己裁决架构、重新引入 LegacyAdapter |
| **Codex** | 前端/UI/UX/API 消费 | 实现命理计算、前端计算 active_yao |
| **GPT** | 最终架构/证据/代码裁决 | 直接代替执行 Agent |
| **独立审计 Agent** | 发现问题、验证 | 修改自己审的东西 |

---

## 三、五经 Agent 职责边界

### 3.1 职责

每个经典 Agent 只负责自己的 Corpus：

```text
原典
 ↓
章节定位
 ↓
原文证据
 ↓
证据上下文
 ↓
候选规则
 ↓
语义结构化
 ↓
Modern Semantic Mapping
 ↓
Assertion Candidate
```

### 3.2 禁止行为

- ❌ 自行决定"是否进入生产"
- ❌ 跳过 provenance 链条
- ❌ 为通过率强行授权
- ❌ 比较其他经典的结论

### 3.3 输出格式

每条 Assertion 必须包含完整 provenance：

```json
{
  "assertion_id": "A-DTS-001-001",
  "source_system": "滴天髓辨证代理",
  "source_work": "滴天髓",
  "chapter": "通神论·衰旺",
  "source_locator": {
    "classic": "滴天髓",
    "chapter": "通神论·衰旺",
    "section": "第123段",
    "source_locator": "滴天髓·通神论·衰旺第123段"
  },
  "evidence_text": {
    "original_text": "...",
    "text_layer": "ORIGINAL",
    "context_before": "...",
    "context_after": "..."
  },
  "evidence_context": "...",
  "semantic_parse": {
    "observation_dimension": "得令",
    "evidence_type": "SEASONAL_SUPPORT",
    "direction": "SUPPORT",
    "mapping_to_canonical": {...}
  },
  "feature_mapping": {...},
  "trigger": "...",
  "judgment": "...",
  "modern_semantic": "...",
  "confidence": 0.7,
  "authorization_status": "PARTIAL",
  "production_status": "CANDIDATE"
}
```

---

## 四、生产准入流程

```text
Agent 生成 Assertion Candidate
         ↓
Independent Audit（独立审计）
         ↓
    ┌────┴────┐
    ↓         ↓
APPROVED   REJECTED
    ↓         ↓
Production  Revision
    ↓
GPT 最终裁决
```

**只有经过 GPT 裁决 APPROVED 的 Assertion 才能进入生产。**

---

## 五、核心原则

1. **原典授权 ≠ 条件成立 ≠ 断事结论授权** — 三层永久分离
2. **推理强度 ≤ 原典授权强度** — PARTIAL 只能输出 QUALIFIED
3. **每条证据必须可溯源** — 引用必须标注经典名 + 篇章 + 原文
4. **互补不比较** — 五 Agent 独立输出，不投票不平均
5. **不为通过率高强行授权** — 找不到原文就标 INSUFFICIENT_SOURCE
6. **算 → 辨 → 解 严格分层** — 不得用后层成果证明前层正确

---

## 六、代码轨道纪律

### 6.1 禁止事项

- ❌ 重新引入 `LegacyAdapter`
- ❌ 自行裁决架构问题
- ❌ 用测试结果掩盖设计缺陷

### 6.2 必须遵守

- ✅ 单一 Contract（CanonicalSignal、TemporalConvergence）
- ✅ 追踪 `signal_engine.py` 和 `CrossAnalyzer`
- ✅ 确认 Yi / Heluo / Blind Bazi 标准输出
- ✅ 最终形成 ONE PRODUCTION PATH

---

## 七、前端轨道纪律

### 7.1 禁止事项

- ❌ 前端计算命理（包括 `active_yao`）
- ❌ 前端实现八字/紫微/河洛计算

### 7.2 必须遵守

- ✅ 前端只消费 API
- ✅ `active_yao` 来自 EXIS API
- ✅ 遵守 LIORIN 前端规范

---

*本权限边界协议经 GPT 裁决后生效，所有 Agent 必须严格遵守。*
