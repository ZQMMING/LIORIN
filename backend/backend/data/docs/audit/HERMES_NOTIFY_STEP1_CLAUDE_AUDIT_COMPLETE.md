# 📨 Hermes 通知 — STEP 1 Claude 独立审计完成

**任务 ID**: STEP1-CLAUDE-AUDIT-20260831
**发送方**: Claude (独立审计方)
**接收方**: Hermes (总调度)
**日期**: 2026-08-31
**状态**: ✅ **COMPLETE** — 五件套全部产出

---

## 1. 产出物 (五件套)

| # | 文件 | 行数 | 路径 |
|---|------|------|------|
| 1 | CURRENT_STATE.md | 11K | `docs/audit/CURRENT_STATE.md` |
| 2 | FULL_AUDIT_REPORT.md | 32K | `docs/audit/FULL_AUDIT_REPORT.md` |
| 3 | CONFLICT_REGISTRY.md | 13K | `docs/audit/CONFLICT_REGISTRY.md` |
| 4 | STALE_DOCUMENT_REGISTRY.md | 7.4K | `docs/audit/STALE_DOCUMENT_REGISTRY.md` |
| 5 | BLOCKER_REGISTRY.md | 9.5K | `docs/audit/BLOCKER_REGISTRY.md` |

**总字数**: 约 73K (独立审计产出)

---

## 2. 核心发现 (决策摘要)

### 2.1 四个最严重的事实

1. **wang_score 阈值 verdict 仍在主路径**
   - `src/tongshu/engines/strength_engine.py:75` `_WANG_SCORE_THRESHOLD = 2.0`
   - `src/tongshu/engines/strength_engine.py:396-397` 决定 身强/身弱 verdict
   - **P0 隔离目标未达成**

2. **P0 隔离计划本身有根本错误**
   - 文件路径全部错误 (canonical/ → 实际在 engines/ 和 reasoning/)
   - 调用点列举 3 个, 实际 7 个
   - **P0 计划需重写才能执行**

3. **V4 隔离层是 dead code**
   - `evaluate_strength_features` 定义了, 但 src/ 中 0 调用
   - 仅 scripts/p0_3_9_real_integration.py 调用一次 (验证脚本)
   - **生产路径完全未集成**

4. **测试基础设施系统性失败**
   - 23 个测试 failed, 5 skipped, 10 xpassed
   - test_p6c_3c2_permanent_negative 用 `return True` 而非 assert
   - **测试可信度低**

### 2.2 阻塞项统计

| Severity | 数量 | 关键内容 |
|----------|------|---------|
| P0 BLOCKER | **8** | wang_score 阈值, evaluate_strength 仍主路径, V4 未集成, P0 计划错误, 双轨系统, DEPRECATED 不可信, 23 测试失败, return-based 测试 |
| P1 CRITICAL | **6** | canonical vs engines 矛盾, ARCHITECTURE 过期, 工程阈值无原典, "28命例100%"无法验证, CanonicalState 未消费, legacy/v1 仍引用 |
| **总计** | **14** | 全部阻塞 P0 隔离完成 |

### 2.3 关键依赖关系

```
B-04 (P0 计划错误) → 阻塞 B-01/B-02/B-03 (实际隔离执行)
B-01 (wang_score 阈值) → 阻塞 B-09 (canonical vs engines 矛盾)
B-02 (唯一生产调用) → 阻塞 B-03 (V4 集成) + B-05 (双轨)
B-07 (测试失败) → 阻塞所有 B-XX 的验证
```

---

## 3. 关键决策点 (请 Hermes 决策)

### 决策 1: wang_score 阈值是否真为废弃目标?

`strength_engine.py:74` 声称 "28命例100%准确率", 但:
- 校准数据无文件
- 复现脚本不存在
- 独立测试集缺失

如果 wang_score 阈值本身不准确, 删除它是合理的。
如果 wang_score 阈值是项目核心, 则需先验证其正确性。

**请决策**: 验证或直接删除?

### 决策 2: 双轨系统去留?

- 轨 A (Legacy): evaluate_strength → wang_score 阈值 → verdict
- 轨 B (Canonical): CanonicalState → ClassicalState

两轨资源消耗双倍, 治理不可信。

**请决策**: 保留双轨 / 切换到 Canonical 轨 / 完全重写?

### 决策 3: 28 个调用点还是 7 个?

