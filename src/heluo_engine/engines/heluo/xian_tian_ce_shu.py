"""六十四卦爻先天策数（原典《河洛真数》L1795–L1807）

本模块实现起例卷之下「六十四卦爻先天策数」的两套推演，并用原典两个
算例逐段对拍。**只有算式自洽的一路真正实现**，另一路明确拒算。

## 规则原文（L1798 / L1804）

L1798（总纲）：

    「凡占卦，看演得何卦，阴阳数得若干为**祖数**，分上下体，动爻因之。
      如**上体卦动**，则以动爻因十而加大数，以卦数因零而加小数。
      次加本卦祖数及动爻，并上下卦错综数合成千百十零，
      分为**元会运世**。」

L1804（另一路）：

    「**下卦动**以卦数因十而加大数，以动爻数因零而加小数。
      次加本卦祖数及动爻数，并内外卦错综数，
      合成千百十零，布为元会运世是也。」

## 八卦数：先天策数用洛书序，与起例卷 L174 那套并存

起例卷 L174 作「一坎　二坤　三震　四巽　中五寄宫　六乾　七兑　八艮　九离」。
若拿它去读先天策数的算例，**三处全错**：

    | 卦 | 算例原文 | L174 | 洛书序 |
    |----|----------|------|--------|
    | 兑 | 「内卦兑二数」（L1801、L1807 各一见） | 7 ✗ | 2 ✓ |
    | 离 | 「外卦离三数」（L1807） | 9 ✗ | 3 ✓ |
    | 巽 | 「上卦巽五数」（L1801） | 4 ✗ | 5 ✓ |

三处全中洛书序（乾1 兑2 离3 震4 巽5 坎6 艮7 坤8），无一命中 L174，
故判定**先天策数自成一套卦数**，与起例卷 L174 并存（与节候卦双轨同理）。
本仓处理方式：只把**有算例直接文字佐证**的离/兑/巽列为确证值，
其余五卦**不填默认值**——填了就等于替原典补规则。
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: 先天策数中**有原典算例直接佐证**的卦数（洛书序）。
#: 佐证出处：L1801「上卦巽五数」「内卦兑二数」、L1807「外卦离三数」「内卦兑二数」。
BAGUA_NUM_CONFIRMED: dict[str, int] = {"离": 3, "兑": 2, "巽": 5}

#: 洛书序全套，仅作备查与人工核对用。
#: 乾/震/坎/艮/坤 五卦在先天策数算例中**未出现**，本仓不据此推算。
BAGUA_NUM_LUOSHU_REFERENCE: dict[str, int] = {
    "乾": 1, "兑": 2, "离": 3, "震": 4, "巽": 5, "坎": 6, "艮": 7, "坤": 8,
}

#: 起例卷 L174 那套卦数，与上表**并存**，勿混用。
BAGUA_NUM_QILUO_L174: dict[str, int] = {
    "坎": 1, "坤": 2, "震": 3, "巽": 4, "乾": 6, "兑": 7, "艮": 8, "离": 9,
}

#: 上体卦动第二段的验算常数（见模块底部「原典算例核验」）。
#: 原文：「下五个一百为五百，又下五个九十为四百五十，又下二个五为一十」
UP_PART_SEG2_ITEMS: tuple[int, int, int] = (500, 450, 10)
UP_PART_SEG2_SUM: int = 960  # 500 + 450 + 10


@dataclass(frozen=True)
class CeShuResult:
    """先天策数推演结果。

    ``ce_shu == 0`` 表示**拒算**——原典证据不足以确定该卦的策数，
    此时 ``caveat`` 必非空，调用方**不得**把 0 当成一个真实的策数。
    """

    gua: str
    moving_yao: int                     # 动爻位 0=初 … 5=上
    zu_shu: int                         # 祖数（阴阳数）
    moving_part: str                    # "上体" / "下卦" / "?"（拒算时可能为 "?"）
    ce_shu: int                         # 最终策数；0 = 拒算
    yuan_hui_yun_shi: tuple[int, int, int, int]   # 元/会/运/世；拒算时为 (0,0,0,0)
    steps: tuple[str, ...] = field(default_factory=tuple)
    caveat: str = ""                    # 拒算原因 / 原典歧义登记

    @property
    def refused(self) -> bool:
        """是否因原典证据不足而拒算。"""
        return self.ce_shu == 0


def split_yuan_hui_yun_shi(ce_shu: int) -> tuple[int, int, int, int]:
    """千百十零 → 元会运世（L1807「以千为元，百为会，十为运，零为世」）。

    中孚例另注「除万不用，以二六八五四位布为元会运世」，
    即策数过万时**弃去万位**只取四位，故先除万再分解。
    对不足四位者 ``% 10000`` 是恒等操作，不改变结果。
    """
    n = ce_shu % 10000
    return (n // 1000, (n // 100) % 10, (n // 10) % 10, n % 10)


def _refuse(gua: str, moving_yao: int, zu_shu: int, moving_part: str,
            steps: list[str], caveat: str) -> CeShuResult:
    return CeShuResult(
        gua=gua, moving_yao=moving_yao, zu_shu=zu_shu, moving_part=moving_part,
        ce_shu=0, yuan_hui_yun_shi=(0, 0, 0, 0), steps=tuple(steps), caveat=caveat,
    )


def compute_xian_tian_ce_shu(
    gua: str,
    upper: str,
    lower: str,
    moving_yao: int,
    zu_shu: int,
) -> CeShuResult:
    """按原典 L1804/L1807 推演先天策数（**仅下卦动一路**）。

    上体卦动一路见 :func:`compute_shangti_ce_shu`，该路因原典算例自相
    矛盾而拒算，不在此实现。

    推演严格照原典的三段分解式与累加次序（睽例）：

        第一段：以卦数（下卦）因十而加大数，下卦动则动爻数因零而加小数
                → 下 N 个百、下 N 个九十、下 N 个小数，三项相加
        第二段：再以动爻数乘之，下 M 个百、下 M 个九十、下 M 个 M
        累加前两段，再加祖数，再加外卦数 + 内卦数 + 动爻数

    :param gua: 卦名，如「睽」
    :param upper: 上卦名，如「离」
    :param lower: 下卦名，如「兑」
    :param moving_yao: 动爻位 0=初 … 5=上（本路要求 < 3）
    :param zu_shu: 祖数（该卦阴阳数之和）
    """
    steps: list[str] = [
        f"卦={gua}（上{upper}下{lower}），动爻={moving_yao + 1}爻，祖数={zu_shu}"
    ]

    if moving_yao >= 3:
        steps.append("动爻在上体，属「上体卦动」一路，本函数不受理")
        return _refuse(gua, moving_yao, zu_shu, "上体", steps,
                       "上体卦动一路原典算例自相矛盾，不敢臆算；"
                       "请改用 compute_shangti_ce_shu 查看登记")

    up_num = BAGUA_NUM_CONFIRMED.get(upper)
    low_num = BAGUA_NUM_CONFIRMED.get(lower)
    if up_num is None or low_num is None:
        missing = [n for n, v in (("上卦" + upper, up_num), ("下卦" + lower, low_num)) if v is None]
        steps.append("卦数缺：" + "、".join(missing))
        return _refuse(gua, moving_yao, zu_shu, "下卦", steps,
                       f"八卦数未裁决（{'、'.join(missing)}），不敢臆算")

    yao_no = moving_yao + 1

    # 第一段：下卦数因十而加大数 → 20；小数 = 动爻数 → 2
    # 原文「下二十个一百为二千，又下二十个九百为一千八百，次下二十个二为四十」
    # 注：原文「九百」为讹，按其自述结果「一千八百」反推应为「九十」。
    da_shu = low_num * 10
    c1 = da_shu * 100 + da_shu * 90 + da_shu * yao_no
    steps.append(
        f"第一段：下卦{lower}数{low_num}因十而加大={da_shu}，小数=动爻{yao_no} → "
        f"下{da_shu}个百为{da_shu * 100}，下{da_shu}个九十为{da_shu * 90}（原文作「九百」，讹），"
        f"下{da_shu}个{yao_no}为{da_shu * yao_no}，共{c1}"
    )

    # 第二段：再以动爻数乘之 —— 原文「下二个一百…又下二个九十…又下二个二」
    c2 = yao_no * 100 + yao_no * 90 + yao_no * yao_no
    steps.append(
        f"第二段：再以动爻{yao_no}数乘之 → 下{yao_no}个百为{yao_no * 100}，"
        f"下{yao_no}个九十为{yao_no * 90}，下{yao_no}个{yao_no}为{yao_no * yao_no}，共{c2}"
    )

    sub = c1 + c2
    steps.append(f"累加前两段 = {sub}")

    # 原文分两步加：「又加祖数一百九十二，合得四千四百一十六」
    #                        「又加外卦离三数，内卦兑二数，动爻二数，共合得四千四百二十三数」
    with_zu = sub + zu_shu
    steps.append(f"加祖数{zu_shu} → {with_zu}")

    tail = up_num + low_num + yao_no
    steps.append(
        f"又加外卦{upper}数{up_num} +内卦{lower}数{low_num} +动爻{yao_no} = +{tail}"
    )

    total = with_zu + tail
    steps.append(f"合计={total}")
    steps.append(f"除万不用 → {total % 10000}，布元会运世 {split_yuan_hui_yun_shi(total)}")

    return CeShuResult(
        gua=gua, moving_yao=moving_yao, zu_shu=zu_shu, moving_part="下卦",
        ce_shu=total, yuan_hui_yun_shi=split_yuan_hui_yun_shi(total),
        steps=tuple(steps), caveat="",
    )


def compute_shangti_ce_shu(gua: str, upper: str, lower: str,
                           moving_yao: int, zu_shu: int) -> CeShuResult:
    """上体卦动一路 —— **恒拒算**，只返回原典歧义登记。

    原因（原典 L1801 中孚上九例）：除首段外的每一段都能复算，但**首段
    的分解式与其自述总数对不上**，且差额来源无法从原典确定：

        原文三项：6000（六十个百）+ 5400（六十个九十）+ 120（六个二十）
        = **11520**
        原文自述总数：**11712**     → 差 **192**

    192 恰为下一段开头「假如睽九二爻祖数一百九十二」的睽卦祖数，
    而非本卦祖数 129。且原文后半段全链都从 11712 起算并自洽：

        11712 + 960（第二段 500+450+10）= 12672 ✓
        12672 + 13（巽5+兑2+上爻6）   = 12685 ✓

    即：**基数 11712 是真实被使用的，总数链条自洽；唯独首段分解式算不出它。**
    无论把 192 解释成串例、印讹还是漏项，都是在替原典补规则，故不推算。
    """
    steps = [
        f"卦={gua}（上{upper}下{lower}），动爻={moving_yao + 1}爻，祖数={zu_shu}",
        "属「上体卦动」一路（L1798）",
        f"第一段照字面分解：60×100={60 * 100}，60×90={60 * 90}，6×20={6 * 20}"
        f"，合计 {60 * 100 + 60 * 90 + 6 * 20}；原典自述 11712，差 "
        f"{11712 - (60 * 100 + 60 * 90 + 6 * 20)}",
        f"第二段（上卦{upper}数）：500+450+10={UP_PART_SEG2_SUM}，自洽",
        "首段基数不可复算 → 拒算",
    ]
    return _refuse(
        gua, moving_yao, zu_shu, "上体", steps,
        "上体卦动例（中孚 L1801）首段分解式得 11520，与原典自述 11712 不符，"
        "差 192——恰为下例睽卦祖数（疑串例），本仓未裁决，不敢臆算；"
        "首段之后各段（+960、+13、除万取 2685）均自洽，"
        "但基数既不可复算，策数与元会运世一律拒算。",
    )


#: 原典两个算例（L1801 中孚 / L1807 睽），供对拍。
#: ``reproducible=False`` 表示该例因原典歧义拒算，其策数仅作登记不得强求对拍。
ORIGINAL_CASES: tuple[tuple[str, str, str, int, int, int, bool], ...] = (
    ("中孚", "巽", "兑", 5, 129, 12685, False),   # 上体卦动，四阳二阴，首段歧义
    ("睽",   "离", "兑", 1, 192, 4423, True),     # 下卦动，逐段自洽
)


__all__ = [
    "BAGUA_NUM_CONFIRMED", "BAGUA_NUM_LUOSHU_REFERENCE", "BAGUA_NUM_QILUO_L174",
    "UP_PART_SEG2_ITEMS", "UP_PART_SEG2_SUM",
    "CeShuResult", "split_yuan_hui_yun_shi",
    "compute_xian_tian_ce_shu", "compute_shangti_ce_shu", "ORIGINAL_CASES",
]
