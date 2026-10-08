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
    compute_liuri_stub,
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
#: 节气→农历月 映射缓存，2026-10-06 加容量上限。
#: 原为无界 dict：实测跑到 124 年 / 1,488 条（出生年跨度可达数百年），
#: 长期服务会缓慢涨内存且永不回收。超出即按插入顺序丢最旧的（FIFO）。
#: 刻意用普通 dict 而非 OrderedDict —— Python 3.7+ dict 保序，FIFO 已够，
#: 且不影响任何外部对 _jie_cache 注入普通 dict 的用法。
_jie_cache: dict[int, dict[int, str]] = {}
_JIE_CACHE_MAX = 256

#: sxtwl 惰性单例：_SXTWL 为已解析模块，_SXTWL_FAILED=True 表示本进程不可用。
#: 2026-10-06：旧实现把 `import sxtwl` 写在 _compute_year_jie 体内，缺依赖时
#: 每调用一次就重走一遍 import 机制并抛 ImportError（一盘 1,116 次 ≈ 206 ms），
#: 且异常穿透使 _jie_cache 永远写不进去，缓存完全失效。此处改为进程级解析一次。
_SXTWL = None
_SXTWL_FAILED = False


def _get_sxtwl():
    """惰性解析 sxtwl，进程内至多解析一次；不可用时返回 None 并记住失败。"""
    global _SXTWL, _SXTWL_FAILED
    if _SXTWL is None and not _SXTWL_FAILED:
        try:
            import sxtwl as _m
            _SXTWL = _m
        except ImportError:
            _SXTWL_FAILED = True
    return _SXTWL


def _jie_datetime_for_lunar_month(year: int, lunar_month: int) -> str | None:
    """返回农历 lunar_month 月"节"的精确时刻（公历 YYYY-MM-DD HH:MM）。

    一次遍历拿到该公历年的全部12个"节"并缓存，后续查表（避免逐月重复遍历）。
    用于流日卦节气对齐（《河洛理数》卷二下）。
    sxtwl 不可用时缓存空表并返回 None，不重复试探 import。
    """
    global _jie_cache
    if year not in _jie_cache:
        sxtwl = _get_sxtwl()
        _jie_cache[year] = _compute_year_jie(year, sxtwl) if sxtwl is not None else {}
        if len(_jie_cache) > _JIE_CACHE_MAX:
            for stale in list(_jie_cache)[:len(_jie_cache) - _JIE_CACHE_MAX]:
                _jie_cache.pop(stale, None)
    return _jie_cache[year].get(lunar_month)


def _jie_by_batch(sxtwl, year: int) -> dict[int, tuple] | None:
    """用 sxtwl.getJieQiByYear 批量取 year-1~year+1 的 12 个"节"。

    返回 {农历月: (gap, "YYYY-MM-DD HH:MM")}；批量接口不可用时返回 None，
    由调用方回退到逐日扫描。取窗与取月口径与旧逐日实现完全一致。

    ⚠ API 形态（2026-10-06 实机核正）：sxtwl 有两个不同的返回类，方法名不能混用——
      - ``sxtwl.fromSolar(...)``      → ``Day``，有**方法** getJieQi() / getJieQiJD()
      - ``sxtwl.getJieQiByYear(y)``  → ``JieQiInfo`` 元组（25 项，含跨年小寒/大寒），
        只有**属性** .jd / .jqIndex，**没有** getJieQi() / getJieQiJD()
    本函数初版误按方法取，抛 AttributeError 被兜底吞掉，静默退回慢路径（空转）。
    此处按 bazi_engine._compute_with_sxtwl 的既有形态取属性，并保留 tuple 兼容分支。
    """
    jie_to_lm = {idx: m for m, idx in _LUNAR_MONTH_JIE.items()}
    best: dict[int, tuple] = {}
    try:
        for target in (year - 1, year, year + 1):
            for info in sxtwl.getJieQiByYear(target):
                # JieQiInfo 形态：属性 .jd/.jqIndex；老版本为 tuple，兜底 _jq[0]/_jq[1]
                jd, idx = (info.jd, info.jqIndex) if hasattr(info, "jd") else (info[0], info[1])
                lm = jie_to_lm.get(idx)
                if lm is None:
                    continue
                t = sxtwl.JD2DD(jd)
                if not (0 < t.Y <= 2200):
                    continue
                gap = abs(t.Y - year)
                if lm not in best or gap < best[lm][0]:
                    best[lm] = (gap, f"{t.Y:04d}-{t.M:02d}-{t.D:02d} "
                                       f"{int(t.h):02d}:{int(t.m):02d}")
    except Exception:
        return None
    return best or None


