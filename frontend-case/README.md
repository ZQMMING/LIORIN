# LIORIN Frontend Case

当前按 `LIORIN_FRONTEND_SPEC_V2.md` 分阶段接入生产后端。**默认是公共今日页**，向本地后端请求 `GET /v1/today`；无法连接或响应缺字段时显示错误，不使用模拟数据兜底。

## 本地运行

在 `D:\shuntian` 中启动后端（默认仅监听 `127.0.0.1:8000`）：

```bash
python run_server.py
```

在 `frontend-case` 目录启动前端：

```bash
npm run dev
```

访问 `http://localhost:5173`。开发模式默认访问本机后端；正式构建默认请求页面同源的 `/v1`，部署时须将该路径代理到后端。如需指定其他后端地址，构建或启动前设置 `VITE_API_BASE`；跨源访问须由后端 `TONGSHU_CORS_ORIGINS` 放行对应前端地址。运行测试与构建：`npm test`、`npm run build`。

### 本机网页预览（后端可暂不启动）

在 `frontend-case` 目录的 Bash 终端运行：

```bash
LIORIN_LOCAL_PREVIEW=1 VITE_LIORIN_LOCAL_PREVIEW=1 npm run dev -- --host 127.0.0.1 --port 5191 --strictPort
```

打开 `http://127.0.0.1:5191/`。前端仅监听本机；通过 Vite 同源代理访问本机 `127.0.0.1:8000` 的 API。后端未启动时显示明确的“本机预览/数据服务尚未连接”空状态，不展示伪造公共卦象。开发模式右下角状态切换器仅用于设计预览，标有 `MOCK ONLY`，不能用作真实业务验收。

要从网页测试引擎而无需真实注册账户，可在开发机**另开终端**启动仅 loopback 的 QA 后端：

```bash
LIORIN_LOCAL_ENGINE_QA=1 python tools/local_engine_qa.py
```

再到网页「我的」→「打开引擎测试工作台（TEST ONLY）」输入测试命例并点击运行。此为**本机 QA 会话，不是正式测试账号**；后端使用仓库测试权威凭据与 Stub renderer，不装配用户数据库或邮件服务，只返回有界摘要（canonical、trace、证据索引和状态），不会把 100 年河洛全量时间轴送进浏览器。若校验显示未通过，请记录 trace/摘要用于后续逐引擎排查。禁止把 QA 服务绑定到局域网或公网。

### 局域网内部预览（显式 opt-in）

后端始终只监听同机 `127.0.0.1:8000`，前端开发服务仅在显式设置 **两个**开关后绑定局域网并同源代理 `/v1`、`/health`：

```bash
# 在 frontend-case 目录（Bash）
LIORIN_LAN_TEST=1 VITE_LIORIN_LAN_TEST=1 npm run dev -- --port 5190 --strictPort
```

在同一局域网另一设备访问 `http://<开发机局域网IP>:5190/`。无需把后端 8000 暴露到局域网；前端请求 `/v1/*` 由 Vite 代理到开发机 loopback。仅用于受信任内网的短期测试，测试后关闭服务，并检查 Windows 防火墙仅对私有网络放行该临时端口；**不要暴露公网**。没有后端服务时页面可打开，但 API 会报错；这不算联调通过。

完整账户链路另需：真实 authority trust root、显式数据库 DSN、人工验收并执行 `profile_0001.sql` 与 `email_auth_0001.sql`、SMTP STARTTLS 配置以及邮箱/数据库实际读写测试。当前环境未配置这些值，不能声称已完成完整局域网端到端验收。

**边界**：生产构建默认展示公共真数据；邮箱登录、存档和个人河洛今日的代码链已接入，但真实数据库迁移/邮件投递尚未在本机验收，不能算已上线。Premium 与未经核验的解释仍未开放。右下角模拟状态切换器仅在开发模式出现，个人预览数据有 `MOCK ONLY · 示例数据` 标识；不要把预览当真实结果。后端默认未装配数据库时，认证接口返回 503；个人河洛端点 `GET /v1/personal/heluo-today` 需有效用户身份和已存档案。

认证数据库装配采用显式 opt-in：仅在完成现有冻结契约与 Auth 迁移的人工验收、设置 `TONGSHU_AUTH_DB_ENABLED=1` 和 `OTC_G_DATABASE_URL` 后启动。缺少 DSN 或数据库不可达时服务拒绝启动；启动脚本不执行迁移、seed，也不使用默认本地库口令来隐式启用认证。

