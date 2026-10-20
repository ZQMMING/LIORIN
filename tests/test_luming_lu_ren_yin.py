# -*- coding: utf-8 -*-
"""禄刃印母法 (LURY) — 子平轴独立校验层测试.

原著锚定 (2026-10-20 核实):
  - 禄=日主临官 / 刃=帝旺(禄前一辰): 五行精纪 L3350/L3380
  - 物极必反: L3379 "已极而将反则为凶"; 三命通会 L9379/L9465/L13011
  - 刃印全非必凶: L3287 印绶化刃故贵 / L3382 揽辔澄清格 → 先查制化
  - 印绶喜食伤: L14184; 身弱喜刃印: L16900 (情形2以身旺太过为前提)
"""
import pytest

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.luming.lu_ren_yin import calc_lu_ren_yin, check_year_lury

BE = BaziEngine()


def _chart(y, m, d, h):
    return BE.compute((y, m, d, h), gender="male")


# ---------------------------------------------------------------------------
# 1. 确定性事实: 禄/刃/印分布
# ---------------------------------------------------------------------------
def test_1989_geng_ren_yin_count_two():
    """1989-12-26 亥时 男 (己巳 丙子 庚申 丁亥): 庚日 禄申✓ 刃酉✗ 印己✓ → count=2 过强."""
    ch = _chart(1989, 12, 26, 22)
    f = calc_lu_ren_yin(ch)
    assert f["day_master"] == "GENG"
    assert f["lu_branch"] == "SHEN" and f["lu_in_chart"] is True
    assert f["ren_branch"] == "YOU" and f["ren_in_chart"] is False
    assert "JI" in f["yin_stems"]
    assert f["count"] == 2 and f["strong"] == "过强"


def test_definition_tables():
    """禄/帝旺查表口径 (五行精纪 L3350 禄前一辰为羊刃)."""
    # 枚举找一个甲日主: 甲禄在寅, 甲帝旺在卯
    f_甲 = None
    for y in range(1975, 2001):
        for m in range(1, 13):
            for d in range(1, 29):
                try:
                    ch = BE.compute((y, m, d, 12), gender="male")
                except Exception:
                    continue
                if ch.day_master == "JIA":
                    f_甲 = calc_lu_ren_yin(ch)
                    break
            if f_甲:
                break
        if f_甲:
            break
    assert f_甲 is not None
    assert f_甲["lu_branch"] == "YIN"      # 甲禄在寅
    assert f_甲["ren_branch"] == "MAO"     # 甲帝旺在卯
    f_庚 = calc_lu_ren_yin(_chart(1989, 12, 26, 22))
    assert f_庚["lu_branch"] == "SHEN"     # 庚禄在申
    assert f_庚["ren_branch"] == "YOU"     # 庚帝旺在酉


# ---------------------------------------------------------------------------
# 2. 情形1: 命局占二 + 流年凑齐 — 有制不凶 (LURY-03) / 无制则凶 (LURY-02)
# ---------------------------------------------------------------------------
def test_1989_lury03_has_control_not_bad():
    """1989 庚申男 (禄+印占二), 2029 己酉 流年凑刃 — 原局丙丁火=七杀制刃 → LURY-03 不判凶."""
    ch = _chart(1989, 12, 26, 22)
    hits = check_year_lury(ch, "JI", "YOU")
    assert len(hits) == 1 and hits[0]["rule_id"] == "LURY-03"
    assert hits[0]["tone"] == "平"
    assert "有制" in hits[0]["out"] or "不主凶" in hits[0]["out"]


def test_1989_non_completing_year_no_hit():
    """2025 乙巳 非凑齐要素 → LURY 不触发."""
    ch = _chart(1989, 12, 26, 22)
    hits = check_year_lury(ch, "YI", "SI")
    assert hits == []


def test_lury02_no_control_is_bad():
    """1975-1-1 午时 男 (丁未日 禄午✓印甲✓无刃) 流年乙巳 凑刃, 无官杀无食伤 → LURY-02 凶."""
    ch = _chart(1975, 1, 1, 12)
    f = calc_lu_ren_yin(ch)
    assert f["count"] == 2 and not f["guan_stems"] and not f["shi_stems"]
    hits = check_year_lury(ch, "YI", "SI")
    assert len(hits) == 1 and hits[0]["rule_id"] == "LURY-02"
    assert hits[0]["tone"] == "凶"
    assert "物极必反" in hits[0]["out"] or "不利" in hits[0]["out"]


# ---------------------------------------------------------------------------
# 3. 命局禄刃印全: 无制无泄凶兆 (LURY-01) / 有制不凶 (LURY-05 由 L3287 约束)
# ---------------------------------------------------------------------------
def test_lury01_full_no_control_bad_omen():
    """1975-9-8 午时 男 (丁巳日 禄午✓刃巳✓印甲乙✓ 无制无泄) → LURY-01 凶兆."""
    ch = _chart(1975, 9, 8, 12)
    f = calc_lu_ren_yin(ch)
    assert f["count"] == 3
    hits = check_year_lury(ch, "YI", "SI")
    assert any(h["rule_id"] == "LURY-01" for h in hits)
    bad = [h for h in hits if h["rule_id"] == "LURY-01"][0]
    assert bad["tone"] == "凶"
    assert "L3379" in bad["evidence"]


