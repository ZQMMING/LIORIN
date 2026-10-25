"""河洛引擎（Heluo Engine）—— 独立可部署包。

**这是什么**
按《河洛真数》原典做的离线推命引擎：先天卦 / 后天卦 / 元堂 / 大运 /
流年 / 流月 / 流日 / 节候 / 化工 / 元气 / 判词 / 死断。

**为什么是独立顶层包**
2026-10-24 结构性重构。此前本引擎以 `tongshu.engines.heluo` 的形式寄居在
主仓 `tongshu` 命名空间下，带来两个实测确认的问题：

1. **命名空间互斥**：主仓顶层包也叫 `tongshu`，且 `engines/facts/reasoning/spec`
   四个子包同名重叠 ⇒ 两个 `tongshu` 不能同时 import。实测两种安装顺序：
   本包 site-packages 在前时，**主仓 32 个顶层子包全部消失**，而报错只说
   「找不到 tongshu.signal」，**不提示你装了本包** —— 静默破坏。
2. **路径绑定**：数据定位靠 `Path(__file__).resolve().parents[4]` 反推仓库根，
   换任何一层目录即失效，且把本包绑死在主仓仓库结构上，无法独立部署。

现改为独立顶层包 `heluo_engine`：
* 命名空间与主仓**完全隔离** ⇒ 可与主仓同环境共存、互不干扰；
* 数据**随包分发**，用 `importlib.resources` 按包定位 ⇒
  与安装位置、运行目录、CWD **全部无关**；
* 河洛相关的一切（源码 + 数据 + 对外 API）都在 `heluo_engine/` 一个文件夹下。

**一切随包分发**
河洛相关的一切都在 `heluo_engine/` 这一个文件夹下，分三块：

| 目录 | 内容 | 性质 |
|---|---|---|
| `data/` | 判词库 `guajie_data.json` / 精义 `guajie_jingyi.json` / 扩展断语 `kuozhan_duanyu.json` / 参评诗断语料 `canping/*.json` / 出生地点表 `locations.json` | **运行时必需** |
| `orig/` | 原典切片（起例卷三卷、《易卦释义》《诗断秘诀》《河洛理数·日卦起例卷》等） | 判词与语料的**逐字上游**，守卫随包走 |
| `docs/` | 依据文档（定案 / 裁决 / 核定 / 对照表 / 参评考证） | 判据的**证据链** |

三块都按包定位（`importlib.resources` ⇒ 与安装位置、运行目录、CWD 全部无关），
服务器上 `pip install heluo-engine` 即可运行，不需要仓库、不需要主仓。

**最小用法**
```python
from heluo_engine import HeluoAdapter

ad = HeluoAdapter()
res = ad.compute((1983, 11, 3, 12), gender="male", target_date="2026-10-23")
print(res.prenatal.hexagram_name, res.yuantang.yuantang, res.postnatal.hexagram_name)
```
"""
from __future__ import annotations

__version__ = "1.1.0"

__all__ = [
    "HeluoAdapter",
    "HeluoCanonical",
    "HeluoResult",
    "BaziEngine",
    "BaziChart",
    "build_platform_signals",
    "sanyuan",
]


def __getattr__(name):
    """惰性导出：只有真正被访问时才 import，避免拖慢 import 期。"""
    if name in ("BaziEngine", "BaziChart"):
        from .engines.bazi_engine import BaziEngine, BaziChart
        return {"BaziEngine": BaziEngine, "BaziChart": BaziChart}[name]
    if name in ("HeluoCanonical", "HeluoResult"):
        from .engines.heluo.canonical import HeluoCanonical, HeluoResult
        return {"HeluoCanonical": HeluoCanonical, "HeluoResult": HeluoResult}[name]
    if name == "HeluoAdapter":
        from .adapter import HeluoAdapter
        return HeluoAdapter
    if name == "build_platform_signals":
        from .engines.heluo.canonical_signals import build_platform_signals
        return build_platform_signals
    if name == "sanyuan":
        from .adapter import sanyuan
        return sanyuan
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
