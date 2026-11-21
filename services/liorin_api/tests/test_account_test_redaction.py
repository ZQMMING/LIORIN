import os
import subprocess
import sys
from pathlib import Path


def test_account_failure_redacts_terminal_and_junit(tmp_path):
    root = Path(__file__).resolve().parents[3]
    script = tmp_path / 'test_failure.py'
    script.write_text(
        '''
import os
import pytest
from services.liorin_api.account_tests.redaction import protect

def test_skip():
    pytest.skip(os.environ["LIORIN_M3_TEST_DSN"])

def test_failure():
    print(os.environ["LIORIN_M3_TEST_DSN"])
    print("Authorization: Bearer " + "-".join(("synthetic", "bearer", "value")))
    code = protect("441" + "277")
    assert code == "wrong"
''',
        encoding='utf-8',
    )
    xml = tmp_path / 'report.xml'
    password = 'synthetic-db-password-for-test'
    dsn = f'host=127.0.0.1 password={password}'
    env = dict(os.environ, LIORIN_M3_TEST_DSN=dsn, PYTHONPATH=str(root))
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', '-q', '-o', 'addopts=', '-o', 'junit_logging=all',
         '-p', 'services.liorin_api.account_tests.conftest', f'--junitxml={xml}', str(script)],
        cwd=root, env=env, capture_output=True, encoding='utf-8', timeout=25, check=False,
    )
    assert result.returncode == 1
    assert '1 skipped' in result.stdout
    for output in (result.stdout, xml.read_text(encoding='utf-8')):
        assert '[redacted]' in output
        assert password not in output
        assert 'synthetic-bearer-value' not in output
        assert '441277' not in output
