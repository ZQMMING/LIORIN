# -*- coding: utf-8 -*-
"""「OCR 疑义不得放过」守卫（2026-10-24 新增）。

纪律
----
**本地 OCR 识别有疑义时，不得放过** —— 依次走三条通道取证：
  ① 多底本异文对照（同书的另一底本/另一 OCR 引擎不讹 ⇒ 该处即 OCR 讹）；
  ② 影印原件逐页目视（唯一能定「原书用字」的通道）；
  ③ 互联网多源（人名字号、书名通行本、术语考据）。

本守卫把纪律变成**硬断言**：
  1. 校记必须有「多通道取证」章节，且**必须提到互联网通道**（不许只用本地就宣称定论）；
  2. 校记登记的**每一条疑讹**都必须带**定论状态**（已定论 / 部分定论 / 待核）——
     不许留「裸疑点」；
  3. **引擎实际引用的每一条原典句**都必须能在包内 ``orig/`` **逐字回查**
     （底本实际写法，含 OCR 讹字）—— 否则就是「引用了包外原文」；
  4. 上述关键句必须在校记的取证表里**有对应记录**（不许代码引了、文档没记）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

ORIG = _REPO / "src" / "heluo_engine" / "orig"
NOTE = ORIG / "河洛理数_年卦月卦切片_校记.md"
SLICE = ORIG / "河洛理数_年卦月卦切片.txt"

#: 引擎**实际引用**的原典句（**底本实际写法**，含 OCR 讹字）
#: ⇒ (用途, 底本形态原句)
ENGINE_CITED = [
    ("日卦六日制（gua6 口径）", "日卦者每月變五卦每卦管六日方成一月五六三"),
    ("日卦六日制（K3-448 同源句）", "其餘五交五舞一卦管六日"),
    ("每日添一刻七分天（流日时刻推移）", "以此推之则每日添一刻七分天六日"),
    ("刻七分六日（K3-447 同源句）", "刻七分六目数過一時是也"),
    ("六十卦每卦管六日", "已上六十卦每一卦冬管六日"),
    ("每卦管六日之补充", "六十目每一日各坐一交亦可照日卦"),
    ("十二辟卦爻位-节气对照", "坎一初文起冬至二文寒三文大寒"),
    ("爻位-节气对照（K3-448 段）", "交春白五交两水〇上久击初交起春分夕二交清明三雨"),
    ("候卦九十日 / 十五日", "卦每一卦各管九十日自初交而至上支每一交各臂十五日也"),
    ("小象阳爻九阳运行例", "小象陽交九年運行例"),
    ("起日卦定式", "起目卦定式"),
    ("起月卦之式（卷目次）", "起月卦之式"),
    ("起日卦之式（卷目次）", "起日卦之式"),
    ("起日卦例·逐日一爻", "挨次而变，不容紊也"),
    ("起月卦例·准正月起", "要从人所生之月准正月起"),
]


def _flat(text: str) -> str:
    """归一化：去空白 + **去 markdown 强调标记**（否则 `「坎一初**文**起冬至」`
    与底本形态 `「坎一初文起冬至」` 对不上）。"""
    text = re.sub(r"[*`]", "", text)
    return re.sub(r"\s+", "", text)


@pytest.fixture(scope="module")
def pkg_flat() -> str:
    return _flat("\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in sorted(ORIG.glob("*.txt"))))


class TestEngineCitedLinesAreInPackage:
    """★ 引擎引用的原典句必须**包内可逐字回查**（杜绝「包外依赖」）。"""

    def test_all_engine_cited_lines_present(self, pkg_flat):
        missing = [f"{desc}：{line}"
                   for desc, line in ENGINE_CITED
                   if _flat(line) not in pkg_flat]
        assert not missing, (
            "以下引擎实际引用的原典句在包内 orig/ 查不到（切片缺口）：\n  "
            + "\n  ".join(missing))

    def test_cited_lines_exist_in_new_slice(self):
        """其中「日卦定式/時刻法/爻位对照」一段必须落在**新增的 S7 段**里。"""
        txt = SLICE.read_text(encoding="utf-8")
        for line in ("以此推之则每日添一刻七分天六日",
                     "其餘五交五舞一卦管六日",
                     "卦每一卦各管九十日自初交而至上支每一交各臂十五日也"):
            assert _flat(line) in _flat(txt), (
                f"S7 段缺引擎引用的原典句：{line}")


class TestDoubtRegisterIsClosed:
    """疑讹登记必须**有定论状态**（不留裸疑点）。"""

    NOTE_TEXT = NOTE.read_text(encoding="utf-8")

    def test_note_has_multi_channel_section(self):
        heads = [l for l in self.NOTE_TEXT.splitlines() if l.startswith("## ")]
        assert any("多通道取证" in h for h in heads), (
            f"校记缺「多通道取证」章节；现有章节：{heads}")

    def test_note_mentions_internet_channel(self):
        """必须提到**互联网**通道 —— 只用本地就宣称定论是不够的。"""
        assert "互联网" in self.NOTE_TEXT, "校记未记录互联网取证通道"

    def test_doubt_rows_have_verdict_status(self):
        """疑讹登记的每一行都要有定论状态标记。"""
        statuses = ("已定论", "部分定论", "待核")
        bad = []
        for ln in self.NOTE_TEXT.splitlines():
            if not ln.strip().startswith("| L"):
                continue
            if not any(s in ln for s in statuses):
                bad.append(ln.strip()[:90])
        assert not bad, "以下疑讹行没有定论状态（裸疑点）：\n  " + "\n  ".join(bad)

    def test_key_sentences_recorded_in_verification_table(self):
        """引擎引用的关键句必须在校记的**取证表**里有记录。"""
        flat = _flat(self.NOTE_TEXT)
        for line in ("日卦者每月變五卦每卦管六日",
                     "刻七分六目数過一時",
                     "小象陽交九年運行例",
                     "起目卦定式",
                     "坎一初文起冬至"):
            assert _flat(line) in flat, f"校记取证表缺记录：{line}"


class TestVerificationToolsExist:
    """取证工具必须**随仓可复跑**（取证结论可被重做）。"""

    @pytest.mark.parametrize("name", [
        "tools/heluo/verify_ocr_doubt.py",
        "tools/heluo/cross_ocr_align.py",
        "tools/heluo/extract_orig_slice.py",
    ])
    def test_tool_exists(self, name):
        p = _REPO / name
        assert p.exists(), f"取证工具缺失：{name}"
        txt = p.read_text(encoding="utf-8", errors="replace")
        assert txt.strip(), f"取证工具是空文件：{name}"
