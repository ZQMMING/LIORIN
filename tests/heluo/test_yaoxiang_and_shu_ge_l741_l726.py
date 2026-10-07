"""批次 F-2 守卫：爻辞取象 L741 接生产链 + 数格 L726/L729/L732 落码

2026-10-08。覆盖三件事，每件都要有牙齿：

1. **数格三条真落码**——不是查表里有没有名字，而是查判域**逐支**对不对、
   边界外侧反例**必须不命中**。
2. **爻辞取象接进生产链**——`compose_guajie` 真的调了扫描器，
   结果真的进了 `evidence` / `to_dict` / `to_structured`。
3. **不敢猜的地方仍然不敢猜**——L726「更元堂安非其位」与 L741「卦数凶」
   两个未定义条件必须仍标为不可判，不得悄悄补一个默认值。

═══════════════════════════════════════════════════════════════════
本文件的取证依据（2026-10-08，四本独立转录交叉核对一致）
═══════════════════════════════════════════════════════════════════

L726「天数二十四以下而地数三十，地数二十八以下而天数二十五，
      天数二十六以上而地数三十，地数三十二以上而天数二十五，
      此阴阳偏胜偏负，更元堂安非其位，必主孤寡下贱。」
L729「天数四五十以上而地数不足，名以强凌弱，以尊凌卑，
      在阳月生人大贵，七八九十冬月生横恶凶死。」
L732「地数五六十以上而天数不足，名以下犯上，以卑逾尊，
      在阴月生人富贵，而水以后夏至前生人最恶下贱。」
L741「……文王作易，近取诸身，远取诸物，如言龙则必贵。
      二月至八月生者，吉余欠利。言马则前程远大……」

L732 末句「而水以后夏至前」——四本转录**俱作「水」**，按语义当作「冬」；
逐字照录不擅改，理由登记在 yue_ling_shu_ge.SHU_GE_TABLE 的 verdict 栏。
"""
from __future__ import annotations

import ast
import io
import re
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src" / "tongshu" / "engines" / "heluo"


def _strip_docstrings_and_comments(src: str) -> str:
    """返回**只含可执行代码**的源码：剥掉三引号文档字符串与 ``#`` 注释。

    本立纪律的由来：修复注释里大量引用被修掉的旧串（如 ``pattern`` 那条
    「单轴分档不占 pattern 主判位」旁会写旧名），用全文 assertNotIn 判
    「某缺陷不存在」会被注释里的另一份副本遮住，等于没判。
    注释是否提及与缺陷是否存在是两件事，故断言必须落在可执行代码上。
    """
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    tree2 = ast.parse(src)
    for node in ast.walk(tree2):
        if hasattr(node, "body") and isinstance(getattr(node, "body"), list):
            node.body = [n for n in node.body
                         if not (isinstance(n, ast.Expr)
                                 and isinstance(n.value, ast.Constant)
                                 and isinstance(n.value.value, str))]
    # 逐行去注释（保守：只砍不在字符串里的 #）
    out = []
    for line in ast.unparse(tree).split("\n"):
        out.append(re.sub(r"\s+#.*$", "", line))
    return "\n".join(out)


