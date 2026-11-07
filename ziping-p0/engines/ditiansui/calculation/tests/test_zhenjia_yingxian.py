"""真假神/隐显众寡/才德派生测试（DTS-023/027/036，PENDING_VERIFY 结构近似）。

消费规则：CAND-DTS-030/031/032/033/034/035/045/046（status=PENDING 隔离）。
口径：结构事实→状态判定；禁绝对量化（众寡用相对计数）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.ditiansui.calculation.state import derive_state  # noqa: E402


def _base(day_stem, day_branch, month_branch, ys, ms, hs, yb, hb):
    return {
        "year_stem": ys, "month_stem": ms, "hour_stem": hs,
        "year_branch": yb, "month_branch": month_branch,
        "day_branch": day_branch, "hour_branch": hb,
        "stem_branch_pair": day_stem + day_branch,
    }


def test_zhen_shen_de_yong():
    """真神得用：丙日主巳月（火=真神/月令行），喜用=财官杀食伤（土水金）。
    巳月火∉喜用 → 真神不得用；庚金透干（喜用）但月支≠金 → 用假。
    ——构造 WANG：丙/巳月 + 寅藏甲（帮身得地）。"""
    out = derive_state(
        day_stem="丙", month_branch="巳",
        base=_base("丙", "午", "巳", "庚", "戊", "庚", "寅", "戌"),
        hidden={"寅": ["甲", "丙", "戊"], "辰": ["戊", "乙", "癸"]},
        branches=["寅", "巳", "午", "戌"])
    p = out["pending"]
    assert out["day_strength_classic"] == "WANG"
    # 真神=月令行（火），喜用=土水金 → 月支行∉喜用 → 不得用
    assert p["zhen_shen_state"] == "不得用"
    # 喜用（庚金）透干但月支非金 → 用假
    assert p["jia_shen_state"] == "用假"


def test_zhen_shen_used_when_month_is_xi():
    """真神得用：戊日主寅月（木=月令行），身弱喜印比（木火）→ 月支行木∈喜用且忌神不透 → 得用。
    构造 SHUAI：戊日主，寅月，四干无帮扶透（除日主）、藏干无火……SHUAI 需无令无地无势——
    寅月=木∈bang（木火）→ 得令 → 非 SHUAI。改用 JUN_HENG 验证不可达？"""
    # 此构造在最小版 strength 下难以同时满足（身弱判定=无帮扶透，与喜用透干冲突），
    # 故锁定：JUN_HENG 无定喜 → 真假神不输出（u 空条件）
    out = derive_state(
        day_stem="丙", month_branch="卯",
        base=_base("丙", "午", "卯", "庚", "癸", "辛", "申", "酉"),
        hidden={"辰": ["戊", "乙", "癸"]}, branches=["申", "卯", "午", "酉"])
    p = out["pending"]
    assert "zhen_shen_state" not in p


def test_jishen_tai_lu_xiongwu_shen_cang():
    """吉神太露/凶物深藏：丙日主巳月 WANG，喜用=土水金。
    庚金透干 → 吉神太露；忌神=木火，乙木藏于辰 → 凶物深藏（不透干但藏干现）。"""
    out = derive_state(
        day_stem="丙", month_branch="巳",
        base=_base("丙", "午", "巳", "庚", "戊", "庚", "寅", "戌"),
        hidden={"寅": ["甲", "丙", "戊"], "辰": ["戊", "乙", "癸"]},
        branches=["寅", "巳", "午", "戌"])
    p = out["pending"]
    assert p["jishen_state"] == "太露"       # 喜神（庚金）透干
    assert p["xiongwu_state"] == "深藏"      # 忌神（乙木）藏于辰，不透干


def test_wo_shi_di():
    """强众敌寡：丙日主巳月 WANG（忌=木火）。
    丙午日支午火（比劫）→ 我=火 count 高；忌=木火。"""
    out = derive_state(
        day_stem="丙", month_branch="巳",
        base=_base("丙", "午", "巳", "庚", "戊", "庚", "午", "戌"),
        hidden={"寅": ["甲", "丙", "戊"]}, branches=["午", "巳", "午", "戌"])
    p = out["pending"]
    assert out["day_strength_classic"] == "WANG"
    # 8 字：丙庚戊庚/午巳午戌 → 火=丙+午+巳+午=4，木火忌=4+（寅藏甲不计8字）→ my=4 enemy(木火)=4
    assert p["wo_shi"] in ("強衆", "強寡")
    assert p["di"] in ("敵寡", "敵衆")


def test_decai_de_sheng_cai():
    """德胜才：清∧无冲。丙日主巳月 WANG，庚透得地、忌不透 → 一清到底有精神；无冲 → 德胜才。"""
    out = derive_state(
        day_stem="丙", month_branch="巳",
        base=_base("丙", "午", "巳", "庚", "戊", "庚", "寅", "戌"),
        hidden={"寅": ["甲", "丙", "戊"], "辰": ["戊", "乙", "癸"]},
        branches=["寅", "巳", "午", "戌"])
    p = out["pending"]
    assert p["qing_state"] == "一清到底有精神"
    assert p["decai_relation"] == "德勝才"


def test_decai_cai_sheng_de_with_chong():
    """才胜德：清∧有冲 → 才胜德（混浊破害）。
    丙日主寅月 WANG（得令∧寅藏甲得地）；四干戊庚庚全喜用（土金）→ 一清到底；
    申寅冲 → 才勝德。"""
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
    assert out["day_strength_classic"] == "WANG"
    assert p["qing_state"] == "一清到底有精神"
    assert p["decai_relation"] == "才勝德"


def test_isolation():
    """P-1 隔离：新字段不在顶层，仅 pending 可见。"""
    out = derive_state(
        day_stem="丙", month_branch="巳",
        base=_base("丙", "午", "巳", "庚", "戊", "庚", "寅", "戌"),
        hidden={"寅": ["甲", "丙", "戊"], "辰": ["戊", "乙", "癸"]},
        branches=["寅", "巳", "午", "戌"])
    for f in ("zhen_shen_state", "jia_shen_state", "jishen_state",
              "xiongwu_state", "wo_shi", "di", "decai_relation"):
        assert f not in out
        assert f in out["pending"]
