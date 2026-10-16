"""H10: 卷十《河洛叅评》独立体系（金锁银匙歌起数 + 五行部参评定位）

独立建档，不与卦爻断主链（guajie.py）混入。算法与原文出自
K3-447_009 卷十《河洛叅评》（陈抟著/邵雍述/史应选重订影印本）：

  起参评秘诀·金锁银匙歌（原文逐句）：
    1. 阴阳俱用二千祖   —— 不论阴阳男女，八字所属干支，虚加二千于算盘千位上为祖
    2. 日至生时百中数   —— 只就日时地支：日支数至时支（含起止），一字准一百数，加百位
    3. 时日皆从子上轮 十零本位月休睹
                       —— 从子轮起数至日支字数 + 数至时支字数，和数：十位=和//10、零位=和%10
                          "月休睹"=只用日时，不用月令干支
    4. 岁君水火廿七加   —— 当生年纳音水火 +27
    5. 木金虚度五十土   —— 纳音木金不加（虚度）、土 +50
    6. 再将一二三四五 配却水火木金土
                       —— 纳音水配1、火配2、木配3、金配4、土配5（加于总数）
    7. 得策寻纳看当生   —— 总数百千十零四位数 → 依当生年纳音所属五部寻行（诗断）
    8. 时日顺冲还共语   —— 顺数/逆数两法（逆数=从时支数至日支），各得诗断

  起大运例：阴阳俱用二千同，只将大运替时轮（弃时支，以大运地支对日支算，余一一依前例）
  起流年例：流年之法是何如，千上同前自不殊，只把日支对太岁，替却日时一例推

  参评例（原典）：一数有水火木金土之五部，不拘男女之命，各循其部而求之；
    此数名目谨依皇极之例，以千百十零为定局。
    五行部参评每数分三层：上层=男命、中层=女命、下层=男女相共大运流年。
    中层女命数空无字者乃贫贱夭折之命；下层大运流年数空无字者重者损寿轻者破耗刑克。

原典复算（测试基线）：
  戌日寅时，乙卯（纳音水）：2000+500+14(十1零4)+27+1 = 2542 ✓（原文"二千五百四十二"）
  申日申时，戊午（纳音火）：2000+1300+18(十1零8)+27+2 = 3347 ✓（原文"三千三百四十七"）
  戌日寅时逆数（乙卯水）：2000+900+14+27+1 = 2942 ✓（原文"二千九百四十二"）
"""

from __future__ import annotations

import os

from typing import Optional

# 地支顺序（子=0）
_BRANCH_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 60甲子纳音（与 guajie._NAYIN 一致，独立维护）
_NAYIN = {
    "甲子": "金", "乙丑": "金", "丙寅": "火", "丁卯": "火", "戊辰": "木", "己巳": "木",
    "庚午": "土", "辛未": "土", "壬申": "金", "癸酉": "金", "甲戌": "火", "乙亥": "火",
    "丙子": "水", "丁丑": "水", "戊寅": "土", "己卯": "土", "庚辰": "金", "辛巳": "金",
    "壬午": "木", "癸未": "木", "甲申": "水", "乙酉": "水", "丙戌": "土", "丁亥": "土",
    "戊子": "火", "己丑": "火", "庚寅": "木", "辛卯": "木", "壬辰": "水", "癸巳": "水",
    "甲午": "金", "乙未": "金", "丙申": "火", "丁酉": "火", "戊戌": "木", "己亥": "木",
    "庚子": "土", "辛丑": "土", "壬寅": "金", "癸卯": "金", "甲辰": "火", "乙巳": "火",
    "丙午": "水", "丁未": "水", "戊申": "土", "己酉": "土", "庚戌": "金", "辛亥": "金",
    "壬子": "木", "癸丑": "木", "甲寅": "水", "乙卯": "水", "丙辰": "土", "丁巳": "土",
    "戊午": "火", "己未": "火", "庚申": "木", "辛酉": "木", "壬戌": "水", "癸亥": "水",
}

# 纳音 → 加数（岁君水火廿七加 / 木金虚度五十土）
_NAYIN_ADD = {"水": 27, "火": 27, "金": 0, "木": 0, "土": 50}
# 纳音 → 配数（再将一二三四五，配却水火木金土）
_NAYIN_PEI = {"水": 1, "火": 2, "木": 3, "金": 4, "土": 5}
# 纳音 → 参评五部（得策寻纳看当生）
_NAYIN_PART = {"水": "水部", "火": "火部", "木": "木部", "金": "金部", "土": "土部"}


