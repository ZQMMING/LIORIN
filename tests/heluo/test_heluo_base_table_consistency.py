"""河洛引擎基础表**副本全等守卫**（机器级）

背景
════
河洛引擎里有多份**内容应当完全相同**的基础表副本：

  · 六十四卦表（上卦,下卦）→ 卦全名
  · 八卦 → 五行
  · 错卦（先天方位对宫）
  · 五行生克
  · 三爻二进制 → 三画卦名

这些表此前**没有任何机器守卫**：任何一处改动而另一处不动，
就会静默分叉，产出互相矛盾的判词（例如一处认为「乾为金」、
另一处认为「乾为木」）。本文件把这些副本**钉死**。

设计原则
════════
1. **内容断言**（相等）+ **同一性断言**（`assertIs`）双管齐下：
   - 内容相等只能证明「此刻一致」，证明不了「不会各改各的」；
   - 同一性（`is`）才能证明「它们就是同一份数据，不可能分叉」。
   故凡属引用同一来源的，一律断言 `assertIs`；凡属**手抄副本**
   （确实是两份独立字面量），断言内容相等并指出是哪两份。
2. **失败消息必须点名是哪两个副本不一致**，便于直接定位。
3. **明确排除**语义不同、只名字相似的表：
   - `hexagram_state.HUAGONG_FAN_GUA`（化工相反·四季对宫）≠ 错卦表；
   - `guajie.TWELVE_XIONG_GUA`（今人整理口径，非原典）不参与任何全等断言；
   - `guajie.ZONG_GUA`（64 条综卦对照表）已于 2026-10-22 收敛为
     `hexagram.compute_zong_gua` 的派生表（严格六爻倒转），
     本文件断言二者**逐条相等**（此前是「六爻倒转」手抄表 vs「上下卦易位」
     两套口径，64 卦中 48 卦结果不同）。
4. **不断言 `guajie.compute_huti` 与 `hexagram.compute_hu_gua` 的名字字符串相等**
   （前者返回三画卦名、后者返回六十四卦全名，格式不同）：
   改为断言二者**取爻规则一致**（都取 lines[1:4] 作下互、lines[2:5] 作上互），
   并借助「卦全名 ↔ (上卦,下卦)」这一**唯一可逆**的权威映射，
   把两者的结果还原到同一个 (上卦,下卦) 层面再比较。
"""
from __future__ import annotations

import ast
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo import (guajie, hexagram, hexagram_state, hua_gong,
                                   numbers, timeline_yun, yuanqi_tables)
from tongshu.engines.heluo.relationship import engine as rel_engine
from tongshu.engines.yi import core as yi_core

# ═══════════════════════════════════════════════════════════════
# 公共常量
# ═══════════════════════════════════════════════════════════════

TRIGRAM_NAMES = ("乾", "兑", "离", "震", "巽", "坎", "艮", "坤")
ELEMENTS = ("金", "木", "水", "火", "土")

#: 权威的三爻二进制 → 三画卦名（自下而上，'1'=阳）
CANON_BINARY_TO_TRIGRAM = {
    "111": "乾", "110": "兑", "101": "离", "100": "震",
    "011": "巽", "010": "坎", "001": "艮", "000": "坤",
}


def _diff(a: dict, b: dict, name_a: str, name_b: str) -> str:
    """产出「哪两个副本、差在哪里」的可读描述。"""
    only_a = {k: a[k] for k in sorted(set(a) - set(b))}
    only_b = {k: b[k] for k in sorted(set(b) - set(a))}
    changed = {k: (a[k], b[k]) for k in sorted(set(a) & set(b)) if a[k] != b[k]}
    return ("%s 与 %s 不一致 —— 仅 %s 有：%s；仅 %s 有：%s；"
            "同键不同值（%s 的值, %s 的值）：%s"
            % (name_a, name_b, name_a, only_a, name_b, only_b,
               name_a, name_b, changed))


def _assert_dict_equal(case, a: dict, b: dict, name_a: str, name_b: str) -> None:
    """断言两个字典完全相等，失败消息点名两个副本。"""
    case.assertEqual(
        a, b,
        "%s 与 %s 内容不一致 —— 这两张表应当是同一份数据，"
        "任何一处改动而另一处不动都会静默分叉。%s"
        % (name_a, name_b, _diff(a, b, name_a, name_b)))


