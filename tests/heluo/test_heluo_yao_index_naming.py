# -*- coding: utf-8 -*-
"""爻位字段命名守卫（2026-10-24）。

**为什么要有这个守卫**
------------------

河洛的「爻位」有三个**语义完全不同**的量，此前共用一个名字
`yuantang_index`：

| 概念 | 含义 | 变化规律 | 现名 |
|---|---|---|---|
| 本命元堂 | 出生时先天卦的元堂爻 | **全程唯一** | `YuanTang.yuantang_index` |
| 大运段元堂 | 本岁所属大运段的元堂爻 | **每段变一次，段内 9 年恒定** | `dayun_seg_yuantang_index` |
| 行年爻 | 该年小象游变变出的那一爻 | **逐年挨次变** | `xingnian_yao_index` |

同名异义直接导致过三次**静默错判**（指标全绿、测试全过、功能实际是死的）：

1. **流年断爻取错**（§14.33）：取「年卦的元堂爻」= 大运段爻 ⇒
   同一大运段内 9 年流年判词**完全相同**（实测 2024/2025/2026 皆取「上九」），
   而原典要求行年爻逐年挨次变。
2. **流月起卦基准取错**（§14.34）：起月卦基准误用大运段元堂爻 ⇒
   同一大运段内 9 年的流月序列完全相同。
3. **死断「流年连三年不吉」取错**（本轮）：死断判的正是**流年判词**，
   却取了大运段爻位 ⇒ 三年取同一爻位。

本守卫把「三个概念必须各有专属名字」钉成回归断言，
并断言**流年判词 / 死断流年判词 / 流月基准**三处口径**完全一致**
（都是行年爻），杜绝同类错再次以「同名异义」的形式复发。

**覆盖**
--------
* `LiuNianYear` 字段名：`dayun_seg_yuantang_index` / `xingnian_yao_index`，
  且**不得**再有裸 `yuantang_index`；
* 流年卦条目（`timeline.yearly_hexagrams[]`）键名同理；
* 三处取爻口径一致（流年判词 / 死断流年判词 / 流月基准 == 行年爻）；
* 大运段元堂爻在段内**恒定**、行年爻在段内**逐年变**（两者必须可区分，
  否则改名只是换了个说法，实际仍取同一个值）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tongshu.engines.heluo.timeline_yun import compute_liunian  # noqa: E402
from tongshu.engines.heluo.guajie import (  # noqa: E402
    _pick_liunian_yao_index, _yao_name,
)

#: 同人卦（天火同人）：上乾下离，自下而上 = 离(1,-1,1) + 乾(1,1,1)
TONG_REN = [1, -1, 1, 1, 1, 1]
#: 原典「同人九三爻是元堂」→ 元堂 index 2
YUANTANG_9_3 = 2


def _res():
    """1983-11-03 午时男（1983-11-03 12:00）→ 流年近 3 年。"""
    from tongshu.engines.heluo_adapter import HeluoAdapter
    ad = HeluoAdapter()
    return ad.compute((1983, 11, 3, 12), gender="male",
                       target_date="2026-10-23")


class TestFieldNaming(unittest.TestCase):
    """三个爻位概念必须各有专属名字。"""

    def test_liunian_year_has_no_bare_yuantang_index(self):
        """LiuNianYear 不得再有裸 `yuantang_index` 字段。"""
        from tongshu.engines.heluo.timeline_yun import LiuNianYear
        import dataclasses
        names = {f.name for f in dataclasses.fields(LiuNianYear)}
        self.assertNotIn(
            "yuantang_index", names,
            "LiuNianYear 仍带裸 yuantang_index —— 与本命元堂同名异义，"
            "是「该取行年爻却取大运段爻」的复发源")
        self.assertIn("dayun_seg_yuantang_index", names)
        self.assertIn("xingnian_yao_index", names)

    def test_yearly_entry_keys_are_unambiguous(self):
        """流年卦条目的键不得再用裸 `yuantang_index` / `yuantang_nature`。"""
        res = _res()
        entries = res.timeline.yearly_hexagrams or []
        self.assertTrue(entries, "流年条目为空，无法校验键名")
        for e in entries:
            with self.subTest(year=e.get("year")):
                self.assertNotIn("yuantang_index", e,
                                 "流年条目仍带裸 yuantang_index")
                self.assertNotIn("yuantang_nature", e,
                                 "流年条目仍带裸 yuantang_nature")
                self.assertIn("dayun_seg_yuantang_index", e)
                self.assertIn("dayun_seg_yuantang_nature", e)
                self.assertIn("xingnian_yao_index", e)

    def test_target_year_entry_keys_are_unambiguous(self):
        """target_year_hexagram 摘要的键名同样须语义明确。"""
        res = _res()
        t = res.timeline.target_year_hexagram or {}
        self.assertNotIn("yuantang_index", t)
        self.assertNotIn("yuantang_nature", t)
        self.assertIn("dayun_seg_yuantang_index", t)
        self.assertIn("xingnian_yao_index", t)

    def test_natal_yuantang_keeps_its_own_name(self):
        """本命元堂**保持** `yuantang_index`（唯一语义，无歧义，不动）。"""
        res = _res()
        self.assertIsInstance(res.yuantang.yuantang_index, int)
        self.assertTrue(0 <= res.yuantang.yuantang_index <= 5)


class TestTwoSegmentAndXingnianAreDistinguishable(unittest.TestCase):
    """改名不是换说法：大运段元堂与行年爻必须**取值可区分**。"""

    def test_segment_yuantang_constant_within_segment(self):
        """大运段元堂爻在同一段内恒定（这正是它不能当行年爻用的原因）。"""
        res = compute_liunian(
            prenatal_lines=TONG_REN, prenatal_yuantang=YUANTANG_9_3,
            postnatal_lines=TONG_REN, postnatal_yuantang=YUANTANG_9_3,
            birth_year=2024, age_from=1, age_to=9,
        )
        segs = [y.dayun_seg_yuantang_index for y in res.years]
        self.assertEqual(len(set(segs)), 1,
                         f"同一大运段内段元堂爻应恒定，实得 {segs}")
        xys = [y.xingnian_yao_index for y in res.years]
        self.assertGreater(len(set(xys)), 1,
                           f"行年爻在段内恒为 {xys} —— 那就是段元堂爻，"
                           "两者取值必须可区分")

    def test_end_to_end_two_yao_indices_differ(self):
        """实跑：流年近 3 年的行年爻与段元堂爻**逐年不同**。"""
        res = _res()
        entries = res.timeline.yearly_hexagrams or []
        diff = 0
        for e in entries:
            xy = e.get("xingnian_yao_index")
            seg = e.get("dayun_seg_yuantang_index")
            if isinstance(xy, int) and isinstance(seg, int) and xy != seg:
                diff += 1
        self.assertGreater(diff, 0,
                           "行年爻与段元堂爻处处相同 —— 改名未带来实际分流")


class TestAllThreeTakeXingnianYao(unittest.TestCase):
    """流年判词 / 死断流年判词 / 流月基准 —— 三处口径必须一致（都是行年爻）。"""

    def test_liunian_judgement_yao_is_xingnian_yao(self):
        """流年判词所取之爻 == 该年行年爻。"""
        res = _res()
        gj = res.guajie or {}
        ly = gj.get("liunian_yao") or {}
        target = next((e for e in (res.timeline.yearly_hexagrams or [])
                       if e.get("year") == gj.get("liunian_year")), None)
        self.assertIsNotNone(target, "应能定位到流年卦条目")
        xy = target.get("xingnian_yao_index")
        self.assertIsInstance(xy, int)
        want = _yao_name(xy, target["lines"][xy])
        self.assertEqual(ly.get("yao"), want,
                         f"流年判词所取之爻应为行年爻 {want}，实得 {ly.get('yao')}")

    def test_pick_helper_prefers_xingnian_yao(self):
        """`_pick_liunian_yao_index` 首选行年爻。"""
        res = _res()
        entries = res.timeline.yearly_hexagrams or []
        for e in entries:
            xy = e.get("xingnian_yao_index")
            if not isinstance(xy, int):
                continue
            with self.subTest(year=e.get("year")):
                self.assertEqual(_pick_liunian_yao_index(e, entries), xy,
                                 "取爻helper未首选行年爻")

    def test_pick_helper_falls_back_to_segment_yuantang(self):
        """行年爻缺失时回退大运段元堂爻（可审计的三级回退仍在）。"""
        e = {"year": 2026, "lines": [1, 1, -1, 1, -1, 1],
             "xingnian_yao_index": -1, "dayun_seg_yuantang_index": 4}
        self.assertEqual(_pick_liunian_yao_index(e, [e]), 4)

    def test_pick_helper_falls_back_to_year_over_year_diff(self):
        """三级回退：与上一年流年卦的唯一差异爻。"""
        prev = {"year": 2025, "lines": [1, 1, -1, 1, -1, 1]}
        cur = {"year": 2026, "lines": [1, 1, -1, 1, -1, -1]}
        e = {"year": 2026, "lines": cur["lines"],
             "xingnian_yao_index": -1, "dayun_seg_yuantang_index": -1}
        self.assertEqual(_pick_liunian_yao_index(e, [prev, cur]), 5)

    def test_pick_helper_returns_none_when_nothing_available(self):
        """三者皆不可得时返回 None（不得静默代换一个爻）。"""
        e = {"year": 2026, "lines": [1, 1, -1, 1, -1, 1]}
        self.assertIsNone(_pick_liunian_yao_index(e, [e]))

    def test_siduan_recent_years_yao_is_xingnian_yao(self):
        """死断「近3年流年判词」所取之爻 == 各该年行年爻。

        原典依据（起例卷之上 L369，三源逐字一致）：
        「大象虽佳，（即所得阳爻九年，阴爻六年是也。）
          **不若流年佳。（即小象行年爻也。）**
          流年若佳，未有不应之者。若流年多凶，大象身爻虽佳，亦奚以为。」
        → 原典**自注**「流年」即「小象行年爻」⇒ 流年层面取爻唯一确定。

        死断原句（起例卷之下 L1555）：
        「若流年连三年不吉，卦爻又不吉，本身卦不佳，重反支干元气，便可以死断之。」
        → 「流年连三年不吉」判的是**流年判词**，取爻即取行年爻。

        做法：拦截 `judge_si_duan`，捕获它实际收到的 `recent_years`，
        再逐年比对「实际取的爻」与「该年行年爻」——**不重新实现一遍**取爻逻辑。
        """
        from tongshu.engines.heluo import guajie as gj_mod
        res = _res()
        entries = res.timeline.yearly_hexagrams or []
        # 1983-11-03 午时男：癸亥 壬戌 乙未 壬午
        bazi = [("癸", "亥"), ("壬", "戌"), ("乙", "未"), ("壬", "午")]

        captured: dict = {}
        orig = gj_mod.judge_si_duan

        def _spy(**kw):
            captured["recent"] = kw.get("recent_years")
            return orig(**kw)

        gj_mod.judge_si_duan = _spy
        try:
            gj_mod._collect_si_duan(
                result=res,
                prenatal="风山渐",
                postnatal="火风鼎",
                bazi=bazi,
                target_year=2026,
                shu_xiong=False,
                year_ganzhi="丙午",
            )
        finally:
            gj_mod.judge_si_duan = orig

        recent = captured.get("recent")
        self.assertIsInstance(recent, list, "未能拦截到死断的 recent_years")
        self.assertTrue(recent, "死断未收到近3年流年判词")
        for r in recent:
            e = next((x for x in entries if x.get("year") == r.get("year")), None)
            if e is None:
                continue
            xy = e.get("xingnian_yao_index")
            if not isinstance(xy, int):
                continue
            want = _yao_name(xy, e["lines"][xy])
            with self.subTest(year=r.get("year")):
                self.assertEqual(
                    r.get("yao"), want,
                    f"{r.get('year')} 死断流年判词所取之爻应为行年爻 {want}，"
                    f"实得 {r.get('yao')}")

    def test_xingnian_yao_matches_year_over_year_unique_diff(self):
        """行年爻 == 与上一年流年卦的**唯一差异爻**（几何法独立互证）。

        原典 L366 机制：一年变一卦、一年变一爻 ⇒ 本年卦与上年卦恰好差一爻，
        该差异爻即行年爻。此断言走**完全独立**的路径（几何差分），
        与引擎落字段互证，不靠引擎自证。
        """
        res = _res()
        entries = res.timeline.yearly_hexagrams or []
        checked = 0
        for i in range(1, len(entries)):
            cur = entries[i]
            prev = entries[i - 1]
            cl = cur.get("lines") or []
            pl = prev.get("lines") or []
            diffs = [k for k in range(6)
                     if len(cl) > k and len(pl) > k and cl[k] != pl[k]]
            xy = cur.get("xingnian_yao_index")
            with self.subTest(year=cur.get("year")):
                self.assertEqual(len(diffs), 1,
                                 "本年卦与上年卦应恰好差一爻（一年变一卦一爻）")
                self.assertEqual(diffs[0], xy,
                                 "行年爻与几何差分法不一致")
            checked += 1
        self.assertGreater(checked, 0, "样本不足，无法互证")


class TestOriginalTextBasis(unittest.TestCase):
    """原典依据必须**逐字**在底本中（防止依据被改写/讹传）。"""

    #: 原典起例卷之上 L369（三源逐字一致）——「流年」的原典自注
    ORIGINAL_L369 = ("大象虽佳，（即所得阳爻九年，阴爻六年是也。）"
                     "不若流年佳。（即小象行年爻也。）"
                     "流年若佳，未有不应之者。若流年多凶，大象身爻虽佳，亦奚以为。")

    #: 原典起例卷之下 L1555 —— 死断四条件
    ORIGINAL_L1555 = ("若行后天，连三爻不吉，必多坎壈。若过了第四爻，遇凶，十死八九。"
                      "若流年连三年不吉，卦爻又不吉，本身卦不佳，重反支干元气，"
                      "便可以死断之。")

    def _slice(self) -> str:
        p = ROOT / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之上.txt"
        return p.read_text(encoding="utf-8")

    def test_liu_nian_is_defined_as_xingnian_yao_in_original(self):
        """原典必须逐字含「流年佳。（即小象行年爻也。）」这一自注。

        这是「流年层面取爻 = 行年爻」的**唯一**原典依据，
        必须逐字在底本里，不容改写或讹传。
        """
        text = self._slice()
        self.assertIn(
            self.ORIGINAL_L369, text,
            "包内原典切片未逐字含 L369「流年佳。（即小象行年爻也。）」自注 —— "
            "取爻口径的依据已变动，须重新核实")

    def test_si_duan_clause_quoted_verbatim(self):
        """死断原句必须逐字在底本中（判词层的引文保真）。"""
        p = ROOT / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之下.txt"
        text = p.read_text(encoding="utf-8")
        self.assertIn(
            self.ORIGINAL_L1555, text,
            "包内原典切片未逐字含 L1555 死断四条件原句")

    def test_engine_source_cites_l369_basis(self):
        """引擎死断取爻处必须引用 L369 自注（不得只引 L1555 的一半）。

        只引「若流年连三年不吉」只能推出「主语是流年」，
        推不出「取哪一爻」；取爻的唯一依据是 L369 的「即小象行年爻也」。
        """
        p = (ROOT / "src" / "tongshu" / "engines" / "heluo" / "guajie.py")
        text = p.read_text(encoding="utf-8")
        self.assertIn(
            "即小象行年爻也", text,
            "guajie.py 死断取爻处未引用原典 L369 自注"
            "「流年佳。（即小象行年爻也。）」—— 取爻依据缺失")


class TestNoBareYuantangIndexInFlowYearLayer(unittest.TestCase):
    """流年层源码里不得再出现裸 `yuantang_index` 取/赋值。"""

    def test_source_scan(self):
        """静态扫描：河洛包流年层不得出现裸 `yuantang_index`。"""
        import re
        pkg = ROOT / "src" / "tongshu" / "engines" / "heluo"
        # 流年层相关文件（流年/流月/流日/大运推演与流年判词）
        targets = [
            "timeline_yun.py",   # LiuNianYear 字段
            "guajie.py",         # 流年断爻 / 死断流年判词
        ]
        # canonical.py 不在扫描范围（内含本命元堂调用 YuanTang.yuantang_index）。
        pat = re.compile(r"(?<![\w.])yuantang_index")
        for name in targets:
            text = (pkg / name).read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                # 注释行允许提及（用于解释改名来由）
                if stripped.startswith("#"):
                    continue
                self.assertIsNone(
                    pat.search(line),
                    f"{name}:{lineno} 出现裸 yuantang_index —— "
                    f"流年层须用 dayun_seg_yuantang_index / xingnian_yao_index：{stripped}")


if __name__ == "__main__":
    unittest.main()
