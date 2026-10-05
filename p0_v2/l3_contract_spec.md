# L3 判据契约（判据中心 · 非「六维框架」）

> 版本 **v1.17**　　日期 2026-10-04　　状态 **L2 十神层核过 + 证据分级含 AXIOM/BOOK_CITED/ENGINE_DEFINED_PENDING + 四范式程级收口 + 字段消费类型声明制**（v1.16 §4.25 L2 十神层核验 → v1.17 §4.25.6 藏干表三层分级 + §4.25.7 排序核验 + §4.25.8/9 两个 issue〔裁132/133/134〕· L2 标核过）（v1.7 判层措辞/双源登记/strength_rules登记 → v1.8 §二去重 + §八 文档规范）（v1.5 旺/衰判定核验 + 判层归宿 → v1.6 字段清单唯一出处〔裁48〕/ 冲激字段取值修正〔裁49〕/ compare_key 契约化〔裁45〕/ L215 条件互斥〔裁44〕/ 第4刀作废〔裁42〕）
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
| 5 | `strength_verdict` | dict | `{value,status,predictive,basis}`（**v1.11 起为 dict**，见 §2.6.7） | — | 规则输出结构 | 主 | **ENGINE_DEFINED / predictive=False** |
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

★（v1.6）字段数 / 字段清单引用一律以 §2.7.5「字段唯一清单节」为唯一出处：
  §一 表为 v1.0 历史核验快照（含 `strength_verdict`、未列 `yin_ben_eff`），字段数**不**以本表为准。

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
**`strength_verdict` 当前为 dict 形态（§2.6.7）: value 恒 None, predictive 恒 False —— 值域已定义, 三档映射未落。**

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


### 2.6 ★ 旺/衰判定核验结论（v1.5 新增，裁三十九丙 / 裁四十甲 / 裁四十一乙）

#### 2.6.1 DTS 判定明文核验（三核逐段，2026-10-03）

```
L108-L110 §八 冲
  L108 「旺者冲衰衰者拔，衰神冲旺旺神发。」
  L110 ★原注「子旺午衰，冲则午拔不能立；子衰午旺，冲则午发而为福。余仿此。」
        → DTS 全文唯一一处旺衰判定明文
        → 判据形态 = 【同类相对比较】（子强于午），不是绝对阈值
        → 判据对象 = 【地支之间】的旺衰，不是日主旺衰

L242-L245 §十九 源流
  L245 「不必论当令不令，只论取最多最旺，而可以为满局之祖宗者，为源头也。」
        → ① 否定：当令不令 不是判据
        → ② 方法：最多最旺（相对比较）
        → ③ 对象：满局之祖宗（源流源头）

L232-L235 §十七 衰旺
  L233 「能知衰旺之真机，其于三命之奥，思过半矣。」
  L235 ★原注「旺则宜泄宜伤，衰则喜帮喜助」        ← 处理方向，非判定
        ★「旺中有衰者存，不可损也；衰中有旺者存，不可益也」← 辩证，非纯序数
        ★「旺之可损，以损在其中矣；衰之极者不可益」    ← 极档边界

L32-L35 §五 理气
  L33 「理承气行岂有常，进兮退兮宜抑扬。」
  L35 原注「行之始而进…三月之甲木…行之盛而退…九月之甲木…」
        → 是【同五行在月份上的进退相位】，处理原则，非旺衰判定法

全文词频（判定可能性排序）:
  旺 92 / 多 59 / 衰 26 / 虚 9 / 无气 8 / 实 7 / 寡 7 / 强弱 2 / 当令 2 / 不令 1
  ★「当令」仅 2 处（L240/L245）、「不令」仅 1 处（L245）、
    「强弱」2 处（L438/L440 从儿格，明说「不论日主强弱」）

L438 / L440 从儿格
  「从儿不管身强弱」「不论日主强弱」
        → DTS 在此明确【不管旺衰】，反证旺衰不是该格的判据
```

**★ 核验结论（结果丙）：DTS 无「日主旺衰绝对判定法」。**

```
DTS 给了：① 旺衰的【处理方向】(L235)
           ② 相对比较的【方法原则】(L110 + L245)
           ③ 「旺中有衰」的【辩证补充】(L235)
           ④ 「当令一票定旺衰」的【否定】(L245)
DTS 没给：日主旺衰的【绝对阈值 / 合成公式 / 档位映射】
→ 任何「得分 > 阈值 → STRONG」的规则都是 ENGINE_DEFINED
```

#### 2.6.2 ★ 「相对比较」不是独立判据，是判据之上的方法（裁三十九丙）

```
相对比较原则（L110「余仿此」+ L245「最多最旺」）的前置依赖:
  每支 / 每五行的「旺衰值」从哪来 —— DTS 未给
  可能的来源: 月令(ling_state) / 根(root_grade) / 得势(dang_duo) 的合成
  ★ 该合成规则本身 = ENGINE_DEFINED（见 2.6.4 与 §2.1）

→ 「相对比较」不是独立判据，是【判据之上的比较方法】
  它自身也依赖「值」的定义
→ 因此本轮【不落码 compare_zhis_wang】—— 落码即空函数（输入无来源）
  同 strength_verdict 恒 NOT_AUTHORIZED 同款处理
```

**触发条件：每支/每五行有了 DTS 有据的「旺衰值」→ 即可直接落码。**

#### 2.6.3 ★ L110 与 L245 的「相对比较」是 DTS 一致原则，不是两处独立方法

```
L110 §八   相对比较 → 用于【冲的吉凶】（旺者被衰冲则拔，衰者被旺冲则发）
L245 §十九 相对比较 → 用于【源流源头判定】（取最多最旺者为祖宗）

方法一致（都是「同类比大小」），对象不同（冲 / 源头）
→ 这不是巧合，是 DTS 的一贯取舍：
  凡「谁强谁弱」的判断，DTS 都用相对比较，不用绝对阈值
→ 契约记为【DTS 一致原则】，不是两处独立方法
```

#### 2.6.4 ★ 设计约束：L3 全部枚举字段受「旺中有衰」约束（裁四十甲）

```
DTS L235 明文: 「旺中有衰者存，不可损也；衰中有旺者存，不可益也」
        → 旺衰是【混合的】，不是一维序数

★ 约束范围不是只管 strength_verdict —— 【全部 L3 枚举字段】都受此约束:
  ling_state    (5 值)    旺中有衰时它怎么表达？
  root_grade    (3 值)    同上
  support_state (3 值)    同上
  strength_verdict        不能是纯序数

→ 任何「纯序数」的 L3 字段, 都要评估是否需配套 mixed_flag
→ 本轮只记【约束】, 不落 mixed_flag 代码（两维都无 DTS 判定式）
★ v1.10 更正: 「等有多档反标定样本再定」这一句已失效 ——
  反标定路径实测零区分力(§2.6.6), 不是样本量不足, 是方法前提不满足。
  改为: 等「枚举判据路径」定案（§2.6.6 下一步: DTS 散句组合 / 永久 NOT_AUTHORIZED）后再定。
```

#### 2.6.5 ★ 判层归宿：只有两种形态，没有第三条路（裁四十一乙）

```
架构 §2.5.1 已裁: 「判层独立」—— L3 出量, 判层出判, L4 读判不读量

★ v1.11 更正（核1 实测, 见架构 §2.5.1 v2）:
  「L4 读判不读量」是【设计意图】, 不是执行事实。
  实测 L4 读 l3_contract = 0 处（18 字段全未读）, 它直读 facts + wuxing_power。
  正确定性: L3 与 L4 是【并行出口】, 各自直读 L0/L1, 不是上下游。
  → L3 是契约视图出口（外部/审计/回归用）; L4 是格局判定出口（格局/用神用）。
  ★ 执行顺序 ≠ 分层顺序: L0 → L1 → L2 → L4 → L3（bazi_gate.py L168 vs L284）。

★ 源集合实测（核2-丁, 2026-10-05; 裁八十八甲措辞修正版）:
  L3 与 L4 共享的源: {L0-facts, special, wuxing_power}
      L4 读 facts['special'] 2 处（ge_jie_layer L136 / L878）
  L3 另有、L4 没有的源: relations（只喂 fan_ju）
  ★ 正确表述（不是「L4 源 ⊇ L3 源」—— 那个符号会自我否定）:
      L3 的源 ⊆ L4 的源 ∪ {relations}, 且 relations 只喂 fan_ju, L4 不需要
  结论: L3 对 L4【无新信息】, 并行定性成立。
  ★ L4 不读 relations 是【格局判据不用它】, 不是漏接线。

★ fan_ju 身份登记（裁九十甲, 附触发条件）:
  消费方: topology_paths（已接paipan 顶层, 方局混纯正式口径）
  L4 消费: 0 处 —— 格局判据不读它
  性质: 拓扑层判据输出, 【不是】META_FIELD（它有真实拓扑层消费者）
  触发条件: 若格局判定将来引入「月令受冲开库」为判据, 那时 L4 才需要 fan_ju
  当前: 不需要, 不接线, 不改

现状: 判层的「判」【无 DTS 来源】

→ 判层的最终形态只有两种:
    甲  承认 ENGINE_DEFINED —— 判层是【引擎规则】, 不是 DTS 判据
    乙  判层【永不存在】 —— L4 直接读「量」, 自己合

★ 没有第三条路。不裁 = 判层悬空。
「判层独立」方向对了但不落地点，等于没定。

本轮裁【乙】: 维持 strength_verdict 不出判值（v1.11 起形态为 dict, 见 §2.6.7）
理由: ENGINE_DEFINED 的判据没有 DTS 依据, 落它等于拍
不出判值就是「无 DTS 判据来源」的如实声明（同 condition_2_pending）

→ 判层归属: 【接口存在, 但被禁止出值】（v1.7 修正措辞, 见下）

★ v1.7 措辞修正(裁五十五甲 + 专核实测):
原措辞「判层【暂不存在】」不准确 —— 判层【接口是存在的】:
    engines/common/strength_producer.py :: produce_strength()   接口在
    strength_state 在 engines/ 生产层 100 处 / 23 个文件出现, 20+ 文件在读
    唯一生产者恒返回 value='UNDETERMINED'
      注: strength_producer.py L52「综合生产条件未授权组合
           （无单一经典直产 strength_state）→ FAIL_CLOSED 正确」

「不存在」与「被禁止」对 L4 是两件事:
    不存在 = 无接口, L4 拿不到东西, 要新建接口
    被禁止 = 接口在, L4 能调, 但拿到的值恒为 FAIL_CLOSED, 不用建接口

对 L4 的影响: 接口在 → L4 不必另建接口
                值恒 UNDETERMINED → L4 仍拿不到判定

★ 与 strength_state=UNDETERMINED 的关系【不合并】(裁六十一乙):
两者【框架不同】, 表层相似但语义不同, 强行合并会把强断言降成待办:
    strength_verdict.value = None, predictive=False (v1.11 dict 形态, 见 §2.6.7)
      含义: DTS 层面无绝对判定法(依据 L245 + §2.6.1 三核)
      强度: 强断言 —— 依据源本身不提供
    strength_state  = UNDETERMINED
      含义: 规则未准入(rule_admission 状态机 DRAFT→CANDIDATE→ADMITTED 未达)
      强度: 弱断言 —— 工程流程状态
★ authorized 指【规则准入状态机的 ADMITTED】, 不指「DTS 有无明文」
    (实证: rule_admission.py L3 状态机定义 / L52「无授权综合, FAIL_CLOSED」)
→ 不登记为「同一结论的两个实现」, 也不要求两者同步修改（v1.11 实测管线独立, 见 §2.6.8）
  待办: 由案例反标定产生判据, 且反标定样本量达标后, 再裁甲或乙
    触发条件: 基准集扩到可反标定规模（现 7 盘仅 sanity check, 见 §2.5）
```

#### 2.6.6 ★ 反标定路径当前不成立：两轴并存登记（v1.10 新增，裁七十九丙）

**实测（裁七十六丙 + 裁八十一甲，独立进程 301 盘三类口径）**

```
日主向样本池 = 301 盘
  WANG 220 / SHUAI 79 / NEUTRAL 2（样本不足，不参与区分度计算）
  宽口径 303 与三类 301 差 2 = 中和盘

8 候选字段逐一造「字段值 × 断语」交叉表, 指标 = |P(WANG|v) − P(SHUAI|v)|
（样本量加权: 只看样本数 ≥20 的值; 未加权时 2~3 盘的稀疏值会刷到 1.000）

★ 8 字段的二元切分准确率【全部】= 73.6%
  基线（无脑全判多数类 WANG 220/299）= 73.6%
  ★ 提升 0.0 个百分点 —— 无一字段能区分身旺/身弱
```

**两轴的精确定义（不空写「不同轴」，否则下次还会再试反标定）**