def _literal_dicts(mod, names) -> dict:
    """抽出模块里赋值给指定名字的**字面量字典**（含函数内局部字面量）。

    用于抓「藏在函数体内的手抄表」——模块级属性看不到它们，
    但它们同样是副本，改一处就分叉。
    """
    want = set(names)
    tree = ast.parse(io.open(mod.__file__, encoding="utf-8").read())
    found = {}
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        else:
            continue
        for t in targets:
            if isinstance(t, ast.Name) and t.id in want:
                try:
                    lit = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    continue
                if isinstance(lit, dict):
                    found.setdefault(t.id, []).append(lit)
    return found


# ═══════════════════════════════════════════════════════════════
# 1. 六十四卦表
# ═══════════════════════════════════════════════════════════════

class TestSixtyFourHexagramTable(unittest.TestCase):
    """六十四卦表的各副本。"""

    def setUp(self):
        self.num = numbers.SIXTY_FOUR_HEXAGRAMS
        self.yi = yi_core.SIXTY_FOUR_MAP

    def test_numbers_and_yi_core_tables_are_content_identical(self):
        """numbers.SIXTY_FOUR_HEXAGRAMS 与 yi.core.SIXTY_FOUR_MAP 逐条相等。"""
        _assert_dict_equal(
            self, self.num, self.yi,
            "numbers.SIXTY_FOUR_HEXAGRAMS", "yi.core.SIXTY_FOUR_MAP")

    def test_both_tables_have_exactly_64_entries(self):
        self.assertEqual(len(self.num), 64,
                         "numbers.SIXTY_FOUR_HEXAGRAMS 应恰好 64 条，实际 %d"
                         % len(self.num))
        self.assertEqual(len(self.yi), 64,
                         "yi.core.SIXTY_FOUR_MAP 应恰好 64 条，实际 %d"
                         % len(self.yi))

    def test_both_tables_cover_the_same_64_trigram_pairs(self):
        """两表的键集合（64 组上卦/下卦）完全相同，无多无少。"""
        _assert_dict_equal(
            self,
            {k: None for k in self.num},
            {k: None for k in self.yi},
            "numbers.SIXTY_FOUR_HEXAGRAMS 的键集合",
            "yi.core.SIXTY_FOUR_MAP 的键集合")

    def test_hexagram_module_uses_the_yi_core_table_as_single_source(self):
        """hexagram._SIXTY_FOUR_MAP 是从 yi.core 引入的**同一对象**。"""
        self.assertIs(hexagram._SIXTY_FOUR_MAP, self.yi,
                      "hexagram._SIXTY_FOUR_MAP 不再是 yi.core.SIXTY_FOUR_MAP "
                      "本身 —— 有人把它改成了一份拷贝，两边会各改各的")
        self.assertIs(hexagram._NAME_TO_TRIGRAMS, yi_core.NAME_TO_TRIGRAMS,
                      "hexagram._NAME_TO_TRIGRAMS 不再是 yi.core.NAME_TO_TRIGRAMS "
                      "本身 —— 反查表也是副本风险点")

    def test_guajie_compound_gua_inverts_the_authoritative_table(self):
        """guajie.COMPOUND_GUA 每条 (上卦,下卦) 都能在权威表里找到对应全名。

        权威表的键是 (上卦,下卦)、值是卦**全名**；COMPOUND_GUA 的键是
        卦**简称**、值是 (上卦,下卦)。二者互逆，且不得冲突。
        """
        short_of = numbers.HEXAGRAM_SHORT_NAMES
        for short, pair in guajie.COMPOUND_GUA.items():
            self.assertIn(pair, self.num,
                          "guajie.COMPOUND_GUA[%r] = %r 在 "
                          "numbers.SIXTY_FOUR_HEXAGRAMS 里找不到对应条目"
                          % (short, pair))
            full = self.num[pair]
            self.assertEqual(
                short_of[full], short,
                "guajie.COMPOUND_GUA[%r] = %r 与权威表不符："
                "numbers.SIXTY_FOUR_HEXAGRAMS[%r] = %r，其简称为 %r"
                % (short, pair, pair, full, short_of[full]))

    def test_guajie_compound_gua_covers_all_64_hexagrams_without_conflict(self):
        """COMPOUND_GUA 的 64 个简称必须与权威表的全名集合一一对应。"""
        self.assertEqual(len(guajie.COMPOUND_GUA), 64,
                         "guajie.COMPOUND_GUA 应恰好 64 条，实际 %d"
                         % len(guajie.COMPOUND_GUA))
        self.assertEqual(
            set(guajie.COMPOUND_GUA),
            set(numbers.HEXAGRAM_SHORT_NAMES.values()),
            "guajie.COMPOUND_GUA 的简称集合与权威 64 卦的简称集合不一致 —— %s"
            % _diff({k: None for k in guajie.COMPOUND_GUA},
                    {k: None for k in numbers.HEXAGRAM_SHORT_NAMES.values()},
                    "guajie.COMPOUND_GUA 的键",
                    "numbers.HEXAGRAM_SHORT_NAMES 的值集合"))
        # 反向：权威表 64 条经 (上,下)→简称 折叠后，也应恰好落回这 64 个简称
        folded = {numbers.HEXAGRAM_SHORT_NAMES[v]: k
                  for k, v in self.num.items()}
        self.assertEqual(len(folded), 64,
                         "权威表折叠成简称后不足 64 条，说明有卦全名重复")
        _assert_dict_equal(
            self, folded, dict(guajie.COMPOUND_GUA),
            "权威表折叠出的 简称→(上卦,下卦)",
            "guajie.COMPOUND_GUA")

    def test_guajie_pure_gua_agrees_with_authoritative_table(self):
        """PURE_GUA（八纯卦）与权威表一致。"""
        self.assertEqual(len(guajie.PURE_GUA), 8,
                         "guajie.PURE_GUA 应恰好 8 条，实际 %d"
                         % len(guajie.PURE_GUA))
        for short, pair in guajie.PURE_GUA.items():
            self.assertEqual(pair, (short, short),
                             "guajie.PURE_GUA[%r] 应为 (%r, %r)，实际 %r"
                             % (short, short, short, pair))
            self.assertIn(pair, self.num,
                          "guajie.PURE_GUA[%r] = %r 在权威表里找不到"
                          % (short, pair))
            self.assertIn(short, guajie.COMPOUND_GUA,
                          "guajie.PURE_GUA[%r] 未被并入 guajie.COMPOUND_GUA" % short)

    def test_hexagram_short_names_are_a_bijection(self):
        """64 个全名 → 64 个简称必须两两不同（否则简称表塌了）。"""
        shorts = list(numbers.HEXAGRAM_SHORT_NAMES.values())
        self.assertEqual(len(shorts), 64,
                         "权威 64 卦应派生 64 个简称，实际 %d" % len(shorts))
        self.assertEqual(len(set(shorts)), 64,
                         "权威 64 卦派生的简称出现重复：共 %d 个，"
                         "去重后仅 %d 个" % (len(shorts), len(set(shorts))))


