# 当前架构审计（工作稿）

## 补充：禄命法入口与测试对象

- 在当前工作区，`src/tongshu/luming/engine.py:2626,2694` 提供 `from_bazi_chart` 和 `LumingEngine.compute`；对仓库 Python 源码检索 `LumingEngine` 构造及 `tongshu.luming` 的显式导入，命中独立引擎和测试，未发现 `src/tongshu` 平台生产调用方。动态导入和外部调用尚未穷尽，因此不能认定所有部署路径均未接入。
- 已核对当前平台主要链：`app.py` 的个人计算入口 → `pipeline.py` → `pipeline_stages/compute_stage.py:123-250`，该 stage 调用八字/紫微 adapter、黄历、河洛、盲派以及有条件的子平 bridge；未见禄命法调用。公共 TODAY 另走 `app.py:_today_card`，亦不能由引擎包存在推断调用禄命法。
- 本轮 `PYTHONPATH=src python -m pytest tests/test_luming_engine.py tests/test_luming_query_year.py tests/test_luming_mapping.py -q -p no:cacheprovider`：109 passed。测试直接导入 `tongshu.luming.engine` 的引擎/函数，覆盖独立模块，不是对平台 API、前端接线或算法整体准确率的验收。第一次未设置 `PYTHONPATH` 时在测试初始化阶段因找不到 `tongshu` 退出；设置项目源码路径后重跑成功。

## 补充：当前工作区平台引擎与测试边界

以下是 `app.py:227,370-404,460-466,666-688` 的个人计算链路证据，**不适用于独立的公共 TODAY 路径，也不等于线上状态**：`TONGSHUPipeline.for_demo` → `pipeline.py:373` → `ComputeStage.run`。

| 模块 | 实际绑定和入口 | 测试对象与局限 |
|---|---|---|
| 八字 | `compute_stage.py:98-100,137-165` 的 `BaziAdapter` 使用 pipeline 注入的 `BaziEngine`；有上下文和缺省上下文两条分支 | B02 和算法测试曾在此工作区运行；晚子时规则冲突及缺省上下文问题另见本报告，不能直接认定规则获批准 |
| 紫微 | `compute_stage.py:100,145,165` 的 `ZiweiAdapter` 使用注入的 `ZiweiEngine` | 已查 B02 测试显式允许 stub；冻结的 canonical 依据及真实服务运行未验收 |
| 黄历 | `compute_stage.py:168` 的 `HuangliEngine.get_day`；公共 TODAY 另在 `app.py:523` 直接调用同类引擎 | 工作区 `tests/test_huangli_engine.py` 直接构造该类；本轮与 B01 合计 10 passed，不等于宜忌权威样本验证 |
| 河洛 / 易 | `compute_stage.py:184,319-375` 调用 `HeluoCanonical.calculate`，再经 `YiAdapter` 与 `YiInterpretationEngine`；与某些测试使用的 `HeluoAdapter.compute` 不应混称同一入口 | `tests/test_b01_heluo_yi_passthrough.py` 两项实际执行 `pipeline.run(compute_only=True)` 并断言河洛与易结果；其中序列化辅助函数是测试内的复制逻辑，并非直接调用 API，且允许紫微 stub。本轮该文件与黄历测试合计 10 passed |
| 盲派 | `compute_stage.py:200,399-451` 懒加载 `BlindBaziEngine.compute_from_chart`，失败可降级 | `tests/test_blind_integration_bazi.py` 直接使用 `BlindBaziEngine.compute` 和单独八字引擎，非对实际 stage 中的 `compute_from_chart` 降级行为全覆盖；此前单独复现的异常见下文 |
| 子平 | `compute_stage.py:240-250` 仅在 `judgment_composer` 存在时调用 `run_ziping_judgment`；`for_demo` 的具体注入与 bridge 测试见 TODAY 追踪 | 有条件调用及异常降级，不代表每个请求都有子平判断，也不代表公共 TODAY 使用该判断 |
| 禄命 | 已检查的上述 stage 未见接入，独立入口见上一节 | 独立测试通过不能证明平台或页面接线 |

## 补充：出生地别名的歧义风险

