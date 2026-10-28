"""情性/出身/地位派生测试（DTS-052/054/055，PENDING_VERIFY 结构近似）。

消费规则：CAND-DTS-057/058/088/089/090（status=PENDING 隔离）。
口径：结构事实→状态判定；禁绝对量化（覆盖≥4 为「偏枯」全集覆盖近似）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.ditiansui.calculation.state import derive_state  # noqa: E402


def test_wuxing_bu_li_qing_he():
    """五行不戾正清和：丙日主寅月 WANG，四干戊庚庚（土金=喜用），无冲、五行覆盖≥4、清。
    申午戌寅覆盖 金火土木=4 → 不戾正清和。"""
    out = derive_state(
        day_stem="丙", month_branch="寅",
        hidden={"寅": ["甲", "丙", "戊"], "戌": ["戊", "辛", "丁"],
                "申": ["庚", "壬", "戊"], "午": ["丁", "己"]},
        branches=["申", "寅", "午", "戌"],
        base={"year_stem": "戊", "month_stem": "庚", "hour_stem": "庚",
              "year_branch": "申", "month_branch": "寅", "day_branch": "午",
              "hour_branch": "戌", "stem_branch_pair": "丙午"})
    p = out["pending"]
    assert p["qing_state"] == "一清到底有精神"
    assert p["wuxing_state"] == "不戾正清和"
    assert p["rigan_state"] == "得氣"      # 得令（寅∈木火）∨得地（寅藏甲）
    assert p["geju"] == "清純"


def test_wuxing_zhuo_luan():
    """浊乱偏枯：有冲 → 戾。丙日主寅月 + 申寅冲。"""
    out = derive_state(
        day_stem="丙", month_branch="寅",
        hidden={"寅": ["甲", "丙", "戊"], "戌": ["戊", "辛", "丁"],
                "申": ["庚", "壬", "戊"], "午": ["丁", "己"]},
        branches=["申", "寅", "午", "戌"],
        base={"year_stem": "戊", "month_stem": "庚", "hour_stem": "庚",
              "year_branch": "申", "month_branch": "寅", "day_branch": "午",
              "hour_branch": "戌", "stem_branch_pair": "丙午",
              "relations": {"liu_chong": ["申", "寅"]}})
    p = out["pending"]
    assert p["wuxing_state"] == "濁亂偏枯"
    assert p["decai_relation"] == "才勝德"    # 有冲联动


def test_rigan_caixing():
    """日干得气遇才星：丙日主寅月 WANG（得气）；财=金（我克）。
    四干戊庚庚 → 庚金透 → 才星遇。"""
    out = derive_state(
        day_stem="丙", month_branch="寅",
        hidden={"寅": ["甲", "丙", "戊"], "戌": ["戊", "辛", "丁"],
                "申": ["庚", "壬", "戊"], "午": ["丁", "己"]},
        branches=["申", "寅", "午", "戌"],
        base={"year_stem": "戊", "month_stem": "庚", "hour_stem": "庚",
              "year_branch": "申", "month_branch": "寅", "day_branch": "午",
              "hour_branch": "戌", "stem_branch_pair": "丙午"})
    p = out["pending"]
    assert p["rigan_state"] == "得氣"
    assert p["caixing"] == "遇"


def test_caixing_bu_yu():
    """才星不遇：丙日主寅月，四干无财（金）透、藏干无金。"""
    out = derive_state(
        day_stem="丙", month_branch="寅",
        hidden={"寅": ["甲", "丙", "戊"], "午": ["丁", "己"]},
        branches=["寅", "寅", "午", "午"],
        base={"year_stem": "甲", "month_stem": "乙", "hour_stem": "丁",
              "year_branch": "寅", "month_branch": "寅", "day_branch": "午",
              "hour_branch": "午", "stem_branch_pair": "丙午"})
    p = out["pending"]
    assert p["caixing"] == "不遇"


def test_rensha_shen_qing():
    """刃煞神清气势恢：丙日主寅月 WANG、清；阳刃=午（丙帝旺）现于日支；
    煞=水（克丙）透干？四干戊庚庚无壬癸 → 煞不透。改用甲日主：刃=卯、煞=金（庚辛透）。
    甲日主卯月？卯∈bang（木水）→ 得令；藏干本气水/木？卯藏乙（木∈bang）→ 得地 → WANG。
    四干庚戊庚戊（金土=喜用，财官杀食伤）；忌=木水不透 → 清。"""
    out = derive_state(
        day_stem="甲", month_branch="卯",
        hidden={"卯": ["乙"], "申": ["庚", "壬", "戊"],
                "戌": ["戊", "辛", "丁"], "未": ["己", "丁", "乙"]},
        branches=["申", "卯", "戌", "未"],
        base={"year_stem": "庚", "month_stem": "戊", "hour_stem": "庚",
              "year_branch": "申", "month_branch": "卯", "day_branch": "戌",
              "hour_branch": "未", "stem_branch_pair": "甲戌"})
    p = out["pending"]
    assert out["day_strength_classic"] == "WANG"
    assert p["qing_state"] == "一清到底有精神"
    assert p["rensha_state"] == "神清氣勢恢"   # 刃（卯）现∧煞（庚金透干）∧清


def test_rensha_bu_hui():
    """刃煞不恢：刃现但煞不透（甲日主卯月，四干无庚辛金）。"""
    out = derive_state(
        day_stem="甲", month_branch="卯",
        hidden={"卯": ["乙"], "寅": ["甲", "丙", "戊"]},
        branches=["寅", "卯", "寅", "卯"],
        base={"year_stem": "戊", "month_stem": "戊", "hour_stem": "戊",
              "year_branch": "寅", "month_branch": "卯", "day_branch": "寅",
              "hour_branch": "卯", "stem_branch_pair": "甲寅"})
    p = out["pending"]
    assert p["rensha_state"] == "不恢"


def test_caiguan_he_geju():
    """财官和+格局清纯：甲日主卯月 WANG、清；财=土（我克）透、官=金（克我）透 → 和。"""
    out = derive_state(
        day_stem="甲", month_branch="卯",
        hidden={"卯": ["乙"], "申": ["庚", "壬", "戊"],
                "戌": ["戊", "辛", "丁"], "未": ["己", "丁", "乙"]},
        branches=["申", "卯", "戌", "未"],
        base={"year_stem": "庚", "month_stem": "戊", "hour_stem": "庚",
              "year_branch": "申", "month_branch": "卯", "day_branch": "戌",
              "hour_branch": "未", "stem_branch_pair": "甲戌"})
    p = out["pending"]
    assert p["caiguan"] == "和"          # 财（戊土透）∧官（庚金透）
    assert p["geju"] == "清純"


def test_isolation():
    """P-1 隔离：新字段仅 pending 可见。"""
    out = derive_state(
        day_stem="丙", month_branch="寅",
        hidden={"寅": ["甲", "丙", "戊"], "戌": ["戊", "辛", "丁"],
                "申": ["庚", "壬", "戊"], "午": ["丁", "己"]},
        branches=["申", "寅", "午", "戌"],
        base={"year_stem": "戊", "month_stem": "庚", "hour_stem": "庚",
              "year_branch": "申", "month_branch": "寅", "day_branch": "午",
              "hour_branch": "戌", "stem_branch_pair": "丙午"})
    for f in ("wuxing_state", "rigan_state", "caixing",
              "rensha_state", "caiguan", "geju"):
        assert f not in out
        assert f in out["pending"]
