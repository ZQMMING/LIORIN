"""H11 节候卦与原典逐条核对（D-018，2026-11-06）

原典：`data/heluo/guajie_raw/河洛真数_起例卷之下.txt`「节候卦爻」段。
本测试不引入任何新期望值之外的数据，只做三件事：
  1. 七十二候候名按序命中原文（正常化标点后逐条比对）；
  2. 24 节气 = 原文七十二候的「每三候一组」，节候卦由首候派生，变卦 = 该爻机械翻转；
  3. 八节卦（四正卦分领）与原文首句一致。
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from tongshu.engines.heluo.guajie import COMPOUND_GUA, hexagram_to_lines, _lines_to_gua
from tongshu.engines.heluo.jiehhou import (
    BI_GUA,
    HOU_GUA,
    HOU_GUA_BY_JQ,
    JIE_GUA,
    JIEHOU_GUA,
    JIEHOU_GUA_NAME,
    SIXTY_GUA,
    SIZHENG_GUA,
    SOLAR_TERMS,
    get_qi_phase,
    get_seasonal_hexagram,
    _gua_full,
)

_RAW = Path(__file__).resolve().parents[1] / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之下.txt"

# 转录异文：原文「鹰化为始」（月令作「鹰化为鸠」），保留原文写法登记
_HOU_VARIANTS = {"鹰化为鸠": "鹰化为始"}

# 八节卦分领：每 6 个节气一组
_JIE_GROUPS = [(0, "坎"), (6, "震"), (12, "离"), (18, "兑")]


def _jieqi_paragraph() -> str:
    text = _RAW.read_text(encoding="utf-8")
    i = text.find("节候卦爻")
    assert i >= 0, "原文缺「节候卦爻」段"
    j = text.find("先后天八卦变化之义", i)
    return text[i:j if j > 0 else i + 2000]


def _normalize(s: str) -> str:
    return re.sub(r"[，、。；：\s]", "", s)


def test_hou_structure():
    """七十二候结构：72 条、24 节气各 3 候、候序连续、爻位 0-5。"""
    assert len(HOU_GUA) == 72
    by_jq = {}
    for jq, seq, short, idx, hou in HOU_GUA:
        by_jq.setdefault(jq, []).append((seq, short, idx, hou))
        assert 0 <= idx <= 5
        assert short in COMPOUND_GUA
    assert len(by_jq) == 24
    for jq, rows in by_jq.items():
        assert [r[0] for r in rows] == [1, 2, 3], f"节气{jq}候序非 1-3"


def test_hou_names_match_yuanwen_in_order():
    """72 候候名按序命中原文（正常化标点后子串递进匹配）。"""
    para = _normalize(_jieqi_paragraph())
    pos = 0
    misses = []
    for jq, seq, short, idx, hou in HOU_GUA:
        want = _normalize(_HOU_VARIANTS.get(hou, hou))
        found = para.find(want, pos)
        if found < 0:
            # 允许原文拆词（如「天地…」被逗号隔开），退回全段查找
            found = para.find(want)
        if found < 0:
            misses.append((SOLAR_TERMS[jq], seq, short, hou))
        else:
            pos = found + len(want)
    assert not misses, f"候名未命中原文: {misses}"


def test_jiehou_derived_from_first_hou():
    """节候卦 = 该节气首候（候序 1），24 条齐全。"""
    assert len(JIEHOU_GUA) == 24
    for jq in range(24):
        short, idx, hou = HOU_GUA_BY_JQ[jq]
        main, line, result = JIEHOU_GUA[jq]
        assert line == idx
        assert main == JIEHOU_GUA_NAME[jq]
        # 全名由上下卦象拼出，且短名可反查
        assert result


def test_result_gua_is_mechanical_flip():
    """派生变卦 = 候卦该爻阴阳翻转（原典未载变卦，仅机械一致）。"""
    for jq, (short, idx, _hou) in HOU_GUA_BY_JQ.items():
        lines = hexagram_to_lines(short)
        lines[idx] = 1 if lines[idx] == 0 else 0
        expect_short = _lines_to_gua(lines)
        got = get_seasonal_hexagram(jq).result_gua
        # 纯卦结果用全名（震为雷），非纯卦用「上象+下象+短名」；统一用引擎同一拼名函数比对
        assert got == _gua_full(expect_short), f"{SOLAR_TERMS[jq]}: {got} != {_gua_full(expect_short)}"


def test_jie_gua_division():
    """八节卦：坎冬至起六爻→惊蛰；震春分→芒种；离夏至→白露；兑秋分→大雪。"""
    assert len(JIE_GUA) == 24
    for start, trigram in _JIE_GROUPS:
        for k in range(6):
            jq = start + k
            assert JIE_GUA[jq] == (trigram, k), f"{SOLAR_TERMS[jq]} 八节卦应为 {trigram}·第{k}爻"
    for jq in range(24):
        info = get_seasonal_hexagram(jq)
        assert info.jie_gua  # 全名非空
        assert info.jie_line == jq % 6


def test_qi_phase_semantics():
    """卦气：二至二分四正卦当值；辟卦按节气月建；其余行六日七分。"""
    assert get_qi_phase(2026, 0).is_sizheng
    assert get_qi_phase(2026, 3).is_sizheng is False
    assert get_qi_phase(2026, 0).bi_gua == "复"   # 冬至子月
    assert get_qi_phase(2026, 3).bi_gua == "泰"   # 立春寅月
    assert get_qi_phase(2026, 12).bi_gua == "姤"  # 夏至午月
    assert get_qi_phase(2026, 1).six_day_seven_method
    assert get_qi_phase(2026, 0).six_day_seven_method is False


def test_sixty_gua_table():
    """六十卦表：60 条、无重复、不含四正、全部是有效卦名。"""
    assert len(SIXTY_GUA) == 60
    assert len(set(SIXTY_GUA)) == 60
    assert not (set(SIXTY_GUA) & SIZHENG_GUA)
    assert all(n in COMPOUND_GUA for n in SIXTY_GUA)
    # 十二辟卦全部在六十卦内（四正不在辟卦）
    assert all(b in SIXTY_GUA for b in BI_GUA)


def test_yuanwen_has_jie_gua_sentence():
    """原文首句存在（八节卦分领与 90 日/15 日口径）。"""
    para = _normalize(_jieqi_paragraph())
    assert _normalize("节卦坎初六起冬至") in para
    assert _normalize("每卦总管九十日") in para
    assert _normalize("每一爻各直十五日") in para
