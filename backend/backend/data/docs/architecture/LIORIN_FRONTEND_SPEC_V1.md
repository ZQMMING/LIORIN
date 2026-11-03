# LIORIN · 前端工程总规范 V1.0

## Frontend Architecture & Product UI Contract

> 独立 UI Case 规范
> 当前不进入顺天生产仓库。
> UI / UX / Interaction / Component / State / Data Contract 全部验证通过后，方可合入主项目。

---

# 0. 产品定位

LIORIN 前端不是传统命理网站，也不是"命理计算器"。

前端的职责是：

```text
Backend / EXIS
      ↓
Canonical State
      ↓
Evidence
      ↓
Judgment
      ↓
Modern Semantic
      ↓
Guidance
      ↓
Entitlement
      ↓
Frontend View Model
      ↓
LIORIN UI
```

前端只负责：

```text
Render
Interaction
Navigation
Animation
Accessibility
Responsive Layout
Content Presentation
Permission Presentation
```

前端禁止：

```text
命理计算
日期推导
active_yao 推导
卦象推导
旺衰判断
吉凶判断
断言生成
Semantic Mapping
Judgment
Authority
Fallback 推断
```

---

# 1. 产品权限模型

整个产品采用三层用户状态。

```text
PUBLIC
游客

AUTHENTICATED
登录 + Profile VALID

PREMIUM
登录 + Premium
```

注意：

```text
Login ≠ Personal Calculation Valid
```

因此必须存在：

```text
AUTHENTICATED
      ↓
Profile Gate
├── NONE
├── INSUFFICIENT
└── VALID
```

---

# 2. Public Layer

游客进入 TODAY：

```text
TODAY
│
├── 日期
├── 当日公共卦象
├── 黄历
├── 有利方位
├── 有利颜色
├── 人际
├── 今日提示
└── Login CTA
```

Public Layer 不得出现：

```text
个人流日卦
个人 active_yao
息爻
个人紫微
个人河洛命盘
个人八字
五经深度判断
盲派判断
个人跨体系分析
```

Public Hexagram 必须有明确语义：

```text
Public Hexagram
```

不能让用户误认为：

```text
这是我的个人卦象
```

---

# 3. Authenticated Personal Layer

当：

```text
authenticated = true
profile_status = VALID
```

TODAY 切换为：

```text
PERSONAL TODAY
```

核心 Hero：

```text
Personal Flow Hexagram
```

结构：

```text
六日流日卦
      ↓
当前六日周期
      ↓
当前 Day
      ↓
active_yao
      ↓
息爻
      ↓
Today's Yao
      ↓
Guidance
```

---

# 4. 六日流日卦

这是 Personal TODAY 的核心产品模型。

## 4.1 六日周期

一个六日周期对应一个 Hexagram。

```text
Cycle
│
├── Day 1 → 初爻
├── Day 2 → 二爻
├── Day 3 → 三爻
├── Day 4 → 四爻
├── Day 5 → 五爻
└── Day 6 → 上爻
```

第七日：

```text
New Cycle
    ↓
New Hexagram
    ↓
Day 1
```

---

# 5. 前端不得计算 active_yao

后端直接提供：

```json
{
  "cycle": {
    "cycle_id": "...",
    "hexagram_id": "...",
    "start_date": "...",
    "end_date": "...",
    "cycle_day": 3,
    "total_days": 6
  },
  "active_yao": {
    "yao_id": "...",
    "position": 3,
    "type": "yang"
  }
}
```

前端只：

```text
consume → render
```

禁止：

```text
date % 6
```

或任何等价推导。

换日、时区、节气、真太阳时、周期边界全部属于 EXIS / Calculation Contract。

---

# 6. Personal Hero

Hero 是整个 TODAY 页面的视觉核心。

最终结构：

```text
             PERSONAL FLOW
                HEXAGRAM

                 ─────
                 ─────

                 ─────
                 ─────

                 ~────~
                   ↑
                 TODAY

                 ─────
                 ─────

                 DAY 3 / 6

                  三爻
                 今日之爻
```

