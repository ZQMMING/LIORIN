"""Z80-H/W1: 经典细则层——古籍原文资产接线（build_classical_detail）。

单一入口 `build_classical_detail(chart)`，由 answer_layer 的
`_build_classical_detail_safe` 调用，结果落在 build_answer 顶层键
`classical_detail`（独立通道，不并入 12 宫位维 / 体用层）。

九张母表 → 九个出口：
  palace_jue        ← pattern_rules.PALACE_FORTUNE_RULE(12) / PALACE_DEPRIVATION_RULE(9)
  classical_patterns← pattern_rules.WEALTH/NOBILITY/POVERTY/MISC_PATTERN(49)
  nvming            ← nvming_rules.NVMING_RULES(9) + NVMING_ZHUAN(6)
  child_limit       ← child_limit_rules.CHILD_LIMIT_RULES(5)
  limit_advanced    ← limit_advanced_rules.LIMIT_ADVANCED_RULES(7)
  temporal_rules    ← temporal_rules.TAISUI_XIAOXIAN_RULES(25) + DOUJUN_RULES(1) + LIUYAO_RULES(3)
  aux_verdicts      ← aux_star_verdicts.AUX/SHA/MISC_STAR_VERDICTS(16)
  temporal_facts    ← temporal_facts（太岁/小限/斗君/流禄流羊流陀/虚岁）
  summary           ← 计数

断语纪律（ANTI-FAKE-HIT）：
  1. 原文（verbatim）原样带出，不改写、不概括；
  2. 只有「母表条件句子 → 机器可判定谓词」一一映射的条目才 `evaluated=True`；
     谓词不足的条目 `evaluated=False`，附 `reason`（宁可不出，不做臆断命中）；
  3. 命中的条目必须给出 `evidence`（逐条谓词的实测值），可回溯；
  4. `_PATTERN_SPEC` 是母表 `formation_conditions` 的机器投影，与母表 1:1；
     tests/test_ziwei_classical_detail.py 校验「母表每条都有投影 / 投影无孤儿」，
     母表增删条目而本表未同步时测试直接失败。

已知未实现判据（登记于 summary.data_issues，不做假命中）：
  空亡（旬空）、日月反背、运限类主观条件（MISC 八条）、天伤天使安法。
"""
from __future__ import annotations

import logging

from .aux_star_verdicts import AUX_STAR_VERDICTS, MISC_STAR_VERDICTS, SHA_STAR_VERDICTS
from .child_limit_rules import CHILD_LIMIT_RULES
from .limit_advanced_rules import LIMIT_ADVANCED_RULES
from .nvming_rules import NVMING_RULES, NVMING_ZHUAN
from .palace_relationship import three_square_four
from .pattern_rules import (
    ALL_PATTERNS,
    MISC_PATTERN,
    NOBILITY_PATTERN,
    PALACE_DEPRIVATION_RULE,
    PALACE_FORTUNE_RULE,
    POVERTY_PATTERN,
    WEALTH_PATTERN,
)
from .temporal_facts import BRANCH_ORDER, flow_star_positions, small_limit_branch, taisui_branch
from .temporal_rules import DOUJUN_RULES, LIUYAO_RULES, TAISUI_XIAOXIAN_RULES

logger = logging.getLogger(__name__)

_DIGITS = {"二": 2, "三": 3, "四": 4, "五": 5, "六": 6}
_JIXIANG = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存", "天马"}
_GAN = "甲乙丙丁戊己庚辛壬癸"


def _empty_structure() -> dict:
    return {
        "palace_jue": [],
        "classical_patterns": [],
        "nvming": [],
        "child_limit": [],
        "limit_advanced": [],
        "temporal_rules": [],
        "aux_verdicts": [],
        "temporal_facts": {},
        "summary": {
            "palace_jue": 0,
            "classical_patterns": 0,
            "nvming": 0,
            "child_limit": 0,
            "limit_advanced": 0,
            "temporal_rules": 0,
            "aux_verdicts": 0,
        },
    }


