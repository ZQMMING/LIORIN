"""H6: 化工计算测试

覆盖：NORMAL / REVERSE / RESCUED / KEZHI / UNRESOLVED 五种状态判定

原典依据（2026-10-07 逐条核对）：
  · L582「又有大象与小象化工虽相反，**却又有相生者，则吉。但忌克制，尤凶**。」
  · L597「凡人根基不得化工者，灾重也。……有化工之气者，艰难获福。」
  · L324「离为正伯，即化工也。化工入域……」

⚠ 原书无「论化工」一节（检索 0 处），旧 docstring 的该出处系误植，已删。
"""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.hua_gong import compute_huagong, HuaGongState


class TestHuaGongNormal(unittest.TestCase):
    """NORMAL: 卦中含当令化工卦，无反卦"""

    def test_spring_zhen_no_dui(self):
        """春震卦，卦中含震但无兑 → NORMAL"""
        r = compute_huagong("乾", "震", "乾", "震", "寅")
        self.assertEqual(r.state, HuaGongState.NORMAL)
        self.assertTrue(r.has_huagong)
        self.assertFalse(r.has_opposite)
        self.assertEqual(r.huagong_trigram, "震")

    def test_summer_li_no_kan(self):
        """夏离卦，卦中含离但无坎 → NORMAL"""
        r = compute_huagong("离", "离", "离", "乾", "午")
        self.assertEqual(r.state, HuaGongState.NORMAL)

    def test_autumn_dui_no_zhen(self):
        """秋兑卦，卦中含兑但无震 → NORMAL"""
        r = compute_huagong("兑", "兑", "乾", "兑", "申")
        self.assertEqual(r.state, HuaGongState.NORMAL)

    def test_winter_kan_no_li(self):
        """冬坎卦，卦中含坎但无离 → NORMAL"""
        r = compute_huagong("坎", "坎", "坎", "坤", "子")
        self.assertEqual(r.state, HuaGongState.NORMAL)


