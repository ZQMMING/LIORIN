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

from .nayin import NAYIN_TABLE, get_nayin_element as _nayin_get_nayin_element

# 地支顺序（子=0）
_BRANCH_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 60甲子纳音（**单一来源** nayin.NAYIN_TABLE，2026-10-22 收敛）
# 原为 canping 与 guajie 各存一份的同名副本，现两者共用 nayin.py 这一份。
# `_NAYIN` 作为**别名**保留（保名不保表）：外部有引用
# （tests/heluo/test_yuanqi_tables_fidelity.py 用 canping._NAYIN 钉死
# 「本表 ≠ yuanqi_tables.GANZHI_GUA_GROUPS 两张表，不得合并」），故不得删名。
_NAYIN = NAYIN_TABLE

# 纳音 → 加数（岁君水火廿七加 / 木金虚度五十土）
_NAYIN_ADD = {"水": 27, "火": 27, "金": 0, "木": 0, "土": 50}
# 纳音 → 配数（再将一二三四五，配却水火木金土）
_NAYIN_PEI = {"水": 1, "火": 2, "木": 3, "金": 4, "土": 5}
# 纳音 → 参评五部（得策寻纳看当生）
_NAYIN_PART = {"水": "水部", "火": "火部", "木": "木部", "金": "金部", "土": "土部"}


def get_nayin_element(year_gan: str, year_zhi: str) -> str:
    """年柱纳音五行（60甲子纳音表）。

    ⚠ 签名保持 **两柱分列**（year_gan, year_zhi）不变——外部有调用方
    （hua_gong.py 延迟导入本模块的 get_nayin_element、既有测试）。
    实际查表走 nayin.get_nayin_element（干支二字合一），此处仅转发。
    """
    return _nayin_get_nayin_element(year_gan + year_zhi)


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


# 五行部参评诗断表：heluo_engine/data/canping/（原文建档，见 README.md）
# 当前仅录入金锁银匙歌+参评例+已读样例（水部/火部开头数条）；
# 全表（5部×60干支×三层）待全卷逐页录入。
_CANPING_DIR: Optional[str] = None


def set_canping_dir(path: str) -> None:
    """设置参评诗断表数据目录（默认 heluo_engine/data/canping/）。"""
    global _CANPING_DIR
    _CANPING_DIR = path


def _canping_dir() -> str:
    """参评诗断表目录（**零路径绑定**，2026-10-24 结构性重构）。

    ⚠ 旧实现靠 `dirname(abspath(__file__))` + 四层 `..` 反推仓库根再拼
      `data/heluo/canping` —— 换任何一层目录即失效，且与主仓仓库结构硬耦合，
      河洛包无法独立部署。现改为按**包**定位（随包分发）。
    """
    if _CANPING_DIR:
        return _CANPING_DIR
    from ..._paths import pkg_data
    return str(pkg_data("canping"))


# ── 卷十诗断 OCR 原始语料检索（v1，2026-09-12 重读校对） ──────────────
# 语料：heluo_engine/data/canping/raw_shici_p24-58.json
#   = K3-447_009 卷十《河洛叅评》五行部参评诗断表 p22-58 v1（逐页放大重读，与 K3-448_008 第二印本对照）。
# 已实证（与金锁银匙歌原典例逐字吻合）：
#   2542 例（戌日寅时乙卯水）→ "掌中秋月扇/举动好风生" 于 p29 丑酉列（水部）
#   2942 例（戌日寅时逆数）  → "玉壺無別物/赤蟻似蜂屯" 于 p34 辰宾列（水部）
#   3347 例（未未列）        → "道是無形光/鴻毛草上風/陰陽互寒暑" 于 p53 未未列（火部）
# 异文清单见 算法原文对照核证表 第十三节；448 编号对照见 448_duizhao.json。

