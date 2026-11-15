# API View Contract — LIORIN 前端联调契约（2026-11-11 · V1）

> 生成方式：从运行中的 FastAPI `create_app()` 直接导出 `openapi.json` + 用 `TestClient` 实测各端点响应。
> 治理依据：`AGENTS_V2.md` §2.3、§5.9/5.10；`LIORIN_FRONTEND_SPEC_V2.md` §2 Gap 分析。
> 原则：**Contract 不匹配 = FAIL FAST**，前端不猜字段、不兼容猜测。字段分类只认实测，不认报告示例。

## 0. 实测环境与导出

| 项 | 值 |
|---|---|
| OpenAPI 导出文件 | `frontend-case/contracts/openapi.json` |
| 端点总数 | 15 |
| 生成命令 | `TONGSHU_AUTH_SECRET=x TONGSHU_AUTHORITY_CREDENTIALS="architecture-governance:schema-v1-arch-gov-2026" PYTHONPATH=src python -c "..."` |
| 生成日期 | 2026-11-11 |
| 后端版本 | `0.2.0`（见 `/health`） |

**15 个端点清单**：`/health`、`/v1/today`、`/v1/calculate`、`/v1/daily-guide`、`/v1/profile`、`/v1/auth/{register,login,refresh,logout,me}`、`/api/reading`、`/api/today`（deprecated）、`/nfc/{daily,relationship,state}`（冻结）。

## 1. 端点状态与消费边界（前端只看这一节就能定接口）

| 端点 | 状态 | 前端可否消费 | 备注 |
|---|---|---|---|
| `GET /health` | 200 OK | ✅ 可 | 健康检查，含 `renderer/model_id/version/gates_blocked` |
| `GET /v1/today` | 200 OK | ✅ **主面** | 真数据字段见 §3；无 mock 字段实际数据 |
| `POST /v1/profile` | 200 OK（无 DB 持久化） | ✅ 部分 | 校验+真太阳时解析，返回 `profile_status`；**无持久化** |
| `POST /v1/calculate` | 200 OK | ✅ 可 | 计算管线，需 `ReadingRequest` |
| `POST /v1/daily-guide` | 200 OK | ✅ 可 | 同上，多 render |
| `POST /v1/auth/register` | **503** AUTH_UNAVAILABLE | ❌ | 无 `db_ops` 装配 → gateway 未初始化 |
| `POST /v1/auth/login` | **400**（无 db 时先过 body 校验） | ❌ | 需 DB 装配 |
| `POST /v1/auth/refresh` | **400** | ❌ | 同上 |
| `POST /v1/auth/logout` | **400** | ❌ | 同上 |
| `GET /v1/auth/me` | **503** | ❌ | 同上 |
| `GET /api/today` | 200（deprecated） | ❌ **禁止** | Sunset 2027-08-18 |
| `POST /api/reading` | deprecated | ❌ **禁止** | |
| `GET /nfc/daily` | **501** 冻结 | ❌ **禁止** | 禁止修复 |
| `GET /nfc/relationship` | **501** 冻结 | ❌ **禁止** | |
| `GET /nfc/state` | **501** 冻结 | ❌ **禁止** | |

## 2. 错误响应两种形态（必须都处理，不能只认一种）

后端存在**两套错误响应外壳**，前端 error handler 必须同时兼容：

### 形态 A：`{"error": {...}}`（业务错误）
```json
{
  "error": {
    "code": "INVALID_INPUT",            // 或 INSUFFICIENT_INPUT / AUTH_* 等
    "message": "request fields present but invalid",
    "request_id": "RR-...",
    "trace_id": "TRACE-...",
    "details": [{"loc": ["body","birth_time"], "msg": "Field required", "type": "missing"}]
  }
}
```

### 形态 B：`{"detail": {...}}`（auth gateway 未初始化）
```json
{
  "detail": { "code": "AUTH_UNAVAILABLE", "message": "gateway not initialised" }
}
```

**注意**：login/refresh/logout 因 body 校验先于 DB 检查，返回形态 A（400）；register/me 无 body，返回形态 B（503）。前端不得假设 auth 错误统一为 503。

## 3. GET /v1/today 响应字段（实测，2026-11-11）

### 3.1 顶层字段（游客态，无认证）

