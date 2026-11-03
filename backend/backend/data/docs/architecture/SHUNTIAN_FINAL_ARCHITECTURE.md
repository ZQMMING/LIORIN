# 顺天最终架构定稿

> 定稿时间：2026-08-31  
> 状态：**最终架构Contract，所有后续工程按此执行**  
> 基线继承：ARCHITECTURE_V13_FINAL.md (断言层改造) + CONTEXT_SAVE_20260828.md (七层语义授权链) + 本次产品分层补充

---

## 一、产品最终定位

顺天不是单纯的：

> 八字排盘 + AI 解读

而是：

> **一个以中国传统时间/命理体系为计算基础，以确定性引擎、经典证据、语义映射和结构化判断为核心的东方时间智能系统。**

核心体系：

| 体系 | 角色 |
|------|------|
| 子平 / 五经 | 核心知识资产域（Evidence/Judgment源） |
| 盲派 | 做功/应期维度 |
| 紫微斗数 | 星曜/宫位/四化/限运维度 |
| 河洛理数 | 数/时/位/卦的动态结构 |
| 易经 | 卦辞/爻辞/象义解释层 |
| 黄历 | 公共日常层入口 |

---

## 二、用户产品分层

```text
                    顺天
                     │
          ┌──────────┴──────────┐
          │                     │
        游客                    用户
          │                     │
      公共黄历              Personal Profile
          │                     │
          │             ┌───────┴───────┐
          │             │               │
          │           免费登录        订阅/高级会员
          │             │               │
          │       河洛/易经/紫微       私享完整体系
          │             │               │
          └─────────────┴───────────────┘
```

### 权限矩阵（产品Contract）

| 功能 | 游客 | 登录用户 | Premium |
|------|:----:|:--------:|:-------:|
| 今日黄历 | ✅ | ✅ | ✅ |
| 公共卦象 | ✅ | ✅ | ✅ |
| 有利方位 | ✅ | ✅ | ✅ |
| 适合颜色 | ✅ | ✅ | ✅ |
| 人际日提示 | ✅ | ✅ | ✅ |
| 个人八字 | ❌ | ✅ | ✅ |
| 河洛流日 | ❌ | ✅ | ✅ |
| 紫微基础 | ❌ | ✅ | ✅ |
| 易经流日 | ❌ | ✅ | ✅ |
| 五部经典 | ❌ | ❌ | ✅ |
| 盲派 | ❌ | ❌ | ✅ |
| 深度紫微 | ❌ | ❌ | ✅ |
| 深度河洛 | ❌ | ❌ | ✅ |
| 深度易经 | ❌ | ❌ | ✅ |
| 跨体系综合 | ❌ | ❌ | ✅ |
| LLM个性化润色 | ❌ | ❌ | ✅ |

---

## 三、游客层（不登录）

游客不需要出生资料。

进入首页直接看到：

```text
今日日期
今日干支
今日黄历
今日公共卦象
有利方位
适合颜色
人际主题
行动主题
注意事项
```

这些属于**公共日历信息**。

游客不能看到：
- 个人八字
- 个人紫微
- 个人河洛命盘
- 个人易经流日
- 五经个性化断事
- 盲派
- 私享分析

---

## 四、普通登录用户

登录以后建立：

```text
User
 +
Profile
 +
CalculationContext
```

Profile 核心输入：

```text
birth_date
birth_time
calendar_system
birth_location
timezone
gender
true_solar_time
day_boundary_rule
calendar_conversion
```

这些属于**计算上下文**，不是文案层字段。

登录用户看到：

### 我的今日

核心增加：

1. **河洛理数**
   ```text
   本命
   元堂
   后天
   流年
   流月
   流日
   时序
   ```

2. **易经**
   ```text
   今日卦
   流日卦
   卦象
   爻位
   卦辞
   爻辞
   象义
   基础行动提示
   ```

3. **紫微斗数**
   ```text
   命宫
   身宫
   主要宫位
   主星
   四化
   当前流年
   相关时间结构
   ```

---

## 五、订阅/高级会员

用户登录后，如果：

```text
subscription = ACTIVE
plan = PREMIUM
```

打开：「我的私享」

完整开放：

```text
子平
├── 《渊海子平》
├── 《子平真诠》
├── 《滴天髓》
├── 《穷通宝鉴》
└── 《三命通会》

盲派
紫微斗数
河洛理数
易经
```

以及：

```text
跨体系事件分析
时间轴
流年
流月
流日
应期
现代语义
行动建议
```

---

## 六、五部经典的角色定义

**五部经典不是五个计算引擎。**

它们是：

> **子平知识 / Evidence / Judgment 资产域。**

计算仍然来自：

```text
Bazi Engine
      ↓
Engine Evidence
      ↓
Semantic Atom
      ↓
经典 Evidence
      ↓
Condition
      ↓
Judgment
```

