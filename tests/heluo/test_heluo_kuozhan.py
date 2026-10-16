# -*- coding: utf-8 -*-
"""H10 扩展断法测试（原著优先·K3-447《河洛理数》卷一/卷十）

覆盖：
  ① 金锁银匙歌起数（卷十·原典三例复算：2542/3347/2942）
  ② 四体八体/伏体（卷一·渐卦例）
  ③ 福力层次（卷一·论应其时合其用）
  ④ 五命得卦（卷一·五命得卦）
  ⑤ 论所得卦数吉凶·余数断（卷一 p129-130）
  ⑥ 月令非时论·四时五行盛衰（卷一 p117-119）
  ⑦ 数极京城山林（卷一·详说伏体要旨，标注级）
"""
import pytest

from src.tongshu.engines.heluo import canping as cp
from src.tongshu.engines.heluo import guajie as g


# ── ① 金锁银匙歌起数（卷十·原典三例复算） ──────────────────────

class TestQishu:
    def test_yinshu_yimao_2542(self):
        """戌日寅时，乙卯（纳音水）：2000+500+14(十1零4)+27+1=2542 ✓ 原典例"""
        r = cp.qishu("戌", "寅", "水")
        assert r["total"] == 2542
        assert (r["qian"], r["bai"], r["shi"], r["ling"]) == (2, 5, 4, 2)
        assert r["part"] == "水部"

    def test_shenshi_wuwu_3347(self):
        """申日申时，戊午（纳音火）：2000+1300+18(十1零8)+27+2=3347 ✓ 原典例"""
        r = cp.qishu("申", "申", "火")
        assert r["total"] == 3347
        assert (r["qian"], r["bai"], r["shi"], r["ling"]) == (3, 3, 4, 7)

    def test_yinshu_ni_2942(self):
        """戌日寅时逆数（乙卯水）：2000+900+14+27+1=2942 ✓ 原典例（时日顺冲还共语）"""
        r = cp.qishu("戌", "寅", "水", direction="逆")
        assert r["total"] == 2942

    def test_nayin_add_pei(self):
        """纳音加数/配数：木金虚度(0)、土+50；配数水1火2木3金4土5"""
        assert cp.NAYIN_ADD["木"] == 0 and cp.NAYIN_ADD["金"] == 0
        assert cp.NAYIN_ADD["土"] == 50 and cp.NAYIN_ADD["水"] == 27
        assert cp.NAYIN_PEI == {"水": 1, "火": 2, "木": 3, "金": 4, "土": 5}

    def test_dayun_liunian(self):
        """起大运例/起流年例：只将大运/太岁替时支，其余照前例"""
        rd = cp.qishu_dayun("戌", "卯", "水")
        rl = cp.qishu_liunian("戌", "午", "水")
        assert rd["total"] > 2000 and rl["total"] > 2000
        assert rd["total"] == cp.qishu("戌", "卯", "水")["total"]
        assert rl["total"] == cp.qishu("戌", "午", "水")["total"]


# ── ② 四体八体/伏体（卷一·渐卦例） ─────────────────────────────

class TestSitiBati:
    def test_jian_bati(self):
        """渐卦（巽上艮下）→正体巽艮/伏体震兑/互体离坎/变体（后天鼎=离上巽下）"""
        r = g.compute_siti_bati("渐", "鼎")
        assert r["zheng_ti"] == {"upper": "巽", "lower": "艮"}
        # 原典："艮有伏震，巽有伏兑"
        assert r["fu_ti"] == {"upper": "震", "lower": "兑"}
        # 原典："九五六四九三互离，六四九三六二互坎"
        assert r["hu_ti"] == {"upper": "离", "lower": "坎"}
        assert r["bian_ti"] == {"upper": "离", "lower": "巽"}

    def test_fu_li(self):
        """福力层次：本体为最；渐之反体/对体皆归妹（渐归妹互为综错）"""
        out = g.judge_fu_li("渐")
        joined = "；".join(out)
        assert "皆不若本体有之为妙耳" in joined
        assert "受兄弟子孙之福" in joined
        assert "遭变故而得安宁" in joined
        assert "虽死而有余福" in joined
        assert "反体（归妹）" in joined and "对体（归妹）" in joined


# ── ④ 五命得卦（卷一·五命得卦） ─────────────────────────────────

