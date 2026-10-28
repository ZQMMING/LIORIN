# PATCH-003A-R1-04：SOURCE_ALIGNMENT（人元用事 概念/机制/schedule 三层对齐）

> 日期：2026-09-16 ｜ Human 裁决：R1-04 = SOURCE_ALIGNMENT（非 SOURCE_MERGE），允许 CONFLICT
> 数据：`governance/r1_04_source_alignment.json`

## 一、对齐原则（Human 锁定）

- 三层分离：CONCEPT ≠ MECHANISM ≠ SCHEDULE
- 允许结果：`ALIGNED / PARTIALLY_ALIGNED / CONFLICT / NOT_FOUND`
- CONFLICT 是有效裁决结果，不是失败
- SOURCE_PRIORITY 只表示证据/执行资格层级，**不代表某书高于另一部经典**

## 二、三层对齐矩阵

### LEVEL-1 概念层（人元/藏干/用事/司令 概念存在性）

| 书 | 状态 | 证据 |
|---|---|---|
| YHZP | ALIGNED | 030-001 論三元「子中所藏癸水為人元」；049-002 四時用事 |
| PZZQ | PARTIALLY_ALIGNED | 无「人元/用事」词，以「八字用神專求月令」表达 |
| DTS | ALIGNED | 015-003 正文「人元用事之神，宅之向也」 |
| QTBJ | ALIGNED | 48 条司權/司令/當權体系 |
| SMTH | PARTIALLY_ALIGNED | 「當權」零星诗诀 |
| SFTK | ALIGNED | 123-002「支中所藏者為人元」+ 36 条當權体系 |

### LEVEL-2 机制层（时间位置→地支→藏干→用事主体→取用）

| 书 | 状态 | 证据 |
|---|---|---|
| YHZP | ALIGNED | 056-001 12 月分段 + 049-002 四时用事 |
| PZZQ | ALIGNED | 月令取格机制（用神專求月令） |
| DTS | ALIGNED | 015-004 令星用事「知此可以取用，亦可以取格矣」 |
| QTBJ | ALIGNED | 逐月司權标注 |
| SMTH | PARTIALLY_ALIGNED | 當權零星，未成体系 |
| SFTK | ALIGNED | 當權/司權体系 + 十干逐月歌 |

### LEVEL-3 schedule 层（精确时间表——仅此层裁决执行资格）

| 书 | 状态 | 证据 | eligibility |
|---|---|---|---|
| YHZP | **ALIGNED** | 056-001 12/12 月完整时间表 | **CORE_RULE_ELIGIBLE** |
| PZZQ | NOT_FOUND | 无精确用事日程 | FAIL_CLOSED |
| DTS | PARTIALLY_ALIGNED | 寅月三段（015-004）+ 子时（015-006） | CANDIDATE_RULE |
| QTBJ | PARTIALLY_ALIGNED | 仅午月上半月/下半月粗分 | CANDIDATE_RULE（粗分） |
| SMTH | NOT_FOUND | 无时间表 | FAIL_CLOSED |
| SFTK | NOT_FOUND | 當權体系无精确日程 | FAIL_CLOSED |

## 三、SCHEDULE_VARIANT（source-specific schedule，Human 拍板并存）

### 寅月：CONFLICT（两套体系，禁止合并）

| | YHZP-056-001（A） | DTS-015-004（B1） |
|---|---|---|
| 立春後1-7日 | 丙火 | 戊土 |
| 8-14日 | 丙火 | 丙火 |
| 15-23日 | 丙火 | 甲木 |
| 24日~驚蟄 | 甲木 | 甲木 |

禁止：平均 / 投票 / 优先级覆盖 / 拼接成第三套（003A-RULE-10）。

### 子时：PARTIALLY_ALIGNED
- DTS-015-006（B1）：前三刻三分壬水，後三刻七分癸水
- 其余五书 NOT_FOUND
- **禁止**：从任氏曰「余时亦有前后用事」反推具体日数（任氏解释 ≠ 原典 schedule）

### 其余 11 时支：NOT_FOUND → FAIL_CLOSED
- 禁止现代规则补全
- 禁止从月令 schedule 类推
- 禁止从任氏曰反推

## 四、SOURCE_PRIORITY（证据资格层级，非书的高下）

| source | 书 | grade | schedule 覆盖 | eligibility |
|---|---|---|---|---|
| YHZP-056-001 | YHZP | A | 12/12 月 | CORE_RULE_ELIGIBLE |
| DTS-015-004 | DTS | B1 | 寅月 | CANDIDATE_RULE |
| DTS-015-006 | DTS | B1 | 子时 | CANDIDATE_RULE |
| QTBJ-018-001 | QTBJ | A | 午月上半月/下半月 | CANDIDATE_RULE（粗分） |

## 五、执行状态

```
R1-01  attribution 细分        ✅ PASS（61540843）
R1-02  原注/任氏/后世 定层      ✅ PASS（61540843）
R1-03  12月×12时 交叉验证       ✅ PASS（16ae87ec）
R1-04  SOURCE_ALIGNMENT        ✅ PASS（本提交）
R1-05  28×6 VERIFIED_SCOPE     ⏳ 下一步（Human 确认后启动）
PATCH-003B                      ⏳
```

## 六、结论

- 「人元用事」是**共同概念**；「用事日程表」是 **source-specific schedule**
- 概念层六部 ALIGNED/PARTIALLY_ALIGNED，机制层一致，schedule 层 YHZP 唯一完整（A）、DTS 局部（B1）、其余 NOT_FOUND
- 寅月 CONFLICT 已冻结为双 variant 并存，不做任何算法合并
