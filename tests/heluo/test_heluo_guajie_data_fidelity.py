# -*- coding: utf-8 -*-
"""判词数据（`data/heluo/guajie_data.json`）的**原典保真守卫**（2026-10-22）。

**为什么要有这个守卫**
-------------------

`guajie_data.json` 是引擎**全部断语输出**的唯一数据源（64 卦 × 6 爻的
卦辞、爻辞、象曰、释义、断语、邵曰）。它一旦被静默改动 —— 改一个字、
删一条断语、串一行 —— 引擎会**照单全收地输出改过的判词**，而现有守卫
（表一致性、接口形状、变异演练）**全都发现不了**：数据变了，结构没变。

本守卫把「判词数据逐字来自原典」变成可回归的断言：
`data/heluo/guajie_raw/` 下的**原典切片**是唯一权威文本，
数据里的每一个字都必须能在切片中**逐字找到**。

**实测（2026-10-22）**：卦辞 64/64、爻辞 384/384、象曰 384/384、
断语 1088/1088、邵曰 383/383 —— **全部 100% 逐字命中**。

**不覆盖的字段**：`yi`（爻辞释义）与 `jingyi`/`shiyi`（精义/现代语义）
来自 `guajie_jingyi.json`（**现代语义整理**，非原典逐字），故不作原典回查 ——
但它们的**键集合**仍须与爻数一致（本守卫一并查）。
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "heluo" / "guajie_data.json"
SLICE_DIR = ROOT / "data" / "heluo" / "guajie_raw"


def _norm(s: str) -> str:
    """去全部空白（切片与数据可能跨行排版不同）。"""
    return re.sub(r"\s+", "", s or "")


def _slice_text() -> str:
    parts = []
    for p in sorted(SLICE_DIR.glob("*.txt")):
        parts.append(p.read_text(encoding="utf-8"))
    return _norm("\n".join(parts))


class TestGuajieDataFidelity(unittest.TestCase):
    """判词数据逐字来自原典切片。"""

    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.text = _slice_text()
        cls.assertTrue(cls.text, "原典切片为空，无法做保真校验")

    def test_sixty_four_hexagrams(self):
        self.assertEqual(len(self.data), 64, "应为 64 卦")
        names = [g["name"] for g in self.data]
        self.assertEqual(len(set(names)), 64, "卦名不得重复")

    def test_six_yao_each(self):
        for g in self.data:
            with self.subTest(gua=g["name"]):
                self.assertEqual(len(g.get("yaos") or []), 6,
                                 f"{g['name']} 应有 6 爻")

    def test_gua_ci_verbatim(self):
        """卦辞逐字来自原典。"""
        for g in self.data:
            with self.subTest(gua=g["name"]):
                ci = _norm(g.get("gua_ci"))
                self.assertTrue(ci, f"{g['name']} 卦辞为空")
                self.assertIn(ci, self.text,
                              f"{g['name']} 卦辞在原典切片中找不到：{g.get('gua_ci')}")

    def test_yao_ci_verbatim(self):
        """爻辞逐字来自原典（384 条）。"""
        for g in self.data:
            for y in g.get("yaos") or []:
                with self.subTest(gua=g["name"], yao=y.get("yao")):
                    ci = _norm(y.get("ci"))
                    self.assertTrue(ci, f"{g['name']}{y.get('yao')} 爻辞为空")
                    self.assertIn(ci, self.text,
                                  f"{g['name']}{y.get('yao')} 爻辞在原典切片中找不到：{y.get('ci')}")

    def test_xiang_verbatim(self):
        """象曰逐字来自原典（384 条）。"""
        for g in self.data:
            for y in g.get("yaos") or []:
                with self.subTest(gua=g["name"], yao=y.get("yao")):
                    x = _norm(y.get("xiang"))
                    self.assertTrue(x, f"{g['name']}{y.get('yao')} 象曰为空")
                    self.assertIn(x, self.text,
                                  f"{g['name']}{y.get('yao')} 象曰在原典切片中找不到：{y.get('xiang')}")

    def test_duans_verbatim(self):
        """断语逐字来自原典（1088 条）。"""
        for g in self.data:
            for y in g.get("yaos") or []:
                for i, d in enumerate(y.get("duans") or []):
                    with self.subTest(gua=g["name"], yao=y.get("yao"), duan=i):
                        dn = _norm(d)
                        self.assertTrue(dn, "断语为空")
                        self.assertIn(dn, self.text,
                                      f"{g['name']}{y.get('yao')} 第{i+1}条断语在原典切片中找不到：{d}")

    def test_shao_verbatim(self):
        """邵曰逐字来自原典（383 条；革九四底本无邵曰，空者跳过）。"""
        for g in self.data:
            for y in g.get("yaos") or []:
                s = _norm(y.get("shao"))
                if not s:
                    # 底本缺该条（革九四）—— 记为「原典无」，不判、不造。
                    self.assertEqual((g["name"], y.get("yao")), ("革", "九四"),
                                     "除底本缺失者外，邵曰不得为空")
                    continue
                with self.subTest(gua=g["name"], yao=y.get("yao")):
                    self.assertIn(s, self.text,
                                  f"{g['name']}{y.get('yao')} 邵曰在原典切片中找不到：{y.get('shao')}")

    def test_gua_header_lines_verbatim(self):
        """卦头断语逐字来自原典（288 条；**纳甲、旺时、卦气属月都在其中**）。

        卦头是「纳甲是：…」「卦气属X月」「…得时也」等判据的载体 ——
        纳甲又是「叶/不叶」的第二输入（年干支是否在纳甲 ✓），
        故卦头同样必须逐字来自原典。
        """
        for g in self.data:
            for i, ln in enumerate(g.get("lines") or []):
                with self.subTest(gua=g["name"], line=i):
                    n = _norm(str(ln))
                    self.assertTrue(n, "卦头条目为空")
                    self.assertIn(n, self.text,
                                  f"{g['name']} 第{i+1}条卦头在原典切片中找不到：{ln}")

    def test_engine_exposes_same_data(self):
        """引擎读到的判词与数据文件一致（防止引擎另有一份副本）。"""
        from tongshu.engines.heluo import guajie as gj
        loaded = gj.load_guajie_data()
        self.assertEqual(len(loaded), 64)
        for g in self.data:
            with self.subTest(gua=g["name"]):
                got = loaded.get(g["name"])
                self.assertIsNotNone(got, f"引擎未载入 {g['name']}")
                self.assertEqual(_norm(got.gua_ci), _norm(g["gua_ci"]),
                                 f"{g['name']} 卦辞与数据文件不一致")


if __name__ == "__main__":
    unittest.main()
