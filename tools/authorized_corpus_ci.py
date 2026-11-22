"""Verify an owner-supplied corpus manifest before running private checks."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "criteria": ("LIORIN_CRITERIA_ROOT", "tests/test_criteria_anchors.py"),
    "cases": ("LIORIN_REAL_CASES_FILE", "tests/test_real_case_smoke.py"),
}


def inventory(name: str, location: Path) -> dict[str, str]:
    if name == "criteria":
        slices = sorted(location.glob("p0_v2/output/*/*_slices.jsonl"))
        if not slices:
            raise ValueError("No original-text slices")
        paths = [location / "p0_v2/output/ENGINE_CRITERIA_ANCHORS.json", *slices]
        paths += sorted(path for path in location.glob("engines/common/*.py") if ".bak" not in str(path))
        paths += sorted(path for path in location.glob("p0_v2/*.py") if ".bak" not in str(path))
        files = [(path.relative_to(location).as_posix(), path) for path in paths]
    else:
        files = [("real_cases", location)]
    result = {}
    for name, path in files:
        if not path.resolve().is_relative_to(location.resolve() if location.is_dir() else location.parent.resolve()):
            raise ValueError("Corpus file escaped approved path")
        with path.open("rb") as handle:
            result[name] = hashlib.file_digest(handle, "sha256").hexdigest()
    return result


def main() -> int:
    try:
        manifest_path = Path(os.environ["LIORIN_CI_DATA_MANIFEST"]).resolve(strict=True)
        if manifest_path.is_relative_to(ROOT):
            raise ValueError("Manifest must be supplied outside the checkout")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["schema"] != 1 or manifest["scope"] != "liorin-ci-read-only":
            raise ValueError("Unsupported manifest")
        for name, (variable, _) in CHECKS.items():
            record = manifest["inputs"][name]
            if not all(isinstance(record[key], str) and record[key].strip()
                       for key in ("owner", "source", "version", "authorization")):
                raise ValueError("Provenance incomplete")
            location = Path(os.environ[variable]).resolve(strict=True)
            if location.is_relative_to(ROOT) or record["sha256"] != inventory(name, location):
                raise ValueError("Corpus inventory mismatch")
    except (KeyError, OSError, TypeError, ValueError):
        print("AUTHORIZED_CORPUS: UNVERIFIED — approved provenance or corpus inventory is missing or differs.")
        return 2

    failed = False
    for name, (_, test_path) in CHECKS.items():
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--color=no", "-m", "authorized_corpus", test_path],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
            errors="replace", check=False,
        )
        passed = result.returncode == 0 and bool(
            re.search(r"^1 passed(?:, \d+ warnings?)? in ", result.stdout, re.MULTILINE)
        )
        print(f"AUTHORIZED_CORPUS {name}: {'PASSED' if passed else 'FAILED'}")
        failed |= not passed
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
