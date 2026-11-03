# 断事准确性验证方案（DuanShi Accuracy Validation · 第四重闸门）

> 版本：v1.0 ｜ 状态：**强制（HARD GATE）** ｜ 关联：`RULE_ENTRY_VALIDATION_SPEC.md`
> 定位：本方案是断言规则进库校验的**第四重闸门（实证验证）**，回答"这套断事规则到底准不准、能否成立"。
> 原则：**成立与否是验证出来的，不是推断出来的**。每条规则都是"可证伪的假设"，未通过数据验证一律不得进 active。

---

## 0. 当前验证资产（backend 已有，勿重复造轮子）

| 资产 | 路径 | 作用 |
|---|---|---|
| 盲测数据集 | `dataset/accuracy/blind/blind_candidates.json`、`blind_manifest.json`、`blind_prediction_results.json` | 不带答案的盲测 |
| 专家 Pilot 评分 | `dataset/accuracy/expert_pilot/ai_ratings.json(_v3)`、`frozen_sample.json`、`rater_registry.json`、`cases/SAMPLE_001-009_BLIND.md` | 独立评分（7 维：state/opportunity/risk/remediation/action/temporal/evidence，0-2/维，0-14 总分，归一 0-100） |
| 仅证据集 | `dataset/accuracy/evidence_only/historical_evidence.json` | 纯事实证据对照 |
| Golden cases | `tests/test_s5_golden_cases.py`、`test_s6_golden_expansion.py`、`test_golden_jixiaolan.py`、`test_k2g_golden.py` | 已知答案真题 |
| 命理盲测 | `tests/test_mingli_bench_blind.py` | 命理方向盲测 |
| 年度事件评估 | `tests/test_annual_event_evaluator.py` + `src/` 的 `annual_event_evaluator.py` | 流年事件评分/排序 |
| 现有基线 | **27.3%**（单一八字岁运基线） | 每个新规则/新体系必须证明超过它才有增量 |
| 数据集配置 | `dataset/accuracy/dataset_config.json`（30 人 / 100-150 事件 / A2-Pilot） | 规模与阶段 |

---

## 1. 验证目标（可证伪假设）

**核心命题**：从「空空道人」等讲师资料提炼的断事规则，在真实/真题命例上，是否在**事件主题、方向、时间窗口**三个维度产生**高于随机基线的稳定信号**？

- 假设 H0（不成立）：规则命中率 ≈ 随机基线 → 规则**淘汰**或回 draft
- 假设 H1（成立）：规则命中率 > 基线 + 显著增量 → 规则可进 validated

---

## 2. 数据分层（按证据强度排序）

```
Tier 1  完全一致/高度相似八字 + 已知事件（双胞胎/同八字自然实验）
Tier 2  同日出生、不同时辰/地区案例
Tier 3  历史/公众人物（金大侠/纪晓岚等已入库者）
Tier 4  Golden Dataset（已知答案）
Tier 5  真实用户匿名时间线（仅示例）
```
- 命例只提供 `birth_datetime + birth_location + current_living_location`（遵守 P1 输入边界，不要求事件信息）。
- 答案与命例**严格分离**：盲测时预测侧看不到答案。

---

## 3. 单规则验证流程（候选 → 通过/淘汰）

每条候选规则走：

```
候选规则(draft)
   │ ①来源一致  ②可计算字段  ③冲突裁定（前三重闸门）
   ▼
  进入验证集（登记 rule_id + 触发条件）
   │
  ④ 单元测试：构造命例，规则触发是否符合预期（trigger==预期）
   │
  ⑤ Golden/真题命中：对已知答案命例，规则预测是否命中事件主题/方向/时间
   │
  ⑥ 盲测：预测侧看不见答案，比较命中率 vs 基线
   │
  ⑦ 消融：全量 vs 去掉本规则，看指标是否下降（下降=有增量）
   │
  ⑧ 交叉验证：子平×盲派×紫微×河洛 对同一事件是否收敛
   ▼
  ├─ 全部通过 ─▶ validated
  └─ 任一不通过 ─▶ 回 draft（保留证据，标注失败原因）
```

---

