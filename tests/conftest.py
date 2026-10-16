# -*- coding: utf-8 -*-
"""Global test fixtures.

Ziwei stub opt-in (B-03a guard): iztro is not installed in the dev/test
environment, and the production guard raises ZiweiEngineUnavailableError unless
TONGSHU_ALLOW_ZIWEI_STUB=1. Individual suites were setting this env themselves;
suites that reach the ziwei engine transitively (api/pipeline/canonical tests)
were missed, causing 35 failures in clean environments. Centralizing it here so
every test runs with the same engine availability assumptions.

This does NOT weaken any test semantics: the stub behavior itself is identical;
only the env gate is satisfied. Production default remains fail-closed.

P1.5 update: When iztro is installed, tests should run with real Runtime
(TONGSHU_ALLOW_ZIWEI_STUB unset). The stub is only for development when iztro
is unavailable. See tests/spec/test_p15_shadow_integration.py Gate A.

P2.1-B: Register test authority credential so test fixtures with
authority_source='admission_registry' pass G2 authority check.
"""
import os
from pathlib import Path

# Check if real iztro is available
_project_root = Path(__file__).parent.parent
_iztro_path = _project_root / "node_modules" / "iztro"
_iztro_available = _iztro_path.exists()

if not _iztro_available:
    # Fall back to stub for development
    os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")


def pytest_configure(config):
    """Register test authority credentials before tests run.

    P2.1-F: Authority is loaded via TONGSHU_AUTHORITY_CREDENTIALS env var,
    matching the production bootstrap path. Tests must set this env var
    (or the pipeline bootstrap will fail).
    """
    import os as _os
    from tongshu.assertion.admission_registry import (
        register_authority_credential, clear_authority_credentials,
    )
    clear_authority_credentials()
    # P2.1-F: Set test authority credential via env var (same path as production)
    # Must match the declared_credential_hash in production_assertion_rules.json
    _os.environ["TONGSHU_AUTHORITY_CREDENTIALS"] = (
        "architecture-governance:schema-v1-arch-gov-2026;"
        "admission_registry:test-cred-hash"
    )
    # Re-register to match what load_trust_root() would produce
    register_authority_credential("architecture-governance", "schema-v1-arch-gov-2026")
    register_authority_credential("admission_registry", "test-cred-hash")
