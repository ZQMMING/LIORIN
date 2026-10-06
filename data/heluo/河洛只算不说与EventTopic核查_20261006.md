# 河洛「只算不说」与 EVENT_TOPIC 声明核查

日期：2026-10-06
支线：`feature/heluo-event-topic-claim-audit-20261006`

## 〇、本轮结论：上一轮的建议（接线 evidence/frozen_state/diagnosis）是错的

原计划接线 `frozen_state` + `evidence_producer` + `diagnosis_rule_graph`。
动手前查接入点，发现前提不成立，故**未执行接线**，改为查清真相。

## 一、河洛目前是「只算不说」引擎

实测走完整 `pipeline.run()`：

| 项 | 实测值 |
|---|---|
| `cross_result.by_engine` 键 | `['ZI_PING', 'ZI_WEI']` —— **HE_LUO 完全缺席** |
| ZI_PING 证据数 | 7 |
| ZI_WEI 证据数 | 1 |
| `coverage.total_assertions` | 3 |
| signals 各层 source_engine | 全部 `ZI_PING`（命中规则全为 `ZPZ-*`） |

即：**河洛算出了完整卦象，但没有一条河洛证据进入跨域推理**。

### 为什么接不了

1. `HeLuoEvidenceProducer` 产出的 `EngineEvidence` **没有下游**。
   `ComputeStage._orchestrate_signals` 是**内联手搓** `EngineEvidence`
   （十神、命主星、四柱信号），再喂 `CrossDomainOrchestrator`；
   producer 类只是另一条没走的路。直接把 producer 输出塞进去，
   会改变 `by_engine` 构成与 `coverage` 统计，进而影响
   `_alignment_status`（ALIGNED/PARTIAL/INSUFFICIENT 判定）与各覆盖门禁。

2. `BaziEvidenceProducer` / `ZiweiEvidenceProducer` **同样无任何调用点**——
   整套 `EngineEvidence` 产出架构（P1.2-A）在三个引擎里都是悬空的。
   这不是河洛独有问题。

3. `diagnosis_rule_graph.build_diagnosis()` 需要 `evidences + signals + frozen_state`，
   而河洛当前产出 **0 条 signal**，输入本就缺一半。

## 二、21 条河洛 HL 规则为何一条都不生效——是治理，不是缺陷

规则库 `backend/data/rules/HL-1*.json` 共 **21 条**，条件字段为
`heluo_benming_guawuxing` / `heluo_dishu_youyu` / `heluo_birth_season_unfavorable` 等
`heluo_*`——**接入方向本身是对的**，`extract_heluo_context()` 也确实把河洛字段
注入了 `RuleContext`。

但它们一条都不生效，两道门：

1. **status 门**：21 条 **全部 `draft`**，而
   `EXECUTABLE_STATUSES = ("validated", "active")`
   （matcher.py:120，DECISION-010：防止 AI 自动静默激活规则）→ 全部跳过。
2. **层门**：其中 11 条 `applies_to_layers: ["EVENT_TOPIC"]`，
   而 `SIGNAL_LAYER_ORDER = ("BASELINE","CYCLE_CONTEXT","DAILY_ACTIVATION")`
   不含 EVENT_TOPIC → 连求值路径都进不去。
   另 10 条（HL-112~121）是 BASELINE 层，**只被 status 门挡住**。

> **不得为了让规则生效而改 status。** 激活规则是治理决定
> （需证据引用校验），不是技术修复。

## 三、查实缺陷一：EVENT_TOPIC 求值器根本不存在

`matcher.py` 多处注释把使用者导向一个**不存在的模块**：

| 原注释 | 事实 |
|---|---|
| 「The dedicated evaluator lives in `tongshu.reasoning.event_topic`」 | `src/tongshu/reasoning/event_topic.py` **不存在** |
| 「EVENT_TOPIC 层字段（婚姻/健康断事, EventTopicEngine 提供）」 | 同上 |
| 「EVENT_TOPIC-only ops … handled by EventTopicEngine._eval_leaf」 | 同上 |
| 异常信息「use EventTopicEngine instead」 | 指向不存在的引擎 |
| `canonical/producer.py:6` 提及 `annual_event_evaluator.py` | 该文件**不存在** |

这类注释比没有更糟——会把后来者引向幻影模块。
EVENT_TOPIC 求值器属**待建**，而非「存在于别处」。

**不影响现网正确性**：现网 EVENT_TOPIC 规则全部 draft，本就在门禁外。

## 四、查实缺陷二：信号引擎归属只认 `ZW-` 前缀

`compute_stage.py` 原代码：

```python
raw_eng = "ZI_WEI" if any(str(r).startswith("ZW-") for r in rule_refs) else "ZI_PING"
```

**其余一律归 `ZI_PING`**。一旦 `HL-`（河洛）或盲派规则命中，
就会被错记到子平名下，污染 `CrossDomainResult.by_engine` 的归属与 coverage 统计。

改为显式前缀表：

```python
_RULE_PREFIX_ENGINE = {"HL-": "HE_LUO", "ZW-": "ZI_WEI"}
```

只登记**能确证归属**的前缀，未登记者沿用原默认 `ZI_PING`，不做猜测。
`HLT-`（健康类，17 条，active）与 `HL-` 是不同前缀，不会互相误判——
已加测试钉住这一点。

**当前零行为影响**：HL 规则全为 draft，该分支今天走不到。属消除潜在缺陷。

## 五、附带查出的既有问题（未处理）

- `tests/test_rule_lifecycle.py::test_golden_rule_refs_resolve_and_executable`
  **NameError: `VIRTUAL_RULE_REFS` is not defined**，基线即红。
  该文件是规则生命周期治理审计，坏掉意味着这项审计长期没跑成。
  修复需先理解 `VIRTUAL_RULE_REFS` 语义，超出本轮范围，未动。

## 六、测试

新增 `tests/heluo/test_heluo_event_topic_claims.py`（12 项），锁定：
前缀表归属、HLT/HL 不混淆、21 条 HL 规则确为 draft、HL 规则确实引用
`heluo_*` 字段、`event_topic.py` 与 `annual_event_evaluator.py` 确实不存在、
matcher 源码与异常信息不再指向幻影引擎、EVENT_TOPIC 不在层序内。

**区分度已验证**：把 `"HL-": "HE_LUO"` 临时改回 `"ZI_PING"` 后，12 项中 2 项转红。

严格同集合回归（含 `test_matcher.py` / `test_rule_engine.py`）：

| | 结果 |
|---|---|
| 改动前 | 671 passed / 5 failed（**全部落在新测试文件内**） |
| 改动后 | **676 passed / 0 failed** |

## 七、下一步建议（需用户裁决）

要让河洛真正「说话」，路径不是接线，而是：

1. **建 EVENT_TOPIC 求值器**（`tongshu.reasoning.event_topic`）——
   这是 11 条 HL 规则与全部 MAR/HLT/WLT/CRR/EDU 断事规则的共同前置。
2. **激活 HL 规则**（draft → validated）——需先补证据引用校验，属治理流程。
3. 在 1、2 之后，`extract_heluo_context` 已有字段才能真正产出信号，
   届时 HE_LUO 才会自然出现在 `by_engine` 里。

单接 `evidence_producer` 是**本末倒置**：没有信号就没有证据可产，
强行塞证据只会污染 coverage 与门禁判定。