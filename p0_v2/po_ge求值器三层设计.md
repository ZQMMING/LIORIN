# po_ge 破格条件求值器 · 完整设计（五处补齐版）

> 架构级 bug 修复。旧裁决「po_ge 非空 = 破格」**作废**。
> po_ge 由**两条路径混合**：build_ge_cheng 写【待求值模板】，apply_he_po_ge 追加【已判事件】。
> cheng_bai 旧用 `len(po_ge)` 数条数，把"破的可能"当"已破"。修复 = L4 内统一求值成命中事件，
> cheng_bai 与 P1 格局/结构病域只读命中事件。

## 一、po_ge 两类条目（分开处理）

| 来源 | 形态 | 语义 | 求值器处理 |
|---|---|---|---|
| build_ge_cheng（24处） | type 组合/地支/缺失 | **待求值模板** | 逐条判命中 |
| apply_he_po_ge（追加） | `type:'冲月令破格', required:[月令五行]` | **已判事件**（条件 L1014 已满足：月令五行∈ti/xi 且被存活相邻六冲） | 直接计命中，不再求值 |

## 二、层1 · 模板枚举（完整）

**type（模板 3 种 + 已判事件 1 种）：**

| type | 字段 | 语义 | 分级 |
|---|---|---|---|
| `组合` | required:[十神] + match ANY/ALL | 见 required 十神则破 | 骨架 BOOK_CITED（PZZQ 破格条件式） |
| `地支` | branch_cond:'刑冲' | 地支见刑冲则破 | DTS_CITED/L0 已有 |
| `缺失` | forbidden:[十神] | forbidden 全缺则破 | BOOK_CITED（阳刃无官煞等） |
| `冲月令破格` | required:[月令五行] | 月令被存活相邻六冲 | DTS L100/102 + apply_he_po_ge |

match：ANY / ALL。required 十神全集：比肩、劫财、食神、伤官、偏印、正财、偏财、七杀、正官。

## 三、层2 · cheng_bai 状态机（六态，穷尽）

| 条件 | 状态 |
|---|---|
| ge = None/无格 | `NO_GE` |
| special 格（从/专/化）成立且**真** | `SPECIAL_PASS` |
| special 格但**假**（假从/假化/被破） | `SPECIAL_FAIL` |
| 普通格 H = 0 | `CHENG` |
| 普通格 H > 0 且 xi_wx_status = DEFINED | `CHENG_ZHONG_YOU_PO` |
| 普通格 H > 0 且 xi_wx_status ≠ DEFINED | `PO` |

H = 命中破事件数（求值器输出）。六态互斥、穷尽。

## 四、层3 · 命中事件 schema（含分域）

```
{
  hit_type:   组合 | 地支 | 缺失 | 冲月令破格,
  match:      ANY | ALL,
  hit_detail: str,          # "偏印透干" / "寅申刑冲" / "官杀全缺" / "月令被冲"
  sources:    [str],        # 命中载体: 十神名 或 支名 或 五行
  domain:     GEJU | JIEGOU,  # 分域, 见五
  basis:      DTS_CITED | BOOK_CITED | ENGINE_DEFINED
}
```

## 五、分域规则（格体十神 × 命中忌神十神）

| 格体 | 命中忌神 | 病名 | 域 |
|---|---|---|---|
| 印 | 财 | 财破印 | **结构** |
| 食神 | 偏印 | 枭神夺食 | **结构** |
| 财 | 比劫 | 比劫争财 | **结构** |
| 官 | 伤官／合官 | 用神被伤/被合去 | **格局** |
| 七煞 | 食伤制尽／合煞 | 用神被冲败/合去 | **格局** |
| 任意格 | 辅佐失用／喜神被劫 | 辅佐冲突/成中有败 | **格局** |

## 六、求值口径与分级

- **组合 required**：十神在"天干透出 **或** 地支本气"算在局；**中余气不计**。
  - 「中余不计」**ENGINE_DEFINED**（原文无阈值）。与 de_di"中气算根"不冲突：de_di 判日主根之
    轻重（程度），此处判忌神是否足以破格（存在到有力），本气/透干才足破格。
- **地支刑冲**：读 L0 `resolved.chong_survive`（已判**相邻**存活、无合解）；统一称"相邻"，
  不用"紧贴/坐支"。DTS_CITED/L0 已有。
- **缺失 forbidden**：按同口径（透干/本气）全缺才命中。
- **冲月令破格**：已判事件，直接计。
- 分级：骨架/刑冲/缺失/冲月令 为 BOOK_CITED·DTS_CITED；"中余不计、相邻、本气"为 ENGINE_DEFINED。

## 七、求值器落点

**放 L4（ge_jie_layer）**。求值 = L4 把模板落成"破在哪"的事实，属 L4 职责；P1 只读命中事件归域。
L4 顺序：`build_ge_cheng → apply_he_po_ge → evaluate_po_ge → normalize_ti_wx`。
输出 `ge_cheng.po_ge_hits`（命中事件列表），po_ge 原模板保留可溯。

## 八、旧分布作废

旧 cheng_bai 分布（CHENG 353 / CZYP 13 / PO 1395 / NO_GE 345）**全部作废**（基于数模板错误逻辑）。
新分布出来前，所有基于 cheng_bai 的验收数字无效，须重报。

## 九、落码顺序

1. ge_jie_layer 新增 `evaluate_po_ge(po_ge, facts)` → po_ge_hits；
2. cheng_bai 改读命中数（六态）；
3. P1 格局/结构病域读 po_ge_hits，按分域规则产出病；
4. 全量回归，新旧成败分布对比；空缺标 ENGINE_DEFINED + 触发条件。
