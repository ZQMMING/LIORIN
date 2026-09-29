"""Z76: 流日参数与来源契约（第一阶段）

原则（用户铁律）：
1. 先做"流日计算与来源契约"，再做规则接入。
2. 流日四化天干来源未在《飞星秘仪》查到原文 → 不反套流月规则，标 UNRESOLVED。
3. 南北派继续绝对隔离，不投票不互补。
4. 本模块只回答机器层面：
   给定 natal_chart + flow_year + flow_month + flow_day（阳历日），
   唯一确定 flow_day_gan / flow_day_zhi / day_position / applicable_method。
   不接 Rule/Evidence/Assertion。

已钉边界（对照现有层）：
- 流年四化：北派钦天 = 流年命宫宫干（非流年干支本身），已由 QTN-CMB-016 钉住。
- 流月四化：《飞星秘仪》"流月四化飛曜天干：一律用本命盤天干，不可另取用"，
  已由 QTN-CMB-054 钉住。
- 流日四化天干：《飞星秘仪》原文未检索到流日四化天干的明确讲法。
  iztro 默认 daily.mutagen 用流日干支（阳历日天干），但这不是钦天口径。
  → 本阶段不假设、不反套，标 UNRESOLVED，等原典取证。
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class FlowDayContract:
    """流日参数契约——给定 natal + 阳历日，唯一确定流日定位。

    本结构不做吉凶判断，只钉"这一天在盘上是什么、为什么这样取"。
    """
    flow_day_date: str            # 阳历日 "YYYY-MM-DD"
    flow_day_gan: str             # 流日天干（iztro daily.heavenlyStem）
    flow_day_zhi: str             # 流日地支（iztro daily.earthlyBranch）
    flow_day_mutagen: list        # 流日四化 [禄,权,科,忌]（iztro 计算）
    day_position_palace: str      # 流日地支落本命盘哪个宫名
    source_of_gan: str            # 天干来源说明
    source_of_zhi: str            # 地支来源说明
    applicable_sect: list         # 本阶段允许进入的派别（默认空=不接规则）
    sihua_gan_source: str         # 流日四化天干来源契约状态
    notes: str = ""


def resolve_flow_day(chart, flow_day: tuple[int, int, int]) -> FlowDayContract:
    """解析流日参数契约（第二阶段：契约落地，规则仍不接入）。

    数据源约定（不重复调 iztro）：
        chart 必须由 ``ZiweiEngine.full_chart(lunar_date, hour, gender,
        flow_day=(y, m, d))`` 构造——该路径已在 Z76 中把流日天干/地支/四化
        写入 ZiweiChart.flow_day_gan / flow_day_zhi / flow_day_mutagen。
        本函数只做"从 chart 读出 + 落宫反查 + 来源标注"，不引入任何
        吉凶判断，也不允许用本命盘干支顶替（fail-closed）。

    参数：
        chart: ZiweiChart（需含 palaces 地支映射；流日字段须经
            full_chart(flow_day=...) 填充）
        flow_day: (年, 月, 日) 阳历日，须与构造 chart 时传入的一致

    返回：FlowDayContract

    异常：
        ValueError: chart 未携带流日干支（调用方未经 full_chart(flow_day=)
            构造），拒绝凭空推断。
    """
    y, mo, d = flow_day

    gan = str(getattr(chart, "flow_day_gan", "") or "")
    zhi = str(getattr(chart, "flow_day_zhi", "") or "")
    mutagen = list(getattr(chart, "flow_day_mutagen", []) or [])

    if not gan or not zhi:
        raise ValueError(
            "resolve_flow_day: chart 未携带流日干支。请先用 "
            "ZiweiEngine.full_chart(..., flow_day=(年,月,日)) 构造命盘，"
            "本契约拒绝凭空推断（Z76 铁律：只钉参数，不反套规则）。"
        )

    # 流日地支落本命盘哪一宫（与 palace_stems 的 branch 规范化口径一致）
    palaces = getattr(chart, "palaces", {}) or {}
    position = ""
    for pname, pdata in palaces.items():
        branch = str(pdata.get("branch", "")).strip("'\"")
        if branch and branch == zhi:
            position = pname
            break

    return FlowDayContract(
        flow_day_date=f"{y}-{mo:02d}-{d:02d}",
        flow_day_gan=gan,
        flow_day_zhi=zhi,
        flow_day_mutagen=mutagen,
        day_position_palace=position,
        source_of_gan="iztro horoscope daily.heavenlyStem（阳历日干支口径）",
        source_of_zhi="iztro horoscope daily.earthlyBranch（阳历日地支口径）",
        applicable_sect=[],  # 第一阶段铁律：不接 Rule/Evidence/Assertion
        sihua_gan_source=(
            "UNRESOLVED —《飞星秘仪》未检索到流日四化天干的明确原文；"
            "iztro daily.mutagen 用流日干支，属通用口径而非钦天口径，"
            "仅供参数钉位，禁止据此断事（等原典取证后升级为第二阶段规则接入）"
        ),
        notes="契约层输出，无吉凶语义；南北派均未接入流日规则。",
    )
