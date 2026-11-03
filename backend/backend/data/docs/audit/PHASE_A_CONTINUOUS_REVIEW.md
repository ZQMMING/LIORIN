# Phase A 持续审查记录

## 审查时间: 2026-09-02

### 审查记录

| Commit | 日期 | 裁决 | 说明 |
|--------|------|------|------|
| c846ee9 | 2026-09-02 | 🟢 轻量检查通过 | 6条新增证据无硬性阻塞问题 |
| 708540d | 2026-09-02 | 🟢 PASS (收尾提交) | 仅同步manifest时间戳，不新增Evidence |
| 99c7d55 | 2026-09-02 | 🟢 PASS | 修复manifest provenance_distribution同步 |
| a1c7a72 | 2026-09-02 | 🟢 PASS | 修复extraction_topic数字ID污染 |
| 87f58e1 | 2026-09-02 | 🟡 CONDITIONAL PASS | 恢复A层edition，建立PM规则 |
| 5138eeb | 2026-09-02 | 🟡 CONDITIONAL PASS | PM-003分层细化，validator建立 |
| e8e746a | 2026-09-02 | 🔴 REWORK REQUIRED | Topic taxonomy污染（数字ID）|
| 3fe32aa | 2026-09-02 | 🟢 PASS | 修复Topic分类（WORK_METHOD拆分）|
| bcbc472 | 2026-09-02 | 🔴 REWORK REQUIRED | Provenance integrity违规 |
| 054d217 | 2026-09-02 | 🔴 REWORK REQUIRED | 生产规则提前授权 + manifest矛盾 |
| 5eeff78 | 2026-09-02 | 🟢 PASS | 修复054d217，移除prod rules，更新audit trail |
| 01df473 | 2026-09-02 | 🟡 CONDITIONAL PASS | 扩充到55条，DIRECT/HIGH待最终核验 |

---

## 持续性问题

### 1. DIRECT + HIGH 过早授权

所有新增证据（包括B层和C层案例）都标为 `source_fidelity = DIRECT` 和 `certainty = HIGH`。

**现状**: Validator 能验证字段结构，但不能验证原文真实性。

**待解决**: 进入 Multi-AI Final Verification 时，需要独立文献核验。

**建议状态**: 标记为 `PENDING_SOURCE_VERIFICATION` 而非直接视为已核实。

---

### 2. P16 Runtime Test 断言强度不足

`tests/spec/test_p16_production_runtime_proof.py` 的 P16-05 测试：

- 标题声称：Pipeline 必须产生来自 Production Rule 的 Atomic Claims
- 实际实现：仅检查 claims > 0，production rule 引用仅作为 WARNING

**影响**: 非 Phase A blocker，但属于测试契约强度问题。

**后续**: 应加强为强制检查。

---

### 3. Production Assertion Rules 边界

仓库中存在 `data/assertion_rules/production_assertion_rules.json`：

```json
{
  "status": "PRODUCTION",
  "verification_scope": "PRODUCTION_ADMITTED",
  "verified_by": "gpt-adjudicator-v1",
  "rules": ["ASR-PROD-001", "ASR-PROD-002", "ASR-PROD-003"]
}
```

**重要澄清**:
- 此文件**不是** 054d217 或 01df473 新增（054d217 添加的是错误位置的文件）
- 此文件位于 `data/assertion_rules/` 而非 `data/evidence/blind_seg/`
- 此文件是 Claude 主导的 Production Admission 工作的一部分，不在盲派 Phase A 范围内

**边界保持**:
- 盲派 Phase A = Evidence Collection
- Production Admission = Claude 负责
- 两者通过仲裁机制协调，不混入同一目录

---

## 当前状态

| 项目 | 状态 |
|------|------|
| 五经 Evidence | 1498条，Phase 3 冻结 |
| 盲派 Phase A Evidence | 55条，PHASE_A_IN_PROGRESS |
| Phase B Signal Schema | 冻结，等待裁决 |
| Multi-AI Final Verification | 冻结，待全部完成后启动 |
| Production Admission | Claude 负责，独立轨道 |

---

## 下一步

1. **继续扩充 Phase A** — 质量优先，真实出处 > 数量
2. **准备五经 Phase 4** — Independent Verification
3. **等待 Phase B 裁决** — Signal Schema 定义
4. **最终 Multi-AI Verification** — 五经 + 盲派全部完成后启动