# ═══════════════════════════════════════════════════════════════
# 2. 八卦 → 五行
# ═══════════════════════════════════════════════════════════════

class TestTrigramElementTable(unittest.TestCase):
    """TRIGRAM_ELEMENT 的各副本。"""

    COPIES = (
        ("numbers.TRIGRAM_ELEMENT", lambda: numbers.TRIGRAM_ELEMENT),
        ("hexagram.TRIGRAM_ELEMENT", lambda: hexagram.TRIGRAM_ELEMENT),
        ("guajie.TRIGRAM_ELEMENT", lambda: guajie.TRIGRAM_ELEMENT),
        ("hua_gong.TRIGRAM_ELEMENT", lambda: hua_gong.TRIGRAM_ELEMENT),
        ("yi.core.TRIGRAM_ELEMENT", lambda: yi_core.TRIGRAM_ELEMENT),
    )

    def test_all_copies_are_identical(self):
        base_name, base_get = self.COPIES[0]
        base = base_get()
        for name, get in self.COPIES[1:]:
            _assert_dict_equal(self, base, get(), base_name, name)

    def test_exactly_8_trigrams_each_with_a_legal_element(self):
        for name, get in self.COPIES:
            table = get()
            self.assertEqual(len(table), 8,
                             "%s 应恰好 8 个三画卦，实际 %d" % (name, len(table)))
            self.assertEqual(set(table), set(TRIGRAM_NAMES),
                             "%s 的键不是八卦全名：%s" % (name, sorted(table)))
            for tri, elem in table.items():
                self.assertIn(elem, ELEMENTS,
                              "%s[%r] = %r 不是合法五行（%s）"
                              % (name, tri, elem, "/".join(ELEMENTS)))


