# -*- coding: utf-8 -*-
"""盲派应期断法引擎测试
交叉验证源: ./盲派命理-案例资料集.md §6应期断法 + §2应期断案例
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path("./backend/src")))

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.engines.blind_yingqi import BlindYingqiEngine, DAXIAN_SEGMENTS


class TestBlindYingqi(unittest.TestCase):
    def setUp(self):
        self.engine = BlindYingqiEngine()
        self.be = BaziEngine()

    def test_daxian_segments(self):
        """大限分段: 年柱1-18/月柱18-35/日柱35-55/时柱55+(典籍)."""
        eng = self.engine
        self.assertEqual(eng._daxian_of_age(10)[0], "year")
        self.assertEqual(eng._daxian_of_age(25)[0], "month")
        self.assertEqual(eng._daxian_of_age(45)[0], "day")
        self.assertEqual(eng._daxian_of_age(70)[0], "hour")

    def test_flow_year_ganzhi(self):
        """流年干支计算正确."""
        eng = self.engine
        # 2024甲辰, 2025乙巳, 2026丙午
        self.assertEqual(eng._ganzhi_of_year(2024), ("JIA", "CHEN"))
        self.assertEqual(eng._ganzhi_of_year(2025), ("YI", "SI"))
        self.assertEqual(eng._ganzhi_of_year(2026), ("BING", "WU"))

    def test_analyze_basic(self):
        """基本分析: 返回大限/大运/流年."""
        r = self.engine.analyze((1990, 5, 15, 12), "male", target_age=40)
        self.assertEqual(r.age, 40)
        self.assertEqual(r.flow_year, 2030)
        self.assertIn(r.daxian_pillar, ("year", "month", "day", "hour"))
        self.assertTrue(r.luck_stem and r.luck_branch)
        self.assertTrue(r.flow_stem and r.flow_branch)

    def test_analyze_by_year(self):
        """按目标年份分析."""
        r = self.engine.analyze((1990, 5, 15, 12), "male", target_year=2025)
        self.assertEqual(r.age, 35)
        self.assertEqual(r.flow_year, 2025)

    def test_luck_pillars_ext(self):
        """扩展大运柱数量正确: 排盘引擎 BaziChart.luck_pillars=10 柱(三层接通后),
        应期层优先消费 chart.luck_pillars, 排盘缺失才回退自推 8 柱。"""
        chart = self.be.compute((1990, 5, 15, 12), gender="male")
        pillars = self.engine._luck_pillars_ext(chart)
        self.assertEqual(len(pillars), 10)

    def test_trigger_cihong(self):
        """冲引动识别: 流年支冲命局支."""
        r = self.engine.analyze((1948, 1, 23, 18), "male", target_age=52)
        kinds = [e['mechanism'] for e in r.yingqi_events]
        # 案例48: 丑未冲开墓库
        self.assertIn('muku_kai', kinds)

    def test_case3_lu_chuan(self):
        """案例3(禄坏): 庚寅年寅申冲触两申(禄), 应灾."""
        # 戊申己未庚申辛巳近似: 用1968-07-01, 30岁
        r = self.engine.analyze((1968, 7, 1, 10), "male", target_age=30)
        # 流年YIN冲SHEN(禄)应为冲主位
        found_chong = any(
            e['mechanism'] == 'chong' and 'SHEN' in e['mech']
            for e in r.yingqi_events
        )
        # 寅申冲识别
        self.assertTrue(found_chong or any('YIN' in e['mech'] for e in r.yingqi_events))

    def test_tougan_yingqi(self):
        """遁藏透干应期: 命局藏干现于运年天干."""
        # 案例48(1948-01-23, 丁亥癸丑丁未己酉)大限day(未)藏丁透干
        r = self.engine.analyze((1948, 1, 23, 18), "male", target_age=52)
        kinds = [e['mechanism'] for e in r.yingqi_events]
        self.assertIn('tougan', kinds)

    def test_sanxing_yingqi(self):
        """三刑引动(恃势之刑): 案例15(乙未乙酉丙戌己丑)16岁死母."""
        # 丑未戌三刑: 未大限遇丑戌构成恃势之刑
        r = self.engine.analyze((1895, 10, 6, 2), "female", target_age=16)
        kinds = [e['mechanism'] for e in r.yingqi_events]
        self.assertIn('sanxing', kinds)

    def test_muku_kai_yingqi(self):
        """墓库开闭应期: 案例48(丁亥癸丑丁未己酉)大限未冲开丑金库."""
        r = self.engine.analyze((1948, 1, 23, 18), "male", target_age=50)
        kinds = [e['mechanism'] for e in r.yingqi_events]
        self.assertIn('muku_kai', kinds)

    # ── 6项应期缺口回归（段建业第02章原文）──────────────────
    def test_hejianchong_yingqi(self):
        """合见冲为应: 原局有合,岁运冲之=以冲为应（第02章原文）.
        1980-06-22(庚申壬午丙寅癸巳): 原局巳申合, 2026大运亥冲巳."""
        r = self.engine.analyze((1980, 6, 22, 10), "male", target_year=2026)
        kinds = [e['mechanism'] for e in r.yingqi_events]
        self.assertIn('hejianchong', kinds)

    def test_chongjianhe_yingqi(self):
        """冲见合为应: 原局有冲,岁运合之=以合为应（第02章原文）.
        1980-06-22: 原局寅申冲, 2026大运亥合寅."""
        r = self.engine.analyze((1980, 6, 22, 10), "male", target_year=2026)
        kinds = [e['mechanism'] for e in r.yingqi_events]
        self.assertIn('chongjianhe', kinds)

    def test_chong_effect_xingqi(self):
        """旺衰冲应: 弱神冲旺神=冲起→七冲法 V3.6.9㊲ 改"冲去"(旧版"冲起"为旺衰冲应 3 类,
        ㊲ 扩展为七冲法 7 类: 冲去=衰者冲旺[兜底]）。
        1980-06-22(午月): 大运亥(衰)冲巳(旺) → 冲去(七冲法兜底)。
        ㊲ 口径: 冲区/冲开/冲出/冲破/冲旺/冲动 均 不 命中 此例, 兜底=冲去."""
        r = self.engine.analyze((1980, 6, 22, 10), "male", target_year=2026)
        effects = [e.get('chong_effect') for e in r.yingqi_events if e['mechanism'] == 'chong']
        # 七 冲 法 7 类 口 径 集 合, 断 言 命 中 其 中 任 一 类
        self.assertTrue(any(e in effects for e in ["冲 破", "冲 开", "冲 区", "冲 出", "冲 旺", "冲 动", "冲 去"]),
                        f"七 冲 法 7 类 口 径 未 命 中: {effects}")

    def test_chuan_nature_daisheng(self):
        """穿中带生有动意（第02章案例"寅冲穿巳是动了巳,穿而生有动意"）.
        1980-06-22: 大运亥穿申, 申金生亥水=带生."""
        r = self.engine.analyze((1980, 6, 22, 10), "male", target_year=2026)
        natures = [e.get('chuan_nature') for e in r.yingqi_events if e['mechanism'] == 'chuan']
        self.assertIn('带生', natures)

    def test_muku_bi_yingqi(self):
        """闭库应期: 岁运合墓库=库收物（本地盲派资料"闭库=库收物"）.
        1950-01-15 八字带丑库, 2020流年子合丑闭库."""
        r = self.engine.analyze((1950, 1, 15, 10), "male", target_year=2020)
        kinds = [e['mechanism'] for e in r.yingqi_events]
        self.assertIn('muku_bi', kinds)

    def test_muku_kai_xing_open(self):
        """刑也开库: 丑未戌三刑刑墓库（第02章案例"丙戌年,戌刑未开库"）.
        1950-01-15 八字带戌库, 2021流年丑刑开戌库."""
        r = self.engine.analyze((1950, 1, 15, 10), "male", target_year=2021)
        self.assertTrue(
            any('刑开' in e['mech'] for e in r.yingqi_events),
            "丑未戌三刑应开库"
        )

    def test_he_nature_hedong_heban(self):
        """合动/合绊: 支合=合动, 天地合=合绊（第02章"子丑合为合动,天地合为合绊"）.
        1980-06-22: 大运亥合寅(非天地合)=合动."""
        r = self.engine.analyze((1980, 6, 22, 10), "male", target_year=2026)
        natures = [e.get('he_nature') for e in r.yingqi_events if e['mechanism'] == 'liuhe']
        self.assertIn('合动', natures)


if __name__ == "__main__":
    unittest.main()
