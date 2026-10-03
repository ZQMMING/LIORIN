# L3 判据契约（判据中心 · 非「六维框架」）

> 版本 **v1.3**　　日期 2026-10-03　　状态 **第3刀拓扑层已落（孤立模块）**（v1.2 缺口登记 → v1.3 拓扑层 schema）
> 依据：刘基《滴天髓》京图撰刘基原注本（准神，行号引 `registries/source/raw/DTS_滴天髓_京图撰刘基原注.md`）
> 定位：**事实声明**，不是愿望清单。字段是「现在能读到什么」，不是「应该有什么」。

---

## 〇、缘起：为什么不是「六维」

`bazi_gate.py` 曾有一句 note 定义六维：**月令 / 得地 / 得势 / 通根 / 合冲 / 透干**。

**核原典后该 note 不作准**（2026-10-03）：

| note 的词 | DTS 命中 | 核验结论 |
|---|---|---|
| 得时 | L225/L240/L245/L275/L280/L361 | 概念有，原词是「**得令**」；L245「不必论当令不令」→ 月令不是唯一判据 |
| 得地 | L83/L119/L127/L255/L430/L456 | 概念有（「有根无根」L119/L127），「得地」非原词 |
| 得势 | L280/L604 | ★「得势」**非原词**；对应概念是「**党多/党少**」 |
| 通根 | — | ★与「得地」在 DTS 是**同一概念**（L119 有根无根），note 拆成两维是重复 |
| 合冲 | **0 命中** | 概念明（§八 冲 / §九 合），「合冲」非原词 |
| 透干 | L210/L275 | ★**无维度定义**；L210「人元透于天干者取格」是格局规则 |

**根因**：DTS 不按「维度」组织文本，是一句一格言讲**判据**，不成体系。
**「六维」是后人为工程化提炼的框架** —— 强建它等于把后人框架披上 DTS 外衣。

**故本契约采判据中心：每个字段对应一条 DTS 明文判据，不强套六维。**

---

## 一、10 个契约字段

**9 个主字段 + 1 个复合字段。全部整数/枚举/布尔，无浮点（架构 §1.2）。**

| # | 字段 | 类型 | 值域 | DTS 行号 | 来源 | role | status |
|---|---|---|---|---|---|---|---|
| 1 | `dm_ben_eff` | int | `>= 0` 整数计数 | L9「根拔」/ L88「根拔而祸更甚」 | **`special.get("dm_ben_eff")`**（special_pattern 输出，非直取 L0） | 主 | ACTIVE |
| 2 | `ling_state` | str 枚举 | `旺/相/休/囚/死`（5 值互斥） | L225「气象得令者吉」 | 直取 `_dmp` | 主 | ACTIVE |
| 3 | `root_grade` | str 枚举 | `无/余/本` | L119「不论有根无根」 | **L3 计算**：`_grade_of(_classes)`，再经 `dm_ben_eff==0 → 无` | 主 | ACTIVE |
| 4 | `support_state` | str 枚举 | `SHENG_FU_CHENG_SHI/KE_XIE_CHENG_SHI/PINGHENG` | L280「党多」/ L604「子之党多」 | **L3 计算**：同党/异党离散计数对比 | 主 | ACTIVE |
| 5 | `strength_verdict` | str | `'NOT_AUTHORIZED'`（**键存在，值为字符串**） | — | 常量字符串 | 主 | **NOT_AUTHORIZED** |
| 6 | `chong_adjust` | int 序数 | `-1 / 0 / +1`（严格三值，越界=违反） | L108「旺者冲衰衰者拔，衰神冲旺旺神发」/ L110 两方对比 | 直取 `_dmp` | 主 | ACTIVE |
| 7 | `chong_role` | str 枚举 | `CHONG_ACTIVE/CHONG_PASSIVE/BROTHER_CHONG/NO_CHONG` | L106「申能克寅，是彼冲我」/ L102「四库兄弟之冲」 | 直取 `_dmp` | 主 | ACTIVE |
| 8 | `chong_by` | str \| None | 冲方支名 | L106「能克方为冲方」 | 直取 `_dmp` | 主 | ACTIVE |
| 9 | `library_open` | bool | `True / False` | L96「生方怕动库宜开」/ L98「辰戌丑未四库也，宜冲开」 | 直取 `_dmp` | 主 | ACTIVE |
| 10 | `ling_state_eff` | str 枚举 | **8 值互斥**（见 §1.1） | 合成字段，由 2/6/7/9 合成 | **合成** `f(2,6,7,9)` | **COMPOSITE** | ACTIVE |

