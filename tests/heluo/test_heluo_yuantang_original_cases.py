# -*- coding: utf-8 -*-
"""元堂定位 —— 原典逐盘实例守卫（起例卷 定元堂式 L255-288）

原典在「定元堂式」后给了 21 条逐盘断语，是元堂算法唯一的硬验算材料。
本类把这些断语逐条固化为断言，防止后续改动悄悄漂移。

    L255  如亥时生人得小畜，午未同在六四，申九五，酉上九，戌初九，亥九二是也
    L258  戌时生得讼，午初六，未六三，申复初六，酉复六三，戌九四是也
    L261  亥时生得咸，亥在上六是也
    L264  戌时得明夷，元堂初九是也
    L267  亥时得颐，元堂初九是也
    L270  亥时得升，元堂九三是也
    L273  亥时得谦，元堂九三是也
    L276  巳时得屯，元堂六二是也
    L279  巳时得既济，元堂九五是也
    L282  巳时得大过，元堂在初六
    L285  巳时得遁，元堂在六二
    L288  申时得渐…申时是第三个阴时，合在本卦第三阴爻…正是六四

各条覆盖的算法分支：
    REPEAT               —— N=1/2/3 的重数段
    QI_GONG              —— N=1/2 的寄位回绕
    QI_GONG_ROUNDTRIP    —— N=4/5 且同类爻连续时的寄位回绕
    QI_GONG_MODULO       —— N=4/5 且同类爻有 gap 时的寄位取模
"""

import unittest

from heluo_engine.engines.heluo.numbers import (
    SIXTY_FOUR_HEXAGRAMS,
    build_six_lines,
)
from heluo_engine.engines.heluo.yuan_tang import find_yuantang

_NAME2UL = {v: k for k, v in SIXTY_FOUR_HEXAGRAMS.items()}


def _lines(short: str) -> list[int]:
    """简称（渐 / 小畜 / 讼）→ 六爻（自下而上）。"""
    hits = [v for v in _NAME2UL if v.endswith(short)]
    assert len(hits) == 1, f"卦名无法唯一解析：{short} -> {hits}"
    upper, lower = _NAME2UL[hits[0]]
    return build_six_lines(upper, lower)


# 原典断语：(卦, 时辰, 元堂, 命中的 action 档位)
ORIGINAL_CASES = [
    ("小畜", "午", "六四", "REPEAT"),
    ("小畜", "未", "六四", "REPEAT"),
    ("小畜", "申", "九五", "QI_GONG"),
    ("小畜", "酉", "上九", "QI_GONG"),
    ("小畜", "戌", "初九", "QI_GONG"),
    ("小畜", "亥", "九二", "QI_GONG"),
    ("讼", "午", "初六", "REPEAT"),
    ("讼", "未", "六三", "REPEAT"),
    ("讼", "申", "初六", "REPEAT"),
    ("讼", "酉", "六三", "REPEAT"),
    ("讼", "戌", "九四", "QI_GONG"),
    ("咸", "亥", "上六", "REPEAT"),
    ("明夷", "戌", "初九", "QI_GONG_MODULO"),
    ("颐", "亥", "初九", "QI_GONG_ROUNDTRIP"),
    ("升", "亥", "九三", "QI_GONG_MODULO"),
    ("谦", "亥", "九三", "QI_GONG_MODULO"),
    ("屯", "巳", "六二", "QI_GONG"),
    ("既济", "巳", "九五", "REPEAT"),
    ("大过", "巳", "初六", "QI_GONG_ROUNDTRIP"),
    ("遁", "巳", "六二", "QI_GONG_ROUNDTRIP"),
    ("渐", "申", "六四", "REPEAT"),
]