class TestShuGeThreeNewRules(unittest.TestCase):
    """L726/L729/L732 三条数格。"""

    @classmethod
    def setUpClass(cls):
        from tongshu.engines.heluo.yue_ling_shu_ge import (
            SHU_GE_TABLE, classify_shu_ge, shu_ge_conflicts)
        cls.TABLE = SHU_GE_TABLE
        cls._classify = staticmethod(classify_shu_ge)
        cls._conflicts = staticmethod(shu_ge_conflicts)
        cls.BY_NAME = {r.name: r for r in SHU_GE_TABLE}

    def names(self, t: int, d: int) -> set[str]:
        return {r.name for r in self._classify(t, d)}

    # ── 存在性 ──────────────────────────────────────────────────
    def test_three_rules_exist(self):
        for must in ("阴阳偏胜偏负", "以强凌弱", "以下犯上"):
            self.assertIn(must, self.BY_NAME, f"数格表缺 L726/L729/L732 的「{must}」")

    def test_citations_point_at_right_lines(self):
        """出处必须指到本批次取证的那三行，不能张冠李戴。"""
        self.assertIn("L726", self.BY_NAME["阴阳偏胜偏负"].citation)
        self.assertIn("L729", self.BY_NAME["以强凌弱"].citation)
        self.assertIn("L732", self.BY_NAME["以下犯上"].citation)
        # 逐字首句
        self.assertIn("天数二十四以下而地数三十", self.BY_NAME["阴阳偏胜偏负"].citation)
        self.assertIn("天数四五十以上而地数不足", self.BY_NAME["以强凌弱"].citation)
        self.assertIn("地数五六十以上而天数不足", self.BY_NAME["以下犯上"].citation)

    # ── 阴阳偏胜偏负：四支并集 ─────────────────────────────────
    def test_pian_sheng_four_branches_declared(self):
        alts = self.BY_NAME["阴阳偏胜偏负"].alternatives
        self.assertEqual(len(alts), 4, "L726 是四个并列条件，少一支就漏判")
        self.assertEqual(set(alts), {(0, 24, 30, 30), (25, 25, 0, 28),
                                     (26, 999, 30, 30), (25, 25, 32, 999)})

    def test_pian_sheng_each_branch_hits(self):
        cases = [(20, 30), (25, 20), (30, 30), (25, 40)]
        for t, d in cases:
            self.assertIn("阴阳偏胜偏负", self.names(t, d), f"支({t},{d}) 未命中")

    def test_pian_sheng_branch_outer_edges_miss(self):
        """四支的外侧必须**不**命中——并集判域最容易被写成一个大矩形。"""
        miss = [(25, 30), (24, 31), (26, 29), (25, 31), (25, 29), (20, 20)]
        for t, d in miss:
            self.assertNotIn("阴阳偏胜偏负", self.names(t, d),
                             f"({t},{d}) 在四支之外，误命中说明并集被压成了矩形")

    def test_pian_sheng_branch_boundaries_exact(self):
        """四支的内侧端点必须命中（24/26/28/32 全部卡死）。"""
        hits = [(24, 30), (26, 30), (25, 28), (25, 32)]
        for t, d in hits:
            self.assertIn("阴阳偏胜偏负", self.names(t, d), f"端点({t},{d}) 漏判")

    def test_pian_sheng_uses_alternatives_not_rectangle(self):
        """判域**只能**由 alternatives 表达；若退回单一矩形，支②必错。"""
        rule = self.BY_NAME["阴阳偏胜偏负"]
        self.assertTrue(rule.alternatives, "alternatives 被清空了")
        self.assertNotEqual((rule.lo_t, rule.hi_t, rule.lo_d, rule.hi_d),
                            (25, 25, 0, 28),
                            "lo/hi 又被填成支②的矩形，将吞掉其余三支")

    # ── 以强凌弱 L729 ──────────────────────────────────────────
    def test_yi_qiang_ling_ruo_domain(self):
        for t, d in [(40, 29), (50, 5), (60, 20), (100, 1)]:
            self.assertIn("以强凌弱", self.names(t, d), f"({t},{d}) 应命中")

    def test_yi_qiang_ling_ruo_outer_edges_miss(self):
        """「四五十以上」下界取 40；天数不足上界取 29（原典「地数不足」）。"""
        for t, d in [(39, 20), (40, 30), (100, 30)]:
            self.assertNotIn("以强凌弱", self.names(t, d),
                             f"({t},{d}) 越界误命中")

    def test_yi_qiang_ling_ruo_declares_same_grille_alias(self):
        """L729 与 L58「以强伏弱」同格异名，必须登记，不得静默合并。"""
        self.assertIn("以强伏弱", self.BY_NAME)
        self.assertIn("同格异名", self.BY_NAME["以强凌弱"].conflict)
        # 重叠处两存
        names = self.names(50, 5)
        self.assertIn("以强凌弱", names)
        self.assertIn("以强伏弱", names)

    # ── 以下犯上 L732 ──────────────────────────────────────────
    def test_yi_xia_fan_shang_domain(self):
        for t, d in [(24, 50), (10, 60), (0, 999), (9, 50)]:
            self.assertIn("以下犯上", self.names(t, d), f"({t},{d}) 应命中")

    def test_yi_xia_fan_shang_outer_edges_miss(self):
        """天数须**不足**（<25）、地数须「五六十以上」（≥50）。"""
        for t, d in [(25, 60), (15, 49), (25, 50)]:
            self.assertNotIn("以下犯上", self.names(t, d), f"({t},{d}) 越界误命中")

    def test_yi_xia_fan_shang_keeps_the_yuan_verbatim(self):
        """L732 末句「而水以后夏至前」是讹字，判语须**逐字照录「水」**。
        把「水」偷偷改成「冬」= 把订正伪装成原典；订正理由另记，不得混入判语。
        """
        v = self.BY_NAME["以下犯上"].verdict
        self.assertIn("而水以后夏至前生人最恶下贱", v)
        self.assertIn("讹字", v, "照录的同时必须留下订正理由")

    # ── 未定义条件不得被悄悄补上 ───────────────────────────────
    def test_an_fei_qi_wei_marked_undefined_not_faked(self):
        """L726 缀的「更元堂安非其位」全卷未定义 → 标未定义、不参与判定。
        不得伪造一个安位/非其位判据出来。
        """
        c = self.BY_NAME["阴阳偏胜偏负"].conflict
        self.assertIn("未定义", c)
        self.assertIn("更元堂安非其位", c)
        src = (_SRC / "yue_ling_shu_ge.py").read_text(encoding="utf-8")
        code = _strip_docstrings_and_comments(src)
        for fake in ("an_fei_qi_wei", "anwei", "非其位判据", "is_an_wei"):
            self.assertNotIn(fake, code,
                             f"可执行代码里冒出了伪造的「{fake}」安位判据")

    def test_conflict_disclosure_surfaced(self):
        """三条都带 conflict 登记 → 上层必须能披露出来，不是死字段。"""
        joined = " ".join(self._conflicts(24, 30)) + " " + \
                 " ".join(self._conflicts(50, 5))
        self.assertTrue(joined.strip(), "重叠区未披露任何冲突说明")

    # ── 静态：并集分支不可删 ───────────────────────────────────
    def test_matches_alternatives_branch_is_executable(self):
        src = (_SRC / "yue_ling_shu_ge.py").read_text(encoding="utf-8")
        code = _strip_docstrings_and_comments(src)
        self.assertIn("rule.alternatives", code,
                      "_matches 里的并集分支被删了，四支判域将退化为空")
        # 只查「同一支里 t、d 两轴**同时**卡」这个关键语义。比对前压掉全部空白，
        # 且不锚定 any( 后的括号个数——ast.unparse 对跨行生成器表达式会多补一层
        # 括号，锚死括号就成了对格式化器而不是对逻辑的断言。
        flat = re.sub(r"\s+", "", code)
        self.assertIn("lo_t<=t<=hi_tandlo_d<=d<=hi_dfor", flat,
                      "并集判域的矩形判定被改写，四支可能退化成单轴比较")