### 1.0-b 第 1 刀 · 布尔补齐（v1.1 新增，字段 11~13）

**三个布尔，值域严格 `{True, False}`，由已有判据投影，不新增判据。**

| # | 字段 | 类型 | 值域 | DTS 行号 | 来源（投影式） |
|---|---|---|---|---|---|
| 11 | `de_ling` | bool | `{True, False}` | L225「气象得令者吉」 | `(ling_state == '旺')` |
| 12 | `de_di` | bool | `{True, False}` | L119「有根无根」+ L9「根拔」 | `(dm_ben_eff >= 1)` |
| 13 | `dang_duo` | bool | `{True, False}` | L280「党多」/ L604「子之党多」 | `(support_state == 'SHENG_FU_CHENG_SHI')` |

### 1.5 ★ `de_di` / `root_grade` / `dm_ben_eff` 三层关系（v1.1）

```
root_grade      枚举 3 值  {无, 余/中, 本}     ← 分类视图
dm_ben_eff      序数 int  {0, 1, 2, ...}      ← 本气根计数（经孤根被冲拔/合局化根修正）
de_di           布尔       = (dm_ben_eff >= 1) ← 判据视图
```

**恒等关系（实测 2106 盘，零例外）：**
```
root_grade == '无'   当且仅当   dm_ben_eff == 0
de_di == (root_grade != '无')  == (dm_ben_eff >= 1)
```

**根因**：`bazi_gate.py:240` —— `_root_grade = "无" if _dm_ben_eff0 <= 0 else _root_grade_raw`
**`root_grade` 是 `dm_ben_eff` 的门控派生，不是独立判据。**

**故 `de_di` 是 `dm_ben_eff` 的布尔投影，不是 `root_grade` 的。**
**实测：原先拟落的 `de_di_raw` 与 `de_di_eff` 在 2106 盘完全恒等（交叉表仅两格，零条 raw=True/eff=False）→ 落一个，不落两个。** 落两个即造两个恒等源。

### 1.6 演进方向（记入契约，本轮不做）

```
触发条件: 若将来 DTS L119「原始根」与 L9「有效根」要拆为两个独立判据
动作:
    1. de_di 拆 de_di_raw / de_di_eff 两个布尔
    2. root_grade 去掉 dm_ben_eff 门控, 改为独立计算(_grade_of(_classes) 直接用)
验收: 2106 盘交叉表出现 raw=True/eff=False 格(根被拔但原始有根)
       当前该格样本数 = 0, 即引擎尚无「原始有根但有效无根」的盘
```

**★ 来源列按【代码事实】填，不按架构文档填。**
已发现文档与实现脱节一处：**架构 §2.5 记「`dm_ben_eff` 来源 L0」，实际是 `special.get(...)`（special_pattern 层输出）。**
`root_grade` 亦非直取，是 `_grade_of()` 计算 + `dm_ben_eff==0` 归「无」两步。
**架构 §2.5 的来源列需同步修正（另立，本轮不搭车）。**

### 1.1 ★ `ling_state_eff` 值域（8 值互斥枚举，**非集合**）

```
ling_state_eff ∈ { 旺, 相, 休, 囚, 死, CHONG_BA, CHONG_FA, KU_KAI }
                  └── 5 值同 ling_state ──┘  └──── 3 值合成 ────┘
共 8 值，**互斥**，无集合语义。
```

