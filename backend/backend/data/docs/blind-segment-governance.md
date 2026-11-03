# 盲派辨证据收集治理要点

## 本Session Key Decisions (2026-09-02)

### 1. 架构边界

**盲派辨Evidence Corpus ≠ 五经证据系统**

- 盲派辨存储在 `data/evidence/blind_seg/`
- 五经证据存储在 `data/evidence/`
- 两者必须物理隔离，禁止混入

### 2. 分层架构 (A/B/C/D)

| Layer | 定义 | Authority Status | 示例 |
|-------|------|------------------|------|
| A | 传承证据 | PRIMARY_TRADITION | 夏仲奇口传、邢铭芬整理 |
| B | 段氏系统化理论 | SYSTEMATIZED | 段建业《盲派初级命理学》 |
| C | 命例验证 | CASE_EVIDENCE | 案例资料集中的具体命例 |
| D | 派生内容 | DERIVED | 后人整理、二次分析 |

**禁止**: B→A / C→A / C→B 等 provenance 升级

### 3. 治理规则

#### PM-001: Provenance Immutability
Evidence 创建后 `provenance_layer` 原则上不可修改。发现分类错误时，不应覆盖原证据，而应：
1. 保留原 Evidence
2. 标记 `status = SUPERSEDED`
3. 新增正确层级的新 Evidence

#### PM-002: Layer × Authority 一致性
```
A → PRIMARY_TRADITION
B → SYSTEMATIZED
C → CASE_EVIDENCE
D → DERIVED
```

#### PM-003: DIRECT Fidelity (分层要求)
- **A层**: edition + locator + author + chapter REQUIRED
- **B层**: edition RECOMMENDED, locator REQUIRED
- **C层**: edition OPTIONAL, locator REQUIRED
- **D层**: N/A

#### PM-004: 禁止Provenance升级
禁止通过修改Evidence内容改变provenance层级。

#### PM-005: Original Text 真实性
- `<10 chars` 或 `>500 chars` 触发 warning
- `source_fidelity = DIRECT` 不等于已核实原文
- 最终需进入 Multi-AI Final Verification 队列

### 4. Topic Taxonomy (13项)

核心主题列表（extraction topics，非冻结Blind Signals）:

```
GUEST_HOST        宾主
BODY_USE_RELATION 体用
WORK_RELATION     做功关系
WORK_TYPE         做功类型
WORK_ACTOR        做功主体
WORK_TARGET       功靶/功用
WORK_EFFICIENCY   做功效率
POWER_PARTY       势/党
EMPTY_USELESS     虚实
IMAGE             象法
YING_QI           应期
COMPLEX_WORK      复杂做功
WORK_METHOD       做功方式
```

**注意**: 这些是extraction topics，不是已冻结的Blind Signals。Phase B才定义Signal Schema。

### 5. Phase A 执行约束 (B1-B4)

来自仲裁裁决的四个约束:

- **B1**: Canonical Chart State 可跨体系共享，但 Signal Namespace 必须独立
- **B2**: BODY_USE_RELATION ≠ 子平用神，禁止产生统一 yongshen 字段
- **B3**: 必须区分 RAW_EVIDENCE / DERIVED_BLIND_STATE / SEMANTIC_INTERPRETATION
- **B4**: Phase A 只做 Evidence Corpus，不做 Signal Mapping

### 6. Phase B 触发条件

Phase B (Signal Schema定义) 必须等待:
1. 五部经典证据全部完成
2. 盲派辨 Phase A Evidence 全部完成
3. 获得仲裁裁决批准

### 7. 生产规则边界

**严禁在Phase A中建立任何 Production Assertion Rules**

- `data/rules/production_assertion_rules.json` 必须移除
- 候选规则应放 `data/drafts/` 并标记 `status = CANDIDATE`
- Production Admission 由 Claude 负责，不在盲派 Phase A 范围内

### 8. 审计要求

每个 commit 必须保持:
- Manifest 与实际证据文件数量一致
- Audit Trail 文档同步更新
- Validator 运行结果干净 (0 errors)

### 9. 持续性问题记录

#### 问题1: DIRECT + HIGH 过早授权
当前所有新增证据都标为 `DIRECT + HIGH`，但 Validator 只能验证字段结构，不能验证原文真实性。

**建议状态**: 标记为 `PENDING_SOURCE_VERIFICATION` 而非直接视为已核实权威证据。

#### 问题2: P16 Runtime Test 断言强度不足
测试标题声称 \"Pipeline 必须产生来自 Production Rule 的 Atomic Claims\"，但实际只检查 `claims > 0`。

**后续**: 应加强为强制检查 production rule 引用。

---

## 当前状态 (2026-09-02)

| 项目 | 状态 |
|------|------|
| 五经 Evidence | 1498条, Phase 3 冻结 (14cf35e) |
| 盲派 Phase A Evidence | 55条, PHASE_A_IN_PROGRESS |
| 盲派 Phase B | 冻结, 等待裁决 |
| Multi-AI Final Verification | 冻结, 待全部完成后启动 |
| Production Admission | Claude 负责, 独立轨道 |
