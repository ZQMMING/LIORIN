# -*- coding: utf-8 -*-
"""原典切片的**多维保真守卫**（2026-10-24）。

**这个守卫盯住什么**

切片 `heluo_engine/orig/` 是河洛引擎的**原典权威文本**。它一旦被悄悄改动 ——
删一段、改一个字、调换两行 —— 引擎**照单全收**地照着算，而现有守卫
（表一致性、接口形状、变异演练）**全都发现不了**：
数据变了，结构没变。

本守卫把「切片是可信的」变成可回归的断言，五个维度：

1. **结构钉死**：每个切片文件的行数 + 内容哈希固定 ⇒ 任何改动都会红，
   逼改动走「显式留档 + 更新常量」的流程，而不是悄悄发生。
2. **噪音边界**：网页抓取残留（标题/标语/CSS/导航）**只允许出现在头尾**，
   且位置固定 ⇒ 内容区行号不会漂移（内容区行号是外部锚点的换算依据）。
3. **判词库回查**：判词库 7 个字段的**每一条**都必须在切片里逐字命中
   （整串连续，跨段摘句按分句全覆盖）⇒ 判词不得凭空。
4. **关键依据在包内**：判据层最关键的 12 条原典依据必须**能在包内切片回查**
   ⇒ 杜绝「包外依赖」悄悄出现。
5. **行号映射自洽**：`orig/行号映射.md` 与切片实际行数一致 ⇒ 映射表不腐烂。

**不做的事**：不校验切片与**包外底本**是否一致（那需要 `D:\\顺天系统资料`，
服务器上没有）。底本一致性由《原典切片多维验证报告_20261024.md》留证。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
ORIG = ROOT / "src" / "heluo_engine" / "orig"

# ── 维度1：切片清单钉死（文件名 → 行数, 内容 sha256 前 16 位）──
# ⚠ 任何**有意**的改动都必须：改这里 + 在
#   `src/heluo_engine/docs/原典切片多维验证报告_20261024.md` 留证，
#   否则守卫会红 —— 这是刻意的：切片变更必须显式、可追溯。
SLICE_LOCK = {
    "崇祯五年刻本_卷六_识典整理.txt": (443, "2cf5c7d26703f553"),
    "易卦释义_上经卷之上.txt": (836, "79465b27e2652963"),
    "易卦释义_上经卷之下.txt": (653, "151a067ded70462c"),
    "易卦释义_下经卷之上.txt": (608, "b7bdd0f5d287fe21"),
    "易卦释义_下经卷之下.txt": (559, "e2794159cc107a36"),
    "易卦释义_下经卷之中.txt": (562, "f8dfb7897432143f"),
    "河洛理数_日卦起例卷.txt": (332, "bf0082baf1b972f0"),
    "河洛理数_关键条文切片.txt": (3072, "e0d5231fcabeee31"),
    "河洛真数_起例卷之上.txt": (279, "9c97489abb122270"),
    "河洛真数_起例卷之下.txt": (143, "4231253574c50b5f"),
    "河洛真数_起例卷之中.txt": (213, "1d0b226ff807050a"),
    "诗断秘诀卷之上.txt": (1497, "06a81dcdcf3e918b"),
    "诗断秘诀卷之下.txt": (1682, "29b487c89b0aa0c6"),
}

# ── 维度2：抓取噪音特征（只允许在头尾）──
NOISE_RE = re.compile(
    r"中华典藏|吸取国学精华|传承中华文化|本站非营利性站点|陈邵二先生|陈图南先生"
    r"|_河洛真数_邵雍_在线阅读|\(默认\)\s*18px|以方便网友为主|仅供学习"
    r"|河洛真数邵雍作品集|上一章|返回目录|下一章"
)

# ── 维度4：判据层关键依据（必须能在包内切片逐字回查；繁简双写）──
#   每条 = (说明, 简体写法, 繁体写法)
KEY_ANCHORS = [
    ("十体分级·贵命十体", "大概爻位名体援势理时辞吉", "大概爻位名體援勢理時辭吉"),
    ("六才例·应爻=元堂隔三位", "假如同人九三爻是元堂", "假如同人九三爻是元堂"),
    ("六才例·泰卦九二", "又假如小象是泰卦九二", "又假如小象是泰卦九二"),
    ("四季旺时·辰戌丑未各旺十八日", "坤艮卦主四季", "坤艮卦主四季"),
    ("一卦名吉规则", "一卦名吉", "一卦名吉"),
    ("三辞吉规则", "三辞吉", "三辭吉"),
    ("起时卦例·两法并通", "二法皆通，前法为优", "二法皆通，前法為優"),
    ("纳甲歌诀三十组", "纳甲歌诀", "納甲歌訣"),
    ("财富意象·金玉龍麟", "金玉龙麟", "金玉龍麟"),
    ("参评诗断·空无字损寿", "空无字", "空無字"),
    ("元气相反（反悖）", "元气相反", "元氣相反"),
    ("化工（判据层核心机制）", "化工者，天地生生化化之妙也", "化工者，天地生生化化之妙也"),
]

# ── 维度5：行号映射表 ──
LINEMAP = ORIG / "行号映射.md"


def _all_slice_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8", errors="replace")
                     for p in sorted(ORIG.glob("*.txt")))


FLAT = re.sub(r"\s+", "", _all_slice_text())


class TestSliceStructureLocked(unittest.TestCase):
    """维度1：切片清单钉死。"""

    def test_slice_set_matches_lock(self):
        actual = {p.name for p in ORIG.glob("*.txt")}
        self.assertEqual(actual, set(SLICE_LOCK),
                         "orig/ 下的切片文件集合与锁定清单不符")

    def test_slice_line_count_and_hash(self):
        for name, (n_lines, sha) in SLICE_LOCK.items():
            with self.subTest(slice=name):
                p = ORIG / name
                self.assertTrue(p.exists(), f"缺切片 {name}")
                t = p.read_text(encoding="utf-8")
                self.assertEqual(len(t.splitlines()), n_lines,
                                 f"{name} 行数变了（原 {n_lines}）—— "
                                 "切片变更须留档并更新 SLICE_LOCK")
                self.assertEqual(hashlib.sha256(t.encode()).hexdigest()[:16], sha,
                                 f"{name} 内容变了 —— 切片变更须留档并更新 SLICE_LOCK")


class TestNoiseOnlyAtEdges(unittest.TestCase):
    """维度2：抓取噪音只允许在头尾（内容区行号不得漂移）。"""

    def test_noise_lines_are_edge_only(self):
        for name in SLICE_LOCK:
            with self.subTest(slice=name):
                lines = (ORIG / name).read_text(encoding="utf-8").splitlines()
                n = len(lines)
                noise_idx = [i for i, l in enumerate(lines, 1) if NOISE_RE.search(l)]
                if not noise_idx:
                    # 该切片不是网页抓取来的（崇祯刻本识典 / 《河洛理数》OCR 底本），
                    # 本就没有抓取噪音 ⇒ 无需检查边界
                    continue
                head = [i for i in noise_idx if i <= 45]
                tail = [i for i in noise_idx if i > n - 45]
                mid = [i for i in noise_idx if i not in head and i not in tail]
                self.assertEqual(mid, [],
                                 f"{name} 中段出现抓取噪音行 {mid} —— "
                                 "中段行号是外部锚点的换算依据，不得被噪音污染")


class TestGuajieQuotesTraceableToSlices(unittest.TestCase):
    """维度3：判词库**结构**与**内容**都必须在切片里可回查。

    ⚠ 只查「存在的文本能否回查」是不够的 —— 删掉一条断语后，
    剩下的文本仍然都能回查，守卫会**恒绿**。故本类分两段：
      (a) 结构计数钉死（卦数 / 爻数 / 卦名集合 / 断语条数）；
      (b) 内容逐字回查（整串连续，或分句全覆盖）。
    """

    #: 判词库结构锁定（改动前须更新 + 留档）
    GUA_COUNT = 64
    YAO_PER_GUA = 6
    GUA_NAMES = (
        "乾 坤 屯 蒙 需 讼 师 比 小畜 履 泰 否 同人 大有 谦 豫 随 蛊 临 观 噬嗑 贲 剥 复 "
        "无妄 大畜 颐 大过 坎 离 咸 恒 遁 大壮 晋 明夷 家人 睽 蹇 解 损 益 夬 姤 萃 升 困 井 "
        "革 鼎 震 艮 渐 归妹 丰 旅 巽 兑 涣 节 中孚 小过 既济 未济"
    ).split()

    def test_structure_locked(self):
        data = json.loads(
            (ROOT / "src/heluo_engine/data/guajie_data.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data), self.GUA_COUNT, "卦数变了")
        self.assertEqual([g["name"] for g in data], self.GUA_NAMES,
                         "卦名集合/顺序变了（判词库是原典直录，不应改序）")
        for g in data:
            with self.subTest(gua=g["name"]):
                self.assertEqual(len(g.get("yaos") or []), self.YAO_PER_GUA,
                                 f"{g['name']} 爻数变了（应为 6 爻）")
                for y in (g.get("yaos") or []):
                    for k in ("yao", "ci", "xiang", "yi", "shao", "duans"):
                        self.assertIn(k, y, f"{g['name']}{y.get('yao')} 缺字段 {k}")
                    self.assertTrue(y.get("duans"),
                                    f"{g['name']}{y.get('yao')} 断语被清空 —— "
                                    "判词库每爻恒有断语（原典直录）")

    def test_gua_names_traceable_to_slices(self):
        """卦名本身也是原典（《周易》卦名），须在切片内出现。"""
        data = json.loads(
            (ROOT / "src/heluo_engine/data/guajie_data.json").read_text(encoding="utf-8"))
        miss = [g["name"] for g in data
                if re.sub(r"\s+", "", g["name"]) not in FLAT]
        self.assertEqual(miss, [], f"卦名在切片里查不到：{miss}")

    def test_all_fields_verbatim(self):
        data = json.loads(
            (ROOT / "src/heluo_engine/data/guajie_data.json").read_text(encoding="utf-8"))
        # 口径与 test_heluo_guajie_data_fidelity.py 一致：
        #   整串连续命中，或**分句全覆盖**（分句按句末标点切，短于 8 字的碎句不单独要求）
        sent_split = re.compile(r"[。；！？]")
        totals = {"整串": 0, "分句": 0, "底本原缺": 0}
        misses = []
        for g in data:
            parts = [g.get("gua_ci", "")] + list(g.get("lines") or [])
            for y in (g.get("yaos") or []):
                parts += [y.get("ci", ""), y.get("xiang", ""),
                          y.get("yi", ""), y.get("shao", "")]
                parts += list(y.get("duans") or [])
            for s in parts:
                if not s or len(s) < 4:
                    totals["底本原缺"] += 1
                    continue
                if re.sub(r"\s+", "", s) in FLAT:
                    totals["整串"] += 1
                    continue
                segs = [x for x in sent_split.split(s)
                        if len(re.sub(r"\s+", "", x)) >= 8]
                if segs and all(re.sub(r"\s+", "", x) in FLAT for x in segs):
                    totals["分句"] += 1
                else:
                    misses.append((g["name"], s[:60]))
        self.assertEqual(misses, [],
                         f"判词库有 {len(misses)} 条在切片里查不到：\n"
                         + "\n".join(f"  {n}: {s}" for n, s in misses[:10]))
        self.assertGreater(totals["整串"], 2000, "整串命中数异常偏少，回查口径可能失效")
        self.assertGreater(totals["分句"], 0, "分句回查分支从未被触发 —— 口径可能失效")


class TestKeyAnchorsInPackage(unittest.TestCase):
    """维度4：判据层关键依据必须包内可回查（杜绝包外依赖）。"""

    def test_key_anchors_present(self):
        missing = []
        for desc, simp, trad in KEY_ANCHORS:
            if (re.sub(r"\s+", "", simp) not in FLAT
                    and re.sub(r"\s+", "", trad) not in FLAT):
                missing.append(desc)
        self.assertEqual(missing, [],
                         "以下判据层关键依据在包内切片查不到（包外依赖）：\n  "
                         + "\n  ".join(missing))


class TestSliceHeaderDeclaresOcrBase(unittest.TestCase):
    """★ 切片**必须**如实声明底本是 OCR 文本（2026-10-24 影印核定后新增）。

    **为什么要有这个守卫**

    影印原件（`河洛理数_藏书阁K3-448_1632_OCR/.../p0035.png`、`p0037.png`）逐字核定后确认：
    切片的**行序 / 分栏顺序 / 断句位置 / 页标**与影印**完全一致**，
    差异**只在字形层** —— 底本是 **OCR 文本**，且经过**繁简转换**（简繁混排）。

    ⇒ 切片里的「错讹一仍其旧」指的是**保留 OCR 讹字**，**不是**保留原书错字。
    若页眉写成「原文逐字照抄」，读者会误以为它与影印原件逐字相同 ⇒ **误导**。

    故钉死：页眉须写明「OCR 底本」，且校记须有「影印核定」节。
    """

    SLICE = ORIG / "河洛理数_日卦起例卷.txt"
    NOTE = ORIG / "河洛理数_日卦起例卷_校记.md"

    def test_slice_header_says_ocr_base(self):
        head = "\n".join(self.SLICE.read_text(encoding="utf-8").splitlines()[:16])
        self.assertIn("OCR", head,
                      "切片页眉必须声明底本是 OCR 文本（否则读者会误以为与影印原件逐字相同）")
        self.assertIn("底本", head, "切片页眉必须列出底本")

    def test_caliber_note_has_scan_verification(self):
        note = self.NOTE.read_text(encoding="utf-8")
        self.assertIn("影印", note,
                      "校记必须含影印核定的记录（原件级验证）")
        self.assertRegex(note, r"L\d{2,4}",
                         "校记必须带底本行号，便于回源定位")


class TestEngineCriteriaHaveOriginalSource(unittest.TestCase):
    """★ 引擎**判据依赖的关键原典**必须能在包内 `orig/` 回查（2026-10-24 体检新增）。

    **为什么要有这个守卫**

    2026-10-24 齐全度体检发现：《河洛理数》三本（18 册 / 1912 页）原先只切了
    「日卦起例卷」一段 ⇒ 引擎最核心的判据 —— **大运只走一轮**、**元堂取法**、
    **天数地数诸格**、**合婚例**、**三刑六列** —— 在包内**没有原典可回查**。

    更严重的一次教训：曾因「包内检索不到」而判定「河洛原典无三刑六害/合婚」，
    实则《河洛理数·卷一》目次明载「詳河洛合婚例」「三刑六列」
    ⇒ **把切片缺口误判成原典缺口**。本守卫把「判据的原典在不在包里」变成硬断言。

    ⚠ 关键词一律用**底本实际写法**（含 OCR 讹字），
    不用推测正字 —— 否则守卫会因为「底本写的是讹字」而误报缺失。
    """

    #: (判据, 必须在包内出现的底本实际写法)
    REQUIRED = [
        ("元堂取法",        ["起元堂", "群元堂"]),
        ("大运（只走一轮）", ["起大運例", "起小運", "起八字法"]),
        ("流年例",          ["起流年例"]),
        ("合婚例",          ["合婚例"]),
        ("三刑六害",        ["三刑六列"]),
        ("卦气歌/候卦定局", ["定御候卦", "使卦定局", "卦氣歌"]),
        ("化工/元气相反",   ["化工元氯", "逢元氰", "元氯相反"]),
        ("十吉/十不吉",     ["青命十吉", "命十不吉"]),
        ("天数地数诸格",    ["孤阴向陽數", "输以弱敢强", "地敗不足",
                          "陽數太過", "醫數太通", "得中數"]),
        ("大易数妙义",      ["大易数妙羲", "其用合其時"]),
        ("互体四体八体",    ["互體四體八體", "六十四卦互體", "內卦出外例"]),
        ("五行约音",        ["五行約音"]),
        ("金银匙歌",        ["金銀匙歌"]),
        ("时刻法",          ["它時刻法"]),
        ("起月卦/起日卦",   ["起月卦之式", "起日卦之式"]),
    ]

    @classmethod
    def setUpClass(cls):
        cls.flat = re.sub(r"\s+", "", "\n".join(
            p.read_text(encoding="utf-8", errors="replace")
            for p in sorted(ORIG.glob("*.txt"))))

    def test_engine_criteria_have_original_source(self):
        missing = []
        for name, kws in self.REQUIRED:
            if not any(re.sub(r"\s+", "", k) in self.flat for k in kws):
                missing.append(f"{name}（{'/'.join(kws)}）")
        self.assertEqual(missing, [],
                         "以下引擎判据在包内 orig/ 找不到原典依据（切片缺口）：\n  "
                         + "\n  ".join(missing))

    def test_heluo_lishu_slices_present(self):
        """《河洛理数》两批切片都要在（关键条文 + 日卦起例卷）。"""
        for name in ("河洛理数_关键条文切片.txt", "河洛理数_日卦起例卷.txt"):
            with self.subTest(slice=name):
                self.assertTrue((ORIG / name).exists(), f"缺切片 {name}")


class TestLineMapConsistency(unittest.TestCase):
    """维度5：行号映射表与切片自洽。"""

    def test_linemap_exists(self):
        self.assertTrue(LINEMAP.exists(),
                        "缺 orig/行号映射.md —— 全书行号与切片行号的换算依据")

    def test_linemap_matches_slices(self):
        txt = LINEMAP.read_text(encoding="utf-8")
        rows = re.findall(r"^\|\s*L(\d+)\s*\|\s*L(\d+)\s*\|", txt, re.M)
        self.assertGreater(len(rows), 500, "映射表条目过少")
        # 映射表里出现的切片行号必须真实存在（按 ### 小节切分，避免串到别的切片）
        bad = []
        for cut_name in ("河洛真数_起例卷之上.txt", "河洛真数_起例卷之中.txt",
                         "河洛真数_起例卷之下.txt"):
            n = len((ORIG / cut_name).read_text(encoding="utf-8").splitlines())
            sec = re.search(rf"### `{re.escape(cut_name)}`(.*?)(?=\n### |\Z)", txt, re.S)
            self.assertIsNotNone(sec, f"映射表缺 {cut_name} 小节")
            for m in re.finditer(r"^\|\s*L(\d+)\s*\|\s*L(\d+)\s*\|", sec.group(1), re.M):
                sl = int(m.group(2))
                if sl > n:
                    bad.append(f"{cut_name} 切片 L{sl} > 实际 {n} 行")
        self.assertEqual(bad, [], "行号映射表与切片不一致：\n  " + "\n  ".join(bad))


if __name__ == "__main__":
    unittest.main()