## 4. 盲测协议（Anti-bias）

- 样本随机抽取，**预测先于答案暴露**（pre-registration）。
- 含对照组（随机基线 / 空模型）。
- 结果写入 `blind_prediction_results.json`，不允许事后修改。
- 多评分者（`rater_registry.json`），独立评分，取一致性。
- 控 selection / confirmation / survivorship bias：不用"成功名人吻合"当证据，用随机+对照。

---

## 5. 指标与通过阈值（保守，宁缺毋滥）

| 指标 | 定义 | 通过阈值（建议） |
|---|---|---|
| 命中率(Recall) | 命中事件数 / 实际事件数 | ≥ 基线 + 5pp（即 ≥32.3%，随基线更新） |
| 方向准确率 | 正向/负向判断对的事件占比 | ≥ 55% |
| 时间窗口准确率 | 年份/时段命中 | ≥ 45% |
| Precision | 断言的事件中真实发生占比 | ≥ 60% |
| **False Positive Rate** | 错误断言率（最重要的红线） | ≤ 40%（防"什么都敢断"） |
| Ablation 增量 | 加规则后指标变化 | 必须 > 0（纯堆数量不算） |
| Cross-system 收敛 | ≥2 独立体系同向支持 | 收敛时 confidence 提升；冲突时不硬判 |
| Expert Pilot 归一化分 | 0-100 | ≥ 60 |

- **单条规则不达阈值 → 淘汰或回 draft**，不得以"多规则叠加能救"为由硬留。
- 每个体系（子平/盲派/紫微/河洛）**必须独立达到阈值**，才能成为 Signal Producer；达不到就标记 INSUFFICIENT_EVIDENCE，不强行参与评分。

---

## 6. 消融实验（证明增量，而非堆规则）

```
Model A  只排盘（不断事）
Model B  + 八字断事
Model C  + 盲派
Model D  + 紫微
Model E  + 河洛
Model F  + 交叉验证融合
```
逐级比较命中率。**只有上一级 < 下一级，才证明该层有增量信息（incremental predictive value）**。增量不明显的一层标记为"待验证"，不列为产品能力。

---

## 7. 交叉验证（多体系收敛协议）

- 四体系**独立计算 → 统一 EVENT_SIGNAL → 交叉裁定**，禁止互相反向修改原始结果。
- 裁定结果分为：`同向收敛(STRONG/MODERATE)` / `冲突(CONFLICT)` / `单体系` / `缺失(NONE)`。
- 冲突时不强行平均，进入 Conflict State 寻找原因（时间尺度/事件性质/收入vs支出/大运背景）。

---

## 8. 通过标准（进库状态机）

```
draft ──▶ review（①②③ 通过）
review ──▶ validated（④⑤⑥⑦⑧ 通过）
validated ──▶ active（评审确认无副作用）
任一步失败 ──▶ 回 draft 或 deprecated（保留失败证据供复盘）
```
- 未达阈值的规则**只能**停留在 draft / review，作为 INSUFFICIENT_EVIDENCE，不得输出给用户当结论。

---

## 9. 执行路线（对接 Hermes）

1. **快照基线**：先跑现有 Golden/盲测，冻结当前命中率（含 27.3% 八字岁运基线）→ 基线快照。
2. **候选规则登记**：把《空空道人候选规则清单.md》32 条候选按本方案 ③ 可计算性登记，剔除不可计算项。
3. **单规则验证**：逐条走④⑤⑥⑦⑧，产出每条的命中率/方向/时间/消融/收敛证据表。
4. **汇总报告**：生成《断事规则验证报告》——哪些成立、哪些淘汰、哪些待补字段。
5. **成立的才进 validated**，按 RULE_ENTRY_VALIDATION_SPEC 走完生命周期。

> 红线：禁止为"涨准确率"用 bug 撑数；禁止把单体系测试通过宣传为多体系正确；禁止隐藏矛盾证据。

---

## 附：产出物
- 本方案 → `backend/docs/DUANSHI_ACCURACY_VALIDATION.md`
- 待生成：每候选规则的验证证据表（rule_id × 指标）、断事规则验证总报告
