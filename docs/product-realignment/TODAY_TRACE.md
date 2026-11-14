# TODAY 双向追踪（工作稿）

## 个人今日：日期、资料和时间段

- 真实页面链：`App.tsx:114` 在会话存在时进入 `RealPersonalHeluoToday`；该页调用 `fetchPersonalHeluoToday(token)`，没有传日期。`frontend-case/src/api/heluoToday.ts:17-19` 因而不带 `date` 参数；`src/tongshu/api/app.py:683` 默认采用运行后端机器的 `date.today()`。公共今日同样由 `App.tsx` 不传日期，后端 `app.py:555` 默认服务器日期。当地日期与服务器日期跨日时可能展示不同于用户所在地的“今日”；系统应以哪个地点/时区为准尚需产品裁定，实际部署时区未验证。
- 个人页面仅显示河洛流日段投影：卦名、日期区间、六爻、当前爻、上下卦和来源，页面明确写个人解释及行动建议未开放（`RealPersonalHeluoToday.tsx:66-84`）；不能把它称为多引擎判断或完整个性化指引。
- `project_heluo_today` 在日期落于某段、且爻字段有效时固定返回 `period_days=5`，未核对区间长度。用独立构造的 2026-11-10 至 2026-11-11 合成段直接调用真实函数，返回区间为两天但 `period_days` 为 5。前端仅检查该字段等于 5 和日期在区间中，随后显示每爻五日。此测试证明投影函数对异常输入没有检测，不证明真实河洛引擎当前生成过两日段；引擎规则与上游真实数据先核对，修正需另行审批。
- **真实计算样本的日期覆盖问题**：`canonical.py:467` 使用 `timeline_yun.compute_liuri`，后者 `:356-377` 按每个节起始日构造六个连续五日段。以测试凭据和允许紫微 stub 的本地 `TONGSHUPipeline.for_demo`，输入 1980-06-22 12:30、男、`CN_BEIJING`、`Asia/Shanghai`，检查一次真实 pipeline 结果中全部流日段对 2026 年每个公历日的命中数：356 日唯一、2 日重复、7 日无段；重复为 01-05、03-05，无段为 04-04、06-04、07-05、07-06、08-06、09-06、10-07。`project_heluo_today` 在非唯一时返回 None，接口代码将其转为 422 `HELUO_DAY_UNAVAILABLE`；这次试验直接测的是 pipeline 输出与投影判定，并非对以上每一天逐个发 HTTP 请求。结果只适用于此工作区和此样本，不代表全部命盘或线上状态；涉及节气边界/传统口径的修复须先核验依据，不能简单填补或压平重叠。
- 接口级补证：使用同一合成档案、内存 ProfileStore、测试身份以及真实本机计算管线，通过 FastAPI TestClient 请求 `/v1/personal/heluo-today`，2026-08-06 返回 422 `HELUO_DAY_UNAVAILABLE`，2026-08-17 返回 200。测试不访问真实账户或真实数据库；其余缺失/重复日期尚未逐个发请求。
- 两套河洛实现的差异：远端主线 `1925adf0` 的独立包 `src/heluo_engine/engines/heluo/timeline_yun.py:488-611` 在同时提供本节与下节时刻时有 H10b 实际节气间隔对齐；其 `canonical.py:145-147` 和主线 README 的 H10b 段也说明此口径。当前工作区平台走的是 `src/tongshu/engines/heluo/canonical.py` → 同目录 `timeline_yun.py` 的另一实现，不应将独立包能力当作平台当前已接入。两者数据结构、边界时刻及传统依据需逐项比较，不能直接移植或据源码差异断言主线能修复所有日期问题。
- 证据边界：`tests/test_personal_profile_to_heluo_flow.py` 使用真实 pipeline 与内存档案、假邮件验证，提供明确日期并验证同一进程中两个账户互不读取；`frontend-case/src/test/accountJourney.test.tsx` 使用 mock 登录、存档和个人今日。两者均不覆盖跨时区默认日期或真实 SMTP/数据库。
- 本轮复跑 `PYTHONPATH=src python -m pytest tests/test_personal_heluo_today_api.py tests/test_personal_profile_to_heluo_flow.py -q -p no:cacheprovider`：6 passed、2 条依赖弃用警告；测试使用内存档案且未覆盖上述全年区间缺口。

## 工作区公开首页

`frontend-case/src/App.tsx:80` → `src/api/today.ts` GET `/v1/today?region=Beijing` → `src/tongshu/api/app.py:548` `today` → `:501` `_today_card` → `:518` `_computed_ganzhi` 与 `:523` `pipeline.huangli_engine.get_day(ad)` → `frontend-case/src/view-models/publicToday.ts` → `RealPublicToday.tsx`。`today` 默认 `date.today()` 是服务端日期；页面标识公共历法。`_today_card` 另有 `TODAY_MOCK` 来源字段，不能笼统称全部响应均为实时生成。

该公开路径在所追踪范围内没有调用 `pipeline.run()`；`compute_stage.py:236` 的 Judgment 拼装不能因此被认定为该页面已消费。LifeGuidance、映射批准、卡片→判断→证据链 **未验证**。返回数据与视图字段逐项来源仍待核验。

### 已追踪的公开字段

