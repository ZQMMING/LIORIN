# P0-5 工作计划：五经 Local Judgment 第一批真实生产规则

**目标**: 使用已验证的 Authorized Primitive 做第一批真实 Local Judgment

---

## 一、背景

P0-4.9 确认：
- support_ratio → CURRENTLY_NON_PRODUCTION（"二三人"语义不确定）
- wu_ji_pressure → CURRENTLY_NON_PRODUCTION（"愁逢"语义不明确）

**当前可生产状态**
- T2 🟢
- T3 🟢
- P0-3.4 ~ P0-3.9 🟢
- P0-4.1 ~ P0-4.9 🟢
- Canonical Feature 🟢
- Derivable Feature 🔴 当前不可生产
- Semantic Only 🔴 不可伪装计算事实
- Condition Graph 🟢 技术能力
- Authorization 🟢
- Local Judgment 🟢 已有基础
- Composite Judgment 🔒 暂缓
- 最终身强身弱 🔒 暂缓

---

## 二、第一批可生产 Primitive

基于 P0-3.7 授权核验结果（EXPLICIT=4）和 P0-4.7/4.8 验证：

| Primitive | Feature | 类型 | 状态 |
|-----------|---------|------|------|
| 得令 | de_ling | CANONICAL_FEATURE | ✅ 可生产 |
| 得地 | de_di | CANONICAL_FEATURE | ✅ 可生产 |
| 得势 | de_shi | CANONICAL_FEATURE | ✅ 可生产 |

**排除项**
- ❌ 身强/身弱总判断（Composite Judgment）
- ❌ support_ratio（CURRENTLY_NON_PRODUCTION）
- ❌ wu_ji_pressure（CURRENTLY_NON_PRODUCTION）

---

## 三、验证范围

### 只做局部、可验证、低歧义的问题

✅ 可以：
- 某状态是否成立？
- 某关系是否成立？
- 某原典条件是否满足？
- 某制化条件是否存在？

❌ 不做：
- 综合所有因素判断身强/身弱
- 多条件复杂的 Composite Judgment
- 需要人为权重的判断

---

## 四、测试样本

选择真实命例，验证：
1. de_ling=True 时，原典条件是否满足
2. de_di=True 时，原典条件是否满足
3. de_shi=True 时，原典条件是否满足

---

## 五、输出物

1. `docs/P0_5_PRODUCTION_RULES.md` - 生产规则定义
2. `scripts/p0_5_local_judgment_replay.py` - Replay 验证脚本
3. `data/p0_5_judgment_result.json` - 验证结果
4. `docs/P0_5_VERIFICATION_REPORT.md` - 验证报告

---

## 六、禁止事项

❌ 不得进入 Composite Judgment  
❌ 不得做身强/身弱综合判断  
❌ 不得扩大 Feature 数量  
❌ 不得假设"二三人"=支持数≥2  
❌ 不得假设"愁逢"有明确阈值

---

## 七、成功标准

✅ 使用真实命例验证  
✅ 只使用 CANONICAL_FEATURE  
✅ 只使用已授权 Primitive  
✅ 产生明确的 Local Judgment  
✅ 无"伪确定性"判断

---

**开始执行**
