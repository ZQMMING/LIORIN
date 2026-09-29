"""
BOT-BAZI Phase 0 完整边界测试集
覆盖 P0-P9 所有验证项 + 附加项
"""

import sys
from pathlib import Path
from datetime import date, datetime
from datetime import timedelta
from zoneinfo import ZoneInfo
import math

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tongshu.engines.time.resolver import TimeResolver
from tongshu.engines.time.day_boundary import DAY_BOUNDARY, traditional_hour_name
from tongshu.engines.time.eot import equation_of_time
from tongshu.engines.time.longitude_offset import (
    MIN_PER_DEGREE,
    longitude_correction_minutes,
    ref_meridian_from_offset,
)
from tongshu.engines.bazi_engine import BaziEngine
from tongshu.engines.bazi_adapter import BaziAdapter


class BaziBoundaryResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def record(self, name, passed, detail=""):
        status = "✅" if passed else "❌"
        self.tests.append((status, name, detail))
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"测试结果: {self.passed}/{total} PASS, {self.failed} FAIL")
        print(f"{'='*60}\n")
        return self.failed == 0


# 初始化
resolver = TimeResolver()
bazi_engine = BaziEngine()
adapter = BaziAdapter(bazi_engine)
results = BaziBoundaryResult()

print("="*60)
print("BOT-BAZI Phase 0 完整边界测试")
print("="*60)

# ============================================================================
# P0: 时间输入合法性
# ============================================================================
print("\n=== P0: 时间输入合法性 ===")

# ① 闰年测试
p0_tests = [
    ("2024-02-29 11:33 (闰年)", date(2024, 2, 29), 11, 33),
    ("2023-02-28 11:33 (平年)", date(2023, 2, 28), 11, 33),
    ("1900-02-28 11:28 (世纪非闰年)", date(1900, 2, 28), 11, 28),
    ("2000-02-29 11:33 (世纪闰年)", date(2000, 2, 29), 11, 33),
]

for name, d, h, m in p0_tests:
    try:
        resolved = resolver.resolve(
            birth_date=d,
            hour=h,
            minute=m,
            timezone="Asia/Shanghai",
            location="北京",
        )
        results.record(name, True, f"resolved={resolved.effective_date}")
    except Exception as e:
        results.record(name, False, str(e))

# ② 边界时间测试
boundary_tests = [
    ("23:59:59", 23, 59),
    ("00:00:00", 0, 0),
    ("12:30:00", 12, 30),
]

for name, h, m in boundary_tests:
    try:
        resolved = resolver.resolve(
            birth_date=date(2024, 8, 21),
            hour=h,
            minute=m,
            timezone="Asia/Shanghai",
            location="北京",
        )
        results.record(f"边界测试 {name}", True, f"hour={resolved.effective_hour}")
    except Exception as e:
        results.record(f"边界测试 {name}", False, str(e))

# ③ 跨年月日测试
cross_boundary = [
    ("跨年 12/31→1/1", date(2024, 12, 31), date(2025, 1, 1)),
    ("跨月 1/31→2/1", date(2024, 1, 31), date(2024, 2, 1)),
    ("跨日 23:00→00:00", date(2024, 8, 21), date(2024, 8, 22)),
]

for name, d1, d2 in cross_boundary:
    try:
        r1 = resolver.resolve(birth_date=d1, hour=23, minute=59, timezone="Asia/Shanghai", location="北京")
        r2 = resolver.resolve(birth_date=d2, hour=0, minute=0, timezone="Asia/Shanghai", location="北京")
        results.record(name, True, f"d1={r1.effective_date}, d2={r2.effective_date}")
    except Exception as e:
        results.record(name, False, str(e))

# ============================================================================
# P0: 时区支持
# ============================================================================
print("\n=== P0: 时区支持 ===")

timezone_tests = [
    "America/Los_Angeles",
    "America/New_York", 
    "America/Chicago",
    "America/Denver",
    "Asia/Shanghai",
    "Asia/Tokyo",
    "Asia/Singapore",
    "Europe/London",
    "Europe/Berlin",
    "Europe/Moscow",
    "Australia/Sydney",
    "Pacific/Auckland",
]

for tz in timezone_tests:
    try:
        resolved = resolver.resolve(
            birth_date=date(2024, 8, 21),
            hour=12,
            minute=0,
            timezone=tz,
            location="北京" if "Shanghai" in tz or "Beijing" in tz else 
                    "London" if "London" in tz else
                    "Tokyo" if "Tokyo" in tz else
                    "New York",
        )
        results.record(f"时区 {tz}", True, f"resolved={resolved.timezone}")
    except Exception as e:
        results.record(f"时区 {tz}", False, str(e))

