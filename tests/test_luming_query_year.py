# -*- coding: utf-8 -*-
"""流年应期层 oracle 测试 (query_year / YEAR_RULES V50~V66).

验收点:
  1. query_year 结构完整 (tai_sui/luck_pillar/verdicts/tone/counts/combined)
  2. 岁运并临/冲年/克时/空亡/刑运/压运: 毛泽东 1976 七凶齐集 → combined 偏凶
  3. 返吟/冲年: 周恩来 1976 → combined 偏凶
  4. 空亡年日旬并查 (五行精纪 L3483 林开五命'论空亡止以年日所在'): 喻求清 1951 太岁卯
     在年旬(甲辰旬空寅卯)空亡
  5. 害日柱 (广信集分柱): 蔡锷 1916 太岁辰害日支卯 → '生日妻妾己身之灾'
"""
import datetime
import pytest

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.luming.engine import from_bazi_chart, query_year, _kong_wang_branches


@pytest.fixture(scope="module")
def be():
    return BaziEngine()


def _chart(be, y, m, d, h, gender="male"):
    return be.compute((y, m, d, h), gender=gender)


def _qy(be, y, m, d, h, qyear, gender="male"):
    chart = _chart(be, y, m, d, h, gender)
    lm = from_bazi_chart(chart)
    return query_year(chart, qyear, lm=lm)


class TestQueryYearStructure:
    def test_120_structure_complete(self, be):
        r = _qy(be, 1893, 12, 26, 20, 1976)
        assert set(("year", "tai_sui", "luck_pillar", "verdicts", "tone", "counts", "combined")) <= set(r)
        assert r["tai_sui"] == "BINGCHEN"
        assert isinstance(r["verdicts"], list)
        for v in r["verdicts"]:
            # 2026-10-20 流年修复: 允许 LM-V5x/LM-V6x 岁运规则 + LM-Y71 太岁合局吉
            assert v["rule_id"].startswith(("LM-V5", "LM-V6", "LM-Y"))
            assert v["evidence"]
            assert v["tone"] in ("吉", "动", "平", "滞", "凶")

    def test_121_scalar_and_per_pillar_verdicts(self, be):
        r = _qy(be, 1913, 3, 18, 22, 1951)
        ids = {v["rule_id"] for v in r["verdicts"]}
        assert "LM-V51" in ids          # per_pillar 分柱
        assert "LM-V61" in ids          # 空亡 scalar


class TestMao1976:
    """毛泽东 1976 丙辰: 岁运并临+冲年+克时+空亡+刑运压运 → 七凶齐集"""

    def test_122_sui_yun_bing_lin_and_signals(self, be):
        r = _qy(be, 1893, 12, 26, 20, 1976)
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert outs.get("LM-V55")       # 岁运并临 (丙辰=大运丙辰)
        # 冲年修正 (2026-10-20): 年支巳与辰不冲(辰巳地网相邻), 真冲为时支戌(辰戌冲)
        #   → 专门判定年支, 不再把"时柱冲"误判为"冲年"; 年冲 V50/V50A 均不触发
        assert outs.get("LM-V50") is None and outs.get("LM-V50A") is None
        assert any(v["rule_id"] == "LM-V51" and "时" in v["out"] for v in r["verdicts"])
        assert outs.get("LM-V59")       # 太岁克时干 (丙克庚)
        assert outs.get("LM-V61")       # 太岁至空亡 (日柱丁酉甲午旬空辰巳)
        assert outs.get("LM-V52") or outs.get("LM-V53") or outs.get("LM-V54")  # 刑/压大运
        # 2026-10-20 原著聚合重构 (L4276): 厚福+重恶(七分) → 凶; 档位措辞 凶 (替代 偏凶)
        assert r["tone"] == "凶"
        assert r["combined"]["final_verdict"] == "凶"

    def test_123_year_blank_wang_checks_both_xun(self, be):
        # 年柱癸巳(甲申旬空午未) + 日柱丁酉(甲午旬空辰巳) → 辰巳午未
        chart = _chart(be, 1893, 12, 26, 20)
        kw = _kong_wang_branches(chart)
        assert {"CHEN", "SI", "WU", "WEI"} <= set(kw)


