"""变异验证：阴阳二数数格守卫是否真能抓住错误（2026-10-07）

每条变异往源码注入一个已知错误，跑守卫测试，必须**红**。

本轮特意针对开发中真实犯过的三个错设变异：
- 以强伏弱的地数区间漏写（矩形退化 → 全命中）
- 余 0 被当成「余偶」（(25,30) 同时命中孤阴背阳与安和自宁）
- 冲突登记在只有一个当事方时也报

同样用 PYTHONPYCACHEPREFIX 隔离字节码——否则「还原后复跑」可能因
陈旧 .pyc 假红（首版先天策数验证就栽在这）。
"""
from __future__ import annotations

import hashlib
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(r"D:\shuntian_heluo")
GE = ROOT / "src" / "tongshu" / "engines" / "heluo" / "yue_ling_shu_ge.py"
GJ = ROOT / "src" / "tongshu" / "engines" / "heluo" / "guajie.py"
#: 本模块的全部守卫文件。**必须一次跑完**——第二轮验证新增的
#: test_refusal_corrections_round2.py 里锁着「天数至弱」「三阳奇偶合象」
#: 等本轮新实现；只跑第一个文件时，那八条变异会「存活」，
#: 看起来像守卫失效，实则是套件配置漏了文件。
#: 2026-10-07 续挂 test_heluo_siduan_huti_nayin.py（死断四法的后天门控）。
TEST = ("tests/heluo/test_yue_ling_shu_ge_vs_original.py",
        "tests/heluo/test_refusal_corrections_round2.py",
        "tests/heluo/test_heluo_siduan_huti_nayin.py")