```
轴A 案例作者断语轴
    身旺/身弱/太旺/中和 —— 任注/徐注/他本作者的口径
    可能含: 命局整体气象、格局成败、日主坐支、某段运势
    ※ 它是某个【合成结果】, 不是任一散字段的单调函数

轴B 引擎字段轴（DTS 明文的【散字段】, 未合成）
    ling_state / root_grade / dm_ben_eff / yin_ben_eff
    de_ling / de_di / dang_duo / support_state

实测: 轴B 8 个字段对轴A 预测力 = 0
```

**★ 结论：反标定的对象不是「这 8 个字段」，而是「这 8 个字段合成后的一个更高层判定」**

```
→ 但合成规则本身 = ENGINE_DEFINED 且未定
→ 所以「先反标定再定合成规则」是循环依赖

★ 这不是「引擎错」也不是「案例错」, 是【反标定的方法前提不满足】。

枚举判据三条路的现状:
  DTS 明文路   断（L245 否定以令定旺衰, §2.6.1 三核）
  反标定路     断（本节实测零区分力）
  前人已做路   断（strength_rules 输入是硬编码 demo + 虚引用证据, §4.19）
```

**★ 下一步（裁七十九甲）：枚举判据走「DTS 散句组合」路径**

```
从 L110（相对比较）+ L235（旺则宜泄宜伤, 衰则喜帮喜助）+ L245（取最多最旺）
直接构造 f, 不反标定, 显式承认 ENGINE_DEFINED。

★ 与 EXTREME_STRONG 的处理同款: 显式声明「这是工程规则」, 不假装有 DTS 依据。
★ 另一条备选（乙）: 永久 NOT_AUTHORIZED —— L3 只出量。两者择一, 不得并列。

触发条件: 落码前须先核「散句组合」是否引入 DTS 未给的量纲（如某种计数）;
  若引入, 该量纲必须标 ENGINE_DEFINED 并单列, 不混入 DTS_CITED。
```

#### 2.6.7 ★ `strength_verdict` 落码形态：dict 结构版（v1.11 新增，裁丙）

**为什么不是裸字符串（三条裁的取舍）**

```
甲  落 f(support_state, de_ling, de_di) → ACTIVE      ← 已否决
    理由(实测): 这 3 个字段正是 §2.6.6 零区分力的 8 字段中的 3 个。
    落码后重测仍是 73.6% 基线 —— 输入不含信息。
    ★ ACTIVE 但零预测力, 比 NOT_AUTHORIZED 更危险:
      下游看到 "STRONG" 会当判用, 而 NOT_AUTHORIZED 至少告知无判据。

乙  换输入轴                                    ← 未取(轴A 无引擎侧定义可读)

丙  落码但显式声明「非预测性」                    ← 本节采用
```

**落码形态（`p0_v2/bazi_gate.py` PATCH-L3-02）**

```python
"strength_verdict": {
    "value": None,              # 三态见下
    "status": "ENGINE_DEFINED",
    "predictive": False,
    "basis": "L110 相对比较 + L235 方向 + L245 取最多最旺; 阈值 ENGINE_DEFINED",
}
```

**★ 为什么用 dict 而不是裸字符串 —— 运行时防误用，不靠读文档**

```
下游写  if sv == 'STRONG'   → dict 与 str 恒不等 → 条件恒 False
                            → 静默不命中, 而非按错误的判定继续跑
下游写  sv.get('value')    → 显式取到 None, 看到 predictive=False
```
与 `check_guan_topology` 的 `verdict='INCOMPLETE'`、`usable_as_criteria=False` 同款：
**让「不可直接当判用」成为运行时可感知的, 而不是靠读者记得文档。**

**`value` 三态**

```
None                          三档映射未落（当前状态）
"STRONG"/"WEAK"/"EXTREME_WEAK" 映射已落, 但 predictive 恒 False
★ 恒不出 "EXTREME_STRONG" —— §2.4 已否决, 三源语义冲突
```

**`predictive=False` 是实测属性，不是免责声明**

```
它是【规则输出】, 不是【事实度量】。
L4 要判定仍须自己合 —— 本字段只固定「判定发生在 L3 这一处」, 不提供判据。
```

#### 2.6.8 ★ 与 `strength_producer.strength_state` 的管线关系（v1.11 新增，落前核）

**实测结论：两条管线完全独立，落 f 影响面 = 0**

```
核A  produce_strength() 零参数(L33), 结构上不可能读 L3。
     4 个返回值全硬编码: wang=UNKNOWN / shuai=SHUAI / qiang=UNKNOWN / strength=UNDETERMINED
     ★ 与盘无关 —— 同一盘/不同盘返回值完全相同。
     全仓真实调用点 = 0（8 处命中全在本审计脚本自身）

核B  strength_state 写入点 7 处, 无一处在生产链:
     strength_pipeline.py    3 处  硬编码 demo（produce_states）
     strength_rules_full.py  1 处  print(...)  ← 值只进 stdout
     boolean_enum_test.py    1 处  测试
     rule_admission.py       1 处  状态机字典
     strength_producer.py    1 处  那个硬编码返回值

核C  值域零交集:
     l3_contract.strength_verdict : 三档 + dict 结构
     strength_state               : UNDETERMINED（且恒定）
```

**★ 裁定意义：改 L3 的 `strength_verdict` 不动 producer、不动那 20+ 消费者。**

### 2.7 ★ 裁四十二/四十三/四十四 落定（v1.6）+ mo 核证结论

> 裁决输入（三条同意 + 4 条补）：裁四十二 = 丙+甲 / 裁四十三 = 丙（mo 先核，已核） / 裁四十四 = 甲。
> 本节为契约化记录：**只记结构，不落新码**（涉及代码全部为既有实现）。

#### 2.7.1 补1 · 裁四十二：撤销原名「第4刀 优先级范式」，A/B 分列

```
原名「第4刀 优先级范式」撤销:
  「第4刀」已被方局混纯占用（§4.9, v1.4）;
  字典序契约化不是新刀 —— 是既有 P2 码（bing_debate L116）的补记,
  冠名「第4刀」会与方局混纯同名异物。

A/B 分列, 各自独立条目:
  A  P2 四级字典序契约化（补记, 不落码）        → §2.7.3
  B  L3 弱冲突（1451 盘次）记「合成口径待定」→ v1.12 改「多维并列」(§4.17.2)
     —— 不是优先级项, 不与 A 混;
     （1451 盘次 = 评审会话 L3 弱冲突计数, 库内无此数脚本, 如实记为评审结论）
```

#### 2.7.2 补2 · 裁四十三：比较键逐项 evidence 分级（mo 已核, 给结果）

**核1 · mo 函数位置**（奉裁核验）:

```
engines/common/bing_debate.py
  L59-71   month_order(d, m) -> int
           d = 病机五行, m = 月令五行
           返回「旺相休囚死」序数: 旺1 / 相2 / 休3 / 囚4 / 死5 / 9=未知
           语义 = 病机五行相对月令五行的强度位置
  L98      m  = facts.get('month_qi_element')
  L104     wx = role_to_wx(BING_ROLE[bing_id], dm)   # 病机五行
  L115     mo = month_order(wx, m) if m else 9
  L116     key = (mo, dang, -c['tou'], -c['ben'])    ← mo 居首位
```

**核2 · mo DTS 依据**（奉裁核验）:

```
冲突: bing_debate L14 evidence_refs 引「DTS ZHU_CI_BING.001」
      原文 = L245（源流章）「不必论当令不令, 只论取最多最旺」
      —— 该原文【否定】以「论当令」为判据;
      而 mo 居首 = 先按月令相对强度分档, 档内再比成党 = 【论当令在先】。
      → 所引原文语义与实现排序方向相反, L14 属误引。

可证依据: DTS L223-225 §十五 月令
      「月令乃提纲之府……令星乃三命之至要」（月令三元司令）
      → 「月令提纲」之权重有典文出处;
      → 「四级字典序」本身无 DTS 原文（哪项居首 = ENGINE_DEFINED 顺序）。

结论:
  mo 居首之顺序      → 标 ENGINE_DEFINED（不可标 DTS_CITED, 依据=L245 与其原义冲突）
  mo 取值五档(旺相休囚死) → 可引 DTS L223-225（月令章）
  bing_debate L14 之 L245 误引 → 记「应改引月令章 L223-225 + 顺序标 ENGINE_DEFINED」,
                                 改码另立条目, 本轮只记不改
```

★ 逐项 evidence 分级结论 → 【唯一出处见 §4.15.1】(裁六十二甲: 本节只留核验过程, 不留结论标签)
#### 2.7.4 补3 · 裁四十四：DTS L215 结构形态记录（核验记录，结论已迁）

```
DTS L215（§十三 体用 原注）原文:
  「提纲食伤财官太旺，则取年月时上印比为喜神；
   提纲印比太旺，则取年月时上食伤财官为喜神而用之。此二者，乃体用之正法也。」

★ 本节【只留原文与核验过程】, 结构形态（type/结构/约束/evidence/usable_as_criteria）
  → 【唯一出处见 §4.16.2】（裁六十七甲: §4.16 是契约事实章, §2.7 是核验记录章）

核验缘起: 裁四十四 = 甲（记结构形态, 不落码）。
  本节 v1.6 落时把结构形态直接写在核验记录里, 造成与 §4.16.2 重复 ——
  同一事实两处记录 -> 一处改一处没改 -> 漂移（本次两处已对齐, 见 §4.16.2）。
```
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

### 4.0 ★ 状态：已接入 paipan() 顶层（v1.9 改，裁七十一乙）

> **v1.3 原文记「孤立模块，未接入」—— v1.9 已接入，见下方 v1.9 修正块。**

#### 4.0.1 v1.9 接入记录（裁七十一乙）

```
接入位置: paipan() 顶层新键 `topology`, 与 l3_contract 平级
          ★ 不塞 L0~L4 任何一层, 语义标 derived(派生层)

★ 为何不放 raw_facts:
  源流读 mass, mass 来自 wuxing_power = L1
  若 topology 进 raw_facts(L0 输出) → L0 输出依赖 L1 输出 → 层次倒挂
  L0 不能依赖 L1, 这是分层底线

★ 为何不进 l3_contract:
  四块都是【确定性派生】, 无判定、无阈值 —— 不是判据
  find_yuan_tou 排的是「五行的量」不是「日主的旺衰」

四块依赖核验(2026-10-04, 前置核):
  源流    读 mass(L1)              → 不依赖 L4
  方局    读 relations + pan_zhi(L0) → 不依赖 L4
  通关    读 relations + relations(L0) → 不依赖 L4
  关拓扑  读 relations + pos_of(L0)  → 不依赖 L4
  ★ xi_wx 只出现在注释与 endpoint_pending='L4_XI_WX' 标记里, 不是真依赖
    (v1.3 把「未实现标记」误当「真依赖」, 是本轮纠正的错误)

接的 4 个函数:
  build_yuan_liu_skeleton / check_fang_ju_ming_same_wx /
  check_guan_topology / TONG_GUAN_MAP
  ★ 不接 check_fang_ju_ming_loose —— 对照版不供判定(契约 §4.9.1)
  ★ 不接 find_tong_guan —— 通关按盘无成关实例时无调用方, 映射表已投影

装配函数: bazi_gate.py :: _build_topology(facts, pillars)
  mass     = wuxing_power 各行的 ben+zhong+yu+stem (引擎口径四项, 不重算)
  pos_of   = {支名: [柱位]} 重复支盘一视同仁

实测(独立进程 2106 盘, 崩溃 0):
  topology 存在          2106 (100.0%)
  四个子键齐全           2106 (100.0%)
  浮点                   0 盘 (架构 §1.2 禁浮点)

  源流: 有源头 2106 / status=SKELETON_ONLY 2106 / endpoint=None 2106
        并列(tied_with 非空) 659 (31.3%) —— 并列处理在工作, 不是恒取首个
  方局: jun_za_ming=True 54 (2.6%)  ★ 与 §4.9 实测的 54 一致
        degree=None 2106 / variant=JIA_SAME_WUXING 2106
  通关: 规则数 4 / inert 数 1 (第四组金水)  —— 2106/2106 一致
  关拓扑: verdict=INCOMPLETE 2106 (jie_zhan=None, 劫占未核)
          distance SPAN_ONE 824 (39.1%) / REMOTE 37 (1.8%) / None 1245 (59.1%)
          blocked True 196 (9.3%) / False 1910 (90.7%)
          ★ distance/blocked 均非恒值 —— pos_of + relations 实例链在工作

★ 回归 post31 → post32 判定变化 0 —— 但这是【空的】:
  scripts/_l4_baseline.py 只快照 12 个顶层键, 不含 topology 也不含 l3_contract
  → 拓扑层的真验收是 scripts/verify_topology_wired.py(新建)
  ★ 与 §4.14.3.2 同款: 回归 0 不等于该层被验过, 必须看它是否进了快照
```

