# P6-C-3A: Temporal Context Contract — 验收报告

## 阶段定位

P6-C-3A = **Contract Definition**（只做schema，不改推理）

当前基线：
- P6-C-2A Day Master / Ten-God / Year fields → **V2 FREEZE**
- 不再回头修改Deterministic Bazi Engine

## 核心原则

1. **把十神从"直接映射Domain"降级为"Candidate Semantic Signal"**
   - 十神本身不等价于事件领域
   - 正财 ≠ Domain=WEALTH，最多提供Candidate Semantic Signal: resource/transaction/acquisition/responsibility
   - 最终Domain由完整时序Context + 结构关系 + 激活条件决定

2. **TemporalContext四层结构**
   - Natal Context（本命结构背景）
   - Da Yun Context（大运激活）
   - Year Context（流年触发）
   - Derived Signals（派生语义信号）

3. **Evidence Provenance强制**
   - 没有provenance的signal不允许进入ContextResolver
   - 防止EngineEvidence.rule_id ≠ Rule.rule_id身份断裂

4. **ContextResolver职责边界**
   - Resolver = semantic interpretation，不是第二个BaziEngine
   - 不负责重新计算底层命理规则
   - 接受已经经过deterministic engine验证的DerivedSignal[]

## Contract Schema

### 1. DerivedSignal（派生信号）

```
DerivedSignal
├── signal_id: str                    # 唯一标识
├── source: SignalSource              # TEN_GOD / FIVE_ELEMENT / BRANCH_RELATION / ...
├── value: str                        # 信号值 (如 "DIRECT_WEALTH", "CLASH")
├── label_zh: str                     # 中文标签
├── temporal_layer: TemporalLayer     # NATAL / DA_YUN / YEAR / INTERACTION
├── subject: Optional[str]            # 主体 (如 "DAY_MASTER")
├── object: Optional[str]             # 客体
├── polarity: SignalPolarity          # ACTIVATING/RESTRAINING/CONNECTING/CONFLICTING/... (非direction!)
├── strength: SignalStrength          # WEAK/MODERATE/STRONG/DOMINANT
├── participants: list[str]           # 参与者
├── semantic_keys: list[str]          # 语义键 (如 ["RESOURCE", "TRANSACTION"])
└── provenance: SignalProvenance      # 强制! 没有provenance不允许进入Resolver
```

**SignalPolarity ≠ Direction**
- polarity是信号本身的结构极性（激活/制约/连接/冲突/重复/转化）
- 最终direction（supportive/caution/neutral）必须由ContextResolver基于完整context决定

### 2. SignalProvenance（来源追溯）

```
SignalProvenance
├── source_engine: str                # ZI_PING / BLIND_SCHOOL / ZI_WEI / ...
├── source_rule_id: str               # canonical rule_id
├── temporal_layer: TemporalLayer
├── derivation_chain: list[str]       # 推导链 (rule_id序列)
├── raw_evidence_ref: Optional[str]   # 原始EngineEvidence引用
└── calculation_version: str
```

### 3. NatalContext（本命上下文）

```
NatalContext
├── day_master: str
├── gender: str
├── birth_year: int
├── pillars: list[NatalPillar]        # 四柱 (YEAR/MONTH/DAY/HOUR)
├── branch_clashes: list[str]          # 地支冲
├── branch_combinations: list[str]     # 地支合
├── branch_harms: list[str]            # 地支害
├── branch_punishments: list[str]      # 地支刑
├── branch_three_combinations: list[str] # 三合
├── day_master_root: list[str]         # 日主通根
├── day_master_strength: str           # 日主强度
├── day_master_seasonal_state: str     # 季节状态
├── ten_god_distribution: dict[str,int] # 十神分布
├── useful_gods: list[str]             # 用神
├── avoid_gods: list[str]              # 忌神
└── structural_features: list[str]     # 结构特征
```

### 4. DaYunContext（大运上下文）