MUTATIONS = [
    (GE, "以强伏弱漏掉地数非矩形判据（退化为全命中）",
     "match=\"tian_di\", lo_t=30, hi_t=999, di_eq=30, di_le=12,",
     "match=\"tian_di\", lo_t=30, hi_t=999,"),
    (GE, "以强伏弱下界放宽到 29",
     "match=\"tian_di\", lo_t=30, hi_t=999, di_eq=30, di_le=12,",
     "match=\"tian_di\", lo_t=29, hi_t=999, di_eq=30, di_le=12,"),
    (GE, "余 0 不再排除（(25,30) 会同时命中孤阴背阳）",
     "if y <= 0 or y % 2 != rule.yu_parity:",
     "if y % 2 != rule.yu_parity:"),
    (GE, "孤阳不偶/孤阳自偶的奇偶判反",
     "yu_parity=0, yu_side=\"tian\",", "yu_parity=1, yu_side=\"tian\","),
    (GE, "地数至弱区间写成 1–12",
     'tian_band="不限", di_band="8–12", match="di", lo_d=8, hi_d=12,',
     'tian_band="不限", di_band="8–12", match="di", lo_d=1, hi_d=12,'),
    (GE, "地数得中区间写成 30–45（吞掉地数=30）",
     "match=\"di\", lo_d=32, hi_d=45,", "match=\"di\", lo_d=30, hi_d=45,"),
    (GE, "天地俱羸下界放宽到 25",
     "match=\"tian_di\", lo_t=0, hi_t=24, lo_d=0, hi_d=29,",
     "match=\"tian_di\", lo_t=0, hi_t=25, lo_d=0, hi_d=29,"),
    (GE, "阴阳相战把地数=30 也算进去",
     "if not (d < DI_ZHENG or d > DI_ZHENG):",
     "if False:"),
    (GE, "阴数偏少丢掉天数=25 的限定",
     "match=\"tian_di\",\n        lo_t=25, hi_t=25, lo_d=18, hi_d=28,",
     "match=\"di\",\n        lo_d=18, hi_d=28,"),
    (GE, "禄数男女向背对调（36/28 改成利女）",
     '(36, "老阳之禄", "利男不利女"),\n    (28, "少阳之禄", "利男不利女"),',
     '(36, "老阳之禄", "利女不利男"),\n    (28, "少阳之禄", "利女不利男"),'),
    (GE, "禄数在性别未给时按默认男性强判",
     "if not gender:\n                fit: bool | None = None",
     "if not gender:\n                gender = \"male\"\n            if not gender:\n                fit: bool | None = None"),
    (GE, "援阴阳：天数 9 不再映射到离",
     '1: "坎", 3: "震", 5: "艮", 7: "兑", 9: "离"}',
     '1: "坎", 3: "震", 5: "艮", 7: "兑", 9: "坎"}'),
    (GE, "援阴阳：不在表内的数也硬套援阳",
     "        else:\n            out[\"name\"], out[\"gua\"] = \"\", \"\"\n    else:\n        out[\"tian_weak\"] = False",
     "        else:\n            out[\"name\"], out[\"gua\"] = \"援阳\", \"离\"\n    else:\n        out[\"tian_weak\"] = False"),
    (GE, "命无阴阳：阳月令男命阳不足不再判凶",
     "    if g == \"male\" and yang_month and tian_shu < TIAN_ZHENG:",
     "    if False:"),
    (GE, "冲突登记在单方时也报",
     "    if len(hits) < 2:\n        return ()",
     "    if not hits:\n        return ()"),
    (GE, "REFUSED 登记被清空",
     "REFUSED: tuple[tuple[str, str, str], ...] = (",
     "REFUSED: tuple[tuple[str, str, str], ...] = (\n"
     "    (\"占位\", \"占位\", \"占位\"),)\n_UNUSED_REFUSED = ("),
    (GE, "REFUSED 丢失天数至弱的基线存疑登记",
     "    (\"L38 首句「天数一十有五」的**基线数字**",
     "    (\"X38「占位"),
    # ── 本轮新增实现 ──
    (GE, "天数至弱上界写成 9（吞掉「不足」的下界）",
     'tian_band="4–8（不足一策）", di_band="不限", match="tian", lo_t=4, hi_t=8,',
     'tian_band="4–8（不足一策）", di_band="不限", match="tian", lo_t=4, hi_t=9,'),
    (GE, "天数至弱下界写成 1（凭空扩大区间）",
     'tian_band="4–8（不足一策）", di_band="不限", match="tian", lo_t=4, hi_t=8,',
     'tian_band="4–8（不足一策）", di_band="不限", match="tian", lo_t=1, hi_t=8,'),
    (GE, "三阳窗口缩小（漏掉立春）",
     "CHUNQI_JQ: frozenset[int] = frozenset({1, 2, 3})",
     "CHUNQI_JQ: frozenset[int] = frozenset({1, 2})"),
    (GE, "三阳窗口扩大（把雨水也算进去）",
     "CHUNQI_JQ: frozenset[int] = frozenset({1, 2, 3})",
     "CHUNQI_JQ: frozenset[int] = frozenset({1, 2, 3, 4})"),
    # ── 本轮实际踩到的两个坑 ──
    (GE, "solar_jq_index 不回溯（getJieQi 哨兵 255 导致整年失效）",
     "            jq = sxtwl.fromSolar(cur.year, cur.month, cur.day).getJieQi()\n"
     "            if jq is not None and jq != NO_JIEQI and 0 <= jq < len(JIE_QI_ORDER):\n"
     "                return jq\n"
     "            cur -= _td(days=1)",
     "            return sxtwl.fromSolar(y, m, d).getJieQi()\n"
     "            cur -= _td(days=1)"),
    (GE, "conflict 文案退回被全库证伪的「判语相反」",
     "且两条**同向、只严重度有别**：",
     "且两条**判语相反**："),
    (GJ, "to_dict 不再输出六项新增判定（新增功能全丢）",
     '                "matched": list(self.shu_xiong.matched),',
     '                "matched_off": list(self.shu_xiong.matched),'),
    (GJ, "build_guajie_from_result 误用 tian_shu（该函数内无此名）",
     "            _cq_note, _cq_ok = _jq(tian, _bd)",
     "            _cq_note, _cq_ok = _jq(tian_shu, _bd)"),
    (GJ, "天数至弱未接入 pattern 链",
     '        pattern = "天数至弱"',
     '        pattern = "天数不足"'),
    (GJ, "性别参数被忽略（退回三参）",
     "sx = judge_shu_xiong(tian_shu, di_shu, birth_month, gender)",
     "sx = judge_shu_xiong(tian_shu, di_shu, birth_month)"),
    (GJ, "以强伏弱的方向被改成与 L1073 相同（阳月令才凶）",
     '    if pattern == "以强伏弱":',
     '    if False:'),
    (GJ, "compose_guajie 不再把性别传给 build_guajie",
     "year_ganzhi=year_ganzhi, gender=_gender,",
     "year_ganzhi=year_ganzhi,"),
    # ── 死断四法的后天门控（2026-10-07）──
    (GJ, "死断四法去掉后天门控（先天段上爻又误触上极条）",
     '    is_hou_tian = (dayun_phase == "后天")',
     "    is_hou_tian = True"),
    (GJ, "_collect_si_duan 把当前段 phase 写死成后天（端到端失效）",
     '                dayun_phase = de.get("phase", "") or ""',
     '                dayun_phase = "后天"'),
    (GJ, "dayun_phase 形参默认值偷偷给成后天（漏传即按后天立断）",
     '    dayun_phase: str = "",                # 当前大运段 先天/后天（死断四法限定用）',
     '    dayun_phase: str = "后天",             # 当前大运段 先天/后天（死断四法限定用）'),
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


cache_dir = tempfile.mkdtemp(prefix="shuge_mutate_pycache_")
ENV = dict(os.environ)
ENV.update({
    "PYTHONPATH": "src",
    "PYTHONIOENCODING": "utf-8",
    "PYTHONPYCACHEPREFIX": cache_dir,
    "TONGSHU_ALLOW_ZIWEI_STUB": "1",
    "TONGSHU_AUTHORITY_CREDENTIALS": ("architecture-governance:schema-v1-arch-gov-2026;"
                                     "admission_registry:test-cred-hash"),
})

originals: dict[Path, str] = {}


def read(p: Path) -> str:
    raw = io.open(p, encoding="utf-8", newline="").read()
    return raw.replace("\r\n", "\n") if "\r\n" in raw else raw


def write(p: Path, text: str) -> None:
    nl = "\r\n" if "\r\n" in io.open(p, encoding="utf-8", newline="").read() else "\n"
    io.open(p, "w", encoding="utf-8", newline="").write(text.replace("\n", nl))


for p in {GE, GJ}:
    originals[p] = read(p)
base = {p: sha(t) for p, t in originals.items()}


def run() -> tuple[bool, str]:
    pr = subprocess.run(
        [sys.executable, "-m", "pytest", *TEST, "-q", "--no-header", "-p", "no:cacheprovider"],
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
ok_end, msg_end = run()
print(f"[还原 ] 应回到全绿 → {'OK  ' if ok_end else 'FAIL'}  {msg_end}")
if not ok_end:
    problems.append(f"还原后未回绿：{msg_end}")

if problems:
    print(f"\n❌ {len(problems)} 项异常：")
    for x in problems:
        print("   -", x)
    sys.exit(1)
print(f"\n✅ {len(MUTATIONS)} 条变异全部被守卫抓住，还原后基线一致")
