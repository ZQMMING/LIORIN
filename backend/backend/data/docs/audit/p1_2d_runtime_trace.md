# P1.2-D: Real Bazi Runtime Vertical Slice — Production Call Trace

> 测试时间：2026-09-01
> 命例：纪晓岚（公历 1724-08-03 午时，男命）
> 状态：🟢 11/11 tests PASS

---

## 一、生产调用图

```
真实生产输入
    │
    ▼
BaziEngine.compute((1724, 8, 3, 11), gender="male")
    │
    ├── 输入: 公历时间 + 性别
    ├── 计算: 四柱排盘 + 十神推导 + 地支关系
    └── 输出: BaziChart (day_master=BING, 四柱=甲辰/辛未/丙戌/甲午)
    │
    ▼
BaziEvidenceProducer.produce(chart)
    │
    ├── Stage 1: 四柱天干地支（8 条 Evidence）
    │   ├── year_pillar: JIA/CHEN → EngineEvidence(ZP-STEM-YEAR, ZP-BRANCH-YEAR)
    │   ├── month_pillar: XIN/WEI → EngineEvidence(ZP-STEM-MONTH, ZP-BRANCH-MONTH)
    │   ├── day_pillar: BING/XU  → EngineEvidence(ZP-STEM-DAY,   ZP-BRANCH-DAY)
    │   └── hour_pillar: JIA/HAI → EngineEvidence(ZP-STEM-HOUR,  ZP-BRANCH-HOUR)
    │
    ├── Stage 2: 十神事实（4 条 Evidence）
    │   ├── year:  JIA → 偏印 (TEN_GOD_PIAN_YIN)
    │   ├── month: XIN → 正财 (TEN_GOD_ZHENG_CAi)
    │   ├── day:   BING → 比肩 (TEN_GOD_BI_JIAN)
    │   └── hour:  JIA → 偏印 (TEN_GOD_PIAN_YIN)
    │
    ├── Stage 3: 地支关系（可选，本例无冲）
    ├── Stage 4: 桃花（本例无）
    └── Stage 5: 五行失衡（本例无）
    │
    ▼ 共 ~12-16 条 EngineEvidence（纯事实，无方向/强度/置信度）
    │
    ▼
ten_gods.json 查表 → SemanticAtomMapper
    │
    ├── TEN_GOD_PIAN_YIN → SemanticAtom(
    │       atom_id="TEN_GOD_PIAN_YIN",
    │       semantic_keys=["SPECIAL_SKILL","INTUITION","UNCONVENTIONAL_KNOWLEDGE",...],
    │       domain_candidates=["GROWTH","CAREER","DECISION"],
    │       evidence_ref="EV-ZP-TG-YEAR-xxxx"   ← 追溯到 EngineEvidence.evidence_id
    │   )
    ├── TEN_GOD_ZHENG_CAi → SemanticAtom(...)
    └── TEN_GOD_BI_JIAN → SemanticAtom(...)
    │
    ▼ 无 direction，无 polarity
    │
    ▼
AssertionRuleLibrary.find_rule(atom, context)
    │
    ├── ASR-BT-PIAN_YIN: EXACT match on TEN_GOD_PIAN_YIN → direction=caution
    ├── ASR-BT-ZHENG_CAi: EXACT match on TEN_GOD_ZHENG_CAi → direction=supportive
    └── ASR-BT-BI_JIAN:  EXACT match on TEN_GOD_BI_JIAN   → direction=neutral
    │
    ▼ direction 由规则授权产生，非 MappingLayer 自由决定
    │
    ▼
CanonicalAssertion（每条）
    ├── assertion_id = "AS-{evidence_id}-{atom_id}"
    ├── subject = "jixiaolan"
    ├── domain = rule.domain（来自规则）
    ├── semantic = atom.atom_id
    ├── direction = rule.direction（来自规则，非默认）
    ├── temporal_scope = "birth"
    ├── source_engine = "ZI_PING"
    ├── source_rule = evidence.evidence_id
    ├── authorized_rule_id = rule.rule_id
    └── evidence = {evidence_ref, engine, value, source_rule_ref, ...}
```

---

## 二、禁止组件调用确认

