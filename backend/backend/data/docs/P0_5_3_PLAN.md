# P0-5.3 工作计划：Local Judgment Replay（CLASSICAL_EXPLICIT 专用）

**目标**: 只用 CLASSICAL_EXPLICIT + VERIFIED 规则做 Local Judgment Replay

---

## 一、背景

P0-5.2 确认：
- de_ling → CLASSICAL_EXPLICIT（生产层）
- de_di/de_shi → ENGINEERED_THRESHOLD（研究层，禁止生产）

**核心约束**：
> P0-5.3 不能把 de_di >= 2 / de_shi >= 2 混进 Classical Replay

---

## 二、测试计划

### 1. 只使用 CLASSICAL_EXPLICIT 条件
- de_ling = True（得令者旺）
- 来源：滴天髓·得令者旺

### 2. 验证规则
- 如果 de_ling=True → PASS（得令条件满足）
- 如果 de_ling=False → FAIL（得令条件不满足）
- 不输出"身强/身弱"综合判断

### 3. 禁止事项
- ❌ 不混合 ENGINEERED_THRESHOLD
- ❌ 不做身强/身弱综合判断
- ❌ 不跨进 Composite Judgment

---

## 三、实现计划

1. 修改测试脚本，只保留 CLASSICAL_EXPLICIT 条件
2. 使用真实命例（P0-5 的 4 个）
3. 验证 Authorization Gate 只放行 CLASSICAL_EXPLICIT
4. 输出结果保存 JSON

---

## 四、关键验证点

1. de_ling=True 时产生 PASS ✅
2. de_ling=False 时产生 FAIL ✅
3. de_di/de_shi 不进入测试 ❌
4. 无"伪确定性"综合判断 ✅

---

**请 GPT 裁决是否批准此计划**
