# 前端产品审计（工作稿）

## 补充现场检查：窄屏与账户不可用

- 2026-11-14 在本机预览服务、320×568 模拟视口下，今日页和“我的”页的文档宽度均为 320px；现场检查未发现已限定横向溢出的容器有内容超宽。这只覆盖两个页面及该尺寸，不证明全部内容、视口和真实手机均无溢出。
- “我的”页认证检查结束后明确显示“认证服务尚未装配，当前无法建档或登录”；邮箱、验证码、设备 ID 和配对码仍可输入，但三个提交按钮均禁用。用户可以输入却无法继续；状态文字说明了原因，但该环境不具备真实的首次登录和建档闭环。四个输入框在 DOM 中均存在对应 label；键盘操作全流程和屏幕阅读器实际朗读未验证。
- 点击主导航“我的”后 URL 仍为 `/`，证实该导航切换不产生独立页面 URL；刷新行为见下节，浏览器后退和深链仍未验证。此轮使用真实本地浏览器，仅涉及浏览和状态读取，未提交真实个人资料。

## 导航刷新与本机预览恢复（浏览器实测）

- 在本机 `127.0.0.1:5175` 显式本机预览模式，从今日点击“我的”后地址仍为 `/`，刷新后返回今日加载态，随后展示公共今日，未保留“我的”页；点击前快照 `.playwright-cli/page-2026-11-14T06-43-47-769Z.yml`，刷新后快照 `.playwright-cli/page-2026-11-14T06-44-02-828Z.yml`。这是游客、单个浏览器场景；浏览器后退、深链与已登录草稿恢复仍未验证。
- 在同一预览会话仅对 `/v1/today` 临时注入 HTTP 503，页面展示“数据服务尚未连接”和“重试连接”，没有用模拟内容伪装成功；撤销拦截后点击重试，实测恢复到公共今日。故障由浏览器网络拦截模拟，测试的是本机预览分支，不等同于真正断网、生产构建错误页或真实服务重启。

## 账户和档案能力边界（源码核对）

- 登录会话由 `App.tsx:58` 和 `AccountPanel.tsx:40-54` 保存于页面内存；刷新或关闭后不恢复，页面文案也提示需重新邮箱验证。`api/auth.ts:39` 虽定义 `refreshSession`，全 `frontend-case/src` 搜索只命中该定义，未找到调用；因此不能把后端支持 refresh 当作前端已自动续期。真实服务下过期时间、刷新后的重新登录与草稿保留体验未验收。
- 当前工作区档案前端 `api/profile.ts` 只有读取和保存，`AccountPanel.tsx:161-195` 有编辑、保存及读取按钮；`app.py:624,654` 对 `/v1/profile/stored` 注册 PUT 与 GET，检索未发现同路径 DELETE。当前这条产品入口没有找到删除和取消编辑控件；不排除仓库存在其他独立管理路径，线上能力未验证。涉及个人数据的删除路径应在 Gate B 时与权限、数据保留和恢复规则一并确认。

状态：**未完成**。对象是 `D:/shuntian/frontend-case` 的未提交工作区，不是远端 `origin/main@1925adf0`。本机 Vite `127.0.0.1:5175` 使用显式本机预览选项，后端为现存本机服务；不代表部署环境。

| 范围 | 状态 | 证据与限度 |
|---|---|---|
| 公共首页 | 部分实现 | `src/App.tsx:80,109`、`src/pages/today/RealPublicToday.tsx`；2026-11-14 浏览器可见日期、干支、卦和宜忌。生活指引闭环未证实。 |
| 档案与账号 | 部分实现 | `src/components/account/AccountPanel.tsx` 提供邮箱、配对、读取及保存；移动宽度现场显示认证服务尚未装配。真实 SMTP、数据库及同账号持久化未验收。 |
| 本机测试 | 部分实现 | `src/pages/EngineQaPage.tsx` 显式 TEST ONLY，仅用于 QA；不等于正式用户体验或算法验收。 |
| 导航与页面 | 部分实现 | `src/components/navigation/BottomNav.tsx:21` 为今日、指引、洞察、我的、更多；与方案五栏 IA 不同。洞察页明确未开放，关系页未见主导航。深链/404 未验证。 |
| 权益、删除、会话恢复 | 未验证 | 未完成生产调用与端到端核对，不据页面文案推断可用。 |
| 移动及辅助功能 | 未验证 | 已打开 390×844 视口并截首页；尚未完成所有页面、触摸、键盘、缩放与溢出检查。截图 `.playwright-cli/page-2026-11-14T05-44-46-944Z.png`。 |

本轮 `frontend-case` 的 `npm test`：14 文件、66 项通过；测试使用 jsdom 与 mock，不能代替真实邮箱、真实 DB、全部交互或生产验收。`npm run build` 的 TypeScript 编译和 Vite 生产构建通过，但构建成功不代表功能闭环可用。

工作区后端本轮 `pytest tests/test_email_auth_api.py tests/test_personal_heluo_today_api.py tests/test_personal_profile_to_heluo_flow.py -q -p no:cacheprovider`：10 passed。`test_email_auth_api.py:15,27,48` 使用内存 Store 并 mock 发送；`test_personal_heluo_today_api.py:16,51-54` 使用内存 Store 和部分 mock pipeline；`test_personal_profile_to_heluo_flow.py:21-25` 使用内存档案及假邮箱 Store，覆盖真实 pipeline 的个人结果。三类证据不能当成真实 SMTP、真实持久数据库或跨进程会话验收。

权限风险需区分入口：本机 TEST ONLY 服务主动关闭认证；在隔离 TestClient 中，工作区 `/v1/calculate` 无凭据时 flag=0 返回 200、flag=1 返回 401；此结论不代表真实用户档案被读取，也不证明线上开关状态。依据见 `CURRENT_ARCHITECTURE_AUDIT.md`。

## 已复现的开发预览交互缺陷

普通开发服务 `127.0.0.1:5176` 的 `No Profile` 模拟状态标有 `MOCK ONLY`；“完善资料”可点击，点击前后停在同一画面（`.playwright-cli/page-2026-11-14T05-56-24-610Z.yml` 和 `05-56-41-928Z.yml`）。`Valid` 模拟状态的“解锁私享内容”同样点击后无可见变化（`05-57-07-886Z.yml` 和 `05-57-29-213Z.yml`）。代码线索：`App.tsx` 对 `PersonalToday` 未传入 `onProfileNext`，`PersonalToday.tsx:203` 的 `PremiumGate` 未传 `onUnlock`。这两项是**开发模拟路径**上的确认问题，不应误称正式付费接口或正式账户路径已复现相同缺陷；Phase 0 不改代码。
