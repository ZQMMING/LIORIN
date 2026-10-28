"""阴阳二数多寡随时吉凶论（起例卷之中 L31–L105）

本模块把原典逐条立名的「数格」拆成三类，**互不混淆**：

1. :func:`classify_shu_ge` —— **纯数值档**。只看天数/地数本身，
   原典给了完整可判的数值区间，照录成表。L50/L53/L74/L77/L83/L87 六条
   早已在 ``guajie.judge_shu_xiong`` 内，本模块是它们之外的补全
   （阳数偏少、以强伏弱、地数至弱、地数得中、地数太过、阴数偏少、
   天地俱羸、阴阳相战）。

2. :func:`judge_shu_he_shi` —— **节气窗口档**。原典对部分数格给了
   「自某节气后至某节前」的时令窗口，须有出生公历日才能定，
   只给月份判不了。

3. :func:`judge_lu_shu` / :func:`xingbie_xiang_bei` —— **禄数与性别向背**。
   原典 L34/L56/L61/L80/L95/L105 五处明写男女向背，此前引擎签名无性别
   入参而全部落空。

原典**未言**或**自相矛盾**者，一律进 :data:`REFUSED`，返回「未裁决」而非
编一个结果。逐条理由见该表。

## 变更履历（**不进 conflict 输出字段**）

conflict 是面向用户的判词文本，只陈述事实；修订历史留在文档里。

- 2026-10-07 首版在 ``阳数偏少`` 的 conflict 栏写作「与 L83 判语相反」——
  **这是错的**。经 20158 行全库取证证伪：L995「阴令得之犹可喜，若生阳月必孤睽」
  与 L1076「阴令忧危浅，阳月有大殃」方向相同（都是阴月令较轻、阳月令较重），
  差别只在严重度（L83 更重）。两诗断原文见
  ``tests/heluo/test_refusal_corrections_round2.py::TestPoemsAgreeInDirection``。
- 2026-10-07 同日：首版把「天数至弱 L38」与「三阳奇偶合象 L99」整条拒算，
  亦经全库取证证明属**过度保守**，两条均已撤销拒算并实现。
  依据同见 ``test_refusal_corrections_round2.py``。

## 本卷关键常数（均有明文）

    L42 「天数二十五为正」        → :data:`TIAN_ZHENG` = 25
    L70 「地数三十」              → :data:`DI_ZHENG` = 30
    L42 「论九是阳之一策」        → 策 = 9
    「余」= 天数−25／地数−30      → :func:`yuan_shu`
"""
from __future__ import annotations

from dataclasses import dataclass

#: L42「天数二十五为正」
TIAN_ZHENG = 25
#: L70「地数三十」（L65/L71/L72 复称「地数三十」为正）
DI_ZHENG = 30
#: L42「论九是阳之一策」
CE = 9


def yuan_shu(tian_shu: int, di_shu: int) -> tuple[int, int]:
    """「余」＝天数−25（阳数之正）／地数−30（阴数之正）。

    L50「天数二十六以上……**余偶数**」、L53「……**余奇数**」——
    两条以奇偶相区分，必须先定义余。
    """
    return tian_shu - TIAN_ZHENG, di_shu - DI_ZHENG


def _tian_state(t: int) -> str:
    if t < TIAN_ZHENG:
        return "不足"
    if t == TIAN_ZHENG:
        return "足"
    return "有余"


def _di_state(d: int) -> str:
    if d < DI_ZHENG:
        return "不足"
    if d == DI_ZHENG:
        return "足"
    return "有余"


@dataclass(frozen=True)
class ShuGeRule:
    """一条有名有姓的数格（逐字摘录原典）。"""

    name: str                       # 数格名，与原典标题一致
    citation: str                   # 转录行号 + 首句
    tian_band: str                  # 天数条件（人话）
    di_band: str                    # 地数条件（人话）
    verdict: str                    # 原典判语（逐字摘录，不改写）
    match: str                      # "tian_di" | "tian" | "di"
    lo_t: int = 0                   # 闭区间下界（match 含 tian 时有效）
    hi_t: int = 999                 # 闭区间上界
    lo_d: int = 0
    hi_d: int = 999
    #: 非矩形的地数判据：命中当且仅当 ``di == di_eq`` **或** ``di <= di_le``。
    #: 二者皆 None 时才走 [lo_d, hi_d] 矩形。L58「地数三十**或**至十二以下」
    #: 正是这种「等于某值或低于某值」的非连续集合，用矩形表达会漏判。
    di_eq: int | None = None
    di_le: int | None = None
    yu_parity: int | None = None    # 余数奇偶限定：0=偶 1=奇 None=不限
    yu_side: str = ""               # "tian" | "di" | ""
    conflict: str = ""              # 与其他数格的重叠说明
    #: 非矩形的判域：``(lo_t, hi_t, lo_d, hi_d)`` 矩形的**并集**，原典任一支命中即算。
    #:
    #: 原典 L726「阴阳偏胜偏负」是四个并列条件的并集——天数二十四以下而地数三十、
    #: 地数二十八以下而天数二十五、天数二十六以上而地数三十、地数三十二以上而天数二十五。
    #: 任何**单一**矩形都表达不了它，压成一个必错其中一支，故增设本字段。
    alternatives: tuple[tuple[int, int, int, int], ...] = ()


# ═══════════════════════════════════════════════════════════════════
# 数格表（严格按原典出场先后排列；顺序即冲突时的取用次序）
# ═══════════════════════════════════════════════════════════════════