| 字段 | 类型 | 分类 | 说明 |
|---|---|---|---|
| `ganZhi` | `[{name,label,color}]` (3) | **computed 真数据** | 年柱/月柱/日柱干支（当日） |
| `weekday` | `string` | **computed 真数据** | 星期，如「星期三」 |
| `day` | `int` | **computed 真数据** | 日号 |
| `lunarMonth` | `string` | **computed 真数据** | 如「农历十月 · 孟冬」 |
| `yi` | `string[]` | **computed 真数据** | 宜（黄历） |
| `ji` | `string[]` | **computed 真数据** | 忌（黄历） |
| `calendar` | `object` | **computed 真数据** | 完整黄历，36 字段，见 §3.3 |
| `provenance` | `object` | **元数据** | 字段来源标注，见 §3.4 |
| `trace_id` | `string` | **元数据** | 追踪 id |
| `personal` | `object` | **认证态才出现** | 仅 `identity.is_authenticated` 时，见 §3.5 |

### 3.2 关键事实：mock 字段实际不存在

`provenance` 里标注 `mock_until_profile_gate_or_content_module` 的字段
（greeting/monthLabel/theme/catalyst/dimensions/time_window/hexagram/reasoning/cross_validation）
**在当前工作树中实际不返回任何数据** —— 因为 mock 数据源 `web/data/today.json` 文件不存在
（`TODAY_MOCK = {}`）。

**前端结论**：这些字段**不能期待、不能消费**。UI 不得展示占位的 greeting/hexagram/reasoning。

### 3.3 calendar 字段（36 字段，全部 computed）

`solar_date`、`day_stem`、`day_branch`、`year_ganzhi`、`month_ganzhi`、`day_ganzhi`、
`lunar_month`、`lunar_day`、`lunar_month_label`、`jie_qi`、`prev_jie_qi{name,date}`、
`next_jie_qi{name,date}`、`jianchu`、`zhishen`、`zhishen_type`、`zhishen_luck`、
`xiushu`、`xiushu_luck`、`chong`、`chong_shengxiao`、`sha`、`sheng_xiao`、
`nian_na_yin`、`month_na_yin`、`day_na_yin`、`peng_zu_gan`、`peng_zu_zhi`、
`position_xi`、`position_fu`、`position_cai`、
`daily_hexagram{name,upper,lower,moving_line,changed}`、
`yi[]`、`ji[]`、`ji_xiang[]`、`xiong_sha[]`、`source_ids[]`。

### 3.4 provenance 字段（元数据，前端可用于 UI 标注）

| 键 | 值 | 含义 |
|---|---|---|
| `ganZhi` | `"computed"` | 真数据 |
| `weekday` | `"computed"` | 真数据 |
| `day` | `"computed"` | 真数据 |
| `lunarMonth/yi/ji/calendar` | `"computed (...)"` | 真数据 |
| `greeting/.../hexagram/reasoning/cross_validation` | `"mock_until_profile_gate_or_content_module"` | 标注 mock，但实际无数据 |

### 3.5 personal 块（仅认证态）

`_personal_block()` 返回 `{tier:"personal", user_id?, token_version?, has_birth_info?, is_new_user?, device_id?, device_type?}`。
这是稳定小结构，前端据此切 tier，**不需解码 access token**。

## 4. POST /v1/profile 响应（实测）

请求体 `ProfileRequest`（与 `ReadingRequest` 不同！）：
```json
{
  "birth_date": "1990-05-15",           // 必填
  "birth_time": {"hour": 12, "minute": 30},  // 必填，嵌套；minute 可选
  "gender": "male",                      // 必填，^(male|female)$
  "timezone": "Asia/Shanghai",           // 可选
  "calendar_system": "solar",            // 可选，默认 solar
  "location": "beijing",                 // 可选，出生地
  "current_location": "...",             // 可选，仅记录不参与排盘
  "analysis_date": "2026-11-11"          // 可选
}
```

200 响应关键字段：
- `profile_status`: `"VALID"` / `"INSUFFICIENT_INPUT"`（422）/ 其他
- `resolved_time_policy`: 含 `timezone`、`longitude/latitude`、`apparent_solar`、
  `calendar_system`、`day_boundary`（`"00:00"`）、`birth_effective{date,hour,minute,day_rolled}`、
  `correction_minutes`、`corrections{utc_offset_min,ref_meridian,longitude,longitude_correction_min,eot_min,total_correction_min}`、
  `warnings[]`。
