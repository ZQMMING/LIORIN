# -*- coding: utf-8 -*-
"""Portable acceptance runner. Missing, skipped and failed checks never count as PASS."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SUITES = [
    'test_yuanjuan_matrix', 'test_criteria_anchors', 'test_special_pattern_golden',
    'test_bingyao_layer_golden', 'test_yongshen_geju_golden', 'test_xiang_shen_golden',
    'test_dayun_xiji_yongshen_golden', 'test_daymaster_root_class_golden',
    'test_qtbj_climate_golden', 'test_ancient_case_golden',
    'test_daymaster_root_relations_golden', 'test_daymaster_wang_xiang_golden',
    'test_runtime_contract_repair', 'test_final_gate_contract', 'test_case_presence_trace', 'test_medicine_evidence_contract', 'test_climate_candidate_identity', 'test_slice_root_conditions', 'test_source_track_wiring', 'test_usage_resolution', 'test_production_gate_golden', 'test_compound_query_refresh',
]


def run_check(root: Path, relative: str, timeout: float = 180) -> dict:
    path = root / relative
    if not path.is_file():
        return {'check': relative, 'status': 'BLOCKED', 'reason': 'required script missing',
                'returncode': None, 'stdout': '', 'stderr': ''}
    env = os.environ.copy()
    env['PYTHONPATH'] = str(root) + os.pathsep + env.get('PYTHONPATH', '')
    try:
        result = subprocess.run(
            [sys.executable, '-X', 'utf8', str(path)], cwd=root, env=env,
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {'check': relative, 'status': 'FAIL', 'reason': 'timeout',
                'returncode': None, 'stdout': '', 'stderr': ''}
    except OSError as exc:
        return {'check': relative, 'status': 'BLOCKED', 'reason': str(exc),
                'returncode': None, 'stdout': '', 'stderr': ''}
    output = result.stdout + '\n' + result.stderr
    # Legacy standalone suites use exit(0) for unavailable/frozen tests.
    skipped = re.search(r'(?im)^\s*SKIP\b|\bskipped\s*=\s*[1-9]\d*|\b[1-9]\d*\s+skipped\b', output)
    crashes = re.search(r'(?im)^\s*Total crashes\s*[:=]\s*([1-9]\d*)', output)
    blocked = re.search(r'(?im)^\s*BLOCKED\b', output)
    if blocked and result.returncode == 2:
        status = 'BLOCKED'
    else:
        status = 'FAIL' if result.returncode or crashes else ('SKIP' if skipped else 'PASS')
    return {'check': relative, 'status': status, 'returncode': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def summarize(checks: list[dict]) -> dict:
    counts = {status: sum(c['status'] == status for c in checks)
              for status in ('PASS', 'FAIL', 'SKIP', 'BLOCKED')}
    return {'passed': bool(checks) and counts['PASS'] == len(checks),
            'counts': counts, 'checks': checks}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout', type=float, default=180)
    parser.add_argument('--json-out', type=Path,
                        default=ROOT / 'p0_v2/output/FINAL_VERIFICATION.json')
    args = parser.parse_args(argv)
    paths = ['tests/check_fact_source.py'] + [f'tests/{suite}.py' for suite in SUITES]
    paths += ['p0_v2/_verify_20261009/run_all.py', 'tests/regress_gate.py']
    checks = []
    for relative in paths:
        check = run_check(ROOT, relative, args.timeout)
        checks.append(check)
        print(f"{check['status']:7s} {relative}", flush=True)
    report = summarize(checks)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('COUNTS:', report['counts'])
    print('ACCEPTANCE:', 'PASS' if report['passed'] else 'NOT PASSED')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
