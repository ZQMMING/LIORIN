"""Calendar 去 Mock — real 黄历 engine tests (V4.0.1 §7.4).

Deterministic real 黄历 computation (lunar_python 1.4.8 + 日柱干支锚定).

独立核对 (2026-08-18, Claude):
  - 建除: 月支申为「建」,顺数 日支亥 → 平 ✓ (建除满平定执破危成收开闭)
  - 值神: 黄道黑道十二值神,亥日 → 勾陈(黑道·凶) ✓
  - 冲:   巳亥六冲 → 冲巳 ✓
  - 煞:   亥卯未日煞西(申酉戌) → 煞西 ✓
  - 纳音: 丙午=天河水, 丙申=山下火, 壬戌癸亥=大海水 ✓
  - 农历: 2026-08-17 = 农历七月 初五, 孟秋 ✓
  - 二十八宿/宜忌/吉神凶煞: lunar_python 确定性表推导;独立核对待补
    (已记入 backend/data/calendar_sources.json verification_status)
"""

from __future__ import annotations
import unittest
from datetime import date

from tongshu.engines.huangli_engine import BRANCH_CN, STEM_CN, HuangliDay, HuangliEngine

_D = date(2026, 8, 17)


class TestHuangliEngine(unittest.TestCase):
    def setUp(self):
        self.engine = HuangliEngine()

    # ------------------------------------------------------------------ #
    # 2026-08-17 已知值(独立核对)
    # ------------------------------------------------------------------ #

    def test_known_values_2026_08_17(self):
        hl = self.engine.get_day(_D)
        # 干支 + 农历
        self.assertEqual(hl.year_ganzhi, "丙午")
        self.assertEqual(hl.month_ganzhi, "丙申")
        self.assertEqual(hl.day_ganzhi, "癸亥")
        self.assertEqual(hl.lunar_month, "七")
        self.assertEqual(hl.lunar_day, "初五")
        self.assertEqual(hl.lunar_month_label, "农历七月 · 孟秋")
        self.assertEqual(hl.sheng_xiao, "马")
        # 建除 / 值神 / 冲 / 煞 / 纳音(独立核对)
        self.assertEqual(hl.jianchu, "平")
        self.assertEqual(hl.zhishen, "勾陈")
        self.assertEqual(hl.zhishen_type, "黑道")
        self.assertEqual(hl.zhishen_luck, "凶")
        self.assertEqual(hl.chong, "巳")
        self.assertEqual(hl.chong_shengxiao, "蛇")
        self.assertEqual(hl.sha, "西")
        self.assertEqual(hl.nian_na_yin, "天河水")
        self.assertEqual(hl.month_na_yin, "山下火")
        self.assertEqual(hl.day_na_yin, "大海水")
        # 节气区间(非交节日)
        self.assertEqual(hl.jie_qi, "")
        self.assertEqual(hl.prev_jie_qi, ("立秋", "2026-08-07"))
        self.assertEqual(hl.next_jie_qi, ("处暑", "2026-08-23"))

    def test_yi_ji_ji_xiang_xiong_sha_deterministic(self):
        hl = self.engine.get_day(_D)
        # lunar_python 确定性表输出(逐条引证待核对,见 registry)
        self.assertEqual(hl.yi, ["修饰垣墙", "平治道涂", "祭祀", "沐浴", "作灶"])
        self.assertEqual(
            hl.ji,
            ["嫁娶", "词讼", "治病", "置产", "作梁", "祈福", "安葬", "栽种", "伐木", "安门"],
        )
        self.assertEqual(hl.ji_xiang, ["天德", "四相", "相日", "普护"])
        self.assertEqual(hl.xiong_sha, ["天罡", "死神", "月害", "游祸", "五虚", "重日", "勾陈"])

    # ------------------------------------------------------------------ #
    # golden 语义稳定:day_stem/day_branch 锚定不变
    # ------------------------------------------------------------------ #

    def test_day_stem_branch_anchor_stable(self):
        hl = self.engine.get_day(_D)
        self.assertEqual(hl.day_stem, "GUI")
        self.assertEqual(hl.day_branch, "HAI")
        # 锚定干支与 lunar 日干支一致(硬一致校验在引擎内执行,漂移即失败)
        self.assertEqual(f"{STEM_CN[hl.day_stem]}{BRANCH_CN[hl.day_branch]}", hl.day_ganzhi)

    def test_legacy_positional_construction_compatible(self):
        # 旧调用方式仍可构造(pipeline 只读 day_stem/day_branch)
        hl = HuangliDay(_D, "GUI", "HAI")
        d = hl.to_dict()
        self.assertEqual(d["day_stem"], "GUI")
        self.assertEqual(d["day_branch"], "HAI")
        self.assertEqual(d["yi"], [])

    # ------------------------------------------------------------------ #
    # 确定性 + 来源登记
    # ------------------------------------------------------------------ #

    def test_determinism(self):
        self.assertEqual(self.engine.get_day(_D), self.engine.get_day(_D))
        self.assertEqual(
            self.engine.get_day(_D).to_dict(), self.engine.get_day(_D).to_dict()
        )

    def test_source_registry_loaded(self):
        ids = {s["source_id"] for s in self.engine.source_registry}
        self.assertIn("lunar_python", ids)
        self.assertIn("day_stem_branch_anchor", ids)
        hl = self.engine.get_day(_D)
        self.assertEqual(set(hl.source_ids), {"lunar_python", "day_stem_branch_anchor", "ganzhi_daily_hexagram"})

    def test_to_dict_full_shape(self):
        d = self.engine.get_day(_D).to_dict()
        for key in (
            "solar_date", "day_stem", "day_branch", "year_ganzhi", "month_ganzhi",
            "day_ganzhi", "lunar_month", "lunar_day", "lunar_month_label", "jie_qi",
            "prev_jie_qi", "next_jie_qi", "jianchu", "zhishen", "zhishen_type",
            "zhishen_luck", "xiushu", "xiushu_luck", "chong", "chong_shengxiao",
            "sha", "sheng_xiao", "nian_na_yin", "month_na_yin", "day_na_yin",
            "peng_zu_gan", "peng_zu_zhi", "position_xi", "position_fu",
            "position_cai", "yi", "ji", "ji_xiang", "xiong_sha", "source_ids",
        ):
            self.assertIn(key, d)


if __name__ == "__main__":
    unittest.main()
