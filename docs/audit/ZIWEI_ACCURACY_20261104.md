# 紫微引擎 · 排盘准确率核验与修正（2026-11-04）

> 负责人：本会话（紫微引擎 line）。范围：**算得准**，不以测试绿灯为验收。
> 关联：`AGENTS.md` 三重取证；`docs/PROJECT_INVENTORY.md`（紫微状态 BLOCKED 的历史记录）。

## 一、为什么要重做核验

生产排盘 `tongshu/engines/ziwei_engine.py` 是 **iztro（npm 2.6.0）的 subprocess 包装**；
而仓库里的“紫微 Golden 80 案”（`cases/golden/ziwei_golden_set.json`，来源
`renhuai123/ziwei-doushu` v3 倪海厦体系）**本身也是用 iztro 生成的**（见该数据集
`lib/ziwei/algorithm.ts` 直接调用 `astro.bySolar`）。历史验收数字（80/80、240/240）
因此是“拿 iztro 验 iztro”的自洽循环，不能作为准确率结论，符合用户“不自洽、不手调全绿”的要求。

## 二、真值层（新增）

新增 `src/tongshu/engines/ziwei_natal.py`：按《紫微斗数全书》通行安星诀独立实现，
不 import iztro、不 import 任何第三方排盘库：

- 命宫（寅起正月顺数、起子逆数）/ 身宫（同起点顺数）
- 五行局（五虎遁定命宫干 + 六十甲子纳音 → 水二木三金四土五火六）
- 紫微星（日数除局数；除尽取商数前一宫；余数取补数，单退双进）
- 十四主星（紫微系逆、天府系顺）/ 六吉六煞 / 禄存天马 / 十四主星亮度位
- 本命四化（通行本十干表，与 `GAN_SIHUA` 同源）/ 大限（局数起限、阳男阴女顺）/ 命主身主

**校核过程（全部可复现）**

| 校核项 | 方法 | 结果 |
|---|---|---|
| 紫微安星表 | 用 iztro 全月×全时×全日 4260 盘聚合出 (局,日)→紫微 150 格 | 我方公式 **150/150** |
| 核心排盘全字段 | 独立实现 vs iztro 逐字段（命/身/局/紫微/14主星/14辅煞/四化/命主身主/大限/宫干） | 1990 男 4260 盘、1990 女 4260 盘、1983 女 4260 盘、1961 男 4260 盘，**全 0 不一致** |
| 大限区间 | 逐宫 `decadal.range` 对照 | **51120/51120** |
| 外部数据集 | 独立实现 vs Golden 80 案 expected | 命/身/局/紫微/12宫主星 **80/80** |
| 生产适配器 | `scripts/ziwei_natal_verify.py` 抽样 195 盘 × 9 字段 | **100%**（修正后） |

> 说明：独立实现与 iztro 在 17040 盘上完全一致，是两条互不依赖的代码路径在同一口诀上的
> 收敛，而不是同一实现的自比对。

## 三、发现并修正的缺陷

### D1（已修）包级死导入，亮度注入随机失效