| 页面字段 | 前端转换 | 后端来源 | 限度 |
|---|---|---|---|
| 日期及历法年/月/日 | `publicToday.ts:63-70` 取 `calendar.solar_date`、`*_ganzhi` | `_today_card` 的 `huangli_engine.get_day(ad).to_dict()` | 服务端 `date.today()`；未建立跨时区 TODAY 契约。 |
| 今日卦/上卦/下卦 | `:57-60,85-89` 取 `calendar.daily_hexagram` | `huangli_engine.py:330,367-371` 调 `_ganzhi_daily_hexagram` | 这是黄历路径字段，不能称个人河洛判断或已验证生活指引。 |
| 年/月/日柱列表 | `:92` 取 `resp.ganZhi` | `app.py:488-498` 调 `pipeline.bazi_engine.compute`，固定中午与 `gender="male"` | 该路径输出的是公共三柱，不是用户出生八字；中午、性别对输出的影响与边界尚需单独验证。 |
| 宜/忌 | `:90-91` 取顶层 `yi/ji`，非数组时转空数组 | `app.py:523-528` 取黄历对象字段 | 数据来源和具体可公开语义是否符合生活指引要求未验收；缺字段在前端与空列表表现相同，需评估契约。 |
| 节气/建除/冲煞/纳音 | `:72-81` 从 `calendar` 取非空字段 | `HuangliDay.to_dict()` | 空值被省略；逐字段准确性未审计。 |
| 判断/行动/来源说明 | 此公开页面未见对应 LifeGuidance 字段渲染 | 当前链路未证明 | 缺失或未接线，不能将静态界面说明视为证据链。 |

`tests/test_v1_today_contract.py:37-95` 对 `TestClient(create_app())` 的游客响应作字段及无 personal 断言，本轮 6 passed。该测试使用当前实际文件状态；`web/data/today.json` 当前不存在，但 `app.py:481-508` 在文件存在时会将其选中条目复制到响应后再覆盖部分字段。故“当前测试无 mock 编辑字段”不能外推为“任何部署提供该文件时都不会返回 mock 编辑字段”；前端 `publicToday.ts` 目前未消费提案列出的顶层 theme/reasoning 字段。该配置差异应在隔离环境进一步验证，不在 Phase 0 修改。

**条件性风险已复现（2026-11-14，开发工作区）**：在 Python `TemporaryDirectory` 建立 `web/data/today.json`，内容为 `{"default":{"theme":"TEST_MARKER","reasoning":"TEST_MARKER"}}`；将 `TONGSHUPipeline.for_demo` 替换为含真实 `BaziEngine()`、`HuangliEngine()` 的简单对象，以临时根目录调用真实 `create_app`/`TestClient` 并 GET `/v1/today`。结果 HTTP 200，顶层 `theme` 与 `reasoning` 均等于标记。此测试隔离了资源构建并替换 pipeline 工厂，证实 `_today_card` 路由在该文件存在时的复制行为，不证明线上已部署该文件，也不证明当前 React 页面消费这些字段。数据文件/默认根目录的内容差异使 `test_v1_today_contract.py:85-90` 在当前无文件环境为绿，不能证明有文件条件也为绿。未改生产代码、测试期望或实际数据文件。

开发工作区另一条计算路径：`TONGSHUPipeline.for_demo()` 在 `pipeline.py:260-261,289` 构造并传入 `JudgmentClaimComposer`；`pipeline.run():382` 传给 `ComputeStage`；`compute_stage.py:241-249` 在 composer 非空时调用 `run_ziping_judgment` 并生成 claims，异常被捕获记录。注意相邻注释提及默认 OFF，但实际构造与传参需要以运行绑定为准，不能只引注释。`tests/test_ziping_bridge.py:31-34,51-80` 测试直接用 `BaziEngine` 构造 chart 后调用 bridge；`test_int_05_judgment_claim_composer.py:22-35` 的部分测试使用 mock resolver 和假判断对象。两文件本轮共 25 passed，覆盖各自测试对象，并不证明公开 TODAY 消费这些判断。

## 工作区个人路径

`App.tsx` session → `RealPersonalHeluoToday.tsx` → `/v1/personal/heluo-today` (`app.py:666`) → `pipeline.run` (`:688`) → `compute_stage.py`（BaziAdapter、ZiweiAdapter、河洛路径）→ `heluo_today.py` 时间段投影。真实 DB/SMTP 未验收；组件 mock 与服务内存存储测试不等于生产数据库验证。时间规则及与其他入口一致性未完成三重取证。

工作区 `/v1/calculate` 已通过内存身份服务及真实 pipeline 包装观察验证：时区遗漏的悉尼合成输入与显式时区输入均为 HTTP 200，但 pipeline chart 日柱不同；一次请求日志同时出现盲派 `actor_dim` 未绑定并降级。该实验不是个人 TODAY 端到端证明，详见 `CURRENT_ARCHITECTURE_AUDIT.md`。

`/v1/profile/stored` 将 `state.timezone` 写入档案（`app.py:630-648`）；与之不同，计算接口及本机 QA 的 `_gate_personal` 仅校验，后续传入原始 `req.timezone`。QA 路径在遗漏时区时已实测命中默认北京/分钟 30 的风险，详见 `CURRENT_ARCHITECTURE_AUDIT.md`；不能以档案路径的正确派生证明所有计算接口都正确。

## 主线

远端 `origin/main@1925adf0` 无当前工作区的 `frontend-case` 和 `src/tongshu/api/app.py`；以上调用链不得归因于主线。非测试、非 archive 的 Python FastAPI/APIRouter/uvicorn 静态检索未找到对应产品入口，但不排除其他语言、入口形式或外部部署。主线在平台模块不存在时有意忽略 `tests/cross_repo`；仅显式指定其中旧文件才复现缺失导入，不能将这些未运行的守卫视为页面到引擎的集成通过，也不能误报常规收集必定失败。完整证据见架构审计。
