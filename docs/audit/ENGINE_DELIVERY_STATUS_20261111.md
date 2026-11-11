# 引擎交付状态汇总（2026-11-11 · V2）

> 取代 `ENGINE_DELIVERY_STATUS_20261110.md`（归档保留，其数字均属 2026-11-10 Round 27 口径）。
> 2026-11-11 原交付快照：分支 `feature/luming-engine`，当时 HEAD `5b5ee56b`；此后新增晚子时测试 `6021eaf6` 和修复 `45e2653b`。接手时重新核对当前 HEAD 与工作树。
> 每项附证据指针；登记项 = 宁缺勿猜 / fail-closed 口径下的未决输入，非缺陷。
> 治理规则见根目录 `AGENTS_V2.md`。

## 0. 本版相对 20261110 版的实质变化

1. **子平 V7.206 → V7.207**：pzzq-018 格层收平（`b414f2c6`）。
2. **三文件合线完成**：`e01fb1eb`（我方 V7.197-199b 与 GPT fail-closed 硬化整体单提交，行级交错不可拆，见 §二十六.9）——11-10 版挂起项 1 勾销。
3. **新增三登记**：晚子时口径已由用户裁决并修复（§4.1）、V1 权威指针缺失（§4.2）、工作树未归属改动（§4.3）。
4. 全量测试数字**先于合线与 V7.207**，需重跑刷新（§5 注意事项）。

## 产品报告对照说明（2026-11-11）

2026-11-03 产品与技术报告未在本机执行全量测试，其所列状态、救应链缺陷与旧测试数字均是当时材料或待核假设，不能直接升级为当前工作树结论。本文件保留历史快照；对外开放每个引擎和子功能前，应分别核实**实际入口、规则依据、边界/反例测试、版本及失败记录**，建立能力清单。接线完成、测试通过和算法经原典验收是不同状态。

报告特别提出核查救应入口是否真的命中破格、十神共现是否造成假阳性、阻断条件及证据不足时是否保留不可评价；这些是**核查项，不是本次新确认的当前缺陷**。不要以单个案例调整算法或改变六经典冻结版本。

计算事实、传统判断和现代解释须可追溯且独立展示；跨流派分歧不得投票抹平。API 的能力状态和版本字段应先与实际代码核对，再制定合同，不能把报告示例作为现有接口。NFC 产品规划不解除现有 NFC 三端点冻结；紫微 Canonical 仍按治理文件 BLOCKED 执行。

## 1. 各引擎状态

| 引擎 | 算层/解层 | 生产接线 | 回归证据 | 遗留登记 |
|---|---|---|---|---|
| 紫微 ziwei | 收口（17040 盘 parity；解层 9 出口+49 投影；闰月双口径） | **✓ 默认 native**（e04a6bcf：Engine/Adapter 切换+source 参数化+流日 Z76 原生路径+Golden 基线重录 6e4a1323） | `-k ziwei` 608 passed/1 skipped | luck_branch 流日命宫 iztro 内部算法未核实→置空；to_dict 展示层差异；p014 ratified 白名单含 native |
| 盲派 blind | 收口（真值 13/13+应期 6/6+引擎快照 258769fec；golden blind hash 10d1dab6 跨进程稳定 V7.202） | **✓ 三层链**（f73d34c6：analyze_from_chart S0 入口禁重排盘+ComputeResult.blind_yingqi/blind_judgment+判定层 judge_blind） | `-k blind` **230 passed/3 skipped**；truth 13/13+event 6/6；隔离 8/8 | mapping_registry SOCIAL 白名单失败=GPT 在途树状态（合线后待重跑定性）；全树跑批 blind setUpClass 污染=测试隔离问题，归树所有者 |
| 河洛 heluo | 收口（真值 4/4+384 爻逐字 0 不符+卷十锚点；D-006~D-023 修毕） | 已接（流年/流日/流时链式） | `-k "heluo or meihua"` 650 passed | DT-0380 等少量配合级 |
| 黄历 huangli | 收口（D-01 甲申↔火水未济锚点；1900-2100 双库日柱/节气 0 差异） | 已接（SignalEngine 消费 get_day；ziwei 流日日柱同锚复用） | `-k huangli` 67 passed | **宜忌（活动吉凶）层待语料样本**——登记，外部输入 |
| 六爻 yijing | 装卦层收口（京房纳甲 64/64） | 装卦可产 | 64 卦对全过 | **断课层待《增删卜易》原典入库**——登记，外部输入 |
| 梅花 meihua | 维持 | — | — | 用户叫停（m04187），不接线 |
| 子平 ziping | **V7.207**（阴干从势通道+禄劫NE占位让位从格兜底+印通道 span 终裁 b414f2c6；V7.206 病药合对柱位 f2fc0b03；八格成败+五域+用神判据层 V7.201-205） | **✓ BZ-FNDR-15 契约**（compute_stage L243 run_ziping_judgment→composer→atomic_claims；经 `src\tongshu\reasoning\ziping_bridge.py` 消费根 `engines\production_entry`） | 合线前口径：`-k ziping` **1912 passed/15 failed**（=8 GPT 基线+7 登记契约冲突，0 新增）。**合线 e01fb1eb 后未重跑，见 §5** | pzzq-018 用神级配合级 conflict（判词「从木」=格局定性非用神五行，engine 从杀格喜神=财 PZZQ5000 锚）；40 盘余差见 §2 |