class TestHuaGongWuRelation(unittest.TestCase):
    """有化工卦又有反卦时，按 L582 实算五行关系，不得一律判吉。

    原典：「却又有相生者，则吉。**但忌克制，尤凶。**」
    旧实现无条件判 RESCUED（下游映射为 SUPPORTIVE＝吉），
    致坎(水)克离(火)之盘误作吉断——原典明说此为最凶一档。
    """

    def test_summer_li_with_kan_is_kezhi_not_rescued(self):
        """夏离(火) + 坎(水)反卦 → 水克火 → KEZHI，不得判救应。"""
        r = compute_huagong("乾", "离", "坎", "兑", "午")
        self.assertEqual(r.state, HuaGongState.KEZHI)
        self.assertEqual(r.wu_relation, "克制")
        self.assertTrue(r.has_huagong)
        self.assertTrue(r.has_opposite)
        self.assertTrue(any("尤凶" in e for e in r.evidence), r.evidence)

    def test_winter_kan_with_li_is_kezhi_not_rescued(self):
        """冬坎(水) + 离(火)反卦 → KEZHI。"""
        r = compute_huagong("离", "坎", "乾", "坎", "子")
        self.assertEqual(r.state, HuaGongState.KEZHI)
        self.assertEqual(r.wu_relation, "克制")

    def test_autumn_dui_with_zhen_is_kezhi(self):
        """秋兑(金) + 震(木)反卦 → 金克木 → KEZHI。

        2026-10-07 第二轮改：反卦表改回原典 L585–594 的**四季对宫**后，
        兑之反为震（金克木），不再是艮（土生金）。上一轮据此写的
        「RESCUED 唯一相生档」已随表更正而失效。
        """
        r = compute_huagong("乾", "兑", "震", "乾", "申")
        self.assertEqual(r.state, HuaGongState.KEZHI)
        self.assertEqual(r.wu_relation, "克制")

    def test_spring_zhen_with_dui_is_kezhi(self):
        """春震(木) + 兑(金)反卦 → 金克木 → KEZHI。"""
        r = compute_huagong("乾", "震", "兑", "乾", "寅")
        self.assertEqual(r.state, HuaGongState.KEZHI)
        self.assertEqual(r.wu_relation, "克制")

    def test_all_four_hua_gong_opposites_are_ke(self):
        """L585–594 四组化工相反，两两互为克制，无一组相生。

        原典逐条：
          L585「坎卦反离，主夏至以后秋分前。」   坎(水)↔离(火) → 水克火
          L588「离卦反坎，主冬至以后春分前。」   同上反向
          L591「兑卦反震，主春分以后夏至前。」   兑(金)↔震(木) → 金克木
          L594「震卦反兑，主秋分以后冬至前。」   同上反向

        推论（本轴）：「正体 vs 化工相反卦」这一轴上 **RESCUED 不可达**。
        L582「相生者则吉」讲的是大象（先天）与小象（流年）两个化工之间，
        本模块未接流年，该轴未实现。此处把「不可达」显式断言下来，
        免得日后有人以为漏了相生档。
        """
        from heluo_engine.engines.heluo.hua_gong import (
            HUAGONG_FAN_GUA, TRIGRAM_ELEMENT, _wu_relation)
        self.assertEqual(HUAGONG_FAN_GUA,
                         {"坎": "离", "离": "坎", "兑": "震", "震": "兑"})
        for g, o in HUAGONG_FAN_GUA.items():
            rel = _wu_relation(TRIGRAM_ELEMENT[g], TRIGRAM_ELEMENT[o])
            self.assertEqual(rel, "克制", f"{g}↔{o} 应为克制，实为 {rel}")
        self.assertNotIn("乾", HUAGONG_FAN_GUA)
        self.assertNotIn("坤", HUAGONG_FAN_GUA)
        self.assertNotIn("艮", HUAGONG_FAN_GUA)
        self.assertNotIn("巽", HUAGONG_FAN_GUA)

    def test_rescued_unreachable_on_this_axis(self):
        """本轴任一组合都不得判出 RESCUED（因四组全克制）。"""
        from heluo_engine.engines.heluo.hua_gong import HUAGONG_FAN_GUA
        for b, g in (("子", "坎"), ("午", "离"), ("寅", "震"), ("申", "兑")):
            r = compute_huagong("乾", g, HUAGONG_FAN_GUA[g], "乾", b)
            self.assertNotEqual(r.state, HuaGongState.RESCUED,
                                f"{b}月{g} 竟判出 RESCUED")
            self.assertEqual(r.wu_relation, "克制")

    def test_kezhi_maps_to_caution_not_supportive(self):
        """KEZHI 在诊断规则图里必须映射为 CAUTION，不得 SUPPORTIVE。

        原典 L582「但忌克制，尤凶」——判吉是实质错误，不是措辞问题。
        """
        from heluo_engine.engines.heluo.diagnosis_rule_graph import HUAGONG_DIRECTION
        from heluo_engine.spec.canonical import AssertionDirection
        self.assertEqual(HUAGONG_DIRECTION[HuaGongState.KEZHI.value],
                         AssertionDirection.CAUTION)
        self.assertNotEqual(HUAGONG_DIRECTION[HuaGongState.KEZHI.value],
                            AssertionDirection.SUPPORTIVE)


class TestHuaGongRescuedLegacy(unittest.TestCase):
    """原 RESCUED 用例的其余部分（不涉五行关系者保留原判）"""

    def test_spring_zhen_with_dui(self):
        """春震(木) + 兑(金) → 兑是震之**化工相反**（L591）→ 金克木 → KEZHI。

        2026-10-07 第二轮改：反卦表改回原典 L585–594 四季对宫后，
        兑不再「非震之反卦」。旧断言 NORMAL 随表更正而失效。
        """
        r = compute_huagong("兑", "震", "乾", "震", "卯")
        self.assertEqual(r.state, HuaGongState.KEZHI)
        self.assertTrue(r.has_huagong)
        self.assertTrue(r.has_opposite)