Hero 必须同时表达：

```text
① What
   哪一个卦

② Where
   六日周期第几天

③ Today
   今天是哪一爻
```

---

# 7. 息爻 Breathing Yao

## 7.1 定义

"息爻"不是装饰动画。

它是：

```text
Active Yao
```

的视觉状态表达。

语义：

```text
六日整体状态 = 卦

今天在这个状态中的位置 = 爻

息爻 = 今天
```

---

# 8. 息爻动画规范

必须克制。

允许：

```text
opacity
scale
stroke-width
subtle luminance
weak halo
```

建议：

```text
Duration: 3.2s
Easing: ease-in-out
Scale: 1.000 → 1.015/1.025 → 1.000
```

禁止：

```text
neon glow
强闪烁
快速 pulse
大幅 scale
高亮颜色跳变
游戏化效果
```

视觉感受：

```text
Breathing
```

而不是：

```text
Flashing
```

---

# 9. Reduced Motion

必须支持：

```text
prefers-reduced-motion
```

Reduced Motion：

```text
取消入场动画
取消息爻持续动画
保留 active yao 静态状态
```

用户设置可提供：

```text
Motion
├── Full
├── Reduced
└── Off
```

---

# 10. Hero 入场状态机

完整动画：

```text
IDLE
 ↓
HETU_LUOSHU
 ↓
NUMBER_FLOW
 ↓
CONVERGENCE
 ↓
YIN_YANG
 ↓
YAO
 ↓
HEXAGRAM
 ↓
HOLD
 ↓
TODAY_REVEAL
 ↓
BREATHING_YAO
```

最终不能停在：

```text
Static Hexagram
```

必须进入：

```text
Living Hexagram
+
Active Yao
+
Breathing
```

---

# 11. Public Hero 与 Personal Hero

两者必须是不同状态组件。

```text
PublicTodayHero
```

和：

```text
PersonalFlowHexagram
```

不要用：

```text
同一个 Hero
+ if user logged in
```

强行改变大量行为。

组件语义必须明确。

---

# 12. Hexagram Renderer

Hexagram Renderer 数据驱动。

输入：

```text
hexagram_id
yaos[]
active_yao
```

输出：

```text
SVG Hexagram
```

Renderer 负责：

```text
阳爻
阴爻
位置
间距
active state
animation state
```

Renderer 不负责：

```text
卦义
爻义
吉凶
Judgment
```

---

# 13. 今日爻卡片

Hero 下方：

```text
TODAY'S YAO

三爻

────────────

[ Classical Text ]

现代解释

……

[ 今日行动 ]
```

内容来源：

```text
Canonical Evidence
      ↓
Modern Semantic
      ↓
Guidance
```

前端不能自己把古文解释成现代语义。

---

# 14. 六日进度

建议：

```text
01 ─ 02 ─ ●03 ─ 04 ─ 05 ─ 06
```

或者：

```text
01   02   03   04   05   06
○    ○    ●    ○    ○    ○
```

当前 Day 必须来自：

```text
cycle.cycle_day
```

前端不得自行计算。

---

# 15. 点击 Hexagram

默认：

```text
Hexagram
+
Today Yao
```

点击以后展开：

```text
六日流日卦

上爻
五爻
四爻
三爻 ← TODAY
二爻
初爻

DAY 3 / 6
```

然后：

```text
Today's Yao
Classical Text
Modern Meaning
```

展开属于 UI 状态，不产生任何新的计算。

---

# 16. Personal TODAY 信息结构

推荐：

```text
TODAY
│
├── Personal Flow Hexagram
│
├── Today's Yao
│
├── Heluo
│
├── Yijing
│
├── Ziwei
│
├── Guidance
│
└── Premium Private
```

---

# 17. 河洛卡片

```text
HELUO

今日流日
时间结构

[ 查看河洛 ]
```

