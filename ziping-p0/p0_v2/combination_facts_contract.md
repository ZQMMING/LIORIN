# combination_facts 契约（结构重设计 · 丙方案）

> 版本 **v1.1**　　日期 2026-10-03　　状态 **已验收·落码中**（v1.0 审计态 → v1.1 验证后新增4条硬约束）
> 依据：刘基《滴天髓》京图撰刘基原注本（准神）＋ 架构 §1.2 序数范式（禁浮点）＋ 架构 §2.2 L0 唯一源

---

## 〇、审计缘起与结论

**缘起**：STEP-DBG-14 落 `branch_chong`（任意支受冲 → 柱位维度 `adj`）时发现
`transit_power._by_pos = {支名: 柱位}` 单值映射会把重复支的第二处位置丢掉
（DT-0039 `甲寅戊辰丙寅丙申`：day 寅 参与申寅冲，但 `_by_pos['寅']` 已被 year 占，day 落空）。

**定位**：这不是 `transit_power` 的实现 bug，而是 **L0 `combination_facts` 从设计上就存错了粒度**
—— 存「支名对」而非「柱位对」。架构 §2.2 明定 L0 为唯一源，源粒度不足，下游任何实现都在补。

**审计范围**：`combination_facts` 全九键 + `branch_relations` + `stem_combination_facts`（同源同病，不单审一个字段）。

### 现存粒度四类并存（全部读自 L0 生成代码，非推测）

| 类 | 形态 | 字段 | 柱位可得 |
|---|---|---|---|
| **A** | 支名对 `[a, b]` | `liuhe` / `liuchong` | ✗ |
| **B** | 字符串 `'申子辰合水'` | `sanhe` / `sanhui` / `liuhai` / `liupo` / `sanxing` | ✗ |
| **C** | dict `{pair:[a,b], wx}` | `banhe` | ✗ |
| **D** | dict `{branch, positions}` | `self_punishment` | ✓ **唯一合规** |

**三种实例策略并存**：`liuchong` 按柱位实例（`i<j` 遍历）／`banhe` 走 `_seen` 去重／`sanhe` 走集合包含（三支齐全才报）。

**结论：丙（结构重设计）** —— 加统一 `relations` 出口 + 全部旧键降级为派生视图。
甲（全部改柱位对）浪费：93 处消费者**无一处需要柱位**；乙（只改 `liuchong`）留同类隐患。

---

## 一、relations schema

### 1.1 统一字段

```python
relations: [
  {
    'type':    str,          # 必填  关系类型枚举, 见 1.2
    'branches':[str, ...],   # 必填  参与的支名, 【标准序】(见 1.3)
    'positions':[[str, ...], # 必填  与 branches 一一对齐的柱位名列表
                 ...],      #        positions[i] = branches[i] 所在全部柱位
                              #        柱位名用 'year'/'month'/'day'/'hour', 非索引
    'wx':      str | None,   # 必填  该关系的五行(化神/局五行); 无则 None
    'distance':str | None,   # 可选  'adjacent'/'span_one'/'remote' —— 仅 HE/ANHUI 有
    'blocking':{             # 可选  仅 HE 有
       'intervening': [str], #        中间支
       'blocking_branches':[str], #   阻隔支(化神克星或冲神)
       'has_blocking': bool, #        布尔, 禁浮点
    },
    'instance_count': int,   # 必填  本条关系代表几组柱位实例(见 1.4)
    'meta': {                # 可选  附加信息(原典名/证据等级等)
       'name': str,          #        如 '申子辰合水'(与旧键一致, 供派生)
       'evidence_grade': str,#        如 'WEAK'(暗会)
       'note': str,
    },
  },
  ...
]
```

### 1.2 type 枚举（9 类）

