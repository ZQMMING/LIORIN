# AGENTS.md · V2 — 治理总纲（全栈接手版）

> 生效日期：2026-11-11
> 取代：`AGENTS.md`（V1，baseline-v1.4-interim-20260823）。V1 归档保留，但**事实性内容以本文档为准**；冲突时按本文档裁决。
> 定位：Claude 接手**全栈开发**（后端引擎 + API + 前端）时的治理宪法与接手说明书。
> 读者：Claude（开发执行者）与 User（裁定者）。

> 接手提示：根目录 `AGENTS.md` 可能仍保留旧口径。执行时先读取实际适用的指令；若文件之间冲突，以用户最新明确裁决及更高优先级指令为准，不要自行扩大冻结资产变更权限。晚子时最新裁决见 §3.6。

---

## 0. V1 失效声明（为什么重写）

V1 是"多 Agent 编排"时代的产物，与现实脱节：

| V1 内容 | 现状 | 处置 |
|---|---|---|
| 四角色提交链（OpenCode→Claude→Hermes→User） | 当前仅 User + Claude 两方；Hermes/OpenCode 编排线未在运行 | 推倒，改为两角色模型（§1） |
| 权威指针 `docs/audit/step0_baseline/GOLDEN_BASELINE.md`、`REVIEW_BATCH1/2`、`DECISION_LOG_C14_ADDENDUM` | **文件在工作树中不存在** | 指针失效；历史基线数字（LOADED 20 / PASSED 7 / FAILED 13 等）不得再引用为当前事实 |
| Golden 路径 `backend/dataset/golden_v1/`、`backend/dataset/accuracy/` | `backend\` 是空壳，无代码无 dataset | 修正为真实路径（§3.1） |
| 晚子时规则"已锚定"（`test_2330_bazi_next_day`） | 该测试**全仓不存在**；现行代码用 0:00 日界；`test_b02_late_zi_golden.py` 断言相反口径且通过 | 用户已裁决为 23:00 换时不换日、00:00 换日（§3.6） |
| 生产入口链描述（app.py 路由等） | 仍大体正确 | 收编进 §2 |

V1 中**继续有效**的纪律：三重取证（§4）、红线（§5）、编码规范（§5.4）。这些不是编排流程，是防事故条款，全部保留。

---

## 1. 角色与权限（两角色模型）

| 角色 | 职责 | 可做 | 不可做 |
|------|------|------|--------|
| **User** | 最终裁定权 | 批准/驳回任务、终裁冲突（晚子时裁决见 §3.6）、授权越界操作、解除冻结、定优先级 | — |
| **Claude（全栈）** | 开发 + 执行 + 自审 | 按任务写前后端代码/测试、feature 分支原子 commit、起草契约文档、跑回归并如实报告 | 直接改 master/main（合并须 User 批准）、改 Golden 期望值、降级测试断言、动冻结资产、`git add -A`/`git add .` |

**提交链**：Claude 执行 → 自审（跑分域回归 + golden_replay）→ User 终裁合并。

**变更本文件**：任何修订须 User 明示批准，并在此处登记日期与理由。

---

## 2. 真实架构地图（唯一权威路径表）

> ⚠️ 本表是**当前事实**。凡与旧文档（README.md、CONTEXT_SNAPSHOT.md、V1 AGENTS.md）冲突，以本表为准。

### 2.1 代码实体

| 实体 | 路径 | 说明 |
|---|---|---|
| 生产后端包 | `src\tongshu\` | FastAPI + Pydantic v2 + uvicorn + psycopg2。引擎、API、管线、DB 全在此包 |
| API 入口 | `src\tongshu\api\app.py` | `create_app()` factory；路由见 §2.3 |
| 启动脚本 | `run_server.py`（根目录） | `PYTHONPATH=src python run_server.py`；默认仅本地 127.0.0.1:8000 |
| 管线 | `src\tongshu\pipeline.py` → `pipeline_stages\{compute,validation,render,audit_composer}_stage.py` | 算→辨→解 生产链 |
| 包内引擎 | `src\tongshu\engines\` | bazi(+adapter)、blind(~20 文件)、ziwei、heluo、huangli、liuyao(+najia)、meihua、time_resolver |
| **子平引擎（p0 线）** | `engines\`（**根目录**，与包内 engines 是**两个不同实体**） | `production_entry.py` 是唯一生产入口；V7.207；经 `src\tongshu\reasoning\ziping_bridge.py` 消费 |
| 子平规则层 | `engines\common\`（200+ 文件） | 2026-11 高频改动区（yongyao_resolve / ge_jie_layer / special_pattern 等） |
| 子平切片规范线 | `p0_v2\` | 六部经典 MD 文库 + 切片技能 + 判据 py。**规范+核验线，非运行时** |
| 前端工程 | `frontend-case\` | React 18 + TS + Vite 6。**纯 mock，零 HTTP 调用**（详见 LIORIN_FRONTEND_SPEC_V2.md） |
| 前端静态原型 | `frontend\` | hetu-luoshu.html / liorin-v3.html / DESIGN_SPEC.md。原型参考，非生产 |
| 测试 | `tests\`（358 个文件） | 根层 263 + 子目录；分域跑批口径见 §2.4 |
| Golden | `cases\golden\`、`cases\truth\`、`cases\baselines\` | 见 §3.1 |
| DB 代码 | `src\tongshu\db\` | config / auth_db / dao / init_auth / kb_reader / migrate / seed |

### 2.2 非代码实体（勿当生产）

| 路径 | 实质 |
|---|---|
| `backend\` | **空壳**。只有 `backend\audit\audit_log.jsonl`（审计流水，活跃）和 `backend\backend\data\`（知识数据）。**无 app.py、无 src、无 tests、无 .venv** |
| `ziping-p0\` | 嵌套的**旧项目完整副本**（10 月产物）。历史工作区，禁止当生产、禁止在其内改代码 |
| `p0_8_10\` | 断言管线验证报告堆 |
| `phase0\` | 守门脚本（canonical_gate / import 边界 / contract validator）——治理工具 |
| `GPT\` | 空目录。"GPT 在途子系统"指 `engines\common\` 三文件（ge_jie_layer/special_pattern/bingyao_layer）里的另一协作线改动，**已于 2026-11-11 `e01fb1eb` 整体合线** |
| 根目录 `_*.txt` / `_*json` / 乱码文件名 md | 探针/临时产物与规范文档混放；`盲派*.md`、`ARCHITECTURE_V*.md` 为历史文档 |
| `CONTEXT_SNAPSHOT.md` | **过时**（写于 2026-08-28，指向 `D:\today` 旧路径与已废弃的 assertion V11 架构） |

### 2.3 API 端点面（GET /docs 可复核）

| 端点 | 状态 |
|---|---|
| `GET /health` | ✓ |
| `POST /v1/daily-guide`、`POST /v1/calculate`、`GET /v1/today`、`POST /v1/profile` | ✓ 主面 |
| `/v1/auth/*`（register/login/refresh/logout/me） | 装配 db_ops 才可用；否则 **503** |
| `/api/reading`、`/api/today` | **DEPRECATED**（Sunset 2027-08-18），禁止新前端消费 |
| `/nfc/daily`、`/nfc/relationship`、`/nfc/state` | **冻结 501，禁止修复** |

注意：`GET /v1/today` 的 `provenance` 里 greeting/monthLabel/theme/catalyst/dimensions/time_window/**hexagram/reasoning/cross_validation** 显式标注 `mock_until_profile_gate_or_content_module`——**后端今日卡自身也有 mock 字段**，联调时不得当真数据展示。

### 2.4 测试分域口径

全树跑批存在测试隔离污染（blind setUpClass 被前置测试污染，属已知问题）。**可比口径 = 分域跑**：

```
cd D:\shuntian
$env:PYTHONPATH="src"
python -m pytest tests/ -k ziping     # 子平
python -m pytest tests/ -k ziwei      # 紫微
python -m pytest tests/ -k blind      # 盲派
python -m pytest tests/ -k "heluo or meihua"
python -m pytest tests/ -k huangli
```

最新全树快照（Round 27，2026-11-10）：**5434 passed / 135 failed / 92 errors**，失败由 GPT 在途子系统（已合线，待重跑确认）主导。数字引用必须带日期与口径。

---

## 3. 冻结与悬案清单

### 3.1 Golden Dataset（受保护，禁改期望值）

真实路径：`cases\golden\`（ziping/ziwei/huangli/meihua/yijing/blind 各 golden_set + ground_truth_frozen）、`cases\truth\`（盲派真值/事件、河洛）、`cases\baselines\`（golden_replay_baseline 等）、`dataset\golden_v1\`、`dataset\accuracy\`。

- 禁止修改 YAML/JSON 期望值"凑绿"；新增 case 须 test-first 独立 commit。
- 失败案例逐条登记，禁止降级断言（`assertEqual`→`assertGreaterEqual` 类）。
- 回放命令：`python scripts/golden_replay.py --check`（六引擎全 [OK] 为放行门）。

### 3.2 紫微 Canonical — **BLOCKED**

书目/Passage Registry/流派/四化/时间规则无正式冻结记录；iztro stub 仅在 `TONGSHU_ALLOW_ZIWEI_STUB=1` 下可运行；禁止补算法/星曜/四化。紫微生产已切 native（默认）。

### 3.3 NFC 三端点 — 下线 (501)

保留路由注册；禁止修复 `write_snapshot`/`calculate`。

### 3.4 DB 双库 — 现状冻结

- `otcg`（运行时，28 表）与 `shuntian_kb`（知识库，115 表）并存；`config.py`：`DEFAULT_DSN = .../otcg`，`DEFAULT_KB_DSN = .../shuntian_kb`；环境变量 `OTC_G_DATABASE_URL` / `SHUNTIAN_KB_DATABASE_URL`。
- 禁止跨库连接混用；禁止未授权写 DB（migration/seed/补数据）。
- otcg 基线行数（rules=55 active30/draft15/validated10、evidence=52、mappings=10）为冻结口径，精确等值断言不得降级为 `>=`。

### 3.5 梅花 — 用户叫停

不接线、不开发。

### 3.6 晚子时换日 — 用户已裁决（2026-11-11）

- **23:00–23:59 换时柱、不换日柱；00:00 起换日柱**。晚子时时干按次日日干起；00:00 至 00:59 仍属子时。
- 用于判断的时间由 TimeResolver 按配置处理；默认真太阳时路径应以转换后的有效时间判断，不得把钟表时间误认为真太阳时。
- 正常排盘链与直接调用已统一；测试提交 `6021eaf6`，修复提交 `45e2653b`。边界回归 `tests/test_bazi_midnight_policy.py` 与 `tests/test_b02_late_zi_golden.py` 共 10 项通过。
- 旧版“23:00 换日”表述不再作为执行依据；不擅自改动受保护的 Golden 期望值。后续更改此口径须用户明确裁决。

### 3.7 引擎接线现状（接手时基线）

紫微（native 默认）/ 盲派（三层链）/ 河洛 / 黄历已收口接线；六爻装卦层收口（断课层待语料）；子平 V7.207（PZZQ 20/20，pzzq-018 格层收平、用神级 conflict 维持）。数字级细节与证据指针见 `docs\audit\ENGINE_DELIVERY_STATUS_20261111.md`。

---

## 4. 三重取证纪律（保留，一字未改的价值条款）

任何"是否在生产路径上""测试是否覆盖真实对象"类结论，必须同时满足，缺一不可：

1. **调用图取证**：`grep`/`rg` 全仓库符号引用，确认生产调用方数量与位置。零调用方 = 孤儿代码，不得假定为生产路径。
2. **生产入口链取证**：API 入口（app.py 路由）→ pipeline → stage → 引擎逐层追踪，确认运行时实际绑定的实现（警惕 Adapter 层改变目标）。
3. **测试对象核对**：测试断言作用的实体与生产路径为同一实体（import 别名、delegate wrapper、stub/fallback 均可造成"绿但测的不是生产对象"）。

**命名陷阱（本项目专属）**：根 `engines\`（子平 p0 线）≠ `src\tongshu\engines\`（包内引擎）；`ziping-p0\` 是旧副本。写代码、跑测试、下结论前先确认实体。

---

## 5. 红线

1. 禁止 `git add -A` / `git add .`；只逐路径 add 白名单文件。
2. 禁止为让测试通过而降级断言。
3. 禁止修改 Golden 期望值"修复"失败。
4. 禁止未授权写 DB。
5. 禁止引用已被实测推翻的旧审计数字作为当前事实（引用任何数字须带日期+口径）。
6. **所有 `open()` 必须显式 `encoding="utf-8"`**——Windows GBK 代码页下必崩（已有两次事故 G-F4）。
7. 引擎必需项无确定答案时，显式 `NO_EVIDENCE` + fail-closed，不得默认成立。
8. 子平切片覆盖缺口只允许三种法定结局：已补（切片ID）/ 已覆盖（承载切片ID）/ 准入排除（排除依据）。禁止"宁缺勿滥"式结案。
9. 前端不得实现任何命理计算（完整红线清单见 `LIORIN_FRONTEND_SPEC_V2.md`）。
10. 禁止消费 deprecated API（`/api/reading`、`/api/today`）与 `/nfc/*` 冻结端点。

---

## 6. 全栈接手优先级（Claude 的第一批任务）

> 前置：**P0 核对工作树与分支**。2026-11-11 本次检查分支为 `feature/luming-engine`；晚子时修复提交为 `45e2653b`。接手时重新检查 HEAD、暂存区和工作树；大量未提交或未跟踪文件可能属于并行工作，不得擅自清理、覆盖或一并提交。探针清理须 User 确认。

| 优先级 | 任务 | 说明 |
|---|---|---|
| **P0** | 工作树收口 + 分叉处理 | 重新核对本地与上游关系，确认改动归属后制定同步策略 |
| **P1** | 前后端契约落地 | 从 FastAPI 提取 OpenAPI → `API_VIEW_CONTRACT.md`；前端建 HTTP client + contract types；详见 `LIORIN_FRONTEND_SPEC_V2.md` |
| **P1.5** | Public 层联调 | `frontend-case` ↔ `GET /v1/today`（真数据先接 ganZhi/黄历/农历；mock 字段 UI 显式标注） |
| **P2** | Auth + Profile 联调 | 需要 DB 装配（create_app(db_ops=...)）；`/v1/profile` 当前无状态，持久化属后端待办 |
| **P3** | Personal Today 端点设计 | 六日流日卦/cycle/active_yao **后端目前没有此端点**——须走管线新增，前端禁止算（规约 §Gap） |
| **P4** | 权威指针重建 | 把 2026-11 的真实基线固化为新指针文档（本文件 §3 + ENGINE_DELIVERY_STATUS_20261111 即第一版） |

**明确不做**：NFC 修复、梅花接线、改 Golden、擅自改变已裁决的晚子时口径、紫微 canonical 补算法。

---

## 7. 环境与运行手册

### 7.1 后端

```
# 启动（开发）
cd D:\shuntian
$env:PYTHONPATH="src"
python run_server.py            # -> http://127.0.0.1:8000/docs

# 测试（分域，见 §2.4）
python -m pytest tests/ -k ziping

# Golden 回放（放行门）
python scripts/golden_replay.py --check
```

环境变量：`TONGSHU_HOST`（默认 127.0.0.1，**禁止公网**）、`TONGSHU_PORT`（8000）、`TONGSHU_CORS_ORIGINS`、`DEEPSEEK_API_KEY`（未设 → deterministic Stub renderer）、`TONGSHU_TONG_EAGER`、`OTC_G_DATABASE_URL`、`SHUNTIAN_KB_DATABASE_URL`、`TONGSHU_ALLOW_ZIWEI_STUB=1`（仅紫微 stub）。

依赖：Python ≥3.11；Windows 必须装 `tzdata`。

### 7.2 前端（frontend-case）

```
cd D:\shuntian\frontend-case
npm install
npm run dev        # vite
npm run build      # tsc -b && vite build
```

React 18 + TS ~5.6 + Vite 6；**无路由库、无 HTTP 客户端**（联调时引入，见规约 V2 §计划）。

### 7.3 Windows 专项

- GBK 代码页：`open()` 必带 `encoding="utf-8"`；中文路径/文件名在 PowerShell 输出可能乱码。
- 分域跑测试；全树跑批结果带"含隔离污染"免责说明。

---

## 8. 变更登记

| 日期 | 变更 | 批准 |
|---|---|---|
| 2026-11-11 | 初版：推倒 V1 编排结构，改两角色模型；勘误失效路径与悬案；新增全栈优先级 | 初版记载为 User 批准 |
| 2026-11-11 | 登记用户晚子时裁决、修复提交和接手时工作树核验要求 | User 要求修正三份交接文件 |
