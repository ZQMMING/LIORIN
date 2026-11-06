"""H7 元气分体判定（正体 / 互体 / 伏体 / 相生 / 元反）——原典逐条对照。

原典（data/heluo/guajie_raw/河洛真数_起例卷之上.txt）：
  · 「凡人当生年天干为天元气，主贵，地支为地元气，主富，纳音为人元气，主寿。」
  · 「正体若无，须看互体，互体又无，推及伏体……如甲子生人得小过，虽卦中无乾兑金元气，
     然互体有兑，亦是纳音。」
  · 「又如水命生人，天干地支俱无元气，而得乾兑之卦，是金能生水，亦可谓得元气也。」
  · 「如卦体中二者俱反，必贫穷困苦夭死者也。」
"""
import pytest

from tongshu.engines.heluo.yuan_qi import (
    compute_yuan_qi, nayin_element, YuanQiState,
)


@pytest.mark.parametrize("stem,branch,el", [
    ("甲", "子", "金"), ("丙", "寅", "火"), ("戊", "辰", "木"),
    ("庚", "午", "土"), ("壬", "申", "金"), ("癸", "亥", "水"),
    ("甲", "辰", "火"), ("庚", "申", "木"), ("戊", "申", "土"),
])
def test_nayin_element_follows_ganzhi_nagua(stem, branch, el):
    # 原典「干支纳卦」：纳音即人元气
    assert nayin_element(stem, branch) == el


def test_nayin_invalid_ganzhi_pair():
    # 甲(阳干) + 丑(阴支) 非六十甲子组合
    assert nayin_element("甲", "丑") == ""


def test_xiaoguo_hu_ti_is_de_yuan_qi():
    # 原典举例：甲子生人得小过，卦中无乾兑金元气，然互体有兑，亦是纳音 → 得元气
    r = compute_yuan_qi("甲", "子", "震", "艮", "震", "艮")
    assert r.ren_yuan_element == "金"
    assert set(r.ren_yuan_qi) == {"乾", "兑"}
    assert r.state is YuanQiState.NORMAL
    assert r.scope == "互体"
    assert "互体" in r.evidence[-1] or any("互体" in e for e in r.evidence)


def test_shuisheng_de_qian_dui_is_sheng_wo():
    # 原典：水命生人，天干地支俱无元气，而得乾兑之卦，金能生水，亦可谓得元气
    r = compute_yuan_qi("丙", "子", "乾", "乾", "乾", "乾")
    assert r.ren_yuan_element == "水"
    assert r.state is YuanQiState.NORMAL
    assert r.scope == "相生"
    assert any("金生水" in e for e in r.evidence)


def test_reverse_when_zheng_ti_has_fan_gua():
    # 甲子年：天元气乾（反坤）、地元气坎（反离）；卦得坤，正体/互体无元气 → 元反
    r = compute_yuan_qi("甲", "子", "坤", "坤", "坤", "坤")
    assert r.state is YuanQiState.REVERSE
    assert r.scope == ""
    assert any("元反" in e for e in r.evidence)


def test_zheng_ti_takes_precedence_over_fan():
    # 纪晓岚日 甲辰年：天元气乾在正体，虽卦中亦有元反之卦，元气为主
    r = compute_yuan_qi("甲", "辰", "乾", "坎", "乾", "巽")
    assert r.state is YuanQiState.NORMAL
    assert r.scope == "正体"