class TestYuantangOriginalCases(unittest.TestCase):
    """原典 21 条逐盘断语 —— 元堂杂卦算法的硬约束"""

    def _yt(self, gua: str, hour: str):
        return find_yuantang(six_lines=_lines(gua), birth_hour=hour,
                             gender="male", xiantian_name=gua,
                             solar_phase="winter")

    def test_all_21_original_cases(self):
        """21 条原典断语逐条命中"""
        for gua, hour, want, action in ORIGINAL_CASES:
            y = self._yt(gua, hour)
            self.assertEqual(y.yuantang, want,
                             f"原典「{gua} {hour}时元堂{want}」，实得 {y.yuantang}")
            self.assertEqual(y.trace[0]["action"], action,
                             f"{gua} {hour}时 应走 {action} 分支")

    def test_case_count_never_shrinks(self):
        """新增/删除原典用例时必须同步更新本守卫的条数说明"""
        self.assertEqual(len(ORIGINAL_CASES), 21)

    def test_xugua_group_covers_whole_six_hours(self):
        """小畜 L255 给了整组六时断语，全部要中"""
        want = {"午": "六四", "未": "六四", "申": "九五",
                "酉": "上九", "戌": "初九", "亥": "九二"}
        for h, exp in want.items():
            self.assertEqual(self._yt("小畜", h).yuantang, exp, f"小畜 {h}时")

    def test_song_group_covers_five_hours(self):
        """讼 L258 给了整组断语（原文至戌时止）"""
        want = {"午": "初六", "未": "六三", "申": "初六",
                "酉": "六三", "戌": "九四"}
        for h, exp in want.items():
            self.assertEqual(self._yt("讼", h).yuantang, exp, f"讼 {h}时")

    def test_zhan_third_yin_hour_takes_third_yin_yao(self):
        """渐 L288 原典自释：申时是第三个阴时，取本卦第三阴爻（六四）"""
        y = self._yt("渐", "申")
        self.assertEqual(y.yuantang, "六四")
        # 阴时组第三个时辰 = 申（午、未、申）
        yin_yao_idx = [i for i, l in enumerate(_lines("渐")) if l == -1]
        self.assertEqual(y.yuantang_index, yin_yao_idx[2],
                         "申时（第三个阴时）应落第三个阴爻")

    def test_mixed_gua_ignores_gender(self):
        """L294「父母与六子安时元堂不同」—— 乾坤之外诸卦不按男女分"""
        for gua, hour, want, _ in ORIGINAL_CASES:
            for gender in ("male", "female"):
                y = find_yuantang(six_lines=_lines(gua), birth_hour=hour,
                                  gender=gender, xiantian_name=gua,
                                  solar_phase="winter")
                self.assertEqual(y.yuantang, want,
                                 f"{gua} {hour}时 {gender} 应同为 {want}")

    def test_mixed_gua_ignores_solar_phase(self):
        """杂卦不应受节气影响（冬夏两季结果必须相同）"""
        for gua, hour, want, _ in ORIGINAL_CASES:
            for phase in ("winter", "summer"):
                y = find_yuantang(six_lines=_lines(gua), birth_hour=hour,
                                  gender="male", xiantian_name=gua,
                                  solar_phase=phase)
                self.assertEqual(y.yuantang, want,
                                 f"{gua} {hour}时 {phase} 应同为 {want}")


class TestYuantangEngineDefinedPaths(unittest.TestCase):
    """ENGINE_DEFINED 路径的现状锁定（无原典实例者，显式登记而非默默跑）"""

    def test_n4n5_single_pass_is_engine_defined(self):
        """N=4/5 的单飞段（action=NORMAL）原典零实例。

        L249/252 只说「四阴四阳卦…虽有寄位，无重数」，未给落点。
        当前实现为「N 个同类爻配 N 个时辰顺飞」，属结构性推论。
        本测试锁定现状并显式命名，防止后人误认有原典背书。
        """
        lines = _lines("大过")          # 阳爻 idx=[1,2,3,4] 连续，n=4
        sub = [find_yuantang(six_lines=lines, birth_hour=h, gender="male",
                             xiantian_name="大过", solar_phase="winter")
               for h in ("子", "丑", "寅", "卯", "辰", "巳")]
        self.assertEqual([y.trace[0]["action"] for y in sub],
                         ["NORMAL"] * 4 + ["QI_GONG_ROUNDTRIP", "QI_GONG_ROUNDTRIP"])
        self.assertEqual([y.yuantang for y in sub],
                         ["九二", "九三", "九四", "九五", "上六", "初六"])
        # 末位「初六」即原典 L282「巳时得大过，元堂在初六」

    def test_pure_gua_summer_phase_is_engine_defined(self):
        """**已于 2026-10-07 裁决并改实现**：纯卦元堂冬夏**同族**，皆为线性六爻推移。

        本测试原为「冬重数、夏线性」两版缝合现状的快照，现改为正文版守卫：
        L297「男得乾……十二时皆自下而行上，子午皆在初爻」＋
        「女得乾……生冬至以后至夏至以前，自上九为始，往下行至初爻；
          若生夏至以后至冬至以前，当自初九为始，往上行至上九」。

        故女乾：冬半年自上爻起步往下行，夏半年自初爻起步往上行，
        两者**同为「逐时移一爻」的线性推移**，只是起点相反。
        「又一本云」重数版（L306-315）已废止，理由见 yuan_tang.py 同处裁决注
        与 heluo_engine/docs/纯卦元堂重数规则定案_20261007.md 更正块。
        """
        qian = [1] * 6
        hours = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
        winter = [find_yuantang(six_lines=qian, birth_hour=h, gender="female",
                                xiantian_name="乾", solar_phase="winter").yuantang_index
                  for h in hours]
        summer = [find_yuantang(six_lines=qian, birth_hour=h, gender="female",
                                xiantian_name="乾", solar_phase="summer").yuantang_index
                  for h in hours]
        # 冬：自上九(5)为始往下行 → 子5 丑4 寅3 卯2 辰1 巳0 午5 …
        self.assertEqual(winter, [5, 4, 3, 2, 1, 0, 5, 4, 3, 2, 1, 0])
        # 夏：自初九(0)为始往上行 → 子0 丑1 寅2 卯3 辰4 巳5 午0 …
        self.assertEqual(summer, [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5])
        self.assertNotEqual(winter, summer,
                            "若此断言失败，说明冬夏已同向，请更新本测试与"
                            "heluo_engine/docs/元堂算法核验_20261007.md 的裁决记录")
        # 冬夏互为镜像：夏[h] == 5 - 冬[h]
        for w, s in zip(winter, summer):
            self.assertEqual(s, 5 - w, "冬夏两分支应为起点相反的同族线性推移")


