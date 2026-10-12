#!/usr/bin/env python3
"""紫微斗数 Production Runtime Trace (严格版)

约束:
- 不使用 STUB, 必须走 iztro 生产路径
- 真太阳时做 differential test (跨时辰边界案例)
- Natal Chart 与 Temporal Mutation Probe 分离
- 明确标注各层数据来源

输出: ZIWEI_PROFILE_V0 (IZTRO_CORE + SHUNTIAN_ADAPTER)
"""
import os, sys, json
from pathlib import Path

# ── 路径设置 ─────────────────────────────────────────────
for p in ['C:/Users/wisdom/wisdom/src', 'D:/today/backend/src']:
    if Path(p).exists():
        sys.path.insert(0, p)

# ⚠️ 不设 STUB - 必须走生产路径
if os.environ.get('TONGSHU_ALLOW_ZIWEI_STUB') == '1':
    del os.environ['TONGSHU_ALLOW_ZIWEI_STUB']

from tongshu.engines.ziwei_engine import ZiweiEngine, GAN_SIHUA, time_index_from_hour

engine = ZiweiEngine()

# ── 启动确认 ─────────────────────────────────────────────
print("=" * 70)
print("紫微 Production Runtime Trace")
print("=" * 70)
print(f"\nIZTRO_AVAILABLE = {engine._iztro_available}")
print(f"STUB_USED = False (production path enforced)")
assert engine._iztro_available, "iztro not available - cannot proceed"

# ── 固定案例 ─────────────────────────────────────────────
LUNAR_NATAL = (1893, 11, 19)
HOUR_NATAL = 6          # 辰时
GENDER = 'male'
LONGITUDE_NATAL = 112.9  # 湘潭
SOLAR_NATAL = (1893, 12, 26)

print(f"\n【Natal Case】")
print(f"  农历: {LUNAR_NATAL}, 阳历: {SOLAR_NATAL}")
print(f"  时辰: {HOUR_NATAL}h, 性别: {GENDER}")
print(f"  经度: {LONGITUDE_NATAL}°E")

# ════════════════════════════════════════════════════════
# PART 1: Natal Chart (本命盘)
# ════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print("PART 1: NATAL CHART (本命盘)")
print("=" * 70)

# 1.1 时辰索引
ti_natal = time_index_from_hour(HOUR_NATAL)
print(f"\n1.1 时辰索引 (生产路径)")
print(f"  hour={HOUR_NATAL} → index={ti_natal} (辰时)")
print(f"  来源: ziwei_engine.py time_index_from_hour()")

# 1.2 真太阳时校正 - differential test
ti_corrected = engine.corrected_hour_index(HOUR_NATAL, LONGITUDE_NATAL, SOLAR_NATAL)
print(f"\n1.2 真太阳时校正 (differential)")
print(f"  原始时辰 index: {ti_natal}")
print(f"  真太阳时 index: {ti_corrected}")
if ti_corrected != ti_natal:
    print(f"  ⚠️ 真太阳时跨越时辰边界! 排盘将使用 index={ti_corrected}")
else:
    print(f"  → 无跨越，排盘使用原始时辰 index={ti_natal}")

# 1.3 生产排盘
chart = engine.compute(LUNAR_NATAL, HOUR_NATAL, GENDER)
full = engine.full_chart(LUNAR_NATAL, HOUR_NATAL, GENDER)

print(f"\n1.3 命盘定位 (iztro core)")
print(f"  命宫地支: {full['soulPalaceBranch']}")
print(f"  身宫地支: {full['bodyPalaceBranch']}")
print(f"  五行局: {full['fiveElementsClass']}")
print(f"  来源: iztro byLunar().earthlyBranchOfSoulPalace/BodyPalace/fiveElementsClass")

print(f"\n1.4 十四主星分布")
STARS_14 = {'紫微','天府','太阳','武曲','天同','廉贞','太阴','贪狼',
            '巨门','天相','天梁','七杀','破军','天机'}