# ═══════════════════════════════════════════════════════════════
# 3. 错卦（先天方位对宫）
# ═══════════════════════════════════════════════════════════════

class TestQianxiDukongTable(unittest.TestCase):
    """错卦表的各副本。"""

    def test_qianxi_dukong_equals_yi_core_cuo_gua_map(self):
        """hexagram_state.QIANXI_DUKONG 与 yi.core.CUO_GUA_MAP 内容相等。"""
        _assert_dict_equal(
            self, hexagram_state.QIANXI_DUKONG, yi_core.CUO_GUA_MAP,
            "hexagram_state.QIANXI_DUKONG", "yi.core.CUO_GUA_MAP")

    def test_yuanqi_tables_dui_gua_is_the_same_object(self):
        """yuanqi_tables.DUI_GUA 必须**就是** QIANXI_DUKONG 本身。"""
        self.assertIs(yuanqi_tables.DUI_GUA, hexagram_state.QIANXI_DUKONG,
                      "yuanqi_tables.DUI_GUA 不再是 "
                      "hexagram_state.QIANXI_DUKONG 本身 —— 错卦表又分叉了")

    def test_guajie_hua_gong_hexagram_all_share_the_same_object(self):
        """引用同一来源的模块必须 `is` 同一对象。"""
        src = hexagram_state.QIANXI_DUKONG
        self.assertIs(guajie.QIANXI_DUKONG, src,
                      "guajie.QIANXI_DUKONG 不再是 hexagram_state."
                      "QIANXI_DUKONG 本身")
        self.assertIs(hua_gong.QIANXI_DUKONG, src,
                      "hua_gong.QIANXI_DUKONG 不再是 hexagram_state."
                      "QIANXI_DUKONG 本身")
        self.assertIs(hexagram._QIANXI_DUKONG, src,
                      "hexagram._QIANXI_DUKONG 不再是 hexagram_state."
                      "QIANXI_DUKONG 本身")

    def test_dukong_is_an_involution_over_the_eight_trigrams(self):
        """错卦表自洽：对宫两次回到自身，且恰收八卦。"""
        table = hexagram_state.QIANXI_DUKONG
        self.assertEqual(len(table), 8,
                         "QIANXI_DUKONG 应恰好 8 条，实际 %d" % len(table))
        self.assertEqual(set(table), set(TRIGRAM_NAMES),
                         "QIANXI_DUKONG 的键不是八卦全名：%s" % sorted(table))
        for tri, fan in table.items():
            self.assertIn(fan, TRIGRAM_NAMES,
                          "QIANXI_DUKONG[%r] = %r 不是三画卦名" % (tri, fan))
            self.assertEqual(table[fan], tri,
                             "QIANXI_DUKONG 非对合：%r→%r→%r"
                             % (tri, fan, table[fan]))
            self.assertNotEqual(tri, fan,
                                "QIANXI_DUKONG[%r] 指向自身，不可能是对宫" % tri)

    def test_huagong_fan_gua_is_not_confused_with_dukong(self):
        """化工相反表（四季对宫）**不得**与错卦表混为一谈。"""
        fan = hua_gong.HUAGONG_FAN_GUA
        self.assertEqual(len(fan), 4,
                         "HUAGONG_FAN_GUA 应恰好 4 项（四季对宫），实际 %d"
                         % len(fan))
        self.assertNotEqual(fan, hexagram_state.QIANXI_DUKONG,
                            "HUAGONG_FAN_GUA 与 QIANXI_DUKONG 变成了同一张表 —— "
                            "两者语义不同（四季对宫 vs 先天对宫），混用即静默判错")
        self.assertNotIn("乾", fan,
                         "化工相反表不收乾/坤/艮/巽，混入即为错")
        self.assertIn("乾", hexagram_state.QIANXI_DUKONG,
                      "错卦表必须收乾（乾对坤），缺失即为错")
        self.assertEqual(hexagram_state.QIANXI_DUKONG["乾"], "坤",
                         "错卦表里乾的对宫必须是坤")


# ═══════════════════════════════════════════════════════════════
# 4. 五行生克
# ═══════════════════════════════════════════════════════════════

