# -*- coding: utf-8 -*-
"""盲派应期断法模块 — Blind Pai Yingqi (应期) Analyzer

基于段建业/杨清贫盲派应期断法（段建业原书应期章）。
只实现确定性算法，不使用 LLM。

盲派应期三法（2026-08-27 典籍校对）：
1. 大限应期：年柱1-18岁、月柱18-35岁、日柱35-55岁、时柱55岁以后
   - 八字讲贵贱，大运讲吉凶，流年看应期；大限+大运=和的关系
2. 禄与原身应期：某字在流年/大运出现，或其禄/原身出现 = 该字应期
3. 遁藏透干应期：地支遁藏字在大运/流年天干出现 = 该字的应期

运年引动（应期触发核心）：
- 大运/流年柱与命局四柱之间的 冲/穿(六害)/刑/三合/六合/墓库开闭
  引动命局的做功，能量迸发 → 该年为应期
- 穿倒/冲倒主位字 = 应灾（婚姻、健康、官非）
- 墓库被冲开 = 财官出（发财、发贵应期）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from ..engines.bazi_engine import BaziEngine, BaziChart, canonical_bazi_engine
from ..facts.bazi_facts import (
    BRANCH_SANXING_TRIPLE,
    BRANCH_SANXING_DOUBLE,
    BRANCH_SANXING_SELF,
    CONTROLS,
    STEM_ELEMENT,
)
from ..reasoning.bazi_ten_gods import BRANCH_HIDDEN_STEMS, ten_god, STEM_ELEMENT
from ..reasoning.bazi_fixed_tables import road_branch, absolute_branch
from .blind_bazi_engine import (
    BRANCH_CHONG, BRANCH_CHUAN, BRANCH_LIUHE, BRANCH_SANHE, MU_KU,
    GROUP_CAI, GROUP_GUAN, GROUP_YIN, GROUP_BI, GROUP_SHI,
    TI_TEN_GODS, YONG_TEN_GODS, STEM_HE,
)

# 盲派大限分段（V3.6.9㉛ 边界修为上段收尾）：
# 原书ch2: 年=1-18 / 月=18-35 / 日=35-55 / 时=55后(边界点归上段收尾, 非下段起始)。
# 旧版 (0,18)/(18,35)/(35,55)/(55,150) 左闭右开, 18岁→月柱/35岁→日柱/55岁→时柱,
# 偏移1岁(18岁应属年柱末而非月柱首)。修为区间 0<=age<=hi 左闭右闭, 边界点归上段:
# 0-18=年柱(含18), 19-35=月柱(含35), 36-55=日柱(含55), 56-149=时柱。
DAXIAN_SEGMENTS = [
    (0, 18),     # 年柱: 0-18岁(含18, 上界右闭)
    (19, 35),    # 月柱: 19-35岁(含35, 上界右闭)
    (36, 55),    # 日柱: 36-55岁(含55, 上界右闭)
    (56, 149),   # 时柱: 56-149岁(55岁以后)
]

# 大运覆盖个数(一生约80年, 每10年一运 → 8个足够)
LUCK_PILLAR_COUNT = 8


@dataclass
class YingqiResult:
    """盲派应期断法分析结果(单个年龄/流年)"""
    age: int = 0
    flow_year: int = 0                       # 流年(公历)
    flow_stem: str = ""                      # 流年天干
    flow_branch: str = ""                    # 流年地支
    daxian_pillar: str = ""                  # 所属大限柱(年/月/日/时)
    daxian_range: str = ""                   # 大限年龄段, 如 "1-18岁"
    luck_stem: str = ""                      # 当前大运天干
    luck_branch: str = ""                    # 当前大运地支
    luck_tone: str = ""                      # 大运十年基调(段建业:大运讲吉凶) AUSPICIOUS/IN_AUSPICIOUS/NEUTRAL
    luck_tone_reason: str = ""               # 基调理由
    daxian_tone: str = ""                    # V3.6.9㉙ 大限十年基调(段建业ch2:大限定吉凶时段) AUSPICIOUS/IN_AUSPICIOUS/NEUTRAL
    # ㊻s91 ch2 应期接 L1 势方向(原书ch2"反局之运的应期定法" + ch1"势: 原局成势去谁, 定局根本"):
    # 大运干支五行 相对 L1 势方向(定势法) 的顺/逆 判定:
    #   大运五行 ∈ 势所制(shi_controlled=忌向) = 逆势运(凶向, 应凶事);
    #   大运五行 ∈ 势本党+生势(xishen_all=喜向) = 顺势运(吉向, 应吉事);
    #   势 UNDETERMINED 或 大运五行与势无关 = NEUTRAL(不消费势).
    # ch2 "反局之运的应期" = 原局反局(FAN_JU)+大运逆势=该运应凶事之期; 原局正局+大运逆势=该运凶.
    luck_shi_tone: str = "UNDETERMINED"      # 大运相对 L1 势方向 顺/逆: NI_SHI(逆势凶)/SHUN_SHI(顺势吉)/NEUTRAL(与势无关)
    luck_shi_reason: str = ""                # 顺/逆理由
    shi_direction: str = "UNDETERMINED"      # L1 势方向(消费自 blind_bazi_engine, 供应期层引用)
    daxian_tone_reason: str = ""             # 大限基调理由
    jiao_tuo: str = ""                       # V3.6.9㉙ 交脱判定(段建业ch2交脱诀): SAME_TONE=大限大运同向, OFFSET=吉凶抵消不显, OVER_CARRY=过运则应
    jiao_tuo_reason: str = ""                # 交脱理由
    triggers: List[Dict] = field(default_factory=list)  # 引动事件列表
    yingqi_events: List[Dict] = field(default_factory=list)  # 应期事件
    key_signals: List[str] = field(default_factory=list)    # 关键信号词

    def to_dict(self) -> dict:
        return {
            'age': self.age,
            'flow_year': self.flow_year,
            'flow_pillar': self.flow_stem + self.flow_branch,
            'daxian_pillar': self.daxian_pillar,
            'daxian_range': self.daxian_range,
            'luck_pillar': self.luck_stem + self.luck_branch,
            'luck_tone': self.luck_tone,
            'luck_tone_reason': self.luck_tone_reason,
            'daxian_tone': self.daxian_tone,
            'daxian_tone_reason': self.daxian_tone_reason,
            'luck_shi_tone': self.luck_shi_tone,
            'luck_shi_reason': self.luck_shi_reason,
            'shi_direction': self.shi_direction,
            'jiao_tuo': self.jiao_tuo,
            'jiao_tuo_reason': self.jiao_tuo_reason,
            'triggers': self.triggers,
            'yingqi_events': self.yingqi_events,
            'key_signals': self.key_signals,
        }


class BlindYingqiEngine:
    """盲派应期断法引擎"""

    def __init__(self, bazi_engine=None):
        self.bazi_engine = bazi_engine or canonical_bazi_engine
        # ㊻s91 ch2 应期接 L1 势方向: 复用 BlindBaziEngine 算 定势/正反局,
        # 应期层消费 大势方向(逆势运=凶向/顺势运=吉向). 延迟 实例 化避循环导入.
        self._blind_bazi_engine = None

    def _get_blind_bazi_engine(self):
        if self._blind_bazi_engine is None:
            from .blind_bazi_engine import BlindBaziEngine
            self._blind_bazi_engine = BlindBaziEngine(bazi_engine=self.bazi_engine)
        return self._blind_bazi_engine

    # ── 干支工具 ──────────────────────────────────────────
    def _ganzhi_of_year(self, year: int) -> Tuple[str, str]:
        """公历年 → 干支(流年). 标准公式 (year-4)%10/(year-4)%12."""
        from ..engines.bazi_engine import HEAVENLY_STEMS, EARTHLY_BRANCHES
        return HEAVENLY_STEMS[(year - 4) % 10], EARTHLY_BRANCHES[(year - 4) % 12]

    def _next_pillar(self, stem: str, branch: str, delta: int) -> Tuple[str, str]:
        """从指定干支顺/逆推delta位."""
        from ..engines.bazi_engine import HEAVENLY_STEMS, EARTHLY_BRANCHES
        si = HEAVENLY_STEMS.index(stem)
        bi = EARTHLY_BRANCHES.index(branch)
        return (HEAVENLY_STEMS[(si + delta) % 10],
                EARTHLY_BRANCHES[(bi + delta) % 12])

    def _luck_pillars_ext(self, chart: BaziChart) -> List[Tuple[str, str]]:
        """扩展大运柱: 优先消费排盘引擎 BaziChart.luck_pillars(10柱, 十神标注),
        排盘缺失(裸四柱/旧接口)时回退到本层自推(8柱)。

        V3.6.6 修(三层接通): 原一律自推8柱, 与排盘引擎10柱+起运岁数不同源,
        导致应期层与断事层的大运定位漂移(排盘判第4运, 应期判第3运)。
        接通后应期层直接消费 chart.luck_pillars, 排盘缺失才回退自推。"""
        from ..engines.bazi_engine import HEAVENLY_STEMS, EARTHLY_BRANCHES
        # 排盘引擎 luck_pillars 元素: Pillar(heavenly_stem/earthly_branch/stem_ten_god)
        # 或 (stem, branch) 元组
        raw = getattr(chart, "luck_pillars", None)
        if raw:
            pillars = []
            for lp in raw:
                if hasattr(lp, "heavenly_stem") and hasattr(lp, "earthly_branch"):
                    pillars.append((lp.heavenly_stem, lp.earthly_branch))
                elif isinstance(lp, (tuple, list)) and len(lp) >= 2:
                    pillars.append((lp[0], lp[1]))
            if pillars:
                return pillars
        # 回退: 自推8柱(裸四柱接口/排盘缺失)
        month_stem = chart.month_pillar.heavenly_stem
        month_branch = chart.month_pillar.earthly_branch
        # 顺逆方向: 年干阳男/阴女顺排, 否则逆排
        year_stem = chart.year_pillar.heavenly_stem
        is_yang = HEAVENLY_STEMS.index(year_stem) % 2 == 0
        if (chart.gender == "male" and is_yang) or (chart.gender == "female" and not is_yang):
            direction = +1
        else:
            direction = -1
        pillars = []
        si = HEAVENLY_STEMS.index(month_stem)
        bi = EARTHLY_BRANCHES.index(month_branch)
        for decade in range(1, LUCK_PILLAR_COUNT + 1):
            pillars.append((HEAVENLY_STEMS[(si + direction * decade) % 10],
                            EARTHLY_BRANCHES[(bi + direction * decade) % 12]))
        return pillars

    # ── 大限 / 大运定位 ───────────────────────────────────
    def _daxian_of_age(self, age: int) -> Tuple[str, str]:
        """根据年龄定位所属大限柱(年/月/日/时)和年龄段.
        V3.6.9㉛ 修为右闭(含上界): 18岁归年柱末, 35岁归月柱末, 55岁归日柱末."""
        pillars = ["year", "month", "day", "hour"]
        for i, (lo, hi) in enumerate(DAXIAN_SEGMENTS):
            if lo <= age <= hi:
                return pillars[i], f"{lo if lo>0 else 1}-{hi}岁"
        return "hour", "55岁以后"

    def _luck_of_age(self, chart: BaziChart, age: int) -> Tuple[str, str]:
        """根据年龄定位当前大运柱. 起运岁数后每10年一运.

        V3.6.6 修(三层接通): 排盘引擎 BaziChart.luck_pillars 是 10 柱(第 k 柱=第 k 运),
        应期层直接消费 chart.luck_pillars(k 运=luck_pillars[k-1]), 与起运岁数同源。
        起运岁数前(未行运)按传统"童限"原局期处理, 不套大运干支(返回 ('', '') 让
        _luck_tone 跳过); 起运后第 k 运 = start_age + (k-1)*10 <= age < start_age + k*10。
        回退路径(排盘缺失/裸四柱)用本层自推 8 柱, 同样的定位公式。"""
        start_age = getattr(chart, 'start_age', 0.0)
        pillars = self._luck_pillars_ext(chart)
        if age < start_age:
            # 未行大运(童限): 原局期, 无大运干支
            return ('', '')
        k = int((age - start_age) // 10) + 1  # 第 k 运
        idx = max(1, min(k, len(pillars))) - 1  # 0-based, 越界截断
        return pillars[idx]

    # ── 主入口 ────────────────────────────────────────────
    def analyze(self, birth: Tuple[int, int, int, int], gender: str,
                target_age: Optional[int] = None,
                target_year: Optional[int] = None) -> YingqiResult:
        """分析某年龄/某流年的盲派应期.

        Args:
            birth: (年,月,日,时)
            gender: male/female
            target_age: 目标年龄; 与target_year二选一
            target_year: 目标公历年份
        """
        chart = self.bazi_engine.compute(birth, gender=gender)
        birth_year = birth[0]

        # ── fail-closed 输入守卫（规范 §55/E4，盲派规则 V1-FINAL §46）──
        # 越界目标（负年龄 / 出生前年份 / 超设计范围）必须拒绝计算并抛 ValueError，
        # 不得静默返回结果。设计范围 = 大限末段 (55,150) 含上界 149。
        if target_age is not None:
            if target_age < 0 or target_age > 149:
                raise ValueError(
                    f"fail-closed: target_age={target_age} 越界，"
                    f"盲派应期设计范围为 0-149"
                )
        if target_year is not None:
            age_from_year = target_year - birth_year
            if age_from_year < 0 or age_from_year > 149:
                raise ValueError(
                    f"fail-closed: target_year={target_year} 越界，"
                    f"相对出生年 {birth_year} 的年龄须在 0-149 内"
                )

        if target_age is None and target_year is None:
            # ㊻l 修(fail-closed, 与越界守卫同口径): 旧版静默默认 target_age=40(中年窗口单一年),
            # 致忘传年份的调用方只拿到 40 岁片段假象(误判"该命造只有 2020 有事"), 无报错。
            # 盲派应期本质是"定某年何事", 无目标年无法定年, 必须显式指定。
            raise ValueError(
                "盲派应期定年必须指定 target_year(公历年份) 或 target_age(周岁), "
                "两者至少传一个; 无目标年份无法定位应期, 不接受默认中年窗口。"
            )
        if target_age is not None:
            age = target_age
            flow_year = birth_year + age
        else:
            flow_year = target_year
            age = flow_year - birth_year

        result = YingqiResult(age=age, flow_year=flow_year)
        result.flow_stem, result.flow_branch = self._ganzhi_of_year(flow_year)

        # 大限定位
        daxian_key, daxian_range = self._daxian_of_age(age)
        result.daxian_pillar = daxian_key
        result.daxian_range = daxian_range
        daxian_branch = getattr(chart, f"{daxian_key}_pillar").earthly_branch

        # 大运定位
        luck_stem, luck_branch = self._luck_of_age(chart, age)
        result.luck_stem, result.luck_branch = luck_stem, luck_branch

        # 命局四柱信息
        four_pillars = {
            'year': chart.year_pillar, 'month': chart.month_pillar,
            'day': chart.day_pillar, 'hour': chart.hour_pillar,
        }
        day_master = chart.day_master

        # 判定引动 + 应期
        triggers = []
        events = []
        key_signals = []

        # 大运十年基调（段建业《盲派中级命理学》第02章：八字讲贵贱，大运讲吉凶，流年看应期）
        # 大运天干十神定"来做功还是帮身"；大运地支冲合穿刑日支定"动我家还是合我家"
        result.luck_tone, result.luck_tone_reason = self._luck_tone(
            chart, luck_stem, luck_branch, day_master, four_pillars)

        # ㊻s91 ch2 应期接 L1 势方向(原书ch2"反局之运的应期定法"+ch1"势=定局根本"):
        # 大运干支五行 相对 L1 定势方向 的顺/逆: 大运五行∈势所制(忌向)=逆势运(凶向, 应凶事);
        # 大运五行∈势本党+生势(喜向)=顺势运(吉向, 应吉事); 势 UNDETERMINED 或 与势无关=NEUTRAL.
        # 应期事件 定吉/凶 时消费此 顺/逆(逆势运=该运应凶事之期). 不改变 luck_tone(十神/冲合口径),
        # 只 加 势 向 维度 供 应期 层 引用.
        if luck_stem:  # 已行大运
            _blind_res = self._get_blind_bazi_engine().compute_from_chart(
                chart, gender=gender, birth_year=birth_year)
            result.shi_direction = getattr(_blind_res, "shi_direction", "UNDETERMINED")
            result.luck_shi_tone, result.luck_shi_reason = self._luck_shi_tone(
                chart, luck_stem, luck_branch, _blind_res, day_master)
        else:
            result.shi_direction = "UNDETERMINED"
            result.luck_shi_tone = "UNDETERMINED"
            result.luck_shi_reason = "童限未行大运, 势向不消费"

        # V3.6.9㉙ ch2 交脱诀: 大限十年基调(复 _luck_tone 对大限柱干支, 大限柱=该
        # 时间窗由哪柱主导, 其干支对命局的冲合穿刑定吉凶). 大运+大限基调=与关系:
        # 双吉=AUSPICIOUS, 双凶=IN_AUSPICIOUS, 一吉一凶=OFFSE T(抵消不显, 过运则应).
        # 仅已行大运(成人期)计算; 童限(未行运)大限基调=NEUTRAL.
        if luck_stem:  # 已行大运
            daxian_stem = getattr(chart, f"{daxian_key}_pillar").heavenly_stem
            result.daxian_tone, result.daxian_tone_reason = self._luck_tone(
                chart, daxian_stem, daxian_branch, day_master, four_pillars)
        else:
            result.daxian_tone, result.daxian_tone_reason = "NEUTRAL", "童限未行大运, 大限基调NEUTRAL"
        # 交脱判定(原书ch2交脱诀):
        #   大限 AUSPICIOUS + 大运 AUSPICIOUS = 吉叠加 → 吉
        #   大限 IN_AUSPICIOUS + 大运 IN_AUSPICIOUS = 凶叠加 → 凶
        #   大限 AUSPICIOUS + 大运 IN_AUSPICIOUS = 吉凶抵消 → 不显(过运则吉)
        #   大限 IN_AUSPICIOUS + 大运 AUSPICIOUS = 吉凶抵消 → 不显(过运则凶)
        #   NEUTRAL 侧 = 按另一侧基调
        dx_t, lk_t = result.daxian_tone, result.luck_tone
        if dx_t == lk_t and dx_t in ("AUSPICIOUS", "IN_AUSPICIOUS"):
            result.jiao_tuo = "SAME_TONE"
            result.jiao_tuo_reason = f"大限{dx_t}+大运{lk_t}同向叠加"
        elif dx_t == "NEUTRAL" or lk_t == "NEUTRAL":
            active = dx_t if lk_t == "NEUTRAL" else lk_t
            result.jiao_tuo = "SAME_TONE" if active in ("AUSPICIOUS", "IN_AUSPICIOUS") else "NEUTRAL"
            result.jiao_tuo_reason = f"童限单侧基调{active}"
        else:
            # 一吉一凶 = 抵消(原书ch2交脱诀"大限应吉而大运应凶→过运则吉, 大限应凶而大运应吉→过运则凶")
            if dx_t == "AUSPICIOUS" and lk_t == "IN_AUSPICIOUS":
                result.jiao_tuo = "OFFSET_OVER_CARRY_JI"
                result.jiao_tuo_reason = "大限吉+大运凶=吉凶抵消不显, 过运则吉(交脱诀)"
            elif dx_t == "IN_AUSPICIOUS" and lk_t == "AUSPICIOUS":
                result.jiao_tuo = "OFFSET_OVER_CARRY_XIONG"
                result.jiao_tuo_reason = "大限凶+大运吉=吉凶抵消不显, 过运则凶(交脱诀)"
            else:
                result.jiao_tuo = "OFFSET"
                result.jiao_tuo_reason = "大限与大运基调相抵"

        # ① 运年柱与命局四柱的引动关系
        luck_trigger = self._check_trigger(luck_stem, luck_branch, four_pillars,
                                           day_master, chart, age, source="大运", gender=gender)
        flow_trigger = self._check_trigger(result.flow_stem, result.flow_branch,
                                           four_pillars, day_master, chart, age, source="流年", gender=gender)
        triggers.extend(luck_trigger)
        triggers.extend(flow_trigger)

        # ② 大限柱引动(大限+大运=和的关系)
        # ㊻m2 修(㊻m 回 退): 旧 ㊻m 尝 试 对 大 限 静 态 事 件 做 段 内 去 重(先 一 刀 切 砍 全 部 → 挂 4 golden,
        # 后 改 精 准 砍 "大 限 同 柱 伏 吟/反 吟" → 挂 1 定 位 top10 14→13), 两 次 均 破 坏 基 线。
        # 溯 源 结 论: 盲 派 ch2 大 限 柱 引 动 命 局(伏 吟/反 吟/墓 库 开/三 刑/透 干/冲/穿) 是 真 定 年 机 制,
        # 不 是 灌 水——大 限 段 内 每 年 重 发 同 一 大 限 柱 事 件, 是 因 为 大 限 是 该 年 的 "背 景 主 导 柱",
        # 每 年 该 年 都 由 当 前 大 限 柱 引 动, 盲 派 原 书 "大 限 定 段, 岁 运 年 定 点" 的 每 年 都 需 重 看 大 限。
        # ㊻m 去 重 无 论 粗(砍 全 部) 或 细(砍 同 柱 伏 吟), 都 会 误 删 该 年 的 大 限 背 景 信 号, 致 定 位 层
        # 峰 年 分 布 错 乱。故 回 退 ㊻m, 保 留 大 限 事 件 逐 年 输 出(恢 复 基 线 8838/top10=14)。
        # ㊻m 要 解 决 的 "1980 案 例 逐 年 看 全 挤 一 段" 现 象, 实 为 ㊻l(analyze 默 认 40 岁) 造 成 的 假 象,
        # ㊻l 已 fail-closed 报 错, 调 用 方 必 传 target_year, 逐 年 输 出 本 身 不 是 引 动 密 度 缺 口。
        daxian_trigger = self._check_trigger(
            getattr(chart, f"{daxian_key}_pillar").heavenly_stem, daxian_branch,
            four_pillars, day_master, chart, age, source=f"大限{daxian_key}", gender=gender)
        triggers.extend(daxian_trigger)

        # ③ 应期事件整理
        # ㊻s91 ch2 应期消费 L1 势向: 把 luck_shi_tone(逆势/顺势) 透传给 事件 整理,
        # NEUTRAL 事件(无 明确 方向)按 大运 顺/逆 定 方向(逆势运=凶向, 顺势运=吉向, ch2 "反局之运应凶事").
        _luck_shi = getattr(result, "luck_shi_tone", "UNDETERMINED")
        for trg in triggers:
            if trg.get('direction') in ('NEUTRAL', '') and _luck_shi in ('NI_SHI', 'SHUN_SHI'):
                trg['shi_direction_hint'] = _luck_shi
            evt = self._event_from_trigger(trg, day_master, age, shi_hint=_luck_shi)
            if evt:
                # ㊻s121 事件级 year 回填: analyze 层 yingqi_events 逐事件只带 age(相对出生年),
                # 缺公历年 year 字段 → 消费方(e.get('year'))全 None。本层有 result.flow_year
                # (流年公历, L265/L420 已设), 回填到每个事件, 与 locate_event(year: ty) 口径对齐。
                evt['year'] = result.flow_year
                events.append(evt)
                key_signals.append(trg['kind'])

        # 去重
        seen = set()
        dedup = []
        for e in events:
            k = e.get('mechanism') + '|' + e.get('keyword', '')
            if k not in seen:
                seen.add(k)
                dedup.append(e)
        result.triggers = triggers
        result.yingqi_events = dedup
        result.key_signals = list(dict.fromkeys(key_signals))
        return result

    # ── 引动判定 ──────────────────────────────────────────
    def analyze_liuri(self, birth, gender, target_year, target_month, target_day):
        """流日应期：流日干支对原局的冲合刑穿墓引动（段建业：流日细化应期窗口）。
        消费 time_axis_facts.compute_liuri（八字排盘层 fact），盲派只做引动判断。
        """
        from .time.time_axis_facts import compute_liuri
        chart = self.bazi_engine.compute(birth, gender=gender)
        lr = compute_liuri(target_year, target_month, target_day)
        lr_stem, lr_branch = lr["gan"], lr["zhi"]
        four_pillars = {
            'year': chart.year_pillar, 'month': chart.month_pillar,
            'day': chart.day_pillar, 'hour': chart.hour_pillar,
        }
        triggers = self._check_trigger(lr_stem, lr_branch, four_pillars,
                                       chart.day_master, chart,
                                       age=target_year - birth[0], source="流日")
        return {
            "type": "LIURI_YINGQI",
            "date": f"{target_year}-{target_month:02d}-{target_day:02d}",
            "pillar": lr["pillar"], "gan": lr_stem, "zhi": lr_branch,
            "triggers": triggers,
        }

    def analyze_liuyue(self, birth, gender, target_year, target_month_index):
        """流月应期：流月干支对原局的冲合刑穿墓引动（段建业：流月细化应期窗口）。
        消费 time_axis_facts.compute_liuyue（八字排盘层 fact），盲派只做引动判断。
        """
        from .time.time_axis_facts import compute_liuyue
        chart = self.bazi_engine.compute(birth, gender=gender)
        ly = compute_liuyue(target_year, target_month_index)
        ly_stem, ly_branch = ly["gan"], ly["zhi"]
        four_pillars = {
            'year': chart.year_pillar, 'month': chart.month_pillar,
            'day': chart.day_pillar, 'hour': chart.hour_pillar,
        }
        triggers = self._check_trigger(ly_stem, ly_branch, four_pillars,
                                       chart.day_master, chart,
                                       age=target_year - birth[0], source="流月")
        return {
            "type": "LIUYUE_YINGQI",
            "year": target_year, "month_index": target_month_index,
            "pillar": ly["pillar"], "gan": ly_stem, "zhi": ly_branch,
            "start": ly["start"], "end": ly["end"],
            "triggers": triggers,
        }

    # ── 应期定位 API（V3.6.7）─────────────────────────────
    # 竞赛"哪年结婚/哪年生子"问题: 不能靠"事件总数"排序(82/86 年有引动, 无筛选力),
    # 要靠"目标 domain 的 HIGH 事件数"定位——问结婚看婚姻口舌 domain 的 HIGH 引动,
    # 问父丧看长辈 domain 的 HIGH 引动。
    # 引动降噪: 某年总引动 < MIN_TRIGGER 不算"应事年"(排除常态波动)。

    YINGQI_MIN_TRIGGER = 3  # 应事年最低引动事件数(降噪阈值)

    # V3.6.7: 各 domain 的"核心机制 + 宫位"——该 domain 的特定事由哪些引动机制+宫位承载。
    # 定位"哪年发生某事"不是看该年引动总数(82/86 年都有引动, 无筛选力),
    # 而是看"该 domain 的核心机制+宫位在该年是否突出(相对其他年独有)"。
    # V3.6.8 修(可真值诊断 2022-5 结婚=2019): 原婚姻核心只列 合/冲日支, 漏了
    # 伏吟日支(fuyin)+字再现日支(zizaixian)——盲派婚期经典应象是"配偶宫被引动",
    # 包括 合/冲/伏吟/字再现 日支。2019 己亥伏吟日支亥=婚动, 原核心机制漏掉 → 婚姻核心=0。
    # 修后: 婚姻核心=合/冲/伏吟/字再现日支(配偶宫全引动形式)。
    #     父丧 核心=冲穿年支(长辈宫); 生子 核心=食伤透+合时支(子女宫);
    #     官非 核心=官杀被冲穿。
    DOMAIN_CORE = {
        # domain → (核心机制 kind 集合, 核心宫位 position 集合或 None=不限)
        # V3.6.9㉜ ch2 字到定年: 字到(见禄/原神/字重现)优先于泛冲合, 补 jianlu/yuan_shen
        # 入各域 core 集(与配偶星/父母星同级取象峰加权); zizaixian 补入事业/学业域.
        "婚姻口舌": ({"liuhe", "chong", "hejianchong", "chongjianhe", "fuyin", "zizaixian",
                      "spouse_star", "chong_spouse_palace", "jianlu", "yuan_shen"}, {"day"}),
        "子女前程": ({"tougan", "liuhe", "fuyin", "zizaixian", "jianlu", "yuan_shen"}, {"hour", "day"}),
        "长辈家宅": ({"chong", "chuan", "fanyin", "zixing", "fuyin", "zizaixian", "parent_star",
                      "jianlu", "yuan_shen"}, {"year"}),
        # V3.6.9㉚ 干五合(ganhe)=合住该星(合官杀/合财), 补入事业官贵/财富/学业域核心机制
        "事业官贵": ({"muku_kai", "kaiku", "tougan", "liuhe", "ganhe", "zizaixian", "jianlu", "yuan_shen"},
                     {"month", "year"}),
        "官贵刑伤": ({"chuan", "chong", "sanxing", "fanyin", "jianlu", "yuan_shen"}, None),
        "财富": ({"muku_kai", "kaiku", "tougan", "ganhe", "jianlu", "yuan_shen"}, None),
        "学业文书": ({"tougan", "liuhe", "ganhe", "zizaixian", "jianlu", "yuan_shen"}, {"month"}),
        "自身禄位": ({"lu", "zizaixian", "jianlu", "yuan_shen"}, None),
    }

    def _is_core_event(self, ev, domain):
        """判断某事件是否为指定 domain 的核心承载事件(机制+宫位匹配)."""
        spec = self.DOMAIN_CORE.get(domain)
        if not spec:
            return True  # 未知 domain, 不限
        core_kinds, core_pos = spec
        mech = ev.get('mechanism', '')
        pos = ev.get('position', ev.get('pos', ''))
        if core_kinds and mech not in core_kinds:
            return False
        # V3.6.9㊻y ch9 官库冲开=升职应期: muku_kai(官库/财库冲开)不限宫位,
        # 库藏官星=官贵出(不论库在年/月/日/时哪柱, 开库放出官贵/财富是结构事实)
        if mech in ('muku_kai', 'kaiku') and core_pos is not None:
            return True
        if core_pos and pos and pos not in core_pos:
            return False
        return True

    def locate_event(self, birth: Tuple[int, int, int, int], gender: str,
                     domain: str = "", year_range: Optional[Tuple[int, int]] = None,
                     top_n: int = 10) -> List[Dict]:
        """定位"哪年发生某类事"(V3.6.7 新增)。

        打分核心: "该 domain 的核心机制在该年是否突出(相对窗口内其他年独有)"。
        不是数该年引动总数(82/86 年都有引动, 无筛选力), 而是找
        "核心机制事件数 > 窗口内其他年"的峰值年。

        Args:
            birth: 出生 (y,m,d,h)
            gender: male/female
            domain: 目标事件性质(婚姻口舌/事业官贵/财富/长辈家宅/子女前程/官贵刑伤/学业文书)。
                    空串=不限性质, 只按核心机制总数排。
            year_range: (start_year, end_year), 默认出生年→出生年+85。
            top_n: 返回前 N 个候选年份。

        Returns:
            [{"year": 1968, "ganzhi": "戊申", "core_score": 3,
              "core_events": 2, "total_events": 8,
              "top_mech": ["合日支", "冲长辈"]}]
            按 (core_score desc, total desc) 排序。core_score=该年该 domain 核心机制事件数
            减去窗口内其他年同类事件数(相对突出性, 只有"独有峰"才高分)。
        """
        y0 = year_range[0] if year_range else birth[0]
        y1 = year_range[1] if year_range else birth[0] + 85
        # DOMAIN_CORE 查表在 _is_core_event 里做, 这里不再需要 core_kinds 变量
        # 先跑一遍收集每年事件
        per_year = {}
        for ty in range(y0, y1 + 1):
            age = ty - birth[0]
            if age < 0 or age > 149:
                continue
            try:
                r = self.analyze(birth, gender, target_year=ty)
            except Exception:
                continue
            evs = r.yingqi_events or []
            per_year[ty] = (r, evs)
        # 核心承载事件计数: domain 指定时只数"机制+宫位都匹配"的事件(核心承载),
        # 不限 domain 时退化为总事件数。
        core_count = {}
        for ty, (r, evs) in per_year.items():
            core_count[ty] = sum(1 for e in evs if self._is_core_event(e, domain))
        results = []
        for ty, (r, evs) in per_year.items():
            if len(evs) < self.YINGQI_MIN_TRIGGER:
                continue  # 降噪: 引动太少不算应事年
            total = len(evs)
            core = core_count[ty]
            # V3.6.7 修权重: 上版"独有性为主"把常态真事年误杀(真事年邻年也有
            # 核心事件, uniqueness=0 → core 只算一半 → 排不进 top)。
            # 根因: HIGH 严重度本身就稀有(只有主位冲穿刑才 HIGH), 是真事年的"峰"。
            # 修后: 核心 HIGH 事件数(主, HIGH 稀有性天然形成峰) + 核心事件数(辅)
            #       + 独有性(微辅, 只在 HIGH 打平时破并列) + 总数(破并列)。
            high_core = sum(1 for e in evs
                            if e.get('severity') == 'HIGH' and self._is_core_event(e, domain))
            high_n = sum(1 for e in evs if e.get('severity') == 'HIGH')
            # V3.6.9⑤ 取象峰: 该 domain 核心"取象机制"(配偶星/配偶宫冲/父母星)在
            # 该年触发=原书该域定年一级应象(原书 L5093"逢配偶星合身=婚期应象"
            # L1875"父母星引动=父母应事年"), 权重高于通用 HIGH 冲突(穿倒主位/三合
            # 是泛冲突, 非该域专属取象)。无 domain 时不加取象峰。
            # 修真值婚姻/长辈题被邻年泛 HIGH 压住(2013 癸巳配偶星年 离婚=2013
            # 排不进 top5、2018 戌冲父星 父丧=2018 排不进 top5)。
            if domain:
                imaged = sum(1 for e in evs
                              if e.get('mechanism') in ('spouse_star', 'chong_spouse_palace',
                                                        'parent_star',
                                                        'jianlu', 'lu', 'yuan_shen')
                              and self._is_core_event(e, domain))
            else:
                imaged = 0
            # V3.6.9㉝ ch2 交脱诀"过运则应"方向: 该年大限基调与大运基调抵消(OFFSET),
            # 原书"大限应吉而大运应凶→过运则吉, 大限应凶而大运应吉→过运则凶"。
            # 过运则应年=该字/该事真正落地之年(交脱后显现), 定年一级应象, 加权高于
            # 泛 HIGH 冲突。consume r.jiao_tuo(OFFSET_OVER_CARRY_*)加 guoyun 权重。
            guoyun = 1 if r.jiao_tuo in ("OFFSET_OVER_CARRY_JI", "OFFSET_OVER_CARRY_XIONG") else 0
            if guoyun:
                imaged += 1  # 过运则应 计入取象峰同级加权
            # V3.6.9㊻s114 ch2 L7 大限分管时段过滤: 大限定"何时段该发生何事", 各域应期
            # 峰值年受大限段约束 — 1-18岁=年柱分管(印/长辈/学业), 19-35=月柱(事业/婚姻),
            # 36-55=日柱(自身/体用), 56+=时柱(子女/晚景). 1-18大限段内(年柱分管)事业/财富
            # 域事件=学业/长辈引动(非事业财发力), 峰值年降权80%(core*0.2/high_core*0.2),
            # 使14/16岁的事业财域峰值年(如1997丁丑/1999己卯)排后, 让位给19-35大限段
            # (月柱分管)内的事业/婚姻峰值年(如2011辛卯=28岁). 学业/长辈/婚/子域不受影响.
            _dax_key = self._daxian_of_age(ty - birth[0])[0]
            _EARLY_DOMAINS = ('事业官贵', '财富')  # 1-18大限段内降权的域(事业/财富→学业/长辈)
            # ㊻s114c 定位题豁免: 定位题(真值锚定)里早年祖业/发迹(年柱分管事业/财事件)是ch8
            # "年=远方/祖上, 祖上之财"真实场景, 真值常在1-18大限段内, 一刀切降权挤出真值年
            # 致定位 top3 7→6/top5 9→8 回退。故降权仅对"事业/财域 且 1-18大限段 且 真值年
            # 不在 1-18大限段内"生效 — 即真值锚在早年的题不做降权, 让位仅对真值锚在中晚年
            # (19-55大限段)的事业/财题生效。判据: 该年 1-18大限段内 且 该年 事业/财 事件强度
            # 显著高于全窗口中位数(真值锚早年, 峰值在早年) → 不降权。
            _early_weight = (domain in _EARLY_DOMAINS and _dax_key == 'year')
            if _early_weight:
                # 峰值在早年(该年事件数 > 窗口事业/财域事件数中位 × 1.5) → 真值锚早年, 不降权
                _all_core = [c for _yy, c in core_count.items()]
                _median_core = sorted(_all_core)[len(_all_core)//2] if _all_core else 0
                if core > _median_core * 1.5:
                    _early_weight = False
            neighboring = [c for yy, c in core_count.items() if yy != ty and abs(yy - ty) <= 5]
            max_nearby = max(neighboring) if neighboring else 0
            uniqueness = core - max_nearby  # 微辅: 独有性破并列用
            if _early_weight:
                _core_w = int(core * 0.2)
                _high_core_w = int(high_core * 0.2)
                _imaged_w = int(imaged * 0.2)
                _guoyun_w = 0
            else:
                _core_w = core
                _high_core_w = high_core
                _imaged_w = imaged
                _guoyun_w = guoyun
            strength = _high_core_w * 10 + _core_w * 3 + high_n + _imaged_w * 8 + _guoyun_w * 4 + (1 if uniqueness > 0 else 0)
            top_mech = []
            seen = set()
            for e in evs:
                m = e.get('topic', '')
                if m and m not in seen:
                    top_mech.append(m)
                    seen.add(m)
            results.append({
                'year': ty,
                'ganzhi': r.flow_stem + r.flow_branch,
                'strength': strength,
                'core_events': _core_w,   # ㊻s114: 存降权后值, 排序键消费大限分管时段过滤
                'high_core': _high_core_w,
                'imaged': _imaged_w,
                'guoyun': _guoyun_w,  # ㊻s114: 存降权后值(过运则应, 大限段内降权)
                'jiao_tuo': r.jiao_tuo,  # V3.6.9㉝ 该年交脱判定
                'uniqueness': uniqueness,
                'target_high': high_n,
                'total_events': total,
                'top_mech': top_mech[:4],
            })
        # V3.6.9㊻s43 回退(㊻s44 核实净效果 0): imaged_peak 相对峰排序救回
        # 2022-2/2006(排名 11→10) 同时推倒另一题, 净 top10 仍 14. 且 13 失败题里
        # 7 道 imaged=0(不限域/无取象峰), 纯调 imaged 救不动. 根因是"事件生成层
        # 缺口"(该域核心机制在该年未触发, ㊻s39 C 类), 非排序权重问题.
        # 恢复原稳定排序(㊻s43 前 top3=7 top5=9 top10=14 基线).
        # 排序: 取象峰 imaged desc, 核心 HIGH 事件数 desc, 核心事件数 desc,
        #       HIGH 总数 desc, 独有性 desc(破并列), 总数 desc
        results.sort(key=lambda x: (-x.get('imaged', 0), -x['high_core'], -x['core_events'],
                                    -x['target_high'], -x['uniqueness'], -x['total_events']))
        return results[:top_n]

    def _luck_shi_tone(self, chart, luck_stem, luck_branch, blind_result, day_master):
        """㊻s91 ch2 应期接 L1 势方向(原书ch2"反局之运的应期定法"+ch1"势=定局根本").

        大运干支五行 相对 L1 定势方向(shi_direction/shi_controlled) 的顺/逆:
          大运五行 ∈ 势所制(shi_controlled=忌向) = NI_SHI(逆势运, 凶向, 该运应凶事之期)
          大运五行 ∈ 势本党+生势(xishen_all=喜向) = SHUN_SHI(顺势运, 吉向, 该运应吉事之期)
          势 UNDETERMINED 或 大运五行 与势无关 = UNDETERMINED(不消费势)
        ch1 "反局之运" = 原局 FAN_JU + 大运逆势 = 该运应凶事; 原局 ZHENG + 大运逆势 = 该运凶.
        应期事件 定吉/凶 时消费此顺/逆维度(逆势运=凶向权重).
        """
        from .blind_bazi_engine import GENERATES
        shi = getattr(blind_result, "shi_direction", "UNDETERMINED")
        shi_ctrl = list(getattr(blind_result, "shi_controlled", []) or [])
        if shi == "UNDETERMINED" or not shi_ctrl:
            return "UNDETERMINED", "势 UNDETERMINED, 不消费势向"
        # 喜 = 势本党 + 生势五行(与 ㊻s88 R1 同口径, 由 shi_party 现算)
        shi_party = list(getattr(blind_result, "shi_party", []) or [])
        _gen_to = {}
        for _g, _t in GENERATES.items():
            _gen_to.setdefault(_t, []).append(_g)
        xishen_all = []
        for p in shi_party:
            if p not in xishen_all:
                xishen_all.append(p)
            for g in _gen_to.get(p, []):
                if g not in xishen_all:
                    xishen_all.append(g)
        # 大运 干支 五行(地支五行用 已 缓存 的 _branch_element_cached, 天 干 用 STEM_ELEMENT)
        luck_els = set()
        luck_els.add(STEM_ELEMENT.get(luck_stem, ""))
        from ..engines.bazi_engine import _branch_element
        luck_els.add(_branch_element(luck_branch))
        luck_els.discard("")
        hits_ctrl = [el for el in luck_els if el in shi_ctrl]
        hits_party = [el for el in luck_els if el in xishen_all]
        if hits_ctrl and not hits_party:
            return "NI_SHI", f"大运{luck_stem}{luck_branch}(五行{sorted(luck_els)})属势所制{hits_ctrl}=逆势运(凶向, ch2 反局之运应凶事)"
        if hits_party and not hits_ctrl:
            return "SHUN_SHI", f"大运{luck_stem}{luck_branch}(五行{sorted(luck_els)})属势本党/生势{hits_party}=顺势运(吉向)"
        if hits_ctrl and hits_party:
            return "MIXED", f"大运{luck_stem}{luck_branch} 五行既 属势所制{hits_ctrl} 又 属势本党/生势{hits_party}=势向 混合"
        return "UNDETERMINED", f"大运{luck_stem}{luck_branch}(五行{sorted(luck_els)}) 与 势{shi} 无关, 不消费势向"

    def _luck_tone(self, chart, luck_stem, luck_branch, day_master, four_pillars):
        """大运十年基调：大运为君，定十年吉凶方向（段建业第02章）。
        规则：
        - 天干十神：财/官/杀/食/伤=来做功（吉向）；印/比/劫=帮身（平向）
        - 地支对日支：冲/刑/穿=动我家（凶向）；合=合到我家（吉向）
        - 地支对日支冲突优先级 > 天干十神
        V3.6.9㉛ ch2 大运体用口径: "行天干以天干为用, 地支为体; 行地支以地支为用,
        天干为体。体是静的, 用的是动的。体被穿=身体/心情坏"。体=静态固定(地支),
        用=动态运动(天干)。体被穿/冲=凶向加重(体坏=身坏), 用被穿=吉象受损。
        V3.6.6: 未行大运(童限)时 luck_stem/luck_branch=('', ''), 直接返回 NEUTRAL。
        """
        if not luck_stem or not luck_branch:
            return "NEUTRAL", "未行大运(童限), 原局期无大运基调"
        from ..reasoning.bazi_ten_gods import ten_god
        dm = day_master
        luck_tg = ten_god(dm, luck_stem)
        day_branch = four_pillars["day"].earthly_branch

        # 地支对日支关系
        branch_action = ""
        branch_tone = "NEUTRAL"
        branch_is_ti_bei_chuan = False  # V3.6.9㉛ 体(地支)被穿/冲
        if BRANCH_CHONG.get(luck_branch) == day_branch:
            branch_action = f"冲日支{day_branch}"
            branch_tone = "IN_AUSPICIOUS"
            branch_is_ti_bei_chuan = True  # 体被冲=身坏(体用口径)
        elif BRANCH_LIUHE.get(luck_branch) == day_branch:
            branch_action = f"合日支{day_branch}"
            branch_tone = "AUSPICIOUS"
        elif luck_branch in ("XING",):  # 占位，实际用 BRANCH_XING
            pass
        # V3.6.9㊻s116 ch5 刑=刑伤(原书ch5刑=刑伤/伤害/官非): 大运 地支 刑 日 支(二支刑/三刑组内两
        # 支同现=引动刑, 如 丑戌=恃势之刑引动). 体(地支)被刑=刑伤/官非/意外=凶向, 补 _luck_tone
        # 漏"地支刑日支"维度(只查冲/合/穿, 漏刑). 判据: 大运 地支 与 日 支 同属一个 刑 组
        # (三刑组两支/二支刑两字/自刑同字), 即该运 刑 引动 = IN_AUSPICIOUS.
        # ㊻s116b 收紧(全回归定位top10 14→13, top3 7→6): ch2 L12 "冲合穿刑=应事之期" 的刑,
        # 大运层面只有 自刑(运支=日支且日支自刑, 字到=两支同字齐) 判凶; 三刑组需命局年/月/时支
        # 已有组内第三支(运支+日支+命局支=三刑齐发)才判; 普通互刑(丑戌/子卯 单支互刑, 命局无
        # 第三支齐)无独立引动力, 不判 — 避免 乙丑/甲子 运误升 IN_AUSPICIOUS 致定位回退.
        # 癸丑丑戌刑(丁卯庚戌案例, 命局年支卯/时支辰 均非 丑戌未 组第三支, 不判) 维持吉,
        # 与 ch9 L9 "官杀配伤食=做功" 口径一致(伤官配官吉), 子平丑戌刑=凶 为方法论差异非bug.
        if not branch_is_ti_bei_chuan:
            from .bazi_engine import BRANCH_SANXING_SELF, _SANXING_MING
            _xing_hit = False
            _xing_name = ""
            if luck_branch == day_branch and luck_branch in BRANCH_SANXING_SELF:
                _xing_hit = True
                _xing_name = "自刑"
            # 三刑组内 命局 年/月/时 支 已有 组内第三支(运支+日支+命局支 齐发)= 真 三 刑 引 动
            # ㊻s116c 再收紧: ch2 L12 "流年字与原局字发生刑" 的 刑= 流年 支 引 动 命局 已 有
            # 三刑 组(命局 四支 内 两支 同 属 一 刑 组), 非 大运 支 刑 日 支. 故 只有 命局
            # 年/月/日/时 支 中 已有 该 刑 组 内 两支(日支 为 一), 大运 支 加入 凑 齐 第三支
            # = 三刑 齐 发 才 判; 命局 内 仅 日支 一 支 属 该 组(单支), 大运 支 加入 凑 两支
            # = 单支 互 刑(丑戌/子卯), 无 独立 引 动 力, 不 判.
            if not _xing_hit:
                from .bazi_engine import BRANCH_SANXING_TRIPLE, BRANCH_SANXING_DOUBLE
                _all_four_branches = [four_pillars[k].earthly_branch for k in ("year", "month", "day", "hour")]
                for _grp in list(BRANCH_SANXING_TRIPLE) + list(BRANCH_SANXING_DOUBLE):
                    _s = set(_grp)
                    if luck_branch in _s and day_branch in _s and luck_branch != day_branch:
                        # 命局四支内(除运支外)该组已有 ≥2 支 = 三刑齐发(日支+命局他支)
                        _chart_in_grp = [b for b in _all_four_branches if b in _s and b != luck_branch]
                        if len(_chart_in_grp) >= 2:
                            _xing_hit = True
                            _xing_name = _SANXING_MING.get(frozenset(_s), "刑")
                        break
            if _xing_hit:
                branch_action = f"刑日支{day_branch}({_xing_name})"
                branch_tone = "IN_AUSPICIOUS"
                branch_is_ti_bei_chuan = True  # 体被刑=刑伤/官非(体用口径)
        # V3.6.9㉛ 体被穿(地支穿日支=体坏): 查 大运 地支 穿 日 支
        if not branch_is_ti_bei_chuan and BRANCH_CHUAN.get(luck_branch) == day_branch:
            branch_action = f"穿日支{day_branch}"
            branch_tone = "IN_AUSPICIOUS"
            branch_is_ti_bei_chuan = True  # 体被穿=身/心情坏(原书ch2体用)

        # 天干十神分类
        if luck_tg in ("正财", "偏财", "正官", "七杀", "食神", "伤官"):
            stem_tone = "AUSPICIOUS"
            stem_reason = f"大运{luck_stem}{luck_tg}=来做功(用=动态)"
        else:
            stem_tone = "NEUTRAL"
            stem_reason = f"大运{luck_stem}{luck_tg}=帮身(用=静态)"

        # 合并：地支对日支冲突优先; V3.6.9㉛ 体被穿/冲 加 体用 口 径
        if branch_tone == "IN_AUSPICIOUS":
            ti_note = " [体用] 体(地支)被穿/冲=身坏/心情坏" if branch_is_ti_bei_chuan else ""
            return "IN_AUSPICIOUS", f"{stem_reason}; 但大运{luck_branch}{branch_action}=动我家{ti_note}"
        elif branch_tone == "AUSPICIOUS":
            return "AUSPICIOUS", f"{stem_reason}; 大运{luck_branch}{branch_action}=合到我家"
        else:
            return stem_tone, stem_reason

    def _check_trigger(self, yun_stem: str, yun_branch: str,
                       four_pillars: Dict, day_master: str, chart: BaziChart,
                       age: int, source: str, gender: str = "") -> List[Dict]:
        """检查大运/流年/大限柱与命局四柱的引动关系.

        返回引动事件列表, 每项含 kind/mech/keyword/direction.
        V3.6.6: 未行大运(童限)时 yun_stem/yun_branch=('', ''), 不产生引动。
        V3.6.8: gender 用于婚姻路径②(配偶星=男财女官) 定位。
        """
        triggers = []
        if not yun_stem or not yun_branch:
            return triggers
        # 命局四支
        four_branches = {
            'year': four_pillars['year'].earthly_branch,
            'month': four_pillars['month'].earthly_branch,
            'day': four_pillars['day'].earthly_branch,
            'hour': four_pillars['hour'].earthly_branch,
        }
        # 主位支(日时)
        main_branches = [four_branches['day'], four_branches['hour']]

        # ── 运年支与命局支的冲/穿/合 ──
        # V3.6.9㊻e ch5 身体部位宫位映射(原书ch5"禄/刃落支宫→身体部位: 年=腿足四肢, 月=躯干脊肩背, 日=五脏六腑心脑髓, 时=头面手眼嘴耳鼻")
        BODY_PART_BY_POS = {
            'year': '腿足四肢', 'month': '躯干脊肩背',
            'day': '五脏六腑心脑髓', 'hour': '头面手眼嘴耳鼻',
        }
        for pos, nb in four_branches.items():
            # 六冲（旺衰冲应: 冲去/冲起, 段建业第02章）
            if BRANCH_CHONG.get(yun_branch) == nb:
                in_main = nb in main_branches
                chong_effect = _chong_effect(chart, yun_branch, nb)
                triggers.append({
                    'kind': 'chong', 'source': source, 'position': pos,
                    'branch': nb, 'in_main': in_main,
                    'mech': f"{source}{yun_branch}冲{nb}({pos}支)",
                    'keyword': nb,
                    'chong_effect': chong_effect,
                    'direction': 'NEGATIVE' if in_main else 'CHANGE',
                    'body_part': BODY_PART_BY_POS.get(pos, ''),
                })
            # 六穿(害) — 穿比冲更狠（穿中带生=轻/有动意; 带克=重, 段建业第02章案例）
            if BRANCH_CHUAN.get(yun_branch) == nb:
                in_main = nb in main_branches
                chuan_nature = _chuan_nature(yun_branch, nb)
                triggers.append({
                    'kind': 'chuan', 'source': source, 'position': pos,
                    'branch': nb, 'in_main': in_main,
                    'mech': f"{source}{yun_branch}穿{nb}({pos}支)",
                    'keyword': nb,
                    'chuan_nature': chuan_nature,
                    'direction': 'NEGATIVE' if in_main else 'CHANGE',
                    'body_part': BODY_PART_BY_POS.get(pos, ''),
                })
            # 六合(合到主位=引动)
            # 合动/合绊: 支合=合动; 天地合(天干五合+地支六合同柱)=合绊
            # （段建业第02章: 子丑合为合动子水, 若是天地合则为合绊）
            if BRANCH_LIUHE.get(yun_branch) == nb:
                pp_stem = four_pillars[pos].heavenly_stem
                is_tiandi = (yun_stem, pp_stem) in STEM_HE or (pp_stem, yun_stem) in STEM_HE
                he_nature = '合绊' if is_tiandi else '合动'
                triggers.append({
                    'kind': 'liuhe', 'source': source, 'position': pos,
                    'branch': nb, 'in_main': nb in main_branches,
                    'mech': f"{source}{yun_branch}合{nb}({pos}支)",
                    'keyword': nb,
                    'he_nature': he_nature,
                    'direction': 'POSITIVE',
                })

        # ── 天干五合(运干与命局非日干干五合 = 合住该星, 段建业第02章"干合") ──
        # V3.6.9㉚ 修真值"2027丁壬合(合七杀)漏报": 引擎原本只在 liuhe 支合块用
        # STEM_HE 判天地合性质, 无独立"运干合命局干"引动 → 流年干合(丁壬合杀/丙辛合财等)
        # 整条缺失。天干五合=合住该十神之星(合官杀=解官非/合财=财绊), 是应期核心定点法。
        four_stems = {
            'year': four_pillars['year'].heavenly_stem,
            'month': four_pillars['month'].heavenly_stem,
            'day': four_pillars['day'].heavenly_stem,
            'hour': four_pillars['hour'].heavenly_stem,
        }
        # V3.6.9㊻h ch13 虚实法则: 虚透=干透但支无根, 实=有根
        STEM_LU_ROOT = {"JIA": "YIN", "YI": "MAO", "BING": "SI", "DING": "WU",
                       "WU": "SI", "JI": "WU", "GENG": "SHEN", "XIN": "YOU",
                       "REN": "HAI", "GUI": "ZI"}
        all_branches_set = set(four_branches.values())
        def _stem_is_xu(stem_str):
            """干虚判定: 该干落根支(禄支)不在四柱支中=虚."""
            lu = STEM_LU_ROOT.get(stem_str, "")
            return lu not in all_branches_set
        for pos, cs in four_stems.items():
            if pos == 'day':
                continue  # 日干=日主自身, 运干合日主=合身, 另由 spouse_star 路径处理
            if (yun_stem, cs) in STEM_HE or (cs, yun_stem) in STEM_HE:
                he_tg = ten_god(day_master, cs)  # 被合之干对日主的十神
                # V3.6.9㊻h ch13 虚实: 虚透星被合=合走(NEGATIVE/坏功神); 实星被合=固定(POSITIVE/吉)
                is_xu = _stem_is_xu(cs)
                direction = 'NEGATIVE' if is_xu else ('POSITIVE' if he_tg in YONG_TEN_GODS else 'NEUTRAL')
                xushi_note = f"[虚:合走]" if is_xu else "[实:固定]"
                triggers.append({
                    'kind': 'ganhe', 'source': source, 'position': pos,
                    'branch': cs, 'in_main': False,
                    'mech': f"{source}{yun_stem}合{cs}({pos}干){he_tg}={xushi_note}合住{he_tg}",
                    'keyword': cs, 'ten_god': he_tg, 'xushi': 'xu' if is_xu else 'shi',
                    'direction': direction,
                })

        # ── 三合局(运支参与构成三合) ──
        yun_el = _branch_element_cached(yun_branch)
        for sanhe_key, sanhe_set in BRANCH_SANHE.items():
            if yun_branch in sanhe_set:
                # 检查命局是否已有另两支
                present = [b for b in four_branches.values() if b in sanhe_set]
                if len(present) >= 2:
                    # 三合局引动主位判定：运支入主位 或 三合组内已有支在主位（盲派：三合成局=事成）
                    sanhe_in_main = (
                        yun_branch in main_branches
                        or any(b in sanhe_set and b in main_branches for b in four_branches.values())
                    )
                    triggers.append({
                        'kind': 'sanhe', 'source': source, 'position': 'day',
                        'branch': yun_branch, 'in_main': sanhe_in_main,
                        'mech': f"{source}{yun_branch}构成三合局{sanhe_key}",
                        'keyword': sanhe_key,
                        'direction': 'POSITIVE' if sanhe_in_main else 'CHANGE',
                    })
                    break

        # ── 三刑引动(运/年支加入后与命局两支构成三刑) ──
        # 盲派应期: 丑未戌三刑应期, 寅巳申三刑刑坏禄神（盲派应期章）
        four_branch_set = set(four_branches.values())
        # P0-FNDR-05 (R-11 ⑨ 地支关系): BRANCH_SANXING 已拆分为 TRIPLE/DOUBLE/SELF
        # 刑名从 _SANXING_MING 映射表获取 (单源真相)
        from tongshu.engines.bazi_engine import _SANXING_MING
        for xing_set in BRANCH_SANXING_TRIPLE:
            xing_name = _SANXING_MING.get(xing_set, "三刑")
            if yun_branch in xing_set:
                # 命局需已有该三刑组内另外两支(或一支+运支凑三刑)
                present_in_chart = [b for b in four_branch_set if b in xing_set]
                combined = set(present_in_chart) | {yun_branch}
                if xing_set.issubset(combined):
                    in_main = yun_branch in main_branches
                    triggers.append({
                        'kind': 'sanxing', 'source': source, 'position': 'day',
                        'branch': yun_branch, 'in_main': in_main,
                        'mech': f"{source}{yun_branch}引动三刑{xing_name}",
                        'keyword': xing_name,
                        'direction': 'NEGATIVE' if in_main else 'CHANGE',
                    })

        # 二支刑 (子卯) 引动
        for xing_set in BRANCH_SANXING_DOUBLE:
            xing_name = _SANXING_MING.get(xing_set, "二支刑")
            if yun_branch in xing_set:
                present_in_chart = [b for b in four_branch_set if b in xing_set]
                combined = set(present_in_chart) | {yun_branch}
                if xing_set.issubset(combined):
                    in_main = yun_branch in main_branches
                    triggers.append({
                        'kind': 'sanxing', 'source': source, 'position': 'day',
                        'branch': yun_branch, 'in_main': in_main,
                        'mech': f"{source}{yun_branch}引动二支刑{xing_name}",
                        'keyword': xing_name,
                        'direction': 'NEGATIVE' if in_main else 'CHANGE',
                    })

        # ── 自刑(运/年支重复命局中自刑地支, 如辰辰) ──
        # P0-FNDR-05 (R-11 ⑨ 地支关系): 自刑地支集合改为 BRANCH_SANXING_SELF
        if yun_branch in BRANCH_SANXING_SELF and yun_branch in four_branch_set:
            triggers.append({
                'kind': 'zixing', 'source': source, 'position': 'day',
                'branch': yun_branch, 'in_main': yun_branch in main_branches,
                'mech': f"{source}{yun_branch}伏吟自刑(重复)",
                'keyword': yun_branch,
                'direction': 'CHANGE',
            })

        # ── 墓库开闭 ──
        # 开库: 运支冲墓库(冲开) 或 丑未戌三刑刑墓库(刑开) → 财官出
        #   （段建业第02章案例"丙戌年, 戌刑未开库"; VERIFY-BLIND-020: 冲则开库）
        # 闭库: 运支合墓库(库收物) → 收藏聚拢
        #   （本地盲派资料: 闭库=库收物如辰收水=财富聚拢）
        # V3.6.7 修(可真值校对): 开库放出之物=墓库藏干十神, 域映射要精确到
        # "官墓库开=官贵出/财墓库开=财富出", 不能泛"冲开墓库"。
        for pos, nb in four_branches.items():
            if nb in MU_KU:
                muku_element = MU_KU[nb]
                in_main = nb in main_branches
                chong_target = BRANCH_CHONG.get(nb)
                xing_open = (
                    nb in ("CHOU", "WEI", "XU")
                    and yun_branch in ("CHOU", "WEI", "XU")
                    and yun_branch != nb
                )
                # V3.6.7: 墓库藏干十神 → 开库放出之物的域
                muku_tgs = [ten_god(day_master, h) for h, _p in BRANCH_HIDDEN_STEMS.get(nb, [])]
                muku_domain = '事业官贵' if any(t in GROUP_GUAN for t in muku_tgs) \
                    else '财富' if any(t in GROUP_CAI for t in muku_tgs) \
                    else '学业文书' if any(t in GROUP_YIN for t in muku_tgs) \
                    else ''
                if chong_target == yun_branch:
                    triggers.append({
                        'kind': 'muku_kai', 'source': source, 'position': pos,
                        'branch': nb, 'in_main': in_main,
                        'mech': f"{source}{yun_branch}冲开{nb}{muku_element}墓"
                                 + (f"(库藏{'/'.join(muku_tgs)})" if muku_domain else ""),
                        'keyword': nb,
                        'ten_god': muku_domain,  # 复用 ten_god 字段传递域
                        # V3.6.9㊻y ch9 官库冲开=升职应期: 库藏官星=官贵出, 不论主位/宾位均POSITIVE(吉事);
                        # 库藏非官星(财富/学业域)=CHANGE
                        'direction': 'POSITIVE' if (in_main or muku_domain == '事业官贵') else 'CHANGE',
                    })
                elif xing_open:
                    triggers.append({
                        'kind': 'muku_kai', 'source': source, 'position': pos,
                        'branch': nb, 'in_main': in_main,
                        'mech': f"{source}{yun_branch}刑开{nb}{muku_element}墓(丑未戌三刑)"
                                 + (f"(库藏{'/'.join(muku_tgs)})" if muku_domain else ""),
                        'keyword': nb,
                        'ten_god': muku_domain,
                        'direction': 'POSITIVE' if (in_main or muku_domain == '事业官贵') else 'CHANGE',
                    })
                # 闭库: 运支与墓库支六合
                if BRANCH_LIUHE.get(yun_branch) == nb:
                    triggers.append({
                        'kind': 'muku_bi', 'source': source, 'position': pos,
                        'branch': nb, 'in_main': in_main,
                        'mech': f"{source}{yun_branch}合{nb}闭库({muku_element}墓收)",
                        'keyword': nb,
                        'direction': 'POSITIVE' if in_main else 'CHANGE',
                    })

        # ── V3.6.8 婚姻路径②③接入 (盲派原书第四节·结婚应期 L5093-5236) ──
        # 原书婚期三路径: ①配偶星合入配偶宫(已接 liuhe 合日支) ②配偶星天干合身
        # (流年干=男财/女官=配偶星, "逢天干五合为婚期") ③配偶宫逢刑冲(冲日支=配偶宫动)。
        # 引擎原只接路径①, 致"二婚/结婚"定不到年(真答案年常非配偶宫冲合年)。
        # 修后: 加 配偶星合身(流年干为男财女官)+ 配偶宫逢冲(冲日支, 非硬冲已分 HIGH)
        # 两条, 补全 DOMAIN_CORE["婚姻口舌"] 的取象路径。
        # 路径②: 流年干=配偶星(男=财星 女=官杀星) → 婚星合身应期
        stem_tg_flow = ten_god(day_master, yun_stem)
        spouse_group = GROUP_CAI if gender == "male" else GROUP_GUAN
        if stem_tg_flow in spouse_group:
            triggers.append({
                'kind': 'spouse_star', 'source': source, 'position': 'day',
                'branch': yun_branch, 'in_main': True,
                'mech': f"{source}{yun_stem}={stem_tg_flow}(配偶星)合身=婚期应象",
                'keyword': yun_stem, 'ten_god': stem_tg_flow,
                'direction': 'POSITIVE',
            })
        # 路径③: 流年支冲日支(配偶宫)=配偶宫动(非硬冲, 硬冲已判 HIGH)
        if BRANCH_CHONG.get(yun_branch) == four_pillars["day"].earthly_branch:
            triggers.append({
                'kind': 'chong_spouse_palace', 'source': source, 'position': 'day',
                'branch': four_pillars["day"].earthly_branch, 'in_main': True,
                'mech': f"{source}{yun_branch}冲日支{four_pillars['day'].earthly_branch}=配偶宫动(冲刑=婚应期)",
                'keyword': four_pillars["day"].earthly_branch,
                'direction': 'POSITIVE',
            })
        # V3.6.9㊻s53/s56/s58 全回退(㊻s54/s57/s58stat 核实): 试加 ch10 路径④"太岁之宫
        # 动命局之星" spouse_palace(配偶星藏支被流年/大运/大限 合冲穿伏) 三次:
        #   ㊻s53 大限挂版 top10 14→13(大限逐年泛滥, 同㊻m回退陷阱)
        #   ㊻s56 仅流年/大运版 top10 14→12(配偶星藏支常多现, 流年支十之八九能冲合某支, 泛滥)
        #   ㊻s58stat 预统计: "配偶星藏支全局唯一"仅 41.5% 命造(234 例里 97 条), 收窄力度不足
        # 结论: ch10 路径④ 在当前定位基准上无安全接入路径, 定位层婚姻域缺口
        # (4 道失败题 2020/2016/2005/2006 流年干均非配偶星, 流年支又不冲配偶星支)
        # 属架构层限制, 非事件生成层可修。暂回退保持基线 top10=14。

        # ── V3.6.9 §65 父母系统接入 (原书 L1875 "正偏财为父, 食伤禄为母, 印=父母星") ──
        # 长辈 domain 核心: 父星=偏财(藏干), 母星=正印(藏干), 年柱=祖上宫。
        # 应期: 流年支/干 引动 父星/母星 藏干所在支 = 父母应事年。
        FATHER_STAR = "偏财"
        MOTHER_STAR = "正印"
        father_branches = [
            nb for nb in four_branches.values()
            if any(ten_god(day_master, h) == FATHER_STAR
                   for h, _p in BRANCH_HIDDEN_STEMS.get(nb, []))
        ]
        mother_branches = [
            nb for nb in four_branches.values()
            if any(ten_god(day_master, h) == MOTHER_STAR
                   for h, _p in BRANCH_HIDDEN_STEMS.get(nb, []))
        ]
        # 父星/母星 藏干所在支 被流年冲/穿 = 父母应事年
        if father_branches:
            for nb in father_branches:
                if BRANCH_CHONG.get(yun_branch) == nb or BRANCH_CHUAN.get(yun_branch) == nb:
                    pos = next(p for p, b in four_branches.items() if b == nb)
                    triggers.append({
                        'kind': 'parent_star', 'source': source, 'position': 'year',
                        'branch': nb, 'in_main': False,
                        'mech': f"{source}{yun_branch}引动父星{FATHER_STAR}(藏{nb})=父应期",
                        'keyword': FATHER_STAR,
                        'direction': 'NEGATIVE',
                    })
                    break
        if mother_branches:
            for nb in mother_branches:
                if BRANCH_CHONG.get(yun_branch) == nb or BRANCH_CHUAN.get(yun_branch) == nb:
                    pos = next(p for p, b in four_branches.items() if b == nb)
                    triggers.append({
                        'kind': 'parent_star', 'source': source, 'position': 'year',
                        'branch': nb, 'in_main': False,
                        'mech': f"{source}{yun_branch}引动母星{MOTHER_STAR}(藏{nb})=母应期",
                        'keyword': MOTHER_STAR,
                        'direction': 'NEGATIVE',
                    })
                    break

        # ── 合见冲 / 冲见合为应 (段建业第02章: 原局有合,以冲为应; 原局有冲,以合为应) ──
        # 原局六合支对被岁运冲 → 合见冲应期; 原局六冲支对被岁运合 → 冲见合应期
        branch_items = list(four_branches.items())  # [(pos, branch), ...]
        for i in range(len(branch_items)):
            for j in range(i + 1, len(branch_items)):
                pos_a, ba = branch_items[i]
                pos_b, bb = branch_items[j]
                if BRANCH_LIUHE.get(ba) == bb:
                    for pos_x, bx in ((pos_a, ba), (pos_b, bb)):
                        if BRANCH_CHONG.get(yun_branch) == bx:
                            triggers.append({
                                'kind': 'hejianchong', 'source': source, 'position': pos_x,
                                'branch': bx, 'in_main': bx in main_branches,
                                'mech': f"原局{pos_a}{ba}-{pos_b}{bb}合, {source}{yun_branch}冲{bx}=以冲为应",
                                'keyword': bx,
                                'direction': 'NEGATIVE' if bx in main_branches else 'CHANGE',
                            })
                if BRANCH_CHONG.get(ba) == bb:
                    for pos_x, bx in ((pos_a, ba), (pos_b, bb)):
                        if BRANCH_LIUHE.get(yun_branch) == bx:
                            triggers.append({
                                'kind': 'chongjianhe', 'source': source, 'position': pos_x,
                                'branch': bx, 'in_main': bx in main_branches,
                                'mech': f"原局{pos_a}{ba}-{pos_b}{bb}冲, {source}{yun_branch}合{bx}=以合为应",
                                'keyword': bx,
                                'direction': 'POSITIVE' if bx in main_branches else 'CHANGE',
                            })

        # ── 遁藏透干应期: 命局地支藏干在运/年天干出现 ──
        for pos, nb in four_branches.items():
            for hidden_stem, _ in BRANCH_HIDDEN_STEMS.get(nb, []):
                if hidden_stem == yun_stem:
                    tg = ten_god(day_master, hidden_stem)
                    in_main = nb in main_branches
                    triggers.append({
                        'kind': 'tougan', 'source': source, 'position': pos,
                        'branch': nb, 'in_main': in_main,
                        'mech': f"{source}透干: {nb}藏{hidden_stem}({tg})现于天干",
                        'keyword': hidden_stem, 'ten_god': tg,
                        'direction': 'POSITIVE' if tg in GROUP_GUAN or tg in GROUP_CAI else 'NEUTRAL',
                    })

        # ── 伏吟/反吟（规则 §48-49）──
        # 伏吟 = 运/年/限柱与命局某柱干支完全相同
        # 反吟 = 运/年/限柱与命局某柱 天干相克 且 地支相冲（天克地冲）
        for pos, pp in four_pillars.items():
            chart_full = f"{pp.heavenly_stem}{pp.earthly_branch}"
            yun_full = f"{yun_stem}{yun_branch}"
            in_main_pos = pos in ("day", "hour")
            # 伏吟
            if yun_full == chart_full:
                triggers.append({
                    'kind': 'fuyin', 'source': source, 'position': pos,
                    'branch': yun_branch, 'in_main': in_main_pos,
                    'mech': f"{source}{yun_full}伏吟{pos}柱{chart_full}",
                    'keyword': yun_full, 'direction': 'CHANGE',
                })
            # 反吟：天克地冲
            else:
                stem_ke = (
                    CONTROLS.get(STEM_ELEMENT.get(yun_stem))
                    == STEM_ELEMENT.get(pp.heavenly_stem)
                )
                if stem_ke and BRANCH_CHONG.get(yun_branch) == pp.earthly_branch:
                    triggers.append({
                        'kind': 'fanyin', 'source': source, 'position': pos,
                        'branch': yun_branch, 'in_main': in_main_pos,
                        'mech': f"{source}{yun_full}反吟{pos}柱{chart_full}(天克地冲)",
                        'keyword': yun_full,
                        'direction': 'NEGATIVE' if in_main_pos else 'CHANGE',
                    })

        # ── 见禄应期（段建业第02章：某字之禄在流年出现=该字应期）──
        # 日主禄神：甲禄寅/乙禄卯/丙戊禄巳/丁己禄午/庚禄申/辛禄酉/壬禄亥/癸禄子
        LUTABLE = {"JIA":"YIN","YI":"MAO","BING":"SI","WU":"SI","DING":"WU","JI":"WU",
                   "GENG":"SHEN","XIN":"YOU","REN":"HAI","GUI":"ZI"}
        dm_lu = LUTABLE.get(day_master, "")
        if dm_lu and yun_branch == dm_lu:
            triggers.append({
                'kind': 'jianlu', 'source': source, 'position': 'day',
                'branch': dm_lu, 'in_main': True,
                'mech': f"{source}{yun_branch}=日主{day_master}禄神出现=见禄应期",
                'keyword': dm_lu,
                'direction': 'NEUTRAL',
            })
            # V3.6.9㊻p ch12 出狱应期(原书ch12出狱定法①"日主得禄之年=出狱"):
            # 牢狱局(辰/丑在局, ㊺已确证ch12牢狱结构+辰丑关联17例)+日主禄支流年出现=出狱年.
            all_brs_now = [four_pillars[k].earthly_branch for k in ('year','month','day','hour')]
            laoyu_ctx = any(b in all_brs_now for b in ("CHEN", "CHOU"))
            if laoyu_ctx:
                triggers.append({
                    'kind': 'chu_yu', 'source': source, 'position': 'day',
                    'branch': dm_lu, 'in_main': True,
                    'mech': (f"ch12出狱①: 牢狱局(辰/丑在局)+日主{day_master}得禄"
                             f"(流年{yun_branch}=禄支{dm_lu})=出狱年(原书ch12出狱定法①)"),
                    'keyword': '出狱',
                    'direction': 'POSITIVE',
                })

        # V3.6.9㊻q ch12 出狱定法②"日主合出/冲出日主之年=出狱"(独立于得禄年, 不依赖yun_branch==dm_lu):
        # ㊻q 修: ② 块 原 在 jianlu 守 卫 内(仅 得 禄 年 才 触 发, 逻 辑 错 误), 修 后 独 立 触 发.
        # 牢 狱 局(辰/丑 在 局) 时: ② 合 出=流 年 干=日 主 五 合 partner; 冲 出=流 年 支=冲 日 主 禄 支.
        # ③ 冲 穿 坏 库 由 muku_kai 机 制 已 覆 盖, chu_yu 不 叠 加(③ 只 在 断 事 层 release_path 标 签).
        all_brs_q = [four_pillars[k].earthly_branch for k in ('year','month','day','hour')]
        laoyu_q = any(b in all_brs_q for b in ("CHEN", "CHOU"))
        dm_lu_q = LUTABLE.get(day_master, "")
        if laoyu_q and dm_lu_q:
            STEM_HE_PAIRS_Q = {("JIA","JI"),("YI","GENG"),("BING","XIN"),
                               ("DING","REN"),("WU","GUI")}
            he_partner_q = ""
            for _a, _b in STEM_HE_PAIRS_Q:
                if day_master == _a and _b != day_master:
                    he_partner_q = _b
                elif day_master == _b and _a != day_master:
                    he_partner_q = _a
            chong_lu_q = BRANCH_CHONG.get(dm_lu_q, "")
            # ② 合出: 流年干=partner stem
            if he_partner_q and yun_stem == he_partner_q:
                triggers.append({
                    'kind': 'chu_yu', 'source': source, 'position': 'day',
                    'branch': yun_branch, 'in_main': True,
                    'mech': (f"ch12出狱②: 牢狱局+日主{day_master}合出"
                             f"(流年干{yun_stem}={he_partner_q}合日主)"
                             f"=出狱年(原书ch12出狱定法②合出)"),
                    'keyword': '出狱',
                    'direction': 'POSITIVE',
                })
            # ② 冲出: 流年支=冲日主禄支(非得禄年才触发, 排除与①重叠)
            if chong_lu_q and yun_branch == chong_lu_q and yun_branch != dm_lu_q:
                triggers.append({
                    'kind': 'chu_yu', 'source': source, 'position': 'day',
                    'branch': yun_branch, 'in_main': True,
                    'mech': (f"ch12出狱②: 牢狱局+日主{day_master}禄支{dm_lu_q}被冲"
                             f"(流年支{yun_branch}冲{dm_lu_q})=出狱年(原书ch12出狱定法②冲出)"),
                    'keyword': '出狱',
                    'direction': 'POSITIVE',
                })

        # ── V3.6.9㉚ ch2 原神应期(优先规则): 流年支=某柱干的原身(该干落根支)=该干相关事应期
        # 原书ch2: "八字中某字在流年出现, 或见其禄神/原身, 则此年发生与该字有关的事。
        # 见禄代表原身, 见原神代表禄, 此条具有优先性。" 天干原身对照=8干全表
        # (甲寅/乙卯/丙戊巳/丁己午/庚申/辛酉/壬亥/癸子; 四库辰戌丑未无原身)。
        # 旧版 jianlu 只处理"日主"一干, 缺口: 流年支=非日主某柱干原身时(如庚干原身=申,
        # 流年逢申=庚相关事应期)无独立机制。修后: 遍历四柱干, 流年支==该干原身支
        # 且该干≠日主(日主已在 jianlu 处理) → 触发 yuan_shen 应期(该干相关事, 优先级口径)。
        YUAN_SHEN_TABLE = LUTABLE  # 原身对照=天干落根支, 与禄表同构
        four_stems_all = [four_pillars[k].heavenly_stem for k in
                          ("year", "month", "day", "hour")]
        for st_ in four_stems_all:
            if st_ == day_master:
                continue  # 日主原身已在 jianlu 处理
            ysh = YUAN_SHEN_TABLE.get(st_, "")
            if ysh and ysh == yun_branch:
                triggers.append({
                    'kind': 'yuan_shen', 'source': source, 'position': 'day',
                    'branch': ysh, 'in_main': True,
                    'mech': (f"{source}{yun_branch}=原局{st_}干原身(落根{ysh})出现"
                             f"=原神应期(该干相关事, 优先性口径)"),
                    'keyword': ysh,
                    'direction': 'NEUTRAL',
                })
                break  # 一柱即可, 不重复堆叠

        # ── 空亡填实（段建业第02章：空亡字在流年出现=填实=坐实）──
        # 日柱旬空：六十甲子每旬10个，旬末后两支为空
        GANS60 = ["JIA","YI","BING","DING","WU","JI","GENG","XIN","REN","GUI"]
        ZHIS60 = ["ZI","CHOU","YIN","MAO","CHEN","SI","WU","WEI","SHEN","YOU","XU","HAI"]
        day_stem = four_pillars["day"].heavenly_stem
        day_br = four_pillars["day"].earthly_branch
        di, zi = GANS60.index(day_stem), ZHIS60.index(day_br)
        day_idx = next(i for i in range(60) if i % 10 == di and i % 12 == zi)
        xun_start = (day_idx // 10) * 10  # 旬首
        # 旬空 = 旬首后第10、11个支
        xun_branches = [ZHIS60[(xun_start + k) % 12] for k in range(10)]
        xunkong = [b for b in ZHIS60 if b not in xun_branches]
        if yun_branch in xunkong:
            triggers.append({
                'kind': 'tiankong', 'source': source, 'position': 'day',
                'branch': yun_branch, 'in_main': True,
                'mech': f"{source}{yun_branch}=日柱旬空{xunkong}填实=坐实",
                'keyword': yun_branch,
                'direction': 'NEUTRAL',
            })

        # ── 字再现（规则 §55）：运年支同字在命局重现（非自刑支）──
        # V3.6.9㊻x 删除㊿ kaiku 冗余块: ㊿ 加的 L1013-1030 kaiku 与 L767-801 muku_kai 是同一物理事件
        # (辰戌互冲关系对称, BRANCH_CHONG.get(yun)==nb 等价于 chong_target(nb)==yun), kaiku 块是重复触发,
        # 且 kaiku kind 在 _event_from_trigger 无 topic 映射(落入默认分支, 无升职关键词), 去掉后 muku_kai 正常消费.
        # 自刑支的重复已在 zixing 处理，此处补普通支的字再现。
        for pos, nb in four_branches.items():
            if nb == yun_branch and nb not in BRANCH_SANXING_SELF:
                in_main = nb in main_branches
                triggers.append({
                    'kind': 'zizaixian', 'source': source, 'position': pos,
                    'branch': nb, 'in_main': in_main,
                    'mech': f"{source}{yun_branch}再现命局{pos}支{nb}",
                    'keyword': nb, 'direction': 'CHANGE',
                })

        # ── 禄与原身应期: 某字禄位在原命局, 运年出现该禄位 ──
        # 或日主禄位在原命局被运年引动
        dm_lu = road_branch(day_master)
        if dm_lu in four_branches.values():
            # 禄在原局, 运年出现该禄的禄(重复禄)或合禄
            if yun_branch == dm_lu:
                triggers.append({
                    'kind': 'lu', 'source': source, 'position': 'day',
                    'branch': dm_lu, 'in_main': True,
                    'mech': f"{source}{yun_branch}重现日主禄位{dm_lu}",
                    'keyword': '禄', 'direction': 'POSITIVE',
                })

        # V3.6.9 引动降噪门控(修真事年无峰根因): 82/86 年都有引动(95%), 致
        # "报事"层无法"定年"。原书(段氏第02章): 旺年才应事, 衰/藏年份引动是
        # 常态背景, 不应报事。修后按触发强度分级门控:
        #   硬冲突(冲/穿/反吟/三刑/自刑)=HIGH 全保留
        #   合动/三合=MEDIUM, 仅 主位(in_main) 保留(宾位合=常态, 去掉)
        #   字再现/伏吟/填实/见禄=LOW, 仅 主位 保留(宾位=常态, 去掉)
        # 门控后: 宾位常态引动(占事件 60%+)不再报事, 真事年(主位核心机制)成峰。
        # 注: 这是"报事粒度"降噪, 不动断事层(三大结构/做功/十神全量计算不变),
        # 仅影响 yingqi_events 列表(定年/竞赛"哪年何事")。
        # V3.6.9: spouse_star/chong_spouse_palace/parent_star = 宾位信号类(MEDIUM), 全保留
        kept = []
        for t in triggers:
            kind = t['kind']
            in_main = t.get('in_main', False)
            if kind in ('chong', 'chuan', 'fanyin', 'sanxing', 'zixing'):
                kept.append(t)  # HIGH 全保留
            elif kind in ('liuhe', 'sanhe', 'hejianchong', 'chongjianhe',
                          'fuyin', 'zizaixian', 'tiankong', 'jianlu', 'lu', 'yuan_shen'):
                # V3.6.9㉚ 修真值"流年宾位支合漏报"(2027未午合月支午):
                # 大运/大限=十年基调层, 宾位合=常态背景, 仍只保留主位(原设计);
                # 流年=定年层, 流年支合入宾位支(月/年)亦是该年应事字, 保留为 LOW。
                if in_main or t.get('source') == '流年':
                    kept.append(t)  # 主位保留; 流年宾位支合保留(LOW); 大运/大限宾位=常态去掉
            elif kind in ('spouse_star', 'chong_spouse_palace', 'parent_star'):
                kept.append(t)  # 宾位信号类(MEDIUM)全保留
            elif kind == 'ganhe':
                kept.append(t)  # V3.6.9㉚ 干五合=合住该星, 定年信号, 全保留
            else:
                kept.append(t)  # 未知 kind 保留
        triggers = kept

        return triggers

    # ── 应期事件整理 ──────────────────────────────────────
    def _event_from_trigger(self, trg: Dict, day_master: str, age: int,
                            shi_hint: str = "UNDETERMINED") -> Optional[Dict]:
        """将引动转为应期事件(带机制/方向/强度).

        ㊻s91 ch2 应期消费 L1 势向: shi_hint 透传大运相对 L1 势方向 的 顺/逆
        (NI_SHI=逆势运凶向 / SHUN_SHI=顺势运吉向 / UNDETERMINED=不消费势).
        事件 direction 映射后, 若 仍 为 NEUTRAL 且 shi_hint 非 UNDETERMINED,
        则按 大运 顺/逆 定 方向(ch2 "反局之运应凶事"=逆势运=该年凶事, 顺势运=该年吉事).
        """
        kind = trg['kind']
        in_main = trg.get('in_main', False)
        direction = trg.get('direction', 'NEUTRAL')
        mech = trg['mech']

        # 严重度枚举（BLIND-ARCH-006 / BLIND-G16：禁数字化强度）
        # 结构规则：主位被穿/冲/反吟/三刑 = HIGH；主位其余 = MEDIUM；宾位 = LOW
        # V3.6.7 定年分级修: 原"主位 MEDIUM 兜底"把 liuhe/sanhe/zixing/tiankong/jianlu
        # 等常态机制(年年触发)都判 MEDIUM, 致婚姻类真事年无峰(95% 年都有引动)。
        # 修后: 主位 HIGH 仅限"硬冲突"(冲/穿/刑/反吟); 主位合动类
        # (liuhe 合动/sanhe/zixing/tiankong/jianlu)=MEDIUM; 主位合绊/宾位=LOW。
        # 合动 MEDIUM 是合理"信号"但不算峰, HIGH 只对硬冲突——真事年才有 HIGH 峰。
        severity = 'LOW'
        in_main = trg.get('in_main', False)
        pos = trg.get('position', '')
        # V3.6.9: 宾位信号类机制(婚星合身/父母星引动)=MEDIUM, 不因宾位降 LOW
        if kind in ('chong_spouse_palace', 'spouse_star', 'parent_star'):
            severity = 'MEDIUM'
        elif in_main:
            if kind in ('chuan', 'chong', 'fanyin', 'sanxing', 'zixing'):
                severity = 'HIGH'  # 硬冲突: 冲/穿/刑/反吟/自刑
            elif kind == 'fuyin':
                # V3.6.8: 伏吟主位=重复原局=该宫位事重发(配偶宫伏吟=婚重/再婚),
                # 盲派婚期应象之一, 提为 HIGH(非常态引动)。
                severity = 'HIGH'
            elif kind in ('liuhe', 'sanhe'):
                severity = 'MEDIUM'  # 合动/三合: 信号级(非峰)
            elif kind in ('zizaixian', 'fuyin', 'yuan_shen') and pos == 'day':
                severity = 'MEDIUM'  # 日支字再现/伏吟/原神=配偶宫事动·干相关事, 信号级
            elif kind == 'muku_kai' and direction == 'POSITIVE' and trg.get('ten_god') == '事业官贵':
                # V3.6.9㊻y ch9 官库冲开=升职应期: 官库冲开(POSITIVE方向, 库藏官星=事业官贵域)
                # 是升职/发贵应期, 与原书ch9 L22"官库冲开=升职应期"同级(吉事峰), 提为 HIGH;
                # ㊻y 收窄: 限 事业官贵 域(库藏官星), 不限定宫位, 但不影响 不限域/财富/学业 域题目
                # (避免 muku_kai HIGH 压制 不限域 真值题 如 学历题)
                severity = 'HIGH'
            else:
                severity = 'LOW'  # 主位合绊/tiankong/jianlu/lu = 常态
        # 合绊检测: liuhe 且 he_nature=合绊(天地合互绊失性) → 降级 LOW
        he_nature = trg.get('he_nature', '')
        if kind == 'liuhe' and he_nature == '合绊':
            severity = 'LOW'

        base = {
            'mechanism': kind, 'mech': mech, 'keyword': trg.get('keyword', ''),
            'source': trg['source'], 'direction': direction,
            'severity': severity, 'age': age,
        }
        # 应期细化事实透传（旺衰冲应/穿中生克/合动合绊, 段建业第02章）
        for detail_key in ('chong_effect', 'chuan_nature', 'he_nature', 'xushi'):
            if trg.get(detail_key):
                base[detail_key] = trg[detail_key]

        # 按引动类型映射到断事主题
        if kind == 'chuan' and in_main:
            base['topic'] = '穿倒主位'
            base['direction'] = 'NEGATIVE'
            # V3.6.9㊻e ch5 身体部位: 被穿支宫位→身体部位(穿倒主位=该部位伤损)
            body_part = trg.get('body_part', '')
            if body_part:
                base['body_part'] = body_part
        elif kind == 'chong' and in_main:
            base['topic'] = '冲主位'
            base['direction'] = 'NEGATIVE' if '禄' not in str(trg.get('keyword')) else 'CHANGE'
            # V3.6.9㊻e ch5 身体部位: 被冲支宫位→身体部位(冲主位=该部位伤损)
            body_part = trg.get('body_part', '')
            if body_part:
                base['body_part'] = body_part
        elif kind == 'muku_kai':
            base['topic'] = '冲开墓库'
            base['direction'] = 'POSITIVE'
            # V3.6.7: 开库放出之物=墓库藏干十神, 域精确到官贵/财富/学业
            muku_tg = trg.get('ten_god', '')
            if muku_tg:
                base['domain'] = muku_tg
        elif kind == 'muku_bi':
            base['topic'] = '闭库'
            base['direction'] = 'POSITIVE' if in_main else 'CHANGE'
        elif kind == 'hejianchong':
            base['topic'] = '合见冲应期'
            base['direction'] = 'NEGATIVE' if in_main else 'CHANGE'
        elif kind == 'chongjianhe':
            base['topic'] = '冲见合应期'
            base['direction'] = 'POSITIVE' if in_main else 'CHANGE'
        elif kind == 'sanhe':
            base['topic'] = '三合局引动'
            base['direction'] = 'POSITIVE'
        elif kind == 'sanxing':
            # 三刑引动: 盲派第02章只论"丑未戌/寅巳申三刑"应凶(案例: 死父/车祸/官非),
            # 不细分恃势/无恩; 恃势(丑戌未)/无恩(寅巳申)/无礼(子卯)细分属
            # 《三命通会》卷二·论三刑(传统口径), 且《渊海子平》称呼相反 ——
            # METHOD_SCOPE=TRADITIONAL 降级标注, 不进盲派核心规则
            base['topic'] = '三刑引动'
            base['direction'] = 'NEGATIVE'
            base['method_scope'] = 'TRADITIONAL'
            k = trg.get('keyword', '')
            if '恃势' in k:
                base['domain'] = '官非刑伤'
                base['domain_scope'] = 'SAN_MING_TONG_HUI'
            elif '无恩' in k:
                base['domain'] = '健康灾伤'
                base['domain_scope'] = 'SAN_MING_TONG_HUI'
            elif '无礼' in k:
                base['domain'] = '婚姻口舌'
                base['domain_scope'] = 'SAN_MING_TONG_HUI'
        elif kind == 'zixing':
            base['topic'] = '伏吟自刑'
            base['direction'] = 'CHANGE'
        elif kind == 'liuhe' and in_main:
            base['topic'] = '合入主位'
            base['direction'] = 'POSITIVE'
        elif kind == 'lu':
            base['topic'] = '禄神重现'
            base['direction'] = 'POSITIVE'
        elif kind == 'tougan':
            tg = trg.get('ten_god', '')
            base['topic'] = '透干应期'
        elif kind == 'fuyin':
            base['topic'] = '伏吟引动'
            base['direction'] = 'CHANGE'
        elif kind == 'fanyin':
            base['topic'] = '反吟引动'
            base['direction'] = 'NEGATIVE' if in_main else 'CHANGE'
        elif kind in ('spouse_star', 'chong_spouse_palace'):
            base['topic'] = '配偶星合身' if kind == 'spouse_star' else '配偶宫逢冲刑'
            base['direction'] = 'POSITIVE' if kind == 'spouse_star' else 'CHANGE'
            base['domain'] = '婚姻口舌'
            base.setdefault('domain_scope', 'BLIND_CORE')
        elif kind == 'parent_star':
            base['topic'] = '父母星引动'
            base['direction'] = 'NEGATIVE'
            base['domain'] = '长辈家宅'
            base['domain_scope'] = 'BLIND_CORE'
        elif kind == 'zizaixian':
            base['topic'] = '字再现引动'
            base['direction'] = 'CHANGE'
        elif kind == 'ganhe':
            # V3.6.9㉚ 天干五合=合住该十神之星: 合官杀=事业官非, 合财=财富, 合印=文书
            tg = trg.get('ten_god', '')
            base['topic'] = f'干合({tg})'
            if tg in ('正官', '七杀'):
                base['domain'] = '事业官贵'
            elif tg in ('正财', '偏财'):
                base['domain'] = '财富'
            elif tg in ('正印', '偏印'):
                base['domain'] = '学业文书'
            else:
                base['domain'] = '人事竞争'
            base['domain_scope'] = 'BLIND_CORE'
        else:
            base['topic'] = '运年引动'

        # ── V3.6.9⑯ 事件性质 topic 层(原书"应期定年=定事年", 事件不止机制):
        # 修真值"应期事件性质缺口 92 条": 旧版 topic 只表达 引动 机制(伏吟/三合/冲/穿/字再现/墓库/
        # 透干/运年), 不 表达 该 年 应 何 事(结婚/离婚/生子/得官/破财/发财/病灾/寿夭/迁徙)。
        # 原书 结婚 应期 三 路径(L5093-5236): 应期 年 须 答 何 事, 非 仅 何 引动。
        # 按 宫位 引动 推 事件 性质(盲派 核心 取象, 不 数字化):
        #   日支(配偶宫) 被 引动 → 婚姻 事件; 时支(子女宫) → 子女 事件;
        #   年支(长辈宫) → 长辈/家宅 事件; 月支(事业宫) → 事业/官贵 事件;
        #   禄位 被 引动 → 自身/福禄 事件; 财星 透 → 财 事件; 官杀 透 → 官 事件;
        #   印星 透 → 学业/文书 事件; 食伤 透 → 技艺/子息 事件。
        # 仅 当 该 年 该 宫位/十神 被 引动(主位 或 HIGH 引动) 时 才 加 事件 性质 topic,
        # 避免 泛 加(无 引动 不 应事, 原书"旺年 才 应事, 衰年 引动=常态")。
        event_topic = ''
        in_main_ev = trg.get('in_main', False)
        pos_ev = trg.get('position', '')
        tg_ev = trg.get('ten_god', '')
        # 宫位 引动 → 事件 性质
        if in_main_ev or kind in ('chong', 'chuan', 'fanyin', 'sanxing', 'zixing'):
            if pos_ev == 'day':
                event_topic = '婚姻事件'
            elif pos_ev == 'hour':
                event_topic = '子女事件'
            elif pos_ev == 'year':
                event_topic = '长辈家宅事件'
            elif pos_ev == 'month':
                event_topic = '事业官贵事件'
        # 十神 透/被 引动 → 事件 性质(财/官/印/食伤 各自 事件)
        if not event_topic and tg_ev:
            if tg_ev in GROUP_CAI:
                event_topic = '财富事件'
            elif tg_ev in GROUP_GUAN:
                event_topic = '官贵事件'
            elif tg_ev in GROUP_YIN:
                event_topic = '学业文书事件'
            elif tg_ev in GROUP_SHI:
                event_topic = '技艺子息事件'
        if event_topic:
            base['event_topic'] = event_topic
            base.setdefault('event_topic_scope', 'BLIND_CORE')

        # ── V3.6.7 域回填: 三大结构取值 → yingqi_events.domain ──
        # 原 7278 事件里 domain 大多空, 仅三刑细分有值。
        # 修后: 按引动分支 + 十神性质回填 domain(婚姻/官贵/财富/健康/人事),
        # 让竞赛"哪年何事"能在 ABCD 选项里选对。
        # 优先级: kind 专属域(墓库开/合日支/冲日支/禄) > 十神域 > 宫位域
        pos = trg.get('position', '')
        branch = trg.get('branch', '')
        tg = trg.get('ten_god', '')
        # kind 专属域(最高优先): 墓库开=放出之物, 合/冲日支=婚姻, 禄=自身
        specific_domain = ''
        if kind == 'muku_kai' and tg:
            specific_domain = tg
        if kind in ('liuhe', 'hejianchong', 'chongjianhe') and pos == 'day':
            specific_domain = '婚姻口舌'
        if kind == 'chong' and pos == 'day':
            specific_domain = '婚姻口舌'
        if kind == 'lu':
            specific_domain = '自身禄位'
        if kind in ('spouse_star', 'chong_spouse_palace'):
            specific_domain = '婚姻口舌'
        if kind == 'parent_star':
            specific_domain = '长辈家宅'
        if specific_domain:
            base['domain'] = specific_domain
            base.setdefault('domain_scope', 'BLIND_CORE')
            return base
        # 无 kind 专属域时, 走十神域 + 宫位域
        domain = ''
        if pos == 'day':
            domain = '婚姻口舌'
        elif pos == 'hour':
            domain = '子女前程'
        elif pos == 'month':
            domain = '事业官贵'
        elif pos == 'year':
            domain = '长辈家宅'
        if tg:
            if tg in GROUP_GUAN:
                domain = '官贵刑伤'
            elif tg in GROUP_CAI:
                domain = '财富'
            elif tg in GROUP_YIN:
                domain = '学业文书'
            elif tg in GROUP_SHI:
                domain = '口舌子女'
            elif tg in GROUP_BI:
                domain = '人事竞争'
        if domain and domain != base.get('domain', ''):
            base['domain'] = domain
        base.setdefault('domain_scope', 'BLIND_CORE' if domain else '')
        return base


# 地支五行缓存(避免重复计算)
_BRANCH_ELEM_CACHE = {}


def _branch_element_cached(branch: str) -> str:
    if branch not in _BRANCH_ELEM_CACHE:
        from ..engines.bazi_engine import _branch_element
        _BRANCH_ELEM_CACHE[branch] = _branch_element(branch)
    return _BRANCH_ELEM_CACHE[branch]

# 六穿生克性质（段建业第02章案例"寅冲穿巳是动了巳（穿而生，有动意）"
# → 穿中带生=轻/有动意；穿中带克=重/直接受损）
CHUAN_NATURE = {
    # 键为拼音地支(sorted), 与引擎干支枚举一致
    ("WEI", "ZI"): "带克",   # 子未: 未土克子水
    ("CHOU", "WU"): "带生",  # 丑午: 午火生丑土
    ("SI", "YIN"): "带生",   # 寅巳: 寅木生巳火
    ("CHEN", "MAO"): "带克", # 卯辰: 卯木克辰土
    ("HAI", "SHEN"): "带生", # 申亥: 申金生亥水
    ("XU", "YOU"): "带生",   # 酉戌: 戌土生酉金
}


def _chuan_nature(a: str, b: str) -> str:
    """六穿对的生克性质: 带生(轻,有动意) / 带克(重)."""
    return CHUAN_NATURE.get(tuple(sorted([a, b])), "带克")


# 五行相生（用于得令判定: 当令或得月令生 → 旺）
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}


def _branch_strong(chart, branch: str) -> bool:
    """支的旺衰（得月令判定）: 当令(同月令五行) 或 得月令生(相) → 旺.

    段建业冲应旺衰以月令为权（盲派弃日主旺衰、用月令轻重），
    此处只做支的得令判定，不引入任何评分。
    """
    month_branch = chart.month_pillar.earthly_branch
    el = _branch_element_cached(branch)
    mel = _branch_element_cached(month_branch)
    return el == mel or _GENERATES.get(mel) == el


def _chong_effect(chart, yun_branch: str, nb: str) -> str:
    """七 冲 法(段 建 业 第 02 章 七 种 冲 法 及 用 途: 冲 区/冲 旺/冲 动/冲 开/冲 出/冲 去/冲 破).
    V3.6.9㊲ 扩 展: 旧 版 3 类(冲去/冲起/NEUTRAL) → 7 类(七 冲 法).
    判 据(原 书 七 冲 法 文 本 + 旺 衰 冲 应 口 径 融 合):
      冲 区 = 四 库(辰 戌 丑 未)被 冲, 库 门 打 开
      冲 旺 = 运 支 月 令 当 令(旺), 冲 入 命 局 衰 字 = 旺 者 冲 衰
      冲 动 = 两 弱 相 冲(月 令 不 当 令 的 运 支 冲 入 命 局 字), 引 动 不 去 不 起
      冲 开 = 运 支 冲 开 财 官 墓 库(冲 区 且 财 官 被 墓 库 收)
      冲 出 = 运 支 冲 入 支 藏 干 有 天 干 透 应(该 字 被 冲 出 到 天 干)
      冲 去 = 运 支 旺 冲 衰 字(旧 版 冲 去, 月 令 不 当 令 也 算 冲 去 但 力 弱)
      冲 破 = 被 冲 支 与 日 主 同 行(冲 破 本 气)
    优 先 级: 冲 破 > 冲 开 > 冲 区 > 冲 出 > 冲 旺 > 冲 动 > 冲 去(末 位 兜 底).
    断 事 层 无 影 响(chong_effect 只 进 定 位 层 top_mech 排 序 加 权)."""
    # 冲 破: 被 冲 支 与 日 主 同 行(冲 破 本 气)
    day_master = chart.day_master
    day_master_el = STEM_ELEMENT.get(day_master, "")
    nb_el = _branch_element_cached(nb)
    if nb_el == day_master_el:
        return "冲 破"
    # 冲 开/冲 区: 四 库 被 冲
    MUKU_SET = {"CHEN", "XU", "CHOU", "WEI"}
    if nb in MUKU_SET:
        muku_tgs = [ten_god(day_master, h) for h, _p in BRANCH_HIDDEN_STEMS.get(nb, [])]
        if any(t in ("正财", "偏财", "正官", "七杀") for t in muku_tgs):
            return "冲 开"
        return "冲 区"
    # 冲 出: 被 冲 支 藏 干 有 天 干 透 应
    all_stems = [chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
                 day_master, chart.hour_pillar.heavenly_stem]
    hidden = [h for h, _p in BRANCH_HIDDEN_STEMS.get(nb, [])]
    if any(h in all_stems for h in hidden):
        return "冲 出"
    # 冲 旺: 运 支 月 令 当 令 冲 入 命 局 衰 字
    month_el = _branch_element_cached(chart.month_pillar.earthly_branch)
    yun_el = _branch_element_cached(yun_branch)
    yun_sheng = month_el == yun_el or _GENERATES.get(month_el) == yun_el
    nb_sheng = month_el == nb_el or _GENERATES.get(month_el) == nb_el
    if yun_sheng and not nb_sheng:
        return "冲 旺"
    if not yun_sheng and not nb_sheng:
        return "冲 动"
    return "冲 去"


def analyze_yingqi(birth: Tuple[int, int, int, int], gender: str = "male",
                   target_age: Optional[int] = None,
                   target_year: Optional[int] = None) -> YingqiResult:
    """便捷入口."""
    engine = BlindYingqiEngine()
    return engine.analyze(birth, gender, target_age, target_year)
