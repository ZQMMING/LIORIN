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

- **927 passed**（`python -m pytest tests/` 全量，含 16 个河洛测试文件）
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

## 11. 与其它副本的差异 + 2026-10-21/22 重建记录

河洛引擎历史上存在三份副本，现已收敛为**本包为唯一活副本**：

| 副本 | 位置 | 状态 |
|---|---|---|
| **本包（权威）** | `feature/heluo-engine-package-20261011` | 36 模块 + 56 原典 + 285 规则 + 52 守卫 + 58 工具，**927 全绿** |
| wisdom main | `ZQMMING/wisdom` `main`（`e6a6a41e`，09-30） | 旧架构快照，29 模块，**9-30 后未再更新河洛** |
| D:\shuntian 主工作区 | `feature/luming-engine`（`10a59d82`） | 河洛整目录已移走（"移除重复冗余"），**非河洛域不再持有河洛** |

### 11.1 【重要】独立包曾发生功能退化，2026-10-22 已修复

`19ea5ea7`（10-16，名为「河洛引擎独立打包更新——修复+元气/断语层+真太阳时口径统一」）
实测是**大删减**：相对共同祖先 `78fc5694` **净删 6540 行、只加 1212 行**。

删掉的每一项都有 main 上的守卫在用：

| 被删 | main 上的守卫 | 后果（实测） |
|---|---|---|
| `hua_gong.py` -634 行 | `test_h6_hua_gong.py` 等 | **用 main 守卫测独立包代码 → 25 failed / 7 passed** |
| `jiegua` / `yue_ling_shu_ge` / `gui_ming_liu_ju` / `xian_tian_ce_shu` / `yao_xiang` / `yuanqi_tables` / `temporal` / `time_sequence` / `hexagram_state` / `dayu` / `interpretation` | 13 个守卫文件 | collection error |
| `jiehhou.solar_term_date`（批次 L 性能优化，fromSolar 224→40） | — | 退回逐日扫整月 92 次 |
| 批次 P fast-path（99 骨架 + 2 段嵌入） | `tests/test_heluo_fastpath.py`（10 条） | 输出体积 **10MB → 65MB（6.3 倍）** |
| 33 个守卫文件 | — | 「删掉会失败的测试让全绿」 |

同盘对比（5 个真实案例）：

- **化工**：独立包判 `RESCUED`（救应·吉），main 判 `KEZHI`（克制·原典"尤凶"）
  → 即 `fed7a4a7` 修过的「相生救应」空断言 bug 回归
- **structure**：独立包 `hu_gua` / `cuo_gua` / `zong_gua` 全 `None`（互/错/综卦未接，`9004e649` 修复丢失）
- 其余字段（numbers / prenatal / yuantang / postnatal / guajie 等）**完全一致**

### 11.2 本次重建（以 main 河洛域为准）

1. **`src/tongshu/engines/heluo/`** ← main 全部 34 模块
   （恢复化工三级判据、互错综卦接线、死断诸法、批次 L 性能优化、批次 P fast-path、
   以及被删的 11 个模块）
2. **`data/heluo/`** ← main 完整原典数据（56 文件，canping 金土部 78 条全量）
3. **`data/rules/`** ← main 的 `HL-*` / `HLT-*` 判据规则表（285 个）
4. **`tests/heluo/`** ← main 47 个守卫 + `tests/` 顶层 10 个 heluo 守卫
5. **`tools/heluo/`** ← main 的变异验证 + 取证 + 独立复核脚本（58 个）

### 11.3 补修的两个导入缺陷（本包特有）

- **`src/tongshu/__init__.py`（补）**：独立包原先缺此文件 → `tongshu` 退化为
  namespace package（`__file__ = None`）→ pytest 收集时 `tongshu.engines.heluo`
  解析失配，报误导性的 `No module named 'tongshu.engines.heluo'`。补回后导入链恢复。
- **`src/tongshu/engines/__init__.py`（新增）**：main 版导出 Ziwei / Huangli，
  本包不含，故写惰性导出版（只导 Heluo / Bazi）。

### 11.4 从独立包移植回来的新功能

