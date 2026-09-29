"""test_bazi_spec_l0 — L0 裁决 (2026-09-14) 投影层 Fact 边界测试.

依据: 桌面《八字排盘.txt》(SHA-1 16c958d) + 知识工程 V2.2.2 分层 (L0=Fact Root)。
覆盖:
- 判断字段已移出 L0 (rizhu_wangshuai/de_ling/de_di/de_shi/han_nuan/zao_shi)
- 新增: pillars 聚合 / 命宫胎元身宫胎息 / 上下节时刻 / 经纬度 /
        大运公历区间(T1) / 流时 / 伏吟反吟(双口径) / 支级引动 /
        旺衰·寒暖原始数据 / 量化口径标注 / provenance
- 回归: wuxing_score 数值不变, 时间层仍输出
"""

from datetime import datetime

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.engines.bazi_engine_spec import build_spec_output

CASE = (1980, 6, 22, 10)  # 庚申 壬午 丙寅 癸巳
NOW = datetime(2026, 9, 14, 12, 0, 0)

JUDGMENT_FIELDS = ("rizhu_wangshuai", "de_ling", "de_di", "de_shi", "han_nuan", "zao_shi")


def _out():
    chart = BaziEngine().compute(CASE, gender="male")
    return build_spec_output(chart, current_datetime=NOW)


# ---------------------------------------------------------------- A: 判断字段移出 L0
def test_judgment_fields_removed_from_l0():
    out = _out()
    leaked = [k for k in JUDGMENT_FIELDS if k in out]
    assert leaked == [], f"判断字段泄漏进 L0: {leaked}"

# ---------------------------------------------------------------- 第1组: pillars 聚合
def test_pillars_unified_structure():
    out = _out()
    p = out["pillars"]
    assert p["year"] == {"stem": "GENG", "branch": "SHEN"}
    assert p["month"] == {"stem": "REN", "branch": "WU"}
    assert p["day"] == {"stem": "BING", "branch": "YIN"}
    assert p["hour"] == {"stem": "GUI", "branch": "SI"}
    # 散字段保留 (兼容)
    assert out["year_gan"] == "GENG" and out["hour_zhi"] == "SI"


# ---------------------------------------------------------------- C: 命宫/胎元/身宫/胎息
def test_ming_tai_shen_fields_present():
    out = _out()
    # 2026-09-14 取证裁决 (以《五行精纪》为基准): 命宫顺数见卯, 身宫太阴星宫法
    assert out["ming_gong"]["chinese"] == "壬午"
    assert out["ming_gong"]["algorithm"] == "WXJJ_LUN_MINGGONG_SHENGONG"
    assert out["tai_yuan"]["chinese"] == "癸酉"
    assert out["shen_gong"]["chinese"] == "辛巳"
    assert out["tai_xi"]["chinese"] == "丁巳"


# ---------------------------------------------------------------- D2: 上下节名称+时刻
def test_prev_next_jieqi_moment_level():
    out = _out()
    assert out["prev_jieqi_name"] == "芒种"
    assert out["next_jieqi_name"] == "小暑"
    assert out["prev_jieqi_time"].startswith("1980-06-05")
    assert out["next_jieqi_time"].startswith("1980-07-07")
    # 时刻级 (含时分), 非日级
    assert len(out["prev_jieqi_time"].split("T")[1]) >= 5


# ---------------------------------------------------------------- D3: 经纬度
def test_longitude_latitude_default_none():
    out = _out()
    assert out["longitude"] is None
    assert out["latitude"] is None


# ---------------------------------------------------------------- D1/T1: 大运公历区间
def test_dayun_intervals_gregorian():
    out = _out()
    assert len(out["dayun_list"]) == 10
    first = out["dayun_list"][0]
    assert first["start_age"] == 4.96  # 出生到小暑实历14.9天÷3 (折除实历)
    # 交运时刻 = 出生 + start_age×360日 (《五行精纪》卷33 折除口径, 非旧"到节天数")
    assert first["start_date"] == "1985-05-14"
    assert first["end_date"] == "1995-05-14"
    # 每步递增 10 年
    assert out["dayun_list"][1]["start_date"] == "1995-05-14"
    assert out["dayun_list"][1]["end_date"] == "2005-05-14"


# ---------------------------------------------------------------- D4: 流时
def test_liushi_hour_pillar():
    out = _out()
    assert out["liushi"]["gan"] == "JIA"
    assert out["liushi"]["zhi"] == "WU"


