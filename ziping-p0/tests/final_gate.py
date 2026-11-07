# -*- coding: utf-8 -*-
"""最终全面核验: 全套件 + 矩阵 + 锚点 + 基线 + 全量 crash + 分布快照."""
import subprocess, sys, os, io, json, glob, collections
ROOT = r"D:\shuntian-ziping-p0"
PY = r"D:\shuntian\.venv\Scripts\python.exe"

SUITES = ['test_yuanjuan_matrix', 'test_criteria_anchors', 'test_special_pattern_golden',
          'test_bingyao_layer_golden', 'test_yongshen_geju_golden', 'test_xiang_shen_golden',
          'test_dayun_xiji_yongshen_golden', 'test_daymaster_root_class_golden',
          'test_qtbj_climate_golden', 'test_ancient_case_golden',
          'test_daymaster_root_relations_golden', 'test_daymaster_wang_xiang_golden']

out = io.open(os.path.join(ROOT, "p0_v2", "output", "FINAL_VERIFICATION.txt"), "w", encoding="utf-8")
out.write("八字引擎 最终核验报告\n")
out.write("=" * 74 + "\n")

fails = []
out.write("\n[1] 黄金套件\n")
for s in SUITES:
    r = subprocess.run([PY, "-X", "utf8", os.path.join(ROOT, "tests", s + ".py")],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=ROOT)
    ok = (r.returncode == 0)
    if not ok:
        fails.append(s)
    note = ""
    for ln in (r.stdout or "").split('\n'):
        if '矩阵结果' in ln or 'TOTAL' in ln or '结果:' in ln or 'FAILS' in ln:
            note = ln.strip()[:70]
    out.write("  %-34s %s  %s\n" % (s, "PASS" if ok else "FAIL", note))

out.write("\n[2] 全量 2106 盘\n")
r = subprocess.run([PY, "-X", "utf8", os.path.join(ROOT, "p0_v2", "_verify_20261009", "run_all.py")],
                   capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=ROOT)
crash = "?"
for ln in (r.stdout or "").split('\n'):
    if 'Total crashes' in ln or 'Total cases' in ln:
        out.write("  %s\n" % ln.strip())
        if 'crashes' in ln:
            crash = ln.strip()
out.write("\n[3] 回归闸门(100盘基线)\n")
r = subprocess.run([PY, "-X", "utf8", os.path.join(ROOT, "tests", "regress_gate.py")],
                   capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=ROOT)
for ln in (r.stdout or "").split('\n')[:3]:
    if ln.strip():
        out.write("  %s\n" % ln.strip())
if r.returncode != 0:
    fails.append("regress_gate")

out.write("\n[4] 判据锚点(公理三)\n")
r = subprocess.run([PY, "-X", "utf8", os.path.join(ROOT, "tests", "test_criteria_anchors.py")],
                   capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=ROOT)
for ln in (r.stdout or "").split('\n'):
    if '引擎原典引用点' in ln or '结果:' in ln:
        out.write("  %s\n" % ln.strip())
if r.returncode != 0:
    fails.append("criteria_anchors")

out.write("\n[5] 分布快照\n")
rp = os.path.join(ROOT, "p0_v2", "output", "REGRESSION_LATEST.txt")
if os.path.exists(rp):
    for ln in open(rp, encoding='utf-8').read().split('\n'):
        if ln.startswith(('病机', 'primary', '格局', '形态', '大运')):
            out.write("  %s\n" % ln[:200])

out.write("\n" + "=" * 74 + "\n")
out.write("总判定: %s\n" % ("全部通过" if not fails else "失败项: %s" % fails))
out.write("=" * 74 + "\n")
out.close()
print("FAILS:", fails if fails else "NONE")
