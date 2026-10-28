"""Engine layer（河洛独立包）。

本包携带四个引擎：

- `heluo`  河洛引擎（本包主体）
- `bazi`   八字排盘（河洛引擎的必需上游：排四柱）
- `time`   真太阳时 / 时区 / 经度偏移（河洛引擎的必需上游）
- `yi`     易经卦爻辞结构（河洛解卦层的结构来源）

上游模块不在本包内的（如紫微、黄历）不导入，避免 import 期即失败。
"""

__all__ = [
    "BaziEngine",
    "BaziChart",
    "HeluoCanonical",
    "HeluoResult",
]


def __getattr__(name):
    """惰性导出：只有真正被访问时才 import，避免拖慢 import 期。"""
    if name in ("BaziEngine", "BaziChart"):
        from .bazi_engine import BaziEngine, BaziChart
        return {"BaziEngine": BaziEngine, "BaziChart": BaziChart}[name]
    if name in ("HeluoCanonical", "HeluoResult"):
        from .heluo.canonical import HeluoCanonical, HeluoResult
        return {"HeluoCanonical": HeluoCanonical, "HeluoResult": HeluoResult}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
