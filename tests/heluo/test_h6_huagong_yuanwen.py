"""H6 化工：按原典《河洛真数·起例卷之上·化工论》核验四季映射与三层判据（D-019）。

原典明文：
  坎卦自冬至十一月中以后至惊蛰终止。
  震卦自春分二月中以后至芒种终止。
  离卦自夏至五月中以后至白露终止。
  兑卦自秋分八月中以后至大雪终止。
  坤艮卦主四季辰戌丑未月，除正节气十二日外，各旺十八日。妇人得此，名儿女星，
  又为贞母节妇。
  正不逢而互体得之；若正互俱无，则取纳甲纳音，终是浅薄，福寿减半。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from tongshu.engines.heluo.hua_gong import (  # noqa: E402
    HuaGongState,
    compute_huagong,
    hu_trigrams,
    TU_WANG_BRANCHES,
    TU_WANG_TRIGRAMS,
    SEASON_BRANCH_TO_HUAGONG,
)

RAW = REPO / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之上.txt"

# 原典四句 → 月支区间（节气月：冬至=子月中，惊蛰=卯月节，春分=卯月中，
# 芒种=午月节，夏至=午月中，白露=酉月节，秋分=酉月中，大雪=子月节）
YUANWEN_MONTH_RANGES = {
    "坎": ("子", "丑", "寅"),
    "震": ("卯", "辰", "巳"),
    "离": ("午", "未", "申"),
    "兑": ("酉", "戌", "亥"),
}


def _raw_text() -> str:
    return RAW.read_text(encoding="utf-8")


class TestYuanwenMapping:
    def test_yuanwen_sentences_present(self):
        text = _raw_text()
        for sentence in (
            "坎卦自冬至十一月中以后至惊蛰终止",
            "震卦自春分二月中以后至芒种终止",
            "离卦自夏至五月中以后至白露终止",
            "兑卦自秋分八月中以后至大雪终止",
            "坤艮卦主四季辰戌丑未月",
        ):
            assert sentence in text, sentence

    @pytest.mark.parametrize("branch,trigram", [
        ("子", "坎"), ("丑", "坎"), ("寅", "坎"),
        ("卯", "震"), ("辰", "震"), ("巳", "震"),
        ("午", "离"), ("未", "离"), ("申", "离"),
        ("酉", "兑"), ("戌", "兑"), ("亥", "兑"),
    ])
    def test_branch_to_trigram_follows_yuanwen(self, branch, trigram):
        assert SEASON_BRANCH_TO_HUAGONG[branch] == trigram
        assert branch in YUANWEN_MONTH_RANGES[trigram]

    def test_mapping_is_exact_partition(self):
        """12 月支一一对应，无遗漏无重复（且与旧表错位一月的写法不同）。"""
        assert set(SEASON_BRANCH_TO_HUAGONG) == set("子丑寅卯辰巳午未申酉戌亥")
        for tri, branches in YUANWEN_MONTH_RANGES.items():
            assert {b for b in SEASON_BRANCH_TO_HUAGONG if SEASON_BRANCH_TO_HUAGONG[b] == tri} == set(branches)

    def test_opposite_spans_follow_yuanwen(self):
        """化工相反图：坎反离主夏至后秋分前（=离月见坎为反）；震反兑主秋分后冬至前。"""
        text = _raw_text()
        assert "坎卦反离，主夏至以后秋分前" in text
        assert "离卦反坎，主冬至以后春分前" in text
        assert "兑卦反震，主春分以后夏至前" in text
        assert "震卦反兑，主秋分以后冬至前" in text


class TestHuaGongLayers:
    def test_tu_wang_branches(self):
        assert TU_WANG_BRANCHES == ("辰", "戌", "丑", "未")
        assert TU_WANG_TRIGRAMS == ("坤", "艮")

    def test_tu_wang_month_kun_gen_is_huagong(self):
        """四季月（辰）见坤 → 土旺化工（原典：坤艮主四季月，各旺十八日）。"""
        r = compute_huagong("坤", "震", "乾", "震", "辰", gender="female")
        assert r.state is HuaGongState.NORMAL
        assert r.scope == "土旺"
        assert r.tu_wang is True
        assert any("儿女星" in e for e in r.evidence)

    def test_male_no_nverxing_note(self):
        r = compute_huagong("坤", "震", "乾", "震", "辰", gender="male")
        assert r.scope == "土旺"
        assert not any("儿女星" in e for e in r.evidence)

    def test_hu_trigrams_example(self):
        # 乾上坎下（天水讼）：上互乾、下互离
        assert hu_trigrams("乾", "坎") == ("巽", "离")
        assert hu_trigrams("乾", "乾") == ("乾", "乾")
        assert hu_trigrams("坤", "坤") == ("坤", "坤")

    def test_hu_ti_fallback(self):
        """午月（离）正体无离，但兑兑互体含离 → 互体得化工（原典：正体若无，须看互体）。"""
        r = compute_huagong("兑", "兑", "兑", "兑", "午")
        assert r.state is HuaGongState.NORMAL
        assert r.scope == "互体"
        assert any("互体得离" in e for e in r.evidence)

    def test_nayin_fallback_weak(self):
        """正互俱无，纳音火与化工离同气 → 得化工但浅薄（福寿减半）。"""
        r = compute_huagong("乾", "乾", "乾", "乾", "午", nayin_element="火")
        assert r.state is HuaGongState.NORMAL
        assert r.scope == "纳音"
        assert r.weak is True
        assert any("福寿减半" in e for e in r.evidence)

    def test_nayin_sheng_huagong(self):
        """纳音木生离火 → 亦得，仍记浅薄。"""
        r = compute_huagong("乾", "乾", "乾", "乾", "午", nayin_element="木")
        assert r.scope == "纳音"
        assert r.weak is True

    def test_nayin_mismatch_unresolved(self):
        r = compute_huagong("乾", "乾", "乾", "乾", "午", nayin_element="金")
        assert r.state is HuaGongState.UNRESOLVED
        assert r.scope == ""

    def test_reverse_when_only_opposite(self):
        """午月（离）只见坎（反卦）、互体无离 → 反位。"""
        r = compute_huagong("坎", "坎", "坎", "坎", "午")
        assert r.state is HuaGongState.REVERSE
        assert r.has_opposite and not r.has_huagong

    def test_zhangluo_evidence_mentions_original_text(self):
        r = compute_huagong("乾", "震", "乾", "震", "卯")
        assert any("当令化工卦=震" in e for e in r.evidence)
        joined = "\n".join(r.evidence)
        assert re.search(r"出生月支卯", joined)