`src/tongshu/engines/ziwei/__init__.py:45` `from .rules.classical_detail import build_classical_detail`
——该模块**在全仓所有 ref（含 origin/*）都不存在**。后果：
包 `tongshu.engines.ziwei` 导入抛 `ModuleNotFoundError`；`full_chart` 内亮度注入的
`try/except` 把它吞成 warning，且因 Python 部分导入的 sys.modules 残留，
**同一进程内亮度时而注入、时而缺失**（Z80-G 式假绿）。同时造成 3 个测试文件收集失败。

修正：删除该死导入与 `__all__` 条目。

### D2（已修）两条生产排盘入口排出两个盘

| 入口 | 输入 | 借对宫 | 生年四化 | 亮度表 | 天刑天姚 | 斗君 |
|---|---|---|---|---|---|---|
| `ZiweiEngine.full_chart` | 农历 | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ZiweiSolarAdapter`（pipeline 实际消费） | 阳历 | ❌ | ❌ | ❌ | ❌ | ❌ |

修正：新增 `ziwei_engine.postprocess_natal_palaces()` 作为**唯一后处理实现**
（亮度表 → 天刑/天姚 → 命宫空宫借对宫 → 生年四化入命宫 → 生年斗君），
`full_chart` 与 `solar_to_chart` 均调用它；`solar_to_chart` 的 JS 侧补输出
`rawDates.lunarDate` 以提供斗君所需的农历月。

### D3（已修）键名混用

适配器 `palaces[*].major` 为拼音键，`brightness` 原为中文键 → 同一字典两套命名，
下游按 major 取亮度会全部 miss。修正：`brightness` 键统一为拼音，与 major 对齐。

### D4（已核实，无需改）晚子时

`time_index_from_hour(23) = 12`。实测 iztro timeIndex 12 对**日系安星取次日**
（1990-3-1 23:00 紫微=未，与 1990-3-2 00:00 相同），与“23 点起次日”一致；
命宫/身宫按子时不变。口径可用。

### D5（已裁决：原典明文档）闰月折算

`bySolar(..., fixLeap=true)`（生产与数据集都用 true）读 iztro 源码
`utils.fixLunarMonthIndex` 确认为**闰月分上下半月**：闰月 1–15 日按本月算、
16 日起按次月算（晚子时 timeIndex=12 不作次月折算）。实测
1995 闰八月十八 → 命宫按月 9；1995 闰八月十五 → 按月 8。

**原典裁决（2026-11-05）**：《紫微斗数全书》原文
（`D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\古籍文字版\紫微斗数全书_完整原文.txt:714`）
「假如正月生子时就在寅宫安身命……**又若闰月正月生者要在二月内起安身命，
凡有闰月具要依此为例**」——原典口径是**闰月整体作次月**，不是上下半月折算。

裁定：
1. **产品口径（原典口径）** = 闰月整体作次月，落地在原生真值层
   `ziwei_natal` 的「原典模式」（`leap_mode="classic"`）；
2. **生产当前口径** = iztro 上下半月折算（`leap_mode="half_month"`），
   与数据集（ziwen-doushu 由 iztro 生成）保持可比；两种口径**显式可切换**，
   不再混用，差异登记在 `ziwei_natal.py` 模块级 docstring；
3. 核验分母仍是上下半月折算（200 盘含 5 个闰月盘，100% 一致），
   「整体次月」口径另做原典锚点回归（闰八月十五/十八两案）。

### D6（已补，2026-11-05）classical_detail 通道恒空

`answer_layer.py` 的 `classical_detail` 顶层通道在 Z80-H 文档里被描述为已接线，
但实现文件不存在，`_build_classical_detail_safe` 永远走空结构兜底。
这属于**解层**缺口（不是排盘算错）。

已补：`src/tongshu/engines/ziwei/rules/classical_detail.py`（`build_classical_detail`），
接 9 张母表 → 9 个出口（`palace_jue` / `classical_patterns` / `nvming` /
`child_limit` / `limit_advanced` / `temporal_rules` / `aux_verdicts` /
`temporal_facts` / `summary`）。四条反假命中纪律：

1. 原文 `verbatim` 原样带出，不改写；
2. 只有「母表条件句 → 机器可判定谓词」一一映射的条目才 `evaluated=True`；
   `_PATTERN_SPEC`（49 条）与母表 `formation_conditions` 1:1，测试校验无孤儿/无缺项；
3. 命中必须带 `evidence`（逐条谓词实测值）；
4. 未实现判据（空旬空亡 POV-01~03、日月反背 POV-04、MISC 运限八条）一律
   `evaluated=False + reason`，实测 1990-03-01 午时男盘 12 条进 `summary.unevaluated`、
   0 条假命中。

`PF`/`PD` 21 条经核：条文内含星曜组合条件（如 PD-08「戌上紫破若相逢」要求
紫微+破军同宫），母表未结构化 → 出口只作按命宫地支的**参考条文**（`hit=False`），
不输出得地/失陷吉凶结论（此前只按地支直出的版本会给出错误结论，已改）。

实测（1990-03-01 午时男，命宫戌）：格局命中 `NOB-19/20/21`（带证据）、
四组十二神与运限事实齐备、2026 丙午 流禄巳/流羊午/流陀辰 与 `temporal_facts` 一致。
回归：`tests/test_ziwei_classical_detail.py` 9 passed；紫微测试族 **606 passed / 1 skipped**。

### D7（已修）Golden 80 案的输入语义与生产口径不一致

`ziwei_golden_set.json` 的 `input.birth_hour` 是**时辰序号 0–12**（数据集生成时直接
当 iztro timeIndex 传入），而生产适配器按 **24h 小时**解析并转 timeIndex。
直接拿 golden 喂生产适配器会得到 85% 的“差异”，但那是输入语义错配，不是排盘错
（原始实录：80 案中 68 案命宫错位）。

修正：
1. `scripts/golden_replay.py::_exec_case`（ziwei 分支）增加 `_time_index_to_hour24()`
   显式换算（h = 2ti−1，ti=0→0，ti=12→23），Golden 集本身**未改动**；
2. 新增 `scripts/ziwei_golden_accuracy.py`：按正确语义逐字段比对
   `expected_calculation`（命宫/身宫/五行局/紫微星/十二宫主星）。
   结果：**80/80 逐字段全部一致**。

副作用（按 V2 §21 需登记）：`golden_replay --engine ziwei --check` 的 hash
`92c8da4d9e641d4e → aff32f7e7c8633ed` **EXPECTED_CHANGE**
（原因是修正输入语义，不是回归；基线快照 `cases/baselines/golden_replay_baseline.json`
需在裁决后用 `--snapshot` 重录，本次未擅自改写锚定文件）。

### D8（已修）`npm install` 本身是坏的

根 `package.json` 声明 `lunar-lite: "^1.0.0"`（npm 上最新仅 0.2.8，无 1.x）与
`lunar-typescript`，而 `package-lock.json` 根依赖只有 `iztro`（lock 与 manifest 不一致），
且全仓 JS 没有任何地方直接 `require` 这两个包（iztro 自带其传递依赖）。
结果：`npm install` 必失败（ETARGET）→ 生产排盘依赖装不上，紫微引擎在干净环境根本起不来。
修正：`package.json` 对齐 lock，只保留 `iztro: ^2.6.0`；已在独立目录验证可安装。

### D10（已修）引擎内两张亮度表互相矛盾（88/168 格）

`rules/brightness.py`（Z39 四档：庙/旺/利/陷，注入 `palaces.brightness`）与
`rules/interpretation.py` 自带的六档 `STAR_BRIGHTNESS`（庙/旺/得/利/平/弱/陷，
用于断语断言）**168 格中 88 格三档归类相反**，例如：

- 紫微卯：六档表「弱」/ Z39「庙」
- 天同午：六档表「庙」/ Z39「陷」（按《全书》天同午为陷）
- 天相与天梁两行**完全相同**（复制粘贴错误）

裁定：以 iztro/倪海厦体系数字化样本（1990 全网格）做第三方对照，
旧六档表三档归类只对 **75/168**，Z39 四档表对 **158/168**（唯一差异是已登记的
「太阳酉→利」命图裁决）→ 旧表判为错表。
修正：`interpretation.STAR_BRIGHTNESS` 改为由 `rules/brightness.py` **派生**
（旧表改名 `_DEPRECATED_STAR_BRIGHTNESS_6LEVEL` 留痕、不再被消费），
引擎内只保留一张亮度表。核对：168 格不一致 **0**；断语相关测试 111 passed。

### D11（记录）辅星亮度未进 `palaces.brightness`

`inject_brightness_table` 只对主星填 `palaces.brightness`；文昌/文曲/火星/铃星/
擎羊/陀罗等辅星的亮度仍只在 `starDetail[*].brightness`（来自 iztro 六档）。
`domain_reading` 消费 starDetail，因此功能上未缺失；若后续规则要按辅星庙旺门控，
需先补辅星亮度表（尚未裁决口径）。

### D9（已修）流日命宫偏 2 宫：`palaceNames` 是寅起不是子起

`_resolve_flow_day` 取 `daily.palaceNames.indexOf('命宫')` 后直接用 `B[li]`
（B 为子起地支表）。实测 iztro 各层 `palaceNames` 的下标与 `astrolabe.palaces`
同序 = **寅起**：流年层 2024(辰)/2025(巳)/2026(午) 的「命宫」下标分别
2/3/4，即 `idx = 流年支 − 2`。原实现使 `daily_luck_palace` 恒偏 2 宫。
修正：`B[(li + 2) % 12]`。修复后 1990-3-1 男：2026-06-01 流日命宫=寅、06-02=卯（逐日顺行一格）。

## 四、修正后的可复现命令

```powershell
cd D:\shuntian
$env:PYTHONPATH='src;.'; $env:PYTHONUTF8='1'
# 前提：node_modules/iztro 存在（npm install；已在 .gitignore）
python scripts\ziwei_natal_verify.py 200      # 独立口诀实现 vs 生产适配器，逐字段准确率
```

输出（2026-11-04 第三轮）：`核验盘数 = 150（含闰月 4 盘）；13 个字段全部 100%`
（命宫支/身宫支/五行局/紫微星/十四主星/辅煞星/命宫主星/生年四化/亮度注入/
长生十二神/博士十二神/将前十二神/岁前十二神）。

其他校核脚本（临时，`.tmp_cases/ziwei_audit/`，未入库）：
`oracle_vs_dataset.py`（80 案）、`oracle_vs_iztro_grid.py`（全网格）、
`decadal_brightness.py`（大限+亮度表聚合）、`paths_consistency.py`（双路径一致性）、
`adj_diag.py`（38 杂曜逐星）、`probe_years.js` + `multi_year_check.py`（60 甲子抽样）。

## 四之二、第二轮进展（2026-11-04 续）：38 杂曜 + 60 甲子

真值层 `aux_stars` 从 18 颗扩到 **38 颗**（iztro 的 minor+adjective 全名单）：
六吉六煞、禄存天马、三台八座、恩光天贵、台辅封诰、红鸾天喜、天刑天姚、
华盖咸池、孤辰寡宿、破碎蜚廉、龙池凤阁、天哭天虚、天才天寿、天伤天使、
天官天福、天厨、年解、解神（月解）、阴煞、天月、天巫、天德月德、天空、截路、空亡、旬空。

**修正的 6 条口诀错误（我自己的实现错，不是 iztro 错）**：
- 五虎遁定宫干：子/丑宫绕回天干时不能按 10 取模（影响 21% 盘的五行局）
- 紫微安星：商数宫起寅、除尽取前一宫、补数单退双进（原实现进退方向反了）
- 华盖：三合墓库表错位（寅午戌应戌）
- 天官/天福/天厨：三张年干表全错
- 孤辰/寡宿：按三合局分组（原实现按支序线性，错）
- 天伤/天使：宫位按地支顺行编号，天伤=命宫+5（仆役）、天使=命宫+7（疾厄）

**核对结果**：
- 1990 全网格 4260 盘 × 38 杂曜：**逐星 0 不一致**
- 1924–1983 全 60 甲子抽样 2880 盘（12 月 × 2 时 × 2 日）：命宫/五行局/十四主星/38 杂曜 **0 不一致**

**口径说明**：杂曜公式依据 iztro 源码注释所引的安星诀（如「甲丁食蛇口…」「天伤奴仆、天使疾厄」），
属**实现参考资料**，尚未与《紫微斗数全书》原典原文逐字核对；仓库内无紫微原典文本（见 D6）。

## 四之三、流年 / 大限层核对（2026-11-04 续）

6 个命例 × 4 个流年（2024/2025/2026/2030）逐项对照 iztro `horoscope()`：

| 字段 | 口径 | 不一致 |
|---|---|---|
| 宫干 | 五虎遁（含子丑绕回） | 0 |
| 流年命宫 | 流年支所在宫（`palaceNames` 寅起：idx = 支 − 2） | 0 |
| 流年四化 | 流年干查通行本四化表 | 0 |
| 大限宫支 | 五行局起限 + 阳男阴女顺/阴男阳女逆 | 0 |
| 大限宫干 | 大限宫五虎遁 | 0 |
| 大限四化 | **按大限宫干**查表（非生年干） | 0 |

核对中发现并修正生产缺陷 D9（流日命宫 palaceNames 寅起假设错误）。

## 四之四、四组十二神（长生 / 博士 / 将前 / 岁前）

真值层新增 `twelve_gods()`：

- **长生十二神**：水二局长生申、木三局亥、金四局巳、土五局申、火六局寅；阳男阴女顺、阴男阳女逆。
- **博士十二神**：自禄存起，顺逆同长生（博士/力士/青龙/小耗/将军/奏书/飞廉/喜神/病符/大耗/伏兵/官府）。
- **将前十二神**：寅午戌将星午、申子辰子、巳酉丑酉、亥卯未卯，顺行（将星/攀鞍/岁驿/息神/华盖/劫煞/灾煞/天煞/指背/咸池/月煞/亡神）。
- **岁前十二神**：年支起岁建，顺行（岁建/晦气/丧门/贯索/官符/小耗/大耗/龙德/白虎/天德/吊客/病符）。

核对（逐宫对照 iztro 字段，含顺逆两支）：
- 1990 男命 4260 盘：**四组 0 不一致**
- 1990 女命 4260 盘（阳女逆行）：**四组 0 不一致**

## 四之五、回归锚点（不依赖 node）

新增 `tests/test_ziwei_natal_anchors.py`（6 组断言，纯 Python）：
起紫微星诀原典三例（27日木三局→戌 / 13日火六局→亥 / 6日土五局→未）、
命宫身宫口诀、紫微在子时十四主星全布局、通行本十干四化、闰月上下半月折算、
四组十二神起例与顺逆（土五局长生在申、庚年阳男顺/阳女逆、博士起禄存、岁起年支、将起三合）。
运行：`python -m pytest tests/test_ziwei_natal_anchors.py -q` → 6 passed。

## 四之六、原生后端（无 node / 无 iztro 也能出盘）

新增两条可选后端开关（默认行为不变，避免影响既有治理契约）：

- `ZiweiEngine(backend="native")`：`full_chart()` 直接走 `ziwei_natal.native_raw_chart()`，
  不再 spawn node；盘面结构与 iztro 后端同构，共用同一后处理。
- `ZiweiSolarAdapter(backend="native")`：阳历 → 农历（lunar_python）→ 原生排盘；
  `backend="auto"`（默认）在检测不到 `node_modules/iztro` 或 node 时**自动退回原生**，
  不再抛 `ZiweiEngineUnavailableError` / 返回 stub。

**后端一致性验收**

| 对照 | 案例 | 结果 |
|---|---|---|
| `ZiweiEngine` iztro后端 vs native后端（`scripts/ziwei_backend_parity.py`） | 11（含闰月前/后半月、晚子时） | 命宫/身宫/五行局/十四主星/辅煞/杂曜/四组十二神/宫干/大限/生年四化 **全部一致** |
| `ZiweiSolarAdapter` iztro vs native（`scripts/ziwei_adapter_parity.py`） | 12（含闰月 2、晚子时 2） | 全部一致 |

另修一处晚子时细节：紫微安星在 timeIndex=12 时须用**次日**日数
（超当月天数回绕，`lunar_month_days()` 由 lunar_python 给出当月天数），
而三台/八座等日系星仍用当日日数——此前原生实现漏了这一步，会导致晚子盘整盘错位。

无 node 回归：`tests/test_ziwei_native_backend.py`（3 组）+ 6 组锚点 → 9 passed。

## 四之七、Golden 80 案准确率（数据集桥接口径修正后）

`python scripts/ziwei_golden_accuracy.py` →

```
Golden 案例 = 80
  逐字段全部一致（命宫/身宫/五行局/紫微星/十二宫主星）
```

语义口径见 D7：Golden 的 `birth_hour` 是时辰序号，必须换算成 24h 时钟再喂生产适配器；
`scripts/golden_replay.py` 的对应换算已修，Golden 资产本身未改。

## 四之八、一条命令复现全部准确率证据

```powershell
cd D:\shuntian
$env:PYTHONPATH='src;.'; $env:PYTHONUTF8='1'
python scripts\ziwei_accuracy_report.py 120
```

输出（2026-11-05 实测）：

```
  原典锚点（无 node）        PASS
  Golden 80 案逐字段      PASS
  原生 vs 生产适配器（13 字段）  PASS
  引擎双后端一致性            PASS
  适配器双后端一致性           PASS
  结论：全部可执行项 PASS          (exit=0)
```

缺 node/iztro 时，3/4/5 三项标 **SKIP**（显式声明"只跑了原典锚点+原生实现"），
不会把 SKIP 当 PASS。

## 四之九、亮度表外部取证（168 格逐格核对）

`python scripts/ziwei_brightness_audit.py`（数据源：`亮度表四方对照_Z39.md`，
记录 引擎/明刊捷览 · dataset 众数 · 倪师断言 · 原著命图 四方值 + 证据等级）：

```
对照表格数 = 168
证据等级分布：OK一致 73 (43.5%) / Cdataset 60 (35.7%) / B单证 35 (20.8%)
与 dataset 众数三档不一致 = 2
  太阳酉: 产品=利 dataset=dim（Z41 命图10 原著平+主流平 → 利，已登记）
  太阴酉: 产品=旺 dataset=dim（命图1 原著旺 > dataset，铁律原著优先，已登记）
与倪师断言列冲突 = 1
  太阴卯: 产品=陷 vs 倪师断言=庙（dataset=dim；Z69 四源一致=陷）→ 已裁决：原典明文=陷
```

**结论与边界**：
- 产品表 = dataset 众数 + 2 处已登记命图裁决，逐格可追溯；
- **60/168 格（35.7%）只有 dataset（iztro）单一证据**，属自证循环，
  因此"亮度准确率"的上限受限于命图转录量，不能宣称已与原著全量对齐；
- 太阴卯 一格已按原典明文裁为 **陷**（见「四之十一」），倪师断言列那条系**误摘**，
  已注销该冲突条；剩余 60 格标注「dataset 单证 / 未达双证」，不升级、不改表。

## 四之十、CodeGraph 接入（colbymchenry）与调用图取证收口

`@colbymchenry/codegraph` v1.6.2（全局 CLI，`codegraph`），本仓索引
`.codegraph/codegraph.db`（1,244 文件 / 20,696 节点 / 46,790 边）。2026-11-05 已
`codegraph sync`（同步 38 个变更文件，含本轮紫微改动）。

DSH 会话没有 MCP 挂载点（codegraph 的 `install` 支持 hermes/claude/codex/cursor 等，
不含 DSH），本会话以 **CLI 等价使用**：`codegraph callers/callees/impact/explore/sync`。
MCP 形态为 `codegraph serve --mcp`，供支持的客户端后续接入。

**对紫微改动补做调用图取证（AGENTS.md §2 第①腿）**：

| 符号 | callers | 结论 |
|---|---|---|
| `postprocess_natal_palaces` | `full_chart`(ziwei_engine) + `solar_to_chart`(ziwei_adapter) | 双入口统一后处理已接线，无第三入口 |
| `native_raw_chart` | `full_chart` native 分支 + `native_solar_chart` | 一致 |
| `native_solar_chart` | `ZiweiSolarAdapter.compute` | 一致 |
| `inject_brightness_table` | 仅 `postprocess_natal_palaces` | 单一实现，无旁路 |
| `ZiweiSolarAdapter.compute` | `pipeline_stages/compute_stage.py:123`（生产绑定） | 生产链确认 |

**取证发现并清理（D12）**：统一后处理接线后，旧方法
`ZiweiEngine._inject_tianxing_tianyao`、`ZiweiEngine._compute_doujun` 变为零调用方
孤儿代码（codegraph callers=0，全仓 grep 仅剩定义与注释），已删除并留痕注释；
清理后索引 `callers _compute_doujun` 返回 not found。回归：核心紫微 7 文件
**97 passed**。

## 四之十一、三项口径裁决（2026-11-05，按原典明文）

原典文本：`D:\顺天系统资料\豆包资料\六部经典校对版\紫薇体系\古籍文字版\紫微斗数全书_完整原文.txt`
（仓内无原典，故证据只引外部资料的原文行号，不改写）。

### 裁决一：闰月 —— 原典是「整体作次月」，不是上下半月

原文（`:714`）：

> 假如正月生子时就在寅宫安身命……**又若闰月正月生者要在二月内起安身命，
> 凡有闰月具要依此为例**。

- **裁定**：原典口径 = 闰月**整体作次月**。
- **落地**：`ziwei_natal.build_natal_chart(..., leap_mode=)` 双口径显式可切换——
  `"classic"`（原典：整体作次月）/ `"half_month"`（默认，与 iztro `fixLeap=true`、
  与数据集生成器一致：1–15 日本月、16 日起次月）。
  `native_raw_chart` / `ZiweiEngine.full_chart` 同名透传，非法值 fail-fast。
- **为什么不把生产默认改成原典口径**：数据集（ziwei-doushu）由 iztro 生成，
  Golden 80 案与 parity 脚本都以它为参照；改默认会让「准确率报告」变成两套口径互比。
  因此生产默认保持 `half_month`，原典口径作为**可验证的另一实现**存在，
  回归锚点 `tests/test_ziwei_natal_anchors.py::test_leap_month_classic_rule` 固定其行为。
- 待办：数据集侧若重录，再评估是否把默认切到 `classic`（属接线裁决，不在本轮）。

### 裁决二：太阴卯亮度 = 陷（原典明文，产品口径正确）

原文（`:2145`）：

> **太阴 庙亥子丑 旺寅酉戌 陷卯辰巳**。

- 原典把太阴卯明确列入**陷**，与产品表一致，也与 Z69 四源（=陷）一致。
- 冲突源 `倪师亮度断言库_Z38.md:9` 那条「太阴庙」是**误摘**：原文片段讲的是
  「水澄桂萼」「太阴庙在子时」，并不构成「太阴卯=庙」的断言。
- **裁定**：保留 陷；「四方对照」里的倪师断言冲突条**注销**（记误摘），
  不再作为待裁决项；产品表不改。

### 裁决三：亮度 60/168 格仅有 dataset 单证 —— 维持四档表，不升级

- 单证格（Cdataset）占 35.7%，其「证据」与被验证对象同源（iztro/dataset），属自证循环，
  不能当双证使用；`Z40` 已逐格复核过关键冲突格（太阴酉=旺、天梁申/亥=陷、
  武曲酉=利、天同卯=利/平、武曲卯与太阳酉为流派差异）。
- **裁定**：保留四档表 + 命图 2 处已登记裁决（太阳酉→利、太阴酉→旺）；
  其余单证格标注「dataset 单证 / 未达双证」，**不升级、不改表、不再宣称全量对齐**；
  `Z41` 命图锚点库列出的 18 个多图众数差异格，登记为「待命图转录补证」（下一轮做命图 OCR 再裁）。

三项裁决的落点：前两项已进代码/测试，第三项是口径边界（不改代码，改的是对外宣称）。


## 五、改动文件

| 文件 | 改动 |
|---|---|
| `src/tongshu/engines/ziwei_natal.py` | 新增：原生安星实现（真值层 + `native_raw_chart` 后端）；`leap_mode` 双闰月口径 |
| `src/tongshu/engines/ziwei_engine.py` | `postprocess_natal_palaces`、`backend` 开关、D9 流日命宫修正、`leap_mode` 透传 |
| `src/tongshu/engines/ziwei/rules/classical_detail.py` | 新增：解层经典细则（9 出口 + 49 条格局投影 + 反假命中纪律） |
| `src/tongshu/engines/ziwei_adapter.py` | 阳历路径接入统一后处理；`backend` 开关 + 无 iztro 时原生退回 |
| `src/tongshu/engines/ziwei/rules/interpretation.py` | 亮度表统一到 Z39（旧六档表作废留痕） |
| `src/tongshu/engines/ziwei/__init__.py` | 删除不存在的 `classical_detail` 死导入 |
| `package.json` | 依赖对齐 lock（修 `npm install` 必失败） |
| `scripts/ziwei_natal_verify.py` | 准确率核验脚本（13 字段） |
| `scripts/ziwei_backend_parity.py` | 引擎双后端一致性 |
| `scripts/ziwei_adapter_parity.py` | 适配器双后端一致性 |
| `scripts/ziwei_golden_accuracy.py` | Golden 80 案逐字段准确率（语义换算后） |
| `scripts/ziwei_accuracy_report.py` | 一条命令汇总全部准确率证据（含 SKIP 语义） |
| `scripts/ziwei_brightness_audit.py` | 亮度表 168 格外部取证核对（含证据等级统计） |
| `scripts/golden_replay.py` | D7：ziwei 分支时辰序号→24h 换算（EXPECTED_CHANGE 已登记） |
| `tests/test_ziwei_natal_anchors.py` | 原典锚点回归（7 组，含闰月原典口径） |
| `tests/test_ziwei_native_backend.py` | 无 node 原生后端回归（3 组） |
| `tests/test_ziwei_classical_detail.py` | 解层经典细则回归（9 组：1:1 投影/假命中防护/真值/女命/运限/空盘） |

## 六、下一步（准确率口径）

1. ~~闰月口径裁决~~（已完成：原典明文=整体作次月，`leap_mode="classic"` 可切换；
   是否切生产默认为接线裁决）。
2. ~~杂曜逐曜对差~~（已完成：38 颗全对；仍缺原典逐字核对）。
3. ~~流年层真值~~（已完成：流年命宫/流年四化/大限宫干支/大限四化 24 样本 0 不一致）。
4. ~~亮度表内部矛盾~~（已完成：统一为 Z39 四档单一来源）。
5. ~~长生十二神、博士十二神、将前/岁前十二神~~（已完成：男女顺逆各 4260 盘 0 不一致）。
6. 亮度六档：现统一为四档（庙/旺/利/陷）；得/平/弱 细分需更多命图锚点
   （Z41 的 18 个众数差异格待命图转录补证）。
7. ~~`classical_detail` 解层通道按原典重建~~（已完成：9 出口接线，反假命中纪律 + 9 组回归）。
8. ~~把 `ziwei_natal` 提升为可选原生主路径~~（已完成：`backend="native"` 可选，
   适配器 auto 模式在缺 iztro 时自动退回原生；**切换为默认后端属接线裁决**，待定）。
