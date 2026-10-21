# 河洛引擎（Heluo Engine）— 接线与契约

> **独立包边界（2026-10-16 提纯）**：本包为独立河洛引擎，仅含
> `src/tongshu/engines/heluo/`、`heluo_adapter.py`，以及运行必需的上游
> `bazi_engine`/`bazi_adapter`（排四柱）、`time/`（真太阳时）、`yi/`（易经卦爻辞结构）、
> `facts/`、`reasoning/`、`spec/`。入口为 `heluo_adapter.HeluoAdapter`；
> 完整 `pipeline`/`compute_stage` 属集成层，不在本包。流时卦剥离，大运/流年/流月引擎自算。
> 以下历史文档中「compute_stage / 黄历引擎接线 / YiAdapter 跨模块不含」等描述为提纯前口径，
> 实际边界以仓库根 `README.md` 与本说明为准。

**状态**：v2 frozen（2026-10-10 批次 P 完成算力裁剪）
**位置**：`src/tongshu/engines/heluo/`
**数据**：`data/heluo/`（原典 + 取证 + 多源校对）
**原典**：《河洛真数》（续修四库全书·天一阁本）

---

## 1. 引擎是什么

按《河洛真数》原典做的**离线推演引擎**，接排盘输入（出生公历日期/时辰/性别）→ 算出本命卦 / 元堂 / 后天卦 / 大运 / 流年 / 流月 / 流日 / 节候 / 化工 / 解卦 / 诊断 / 建议。

本分支**只包含河洛域**（`src/tongshu/engines/heluo/`）的代码、守卫、原典数据与文档。**不包含显示层、pipeline、render、其它引擎**。

## 2. 计算管线（calculation pipeline）

```
出生公历 → 真四柱（BaziAdapter 真太阳时校正）
  → HeluoCanonical.calculate(bazi, gender, birth_hour, birth_year, birth_date, target_year=...)
       ├─ 天数地数（compute_tian_di_shu）
       ├─ 先天卦（determine_prenatal_hexagram）
       ├─ 六爻（build_six_lines）
       ├─ 后天卦（compute_postnatal）
       ├─ 时间序列（_build_timeline(target_year=...)）── fast-path
       ├─ 卦象结构（analyze_hexagram）
       └─ 节候卦 + 化工（_compute_seasonal_hexagram / _compute_huagong）

  → HeluoResult = { input, numbers, prenatal, yuantang, postnatal, timeline,
                     structure, hua_gong, era, seasonal_hexagram, guajie }

  → YiAdapter.adapt() → YiStructure          （跨模块，本分支不包含）
  → YiInterpretationEngine.interpret() → YiInterpretation  （跨模块，本分支不包含）
  → H8 解卦层（build_guajie_from_result）── 50 条 evidence  （河洛内）
```

## 3. 时间口径（用户口径「时间上接黄历引擎」）

```
应期日 → 优先取 HuangliDay.lunar_month / lunar_day（黄历权威值）
        ↓ 不可用
        回退 lunar_python
        ↓ 不可用
        回退 公历口径
```

`_heluo_lunar_target(target_date, huangli_day=None)` 在 `compute_stage.py` 定义（compute_stage 是河洛接线边界，可动）。`_huangli_for_heluo(day)` 取黄历对象，失败返回 None。

## 4. 算力裁剪（fast-path 批次 P — 2026-10-10）

> ⚠️ 本节为早期 fast-path 规划描述；**当前 canonical.calculate 实现为全量路径**：
> 87 段流年全部嵌满 12 月 × 6 日（无 97 段元数据裁剪），
> 且 `interpret_all_liunian`（yi_interpreter）对全部流年段实际挂载 yi_signal（非 dead-write）。
> 顶层 `monthly_hexagrams` 已填充首年 12 月模板（2026-10-21 清理后）。

`canonical.calculate(target_year=None)` 走全量路径（旧契约保留，守卫钉死）。

## 5. 模块接线

