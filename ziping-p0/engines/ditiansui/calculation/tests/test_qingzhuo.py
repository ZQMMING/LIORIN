"""清浊/出身派生测试（P9 2026-09-16，PENDING_VERIFY 结构近似）。

消费规则：CAND-DTS-029/086/087（status=PENDING 隔离）。
口径：结构事实→状态判定；禁量化；用神=喜用行（strength 派生），忌神=内部反推（不输出）。
显混=忌神透干相战（DTS-022-002 注「縱有比肩食神印綬才煞雜之…循序得所…乃為清奇」）；
支藏忌神为有根闲神不破局，不判浊。
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


def test_qing_yide_daodi_you_jingshen():
    """身旺清格：丙日主巳月得令∧寅藏甲（帮身得地）→WANG，喜用=财官杀食伤（土水金）。
    庚金（财）透出，辰藏戊（本气土∈喜用）得地；忌神（木/火）不透干
    （寅午支现木火=有根闲神不破局；月支巳火=月令不判浊）→ 一清到底有精神。"""
    out = derive_state(
        day_stem="丙", month_branch="巳",
        base=_base("丙", "午", "巳", "庚", "戊", "庚", "寅", "戌"),
        hidden={"寅": ["甲", "丙", "戊"], "辰": ["戊", "乙", "癸"]},
        branches=["寅", "巳", "午", "戌"])
    p = out["pending"]
    assert out["day_strength_classic"] == "WANG"
    assert p["qing_state"] == "一清到底有精神"
    assert p["qingqi_state"] == "有清氣"


def test_qing_de_jin_not_reachable_in_min_strength():
    """清得盡（DTS-054-003「清得盡時黃榜客」）在最小版 strength 下结构不可达：
    帮身得地支（寅午巳卯）藏干必含印比劫（忌神）→ 藏干恒有闲神；
    独透（四干仅一用神）需他干为忌神透干 → 混。
    代码保留清得盡分支，待 strength 精度迭代（SLIGHTLY_WEAK 等）后可达。
    当前同构造应落「一清到底有精神」（支根闲神不破局、藏干闲神不判浊）。"""
    out = derive_state(
        day_stem="丙", month_branch="巳",
        base=_base("丙", "午", "巳", "庚", "戊", "庚", "寅", "戌"),
        hidden={"寅": ["甲", "丙", "戊"], "丑": ["己", "癸", "辛"]},
        branches=["寅", "巳", "午", "戌"])
    p = out["pending"]
    assert p["qing_state"] == "一清到底有精神"


def test_qing_ku():
    """清而枯弱：用神透干但不得地不得令 → 清枯。
    构造（JUN_HENG 无定喜路径）：丙日主卯月（非帮扶月），
    用神（辛金）透出但藏干无金本气 → 无锚点时落 UNDETERMINED；
    清枯路径在 strength 精度迭代（SLIGHTLY_WEAK）后可达，本测试锁当前行为。"""
    out = derive_state(
        day_stem="丙", month_branch="卯",
        base=_base("丙", "午", "卯", "辛", "癸", "庚", "申", "酉"),
        hidden={"辰": ["戊", "乙", "癸"]}, branches=["申", "卯", "午", "酉"])
    p = out["pending"]
    assert p["qing_state"] in ("清枯", "UNDETERMINED")


def test_man_pan_zhuo_qi():
    """忌神当权：忌神（木火）透干∧得令∧得地∧用神（土水金）不透 → 滿盤濁氣。
    丙日主午月 WANG；四干全木火（乙丁甲），寅支藏甲本气（木∈忌）。"""
    out = derive_state(
        day_stem="丙", month_branch="午",
        base=_base("丙", "午", "午", "乙", "丁", "甲", "寅", "戌"),
        hidden={"寅": ["甲", "丙", "戊"]}, branches=["寅", "午", "午", "戌"])
    p = out["pending"]
    assert out["day_strength_classic"] == "WANG"
    assert p["qing_state"] == "滿盤濁氣"


def test_ban_zhuo_ban_qing():
    """用忌混杂：用神透∧忌神透 → 半濁半清。
    丙日主午月 WANG；庚金（财∈喜用）透出 + 乙木（印∈忌）透出。"""
    out = derive_state(
        day_stem="丙", month_branch="午",
        base=_base("丙", "午", "午", "乙", "庚", "辛", "申", "戌"),
        hidden={"辰": ["戊", "乙", "癸"]}, branches=["申", "午", "午", "戌"])
    p = out["pending"]
    assert p["qing_state"] == "半濁半清"


def test_mutual_exclusion_boundary():
    """Human 裁决 2026-09-16 互斥边界验证：
    边界2：半浊半清必须 喜透>0∧忌透>0；边界1：清枯须喜神透干=0。
    喜透>0∧忌透>0 → 半浊半清（不得判清枯）。"""
    out = derive_state(
        day_stem="丙", month_branch="午",
        base=_base("丙", "午", "午", "乙", "庚", "辛", "申", "戌"),
        hidden={"辰": ["戊", "乙", "癸"]}, branches=["申", "午", "午", "戌"])
    p = out["pending"]
    assert p["qing_state"] == "半濁半清"  # 若误判清枯则违反边界1


def test_jun_heng_no_anchor():
    """均衡无定喜：JUN_HENG → qing_state=UNDETERMINED、qingqi=無清氣。"""
    out = derive_state(
        day_stem="丙", month_branch="卯",
        base=_base("丙", "午", "卯", "庚", "癸", "辛", "申", "酉"),
        hidden={"辰": ["戊", "乙", "癸"]}, branches=["申", "卯", "午", "酉"])
    p = out["pending"]
    assert p["qing_state"] == "UNDETERMINED"
    assert p["qingqi_state"] == "無清氣"


def test_guan_bu_lou():
    """官不露：官星（克日主=水）不透他干 → 不露。"""
    out = derive_state(
        day_stem="丙", month_branch="午",
        base=_base("丙", "午", "午", "庚", "戊", "庚", "申", "戌"),
        hidden={"辰": ["戊", "乙", "癸"]}, branches=["申", "午", "午", "戌"])
    p = out["pending"]
    assert p["guan"] == "不露"


def test_guan_lou():
    """官露：壬水（官）透出 → 露。"""
    out = derive_state(
        day_stem="丙", month_branch="午",
        base=_base("丙", "午", "午", "壬", "戊", "庚", "申", "戌"),
        hidden={"辰": ["戊", "乙", "癸"]}, branches=["申", "午", "午", "戌"])
    p = out["pending"]
    assert p["guan"] == "露"


def test_isolation():
    """P-1 隔离：qing_state/qingqi_state/guan 不在顶层，仅 pending 命名空间可见。"""
    out = derive_state(
        day_stem="丙", month_branch="巳",
        base=_base("丙", "午", "巳", "庚", "戊", "庚", "申", "戌"),
        hidden={"辰": ["戊", "乙", "癸"]}, branches=["申", "巳", "午", "戌"])
    for f in ("qing_state", "qingqi_state", "guan"):
        assert f not in out
    assert "qing_state" in out["pending"]
