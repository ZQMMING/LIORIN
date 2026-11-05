"""紫微斗数适配器 — bySolar 模式

关键修改：使用 iztro 的 bySolar 函数（阳历输入），而非 byLunar。

依据：倪海厦《天纪》体系 + 官方数据集验证
- 数据集使用 bySolar(solarDate, hour, gender, isLeapMonth, locale)
- 我们的引擎必须对齐此行为
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .ziwei_engine import ZiweiEngine, ZiweiChart, time_index_from_hour

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZiweiCalculationPolicy:
    """紫微斗数计算政策 — P0-14 已冻结。"""
    date_source: str = "lunar"
    late_zi_handling: str = "same_day"
    ratified_policy_version: str = "P0-14-v1"

    @property
    def is_pending(self) -> bool:
        return False

    @property
    def is_ratified(self) -> bool:
        return True

    def to_dict(self) -> dict:
        return {
            "status": "RATIFIED",
            "date_source": self.date_source,
            "late_zi_handling": self.late_zi_handling,
            "ratified_policy_version": self.ratified_policy_version,
        }


@dataclass(frozen=True)
class SolarInput:
    """阳历输入"""
    year: int
    month: int
    day: int
    hour: int
    gender: str = "male"
    longitude: Optional[float] = None  # 经度（用于真太阳时校正）


def compute_via_solar(year: int, month: int, day: int, hour: int, 
                       gender: str = "male") -> dict:
    """使用 bySolar 计算命盘（与数据集一致）
    
    Args:
        year: 阳历年
        month: 阳历月
        day: 阳历日
        hour: 出生时辰（24小时制，0-23）
        gender: 性别
    
    Returns:
        dict: 包含命盘关键信息的字典
    """
    gender_js = "男" if gender == "male" else "女"
    
    # iztro bySolar() 第2个参数是 timeIndex (0-12 时辰序号: 0=早子, 1=丑 … 11=亥, 12=晚子)。
    # 必须与 ziwei_engine.time_index_from_hour 保持一致（修复：旧实现 hour<=12 时直接把
    # 24h 小时当 timeIndex 用，导致巳时(10h)被传成 index 10=戌时、23h 被截成亥时而非晚子时，
    # 阳历接入路径与农历主路径排盘不一致）。
    time_index = time_index_from_hour(hour)
    
    script = f'''
    const {{ bySolar }} = require('iztro').astro;
    const a = bySolar('{year}-{month}-{day}', {time_index}, '{gender_js}', true, 'zh-CN');
    const rd = (a.rawDates && a.rawDates.lunarDate) || null;
    console.log(JSON.stringify({{
        soul: a.earthlyBranchOfSoulPalace,
        body: a.earthlyBranchOfBodyPalace,
        wuxing: a.fiveElementsClass,
        natalYearStem: (a.rawDates && a.rawDates.chineseDate && a.rawDates.chineseDate.yearly) ? a.rawDates.chineseDate.yearly[0] : '',
        lunarDate: rd ? {{ year: rd.lunarYear, month: rd.lunarMonth, day: rd.lunarDay, isLeap: !!rd.isLeapMonth }} : null,
        soulStar: a.soul || '', bodyStar: a.body || '',
        solarDate: a.solarDate || '', lunarDateText: a.lunarDate || '',
        timeText: a.time || '', timeRange: a.timeRange || '',
        sign: a.sign || '', zodiac: a.zodiac || '',
        palaces: a.palaces.map(p => ({{
            name: p.name,
            branch: p.earthlyBranch,
            major: (p.majorStars||[]).map(s=>s.name),
            minor: (p.minorStars||[]).map(s=>s.name),
            stem: p.heavenlyStem,
            decadalRange: p.decadal?.range || [],
            decadalStem: p.decadal?.heavenlyStem || '',
            adjective: (p.adjectiveStars||[]).map(s=>s.name),
            starDetail: []
                .concat((p.majorStars||[]).map(s => ({{ name: s.name, kind: 'major', brightness: s.brightness || '', mutagen: s.mutagen || '' }})))
                .concat((p.minorStars||[]).map(s => ({{ name: s.name, kind: 'minor', brightness: s.brightness || '', mutagen: s.mutagen || '' }}))),
            changsheng12: p.changsheng12 || '', boshi12: p.boshi12 || '',
            jiangqian12: p.jiangqian12 || '', suiqian12: p.suiqian12 || '',
            isBody: !!p.isBodyPalace, isOriginal: !!p.isOriginalPalace,
            ages: p.ages || [],
        }}))
    }}));
    '''
    
    proc = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
    )
    
    if proc.returncode != 0:
        raise RuntimeError(f"iztro bySolar failed: {proc.stderr}")
    
    return json.loads(proc.stdout)


def solar_to_chart(solar_input: SolarInput, raw_result: dict) -> ZiweiChart:
    """将 bySolar 结果转换为 ZiweiChart（与 full_chart 同一后处理口径）

    Z-ACC(2026-11-04) 修复：此前本路径只做字段搬运，缺
      ① 命宫空宫借对宫（DECISION-009 / 倪海厦约束9，任何空宫必借对宫论事）
      ② 生年四化入命宫（soul_palace_sihua 恒为 []，证据生产者该分支恒空转）
      ③ Z39 亮度表注入（沿线使用 iztro 原始亮度，与 full_chart 不一致）
      ④ 天刑/天姚（月系安星，full_chart 有、本路径无）
      ⑤ 生年斗君
    → 同一个人经阴历入口与阳历入口得到两张不同的盘。现统一调用
      ziwei_engine.postprocess_natal_palaces（单一实现）。
    """
    from .ziwei_engine import CHINESE_STAR_TO_KEY, postprocess_natal_palaces

    BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    KEY_TO_CHINESE = {v: k for k, v in CHINESE_STAR_TO_KEY.items()}

    soul_branch = raw_result.get('soul', '')
    body_branch = raw_result.get('body', '')
    wuxing = raw_result.get('wuxing', '')
    natal_stem = raw_result.get('natalYearStem', '') or ''

    # ── 1) 还原成中文盘面（与 full_chart 同结构），交给统一后处理 ──
    raw_palaces = raw_result.get('palaces') or []
    if isinstance(raw_palaces, dict):      # 原生后端（native_raw_chart）为 dict 形态
        raw_palaces = [dict(p, name=name) for name, p in raw_palaces.items()]
    palaces_zh: dict[str, dict] = {}
    for p in raw_palaces:
        name = p.get('name', '')
        if not name:
            continue
        palaces_zh[name] = {
            'stem': p.get('stem', ''),
            'branch': p.get('branch', ''),
            'major': list(p.get('major', []) or []),
            'minor': list(p.get('minor', []) or []),
            'decadalRange': p.get('decadalRange', []),
            'decadalStem': p.get('decadalStem', ''),
            'adjective': p.get('adjective', []) or [],
            'starDetail': list(p.get('starDetail', []) or []),
            'changsheng12': p.get('changsheng12', ''),
            'boshi12': p.get('boshi12', ''),
            'jiangqian12': p.get('jiangqian12', ''),
            'suiqian12': p.get('suiqian12', ''),
            'isBody': p.get('isBody', False),
            'isOriginal': p.get('isOriginal', False),
            'ages': p.get('ages', []) or [],
        }

    lunar = raw_result.get('lunarDate') or {}
    lunar_date = None
    if lunar and lunar.get('year'):
        month = int(lunar.get('month') or 1)
        lunar_date = (int(lunar['year']), -month if lunar.get('isLeap') else month,
                      int(lunar.get('day') or 1))

    facts = {'soul_keys': [], 'soul_sihua': [], 'doujun_palace': ''}
    if lunar_date:
        facts = postprocess_natal_palaces(
            palaces_zh,
            soul_branch=soul_branch,
            natal_stem=natal_stem,
            lunar_date=lunar_date,
            hour=solar_input.hour,
        )
    else:
        logger.warning("ZiweiSolarAdapter: raw 缺 lunarDate，跳过盘面后处理（借星/四化/亮度/斗君 未启用）")

    # ── 2) 组装对外 palace_data（主星保持拼音键，兼容既有消费方）──
    palace_data = {}
    for name, pdata in palaces_zh.items():
        major_keys = [CHINESE_STAR_TO_KEY.get(s, s) for s in pdata['major']]
        palace_data[name] = {
            'branch': pdata['branch'],
            'stem': pdata['stem'],
            'major': major_keys,
            'minor': list(pdata['minor']),
            'decadal_range': pdata.get('decadalRange', []),
            'decadal_stem': pdata.get('decadalStem', ''),
            'adjective': pdata.get('adjective', []),
            'brightness': {CHINESE_STAR_TO_KEY.get(k, k): v
                           for k, v in (pdata.get('brightness') or {}).items()},
            'starDetail': list(pdata.get('starDetail') or []),
            'changsheng12': pdata.get('changsheng12', ''),
            'boshi12': pdata.get('boshi12', ''),
            'jiangqian12': pdata.get('jiangqian12', ''),
            'suiqian12': pdata.get('suiqian12', ''),
            'isBody': pdata.get('isBody', False),
            'isOriginal': pdata.get('isOriginal', False),
            'ages': pdata.get('ages', []),
        }

    main_stars = list(facts.get('soul_keys') or [])
    main_star = main_stars[0] if main_stars else ''

    return ZiweiChart(
        soul_palace_main_star=main_star,
        soul_palace_main_stars=main_stars,
        soul_palace_sihua=list(facts.get('soul_sihua') or []),
        palace_data={
            'five_elements_class': wuxing,
            'soul_earthly_branch': soul_branch,
            'body_earthly_branch': body_branch,
            'palaces': palace_data,
        },
        source='iztro',
        soul_earthly_branch=soul_branch,
        body_earthly_branch=body_branch,
        palaces=palace_data,
        fiveElementsClass=wuxing,
        birth_year=solar_input.year,
        gender=solar_input.gender,
        doujun_palace=facts.get('doujun_palace', ''),
        natal_year_stem=natal_stem,
        soul_star=raw_result.get('soulStar', ''), body_star=raw_result.get('bodyStar', ''),
        solar_date=raw_result.get('solarDate', ''), lunar_date_text=raw_result.get('lunarDateText', ''),
        time_text=raw_result.get('timeText', ''), time_range=raw_result.get('timeRange', ''),
        sign=raw_result.get('sign', ''), zodiac=raw_result.get('zodiac', ''),
    )


def native_solar_chart(year: int, month: int, day: int, hour: int,
                       gender: str = "male") -> dict:
    """原生后端（无 node/iztro）：阳历 → 农历（lunar_python）→ native_raw_chart。

    输出归一为 `solar_to_chart` 使用的 raw 形态（soul/body/wuxing/palaces 列表 + lunarDate）。
    """
    from lunar_python import Solar

    from .ziwei_natal import native_raw_chart

    lun = Solar.fromYmd(year, month, day).getLunar()
    lm = lun.getMonth()
    base = native_raw_chart((lun.getYear(), lm, lun.getDay()), hour, gender)
    return {
        "soul": base["soulPalaceBranch"],
        "body": base["bodyPalaceBranch"],
        "wuxing": base["fiveElementsClass"],
        "natalYearStem": base["natalYearStem"],
        "soulStar": base["soulStar"],
        "bodyStar": base["bodyStar"],
        "solarDate": f"{year}-{month}-{day}",
        "lunarDateText": base["lunarDateText"],
        "timeText": base["timeText"],
        "timeRange": base["timeRange"],
        "sign": base["sign"],
        "zodiac": base["zodiac"],
        "lunarDate": {"year": lun.getYear(), "month": abs(lm),
                      "day": lun.getDay(), "isLeap": lm < 0},
        "palaces": [dict(p, name=name) for name, p in base["palaces"].items()],
    }


class ZiweiSolarAdapter:
    """阳历输入的紫微斗数适配器

    使用 bySolar 函数，与倪海厦数据集保持一致。
    """

    def __init__(self, engine: Optional[ZiweiEngine] = None, policy: Optional[ZiweiCalculationPolicy] = None,
                 backend: str = "auto"):
        """backend:
        - "auto"（默认）：有 node_modules/iztro 走 iztro；缺失则自动退回原生实现
          （`ziwei_natal.native_raw_chart` + lunar_python 农历换算），不再 throw/stub。
        - "iztro" / "native"：强制指定后端。
        """
        if backend not in ("auto", "iztro", "native"):
            raise ValueError(f"backend 必须 auto/iztro/native，收到 {backend!r}")
        self._engine = engine
        self._backend = backend
        self.policy = policy if policy is not None else ZiweiCalculationPolicy()

    def _use_native(self) -> bool:
        if self._backend == "native":
            return True
        if self._backend == "iztro":
            return False
        return not (Path("node_modules") / "iztro").exists() or shutil.which("node") is None

    def compute(self, year_or_ctx, month: int = None, day: int = None,
                hour: int = None, gender: str = "male") -> ZiweiChart:
        """计算命盘 - 支持两种调用方式：compute(ctx) 或 compute(year, month, day, hour)

        Args:
            year_or_ctx: 阳历年(int) 或 CalculationContext对象
            month: 阳历月 (当year_or_ctx是int时必填)
            day: 阳历日 (当year_or_ctx是int时必填)
            hour: 出生时辰 (24h hour 或 timeIndex, 由 compute_via_solar 内部转换)
            gender: 性别 ("male"/"female")

        Returns:
            ZiweiChart 实例
        """
        # 支持两种调用方式
        if hasattr(year_or_ctx, 'birth_civil_datetime'):
            # 传入的是 CalculationContext
            ctx = year_or_ctx
            year = ctx.birth_civil_datetime.year
            month = ctx.birth_civil_datetime.month
            day = ctx.birth_civil_datetime.day
            hour = ctx.birth_civil_datetime.hour  # 24h hour, compute_via_solar 内部转 timeIndex
        else:
            year = year_or_ctx

        if self._use_native():
            raw = native_solar_chart(year, month, day, hour, gender)
        else:
            raw = compute_via_solar(year, month, day, hour, gender)
        return solar_to_chart(SolarInput(year, month, day, hour, gender), raw)
    
    @property
    def engine(self):
        if self._engine is None:
            from .ziwei_engine import ZiweiEngine
            self._engine = ZiweiEngine()
        return self._engine


__all__ = [
    'SolarInput',
    'compute_via_solar',
    'solar_to_chart',
    'ZiweiSolarAdapter',
    'ZiweiCalculationPolicy',
    'ZiweiAdapter',  # 别名兼容
]

# 别名兼容：ZiweiAdapter = ZiweiSolarAdapter
ZiweiAdapter = ZiweiSolarAdapter