# ============================================================
# 盘面视图——把 ZiweiChart 归一成「宫名 → 地支 / 星曜集」
# ============================================================
class _View:
    """只读盘面视图。星曜一律用中文名（母表口径），不转拼音键。"""

    def __init__(self, chart):
        palaces = getattr(chart, "palaces", None) or {}
        self.chart = chart
        self.palaces = {n: dict(d or {}) for n, d in palaces.items()}
        self.branch = {n: str(d.get("branch", "") or "") for n, d in self.palaces.items()}
        self.by_branch = {b: n for n, b in self.branch.items() if b}
        self.stars = {}
        self.major = {}
        self.bright = {}
        self.hua = {}  # 星 → 生年四化集（禄/权/科/忌）
        for name, data in self.palaces.items():
            star_set = set()
            for key in ("major", "minor", "adjective"):
                star_set |= {s for s in (data.get(key) or []) if s}
            self.stars[name] = star_set
            self.major[name] = [s for s in (data.get("major") or [])]
            bright = dict(data.get("brightness") or {})
            for sd in data.get("starDetail") or []:
                star, b = sd.get("name"), sd.get("brightness")
                if star and b and star not in bright:
                    bright[star] = b
                mu = sd.get("mutagen")
                if star and mu:
                    self.hua.setdefault(star, set()).add(str(mu))
            self.bright[name] = bright
        self.soul_branch = str(getattr(chart, "soul_earthly_branch", "") or "")
        self.soul_palace = self.by_branch.get(self.soul_branch, "")
        if not self.soul_palace and "命宫" in self.palaces:
            self.soul_palace = "命宫"
            self.soul_branch = self.branch.get("命宫", self.soul_branch)
        self.body_palace = ""
        for name, data in self.palaces.items():
            if data.get("isBody"):
                self.body_palace = name
                break
        self.gender = str(getattr(chart, "gender", "") or "").lower()
        self.birth_year = int(getattr(chart, "birth_year", 0) or 0)
        self.flow_year = int(getattr(chart, "flow_year", 0) or 0) or self.birth_year
        self.ju = _ju_number(str(getattr(chart, "fiveElementsClass", "") or ""))

    # ---------- 基础查询 ----------
    def palace_name(self, key: str) -> str:
        if key == "命宫":
            return self.soul_palace
        if key == "身宫":
            return self.body_palace
        return key if key in self.palaces else ""

    def branch_of(self, key: str) -> str:
        name = self.palace_name(key)
        return self.branch.get(name, "") if name else ""

    def stars_in(self, key: str) -> set:
        name = self.palace_name(key)
        return self.stars.get(name, set()) if name else set()

    def sanfang_names(self, key: str) -> list:
        branch = self.branch_of(key)
        if not branch:
            return []
        tsf = three_square_four(branch)
        out = []
        for b in (tsf["self"], tsf["opposite"], tsf["trine_1"], tsf["trine_2"]):
            n = self.by_branch.get(b)
            if n and n not in out:
                out.append(n)
        return out

    def sanfang_stars(self, key: str) -> set:
        out = set()
        for n in self.sanfang_names(key):
            out |= self.stars.get(n, set())
        return out

    def adjacent(self, key: str) -> tuple[str, str]:
        branch = self.branch_of(key)
        if not branch:
            return "", ""
        i = BRANCH_ORDER.index(branch)
        return (self.by_branch.get(BRANCH_ORDER[(i - 1) % 12], ""),
                self.by_branch.get(BRANCH_ORDER[(i + 1) % 12], ""))

    def is_female(self) -> bool:
        return self.gender in ("female", "f", "女")

    def nominal_age(self) -> int:
        if not self.birth_year:
            return 0
        return max(1, self.flow_year - self.birth_year + 1)


def _ju_number(cls: str) -> int:
    """五行局 → 起限岁数（水二/木三/金四/土五/火六）。"""
    for ch, num in _DIGITS.items():
        if ch in cls:
            return num
    for i, ch in enumerate("二三四五六", start=2):
        pass
    m = "".join(c for c in cls if c.isdigit())
    return int(m) if m else 0


# ============================================================
# 谓词（母表条件句子 → 机器可判定原子）
# ============================================================
def A_loc(palace: str, branches: str) -> dict:
    return {"kind": "loc", "palace": palace, "branches": branches}


def A_star(palace: str, stars, mode: str = "all") -> dict:
    return {"kind": "star", "palace": palace, "stars": list(stars), "mode": mode}


def A_sanfang(palace: str, stars, mode: str = "all") -> dict:
    return {"kind": "sanfang", "palace": palace, "stars": list(stars), "mode": mode}


def A_jia(palace: str, stars) -> dict:
    return {"kind": "jia", "palace": palace, "stars": list(stars)}


def A_sihua(palace: str, hua, scope: str = "sanfang") -> dict:
    return {"kind": "sihua", "palace": palace, "hua": list(hua), "scope": scope}


def A_bright(palace: str, stars, allow) -> dict:
    return {"kind": "brightness", "palace": palace, "stars": list(stars), "allow": list(allow)}


def A_body(palace: str) -> dict:
    return {"kind": "body", "palace": palace}


def A_at(star: str, branch: str) -> dict:
    return {"kind": "star_at", "star": star, "branch": branch}


def _has(star_set: set, stars, mode: str) -> bool:
    if mode == "single":
        return len(star_set) == 1 and next(iter(star_set)) in set(stars)
    if mode == "any":
        return any(s in star_set for s in stars)
    return all(s in star_set for s in stars)


_UNSUPPORTED_KINDS = {
    "kongwang": "空亡（旬中空亡）安法未实现",
    "fanbei": "日月反背判据（昼生夜生+星曜+地支）未定",
    "yunxian": "运限叠加/主观项，本命单盘不可判定",
}


def _expand_sihua(stars, palace_name: str, view: _View) -> list:
    """`__sihua__禄` 哨兵 → 该宫内实际带此四化的星名（NOB-22 用）。"""
    out = []
    for star in stars:
        if star.startswith("__sihua__"):
            hua = star[len("__sihua__"):]
            out.extend(s for s in view.stars.get(palace_name, set())
                       if hua in view.hua.get(s, set()))
        else:
            out.append(star)
    return out