SHU_GE_TABLE: tuple[ShuGeRule, ...] = (
    ShuGeRule(
        name="天数至弱", citation="L38「天数至弱　天数一十有五，如只得四五六七八数，"
                                  "此不满一策，是谓至弱。」",
        tian_band="4–8（不足一策）", di_band="不限", match="tian", lo_t=4, hi_t=8,
        verdict="「天数至弱，男子不宜。艰辛不利，忧苦多为。……阴令可乖，阳令非时。」"
                "「夫阳数至弱，辰戌丑未月时生，必克父于童稚之时。」",
    ),
    ShuGeRule(
        name="天数不足", citation="L42「天数不足　天数二十五为正，只如得九或十、十一……"
                                  "十六至二十四数，皆谓之不足。」",
        tian_band="9–24", di_band="不限", match="tian", lo_t=9, hi_t=24,
        verdict="「论九是阳之一策，十八已为一策之余，虽云不足，即非至弱之比，犹庶几可也。」"
                "「大抵不足二字，未有十全如意，当先丧父，阳男尤验，阴女同。」",
    ),
    ShuGeRule(
        name="孤阳不偶", citation="L50「孤阳不偶　天数二十六以上，至四十以下，余偶数，"
                                  "而地数只得三十是也。」",
        tian_band="26–40 且 余偶", di_band="= 30", match="tian_di",
        lo_t=26, hi_t=40, lo_d=30, hi_d=30, yu_parity=0, yu_side="tian",
        verdict="「乃阳数有余，阴数无余。」「有阳无阴，是太燥也……所以损子刑妻，"
                "性多刚躁，好辨是非。」",
    ),
    ShuGeRule(
        name="孤阳自偶", citation="L53「孤阳自偶　天数三十一至四十一、五十一，余奇数，"
                                  "地数只得三十是也。」",
        tian_band="26–40 且 余奇（原典作「三十一至四十一、五十一」）", di_band="= 30",
        match="tian_di", lo_t=26, hi_t=40, lo_d=30, hi_d=30, yu_parity=1, yu_side="tian",
        verdict="「本无阴以应之，而阳极自生其阴，是谓刚亢反和之象，多是先难后易，"
                "先贫后富，先微后贵。」诗曰「壮岁艰辛勤苦立，晚年得势始荣欣」。",
    ),
    ShuGeRule(
        name="阳数偏少", citation="L56「阳数偏少　天数二十有五，只得四、五、六至二十四，"
                                  "地数三十是也。」",
        tian_band="4–24", di_band="= 30", match="tian_di", lo_t=4, hi_t=24, lo_d=30, hi_d=30,
        verdict="「乃阳数不足，阴数足也。此谓之有阴无阳，得阳数偏少，利女子，不利男子。」"
                "「有福无寿，有官无权，有妻无子，有子刑妻，业多劳碌。」",
        conflict="与 L83「以弱敌强」在 (天数≤24, 地数=30) 处**完全重叠**，"
                  "且两条**同向、只严重度有别**："
                  "L995「阴令得之犹可喜，若生阳月必孤睽」"
                  "与 L1076「阴令忧危浅，阳月有大殃」同指「阴月令较轻、阳月令较重」，"
                  "其中 L83 判词更重（「必主灭顶之凶」「斩戮在边场」），"
                  "且 L1079 明给缓解条件。本条判域更窄（地数恰 30），L83 更宽（地数 30–60+），"
                  "属「先特殊、后一般」。原典未明写先后，故按出场次序取本条并把两条全量列出。",
    ),
    ShuGeRule(
        name="以强伏弱", citation="L58「以强伏弱　如天数三十、四十、五十之类，"
                                  "地数三十或至十二以下是也。」",
        tian_band="≥30（原典举 30/40/50「之类」）", di_band="= 30 或 ≤12（13–29 原典未言）",
        match="tian_di", lo_t=30, hi_t=999, di_eq=30, di_le=12,
        verdict="「若值阳月令不妨，逢阴月令颇有恃势致凶之象。……若胜之不以理，"
                "则必悖而有亢，上下不安矣，至此则虽贵而不善终。」",
    ),
    ShuGeRule(
        name="地数至弱", citation="L65「地数至弱　地数三十，只得八、九、十、十一、"
                                  "十二数者，是谓至弱。」",
        tian_band="不限", di_band="8–12", match="di", lo_d=8, hi_d=12,
        verdict="「阴数至弱，女人不堪，幼克父母，六眷难安，不得其家……」"
                "「若子午卯酉月时生必克父母于幼稚之时。」",
    ),
    ShuGeRule(
        name="地数不足", citation="L70「地数不足　地数三十，只得十八者，是谓之不足。」",
        tian_band="不限", di_band="< 30", match="di", lo_d=0, hi_d=29,
        verdict="「大抵此数女子得之福必鲜，若子午卯酉月时生必克母于童稚之年……」"
                "「当先丧母，阴男阳女尤验。」",
    ),
    ShuGeRule(
        name="地数得中", citation="L71「地数得中　地数三十，得三十二至四十五以下，"
                                  "皆谓得中。」",
        tian_band="不限", di_band="32–45", match="di", lo_d=32, hi_d=45,
        verdict="「但八九月立冬前，卦名爻位吉，理长有援，主富贵荣华，可知矣。」",
    ),
    ShuGeRule(
        name="地数太过", citation="L72「地数太过　地数三十，如得五六十以上者，皆谓太过。」",
        tian_band="不限", di_band="≥50", match="di", lo_d=50, hi_d=999,
        verdict="「此时天寒地冻，当有屈伏钦肃之象。得此数者，主刑伤战戮，少得喜终。」"
                "「在十一月前，十月立冬后，未冬至前，却为不害。」",
    ),
    ShuGeRule(
        name="孤阴背阳", citation="L74「孤阴背阳　地数三十至五十、六十，余偶数，"
                                  "而天数只二十五是也。」",
        tian_band="= 25", di_band="30–60 且 余偶", match="tian_di",
        lo_t=25, hi_t=25, lo_d=30, hi_d=60, yu_parity=0, yu_side="di",
        verdict="「乃阳无余，阴数有余。……积阴之数，无阳不成。」",
    ),
    ShuGeRule(
        name="孤阴向阳", citation="L77「孤阴向阳　天数二十五，地数得四十至六十以下，"
                                  "余奇数是也。」",
        tian_band="= 25", di_band="40–60 且 余奇", match="tian_di",
        lo_t=25, hi_t=25, lo_d=40, hi_d=60, yu_parity=1, yu_side="di",
        verdict="「乃阴数过，阳数足。」「本无阳以应之，而阴极自生阳，即寒谷回春之意。」"
                "诗曰「有阳能改过，有阴奸盗随」。",
    ),
    ShuGeRule(
        name="阴数偏少", citation="L80「阴数偏少　地数十八至二十八，天数二十五是也。」",
        tian_band="= 25", di_band="18–28", match="tian_di",
        lo_t=25, hi_t=25, lo_d=18, hi_d=28,
        verdict="「乃阳数足，阴数不足。阴数无用与不足，同是谓阴数偏于少也。」"
                "「利男子不利女人……阳月令得之，多主富贵，阴月令得之，多主贫穷。」",
    ),
    ShuGeRule(
        name="以弱敌强", citation="L83「以弱敌强　地数三十至四十、五十、六十以上，"
                                  "天数只得二十四以下是也。」",
        tian_band="≤24", di_band="≥30", match="tian_di", lo_t=0, hi_t=24, lo_d=30, hi_d=999,
        verdict="「乃地数太过，天数不足。阴月令逢之，尚庶几，阳月令逢之，"
                "必主灭顶之凶。」",
        conflict="与 L56「阳数偏少」在 (天数≤24, 地数=30) 处重叠且**同向不同severity**"
                  "（诗断一致，仅本条判词更重）。原典未明写先后，见 L56 栏。",
    ),
    ShuGeRule(
        name="安和自宁", citation="L87「安和自宁　天数二十五，地数三十，"
                                  "乃天地二数无余无不足是也。」",
        tian_band="= 25", di_band="= 30", match="tian_di",
        lo_t=25, hi_t=25, lo_d=30, hi_d=30,
        verdict="「阴阳数俱平者，依卦中吉凶断之。诸数惟此数为最佳也，吉凶极定。」",
    ),
    ShuGeRule(
        name="天地俱羸", citation="L90「天地俱羸　天数二十四以下，地数二十九以下，"
                                  "是乃阴阳二数俱不足者也。」",
        tian_band="≤24", di_band="≤29", match="tian_di", lo_t=0, hi_t=24, lo_d=0, hi_d=29,
        verdict="「二气俱羸不固坚，须知名利不能全。有官难显福难守，尤恐天年不可延。」"
                "「男宜为僧道，妇多尼妓。」",
    ),
    ShuGeRule(
        name="阴阳相战", citation="L93「阴阳相战　盖阳数多，阴数少，"
                                  "或阴阳二数俱多，清浊相干者是也。」",
        tian_band=">25（阳数多）", di_band="<30（阴数少）或 >30（俱多）",
        match="tian_di", lo_t=26, hi_t=999, lo_d=0, hi_d=999,
        verdict="「阴阳相战必然伤，二亲兄弟克离乡。……贵者遇之多毁折，"
                "富人值此讼频访。」",
    ),
    # ── 起例卷之上 L726–L732 三条（2026-10-08 补）────────────────────
    # 出场次序在 L93 之后，故仍按原典先后追加在表末，取用次序不受影响。
    ShuGeRule(
        name="阴阳偏胜偏负",
        citation="L726「天数二十四以下而地数三十，地数二十八以下而天数二十五，"
                 "天数二十六以上而地数三十，地数三十二以上而天数二十五，"
                 "此阴阳偏胜偏负，更元堂安非其位，必主孤寡下贱。」",
        tian_band="四支并列：≤24／=25／≥26／=25（见 alternatives）",
        di_band="四支并列：=30／≤28／=30／≥32（见 alternatives）",
        match="tian_di", lo_t=0, hi_t=999, lo_d=0, hi_d=999,
        alternatives=((0, 24, 30, 30), (25, 25, 0, 28),
                      (26, 999, 30, 30), (25, 25, 32, 999)),
        verdict="「此阴阳偏胜偏负，更元堂安非其位，必主孤寡下贱。」",
        conflict="⚠️ 原典在本条后缀了一个**本卷未定义**的条件——「更元堂安非其位」。"
                 "「安位／非其位」的判法通读 20158 行未得定义（元堂爻位只到「六位贵贱」"
                 "L627 一处，未涉安位与否），故此处**只按数格四支落码，"
                 "该附加条件标为未定义、不参与判定**。这不是遗漏，是不敢臆补。"
                 "四支各自与既有数格重叠：①与 L56「阳数偏少」(≤24/=30) 同域、"
                 "②与 L80「阴数偏少」(=25/18–28) 同域、③与 L50「孤阳不偶」"
                 "(26–40 余偶/=30) 同域、④与 L74「孤阴背阳」(=25/30–60 余偶) 同域；"
                 "但 L726 判语（孤寡下贱）是四支**共用的总判**，与各条自身判语不冲突。",
    ),
    ShuGeRule(
        name="以强凌弱",
        citation="L729「天数四五十以上而地数不足，名以强凌弱，以尊凌卑，"
                 "在阳月生人大贵，七八九十冬月生横恶凶死。」",
        tian_band="≥40（原典作「四五十以上」，41–49 未言，按「以上」取下界）",
        di_band="<30（不足，依 L70「地数三十，只得十八者，是谓之不足」）",
        match="tian_di", lo_t=40, hi_t=999, lo_d=0, hi_d=29,
        verdict="「名以强凌弱，以尊凌卑，在阳月生人大贵，七八九十冬月生横恶凶死。」",
        conflict="与 L58「以强伏弱」在 (天数≥40, 地数≤12) 处重叠。二者**同格异名、"
                 "同向**：L58「若值阳月令不妨」（阳月无凶）vs 本条「在阳月生人大贵」"
                 "（阳月大吉）；L58「逢阴月令颇有恃势致凶之象」vs 本条"
                 "「七八九十冬月生横恶凶死」（冬月即阴月，凶）。阈值 L58 为 ≥30、"
                 "本条为 ≥40，本条更窄，属「先一般、后特指」。原典未明写二者是一格，"
                 "故两存并列，不合并、不择一。",
    ),
    ShuGeRule(
        name="以下犯上",
        citation="L732「地数五六十以上而天数不足，名以下犯上，以卑逾尊，"
                 "在阴月生人富贵，而水以后夏至前生人最恶下贱。」",
        tian_band="<25（不足，依 L42「天数二十五为正」以下皆不足）",
        di_band="≥50（原典作「五六十以上」，与 L72「地数太过」同下界）",
        match="tian_di", lo_t=0, hi_t=24, lo_d=50, hi_d=999,
        verdict="「名以下犯上，以卑逾尊，在阴月生人富贵，"
                "而水以后夏至前生人最恶下贱。」"
                "（末句「水」为讹字，四本转录俱作「水」，按语义当作「冬」，"
                "此处逐字照录不擅改；理由见 covers_gap/起例卷之上原典覆盖缺口_20261007.md）",
        conflict="与 L83「以弱敌强」(天数≤24, 地数≥30) 大范围重叠，且**同向**："
                 "L83「阴月令逢之，尚庶几，阳月令逢之，必主灭顶之凶」"
                 "与本条「在阴月生人富贵，而（冬）以后夏至前生人最恶下贱」"
                 "——阴月令较轻/较吉、阳月令（夏至后至冬前）大凶，方向完全一致。"
                 "L83 判域更宽（地数≥30），本条更窄（地数≥50）。两存不择一。",
    ),
)


