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
from .timeline_yun import Timeline
from .timeline_yun import (
    compute_dayun_liyao,
    compute_liunian,
    compute_liuri,
    compute_liushi,
    compute_liuyue,
)


# 节气月（子月起）→ 月令"节"（sxtwl 节气索引，奇数=节）
# 编号语义与 timeline_yun.compute_liuyue 的流月编号一致：month=1=子月、2=丑月 … 12=亥月。
# （河洛流月卦自子月起，见《起例卷之上·起月卦例》"月卦之法悉从二十四气，非从朔望"；
#   H16 观卦上九元堂子月=风雷益为证。原表按农历"正月=寅月"建号，与流月编号错位
#   一整节对——流日卦节气锚整体错位，2026-10-15 收敛性审计修正。）
# 子月=大雪(23)、丑月=小寒(1)、寅月=立春(3)、卯月=惊蛰(5)、辰月=清明(7)、
# 巳月=立夏(9)、午月=芒种(11)、未月=小暑(13)、申月=立秋(15)、酉月=白露(17)、
# 戌月=寒露(19)、亥月=立冬(21)
_LUNAR_MONTH_JIE = {
    1: 23, 2: 1, 3: 3, 4: 5, 5: 7, 6: 9,
    7: 11, 8: 13, 9: 15, 10: 17, 11: 19, 12: 21,
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


def _jie_interval_for_lunar_month(year: int, lunar_month: int) -> tuple[str | None, str | None]:
    """(当月节时刻, 下月节时刻) — 节气为界（H10b 规则分疏）。

    流日卦段边界须按"节→下节"实际间隔（约 29~31 日不等）均匀切分，
    不可机械固定每段日数。下月节跨年：亥月（12）→ 下一年链子月（大雪）。
    """
    t0 = _jie_datetime_for_lunar_month(year, lunar_month)
    if t0 is None:
        return None, None
    nxt_lm = lunar_month + 1
    nxt_year = year
    if nxt_lm > 12:
        nxt_lm = 1
        nxt_year = year + 1
    t1 = _jie_datetime_for_lunar_month(nxt_year, nxt_lm)
    return t0, t1


def _compute_year_jie(year: int) -> dict[int, str]:
    """遍历公历 year-1~year+1，找齐 12 个"节"，按农历月 1-12 建映射。

    节气归属（《河洛真数·起例卷之上·起月卦例》"悉从二十四气…此说方合节气"）：
      - 流年链 year 的 12 个流月按节气顺次（子月=大雪 → 亥月=立冬），
        以大雪（冬至）为岁首，子月跨前一年末。
      - 因此子月（lunar_month=1，大雪）锚 **year-1 年 12 月**（2027 链子月=2026-12-07），
        其余月（丑~亥）锚当年。修复此前 gap 就近导致子月锚当年末大雪
        （2027-12-07）而时序倒错（子月晚于丑月）的缺陷。
    """
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
            # 归属：子月（大雪）属流年链上一公历年末；其余月属当年
            if lm == 1:
                gap = 0 if d.year == year - 1 else abs(d.year - year) + 10
            else:
                gap = 0 if d.year == year else abs(d.year - year) + 10
            if lm not in best or gap < best[lm][0]:
                best[lm] = (gap, f"{t.Y:04d}-{t.M:02d}-{t.D:02d} {int(t.h):02d}:{int(t.m):02d}")
        d += timedelta(days=1)
    for lm, (_, dtstr) in best.items():
        result[lm] = dtstr
    return result
from .hexagram import analyze_hexagram, HexagramStructure
from .yi_interpreter import interpret_all_liunian
from .hua_gong import compute_huagong, HuaGongResult
from .yuan_qi import compute_yuan_qi, YuanQiResult
from .jiehhou import get_seasonal_hexagram, get_current_jieqi_info

_STEMS60 = "甲乙丙丁戊己庚辛壬癸"
_BRANCHES60 = "子丑寅卯辰巳午未申酉戌亥"


def _recover_birth_year(bazi_year_ganzhi: str, now_year: int | None = None) -> int | None:
    """从年柱干支反推最近（≤当前年）的公历年份。

    DISPUTE-HL-03 配套：docstring 承诺"未提供时从 bazi 年柱干支反推（60 甲子近似）"，
    取代此前 `birth_year = 1984` 的误导占位。甲子年 = 1984（(y-4)%10==0 且 (y-4)%12==0）。
    """
    if not bazi_year_ganzhi or len(bazi_year_ganzhi) < 2:
        return None
    try:
        g = _STEMS60.index(bazi_year_ganzhi[0])
        z = _BRANCHES60.index(bazi_year_ganzhi[1])
    except ValueError:
        return None
    import datetime
    if now_year is None:
        now_year = datetime.date.today().year
    y = now_year
    for _ in range(300):  # 5 个甲子（300 年）内必命中最近过去年
        if (y - 4) % 10 == g and (y - 4) % 12 == z:
            return y
        y -= 1
    return None


def _hua_gong_to_dict(hg: HuaGongResult | None) -> dict | None:
    """HuaGongResult → dict（state 枚举转字符串，供 timeline.hua_gong 回填）。"""
    if hg is None:
        return None
    return {
        "state": hg.state.value if hasattr(hg.state, "value") else str(hg.state),
        "huagong_trigram": hg.huagong_trigram,
        "birth_month_branch": hg.birth_month_branch,
        "has_huagong": hg.has_huagong,
        "has_opposite": hg.has_opposite,
        "evidence": list(hg.evidence),
    }


def _compose_daily_hexagram(
    monthly_hexagrams: list[dict],
    target_month: int | None = None,
    target_day: int | None = None,
) -> dict:
    """H10 顶层流日结构：目标月 1 个流日本卦（《起日卦例》每爻管5日/满30日）。

    daily_yao = 6 段（初爻→上爻，每段管 5 日），target_day 命中段标 active_segment。
    流日卦以当月流月卦为本逐爻变（days 段由 compute_liuri 产出，节气对齐）。
    """
    empty = {"base_hex": None, "daily_yao": [], "target_day": target_day,
             "active_segment": None, "note": "无目标年流月卦"}
    if not monthly_hexagrams:
        return empty
    m = None
    if target_month is not None:
        for mm in monthly_hexagrams:
            if mm.get("month") == target_month:
                m = mm
                break
    if m is None:
        m = monthly_hexagrams[0]
    days = m.get("days") or []
    if not days:
        return {"base_hex": None, "daily_yao": [], "target_day": target_day,
                "active_segment": None, "note": "目标月无流日段"}
    daily_yao = []
    active_segment = None
    m_lines = m.get("lines") or []
    for k, dseg in enumerate(days):
        yao_idx = k if k < 6 else 5
        dl = dseg.get("lines") or []
        # 流日动爻 = 段卦相对月卦的变爻（《起日卦例》逐爻俱变）
        fl = dseg.get("flip_index")
        if fl is None:
            diffs = [i for i in range(6) if len(dl) > i and len(m_lines) > i and dl[i] != m_lines[i]]
            fl = diffs[0] if len(diffs) == 1 else None
        seg = {
            "day_from": dseg.get("day_from", k * 5 + 1),
            "day_to": dseg.get("day_to", k * 5 + 5),
            "active_yao": ("初爻", "二爻", "三爻", "四爻", "五爻", "上爻")[yao_idx],
            "hexagram": dseg.get("name", ""),
            "lines": dl,
            "flip_index": fl,
            "date_from": dseg.get("date_from") or "",
            "jie_span_days": dseg.get("jie_span_days"),  # H10b 实际节气间隔（天）
            "hours": dseg.get("hours") or [],  # 流时（设计剥离，保留结构）
        }
        daily_yao.append(seg)
        if target_day is not None and seg["day_from"] <= target_day <= seg["day_to"]:
            active_segment = seg
    return {
        "base_hex": {
            "month": m.get("month"),
            "month_hexagram": m.get("name", ""),
            "yue_yao_index": m.get("yue_yao_index"),
            "jie_datetime": m.get("jie_datetime") or "",
            "first_segment": daily_yao[0] if daily_yao else None,
            "note": "流日本卦：以目标月月卦为本逐爻变，每爻管5日、满30日（起日卦例）",
        },
        "daily_yao": daily_yao,
        "target_day": target_day,
        "active_segment": active_segment,
    }


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
    yuan_qi: YuanQiResult | None = None            # H7: 元气状态（天/地元气 + 元反）
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
        target_year: int | None = None,
        target_month: int | None = None,
        target_day: int | None = None,
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
        target_year/target_month/target_day: H10 惰性化目标点。仅目标流年生成完整流年卦、
                      目标年 12 流月卦、目标月 1 流日卦；其余流年仅元数据。缺省仅元数据。
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

        # Step 6: 时间序列（大运爻位值运 + 流年卦 + 流月卦 + 流日卦；H10 惰性目标点）
        timeline = self._build_timeline(
            bazi, prenatal, yuantang, postnatal, postnatal_yuantang, birth_year,
            target_year=target_year, target_month=target_month, target_day=target_day,
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

        # Step 8.5: H7 元气（年柱纳甲/后天宫位配先天之气）— 与化工对偶
        try:
            from .yuan_qi import compute_yuan_qi as _cyq
            yr_stem = bazi[0][0] if (bazi and len(bazi) > 0) else ""
            yr_branch = bazi[0][1] if (bazi and len(bazi) > 0) else ""
            yuan_qi = None
            if yr_stem and yr_branch:
                yuan_qi = _cyq(
                    yr_stem, yr_branch,
                    prenatal.upper_gua, prenatal.lower_gua,
                    postnatal.upper_gua, postnatal.lower_gua,
                )
        except Exception:
            yuan_qi = None

        # Step 9: H11 节候卦（出生日所在节气）
        seasonal_hex = self._compute_seasonal_hexagram(birth_date)

        # Step 10: timeline 占位字段回填真实值（seasonal_hexagram/hua_gong），
        # 消除 timeline 内 None 易误读（P3）；流时 hourly_hexagram 按设计剥离保持 None。
        if timeline is not None:
            from dataclasses import replace as _replace
            timeline = _replace(
                timeline,
                seasonal_hexagram=seasonal_hex,
                hua_gong=_hua_gong_to_dict(hua_gong),
            )

        return HeluoResult(
            input=input_obj,
            numbers=numbers,
            prenatal=prenatal,
            yuantang=yuantang,
            postnatal=postnatal,
            timeline=timeline,
            structure=structure,
            hua_gong=hua_gong,
            yuan_qi=yuan_qi,
            seasonal_hexagram=seasonal_hex,
        )

    def _build_timeline(
        self,
        bazi: list[tuple[str, str]],
        prenatal: PrenatalHexagram,
        yuantang: YuanTang,
        postnatal: PostnatalHexagram,
        postnatal_yuantang: YuanTang,
        birth_year: int | None,
        target_year: int | None = None,
        target_month: int | None = None,
        target_day: int | None = None,
    ) -> Timeline:
        """构建时间序列：大运（爻位值运）+ 流年卦 + 流月卦 + 流日卦。

        基于 timeline_yun 模块（《河洛理数·卷之四/五》论大运/流年/流月）。

        H10 定稿方案惰性化：完整卦只算目标点——
          - 大运层：元数据（爻位值运，不起卦）
          - 流年层：全部年份保留元数据（yearly_meta）；仅目标流年 target_year 生成完整卦
          - 流月层：仅目标年 12 个流月卦，放顶层 monthly_hexagrams（不再嵌套 yearly[].months 全量）
          - 流日层：仅目标月 1 个流日本卦，放顶层 daily_hexagram（base_hex + 30 日/6 爻段）
        target_year 缺省：仅元数据，不产目标卦（guajie 无目标不定位，向后兼容）。
        """
        if birth_year is None:
            # DISPUTE-HL-03：不再静默占位（1984 甲子），按 docstring 承诺从年柱干支反推
            # 最近（≤当前年）的公历年份；反推失败则显式报错，宁漏勿错。
            birth_year = _recover_birth_year(bazi_year_ganzhi=bazi[0][0] + bazi[0][1])
            if birth_year is None:
                raise ValueError(
                    "birth_year 未提供且无法从年柱干支反推，必须显式传入真实出生年份")

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

        # 流年卦（1~100 岁，按大运爻分段；H10 惰性：仅 target_year 生成完整卦象）
        liunian = compute_liunian(
            prenatal_lines,
            yuantang.yuantang_index,
            postnatal_lines,
            postnatal_yuantang.yuantang_index,
            birth_year=birth_year,
            age_from=1,
            age_to=100,
            target_year=target_year,
        )

        # 流月卦（以流年卦为本，元堂取该流年所属大运段元堂）+ 流日卦
        yearly = []
        yearly_meta = []
        for y in liunian.years:
            yearly_meta.append({
                "age": y.age,
                "year": y.year,
                "ganzhi": y.ganzhi,
                "yang_year": y.yang_year,
                "yuantang_index": y.yuantang_index if y.yuantang_index >= 0 else -1,
            })
            if not y.hexagram_name:
                continue  # 非目标年：仅元数据，不起流月/流日卦
            # 流年卦元堂：大运分段后取该年所属大运段元堂；无则回退先天元堂
            yyt = y.yuantang_index if y.yuantang_index >= 0 else yuantang.yuantang_index
            # 流年卦元堂爻性（H8 解卦层：流年卦断爻=流年卦元堂，规格书"流月以流年卦元堂为本"）
            yyt_nature = y.lines[yyt] if y.lines and 0 <= yyt < len(y.lines) else None
            liuyue = compute_liuyue(y.lines, yyt)
            months = []
            for m in liuyue.months:
                # 流日卦：以当月月卦为本，从居位爻下一爻起六爻俱变（节气为界，H10b 均匀分配）
                # 段边界按"当月节→下月节"实际间隔均匀切分，不可机械固定每段日数
                jie_dt, next_jie_dt = _jie_interval_for_lunar_month(y.year, m["month"])
                liuri = compute_liuri(m["lines"], m["yue_yao_index"], jie_dt, next_jie_dt)
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

        # P1：易经解卦层 — 为目标流年卦附加 EVENT_SIGNAL（惰性：仅 1 条）
        if yearly:
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

        # H10 顶层结构：monthly_hexagrams = 目标年 12 流月卦（完整，含 days）
        monthly_hexagrams = list(yearly[0].get("months", [])) if yearly else []
        # H10 顶层结构：daily_hexagram = 目标月流日本卦（base_hex + 30 日/6 爻段）
        daily_hexagram = _compose_daily_hexagram(monthly_hexagrams, target_month, target_day)

        return Timeline(
            yearly_hexagrams=yearly,
            # 完整流月卦在 monthly_hexagrams（修复"内嵌在 year、顶层为空"的接线 bug）
            monthly_hexagrams=monthly_hexagrams,
            daily_hexagram=daily_hexagram,
            hourly_hexagram=None,  # 流时按设计剥离（不接）
            seasonal_hexagram=None,  # H11 节候卦：calculate() 层回填
            qi_phase={
                "dayun": dayun_entries,
                "note": "爻位值运（阳爻9年/阴爻6年，自元堂起行先天再行后天）",
            },
            hua_gong=None,  # H6 化工：calculate() 层回填 dict
            yearly_meta=yearly_meta,
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
