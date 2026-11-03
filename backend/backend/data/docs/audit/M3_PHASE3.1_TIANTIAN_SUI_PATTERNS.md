# M3 Phase 3.1 滴天髓格局生产计划

**批准时间**: 2026-08-31  
**启动Commit**: 19128a6  
**状态**: 🟢 待启动

---

## 背景

用户裁决确认：
- V1.4基线清理完成（1782 passed, 0 failed, 0 xpassed）
- 批准进入M3 Phase 3
- 强调：P0/P1工程治理通过 ≠ 断言引擎准确性通过
- 要求：第一批20条断言作为独立生产/审计批次

---

## 生产范围

**经典**: 《滴天髓》格局篇  
**数量**: 20条高置信断言  
**类型**: 格局判断（正格/从格/化气格等）

---

## 生产流程

```
【STEP 1】原典定位
  ↓
  滴天髓·格局篇原文定位
  提取classical_source/volume/chapter/passage_id/raw_text/context

【STEP 2】Evidence提取
  ↓
  原文+注释分层
  区分ORIGINAL_TEXT/ORIGINAL_COMMENTARY/LATER_COMMENTARY

【STEP 3】Primitive提炼
  ↓
  定义信号（如：月令透干、日主根气等）
  每个Primitive必须有classical_source绑定

【STEP 4】Condition构建
  ↓
  触发条件定义
  使用CanonicalState + Condition Evaluator

【STEP 5】Evaluator编码
  ↓
  生产代码实现
  不得调用evaluate_strength（LEGACY/RESEARCH_ONLY）

【STEP 6】Local Judgment
  ↓
  断言输出
  必须包含完整trace

【STEP 7】Claude审计
  ↓
  独立验证
  检查：原典定位、Evidence完整性、Primitive准确性、Condition合理性

【STEP 8】GPT裁决
  ↓
  每5条一批
  裁决是否授权进入Production

【STEP 9】测试写入
  ↓
  验证用例编写
  1782+新测试，必须全部通过

【STEP 10】Commit记录
  ↓
  完整追溯链
  包含：原典→证据→断言→审计→裁决
```

---

## 质量门槛

### 单条断言标准

```
✅ 原典定位：滴天髓格局篇具体章节+原文定位
✅ Evidence完整：原文+注释+上下文
✅ Primitive定义：信号明确，有classical_source绑定
✅ Condition合理：触发条件清晰，符合原典语义
✅ Evaluator准确：生产代码正确实现Condition
✅ Local Judgment完整：断言输出包含完整trace
✅ Claude审计通过：独立验证无问题
✅ GPT裁决授权：每5条一批，通过裁决
✅ 测试覆盖：对应测试用例全部通过
```

### 批量标准（每5条）

```
✅ Claude独立审计：5条全部通过
✅ GPT裁决：授权进入Production
✅ 测试通过：1782+新测试，0 failed
✅ 无Legacy回流：verify_legacy_calls.py 0
✅ 无XPassed：pytest --tb=short 0 xpassed
```

---

## 禁止行为

```
🔴 禁止批量灌库（无审计生产）
🔴 禁止用Similarity/AE匹配替代原典Evidence
🔴 禁止恢复Legacy调用
🔴 禁止使用wang_score阈值
🔴 禁止自写自审
🔴 禁止跳过Claude审计
🔴 禁止跳过GPT裁决
```

---

## 执行顺序

```
第1批（5条）→ Claude审计 → GPT裁决 → 批准
第2批（5条）→ Claude审计 → GPT裁决 → 批准
第3批（5条）→ Claude审计 → GPT裁决 → 批准
第4批（5条）→ Claude审计 → GPT裁决 → 批准

总计：20条，分4批，每批5条
```

---

## 交付物

### 每批交付

```
src/tongshu/assertion/classics/ditian_sui/
  ├── patterns.py          # 生产代码
  ├── evidence/            # Evidence目录
  │   └── 001-正格.json    # 单条断言Evidence
  ├── audit/               # Claude审计记录
  │   └── 001-claude-audit.md
  └── ruling/              # GPT裁决记录
      └── 001-gpt-ruling.md

tests/test_di_tian_sui_patterns.py  # 测试用例
```

### 完整追溯

```
每条断言必须可追溯：
滴天髓·格局篇 → Evidence → Primitive → Condition → Evaluator → Judgment → Audit → Ruling
```

---

## 启动条件

✅ V1.4基线完全干净（1782 passed, 0 failed, 0 xpassed）  
✅ 治理机制已确立（Claude审计+GPT裁决）  
✅ 硬约束已锁定（禁止Legacy/Strength新公式/无审计生产）  
✅ 用户裁决确认（19128a6）

**可以启动M3 Phase 3.1滴天髓格局生产。**

---

等待Herme调度指令。