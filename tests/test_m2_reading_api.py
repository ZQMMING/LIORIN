"""Real API and pipeline; a deterministic renderer outage uses no network."""
from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest

from tongshu.cross_domain.result import (CrossDomainResult, DomainSemanticIndex,
    EngineAssertionSet, EngineEvidenceSet, MultiDomainSemanticCoverage)
from tongshu.cross_domain.status import derive_cross_status
from tongshu.pipeline_stages.compute_stage import ComputeStage
from tongshu.render.clients.openai_compat import RenderClientError
from tongshu.render.renderer import Renderer, StubLLMClient
from tongshu.render.template_fallback import TemplateFallback
from tests.test_m2_context_propagation import client  # noqa: F401


REQUEST = {'birth_date': '1980-06-22', 'hour': 12, 'birth_minute': 30,
           'gender': 'male', 'location': 'CN_BEIJING', 'timezone': 'Asia/Shanghai',
           'analysis_date': '2026-08-06', 'theme': 'WORK'}


def test_real_daily_guide_renderer_outage_uses_evidence_based_fallback(client):
    with patch.object(Renderer, 'render', side_effect=RenderClientError('test outage')):
        response = TestClient(client.app).post('/v1/daily-guide', json=REQUEST)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['source'] == 'template_fallback'
    assert body['rendered_text']
    assert body['engine_rule_status']['blind'] == 'pending_review'
    assert body['rendered_text'] == TemplateFallback().render('WORK', body['cross_status'])


def coverage_result(status):
    evidence = ['test-evidence'] if status != 'INSUFFICIENT' else []
    by_engine = {
        'one': EngineEvidenceSet('one', evidence_ids=evidence),
        'two': EngineEvidenceSet('two', evidence_ids=evidence if status == 'ALIGNED' else []),
    }
    index = DomainSemanticIndex('work', 'test', {'one': EngineAssertionSet('one', ['test-assertion'])})
    coverage = MultiDomainSemanticCoverage({'work': {'test': index}} if evidence else {})
    return CrossDomainResult('test', 'DAY', by_engine, coverage)


def test_partial_evidence_without_assertions_is_insufficient_in_both_forms():
    data = coverage_result('PARTIAL')
    data = CrossDomainResult(data.case_id, data.temporal_scope, data.by_engine,
                             MultiDomainSemanticCoverage({}))
    assert derive_cross_status(data) == 'INSUFFICIENT'
    assert derive_cross_status(data.to_dict()) == 'INSUFFICIENT'


@pytest.mark.parametrize('expected', ['ALIGNED', 'PARTIAL', 'INSUFFICIENT'])
def test_actual_reading_api_template_matches_coverage(client, expected):
    # Only orchestration evidence is synthetic; API, compute, render and
    # serialization paths are the production entities. No assertion is promoted
    # into an authorized claim by this fixture.
    with patch.object(ComputeStage, '_orchestrate_signals', return_value=coverage_result(expected)), \
         patch.object(ComputeStage, '_extract_authorizations', return_value=[]), \
         patch.object(Renderer, 'render', side_effect=RenderClientError('test outage')):
        response = client.post('/v1/daily-guide', json=REQUEST)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['cross_status'] == expected
    assert body['rendered_text'] == TemplateFallback().render('WORK', expected)
    assert body['engine_rule_status']['blind'] == 'pending_review'
    assert {'ALIGNED': '不代表结论一致', 'PARTIAL': '证据不足',
            'INSUFFICIENT': '证据不足以支持判断'}[expected] in body['rendered_text']


def test_actual_reading_api_with_local_stub_renderer(client):
    stub = Renderer(StubLLMClient())
    with patch.object(Renderer, 'render', side_effect=stub.render):
        response = client.post('/v1/daily-guide', json=REQUEST)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['engine_rule_status']['blind'] == 'pending_review'
    assert body['cross_status'] in ('ALIGNED', 'PARTIAL', 'INSUFFICIENT')
    assert body['rendered_text']
    assert not any('blind' in str(claim).casefold() for claim in body['atomic_claims'])