ZW_ORDER = ["命宫","兄弟","夫妻","子女","财帛","疾厄","迁移","仆役","官禄","田宅","福德","父母"]
for pname in ZW_ORDER:
    pdata = full['palaces'][pname]
    major = [s for s in pdata['major'] if s in STARS_14]
    minor = [s for s in pdata['minor'] if s not in STARS_14]
    star_str = f"{', '.join(major)}" + (f" +{minor}" if minor else "")
    print(f"  {pname}({pdata['branch']}): {star_str or '(空宫)'}")

# 1.5 生年四化
year_stem_idx = (LUNAR_NATAL[0] - 4) % 10
year_stems = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
year_stem = year_stems[year_stem_idx]
print(f"\n1.5 生年四化 (Shuntian GAN_SIHUA adapter)")
print(f"  生年干: {year_stem} (农历年{LUNAR_NATAL[0]})")
print(f"  四化表来源: ziwei_engine.py GAN_SIHUA (中州派/王亭之)")
print(f"  {year_stem}干: 禄={GAN_SIHUA[year_stem][0]}, 权={GAN_SIHUA[year_stem][1]}, "
      f"科={GAN_SIHUA[year_stem][2]}, 忌={GAN_SIHUA[year_stem][3]}")
sihua = engine.get_sihua_palaces(full, year_stem)
print(f"  落宫: 禄={sihua['hua_lu']}, 权={sihua['hua_quan']}, "
      f"科={sihua['hua_ke']}, 忌={sihua['hua_ji']}")

# 1.6 三方四正
print(f"\n1.6 三方四正 (Shuntian adapter)")
sfsz = engine.get_sanfang_sizheng(full, '命宫')
print(f"  本宫: {sfsz['ben']}({sfsz['ben_branch']})")
print(f"  对宫: {sfsz['dui']}({sfsz['dui_branch']})")
print(f"  三合: {sfsz['sanhe1']}({sfsz['sanhe1_branch']}), {sfsz['sanhe2']}({sfsz['sanhe2_branch']})")
print(f"  四方主星: {sfsz['all_major']}")

# 1.7 大限
print(f"\n1.7 大限系统 (iztro core)")
for pname in ZW_ORDER:
    pdata = full['palaces'][pname]
    dr = pdata['decadalRange']
    print(f"  {pname}({pdata['branch']}): {dr[0]}-{dr[1]}岁, 天干{pdata['decadalStem']}")

# 1.8 宫干自化
print(f"\n1.8 宫干自化 (Shuntian GAN_SIHUA adapter)")
for pname in ZW_ORDER[:6]:
    zihua = engine.palace_self_mutagen(full, pname)
    stem = full['palaces'][pname]['stem']
    if zihua:
        print(f"  {pname}({stem}干): 自化{zihua}")
    else:
        print(f"  {pname}({stem}干): 无自化")


# ════════════════════════════════════════════════════════
# PART 2: True Solar Time Boundary Test
# ════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print("PART 2: TRUE SOLAR TIME BOUNDARY TEST")
print("=" * 70)

# 选择接近时辰边界的案例来验证真太阳时是否跨界
# 案例A: 标准辰时(06:00) - 应该不变
# 案例B: 接近巳时边界(09:00) + 西经度(慢) → 可能跨入辰时
# 案例C: 接近巳时边界(09:00) + 东经度(快) → 可能保持在巳时

test_cases = [
    # (lunar_date, hour, longitude, solar_date, desc)
    ((1893, 11, 19), 6, 112.9, (1893, 12, 26), "湘潭06:00辰时"),
    ((1893, 11, 19), 9, 112.9, (1893, 12, 26), "湘潭09:00巳时"),
    ((1893, 11, 19), 9, 125.0, (1893, 12, 26), "东经125°09:00"),
    ((1893, 11, 19), 9, 108.0, (1893, 12, 26), "西经108°09:00"),
]

print(f"\n边界测试矩阵:")
print(f"{'案例':<20} {'原始h':>5} {'经度':>8} {'校正后':>6} {'跨界':>6} {'时辰变化'}")
print("-" * 60)
for lunar, hour, lng, solar, desc in test_cases:
    orig_ti = time_index_from_hour(hour)
    corr_ti = engine.corrected_hour_index(hour, lng, solar)
    crossed = "YES" if corr_ti != orig_ti else "no"
    change = f"{orig_ti}→{corr_ti}" if corr_ti != orig_ti else f"{orig_ti}(=)"
    print(f"  {desc:<18} {hour:>5} {lng:>7.1f}° {corr_ti:>6} {crossed:>6} {change}")

