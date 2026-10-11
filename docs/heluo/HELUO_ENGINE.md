# 河洛引擎（Heluo Engine）— 接线与契约

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

`canonical.calculate(target_year, target_month)` 启用 fast-path 时：

- **99 流年骨架保留**（依赖大运段判定）；
- **目标流年 + 上一年 2 段嵌满 12 月 × 6 日**；
- **其余 97 段只元数据**（10 字段：age/year/ganzhi/yang_year/hexagram/upper/lower/lines/yuantang_index/yuantang_nature，无 months/days/yi_signal/yi_interpretation）；
- **不再调 `interpret_all_liunian`**（yearly[].yi_signal / yi_interpretation 全仓零消费方，是 dead-write）；
- 顶层 `monthly_hexagrams` = 目标年 12 月（扁平化）；
- 顶层 `daily_hexagram` = 目标年目标月 6 日段链式累变。

**实测压缩**（1983-11-03 12:00 男 / target=2026/7）：
- asdict 字符数：~2,142,000 → ~85,000（**25 倍压缩**）
- 耗时：~120ms → ~13.9ms（**8 倍**）

`canonical.calculate(target_year=None)` 退回全量路径（旧契约保留，守卫钉死）。

## 5. 模块接线

```
src/tongshu/engines/heluo/
  ├─ canonical.py             主入口 HeluoCanonical.calculate()
  ├─ timeline_yun.py          大运 + 流年 + 流月 + 流日（六爻俱变）
  ├─ evidence_producer.py     解卦层证据
  ├─ guajie.py                H8 解卦层（3000+ 行原典断语）
  ├─ diagnosis_rule_graph.py  诊断层 HL_* 判据
  ├─ interpretation.py        YiStructure 拼装
  ├─ frozen_state.py          FrozenHeluoState 冻结态
  ├─ yi_interpreter.py        YiInterpretation
  ├─ yuan_tang.py             元堂（先/后天）
  ├─ yuan_qi.py               元气（先/后天）
  ├─ yuanqi_tables.py         元气查表
  ├─ yue_ling_shu_ge.py       月令数格
  ├─ hexagram.py              卦象基础
  ├─ hexagram_state.py        卦气状态
  ├─ jiehhou.py               H11 节候卦
  ├─ hua_gong.py              化工（原典 L558-L567 节气窗口）
  ├─ dayu.py                  大运爻位值运
  ├─ jiegua.py                解卦（基础）
  ├─ gui_ming_liu_ju.py       贵命六体
  ├─ canping.py               参评
  ├─ prenatal.py              先天卦
  ├─ postnatal.py             后天卦
  ├─ yao_xiang.py             爻象取象（原典 L741）
  ├─ xian_tian_ce_shu.py      先天策数
  ├─ metrics_v2.py            指标 V2
  ├─ exceptions.py            异常类
  ├─ input.py                 HeluoInput
  ├─ schemas.py               数据 schema
  ├─ temporal.py              时间原子对象
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

- **1005 + 3 subtests passed**（heluo 子目录）
- **10 条 fast-path 守卫**（`tests/test_heluo_fastpath.py`）：
  - 99 流年骨架完整 + 10 元数据字段
  - 仅目标流年 + 上一年 2 段嵌 12 月 × 6 日
  - 其余 97 段钉死无 months / yi_signal / yi_interpretation / days / hours
  - 顶层 monthly_hexagrams 12 项 + daily_hexagram 6 段
  - target_month 未传 → daily_hexagram 保持空 {}
  - timeline 体积 < 100k chars
  - target_year=None → 全量路径体积 ∈ [1.5M, 3M]（锁基线）
- **变异演练**（`tools/heluo/quzheng_20261008/`）：防回归

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