def _matches(rule: ShuGeRule, t: int, d: int) -> bool:
    if rule.alternatives:
        # 并集判域：原典「……，……，……，……」四句并列，任一支命中即算。
        # 此处**直接返回**，不再叠加下面的矩形/余数判据——
        # 原典每一支各自已是一句完整判据，叠加只会把未列的支也误收进来。
        return any(lo_t <= t <= hi_t and lo_d <= d <= hi_d
                   for lo_t, hi_t, lo_d, hi_d in rule.alternatives)
    if rule.match in ("tian", "tian_di") and not (rule.lo_t <= t <= rule.hi_t):
        return False
    if rule.match in ("di", "tian_di"):
        if rule.di_eq is not None or rule.di_le is not None:
            # 非矩形判据：「等于某值 或 低于某值」
            if not (d == rule.di_eq or (rule.di_le is not None and d <= rule.di_le)):
                return False
        elif not (rule.lo_d <= d <= rule.hi_d):
            return False
    if rule.match == "tian_di" and rule.name == "阴阳相战":
        # 原典：「阳数多，阴数少，或阴阳二数俱多」——地数两端皆可，唯地数=30 除外
        # （地数=30 为阴数无余，不属「少」也不属「俱多」的清浊相干）。
        if not (d < DI_ZHENG or d > DI_ZHENG):
            return False
    if rule.yu_parity is not None:
        t_yu, d_yu = yuan_shu(t, d)
        y = t_yu if rule.yu_side == "tian" else d_yu
        # 「余偶数／余奇数」的前提是**有余**：余 0 是「无余」（安和自宁），
        # 不是「余偶」。若不排除 y==0，(25,30) 会同时命中孤阴背阳与安和自宁。
        if y <= 0 or y % 2 != rule.yu_parity:
            return False
    return True