# 关键验证: 用跨界前后的参数分别排盘，对比命盘是否不同
print(f"\n关键验证: 边界案例A vs 边界案例B")
# 找一组经度差导致跨界的案例
lunar_t = (1893, 11, 19)
solar_t = (1893, 12, 26)

# 案例: 09:00 在108°E可能跨入辰时
hour_t = 9
ti_108 = engine.corrected_hour_index(hour_t, 108.0, solar_t)
ti_125 = engine.corrected_hour_index(hour_t, 125.0, solar_t)
print(f"  hour={hour_t}, 108°E → index={ti_108}")
print(f"  hour={hour_t}, 125°E → index={ti_125}")
if ti_108 != ti_125:
    print(f"  ✓ 经度差异导致时辰跨越!")
    chart_108 = engine.full_chart(lunar_t, ti_108, GENDER)
    chart_125 = engine.full_chart(lunar_t, ti_125, GENDER)
    ming_108 = chart_108['palaces']['命宫']['branch']
    ming_125 = chart_125['palaces']['命宫']['branch']
    print(f"  命宫(108°E): {ming_108}")
    print(f"  命宫(125°E): {ming_125}")
    if ming_108 != ming_125:
        print(f"  ✓ 真太阳时跨界改变了命盘!")
    else:
        print(f"  ⚠️ 命宫相同但需检查全盘差异")
else:
    print(f"  → 该日期/时辰组合下经度差异未导致跨时辰")


# ════════════════════════════════════════════════════════
# PART 3: Temporal Mutation Probe (独立于本命)
# ════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print("PART 3: TEMPORAL MUTATION PROBE (独立测试)")
print("=" * 70)
print(f"注: 以下时间不与本命案例(1893)混淆，仅测试 horoscope API")

# 3.1 流年
print(f"\n3.1 流年四化 (horoscope rule probe)")
yearly = engine.flow_years_mutagen([1893], LUNAR_NATAL, HOUR_NATAL, GENDER)
print(f"  1893年: {yearly.get(1893, [])}")
print(f"  来源: iztro astrolabe.horoscope('1893-6-15').yearly.mutagen")

# 3.2 流月 - 使用本命年份
print(f"\n3.2 流月四化 (horoscope rule probe)")
monthly_1893 = engine.flow_month_mutagen(1893, 1, LUNAR_NATAL, HOUR_NATAL, GENDER)
monthly_1893_6 = engine.flow_month_mutagen(1893, 6, LUNAR_NATAL, HOUR_NATAL, GENDER)
print(f"  1893年1月: {monthly_1893}")
print(f"  1893年6月: {monthly_1893_6}")
print(f"  来源: iztro astrolabe.horoscope('1893-M-15').monthly.mutagen")

# 3.3 流日
print(f"\n3.3 流日四化 (horoscope rule probe)")
daily = engine.flow_day_mutagen(1893, 11, 19, LUNAR_NATAL, HOUR_NATAL, GENDER)
print(f"  1893-11-19: {daily}")
print(f"  来源: iztro astrolabe.horoscope('1893-11-19').daily.mutagen")

# 3.4 四尺度对比
print(f"\n3.4 四尺度对比 (同一本命盘)")
print(f"  生年(癸干): {GAN_SIHUA['癸']}")
print(f"  大限(1893): {engine.flow_decadal_mutagen([1893], LUNAR_NATAL, HOUR_NATAL, GENDER).get(1893, [])}")
print(f"  流年(1893): {yearly.get(1893, [])}")
print(f"  流月(1893-01): {monthly_1893}")
print(f"  流日(1893-11-19): {daily}")


# ════════════════════════════════════════════════════════
# PART 4: ZIWEI_PROFILE_V0
# ════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print("PART 4: ZIWEI_PROFILE_V0 (Arbitration-defined)")
print("=" * 70)

