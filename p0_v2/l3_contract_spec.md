# L3 判据契约（判据中心 · 非「六维框架」）

> 版本 **v1.1**　　日期 2026-10-03　　状态 **第1刀已落码**（v1.0 冻结 10 字段 → v1.1 增第1刀三布尔）
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

## 三、`strength_verdict` 的处置

```
值恒为 NOT_AUTHORIZED。
【写进契约】并标 status=NOT_AUTHORIZED —— 它是架构 §2.5 明文定的 L3 契约字段，
缺实现 ≠ 不该在契约里。契约的 status 字段把「未实现」显式化，
与 relations 的 ANHUI `condition_2_pending` 同款处理。
```

---

## 四、视图联动检查项

```
⚠ 契约字段的值来自 L1（wuxing_power / transit_power）。改它们必须重跑：
   - l3_contract 五字段 == _dmp 同名字段   （2106 × 5 diff=0）
   - ling_state_eff 8 值分布不变            （scripts/verify_chong_adjust.py）
   - 全量判定变化                            （scripts/_l4_baseline.py）
   - P1 六本回归                             （scripts/check_P1.py）
```

---

## 五、待审确认项

1. 10 字段表（名/类型/值域/DTS 行号/role/status）
2. `ling_state_eff` 8 值互斥枚举（§1.1）
3. 合成式与三条顺序敏感约束（§1.2）
4. 只在月令行有值（§1.3）
5. `naming_note` 记不改（§1.4）
6. 一次性切不双写（§2.2）
7. `strength_verdict` 写入并标 status（§三）

**审完落码。**