def classify_shu_ge(tian_shu: int, di_shu: int) -> tuple[ShuGeRule, ...]:
    """返回**全部**命中的数格，按原典出场先后排列。

    不用「首个命中即返回」——原典 L56「阳数偏少」与 L83「以弱敌强」
    在 (天数≤24, 地数=30) 处**判语相反且原典未裁先后**，返回全部命中
    并保留各条 conflict 说明，交由上层显式披露，不静默挑一条。
    """
    return tuple(r for r in SHU_GE_TABLE if _matches(r, tian_shu, di_shu))


def primary_shu_ge(tian_shu: int, di_shu: int) -> ShuGeRule | None:
    """取原典出场最先的命中数格；无命中返回 ``None``。"""
    hits = classify_shu_ge(tian_shu, di_shu)
    return hits[0] if hits else None


def shu_ge_conflicts(tian_shu: int, di_shu: int) -> tuple[str, ...]:
    """返回命中数格中带冲突登记的说明（供上层显式披露）。

    同一次冲突通常被互相指认的两条各写一遍，这里按 ``conflict`` 文本去重，
    免得输出里同一件事说两遍；两条数格名仍都在 ``classify_shu_ge`` 的结果里。
    """
    hits = [r for r in classify_shu_ge(tian_shu, di_shu) if r.conflict]
    # 冲突至少要有**两个当事方**才会成立：单条规则自带的 conflict 栏只是
    # 「一旦重叠该怎么说」的说明，本身并不构成冲突。故只在两条以上同时命中
    # 且都带 conflict 时才报，避免在重叠区之外误报。
    if len(hits) < 2:
        return ()
    return (f"{hits[0].name}：{hits[0].conflict}",)


# ═══════════════════════════════════════════════════════════════════
# 援阴／援阳（L100–L101）
# ═══════════════════════════════════════════════════════════════════