- 当前工作区 `src/tongshu/engines/time/location_registry.py:61-74` 将 ID、中文名和别名写入同一字典，重名时后者覆盖前者；`src/tongshu/api/profile.py:151-165` 通过该查找结果校验并可推导时区。实读当前地点表，发现 15 个别名对应的条目具有不同的时区或坐标；这包括细微坐标差异，并不等同于 15 个不同城市错误。
- 可复现例子：`Hamilton` 同时对应百慕大 `BM_HAMILTON` 和新西兰 `NZ_HAMILTON`，当前 `TimeResolver.lookup('Hamilton')` 选择后者；`圣地亚哥` 同时对应美国 `US_SAN_DIEGO` 和多米尼加 `DO_SANTIAGO_DE_LOS_CABALLEROS`，当前选择后者。使用 `resolve_profile` 传入 `Hamilton`、无时区、solar 和 male，实际返回 `VALID` 与 `Pacific/Auckland`。仅此证实底层解析和校验结果，尚未证明用户曾受到影响。
- 存档和个人河洛入口分别在 `src/tongshu/api/app.py:634-637,679-681` 检查歧义；`/v1/calculate`、`/v1/daily-guide` 和本机 QA 经 `_gate_personal` → `resolve_profile` 的代码路径未见同样的歧义检查。是否可由正式前端提交这些同名自由文本、实际线上地点表及线上影响均未验证；接口端风险为条件性 P0。应以明确城市 ID 贯穿请求并在所有入口统一处理歧义，具体改法留待审批。

审计时间：2026-11-14。状态：**未完成**；本目录记录取证，不表示 Gate A 已通过。

## 版本边界

- 远端 `origin/main` 经 `git fetch origin main` 核实为 `1925adf0e796e7346960c4cc2ed7f1af12449355`；只读核对目录 `D:/liorin-product-audit-main`。`git ls-tree -r --name-only FETCH_HEAD` 未发现前端 `package.json` 或 `src/tongshu/api/app.py`。不得把下述开发工作区的页面和 API 当成主线已有。
- 开发工作区 `D:/shuntian` 为 `feature/luming-engine`，HEAD `5255c2b7`，包含大量已修改及未跟踪文件。`git rev-list --left-right --count FETCH_HEAD...HEAD` 输出 `1498 159`；未执行合并、切换或清理。
- 2026-11-14 `git ls-remote --heads origin` 核实远端分支：`main=1925adf0`、`feature/bazi-engine=4d124ee2`、`feature/blind-engine-migration=809e397c`、`feature/heluo-engine-package-20261011=a1ddd7d3`、`feature/huangli-engine=640ed958`、`feature/luming-engine=9cea1612`、`feature/ziping=2c576a93`、`feature/ziwei-engine-migration=e1277ad7`、`codex/ziping-runtime-contract-repair=2c914e40`、`fix/bazi-julian-caliber-20261022=6fe1326d`。这些是分支指针，不证明功能已合并；各分支差异/依赖需逐一审计。工作区相对其本地远端跟踪分支显示 ahead 99 / behind 47。`stash@{0}` 存在，内容与归属未在本轮裁定，未移动或删除。
- 本机资料：`D:/顺天系统资料/V2版本手册/V2新架构和引擎规范.txt` 自称 V2.0-FINAL、ACTIVE；`D:/顺天系统资料/V2版本手册/前端开发手册.txt` 自称 V3.0；`D:/顺天系统资料/开发资料/参考资料/词库V4.0/参考词库综合版本.md` 存在。三者授权副本与批准状态 **未验证**，不能以文件存在代替权威确认。
- 三份本地文件 SHA-256 依次为 `EEB6DA40272DB01571E0556958BC0DD8B0541C2310504DE7712AB3DD0E78E2CA`、`EF807DBB89762FC679B4A370F729C66B5CFA7BDA224F4F3986AAE219E2C12DEA`、`D5EB7CAD5203C58522306F85A7F6EB8DCC21D3129EBE0653ECACA054517EAFE2`；哈希用于标识读到的副本，不代表批准。

## 主线引擎抽查

2026-11-14 对隔离的 `origin/main@1925adf0` 执行额外入口搜索：全树 Python 文件名查找 `app.py`、`pipeline.py`、`compute_stage.py`、`production_entry.py`，仅找到 `engines/production_entry.py`；对非测试、非 archive 的 Python 搜索 FastAPI、APIRouter、路由装饰器和 `uvicorn.run` 未命中。这是有范围的静态检索，不排除不同文件名、其他语言或外部部署入口，不能据此断言任何线上系统不存在。

主线 `tests/cross_repo/test_heluo_context.py:8` 导入 `tongshu.engines.heluo.canonical`，而该主线没有该包；在隔离工作树显式指定文件并运行 `PYTHONPATH=src python -m pytest tests/cross_repo/test_heluo_context.py --collect-only -q -p no:cacheprovider`，实测 **0 项收集、1 个导入错误**（`No module named 'tongshu.engines.heluo'`）。进一步核对发现这是独立包预期隔离边界：`tests/cross_repo/conftest.py:34-42` 在找不到 `tongshu.pipeline` 时以 `collect_ignore_glob` 排除目录；直接对整个目录运行 collect-only 实测 0 项收集，退出码 5，无导入报错。显式指定单文件绕开了目录忽略，不能称普通主线测试必然因该文件报错，也不代表全部 cross_repo 测试均失败。它说明这里没有运行这些跨仓接线守卫，不能将其误称产品路径已接通。独立包 `tests/heluo/test_heluo_public_api.py` 测的是不同对象。

