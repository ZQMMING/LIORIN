# 身强身弱多维矩阵设计（PATCH-160 整体研究 v2）

状态：研究扩展完成 / 前置设计 / 待执行
基准：93a3426d

---

## 一、六部经典身强身弱相关原文（深度搜索后）

### PZZQ（子平真诠）
| 原文 | evidence_id | 语义 | 维度 |
|---|---|---|---|
| 得时为旺，失时为衰 | PZZQ-005-005 | 月令旺衰 | D1 SEASONAL |
| 党众为强，助寡为弱 | 待定位 | 同党多少 | D3 SUPPORT |
| 得时而不旺（得令但泄太重） | PZZQ-005-005 | 得令+泄太重 | D1+D4 |
| 失时而不弱（失令但比印重叠） | PZZQ-005-005 | 失令+扶重叠 | D1+D3 |
| 有根便能任财官 | 待定位 | 根→承受力 | D2 ROOT |
| 长生/禄/旺/刃=重根；墓库/余气=轻根 | 待定位 | 根层级 | D2 ROOT |
| 干多不如根重 | 待定位 | 根>干 | D2 vs D3 |
| 透干会支，别取财官煞食为用 | PZZQ-007-033 | 透藏关系 | D13 TOU_CANG |
| 有情无情、有力无力之间 | PZZQ-007-001 | 格局高低（非身强弱） | — |

### DTS（滴天髓）
| 原文 | evidence_id | 语义 | 维度 |
|---|---|---|---|
| 强众敌寡/强寡敌众 | DTS-027-003 | 两端成势 | D6 TWO_SIDE |
| 通根透癸，冲天奔地 | DTS-008-021 | 通根=有力 | D2 ROOT |
| 不论有根无根，俱要天覆地载 | DTS-010-003 | 根+结构 | D2+D12 |
| 五阳从气不从势，五阴从势无情义 | DTS-008-003 | 从化 | D10 CONG_HUA |
| 何知章：何处起根源，流到何方住 | DTS-018-001 | 源流/通关 | D15 GUAN_TONG |

### QTBJ（穷通宝鉴）
| 原文 | evidence_id | 语义 | 维度 |
|---|---|---|---|
| 正月甲木/二月甲木... | QTBJ-003-001等 | 调候 | D9 TIAO_HOU |
| 寒暖燥湿 | 全书 | 调候 | D9 TIAO_HOU |

---

## 二、完整多维矩阵（16 维）

```
日主多维网络（16 维）
│
├─ D1 SEASONAL（得令/失令）✅ 已建
│   ├─ in_season
│   ├─ month_supports
│   └─ 原著: 得时为旺，失时为衰
│
├─ D2 ROOT（根气）✅ 已建（待细分 root_type）
│   ├─ has_root
│   ├─ root_weight_class: HEAVY/LIGHT
│   ├─ root_type: 长生/禄/旺/刃/墓库/余气（待接）
│   └─ per_pillar
│
├─ D3 SUPPORT（党众/助寡）✅ 已建
│   ├─ BIJIE: stem/root present
│   └─ YIN: stem/root present
│
├─ D4 DRAIN（泄耗）✅ 已建
│   ├─ SHISHANG: stem/root present
│   └─ CAI: stem/root present
│
├─ D5 CONTROL（克制）✅ 已建
│   └─ GUANSHA: stem/root present
│
├─ D6 TWO_SIDE（两端成势）🔒 HOLD
│   ├─ daymaster_side: D2+D3
│   ├─ opposing_side: D4+D5
│   └─ 原著: 强众敌寡/强寡敌众
│
├─ D7 TRANSMISSION（传递链）✅ C级
│   ├─ SHISHANG→CAI
│   ├─ CAI→GUANSHA
│   └─ GUANSHA→YIN
│
├─ D8 STRUCTURE（合冲刑害破）🔒 HOLD
│   ├─ 合/冲/刑/害/破
│   └─ 对根气影响（根动/根拔）
│
├─ D9 TIAO_HOU（调候）🔒 未建
│   ├─ 寒暖燥湿
│   ├─ 月令调候需求
│   └─ 原著: QTBJ 全书
│
├─ D10 CONG_HUA（从化）🔒 未建
│   ├─ 从格（从财/从杀/从儿/从势）
│   ├─ 化格
│   └─ 原著: DTS 五阳从气不从势
│
├─ D11 XI_WANG_XIU_QIU（旺相休囚）⚠️ 待建
│   ├─ 日主在月令的旺相休囚
│   └─ 原著: PZZQ/QTBJ
│
├─ D12 TIAN_FU_DI_ZAI（天覆地载）🔒 HOLD
│   ├─ 不论有根无根俱要天覆地载
│   ├─ 根动/根拔
│   └─ 原著: DTS
│
├─ D13 TOU_CANG（透藏关系）⚠️ 待建
│   ├─ 透干会支
│   ├─ 天干透 vs 地支藏
│   └─ 原著: PZZQ 透干会支取财官煞食
│
├─ D14 GE_JU_GAO_DI（格局高低）— 非身强弱
│   ├─ 有情无情/有力无力/清浊真假
│   └─ 注意: 这是格局层，不属身强弱矩阵
│
├─ D15 GUAN_TONG（通关/源流）✅ C级
│   ├─ 生克路线
│   ├─ 通关
│   └─ 原著: DTS 源流论
│
└─ D16 SUI_YUN（岁运）🔒 冻结（215）
    ├─ 运支×命局刑破害
    ├─ 运干×命局合冲
    └─ 之前已冻结
```