| 功能 | 来源 | 状态 |
|---|---|---|
| **H7 元气层** | `5f837cbf` | ✅ 已移植（canonical + frozen_state），`test_h7_yuan_qi.py` 7/7 |
| **H10b 节气为界均匀分配** | `e13e7fd7` | ✅ 机制已移植（`compute_liuri` 新增 `next_jie_datetime` / `rule="gua6"`；`_jie_interval_for_lunar_month`）——**作为显式调用能力**，生产路径保持 main 批次 P 行为不变 |
| **H10 惰性化** | `e15298dd` | ❌ 未移植（重写 canonical 133 行 + guajie 105 行，与批次 P fast-path 方案冲突；**保留 main 方案**，其 10 条 fast-path 守卫钉死） |
| **H9b 黄历×河洛桥接** | `ec6e2214` | ❌ 未移植（依赖 H10 的 `target_*` 惰性化接口；`heluo_lunar_bridge.py` 已随重建进包，待接） |

> H10b 的另两条数值契约（`test_hou5_uniform_not_mechanical` / `test_gua6_five_segments`）
> 依赖独立包独有的「农历月 ↔ 流月编号」映射，在 main 代码底上不成立，
> 拆分为 `tests/heluo/test_h10b_jie_interval.py` 保留与映射无关的两条
> （节气间隔真实不均等 / 30 日整间隔退化一致），其余待口径统一后重校。

### 11.5 变异演练已恢复（核心方法论资产）

独立包此前无 `tools/` 目录 → 「变异演练防自证」全部缺席（能测但不能证伪）。
补回后实测 `mutation_verify_hua_gong.py`：

- 基线全绿 OK（69 passed）
- 注入「KEZHI 退回 RESCUED（原典尤凶又变吉）」→ **[CAUGHT]**
- 注入「五行相克表清空」「相克判定退化单向」「KEZHI 映射回 SUPPORTIVE」
  「反卦表退回先天对宫」「伪引文复现」「真实原句被删」「出处改回伪节名」等 → 全部 **[CAUGHT]**

正是这类演练能提前抓住 11.1 节的退化。

### 11.6 死代码留档

`hexagram_symbol.py` 引用了不存在的 `models` 模块，全仓无人 import，**导入即崩但不影响运行**。
按原审计报告判定为历史遗留死代码，暂留档不删。

### 11.7 本包不含的守卫（集成层依赖）

以下守卫依赖 `tongshu.pipeline` / `tongshu.engines.meihua` / `tongshu.reasoning.signal_engine`
等**集成层**，本独立包不含，故不纳入：

`test_meihua*`（4）/ `test_heluo_event_topic_claims` / `test_heluo_birthinfo_passthrough`
/ `test_h16_independent_verification` / `test_b01_heluo_yi_passthrough` / `test_heluo_context`
/ `test_heluo_guajie_wiring` / `test_heluo_yi_flow` / `test_layer_consistency_20261009`
/ `test_own_direction_20261008` / `test_interp_and_wiring_20261008`

这些守卫在 main 上**全部存在且通过**（集成层跑），并未被删除。

## 12. 算力口径定稿（2026-10-22）

用户定稿的河洛理数计算规则（**一卦管 6 日、一爻一日**），本包已按此落码。

### 12.1 四层口径

| 层 | 定稿 | 本包落点 |
|---|---|---|
| **出生静态层** | 先天卦 / 后天卦 / 元堂 / 天数 / 地数，一次计算永久复用 | `HeluoCanonical.calculate`（未变） |
| **大运层** | 只生成**元数据**，不起大运卦 | `frozen_state.dayun_summary` 落 `{start_age, end_age, ganzhi}`；`qi_phase.dayun` 仍留完整字段供 guajie 运反判定 |
| **流年层** | 只算**近 3 年**完整流年卦，其余只存元数据 | `timeline.yearly_hexagrams`（3 条）+ `timeline.yearly_meta`（96 条 `{year, age, ganzhi}`） |
| **流月层** | 只有**目标年**算 12 个流月卦（全算） | `timeline.monthly_hexagrams`（12 项） |
| **流日层** | 1 个流日本卦（完整卦一次算好）+ 6 日各自激活爻 | `timeline.daily_hexagram{base_hex, daily_yao[6]}` |

近 3 年之所以保留完整流年卦：guajie 的「近 3 年流年判词」
（`guajie.py` L1779-1796）取 `yearly[].hexagram / yuantang_index / lines`，
是既有功能，不因裁剪而丢弃。

### 12.2 流日层口径（一卦管 6 日、一爻一日）

定稿原文：
> 「完整起卦：只做1次，生成流日本卦本体（本卦、互错综、基础卦气全部一次算好）
> 　之后6日唔再起完整卦；每日只取对应爻（初爻→第1日，二爻→第2日……上爻→第6日），
> 　单独跑该爻嘅爻变、卦气、象义运算，属于轻量爻运算。
> 　6日用完，先至起下一个新流日卦。」

落码（`timeline_yun.compute_daily_base_hex`）：

