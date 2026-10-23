# -*- coding: utf-8 -*-
"""天地二数**取数口径**守卫：引擎数表 ⟷ 原典 L41-L51 逐字 ⟷ 第三方解读（2026-10-22）。

## 这条口径是什么

《河洛真数·起例卷之上》给了三样东西：

**L41-L44　天干的河图天地之数（逐字，含「左下/右下」排版标注）**

    壬甲从乾起六偶右下　乙癸向坤求二偶右下
    庚来震上坐三奇左下　辛出巽方游四偶右下
    丙向艮门立八偶右下　己取离为头九奇左下
    戊从坎位数一奇左下　丁在兑家留七奇左下

**L47-L51　地支的河图天地之数（逐字，每支两个数，各带标注）**

    亥子属水天一生水地六成之　天一奇左下　地六偶右下
    寅卯属木天三生木地八成之　天三奇左下　地八偶右下
    巳午属火地二生火天七成之　天七奇左下　地二偶右下
    申酉属金地四生金天九成之　天九奇左下　地四偶右下
    辰戌丑未属土天五生土地十成之　天五奇左下　地十偶右下

**L53　求数法（逐字）**

    凡人生年月日时所得干支，依此法，**下阳天之数为奇左边，下阴地之数为偶右边**……
    年月日时**以天干下河图之数，以地支下洛书之数**，支数为奇属阳……
    看人命四柱内得天地数若干，除还天地正数外，以余数取卦……

**L57　定数合卦例**：一坎 二坤 三震 四巽 中五寄宫 六乾 七兑 八艮 九离

## 规则解读（本守卫锁定的口径）

- 河图十数中，**奇数（1,3,5,7,9）为天位**、**偶数（2,4,6,8,10）为地位**
  —— 故「奇左下 / 偶右下」= 奇数归天数、偶数归地数。
- 天干各配**一个**河图数（L41-L44）；地支各配**两个**（天一地六式，L47-L51）。
- 四柱天地二数 = 把每柱的「干值 + 支的两个值」全部按**数值奇偶**分：
  奇数之和为天数，偶数之和为地数。

引擎 `numbers.py` 的 `STEM_VALUES` / `BRANCH_VALUES` / `compute_tian_di_shu`
正是这一口径。**注意**：引擎的 `BRANCH_VALUES` 存的是两数的**数值升序**
（如巳午存 (2,7)，而原典写的是「地二…天七」），语义等价、存储顺序不同 ——
本守卫按**语义**（每支的天位值/地位值）比对，不绑存储顺序。

## 第三方交叉印证（互联网，2026-10-22）

微博「玄易命运预测」《上篇博文有诗曰：壬甲从乾数…》（并被搜狐
《〈河洛〉的妙用！四柱干支对应的卦名和数字》引述）给出的解读与本守卫完全一致：

    「壬甲从乾数，乙癸向坤求。庚来震上立，辛在巽方游。丙于艮门立，
      己以离为头。戊须坎出处，丁向兑家流」。也即是**天干配八卦**。
      洛书以坎为一，坤为二，震为三，巽为四，中为五，乾为六，兑为七，
      艮为八，离为九。那么依此可推出**十天干配九宫数**即为：
      壬甲为6，乙癸为2，丙为8，丁为7，戊为1，己为9，庚为3，辛为4。
      **地支配数歌**：亥子一六水，寅卯三八真。巳午二七火，申酉四九金。
      辰戌丑未土，五十总生成。
      ……天干、地支皆能换算成数字……**八字干支所得之数，奇数之和为天数，
      偶数之和为地数。**

该文并给出一个算例：八字「庚午、戊戌、己酉、乙亥」→ 奇数之和 35、偶数之和 24。
本守卫把它作为**第五个对拍点**（第三方解读口径的对拍）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.numbers import (
    BRANCH_VALUES,
    LUSHU_TO_TRIGRAM_NAME,
    STEM_VALUES,
    compute_tian_di_shu,
)

#: 原典 L41-L44 逐字：天干 → (河图数, 原典排版标注)
#: 标注「奇左下」= 奇数 → 归天数；「偶右下」= 偶数 → 归地数。
STEM_FROM_ORIGINAL = {
    "壬": (6, "偶右下"), "甲": (6, "偶右下"),
    "乙": (2, "偶右下"), "癸": (2, "偶右下"),
    "庚": (3, "奇左下"),
    "辛": (4, "偶右下"),
    "丙": (8, "偶右下"),
    "己": (9, "奇左下"),
    "戊": (1, "奇左下"),
    "丁": (7, "奇左下"),
}

#: 原典 L47-L51 逐字：地支 → (天位值, 地位值)
BRANCH_FROM_ORIGINAL = {
    "子": (1, 6), "亥": (1, 6),
    "寅": (3, 8), "卯": (3, 8),
    "巳": (7, 2), "午": (7, 2),
    "申": (9, 4), "酉": (9, 4),
    "辰": (5, 10), "戌": (5, 10), "丑": (5, 10), "未": (5, 10),
}


class TestNumberTablesMatchOriginal(unittest.TestCase):
    """引擎数表 ⟷ 原典 L41-L51 逐字。"""

    def test_stem_values_match_original_song(self):
        """天干数 ⟷ 原典「壬甲从乾起六偶右下」等八句。"""
        for gan, (num, mark) in STEM_FROM_ORIGINAL.items():
            with self.subTest(gan=gan):
                self.assertEqual(STEM_VALUES[gan], num,
                                 f"{gan} 的河图之数与原典 L41-L44 不符")
                # 标注即奇偶归属：奇数归天、偶数归地
                self.assertEqual(
                    ("奇左下" if num % 2 == 1 else "偶右下"), mark,
                    f"{gan} 的奇偶归属与原典标注不符")

    def test_branch_values_match_original_song(self):
        """地支两数 ⟷ 原典「亥子属水天一生水地六成之」等五句。"""
        for zhi, (tian_pos, di_pos) in BRANCH_FROM_ORIGINAL.items():
            with self.subTest(zhi=zhi):
                got = BRANCH_VALUES[zhi]
                self.assertEqual(set(got), {tian_pos, di_pos},
                                 f"{zhi} 的河图天地之数与原典 L47-L51 不符")
                self.assertEqual(len(set(got)), 2, f"{zhi} 的两个数不应相同")

    def test_odd_is_tian_even_is_di(self):
        """河图十数：奇为天位、偶为地位（引擎「全按奇偶分」的根据）。"""
        for zhi, (tian_pos, di_pos) in BRANCH_FROM_ORIGINAL.items():
            with self.subTest(zhi=zhi):
                self.assertEqual(tian_pos % 2, 1, f"{zhi} 的天位值应为奇数")
                self.assertEqual(di_pos % 2, 0, f"{zhi} 的地位值应为偶数")

    def test_luoshu_order_matches_original(self):
        """洛书序 ⟷ 原典 L57「一坎 二坤 三震 四巽 中五寄宫 六乾 七兑 八艮 九离」。"""
        self.assertEqual(
            LUSHU_TO_TRIGRAM_NAME,
            {1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "中",
             6: "乾", 7: "兑", 8: "艮", 9: "离"},
        )


class TestThirdPartyCase(unittest.TestCase):
    """第三方解读（微博「玄易命运预测」/ 搜狐《〈河洛〉的妙用》）给的算例。

    八字「庚午、戊戌、己酉、乙亥」→ 该文自述「奇数之和为35，偶数之和为24」。
    引擎须给出同一结果。
    """

    def test_case_matches_third_party_reading(self):
        r = compute_tian_di_shu(
            [("庚", "午"), ("戊", "戌"), ("己", "酉"), ("乙", "亥")], "male")
        self.assertEqual((r.tian_shu, r.di_shu), (35, 24),
                         "天地二数与第三方解读算例不符")


class TestOriginalTextInRepo(unittest.TestCase):
    """原典原文必须在库（可逐字回查）。"""

    def test_songs_present_verbatim(self):
        raw = (Path(__file__).resolve().parents[2]
               / "src" / "heluo_engine" / "orig" / "河洛真数_起例卷之上.txt")
        text = raw.read_text(encoding="utf-8")
        for frag in (
            "壬甲从乾起六偶右下", "乙癸向坤求二偶右下",
            "庚来震上坐三奇左下", "辛出巽方游四偶右下",
            "丙向艮门立八偶右下", "己取离为头九奇左下",
            "戊从坎位数一奇左下", "丁在兑家留七奇左下",
            "亥子属水天一生水地六成之", "天一奇左下", "地六偶右下",
            "寅卯属木天三生木地八成之", "天三奇左下", "地八偶右下",
            "巳午属火地二生火天七成之", "天七奇左下", "地二偶右下",
            "申酉属金地四生金天九成之", "天九奇左下", "地四偶右下",
            "辰戌丑未属土天五生土地十成之", "天五奇左下", "地十偶右下",
            "下阳天之数为奇左边，下阴地之数为偶右边",
            "年月日时以天干下河图之数，以地支下洛书之数",
            "一坎　二坤　三震　四巽　中五寄宫　六乾　七兑　八艮　九离",
        ):
            self.assertIn(frag, text, f"原典取数法条文缺失：{frag}")


if __name__ == "__main__":
    unittest.main()