---

## 三、已建 vs 缺失（扩展后）

### 已建
| 维度 | 状态 |
|---|---|
| D1 SEASONAL | ✅ |
| D2 ROOT | ✅（待细分 root_type） |
| D3 SUPPORT | ✅ |
| D4 DRAIN | ✅ |
| D5 CONTROL | ✅ |
| D7 TRANSMISSION | ✅ C级 |
| D15 GUAN_TONG | ✅ C级 |

### 缺失（未建）
| 维度 | 状态 | 原因 |
|---|---|---|
| D6 TWO_SIDE 成势 | 🔒 HOLD | 成势带作用语义 |
| D8 STRUCTURE 影响根气 | 🔒 HOLD | 根动/根拔带作用语义 |
| D9 TIAO_HOU 调候 | 🔒 未建 | QTBJ 体系，独立于身强弱 |
| D10 CONG_HUA 从化 | 🔒 未建 | 从格化格，特殊路径 |
| D11 XI_WANG_XIU_QIU | ⚠️ 待建 | 旺相休囚，与 D1 有重叠 |
| D12 TIAN_FU_DI_ZAI | 🔒 HOLD | 天覆地载带结构关系 |
| D13 TOU_CANG 透藏 | ⚠️ 待建 | 透干会支，结构关系 |
| D14 GE_JU_GAO_DI | — | 格局层，不属身强弱 |
| D16 SUI_YUN | 🔒 冻结 | 215 已冻结 |

---

## 四、Query 全集（扩展后）

### 已建
| Query | 原著依据 | 维度 |
|---|---|---|
| CAN_REN_CAIGUAN | 有根便能任财官 | D2 |
| DESHI_BUWANG | 得时不旺 | D1+D4 |
| SHISHI_BURUO | 失时不弱 | D1+D3 |

### 缺失 Query（待研究）
| Query | 原著依据 | 维度 | 状态 |
|---|---|---|---|
| 根重 vs 根轻 | 根分轻重 | D2 | ⚠️ 待建 |
| 干多不如根重 | 根>干 | D2 vs D3 | ⚠️ 待建 |
| 通根透癸 | 通根=有力 | D2 | ⚠️ 待建 |
| 天覆地载 | 不论有根无根俱要 | D2+D12 | 🔒 HOLD |
| 强众敌寡 | 两端成势 | D6 | 🔒 HOLD |
| 强寡敌众 | 两端成势 | D6 | 🔒 HOLD |
| 透干会支取财官 | 透藏 | D13 | ⚠️ 待建 |
| 寒暖燥湿调候 | QTBJ | D9 | 🔒 独立体系 |
| 从化成立 | 从格化格 | D10 | 🔒 特殊路径 |

---

## 五、依赖关系（关键）