def test_lury05_full_with_control_not_bad():
    """命局禄刃印全且有制 (官杀/食伤) → 不主凶 (L3287 印绶化刃故贵)."""
    # 构造: 庚申日 + 时支酉(刃) + 月干己(印) + 原局丙丁(七杀制刃)
    # 枚举近 1978-1998 找 count=3 且 guan/shi 非空
    found = None
    for y in range(1975, 2001):
        for m in range(1, 13):
            for d in range(1, 29):
                try:
                    ch = BE.compute((y, m, d, 12), gender="male")
                except Exception:
                    continue
                f = calc_lu_ren_yin(ch)
                if f["count"] == 3 and (f["guan_stems"] or f["shi_stems"]):
                    found = (ch, f)
                    break
            if found:
                break
        if found:
            break
    assert found is not None, "未找到 命局禄刃印全+有制 的真实案例"
    ch, f = found
    hits = check_year_lury(ch, "YI", "SI")
    assert any(h["rule_id"] == "LURY-05" for h in hits)
    good = [h for h in hits if h["rule_id"] == "LURY-05"][0]
    assert good["tone"] == "平"
    assert "L3287" in good["evidence"]


# ---------------------------------------------------------------------------
# 4. 情形2: 刃印齐不透劫财 + 流年食伤 → 吉 (LURY-04, L14184 印绶最好行伤官食神)
# ---------------------------------------------------------------------------
def test_lury04_ren_yin_with_food_god_is_good():
    """1975-5-6 午时 男 (壬子日 刃子✓印辛✓ 无劫财透) 流年丙寅(寅中甲木=食神) → LURY-04 吉."""
    ch = _chart(1975, 5, 6, 12)
    f = calc_lu_ren_yin(ch)
    assert f["day_master"] == "REN"
    assert f["ren_in_chart"] is True and f["yin_in_chart"] is True and not f["jie_stems"]
    hits = check_year_lury(ch, "BING", "YIN")
    assert any(h["rule_id"] == "LURY-04" for h in hits)
    good = [h for h in hits if h["rule_id"] == "LURY-04"][0]
    assert good["tone"] == "吉"
    assert "L14184" in good["evidence"]


def test_lury04_blocked_by_jie_cai():
    """劫财透干 → 情形2 不触发 (刃被劫夺, 非"不透劫财")."""
    # 1986-9-10 午时 男 (丙寅 丁酉 丁巳 丙午): 丁日 禄午✓刃巳✓ 印无 劫丙透
    ch = _chart(1986, 9, 10, 12)
    f = calc_lu_ren_yin(ch)
    assert f["jie_stems"]  # 劫财透干
    hits = check_year_lury(ch, "BING", "YIN")
    assert all(h["rule_id"] != "LURY-04" for h in hits)


# ---------------------------------------------------------------------------
# 5. query_year 挂载: LURY 为流年吉凶主判 (用户定案) — 触发即定案, 重恶不覆盖
# ---------------------------------------------------------------------------
def test_query_year_lury_master_judgment():
    """禄刃印母法主判: LURY-01/02 触发 → 流年 tone=凶; LURY-04(无重恶) → 吉."""
    from tongshu.luming.engine import query_year
    # LURY-02: 1975-1-1 丁未日 (禄午+印甲 占二) 流年乙巳凑刃无制 → 凶
    ch2 = _chart(1975, 1, 1, 12)
    out2 = query_year(ch2, 2025)
    assert any(h["rule_id"] == "LURY-02" for h in out2["lury"])
    assert out2["tone"] == "凶"
    # LURY-04: 1975-5-6 壬子日 (刃子+印辛 无劫财) 2024 甲辰 (甲=食神, 无重恶) → 吉
    ch4 = _chart(1975, 5, 6, 12)
    out4 = query_year(ch4, 2024)
    assert any(h["rule_id"] == "LURY-04" for h in out4["lury"])
    assert out4["tone"] == "吉"


def test_query_year_lury04_blocked_by_heavy_evil():
    """LURY-04 食伤吉面需无重灾凶信号 (L14184 忌官刑冲羊刃 / L4409 无冲害刑克):
    毛泽东 1976 丁日(刃巳+印甲) 丙辰年辰中戊=伤官, 但岁运并临+6凶齐集=重恶 → 仍凶."""
    from tongshu.luming.engine import from_bazi_chart, query_year
    ch = _chart(1893, 12, 26, 20)
    lm = from_bazi_chart(ch)
    out = query_year(ch, 1976, lm=lm)
    assert any(h["rule_id"] == "LURY-04" for h in out["lury"])   # 母法触发
    assert out["tone"] == "凶"                                    # 重恶 → 不覆盖
    assert out["combined"]["l4273"]["mode"] == "无"


def test_query_year_lury03_no_override():
    """LURY-03 (占二凑齐·有制不凶) 交原层, 不覆盖流年判定."""
    from tongshu.luming.engine import query_year
    ch = _chart(1989, 12, 26, 22)
    out = query_year(ch, 2029)
    assert any(h["rule_id"] == "LURY-03" for h in out["lury"])
    # 流年自身判定保留 (不因 LURY-03 变吉变凶)
    assert out["tone"] in ("吉", "吉凶相杂", "凶")
