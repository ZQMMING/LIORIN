# P6 Assertion Layer V2 - 五引擎原生断言层架构文档

## 核心原则

1. **五大引擎各自拥有自己的原生断言层**，不共用统一断语模板
2. **断言层之后才进入统一Mapping / Cross-Engine聚合**
3. **互补，不比较**；各体系不能互相改写
4. **禁止**: direction/polarity/pos/neg/confidence/vote/majority/SYSTEM_WEIGHTS
5. **每个NativeJudgment必须带provenance和mapping_hook**

## 整体架构

```
┌────────────────────┐
│ Deterministic      │
│ Engines            │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│ Engine Evidence    │
└─────────┬──────────┘
          ↓
┌───────────┼───────────┐
↓           ↓           ↓
子平Judgment 盲派Judgment 紫微Judgment
│           │           │
└──────┬────┴────┬──────┘
       │         │
  河洛Judgment 易经Judgment
       │         │
       └────┬────┘
            ↓
┌─────────────────────┐
│ Unified Mapping     │
│ Semantic Layer      │
└──────────┬──────────┘
           ↓
      8 Life Domains
           ↓
    Guidance Composer
           ↓
     LLM Renderer
```

## 各引擎原生断言类型

### 子平 (ZI_PING)
- PATTERN: 格局层
- DAY_TIME: 日时层
- TUNING: 调候层
- FUWEN: 赋文层
- TEN_GOD: 十神断语
- STRENGTH: 旺衰断语
- STEM_BRANCH: 干支断语
- PUNISHMENT_CLASH: 刑冲合害
- YEAR_LUCK: 岁运断语
- TIMING: 应期断语

### 盲派 (BLIND_SCHOOL)
- DOING_WORK: 做功
- GUEST_HOST: 宾主体用
- TEN_GOD_PALACE: 十神落宫
- PALACE_RELATION: 宫位关系
- STEM_BRANCH_COMBO: 干支组合
- PUNISHMENT_CLASH: 刑冲合害
- GRAVE: 墓库
- BODY_USE: 体用
- TIMING: 应期
- MANTRA: 盲派口诀/断语

### 紫微 (ZI_WEI)
- TWELVE_PALACES: 十二宫断语
- MAJOR_STARS: 主星组合
- MINOR_STARS: 辅星组合
- SIHUA: 四化
- PALACE_STAR: 宫位×星曜
- SANFANG_SIZHENG: 三方四正
- OPPOSITE_PALACE: 对宫
- DA_LIMIT: 大限
- FLOW_YEAR: 流年
- FLOW_MONTH: 流月
- FLOW_DAY: 流日
- ANCIENT_MANTRA: 紫微古诀

### 河洛 (HE_LUO)
- PREHEAVEN_HEXAGRAM: 先天卦
- YUANTANG: 元堂
- POSTHEAVEN_HEXAGRAM: 后天卦
- YEAR_HEXAGRAM: 流年卦
- MONTH_HEXAGRAM: 流月卦
- DAY_HEXAGRAM: 流日卦
- MOMENT: 时刻
- JIEHOU_HEXAGRAM: 节候卦
- HEXAGRAM_QI: 卦气
- HEXAGRAM_POSITION: 卦×位
- NUMBER_LOGIC: 数理
- ANCIENT_MANTRA: 河洛古诀

### 易经 (YI_JING)
- HEXAGRAM_TEXT: 卦辞
- YAO_TEXT: 爻辞
- TUAN_TEXT: 彖辞
- DA_XIANG: 大象
- XIAO_XIANG: 小象
- HUMAN_AFFAIRS: 人事义
- POSITION: 位
- ZHONG_ZHENG: 中正
- CHENG_CHENG_BI_YING: 承乘比应
- CHANGED_HEXAGRAM: 变卦
- DECISION: 决策类断语

## 核心数据结构

### NativeJudgment (原生断言)
```python
@dataclass(frozen=True)
class NativeJudgment:
    judgment_id: str
    engine: EngineName
    judgment_type: str
    condition: dict[str, Any]
    canonical_text: str
    source: dict[str, Any]
    provenance: JudgmentProvenance
    mapping_hook: MappingHook
```

### JudgmentProvenance (来源追溯)
```python
@dataclass(frozen=True)
class JudgmentProvenance:
    source_engine: EngineName
    source_rule_id: str
    source_evidence_ref: Optional[str]
    source_work: Optional[str]
    source_chapter: Optional[str]
    derivation_chain: list[str]
    calculation_version: str
```

### MappingHook (映射钩子)
```python
@dataclass(frozen=True)
class MappingHook:
    semantic_candidates: list[str]
    domain_candidates: list[str]
```

## 8 Life Domains

- CAREER: 事业
- FINANCE: 财富
- RELATIONSHIP: 感情/婚姻
- FAMILY: 家庭
- HEALTH: 健康
- GROWTH: 个人成长
- DECISION: 决策
- MIGRATION: 迁移/出行

## 禁止事项

### 禁止字段
- direction / polarity / pos / neg / positive / negative
- confidence / score / weight
- vote / majority
- SYSTEM_WEIGHTS
- lucky / unlucky / good / bad / auspicious / inauspicious

### 禁止行为
- 跨引擎比较/投票
- 输出direction/pos/neg/confidence
- 修改原生断言
- 让LLM重新算命
- 十神→Domain硬映射

## 与旧断言层(V1)的区别

| 维度 | V1 (已归档) | V2 (当前) |
|------|-------------|-----------|
| 断言结构 | 统一Assertion格式 | 各引擎原生NativeJudgment |
| Direction | POSITIVE/NEGATIVE/NEUTRAL | 禁止, 由ContextResolver产生 |
| Confidence | SUPPORTED/LIKELY/WEAK | 禁止, 用evidence_count表示覆盖面 |
| 引擎关系 | 统一Producer, 可比较 | 各自独立, 互补不比较 |
| 映射 | 直接输出Domain | 通过MappingHook提供候选, 由UnifiedMappingLayer决定 |
| 追溯 | 部分有 | 强制provenance |

## 文件位置

- Contract: `src/tongshu/assertion_v2/contract.py`
- 旧断言层归档: `src/tongshu/legacy/assertion_v1/`

## 下一步

1. 建立各引擎的JudgmentMatcher (各引擎独立)
2. 建立各引擎的Canonical Judgment Library
3. 建立Assertion Observatory五套断言工作台
4. 接入P6-C-3C Resolver Integration
