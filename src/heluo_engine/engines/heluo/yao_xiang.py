"""爻辞取象断语（原典 L741「凡看爻辞依不得周易正解……触类而长之，思过半矣」）

2026-10-08 新增。原典这一段是《河洛真数》里少见的**「凭一个字断」**的取象法：
不看卦爻辞的吉凶，只看**辞中出现了哪个字**，便得一条断语。审计指出
`guajie._yao_buji` 只有一张十三字凶词黑名单（凶危死灾咎厉悔亡败伤困病讼），
既不做取象，也完全没有吉类取象——本模块补的就是这一层。

═══ 取证（2026-10-08，四本独立转录交叉核对）═══

    L741  凡看爻辞依不得周易正解，如命值数卦爻位俱好，又有化工元气，宜以富贵
          上命断之。纵爻辞不佳，或至凶，此人富显中不免有患难坎坷，甚者子息少，
          不令终。文王作易，**近取诸身，远取诸物**，如言龙则必贵。二月至八月生
          者，吉余欠利。言马则前程远大，言牛则功名迟钝，而体大身壮，必见富饶，
          言羊则身分虽不及牛，而进取必锐，科目或早发，只不极贵耳。言永或富或贵，
          其人必贪汗。言鹤必主清高。言龟必主遁窜。言鸿必主飞腾。言鸟同。如卦数
          凶，此走空浮薄之夫。**言月生望前者佳。言木生春夏者荣。** 言血必刑克
          伤残。言忧泣必有克害。言甘必受用。言苦必困穷。言金非贵必富。言肉必
          多饮食。男人言朋亡，一生交游非人，女人必为孀妇。触类而长之，思过半矣。

    —— 续修四库点校本 L1067–L1077 与之逐字一致；河洛真数OCR 本 L3863 亦见
       「夫言月生望前者佳言木生春夏者榮」。三本俱在，非孤本孤证。

═══ 为什么分成「无条件」与「带条件」两档 ═══

十八条里**只有四条带成立条件**，其余十四条是无条件取象：

    带条件：言龙（二月至八月生者吉，余欠利）／言木（生春夏者荣）／
            言月（生望前者佳）／言朋（按性别分断）／
            言鸟（「如卦数凶则走空浮薄」——前提挂在卦数上）
    无条件：言马、言牛、言羊、言永、言鹤、言龟、言鸿、言血、言忧泣、
            言甘、言苦、言金、言肉

条件齐全的条目**可以进判定链**；其余条原典只给了断语、**没给取字之外的
可算判据**，且「言鸟同」一句原典自己就挂了「如卦数凶」这个前提。故本模块对
十四条一律返回「已识别 + 断语 + 提示未参与判定」，**不硬判吉凶**：
把断语写进 evidence 供人参考，但 direction 恒为 NEUTRAL。

这是「可以落码就不要挂」与「不凭猜补规则」两条的交界处：能落的是**取字与断语的
对应关系**（原典明载，十八条全覆盖），不能落的是**吉凶方向**（原典未给可算判据）。

═══ 与既有取象层的边界 ═══

* ``guajie._yao_buji`` 是**反向**的：只按凶词判凶，13 字黑名单，不做取象。
  两者不互相覆盖。
* 本模块的「条件组」需要生月，故入参是**公历月（1–12）**，不是节气月支。
  月支换算另见调用方；此处不自行推断月支→公历月的近似（那正是化工层
  2026-10-07 修掉的错误）。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class YaoXiangHit:
    """一条命中的爻辞取象。"""
    key: str                 # 原典取用的字（龙/马/牛…）
    verdict: str             # 原典断语，逐字
    conditional: bool        # 是否附带成立条件
    condition: str = ""      # 条件描述（conditional 为真时有）
    satisfied: bool | None = None   # 条件是否满足；None=条件不可判
    participated: bool = False      # 是否进入判定（目前仅条件组为 True）


#: 二月至八月（含两端）——原典「二月至八月生者，吉余欠利」。
_YAN_LONG_MONTHS: frozenset[int] = frozenset({2, 3, 4, 5, 6, 7, 8})
#: 春夏——原典「言木生春夏者荣」。
_YAN_MU_MONTHS: frozenset[int] = frozenset({3, 4, 5, 6})


#: 原典取象条目，逐条照录，不改写。顺序即原典出场次序，共 **18 条**。
#:
#: ⚠ 条数口径：审计报告写「16 组」，那是把「言鸟同」并进了「言鸿」（原典确实
#: 说「同」，可视为一条）并把「男人言朋亡」另计所致。本模块**按字面逐条立 18 条**，
#: 不做合并——合并会让「言鸟」这一条在辞中单独出现时查不到。宁可多列，不可漏判。
#:
#: key 是原典用来取象的那个字；verdict 是原典断语。
YAO_XIANG_TABLE: tuple[YaoXiangHit, ...] = (
    YaoXiangHit("龙", "则必贵", True, "二月至八月生者吉，余月欠利"),
    YaoXiangHit("马", "则前程远大", False),
    YaoXiangHit("牛", "则功名迟钝，而体大身壮，必见富饶", False),
    YaoXiangHit("羊", "则身分虽不及牛，而进取必锐，科目或早发，只不极贵耳", False),
    YaoXiangHit("永", "或富或贵，其人必贪汗", False),
    YaoXiangHit("鹤", "必主清高", False),
    YaoXiangHit("龟", "必主遁窜", False),
    YaoXiangHit("鸿", "必主飞腾", False),
    # 原典「言鸟同」——「同」承接上条「言鸿」，故断语同飞腾；
    # 但其后另缀「如卦数凶，此走空浮薄之夫」是一个前提，故条件挂在**卦数凶**上。
    YaoXiangHit("鸟", "同（与言鸿同，亦主飞腾）", True, "卦数不凶方取此；卦数凶则走空浮薄"),
    YaoXiangHit("月", "生望前者佳", True, "生望前者佳"),
    YaoXiangHit("木", "生春夏者荣", True, "生春夏者荣"),
    YaoXiangHit("血", "必刑克伤残", False),
    YaoXiangHit("忧", "泣必有克害", False),
    YaoXiangHit("甘", "必受用", False),
    YaoXiangHit("苦", "必困穷", False),
    YaoXiangHit("金", "非贵必富", False),
    YaoXiangHit("肉", "必多饮食", False),
    YaoXiangHit("朋", "男人言朋亡，一生交游非人；女人必为孀妇", True, "按性别分断"),
)


#: 十八条里唯一带**公历月**条件的两组，按 key 索引。
_YAN_LONG = YAO_XIANG_TABLE[0]
_YAN_MU = YAO_XIANG_TABLE[10]
_YAN_PENG = YAO_XIANG_TABLE[17]


def scan_yao_xiang(yao_text: str, birth_month: int | None = None,
                   day_lunar: int | None = None,
                   gender: str = "", shu_gua_xiang: bool | None = None
                   ) -> list[YaoXiangHit]:
    """扫描一条爻辞，返回命中的取象条目。

    Args:
        yao_text: 爻辞（含象曰）。空/None 返回 []。
        birth_month: 出生公历月（1–12），供「言龙」「言木」判月令条件。
                      缺则这两组条件判为不可判（satisfied=None），
                      **不得**默认成一个月份——那正是 2026-10-07 化工层
                      修掉的「拿公历月硬凑月支」那类错。
        day_lunar: 农历日（1–30），供「言月生望前」判条件。
                   望 = 十五。原典只说「望前」未给精确界，
                   故此处以农历十五为界：**此界为引擎取定，原典未载，随结果披露为近似**。
        gender: "male"/"female"，供「言朋」按性别分断。
        shu_gua_xiang: 卦数是否凶，供「言鸟同」的「如卦数凶则走空浮薄」前提。
                        None = 不知 → 条件不可判。
    """
    if not yao_text:
        return []
    out: list[YaoXiangHit] = []
    for base in YAO_XIANG_TABLE:
        if base.key not in yao_text:
            continue
        if base is _YAN_LONG:
            ok = None if not birth_month else (birth_month in _YAN_LONG_MONTHS)
            out.append(_mk(base, ok))
        elif base is _YAN_MU:
            ok = None if not birth_month else (birth_month in _YAN_MU_MONTHS)
            out.append(_mk(base, ok))
        elif base.key == "月":
            ok = None if not day_lunar else (day_lunar < 15)
            out.append(_mk(base, ok, extra="（引擎以农历十五为界，此近似原典未载）"))
        elif base is _YAN_PENG:
            ok = None if not gender else (gender in ("male", "female"))
            out.append(_mk(base, ok))
        elif base.key == "鸟":
            # 前提是「卦数不凶」才取飞腾；凶则「走空浮薄」，断语方向相反。
            ok = None if shu_gua_xiang is None else (not shu_gua_xiang)
            out.append(_mk(base, ok))
        else:
            out.append(_mk(base, None))
    return out


def _mk(base: YaoXiangHit, ok: bool | None, extra: str = "") -> YaoXiangHit:
    """组装命中项。条件不明或未满足者一律不参与判定。"""
    return YaoXiangHit(
        base.key, base.verdict, base.conditional, base.condition + extra,
        ok, participated=bool(base.conditional and ok is True))


def xiang_evidence(hits: list[YaoXiangHit]) -> list[str]:
    """命中项 → evidence 文本行（逐条写清是否参与判定）。"""
    ev = []
    for h in hits:
        if h.conditional:
            state = {True: "条件满足", False: "条件不满足",
                     None: "条件不可判（缺生月/农历日）"}[h.satisfied]
            ev.append(f"爻辞取象「言{h.key}」：{h.verdict}——{state}"
                      f"（{h.condition}）"
                      + ("，**已参与判定**" if h.participated
                         else "，未参与判定"))
        else:
            ev.append(f"爻辞取象「言{h.key}」：{h.verdict}"
                      f"——原典未给取字之外的判据，**只登记不断吉凶**")
    return ev


def scan_and_evidence(yao_text: str, birth_month: int | None = None,
                      day_lunar: int | None = None, gender: str = "",
                      shu_gua_xiang: bool | None = None
                      ) -> tuple[list[YaoXiangHit], list[str]]:
    """便捷入口：扫描 + 生成 evidence。"""
    hits = scan_yao_xiang(yao_text, birth_month, day_lunar, gender, shu_gua_xiang)
    return hits, xiang_evidence(hits)