五部经典分别独立维护：

```text
《滴天髓》
《子平真诠》
《穷通宝鉴》
《三命通会》
《渊海子平》
```

每一本拥有自己的：

```text
Corpus
Evidence
Primitive
Condition
Judgment
Provenance
Authority
```

**但是最终进入 Production 的权限必须统一。**

---

## 七、紫微与河洛的定位

### 紫微

重点先做：

```text
确定性排盘
↓
星曜
↓
十二宫
↓
四化
↓
限运
↓
流年
↓
流月/流日
```

GitHub 开源代码（iztro）只能作为：
> **Implementation Reference**

绝不能当：
> Canonical Authority

### 河洛

重点：

```text
本命
↓
元堂
↓
后天
↓
大运
↓
流年
↓
流月
↓
流日
↓
时序
```

仓库已有 `timeline_yun.py` 实现时间链，这是：
> **确定性时间结构引擎**

### 易经与河洛必须分开

- **河洛**：负责数、时、位、卦的动态结构
- **易经**：负责卦、爻、象、辞、理的解释

流程：

```text
河洛 Engine
      ↓
今日/流日卦
      ↓
易经 Engine
      ↓
卦辞/爻辞/象
      ↓
结构化解释
```

---

## 八、五大体系统一方式

不是统一算法。

而是统一：

# `EngineEvidence Contract`

```text
子平 ─────┐
盲派 ─────┤
紫微 ─────┤
河洛 ─────┼──→ EngineEvidence
易经 ─────┘
```

每个体系保持自己的：
- 算法
- 术语
- 结构
- 时间逻辑
- 原典体系

但最终都输出统一的事实证据。

V13 已冻结：`EngineEvidence` 只能包含事实、数值、结构、位置、时间，不允许 `polarity/direction`。

---

## 九、完整核心数据链

```text
INPUT
  │
  ▼
Calculation Context
  │
  ▼
Deterministic Engines
  │
  ├── Bazi / 子平
  ├── Blind School
  ├── Ziwei
  ├── Heluo
  ├── Yijing
  └── Almanac
  │
  ▼
EngineEvidence
  │
  ▼
Canonical State
  │
  ▼
Semantic Atom
  │
  ▼
Canonical Evidence
  │
  ▼
Condition Evaluator
  │
  ▼
Judgment
  │
  ▼
Authority Gate
  │
  ▼
Cross-Domain Evidence
  │
  ▼
Modern Semantic Mapping
  │
  ▼
Domain
  │
  ▼
Guidance
  │
  ▼
LLM Renderer
  │
  ▼
User Output
```

---

## 十、现代语义映射

传统术语**不能直接进入用户界面**。

必须：

```text
传统计算
 ↓
Semantic Atom
 ↓
Modern Concept
 ↓
Domain
 ↓
Guidance
```

例如：

```text
五行/十神
      ↓
Semantic Atom
      ↓
现代概念
      ↓
事业/财富/人际/家庭
      ↓
行为指引
```

V13 已冻结语义目录：

```text
five_elements
ten_gods
ziwei_stars
transformations
hexagrams
yao
he_luo
modern_concepts
```

---

## 十一、8个最终用户领域

```text
CAREER       事业
FINANCE      财富
RELATIONSHIP 感情
FAMILY       家庭
SOCIAL       人际
GROWTH       成长
HEALTH       健康
DECISION     决策
```

---

## 十二、LLM的最终位置

LLM：

```text
❌ 不排盘
❌ 不计算
❌ 不判断强弱
❌ 不创造断言
❌ 不改变Judgment
❌ 不改变方向
❌ 不增加证据
❌ 不引用系统没有提供的规则
```

只负责：

> **把已经得到授权的结构化Guidance写成人能理解的语言。**

按会员层级：

| 用户类型 | LLM使用 |
|----------|---------|
| 游客 | 不用LLM |
| 普通登录 | 确定性模板/结构化解释 |
| Premium | LLM个性化润色 |

```text
Deterministic Result
       ↓
Modern Guidance
       ↓
Premium LLM Renderer
       ↓
个性化自然语言
```

---

## 十三、前端最终结构

```text
                    APP
                     │
             ┌───────┴───────┐
             │               │
          Public           Account
             │               │
           TODAY             │
             │        ┌──────┴──────┐
             │        │             │
             │       Free        Premium
             │        │             │
             │        └──────┬──────┘
             │               │
             └───────────────┘
```

### 公共导航

```text
TODAY
CALENDAR
HEXAGRAM
PROFILE
```

登录后增加：

```text
MY DAY
MY CHART
ZIWEI
HELUO
YIJING
```

Premium：

```text
PRIVATE
├── 子平
├── 五经
├── 盲派
├── 紫微
├── 河洛
├── 易经
├── 时间轴
└── 综合分析
```

