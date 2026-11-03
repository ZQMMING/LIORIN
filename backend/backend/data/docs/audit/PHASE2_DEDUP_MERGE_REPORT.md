# Dedup/Merge执行报告 - Phase 2

**时间**: 2026-08-31  
**执行阶段**: Phase 2 Dedup/Merge  
**状态**: 🟢 完成

---

## 输入数据

从5个Worker收集：
- WORKER-DTS: 25个Candidate
- WORKER-ZPZQ: 20个Candidate
- WORKER-QTBJ: 15个Candidate
- WORKER-SMTH: 20个Candidate
- WORKER-YHZP: 18个Candidate
- **总计**: 98个Candidate

---

## Dedup规则

### 去重键
```
dedup_key = (semantic_unit, primitive_candidate)
```

### 去重策略
1. 如果多个Worker产出相同semantic_unit + primitive_candidate
2. 保留最早creation_time的条目
3. 记录重复条目到dedup_log
4. 合并agent_id为原始Worker列表

---

## Merge结果

| 操作 | 数量 | 说明 |
|------|------|------|
| **原始输入** | 98个 | 5 Worker产出 |
| **去重移除** | 0个 | 无重复条目 |
| **最终输出** | 98个 | 全部保留 |

**结论**: 5部经典产出无语义重复，全部保留

---

## Schema V4迁移

### 迁移规则
```
CANONICAL → MAPPING_CANDIDATE
PARTIAL → PARTIAL_CANDIDATE
UNRESOLVED → UNRESOLVED_CANDIDATE
```

### 迁移统计

| 原值 | 新值 | 数量 |
|------|------|------|
| CANONICAL | MAPPING_CANDIDATE | 86个 |
| PARTIAL | PARTIAL_CANDIDATE | 5个 |
| UNRESOLVED | UNRESOLVED_CANDIDATE | 7个 |
| **总计** | - | **98个** |

---

## BLOCKED验证

### 强制BLOCKED条目（7个）

| Candidate ID | 理由 |
|--------------|------|
| CAND-DTS-005 | 气/势未定义，涉及L4风险 |
| CAND-ZPZQ-005 | 成格条件原典未明确 |
| CAND-ZPZQ-006 | 破格条件涉及L4风险 |
| CAND-ZPZQ-013 | 成格条件重复 |
| CAND-ZPZQ-014 | 败格条件原典未明确 |
| CAND-ZPZQ-019 | 格之成败非条件判断 |
| CAND-ZPZQ-020 | 从化诸格涉及从格 |

**验证**: 7个BLOCKED全部正确标记

---

## 输出文件

### Candidate Pool（V4 Schema）
```
data/canonical/candidate_pool_pilot_v2.json
```

### Dedup Log
```
docs/audit/DEDUP_LOG_PILOT_BATCH.md
```

### Schema迁移日志
```
docs/audit/SCHEMA_MIGRATION_LOG_V3_TO_V4.md
```

---

## 下一步

### Phase 3: Red-Team审查
- 独立审查所有98个Candidate
- 检查6项风险
- 输出审查报告

**启动Red-Team审查**