class TestHuaGongReverse(unittest.TestCase):
    """REVERSE: 卦中含反卦但无当令化工卦"""

    def test_winter_kan_opposite(self):
        """正体无坎，但**互体**得坎（L576 二级）→ 化工相反 → KEZHI。

        2026-10-07 三轮：旧实现只查正体，故本例判 REVERSE。
        L576「故正不逢而互体得之」确立互体为合法化工层，
        互体得坎（后天互震/坎）后，坎之化工相反离在正体 → 克制。
        """
        r = compute_huagong("乾", "离", "坤", "离", "子")
        self.assertEqual(r.state, HuaGongState.KEZHI)
        self.assertEqual(r.level, "互体")
        self.assertTrue(r.has_huagong)
        self.assertTrue(r.has_opposite)

    def test_summer_li_opposite(self):
        """正体无离，但**互体**得离（L576 二级）→ 化工相反 → KEZHI。

        2026-10-07 三轮：后天互得离（巽/离），坎为离之化工相反，
        水克火 → L582「忌克制，尤凶」。
        """
        r = compute_huagong("坎", "坎", "乾", "坎", "午")
        self.assertEqual(r.state, HuaGongState.KEZHI)
        self.assertEqual(r.level, "互体")


class TestHuaGongUnresolved(unittest.TestCase):
    """UNRESOLVED: 卦中既无化工卦也无反卦"""

    def test_winter_no_kan_no_li(self):
        """冬乾卦，无坎无离 → UNRESOLVED"""
        r = compute_huagong("乾", "乾", "坤", "坤", "子")
        self.assertEqual(r.state, HuaGongState.UNRESOLVED)
        self.assertFalse(r.has_huagong)
        self.assertFalse(r.has_opposite)

    def test_spring_no_zhen_no_dui(self):
        """春巽卦：卦中无震（化工）、亦无兑（震之化工相反）→ 无据。

        2026-10-07 第二轮改：化工相反表改回 L585–594 后不含巽，
        故本例不再是 REVERSE。旧断言随表更正而失效。
        """
        r = compute_huagong("巽", "巽", "乾", "乾", "辰")
        self.assertEqual(r.state, HuaGongState.REVERSE)
        self.assertEqual(r.level, "无")
        self.assertFalse(r.has_huagong)
        self.assertTrue(r.has_opposite)


class TestHuaGongThreeLevels(unittest.TestCase):
    """L576 三级回退：正体 → 互体 → 纳甲纳音（末级福寿减半）

    原典 L576 逐字：「故正不逢而互体得之。若正互俱无，则取纳甲纳音，
    **终是浅薄，福寿减半。**」
    """

    def test_mutual_trigram_matches_original_example(self):
        """互体取法须合原典例：渐卦「九五六四九三互离，六四九三六二互坎」。

        本模块的 compute_mutual_trigram 与 guajie.compute_huti 是两份等价实现
        （hua_gong 不 import guajie 以免循环依赖），此处逐卦对拍防漂移。
        """
        from heluo_engine.engines.heluo.hua_gong import compute_mutual_trigram
        from heluo_engine.engines.heluo.guajie import compute_huti, trigram_to_lines
        self.assertEqual(compute_mutual_trigram("巽", "艮"), ("离", "坎"))
        for upper, lower in (("巽", "艮"), ("乾", "坤"), ("坎", "兑"),
                             ("震", "巽"), ("离", "艮"), ("乾", "乾")):
            lines = list(trigram_to_lines(lower)) + list(trigram_to_lines(upper))
            self.assertEqual(compute_mutual_trigram(upper, lower),
                             compute_huti(lines), f"{upper}/{lower} 两实现漂移")

    def test_level_zhengti(self):
        """正体得化工 → level=正体，不减半。"""
        r = compute_huagong("乾", "震", "乾", "震", "寅")
        self.assertEqual(r.level, "正体")
        self.assertFalse(r.reduced)

    def test_level_huti_when_zhengti_fails(self):
        """正体不得而互体得之 → level=互体（L576 二级）。"""
        r = compute_huagong("坎", "坎", "乾", "坎", "午")
        self.assertEqual(r.level, "互体")
        self.assertFalse(r.reduced, "互体层原典未言减半")

    def test_level_nayin_reduced(self):
        """正互俱无取纳甲纳音 → level=纳音 且 reduced=True（福寿减半）。"""
        r = compute_huagong("乾", "乾", "乾", "乾", "午",
                            year_gan="甲", year_zhi="辰")   # 甲辰纳音火
        self.assertEqual(r.level, "纳音")
        self.assertTrue(r.reduced, "L576「终是浅薄，福寿减半」")
        self.assertTrue(r.has_huagong,
                        "纳音层**确实得了化工**，不得判 has_huagong=False")

    def test_level_none_when_all_fail(self):
        """三层俱无 → level=无，不得硬凑。"""
        r = compute_huagong("乾", "乾", "乾", "乾", "午",
                            year_gan="甲", year_zhi="子")   # 甲子纳音金，与离火不合
        self.assertEqual(r.level, "无")
        self.assertFalse(r.has_huagong)

    def test_evidence_states_level(self):
        """evidence 须写明得化工之层，减半时须显式标注。"""
        r = compute_huagong("乾", "乾", "乾", "乾", "午",
                            year_gan="甲", year_zhi="辰")
        joined = chr(10).join(r.evidence)
        self.assertIn("三级", joined)
        self.assertIn("福寿减半", joined)
        none_ev = chr(10).join(compute_huagong("乾", "乾", "乾", "乾", "午").evidence)
        self.assertIn("若不以震为化工", none_ev,
                      "三层俱无时须引 L576「若不以震为化工，则曰无化工矣」")


