# jishen_state 字段迁移方案草案（2026-09-16，待 Human 批准后执行）

> **状态**：DRAFT — 仅方案，未进入实现。
> **Human 裁决（2026-09-16）**：jishen_state 拆字段方向 APPROVED_SPLIT（原因：同音异义字段污染——吉神 ji shén / 忌神 jì shén 拼音相同但古典概念完全不同；**不允许依靠拼音字段作为 canonical identifier**）。
> **执行限制（Human 明令）**：暂不能删除旧字段 / 修改规则引用 / 修改 evidence 绑定 / 自动迁移生产规则。

## 一、问题现状

`jishen_state` 当前承载两个完全不同概念：

| 消费规则 | 出处 | 实际概念 | 值域 |
|---|---|---|---|
| CAND-DTS-032/033 | DTS-027-001 隱顯衆寡論「吉神太露，起爭奪之風；凶物深藏，成養虎之患」 | **吉神**（喜用神）显隐/位置状态 | 太露 / 深藏 |
| CAND-DTS-041 | DTS-033-011 何知章「何知其人凶？忌神展轉攻」 | **忌神**（忌用神）攻击/作用状态 | 展轉攻 |

## 二、目标字段设计（二选一，Human 定名）

**方案 A（推荐）**：
- 吉神：`auspicious_deity_state`（值域：太露 / 深藏）
- 忌神攻击：`jishen_attack_state`（值域：展轉攻）

**方案 B**：
- 吉神：`jishen_good_state`（值域：太露 / 深藏）
- 忌神攻击：`jishen_attack_state`（值域：展轉攻）

共同原则：**canonical identifier 用语义全名，不用拼音缩写**；忌神侧统一用 `jishen_attack_state`（忌神作用/攻击状态）。

## 三、alias 映射方案（迁移期双写）

```
旧字段（当前）           →  新字段（目标）
jishen_state（032/033）  →  auspicious_deity_state   (或 jishen_good_state)
jishen_state（041）      →  jishen_attack_state
```

迁移期策略：
1. enum_registry 注册新枚举（PENDING）：`dts_auspicious_deity_state`、`dts_jishen_attack_state`
2. state.py **双写**：旧 `jishen_state` 与两个新字段同时输出（旧字段标 deprecated）
3. 规则引用逐条迁移：032/033 → 新吉神字段；041 → jishen_attack_state
4. 旧 `jishen_state` 字段退役（删除），alias 记录保留在 enum_registry notes

## 四、涉及范围（迁移清单）

| 对象 | 路径 | 动作 |
|---|---|---|
| enum_registry | governance/enum_registry.json | 注册 2 新枚举（PENDING）+ 旧 jishen_state 标 deprecated 待删 |
| state.py | engines/ditiansui/calculation/state.py | 双写（待批） |
| 规则 rules.dts.jsonl | CAND-DTS-032/033/041 | 改引用字段（待批） |
| 测试 | test_zhenjia_yingxian.py | 断言字段更新（待批） |
| 审计口径清单 | docs/DTS_态势派生_待验证口径清单.md | 同步（待批） |

## 五、验证点（迁移完成后）

- [ ] enum_registry 无拼音缩写 canonical id（jishen_state 删除或仅留 deprecated 记录）
- [ ] 032/033 消费新吉神字段且仅匹配 太露/深藏
- [ ] 041 消费 jishen_attack_state 且仅匹配 展轉攻
- [ ] 无规则再消费旧 jishen_state
- [ ] 全量测试通过
- [ ] 隔离一致性校验通过

## 六、wuxing_state（PENDING-01b）——CONTINUE_PENDING，本方案不涉及

维持 `PENDING_SEMANTIC_AUDIT`：057/058「不戾正清和/濁亂偏枯」vs 074「和」——「和」是五行总状态（wuxing_state=和）还是 qing_zhuo_state 的一个结果，证据不足，不拆字段。
