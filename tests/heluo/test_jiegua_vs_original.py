"""节卦表 / 七十二候表 —— 逐条比对原典 L1492（2026-10-07）

**这是录入正确性的牙齿**：不信任 ``jiegua.py`` 里手工抄进去的表，
而是把原典 L1492 的原文**重新解析一遍**，与表逐条比对。
若任一条卦名、爻位、节气、物候被抄错，此处立刻转红。

同时校验原典自身的三处结构性规则：
  - 「气之八节，总之其卦四」→ 四正卦恰为坎/震/离/兑
  - 「每卦总管九十日，自下而上，每一爻各直十五日」→ 6×15=90
  - 「候有七十二」→ 恰 72 条；「每卦总六日，自初而上爻各一日」→ 每候 6 条
"""
from __future__ import annotations

import io
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.jiegua import (
    HOU_72_TABLE,
    JIE_GUA_DAYS_PER_TRIGRAM,
    JIE_GUA_DAYS_PER_YAO,
    JIE_GUA_TABLE,
    JIEQI_24,
    get_hou_by_jq,
)

_ROOT = Path(__file__).resolve().parents[2]

# 原典全文路径（与起例卷 guajie_raw 同源转录）
_ORIGINAL = Path(os.environ.get(
    "HELUO_ORIGINAL_TXT",
    r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
    r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6_07333092-河洛真数——原著.txt",
))


def _original_line_1492() -> str:
    """取原典 L1492（节候卦爻节）全文。"""
    if not _ORIGINAL.exists():
        raise unittest.SkipTest(f"原著全文不在预期路径：{_ORIGINAL}")
    with io.open(_ORIGINAL, encoding="utf-8") as f:
        lines = f.read().split("\n")
    for ln in lines:
        if "气之八节" in ln and "候有七十二" in ln:
            return ln
    raise AssertionError("原著中未找到「气之八节…候有七十二」段")


_ORIG = _original_line_1492()


class TestJieGuaTableVsOriginal(unittest.TestCase):
    """节卦表 24 条逐条比对原典。"""

    def _parse_original_jie_gua(self):
        """把原典「节卦」段解析成 {卦: [(爻名, 节气), …]}。

        原文形如「坎初六起冬至，九二小寒，六三大寒，六四立春，九五雨水，
        上六惊蛰。震初九起春分……」。故按四正卦名切段，再逐条抽「爻名+节气」。
        """
        head = _ORIG[:_ORIG.index("候卦")]
        seg = head[head.index("节卦"):]
        out = {}
        marks = [(trigram, seg.index(trigram + "初"))
                 for trigram in ("坎", "震", "离", "兑")]
        for k, (trigram, pos) in enumerate(marks):
            pos = marks[k][1] + 1   # 跳过卦名本身，从爻名开始
            end = marks[k + 1][1] if k + 1 < len(marks) else len(seg)
            seg_t = seg[pos:end]
            out[trigram] = re.findall(
                # 爻名形如 初六 / 九二 / 六三 / 六四 / 九五 / 上六
                # ——「初/上」在前，「二三四五」在后，故阴阳标记亦在序数之前
                r"([初上][九六]|[九六][二三四五])\s*起?\s*"
                r"(冬至|小寒|大寒|立春|雨水|惊蛰|春分|清明|谷雨|立夏|小满|芒种|"
                r"夏至|小暑|大暑|立秋|处暑|白露|秋分|寒露|霜降|立冬|小雪|大雪)",
                seg_t)
            if len(out[trigram]) != 6:
                self.fail(f"{trigram}段只解析出 {len(out[trigram])} 条，应为 6：{seg_t!r}")
        return out

    def test_all_24_entries_match_original(self):
        orig = self._parse_original_jie_gua()
        got = {}
        for e in JIE_GUA_TABLE:
            got.setdefault(e.trigram, []).append((e.yao_name, e.jq_name))
        self.assertEqual(got, orig,
                         f"节卦表与原典不符：\n原典={orig}\n实现={got}")

    def test_table_covers_24_terms(self):
        self.assertEqual(len(JIE_GUA_TABLE), 24)
        self.assertEqual([e.jq_name for e in JIE_GUA_TABLE], list(JIEQI_24),
                         "节卦表须按冬至→大雪排列且无缺漏")

    def test_four_trigrams_are_the_four_moons(self):
        """原典「气之八节，总之其卦四」→ 坎/震/离/兑，四卦各辖六爻。"""
        tris = [e.trigram for e in JIE_GUA_TABLE]
        self.assertEqual(sorted(set(tris)), sorted(["坎", "震", "离", "兑"]),
                         "节卦只取坎震离兑四正卦")
        for t in ("坎", "震", "离", "兑"):
            self.assertEqual(tris.count(t), 6, f"{t}卦须辖六爻")

    def test_days_rule(self):
        """原典「每卦总管九十日…每一爻各直十五日」"""
        self.assertEqual(JIE_GUA_DAYS_PER_YAO * 6, JIE_GUA_DAYS_PER_TRIGRAM)
        self.assertEqual(JIE_GUA_DAYS_PER_TRIGRAM, 90)
        for e in JIE_GUA_TABLE:
            self.assertEqual(e.days, 15)

    def test_yao_index_ascends_within_trigram(self):
        """原典「自下而上」——每卦六爻须按初→上排列。"""
        for t in ("坎", "震", "离", "兑"):
            idx = [e.yao_index for e in JIE_GUA_TABLE if e.trigram == t]
            self.assertEqual(idx, [0, 1, 2, 3, 4, 5], f"{t}卦爻序非自下而上")