| type | 原典关系 | 支数 | wx | distance | blocking | 实例口径 | 源(L0) |
|---|---|---|---|---|---|---|---|
| `CHONG` | 六冲 | 2 | None | ✗ | ✗ | 柱位实例 | L181 |
| `HE` | 六合 | 2 | 化神 | ✓ | ✓ | 柱位实例 | L180 |
| `ANHUI` | 暗会 | 2 | 局干 | ✓ | ✗ | 柱位实例 | L392 |
| `SANHE` | 三合 | 3 | 局五行 | ✗ | ✗ | 局（三支齐全） | L348 |
| `HUI` | 三会 | 3 | 局五行 | ✗ | ✗ | 局（三支齐全） | L349 |
| `BANHE` | 半合 | 2 | 局五行 | ✗ | ✗ | 去重（一对一条） | L362 |
| `HAI` | 六害 | 2 | None | ✗ | ✗ | 集合包含 | L375 |
| `PO` | 六破 | 2 | None | ✗ | ✗ | 集合包含 | L376 |
| `XING` | 相刑/三刑 | 2~3 | None | ✗ | ✗ | 集合包含 | L377 |
| `SELF` | 自刑 | 1 | None | ✗ | ✗ | 每支一条 | L384 |

### 1.3 ★ 顺序钉死

```
branches 用【标准序】(与 SANHE/SANHUI/ANHUI 表内顺序一致), 不跟盘序。
positions 按 branches 顺序对齐, 不是盘序。

  盘:  year=辰  month=申  day=子  hour=亥
  branches:  ['申','子','辰']              ← 标准序
  positions: [['month'], ['day'], ['year']]  ← 按 branches 对齐, 非 ['year','month','day']
```

**理由**：盘序会随盘变化，同一局在不同盘里 `branches` 顺序不同 → 派生 diff 不稳定。
`positions` 若用盘序，下游派生 `branch_distance` 会错位。

**重复支**：`positions[i]` 是**列表**，可为多值（DT-0039 的两个寅 → `positions[['year','day']]`）。

### 1.4 instance_count 三口径并存

| 口径 | 适用 | `instance_count` | 下游语义 |
|---|---|---|---|
| 柱位实例 | CHONG / HE / ANHUI / HAI / PO / XING | 该关系覆盖的柱位实例组数 | `=1` 可走快路径；`>1` **必须显式展开或聚合** |
| 局 | SANHE / HUI | 1（三支齐全才报） | — |
| 去重 | BANHE | 1（一对一条） | — |

**性能/语义开关**：`instance_count == 1` 的关系，下游不需要位置时可跳过展开。

### 1.5 ★ SANHE 与 BANHE 的边界（钉死）

```
三支齐全 → type='SANHE'，branches 3 支
仅两支   → type='BANHE'，branches 2 支
【不】两支时报 SANHE（半合不是三合）
```

### 1.6 禁浮点

`distance` 是**枚举三档**字符串，非 0.8/0.6/0.4；`has_blocking` 是**布尔**。
全部关系字段无任何浮点权重。符合架构 §1.2。

---

### 1.7 ★ 四条硬约束（v1.1 新增 · 落码前冻结）

**这四条是前置核 1-B 实跑验证过程中确认的事实，非新设计。**

#### ① `positions` 两层结构（SELF 是唯一例外）

```
一般关系 (CHONG/HE/HAI/PO/XING/BANHE/SANHE/HUI):
    positions[k] = [[pos_i], [pos_j]]     # 每元素 = 一组柱位实例
SELF (自刑，单支不成对):
    positions[k] = [pos_a, pos_b, ...]     # 扁平, 该支全部柱位
```

**SELF 例外必须写明**：单支不成对，若按 `put('SELF', [z], [sorted(pos)])` 多包一层，
`positions` 变三层 → 派生值 `[["day","month"]]` vs 旧值 `["day","month"]`，
实测 **399/2106 盘差异**。已修（生成端去多余括号）。

#### ①-b `positions` 元素的**语义类型**（v1.1 补定义）

```
成对关系 (CHONG/HE/HAI/PO/XING/BANHE/SANHE/HUI):
    positions[k] = [[pos_i],[pos_j]]     【有序对】pos_i < pos_j 是结构信息
                                            (谁是 A 谁是 B, 顺序承载语义)

SELF (自刑, 单支不成对):
    positions[k] = 柱位集合, 以列表承载 (JSON 无 set)
                   顺序【不保证】, 消费者按集合处理
```

