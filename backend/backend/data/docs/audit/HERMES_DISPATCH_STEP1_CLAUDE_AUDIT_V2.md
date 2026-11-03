# 📋 HERMES-DISPATCH: STEP 1 - Claude独立12域全审

---

**Task ID**: STEP1-CLAUDE-AUDIT-20260831  
**Priority**: P0 BLOCKER  
**Owner**: Claude (独立审计方)  
**Requester**: Hermes (总调度)  
**Deadline**: 立即执行  

---

## WHY

Legacy Strength Engine 标记为LEGACY但仍在生产调用链运行，形成双轨系统。必须独立审计确认所有风险点，为后续P0修复提供依据。

---

## WHAT

执行 **12域独立代码审计**，重点攻击以下薄弱点：

### 核心攻击点（必须验证）

1. **wang_score隐性生产路径**
   - 检查所有import/调用关系
   - 确认是否还有未切断的生产入口
   - 特别关注：annual_event_evaluator.py, judgment_engine.py, health_signals.py

2. **数量替代力量**
   - 查找所有weight/threshold/score用法
   - 确认是否有工程阈值冒充Canonical
   - 检查Feature ≠ Concept混淆

3. **Canonical State反向推导**
   - 验证下游结果是否反推上游State
   - 检查Assertion → State的逆向依赖
   - 确认单向流向：Input → Calc → Rule → Output

4. **Condition TRUE真实性**
   - 验证TRUE是否由Canonical State证明
   - 检查是否有mock/fake data伪造测试
   - 确认Mapper不会因命中就直接授权

5. **UNRESOLVED误用**
   - 检查是否有UNRESOLVED被当FALSE/PASS
   - 验证逻辑传播是否正确
   - 确认AND/OR复合没有原典授权伪装

6. **Composite AND/OR原典授权**
   - 检查复合条件是否有五经明确授权
   - 确认不是工程构造的逻辑组合
   - 验证每个原子条件的Canonical来源

7. **测试真实性**
   - 查找所有mock/fixture/hard-coded
   - 检查simulate_chart等自造数据
   - 确认宽松assert（如`in [TRUE, UNRESOLVED]`）

8. **文档 vs 代码一致性**
   - 对比docs/声明与src/实际实现
   - 确认DEPRECATED标注与实际运行状态
   - 验证FROZEN声明与实际可修改状态

---

## CURRENT STATE

```
M2资产验证进度: 86/86 (100%)
结构性条件: TenGod✅ PowerComparison✅ Negation✅ DayYearRelation✅ Root✅
Legacy Strength: 标记DEPRECATED但仍在生产链运行
STEP 0: 已冻结 (tag: STEP0-FREEZE-20260831-054019)
```

---

## CANONICAL

依据文件：
- `D:/wiki/wiki/Obsidian/Hermes/生活通书项目/SHUNTIAN_V1.3_GOVERNANCE_RESET_权威基准.md`
- `src/tongshu/canonical/` 目录下的契约定义
- 五部经典：滴天髓、子平真诠、穷通宝鉴、三命通会、渊海子平

---

## SCOPE

**允许检查**:
- 所有src/目录下的Python代码
- 所有tests/目录下的测试代码
- 所有docs/目录下的文档
- 所有配置文件

**允许搜索**:
- grep/import/调用关系分析
- 阈值/权重/评分相关代码定位
- mock/fixture/hard-coded识别
- 文档与代码一致性比对

**禁止修改**:
- ❌ 不修改任何生产代码
- ❌ 不修改任何测试代码
- ❌ 不修改任何配置
- ❌ 只发现，不修复

---

## BOUNDARY

- 只输出审计发现，不执行修复
- 如果发现P0 BLOCKER，必须明确标注
- 使用Severity分级：P0 BLOCKER / P1 CRITICAL / P2 IMPORTANT / P3 NON-BLOCKING / STALE / RESEARCH
- 每个发现必须提供Evidence（文件路径+行号）

---

## INPUT契约

```python
class AuditFinding:
    id: str                    # A01, A02, ...
    domain: str               # Runtime/Canonical/Governance/Validation/Architecture/Process
    severity: str             # P0/P1/P2/P3/STALE/RESEARCH
    finding: str              # 发现的问题描述
    evidence: str             # 具体证据（文件+行号）
    current_reality: str      # 当前实际状态
    canonical_expectation: str # 应该是什么
    owner: str               # 负责修复的Agent
    action: str              # 建议操作（KEEP/FIX/REMOVE/RESEARCH/STALE）
```

---

## OUTPUT契约

**必须产出五件套**:

1. **CURRENT_STATE.md** - 当前系统状态快照
2. **FULL_AUDIT_REPORT.md** - 12域完整审计报告
3. **CONFLICT_REGISTRY.md** - 发现的所有冲突列表
4. **STALE_DOCUMENT_REGISTRY.md** - 过期/不一致文档清单
5. **BLOCKER_REGISTRY.md** - 必须解决的阻塞项（P0/P1）

**输出位置**: `docs/audit/`

---

## ACCEPTANCE CRITERIA

1. ✅ 所有12域均有审计结论
2. ✅ 每个P0 BLOCKER都有明确证据（文件+行号）
3. ✅ 五件套全部产出
4. ✅ 不含任何修复代码，只输出发现
5. ✅ 明确区分"声明"vs"现实"

---

## TEST

审计本身无需测试，但产出物必须满足：
- 每个发现可复现（提供具体路径和行号）
- 每个Severity判定有依据
- 每个ACTION建议可执行

---

## REGRESSION

本次审计禁止修改任何代码，不存在回归风险。

---

## ROLLBACK

如果审计过程中发现误判，可以在FINAL_AUDIT_REPORT中补充修正，不追溯修改。

---

## Gatekeeper

**Reviewer**: GPT（最终裁决）  
**Approver**: 用户确认（飞书通知）

---

## Notes

**重要提醒**:
- 这是**独立审计**，Claude不是Hermes的下属，而是独立的审计方
- 必须主动寻找"为什么系统可能是错的"，而不是"系统为什么是对的"
- 特别是命理项目，很多错误是**语义模型错误**，不是Python bug
- 自测最难发现这类错误，所以需要外部视角

---

**Dispatch Time**: 2026-08-31  
**Status**: 🚨 P0 BLOCKER - 立即执行