## 2. 子平当前精度（真值对照，非自洽；截至 V7.207）

- **12 原典案 12/12 全平**（`scripts/ziping_rule_audit.py`）：含 龙济光煞刃成（PZZQ L1223）、石友三成中有败（L1220 合去精化）、谭延闿败中有成（L1210 救应→CZP，用神=食神）、王克敏食伤制煞成（V7.190）、蔡元培金水伤官/财通关豁免、乾隆阳刃成。
- **PZZQ 覆盖 20/20**（`scripts/ziping_pzzq_replay.py` locked 20 全 HIT）。known conflicts **仅 pzzq-018**：
  - **格层已收平**（V7.207 `b414f2c6`）：合线落地即按 §二十六.10 判据 v3 落码 special_pattern 阴干从势通道+ge_jie_layer 消费门+印通道 span 终裁；018 → 从杀格 CONFIRMED/CHENG「即从木」L182 亲证；阎锡山/许世英/004/辛未 正反例锚全过。首版裸 partner-in-stems 误判 017 遥隔印被合去 replay 翻车，复用 V7.203 `_wuhe_span_state` 修复。
  - **用神级维持配合级 conflict**：判词「从木」=格局定性非用神五行，沈未亲证；KNOWN_CONFLICTS 维持 {pzzq-018}（注释升级，§二十六.11）。
- V7.201→V7.205 收平五案：020 朱家宝（印重两说判别式 66a81054）/017 朱有卿+019 王某（五合终裁三态 22972a9f）/010 蔡孑民（扶抑扶边 ff6eecd4）/021 己酉丙子戊辰癸亥（佩印×财专向用神归印 db22f308）。
- **40 随机盘**：取格差 **1/40**（甲午己巳壬午壬寅 V7.34 无根口径，登记）+ 特格族 2（核验器无判据）；成败差 **2/40**（乙未丁亥丙申辛卯 身强 metric 分歧、丙寅己亥丁卯辛亥 破的效力——均登记配合级）+ 特格族 1（从杀 vs 财格）。
- **e2e claims 域验证**（合线前口径）：普通盘 4 域 claims（WANGSHUAI/GEJU/YONGSHEN/SHIJIAN）；NE 格盘正确降级只出 WANGSHUAI（fail-closed）；SHIJIAN 仅冲对年出 claim（EVENT_ABSENT 0 claim 口径保持）。
- 版本链：V7.180→V7.207（审计 `docs/audit/ZIPING_CLASSIC_RULES_20261108.md` §1-26 全量记录）。

## 3. 跨引擎口径登记（已知并存差异）

- **小运起法**：禄命线=古法（男丙寅顺/女壬申逆，用户 2026-10-21 亲裁）vs 子平线=醉醒子法（时柱起/年定逆顺，COV-006 裁决 8bd7af1a）。同盘答案不同；统一须独立立项（厄会②消费面重验）。
- **子平线小运消费边界**：COV-013-2 fail-closed——只产时间线，不参与喜忌/吉凶断语/事件触发（守卫测试锁定）。
- **SHIJIAN 事件域**：V7.193 治理放行（method audit 六项 PASS；结论级 fail-closed 保留——EVENT_ABSENT 不产 claim）。

## 4. 新登记悬案（2026-11-11）

### 4.1 晚子时换日：用户已裁决并修复（2026-11-11）

- 用户明确：23:00–23:59 换时柱不换日柱；00:00 起换日柱。晚子时时干按次日日干起，00:00 至 00:59 仍属子时。
- `6021eaf6` 先添加直接调用与适配器边界测试；`45e2653b` 修复直接调用提前换日并修正时间提示。正常路径和直接调用的日柱、时柱已对齐。
- `tests/test_bazi_midnight_policy.py` 与 `tests/test_b02_late_zi_golden.py`：10 passed；覆盖普通日、跨年、闰日。默认真太阳时路径按转换后的有效时间判断边界。
- 此裁决不意味着其他引擎的独立时间政策已逐条核验；禁止擅改 Golden 期望值。