class TestWumingDeGua:
    def test_shui_ming_jian(self):
        """癸亥（水命）得渐（巽上艮下）：巽风起波浪秋冬可畏 / 艮山下有险为巨壑流蹇"""
        out = g.judge_wuming_de_gua("癸亥", "渐")
        joined = "；".join(out)
        assert "水命" in joined
        assert "巽风起波浪" in joined
        assert "艮山下有险" in joined

    def test_jin_ming_guan(self):
        """庚申（金命）得观（巽上坤下）：巽冷风潇潇秋冬喜遇 / 坤抱母得源多获福庆"""
        out = g.judge_wuming_de_gua("庚申", "观")
        joined = "；".join(out)
        assert "金命" in joined
        assert "巽冷风潇潇" in joined
        assert "坤抱母得源" in joined

    def test_empty_input(self):
        assert g.judge_wuming_de_gua("", "渐") == []
        assert g.judge_wuming_de_gua("甲", "渐") == []


# ── ⑤ 论所得卦数吉凶·余数断（卷一 p129-130） ────────────────────

class TestSuoshuJiXiong:
    def test_winter_odd_junzi(self):
        """冬半年（阳令）：天数>25，余奇数=君子之合象（吉）"""
        out = g.judge_suoshu_ji_xiong(29, 30, 3, 0, "winter")
        assert len(out) == 1 and "君子之合象" in out[0]

    def test_winter_even_si_light(self):
        """冬半年：余4=巽（轻）：四为巽，巽者顺也，有隐忍之心，未为甚害"""
        out = g.judge_suoshu_ji_xiong(29, 30, 4, 0, "winter")
        assert len(out) == 1 and "巽" in out[0] and "轻" in out[0]

    def test_winter_even_liu_heavy(self):
        """冬半年：余6=乾（重）：六为乾，乾者健也…遇阳年阳命犯之者必主刑伤之祸"""
        out = g.judge_suoshu_ji_xiong(31, 30, 6, 0, "winter")
        assert len(out) == 1 and "乾" in out[0] and "重" in out[0]

    def test_summer_di_yu_kun(self):
        """夏半年（阴令）：地数>30，余2=坤（原文未载轻重）：二为坤，纵有杀尚存慈母惜子之心"""
        out = g.judge_suoshu_ji_xiong(25, 32, 0, 2, "summer")
        assert len(out) == 1 and "坤" in out[0]

    def test_summer_yi_kan_heavy(self):
        """夏半年：余1=坎（重）：一为坎，坎者陷也，主陷害于人"""
        out = g.judge_suoshu_ji_xiong(25, 31, 0, 1, "summer")
        assert len(out) == 1 and "坎" in out[0] and "重" in out[0]

    def test_no_remainder(self):
        """天数25/地数30 无余 → 不断"""
        assert g.judge_suoshu_ji_xiong(25, 30, 0, 0, "winter") == []
        assert g.judge_suoshu_ji_xiong(25, 30, 0, 0, "summer") == []


# ── ⑥ 月令非时论·四时五行盛衰（卷一 p117-119） ──────────────────

class TestYueLingFeiShi:
    def test_winter_shui_sheng(self):
        """冬三月水盛：水为当时，而丰亨豫泰"""
        bazi = [("甲", "子"), ("丙", "子"), ("戊", "辰"), ("庚", "午")]
        out = g.judge_yue_ling_fei_shi(bazi, 25, 40)
        joined = "；".join(out)
        assert "冬三月" in joined
        assert "丰亨豫泰" in joined

    def test_winter_tu_sheng(self):
        """冬三月土盛：水被土制，而贫愁困苦"""
        bazi = [("甲", "子"), ("丙", "子"), ("戊", "辰"), ("庚", "辰")]
        out = g.judge_yue_ling_fei_shi(bazi, 25, 40)
        assert any("土盛" in x and "贫愁困苦" in x for x in out)

    def test_spring_huo_sheng(self):
        """春三月火盛：木去生火，为子孙昌荣"""
        bazi = [("甲", "寅"), ("丙", "寅"), ("丙", "午"), ("庚", "午")]
        out = g.judge_yue_ling_fei_shi(bazi, 30, 32)
        assert any("火盛" in x and "子孙昌荣" in x for x in out)

    def test_empty_bazi(self):
        assert g.judge_yue_ling_fei_shi([], 25, 30) == []
        assert g.judge_yue_ling_fei_shi([("甲", "子")], 25, 30) == []


# ── ⑦ 数极京城山林（标注级） ────────────────────────────────────

class TestShuJi:
    def test_not_triggered(self):
        assert g.judge_shu_ji(["正常断语"]) == []

    def test_triggered_on_jun_yao(self):
        out = g.judge_shu_ji(["后天之气数行至君爻之位，此为数足，到此必死"])
        assert len(out) == 1
        assert "京城" in out[0] and "山林" in out[0]

    def test_triggered_on_shang_ji(self):
        out = g.judge_shu_ji(["纵到君爻，亦不许行至上极一爻，寿必不久"])
        assert len(out) == 1 and "京城" in out[0]