#### 4.0.2 接入后仍未落的部分（不是「未接入」，是「已接入但内容待补」）

```
源流步骤 3-6（终点/是否气泄为乱/遇阻节/流住之地）→ 待 L4 xi_wx
  ★ 但骨架(步骤1-2)已出结果, 不是空壳
通关第四条件「能胜劫占之神」            → 待「劫占」核清(§4.5)
  ★ 但前三组已可触发, 第四组标 inert 如实登记
关拓扑 jie_zhan                        → 待劫占核清
  ★ 但 distance/blocked 已落, verdict 如实返 INCOMPLETE 而非 FAIL
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
check_fang_ju_ming_same_wx(rel, zhis) → 方局混纯主判据 参数全部使用 ✓
check_fang_ju_ming_loose(rel, zhis)   → 方局混纯对照版 不在 __all__ ✓
check_guan_topology(rel, a, b, pos_of) → 关拓扑判定   参数全部使用 ✓

---

---

### 4.9 ★ 方局混纯 §十一 L183-L193（v1.4 新增，第4刀）

#### 4.9.1 判据口径（裁二十五丙 / 裁三十三丙）

| 函数 | 角色 | 导出 | 2106 盘命中 |
|---|---|---|---|
| `check_fang_ju_ming_same_wx` | **主判据**（甲版·同五行） | `__all__` ✓ | **54**（FANG_HUN_JU 24 / JU_HUN_FANG 30） |
| `check_fang_ju_ming_loose` | 对照版（乙版·任意） | **不在 `__all__`** | 227 |

- **「同五行」限制 = `ENGINE_DEFINED`** —— DTS 只给木组两例（L185/L189），
  L183 总纲「要得方，莫混局」**无五行限制语**。函数名保留 `_same_wx` 后缀
  即为让此限制显式化（裁三十八甲）。
- 乙版标 `usable_as_criteria: False`（同 `EXTREME_STRONG` 处理）。
- 落盘时**只载甲版**（`criterion_status='JIA_APPROVED'`）。

#### 4.9.2 判据内核：完整组 + 额外一支（裁二十八甲精确化）

```
方混局 (L185)  完整三会 {a,b,c}（relations 有 HUI，三支齐）
             + 第4支 d，d ∈ 【同五行的】三合组，且 d ∉ {a,b,c}
局混方 (L189)  完整三合 {a,b,c}（relations 有 SANHE，三支齐）
             + 第4支 d，d ∈ 【同五行的】三会组，且 d ∉ {a,b,c}
```

- ★「搭一」「混一」的「一」= **额外的一支**，量词，不是「三元组重叠」。
  L189「混一**寅辰**」的「寅辰」用顿号分隔 = 「或寅或辰」，同 L185「亥**或**卯或未」句式。
  （曾误读为「寅和辰两支」→ 判据成「完整三元组重叠」→ 2106/2106 恒 False。）
- ★ 两侧数据源不同：**完整组用 relations**（需三支齐）；
  **额外一支的成员资格用常量表**（`SANHE_GROUPS` / `HUI_GROUPS`）。

#### 4.9.3 四组映射 evidence 分级（裁三十一）

| 组 | HUI ↔ SANHE | evidence | 依据 |
|---|---|---|---|
| 木 | 寅卯辰 ↔ 亥卯未 | **`DTS_CITED`** | L185/L189 双例明文 |
| 火 | 巳午未 ↔ 寅午戌 | `ENGINE_DEFINED` | 五行推，DTS 未举火例 |
| 金 | 申酉戌 ↔ 巳酉丑 | `ENGINE_DEFINED` | 五行推，DTS 未举金例 |
| 水 | 亥子丑 ↔ 申子辰 | `ENGINE_DEFINED` | 五行推，DTS 未举水例 |

**逐组标 `evidence`，不笼统说「方局混纯 DTS 明文」。**

#### 4.9.4 接口约定（裁三十四甲 —— 显示与判断分离）

```
peer_group_display      标准序字符串  '巳午未' / '寅卯辰'    → 显示 / 日志
peer_group_set          frozenset                            → 程序判断
complete_group_display  标准序字符串                         → 显示 / 日志
complete_group_set      frozenset                            → 程序判断
```

**理由：支序在命理有义（顺生逆死），显示错序会被误读。**
与 `relations.positions`（结构序）/ `branch_relations`（集合语义）同类处理。

#### 4.9.5 差异盘核验结论（裁三十三）

```
甲 54  /  乙 227  /  差 173
173 差异盘案例断语含「混局/纯疵/太过」= 8 盘
  逐盘核 → 7 盘「太过」是 DTS【通用程度词】（忌神太过 / 泄气太过 / 制伏七煞太过 …）
          1 盘「纯一」语义相反（YH-0171「四柱纯一不杂」= 不杂，与混局相反）
  跨书同盘去重 → SF-0124 = YH-0095（同八字两书各录），独立证据仅 7 个