#: L100「阳弱而余二四六八者，谓之援阴」
JU_YIN_NUMBERS: tuple[int, ...] = (2, 4, 6, 8)
#: L100「阳弱而余一三七九者，谓之援阳」
JU_YANG_NUMBERS: tuple[int, ...] = (1, 3, 7, 9)
#: L100「二为坤母道也……四为巽……六为乾……八为艮」
JU_YIN_GUA: dict[int, str] = {2: "坤", 4: "巽", 6: "乾", 8: "艮"}
#: L101「一为坎陷也……三为震……五为艮……七为兑……九为离」
JU_YANG_GUA: dict[int, str] = {1: "坎", 3: "震", 5: "艮", 7: "兑", 9: "离"}


def judge_you_yin_yang(tian_shu: int, di_shu: int) -> dict:
    """判「援阴／援阳」（L100–L101）。

    L100 明文只对**阳弱**（天数不足）立此二名：
        「阳弱而余二四六八者，谓之援阴。阳弱而余一三七九者，谓之援阳。」

    「阳弱」语境下「余」的所指，原典未明写死，本实现取**天数本身**，
    依据是 L101 的断语「**九者阳之亢也，其卦为离**」——九正是 L42「阳之一策」，
    只有按「天数本身为九」才讲得通；若按「余 = 25−天数」，则得 16，
    不落在 1/3/5/7/9 内，此句将永无触发。另一读法已登记在 :data:`REFUSED`。

    L101 另对**阴弱**（地数不足）作对称叙述：
        「阴若弱而援二四六八之阴者，主先贱后贵……阴弱而援一三七九之阳者，
          此弱而又弱也。」——取**地数本身**。
    """
    t_yu, d_yu = yuan_shu(tian_shu, di_shu)
    out: dict = {"tian_yu": t_yu, "di_yu": d_yu,
                 "yu_reading": "阳弱/阴弱语境下「余」取该数本身（依 L101「九者阳之亢」）"}

    if tian_shu < TIAN_ZHENG:
        out["tian_weak"] = True
        if tian_shu in JU_YIN_NUMBERS:
            out["name"], out["gua"] = "援阴", JU_YIN_GUA[tian_shu]
        elif tian_shu in JU_YANG_NUMBERS:
            out["name"], out["gua"] = "援阳", JU_YANG_GUA[tian_shu]
        else:
            out["name"], out["gua"] = "", ""
    else:
        out["tian_weak"] = False
        out["name"], out["gua"] = "", ""

    if di_shu < DI_ZHENG:
        out["di_weak"] = True
        out["di_jie"] = ("先贱后贵" if di_shu in JU_YIN_NUMBERS else
                         "弱而又弱" if di_shu in JU_YANG_NUMBERS else "")
    else:
        out["di_weak"] = False
        out["di_jie"] = ""
    return out


# ═══════════════════════════════════════════════════════════════════
# 阴阳禄数（L105）
# ═══════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class LuShuHit:
    """一条禄数命中。``which`` 只记「天/地」，**不替原典指定**。"""

    value: int
    which: str        # "天" / "地" —— 原典只说「凡数得三十六」，未指明天数还是地数
    name: str         # 老阳之禄 / 少阳之禄 / 老阴之禄 / 少阴之禄
    xing_bie: str     # "利男不利女" / "利女不利男"
    gender_fit: bool | None   # 给定性别时：True=相利，False=相妨，None=未给性别


#: L105 逐字：「凡数得三十六为老阳之禄数，二十八为少阳之禄数，利男不利女。
#:           二十四为老阴之禄，三十二为少阴之禄，利女不利男。」
LU_SHU_TABLE: tuple[tuple[int, str, str], ...] = (
    (36, "老阳之禄", "利男不利女"),
    (28, "少阳之禄", "利男不利女"),
    (24, "老阴之禄", "利女不利男"),
    (32, "少阴之禄", "利女不利男"),
)


def judge_lu_shu(tian_shu: int, di_shu: int, gender: str = "") -> tuple[LuShuHit, ...]:
    """判阴阳禄数（L105）。

    原典作「凡数得三十六为老阳之禄数」——**未指明是天数还是地数**。
    本函数对天、地两数各自比对，命中即登记为独立标记，
    **不替原典指定归属**；两数同值亦照实各记一条。
    """
    gender = (gender or "").strip().lower()
    hits: list[LuShuHit] = []
    for value, name, xb in LU_SHU_TABLE:
        for which, num in (("天", tian_shu), ("地", di_shu)):
            if num != value:
                continue
            if not gender:
                fit: bool | None = None
            elif xb.startswith("利男"):
                fit = gender == "male"
            else:
                fit = gender == "female"
            hits.append(LuShuHit(value=value, which=which, name=name,
                                 xing_bie=xb, gender_fit=fit))
    return tuple(hits)


# ═══════════════════════════════════════════════════════════════════
# 性别向背（L34 / L56 / L61 / L80 / L95）
# ═══════════════════════════════════════════════════════════════════

#: L34「利于阳者，自十一月冬至后，至四月终……利男子，不利女人也」
YANG_YUE_LING_MONTHS: frozenset[int] = frozenset({11, 12, 1, 2, 3, 4})
#: L61「利于阴者，自五月一阴生，至十月阴胜极，利女人不利男子也」
YIN_YUE_LING_MONTHS: frozenset[int] = frozenset({5, 6, 7, 8, 9, 10})


@dataclass(frozen=True)
class XingBeiResult:
    """一条性别向背判定。"""

    rule: str          # 原典条款（L34/L56/…）
    favor: str         # "男" / "女"
    against: str       # 被不利的一方
    reason: str        # 原典理由（逐字摘录）
    applies: bool      # 该条是否适用于当前 (天数, 地数, 月份, 性别)