# ── ⑧ 深度检验回归（2026-09-12：无效卦名 / 节气精确半年） ─────────

class TestDeepAudit:
    def test_invalid_gua_no_kun_false_positive(self):
        """无效卦名不得误算成坤（修复：_gua_to_lines 无效返回 None）"""
        r = g.compute_siti_bati("?", "?")
        assert r["zheng_ti"] == {"upper": "", "lower": ""}
        assert r["hu_ti"] == {"upper": "", "lower": ""}
        fl = g.judge_fu_li("?")
        assert len(fl) == 1 and "本体" in fl[0]  # 只有本体，无互/反/对体

    def test_pure_gua_siti_bati(self):
        """纯卦八体：乾→正乾乾/伏坤坤/互乾乾"""
        r = g.compute_siti_bati("乾", "坤")
        assert r["zheng_ti"] == {"upper": "乾", "lower": "乾"}
        assert r["fu_ti"] == {"upper": "坤", "lower": "坤"}
        assert r["hu_ti"] == {"upper": "乾", "lower": "乾"}
        fl = "；".join(g.judge_fu_li("乾"))
        assert "对体（坤）" in fl

    def test_solar_phase_wuzi_boundary(self):
        """节气精确半年：午月初（夏至前）仍为 winter；子月初（冬至前）仍为 summer
        （修复月支近似在 6/15、12/15 的误差）"""
        assert g._solar_phase("1980-06-15") == "winter"   # 6/15 夏至前
        assert g._solar_phase("1980-06-25") == "summer"   # 6/25 夏至后
        assert g._solar_phase("1980-12-15") == "summer"   # 12/15 冬至前
        assert g._solar_phase("1980-12-25") == "winter"   # 12/25 冬至后
        assert g._solar_phase("") == ""

    def test_solar_phase_1980_1983(self):
        """历史案例：1980-06-22 夏至后=summer；1983-11-03 立冬前=summer"""
        assert g._solar_phase("1980-06-22") == "summer"
        assert g._solar_phase("1983-11-03") == "summer"

# ── ⑨ 卷十诗断 OCR 语料检索（2026-09-12 建档） ───────────────────

class TestCanpingRawShici:
    def test_search_2542_example_poem(self):
        """金锁银匙歌 2542 例（戌日寅时乙卯水）：掌中秋月扇/举动好风生，水部 p29 丑酉列（v1 重读修正页）"""
        hits = cp.search_raw_poem("掌中秋月扇")
        assert hits and hits[0][0] == 29 and hits[0][1] == "丑酉"
        assert cp.search_raw_poem("举动好风生")

    def test_search_2942_example_poem(self):
        """金锁银匙歌 2942 例（逆数）：玉壺無別物/赤蟻似蜂屯，水部 p34 辰宾列（v1 重读修正页）"""
        hits = cp.search_raw_poem("玉壺無別物")
        assert hits and hits[0][0] == 34 and hits[0][1] == "辰宾"
        assert cp.search_raw_poem("赤蟻似蜂屯")

    def test_search_empty_and_missing(self):
        assert cp.search_raw_poem("") == []
        assert cp.search_raw_poem("zzz不存在的词") == []

    def test_search_no_false_positive(self):
        """检索不得误命中无关字（语料扩容后改用罕见字抽查；含 坤 句现已入语料）"""
        assert cp.search_raw_poem("齉") == []
        assert cp.search_raw_poem("龘") == []

    def test_search_full_corpus_hits(self):
        """全 35 页语料扩容后检索命中新部句（返回 (页, 列头, 句) 三元组；v1 重读修正列头）"""
        hits = cp.search_raw_poem("乾坤自我持")
        assert hits and hits[0][0] == 44 and hits[0][1] == "子辰" and hits[0][2] == "乾坤自我持"
        hits2 = cp.search_raw_poem("鴻毛草上風")
        assert hits2 and hits2[0][0] == 53 and hits2[0][1] == "申申" and hits2[0][2] == "鴻毛草上風"  # 2026-09-15多方校对专项②：申申号句，原误并未未列已归位

    def test_canping_dir_default(self):
        """默认语料目录可解析（data/heluo/canping/ 存在）"""
        import os
        d = os.path.join(r"D:\shuntian", "data", "heluo", "canping")
        assert os.path.exists(os.path.join(d, "raw_shici_p24-58.json"))


