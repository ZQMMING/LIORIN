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

from heluo_engine.engines.heluo.guajie import (
    compute_huti, judge_nayin_yuanqi, get_nayin_element,
    judge_si_duan, judge_jiehua_gong, judge_nayin_huti,
    compose_guajie, hexagram_to_lines,
)
from heluo_engine.engines.heluo.yuan_tang import find_yuantang, HOUR_NAMES


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
    """死断诸法（起例卷之下·后天详说）

    2026-10-06 按原著上下文校订后重写。以下旧断言锁的是**未校订口径**，
    与原典原文冲突，故按原典改写而非保留：
      · 旧 test_xiaoxiang_fandui 不传 dayun_line_index 就能触发「定死」——
        原典该句系「无阴骘者…便死」分支的附加条件，须先入君爻才谈得上。
      · 旧 test_kanli 用近三年**流年**判词触发「连三爻」——
        原典「连三爻」主语是大运所历之**爻**。
      · 旧断言只看关键词命中，不校验限定语——本类新增四段式结构校验。
    """

    def test_junyao_death(self):
        """后天行至君爻（五爻）→ 原典立断"""
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=4, dayun_phase="后天")
        self.assertTrue(any("君爻" in x for x in w), w)

    def test_junyao_keeps_yinzhi_both_branches(self):
        """阴骘前置必须两支并陈，不得径取「无阴骘」一支。

        原典：「无阴骘者，生日之前便死」「有阴骘者，到君爻阳爻延九年」。
        阴骘＝暗中积德（出《书·洪范》「惟天阴骘下民」），非生辰可推，
        故引擎不得替用户预设其有无。
        """
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=4, dayun_phase="后天")
        joined = "\n".join(w)
        self.assertIn("无阴骘者", joined)
        self.assertIn("有阴骘者", joined)
        self.assertIn("不作预设", joined)

    def test_shangji(self):
        """上极一爻 → 原典于上极所列后果"""
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=5, dayun_phase="后天")
        self.assertTrue(any("上极" in x for x in w), w)

    def test_shangji_keeps_full_consequences(self):
        """上爻后果不得只引「寿必不久」半句。

        原典另列「主大变之祸殃…或生异疾，或殃及子孙，或反本复始之失」，
        且紧接着说「有过此上极之爻，当为超凡越世之士」。
        """
        joined = "\n".join(judge_si_duan(
            prenatal_name="比", postnatal_name="解",
            dayun_line_index=5, dayun_phase="后天"))
        for kw in ("祸殃", "异疾", "殃及子孙", "反本复始", "超凡越世"):
            self.assertIn(kw, joined, f"上爻断语漏了「{kw}」")

    def test_three_years_bad_plus_chongfan(self):
        """流年连三年不吉+数凶+重反支干元气 → 死断

        本条**刻意不传 dayun_phase**：原典该句另起「若」字新分句、
        主语是流年（流年不分先后天段），与①②③④的大运爻位口径不同。
        门控与否原典未明，两存待考——此处锁死「不门控」这一侧，
        改判须同步改本守卫，不得静默变更。
        """
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
        """小象大象反对+爻凶+已入君爻 → 定死无疑（泰↔否综卦）

        原典该句系「无阴骘」分支的附加条件，故须 dayun_line_index>=4。
        """
        w = judge_si_duan(prenatal_name="泰", postnatal_name="大畜",
                          dayun_line_index=4, dayun_phase="后天",
                          recent_years=[{"year": 2020, "hexagram": "否",
                                         "ci": "否之匪人，不利君子贞。凶", "buye": "", "suiyun": ""}])
        self.assertTrue(any("定死" in x for x in w), w)

    def test_fandui_requires_junyao(self):
        """未入君爻时不作「定死无疑」——原典该句是君爻分支的附加条件。"""
        w = judge_si_duan(prenatal_name="泰", postnatal_name="大畜",
                          dayun_line_index=2, dayun_phase="后天",
                          recent_years=[{"year": 2020, "hexagram": "否",
                                         "ci": "否之匪人，不利君子贞。凶", "buye": "", "suiyun": ""}])
        self.assertFalse(any("定死" in x for x in w), w)

    def test_guo_di_shi_fou_means_entered_junyao(self):
        """「若过了第四爻」指已过四爻入五爻，不是正行第四爻。

        原著同篇「大易之数」条自释：「以上初是初爻，**以五上是过**」，
        「过」为越过本爻入下一爻。故 li>=4 才成立。
        """
        bad = [{"year": 2020, "hexagram": "否",
                "ci": "否之匪人，不利君子贞。凶", "buye": "", "suiyun": ""}]
        at_four = judge_si_duan(prenatal_name="比", postnatal_name="解",
                                dayun_line_index=3, dayun_phase="后天",
                                recent_years=bad)
        self.assertFalse(any("十死八九" in x for x in at_four), at_four)
        at_five = judge_si_duan(prenatal_name="比", postnatal_name="解",
                                dayun_line_index=4, dayun_phase="后天",
                                recent_years=bad)
        self.assertTrue(any("十死八九" in x for x in at_five), at_five)

    def test_kanli(self):
        """连三爻不吉 → 多坎壈（主语是大运所历之爻，非流年）

        原典「若**行后天**，连三爻不吉」——主语是后天段，故三爻须全带
        phase="后天" 才成立（2026-10-06 补门控，见 test_kanli_not_in_prenatal）。
        """
        bad3 = [{"hexagram": "剥", "yao": "初六", "phase": "后天",
                 "ci": "凶", "buye": "", "suiyun": ""}] * 3
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=2, recent_dayun_yao=bad3)
        self.assertTrue(any("坎壈" in x for x in w), w)

    def test_kanli_not_in_prenatal(self):
        """先天段不得触发「连三爻不吉」——原典限定「行后天」。"""
        bad3 = [{"hexagram": "渐", "yao": "初六", "phase": "先天",
                 "ci": "凶", "buye": "", "suiyun": ""}] * 3
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=2, recent_dayun_yao=bad3)
        self.assertFalse(any("坎壈" in x for x in w), w)

    def test_kanli_not_triggered_by_liunian_only(self):
        """只给近三年流年不得触发「连三爻」——原典主语是大运爻。"""
        bad3 = [{"year": 2015, "hexagram": "剥", "ci": "凶", "buye": "", "suiyun": ""}] * 3
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=2, recent_years=bad3)
        self.assertFalse(any("坎壈" in x for x in w), w)

    def test_normal_no_trigger(self):
        """正常流年不触发死断"""
        good = [{"year": 2020, "hexagram": "井", "ci": "井渫不食，为我心恻",
                 "buye": "", "suiyun": "岁运逢之，得贵人助"}]
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=1, dayun_phase="后天",
                          recent_years=good)
        self.assertEqual(w, [])

    def test_every_line_has_four_segments(self):
        """每条断语必须是四段式，且开头带「勿字面直解」警示。

        原典硬断句（到此必死／寿必不久／十死八九／定死无疑）在中文里
        没有第二种读法，直出到 LLM 上下文必被字面复述成寿命断言。
        """
        bad = [{"year": 2015, "hexagram": "剥", "ci": "凶", "buye": "", "suiyun": ""}] * 3
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=5, dayun_phase="后天",
                          tian_yuan_fan="坤", di_yuan_fan="震", shu_xiong=True,
                          recent_years=bad,
                          recent_dayun_yao=[{"hexagram": "剥", "yao": "初六",
                                              "phase": "后天",
                                              "ci": "凶", "buye": "", "suiyun": ""}] * 3)
        self.assertTrue(w)
        for line in w:
            self.assertTrue(line.startswith("【原典断语·须带条件读，勿字面直解】"), line)
            for seg in ("｜触发：", "｜限定：", "｜异说："):
                self.assertIn(seg, line, f"断语缺 {seg} 段：{line}")

    def test_alt_school_recorded_on_junyao(self):
        """君爻条须带出原典内部的异说（行到四爻方可断生死）。"""
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=4, dayun_phase="后天")
        self.assertTrue(any("行到四爻，方可断人生死" in x for x in w), w)


