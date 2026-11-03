# Multi-Agent Parallel Pipeline - 顺天裁决执行

**时间**: 2026-08-31  
**依据**: 顺天裁决 M3 Multi-Agent Pipeline  
**状态**: 🟢 APPROVED启动

---

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                  Multi-Agent Parallel Pipeline           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Worker A │  │ Worker B │  │ Worker C │  ...        │
│  │ 滴天髓   │  │ 子平真诠 │  │ 穷通宝鉴 │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │             │             │                     │
│       └─────────────┴─────────────┘                     │
│                      │                                  │
│                      ▼                                  │
│            ┌─────────────────┐                          │
│            │ Candidate Pool  │                          │
│            │ (Dedup/Merge)   │                          │
│            └────────┬────────┘                          │
│                     │                                   │
│                     ▼                                   │
│            ┌─────────────────┐                          │
│            │  Red-Team Agent │                          │
│            │  (独立审查)     │                          │
│            └────────┬────────┘                          │
│                     │                                   │
│                     ▼                                   │
│            ┌─────────────────┐                          │
│            │Claude独立审计   │                          │
│            └────────┬────────┘                          │
│                     │                                   │
│                     ▼                                   │
│            ┌─────────────────┐                          │
│            │  GPT Final      │                          │
│            │  Ruling         │                          │
│            └─────────────────┘                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Agent分工

### Worker Agents（5个）

| Agent ID | 经典 | 职责 |
|----------|------|------|
| WORKER-DTS | 《滴天髓》 | 原典挖掘 + Primitive提取 |
| WORKER-ZPZQ | 《子平真诠》 | 原典挖掘 + Primitive提取 |
| WORKER-QTBJ | 《穷通宝鉴》 | 原典挖掘 + Primitive提取 |
| WORKER-SMTH | 《三命通会》 | 原典挖掘 + Primitive提取 |
| WORKER-YHZP | 《渊海子平》 | 原典挖掘 + Primitive提取 |

### Red-Team Agent（1个）

| Agent ID | 职责 |
|----------|------|
| REDTEAM-001 | 独立审查所有Worker产出 |

### 审计Agent（1个）

| Agent ID | 职责 |
|----------|------|
| CLAUDE-AUDIT | Claude独立语义审计 |

---

## Pilot Batch设计

### 目标
每部经典提取20-30个Primitive Candidate，验证流水线稳定性。

### 范围
- 《滴天髓·通神论》全文（已完成Step 1-2）
- 《子平真诠·格局篇》（选取核心章节）
- 《穷通宝鉴·甲木篇》（选取1-2个天干）
- 《三命通会·天干篇》（选取核心内容）
- 《渊海子平·基础论》（选取基础概念）

### 产出目标
- 5部 × 25个 = 125个Primitive Candidate
- 进入Candidate Pool
- Red-Team审查
- Claude独立审计
- GPT裁决

---

## Candidate Package格式（强制标准）

```json
{
  "candidate_id": "CAND-{BOOK}-{SEQ}",
  "source_book": "滴天髓|子平真诠|穷通宝鉴|三命通会|渊海子平",
  "source_version": "通行本|任铁樵注|京图原注|其他",
  "text_layer": "ORIGINAL_TEXT|ORIGINAL_COMMENTARY|LATER_COMMENTARY",
  "original_text": "完整原文引用",
  "source_location": "章节位置",
  "semantic_unit": "提取的语义单元",
  "primitive_candidate": "候选Primitive名称",
  "canonical_mapping": "CANONICAL|PARTIAL|UNRESOLVED",
  "confidence": "HIGH|MEDIUM|LOW",
  "unresolved_questions": ["问题1", "问题2"],
  "agent_id": "WORKER-DTS|WORKER-ZPZQ|...",
  "creation_time": "ISO8601",
  "red_team_flags": [],
  "audit_status": "PENDING|APPROVED|DENIED"
}
```

---

## Red-Team审查清单

### 必须检查6项
1. ❓ 是否把注释当原典？
2. ❓ 是否把描述变成判断？
3. ❓ Primitive是否偷偷包含Judgment？
4. ❓ 是否自行增加Condition？
5. ❓ 是否存在工程推断？
6. ❓ 是否触碰L4 Strength？

### 输出格式
```json
{
  "redteam_id": "RT-{CANDIDATE_ID}",
  "candidate_id": "CAND-XXX",
  "checks": [
    {"item": "注释当原典", "result": "PASS|FAIL", "note": "..."},
    {"item": "描述变判断", "result": "PASS|FAIL", "note": "..."},
    {"item": "Primitive含Judgment", "result": "PASS|FAIL", "note": "..."},
    {"item": "自行增加Condition", "result": "PASS|FAIL", "note": "..."},
    {"item": "工程推断", "result": "PASS|FAIL", "note": "..."},
    {"item": "L4 Strength", "result": "PASS|FAIL", "note": "..."}
  ],
  "verdict": "PASS|FAIL",
  "findings": ["发现1", "发现2"],
  "recommendation": "建议..."
}
```

---

## 执行计划

### Phase 1: 基础设施（当前）
- [x] 设计Pipeline架构
- [x] 定义Candidate Package格式
- [x] 定义Red-Team审查清单
- [ ] 创建Worker Agent配置
- [ ] 创建Red-Team Agent配置
- [ ] 建立Candidate Pool存储

### Phase 2: Pilot Batch执行
- [ ] 启动5个Worker并行生产
- [ ] 收集Candidate Package
- [ ] Dedup/Merge
- [ ] Red-Team审查
- [ ] Claude独立审计
- [ ] GPT裁决

### Phase 3: 评估与扩大
- [ ] 评估Pilot效果
- [ ] 验证并行调度稳定性
- [ ] 验证Evidence格式统一性
- [ ] 验证Agent输出重复率
- [ ] 验证Red-Team有效性
- [ ] 验证Claude审计接收能力
- [ ] 评估成本/速度比
- [ ] 决定是否扩大规模

---

## 严格禁止

❌ **多Agent不是投票系统**
- 禁止：Agent A成立 + Agent B成立 + Agent C不成立 → 多数票通过
- 正确：多个Agent互补取证 → Red-Team独立审查 → Claude独立审计 → GPT裁决

❌ **禁止提前进入Condition/Judgment**
- 当前只批准：原典→Evidence→A/B/C→Primitive Candidate
- 禁止：Primitive→Condition→Judgment→Production

❌ **禁止跳过独立审计**
- 未经Claude独立审计 + GPT裁决，不得进入Production

---

## 立即执行

**现在开始Phase 1基础设施搭建**。