class TestCanpingJintu:
    """金/土部诗断语料（448_008 五部全本，v1 转录）"""

    def test_corpus_counts(self):
        """五行齐全：金部 74 + 土部 82 = 156 编号"""
        items = cp.load_raw_shici_jintu()
        assert len(items) == 156
        jin = [i for i in items if i["part"] == "jin"]
        tu = [i for i in items if i["part"] == "tu"]
        assert len(jin) == 74 and len(tu) == 82

    def test_search_jin_no(self):
        """金部编号检索：3306 → p59 鹤在白雲棲（表头页）"""
        hits = cp.search_raw_poem_448(no="3306")
        assert hits and hits[0][0] == "jin" and hits[0][1] == 59
        assert "鶴在白雲棲" in hits[0][4]

    def test_search_tu_no(self):
        """土部编号检索：3357 → p75 蜘蛛結網羅（表头页）"""
        hits = cp.search_raw_poem_448(no="3357")
        assert hits and hits[0][0] == "tu" and hits[0][1] == 75
        assert "蜘蛛結網羅" in hits[0][4]

    def test_search_dup_no_returns_all(self):
        """448 编号非唯一键：跨页异文应全部返回。
        2026-09-16 人工校原书编号带（448 p87-89 高倍）：原缩略读把四位编号读成三位，
        博浪 331->3371、隨山 372->2272、上陽 373->2373、馬陵 375->2575、象取 373->3373、
        用岳 374->2374、東山 375->3375、鴻鵠 371->2271、天涯 377->2377、雷聲 377->3377、乘桴 378->2278。
        改后唯一跨页重出 no = 273（p76 廣寒宮／p86 松筠）。"""
        hits = cp.search_raw_poem_448(no="2272", part="tu")
        assert {h[1] for h in hits} == {88}
        hits2 = cp.search_raw_poem_448(no="273", part="tu")
        assert {h[1] for h in hits2} == {76, 86}
        hits2b = cp.search_raw_poem_448(no="3771", part="tu")
        assert {h[1] for h in hits2b} == {85}
        hits2c = cp.search_raw_poem_448(no="2268", part="tu")
        assert {h[1] for h in hits2c} == {85}
        hits3 = cp.search_raw_poem_448(no="2575", part="tu")
        assert {h[1] for h in hits3} == {89}
        hits4 = cp.search_raw_poem_448(no="2271", part="tu")
        assert {h[1] for h in hits4} == {90}
        hits5 = cp.search_raw_poem_448(no="2278", part="tu")
        assert {h[1] for h in hits5} == {90}

    def test_search_keyword_in_lines(self):
        """关键字检索句文：土部 内覈 条 三三七九 含 八尺長燈檠"""
        hits = cp.search_raw_poem_448(keyword="八尺長燈檠")
        assert hits and hits[0][2] == "3379" and hits[0][1] == 91

    def test_search_part_filter(self):
        """part 过滤：jin 不含土部句"""
        hits = cp.search_raw_poem_448(keyword="河洛出圖書", part="jin")
        assert hits == []
        hits = cp.search_raw_poem_448(keyword="河洛出圖書", part="tu")
        assert hits and hits[0][0] == "tu" and hits[0][1] == 77

    def test_search_missing(self):
        """语料缺失/无命中容错"""
        assert cp.search_raw_poem_448(keyword="", no="zzz") == []
        assert cp.search_raw_poem_448(keyword="", part="xx") == []


