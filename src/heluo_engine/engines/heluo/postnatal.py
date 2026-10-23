"""河洛后天卦计算模块（Module 5）

负责：后天卦计算（两步法：元堂爻变 + 内外卦互换）
冻结规则依据：Architecture Freeze V1.0 §2.3 模块5

六爻表示：与原典参考实现一致
  - 1 = 阳爻
  - -1 = 阴爻
  - 变爻：1→-1, -1→1
"""

from __future__ import annotations

from dataclasses import dataclass

from .numbers import SIXTY_FOUR_HEXAGRAMS, TRIGRAM_LINES


@dataclass(frozen=True)
class PostnatalHexagram:
    """后天卦结果"""
    hexagram_name: str       # 后天卦名（互换后最终卦）
    upper_gua: str           # 后天卦上卦（互换后）
    lower_gua: str           # 后天卦下卦（互换后）
    lines: list[int]         # ⚠️ 第一步变爻后、未互换的六爻（审计保留）
                             #    最终后天卦六爻 = build_six_lines(upper_gua, lower_gua)
                             #    （2026-09-12 审核：后天元堂定位曾误用本字段，已改为用最终卦）
    step1_hexagram: str      # 第一步结果（元堂爻变后）
    step2_hexagram: str      # 第二步结果（内外卦互换后）


def compute_postnatal(
    six_lines: list[int],
    yuantang_index: int,
    xiantian_name: str | None = None,
    birth_month_yang: bool | None = None,
) -> PostnatalHexagram:
    """
    计算后天卦（C-08，两步法，冻结于 Canonical V2.0）

    算法：
    1. 取元堂爻位（0-5），翻转该爻的阴阳（1→-1, -1→1）
    2. 上下卦互换（外卦入内，内卦出外）

    至尊卦例外（总集/原典口径）：先天命卦 坎、水雷屯、水山蹇，元堂在
    九五或上六时变法不同：
      - 元堂九五（阳爻）：生阴月 不换上下（只变爻：坎→师、屯→复、蹇→谦）；
                          生阳月 换上下（两步法：坎→比、屯→豫、蹇→剥）
      - 元堂上六（阴爻）：生阴月 换上下（两步法：坎→井、屯→恒、蹇→蛊）；
                          生阳月 不换上下（只变爻：坎→涣、屯→益、蹇→渐）
    birth_month_yang: 出生月令（节气月/月柱地支）阴阳，阳支月（子寅辰午申戌）=True。
                     仅当 xiantian_name 为至尊卦且元堂在九五/上六时使用；其余情况忽略。

    纪晓岚 Golden Case 验证：
    地天泰 → 元堂六四 → 第一步：雷天大壮 → 第二步：天雷无妄
    """
    if len(six_lines) != 6:
        raise ValueError(f"six_lines must have 6 elements, got {len(six_lines)}")
    if not (0 <= yuantang_index <= 5):
        raise ValueError(f"yuantang_index must be 0-5, got {yuantang_index}")

    # 第一步：元堂爻变（1↔-1）
    step1_lines = six_lines.copy()
    step1_lines[yuantang_index] = -step1_lines[yuantang_index]

    # 至尊卦换卦判定（仅 坎为水/水雷屯/水山蹇 + 元堂九五/上六）
    zun_tri = xiantian_name in ("坎为水", "水雷屯", "水山蹇")
    zun_idx = yuantang_index in (4, 5)
    swap = True  # 是否执行第二步（上下互换）
    zun_applied = False
    if zun_tri and zun_idx and birth_month_yang is not None:
        zun_applied = True
        if yuantang_index == 4:   # 元堂九五（阳爻）
            # 生阴月：不换（只变爻）；生阳月：换（两步法）
            swap = birth_month_yang
        else:                     # 元堂上六（阴爻）
            # 生阴月：换（两步法）；生阳月：不换（只变爻）
            swap = not birth_month_yang

    # 提取上下卦（自下而上）
    step1_lower = step1_lines[:3]  # 初、二、三爻
    step1_upper = step1_lines[3:]  # 四、五、上爻

    # 转换为卦名
    step1_lower_name = _lines_to_trigram(step1_lower)
    step1_upper_name = _lines_to_trigram(step1_upper)
    step1_name = SIXTY_FOUR_HEXAGRAMS.get((step1_upper_name, step1_lower_name), "?")

    if swap:
        # 第二步：内外卦互换
        # 原内卦（下卦）变外卦，原外卦（上卦）变内卦
        final_lower = step1_upper   # 原上卦变下卦
        final_upper = step1_lower   # 原下卦变上卦
    else:
        # 至尊卦"不换"：只变爻，保持内外卦序
        final_lower = step1_lower
        final_upper = step1_upper

    final_lower_name = _lines_to_trigram(final_lower)
    final_upper_name = _lines_to_trigram(final_upper)
    final_name = SIXTY_FOUR_HEXAGRAMS.get((final_upper_name, final_lower_name), "?")

    return PostnatalHexagram(
        hexagram_name=final_name,
        upper_gua=final_upper_name,
        lower_gua=final_lower_name,
        lines=step1_lines,
        step1_hexagram=step1_name,
        step2_hexagram=final_name,
    )


def _lines_to_trigram(lines: list[int]) -> str:
    """三爻数组 → 八卦名"""
    key = tuple(lines)
    for name, triline in TRIGRAM_LINES.items():
        if triline == key:
            return name
    return "?"


# 向后兼容
resolve_yuantang = None  # alias in yuan_tang module
