# strength_verdict 合成函数取证单（甲路·非反标定）

> 出证 2026-10-08（v2，撤 L240 跨层 + 换日主行 ling_state 后修订）。L3 判层唯一缺口（strength_verdict value=null，0/100 案例命中）。
> 落地归属：引擎线落码，User commit。本单只出证，不擅改引擎。
> 铁律遵守：f = ENGINE_DEFINED 工程合成判据，参考 DTS **L110/L230 两句方向**（L240 源流章「源头」判据归源流层，不进 L3，撤出）；
> 阈值 = 工程规则边界，**非 775 盘反标定**（反标定路已断）。
> 775 盘旺衰词分布 = 落码后**验证标尺**（看 STRONG/WEAK 与案例旺衰词一致率），非反推来源。

## 一、判层落点（已坐实）

- 落码处：`p0_v2/bazi_gate.py` L386-391（l3_contract 内 strength_verdict）
- 契约：`p0_v2/l3_contract_spec.md` §1.2 / §2.4
- 现状：`value: null, status: ENGINE_DEFINED, predictive: False, basis: "L110 相对比较 + L235 方向 + L245 取最多最旺; 阈值 ENGINE_DEFINED"`
- bazi_gate L387 原注：value=null =「三档映射未落——键在，值不出」
- bazi_gate L384 已定值域：`"STRONG"/"WEAK"/"EXTREME_WEAK"`（**恒不出 EXTREME_STRONG**，§2.4 三源冲突否决）

## 二、依据行号更正（basis 现写错两处，落码须用实测行号）

| basis 现写 | 实测原句 | 实测行号 |
|---|---|---|
| L110 相对比较 | L110「凡此皆详其干支**轻重**之机，母子相依之势…若专执生死败绝之说，推断多误」 | ✓ L110 |
| **L235** 方向 | L230「**旺则宜泄宜伤，衰则喜帮喜助**…旺之可损，以损在其中矣；**衰之极者不可益**」 | ✗→**L230** |
| **L245** 取最多最旺 | L240「不必论当令不令，只论**取最多最旺**，而可以为满局之祖宗者，为源头也」 | ✗→**L240**（但 L240 **撤出 L3 f**：源流章「源头」判据跨层，不进日主旺衰） |

> ★ 语义定性（裁令二）：三句**均非「日主旺衰绝对判定法」，只给方向**——
>   L110 讲【干支】关系轻重（母子相依/阴阳消息）、L230 讲【判旺/判衰之后】怎么处理、
>   L240 讲源流章【源头取最旺者】。没有一句是「日主身强/身弱的绝对判定」。
>   用它们构造 f = 甲路：**f 是 ENGINE_DEFINED 工程合成判据，不是 DTS 判据，不假装准神。**
>
> 引句实测值（DTS 京图撰刘基原注本，作方向参考）：
> - L110：相对/轻重——勿专执生死败绝，须详干支轻重之机（日主月令位 `l3.ling_state` 的方向锚）
> - L230：方向——旺宜泄/衰喜帮 + 「衰之极者不可益」（EXTREME_WEAK 的方向锚）
> - L240「取最多最旺」**撤出 L3 f**（裁令三）——L240 属 §十九 源流章，判的是「源头」（满局气脉起点），**不是日主旺衰**；dump 4 盘坐实：日主全非满局最旺却 root_grade=本（有根），满局最旺与日主强弱常背离 → 引 L240 = 跨层，归源流层（P2/L4 顶层），不进 L3。
> - L230 末句「旺之可损」= 旺亦不可留损 → 否决 EXTREME_STRONG（三源冲突，memory 裁甲）

## 三、合成函数 f（甲路：DTS L110/L230 两句方向，ENGINE_DEFINED 工程合成；L240 撤出）

**输入**（三量，全部 l3_contract 已有、L386 前底层量可取，前置核 dump 4 盘坐实；撤 `_mass_rank`/L240=跨层）：
- `l3.ling_state`（L368，**日主行**月令位 = 日主得令/失令；非月令行 `ling_state_eff`——后者判月令五行自身当令，非日主）
- `dm_ben_eff`（日主本气根，0/≥1）
- `dang_duo`（L280/L604 党多/党少，`support_state == "SHENG_FU_CHENG_SHI"`）

**f(l3.ling_state, dm_ben_eff, dang_duo) → 值域 {STRONG / WEAK / EXTREME_WEAK / None}**

