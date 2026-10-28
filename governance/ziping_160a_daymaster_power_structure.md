# PATCH-160-A 日主力量结构（Daymaster Power Structure）施工依据

状态：160-A AUTHORIZED TO BUILD / 160-B STRENGTH JUDGMENT NOT_AUTHORIZED
修订：已按审计修正三处（官杀边方向 / 得令口径 / 比劫食伤数据源）

---

## 0. 唯一目标
160 不发明身强/身弱公式。160-A 只把日主在原局的
得时、根气、扶助、泄耗、克制、源流，组织成 Deterministic Fact Graph。

```
FrozenCanonicalBaziChart + 已有L0 Fact
        ↓
160-A Structure Generator (STRUCTURE COMPOSER, 不是第二套Fact Engine)
        ↓
Daymaster Power Structure Fact
        ↓
160-B Strength Resolver  ← NOT_AUTHORIZED, 禁建
```

---

## 1. 六经典裁决基础
- PZZQ: 得时为旺失时为衰；党众为强助寡为弱。旺≠强, 衰≠弱。
- 得时而不旺 / 失时而不弱 → 禁 month_supports == True 就 STRONG。
- 根轻重: 长生/禄/旺/刃=重根, 墓库/余气=轻根; "干多不如根重"。
  root_type 保持独立 Fact, 不等价 strength。

## 2. 对象边界
160 只分析日主。不判格局/用神/宜忌/祸福/事件。不做"身强喜什么"。

## 3. 输入（全部消费已有L0 Fact，禁重算）
- daymaster_stem/element/yinyang, month_branch
- four_stems/branches, hidden_stems
- ten_god_members, root_facts/root_type, changsheng_direction
- relation_facts(185), month_supports_daymaster

禁: 重新排盘/十神/藏干/月令, 禁调 sxtwl。160 是下游 consumer。

---

## 4. 【修正1】得时轴 seasonal_axis（口径拆开）
引擎现有 Fact: `month_supports_daymaster = 月令本气==日主五行 OR 月令生日主五行`。
这是"月令生扶"，不纯等于 PZZQ"得时"。拆开两字段:

```
seasonal_axis:
  in_season        = 月令本气五行 == 日主五行        (纯得令/得时)
  month_supports  = 月令本气==日主五行 OR 月令生日主五行 (现有Fact)
```
只表达时令状态, 不输出 strong/weak。

---

## 5. 自身根气 root_axis
直接消费 root_type / target_root_facts / changsheng_direction。
输出 branch/hidden_stem/root_type/root_weight_class ∈ {HEAVY,LIGHT,NONE}。
禁: HEAVY→STRONG, LIGHT→WEAK。HEAVY 只="根气较重这一事实"。

---

## 6. 【修正2】扶身/泄耗克节点（数据源写明）
集团:
- SUPPORT: BIJIE(比肩/劫财), YIN(正印/偏印)
- DRAIN:   SHISHANG(食神/伤官), CAI(正财/偏财)
- CONTROL: GUANSHA(正官/七杀)

每节点记: stem_present / root_present / root_type。

数据源:
- 财/官/印: 现成 any_stem_has_ten_god + target_root_facts
- 比劫/食伤: **无独立键, 从 ten_god_members 现筛**
  type=='stem' → stem_present; type=='hidden' → root_present
  不新造搜索器, 不假设已有键。

只记关系分类, 不推 net_power。食伤不一定削弱、财不一定耗尽、官杀不一定压倒
——因有源流/制化/通关。

---

## 7. 【修正3】传递网络 Edge 方向（已改）
有向边（方向按五行作用）:

```
SUPPORT  → DAYMASTER:
  BIJIE → DAYMASTER   (同类扶)
  YIN   → DAYMASTER   (生我扶)

DAYMASTER → 我所泄/我所克:
  DAYMASTER → SHISHANG  (泄)
  DAYMASTER → CAI       (耗: 日主克财)

【修正】克我:
  GUANSHA → DAYMASTER   (克: 官杀克日主; 原手册误写成 DAYMASTER→GUANSHA)

传递链:
  SHISHANG → CAI    (食伤生财)
  CAI      → GUANSHA (财生官杀)
  GUANSHA  → YIN     (官杀生印)
```

