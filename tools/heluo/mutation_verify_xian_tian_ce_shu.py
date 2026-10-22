"""变异验证：先天策数守卫是否真能抓住错误（2026-10-07）

每条变异都往源码注入一个已知错误，跑守卫测试，必须**红**。全绿即说明守卫是摆设。

两处工程约束（首版都踩过）：

1. ``PYTHONPYCACHEPREFIX`` 隔离字节码。否则「还原源文件」后若 mtime 落在
   同一秒、且变异前后**字节数相同**（如 ``(0, 0, 0, 0)``→``(9, 9, 9, 9)``），
   Python 会复用陈旧 ``.pyc``，让"还原后复跑"假红。首版正是这样被骗的。
2. 每条变异还原后校验内容哈希，确保真的回到初始字节。
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
SRC = ROOT / "src" / "tongshu" / "engines" / "heluo" / "xian_tian_ce_shu.py"
TEST = "tests/heluo/test_xian_tian_ce_shu_vs_original.py"

MUTATIONS: list[tuple[str, str, str]] = [
    ("采信原典讹字「九百」（20×900≠1800）",
     "c1 = da_shu * 100 + da_shu * 90 + da_shu * yao_no",
     "c1 = da_shu * 100 + da_shu * 900 + da_shu * yao_no"),
    ("巽数退回起例卷 L174 的 4",
     '"巽": 5}', '"巽": 4}'),
    ("第二段与第一段相乘而非累加",
     "sub = c1 + c2", "sub = c1 * c2"),
    ("元会运世不除万（12685 不取 2685）",
     "n = ce_shu % 10000", "n = ce_shu"),
    ("元会运世元/会对调",
     "return (n // 1000, (n // 100) % 10, (n // 10) % 10, n % 10)",
     "return ((n // 100) % 10, n // 1000, (n // 10) % 10, n % 10)"),
    ("末段漏加动爻数",
     "tail = up_num + low_num + yao_no", "tail = up_num + low_num"),
    ("末段漏加祖数",
     "with_zu = sub + zu_shu", "with_zu = sub"),
    ("上体卦动偷偷给数（首版算出 11436）",
     'return _refuse(\n        gua, moving_yao, zu_shu, "上体", steps,',
     'return CeShuResult(gua, moving_yao, zu_shu, "上体", 11436, (1, 1, 4, 3), tuple(steps), "")\n'
     '    _dead = (\n        gua, moving_yao, zu_shu, "上体", steps,'),
    ("给未确证卦数填洛书序默认值",
     "up_num = BAGUA_NUM_CONFIRMED.get(upper)",
     "up_num = BAGUA_NUM_LUOSHU_REFERENCE.get(upper)"),
    ("下卦动函数越界受理上体动爻",
     "if moving_yao >= 3:", "if False:"),
    ("拒算时不归零元会运世",
     "ce_shu=0, yuan_hui_yun_shi=(0, 0, 0, 0), steps=tuple(steps), caveat=caveat,",
     "ce_shu=0, yuan_hui_yun_shi=(9, 9, 9, 9), steps=tuple(steps), caveat=caveat,"),
    ("拒算时不置 refused",
     "return self.ce_shu == 0", "return True"),
    ("歧义登记抹掉具体数字",
     '"上体卦动例（中孚 L1801）首段分解式得 11520，与原典自述 11712 不符，"',
     '"上体卦动例（中孚 L1801）首段分解式有误，与原典不符，"'),
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


original = io.open(SRC, encoding="utf-8", newline="").read()
base_sha = sha(original)
# ⚠ 2026-10-22 修：此处原有一行
#     `assert "\r\n" not in original, "源码为 LF，无需 CRLF 转换"`
#   ——那是**行尾前置检查**，源码后来被规范成 CRLF，断言遂失败，
#   整个套件在跑第一条变异**之前**就崩掉（静默失效：工具看起来
#   「有未抓住的变异」，实则一条都没跑）。现改为与其他套件一致的
#   「读时归一为 LF、写回时还原原行尾」：多行锚点在 CRLF 文件里
#   同样能命中，且还原后字节一致。
NL = "\r\n" if "\r\n" in original else "\n"
original_lf = original.replace("\r\n", "\n")

cache_dir = tempfile.mkdtemp(prefix="ce_shu_mutate_pycache_")
ENV = dict(os.environ)
ENV.update({
    "PYTHONPATH": "src",
    "PYTHONIOENCODING": "utf-8",
    "PYTHONPYCACHEPREFIX": cache_dir,     # 隔离 .pyc，杜绝陈旧字节码
    "TONGSHU_ALLOW_ZIWEI_STUB": "1",
    "TONGSHU_AUTHORITY_CREDENTIALS": ("architecture-governance:schema-v1-arch-gov-2026;"
                                     "admission_registry:test-cred-hash"),
})


def run_tests() -> tuple[bool, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", TEST, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8",
    )
    tail = [ln for ln in p.stdout.strip().splitlines() if ln.strip()]
    return p.returncode == 0, (tail[-1] if tail else p.stdout[-200:])


def write(text: str) -> None:
    io.open(SRC, "w", encoding="utf-8", newline="").write(text.replace("\n", NL))


print("=" * 74)
problems: list[str] = []

ok0, msg0 = run_tests()
print(f"[基线 ] 未变异应全绿 → {'OK  ' if ok0 else 'FAIL'}  {msg0}")
if not ok0:
    problems.append("基线未变异就不是绿的，变异验证无意义")

for name, old, new in MUTATIONS:
    if old not in original_lf:
        print(f"[SKIP ] {name} —— 锚点未命中")
        problems.append(f"{name}（锚点未命中）")
        continue
    write(original_lf.replace(old, new, 1))
    try:
        green, msg = run_tests()
    finally:
        write(original_lf)
    if sha(io.open(SRC, encoding="utf-8", newline="").read()) != base_sha:
        problems.append(f"{name}（还原失败，源文件已损坏）")
        print(f"[BROKEN] {name} —— 还原失败！")
        continue
    caught = not green
    print(f"[{'CAUGHT' if caught else 'MISSED'}] {name}"
          + ("" if caught else f"   ← 变异存活！{msg}"))
    if not caught:
        problems.append(f"{name}（变异存活）")

print("=" * 74)
ok_end, msg_end = run_tests()
print(f"[还原 ] 应回到全绿 → {'OK  ' if ok_end else 'FAIL'}  {msg_end}")
if not ok_end:
    problems.append(f"还原后未回绿：{msg_end}")
print(f"字节码隔离目录：{cache_dir}")

if problems:
    print(f"\n❌ {len(problems)} 项异常：")
    for p_ in problems:
        print("   -", p_)
    sys.exit(1)
print(f"\n✅ {len(MUTATIONS)} 条变异全部被守卫抓住，还原后基线一致")
