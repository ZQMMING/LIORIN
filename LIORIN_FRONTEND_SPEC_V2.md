# LIORIN · 前端工程总规范 V2.0 — 联调与生产接入

> 生效日期：2026-11-11
> 取代：`LIORIN_FRONTEND_SPEC_V1.md`（归档保留）。V1 的定位是"独立 UI Case，不进生产仓"——该阶段已经事实上完成（`frontend-case\` 已建成 UI Case），V2 进入**下一阶段：与生产后端联调接入**。V1 的产品语义与红线中仍然有效的部分已收编进本文件，冲突时以本文档为准。
> 读者：Claude（全栈开发执行者）。
> 配套：治理规则见 `AGENTS_V2.md`；引擎状态见 `docs\audit\ENGINE_DELIVERY_STATUS_20261111.md`。

---

## 0. 产品定位（不变的总纲）

LIORIN 前端不是命理计算器。数据链：

```
Backend / EXIS → Canonical State → Evidence → Judgment → Modern Semantic
→ Guidance → Entitlement → Frontend View Model → LIORIN UI
```

前端只负责：Render / Interaction / Navigation / Animation / A11y / Responsive / 内容呈现 / 权限呈现。

前端禁止：命理计算、日期推导、active_yao 推导、卦象推导、旺衰判断、吉凶判断、断言生成、Semantic Mapping、Judgment、Authority、Fallback 推断。

**核心产品语义**（详见 §10 红线与 V1 归档）：

- 三层用户状态：PUBLIC（游客）→ AUTHENTICATED+Profile VALID → PREMIUM。
- Personal TODAY 的核心是**六日流日卦**：一个六日周期对应一个卦，Day N = 第 N 爻，今天的爻 = active_yao（息爻）。
- 五体系（子平/五经、盲派、紫微、河洛、易经）是**互补域**，UI 禁止投票/权重/一致性/胜负比较。
- Premium 只改变可见性/深度/表达（Same Calculation, Different Entitlement）。
- 计算很复杂，UI 很简单：用户看到的是 卦 → 爻 → 今天 → 理解 → 行动。

---

## 0.1 与双产品报告的关系（2026-11-11 对照）

2026-11-03 产品报告提出两个独立消费产品：**深度报告**与 **NFC 饰品每日体验**，共享 LIORIN Core，但分别设计品牌、用户旅程和数据授权；LIORIN Core 不默认作为消费品牌。命名、价格、VI、实际技术栈和上市节奏仍是待验证方案，不得当作已冻结事实。报告网站可优先验证商业闭环，手环可并行做不触及冻结端点的原型；具体实施顺序以用户安排和当前验收结果为准。

本文件后续 Public/Personal Today 页面与 `frontend-case` 是现有原型及联调方案，**不是两个品牌已建成、已确定归属或报告站完整需求已覆盖的证明**。报告站还需独立设计出生信息与时间可信度、免费结果、证据阅读、支付、报告生成与恢复、下载和隐私删除等流程；手环方案另需商品、可选个性化、公开页/私密授权、NFC 失败替代、解绑转赠与隐私流程。两者的最终范围与接口在实际契约和用户确认的产品方案中落实，不应把示例端点或建议目录直接当作现成实现。

用户可见信息须区分计算事实、传统判断和现代解释；仅展示已验收能力，缺依据或未评估时明确说明。独立流派保留不同条件和来源，不能投票合并；原典可追溯不等于科学预测保证。未知出生时间不得静默假设；敏感出生资料不得写入 NFC 标签或第三方分析事件。

产品报告中的品牌视觉方案仍是候选；下文黑色/朱砂等是**现有原型的视觉参考**，不自动成为两个独立品牌最终 VI。任何 NFC 新方案均不能解除现有 `/nfc/*` 三端点 501 冻结。

---

## 1. 现状盘点（2026-11-11 快照，接手时须复核）

> 以下为当时盘点，非永久保证。开发前核对实际运行入口、OpenAPI、响应字段及 provenance，并以当前实测结果更新契约；测试通过或构建成功不能单独证明真实接入。

### 1.1 frontend-case（唯一的现代前端工程）

```
frontend-case\   React 18.3 + TypeScript 5.6 + Vite 6
├── src/
│   ├── App.tsx                  # ⚠️ 模拟登录/档案状态
│   ├── pages/today/{PublicToday,PersonalToday}.tsx + {Me,Insights,Guide}Page.tsx
│   ├── components/hexagram/     # HexagramRenderer / FlowHexagram / SixDayCycle / HetuLuoshuHero
│   ├── components/{yao,cards,shell,navigation,premium,feedback}/
│   ├── design-system/tokens.ts  # 设计令牌（配合 frontend\DESIGN_SPEC.md：纯黑/无圆角/朱砂金点缀）
│   ├── view-models/today.ts
│   ├── domain/entitlement.ts
│   ├── mock/data.ts             # ⚠️ 全部数据来源
│   └── animation/hero.ts
└── dist/                        # 2026-11-11 构建
```

**关键事实：全项目无 fetch/axios/任何 HTTP 客户端；无路由库。登录与档案全是 App.tsx 里的模拟状态。构建成功 ≠ 对接成功。**

### 1.2 其他前端形态

- `frontend\`：纯静态原型（hetu-luoshu.html 主版动画、liorin-v3.html 参考版、DESIGN_SPEC.md 设计规范）。原型参考，不接 API。
- 命名区分：`frontend-case`（React 工程）≠ `frontend`（静态原型）。

### 1.3 后端 API 真实面（GET /docs 可复核）

| 端点 | 状态 | 备注 |
|---|---|---|
| `GET /health` | ✓ | |
| `GET /v1/today` | ✓ | date/region 参数；返回 ganZhi/weekday/黄历 yi/ji/calendar/lunarMonth（**真数据**）；provenance 里 greeting/monthLabel/theme/catalyst/dimensions/time_window/**hexagram/reasoning/cross_validation** 标注 `mock_until_profile_gate_or_content_module`（**后端自身也有 mock 字段**）；认证用户才带 `personal` block |
| `POST /v1/calculate` | ✓ | |
| `POST /v1/daily-guide` | ✓ | |
| `POST /v1/profile` | ✓ | **无状态校验+真太阳时解析**；DB 持久化未做（SIR Runtime P0-5） |
| `/v1/auth/*` | 条件 | create_app() 无 db_ops → **503**；须装配 PostgresAuthDB |
| `/api/reading`、`/api/today` | **DEPRECATED**（Sunset 2027-08-18） | 新前端禁止消费 |
| `/nfc/*` 三端点 | **冻结 501** | 禁止修复 |

---

## 2. Gap 分析（规约愿景 vs 后端现实）

联调不是"接上就行"。V1 规约要求的 Personal 层数据，**后端目前不存在**：

| V1 规约要求 | 后端现状 | 结论 |
|---|---|---|
| 六日流日卦 cycle（cycle_id/hexagram_id/start/end/cycle_day/total_days） | **无端点** | 后端待开发（走管线） |
| active_yao（yao_id/position/type） | **无端点** | 后端待开发 |
| Personal Flow Hexagram Hero 数据 | `/v1/today` 的 hexagram 字段是 **mock_until** | 后端待开发 |
| Today's Yao（古文+现代语义+今日行动） | reasoning/cross_validation 是 mock_until；Guidance 无独立端点 | 后端待开发 |
| Entitlement（PUBLIC/AUTH/PREMIUM 统一判定） | auth 可用但需 DB 装配；premium 语义未在 API 面暴露 | 后端待补 |
| Profile Gate（NONE/INSUFFICIENT/VALID） | `/v1/profile` 校验可用（422 INSUFFICIENT_INPUT+missing_fields），但**无持久化** | 可部分联调 |
| Public TODAY（黄历/方位/颜色/公共卦） | 黄历 yi/ji/calendar **真数据可接**；hexagram/reasoning 是 mock | **可立即联调的部分** |

**铁律**：这些缺口全部在后端补。前端**禁止**用 mock 逻辑或日期计算填补（如 `date % 6` 推 cycle_day）——宁缺勿算，缺端点就显式降级为 Empty/Error 状态。

---

## 3. 联调执行计划（阶段化，每步独立可验收）

> 前置：AGENTS_V2 §6-P0（核对工作树与改动归属）。每步走：契约先行 → 实现 → 分域回归 → User 验收。不得清理或覆盖其他进行中的工作。

### Step A — 契约落地与客户端基础设施

先完成 OpenAPI 与字段来源核验，再建立 HTTP 客户端；本步不实现页面业务联调。

1. 从运行中的 FastAPI（`http://127.0.0.1:8000/openapi.json`）导出 OpenAPI，落成 `frontend-case\contracts\api\API_VIEW_CONTRACT.md`（+ 生成的 TS types）。
2. 逐字段核对：真数据 / mock_until / deprecated 三类标注。**前端不允许猜字段**；Contract 不匹配 = FAIL FAST，不做兼容猜测。
3. 引入 HTTP 客户端与 API client 层（`src\api\`），base URL 走环境变量（`VITE_API_BASE`，默认 `http://127.0.0.1:8000`）；后端 `TONGSHU_CORS_ORIGINS` 相应放行 localhost。

### Step B — Public 层联调（第一个真数据闭环）

- `GET /v1/today` → PublicToday 页：先接真数据（干支/星期/农历/宜忌/calendar）。
- mock_until 字段（hexagram/reasoning/greeting 等）：UI 显式标注"示例数据"或置灰，**不得冒充真数据**（V1 §49 错误边界仍然生效）。
- 保留 mock 层仅作 dev fallback（显式 `MOCK ONLY` 标注，禁止生产路径混入）。

### Step C — Auth + Profile 联调

- 后端：以 db_ops 装配启动（需 PostgreSQL + otcg 库，见 AGENTS_V2 §3.4/§7）。
- 前端：`/v1/auth/*` 真登录替换 App.tsx 模拟状态；`/v1/profile` 对接 Profile Gate（NONE→建档 / INSUFFICIENT→补资料 / VALID→Personal）。
- 登录 ≠ Profile VALID，两级 Gate 保持分离（V1 §1 语义）。

### Step D — Personal Today 端点（后端开发任务，前端等待消费）

- 需求：六日流日卦 cycle + active_yao + 今日爻语义 + Guidance，数据必须来自生产管线（compute/render stage → view model），由后端授权口径输出。
- 立项约束：涉及河洛/易经历法语义，**须 User 批准方案后动工**；不得绕过 Governance 直接在 API 层拼数据。
- 前端在此步之前**保持 Personal 页 mock 隔离**（dev only，显式标注）。

### Step E — Entitlement / Premium / LLM Presentation

- 统一 Entitlement Service（canView/canExpand/canUseLLM），组件内禁止散写 `if (user.subscription...)`。
- Premium 边界：前端隐藏只是 UI，后端必须二次授权。
- LLM 层：只组织语言，禁止重算/造证据；UI 文案"正在整理今日信息"，不暴露内部模型。

---

## 4. 错误与状态边界（收编 V1 §26-29，仍然全部生效）

- Error 五分类：Network / Data / Profile / Calculation / Entitlement，禁止统一 "Something went wrong"。
- **绝对禁止 Personal → Public fallback**：个人计算失败不得用公共数据替代。
- Empty State 必须说清"为什么 + 下一步"（"你的个人时间结构尚未建立 [完善资料]"）。
- Loading 用六条淡爻线渐次成卦的品牌语言。

---

## 5. 息爻与 Hero（收编 V1 §6-11 核心）

- Personal Hero = Personal Flow Hexagram：表达 What（哪个卦）+ Where（第几天）+ Today（哪一爻）。
- 息爻动画：克制（opacity/scale 1.000→1.015/1.025→1.000，3.2s ease-in-out）；禁止 neon/强闪/快 pulse。
- 必须支持 `prefers-reduced-motion`；动画关闭时信息仍完整（TODAY / DAY 3 / 6 / 三爻 文字可达）。
- PublicTodayHero 与 PersonalFlowHexagram 是**不同组件**，不得用 if-login 复用。
- 数据全部来自 API（cycle.cycle_day、active_yao），前端零推导。

---

## 6. 前端红线（收编 V1 §56，全部生效）

```
❌ 不修改 EXIS 计算逻辑          ❌ 不实现命理计算
❌ 不实现 Semantic Mapping       ❌ 不实现 Judgment / 不生成断言
❌ 不自己推 active_yao           ❌ 不根据日期推周期（date % 6 类）
❌ 不 Personal → Public fallback ❌ 不让 LLM 做计算
❌ 不前端硬编码 Premium 数据      ❌ 不消费 Legacy API（/api/*、/nfc/*）
❌ 不绕 Contract（FAIL FAST）     ❌ 不加 Legacy Adapter/Fallback/旧字段猜测
```

---

## 7. 测试与验收

- 契约测试（response schema 对齐 OpenAPI）+ 组件测试 + 三层状态（PUBLIC/AUTH/PREMIUM）场景 + Calculation Error 不回退公共数据 + Reduced Motion + 移动 375/390/430 + 桌面 1280/1440。
- 核心页面 Visual Snapshot：Public Today / Personal Today / Premium Gate / Flow Hexagram / Yao Detail。
- Golden UI Cases 十例沿用 V1 §54（Public、Personal Day 1/3/6、New Cycle、Premium Gate、Private、Calculation Error、Reduced Motion、Mobile）。

### 合入生产仓条件（V1 §63 沿用）

□ UX/视觉/交互/契约 Approved □ Responsive □ A11y □ Mock 边界（无前端计算）□ 无 Legacy Fallback □ Premium 边界 □ Public/Personal 隔离 □ Visual Regression □ Code Audit → **UI CASE FREEZE → Contract Freeze → 合入**

---

## 8. 与其他文档的关系

| 文档 | 关系 |
|---|---|
| `AGENTS_V2.md` | 治理、路径权威表、红线 1-10；本文件红线为其 §5.9/5.10 的细化 |
| `ENGINE_DELIVERY_STATUS_20261111.md` | 引擎/测试基线；Personal Today 端点开发以其收口状态为前提 |
| `LIORIN_FRONTEND_SPEC_V1.md` | 归档；产品语义细节参考（§12 Renderer、§16-24 页面信息结构等），冲突以 V2 为准 |
| `frontend\DESIGN_SPEC.md` | 视觉规范（纯黑/无圆角/朱砂金），design tokens 落地在 `frontend-case\src\design-system\tokens.ts` |

## 9. 变更登记

| 日期 | 变更 | 批准 |
|---|---|---|
| 2026-11-11 | 初版 V2：定位从"独立 Case"改为"联调接入"；补现状盘点/Gap 分析/Step A-E 计划；收编 V1 仍有效条款 | 初版记载为 User 批准 |
| 2026-11-11 | 对照双产品报告，澄清品牌边界、原型定位、证据呈现和冻结状态 | User 要求根据报告修正 |

> 2026-11-11 接手补充：八字晚子时已由用户裁决为 23:00 换时不换日、00:00 换日；前端只展示后端结果，不自行推导。详见 `AGENTS_V2.md` §3.6。