### 4.2 V1 权威指针文件缺失

V1 `AGENTS.md` §4 指向的 `GOLDEN_BASELINE.md`、`REVIEW_BATCH1/2`、`DECISION_LOG_C14_ADDENDUM`（路径 `docs/audit/step*`）在工作树中不存在。历史基线数字（LOADED 20 / PASSED 7 / FAILED 13 等）不得再引用为当前事实。现行权威指针 = 本文件 + `AGENTS_V2.md`。指针重建任务见 AGENTS_V2 §6-P4。

### 4.3 工作树未归属改动

原快照记载分支 ahead 77 / behind 47、约 219 条工作树状态，现已过时。接手时重新检查分支、上游及暂存区，并核对未提交文件归属；含 `engines\common\` 和其他并行改动，不得擅自清理或整体提交。

## 5. 全测试套件健康快照

> ⚠️ Round 27（2026-11-10）数字：**5434 passed / 135 failed / 92 errors**（406 subtests passed）。该口径**先于 `e01fb1eb` 合线与 V7.207**；合线放行门执行中，**合线后须重跑全树刷新本节**。
> 失败分布（Round 27）：test_profile_gate 25、test_m2b_evidence 23、test_m2a_migration 20、test_matcher 15、test_api 14、test_edition_registry 13、test_canonical_meta 10、test_mapping_registry 9、test_k2g_state_engine 9、test_frontend_integration 9、test_rule_lifecycle 9 等（GPT 在途子系统主导，已合线，待重跑定性）。
> 子平失败 = 8 GPT 基线 + 7 登记契约冲突（与 `-k ziping` 口径一致，0 新增；**V7.207 后待重跑**）。
> 全树跑批存在 blind setUpClass 前置污染（二分排除 canonical_meta/mapping_registry 直杀）——可比口径 = 分域跑（AGENTS_V2 §2.4）。
> 2026-11-11 本次八字相关筛选：`python -m pytest tests/ -k "bazi or late_zi" -q`，539 passed / 8 skipped / 1 failed / 5134 deselected；失败为 `test_m2a_migration::TestFiveLayerStructure::test_bazi_cross_verified` 缺少 `backend/data/knowledge/books.json`，未进入晚子时计算。
> 2026-11-11 当前工作树 `python scripts/golden_replay.py --check`：六引擎均完成执行，但 **ziping 哈希 bff58abe3b7eadca → 5ec59965f7312605，不符合冻结基线，整体 FAIL**。子平存在其他未提交改动，原因尚未隔离；不得改基线凑绿。此前六引擎 [OK] 是历史结果。

## 6. 挂起与外部依赖

1. ~~ge_jie_layer.py 收编合线~~ **已完成**（2026-11-11 `e01fb1eb`；放行门全量回归+PZZQ 20/20+40盘基线，§二十六.9）。
2. 黄历宜忌层：待语料样本。
3. 六爻断课层：待《增删卜易》原典入库。
4. pzzq-018：格层已收平；**用神级保持配合级 conflict**（§2）。
5. 晚子时：用户已裁决并修复（§4.1）；跨引擎独立时间政策仍须逐项核验。
6. 前后端联调：`frontend-case` 纯 mock、零 HTTP；后端 `/v1/today` 部分字段自身 mock_until——统一收口计划见 `LIORIN_FRONTEND_SPEC_V2.md`。

## 7. 提交链（统一接线阶段 → 合线收口）

`8bd7af1a`（COV-006 醉醒子小运）→ `9a224301`+`3fbe854d`（V7.199b）→ `e04a6bcf`（紫微接线）→ `f73d34c6`（盲派接线）→ `f291a42b`（11-10 版文档）→ `66a81054`（V7.201）→ `296b537b`+`04362011`（V7.202+勘误）→ `22972a9f`（V7.203 五合终裁）→ `ff6eecd4`（V7.204 扶抑扶边）→ `db22f308`（V7.205 佩印×财专向）→ `96e2caa6`（拆分实证）→ `50df2036`+`d323d2b7`+`e4a7c0b1`（018 判据 v3+勘误）→ `30c7d4e1`（V3 残留清理）→ `e1e7cc89`+`77bdf6a6`（018 立项包+40盘精诊）→ `f2fc0b03`（V7.206 病药合对）→ `a0c19c94`（V7.206 基线）→ `96e2caa6` 前后审计穿插 → **`e01fb1eb`（三文件合线）→ `b414f2c6`（V7.207 阴干从势）→ `efb6256e`（§二十六.11）→ `5b5ee56b`（挂起清单收口，本版基线）**。

> 2026-11-11 追加：`6021eaf6`（晚子时边界测试）→ `45e2653b`（直接调用口径修复及说明）。
