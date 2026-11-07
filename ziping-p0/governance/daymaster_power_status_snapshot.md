# 身强身弱工程状态快照（PATCH-160-B V2）

状态：D2 root_class 细分已完成
HEAD：5a1d7ed0
日期：2026-09-17

---

## 零、D2 完成记录（5a1d7ed0）

新增 `engines/common/daymaster_root_class.py`，8 类离散 RootClass：
- HEAVY_LONGSHENG / HEAVY_LU / HEAVY_WANG(刃别名 ren_alias)
- LIGHT_MU_KU / LIGHT_YU_QI
- SPECIAL_LONGSHENG_YIN（阴长生明根，独立级）
- NONE

关键发现：L0 root_facts 用"同字"判断，网络层补两类（非改 L0、非重算）：
1. 阳干帝旺位/墓库位藏阴干同类（甲卯藏乙、甲未藏乙、丙午藏丁）→ 同五行根
2. 阴长生位藏干全无日主五行（乙逢午藏丁己）→ 十二长生位置明根

阴干墓库按库中本气藏干精确判定：乙戌/丁丑/辛辰/癸未=NONE；己丑=有。
阴干不论羊刃，阴帝旺位保守 LIGHT_YU_QI。
刃=帝旺别名，不另建计算。
network D2 新增 root_class_detail（可选参数，默认行为不变）。
Golden 16/16 PASS；全量回归 67 PASS / 0 FAIL。
无数值/权重/求和/STRONG/WEAK。

下一候选：D13 透藏关系 或 T43 时柱位置；待用户拍板。

---

## 一、已落地文件

| 文件 | 状态 | 说明 |
|---|---|---|
| engines/common/daymaster_power_structure.py | 🔒 FROZEN | 160-A 五轴结构 |
| engines/common/daymaster_power_network.py | 🔒 FROZEN | 160-B V2 多维网络 |
| engines/common/daymaster_power_queries.py | 🔒 FROZEN | 160-C v0 三Query |
| governance/daymaster_power_network_direction.md | 🔒 FROZEN | 方向锁死 |
| governance/daymaster_power_matrix_design.md | 🔒 FROZEN | 16维矩阵 |

---

## 二、160-C v0 三 Query 状态

| Query | state | match_type | evidence |
|---|---|---|---|
| CAN_REN_CAIGUAN | SUPPORTED/NOT_SUPPORTED | STRUCTURE_MATCH/NO_MATCH | refs空（原文待定位） |
| DESHI_BUWANG | UNKNOWN | STRUCTURE_MATCH/NO_MATCH | PZZQ-005-005 |
| SHISHI_BURUO | UNKNOWN | STRUCTURE_MATCH/NO_MATCH | PZZQ-005-005 |

---

## 三、D2 root_type 细分开工规格（已校对通过）

### RootClass 枚举
```
HEAVY
├── HEAVY_LONGSHENG  长生
├── HEAVY_LU         禄（临官）
├── HEAVY_WANG       帝旺
└── HEAVY_REN        刃（帝旺别名，不重算）

LIGHT
├── LIGHT_MU_KU_YANG 阳干墓库
└── LIGHT_YU_QI      余气

SPECIAL
└── SPECIAL_LONGSHENG_YIN  阴长生（明根，约余气）

NONE
```

### 阴阳干规则
- 阳干逢库 = 有根（LIGHT_MU_KU_YANG）
- 阴干逢库：按库中本气藏干是否存在精确判定
  - 乙逢戌：戌中无藏木 → NONE
  - 丁逢丑：丑中无藏火 → NONE
- 阴干余气（乙逢辰、丁逢未）= LIGHT_YU_QI
- 阴长生（乙逢午、丁逢酉）= SPECIAL_LONGSHENG_YIN
- 刃不重算：用已有帝旺识别，只加原典语义标签

### 禁止
- 不做 power=1/2/3
- 不做 HEAVY=3/LIGHT=1
- 不做 sum(root_power)
- 不做根越多→越强
- 不做根力→STRONG/WEAK
- 不做 score/weight/threshold

### 验收 Golden
- 阳干长生 PASS
- 阳干禄 PASS
- 阳干帝旺 PASS
- 阳干羊刃 PASS（帝旺别名）
- 阳干墓库 PASS
- 阳干余气 PASS
- 阴干长生 SPECIAL PASS
- 阴干禄 PASS
- 阴干帝旺 PASS
- 阴干墓库 按藏干精确判定
- 阴干余气 PASS
- 普通无根 NONE

---

## 四、51 触发点分层（已校对）

### 🟢 纯结构（D2 这刀覆盖）
T4/T5/T8/T24/T38/T39/T40/T41/T42 共 9 个

