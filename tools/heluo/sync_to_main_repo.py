# -*- coding: utf-8 -*-
"""把独立包**同步**到主仓的 vendor 副本（2026-10-24）。

背景
----
主仓（``tongshu``）已改为直接使用独立包 ``heluo_engine``：主仓内放置
``src/heluo_engine/``（与 ``src/tongshu/`` 平级），这样
  · 独立包源码**零改写**（相对导入 ``from ..._paths import`` 仍然成立 ——
    三级相对导入在 ``src.heluo_engine.engines.heluo`` 上下文里指向
    ``src.heluo_engine._paths`` ✓）；
  · ``_paths.py`` 的 ``__file__`` 兜底正好落到 ``src/heluo_engine/data|orig|docs`` ✓；
  · 主仓 ``[tool.setuptools.packages.find] where = ["src"]`` **自动**纳入打包 ✓。

⚠ 于是**同一份源码会有两份**（独立包 + 主仓 vendor 副本）⇒ 必须有同步工具，
  否则两边漂移。本工具做**镜像同步**（含删除目标端多余文件）。

用法
----
    # 只看差异（默认行为，不写任何文件）
    python tools/heluo/sync_to_main_repo.py
    # 执行同步
    python tools/heluo/sync_to_main_repo.py --apply
    # 指定主仓 worktree
    python tools/heluo/sync_to_main_repo.py --apply --main-repo D:\\shuntian\\.wt-jd
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / "src" / "heluo_engine"
DEFAULT_MAIN = Path(r"D:\shuntian\.wt-jd")

#: 不参与同步的文件（缓存与本地产物）
SKIP_SUFFIX = {".pyc", ".pyo"}
SKIP_DIR = {"__pycache__", ".pytest_cache"}

#: ★ 随包带去主仓的**河洛工具**（2026-10-26 新增）。
#:
#: 为什么需要：主仓也要跑**河洛专属的 CI**（测试 + 守卫盲区扫描），
#: 而扫描器必须能在**主仓的 vendor 副本**上就地运行
#: （扫描是**原地改源码**的工具 ⇒ 只能在「被扫的那份代码」所在处跑）。
#:
#: 这三个文件是**纯工具**：
#:   · 只依赖 ``src/heluo_engine``（vendor 镜像）+ pytest；
#:   · 不含任何业务判据、不含原典文本；
#:   · 与主仓其他引擎**零耦合** ⇒ 放进主仓**不会波及其他引擎**。
#:
#: ⚠ 边界：主仓的公共声明（如 ``pyproject.toml`` 的依赖）**不动** ——
#:   那是跨引擎的公共契约，改它会影响 ziwei/bazi/blind/platform 等所有引擎。
TOOL_FILES = [
    "mutation_sweep.py",
    "behaviour_snapshot.py",
    "mutation_sweep_batch.py",
]


def _files(root: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if any(part in SKIP_DIR for part in p.parts):
            continue
        if p.is_file() and p.suffix not in SKIP_SUFFIX:
            out[p.relative_to(root).as_posix()] = p
    return out


def _norm(path: Path) -> bytes:
    """归一化后比较：去 BOM、统一换行。

    ⚠ 2026-10-24 实测踩坑：直接用 ``filecmp.cmp`` 逐字节比较时，
    主仓 vendor 副本（Windows checkout ⇒ CRLF）与独立包（LF）
    会被误报成 41 个「内容不同」文件 —— 实际内容**完全一致**。
    本工具必须按**归一化后**的内容判断差异，否则每次同步都在
    报假差异、或者把 LF 无脑改成 CRLF 制造无谓 diff。
    """
    b = path.read_bytes()
    if b.startswith(b"\xef\xbb\xbf"):
        b = b[3:]
    return b.replace(b"\r\n", b"\n")


def _same(a: Path, b: Path) -> bool:
    try:
        return _norm(a) == _norm(b)
    except OSError:
        return False


def _sync_tools(main_root: Path, apply: bool) -> None:
    """把**河洛工具**同步到主仓 ``tools/heluo/``（主仓的河洛 CI 需要它们）。

    只同步 ``TOOL_FILES`` 里显式登记的文件 ⇒ **不会**把独立包的其它工具
    （含只服务独立包的脚本）带进主仓。
    """
    src_dir = REPO / "tools" / "heluo"
    dst_dir = main_root / "tools" / "heluo"
    added, changed, missing = [], [], []
    for name in TOOL_FILES:
        s = src_dir / name
        d = dst_dir / name
        if not s.exists():
            missing.append(name)
            continue
        if not d.exists():
            added.append(name)
        elif not _same(s, d):
            changed.append(name)
    print(f"\n河洛工具 → 主仓 {dst_dir}")
    print(f"  新增 {len(added)} / 内容不同 {len(changed)} / 源缺失 {len(missing)}")
    for n in added:
        print(f"   + {n}")
    for n in changed:
        print(f"   ~ {n}")
    for n in missing:
        print(f"   ! {n}（独立包里没有，跳过）")
    if not apply:
        return
    for name in added + changed:
        s, d = src_dir / name, dst_dir / name
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
    print(f"  ✔ 工具同步完成：写入 {len(added) + len(changed)} 文件")


def main() -> int:
    ap = argparse.ArgumentParser(description="独立包 → 主仓 vendor 副本 镜像同步")
    ap.add_argument("--main-repo", default=str(DEFAULT_MAIN),
                    help="主仓 worktree 根目录")
    ap.add_argument("--apply", action="store_true", help="真正写入（默认只报差异）")
    args = ap.parse_args()

    main_root = Path(args.main_repo)
    dst = main_root / "src" / "heluo_engine"
    if not main_root.exists():
        print(f"✘ 主仓路径不存在：{main_root}")
        return 1
    if not PKG.exists():
        print(f"✘ 独立包不存在：{PKG}")
        return 1

    src_files = _files(PKG)
    dst_files = _files(dst)

    added = sorted(set(src_files) - set(dst_files))
    removed = sorted(set(dst_files) - set(src_files))
    changed = sorted(
        rel for rel in (set(src_files) & set(dst_files))
        if not _same(src_files[rel], dst_files[rel])
    )

    print(f"独立包 {len(src_files)} 文件 → 主仓 {dst}")
    print(f"  新增 {len(added)} / 删除 {len(removed)} / 内容不同 {len(changed)}")
    print("  （比较已归一化换行符与 BOM ⇒ 不报假差异）")
    for rel in added[:20]:
        print(f"   + {rel}")
    for rel in removed[:20]:
        print(f"   - {rel}")
    for rel in changed[:20]:
        print(f"   ~ {rel}")
    if len(added) + len(removed) + len(changed) > 60:
        print("   …（其余略）")

    if not args.apply:
        print("\n(--check 模式：未写任何文件；加 --apply 执行同步)")
        _sync_tools(main_root, apply=False)
        return 0

    for rel in removed:
        (dst / rel).unlink(missing_ok=True)
    for rel in added + changed:
        s = src_files[rel]
        d = dst / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
    print(f"\n✔ 同步完成：写入 {len(added) + len(changed)} 文件，删除 {len(removed)} 文件")
    _sync_tools(main_root, apply=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
