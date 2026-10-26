# 变更日志（Changelog）

本文件记录**对下游有影响**的变更。格式参考
[Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划
- 补切《河洛理数》卷二经文余下段落（S8–S10 影印核定未完成部分）。
- 「逐爻位断语表」（卷之上 L189–199）落地 —— 需原典门槛明确。
- mypy 逐步扩面：目前只对「接线层」核心小模块严格检查，
  原典大模块走宽松档（见 `[tool.mypy.overrides]`）。

## [1.1.1] — 2026-10-26

### 修复
- **★ 证据文本非确定（生产缺陷）**：`yuan_qi.py` 的证据里直接插值 Python
  `set`（`{all_trigrams}`）⇒ 集合顺序依赖 `PYTHONHASHSEED`（每进程随机）
  ⇒ **同一盘排两次，证据文本的卦名顺序不同**。
  后果：① 审计留痕**不可复现**（无法回归比对）；
  ② 行为快照**非确定** ⇒ 变异扫描的「等价 vs 真盲区」判定**全错**
  （基线与变异快照永远不同 ⇒ 所有存活变异被误判成真盲区）。
  ⇒ 修法：一律 `sorted()` 后再拼。
- **★ 扫描器致命顺序错误（工具自身的 bug，但会**作废扫描结论**）**：
  `mutation_sweep.py` 里 `runner.restore()`（还原源码）排在了
  `_behaviour_snapshot()`（取快照）**之前** ⇒ 快照子进程读到的已是原码
  ⇒ 快照**必然**等于基线 ⇒ **每个存活变异都被判成「等价变异」**
  ⇒ **真盲区一个都发现不了**，而报告写「★ 真盲区 0」。
  ⚠ 它**不报错、不崩、退出码 0、还原校验通过** ⇒ 前两轮扫描都未发现。
  ⇒ 修法：**先取快照，再还原**。
- **扫描器快筛无视 `--tests` 范围**：快筛硬编码 `tests/heluo` ⇒
  当 `--tests` 指向别处时，「这个范围内有没有守卫」这个问题
  被**范围外**的守卫回答了 ⇒ 结论与前提不一致。
  ⇒ 快筛与慢筛改用**同一个** tests_dir。
- **子进程漏传 `env`（假绿/假红双向失效）**：
  `test_heluo_cli.py::TestNoStrayOutput::test_import_is_silent`
  构造了 `env` 却**从未传给** `subprocess.run` ⇒ 本机假红、
  CI（`pip install -e .`）假绿 ⇒ 被测断言从未真正生效。
  ⇒ 已修 + 新增 AST 守卫 `test_heluo_subprocess_env.py`。
- **固定 `PYTHONHASHSEED` 会让确定性守卫恒绿**：守卫「跨进程跑两次比对」
  依赖两次拿到**不同** seed ⇒ 若环境固定 seed ⇒ 非确定性检不出来
  （实测守卫仍全绿）。
  ⇒ 守卫改为**显式用两个不同 seed** 跑自己的子进程；
  同时扫描器自己的快照对比**固定同一 seed**（否则全判盲区）。

### 新增
- **变异扫描自动化**（`tools/heluo/mutation_sweep.py`）：
  AST 自动生成四类变异（字面量 / 运算符 / 去否定 / 返回值吞掉），
  两级筛（快筛 → 全量确认），存活变异用**行为快照**区分
  「等价变异」与「★真盲区」。
- **行为快照**（`tools/heluo/behaviour_snapshot.py`）：5 个固定盘 → 确定性 JSON；
  覆盖 `HeluoResult` **全部主要输出面**（数值/元气/世代/节候/卦象结构/
  运程/判词/解读层/冻结状态/时间层）。
- **批跑器**（`tools/heluo/mutation_sweep_batch.py`）：串行跑多模块、
  产出**机器可读 JSON**（`--json-out`），有真盲区 ⇒ 退出码 **2**。
- **工具自检守卫**（`test_heluo_mutation_sweep_selfcheck.py`）：
  故意造一个真盲区，验证扫描器能抓到它且退出码为 2
  ⇒ **这是唯一能暴露「工具坏了却报告一切正常」的手段**。
  ⚠ 自检在**源码副本**里跑（绝不碰真实 `src/`）+ 环境变量**递归熔断**
  （否则 扫描 → 全量测试 → 本守卫 → 又一个扫描 ⇒ 无限套娃 + 并发污染）。
- **死代码守卫**（`test_heluo_no_dead_code.py`）：包内模块级函数/类不得零引用
  （含主仓 vendor 引用范围；排除守卫自身）。
- **快照确定性守卫**（`test_heluo_snapshot_determinism.py`）：
  **跨进程、两个不同 seed** 两次快照逐字段比对 + 输出面覆盖检查。
- **CI 接入**（`.github/workflows/mutation-sweep.yml`）：
  PR 快速档（2 模块，分钟级，有真盲区即红）+
  夜间全量档（22 模块，6 分片并行）；两道保险 = 扫描器退出码 + `git diff` 还原校验。
- **依赖锁定**（`requirements-ci.txt`）：16 个包锁定到已验证版本
  ⇒ CI 结果**可复现**（原先写 `>=` 下限 ⇒ 上游发版就把 CI 打红且不可复现）。

### 变更
- `mutation_sweep.py` 的超时判定细化：**超时 ≠ 被抓住**
  （否则「守卫本身慢」会被误判成「变异被抓住」⇒ **掩盖真盲区**）⇒
  区分「挂起型 / 真正失败 / 升级复核」三态；
  超时预算按**基线实测耗时**推算，不再拍脑袋。
- 扫描器**中断必还原**：`finally` + 信号处理器无条件还原并校验哈希
  （扫描原地改 `src/`，实测中断曾残留 `return None` 变异）。

## [1.1.0] — 2026-10-25

### 新增
- **CLI 覆盖率守卫**：原 CLI 测试全部走**子进程** ⇒ coverage **跟踪不到**
  （实测 cli.py 覆盖率仅 11%，形成「有测试」的假盲区）。
  改为 in-process（`cli.main(argv)`）为主 + 子进程验「真实安装形态」两条路并存
  ⇒ cli.py 覆盖率 11% → **80%**。
- **降级契约守卫**（`test_heluo_degradation_contracts.py`，19 条）：
  子块失败必须**留痕**（warnings）、非法入参必须**显式报错**、
  公开门面必须可解析、判据不得给 0–1 分数。
- **公开 API 稳定性守卫**（`test_heluo_public_api.py`，14 条）：
  `__all__` 成员集合 + 关键函数签名 + 契约层类身份 + 资源定位与 CWD 无关。
- **测试卫生守卫**（`test_heluo_test_hygiene.py`）：
  同类内**不得有同名测试方法**（后者覆盖前者 ⇒ 先前的守卫从未执行）。
- **有意重导出守卫**（`test_heluo_reexports.py`）：
  显式登记全部「同一对象」型重导出，校验其**存在 + 是同一对象**，
  且 import 行**必须**带「noqa: F401」标注（否则会被未用 import 工具删掉）。
- **工程化配套**：`py.typed`、`.github/workflows/ci.yml`（测试矩阵 +
  静态检查 + 构建/部署自检）、`CHANGELOG.md`、`LICENSE`、`CONTRIBUTING.md`、
  `pyproject.toml` 完整化（classifiers / keywords / urls / dev 依赖组 /
  pytest / coverage / ruff / mypy 配置）。

### 修复
- **解读层 `getattr` 穿透**：`getattr(obj, name, default)` 的默认值**只对
  「属性不存在」生效**；属性访问**本身抛异常**时会穿透 ⇒ 解读层曾是
  「唯一能让主链崩掉的入口」。现统一走 `_safe_getattr`，失败**留痕**。
- **`bazi_engine.py` 用了未 import 的 `Optional` / `date`**：
  靠 `from __future__ import annotations`（注解不求值）掩盖 ⇒ 运行时不报错，
  但任何 `typing.get_type_hints()` / IDE / 文档工具都会 NameError。
- **`canonical.__all__` 里的悬空导出** `GOLDEN_CASES`：它**只作为类属性**存在，
  模块级没有 ⇒ `from ...canonical import *` 会 ImportError。
- **数格判据「缺生月就静默判错」**：诊断图取不到生月时把 `None` 传给
  `judge_shu_xiong`（其 `birth_month` 是必填 int）⇒ 落进「既非阳月也非阴月」
  的隐式分支。现改为**不判数格**并写明理由。
- **性别值未校验**：adapter 签名是 `gender: str`，下游只接受
  `Literal["male","female"]` ⇒ 传 `"Male"` / `"M"` 会在深处才炸。
  现入口**归一 + 显式报错**（支持 M/F/男/女 等别名）。
- **重复定义的死代码**：`time_layer_judgment` 里两张内容相同的爻位表 +
  一张被定义两次；`bazi_ten_gods` 里被 facts 层 import 覆盖的手抄表
  （`GENERATES` / `CONTROLS` / `BRANCH_HIDDEN_STEMS`）⇒ 均删除，只留单一来源。
- **`test_no_fabricated_verdict.py` 的同名测试方法**：后定义的覆盖了先定义的
  ⇒ 先前那条守卫**从未执行**。已删除重复项。
- **`test_h6_hua_gong` 的脆弱文本切片**：它按整行文本匹配 import 行，
  源码加一句注释就让守卫 ValueError ⇒ 改为按**行首**匹配。

### 变更
- 依赖下限：`sxtwl>=1.0.0` → **`sxtwl>=2.0.0`**。
- **Ruff 规则集收窄到「真 bug 类」**：F401（未用 import）与 I001（import 排序）
  **不启用** —— 本仓大量「未用 import」其实是**有意的重导出**
  （守卫要求它们与源头是**同一对象**），批量清理会破坏「全局只有一份」的保证
  （实测：删掉 5 处重导出 ⇒ 5 条守卫变红）。
  **保留** F821（未定义名）/ F822（悬空导出）—— 这两类是真缺陷。
- **CI 不跑 `ruff format --check`**：实测 ruff 0.17.2 在本仓源码上**直接 panic**
  （本仓大量中文/全角字符触发其 source-map 缺陷）⇒ 加进 CI 只会让流水线恒红。

### 静态检查现状
- `ruff check src tests tools` ⇒ **All checks passed!**
- `mypy src/heluo_engine` ⇒ **Success: no issues found in 72 source files**
- `pytest` ⇒ 1503 passed / 6 skipped / 0 failed

## [1.0.0] — 2026-10-25

首个**可独立部署**版本。

### 新增
- **时间层判据**（`time_layer_judgment`）：流年 / 流月 / 流日按原典爻辞判据
  （起例卷之上 L212「三辞吉：卦爻中有元吉亨利是也」）给出**吉 / 不判**。
  - 只给三态，**不给 0–1 分数**；
  - **不判凶** —— L222「三辞凶」只给名目未给门槛，且 L257 明言
    「若拘拘于爻辞吉凶，则失之矣」；
  - 判据为**卦级**（L212 原文「卦爻中」= 该卦六爻），门槛窄是原典实况。
- **诊断图接线**：`HL_DAYUN` / `HL_LIUNIAN_GUA` / `HL_YUEGUA` / `HL_RIGUA`
  四条时间层规则此前「注册了却从不产出」（空授权），现产出证据并进图。
- **卦体维度** `PATTERN.05`（正体 / 互体 / 伏体）：`HL_HEXAGRAM_STRUCTURE`
  证据此前被产出却因未注册而**静默丢弃**，现已补注册 + 维度映射。
- **命令行入口** `heluo-engine`：`compute` / `interpret` / `gua` / `doctor`
  / `--version` / `--where`；输出为**纯 JSON**。
- **部署自检** `doctor`：校验包内资源齐备、可按包定位、CWD 无标准库 shadow。
- **构建验证脚本** `tools/heluo/build_and_verify.py`：构建 wheel → 查内容 →
  装进干净 venv → 跑自检与真实排盘，一条命令完成部署验收。
- **部署指南** `docs/heluo/独立部署指南_20261025.md`。
- **同步工具** `tools/heluo/sync_to_main_repo.py`：独立包 → 主仓 vendor 副本
  镜像同步（比较时归一化换行符与 BOM）。

### 修复
- **流日日历口径**：公历目标日曾被当作「节气月序 + 节后日序」使用，
  取错月（实测差 33 天）。现按 `resolve_jieqi_window` 换算。
- **流日黄历与平台 DAILY 信号**：改按目标日（此前落在日段首日）。
- **解读层 `getattr` 穿透**：`getattr(obj, name, default)` 的默认值只对
  「属性不存在」生效；属性访问**本身抛异常**时会穿透 ⇒ 解读层曾是
  「唯一能让主链崩掉的入口」。现统一走 `_safe_getattr`，失败**留痕**。
- **`src.heluo_engine` 形态的 import**：`src` 是打包根目录、不是包 ⇒
  装成 wheel 后该 import 失效。已改为顶层包名形态。
- **契约层类身份分裂**：主仓 `tongshu/spec/canonical` 与
  `heluo_engine/spec/canonical` 字节相同但**类身份不同** ⇒ `isinstance`
  恒假。现主仓改为纯转发 vendor，实体定义只留一份。

### 变更
- 顶层包名由 `tongshu` 改为 **`heluo_engine`**（与主仓命名空间完全隔离，
  可同环境共存）。旧配置装出的顶层包 `tongshu` 与主仓同名，
  实测会**静默吃掉**主仓 32 个顶层子包。
- 主仓 `src/tongshu/engines/heluo/` 旧副本**已删除**（逐文件比对确认
  无独有能力），主仓改用 `src/heluo_engine/` vendor 副本。
- 依赖下限收紧：`sxtwl>=2.0.0`（原 `>=1.0.0`）。

### 工程化
- `py.typed` 标记（类型信息随包分发）。
- `pyproject.toml` 完整化：classifiers / keywords / license / urls /
  `optional-dependencies`（dev / typing）/ pytest / coverage / ruff / mypy 配置。
- CI：GitHub Actions（测试矩阵 py3.11+3.12 × ubuntu+windows、静态检查、
  构建 + 部署自检）。
- `CHANGELOG.md` / `LICENSE` / `CONTRIBUTING.md`。
- 公开 API 稳定性守卫（`__all__` 快照 + 关键签名冻结 + 契约层类身份）。
- 降级契约守卫（失败必留痕、非法入参必报错、公开门面可解析）。

[未发布]: https://github.com/ZQMMING/LIORIN/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ZQMMING/LIORIN/releases/tag/v1.0.0
