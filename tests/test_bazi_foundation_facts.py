"""P0-FNDR-11: Bazi Foundation Contract 28类 Fact 补齐 — Oracle 验证测试.

覆盖: 完整藏干 / 地支十神 / 四柱阴阳 / 十二长生 / 天干五合 / 天干相冲 /
地支六破 / 神煞体系 / 胎元 / 胎息 / 命宫 / 身宫 / 引擎版本 (Provenance),
以及时间轴事实层 (流年/流月/流日).

Oracle 来源:
- 1980-06-22 10:00 男 广州 (真太阳时 09:30:56 → 巳时), 四柱 庚申 壬午 丙寅 癸巳
- 藏干/十神/神煞/胎命身: 经典表手工推导 (见各断言注释)
- 流年/流月: ZIPING Fact API 边界 ADR 已核验契约 (2026=丙午, 立春 2026-02-04,
  惊蛰 2026-03-05, 丙年寅月=庚寅)
"""

import pytest

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.engines.time.time_axis_facts import (
    compute_liunian,
    compute_liuyue,
    compute_liuyue_all,
    compute_liuri,
)

CASE = dict(
    solar_date=(1980, 6, 22, 10),
    gender="male",
    birth_datetime=__import__("datetime").datetime(1980, 6, 22, 10, 0, 0),
)


@pytest.fixture(scope="module")
def chart():
    return BaziEngine().compute(**CASE)


@pytest.fixture(scope="module")
def d(chart):
    return chart.to_dict()


# ---------------------------------------------------------------- 四柱基线
def test_four_pillars_frozen(chart):
    """已冻结四柱不得改变 (回归锚点)."""
    assert chart.get_pillars_chinese() == {
        "year": "庚申", "month": "壬午", "day": "丙寅", "hour": "癸巳",
    }


# ---------------------------------------------------------------- 完整藏干
def test_hidden_stems_full(d):
    """四支完整藏干 (本/中/余气 + all), 单源 bazi_facts.BRANCH_HIDDEN_STEMS."""
    assert d["hidden_stems"] == {
        "year":  {"main": "GENG", "middle": "REN", "residual": "WU", "all": ["GENG", "REN", "WU"]},
        "month": {"main": "DING", "middle": "JI", "residual": None, "all": ["DING", "JI"]},
        "day":   {"main": "JIA", "middle": "BING", "residual": "WU", "all": ["JIA", "BING", "WU"]},
        "hour":  {"main": "BING", "middle": "WU", "residual": "GENG", "all": ["BING", "WU", "GENG"]},
    }


# ---------------------------------------------------------------- 地支十神
def test_branch_ten_gods(d):
    """四支藏干对日主丙火的十神 (本/中/余气 + all)."""
    assert d["branch_ten_gods"] == {
        "year":  {"main": "偏财", "middle": "七杀", "residual": "食神", "all": ["偏财", "七杀", "食神"]},
        "month": {"main": "劫财", "middle": "伤官", "residual": "", "all": ["劫财", "伤官"]},
        "day":   {"main": "偏印", "middle": "比肩", "residual": "食神", "all": ["偏印", "比肩", "食神"]},
        "hour":  {"main": "比肩", "middle": "食神", "residual": "偏财", "all": ["比肩", "食神", "偏财"]},
    }


# ---------------------------------------------------------------- 四柱阴阳
def test_stem_branch_polarity(d):
    """四柱天干/地支阴阳 (阳: 庚壬丙寅申午; 阴: 癸巳)."""
    assert d["stem_branch_polarity"] == {
        "year":  {"stem": "YANG", "branch": "YANG"},
        "month": {"stem": "YANG", "branch": "YANG"},
        "day":   {"stem": "YANG", "branch": "YANG"},
        "hour":  {"stem": "YIN", "branch": "YIN"},
    }


# ---------------------------------------------------------------- 十二长生
def test_twelve_growth(d):
    """日主丙火对四支: 申=病, 午=帝旺, 寅=长生, 巳=临官."""
    assert d["twelve_growth"] == {
        "year": "病", "month": "帝旺", "day": "长生", "hour": "临官",
    }


# ---------------------------------------------------------------- 干支关系
def test_stem_he_pairs_empty(d):
    """四干 庚壬丙癸 无五合配对 (甲己/乙庚/丙辛/丁壬/戊癸)."""
    assert d["stem_he_pairs"] == []


def test_stem_clash_pairs(d):
    """丙壬相冲命中 (甲庚/乙辛/丙壬/丁癸)."""
    assert d["stem_clash_pairs"] == [["REN", "BING"]]


def test_branch_po_pairs(d):
    """巳申六破命中 (子酉/丑辰/寅亥/卯午/巳申/未戌)."""
    assert d["branch_po_pairs"] == [["SHEN", "SI"]]


# ---------------------------------------------------------------- 神煞
def test_shensha(d):
    """日干丙: 文昌=申(丙戊申), 羊刃=午(丙午);
    年支申(申子辰局): 驿马=寅, 劫煞=巳; 华盖=辰/将星=子/亡神=亥 未现;
    天乙(丙丁猪鸡=亥酉) 未现; 金舆(丙=未) 未现; 桃花(日支寅→卯) 未现."""
    assert d["shensha"] == {
        "WEN_CHANG": ["SHEN"],
        "YANG_REN": ["WU"],
        "YI_MA": ["YIN"],
        "JIE_SHA": ["SI"],
    }


