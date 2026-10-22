"""变异验证：2026-10-07 深度审计修复批（批次 A/B/C/D）。

守卫全绿不等于「缺陷复现了也会绿」——那才是要害。本套件逐条把三类审计查出的
缺陷**原样注入回去**，要求 tests/heluo/test_audit_batch_20261007.py 必须变红：

* 空断言复现：把没跑的检查写成已检查
* 输出契约回退：字段重新丢失、文案重新写错、重复条目重新出现
* 伪引与假授权复现：出处重新指向不存在的文件、授权重新挂到不存在的规则集

另有一条**判决口径漂移**类变异：审计只要求改证据表述时，判决绝不能跟着变。
"""
from __future__ import annotations

import hashlib
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E = ROOT / "src" / "tongshu" / "engines" / "heluo"
HG = E / "hua_gong.py"
GD = E / "guidance.py"
GJ = E / "guajie.py"
CN = E / "canonical.py"
FS = E / "frozen_state.py"
EP = E / "evidence_producer.py"
DR = E / "diagnosis_rule_graph.py"
NUM = E / "numbers.py"
HS = E / "hexagram_state.py"
IT = E / "interpretation.py"
GM = E / "gui_ming_liu_ju.py"

#: 本模块全部守卫文件，必须一次跑完（只跑第一个会「假存活」）
TEST = ("tests/heluo/test_audit_batch_20261007.py",
        "tests/heluo/test_h6_hua_gong.py",
        "tests/heluo/test_h12_diagnosis.py",
        "tests/heluo/test_h2_frozen_state.py",
        "tests/heluo/test_full_pipeline.py")

