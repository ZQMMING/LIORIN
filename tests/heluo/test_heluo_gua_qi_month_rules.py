# -*- coding: utf-8 -*-
"""卦气月的**两套规则**守卫（2026-10-22）。

**先说清楚一件事**：仓里有两个都叫「卦气月」的东西，它们**不是同一规则的两个副本**，
而是**两套不同的原典规则**。2026-10-22 的体检报告曾把二者误判为「同一规则
两套来源」，据此建议加「两源必须一致」的断言 —— 那是错的，加了就会逼着人
改坏判词。本文件按**正确的形式**立守卫。

| 规则 | 来源 | 形态 | 用途 |
|---|---|---|---|
| **十二月卦气表** | 原典 L854–L914 逐月原文 | 12 条：月 → (节气, 卦名, 原典自述) | 十二辟卦的**月令卦**（正月泰、二月大壮…）|
| **每卦卦气月** | 每卦卦头「卦气属X月」 | 55 卦：卦 → 月（**多对多**）| 叶/不叶判定的输入之一 |

两者**不冲突**，因为它们的定义域不同。真正的交叉验证点是：
**十二辟卦的「卦头自述卦气月」必须恰等于它作为月令卦的那个月。**
实测 10 个十二辟卦（坤、复的卦头未写卦气月）全部吻合 —— 这才是有牙齿的断言。

另：原典《河洛真数·起例卷之下》L15 起例卷的「节卦候卦」是**第三套**体系
（每卦管 90 日、每爻 15 日），与本文件两者皆不同，不得混用。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo import guajie
from tongshu.engines.heluo.numbers import HEXAGRAM_SHORT_NAMES

#: 十二辟卦的阳/阴数递增序（引擎内已登记，用于守卫「月令阴阳」）
_YANG_BY_COUNT = guajie._YANG_MONTHS_BY_YANG_COUNT   # {阳数: 月}
_YIN_BY_COUNT = guajie._YIN_MONTHS_BY_YIN_COUNT        # {阴数: 月}


class TestTwelveMonthTable(unittest.TestCase):
    """十二月卦气表（十二辟卦月令）本身的完整性。"""

    def test_twelve_entries_covering_all_months(self):
        tbl = guajie.GUA_QI_MONTH_TABLE
        self.assertEqual(len(tbl), 12, "十二月卦气表须恰好 12 条")
        self.assertEqual(set(tbl.keys()), set(range(1, 13)),
                         "月份须 1-12 全覆盖")

    def test_each_entry_is_complete(self):
        for m, (jieqi, gua, self_desc) in guajie.GUA_QI_MONTH_TABLE.items():
            self.assertTrue(jieqi, f"{m} 月缺节气名")
            self.assertTrue(gua, f"{m} 月缺卦名")
            self.assertTrue(self_desc, f"{m} 月缺原典自述")
            self.assertIn(gua, HEXAGRAM_SHORT_NAMES.values(),
                          f"{m} 月的卦名 {gua} 不在 64 卦内")

    def test_gua_names_distinct(self):
        guas = [v[1] for v in guajie.GUA_QI_MONTH_TABLE.values()]
        self.assertEqual(len(set(guas)), 12, "十二个月令卦名须互不相同")

    def test_yang_yin_count_order_strict(self):
        """卦名的阴阳数须与月份严格对应（十一月一阳…四月六阳；五月一阴…十月六阴）。"""
        tbl = guajie.GUA_QI_MONTH_TABLE
        for count, month in _YANG_BY_COUNT.items():
            self.assertEqual(tbl[month][1], _expected_gua(month),
                             f"{month} 月的月令卦与阳数递增序不符")
            self.assertTrue(tbl[month][1] in _YANG_GUAS,
                            f"{month} 月应属阳卦序")
        for count, month in _YIN_BY_COUNT.items():
            self.assertEqual(tbl[month][1], _expected_gua(month),
                             f"{month} 月的月令卦与阴数递增序不符")

    def test_original_text_in_repo(self):
        """原典逐月原文须在库。

        ⚠ 出处更正（2026-10-22）：这 12 条「原典自述」在**《河洛真数·起例卷之中》**
        L10-L30（泰 L10 / 大壮 L12 / 夬 L14 / 乾 L18 / 姤 L20 / 遁 L21 /
        否 L23 / 观 L25 / 剥 L27 / 坤 L28 / 复 L29 / 临 L30），
        **不在**起例卷之下。引擎原注释标的「L854–L914」是取证时另一底本的
        行号，搬进包内后未同步 —— 已一并更正。
        """
        raw = (Path(__file__).resolve().parents[2]
               / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之中.txt")
        text = raw.read_text(encoding="utf-8")
        for frag in ("三阳出于寅，三阳至而大道成",
                     "四阳生于卯，四阳盛壮",
                     "五阳生于辰，其卦为夬",
                     "六阳终于巳，其卦为乾，乃纯阳之月",
                     "一阴始生于午",
                     "二阴生于未，其卦为遁",
                     "三阴生于申，其卦为否",
                     "四阴生于酉，四阴既长，是名观卦",
                     "五阴生于戌，五阴长而阳剥落",
                     "六阴生于亥，六阴盛长，乃纯阴之时",
                     "一阳生于子",
                     "二阳生于丑，其卦为临"):
            self.assertIn(frag, text, f"原典十二月卦气自述缺失：{frag}")


#: 阳卦序列（十一月一阳复 → 四月六阳乾）
_YANG_GUAS = ("复", "临", "泰", "大壮", "夬", "乾")
#: 阴卦序列（五月一阴姤 → 十月六阴坤）
_YIN_GUAS = ("姤", "遁", "否", "观", "剥", "坤")


def _expected_gua(month: int) -> str:
    """按阳/阴数递增序推出该月的月令卦。"""
    if month in _YANG_BY_COUNT.values():
        return _YANG_GUAS[list(_YANG_BY_COUNT.values()).index(month)]
    return _YIN_GUAS[list(_YIN_BY_COUNT.values()).index(month)]


class TestPerGuaQiMonthRule(unittest.TestCase):
    """每卦卦头自述的「卦气属X月」。"""

    @classmethod
    def setUpClass(cls):
        cls.data = guajie.load_guajie_data()
        cls.with_month = {g.name: g.gua_qi_month for g in cls.data.values()
                          if g.gua_qi_month is not None}

    def test_some_guas_have_guaqi_month(self):
        self.assertGreaterEqual(len(self.with_month), 50,
                                "应有 50 卦以上自述卦气月")

    def test_months_in_range(self):
        for name, m in self.with_month.items():
            self.assertIn(m, range(1, 13), f"{name} 的卦气月越界：{m}")

    def test_twelve_bi_gua_agree_with_month_table(self):
        """★ 跨规则不变量：十二辟卦的卦头自述卦气月 == 其月令月。

        这是两套规则之间**唯一**真正的交叉点，也是最硬的一处牙齿：
        月令表说「某月是某卦之月」，该卦的卦头也说「我属某月」——
        两处独立来源必须互相对上。
        """
        month_of_gua = {v[1]: m for m, v in guajie.GUA_QI_MONTH_TABLE.items()}
        checked = 0
        for gua, m in month_of_gua.items():
            self_desc = self.with_month.get(gua)
            if self_desc is None:
                continue  # 坤/复 的卦头未写卦气月 → 留档，见 test_missing_ones_are_known
            self.assertEqual(self_desc, m,
                             f"{gua} 的卦头自述卦气月 {self_desc} "
                             f"与其月令月 {m} 不符")
            checked += 1
        self.assertGreaterEqual(checked, 10,
                                "至少应有 10 个十二辟卦可交叉验证")

    def test_missing_ones_are_known(self):
        """64 卦**全部**自述卦气月 —— 无一缺失。

        ⚠ 2026-10-24 第三轮审计修（此前断言 `missing == {"坤", "复"}`）：
          那条断言把**解析器的缺陷固化成了「已知状态」** ——
          坤卦卦头原文写的是「**卦气在十月**」（原典·易卦释义·上经卷之上 L91），
          复卦写的是「坤宫一世卦**属十一月**」；
          两者的月名都**明写**，只是解析器的正则不认「在」、
          且月名字符集缺「一」⇒「十一」永远匹配不上。
          现解析器已覆盖三种句式（卦气属/卦气在/宫…属/八纯卦…属），
          64 卦全部解析出卦气月。
          故本断言改为「**一个都不能少**」—— 若将来某卦真的缺，
          应先查原典原文，再改本断言（不是反过来把缺陷写成期望）。
        """
        month_of_gua = {v[1]: m for m, v in guajie.GUA_QI_MONTH_TABLE.items()}
        missing = {g for g in month_of_gua
                   if g not in self.with_month}
        self.assertEqual(missing, set(),
                         f"以下卦未解析出卦气月：{sorted(missing)}；"
                         "若原典确实未写，须先核原文再改本断言")

    def test_all_64_guas_have_guaqi_month(self):
        """全部 64 卦都应自述卦气月（与上条同源的更强断言）。"""
        all_missing = {g.name for g in self.data.values()
                       if g.gua_qi_month is None}
        self.assertEqual(all_missing, set(),
                         f"未解析出卦气月的卦：{sorted(all_missing)}")

    def test_rule_is_many_to_many_not_month_to_unique(self):
        """每卦卦气月是**多对多**（同月多卦），与月令表（月→唯一卦）形状不同。

        这条断言是为了**防误用**：不得把月令表当成「卦→月」的映射，
        也不得用它去校验每卦卦气月。
        """
        by_month = {}
        for gua, m in self.with_month.items():
            by_month.setdefault(m, []).append(gua)
        self.assertGreater(len(by_month[1]), 1,
                           "1 月应有多卦（多对多），若只剩一个说明规则被混用了")
        self.assertGreater(len(by_month[7]), 1, "7 月应有多卦")


if __name__ == "__main__":
    unittest.main()