**关键差别**：本条说的是「集合语义，列表只是承载」，
**不是**「漏定义/没保证顺序」—— 语义完整，谁都不该去"修"它。

**实现侧**（`relations_builder.py`）：`put('SELF', [z], sorted(pos))`
`SELF` 不成对，没有 A/B 之分，把它的顺序纳入硬约束② 是**过度约束**。
`sorted()` 按字母序仅为稳定输出（同集合每次同样的列表），**非语义约束**。
集合语义下 POSK 序与字母序等价，故不改（改动是无收益变更，且会碰 diff）。

#### ② `pos_i < pos_j` 保序（作用域：成对实例）

```
按 year(0) < month(1) < day(2) < hour(3)。
【硬约束】positions 每组实例必满足 pos_i < pos_j。
派生全局排序的键依赖此约束；不成立则还原 L0 原序失败。
```

#### ③ 全局排序派生规则（diff=0 的关键）

```python
# 派生 liuchong / liuhe:
#   【不是】按 relation 顺序展开
#   【而是】汇总 relations 里所有实例 → 按 (pos_i, pos_j) 全局排序 → 输出
inst = []
for r in relations:
    if r['type'] != T: continue
    for pair in r['positions']:
        pi, pj = POSI[pair[0][0]], POSI[pair[1][0]]
        inst.append((min(pi,pj), max(pi,pj), list(r['branches'])))
inst.sort(key=lambda x: (x[0], x[1]))
return [x[2] for x in inst]
```

**实测依据 DT-0230**（`壬子丙午壬子丙午`，双子盘）：

```
L0 原序:  [子,午]@(0,1) [子,午]@(0,3) [午,子]@(1,2) [子,午]@(2,3)
聚合后:
    (子,午) count=3, positions=[(0,1),(0,3),(2,3)]
    (午,子) count=1, positions=[(1,2)]
按 relation 序展开 → [子午][子午][子午][午子]   ✗ 第3、4条颠倒
全局 (i,j) 排序     → [子午][子午][午子][子午]   ✓ 还原原序
```

#### ④ 不同 type 不合并

```
同一柱位对同时是 CHONG 和 HE → 出 2 条 relation, 不合并。
【理由】HE 有 wx/distance/blocking 三个可选字段, CHONG 没有;
        合并会让可选字段语义冲突。
        下游按 type 过滤, 与旧键「各读一个字段」行为一致。

schema 生成规则(落码必守):
    对每种关系类型 T:
        遍历该类型实例 → 聚合为 1 条 {type:T, branches, positions, instance_count}
        不同 T 不合并, 即使 branches/positions 完全相同
```

### 1.7-b ★ `instances` 元素类型（v1.1 补 · 阶段3 落码确认）

**`instances` 元素分两种类型，按 `relation.type` 区分。消费者必须先判 type 再读字段。**

```
PAIR 型  (CHONG / HE / ANHUI / HAI / PO / XING / SANHE / HUI / BANHE):
  {
    'a_pos':    柱位名,            # 必填
    'b_pos':    柱位名,            # 必填  硬约束②: a_pos < b_pos (POSK 序)
    'distance': 'adjacent'|'span_one'|'remote',   # 必填 全 type 通用(位置语义)
    'intervening_branches': [支名],               # 必填 全 type 通用
    'blocking_branches':   [支名],               # 必填 【仅 HE 非空】, 其余恒 []
    'has_blocking':        bool,                 # 必填 【仅 HE 可 True】, 其余恒 False
  }

SELF 型  (SELF):
  { 'positions': [柱位名, ...] }    # 单支不成对 → 无 a_pos/b_pos, 无 distance/blocking
```

**字段矩阵（2026-10-03 钉死，显式约束不留下游猜）**

