# -*- coding: utf-8 -*-
"""真实命例回归守卫（2026-10-24）。

**为什么要有这个守卫**

历法/节气/时柱链是河洛引擎的地基：它错了，**后面所有判据全错**，
而表结构、接口形状、变异演练**全都发现不了**（数据没变，结构也没变）。

本守卫用**真实命例**做地基验收：
`data/案例回归样本.json` 里每条都是一条**真实命例已排定的四柱**
（出自公开的八字实战擂台赛反馈），引擎必须从「公历日期 + 时辰 + 性别」
**复现**该四柱。

口径：时辰取命例**时柱区间**的代表小时，四柱按**标准时**复现 ——
因为公开命例本身多按北京时间（东经 120）排定，不做真太阳时校正。
（真太阳时口径另由 `test_heluo_true_solar_siduan.py` 等守卫覆盖。）

样本随包分发 ⇒ **服务器部署后同样能跑这条守卫**。

**另一条线：出生地解析**
真太阳时要靠出生地经度；现实中传入的是「河北省唐山市」这类**行政地址**。
若解析不到地点 ⇒ 真太阳时**拿不到经度** ⇒ 时柱可能整体偏 1 个时辰。
故本文件另钉一组「行政地址 → 期望城市」的解析断言。
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from heluo_engine.engines.bazi_engine import BaziEngine
from heluo_engine.engines.time.resolver import TimeResolver

SAMPLE = ROOT / "src" / "heluo_engine" / "data" / "案例回归样本.json"


class TestRealCaseRegression(unittest.TestCase):
    """真实命例回归：引擎必须复现命例已排定的四柱。"""

    @classmethod
    def setUpClass(cls):
        doc = json.loads(SAMPLE.read_text(encoding="utf-8"))
        cls.samples = doc["samples"]
        cls.doc = doc

    def test_sample_set_is_substantial(self):
        """样本量与覆盖面（样本被削到很少时守卫会失去意义）。"""
        self.assertGreaterEqual(len(self.samples), 50,
                                "回归样本不足 50 条")
        years = [s["date"][0] for s in self.samples]
        self.assertLessEqual(min(years), 1950, "样本未覆盖早年命例")
        self.assertGreaterEqual(max(years), 2020, "样本未覆盖近年命例")
        genders = {s["gender"] for s in self.samples}
        self.assertEqual(genders, {"male", "female"}, "样本未覆盖男女两性")
        hours = {s["hour"] for s in self.samples}
        self.assertGreaterEqual(len(hours), 8, "样本时辰覆盖太少")

    def test_all_pillars_reproduced(self):
        """逐条复现四柱（年/月/日/时）。"""
        engine = BaziEngine()
        bad = []
        for s in self.samples:
            y, m, d = s["date"]
            chart = engine.compute((y, m, d, s["hour"]), gender=s["gender"])
            p = chart.get_pillars_chinese()
            got = [p["year"], p["month"], p["day"], p["hour"]]
            want = s["bazi"].split()
            if got != want:
                bad.append(f"id={s['id']} {y}-{m:02d}-{d:02d} {s['hour']}时 "
                           f"{s['gender']}: 期望 {' '.join(want)} → 实得 {' '.join(got)}")
        self.assertEqual(bad, [],
                         f"{len(bad)}/{len(self.samples)} 条命例四柱未复现：\n"
                         + "\n".join(bad[:20]))


class TestAdminAddressResolution(unittest.TestCase):
    """行政地址 → 地点解析（真太阳时能不能拿到正确经度）。"""

    #: (行政地址, 期望城市名)
    CASES = [
        ("河北省唐山市", "唐山"),
        ("河北省保定市", "保定"),
        ("广西壮族自治区桂林市", "桂林"),
        ("浙江省绍兴市嵊州市", "绍兴"),
        ("黑龙江省牡丹江市", "牡丹江"),
        ("内蒙古自治区阿拉善盟", "阿拉善盟"),
        ("河南省焦作市济源市", "济源"),
        ("广东省潮州市", "潮州"),
        ("江苏省镇江市", "镇江"),
        ("江西省上饶市", "上饶"),
        ("福建省福州市", "福州"),
        ("江苏省镇江市", "镇江"),
        ("吉林省延边朝鲜族自治州", "延边"),
        ("新疆维吾尔自治区乌鲁木齐市", "乌鲁木齐"),
    ]

    @classmethod
    def setUpClass(cls):
        cls.tr = TimeResolver()

    def test_admin_addresses_resolve(self):
        """行政地址必须解析到**具体城市**（不是省级兜底）。"""
        bad = []
        for addr, want in self.CASES:
            with self.subTest(addr=addr):
                try:
                    loc = self.tr.lookup(addr)
                except Exception as e:
                    bad.append(f"{addr}: 解析失败（{e}）")
                    continue
                if loc.name_zh != want:
                    bad.append(f"{addr}: 期望 {want} → 实得 {loc.name_zh}")
                if loc.is_province_representative:
                    bad.append(f"{addr}: 落到省级兜底 {loc.name_zh}，"
                               f"经度误差可达 1–2°（真太阳时 4–8 分钟）")
        self.assertEqual(bad, [], "行政地址解析有误：\n" + "\n".join(bad))

    def test_province_only_falls_back_to_representative(self):
        """只有省名时用省级兜底（并标明是兜底）。"""
        loc = self.tr.lookup("河北省")
        self.assertTrue(loc.is_province_representative,
                        "只有省名的地址应落到省级兜底条目")
        self.assertIsNotNone(loc.longitude)

    def test_exact_match_still_works(self):
        """精确匹配（规范名/别名/id）不能因新增解析而退化。"""
        for name in ("唐山", "北京", "乌鲁木齐"):
            with self.subTest(name=name):
                loc = self.tr.lookup(name)
                self.assertEqual(loc.name_zh, name)

    def test_unknown_location_still_raises(self):
        """查不到仍须抛 LocationError（不静默退化为空 registry）。"""
        from heluo_engine.engines.time.exceptions import LocationError
        with self.assertRaises(LocationError):
            self.tr.lookup("不存在的地点ZZZZ")

    def test_target_year_outside_dayun_is_explicit(self):
        """★ 目标年**不在流年序列**时，必须**显式标注**，不得静默返回空串。

        大运按《河洛理数·卷之四》只走一轮（先天6段+后天6段），
        覆盖到 ~75 岁视阴阳爻组合而定 ⇒ 高龄命主的某些目标年**本就没有**流年卦。

        此前这种情况：判词层流年卦为空串、平台层**不产出**该年信号，
        而提示只藏在 evidence 里一句话 ⇒ 用户侧看不见 = 静默缺失。
        故断言 summary 里必须出现明确说明。
        """
        from heluo_engine.adapter import HeluoAdapter
        # 1942-11-22 生（壬午年），其大运覆盖不到 2026 年（85 岁）
        res = HeluoAdapter().compute((1942, 2, 13, 0), gender="male",
                                     target_date="2026-10-23")
        g = res.guajie or {}
        if g.get("liunian_hexagram"):
            self.skipTest("该命例目标年已在大运覆盖内（构造失效）")
        summary = " ".join(g.get("summary") or [])
        self.assertIn("大运", summary,
                      "目标年不在流年序列时，summary 必须说明原因")
        self.assertIn("2026", summary,
                      "summary 的说明里必须点明是哪个目标年")
        self.assertTrue(any("流年" in e for e in (g.get("evidence") or [])),
                        "evidence 里也须留痕")


if __name__ == "__main__":
    unittest.main()
