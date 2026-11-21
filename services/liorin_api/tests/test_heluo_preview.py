from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from services.liorin_api.app import create_app
from services.liorin_api.heluo_preview import compute_preview
from services.liorin_api.locations import LocationCatalogue
from services.liorin_api.time_context import BirthTimeRequest, normalize_birth_time

DATA = Path(__file__).resolve().parents[3] / 'data'


def test_real_adapter_keeps_mismatched_marker_under_review():
    birth = BirthTimeRequest(birth_date='1984-12-07', hour=16, minute=0,
                             location='CN_BEIJING', timezone='Asia/Shanghai')
    context = normalize_birth_time(birth, LocationCatalogue(DATA))
    result = compute_preview({'gender': 'male'}, context, date(2026, 8, 17), DATA / 'locations.json')
    assert result.rule == 'gua6'
    assert result.line.engine_time_marker.date() == date(2026, 8, 18)
    assert result.marker_matches_requested_date is False
    assert result.current_line_status == 'pending_review'


def test_default_runtime_does_not_expose_private_preview(monkeypatch):
    monkeypatch.delenv('LIORIN_ACCOUNT_MODE', raising=False)
    client = TestClient(create_app())
    assert client.get('/v1/personal/heluo-preview?target_date=2026-08-17').status_code == 404
    assert client.get('/v1/personal/heluo-today').status_code == 503