| type | distance | intervening | blocking | has_blocking |
|---|---|---|---|---|
| HE | ✓ | ✓ | ✓ 可非空 | ✓ 可 True |
| CHONG / ANHUI / HAI / PO / XING / SANHE / HUI / BANHE | ✓ | ✓ | 恒 `[]` | 恒 `False` |
| SELF | — 无该键 — | — | — | — |

**为什么 SELF 不给假值**：给 `[]`/`False` 会让下游 `instances[k]['distance']` 不报错但读到**假值**
——「无阻隔」与「无定义」语义不同，静默假值比 `KeyError` 危险。
**显式失败优于隐式假值**：SELF 走 `KeyError`，强制消费者分路。

**实测（2106 盘）**：`PAIR 型非 HE blocking 恒 []` 2106/2106；
`SELF 型 instances 键集恒 {positions}` 2106/2106。

### 1.8 前置核 1-B 结果（B 结构 · 结构2 · 聚合）

```
OK   liuchong           等价 2106 / 不等价 0        OK   banhe            等价 2106 / 不等价 0
OK   liuhe              等价 2106 / 不价 0        OK   liuhai           等价 2106 / 不等价 0
OK   sanhe              等价 2106 / 不等价 0        OK   liupo            等价 2106 / 不等价 0
OK   sanhui             等价 2106 / 不等价 0        OK   sanxing          等价 2106 / 不等价 0
OK   self_punishment    等价 2106 / 不等价 0
                                            差异总数 = 0
```

**聚合键必须是【有序 tuple】而非 `frozenset`**：DT-0017 `[[丑,未],[未,丑]]` 是两种顺序，
frozenset 并成一条后展开无法还原原序。

**CHONG 的 `instance_count` 分布**（结构2 真实负载）：

| count | relation 条数 | 占比 |
|---|---|---|
| 1 | 750 | 72.9% |
| 2 | 102 | 9.9% |
| 3 | 11 | 1.1% |
| 4 | 3 | 0.3% ← 双子盘，9 条旧差异全出在这 |

**DT-0039 结构2 实际形态**（`甲寅戊辰丙寅丙申`）：

```
branches=['寅','申']  count=2
positions=[[['year'],['hour']], [['day'],['hour']]]
           ↑ 第1组实例        ↑ 第2组实例  ← day 寅 显式存在
```

---

## 二、旧键派生规则（九键全降级为视图）

| 旧键 | 派生表达式 | 等价性 |
|---|---|---|
| `liuhe` | `[r['branches'] for r in R if r['type']=='HE']` | **实测 diff=0** |
| `liuchong` | `[r['branches'] for r in R if r['type']=='CHONG']` | **实测 diff=0** |
| `sanhe` | `[r['meta']['name'] for r in R if r['type']=='SANHE']` | **实测 diff=0** |
| `sanhui` | `[r['meta']['name'] for r in R if r['type']=='HUI']` | **实测 diff=0** |
| `banhe` | `[{'pair':r['branches'],'wx':r['wx']} for r in R if r['type']=='BANHE']` | **实测 diff=0** |
| `liuhai` | `[r['meta']['name'] for r in R if r['type']=='HAI']` | **实测 diff=0** |
| `liupo` | `[r['meta']['name'] for r in R if r['type']=='PO']` | **实测 diff=0** |
| `sanxing` | `[r['meta']['name'] for r in R if r['type']=='XING']` | **实测 diff=0** |
| `self_punishment` | `[{'branch':r['branches'][0],'positions':sorted(r['positions'][0])} for r in R if r['type']=='SELF']` | **实测 diff=0** |

### ★ 前置核 1 结果（2106 盘逐字段 diff）

```
OK   liuchong           等价 2106 / 不等价 0
OK   liuhe              等价 2106 / 不等价 0
OK   sanhe              等价 2106 / 不等价 0
OK   sanhui             等价 2106 / 不等价 0
OK   banhe              等价 2106 / 不等价 0
OK   liuhai             等价 2106 / 不等价 0
OK   liupo              等价 2106 / 不等价 0
OK   sanxing            等价 2106 / 不等价 0
OK   self_punishment    等价 2106 / 不等价 0
                                    差异总数 = 0
```

