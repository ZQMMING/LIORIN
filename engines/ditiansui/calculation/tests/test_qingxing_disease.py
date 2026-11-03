"""情性二/疾病派生测试（DTS-052-022/053，PENDING_VERIFY 结构近似）。

消费规则：CAND-DTS-068~073/075~077（status=PENDING 隔离）。
⚠ CAND-DTS-074 字段值域冲突（wuxing_state 和/不戾）登记待 Human 裁决，不实现。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.ditiansui.calculation.state import derive_state  # noqa: E402


def _run(day_stem, month_branch, ys, ms, hs, yb, hb, db, hidden, chong=None):
    return derive_state(
        day_stem=day_stem, month_branch=month_branch,
        hidden=hidden, branches=[yb, month_branch, db, hb],
        base={"year_stem": ys, "month_stem": ms, "hour_stem": hs,
              "year_branch": yb, "month_branch": month_branch,
              "day_branch": db, "hour_branch": hb,
              "stem_branch_pair": day_stem + db,
              "relations": {"liu_chong": chong} if chong else {}})


def test_yangren_zhan():
    """阳刃战：甲日主卯月（刃=卯），卯酉冲 → 戰。四干庚戊庚戊（喜用透）、忌木水不透 → 清。"""
    out = _run("甲", "卯", "庚", "戊", "庚", "酉", "未", "戌",
               {"卯": ["乙"], "酉": ["辛"], "未": ["己", "丁", "乙"], "戌": ["戊", "辛", "丁"]},
               chong=["卯", "酉"])
    p = out["pending"]
    assert p["yangren_state"] == "戰"


def test_yangren_ruo_unreachable():
    """阳刃弱：最小版下不可达——刃支=日主帝旺位（帮身得地）→ 恒 WANG，非 WEAK。
    登记为已知结构性限制（同清得盡），待 strength 精度迭代后复查。
    锁定：刃现但不冲 → 不输出「戰」。"""
    out = _run("甲", "卯", "庚", "戊", "庚", "申", "戌", "未",
               {"卯": ["乙"], "申": ["庚", "壬", "戊"],
                "戌": ["戊", "辛", "丁"], "未": ["己", "丁", "乙"]})
    p = out["pending"]
    assert p.get("yangren_state") != "戰"    # 无冲 → 非戰（弱待 strength 精度）


def test_shangguan_ge():
    """伤官格：甲日主，伤官行=火（我生）。火透干（丙丁）→ 伤官格。
    甲日主卯月 WANG（卯∈木水bang得令∧卯藏乙得地）；四干丙戊丙戊（火土=喜用）→ 清。
    2026-09-16 三态化：shangguan_ge_state 已删，复用 qing_state（清=一清到底有精神）。"""
    out = _run("甲", "卯", "丙", "戊", "丙", "申", "戌", "未",
               {"卯": ["乙"], "申": ["庚", "壬", "戊"],
                "戌": ["戊", "辛", "丁"], "未": ["己", "丁", "乙"]})
    p = out["pending"]
    assert out["day_strength_classic"] == "WANG"
    assert p["qing_state"] in ("一清到底有精神", "清得盡")
    assert "shangguan_ge_state" not in p


def test_yongshen_duo():
    """用神多：甲日主卯月 WANG（喜用=土金水=财官杀食伤）。
    四干庚戊庚戊（金土）→ 喜用透 3 → 多。"""
    out = _run("甲", "卯", "庚", "戊", "庚", "申", "戌", "未",
               {"卯": ["乙"], "申": ["庚", "壬", "戊"],
                "戌": ["戊", "辛", "丁"], "未": ["己", "丁", "乙"]})
    p = out["pending"]
    assert p["yongshen_state"] == "多"


def test_xueqi_luan():
    """血气乱：有冲（申寅冲）→ 亂。甲日主卯月。"""
    out = _run("甲", "卯", "庚", "戊", "庚", "申", "戌", "未",
               {"卯": ["乙"], "申": ["庚", "壬", "戊"],
                "戌": ["戊", "辛", "丁"], "未": ["己", "丁", "乙"]},
               chong=["申", "寅"])
    p = out["pending"]
    assert p["xueqi_state"] == "亂"


def test_xueqi_he():
    """血气和：无冲无战。甲日主卯月，四干丙戊丙（火土，无庚辛→无天战）。"""
    out = _run("甲", "卯", "丙", "戊", "丙", "寅", "午", "未",
               {"卯": ["乙"], "寅": ["甲", "丙", "戊"],
                "午": ["丁", "己"], "未": ["己", "丁", "乙"]})
    p = out["pending"]
    assert p["xueqi_state"] == "和"


def test_jishen_ru_wuzang():
    """忌神入五脏：甲日主卯月 WANG，忌=木水。忌木克土（五脏行）→ 土现（戌藏戊/未藏己）→ 入五脏。"""
    out = _run("甲", "卯", "庚", "戊", "庚", "申", "戌", "未",
               {"卯": ["乙"], "申": ["庚", "壬", "戊"],
                "戌": ["戊", "辛", "丁"], "未": ["己", "丁", "乙"]})
    p = out["pending"]
    assert p["jishen_location"] == "入五臟"


def test_keshen_you_liujing_unreachable():
    """客神游六经：最小版下不可达——喜忌三档（WANG/SHUAI）喜∪忌恒覆盖全部五行，
    无闲神（非喜非忌）可输出。登记为已知结构性限制，待 strength 精度迭代（
    SLIGHTLY_STRONG/SLIGHTLY_WEAK 细分或喜用多选）后可达。锁定：不输出「遊六經」。"""
    out = _run("甲", "卯", "庚", "戊", "丙", "申", "午", "未",
               {"卯": ["乙"], "申": ["庚", "壬", "戊"],
                "午": ["丁", "己"], "未": ["己", "丁", "乙"]})
    p = out["pending"]
    assert p.get("keshen_location") != "遊六經"    # 喜忌全覆盖 → 无客神（结构性限制）


def test_isolation():
    """P-1 隔离：新字段不输出到顶层；已输出的字段仅在 pending 可见。"""
    out = _run("甲", "卯", "庚", "戊", "庚", "申", "戌", "未",
               {"卯": ["乙"], "申": ["庚", "壬", "戊"],
                "戌": ["戊", "辛", "丁"], "未": ["己", "丁", "乙"]})
    for f in ("yangren_state", "shangguan_ge_state", "yongshen_state",
              "zhige_state", "xueqi_state", "jishen_location", "keshen_location"):
        assert f not in out
    assert out["pending"]["xueqi_state"] == "亂"        # 甲日主+庚透 → 天戰 → 亂（恒输出在 pending）
    assert out["pending"]["yongshen_state"] == "多"
    assert out["pending"]["jishen_location"] == "入五臟"