def xingbie_xiang_bei(tian_shu: int, di_shu: int, birth_month: int,
                      gender: str = "") -> tuple[XingBeiResult, ...]:
    """逐条判性别向背。性别未给（``gender=""``）时 ``applies`` 一律为 False。

    逐条原文：

        L34 「然利于阳者，自十一月冬至后，至四月终，宜阳数……**利男子，不利女人**也。」
        L61 「然利于阴者，自五月一阴生，至十月阴胜极，**利女人不利男子**也。」
        L56 「得阳数偏少，**利女子，不利男子**。」（天数 4–24 且地数 30）
        L80 「凡此有阳无阴之数，**利男子不利女人**……阳月令得之，多主富贵，
              阴月令得之，多主贫穷。」（天数 25 且地数 18–28）
        L95 「但阳月令男命阳不足谓之无阳，阴月令女命阴不足谓之无阴，
              二者失时悖理，**皆主凶**。」（此处不限男女向背，只判凶）
    """
    g = (gender or "").strip().lower()
    yang_month = birth_month in YANG_YUE_LING_MONTHS
    yin_month = birth_month in YIN_YUE_LING_MONTHS
    out: list[XingBeiResult] = []

    def add(rule: str, favor: str, against: str, reason: str, applies: bool) -> None:
        out.append(XingBeiResult(rule, favor, against, reason, applies))

    add("L34", "男", "女",
        "「然利于阳者，自十一月冬至后，至四月终，宜阳数，喜阳爻，利男子，不利女人也。」",
        bool(g) and yang_month)
    add("L61", "女", "男",
        "「然利于阴者，自五月一阴生，至十月阴胜极，利女人不利男子也。」",
        bool(g) and yin_month)

    yang_pian_shao = 4 <= tian_shu <= 24 and di_shu == DI_ZHENG
    add("L56", "女", "男",
        "「此谓之有阴无阳，得阳数偏少，利女子，不利男子。」", bool(g) and yang_pian_shao)

    yin_pian_shao = tian_shu == TIAN_ZHENG and 18 <= di_shu <= 28
    add("L80", "男", "女",
        "「凡此有阳无阴之数，利男子不利女人……阳月令得之，多主富贵，"
        "阴月令得之，多主贫穷。」",
        bool(g) and yin_pian_shao and (yang_month or yin_month))
    return tuple(out)


def judge_ming_wu_yin_yang(tian_shu: int, di_shu: int, birth_month: int,
                           gender: str = "") -> tuple[str, str | None]:
    """命无阴阳（L95）。

        「但阳月令男命阳不足谓之无阳，阴月令女命阴不足谓之无阴，
          二者失时悖理，皆主凶。」

    :returns: ``(说明, 凶否)``。性别未给或该条不适用时凶否为 ``None``。
    """
    g = (gender or "").strip().lower()
    if not g:
        return ("「大凡命不论阴阳男女，但阳月令男命阳不足谓之无阳，阴月令女命阴不足谓之无阴」"
                "——未给性别，本条不判。", None)
    yang_month = birth_month in YANG_YUE_LING_MONTHS
    yin_month = birth_month in YIN_YUE_LING_MONTHS
    if g == "male" and yang_month and tian_shu < TIAN_ZHENG:
        return (f"阳月令{birth_month}月男命，天数{tian_shu}不足（正=25）→ 阳月令阳不足"
                f"谓之无阳，「二者失时悖理，皆主凶」（L95）", True)
    if g == "female" and yin_month and di_shu < DI_ZHENG:
        return (f"阴月令{birth_month}月女命，地数{di_shu}不足（正=30）→ 阴月令阴不足"
                f"谓之无阴，「二者失时悖理，皆主凶」（L95）", True)
    return ("阳月令男命阳未不足／阴月令女命阴未不足，或月令与性别不构成该条的"
            "「失时悖理」组合（L95 未言其余情形）", None)


__all__ = [
    "TIAN_ZHENG", "DI_ZHENG", "CE", "yuan_shu",
    "JIE_QI_ORDER", "CHUNQI_JQ", "solar_jq_index", "judge_chun_qi_qi_ou",
    "ShuGeRule", "SHU_GE_TABLE", "classify_shu_ge", "primary_shu_ge",
    "shu_ge_conflicts",
    "JU_YIN_NUMBERS", "JU_YANG_NUMBERS", "JU_YIN_GUA", "JU_YANG_GUA", "judge_you_yin_yang",
    "LuShuHit", "LU_SHU_TABLE", "judge_lu_shu",
    "YANG_YUE_LING_MONTHS", "YIN_YUE_LING_MONTHS",
    "XingBeiResult", "xingbie_xiang_bei", "judge_ming_wu_yin_yang",
    "REFUSED",
]


# ═══════════════════════════════════════════════════════════════════
# 三阳奇偶合象（L99 / L714）——本卷唯一一条**节气窗口 + 数奇偶**的规则
# ═══════════════════════════════════════════════════════════════════

#: 节气序（jq 0＝冬至）。全库**单一来源 jiegua.JIEQI_24**（2026-10-08 批次 G）。
#: sxtwl 的 getJieQi() 亦用同一序：0 冬至 1 小寒 2 大寒 3 立春 4 雨水 ……
#: ⚠ 此前此处、jiegua.JIEQI_24、jiehhou.SOLAR_TERMS 三处各抄一份（内容相同）。
#:   二十四节气序只能有一处定义——三份各改各的，索引错位要到出卦时才炸。
from .jiegua import JIEQI_24 as JIE_QI_ORDER  # noqa: E402

#: L1121「自冬至后至雨水前」——落在其间的是小寒、大寒、立春三气
CHUNQI_JQ: frozenset[int] = frozenset({1, 2, 3})