```
src/tongshu/engines/heluo/
  ├─ canonical.py             主入口 HeluoCanonical.calculate()（含 _compute_year_jie 节气锚/年柱反推）
  ├─ timeline_yun.py          大运 + 流年 + 流月 + 流日 + 流时（六爻俱变；含 Timeline 数据类）
  ├─ evidence_producer.py     解卦层证据
  ├─ guajie.py                H8 解卦层（3000+ 行原典断语）
  ├─ diagnosis_rule_graph.py  诊断层 HL_* 判据
  ├─ frozen_state.py          FrozenHeluoState 冻结态
  ├─ yi_interpreter.py        流年卦断语（P1 解卦层，interpret_all_liunian）
  ├─ yuan_tang.py             元堂（先/后天）
  ├─ yuan_qi.py               元气（先/后天）
  ├─ canping.py               参评
  ├─ hexagram.py              卦象基础
  ├─ hexagram_symbol.py       卦象符号（孤立死代码，见 §11）
  ├─ heluo_lunar_bridge.py    H9b 河洛×黄历桥接（注入优先 / lunar_python 兜底）
  ├─ jiehhou.py               H11 节候卦
  ├─ hua_gong.py              化工（原典 L558-L567 节气窗口）
  ├─ guidance.py              指导层
  ├─ metrics_v2.py            指标 V2
  ├─ prenatal.py              先天卦
  ├─ postnatal.py             后天卦
  ├─ numbers.py               天数地数/洛书数
  ├─ exceptions.py            异常类
  ├─ input.py                 HeluoInput
  ├─ schemas.py               数据 schema
  ├─ relationship/            关系（互体/反体/对体/纳音福力）
  └─ __init__.py
```

## 6. 数据与原典

```
data/heluo/
  ├─ guajie_data.json         64 卦 × 6 爻判词（原典释义）
  ├─ guajie_jingyi.json       706 单元现代语义版（卦辞+爻辞+释义）
  ├─ yue_ling_shu_ge.json     月令数格 11 条
  ├─ 元堂算法核验_20261007.md
  ├─ 起例卷算法对照表_*.md
  ├─ 河洛引擎全域审计_*.md
  └─ ...
```

```
data/research/heluo/
  ├─ 河洛理数-总集.md
  ├─ 河洛理数-流年流月流日卦推演全解.md
  └─ 河洛理数-流年卦解卦全解.md
```

## 7. 守卫（tests/heluo/）

- **354 passed**（`python -m pytest tests/` 全量，含 16 个河洛测试文件）
- 覆盖：H2 冻结态 / H6 化工 / H7 元气 / H9b 黄历桥接 / H10 惰性化 /
  H11 节候 / H12 诊断 / H16 独立验证 / 参评 / 卦爻辞 / 边界 / 负例 / 扩展
- **审计脚本**（`audit/`，一次性裁决复核，非 pytest）：
  - `audit_anchors.py` — 案例锚点批量验证（1980 / 1724 已确证锚点）
  - `audit_post_fix.py` — 化工五行判定矩阵 + 流月节锚对齐
  - `audit_probe_ag.py` — 大运连续性 + 同人九三流年序列
  - `audit_recheck_bc.py` — H17-B/C 裁决复核（萃/旅卦象构造 + 元堂落点）
  - `audit_recheck_d.py` — H17-D 裁决复核（反卦五行关系 + 锚点）
  - `audit_recheck_e.py` — BUG1 验证（流月编号语义错位）
  - 全部以 `os.path.abspath(__file__)` 相对定位仓库根，**不硬编码绝对路径**

## 8. 端到端跑通

```bash
$env:PYTHONPATH='D:/shuntian_heluo/src'
$env:TONGSHU_ALLOW_ZIWEI_STUB='1'
$env:TONGSHU_AUTHORITY_CREDENTIALS='architecture-governance:schema-v1-arch-gov-2026;admission_registry:test-cred-hash'

python tools/heluo/quzheng_20261008/run_case_1983.py     # 单案例 8 段格式化报告
python tools/heluo/quzheng_20261008/run_e2e_cases.py     # 22 案例批量（1940-2015，0 issues）
python tools/heluo/quzheng_20261008/dump_natural.py      # 引擎自然输出（402 KB / 10 节段）
```

1983-11-03 12:00 男 / target=2026/7 跑出来的 HeluoResult（含六层卦象+解卦+诊断）：asdict 字符 ~85k，13.9ms。

## 9. 边界与已知非河洛缺陷（按红线「如实报告但不动手」）

| 缺陷 | 责任域 | 说明 |
|---|---|---|
| 紫微 iztro `lunar-typescript` Node 包缺失 | 紫微域 | 紫微 spec 失败（p15_shadow_integration 等） |
| LLM 渲染器 API key 401 | 基础设施 | 不在本分支 |
| `CrossDomainResult` 无 `status` 字段 | 显示层 | 不在本分支 |
| 流年切换点（立春/正月初一/公历 1/1）口径 | 时间系统 | 跟随黄历引擎（待用户口径决策） |
| `location_registry`「中山」表缺失 | 紫微域 | 紫微 iztro 路径打挂（紫微域责任） |

## 10. 修改清单（提交记录）

本分支 = `main` + 1 commit `docs(heluo): 新增 HELUO_ENGINE.md`。

主分支 main 河洛相关 commit（按时间倒序）：

