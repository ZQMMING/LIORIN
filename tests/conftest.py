"""Run legacy assertion programs as tests without importing them during collection."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


TESTS = Path(__file__).parent
LEGACY_SCRIPTS = frozenset(
    line for line in (TESTS / "legacy_script_tests.txt").read_text(encoding="utf-8").splitlines()
    if line and not line.startswith("#")
)


class LegacyScriptModule(pytest.Module):
    def collect(self):
        yield LegacyScriptItem.from_parent(self, name="legacy_script")


class LegacyScriptItem(pytest.Item):
    def runtest(self):
        root = self.config.rootpath
        paths = [str(root), str(root / "src")]
        if inherited := os.environ.get("PYTHONPATH"):
            paths.append(inherited)
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(paths), PYTHONIOENCODING="utf-8")
        result = subprocess.run(
            [sys.executable, str(self.path)], cwd=root, env=env,
            capture_output=True, encoding="utf-8", check=False,
            timeout=self.config.getoption("timeout", default=60) or 60,
        )
        if result.returncode:
            pytest.fail(f"Script exited {result.returncode}\n{result.stdout}{result.stderr}", pytrace=False)
        for line in result.stdout.splitlines():
            if line.startswith(f"SKIP {self.path.stem}:"):
                pytest.skip(line)

    def reportinfo(self):
        return self.path, 0, self.name


def pytest_pycollect_makemodule(module_path, parent):
    if module_path.parent == TESTS and module_path.name in LEGACY_SCRIPTS:
        return LegacyScriptModule.from_parent(parent, path=module_path)
    return None