**含条数、顺序、内容逐条比对。**

### `branch_relations` 派生（本轮回滚裁定）

**原裁「保持独立」→ 回滚 → 并入 `relations`。**

理由：核代码发现 `branch_relations`（`daymaster_branch_relations.py` L118-127）**已带 `positions`**，
schema 反而比 `combination_facts` 规范 —— 它是「`combination_facts` 该长成的样子」，
不是异类，是**同类的升级版**。它的距离/阻隔/暗会语义升为 `relations` 的可选字段。

| `branch_relations` 原字段 | → `relations` 承载 |
|---|---|
| `branches` | `branches` |
| `positions` | `positions` |
| `type: liuhe/anhui` | `type: HE / ANHUI` |
| `huashen` / `anhui_shen` | `wx` |
| `position: adjacent/span_one/remote` | `distance` |
| `intervening_branches` | `blocking.intervening` |
| `blocking_branches` / `has_blocking` | `blocking.blocking_branches` / `blocking.has_blocking` |
| `evidence_grade: WEAK` | `meta.evidence_grade` |

**浮点核清**：`branch_relations` 全文 147 行，`distance` 为枚举三档、`has_blocking` 为布尔，**零浮点，符合 §1.2**。

### `stem_combination_facts` 归属

**不在本契约范围。** 它是天干关系（`wuhe`），与地支关系不同族，粒度问题另审。
本轮只在 `relations` 中预留 `SIDE: 'zhi' | 'gan'` 字段以便未来扩展，**当前恒 `'zhi'`**。

---

## 三、迁移顺序

```
阶段1  加 relations(新源)
       L0 内部由现有生成逻辑重放, 产出 facts['relations']
       【旧九键 + branch_relations 保持原样生成, 双写并存】
       验收: relations 与旧键在同一 process 内逐条 diff = 0

阶段2  旧键降级为视图
       九键改为由 relations 派生(纯函数, 不再单独生成)
       branch_relations 改为 relations 的投影
       ★ 消费者零改动(读法完全不变)

阶段3  六维矩阵接 relations
       wangshuai_matrix 新增 relations / branch_distance / blocking

阶段4  transit_power 改读 relations
       _by_pos 单值映射废弃, 直接用 relations 的 positions
       branch_chong 改由 relations 派生, 重复支不再丢实例
```

**过渡期两个源是否并存**：阶段1 是（双写），阶段2 起否（单一源 `relations`）。

---

## 四、等价性验证

### 方法

```
1. 阶段1 后: 同一 process 内, relations 派生的九键 vs 原生成逻辑的九键, 逐条 diff
2. 全量 2106 盘（六本）逐字段比对
3. 允许差异的例外清单: 【无】
```

### 已预跑的结果（阶段1 等价性模拟）

**差异 = 0**（见第二部分）。模拟脚本：`scripts/precheck_relations_equiv.py`
（该脚本不落码，只用现引擎 `l0_fact_builder.build()` 的原值与 relations 派生值比对）。

---

## 五、回归路径

| 层 | 检查器 | 基线 |
|---|---|---|
| L0 事实 | `scripts/_l4_baseline.py` | post17 |
| L1 五行 | `scripts/check_L1.py` | 2106 ✓ |
| L2 十神 | `scripts/check_L2.py` | 100 ✓ |
| L3 旺衰 | `scripts/verify_L3_L4_independent.py` | 2106 ✓ |
| L4 格局 | `_l4_baseline` 的 `ge/ti/xi/po_n` | 判定不变 |
| P1 病药 | `scripts/check_P1.py` | 1412 病机 |
| P2 冲突 | `scripts/check_P2.py` | 六范式 |
| FAN_JU | `scripts/verify_branch_chong.py` | 2053/2106 一致 |

### ★★ 视图联动检查项（v1.1 补 · 落码前必读）

**本节所有下游字段都是 `relations` 的【派生视图】，不是独立源。**

