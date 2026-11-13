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

访问 `http://localhost:5173`。如需更改后端地址，设置 `VITE_API_BASE` 后再启动前端；跨源访问须由后端 `TONGSHU_CORS_ORIGINS` 放行对应前端地址。运行测试与构建：`npm test`、`npm run build`。

**边界**：生产构建只展示公共真数据与游客能力状态；个人今日、登录/建档与 Premium 尚未形成后端闭环。右下角的模拟状态切换器仅在开发模式出现，个人页数据有 `MOCK ONLY · 示例数据` 标识；不要把预览当真实结果。后端默认未装配数据库时，`/v1/auth/*` 返回 503；个人今日端点尚不存在。

认证数据库装配采用显式 opt-in：仅在完成现有冻结契约与 Auth 迁移的人工验收、设置 `TONGSHU_AUTH_DB_ENABLED=1` 和 `OTC_G_DATABASE_URL` 后启动。缺少 DSN 或数据库不可达时服务拒绝启动；启动脚本不执行迁移、seed，也不使用默认本地库口令来隐式启用认证。

个人档案使用**独立迁移** `src/tongshu/db/profile_0001.sql`，不修改冻结 DDL，不会自动执行。部署前核对目标库、备份、Auth 表并手工执行迁移；随后设置 `TONGSHU_PROFILE_STORE_ENABLED=1` 才可启用 `GET/PUT /v1/profile/stored`。启动时只读检查档案表是否存在，缺表拒绝启动。旧 `POST /v1/profile` 仍是无状态校验回执，不表示已保存。

当前账户 UI 只支持已有设备 ID + 配对码登录，令牌仅驻留本页内存；刷新即清除。匿名建号会产生难以恢复的账户，因此在账户恢复流程完成前**不开放**注册按钮。档案只在已认证用户点击保存后发送，后端确认 `stored=true` 才显示成功。

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
