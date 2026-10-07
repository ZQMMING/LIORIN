"""紫微斗数适配器 — bySolar 模式

关键修改：使用 iztro 的 bySolar 函数（阳历输入），而非 byLunar。

依据：倪海厦《天纪》体系 + 官方数据集验证
- 数据集使用 bySolar(solarDate, hour, gender, isLeapMonth, locale)
- 我们的引擎必须对齐此行为
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Optional

from .ziwei_engine import ZiweiEngine, ZiweiChart, time_index_from_hour


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
    console.log(JSON.stringify({{
        soul: a.earthlyBranchOfSoulPalace,
        body: a.earthlyBranchOfBodyPalace,
        wuxing: a.fiveElementsClass,
        natalYearStem: (a.rawDates && a.rawDates.chineseDate && a.rawDates.chineseDate.yearly) ? a.rawDates.chineseDate.yearly[0] : '',
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
    """将 bySolar 结果转换为 ZiweiChart
    
    Args:
        solar_input: 阳历输入
        raw_result: bySolar 返回的原始结果
    
    Returns:
        ZiweiChart 实例
    """
    from .ziwei_engine import CHINESE_STAR_TO_KEY, SIHUA_NAMES
    
    # 地支映射
    BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 五行局名称映射
    WUXING_NAMES = {
        '水二局': '水二局',
        '木三局': '木三局',
        '金四局': '金四局',
        '土五局': '土五局',
        '火六局': '火六局',
    }
    
    soul_branch = raw_result.get('soul', '')
    body_branch = raw_result.get('body', '')
    wuxing = raw_result.get('wuxing', '')
    
    # 构建宫位数据
    palace_data = {}
    for p in raw_result.get('palaces', []):
        name = p.get('name', '')
        branch = p.get('branch', '')
        major = p.get('major', [])
        minor = p.get('minor', [])
        
        # 转换为主星 pinyin key
        major_keys = [CHINESE_STAR_TO_KEY.get(s, s) for s in major if CHINESE_STAR_TO_KEY.get(s)]
        # 辅星保留中文原名：CHINESE_STAR_TO_KEY 仅覆盖14主星，若用该表过滤会把
        # 天魁/左辅/禄存/擎羊等辅星全部过滤成空（端到端检验发现：阳历接入路径
        # 辅星全空，与农历主路径不一致）。辅星原样保留，与 full_chart 中文一致。
        minor_keys = list(minor)
        
        palace_data[name] = {
            'branch': branch,
            'major': major_keys,
            'minor': minor_keys,
            'decadal_range': p.get('decadalRange', []),
            'adjective': p.get('adjective', []),
            'starDetail': p.get('starDetail', []),
            'changsheng12': p.get('changsheng12', ''),
            'boshi12': p.get('boshi12', ''),
            'jiangqian12': p.get('jiangqian12', ''),
            'suiqian12': p.get('suiqian12', ''),
            'isBody': p.get('isBody', False),
            'isOriginal': p.get('isOriginal', False),
            'ages': p.get('ages', []),
        }
    
    # 命宫主星
    soul_palace = palace_data.get('命宫', {})
    main_stars = soul_palace.get('major', [])
    main_star = main_stars[0] if main_stars else ''
    
    # 构建 ZiweiChart：顶层字段是规则层 canonical contract，
    # palace_data 保留为旧调用方兼容结构。
    # Z52: 阳历接入路径同样透传农历界生年干（修 birth_year=阳历年 直推年干的分叉）
    natal_stem = raw_result.get('natalYearStem', '') or ''
    return ZiweiChart(
        soul_palace_main_star=main_star,
        soul_palace_main_stars=main_stars,
        soul_palace_sihua=[],
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
        natal_year_stem=natal_stem,
        soul_star=raw_result.get('soulStar', ''), body_star=raw_result.get('bodyStar', ''),
        solar_date=raw_result.get('solarDate', ''), lunar_date_text=raw_result.get('lunarDateText', ''),
        time_text=raw_result.get('timeText', ''), time_range=raw_result.get('timeRange', ''),
        sign=raw_result.get('sign', ''), zodiac=raw_result.get('zodiac', ''),
    )


class ZiweiSolarAdapter:
    """阳历输入的紫微斗数适配器

    使用 bySolar 函数，与倪海厦数据集保持一致。
    """

    def __init__(self, engine: Optional[ZiweiEngine] = None, policy: Optional[ZiweiCalculationPolicy] = None):
        self._engine = engine
        self.policy = policy if policy is not None else ZiweiCalculationPolicy()
    
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