class TestHeluoZhenshu:
    """《河洛真数》(北大藏本, 河洛真数OCR.txt) 第三来源互证回归"""

    def test_shaoxing_jialing_tiandi_shu(self):
        """河洛真数假令(绍兴四年甲寅年甲戌月己卯日壬申时)：
        天数29(奇数3+5+9+3+9)、地数48(偶数6+8+6+10+8+6+4)——引擎取数表逐字复算"""
        from src.tongshu.engines.heluo.numbers import compute_tian_di_shu
        r = compute_tian_di_shu([("甲", "寅"), ("甲", "戌"), ("己", "卯"), ("壬", "申")], "male")
        assert r.tian_shu == 29 and r.di_shu == 48
        assert r.tian_reduced == 4   # 29-25=4 → 巽
        assert r.di_reduced == 8     # 48-30=18 → 除十只用8 → 艮

    def test_shaoxing_jialing_fengshan_jian(self):
        """假令：阳命男天数卦巽在外、地数卦艮在内 → 风山渐（河洛真数原文）"""
        from src.tongshu.engines.heluo.prenatal import determine_prenatal_hexagram
        ph = determine_prenatal_hexagram(tian_reduced=4, di_reduced=8, gender="male",
                                         birth_year_yang=True)
        assert ph.hexagram_name == "风山渐"
        assert ph.upper_gua == "巽" and ph.lower_gua == "艮"

    def test_guoshi_buyong(self):
        """过十不用：十去九即用一、二十即用二、三十即用三；余18只用8"""
        from src.tongshu.engines.heluo.numbers import normalize_tian_shu, normalize_di_shu
        assert normalize_tian_shu(31) == 6     # 31-25=6
        assert normalize_di_shu(42) == 2       # 42-30=12 → 2
        assert normalize_di_shu(48) == 8       # 18 → 8
        assert normalize_tian_shu(26) == 1     # 10去9即用1
        assert normalize_di_shu(50) == 2       # 20即用2

    def test_jigong_san_dang(self):
        """遇五寄宫三档（河洛真数原文）：上元男艮女坤/中元阳男阴女艮阴男阳女坤/下元男离女兑"""
        from src.tongshu.engines.heluo.prenatal import resolve_middle_palace as rmp
        assert rmp(5, 8, "male", True, "shang") == (8, 8)      # 上元男寄艮
        assert rmp(5, 8, "female", True, "shang") == (2, 8)    # 上元女寄坤
        assert rmp(5, 8, "male", True, "zhong") == (8, 8)      # 中元阳男寄艮
        assert rmp(5, 8, "male", False, "zhong") == (2, 8)     # 中元阴男寄坤
        assert rmp(5, 8, "female", False, "zhong") == (8, 8)   # 中元阴女寄艮
        assert rmp(5, 8, "male", True, "xia") == (9, 8)        # 下元男寄离
        assert rmp(5, 8, "female", True, "xia") == (7, 8)      # 下元女寄兑

    def test_xiaoxiang_tongren_yangnian_jiunian(self):
        """小象行年(河洛真数 同人九三阳年例)：
        第1-9年卦序 = 同人/革/随/屯/复/颐/剥/蒙/蛊（逐字对照原文）"""
        from src.tongshu.engines.heluo.timeline_yun import compute_liunian
        # 天火同人 = 离下(阳阴阳→1,-1,1) + 乾上(111→1,1,1)；元堂九三 = index2；爻值 ±1（1阳/-1阴）
        res = compute_liunian(
            prenatal_lines=[1, -1, 1, 1, 1, 1], prenatal_yuantang=2,
            postnatal_lines=[1, -1, 1, 1, 1, 1], postnatal_yuantang=2,
            birth_year=1980, age_from=1, age_to=9,
        )
        names = [y.hexagram_name for y in res.years]
        assert names == ["天火同人", "泽火革", "泽雷随", "水雷屯",
                         "地雷复", "山雷颐", "山地剥", "山水蒙", "山风蛊"]


class TestLiuWeiGuiJian:
    """六位贵贱升级（起例卷之上·六位贵贱；447 主文）"""

    def test_wu_wei_jun(self):
        """五爻君位=惟五位为佳"""
        out = g.judge_liu_wei_gui_jian("九五")
        assert out and "君位" in out[0] and "惟五位为佳" in out[0]

    def test_san_wei_gongxiang(self):
        """三爻公卿节制=三四又次之（2026-09-15 定案：1632最古刻本；通行本"公乡"为形近误刻）"""
        out = g.judge_liu_wei_gui_jian("九三")
        assert out and "公卿节制" in out[0] and "三四又次之" in out[0]

    def test_chu_wei_yuanshi(self):
        """初爻庶民=初上又次之（2026-09-15 定案：1632印本/10卷本/中华典藏三源一致）"""
        out = g.judge_liu_wei_gui_jian("初九")
        assert out and "庶民" in out[0] and "初上又次之" in out[0]

    def test_empty(self):
        assert g.judge_liu_wei_gui_jian("") == []


