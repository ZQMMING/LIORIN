# ZiPing 引擎交接审计（HANDOVER）

> 目的：让下一个接手的 AI 不跑偏、不原地转圈。读这一份即可接上。
> 最后更新基线：HEAD `40f067cc`，分支 `feature/ziping`，worktree `D:\shuntian-ziping-p0`。

---

## 0. 工具链事实（照抄，别猜）

- 仓库：`https://github.com/ZQMMING/wisdom`，分支 `feature/ziping`，worktree `D:\shuntian-ziping-p0`
- Python 解释器：`D:\shuntian\.venv\Scripts\python.exe`（必须用它跑测试，别用系统 python）
- 推送：PowerShell 先 `$env:GIT_TERMINAL_PROMPT="0"; git push origin feature/ziping`
- 测试：每个 test 末尾 `sys.exit(1 if fails else 0)`；全量回归用 `Get-ChildItem tests -Filter "test_*.py"` 逐个跑，统计非零退出码
- 原典 evidence：`registries/evidence/pzzq_evidence.jsonl`，字段 `quotation`，**繁体关键词**检索（運/衝/剋/財/滅）
- 中文文件用 UTF-8 读写；PowerShell 控制台显示乱码是终端问题，不代表文件坏

---

## 1. 这个项目在做什么（一句话）

把《子平真诠》等六经经典子平法，按"原典给什么，机器只做什么"的原则，做成**可反查、三态、不偷造结论**的推理引擎。
核心信条：**原典边界 = 工程授权边界。原典没给无歧义机器公式的，宁可 UNKNOWN，绝不伪造。**

---

## 2. 主链分层（自下而上，每层已封板）

```
L0 Fact（可验证事实，不出格局/旺衰）
  ↓
三态推理（Condition Evaluator → Router → Bundle → Candidate State）
  ↓
八格 Entry → Candidate → Rule 输入契约（172 A~H 逐格独立）
  ↓
Established Relation（173 十个，仅"结构具备"，三态）
  ↓
岁运 Relation（178/183/184/185，纯结构事实 + provenance）
  ↓
Judgment Producer（provenance fail-closed）
  ↓
Interpretation Producer
```

---

## 3. 正式架构边界 = NOT_AUTHORIZED（永久封板，不是技术债）

**以下四层禁止任何人/任何 PATCH 重新打开、禁止用评分/计数/权重补全：**

| 边界 | 封板 PATCH | 内容 |
|---|---|---|
| 综合身强/身弱、旺衰合成器 | 160 | 原典只有多维观察维度，无机器合成公式 |
| 财太露 | 161 | 禁 count；"露"≠"忌"；无固定阈值 |
| 有效关系/制化成立 | 174 | 10 个关系有效性全卡旺弱层 |
| 岁运缓急轻重 | 179 | 位置只存证，不计算轻重 |
| 伏吟全局 Boolean / 返吟 / 岁运压日 / pressure_on_day | 180/182 | 跨书定义不统一，无唯一机器公式 |

**铁律（违反即跑偏，逐条背）：**
- 不数值化旺衰、有根≠身强、得令≠身强
- UNKNOWN 不降级、supported 不参与硬判
- 最多≠最旺、root_weight 不直出身强
- Entry≠格成、配合前提≠配合成立、同现≠成立、成立≠格成
- 七杀≠正官、见财≠官格 blocked、财印同现≠贪财破印
- 不评分、不加权、不多数决
- 伏吟/刑破害等结构 ≠ 凶；结构 ≠ 作用 ≠ 吉凶

---

## 4. 当前 Relation Fact 完整清单（relation_178.py 实际输出）

输入：`yun={'decade':[干,支],'year':[干,支]}`，`pillars={'year','month','day','hour':[干,支]}`

| relation 名 | 含义 | 来源 PATCH |
|---|---|---|
| 天干五合 | 运干×命干五合 | 178 |
| 运干生命干 / 运干克命干 | 运干×命干五行生克（同类不记） | 185 |
| 地支六合 / 地支六冲 | 运支×命支 | 178 |
| 三合 / 三会 | 运支参与命局成局 | 178 |
| 三刑 / 六害 / 六破 | 运支参与命局成结构（自刑仍不建） | 184 |
| 透清 | 运干透命局藏干 | 178 |
| day_year_same | 流年干支==日柱干支（日年相并） | 183 |
| yun_year_same | 流年干支==大运干支（岁运并临） | 183 |

**全部带 provenance（yun_type / natal_pillar / branches/stems），全部只表结构，无一字判祸福。**

---

## 5. 已封板 NOT_AUTHORIZED 的岁运项（别再挖）

- 岁运压日 / 返吟 / 伏吟全局 Boolean / pressure_on_day（180/182）
- 运支五行生克（会滑向支旺衰，撞 160）
- 天干相冲（甲庚/乙辛，子平正典未授权为运×命结构）
- 运干×运支同柱合并作用（179 干支有别已锁）

---

## 6. 每个新 PATCH 的标准工作流（照这个走）

1. **先只读原典**：grep evidence 找原文，确认原典到底说什么、给没给无歧义机器公式
2. **先核代码现状**：git log + 读相关 .py，别在已有实现上重复造
3. **判定四态**：A 原典明确可机器化 / B 原典明确但缺 L0 Fact / C 综合判断暂不机器化 / D 无授权保持 UNKNOWN
4. **只做 A 类**：拆成原子结构 Fact，带 provenance
5. **写 golden 测试**：正例 + 反例（不构成时必须 False）+ 锁死项（不产出吉凶/格成/身强弱）
6. **跑全量回归**：必须 0 失败
7. **落 governance 文档**：范围/输出/锁死/测试
8. **commit + push**，commit message 写明 PATCH 号和边界

**注意测试坑**：旧测试 `test_yun_natal_178.py` 最后会扫描每条 relation 的完整字符串是否含"喜/忌/吉/凶"。新写的 note **绝不能出现这四个字**，改用"祸福/作用/轻重"等词。

---

## 7. 下一步候选（等用户裁决，别自己挑）

- 岁运结构原子主干已挖完（第 4 节矩阵），再挖就撞 NOT_AUTHORIZED 墙
- 可选项：(A) 落 PATCH-186 总结 governance 封岁运结构原子专项；(B) 转外格新面；(C) 其他用户指定方向

---

## 8. 关键文件索引

- `engines/common/relation_178.py`：岁运 Relation（178/183/184/185 全在这一个函数里）
- `engines/common/l0_fact_builder.py`：L0 主文件（含 163 刑破害表、root_weight、changsheng_direction、各 entry）
- `engines/common/{entry_candidate_contract, *_rule_contract}.py`：八格契约
- `governance/`：38 份封板文档，最新 yunshi_* / fuyin_* / press_on_day_* / yun_*_184 / 185
- `tests/`：50 个 test，全绿