# ── 金/土部诗断语料（v1，2026-09-12 逐页转录；v2，2026-10-05 校正） ────────
# 语料：heluo_engine/data/canping/raw_shici_jintu_448.json
#   = K3-448_008.pdf 金部 p59-74（78 编号）+ 土部 p75-91（78 编号），五部参评全本（448 册）。
#   447_009 卷十残本仅水火木三部，金土部以 448_008 为唯一全本来源。
# 结构：每编号 6 句 = 男命2 + 女命2 + 岁运2（与 447/448 水部同构）；特殊页照录并注明。
# 2026-10-05 校正（详见语料 corrections 块与 heluo_engine/data/canping/448金土部女命层校正_20261005.md）：
#   A 分部误标：448 p74 四条（孤猿枝上啼／仙壇與佛塔／古稱朱陳村／畫堂春正濃）承接 p73
#     「殘燈伴空月」及策数 2326/3326/2227/3328，确属金部正文，v1 误归土部 → 已改 jin。
#     金部因此由 74 → 78 码，土部由 82 → 78 码，与五部齐一（每部 78 码）。
#   B 策数校正：PDF 文字层丢位/形近误识 26 处（如 261→2561、天二一→2621、3159→3359、
#     239→2359、3771→2771、2624→2664），据同册策数递增律并抛本影印回图复核恢复。
#   C 表头示例页：448 p75 两条（土部表头 worked example）加 is_header_example 标记，
#     非查检条目；其女命层层位归属见 448_duizhao.json jintu_nvp_rulings。
# 校正后金／土两部各 78 个编号，部内唯一且均为四位数字。
#   接口仍以 (part,page,no) 定位，以容未来跨页异文重出。
# 女命层（中层）校订结论接入 ruling 层，不回写本语料正文（正文保真原则）：
#   见 448_duizhao.json → jintu_nvp_rulings、heluo_engine/docs/定案字总表.md 附节。
# 特殊编号旁注：金部 p66「三三」旁注辰卯從革八；土部 p91「三三七九」内覈天六九。
# 缺句待证：金部 p66 三三(5句)/p68 二四一七(4句)；土部 p78 二四六二/p79 三〇六八/
#   p83 二八七〇/p85 三七三(各4句)、p89 三七二(7句)、p91 三三七九(10句，含内覈)。
# 异文待证：金部 2326「形畫棋麟閣/毫端爭一莖」（兩讀均錄注）。

#: 448 每编号 6 句的层位顺序（索引 → 层名），**单句**粒度。
CANPING_LAYERS = ("男上", "男下", "女上", "女下", "运上", "运下")