class TestHuaGongEvidence(unittest.TestCase):
    """化工证据链完整性"""

    def test_evidence_contains_branch(self):
        """证据链包含出生月支"""
        r = compute_huagong("乾", "震", "乾", "震", "寅")
        self.assertTrue(any("寅" in e for e in r.evidence))

    def test_evidence_contains_huagong_trigram(self):
        """证据链包含当令化工卦"""
        r = compute_huagong("乾", "震", "乾", "震", "寅")
        self.assertTrue(any("震" in e for e in r.evidence))


class TestHuaGongProvenance(unittest.TestCase):
    """出处保真：原书没有的引文不得再挂在代码/守卫上。

    注意：按**区块**判定而非全文匹配。旧写法用 `assertIn(quote, 全文)`
    有个致命漏洞——同一句原话在 docstring、注释、函数文档里往往出现多次，
    删掉其中一处，别的副本还在，守卫照样绿，等于没锁。
    故此处一律切片到具体区块再查。
    """

    @staticmethod
    def _src() -> str:
        return (Path(__file__).resolve().parents[2]
                / "src" / "heluo_engine" / "engines" / "heluo" / "hua_gong.py"
                ).read_text(encoding="utf-8")

    @staticmethod
    def _slice(text: str, start: str, end: str | None = None) -> str:
        i = text.index(start)
        j = text.index(end, i) if end else len(text)
        return text[i:j]

    def test_no_phantom_section_name(self):
        """「起例卷下·论化工」「逢化工诗」原著检索均 0 处。

        判据是「有没有被当作出处引用」，而非「有没有被提到」——
        本守卫自身提到这两个词时带「0 处」标记，故放行。
        """
        ok_ctx = ("0 处", "零命中", "误植", "没有", "检索")
        self_ctx = ("当作出处", "in line", "ok_ctx")
        src = Path(__file__).resolve().parents[2] / "src" / "heluo_engine" / "engines" / "heluo" / "hua_gong.py"
        for txt, name in ((src.read_text(encoding="utf-8"), src.name),
                          (Path(__file__).read_text(encoding="utf-8"), Path(__file__).name)):
            for n, line in enumerate(txt.splitlines(), 1):
                if "论化工" not in line:
                    continue
                if any(k in line for k in self_ctx):
                    continue
                self.assertTrue(any(k in line for k in ok_ctx),
                                f"{name}:{n} 把「论化工」当作出处：{line.strip()}")

    def test_no_phantom_quotes(self):
        """旧注释引的「三元纯正/生气充畅/元气损」在原著均 0 处。"""
        txt = self._src()
        for phantom in ("三元纯正", "生气充畅", "元气损"):
            self.assertNotIn(phantom, txt, f"伪引文复现：{phantom}")

    def test_real_quote_in_module_docstring_block(self):
        """模块出处块须含 L597 真句「艰难获福」。

        区块限定：只查 docstring 的出处清单，不查全文——
        否则函数文档里那份副本会把删改遮住。
        """
        block = self._slice(self._src(), "**原典依据（2026-10-07 逐条核对",
                            "⚠「逢化工诗」")
        self.assertIn("艰难获福", block)
        self.assertIn("忌克制，尤凶", block)
        self.assertIn("离为正伯", block)
        self.assertIn("但要入域", block)

    def test_qianxi_shallowing_caveat_present(self):
        """L576 对「拘于时气」的异议「气有浅深」须在模块 docstring 在位。

        删掉这句＝把作者自己的反对意见抹掉，让简化近似冒充原典硬规则。
        """
        block = self._slice(self._src(), "⚠ 原典 L576 明言此口径", "——即：")
        self.assertIn("气有浅深", block)

    def test_month_branch_block_declared_approximate(self):
        """月支→固定卦的**注释块**须标为近似并引 L576 逐字。"""
        block = self._slice(self._src(), "# 四季 → 地支月 → 化工卦",
                            "# 四季对应化工卦" if "# 四季对应化工卦" in self._src()
                            else "SEASON_BRANCH_TO_HUAGONG")
        self.assertIn("简化近似", block)
        self.assertIn("拘于时气", block)
        self.assertIn("气有浅深", block)

    def test_opposite_is_siji_dukong_per_L585_594(self):
        """化工相反是**四季对宫**（震↔兑），不是先天对宫（震↔巽）。

        原典 L585–594 逐条写明：坎↔离、兑↔震。
        2026-10-07 首轮把注释误订正为「先天对宫」却未动表，
        第二轮一并改回并把两套对宫彻底分开命名。
        """
        from heluo_engine.engines.heluo.hua_gong import (
            HUAGONG_FAN_GUA, QIANXI_DUKONG)
        self.assertEqual(HUAGONG_FAN_GUA["震"], "兑")
        self.assertEqual(HUAGONG_FAN_GUA["兑"], "震")
        self.assertEqual(HUAGONG_FAN_GUA["坎"], "离")
        self.assertEqual(QIANXI_DUKONG["震"], "巽")
        self.assertEqual(QIANXI_DUKONG["兑"], "艮")
        self.assertIsNot(HUAGONG_FAN_GUA, QIANXI_DUKONG)
        self.assertEqual(set(HUAGONG_FAN_GUA), {"坎", "离", "震", "兑"},
                         "化工相反只收四季四卦，乾/坤/艮/巽 不在其列")
        # 2026-10-08 批次 G：QIANXI_DUKONG 由本模块的字典改成了对
        # hexagram_state 的引用，故切片终点跟着改成 import 语句。
        block = self._slice(self._src(), "# 化工相反（四季对宫）",
                            "from .hexagram_state import QIANXI_DUKONG")
        self.assertIn("坎卦反离", block)
        self.assertIn("震卦反兑", block)

    def test_original_has_huagong_lun_section(self):
        """原著确有「化工论」一节（L573），旧出处标注不算误植。

        2026-10-07 首轮检索「论化工」零命中，据此判为误植——实为**词序反了**，
        原著写作「化工论」。该错误判断已于第二轮撤回。
        """
        block = self._slice(self._src(), "**原典依据", "⚠「逢化工诗」")
        self.assertIn("化工论", block)
        self.assertIn("检索式写成", block, "须写明首轮是检索式词序错了，不是原文没有")

    def test_only_fenghuagong_shi_is_phantom(self):
        """「逢化工诗」原著确为 0 处，是唯一仍存疑的出处项。"""
        block = self._slice(self._src(), "⚠「逢化工诗」")
        self.assertIn("0 处", block)


if __name__ == "__main__":
    unittest.main()
