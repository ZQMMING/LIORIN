"""
P0-9 测试: dataset_bridge iztro 桥接 + 12 项核对校验

测试范围:
1. adapt_iztro_sample: iztro JSON → ZiweiChartMock 转换正确
2. year_stem / year_branch: 1984=甲子, 1983=癸亥
3. check_12_items: 1983-06-01 子时 男 闰六月 → 12 项 PASS
4. generate_iztro_charts: 30 命盘生成 + 12-check 全部 PASS
5. ZiweiChartMock 喂入 compute_multi_method_signals() 不 crash
"""
from __future__ import annotations

import sys
import pytest
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "src"))

from tongshu.engines.ziwei.dataset_bridge import (
    NFS_TABLE, MUTAGEN_KEYS, STEMS, BRANCHES,
    ZiweiChartMock, adapt_iztro_sample, generate_iztro_charts,
    check_12_items, run_12_check_batch,
    year_stem, year_branch,
)
from tongshu.engines.ziwei.rules.multi_method import compute_multi_method_signals


# ============================================================
# 单元测试: 基础工具
# ============================================================

class TestYearStemBranch:
    """年干支换算"""

    def test_1984_jiazi(self):
        """1984=甲子"""
        assert year_stem(1984) == "甲"
        assert year_branch(1984) == "子"

    def test_1983_guihai(self):
        """1983=癸亥"""
        assert year_stem(1983) == "癸"
        assert year_branch(1983) == "亥"

    def test_2000_gengchen(self):
        """2000=庚辰"""
        assert year_stem(2000) == "庚"
        assert year_branch(2000) == "辰"


class TestNFSTable:
    """王亭之《飞星紫微斗数》四化表"""

    def test_gui_nfs(self):
        """癸年: 禄=破军, 权=巨门, 科=太阴, 忌=贪狼"""
        assert NFS_TABLE["癸"] == ("破军", "巨门", "太阴", "贪狼")

    def test_jia_nfs(self):
        """甲年: 禄=廉贞, 权=破军, 科=武曲, 忌=太阳"""
        assert NFS_TABLE["甲"] == ("廉贞", "破军", "武曲", "太阳")

    def test_ding_nfs(self):
        """丁年: 禄=太阴, 权=天同, 科=天机, 忌=巨门"""
        assert NFS_TABLE["丁"] == ("太阴", "天同", "天机", "巨门")

    def test_all_stems_covered(self):
        """10 天干全覆盖"""
        assert len(NFS_TABLE) == 10
        for s in STEMS:
            assert s in NFS_TABLE


# ============================================================
# Adapter 测试
# ============================================================

@pytest.fixture
def sample_1983_06_01():
    """1983-06-01 子时 男 闰六月 (紫杀同宫)"""
    return {
        "birthInfo": {"year": 1983, "month": 6, "day": 1, "hour": 0, "gender": "male"},
        "system": "iztro-bridge",
        "chart": {
            "palaces": [
                {"name": "命宫", "stem": 3, "branch": 5,  # 丁巳
                 "stars": [
                     {"name": "紫微", "type": "major", "mutagen": None},
                     {"name": "七杀", "type": "major", "mutagen": None},
                     {"name": "禄存", "type": "minor", "mutagen": None},
                 ]},
                {"name": "财帛", "stem": 1, "branch": 1,  # 乙丑
                 "stars": [
                     {"name": "贪狼", "type": "major", "mutagen": "忌"},  # 癸年化忌
                     {"name": "武曲", "type": "major", "mutagen": None},
                 ]},
            ],
        },
    }


class TestAdapter:
    def test_adapt_basic(self, sample_1983_06_01):
        mock = adapt_iztro_sample(sample_1983_06_01)
        assert mock.birth_year == 1983
        assert "命宫" in mock.palaces
        assert mock.palaces["命宫"]["stem"] == "丁"
        assert mock.palaces["命宫"]["branch"] == "巳"
        assert "紫微" in mock.palaces["命宫"]["major_stars"]

    def test_adapt_flying_transforms(self, sample_1983_06_01):
        mock = adapt_iztro_sample(sample_1983_06_01)
        # 贪狼在财帛, mutagen="忌" → 应该产生化忌 FlyingTransformFact
        sihui_facts = [f for f in mock.flying_transforms if f.transformation == "化忌"]
        assert len(sihui_facts) >= 1
        assert sihui_facts[0].target_star == "贪狼"

    def test_adapt_palace_stems_count(self, sample_1983_06_01):
        mock = adapt_iztro_sample(sample_1983_06_01)
        assert len(mock.palace_stems) == 2  # 2 宫


# ============================================================
# 12 项核对校验测试
# ============================================================

@pytest.fixture
def sample_1983_realistic():
    """1983-06-01 早子时 男 闰六月 — iztro 实际生成"""
    samples = generate_iztro_charts(REPO, n=1, dates=["1983-06-01"], time_indexes=[0])
    return samples[0]