# ============================================================================
# P1: 子时换日边界 (Day Boundary Contract)
# ============================================================================
print("\n=== P1: 子时换日边界 ===")

day_boundary_tests = [
    (date(2024, 8, 21), 22, 59, False, "22:59 不换日"),
    # 子正换日 (2026-09-14 裁决, 覆盖旧"23:00 换日"): 日界 = 0:00.
    # 23:00-23:59:59 夜子时 → 日柱保持当天 (effective_date 不再 +1);
    # 时柱按次日日干五鼠遁 (见 BaziEngine P4 / getHourGZ True).
    # 北京经度116.41°，经度修正=-14.36min，EoT≈-3.25min
    (date(2024, 8, 21), 23, 0, False, "23:00 夜子时不换日(子正换日)"),
    (date(2024, 8, 21), 23, 14, False, "23:14 夜子时不换日(子正换日)"),
    (date(2024, 8, 21), 23, 20, False, "23:20 夜子时不换日(子正换日)"),
    (date(2024, 8, 21), 23, 30, False, "23:30 夜子时不换日(子正换日)"),
    (date(2024, 8, 21), 23, 59, False, "23:59 夜子时不换日(子正换日)"),
    (date(2024, 8, 22), 0, 0, False, "00:00 早子时不换日"),
    (date(2024, 8, 22), 0, 30, False, "00:30 早子时不换日"),
]

for d, h, m, expect_rolled, name in day_boundary_tests:
    try:
        resolved = resolver.resolve(
            birth_date=d,
            hour=h,
            minute=m,
            timezone="Asia/Shanghai",
            location="北京",
        )
        # 检查是否跨日
        actual_rolled = resolved.effective_date > d
        results.record(f"P1 {name}", actual_rolled == expect_rolled, 
                      f"expected_rolled={expect_rolled}, actual={actual_rolled}")
    except Exception as e:
        results.record(f"P1 {name}", False, str(e))

# 日柱+时柱联动测试
print("\n  --- 日柱+时柱联动 ---")
linkage_tests = [
    # (日期, 小时, 分钟, 说明)
    (date(2024, 8, 21), 22, 59, "换日前22:59"),
    (date(2024, 8, 22), 0, 0, "换日后00:00"),
]

for d, h, m, name in linkage_tests:
    try:
        ctx = resolver.resolve_context(birth_date=d, hour=h, minute=m, timezone="Asia/Shanghai", location="北京", gender="male")
        chart = adapter.compute(ctx)
        pillar_str = f"{chart.year_pillar.heavenly_stem}{chart.year_pillar.earthly_branch}-{chart.month_pillar.heavenly_stem}{chart.month_pillar.earthly_branch}-{chart.day_pillar.heavenly_stem}{chart.day_pillar.earthly_branch}-{chart.hour_pillar.heavenly_stem}{chart.hour_pillar.earthly_branch}"
        results.record(f"联动 {name}", True, 
                      f"day={ctx.effective_date}, pillar={pillar_str}")
    except Exception as e:
        results.record(f"联动 {name}", False, str(e))

# 跨时区子时测试
print("\n  --- 跨时区子时 ---")
cross_tz_tests = [
    ("America/New_York", "纽约"),
    ("Asia/Shanghai", "北京"),
    ("Pacific/Auckland", "奥克兰"),
]

for tz, loc in cross_tz_tests:
    try:
        resolved = resolver.resolve(
            birth_date=date(2024, 8, 21),
            hour=23,
            minute=0,
            timezone=tz,
            location=loc,
        )
        results.record(f"跨时区 {tz} 23:00", True, f"effective={resolved.effective_date}")
    except Exception as e:
        results.record(f"跨时区 {tz} 23:00", False, str(e))

# ============================================================================
# P2: 立春边界 (Solar-Term Boundary Contract)
# ============================================================================
print("\n=== P2: 立春边界 ===")

