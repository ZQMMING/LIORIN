"""包内资源定位（**零路径绑定**，2026-10-24 结构性重构）。

**为什么需要这个模块**

河洛引擎的判词库、参评诗断语料、原典切片与依据文档是**运行时必需**的资源。
此前它们放在仓库根的 `data/heluo/`，代码靠
`Path(__file__).resolve().parents[4]` 反推仓库根再拼路径：

* 换任何一层目录即失效（打包 / 安装 / 改层级全断）；
* 把河洛包**硬耦合**在主仓仓库结构上 —— 无法独立部署到服务器；
* 与主仓 `tongshu` 命名空间冲突（见
  `heluo_engine/docs/河洛回灌接线决策单_20261024.md`）。

现改为：资源**随包分发**，按包定位 ——
与安装位置、运行目录、CWD **全部无关**。

**包内布局**

```
heluo_engine/
├── data/    运行时数据（JSON）：判词库 / 精义 / 扩展断语 / 参评诗断语料 / 出生地点表
├── orig/    原典切片（.txt/.md）：判词与诗断语料的逐字上游、起例卷三卷
└── docs/    依据文档（.md）：定案 / 裁决 / 核定 / 对照表 / 参评考证
```

**两种运行形态都要能用**

1. **已安装**（服务器部署的正常形态）：
   `pip install heluo-engine` ⇒ `importlib.resources` 直接可用。
2. **源码树直跑**（本仓库开发态，测试以
   `from src.heluo_engine... import` 方式导入）：
   此时顶层包名是 `src.heluo_engine` 而非 `heluo_engine`，
   `importlib.resources.files("heluo_engine")` 会 ImportError。

故本模块采用「**先按包定位，失败则按本文件位置定位**」的双通道：
`__file__` 定位走的是**包内相对路径**（`heluo_engine/data/...`），
**不含任何仓库根推算**，因此换目录层级、安装方式、运行目录都不影响。
"""
from __future__ import annotations

from pathlib import Path

__all__ = [
    "pkg_data_dir", "pkg_data", "PKG_DATA_DIR",
    "pkg_orig_dir", "pkg_orig", "PKG_ORIG_DIR",
    "pkg_doc_dir", "pkg_doc", "PKG_DOC_DIR",
]


def _locate_pkg_dir(name: str) -> Path:
    """定位包内子目录（两条通道）。

    通道①：已安装形态 —— 按包名定位（首选，与安装位置无关）
    通道②：源码树直跑形态 —— 按**本文件位置**定位包内子目录
           （本文件在 <包根>/heluo_engine/_paths.py ⇒ 包根 = parents[1]）
    """
    try:
        from importlib.resources import files as _files
        p = Path(str(_files("heluo_engine") / name))
        if p.is_dir():
            return p
    except Exception:
        pass
    p = Path(__file__).resolve().parent.parent / name
    if p.is_dir():
        return p
    raise FileNotFoundError(
        f"河洛包内 {name}/ 目录未找到：既非已安装形态（heluo_engine/{name}），"
        "也不在源码树预期位置。请确认包完整安装/解压。")


def _sub(base: Path, *parts: str) -> Path:
    p = base
    for part in parts:
        p = p / part
    return p


#: 包内运行时数据目录
PKG_DATA_DIR: Path = _locate_pkg_dir("data")
#: 包内原典切片目录
PKG_ORIG_DIR: Path = _locate_pkg_dir("orig")
#: 包内依据文档目录
PKG_DOC_DIR: Path = _locate_pkg_dir("docs")


def pkg_data_dir() -> Path:
    """包内运行时数据目录。"""
    return PKG_DATA_DIR


def pkg_data(*parts: str) -> Path:
    """定位包内运行时数据文件。

    用法：``pkg_data("guajie_data.json")``、
    ``pkg_data("canping", "448_duizhao.json")``。
    """
    return _sub(PKG_DATA_DIR, *parts)


def pkg_orig_dir() -> Path:
    """包内原典切片目录。"""
    return PKG_ORIG_DIR


def pkg_orig(*parts: str) -> Path:
    """定位包内原典切片文件。

    用法：``pkg_orig("河洛真数_起例卷之上.txt")``。
    """
    return _sub(PKG_ORIG_DIR, *parts)


def pkg_doc_dir() -> Path:
    """包内依据文档目录。"""
    return PKG_DOC_DIR


def pkg_doc(*parts: str) -> Path:
    """定位包内依据文档。

    用法：``pkg_doc("死断四条件核定_20261024.md")``、
    ``pkg_doc("canping", "README.md")``。
    """
    return _sub(PKG_DOC_DIR, *parts)
