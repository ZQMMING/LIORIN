"""起日卦（流日）算法与原著逐条对照 —— 2026-10-07

**本文件是「第一性硬编码」守卫，不调用被测函数来算期望值。**

起因：P0-1 把流日从「每段一卦」改成「逐日一爻」后，原有测试被改成
「调用 liuri_day_positions 复算，再和引擎输出比对」——那是**自证循环**：
把 liuri_day_positions 换成 `pos = (pos + 1) % 6` 也能 563 项全绿。
故此处把原典 L390 的字面结果直接写死为期望值。

原典依据（起例卷之上 L390、L393）：

    凡起日卦，于月中寻日，以流月卦前一爻为初一日，每一爻管五日，
    阳日寻阳爻位，（初三五为阳位。）阴日寻阴爻位。（二四上为阴位。）
    假如正月得乾卦初爻，初一日当在三爻，变为履六三，
    初二日变履九四为中孚六四，初三日变中孚九五为损六五，
    初四日变损上九为临上六，初五日变临初九为师初六，挨次而变，不容紊也。
    若月卦得乾二爻，则初一日在三爻起，不待言矣。……
    六爻俱变毕，则满三十日，是为一月之日卦。

口径裁决（**「进一爻起」采信，「前一爻为初一日」不采**）：
    - 乾初爻居位 → 前一爻读作「上爻」时，初一阳日应落五爻，与原文
      「初一日当在三爻」矛盾；读作「进一爻」时自二爻起步、初一阳日
      落三爻，与原文**完全吻合**。
    - 乾二爻居位 → 进一爻得三爻，原文「若月卦得乾二爻，则初一日在三爻起」
      **再次吻合**。
    两处实例互证，故采「进一爻起」。L390 首句「以流月卦前一爻为初一日」
    与同段实例自相矛盾，登记为异文，不据此造规则。
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

from tongshu.engines.heluo.numbers import build_six_lines
from tongshu.engines.heluo.timeline_yun import (
    _flip_line,
    _lines_to_hexagram,
    compute_liuri,
    compute_liuri_stub,
    liuri_day_positions,
    materialize_month_days,
)

QIAN = [1, 1, 1, 1, 1, 1]          # 乾卦六爻俱阳
_YAO = ("初", "二", "三", "四", "五", "上")


class TestLiuriLiteralPositions(unittest.TestCase):
    """原典 L390 阴阳位规则的**字面**展开值（非调用被测函数得来）。"""

    # 六个居位爻各自的 30 日爻位序列（初一起，六日一轮 × 5）
    #
    # 推导只用原典两句：初一为阳日取阳位（初/三/五）、初二为阴日取阴位
    # （二/四/上）、「挨次而变，不容紊也」——即每日自上一日爻位顺推，
    # 取最近的合规位。手工枚举如下：
    #   居初爻(yi=0)：进一爻得二爻 → 初一阳日遇二爻不合，取三爻 → 2,3,4,5,0,1
    #   居二爻(yi=1)：进一爻得三爻（本身阳位）          → 2,3,4,5,0,1
    #   居三爻(yi=2)：进一爻得四爻 → 初一阳日不合，取五爻 → 4,5,0,1,2,3
    #   居四爻(yi=3)：进一爻得五爻（本身阳位）          → 4,5,0,1,2,3
    #   居五爻(yi=4)：进一爻得上爻 → 初一阳日不合，取初爻 → 0,1,2,3,4,5
    #   居上爻(yi=5)：进一爻得初爻（本身阳位）          → 0,1,2,3,4,5
    EXPECTED = {
        0: [2, 3, 4, 5, 0, 1] * 5,
        1: [2, 3, 4, 5, 0, 1] * 5,
        2: [4, 5, 0, 1, 2, 3] * 5,
        3: [4, 5, 0, 1, 2, 3] * 5,
        4: [0, 1, 2, 3, 4, 5] * 5,
        5: [0, 1, 2, 3, 4, 5] * 5,
    }

    def test_positions_match_literal_expansion(self):
        for yi, want in self.EXPECTED.items():
            got = liuri_day_positions(yi)
            self.assertEqual(got, want,
                             f"居{_YAO[yi]}爻的 30 日爻位序列与原典展开值不符")

    def test_original_qian_first_yao_starts_at_third(self):
        """原典「假如正月得乾卦初爻，初一日当在三爻」"""
        self.assertEqual(liuri_day_positions(0)[0], 2,
                         "乾初爻居位，初一日必须在三爻")

    def test_original_qian_second_yao_starts_at_third(self):
        """原典「若月卦得乾二爻，则初一日在三爻起，不待言矣」"""
        self.assertEqual(liuri_day_positions(1)[0], 2,
                         "乾二爻居位，初一日亦在三爻")

    def test_each_yao_exactly_five_days(self):
        """原典「每一爻管五日」+「六爻俱变毕，则满三十日」"""
        self.assertEqual(_LIURI_DAYS := 30, 30)
        for yi in range(6):
            seq = liuri_day_positions(yi)
            self.assertEqual(len(seq), _LIURI_DAYS)
            for p in range(6):
                self.assertEqual(seq.count(p), 5,
                                 f"居{_YAO[yi]}爻时 {_YAO[p]}爻未恰好管满 5 日")

    def test_odd_days_never_on_yin_position(self):
        """原典「阳日寻阳爻位（初三五）」「阴日寻阴爻位（二四上）」"""
        for yi in range(6):
            seq = liuri_day_positions(yi)
            for i, p in enumerate(seq):
                if (i + 1) % 2 == 1:          # 阳日
                    self.assertIn(p, (0, 2, 4), f"居{_YAO[yi]}爻 阳日落阴位")
                else:                          # 阴日
                    self.assertIn(p, (1, 3, 5), f"居{_YAO[yi]}爻 阴日落阳位")


class TestLiuYaoAreLegalLineNames(unittest.TestCase):
    """2026-10-07 公案关闭：「履六三」**不是**讹字。

    本轮之前，本项目把起日卦原文「变为履六三」登记为「原典讹字」，
    理由是「履卦无六三」。**该断言是错的**，已由网络核查推翻：

    - 通行本《周易·履卦》爻辞确有「**六三**：眇能视，跛能履，履虎尾，
      咥人，凶。武人为于大君。」六三是履卦**唯一**的柔爻（阴爻），以阴居阳位。
    - 履 = 上乾下**兑**；兑卦三爻为阴（兑☱ 上爻虚），故下卦三爻即阴爻 → 六三。
    - 《河洛真数·起例卷之中》乾卦条亦云「后天变**履六三**，履虎尾，咥人凶」，
      用字与《周易》爻辞完全一致，可见本书按通行本爻名用字。

    本类把这条卦画事实写成守卫，防止后人再以「履无六三」为由改错卦表或改原典。
    """

    def test_lv_hexagram_third_yao_is_yin(self):
        """履卦 = 上乾下兑，兑三爻为阴 → 六三。"""
        lines = build_six_lines("乾", "兑")
        self.assertEqual(_lines_to_hexagram(lines)[2], "天泽履")
        self.assertEqual(lines[2], -1, "履卦第三爻必须是阴爻，否则「履六三」不成立")
        self.assertEqual([i for i, l in enumerate(lines) if l == -1], [2],
                         "六三须是履卦唯一柔爻")

    def test_all_five_original_line_names_are_legal(self):
        """原典 L390 五日的变爻名在本卦中都必须真的存在。"""
        cur = list(QIAN)
        for d, (pos, gua, yao) in enumerate(TestLiuriOriginalFiveDays.FIVE_DAYS, start=1):
            cur = _flip_line(cur, pos)
            got = _yao_name(pos, cur[pos])
            self.assertEqual(got, yao, f"初{d}日变爻名不符")
            # 该爻名必须与本卦实际六爻自洽（爻性对得上）
            expect_ch = "九" if cur[pos] == 1 else "六"
            self.assertTrue(yao.startswith(expect_ch) or yao.endswith(expect_ch),
                            f"{gua}{yao} 爻性与卦画不符")

    def test_original_text_appears_in_both_transcriptions(self):
        """本地两份转录的起日卦例必须逐字一致（排除单一录入错误）。

        A = data/heluo/guajie_raw/河洛真数_起例卷之上.txt
        B = 用户提供的整本 txt（本轮未变，见下）
        网络核查另比对：diancang.xyz「陈图南先生河洛真数起例卷之上」
        与 shidianguji.com 影印本转录，三者起日卦例文字一致
        （影印本为繁体，含 OCR 异体字如「馮/爲」，语义逐字相同）。
        """
        import os
        root = Path(__file__).resolve().parents[2]
        raw = root / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之上.txt"
        text = raw.read_text(encoding="utf-8")
        for frag in ("凡起日卦，于月中寻日",
                     "阳日寻阳爻位，（初三五为阳位。）阴日寻阴爻位。（二四上为阴位。）",
                     "初一日当在三爻，变为履六三",
                     "初二日变履九四为中孚六四",
                     "初三日变中孚九五为损六五",
                     "初四日变损上九为临上六",
                     "初五日变临初九为师初六",
                     "挨次而变，不容紊也",
                     "六爻俱变毕，则满三十日"):
            self.assertIn(frag, text, f"起日卦例原文缺失：{frag}")
        self.assertTrue(os.path.exists(raw))


class TestLiuriOriginalFiveDays(unittest.TestCase):
    """原典 L390 乾卦初爻居位，初一至初五的逐日断语**逐字**复现。

    原文：
        初一日当在三爻，变为履六三
        初二日变履九四为中孚六四
        初三日变中孚九五为损六五
        初四日变损上九为临上六
        初五日变临初九为师初六
    """

    # (爻位, 卦名, 变爻名)  —— 全部照抄原典，不含任何推导
    FIVE_DAYS = [
        (2, "天泽履", "六三"),
        (3, "风泽中孚", "六四"),
        (4, "山泽损", "六五"),
        (5, "地泽临", "上六"),
        (0, "地水师", "初六"),
    ]

    def test_five_days_reproduce_original_text(self):
        """链式累变：自 FIVE_DAYS 的字面爻位自行累翻，**不调用被测函数**求卦。"""
        cur = list(QIAN)
        for d, (pos, gua, yao) in enumerate(self.FIVE_DAYS, start=1):
            self.assertEqual(liuri_day_positions(0)[d - 1], pos,
                             f"初{d}日爻位不符原典（原文：三爻）")
            cur = _flip_line(cur, pos)          # ← 自**前一日卦**继续翻
            self.assertEqual(_lines_to_hexagram(cur)[2], gua,
                             f"初{d}日变卦不符原典（原文：{gua}）")
            self.assertEqual(_yao_name(pos, cur[pos]), yao,
                             f"初{d}日变爻名不符原典（原文：{yao}）")

    def test_single_flip_model_would_contradict_original(self):
        """反证：若取「月卦单爻翻转」（2026-09-12 旧口径），初二~初五全错。

        这条断言把「为什么必须是链式」钉死，防止有人日后以「另画一乾卦」
        一句为据把实现改回单变。
        """
        wrong = [_lines_to_hexagram(_flip_line(QIAN, pos))[2]
                 for pos, _, _ in self.FIVE_DAYS]
        self.assertEqual(
            wrong, ["天泽履", "风天小畜", "火天大有", "泽天夬", "天风姤"],
            "单变口径的结果变了——原典五日实例的判定前提已被篡改")
        for got, (_, gua, _) in zip(wrong, self.FIVE_DAYS):
            if gua != "天泽履":
                self.assertNotEqual(got, gua,
                                    "单变竟然也吻合原典？请重新核对 L390")


class TestComputeLiuriMatchesOriginal(TestLiuriOriginalFiveDays):
    """把上面的字面期望钉到生产函数 :func:`compute_liuri` 上。

    父类只验「规则本身推得原典」，本类验「引擎真按该规则出卦」——
    两层缺一不可：只验前者，实现错了也不红；只验后者，期望值会被
    实现反向污染。
    """

    def test_compute_liuri_first_five_days(self):
        res = compute_liuri(QIAN, 0)
        items = [it for seg in res.days for it in seg["day_items"]]
        self.assertEqual(len(items), 30)
        for d, (pos, gua, yao) in enumerate(self.FIVE_DAYS, start=1):
            it = items[d - 1]
            self.assertEqual(it["day"], d)
            self.assertEqual(it["day_yao_index"], pos)
            self.assertEqual(it["name"], gua,
                             f"compute_liuri 初{d}日卦名与原典不符（原文 {gua}）")
            self.assertEqual(_yao_name(it["day_yao_index"], it["lines"][pos]), yao,
                             f"compute_liuri 初{d}日变爻名与原典不符（原文 {yao}）")

    def test_compute_liuri_stub_lines_equal_full_days(self):
        """按需化路径（stub）的 day_lines 必须与全量路径逐字一致。

        2026-10-22 口径统一后，``compute_liuri_stub`` 默认走 **gua6**（定稿口径）；
        本类对拍的是《河洛真数》L390 的 **hou5** 原典变体，故显式指定
        ``rule="hou5"`` —— **原典对拍不因生产口径统一而失效**。
        """
        full = compute_liuri(QIAN, 0)
        stub = compute_liuri_stub(QIAN, 0, rule="hou5")
        self.assertEqual(len(stub), 6, "hou5 原典变体是六段 × 五日")
        for k, (seg_f, seg_s) in enumerate(zip(full.days, stub), start=1):
            self.assertEqual(seg_s["flip_index"], seg_f["flip_index"], f"第{k}段")
            self.assertEqual(seg_s["lines"], seg_f["lines"], f"第{k}段段级六爻")
            self.assertEqual(
                seg_s["day_lines"],
                [it["lines"] for it in seg_f["day_items"]],
                f"第{k}段逐日六爻")

    def test_materialize_month_days_matches_compute(self):
        """hou5 变体的物化结果必须与 compute_liuri 逐字一致（原典对拍）。"""
        month = {"lines": QIAN, "yue_yao_index": 0, "jie_datetime": None,
                 "liuri_rule": "hou5",
                 "days": compute_liuri_stub(QIAN, 0, rule="hou5")}
        got = materialize_month_days(month)
        want = compute_liuri(QIAN, 0).days
        self.assertEqual(got, want,
                         "materialize_month_days 与 compute_liuri 不一致")


class TestGua6AndHou5DoNotBleed(unittest.TestCase):
    """两套流日口径必须**各自独立**，互不串味（2026-10-22 口径统一后新增）。

    · hou5（《河洛真数》L390）：6 段 × 5 日，变爻位按阳日寻阳位/阴日寻阴位
    · gua6（定稿口径，一卦管 6 日）：5 段 × 6 日，首日从初爻起

    生产口径是 gua6；hou5 仅供原典对拍。二者若串味，
    「同一问题两种答案」的缺陷就会复活。
    """

    def test_default_stub_is_gua6(self):
        """默认即 gua6：五段 × 六日，段首日 = 初爻。"""
        stub = compute_liuri_stub(QIAN, 0)
        self.assertEqual(len(stub), 5, "gua6 是五段 × 六日")
        for k, seg in enumerate(stub):
            self.assertEqual(seg["rule"], "gua6")
            self.assertEqual(seg["day_from"], k * 6 + 1)
            self.assertEqual(seg["day_to"], k * 6 + 6)
            self.assertEqual(seg["flip_index"], 0, "gua6 段首日 = 初爻")
            self.assertEqual(seg["day_positions"], [0, 1, 2, 3, 4, 5])

    def test_hou5_stub_is_still_six_by_five(self):
        """hou5 原典变体不受影响：六段 × 五日。"""
        stub = compute_liuri_stub(QIAN, 0, rule="hou5")
        self.assertEqual(len(stub), 6)
        for k, seg in enumerate(stub):
            self.assertEqual(seg["rule"], "hou5")
            self.assertEqual(seg["day_from"], k * 5 + 1)
            self.assertEqual(seg["day_to"], k * 5 + 5)

    def test_two_rules_give_different_hexagrams(self):
        """两套口径对同一日给出不同卦 —— 证明它们确实不是同一算法的别名。"""
        g_seg = compute_liuri_stub(QIAN, 0, rule="gua6")
        h_seg = compute_liuri_stub(QIAN, 0, rule="hou5")
        self.assertNotEqual(g_seg[0]["day_lines"], h_seg[0]["day_lines"])

    def test_materialize_honours_explicit_rule(self):
        """materialize_month_days 必须按显式 rule 分流，不得靠形状嗅探。"""
        g_month = {"lines": QIAN, "yue_yao_index": 0, "liuri_rule": "gua6",
                   "days": compute_liuri_stub(QIAN, 0, rule="gua6")}
        h_month = {"lines": QIAN, "yue_yao_index": 0, "liuri_rule": "hou5",
                   "days": compute_liuri_stub(QIAN, 0, rule="hou5")}
        g_days = materialize_month_days(g_month)
        h_days = materialize_month_days(h_month)
        self.assertEqual(len(g_days), 30, "gua6 物化出 30 个逐日条目")
        self.assertEqual(len(h_days), 6, "hou5 物化出 6 个段条目")
        self.assertNotEqual(g_days[0].get("name"), h_days[0].get("name"))


def _yao_name(idx: int, line: int) -> str:
    ch = "九" if line == 1 else "六"
    if idx == 0:
        return f"初{ch}"
    if idx == 5:
        return f"上{ch}"
    return f"{ch}{_YAO[idx]}"


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