class TestZhou1976:
    """周恩来 1976: 运 RENXU 偏吉(无risk) 但流年冲年/害日齐凶 → combined 偏凶 (吉期出凶事)"""

    def test_124_chong_nian_and_hai_day(self, be):
        r = _qy(be, 1898, 3, 5, 6, 1976)
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        # 太岁冲年 (辰冲戌): 太岁丙辰沙中土, 年命戊戌平地木, 木克土(我克=财)
        #   → L4416 我克为财不为灾 → V50A(动), V50 不触发
        assert outs.get("LM-V50A") and outs.get("LM-V50") is None
        # 太岁辰对日支卯 = 辰卯六害 → 走 LM-V51 分柱 (非返吟; 卯酉才冲)
        v51 = [v for v in r["verdicts"] if v["rule_id"] == "LM-V51" and v["target"].startswith("太岁CHEN刑冲压害日")]
        assert v51
        assert outs.get("LM-V56") is None     # 卯不被辰冲 → 不误触发返吟
        assert r["combined"]["luck_verdict"] == "偏吉"   # 运柱本身偏吉
        # 2026-10-20 原著聚合重构 (L4276/L4273): 重恶(冲年+害日+冲运+空亡=重灾级) 不因运吉降级 → 凶
        assert r["combined"]["final_verdict"] == "凶"  # 流年修正


class TestYu1951:
    """喻求清 1951 辛卯: 太岁卯在年旬空亡(癸丑甲辰旬空寅卯) + 压月柱 → 流年偏凶"""

    def test_125_year_xun_kong_wang(self, be):
        r = _qy(be, 1913, 3, 18, 22, 1951)
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert outs.get("LM-V61")       # 太岁卯空亡 (年旬)
        assert outs.get("LM-V51")       # 压月柱
        # 2026-10-20 严谨复核 (L4409 组合吉面): 太岁卯压月柱 → 不满足"无冲害刑压",
        #   LM-Y71 合局吉不立 (原泛合拉平口径废弃) → 空亡+压月柱 2凶
        # 2026-10-20 原著聚合重构 (L4276/L4273): 流年自身 厚福+中恶 = 吉凶相杂(浮灾细累,
        #   L4276 八分福行五六分恶只浮灾细累); 综合判定 辛亥运带天罗(V124) = 凶祸之运,
        #   太岁卯刑压月柱 → 方可发祸 (L4273) → final 凶 (喻求清 1951 年被处决)
        assert r["tone"] == "吉凶相杂"
        assert r["combined"]["final_verdict"] == "凶"


class TestCai1916:
    """蔡锷 1916 丙辰: 太岁辰害日支卯 → 生日妻妾己身之灾"""

    def test_126_hai_day_pillar(self, be):
        r = _qy(be, 1882, 12, 18, 9, 1916)
        v51 = [v for v in r["verdicts"] if v["rule_id"] == "LM-V51"]
        assert v51 and v51[0]["out"] == "太岁刑冲压害生日，主妻妾己身之灾"
        # 2026-10-20 严谨复核 (L4419 晦气): 太岁丙合日干辛 → 晦气凶; 辰害日支卯(广信集)
        #   + 太岁丙辰沙中土犯杨柳木忌(V68) → 三凶齐集 → 偏凶 (贴合蔡锷 1916 卒于日本)
        #   [辛卯日属甲申旬(空午未), 辰非空亡 — 勿误断 V61]
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert outs.get("LM-V59B")     # 丙辛合日干 → 晦气
        assert outs.get("LM-V61") is None   # 辰非空亡(辛卯=甲申旬空午未)
        # 2026-10-20 原著聚合重构 (L4276): 重恶(晦气4+害日3+犯忌3=10=七分恶运) → 凶
        #   (蔡锷 1916 卒于日本; 档位措辞 凶 替代 偏凶)
        assert r["tone"] == "凶"
        # combined: 重恶不因偏吉大运降级 (L4273 细累浮灾仅限刑害级, 重灾级仍报凶)
        assert r["combined"]["final_verdict"] == "凶"


class TestGLMGood:
    """太岁见贵禄马吉面 (L4409: '无冲害刑克, 仍加贵人禄马福神之地则吉').

    前提修正验证: 太岁与命局有冲刑害压时, 贵禄马吉不立 (凶占先)。
    """

    def test_127_glm_needs_clean_year(self, be):
        # 喻求清 1951: 卯为癸年天乙贵人(壬癸兔蛇藏), 但太岁卯压月柱(乙卯)
        #   → L4409 前提不满足, V65 不触发; 太岁辛卯松柏木=木, 非癸丑桑柘木之喜忌
        #   (桑柘木喜金水土火, 忌水多) → V67/V68 均不触发; 空亡+压月柱 → 流年偏凶
        r = _qy(be, 1913, 3, 18, 22, 1951)
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert outs.get("LM-V65") is None
        assert outs.get("LM-V67") is None
        assert outs.get("LM-V68") is None
        # 2026-10-20 严谨复核 (L4409 组合吉面): 太岁卯压月柱 → V65 贵禄马吉不立(凶占先),
        #   Y71 合局吉亦不立 → 空亡+压月柱 2凶 → 偏凶 (喻求清 1951 年被处决)
        assert r["tone"] == "吉凶相杂"
        assert outs.get("LM-V61")      # 太岁卯年旬空亡仍在

    def test_128_glm_clean_year_positive(self, be):
        # 蔡锷 1916: 太岁丙辰, 辰为壬年贵人? 否 (壬癸兔蛇藏); 辰非禄非马 → V65 不触发;
        #   但辰害日支卯 → 亦验证"害占先"不影响 V68 判定
        r = _qy(be, 1882, 12, 18, 9, 1916)
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert outs.get("LM-V65") is None
        assert outs.get("LM-V51")      # 害日柱凶仍在