前端特性：
- PWA
- 单页体验
- 5 tabs
- 四语言 i18n（中文/English/Deutsch/日本語）

---

## 十四、API最终结构

```text
/api/v1/public/*
游客：
  GET /today
  GET /calendar
  GET /public-hexagram

/api/v1/profile/*
登录：
  GET /profile
  POST /profile
  GET /chart
  GET /today/personal

/api/v1/basic/*
普通登录：
  GET /ziwei/basic
  GET /heluo/day
  GET /yijing/day
  GET /timeline

/api/v1/private/*
Premium：
  GET /private/ziping
  GET /private/classics
  GET /private/blind
  GET /private/ziwei
  GET /private/heluo
  GET /private/yijing
  GET /private/cross-domain
  GET /private/timeline

/api/v1/guidance/*
最终：
  GET /guidance/today
  GET /guidance/timeline
  GET /guidance/event
```

---

## 十五、权限系统

最终不是简单的 `logged_in = true`

而是：

```text
anonymous
free_user
premium_user
admin
```

并且：

```text
Feature
   ↓
Entitlement
   ↓
Permission
   ↓
API
   ↓
Output
```

---

## 十六、数据库最终分层

```text
Identity
├── users
├── profiles
├── subscriptions
└── entitlements

Calculation
├── calculation_context
├── charts
├── engine_evidence
└── temporal_states

Knowledge
├── classical_sources
├── evidence
├── primitives
├── conditions
├── judgments
└── provenance

Governance
├── authority_registry
├── admission_records
├── audit_records
└── version_registry

Semantic
├── semantic_atoms
├── modern_concepts
├── domain_mapping
└── guidance_templates

Output
├── guidance
├── rendered_output
└── trace
```

---

## 十七、仓库最终工程结构

```text
wisdom/

├── apps/
│   ├── api/
│   └── web/
│
├── src/tongshu/
│   ├── core/
│   │   ├── contracts/
│   │   ├── context/
│   │   ├── evidence/
│   │   ├── provenance/
│   │   └── temporal/
│   │
│   ├── engines/
│   │   ├── bazi/
│   │   ├── ziping/
│   │   ├── blind/
│   │   ├── ziwei/
│   │   ├── heluo/
│   │   ├── yijing/
│   │   └── almanac/
│   │
│   ├── canonical/
│   │   ├── state/
│   │   ├── facts/
│   │   └── composer/
│   │
│   ├── semantics/
│   │   ├── atoms/
│   │   ├── concepts/
│   │   ├── mappings/
│   │   └── domains/
│   │
│   ├── knowledge/
│   │   ├── ditiansui/
│   │   ├── ziping_zhenquan/
│   │   ├── qiongtong_baojian/
│   │   ├── sanming_tonghui/
│   │   ├── yuanhai_ziping/
│   │   ├── blind_school/
│   │   └── yijing/
│   │
│   ├── judgment/
│   │   ├── primitives/
│   │   ├── conditions/
│   │   ├── evaluators/
│   │   ├── judgments/
│   │   └── resolver/
│   │
│   ├── authority/
│   │   ├── evidence/
│   │   ├── judgment/
│   │   ├── runtime/
│   │   └── admission/
│   │
│   ├── cross_domain/
│   │   ├── evidence/
│   │   ├── temporal/
│   │   └── synthesis/
│   │
│   ├── guidance/
│   │   ├── composer/
│   │   ├── templates/
│   │   └── trace/
│   │
│   ├── renderer/
│   │   ├── deterministic/
│   │   └── llm/
│   │
│   ├── entitlement/
│   │   ├── users/
│   │   ├── subscriptions/
│   │   └── permissions/
│   │
│   └── api/
│       ├── public/
│       ├── auth/
│       ├── basic/
│       ├── private/
│       └── admin/
│
├── data/
│   ├── canonical/
│   ├── semantic/
│   ├── knowledge/
│   ├── golden/
│   └── reference/
│
├── tests/
│   ├── engines/
│   ├── canonical/
│   ├── semantics/
│   ├── judgment/
│   ├── cross_domain/
│   ├── api/
│   ├── entitlement/
│   └── golden/
│
├── docs/
│   ├── architecture/
│   ├── product/
│   ├── contracts/
│   ├── governance/
│   └── audits/
│
└── scripts/
```

---

## 十八、旧架构处理

**不保留第二套生产 Runtime。**

必须删除：

```text
旧Assertion Runtime       ❌ 删除
旧P3/P5结论链             ❌ 删除
旧Strength Verdict         ❌ 删除
wang_score                  ❌ 删除
旧投票/权重机制              ❌ 删除
旧Guidance Runtime         ❌ 删除
```

可复用的：

```text
底层计算
数据
算法
测试资料
经典原文
```