class TestWuxingShengKeTables(unittest.TestCase):
    """五行生克表的各副本。"""

    def test_sheng_map_copies_are_identical(self):
        copies = (
            ("hexagram.SHENG_MAP", hexagram.SHENG_MAP),
            ("hexagram_state.ELEMENT_GENERATES",
             hexagram_state.ELEMENT_GENERATES),
            ("guajie.ELEMENT_GENERATES", guajie.ELEMENT_GENERATES),
            ("relationship.engine.ELEMENT_GEN", rel_engine.ELEMENT_GEN),
        )
        base_name, base = copies[0]
        for name, table in copies[1:]:
            _assert_dict_equal(self, base, table, base_name, name)

    def test_ke_map_copies_are_identical(self):
        copies = (
            ("hexagram.KE_MAP", hexagram.KE_MAP),
            ("hexagram_state.ELEMENT_OVERCOMES",
             hexagram_state.ELEMENT_OVERCOMES),
            ("relationship.engine.ELEMENT_KE", rel_engine.ELEMENT_KE),
        )
        base_name, base = copies[0]
        for name, table in copies[1:]:
            _assert_dict_equal(self, base, table, base_name, name)

    def test_hua_gong_uses_the_hexagram_state_tables_as_single_source(self):
        self.assertIs(hua_gong._WU_SHENG, hexagram_state.ELEMENT_GENERATES,
                      "hua_gong._WU_SHENG 不再是 hexagram_state."
                      "ELEMENT_GENERATES 本身")
        self.assertIs(hua_gong._WU_KE, hexagram_state.ELEMENT_OVERCOMES,
                      "hua_gong._WU_KE 不再是 hexagram_state."
                      "ELEMENT_OVERCOMES 本身")

    def test_sheng_and_ke_are_each_self_consistent(self):
        """生克映射自身自洽：五行生五行、五行克五行、不自指。"""
        sheng = hexagram.SHENG_MAP
        ke = hexagram.KE_MAP
        for name, table in (("SHENG_MAP", sheng), ("KE_MAP", ke)):
            self.assertEqual(set(table), set(ELEMENTS),
                             "hexagram.%s 的键不是五行全集合：%s"
                             % (name, sorted(table)))
            for elem, target in table.items():
                self.assertIn(target, ELEMENTS,
                              "hexagram.%s[%r] = %r 不是合法五行"
                              % (name, elem, target))
                self.assertNotEqual(elem, target,
                                    "hexagram.%s[%r] 指向自身，五行不自生不自克"
                                    % (name, elem))

    def test_sheng_is_a_cycle_and_ke_is_two_steps_of_sheng(self):
        """生为五元环；克 = 隔一位相克（生两次）。"""
        sheng = hexagram.SHENG_MAP
        ke = hexagram.KE_MAP
        for elem in ELEMENTS:
            self.assertEqual(sheng[sheng[elem]], ke[elem],
                             "五行关系不自洽：%r 生 %r 生 %r，但 %r 克 %r"
                             % (elem, sheng[elem], sheng[sheng[elem]],
                                elem, ke[elem]))
        # 生为双射（每个五行恰被一个五行生）
        self.assertEqual(len(set(sheng.values())), 5,
                         "SHENG_MAP 不是双射：%r" % sheng)

    def test_yi_core_local_sheng_ke_behave_identically(self):
        """yi.core 的生克是**函数内局部字面量**，按行为对拍。

        yi/core.py 不导出 SHENG/KE 常量，SHENG/KE 写在
        compute_ti_yong_relation 函数体内（故只能按行为验证），
        但它同样是一份副本，改一处即分叉。
        """
        for upper in TRIGRAM_NAMES:
            for lower in TRIGRAM_NAMES:
                self.assertEqual(
                    yi_core.compute_ti_yong_relation(upper, lower),
                    hexagram.compute_ti_yong(upper, lower)["relation"],
                    "yi.core.compute_ti_yong_relation(%r, %r) 与 "
                    "hexagram.compute_ti_yong(%r, %r) 的体用生克判定不一致 —— "
                    "两处的五行生克表已分叉"
                    % (upper, lower, upper, lower))


# ═══════════════════════════════════════════════════════════════
# 5. 互卦（取爻规则）
# ═══════════════════════════════════════════════════════════════