def _jie_by_dayscan(sxtwl, year: int) -> dict[int, tuple]:
    """回退路径：逐日遍历公历 year-1~year+1 找齐 12 个"节"（1,095 天）。"""
    from datetime import date, timedelta
    jie_to_lm = {idx: m for m, idx in _LUNAR_MONTH_JIE.items()}
    best: dict[int, tuple] = {}
    d = date(year - 1, 1, 1)
    end = date(year + 1, 12, 31)
    while d <= end:
        day_obj = sxtwl.fromSolar(d.year, d.month, d.day)
        jq = day_obj.getJieQi()
        lm = jie_to_lm.get(jq)
        if lm is not None:
            t = sxtwl.JD2DD(day_obj.getJieQiJD())
            if 0 < t.Y <= 2200:
                gap = abs(d.year - year)
                if lm not in best or gap < best[lm][0]:
                    best[lm] = (gap, f"{t.Y:04d}-{t.M:02d}-{t.D:02d} "
                                       f"{int(t.h):02d}:{int(t.m):02d}")
        d += timedelta(days=1)
    return best


def _compute_year_jie(year: int, sxtwl=None) -> dict[int, str]:
    """找齐该公历年对应农历 1-12 月的 12 个"节"，返回 {农历月: 时刻字符串}。

    2026-10-06：主路径改用 sxtwl.getJieQiByYear 批量取节气。旧实现自 year-1-01-01
    逐日扫到 year+1-12-31（1,095 天 × 1 次 fromSolar），一盘 93 个流年即约 10 万次
    天文推算；批量接口 3 次调用覆盖同一取窗。取窗、取月、同月择优口径均不变。
    批量接口不可用时自动回退逐日扫描，保证结果不劣于旧实现。
    """
    if sxtwl is None:
        sxtwl = _get_sxtwl()
    if sxtwl is None:
        return {}
    best = _jie_by_batch(sxtwl, year)
    if best is None:
        best = _jie_by_dayscan(sxtwl, year)
    return {lm: dt for lm, (_, dt) in best.items()}
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
    # 2026-10-07 审计修：era（shang/zhong/xia 上中下元）此前只是 calculate() 的
    # 入参，算完即丢。下游 frozen_state 拿不到，只能去读 result.input.timezone
    # （恒为 "Asia/Shanghai"）冒充 era——**世代出处彻底丢失且被写成时区**。
    era: str = "zhong"
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
        # ⚠ 2026-10-08：下方会把缺失的 birth_date 补成 f"{yr}-01-01" 喂 HeluoInput。
        #   那个占位日期**只许喂 HeluoInput**，不得流进节气链路：
        #   节气窗口（L558–L567）按节气切，补出来的 1 月 1 日会算成「冬至 jq=0」，
        #   化工据此给出一个凭空造出的当令卦，且 evidence 不再标兜底——
        #   **缺失输入被当成真实输入，比答错更坏**。故此处先留住真值。
        _real_birth_date = birth_date
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

        # Step 8: H11 节候卦（出生日所在节气）—— **提前到化工之前**。
        # 2026-10-08：原先它在 Step 9、排在化工之后，于是化工要自己再调一次
        # sxtwl 求同一个 jq_index——同一份结果算两遍。jq 只依赖 birth_date、
        # 与盘面无关，提前算不影响任何东西，故改为算一次、两处共用。
        # 只用**真值**。为 None/空串时返回 None（不判），
        #        化工随之拿不到 jq_index，自会走兜底并在 evidence 里自曝。
        seasonal_hex = (self._compute_seasonal_hexagram(_real_birth_date)
                        if _real_birth_date else None)

        # Step 9: H6 化工计算（复用上面已算好的 jq_index，不再重复求节气）
        hua_gong = self._compute_huagong(
            prenatal, postnatal, bazi, birth_date, gender, birth_year,
            jieqi_index=(seasonal_hex or {}).get("jq_index"),
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
            seasonal_hexagram=seasonal_hex,
            era=era,
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
                # 流日 / 流时均改按需（2026-10-06）：
                #   · 流时：旧实现在此把 93 流年 × 12 月 × 6 日全部展开为流时卦，
                #     共 6,696 次 compute_liushi / 80,352 条小时记录，占四层载荷 91%、
                #     卦名换算 92%——而消费方（guajie）按 target_hour 点查，每次只需 1 条。
                #     只记动爻 flip_index，hours 由 guajie 命中该日段时现算。
                #   · 流日：更进一步，只记 6 段的廉价定位字段（segment/day_from/
                #     day_to/flip_index），**不做卦名换算**。原先每月一次
                #     compute_liuri（内含 6 次 _lines_to_hexagram），1,116 个月
                #     合计 6,696 次，是流时之外最大的一笔开销。
                #     flip_index 改用闭式 (yue_yao_index + 1 + k) % 6，
                #     与原「逐爻 diff 求唯一差异爻」在 20,592 个日段上实测全等。
                #
                # tests/test_heluo_context.py::test_timeline_structure 只断言
                # `len(months[0]["days"]) == 6`（引原典「六爻俱变毕，则满三十日」），
                # **不检查日段内容**，故本改造不触碰其断言。
                # 需要完整日段时走 materialize_month_days（仅命中月）。
                months.append({
                    "month": m["month"],
                    "name": m["name"],
                    "upper": m["upper"],
                    "lower": m["lower"],
                    "lines": m["lines"],
                    "kind": m["kind"],
                    "yue_yao_index": m["yue_yao_index"],
                    "jie_datetime": jie_dt,
                    "days": compute_liuri_stub(m["lines"], m["yue_yao_index"]),
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
                "phase": e.phase,
            }
            for e in dayun.sequence
        ]

        return Timeline(
            yearly_hexagrams=yearly,
            # ── 2026-10-06 修正三处名实不符的占位字段 ────────────────
            # 原先 daily_hexagram 存的是**先天卦**，而字段注释写「今日卦」，
            # 其 date 还塞了 str(birth_year)（如 "1990"）——既不是日期，也不是
            # 流日卦。monthly_hexagrams 恒 []、hourly_hexagram 恒 None。
            # 三者全仓零消费方（测试里的同名 daily_hexagram 均为黄历字段）。
            #
            # 真实流月/流日/流时卦在四层时间轴内：yearly[].months[] 及
            # months[].days[]（日段按需物化，见 compute_liuri_stub /
            # materialize_month_days），消费方 guajie 按时应期定位。
            # 这里不再重复一份**名不副实**的副本，一律置空并在此说明。
            monthly_hexagrams=[],
            daily_hexagram={},
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
        bazi: list[tuple[str, str]],
        birth_date: str,
        gender: str,
        birth_year: int | None,
        jieqi_index: int | None = None,
    ) -> HuaGongResult | None:
        """H6: 计算化工状态。

        2026-10-07 修：原先**拿公历月份硬凑月支**（{1:丑, 2:寅, …, 12:子}），
        而月令以**节气**为界（立春起寅、大雪起子）。公历 1 月实为戌/亥月
        而非丑月 —— 立春至大雪之间的出生**全部判错化工卦**。
        例：1983-11-03 生，公历 11 月 → 亥 → 坎；实为霜降后戌月 → 兑。

        `calculate()` 手上有 bazi，月柱地支即真实月令，现直接取用；
        年干支一并下传，供 L576 的纳音第三级回退使用。
        公历月近似映射整个删除。
        """
        try:
            if not bazi or len(bazi) < 2:
                return None
            month_branch = bazi[1][1]     # 月柱地支＝节气月令
            year_gan, year_zhi = bazi[0][0], bazi[0][1]
            # ⚠ 2026-10-08（F-3）：**未**下传 birth_date，即生产链当前仍走
            #   月支近似表 SEASON_BRANCH_TO_HUAGONG，而非已落码并自校验通过的
            #   原典 L558–L567 节气窗口（hua_gong.huagong_by_birth_date）。
            #   实测二者差异：寅/巳/申/亥 四个月支**整月**不同，卯/午/酉 跨窗口。
            #   例 1724-05-22：节气窗口判「震」(L561 五月正在震窗口内)，
            #   近似表判「离」；下游 state 由 WEAK 变 UNRESOLVED。
            #   翻转会让 tests/heluo/test_h2_frozen_state.py::test_huagong 与
            #   tests/heluo/test_audit_batch_20261007.py::test_weak_case_..._reach_frozen_state
            #   两个 **Golden** 用例翻盘。AGENTS.md 禁擅改 Golden 期望值，
            #   故此处保持原样，待显式批准后再改这两条 + 打开本行。
            #   登记见 hua_gong.HUAGONG_PENDING_BRANCH_SWITCH。
            return compute_huagong(
                prenatal.upper_gua, prenatal.lower_gua,
                postnatal.upper_gua, postnatal.lower_gua,
                month_branch,
                year_gan=year_gan, year_zhi=year_zhi,
                jieqi_index=jieqi_index,
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
                # 2026-10-06: 原用 ❌/✅ 打印，在 GBK 控制台（非 UTF-8 stdout）
                # 会抛 UnicodeEncodeError —— 而本方法是返回 bool 的公开校验入口，
                # 一旦打印失败就变成抛异常，调用方拿不到结论。改用 ASCII 标记。
                print(f"  FAIL {name}: expected {expected_val!r}, got {actual!r}")
                all_pass = False
            else:
                print(f"  OK   {name}: {actual!r}")

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