def solar_jq_index(date_str: str) -> int | None:
    """出生公历日 → 当时所处节气序（0＝冬至）。无 sxtwl 或日期不合法则返回 ``None``。

    注意：``sxtwl`` 的 ``getJieQi()`` **只在交节当天**返回该节气的序号，
    其余日期返回哨兵 255。故此处须自该日**向前回溯**，取最近一个交节日
    ——首版直接取 ``getJieQi()``，导致一年 360 多天都落到 255、窗口判定整年失效。

    **返回 None 时不得默认判吉凶**——原典给的是节气窗口，判不出窗口就不是
    「吉」也不是「不吉」，必须让调用方显式处理。
    """
    try:
        import sxtwl
    except ImportError:
        return None
    try:
        y, m, d = (int(x) for x in str(date_str).split("-")[:3])
    except (ValueError, AttributeError, TypeError):
        return None
    try:
        from datetime import date as _date, timedelta as _td
    except ImportError:                                   # pragma: no cover
        return None

    NO_JIEQI = 255
    cur = _date(y, m, d)
    try:
        for _ in range(40):                              # 最长一个节气约 31 日
            jq = sxtwl.fromSolar(cur.year, cur.month, cur.day).getJieQi()
            if jq is not None and jq != NO_JIEQI and 0 <= jq < len(JIE_QI_ORDER):
                return jq
            cur -= _td(days=1)
    except Exception:
        return None
    return None


def judge_chun_qi_qi_ou(tian_shu: int, birth_date: str = "") -> tuple[str, bool | None]:
    """三阳奇偶合象（L99，并经 L714 平行印证）。

        L1121「凡人生时所得阴阳之数，当合时得令，**自冬至后至雨水前**，
                正三阳交泰之时，**除天数二十五之外，有奇数之余**，
                即君子之合象也。如偶数，是从小人舍君子……死无疑矣。」

        L714 （独立平行例证）「凡男命阳月生者，**冬至以后，雨水前**，
                **天数不及二十五，只余奇**，便妙。……如不及二十五，
                更余偶数……亦凶。」

    两处合起来规则完整：**窗口**与**余的归属**都各有两条独立表述，
    且都指「天数−25」——「除天数二十五之外」与「天数不及二十五，只余奇」
    是同一算法的两种写法。故本条 2026-10-07 由拒算转为实现。

    :returns: ``(说明, 是否合象)``。日期不合法或无 sxtwl 时返回 ``(说明, None)``，
        **不得**当成「不合」。
    """
    note = ("L1121「自冬至后至雨水前，正三阳交泰之时，除天数二十五之外，"
            "有奇数之余，即君子之合象也。如偶数……死无疑矣」；"
            "L714「男命阳月生者，冬至以后，雨水前，天数不及二十五，只余奇，便妙」")

    yu = tian_shu - TIAN_ZHENG
    if not birth_date:
        return (f"未给出生公历日，无法定「冬至后至雨水前」之窗口，不判。{note}",
                None)
    jq = solar_jq_index(birth_date)
    if jq is None:
        return (f"无法由出生日「{birth_date}」定出所处节气（缺 sxtwl 或日期不合法），"
                f"不判。{note}", None)
    in_window = jq in CHUNQI_JQ
    jn = JIE_QI_ORDER[jq] if 0 <= jq < len(JIE_QI_ORDER) else str(jq)
    where = f"生时处「{jn}」（冬至后至雨水前={ '在其间' if in_window else '不在其间' }）"
    if not in_window:
        return (f"{where}，不在 L1121 所限之窗口内，本条不适用。{note}", None)
    if yu == 0:
        return (f"{where}，天数{tian_shu} 足而无余；L1121 判「除天数二十五之外」者，"
                f"足数不在其列，不判。{note}", None)
    if yu % 2 == 1:
        return (f"{where}，天数{tian_shu} 余 {yu}（奇）→ 君子之合象，吉。{note}", True)
    return (f"{where}，天数{tian_shu} 余 {yu}（偶）→ 「从小人舍君子……死无疑矣」，凶。{note}",
            False)



# ═══════════════════════════════════════════════════════════════════
# 原典未言／自相矛盾 → 明确拒算登记
# ═══════════════════════════════════════════════════════════════════