class TestMutualHexagram(unittest.TestCase):
    """互体取爻规则：下互 = lines[1:4]，上互 = lines[2:5]。"""

    def _cases(self):
        """遍历 64 卦，返回 (卦全名, 六爻) 列表。"""
        out = []
        for (upper, lower), full in numbers.SIXTY_FOUR_HEXAGRAMS.items():
            lines = (list(numbers.TRIGRAM_LINES[lower])
                     + list(numbers.TRIGRAM_LINES[upper]))
            out.append((full, lines))
        return out

    def _expected(self, lines):
        """按原典取法独立算出 (上互, 下互) 三画卦名。"""
        def tri(chunk):
            return CANON_BINARY_TO_TRIGRAM[
                "".join("1" if x == 1 else "0" for x in chunk)]
        return tri(lines[2:5]), tri(lines[1:4])

    def test_compute_hu_gua_uses_lines_1_4_and_2_5(self):
        """hexagram.compute_hu_gua 的取爻必须是下互 lines[1:4]、上互 lines[2:5]。"""
        for full, lines in self._cases():
            hu_up, hu_lo = self._expected(lines)
            expected = numbers.SIXTY_FOUR_HEXAGRAMS.get((hu_up, hu_lo))
            self.assertEqual(
                hexagram.compute_hu_gua(lines), expected,
                "hexagram.compute_hu_gua 对 %r 的互体取爻不符："
                "按 lines[1:4]=下互、lines[2:5]=上互 应得 %r，实际 %r"
                % (full, expected, hexagram.compute_hu_gua(lines)))

    def test_compute_huti_uses_lines_1_4_and_2_5(self):
        """guajie.compute_huti 的取爻必须与权威实现一致。"""
        for full, lines in self._cases():
            hu_up, hu_lo = self._expected(lines)
            self.assertEqual(
                guajie.compute_huti(lines), (hu_up, hu_lo),
                "guajie.compute_huti 对 %r 的互体取爻不符："
                "按 lines[1:4]=下互、lines[2:5]=上互 应得 %r，实际 %r"
                % (full, (hu_up, hu_lo), guajie.compute_huti(lines)))

    def test_hu_gua_and_huti_agree_on_the_underlying_trigram_pair(self):
        """两者结果还原到 (上卦,下卦) 层面后必须一致。

        这里**不比较名字字符串**（compute_hu_gua 返回六十四卦全名、
        compute_huti 返回三画卦名，格式不同），而是借助权威表
        「卦全名 ↔ (上卦,下卦)」这一唯一可逆映射，把 compute_hu_gua
        的结果还原到三画卦层面再比。
        """
        reverse = {v: k for k, v in numbers.SIXTY_FOUR_HEXAGRAMS.items()}
        # 先证明这个映射**无损可逆**（64 个全名两两不同、恰好对应 64 组
        # 上下卦），否则「还原到三画卦层面再比」这一步本身就不可靠。
        self.assertEqual(len(reverse), 64,
                         "权威 64 卦表出现重复卦名（%d 个），"
                         "「卦全名 ↔ (上卦,下卦)」不再可逆"
                         % len(reverse))
        self.assertEqual(
            len(set(reverse.values())), 64,
            "权威 64 卦表出现重复的 (上卦,下卦) 组合，映射不可逆")
        for full, lines in self._cases():
            hu_name = hexagram.compute_hu_gua(lines)
            self.assertIn(hu_name, reverse,
                          "hexagram.compute_hu_gua 对 %r 返回的 %r 不在权威 64 卦表内"
                          % (full, hu_name))
            hu_up, hu_lo = reverse[hu_name]
            self.assertEqual(
                guajie.compute_huti(lines), (hu_up, hu_lo),
                "互体取爻分叉：hexagram.compute_hu_gua(%r 的六爻) 还原得 %r，"
                "guajie.compute_huti 得 %r"
                % (full, (hu_up, hu_lo), guajie.compute_huti(lines)))

    def test_hua_gong_mutual_trigram_agrees_with_guajie(self):
        """hua_gong.compute_mutual_trigram 是互体的第二份实现，须与 guajie 一致。"""
        for (upper, lower), full in numbers.SIXTY_FOUR_HEXAGRAMS.items():
            lines = (list(numbers.TRIGRAM_LINES[lower])
                     + list(numbers.TRIGRAM_LINES[upper]))
            self.assertEqual(
                hua_gong.compute_mutual_trigram(upper, lower),
                guajie.compute_huti(lines),
                "hua_gong.compute_mutual_trigram(%r, %r) 与 "
                "guajie.compute_huti 对 %r 的互体取爻不一致"
                % (upper, lower, full))


