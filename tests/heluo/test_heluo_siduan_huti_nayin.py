"""H8+: 死断诸法 / 互体 / 纳音元气 / 生时化工 / 六位贵贱 测试

原典依据：
- 死断：起例卷之下·后天详说
- 互体：起例卷之上·互体伏体论
- 纳音：起例卷之上（金音人得乾兑/相生为福/水火极忌）
- 生时化工：起例卷之下·节候卦爻（生时值节卦者谓之化工）
- 六位贵贱：起例卷之上（初庶民/二侯牧/三公卿节制/四近侍大臣/五君位/上天枢）
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.guajie import (
    compute_huti, judge_nayin_yuanqi, get_nayin_element,
    judge_si_duan, judge_jiehua_gong, judge_nayin_huti,
    compose_guajie, hexagram_to_lines,
)


class TestComputeHuti(unittest.TestCase):
    """互体：中四爻交互成卦（起例卷之上·互体伏体论）"""

    def test_jian_gua_original_example(self):
        """原典例：渐卦 → 上互离/下互坎/合未济（"九五六四九三互离，六四九三六二互坎"）"""
        # 渐=巽(011)上艮(001)下 → 六爻 0,0,1,0,1,1
        upper, lower = compute_huti([0, 0, 1, 0, 1, 1])
        self.assertEqual(upper, "离")
        self.assertEqual(lower, "坎")

    def test_hexagram_to_lines_roundtrip(self):
        """卦名→六爻序列：渐卦"""
        lines = hexagram_to_lines("渐")
        self.assertEqual(lines, [0, 0, 1, 0, 1, 1])


class TestNayinYuanQi(unittest.TestCase):
    """纳音五行元气（起例卷之上）"""

    def test_nayin_table(self):
        self.assertEqual(get_nayin_element("甲", "子"), "金")   # 海中金
        self.assertEqual(get_nayin_element("甲", "辰"), "火")   # 覆灯火
        self.assertEqual(get_nayin_element("癸", "亥"), "水")   # 大海水

    def test_gold_person_gets_qian_dui(self):
        """原典：金音人得乾兑之卦=元气（甲子海中金）"""
        ev = judge_nayin_yuanqi("甲", "子", "乾")
        self.assertTrue(any("金音人得乾兑" in e for e in ev), ev)

    def test_fire_person_gets_wood(self):
        """原典：火人得木卦→相生为福（丙寅炉中火得巽木）"""
        ev = judge_nayin_yuanqi("丙", "寅", "巽")
        self.assertTrue(any("相生为福" in e for e in ev), ev)

    def test_water_fire_opposition(self):
        """原典：水火卦极忌相反（丙午天河水得离火）"""
        ev = judge_nayin_yuanqi("丙", "午", "离")
        self.assertTrue(any("极忌相反" in e for e in ev), ev)


class TestNayinHuti(unittest.TestCase):
    """互体纳音元气（"互体有兑，亦是纳音元气"）"""

    def test_huti_metal_counts(self):
        # 小过=震上艮下（木土），互体=兑（金）→ 甲子金音得互体金
        ev = judge_nayin_huti("甲", "子", "小过", "小过")
        self.assertTrue(any("互体" in e and "纳音元气" in e for e in ev), ev)


class TestSiDuan(unittest.TestCase):
    """死断诸法（起例卷之下·后天详说）"""

    def test_junyao_death(self):
        """后天行至君爻（五爻）→ 数足必死"""
        w = judge_si_duan(prenatal_name="比", postnatal_name="解", dayun_line_index=4)
        self.assertTrue(any("君爻" in x for x in w), w)

    def test_shangji(self):
        """上极一爻 → 寿必不久"""
        w = judge_si_duan(prenatal_name="比", postnatal_name="解", dayun_line_index=5)
        self.assertTrue(any("上极" in x for x in w), w)

    def test_three_years_bad_plus_chongfan(self):
        """流年连三年不吉+数凶+重反支干元气 → 死断"""
        bad3 = [
            {"year": 2015, "hexagram": "剥", "ci": "剥床以足，蔑贞凶", "buye": "", "suiyun": ""},
            {"year": 2016, "hexagram": "否", "ci": "倾否，先否后喜。凶", "buye": "", "suiyun": ""},
            {"year": 2017, "hexagram": "困", "ci": "困于酒食，朱绂方来。凶", "buye": "", "suiyun": ""},
        ]
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          tian_yuan_fan="坤", di_yuan_fan="震",
                          shu_xiong=True, dayun_line_index=3, recent_years=bad3)
        self.assertTrue(any("死断" in x for x in w), w)

    def test_xiaoxiang_fandui(self):
        """小象大象反对+爻凶 → 定死无疑（泰↔否综卦）"""
        w = judge_si_duan(prenatal_name="泰", postnatal_name="大畜",
                          recent_years=[{"year": 2020, "hexagram": "否",
                                         "ci": "否之匪人，不利君子贞。凶", "buye": "", "suiyun": ""}])
        self.assertTrue(any("定死" in x for x in w), w)

    def test_kanli(self):
        """连三爻不吉 → 多坎壈"""
        bad3 = [{"year": 2015, "hexagram": "剥", "ci": "凶", "buye": "", "suiyun": ""}] * 3
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=2, recent_years=bad3)
        self.assertTrue(any("坎壈" in x for x in w), w)

    def test_normal_no_trigger(self):
        """正常流年不触发死断"""
        good = [{"year": 2020, "hexagram": "井", "ci": "井渫不食，为我心恻",
                 "buye": "", "suiyun": "岁运逢之，得贵人助"}]
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=1, recent_years=good)
        self.assertEqual(w, [])


class TestJiehuaGong(unittest.TestCase):
    """生时值节卦 → 化工（起例卷之下·节候卦爻）"""

    def test_summer_solstice_li(self):
        """1980-06-22（夏至后）→ 离节卦 → 化工"""
        ev = judge_jiehua_gong("1980-06-22")
        self.assertTrue(any("化工" in e for e in ev), ev)
        self.assertTrue(any("离" in e for e in ev), ev)

    def test_autumn_equinox_dui(self):
        """1983-11-03（秋分后）→ 兑节卦 → 化工"""
        ev = judge_jiehua_gong("1983-11-03")
        self.assertTrue(any("兑" in e for e in ev), ev)

    def test_spring_zhen(self):
        """1964-04-18（春分后）→ 震节卦 → 化工"""
        ev = judge_jiehua_gong("1964-04-18")
        self.assertTrue(any("震" in e for e in ev), ev)


class TestLiuWeiGuiJian(unittest.TestCase):
    """六位贵贱（起例卷之上）"""

    def test_san_gong(self):
        r = compose_guajie(prenatal_name="渐", postnatal_name="旅", yuantang_yao="九三",
                           birth_month=3, tian_shu=25, di_shu=30)
        self.assertTrue(any("公卿节制" in e for e in r.evidence))

    def test_jin_shi(self):
        r = compose_guajie(prenatal_name="渐", postnatal_name="旅", yuantang_yao="六四",
                           birth_month=3, tian_shu=25, di_shu=30)
        self.assertTrue(any("近侍大臣" in e for e in r.evidence))

    def test_hou_mu(self):
        r = compose_guajie(prenatal_name="渐", postnatal_name="旅", yuantang_yao="六二",
                           birth_month=3, tian_shu=25, di_shu=30)
        self.assertTrue(any("侯牧" in e for e in r.evidence))


if __name__ == "__main__":
    unittest.main()
