# -*- coding: utf-8 -*-
"""主仓接线测试（跨仓）—— **须在主仓仓库中运行**。

本目录下的守卫测的是**主仓**（顶层包 `tongshu`）与河洛引擎的**接线**：
主仓 pipeline 是否把河洛结果透传到位、主仓 `compute_stage` 是否真的调用了
河洛诊断层/建议层、主仓 `reasoning.signal_engine` 是否正确归属河洛信号等。

河洛引擎已于 2026-10-24 提纯为**独立包** `heluo_engine`，
**不再包含主仓专有模块**（`tongshu.pipeline` / `tongshu.pipeline_stages` /
`tongshu.reasoning.signal_engine` / `tongshu.engines.gua_jixiong` …）。
故这些守卫在独立包形态下**无法运行** —— 它们在主仓仓库中才有意义。

处置：主仓不可用时**整目录跳过**（而不是在收集期炸成 error，
让独立包的 CI 一片红）。导入前缀已还原为主仓形态（`tongshu.*`），
故本目录整体并入主仓即可直接运行。

**不要把这些守卫改成依赖河洛独立包即可运行的形态** ——
它们测的就是「主仓有没有把河洛接对」，主仓不在场时该断言无意义。

⚠ 判定主仓是否可用，**必须查具体子模块**，不能只看顶层包：
  顶层 `tongshu` 可能因**命名空间包**（目录存在但无 `__init__.py`）
  或残留目录而「可发现」，但 `tongshu.pipeline` 并不存在 ——
  此时 `find_spec("tongshu")` 返回真而实际 import 失败（实测踩过：
  残留的 `src/tongshu/` 空目录让 `import tongshu` 成功、却无任何子模块）。
"""
import importlib.util

#: 这些守卫的最低门槛：主仓 pipeline 必须真的可导入
_MAIN_REPO_MARKER = "tongshu.pipeline"


def _module_available(name: str) -> bool:
    """模块是否真的可导入（异常一律当作不可用）。"""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError, AttributeError):
        return False


#: 主仓不可用 ⇒ 本目录全部跳过
if not _module_available(_MAIN_REPO_MARKER):
    collect_ignore_glob = ["*.py"]