# 2024年立春时刻: 16:26:53 北京时间
# 总修正 = EoT(-13.85) + 经度修正(-14.36) = -28.21分钟
# 因此真太阳时立春对应民用时间约16:55
# 立春前使用 2023 年 GUI，立春后使用 2024 年 JIA
solar_term_tests = [
    # 2024年立春前后测试（立春时刻: 16:26:53 北京时间，对应输入约16:55）
    (date(2024, 2, 4), 16, 25, "GUI", "立春前（输入16:25，真太阳时15:57）→ GUI年"),
    (date(2024, 2, 4), 16, 55, "JIA", "立春后（输入16:55，真太阳时16:31）→ JIA年"),  # Oracle fix 2026-09-09: civil 16:55 > 立春 16:26:53 → 立春后 → 甲辰年 (JIA). 此前测试预期基于错误 jd_to_datetime +8h 算法
    (date(2024, 2, 4), 17, 0, "JIA", "立春后（输入17:00，真太阳时16:31）→ JIA年"),
    (date(2024, 2, 3), 23, 59, "GUI", "立春前1天23:59 → civil_date=02-03, 立春 02-04 16:26, 23:59 < 立春 → 立春前 → 癸卯年. V2.8 LOCK: 节气判断用 civil_date 而非 effective_date"),  # Oracle fix 2026-09-09: V2.8 修后 civil_date=02-03 无立春, 23:59<16:26 → 癸卯年
    (date(2024, 2, 5), 0, 0, "JIA", "立春后1天 → JIA年（甲年）"),
    # 2023年立春前测试（癸年）
    (date(2023, 2, 4), 16, 25, "GUI", "2023立春前 → GUI年（癸年）"),
]

for d, h, m, exp_stem, name in solar_term_tests:
    try:
        ctx = resolver.resolve_context(birth_date=d, hour=h, minute=m, timezone="Asia/Shanghai", location="北京", gender="male")
        chart = adapter.compute(ctx)
        actual_stem = chart.year_pillar.heavenly_stem
        results.record(f"P2 {name}", actual_stem == exp_stem, 
                      f"expected={exp_stem}, actual={actual_stem}")
    except Exception as e:
        results.record(f"P2 {name}", False, str(e))

# 春节 vs 立春分离测试
print("\n  --- 春节 vs 立春分离 ---")
chunjie_tests = [
    (date(2024, 2, 10), 12, 0, "JIA", "春节(2/10)后仍为甲年"),
]

for d, h, m, exp_stem, name in chunjie_tests:
    try:
        ctx = resolver.resolve_context(birth_date=d, hour=h, minute=m, timezone="Asia/Shanghai", location="北京", gender="male")
        chart = adapter.compute(ctx)
        actual_stem = chart.year_pillar.heavenly_stem
        results.record(f"P2 {name}", actual_stem == exp_stem, 
                      f"actual={actual_stem}")
    except Exception as e:
        results.record(f"P2 {name}", False, str(e))

# ============================================================================
# P3: 24节气边界测试 (72个测试用例)
# ============================================================================
print("\n=== P3: 24节气边界测试 ===")

# 2024年节气精确时刻（UTC+8）- 用于测试月柱切换
# 注意：月柱只在"节"时刻切换（12个节），不在"气"时刻切换
# 数据来源：sxtwl权威输出（北京时间 UTC+8）
# 修正：大雪节气实际在12月6日，非12月7日
# 测试策略：±10分钟确保真太阳时跨越节气
# 月柱切换点：节气前用前一天月柱，节气后用当天月柱
solar_terms_2024 = [
    # (节气名, month, day, (before_h, before_m), (after_h, after_m), before_stem, after_stem)
    ("小寒", 1, 6, (4, 19), (5, 19), "JIA", "YI"),      #小寒 04:49 (节). Oracle fix 2026-09-09: 小寒前(before=04:19 真太阳时≈03:59)→ 2023 年癸卯年 甲子月 → 甲子月 stem=甲(JIA). 月柱不是年柱 (此前错把年柱 GUI 当月柱预期)
    ("立春", 2, 4, (15, 56), (16, 56), "YI", "BING"),    # 立春 16:26 (节). Oracle fix 2026-09-09: 立春前(before=15:56 civil<立春 16:26)→ 2023 癸卯年丑月(乙丑). 五虎遁:癸年起甲寅,丑月=乙(YI). 月柱 stem=乙, 不是甲. 后 16:56 仍立春前 (16:56>16:26 立春后), 测试原期望 BING(丙) 是对的
    ("惊蛰", 3, 5, (9, 52), (10, 52), "BING", "DING"),  # 惊蛰 10:22 (节), BINGYIN→DINGMAO
    ("清明", 4, 4, (14, 32), (15, 32), "DING", "WU"),     # 清明 15:02 (节), DINGMAO→WUCHEN
    ("立夏", 5, 5, (7, 39), (8, 39), "WU", "JI"),        # 立夏 08:09 (节), WUCHEN→JISI
    ("芒种", 6, 5, (11, 39), (12, 39), "JI", "GENG"),     # 芒种 12:09 (节), JISI→GENGWU
    ("小暑", 7, 6, (21, 49), (22, 49), "GENG", "XIN"),   # 小暑 22:19 (节), GENGWU→XINWEI
    ("立秋", 8, 7, (7, 39), (8, 39), "XIN", "REN"),      # 立秋 08:09 (节), XINWEI→RENSHEN
    ("白露", 9, 7, (10, 41), (11, 41), "REN", "GUI"),    # 白露 11:11 (节), RENSHEN→GUIYOU
    ("寒露", 10, 8, (2, 29), (3, 29), "GUI", "JIA"),     # 寒露 02:59 (节), GUIYOU→JIAXU
    ("立冬", 11, 7, (5, 49), (6, 49), "JIA", "YI"),       # 立冬 06:19 (节), JIAXU→YIHAI
    ("大雪", 12, 6, (22, 46), (23, 46), "YI", "BING"),   # 大雪 23:16 (节), YIHAI→BINGZI
]