def _eval_atom(atom: dict, view: _View) -> tuple[bool, str]:
    kind = atom["kind"]
    if kind == "loc":
        got = view.branch_of(atom["palace"])
        ok = bool(got) and got in set(atom["branches"])
        return ok, f"{atom['palace']}地支={got or '?'}（需在 {atom['branches']}）"
    if kind == "star":
        got = view.stars_in(atom["palace"])
        ok = _has(got, atom["stars"], atom["mode"])
        shown = "、".join(sorted(got)) or "空"
        return ok, f"{atom['palace']}星曜[{shown}]含{atom['stars']}（{atom['mode']}）"
    if kind == "sanfang":
        got = view.sanfang_stars(atom["palace"])
        ok = _has(got, atom["stars"], atom["mode"])
        return ok, f"{atom['palace']}三方四正含{atom['stars']}（{atom['mode']}）"
    if kind == "jia":
        left, right = view.adjacent(atom["palace"])
        a, b = atom["stars"][0], atom["stars"][1]
        fwd = a in view.stars.get(left, set()) and b in view.stars.get(right, set())
        rev = b in view.stars.get(left, set()) and a in view.stars.get(right, set())
        ok = bool(left and right) and (fwd or rev)
        return ok, f"{atom['palace']}两邻宫[{left or '?'}]/[{right or '?'}]夹{a}{b}"
    if kind == "sihua":
        names = view.sanfang_names(atom["palace"]) if atom["scope"] == "sanfang" \
            else [view.palace_name(atom["palace"])]
        names = [n for n in names if n]
        hit = []
        for hua in atom["hua"]:
            if any(hua in view.hua.get(s, set()) for n in names for s in view.stars.get(n, set())):
                hit.append(hua)
        ok = len(hit) == len(atom["hua"])
        return ok, f"{atom['palace']}{atom['scope']}内见生年化{hit}"
    if kind == "brightness":
        name = view.palace_name(atom["palace"])
        rates = view.bright.get(name, {})
        stars = _expand_sihua(atom["stars"], name, view)
        if not name or not stars:
            return False, f"{atom['palace']}无对应星曜（需 {atom['allow']}）"
        ok = all(rates.get(s) in set(atom["allow"]) for s in stars)
        got = {s: rates.get(s, "?") for s in stars}
        return ok, f"{atom['palace']}亮度{got}（需 {atom['allow']}）"
    if kind == "empty":
        name = view.palace_name(atom["palace"])
        ok = bool(name) and not view.major.get(name)
        return ok, f"{atom['palace']}主星={'无' if ok else '有'}"
    if kind == "body":
        ok = view.body_palace == atom["palace"]
        return ok, f"身宫={view.body_palace or '?'}（需 {atom['palace']}）"
    if kind == "star_at":
        name = view.by_branch.get(atom["branch"], "")
        ok = bool(name) and atom["star"] in view.stars.get(name, set())
        return ok, f"{atom['branch']}宫={name or '?'}含{atom['star']}"
    if kind == "jixiang":
        got = view.sanfang_stars(atom["palace"]) & _JIXIANG
        ok = bool(got)
        return ok, f"{atom['palace']}三方四正吉曜={sorted(got)}"
    if kind in _UNSUPPORTED_KINDS:
        raise _Unsupported(_UNSUPPORTED_KINDS[kind])
    raise _Unsupported(f"未实现谓词: {kind}")


class _Unsupported(Exception):
    """母表条件含本层未实现的判据（空亡/反背/运限主观项）。"""


def _eval_group(atoms, view: _View) -> tuple[bool, list[str]]:
    evidence = []
    ok = True
    for atom in atoms:
        try:
            a_ok, text = _eval_atom(atom, view)
        except _Unsupported as exc:
            raise _Unsupported(str(exc)) from None
        evidence.append(("✓ " if a_ok else "✗ ") + text)
        ok = ok and a_ok
    return ok, evidence


# ============================================================
# 49 条格局的机器投影（与 pattern_rules.formation_conditions 1:1）
# ============================================================
def _sihua_stars(*hua: str) -> list:
    """生年四化 → 落在命宫的那些星（供 NOB-22「化权化禄守命庙旺」用）。"""
    # 母表只写「化权/化禄」，具体星名由十干四化表决定；用哨兵名让
    # _eval_atom 的 brightness 分支按 hua 反查命宫内实际带该四化的星。
    return ["__sihua__" + h for h in hua]


_PATTERN_SPEC: dict[str, dict] = {}


def _spec(pid: str, all_atoms=None, any_groups=None):
    _PATTERN_SPEC[pid] = {"all": list(all_atoms or []), "any": [list(g) for g in (any_groups or [])]}


