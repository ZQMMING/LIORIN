"""河洛元堂定位模块（Module 4）

负责：元堂（本命动爻）定位
冻结规则依据：Architecture Freeze V1.0 §2.3 模块4

六爻表示：与原典参考实现一致
  - 1 = 阳爻（乾卦三爻为 [1,1,1]）
  - -1 = 阴爻（坤卦三爻为 [-1,-1,-1]）
  - 整体六爻：lower[0:3] + upper[3:6]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class YuanTang:
    """元堂结果"""
    yuantang: str            # 元堂名（如"六四"）
    yuantang_index: int      # 元堂索引（0-5，0=初爻）
    lines: list[int]         # 六爻（1=阳, -1=阴）
    trace: list[dict]        # 追踪信息（供审计）
    yao_nature: Literal["阳", "阴"]  # 元堂爻性


# 时辰定义（对应 0-23 小时）
HOUR_NAMES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 上六时（阳时）与下六时（阴时）
UPPER_HOURS = {0, 1, 2, 3, 4, 5}     # 子丑寅卯辰巳
LOWER_HOURS = {6, 7, 8, 9, 10, 11}   # 午未申酉戌亥


def _is_pure_yang(six_lines: list[int]) -> bool:
    """是否纯阳卦（六爻皆阳）"""
    return all(l == 1 for l in six_lines)


def _is_pure_yin(six_lines: list[int]) -> bool:
    """是否纯阴卦（六爻皆阴）"""
    return all(l == -1 for l in six_lines)


def _qi_gong_roundtrip(start: int, opposite: list[int], k: int) -> int:
    """N=1/2 寄异类落点：从 start（最后占用的同类爻）的下一异类爻起，自下而上回绕。

    依据《河洛真数·起例卷》小畜图：一阴爻六四，午未占六四后，申九五、酉上九、
    戌初九、亥九二——从六四(3)之上一阳爻九五(4)起，自下而上回绕 [4,5,0,1,2]。
    讼图：二阴爻初六/六三，午未申酉重数往复后戌九四——从六三(2)之上一阳爻九四(3)起。
    """
    seq = [i for i in opposite if i > start] + [i for i in opposite if i <= start]
    return seq[k % len(seq)]


def find_yuantang(
    six_lines: list[int],
    birth_hour: str,
    gender: str,
    xiantian_name: str,
    solar_phase: str | None = None,
) -> YuanTang:
    """
    确定元堂爻位（C-07）

    冻结规则：
    - 纯阳卦（乾）：
        - 男：十二时皆自下而上数（原典：男得乾子午皆在初爻）
        - 女：冬至后至夏至前（冬半年）自上九始往下行至初爻；
              夏至后至冬至前（夏半年）自初九始往上行至上九（原典 p051-052）
    - 纯阴卦（坤）：
        - 女：十二时皆自下而上数（原典：女得坤子午皆在初爻）
        - 男：冬至后至夏至前（冬半年）自上六行至初六；
              夏至后至冬至前（夏半年）自下而上（原典 p051-052）
    - 杂卦：按飞支法定位（阳时取阳爻，阴时取阴爻）
    - 索引公式：(offset) % len(candidates)  （无 +1）

    solar_phase: "winter"（冬至后至夏至前）/ "summer"（夏至后至冬至前）。
                 None = 旧行为（女乾/男坤固定自上而下，等价冬半年），向后兼容。
    """
    if gender not in ("male", "female"):
        raise ValueError(f"gender must be male or female, got {gender!r}")

    if birth_hour not in HOUR_NAMES:
        raise ValueError(f"birth_hour must be one of {HOUR_NAMES}, got {birth_hour!r}")

    hour_idx = HOUR_NAMES.index(birth_hour)
    is_yang_hour = hour_idx in UPPER_HOURS

    trace: list[dict] = []
    action = "PURE"

    # 纯卦特殊规则
    if _is_pure_yang(six_lines):
        if gender == "male":
            # 男得乾：十二时皆自下而上
            target_idx = hour_idx % 6
            target_line = 1
        else:
            # 女得乾：冬半年自上而下；夏半年自下而上
            if solar_phase == "summer":
                target_idx = hour_idx % 6
            else:
                target_idx = (5 - hour_idx) % 6
            target_line = 1
        yao_nature = "阳"

    elif _is_pure_yin(six_lines):
        if gender == "female":
            # 女得坤：十二时皆自下而上
            target_idx = hour_idx % 6
            target_line = -1
        else:
            # 男得坤：冬半年自上而下；夏半年自下而上
            if solar_phase == "summer":
                target_idx = hour_idx % 6
            else:
                target_idx = (5 - hour_idx) % 6
            target_line = -1
        yao_nature = "阴"

    else:
        # 杂卦：阳时取阳爻(1)，阴时取阴爻(-1)
        if is_yang_hour:
            target_line = 1
        else:
            target_line = -1

        # 原典诗诀（《河洛真数·起例卷》定元堂式 + 元堂爻位式图示，2026-08-27 据原典图修正）：
        #   阴阳一二重而寄 → N=1/2：同类爻重数（一爻两时 / 两爻两次往复），
        #                     超出后寄入异类爻，从"最后占用同类爻的下一异类爻"起自下而上回绕
        #                     （原典小畜图：午未六四，申九五酉上九戌初九亥九二 = 从六四上一阳爻起回绕）
        #   三位虽重没寄宫 → N=3：重数两次往复正好填满六时，无寄宫
        #   四五无重应有寄 → N=4/5：单飞一遍（无重数），超出寄入异类爻（取模，自下而上）
        # 地支序：阳时从"子"起（t=0..5），阴时从"午"起（t=0..5）——原典"阴时生人取本卦阴爻从午时数起"
        t = hour_idx if is_yang_hour else hour_idx - 6
        candidates = [i for i, l in enumerate(six_lines) if l == target_line]
        if not candidates:
            raise ValueError(f"No {'yang' if target_line == 1 else 'yin'} line found")
        opposite_candidates = [i for i, l in enumerate(six_lines) if l != target_line]
        n_same = len(candidates)

        if n_same == 1:
            # 一阳/一阴卦：子丑或午未二时同在此爻，第三时起寄异类（回绕）
            if t < 2:
                target_idx = candidates[0]
                action = "REPEAT"
            else:
                target_idx = _qi_gong_roundtrip(candidates[0], opposite_candidates, t - 2)
                action = "QI_GONG"
        elif n_same == 2:
            # 二阳/二阴卦：重数两次往复（四时），第五时起寄异类（回绕）
            if t < 4:
                target_idx = candidates[t % 2]
                action = "REPEAT"
            else:
                target_idx = _qi_gong_roundtrip(candidates[1], opposite_candidates, t - 4)
                action = "QI_GONG"
        elif n_same == 3:
            # 三阳/三阴卦：重数两次往复（六时填满），无寄宫
            target_idx = (candidates * 2)[t % 6]
            action = "REPEAT"
        elif n_same in (4, 5):
            # 四/五阴四/五阳卦：单飞一遍，超出寄异类
            # 混合规则（2026-08-27 原典图示+权威案例交叉验证）：
            #   同类爻连续无gap（大过阳[1,2,3,4]、颐阴[1,2,3,4]）→ 回绕
            #     原典p049大过图：辰巳寄阴[5,0]，巳→初六(0)
            #     原典p047颐图：戌亥寄阳[5,0]，亥→初九(0)
            #   同类爻有gap（艮为山阴[0,1,3,4]gap@2）→ 取模自下而上
            #     案例二权威：艮为山戌→九三(2)
            #   last=top时回绕与取模等价（明夷、升）
            is_consecutive = (candidates[-1] - candidates[0] + 1) == n_same
            if t < n_same:
                target_idx = candidates[t]
                action = "NORMAL"
            elif is_consecutive:
                target_idx = _qi_gong_roundtrip(candidates[-1], opposite_candidates, t - n_same)
                action = "QI_GONG_ROUNDTRIP"
            else:
                target_idx = opposite_candidates[(t - n_same) % len(opposite_candidates)]
                action = "QI_GONG_MODULO"
        else:
            raise ValueError(f"Unexpected n_same={n_same}")

        yao_nature = "阳" if six_lines[target_idx] == 1 else "阴"

    trace.append({
        'step': 'pure' if (_is_pure_yang(six_lines) or _is_pure_yin(six_lines)) else 'mixed',
        'lines': six_lines.copy(),
        'target': ("阳" if is_yang_hour else "阴"),
        'candidates': [i for i, l in enumerate(six_lines) if l == (1 if is_yang_hour else -1)],
        'hour': birth_hour,
        'gender': gender,
        'hour_idx': hour_idx,
        'solar_phase': solar_phase,
        'action': action,
        'landed_line_polarity': yao_nature,
    })

    # 构建元堂名称（以实际落点爻的阴阳定"九/六"）
    position_names = ['初', '二', '三', '四', '五', '上']
    line_type = '九' if yao_nature == "阳" else '六'
    if target_idx in (0, 5):
        yuantang_name = f'{position_names[target_idx]}{line_type}'
    else:
        yuantang_name = f'{line_type}{position_names[target_idx]}'

    return YuanTang(
        yuantang=yuantang_name,
        yuantang_index=target_idx,
        lines=six_lines.copy(),
        trace=trace,
        yao_nature=yao_nature,
    )


# 向后兼容别名
resolve_yuantang = find_yuantang
resolve_yuan_tang = find_yuantang  # 旧测试兼容


__all__ = [
    "YuanTang",
    "find_yuantang",
    "resolve_yuantang",
    "HOUR_NAMES",
    "UPPER_HOURS",
    "LOWER_HOURS",
]
