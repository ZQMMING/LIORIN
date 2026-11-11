# 引擎交付状态汇总（2026-11-10）

> 统一接线阶段收口状态一览。分支 `feature/luming-engine`，HEAD `f73d34c6`。
> 每项附证据指针；登记项=宁缺勿猜/fail-closed 口径下的未决输入，非缺陷。

## 1. 各引擎状态

| 引擎 | 算层/解层 | 生产接线 | 回归证据 | 遗留登记 |
|---|---|---|---|---|
| 紫微 ziwei | 收口（17040 盘 parity；解层 9 出口+49 投影；闰月双口径） | **✓ 默认 native**（e04a6bcf：Engine/Adapter 切换+source 参数化+流日 Z76 原生路径+Golden 基线重录 6e4a1323） | `-k ziwei` 608 passed/1 skipped | luck_branch 流日命宫 iztro 内部算法未核实→置空；to_dict 展示层差异；p014 ratified 白名单含 native |
| 盲派 blind | 收口（真值 13/13+应期 6/6+引擎快照 258769fec；golden blind hash 10d1dab6 跨进程稳定 V7.202） | **✓ 三层链**（f73d34c6：analyze_from_chart S0 入口禁重排盘+ComputeResult.blind_yingqi/blind_judgment+判定层 judge_blind） | `-k blind` **230 passed/3 skipped**；truth 13/13+event 6/6；隔离 8/8 | mapping_registry SOCIAL 白名单失败=GPT 在途树状态（干净 HEAD RuleLoadError+双后端 claims 0 差证非我方）；全测试套件跑批时 blind 主链 setUpClass(for_demo) 受前置测试污染（二分排除 canonical_meta/mapping_registry 直杀，属全树测试隔离问题=GPT 在途，合线后治理） |
| 河洛 heluo | 收口（真值 4/4+384 爻逐字 0 不符+卷十锚点；D-006~D-023 修毕） | 已接（流年/流日/流时链式） | `-k "heluo or meihua"` 650 passed | DT-0380 等少量配合级 |
| 黄历 huangli | 收口（D-01 甲申↔火水未济锚点；1900-2100 双库日柱/节气 0 差异） | 已接（SignalEngine 消费 get_day； ziwei 流日日柱同锚复用） | `-k huangli` 67 passed | **宜忌（活动吉凶）层待语料样本**——登记，外部输入 |
| 六爻 yijing | 装卦层收口（京房纳甲 64/64） | 装卦可产 | 64 卦对全过 | **断课层待《增删卜易》原典入库**——登记，外部输入 |
| 梅花 meihua | 维持 | — | — | 用户叫停（m04187），不接线 |
| 子平 ziping | **V7.206**（八格成败+五域+用神判据层 V7.201-205+合对柱位归属修复 f2fc0b03） | **✓ BZ-FNDR-15 契约**（compute_stage L243 run_ziping_judgment→composer→atomic_claims） | 全量 `-k ziping` **1912 passed/15 failed**（=8 GPT 基线+7 登记契约冲突，0 新增；用户病药合对柱位修复 2026-11-11 收平 GPT medicine_he_positions 1 项） | 见 §2 |

## 2. 子平当前精度（真值对照，非自洽）

- **12 原典案 12/12 全平**（`scripts/ziping_rule_audit.py`）：含 龙济光煞刃成（PZZQ L1223）、石友三成中有败（L1220 合去精化）、谭延闿败中有成（L1210 救应→CZP，用神=食神）、王克敏食伤制煞成（V7.190）、蔡元培金水伤官/财通关豁免、乾隆阳刃成。
- **40 随机盘**：取格差 **1/40**（甲午己巳壬午壬寅 V7.34 无根口径，登记）+ 特格族 2（核验器无判据）；成败差 **2/40**（乙未丁亥丙申辛卯 身强 metric 分歧、丙寅己亥丁卯辛亥 破的效力——均登记配合级）+ 特格族 1（从杀 vs 财格）。
- **PZZQ 覆盖 20/20**（`scripts/ziping_pzzq_replay.py` locked 20 全 HIT；known conflicts **仅 pzzq-018**（从势阈值，special_pattern GPT 热区需协调立项））。V7.201→V7.205 收平五案：020 朱家宝（印重两说判别式 66a81054）/017 朱有卿+019 王某（五合终裁三态 22972a9f）/010 蔡孑民（扶抑扶边 ff6eecd4）/021 己酉丙子戊辰癸亥（佩印×财专向用神归印 db22f308）。
- **e2e claims 域验证**（本轮）：普通盘 4 域 claims（WANGSHUAI/GEJU/YONGSHEN/SHIJIAN）；NE 格盘正确降级只出 WANGSHUAI（fail-closed：NE 不产 GEJU/YONGSHEN claim）；SHIJIAN 仅冲对年出 claim（EVENT_ABSENT 0 claim 口径保持）。
- 版本链：V7.180→V7.205（审计 `docs/audit/ZIPING_CLASSIC_RULES_20261108.md` §1-26 全量记录）。