五行生克存在 ≠ 边已获命理 Judgment 授权。

---

## 8. Edge 四层分离
每条 Edge:
```
{edge_id, source, target, relation,
 evidence_ids, authorization_level, activation_facts, status}
```
RELATION/relation(经典关系) EVIDENCE(原典依据)
AUTHORIZATION(能否进Rule) ACTIVATION(本盘是否满足) — 四者不混。

## 9. Authorization 分级
A=可进 Deterministic Rule
B=辅助结构, 不独立产 Judgment
C=仅 Evidence/Research

DIRECT 边(BIJIE/YIN→日主, 日主→SHISHANG/CAI, GUANSHA→日主):
关系结构本身可记, 但**不授权"扶身方强/克身方强"的 Judgment**。
传递链边(SHISHANG→CAI/CAI→GUANSHA/GUANSHA→YIN)当前= C, 不ACTIVE。

## 10. Active Edge 条件
边同时满足 relation+evidence+authorization+activation+无破坏 → ACTIVE。
否则 INACTIVE/UNKNOWN/UNAUTHORIZED。禁把 UNKNOWN→FALSE/TRUE。

## 11. 存在≠有效
节点统一 PRESENT/ROOTED/SEASONAL/CONNECTED/ACTIVE。
例: CAI_PRESENT / CAI_ROOTED / CAI_SEASONAL / CAI_SOURCE_PRESENT / CAI_SOURCE_ACTIVE(可UNKNOWN)。
禁 CAI_ROOTED=True → CAI_STRONG=True。

---

## 12. Generator 输出契约
```
{
  daymaster, seasonal_axis{in_season, month_supports},
  root_axis{root_type, root_weight_class},
  support_group{bijie, yin: {stem_present, root_present, root_type}},
  drain_group{shishang, cai: 同上},
  control_group{guansha: 同上},
  active_edges[], unknown_edges[], unauthorized_edges[],
  evidence_refs[],
  judgment_status: "NOT_AUTHORIZED"
}
```

## 13. 递归限制
DEPTH0=直接日主关系; DEPTH1=经典明确授权传递; DEPTH2+=Candidate暂存。
无明确授权即 STOP → UNRESOLVED_CHAIN, 不无限递归(食伤→财→官→印→日主...)。

## 14. 源头有力只拆结构
"官星虽寡得财扶则强"(DTS) → 只拆 CAI_PRESENT/CAI_ROOTED/CAI_SOURCE_RELATION,
不直接 GUANSHA_STRONG。

## 15. 绝对禁止
数量统计 / 天干×权重 / 地支×权重 / 月令50%根30% / support_score / threshold /
probability / voting / "明显强/明显弱"。

## 16. Golden（160-A）
G160-01 得时扶身不足; 02 失时根气深; 03 得时根重; 04 失时比印众;
05 扶身存在反方复杂; 06 财生官候选链; 07 食伤生财候选链;
08 官杀生印候选链; 09 存在传递但授权不足; 10 结构无法成Judgment。
期望: STRUCTURE=PASS, JUDGMENT=UNKNOWN/NOT_AUTHORIZED。

## 17. 对接
162 root_type/target_root; 176 changsheng_direction; 185 relation;
ten_god_members。160 只组织, 不重造。

## 18. 状态机
FACT→STRUCTURED→EVIDENCED→AUTHORIZED→ACTIVE→JUDGMENT, 缺一即STOP。
FACT→JUDGMENT 禁止。

---

## 修正记录（2026-09-17 审计三处）
1. 官杀边: DAYMASTER→GUANSHA 改为 GUANSHA→DAYMASTER（克日主方向）。
2. 得令口径: 拆 in_season(纯同五行) vs month_supports(同五行或生我), 不混。
3. 比劫/食伤: 无现成键, 从 ten_god_members 现筛, 不新造搜索器。