def get_nayin_element(year_gan: str, year_zhi: str) -> str:
    """年柱纳音五行（60甲子纳音表）。"""
    return _NAYIN.get(year_gan + year_zhi, "")


def _branch_index(branch: str) -> int:
    try:
        return _BRANCH_ORDER.index(branch)
    except ValueError:
        return -1


def _count_branches(a: str, b: str) -> int:
    """地支 a 数至 b 的字数（含起止，顺行）。同支=绕满一圈 13 字（原典申日申时例）。"""
    i, j = _branch_index(a), _branch_index(b)
    if i < 0 or j < 0:
        return 0
    if i == j:
        return 13
    if j > i:
        return j - i + 1
    return 12 - i + j + 1


def _count_from_zi(branch: str) -> int:
    """从子字轮起数至该支的字数（含起止，子=1）。"""
    i = _branch_index(branch)
    return i + 1 if i >= 0 else 0


def qishu(
    day_zhi: str,
    hour_zhi: str,
    nayin_element: str,
    direction: str = "顺",
) -> dict:
    """金锁银匙歌起数（命数）。

    返回：{qian, bai, shi, ling, total, steps, part}
    direction: '顺'（日支数至时支，默认）/ '逆'（时支数至日支，原典顺冲两法）
    """
    if direction == "逆":
        n100 = _count_branches(hour_zhi, day_zhi)
        d100 = f"{hour_zhi}时支逆数至{day_zhi}日支"
    else:
        n100 = _count_branches(day_zhi, hour_zhi)
        d100 = f"{day_zhi}日支顺数至{hour_zhi}时支"
    shi_ling_sum = _count_from_zi(day_zhi) + _count_from_zi(hour_zhi)
    shi, ling = divmod(shi_ling_sum, 10)
    add = _NAYIN_ADD.get(nayin_element, 0)
    pei = _NAYIN_PEI.get(nayin_element, 0)
    total = 2000 + n100 * 100 + shi * 10 + ling + add + pei
    qian, rem = divmod(total, 1000)
    bai, rem = divmod(rem, 100)
    shi2, ling2 = divmod(rem, 10)
    return {
        "qian": qian, "bai": bai, "shi": shi2, "ling": ling2, "total": total,
        "part": _NAYIN_PART.get(nayin_element, ""),
        "steps": [
            "阴阳俱用二千祖：虚加二千为千位祖数",
            f"日至生时百中数：{d100}，隔{n100}字×100={n100 * 100}",
            f"时日皆从子上轮：{day_zhi}={_count_from_zi(day_zhi)}、{hour_zhi}={_count_from_zi(hour_zhi)}，"
            f"和{shi_ling_sum}→十位{shi}零位{ling}（月休睹：不用月令）",
            f"岁君纳音{nayin_element}：加{add}（水火27/土50/木金虚度）＋配数{pei}（水1火2木3金4土5）",
            f"得策：{total}（千{qian}百{bai}十{shi2}零{ling2}）→ 寻{_NAYIN_PART.get(nayin_element, '')}",
        ],
    }


def qishu_dayun(day_zhi: str, dayun_zhi: str, nayin_element: str, direction: str = "顺") -> dict:
    """起大运例：阴阳俱用二千同，只将大运替时轮。

    弃八字时支不用，以大运地支对日支算；其余一一依金锁银匙歌前例。
    """
    return qishu(day_zhi, dayun_zhi, nayin_element, direction)


def qishu_liunian(day_zhi: str, taisui_zhi: str, nayin_element: str, direction: str = "顺") -> dict:
    """起流年例：千上同前自不殊，只把日支对太岁，替却日时一例推。

    不用日时地支，只将流年太岁地支对日支算；其余照金锁银匙歌前例。
    """
    return qishu(day_zhi, taisui_zhi, nayin_element, direction)


# 五行部参评诗断表：data/heluo/canping/（原文建档，见 README.md）
# 当前仅录入金锁银匙歌+参评例+已读样例（水部/火部开头数条）；
# 全表（5部×60干支×三层）待全卷逐页录入。
_CANPING_DIR: Optional[str] = None


def set_canping_dir(path: str) -> None:
    """设置参评诗断表数据目录（默认 data/heluo/canping/）。"""
    global _CANPING_DIR
    _CANPING_DIR = path


def _canping_dir() -> str:
    if _CANPING_DIR:
        return _CANPING_DIR
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "..", "..", "..", "data", "heluo", "canping")


