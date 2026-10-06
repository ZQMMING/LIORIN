# po_ge 破格条件求值器 · 完整设计（三处补齐版）

> 架构级 bug 修复。旧裁决「po_ge 非空 = 破格」**作废**。
> po_ge 两路径混合：build_ge_cheng 写【待求值模板】，apply_he_po_ge 追加【已判·冲月令事件】。
> cheng_bai 旧 `len(po_ge)` 把"破的可能"当"已破"。修复 = L4 统一求值成命中事件，
> cheng_bai 与 P1 格局/结构病域只读命中事件。

## 一、po_ge 两类条目

| 来源 | 形态 | 语义 | 处理 |
|---|---|---|---|
| build_ge_cheng（24处） | 组合/地支/缺失 | 待求值模板 | 逐条判命中 |
| apply_he_po_ge | `type:'冲月令破格', required:[月令五行]` | 已判事件（L1014 已满足） | 直接计命中 |

## 二、L4 执行顺序（核验后修正）

`build_ge_cheng → apply_he_po_ge → normalize_ti_wx → evaluate_po_ge`

- normalize_ti_wx **改 ti_wx 值**（六格 ti=月令本气；建禄阳刃 ti=透干十神），故分域要用归一化后 ti，
  求值器必须在 normalize **之后**；
- normalize **不读 cheng_bai/求值器**（只读 ge 字符串、pillars、hidden），无循环；
- 破格盘 normalize 跳过。

## 三、xi_wx_status 三值（生产源码实测，核验读源码）

UNVERIFIED 仅出现在 cheng_bai 探针假数据，**生产不产生**。生产三值：

| 值 | 含义 |
|---|---|
| `DEFINED` | xi_wx 有值，喜神明确 |
| `UNDEFINED` | 无原典喜用明文（从官/从杀/从势） |
| `None`（键缺） | 正格未写该字段（占多数） |

## 四、cheng_bai 状态机（六态，穷尽）

**先判 H（命中数）：H=0 不看 status，避免 None 盘被扫成 PO。**

| 条件 | 状态 |
|---|---|
| ge = None/无格 | `NO_GE` |
| special 格（从/专/化）H=0，真成立 | `SPECIAL_PASS` |
| special 格 H>0，或假从/假化 | `SPECIAL_FAIL` |
| 普通格 H=0 | `CHENG` |
| 普通格 H>0 且 xi_status=DEFINED | `CHENG_ZHONG_YOU_PO` |
| 普通格 H>0 且 xi_status=None/UNDEFINED | `PO` |

## 五、命中事件 schema

```
{
  hit_type:   组合 | 地支 | 缺失 | 冲月令破格,
  match:      ANY | ALL,
  hit_detail: str,
  sources:    [str],          # 十神名 或 支名 或 五行
  domain:     GEJU | JIEGOU,
  basis:      DTS_CITED | BOOK_CITED | ENGINE_DEFINED
}
```

## 六、domain 全表（24处模板 × 域，按 格体×忌神，穷尽出现组合）

| 格体/路径 | 命中忌神 | 病名 | domain |
|---|---|---|---|
| 从财格 | 比肩/劫财 | 从格被比劫破 | SPECIAL_FAIL |
| 从杀格 | 食神/伤官 | 从格被食伤破 | SPECIAL_FAIL |
| 食神格 | 偏印 | 枭神夺食 | **结构** |
| 食神/伤官(生财) | 财＋煞 ALL | 财党煞 | **结构** |
| 食神制杀路径 | 财 | 财破食/党煞 | **结构** |
| 官格路径 | 伤官 | 伤官见官 | **结构** |
| 官格路径 | 地支刑冲 | 刑冲破格 | **格局** |
| 财格 | 七煞 | 财党煞/官杀混杂 | **结构** |
| 印格 | 财 | 财破印 | **结构** |
| 阳刃格 | 官煞全缺(缺失) | 辅佐缺失格不成 | **格局** |
| 特殊格 | 财官全缺(缺失) | 格不成 | **格局** |
| 冲月令破格 | 月令五行 | 按被冲格体：印/官局被冲→格局 | **格局** |

## 七、多命中聚合（H>1）

- 事件**各自独立产出**，不合并（一事件一病），保留全部 domain；
- 验收层综合：任一真病无救 → bad；
- 不引入 severity 连续权重（序数另立）。

## 八、求值口径与分级

- 组合 required：十神"透干 **或** 地支本气"在局；**中余不计**（ENGINE_DEFINED，原文无阈值；
  与 de_di 中气算根不冲突——彼判日主根之轻重，此判忌神有力破格）。
- 地支刑冲：读 L0 `resolved.chong_survive`（相邻存活、无合解），DTS_CITED/L0。
- 缺失 forbidden：透干/本气口径全缺才命中。
- 冲月令：已判事件直接计。
- 分级：骨架/刑冲/缺失 BOOK·DTS_CITED；"中余不计、相邻、本气" ENGINE_DEFINED。

## 九、层边界

- L4 输出 `ge_cheng.po_ge_hits`（命中事件）+ cheng_bai（六态）；
- **P1 读 po_ge_hits**（不读 cheng_bai 态、不自己求值），格局/结构病域据 domain 产出病。

## 十、旧分布作废

旧 cheng_bai 分布（CHENG 353/CZYP 13/PO 1395/NO_GE 345）**全部作废**；新分布出来前，
基于 cheng_bai 的验收数字无效，须重报。

## 十一、落码顺序

1. ge_jie_layer 加 `evaluate_po_ge`（接 normalize 后）→ po_ge_hits；
2. cheng_bai 改六态、读命中数；
3. P1 格局/结构病域读 po_ge_hits 按 domain 产出病；
4. 全量回归，新旧成败分布对比；空缺标 ENGINE_DEFINED + 触发条件。