MUTATIONS = [
    # ── A：空断言复现（把没跑的检查写成已检查） ──
    (HG, "纳音层未参与却宣称「三层俱不得」（空断言复现）",
     'evidence.append("正体、互体俱不得化工；三级纳音%s，"\n'
     '                            "故本盘**只作二级否定**，不得称「三层俱不得」"',
     'evidence.append("正体、互体、纳音三层俱不得化工（%s）"'),
    (HG, "纳音层是否真的参与判定被抹掉",
     "    nayin_checked = False\n",
     "    nayin_checked = True\n"),

    # ── A：证据链自相矛盾复现 ──
    (HG, "打印当层集合、判定却按全集（审计查出的自相矛盾复现）",
     "    all_trigrams = zhengti | huti",
     "    all_trigrams = pool"),
    (HG, "反卦不再标层（「见于正体/互体」信息丢失）",
     "        if t in zhengti:\n            parts.append(\"正体\")",
     "        if False:\n            parts.append(\"正体\")"),

    # ── A：判决口径漂移（审计只许改表述） ──
    (HG, "化工相反表被改成先天对宫（判决随之漂移）",
     '    "兑": "震",   # L591\n    "震": "兑",   # L594\n}',
     '    "兑": "艮",\n    "震": "巽",\n    "艮": "兑",\n    "乾": "坤",\n    "坤": "乾",\n}'),
    (HS, "五行相克判定失效（KEZHI 判不出）",
     'ELEMENT_OVERCOMES = {\n    "木": "土", "土": "水", "水": "火", "火": "金", "金": "木"\n}',
     "ELEMENT_OVERCOMES: dict[str, str] = {}"),

    # ── A：最凶档重新变成零建议零警示 ──
    (GD, "KEZHI 模板被删（原典最凶档重新落入「待判定」）",
     '    "KEZHI": "化工受克，原典明言「尤凶」，宜彻底守成，不可进取。",',
     '    # KEZHI 模板被删'),
    (GD, "KEZHI 不再产警示（最凶档零警示复现）",
     '            "KEZHI": ("化工业已受克", "化工受克，原典「但忌克制，尤凶」——本岁宜彻底守成，"\n'
     '                                       "不可主动出击，亦不宜大额投入。", 0.95),',
     ""),

    # ── B：输出契约回退 ──
    (GJ, "十二凶卦重新寄生进成对判法（每调必重复两条）",
     "    return warns\n\n\ndef check_twelve_xiong(",
     "    warns += check_twelve_xiong(hexagram, \"命卦\")\n"
     "    return warns\n\n\ndef check_twelve_xiong("),
    (GJ, "流年卦又被标成「命卦」（审计查出的误标复现）",
     '+ check_twelve_xiong(liunian_hexagram, "流年卦"))',
     '+ check_twelve_xiong(liunian_hexagram, "命卦"))'),
    (GJ, "正对反对不再去重",
     "        zdfd = list(dict.fromkeys(zdfd))   # 去重且保序",
     "        # 不去重"),
    (GJ, "流年爻重新丢掉象曰与释义",
     '                "xiang": self.liunian_yao.xiang, "yi": self.liunian_yao.yi,\n',
     ""),
    (GJ, "叶/不叶重新丢掉卦气月与生月",
     '                "gua_qi_month": self.liunian_ye_buye.gua_qi_month,\n'
     '                "birth_month": self.liunian_ye_buye.birth_month,\n',
     ""),
    (GJ, "流日文案重新宣称「每爻管5日」（与逐日一爻算法矛盾）",
     'f"（原典起日卦例·**逐日一爻**，段内五日各变一次；本行为第{target_day}日）")',
     'f"（原典起日卦例·每爻管5日，第{target_day}日）")'),
    (GJ, "生月缺失重新静默兜底",
     "        if _birth_month_missing:",
     "        if False:"),

    # ── B：era 出处 ──
    (CN, "era 再次算完即丢",
     "            seasonal_hexagram=seasonal_hex,\n            era=era,",
     "            seasonal_hexagram=seasonal_hex,"),
    (FS, "era 重新被时区顶替",
     '    _era = getattr(result, "era", None) or "unknown"',
     '    _era = getattr(getattr(result, "input", None), "timezone", "zhong")'),
    (FS, "冻结态重新只搬 state，丢掉 level/reduced",
     '                "level": self.hua_gong_level,\n                "reduced": self.hua_gong_reduced,\n',
     ""),
    (EP, "化工证据重新不报层位",
     '                        "level": getattr(heluo_result.hua_gong, "level", None),\n'
     '                        "reduced": getattr(heluo_result.hua_gong, "reduced", None),\n',
     ""),

    # ── C：伪引与假授权复现 ──
    (EP, "伪引复现：出处指回不存在的 data/rules/heluo_*.json",
     'source_rule_ref="起例卷之下·论化工（L573/L576/L582）"',
     'source_rule_ref="data/rules/heluo_hua_gong.json"'),
    (DR, "授权方重新挂到不存在的「V13_河洛诊断规则集」",
     '            authorized_by="HELUO_RULES::" + (",".join(_auth) if _auth else "NONE"),',
     '            authorized_by="V13_河洛诊断规则集",'),
    (DR, "未注册 rule_id 重新被静默丢弃",
     "            dropped_rule_ids.append(ev.rule_id)\n",
     ""),
    (DR, "天数地数重新被归入 LIFE_EVENT（语义错配）",
     '    "HL_TIAN_DI_SHU": "CAREER",\n', ""),
    (DR, "已注册未产出的规则标注被删",
     '    "HL_DAYUN": RuleNode(          # TODO(证据未接入): 已注册未产出，见上',
     '    "HL_DAYUN": RuleNode('),

    # ── D：机理清理回退 ──
    (NUM, "假别名 resolve_yuantang = None 复现",
     "# 真身：from .yuan_tang import resolve_yuantang   # = find_yuantang",
     "resolve_yuantang = None"),
    (HS, "Tuple 再次未导入",
     "from typing import Optional, Tuple",
     "from typing import Optional"),
    (IT, "时间衰减空操作复现（键集零交集的乘法）",
     "        weights = FACTOR_WEIGHTS.copy()\n",
     "        weights = FACTOR_WEIGHTS.copy()\n"
     "        time_modifier = self._calculate_time_decay()\n"
     "        for _k in weights:\n"
     "            weights[_k] *= time_modifier.get(_k, 1.0)\n"),
    (IT, "五行修正空操作复现（与归一化精确抵消）",
     "        weights = FACTOR_WEIGHTS.copy()\n",
     "        weights = FACTOR_WEIGHTS.copy()\n"
     "        element_modifier = self._calculate_element_modifier()\n"
     "        for _k in weights:\n"
     "            weights[_k] *= (1 + element_modifier)\n"),
    (IT, "伪书名出处复现（《协纪辨方书》）",
     '            source="河洛真数·起例卷之下·流年卦例"',
     '            source="《协纪辨方书》"'),
    (IT, "机会/风险因子重新贴上无行号的卷次书名",
     "classical_basis=_NO_BASIS\n",
     'classical_basis="《河洛理数·卷之三》"\n'),

    # ── 讹字留证 ──
    (GM, "L648 讹字留证被删（静默订正复现）",
     "**九月生人得地数多人数少**",
     "**九月生人得地数多天数少**"),
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


cache_dir = tempfile.mkdtemp(prefix="audit_mutate_pycache_")
ENV = dict(os.environ)
ENV.update({
    "PYTHONPATH": "src",
    "PYTHONIOENCODING": "utf-8",
    "PYTHONPYCACHEPREFIX": cache_dir,
    "TONGSHU_ALLOW_ZIWEI_STUB": "1",
    "TONGSHU_AUTHORITY_CREDENTIALS": ("architecture-governance:schema-v1-arch-gov-2026;"
                                      "admission_registry:test-cred-hash"),
})

TARGETS = (HG, GD, GJ, CN, FS, EP, DR, NUM, HS, IT, GM)
originals: dict[Path, str] = {}


def read(p: Path) -> str:
    raw = io.open(p, encoding="utf-8", newline="").read()
    return raw.replace("\r\n", "\n") if "\r\n" in raw else raw


def write(p: Path, text: str) -> None:
    nl = "\r\n" if "\r\n" in io.open(p, encoding="utf-8", newline="").read() else "\n"
    io.open(p, "w", encoding="utf-8", newline="").write(text.replace("\n", nl))


for p in TARGETS:
    originals[p] = read(p)
base = {p: sha(t) for p, t in originals.items()}


def run() -> tuple[bool, str]:
    pr = subprocess.run(
        [sys.executable, "-m", "pytest", *TEST, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8")
    lines = [ln for ln in pr.stdout.strip().splitlines() if ln.strip()]
    return pr.returncode == 0, (lines[-1] if lines else pr.stdout[-200:])


print("=" * 76)
problems: list[str] = []

ok0, msg0 = run()
print(f"[基线 ] 未变异应全绿 → {'OK  ' if ok0 else 'FAIL'}  {msg0}")
if not ok0:
    problems.append("基线未绿")

for target, name, old, new in MUTATIONS:
    src = originals[target]
    if old not in src:
        print(f"[SKIP ] {name} —— 锚点未命中")
        problems.append(f"{name}（锚点未命中）")
        continue
    write(target, src.replace(old, new, 1))
    try:
        green, msg = run()
    finally:
        write(target, originals[target])
    if sha(read(target)) != base[target]:
        problems.append(f"{name}（还原失败）")
        print(f"[BROKEN] {name} —— 还原失败！")
        continue
    caught = not green
    print(f"[{'CAUGHT' if caught else 'MISSED'}] {name}"
          + ("" if caught else f"   ← 变异存活！{msg}"))
    if not caught:
        problems.append(f"{name}（变异存活）")

print("=" * 76)
if problems:
    print("问题：" + "；".join(problems))
    raise SystemExit(1)
print(f"\n✅ {len(MUTATIONS)} 条变异全部被守卫抓住，还原后基线一致")
raise SystemExit(0)