# ═══════════════════════════════════════════════════════════════
# 6. 三爻二进制 → 三画卦名
# ═══════════════════════════════════════════════════════════════

class TestBinaryToTrigramTables(unittest.TestCase):
    """三画卦名的二进制映射副本。"""

    def test_module_level_copies_are_identical(self):
        copies = (
            ("hexagram._LINES_TO_TRIGRAM", hexagram._LINES_TO_TRIGRAM),
            ("guajie._TRI_NAME", guajie._TRI_NAME),
            ("numbers.TRIGRAM_BINARY（反向）",
             {v: k for k, v in numbers.TRIGRAM_BINARY.items()}),
        )
        base_name, base = copies[0]
        for name, table in copies[1:]:
            _assert_dict_equal(self, base, table, base_name, name)

    def test_function_local_copies_are_identical(self):
        """函数体内的局部字面量副本（模块级属性看不到它们）。"""
        for mod, name in ((timeline_yun, "rev"), (guajie, "rev")):
            found = _literal_dicts(mod, [name]).get(name, [])
            self.assertTrue(found,
                            "%s 里找不到名为 %r 的字面量字典 —— "
                            "该局部表被改名或删除，本守卫已失效" % (mod.__name__, name))
            for i, table in enumerate(found):
                _assert_dict_equal(
                    self, CANON_BINARY_TO_TRIGRAM, table,
                    "权威 三爻二进制→三画卦名",
                    "%s 内局部 %s[%d]" % (mod.__name__, name, i))

    def test_trigram_binary_is_consistent_with_trigram_lines(self):
        """numbers.TRIGRAM_BINARY 与 TRIGRAM_LINES 必须彼此吻合。"""
        for tri, lines in numbers.TRIGRAM_LINES.items():
            bits = "".join("1" if x == 1 else "0" for x in lines)
            self.assertEqual(
                numbers.TRIGRAM_BINARY.get(tri), bits,
                "numbers.TRIGRAM_BINARY[%r] 与 TRIGRAM_LINES[%r] 不符：%r vs %r"
                % (tri, tri, numbers.TRIGRAM_BINARY.get(tri), bits))


# ═══════════════════════════════════════════════════════════════
# 7. 综卦表自身自洽（不与 compute_zong_gua 互证）
# ═══════════════════════════════════════════════════════════════

class TestZongGuaSelfConsistency(unittest.TestCase):
    """guajie.ZONG_GUA 的自身自洽，且与 hexagram.compute_zong_gua **一致**。

    2026-10-22：二者此前是**两套不同口径**（前者「六爻倒转」手抄表、
    后者「上下卦易位」），对 64 卦中的 48 卦给出不同结果。现已统一为
    严格六爻倒转（原典《六十四卦反对图》计数：上经正卦六、下经正卦二），
    本类改为断言二者**逐条相等** —— 见
    ``tests/heluo/test_heluo_zong_gua_original.py`` 的原典计数守卫。
    """

    def test_zong_gua_is_an_involution_covering_all_64(self):
        table = guajie.ZONG_GUA
        self.assertEqual(len(table), 64,
                         "guajie.ZONG_GUA 应恰好 64 条，实际 %d" % len(table))
        self.assertEqual(
            set(table), set(numbers.HEXAGRAM_SHORT_NAMES.values()),
            "guajie.ZONG_GUA 的键不是权威 64 卦的简称集合")
        for short, zong in table.items():
            self.assertIn(zong, table,
                          "guajie.ZONG_GUA[%r] = %r 不在表内" % (short, zong))
            self.assertEqual(table[zong], short,
                             "guajie.ZONG_GUA 非对合：%r→%r→%r"
                             % (short, zong, table[zong]))

    def test_zong_gua_equals_authoritative_implementation(self):
        """综卦表必须与权威实现逐条相等（曾有第二份手抄副本，已收敛）。"""
        mism = []
        for (up, lo), full in numbers.SIXTY_FOUR_HEXAGRAMS.items():
            short = numbers.short_hexagram_name(full)
            want = numbers.short_hexagram_name(hexagram.compute_zong_gua(up, lo))
            got = guajie.ZONG_GUA.get(short)
            if got != want:
                mism.append((short, got, want))
        self.assertEqual(mism, [],
                         "综卦表与权威实现不一致：%s" % (mism[:5],))


if __name__ == "__main__":
    unittest.main()
