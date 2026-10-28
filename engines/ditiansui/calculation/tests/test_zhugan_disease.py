"""柱内关系/疾病五行受制测试（DTS-010-012/014、DTS-053-009/012，PENDING_VERIFY）。

消费规则：CAND-DTS-016/017/078/079/084/085（status=PENDING 隔离）。
登记不实现：007/008 branch 粒度缺陷、010/011 冲旺衰、062-067 方位流向/顺逆生。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.ditiansui.calculation.state import derive_state  # noqa: E402


def test_pillar_di_sheng_tian():
    """地生天：甲子日柱——子水（水）生日干甲（木）→ 地生天。
    甲日主申月 SHUAI（申金∉木水bang不得令、无得地得势）→ 天衰。"""
    out = derive_state(
        day_stem="甲", month_branch="申",
        hidden={"子": ["癸"], "申": ["庚", "壬", "戊"],
                "戌": ["戊", "辛", "丁"], "未": ["己", "丁", "乙"]},
        branches=["戌", "申", "子", "未"],
        base={"year_stem": "庚", "month_stem": "辛", "hour_stem": "戊",
              "year_branch": "戌", "month_branch": "申", "day_branch": "子",
              "hour_branch": "未", "stem_branch_pair": "甲子"})
    p = out["pending"]
    assert p["pillar_relation"] == "地生天"
    assert p["day_master_strength"] == "衰"      # SHUAI → WEAK → 天衰
    assert p["branch_strength"] == "不旺"         # 子水≠申金月令


def test_pillar_tian_he_di():
    """天合地：甲己合——甲日主坐未（未藏己）→ 天合地。
    甲日主午月？午=火∉木水bang不得令；午藏丁（火∉bang）无得地；四干无木水透→无得势→SHUAI。
    地旺：午≠午月令？月支午==日支午 → 旺。"""
    out = derive_state(
        day_stem="甲", month_branch="午",
        hidden={"午": ["丁", "己"], "申": ["庚", "壬", "戊"],
                "戌": ["戊", "辛", "丁"], "未": ["己", "丁", "乙"]},
        branches=["申", "午", "午", "未"],
        base={"year_stem": "庚", "month_stem": "庚", "hour_stem": "庚",
              "year_branch": "申", "month_branch": "午", "day_branch": "午",
              "hour_branch": "未", "stem_branch_pair": "甲午"})
    p = out["pending"]
    assert p["pillar_relation"] == "天合地"      # 日干甲与日支午藏己 → 甲己合
    assert p["branch_strength"] == "旺"           # 日支午==月支午（当令）


def test_wood_bu_shou_shui():
    """木不受水：木行现（甲/寅卯）但水行不现 → 木不受水。"""
    out = derive_state(
        day_stem="甲", month_branch="卯",
        hidden={"卯": ["乙"], "戌": ["戊", "辛", "丁"],
                "申": ["庚", "壬", "戊"], "午": ["丁", "己"]},
        branches=["申", "卯", "午", "戌"],
        base={"year_stem": "丙", "month_stem": "戊", "hour_stem": "庚",
              "year_branch": "申", "month_branch": "卯", "day_branch": "午",
              "hour_branch": "戌", "stem_branch_pair": "甲午"})
    p = out["pending"]
    assert p["wood_state"] == "不受水"    # 木现（甲/卯）∧水不现（干支均无壬癸亥子）


def test_earth_shou_huo():
    """土受火：土行现（戊/戌未）且火行现（午） → 受火。"""
    out = derive_state(
        day_stem="戊", month_branch="午",
        hidden={"午": ["丁", "己"], "戌": ["戊", "辛", "丁"],
                "申": ["庚", "壬", "戊"], "未": ["己", "丁", "乙"]},
        branches=["申", "午", "戌", "未"],
        base={"year_stem": "丙", "month_stem": "戊", "hour_stem": "庚",
              "year_branch": "申", "month_branch": "午", "day_branch": "戌",
              "hour_branch": "未", "stem_branch_pair": "戊戌"})
    p = out["pending"]
    assert p["earth_state"] == "受火"


def test_jinshui_ku_shang():
    """金水枯伤：金水现但月支非金水（不得令）→ 枯傷。"""
    out = derive_state(
        day_stem="庚", month_branch="卯",
        hidden={"卯": ["乙"], "申": ["庚", "壬", "戊"],
                "午": ["丁", "己"], "未": ["己", "丁", "乙"]},
        branches=["申", "卯", "午", "未"],
        base={"year_stem": "庚", "month_stem": "壬", "hour_stem": "辛",
              "year_branch": "申", "month_branch": "卯", "day_branch": "午",
              "hour_branch": "未", "stem_branch_pair": "庚午"})
    p = out["pending"]
    assert p["jinshui_state"] == "枯傷"    # 金（庚辛申）水（壬）现 ∧ 卯月非金水


def test_shuitu_xiang_sheng():
    """水土相胜：水土同现∧冲（申寅冲）→ 相勝。壬日主申月。"""
    out = derive_state(
        day_stem="壬", month_branch="申",
        hidden={"申": ["庚", "壬", "戊"], "寅": ["甲", "丙", "戊"],
                "午": ["丁", "己"], "戌": ["戊", "辛", "丁"]},
        branches=["寅", "申", "午", "戌"],
        base={"year_stem": "庚", "month_stem": "庚", "hour_stem": "戊",
              "year_branch": "寅", "month_branch": "申", "day_branch": "午",
              "hour_branch": "戌", "stem_branch_pair": "壬午",
              "relations": {"liu_chong": ["申", "寅"]}})
    p = out["pending"]
    assert p["shuitu_state"] == "相勝"    # 水土同现 ∧ 申寅冲


def test_isolation():
    """P-1 隔离：新字段不输出到顶层。"""
    out = derive_state(
        day_stem="甲", month_branch="卯",
        hidden={"卯": ["乙"], "戌": ["戊", "辛", "丁"],
                "申": ["庚", "壬", "戊"], "午": ["丁", "己"]},
        branches=["申", "卯", "午", "戌"],
        base={"year_stem": "丙", "month_stem": "戊", "hour_stem": "庚",
              "year_branch": "申", "month_branch": "卯", "day_branch": "午",
              "hour_branch": "戌", "stem_branch_pair": "甲午"})
    for f in ("pillar_relation", "day_master_strength", "branch_strength",
              "wood_state", "earth_state", "jinshui_state", "shuitu_state"):
        assert f not in out
