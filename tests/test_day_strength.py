"""日主旺衰判定 oracle 测试 (得令/得地/得势)."""
import pytest

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.reasoning.day_strength import calc_day_strength


@pytest.fixture(scope="module")
def be():
    return BaziEngine()


def _strength(be, y, m, d, h, gender="male"):
    ch = be.compute((y, m, d, h), gender=gender)
    return calc_day_strength(ch)


class TestDayStrength:
    def test_1989_three_strong(self, be):
        # 26亥/26子 庚日主: 年支巳=长生, 日支申=临官(禄), 双根 → 强
        r1 = _strength(be, 1989, 12, 26, 21)
        r2 = _strength(be, 1989, 12, 26, 0)
        assert r1["strength"] == "强"
        assert r2["strength"] == "强"
        assert r1["di"] >= 4
        # 27子 辛日主: 日支酉=临官, 月/时子=长生 → 强
        r3 = _strength(be, 1989, 12, 27, 0)
        assert r3["strength"] == "强"

    def test_mao_1893_strong(self, be):
        # 毛 1893-12-26 20时 丁日主: 酉=长生, 巳=帝旺, 甲木印 → 强
        r = _strength(be, 1893, 12, 26, 20)
        assert r["day_master"] == "DING"
        assert r["strength"] == "强"

    def test_fields_complete(self, be):
        r = _strength(be, 1989, 12, 26, 21)
        assert r["ling"] in (0, 1, 2)
        assert r["total"] == r["ling"] + r["di"] + r["shi"]
        assert r["strength"] in ("强", "中和", "弱")
        assert r["evidence"]
        assert r["roots"]