**下游必须用 `==` 比对，禁止用 `in`。**
（写成 `ling_state ∪ {...}` 会让下游误以为它是集合，从而写出 `in` 查询 —— 故本契约显式枚举 8 值。）

### 1.2 ★ `ling_state_eff` 合成式（顺序敏感，一字不改）

```python
if chong_adjust == +1:
    ling_state_eff = 'CHONG_FA'        # 发（DTS L108「衰神冲旺旺神发」）
elif chong_adjust == -1:
    ling_state_eff = 'CHONG_BA'        # 拔（DTS L108「旺者冲衰衰者拔」）
elif chong_role == 'BROTHER_CHONG' and library_open:
    ling_state_eff = 'KU_KAI'          # 库开（DTS L96/L98）
else:
    ling_state_eff = ling_state        # 未受冲激，取原值兜底
```

**★ 值域硬约束（前置）**

```
chong_adjust 值域【严格】为 {-1, 0, +1}。
越界（任何非此三值）= 契约违反，不是合法输入。

合成式第一支用真值判断 `if _adj:`（代码原样，非 `== +1`）。
在 {-1,0,+1} 域内两者等价 —— 但【若 adj 越界（如 -2），代码会走 BA 分支】。
契约的意图是三值域，因此：
  · 下游遇越界值 → 【断言错误】，不得静默处理，也不得跟着代码走 BA
  · 正确动作是【先改契约（扩值域），再改代码】——不是让契约提前变严格
```

**三条顺序敏感约束（换顺序 → diff 变）：**

1. **`chong_adjust` 优先于 `KU_KAI`** —— 某盘月令既被冲又库开，报 `CHONG_*` 不报 `KU_KAI`。
2. **`KU_KAI` 需 `chong_role == 'BROTHER_CHONG'`** —— 不是单凭 `library_open == True`（后者对 ACTIVE/PASSIVE 也可能为真）。
   **该 `role` 门当前恒真**（`library_open=True` 只在 BROTHER_CHONG 时生成，见 transit_power.py:187-192），
   但**契约写全，不靠「当前恒真」隐性保证** —— 落码时若有人只写 `library_open` 漏掉 role 门，diff 变。
3. **`+1 → FA`（发）、`-1 → BA`（拔）** —— 方向与 DTS L108 一致，不可反。

**源**：`engines/common/transit_power.py:278-284`。本契约把它**公开化**，落码时不改其实现，只保证等价。

### 1.3 ★ 只在月令行有值（硬约束）

```
字段 6~10（chong_adjust / chong_role / chong_by / library_open / ling_state_eff）
    仅在【月令五行的行】有值。
    其余四行（非月令五行）无此 5 个键。
```

**根因**：`transit_power.py:269` 的 `if wx == month_wx:` —— 五行全表里只有月令那行算冲激。

**下游遍历五行全表取值时，非月令行会读到 undefined。**
需要任意五行的受冲处境 → 读 `wangshuai_matrix.branch_chong`（**柱位维度**，四支各一），不是本契约的 5 个字段。

### 1.4 `naming_note`（记，不改）

```
ling_state_eff 的 "eff" 暗示「日主有效旺衰」，实际语义是「月令受冲后状态」。
【本轮不改名】—— 改名破现存消费者（scripts/verify_chong_adjust.py:91-92）。
将来迁至 L4 时一并改。
```

---

## 二、`six_dims` 废弃与迁移记录

### 2.1 核验依据（落码前实测）

| 核 | 结果 |
|---|---|
| `six_dims` 8 个 L1 字段 == `by_element[日主五行]` 同名字段 | **2106 盘 × 8 字段 = 16848 次，差异 0** |
| `six_dims` 全量遍历消费者 | `engines/` 零、`p0_v2/` 零（除生产端）、`tests/` 零 |
| `for k in out` / `out.keys()` / `out.items()` 模式 | 全仓零命中 |
| `ling_state_eff` 现存消费者 | `scripts/verify_chong_adjust.py:91-92` |

