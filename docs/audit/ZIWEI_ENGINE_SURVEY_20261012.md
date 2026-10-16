# 紫微引擎现场勘查报告

**日期**：2026-10-12
**范围**：`D:/shuntian` 紫微斗数引擎全链路（算 → 辨 → 解）
**性质**：只读勘查 + 测试验证，未修改任何业务逻辑
**环境**：Python 3.13（`.venv`）、Node（iztro 2.6.0）、pytest

---

## 一、代码规模

紫微相关源码合计 **17,775 行**（`wc -l` 实测）。

### 1.1 引擎核心（`src/tongshu/engines/`）

| 文件 | 行数 | 职责 |
|------|------|------|
| `ziwei_engine.py` | 1,374 | 排盘引擎：iztro subprocess 调用、`ZiweiChart` 契约、`GAN_SIHUA` 四化表、大限/流年/流月/流日四化、三方四正、宫干飞化 |
| `ziwei_adapter.py` | 272 | 阳历接入路径（`bySolar`），`ZiweiCalculationPolicy`（P0-14 已冻结） |
| `ziwei_palace_resolution.py` | 497 | 宫位解析、空宫借星、三方四正解析器 |
| `ziwei_dependency_adapter.py` | 475 | iztro 2.6.0 大限方向 bug 修正适配器（BUG-P0-2） |
| `ziwei_method_profile.py` | 286 | 流派契约：`MethodId` / `RuleType` / `ConfidenceLevel` / `SiHuaTable` |
| `ziwei/evidence_producer.py` | 268 | V13 契约证据生产者（`EngineEvidence`，只出事实） |
| `ziwei/dataset_bridge.py` | 515 | iztro → MockChart 桥接 + 12 项四化表核对 |
| `ziwei/z14/evidence_collector.py` | — | 同盘异法验收契约：一张盘两条独立证据链 |

### 1.2 规则层（`src/tongshu/engines/ziwei/rules/`）

| 文件 | 行数 | 职责 |
|------|------|------|
| `method_graphs.py` | 538 | `BaseZiweiRuleGraph` 抽象 + `SanheRuleGraph`（南派） |
| `qintian/combinations.py` | 3,609 | 钦天门 **60 条 production 检测器**（来因/时空/自化/体用/飞化/应期） |
| `interpretation.py` | 2,424 | 解层：`MultiMethodSignal` → 古典断语，逐字抄录 + `evidence_ref` |
| `answer_layer.py` | 906 | 答案层组装：两派规则命中 → 八维度平行答案 |
| `domain_reading.py` | 921 | 维度断语层：十二宫逐宫 + 六大领域聚合 |
| `nihai_assertions.py` | 812 | 倪海厦《天纪》主星×宫位断言 |
| `palace_star_verdicts.py` | 507 | 宫位·星曜论断层（43 组键） |
| `pattern_rules.py` | 317 | 格局规则 |
| `rule_graph.py` | 177 | 规则图数据模型 + **`PATTERN_DEFS` 40 格局** |
| `rules.json` 家族（decadal / temporal_rules / wuxing_rules / brightness / nvming_rules / child_limit_rules / limit_advanced_rules / palace_general_rules / palace_relationship / multi_method 等） | ~1,900 | 各专项规则 |
| `qintian/` 其余（evidence 601 / judgments 255 / features 121 / flow_day_contract 102 / rule_graph 114 / 三张数据表） | ~1,200 | 钦天证据绑定、判定映射、特征抽取 |

---

## 二、架构定位

### 2.1 全链路

```
八字排盘（输入层）
   ↓
紫微斗数 ── 算层：FrozenZiweiChart（一张盘，两派共用，不复制计算）
   ↓
        ├── 南派 SANHE    → SanheRuleGraph.match_all()
        └── 北派 QINTIAN  → QintianRuleGraph.match_all() + detect_all_production()
   ↓
辨层：MultiMethodSignal（两个 MethodBundle，命名空间隔离，不投票不融合）
   ↓
解层：interpretation.py（古典断语 + evidence_ref）
   ↓
答案层：answer_layer.py → 八维度（性格/格局/事业/婚姻/财运/健康/应期/四化体用）
   ↓
维度断语：domain_reading.py（十二宫逐宫 + 六大领域聚合）
```

### 2.2 已冻结契约

- **P0-14 时间政策**：`ZiweiCalculationPolicy.status == RATIFIED`（阳历/农历源、晚子时不换日）
- **Z17 两派收敛**（2026-09-14 用户定稿）：全系统收敛为 **SANHE（南派/倪海厦《天纪》）** + **QINTIAN（北派/钦天门）**；中州派、飞星派及其专属四化表已删除
- **V13 契约**：`evidence_producer` 只输出事实（数值/结构/位置/时间），**不带** direction/polarity/strength/confidence
- **算→辨→解 三层铁律**：计算层只调 iztro，**紫微路径无 LLM、无 score/weight/percentage**
- `FrozenZiweiChart = ZiweiChart`（别名，向后兼容）

---

## 三、规则资产盘点