class TestJiaoYun:
    """交运年应期 (五行精纪 L4267-4268: 阴男阳女时观出入之年;
    L4269 三命指掌: 凡阳男阳女至交运时主有灾滞)."""

    def test_129_jiao_yun_year_detected(self, be):
        # 1983-11-3 午时男 (癸亥阴男逆排): start_age=8.43
        # 交运点 8.43/18.43/28.43/38.43/48.43 → 交运年 1992/2002/2012/2022/2032
        # 边界语义: start_age+10*i 交入 luck_pillars[i] (1992=起运交入辛酉, from 为空)
        chart = _chart(be, 1983, 11, 3, 12)
        for yr, frm, to in ((1992, "", "XINYOU"), (2002, "XINYOU", "GENGSHEN"),
                            (2012, "GENGSHEN", "JIWEI"), (2022, "JIWEI", "WUWU"),
                            (2032, "WUWU", "DINGSI")):
            r = query_year(chart, yr)
            assert r["jiao_yun"] is True, yr
            assert r["jiao_yun_from"] == frm and r["jiao_yun_to"] == to, yr

    def test_130_jiao_yun_not_in_plain_year(self, be):
        chart = _chart(be, 1983, 11, 3, 12)
        r = query_year(chart, 2020)     # 非交运年 (2020 介于 2012 与 2022 之间)
        assert r["jiao_yun"] is False
        r2 = query_year(chart, 2026)
        assert r2["jiao_yun"] is False

    def test_131_jiao_yun_rule_emits_verdict(self, be):
        chart = _chart(be, 1983, 11, 3, 12)
        r = query_year(chart, 2022)
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert outs.get("LM-V69") is not None
        assert "交运" in outs["LM-V69"]["out"]
        # L4269 三命指掌"至交运时主有灾滞" → tone=滞
        assert outs["LM-V69"]["tone"] == "滞"
        # 交入戊午: from 己未(上一步) → to 戊午(当前步)
        assert r["jiao_yun_from"] == "JIWEI" and r["jiao_yun_to"] == "WUWU"


class TestYuanChen:
    """元辰之岁 (五行精纪 L4267 阴女阳男更看元辰之岁; L4270 阳男阴女
    大小运行年之元辰亦为厄会; L3346 岁运临之如物当风)."""

    def test_135_tai_yuan_chen_year(self, be):
        # 1984-2-10 巳时男 甲子阳男: 元辰=未(冲午前一位); 2027 丁未太岁支=未 → 元辰之岁凶
        chart = _chart(be, 1984, 2, 10, 10)
        r = query_year(chart, 2027)
        assert r["yuan_chen"] == "WEI"
        assert r["tai_yuan_chen"] is True
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert outs.get("LM-V70") is not None
        assert outs["LM-V70"]["tone"] == "凶"
        # 对照: 2026 丙午 太岁支午≠元辰未 → 不触发
        r2 = query_year(chart, 2026)
        assert r2["tai_yuan_chen"] is False

    def test_136_yuan_chen_gender_diff(self, be):
        # 同盘女命 1984 甲子阳女(顺行): L3345"阴男阳女在冲后一位" → 午后一位=巳
        chart = _chart(be, 1984, 2, 10, 10, gender="female")
        r = query_year(chart, 2027)
        assert r["yuan_chen"] == "SI"
        assert r["tai_yuan_chen"] is False   # 2027 太岁未 ≠ 元辰巳
        # 1983 癸亥男(阴男逆行): 亥冲巳后一位=辰; 2024 甲辰 → 元辰之岁
        chart2 = _chart(be, 1983, 11, 3, 12)
        r2 = query_year(chart2, 2024)
        assert r2["yuan_chen"] == "CHEN"
        assert r2["tai_yuan_chen"] is True
        outs = {v["rule_id"]: v for v in r2["verdicts"]}
        assert outs.get("LM-V70") is not None
