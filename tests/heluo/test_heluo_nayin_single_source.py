# -*- coding: utf-8 -*-
"""60 甲子纳音：**单一来源**守卫 + 原典纳甲歌诀逐组对拍（2026-10-22）。

背景：60 甲子纳音表此前在河洛引擎里存了**两份**（内容完全相同）：
  * ``canping.py`` 的 ``_NAYIN``（卷十《河洛叅评》纳音加数/配数/参评定位）
  * ``guajie.py`` 的 ``_NAYIN``（解卦层纳音元气、互体诸法）
两份各自维护 = 同一规则多套来源；一处改了另一处不动就静默分叉
（同一干支在两条链路上得出不同纳音，判词随之漂移，且**无任何报错**）。
2026-10-22 收敛为 ``nayin.py`` 一份，两处改为 import。

本守卫锁四件事：
  1. 三处引用**必须是同一个对象**（证明已收敛，不是又抄了第三份）
  2. 60 甲子全覆盖，五行取值域受控
  3. **原典《河洛真数·起例卷之下》L137「纳甲歌诀」逐组对拍**（30 组）
  4. ``yuanqi_tables.GANZHI_GUA_GROUPS``（干支组→卦）是**另一张表**，
     不得与纳音表合并（其模块注释已明钉）
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo import canping, guajie, nayin, yuanqi_tables

#: 《河洛真数·起例卷之下》L137「纳甲歌诀」逐组（阳干干支, 阴干干支, 纳音五行）
#: 底本该处「甲辰己巳佛灯火」的「己」为抄刻讹（该组首字必为「甲辰」），
#: 歌诀的配对是「同干同支的阳干 + 阴干」，据此可正。
NAYIN_GE: tuple[tuple[str, str, str], ...] = (
    ("甲子", "乙丑", "金"),   # 海中金
    ("丙寅", "丁卯", "火"),   # 炉中火
    ("戊辰", "己巳", "木"),   # 大林木
    ("庚午", "辛未", "土"),   # 路旁土
    ("壬申", "癸酉", "金"),   # 剑锋金
    ("甲戌", "乙亥", "火"),   # 山头火
    ("丙子", "丁丑", "水"),   # 涧下水
    ("戊寅", "己卯", "土"),   # 城头土
    ("庚辰", "辛巳", "金"),   # 白蜡金
    ("壬午", "癸未", "木"),   # 杨柳木
    ("甲申", "乙酉", "水"),   # 泉中水
    ("丙戌", "丁亥", "土"),   # 屋上土
    ("戊子", "己丑", "火"),   # 霹雳火
    ("庚寅", "辛卯", "木"),   # 松柏木
    ("壬辰", "癸巳", "水"),   # 长流水
    ("甲午", "乙未", "金"),   # 沙中金
    ("丙申", "丁酉", "火"),   # 山下火
    ("戊戌", "己亥", "木"),   # 平地木
    ("庚子", "辛丑", "土"),   # 壁上土
    ("壬寅", "癸卯", "金"),   # 金箔金
    ("甲辰", "乙巳", "火"),   # 佛灯火
    ("丙午", "丁未", "水"),   # 天河水
    ("戊申", "己酉", "土"),   # 大驿土
    ("庚戌", "辛亥", "金"),   # 钗钏金
    ("壬子", "癸丑", "木"),   # 桑柘木
    ("甲寅", "乙卯", "水"),   # 大溪水
    ("丙辰", "丁巳", "土"),   # 沙中土
    ("戊午", "己未", "火"),   # 天上火
    ("庚申", "辛酉", "木"),   # 石榴木
    ("壬戌", "癸亥", "水"),   # 大海水
)

_ELEMENTS = ("金", "木", "水", "火", "土")


class TestNayinSingleSource(unittest.TestCase):
    """三处引用必须是同一份表。"""

    def test_all_three_point_to_one_object(self):
        self.assertIs(canping._NAYIN, nayin.NAYIN_TABLE,
                      "canping._NAYIN 须与 nayin.NAYIN_TABLE 是同一对象")
        self.assertIs(guajie._NAYIN, nayin.NAYIN_TABLE,
                      "guajie._NAYIN 须与 nayin.NAYIN_TABLE 是同一对象")
        self.assertIs(canping._NAYIN, guajie._NAYIN,
                      "canping 与 guajie 的纳音表须是同一对象")

    def test_table_covers_all_60(self):
        self.assertEqual(len(nayin.NAYIN_TABLE), 60,
                         "纳音表须恰好 60 条")
        covered = {g for a, b, _ in NAYIN_GE for g in (a, b)}
        self.assertEqual(covered, set(nayin.NAYIN_TABLE),
                         "歌诀覆盖的 60 干支须与表一致")

    def test_elements_in_domain(self):
        for g, e in nayin.NAYIN_TABLE.items():
            self.assertIn(e, _ELEMENTS, f"{g} 纳音五行越界：{e}")

    def test_three_lookups_agree_on_all_60(self):
        """三处查表接口对全部 60 组必须给出同一答案。"""
        for a, b, _ in NAYIN_GE:
            for g in (a, b):
                self.assertEqual(nayin.get_nayin_element(g),
                                 canping.get_nayin_element(g[0], g[1]),
                                 f"{g}：nayin 与 canping 不一致")
                self.assertEqual(nayin.get_nayin_element(g),
                                 guajie.get_nayin_element(g[0], g[1]),
                                 f"{g}：nayin 与 guajie 不一致")


class TestNayinAgainstOriginalGe(unittest.TestCase):
    """原典《起例卷之下》L137 纳甲歌诀逐组对拍。"""

    def test_every_group_matches_original_song(self):
        """30 组歌诀逐组对拍（阳干干支 + 阴干干支 → 纳音五行）。"""
        for a, b, elem in NAYIN_GE:
            self.assertEqual(nayin.NAYIN_TABLE.get(a), elem,
                             f"{a} 纳音与原典歌诀不符")
            self.assertEqual(nayin.NAYIN_TABLE.get(b), elem,
                             f"{b} 纳音与原典歌诀不符")

    def test_each_element_has_twelve_ganzhi(self):
        """五行各十二干支。"""
        counts = {}
        for g, e in nayin.NAYIN_TABLE.items():
            counts[e] = counts.get(e, 0) + 1
        self.assertEqual(counts, {"金": 12, "木": 12, "水": 12, "火": 12, "土": 12},
                         f"各五行应各十二干支，实得 {counts}")

    def test_original_song_is_in_repo(self):
        """原典歌诀原文必须在库（可回查）。

        注：底本该处作「甲辰**己**巳佛灯火」（抄刻讹），断言用**实际字串**，
        不自行订正 —— 歌诀的配对是「同干同支的阳干 + 阴干」，据此可正。
        """
        raw = (Path(__file__).resolve().parents[2]
               / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之下.txt")
        text = raw.read_text(encoding="utf-8")
        self.assertIn("纳甲歌诀", text, "原典「纳甲歌诀」标题缺失")
        for frag in ("甲子乙丑海中金", "丙寅丁卯炉中火", "戊辰己巳大林木",
                     "庚午辛未路旁土", "壬申癸酉剑锋金", "甲戌乙亥山头火",
                     "丙子丁丑涧下水", "戊寅己卯城头土", "庚辰辛巳白蜡金",
                     "壬午癸未杨柳木", "甲申乙酉泉中水", "丙戌丁亥屋上土",
                     "戊子己丑霹雳火", "庚寅辛卯松柏木", "壬辰癸巳长流水",
                     "甲午乙未沙中金", "丙申丁酉山下火", "戊戌己亥平地木",
                     "庚子辛丑壁上土", "壬寅癸卯金箔金",
                     "甲辰己巳佛灯火",   # 底本讹字（当作「甲辰乙巳」）
                     "丙午丁未天河水", "戊申己酉大驿土", "庚戌辛亥钗钏金",
                     "壬子癸丑桑柘木", "甲寅乙卯大溪水", "丙辰丁巳沙中土",
                     "戊午己未天上火", "庚申辛酉石榴木", "壬戌癸亥大海水"):
            self.assertIn(frag, text, f"原典纳甲歌诀缺失：{frag}")


class TestGanzhiGuaGroupsStaysSeparate(unittest.TestCase):
    """干支组→卦表是**另一张表**，不得与纳音表合并。"""

    def test_two_tables_are_not_the_same_shape(self):
        """``GANZHI_GUA_GROUPS`` 给的是「干支组 → 卦」，纳音表给的是「干支 → 五行」。"""
        groups = yuanqi_tables.GANZHI_GUA_GROUPS
        self.assertTrue(groups, "干支组表不应为空")
        # 两者形状不同：纳音表是 60 条 干支→五行，组表是 干支组→卦
        self.assertNotEqual(set(groups.keys()), set(nayin.NAYIN_TABLE.keys()),
                            "两张表不得合并为一张")
        # 组表的值是**卦名**（非五行）
        for k, v in list(groups.items())[:3]:
            self.assertNotIn(str(v), _ELEMENTS,
                             f"干支组表的值应是卦名而非五行：{k}→{v}")


if __name__ == "__main__":
    unittest.main()