_spec("WEALTH-01", any_groups=[
    [A_star("命宫", ["武曲", "天相"])],
    [A_star("田宅宫", ["武曲", "天相"])],
])
_spec("WEALTH-02", any_groups=[
    [A_star("命宫", ["武曲"]), A_jia("命宫", ["太阳", "太阴"])],
    [A_star("财帛宫", ["武曲"]), A_jia("财帛宫", ["太阳", "太阴"])],
])
_spec("WEALTH-03", all_atoms=[
    A_star("命宫", ["天马"]), A_jia("命宫", ["武曲", "禄存"]),
])
_spec("WEALTH-04", all_atoms=[
    A_body("田宅宫"), A_sanfang("田宅宫", ["天梁", "天相"]),
])
_spec("WEALTH-05", all_atoms=[A_star("田宅宫", ["太阳", "太阴"])])
_spec("WEALTH-06", all_atoms=[A_loc("命宫", "午"), A_star("命宫", ["太阳"], "single")])

_spec("NOB-01", all_atoms=[A_jia("命宫", ["太阳", "太阴"])])
_spec("NOB-02", any_groups=[
    [A_loc("命宫", "卯"), A_star("命宫", ["太阳"])],
    [A_star("官禄宫", ["太阳"])],
])
_spec("NOB-03", all_atoms=[A_loc("命宫", "亥"), A_star("命宫", ["太阴"])])
_spec("NOB-04", all_atoms=[A_loc("田宅宫", "子"), A_star("田宅宫", ["太阴"])])
_spec("NOB-05", all_atoms=[A_star("命宫", ["紫微"])], any_groups=[
    [A_jia("命宫", ["左辅", "右弼"])],
    [A_sanfang("命宫", ["左辅", "右弼"])],
])
_spec("NOB-06", all_atoms=[A_star("命宫", ["紫微", "左辅", "右弼"])])
_spec("NOB-07", any_groups=[
    [A_star("命宫", ["禄存"]), A_jia("命宫", ["天梁", "天相"])],
    [A_star("财帛宫", ["禄存"]), A_jia("财帛宫", ["天梁", "天相"])],
])
_spec("NOB-08", all_atoms=[A_star("命宫", ["天马", "禄存", "天相"])])
_spec("NOB-09", any_groups=[
    [A_star("命宫", ["天魁", "天钺"])],
    [A_sanfang("命宫", ["天魁", "天钺"])],
])
_spec("NOB-10", all_atoms=[A_loc("命宫", "午"), A_star("命宫", ["天马", "擎羊"])])
# 母表 formation_conditions 作「寅申子辰」，原典 verbatim 作「寅申子午」；
# 七杀不入辰，故按原典取「寅申子午」，差异登记于 data_issues（NOB-11）。
_spec("NOB-11", all_atoms=[A_loc("命宫", "寅申子午"), A_star("命宫", ["七杀"])])
_spec("NOB-12", all_atoms=[
    A_at("太阳", "午"), A_at("太阴", "子"), A_sanfang("命宫", ["太阳", "太阴"]),
])
_spec("NOB-13", all_atoms=[A_loc("命宫", "亥卯未"), A_star("命宫", ["太阴"])])
_spec("NOB-14", all_atoms=[A_star("命宫", ["太阳", "太阴"])])
_spec("NOB-15", any_groups=[
    [A_star("命宫", ["天刑", "廉贞"])],
    [A_star("身宫", ["天刑", "廉贞"])],
])
_spec("NOB-16", all_atoms=[A_sihua("命宫", ["禄", "权", "科"])])
_spec("NOB-17", all_atoms=[
    A_star("命宫", ["贪狼", "火星"]), A_bright("命宫", ["贪狼", "火星"], ["庙", "旺"]),
])
_spec("NOB-18", all_atoms=[A_loc("命宫", "卯"), A_star("命宫", ["武曲"])])
_spec("NOB-19", all_atoms=[A_sanfang("命宫", ["天府", "天相"])])
_spec("NOB-20", all_atoms=[A_sanfang("命宫", ["紫微", "天府"])])
_spec("NOB-21", all_atoms=[A_sanfang("命宫", ["文昌", "文曲"])])
_spec("NOB-22", all_atoms=[
    A_sihua("命宫", ["权", "禄"], scope="palace"),
    A_bright("命宫", _sihua_stars("权", "禄"), ["庙", "旺"]),
])
_spec("NOB-23", all_atoms=[
    A_loc("命宫", "辰戌丑未"), A_star("命宫", ["擎羊"]),
    {"kind": "jixiang", "palace": "命宫"},
])
_spec("NOB-24", all_atoms=[A_loc("命宫", "卯"), A_star("命宫", ["巨门", "天机"])])
_spec("NOB-25", all_atoms=[A_star("命宫", ["禄存"]), A_sihua("命宫", ["禄"])])
_spec("NOB-26", all_atoms=[A_star("命宫", ["紫微"]), A_jia("命宫", ["太阳", "太阴"])])
_spec("NOB-27", all_atoms=[A_sihua("命宫", ["科", "禄"])])