**结论**：`six_dims` 8 个 L1 字段是 `by_element` 的**纯副本**，无引擎消费者 → 删除无回归面。

### 2.2 迁移五步（一次性切，不双写）

```
理由：双写的价值是防消费者回归；本项核证「无引擎消费者」= 无回归面 = 双写是空跑。
     （对照 relations 迁移需要双写，因为那里有 93 处消费者。）
```

| 步 | 动作 | 验收 |
|---|---|---|
| 1 | `l3_contract` 加 6/7/8/9/10 五字段，值直取 `_dmp` | — |
| 2 | 验 `l3_contract` 五字段 == `six_dims` 同名字段 | 2106 盘 × 5 = 10530 次 diff=0 |
| 3 | 删 `bazi_gate.py` 的 `six_dims` 整块 | **不删** `dm_row` / `by_element`（L1 数据出口） |
| 4 | `diag_base_matrix.py` 改读 `by_element[dwx]` + raise；`_v12.py` 删除 | — |
| 5 | 全量判定变化 + P1 四本回归 | 变化 0 盘；P1 与基线逐项一致 |

### 2.3 脚本改法

```python
# scripts/diag_base_matrix.py L46
#  旧: six = wm.get("six_dims") or {}
#  新: 两段显式失败
#    段1 —— dwx 由脚本自算(L48 GW[dm]), 引擎 dwx 是 _dmwx(daymaster_element),
#          两者可能不一致; 若脚本 dwx 恰是另一合法五行, 只判 by_element 缺行【不会】raise,
#          会静默读错行 → 必须先比对两者是否相等。
_dwx_eng = wm.get("daymaster_element")
if dwx != _dwx_eng:
    raise KeyError(f"脚本 dwx={dwx} ≠ 引擎 daymaster_element={_dwx_eng}")
#  段2 —— by_element 确实没有该行(引擎侧异常)
_dmp = (wm.get("by_element") or {}).get(dwx)
if _dmp is None:
    raise KeyError(f"by_element 缺 {dwx}")
```

**用工程理由不用语义理由**：脚本 L48/L51 本就在算 `dwx` 并按日主五行取行，`by_element[dwx]` 与其既有写法一致。


---

## 二、第 2 刀 · 缺口登记（v1.2 新增，2026-10-03）

**本节是「已知缺口清单」，是案例反标定的输入，不是待办 TODO。**

### 2.1 `strength_verdict` —— 无 DTS 判据来源

```
现状:  NOT_AUTHORIZED（L3 唯一「判」字段未授权）
根因:
    DTS §十七 衰旺(L235) 只给【处理方向】——
        「旺则宜泄宜伤，衰则喜帮喜助」是「旺了怎么办」，不是「怎么算旺」
    DTS §十五 月令(L225)「气象得令者吉」讲的是月令三元司令(取格取用), 与日主旺衰不同轴
    DTS L245「不必论当令不令」【明确否定】以月令定旺衰
结论:  L3 现状是「有量无判」——
        量层(ling_state/root_grade/dm_ben_eff/de_ling/de_di/dang_duo)有 DTS 依据
        判层(strength_verdict)无判据来源
```

### 2.2 `support_state` —— 阈值三处 ENGINE_DEFINED

| # | 位置 | 内容 | 依据状态 |
|---|---|---|---|
| 1 | `_tong_party > _yi_party` | 「同党 mass 严格大于异党」判为成势 | `ENGINE_DEFINED` —— DTS L604「党多→凶 / 党少→吉」是两分，无「>」这个阈值 |
| 2 | `== ` 兜底 → `PINGHENG` | 同党 == 异党 时判「平横」 | `ENGINE_DEFINED` —— DTS 无「平横」对应判据；实测 252 盘 (12.0%) |
| 3 | `_mass = ben_n + zhong_n + yu_n + stem_n` | 四项相加为「某五行的力量」 | `ENGINE_DEFINED` —— DTS 无此加法口径 |