个人档案使用**独立迁移** `src/tongshu/db/profile_0001.sql`，不修改冻结 DDL，不会自动执行。部署前核对目标库、备份、Auth 表并手工执行迁移；随后设置 `TONGSHU_PROFILE_STORE_ENABLED=1` 才可启用 `GET/PUT /v1/profile/stored`。启动时只读检查档案表是否存在，缺表拒绝启动。旧 `POST /v1/profile` 仍是无状态校验回执，不表示已保存。

账户 UI 采用**邮箱验证码登录/注册同一账户**：请求验证码不建号，验证码验证成功后按邮箱查找原账户或新建账户。设备 ID + 配对码保留为兼容入口，错误配对不得新建孤儿账户。令牌仅驻留本页内存；刷新后再次通过邮箱验证码登录。档案只在已认证用户点击保存后发送，后端确认 `stored=true` 才显示成功。

邮箱能力须显式启用 `TONGSHU_EMAIL_AUTH_ENABLED=1`，并设置 `TONGSHU_EMAIL_AUTH_SECRET`（至少 32 字节）、`TONGSHU_SMTP_HOST`、`TONGSHU_SMTP_FROM`，按实际服务设置 `TONGSHU_SMTP_PORT`、`TONGSHU_SMTP_USER`、`TONGSHU_SMTP_PASSWORD`。部署前需人工验收并执行独立迁移 `src/tongshu/db/email_auth_0001.sql`；启动只读检查挑战表是否存在，缺表或 SMTP 配置不完整时拒绝启动。验证码只存 HMAC，不写明文日志；邮件发送服务须支持 STARTTLS。

---

## Architecture

```
liorin-frontend-case/
├── src/
│   ├── animation/         # Hero state machine, breathing yao
│   ├── components/
│   │   ├── cards/         # Heluo, Yijing, Ziwei cards
│   │   ├── feedback/      # Profile gate, errors, loading
│   │   ├── hexagram/      # Hexagram renderer, flow, six-day cycle
│   │   ├── navigation/    # Bottom nav
│   │   ├── premium/       # Premium gate
│   │   ├── shell/         # Header + app layout
│   │   └── yao/           # Today's yao card
│   ├── design-system/     # Token definitions
│   ├── domain/            # Entitlement service
│   ├── mock/              # MOCK ONLY data — no calculations
│   ├── pages/             # Today, Guide, Insights, Me
│   ├── view-models/       # API → UI transformation
│   └── App.tsx
├── index.html
├── vite.config.ts
└── tsconfig.json
```

---

## Design Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-primary` | `#10100E` | Page background |
| `--text-primary` | `#F1EDE3` | Main text |
| `--text-secondary` | `#9B988F` | Secondary text |
| `--text-muted` | `#5C5A54` | Labels, disabled |
| `--accent` | `#A34A3A` | Active yao, CTAs (cinnabar) |
| `--font-display` | Noto Serif SC | Headings, classical text |
| `--font-body` | Inter | Body text |
| `--font-mono` | JetBrains Mono | Dates, cycle days |

---

## Golden UI Cases

| Case | State | Description |
|------|-------|-------------|
| 01 | Public TODAY | Guest sees public hexagram + guidance |
| 02 | Personal DAY 1 | First day of six-day cycle |
| 03 | Personal DAY 3 | Active yao = 三爻 |
| 04 | Personal DAY 6 | Last day of cycle |
| 05 | New Cycle | Day 7 → new hexagram starts |
| 06 | Premium Gate | Authenticated but not premium |
| 07 | Private TODAY | Premium + valid profile |
| 08 | Calculation Error | Profile valid but data unavailable |
| 09 | Reduced Motion | prefers-reduced-motion enabled |
| 10 | Mobile | 375px viewport |

---

## Red Lines (spec section 56)

- ❌ No frontend calculation of active_yao, cycle_day, or hexagram
- ❌ No Personal → Public fallback
- ❌ No Legacy adapter or field guessing
- ❌ No LLM doing computation
- ❌ No gold/dragon/phoenix visual clichés
- ❌ No neon effects or game-like particles

---

## Dev Notes

The bottom-right corner has a state switcher for testing all golden cases:
- Public
- No Profile
- Incomplete
- Valid
- Premium
- Error

To switch language/timezone, use the header controls.