```
唯一源:  relations            (engines/common/relations_builder.py)
   ├─→ combination_facts 九键       契约 §2 派生规则
   ├─→ branch_relations             daymaster_branch_relations.py (PATCH-REL-06 投影)
   └─→ wangshuai_matrix.branch_chong  transit_power.py (PATCH-REL-03 切源)
```

**⚠ 视图不是「一次降级永久安全」。每次改 `relations` 的 schema，必须重跑：**

| 检查项 | 脚本 | 期望 |
|---|---|---|
| `instances` 派生 `positions` == `positions` | `verify_stage3b.py` | 5483 条 diff=0 |
| `relations` 派生九键 == L0 数据层旧键 | `verify_stage1_relations.py` | 2106×9 = 18954 次 diff=0 |
| `branch_relations` 投影 key 集 == 原 key 集 | `precheck_stage3_branch_relations.py` | 2106/2106 分 type 一致 |
| `branch_relations` 投影值 == 原值 | `verify_stage3b.py` | 939 HE 实例 + 438 ANHUI 实例全命中 |
| 全量判定变化 | `_l4_baseline.py` | post→post 变化 0 盘 |
| P1 逐本回归 | `check_P1.py` | 六本与基线逐项一致 |

**为什么必须写死**：改了 `relations` 而没同步视图，下游读到的是**过期值**且**不报错** ——
这是最静默的错。`branch_relations` 投影失败会 `raise`（不回落旧逻辑），
但「投影成功但字段过期」是它拦不住的。

### 消费者清单

| 类别 | 数量 | 阶段2 影响 |
|---|---|---|
| `liuchong` 直接消费者 | 21 处 / 10 文件 | **零改动**（旧键派生等价） |
| `combination_facts` 消费者 | 72 处 / 24 文件 | **零改动** |
| `branch_relations` 消费者 | 3 处（`bazi_gate.py:148`、`production_entry.py:71`、`pzzq_align.py:335`） | 读法不变 |
| 新增消费者 | — | `transit_power`（改读 relations）、六维矩阵 |

**阶段2 原则：93 处消费者零改动** —— 这是「旧键降级为视图」的全部意义。

---

## 六、六维矩阵消费路径

```python
wangshuai_matrix 新增:
  relations        = facts['relations']                          # 全量关系表
  branch_distance  = {'adjacent': N, 'span_one': N, 'remote': N}  # 从 relations.distance 计数
  blocking         = {'has_blocking': bool, 'blocked': [...]}      # 从 relations.blocking 提
```

**唯一出口 = `relations`。** 不再有两个平行出口（`combination_facts` / `branch_relations` 各一份）。

`branch_chong`（STEP-DBG-14 已落）改为由 `relations` 派生：
```
for r in relations where r['type']=='CHONG':
    对每个柱位实例 (pos_a, pos_b):
        冲方 = KE[支a五行]==支b五行 者
        branch_chong[pos_passive].adj = _compare_both(mw, 支b五行, 支a五行)
```
→ **重复支不再丢实例，DT-0039 的 day 寅 正确落 CHONG_PASSIVE。**

---

## 七、本轮回滚记录

| 项 | 上一轮裁 | 本轮裁 | 原因 |
|---|---|---|---|
| `branch_relations` | 「与 `combination_facts` 不是同类，保持独立（乙）」 | **回滚 → 并入 `relations`** | 核代码发现它已带 `positions`，schema 反而更规范；它是同类升级版，非异类 |
| `self_punishment` | 保留为派生视图（甲） | **维持甲** | 本就是 `combination_facts` 的键（L384），九键口径一致 |

---

## 八、待审确认项

1. schema 字段必填/可选划分
2. `branches` 标准序 + `positions` 对齐（§1.3）
3. SANHE/BANHE 边界（§1.5）
4. 三口径 + `instance_count`（§1.4）
5. 四阶段迁移顺序
6. `stem_combination_facts` 本轮不纳入（预留 `SIDE` 字段）

**审完落码。**