**三处均无 DTS 依据，不是只第三支。** 保留三值 + 如实标级，不删不改。

### 2.3 `strength_verdict` 档位与依据分级

**值域定义：`strength_verdict` 值域 = 「引擎敢输出的值」的集合。**

| 档位 | 依据 | evidence | usable_as_criteria |
|---|---|---|---|
| `STRONG` | DTS L235「旺则宜泄宜伤」 | `DTS_CITED` | True |
| `WEAK` | DTS L235「衰则喜帮喜助」 | `DTS_CITED` | True |
| `EXTREME_WEAK` | DTS L235「**衰之极者不可益**」 | `DTS_CITED` | True |

**三值，非对称（原典本如此）。**
**`strength_verdict` 字段当前值恒为 `'NOT_AUTHORIZED'` —— 值域已定义，无判据不出值。**

### 2.4 ★ 已否决候选：`EXTREME_STRONG`

```
否决理由: 【三源语义冲突】，不是「无 DTS 依据」
    DTS   L235        「旺之【可】损，以损在其中矣」  ← 说「旺极里含着衰，故可损」
    任注  DT-0121     「旺之极者不可损」              ← 任氏自述改写对仗句(原文写「原注云」区分得很清楚)
    PZZQ  L1034       「旺之极者，亦喜其泄」          ← ★语境是【化气格化神】, 非日主; 结论亦相反
三处都提「旺之极」，但没有一处是「日主旺之极」的定义。概念本身未理清。
```

**重新纳入的触发条件（三条全满足）：**
```
1. 找到「日主旺之极」在 DTS 或任一 canonical 底本（registries/source/raw/）的明文定义
2. 该定义不与 DTS L235「旺之可损」语义冲突
3. 语义冲突可解释（即能说清「旺之可损」与「旺之极」为何是两个层级）
```

**未触发前：值域不含 `EXTREME_STRONG`；下游代码写 `== 'EXTREME_STRONG'` 视为 bug。**

### 2.5 基准集（7 盘）

**文件**：`p0_v2/baseline/strength_baseline.jsonl`
（★ 不放 `case_audit/`：那是六本案例**输入数据**，基准集是**引擎产物**，两者语义不同）
**构建脚本**：`scripts/build_strength_baseline.py`

| 类别 | 盘数 | 依据 | case_id |
|---|---|---|---|
| `EXTREME_WEAK` | 4 | DTS L235 + 案例 | DT-0042 / DT-0043 / DT-0395 / DT-0423 |
| `REVERSE_NOT_WANG` | 3 | DTS L245 + 案例 | DT-0001 / DT-0029 / DT-0245 |

**分类口径（严格按语境，不按关键词）：**
```
EXTREME_WEAK  必须指向【日主】衰极（日主/日元/日干/天衰/身衰/身弱）
              且必须排除「某五行衰极」句式（木/火/土/金/水衰极）
              剔除实例: DT-0105「木衰极者」DT-0117「金衰极者」
                        DT-0121「水衰极者」DT-0402「时支子水衰极」
REVERSE_NOT_WANG  「不作旺论」/「不得旺」——有令但不旺
              剔除实例: PZ-0030（化气语境「化真不得旺运」，非日主旺衰）
              去重:    PZ-0123 与 DT-0001 同八字，保留 DT-0001
```

**用途与限制：**
```
✓ sanity check   —— 4 EXTREME_WEAK 不应判成 STRONG
✓ 反向验证       —— 3 REVERSE_NOT_WANG 不应判成 STRONG
✓ 回归锚点       —— 后续改造的固定测试用例
✗ 定阈值         —— 7 盘画不出边界, 样本不够
✗ 统计验证       —— 样本量不足, 无统计意义
```