# ---------------------------------------------------------------- D5: 伏吟反吟 (双口径)
def test_fuyin_fanyin_dual_base():
    out = _out()
    ff = out["fuyin_fanyin"]
    assert set(ff.keys()) == {"nianzhi_base", "rizhu_base", "provenance"}
    for base in ("nianzhi_base", "rizhu_base"):
        assert set(ff[base].keys()) == {"dayun", "liunian", "liuyue", "liuri"}
        for obj in ff[base].values():
            assert {"object", "gan", "zhi", "fuyin", "fanyin"} <= set(obj.keys())
    assert "神峰通考" in ff["provenance"]["nianzhi_base"]
    assert "滴天髓" in ff["provenance"]["rizhu_base"]


# ---------------------------------------------------------------- D6: 支级引动
def test_zhi_relations_per_branch():
    out = _out()
    rel = out["zhi_relations_per_branch"]
    assert set(rel.keys()) == {"SHEN", "WU", "YIN", "SI"}
    # 申与寅冲 (对冲互见)
    kinds_shen = {x["kind"] for x in rel["SHEN"]}
    assert "liuchong" in kinds_shen
    kinds_yin = {x["kind"] for x in rel["YIN"]}
    assert "liuchong" in kinds_yin
    # 每个条目都有 kind+target
    for b, items in rel.items():
        for it in items:
            assert {"kind", "target"} <= set(it.keys())


# ---------------------------------------------------------------- D7: 日主关系原始数据 (raw 审计后)
def test_day_master_relations_raw_facts():
    out = _out()
    raw = out["day_master_relations_raw"]
    # 审计: 键名零判断词 (de_ling/de_di/de_shi 已去)
    assert {"month", "roots", "stems", "provenance"} == set(raw.keys())
    # 月支: 午火, 丙火日主比和
    assert raw["month"]["branch"] == "WU"
    assert raw["month"]["branch_vs_day_master"] == "比和"
    assert ("DING", "比和") in [(h["stem"], h["relation_to_day_master"]) for h in raw["month"]["hidden_stems"]]
    assert ("JI", "我生") in [(h["stem"], h["relation_to_day_master"]) for h in raw["month"]["hidden_stems"]]
    # 日主之根: 午中丁 / 寅中丙 / 巳中丙
    assert len(raw["roots"]) == 3
    # 天干关系: 生克与十神自洽 (偏财=我克, 七杀=克我)
    shi = {s["stem"]: s for s in raw["stems"]}
    assert shi["GENG"]["ten_god"] == "偏财" and shi["GENG"]["element_relation"] == "我克"
    assert shi["REN"]["ten_god"] == "七杀" and shi["REN"]["element_relation"] == "克我"
    assert shi["GUI"]["ten_god"] == "正官" and shi["GUI"]["element_relation"] == "克我"


# ---------------------------------------------------------------- D8: 季节事实 (raw 审计后)
def test_season_facts():
    out = _out()
    s = out["season_facts"]
    assert s == {
        "month_branch": "WU",
        "season": "SUMMER",
        "provenance": "季节归类为 L0 事实; 调候用神见《穷通宝鉴》论, 属 L2D",
    }


