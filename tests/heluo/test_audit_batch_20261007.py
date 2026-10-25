"""2026-10-07 深度审计修复批的守卫（批次 A/B/C/D）。

三份只读审计（数据流与输出契约 / 空断言与伪引 / 原典覆盖缺口）查出的实质缺陷，
逐条在此立牙。守则：

* 每条断言都锁**审计复现的具体失败形态**，不是锁「代码长这样」。
* 凡涉及原典出处的，按**区块切片**判定，不用全文 ``assertIn``——
  同句原话在 docstring／注释／函数文档里常有多份副本，全文匹配会被别的副本遮住。
* 不调用被测函数去求期望值。
"""
from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo import guajie as G                      # noqa: E402
from heluo_engine.engines.heluo.canonical import HeluoCanonical          # noqa: E402
from heluo_engine.engines.heluo.diagnosis_rule_graph import (             # noqa: E402
    HELUO_RULES, RULE_DOMAIN_MAP, build_diagnosis_graph, dropped_rules,
)
from heluo_engine.engines.heluo.evidence_producer import HeLuoEvidenceProducer  # noqa: E402
from heluo_engine.engines.heluo.frozen_state import build_frozen_state     # noqa: E402
from heluo_engine.engines.heluo.guidance import (                         # noqa: E402
    HUAGONG_ACTION_TEMPLATES, HUAGONG_ADVICE, HeluoGuidanceEngine,
)
from heluo_engine.engines.heluo.hua_gong import (                         # noqa: E402
    HuaGongState, compute_huagong,
)

ENGINE = Path(__file__).resolve().parents[2] / "src" / "heluo_engine" / "engines" / "heluo"