class TestYaoXiangTable(unittest.TestCase):
    """爻辞取象表 L741。"""

    @classmethod
    def setUpClass(cls):
        from tongshu.engines.heluo.yao_xiang import (
            YAO_XIANG_TABLE, scan_yao_xiang, xiang_evidence)
        cls.T = YAO_XIANG_TABLE
        cls._scan = staticmethod(scan_yao_xiang)
        cls._ev = staticmethod(xiang_evidence)

    def test_eighteen_keys_in_original_order(self):
        self.assertEqual([h.key for h in self.T],
                         ["龙", "马", "牛", "羊", "永", "鹤", "龟", "鸿",
                          "鸟", "月", "木", "血", "忧", "甘", "苦", "金",
                          "肉", "朋"])

    def test_conditional_count_is_five(self):
        cond = [h.key for h in self.T if h.conditional]
        self.assertEqual(cond, ["龙", "鸟", "月", "木", "朋"])

    def test_unconditional_never_participates(self):
        """无条件 13 条：登记断语但**恒不参与判定**（原典没给取字之外的判据）。"""
        for h in self._scan("马牛羊永鹤龟鸿血忧甘苦金肉"):
            self.assertFalse(h.participated, f"言{h.key} 无条件却参与了判定")

    def test_real_corpus_yao_hits(self):
        """用真实语料（坤上六「龙战于野，其血玄黄」）验证，不是自造句子。"""
        hits = self._scan("龙战于野，其血玄黄")
        self.assertEqual([h.key for h in hits], ["龙", "血"])

    def test_yan_long_month_condition(self):
        """L741「二月至八月生者，吉余欠利」——含两端。"""
        self.assertTrue(self._scan("龙战于野", birth_month=2)[0].satisfied)
        self.assertTrue(self._scan("龙战于野", birth_month=8)[0].satisfied)
        self.assertFalse(self._scan("龙战于野", birth_month=1)[0].satisfied)
        self.assertFalse(self._scan("龙战于野", birth_month=9)[0].satisfied)

    def test_yan_mu_spring_summer_condition(self):
        for m, want in ((2, False), (3, True), (6, True), (7, False)):
            h = [x for x in self._scan("言木之华", birth_month=m)][0]
            self.assertEqual(h.satisfied, want, f"生月{m}")

    def test_missing_month_yields_undecidable_not_default(self):
        """缺生月 → satisfied=None（不可判），不得默认为某个月份。"""
        h = self._scan("龙战于野")[0]
        self.assertIsNone(h.satisfied)
        self.assertFalse(h.participated)

    def test_yan_niao_needs_gua_number(self):
        """L741「如卦数凶，此走空浮薄之夫」——前提挂在卦数上。"""
        self.assertIsNone(self._scan("飞鸟遗之", shu_gua_xiang=None)[0].satisfied)
        self.assertTrue(self._scan("飞鸟遗之", shu_gua_xiang=False)[0].satisfied)
        self.assertFalse(self._scan("飞鸟遗之", shu_gua_xiang=True)[0].satisfied)

    def test_yan_yue_discloses_engine_picked_boundary(self):
        """L741 只说「望前」未给精确界 → 引擎取农历十五为界**必须随结果披露**。"""
        h = self._scan("如月之恒", day_lunar=20)[0]
        self.assertFalse(h.satisfied)
        self.assertIn("原典未载", h.condition)
        self.assertTrue(self._scan("如月之恒", day_lunar=10)[0].satisfied)

    def test_evidence_says_why_unconditional_not_judged(self):
        ev = " ".join(self._ev(self._scan("马牛之壮")))
        self.assertIn("只登记不断吉凶", ev)