# ---------------------------------------------------------------- 最终裁决三: raw 判断词零泄漏
def test_raw_zero_judgment_words():
    """raw 只含 Fact 分类: 键名与文本不得出现判断词."""
    out = _out()
    bad_words = ("de_ling", "de_di", "de_shi", "han_nuan", "zao_shi",
                 "wangshuai", "得令", "失令", "身强", "身弱", "旺衰",
                 "寒", "暖", "燥", "湿")

    def scan(obj, path=""):
        found = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if any(w in str(k) for w in bad_words):
                    found.append(path + "/" + str(k))
                found += scan(v, path + "/" + str(k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                found += scan(v, path + f"[{i}]")
        return found

    raw = {k: out[k] for k in ("day_master_relations_raw", "season_facts")}
    assert scan(raw) == [], f"raw 泄漏判断词: {scan(raw)}"


# ---------------------------------------------------------------- B: 量化口径标注
def test_quantification_notes():
    out = _out()
    q = out["quantification_notes"]
    assert set(q.keys()) == {"canggan_weight", "dayun_interval"}
    assert q["canggan_weight"]["algorithm"].startswith("ENGINE_DEFINED")


# ---------------------------------------------------------------- D9: Provenance
def test_provenance_present():
    out = _out()
    p = out["provenance"]
    assert p["engine_version"].startswith("bazi-engine-")
    assert p["calculation_version"].startswith("bazi-calc-")
    assert "E-YHZP-040" in p["shensha"]
    assert "五行精纪" in p["ming_gong"]


# ---------------------------------------------------------------- 回归保护
def test_wuxing_score_moved_to_ui_layer():
    """最终裁决: wuxing_score/ratio/shishen_score 下移 UI 层, L0 只留纯计数."""
    out = _out()
    assert "wuxing_score" not in out
    assert "wuxing_ratio" not in out
    assert "shishen_score" not in out
    assert out["wuxing_count"] == {"WOOD": 1, "FIRE": 3, "EARTH": 0, "METAL": 2, "WATER": 2}
    assert out["shishen_count"] != {}


# ---------------------------------------------------------------- 最终裁决一: 小运 scope
def test_xiaoyun_scope_male_verified():
    """男命: 丙寅起顺行一位一年, SOURCE_VERIFIED(SMTH_0244), 只出 Fact."""
    out = _out()
    xy = out["xiaoyun_scope"]
    assert xy["scope"] == "xiaoyun"
    assert xy["status"] == "SOURCE_VERIFIED"
    assert xy["algorithm"] == "SOURCE_VERIFIED(WXJJ_V33_论小运)"
    assert xy["start_pillar"] == {"gan": "BING", "zhi": "YIN"}
    assert xy["direction"] == "forward"
    # 2026-09-14 时 46 周岁 → 丙寅顺推45位 = 辛亥
    cur = xy["current"]
    assert cur["age"] == 46
    assert cur["gan"] == "XIN" and cur["zhi"] == "HAI"
    assert cur["shishen"]["gan"] == "正财"  # 辛金 vs 丙火日主
    assert set(cur["relations_with_natal"].keys()) == {
        "liuhe", "liuchong", "sanhe", "banhe", "sanxing",
        "liuchuan", "liupo", "liujue", "anhe", "gan_wuhe", "gan_chong"}
    # 序列: 1岁丙寅, 2岁丁卯, 3岁戊辰
    seq = {s["age"]: (s["gan"], s["zhi"]) for s in xy["sequence"]}
    assert seq[1] == ("BING", "YIN")
    assert seq[2] == ("DING", "MAO")
    assert seq[3] == ("WU", "CHEN")


def test_xiaoyun_scope_female_verified():
    """女命: 壬申逆行 (《五行精纪》卷33 四方一致定案, 取代三命通会丙申异文)."""
    from tongshu.engines.bazi_engine import BaziEngine
    chart = BaziEngine().compute(CASE, gender="female")
    xy = build_spec_output(chart, current_datetime=NOW)["xiaoyun_scope"]
    assert xy["status"] == "SOURCE_VERIFIED"
    assert xy["start_pillar"] == {"gan": "REN", "zhi": "SHEN"}
    assert xy["direction"] == "backward"
    cur = xy["current"]
    assert cur["age"] == 46
    assert cur["gan"] == "DING" and cur["zhi"] == "HAI"  # 壬申逆推45位
    seq = {s["age"]: (s["gan"], s["zhi"]) for s in xy["sequence"]}
    assert seq[1] == ("REN", "SHEN")
    assert seq[2] == ("XIN", "WEI")
    assert seq[3] == ("GENG", "WU")


def test_time_axis_facts_six_scopes():
    """裁决四: time_axis_facts 接入, 只出 Fact, 六 scope 独立."""
    out = _out()
    taf = out["time_axis_facts"]
    assert set(taf.keys()) == {"natal", "dayun", "liunian", "liuyue", "liuri", "liushi"}
    # natal 四柱
    assert taf["natal"]["scope"] == "natal"
    assert taf["natal"]["pillars"]["day"] == {"gan": "BING", "zhi": "YIN"}
    # dayun: 2026-09-14 处于丁亥大运 (2025-05-14 → 2035-05-14, 折除实历交运)
    d = taf["dayun"]
    assert d["gan"] == "DING" and d["zhi"] == "HAI"
    assert d["start_date"] == "2025-05-14" and d["end_date"] == "2035-05-14"
    assert d["start_age"] == 44.96 and d["end_age"] == 54.96
    assert d["shishen"]["gan"] == "劫财"
    assert set(d["relations_with_natal"].keys()) == {
        "liuhe", "liuchong", "sanhe", "banhe", "sanxing",
        "liuchuan", "liupo", "liujue", "anhe", "gan_wuhe", "gan_chong"}
    # 流年 2026 = 丙午
    assert taf["liunian"]["gan"] == "BING" and taf["liunian"]["zhi"] == "WU"
    assert "relations_with_dayun" in taf["liunian"]
    # 逐层递进关系
    assert "relations_with_liunian" in taf["liuyue"]
    assert "relations_with_liuyue" in taf["liuri"]
    assert "relations_with_liuri" in taf["liushi"]
    # 铁律: 各 scope 零判断字段
    for scope in taf.values():
        for key in ("wangshuai", "geju", "xiyong", "judgment"):
            assert key not in scope, f"{scope['scope']} 泄漏判断字段 {key}"


def test_time_layer_still_outputs_current_values():
    out = _out()
    assert out["liunian_gan"] == "BING" and out["liunian_zhi"] == "WU"  # 2026 = 丙午
    assert out["dayun_gan"] != ""  # 当前大运存在