```
DaYunContext
├── current_da_yun: Optional[DaYunPillar]   # 当前大运 (必要输入!)
├── previous_da_yun: Optional[DaYunPillar]  # 上一步大运
├── next_da_yun: Optional[DaYunPillar]      # 下一步大运
├── all_da_yun: list[DaYunPillar]            # 全部大运
├── natal_dayun_clashes: list[str]            # 大运与本命冲
├── natal_dayun_combinations: list[str]       # 大运与本命合
├── dayun_ten_god_activation: list[str]       # 大运激活的十神
├── is_transition_period: bool                 # 是否换运期
├── transition_start_year: Optional[int]
└── transition_end_year: Optional[int]
```

**关键**：很多事件不是Natal→Event，而是：
```
Natal latent structure
→ Da Yun activates structure
→ Year triggers structure
→ Event manifestation
```

### 5. YearContext（流年上下文）

```
YearContext
├── target_year: int
├── year_stem: str
├── year_branch: str
├── year_stem_ten_god: Optional[str]
├── natal_year_clashes: list[str]          # 流年与本命冲
├── natal_year_combinations: list[str]     # 流年与本命合
├── natal_year_harms: list[str]            # 流年与本命害
├── natal_year_punishments: list[str]      # 流年与本命刑
├── natal_year_fuyin: list[str]            # 流年与本命伏吟
├── dayun_year_clashes: list[str]          # 流年与大运冲
├── dayun_year_combinations: list[str]     # 流年与大运合
├── dayun_year_fuyin: list[str]            # 流年与大运伏吟
└── three_layer_interactions: list[str]     # Natal×DaYun×Year三层交互
```

### 6. TemporalContext（完整时序上下文）

```
TemporalContext
├── case_id: str
├── target_year: int
├── natal: NatalContext              # 第一层: 本命结构
├── da_yun: DaYunContext             # 第二层: 大运激活
├── year: YearContext                # 第三层: 流年触发
├── derived_signals: list[DerivedSignal]  # 第四层: 派生语义信号
├── context_version: str
├── assembly_timestamp: str
└── completeness_score: float
```

## Candidate Signal降级规则

### 十神 → Candidate Semantic Keys（不是Domain!）

| 十神 | 中文 | semantic_keys | polarity |
|------|------|--------------|----------|
| BIJIAN | 比肩 | SELF, PEER, COMPETITION, SUPPORT, ENDURANCE | CONNECTING |
| JIECAI | 劫财 | COMPETITION, RESOURCE_DISPUTE, ACTION, RISK | CONFLICTING |
| SHISHEN | 食神 | OUTPUT, CREATIVITY, EXPRESSION, LEISURE, FREEDOM | ACTIVATING |
| SHANGGUAN | 伤官 | OUTPUT, EXPRESSION, INNOVATION, AUTONOMY, REBELLION | ACTIVATING |
| ZHENGCAI | 正财 | RESOURCE, TRANSACTION, ACQUISITION, RESPONSIBILITY, STABILITY | CONNECTING |
| PIANCAI | 偏财 | RESOURCE, OPPORTUNITY, TRANSACTION, RISK, FLUIDITY | TRANSFORMING |
| ZHENGGUAN | 正官 | RULE, RESPONSIBILITY, STRUCTURE, AUTHORITY, DISCIPLINE | RESTRAINING |
| QISHA | 七杀 | PRESSURE, COMPETITION, CHANGE, CHALLENGE, DISCIPLINE | CONFLICTING |
| ZHENGYIN | 正印 | SUPPORT, KNOWLEDGE, RESOURCE, PROTECTION, TRADITION | CONNECTING |
| PIANYIN | 偏印 | KNOWLEDGE, INSIGHT, RESOURCE, UNCONVENTIONAL, ISOLATION | NEUTRAL |

**关键**：这些是semantic_keys，不是Domain。最终Domain（CAREER/FINANCE/RELATIONSHIP/FAMILY/...）由ContextResolver基于完整Context决定。

### 地支关系 → Candidate Semantic Keys（不是Direction!）

