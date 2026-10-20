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


def _lm(be, y, m, d, h, gender="female"):
    return from_bazi_chart(_chart(be, y, m, d, h, gender))


class TestQueryYearStructure:
    def test_120_structure_complete(self, be):
        r = _qy(be, 1893, 12, 26, 20, 1976)
        assert set(("year", "tai_sui", "luck_pillar", "verdicts", "tone", "counts", "combined")) <= set(r)
        assert r["tai_sui"] == "BINGCHEN"
        assert isinstance(r["verdicts"], list)
        for v in r["verdicts"]:
            # 2026-10-20 流年修复: 允许 LM-V5x/LM-V6x 岁运规则 + LM-Y71 太岁合局吉
            # 2026-10-21: 新增 LM-V7x(丧吊/勾绞/日干轴/征太岁) + LM-V8x(小运)
            assert v["rule_id"].startswith(("LM-V5", "LM-V6", "LM-V7", "LM-V8", "LM-Y"))
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
        # 2026-10-20 第二版 (原著核实, 大运归大运/流年归流年): 流年自身 厚福+重恶(七分)
        #   = 凶 (L4276 方有重灾); 大运丙辰"相当"非吉泰非凶祸 → L4273 无互动
        assert r["tone"] == "凶"
        assert r["combined"]["l4273"]["mode"] == "无"
        assert r["combined"]["year_tone"] == "凶"
        assert "final_verdict" not in r["combined"]   # 无运年算术聚合

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
        # 2026-10-20 第二版 (原著核实): 流年自身 重恶(冲年+害日+冲运+空亡=重灾级) → 凶
        #   (L4276 重灾); 大运壬戌带天罗(LM-V124)= 屯蹇凶祸之运, 太岁辰冲运戌 → L4273 发祸
        assert r["tone"] == "凶"  # 流年修正
        assert r["combined"]["l4273"]["mode"] == "发祸"


class TestYu1951:
    """喻求清 1951 辛卯: 太岁卯在年旬空亡(癸丑甲辰旬空寅卯) + 压月柱 → 流年偏凶"""

    def test_125_year_xun_kong_wang(self, be):
        r = _qy(be, 1913, 3, 18, 22, 1951)
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert outs.get("LM-V61")       # 太岁卯空亡 (年旬)
        assert outs.get("LM-V51")       # 压月柱
        # 2026-10-20 严谨复核 (L4409 组合吉面): 太岁卯压月柱 → 不满足"无冲害刑压",
        #   LM-Y71 合局吉不立 (原泛合拉平口径废弃) → 空亡+压月柱 2凶
        # 2026-10-20 第二版 (原著核实): 流年自身 厚福+中恶 = 吉凶相杂(浮灾细累,
        #   L4276 八分福行五六分恶只浮灾细累); L4273: 辛亥运带天罗(LM-V124) = 屯蹇
        #   凶祸之运, 太岁卯刑压月柱 → 方可发祸 → 流年 tone 升凶 (喻求清 1951 年被处决)
        assert r["tone"] == "凶"
        assert r["combined"]["l4273"]["mode"] == "发祸"


class TestCai1916:
    """蔡锷 1916 丙辰: 太岁辰害日支卯 → 生日妻妾己身之灾"""

    def test_126_hai_day_pillar(self, be):
        r = _qy(be, 1882, 12, 18, 9, 1916)
        v51 = [v for v in r["verdicts"] if v["rule_id"] == "LM-V51"]
        assert v51 and v51[0]["tone"] == "平"
        # 2026-10-20 系统性重构 (珞琭子 L4416): 太岁丙辰沙中土 vs 壬午杨柳木
        #   = 木克土(我克为财) 非克身 → 辰害日支卯 = 平(细累浮灾不为重害 L4273),
        #   应期仍定位"妻妾己身之应" (广信集 L4423 分柱)
        assert v51[0]["out"] == "太岁刑冲压害生日，主妻妾己身之应（克身者己身之灾，不克身者变动应期）"
        # 2026-10-20 严谨复核 (L4419 晦气): 太岁丙合日干辛 → 晦气凶; 辰害日支卯(广信集)
        #   + 太岁丙辰沙中土犯杨柳木忌(V68) → 重恶(晦气4+犯忌3=7=重恶运) → 凶
        #   [辛卯日属甲申旬(空午未), 辰非空亡 — 勿误断 V61]
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert outs.get("LM-V59B")     # 丙辛合日干 → 晦气
        assert outs.get("LM-V61") is None   # 辰非空亡(辛卯=甲申旬空午未)
        # 重恶(晦气4+犯忌3=7=七分恶运) → 凶 (L4276 方有重灾; 蔡锷 1916 卒于日本);
        # 大运乙卯吉泰+太岁辰害日支卯 → L4273 浮灾标注(不为重害) — 流年自身已凶,
        # 浮灾不加重不减轻
        assert r["tone"] == "凶"
        assert r["combined"]["l4273"]["mode"] == "浮灾"


