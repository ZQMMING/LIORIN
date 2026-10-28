"""H2: FrozenHeluoState — 河洛冻结状态对象

职责：
  将 HeluoResult 的所有计算结果整合为一个不可变的状态对象，
  代表"已经计算出来的河洛世界"，而非直接给出吉凶结论。

  对应紫微的 FrozenZiweiChart，作为 Signal → Assertion → Guidance 的输入源。

设计原则：
  1. 冻结（frozen=True）：一旦创建不可修改
  2. 含 calculation_policy：记录使用了哪套规则（元、背法等）
  3. 不含 value judgment：无 direction/strength/confidence
     （这些由 yi_interpreter.py 的 EVENT_SIGNAL 处理）
  4. 两条时间轴分离：人之时间轴 / 天之时间轴
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class FrozenHeluoState:
    """
    河洛理数冻结状态对象。

    人之时间轴：
      birth_numbers → prenatal → yuan_tang → postnatal → timeline

    天之时间轴：
      seasonal_hexagram → qi_phase

    状态判断层：
      hua_gong（化工状态，H6）
    """
    # ── 基础数据 ──────────────────────────────────────────────
    version: str                           # 计算版本，如 "v2.0"
    calculation_policy: dict               # 计算策略（元、背法等）

    # ── 人之时间轴（出生 → 大运 → 流年 → 流月 → 流日）──────────
    tian_shu: int                          # 天数（原始合计）
    di_shu: int                            # 地数（原始合计）
    tian_reduced: int                      # 天数归一化
    di_reduced: int                        # 地数归一化

    prenatal_name: str                     # 先天卦名
    prenatal_upper: str                    # 先天上卦
    prenatal_lower: str                    # 先天下卦
    prenatal_lines: tuple[int, ...]        # 先天六爻（1=阳, -1=阴）

    yuan_tang: str                         # 元堂名（如"六四"）
    yuan_tang_index: int                   # 元堂索引（0-5）
    yuan_tang_nature: str                  # 元堂爻性（"阳"/"阴"）

    postnatal_name: str                    # 后天卦名
    postnatal_upper: str                   # 后天上卦
    postnatal_lower: str                   # 后天下卦
    postnatal_lines: tuple[int, ...]       # 后天六爻

    # ── 天之时间轴（节气 → 节候卦 → 卦气）─────────────────────
    seasonal_hexagram: Optional[dict]      # 出生日节候卦信息
    qi_phase: Optional[dict]               # 卦气阶段信息

    # ── 状态判断层（H6）───────────────────────────────────────
    hua_gong_state: Optional[str]          # NORMAL / REVERSE / RESCUED / KEZHI / WEAK / UNRESOLVED
    hua_gong_evidence: Optional[list[str]] # 化工证据链

    # ── 时间序列（从 canonical._build_timeline 提取）──────────
    dayun_summary: list[dict]              # 大运摘要（年龄区间 + 卦 + 爻）
    liunian_count: int                     # 流年卦总数
    birth_year: int                        # 出生年份

    # ── 辅助信息 ──────────────────────────────────────────────
    gender: str                            # "male" / "female"
    birth_hour: str                        # 出生时辰
    birth_date: str                        # 出生日期 ISO

    # 2026-10-07 审计修：L576 三级回退的两个决定性标志此前不在冻结态内，
    # 导致「正体得位」与「仅得纳音、福寿减半」在下游只剩同一个 state 值可看。
    # 必须追加在末尾——dataclass 里带默认值的字段不能后接非默认值，
    # 插在 hua_gong_state 之后会连累 dayun_summary 等后续字段全部报错。
    hua_gong_level: Optional[str] = None   # 正体 / 互体 / 纳音 / 无

    # ── 元气层（H7）────────────────────────────────────────
    yuan_qi_state: Optional[str] = None   # NORMAL / REVERSE / UNRESOLVED
    yuan_qi_evidence: Optional[list[str]] = None  # 元气证据链
    yuan_qi_tian: Optional[str] = None    # 天元气卦（年干纳甲）
    yuan_qi_di: Optional[str] = None      # 地元气卦（年支后天宫）
    hua_gong_reduced: Optional[bool] = None  # 末级减半（L576「终是浅薄，福寿减半」）

    def to_dict(self) -> dict:
        """序列化为字典，供 Signal/Assertion 层消费。"""
        return {
            "version": self.version,
            "calculation_policy": self.calculation_policy,
            "birth": {
                "year": self.birth_year,
                "date": self.birth_date,
                "gender": self.gender,
                "hour": self.birth_hour,
            },
            "numbers": {
                "tian_shu": self.tian_shu,
                "di_shu": self.di_shu,
                "tian_reduced": self.tian_reduced,
                "di_reduced": self.di_reduced,
            },
            "prenatal": {
                "name": self.prenatal_name,
                "upper": self.prenatal_upper,
                "lower": self.prenatal_lower,
                "lines": list(self.prenatal_lines),
            },
            "yuan_tang": {
                "name": self.yuan_tang,
                "index": self.yuan_tang_index,
                "nature": self.yuan_tang_nature,
            },
            "postnatal": {
                "name": self.postnatal_name,
                "upper": self.postnatal_upper,
                "lower": self.postnatal_lower,
                "lines": list(self.postnatal_lines),
            },
            "yuan_qi": {
                "state": self.yuan_qi_state,
                "tian": self.yuan_qi_tian,
                "di": self.yuan_qi_di,
                "evidence": self.yuan_qi_evidence,
            },
            "hua_gong": {
                "state": self.hua_gong_state,
                "level": self.hua_gong_level,
                "reduced": self.hua_gong_reduced,
                "evidence": self.hua_gong_evidence,
            },
            "seasonal": self.seasonal_hexagram,
            "qi_phase": self.qi_phase,
            "timeline": {
                "dayun_summary": self.dayun_summary,
                "liunian_count": self.liunian_count,
            },
        }


def build_frozen_state(result: Any, calculation_policy: Optional[dict] = None) -> FrozenHeluoState:
    """
    从 HeluoResult 构建 FrozenHeluoState。

    Args:
        result: HeluoResult 对象（来自 HeluoCanonical.calculate()）
        calculation_policy: 计算策略，默认从 result 推断

    Returns:
        FrozenHeluoState
    """
    from .numbers import TRIGRAM_LINES

    # ⚠ 2026-10-07 审计修：era 此前取的是 result.input.timezone（恒为
    # "Asia/Shanghai"）——把**时区**填进了**世代**字段，上中下元出处彻底丢失。
    # 现从 result.era 读真值；旧结果对象无该字段时记 "unknown"，不再拿时区顶替。
    _era = getattr(result, "era", None) or "unknown"
    policy = calculation_policy or {
        "stem_method": "河图",
        "era": _era,
        "calc_version": "v2.0",
    }

    # 从上下卦重建先天六爻
    def _trigrams_to_lines(upper: str, lower: str) -> tuple[int, ...]:
        lower_lines = list(TRIGRAM_LINES.get(lower, (-1,-1,-1)))
        upper_lines = list(TRIGRAM_LINES.get(upper, (-1,-1,-1)))
        return tuple(lower_lines + upper_lines)

    # 提取时序数据
    dayun_summary = []
    liunian_count = 0
    timeline = getattr(result, 'timeline', None)
    if timeline is not None:
        yearly = getattr(timeline, 'yearly_hexagrams', [])
        liunian_count = len(yearly) if yearly else 0
        qi_phase = getattr(timeline, 'qi_phase', None) or {}
        # 定稿（2026-10-22）：大运层只生成**元数据**，不起大运卦。
        # qi_phase.dayun 仍保留完整字段（hexagram/line_index/phase）供 guajie
        # 的运反判定用；此处 dayun_summary 落纯元数据 {start_age, end_age, ganzhi}。
        #
        # ganzhi 定义：大运是「爻位值运」（阳爻 9 年 / 阴爻 6 年），不按干支轮转，
        # 故取该段**起始年**（虚岁 == start_age）所对应的流年干支作定位标识。
        _ganzhi_by_age: dict = {}
        for _e in list(getattr(result, 'timeline', None).yearly_meta or []) if getattr(result, 'timeline', None) else []:
            _ganzhi_by_age[_e.get('age')] = _e.get('ganzhi', '')
        for _e in list(getattr(result, 'timeline', None).yearly_hexagrams or []) if getattr(result, 'timeline', None) else []:
            _ganzhi_by_age.setdefault(_e.get('age'), _e.get('ganzhi', ''))
        dayun_summary = []
        for _de in (qi_phase.get('dayun', []) or []):
            _sa = _de.get('age_start')
            dayun_summary.append({
                "start_age": _sa,
                "end_age": _de.get("age_end"),
                "ganzhi": _ganzhi_by_age.get(_sa, ""),
            })

    hua_gong = getattr(result, 'hua_gong', None)
    yuan_qi = getattr(result, 'yuan_qi', None)
    seasonal_hex = getattr(result, 'seasonal_hexagram', None)

    # 解析出生日期
    birth_date = getattr(getattr(result, 'input', None), 'birth_date', '')
    birth_year = int(birth_date.split('-')[0]) if birth_date else 0
    gender = getattr(getattr(result, 'input', None), 'gender', 'male')
    birth_hour = getattr(getattr(result, 'input', None), 'birth_time', '子')

    return FrozenHeluoState(
        version="v2.0",
        calculation_policy=policy,
        tian_shu=result.numbers.tian_shu,
        di_shu=result.numbers.di_shu,
        tian_reduced=result.numbers.tian_reduced,
        di_reduced=result.numbers.di_reduced,
        prenatal_name=result.prenatal.hexagram_name,
        prenatal_upper=result.prenatal.upper_gua,
        prenatal_lower=result.prenatal.lower_gua,
        prenatal_lines=_trigrams_to_lines(result.prenatal.upper_gua, result.prenatal.lower_gua),
        yuan_tang=result.yuantang.yuantang,
        yuan_tang_index=result.yuantang.yuantang_index,
        yuan_tang_nature=result.yuantang.yao_nature,
        postnatal_name=result.postnatal.hexagram_name,
        postnatal_upper=result.postnatal.upper_gua,
        postnatal_lower=result.postnatal.lower_gua,
        postnatal_lines=tuple(result.postnatal.lines),
        seasonal_hexagram=seasonal_hex,
        qi_phase=qi_phase if timeline else None,
        hua_gong_state=hua_gong.state.value if hua_gong else None,
        hua_gong_level=getattr(hua_gong, "level", None) if hua_gong else None,
        hua_gong_reduced=getattr(hua_gong, "reduced", None) if hua_gong else None,
        hua_gong_evidence=hua_gong.evidence if hua_gong else None,
        yuan_qi_state=yuan_qi.state.value if yuan_qi else None,
        yuan_qi_evidence=yuan_qi.evidence if yuan_qi else None,
        yuan_qi_tian=yuan_qi.tian_yuan_qi if yuan_qi else None,
        yuan_qi_di=yuan_qi.di_yuan_qi if yuan_qi else None,
        dayun_summary=dayun_summary,
        liunian_count=liunian_count,
        birth_year=birth_year,
        gender=gender,
        birth_hour=birth_hour,
        birth_date=birth_date,
    )