BAZI = [("癸", "亥"), ("乙", "丑"), ("戊", "午"), ("丙", "午")]
JXL = [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")]     # 纪晓岚盘


def _src(name: str) -> str:
    with io.open(ENGINE / name, encoding="utf-8") as f:
        return f.read()


def _strip(text: str) -> str:
    """剥掉三引号文档字符串与 # 行注释，只留可执行代码。"""
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith('"""', i) or text.startswith("'''", i):
            q = text[i:i + 3]
            j = text.find(q, i + 3)
            i = n if j < 0 else j + 3
            continue
        if text[i] == "#":
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _code(name: str) -> str:
    """只取**可执行代码**：剥掉三引号文档字符串与 # 行注释。

    本批修复在解释性注释里大量引用了被修掉的旧串（伪引路径、「V13_河洛诊断
    规则集」、「并列共存」、``resolve_yuantang = None``…）。若用全文 assertIn，
    这些「说明自己修了什么」的注释会把断言自己遮住——正是本项目反复踩的坑。
    守卫必须只盯会真正生效的那一行。
    """
    return _strip(_src(name))


def _sample_guajie(min_year=2020, max_year=2035, want_xiong=False):
    c = HeluoCanonical()
    res = c.calculate(BAZI, "male", "午", birth_year=1983, birth_date="1983-11-03")
    for yr in range(min_year, max_year):
        g = G.build_guajie_from_result(res, target_year=yr, target_month=5, target_day=10)
        d = g if isinstance(g, dict) else g.to_dict()
        if d.get("liunian_yao") and (not want_xiong
                                     or d.get("liunian_hexagram") in set(G.TWELVE_XIONG_GUA)):
            return res, d
    return res, None


# ═══════════════════════════ 批次 A：化工 ═══════════════════════════
class TestHuaGongHonesty(unittest.TestCase):
    """A1 未跑过的检查不得写成「已检查且未通过」。"""

    def test_nayin_layer_not_run_must_not_claim_all_three_layers_checked(self):
        """未传年干支 → 纳音层**根本没参与**，evidence 不得称「三层俱不得」。

        断言按**语义子串**判，不按整句前缀——变异可能把措辞改写，
        只要还在宣称三层都查过，就必须抓住。
        """
        r = compute_huagong("乾", "乾", "乾", "乾", "子")
        for e in r.evidence:
            self.assertNotIn("纳音三层俱不得", e,
                             "把未跑的第三层写成已检查：%r" % e)
        # 关键判据不是「有没有写未参与」——那只说明措辞，
        # 而是说**不许拿纳音跟当令化工卦比过**（本级根本没参与，比不了）。
        for e in r.evidence:
            self.assertNotIn("不同气", e,
                             "未传年干支却声称比过纳音五行：%r" % e)

    def test_nayin_layer_actually_checked_is_recorded(self):
        """传了年干支 → 本级真的跑了，证据里必须有「已查 + 比过」。"""
        r = compute_huagong("乾", "乾", "乾", "乾", "子", year_gan="甲", year_zhi="辰")
        self.assertTrue(any("已查" in e for e in r.evidence), r.evidence)
        self.assertFalse(any("只作二级否定" in e for e in r.evidence),
                         "本级已参与却仍称只作二级否定：%s" % r.evidence)
        self.assertTrue(any("不同气" in e for e in r.evidence),
                        "本级已查却没留下比对结果：%s" % r.evidence)

    def test_printed_set_contains_claimed_opposite(self):
        """evidence 打印的三画卦集合必须**含**它下一行声称的反卦。"""
        r = compute_huagong("乾", "乾", "巽", "兑", "寅")
        quan = [e for e in r.evidence if e.startswith("卦中三画卦全集")]
        opp = [e for e in r.evidence if "含反卦" in e]
        self.assertEqual(len(quan), 1, r.evidence)
        self.assertTrue(opp, "本例应含反卦：%s" % r.evidence)
        claimed = opp[0].split("含反卦")[1].split("（")[0]
        self.assertIn(claimed, quan[0],
                      "打印的集合 %r 不含所称反卦 %r" % (quan[0], claimed))

    def test_opposite_line_names_its_layer(self):
        """反卦行须标出它出自哪一层，否则「同层/跨层」无从复核。"""
        r = compute_huagong("乾", "乾", "巽", "兑", "寅")
        opp = [e for e in r.evidence if "含反卦" in e][0]
        self.assertTrue(any(w in opp for w in ("正体", "互体")),
                        "反卦行未标层：%r" % opp)

    def test_verdict_unchanged_by_honesty_fixes(self):
        """审计只要求改证据表述，**判决口径不得随之漂移**。"""
        for args, want in (
            (("乾", "离", "坤", "离", "子"), (HuaGongState.KEZHI, "互体")),
            (("坎", "坎", "乾", "坎", "午"), (HuaGongState.KEZHI, "互体")),
            (("兑", "震", "乾", "震", "卯"), (HuaGongState.KEZHI, "正体")),
            (("巽", "巽", "乾", "乾", "辰"), (HuaGongState.REVERSE, "无")),
            (("乾", "乾", "坤", "坤", "子"), (HuaGongState.UNRESOLVED, "无")),
        ):
            r = compute_huagong(*args)
            self.assertEqual((r.state, r.level), want, args)

    def test_no_replacement_char_in_source(self):
        """注释里的 U+FFFD 是编码损坏，须清零。"""
        self.assertNotIn("\ufffd", _src("hua_gong.py"), "hua_gong.py 残留替换字符")


class TestGuidanceStatesComplete(unittest.TestCase):
    """A2 KEZHI（原典最凶档）曾产出 0 建议 0 警示。"""

    ALL_STATES = ("NORMAL", "RESCUED", "REVERSE", "KEZHI", "WEAK", "UNRESOLVED")

    def test_every_state_has_templates(self):
        for st in self.ALL_STATES:
            self.assertIn(st, HUAGONG_ADVICE, "缺总体基调：%s" % st)
            self.assertIn(st, HUAGONG_ACTION_TEMPLATES, "缺行动模板：%s" % st)

    def test_worst_state_is_not_the_least_advised(self):
        eng = HeluoGuidanceEngine()

        def n(st):
            g = eng.generate([], None, "乾为天", "乾为天", "乾", hua_gong_state=st,
                             subject="t")
            return len(g.action_items), len(g.caution_items)

        kezhi = n("KEZHI")
        self.assertGreater(kezhi[0] + kezhi[1], 0, "KEZHI 产出零建议零警示")
        self.assertGreater(kezhi[1], 0, "KEZHI（原典最凶档）拿不到任何警示")

    def test_unknown_state_fallback_is_only_for_unknown(self):
        """「化工状态待判定」只允许留给真未知的态，不得吞掉已定义状态。"""
        g = HeluoGuidanceEngine().generate([], None, "乾为天", "乾为天", "乾",
                                           hua_gong_state="KEZHI", subject="t")
        self.assertNotIn("待判定", g.overview, g.overview)


# ═══════════════════════════ 批次 B：输出契约 ═══════════════════════════
class TestZhengduiFandui(unittest.TestCase):
    """B1 十二凶卦曾被写成「命卦」且必然重复两条。"""

    def test_pairwise_check_has_no_twelve_xiong(self):
        """十二凶卦是单卦属性，不得寄生在成对判法里（否则每调必重复）。"""
        w = G.check_zhengdui_fandui("乾", "坤")
        self.assertFalse(any("十二凶卦" in x for x in w), w)

    def test_label_follows_caller_not_hardcoded(self):
        self.assertTrue(G.check_twelve_xiong("乾", "流年卦")[0].startswith("流年卦乾"))
        self.assertTrue(G.check_twelve_xiong("乾", "命卦")[0].startswith("命卦乾"))
        self.assertEqual(G.check_twelve_xiong("乾为天"), [], "非十二凶卦却报警")

    def test_no_duplicate_when_prenatal_equals_postnatal(self):
        """先天卦与后天卦同名时，两次配对会给出**同一条**警示，去重必须生效。

        这是去重那行唯一真正起作用的场景——只测「流年卦落十二凶卦」是
        空跑（拆出 check_twelve_xiong 后本就不可能重复）。
        卦对从 ZONG_GUA 实查，不写死。
        """
        pair = next(((a, b) for a, b in G.ZONG_GUA.items()
                     if a in G.COMPOUND_GUA and b in G.COMPOUND_GUA), None)
        self.assertIsNotNone(pair, "ZONG_GUA 里没有可用的综卦对")
        liunian, other = pair
        r = G.compose_guajie(
            prenatal_name=other, postnatal_name=other,
            yuantang_yao="九五", birth_month=1, tian_shu=30, di_shu=30,
            liunian_hexagram=liunian, liunian_yao="九五")
        z = r.zhengdui_fandui
        self.assertTrue(z, "本例应产出正对反对条目（%s↔%s）" % (liunian, other))
        self.assertEqual(len(z), len(set(z)),
                         "先天＝后天时条目重复：%s" % z)

    def test_no_duplicate_and_label_is_liunian(self):
        _, d = _sample_guajie(want_xiong=True)
        self.assertIsNotNone(d, "未取到落在十二凶卦的流年样本")
        self.assertIn(d["liunian_hexagram"], set(G.TWELVE_XIONG_GUA))
        z = d["zhengdui_fandui"]
        self.assertEqual(len(z), len(set(z)), "正对反对条目有重复：%s" % z)
        xg = [x for x in z if "十二凶卦" in x]
        self.assertEqual(len(xg), 1, "十二凶卦应恰好一条，实得 %d：%s" % (len(xg), z))
        self.assertTrue(xg[0].startswith("流年卦"),
                        "流年卦被标成别的卦：%r" % xg[0])


class TestToDictFields(unittest.TestCase):
    """B2/B3 象曰、释义、卦气月、生月四字段曾只存在于 dataclass 上。"""

    def setUp(self):
        _, self.d = _sample_guajie()

    def test_yaoxiang_and_shiyi_present_and_nonempty(self):
        ly = self.d["liunian_yao"]
        self.assertIsNotNone(ly, "无流年爻样本")
        for k in ("xiang", "yi"):
            self.assertIn(k, ly, "流年爻缺 %s" % k)
            self.assertTrue(ly[k], "%s 补了键但值为空——等于没补" % k)

    def test_all_four_yao_templates_same_shape(self):
        for k in ("liunian_yao", "liuyue_yao", "liuri_yao", "liushi_yao"):
            v = self.d[k]
            if v is not None:
                for f in ("xiang", "yi"):
                    self.assertIn(f, v, "%s 缺 %s" % (k, f))

    def test_yebu_ye_carries_its_two_decisive_inputs(self):
        yb = self.d["liunian_ye_buye"]
        self.assertIsNotNone(yb, "无叶/不叶样本")
        for k in ("gua_qi_month", "birth_month"):
            self.assertIn(k, yb, "叶/不叶缺决定性输入 %s" % k)
        self.assertIsInstance(yb["birth_month"], int)


class TestEraProvenance(unittest.TestCase):
    """B4 era 曾被 result.input.timezone（恒 Asia/Shanghai）顶替。"""

    def test_result_carries_era(self):
        r = HeluoCanonical().calculate(JXL, "male", "午", era="shang",
                                       birth_year=1724, birth_date="1724-05-22")
        self.assertEqual(getattr(r, "era", None), "shang")

    def test_frozen_state_era_is_not_a_timezone(self):
        r = HeluoCanonical().calculate(JXL, "male", "午", era="shang",
                                       birth_year=1724, birth_date="1724-05-22")
        era = build_frozen_state(r).calculation_policy["era"]
        self.assertEqual(era, "shang")
        self.assertNotIn("/", era, "era 字段装的是时区：%r" % era)

    def test_era_field_exists_in_canonical_source(self):
        src = _src("canonical.py")
        self.assertIn("era: str = ", src, "canonical.py 无 era 字段")


class TestLiuriEvidence(unittest.TestCase):
    """B5 「每爻管5日」与逐日一爻的算法相矛盾。"""

    def test_evidence_matches_daily_step_algorithm(self):
        _, d = _sample_guajie()
        ev = "\n".join(d["evidence"])
        self.assertNotIn("每爻管5日", ev, "仍在宣称每爻管5日")
        if "流日定位" in ev:
            self.assertIn("逐日一爻", ev, "流日定位未说明逐日一爻")


class TestHuaGongLevelPervasive(unittest.TestCase):
    """B6 三级回退的 level / reduced 曾只存在于 HuaGongResult 上。"""

    def test_weak_case_level_and_reduced_reach_frozen_state(self):
        """三级回退的 level / reduced 须真的进到冻结态里。

        ⚠ 2026-10-08（**经用户显式批准**）：本用例原期望 WEAK/纳音/reduced=True，
        那出自 `SEASON_BRANCH_TO_HUAGONG` 自造近似表（未→离）。改按原典
        L558–L567 节气窗口后，1724-05-22 处小满（jq=10）落在
        L561「震卦自春分二月中以后至芒种终止」窗口内 → 当令化工卦为**震**。

        正体即见震 → level=正体、reduced=False（不属纳音末级）；
        震(木) 与其相反卦兑(金) 相克 → L582「但忌克制，尤凶」判 **KEZHI**。
        旧期望值已不成立，但它当初守的是「reduced 必须透传」这件事——
        该项由下方 test_reduced_false_is_propagated 继续守住。
        """
        r = HeluoCanonical().calculate(JXL, "male", "午", birth_year=1724,
                                       birth_date="1724-05-22")
        fs = build_frozen_state(r)
        hg = fs.to_dict()["hua_gong"]
        self.assertEqual(hg["state"], "KEZHI", hg["state"])
        self.assertEqual(hg["level"], "正体", hg["level"])
        self.assertIs(hg["reduced"], False, hg["reduced"])

    def test_reduced_false_is_propagated(self):
        """reduced=False 也必须真的落到冻结态里（旧用例顺带守的那件事）。"""
        r = HeluoCanonical().calculate(JXL, "male", "午", birth_year=1724,
                                       birth_date="1724-05-22")
        hg = build_frozen_state(r).to_dict()["hua_gong"]
        self.assertIn("reduced", hg)
        self.assertIs(hg["reduced"], False, "reduced 未透传")
        ev = HeLuoEvidenceProducer().produce(r)
        row = [e for e in ev if e.rule_id.endswith("_HUA_GONG")][0]
        self.assertIn("reduced", row.attributes)

    def test_evidence_carries_level_and_reduced(self):
        r = HeluoCanonical().calculate(JXL, "male", "午", birth_year=1724,
                                       birth_date="1724-05-22")
        ev = HeLuoEvidenceProducer().produce(r)
        hg = [e for e in ev if e.rule_id.endswith("_HUA_GONG")]
        self.assertEqual(len(hg), 1)
        self.assertIn("level", hg[0].attributes, "证据缺 level")
        self.assertIn("reduced", hg[0].attributes, "证据缺 reduced")


class TestSilentDegrade(unittest.TestCase):
    """B7/B8 加载失败与生月缺失都必须留痕。"""

    def test_jingyi_load_error_accessor_exists_and_normal(self):
        self.assertTrue(hasattr(G, "jingyi_load_error"))
        self.assertIsInstance(G.jingyi_load_error(), str)

    def test_missing_birth_month_leaves_trace(self):
        """生月由 bazi[1][1] 经 BRANCH_TO_MONTH 推出；不传 bazi 即为「缺生月」。"""
        c = HeluoCanonical()
        res = c.calculate(BAZI, "male", "午", birth_year=1983, birth_date="1983-11-03")
        g = G.build_guajie_from_result(res)          # 刻意不传 bazi
        d = g if isinstance(g, dict) else g.to_dict()
        blob = "\n".join(d["summary"]) + "\n" + "\n".join(d["evidence"])
        self.assertIn("已按正月", blob,
                      "生月漏传未留痕（判据须用兜底专用措辞，不能用「生月」二字"
                      "——叶/不叶的证据里本来就有「生月N月」）：%s" % blob[-300:])

    def test_birth_month_present_leaves_no_missing_trace(self):
        """传了 bazi 就不该出现兜底提示（否则该提示也成了空断言）。"""
        c = HeluoCanonical()
        res = c.calculate(BAZI, "male", "午", birth_year=1983, birth_date="1983-11-03")
        g = G.build_guajie_from_result(res, bazi=BAZI)
        d = g if isinstance(g, dict) else g.to_dict()
        blob = "\n".join(d["summary"]) + "\n" + "\n".join(d["evidence"])
        self.assertNotIn("已按正月", blob, "生月齐备却仍报兜底")


# ═══════════════════════════ 批次 C：伪引与授权 ═══════════════════════════
class TestProvenanceNotFake(unittest.TestCase):
    """C1 source_rule_ref 曾指向 data/rules/heluo_*.json——该处无此文件。"""

    def test_no_reference_to_nonexistent_rule_files(self):
        src = _src("evidence_producer.py")
        self.assertNotIn("data/rules/heluo_", _code("evidence_producer.py"),
                         "仍在指向不存在的规则文件")
        for n in range(101, 122):
            self.assertTrue((Path(__file__).resolve().parents[2]
                             / "data" / "rules" / ("HL-%d.json" % n)).exists(),
                            "HL-%d.json 不存在" % n)

    def test_every_emitted_rule_is_traceable(self):
        r = HeluoCanonical().calculate(BAZI, "male", "午", birth_year=1983,
                                       birth_date="1983-11-03")
        for ev in HeLuoEvidenceProducer().produce(r):
            self.assertTrue(ev.source_rule_ref.strip(),
                            "%s 出处为空" % ev.rule_id)
            self.assertFalse(ev.source_rule_ref.startswith("data/rules/heluo_"),
                             "%s 指向不存在的文件" % ev.rule_id)


class TestRuleRegistryConsistency(unittest.TestCase):
    """C2 未注册的 rule_id 曾被静默丢弃；领域映射漏登记。"""

    def test_dropped_rules_are_disclosed(self):
        c = HeluoCanonical()
        res = c.calculate(BAZI, "male", "午", birth_year=1983, birth_date="1983-11-03")
        evs = HeLuoEvidenceProducer().produce(res)
        build_diagnosis_graph(evs, [], build_frozen_state(res))
        produced = {e.rule_id for e in evs}
        unregistered = produced - set(HELUO_RULES)
        self.assertEqual(set(dropped_rules()) & unregistered, unregistered,
                         "未注册 rule_id 未被记录：%s" % dropped_rules())

    def test_every_registered_rule_has_a_domain(self):
        for rid in HELUO_RULES:
            self.assertIn(rid, RULE_DOMAIN_MAP,
                          "%s 无领域映射，会落到默认 LIFE_EVENT" % rid)

    def test_tian_di_shu_not_misfiled_as_life_event(self):
        self.assertEqual(RULE_DOMAIN_MAP["HL_TIAN_DI_SHU"], "CAREER",
                         "本命天数地数被归入 LIFE_EVENT，语义错配")

    def test_dead_rules_are_marked(self):
        """注册却从不产出的规则必须**逐条**带 TODO 标注。

        不能只查「文件里有没有 TODO」——三条里删掉一条，另外两条仍能过，
        那等于没查。必须按 rule_id 定位到它自己的那一行。

        ⚠ 2026-10-25：四条时间层规则（大运/流年/流月/流日）现已**产出证据**
          （见 ``time_layer_judgment``），故本守卫在其产出场景下不再要求
          TODO 标注。
          ⚠ 但**直调** ``HeluoCanonical.calculate()``（无 target_date）时，
            时序层只算年不算月/日 ⇒ ``HL_YUEGUA`` / ``HL_RIGUA`` 确实不产出。
            这**不是**「规则未接入」，而是「该场景本就无月/日可算」⇒
            守卫改用**带 target_date 的** adapter 路径判定（生产链路径），
            并另设一条守卫钉住「直调场景的例外」不被误当成缺陷。
        """
        from heluo_engine.adapter import HeluoAdapter
        res = HeluoAdapter().compute(
            (1983, 11, 3, 12), gender="male", target_date="2026-10-23")
        produced = {e.rule_id for e in HeLuoEvidenceProducer().produce(res)}
        src = _src("diagnosis_rule_graph.py")
        for rid in ("HL_DAYUN", "HL_LIUNIAN_GUA", "HL_YUEGUA", "HL_RIGUA"):
            if rid in HELUO_RULES and rid not in produced:
                line = [x for x in src.split("\n") if '"%s": RuleNode(' % rid in x]
                self.assertEqual(len(line), 1, "%s 定位不到唯一注册行" % rid)
                self.assertIn("TODO(证据未接入)", line[0],
                              "%s 已注册未产出却无标注：%r" % (rid, line[0]))

    def test_time_layer_rules_produce_evidence_with_target_date(self):
        """★ 四条时间层规则在**生产链路径**（带 target_date）必须产出证据。

        这是 ``test_dead_rules_are_marked`` 的**反向**守卫：防止将来
        「又变回注册了却不产出」而没人发现。
        """
        from heluo_engine.adapter import HeluoAdapter
        res = HeluoAdapter().compute(
            (1983, 11, 3, 12), gender="male", target_date="2026-10-23")
        produced = {e.rule_id for e in HeLuoEvidenceProducer().produce(res)}
        for rid in ("HL_DAYUN", "HL_LIUNIAN_GUA", "HL_YUEGUA", "HL_RIGUA"):
            with self.subTest(rule=rid):
                self.assertIn(rid, produced,
                              "%s 在生产链路径未产出证据（应已接入）" % rid)


class TestJudgmentAuthorization(unittest.TestCase):
    """C3 authorized_by 曾写死一个全仓不存在的「V13_河洛诊断规则集」。"""

    def setUp(self):
        c = HeluoCanonical()
        self.res = c.calculate(BAZI, "male", "午", birth_year=1983,
                               birth_date="1983-11-03")
        self.state = build_frozen_state(self.res)
        self.evs = HeLuoEvidenceProducer().produce(self.res)
        self.result = build_diagnosis_graph(self.evs, [], self.state)

    def test_authorized_by_points_at_real_rule_nodes(self):
        j = self.result.judgment
        if j is None:
            self.skipTest("本盘断言不足两条，本就不产生 Judgment")
        self.assertTrue(j.authorized_by.startswith("HELUO_RULES::"),
                        "授权方未指向真实注册表：%r" % j.authorized_by)
        named = {x for x in j.authorized_by.split("::", 1)[1].split(",") if x}
        real = {a.authorized_rule_id for a in self.result.assertions
                if getattr(a, "authorized_rule_id", "")}
        self.assertEqual(named, real, "授权方与实际授权规则不符")

    def test_phantom_registry_name_gone_from_source(self):
        self.assertNotIn("V13_河洛诊断规则集", _code("diagnosis_rule_graph.py"),
                         "仍在引用不存在的规则集名")


# ═══════════════════════════ 批次 D：机理清理 ═══════════════════════════
class TestMechanismCleanup(unittest.TestCase):
    def test_fake_alias_removed(self):
        """numbers.py 的 resolve_yuantang = None：名为别名、实为空值。"""
        src = _code("numbers.py")
        self.assertNotIn("resolve_yuantang = None", src,
                         "假别名仍在，误用者会拿到 None")

    def test_real_alias_importable(self):
        from heluo_engine.engines.heluo.yuan_tang import resolve_yuantang
        self.assertTrue(callable(resolve_yuantang))

    def test_tuple_actually_imported(self):
        import typing
        from heluo_engine.engines.heluo import hexagram_state as hs
        self.assertIs(typing.get_type_hints(hs.get_base_factors).get("return"),
                      typing.Tuple[float, float],
                      "Tuple 未真正导入，get_type_hints 运行时内省会失败")

    def test_jiegua_docstring_not_stale(self):
        """jiegua 文档曾称与 jiehhou「并列共存」，实际是 jiehhou 派生自它。"""
        src = _src("jiegua.py")
        self.assertNotIn("二者是两套不同体系，不互相覆盖", src,
                         "jiegua.py 文档仍称与 jiehhou 不互相覆盖，与单向依赖的实情不符")
        self.assertIn("派生自", src, "未写明 jiehhou 派生自本模块")

    def test_no_op_weight_fixes_removed(self):
        """两处恒等于无操作的权重修正必须已删除（删掉即恢复静默空转）。"""
        import inspect
        from heluo_engine.engines.heluo.interpretation import (
            RelationalInterpretationEngine as R,
        )
        body = _strip(inspect.getsource(R._compute_factor_weights))
        # 只按变量名判会被「换个名字照样是空操作」绕过，故直接禁掉任何乘法修正：
        # 权重只允许来自 FACTOR_WEIGHTS.copy()，之后只做归一化（除法）。
        self.assertNotIn("*=", body,
                         "权重里重新出现乘法修正——两处修正都是恒等于无操作的空操作：%s" % body)
        self.assertNotIn("* (1 +", body, "五行修正空操作复现")
        self.assertNotIn("* time_modifier", body, "时间衰减空操作复现")
        self.assertIn("FACTOR_WEIGHTS.copy()", body, "权重真实来源被改掉了")
        self.assertIn("/ total", body, "归一化步骤被删掉了")

    def test_interpretation_chain_cites_this_project_only(self):
        """解释链出处曾指向《协纪辨方书》等非本项目之书。"""
        src = _code("interpretation.py")
        self.assertNotIn("协纪辨方书", src, "仍引用非本项目之书作出处")
        self.assertNotIn("《河洛理数·卷之", src, "仍引用无行号的卷次伪引")


# ═══════════════════════════ 讹字留证 ═══════════════════════════
class TestErratumIsRecorded(unittest.TestCase):
    """L648「九月生人得地数多**人**数少」——讹字须留证，不得静默订正。"""

    def test_erratum_is_quoted_verbatim(self):
        src = _src("gui_ming_liu_ju.py")
        i = src.index("judge_shun_shi")
        block = src[i:i + 3000]
        self.assertIn("人数少", block, "原典讹字「人数少」未被逐字留证")

    def test_correction_is_labelled_as_correction(self):
        src = _src("gui_ming_liu_ju.py")
        i = src.index("judge_shun_shi")
        block = src[i:i + 3000]
        self.assertIn("讹", block, "未标明这是订正而非原文")


if __name__ == "__main__":
    unittest.main()