**`sample_size_note`：7 盘为 sanity check 规模，非反标定规模。**

```
剔掉污染 > 攒够数量。
原始 19 处命中 → 剔 8 盘污染(某五行衰极 4 + 化气语境 1 + 同八字去重 1 + 4 处重复)
              → 剩 11 → 剔 PZ-0030 化气 + PZ-0123 同八字 → 7 盘干净

7 盘干净 > 15 盘带 8 盘污染。分类口径的严格性优先于样本量。
反标定待「二十造」或其他底本扩充后进行。
```

**扩充待办：** DT-0121 提及「以上二十造」（任注专列的极旺极衰命例），
经核 `registries/source/raw/` 七本底本**均无此二十造**（「二十造」「以上二十」「极旺极衰」「太旺太衰」全七本零命中），
且 DTS 刘基原注本 623 行**通篇无命例**（含八字行仅 3 行，全为举例句）。
**该二十造在 DTS 与 registries 之外，需另找底本。**

---

## 三、第 2 刀 · 架构定性：判层独立

**L3 有量无判是架构级问题，不是字段级。**

```
L3    出「量」  —— 有 DTS 依据的客观字段（ling_state / root_grade / dm_ben_eff /
                  de_ling / de_di / dang_duo / chong_* / fan_ju）
判层  出「判」  —— 判据后补，可案例反标定（strength_verdict 等）
L4    读「判」  —— 不读「量」
```

**为什么必须分出判层：**
```
架构 §2.1 铁律「底层不牢，上层全废」。L4 格局判定需要「身旺可任财官」「身弱忌财官」——
若 L4 拿不到「旺/弱」而只能拿量，它会自己造「从量到判」的规则，
那就是 **L4 越权做 L3 的判**，违背分层。

分层的目的是分工：L3 出量（客观、有 DTS 依据）、判层出判（判据可后补、可反标定）。
硬把「判」塞进 L3 会掩盖「判据无来源」这个根本问题。
```

**本节原则记架构文档（为什么），具体字段记本契约（是什么）。**


---

## 四、第 3 刀 · 拓扑层（v1.3 新增）

**文件**：`engines/common/topology_paths.py`
**验收脚本**：`scripts/verify_knife3_topology.py`

### 4.0 ★ 状态：孤立模块，未接入 L3/L4

```
实测(2026-10-03): grep topology_paths 全仓
    engines/    0 处引用
    p0_v2/       0 处引用
    tests/       0 处引用
    scripts/     1 处(仅验收脚本 verify_knife3_topology.py)
→ 纯孤立新文件, post24→post25 全量判定变化 0 盘 / 2106

理由: 源流步骤3-6 待 L4 xi_wx / 通关第四条件待「劫占」核清

接入触发条件(两条全满足):
    1. L4 xi_wx 就绪(源流步骤3「所喜之神即在此住了」)
    2. 「劫占」定义核清(通关第四条件「能胜劫占之神」)

未触发前: 下游 import 视为【超前接入】。
★ 状态显式化, 不靠读者推断 —— 与 EXTREME_STRONG「已否决候选」、
  劫占「INFERRED 不进 relations.type」同款处理。
```

### 4.1 落法铁律：路径禁止显式图

```
源流/通关路径搜索, 只准用现有 WX_SHENG / WX_KE 两张映射表逐步递推。
【禁止】引入邻接矩阵 / 邻接表 / 节点类等显式图数据结构。
理由: DTS 无「图」, 只有散句 —— 全文无一处把五行生克表述为「图/循环/环」。
      算法可以是路径搜索, 但图的表示不显式化。

实测: adjacency / Graph / Node( / neighbors / adj_list / edge / Edge
      九个词在 topology_paths.py 中各出现 0 次
      WX_SHENG 引用 11 次 / WX_KE 引用 8 次
```

### 4.2 源流 §十九 L245（步骤 1-2 已落，3-6 未落）