> ★ 语义定性（裁令二 + 三）：**f 是 ENGINE_DEFINED 工程合成判据，不是 DTS 判据，不引 L240（跨层）。**
> 下表的"分支条件"是**工程规则边界**（参考 DTS L110/L230 两句方向构造，非 DTS 明文阈值，也非案例反推）；
> "方向锚"列只是两句给的**处理方向**，不构成判定标准本身。

| 输出 | 分支条件（ENGINE_DEFINED 工程边界，参考 DTS L110/L230 方向，非案例反推） | 方向锚 |
|---|---|---|
| **EXTREME_WEAK** | `dm_ben_eff==0`（无本气根）且 `l3.ling_state∈{囚,死}`（失令）且 `dang_duo==False`（党少） | L230「衰之极者不可益」（方向） |
| **STRONG** | `l3.ling_state∈{旺,相}`（得令）且 `dm_ben_eff≥1`（有根）且 `dang_duo==True`（党多） | L110 相对旺 + L230「旺则宜泄」（方向） |
| **WEAK** | 以上两档之外（有根但未得令，或党不多） | L230「衰则喜帮喜助」（方向） |
| **None** | 三档判据并列/边界重叠无法区分时，如实不出 | 铁律「宁漏勿错」 |

> 阈值说明：所有边界（无本气根 / 失令位 / 党少 / 得令+有根+党多）均为 **ENGINE_DEFINED 工程合成**——
> 参考 DTS L110/L230 两句方向，**非 775 盘反标定**（反标定路已断，用户铁律），**非 L240 满局最旺**（L240 归源流层，不进 L3）。
> 775 盘（泄348/身旺172/身弱100/太旺87/中和71…）仅作落码后**验证标尺**（看 STRONG/WEAK 与案例旺衰词一致率），非反推来源。

## 四、分级与置信度（给 User 拍板）

| 项 | 定级 | 说明 |
|---|---|---|
| 依据分级 | **ENGINE_DEFINED** | DTS 三句给方向、不给数值阈值；阈值是规则合成边界，显式声明无 DTS 明文阈值 |
| predictive | **保持 False** | bazi_gate L380 原注：规则输出非事实度量，L4 判定仍须自合 |
| 值域 | **锁定 {STRONG/WEAK/EXTREME_WEAK/None}** | 恒不出 EXTREME_STRONG（L230 旺之可损否决） |
| 置信度 | **中** | 三输入（日主月令位/根/党）方向稳，但 ENGINE_DEFINED 边界对中和盘偏粗，落码后须 100 案例 + 954 基线验；L240 满局最旺已撤出（跨层），不进 L3 |

## 五、落码建议（引擎线）

```python
# bazi_gate.py L386 处: value: None → value: _sv (模块级 _strength_verdict(...))
# _strength_verdict(l3_ling_state, dm_ben_eff, dang_duo):  # 三输入, 撤 _mass_rank(L240 跨层)
#   按第三节 f 三分支映射:
#     EXTREME_WEAK: dm_ben_eff==0 and l3_ling_state in {囚,死} and not dang_duo
#     STRONG:       l3_ling_state in {旺,相} and dm_ben_eff>=1 and dang_duo
#     WEAK:         其余
#     None:         边界重叠无法区分时不硬判
#   边界 = ENGINE_DEFINED 工程合成(参考 DTS L110/L230 两句方向, 非 DTS 判据, 非案例反推, 不引 L240)
#   predictive=False 保持
# basis 字符串更正为:
#   "L110/L230 散句方向 + ENGINE_DEFINED 合成规则(非 DTS 判据); 阈值=工程边界, 非 DTS 明文, 非案例反推; L240(源流章源头) 归源流层不进 L3"
# ★ 前置核已 dump 坐实: 三输入 L386 前底层量可取
#   l3.ling_state = L368 _dmp.get("ling_state") (日主行)
#   dm_ben_eff    = L366 special.get("dm_ben_eff")
#   dang_duo      = L354 _support_state == "SHENG_FU_CHENG_SHI"
```
回归口径：100 案例 + 954 验收基线（memory 口径），报判定可解释变化，非连带破坏。
验证标尺（非反推）：落码后统计 STRONG/WEAK/EXTREME_WEAK 与 775 盘旺衰词分布的一致率，交 User 判。
