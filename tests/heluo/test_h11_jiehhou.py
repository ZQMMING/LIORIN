"""H11: 节候卦计算测试

覆盖：24节气节候卦映射、动爻位置、原典一致性
原典依据：《河洛真数》起例卷下·定节候卦说
"""
from __future__ import annotations

import unittest
import inspect
import sys
import types
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.jiehhou import (
    SOLAR_TERMS,
    JIEHOU_GUA,
    JIEHOU_GUA_NAME,
    get_seasonal_hexagram,
    get_qi_phase,
    get_current_jieqi_info,
    SeasonalHexagram,
)


class TestSolarTerms(unittest.TestCase):
    """24节气名称顺序验证"""

    def test_24_terms_count(self):
        self.assertEqual(len(SOLAR_TERMS), 24)

    def test_24_terms_order(self):
        expected = [
            "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
            "春分", "清明", "谷雨", "立夏", "小满", "芒种",
            "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
            "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
        ]
        # 2026-10-08 批次 G：SOLAR_TERMS 改为引用 jiegua.JIEQI_24（单一来源），
        # 后者是 tuple，故此处比 list(...)；下面的 test 是「确为同一对象」的断言。
        self.assertEqual(list(SOLAR_TERMS), expected)

    def test_solar_terms_is_the_single_source_object(self):
        """二十四节气序全库只许有一处定义。

        批次 G 之前此处、jiegua.JIEQI_24、yue_ling_shu_ge.JIE_QI_ORDER 各抄一份。
        三份各改各的，索引错位要到出卦时才炸——故钉住「必须是同一个对象」。
        """
        from heluo_engine.engines.heluo.jiegua import JIEQI_24
        from heluo_engine.engines.heluo.yue_ling_shu_ge import JIE_QI_ORDER
        self.assertIs(SOLAR_TERMS, JIEQI_24, "SOLAR_TERMS 与 jiegua.JIEQI_24 不是同一对象")
        self.assertIs(JIE_QI_ORDER, JIEQI_24, "JIE_QI_ORDER 与 jiegua.JIEQI_24 不是同一对象")


class TestSeasonalHexagram(unittest.TestCase):
    """节候卦映射验证"""

    def test_all_24_coverage(self):
        """24节气全覆盖，无缺失"""
        for i in range(24):
            info = get_seasonal_hexagram(i)
            self.assertEqual(info.jq_name, SOLAR_TERMS[i])
            self.assertIn(info.main_gua, JIEHOU_GUA_NAME.values())

    def test_dongzhi_yi_fu(self):
        """冬至：坎初六（原典 L1492「节卦坎初六起冬至」）"""
        info = get_seasonal_hexagram(0)
        self.assertEqual(info.jq_name, "冬至")
        self.assertEqual(info.main_gua, "坎")
        self.assertEqual(info.moving_line, 0)
        self.assertEqual(info.result_gua, "初六")

    def test_lichun_jie(self):
        """立春：坎六四（原典「六四立春」，坎卦第四爻）"""
        info = get_seasonal_hexagram(3)
        self.assertEqual(info.main_gua, "坎")
        self.assertEqual(info.moving_line, 3)
        self.assertEqual(info.result_gua, "六四")

    def test_chunfen_duogua(self):
        """春分：震初九（原典「震初九起春分」）"""
        info = get_seasonal_hexagram(6)
        self.assertEqual(info.main_gua, "震")
        self.assertEqual(info.moving_line, 0)
        self.assertEqual(info.result_gua, "初九")

    def test_xiazhi_shi_pou(self):
        """夏至：离初九（原典「离初九起夏至」）"""
        info = get_seasonal_hexagram(12)
        self.assertEqual(info.main_gua, "离")
        self.assertEqual(info.moving_line, 0)
        self.assertEqual(info.result_gua, "初九")

    def test_qiufen_dun(self):
        """秋分：兑初九（原典「兑初九起秋分」）"""
        info = get_seasonal_hexagram(18)
        self.assertEqual(info.main_gua, "兑")
        self.assertEqual(info.moving_line, 0)
        self.assertEqual(info.result_gua, "初九")

    def test_invalid_index_raises(self):
        """越界应抛出 ValueError"""
        with self.assertRaises(ValueError):
            get_seasonal_hexagram(-1)
        with self.assertRaises(ValueError):
            get_seasonal_hexagram(24)

    def test_evidence_chain(self):
        """证据链包含原典引用"""
        info = get_seasonal_hexagram(0)
        self.assertTrue(any("河洛真数" in e for e in info.evidence))