同一主线另运行 `PYTHONPATH=src python -m pytest tests/heluo/test_heluo_liuri_calendar.py tests/heluo/test_heluo_public_api.py -q -p no:cacheprovider`，**47 passed、29 subtests passed**。前者测试 `heluo_engine.adapter.HeluoAdapter` 及独立包节气窗口，后者侧重导出、签名与资源解析；这证明所选独立包测试通过，不证明旧平台路径或当前前端个人今日接口已修好。

| 模块 | 状态 | 证据及边界 |
|---|---|---|
| 河洛独立包 | 部分实现 | `src/heluo_engine/adapter.py:151,192,204,277` 有独立、context、chart 三入口及 canonical 调用；主线 `tests/heluo/test_heluo_degradation_contracts.py` 测试 `heluo_engine.adapter.HeluoAdapter` 等独立包对象，19 passed、19 subtests passed；是否已接入最终产品 **未验证**。 |
| 黄历 | 部分实现 | `src/tongshu/engines/huangli_engine.py:276,297` 为引擎与按日接口。主线抽样 `pytest tests/test_heluo_canonical.py tests/test_huangli_engine.py -q -p no:cacheprovider`：20 passed；不是全引擎或准确性验收。 |
| 子平 | 部分实现 | 主线 `engines/production_entry.py:157` 提供 `production_entry`；`tests/evaluate_by_book.py:17,232` 和 `tests/test_production_gate_golden.py:6-61` 有引用，后者在导入阶段执行断言但未定义 pytest 测试项，单独计数时不可误算进上述 19 个测试；产品调用方仍未核实。开发工作区另有 `compute_stage.py:241-249` → `ziping_bridge.py:509,556-569` → `engines/production_entry.py:188`，仅表示可达路径，条件与运行配置需分别核验。 |
| 紫微 / 盲派 / 其他 | 未验证 | 主线生产入口、绑定和覆盖仍需三重取证，不根据文件存在判生产接入。 |
| 统一生活指引 | 未验证 | 未在主线确认完整 LifeGuidance → Judgment → Evidence → Engine 生产链。不得把搜索未命中当全局不存在。 |

开发工作区 `src/tongshu/pipeline.py:317` → `pipeline_stages/compute_stage.py:123,142,145,184` 有算例编排，具体部署与主线合并状态未验证。冻结规则、Golden 和数据库不得改动。

## 时间规则冲突（P0，待裁决）

当前 `AGENTS.md:42` 写 23:00 真太阳时后日柱换次日；但工作区 `src/tongshu/engines/bazi_adapter.py:7,41-46` 及 `src/tongshu/engines/time/resolver.py:154` 写 23:00 换时不换日、00:00 换日，`LIORIN_FRONTEND_SPEC_V2.md:210` 亦记录后一规则。用户此前明确要求后一规则。两种表述不能同时作为当前统一事实；本轮不修改规则或冻结资产，需对主线及各入口做边界运行和测试对象核验后，由 Bazi owner 与用户裁定。

2026-11-14 工作区执行 `pytest tests/test_b02_late_zi_golden.py tests/test_algorithm_verification.py -q -p no:cacheprovider`：32 passed、27 subtests passed。`test_b02_late_zi_golden.py:30-54,107-117` 实际构造 `TimeResolver`、`BaziAdapter(BaziEngine())`，断言真太阳时 23:19 的日柱仍为当天；同文件 `:25` 允许紫微 stub，不能把紫微测试当生产紫微证明。`AGENTS.md` 所列 `test_2330_bazi_next_day` 在当前 `tests`/`src/tongshu` 搜索未命中；该文件现有测试名为 `test_2330_bazi_same_day`。这些证据只描述当前工作区，不裁定主线或所有入口。

## P0：时区派生没有贯通到计算（工作区本机 QA 实测）

`src/tongshu/api/profile.py:151-165` 在未传时区时按地点派生；`app.py:231-245` 调用该函数并检查状态，但没有返回派生状态；QA 路由 `app.py:459-472` 原样传 `req.timezone`；`pipeline.py:348-356` 只有时区和地点均非空才创建 context；否则 `compute_stage.py:146-163` 以北京、`Asia/Shanghai`、分钟 30 构造默认 context。`/v1/calculate` 和 `/v1/daily-guide` 在 `app.py:376-386,402-413` 也有相同的原值传递形态；前者已通过下述内存身份服务复现，后者及真实认证环境和线上均未复现。