- **段边界按节气实际间隔均匀分配**（不可执定「卦六日」死板规则）：
  当月按节时刻 T0 → 下月节时刻 T1 的**实际间隔**均匀切成 5 段，
  段长 ≈ (T1-T0)/5（约 5.9~6.3 日，**不是固定 6 日**）
  · 实测：某年 7 月 jie_span_days = 31.12 日 → 第 3 段日序 **14-19**（非固定 13-18）
  · 段首带真实时刻（`date_from`，如 `2026-08-20 06:29`）
- 每段 1 个流日本卦（本体/互/错/综/卦气**一次算好**）；互错综复用 `hexagram.py`
  的权威实现，不自造第二套口径
- 段内 6 日共用本卦，每日只取对应爻位（**首日从初爻开始**：初→1日 … 上→6日）
  做**轻量爻运算**（爻变 + 卦名 + 卦气五行），不再起完整卦
- 段间链式推进：第 k 段本卦 = 链式 `day_lines[k*6]`
- 本任务只算**目标日所在的那一段**
- `daily_yao` 每条含 `day_no / day_in_seg / active_yao / yao_index / yao_nature /
  changed_name / changed_upper / changed_lower / changed_lines / changed_element`

### 12.3 与原典 L129 的关系（如实留档）

原典《河洛真数·起例卷之上》L129 另一套口径：
> 「凡起日卦……**每一爻管五日**，阳日寻阳爻位……**挨次而变，不容紊也**」
> L130：「**六爻俱变毕，则满三十日**，是为一月之日卦」

即原典是「每爻管 5 日 + 链式累变」（本包内的 `hou5` 口径），
而定稿是「一卦管 6 日 + 一爻一日」（`gua6`）。**两者不可兼容**。

本包的处理：
- **fast-path（target_year 非 None）按定稿走 gua6**
- **全量路径（target_year=None）保持 hou5 旧契约**（守卫
  `test_full_path_payload_is_baseline` 钉住全量体积基线 ~2.0M，不受定稿影响）
- `materialize_month_days` 按 days 形态自动分流：带 `day_no` → gua6 新结构；
  不带 → hou5 stub 走旧法现算

### 12.4 输出结构

```
timeline:
  yearly_hexagrams     近 3 年完整流年卦（3 条）
  yearly_meta          其余流年纯元数据（96 条 {year, age, ganzhi}）
  target_year_hexagram 目标流年卦摘要（ganzhi/hexagram/yi_signal/changed_line）
  monthly_hexagrams    目标年 12 个流月卦
  daily_hexagram       {base_hex: 完整卦, daily_yao: 6 日激活爻}
frozen_state:
  dayun_summary        大运纯元数据（12 条 {start_age, end_age, ganzhi}）
```

`ganzhi` 定义：大运是「爻位值运」（阳爻 9 年 / 阴爻 6 年），不按干支轮转，
故取该段**起始年**（虚岁 == start_age）所对应的流年干支作定位标识。

### 12.5 算力实测（1983-11-03 12:00 男 / target=2026/7）

| 指标 | 定稿前（批次 P） | 定稿后 |
|---|---|---|
| HeluoResult 总字符 | 9,934,038 | **17,593**（约 565× 压缩） |
| timeline 子树字符 | 9,934,038 | **14,915** |
| 耗时 | — | 23.8 ms |

定稿估算「大约 2.8 万字符」——实测 1.76 万，比估算更省。

### 12.6 守卫

`tests/test_heluo_fastpath.py` 按定稿重写为 12 条，保留全部防退化意图：
- yearly_hexagrams 只含近 3 年；yearly_meta 恰为 {year, age, ganzhi} 三字段
- 非近 3 年流年禁止 yi_signal / yi_interpretation / days / hours（dead-write 不得复活）
- 只有目标年嵌 months（12 个）
- 顶层 monthly_hexagrams 12 项
- 顶层 daily_hexagram 含 base_hex（完整卦）+ daily_yao（6 日，day_no 1..6，active_yao 初→上）
- 顶层 target_year_hexagram 摘要字段齐
- timeline 体积 < 100k
- target_year=None 退回全量（旧契约冻结保留）

### 12.7 H9b 恢复

`19ea5ea7` 大删减时被一并删掉的「河洛×黄历桥接」本次恢复
（独立包 `ec6e2214`）：`GuaJieResult.liuri_lunar` 字段 + `build_guajie_from_result`
的 `huangli_provider` 形参 + 流日应期段挂黄历标注（注入优先，lunar_python 兜底）。
`heluo_lunar_bridge.py` 本就在包内，本次接通。