只展示后端已经计算完成的信息。

---

# 18. 易经卡片

```text
YIJING

今日之卦
今日之爻

卦辞
爻辞

[ 查看易经 ]
```

---

# 19. 紫微卡片

```text
ZIWEI

今日个人状态

[ 查看紫微 ]
```

紫微是独立体系。

不能 UI 上表现为：

```text
河洛结论
vs
紫微结论
```

禁止比较 / 投票式设计。

---

# 20. 五体系 UI 原则

完整会员页面：

```text
子平 / 五经
盲派
紫微
河洛
易经
```

它们是：

```text
Complementary Domains
```

不是：

```text
Competing Predictors
```

UI 禁止出现：

```text
哪个体系更准
一致率
投票
权重
冲突胜负
```

---

# 21. Premium

Premium 不改变计算结果。

只改变：

```text
Visibility
Depth
Explanation
Guidance
LLM Presentation
```

即：

```text
Same Calculation
Different Entitlement
```

---

# 22. Premium Gate

普通用户：

```text
PRIVATE

深入了解你的时间结构

子平
五经
盲派
紫微
河洛
易经

[ 解锁私享 ]
```

Premium：

```text
PRIVATE
↓
完整内容
```

---

# 23. Private 页面

```text
PRIVATE
│
├── 今日
├── 我的八字
│   ├── 子平
│   ├── 五经
│   └── 盲派
│
├── 我的紫微
├── 我的河洛
├── 我的易经
├── 时间轴
└── 综合观察
```

---

# 24. LLM Presentation Layer

Premium 用户可以得到更自然的语言表达。

数据流：

```text
Evidence
 ↓
Judgment
 ↓
Semantic
 ↓
Guidance
 ↓
LLM
 ↓
Presentation
```

LLM 只能：

```text
组织语言
上下文衔接
个性化表达
阅读体验优化
```

禁止：

```text
重新计算
改变 Judgment
创造规则
创造 Evidence
创造原典依据
改变 Authority
```

---

# 25. LLM UI

不要显示：

```text
AI 正在思考命理……
```

推荐：

```text
正在整理今日信息
```

或者直接使用内容 Skeleton。

用户不需要知道内部模型。

---

# 26. Profile Gate

状态：

```text
NONE
```

显示：

```text
建立你的个人档案
```

---

```text
INSUFFICIENT
```

显示：

```text
还需要完善出生资料
```

---

```text
VALID
```

进入：

```text
Personal TODAY
```

---

```text
CALCULATION_ERROR
```

显示：

```text
个人今日信息暂时无法计算

[重新加载]
```

绝对禁止：

```text
Personal Error
 ↓
Public Hexagram
```

---

# 27. Loading

Loading 不能只是：

```text
Loading...
```

可以使用：

```text
六条淡爻线
```

逐渐形成：

```text
阴
阳
阴
阳
...
```

最后形成完整卦象。

这样 Loading 也是 LIORIN 的品牌语言。

---

# 28. Error

Error 必须区分：

```text
Network Error
Data Error
Profile Error
Calculation Error
Entitlement Error
```

不能统一：

```text
Something went wrong
```

尤其 Calculation Error：

```text
不能使用 Public Data 替代 Personal Data
```

---

# 29. Empty State

例如没有 Profile：

```text
你的个人时间结构尚未建立

[ 完善资料 ]
```

而不是：

```text
暂无数据
```

Empty State 必须告诉用户：

```text
为什么
下一步做什么
```

---

# 30. Navigation

建议保持 5 Tab：

```text
TODAY
GUIDE
INSIGHTS
ME
MORE / PRIVATE
```

但导航本身必须服从 Entitlement。

普通用户看见：

```text
Private
```

可以进入 Gate。

Premium：

```text
Private
```

直接进入。

---

# 31. App Shell

结构：

```text
AppShell
│
├── Header
│   ├── Logo
│   ├── Language
│   └── Timezone
│
├── Main
│
└── BottomNavigation
```

