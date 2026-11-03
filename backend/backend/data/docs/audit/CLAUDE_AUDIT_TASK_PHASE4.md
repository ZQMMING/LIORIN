# Phase 4: Claude独立审计任务 - Pilot Batch 98条Candidate

**审计Agent**: Claude Code CLI  
**审计时间**: 2026-08-31  
**审计对象**: data/canonical/candidate_pool_pilot.json（98条）  
**依据**: GPT裁决 63ad54d  
**状态**: 🟢 APPROVED启动

---

## 审计目标

逐条判断98条MAPPING_CANDIDATE：
1. **原典是否支持？** - 是否是《滴天髓》/《子平真诠》等原文内容
2. **Primitive是否忠实？** - 提取的语义单元是否准确
3. **是否只是任注？** - 任铁樵注释不等于原典授权
4. **是否偷入Condition？** - Primitive是否隐含条件判断
5. **是否触碰L4？** - 是否涉及力量/旺衰比较

---

## 统计口径修正（GPT裁决要求）

### 问题
报告声称：
- FAIL = 9个
- BLOCKED = 7个（UNRESOLVED）

差异原因：
- 2个FAIL是Red-Team标记但不属于UNRESOLVED类别
- 需要明确区分BLOCKED vs FAIL vs PENDING

### 修正定义

| 状态 | 含义 | 数量 |
|------|------|------|
| **BLOCKED** | UNRESOLVED_CANDIDATE，明确禁止生产 | 7个 |
| **FAIL** | Red-Team审查未通过，需标注原因 | 9个 |
| **PENDING** | Red-Team PASS，待Claude审计 | 89个 |

**注意**: FAIL包含BLOCKED + PARTIAL两类

---

## 9个FAIL完整列表

### 1. CAND-DTS-005（BLOCKED）
```json
{
  "candidate_id": "CAND-DTS-005",
  "red_team_flags": ["CONDITION_RISK", "L4_RISK", "UNRESOLVED_DEFINITION"],
  "audit_status": "BLOCKED",
  "fail_reason": "气和势未定义，涉及L4力量问题"
}
```

### 2-7. CAND-ZPZQ-005/006/013/014/019/020（BLOCKED）
```json
{
  "candidate_ids": [
    "CAND-ZPZQ-005",
    "CAND-ZPZQ-006",
    "CAND-ZPZQ-013",
    "CAND-ZPZQ-014",
    "CAND-ZPZQ-019",
    "CAND-ZPZQ-020"
  ],
  "audit_status": "BLOCKED",
  "fail_reason": "格局成败条件原典未明确，涉及L4风险"
}
```

### 8. CAND-QTBJ-015（PARTIAL）
```json
{
  "candidate_id": "CAND-QTBJ-015",
  "canonical_mapping": "PARTIAL_CANDIDATE",
  "red_team_flags": ["UNDEFINED_CONCEPT"],
  "audit_status": "PENDING",
  "fail_reason": "调候概念原典未明确定义"
}
```

### 9. CAND-YHZP-016（PARTIAL）
```json
{
  "candidate_id": "CAND-YHZP-016",
  "canonical_mapping": "PARTIAL_CANDIDATE",
  "red_team_flags": ["AMBIGUOUS_RELATIONSHIP"],
  "audit_status": "PENDING",
  "fail_reason": "偏印/枭神关系不明确"
}
```

---

## 统计修正后

| 状态 | 数量 | 说明 |
|------|------|------|
| **BLOCKED** | 7个 | UNRESOLVED，禁止生产 |
| **PARTIAL** | 2个 | 需补充定义，待Claude审计 |
| **PENDING** | 89个 | Red-Team PASS，待Claude审计 |
| **总计** | 98个 | - |

**FAIL总数 = 9个（7 BLOCKED + 2 PARTIAL）**

---

## 审计输入文件

### 主要数据
- `data/canonical/candidate_pool_pilot.json` - 98条Candidate（V4 Schema）

### 参考文档
- `docs/audit/RECONSTRUCTION_STEP1/DTS_TONGSHENLUN_ANALYSIS_V2.md` - 滴天髓Step 1分析
- `docs/audit/CANDIDATE_POOL_SCHEMA_V4.md` - Schema定义
- `docs/audit/REDTEAM_REPORT_PILOT_BATCH_V2.md` - Red-Team报告

---

## 审计输出格式

每条Candidate输出：
```json
{
  "candidate_id": "CAND-XXX",
  "original_text_check": "PASS|FAIL|NEEDS_REVIEW",
  "primitive_fidelity_check": "PASS|FAIL|NEEDS_REVIEW",
  "commentary_risk_check": "PASS|FAIL|NEEDS_REVIEW",
  "condition_leakage_check": "PASS|FAIL|NEEDS_REVIEW",
  "l4_risk_check": "PASS|FAIL|NEEDS_REVIEW",
  "overall_verdict": "APPROVED|DENIED|PENDING_CLARIFICATION",
  "notes": "审计说明"
}
```

---

## 重点审计对象

### 高风险条目（需逐字核对原文）
1. **滴天髓Worker**: 甲木、乙木...癸水（8条，全部任注）
2. **子平真诠Worker**: 格局成败相关（6条）
3. **穷通宝鉴Worker**: 调候概念（1条）

### 中风险条目（需验证原典出处）
1. **三命通会Worker**: 天干地支总论（20条）
2. **渊海子平Worker**: 十神定义（18条）

---

## 执行命令

```bash
cd /d/shuntian/backend
claude --model sonnet -p "$(cat CLAUDE_AUDIT_TASK_PHASE4.md)"
```

**预计输出**: 
- Claude独立审计报告
- 98条逐条审计结果
- 最终裁决建议（APPROVED/DENIED/PENDING）

---

## 下一步

Claude审计完成后：
1. 输出审计报告到 `docs/audit/CLAUDE_AUDIT_PHASE4_RESULT.md`
2. 提交GPT裁决Phase 4
3. 根据裁决决定是否进入Production