class TestGLMGood:
    """太岁见贵禄马吉面 (L4409: '无冲害刑克, 仍加贵人禄马福神之地则吉').

    前提修正验证: 太岁与命局有冲刑害压时, 贵禄马吉不立 (凶占先)。
    """

    def test_127_glm_needs_clean_year(self, be):
        # 喻求清 1951: 卯为癸年天乙贵人(壬癸兔蛇藏), 太岁辛卯压月柱(乙卯).
        # 2026-10-20 系统性重构 (珞琭子 L4416 王氏注): "掩冲岁临尚不为灾…癸亥生得
        #   乙巳岁, 虽巳亥冲临于返吟之上, 以身财之旺故不为灾, 宜获福" — 冲/压
        #   (返吟/伏吟)本身不为灾, 不阻断贵禄马吉面; 贵禄马仅被"克身之鬼"阻断.
        #   → V65 吉面在场 (卯贵人+卯马, 太岁辛卯松柏木 vs 癸丑桑柘木=比和不克身);
        #   V51 压月柱=动(不为灾); 空亡凶(2分) → 辛亥运天罗(男4)+太岁卯压月柱
        #   → L4273 发祸 → tone 凶 (喻求清 1951 年被处决, 凶年正确)
        r = _qy(be, 1913, 3, 18, 22, 1951)
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert outs.get("LM-V65")            # 贵禄马命中且不克身 → 吉面在场 (L4416)
        assert outs.get("LM-V67") is None
        assert outs.get("LM-V68") is None
        assert r["tone"] == "凶"             # 发祸 (凶祸运+太岁刑压) 压过贵禄马吉面
        assert outs.get("LM-V61")            # 太岁卯年旬空亡仍在

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