# ---------------------------------------------------------------- 胎元/胎息
def test_tai_yuan(d):
    """胎元 = 月柱壬午 → 天干进1 癸 + 地支进3 酉 = 癸酉."""
    assert d["tai_yuan"] == {"stem": "GUI", "branch": "YOU", "chinese": "癸酉"}


def test_tai_xi(d):
    """胎息 = 日柱丙寅 → 丁巳."""
    assert d["tai_xi"] == {"stem": "DING", "branch": "SI", "chinese": "丁巳"}


# ---------------------------------------------------------------- 命宫/身宫
def test_ming_gong(d):
    """命宫 (《五行精纪·起命宫例》顺数见卯): 午月(5) → 子逆数落申(8), 巳时(5) 顺数至卯 → 午; 壬午.

    验证 (三命通会·论坐命官 原例): 甲子年三月戌时 → 命宫丁卯; 本算法 L=(1-3)%12=10(戌),
    (10+(3-10)%12)%12=3(卯), 甲年五虎遁 → 丁卯 ✓ 与原例一致。
    """
    assert d["ming_gong"]["branch"] == "WU"
    assert d["ming_gong"]["stem"] == "REN"
    assert d["ming_gong"]["chinese"] == "壬午"
    assert d["ming_gong"]["algorithm"] == "WXJJ_LUN_MINGGONG_SHENGONG"


def test_shen_gong(d):
    """身宫 (《五行精纪·起身宫例》太阴星宫法): 1980-06-22 农历五月初十 → 月首宿毕(18) +9日 = 轸(27) → 巳; 辛巳.

    验证 (求太阴星约法 原例): 正月初十 → 危(11)+9=参(20), 参配申宫 ✓ 与 L3739 一致。
    """
    assert d["shen_gong"]["branch"] == "SI"
    assert d["shen_gong"]["stem"] == "XIN"
    assert d["shen_gong"]["chinese"] == "辛巳"


# ---------------------------------------------------------------- Provenance
def test_versions_present(d):
    assert d["engine_version"].startswith("bazi-engine-")
    assert d["calculation_version"].startswith("bazi-calc-")


# ---------------------------------------------------------------- 时间轴事实
def test_liunian_2026():
    """2026=丙午, 立春 2026-02-04 切换, end=次年立春前一日 (ADR 已核验)."""
    f = compute_liunian(2026)
    assert f["type"] == "LIUNIAN"
    assert f["year"] == 2026
    assert f["pillar"] == "丙午"
    assert f["gan"] == "BING" and f["zhi"] == "WU"
    assert f["start"] == "2026-02-04"
    assert f["end"] == "2027-02-03"


def test_liuyue_2026_yin():
    """丙年寅月=庚寅 (五虎遁), start=立春, end=惊蛰 (ADR 已核验)."""
    f = compute_liuyue(2026, 1)
    assert f["type"] == "LIUYUE"
    assert f["month_index"] == 1
    assert f["pillar"] == "庚寅"
    assert f["gan"] == "GENG" and f["zhi"] == "YIN"
    assert f["start"] == "2026-02-04"
    assert f["end"] == "2026-03-05"


def test_liuyue_all_2026_twelve():
    """全年 12 个月, 干支序列连续 (寅庚 → 卯辛 → … → 丑辛)."""
    months = compute_liuyue_all(2026)
    assert len(months) == 12
    assert months[0]["pillar"] == "庚寅"
    assert months[1]["pillar"] == "辛卯"
    assert months[11]["pillar"] == "辛丑"


def test_liuyue_chou_cross_year():
    """丑月跨年: 2026 丑月 = 2027-01-05(小寒) ~ 2027-02-04(立春), 辛丑."""
    f = compute_liuyue(2026, 12)
    assert f["pillar"] == "辛丑"
    assert f["start"] == "2027-01-05"
    assert f["end"] == "2027-02-04"


def test_liuri_continuity():
    """流日连续性: 相邻日期日柱 +1 (sxtwl getDayGZ 冻结验证过的同源计算)."""
    a = compute_liuri(2026, 5, 20)
    b = compute_liuri(2026, 5, 21)
    ia = __import__("tongshu.facts.bazi_facts", fromlist=["JIAZI_INDEX"])
    # 甲午 -> 乙未 必须连续
    assert a["pillar"] == "甲午"
    assert b["pillar"] == "乙未"
    assert a["gan"] == "JIA" and a["zhi"] == "WU"
    assert b["gan"] == "YI" and b["zhi"] == "WEI"


def test_nayin_60_jiazi_frozen():
    """60 甲子纳音表关键锚点 (E-SMTH-003-001 经典表, 60 组)."""
    from tongshu.facts.bazi_facts import NAYIN_60
    assert len(NAYIN_60) == 60
    assert NAYIN_60[("JIA", "ZI")] == "海中金"
    assert NAYIN_60[("GENG", "SHEN")] == "石榴木"
    assert NAYIN_60[("JIA", "WU")] == "沙中金"
    assert NAYIN_60[("REN", "XU")] == "大海水"


def test_nayin_case_19800622():
    """1980-06-22 10:00 男广州: 庚申壬午丙寅癸巳 → 石榴木/杨柳木/炉中火/长流水."""
    d = BaziEngine().compute((1980, 6, 22, 10), gender="male").to_dict()
    assert d["nayin"] == {
        "year": "石榴木", "month": "杨柳木", "day": "炉中火", "hour": "长流水",
    }