| 步骤 | DTS 原文 | 状态 |
|---|---|---|
| 1 源头 | 「取最多最旺，而可以为满局之祖宗者，为源头也」 | **已落** `find_yuan_tou()` |
| 2 流到何方 | 「看此源头，流到何方」 | **已落** `gen_liu_cheng()` —— 只生成路径, **不判终点** |
| 3 住 | 「流去之处，是所喜之神，即在此住了」 | **未落** —— 依赖 L4 `xi_wx` |
| 4 再流 | 「若再流至木地，则气泄为乱」 | **未落** —— 依赖步骤3 |
| 5 阻节 | 「中间即遇阻节，看其阻住之神何神」 | **未落** —— 依赖步骤3 |
| 6 地位 | 「流住之地何地，以知其地位」 | **未落** —— 依赖步骤3 |

**步骤1 的两条约束：**

```
① 「满局之祖宗」是「最多最旺」的同义改写, 非独立判据
   核证: DTS 全文「祖宗」1 处 / 「源头」1 处, 均在 L245 同一句
   并列处理: 遍历 WX 序用 `>` 保留首个最旺者, 其余记 tied_with
             (DTS「取最多最旺」在并列时本就无唯一解)

② upstream_pending: _mass_formula
   排序依据 _mass = ben_n + zhong_n + yu_n + stem_n 是 ENGINE_DEFINED
   (见 §2.2 第3条, DTS 无此加法口径)
   → 源流步骤1 建立在 ENGINE_DEFINED 之上, 【不与「DTS 明文」同级】
```

### 4.3 通关 §二十 L250（四组映射已落）

```
木土 → 火    DTS L250   verify=True
火金 → 土    DTS L250   verify=True
土水 → 金    DTS L250   verify=True
金水 → 水    DTS L250   verify=False  inert=True   ★ 见 §4.4
```

**触发条件统一为 `KE`(相克)** —— 前三组 DTS 明文成关，第四组因不相克而 inert。

### 4.4 ★ 已否决候选：通关第四组「金水而要水」

```
否决依据: 【构造矛盾】, 不是「无 DTS 依据」(底本原样, 一字未改)
    DTS L250  木土而要火 / 火金而要土 / 土水而要金 / 金水而要水
    前三组: 两两相克(木克土/火克金/土克水), 构造一致
            通关神是「生 A 又克 B」的中间调和者
    第四组: 「金水」是【相生】(金生水), 水非第三方, 构造不通

六本底本逐本核证(2026-10-03):
    DTS   四组映射各 1 处          ← 原文如此
    PZZQ  通关 36 处但【零映射表】(L1100「引入第三方五行居中调和」/ L4566「以第三方食伤疏导」)
    QTBJ / SFTK / SMTH / YHZP  零映射
    → 「金水而要水」是 DTS 底本原样, 非 OCR 错
      (若 OCR 错, PZZQ 会有同句可比)

落法: 按原文落, 标 inert=True
      规则在表里, 但触发条件(相克)永不满足 → 【永不执行的规则】
      与 condition_2_pending / usable_as_criteria 同款处理

emendation_candidate: 「金木而要水」(金克木成关, 水通关)
      【未采纳】—— 改它就是替刘基改字; 且无第二来源可对照
```

### 4.5 推断候选：`劫占`（INFERRED，不进 `relations.type`）

```
DTS L250「或被刑冲，或被劫占，或隔一物，皆谓之关也」
    「劫占」全文 1 处 / 「占」全文 1 处 —— 均只在 L250

核证三点:
    ① 「劫」的对应物: L250 未指明是月劫(长生)还是劫财(十神)
       L353「忌劫而官能去劫」提示劫=劫财(去劫=用官克劫财)
       但属【跨语境推断】
    ② 「占」的语义: 与「刑冲」「隔一物」三项并列, 同属【关系事件】
       不是力量比较(L250 不会把事件与力量并列)
    ③ 层级: 位置关系 → relations 层

处置: evidence=INFERRED, 不进 relations.type 枚举
      理由: relations.type 是「事实声明」, 每个 type 代表「有明文支持的关系」
            塞 INFERRED 会污染唯一源
      状态: GUAN_TOPO_CONDITIONS 中 status='PENDING'
```