Header 不承担命理信息。

---

# 32. Design System

设计系统采用：

```text
Tokens
 ↓
Primitives
 ↓
Components
 ↓
Patterns
 ↓
Pages
```

---

# 33. Design Token

至少定义：

```text
Color
Typography
Spacing
Radius
Border
Shadow
Motion
Z-index
Container
Breakpoint
```

颜色不得承担：

```text
吉 / 凶
好 / 坏
正 / 负
```

颜色只表达：

```text
UI State
```

例如：

```text
active
selected
hover
disabled
error
```

---

# 34. Typography

建议：

```text
Display
现代东方 Serif

Body
高可读 Sans

Classical
Serif

Data
Sans / Mono
```

禁止过度书法化。

---

# 35. Visual Language

整体：

```text
东方
克制
现代
安静
留白
几何
低对比
```

避免：

```text
大量金色
祥云
龙凤
罗盘堆叠
紫色玄学渐变
水晶球
neon
"大师"式视觉
```

---

# 36. Responsive

必须验证：

```text
Mobile
375 / 390 / 430

Tablet
768

Desktop
1280 / 1440 / 1920
```

Mobile 不是 Desktop 缩小版。

---

# 37. Mobile Layout

```text
Header
 ↓
Hero
 ↓
Today's Yao
 ↓
Heluo
 ↓
Yijing
 ↓
Ziwei
 ↓
Guidance
 ↓
Premium
```

---

# 38. Desktop Layout

Hero 作为核心。

下方：

```text
        HERO
          │
   ┌──────┼──────┐
   │      │      │
 河洛   易经   紫微
   │      │      │
   └──────┼──────┘
          ↓
       Guidance
```

---

# 39. Accessibility

必须支持：

```text
Keyboard Navigation
Screen Reader
ARIA
Focus State
Reduced Motion
Contrast
Touch Target
```

动画不能成为理解信息的唯一方式。

例如：

```text
息爻
```

即使动画关闭，也必须有：

```text
TODAY
DAY 3 / 6
三爻
```

---

# 40. Frontend Component Architecture

建议：

```text
src/
│
├── app/
│   ├── router
│   ├── state
│   └── providers
│
├── components/
│   ├── shell/
│   ├── navigation/
│   ├── hexagram/
│   ├── yao/
│   ├── cards/
│   ├── guidance/
│   ├── premium/
│   └── feedback/
│
├── pages/
│   ├── today/
│   ├── guide/
│   ├── insights/
│   ├── me/
│   └── private/
│
├── domain/
│   ├── auth/
│   ├── profile/
│   ├── entitlement/
│   └── today/
│
├── contracts/
│   └── api/
│
├── view-models/
│
├── animation/
│
├── design-system/
│
└── i18n/
```

---

# 41. Domain / UI 分离

Domain：

```text
API Data
```

View Model：

```text
API Data
 ↓
UI-ready structure
```

Component：

```text
View Model
 ↓
Render
```

这样 API 改变不会直接污染 UI。

---

# 42. Mock 数据

独立 Case 阶段：

```text
mock/
```

所有 Mock 必须显式：

```text
MOCK ONLY
NOT PRODUCTION
```

Mock 不得偷偷承担计算。

例如：

```json
{
  "cycle_day": 3
}
```

可以。

但：

```javascript
cycleDay = date % 6
```

禁止。

---

# 43. API Contract

前端最终消费：

```text
Auth
Profile
Entitlement
Today
FlowHexagram
Yao
Heluo
Yijing
Ziwei
Guidance
Private
```

每个接口必须有明确 Contract。

前端不允许猜字段。

---

# 44. View Model

建议：

```text
TodayViewModel
```

包含：

```text
user_state
profile_state
entitlement
today
flow_hexagram
active_yao
guidance
modules
```

页面只消费 View Model。

---

# 45. Entitlement

统一：

```text
PUBLIC
AUTHENTICATED
PREMIUM
```

