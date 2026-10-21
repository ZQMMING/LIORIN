# -*- coding: utf-8 -*-
"""元堂定位（HL-DISPUTE-004 冻结诗诀算法）回归测试

覆盖 2026-08-27 修复的三个问题：
1. N=4/5 时"四五无重应有寄"的寄宫（QI_GONG）分支此前完全缺失；
2. 寄宫落点为异极性爻时，元堂名"九/六"错用目标阴阳而非实际落点阴阳；
3. 六十四卦表重复条目导致 len != 64。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tongshu.engines.heluo.numbers import SIXTY_FOUR_HEXAGRAMS
from tongshu.engines.heluo.yuan_tang import find_yuantang


class TestHexagramTableIntegrity(unittest.TestCase):
    """六十四卦表完整性。"""

    def test_exactly_64_entries(self):
        self.assertEqual(len(SIXTY_FOUR_HEXAGRAMS), 64)

    def test_all_upper_lower_combos_present(self):
        gua = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
        for u in gua:
            for l in gua:
                self.assertIn((u, l), SIXTY_FOUR_HEXAGRAMS, f"缺 ({u},{l})")


class TestQiGongBranch(unittest.TestCase):
    """N=4/5 寄宫规则（原典'四五无重应有寄'）。

    权威依据：heluo-lishu/docs/yuan_tang.md §五 寄宫案例 与 §3.4 工程伪码。
    """

    # 天泽履：[-1,1,1,1,1,1]，阳爻候选 = [二三四五上]，N=5
    LV_LINES = [-1, 1, 1, 1, 1, 1]

    def test_zi_normal_flight(self):
        """子时(t=0) → 落第一个阳爻 九二，NORMAL。文档寄宫案例①。"""
        r = find_yuantang(self.LV_LINES, "子", "male", "天泽履")
        self.assertEqual(r.yuantang_index, 1)
        self.assertEqual(r.yao_nature, "阳")
        self.assertEqual(r.trace[0]["action"], "NORMAL")

    def test_si_qi_gong_to_initial_six(self):
        """巳时(t=5) → 单飞超出 path 长度 → 寄入初六，QI_GONG。文档寄宫案例②。"""
        r = find_yuantang(self.LV_LINES, "巳", "male", "天泽履")
        self.assertEqual(r.yuantang_index, 0)
        self.assertEqual(r.yao_nature, "阴")
        self.assertEqual(r.trace[0]["action"], "QI_GONG_ROUNDTRIP")
        self.assertEqual(r.yuantang, "初六")

    def test_n4_dachen_qi_gong(self):
        """泽风大过 [-1,1,1,1,1,-1] 阳爻候选=[一二三四五] N=4：
        子卯正常飞（二/五），辰(t=4)起寄宫。"""
        lines = [-1, 1, 1, 1, 1, -1]
        r_zi = find_yuantang(lines, "子", "male", "泽风大过")
        self.assertEqual((r_zi.yuantang_index, r_zi.trace[0]["action"]), (1, "NORMAL"))
        r_mao = find_yuantang(lines, "卯", "male", "泽风大过")
        self.assertEqual((r_mao.yuantang_index, r_mao.trace[0]["action"]), (4, "NORMAL"))
        r_chen = find_yuantang(lines, "辰", "male", "泽风大过")
        self.assertEqual(r_chen.trace[0]["action"], "QI_GONG_ROUNDTRIP")
        self.assertEqual(r_chen.yao_nature, "阴")
        # 元堂名必须按实际落点(阴)称"六"，不得称"九"
        self.assertTrue(r_chen.yuantang.startswith("初六") or "六" in r_chen.yuantang)


class TestDoubleFlightInvariant(unittest.TestCase):
    """N<=3 重飞两遍语义不变性：修复后结果与旧取模公式一致。

    旧公式：offset = 同极性半天内偏移；idx = candidates[offset % N]
    新公式：path = candidates*2; idx = path[hour_idx % (2N)]
    数学上两者在 N∈{1,2,3} 等价（因 6 % N == 0）。
    """

    def _legacy(self, six_lines, hour_idx, target_line):
        cand = [i for i, l in enumerate(six_lines) if l == target_line]
        offset = hour_idx if hour_idx < 6 else hour_idx - 6
        return cand[offset % len(cand)]

    STRUCTURES = [
        [1, 1, 1, -1, -1, -1],   # 泰：阳3阴3
        [-1, -1, -1, 1, 1, 1],   # 否
        [-1, 1, 1, -1, 1, -1],   # 阳3阴3 变体
        [1, 1, -1, -1, 1, 1],    # 兑上乾下? 泽天夬型 阳4阴2 — 不入本组
        [1, -1, -1, 1, -1, -1],  # 阴4阳2
        [1, -1, 1, -1, 1, -1],   # 既济[-?]交互型
        [-1, 1, -1, 1, -1, 1],   # 未济型
    ]

    HOURS = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

    def test_n_le_3_unchanged(self):
        """逐时辰按'阳时取阳爻/阴时取阴爻'切极性后，与旧公式逐一比对。"""
        for lines in self.STRUCTURES:
            for h_i, h in enumerate(self.HOURS):
                is_yang_hour = h_i < 6
                target_line = 1 if is_yang_hour else -1
                cand = [i for i, l in enumerate(lines) if l == target_line]
                n = len(cand)
                if not (1 <= n <= 3):
                    continue  # 该时辰落在新寄宫规则或纯卦分支，不在不变性范围
                r = find_yuantang(lines, h, "male", "X")
                if r.trace[0]["action"] != "REPEAT":
                    continue
                self.assertEqual(
                    r.yuantang_index,
                    self._legacy(lines, h_i, target_line),
                    f"{lines} {h}时 N={n}",
                )

    def test_golden_jixiaolan_ta_hexagram_unchanged(self):
        """泰卦·午时男 = 六四（纪晓岚金例关键节点）。"""
        tai = [1, 1, 1, -1, -1, -1]
        r = find_yuantang(tai, "午", "male", "地天泰")
        self.assertEqual(r.yuantang, "六四")
        self.assertEqual(r.yuantang_index, 3)
        self.assertEqual(r.trace[0]["action"], "REPEAT")

    def test_pure_gua_pinned_cases(self):
        """纯卦钉死样例：乾子男→初九、坤午女→初六。"""
        qian = [1] * 6
        r = find_yuantang(qian, "子", "male", "乾为天")
        self.assertEqual(r.yuantang, "初九")
        kun = [-1] * 6
        r2 = find_yuantang(kun, "午", "female", "坤为地")
        self.assertEqual(r2.yuantang, "初六")


if __name__ == "__main__":
    unittest.main()
