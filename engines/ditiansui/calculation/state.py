"""DTS 基础态势派生（Phase 6 §65 ·《滴天髓》基础字段）。

本轮输出（对应 DTS 规则 001-009，不依赖 strength 旺衰）：
- stem           : 日干（CAND-DTS-001/002 丙/癸 判定「陽之至/陰之至」）
- stem_yinyang   : 日干阴阳（003/004 從氣不從勢/從勢）
- branch_yinyang : 月支阴阳（005/006 動強速達/靜專否泰；口径：月支，月令为纲）
- relation       : "沖"（007/009 沖关系存在时；展开 L0 relations.liu_chong）
- pillar         : 日柱干支（018/019 甲申/戊寅/癸丑/庚寅 判定；= stem_branch_pair）
- tian_status    : 四天干同五行 → "全一氣"（012，DTS-010-004）
- di_status      : 四地支成三会/三合局 → "全三物"（013，DTS-010-006/007 注：寅卯辰、亥卯未）
- stem_position  : 日干阳+日支阳 → "陽乘陽位"；阴+阴 → "陰乘陰位"（014/015，DTS-010-008/010）
- xing_state     : 四柱干支五行覆盖（DTS-011-003/008：五行俱全→"形全"；有缺→"形缺"）
- pattern        : "兩氣合而成象"（DTS-011-001/002 注：天干属一行、地支属一行且两行相生，
  如天干屬木地支屬火；其象屬一，见金水则破——静态盘干支各一行即无第三行）
- zhan_state     : "天戰"/"地戰"（DTS-046-002 注：干頭遇甲乙庚辛→天戰；地支寅申卯酉→地戰；
  并存时天戰优先，口径记录）
- xiang_state    : 君亢/臣過/母旺子孤/子衆母衰（DTS-048-002/049-002/050-002/051-002 注：
  日主行满盘（四支全日主五行）时按财/官/食伤/印行出现数判定，取首命中）
- pattern        : "獨象"/"全象"（DTS-011-005/007 注：一者為獨，曲直炎上之類（日主行≥6/8 专旺）；
  三者為全，有傷官而又有財（8字恰含日主/食伤/财三行且日主行旺））
- cong_state     : "真"/"假"（DTS-040-002/042-002 注：日主孤弱無氣、絕無一毫生扶→真从；
  中有所助及暗生→假从；保守按 8 字生扶行（比劫+印）计数 0-1→真、2-3→假，财官行≥4）
- hua_state      : "真"/"假"（DTS-041-002/043-002 注：日干合干单透一位、不遇印比劫及同类干、
  有辰（龙）、化神得令（月支=合化五行）→真化；合成立但缺真化条件→假化）

注：CAND-DTS-007（生方忌沖動）为 suppress 规则，RuleEngine 只消费 emit，
suppress 语义 V2.22 未定义条款，已记录待审批裁决；本派生只注入其前置字段。
旺衰类字段（source_strength/target_strength/day_master_strength 等）依赖
strength_state 判定（《滴天髓》衰旺篇规则），后续篇章派生接入。
"""

from __future__ import annotations

from typing import Any, Dict

# 干五行
STEM_ELEMENT: Dict[str, str] = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
# 支五行
BRANCH_ELEMENT: Dict[str, str] = {
    "寅": "木", "卯": "木", "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水", "子": "水", "丑": "土",
}
# 三合局（任两支成局即视为局气，取完整组判定：组内三支齐全）
SANHE: Dict[str, set] = {
    "寅午戌": {"寅", "午", "戌"},
    "申子辰": {"申", "子", "辰"},
    "巳酉丑": {"巳", "酉", "丑"},
    "亥卯未": {"亥", "卯", "未"},
}
# 三会方（DTS-010-007 注「寅卯辰、亥卯未」）
SANHUI: Dict[str, set] = {
    "寅卯辰": {"寅", "卯", "辰"},
    "巳午未": {"巳", "午", "未"},
    "申酉戌": {"申", "酉", "戌"},
    "亥子丑": {"亥", "子", "丑"},
}
# 干阴阳（阳干：甲丙戊庚壬）
STEM_YINYANG: Dict[str, str] = {
    "甲": "陽", "丙": "陽", "戊": "陽", "庚": "陽", "壬": "陽",
    "乙": "陰", "丁": "陰", "己": "陰", "辛": "陰", "癸": "陰",
}
# 支阴阳（阳支：子寅辰午申戌）
BRANCH_YINYANG: Dict[str, str] = {
    "子": "陽", "寅": "陽", "辰": "陽", "午": "陽", "申": "陽", "戌": "陽",
    "丑": "陰", "卯": "陰", "巳": "陰", "未": "陰", "酉": "陰", "亥": "陰",
}


def _has_bureau(branches: list) -> bool:
    """四地支是否成三会/三合局（组内三支齐全）。"""
    bset = set(branches)
    for grp in list(SANHE.values()) + list(SANHUI.values()):
        if grp <= bset:
            return True
    return False


# 五行相生（木→火→土→金→水→木）
_SHENG: Dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 五行相克（木克土、土克水、水克火、火克金、金克木）
_KE: Dict[str, str] = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
# 天干六合（日干→合干）
_HE: Dict[str, str] = {"甲": "己", "己": "甲", "乙": "庚", "庚": "乙", "丙": "辛",
                       "辛": "丙", "丁": "壬", "壬": "丁", "戊": "癸", "癸": "戊"}
# 合化五行（DTS-041-002 注原文推演：丙辛冬月（水）、戊癸夏月（火）、乙庚秋月（金）、
# 丁壬春月（木）、甲己生於四季（土）→ 甲己化土/乙庚化金/丙辛化水/丁壬化木/戊癸化火）
_HUA: Dict[str, str] = {"甲": "土", "己": "土", "乙": "金", "庚": "金", "丙": "水",
                        "辛": "水", "丁": "木", "壬": "木", "戊": "火", "癸": "火"}


def _generates(a: str, b: str) -> bool:
    """a 生 b。"""
    return _SHENG.get(a) == b


def _ke(a: str, b: str) -> bool:
    """a 克 b。"""
    return _KE.get(a) == b