#: 每条 = (原典条款, 为什么不判, 正确裁决需要什么)
REFUSED: tuple[tuple[str, str, str], ...] = (
    ("L38 首句「天数一十有五」的**基线数字**（判据本身已实现并获外部印证，见 SHU_GE_TABLE「天数至弱」）",
     "该短语与 L950「天数二十五为正」冲突（L950 同时是「九至二十四谓不足、"
     "**即非至弱之比**」的出处）。"
     "**但判据不依赖这个基线**：L938「如只得四五六七八数，此不满一策，是谓至弱」"
     "自足，「策＝9」使 4–8 自洽；以正＝25 或正＝15 两种读法推算，落点都是「至弱＝天数 4–8」。"
     "故 2026-10-07 首轮的整条拒算属过度保守，已撤销。"
     "网络第二证据（2026-10-07，heluo_engine/docs/天数至弱异文核查_20261007.md）**支持这个拆分**："
     "取得的第二来源识典古籍 CADAL02094383「起例卷中正文」同样作「一十有五」，"
     "但**判据半句与「論九是陽之一策」逐字一致**，冲突只集中在首句那一个数字上。"
     "该源系影印图 OCR，且本地底本即中华典藏（不算独立第二源），"
     "两源或同属一刊本系，影印原页未取得——故基线仍列待考。",
     "仅剩这一句的**基线数字**待定：天数之正究竟是 25 还是 15。"
     "取得识典 pageId 7516987006715445298 的影印页图（或另一独立刊本）即可定谿。"),

    ("L45「天数得中　二十五之外，更至二策二十以下者，非过非不及……」",
     "该条本身把 26–45 判为得中（可实现），但其下的三分「春分前谓之顺时，立春前为太过，"
     "春分后为不及」需要**节气日界**，且「立春前为太过」与 L47「天数太过」的定义"
     "（「合少而多，谓之太过」）用词冲突。",
     "须先厘清「太过」一词在本卷是否前后同义，再接节气窗口。"),

    ("L36「阳数得中，自正月立春后，三阳交泰，此时阳气方亨」——**下界有据，上界原典未言**",
     "起点「立春」有旁证：L932 自述 + L333 命例「有人坤卦初六爻安元堂正在"
     "**正月节气内生**……值三阳交泰之时」，两见皆以立春为起点。"
     "但原典**从未给出上界**（春分？惊蛰？下一个节气？），"
     "且同词在 L1121 指另一窗口，措辞不统一。"
     "2026-10-07 首轮把理由写成「两窗口无法取舍」，不准确——"
     "拒算的真因是**上界缺失**，不是起点有争议。",
     "须定案「立春后」的终点落在哪个节气。"),

    ("L35「阳数不及，在十一月冬至之后，十二月未泰之时」",
     "下界（冬至后）明确，但上界「十二月未泰之时」无明确定义，"
     "无法确定终点落在哪个节气或哪一天。",
     "须定案「十二月未泰之时」的终点。"),

    ("L47「天数太过　天数合少而多，谓之太过……四十以下至五十、六十者，三月至四月无妨」",
     "「合少而多／合多而少」是与天数无关的**相对**判法，原典未定义「合」；"
     "「四十以下至五十、六十者，三月至四月无妨」的区间上下限本身含混"
     "（四十以下却含五十、六十？）。",
     "须先定义「合」的含义并厘清该区间。"),

    ("L49「太过有尤」／L73「地数太过有悔」／L86「阴数太过有悔」——**门槛原典全库无载**",
     "三条都要求**卦中阳（阴）爻多寡**，但计数门槛在 20158 行全库中找不到："
     "「多数」0 命中；「过半」2 命中（均与爻多寡无关）；"
     "「三爻／四爻／五爻」各 16–20 处**全部指爻位**（二五爻得位、上九、"
     "第四爻等），无一指爻数；「多寡」7 处皆指天地二数或多寡论题，非爻数。"
     "命例 L1376「其数阳多阴少」、L1382「阳少阴多」亦为定性语，无阈值。"
     "另「所立爻阴阳」引擎其实有（元堂爻），但缺爻多寡门槛即无法起判。",
     "须定案「卦中阳爻多」的下限（如四爻以上为多？三爻为平？）。"
     "本表不替原典假设阈值——六爻三平，三为平还是四为多，全库无凭。"),

    ("L110–L113（顺逆四象与豁免三条件）",
     "同属四元组判定，且 L112/L113 的豁免需「辞吉」——爻辞吉凶需卦爻上下文，"
     "本函数无从判「辞吉」。",
     "须接入卦爻与爻辞吉凶数据源。"),

    ("L114「男子行阴令，居阴爻，主心气柔弱」／L115「女子行阳令，居阳爻，主情性刚强」",
     "需「居某爻」的爻位信息，无入参。",
     "须接入爻位数据源。"),

    ("L99 首句「正三阳交泰之时」这一**措辞**（规则本身已实现，见 judge_chun_qi_qi_ou）",
     "「三阳交泰」一词在 L932（自正月立春后）与 L1121（自冬至后至雨水前）"
     "分指两个窗口，措辞不统一；子平常法以寅月（三阳已成）为三阳交泰，"
     "故 L932 的用法更合常法。但**这只影响措辞，不影响规则**——"
     "L99 的窗口「冬至后至雨水前」与其判据「天数余奇则吉」已由 L714 独立平行表述："
     "「凡男命阳月生者，冬至以后，雨水前，天数不及二十五，只余奇，便妙。」"
     "故 2026-10-07 首轮的拒算属过度保守，已撤销。",
     "仅剩措辞统一问题：三阳交泰究竟专指寅月，还是可兼指冬至后雨水前。"),

    ("L100–L101 中「阳月令得阴数，余有二四者轻、六八者重」「阴月令得阳零数者……」",
     "余数与卦的对应（2坤4巽6乾8艮 / 1坎3震5艮7兑9离）已实现于"
     "``judge_you_yin_yang``；但「轻／重」的程度差别与「零数」的完整断语"
     "需要逐句处理，本轮未逐条实现。",
     "须逐句拆解 L100/L101 的断语强度分级。"),

    ("L104/L108「天数属阳，利男子，喜阳爻」中的「喜阳爻」",
     "「喜／不喜阳爻」需卦中阳爻多寡，无入参。",
     "须接入卦六爻数据源。"),

    ("L105 阴阳禄数中「凡数得三十六」的数之归属",
     "原典未指明是天数还是地数。本实现对天、地两数各自比对并如实标记归属，"
     "**但不替原典指定**——若原典本意只指其中一数，则会出现两条命中。",
     "须定案禄数查的是天数、地数，还是二数之合。"),

    ("L100–L101「阳弱而余二四六八」中「余」的所指",
     "「余」在**有余**语境下确指「天数−25」（L50/L53 已明），但在**阳弱**（天数不足）"
     "语境下无明确定义：可解为天数本身，也可解为「25−天数」的亏，两者给出的卦完全不同。"
     "本实现取**天数本身**，依据是 L101「**九者阳之亢也，其卦为离**」——九正是"
     "L42「阳之一策」，按「余=25−天数」读则得 16，该句将永无触发。"
     "另一读法未裁决。",
     "须定案「阳弱」语境下「余」是本数还是亏数；一俟定案，"
     "``judge_you_yin_yang`` 的 ``yu_reading`` 分支须同步切换。"),
)