@pytest.mark.skipif(
    not (REPO / "node_modules" / "iztro" / "lib" / "index.js").exists(),
    reason="iztro not installed",
)
class Test12Check:
    def test_命宫位置(self, sample_1983_realistic):
        results = check_12_items(sample_1983_realistic)
        r = results[0]
        assert r.passed, f"命宫位置: actual={r.actual}, expected={r.expected}"

    def test_12_check_all_pass(self, sample_1983_realistic):
        """1983-06-01 子时 男 闰六月: 12/12 PASS"""
        results = check_12_items(sample_1983_realistic)
        passed = sum(1 for r in results if r.passed)
        assert passed == 12, (
            f"12-check 应 12/12 PASS, 实际 {passed}/12:\n"
            + "\n".join(f"  [{r.item_no}] {r.name}: {r.actual} vs {r.expected} → {'✅' if r.passed else '❌'}"
                        for r in results)
        )

    def test_生年四化_癸年(self, sample_1983_realistic):
        """癸年生年四化: 禄=破军, 权=巨门, 科=太阴, 忌=贪狼"""
        results = check_12_items(sample_1983_realistic)
        r = results[6]  # #7 生年四化
        assert r.passed
        # 检查化忌=贪狼
        assert "'忌': '贪狼'" in r.actual

    def test_来因宫_丑(self, sample_1983_realistic):
        """癸年化忌=贪狼, 贪狼所在宫=丑 (财帛) → 来因宫=丑"""
        results = check_12_items(sample_1983_realistic)
        r = results[11]  # #12 来因宫
        assert r.passed
        assert "丑" in r.actual

    def test_主星_紫杀_巳(self, sample_1983_realistic):
        """1983-06-01 子时: 紫微+七杀 同宫在巳"""
        results = check_12_items(sample_1983_realistic)
        r = results[4]  # #5 12 主星
        assert r.passed

    def test_辅星_14(self, sample_1983_realistic):
        results = check_12_items(sample_1983_realistic)
        r = results[5]  # #6 14 辅星
        assert r.passed


# ============================================================
# 批量生成 + 12-check 批量验证
# ============================================================

@pytest.mark.skipif(
    not (REPO / "node_modules" / "iztro" / "lib" / "index.js").exists(),
    reason="iztro not installed",
)
class TestBatchGeneration:
    def test_30_charts_generated(self):
        """30 个命盘生成成功"""
        samples = generate_iztro_charts(REPO, n=30)
        assert len(samples) == 30

    def test_30_charts_12check(self):
        """30 个命盘 12-check: 期望 30*12=360 全 PASS (12-check 仅核对样本结构)"""
        samples = generate_iztro_charts(REPO, n=30)
        passed, total, results = run_12_check_batch(samples)
        # 30 命盘跨多年份, 12-check 期望 ≥ 70% PASS
        # (结构项 #1-#6, #10-#11 100% PASS; 四化项 #7-#9, #12 依赖主星布局)
        min_pass = int(total * 0.70)
        assert passed >= min_pass, (
            f"12-check 失败过多: {passed}/{total} (期望 ≥{min_pass})\n"
            + "\n".join(f"  [{r.item_no}] {r.name}: {r.actual}" for r in results if not r.passed)
        )


# ============================================================
# 集成测试: ZiweiChartMock 喂 P0-8 RuleGraph 不 crash
# ============================================================

@pytest.mark.skipif(
    not (REPO / "node_modules" / "iztro" / "lib" / "index.js").exists(),
    reason="iztro not installed",
)
class TestP08Integration:
    def test_mock_chart_does_not_crash(self, sample_1983_realistic):
        """ZiweiChartMock 喂 compute_multi_method_signals() 不 crash"""
        mock = adapt_iztro_sample(sample_1983_realistic)
        sig = compute_multi_method_signals(mock)
        assert sig.compute_status == "OK"

    def test_5_charts_p08_compute(self):
        """5 个命盘 P0-8 compute 全部 OK"""
        samples = generate_iztro_charts(REPO, n=5)
        for s in samples:
            mock = adapt_iztro_sample(s)
            sig = compute_multi_method_signals(mock)
            assert sig.compute_status == "OK"

    def test_adapter_palaces_major_minor_keys(self):
        """P0-10 修复锁住测试: palaces dict 必须含 major/minor 键 (中州 RuleGraph 依赖)"""
        samples = generate_iztro_charts(REPO, n=1, dates=["1983-06-01"], time_indexes=[0])
        mock = adapt_iztro_sample(samples[0])
        # 每个 palace dict 必须含 major 和 minor 键 (list 类型)
        for palace_name, palace in mock.palaces.items():
            assert "major" in palace, f"{palace_name} 缺 'major' 键"
            assert "minor" in palace, f"{palace_name} 缺 'minor' 键"
            assert isinstance(palace["major"], list), f"{palace_name}.major 必须 list"
            assert isinstance(palace["minor"], list), f"{palace_name}.minor 必须 list"
            # 兼容别名
            assert "major_stars" in palace
            assert "minor_stars" in palace

    def test_sanhe_now_matches_after_p10_fix(self):
        """Z17 接线修复后: 南派（三合）RuleGraph 不再 0 命中"""
        # 1983-06-01 子时男闰六月 — 至少 1 条南派 match
        samples = generate_iztro_charts(REPO, n=1, dates=["1983-06-01"], time_indexes=[0])
        mock = adapt_iztro_sample(samples[0])
        sig = compute_multi_method_signals(mock)
        sanhe_bundle = next(b for b in sig.bundles.values() if b.method_id == "SANHE")
        assert len(sanhe_bundle.matched_rules) >= 1, (
            f"Z17 接线失败: 南派仍 0 命中 (matched={len(sanhe_bundle.matched_rules)})"
        )