→ 8 盘无一是「甲版漏判」证据 → 甲版 54 盘为落点
```

**交叉证据：「混局」0 盘、「纯疵」0 盘。**

#### 4.9.6 程度待核

```
「太过」(L185)「纯疵」(L187/L189)「太强」(L189)  DTS 有词、无档位、无阈值
→ degree = None（显式 None）  degree_pending = True
```

#### 4.9.7 ★ L185「搭一卯」记 pending

L185「搭一亥**或卯**或未」中的「卯」已在寅卯辰组内 → 语义歧义（笔误？重复支盘？）。

**六本底本逐本核（2026-10-03）：无第二来源** —— PZZQ/SMTH/QTBJ/YHZP/SFTK
均无 DTS 此段的对应句（「搭一」「莫混局」全文各 1 处，都在 L185/L183）。
→ **只落「亥」「未」两项，「卯」记 pending。**

#### 4.9.8 ★ 重写等价性证据

```
verify_knife3_topology.py  全绿
  ⑧ 无显式图：adjacency / AdjacencyMatrix / graph / Graph / Node( / neighbors
     / adj_list / edge / Edge  全 0 次；WX_SHENG 11 次 / WX_KE 8 次
  ⑨ list_chong_xing：4 类关系输入 → 2 条（SELF / HE 跳过）✓
  ⑩ find_yuan_tou 边界：全负→None / 含 None→None / 三值并列 tied=['火','金'] ✓

verify_fang_ju_ming.py  2106 盘 崩溃 0
  甲 54 / 乙 227 / 差 173 / 前提 118+159 / evidence 27+27
  —— 与重写前【完全一致】

唯一变化：peer_group_display 从集合序 → 标准序（裁三十四）
```

**本条入契约的意义：下次有人看 `topology_paths.py` 改动历史，
知道「重写」是结构重组、不是改逻辑。**

---

### 4.10 ★ 关拓扑判定 `check_guan_topology`（v1.4 新增，块5）

#### 4.10.1 接口（裁三十七定死）

```python
check_guan_topology(relations, guan_a, guan_b, pos_of=None) -> dict:
    {
      'topo_ok':   bool | None,   # 综合判定；有 None 项 → None
      'conditions': {
        'distance': 'SPAN_ONE' | 'REMOTE' | None,   # DTS L250 远隔/远绝/隔一物
        'blocked':  bool | None,                    # 刑冲阻断
        'jie_zhan': None,                           # ★ PENDING 待劫占核清
      },
      'verdict':   'PASS' | 'FAIL' | 'INCOMPLETE',  # 有 None 项即 INCOMPLETE
      'pending':   [...],
      'detail':    {...},
    }
```

**★「判不了」≠「判了为否」：任一条件为 `None` 则 `verdict='INCOMPLETE'`，
绝不因未判而输出 `FAIL`。** 同 `condition_2_pending` / `usable_as_criteria` 处理。

#### 4.10.2 已落 / 未落

| 条件 | 状态 | 说明 |
|---|---|---|
| `distance` | **已落** | 需 `pos_of={支名:[柱位]}`；多柱位组合取最远档 |
| `blocked` | **已落** | 查该柱位对上的 `CHONG` / `XING` 实例 |
| `jie_zhan` | **`None`（PENDING）** | 劫占 INFERRED，未核（§4.5） |

→ 因 `jie_zhan` 恒 `None`，**`verdict` 恒为 `INCOMPLETE`**（这是如实状态，不是 bug）。

`pos_of` 不传 → `distance` / `blocked` 显式 `None` + `detail.pos_of_missing=True`。
`pos_of` 由调用方传入（本层不重算四柱）。

---

### 4.11 ★ 布尔范式核验表（v1.4 新增，9 条候选逐条定性）

> 记录格式统一为：`判据 | 状态 | 原文行 | 缺失点 | 触发条件`

| 判据 | 状态 | 原文行 | 缺失点 | 触发条件 |
|---|---|---|---|---|
| **天覆地载** | 判据内核缺失 | L119–L127 | 内核「气序」全段未定义；**L127 明说「不论有根无根」→ 直接否定「载 = 有根」** | 找到「气序」定义句 |
| **情协** | 格言体非判据 | L149 / L151 | 「有情」「反背」无判定式（DTS 韵文给境界不给判据） | DTS 或他本给判定条件 |
| **同志** | 格言体非判据 | L153 / L155 | 「生化不错」无判定式 | 同上 |
| **方局混纯** | **部分可落（已落）** | L183–L193 | 布尔可落（§4.9）；程度未定义 | 程度判据另核 |
| 生方怕动 / 败地逢冲 | **已覆盖，不另落** | L96 | 已落于契约 §1 字段 9 `library_open`；唯一出处 DTS L96/L98 | 见 §4.13 追溯链 |
| 形全形缺 | 已核，非判据 | L190 | DTS 全文**零命中**「形全/形缺」 | — |
| 刚柔 | 已核，论述 | §二十七 | 论述 / 泛用原则，非可执行条件 | — |
| 顺逆 | 已核，论述 | §二十八 | 论述 / 泛用原则，非可执行条件 | — |
| （原「方混局」词） | **用词纠正** | L183 | DTS 原词是「**混局**」，无「方混局」独立词条 | — |

**四条新判据候选中：1 条可落（方局混纯）、3 条内核缺失（天覆地载 / 情协 / 同志）。**

---

### 4.12 ★ 判据关键词表（单一源，裁三十五甲+丙）

```python
# engines/common/topology_paths.py 块1
FANG_JU_HUN_WORDS = ['混局', '纯疵']
```

**与本节同步；契约改则代码改。** 头注释指向本节.

#### 4.12.1 剔「太过」「纯一」的理由

```
「太过」 DTS 通用程度词 —— L185 本身就在用（「则太过」），任何命书都高频
              → 不作判据证据
「纯一」 YH-0171 语境是「四柱纯一不杂」=【不杂】，与「混局」语义相反
              → 不作判据证据（拿它当「甲版漏判」证据是反的）
```

#### 4.12.2 ★ 元教训（判据词 vs 通用词）

```
关键词检索法使用前必核：该词是【判据专有词】    vs 【通用程度词】
  通用词（太过 / 太旺 / 中和 / 身旺 / 身弱 …）→ 高频于任何命书 → 不作判据证据
  判据词（混局 / 纯疵 / 旺之极 …）             → 某条判据的专名 → 才作证据
```

**这条不写，下次核别的判据还会踩。**

#### 4.12.3 跨书同盘去重

```
SF-0124 (SFTK) = YH-0095 (YHZP)  同八字 丙戌丙申甲午丙寅，两书各录
→ 独立证据计数时，跨书同盘只算 1
→ §4.11 / §4.9.5 的证据计数已按此去重（8 盘 → 独立证据 7 个）
```

**跨书同盘的重复要在统计里拆开 —— 这是核验规范的一部分，与关键词表同级。**

---

### 4.13 ★ `library_open` 追溯链（裁二十七）

```
DTS L96/L98「生方怕动 / 败地逢冲」
  状态    : 已覆盖，不另落（裁二十三）
  落于    : 契约 §1 字段 9  `library_open`
  唯一出处: DTS L96 / L98
  note    : 若 L96 原文改判，library_open 同步修改，不另开新字段
```

**只记「已覆盖」是断链 —— 必须指到「覆在哪」。**

---



#### 4.14.0 ★ 更正记录（由 §2.7.5 迁入, 裁六十六甲）

```
更正 1（v1.6 落, §2.7.5 原文保留）:
  「判定子组」曾被误引 13 个 —— 实为 5 个
  （13 = 三组合计; 5 = 判定子组计数）。
  —— 这是对【另一个错误】的更正，与本节「18 键」不是同一口径

更正 2（v1.8 落）:
  §2.7.5 曾记「合计 = 13 个」, 与本节实测「18 键」冲突 ——
  同一次 v1.6 commit 内并存两个数字（§2.7.5 与 §4.14）。
  §2.7.5 已整节删除（它是已被实测推翻的版本），本节为唯一出处。

根因复盘: §2.7.5 把 strength_verdict / root_grade_raw / fan_ju /
  boundary_note / evidence_refs 这 5 个归入「不计入」, 本节归入「元信息3 + 判定5」。
  同一批字段两个归属口径 -> 合计数不同。

★ 本条同时是「文档层单一出处」的起因案例:
  同一次提交里两处记录同一事实, 提交前无一致性检查 -> 数字漂移。
  已固化: scripts/check_contract_consistency.py（裁七十丙）, 提交前必跑。
```
### 4.14 ★ `l3_contract` 字段唯一清单（v1.6 新增，裁四十八乙）

> **引用 `l3_contract` 字段数, 以本节为唯一出处, 不凭记忆。**
> 实测方式: 独立进程 `paipan()`, 六本 2106 盘, 全部 18 键。

```
实测键数 = 18 (2106/2106 盘一致)

判定字段(5):
  ling_state / root_grade / root_grade_raw / support_state / strength_verdict
计数字段(2):
  dm_ben_eff / yin_ben_eff
冲激字段(5):
  chong_adjust / chong_role / chong_by / library_open / ling_state_eff
布尔字段(3):
  de_ling / de_di / dang_duo
元信息(3):
  fan_ju / boundary_note / evidence_refs
```

#### 4.14.1 ★ 5 冲激字段取值行修正（裁四十九甲）

```
错位根因:
  transit_power.py L269  `if wx == month_wx:`  ← 只在【月令五行】行赋 5 冲激字段
  bazi_gate.py   L196    _dmp = _wpd[日主五行] ← 但从【日主行】读它们
  → 日主五行 != 月令五行的盘, 5 字段恒 None
    实测 2106 盘: 日主==月令 502 (23.8%) / 日主!=月令 1604 (76.2%)
    → 修正前 76.2% 的盘这 5 字段全是 None

修法: bazi_gate 新增 _dmp_month = _wpd[月令五行], 5 字段改从 _dmp_month 取
      _dmp 保留(供 ling_state 等日主相关字段), 两者分行不混用
      月令行也缺键时显式 None, 不静默回落日主行

语义依据: 5 冲激字段判的是【月令受冲】(transit_power L267-L284), 与日主五行无关

修正后实测(独立进程 2106 盘):
  chong_adjust     None=0缺键=0
  chong_role       None=0      缺键=0
  library_open     None=0      缺键=0
  ling_state_eff   None=0      缺键=0
  chong_by         None=1665  ← 合法值(未被冲时本就 None, chong_role='NO_CHONG')
  ★ 核心: 日主!=月令的 1604 盘中, 4 字段(除 chong_by 合法 None)全部有值

回归影响:
  post28 -> post29 判定变化 0 (2106 盘, 顶层键无增删)
  ★ 零变化的真实原因: 5 冲激字段【无生产消费者】——
    grep 全仓: 仅 bazi_gate 构造 + scripts/ 下 7 个验收脚本读,
    engines/ 与 p0_v2/ 无任何层消费它们 → 修正不触及判定, 变化 0 是真的
```

#### 4.14.2 ★ 工程假设分级：新增 `ENGINE_DEFINED_CONFLICT`

```
原两级:
  DTS_CITED      DTS 明文
  ENGINE_DEFINED 工程定, DTS 无明文

新增第三级(裁四十五):
  ENGINE_DEFINED_CONFLICT  工程定, 且【与 DTS 明文冲突】

★ 归属: P2 bing_debate.compare_key 的 mo-first(见 §4.15)
  —— mo 排字典序首位 = 「月令位序优先于规模」,
     DTS L245「不必论当令不令, 只论取最多最旺」否定此优先
  —— 不区分两级, 下个人看到 ENGINE_DEFINED 会以为只是没依据,
     实际是「有明文反对它, 但工程已采用」
```

---

### 4.14.3 ★ 5 冲激字段三态 + 待接入方候选（v1.7 新增，裁五十二甲）

#### 4.14.3.1 三态定性

```
状态: 【已产出 + 验收层验证 + 生产层零消费】

已产出   : 裁四十九甲修值行后, 4 字段 2106/2106 有值
           (chong_by None=1665 属合法值: 未被冲时本就 None, chong_role='NO_CHONG')
验收层   : scripts/ 下 7 个脚本显式 .get() 读取
生产层   : 零消费 —— ★ 由【变量来源追踪】得出(裁五十三甲), 非按键名 grep:
           生产层唯一相关处是 transit_power.py L271-L284 的【定义端】
           (往 wuxing_power[月令行] 里写这 5 个键), 不是读 l3_contract

★ 不是死字段(有 DTS 明文 L108/L96 + 已通过验收), 也不是预留接口(无既定接入方)
  → 是第三种: 【值已产出、被验收、但没有任何判定读它】
```

#### 4.14.3.2 回归 0 的理由（裁五十六 —— 换掉旧理由）

```
旧理由「零生产消费者」依赖【按键名 grep】—— 该方法已证不可靠(见 §4.18), 作废

新理由:
  生产层读 l3_contract 的这 5 个键 = 0 处        (变量来源追踪实测)
  生产层读 wuxing_power 的这 5 个键 = 5 处      (transit_power 定义端, 值本就有)
  bazi_gate 的修正是「让 l3_contract 的副本与 wuxing_power 对齐」
  → 两处读的值本来就相同 → post28→post29 判定变化 0 是真的

★ 新理由不依赖任何有争议的方法。
```

#### 4.14.3.3 待接入方【候选】清单（列候选, 不列承诺）

```
chong_adjust   → strength 判层的合成输入（判层建立后）?
                 或 L3 弱冲突合成规则（若裁「合成」式）?
ling_state_eff → 月令受冲的最终位, 应进 L3 判定
                 但当前 L3 无判定层 → 待判层建立
library_open   → P1 结构病域（库开/库闭影响病机）?
chong_role     → 供 branch_chong 归属判断, 但与 branch_chong 同源?
chong_by       → 同 chong_role

★ 列候选不列承诺:
  不列候选 → L4 建时重新发明字段
  列承诺   → L4 没用它们就是违约
  两者都是错。

触发条件: mo 口径定案(§4.15.2-b) + L4/P2 若需要月令受冲量, 从这 5 字段读
```

---

### 4.15 ★ P2 `bing_debate.compare_key` 契约化（v1.6 新增，裁四十五乙）

#### 4.15.1 四级字典序（已在生产运行，契约首次记录）

```python
# engines/common/bing_debate.py L116
key = (mo, dang, -c['tou'], -c['ben'])   # 字典序最小者为主病
# L126  ranked.sort(key=lambda r: tuple(r['key']))
```

| 项 | 含义 | evidence |
|---|---|---|
| `mo` | `month_order()` 病五行相对月令的位序 1旺2相3休4囚5死9 | **`ENGINE_DEFINED_CONFLICT`** |
| `dang` | `_dang_level(combo)` 成党0/成势1/不成2 | `ENGINE_DEFINED` |
| `-tou` | 透干数（**排除日干**） | `DTS_CITED` |
| `-ben` | 本气根数 | `DTS_CITED` |
| **字典序顺序本身** | `(mo, dang, -tou, -ben)` 四级且此序 | `ENGINE_DEFINED` |

**引擎运行时 `boundary_note`(保留原文, 裁六十九甲 —— 与上方「依据」列不合并):**

```
「只定主病不判吉凶; 成党阈值(combo>=4)为工程离散值」
  —— 出处: bing_debate.py L166 实际返回该字段, 是引擎契约的一部分
  —— 与本表「依据」列分工:
       boundary_note = 引擎运行时语义边界(定主病 / 不判吉凶)
       依据列         = 阈值出自哪、已标何级
  ★ 不合并: 删掉 boundary_note 里「成党阈值」那半句, 就丢了
    「引擎运行时会输出这一句」的事实。
```

#### 4.15.2 ★ `mo` 的两级问题（裁四十五）

```
问题1  五档无出处:
  DTS 全文搜「旺相休囚死」五字 → 仅 L594「休囚系乎运, 尤系乎岁」
  是句中用语(讲岁运), 不是五行序数表 → mo 的 1~5 档 DTS 零命中

问题2  ★ 排首位与 DTS L245 冲突:
  mo 排字典序第一 = 「月令位序」压过「规模」(dang)
  DTS L245「不必论当令不令, 只论取最多最旺」→ 最旺(规模)应居首
  → mo-first 是「以月令位序代替当令」顶在最前, 正是 L245 否定的那件事
  → 无任何 DTS 明文说「位序优先于规模」

裁决(裁四十五乙): 【不改代码】
  改键序会改变全部主病选择, 而「哪个对」现在无 DTS 判据可决定(反标定样本不够)
  现在改 = 拍 → 契约显式记 mo-first = ENGINE_DEFINED_CONFLICT
  待案例反标定样本量达标后重裁
```

#### 4.15.3 偏序性质（不是全序）

```
by_domain 各域独立排序, 域间【不比较】(架构 §2.8「五域并行, 跨域不冲突」)
SELF_INVENTED 单独成组, 不参与域间比较
→ compare_key 是【域内偏序】, 不是全局全序
```

---

### 4.16 ★ DTS 优先级明文核验（v1.6 新增，裁四十四甲）

#### 4.16.1 全文检索结果

```
「不可得兼」  0 命中
「从重」      0 命中(DTS); SFTK「从重者论」在 SFTK 原书, 非 DTS
「取舍」      作独立词 0 命中(L106/L210/L215 中的「取」是句中动词)
「最多最旺」  1 命中 (L245)
「专一/专则」 2 命中 (L92/L94 「阴支静且专」, 讲阴阳特性非优先级)

★ DTS 无「二者不可得兼」类表述, 无「先…后…」优先级序列(仅 L596「权其轻重」但未给法)
```

#### 4.16.2 唯一一处「条件互斥优先级」明文：L215（裁四十四甲）

```
DTS L215 §十四 原注:
  「提纲食伤财官太旺，则取年月时上印比为喜神；
    提纲印比太旺，则取年月时上食伤财官为喜神而用之。
    此二者，乃体用之正法也。」

结构形态（记结构, 不落码）—— 唯一出处（裁六十七甲, 由 §2.7.4 迁入）:
  type        = 条件互斥优先级型
  结构        = { 条件A(提纲食伤财官太旺) → 取B(年月时上印比)
                  条件B(提纲印比太旺)     → 取A(食伤财官) }
  约束        = A ∧ B 恒假（互斥保证 ——「此二者，乃体用之正法」）
  evidence    = DTS_CITED L215
  usable_as_criteria = False      ← 由 §2.7.4 迁入, 本节此前缺此项
  —— A「太旺」与 B「太旺」分指两类神, 同时成立则无从取舍

为何不落码:
  具体条件 A/B 属 L4 格局/喜用层, L3 无对应对象
  → 记结构 ≠ 造空模板:
     空模板 = 有函数无体(check_guan_topology 恒 INCOMPLETE 同款)
     记结构 = 有形态无实例
  触发条件: L4 格局/喜用层就绪 + 具体条件 A/B 由 DTS 其他段落给出
```

#### 4.16.3 ★ L110 与 L245 的「相对比较」是 DTS 一致原则

```
L110 §八   相对比较 → 用于【冲的吉凶】(旺者被衰冲则拔, 衰者被旺冲则发)
L245 §十九 相对比较 → 用于【源流源头判定】(取最多最旺者为祖宗)

方法一致(都是「同类比大小」), 对象不同(冲 / 源头)
→ 不是两处独立方法, 是 DTS 的一贯取舍:
  凡「谁强谁弱」的判断, DTS 都用相对比较, 不用绝对阈值
```

---

### 4.17 ★ 「第 4 刀 = 优先级范式」作废（v1.6 新增，裁四十二丙+甲）

```
作废理由:
  优先级范式【已在 P2 生产运行】(bing_debate 四级字典序, 见 §4.15)
  底层(L0-L3)【无硬冲突】, 只有弱冲突 —— L3 是「量」层, 量之间是合成关系
  → 「第 4 刀」会变成给已存在的东西再造一个新范式

实际是两件事, 必须分开:
  A. P2 已有四级字典序 → 【契约化】(已完成, §4.15)
  B. L3 弱冲突(1451 盘次反向但同真) → 【多维并列, 无合成需求】(v1.12 改, 见 §4.17.2)

不加区分, 「第 4 刀」还会以另一种形式回来。
```

#### 4.17.1 L3 弱冲突实测（2106 盘）

```
反向组合（同真但指向相反）:
  ① 得令/相 但 无根            257 (12.2%)
  ② 失令 但 有本气根          452 (21.5%)
  ⑤ 得令/相 但 异党成势        176 ( 8.4%)
  ⑥ 失令 但 同党成势          566 (26.9%)
  合计 1451 盘次 = 每盘平均 0.69 处反向

同向组合:
  ③ 得令/相 且 有本根          683 (32.4%)
  ④ 失令 且 无根              688 (32.7%)

★ 反向不是异常态, 是常态 → 这是【合成】问题(量之间怎么合), 不是【消解】问题
★ 反向不是异常态, 是常态 → 但【不是合成问题】, 是【多维并列】(v1.12 定性, 见 §4.17.2)
```

#### 4.17.2 ★ 程级范式收口：L3 弱冲突 = 多维并列，不需程级（v1.12 新增）

**★ 「完成类型」三分类（裁八十九甲）**

```
建设完成    字段 + 码 + 定性 三者齐        布尔 / 序数 / 拓扑 / P2程级
证明不需要  字段 + 码皆无, 定性完成        L3 弱冲突（结论是「不需要程级」）
证明不通    字段 + 码有, 路走不通, 路关闭   枚举判据的【反标定路】
★ 三者不可混称「齐」—— 程级的「完成」是证明不需要, 与建设完成不同。
★ 单列: 反标定路已关闭（301 盘实测 8 字段切分 = 73.6% 基线, 提升 0.0pp）
  它不是第五个范式, 是构造判据的一条方法路径, 该路径已用实测关闭（§2.6.6）。
```


**押后条件已不成立（核1 实测推翻）**

```
原押后条件: 「等 L4 建再定」—— 理由是 L4 可能会读 L3, L3 的合成口径要配合 L4
★ 实测推翻（核1, 2026-10-05）:
  L4 已建, 但【不读 L3】(0/18 字段), 两出口并行（架构 §2.5.1 v2）
  → L3 的合成口径不需要「配合 L4」, 因为 L4 与它无数据依赖
  → 押后条件不成立, 可立即定
```

**定性：这不是「冲突待消解」，是「两个独立维度的取值组合」**

```
得令/相 但 无根     ← ling_state 维度（得令）× root_grade 维度（无根）
失令 但 有本气根    ← ling_state 维度（失令）× root_grade 维度（本）
得令/相 但 异党成势  ← ling_state 维度 × support_state 维度（异党）
失令 但 同党成势    ← ling_state 维度 × support_state 维度（同党）

★ 每一条「反向」都是【不同维度】的组合, 不是【同一维度】的矛盾。
  ling_state 与 root_grade 是两个独立轴, 「旺但无根」在 DTS 里是常理, 不是悖论。
```

**程级范式结论**

```
P2:  已有四级字典序（已契约化, §4.15）
L3:  弱冲突 = 多维并列, 不需要优先级, 不需要合成 —— 并列输出即可
→ 【程级范式完成】
```

**★ 「合成口径待定」的处置：不待了，改记为「无合成需求」**

```
原 §4.17.1 末行「B 项触发条件: 反标定样本量达标后定合成口径」—— 【撤销】
理由: 若维度间无冲突（多维并列）, 就不存在「口径」需要定。
      §2.6.6 的反标定实测（8 字段零区分力）也说明:
      即使反标定成功, 得到的也是「某个合成结果」, 不是「维度间的优先级」。
★ 不删除数据, 只改定性: 从「合成口径待定」改为「多维并列, 无合成需求」。
```

---


### 4.18 ★ 同名字段双源登记（v1.7 新增，裁五十三甲/丙）

#### 4.18.1 双源键清单（专核实测）

```
l3_contract 与 wuxing_power[五行]行 同名的 6 个键:
  ling_state / chong_adjust / chong_role / chong_by / library_open / ling_state_eff

来源:
  l3_contract            bazi_gate.py L294-L305 (从 _dmp / _dmp_month 直取)
  wuxing_power[五行]行    transit_power.py L258-L284 (五行行, 冲激字段仅月令行)
```

#### 4.18.2 ★ 两份真实消费者清单（按变量来源追踪, 非键名 grep）

```
l3_contract 真实消费者: 生产层 0 处, 全部在 scripts/ 验收层
  dm_ben_eff 9 / root_grade 7 / support_state 6 / de_di 3 / ling_state 3
  de_ling 1 / dang_duo 1 / root_grade_raw 1 / strength_verdict 1 / fan_ju 1

wuxing_power 真实消费者(同名键): 生产层有
  transit_power.py L271/272/273/274/280/284  ← 【定义端】往五行行写
  transit_power.py L510 / yongshen_engine.py L167  ← 读五行行
```

#### 4.18.3 ★★ 方法级立规（裁五十七）

```
规: 统计「某字段的消费者」时, 必须同时确认【数据源】。
    若该键名在多个结构中存在(如 l3_contract vs wuxing_power[五行]),
    【按键名 grep 统计的结果一律无效】, 改用变量来源追踪:
      facts['l3_contract'][X] / lc.get(X)        → l3_contract 消费
      wp.get(X) / _dmp.get(X) / _dmp_month.get(X) → wuxing_power 消费
      → 读键那行的接收者变量, 回溯该变量在同文件内的赋值链

★ 与「双路径 import 假差异」「持久 kernel 污染」同级, 进工作规范。

作废范围(裁五十三甲 —— 逐项重核):
  relations 迁移期     「93 处消费者」       ← 待重核
  six_dims 删除期      「零引擎消费者」     ← 待重核
  5 冲激字段期         「零生产消费者」     ← 已重核, 结论成立但旧理由无效
  l3_contract 加字段期 「零回归」          ← 已重核, 新理由见 §4.14.3.2
  branch_relations 期   「147 行零浮点」     ← 非消费者核, 不受影响
```

---

### 4.19 ★ `strength_rules*.py` 登记（v1.7 新增，裁六十甲）

#### 4.19.1 存在

```
6 档判定规则草案:
  VERY_STRONG / STRONG / SLIGHTLY_STRONG / NEUTRAL / SLIGHTLY_WEAK / WEAK / VERY_WEAK
  文件: engines/common/strength_rules.py      :: rule_034_01_strength()
        engines/common/strength_rules_full.py :: rule_034_02_strength_full()
        engines/common/strength_pipeline.py  :: produce_states() / rule_match()
```

#### 4.19.2 三事实

```
零 import      : 三文件被 import 各 0 处(全仓静态扫描)
未接入        : 不在 paipan() 链上
git 有 3 次提交: cf9268f9 PATCH-022B / 7cfbf112 PATCH-034 / 247eed22 PATCH-055
              → 不是历史残留, 是主动落的规则层
```

#### 4.19.3 ★ 三条使其【不可作反标定锚点】的原因（缺一条会被误读）

```
① 主源是 YHZP-138-001(6/7 档), 不是 DTS
   实测 evidence 分布: YHZP 6/7 · DTS 3/7 · SFTK 2/7
   且 evidence 是【切片 ID】不是原文引句

② 输入值来自 strength_pipeline.produce_states 硬编码 demo, 不是真实排盘
   → 6 档的判据组合(wang_state/root_state/support_state ...)输入不真实

③ 切片 ID 引文未核 —— 见 §4.21【全仓虚引用核】
   与 P1 六本 2106 盘 slice_id/bing_domain 结构性全缺 同类
```

#### 4.19.4 价值 + 防重走

```
价值: 曾有人做过一版 6 档 —— 此路走过、走不通(输入不真实), 防止将来重走一遍。

★ 触发条件: 若判层建立, 必须从「真实排盘输入 + DTS 来源」重做,
  【不沿用】本草案的 6 档与证据。
```

---

### 4.20 ★ `xiji_adjudicate` 文案登记（v1.7 新增，裁六十一乙）

```
位置: engines/common/liunian_state.py L143 :: xiji_adjudicate() 的 else 分支

else 分支文案: 「中和/未定不裁喜忌」

实际语义(两个不同态落同一分支):
  NEUTRAL       DTS 中和（§十八 L240 有据）
  UNDETERMINED  规则未准入（rule_admission ADMITTED 未达）

判定行为: weak_dir/strong_dir 都不 True → 循环不进 → xi=ji=[]
          两者都【不裁喜忌】—— 行为正确
文案问题: 把「有据的中和」与「无据的未定」并成一句

★ 隐性判定核查(裁五十五新增核): 无「未判定→默认 STRONG」的默认档
  UNDETERMINED 正确闭锁在「不裁喜忌」, 不是隐性判定

不在本轮修的理由: 改生产代码 + 跑回归, 为一句文案不值
触发条件: 若判层建立后引入第三个「未定」档, 必须把三者分开
```

---

### 4.21 ★ 全仓虚引用核：211 条 `BOOK-NNN-NNN` ID（v1.8 新增，裁七十七甲 / 裁八十丙 / 裁八十三甲）

#### 4.21.1 事实

```
全仓 .py 命中 BOOK-NNN-NNN 式 ID = 211 条（去重）
942 切片库真实「切片ID」字段集合 = 915 个（STATE./STRUCTURE./FOUNDATION. 式）
★ 211 / 211 在真实切片ID 中一个都找不到 → 命中率 0

分布: QTBJ 系 100+ 条（qtbj_climate_candidates.py 独占大半）· DTS 50 · PZZQ 24
      YHZP 22 · SFTK 8 · 含 YHZP-999-999（test_rule_engine.py 的测试占位）
```

#### 4.21.2 「未迁移 / 命名变迁」已排除（裁八十丙三步）

```
第一步 git 全历史 --diff-filter=A 文件名: BOOK_NNN_NNN 式 0 命中
第二步 全仓 66 个归档目录 + 文件名扫描:            0 命中
第三步 942 库「来源」字段: 320/915 含书名, 但全部是「书名 + 章节名」
        （如「DTS 月令（第十五章）」）, 无一条是「书名 + 行号」编号
★ 915 个切片里没有一个的 ID 是 BOOK-NNN-NNN 式 → 不存在「对应不上」, 是两套独立虚构编号
```

#### 4.21.3 ★ 定性：甲类纯元数据，不是断链（裁八十三甲）

**措辞精确到消费类型（第四次同类错误的修正，裁「粗口径掩盖精度」）**

```
★ 精确表述: 这 211 条 ID 从不参与【判定 / 寻址 / 排序】,
  只被 list() 复制与 bool() 非空判断触及。

★ 上轮曾写「从不参与计算或寻址」—— 「从不计算」过宽, 已更正。
  evidence_refs 实测(AST 精确核, 排除局部变量):
    写入 199 处 / 读取 25 处 = 生产 8 + 验收 17
    8 处生产读取全部是搬运或非空判断:
      climate_effect_correction.py L163/L164  .get() 非空判断 + 赋值
      qtbj_climate_candidates.py L545/L553     list(row[...]) 复制
      qtbj_climate_presence.py L78/L82          list(base.get(..., [])) 复制
      bazi_gate.py L456                         透传到输出
    ★ 唯一有「判断」的 L163 判的是「ID 列表非空」, 不是「ID 是否存在于切片库」
```

#### 4.21.4 反向核：引擎确实需要寻址，但用的是另一套 ID

```
切片寻址调用点全仓仅 5 处, 全在 p0_v2/bazi_gate.py:
  L27   read_slice("STRUCTURE.GE_JU.HUA_GE.001")   ← 库内真实格式
  L626  load_slices()
  L653  read_slice(slice_id)
  L671  read_slice(path_or_id)
  L702  load_slices()
★ 引擎设计上【需要】寻址切片(read_slice/slice_authority 都在跑),
  但它用的是 STATE./STRUCTURE. 式正确格式, 没有一处用 BOOK-NNN-NNN。
  → 反向成立: 两侧 ID 体系不兼容, 但方向是「211 条从未参与寻址」, 不是「寻址失败」
```

#### 4.21.5 处置：不删，schema 层统一声明

```
不删除: 211 条不影响任何计算(判定变化 0 已实测), 逐条迁移成本高且多数无真实对应。
★ schema 层统一声明(一处, 不逐条加标记):
    evidence_refs 等字段的 ID 格式 = LEGACY_BOOK_NNN
    该格式不能用于 read_slice 寻址, 只能作人类追溯标记。

★ 触发条件: 若任一 ID 进入【运行时判据 / 排序 / 准入 / 输出生成】,
  重新分类为运行时证据, 必须换成库内真实 ID, 否则不得参与计算。
```

---

### 4.22 ★ 字段消费类型声明制（v1.8 新增，裁八十七甲 + 落法升级）

#### 4.22.1 规

```
任何落进 dict 的字段, 必须显式声明消费类型:

  COMPUTED    值被下游读来参与【计算 / 判定 / 寻址 / 排序】
  META_FIELD  值仅作人类追溯, 无引擎消费
  PENDING     值已产出, 消费方未接入, 附触发条件

★ 未声明类型的字段 = 可疑, 不得进契约。
★ 有了这条, 「字段是否被消费」不再是审计题, 是【声明题】:
  每个字段落码时声明, 审计脚本只核「声明与实现是否一致」。
```

#### 4.22.2 复发记录（四次同类错误，共享根因）

```
① 键名 grep 统计消费者        → 假零结果(引号/盘符/同名双源)
② 按字段名出现次数判「被消费」 → 把「被写入」当「被消费」
③ 局部变量当字典字段          → 正则 key= 把 traceback/stage/tags 算成字段
④ 粗口径掩盖精度              → 「从不计算」盖掉「list() 复制 + bool() 非空」

★ 根源(本条规的由来): 字段【无消费类型声明】, 每次审计都要重新「猜」它给谁用。
★ 根治不是改扫描器(裁八十五丙): 正则改到 AST 也只是把「猜」变准, 不是变对。
  AST 是必要的——它能区分 Subscript(真字典字段) vs Name(局部变量),
  排除 ③; 但它仍不能回答「这字段给谁用」——那只能靠声明, 不能靠扫。
```

#### 4.22.3 本轮已声明的三个 META_FIELD（AST 实测：写入即终点，读取 0）

| 字段 | 写入 | 读取 | 声明 | 依据 |
|---|---|---|---|---|
| `pair_map_evidence` | 1 | 0 | `META_FIELD` | `topology_paths.py` L272 方局判据附带的 evidence（DTS L185/L189），追溯用，非引擎输入 |
| `classic_line` | 4 | 0 | `META_FIELD` | `fan_ju.py` L354/366/380，落它时无消费方 |
| `evidence_chain` | 26 | 0 | `META_FIELD` | 与 `evidence_refs` 同类，名字即「证据链」，供人查 |

```
★ 触发条件（classic_line）: 若将来有人要用「依据行号」做证据审计, 那时再接消费方。
★ 触发条件（evidence_chain）: 若判层要求逐条输出依据链, 那时再接。
★ 触发条件（pair_map_evidence）: 同上; 现与 condition_2_pending 同款——显式化追溯状态。
```

---

### 4.23 ★ 证据分级体系：新增 `BOOK_CITED`（v1.14 新增，裁九十六甲）

#### 4.23.1 原有分级缺一层

```
分级体系（v1.14 之前）:
  DTS_CITED                依据 = 准神 DTS 刘本, 有原文行号
  ENGINE_DEFINED           依据 = 工程自定, 无原文
  ENGINE_DEFINED_CONFLICT  工程自定 + 与 DTS 明文冲突
  CASE_ONLY                依据 = 案例断语, 无原文
  INFERRED                 跨语境推断

★ 缺口: 只有「准神有原文」与「工程自定」两极,
  「六部经典中【非 DTS 的他本】有原文」无处归位。
  专旺 gate_ok 就是这一类: 依据是《碧渊赋》, 在库内, 但不是 DTS。
```

#### 4.23.2 新增分级定义（裁九十六甲）

```
BOOK_CITED    依据 = 六部经典中【非 DTS 的他本】, 有原文行号
              定义: 依据可追溯到 registries/source/raw/ 内六本底本的具体行
              等级: 低于 DTS_CITED, 高于 ENGINE_DEFINED

★ 为什么不是 DTS_CITED: canonical source 是准神 DTS 刘本体系,
  六部经典里另外 5 本是旁参。「在底本内」≠「是准神」——
  这与「DTS 旁参」是不同层级。
★ 为什么不是 ENGINE_DEFINED: 有原文行号可追溯, 不是工程自造。
```

#### 4.23.3 专旺 `gate_ok` 落定 `BOOK_CITED`

```
判据: special_pattern.py L503-506  gate_ok =
        (gs_ben_zw==0 and gs_stem_zw==0 and gs_ju==0)
        and (cai_ben_zw <= 1 and cai_stem_zw == 0 and cai_ju == 0)
      即「官杀无本气、不透、不成局；财至多一余气、不透、不成局」
代码注释自述依据: 《碧渊赋》（L434 注释:「碧渊赋未要求月令当旺，
      只要求局全透干不见官杀」）

★ 原文核（2026-10-05 实测, registries/source/raw/YHZP_渊海子平_原文.md）:
    L9088「碧渊赋(元妙论)」
    L9089  尝谓分二气以定三才，播四时而成万物，皆由命令也。
    L9090  斯令者，贯四时而立四极，专以日主，以定三元。
    L9091  命乃无令而不行，令乃无命而不立…

  「专以日主，以定三元」= 日主专一, 正是 gate_ok 的立意:
  官杀/财一动, 三元就不专。
  → gate_ok 可标 BOOK_CITED（不是 ENGINE_DEFINED）

★ 引用限定 L9089-L9091。【禁止】引用 L9235-L9240:
  该段是现代注解（「现代启示」「耶克斯-多德森定律」）, 不是原典。
```

#### 4.23.4 专旺判据整体依据分层（裁九十五甲）

```
专旺（曲直/炎上/稼穑/从革/润下）实测 70 盘已判, 但切片库覆盖 = 0:

  层                依据                                分级
  ─────────────────────────────────────────────────────────────
  专旺格立意        DTS §十 形象「独象喜行化地」         DTS_CITED
  硬闸门 gate_ok   碧渊赋 YHZP L9089-L9091              BOOK_CITED
  官杀=0 / 财≤1 阈值  工程自定（原文只给立意, 无数字）      ENGINE_DEFINED
  ★ 切片对照        【无】—— CONG_GE 段 4 条全是从格, 专旺 0 条

★ 与 211 条虚引用是【镜像】:
    211 条: 引用了【不存在的切片ID】   —— 引用虚化
    专旺:   判据已实现但【无切片对照】 —— 依据虚化
两条同属「证据链未建立」, 方向相反, 归同一 issue。

★ 补建路径（交 Human Architect）: 碧渊赋在 YHZP/SMTH 底本内可抽,
  但 canonical source 是准神体系, 是否收他本为切片需 User/Human Architect 定。
```

#### 4.23.5 连带扫描结果（裁九十六甲要求）

```
扫「契约里 ENGINE_DEFINED / DTS_CITED 附近是否有他本书名, 却标了错级」:
  → 实测【0 处】错标
special_pattern.py 内的他本引用点 = 2 处:
  L434  《碧渊赋》      —— 专旺闸门     → BOOK_CITED（见 4.23.3）
  L491  《渊海·论运化气》"天干化合者秀气" —— ganhe_tight
        ★ 该处未标分级, 待补; 依据《渊海》非 DTS → 应为 BOOK_CITED
```

#### 4.23.6 ★ PATCH-L4-01：L450 白名单丢弃 `patterns`（v1.14，裁九十八甲）

**缺陷（探针发现，AST 定位）**

```
ge_jie_layer._special_of(spv):
  L110  if spv.get('patterns') is not None: return spv    ← 复用已算 special
  L112  return build_special_patterns(...)                ← 兜底重算

但 bazi_gate L450 白名单只 8 键, 【无 patterns】
→ spv 里根本没这个键 → spv.get('patterns') 恒 None → L110 恒 False
★ 三重后果:
  ① build_special_patterns 每盘被跑两遍（PATCH-GAP11d「单一数据源免重算」完全失效）
  ② L902 的 _cong_pat 从格证据链恒为 None —— 格局判定的出处是空的
  ③ patterns 是唯一带 note + facts 的证据链载体, 丢弃即证据链虚化
     （与 §4.21 的 211 条虚引用同病: 引用虚化 vs 出口虚化）
```

**修复范围（最小）**

```
L450 白名单 + patterns  一个键
不加 judgment_status / mu_mie_state —— 生产消费者 0, 加了徒增回归面
```

**验收（探针 + 回归，裁九十八甲：回归即验证，不做同构重算）**

```
探针  P1 白名单含 patterns        PASS
     P2 2106 盘 0 崩溃            PASS
     P3 patterns 真出口           PASS（special 8键 → 9键）
     P4 facts['special'] AST = 2   PASS
回归  post33 -> post34  判定字段总变化 = 0（2106 盘）
★ 预期 A 成立: 修复是【纯性能】, 两条路径同结果
  → build_special_patterns 是确定性的, 无副作用
  → 同构重算（加 facts 导出入口改生产代码）不需要, 已撤回该方案
```

**★ 撤回记录：本轮曾误报「两路 special 分叉 427/2106」**

```
错因: 重算时把 paipan 顶层投影当作内部 facts 传入
     顶层有 hidden, 无 hidden_stems（L434 显示顶层 hidden 是 f["hidden_stems"] 的派生）
     → 从杀/从官的藏干细分失效 → 大量误判 None
★ 该数字已撤回, 未进契约。教训: 回归可以当验证器, 不要为「提前验证」改生产代码。
```

#### 4.23.7 单立 issue：`judgment_status` 全仓 8 源同名不同义

```
实测（AST, 无窄过滤）: judgment_status 读取 12 处, 【全部是 tests/ 断言】
★ 但它们读的不是 special 的 judgment_status, 而是各自模块的同名字段:
  test_climate_structure_golden      → CLIMATE_STRUCTURE_ONLY
  test_daymaster_power_structure      → NOT_AUTHORIZED
  test_namespace_alignment_golden     → GEJU_CANDIDATE_ONLY / CLIMATE_CANDIDATE_ONLY
  test_qtbj_climate_golden / presence → CLIMATE_CANDIDATE_ONLY
  test_transit_power_golden           → TRANSIT_POWER_*
  test_unified_overview_golden        → PARALLEL_VIEW_NO_TOTALIZER
  test_xiang_shen_golden              → XIANG_ROLE_CANDIDATE_ONLY
  test_yongshen_geju_golden            → GEJU_CANDIDATE_ONLY
  test_zhonghe_structure_golden       → ZHONGHE_STRUCTURE_ONLY
  + special.judgment_status（0 消费者）

★ 本仓 judgment_status 是【跨模块通用字段名】, 8 处含义各不相同。
  与 support_state / ling_state 的同名双源同款, 但更严重 —— 那两个是两个引擎数据源,
  这个是 8 个不同模块的同名不同枚举值。
★ 后果: 按 judgment_status 统计「消费者」必然出错（本轮已连续出错两次）。
  与 §4.18 同名双源登记同款处置 —— 但本轮只登记, 不治理。
触发条件: 若将来要按 judgment_status 做跨模块查询/汇总, 必须先加命名空间前缀。
```

---

### 4.24 ★ `special_pattern.py` 判定树（L4 内部核，2026-10-05 结账）

> 数据源：源码实读（`engines/common/special_pattern.py` 683 行），非推断。
> 实测样本：六本 2106 盘，独立进程。

#### 4.24.1 输出结构（探针实测）

```
paipan 顶层 special = 9 键（PATCH-L4-01 后）:
  cong_type / cong_state / zhuanwang / zhuanwang_state /
  hua_qi / hua_qi_state / liangqi / mu_mie / patterns
源码 build_special_patterns 返回 10 键, 白名单只放 9（judgment_status 未放, 消费者 0）
patterns 是唯一带 note + facts 的证据链载体（COMPUTED）
```

#### 4.24.2 四类格的判定条件与实测分布

```
【从格】354 盘 | CONFIRMED 222 / CANDIDATE 132
  类型: 从财 122(91C/31K) · 从儿 93(52C/41K) · 从杀 83(50C/33K)
        从官 54(29C/25K) · 从势 2(全CANDIDATE)

  判定条件（源码 L186 起）:
    前置 rootless = (dm_ben_eff == 0 and yin_ben_eff == 0 and not _yin_block)
      _yin_block = 印透干 且 (化根后本气>=1 或 中气>=1 或 余气>=1)   ← 印透有根则不从
      ★ 根数按【化根后】三级（本气/中气/余气）计, 不只看本气（L165-183 注释）
    降级 CANDIDATE: virtual_support / ke_struck / yin_fanwu / yin_ke2 /
                    jia_xu_sha 任一为真
    从儿分支（L392, 从儿不论身强弱）:
      gs_ben==0 且 gs_stem==0 且 yin_ben_eff==0 且 ss_pow 且 !dm_ling
      且 !cai_lead 且 dm_ben_eff<=1
      ★ 若 cai_stem>=2 and cai_ben>=1 → 改判【从势格】（食伤生财顺克泄）
    从杀→从官细分（L409-426）:
      正官(异阴阳)藏干支占优, 或支均而正官透干占优 → 从官格
      （DTS 官杀多混称, 故须细分）
    气候假从（L403）: XU_SHI_HAN_TU 且 财成势 → 从财格 + CANDIDATE

【专旺】70 盘 | CONFIRMED 29 / CANDIDATE 41
  曲直 25 · 润下 16 · 炎上 12 · 稼穑 11 · 从革 6

  硬闸门 gate_ok（L503-506）:
    (gs_ben_zw == 0 and gs_stem_zw == 0 and gs_ju == 0)
    and (cai_ben_zw <= 1 and cai_stem_zw == 0 and cai_ju == 0)
    即「官杀无本气、不透、不成局；财至多一余气、不透、不成局」
  CONFIRMED_ZW（L517）: gate_ok 且 dm_ju>=1（支局全）且 本行透干 且 日主属该行
  CANDIDATE_ZW（L520）: gate_ok 且 party>=4 且 dm_ben_eff>=2 且 本行透干
  破格扣除: 合局化去官杀/财本气（L445-457）· 天干合化财星扣透干（L459-478）
  印旺非专旺（L485）: dm_ju==0 且 _dm_ben_pure<=1 且 yin_ben_eff>=3
  月令当旺【不入硬闸门】, 仅作置信度加权（L434-440, 据碧渊赋）

【化气】3 盘（全部化木气格）
  真化 CONFIRMED: 日干与【紧邻】（月干/时干）五合 + 化神得令或成势
                 + 日主无根无印
  假化 CANDIDATE: 微根 / 微印 / 化神被克制
  合而不化: 隔位遥合 / 化神不当令不成势 → 不判
  ★ 化神为木另须四支局全（亥卯未/寅卯辰, 沈孝瞻原文明举）

【母灭】50 盘
  母多灭子/印势漂没 40 · 土多金熄 5 · 水多木熄 2 · 火多土熄 2 · 金多水熄 1
```

#### 4.24.3 ★ 专旺与从格：并列，非分支（核2-乙 定性）

```
实测: 同时命中 cong_type 与 zhuanwang 的盘 = 0 / 2106
      只命中从格 354 / 只命中专旺 70  → 完全互斥
源码 L559 有 _existing_cong 检查（专旺段会看是否已判从格）,
      但两者是【并列的两条规则】, 不是分支关系。

★ 修正上一轮误读: 「专旺 4 条挂 CONG_GE 段」不成立。
  CONG_GE 段实有 4 条, 但【全是从格】:
    .001 真从格成立后取用神（DTS 下篇十二 从象）
    .002 假从（DTS 下篇十四 假从）
    .003 五阳从气五阴从势（DTS 上篇七 天干）
    .004 真从判定条件（DTS 十二 从象）
  → 专旺切片覆盖 = 0 条（不是 4 条）
```

#### 4.24.4 依据分级三层（核2-丙）

| 层 | 依据 | 分级 |
|---|---|---|
| 从格判据 | DTS 下篇十二/十四 从象·假从；PZZQ L187/L4936 印透有根不从 | `DTS_CITED` + PZZQ 旁参 |
| 化气判据 | DTS 化象章 L436「化得真者只论化」 | `DTS_CITED` |
| 专旺格立意 | DTS §十 形象「独象喜行化地」 | `DTS_CITED` |
| 专旺硬闸门 `gate_ok` | 碧渊赋 YHZP L9089-L9091 | `BOOK_CITED` |
| 官杀=0 / 财≤1 阈值 | 工程自定（原文只给立意，无数字） | `ENGINE_DEFINED` |
| `ganhe_tight`（L491） | 《渊海·论运化气》「天干化合者秀气」 | ★ **未标分级, 待补 → 应为 `BOOK_CITED`** |

#### 4.24.5 ★ 单立 issue：专旺判据已实现但切片对照 = 0（核2-乙/丙）

```
现状: 专旺 70 盘已判（29 CONFIRMED / 41 CANDIDATE）, 但
      STRUCTURE.GE_JU.CONG_GE 段 4 条全是从格, 【专旺切片 0 条】

★ 与 §4.21 的 211 条虚引用是【镜像】, 同属「证据链未建立」:
    211 条虚引用: 引擎引用了【不存在的切片 ID】  —— 引用虚化
    专旺:       判据已实现但【无切片对照】      —— 依据虚化
  方向相反, 归同一 issue。

依据分层（核2-丙 已定, 见 4.24.4）:
  格立意 DTS §十 DTS_CITED / 硬闸门 碧渊赋 BOOK_CITED / 阈值 ENGINE_DEFINED

★ 补建路径（交 Human Architect 拍）:
  碧渊赋在 YHZP L9084+ / SMTH L22905 底本内可抽;
  但 canonical source 是准神 DTS 体系, 是否收他本为切片需 User 定。
  ★ 本轮只登记, 不动切片库（切片库是 canonical source, 非本层职责）。
触发条件: 若 Human Architect 批准补建, 则专旺判据从「无对照」升级为「可追溯」。
```


---

### 4.25 ★ L2 十神层：`ten_god` 与五行生克表分级（v1.16，2026-10-05）

> 底层唯一未核分层的核验结果。探针 P1–P10 全 PASS 才出真实数据（立规 2f）。

#### 4.25.1 `ten_god` 实现形态：算法，不是查表

```
engines/common/l0_fact_builder.py L64-82
  def ten_god(day_stem, other_stem):     ← 签名 P6 实测一致
    L69  same_yin_yang = (day_stem in YANG) == (other_stem in YANG)
    L70  sheng = {木→火, 火→土, 土→金, 金→水, 水→木}
    L71  ke    = {木→土, 土→水, 水→火, 火→金, 金→木}
    L72-81  五个分支: 同五行 / 我生 / 我克 / 克我 / 生我 × 阴阳 → 十值

★ 是算法不是查表 —— 100 组组合全部由 5 条规则推出, 不可能「某格写错」。
  这使「手写查表出错」类风险在本实现上不成立。

探针 P1-P7（锚点全 PASS 才跑真实数据, 立规 2e/2f）:
  P1 甲见庚 → 七杀（克我·同阴阳）    PASS
  P2 甲见癸 → 正印（生我·异阴阳）    PASS
  P3 甲见丙 → 食神（我生·同阴阳）    PASS
  P4 甲见己 → 正财（我克·异阴阳）    PASS
  P5 甲见乙 → 劫财（同五行·异阴阳）  PASS
  P6 ten_god 签名 (day_stem, other_stem)          PASS
  P7 全十类产出 10 类（值域正好 10, 无 '?'）       PASS
  附  异干误判比肩 0 处                            PASS
```

#### 4.25.2 ★ 分级：骨架 `AXIOM` / 正偏命名 `ENGINE_DEFINED_PENDING`

```
【生克骨架】我生/我克/克我/生我/同我   →  AXIOM
   依据: 依赖的 sheng/ke 表本身是 AXIOM（见 4.25.3）

【正偏命名】同阴阳为偏 / 异阴阳为正   →  ENGINE_DEFINED_PENDING（新增分级）
   已核: DTS L210「财官印绶发偏正，兼论食伤八格定」
        —— 此句说「财官印有正偏」, 但【未给「同/异阴阳」的映射规则】
   实现的映射（源码 L72-81）:
        同五行: 同阴阳=比肩   异=劫财
        我生  : 同阴阳=食神   异=伤官
        我克  : 同阴阳=偏财   异=正财
        克我  : 同阴阳=七杀   异=正官
        生我  : 同阴阳=偏印   异=正印
   ★ 比劫/食伤是「同=专」, 财官印是「异=正」—— 两侧命名方向相反,
     这是传统命理固有（前者属「同我/我生」侧, 后者属「异我」侧）, 不是笔误。
   待核: 找 DTS 或六本里【正偏 ←→ 阴阳同异】映射规则的明文
        在 DTS → DTS_CITED / 在他本 → BOOK_CITED / 无明文 → 确认 ENGINE_DEFINED
   ★ 不写 _PENDING, 这部分就混在 ENGINE_DEFINED 里, 将来没人记得它没核过。
```

#### 4.25.3 ★ `sheng` / `ke` 表分级 = `AXIOM`（新增分级）

```
定义: 体系公理 —— 命理基础共识, 六本共享, 无单一出处
理由: 与「天干有十 / 地支有十二」同级 —— 不是某本书定义, 是体系前提
      DTS 没有专门定义五行生克表（因为不需要）, 用反局章的举例当定义
      是【拿使用当定义】

已核（探针 8/9/10）:
  ✓ P8/P9 十对逐条与 DTS 明文一致（详见下表）
  ✓ 六本覆盖: 相生 5/5 · 相克 5/5（探针 10 双版实测）
  ✓ 已人工核 2 处语境判定, 均判【非冲突】:
      SMTH L3576「火克木而死」  = 太极生发收藏 + 卦象方位（木发于子终于午）
      YHZP L13180「土生火盛之地」= 土燥为病的脏腑传变（燥土→火炎→金伤）

待核（不阻塞分级, 状态显式化）:
  □ 紧邻版候选 64 处, 已核 11 处（全为「泄金生木」「润土生木」这类
    【动词+五行】动宾结构或语境关系, 无真冲突）, 剩余 53 处未核
  □ 跨字版线索池 891 处未筛
  □ 若两版核完确认 0 真冲突 → AXIOM 无保留
  □ 若有真冲突 → 重评分级

★ 精度声明: 不是「六本逐对明文」, 是「六本使用一致, 已核部分无冲突」。
  与 condition_2_pending / usable_as_criteria=False 同款 —— 状态显式化,
  状态本身不阻塞字段落定。

探针 8/9 的 DTS 明文依据（L445/L447 逐字给出全部十对）:
  相生 5 对  木→火 L445「木旺火炽，金伐木则生火」
          火→土 L445「火旺土焦，水克火则土」
          土→金 L445「土重金埋，木克土则生金」
          金→水 L445「火克金则生水」
          水→木 L445「水泛木浮，土止水则生木」
  相克 5 对  木→土 L445「木克土则生金」   火→金 L445「火克金则生水」
          土→水 L447「土克水则生火」   金→木 L447「金克木则生土」
          水→火 L539「不特火胜水，水克火之类」
★ L445/L447 主题是「君臣母子相生」反局机制, 不是「五行生克次序」——
  它们【恰好逐字给出了完整次序】, 故可作旁证但非定义。这就是标 AXIOM 而非
  DTS_CITED 的原因。
```

#### 4.25.4 ★ 候选池必须声明下游用途（第九次同类错的规缺口）

```
规: 候选池的生成规则必须声明【下游用途】, 精度权衡由用途决定。

  用途 = 机器判   → 高精度, 宁漏勿错
  用途 = 人工核   → 宽召回, 宁错勿漏（误报由人工核掉）
  用途 = 线索池   → 更宽, 只要覆盖

★ 本轮双版抓法【合规】, 不是「第十次同类错」:
  紧邻版 64 处  = 用途「人工核」→ 允误报（现行抓法合规）
  跨字版 891 处 = 用途「线索池」→ 允大量噪声（现行抓法合规）
★ 上轮把它定性为「同类错」是过度了 —— 缺的只是【用途声明】, 不是抓法本身。

★ 候选池【永远不是结论】: 真实冲突数 = 人工核完的数, 脚本不出该数。
```

#### 4.25.5 L2 核验结论

```
★ 十神表本身无缺陷 —— 探针 7/7 全 PASS, 算法形态, 十值域完整。
★ 天干×地支藏干 + 中余气十神已核（甲②③ 完成）:
  探针 P8–P17（修版2: 分句 + 三层规则, 判据「12 支全解析, 11/12 也 FAIL」）
    P2  源文逐字核对 YHZP/SFTK        PASS
    P3  YHZP 解析 12 支全（缺支0/空0/未解析0）  PASS
    P4  SFTK 解析 午={丁}（修版后不偷「己未宮」的己）  PASS
    P5  引擎表 12 支有值              PASS
    Pn  来源核 12 支来源句精确, 跨支违规 0  PASS
  集合对照: 引擎藏干表 vs YHZP《地支藏遁歌》12/12 全同, 零冲突
    子癸 · 丑己癸辛 · 寅甲丙戊 · 卯乙 · 辰乙戊癸 · 巳丙庚戊
    午丁己 · 未丁乙己 · 申庚壬戊 · 酉辛 · 戌丁戊辛 · 亥壬甲

→ 【L2 十神层核过】

遗留（不算未核, 是待核）:
  ten_god 正偏命名 —— ENGINE_DEFINED_PENDING
    DTS L210「财官印绶发偏正」只说有正偏, 未给「同/异阴阳」映射规则
★ 「L2 核过」= 十神算法与藏干表都核过; 正偏命名的 DTS 依据仍待核。
```

#### 4.25.6 ★ 藏干表三层分级（2026-10-05 定）

| 层 | 内容 | 分级 | 依据 |
|---|---|---|---|
| 层1 | 地支藏什么干（12 支×各干） | `BOOK_CITED` | YHZP L2523-2527《地支藏遁歌》12 支完整；SMTH L2055、PZZQ L2879 亦全；SFTK L4057 同内容 |
| 层2 | 藏干次序（本气→中气→余气） | `BOOK_CITED` | PZZQ L2917/L2918「寅中藏甲丙戊，甲当旺之气也…次序先甲次丙次戊」「辰中藏戊乙癸，戊土之本气也」 |
| 层3 | 层数（子一、丑三、午二…） | `AXIOM` | 与「天干有十」同级的体系公理, 无独立明文 |

★ 层1/层2 定 `BOOK_CITED` 而非 `AXIOM`: 有具体原文行号可追溯, 不是「六本共享无出处」。
★ 层3 定 `AXIOM`: 无任何书本明文规定每支几层, 属体系前提。

#### 4.25.7 ★ 藏干排序核验（分层加注，裁一百三十二甲）

```
【已验证】PZZQ 有明文且引擎一致（2 支）
  寅  PZZQ L2918「次序先甲次丙次戊」      引擎=甲丙戊   一致
  辰  PZZQ L2918「辰中藏戊乙癸，戊土之本气也」 引擎=戊乙癸   一致

【无法证伪】PZZQ 未逐支定义（4 支）
  丑 巳 未 戌 —— PZZQ 无明文, 无对照, 引擎排序体系内部一致

★ 两状态不同, 不可混称:
  已验证    = 引擎排序符 PZZQ 体系, 有明文对照
  无法证伪  = PZZQ 无明文, 无对照, 但引擎排序体系内部一致
★ 「无法证伪」【不是】PENDING —— 引擎每支都是本气在前, 体系一致,
  不是「未定状态」, 是「唯一可证的两支已证, 其余不可证但无冲突」。

【歌诀语序不构成判据】—— 已由辰的实证确立
  YHZP 歌诀「辰藏乙戊三分癸」(乙戊癸)
  PZZQ + 引擎      「戊乙癸」
  → 歌诀语序与引擎不同而引擎正确 → 歌诀语序服从韵文, 非判据

★ 实测排序差 5 支（丑辰巳未戌）= 歌诀语序 vs 结构序, 非冲突。
```

#### 4.25.8 ★ issue: SFTK L4057《十二支中所藏法》传抄缺漏（裁一百三十三）

```
缺陷 1  缺卯      修版2 复现: SFTK 卯=(无)   引擎={乙}
缺陷 2  午缺己    修版2 复现: SFTK 午={丁}   引擎={丁己}
旁证    YHZP L2523-L2527《地支藏遁歌》同内容, 12 支完整
        （SFTK 与 YHZP 是同一内容、不同篇名的两首歌诀, 逐支集合一致）
定性    非体系缺陷 —— SMTH L2055 / YHZP L6201 / PZZQ L2879 均有 12/12 完整表述
        是 SFTK 单本传抄问题
触发    若核 SFTK 原书（非电子版）含卯含己 → 定性改为「电子版传抄」

★ 边界: 本 issue 与 §4.25.9 的「子」分歧【分开】——
  一为单本传抄缺陷, 一为准神与五本共识的分歧。

证据链（各自独立, 互不借用）:
  ① 全书「卻」26 处用例全为转折义（无让步用法）
     → 「午宮卻有丁火」=「午宫却只有丁」
  ② 修版2 解析器（句式锚点, 不按字符集）独立复现 午={丁}
```

#### 4.25.9 ★ issue: DTS 与五本在「子藏什么」上分歧（裁一百三十四）

```
DTS  L230「子时生人，前三刻，三分壬水用事；后四刻，七分癸水用事」 → {壬, 癸}
五本  {癸}  —— 38 处明文, {壬} 零出现
     YHZP 6 / SMTH 16 / QTBJ 10 / SFTK 4 / PZZQ 2
     其中 34/38 来自无缺陷的 4 本（YHZP+SMTH+QTBJ+PZZQ）

【不采纳 DTS 的理由】
  ① 五本 38:0 共识
  ② DTS 的「用事=藏干」是【读出来的】——
     §十五 L223「月令乃提纲之府…人元为用事之神」
     §十六 L228「生时乃归宿之地…人元为用事之神」  ← 句式对称
     L230 后半自回引 §十五 作并列比较（「评其与寅月生人，戊土用事何如…」）
     不是 DTS 明写「子藏壬癸」

【层级说明】（不是理由, 是结构性边界）
  藏干表属 AXIOM / BOOK_CITED 级, 不在 DTS 的判定范围
  → DTS 在此超出层级给特例
★ 理由 = 为什么这次不采纳; 层级 = 为什么这条不属 DTS 判定范围。
  两者分开写, 下次遇到同类分歧（DTS 超出层级）时有可复用框架。

【触发条件】
  若 DTS 他章或权威本支持「子藏壬癸」 → 重估
  若 YHZP《地支藏遁歌》等歌诀某本含壬  → 重估

★ 当前处置: 引擎用五本（{癸}）, 与 YHZP《地支藏遁歌》12 支集合全同。
★ 前次双轨报告「午 {丁己} 集合同」是【解析器假数据】——
  解析器按支名字符切段, 「己未宮」的「己」被当支名, 午偷到下一支的己。
  该错误已由修版2 修正（见 §4.25.5 P4）。
```

---

### 4.26 ★ L4 格局成败（核A，v1.18 新增，裁135丙+138丙 / 裁139 / 裁140甲）

> L4 是上层（底层 L0-L3 已冻结）—— 本节是**L4 格局成败判据库的结构声明**，不是引擎改动。
> 依据行号引 DTS L206 / L265 / L268 / L591 / L215 / L305 / L365 / L369。

#### 4.26.1 层级 + 正交维度（裁138丙）

```
层:
  格体  —— §十二「格之真者，月支之神，透于天干也」（L206）
            散乱天干寻所附于提纲，非格；方局气象不可言格；飞天合禄可破害刑冲论者亦不可言格
  成败  —— §二十一~二十四，各格成败条件
            §二十一 官杀 / §二十二 伤官 / §二十三 清气 / §二十四 浊气

正交维度（不独立成层）:
  清浊  —— ★ L591 明文「不专是官印绶内有清浊，凡格局、气象、用神、合神、
            日主化气、从气、神气、精气，以序收藏发生意向…主从之间皆有之」
            → 清浊是【贯穿所有层的正交量度】，与 L3 弱冲突「多维并列」同款
            → 不建「清浊层」，建「清浊度量」（跨层可读）
```

#### 4.26.2 判据库 12 条 + 分级（裁139）

**映射两列 —— 章节归属（BOOK_CITED）/ 切片分组（ENGINE_DEFINED）**

| 切片 ID | 来源 | 章节归属 | 分组 | 分级 |
|---------|------|---------|------|------|
| `.CHENG_BAI.001` | DTS §十二 L206 | 格体标准 | 通用 | **BOOK_CITED** |
| `.CHENG_BAI.002` | DTS §十二 L206 | 无格可立 | 通用 | **BOOK_CITED** |
| `.CHENG_BAI.003` | DTS §二十一 | 官杀格 | 官杀 | **BOOK_CITED** |
| `.CHENG_BAI.004` | DTS §二十二 | 伤官格 | 伤官 | **BOOK_CITED** |
| `.CHENG_BAI.005` | DTS §二十三 L265 | 清气 | 通用（格内配置） | **BOOK_CITED** |
| `.CHENG_BAI.006` | DTS §二十四 L268 | 浊气 | 通用（格内配置） | **BOOK_CITED** |
| `.CHENG_BAI.007` | PZZQ §九/十三 | 八格成格条件 | 八格总则 | **BOOK_CITED** |
| `.CHENG_BAI.008` | PZZQ §九/十三 | 八格败格条件 | 八格总则 | **BOOK_CITED** |
| `.CHENG_BAI.009` | PZZQ §十三 | 成中有败 | 八格总则 | **BOOK_CITED** |
| `.CHENG_BAI.010` | PZZQ §十三 | 因成得败/因败得成 | 八格总则 | **BOOK_CITED** |
| `.CHENG_BAI.011` | PZZQ §十八/十九 | 四吉神破格 | 八格总则 | **BOOK_CITED** |
| `.CHENG_BAI.012` | PZZQ §十八/十九 | 四凶神成格 | 八格总则 | **BOOK_CITED** |

★ **12/12 全部 BOOK_CITED**（章节归属来自源文）
★ 切片分组（如「官杀」「伤官」）是**编者分类**，标 **ENGINE_DEFINED** —— 若某格未明写于 §二十一/二十二（如财格、印格无独立章），分组即悬空 → **`unmapped` 显式列出**

#### 4.26.3 「忌神」相对性核验（裁136乙 / 裁139修正）

```
★ DTS 全仓搜「忌神」13 处，无固定集合定义。
  L305「局所忌之神」—— 相对局而定
  L215「提纲食伤财官太旺，则取印比为喜神」—— 喜忌随配置翻转
  L365「纵有一二忌神，适来攻击，亦不为凶」—— 量与制化定吉凶
  L369「忌神太多，或刑或冲…辗转攻击」—— 同

★ PZZQ .008「遇忌神破格」与 .012「凶神得宜可以成格」不冲突：
  同一个煞，在 A 格为忌且多而无制 → 破格
  同一个煞，在 B 格为喜且用得宜 → 成格
  「忌神」不是固定集合，是【相对于本局配置】的判据
  → 裁136乙成立
```

#### 4.26.4 cheng_bai_criteria 字段形态（裁140甲）

```
落点: p0_v2/cheng_bai_criteria.py :: build_cheng_bai_criteria(ge_name)
消费类型: COMPUTED（下游可读，供人工核或后续合判）

形态:
  {
    "applicable":  [判据ID列表],     # 本盘适用的判据
    "map_version": "v0",             # 映射表版本
    "map_coverage": "N/12",         # 已映射条数/总数
    "unmapped":    [未映射的判据ID], # 显式列出，不藏
    "note":        (不命中格名时) "格名 X 未在映射表内 —— 待补映射"
  }

探针（独立进程，不 import 引擎生产路径）:
  正官格/七煞格/伤官格  applicable=10 unmapped=2
  正财格/偏印格/食神格  applicable=9 unmapped=3
  建禄格  applicable=9 unmapped=3（DTS 无专章 → 通用 9 条）
  不命中格名  applicable=0 unmapped=12 note 显式列出
```

---

## 五、`strength_verdict` 字段形态
```
值形态为 dict（v1.11 改, 见 §2.6.7）: {value, status, predictive, basis}
value 恒为 None（三档映射未落）; predictive 恒 False —— 它是【规则输出】不是【事实度量】。
【写进契约】并显式化未实现状态 —— 它是架构 §2.5 明文定的 L3 契约字段，
缺实现 ≠ 不该在契约里。predictive=False 把「无判据」显式化，
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

---

## 八、文档规范（v1.8 新增，裁六十八甲 + 裁七十丙）

### 8.1 单一出处规（精确版）

```
规: 契约文档内, 同一事实的【结论部分】只允许一处记录（契约事实章）。
    其他章节提及该事实, 只能以【指针】形式（"见 §x"）。

判据: 该内容是「可被引用的结论」还是「怎么得出该结论的过程」
      前者 → 唯一出处; 后者 → 可多处

核验记录章（如 §2.7）可保留:
  怎么查的 / 观察到什么 / 证据引文 / 核验时点
核验记录章【不可】保留:
  结论标签 / 数字 / 值域 —— 这些只属契约事实章

★ 不精确写成「同一事实只许一处」会把核验记录也砍掉，
  但核验过程本就该可复现，复现过程要留。
```

### 8.2 起因案例（本节存在的理由）

```
v1.6 同一次 commit 内并存两个数字:
  §2.7.5 记「l3_contract 合计 = 13 个」
  §4.14  记「实测键数 = 18」
  —— 提交前无一致性检查, 数字漂移。

根因: 同一批字段（strength_verdict / root_grade_raw / fan_ju /
  boundary_note / evidence_refs）在两节归属口径不同 —— 一个归「不计入」,
  一个归「元信息3 + 判定5」。

同类: compare_key 分级曾有三处记录（§2.7.2 表 / §2.7.3 四级登记 / §4.15.1 表），
      我修了其中一处，另两处漏改。

★ 与代码层同名双源（§4.18 l3_contract vs wuxing_power[五行]）同款:
  同一份文档两个源，与同一份数据两个出口，是同一类病。
```

### 8.3 提交前一致性检查（固化）

```
规: 契约文档改动后, 提交前跑一遍 ——
    scripts/check_contract_consistency.py

★ 脚本职责 = 「把散落的同主题记录聚到一处给人看」，【不自动判冲突】。
  理由: 「数字不同」可能是「口径不同」（13 是三组合计 / 18 是实测键数），
        自动判定必然误报。判断仍由人做 —— 与「契约是事实声明，核验靠人工」一致。

检查三类:
  1 数字: l3_contract 键数 / compare_key 档数 / 六本盘数
  2 标签: ENGINE_DEFINED / DTS_CITED / ENGINE_DEFINED_CONFLICT 的归属
  3 表标题: 同一主题的表是否在两节各存一份

输出格式: 关键词 | 出现节 | 行号 | 上下文行（按关键词分组，组内按行号排）
```

---
