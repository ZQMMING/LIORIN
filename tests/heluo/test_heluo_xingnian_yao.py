# -*- coding: utf-8 -*-
"""「小象行年爻」守卫（2026-10-24）。

**为什么要有这个守卫**
------------------

流年断爻取的是**小象行年爻** = 该年小象游变**变出的那一爻**。
原典（起例卷之上·小象行年卦气，三源逐字一致）：

  「其一年变一卦之法亦自本卦之爻而始。假如同人九三爻是元堂，其阳爻九年者，
    此大象也。其小象当看此年是阳是阴。如此年是阳年则不变，
    一岁在同人九三（阳）爻；二岁取应爻变，同人上九为革上六；
    三岁复取应爻变，革九三为随六三；然后自下而上，
    四岁变随九四为屯六四；五岁变屯九五为复六五；六岁变复上六为颐上九；
    七岁变颐初九为剥初六；八岁变剥六二为蒙九二；九岁变蒙六三为蛊九三」

⚠ 2026-10-24 修正（此前无守卫，且实现取错爻）：
  原实现取「**年卦的元堂爻**」= **大运段爻**（`yuantang_index`）——
  同一大运段内 9 年**恒定不变**（实测 2024/2025/2026 皆取「上九」），
  而原典要求行年爻**逐年挨次变**。后果：流年判词整层取错爻，
  且同一大运段内各年流年判词完全相同 —— 与原典「流年若佳，未有不应之者」
  （流年逐年不同才谈得上应期）相悖。

本守卫把原典硬算例（同人九三为例的九年逐岁卦名 + 行年爻）钉成回归断言。

**覆盖**
--------
* `compute_liunian` 的九年序列与原典逐字比对（卦名 + 行年爻位）；
* 「行年爻逐年不同」（除首年不变的情形）；
* 端到端：流年判词所取之爻 == 该年 `xingnian_yao_index` 对应之爻。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tongshu.engines.heluo.timeline_yun import (  # noqa: E402
    compute_liunian, _flip_line, _lines_to_hexagram,
)
from tongshu.engines.heluo.guajie import _yao_name  # noqa: E402

#: 同人卦（天火同人）：上乾下离，自下而上 = 离(1,-1,1) + 乾(1,1,1)
TONG_REN = [1, -1, 1, 1, 1, 1]
#: 原典「同人九三爻是元堂」→ 元堂 index 2
YUANTANG_9_3 = 2

#: 原典硬算例（起例卷之上·小象行年卦气）：岁 → (流年卦名, 行年爻位)
#: 「一岁在同人九三（阳）爻；二岁取应爻变，同人上九为革上六；三岁复取应爻变，
#:  革九三为随六三；然后自下而上，四岁变随九四为屯六四；五岁变屯九五为复六五；
#:  六岁变复上六为颐上九；七岁变颐初九为剥初六；八岁变剥六二为蒙九二；
#:  九岁变蒙六三为蛊九三」
ORIGINAL_NINE = [
    (1, "天火同人", 2),   # 一岁在同人九三（阳）爻
    (2, "泽火革", 5),     # 二岁取应爻变 → 同人上九为革上六
    (3, "泽雷随", 2),     # 三岁复取应爻变 → 革九三为随六三
    (4, "水雷屯", 3),     # 四岁变随九四为屯六四
    (5, "地雷复", 4),     # 五岁变屯九五为复六五
    (6, "山雷颐", 5),     # 六岁变复上六为颐上九
    (7, "山地剥", 0),     # 七岁变颐初九为剥初六
    (8, "山水蒙", 1),     # 八岁变剥六二为蒙九二
    (9, "山风蛊", 2),     # 九岁变蒙六三为蛊九三
]


class TestXiaoXiangXingNianYao(unittest.TestCase):
    """小象行年爻：原典硬算例逐字对拍。"""

    @classmethod
    def setUpClass(cls):
        # 用一个阳年起始的段（段首阳年 → 一岁不变），与原典「如是阳年则不变」一致
        cls.res = compute_liunian(
            prenatal_lines=TONG_REN, prenatal_yuantang=YUANTANG_9_3,
            postnatal_lines=TONG_REN, postnatal_yuantang=YUANTANG_9_3,
            birth_year=2024, age_from=1, age_to=9,
        )

    def test_nine_year_hexagram_names_match_original(self):
        """九年流年卦名须与原典硬算例逐字一致。"""
        got = [(y.age, y.hexagram_name) for y in self.res.years]
        want = [(a, n) for a, n, _ in ORIGINAL_NINE]
        self.assertEqual(got, want, "流年卦名序列与原典硬算例不符")

    def test_xingnian_yao_index_match_original(self):
        """行年爻位须与原典硬算例一致。"""
        for y in self.res.years:
            want = dict((a, i) for a, _, i in ORIGINAL_NINE)[y.age]
            with self.subTest(age=y.age):
                self.assertEqual(
                    y.xingnian_yao_index, want,
                    f"{y.age} 岁行年爻位应为 {want}，实得 {y.xingnian_yao_index}")

    def test_xingnian_yao_not_constant_within_segment(self):
        """行年爻**不能**在同一大运段内恒定。

        原典「挨次而变」：九年行年爻走满一轮（2,5,2,3,4,5,0,1,2），
        其中 1/3/9 年同为 index 2 是**循环回绕**的必然结果（6 爻一轮），
        但**不能整段同值**——那正是旧实现取「年卦的元堂爻」的表现
        （大运段爻固定 → 9 年行年爻全同）。
        """
        idxs = [y.xingnian_yao_index for y in self.res.years]
        self.assertGreater(len(set(idxs)), 1,
                           f"行年爻在段内恒为 {idxs} —— 这是旧实现的错法"
                           "（取大运段爻而非逐年变出之爻）")
        # 且必须走满 6 爻一轮（9 年 → 至少覆盖 6 个不同爻位）
        self.assertEqual(len(set(idxs)), 6,
                         f"行年爻九年应走满 6 爻一轮，实得 {sorted(set(idxs))}")

    def test_flip_actually_produces_original_hexagram(self):
        """逐岁复算 flip，确认卦名与行年爻位由原典描述得出。

        原典一岁「如是阳年则不变」→ **不翻**，行年爻仍为元堂爻（同人九三）。
        """
        cur = list(TONG_REN)
        seg_yt = YUANTANG_9_3
        for age, want_name, want_idx in ORIGINAL_NINE:
            if age == 1:
                flip = None            # 一岁不变（阳年）
            elif age == 2:
                flip = (seg_yt + 3) % 6
            elif age == 3:
                flip = seg_yt
            else:
                flip = (seg_yt + (age - 3)) % 6
            if flip is not None:
                cur = _flip_line(cur, flip)
            u, lo, name = _lines_to_hexagram(cur)
            with self.subTest(age=age):
                self.assertEqual(name, want_name,
                                 f"{age} 岁复算卦名应为 {want_name}，实得 {name}")
                self.assertEqual(flip if flip is not None else seg_yt, want_idx,
                                 f"{age} 岁行年爻位应为 {want_idx}")


class TestLiunianJudgementUsesXingNianYao(unittest.TestCase):
    """端到端：流年判词所取之爻 == 该年行年爻。"""

    def test_guajie_liunian_yao_is_xingnian_yao(self):
        from tongshu.engines.heluo_adapter import HeluoAdapter
        ad = HeluoAdapter()
        res = ad.compute((1983, 11, 3, 12), gender="male",
                         target_date="2026-10-23")
        for e in (res.timeline.yearly_hexagrams or []):
            xy = e.get("xingnian_yao_index")
            if not isinstance(xy, int) or not (0 <= xy < len(e.get("lines") or [])):
                continue
            with self.subTest(year=e["year"]):
                self.assertIsNotNone(
                    e.get("xingnian_yao_index"),
                    "年卦条目须带 xingnian_yao_index")
        # 流年判词的爻
        gj = res.guajie or {}
        ly = gj.get("liunian_yao") or {}
        target = next((e for e in (res.timeline.yearly_hexagrams or [])
                       if e.get("year") == gj.get("liunian_year")), None)
        self.assertIsNotNone(target, "应能定位到流年卦条目")
        xy = target.get("xingnian_yao_index")
        self.assertIsInstance(xy, int, "流年卦条目须带 xingnian_yao_index")
        # ⚠ 2026-10-24 修：原写 `_yao_name(xy, target["lines"])` ——
        #   _yao_name 的第二参是**爻的阴阳值**（1/-1），误传整个 lines 列表
        #   → 恒判「阴」，期望值与实际值只在「恰好也是阴爻」时相等。
        #   本盘 2026 年行年爻恰是阴爻（六五），故旧写法**侥幸通过**；
        #   换成阳爻年份即会红。改为传爻值本身。
        want = _yao_name(xy, target["lines"][xy])
        self.assertEqual(ly.get("yao"), want,
                         f"流年判词所取之爻应为行年爻 {want}，实得 {ly.get('yao')}")


if __name__ == "__main__":
    unittest.main()
