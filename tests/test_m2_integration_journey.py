"""Combined API regression across the three independently reviewed changes."""
from datetime import date
from unittest.mock import patch

import pytest

from tests.test_m2_context_propagation import client  # noqa: F401
from tests.test_m2_reading_api import REQUEST
from tongshu.pipeline_stages.compute_stage import ComputeStage
from tongshu.render.clients.openai_compat import RenderClientError
from tongshu.render.renderer import Renderer
from tongshu.render.template_fallback import TemplateFallback


@pytest.mark.parametrize(('blind', 'blind_status'), [
    ((None, None, None), 'unavailable'),
    ((object(), None, object()), 'partial'),
])
def test_today_and_reading_degradation_are_visible_together(client, blind, blind_status):
    class ServerDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 8, 5)

    with patch('tongshu.api.app.date', ServerDate):
        explicit = client.get('/v1/today?date=2026-08-06')
        default = client.get('/v1/today')
    assert explicit.status_code == default.status_code == 200
    assert explicit.json()['date_context']['source'] == 'explicit_date'
    assert explicit.json()['date_context']['date'] == '2026-08-06'
    assert default.json()['date_context']['source'] == 'server_local_date'
    assert default.json()['date_context']['date'] == '2026-08-05'

    with patch.object(ComputeStage, '_compute_blind', return_value=blind), \
         patch.object(Renderer, 'render', side_effect=RenderClientError('test outage')):
        reading = client.post('/v1/daily-guide', json=REQUEST)
    assert reading.status_code == 200, reading.text
    body = reading.json()
    assert body['engine_status']['blind'] == blind_status
    assert body['engine_rule_status']['blind'] == 'pending_review'
    assert body['heluo_day_status'] == {'status': 'unavailable', 'reason': 'missing', 'match_count': 0}
    assert body['rendered_text'] == TemplateFallback().render('WORK', body['cross_status'])
    assert body['source'] == 'template_fallback'