| commit | 内容 |
|---|---|
| b2666ddf | 批次 P（河洛算力裁剪）两步落地——时间对接 + 99→2 段 |
| 759985d6 | fix(heluo): 诊断层与解卦层对同一份数据给出不同结论（数格方向 + source_ref 重复）|
| fe1b92bc | perf(heluo): 消除对 sxtwl 的重复计算（fromSolar 224→40） |
| dae04b1b | fix(heluo): 河洛诊断方向改由河洛自有判据给出（用户选 B 方案）|
| b522c6ac | fix(heluo): interpretation 接原典六项判据 + 诊断建议接入管线 |
| 4fcd2b1d | fix(heluo): 诊断图 signals 类型契约 + 建议层伪引残留 |
| 406de539 | test(heluo): 真实案例全量转储 1983-11-03 |
| 3cf6352e | test(heluo): 跑批案例换成 1940 后真实区间，22/22 跑通 |
| 6cbc9d49 | test(heluo): 端到端案例跑批脚本 + 本轮结果 |
| 29f7a566 | refactor(heluo): 批次 G —— 消掉自造副本表与同名不同义 |
| fb4e6d00 | refactor(heluo): 化工窗口吃引擎、不重复计算、不自造表 |
| bd943e00 | 取证落码批次 E/F |
| c6c57654 | fix(heluo): 深度审计批次 A/B/C/D |
| fed7a4a7 | fix(heluo): 化工「相生救应」空断言致克制盘误判为吉 |
| 30b25387 | fix(heluo): H11 节候卦回归《河洛真数》原典体系 |
| ea21ff61 | fix(heluo): 死断四法补后天段门控 |
| e3041139 | docs(heluo)+fix: 起例卷中/下算法对照表 + 余数奇偶修正 |
| 36ca5523 | fix(heluo)!: 作废三处无原典依据的自拟分数 |
| 8c145bdd | fix(heluo): 撤除两处无据内容 —— 伪造判词 + 节卦爻名分叉 |
| 59fab4de | feat(heluo): 节候卦新增节卦表 + 七十二候表 |
| 42166dd8 | fix(heluo)!: 阳月令按原典十二月卦气表更正 |
| ... 之前河洛 commit 共 50+ 条 | 涵盖原典覆盖、口径校订、多方取证等 |

主分支：main（HEAD = 78fc5694）
本分支：`feature/heluo-engine-package-20261011`（仅河洛域）

## 11. 与其它副本的差异（2026-10-21 整理时核实）

河洛引擎历史上存在三份副本，现已收敛为**本包为唯一活副本**：

| 副本 | 位置 | 状态 |
|---|---|---|
| **本包（权威）** | `feature/heluo-engine-package-20261011` | ✅ 25 模块 + 38 原典 + 16 测试，**354 全绿** |
| wisdom main | `ZQMMING/wisdom` `main`（`e6a6a41e`，09-30） | 旧架构快照，29 模块（多 5 个旧模块），**9-30 后未再更新河洛** |
| D:\shuntian 主工作区 | `feature/luming-engine`（`10a59d82`） | 河洛整目录已移走（"移除重复冗余"），**非河洛域不再持有河洛** |

### 11.1 旧模块的去向（不是缺件，是架构演进）

`8b863c62`（未接盘点收口）删掉 5 个模块，均为**无人 import 的死模块**：

| 旧模块 | 去向 |
|---|---|
| `temporal.py` | 能力迁入 `timeline_yun.py`（`class Timeline`）；`canonical.py` 改 `from .timeline_yun import Timeline` |
| `interpretation.py` | 内联进 `guajie.py` |
| `dayu.py` / `hexagram_state.py` / `time_sequence.py` | 旁支死模块，无人 import |

> wisdom main 上 `temporal.py` 仍是**活代码**（`canonical.py` 直接 import），故 wisdom 旧快照会与本包行为有别——**以本包为准**。

### 11.2 死代码留档

`hexagram_symbol.py` 引用了不存在的 `models` 模块，全仓无人 import，**导入即崩但不影响运行**。按原审计报告判定为历史遗留死代码，暂留档不删。

### 11.3 本次整理动作（2026-10-21）

- 补回 6 个河洛审计脚本（`audit/`）——它们在 `10a59d82` 移除主工作区副本时被一并删掉，
  且未进本包。取回自 `10a59d82^`，并把其中的 `sys.path.insert(0, r"D:\shuntian")`
  硬编码改为 `os.path.abspath(__file__)` 相对定位，6 个脚本实跑 exit=0 断言全过。
- 修正 `tests/heluo/test_heluo_kuozhan.py::test_canping_dir_default` 的路径断言
  （旧版硬编码 `D:\shuntian\data\heluo\canping`，换机/worktree 必挂）。
- 更新本文件模块清单（补 `heluo_lunar_bridge.py`）与守卫数字。