# ── 卷十诗断 OCR 原始语料检索（v1，2026-09-12 重读校对） ──────────────
# 语料：data/heluo/canping/raw_shici_p24-58.json
#   = K3-447_009 卷十《河洛叅评》五行部参评诗断表 p22-58 v1（逐页放大重读，与 K3-448_008 第二印本对照）。
# 已实证（与金锁银匙歌原典例逐字吻合）：
#   2542 例（戌日寅时乙卯水）→ "掌中秋月扇/举动好风生" 于 p29 丑酉列（水部）
#   2942 例（戌日寅时逆数）  → "玉壺無別物/赤蟻似蜂屯" 于 p34 辰宾列（水部）
#   3347 例（未未列）        → "道是無形光/鴻毛草上風/陰陽互寒暑" 于 p53 未未列（火部）
# 异文清单见 算法原文对照核证表 第十三节；448 编号对照见 448_duizhao.json。

# ── 金/土部诗断语料（v1，2026-09-12 逐页转录） ────────────────────────
# 语料：data/heluo/canping/raw_shici_jintu_448.json
#   = K3-448_008.pdf 金部 p59-73（74 编号）+ 土部 p74-91（82 编号），五部参评全本（448 册）。
#   447_009 卷十残本仅水火木三部，金土部以 448_008 为唯一全本来源。
# 结构：每编号 6 句 = 男命2 + 女命2 + 岁运2（与 447/448 水部同构）；特殊页照录并注明。
# 编号体系：448 编号非唯一键（同编号不同页可为异文，如金部三一七/三一八/三三二二、
#   土部三七二/三七三/三七五/三七七 均多次出现且文不同），检索必须带 (part,page,no)。
# 特殊编号：金部 p70「天二一」、p66「三三」旁注辰卯從革八、土部 p91「三三七九」内覈天六九。
# 缺句待证：金部 p66 三三(5句)/p68 二四一七(4句)；土部 p78 二四六二/p79 三〇六八/
#   p83 二八七〇/p85 三七三(各4句)、p89 三七二(7句)、p91 三三七九(10句，含内覈)。
# 异文待证：土部 p74 二三二六「形盡(畫?)棋猶閣/毫端争一莖(著?)」（两读均录注）。

def search_raw_poem(keyword: str) -> list:
    """在卷十诗断 OCR 原始语料中检索关键字。

    返回 [(页, 列头, 句), ...]；keyword 为空或语料缺失时返回 []。
    """
    import json as _json
    p = os.path.join(_canping_dir(), "raw_shici_p24-58.json")
    try:
        with open(p, encoding="utf-8") as f:
            data = _json.load(f)
    except (OSError, ValueError):
        return []
    out = []
    for pg in data.get("pages", []):
        for col in pg.get("cols", []):
            for ln in col.get("lines", []):
                if keyword and keyword in ln:
                    out.append((pg.get("page"), col.get("header", ""), ln))
    return out


def load_raw_shici_jintu() -> list:
    """载入金/土部诗断语料（raw_shici_jintu_448.json）。

    返回 items 列表（每条 {part,page,no,note,lines}）；文件缺失返回 []。
    """
    import json as _json
    p = os.path.join(_canping_dir(), "raw_shici_jintu_448.json")
    try:
        with open(p, encoding="utf-8") as f:
            data = _json.load(f)
    except (OSError, ValueError):
        return []
    return data.get("items", [])


def search_raw_poem_448(
    keyword: str = "",
    part: str = "",
    no: str = "",
) -> list:
    """在金/土部诗断语料（448_008 编号制）中检索。

    keyword 匹配句文；part ∈ {jin, tu}；no 匹配编号（原样，如 "2510"/"天二一"）。
    返回 [(part, page, no, note, line), ...]。448 编号非唯一键，同编号跨页异文全部返回，
    调用方须以 (part,page,no) 定位。
    """
    out = []
    for it in load_raw_shici_jintu():
        if part and it.get("part") != part:
            continue
        if no and it.get("no") != no:
            continue
        for ln in it.get("lines", []):
            if keyword and keyword not in ln:
                continue
            out.append((it.get("part"), it.get("page"), it.get("no"),
                        it.get("note", ""), ln))
    return out


__all__ = [
    "get_nayin_element", "qishu", "qishu_dayun", "qishu_liunian",
    "set_canping_dir", "search_raw_poem", "search_raw_poem_448",
    "load_raw_shici_jintu", "NAYIN_ADD", "NAYIN_PEI", "NAYIN_PART",
]

# 模块级导出（供外部只读访问）
NAYIN_ADD = _NAYIN_ADD
NAYIN_PEI = _NAYIN_PEI
NAYIN_PART = _NAYIN_PART
