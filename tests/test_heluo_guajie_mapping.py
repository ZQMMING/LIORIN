# -*- coding: utf-8 -*-
"""河洛解层映射完整性测试：原典断语必须逐字到达引擎输出。

真值来源：data/heluo/guajie_data.json（64 卦原典：卦辞 + 六爻辞/小象/断语）。
本测试只校验「原典文本 → 引擎字段」的映射没有丢字、没有截断、没有改写，
不校验断法本身（断法见 tests/test_heluo_truth.py 与 H16 独立验证）。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tongshu.engines.heluo.guajie import load_guajie_data, query_yao_duan

REPO = Path(__file__).resolve().parent.parent
DATA_PATH = REPO / "data" / "heluo" / "guajie_data.json"
_RAW = json.loads(DATA_PATH.read_text(encoding="utf-8"))


def test_gua_ci_verbatim_for_all_64():
    gua = load_guajie_data()
    assert len(gua) == 64
    bad = []
    for entry in _RAW:
        name = entry["name"]
        item = gua.get(name)
        if item is None:
            bad.append((name, "MISSING_GUA"))
            continue
        if item.gua_ci != entry["gua_ci"]:
            bad.append((name, "gua_ci", item.gua_ci, entry["gua_ci"]))
    assert bad == [], f"卦辞映射不符：{bad[:5]}"


def test_yao_ci_verbatim_for_all_384():
    bad = []
    checked = 0
    for entry in _RAW:
        name = entry["name"]
        for yao in entry["yaos"]:
            checked += 1
            got = query_yao_duan(name, yao["yao"])
            if got is None:
                bad.append((name, yao["yao"], "MISSING"))
                continue
            if got.ci != yao["ci"]:
                bad.append((name, yao["yao"], "ci", got.ci, yao["ci"]))
            if got.xiang != yao["xiang"]:
                bad.append((name, yao["yao"], "xiang", got.xiang, yao["xiang"]))
    assert checked == 384
    assert bad == [], f"爻辞映射不符：{bad[:5]}"


def test_every_hexagram_has_six_yao():
    for entry in _RAW:
        assert len(entry["yaos"]) == 6, entry["name"]
        names = [y["yao"] for y in entry["yaos"]]
        assert len(set(names)) == 6, entry["name"]


def test_duans_preserved_without_truncation():
    """原典断语（duans）必须全部进入 YaoDuan 的叶/不叶/岁运三栏，不得丢字。

    注：loader 用 _split_duans 把 duans 重组为 ye/buye/suiyun（原典措辞变体归类），
    所以校验方式是「每条原文断语都能在三栏拼接文本中原样找到」，而不是要求字段名一致。
    """
    lost = []
    total = 0
    for entry in _RAW:
        for yao in entry["yaos"]:
            got = query_yao_duan(entry["name"], yao["yao"])
            if got is None:
                lost.append((entry["name"], yao["yao"], "MISSING"))
                continue
            all_text = " ".join([got.ye or "", got.buye or "", got.suiyun or ""])
            for d in yao.get("duans", []):
                total += 1
                if d not in all_text:
                    lost.append((entry["name"], yao["yao"], d[:20]))
    assert total == 1088, f"原典断语条数变化：{total}"
    assert lost == [], f"断语丢失：{lost[:5]}"


def test_gua_ci_jingyi_covers_all_64():
    """精义层（现代语义）必须 64 卦齐备，且与卦名一一对应。"""
    jingyi_path = REPO / "data" / "heluo" / "guajie_jingyi.json"
    jingyi = json.loads(jingyi_path.read_text(encoding="utf-8"))
    gua = load_guajie_data()
    assert len(jingyi) == 64
    for entry in _RAW:
        name = entry["name"]
        assert name in jingyi, name
        item = gua[name]
        assert item.gua_ci_jingyi, f"{name} 精义为空"
        assert item.gua_ci_shiyi, f"{name} 释义为空"


# ═══════════════════════════════════════════════════════════════════
# 卦气月 / 纳甲（006：原典写法不统一，抽取必须 64/64 全覆盖）
# ═══════════════════════════════════════════════════════════════════

# 原典「纳甲是」段落两处转录异文（不是解析缺陷）：
#   观：原文写「辛巳、辛卯、辛丑」，按巽外卦应为「辛未、辛巳、辛卯」→ 辛丑 系 辛未 之讹
#   损：原文写「丙戊」，戊非地支 → 丙戌 之讹
_NAJIA_TEXT_VARIANTS = {"观": {"辛未"}, "损": {"丙戌"}}


def test_gua_qi_month_covers_all_64():
    """64 卦卦气月必须全部解析出来（原典写法有「属X月」「在X月」「世在上属X月」三种）。"""
    gua = load_guajie_data()
    missing = [name for name, g in gua.items() if g.gua_qi_month is None]
    assert missing == [], f"卦气月未解析：{missing}"
    bad = [name for name, g in gua.items() if not 1 <= (g.gua_qi_month or 0) <= 12]
    assert bad == [], f"卦气月越界：{bad}"


def test_najia_six_lines_for_all_64():
    """每卦纳甲必须是完整六爻（初→上），不能只剩内卦三条。"""
    from tongshu.engines.heluo.guajie import COMPOUND_GUA, hexagram_najia

    gua = load_guajie_data()
    bad = []
    for name, g in gua.items():
        if len(g.najia) != 6 or len(set(g.najia)) != 6:
            bad.append((name, g.najia))
        # 与按卦象独立重算的结果一致
        if g.najia != hexagram_najia(name):
            bad.append((name, "recompute", g.najia, hexagram_najia(name)))
        up, low = COMPOUND_GUA[name]
        assert g.najia[:3] == hexagram_najia(name)[:3] and up and low
    assert bad == [], f"纳甲不完整：{bad[:5]}"


def test_najia_matches_jingfang_table():
    """纳甲必须合京房纳甲表（河洛原典「纳甲是」所载即京房表）。"""
    from tongshu.engines.heluo.guajie import hexagram_najia

    expected = {
        "乾": ["甲子", "甲寅", "甲辰", "壬午", "壬申", "壬戌"],
        "坤": ["乙未", "乙巳", "乙卯", "癸丑", "癸亥", "癸酉"],
        "比": ["乙未", "乙巳", "乙卯", "戊申", "戊戌", "戊子"],   # 坤内 + 坎外
        "小畜": ["甲子", "甲寅", "甲辰", "辛未", "辛巳", "辛卯"],  # 乾内 + 巽外
    }
    for name, want in expected.items():
        assert hexagram_najia(name) == want, name


def test_najia_text_evidence_cross_check():
    """原文「纳甲是」+「借用」并集必须覆盖计算出的纳甲（除登记的两处异文）。"""
    from tongshu.engines.heluo.guajie import _parse_gua_header, hexagram_najia

    bad = []
    for entry in _RAW:
        name = entry["name"]
        _month, najia_text, borrow = _parse_gua_header(entry.get("lines", []))
        union = set(najia_text) | set(borrow)
        missing = set(hexagram_najia(name)) - union
        if missing - _NAJIA_TEXT_VARIANTS.get(name, set()):
            bad.append((name, sorted(missing)))
    assert bad == [], f"原文纳甲与京房表不符：{bad[:5]}"


def test_ye_buye_uses_gua_qi_and_najia():
    """命卦叶/不叶：生月=卦气月 + 年干支在纳甲 → 叶；只满足一项 → 半叶。"""
    from tongshu.engines.heluo.guajie import judge_ye_buye

    ye = judge_ye_buye("乾", 4, "甲子")     # 乾卦气属四月，甲子在纳甲
    assert ye is not None and ye.ye is True and ye.buye is False
    assert ye.najia_hit is True
    # 乾卦头「二月已后八月以前及时」→ 得时窗 2-8 月；11 月既非卦气月也非得时
    half = judge_ye_buye("乾", 11, "甲子")  # 月不合、纳甲合 → 半叶
    assert half is not None and half.ye is False and half.buye is False
    buye = judge_ye_buye("乾", 11, "乙丑")  # 两不合 → 不叶
    assert buye is not None and buye.buye is True


def test_shu_xiong_does_not_assume_yang_month():
    """生月未知时不得假设阳月，否则「数有余」会被误判成数凶。"""
    from tongshu.engines.heluo.guajie import judge_shu_xiong

    sx = judge_shu_xiong(22, 56, 0)
    assert sx.pattern == "以弱敌强"
    assert any("生月未知" in e for e in sx.evidence)
    assert sx.shu_xiong is True  # 数有余本身仍记凶，但不得伪称"阳月"


def test_compose_guajie_outputs_benming_ye_buye():
    """解卦层输出必须带命卦叶/不叶（此前只算流年卦）。"""
    from tongshu.engines.heluo.canonical import heluo_calculate
    from tongshu.engines.heluo.guajie import build_guajie_from_result

    bazi = [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")]
    r = heluo_calculate(("甲辰", "辛未", "丙戌", "甲午"), gender="male",
                        birth_hour="午", era="shang")
    gj = build_guajie_from_result(r, bazi=bazi)
    yb = gj["benming_ye_buye"]
    assert yb is not None
    assert yb["gua_qi_month"] == 1      # 泰卦气属正月
    assert yb["najia_hit"] is True      # 甲辰在纳甲
    assert any("命卦叶/不叶" in e for e in gj["evidence"])


def test_de_shi_windows_parsed_from_book_text():
    """卦头「及时/得时/失时」月窗：旧实现只认出乾 1 卦，新实现覆盖 19 卦。"""
    from tongshu.engines.heluo.guajie import load_guajie_data, _parse_de_shi_windows

    data = load_guajie_data()
    windows = {}
    for name, g in data.items():
        de, shi = _parse_de_shi_windows(g.gua_lines)
        if de or shi:
            windows[name] = (de, shi)

    assert len(windows) == 19
    de, shi = windows["乾"]                 # 二月已后八月以前及时
    assert de == set(range(2, 9)) and not shi
    de, shi = windows["兑"]                 # 生于秋则及时
    assert de == {7, 8, 9}
    de, shi = windows["渐"]                 # 在冬则及时
    assert de == {10, 11, 12}
    de, shi = windows["恒"]                 # 二至八月及时，九至十二月失时
    assert de == set(range(2, 9)) and shi == {9, 10, 11, 12}
    de, shi = windows["噬嗑"]               # 二至八月及时，十月至正月失时
    assert de == set(range(2, 9)) and shi == {10, 11, 12, 1}


def test_ye_buye_uses_de_shi_window():
    """得时月窗参与叶/不叶判定：乾 6 月得时 + 纳甲合 → 叶。"""
    from tongshu.engines.heluo.guajie import judge_ye_buye

    ye = judge_ye_buye("乾", 6, "甲子")
    assert ye is not None and ye.ye is True
    assert any("得时" in e for e in ye.evidence)
