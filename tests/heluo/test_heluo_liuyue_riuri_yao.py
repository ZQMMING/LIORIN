# -*- coding: utf-8 -*-
"""流月/流日取爻守卫（2026-10-24）。

**为什么要有这个守卫**
------------------

流月卦的起卦基准是**该年流年卦的行年爻**（小象行年爻）。
原典（起例卷之上·起月卦例 L125-L128，三源逐字一致）：

  「凡起月卦，**就年卦中前一位起**，单月变爻，双月变应爻。
    假如**观卦上九爻流年**，进一位从初爻变起。
    已上先将单月挨次变去排定，然后双月取变卦之应爻变之。」
  「又假如**小象是泰卦九二**，卦应爻居五，双月取应爻。」

  → 「年卦」= 流年卦（小象行年卦）；「观卦上九爻流年」的「上九」是那一年的
    **行年爻**（小象游变到的那一爻），**不是**大运段元堂爻。

⚠ 2026-10-24 修正（此前无守卫，且实现用错基准）：
  原实现 `compute_liuyue(y.lines, yyt)` 传的是**大运段元堂爻** —— 同一大运段内
  9 年**恒定**，于是该段各年的流月序列**完全相同**，与原典「流月逐年不同」相悖。
  实测 1983-11-03 午时：2026 年 12 个流月里 **10 个卦名不同**。

**流日取爻**（同段，起日卦例 L129-L131）经核**无缺陷**：
  「以**流月卦前一爻为初一日**，每一爻管五日，**阳日寻阳爻位**（初三五），
    **阴日寻阴爻位**（二四上）……假如正月得乾卦初爻，初一日当在三爻，
    变为履六三；初二日变履九四为中孚六四；……」—— 引擎逐字对应，
  故本守卫同时**钉住**这一既成正确行为，防将来被改坏。

**覆盖**
--------
* 流月基准 = 该年行年爻（对拍原典观卦例、泰卦例）；
* 流月序列逐年不同（不与大运段元堂混用）；
* 流日逐日爻位 = 原典「初一日当在三爻…挨次而变」实例逐字比对。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from heluo_engine.engines.heluo.numbers import build_six_lines  # noqa: E402
from heluo_engine.engines.heluo.timeline_yun import (  # noqa: E402
    compute_liuyue, liuri_day_positions, liuri_day_lines,
)
from heluo_engine.engines.heluo.guajie import _yao_name  # noqa: E402


class TestLiuYueBaseIsXingNianYao(unittest.TestCase):
    """流月起卦基准 = 年卦行年爻。"""

    def test_guan_original_case(self):
        """原典「假如观卦上九爻流年，进一位从初爻变起」。

        观卦（巽上艮下）lines = build_six_lines("巽", "艮")
        上九 = 爻位 5 → 进一位 = 初爻(0)
        """
        guan = build_six_lines("巽", "艮")
        res = compute_liuyue(guan, 5)      # 5 = 行年爻（上九）
        got = {m["month"]: m for m in res.months}
        self.assertEqual(got[1]["yue_yao_index"], 0, "月1 应从初爻起")
        self.assertEqual(got[1]["name"], "风火家人", "观卦单月变初爻 → 风火家人")
        self.assertEqual(got[2]["yue_yao_index"], 3, "月2 应变应爻（爻位3）")
        self.assertEqual(got[2]["name"], "天火同人", "观卦双月变应爻 → 天火同人")
        self.assertEqual(got[3]["yue_yao_index"], 1, "月3 应进一位到爻位1")
        self.assertEqual(got[3]["name"], "风天小畜", "月3 卦名")

    def test_tai_original_case(self):
        """原典「又假如小象是泰卦九二，卦应爻居五，双月取应爻」。

        泰卦九二 = 爻位 1 → 十二月双月取其应爻（居五 = 爻位 4）。
        """
        tai = build_six_lines("坤", "乾")
        res = compute_liuyue(tai, 1)       # 1 = 行年爻（九二）
        got = {m["month"]: m for m in res.months}
        yang = [got[m]["yue_yao_index"] for m in (1, 3, 5, 7, 9, 11)]
        self.assertEqual(yang, [2, 3, 4, 5, 0, 1],
                         "阳月居位 = 九二 + 1…+6（三、四、五、上、初、二）")
        yin = [got[m]["yue_yao_index"] for m in (2, 4, 6, 8, 10, 12)]
        self.assertEqual(yin, [5, 0, 1, 2, 3, 4],
                         "双月取当月居位变爻的应爻（隔三位）")
        self.assertEqual(got[12]["yue_yao_index"], 4,
                         "十二月双月取九二的应爻，居五（爻位4）")


class TestLiuYueUsesXingNianYaoInPipeline(unittest.TestCase):
    """端到端：流月基准必须是该年流年卦的**行年爻**，不是大运段元堂爻。"""

    def test_month_sequence_differs_from_dayun_segment_base(self):
        """流月序列**不得**等于「以大运段元堂爻起算」的结果。

        原实现用段元堂爻作基准 → 该基准在同一大运段内恒定。
        本断言直接对比两种基准：两者必须不同（否则说明仍未用行年爻）。
        """
        from heluo_engine.adapter import HeluoAdapter
        ad = HeluoAdapter()
        res = ad.compute((1983, 11, 3, 12), gender="male",
                         target_date="2026-10-23")
        checked = 0
        for e in (res.timeline.yearly_hexagrams or []):
            months = e.get("months") or []
            if not months:
                continue
            xy = e.get("xingnian_yao_index")
            seg = e.get("dayun_seg_yuantang_index")
            if not isinstance(xy, int) or not isinstance(seg, int):
                continue
            if xy == seg:
                continue          # 两者恰同，无从区分
            by_xing = [m["name"] for m in compute_liuyue(e["lines"], xy).months]
            by_seg = [m["name"] for m in compute_liuyue(e["lines"], seg).months]
            with self.subTest(year=e["year"]):
                self.assertNotEqual(
                    by_xing, by_seg,
                    f"{e['year']}：行年爻与段元堂爻起算结果相同 —— 无法区分基准")
            checked += 1
        self.assertGreater(checked, 0,
                           "未找到行年爻 ≠ 段元堂爻的年份，无法验证基准")

    def test_month_base_equals_xingnian_yao(self):
        """流月序列须由「行年爻」起（与 compute_liuyue(年卦, 行年爻) 逐字一致）。"""
        from heluo_engine.adapter import HeluoAdapter
        ad = HeluoAdapter()
        res = ad.compute((1983, 11, 3, 12), gender="male",
                         target_date="2026-10-23")
        for e in (res.timeline.yearly_hexagrams or []):
            months = e.get("months") or []
            if not months:
                continue
            xy = e.get("xingnian_yao_index")
            self.assertIsInstance(xy, int,
                                  "年卦条目须带 xingnian_yao_index")
            want = compute_liuyue(e["lines"], xy)
            self.assertEqual([m["name"] for m in months],
                             [m["name"] for m in want.months],
                             f"{e['year']} 的流月序列与「以行年爻起算」不符")


class TestLiuRiDayPositions(unittest.TestCase):
    """流日逐日爻位（原典「阳日寻阳位、阴日寻阴位」）—— 既成正确，防回退。"""

    def test_qian_first_yao_original_case(self):
        """原典「假如正月得乾卦初爻，初一日当在三爻，变为履六三……」

        乾卦 = build_six_lines("乾", "乾")；月卦居位变爻 = 初爻(0)
        逐日：初一→三爻、二→四爻、三→五爻、四→上爻、五→初爻
        """
        qian = build_six_lines("乾", "乾")
        pos = liuri_day_positions(0)
        self.assertEqual(pos[:5], [2, 3, 4, 5, 0],
                         "原典逐日爻位：初一三爻、初二四爻、初三五爻、初四上爻、初五初爻")

    def test_day_lines_follow_original_case(self):
        """逐日卦：初一变履六三、初二变中孚六四……（挨次而变）。"""
        qian = build_six_lines("乾", "乾")
        dl = liuri_day_lines(qian, 0)
        # 原典：初一日当在三爻，变为履六三
        self.assertEqual(dl[0][0], 2, "初一日变爻位应为三爻")
        self.assertEqual(dl[0][1], [1, 1, -1, 1, 1, 1],
                         "初一日之卦应为履六三（离下乾上）")
        # 初二日变履九四为中孚六四
        self.assertEqual(dl[1][0], 3, "初二日变爻位应为四爻")
        self.assertEqual(dl[1][1], [1, 1, -1, -1, 1, 1],
                         "初二日之卦应为中孚六四")
        # 初三日变中孚九五为损六五
        self.assertEqual(dl[2][1], [1, 1, -1, -1, -1, 1],
                         "初三日之卦应为损六五")

    def test_each_yao_appears_five_times(self):
        """「每一爻管五日」：30 日内每爻恰 5 次。"""
        for base in range(6):
            with self.subTest(base=base):
                pos = liuri_day_positions(base)
                self.assertEqual(len(pos), 30)
                counts = [pos.count(i) for i in range(6)]
                self.assertEqual(counts, [5] * 6,
                                 f"每爻应恰管 5 日，实得 {counts}")

    def test_yang_days_on_yang_positions(self):
        """阳日（奇数日）只落在阳位（初/三/五）；阴日只落阴位（二/四/上）。"""
        pos = liuri_day_positions(3)
        for i, p in enumerate(pos):
            with self.subTest(day=i + 1):
                if (i + 1) % 2 == 1:
                    self.assertIn(p, (0, 2, 4), "阳日应取阳位（初/三/五）")
                else:
                    self.assertIn(p, (1, 3, 5), "阴日应取阴位（二/四/上）")


if __name__ == "__main__":
    unittest.main()
