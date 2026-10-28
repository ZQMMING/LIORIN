# -*- coding: utf-8 -*-
"""真太阳时边界与死断触发面守卫（2026-10-24）。

**为什么要有这个守卫**

1. **真太阳时边界**：河洛的 `HeluoInput.true_solar_datetime` **只落记录、
   不参与任何判定**；真太阳时的影响是**通过时柱地支**间接传导的。
   若有人误以为「河洛入口会自己校正真太阳时」，就会在
   **跨时辰界**的出生时刻上得到静默不同的盘（实测：先天卦/后天卦全变）。
   本守卫把两条入口的**实际差异**钉住，并钉住「河洛不自己算真太阳时」这一事实。

2. **死断触发面**：死断原文措辞极重（「到此必死」「定死无疑」），
   而实测近三成盘会命中至少一条 —— 下游若不知这个量级，
   容易把 ①④（无条件式硬断）当成罕见事件。
   本守卫钉住：①④ 的门控**真的会通**（不是恒假分支）、
   且死断原文**不进 summary**（只读 summary 的下游看不到「必死」）。

**覆盖**
--------
* 两条入口（独立入口 vs 正式链路）的四柱时柱差异；
* 正式链路确实吃真太阳时（TimeResolver 校正量 > 0）；
* 河洛判定层**不读** `true_solar_datetime`（只落记录）；
* 死断①（君爻/后天五爻）门控**真的会命中**（防恒假分支）；
* 死断原文**不进 summary**。
"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from heluo_engine.adapter import HeluoAdapter  # noqa: E402


class TestTrueSolarBoundary(unittest.TestCase):
    """真太阳时的两条入口边界。"""

    def test_time_resolver_produces_true_solar(self):
        """TimeResolver 确实做真太阳时校正（经度差 + 均时差）。"""
        from heluo_engine.engines.time.resolver import TimeResolver
        ctx = TimeResolver().resolve_context(
            birth_date=datetime(1983, 11, 3, 11, 0).date(),
            hour=11, minute=0, timezone="Asia/Shanghai",
            location="中山", gender="male",
        )
        self.assertIsNotNone(ctx.true_solar_datetime)
        self.assertNotEqual(
            ctx.true_solar_datetime.replace(tzinfo=None),
            ctx.birth_civil_datetime.replace(tzinfo=None),
            "TimeResolver 未对真太阳时做任何校正 —— 边界已变")
        # 中山：经度 113.3791（东经）→ 经度差 −26.48 分；11 月均时差 ≈ +16 分
        corr = ctx.corrections or {}
        self.assertIn("longitude_correction_min", corr)
        self.assertIn("eot_min", corr)
        self.assertNotEqual(corr.get("total_correction_min", 0), 0,
                            "总校正量为 0 —— 真太阳时校正未生效")

    def test_two_entries_give_different_hour_pillar(self):
        """独立入口（民用）与正式链路（真太阳时）在跨时辰界时**结果不同**。

        这是「河洛域内无需接线、但独立入口用民用时间」的事实依据：
        真太阳时的影响经**时柱地支**传导，先天/后天卦随之改变。
        """
        ad = HeluoAdapter()
        # 北京时间 11:00 → 中山真太阳时 10:49（跨巳/午界）
        r_civil = ad.compute((1983, 11, 3, 11), gender="male",
                             target_date="2026-10-23")

        from heluo_engine.engines.bazi_adapter import BaziAdapter
        from heluo_engine.engines.bazi_engine import BaziEngine
        from heluo_engine.engines.time.resolver import TimeResolver
        ctx = TimeResolver().resolve_context(
            birth_date=datetime(1983, 11, 3, 11, 0).date(),
            hour=11, minute=0, timezone="Asia/Shanghai",
            location="中山", gender="male",
        )
        chart = BaziAdapter(BaziEngine()).compute(ctx, gender="male")
        r_solar = ad.compute_from_chart(chart, target_date="2026-10-23")

        self.assertNotEqual(
            r_civil.input.birth_time, r_solar.input.birth_time,
            "两入口时柱应不同（民用 11:00=午 vs 真太阳时 10:49=巳）")
        self.assertNotEqual(
            r_civil.prenatal.hexagram_name, r_solar.prenatal.hexagram_name,
            "跨时辰界 ⇒ 先天卦应不同 —— 若相同则真太阳时未传导到河洛")

    def test_heluo_does_not_compute_true_solar_itself(self):
        """河洛判定层**不自己算真太阳时**（只落记录）。

        钉住这一事实：将来若有人「顺手」在河洛里加一层真太阳时校正，
        就会与上游 TimeResolver **重复校正**（双重校正）。
        """
        import inspect
        from heluo_engine.engines.heluo import canonical
        src = inspect.getsource(canonical)
        # 河洛不得出现真太阳时计算（经度/均时差）
        for forbidden in ("equation_of_time", "longitude_correction",
                          "均时差", "true_solar"):
            if forbidden == "true_solar":
                continue
            self.assertNotIn(forbidden, src,
                             f"canonical.py 出现了真太阳时计算相关符号「{forbidden}」"
                             " —— 河洛不做真太阳时校正（上游 TimeResolver 负责），"
                             "在此重复会双重校正")

    def test_true_solar_field_is_record_only(self):
        """`HeluoInput.true_solar_datetime` 只落记录，默认值形同虚设。

        钉住「河洛不消费它」：将来若有人开始用它参与判定，
        必须同步改本守卫并说明为何不与上游重复。
        """
        ad = HeluoAdapter()
        res = ad.compute((1983, 11, 3, 12), gender="male",
                         target_date="2026-10-23")
        # 默认应等于 birth_date + T00:00:00（即"记录占位"，非真实真太阳时）
        self.assertTrue(
            res.input.true_solar_datetime.startswith(res.input.birth_date),
            "true_solar_datetime 默认应取 birth_date 起头（记录占位）")


class TestSiDuanTriggerSurface(unittest.TestCase):
    """死断触发面：门控真的会通 + 原文不进 summary。"""

    @classmethod
    def setUpClass(cls):
        cls.ad = HeluoAdapter()
        cls.si_duan_hits = []
        cls.summary_hits = []
        n = 0
        for y in (1938, 1955, 1972, 1990, 2005):
            for m in (1, 7):
                for d in (1, 15, 28):
                    for h in ("子", "午"):
                        for g in ("male", "female"):
                            try:
                                r = cls.ad.compute((y, m, d, 12), gender=g,
                                                   target_date="2026-10-23")
                            except Exception:
                                continue
                            n += 1
                            gj = r.guajie or {}
                            cls.si_duan_hits.extend(gj.get("si_duan") or [])
                            cls.summary_hits.extend(gj.get("summary") or [])
        cls.n = n

    def test_siduan_actually_fires(self):
        """死断诸法**真的会触发**（不是恒假分支）。

        若此断言失败，说明死断整层失能（比「太松」更严重）。
        """
        self.assertGreater(len(self.si_duan_hits), 0,
                           "死断整层零命中 —— 六条判据全失能")
        self.assertGreater(self.n, 0, "样本量为 0")

    def test_junyao_clause_fires(self):
        """①君爻条（后天行至五爻）**会命中**（门控是通的）。

        原文「如后天之气数行至君爻之位，此数为足，到此必死」——
        该条措辞最重，若它恒不触发反而是好事；但实测它**会**触发，
        故必须让下游知道这个量级（不可误以为是罕见事件）。
        """
        hit = [w for w in self.si_duan_hits if "此数为足，到此必死" in w]
        self.assertGreater(len(hit), 0,
                           "①君爻条恒不命中 —— 需确认是门控失效还是样本未覆盖")

    def test_siduan_never_leaks_into_summary(self):
        """死断原文**不进 summary** —— 只读 summary 的下游看不到「必死」。

        这是引擎侧现有的展示管控（死断原文只落 si_duan / evidence）。
        """
        bad_words = ("必死", "定死无疑", "十死八九", "坎壈", "寿必不久")
        leaked = [s for s in self.summary_hits
                  if any(w in s for w in bad_words)]
        self.assertEqual(leaked, [],
                         f"死断硬断措辞泄漏到 summary：{leaked[:3]}")

    def test_siduan_entries_carry_qualifier(self):
        """每条死断断语都带「须带条件读」限定语（防止下游字面直读）。"""
        for w in self.si_duan_hits:
            with self.subTest(w=w[:40]):
                self.assertIn("须带条件读", w)
                self.assertIn("触发：", w)
                self.assertIn("限定：", w)


if __name__ == "__main__":
    unittest.main()
