# PATCH-157 PZZQ Candidate State Machine 阶段封板审计

## 一、链路（已贯通）
```
四柱
  ↓ L0 Fact Builder (藏干/透干/十神/根/合冲/any_stem/target_relation)
  ↓ Assertion(SPO) → 三桶 required/blocked/supported
  ↓ Condition Router → SAT/UNSAT/UNKNOWN
  ↓ required_bundle / blocked_bundle
  ↓ synthesize
  ↓ candidate_direction: SUPPORTED / NOT_SUPPORTED / PENDING
```

## 二、三态证据（全真实 Resolver 链）
| direction | 真实来源 | 证据 |
|---|---|---|
| SUPPORTED | required全SAT + blocked CLEAR | 官格(乙日申月透庚,无财,官支不冲) |
| NOT_SUPPORTED | required缺 / blocked命中 | 财格(不透)、官格见财 |
| PENDING | required够但blocked仍UNKNOWN | 财格「财太露」 |

## 三、纪律检查
- ✅ 无评分/加权/多数决/概率
- ✅ UNKNOWN 不降级（财太露→PENDING，没硬出SUPPORTED）
- ✅ 不输出"成格/破格/吉凶"（SUPPORTED=candidate_direction非成格）
- ✅ supported 纯记录不参与硬判定
- ✅ L0 只出事实，不反推格局
- ✅ Relation Fact 只判存在，作用到目标才判 effect
- ✅ 有合≠官被合，有冲≠官受冲

## 四、Golden 全清单
- test_root/transparent/combination_condition_evaluator
- test_condition_router / test_condition_bundle
- test_cai_bundle_4state / test_guan_yin_bundle / test_blocked_supported_bundle
- test_resolver_full_chain / test_anywhere_transparent / test_stem_wuhe
- test_sanhe_sanhui / test_guan_target_relation / test_guan_full_state
全部 assert + sys.exit 非零退出。

## 五、明确挂起（不硬造）
- 财太露：关系综合（露/根/生官/逢劫），禁止 count>=N，永久 UNKNOWN/PENDING
- 刑/破/害：未建 Relation，不入 blocked
- 身强/身弱/得令权重：仍禁止直出
- target_relation_facts 当前 boolean，后续扩 Relation/Target/Effect 结构（架构债，不返工）

## 封板结论
PZZQ Candidate State Machine：三态闭环成立，SEALED。
下一阶段（财太露语义研究 / 其他Producer）另起。