```
CAN_REN_CAIGUAN (D2.has_root)
    ↓ 独立，不依赖其他维度

DESHI_BUWANG (D1.in_season + D4.has_drain)
    ↓ 依赖 D1 + D4
    ↓ 不依赖 D2/D3/D5

SHISHI_BURUO (NOT D1.in_season + D3.has_support)
    ↓ 依赖 D1 + D3
    ↓ 不依赖 D2/D4/D5

D6 TWO_SIDE 成势
    ↓ 依赖 D2 + D3 + D4 + D5
    ↓ 但"成势"带作用语义 → HOLD

D8 STRUCTURE 影响根气
    ↓ 依赖 D2 + D8
    ↓ 但"根动/根拔"带作用语义 → HOLD

D9 TIAO_HOU 调候
    ↓ 独立体系，不与身强弱混算

D10 CONG_HUA 从化
    ↓ 特殊路径，不与普通身强弱混算

D13 TOU_CANG 透藏
    ↓ 依赖 D1 + 天干透/地支藏
    ↓ 纯结构，可建
```

---

## 六、执行优先级（扩展后）

### 第一刀：补 D2 ROOT root_type 细分
- 当前：HEAVY/LIGHT
- 原著：长生/禄/旺/刃=重根；墓库/余气=轻根
- 纯结构，低风险

### 第二刀：补 D13 TOU_CANG 透藏关系
- 透干会支
- 纯结构，中风险

### 第三刀：补 D11 XI_WANG_XIU_QIU
- 旺相休囚
- 与 D1 有重叠，需区分

### 第四刀：研究 D9 TIAO_HOU 调候能否纯结构
- QTBJ 体系独立
- 可能 HOLD

### 第五刀：研究 D10 CONG_HUA 从化
- 从格化格
- 特殊路径，可能 HOLD

### 暂不执行
- D6 TWO_SIDE 成势（作用语义）
- D8 STRUCTURE 影响根气（作用语义）
- D12 天覆地载（结构关系）
- D14 格局高低（非身强弱）
- D16 岁运（已冻结）

---

## 七、永久边界

- 不评分/不权重/不阈值/不计数
- 不汇总成 STRONG/WEAK
- 矛盾共存不裁
- 结构匹配 ≠ 命题成立
- evidence_refs 空 ≠ 有证据
- 格局层（D14）不混入身强弱矩阵
- 调候（D9）独立体系，不与身强弱混算

---

## 八、纯结构维度收口裁决（2026-09-17，HEAD c0b073cc）

### 已落地（纯结构，全部 Golden + 全量回归 69/0）
| 维度 | 产物 | 状态 |
|---|---|---|
| D1 SEASONAL | 160-A in_season/month_supports | ✅ |
| D2 ROOT 细分 | daymaster_root_class.py（8 类 RootClass，补 L0 同字漏判） | ✅ 5a1d7ed0 |
| D3 SUPPORT | 160-A BIJIE/YIN | ✅ |
| D4 DRAIN | 160-A SHISHANG/CAI | ✅ |
| D5 CONTROL | 160-A GUANSHA | ✅ |
| D7 TRANSMISSION | network C 级边（不参与） | ✅ |
| D11 旺相休囚死 | daymaster_wang_xiang.py（五态纯映射） | ✅ c0b073cc |
| D13 透藏四态 | daymaster_tou_cang.py（BOTH/TOU_ONLY/CANG_ONLY/ABSENT） | ✅ bed7a7d7 |
| D15 通关源流 | network C 级边 | ✅ |
| T43 时柱禄旺 | 已被 D2 per_pillar.hour 覆盖（时支长生/禄/旺即 HEAVY 类） | ✅ 无需另建 |

network 维度集：SEASONAL / ROOT / SUPPORT / DRAIN / CONTROL / TOU_CANG / WANG_XIANG（后三者可选参数，默认行为不变）。

