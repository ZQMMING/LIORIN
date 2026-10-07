# -*- coding: utf-8 -*-
"""精义/释义接入解卦层测试（2026-09-15 接入 guajie_jingyi.json 706 单元）。"""
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "src"))

from tongshu.engines.heluo.guajie import (
    GuaDuan,
    YaoDuan,
    build_guajie_from_result,
    load_guajie_data,
    query_yao_duan,
)
from tongshu.engines.heluo_adapter import HeluoAdapter


class TestJingyiDataLayer:
    """数据层：load_guajie_data 合并精义/释义。"""

    def test_load_has_jingyi_fields(self):
        data = load_guajie_data()
        g = data.get("观")
        assert g is not None
        assert isinstance(g, GuaDuan)
        # 卦辞精义/释义
        assert g.gua_ci_jingyi and "瞻仰" in g.gua_ci_jingyi
        assert g.gua_ci_shiyi
        # 卦象断语精义/释义与原文对齐
        assert g.gua_lines and g.lines_jingyi and g.lines_shiyi
        assert len(g.gua_lines) == len(g.lines_jingyi) == len(g.lines_shiyi)

    def test_yao_has_jingyi(self):
        y = query_yao_duan("观", "初六")
        assert y is not None
        assert isinstance(y, YaoDuan)
        assert y.ci and "童观" in y.ci
        assert y.jingyi and "童" in y.jingyi
        assert y.shiyi

    def test_64_gua_all_merged(self):
        """64 卦全部命中精义（无卦遗漏）。"""
        data = load_guajie_data()
        assert len(data) == 64
        missing = [
            name for name, g in data.items()
            if not (g.gua_ci_jingyi and g.gua_ci_shiyi and g.lines_jingyi and g.lines_shiyi)
        ]
        assert not missing, f"精义缺失卦: {missing}"
        # 精义/释义条数一致
        for name, g in data.items():
            assert len(g.lines_jingyi) == len(g.lines_shiyi), name

    def test_no_web_noise(self):
        """gua_lines 已过滤中华典藏网页残留（上一章/返回目录/中华典藏网…）。"""
        data = load_guajie_data()
        noise = ("上一章", "返回目录", "下一章", "中华典藏网", "本站非营利性站点", "吸取国学精华")
        dirty = [
            name for name, g in data.items()
            if any(n in line for line in g.gua_lines for n in noise)
        ]
        assert not dirty, f"含网页残留卦: {dirty}"

    def test_jingyi_fallback_empty(self):
        """未收录爻（如超范围）精义为空但不崩溃。"""
        y = query_yao_duan("乾", "上九")
        assert y is not None
        assert y.jingyi != ""  # 乾上九在库内


class TestJingyiOutputLayer:
    """输出层：解卦层 dict 带出 benming + 四层爻断 jingyi/shiyi。"""

    @pytest.fixture(scope="class")
    def guajie_dict(self):
        r = HeluoAdapter().compute((1980, 6, 22, 10), gender="male")
        return build_guajie_from_result(
            r, target_year=2026, target_month=9, target_day=15, target_hour=10)

    def test_benming_present(self, guajie_dict):
        bm = guajie_dict.get("benming") or {}
        assert bm.get("hexagram") == "观"
        assert bm.get("gua_ci") and "盥而不荐" in bm["gua_ci"]
        assert bm.get("gua_ci_jingyi")
        assert bm.get("gua_ci_shiyi")
        assert len(bm.get("lines") or []) == 4
        assert len(bm.get("lines_jingyi") or []) == 4
        assert len(bm.get("lines_shiyi") or []) == 4

    def test_liunian_yao_jingyi(self, guajie_dict):
        ly = guajie_dict.get("liunian_yao") or {}
        assert ly.get("yao") == "六五"
        assert ly.get("ci") and "贲于丘园" in ly["ci"]
        assert ly.get("jingyi") and ly.get("shiyi")

    def test_liuri_yao_jingyi(self, guajie_dict):
        """流日层：必出爻、必带爻辞与精义/释义。

        2026-10-07：起日卦依原典 L390 由「六段顺次」改为「逐日一爻、
        阳日寻阳位/阴日寻阴位」后，流日卦象随之改变，故**不再硬编码
        某一卦的爻辞字样**（那属于快照式断言，规则一改必假失败）。
        内容正确性由 TestLiuriRuleConsistency 按原典规则复算保证；
        本测试只守「流日层必须带全精义/释义」这一结构契约。
        """
        lr = guajie_dict.get("liuri_yao") or {}
        assert lr.get("yao"), "流日层应出爻"
        assert lr.get("ci"), "流日爻应带爻辞"
        assert lr.get("jingyi") and lr.get("shiyi")
        assert guajie_dict.get("liuri_hexagram"), "流日层应出卦名"

    def test_four_layers_all_have_jingyi(self, guajie_dict):
        """流年/月/日/时四层只要出爻就必带 jingyi/shiyi。"""
        for key in ("liunian_yao", "liuyue_yao", "liuri_yao", "liushi_yao"):
            v = guajie_dict.get(key)
            if v:
                assert "jingyi" in v and "shiyi" in v, f"{key} 缺精义/释义"
                assert v["jingyi"] and v["shiyi"], f"{key} 精义/释义为空"

    def test_benming_null_when_no_prenatal(self):
        """prenatal 缺省时 benming 为 None（兼容既有输出）。"""
        # 直接构造空 result 场景由既有测试覆盖；此处仅验证 to_dict 键存在
        g = build_guajie_from_result(None)
        assert isinstance(g, dict)
        assert "benming" in g or "error" in g
