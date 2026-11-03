# 顺天项目 User 裁决记录 — 2026-08-30

**裁决者**: User  
**裁决前状态**: Hermes TAKEOVER AUDIT PASS

---

## 一、T1 → T2 → T3 执行顺序

### T1: signal_engine 兼容性修复
- **目标**: 让 signal_engine 同时兼容 `produces_layer_output_template` 和 `produces_semantic_atoms` 两种格式
- **约束**: 不修改 Golden、不恢复旧投票/方向逻辑
- **验收**: 3个失败测试全部 PASS，且现有1615个PASS不受影响

### T2: strength_engine 审计与隔离
- **目标**: 确认所有生产调用，将 wang_score 隔离为 Legacy Reference
- **约束**: 不删除代码，只做隔离（标记 deprecated）
- **验收**: 无生产路径调用 wang_score >= 2.0 判定身强

### T3: Primitive 小闭环验证
- **目标**: 拿 20-50 条真实五经证据做 Evidence → Primitive → Condition → Local Judgment 闭环
- **约束**: **不先改 schema**，先验证 Primitive 字段设计能否表达原典，再正式冻结
- **验收**: 小闭环通过，Primitive schema 设计文档通过裁决

---

## 二、关键裁决细节

1. **T3 不先改 schema**：先拿真实证据验证 Primitive 字段设计，再冻结
2. **Cross-Validation 阶段4已完成**：commit 664439c (P0-3.1) 已做50条跨经典抽样，Hermes 报告口径需校准
3. **T1 不恢复旧方向逻辑**：produces_semantic_atoms 转 Signal 时需要新的 direction 推导规则，不能用旧的

---

## 三、校准说明

| 问题 | 实际情况 | 说明 |
|------|----------|------|
| P0-3.0 报告中"阶段4未执行" | 阶段4已在 P0-3.1 完成 | commit 664439c 已做50条跨经典抽样验证 |
| Primitive 字段缺失 | rules schema 确实无 primitive 字段 | T3 小闭环重点验证这个问题 |