class TestGuiMingShiTi:
    """贵命十体（起例卷之上·贵命十体）"""

    def test_tai_liu_wu_tu_ming_yin(self):
        """泰卦（卦名吉）+六五（爻吉）+辞吉+寅月顺时+土命得体+有援 → 得五六如通命"""
        out = g.judge_gui_ming_shi_ti(
            prenatal_name="泰", yuantang_yao="六五",
            yao_cis=["元吉", "凶", "凶", "凶", "凶", "凶"],
            yao_lines=[1, 1, 1, 0, 0, 0],
            birth_month_branch="寅", tian_shu=28, di_shu=24,
            year_gan="戊", year_zhi="子",
        )
        joined = "；".join(out)
        assert "①卦名吉" in joined
        assert "②爻吉" in joined
        assert "③辞吉" in joined
        assert "⑤有援" in joined
        assert "⑥顺时" in joined
        assert "⑦得体" in joined
        assert any("如通命" in o for o in out)

    def test_dang_wei_yang_yue_yang_yao(self):
        """当位：阳月（寅=冬半年阳令）元堂阳爻 ✓"""
        out = g.judge_gui_ming_shi_ti(
            prenatal_name="复", yuantang_yao="初九",
            yao_cis=[], yao_lines=[1, 0, 0, 0, 0, 0],
            birth_month_branch="寅", year_gan="甲", year_zhi="子",
        )
        assert any("⑧当位" in o for o in out)

    def test_he_li_jin_ming_kun_gen(self):
        """合理：金命见坤艮（土生金）✓"""
        out = g.judge_gui_ming_shi_ti(
            prenatal_name="坤", yuantang_yao="六五",
            yao_cis=[], yao_lines=[0, 0, 0, 0, 0, 0],
            birth_month_branch="午", year_gan="庚", year_zhi="申",
        )
        assert any("⑨合理" in o for o in out)

    def test_zhong_zong_yi_yang_wu_yin(self):
        """众宗：元堂一阳为五阴所宗（复卦初九）✓"""
        out = g.judge_gui_ming_shi_ti(
            prenatal_name="复", yuantang_yao="初九",
            yao_cis=[], yao_lines=[1, 0, 0, 0, 0, 0],
            birth_month_branch="午", year_gan="庚", year_zhi="申",
        )
        assert any("⑩众宗" in o for o in out)

    def test_empty(self):
        assert g.judge_gui_ming_shi_ti(prenatal_name="") == []


class TestJianMingShiTi:
    """贱命十体（起例卷之上·贱命十体：皆与十贵相反）"""

    def test_duo_jian_ti_duan(self):
        """构造贱体密集命中：非示例卦+元堂初爻+辞凶+夏月不得时+无援+不得体+位不当 → 僧道九流/吏僧孤独"""
        out = g.judge_jian_ming_shi_ti(
            prenatal_name="剥", yuantang_yao="初六",
            yao_cis=["凶", "凶", "凶", "凶", "凶", "凶"],
            yao_lines=[0, 0, 0, 0, 0, 1],
            birth_month_branch="午", tian_shu=20, di_shu=35,
            year_gan="庚", year_zhi="申",
        )
        joined = "；".join(out)
        assert "贵体取反" in out[0]
        assert "①卦名凶" in joined
        assert "②爻位凶" in joined
        assert "③辞凶" in joined
        assert "④不得时" in joined
        assert "⑤无援" in joined

    def test_jian_fenji(self):
        """得 3-4 贱体 → 僧道九流之命"""
        out = g.judge_jian_ming_shi_ti(
            prenatal_name="剥", yuantang_yao="初六",
            yao_cis=["凶", "凶", "凶", "凶", "凶", "凶"],
            yao_lines=[0, 0, 0, 0, 0, 1],
            birth_month_branch="午", tian_shu=20, di_shu=35,
            year_gan="庚", year_zhi="申",
        )
        assert any("僧道九流" in o for o in out) or any("吏僧孤独" in o for o in out)


class TestYaoCiBiLi:
    """吉凶爻辞比例断命（起例卷之上）"""

    def test_quan_ji(self):
        out = g.judge_yao_ci_bi_li(["元吉", "亨利", "贞吉", "利见大人", "无咎", "吉"])
        assert out and "全吉" in out[0] and "富贵高寿" in out[0]

    def test_quan_xiong(self):
        out = g.judge_yao_ci_bi_li(["凶", "厉", "悔", "咎", "危", "灾"])
        assert out and "全凶" in out[0] and "贫贱夭寿" in out[0]

    def test_xiong_duo_ji_shao(self):
        out = g.judge_yao_ci_bi_li(["吉", "凶", "凶", "凶", "凶", "凶"])
        assert out and "凶多吉少" in out[0] and "僧道九流" in out[0]

    def test_ji_duo_xiong_shao(self):
        out = g.judge_yao_ci_bi_li(["吉", "吉", "吉", "吉", "凶", "凶"])
        assert out and "吉多凶少" in out[0] and "浊富" in out[0]

    def test_empty(self):
        assert g.judge_yao_ci_bi_li([]) == []
        assert g.judge_yao_ci_bi_li(None) == []