class TestHouTableVsOriginal(unittest.TestCase):
    """七十二候表逐条比对原典。"""

    def _original_hou_text(self) -> str:
        i = _ORIG.index("候卦")
        seg = _ORIG[i + 3:]
        return seg[:seg.index("其下接颐")]

    def test_count_is_72(self):
        """原典「候有七十二」"""
        self.assertEqual(len(HOU_72_TABLE), 72)

    def test_every_wuhou_appears_in_original(self):
        """72 个物候名逐个须在原典该段出现——防抄错防杜撰。"""
        seg = self._original_hou_text()
        missing = [h.wuhou for h in HOU_72_TABLE if h.wuhou not in seg]
        self.assertEqual(missing, [], f"原典段中查无此物候：{missing}")

    def test_every_gua_appears_before_its_wuhou(self):
        """每条的卦名须紧邻其物候名之前出现。

        **原典两处省文（实测登记，不臆补）**：
          - 首条作「四爻起冬至蚯蚓结」，省去卦名「颐」——
            承接上节「其下接颐」，即仍属颐卦；
          - 井卦两条原文省「爻」字（作「井三鹫鸟厉疾」「井四爻起夏至」），
            本表统一按「三爻」「四爻」登记，卦位不变。
        故窗口放宽到 18 字，并允许首条卦名来自上段承接。
        """
        seg = self._original_hou_text()
        bad = []
        for h in HOU_72_TABLE:
            pos_w = seg.find(h.wuhou)
            if pos_w < 0:
                bad.append((h.gua, h.wuhou, "物候名不存在"))
                continue
            window = seg[max(0, pos_w - 18):pos_w]
            if h.gua not in window:
                bad.append((h.gua, h.wuhou, f"卦名不在邻近窗口：{window!r}"))
        # 首条「颐」在原典属上段承接，其卦名为已知登记项，单列放行
        self.assertEqual([b for b in bad if b[1] != "蚯蚓结"], [],
                         f"卦名与物候名对不上：{bad}")

    def test_every_jq_term_appears(self):
        """每条候的节气归属须与原典一致。

        原典把某节气名写在**该节气首候**前（如「噬嗑四爻起小雪虹藏不见」，
        其后大过、坤二两候同属小雪），故不能只按邻近窗口判——
        须**先按 24 节气把原文切成 24 段**，再断言每候物候名落在其所属段内。
        """
        seg = self._original_hou_text()
        jq_list = ["冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
                   "春分", "清明", "谷雨", "立夏", "小满", "芒种",
                   "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
                   "秋分", "寒露", "霜降", "立冬", "小雪", "大雪"]
        # 按首次出现位置切段（顺次，非全局首个）
        cuts = []
        cursor = 0
        for j in jq_list:
            pos = seg.index(j, cursor)
            cuts.append((j, pos))
            cursor = pos + len(j)
        seg_of = {}
        for k, (j, pos) in enumerate(cuts):
            end = cuts[k + 1][1] if k + 1 < len(cuts) else len(seg)
            seg_of[j] = seg[pos + len(j):end]

        bad = []
        for h in HOU_72_TABLE:
            if h.wuhou not in seg_of[h.jq_name]:
                bad.append((h.index, h.gua, h.wuhou, h.jq_name,
                            seg_of[h.jq_name][:40]))
        self.assertEqual(bad, [], f"候的节气归属与原典不符：{bad[:5]}")

    def test_three_hou_per_jq(self):
        """七十二候 = 二十四节气 × 三候。"""
        counts = {}
        for h in HOU_72_TABLE:
            counts[h.jq_name] = counts.get(h.jq_name, 0) + 1
        self.assertEqual(set(counts.values()), {3},
                         f"每节气应恰三候，实得：{counts}")
        self.assertEqual(len(counts), 24)

    def test_jq_order_is_solar_term_order(self):
        """全年顺序须严格按冬至→大雪推进（各节气连续三候）。"""
        expected = [j for j in JIEQI_24 for _ in range(3)]
        self.assertEqual([h.jq_name for h in HOU_72_TABLE], expected,
                         "七十二候须按节气顺序、每节气三候连续排列")

    def test_index_is_sequential(self):
        self.assertEqual([h.index for h in HOU_72_TABLE], list(range(72)))

    def test_lookup_by_jq(self):
        winter = get_hou_by_jq("冬至")
        self.assertEqual(len(winter), 3)
        self.assertEqual([h.wuhou for h in winter], ["蚯蚓结", "麋角解", "水泉动"],
                         "原典：颐四爻起冬至蚯蚓结，中孚三爻麋角解，复二爻水泉动")

    def test_first_and_last_match_original(self):
        """首尾两条须与原典首尾逐字相符。"""
        self.assertEqual(
            (HOU_72_TABLE[0].gua, HOU_72_TABLE[0].yao_index,
             HOU_72_TABLE[0].jq_name, HOU_72_TABLE[0].wuhou),
            ("颐", 3, "冬至", "蚯蚓结"),
            "原典首条：颐四爻起冬至蚯蚓结")
        self.assertEqual(
            (HOU_72_TABLE[-1].gua, HOU_72_TABLE[-1].yao_index,
             HOU_72_TABLE[-1].jq_name, HOU_72_TABLE[-1].wuhou),
            ("蹇", 4, "大雪", "荔挺出"),
            "原典末条：蹇五荔挺出")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
