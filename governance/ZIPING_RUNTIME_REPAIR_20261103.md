# 子平运行契约修复：第一批（待完整环境验收）

核查日期：2026-11-03（北京时间）。
基线：LIORIN feature/ziping `2c576a9313d9961b888b72b8d68a10222fa1a428`。
工作分支：`codex/ziping-runtime-contract-repair`。

## 范围

本批只修调用契约、五行反查错值与验收可信度，不调整 severity、成党门槛、候神力级、吉凶裁决优先级，不改经典原文、证据或 Golden 期望。
这不是全引擎审计封板，也不是预测准确性认证。

## 已复现并修复

1. 病药路由读取 facts.p1_bing，但已追踪的原局主入口没有提供本次 P1 结果。
   给 resolve_yongyao / _yongshen_routing 增加可选关键字 bing_list；原局、分层调试、production_entry 和岁运入口传入实际病机列表。
   显式空列表优先于旧快照，旧三参数调用仍可运行。
2. 路由的克病反查把土映射到水。复用既有 KE_BACK（土→木），消除局部错误副本。
   独立五行生克反例在修改前失败、修改后通过。
3. 原局计算了转归 zg，却把原始 debate 传给用药层；岁运与 production_entry 已使用 zg。
   原局及 walk_layers 改消费 zg，避免已经转药的候选仍作为次病排斥用药。
4. final_gate 改用当前解释器和仓库相对路径；区分 PASS/FAIL/SKIP/BLOCKED。
   缺脚本、子进程失败、非零崩溃数、跳过以及超时均不能形成整体通过。
5. 增加权威事实源预检；排盘依赖缺失不能靠旧表兜底获得正式验收通过。
6. 判据矩阵和锚点脚本移除本机绝对根路径；未改变它们的断言。

## 执行结果

- 新增运行契约测试 3 项：通过；修改前复现 2 失败、1 错误。
- 新增验收闸门测试 6 项：通过。
- 编译检查与 git diff --check：通过。
- 本轮指定验收入口 17 项检查：10 PASS / 4 FAIL / 1 SKIP / 2 BLOCKED，整体退出码 1。
  数字是套件/预检项数量，不是案例准确率，也不是全仓所有测试数。

失败与阻塞：
- 权威排盘源不可用：vendor 被忽略，分支 src/tongshu 仅有 __init__.py，缺 tongshu.facts 等真实依赖。
- test_yuanjuan_matrix 与 test_dayun_xiji_yongshen_golden 因该依赖失败。
- test_criteria_anchors 检测到输出切片库 0 条；不能用旧锚点产物证明当前原文已加载。
- 古命例测试因已移除的 unified_overview 主动跳过。
- p0_v2/_verify_20261009/run_all.py 不在当前提交中。
- regress_gate：ge_diff=0 / xi_diff=0 / winner_diff=5，未修改旧基线凑绿；六书分布为空，不能作为全量语料回放。

## 100 盘修改前后比较（仅工程影响检查）

100 盘均返回结果，格局输出和主药五行全部不变。
6 盘结构化输出有变化，其中 5 盘新增原先为空的 winner；2 盘用药相关输出变化（有重叠）。

| 四柱 | 旧 winner | 新 winner | 主药 |
|---|---|---|---|
| 丙子 丙申 丙子 丙申 | 空 | 土 | 土，未变 |
| 壬辰 甲辰 庚午 丙戌 | 空 | 木 | 木，未变 |
| 壬子 壬寅 庚申 庚辰 | 空 | 土 | 水，未变 |
| 丙戌 壬辰 丙申 丙申 | 空 | 火 | 木，未变 |
| 癸酉 乙卯 壬戌 乙巳 | 空 | 金 | 金，未变 |
| 甲戌 辛未 乙丑 乙酉 | 火 | 火 | 木，未变；候选输出变化 |

重要限制：本环境 _HIDDEN_GUARD.checked=False，paipan.raw_facts.l0_chart={}。
上述 100 盘通过了现有旧表兜底，不能证明权威事实链、经典一致性或现实吉凶正确。
本次新增预检把这一情况作为正式验收阻塞。

## 后续顺序

1. 从原开发环境恢复并固定子平实际使用的排盘依赖版本及测试资源；不从其他分支随意拼装以求测试通过。
2. 补全语料/切片资源与全量回放入口，原典与 Golden 内容不变。
3. 在完整环境重跑当前补丁和 100 盘差异；逐盘复核新增 winner，尤其 winner 与 primary 不同的两盘。
4. 再审查切片条件与硬编码触发分歧、未知传播、跨域主病/并列处理、程度阈值及岁运增量重评。
5. 规则正确性与真实吉凶/应期有效性分开验收。引擎保留完整判断，产品表达限制在前端处理。

## 运行

```bash
python -X utf8 tests/test_runtime_contract_repair.py
python -X utf8 tests/test_final_gate_contract.py
python -X utf8 tests/final_gate.py --json-out /tmp/ziping_acceptance.json
```

最后一条在缺资源或存在未解释差异时应返回非零。Windows 可将 --json-out 改为本机有效输出路径。
