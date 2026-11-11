from datetime import date

import pytest

from tongshu.engines.bazi_adapter import BaziAdapter
from tongshu.engines.bazi_engine import BaziEngine
from tongshu.engines.time.resolver import TimeResolver


@pytest.mark.parametrize("birth_date", [date(1990, 11, 10), date(2023, 12, 31), date(2024, 2, 29)])
def test_direct_and_adapter_agree_across_midnight(birth_date):
    from datetime import timedelta

    engine = BaziEngine()
    adapter = BaziAdapter(engine)
    resolver = TimeResolver()
    tomorrow = birth_date + timedelta(days=1)
    charts = []
    for day, hour, minute in [(birth_date, 22, 59), (birth_date, 23, 0),
                              (birth_date, 23, 59), (tomorrow, 0, 0)]:
        context = resolver.resolve_context(
            birth_date=day, hour=hour, minute=minute, timezone="Asia/Shanghai",
            location="beijing", apparent_solar=False, gender="male",
        )
        if hour == 23:
            assert any("日柱仍按当日" in warning for warning in context.warnings)
        adapted = adapter.compute(context, gender="male")
        direct = engine.compute((day.year, day.month, day.day, hour), gender="male")
        def pillars(chart):
            return tuple((p.heavenly_stem, p.earthly_branch) for p in
                         (chart.day_pillar, chart.hour_pillar))
        assert pillars(direct) == pillars(adapted)
        charts.append(pillars(adapted))

    assert charts[0][0] == charts[1][0] == charts[2][0]
    assert charts[0][1][1] == "HAI"
    assert charts[1][1][1] == charts[2][1][1] == "ZI"
    assert charts[3][0] != charts[2][0]
    assert charts[3][1] == charts[2][1]