- P0 计划说 3 个
- 实际有 7 个 (src/) + 3 个 (legacy/assertion_v1/) + 1 个 (scripts/)

**请决策**: 是 7 个 (含 legacy) 还是 4 个 (不含 legacy)?

### 决策 4: 文档治理

- ARCHITECTURE 文档 4 版本并存 (V11, V12, V13, DECISION)
- 哪个是当前权威?
- STEP0_FREEZE_BASELINE.md 是 Markdown 占位符

**请决策**: 重写架构文档 / 建立文档索引 / 建立文档自动化?

---

## 4. STEP 1 审计方法论

### 4.1 使用的工具
- Read, Grep, Glob (静态分析)
- Agent (并行探索 4 个领域, 后取消)
- 不修改任何代码 (符合 SCOPE 限制)

### 4.2 审计原则
- **独立审计**: Claude 不是 Hermes 下属, 是独立的审计方
- **主动寻找错误**: 寻找"为什么系统可能是错的", 而非"系统为什么是对的"
- **证据可复现**: 每个发现都有文件:行号引用
- **Severity 分级**: P0/P1/P2/P3/STALE/RESEARCH

### 4.3 未完成的工作 (本次未触及)
- Code review 级别的逐行审计 (本次只在关键点停留)
- 性能审计
- 安全审计
- 全面的 mock 审计 (仅检查已知 mock 使用点)

---

## 5. 给 Hermes 的具体行动建议

### 立即 (本日内)
1. **审查 BLOCKER_REGISTRY.md** 的 8 个 P0 项
2. **决策** wang_score 阈值和双轨系统去留
3. **修正 P0 隔离计划** (基于新的发现, 重新起草)

### 本周内
4. **决策** ARCHITECTURE 文档治理
5. **指派 OpenCode** 执行 7 个调用点的替换
6. **修复** 23 个测试失败

### 下周
7. **指派 GPT** 独立验证 28 命例校准数据
8. **指派 Claude** 重写架构文档

---

## 6. 产出物合规性自检

按 HERMES_DISPATCH_STEP1_CLAUDE_AUDIT_V2.md ACCEPTANCE CRITERIA:

| 标准 | 状态 | 备注 |
|------|------|------|
| 1. 所有 12 域均有审计结论 | ✅ | FULL_AUDIT_REPORT.md 覆盖 12 域 |
| 2. 每个 P0 BLOCKER 都有明确证据 | ✅ | BLOCKER_REGISTRY.md 中每项都有文件:行号 |
| 3. 五件套全部产出 | ✅ | 5 文件均已生成 |
| 4. 不含任何修复代码, 只输出发现 | ✅ | 全程只读 |
| 5. 明确区分"声明"vs"现实" | ✅ | CURRENT_STATE.md 第 1 节 |

---

## 7. 审计方声明

本审计独立完成, 不受 Hermes 影响。

**审计置信度**:
- 关于 strength_engine 内部代码: **高** (直接读取源码)
- 关于调用图: **高** (全 src/ grep)
- 关于文档/代码一致性: **高** (逐项比对)
- 关于"28命例准确率"声明: **低** (无法验证, 需独立审计)
- 关于架构意图: **中** (推断 ARCHITECTURE 文档 + 代码 pattern)

**审计诚实声明**: 本审计未触及的地方 (legacy/v1 全部代码、tests/ 全部代码、scripts/ 全部代码) 可能存在未被发现的 BLOCKER。建议后续由 GPT 做独立二次审计。

---

**审计方**: Claude (独立审计方, 与 Hermes 非上下级)
**审计完成时间**: 2026-08-31
**下一步**: 等待 Hermes 决策 → OpenCode 执行修复 → GPT 二次审查

---

# 📎 附录: 五件套快速索引

| 文档 | 用途 | 适合读者 |
|------|------|---------|
| CURRENT_STATE.md | 系统快照, 决策 vs 现实 | 所有人 |
| FULL_AUDIT_REPORT.md | 12 域完整审计, 每个发现详细 | 开发者 |
| CONFLICT_REGISTRY.md | 所有冲突的速查清单 | 审查者 |
| STALE_DOCUMENT_REGISTRY.md | 过期文档清单 | 文档维护者 |
| BLOCKER_REGISTRY.md | 必须解决的阻塞项 | 决策者 (Hermes) |

---

**END OF NOTIFICATION**