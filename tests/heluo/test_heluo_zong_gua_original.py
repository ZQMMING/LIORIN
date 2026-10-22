# -*- coding: utf-8 -*-
"""综卦（反对）口径守卫 ——《河洛真数·起例卷之下》「六十四卦反对图」（2026-10-22）。

**背景：同一个概念，仓里曾有两套实现，且都生产判词。**

  · ``hexagram.compute_zong_gua(upper, lower)``
      = ``SIXTY_FOUR_HEXAGRAMS[(lower, upper)]`` —— 只把上下卦**对调**，
        三画卦内部没有倒。
  · ``guajie.ZONG_GUA`` —— 64 条手抄表，注释明写「**六爻倒转**」。

两者对 **64 卦中的 48 卦**给出不同结果；自反卦（倒转后仍是自己）个数
分别是 4 与 10。而 ``compute_zong_gua`` 的产物直接进生产输出
（``daily_hexagram.base_hex.zong_name``）。

**原典给了判决。** 起例卷之下 L46-L48 逐字：

    L46: 六十四卦反对图
    L47: 上经正卦六，反卦二十四，共用十八卦，成三十卦。
         下经正卦二，反卦三十二，亦用十八卦，成三十四卦。
    L48: 又尝合上下经始终而论之，乾坤天地也，坎离水火也。以体言也……

「正卦」= **自反卦**。原典要求：上经 6 个、下经 2 个，合计 8 个。

| 口径 | 自反卦 | 上经 | 下经 | 与原典 |
|---|---:|---:|---:|---|
| 上下卦对调（原 compute_zong_gua） | 4 | 4 | 4 | ✗ |
| 手抄表 ZONG_GUA | 10 | 4 | 6 | ✗ |
| **严格六爻倒转** | **8** | **6** | **2** | **✓ 逐位吻合** |

故：综卦 = **六爻整体倒转**（下卦变上卦、上卦变下卦，且三画卦内部亦倒，
震↔艮、巽↔兑；乾坤坎离不变）。2026-10-22 已据此统一两处实现。

本文件把该口径钉死：原典计数、64 卦全表、逐卦倒转、对合性、
以及**原典原文逐字在库**（防日后有人据二手转述改口径）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo import guajie
from tongshu.engines.heluo.hexagram import (
    _lines_to_gua_name,
    compute_zong_gua,
)
from tongshu.engines.heluo.numbers import (
    SIXTY_FOUR_HEXAGRAMS,
    build_six_lines,
    short_hexagram_name,
)

#: 通行本《周易》卦序 · 上经 30 卦（乾…离）
SHANG_JING = [
    "乾", "坤", "屯", "蒙", "需", "讼", "师", "比", "小畜", "履",
    "泰", "否", "同人", "大有", "谦", "豫", "随", "蛊", "临", "观",
    "噬嗑", "贲", "剥", "复", "无妄", "大畜", "颐", "大过", "坎", "离",
]

#: 通行本《周易》卦序 · 下经 34 卦（咸…未济）
XIA_JING = [
    "咸", "恒", "遁", "大壮", "晋", "明夷", "家人", "睽", "蹇", "解",
    "损", "益", "夬", "姤", "萃", "升", "困", "节", "井", "革",
    "鼎", "震", "艮", "渐", "归妹", "丰", "旅", "巽", "兑", "中孚",
    "小过", "既济", "未济", "涣",
]

#: 原典 L47 明文的两组计数
YUAN_DIAN_SHANG_ZHENG = 6      # 上经正卦六
YUAN_DIAN_XIA_ZHENG = 2        # 下经正卦二


class TestZongGuaOriginalCount(unittest.TestCase):
    """原典「六十四卦反对图」的计数规则 —— 综卦口径的判决依据。"""

    def _self_guas(self):
        return [g for g in guajie.ZONG_GUA if guajie.ZONG_GUA[g] == g]

    def test_self_count_matches_original(self):
        """自反卦合计 = 上经正卦六 + 下经正卦二 = 8。"""
        self.assertEqual(len(self._self_guas()),
                         YUAN_DIAN_SHANG_ZHENG + YUAN_DIAN_XIA_ZHENG,
                         "原典「上经正卦六…下经正卦二」⇒ 自反卦合计 8 个")

    def test_shang_jing_count_matches_original(self):
        """上经正卦 6 个。"""
        got = [g for g in SHANG_JING if guajie.ZONG_GUA.get(g) == g]
        self.assertEqual(len(got), YUAN_DIAN_SHANG_ZHENG,
                         f"上经正卦应为 6 个，实得 {got}")

    def test_xia_jing_count_matches_original(self):
        """下经正卦 2 个。"""
        got = [g for g in XIA_JING if guajie.ZONG_GUA.get(g) == g]
        self.assertEqual(len(got), YUAN_DIAN_XIA_ZHENG,
                         f"下经正卦应为 2 个，实得 {got}")

    def test_shang_and_xia_cover_all_64(self):
        """上经 30 + 下经 34 = 64，不得有漏。"""
        self.assertEqual(len(SHANG_JING), 30)
        self.assertEqual(len(XIA_JING), 34)
        self.assertEqual(len(set(SHANG_JING) & set(XIA_JING)), 0,
                         "上经与下经卦名不得重叠")
        self.assertEqual(len(set(SHANG_JING) | set(XIA_JING)), 64)


class TestZongGuaIsSixLineReversal(unittest.TestCase):
    """综卦 = 六爻整体倒转。"""

    def test_every_hexagram_matches_line_reversal(self):
        """逐卦核对：倒转六爻后所得之卦，必须与实现一致。

        期望值由**倒转六爻**独立算出（不调用被测函数），
        与 ``compute_zong_gua`` 对拍。
        """
        mism = []
        for (up, lo), full in SIXTY_FOUR_HEXAGRAMS.items():
            lines = build_six_lines(up, lo)
            want = short_hexagram_name(_lines_to_gua_name(list(reversed(lines))))
            got = short_hexagram_name(compute_zong_gua(up, lo))
            if got != want:
                mism.append((short_hexagram_name(full), got, want))
        self.assertEqual(mism, [], f"综卦不等于六爻倒转：{mism[:5]}")

    def test_trigram_internal_order_is_reversed(self):
        """六爻倒转时，三画卦**内部**也要倒 —— 这是旧实现漏掉的那一步。

        震☳ 倒转成艮☶、艮☶ 倒转成震☳、巽☴ 倒转成兑☱、兑☱ 倒转成巽☴；
        乾坤坎离自身对称，不变。
        """
        from tongshu.engines.heluo.hexagram import _TRIGRAM_REVERSED
        self.assertEqual(_TRIGRAM_REVERSED, {
            "乾": "乾", "坤": "坤", "坎": "坎", "离": "离",
            "震": "艮", "艮": "震", "巽": "兑", "兑": "巽",
        })

    def test_known_pairs(self):
        """几个可人工核对的对子（值是卦名**简称**）。"""
        cases = {
            "泽山咸": "恒",     # 上兑下艮 → 下艮倒为震、上兑倒为巽 = 雷风恒
            "雷山小过": "小过",   # 自反（[a,b,c,c,b,a]）
            "山雷颐": "颐",       # 自反
            "泽风大过": "大过",   # 自反
            "天水讼": "需",
            "地火明夷": "晋",
            "震为雷": "艮",       # 震为雷 → 艮为山
            "巽为风": "兑",       # 巽为风 → 兑为泽
            "乾为天": "乾",
            "坤为地": "坤",
            "坎为水": "坎",
            "离为火": "离",
        }
        for full, want in cases.items():
            short = short_hexagram_name(full)
            got = guajie.ZONG_GUA.get(short)
            self.assertEqual(got, want, f"{full} 综卦")

    def test_trigram_swap_only_is_rejected(self):
        """反证：只把上下卦对调（不算三画卦内部倒置）会被本守卫抓住。

        旧实现正是这样做的 —— 对 64 卦中的 48 卦给出错误结果。
        """
        wrong = 0
        for (up, lo), full in SIXTY_FOUR_HEXAGRAMS.items():
            swap_only = short_hexagram_name(SIXTY_FOUR_HEXAGRAMS.get((lo, up), ""))
            right = guajie.ZONG_GUA.get(short_hexagram_name(full))
            if swap_only != right:
                wrong += 1
        self.assertGreater(wrong, 40,
                           "上下卦对调口径应与六爻倒转在大量卦上不同；"
                           "若已相同，说明两者已被混为一谈")


class TestOriginalTextIsInRepo(unittest.TestCase):
    """原典原文必须**在库**（可回查），不得只凭转述。"""

    def test_fanduan_pianxia_contains_fandui_tu(self):
        raw = (Path(__file__).resolve().parents[2]
               / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之下.txt")
        self.assertTrue(raw.exists(), f"原典文件缺失：{raw}")
        text = raw.read_text(encoding="utf-8")
        for frag in ("六十四卦反对图",
                     "上经正卦六，反卦二十四，共用十八卦，成三十卦",
                     "下经正卦二，反卦三十二，亦用十八卦，成三十四卦"):
            self.assertIn(frag, text, f"原典反对图条文缺失：{frag}")


if __name__ == "__main__":
    unittest.main()