def derive_state(day_stem: str | None = None,
                 month_branch: str | None = None,
                 hidden: Any = None,
                 transparent_stems: Any = None,
                 branches: Any = None,
                 base: Dict[str, Any] | None = None,
                 l0_chart: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """DTS 基础态势派生（§65）：注入 stem/阴阳/冲关系。"""
    out: Dict[str, Any] = {}
    if day_stem:
        out["stem"] = day_stem
        out["stem_yinyang"] = STEM_YINYANG.get(day_stem)
    if month_branch:
        out["branch_yinyang"] = BRANCH_YINYANG.get(month_branch)
    relations = (base or {}).get("relations") or {}
    if relations.get("liu_chong"):
        out["relation"] = "沖"
    if base and base.get("stem_branch_pair"):
        out["pillar"] = base["stem_branch_pair"]
    # 全一氣：四天干同五行（DTS-010-004）——三态化 2026-09-16：补反态「非全一氣」
    if base:
        stems = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        if all(stems):
            out["tian_status"] = "全一氣" if len({STEM_ELEMENT.get(s) for s in stems}) == 1 else "非全一氣"
        else:
            out["tian_status"] = "UNDETERMINED"
    # 全三物：四地支成三会/三合局（DTS-010-006/007）——三态化：补反态「非全三物」
    if branches:
        out["di_status"] = "全三物" if _has_bureau(list(branches)) else "非全三物"
    else:
        out["di_status"] = "UNDETERMINED"
    # 陽乘陽位 / 陰乘陰位（DTS-010-008/010；口径：日干坐日支）——三态化：补 UNDETERMINED
    if day_stem and (base or {}).get("day_branch"):
        ds_yy = STEM_YINYANG.get(day_stem)
        db_yy = BRANCH_YINYANG.get((base or {}).get("day_branch"))
        if ds_yy == "陽" and db_yy == "陽":
            out["stem_position"] = "陽乘陽位"
        elif ds_yy == "陰" and db_yy == "陰":
            out["stem_position"] = "陰乘陰位"
        else:
            out["stem_position"] = "UNDETERMINED"
    # 形全/形缺：四柱干支五行覆盖（DTS-011-003/008「形全者宜損其有餘，形缺者宜補其不足」）
    # 三态化 2026-09-16：xing_state 只承载「形全/形缺」语义；寿段「性定」拆至 xing_ding_state
    if base:
        els = {STEM_ELEMENT.get(s) for s in (base.get("year_stem"), base.get("month_stem"),
                                             day_stem, base.get("hour_stem"))}
        els |= {BRANCH_ELEMENT.get(b) for b in (base.get("year_branch"), base.get("month_branch"),
                                                base.get("day_branch"), base.get("hour_branch"))}
        els.discard(None)
        out["xing_state"] = "形全" if len(els) >= 5 else "形缺"
    # 性定（何知章寿段「柱中無沖無合，無缺無貪，則定性矣」）——新建 xing_ding_state（三态化拆分）
    if base:
        _has_chong = bool((base.get("relations") or {}).get("liu_chong"))
        _stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        _brs4 = [base.get("year_branch"), base.get("month_branch"),
                 base.get("day_branch"), base.get("hour_branch")]
        if all(_stems4) and all(_brs4):
            _no_chong_he = not _has_chong
            out["xing_ding_state"] = "定" if _no_chong_he else "不定"
        else:
            out["xing_ding_state"] = "UNDETERMINED"
    # 兩氣合而成象（DTS-011-001/002）：四干全一行、四支全一行、两行相生
    if base and day_stem:
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        if all(stems4) and all(brs4):
            stem_els = {STEM_ELEMENT.get(s) for s in stems4}
            br_els = {BRANCH_ELEMENT.get(b) for b in brs4}
            if len(stem_els) == 1 and len(br_els) == 1:
                se, be = next(iter(stem_els)), next(iter(br_els))
                if se != be and _generates(se, be):
                    out["pattern"] = "兩氣合而成象"
    # 天戰/地戰（DTS-046-002 注：干頭遇甲乙庚辛→天戰；地支寅申卯酉→地戰）——三态化：补反态「無戰」
    if base and day_stem:
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        if any(s in ("甲", "乙") for s in stems4) and any(s in ("庚", "辛") for s in stems4):
            out["zhan_state"] = "天戰"
        elif "寅" in brs4 and "申" in brs4 or ("卯" in brs4 and "酉" in brs4):
            out["zhan_state"] = "地戰"
        else:
            out["zhan_state"] = "無戰"
    # 君亢/臣過/母旺子孤/子衆母衰（DTS-048-002/049-002/050-002/051-002 注：
    # 「滿盤是木」=日主行过半（8字中≥5）；「內有一二X氣」=该行 1≤count≤2，
    # 按篇序（君象→臣象→母象→子象）取首；印多（≥3）独立判定为子衆母衰）
    if base and day_stem:
        day_el = STEM_ELEMENT.get(day_stem)
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        if day_el and all(stems4) and all(brs4):
            els8 = [STEM_ELEMENT.get(s) for s in stems4] + [BRANCH_ELEMENT.get(b) for b in brs4]
            from collections import Counter
            cnt = Counter(e for e in els8 if e)
            if cnt.get(day_el, 0) >= 5:  # 日主行满盘（过半）
                sheng_wo = _SHENG.get(day_el)      # 日主所生：食伤
                ke = _KE.get(day_el)               # 日主所克：财
                ke_wo = next((k for k, v in _KE.items() if v == day_el), None)  # 克日主：官
                sheng = next((k for k, v in _SHENG.items() if v == day_el), None)  # 生日主：印
                picks = []
                if ke and 1 <= cnt.get(ke, 0) <= 2:
                    picks.append("君亢")        # 君盛臣衰（财一二）
                if ke_wo and 1 <= cnt.get(ke_wo, 0) <= 2:
                    picks.append("臣過")        # 臣盛君衰（官一二）
                if sheng_wo and 1 <= cnt.get(sheng_wo, 0) <= 2:
                    picks.append("母旺子孤")    # 母旺子孤（食伤一二）
                if picks:
                    out["xiang_state"] = picks[0]
                elif sheng and cnt.get(sheng, 0) >= 3:
                    out["xiang_state"] = "子衆母衰"  # 子衆母衰（印多）
                else:
                    out["xiang_state"] = "UNDETERMINED"
    # 獨象/全象（DTS-011-005/007 注：一者為獨，曲直炎上之類是也；三者為全，有傷官而又有財是也）
    # PENDING_VERIFY 口径（无原文量化，待多源验证/Human 裁决）：
    #   獨象＝8字中日主行 ≥6（"一者為獨"未给量化；传统专旺另需当令/会局/无克，未纳入）
    #   全象＝8字恰含日主/食伤/财三行且日主行 ≥3（"主旺喜財旺"依赖旺衰，暂以计数近似）
    if base and day_stem:
        day_el = STEM_ELEMENT.get(day_stem)
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        if day_el and all(stems4) and all(brs4):
            els8 = [STEM_ELEMENT.get(s) for s in stems4] + [BRANCH_ELEMENT.get(b) for b in brs4]
            from collections import Counter
            cnt = Counter(e for e in els8 if e)
            if cnt.get(day_el, 0) >= 6:
                out["pattern"] = "獨象"        # 一行专旺（曲直炎上之類）[PENDING_VERIFY]
            else:
                sheng_wo = _SHENG.get(day_el)      # 食伤行
                ke = _KE.get(day_el)               # 财行
                others = {e for e in cnt if e not in (day_el, sheng_wo, ke)}
                if (sheng_wo and cnt.get(sheng_wo, 0) >= 1 and ke
                        and cnt.get(ke, 0) >= 1 and cnt.get(day_el, 0) >= 3 and not others):
                    out["pattern"] = "全象"        # 三者為全：主/食伤/财三行 [PENDING_VERIFY]
    # 真从/假从（DTS-040-002/042-002 注：日主孤弱無氣，天地人元絕無一毫生扶之力，才官強甚→真从；
    # 中有所助及暗生者，從之不真→假从）
    # Human 裁决 2026-09-15：不量化——「才官強甚/中有所助」为结构事实+性质枚举，
    # 架构 = 结构事实 → 状态判定 → 从格规则（CAND-DTS-047/049 消费两枚举）：
    #   cai_guan_state : NOT_STRONG / STRONG（「才官強甚」）
    #   cong_support_state : NONE / HAS_SUPPORT（「絕無一毫生扶」vs「中有所助及暗生」；F-3 改名解耦）
    # PENDING_VERIFY：STRONG 初版按结构事实近似（财官得令∧（透干∨通根））；
    #   组合/制化维度待 strength 前置引擎接入后接管；「暗生」并入 HAS_SUPPORT（藏干生扶）
    if base and day_stem:
        day_el = STEM_ELEMENT.get(day_stem)
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        if day_el and all(stems4) and all(brs4):
            ke = _KE.get(day_el)                                                 # 财行（日主所克）
            ke_wo = next((k for k, v in _KE.items() if v == day_el), None)       # 官杀行（克日主）
            cai_guan = {e for e in (ke, ke_wo) if e}
            # 结构事实（财官强甚）：
            de_ling = BRANCH_ELEMENT.get(base.get("month_branch")) in cai_guan   # 得令
            tou_gan = any(STEM_ELEMENT.get(s) in cai_guan for s in stems4)       # 透干
            tong_gen = False                                                     # 通根（藏干含财官）
            if isinstance(hidden, dict):
                for _v in hidden.values():
                    if isinstance(_v, (list, tuple)) and any(
                            STEM_ELEMENT.get(_s) in cai_guan for _s in _v):
                        tong_gen = True
            out["cai_guan_state"] = "STRONG" if (de_ling and (tou_gan or tong_gen)) else "NOT_STRONG"
            # 结构事实（生扶有无）：干支（除日干）比劫/印行 + 藏干生扶（含「暗生」）
            sheng = next((k for k, v in _SHENG.items() if v == day_el), None)    # 印行
            has = False
            for i, s in enumerate(stems4):
                if i == 2:      # 跳过日柱位置（日干自身非生扶）
                    continue
                if STEM_ELEMENT.get(s) in (day_el, sheng):
                    has = True
            if not has:
                for b in brs4:
                    if BRANCH_ELEMENT.get(b) in (day_el, sheng):
                        has = True
                        break
            if not has and isinstance(hidden, dict):
                for _v in hidden.values():
                    if isinstance(_v, (list, tuple)) and any(
                            STEM_ELEMENT.get(_s) in (day_el, sheng) for _s in _v):
                        has = True
                        break
            out["cong_support_state"] = "HAS_SUPPORT" if has else "NONE"
    # 身旺/身衰/均衡（strength 最小可用版）
    # Human 裁决 2026-09-16：清浊（CAND-DTS-029/086/087）判定依赖 strength——「清」=用神有力、
    # 「浊」=忌神当权；用神取法以旺衰为锚（身旺喜克泄耗、身弱喜生扶），未定旺衰则清浊无锚点，
    # 整组待命为逻辑必然。最小版输出（PENDING_VERIFY，结构事实近似，不量化）：
    #   day_strength_state  : 附录 L-3 标准六级（STRONG/SLIGHTLY_STRONG/NEUTRAL/
    #                          SLIGHTLY_WEAK/WEAK/UNDETERMINED）——F-2 Human 裁决 2026-09-16
    #                          当前精度三档：WANG→STRONG、SHUAI→WEAK、JUN_HENG→NEUTRAL；
    #                          SLIGHTLY_STRONG/SLIGHTLY_WEAK 精度未达不输出（登记 PENDING_VERIFY，
    #                          待 strength 精度迭代）；数据缺失→UNDETERMINED
    #   day_strength_classic : 古典文本语义层 WANG/SHUAI/JUN_HENG（旺/衰/均衡）——仅作解释层，
    #                          与附录 L 标准枚举隔离，不得混用（F-2 裁决：古典语义不得进入正式字段）
    #   yong_shen_el        : 喜用五行（WANG→财/官杀/食伤行；SHUAI→印/比劫行；JUN_HENG→空=中和无定喜）
    #   yong_shen_ten_god   : 喜用十神方向（同上对应）
    # 结构事实：得令＝月支∈{日主,印}行；得地＝四支藏干本气∈{日主,印}行；
    #   得势＝其余三干有帮扶（布尔，不计数）；WANG＝得令∧(得地∨得势)；SHUAI＝¬得令∧¬得地∧¬得势
    # PENDING_VERIFY：藏干权重（本气/中气/余气）、组合/制化维度未纳入——待 strength 精度迭代；
    #   JUN_HENG 喜用为空（中和无定喜，调候/通关维度后续）
    out["day_strength_state"] = "UNDETERMINED"
    if base and day_stem:
        day_el = STEM_ELEMENT.get(day_stem)
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        if day_el and all(stems4) and all(brs4):
            sheng = next((k for k, v in _SHENG.items() if v == day_el), None)    # 印行（生我）
            bang = {day_el, sheng} if sheng else {day_el}                        # 生扶行（比劫+印）
            de_ling = BRANCH_ELEMENT.get(base.get("month_branch")) in bang       # 得令
            de_di = False                                                        # 得地（藏干本气）
            if isinstance(hidden, dict):
                for _v in hidden.values():
                    if isinstance(_v, (list, tuple)) and _v and STEM_ELEMENT.get(_v[0]) in bang:
                        de_di = True
                        break
            de_shi = any(STEM_ELEMENT.get(s) in bang for i, s in enumerate(stems4) if i != 2)  # 得势（布尔，跳过日柱位置）
            if de_ling and (de_di or de_shi):
                classic = "WANG"
            elif not de_ling and not de_di and not de_shi:
                classic = "SHUAI"
            else:
                classic = "JUN_HENG"
            out["day_strength_classic"] = classic                                  # 古典语义层（解释用）
            out["day_strength_state"] = {"WANG": "STRONG", "SHUAI": "WEAK",
                                         "JUN_HENG": "NEUTRAL"}[classic]           # 附录 L-3 标准值
            if classic == "WANG":
                sheng_wo = _SHENG.get(day_el)                                    # 食伤（我生）
                ke = _KE.get(day_el)                                             # 财（我克）
                ke_wo = next((k for k, v in _KE.items() if v == day_el), None)   # 官杀（克我）
                els = {e for e in (ke, ke_wo, sheng_wo) if e}
                out["yong_shen_el"] = sorted(els)
                out["yong_shen_ten_god"] = ["财", "官杀", "食伤"]
            elif classic == "SHUAI":
                els = {e for e in (day_el, sheng) if e}
                out["yong_shen_el"] = sorted(els)
                out["yong_shen_ten_god"] = ["印", "比劫"]
            else:
                out["yong_shen_el"] = []
                out["yong_shen_ten_god"] = []
    # 清浊/出身（P9 2026-09-16；CAND-DTS-029/086/087 消费 qing_state/qingqi_state/guan）
    # Human 裁决 2026-09-16：清浊整组依赖 strength 喜用方向——strength 最小版已输出
    #   yong_shen_el/yong_shen_ten_god，挂载门槛达成；清/浊结构事实口径为下一增量，
    #   本实现为保守结构近似（PENDING_VERIFY），收进 pending 命名空间，规则不消费。
    # 结构事实口径（无量化，待 Human 裁决）：
    #   喜用 U = yong_shen_el；忌神 J = 与喜用相反方向行（内部推导，不输出字段，规避全局喜忌禁令）
    #     身旺（WANG）：U=财/官杀/食伤 → J=印/比劫（生扶行）
    #     身弱（SHUAI）：U=印/比劫     → J=财/官杀/食伤（克泄耗行）
    #     均衡（JUN_HENG）：U 空 → 清浊无锚点 → UNDETERMINED
    #   一清到底有精神（DTS-022-001/002 注）：用神透干 ∧ 用神得地（藏干本气）∧ 忌神干支 0 现
    #   清得盡（DTS-054-003）：清 ∧ 忌神藏干亦 0 现（全局无一点忌）
    #   清枯（DTS-022-003）：用神透干但不得地不得令（清而枯弱）
    #   滿盤濁氣（DTS-022-003）：忌神透干 ∧（忌神得令 ∨ 忌神得地）∧ 用神不透干
    #   半濁半清（DTS-022-003）：用神透干 ∧ 忌神透干（混杂）
    # qingqi_state（DTS-054-005）：用神透干 ∧ 得地 → 有清氣；否则 無清氣
    # guan（DTS-054-005）：官星（克日主行）天干透 → 露；不透 → 不露
    if base and day_stem:
        day_el = STEM_ELEMENT.get(day_stem)
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        u = out.get("yong_shen_el")
        if day_el and u is not None and all(stems4) and all(brs4):
            # 内部忌神行推导（不输出）：身旺忌生扶行（印/比劫），身弱忌克泄耗行（财/官杀/食伤）
            classic = out.get("day_strength_classic")
            j_set = None
            if classic == "WANG":
                sheng = next((k for k, v in _SHENG.items() if v == day_el), None)
                j_set = {day_el, sheng} if sheng else {day_el}
            elif classic == "SHUAI":
                sheng_wo = _SHENG.get(day_el)
                ke = _KE.get(day_el)
                ke_wo = next((k for k, v in _KE.items() if v == day_el), None)
                j_set = {e for e in (sheng_wo, ke, ke_wo) if e}
            if j_set is None or not u:
                # 均衡无定喜 → 清浊无锚点；缺失数据 → UNDETERMINED
                out["qing_state"] = "UNDETERMINED"
                out["qingqi_state"] = "無清氣"
            else:
                u_set = set(u)
                stem_els_other = {STEM_ELEMENT.get(s) for s in stems4[0:2] + stems4[3:4]}  # 除日干外三干
                br_els = {BRANCH_ELEMENT.get(b) for b in brs4}
                # 藏干（含本气/中气/余气；本气=首位）
                hidden_els = set()
                hidden_root = set()
                if isinstance(hidden, dict):
                    for _v in hidden.values():
                        if isinstance(_v, (list, tuple)) and _v:
                            hidden_root.add(STEM_ELEMENT.get(_v[0]))
                            hidden_els |= {STEM_ELEMENT.get(_s) for _s in _v}
                hidden_els.discard(None)
                hidden_root.discard(None)
                mb_el = BRANCH_ELEMENT.get(base.get("month_branch"))
                # 用神/忌神：透干=他柱天干（日干为日主本体，不算「透出/混杂」）。
                # 口径修正 2026-09-16（DTS-022-002 注「縱有比肩食神印綬才煞雜之，皆循序得所，
                # 有安頓，或作閑神不來破局，乃為清奇」）：显混=忌神透干相战；
                # 支藏忌神为「有根闲神不破局」，不判浊。
                u_tou = bool(u_set & stem_els_other)
                j_tou = bool(j_set & stem_els_other)
                u_de_ling = mb_el in u_set
                j_de_ling = mb_el in j_set
                u_de_di = bool(u_set & hidden_root)
                j_de_di = bool(j_set & hidden_root)
                j_br = bool(j_set & (br_els - {mb_el}))  # 忌神显于四支（除月支；月令为格局根本不判浊）
                j_hidden = bool(j_set & hidden_els)    # 忌神藏于支（闲神/暗藏）
                # Human 裁决 2026-09-16：清浊结构事实定义 APPROVED + 判定顺序互斥边界
                #   判定顺序：先判喜神透干有无 → 再分四态（半浊半清/清/满盘浊/清枯）
                #   边界1：清枯触发必须包含「喜神透干=0」——喜透>0∧忌透>0 只能归半浊半清，不得判清枯
                #   边界2：半浊半清必须「喜透>0∧忌透>0」——喜透=0 即使忌神不满盘也归清枯，不得判半浊半清
                if u_tou and j_tou:
                    out["qing_state"] = "半濁半清"        # 边界2：喜透>0∧忌透>0（透干相战）
                elif u_tou and u_de_di and not j_tou:
                    # 清：用神有力∧忌神不透干（DTS-022-002「並無傷官七煞混之」——混=透干；
                    # 支根比劫为「闲神不破局」不判浊；「縱有比肩食神印綬才煞雜之…循序得所…清奇」）
                    # 清得盡（DTS-054-003）：藏干亦无一点忌；否则一清到底有精神（DTS-022-001/002）
                    out["qing_state"] = "清得盡" if not j_hidden else "一清到底有精神"
                elif j_tou and (j_de_ling or j_de_di) and not u_tou:
                    out["qing_state"] = "滿盤濁氣"        # 忌神当权（得令/得地）、喜神不透
                elif not u_tou:
                    out["qing_state"] = "清枯"            # 边界1：喜神透干=0（喜用无透、非满盘浊）→ 清枯
                else:
                    out["qing_state"] = "UNDETERMINED"    # 喜透>0 但无力（不得地不得令）且忌不透
                out["qingqi_state"] = "有清氣" if (u_tou and u_de_di) else "無清氣"
            # guan 显隐（DTS-054-005 官不露）：官星=克日主行
            ke_wo = next((k for k, v in _KE.items() if v == day_el), None)
            if ke_wo:
                out["guan"] = "露" if ke_wo in stem_els else "不露"
    # 真假神/隐显众寡/才德（DTS-023/027/036；PENDING_VERIFY 结构近似，收进 pending）
    # 均依赖 strength 喜用方向（yong_shen_el）——最小版已输出，挂载达成；
    # 口径待 Human 裁决，P-1 隔离（不输出顶层、规则不消费）
    # 真假神（DTS-023-001/002「令上尋真聚得真…真神得用平生貴，用假終為碌碌人」；
    #   注「木火透者生寅月，聚得真，不要金水亂之。真神得用，不為忌神所害則貴」）：
    #   真神=月令行（令上尋真）；得用=月支行∈喜用∧忌神不透干（不被害）
    #   用假=喜用透干但喜用行≠月支行（DTS-023-002「金水又不得令…徒與木火不和」）
    # 隐显（DTS-027-001「吉神太露，起爭奪之風；凶物深藏，成養虎之患」+ 027-002 注）：
    #   吉神=喜神：太露=透干、深藏=不透（「暗用吉神為妙」）
    #   凶物=忌神：深藏=不透干但现于支/藏干（「忌神伏藏於地支」）、顯現=透干
    # 众寡（DTS-027-003「強衆而敵寡者，勢在去其寡；強寡而敵衆者，勢在成乎衆」）：
    #   我=日主行、敌=忌神行；相对计数（非绝对阈值）；STRONG 前提下输出
    # 才德（DTS-036-001「德勝才者，局全君子之風；才勝德者，用顯多能之象」+ 002 注）：
    #   德勝才=清∧无冲（清利平顺、主辅得宜）；才勝德=浊∨冲（混浊破害）
    #   「陽在內陰在外」概念未实现（结构近似，待裁决）
    if base and day_stem:
        day_el = STEM_ELEMENT.get(day_stem)
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        u = out.get("yong_shen_el")
        classic = out.get("day_strength_classic")
        if day_el and u is not None and u and classic != "JUN_HENG" and all(stems4) and all(brs4):
            u_set = set(u)
            stem_els_other = {STEM_ELEMENT.get(s) for s in stems4[0:2] + stems4[3:4]}
            br_els = {BRANCH_ELEMENT.get(b) for b in brs4}
            mb_el = BRANCH_ELEMENT.get(base.get("month_branch"))
            hidden_els = set()
            if isinstance(hidden, dict):
                for _v in hidden.values():
                    if isinstance(_v, (list, tuple)):
                        hidden_els |= {STEM_ELEMENT.get(_s) for _s in _v}
                hidden_els.discard(None)
            j_set = None
            if classic == "WANG":
                sheng = next((k for k, v in _SHENG.items() if v == day_el), None)
                j_set = {day_el, sheng} if sheng else {day_el}
            elif classic == "SHUAI":
                sheng_wo = _SHENG.get(day_el)
                ke = _KE.get(day_el)
                ke_wo = next((k for k, v in _KE.items() if v == day_el), None)
                j_set = {e for e in (sheng_wo, ke, ke_wo) if e}
            u_tou = bool(u_set & stem_els_other)
            j_tou = bool(j_set & stem_els_other) if j_set else False
            # 真假神
            out["zhen_shen_state"] = "得用" if (mb_el in u_set and not j_tou) else "不得用"
            out["jia_shen_state"] = "用假" if (u_tou and mb_el not in u_set) else "不用假"
            # 隐显（三态化：补 UNDETERMINED）
            out["jishen_state"] = "太露" if u_tou else "深藏"
            if j_set:
                if j_tou:
                    out["xiongwu_state"] = "顯現"
                elif bool(j_set & (br_els | hidden_els)):
                    out["xiongwu_state"] = "深藏"
                else:
                    out["xiongwu_state"] = "UNDETERMINED"
            else:
                out["xiongwu_state"] = "UNDETERMINED"
            # 众寡（相对计数）——三态化：补 UNDETERMINED
            from collections import Counter
            els8 = [STEM_ELEMENT.get(s) for s in stems4] + [BRANCH_ELEMENT.get(b) for b in brs4]
            cnt = Counter(e for e in els8 if e)
            my_cnt = cnt.get(day_el, 0)
            enemy_cnt = sum(cnt.get(e, 0) for e in j_set) if j_set else 0
            if classic == "WANG":
                out["wo_shi"] = "強衆" if my_cnt >= enemy_cnt else "強寡"
                out["di"] = "敵寡" if enemy_cnt < my_cnt else "敵衆"
            else:
                out["wo_shi"] = "UNDETERMINED"
                out["di"] = "UNDETERMINED"
            # 才德（依赖 qing_state，清浊块已写入 out）——三态化：补 UNDETERMINED
            qs = out.get("qing_state")
            has_chong = bool(((base or {}).get("relations") or {}).get("liu_chong"))
            if qs in ("一清到底有精神", "清得盡") and not has_chong:
                out["decai_relation"] = "德勝才"
            elif qs in ("滿盤濁氣", "半濁半清") or has_chong:
                out["decai_relation"] = "才勝德"
            else:
                out["decai_relation"] = "UNDETERMINED"
    # 情性/出身/地位（DTS-052/054/055；PENDING_VERIFY 结构近似，收进 pending）
    # wuxing_state（DTS-052-001「五行不戾，惟正清和；濁亂偏枯，性情乖逆」+ 052-002 注）：
    #   不戾正清和=无冲∧五行覆盖≥4∧清（五氣不乖張）；濁亂偏枯=冲∨偏枯（缺行）
    # rigan_state（DTS-054-007「日干得氣遇才星」+ 008 注「才星得個門戶，通得官星」）：
    #   日干得气=得令∨得地∨得势（有根气）；caixing 才星遇=财行（我克）透干∨通根
    # rensha_state（DTS-055-003「刃煞神清氣勢恢」+ 004 注「清中精神必異，又或刃煞兩顯也」）：
    #   刃=日主行帝旺支现（甲卯/乙寅/丙午/丁巳/戊午/己巳/庚酉/辛申/壬子/癸亥）；
    #   煞=克日主行透干；兩顯∧清→神清氣勢恢
    # caiguan/geju（DTS-055-005「分藩司牧財官和，格局清純神氣多」+ 006 注「才官為重…格正局全」）：
    #   财官和=财行∧官杀行俱现（透干∨通根）；格局清纯=清（qing_state）
    if base and day_stem:
        day_el = STEM_ELEMENT.get(day_stem)
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        if day_el and all(stems4) and all(brs4):
            stem_els4 = {STEM_ELEMENT.get(s) for s in stems4}
            br_els4 = {BRANCH_ELEMENT.get(b) for b in brs4}
            els8 = (stem_els4 | br_els4) - {None}
            mb_el = BRANCH_ELEMENT.get(base.get("month_branch"))
            hidden_els = set()
            if isinstance(hidden, dict):
                for _v in hidden.values():
                    if isinstance(_v, (list, tuple)):
                        hidden_els |= {STEM_ELEMENT.get(_s) for _s in _v}
                hidden_els.discard(None)
            sheng = next((k for k, v in _SHENG.items() if v == day_el), None)    # 印行（生我）
            bang = {day_el, sheng} if sheng else {day_el}
            de_ling = mb_el in bang
            de_di = False
            if isinstance(hidden, dict):
                for _v in hidden.values():
                    if isinstance(_v, (list, tuple)) and _v and STEM_ELEMENT.get(_v[0]) in bang:
                        de_di = True
                        break
            de_shi = any(STEM_ELEMENT.get(s) in bang for s in stems4[0:2] + stems4[3:4])
            has_chong = bool(((base or {}).get("relations") or {}).get("liu_chong"))
            qs = out.get("qing_state")
            # 情性：五行不戾
            coverage = len(els8)
            if (not has_chong) and coverage >= 4 and qs in ("一清到底有精神", "清得盡"):
                out["wuxing_state"] = "不戾正清和"
            else:
                out["wuxing_state"] = "濁亂偏枯"
            # 出身：日干得气 / 才星遇
            out["rigan_state"] = "得氣" if (de_ling or de_di or de_shi) else "無氣"
            ke = _KE.get(day_el)                                       # 财行（我克）
            cai_tou = bool(ke and (ke in stem_els4))
            cai_gen = bool(ke and (ke in hidden_els))
            out["caixing"] = "遇" if (cai_tou or cai_gen) else "不遇"
            # 地位：刃煞神清气势恢
            DI_WANG = {"甲": "卯", "乙": "寅", "丙": "午", "丁": "巳",
                       "戊": "午", "己": "巳", "庚": "酉", "辛": "申",
                       "壬": "子", "癸": "亥"}
            ke_wo = next((k for k, v in _KE.items() if v == day_el), None)   # 官杀行（克我）
            ren = DI_WANG.get(day_stem) in brs4                            # 阳刃（帝旺支现）
            sha = bool(ke_wo and (ke_wo in stem_els4))                     # 七杀透干
            if ren and sha and qs in ("一清到底有精神", "清得盡"):
                out["rensha_state"] = "神清氣勢恢"
            else:
                out["rensha_state"] = "不恢"
            # 地位：财官和 / 格局清纯
            cai_guan = {e for e in (ke, ke_wo) if e}
            cg_tou = bool(cai_guan & stem_els4)
            cg_gen = bool(cai_guan & hidden_els)
            out["caiguan"] = "和" if (cg_tou or cg_gen) else "不和"
            out["geju"] = "清純" if qs in ("一清到底有精神", "清得盡") else "混濁"
    # 情性二/疾病（DTS-052-022/053；PENDING_VERIFY 结构近似，收进 pending）
    # 阳刃/伤官格/用神多/支格（052-022「陽刃局戰則逞威，弱則怕事；傷官格清則諧和，
    #   濁則剛猛；用神多者情性不常，支格濁者虎頭鼠尾」）：
    #   战=刃支逢冲；弱=刃现∧身弱（WEAK）
    #   伤官格=伤官行（我生）透干∨月支为伤官行；清/浊复用 qing_state
    #   用神多=喜用行透干≥2；支格浊=地支显忌神
    # 疾病（053-003「血氣亂者」/005「忌神入五臟而病凶」/007「客神遊六經者災小」）：
    #   血气乱=冲∨天战地战（五行反逆）；忌神入五脏=忌神行∧其克行现；
    #   客神=闲神（非喜非忌），遊六经=客神现
    # ⚠ CAND-DTS-074 消费 wuxing_state=和 与 057/058（不戾正清和/濁亂偏枯）字段值域冲突，
    #   同字段两值域——登记待 Human 裁决，074 不实现
    if base and day_stem:
        day_el = STEM_ELEMENT.get(day_stem)
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        u = out.get("yong_shen_el")
        classic = out.get("day_strength_classic")
        if day_el and u is not None and u and classic != "JUN_HENG" and all(stems4) and all(brs4):
            u_set = set(u)
            stem_els4 = {STEM_ELEMENT.get(s) for s in stems4}
            br_els4 = {BRANCH_ELEMENT.get(b) for b in brs4}
            mb_el = BRANCH_ELEMENT.get(base.get("month_branch"))
            hidden_els = set()
            if isinstance(hidden, dict):
                for _v in hidden.values():
                    if isinstance(_v, (list, tuple)):
                        hidden_els |= {STEM_ELEMENT.get(_s) for _s in _v}
                hidden_els.discard(None)
            sheng = next((k for k, v in _SHENG.items() if v == day_el), None)    # 印行
            sheng_wo = _SHENG.get(day_el)                                        # 我生=伤官行
            ke = _KE.get(day_el)                                                 # 我克=财行
            ke_wo = next((k for k, v in _KE.items() if v == day_el), None)       # 克我=官杀行
            j_set = None
            if classic == "WANG":
                j_set = {day_el, sheng} if sheng else {day_el}
            elif classic == "SHUAI":
                j_set = {e for e in (sheng_wo, ke, ke_wo) if e}
            has_chong = bool(((base or {}).get("relations") or {}).get("liu_chong"))
            qs = out.get("qing_state")
            zhan = out.get("zhan_state")
            # 阳刃局
            DI_WANG = {"甲": "卯", "乙": "寅", "丙": "午", "丁": "巳",
                       "戊": "午", "己": "巳", "庚": "酉", "辛": "申",
                       "壬": "子", "癸": "亥"}
            ren_br = DI_WANG.get(day_stem)
            if ren_br in brs4:
                ren_chong = bool((base or {}).get("relations") or {}) and \
                    ren_br in ((base or {}).get("relations") or {}).get("liu_chong", [])
                if ren_chong:
                    out["yangren_state"] = "戰"
                elif out.get("day_strength_state") == "WEAK":
                    out["yangren_state"] = "弱"
            # 伤官格（2026-09-16：shangguan_ge_state 已删，规则改消费 qing_state；
            # 此处仅保留 sg_ge 判定供审计，不再输出独立字段）
            # 用神多
            u_cnt = sum(1 for s in stems4 if STEM_ELEMENT.get(s) in u_set)
            out["yongshen_state"] = "多" if u_cnt >= 2 else "不多"
            # 支格浊（地支显忌神）
            if j_set:
                j_br_di = bool(j_set & (br_els4 - {mb_el}))
                out["zhige_state"] = "濁" if j_br_di else "清"
            # 血气乱（冲∨天战地战）
            out["xueqi_state"] = "亂" if (has_chong or zhan in ("天戰", "地戰")) else "和"
            # 忌神入五脏（忌神行克入行现）
            if j_set:
                j_ke_in = set()
                for j in j_set:
                    jk = _KE.get(j)                 # 忌神所克=五脏行
                    if jk and (jk in (stem_els4 | br_els4 | hidden_els)):
                        j_ke_in.add(jk)
                out["jishen_location"] = "入五臟" if j_ke_in else "不入"
            # 客神遊六经（闲神=非喜非忌行现）
            ke_shen = {e for e in (stem_els4 | br_els4 | hidden_els)
                       if e not in u_set and (not j_set or e not in j_set)}
            out["keshen_location"] = "遊六經" if ke_shen else "不遊"
    # 柱内关系/疾病五行受制（DTS-010-012/014、DTS-053-009/012；PENDING_VERIFY 结构近似）
    # pillar_relation（010-012「地生天者天衰怕衝」/014「天合地者地旺宜靜」，日柱）：
    #   地生天=日支行生日干行；天合地=日干与日支藏干五合（甲己/乙庚/丙辛/丁壬/戊癸）
    # day_master_strength（天衰=日主 WEAK）；branch_strength（地旺=日支行==月支行当令）
    # wood/earth_state（053-009「木不受水者血病，土不受火者氣傷」）：
    #   木行现∧水行不现→木不受水；土行现∧火行不现→土不受火
    # jinshui/shuitu_state（053-012「金水枯傷而腎經虛，水土相勝而脾胃洩」）：
    #   金水现∧不得令→枯傷；水土同现∧（冲∨克战）→相勝
    # ⚠ CAND-DTS-007/008（branch∈四生方/四库）字段粒度缺陷——单字段无法定位
    #   被冲支，规则设计待审批；CAND-DTS-010/011 冲旺衰（source/target_strength）
    #   口径待裁决；CAND-DTS-062~067（西水還南/東火轉北/順逆生/陽明/陰濁）方位流向
    #   与顺逆生判定口径不清，均登记不实现
    if base and day_stem:
        day_el = STEM_ELEMENT.get(day_stem)
        db = base.get("day_branch")
        if day_el and db:
            # 柱内关系（日柱）
            db_el = BRANCH_ELEMENT.get(db)
            hidden_db = set()
            if isinstance(hidden, dict) and db in hidden and isinstance(hidden[db], (list, tuple)):
                hidden_db = {STEM_ELEMENT.get(_s) for _s in hidden[db]}
                hidden_db.discard(None)
            # 地生天：日支行所生 == 日干行（如甲子：子水生甲木）
            if db_el and _SHENG.get(db_el) == day_el:
                out["pillar_relation"] = "地生天"
            # 天合地：日干与日支藏干五合（藏干存天干字，直接比对字面）
            HE = {"甲": "己", "乙": "庚", "丙": "辛", "丁": "壬", "戊": "癸",
                  "己": "甲", "庚": "乙", "辛": "丙", "壬": "丁", "癸": "戊"}
            he_stem = HE.get(day_stem)
            if he_stem and isinstance(hidden, dict) and db in hidden and he_stem in hidden[db]:
                out["pillar_relation"] = "天合地"
            if "pillar_relation" not in out:
                out["pillar_relation"] = "UNDETERMINED"
            # 天衰=日主非 STRONG（地生天者天衰怕衝——干自身失令即衰，得地生仍怕冲）
            # 2026-09-16 DEPRECATED：与附录L-3 strength_state 六级冲突，保留输出（对齐古典层）但规则层不得消费
            out["day_master_strength"] = "衰" if out.get("day_strength_state") != "STRONG" else "旺"
            mb_el = BRANCH_ELEMENT.get(base.get("month_branch"))
            out["branch_strength"] = "旺" if (db_el and mb_el and db_el == mb_el) else "不旺"
        # 疾病五行受制（无需 strength，独立结构事实）——三态化：补 UNDETERMINED
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        if all(stems4) and all(brs4):
            els8 = {STEM_ELEMENT.get(s) for s in stems4} | {BRANCH_ELEMENT.get(b) for b in brs4}
            els8.discard(None)
            mb_el = BRANCH_ELEMENT.get(base.get("month_branch"))
            has_chong = bool(((base or {}).get("relations") or {}).get("liu_chong"))
            zhan = out.get("zhan_state")
            if "木" in els8:
                out["wood_state"] = "不受水" if "水" not in els8 else "受水"
            else:
                out["wood_state"] = "UNDETERMINED"
            if "土" in els8:
                out["earth_state"] = "不受火" if "火" not in els8 else "受火"
            else:
                out["earth_state"] = "UNDETERMINED"
            jin_shui = {"金", "水"} & els8
            if len(jin_shui) == 2:
                de_ling_js = (mb_el in jin_shui)
                out["jinshui_state"] = "枯傷" if not de_ling_js else "不枯"
            else:
                out["jinshui_state"] = "UNDETERMINED"
            if "水" in els8 and "土" in els8:
                out["shuitu_state"] = "相勝" if (has_chong or zhan in ("天戰", "地戰")) else "不相勝"
            else:
                out["shuitu_state"] = "UNDETERMINED"
    # 情性初版（DTS-052 情性篇；PENDING_VERIFY——以干支五行同现结构事实近似，
    # 「烈」=火当令∧火透干；旺衰/五行多寡维度待 strength 精度迭代接管）
    # 059 火烈而性燥者，遇金水之激（fire_state=烈 + stimulus=金水之激 两字段独立派生，规则组合消费）
    # 060 木奔南而軟怯（wood_flow=奔南：木火同现，木向火泄）
    # 061 金見水則流通（gold_meets=水：金水同现，金生水流通）
    # 057/058（五行不戾→清和、濁亂偏枯→乖逆）结构事实不足（需五行流通/源流判定），登记待裁决，未实现
    if base and day_stem:
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        if all(stems4) and all(brs4):
            els = {STEM_ELEMENT.get(s) for s in stems4} | {BRANCH_ELEMENT.get(b) for b in brs4}
            els.discard(None)
            if isinstance(hidden, dict):
                for _v in hidden.values():
                    if isinstance(_v, (list, tuple)):
                        els |= {STEM_ELEMENT.get(_s) for _s in _v}
                els.discard(None)
            # 火烈：月支属火 ∧ 天干透火 [PENDING_VERIFY]——三态化：补反态
            if BRANCH_ELEMENT.get(base.get("month_branch")) == "火" and any(
                    STEM_ELEMENT.get(s) == "火" for s in stems4):
                out["fire_state"] = "烈"
            else:
                out["fire_state"] = "不烈"
            # 金水之激 / 金見水：金水同现（干支任一）——三态化：补反态
            if "金" in els and "水" in els:
                out["stimulus"] = "金水之激"
                out["gold_meets"] = "水"
            else:
                out["stimulus"] = "非激"
                out["gold_meets"] = "非水"
            # 木奔南：木火同现——三态化：补反态
            if "木" in els and "火" in els:
                out["wood_flow"] = "奔南"
            else:
                out["wood_flow"] = "不奔南"
    # 寒热燥湿（climate，DTS-026 寒溫濕燥論）——Human 最终裁决 2026-09-16
    # PATCH-001 §2（2026-09-16）：is_cold/is_hot/is_dry/is_wet 为「结构事实技术属性」
    # （is_present 类，供 climate/cold_level/hot_level/dry_level 枚举合成），
    # **非业务裁决**——最终业务判定只由枚举承载，规则层禁止消费 is_* 布尔。
    # 执行架构：原文证据→Source Variant→Evidence→Derived Fact→Boolean/Enum→寒热判定
    # 古文证据层 ≠ 工程判定层：寒热.txt 结构规则可执行，但证据链待重绑，不得 Admission 为最终古典规则集
    # 判定只用结构事实（月令/透干/支根/藏干），禁量化阈值：
    #   ✗ 假寒局「亥子水占比≥3」、假热局「巳午火占比≥3」、EXTREME「金水/木火≥7」均不实现（量化，无古籍原文依据）
    #   ✗ DRY_BURNT（依据《三命通会》火烈金熔——出处未证实 C6）、WITHOUT_STAGNATION（《何知章》反义 D1）、
    #     WET_STAGNANT/WET_FLOOD（依赖旺衰）挂起
    # PENDING（文档结构矛盾）：寒热.txt is_cold 条件「无明透丙丁+无巳午根」与 COLD_WITH_WARM 条件
    #   「天干有丙丁透出或地支有巳午火根」互斥（WITH_WARM 不可达）——工程按 DTS-026 正文「得氣之寒」
    #   以月令冬三月判寒局、枚举层分有暖/无暖，自洽；文档条件 2/3 与枚举矛盾待 Human 裁定
    # 判定依据绑定：DTS-026-001/003 正文 + DTS-026-002 注（B1 反义异文：内非/内有，text_variant 已记录）
    if base and day_stem:
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        if all(stems4) and all(brs4):
            mb = base.get("month_branch")
            stems_els = {STEM_ELEMENT.get(s) for s in stems4}
            br_els = {BRANCH_ELEMENT.get(b) for b in brs4}
            has_stem_fire = "火" in stems_els       # 明透丙丁（天干火行）
            has_br_fire = "巳" in brs4 or "午" in brs4  # 地支巳午火根
            has_stem_water = "水" in stems_els      # 明透壬癸（天干水行）
            has_br_water = "亥" in brs4 or "子" in brs4  # 地支亥子水根
            # is_cold：冬三月（得气之寒）；枚举层分有暖/无暖（COLD_WITH_WARM/COLD_NO_WARM）
            is_cold = mb in ("亥", "子", "丑")
            # is_hot：夏三月（得气之暖）；枚举层分有制/无制
            is_hot = mb in ("巳", "午", "未")
            # is_dry：燥土月/火月（未戌巳午）∧ 干支无亥子水 ∧ 无丑辰湿土润局
            is_dry = (mb in ("未", "戌", "巳", "午")) and ("亥" not in brs4 and "子" not in brs4
                     and "丑" not in brs4 and "辰" not in brs4 and "水" not in stems_els)
            # is_wet：湿土月/水月（辰丑亥子）∧ 无明透火 ∧ 无未戌燥土制水
            is_wet = (mb in ("辰", "丑", "亥", "子")) and (not has_stem_fire) and ("未" not in brs4 and "戌" not in brs4)
            if is_cold:
                out["is_cold"] = True
                # 寒而有暖：天干透火或地支巳午火根；寒而无暖：全局无一点火气
                if has_stem_fire or has_br_fire:
                    out["cold_level"] = "COLD_WITH_WARM"
                else:
                    out["cold_level"] = "COLD_NO_WARM"
            if is_hot:
                out["is_hot"] = True
                if has_stem_water or has_br_water:
                    out["hot_level"] = "HOT_WITH_COOL"
                else:
                    out["hot_level"] = "HOT_NO_COOL"
            if is_dry:
                out["is_dry"] = True
                # 燥而有润：地支藏干含水行（壬/癸）→ 湿气（修复 2026-09-16：
                # 原实现以干名匹配支名（_s in 亥子丑辰）恒 False，DRY_WITH_MOIST 不可达）
                moist_hidden = False
                if isinstance(hidden, dict):
                    for _v in hidden.values():
                        if isinstance(_v, (list, tuple)) and any(
                                STEM_ELEMENT.get(_s) == "水" for _s in _v):
                            moist_hidden = True
                            break
                out["dry_level"] = "DRY_WITH_MOIST" if moist_hidden else "DRY_NO_MOIST"
            if is_wet:
                out["is_wet"] = True
                # WITHOUT_STAGNATION/WET_STAGNANT/WET_FLOOD 全部挂起（D1 反义未定案+依赖旺衰），不输出等级
            # climate 单值（供 CAND-DTS-080~083 消费）：寒/熱/燥/濕/和
            if is_cold:
                out["climate"] = "寒"
            elif is_hot:
                out["climate"] = "熱"
            elif is_dry:
                out["climate"] = "燥"
            elif is_wet:
                out["climate"] = "濕"
            else:
                out["climate"] = "和"
            # climate_type 复合（四象限组合；审计用，规则层不消费）
            if is_cold and is_wet:
                out["climate_type"] = "COLD_WET"
            elif is_cold and is_dry:
                out["climate_type"] = "COLD_DRY"
            elif is_hot and is_wet:
                out["climate_type"] = "HOT_WET"
            elif is_hot and is_dry:
                out["climate_type"] = "HOT_DRY"
            else:
                out["climate_type"] = "BALANCED"
    # 真化/假化（DTS-041-002/043-002 注：日干合干單透一位在月時上合之，不遇壬癸甲乙戊己，
    # 而有辰字（龍），且化神得令（丙辛冬月/戊癸夏月/乙庚秋月/丁壬春月/甲己四季）→真化；
    # 暗扶日主、合神虛弱、無龍以運之→假化）
    # 合化行表 _HUA 依 DTS-041-002 注原文（甲己化土/乙庚化金/丙辛化水/丁壬化木/戊癸化火）；
    # 五合关系与「五合均可真化」为 DIRECT_TEXT（原文直接列举）
    # Human 裁决 2026-09-15：「不遇」存在版本异文（崇祯本「壬癸甲乙戊己」/《滴天髓阐微》
    # 「壬癸甲乙戊」/另一通行本「壬癸甲乙庚」），不固化为最终规则——
    # 仅作甲己案例原文条件保留（值按底本，PENDING_VERIFY），其余四合（乙庚/丙辛/丁壬/戊癸）
    # 原文未列「不遇」集合，不套用（DIRECT_TEXT 无此条件，不类推）
    if base and day_stem:
        stems4 = [base.get("year_stem"), base.get("month_stem"), day_stem, base.get("hour_stem")]
        brs4 = [base.get("year_branch"), base.get("month_branch"),
                base.get("day_branch"), base.get("hour_branch")]
        if all(stems4) and all(brs4):
            he = _HE.get(day_stem)
            if he and he in (stems4[1], stems4[3]):      # 月干或时干合
                hua_el = _HUA.get(day_stem)
                other_stems = [s for s in stems4 if s not in (day_stem, he)]  # 剔除日干与合干
                if hua_el:
                    # 单透：合干在四干中只一位
                    single = sum(1 for s in stems4 if s == he) == 1
                    # 「不遇」检查仅甲己合（原文字面条件，PENDING_VERIFY）；
                    # 其余四合不检查（原文未列集合，不类推）[DIRECT_TEXT]
                    not_yu = True
                    if day_stem == "甲" and he == "己":
                        day_el2 = STEM_ELEMENT.get(day_stem)
                        sheng2 = next((k for k, v in _SHENG.items() if v == day_el2), None) if day_el2 else None
                        bad = {s for s in other_stems if STEM_ELEMENT.get(s) in
                               (day_el2, sheng2, "土")}   # 壬癸（印）甲乙（比劫）戊己（同类土）
                        not_yu = not bad
                    has_chen = "辰" in brs4
                    de_ling = BRANCH_ELEMENT.get(base.get("month_branch")) == hua_el
                    if single and not_yu and has_chen and de_ling:
                        out["hua_state"] = "真"
                    elif single and not (has_chen and de_ling):
                        out["hua_state"] = "假"    # 合成立但缺龙/化神不得令 [PENDING_VERIFY]
                    else:
                        out["hua_state"] = "未化"  # 三态化 2026-09-16：合干不单透等→未化
    # 化从互斥仲裁（Human 最终裁决 2026-09-16）
    # 「合化成则论化；合化不成再论从」——有合但合而不化（假化）不终止从格判断：
    #   hua_candidate=真 → special_state=TRUE_HUA（不再论从，CAND-DTS-048 消费）
    #   hua_candidate≠真（无合/假化）→ 再判从：cong_candidate 有值（真/假）→ TRUE_CONG
    #   （CAND-DTS-047/049 消费，method 区分真从/假从）
    #   均不成立 → NONE（普通格局）
    # 内部保留 hua_candidate/cong_candidate 审计字段；special_state 单一输出
    hua_c = out.get("hua_state")
    if hua_c:
        out["hua_candidate"] = hua_c
    cong_c = None
    if out.get("cai_guan_state") == "STRONG":
        cong_c = "真" if out.get("cong_support_state") == "NONE" else "假"
        out["cong_candidate"] = cong_c
    if hua_c == "真":
        out["special_state"] = "TRUE_HUA"
    elif cong_c:
        out["special_state"] = "TRUE_CONG"
    else:
        out["special_state"] = "NONE"
    # P-1~P-3 执行隔离（Human 裁决 2026-09-16）：PENDING 枚举只许登记/审计/测试，
    # 不得作为正式 Derived Fact 输出、不得被规则消费——统一收拢到 out["pending"] 命名空间。
    # 隔离后规则 preconditions 引用这些字段将永不满足（执行隔离 + 治理层 PENDING 双保险）。
    # xing_state 特赦（Human 2026-09-16：len(distinct)==5 属「五行俱全」全集覆盖结构条件，
    # 非统计量化，允许保留正式输出，不判违规）。
    _PENDING_FIELDS = ("tian_status", "di_status", "stem_position", "pattern",
                       "zhan_state", "xiang_state", "hua_state", "hua_candidate",
                       "fire_state", "stimulus", "gold_meets", "wood_flow",
                       "cold_level", "hot_level", "dry_level",
                       "qing_state", "qingqi_state", "guan",
                       "zhen_shen_state", "jia_shen_state", "jishen_state",
                       "xiongwu_state", "wo_shi", "di", "decai_relation",
                       "wuxing_state", "rigan_state", "caixing",
                       "rensha_state", "caiguan", "geju",
                       "yangren_state", "yongshen_state",
                       "zhige_state", "xueqi_state", "jishen_location",
                       "keshen_location", "pillar_relation", "day_master_strength",
                       "branch_strength", "wood_state", "earth_state",
                       "jinshui_state", "shuitu_state",
                       "xing_ding_state")
    pending = {}
    for _f in _PENDING_FIELDS:
        if _f in out:
            pending[_f] = out.pop(_f)
    if pending:
        out["pending"] = pending
    return out