**但旧系统不能作为fallback。**

---

## 十九、互补不比较原则

最终：

```text
子平发现A
盲派发现B
紫微发现C
河洛发现D
易经发现E
```

不是：

```text
A+B+C+D+E
→打分
→投票
→可信度
```

而是：

```text
A─┐
B─┤
C─┤
D─┼──→Cross-Domain Evidence
E─┘
```

**每个体系增加一个观察维度。**

V13 已明确禁止：confidence voting / engine score / majority / weighted direction

---

## 二十、最终研发路线

```text
PHASE 0    架构重置 + Legacy完整删除
    ↓
PHASE 1    Core Contract + Canonical Core
    ↓
PHASE 2    Bazi/子平 Engine收敛
    ↓
PHASE 3    紫微Deterministic Engine
    ↓
PHASE 4    河洛Deterministic Engine
    ↓
PHASE 5    易经Engine/Interpretation
    ↓
PHASE 6    盲派Engine + Knowledge
    ↓
PHASE 7    五部经典知识资产体系
    ↓
PHASE 8    Semantic Mapping
    ↓
PHASE 9    Judgment + Authority
    ↓
PHASE 10   Cross-Domain
    ↓
PHASE 11   Free/Premium Product API
    ↓
PHASE 12   Frontend/PWA完整产品
    ↓
PHASE 13   Golden/Blind/Real Case Validation
    ↓
PHASE 14   Production
```

**工程上可以并行建设计算引擎和知识资产，但生产链必须按照依赖关系逐层打开。**

---

## 二十一、最终前端产品形态

用户看到的是：

```text
┌──────────────────────────────┐
│          顺天 TODAY           │
│                              │
│       今日 · 8月31日          │
│                              │
│       今日卦象                │
│                              │
│  宜：……                       │
│  忌：……                       │
│                              │
│  有利方位  东南               │
│  适合颜色  ……                 │
│  人际主题  ……                 │
│                              │
│      [ 查看我的今日 ]          │
└──────────────────────────────┘
```

登录：

```text
我的今日
│
├── 河洛流日
├── 易经流日卦
├── 紫微今日
└── 我的时间轴
```

Premium：

```text
我的私享
│
├── 子平
│   ├── 五经
│   └── 事件分析
│
├── 盲派
│
├── 紫微
│
├── 河洛
│
├── 易经
│
├── 跨体系
│
└── 时间轴
```

最终用户看到的是**现代语言、现代领域、现代行动建议**。

传统体系全部隐藏在证据链后面。

---

## 二十二、最高级别Contract（12条总原则）

```text
01  确定性计算优先
02  原典是知识授权源
03  GitHub/开源代码只是实现参考
04  Engine只产生Evidence，不产生最终断事
05  五体系互补，不比较、不投票、不加权
06  Evidence/Condition/Judgment/Authority永久分离
07  传统术语必须经过Semantic→Modern Concept
08  LLM只表达，不判断
09  用户权限决定"能看到什么"，不能改变计算结果
10  Premium是内容/解释深度权限，不是另一套算法
11  生产Runtime只有一条，不保留Legacy fallback
12  所有最终输出必须可追溯到Evidence
```

---

## 二十三、顺天一句话概括

> **游客使用顺天看"今天"；登录用户使用顺天理解"我的今天"；高级会员使用顺天理解"我的人生时间结构"。**

底层链路：

```text
              顺天产品
                  │
       ┌──────────┴──────────┐
       ↓                     ↓
   Public Today          Personal Intelligence
                              │
              ┌───────────────┼───────────────┐
              ↓               ↓               ↓
             子平            紫微            河洛
              │               │               │
             盲派            易经            黄历
              └───────────────┼───────────────┘
                              ↓
                       Engine Evidence
                              ↓
                       Canonical State
                              ↓
                       Semantic Layer
                              ↓
                    Evidence/Condition
                              ↓
                          Judgment
                              ↓
                       Authority Gate
                              ↓
                     Cross-Domain Evidence
                              ↓
                     Modern Semantic Map
                              ↓
                          Guidance
                              ↓
                  ┌───────────┴───────────┐
                  ↓                       ↓
             Deterministic             Premium
               Renderer               LLM Polish
                  │                       │
                  └───────────┬───────────┘
                              ↓
                           Frontend
```

---

## 二十四、与V13的关系

V13（ARCHITECTURE_V13_FINAL.md）作为**中间语义/授权核心基线**继续有效。

本文件是**产品级总架构**，覆盖：
- V13的断言层改造
- 七层语义授权链
- 本次补充的产品分层、权限模型、API结构、研发路线

**本文件优先级高于V13，冲突时以本文件为准。**

---

*文档结束。此为顺天最终架构总Contract，不再因单一模块调整而变更顶层结构。*
