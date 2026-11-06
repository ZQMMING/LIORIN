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
