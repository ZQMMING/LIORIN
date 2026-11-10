# 引擎交付状态汇总（2026-11-10）

> 统一接线阶段收口状态一览。分支 `feature/luming-engine`，HEAD `f73d34c6`。
> 每项附证据指针；登记项=宁缺勿猜/fail-closed 口径下的未决输入，非缺陷。

## 1. 各引擎状态

| 引擎 | 算层/解层 | 生产接线 | 回归证据 | 遗留登记 |
|---|---|---|---|---|
| 紫微 ziwei | 收口（17040 盘 parity；解层 9 出口+49 投影；闰月双口径） | **✓ 默认 native**（e04a6bcf：Engine/Adapter 切换+source 参数化+流日 Z76 原生路径+Golden 基线重录 6e4a1323） | `-k ziwei` 608 passed/1 skipped | luck_branch 流日命宫 iztro 内部算法未核实→置空；to_dict 展示层差异；p014 ratified 白名单含 native |
| 盲派 blind | 收口（真值 13/13+应期 6/6+引擎快照 258769fec） | **✓ 三层链**（f73d34c6：analyze_from_chart S0 入口禁重排盘+ComputeResult.blind_yingqi/blind_judgment+判定层 judge_blind） | `-k blind` 228 passed/3 skipped；truth 13/13+event 6/6 | mapping_registry SOCIAL 白名单失败=GPT 在途树状态（干净 HEAD RuleLoadError+双后端 claims 0 差证非我方） |
| 河洛 heluo | 收口（真值 4/4+384 爻逐字 0 不符+卷十锚点；D-006~D-023 修毕） | 已接（流年/流日/流时链式） | `-k "heluo or meihua"` 650 passed | DT-0380 等少量配合级 |
| 黄历 huangli | 收口（D-01 甲申↔火水未济锚点；1900-2100 双库日柱/节气 0 差异） | 已接（SignalEngine 消费 get_day； ziwei 流日日柱同锚复用） | `-k huangli` 67 passed | **宜忌（活动吉凶）层待语料样本**——登记，外部输入 |
| 六爻 yijing | 装卦层收口（京房纳甲 64/64） | 装卦可产 | 64 卦对全过 | **断课层待《增删卜易》原典入库**——登记，外部输入 |
| 梅花 meihua | 维持 | — | — | 用户叫停（m04187），不接线 |
| 子平 ziping | **V7.199b**（八格成败+五域） | **✓ BZ-FNDR-15 契约**（compute_stage L243 run_ziping_judgment→composer→atomic_claims） | 全量 `-k ziping` **1899 passed/16 failed**（=9 GPT 基线+7 登记契约冲突，0 新增） | 见 §2 |

## 2. 子平当前精度（真值对照，非自洽）

- **12 原典案 12/12 全平**（`scripts/ziping_rule_audit.py`）：含 龙济光煞刃成（PZZQ L1223）、石友三成中有败（L1220 合去精化）、谭延闿败中有成（L1210 救应→CZP，用神=食神）、王克敏食伤制煞成（V7.190）、蔡元培金水伤官/财通关豁免、乾隆阳刃成。
- **40 随机盘**：取格差 **1/40**（甲午己巳壬午壬寅 V7.34 无根口径，登记）+ 特格族 2（核验器无判据）；成败差 **2/40**（乙未丁亥丙申辛卯 身强 metric 分歧、丙寅己亥丁卯辛亥 破的效力——均登记配合级）+ 特格族 1（从杀 vs 财格）。
- **PZZQ 覆盖 15/16**（`scripts/ziping_pzzq_replay.py` locked 15 全 HIT；known conflicts 6 案登记：010/017/018/019/020/021）。
- **e2e claims 域验证**（本轮）：普通盘 4 域 claims（WANGSHUAI/GEJU/YONGSHEN/SHIJIAN）；NE 格盘正确降级只出 WANGSHUAI（fail-closed：NE 不产 GEJU/YONGSHEN claim）；SHIJIAN 仅冲对年出 claim（EVENT_ABSENT 0 claim 口径保持）。
- 版本链：V7.180→V7.199b（审计 `docs/audit/ZIPING_CLASSIC_RULES_20261108.md` §1-25 全量记录）。

## 3. 跨引擎口径登记（已知并存差异）

- **小运起法**：禄命线=古法（男丙寅顺/女壬申逆，用户 2026-10-21 亲裁）vs 子平线=醉醒子法（时柱起/年定逆顺，COV-006 裁决 8bd7af1a）。同盘答案不同；统一须独立立项（厄会②消费面重验）。
- **子平线小运消费边界**：COV-013-2 fail-closed——只产时间线，不参与喜忌/吉凶断语/事件触发（守卫测试锁定）。
- **SHIJIAN 事件域**：V7.193 治理放行（method audit 六项 PASS；结论级 fail-closed 保留——EVENT_ABSENT 不产 claim）。

## 4. 挂起与外部依赖

1. **ge_jie_layer.py 收编合线**（GPT 81+ 在途 M 与我方 V7.197-199b 交缠，defer；GPT 提交后按 index-blob 计划合线）。
2. 黄历宜忌层：待语料样本。
3. 六爻断课层：待《增删卜易》原典入库。
4. pzzq-010/017/018/019/020/021 配合级：special_pattern 属 GPT 热区（018 从势阈值需协调立项）。
5. golden_replay blind hash 时变（15 分钟漂移，疑流日/流时锚定当天）待单独审计。

## 5. 提交链（本轮统一接线阶段）

`8bd7af1a`（COV-006 醉醒子小运）→ `9a224301`+`3fbe854d`（V7.199b 核验器+40盘收敛）→ `e04a6bcf`（紫微接线）→ `f73d34c6`（盲派接线）。