_spec("POV-01", all_atoms=[A_star("命宫", ["廉贞"]), {"kind": "kongwang"}])
_spec("POV-02", all_atoms=[A_star("命宫", ["禄存"]), {"kind": "kongwang"}])
_spec("POV-03", all_atoms=[A_star("命宫", ["天马"]), {"kind": "kongwang"}])
_spec("POV-04", all_atoms=[{"kind": "fanbei"}, A_star("命宫", ["巨门"])])
_spec("POV-05", any_groups=[
    [A_star("命宫", ["武曲", "廉贞"])],
    [A_star("身宫", ["武曲", "廉贞"])],
])
_spec("POV-06", all_atoms=[
    A_star("命宫", ["破军"]), A_bright("命宫", ["破军"], ["陷"]),
])
_spec("POV-07", all_atoms=[
    A_star("命宫", ["擎羊", "陀罗", "火星", "铃星"]),
    A_bright("命宫", ["擎羊", "陀罗", "火星", "铃星"], ["陷"]),
])
_spec("POV-08", all_atoms=[
    A_star("命宫", ["禄存"]), A_sihua("命宫", ["禄"], scope="palace"),
    A_star("命宫", ["地空", "地劫"], "any"),
])

for _pid in ("MISC-01", "MISC-02", "MISC-03", "MISC-04",
             "MISC-05", "MISC-06", "MISC-07", "MISC-08"):
    _spec(_pid, all_atoms=[{"kind": "yunxian"}])


# ============================================================
# 格局求值
# ============================================================
def _eval_pattern(pid: str, view: _View) -> dict:
    spec = _PATTERN_SPEC.get(pid)
    if spec is None:
        return {"evaluated": False, "hit": False, "evidence": [],
                "reason": "投影缺失（_PATTERN_SPEC 未覆盖该 pattern_id）"}
    groups = ([spec["all"]] if spec["all"] else []) + list(spec["any"])
    best, err = [], None
    for group in groups:
        try:
            ok, evidence = _eval_group(group, view)
        except _Unsupported as exc:
            err = str(exc)
            continue
        if ok:
            return {"evaluated": True, "hit": True, "evidence": evidence}
        if len(evidence) > len(best):
            best = evidence
    if err is not None:
        return {"evaluated": False, "hit": False, "evidence": [], "reason": err}
    return {"evaluated": True, "hit": False, "evidence": best}


def _match_patterns(view: _View) -> tuple[list, list]:
    rules = ALL_PATTERNS.values() if isinstance(ALL_PATTERNS, dict) else ALL_PATTERNS
    hits, unevaluated = [], []
    for rule in rules:
        pid = rule.get("pattern_id", "")
        res = _eval_pattern(pid, view)
        base = {
            "pattern_id": pid,
            "pattern_name": rule.get("pattern_name", ""),
            "school": rule.get("school", ""),
            "source": rule.get("source", ""),
            "source_section": rule.get("source_section", ""),
            "verbatim": rule.get("verbatim", ""),
            "formation_conditions": list(rule.get("formation_conditions") or []),
        }
        if res["evaluated"] and res["hit"]:
            base.update(hit=True, evidence=res["evidence"])
            hits.append(base)
        elif not res["evaluated"]:
            base.update(hit=False, reason=res["reason"])
            unevaluated.append(base)
    return hits, unevaluated


# ============================================================
# 命宫得地/失陷诀（PF 12 / PD 9，按命宫地支直查）
# ============================================================
def _jue_entry(rule: dict, kind: str, soul_branch: str) -> dict:
    """PF/PD 条文：母表只按命宫地支索引，条文内的星曜组合条件未结构化。

    因此这里只做「命宫地支命中该条文」的**参考条文**输出，不作吉凶判定
    （hit 恒为 False、evaluated 恒为 False），避免「戌宫紫破若相逢」这类
    含星曜组合的条文被误当作本盘失陷结论。
    """
    return {
        "rule_id": rule.get("rule_id", ""),
        "kind": kind,
        "palace_branch": rule.get("palace_branch", ""),
        "soul_branch": soul_branch,
        "verbatim": rule.get("verbatim", ""),
        "school": rule.get("school", ""),
        "source": rule.get("source", ""),
        "source_section": rule.get("source_section", ""),
        "branch_matched": True,
        "evaluated": False,
        "hit": False,
        "reason": "条文含未提取的星曜组合条件，本层仅作按命宫地支的参考条文",
    }


def _palace_jue(view: _View) -> list:
    soul = view.soul_branch
    if not soul:
        return []
    out = []
    for rule in PALACE_FORTUNE_RULE:
        if str(rule.get("palace_branch", "")) == soul:
            out.append(_jue_entry(rule, "得地诀", soul))
    for rule in PALACE_DEPRIVATION_RULE:
        if soul in str(rule.get("palace_branch", "")):
            out.append(_jue_entry(rule, "失陷诀", soul))
    return out


# ============================================================
# 女命（NM 9 + NMZ 6，仅女命盘产出）
# ============================================================
_NV_SPEC: dict[str, dict] = {}


