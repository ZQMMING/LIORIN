# po_ge 破格条件求值器 · 三层设计

> 架构级 bug 修复。旧裁决「po_ge 非空 = 破格」**作废**：po_ge 存的是破格条件**模板（待求值）**，
> cheng_bai 用 `len(po_ge)` 数模板条数，把"有哪些破的可能"当成"已经破了"。
> 修复 = 建求值器，把模板在当前盘逐条判命中，cheng_bai 与 P1 格局病域统一读"命中事件"。

## 层1 · po_ge 模板枚举（完整）

**type（4 种）：**

| type | 字段 | 语义 |
|---|---|---|
| `组合` | `required:[十神...]` + `match` | 见 required 十神则破 |
| `地支` | `branch_cond:'刑冲'` + `match` | 地支见刑冲则破 |
| `缺失` | `forbidden:[十神...]` | forbidden 十神全缺则破 |
| `冲月令` | `required:[月令五行]` + `match` | 月令被紧贴冲则破 |

**match：`ANY`（任一）/ `ALL`（全部）。**

required 十神取值全集：比肩、劫财、食神、伤官、偏印、正财、偏财、七杀、正官。
forbidden 取值：{正官,七杀}、{正官,正财,偏财}。
branch_cond 现仅见 `刑冲`。

## 层2 · cheng_bai 状态机（穷尽，对"有格"盘）

令 **H = 命中破事件数**（求值器输出，非模板条数）：

| 条件 | 状态 |
|---|---|
| H = 0 | `CHENG` |
| H > 0 且 xi_wx_status = DEFINED | `CHENG_ZHONG_YOU_PO`（成中有败） |
| H > 0 且 xi_wx_status ≠ DEFINED | `PO`（破） |

ge 为 None/无格 → None（不在本状态机）。三态互斥、穷尽。

## 层3 · 命中事件 schema（P1 格局病域读它）

```
{
  hit_type:   组合 | 地支 | 缺失 | 冲月令,
  match:      ANY | ALL,
  hit_detail: str,          # "偏印透干" / "寅申刑冲" / "官杀全缺" / "月令被冲"
  sources:    [str],        # 命中载体: 十神名 或 支名 或 五行
  basis:      BOOK_CITED | ENGINE_DEFINED
}
```

## 求值口径

- **组合 required**：十神在"天干透出 **或** 地支本气"即算在局（中余气不计，从严）；
  match ANY＝任一 required 在局；ALL＝全部在局。
- **缺失 forbidden**：按同口径（透干/本气）forbidden 十神**全缺**才命中。
- **地支刑冲**：读 L0 `resolved`（六冲/三刑，紧贴，且无合解）。
- **冲月令**：月令支被紧贴六冲且无合解。
- 依据：PZZQ"见 X 破格"本为条件式（BOOK_CITED）；"透干/本气、中余不计、紧贴"为
  ENGINE_DEFINED 工程口径（原文未给阈值）。

## 落码顺序

1. 建 `evaluate_po_ge(po_ge, facts)` → 命中事件列表；
2. cheng_bai 改读命中数（H）；
3. P1 格局病域读命中事件产出格局病（用神被合去/冲败/被伤、辅佐冲突、成中有败）；
4. 全量回归，新旧 cheng_bai 分布对比；空缺状态标 ENGINE_DEFINED + 触发条件。