| 流派 | 资产 | 规模 |
|------|------|------|
| 南派 SANHE | `PATTERN_DEFS` 格局 | **40 条**（紫微独坐/杀破狼/武贪/机月同梁…） |
| 南派 SANHE | 坐命断语 `SANHE-JUDG-星名` | 14 主星 × 4 维度（性格/吉凶/事业/婚姻） |
| 南派 SANHE | 四化规则 `SANHE-SIHUA-{干}` | 10 天干 |
| 南派 SANHE | 宫位规则 `SANHE-PALACE-{宫}` | 12 宫 + 宫干自化 |
| 北派 QINTIAN | `QTN-CMB-001` ~ `QTN-CMB-060` | **60 条 production**（`DRAFT_DETECTORS` 为空，无草稿残留） |
| 北派 QINTIAN | 证据绑定 | `EVIDENCE_BINDINGS` + `DRAFT_BINDINGS`，一手原文 grade 分级 |
| 四化表 | `GAN_SIHUA` | 传统三合派通行本（戊科=右弼 / 庚科=太阴 / 壬科=左辅）；南北两派共用 |

### 3.1 数据资产

| 资产 | 内容 |
|------|------|
| `cases/golden/ziwei_golden_set.json` | **80 案例**（倪海厦体系） |
| `cases/baselines/ziwei_chart_baseline.json` | 16 项基线 |
| `data/evidence/ziwei/` | E-ZIWEI-002 ~ 006（5 条） |
| `data/rules_index/ziwei_stars.json` | 星曜索引 |
| `data/semantic_atoms/ziwei_stars.json` | 语义原子 |

---

## 四、本轮实测结果

### 4.1 测试套件

```
./.venv/Scripts/python.exe -m pytest tests/ -k ziwei \
  --ignore=tests/test_blind_rule_registry.py \
  --ignore=tests/test_llm_client.py \
  --ignore=tests/test_ziping_15_2_evidence_provenance.py

结果：499 passed, 1 failed, 1 skipped, 32 subtests passed（282.78s）
```

> 3 个 `--ignore` 是**预先存在**的收集错误（`test_blind_rule_registry` / `test_llm_client` / `test_ziping_15_2_evidence_provenance`），
> 与紫微无关，此前报告（`ZIWEI_ENGINE_REPAIR_REPORT_20260928.md`）亦已记录同类 collection error。

### 4.2 唯一失败项归因（非代码缺陷）

- **失败用例**：`test_ziwei_answer_layer_p12.py::TestBodyPalaceSixHomes::test_body_palace_only_six_homes`
- **报错**：`RuntimeError: iztro full_chart failed: node:fs:440`（`ziwei_engine.py:1033`）
- **归因**：该用例穷举 60×2×12 = **480 次** `full_chart()` 子进程调用，本身即重度依赖 Node 文件读取；
  本次运行**沙箱拦截了 iztro 读取自身 `node_modules`**（`zh-TW/fiveElementsClass.js`、`lib/data/earthlyBranches.js` 等），
  属环境侧资源竞争/权限拦截，非引擎逻辑问题。
- **验证证据**：
  - 单独跑整个 `test_ziwei_answer_layer_p12.py` → **8 passed**
  - 用脚本完整复现该用例的 480 次遍历 → **total 480, fails 0**（190.6s）
- **结论**：`full_chart()` 在 480 组参数下全量可用，身宫恒落六寄宫（命/财/官/迁/福/夫妻）成立。

### 4.3 编译检查

```
compileall.compile_dir('src/tongshu/engines/ziwei')  → True
compileall.compile_file('src/tongshu/engines/ziwei_engine.py') → True
```

---

## 五、观察到的风险与待办

| # | 项 | 说明 | 严重度 |
|---|----|------|--------|
| R1 | 测试对沙箱 I/O 敏感 | 480 次 Node 子进程调用的用例在受限权限环境下会误报；建议该用例标记 `@pytest.mark.slow`，或复用单盘 fixture | 🟡 中 |
| R2 | 3 个 collection error | `test_blind_rule_registry` / `test_llm_client` / `test_ziping_15_2_evidence_provenance` 长期未清 | 🟡 中 |
| R3 | 沙箱读取 `node_modules` | iztro 需读自身包文件；在沙箱内跑紫微全链需放行 `D:/shuntian/node_modules/**` 只读 | 🟢 低 |
| R4 | 免费双源核对 | 钦天 60 条虽标 grade=1（一手原文），但 `EVIDENCE_STATUS` 分级与 `MATCH_STATUS`/`CONCLUSION_STATUS` 三分离原则建议再走一轮独立审计 | 🟢 低 |
| R5 | 单测运行时长 | 紫微全量测试 ~4.7 分钟，主因是每次排盘起一个 Node 进程；后续可考虑常驻 Node 服务降本 | 🟢 低 |

---

## 六、结论

紫微引擎处于**可运行、结构清晰**的状态：

- **算层**：iztro 确定性排盘，双路径（农历 `byLunar` / 阳历 `bySolar`）已对齐，历史结构缺失 bug 已修
- **辨层**：两派平行，命名空间隔离，无投票、无 score、无 LLM
- **解层**：断语逐字抄录、带 `evidence_ref`、未命中 fail-closed
- **资产**：南派 40 格局 + 14 坐命断语 + 北派 60 条 production，Golden 80 案例，测试 499 绿

本轮**未发现引擎逻辑缺陷**；唯一失败项为沙箱 I/O 偶发，已用 480 次全量遍历证伪。
