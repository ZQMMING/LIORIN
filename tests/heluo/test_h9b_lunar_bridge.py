# -*- coding: utf-8 -*-
"""H9b 河洛×黄历桥接测试。

覆盖：
  1. annotate_day lunar_python 兜底（农历/日柱/纳音/节气）
  2. annotate_day 注入 HuangliDay dict（字段映射 + source）
  3. adapter.compute 带 huangli_provider → 流日段挂黄历标注
"""
import unittest

from tongshu.engines.heluo.heluo_lunar_bridge import annotate_day, annotate_liuri_yao


class TestLunarBridge(unittest.TestCase):
    def test_annotate_lunar_python_fallback(self):
        """lunar_python 兜底：2026-12-07（大雪）应有农历/日柱/纳音。"""
        a = annotate_day("2026-12-07")
        self.assertEqual(a["source"], "lunar_python")
        self.assertTrue(a["lunar"], "农历不应为空")
        self.assertTrue(a["day_ganzhi"], "日柱不应为空")
        self.assertTrue(a["day_nayin"], "日纳音不应为空")
        # 2026-12-07 是大雪，应返回节气名（lunar_python 交节名）
        self.assertIsInstance(a["jie_qi"], str)

    def test_annotate_huangli_injection(self):
        """注入 HuangliDay dict：字段映射 + source=huangli_engine。"""
        hd = {
            "day_ganzhi": "甲子", "lunar_month": "十一", "lunar_day": "初十",
            "day_na_yin": "海中金", "jie_qi": "大雪",
            "yi": ["祭祀", "祈福"], "ji": ["开市", "动土"],
        }
        a = annotate_day("2026-12-07", hd)
        self.assertEqual(a["source"], "huangli_engine")
        self.assertEqual(a["lunar"], "十一月 初十")
        self.assertEqual(a["day_ganzhi"], "甲子")
        self.assertEqual(a["day_nayin"], "海中金")
        self.assertEqual(a["jie_qi"], "大雪")
        self.assertEqual(a["yi"], ["祭祀", "祈福"])
        self.assertEqual(a["ji"], ["开市", "动土"])

    def test_annotate_liuri_yao_passthrough(self):
        """流日判词挂载：不覆盖原判词字段，追加 lunar 标注。"""
        yao = {"yao": "九二", "ci": "井谷射鲋，瓮敝漏。", "ye": "", "buye": ""}
        out = annotate_liuri_yao(yao, "2026-12-07")
        self.assertEqual(out["yao"], "九二")
        self.assertEqual(out["ci"], "井谷射鲋，瓮敝漏。")
        self.assertIn("lunar", out)
        self.assertEqual(out["lunar"]["source"], "lunar_python")

    def test_annotate_liuri_yao_none(self):
        self.assertIsNone(annotate_liuri_yao(None, "2026-12-07"))


class TestAdapterHuangli(unittest.TestCase):
    def test_compute_with_provider(self):
        """adapter 带 huangli_provider：target 流日段 liuri_yao 挂 lunar。"""
        from tongshu.engines.heluo_adapter import HeluoAdapter

        calls = []

        def provider(solar_date: str):
            calls.append(solar_date)
            return {
                "day_ganzhi": "丙寅", "lunar_month": "十一", "lunar_day": "初十",
                "day_na_yin": "炉中火", "jie_qi": "大雪",
                "yi": ["祭祀"], "ji": ["嫁娶"],
            }

        a = HeluoAdapter()
        r = a.compute(
            (1980, 6, 22, 10), gender="male",
            target_year=2027, target_month=6, target_day=15,
            huangli_provider=provider,
        )
        gj = r.guajie or {}
        liuri_lunar = gj.get("liuri_lunar") or {}
        self.assertIn("lunar", liuri_lunar, "流日应期应挂黄历标注")
        self.assertEqual(liuri_lunar["source"], "huangli_engine")
        self.assertTrue(calls, "provider 应被调用")
        self.assertEqual(liuri_lunar["day_ganzhi"], "丙寅")
        # 原流日判词结构不受影响
        liuri_yao = gj.get("liuri_yao") or {}
        self.assertIn("yao", liuri_yao)

    def test_compute_without_provider(self):
        """不带 provider：lunar_python 兜底，liuri_yao.lunar.source=lunar_python。"""
        from tongshu.engines.heluo_adapter import HeluoAdapter

        a = HeluoAdapter()
        r = a.compute(
            (1980, 6, 22, 10), gender="male",
            target_year=2027, target_month=6, target_day=15,
        )
        liuri_lunar = (r.guajie or {}).get("liuri_lunar") or {}
        self.assertIn("lunar", liuri_lunar, "无 provider 也应挂 lunar（兜底）")
        self.assertEqual(liuri_lunar["source"], "lunar_python")


if __name__ == "__main__":
    unittest.main()