## 3. 跨引擎口径登记（已知并存差异）

- **小运起法**：禄命线=古法（男丙寅顺/女壬申逆，用户 2026-10-21 亲裁）vs 子平线=醉醒子法（时柱起/年定逆顺，COV-006 裁决 8bd7af1a）。同盘答案不同；统一须独立立项（厄会②消费面重验）。
- **子平线小运消费边界**：COV-013-2 fail-closed——只产时间线，不参与喜忌/吉凶断语/事件触发（守卫测试锁定）。
- **SHIJIAN 事件域**：V7.193 治理放行（method audit 六项 PASS；结论级 fail-closed 保留——EVENT_ABSENT 不产 claim）。

## 4. 挂起与外部依赖

1. ~~ge_jie_layer.py 收编合线~~ **已完成**（2026-11-11 用户授权整体单提交 `e01fb1eb`，三文件 GPT 硬化+我方 V7.197-199b 全保留，放行门全过；拆分不可行实证 §二十六.9）。
2. 黄历宜忌层：待语料样本。
3. 六爻断课层：待《增删卜易》原典入库。
4. ~~pzzq-018 从势阈值~~ **格层已收平**（2026-11-11 V7.207 `b414f2c6`：合线落地即按 §二十六.10 验证判据落码 special_pattern 阴干从势通道+ge_jie_layer 消费门+V7.207b 印通道 span 终裁——首版裸 partner-in-stems 误判 017 遥隔印被合去 replay 19/20 翻车，复用 V7.203 `_wuhe_span_state` 修复；018 → 从杀格 CONFIRMED/CHENG「即从木」L182 亲证；阎锡山/许世英/004/辛未 正反例锚全过）。**用神级保持配合级 conflict**：判词「从木」=格局定性非用神五行，沈未亲证；engine 从杀格喜神=财（水，PZZQ5000 既有锚），KNOWN_CONFLICTS 维持 {pzzq-018}（注释升级，§二十六.11）。010/017/019/020/021 均已收平（V7.201-205，见 §2）。
5. ~~golden_replay blind hash 时变待审计~~ 已结案（2026-11-10 V7.202，勘误=PYTHONHASHSEED Set 顺序噪声非时变；修复后 10d1dab6 稳定，提交 296b537b）。同日 V7.201-205 收平 pzzq 五案（020/017/019/010/021，replay 15→20 全 HIT，提交 66a81054/22972a9f/ff6eecd4/db22f308）。

## 5. 提交链（本轮统一接线阶段）

`8bd7af1a`（COV-006 醉醒子小运）→ `9a224301`+`3fbe854d`（V7.199b 核验器+40盘收敛）→ `e04a6bcf`（紫微接线）→ `f73d34c6`（盲派接线）→ `f291a42b`（本文档）→ `66a81054`（V7.201）→ `296b537b`+`04362011`（V7.202+勘误）→ `22972a9f`（V7.203 五合终裁）→ `ff6eecd4`（V7.204 扶抑扶边）→ `db22f308`（V7.205 佩印×财专向）→ `96e2caa6`（拆分实证）→ `50df2036`+`d323d2b7`+`e4a7c0b1`（018 判据 v3+勘误）→ `30c7d4e1`（V3 残留清理）→ **`e01fb1eb`（三文件合线）→ `b414f2c6`（V7.207 阴干从势）→ `efb6256e`（§二十六.11）**。

## 6. 全测试套件健康快照（2026-11-10 Round 27，全树跑批）

`python -m pytest tests/ -q`：**5434 passed / 135 failed / 92 errors**（406 subtests passed）。失败分布由 GPT 在途子系统主导：test_profile_gate 25、test_m2b_evidence 23、test_m2a_migration 20、test_matcher 15、test_api 14、test_edition_registry 13、test_canonical_meta 10、test_mapping_registry 9、test_k2g_state_engine 9、test_frontend_integration 9、test_rule_lifecycle 9 等。子平失败 = 9 GPT 基线 + 7 登记契约冲突（与 `-k ziping` 口径一致，0 新增）。我方盲派主链隔离 8/8 通过，全树跑批时 setUpClass 受前置测试污染（二分排除 canonical_meta/mapping_registry 直杀；全树测试隔离治理归树所有者，GPT 合线后处理）。golden_replay 六引擎全 [OK]（新进程复验 blind 10d1dab6 与 V7.202 重录基线一致）。