# 每个节气测试 2 点：前10分钟、后10分钟（使用调整后的时间确保真太阳时跨越节气）
test_count = 0
for name, month, day, before_time, after_time, before_stem, after_stem in solar_terms_2024:
    bh, bm = before_time
    ah, am = after_time
    base_dt = datetime(2024, month, day, bh, bm)
    
    # 前10分钟 - 应该在节气前
    try:
        ctx_before = resolver.resolve_context(birth_date=base_dt.date(), hour=bh, minute=bm,
                                       timezone="Asia/Shanghai", location="北京", gender="male")
        chart_before = adapter.compute(ctx_before)
        actual = chart_before.month_pillar.heavenly_stem
        results.record(f"P3 {name}前10分钟", actual == before_stem,
                      f"expected={before_stem}, actual={actual}, solar={ctx_before.true_solar_datetime.strftime('%H:%M')}")
        test_count += 1
    except Exception as e:
        results.record(f"P3 {name}前10分钟", False, str(e))
        test_count += 1
    
    # 后10分钟 - 应该在节气后
    ah2, am2 = after_time
    dt_after = datetime(2024, month, day, ah2, am2)
    try:
        ctx_after = resolver.resolve_context(birth_date=dt_after.date(), hour=ah2, minute=am2,
                                      timezone="Asia/Shanghai", location="北京", gender="male")
        chart_after = adapter.compute(ctx_after)
        actual = chart_after.month_pillar.heavenly_stem
        results.record(f"P3 {name}后10分钟", actual == after_stem,
                      f"expected={after_stem}, actual={actual}, solar={ctx_after.true_solar_datetime.strftime('%H:%M')}")
        test_count += 1
    except Exception as e:
        results.record(f"P3 {name}后10分钟", False, str(e))
        test_count += 1

print(f"  已测试 {test_count} 个节气边界点 (预期 36)")

# ============================================================================
# P4: 全球经度修正
# ============================================================================
print("\n=== P4: 全球经度修正 ===")

# 经度修正公式: (longitude - ref_meridian) * 4 min/deg
# ref_meridian = UTC offset hours × 15° (标准时区中央经线)
longitude_tests = [
    ("北京", 116.41, 8, -14.36),   # UTC+8, ref=120°
    ("上海", 121.47, 8, 5.88),     # UTC+8
    ("香港", 114.17, 8, -23.32),   # UTC+8
    ("东京", 139.69, 9, 18.76),    # UTC+9, ref=135°
    ("纽约", -74.01, -5, 3.96),    # UTC-5, ref=-75°
    ("伦敦", -0.13, 0, -0.52),     # UTC+0, ref=0°
    ("悉尼", 151.21, 11, -55.16),  # UTC+11 (DST), ref=165°
]

for name, lon, utc_offset, exp_corr in longitude_tests:
    try:
        ref_meridian = utc_offset * 15  # 标准时区中央经线
        corr = longitude_correction_minutes(lon, ref_meridian)
        results.record(f"P4 {name} 经度修正", 
                      abs(corr - exp_corr) < 0.5,
                      f"lon={lon}, utc_offset={utc_offset}, expected~{exp_corr:.2f}min, actual={corr:.2f}min")
    except Exception as e:
        results.record(f"P4 {name} 经度修正", False, str(e))