class TestQiPhase(unittest.TestCase):
    """卦气阶段测试"""

    def test_sizheng_gua(self):
        """四正卦分管的节气（冬至/春分/夏至/秋分）"""
        sizheng_indices = {0, 6, 12, 18}
        for i in sizheng_indices:
            phase = get_qi_phase(2026, i)
            self.assertTrue(phase.is_sizheng)
            self.assertFalse(phase.six_day_seven_method)

    def test_bi_gua_monthly(self):
        """辟卦月份对应的节气"""
        li_chun = get_qi_phase(2026, 3)
        self.assertTrue(li_chun.is_bi_gua)

    def test_six_day_seven(self):
        """非四正卦节气适用六日七分法"""
        phase = get_qi_phase(2026, 1)  # 小寒
        self.assertTrue(phase.six_day_seven_method)


class TestCurrentJieqiInfo(unittest.TestCase):
    """当前节气查询测试"""

    def test_known_date(self):
        """2026年9月4日应有节候信息（白露附近）"""
        info = get_current_jieqi_info(2026, 9, 4)
        # 可能为None（若sxtwl未加载），不强制断言
        if info is not None:
            self.assertIn(info.jq_name, SOLAR_TERMS)
            self.assertIsInstance(info, SeasonalHexagram)


class TestCurrentJieqiInfoErrorSemantics(unittest.TestCase):
    """2026-10-06 回归：get_current_jieqi_info 只把「缺依赖」降级为 None。

    旧实现带 `except Exception: return None`，函数内任何真实计算错误都被吞成
    None，调用方无法区分「没装 sxtwl」与「算错了」。现只捕 ImportError。
    """

    def test_missing_sxtwl_returns_none(self):
        """sxtwl 不可用 → None（降级路径保留，且不依赖本机是否装了 sxtwl）"""
        with mock.patch.dict(sys.modules, {"sxtwl": None}):
            self.assertIsNone(get_current_jieqi_info(2026, 9, 4))

    def test_real_error_propagates(self):
        """sxtwl 已装但计算出错 → 异常原样上抛，不得吞成 None"""
        boom = RuntimeError("sxtwl boom")
        fake = types.ModuleType("sxtwl")

        def _fromSolar(*_a, **_kw):
            raise boom

        fake.fromSolar = _fromSolar
        with mock.patch.dict(sys.modules, {"sxtwl": fake}):
            with self.assertRaises(RuntimeError) as ctx:
                get_current_jieqi_info(2026, 9, 4)
        self.assertIs(ctx.exception, boom, "应原样上抛，不被降级吞掉")

    def test_no_bare_exception_fallback(self):
        """源码级护栏：函数体内不得再出现 except Exception 降级"""
        src = inspect.getsource(get_current_jieqi_info)
        self.assertNotIn(
            "except Exception", src,
            "get_current_jieqi_info 不应再用 except Exception 吞真实计算错误",
        )

    def test_jq_index_out_of_range_returns_none(self):
        """非错误情形：jq_idx 越界仍返回 None，不上抛"""
        fake = types.ModuleType("sxtwl")

        class _Day:
            def getJieQi(self):
                return -1

        fake.fromSolar = lambda *a, **kw: _Day()
        with mock.patch.dict(sys.modules, {"sxtwl": fake}):
            self.assertIsNone(get_current_jieqi_info(2026, 9, 4))

    def test_valid_path_returns_hexagram(self):
        """正常路径：合法 jq_idx 应返回 SeasonalHexagram"""
        fake = types.ModuleType("sxtwl")

        class _Day:
            def getJieQi(self):
                return 16  # 处暑

        fake.fromSolar = lambda *a, **kw: _Day()
        with mock.patch.dict(sys.modules, {"sxtwl": fake}):
            info = get_current_jieqi_info(2026, 9, 4)
        self.assertIsInstance(info, SeasonalHexagram)
        self.assertEqual(info.jq_name, "处暑")
        self.assertEqual(info.jq_index, 16)


class TestJiehhouDataIntegrity(unittest.TestCase):
    """节候卦数据完整性"""

    def test_jiehou_gua_dict_has_24_entries(self):
        self.assertEqual(len(JIEHOU_GUA), 24)

    def test_jiehou_gua_name_matches(self):
        """JIEHOU_GUA_NAME 与 JIEHOU_GUA 一致"""
        for idx, (main, _, _) in JIEHOU_GUA.items():
            self.assertEqual(JIEHOU_GUA_NAME[idx], main)


if __name__ == "__main__":
    unittest.main()
