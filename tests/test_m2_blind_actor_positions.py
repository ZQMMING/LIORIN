from datetime import date

import pytest

from tongshu.engines.bazi_adapter import BaziAdapter
from tongshu.engines.bazi_engine import BaziEngine
from tongshu.engines.blind_bazi_engine import BlindBaziEngine, _branch_element
from tongshu.engines.time.resolver import TimeResolver


@pytest.mark.parametrize(('birth_date', 'has_drain'), [
    (date(1980, 2, 6), True),
    (date(1980, 2, 18), False),
])
def test_repeated_branch_actor_is_position_based_with_other_rules(birth_date, has_drain):
    """Regression of current provisional behavior, not approval of its meaning."""
    context = TimeResolver().resolve_context(
        birth_date=birth_date, hour=18, minute=30, timezone='Asia/Shanghai',
        location='CN_BEIJING', gender='male',
    )
    chart = BaziAdapter(BaziEngine()).compute(context, gender='male')
    branches = [getattr(chart, name).earthly_branch for name in (
        'year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar')]
    assert branches[2] == branches[3]  # duplicate branch occurs in both main positions
    result = BlindBaziEngine().compute_from_chart(chart, gender='male')
    methods = result.zuo_gong_methods
    dimensions = result.zuo_gong_actor_dimensions
    assert len(methods) == len(dimensions) == len(result.zuo_gong_attributions)
    assert len(methods) > 1  # prior rules must not leak their actor into later rules
    assert ('\u98df\u4f24\u6cc4\u79c0' in methods) is has_drain
    if has_drain:
        assert dimensions[methods.index('\u98df\u4f24\u6cc4\u79c0')] == 'SELF_DIRECT'
    index = methods.index('\u52bf\u505a\u529f')
    assert dimensions[index] == 'TOOL_ASSISTED'
    elements = [_branch_element(branch) for branch in branches]
    assert any(elements.count(element) >= 3 for element in elements[2:])