class TestHexagramAuxiliaryGua(unittest.TestCase):
    """互卦/错卦/综卦 —— 2026-10-07 接线（原三键恒 None）

    互体依据原典 L423「以正体内外卦除初上二爻，用中四爻，交互成卦，谓之互体」，
    并有原典实例可核：渐卦「九五六四九三互离，六四九三六二互坎，合之为未济」。
    错卦＝六爻全变（上下各取对宫）；综卦＝上下卦互换。
    """

    def _s(self, gua: str):
        from heluo_engine.engines.heluo.hexagram import analyze_hexagram
        return analyze_hexagram(gua)

    def test_hu_gua_matches_original_jian_case(self):
        """原典硬验证：渐卦互体必为未济"""
        self.assertEqual(self._s("风山渐").hu_gua, "火水未济")

    def test_hu_gua_known_cases(self):
        cases = {
            "乾为天": "乾为天",       # 六爻同阴阳，取中四爻仍同
            "坤为地": "坤为地",
            "天水讼": "风火家人",
            "泽山咸": "天风姤",
        }
        for gua, want in cases.items():
            self.assertEqual(self._s(gua).hu_gua, want, f"{gua} 互体")

    def test_cuo_gua_is_opposite(self):
        """错卦：上下各取对宫。乾↔坤、坎↔离、震↔巽、艮↔兑"""
        for gua, want in {"乾为天": "坤为地", "天水讼": "地火明夷",
                          "泽山咸": "山泽损", "水雷屯": "火风鼎"}.items():
            self.assertEqual(self._s(gua).cuo_gua, want, f"{gua} 错卦")

    def test_zong_gua_is_six_line_reversal(self):
        """综卦（反对）：**六爻整体倒转**。

        2026-10-22 依原典改正。旧实现只把上下卦**对调**、三画卦内部不倒，
        与仓内另一份综卦表（注释明写「六爻倒转」）在 64 卦中 48 卦上冲突。

        原典（《河洛真数·起例卷之下》L46-L48「六十四卦反对图」）：
            L47: 上经正卦六，反卦二十四，共用十八卦，成三十卦。
                 下经正卦二，反卦三十二，亦用十八卦，成三十四卦。
        「正卦」= 自反卦（倒转后仍是自己）。原典要求上经 6 个、下经 2 个。
        严格六爻倒转给出：上经 6（乾坤坎离颐大过）、下经 2（中孚小过）——
        逐位吻合；上下卦对调只给 4/4，不符。

        故：泽山咸（上兑下艮）倒转后是**雷风恒**（下卦艮倒为震、上卦兑倒为巽），
        不是山泽损；山泽损是它的**错卦**。
        """
        for gua, want in {"天水讼": "水天需", "泽山咸": "雷风恒",
                          "地火明夷": "火地晋", "乾为天": "乾为天",
                          "雷山小过": "雷山小过"}.items():
            self.assertEqual(self._s(gua).zong_gua, want, f"{gua} 综卦")

    def test_no_key_is_none_anymore(self):
        """三键不得再为 None（本次接线前恒空）"""
        for gua in ("乾为天", "风山渐", "天水讼", "泽山咸", "地火明夷"):
            s = self._s(gua)
            for key in ("hu_gua", "cuo_gua", "zong_gua"):
                self.assertTrue(getattr(s, key), f"{gua}.{key} 仍为空")


if __name__ == "__main__":
    unittest.main()
