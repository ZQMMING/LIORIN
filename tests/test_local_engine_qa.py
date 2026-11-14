"""本机引擎 QA 路由：默认不可见、显式开关后只返回有界摘要。"""
from __future__ import annotations

import os
import pytest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from tongshu.api.app import create_app


@pytest.fixture(autouse=True)
def test_authority(monkeypatch):
    monkeypatch.setenv("TONGSHU_AUTH_SECRET", "test-secret-for-qa-only-0123456789")
    monkeypatch.setenv("TONGSHU_AUTHORITY_CREDENTIALS",
        "architecture-governance:schema-v1-arch-gov-2026;admission_registry:test-cred-hash")


BODY = {"birth_date": "1980-06-22", "hour": 12, "gender": "male",
        "theme": "WORK", "analysis_date": "2026-08-17",
        "timezone": "Asia/Shanghai", "location": "Beijing"}


def test_qa_route_absent_in_default_app():
    with patch.dict(os.environ, {"LIORIN_LOCAL_ENGINE_QA": "1"}):
        client = TestClient(create_app())
    assert client.post("/v1/qa/engine", json=BODY).status_code == 404


def test_qa_route_returns_bounded_engine_summary():
    client = TestClient(create_app(local_qa=True))
    canonical = SimpleNamespace(canonical_id="CC-TEST", atomic_claims=[
        {"claim_id": "AC-ZP-one", "domain": "GEJU", "claim": "test claim", "evidence_refs": ["E-1"]}
    ], meta_observability={"trace_id": "TRACE-TEST"})
    chart = SimpleNamespace(get_pillars_chinese=lambda: {"year": "甲子", "month": "丙寅", "day": "戊辰", "hour": "庚午"})
    result = SimpleNamespace(canonical=canonical, source="computed", validation_passed=True,
                             bazi_chart=chart, ziwei_chart=None, blind_result=None,
                             heluo_result=None, yi_structure=None)
    from tongshu.pipeline import TONGSHUPipeline
    with patch.object(TONGSHUPipeline, "run", return_value=result) as run:
        r = client.post("/v1/qa/engine", json=BODY)
    assert r.status_code == 200, r.text
    assert r.json()["ziping_claim_count"] == 1
    assert r.json()["result_available"] == {"heluo": False, "yijing_structure": False}
    assert r.json()["claim_count"] == 1
    assert r.json()["validation_status"] == "not_run"
    assert r.json()["bazi_pillars"] == chart.get_pillars_chinese()
    assert "TEST ONLY" in r.json()["warning"]
    assert len(r.content) < 10000
    run.assert_called_once()
    assert run.call_args.kwargs["compute_only"] is True


def test_qa_route_rejects_incomplete_birth_context():
    client = TestClient(create_app(local_qa=True))
    r = client.post("/v1/qa/engine", json={**BODY, "location": None})
    assert r.status_code == 422


def test_qa_pillars_match_the_same_pipeline_chart():
    from tongshu.pipeline import TONGSHUPipeline

    client = TestClient(create_app(local_qa=True))
    original = TONGSHUPipeline.run
    observed = []

    def capture(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        observed.append(result.bazi_chart.get_pillars_chinese())
        return result

    with patch.object(TONGSHUPipeline, "run", capture):
        response = client.post("/v1/qa/engine", json={**BODY, "birth_minute": 30})
    assert response.status_code == 200, response.text
    assert len(observed) == 1
    assert response.json()["bazi_pillars"] == observed[0]
    assert set(observed[0]) == {"year", "month", "day", "hour"}