| 组件 | 是否在调用链中 | 证据 |
|------|-------------|------|
| `reasoning.signal_engine.SignalEngine` | ❌ 否 | 源码 grep 无引用 |
| `reasoning.cross_analysis.CrossAnalyzer` | ❌ 否 | 源码 grep 无引用 |
| `signal.convergence.ConvergenceArbiter` | ❌ 否 | 源码 grep 无引用 |
| `signal.aggregator.CanonicalSignalAggregator` | ❌ 否 | 源码 grep 无引用 |
| `signal.legacy_adapter` | ❌ 否 | 零引用 |
| `evidence_count` 投票逻辑 | ❌ 否 | AssertionRuleLibrary 无此字段 |
| `NEUTRAL` 作为默认 fallback | ❌ 否 | find_rule 返回 None（NO_ASSERTION） |

---

## 三、追溯链示例（纪晓岚命例）

### Evidence 示例

```json
{
  "evidence_id": "ZP-TG-YEAR-a1b2c3d4",
  "engine": "ZI_PING",
  "rule_id": "ZP_TEN_GOD_YEAR",
  "value": "偏印",
  "temporal_scope": "birth",
  "attributes": {
    "ten_god": "偏印",
    "stem": "JIA",
    "day_master": "BING",
    "pillar": "year"
  },
  "source_rule_ref": "rules/bazi_ten_gods.json",
  "source_field": "ten_god",
  "calculation_version": "2026.09",
  "contract_version": "v13.0"
}
```

### SemanticAtom 示例

```json
{
  "atom_id": "TEN_GOD_PIAN_YIN",
  "engine": "ZI_PING",
  "evidence_ref": "ZP-TG-YEAR-a1b2c3d4",
  "semantic_keys": ["SPECIAL_SKILL", "INTUITION", "UNCONVENTIONAL_KNOWLEDGE", ...],
  "domain_candidates": ["GROWTH", "CAREER", "DECISION"],
  "label_zh": "偏印",
  "category": "TEN_GOD"
}
```

### CanonicalAssertion 示例

```json
{
  "assertion_id": "AS-ZP-TG-YEAR-a1b2c3d4-TEN_GOD_PIAN_YIN",
  "subject": "jixiaolan",
  "domain": "GROWTH",
  "semantic": "TEN_GOD_PIAN_YIN",
  "direction": "caution",
  "temporal_scope": "birth",
  "source_engine": "ZI_PING",
  "source_rule": "ZP-TG-YEAR-a1b2c3d4",
  "authorized_rule_id": "ASR-BT-PIAN_YIN",
  "evidence": {
    "evidence_ref": "ZP-TG-YEAR-a1b2c3d4",
    "engine": "ZI_PING",
    "value": "偏印",
    "source_rule_ref": "rules/bazi_ten_gods.json",
    "temporal_scope": "birth",
    "rule_id": "ZP_TEN_GOD_YEAR",
    "calculation_version": "2026.09",
    "contract_version": "v13.0"
  }
}
```

---

## 四、测试结果

| 测试组 | 测试数 | 通过 | 失败 |
|--------|--------|------|------|
| TestRealRuntimeVerticalSlice (D1-D9) | 9 | 9 | 0 |
| TestProductionCallTrace (D10-D11) | 2 | 2 | 0 |
| **合计** | **11** | **11** | **0** |

**运行时间：** 0.43s

---

## 五、结论

1. **真实生产输入已跑通新 Contract 全链路**：BaziEngine → BaziEvidenceProducer → EngineEvidence → SemanticAtom → CanonicalAssertion
2. **旧 Signal 组件未参与新链路**：SignalEngine / CrossAnalyzer / ConvergenceArbiter 全部未导入
3. **追溯链完整**：每条 Assertion 可追溯到 EngineEvidence.evidence_id → rule_id → source_rule_ref
4. **direction 由规则授权产生**：非默认值，非 MappingLayer 自由决定
5. **EVIDENCE_ID ≠ RULE_ID**：同规则多次命中时各自有唯一 evidence_id

---

## 六、当前状态标签

```
P1.2-C = CONTRACT/SLICE VERIFIED（单元测试层面验证通过）
P1.2-D = REAL RUNTIME VERIFIED（真实生产输入验证通过）
        ≠ PRODUCTION MIGRATED（旧 Pipeline 尚未切换）
```

**下一步：等待 User 裁决是否进入 P1.2-E（独立 Contract Review + 扩展第二引擎）。**