不要在每个 Component 写：

```javascript
if (user.subscription === ...)
```

统一：

```text
Entitlement Service
```

然后：

```text
canView()
canExpand()
canUseLLM()
canViewClassics()
```

---

# 46. Security Boundary

前端权限只是：

```text
UI Presentation
```

真正权限必须由：

```text
Backend
```

控制。

前端隐藏 Premium：

```text
不是安全机制
```

Backend 必须再次授权。

---

# 47. Internationalization

初期：

```text
zh-CN
en
de
ja
```

所有 UI 文本进入：

```text
i18n
```

禁止：

```text
组件内硬编码中文
```

特别是：

```text
TODAY
DAY
Yao
Guidance
Premium
```

都必须可国际化。

---

# 48. 时间与时区

前端：

```text
显示时间
```

后端：

```text
决定时间语义
```

前端禁止：

```text
换日
真太阳时
节气
流日
流时
六日周期
```

自行计算。

Header 可以展示：

```text
Timezone
```

但不是计算依据。

---

# 49. 关键错误边界

以下全部禁止：

```text
Personal → Public fallback

Calculation Error → Default Yao

Missing API → Frontend calculation

Missing Judgment → LLM invention

Missing Guidance → UI 自己解释

Premium denied → Frontend 伪造数据
```

---

# 50. UI 数据流

最终标准：

```text
EXIS
 ↓
API
 ↓
Contract Validation
 ↓
View Model
 ↓
Component
 ↓
Renderer
 ↓
Animation
```

---

# 51. 六爻专用数据流

```text
EXIS
 ↓
cycle
 ↓
active_yao
 ↓
HexagramRenderer
 ↓
YaoRenderer
 ↓
BreathingYao
```

任何中间层都不能重新计算。

---

# 52. 前端测试

至少：

```text
Unit
Component
Interaction
Visual
Responsive
Accessibility
Contract
E2E
```

---

# 53. 必测场景

```text
游客
登录无 Profile
Profile 不完整
Profile VALID
Premium
Network Error
Calculation Error
Entitlement Error
Reduced Motion
Mobile
Desktop
```

---

# 54. Golden UI Cases

必须固定：

```text
Case 01
Public TODAY

Case 02
Personal DAY 1

Case 03
Personal DAY 3

Case 04
Personal DAY 6

Case 05
New Cycle

Case 06
Premium Gate

Case 07
Private TODAY

Case 08
Calculation Error

Case 09
Reduced Motion

Case 10
Mobile
```

---

# 55. Visual Regression

核心页面建立 Snapshot：

```text
Public Today
Personal Today
Private Today
Premium Gate
Flow Hexagram
Yao Detail
```

后续代码修改不得无审计改变核心视觉。

---

# 56. Frontend Red Lines

任何开发 Agent 必须遵守：

```text
❌ 不修改 EXIS 计算逻辑
❌ 不实现命理计算
❌ 不实现 Semantic Mapping
❌ 不实现 Judgment
❌ 不生成断言
❌ 不自己推 active_yao
❌ 不根据日期推周期
❌ 不 Personal → Public fallback
❌ 不让 LLM 做计算
❌ 不在前端硬编码 Premium 数据
❌ 不直接消费 Legacy API
❌ 不绕 Contract
```

---

# 57. Legacy

前端不得为了兼容旧系统而加入：

```text
Legacy Adapter
Legacy Fallback
旧字段猜测
旧 API 自动兼容
```

生产 Runtime：

```text
ONE PATH
```

如果 Contract 不匹配：

```text
FAIL FAST
```

而不是：

```text
猜一个结果继续显示
```

---

# 58. 开发顺序

独立 Case 不允许一上来全部开发。

严格：