def _nv(pid: str, all_atoms=None, any_groups=None):
    _NV_SPEC[pid] = {"all": list(all_atoms or []), "any": [list(g) for g in (any_groups or [])]}


_nv("NM-01", any_groups=[
    [A_star("命宫", ["天府"])], [A_star("命宫", ["天相"])],
    [A_star("命宫", ["廉贞"])], [A_star("命宫", ["天同"])],
])
_nv("NM-02", all_atoms=[
    A_loc("命宫", "寅卯辰巳午"),
    A_star("命宫", ["紫微", "太阳"], "any"),
])
_nv("NM-03", any_groups=[
    [A_star("命宫", ["左辅"])], [A_star("命宫", ["天魁"])],
    [A_star("命宫", ["右弼"])], [A_star("命宫", ["天相"])],
    [A_star("命宫", ["禄存"])],
])
_nv("NM-04", all_atoms=[
    A_loc("命宫", "巳亥"), A_star("命宫", ["紫微", "天府"]),
])
_nv("NM-05", any_groups=[
    [A_star("命宫", ["巨门"])], [A_star("命宫", ["天机"])],
    [A_star("命宫", ["天梁"])], [A_star("命宫", ["太阴"])],
])
_nv("NM-06", any_groups=[
    [A_star("命宫", ["擎羊"])], [A_star("命宫", ["火星"])],
    [A_star("命宫", ["文昌"])], [A_star("命宫", ["文曲"])],
    [A_star("命宫", ["武曲"])], [A_star("命宫", ["破军"])],
])
_nv("NM-07", any_groups=[
    [A_star("命宫", ["贪狼"])], [A_star("命宫", ["七杀"])],
])
_nv("NM-08", any_groups=[
    [A_star("命宫", ["禄存"])],
    [A_sihua("命宫", ["禄"], scope="palace")],
])
_nv("NM-09", any_groups=[
    [A_star("夫妻宫", ["擎羊", "陀罗", "火星", "铃星", "地空", "地劫"], "any")],
    [{"kind": "empty", "palace": "夫妻宫"}],
])


def _nvming(view: _View) -> dict:
    if not view.is_female():
        return {"matched": [], "definitions": [], "note": "男命盘，本出口空置"}
    rules = NVMING_RULES.values() if isinstance(NVMING_RULES, dict) else NVMING_RULES
    matched = []
    for rule in rules:
        pid = rule.get("rule_id", "")
        res = _eval_pattern_nv(pid, rule, view)
        if res["evaluated"] and res["hit"]:
            matched.append({
                "rule_id": pid,
                "name": rule.get("name", ""),
                "verbatim": rule.get("verbatim", ""),
                "condition": rule.get("condition", ""),
                "good_stars": list(rule.get("good_stars") or []),
                "bad_stars": list(rule.get("bad_stars") or []),
                "evidence": res["evidence"],
            })
    definitions = [{
        "rule_id": r.get("rule_id", ""),
        "name": r.get("name", ""),
        "verbatim": r.get("verbatim", ""),
        "condition": r.get("condition", ""),
    } for r in (NVMING_ZHUAN.values() if isinstance(NVMING_ZHUAN, dict) else NVMING_ZHUAN)]
    return {"matched": matched, "definitions": definitions, "note": ""}


def _eval_pattern_nv(pid: str, rule: dict, view: _View) -> dict:
    """女命条目求值：先按 _NV_SPEC 谓词，缺投影时退化为 good_stars 判据。"""
    spec = _NV_SPEC.get(pid)
    if spec is None:
        stars = view.stars_in("命宫")
        want = set(rule.get("good_stars") or [])
        if not want:
            return {"evaluated": False, "hit": False, "evidence": [],
                    "reason": "投影缺失且无 good_stars 可退化"}
        hit = bool(stars & want)
        return {"evaluated": True, "hit": hit,
                "evidence": [f"命宫星曜={sorted(stars)} 含吉星{want}" if hit
                             else f"命宫星曜={sorted(stars)} 不含{want}"]}
    groups = ([spec["all"]] if spec["all"] else []) + list(spec["any"])
    best, err = [], None
    for group in groups:
        try:
            ok, evidence = _eval_group(group, view)
        except _Unsupported as exc:
            err = str(exc)
            continue
        if ok:
            return {"evaluated": True, "hit": True, "evidence": evidence}
        if len(evidence) > len(best):
            best = evidence
    if err is not None:
        return {"evaluated": False, "hit": False, "evidence": [], "reason": err}
    return {"evaluated": True, "hit": False, "evidence": best}


# ============================================================
# 童限（CL 5，起限岁数内给落宫）
# ============================================================
_DATA_ISSUES = [
    "空亡（旬中空亡）安法未实现：POV-01/02/03 不参与判定",
    "日月反背判据未定：POV-04 不参与判定",
    "MISC-01~08 属运限叠加/主观项，本命单盘不可判定",
    "PF 12 / PD 9 为按命宫地支索引的参考条文，条文内星曜组合条件未结构化，"
    "出口只给参考条文、不作得地/失陷吉凶判定",
    "NOB-11 母表 formation_conditions 作「寅申子辰」，原典 verbatim 作「寅申子午」；"
    "七杀不入辰，本层按原典取「寅申子午」",
    "童限：CL-01「十五命宫看端的」与顺行十二宫 15 岁落位不自洽，"
    "本层仅在五行局起限岁数内（≤ 局数）给落宫",
]


