# -*- coding: utf-8 -*-
r"""守卫：**降级路径的产出契约**（2026-10-26 新增）。

为什么要有这个文件
------------------
2026-10-26 的变异扫描（修好扫描器之后）报出 **21 条真盲区**，
逐条看下来，它们**几乎全部**落在两类代码上：

  ① **归一化 / 格式化辅助函数**（`_plain` / `_yao_name` / `_gua_full_name` …）
  ② **降级 / 兜底分支**（"取不到时退化成什么"）

⇒ 而仓里原有的降级守卫（``test_heluo_degradation_contracts.py``）管的是
  「**失败时不崩 + 必须留痕**」，**没有**管「**降级后产出什么**」。
  ⇒ 于是这些分支的行为改了，**没有任何守卫会红**。

⚠ 这直接违背本项目的核心纪律：
  「**缺失被当成正常，比答错更坏**」——
  降级路径的产出（"取不到时给什么"）恰恰是**最不该没人管**的地方。

⚠ 本文件的写法纪律
------------------
每条断言都必须表达**真实的业务契约**（"取不到时必须退化成 X"），
**不是**"这行代码不是 None"那种**为杀变异而写**的假守卫。
⇒ 断言里写清**为什么**（原典 / 模块语义 / 数据流），让后来者能判断
   契约是否仍然成立。

本文件覆盖的 21 条真盲区（模块 → 行）：
    time_layer_judgment.py  8 条（L264 L274 L294 L373 L375 L388 L408 L419）
    interpretation_pipeline.py  4 条（L68 L71 L91 L98）
    metrics_v2.py           2 条（L347 L382）
    calendar_guard.py       2 条（L230 L294）
    canonical.py            1 条（L114）
    canonical_signals.py    1 条（L65）
    diagnosis_rule_graph.py 1 条（L701）
    dimensions.py           1 条（L310）
    interpretation.py       1 条（L702）
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from heluo_engine.engines.heluo import calendar_guard as cg          # noqa: E402
from heluo_engine.engines.heluo import canonical_signals as cs        # noqa: E402
from heluo_engine.engines.heluo import diagnosis_rule_graph as drg   # noqa: E402
from heluo_engine.engines.heluo import dimensions as dims             # noqa: E402
from heluo_engine.engines.heluo import interpretation_pipeline as ip  # noqa: E402
from heluo_engine.engines.heluo import metrics_v2 as mv2              # noqa: E402
from heluo_engine.engines.heluo import time_layer_judgment as tlj     # noqa: E402


# ══════════════════════════════════════════════════════════════
# ① 时间层：卦级判据的**样本**与**兜底来源**
# ══════════════════════════════════════════════════════════════


class TestTimeLayerSampleContract(unittest.TestCase):
    """时间层判据（流年/流月/流日）的**数据来源**契约。

    背景：L212「卦爻中有元吉亨利是也」是**卦级**判据 ⇒ 样本必须是
    **该卦的六爻爻辞**。若六爻取不到而退化成单爻，判法就变了。
    """

    def test_gua_ci_list_returns_empty_when_no_hexagram_name(self):
        """取不到卦名 ⇒ 必须返回**空列表**（不是 None、不是非空）。"""
        for guajie, name in ((None, ""), ({}, ""), ({"x": 1}, "  ")):
            with self.subTest(guajie=type(guajie).__name__):
                out = tlj._gua_ci_list(guajie, name)
                self.assertEqual(out, [],
                                 "取不到卦名时必须返回空列表（调用方据此退化为单爻）")

    def test_gua_ci_list_returns_six_yao_ci(self):
        """★ 取到卦名 ⇒ 必须返回**该卦的六爻爻辞**（L212「卦爻中」的样本）。

        ⚠ 这条最要紧：若被吞成 None ⇒ 判据从**卦级**退化为**单爻**
        ⇒ 原典 L212 的判法被悄悄破坏，而没有任何守卫会红。
        """
        from heluo_engine.engines.heluo.guajie import load_guajie_data
        data = load_guajie_data()
        self.assertTrue(data, "判词数据为空，无法验证卦级样本")
        # 挑一个卦名，其六爻爻辞齐备
        picked = None
        for gua, g in data.items():
            yaos = getattr(g, "yaos", None) or {}
            values = list(yaos.values()) if isinstance(yaos, dict) else list(yaos)
            cis = [getattr(y, "ci", "") or "" for y in values]
            if len(cis) == 6 and all(cis):
                picked = gua
                break
        self.assertIsNotNone(picked, "判词数据里找不到六爻齐备的卦，无法验证")
        out = tlj._gua_ci_list(None, picked)
        self.assertEqual(len(out), 6,
                         "卦级样本必须是**六**爻爻辞，实得 %d 条（%s）"
                         % (len(out), picked))
        self.assertTrue(all(isinstance(c, str) and c for c in out),
                        "卦级样本里有空爻辞")

    def test_hexagram_from_guajie_returns_plain_string(self):
        """判词层给的是**字符串**卦名时 ⇒ 原样取出（不得丢）。"""
        out = tlj._hexagram_from_guajie({"liunian_hexagram": "观"},
                                        "liunian_hexagram")
        self.assertEqual(out, "观", "字符串卦名须原样取出")


class TestTimeLayerFallbackSource(unittest.TestCase):
    """时间层的**兜底来源**：判词层没有时，必须从 ``timeline`` 取。"""

    class _FakeTimeline:
        def __init__(self):
            self.target_year_hexagram = 2026
            self.yearly_hexagrams = [{
                "year": 2026,
                "hexagram": "巽为风",
                "xingnian_yao_index": 3,
                "dayun_seg_yuantang_index": 2,
                "months": [{"month": 6, "name": "坤为地",
                            "yue_yao_index": 1}],
            }]
            self.daily_hexagram = {
                "month": 6,
                "base_hex": {"name": "坎为水"},
            }

    class _FakeResult:
        """判词层**完全没有**时间层信息 ⇒ 逼引擎走 timeline 兜底。"""

        def __init__(self):
            self.guajie = {}
            self.timeline = TestTimeLayerFallbackSource._FakeTimeline()

    def test_falls_back_to_timeline_for_year_month_day(self):
        """★ 判词层缺时间层数据 ⇒ 流年/流月/流日**必须**从 timeline 取到。

        ⚠ 若兜底分支的判据被改（``if not y_gua`` 写反等）⇒
        判定的 hexagram/yao 会变空 ⇒ 时间层**整层判不出来**，
        而原典 L121-L122 明言流年之吉凶**重于**大象 ⇒ 丢不得。
        """
        res = self._FakeResult()
        js = tlj.collect_time_layer_judgments(res)
        self.assertEqual(len(js), 3, "必须产出流年/流月/流日三层")
        by_rule = {j.rule_id: j for j in js}
        self.assertEqual(by_rule["HL_LIUNIAN_GUA"].hexagram, "巽为风",
                         "流年卦未从 timeline 兜底取到")
        self.assertEqual(by_rule["HL_LIUNIAN_GUA"].yao, "四爻",
                         "流年行年爻未从 timeline 兜底取到")
        self.assertEqual(by_rule["HL_YUEGUA"].hexagram, "坤为地",
                         "流月卦未从 timeline 兜底取到")
        self.assertEqual(by_rule["HL_YUEGUA"].yao, "二爻",
                         "流月爻未从 timeline 兜底取到")
        self.assertEqual(by_rule["HL_RIGUA"].hexagram, "坎为水",
                         "流日卦未从 timeline 兜底取到")

    def test_collect_returns_three_layers_in_order(self):
        """collect 必须按 **流年 → 流月 → 流日** 顺序产出三层。"""
        from heluo_engine.adapter import HeluoAdapter
        res = HeluoAdapter().compute((1983, 11, 3, 12), gender="male",
                                      target_date="2026-10-23")
        js = tlj.collect_time_layer_judgments(res)
        self.assertEqual([j.rule_id for j in js],
                         ["HL_LIUNIAN_GUA", "HL_YUEGUA", "HL_RIGUA"],
                         "时间层三层顺序/构成被改（下游按序取用）")


# ══════════════════════════════════════════════════════════════
# ② 解读层：归一化辅助函数
# ══════════════════════════════════════════════════════════════


class TestInterpretationNormalisationContract(unittest.TestCase):
    """解读层的归一化辅助函数：形态必须稳定。"""

    def test_plain_converts_dict_recursively(self):
        """dict ⇒ 递归转成**纯 Python** 形态（可 JSON 序列化）。"""
        import dataclasses

        @dataclasses.dataclass
        class _D:
            a: int = 1

        out = ip._plain({"k": _D(), "l": [_D()]})
        self.assertIsInstance(out, dict)
        self.assertIsInstance(out["k"], dict)
        self.assertIsInstance(out["l"], list)
        self.assertIsInstance(out["l"][0], dict)

    def test_plain_does_not_expand_a_class_object(self):
        """⚠ **类对象**（type）不得被展开成 dataclass 的**字段默认值**。

        契约依据（本项目纪律「**不造值**」「缺失被当成正常，比答错更坏」）：
        dataclass 的字段默认值是写在**类**上的 ⇒ 展开类对象等于
        **凭空造出一份"看起来像真实数据"的值**（那不是任何实例的数据）。

        ⚠ 2026-10-26：变异扫描抓到这条（`_plain(_D)` 曾返回 `{'a': 1, 'b': 'x'}`）
        —— 原实现只在 dataclass 分支挡了类对象，后面的 ``__dict__`` 分支照样展开。
        ⇒ 现已把类对象排除提到最前面；本守卫钉住该契约。
        """
        import dataclasses

        @dataclasses.dataclass
        class _D:
            a: int = 1
            b: str = "x"

        out = ip._plain(_D)
        self.assertNotIsInstance(
            out, dict,
            "类对象被展开成 dict（会造出字段默认值）")
        self.assertIsInstance(out, str)
        # 反向确认：实例仍要正常展开（不能为了防类而误伤实例）
        inst = ip._plain(_D())
        self.assertIsInstance(inst, dict)
        self.assertEqual(inst.get("a"), 1)

    def test_yao_name_maps_index_to_name(self):
        """爻位下标 0..5 ⇒ 爻位名；越界/非法 ⇒ 空串。"""
        for i in range(6):
            with self.subTest(index=i):
                self.assertTrue(ip._yao_name(i).strip(),
                                "爻位 %d 应当有爻名" % i)
        for bad in (-1, 6, 99, None, "x"):
            with self.subTest(bad=bad):
                self.assertEqual(ip._yao_name(bad), "",
                                 "越界/非法下标必须返回空串")

    def test_gua_full_name_format(self):
        """上下卦 ⇒ 「X上Y下」；缺一 ⇒ 空串。"""
        self.assertEqual(ip._gua_full_name("坎", "巽"), "坎上巽下")
        self.assertEqual(ip._gua_full_name("坎", ""), "")
        self.assertEqual(ip._gua_full_name("", "巽"), "")


# ══════════════════════════════════════════════════════════════
# ③ 判据层：兜底取值
# ══════════════════════════════════════════════════════════════


class TestCanonicalSeasonFallback(unittest.TestCase):
    """元堂半年相：夏至后至冬至前 ⇒ ``summer``。"""

    def test_summer_half_year_is_summer(self):
        """夏至后（且冬至前）的出生日 ⇒ ``summer``（原典 p051-052）。"""
        from heluo_engine.engines.heluo.canonical import _solar_phase_for_date
        for d in ("2026-07-15", "2026-08-20", "2026-10-01"):
            with self.subTest(date=d):
                self.assertEqual(_solar_phase_for_date(d), "summer",
                                 "%s 属夏半年，应判 summer" % d)

    def test_winter_half_year_is_winter(self):
        """冬至后（且夏至前）⇒ ``winter``。"""
        from heluo_engine.engines.heluo.canonical import _solar_phase_for_date
        for d in ("2026-01-15", "2026-03-20", "2026-12-25"):
            with self.subTest(date=d):
                self.assertEqual(_solar_phase_for_date(d), "winter",
                                 "%s 属冬半年，应判 winter" % d)


class TestSignalDomainFallback(unittest.TestCase):
    """诊断领域：方向非正非负 ⇒ ``FAMILY``。"""

    def test_unknown_direction_maps_to_family(self):
        self.assertEqual(drg._sig_domain("UNKNOWN"), "FAMILY")
        self.assertEqual(drg._sig_domain(""), "FAMILY")

    def test_positive_negative_map_to_known_domains(self):
        self.assertEqual(drg._sig_domain("POSITIVE"), "CAREER")
        self.assertEqual(drg._sig_domain("NEGATIVE"), "LIFE_EVENT")


class TestYaoIndexContract(unittest.TestCase):
    """爻名 → 爻位序号 1..6。"""

    def test_known_yao_names(self):
        for name, idx in (("初九", 1), ("初六", 1), ("九二", 2), ("六三", 3),
                          ("九四", 4), ("六五", 5), ("上九", 6), ("上六", 6)):
            with self.subTest(name=name):
                self.assertEqual(cs._yao_index(name), idx,
                                 "%s 的爻位序号错了" % name)

    def test_empty_name_returns_zero(self):
        self.assertEqual(cs._yao_index(""), 0)


class TestDirectionPrecedenceContract(unittest.TestCase):
    """★ 方向判定：只有 UNKNOWN 时才给 UNKNOWN；有正/负时**不得被 UNKNOWN 覆盖**。

    契约依据：命中列表里同时有 POSITIVE 与 UNKNOWN 时，
    **已判出方向**就应给该方向；UNKNOWN 只是"没判出方向"那一类
    （如「命中死断条 —— 原典为**条件式立断**，不得径取一支作方向」）。
    """

    def test_unknown_alone_gives_unknown(self):
        """只命中死断条（条件式立断）⇒ 不得径取方向 ⇒ UNKNOWN。"""
        out = dims.heluo_direction({"si_duan": {"text": "阴骘两支并陈"}})
        self.assertEqual(out[0], "UNKNOWN")

    def test_positive_wins_over_unknown(self):
        """★ 死断条 + 遇化工 ⇒ 给 POSITIVE（已判出方向就不该被 UNKNOWN 覆盖）。"""
        out = dims.heluo_direction({"si_duan": {"text": "阴骘两支并陈"},
                                    "hua_gong_hit": {"note": "遇化工"}})
        self.assertEqual(out[0], "POSITIVE",
                         "已判出 POSITIVE 时不得被 UNKNOWN 覆盖")

    def test_negative_wins_over_unknown(self):
        """死断条 + 数凶 ⇒ 给 NEGATIVE。"""
        out = dims.heluo_direction({"si_duan": {"text": "阴骘两支并陈"},
                                    "shu_xiong": {"shu_xiong": "数凶"}})
        self.assertEqual(out[0], "NEGATIVE",
                         "已判出 NEGATIVE 时不得被 UNKNOWN 覆盖")


# ══════════════════════════════════════════════════════════════
# ④ 度量层 / 历法层：兜底取值
# ══════════════════════════════════════════════════════════════


class TestMetricsFallbackContract(unittest.TestCase):
    """质量等级与建议：低分必须落到**兜底档**、低分必须给建议。"""

    def test_quality_level_thresholds(self):
        """质量等级按总分分档；低分必须落到 ``needs_review``（不能给好评）。"""
        self.assertEqual(mv2._get_quality_level(0.95), "excellent")
        self.assertEqual(mv2._get_quality_level(0.80), "good")
        self.assertEqual(mv2._get_quality_level(0.65), "acceptable")
        self.assertEqual(mv2._get_quality_level(0.10), "needs_review",
                         "低分必须落到 needs_review（不能给好评）")

    def test_low_score_must_produce_suggestions(self):
        out = mv2._generate_suggestions({}, 0.5)
        self.assertIsInstance(out, list, "建议必须是列表")
        self.assertTrue(out, "低分必须给出建议（空列表 = 无声放过）")


class TestBirthWindowFallback(unittest.TestCase):
    """出生时辰窗口：时辰不可用 ⇒ **整日窗口**（00:00 → 次日 00:00）。"""

    def test_missing_hour_uses_whole_day(self):
        from datetime import datetime
        for hour in (None, "", "不是时辰"):
            with self.subTest(hour=hour):
                w = cg._birth_window("1990-05-17", hour)
                self.assertIsNotNone(w)
                start, end = w
                self.assertEqual(start, datetime(1990, 5, 17))
                self.assertEqual((end - start).days, 1,
                                 "时辰不可用时必须是**整日**窗口")

    def test_valid_hour_uses_hour_window(self):
        from datetime import datetime
        w = cg._birth_window("1990-05-17", "午")
        self.assertIsNotNone(w)
        start, end = w
        self.assertEqual(start.date(), datetime(1990, 5, 17).date())
        self.assertLess((end - start).total_seconds(), 24 * 3600,
                        "合法时辰必须用**时辰**窗口（不是整日）")


class TestJieqiBeforeWindowContract(unittest.TestCase):
    """★ 出生是否确定早于某节气：三态（早 / 晚 / 不可判定）。

    契约依据：节气的**时刻**落在出生窗口内 ⇒ **不可判定**（None），
    不得偏向任一边（判错年柱 = 全盘错）。

    ⚠ ``_before`` 是 ``authoritative_year_month`` 内部的**嵌套函数**，
    不可直接调用 ⇒ 这里用 **AST 精确检查**它的三个 return 值
    （文本搜索会误伤别处的同名 return）。
    """

    def test_before_helper_keeps_three_state_logic(self):
        """★ 嵌套 ``_before`` 必须有三个分支：True / False / None。

        ⚠ 用 AST 定位到**那个具体的嵌套函数**再检查返回值
        ⇒ 「把 ``return True`` 改成 ``return None``」这类变异会被抓住
        （文本搜索 ``"return True"`` 会因别处也有而漏放）。
        """
        import ast
        import inspect
        src = inspect.getsource(cg.authoritative_year_month)
        tree = ast.parse(src)
        helpers = [n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_before"]
        self.assertEqual(len(helpers), 1,
                         "应恰好有一个嵌套 _before，实际 %d 个" % len(helpers))
        returns = []
        for node in ast.walk(helpers[0]):
            if isinstance(node, ast.Return) and node.value is not None:
                returns.append(ast.unparse(node.value))
        self.assertIn("True", returns,
                      "「确定早于」分支（return True）丢了：%r" % returns)
        self.assertIn("False", returns,
                      "「确定晚于」分支（return False）丢了：%r" % returns)
        self.assertIn("None", returns,
                      "「不可判定」分支（return None）丢了：%r" % returns)

    def test_jieqi_inside_window_is_undecidable(self):
        """节气时刻落在出生窗口**内** ⇒ 不可判定（None），不得偏向一边。"""
        w = cg._birth_window("2026-06-21", None)      # 整日窗口
        self.assertIsNotNone(w)
        w_start, w_end = w
        jd = cg._jieqi_datetime(2026, 12)              # 夏至
        self.assertIsNotNone(jd, "夏至时刻应可取到")
        if w_start < jd < w_end:
            # 复刻 _before 的判据：窗口内 ⇒ None
            self.assertFalse(jd >= w_end)
            self.assertFalse(jd <= w_start)
        else:
            self.assertTrue(jd >= w_end or jd <= w_start,
                            "节气在窗口外 ⇒ 必须能判早/晚")


class TestInterpretationSummaryContract(unittest.TestCase):
    """解读层的输入摘要：必须**列全**五个字段。"""

    def test_summarize_input_lists_all_fields(self):
        """★ 输入摘要必须含 卦/元堂/年/月/日 五个字段。

        ⚠ 缺一个字段，下游就少一条依据 ⇒ 摘要**残缺**却看不出来
        （本项目纪律：缺失被当成正常，比答错更坏）。
        """
        from heluo_engine.engines.heluo.interpretation import (
            HeluoInput, RelationalInterpretationEngine,
        )

        inp = HeluoInput(
            prenatal_hexagram="风地观", yuan_tang="六二",
            postnatal_hexagram="水风井", day_hexagram="坎为水",
            year_cycle="甲子", month_cycle="丙寅", day_cycle="戊辰",
            element_state={"木": 0.6},
            line_position={"初爻": 1}, time_state={"节令": "夏至"},
            da_yun_sequence=[], prenatal_lines=[1, 0, 1, 0, 1, 0],
        )
        engine = RelationalInterpretationEngine(inp)
        summary = engine._summarize_input()
        self.assertIsInstance(summary, dict, "输入摘要必须是 dict")
        for key in ("hexagram", "yuan_tang", "year", "month", "day"):
            self.assertIn(key, summary, "输入摘要缺字段 %r" % key)


if __name__ == "__main__":
    unittest.main()
