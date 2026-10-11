# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""DTS 510 例实质对齐: 从 power_network.dimensions 取结构事实, 与原断 analysis 的喜/用/旺/衰 比对.
不改引擎, 不造综合裁决(封板), 只取已有结构事实做诊断.
对齐维度:
  A. 喜/用天干 → 引擎 yongyao.primary_medicine.wuxing 五行命中
  B. 身强/旺 → 引擎 SEASONAL.in_season=True 或 ROOT=HEAVY
  C. 身弱/衰 → 引擎 SEASONAL.out 或 ROOT=LIGHT/NONE
  D. 从/化 → 引擎 special_pattern.cong_type/zhuanwang
输出: 对齐率 + 不一致例(前30)
"""
import sys, json, re
sys.path.insert(0, '.')
from engines.production_entry import FrozenCanonicalBaziChart, production_entry

K = ('year', 'month', 'day', 'hour')
GAN2WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
def gp(bazi):
    t = re.split(r'[\s,，、]+', bazi.strip())
    if len(t) != 4: return None
    return {K[i]: [t[i][0], t[i][1]] for i in range(4)}

# 从 analysis 提取"喜X为用""取X""用X"里的天干X
def extract_yong_gan(ana):
    """提取原断里指明的用神天干(喜X/取X/用X/以X为用). 返回天干集合."""
    gans = set()
    # 喜X / 取X / 用X / 以X为用 / 必用X / 宜X
    for m in re.finditer(r'[喜取用以]\s*([甲乙丙丁戊己庚辛壬癸])', ana):
        gans.add(m.group(1))
    for m in re.finditer(r'以\s*([甲乙丙丁戊己庚辛壬癸])\s*为', ana):
        gans.add(m.group(1))
    return gans

rows = [json.loads(l) for l in open('p0_v2/case_audit/DTS_clean.jsonl', encoding='utf-8') if l.strip()]
total = len(rows)
align_yong = 0  # 用神五行命中
mismatch_yong = []
has_yong = 0    # 有明确用神天干的原断数

for r in rows:
    ana = r.get('analysis') or ''
    bazi = r.get('bazi', '')
    cid = r.get('case_id', '')
    p = gp(bazi)
    if not p: continue
    try:
        res = production_entry(FrozenCanonicalBaziChart(pillars=p))
    except Exception:
        continue
    zl = res.get('zhenglun') or {}
    yy = zl.get('yongyao') or {}
    pm = yy.get('primary_medicine') or {}
    eng_wx = pm.get('wuxing') if isinstance(pm, dict) else None
    
    yong_gans = extract_yong_gan(ana)
    if yong_gans:
        has_yong += 1
        exp_wx = set(GAN2WX[g] for g in yong_gans)
        if eng_wx and eng_wx in exp_wx:
            align_yong += 1
        else:
            mismatch_yong.append((cid, bazi, sorted(yong_gans), eng_wx, ana[:80].replace('\n',' ')))

print('=' * 60)
print(f"DTS 用神五行对齐: 有明确用神天干的原断={has_yong}/{total}")
print(f"  引擎用神五行命中: {align_yong}/{has_yong} = {align_yong*100//has_yong if has_yong else 0}%")
print(f"  不一致: {len(mismatch_yong)}")
print()
print("--- 不一致例(前30, cid | bazi | 原断用神天干 | 引擎用神五行 | ana截断) ---")
for m in mismatch_yong[:30]:
    print(' ', m)