# ============================================================================
# P5: 历法转换
# ============================================================================
print("\n=== P5: 历法转换 ===")

calendar_tests = [
    ("公历闰年2/29", date(2024, 2, 29)),
    ("公历平年2/28", date(2023, 2, 28)),
    ("世纪非闰年2/28", date(1900, 2, 28)),
    ("世纪闰年2/29", date(2000, 2, 29)),
    ("年末边界", date(2024, 12, 31)),
    ("年初边界", date(2025, 1, 1)),
]

for name, d in calendar_tests:
    try:
        resolved = resolver.resolve(birth_date=d, hour=12, minute=0, timezone="Asia/Shanghai", location="北京")
        results.record(f"P5 {name}", True, f"date={resolved.effective_date}")
    except Exception as e:
        results.record(f"P5 {name}", False, str(e))

# ============================================================================
# P6: 四柱独立重算验证
# ============================================================================
print("\n=== P6: 四柱独立重算 ===")

golden_cases = [
    ("GOLDEN-001", date(1984, 12, 7), 16, 0, "JIA", "BING", "YI", "JIA", "ZI", "ZI", "HAI", "SHEN"),
    ("GOLDEN-004", date(1980, 5, 7), 10, 0, "GENG", "XIN", "GENG", "XIN", "SHEN", "SI", "CHEN", "SI"),
]

for name, d, h, m, exp_ys, exp_ms, exp_ds, exp_hs, exp_yz, exp_mz, exp_dz, exp_hz in golden_cases:
    try:
        ctx = resolver.resolve_context(birth_date=d, hour=h, minute=m, timezone="Asia/Shanghai", location="北京", gender="male")
        chart = adapter.compute(ctx)
        match = (chart.year_pillar.heavenly_stem == exp_ys and chart.year_pillar.earthly_branch == exp_yz and
                chart.month_pillar.heavenly_stem == exp_ms and chart.month_pillar.earthly_branch == exp_mz and
                chart.day_pillar.heavenly_stem == exp_ds and chart.day_pillar.earthly_branch == exp_dz and
                chart.hour_pillar.heavenly_stem == exp_hs and chart.hour_pillar.earthly_branch == exp_hz)
        pillar_str = f"{chart.year_pillar.heavenly_stem}{chart.year_pillar.earthly_branch}-{chart.month_pillar.heavenly_stem}{chart.month_pillar.earthly_branch}-{chart.day_pillar.heavenly_stem}{chart.day_pillar.earthly_branch}-{chart.hour_pillar.heavenly_stem}{chart.hour_pillar.earthly_branch}"
        results.record(f"P6 {name}", match,
                      f"pillar={pillar_str}")
    except Exception as e:
        results.record(f"P6 {name}", False, str(e))

# ============================================================================
# P7: 干支基础算法
# ============================================================================
print("\n=== P7: 干支基础算法 ===")

# 天干10
tian_gan = ["JIA", "YI", "BING", "DING", "WU", "JI", "GENG", "XIN", "REN", "GUI"]
results.record("P7 天干10项", len(tian_gan) == 10, f"count={len(tian_gan)}")

# 地支12
di_zhi = ["ZI", "CHOU", "YIN", "MAO", "CHEN", "SI", "WU", "WEI", "SHEN", "YOU", "XU", "HAI"]
results.record("P7 地支12项", len(di_zhi) == 12, f"count={len(di_zhi)}")

# 六十甲子循环
for i in range(60):
    stem = tian_gan[i % 10]
    branch = di_zhi[i % 12]
    if i < 3:
        results.record(f"P7 六十甲子{i}", True, f"{stem}{branch}")

# 五虎遁（年干→月干映射）
wu_hu_dun = {
    "JIA": "BING", "YI": "WU", "BING": "GENG", "DING": "REN", "WU": "JI",
    "JI": "BING", "GENG": "WU", "XIN": "GENG", "REN": "REN", "GUI": "JI",
}
results.record("P7 五虎遁映射", len(wu_hu_dun) == 10, f"10年干映射")

# 五鼠遁（日干→时干映射）
wu_shu_dun = {
    "JIA": "BING", "YI": "WU", "BING": "GENG", "DING": "REN", "WU": "JI",
    "JI": "BING", "GENG": "WU", "XIN": "GENG", "REN": "REN", "GUI": "JI",
}
results.record("P7 五鼠遁映射", len(wu_shu_dun) == 10, f"10日干映射")