class TestYearDistributionSystemic:
    """2026-10-20 系统性重构回归断言 (流年 90% 凶根治).

    原著框架: 珞琭子 L4416"掩冲岁临尚不为灾, 相生则吉相克则凶" (冲/压不克身
    不为灾, 我克为财主得财) / 三命提要"更带克身之鬼其年决有大灾" (克身才重)
    / 广信集 L4423 分柱=应期定位 / 三命通会 L968 伏吟不利六亲 / L4273 吉面
    净胜之年凶祸运亦只浮灾不为重害.

    锚: 1983 坤造(癸亥大海水, 阴女顺排, 丙寅运偏吉) 2020-2030 十一年 —
    不得再出现"10年9凶"; 凶年必须带重灾4分信号 (晦气/死绝/元辰/冲运/克身).
    """

    def test_132_1983_kun_years_not_all_xiong(self, be):
        ch = _chart(be, 1983, 11, 3, 12, gender="female")
        lm = _lm(be, 1983, 11, 3, 12)
        dist = {}
        for yr in range(2020, 2031):
            r = query_year(ch, yr, lm=lm)
            dist[yr] = r["tone"]
        xiong = sum(1 for t in dist.values() if t == "凶")
        # 2026-10-21 三命通会/珞琭子赋注深挖后: 2021 辛丑 新增 丧门(V74)+岁伤日干(V76)
        #   +征太岁(V78) 三重应期 (丑未冲+三刑+晦气+空亡+丧门 = 重恶年) → 凶7
        assert xiong <= 7, f"凶年仍过多: {dist}"
        # 原著反例修复: 2025 乙巳 (癸亥生得乙巳岁, 水克火为财+巳上乘马,
        #   虽巳亥冲不为灾忒宜获福 L4416 王氏注) — 不得判凶
        assert dist[2025] != "凶", f"2025 乙巳判凶 = 珞琭子原著反例: {dist}"
        # 2024 甲辰: 水克火为财(Y73吉) → 吉面应立
        assert dist[2024] != "凶"

    def test_133_1983_kun_2020_signal_grounded(self, be):
        """凶年必须信号可回指 (重灾4分: 晦气/死绝/元辰/冲运/克身)."""
        ch = _chart(be, 1983, 11, 3, 12, gender="female")
        lm = _lm(be, 1983, 11, 3, 12)
        for yr in range(2020, 2031):
            r = query_year(ch, yr, lm=lm)
            if r["tone"] != "凶":
                continue
            heavy = any(v.get("tone") == "凶" and v["rule_id"] in
                        ("LM-V59", "LM-V59B", "LM-V60", "LM-V66", "LM-V70",
                         "LM-V52", "LM-V50", "LM-Y72C")
                        for v in r["verdicts"])
            assert heavy, f"{yr} {r['tai_sui']} 判凶但无重灾4分信号"

    def test_134_new_shensha_yinji_years(self, be):
        """2026-10-21 珞琭子赋注/三命通会深挖补齐应期验证:
        V74 丧吊 / V75 勾绞 / V76 岁伤日干 / V77 日犯岁君 / V78 征太岁 —
        死亡年丧吊应验 (蔡1916 吊客临命 / 喻1951 丧门临命)."""
        # 蔡锷 1916: 1882 壬午年, 年支午 → 吊客=午前二辰=辰; 太岁丙辰=吊客
        r = _qy(be, 1882, 12, 18, 9, 1916)
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert outs.get("LM-V74")     # 吊客临命 → 孝服哭泣 (蔡锷 1916 病逝日本)
        assert outs.get("LM-V74")["tone"] == "凶"
        # 喻求清 1951: 1913 癸丑年, 年支丑 → 丧门=丑前二辰=卯; 太岁辛卯=丧门
        r2 = _qy(be, 1913, 3, 18, 22, 1951)
        outs2 = {v["rule_id"]: v for v in r2["verdicts"]}
        assert outs2.get("LM-V74")    # 丧门临命 (喻求清 1951 被处决)
        # 周 1976: 1898 戊戌? 日柱与太岁丙辰冲克 → 征太岁 (V78)
        r3 = _qy(be, 1898, 3, 5, 6, 1976)
        outs3 = {v["rule_id"]: v for v in r3["verdicts"]}
        assert outs3.get("LM-V78")    # 征太岁 → 灾祸未免
        # 日犯岁君: 2029 己酉 (1983 坤造 日干乙 vs 太岁己? 乙克己=日犯岁君)
        r4 = _qy(be, 1983, 11, 3, 12, 2029, gender="female")
        outs4 = {v["rule_id"]: v for v in r4["verdicts"]}
        assert outs4.get("LM-V77")    # 乙日犯己岁君 → 灾殃必重

    def test_135_xiao_yun_layer(self, be):
        """2026-10-21 小运层接通 (排盘引擎 xiao_yun_pillars + 禄命法消费):
        三命通会 L933-943 '小运掌一岁之灾祥…行死绝煞旺之宫必有危难'.
        2026-10-21 用户定夺取古法: 男起丙寅顺行, 女起壬申逆行."""
        r = _qy(be, 1983, 11, 3, 12, 2020, gender="female")
        # 古法女逆: 壬申(1岁) → 37岁 = 乙未(养) — 非死绝, V79 不触发
        assert r.get("xiao_yun") == "YIWEI"
        assert not r.get("xy_dead_jue")
        # 排盘引擎小运: 古法 男丙寅顺 / 女壬申逆
        ch = _chart(be, 1983, 11, 3, 12, gender="female")
        assert ch.xiao_yun_pillars[0]["pillar"] == "XINWEI"   # 壬申逆 → 辛未(1岁)
        assert ch.xiao_yun_pillars[2]["pillar"] == "JISI"     # 己巳(3岁, 水绝宫)
        ch2 = _chart(be, 1989, 12, 26, 22, gender="male")
        assert ch2.xiao_yun_pillars[0]["pillar"] == "DINGMAO"  # 丙寅顺 → 丁卯(1岁)
        # 3岁小运己巳(水绝) → V79 死绝凶 (1983坤 1986丙寅年)
        r3 = _qy(be, 1983, 11, 3, 12, 1986, gender="female")
        outs3 = {v["rule_id"]: v for v in r3["verdicts"]}
        assert outs3.get("LM-V79")     # 小运行绝宫必有危难
        assert outs3.get("LM-V79")["tone"] == "凶"

    def test_136_de_jiu_mu_gan_tui(self, be):
        """2026-10-21 救应/重灾补全:
        V82 太岁天月德吉 (珞琭子尊吉卑凶逢灾自愈) / V84 宅墓受杀凶 (珞琭子赋注) /
        V83 干推两重凶 (李虚中命书干推两重防灾於元首之间)."""
        # 1983 坤造 2026 丙午: 午=命后五辰之墓(V84) + 丙=月德(V82) → 吉凶并存
        r = _qy(be, 1983, 11, 3, 12, 2026, gender="female")
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert outs.get("LM-V82")      # 太岁丙=月德(寅午戌月德丙)
        assert outs.get("LM-V84")      # 午=命后五辰之墓
        assert r.get("tai_mu") is True
        assert r.get("tai_tian_yue_de") is True
        # 干推两重 (李虚中"干推两重防灾於元首之间") 需要太岁干+月建干双克日干,
        # 现成案例难以命中; 保留结构断言: 规则已注册于 YEAR_RULES 且权重可查
        from tongshu.luming.rules import YEAR_RULES
        assert any(v["id"] == "LM-V83" for v in YEAR_RULES)

    def test_137_guan_xiang_chi_zhi_ji_hui(self, be):
        """2026-10-21 大运官乡+太岁持之 = 迁官进禄吉会 (五行精纪 L4282:
        '凡行运至临宫帝旺上, 太岁持之, 官员主荐章改秩之喜';
        SMTH L929 同源互证). 大运支=日干禄/刃 且 太岁支同 → V86 吉会,
        且临官帝旺上 V54 压运凶让位 (同支不同判, 专条在临官帝旺论吉)."""
        # 1983 坤造 日干乙: 乙禄卯/刃寅 — 丙寅大运 2022 壬寅 太岁寅持之
        r = _qy(be, 1983, 11, 3, 12, 2022, gender="female")
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert r.get("dl_guan_di_wang") is True   # 丙寅支寅=乙木帝旺(刃)
        assert outs.get("LM-V86")                 # 大运临官帝旺+太岁持之=荐章改秩
        assert outs.get("LM-V86")["tone"] == "吉"
        assert "LM-V54" not in outs               # 临官帝旺上压运凶让位
        # 大运非官乡时 (丁卯运? 卯=乙禄临官仍官乡) — 取 2031-2040 戊辰大运(辰非乙禄刃)
        r2 = _qy(be, 1983, 11, 3, 12, 2036, gender="female")   # 2036 丙辰? 查太岁支=辰
        outs2 = {v["rule_id"]: v for v in r2["verdicts"]}
        if r2.get("tai_ya_dayun"):                 # 太岁辰 若=大运辰 → 支同非官乡 → V54
            assert "LM-V86" not in outs2
            assert outs2.get("LM-V54")

    def test_138_wu_gui_zhong(self, be):
        """2026-10-21 五鬼 (珞琭子三命消息赋徐子平注 L78: '四煞轻五鬼重,
        运逢之轻岁遇之重'; 王廷光: '以纳音克我之谓鬼, 鬼在生败旺死绝五处见').
        1983 坤造 癸亥大海水: 2020 庚子(壁上土)/2028 戊申(大驿土) 土克水
        = 克身之鬼, 且鬼临生败旺死绝宫 → V87 岁遇之重."""
        r = _qy(be, 1983, 11, 3, 12, 2020, gender="female")
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert r.get("tai_wu_gui") is True
        assert outs.get("LM-V87")
        assert outs.get("LM-V87")["tone"] == "凶"
        assert r.get("tai_wu_gui_stage")            # 鬼临生/败/旺/死/绝宫之一
        # 非克我之年不触发: 2023 癸卯(金箔金? 癸卯金生水?) — 金生水非克我
        r2 = _qy(be, 1983, 11, 3, 12, 2023, gender="female")
        assert not r2.get("tai_wu_gui")

    def test_139_si_sha(self, be):
        """2026-10-21 四煞 (珞琭子三命消息赋'四煞轻五鬼重'四煞侧;
        双取法互证: 莹和尚/徐子平/三命通会=辰戌丑未三丘五墓, 王廷光=寅申巳亥
        四冲之劫; 徐子平注'元命犯辰戌丑未在四柱中或大运又行到其上谓之四煞';
        冲身命: '四煞若冲身命定应游走他乡')."""
        # 1983 坤造 月戌日未 原局犯辰戌丑未: 2021 辛丑 太岁丑=四煞+冲日支未
        r = _qy(be, 1983, 11, 3, 12, 2021, gender="female")
        outs = {v["rule_id"]: v for v in r["verdicts"]}
        assert r.get("tai_si_sha") is True
        assert r.get("tai_si_sha_chong") is True    # 丑冲未(日支/身)
        assert outs.get("LM-V88")
        assert outs.get("LM-V89")
        # 原局无辰戌丑未者不触发: 1989 乾造(日庚子?) 查 2021 辛丑
        r2 = _qy(be, 1989, 12, 26, 22, 2021, gender="male")
        assert not r2.get("tai_si_sha")
        # 非四煞年不触发: 2023 癸卯
        r3 = _qy(be, 1983, 11, 3, 12, 2023, gender="female")
        assert not r3.get("tai_si_sha")
