"""河洛理数冻结规则唯一入口（Module 8）

所有 Hermes / Codex / Claude 的算法实现必须通过此入口验证。
对齐 Architecture Freeze V1.0 §2.3 模块8 + §2.6 Golden Case。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .input import HeluoInput, prepare_heluo_input
from .numbers import (
    compute_tian_di_shu,
    TianDiShu,
    STEM_VALUES,
    BRANCH_VALUES,
    build_six_lines,
    TRIGRAM_ELEMENT,
    TRIGRAM_NATURE,
)
from .prenatal import determine_prenatal_hexagram, PrenatalHexagram
from .yuan_tang import find_yuantang, YuanTang
from .postnatal import compute_postnatal, PostnatalHexagram
from .temporal import compute_timeline, Timeline
from .timeline_yun import (
    compute_dayun_liyao,
    compute_liunian,
    compute_liuri,
    compute_liushi,
    compute_liuyue,
)


# 农历月 → 月令"节"（sxtwl 节气索引，奇数=节）
# 正月=立春(3)、二月=惊蛰(5)、三月=清明(7)、四月=立夏(9)、五月=芒种(11)、
# 六月=小暑(13)、七月=立秋(15)、八月=白露(17)、九月=寒露(19)、十月=立冬(21)、
# 十一月=大雪(23)、十二月=小寒(1)
_LUNAR_MONTH_JIE = {
    1: 3, 2: 5, 3: 7, 4: 9, 5: 11, 6: 13,
    7: 15, 8: 17, 9: 19, 10: 21, 11: 23, 12: 1,
}



# ============================================================================
# 纯卦元堂节气分支 + 至尊卦生月阴阳（《河洛理数真正算法确认书 V1》§2.1/§2.2）
# ============================================================================
_YANG_BRANCHES = {"子", "寅", "辰", "午", "申", "戌"}


def _birth_month_yang_from_bazi(bazi) -> bool | None:
    """出生月令（节气月）阴阳：月柱地支为阳支（子寅辰午申戌）→ True（阳月）。

    河洛体系以节气定月（原典"未得十月节气作九月论"），BaziEngine 月柱即节气月，
    故以月柱地支阴阳判生月阴阳（总集至尊卦：阳月=一三五七九十一月）。
    """
    if len(bazi) >= 2 and len(bazi[1]) == 2:
        return bazi[1][1] in _YANG_BRANCHES
    return None


def _solar_phase_for_date(birth_date: str) -> str | None:
    """出生公历日期 → 纯卦元堂半年相（原典 p051-052）。

    winter: 冬至后至夏至前（含冬至日、不含夏至日）→ 女乾/男坤自上而下
    summer: 夏至后至冬至前（含夏至日、不含冬至日）→ 女乾/男坤自下而上
    """
    from datetime import date as _date
    from datetime import timedelta
    try:
        import sxtwl
    except ImportError:
        return None
    try:
        y, m, d = (int(x) for x in birth_date.split("-")[:3])
    except (ValueError, AttributeError):
        return None
    bd = _date(y, m, d)

    def _find_jie(year: int, month: int, jq: int) -> _date:
        d0 = _date(year, month, 1)
        found = d0
        while d0.month == month:
            day = sxtwl.fromSolar(d0.year, d0.month, d0.day)
            if day.getJieQi() == jq:
                found = d0
            d0 += timedelta(days=1)
        return found

    dongzhi_prev = _find_jie(y - 1, 12, 0)   # 冬至 jq=0（上一年）
    dongzhi_cur = _find_jie(y, 12, 0)        # 冬至 jq=0（当年）
    xiazhi_cur = _find_jie(y, 6, 12)         # 夏至 jq=12
    # 冬至当日（12/21-22）起即入"冬至后至夏至前"（冬半年）
    if bd >= dongzhi_cur:
        return "winter"
    if dongzhi_prev <= bd < xiazhi_cur:
        return "winter"
    if xiazhi_cur <= bd < dongzhi_cur:
        return "summer"
    return None
_jie_cache: dict[int, dict[int, str]] = {}


def _jie_datetime_for_lunar_month(year: int, lunar_month: int) -> str | None:
    """返回农历 lunar_month 月"节"的精确时刻（公历 YYYY-MM-DD HH:MM）。

    一次遍历拿到该公历年的全部12个"节"并缓存，后续查表（避免逐月重复遍历）。
    用于流日卦节气对齐（《河洛理数》卷二下）。
    """
    global _jie_cache
    if year not in _jie_cache:
        _jie_cache[year] = _compute_year_jie(year)
    return _jie_cache[year].get(lunar_month)


def _compute_year_jie(year: int) -> dict[int, str]:
    """遍历公历 year-1~year+1，找齐 12 个"节"，按农历月 1-12 建映射。"""
    import sxtwl
    from datetime import date, timedelta
    result: dict[int, str] = {}
    best: dict[int, tuple] = {}
    d = date(year - 1, 1, 1)
    end = date(year + 1, 12, 31)
    while d <= end:
        day_obj = sxtwl.fromSolar(d.year, d.month, d.day)
        jq = day_obj.getJieQi()
        if jq in _LUNAR_MONTH_JIE.values():
            jd = day_obj.getJieQiJD()
            t = sxtwl.JD2DD(jd)
            if not (0 < t.Y <= 2200):
                d += timedelta(days=1)
                continue
            # 该节对应的农历月
            lm = next((m for m, idx in _LUNAR_MONTH_JIE.items() if idx == jq), None)
            if lm is None:
                d += timedelta(days=1)
                continue
            gap = abs(d.year - year)
            if lm not in best or gap < best[lm][0]:
                best[lm] = (gap, f"{t.Y:04d}-{t.M:02d}-{t.D:02d} {int(t.h):02d}:{int(t.m):02d}")
        d += timedelta(days=1)
    for lm, (_, dtstr) in best.items():
        result[lm] = dtstr
    return result
from .hexagram import analyze_hexagram, HexagramStructure
from .yi_interpreter import interpret_all_liunian
from .hua_gong import compute_huagong, HuaGongResult
from .jiehhou import get_seasonal_hexagram, get_current_jieqi_info


@dataclass(frozen=True)
class HeluoResult:
    """河洛计算完整结果"""
    input: HeluoInput
    numbers: TianDiShu
    prenatal: PrenatalHexagram
    yuantang: YuanTang
    postnatal: PostnatalHexagram
    timeline: Timeline | None
    structure: HexagramStructure | None
    hua_gong: HuaGongResult | None = None          # H6: 化工状态
    seasonal_hexagram: dict | None = None          # H11: 节候卦（出生日）
    guajie: dict | None = None                     # H8: 解卦层（原典判词，可选挂载）


class HeluoCanonical:
    """
    河洛理数计算器 — 冻结规则唯一入口。

    用法：
    >>> canonical = HeluoCanonical()
    >>> result = canonical.calculate(context)

    验证：
    >>> canonical.verify_golden_case("jixiaolan")
    True
    """

    # 纪晓岚 Golden Case（冻结）
    GOLDEN_CASES = {
        "jixiaolan": {
            "bazi": [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            "gender": "male",
            "birth_hour": "午",
            "birth_year": 1724,
            "era": "shang",  # (1724-1864)%180=40 <60 上元；无遇5故结果与 zhong 相同
            "expected": {
                "tian_shu": 22,
                "di_shu": 56,
                "tian_reduced": 2,      # 坤
                "di_reduced": 6,        # 乾
                "prenatal": "地天泰",
                "yuantang": "六四",
                "yuantang_index": 3,    # 0-indexed
                "postnatal": "天雷无妄",
            },
        },
    }

    def __init__(self, version: str = "v2.0"):
        self.version = version
        self._validate_frozen_version()

    def _validate_frozen_version(self) -> None:
        """验证冻结版本一致性"""
        # 当前冻结版本为 v2.0
        if self.version != "v2.0":
            raise ValueError(f"HeluoCanonical version must be v2.0, got {self.version!r}")

    def calculate(
        self,
        bazi: list[tuple[str, str]],
        gender: str,
        birth_hour: str,
        era: str = "zhong",
        birth_year: int | None = None,
        birth_date: str | None = None,
        true_solar_datetime: str | None = None,
        solar_phase: str | None = None,
    ) -> HeluoResult:
        """
        完整计算链：
        八字 → TianDiShu → PrenatalHexagram → YuanTang → PostnatalHexagram → Timeline → Structure

        每一步保存中间结果，供 CalculationSnapshot 使用。

        birth_year: 出生公历年份（可选）。用于流年卦推演（流年干支阴阳判定）。
                    未提供时从 bazi 年柱干支反推（60 甲子近似）。
        birth_date: 出生公历日期 ISO 格式（YYYY-MM-DD）。可选，用于 HeluoInput 落真实日期
                    （DISPUTE-HL-03），未提供时由 birth_year 派生，不再使用误导占位。
        true_solar_datetime: 真太阳时 ISO 格式。可选，默认取 birth_date。
        solar_phase: "winter"（冬至后至夏至前）/ "summer"（夏至后至冬至前）。
                      纯卦（女乾/男坤）元堂上下行向分支；未传且 birth_date 有效时自动推算。
        """
        # Step 1: 计算天数地数
        numbers = compute_tian_di_shu(bazi, gender)

        # Step 2: 确定先天卦
        year_gan = bazi[0][0]
        birth_year_yang = year_gan in "甲丙戊庚壬"
        prenatal = determine_prenatal_hexagram(
            numbers.tian_reduced,
            numbers.di_reduced,
            gender,
            birth_year_yang,
            era,
        )

        # Step 3: 构建六爻
        six_lines = build_six_lines(prenatal.upper_gua, prenatal.lower_gua)


        # Step 3.5: 纯卦节气分支 + 至尊卦生月阴阳（原典 p051-052 / 总集至尊卦）
        if solar_phase is None and birth_date:
            solar_phase = _solar_phase_for_date(birth_date)
        birth_month_yang = _birth_month_yang_from_bazi(bazi)

        # Step 4: 确定元堂
        yuantang = find_yuantang(
            six_lines=six_lines,
            birth_hour=birth_hour,
            gender=gender,
            xiantian_name=prenatal.hexagram_name,
            solar_phase=solar_phase,
        )

        # Step 5: 计算后天卦
        postnatal = compute_postnatal(
            six_lines=six_lines,
            yuantang_index=yuantang.yuantang_index,
            xiantian_name=prenatal.hexagram_name,
            birth_month_yang=birth_month_yang,
        )

        # Step 5.5: 后天卦元堂（复用先天元堂取法，用出生时辰）
        postnatal_yuantang = find_yuantang(
            six_lines=build_six_lines(postnatal.upper_gua, postnatal.lower_gua),
            birth_hour=birth_hour,
            gender=gender,
            xiantian_name=postnatal.hexagram_name,
            solar_phase=solar_phase,
        )

        # Step 6: 时间序列（大运爻位值运 + 流年卦 + 流月卦）
        timeline = self._build_timeline(
            prenatal, yuantang, postnatal, postnatal_yuantang, birth_year
        )

        # Step 7: 卦象结构分析
        structure = analyze_hexagram(postnatal.hexagram_name)

        # 构建 HeluoInput（DISPUTE-HL-03：落真实出生日期，不再用误导占位）
        from datetime import date
        if birth_date is None:
            yr = birth_year if birth_year is not None else 1984
            birth_date = f"{yr}-01-01"
        if true_solar_datetime is None:
            true_solar_datetime = birth_date + "T00:00:00"
        input_obj = HeluoInput(
            birth_date=birth_date,
            birth_time=birth_hour,
            gender=gender,
            location=None,  # type: ignore
            timezone="Asia/Shanghai",
            true_solar_datetime=true_solar_datetime,
            day_boundary="23:00",
        )

        # Step 8: H6 化工计算
        hua_gong = self._compute_huagong(
            prenatal, postnatal, birth_date, gender, birth_year
        )

        # Step 9: H11 节候卦（出生日所在节气）
        seasonal_hex = self._compute_seasonal_hexagram(birth_date)

        return HeluoResult(
            input=input_obj,
            numbers=numbers,
            prenatal=prenatal,
            yuantang=yuantang,
            postnatal=postnatal,
            timeline=timeline,
            structure=structure,
            hua_gong=hua_gong,
            seasonal_hexagram=seasonal_hex,
        )

    def _build_timeline(
        self,
        prenatal: PrenatalHexagram,
        yuantang: YuanTang,
        postnatal: PostnatalHexagram,
        postnatal_yuantang: YuanTang,
        birth_year: int | None,
    ) -> Timeline:
        """构建时间序列：大运（爻位值运）+ 流年卦 + 流月卦。

        基于 timeline_yun 模块（《河洛理数·卷之四/五》论大运/流年/流月）。
        """
        if birth_year is None:
            birth_year = 1984  # 未提供时占位（甲子年），后续需由调用方传入真实年份

        # 先天/后天六爻
        prenatal_lines = build_six_lines(prenatal.upper_gua, prenatal.lower_gua)
        postnatal_lines = build_six_lines(postnatal.upper_gua, postnatal.lower_gua)

        # 大运（爻位值运）
        dayun = compute_dayun_liyao(
            prenatal_lines,
            yuantang.yuantang_index,
            postnatal_lines,
            postnatal_yuantang.yuantang_index,
        )

        # 流年卦（1~100 岁，按大运爻分段）
        liunian = compute_liunian(
            prenatal_lines,
            yuantang.yuantang_index,
            postnatal_lines,
            postnatal_yuantang.yuantang_index,
            birth_year=birth_year,
            age_from=1,
            age_to=100,
        )

        # 流月卦（以流年卦为本，元堂取该流年所属大运段元堂）+ 流日卦
        yearly = []
        for y in liunian.years:
            # 流年卦元堂：大运分段后取该年所属大运段元堂；无则回退先天元堂
            yyt = y.yuantang_index if y.yuantang_index >= 0 else yuantang.yuantang_index
            # 流年卦元堂爻性（H8 解卦层：流年卦断爻=流年卦元堂，规格书"流月以流年卦元堂为本"）
            yyt_nature = y.lines[yyt] if y.lines and 0 <= yyt < len(y.lines) else None
            liuyue = compute_liuyue(y.lines, yyt)
            months = []
            for m in liuyue.months:
                # 流日卦：以当月月卦为本，从居位爻下一爻起六爻俱变（每爻管5日，§6.4 裁定）
                # 节气对齐：流日卦须从当月"节"时刻起管（《河洛真数》起日卦例）
                jie_dt = None
                try:
                    jie_dt = _jie_datetime_for_lunar_month(y.year, m["month"])
                except Exception:
                    jie_dt = None
                liuri = compute_liuri(m["lines"], m["yue_yao_index"], jie_dt)
                # 流时卦（《河洛真数·起例卷之上·起时卦例》）：以值日卦为本，
                # 前六时(子~巳)进数变/后六时(午~亥)退数变，阳时变爻阴时取应
                for dseg in liuri.days:
                    diffs = [k for k in range(6) if len(dseg["lines"]) > k and len(m["lines"]) > k
                             and dseg["lines"][k] != m["lines"][k]]
                    if len(diffs) == 1:
                        liushi = compute_liushi(dseg["lines"], diffs[0])
                        dseg["flip_index"] = diffs[0]
                        dseg["hours"] = liushi.hours
                months.append({
                    "month": m["month"],
                    "name": m["name"],
                    "upper": m["upper"],
                    "lower": m["lower"],
                    "lines": m["lines"],
                    "kind": m["kind"],
                    "yue_yao_index": m["yue_yao_index"],
                    "jie_datetime": jie_dt,
                    "days": liuri.days,
                })
            yearly.append({
                "age": y.age,
                "year": y.year,
                "ganzhi": y.ganzhi,
                "yang_year": y.yang_year,
                "hexagram": y.hexagram_name,
                "upper": y.upper,
                "lower": y.lower,
                "lines": y.lines,
                "yuantang_index": yyt,
                "yuantang_nature": yyt_nature,
                "months": months,
            })

        # P1：易经解卦层 — 为每个流年卦附加 EVENT_SIGNAL
        yearly = interpret_all_liunian(
            yearly,
            yuan_tang_index=yuantang.yuantang_index,
            yuan_tang_nature=yuantang.yao_nature,
        )

        dayun_entries = [
            {
                "age_start": e.age_start,
                "age_end": e.age_end,
                "hexagram": e.hexagram_name,
                "line_index": e.line_index,
                "line_nature": e.line_nature,
            }
            for e in dayun.sequence
        ]

        return Timeline(
            yearly_hexagrams=yearly,
            monthly_hexagrams=[],
            daily_hexagram={
                "date": str(birth_year),
                "hexagram": prenatal.hexagram_name,
                "upper": prenatal.upper_gua,
                "lower": prenatal.lower_gua,
            },
            hourly_hexagram=None,
            seasonal_hexagram=None,
            qi_phase={
                "dayun": dayun_entries,
                "note": "爻位值运（阳爻9年/阴爻6年，自元堂起行先天再行后天）",
            },
            hua_gong=None,  # 由 calculate() 在 HeluoResult 中单独设置
        )

    def _compute_huagong(
        self,
        prenatal: PrenatalHexagram,
        postnatal: PostnatalHexagram,
        birth_date: str,
        gender: str,
        birth_year: int | None,
    ) -> HuaGongResult | None:
        """H6: 计算化工状态。"""
        try:
            # 月支按节气节令月精确判定（修复：原实现用公历月份近似，
            # 边界日会错判月支，如 11-03 立冬前实为戌月却被当亥月）。
            from .hua_gong import compute_huagong, resolve_birth_month_branch
            branch = resolve_birth_month_branch(birth_date)
            if branch is None:
                return None
            return compute_huagong(
                prenatal.upper_gua, prenatal.lower_gua,
                postnatal.upper_gua, postnatal.lower_gua,
                branch,
            )
        except Exception:
            return None

    def _compute_seasonal_hexagram(self, birth_date: str) -> dict | None:
        """H11: 获取出生日所在节气的节候卦。"""
        try:
            from datetime import datetime as dt
            bd = dt.fromisoformat(birth_date)
            info = get_current_jieqi_info(bd.year, bd.month, bd.day)
            if info is None:
                return None
            return {
                "jq_index": info.jq_index,
                "jq_name": info.jq_name,
                "main_gua": info.main_gua,
                "moving_line": info.moving_line,
                "result_gua": info.result_gua,
                "evidence": info.evidence,
            }
        except Exception:
            return None

    def verify_golden_case(self, case_name: str) -> bool:
        """
        验证 Golden Case 是否通过当前算法。

        纪晓岚 Golden Case:
        input: 甲辰 辛未 丙戌 甲午 午时 男
        expected: 地天泰 → 六四 → 天雷无妄
        """
        if case_name not in self.GOLDEN_CASES:
            raise ValueError(f"Unknown golden case: {case_name!r}")

        case = self.GOLDEN_CASES[case_name]
        result = self.calculate(
            bazi=case["bazi"],
            gender=case["gender"],
            birth_hour=case["birth_hour"],
            era=case.get("era", "zhong"),
            birth_year=case.get("birth_year"),
        )

        expected = case["expected"]

        # 逐项验证
        checks = [
            ("tian_shu", result.numbers.tian_shu, expected["tian_shu"]),
            ("di_shu", result.numbers.di_shu, expected["di_shu"]),
            ("tian_reduced", result.numbers.tian_reduced, expected["tian_reduced"]),
            ("di_reduced", result.numbers.di_reduced, expected["di_reduced"]),
            ("prenatal", result.prenatal.hexagram_name, expected["prenatal"]),
            ("yuantang", result.yuantang.yuantang, expected["yuantang"]),
            ("yuantang_index", result.yuantang.yuantang_index, expected["yuantang_index"]),
            ("postnatal", result.postnatal.hexagram_name, expected["postnatal"]),
        ]

        all_pass = True
        for name, actual, expected_val in checks:
            if actual != expected_val:
                print(f"  ❌ {name}: expected {expected_val!r}, got {actual!r}")
                all_pass = False
            else:
                print(f"  ✅ {name}: {actual!r}")

        return all_pass

    def run_all_golden_cases(self) -> dict[str, bool]:
        """运行所有 Golden Case 并返回结果"""
        results = {}
        for case_name in self.GOLDEN_CASES:
            print(f"\n=== Golden Case: {case_name} ===")
            results[case_name] = self.verify_golden_case(case_name)
        return results


# ========== 向后兼容入口 ==========

def heluo_calculate(
    bazi: list[tuple[str, str]],
    gender: str = "male",
    birth_hour: str = "子",
    era: str = "zhong",
) -> HeluoResult:
    """
    兼容旧接口的便捷函数。

    注意：此函数仅用于向后兼容，新项目请使用 HeluoCanonical。
    """
    canonical = HeluoCanonical()
    return canonical.calculate(bazi, gender, birth_hour, era)


# 导出标准符号
__all__ = [
    "HeluoCanonical",
    "HeluoResult",
    "heluo_calculate",
    "GOLDEN_CASES",
]
