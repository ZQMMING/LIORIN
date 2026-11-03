# M3 Phase 3.1 滴天髓格局生产计划

**批准时间**: 2026-08-31  
**首批数量**: 5条（独立批次）  
**状态**: 🟢 待启动

---

## 关键约束（用户裁决）

### 约束1: 禁止大Condition
❌ 不能把"格局判断"工程化成一个大Condition  
✅ 必须拆分为：原典→Evidence→Primitive A/B/C→Condition A/B/C→Local Judgment→Composite

### 约束2: 每个Composite必须有原典授权
❌ 不能工程推断 "A+B+C ⇒ 成格"  
✅ 必须证明原典说"A、B、C"且"原典授权Composite规则"

### 约束3: 验收标准升级
pytest PASS只是最后一道门，不是命理正确性的证明。  
每条必须同时证明：
- 原典是真的这样说
- Primitive没有扩大语义
- Condition能从Canonical State得出
- Evaluator没有偷偷重新计算命理
- Judgment没有超过原典授权
- 输出可追溯

---

## 生产流程（修正版）

```
【STEP 1】原典定位
  ↓
  滴天髓·格局篇具体章节+原文定位
  提取: classical_source/volume/chapter/passage_id/raw_text/context

【STEP 2】Evidence分层
  ↓
  原文层 (ORIGINAL_TEXT)
  注释层 (ORIGINAL_COMMENTARY)
  后世层 (LATER_COMMENTARY)
  每层独立标注

【STEP 3】Primitive拆分（核心！）
  ↓
  Primitive A: 最小信号单元（如：月令透干）
  Primitive B: 最小信号单元（如：日主根气）
  Primitive C: 最小信号单元（如：合化条件）
  每个Primitive必须有classical_source绑定

【STEP 4】Condition拆分（核心！）
  ↓
  Condition A: Primitive A的触发条件
  Condition B: Primitive B的触发条件
  Condition C: Primitive C的触发条件
  每个Condition必须从Canonical State得出

【STEP 5】Local Judgment
  ↓
  单条断言输出
  包含完整trace: 原典→Evidence→Primitive→Condition→Judgment

【STEP 6】Composite规则（必须有原典授权！）
  ↓
  原典明确说："若A且B则成格"
  或：原典明确说："若A且B且C则化气"
  不能工程推断！

【STEP 7】Claude审计
  ↓
  独立验证：
  - 原典定位是否准确
  - Evidence分层是否正确
  - Primitive是否最小语义单元
  - Condition是否可从Canonical State得出
  - Judgment是否超过原典授权
  - Composite是否有原典授权

【STEP 8】GPT裁决
  ↓
  每5条一批
  裁决：是否获得Production Authorization

【STEP 9】测试写入
  ↓
  验证用例：
  - 原典定位测试
  - Primitive拆分测试
  - Condition触发测试
  - Judgment边界测试
  - 无Legacy调用测试

【STEP 10】Commit记录
  ↓
  完整追溯链：原典→证据→断言→审计→裁决
```

---

## 首批5条断言范围

**经典**: 《滴天髓·格局篇》  
**类型**: 正格判定  
**数量**: 5条

### 候选断言（待用户确认）

| ID | 断言主题 | 原典章节 | 状态 |
|----|---------|---------|------|
| DTS-GEJU-001 | 月令透干成格 | 格局篇·论月令 | 待生产 |
| DTS-GEJU-002 | 日主有根成格 | 格局篇·论根气 | 待生产 |
| DTS-GEJU-003 | 合化成功条件 | 格局篇·论合化 | 待生产 |
| DTS-GEJU-004 | 破格救应机制 | 格局篇·论破格 | 待生产 |
| DTS-GEJU-005 | 从格成立条件 | 格局篇·论从格 | 待生产 |

---

## 质量门禁（升级版）

### 单条断言标准

```
✅ 原典定位：滴天髓格局篇具体章节+原文定位
✅ Evidence分层：原文层/注释层/后世层独立标注
✅ Primitive拆分：至少3个最小信号单元，每个有classical_source绑定
✅ Condition拆分：每个Condition可从Canonical State得出
✅ Local Judgment：不超原典授权范围
✅ Composite授权：有原典明确授权（非工程推断）
✅ Claude审计：独立验证通过
✅ GPT裁决：每5条一批，获得授权
✅ 测试覆盖：原典定位+Primitive拆分+Condition触发+边界测试
✅ 无Legacy调用：verify_legacy_calls.py 0
✅ 无XPassed：pytest --tb=short 0 xpassed
```

### 批量标准（每5条）

```
✅ Claude独立审计：5条全部通过
✅ GPT裁决：授权进入Production
✅ 测试通过：1782+新测试，0 failed
✅ 无Legacy回流：verify_legacy_calls.py 0
✅ 无XPassed：pytest --tb=short 0 xpassed
✅ 可追溯链：每条断言完整trace
```

---

## 禁止行为（铁律）

```
🔴 禁止把格局判断工程化为大Condition
🔴 禁止无原典授权的Composite规则
🔴 禁止Primitive语义扩大化
🔴 禁止用Similarity/AE匹配替代原典Evidence
🔴 禁止恢复Legacy调用
🔴 禁止使用wang_score阈值
🔴 禁止自写自审
🔴 禁止跳过Claude审计
🔴 禁止跳过GPT裁决
🔴 禁止批量灌库
```

---

## 交付物结构

```
src/tongshu/assertion/classics/ditian_sui/
├── patterns.py                    # 生产代码
├── evidence/
│   ├── 001-月令透干.json          # Evidence分层
│   ├── 002-日主根气.json
│   ├── 003-合化条件.json
│   ├── 004-破格救应.json
│   └── 005-从格条件.json
├── audit/
│   ├── 001-claude-audit.md
│   ├── 002-claude-audit.md
│   ├── 003-claude-audit.md
│   ├── 004-claude-audit.md
│   └── 005-claude-audit.md
└── ruling/
    ├── 001-gpt-ruling.md          # GPT裁决
    ├── 002-gpt-ruling.md
    ├── 003-gpt-ruling.md
    ├── 004-gpt-ruling.md
    └── 005-gpt-ruling.md

tests/test_di_tian_sui_patterns.py  # 测试用例
docs/audit/M3_PHASE3.1_BATCH_001.md  # 批次记录
```

---

## 执行顺序

```
批次1（5条）：
  DTS-GEJU-001 → Claude审计 → GPT裁决
  DTS-GEJU-002 → Claude审计 → GPT裁决
  DTS-GEJU-003 → Claude审计 → GPT裁决
  DTS-GEJU-004 → Claude审计 → GPT裁决
  DTS-GEJU-005 → Claude审计 → GPT裁决
  ↓
  汇总 → GPT最终裁决
  ↓
  授权进入Production
```

---

## 启动条件

✅ V1.4基线完全干净（1782 passed, 0 failed, 0 xpassed）  
✅ 治理机制已确立（Claude审计+GPT裁决）  
✅ 硬约束已锁定（禁止大Condition/禁止无授权Composite/禁止Legacy）  
✅ 用户裁决确认（3d48423）

**可以启动M3 Phase 3.1第一批5条滴天髓格局断言生产。**

---

等待Hermes调度指令。