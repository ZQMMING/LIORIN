# -*- coding: utf-8 -*-
"""河洛引擎 —— 一键构建 + 安装 + 自检脚本（2026-10-25）。

用途：把「构建 wheel → 装到目标环境 → 跑 doctor 自检」三步固化成一条命令，
避免每次部署手工敲三行、漏掉自检。

用法
----
::

    # 构建 wheel（不装）
    python tools/heluo/build_and_verify.py

    # 构建 + 装进临时 venv + 跑自检（不碰当前环境）
    python tools/heluo/build_and_verify.py --venv

    # 构建 + 装进指定环境（用当前 python）
    python tools/heluo/build_and_verify.py --install

    # 指定输出目录
    python tools/heluo/build_and_verify.py --outdir D:\\build

安全
----
* 默认**只构建**，不装任何东西（不污染当前环境）；
* ``--venv`` 建**临时** venv，装完可 ``--keep`` 保留，否则自动删；
* 退出码：0 = 全通过；1 = 有步骤失败。

⚠ 构建产物 ``dist/`` 已被 ``.gitignore`` 排除（实测确认），不会误提交。
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "dist"

#: 检查「CWD 里的同名 .py 没有 shadow 标准库」。
#:
#: ⚠ 2026-10-25 实测踩坑（重要，务必留在代码里）：
#:   CWD 会被放进 ``sys.path[0]`` ⇒ CWD 里若有 ``inspect.py`` / ``json.py``
#:   这类与标准库同名的文件，会**替换**标准库模块。
#:   实测后果：本机 ``C:\Windows\Temp\inspect.py``（一次性审计脚本）shadow 了
#:   ``inspect`` ⇒ ``dataclasses`` 在 import 期抛
#:   ``AttributeError: module 'inspect' has no attribute 'get_annotations'``
#:   ⇒ 引擎 import 失败；**且**那个 shadow 文件被执行，向 stdout 打印了
#:   800 多条无关的八字命例，把真正的错误彻底淹没。
#:   ⇒ 部署时务必在**干净目录**里运行；本检查把该风险变成显式失败。
_SHADOW_CHECK = (
    "import sys, os, json\n"
    "stdlib = set(sys.stdlib_module_names)\n"
    "cwd = os.getcwd()\n"
    "bad = []\n"
    "for name in stdlib:\n"
    "    p = os.path.join(cwd, name + '.py')\n"
    "    if os.path.exists(p):\n"
    "        bad.append(p)\n"
    "for p in bad:\n"
    "    print('SHADOW:', p)\n"
    "if bad:\n"
    "    print('FAIL: CWD 里有与标准库同名的 .py，会 shadow 标准库')\n"
    "    raise SystemExit(1)\n"
    "print('OK: no stdlib shadowing')\n"
)


def _run(cmd, cwd=None, env=None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd or REPO), env=env,
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _ok(msg):
    print("  [OK ] %s" % msg)


def _fail(msg, out=""):
    print("  [FAIL] %s" % msg)
    if out:
        tail = out.strip().splitlines()[-12:]
        for l in tail:
            print("         %s" % l)


def build(outdir: Path) -> tuple[bool, Path | None, str]:
    """构建 wheel。返回 (成功, wheel 路径, 输出)。"""
    print("[1/4] 构建 wheel → %s" % outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    # 清掉旧 wheel，避免拿到过期产物
    for old in outdir.glob("heluo_engine-*.whl"):
        old.unlink()
    rc, out = _run([sys.executable, "-m", "pip", "wheel", ".",
                    "--no-deps", "-w", str(outdir)])
    if rc != 0:
        _fail("构建失败", out)
        return False, None, out
    wheels = sorted(outdir.glob("heluo_engine-*.whl"))
    if not wheels:
        _fail("构建完成但未找到 wheel", out)
        return False, None, out
    _ok("wheel: %s (%.2f MB)" % (wheels[0].name, wheels[0].stat().st_size / 1e6))
    return True, wheels[0], out


def check_wheel_contents(wheel: Path) -> tuple[bool, str]:
    """检查 wheel 内是否带齐**运行必需**的数据。

    ⚠ 这是「装完才发现数据没带进去」的**前置**检查 ——
    纯 Python 包在缺资源时仍能 import，只在**运行时**才炸。
    """
    print("[2/4] 检查 wheel 内容（运行数据是否随包分发）")
    import zipfile
    need = [
        "heluo_engine/data/guajie_data.json",
        "heluo_engine/data/guajie_jingyi.json",
        "heluo_engine/data/kuozhan_duanyu.json",
        "heluo_engine/data/locations.json",
        "heluo_engine/data/canping/raw_shici_jintu_448.json",
        "heluo_engine/orig/河洛真数_起例卷之上.txt",
        "heluo_engine/orig/河洛理数_年卦月卦切片.txt",
        "heluo_engine/docs/算法原文对照核证表.md",
        "heluo_engine/cli.py",
    ]
    with zipfile.ZipFile(wheel) as z:
        names = set(z.namelist())
    missing = [n for n in need if n not in names]
    if missing:
        _fail("wheel 缺以下必需内容：%s" % missing)
        return False, "\n".join(missing)
    _ok("%d 项必需内容齐备" % len(need))
    return True, ""


def verify_in_venv(wheel: Path, keep: bool = False) -> tuple[bool, str]:
    """装进临时 venv，跑 doctor 自检与一次真实排盘。"""
    print("[3/4] 临时 venv 安装 + 自检")
    vdir = REPO / ".verify_venv"
    if vdir.exists():
        shutil.rmtree(vdir, ignore_errors=True)
    venv.EnvBuilder(with_pip=True).create(str(vdir))
    py = vdir / "Scripts" / "python.exe"
    if not py.exists():
        py = vdir / "bin" / "python"

    # ⚠ 自检必须在**干净且受控**的 CWD 里跑。
    #   原因：Python 会把 CWD 放进 sys.path[0] ⇒ CWD 里若有与标准库同名的
    #   .py（如 inspect.py / json.py），会**shadow 标准库** ⇒ dataclasses 等
    #   在 import 期抛 ``module 'inspect' has no attribute 'get_annotations'``
    #   这类**极具误导性**的错误（本项目实测踩过：C:\Windows\Temp\inspect.py
    #   的一次性审计脚本 shadow 了 inspect，连带 800 多条无关输出污染 stdout）。
    #   ⇒ 自检目录必须是**新建的空目录**，不能是系统 TEMP（那里可能积着
    #   历史脚本）。这同时也是给使用者的**部署提示**：不要在有同名 .py 的
    #   目录里跑引擎。
    cdir = REPO / ".verify_cwd"
    if cdir.exists():
        shutil.rmtree(cdir, ignore_errors=True)
    cdir.mkdir(parents=True, exist_ok=True)

    rc, out = _run([str(py), "-m", "pip", "install", "--quiet", str(wheel)])
    if rc != 0:
        _fail("安装失败", out)
        return False, out
    _ok("安装成功")

    # 先查「标准库未被 shadow」，再做功能自检
    rc, out = _run([str(py), "-c", _SHADOW_CHECK], cwd=str(cdir))
    if rc != 0:
        _fail("标准库 shadow 检查未通过（CWD 里有同名 .py？）", out)
        return False, out
    _ok("标准库未被 shadow（CWD 干净）")

    # 从**与仓库无关**的目录跑 ⇒ 验证「不依赖仓库」
    rc, out = _run([str(py), "-m", "heluo_engine.cli", "doctor"], cwd=str(cdir))
    if rc != 0 or '"result": "PASS"' not in out:
        _fail("doctor 自检未通过", out)
        return False, out
    _ok("doctor: PASS（包内资源齐备且按包定位）")

    rc, out = _run([str(py), "-m", "heluo_engine.cli", "compute",
                    "--birth", "1983-11-03", "--time", "12:00", "--brief",
                    "--target", "2026-10-23"], cwd=str(cdir))
    if rc != 0 or "prenatal" not in out:
        _fail("独立排盘失败", out)
        return False, out
    _ok("独立排盘成功（脱离仓库运行）")

    if not keep:
        shutil.rmtree(vdir, ignore_errors=True)
        shutil.rmtree(cdir, ignore_errors=True)
    else:
        print("  临时 venv 保留在：%s" % vdir)
        print("  自检 CWD 保留在：%s" % cdir)
    return True, out


def install_here(wheel: Path) -> tuple[bool, str]:
    print("[3/4] 安装到当前 Python 环境")
    rc, out = _run([sys.executable, "-m", "pip", "install", "--quiet",
                    "--force-reinstall", "--no-deps", str(wheel)])
    if rc != 0:
        _fail("安装失败", out)
        return False, out
    _ok("安装成功")
    rc, out = _run([sys.executable, "-m", "heluo_engine.cli", "doctor"])
    if rc != 0 or '"result": "PASS"' not in out:
        _fail("doctor 自检未通过", out)
        return False, out
    _ok("doctor: PASS")
    return True, out


def main() -> int:
    ap = argparse.ArgumentParser(description="河洛引擎：构建 + 验证")
    ap.add_argument("--outdir", default=str(DEFAULT_OUT), help="wheel 输出目录")
    ap.add_argument("--venv", action="store_true",
                    help="建临时 venv 安装并自检（推荐）")
    ap.add_argument("--install", action="store_true",
                    help="装进当前 Python 环境（会改环境，慎用）")
    ap.add_argument("--keep", action="store_true", help="保留临时 venv")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    ok, wheel, out = build(outdir)
    if not ok:
        return 1
    ok, _ = check_wheel_contents(wheel)
    if not ok:
        return 1

    if args.venv:
        ok, _ = verify_in_venv(wheel, keep=args.keep)
        if not ok:
            return 1
    elif args.install:
        ok, _ = install_here(wheel)
        if not ok:
            return 1
    else:
        print("[3/4] 跳过安装（加 --venv 自检 / --install 装入当前环境）")

    print("[4/4] 完成")
    print("  wheel: %s" % wheel)
    print("  部署到服务器：pip install %s" % wheel.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
