# -*- coding: utf-8 -*-
"""H11 节候卦保真度守卫（2026-10-07）

锁死本轮修复，防止回退到卦气歌体系。

背景（取证见 data/heluo/起例卷之下算法对照表_20261007.md §九）：
  《河洛真数》的节候卦只有起例卷之下 L1489–1492「节候卦爻」一节——四正卦
  （坎震离兑）节卦表，每卦总管九十日、每爻直十五日，外加七十二候表。
  旧 `jiehhou.py` 把 H11 实现成了卦气歌的「卦X爻动→变卦」链，并把它挂在
  「起例卷下·定节候卦说」名下——该节名在原著全库**零命中**，「一索得中男」
  同样零命中。原典节卦表虽已逐条照抄在 `jiegua.py`，却未被任何生产代码引用。

本类锁三件事：
  ① JIEHOU_GUA 必须派生自 jiegua.JIE_GUA_TABLE（单一来源，不得另抄一份分叉）
  ② 24 条逐条对上 L1492 原文，任何卦气歌卦名都不得复现
  ③ 出处串不得再出现原著没有的节名
"""
import io
import unittest
from pathlib import Path

from tongshu.engines.heluo.jiegua import JIE_GUA_TABLE, JIEQI_24
from tongshu.engines.heluo import jiehhou as m

SRC = Path(__file__).resolve().parents[2] / "src" / "tongshu" / "engines" / "heluo" / "jiehhou.py"
SRC_TEXT = SRC.read_text(encoding="utf-8")

#: 旧版卦气歌表的 24 组值。任何一条出现在 H11 输出里即为回退。
_GUAQI_PAIRS = (
    ("山雷颐", "地雷复"), ("水风井", "风山渐"), ("风山渐", "地天泰"),
    ("地天泰", "雷水解"), ("天山遁", "泽天夬"), ("水泽节", "雷天大壮"),
    ("泽天夬", "山泽损"), ("雷天大壮", "火泽睽"), ("火风鼎", "风雷益"),
    ("火山旅", "山天大畜"), ("地火明夷", "水地比"), ("地水师", "天地否"),
    ("水地比", "山地剥"), ("风地观", "泽地萃"), ("山地剥", "火地晋"),
    ("火泽睽", "坎为水"), ("天泽履", "离为火"), ("风火家人", "乾为天"),
    ("雷火丰", "天山遁"), ("泽火革", "泽山咸"), ("火水未济", "山水蒙"),
    ("山水蒙", "天水讼"), ("水山蹇", "水天需"), ("水天需", "坎为水"),
)


class TestSingleSource(unittest.TestCase):
    """JIEHOU_GUA 必须是 jiegua.JIE_GUA_TABLE 的派生，不得另抄一份。"""

    def test_derived_from_jiegua_table(self):
        expected = {e.jq_index: (e.trigram, e.yao_index, e.yao_name)
                    for e in JIE_GUA_TABLE}
        self.assertEqual(m.JIEHOU_GUA, expected)

    def test_imports_the_table_rather_than_relisting(self):
        """源码必须 import 原典表；若改回内联字面量，本守卫立刻红。"""
        self.assertIn("from .jiegua import JIE_GUA_TABLE", SRC_TEXT)
        self.assertNotIn('0:  ("山雷颐"', SRC_TEXT)

    def test_solar_terms_identical_to_jiegua(self):
        """两处节气表同序同值，否则「派生」无从谈起。"""
        self.assertEqual(tuple(m.SOLAR_TERMS), tuple(JIEQI_24))


class TestAgainstOriginalText(unittest.TestCase):
    """24 条逐条对上 L1492 节卦段。"""

    #: 原典 L1492 逐字：「节卦坎初六起冬至，九二小寒，六三大寒，六四立春，
    #: 九五雨水，上六惊蛰。震初九起春分……兑初九起秋分……」
    def test_all_24_match_original(self):
        for i in range(24):
            info = m.get_seasonal_hexagram(i)
            src = JIE_GUA_TABLE[i]
            self.assertEqual(info.jq_name, src.jq_name, i)
            self.assertEqual(info.main_gua, src.trigram, i)
            self.assertEqual(info.moving_line, src.yao_index, i)
            self.assertEqual(info.result_gua, src.yao_name, i)

    def test_four_square_gua_each_cover_six_yao(self):
        """四正卦坎震离兑各管六爻、每爻十五日——原典「每卦总管九十日，
        自下而上，每一爻各直十五日」。"""
        from collections import Counter
        c = Counter(m.JIEHOU_GUA[i][0] for i in range(24))
        self.assertEqual(dict(c), {"坎": 6, "震": 6, "离": 6, "兑": 6})
        self.assertTrue(all(JIE_GUA_TABLE[i].days == 15 for i in range(24)))

    def test_four_origins(self):
        """坎起冬至、震起春分、离起夏至、兑起秋分。"""
        for idx, gua in ((0, "坎"), (6, "震"), (12, "离"), (18, "兑")):
            self.assertEqual(m.JIEHOU_GUA[idx][0], gua, idx)
            self.assertEqual(m.JIEHOU_GUA[idx][1], 0, idx)   # 皆起于初爻

    def test_no_guaqi_names_leak(self):
        """卦气歌的卦名一个都不许出现在 H11 输出里。"""
        for i in range(24):
            info = m.get_seasonal_hexagram(i)
            for bad_main, _ in _GUAQI_PAIRS:
                self.assertNotEqual(info.main_gua, bad_main, f"jq{i}")
                self.assertNotIn(bad_main, info.result_gua, f"jq{i}")

    def test_no_pseudo_guaci_in_result(self):
        """result_gua 必须是原典爻名（初六/九二/六三/六四/九五/上六/初九…）。"""
        allowed = {"初六", "九二", "六三", "六四", "九五", "上六",
                   "初九", "六二", "九三", "九四", "六五", "上九"}
        for i in range(24):
            self.assertIn(m.JIEHOU_GUA[i][2], allowed, i)