class TestSiDuanJunyaoNotShangji(unittest.TestCase):
    """君爻（五爻）与上极（上爻）两级分明，不得合并。

    原典「纵到君爻，亦不许行至上极一爻」——君爻在前、上极在后，是先后
    两级。旧实现 dayun_line_index >= 4 把上爻并入君爻条，导致行上爻时
    误报「行至君爻」。2026-10-06 修为 == 4。
    """

    def test_junyao_only_at_five(self):
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=4, dayun_phase="后天")
        self.assertTrue(any("君爻" in x for x in w), w)

    def test_shangji_does_not_report_junyao(self):
        """行上爻（li=5）只出上极条，不得并报君爻条。

        注意：上极条引文含「纵到**君爻**，亦不许行至上极一爻」——「君爻」
        二字属原句内容，不是误报君爻。故按「触发」段判定，不做全文匹配。
        """
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=5, dayun_phase="后天")
        self.assertTrue(any("上极" in x for x in w), w)
        # 君爻条的触发段写「行至五爻」，上极条触发段写「行至上爻」——
        # 上爻时不应出现「行至五爻」这一君爻专属触发语。
        self.assertFalse(any("触发：后天运程行至五爻" in x for x in w), w)


class TestSiDuanHouTianOnly(unittest.TestCase):
    """死断四法（君爻/过四爻/小象大象反对/上极）原典**只限后天段**。

    原典三处独立明证：
      L1552「如**后天**之气数行至君爻之位，此为数足，到此必死……
             纵到君爻，亦不许行至上极一爻，寿必不久」
      L1555「若**行后天**，连三爻不吉，必多坎壈」
      L1567「此数不许行到**后天**五爻，行到四爻，方可断人生死」
    且全库检索「先天之气数」零命中——原典无先天死断一支。

    2026-10-07 修：_collect_si_duan 取 dayun_line_index 时只按虚岁命中段、
    不辨 phase，致**先天段行至上爻误触上极条**，而该条触发语写死
    「后天运程行至上爻」——标签与事实相反。本类锁死该边界。
    """

    def test_xiantian_five_no_shangji(self):
        """先天段行上爻（li=5）不得出上极条。"""
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=5, dayun_phase="先天")
        self.assertFalse(any("上极" in x for x in w), w)

    def test_xiantian_four_no_junyao(self):
        """先天段行君爻（li=4）不得出君爻条。"""
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=4, dayun_phase="先天")
        self.assertFalse(any("君爻" in x for x in w), w)

    def test_xiantian_four_no_shishiba(self):
        """先天段行君爻不得出「过了第四爻，十死八九」。"""
        bad = [{"year": 2020, "hexagram": "否",
                "ci": "否之匪人，不利君子贞。凶", "buye": "", "suiyun": ""}]
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=4, dayun_phase="先天", recent_years=bad)
        self.assertFalse(any("十死八九" in x for x in w), w)

    def test_xiantian_four_no_dingsi(self):
        """先天段行君爻不得出「小象大象反对，定死无疑」。"""
        w = judge_si_duan(prenatal_name="泰", postnatal_name="大畜",
                          dayun_line_index=4, dayun_phase="先天",
                          recent_years=[{"year": 2020, "hexagram": "否",
                                         "ci": "否之匪人，不利君子贞。凶",
                                         "buye": "", "suiyun": ""}])
        self.assertFalse(any("定死" in x for x in w), w)

    def test_missing_phase_is_silent_not_houtian(self):
        """漏传 dayun_phase（默认空串）不得默认按后天立断。

        宁可沉默，也不得替原典补一条它没有的先天死断。
        """
        w4 = judge_si_duan(prenatal_name="比", postnatal_name="解", dayun_line_index=4)
        self.assertFalse(any("君爻" in x for x in w4), w4)
        w5 = judge_si_duan(prenatal_name="比", postnatal_name="解", dayun_line_index=5)
        self.assertFalse(any("上极" in x for x in w5), w5)

    def test_houtian_still_fires(self):
        """阳性对照：后天段 li=5 仍须出上极条（门控不得写死）。"""
        w = judge_si_duan(prenatal_name="比", postnatal_name="解",
                          dayun_line_index=5, dayun_phase="后天")
        self.assertTrue(any("上极" in x for x in w), w)
        w4 = judge_si_duan(prenatal_name="比", postnatal_name="解",
                           dayun_line_index=4, dayun_phase="后天")
        self.assertTrue(any("君爻" in x for x in w4), w4)