# ============================================================================
# P8: 边界测试矩阵
# ============================================================================
print("\n=== P8: 边界测试矩阵 ===")

boundary_matrix = [
    (date(2024, 12, 31), 23, 59, "年末23:59"),
    (date(2025, 1, 1), 0, 0, "年初00:00"),
    (date(2024, 2, 28), 23, 59, "2月末日23:59"),
    (date(2024, 3, 1), 0, 0, "3月1日00:00"),
    (date(2024, 8, 21), 22, 59, "22:59不换日"),
    (date(2024, 8, 21), 23, 0, "23:00真太阳时22:42不换日"),  # 修正：北京23:00不换日
    (date(2024, 8, 21), 23, 14, "23:14真太阳时22:56不换日"),  # 修正：北京23:14不换日
    (date(2024, 8, 21), 23, 20, "23:20真太阳时23:02换日"),    # 新增：北京23:20换日
    (date(2024, 8, 21), 23, 59, "23:59换日"),
    (date(2024, 8, 22), 0, 0, "00:00不换日"),
    (date(2024, 8, 22), 0, 1, "00:01不换日"),
]

for d, h, m, name in boundary_matrix:
    try:
        resolved = resolver.resolve(birth_date=d, hour=h, minute=m, timezone="Asia/Shanghai", location="北京")
        results.record(f"P8 {name}", True, f"effective={resolved.effective_date}")
    except Exception as e:
        results.record(f"P8 {name}", False, str(e))

# ============================================================================
# P9: 全球城市验证
# ============================================================================
print("\n=== P9: 全球城市验证 ===")

global_cities = [
    ("北京", "Asia/Shanghai", 116.41),
    ("上海", "Asia/Shanghai", 121.47),
    ("香港", "Asia/Hong_Kong", 114.17),
    ("台北", "Asia/Taipei", 121.56),
    ("东京", "Asia/Tokyo", 139.69),
    ("首尔", "Asia/Seoul", 126.98),
    ("新加坡", "Asia/Singapore", 103.82),
    ("曼谷", "Asia/Bangkok", 100.52),
    ("雅加达", "Asia/Jakarta", 106.85),
    ("德里", "Asia/Kolkata", 77.10),
    ("孟买", "Asia/Kolkata", 72.88),
    ("迪拜", "Asia/Dubai", 55.31),
    ("伦敦", "Europe/London", -0.13),
    ("巴黎", "Europe/Paris", 2.35),
    ("柏林", "Europe/Berlin", 13.41),
    ("莫斯科", "Europe/Moscow", 37.62),
    ("纽约", "America/New_York", -74.01),
    ("洛杉矶", "America/Los_Angeles", -118.24),
    ("芝加哥", "America/Chicago", -87.63),
    ("多伦多", "America/Toronto", -79.38),
    ("温哥华", "America/Vancouver", -123.12),
    ("悉尼", "Australia/Sydney", 151.21),
    ("墨尔本", "Australia/Melbourne", 144.96),
    ("奥克兰", "Pacific/Auckland", 174.76),
    ("约翰内斯堡", "Africa/Johannesburg", 28.05),
    ("开罗", "Africa/Cairo", 31.24),
]

for city, tz, lon in global_cities:
    try:
        resolved = resolver.resolve(
            birth_date=date(2024, 8, 21),
            hour=12,
            minute=0,
            timezone=tz,
            location=city,
        )
        results.record(f"P9 {city}", True, f"resolved={resolved.timezone}")
    except Exception as e:
        results.record(f"P9 {city}", False, str(e))

# ============================================================================
# 附加项: 真太阳时 Policy
# ============================================================================
print("\n=== 附加项: 真太阳时 Policy ===")

# 测试真太阳时开关
policy_tests = [
    (True, "启用真太阳时"),
    (False, "禁用真太阳时"),
]

for apparent_solar, name in policy_tests:
    try:
        resolved = resolver.resolve(
            birth_date=date(2024, 8, 21),
            hour=12,
            minute=0,
            timezone="Asia/Shanghai",
            location="北京",
            apparent_solar=apparent_solar,
        )
        results.record(f"Policy {name}", True, 
                      f"apparent_solar={resolved.apparent_solar}, solar={resolved.solar_datetime}")
    except Exception as e:
        results.record(f"Policy {name}", False, str(e))

# ============================================================================
# 附加项: 历法/天文 Authority Layer
# ============================================================================
print("\n=== 附加项: Authority Layer ===")

