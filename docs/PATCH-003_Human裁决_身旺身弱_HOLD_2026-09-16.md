# PATCH-003 Classical Concept Audit：身旺/身強/身弱/身衰（第一批 · Human 裁决落档）

> 日期：2026-09-16 ｜ Human 拍板：**证据审计 PASS，算法裁决 HOLD**

## 一、Human 最终裁决表（禁止推翻）

| 项目 | 裁决 |
|---|---|
| 六经典原文搜索 | PASS |
| 身旺/身强概念审计 | PASS |
| 身弱/身衰概念审计 | PASS |
| 得令/失令证据发现 | PASS |
| 得地/得垣证据发现 | PASS |
| 得势证据 | PENDING（须单独钉查，不得与得垣/持势合并） |
| 统一算法（跨书 StrengthCalculator） | REJECT |
| Boolean 强弱（is_strong=true / is_weak=false） | REJECT |
| 多维中间状态 | APPROVE |
| 最终 strength_state | HOLD（容器保留，判定算法逐书逐章裁决） |

## 二、六部证据钉查（Human 核证，本批已验）

### 渊海子平（YHZP）——旺≠强，得时≠身旺唯一条件
- 「身旺者喜逢祿馬，身弱者忌見財官」
- 「得時俱為旺論，失令便作衰看」
- 「四柱無根，得時為旺」
- 「日干無氣，遇劫為強」
→ 得时→旺 与 无根+得时→旺 并存；无气+遇劫→强。**旺≠强；得时≠身旺唯一条件**。

### 神峰通考（SFTK）——得令/得垣/持势三个独立概念
- 「身主要強，月提得令」
- 「陰木歸垣失令，終為身弱」
- 「五行失令者，縱然歸祿得垣，被比局持勢於月令，不作身旺格矣」
→ 得垣+持势+失令 → 仍不作身旺格。**不得令时，得垣/持势不足以定身旺**。
→ 禁止：ROOT_PRESENT=true → 身旺；得地=true → 身旺。

### 滴天髓（DTS）——注家层不得反推原文算法
- 正文对身旺/身弱直接使用非常有限（「從兒不論身強弱」等）
- 「官星身旺…」等大量具体解释属任氏注解体系
→ 保留 ORIGINAL/ANNOTATION 分层；不得拿任铁樵注反推《滴天髓》原文通用身强算法。

### 子平真诠（PZZQ）——身强是格局条件变量，须记录完整语境
- 「身強印旺，透煞孤貧」——印用七杀的格局语境中成立
→ PZZQ 身强必须记录 chapter+格局+前置条件+后置条件；不得抽取为 PZZQ_SHEN_QIANG=X 全局消费。

### 穷通宝鉴（QTBJ）——调候体系，章节隔离
- 体系：日干+月令+季节+寒暖燥湿+调候（四时五行性质展开）
→ QTBJ 身弱只是特定日干×月令×调候结构中的条件变量，不得定义 ZIPING 通用身弱判定器。

### 三命通会（SMTH）——日时断语是条件变量，不是判定规范
- 194 条中大量为「某日+某时+某月+干支组合+断语」
→ 「某命身旺」≠「三命通会规定身旺算法」；日时断语身旺是条件变量。

## 三、概念清单（可建）vs 触发公式（禁止）

### 可建立的概念（六部证据已现）
得令 / 失令 / 得時 / 無根 / 有根 / 無氣 / 得劫 / 得垣 / 持勢

### 禁止 Admission 的统一触发公式
- 得令 → 身旺 ❌
- 失令 → 身弱 ❌
- 得令+得地 → 身強 ❌
- 得令+得勢 → 身旺 ❌
- 失令+無根 → 身弱 ❌
（以上必须逐条回到具体经典/章节/语境验证后才可裁决）

## 四、Strength Engine 多维状态硬规则（本批 APPROVE）

禁止：is_strong=true / is_weak=false

至少保留以下中间状态维度（各维度独立判定，由具体经典 Rule 消费）：

| 维度 | 值域草案 |
|---|---|
| seasonal_state | IN_COMMAND / OUT_OF_COMMAND / TRANSITION / UNDETERMINED |
| root_state | NONE / WEAK / NORMAL / STRONG / EXCESSIVE / UNDETERMINED |
| qi_state | HAS_QI / NO_QI / UNDETERMINED |
| momentum_state | GAINED / NOT_GAINED / UNDETERMINED |
| support_state | NONE / WEAK / NORMAL / STRONG / EXCESSIVE / UNDETERMINED |
| drain_state | NONE / WEAK / NORMAL / STRONG / EXCESSIVE / UNDETERMINED |
| control_state | NONE / WEAK / NORMAL / STRONG / EXCESSIVE / UNDETERMINED |

判定链（任一经典自己的 Rule 决定，非跨书统一计算器）：
```
CLASSICAL RULE（绑定书×章节×source）
        ↓
中间状态（seasonal/root/qi/momentum/support/drain/control）
        ↓
strength_state（附录 L 六级容器）
```

## 五、附录 L 六级枚举限制说明（Human 定稿）

> 六级枚举（STRONG/SLIGHTLY_STRONG/NEUTRAL/SLIGHTLY_WEAK/WEAK/UNDETERMINED）
> 是**工程状态容器**，不代表六部经典共享同一套强弱判定算法。

六经典不同规则 → 各自映射到容器 → **不得**误以为六经典使用同一判定标准。

## 六、得势单独钉查（本批 PENDING，下一步执行）

- 六部原文中的「得勢」出现位置与语境（不许用现代命理「得令/得地/得势」三分法倒推）
- 「得垣」「持勢」与「得地」「得勢」是否同义，必须六部原文裁决后才能进入 BOT-ZIPING
- 「得時」「得令」「得勢」三者关系待原文钉死

## 七、执行记录

- 2026-09-16：Human 裁决落档（本文件）；六部「得令/失令/得時/得地/得勢/得垣/持勢/無根/有根/無氣/得劫」扫描待跑