### 🟡 半结构
T3（改名 OUT_OF_SEASON_WITH_ROOT）/ T15（已有）/ T43（时柱位置）

### 🔴 HOLD（作用语义）
T6/T7/T11/T12-T14/T30-T37/T44/T45

### ⚫ 特殊路径（不属普通身强弱）
T16-T29/T36/T46-T51

### T1/T2 纠正
- 不做 Query（PZZQ-005-005 原文自己拆了"得时便作旺"）
- 保留为 SEASONAL FACT

---

## 五、永久边界

- 不评分/不权重/不阈值/不计数
- 不汇总 STRONG/WEAK
- 矛盾共存不裁
- 结构匹配 ≠ 命题成立
- evidence_refs 空 ≠ 有证据
- T1/T2 不进 Query
- T3 用中性名 OUT_OF_SEASON_WITH_ROOT
- T39 按藏干精确
- T42 独立 SPECIAL
- REN 不重算

---

## D11/D13 完成 + 纯结构维度收口（c0b073cc，2026-09-17）

- D13 透藏四态 daymaster_tou_cang.py（bed7a7d7）：BOTH/TOU_ONLY/CANG_ONLY/ABSENT，TOU_ONLY 不判虚浮无力。
- D11 旺相休囚死 daymaster_wang_xiang.py（c0b073cc）：旺/相/休/囚/死纯五行生克映射，旺相≠身强。
- T43 时柱禄旺确认被 D2 per_pillar.hour 覆盖，不另建。
- network 维度集：SEASONAL/ROOT/SUPPORT/DRAIN/CONTROL/TOU_CANG/WANG_XIANG。
- 全量回归 69 PASS / 0 FAIL。
- D6/D8/D9/D10/D12 正式 HOLD（作用/用神/强弱两极，未授权）；D14 非身强弱；D16 冻结。
- 结论：身强弱可纯结构落地的维度已全部落地，详见 matrix_design 第八章。


---

## 作用发动层 ACTIVITY 五模块落地（cfa24158，2026-09-17）

前置：作用有效性原典审计 `governance/audit_effectiveness_report.md`（SHA-1 119FEBD，49c916da）。
核心范式：作用 = ①发动层 ACTIVITY（动/静/引动前提，有确定性结构判据）＋ ②成败吉凶层 EFFECT（有用无用/化真/成势/喜忌，全连用神，NOT_AUTHORIZED 一律 HOLD）。

新增 `engines/common/daymaster_activity.py`（SHA-1 0C9F7B6），五模块全部纯结构、候选态中性命名、不接生产、不改任何封板层：

| 模块 | 函数 | 输出态 | 原典 |
|---|---|---|---|
| ① 透藏动静 | build_activity_tou_cang | 透=ACTIVE_CANDIDATE / 藏不透=DORMANT / 不现=ABSENT | PZZQ-007-031(A)、SFTK-006(B)、DTS-027 |
| ② 冲支三类 | build_activity_clash_class | 四生寅申巳亥=ROOT_MOVED候选 / 四库辰戌丑未=OPENED候选 / 四败子午卯酉=UNKNOWN | DTS-009-003~006、DTS-008-014 |
| ③ 合去归属 | build_activity_combine_away | 只认相邻三对；日主非合方=COMBINE_AWAY(无分)候选；官杀被合=CONTROL_NEGOTIATED贪合忘克前提；日主在合=DAYMASTER_BOUND；隔位不论 | PZZQ-005-004、PZZQ-007-031 |
| ④ 通关候选 | build_activity_pass_through | 相战两端须俱透；通关神透=CANDIDATE/藏=DORMANT/无=NO_PASS；通关透干被合=OBSTRUCTED候选；四组桥完备 | DTS-019-001/002 |
| ⑤ 成势候选 | build_activity_formation | 三合/三会全三支成局+局五行透干=FORMATION_CANDIDATE；成局未透=NOT_TRANSPARENT；多局并列不裁；标局五行相对日主十神大类 | DTS-018-001/002、DTS-009 |

统一边界：无 score/weight/threshold/count 结论；不输出 STRONG/WEAK/用神/吉凶/有用无用/化真/成势/源头/去取；
通关有情成功、能胜劫占、悬隔间物、根拔伤根、库开吉凶、争合妒合、化气格 全部 HOLD；化气候选留 D10 专题默认不启用；
藏者岁运引发属 PATCH-215 冻结；SFTK 盖头为 B 级病药派不单独成 A 级规则。

提交链：49c916da(审计) → 6920062d(①②) → b12494f7(③) → 73761abe(④) → cfa24158(⑤)。
全量回归 72 文件 / 0 失败；ACTIVITY Golden 全 PASS。