def _child_limit(view: _View) -> list:
    out = [{
        "rule_id": r.get("rule_id", ""),
        "name": r.get("name", ""),
        "verbatim": r.get("verbatim", ""),
        "condition": r.get("condition", ""),
        "source": r.get("source", ""),
        "source_section": r.get("source_section", ""),
    } for r in CHILD_LIMIT_RULES]
    age, ju = view.nominal_age(), view.ju
    fact = {"nominal_age": age, "ju": ju, "palace": "", "branch": "",
            "evaluated": False, "reason": ""}
    if not view.soul_branch or ju <= 0:
        fact["reason"] = "缺命宫地支或五行局，童限不落宫"
    elif age > ju:
        fact["reason"] = f"虚岁 {age} 已过五行局起限岁数 {ju}，童限不再适用"
    else:
        i = (BRANCH_ORDER.index(view.soul_branch) + age - 1) % 12
        branch = BRANCH_ORDER[i]
        fact.update(palace=view.by_branch.get(branch, ""), branch=branch, evaluated=True,
                    reason="CL-01「余年一派顺流行」：命宫起 1 岁顺行地支")
    out.append({
        "rule_id": "CL-FACT",
        "name": "童限落宫（本盘）",
        "verbatim": "一命二财三疾厄，四妻五福六官禄，余年一派顺流行",
        "computed": fact,
        "evaluated": fact["evaluated"],
    })
    return out


# ============================================================
# 大限进阶（LA 7，可判定者给 hit）
# ============================================================
def _limit_advanced(view: _View, facts: dict) -> list:
    soul = view.soul_branch
    tsf = three_square_four(soul) if soul else {}
    opp = tsf.get("opposite", "")
    san = [b for b in (tsf.get("self"), opp, tsf.get("trine_1"), tsf.get("trine_2")) if b]
    flow_branches = {b for b in (facts.get("flow_yang"), facts.get("flow_tuo")) if b}
    out = []
    for rule in LIMIT_ADVANCED_RULES:
        rid = rule.get("rule_id", "")
        entry = {
            "rule_id": rid,
            "name": rule.get("name", ""),
            "verbatim": rule.get("verbatim", ""),
            "condition": rule.get("condition", ""),
            "definition": rule.get("definition", ""),
            "source": rule.get("source", ""),
            "source_section": rule.get("source_section", ""),
            "evaluated": False, "hit": False, "evidence": [], "reason": "",
        }
        if rid == "LA-01":
            ben = sorted(view.stars.get(view.by_branch.get(opp, ""), set())
                         & {"擎羊", "陀罗"})
            hit = bool(ben) and bool(flow_branches & {opp, soul})
            entry.update(evaluated=True, hit=hit, evidence=[
                f"命宫对宫={view.by_branch.get(opp, '?')}({opp or '?'}) 本命擎羊/陀罗={ben}",
                f"流羊={facts.get('flow_yang', '?')} 流陀={facts.get('flow_tuo', '?')}",
            ])
        elif rid == "LA-02":
            qi_sha = sorted(view.sanfang_stars("命宫") & {"七杀"})
            hit = bool(qi_sha) and bool(flow_branches & set(san))
            entry.update(evaluated=True, hit=hit, evidence=[
                f"命宫三方四正含七杀={bool(qi_sha)}", f"流羊/流陀在命宫三方四正={bool(flow_branches & set(san))}",
            ])
        elif rid == "LA-07":
            entry["reason"] = "天伤/天使安法未实现，本层不判定"
        else:
            entry["reason"] = "原则性规则（南北斗应期/多限叠加），需上下文叠加方可判定"
        out.append(entry)
    return out


# ============================================================
# 太岁小限（TMPL 25 + TDJ 1 + TLY 3）+ 运限事实
# ============================================================
def _flow_gan(year: int) -> str:
    return _GAN[(year - 4) % 10] if year else ""


