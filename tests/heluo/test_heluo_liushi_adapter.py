# -*- coding: utf-8 -*-
"""河洛适配器 流时层接线测试（D-023）.

背景：`HeluoAdapter.compute_from_chart` 曾注释「流时卦（target_hour）剥离不接」，
生产适配器不接收时刻，`build_guajie_from_result` 的 `target_hour` 分支永远走不到。

本测试锁死：①传 target_hour（1=子 … 12=亥）时解卦层挂出 liushi_yao；
②不传时 liushi_yao 为空（不臆造）；③不同时辰取到不同爻（证明 target_hour 真被消费）；
④与 guajie 直调结果逐字段一致（证明适配器只是透传，不另算）。
"""

from __future__ import annotations

import pytest

from tongshu.engines.heluo_adapter import HeluoAdapter
from tongshu.engines.heluo.guajie import build_guajie_from_result
from tongshu.engines.bazi_engine import BaziEngine

BIRTH = (1980, 6, 22, 10)
TARGET = dict(target_year=2026, target_month=9, target_day=1)


@pytest.fixture(scope="module")
def adapter() -> HeluoAdapter:
    return HeluoAdapter()


def _result(adapter: HeluoAdapter, hour):
    return adapter.compute(BIRTH, "male", target_hour=hour, **TARGET)


def test_no_hour_means_no_liushi(adapter):
    g = _result(adapter, None).guajie
    assert g is not None
    assert not g.get("liushi_yao")


@pytest.mark.parametrize("hour", [1, 3, 6, 9, 12])
def test_hour_wires_liushi(adapter, hour):
    g = _result(adapter, hour).guajie
    assert g is not None
    d = g.get("liushi_yao")
    assert d, f"target_hour={hour} 未挂出流时爻断"
    assert d.get("yao"), "流时爻名缺失"
    assert d.get("ci"), "流时爻辞缺失"


def test_hours_produce_different_yao(adapter):
    yao = {}
    for hour in (1, 6, 12):
        d = _result(adapter, hour).guajie["liushi_yao"]
        yao[hour] = (d["yao"], d["ci"])
    assert len(set(yao.values())) == 3, f"不同时辰应取不同爻：{yao}"


def test_adapter_matches_direct_guajie_call(adapter):
    """适配器结果必须与 build_guajie_from_result 直调逐字段一致。"""
    r = _result(adapter, 2)
    g_direct = build_guajie_from_result(
        # 用同一张盘重算 base result，再直调解卦层
        HeluoAdapter()._canonical.calculate(
            bazi=_bazi_of(adapter), gender="male",
            birth_hour="巳", era="zhong",
            birth_year=1980, birth_date="1980-06-22",
        ),
        bazi=_bazi_of(adapter),
        target_hour=2,
        **TARGET,
    )
    assert r.guajie["liushi_yao"] == g_direct["liushi_yao"]


def _bazi_of(adapter: HeluoAdapter):
    chart = BaziEngine().compute(BIRTH, gender="male")
    from tongshu.engines.bazi_engine import STEM_CN, BRANCH_CN
    return [
        (STEM_CN[chart.year_pillar.heavenly_stem], BRANCH_CN[chart.year_pillar.earthly_branch]),
        (STEM_CN[chart.month_pillar.heavenly_stem], BRANCH_CN[chart.month_pillar.earthly_branch]),
        (STEM_CN[chart.day_pillar.heavenly_stem], BRANCH_CN[chart.day_pillar.earthly_branch]),
        (STEM_CN[chart.hour_pillar.heavenly_stem], BRANCH_CN[chart.hour_pillar.earthly_branch]),
    ]
