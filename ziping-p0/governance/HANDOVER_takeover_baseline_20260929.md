# 接手基线核对（2026-09-29）

> 目的：接手 shuntian-ziping-p0（feature/ziping）时的第一道验收。
> 工具链：主仓库自带 venv `D:\wisdom-main\wisdom-main\.venv\Scripts\python.exe`（py 3.11.16 + pytest 9.1.1）。
> 本 worktree 的 git 元数据已断（指向不存在的 `D:\shuntian\.git`），无法用 git diff，故全部以文件态 + 实跑为准。

---

## 一、主链实测（活，非文档）

1983 命例（癸亥 壬戌 乙未 壬午）跑 `production_entry`：

```
gate_passed: True
L1 queries: 40 条（supported=18 / not_supported=22 / unknown=0）
wuxing_power 注入: True
zhenglun 五段: bingyao / debate / zhuangui / climate_static / yongyao 全活
```

**口径提示**：docs/governance 多处写「38 Query」，`daymaster_power_queries.run_queries`（第 150 行）实际返回 **40** 条（qtbj/climate 等 2 条是后加）。接手以 40 为准，文档待回更。

---

## 二、两份 P0 欠账案：文档过期，已销账

| 案 | 文档声称 | 实测真实现状 | 结论 |
|---|---|---|---|
| 案1 transit_power 浮点依赖 | 第45行调已删 `build_wuxing_power`，被 try 吞，大运流年瘫痪 | 第45行是 `_ling_state` 内无关条件；真调用源是 `_build_pure_power`（transit_power.py:311），纯规则无浮点；`build_wuxing_power` 现为 `wuxing_power.py:7` 布尔 shim；`dayun_summary.py:83`/`liunian_summary.py:54` 活 import 无 try 吞 | **已修复，文档过期** |
| 案2 production_entry power 链 | 第62行 import 已删 `daymaster_power_queries` → `run_queries` 静默瘫痪，必走 except | `daymaster_power_queries.py` 存在且 FROZEN，`run_queries` 正常；`_build_l1_queries`（含62/74行）**无任何 try/except 包裹**，若 import 失败会炸出而非静默 | **已修复，文档过期** |

两份 doc 已加「🟢 销账」标记（2026-09-29 接手核对），正文标注「描述的是 2026-09 前旧状态，现已失效」。

---

## 三、本次实际修复的缺陷（唯一活缺陷）

`engines/production_entry.py` 算辩解 except 块（208–213 行）调用 `_tb.print_exc(file=sys.stderr)`，但全文件从未 `import sys`。后果：一旦算辩解链（bingyao/debate/zhuangui/climate/yongyao）任一处抛异常，该 handler 会先抛 `NameError: name 'sys' is not defined`，破坏"保留 traceback 到 stderr"的降级行为。

**修复**：文件顶部（第 11 行）补 `import sys`。已验证：
- 正常 import 干净；
- 模拟 `build_bingyao_layer` 抛 RuntimeError 时，handler 正常降级、`zhenglun` 得到 `{error, traceback}`，不再 NameError。

---

## 四、全量回归基线（接手前即存在）

95 个测试接手前 **8 个失败**。经逐项取证后，本轮已清 2 项、定 4 项为边界、余 2 项待原典裁决：

### 本轮已修复（低风险、A 类明确缺陷）
| 测试 | 修复 | 结果 |
|---|---|---|
| test_dayun_xiji_yongshen_golden | `to_root_grade` 签名漂移：`root_grade_boundary.py` 加 1 参便捷重载 + `yongshen_engine.py` 补 import | 6 fail → **2 fail**（余 2 为「身旺用财官」期望值，待原典核） |
| test_unified_overview_golden | 清除第 2 行行首混入的 `\ufeff` BOM | `SyntaxError: U+FEFF` 消除，文件可编译 |

### 取证判定为「有意删除边界」（INTENTIONALLY_ABSENT，非误删）
4 个 golden 测试 import 的 `unified_overview` / `zhonghe_structure` 已被 P0 有意删除：
- 决定性证据：`tests/test_unified_overview_golden.py` 第 1 行自述「冻结/已删除代码引用：zhonghe_structure/unified_overview已删除，本文件不再跑」
- 全项目 grep：这两个符号**只在 4 个测试文件**出现，`engines/`、`p0_v2/`、`scripts/` 无任何活代码引用
- 其真实能力散在 `meta_unified_output.py` / `authority_matrix.py` / `dangzhong_counter.py`，并未独立成 `engines/common/unified_overview.py` 文件
- 涉及：`test_ancient_case_golden` / `test_new_vs_old` / `test_zhonghe_structure_golden` / `test_unified_overview_golden`

**处置（已按用户裁决方案 1 落地，2026-09-29）**：4 个测试各加 `try/except ModuleNotFoundError` 守卫，缺模块时打印 `SKIP …已被 P0 删除, 本 golden 冻结` 并 `sys.exit(0)`（跳过不计 fail）。未重建任何被删模块，未碰 NOT_AUTHORIZED 封板。→ 4 个测试现在 `exit=0`。

### 当前回归基线（2026-09-29 接手后）
95 测试 = **91 pass / 4 fail**。余 4 fail 全部为接手前旧债，无一由本轮引入：

| 测试 | 现象 | 定性 | 处置 |
|---|---|---|---|
| test_real_case_smoke | 缺外部数据 `D:\顺天系统资料\shuntian\cases\global_mingli.json` | 环境（随 `D:\shuntian` 丢失） | 待用户提供数据路径，否则 skip |
| test_dayun_xiji_yongshen_golden | 「身旺用财官」用神 primary 不存在 / 五行期望水木 | 期望漂移 | 待原典核四态，不硬改期望 |
| test_bingyao_layer_golden | Case1「财多身弱」有病断言不符 | 期望漂移 | 待原典核四态 |
| test_special_pattern_golden | 期望 `[从X/CANDIDATE]` 得 `[从X格/CONFIRMED]` | 期望漂移（CANDIDATE/CONFIRMED 口径） | 待原典核四态 |

> 长期规划 v1.0 写的「91/91 全绿」是 2026-09-21 旧基线；当前代码/数据已漂。
> 根目录 `temp_delete_*.txt`（155/127/419 行）是未清的 scripts 待删清单。

---

## 五、环境事实

- git 历史本地已丢（worktree 指向 `D:\shuntian\.git` 不存在，全盘无 shuntian packfile/refs）。恢复需 GitHub remote `feature/ziping`。
- 原 `D:\shuntian\.venv` 丢失，复用主仓库 `.venv` 可跑。
- 8 旧债中「缺模块 unified_overview / zhonghe_structure」「缺外部数据」「to_root_grade 未定义」需逐个判断：是 P0 误删（活链断了）还是真未做（UNKNOWN 边界）——**不可直接补造**，须先取证再定四态。