def _temporal(view: _View) -> tuple[dict, list]:
    birth_branch = BRANCH_ORDER[(view.birth_year - 1984) % 12] if view.birth_year else ""
    age = view.nominal_age()
    tai = taisui_branch(view.flow_year) if view.flow_year else ""
    gender_cn = "女" if view.is_female() else "男"
    try:
        small = small_limit_branch(birth_branch, gender_cn, age) if (birth_branch and age) else ""
    except Exception:  # noqa: BLE001 - 小限表缺参时不阻断解层
        small = ""
    gan = _flow_gan(view.flow_year)
    flow = flow_star_positions(gan) if gan else {}
    facts = {
        "flow_year": view.flow_year,
        "nominal_age": age,
        "gender": gender_cn,
        "birth_year_branch": birth_branch,
        "taisui_branch": tai,
        "taisui_palace": view.by_branch.get(tai, ""),
        "small_limit_branch": small,
        "small_limit_palace": view.by_branch.get(small, ""),
        "doujun_palace": str(getattr(view.chart, "doujun_palace", "") or ""),
        "flow_year_stem": gan,
        "flow_lu": flow.get("lu", ""),
        "flow_yang": flow.get("yang", ""),
        "flow_tuo": flow.get("tuo", ""),
        "da_xian_palace": str(getattr(view.chart, "decadal_palace", "") or ""),
        "five_elements_class": str(getattr(view.chart, "fiveElementsClass", "") or ""),
        "soul_branch": view.soul_branch,
    }
    rules = []
    for rule in TAISUI_XIAOXIAN_RULES:
        palace = str(rule.get("palace", "") or "子")
        if palace != tai:
            continue
        name = view.by_branch.get(palace, "")
        stars = view.stars.get(name, set())
        rules.append({
            "rule_id": rule.get("rule_id", ""),
            "name": rule.get("name", ""),
            "verbatim": rule.get("verbatim", ""),
            "condition": rule.get("condition", ""),
            "palace": palace,
            "palace_name": name,
            "good_hits": sorted(stars & set(rule.get("good_stars") or [])),
            "bad_hits": sorted(stars & set(rule.get("bad_stars") or [])),
            "applicable": bool(small) and small == tai,
        })
    for rule in DOUJUN_RULES:
        rules.append({
            "rule_id": rule.get("rule_id", ""),
            "name": rule.get("name", ""),
            "verbatim": rule.get("verbatim", ""),
            "condition": rule.get("condition", ""),
            "note": rule.get("note", ""),
            "kind": "concept",
            "computed_palace": facts["doujun_palace"],
        })
    for rule in LIUYAO_RULES:
        rules.append({
            "rule_id": rule.get("rule_id", ""),
            "name": rule.get("name", ""),
            "verbatim": rule.get("verbatim", ""),
            "condition": rule.get("condition", ""),
            "note": rule.get("note", ""),
            "kind": "concept",
            "computed": {"流禄": flow.get("lu", ""), "流羊": flow.get("yang", ""),
                         "流陀": flow.get("tuo", "")},
        })
    return facts, rules


# ============================================================
# 辅煞星断语（AUX 8 / SHA 6 / MISC 2，命宫口径）
# ============================================================
def _aux_verdicts(view: _View) -> list:
    name = view.soul_palace
    stars = view.stars.get(name, set())
    out = []
    for group, verdicts in (("辅星", AUX_STAR_VERDICTS),
                            ("煞星", SHA_STAR_VERDICTS),
                            ("杂曜", MISC_STAR_VERDICTS)):
        for v in verdicts:
            star = v.get("star", "")
            if star not in stars:
                continue
            out.append({
                "group": group,
                "star": star,
                "palace": v.get("palace", "命宫"),
                "palace_name": name,
                "verbatim": v.get("verbatim", ""),
                "source": v.get("source", ""),
                "status": v.get("status", ""),
                "hit": True,
            })
    return out


# ============================================================
# 出口
# ============================================================
def build_classical_detail(chart) -> dict:
    """九出口的经典细则层。缺盘或缺命宫时返回同形空结构，不抛异常。"""
    view = _View(chart)
    if not view.palaces or not view.soul_palace:
        out = _empty_structure()
        out["summary"]["note"] = "盘面无 12 宫或定位不到命宫，经典细则层跳过"
        return out

    jue = _palace_jue(view)
    hits, unevaluated = _match_patterns(view)
    nv = _nvming(view)
    child = _child_limit(view)
    facts, temporal = _temporal(view)
    advanced = _limit_advanced(view, facts)
    aux = _aux_verdicts(view)
    return {
        "palace_jue": jue,
        "classical_patterns": hits,
        "nvming": nv["matched"],
        "child_limit": child,
        "limit_advanced": advanced,
        "temporal_rules": temporal,
        "aux_verdicts": aux,
        "temporal_facts": facts,
        "nvming_definitions": nv["definitions"],
        "nvming_note": nv["note"],
        "summary": {
            "palace_jue": len(jue),
            "classical_patterns": len(hits),
            "patterns_evaluated": sum(
                1 for pid in _PATTERN_SPEC if _eval_pattern(pid, view)["evaluated"]),
            "patterns_unevaluated": len(unevaluated),
            "nvming": len(nv["matched"]),
            "child_limit": len(child),
            "limit_advanced": len(advanced),
            "temporal_rules": len(temporal),
            "aux_verdicts": len(aux),
            "unevaluated": [
                {"pattern_id": e["pattern_id"], "pattern_name": e["pattern_name"],
                 "reason": e["reason"]} for e in unevaluated
            ],
            "data_issues": list(_DATA_ISSUES),
        },
        "engine_notes": [
            "解层输出以原文（verbatim）为准，未实现判据不出命中",
            "命宫限童限/小限/太岁一律用农历虚岁（flow_year - birth_year + 1）",
        ],
    }
