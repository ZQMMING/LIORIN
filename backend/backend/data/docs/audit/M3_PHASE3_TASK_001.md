# M3 Phase 3.1 - 滴天髓格局生产任务单

---

## 基本信息

**Task ID**: M3-P3.1-DTS-GEJU  
**Phase**: M3 Phase 3.1  
**模块**: 滴天髓·通神论·格局篇  
**优先级**: P0（第一批次）  
**目标数量**: 20条断言  
**审计要求**: 逐条Claude审计 + 每5条GPT裁决

---

## 生产范围

### 原典来源
- **经典**: 滴天髓（《天干题咏》+《地支汇考》+《通神论》）
- **章节**: 格局篇（Geju）
- **理论**: 正格判定、格局成败、清浊判断

### 断言列表（20条）

#### 正格判定（10条）
1. DTS-GEJU-001: 正官格成立条件
2. DTS-GEJU-002: 偏官格成立条件
3. DTS-GEJU-003: 正印格成立条件
4. DTS-GEJU-004: 偏印格成立条件
5. DTS-GEJU-005: 食神格成立条件
6. DTS-GEJU-006: 伤官格成立条件
7. DTS-GEJU-007: 财星格成立条件
8. DTS-GEJU-008: 比肩格成立条件
9. DTS-GEJU-009: 劫财格成立条件
10. DTS-GEJU-010: 日主旺衰与格局关系

#### 格局成败（10条）
11. DTS-GEJU-011: 正官格成败条件
12. DTS-GEJU-012: 偏官格成败条件
13. DTS-GEJU-013: 正印格成败条件
14. DTS-GEJU-014: 食神格成败条件
15. DTS-GEJU-015: 伤官格成败条件
16. DTS-GEJU-016: 财星格成败条件
17. DTS-GEJU-017: 格局破败条件
18. DTS-GEJU-018: 格局救应条件
19. DTS-GEJU-019: 格局清纯标准
20. DTS-GEJU-020: 格局混杂标准

---

## 执行步骤

### Step 1: 原典检索（预计10分钟）
- [ ] 定位《滴天髓·通神论》格局相关章节
- [ ] 提取20条原始原文
- [ ] 标注passage_id和text_layer

### Step 2: Primitive构建（预计20分钟）
- [ ] 为每条断言构建Primitive Assertion
- [ ] 定义Condition Evaluator逻辑
- [ ] 添加Evidence引用

### Step 3: Claude审计第1批（1-5条）（预计15分钟）
- [ ] 提交5条断言进行独立审计
- [ ] 修复审计发现的问题
- [ ] 获得Claude APPROVED

### Step 4: GPT裁决第1批（预计5分钟）
- [ ] 提交审计结果请求GPT裁决
- [ ] 获得GPT APPROVED

### Step 5: 重复Step 3-4（第6-10条、11-15条、16-20条）

### Step 6: 测试添加（预计15分钟）
- [ ] 为20条断言添加验证测试
- [ ] 确保Condition Evaluator逻辑正确
- [ ] 运行测试套件确认1778+20 passed

### Step 7: Commit + 通知（预计5分钟）
- [ ] 提交commit
- [ ] 通知Hermes等待下一阶段

---

## 验收标准

### 必须满足
- ✅ 20条断言全部通过Claude审计
- ✅ 每5条断言获得GPT裁决
- ✅ 原典Evidence链完整（classical_source + passage_id + raw_text）
- ✅ text_layer正确标注
- ✅ Condition Evaluator逻辑可验证
- ✅ 测试覆盖完整
- ✅ 无Legacy调用回流
- ✅ 无wang_score阈值使用

### 禁止行为
- ❌ 恢复evaluate_strength生产调用
- ❌ 恢复wang_score阈值判定
- ❌ 使用相似语义匹配替代原典
- ❌ 无审计批量导入
- ❌ 用Assertion反推Canonical State

---

## 交付物

1. **data/canonical/dts_geju_001_020.json**: 20条断言数据
2. **tests/test_dts_geju_001_020.py**: 验证测试
3. **docs/audit/CLAUDE_REVIEW_M3_P3.1.md**: Claude审计记录
4. **docs/audit/GPT_RULING_M3_P3.1.md**: GPT裁决记录
5. **docs/audit/M3_PHASE3_PROGRESS.md**: 进度报告

---

## 时间节点

- **开始时间**: 立即
- **预计完成**: 2小时
- **审计频率**: 每5条断言
- **裁决频率**: 每批完成后

---

**任务单创建完毕。请立即开始原典检索。**