class TestXiangShengWeiFu:
    """相生为福·得体·得局生气表（起例卷之上 L161/L235）"""

    def test_mu_ming_de_zhen_detihuo_deju(self):
        """木命得震：得局（木人得震巽为得局）"""
        out = g.judge_xiang_sheng_wei_fu("震", "甲", "子")
        joined = "；".join(out)
        assert "木命" in joined
        assert "得局" in joined and "震" in joined

    def test_jin_ming_de_kun_heli(self):
        """金命得坤：得局（金人得乾兑艮坤）"""
        out = g.judge_xiang_sheng_wei_fu("坤", "庚", "子")
        assert any("得局" in o for o in out)

    def test_shui_ming_de_kan_shengqi(self):
        """水命得坎：得局（水人得乾兑坎）；木命得坎=生气（坎为生气）"""
        out = g.judge_xiang_sheng_wei_fu("坎", "壬", "子")
        assert any("得局" in o for o in out)
        out2 = g.judge_xiang_sheng_wei_fu("坎", "甲", "子")
        assert any("生气" in o for o in out2)

    def test_tu_ming_de_kun_deti(self):
        """土命得坤：得体（土人得坤艮，皆为得体）"""
        out = g.judge_xiang_sheng_wei_fu("坤", "戊", "子")
        assert any("得体" in o for o in out)

    def test_huo_ming_weizai(self):
        """火人命局生气原文未载 → 标注不作硬断（火命得坎：不得体、得局生气未载）"""
        out = g.judge_xiang_sheng_wei_fu("坎", "丙", "子")
        joined = "；".join(out)
        assert "火" in joined and ("未载" in joined or "均未命中" in joined)


class TestYunLiunianShuFan:
    """运反+流年反+数反（起例卷之上·元气化工有无论）"""

    def test_san_fan_buke_bao(self):
        out = g.judge_yun_liunian_shu_fan(yun_fan=True, liunian_fan=True, shu_fan=True)
        assert out and "不可保" in out[1]

    def test_liunian_fan_only(self):
        out = g.judge_yun_liunian_shu_fan(liunian_fan=True)
        assert out and "不为害" in out[1]

    def test_gua_info_in_head(self):
        """接驳后头行含大运/流年卦名与虚岁"""
        out = g.judge_yun_liunian_shu_fan(
            yun_fan=True, liunian_fan=True, shu_fan=True,
            dayun_gua="遁", liunian_gua="乾", age_now=47)
        assert "大运卦遁" in out[0] and "流年卦乾" in out[0] and "虚岁47" in out[0]

    def test_empty(self):
        assert g.judge_yun_liunian_shu_fan() == []


class TestYunLiunianFanJudge:
    """运反/流年反判据（L200 化工元气相反口径，2026-09-12 接驳）"""

    def test_gua_has_yuanqi_jin_ming_qian_dui(self):
        """金音人（甲子海中金）得乾（金体）→ 元气（原典：金音人得乾兑之卦）"""
        assert g._gua_has_yuanqi("乾", "甲", "子") is True

    def test_gua_has_yuanqi_sheng_wo(self):
        """卦体生纳音：癸亥（大海水）命得乾（金生水）→ 有元气"""
        assert g._gua_has_yuanqi("乾", "癸", "亥") is True

    def test_gua_has_yuanqi_mu_ming_qian_wu(self):
        """庚申（石榴木）命得乾（金体，金不生木）→ 无元气"""
        assert g._gua_has_yuanqi("乾", "庚", "申") is False

    def test_yun_liunian_fan_mu_ming_qian(self):
        """木命得乾：无化工（乾非化工卦）且无元气 → 反"""
        fan, ev = g._yun_liunian_fan("乾", "庚", "申")
        assert fan is True
        assert any("化工=无" in e and "元气=无" in e for e in ev)

    def test_yun_liunian_fan_shui_ming_dayou(self):
        """水命得大有（乾离）：含乾金生水 → 元气有 → 不反"""
        fan, ev = g._yun_liunian_fan("大有", "癸", "亥")
        assert fan is False

    def test_yun_liunian_fan_no_gua(self):
        assert g._yun_liunian_fan("", "庚", "申") == (False, [])


class TestXianTianHouTianYuanQi:
    """先天后天元气有无（起例卷之上·元气化工有无论）"""

    def test_ju_you(self):
        out = g.judge_xian_tian_hou_tian_yuan_qi(xiantian_yq=True, houtian_yq=True)
        assert out and "功名富贵福寿" in out[0]

    def test_you_wu(self):
        out = g.judge_xian_tian_hou_tian_yuan_qi(xiantian_yq=True, houtian_yq=False)
        assert out and "先富贵而后贫贱" in out[0]

    def test_wu_you(self):
        out = g.judge_xian_tian_hou_tian_yuan_qi(xiantian_yq=False, houtian_yq=True)
        assert out and "先贫贱而后富贵" in out[0]

    def test_ju_wu(self):
        out = g.judge_xian_tian_hou_tian_yuan_qi(xiantian_yq=False, houtian_yq=False)
        assert out and "贫穷困苦夭死" in out[0]