真实本机 QA 路由复现（非 mock pipeline；临时合成输入，无真实用户数据）：出生 `1984-12-07 00:05`、男、`AU_SYDNEY`、分析日 `2026-11-14`，分别不传 timezone 与显式 `Australia/Sydney`，两次 HTTP 200，前者日柱 `乙亥`，后者 `甲戌`。只有 timezone 字段不同；该差异证明此路径遗漏时区时存在错误事实源风险，不证明哪组命理结论在其他条件下必然正确。页面目前选城市时通常会填时区，但 API 允许遗漏，不能把 UI 默认行为当 API 保证。QA 为 `compute_only`，不代表正式判断验收。保留计算原始输出/基线，本阶段不修算法、不改断言。

测试对象核对：`tests/test_profile_gate.py:211-221` 只验证 `resolve_profile` 产生派生时区；`:419-424` 对 `/v1/daily-guide` 的“仅地点”北京样本仅断言 HTTP 200，不检查实际传入 pipeline 的时区/地点/分钟。本轮单独运行后者为 1 passed，不能据此证明悉尼或其他非北京数据正确贯通；建议审批后新增跨地区、零时边界与参数传播测试，不替换或削弱现有断言。

**进一步验证 `/v1/calculate`**：在隔离的 FastAPI `TestClient` 使用测试用内存 `FakeDB`、强制认证和测试签发令牌；保留真实 `TONGSHUPipeline.run` 并仅用包装器记录实际入参与返回 chart。同一悉尼合成输入，不传时区及显式传 `Australia/Sydney` 均 HTTP 200；前者实传 `(timezone=None, location=AU_SYDNEY, minute=5)`、日柱乙亥，后者实传正确时区、日柱甲戌。测试未连接真实身份库或线上服务，能证明当前工作区受认证路由与 pipeline 的条件性问题，不能证明线上部署状态。`daily-guide` 尚未用同样方式复现。

## 盲派计算降级（工作区合成样本，P0 待审）

上述受认证计算的日志有一次 `Blind integration failed ... UnboundLocalError`，接口仍返回 HTTP 200。入口链为 `/v1/calculate` → `pipeline.run` → `compute_stage.py:200,399-433` → `BlindBaziEngine.compute_from_chart`；失败在 `_compute_blind` 捕获后返回三个 `None`。用同一回退上下文（1984-12-07 00:30、北京、男）独立调用 `TimeResolver` → `BaziAdapter(BaziEngine())` → `BlindBaziEngine.compute_from_chart`，复现 `blind_bazi_engine.py:813 → :1766` 的 `actor_dim` 未绑定异常。该样本用于暴露程序路径，不作为单一案例推导命理规则，也不表示所有盘均失败；主线与线上未验证。

测试对象核对：工作区 `tests/test_blind_integration_bazi.py` 使用 `BlindBaziEngine`（`:21,36,114`），本轮 8 passed、4 subtests passed；其通过不覆盖或否定上面的特定触发路径。后续应先定位所有 actor 赋值分支、补多个正反及路径覆盖、查明降级状态如何对外暴露，再按独立任务审核，Phase 0 不改规则和断言。

进一步静态线索：`blind_bazi_engine.py:1132-1139` 的 `actor_dim` 在前面的体用循环内赋值，而 `:1766`（食伤泄秀）及 `:1790`（势做功）在后续分支引用；若前一循环执行过，它们可能读取此前迭代留下的值。**是否在某些输入下造成错误归因尚未运行验证**，不能把这一推测当作已证实错误；必须用多路径独立测试和原典/判据复核后裁定。

## P0：个人计算端点认证开关的默认宽松行为

工作区 `src/tongshu/api/deps.py:63-73,213-235` 在 `TONGSHU_AUTH_ENFORCED` 未设置时默认为 false，`get_current_user` 对未登录调用返回匿名用户；`app.py:392-404` 的 `/v1/calculate` 使用该依赖。`tests/auth/test_b09_route_enforcement.py:307-358` 明确把宽松模式下旧端点 200 作为现有迁移行为，不能把它误说成“所有配置均严格认证”。

2026-11-14 以 `TestClient(create_app())`、内存 FakeDB、真实计算管线和合成请求验证：无 Authorization 时，显式 flag `0` 返回 200 且 `X-Auth-Would-Deny: 1`；显式 flag `1` 返回 401。该测试说明个人计算功能在宽松模式对未登录请求开放；**并未证明读取了其他用户档案或发生数据泄漏**。本机 QA 明确主动设为 `0`（`tools/local_engine_qa.py:32`），正式部署环境的开关、网关和隔离策略均未验证，不能外推线上暴露。档案持久化端点另有用户身份检查（`app.py:615-626`），不应把两类端点混同。Phase 0 不修改权限配置或代码。
