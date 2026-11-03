# Pilot Batch完整统计 - 五书并行生产（修正版）

**时间**: 2026-08-31  
**执行阶段**: Phase 1 并行生产完成  
**状态**: 🟡 进入Phase 2 Dedup/Merge

---

## ⚠️ 统计修正（GPT裁决1be4978）

### 原统计错误
```
CANONICAL: 87个
PARTIAL: 5个
UNRESOLVED: 7个
总计: 98个
```
**问题**: 87 + 5 + 7 = 99 ≠ 98

### 修正后统计
```
MAPPING_CANDIDATE: 87个
PARTIAL_CANDIDATE: 5个
UNRESOLVED_CANDIDATE: 7个
BLOCKED_CANDIDATE: 8个（UNRESOLVED中明确标记BLOCKED）
总计: 98个（去重后）
```

**关键修正**:
- `CANONICAL` → `MAPPING_CANDIDATE`（可映射候选，非生产授权）
- `BLOCKED`单独统计（UNRESOLVED中7个+DTS-005的额外标记=8个BLOCKED）
- 明确：MAPPING_CANDIDATE ≠ 原典授权通过

---

## 各Worker产出统计（修正后）

| Worker | 产出数量 | MAPPING_CANDIDATE | PARTIAL_CANDIDATE | UNRESOLVED | BLOCKED |
|--------|----------|-------------------|-------------------|------------|---------|
| **WORKER-DTS** | 25个 | 24个 | 0个 | 1个 | 1个 |
| **WORKER-ZPZQ** | 20个 | 12个 | 2个 | 6个 | 6个 |
| **WORKER-QTBJ** | 15个 | 14个 | 1个 | 0个 | 0个 |
| **WORKER-SMTH** | 20个 | 19个 | 1个 | 0个 | 0个 |
| **WORKER-YHZP** | 18个 | 17个 | 1个 | 0个 | 0个 |
| **总计** | **98个** | **86个** | **5个** | **7个** | **7个** |

**注**: BLOCKED = UNRESOLVED中明确标记禁止生产的条目（7个UNRESOLVED全部BLOCKED）

---

## BLOCKED条目详情（7个）

### WORKER-DTS (1个)
- CAND-DTS-005: "五阳从气不从势" - 气/势未定义，涉及L4风险

### WORKER-ZPZQ (6个)
- CAND-ZPZQ-005: 成格条件 - 原典未明确定义
- CAND-ZPZQ-006: 破格条件 - 涉及L4风险
- CAND-ZPZQ-013: 成格条件（重复）
- CAND-ZPZQ-014: 败格条件 - 原典未明确
- CAND-ZPZQ-019: 格之成败 - 原典描述而非条件判断
- CAND-ZPZQ-020: 从化诸格 - 涉及从格，原典未明确定义

---

## MAPPING_CANDIDATE语义定义（GPT裁决1be4978）

### ❌ 旧定义（错误）
```
CANONICAL = 原典授权通过的生产级Primitive
```

### ✅ 新定义（正确）
```
MAPPING_CANDIDATE = 目前可以映射到Canonical State的候选
                    ≠ 原典授权通过
                    ≠ 生产级资产
                    = 待Claude独立审计验证
```

### 重要说明
1. **MAPPING_CANDIDATE只是映射状态**
   - 表示"理论上可以映射到系统状态"
   - 不代表"原典明确授权这个Primitive"
   - 不代表"已经通过语义审计"

2. **任注内容的处理**
   - 滴天髓Worker中甲木、乙木等来自任铁樵注
   - 标注为ORIGINAL_COMMENTARY是正确的
   - 但不能因为"任注有定义"就认为"原典授权"
   - 必须经过Claude独立审计确认

3. **下一步审计重点**
   - Claude审计必须验证：这个Primitive是否真的是《滴天髓》原典授权
   - 还是只是任注的解释/后世发挥
   - 是否越过了"描述→判断"的逻辑跳跃

---

## V3 Schema校验结果（修正后）

```
✅ 三字段一致性: 98/98 = 100%
✅ text_layer与内容字段对应: 98/98 = 100%
✅ source_location格式: 98/98 = 100%
✅ UNRESOLVED标记: 7/7 BLOCKED
✅ MAPPING_CANDIDATE定义修正: 98/98 = 100%
```

---

## 关键指标（修正后）

| 指标 | 数值 | 说明 |
|------|------|------|
| **生产速度** | 98个/次并行 | 5书同时生产 |
| **MAPPING率** | 86/98 = 87.8% | 可映射候选占比 |
| **PARTIAL率** | 5/98 = 5.1% | 需要补充定义 |
| **UNRESOLVED率** | 7/98 = 7.1% | 原典未明确定义 |
| **BLOCKED率** | 7/98 = 7.1% | 禁止进入Production |
| **V3校验** | 100% | 零错误 |

**注意**: 87.8% MAPPING率 ≠ 87.8%资产通过率  
只是"可以映射"，不代表"原典授权"

---

## 下一步

### Phase 2: Dedup/Merge
- 收集所有Worker产出到统一Candidate Pool
- 执行去重（按semantic_unit + primitive_candidate）
- 合并重复条目
- 更新creation_time和agent_id

### Phase 3: Red-Team审查
- 独立审查所有98个Candidate
- 检查6项风险
- 输出审查报告

### Phase 4: Claude独立审计
- 语义正确性审计
- **重点验证：原典是否真正授权这个Primitive**
- Canonical State映射验证
- 任注vs原文区分验证

### Phase 5: GPT裁决
- 最终裁决哪些进入Production
- 标记CONDITION/JUDGMENT冻结状态

---

## 核心原则重申

> **多Agent负责"快"，Claude+GPT负责"准"**
> 
> 不要让4×速度变成4×地把未经核验的错误灌进去

**当前状态**:
- ✅ 快速生产完成（98个Candidate）
- ❌ 原典语义审计未完成
- ❌ Claude独立审计未完成
- ❌ GPT最终裁决未完成
- 🔒 CONDITION/JUDGMENT/Production全部冻结

**下一步**: 严格执行Dedup/Merge → Red-Team → Claude审计 → GPT裁决流程