class TestStructureKuozhan:
    """解卦层「原文+精义/释义」结构化映射（2026-09-13）"""

    def test_meta_full_13(self):
        assert set(g.KUOZHAN_META.keys()) == {
            "siti_bati", "fu_li", "wuming_de_gua", "suoshu_ji_xiong",
            "yue_ling_fei_shi", "shu_ji", "liu_wei_gui_jian",
            "gui_ming_shi_ti", "jian_ming_shi_ti", "yao_ci_bi_li",
            "xiang_sheng_wei_fu", "yun_liunian_shu_fan",
            "xian_tian_hou_tian_yuan_qi",
        }
        for name, meta in g.KUOZHAN_META.items():
            assert meta.get("origin") and meta.get("source") and meta.get("level"), name

    def test_structure_kuozhan_origin(self):
        kz = {"liu_wei_gui_jian": ["六位贵贱：元堂居九三（公卿节制）"], "unknown_item": ["x"]}
        out = {it["name"]: it for it in g.structure_kuozhan(kz)}
        assert "初为庶民" in out["liu_wei_gui_jian"]["origin"]
        assert out["liu_wei_gui_jian"]["level"] == "原典明文"
        assert out["unknown_item"]["text"] == "x"
        assert "origin" not in out["unknown_item"]

    def test_to_structured_life_timing_warnings(self):
        gj = {
            "kuozhan": {"gui_ming_shi_ti": ["得5体：如通命"]},
            "liunian_yao": {"yao": "六五", "ci": "豮豕之牙，吉。",
                            "shao": "五居君位…吉而有庆。", "ye": "叶", "buye": "不叶", "suiyun": "岁运"},
            "si_duan": ["死断：数足必死"],
            "zhengdui_fandui": ["正对反对：命卦与流年卦反对"],
            "shu_xiong": {"shu_xiong": True, "tian_shu": 29, "di_shu": 32, "pattern": "太过有余"},
            "nayin_yuanqi": [], "jiehua_gong": [], "summary": ["综"],
        }
        st = g.to_structured(gj)
        assert st["life"][0]["name"] == "gui_ming_shi_ti"
        assert "一卦名吉" in st["life"][0]["origin"]
        assert st["life"][0]["source"] == "起例卷之上·贵命十体 L209-224"
        assert st["timing"]["liunian"]["origin"] == "豮豕之牙，吉。"
        assert "吉而有庆" in st["timing"]["liunian"]["yiyi"]
        assert any("数凶" in w["text"] and "太过有余" in w["text"] for w in st["warnings"])
        assert any("死断" in w["text"] for w in st["warnings"])
        assert any("正对反对" in w["text"] for w in st["warnings"])



class TestPolarityMapping:
    """词汇映射器 B：极性标注 + 维度归类（2026-09-13，确定性词表）"""

    def test_polarity_cases(self):
        cases = [
            ("数足必死，有阴骘者延九年", "警示"),
            ("吉多凶少者浊富之人也", "吉"),
            ("凶多吉少者僧道九流", "凶"),
            ("无咎", "平"),
            ("虽流年数不吉不为害", "平"),
            ("纵有杀尚存慈母惜子之心", "平"),
            ("后天之气数行至君爻五爻，数足必死", "警示"),
        ]
        for txt, exp in cases:
            assert g.polarity_of(txt) == exp, (txt, g.polarity_of(txt), exp)

    def test_dimension_full_13(self):
        """13 项断法维度全覆盖且非'其他'"""
        names = set(g.KUOZHAN_DIMENSION.keys())
        assert names == set(g.KUOZHAN_META.keys())
        for n in names:
            assert g.dimension_of(n) != "其他", n

    def test_structure_kuozhan_polarity(self):
        kz = {"gui_ming_shi_ti": ["得5体：如通命"], "jian_ming_shi_ti": ["得3贱体：僧道九流"]}
        out = {it["name"]: it for it in g.structure_kuozhan(kz)}
        assert out["gui_ming_shi_ti"]["polarity"] == "吉"
        assert out["gui_ming_shi_ti"]["dimension"] == "官贵"
        assert out["jian_ming_shi_ti"]["polarity"] == "凶"

    def test_to_structured_warnings_polarity(self):
        gj = {"si_duan": ["数足必死"], "zhengdui_fandui": [], "shu_xiong": None,
              "kuozhan": {}, "nayin_yuanqi": [], "jiehua_gong": [], "summary": []}
        st = g.to_structured(gj)
        assert st["warnings"][0]["polarity"] == "警示"