| 关系 | 中文 | semantic_keys | polarity |
|------|------|--------------|----------|
| CLASH | 冲 | CHANGE, CONFLICT, MOVEMENT, DISRUPTION, SEPARATION | CONFLICTING |
| COMBINATION | 合 | CONNECTION, INTEGRATION, COOPERATION, ATTRACTION, STABILITY | CONNECTING |
| HARM | 害 | FRICTION, MISUNDERSTANDING, SUBTLE_CONFLICT, DAMAGE | RESTRAINING |
| PUNISHMENT | 刑 | TENSION, LEGAL, DISCIPLINE, SUFFERING, RESOLUTION | RESTRAINING |
| FUYIN | 伏吟 | REPETITION, RECURRENCE, DELAY, INTENSIFICATION, RETURN | REPEATING |
| THREE_COMBINATION | 三合 | INTEGRATION, COMPLETION, AMPLIFICATION, STRUCTURE_FORMATION | TRANSFORMING |

**关键**：冲≠caution，合≠supportive，伏吟≠neutral。structural relationship ≠ outcome polarity。

## Contract Validator

```python
ContractValidator.validate_temporal_context(ctx) → {
    valid: bool,
    error_count: int,
    errors: list[str],
    completeness_score: float,
    natal_valid: bool,
    dayun_valid: bool,
    year_valid: bool,
    signals_valid: bool,
    signal_count: int,
}
```

验证规则：
- DerivedSignal必须有有效的provenance（source_engine + source_rule_id）
- NatalContext必须有day_master + 4 pillars
- DaYunContext必须有current_da_yun（大运是必要输入）
- YearContext必须有year_stem + year_branch + year_stem_ten_god
- 所有signal的polarity必须非None

## 禁止事项（P6-C-3A阶段）

| # | 禁止 | 原因 |
|---|------|------|
| 1 | 修改十神计算 | 已513/513=100%，冻结 |
| 2 | 重新训练/调参 | 不是ML tuning问题 |
| 3 | 修改Ground Truth V2 | P5/Ground Truth继续Frozen |
| 4 | 十神→Domain硬映射 | 正财→WEALTH这种one-hop mapping必须退出主解释路径 |
| 5 | ContextResolver重新计算Bazi | Resolver是semantic interpretation，不是第二个BaziEngine |
| 6 | Direction当成投票结果 | 互补≠比较≠投票，Direction来自状态/势的解释 |

## 验收标准

### 第一层：Contract
- ✅ TemporalContext schema valid
- ✅ DerivedSignal schema valid
- ✅ SignalProvenance contract valid
- ✅ Natal/DaYun/Year boundaries defined

### 第二层：完整性
- ✅ Natal Context fields complete
- ✅ Da Yun Context fields complete（current_da_yun标记为必要输入）
- ✅ Year Context fields complete
- ✅ DerivedSignal provenance complete（强制验证）

### 第三层：降级规则
- ✅ 十神→Candidate Semantic Keys定义完成（10个十神，非Domain映射）
- ✅ 地支关系→Candidate Semantic Keys定义完成（6种关系，非Direction映射）
- ✅ SignalPolarity ≠ Direction 明确区分

### 第四层：验证器
- ✅ ContractValidator实现完成
- ✅ 缺少provenance的signal被正确拒绝
- ✅ 完整Context验证逻辑实现

## 文件位置

- Contract定义: `src/tongshu/reasoning/temporal_context_contract.py`
- 验收报告: `docs/audit/p6c_3a_contract_report.md`

## 下一步

P6-C-3A完成 → **P6-C-3B: Context Assembly**

P6-C-3B职责：把Natal + Da Yun + Year + Derived Signals正确组装起来。
验收：513 events Context completeness = 100%

P6-C-3B完成 → **P6-C-3C: Resolver Integration**

P6-C-3C职责：Candidate Signal → ContextResolver → Domain + SemanticFamily + Direction
然后重新跑513 events，建立V3。