- **注意**：`day_boundary` 返回 `"00:00"`，对应晚子时裁决「00:00 换日」。前端只展示，不推导。

## 5. POST /v1/calculate 与 /v1/daily-guide（ReadingRequest）

`ReadingRequest`（与 `ProfileRequest` 不同，**扁平字段**）：
```json
{
  "birth_date": "YYYY-MM-DD",   // 必填
  "hour": 12,                    // 必填，0-23
  "gender": "male",              // 必填
  "theme": "WORK",               // 可选，默认 WORK
  "analysis_date": "YYYY-MM-DD", // 可选，默认今天
  "birth_minute": 0,             // 可选，None=时辰中点
  "timezone": "Asia/Shanghai",   // 可选
  "calendar_system": "solar",    // 可选
  "location": "beijing"          // 可选
}
```

**红线提醒**：`ReadingRequest` 用 `hour`（扁平），`ProfileRequest` 用 `birth_time{hour,minute}`（嵌套）。前端不得把两者字段名混用。

## 6. 前后端 Gap（前端 mock 接口 vs 后端真实接口）

前端 `src/mock/data.ts` 的 `TodayData`/`PublicTodayData` 期望这些字段，**后端 `/v1/today` 均不返回**：

| 前端 mock 期望 | 后端实际 | 处置 |
|---|---|---|
| `cycle`（六日流日卦） | ❌ 无 | 后端待开发（P3，走管线，须 User 批准） |
| `active_yao`（息爻） | ❌ 无 | 后端待开发 |
| `hexagram`（个人卦） | ❌ 无（仅 calendar.daily_hexagram 是当日公共卦） | 后端待开发 |
| `yao_text` | ❌ 无 | 后端待开发 |
| `guidance` | ❌ 无 | 后端待开发 |
| `evidence` | ❌ 无 | 后端待开发 |
| `date_label` | ❌ 无（有 ganZhi/weekday/lunarMonth 真数据可拼） | 前端用真数据字段自拼展示 |
| `daily_hexagram.lines/symbol` | ❌ 无（仅有 name/upper/lower/moving_line/changed） | 后端契约扩展；前端禁止卦象推导补齐（SPEC V2 红线），SVG 爻线渲染待后端补字段后接入 |

**铁律**：这些缺口全部在后端补，前端禁止 mock 填补、禁止 `date % 6` 推 cycle_day、禁止 Personal→Public fallback。

## 7. 可立即联调的部分（Step B 范围）

前端 `PublicToday` 页可立刻接真数据的字段：
`ganZhi`（年/月/日柱）、`weekday`、`day`、`lunarMonth`、`yi`、`ji`、`calendar`（含 daily_hexagram 公共卦）。

> **Step B 已落地（2026-11-12，全栈接手）**：新增 `src/view-models/publicToday.ts`
> （TodayResponse→视图模型纯映射，FAIL FAST）与 `src/pages/today/RealPublicToday.tsx`
> （真数据游客页：卦名/上下卦/动爻/变卦 + 三柱 + 宜忌 + 黄历要点 + trace 溯源）；
> `App.tsx` 游客态走 `fetchToday()` 真数据闭环（loading/error/retry，无 mock 兜底），
> mock 态统一加「MOCK ONLY · 示例数据」徽标。验证：`npm test` 21/21 passed
> （新增 `src/test/realPublicToday.test.tsx` 6 用例），`npm run build`（tsc -b + vite build）通过。
> CORS 实测：后端默认 `TONGSHU_CORS_ORIGINS="*"`，localhost:5173 直连无需代理。

`PersonalToday` 页的 `cycle`/`active_yao`/`hexagram`/`yao_text`/`guidance`/`evidence` 目前**无后端来源**，
前端须显式降级为 Empty/「后端待提供」状态，不接 mock 冒充。

## 8. 环境变量（前端联调需知）

| 前端 | 后端 | 用途 |
|---|---|---|
| `VITE_API_BASE` | — | API base URL，默认 `http://127.0.0.1:8000` |
| — | `TONGSHU_CORS_ORIGINS` | 放行 localhost origin |

后端启动最小 env：`TONGSHU_AUTH_SECRET`（必填，≥32 字节随机）、`TONGSHU_AUTHORITY_CREDENTIALS`（必填，须含 `architecture-governance:schema-v1-arch-gov-2026`）。
`DEEPSEEK_API_KEY` 未设 → deterministic Stub renderer（无 LLM）。