class TestSiDuanPhaseWiringEndToEnd(unittest.TestCase):
    """端到端：案例 A（仓库既有基线案例）虚岁44 落先天 37-45 上爻，
    不得出上极死断条，且引擎须确实把 phase 传到底。

    这是本次修复的**原始触发场景**——case_demo 的案例 A
    （1983-11-03 午时男，2026 流年虚岁44）正是靠它暴露出的标签反相。
    """

    @classmethod
    def setUpClass(cls):
        import sxtwl
        from heluo_engine.engines.heluo.canonical import HeluoCanonical
        from heluo_engine.engines.heluo.guajie import build_guajie_from_result
        gan = "甲乙丙丁戊己庚辛壬癸"
        zhi = "子丑寅卯辰巳午未申酉戌亥"
        day = sxtwl.fromSolar(1983, 11, 3)
        bz = [(gan[g.tg], zhi[g.dz]) for g in
              (day.getYearGZ(), day.getMonthGZ(), day.getDayGZ(), day.getHourGZ(12))]
        r = HeluoCanonical().calculate(
            bazi=bz, gender="male", birth_hour="午", era="zhong",
            birth_year=1983, birth_date="1983-11-03")
        cls.bz = bz
        cls.dayun = (r.timeline.qi_phase or {}).get("dayun") or []
        cls.gj = build_guajie_from_result(
            r, bazi=bz, target_year=2026, target_month=7, target_day=5)

    def test_case_a_is_in_prenatal_shangji(self):
        """先确认本守卫的前提本身成立：虚岁44 确在先天段上爻。"""
        seg = [d for d in self.dayun
               if d.get("age_start") and d.get("age_end")
               and d["age_start"] <= 44 <= d["age_end"]]
        self.assertEqual(len(seg), 1, self.dayun)
        self.assertEqual(seg[0]["phase"], "先天")
        self.assertEqual(seg[0]["line_index"], 5)

    def test_case_a_no_shangji_si_duan(self):
        """案例 A 不得出上极/君爻死断条。"""
        joined = "\n".join(self.gj.get("si_duan") or [])
        self.assertFalse(any("上极" in x for x in (self.gj.get("si_duan") or [])), joined)
        self.assertFalse(any("触发：后天运程行至五爻" in x
                             for x in (self.gj.get("si_duan") or [])), joined)

    def test_case_a_phase_key_present_in_dayun(self):
        """qi_phase.dayun 必须带 phase，否则门控无从判起。"""
        for d in self.dayun:
            self.assertIn("phase", d, d)
            self.assertIn(d["phase"], ("先天", "后天"), d)


