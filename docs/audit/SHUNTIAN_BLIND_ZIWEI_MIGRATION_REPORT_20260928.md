# Shuntian blind/ziwei 覆盖清理迁移报告

**日期**: 2026-09-28  
**分支**: `maintenance/blind-ziwei-migration-20260928`  
**D 基线 HEAD**: `7eb39fcfe5761fd302e73db97fc88b387db7ae01`  
**E 来源**: `E:\迁移合并`（根目录无 Git 元数据）

## 1. 执行结论

本次没有执行目录级覆盖，也没有把 E 侧旧/不同代实现强行覆盖到 D 侧。

原因：

- E 侧没有可证明来源的 Git commit；
- E 侧同时存在 `engines/` 旧式实现和 `ziwei_engine/src/tongshu/` 新式工程；
- E 侧 `engines/ziwei_adapter.py` 使用旧的 raw hour bySolar 调用，缺少 D 侧 time-index 修复；
- E 侧 `engines/ziwei_engine.py` 缺少 D 侧当前 `ZiweiChart` 顶层字段合同；
- E 侧 `src/tongshu/engines/blind/` 与 D 侧对应包不是同一代 API；
- E 侧新增内容主要是新架构、缓存、`node_modules` 和 `.egg-info`，没有确认可直接迁入的生产增量。

**最终策略**：保留 D 侧已经测试通过的生产实现；拒绝不安全覆盖；清理本次测试生成缓存；提交迁移基线、文件映射、清理路径、紫微修复报告和新增合同测试。

## 2. 源/目标对比

### E 侧新增/候选内容

- `ziwei_engine/src/tongshu/engines/blind/`：新一代分层 `BlindEngine`，与 D 侧旧 evidence/rules 包不兼容，未覆盖。
- `ziwei_engine/src/tongshu/engines/ziwei/engine.py`：一站式紫微 facade，不是 D 侧顶层 `ZiweiEngine` 的 drop-in replacement，未覆盖。
- `ziwei_engine/node_modules/`：第三方运行产物，排除。
- `ziwei_engine/src/tongshu.egg-info/`：构建产物，排除。
- 各路径 `__pycache__/*.pyc`：缓存，排除。

### E/D 同路径内容

对实际存在的 `blind/`、`blind_engine/blind/`、`blind_evidence/blind_seg/`、`blind_seg/`、`blind_tests/test_blind_rules/` 和部分 `engines/ziwei/` 文件进行哈希比对：常规源码、JSON 数据和测试文件未发现安全新增增量，重复镜像内容保持原状。

### 未覆盖的高风险文件

- E `engines/ziwei_engine.py` → D `src/tongshu/engines/ziwei_engine.py`
- E `engines/ziwei_adapter.py` → D `src/tongshu/engines/ziwei_adapter.py`
- E `engines/blind_bazi_engine.py` → D `src/tongshu/engines/blind_bazi_engine.py`
- E `engines/blind_yingqi.py` → D `src/tongshu/engines/blind_yingqi.py`

这些文件存在行为或合同回退，未迁移。

## 3. 本次实际变更

### 保留/确认

- D 侧紫微顶层 `ZiweiChart` 结构修复保持有效。
- D 侧 `ZiweiEngine.compute()` 和 `ZiweiSolarAdapter.compute()` 保持 12 宫、命身宫和规则字段。
- D 侧 blind canonical 输入/production gate 代码不被 E 侧旧版本覆盖。
- 生产 import 根保持 `D:\shuntian\src\tongshu`。

### 清理

只清理本次测试生成的 Python/pytest 缓存，具体路径见：

```text
docs/audit/SHUNTIAN_CLEANUP_PATHS_20260928.txt
```

没有删除既有 `blind/`、`blind_engine/`、`engines/`、`blind_evidence/`、`blind_seg/`、`archive/ziwei_legacy/`，因为这些路径可能有外部调用、用户证据或历史 provenance，不能仅凭重复哈希删除。

## 4. 测试结果

### 紫微

```text
250 passed, 32 subtests passed in 30.58s
```

覆盖核心、合同、垂直切片、扩展、cross validation、方法、宫位、规则图、三合和钦天门。

### Bazi/河洛上下游

```text
43 passed in 7.57s
```

覆盖：

```text
test_b02_late_zi_golden.py
test_canonical_bazi_contract.py
test_heluo_context.py
test_heluo_canonical.py
```

### Blind

```text
148 passed, 7 subtests passed, 3 failed
```

3 个失败均来自现有 `blind_tests/test_blind_rules/test_rule_graph.py` 遗留契约：

- `backend/data/rules/BL-sample.json` 规则样本/路径与当前规则库不一致，加载数量为 0 而测试期待 18；
- `MatchContext` 当前没有测试期待的 `zuo_gong_methods` 字段；
- `get_rule("BL-ZG-001")` 因样本未加载返回空。

这些失败未由本次 E/D 迁移造成，且本次没有通过修改测试期望、恢复未知规则文件或改变规则语义来掩盖。

### 模块归属

```text
blind  = D:\shuntian\src\tongshu\engines\blind_bazi_engine.py
ziwei  = D:\shuntian\src\tongshu\engines\ziwei_engine.py
adapter= D:\shuntian\src\tongshu\engines\ziwei_adapter.py
ziping = D:\shuntian\src\tongshu\reasoning\ziping_v3\engine.py
```

## 5. 保护边界

本次没有覆盖或清理：

- Golden Dataset / accuracy 数据；
- `data/canonical/`；
- 数据库；
- `deploy/entry.py`、`run_server.py`；
- 八字、Ziping、河洛算法；
- 紫微 Canonical 冻结规则；
- 用户既有未跟踪/未提交/删除工作区路径。

## 6. 后续遗留项

- 盲派规则图测试需要单独修复“规则样本路径 + `MatchContext.zuo_gong_methods`”契约；这不是本次迁移范围。
- 根级 `blind/` 与 `blind_engine/blind/`、证据镜像目录和根级 `engines/` 仍存在；已登记但未删除，需单独完成外部调用者确认后再清理。
- E 侧新一代 blind/ziwei 架构若要接入，必须另做 API 适配、垂直测试和生产入口迁移，不能直接复制。

## 7. 本次提交白名单

计划只提交以下本次路径：

```text
docs/audit/SHUNTIAN_MIGRATION_BASELINE_20260928.txt
docs/audit/SHUNTIAN_PREEXISTING_STATUS_20260928.txt
docs/audit/SHUNTIAN_PREEXISTING_UNTRACKED_20260928.txt
docs/audit/SHUNTIAN_PREEXISTING_WORKTREE_20260928.patch
docs/audit/SHUNTIAN_BLIND_ZIWEI_FILE_MAP_20260928.md
docs/audit/SHUNTIAN_CLEANUP_PATHS_20260928.txt
docs/audit/SHUNTIAN_BLIND_ZIWEI_MIGRATION_REPORT_20260928.md
docs/audit/ZIWEI_ENGINE_REPAIR_REPORT_20260928.md
tests/test_ziwei_chart_contract.py
src/tongshu/engines/ziwei_engine.py
src/tongshu/engines/ziwei_adapter.py
```

不执行 `git add -A`、`git add .`，不 push，不发布。