class TestYaoXiangWiredIntoProduction(unittest.TestCase):
    """爻辞取象必须真的在生产链上跑，不是躺在一个没人调用的模块里。"""

    def _compose(self, liunian_gua="坤", liunian_yao="上六"):
        from tongshu.engines.heluo.guajie import compose_guajie
        return compose_guajie(
            prenatal_name="乾", postnatal_name="坤", yuantang_yao="九五",
            birth_month=5, tian_shu=25, di_shu=30, year_ganzhi="庚午",
            gender="male", liunian_hexagram=liunian_gua, liunian_yao=liunian_yao,
            target_year=2026)

    def test_compose_produces_hits(self):
        res = self._compose()
        self.assertTrue(res.yao_xiang_hits, "compose_guajie 未产出任何取象命中")
        self.assertEqual([h.key for h in res.yao_xiang_hits], ["龙", "血"])

    def test_evidence_carries_xiang_lines(self):
        ev = self._compose().evidence
        self.assertTrue(any("爻辞取象" in e for e in ev), "evidence 未写取象行")
        self.assertTrue(any("言龙" in e and "言血" in e for e in ev))

    def test_to_dict_serializes_hits(self):
        d = self._compose().to_dict()
        self.assertIn("yao_xiang_hits", d)
        self.assertEqual(len(d["yao_xiang_hits"]), 2)
        self.assertEqual(set(d["yao_xiang_hits"][0]),
                         {"key", "verdict", "conditional", "condition",
                          "satisfied", "participated"})

    def test_to_structured_passes_through(self):
        """to_dict 有、结构化视图无 = 接上它的人静默丢掉整层取象。"""
        from tongshu.engines.heluo.guajie import to_structured
        res = self._compose()
        st = to_structured(res.to_dict())
        self.assertIn("yao_xiang_hits", st)
        self.assertEqual(len(st["yao_xiang_hits"]), 2)

    def test_pipeline_exposes_key(self):
        """端到端：API 出口契约快照里必须有该键。"""
        p = (_ROOT / "tests" / "test_heluo_guajie_wiring.py").read_text(encoding="utf-8")
        block = p[p.index("_GUAJIE_KEYS = {"):p.index("}", p.index("_GUAJIE_KEYS = {"))]
        self.assertIn('"yao_xiang_hits"', block)

    def test_no_guashu_xiong_substituted_for_gua_number(self):
        """「卦数凶」≠ 天数/地数之凶。生产链若把 judge_shu_xiong 塞进
        shu_gua_xiang，等于凭空造一条原典没有的判据。必须仍传 None。
        """
        src = (_SRC / "guajie.py").read_text(encoding="utf-8")
        code = _strip_docstrings_and_comments(src)
        self.assertIn("shu_gua_xiang=None", code,
                      "生产链不再显式传 shu_gua_xiang=None，「卦数凶」条件易被误填")
        self.assertNotIn("shu_gua_xiang=sx", code)
        self.assertNotIn("shu_gua_xiang=shu_xiong", code)

    def test_no_lunar_day_faked_from_gregorian(self):
        """农历日没有输入就得判不可判，不得拿公历日冒充。"""
        src = (_SRC / "guajie.py").read_text(encoding="utf-8")
        code = _strip_docstrings_and_comments(src)
        self.assertIn("day_lunar=None", code)


if __name__ == "__main__":
    unittest.main()