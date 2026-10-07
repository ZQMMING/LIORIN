"""河洛相关全量基线：自动排除导入期 sys.exit 的脚本式测试。

背景：tests/ 根目录有 85 个「脚本式」测试文件在模块顶层调用 sys.exit()，
pytest 一收集就 INTERNALERROR，故不能直接 `pytest tests`。
本脚本按内容特征剔除它们，再跑其余全部可收集用例。
用法：python tools/heluo/run_full_baseline.py
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TESTS = os.path.join(ROOT, "tests")

_EXIT = re.compile(r"^sys\.exit|^    sys\.exit\(1 if fails", re.M)


def is_script_style(path):
    with io.open(path, "r", encoding="utf-8", errors="replace") as f:
        return bool(_EXIT.search(f.read()))


def collect():
    files = []
    for name in sorted(os.listdir(TESTS)):
        if name.endswith(".py") and name.startswith("test"):
            p = os.path.join(TESTS, name)
            if not is_script_style(p):
                files.append(name)
    subdirs = [d for d in sorted(os.listdir(TESTS))
               if os.path.isdir(os.path.join(TESTS, d)) and d != "__pycache__"]
    return files, subdirs


def main():
    files, subdirs = collect()
    skip = len([n for n in os.listdir(TESTS)
                if n.endswith(".py") and n.startswith("test")
                and is_script_style(os.path.join(TESTS, n))])
    args = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    args += ["tests/" + d for d in subdirs]
    args += ["tests/" + f for f in files]
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    env["PYTHONIOENCODING"] = "utf-8"
    env["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"
    env["TONGSHU_AUTHORITY_CREDENTIALS"] = (
        "architecture-governance:schema-v1-arch-gov-2026;"
        "admission_registry:test-cred-hash")
    print("根用例 %d 个（已排除脚本式 %d 个）+ 子目录 %s"
          % (len(files), skip, ",".join(subdirs)))
    r = subprocess.run(args, cwd=ROOT, env=env)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()