print("""
┌─────────────────────────────────────────────────────────────────┐
│  ZIWEI_PROFILE_V0                                             │
│  (IZTRO_CORE + SHUNTIAN_ADAPTER)                              │
├─────────────────────────────────────────────────────────────────┤
│  CORE_CALCULATION                                             │
│    = iztro 2.6.0 (byLunar + horoscope)                        │
│                                                                 │
│  INPUT                                                        │
│    = Lunar date + hour + gender                               │
│                                                                 │
│  CALENDAR_POLICY                                              │
│    = lunar_python / iztro adapter                             │
│    = 闰月: 负月表示 (如-10=闰十月)                             │
│    = 子时: 0h=早子(index 0), 23h=晚子(index 12)               │
│                                                                 │
│  [IZTRO CORE - Black Box]                                     │
│    ├── Ming Palace (命宫)                                      │
│    ├── Shen Palace (身宫)                                      │
│    ├── Five Elements Bureau (五行局)                           │
│    ├── Major Stars (十四主星)                                  │
│    ├── Minor Stars (辅星/煞星)                                 │
│    ├── Decadal (大限)                                          │
│    └── Horoscope (流年/月/日)                                  │
│                                                                 │
│  [SHUNTIAN ADAPTER - Deterministic]                           │
│    ├── GAN_SIHUA = Zhongzhou/Wang Tingzhi declared table     │
│    │   (only this layer is explicitly declared as 中州派)      │
│    ├── Palace Self-Transformation (宫干自化)                   │
│    └── Sanfang Sizheng (三方四正: idx+6,+4,+8)                 │
│                                                                 │
│  [NOT PART OF DETERMINISTIC CORE]                             │
│    ✗ native_direction()  → 语义解释层，违反ea3574d             │
│    ✗ SIHUA_EFFECT (INCREASE/DECREASE) → 语义层                 │
│    ✗ score_topic() → 断事评分层                                 │
│    ✗ decadal_soul_effect() → 语义层                            │
│                                                                 │
│  [TRUE SOLAR TIME - Helper Only]                              │
│    corrected_hour_index() exists but is NOT called by          │
│    compute() by default. Must be explicitly used.              │
│    Requires boundary-crossing test case for evidence.          │
└─────────────────────────────────────────────────────────────────┘
""")

# ════════════════════════════════════════════════════════
# PART 5: Function Provenance
# ════════════════════════════════════════════════════════
print(f"{'='*70}")
print("PART 5: FUNCTION PROVENANCE")
print("=" * 70)

provenance = [
    ("time_index_from_hour()", "ziwei_engine.py:94-104", "Shuntian", "时辰→index"),
    ("corrected_hour_index()", "ziwei_engine.py:949-971", "Shuntian", "真太阳时校正(helper)"),
    ("_compute_via_iztro()", "ziwei_engine.py:239-317", "iztro core", "核心排盘"),
    ("full_chart()", "ziwei_engine.py:655-700", "iztro core", "完整命盘"),
    ("flow_decadal_mutagen()", "ziwei_engine.py:765-794", "iztro core", "大限四化"),
    ("flow_years_mutagen()", "ziwei_engine.py:319-356", "iztro core", "流年四化"),
    ("flow_month_mutagen()", "ziwei_engine.py:819-843", "iztro core", "流月四化"),
    ("flow_day_mutagen()", "ziwei_engine.py:845-867", "iztro core", "流日四化"),
    ("get_sihua_palaces()", "ziwei_engine.py:388-415", "Shuntian", "生年四化落宫"),
    ("palace_self_mutagen()", "ziwei_engine.py:695-720", "Shuntian", "宫干自化"),
    ("get_sanfang_sizheng()", "ziwei_engine.py:360-410", "Shuntian", "三方四正"),
]

print(f"\n{'函数':<30} {'行号':<25} {'层级':<12} {'说明'}")
print("-" * 90)
for name, loc, layer, desc in provenance:
    mark = " ❌" if "❌" in desc else ""
    print(f"{name:<30} {loc:<25} {layer:<12} {desc}{mark}")

print(f"\n{'='*70}")
print("Production Runtime Trace Complete")
print("=" * 70)