#: 层位检索词 → (lines 起始索引, 句数)。
#: 两种粒度同源，不再各自维护映射，避免再脱节：
#:   层名 {"男命","女命","岁运"} 取整层 2 句；
#:   单句标签 CANPING_LAYERS 各取 1 句。
#: 「岁运」层即「运上/运下」层（同起于索引 4），两者是同一层的两种叫法。
CANPING_LAYER_SPANS: dict[str, tuple[int, int]] = {
    "男命": (0, 2), "女命": (2, 2), "岁运": (4, 2),
    "男上": (0, 1), "男下": (1, 1),
    "女上": (2, 1), "女下": (3, 1),
    "运上": (4, 1), "运下": (5, 1),
}

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

    返回 items 列表（每条 {part,page,no,note,lines}，表头示例页另带
    ``is_header_example=True``）；文件缺失返回 []。
    """
    import json as _json
    p = os.path.join(_canping_dir(), "raw_shici_jintu_448.json")
    try:
        with open(p, encoding="utf-8") as f:
            data = _json.load(f)
    except (OSError, ValueError):
        return []
    return data.get("items", [])


#: 语料 ``part`` 内部键 → 五行部中文名（供展示与证据行）
_PART_CN = {"shui": "水部", "huo": "火部", "mu": "木部", "jin": "金部", "tu": "土部"}


def lookup_by_number(number: int, part: str | None = None) -> Optional[dict]:
    """按金锁银匙歌算出的总数检索五行部诗断条目。

    2026-10-06 接通：此前 canping 只到「能起数、能按层取句」，
    **没有把起数结果接回诗断表**——生产链路拿不到任何一条参评断语。
    本函数把两端接上：``qishu(...).total`` 即语料条目的 ``no``（四位数，
    如「二千五百四十二」→ 2542），``part`` 即五行部。

    Args:
        number: 金锁银匙歌起出的总数（int）。
        part: 五行部名（金部/土部/水部/火部/木部）。None = 不限部。

    Returns:
        命中的条目 dict（``{part,page,no,lines,...}``）；未收录返回 None。
    """
    key = str(number)
    for item in load_raw_shici_jintu():
        if str(item.get("no")) != key:
            continue
        if part and item.get("part") != part:
            continue
        return item
    return None


def judge_canping(
    day_zhi: str,
    hour_zhi: str,
    year_gan: str,
    year_zhi: str,
    gender: str = "male",
    *,
    direction: str = "顺",
) -> dict:
    """起参评 + 取本命层诗断（《河洛叅评》卷十，金锁银匙歌）。

    数据流：金锁银匙歌起数 → 总数查五行部诗断表 → 按性别取本命层两句。

    层位口径（参评例：「每数分三层：上层=男命、中层=女命、下层=男女相共
    大运流年」）经 CANPING_LAYER_SPANS 统一解释：
      male → 男命（男上/男下 2 句）；female → 女命（女上/女下 2 句）。
      大运/流年层（运上/运下）见 qishu_dayun / qishu_liunian。

    Returns:
        {ok, total, part, no, layer, lines, steps, found}
        ``found=False`` 表示起数成功但该数尚未逐页转录入语料——
        这**不是错误**，全表 5 部×数十号仍在逐页录入中（见模块头说明）。
    """
    nayin = get_nayin_element(year_gan, year_zhi)
    if not nayin:
        return {"ok": False, "found": False, "lines": [],
                "note": f"年柱{year_gan}{year_zhi}纳音未识别"}
    q = qishu(day_zhi, hour_zhi, nayin, direction)
    total = q["total"]
    item = lookup_by_number(total)
    layer = "男命" if gender == "male" else "女命"
    lines = layer_lines_448(item, layer) if item else []
    part = (item or {}).get("part", "")
    return {
        "ok": True,
        "found": bool(lines),
        "total": total,
        "no": str(total),
        "part": part,
        "part_cn": _PART_CN.get(part, part),
        "layer": layer,
        "lines": lines,
        "direction": direction,
        "steps": q["steps"],
        "page": (item or {}).get("page"),
        "note": "" if lines else f"数{total}（{part}）尚未转录入语料",
    }


def layer_lines_448(item: dict, layer: str) -> list:
    """取 448 条目某一层（或其中一句）的句。

    layer 可取**层名** {"男命", "女命", "岁运"}（各返回 2 句），
    亦可取 **CANPING_LAYERS 单句标签** {"男上"…"运下"}（各返回 1 句）。
    两种粒度统一由 CANPING_LAYER_SPANS 解释。
    层名非法或句数不足返回 []。
    """
    span = CANPING_LAYER_SPANS.get(layer)
    if span is None:
        return []
    start, count = span
    lines = item.get("lines") or []
    return lines[start:start + count] if len(lines) >= start + count else []


def search_raw_poem_448(
    keyword: str = "",
    part: str = "",
    no: str = "",
    layer: str = "",
    include_header_example: bool = True,
) -> list:
    """在金/土部诗断语料（448_008 编号制）中检索。

    keyword 匹配句文；part ∈ {jin, tu}；no 匹配编号（如 "2510"）。
    layer 非空时按 CANPING_LAYER_SPANS 取层或单句：层名 {"男命","女命","岁运"}
    取该层 2 句，单句标签 {"男上"…"运下"} 取该句 1 句；layer 为空默认检索全部 6 句。
    include_header_example=False 时跳过 448 p75 土部表头 worked example（is_header_example）。
    返回 [(part, page, no, note, line), ...]。

    2026-10-05 校正后金／土两部各 78 码、部内编号唯一；接口仍以 (part,page,no)
    定位，以容未来跨页异文重出。
    """
    out = []
    for it in load_raw_shici_jintu():
        if part and it.get("part") != part:
            continue
        if no and it.get("no") != no:
            continue
        if not include_header_example and it.get("is_header_example"):
            continue
        if layer:
            lines = layer_lines_448(it, layer)
        else:
            lines = it.get("lines", [])
        for ln in lines:
            if keyword and keyword not in ln:
                continue
            out.append((it.get("part"), it.get("page"), it.get("no"),
                        it.get("note", ""), ln))
    return out


def load_448_rulings() -> dict:
    """载入 448 编号对照与裁决层原始文件（448_duizhao.json）；文件缺失返回 {}。

    ⚠ 返回的是**整个文件**，其顶层两套 schema 互不相同，勿当作裁决列表直接用：

      ``meta``              : dict —— 来源与总则说明；
      ``items``             : list[35] —— **447/448 跨源字词对照**（K3 定谳），
                              键 {no, text448, p447, diff, ruling}，无 part 字段；
      ``jintu_nvp_rulings`` : dict —— **金/土部女命层逐字校订裁决**，
                              键 {date, scope, basis, method, ordering_ruling,
                              total, identical, diff_count, unmatched, items}，
                              其 items[].part 为 "金"/"土"。

    取用请走具名访问器，别手工 ``.get()`` 猜键：
    :func:`get_448_base_items`（跨源对照表）、
    :func:`get_448_nvp_ruling_block`（女命层裁决块，含统计元数据）、
    :func:`get_nvp_rulings_448`（女命层裁决条目列表）。
    """
    import json as _json
    p = os.path.join(_canping_dir(), "448_duizhao.json")
    try:
        with open(p, encoding="utf-8") as f:
            return _json.load(f)
    except (OSError, ValueError):
        return {}


def get_448_base_items() -> list:
    """447/448 跨源字词对照条目（448_duizhao.json 顶层 items，35 条）。

    每条 {no, text448, p447, diff, ruling}；无 part 字段（该表为跨部对照）。
    与 :func:`get_nvp_rulings_448` 是两套不同 schema，勿混用。
    """
    return load_448_rulings().get("items") or []


def get_448_nvp_ruling_block() -> dict:
    """金/土部女命层逐字校订裁决**块**（含 total/identical/diff_count/unmatched 等元数据）。

    块缺失返回 {}。只要条目列表请用 :func:`get_nvp_rulings_448`。
    """
    return load_448_rulings().get("jintu_nvp_rulings") or {}


def get_nvp_rulings_448(part: str = "", no: str = "") -> list:
    """金／土部女命（中层）校订裁决条目。

    part ∈ {"金", "土"}（中文部名，见 448_duizhao.json jintu_nvp_rulings）。
    返回 ruling 列表；语料或裁决层缺失返回 []。
    块级元数据（total/identical/diff_count/unmatched）用
    :func:`get_448_nvp_ruling_block` 取。
    """
    items = get_448_nvp_ruling_block().get("items", [])
    if part:
        items = [x for x in items if x.get("part") == part]
    if no:
        items = [x for x in items if x.get("no") == no]
    return items


__all__ = [
    "get_nayin_element", "qishu", "qishu_dayun", "qishu_liunian",
    "set_canping_dir", "search_raw_poem", "search_raw_poem_448",
    "load_raw_shici_jintu", "layer_lines_448",
    "CANPING_LAYERS", "CANPING_LAYER_SPANS",
    "load_448_rulings", "get_448_base_items",
    "get_448_nvp_ruling_block", "get_nvp_rulings_448",
    "NAYIN_ADD", "NAYIN_PEI", "NAYIN_PART",
]

# 模块级导出（供外部只读访问）
NAYIN_ADD = _NAYIN_ADD
NAYIN_PEI = _NAYIN_PEI
NAYIN_PART = _NAYIN_PART