class TestYuantangPureGuaZhengwen(unittest.TestCase):
    """乾坤纯卦元堂「正文」锚点（起例卷之上 L297 / L300）

    原典正文：
      「假令男得乾卦纯阳，不问阴阳，但十二时皆自下而行上，**子午皆在初爻**。
        如女得乾卦，生冬至以后，至夏至以前，**自上九为始，往下行至初爻**。
        若生夏至以后，至冬至以前，当**自初九为始，往上行至上九**。」
      「假令女得坤卦，不问阴阳，但十二时皆自下而上，**子午皆在初爻**，如上例。
        如男得坤卦，生冬至以后，夏至以前，**自上六行至初六**，
        夏至以后，冬至以前，当**自下而上行**。」

    落表（爻位 0=初 … 5=上），子丑寅卯辰巳午未申酉戌亥：
      自下而上 = h % 6      子(0)→初爻、午(6)→初爻  ← 正文「子午皆在初爻」
      自上而下 = (5-h) % 6  子(0)→上爻、午(6)→上爻

    交叉验证（L318 同节）：
      「十一月冬至生，元堂居初九为顺时」——男得乾冬，子时 → 初爻 ✓
      「如坤卦夏至生，居初六爻」          ——女得坤夏，子时 → 初爻 ✓

    「又一本云」重数版（L306-315）**不采**：明标他本、编者自评「宜更详之」、
    无冬夏分支、且其自身男乾「午酉三爻」与女坤「午酉四爻」同配置而异说。
    2026-10-07 早前据该版立的「重数全表」已推翻，见
    heluo_engine/docs/纯卦元堂重数规则定案_20261007.md 更正块。
    """

    # (标签, 六爻, 性别)  —— 冬半年
    CASES = [
        ('男乾', [1] * 6, 'male'),
        ('女乾', [1] * 6, 'female'),
        ('女坤', [-1] * 6, 'female'),
        ('男坤', [-1] * 6, 'male'),
    ]

    # 冬半年全表（爻位 0=初 … 5=上），子丑寅卯辰巳午未申酉戌亥
    WINTER_TABLE = {
        '男乾': (0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5),   # 自下而行上
        '女乾': (5, 4, 3, 2, 1, 0, 5, 4, 3, 2, 1, 0),   # 自上九为始往下行
        '女坤': (0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5),   # 自下而上，如上例
        '男坤': (5, 4, 3, 2, 1, 0, 5, 4, 3, 2, 1, 0),   # 自上六行至初六
    }

    # 夏半年全表：女乾「自初九为始，往上行至上九」、男坤「当自下而上行」
    SUMMER_TABLE = {
        '男乾': (0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5),
        '女乾': (0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5),
        '女坤': (0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5),
        '男坤': (0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5),
    }

    def _idx(self, lines, gender, hour, phase='winter'):
        y = find_yuantang(six_lines=lines, birth_hour=hour, gender=gender,
                          xiantian_name='乾', solar_phase=phase)
        return y.yuantang_index

    def _table(self, lines_of, gender_of, phase):
        return {label: tuple(self._idx(lines_of[label], gender_of[label], h, phase)
                             for h in HOUR_NAMES)
                for label in lines_of}

    @property
    def _lines_of(self):
        return {label: lines for label, lines, _ in self.CASES}

    @property
    def _gender_of(self):
        return {label: g for label, _, g in self.CASES}

    # ── 正文两条硬锚点 ────────────────────────────────────────────
    def test_anchor_ziwu_both_in_first_yao(self):
        """正文「子午皆在初爻」——男得乾、女得坤，十二时自下而上，子午皆 0。"""
        for label in ('男乾', '女坤'):
            zi = self._idx(self._lines_of[label], self._gender_of[label], '子')
            wu = self._idx(self._lines_of[label], self._gender_of[label], '午')
            self.assertEqual(zi, 0, f'{label} 子时应在初爻，实得 {zi}')
            self.assertEqual(wu, 0, f'{label} 午时应在初爻，实得 {wu}')

    def test_anchor_winter_starts_from_top_yao(self):
        """正文「自上九为始」「自上六行」——女乾/男坤冬半年子时皆在上爻。"""
        for label in ('女乾', '男坤'):
            zi = self._idx(self._lines_of[label], self._gender_of[label], '子', 'winter')
            self.assertEqual(zi, 5, f'{label} 冬半年子时应起上爻，实得 {zi}')

    def test_anchor_summer_starts_from_first_yao(self):
        """正文「自初九为始」「当自下而上行」——夏半年子时皆在初爻。"""
        for label in ('女乾', '男坤'):
            zi = self._idx(self._lines_of[label], self._gender_of[label], '子', 'summer')
            self.assertEqual(zi, 0, f'{label} 夏半年子时应起初爻，实得 {zi}')

    # ── 全表钉死 ──────────────────────────────────────────────────
    def test_winter_full_table_twelve_hours(self):
        got = self._table(self._lines_of, self._gender_of, 'winter')
        for label, want in self.WINTER_TABLE.items():
            self.assertEqual(got[label], want, f'{label} 冬半年十二时全表不符')

    def test_summer_full_table_twelve_hours(self):
        got = self._table(self._lines_of, self._gender_of, 'summer')
        for label, want in self.SUMMER_TABLE.items():
            self.assertEqual(got[label], want, f'{label} 夏半年十二时全表不符')

    def test_summer_all_four_configurations_identical(self):
        """夏半年四条皆「自初爻为始往上行」，故四配置全表必然相同——
        这是正文四条的直接推论，若实现再分叉（如保留「重数」）此断言即红。"""
        got = self._table(self._lines_of, self._gender_of, 'summer')
        vals = set(got.values())
        self.assertEqual(len(vals), 1,
                         f'夏半年四配置落表竟不一致（重数版残留？）：{got}')

    def test_none_phase_behaves_as_winter(self):
        """未给节气时按冬半年处理（向后兼容），且明文「不抛错、不返 None」。"""
        for label, lines, gender in self.CASES:
            no_phase = tuple(find_yuantang(
                six_lines=lines, birth_hour=h, gender=gender,
                xiantian_name='乾').yuantang_index for h in HOUR_NAMES)
            self.assertEqual(no_phase, self.WINTER_TABLE[label],
                             f'{label} 未给节气时应等同冬半年')
            for h in HOUR_NAMES:
                v = self._idx(lines, gender, h)
                self.assertIsInstance(v, int)
                self.assertIn(v, range(6), f'{label} {h}时落点越界：{v}')

    def test_each_yao_counted_twice(self):
        """十二时配六爻、逐时推移，两轮走完 → 每一爻恰 2 次。"""
        for phase in ('winter', 'summer'):
            got = self._table(self._lines_of, self._gender_of, phase)
            for label, tbl in got.items():
                counts = [0] * 6
                for v in tbl:
                    counts[v] += 1
                self.assertEqual(counts, [2, 2, 2, 2, 2, 2],
                                 f'{label}（{phase}）各爻计数应为 2，实得 {counts}')

    def test_step_is_always_one_yao(self):
        """「皆自下而行上」「往下行至初爻」——逐时相邻爻位恰差 1 爻。

        第六时→第七时（巳→午）为一轮走完后的回绕（末爻回首爻），属同一循环，
        故差值 5（= -1 mod 6）亦算相邻。**恰好 6→0 这一处必须回绕**，
        因为「十二时配六爻」必然走两轮。
        """
        for phase in ('winter', 'summer'):
            got = self._table(self._lines_of, self._gender_of, phase)
            for label, tbl in got.items():
                for i in range(6):
                    d = abs(tbl[i + 1] - tbl[i])
                    self.assertIn(d, (1, 5),
                                  f'{label}（{phase}）{HOUR_NAMES[i]}→'
                                  f'{HOUR_NAMES[i + 1]} 未相邻：{tbl[i]}→{tbl[i + 1]}')
                # 一轮走完必回绕一次，且只此一次
                wraps = [i for i in range(6) if abs(tbl[i + 1] - tbl[i]) == 5]
                self.assertEqual(wraps, [5],
                                 f'{label}（{phase}）回绕点应恰在巳→午，实得 {wraps}')


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
