"""变异验证：2026-10-08 批次 E（死代码/死参数）与 F（元气两说 + 爻辞取象 + 三条数格）

守绿全不等于缺陷已复现——缺陷是**改了也照样全绿**的东西。
本文件逐条把本轮审计查出的缺陷**原样注入回去**，要求守卫文件必须变红。

═══════════════════════════════════════════════════════════════════
三个必须遵守的写法约束（都是踩过坑之后立的）
═══════════════════════════════════════════════════════════════════

1. **一次跑完本模块全部守卫文件**。只跑第一个会漏：变异的可达路径
   常常不在你以为的那个文件里，漏跑等于假红。
2. **锚点必须命中可达代码**。打不到可达路径的变异是假红，会让人误以为
   守卫有牙。锚点未命中一律算失败并报出来。
3. **不许改测试语义来求绿**。守卫是牙齿，牙齿不能为了合上嘴而锉平。
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
GJ = E / "guajie.py"          # CRLF
HG = E / "hua_gong.py"          # F-3：四正卦节气窗口
CN = E / "canonical.py"
GD = E / "guidance.py"
IT = E / "interpretation.py"
NUM = E / "numbers.py"
SG = E / "yue_ling_shu_ge.py"
YX = E / "yao_xiang.py"
YT = E / "yuanqi_tables.py"

#: 本模块全部守卫文件（E/F 三批一次跑完，见约束 1）
TEST = (
    "tests/heluo/test_audit_batch_e_20261008.py",
    "tests/heluo/test_yuanqi_tables_fidelity.py",
    "tests/heluo/test_yaoxiang_and_shu_ge_l741_l726.py",
    "tests/heluo/test_huagong_jieqi_windows.py",
    # 受影响模块的既有守卫：数格表既有判域、guajie 输出契约
    "tests/heluo/test_yue_ling_shu_ge_vs_original.py",
    "tests/heluo/test_refusal_corrections_round2.py",
    "tests/heluo/test_h6_hua_gong.py",
    "tests/test_heluo_guajie_wiring.py",
)

MUTATIONS = [
    # ══ 批次 E ══════════════════════════════════════════════════
    (GJ, "E1 结构化视图又丢 benming（判词整块消失）",
     '    out["benming"] = gj.get("benming")\n', ""),
    (GJ, "E1 结构化视图又丢 evidence（数十行判词清零）",
     '    out["evidence"] = gj.get("evidence") or []\n',
     '    out["evidence"] = []\n'),

    (GJ, "E2 kuozhan 八个判法退回裸 pass（异常被吞）",
     '            _KZ_ERRORS.append("%s: %s: %s" % (name, type(_e).__name__, _e))',
     "            pass"),
    (GJ, "E2 异常留痕只剩一句「失败」，定位不到判法",
     '            _KZ_ERRORS.append("%s: %s: %s" % (name, type(_e).__name__, _e))',
     '            _KZ_ERRORS.append("计算失败")'),

    (NUM, "E3 注释又声称天数25 走特殊分支（本轮修掉的说谎）",
     "    - 兜底：余数与商**皆为0**（即传入 0）→ 5（中宫）",
     "    - 特殊：天数25→5（中宫）"),
    (NUM, "E3 末尾行内注释又撒谎",
     "return 5  # 余数与商皆为0（即 tian_shu==0）时的兜底，归中宫（5）。天数25 走不到这里。",
     'return 5  # 天数=25的特殊情况：除还天地正数后余0，商亦为0，原典"天数正数25"归中宫（5）'),

    (GD, "E4 confidence 基准被悄悄改成 0.99",
     "_CONF_BASE = 0.85", "_CONF_BASE = 0.99"),
    (GD, "E4 动作项重新写死 0.85（不再走 _CONF_BASE）",
     "                confidence=_CONF_BASE,", "                confidence=0.85,"),
    (GD, "E4 注释又自称「基于原典权威度」（伪引复现）",
     "confidence: float            # 0-1（引擎自定标度，**无原典依据**，见 _CONF_BASE）",
     "confidence: float            # 0-1（基于原典权威度）"),

    (GD, "E5 judgment 又被收下不用（签名留、调用不传）",
     "        overview = self._build_overview(source_gua, hua_gong_state, judgment)",
     "        overview = self._build_overview(source_gua, hua_gong_state)"),
    (GD, "E5 断言条数被写死（换 judgment 仍吐同一串字）",
     '            tail = f"本结论由 {len(sup)} 条断言支撑"',
     '            tail = "本结论成立"'),
    (GD, "E5 凭空造一个授权方名字（authorized_by 明明没有）",
     '            if by:\n                tail += f"（授权：{by}）"\n',
     '            tail += "（授权：河洛诊断规则集）"\n'),

    (IT, "E6 secondary 又写死（opp 收下不用）",
     '        secondary = [o.type for o in opp_s[:2]] or ["巩固基础"]',
     '        secondary = ["巩固基础", "学习提升"]'),
    (IT, "E6 avoid 又写死（risk 收下不用）",
     '        avoid = [r.type for r in risk_s[:2]] or ["急躁冒进"]',
     '        avoid = ["急躁冒进"]'),
    (IT, "E6 置信度又只看 score（净差不参与）",
     "        conf = round(max(0.0, min(1.0, base + 0.05 * net)), 2)",
     "        conf = base"),
    (IT, "E6 排序失效：按类型名字母排而非按强度/严重度",
     "        opp_s = sorted(pool_o, key=lambda o: -o.strength)",
     "        opp_s = sorted(pool_o, key=lambda o: o.type)"),

    (IT, "E7 ELEMENT_MODIFIERS 去掉作废标注（无出处权重又被当成有效规则）",
     "#: ⛔ 已作废（2026-10-08 标注）。",
     "#: 五行修正系数。"),
    # ⚠ 上一版这条变异只在常量里**加了一行注释**，而守卫判的是可执行代码
    #   （刻意剥掉注释与文档字符串），所以必然打空。静态守卫要用静态变异打：
    #   让作废常量真的进分数累加链。
    (IT, "E7 作废常量被投入判定",
     '        weighted_sum += 0.1 * weights.get("yuan_tang", 0)',
     '        weighted_sum += 0.1 * weights.get("yuan_tang", 0)'
     ' + ELEMENT_MODIFIERS.get("当令", 0)'),

    # ══ 批次 F-1：元气两说并存 + 干支纳卦 ══════════════════════
    (YT, "F1 元气干支两说被悄悄择一（说二被抹掉）",
     "YUANQI_GANZHI_TABLE_B: dict[str, YuanQiGuaRow] = {",
     "_DROPPED_B: dict[str, YuanQiGuaRow] = {"),
    (YT, "F1 反表被改成非同宫（说一的机械校验不再成立）",
     '    for g, row in YUANQI_FAN_TABLE.items():\n'
     '        duo_gan, duo_zhi = YUANQI_GANZHI_TABLE_A[DUI_GUA[g]]',
     '    for g, row in YUANQI_FAN_TABLE.items():\n'
     '        duo_gan, duo_zhi = YUANQI_GANZHI_TABLE_A.get(g, ("", ""))'),
    (YT, "F1 导入自校验被摘掉（表错了也没人喊）",
     "_self_check()", "# _self_check() 变异：自校验被摘"),

    # ══ 批次 F-2：爻辞取象 + 三条数格 ═════════════════════════
    (SG, "F2 并集判域分支被摘（四支退化为空）",
     "    if rule.alternatives:", "    if False:"),
    (SG, "F2 并集判域被压成单轴（只比天数不比地数）",
     "        return any(lo_t <= t <= hi_t and lo_d <= d <= hi_d",
     "        return any(lo_t <= t <= hi_t"),
    (SG, "F2 阴阳偏胜偏负四支被并成一个大矩形",
     "        alternatives=((0, 24, 30, 30), (25, 25, 0, 28),\n"
     "                      (26, 999, 30, 30), (25, 25, 32, 999)),",
     "        alternatives=((0, 24, 30, 30),),"),
    (SG, "F2 以强凌弱阈值从 40 放宽到 30（与以强伏弱混为一格）",
     '        match="tian_di", lo_t=40, hi_t=999, lo_d=0, hi_d=29,',
     '        match="tian_di", lo_t=30, hi_t=999, lo_d=0, hi_d=29,'),
    (SG, "F2 以下犯上地数下界从 50 放宽到 30（判域与以弱敌强混同）",
     '        match="tian_di", lo_t=0, hi_t=24, lo_d=50, hi_d=999,',
     '        match="tian_di", lo_t=0, hi_t=24, lo_d=30, hi_d=999,'),
    (SG, "F2 L732 讹字被静默订正（「水」悄悄改成「冬」）",
     "「名以下犯上，以卑逾尊，在阴月生人富贵，\"\n                \"而水以后夏至前生人最恶下贱。」",
     "「名以下犯上，以卑逾尊，在阴月生人富贵，\"\n                \"而冬以后夏至前生人最恶下贱。」"),
    (SG, "F2 未定义条件「更元堂安非其位」的登记被删",
     'conflict="⚠️ 原典在本条后缀了一个**本卷未定义**的条件——「更元堂安非其位」。',
     'conflict="'),

    (GJ, "F2 生产链不再扫描爻辞（yao_xiang 又变成躺平模块）",
     "        _hits, _evs = _scan_yao_xiang(", "        _hits, _evs = (None, []) or _scan_yao_xiang("),
    (GJ, "F2 命中结果不再入结果对象",
     "            res.yao_xiang_hits.append(_h)", "            pass"),
    (GJ, "F2 to_dict 又漏掉 yao_xiang_hits",
     '            "yao_xiang_hits": [\n', '            "_yao_xiang_hits": [\n'),
    (GJ, "F2 to_structured 又漏掉 yao_xiang_hits",
     '    out["yao_xiang_hits"] = gj.get("yao_xiang_hits") or []\n', ""),
    (GJ, "F2 用天数地数之凶冒充「卦数凶」（凭空造原典没有的判据）",
     "            gender=gender, shu_gua_xiang=None)",
     "            gender=gender, shu_gua_xiang=sx.shu_xiong)"),
    (GJ, "F2 拿公历日冒充农历日（「望前」判据被凭空补上）",
     "            _text, birth_month=birth_month or None, day_lunar=None,",
     "            _text, birth_month=birth_month or None, day_lunar=15,"),

    (YX, "F2 「言龙」月令窗口被改成 3–8（原典含二月）",
     "_YAN_LONG_MONTHS: frozenset[int] = frozenset({2, 3, 4, 5, 6, 7, 8})",
     "_YAN_LONG_MONTHS: frozenset[int] = frozenset({3, 4, 5, 6, 7, 8})"),
    (YX, "F2 「言木」春夏窗口被改成 2–6（原典自春分至夏）",
     "_YAN_MU_MONTHS: frozenset[int] = frozenset({3, 4, 5, 6})",
     "_YAN_MU_MONTHS: frozenset[int] = frozenset({2, 3, 4, 5, 6})"),
    (YX, "F2 「望前」界从十五改成三十且不再披露为引擎取定",
     "            ok = None if not day_lunar else (day_lunar < 15)\n"
     '            out.append(_mk(base, ok, extra="（引擎以农历十五为界，此近似原典未载）"))',
     "            ok = None if not day_lunar else (day_lunar < 30)\n"
     "            out.append(_mk(base, ok))"),
    (YX, "F2 无条件条目也参与判定（原典未给判据却硬判吉凶）",
     "        ok, participated=bool(base.conditional and ok is True))",
     "        ok, participated=True)"),
    (YX, "F2 取象表被合并（「言鸟」「言朋」并掉，单字出现查不到）",
     '    YaoXiangHit("鸟", "同（与言鸿同，亦主飞腾）", True, '
     '"卦数不凶方取此；卦数凶则走空浮薄"),\n', ""),

    # ══ 批次 F-3：四正卦化工节气窗口 ═════════════════════════
    (HG, "F3 坎窗口终点从惊蛰挪到雨水（四窗口切不满 jq 0–23）",
     '    ("坎", 0, 5), ("震", 6, 11),', '    ("坎", 0, 4), ("震", 6, 11),'),
    (HG, "F3 震窗口起点从春分挪到惊蛰（与 L585–L594 互证立刻对不上）",
     '    ("坎", 0, 5), ("震", 6, 11),', '    ("坎", 0, 5), ("震", 5, 11),'),
    (HG, "F3 节气序被改（窗口起止名全错位）",
     '"小满", "芒种", "夏至",', '"芒种", "夏至", "小暑",'),
    (HG, "F3 导入自校验被摘（窗口错了没人喊）",
     "\n_huagong_self_check()\n", "\n# _huagong_self_check()\n"),
    (HG, "F3 兜底披露被抹掉（走近似表时不写「兜底」）",
     '        _huagong_basis = ("月支近似表（**兜底**）——" + _jq_note',
     '        _huagong_basis = ("月支近似表——" + _jq_note'),
    (HG, "F3 L570 坤艮拒算被撤销（无出处的十八日窗口被放进来）",
     '    ("L570「坤艮卦主四季辰戌丑未月，除正节气十二日外，各旺十八日。」',
     '    ("L599「某某占位。"'),
    (HG, "F3 待批准登记被删（没接线这件事被当成已完成）",
     'HUAGONG_PENDING_BRANCH_SWITCH: dict = {',
     '_DROPPED_PENDING: dict = {'),
    (HG, "F3 越界节气开始瞎猜（jq 24 悄悄夹到末窗）",
     "    if jq is None or not (0 <= jq < len(_JQ_ORDER)):\n        return \"\"",
     "    if jq is None:\n        return \"\"\n"
     "    if not (0 <= jq < len(_JQ_ORDER)):\n        jq = len(_JQ_ORDER) - 1"),
    (CN, "F3 canonical 擅自接线（未批准就翻 Golden）",
     "                year_gan=year_gan, year_zhi=year_zhi,\n            )",
     "                year_gan=year_gan, year_zhi=year_zhi,\n"
     "                birth_date=birth_date,\n            )"),
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


cache_dir = tempfile.mkdtemp(prefix="batch_ef_mutate_")
ENV = dict(os.environ)
ENV.update({
    "PYTHONPATH": "src",
    "PYTHONIOENCODING": "utf-8",
    "PYTHONPYCACHEPREFIX": cache_dir,
    "TONGSHU_ALLOW_ZIWEI_STUB": "1",
    "TONGSHU_AUTHORITY_CREDENTIALS": ("architecture-governance:schema-v1-arch-gov-2026;"
                                      "admission_registry:test-cred-hash"),
})

TARGETS = (GJ, GD, IT, NUM, SG, YX, YT, HG, CN)
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


print("=" * 78)
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

print("=" * 78)
if problems:
    print(f"❌ {len(problems)} 条未过：")
    for p in problems:
        print("   -", p)
    sys.exit(1)
print(f"✅ {len(MUTATIONS)} 条变异全部被捕获")