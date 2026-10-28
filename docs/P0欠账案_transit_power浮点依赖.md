# P0欠账案：transit_power浮点权重依赖

> ## 🟢 销账（2026-09-29 接手核对）
> **本案"病灶"已不存在，文档描述的是修复前的旧状态，特此销账。**
> - "第 45 行调用已删 `build_wuxing_power`"不成立：当前 `transit_power.py:45` 是 `_ling_state` 内一处无关的条件判断；全文件**没有任何**活调用指向已删浮点实现。
> - 浮点体系已废，纯规则替代已落地：真调用源是 `transit_power.py:311` 的 `_build_pure_power`（第 54 行定义，docstring"纯规则五行动力计数——替代已删 build_wuxing_power"），`build_transit_power` 输出四档布尔枚举（强/旺/平/衰），无浮点 score。
> - `build_wuxing_power` **未删**，现为 `engines/common/wuxing_power.py:7` 的布尔兼容 shim（委托 `_build_pure_power`），供 `production_entry.py:159` 等旧调用点保留接口签名。
> - 大运/流年链是活链路：`dayun_summary.py:83` / `liunian_summary.py:54` 直接 import `build_transit_power`/`transit_clash_verdicts`，**没有** try 吞 ImportError。
> - 实测（主仓库 venv）：`production_entry` 带 dayun/liunian 时该层正常计算，`has wuxing_power: True`。

## 现状（描述的是 2026-09 前旧状态，现已失效）
- `engines/common/transit_power.py` 第45行调用 `build_wuxing_power`（已删除）
- 活链 `dayun_summary` / `liunian_summary` 真实依赖浮点权重体系

## 矛盾
- 8案例零变化 + 活链在跑 → 说明该调用路径运行时必被try吞或未触发
- 大运流年力量裁决实际瘫痪或走兜底

## 待裁
大运流年力量按章程重定——《三命通会》大运"过度之处即有灾殃"、流年太岁生克明据 → 应改纯规则裁决，与浮点体系彻底切割

## 状态
冻结，排期，不动活链
