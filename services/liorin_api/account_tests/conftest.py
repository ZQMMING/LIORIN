"""Keep terminal tracebacks, captured output and JUnit reports free of secrets."""

import pytest

from services.liorin_api.account_tests.redaction import PROTECTED, redact


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    report = yield
    if isinstance(report.longrepr, tuple):
        path, line, reason = report.longrepr
        report.longrepr = redact(path), line, redact(reason)
    elif report.longrepr:
        report.longrepr = redact(str(report.longrepr))
    report.sections = [(name, redact(content)) for name, content in report.sections]
    if report.when == 'teardown':
        PROTECTED.clear()
    return report
