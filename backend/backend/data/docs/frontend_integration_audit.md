# Frontend-API Integration Audit Checklist

> 生成日期：2026-08-22
> 审计人：Hermes Agent
> 状态：PENDING CODX DELIVERY

---

## Audit Scope
前端 shuntian-web → 后端 API 对接符合性检查

---

## C1: BackendService 模块 ✅

- [ ] src/lib/backend.ts 存在
- [ ] BASE_URL 使用环境变量 NEXT_PUBLIC_API_URL（非硬编码）
- [ ] fetchToday() 调用 GET /nfc/daily，参数含 pendant_id + date
- [ ] createProfile() 调用 POST /api/v1/profiles
- [ ] handleProfileError() 处理 422 INSUFFICIENT，返回 missing_fields[]
- [ ] 所有 API 调用有 error handling（try/catch 或 .catch()）

---

## C2: Gender 契约 ✅

- [ ] gender 输入只接受 "male" | "female"（React-hook-form / zod 校验）
- [ ] 无默认值（禁止 <select defaultValue="male">）
- [ ] 缺失 gender 时表单字段高亮/禁用提交

---

## C3: Profile Gate 三态 ✅

- [ ] VALID → 保存 profile_id，跳转 /today
- [ ] INSUFFICIENT → 显示 missing_fields[] 列表，不跳转
- [ ] NONE → 显示初始化引导

---

## C4: Today 页面 (首页) ✅

- [ ] 组件挂载时读取 localStorage.pendant_id
- [ ] 有 pendant_id → 调用 getNfcDaily()
- [ ] 无 pendant_id → 显示 NFC Entry 入口
- [ ] 加载状态（Loading spinner）
- [ ] Error 状态（降级显示 Demo Mode）
- [ ] 今日卦象展示来自真实API，非 mock

---

## C5: Onboarding 页面 ✅

- [ ] 表单字段：birth_date、birth_time（hour+minute）、gender、location
- [ ] birth_time 分 hour/minute 两个输入框
- [ ] gender 单选（male/female），无默认
- [ ] location 支持经纬度或城市名

---

## C6: Me 页面 ✅

- [ ] "SET UP PROFILE" 按钮导航到 /onboarding
- [ ] 有 profile 时显示用户信息摘要
- [ ] Profile Status 指示器（VALID/INSUFFICIENT/NONE）

---

## C7: Types ✅

- [ ] NFCRequest 包含 pendant_id, date, gender, birth_date, birth_time, timezone, latitude, longitude
- [ ] ProfileStatus = 'NONE' | 'INSUFFICIENT' | 'VALID'
- [ ] ProfileResponse 包含 profile_id, status, missing_fields, message
- [ ] NFCEntryState 包含 pending, pendant_id?, state

---

## C8: Build ✅

- [ ] npm run build 无 TypeScript 错误
- [ ] 无 console.log 调试输出（生产代码）
- [ ] 无新增 backend 代码（禁止修改 backend）

---

## Verification Commands

```bash
# Build check
cd D:\today\shuntian-web
npm run build

# Type check
npx tsc --noEmit

# Search for violations
grep -r "console.log" src/ --include="*.ts" --include="*.tsx"
grep -r "DEFAULT.*gender" src/ --include="*.ts" --include="*.tsx"
grep -r "localhost" src/ --include="*.ts" --include="*.tsx"
```