```text
STEP 0
Design Tokens

STEP 1
App Shell

STEP 2
Public TODAY

STEP 3
Hexagram Renderer

STEP 4
Personal Profile Gate

STEP 5
Six-Day Flow

STEP 6
Active Yao

STEP 7
Breathing Yao

STEP 8
Today's Yao

STEP 9
Heluo / Yijing / Ziwei

STEP 10
Premium Gate

STEP 11
Private

STEP 12
Guidance / LLM Presentation

STEP 13
Responsive

STEP 14
Accessibility

STEP 15
Visual Regression

STEP 16
UX Audit

STEP 17
Engineering Audit

STEP 18
Final Freeze
```

---

# 59. 最终页面层级

用户看到的不是：

```text
Engine
Evidence
Rule
Judgment
Authority
```

而是：

```text
TODAY
 ↓
WHAT
 ↓
WHERE
 ↓
MEANING
 ↓
GUIDANCE
 ↓
ACTION
```

即：

```text
卦
 ↓
爻
 ↓
今天
 ↓
理解
 ↓
行动
```

---

# 60. 最终产品哲学

LIORIN 前端必须做到：

```text
计算很复杂
 ↓
UI 很简单
```

后台可以存在：

```text
子平
盲派
紫微
河洛
易经
五经
Evidence
Judgment
Authority
Semantic
Temporal
```

但用户首先看到：

```text
今天
```

然后：

```text
今天的象
```

然后：

```text
今天的位置
```

最后：

```text
今天可以怎么理解
今天可以怎么行动
```

---

# 61. 最终架构

```text
                         LIORIN
                            │
                    ┌───────┴───────┐
                    │               │
                 PUBLIC          PERSONAL
                    │               │
                 TODAY        Profile VALID
                    │               │
              Public Hexagram   Flow Hexagram
                                    │
                              Six-Day Cycle
                                    │
                               Active Yao
                                    │
                                  息爻
                                    │
                              Today's Yao
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
               河洛                易经                紫微
                 │                  │                  │
                 └──────────────────┼──────────────────┘
                                    │
                                 Guidance
                                    │
                              ┌─────┴─────┐
                              │           │
                           STANDARD    PREMIUM
                              │           │
                           Basic       PRIVATE
                                          │
                                  五经 / 盲派 / 紫微
                                  河洛 / 易经
                                          │
                                       LLM
                                          │
                                    Presentation
```

---

# 62. 独立 Case 最终交付物

这个 Case 不只是一个 HTML 页面。

最终应该交付：

```text
liorin-frontend-case/

├── README.md
├── DESIGN_SPEC.md
├── FRONTEND_ARCHITECTURE.md
├── INTERACTION_SPEC.md
├── API_VIEW_CONTRACT.md
├── ACCESSIBILITY.md
├── I18N.md
├── TEST_PLAN.md
│
├── src/
├── mock/
├── assets/
├── tests/
└── screenshots/
```

其中：

```text
screenshots/
```

保存最终确认的视觉基线。

---

# 63. 合入主项目条件

必须同时满足：

```text
□ UX Approved
□ Visual Approved
□ Interaction Approved
□ Contract Approved
□ Responsive Passed
□ Accessibility Passed
□ Mock Boundary Passed
□ No Frontend Calculation
□ No Legacy Fallback
□ Premium Boundary Passed
□ Public/Personal Isolation Passed
□ Visual Regression Passed
□ Code Audit Passed
```

全部通过：

```text
UI CASE FREEZE
        ↓
Frontend Contract Freeze
        ↓
Merge into LIORIN / 顺天
```

---

# 64. 最终原则

> **前端不理解命理计算，前端理解"产品语义"。**

Engine 告诉系统：

```text
发生了什么
```

Evidence 告诉系统：

```text
依据是什么
```

Judgment 告诉系统：

```text
被授权的判断是什么
```

Semantic 告诉系统：

```text
现代用户应该如何理解
```

Guidance 告诉系统：

```text
用户可以如何行动
```

LIORIN UI 最后负责：

```text
让用户自然地看见这一切。
```

因此：

> **复杂性留在系统内部，确定性留在 Contract，语义留在 Guidance，体验留在前端。**