### 4.6 关的拓扑条件

| 条件 | DTS 原文 | source | status |
|---|---|---|---|
| `XING_CHONG` | 「或被刑冲」 | relations（CHONG/XING） | **READY** |
| `GE_YI_WU` | 「或隔一物」 | distance 档位 | **READY** |
| `JIE_ZHAN` | 「或被劫占」 | INFERRED | **PENDING** |

**distance 档位映射（`mapping: ENGINE_DEFINED`）：**

| 引擎档 | DTS 词 | 明文处数 |
|---|---|---|
| `span_one` | 「中间上下远隔，为物所间」+「或隔一物」 | **2 处**（两者在 L250 上下文指同一现象） |
| `remote` | 「前后远绝」 | 1 处 |
| `adjacent` | DTS 未列为关（两支相邻不构成阻隔） | — |

**`mapping: ENGINE_DEFINED` 的含义**：DTS 三词 vs 引擎三档，**数量对得上但非逐档一一对等**。
这不是「证据不足」，是「词与档非同源」—— 如实标注，不伪装成直接对等。

### 4.7 ★ TODO：两支成关判定未实现

```
当前: list_chong_xing_in_chart(relations) —— 【盘级列举】
      列出盘里所有 CHONG/XING 实例, 不判「两支之间是否成关」
      函数【无 a_zhi/b_zhi 参数】—— 因为这个判定尚未实现
      返回含 scope='CHART_LEVEL_ONLY' / two_branch_verdict=None 显式声明

待补: 判 a_zhi/b_zhi 之间是否成关
      需 relations.instances[k].positions(柱位) + 柱位→地支映射
触发条件: topology_paths 接入 L3/L4 时(同 §4.0)

★ 不记 TODO, 改名后「两支判定」会永远悬空。
```

### 4.8 已落函数清单（自查后）

```
find_yuan_tou(mass)              → 步骤1 源头        参数全部使用 ✓
gen_liu_cheng(yuan_wx, max_len) → 步骤2 路径生成    参数全部使用 ✓
build_yuan_liu_skeleton(mass)    → 步骤1+2 骨架      参数全部使用 ✓
find_tong_guan(a, b)             → 通关映射查询      参数全部使用 ✓
list_chong_xing_in_chart(rel)    → 盘级刑冲列举      参数全部使用 ✓

---

## 五、`strength_verdict` 字段形态

```
值恒为 NOT_AUTHORIZED。
【写进契约】并标 status=NOT_AUTHORIZED —— 它是架构 §2.5 明文定的 L3 契约字段，
缺实现 ≠ 不该在契约里。契约的 status 字段把「未实现」显式化，
与 relations 的 ANHUI `condition_2_pending` 同款处理。
```

---

## 六、视图联动检查项

```
⚠ 契约字段的值来自 L1（wuxing_power / transit_power）。改它们必须重跑：
   - l3_contract 五字段 == _dmp 同名字段   （2106 × 5 diff=0）
   - ling_state_eff 8 值分布不变            （scripts/verify_chong_adjust.py）
   - 全量判定变化                            （scripts/_l4_baseline.py）
   - P1 六本回归                             （scripts/check_P1.py）
```

---

## 七、待审确认项

1. 10 字段表（名/类型/值域/DTS 行号/role/status）
2. `ling_state_eff` 8 值互斥枚举（§1.1）
3. 合成式与三条顺序敏感约束（§1.2）
4. 只在月令行有值（§1.3）
5. `naming_note` 记不改（§1.4）
6. 一次性切不双写（§2.2）
7. `strength_verdict` 写入并标 status（§三）

**审完落码。**