### 正式 HOLD（带作用语义或属独立/特殊体系，不进入身强弱网络）
| 维度 | HOLD 理由（原典对齐） |
|---|---|
| D6 TWO_SIDE 两端成势 | DTS 强众敌寡是"气势/去取"判断，非二值比较；成势依赖作用有效性，未授权 |
| D8 STRUCTURE 影响根气 | 冲则根拔、合局改根、开库（DTS 旺者冲衰衰者拔）属"作用"层，非纯结构；须独立专题取证 |
| D9 TIAO_HOU 调候 | QTBJ 本体即"用某干调候 + 富贵吉凶"（QTBJ-003-001 当以火温暖/必用庚金），属用神层 NOT_AUTHORIZED；月令气候标签孤立无身强弱意义，不建，未来归独立调候引擎 |
| D10 CONG_HUA 从化 | 成立依赖"极弱无根"（强弱两极）+ D6 成势 + D8 合局变根，前置全部 HOLD；特殊格局路径，不与普通身强弱混算 |
| D12 天覆地载整体 | 结构部分（透/根）已由 D2+D13 覆盖；"俱要天覆地载"整体成格属作用判断，HOLD |
| D14 格局高低 | 有情无情/有力无力/清浊真假属格局层，本就不属身强弱矩阵 |
| D16 岁运 | PATCH-215 已冻结，不并入 |

### 结论
身强身弱"可纯结构落地"的维度已全部落地，无遗漏的确定性 Fact 维度。
再往前的每一刀（D6/D8/D9/D10/D12）都必然触碰"作用有效性 / 用神 / 强弱两极"，
按原典边界这些不能由结构网络自行推出，须各自独立取得原典授权后单独立项。
当前网络保持 NETWORK_ONLY_NO_TOTALIZER，不输出 STRONG/WEAK。

---

## 九、D8 根支关系叠加落地（带依赖节点第一破，2026-09-17）

新增 daymaster_root_class.py 的下游 daymaster_root_relations.py：
- 把 D2 日主根支 与 L0 八类 combination_facts 做结构关联。
- 关系语义：CLASH(冲)/TRIPLE_PUNISH(三刑)/SELF_PUNISH(自刑)/HARM(害)/BREAK(破) 归 STRUCK；
  SIX_COMBINE(六合)/TRIPLE_COMBINE(三合)/DIRECTIONAL_COMBINE(三会) 归 COMBINE。
- 只标记"根支参与何种关系 + 对方/同局支"，输出 struck_root_pillars/combined_root_pillars。
- 非根支不挂关系；无根支不参与。

严格 HOLD（作用层，未授权）：冲则根拔/衰者拔旺者发、合化改根/合走、墓库逢冲开库、根增强/失效、强弱变化。
struck/combined 仅结构分组，不带好坏。network 新增 ROOT_RELATION 维度（可选参数）。
Golden 20 项全 PASS；全量回归 70/0。

依赖解锁：D6 两端成势、D10 从化所需的"根支是否处于冲合刑动结构"已有纯结构输入；
但"根是否真的被拔/被合化"仍须作用层独立授权，D8 不提供该结论。

---

## 十、D6 两端构成投影落地（带依赖节点第二破，2026-09-17）

新增 daymaster_two_side.py：
- DTS "须分日主与四柱两端而论" 的纯结构投影。
- DAYMASTER_SIDE = ROOT + BIJIE + YIN；OPPOSING_SIDE = SHISHANG + CAI + GUANSHA。
- 每成员仅布尔 present + 透藏四态 + 柱位；ROOT 带 root_pillars / struck / combined。
- 不计数、不比众寡、不判成势/胜负/去取、不输出 STRONG/WEAK。
- network 新增 TWO_SIDE 维度（可选参数，只放 present 概览）。
- Golden 25 项全 PASS；全量回归 71/0。

DTS-027-003 "势在去其寡/成乎众" 经核为去取方向(用神层)，任注及诸书案例(子众母衰→用金生水、
身强杀浅→制乡为福、从杀等)全部走向 用/制/从/吉凶，故"成势/众寡/胜负"正式 HOLD，本投影不代为裁决。

依赖链现状：
- D8 根支关系 ✅、D6 两端构成 ✅（成势判定 HOLD）
- D10 从化：仍依赖"成势"(HOLD)+"极弱无根"(强弱两极 NOT_AUTHORIZED)，且从化属特殊格局专题，
  不与普通身强弱混算 -> 维持 HOLD，不在身强弱网络做"无根即从"候选(原著有真从/假从/破格严辨)。
- D12 天覆地载：结构部分已由 D2+D13 覆盖，整体成格属作用 -> HOLD。
- D9 调候：用神体系 -> HOLD。