class TestProvenance(unittest.TestCase):
    """出处串不得再挂原著没有的节名。

    注：这两个伪节名**允许**出现在源码的说明性文字里（docstring/注释中
    标注「原著零命中、旧版误植」正是本轮修复的取证记录）。故此处判定的
    是「有没有被当作出处引用」，而非「有没有被提到」。
    """

    #: 提到即合法的语境标记行——必须同时含其一
    _CTX_OK = ("零命中", "旧", "误植", "已从", "移除", "同名")

    def _assert_never_cited(self, phrase: str):
        # ① 运行时：任何 evidence 都不得把它当出处
        for i in range(24):
            ev = "\n".join(m.get_seasonal_hexagram(i).evidence)
            self.assertNotIn(phrase, ev, f"jq{i} 的 evidence 把 {phrase} 当作出处")
        # ② 源码：只允许出现在「标注其为伪」的说明性行里
        for ln_no, line in enumerate(SRC_TEXT.splitlines(), 1):
            if phrase in line:
                self.assertTrue(
                    any(k in line for k in self._CTX_OK),
                    f"{SRC.name}:{ln_no} 把 {phrase} 当作出处引用而非标注其为伪：{line.strip()}")

    def test_no_phantom_section_name(self):
        """「定节候卦说」在原著全库零命中，不得再作为出处出现。"""
        self._assert_never_cited("定节候卦说")

    def test_no_phantom_quote(self):
        """「冬至一索得中男」同样零命中。"""
        self._assert_never_cited("一索得中男")

    def test_evidence_cites_real_line(self):
        ev = "\n".join(m.get_seasonal_hexagram(0).evidence)
        self.assertIn("L1492", ev)
        self.assertIn("坎初六起冬至", ev)
        self.assertIn("每一爻各直十五日", ev)

    def test_evidence_marks_which_system(self):
        """evidence 须显式声明这是原典节卦、非卦气歌口径。"""
        ev = "\n".join(m.get_seasonal_hexagram(0).evidence)
        self.assertIn("非卦气歌", ev)


class TestQiQiConstants(unittest.TestCase):
    """卦气说辅助常量：名实相符（对照表 §2.3 已登记此名不副实）。"""

    def test_sixty_gua_is_actually_sixty_and_unique(self):
        self.assertEqual(len(m.SIXTY_GUA), 60)
        self.assertEqual(len(set(m.SIXTY_GUA)), 60, "SIXTY_GUA 有重复卦名")

    def test_sixty_gua_has_no_non_gua_names(self):
        """旧版含非卦名「宜」与繁体「損」，须清干净。"""
        valid = set(JIEQI_24) | {
            "复", "临", "泰", "大壮", "夬", "乾", "姤", "观", "否", "遁", "剥", "坤",
            "颐", "屯", "益", "震", "噬嗑", "随", "无妄", "明夷", "贲", "既济", "家人",
            "丰", "革", "同人", "临", "损", "节", "中孚", "归妹", "睽", "兑", "履",
            "大畜", "需", "小畜", "大壮", "大有", "夬", "姤", "大过", "鼎", "恒",
            "巽", "井", "蛊", "升", "讼", "困", "未济", "解", "涣", "蒙", "师", "遯",
            "咸", "旅", "小过", "渐", "蹇", "艮", "谦", "否", "萃", "晋", "豫",
            "观", "比", "剥",
        }
        for g in m.SIXTY_GUA:
            self.assertIn(g, valid, f"非卦名或未收录：{g}")

    def test_sixty_gua_by_jieqi_covers_all_24(self):
        self.assertEqual(set(m.SIXTY_GUA_BY_JIEQI), set(range(24)))
        flat = [g for qs in m.SIXTY_GUA_BY_JIEQI.values() for g in qs]
        self.assertEqual(flat, m.SIXTY_GUA)

    def test_sizheng_comment_distinguishes_two_systems(self):
        """京房四正卦是乾坤坎离；坎震离兑是**本卷节卦**四卦。两者不可混称。"""
        self.assertEqual(m.SIZHENG_GUA, {"坎", "离", "震", "兑"})
        self.assertIn("乾坤坎离", SRC_TEXT,
                      "未澄清京房四正卦（乾坤坎离）与本卷节卦四卦（坎震离兑）之别")


if __name__ == "__main__":
    unittest.main()