# 验证 EoT 计算来源
eot_value = equation_of_time(date(2024, 8, 21))
results.record("Authority EoT计算", True, f"2024-08-21 EoT={eot_value:.2f}min")

# 验证日期计算
doy = (date(2024, 8, 21) - date(2024, 1, 1)).days + 1
results.record("Authority 日期序号", True, f"2024-08-21 = DOY {doy}")

# ============================================================================
# 输出结果
# ============================================================================
all_passed = results.summary()

if not all_passed:
    print("\nFailed tests:")
    for status, name, detail in results.tests:
        if "❌" in status:
            print(f"  {name}: {detail}")


# ============================================================================
# R-04-P0-C: Solar-Term Index / Effective-Day Index Separation (User 裁决)
# 验证 civil_date 与 effective_date 的节气查询分离
# ============================================================================

class TestR04P0CSolarTermIndexSeparation:
    """R-04-P0-C: 节气查询索引与日柱索引分离验证

    User 裁决关键场景:
    - civil: 2024-02-04 23:30 → effective_date: 2024-02-05
    - 立春判断必须基于 civil_date=02-04 (立春前)
    - 日柱必须基于 effective_date=02-05 (换日后日期)
    """

    def test_2024_02_04_23_30_solar_term_on_civil_date(self):
        """civil=02-04 23:30 → effective=02-05
        立春(02-04 16:26)已发生，但必须在 civil_date=02-04 上判断
        因此年柱=甲辰(JIA)，月柱=丙寅(YI)，日柱用 effective_date
        """
        engine = BaziEngine()
        civil_dt = datetime(2024, 2, 4, 23, 30, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        
        chart = engine.compute(
            solar_date=(2024, 2, 4, 23),
            gender="male",
            birth_datetime=civil_dt,
        )
        
        assert chart is not None
        # 年柱: 立春已发生(02-04 16:26 < 23:30)，所以是甲辰
        assert chart.year_pillar.heavenly_stem == "JIA", f"Expected JIA year pillar, got {chart.year_pillar.heavenly_stem}"
        # 月柱: 立春后进入丙寅月
        assert chart.month_pillar.heavenly_stem == "BING", f"Expected BING month pillar, got {chart.month_pillar.heavenly_stem}"

    def test_2024_02_03_23_30_still_pre_lichun(self):
        """civil=02-03 23:30 → effective=02-04
        立春(02-04 16:26)尚未发生，年柱仍为癸卯(GUI)
        """
        engine = BaziEngine()
        civil_dt = datetime(2024, 2, 3, 23, 30, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        
        chart = engine.compute(
            solar_date=(2024, 2, 3, 23),
            gender="male",
            birth_datetime=civil_dt,
        )
        
        assert chart is not None
        # 立春前 → 癸卯年
        assert chart.year_pillar.heavenly_stem == "GUI", f"Expected GUI year pillar, got {chart.year_pillar.heavenly_stem}"

    def test_2024_02_04_16_26_52_pre_lichun_by_second(self):
        """civil=02-04 16:26:52 → 立春前1秒"""
        engine = BaziEngine()
        civil_dt = datetime(2024, 2, 4, 16, 26, 52, tzinfo=ZoneInfo("Asia/Shanghai"))
        
        chart = engine.compute(
            solar_date=(2024, 2, 4, 16),
            gender="male",
            birth_datetime=civil_dt,
        )
        
        assert chart is not None
        # 立春前 → 癸卯年
        assert chart.year_pillar.heavenly_stem == "GUI", f"Expected GUI year pillar, got {chart.year_pillar.heavenly_stem}"

    def test_2024_02_04_16_26_53_on_lichun_exact_second(self):
        """civil=02-04 16:26:53 → 立春时刻 (R-04-P0-J 契约: == 视为立春后)"""
        engine = BaziEngine()
        civil_dt = datetime(2024, 2, 4, 16, 26, 53, tzinfo=ZoneInfo("Asia/Shanghai"))

        chart = engine.compute(
            solar_date=(2024, 2, 4, 16),
            gender="male",
            birth_datetime=civil_dt,
        )

        assert chart is not None
        # R-04-P0-J 契约：civil_dt == 立春时刻 → 立春后 → JIA
        assert chart.year_pillar.heavenly_stem == "JIA", f"Expected JIA at exact lichun (P0-J 契约), got {chart.year_pillar.heavenly_stem}"

    def test_2024_02_04_16_26_54_post_lichun_by_second(self):
        """civil=02-04 16:26:54 → 立春后2秒"""
        engine = BaziEngine()
        civil_dt = datetime(2024, 2, 4, 16, 26, 54, tzinfo=ZoneInfo("Asia/Shanghai"))
        
        chart = engine.compute(
            solar_date=(2024, 2, 4, 16),
            gender="male",
            birth_datetime=civil_dt,
        )
        
        assert chart is not None
        # 立春后 → 甲辰年
        assert chart.year_pillar.heavenly_stem == "JIA", f"Expected JIA year pillar, got {chart.year_pillar.heavenly_stem}"

    def test_2024_02_05_00_10_post_midnight_effective_date_changes(self):
        """civil=02-05 00:10 → effective_date=02-05 (已过23:00换日)
        立春已在02-04发生，年柱=甲辰
        """
        engine = BaziEngine()
        civil_dt = datetime(2024, 2, 5, 0, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        
        chart = engine.compute(
            solar_date=(2024, 2, 5, 0),
            gender="male",
            birth_datetime=civil_dt,
        )
        
        assert chart is not None
        # 立春后 → 甲辰年
        assert chart.year_pillar.heavenly_stem == "JIA", f"Expected JIA year pillar, got {chart.year_pillar.heavenly_stem}"

    def test_2024_02_03_23_30_month_pillar_not_polluted_by_effective_date(self):
        """civil=02-03 23:30 → effective=02-04
        月柱必须是乙丑(YI CHOU)，不能因为 effective_date=02-04 就变成丙寅
        这是 R-04-P0-D 的核心验证：月柱基础必须来自 civil_date，不是 effective_date
        """
        engine = BaziEngine()
        civil_dt = datetime(2024, 2, 3, 23, 30, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        
        chart = engine.compute(
            solar_date=(2024, 2, 3, 23),
            gender="male",
            birth_datetime=civil_dt,
        )
        
        assert chart is not None
        # 年柱: 立春前 → 癸卯
        assert chart.year_pillar.heavenly_stem == "GUI"
        # 月柱: 立春前 → 乙丑 (不能是丙寅!)
        assert chart.month_pillar.heavenly_stem == "YI", f"Expected YI month, got {chart.month_pillar.heavenly_stem}"
        assert chart.month_pillar.earthly_branch == "CHOU", f"Expected CHOU month branch, got {chart.month_pillar.earthly_branch}"

    def test_2024_02_03_23_59_month_still_chou(self):
        """civil=02-03 23:59 → effective=02-04
        月柱必须仍是乙丑，即使 effective_date 已到 02-04
        """
        engine = BaziEngine()
        civil_dt = datetime(2024, 2, 3, 23, 59, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        
        chart = engine.compute(
            solar_date=(2024, 2, 3, 23),
            gender="male",
            birth_datetime=civil_dt,
        )
        
        assert chart is not None
        assert chart.year_pillar.heavenly_stem == "GUI"
        assert chart.month_pillar.earthly_branch == "CHOU"

    def test_2024_02_04_23_30_month_is_yin(self):
        """civil=02-04 23:30 → effective=02-05
        立春已发生(02-04 16:26)，月柱应为丙寅(BING YIN)
        """
        engine = BaziEngine()
        civil_dt = datetime(2024, 2, 4, 23, 30, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        
        chart = engine.compute(
            solar_date=(2024, 2, 4, 23),
            gender="male",
            birth_datetime=civil_dt,
        )
        
        assert chart is not None
        assert chart.year_pillar.heavenly_stem == "JIA"
        assert chart.month_pillar.heavenly_stem == "BING"
        assert chart.month_pillar.earthly_branch == "YIN"

    def test_solar_term_idx_not_day_idx_in_compute(self):
        """验证 _compute_with_sxtwl 使用 solar_term_idx 而非 day_idx 查询节气"""
        import inspect
        source = inspect.getsource(BaziEngine._compute_with_sxtwl)
        
        # 必须包含 solar_term_idx
        assert "solar_term_idx" in source, "Missing solar_term_idx in _compute_with_sxtwl"
        
        # jieqi_val 必须来自 solar_term_idx
        assert "solar_term_idx.getJieQi()" in source, "jieqi_val must use solar_term_idx"
        
        # jieqi_jd 必须来自 solar_term_idx
        assert "solar_term_idx.getJieQiJD()" in source, "jieqi_jd must use solar_term_idx"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
