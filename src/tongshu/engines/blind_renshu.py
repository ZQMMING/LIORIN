# -*- coding: utf-8 -*-
"""盲派释义层 (㊻s124): 子维级·原著颗粒度 → 取到象的子维输出「白话+类象锚点+ch依据+应期」, 虚象单列不坐实.

ch13 虚实法则 + ㊻s124 颗粒度:
  域是范围, 子维才是断点. 每个子维必须查「它自己的引擎字段」是否取到象(不塌缩到域),
  取到象 → 出 白话 + 类象锚点(命局实际值) + ch 依据 + 域内挂应期;
  取不到 → 单列 "象未坐实(不坐实断)", 不出断语/不挂年.

颗粒度来源(零新判据, 只消费引擎已算字段):
  - 引擎每域 _event_structure dict(配偶宫=palace_state/婚次数/早晚/副宫多现/正偏夫...)
  - 引擎 *_evidence 判据说明列表
  - ch 类象速查(ch3/ch5/ch6/ch8/ch9/ch10/ch11): 类象锚点映射
  本层只做「映射+展示」, 不引入新判据(铁律: 案例不进引擎, duanju/renshu 均为纯 mapper).
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from . import blind_duanju as _dj
from .blind_yingqi import BlindYingqiEngine

# ── 干支枚举 → 中文(与 tongshu.facts.bazi_facts 同键) ──
_GAN = {"JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁", "WU": "戊", "JI": "己",
        "GENG": "庚", "XIN": "辛", "REN": "壬", "GUI": "癸"}
_ZH = {"ZI": "子", "CHOU": "丑", "YIN": "寅", "MAO": "卯", "CHEN": "辰", "SI": "巳",
       "WU": "午", "WEI": "未", "SHEN": "申", "YOU": "酉", "XU": "戌", "HAI": "亥"}

def _gz_cn(gz: str) -> str:
    gz = (gz or "").upper()
    if not gz:
        return ""
    for sk, sv in _GAN.items():
        if gz.startswith(sk):
            rest = gz[len(sk):]
            for bk, bv in _ZH.items():
                if rest.startswith(bk):
                    return sv + bv
    return gz


# ── ch 类象锚点映射(支→物象, ch3 L24-35; 干→物象 ch3 L8-17) ──
_BR_OBJ = {  # 支主 行业/物象 (ch3 L24-35)
    "ZI": "水/冰/车船/贸易/玄学", "CHOU": "坟墓/牢狱/银行/军营/沼泽",
    "YIN": "树木/神龛/政府机关", "MAO": "草木/绳索/织物/网络/床",
    "CHEN": "湿土/水库/车辆/机器/中药", "SI": "阴火/文化/影像/道路/网络",
    "WU": "阳火/火器/光彩/信息/广告/剧场", "WEI": "温土/田园/酒店/医药/热毒",
    "SHEN": "铁器/刀/车/军队/司法/机器/医院/金融", "YOU": "金石/剑戟/银行/钟表/法律/技术/玄学",
    "XU": "燥土/窑炉/枪弹/军火/牢狱/坟墓/学校/影院/市场/互联网",
    "HAI": "池塘/酒/水产/科技/运算/数字/思想",
}
_GAN_OBJ = {  # 干主 人性/形 (ch3 L8-17)
    "JIA": "甲=雷/大树/栋梁/公门·宽仁磊落·形直", "YI": "乙=风/花木/栏杆/毛笔·朴实柔情·形曲",
    "BING": "丙=太阳/帝王/传媒/电·激情多言·形大", "DING": "丁=星/灯火/文化/玄学/香火·文雅多思·形小",
    "WU": "戊=大地/山丘/政府/房地产/仓库·忠厚老成·形方", "JI": "己=云/田园/房屋/墓地/财帛·含蓄多疑·形平",
    "GENG": "庚=顽铁/机器/金融/军队/西医·刚强暴躁·形棱角", "XIN": "辛=金/珠宝/针/医药/法律·通达灵动·形致密",
    "REN": "壬=海/江河/航运/贸易/石油·智谋任性·形无规则", "GUI": "癸=雨露/泉/泪/玄学/智业·聪明机敏·形圆润",
}
# 宫位八维·空间/身体 (ch5 L9-11)
_PALACE_SP = {"YEAR": "远方/海外", "MONTH": "祖籍/家乡", "DAY": "现在居所", "HOUR": "门户/出门/远方"}

# 未取到象的子维登记语
_MISS = "象未坐实(不坐实断)"

# 取财方式四分流 (ch8 L13-21): 经营/风险/工薪/打工
# 引擎已算 occupation_candidate.wealth_style (List[str]), 此处纯展示.
def _wealth_style(res) -> str:
    oc = getattr(res, "occupation_candidate", None)
    if isinstance(oc, dict):
        ws = oc.get("wealth_style", "")
        if isinstance(ws, list):
            return "/".join(ws) or "UNDETERMINED"
        return ws or "UNDETERMINED"
    return "UNDETERMINED"

# ── 13 域子维 (维度文本, 用户给的 13 域 N 子维) ──
_SUBDIM: Dict[str, List[str]] = {
    "六亲": ["父母寿缘家境", "手足缘分", "配偶象", "子女厚薄"],
    "事业": ["做功方式定行业岗位", "职权", "转职", "失业", "是非"],
    "财运": ["求财路径", "进财", "破财", "不动产", "取财方式", "富贵程度"],
    "婚姻感情": ["配偶宫动静", "合冲", "婚外缘分", "分居离异", "多婚源", "独身象"],
    "健康": ["干支对应身体部位", "禄刃受损", "墓库看慢病伤病"],
    "灾厄是非": ["官杀破损", "穿禄", "冲刃", "官司意外牢狱伤病"],
    "人际合伙": ["同辈互动", "合伙成败", "利益争夺", "同伴反目"],
    "家宅居所": ["置业变卖", "搬迁移居", "宅内是非", "房屋纠纷"],
    "名气口碑": ["扬名机会", "流言非议", "公众评价", "声誉得失"],
    "学业技艺": ["悟性高低", "文凭证书", "技艺类型", "考证成败"],
    "出行异地": ["异地谋生", "远行吉凶", "在外定居", "奔波变动"],
    "心性性格": ["内心底色", "处事模式", "城府深浅", "脾气特质"],
    "福分寿元": ["寿元厚薄", "享福安稳", "操劳程度", "福气得失"],
}


def _evidence(res, *names) -> str:
    """取引擎已算的 *_evidence 判据说明(取第一条), 作 ch 依据展示. 无则空."""
    for n in names:
        ev = getattr(res, n, None)
        if isinstance(ev, list) and ev and str(ev[0]).strip():
            return str(ev[0])
    return ""


def _probe(res, dom: str, sub: str):
    """返回 (hit, 白话, 类象锚点, ch依据, 定位域键).
    hit=False → 白话=未坐实登记语, 其余空. 全部读引擎已产字段, 零新判据."""
    miss = _MISS

    if dom == "六亲":
        pa = res.parental_event_structure if isinstance(res.parental_event_structure, dict) else {}
        ch = res.child_event_structure if isinstance(res.child_event_structure, dict) else {}
        fa_state = pa.get("father_state", "UNDETERMINED")
        mo_state = pa.get("mother_state", "UNDETERMINED")
        if sub == "父母寿缘家境":
            # ㊻s124g 精度打磨: 父/母星三态细分(引擎 enum STRONG/WEAKENED/ABSENT), 不再混读一刀切:
            # STRONG=在局非缘薄(寿缘家境可断); WEAKENED=在局但受克/克星(缘薄可断, 非寿缘);
            # ABSENT=缘薄(祖上宫被冲穿/星不在局); 全 UNDETERMINED=未坐实.
            if fa_state == "STRONG" or mo_state == "STRONG":
                b = f"父星={fa_state}/母星={mo_state}"
                chref = _evidence(res, "parental_event_evidence")
                return (True, "父母寿缘家境可断(父星/母星在局非缘薄, ch5)", b, chref, "长辈家宅")
            if fa_state == "WEAKENED" or mo_state == "WEAKENED":
                b = f"父星={fa_state}/母星={mo_state}"
                chref = _evidence(res, "parental_event_evidence")
                return (True, "父母缘薄可断(父星/母星在局但受克/克星=缘薄非寿缘, ch5)", b, chref, "长辈家宅")
            # ABSENT=缘薄(祖上宫被冲穿/星不在局), 引擎判了也是真象
            if pa:
                b = f"父星{pa.get('father_star','')}={fa_state}/母星{pa.get('mother_star','')}={mo_state}"
                return (True, "父母缘薄(财克印/比劫夺财=母缘薄·父缘薄, ch5年柱祖上被冲穿)", b, pa.get("note", "ch5"), "长辈家宅")
            return (False, miss, "", "", "长辈家宅")
        if sub == "手足缘分":
            hit = any(m == "比劫制财" for m in res.zuo_gong_methods) or \
                  res.bijie_zhichai_fenliu not in ("UNDETERMINED", "")
            return (hit, ("手足缘可断(比劫在局=有手足; 主位分禄=手足争产, ch6)" if hit else miss),
                   f"比劫分禄={res.bijie_zhichai_fenliu}", "", "长辈家宅")
        if sub == "配偶象":
            mm = res.marriage_event_structure if isinstance(res.marriage_event_structure, dict) else {}
            hit = mm.get("marriage_state", "UNDETERMINED") not in ("UNDETERMINED", "")
            return (hit, ("配偶象可断(婚姻系统有象, ch10)" if hit else miss),
                   f"婚状态={mm.get('marriage_state','')}/宫={mm.get('spouse_palace','')}", "", "婚姻口舌")
        if sub == "子女厚薄":
            hit = ch.get("child_state", "UNDETERMINED") not in ("UNDETERMINED", "")
            return (hit, ("子女厚薄可断(子女系统: 星有=有子·宫冲=子薄, ch4)" if hit else miss),
                   f"子女星在={ch.get('child_star_present','')}/时支冲={ch.get('hour_attacked','')}", "", "子女前程")
        return (False, miss, "", "", "长辈家宅")

    if dom == "事业":
        off = res.official_event_structure if isinstance(res.official_event_structure, dict) else {}
        state = off.get("official_state", "UNDETERMINED")
        # ㊻s124f 精度打磨: 事业 5 子维各查各字段, 不再塌缩到 official_state != UNDET:
        # 职权=官有(official_state 非 UNDET) 或 企业之官(cai_ku_zhi_yin) 或 管理权(guan_he=TAGUAN_WO/MANLI)
        # 是非=UNCONTROLLED(官杀无制必犯官非, ch9) 或 CONTROLLED_PARTIAL(制不净带非)
        # 转职/失业=DAMAGED(官根受损=官动换岗) 或 ROBBED(官被劫走=丢职)
        guan_kw = off.get("guan_he_consume", "")
        has_off = state not in ("UNDETERMINED", "")
        submap = {
            "做功方式定行业岗位": ("行业/岗位可做功定位(官命做功指向, ch8/ch9)", has_off),
            "职权": ("职权可断(官有/企业之官/合官管理权, ch9)",
                  has_off or off.get("cai_ku_zhi_yin","")=="TRIGGERED" or guan_kw=="MANLI"),
            "转职": ("转职/变动象(官根损/官被劫=换岗, ch9)", state in ("DAMAGED","ROBBED")),
            "失业": ("失业象(官损/官被劫=丢职, ch9)", state in ("DAMAGED","ROBBED")),
            "是非": ("官非口舌(官杀制不净/无制=带非, ch9)", state in ("UNCONTROLLED","CONTROLLED_PARTIAL")),
        }
        t, hit = submap.get(sub, (miss, False))
        anchor = f"官状态={state}/控制度={off.get('control_completeness','')}/合官消费={guan_kw}/企业官={off.get('cai_ku_zhi_yin','')}"
        return (hit, (t if hit else miss), anchor, _evidence(res, "official_evidence"), "事业官贵")

    if dom == "财运":
        w = res.wealth_event_structure if isinstance(res.wealth_event_structure, dict) else {}
        # ㊻s124f 精度打磨: 财域 6 子维各查各字段, 不再塌缩到 wealth_state:
        # 求财路径=wealth_state 非 UNDET(有做功路径); 进财=wealth_present; 破财=bijie_zhichai_fenliu;
        # 不动产=shi_zhicaixiang; 取财方式=wealth_style; 富贵程度=西瓜皮肉
        submap = {
            "求财路径": ("求财路径可断(做功方式: 经营/工薪/风险/打工, ch8)", w.get("wealth_state", "UNDETERMINED") not in ("UNDETERMINED", "")),
            "进财": ("进财可断(财星得地/做功指向财, ch8)", w.get("wealth_present", "False") in ("True", True)),
            "破财": ("破财象(比劫分禄/财被夺=破财, ch8)", w.get("bijie_zhichai_fenliu", "UNDETERMINED") not in ("UNDETERMINED", "")),
            "不动产": ("不动产/置产象(财库/墓库=置产, ch8)", w.get("shi_zhicaixiang", "UNDETERMINED") not in ("UNDETERMINED", "")),
            # ── ㊻s124e ch8 取财方式四分流/富贵程度(西瓜皮肉)(引擎 wealth_efficiency 已算, ch8 L13-21 取财方式 + L21 西瓜皮肉) ──
            "取财方式": ("取财方式可断(经营/风险/工薪/打工, ch8 L13-21)", _wealth_style(res) not in ("UNDETERMINED", "")),
            "富贵程度": ("富贵程度可断(西瓜皮肉: 合到财库=吃肉富/合到财外=吃皮穷, ch8 L21)", w.get("wealth_efficiency", "UNDETERMINED") in ("CHI_ROU", "CHI_PI")),
        }
        t, hit = submap.get(sub, (miss, False))
        # 颗粒度: 财状态 + 象替 + 取财方式 + 西瓜皮肉
        style = _wealth_style(res)
        wei = w.get("wealth_efficiency", "UNDETERMINED")
        anchor = f"财状态={w.get('wealth_state','')}/象替={w.get('image_substitution','')}/取财方式={style}/西瓜皮肉={wei}"
        return (hit, (t if hit else miss), anchor, _evidence(res, "wealth_evidence"), "财富")

    if dom == "婚姻感情":
        mm = res.marriage_event_structure if isinstance(res.marriage_event_structure, dict) else {}
        fu = getattr(res, "fugong_palace", "UNDETERMINED")
        submap = {
            "配偶宫动静": ("配偶宫动静可断(宫冲/破=婚动, ch10)", mm.get("palace_state", "UNDETERMINED") not in ("UNDETERMINED", "")),
            "合冲": ("合冲可断(夫宫/夫星合冲=应期, ch10)", mm.get("marriage_timing", "UNDETERMINED") not in ("UNDETERMINED", "")),
            "婚外缘分": ("婚外/副缘象(副宫多现=短暂副缘, ch7/ch10)", fu not in ("UNDETERMINED", "")),
            "分居离异": ("分居离异象(宫坏+星弱=离异, ch10)", mm.get("marriage_state", "") == "BROKEN"),
            # ── ㊻s124e ch10 多婚源/独身象(引擎 marriage_count_signal/marriage_solitary 已算, ch10 L16-17 多婚看星宫多现/副宫多现; L20-24 独身四型) ──
            "多婚源": ("多婚源可断(星宫多现/副宫多现=几次夫妻星几次婚姻, ch10 L16-17)", mm.get("marriage_count_signal", "") == "MULTIPLE"),
            "独身象": ("独身象可断(水中捞月=正星坐宫+日主自合+偏星干扰, ch10 L20-24)", mm.get("marriage_solitary", "") == "SHUI_ZHONG_LAO_YUE"),
        }
        t, hit = submap.get(sub, (miss, False))
        # 颗粒度: 配偶宫支的物象 + 宫动静 + 早晚 + 独身/多婚
        palace = mm.get("spouse_palace", "")
        solitary = mm.get("marriage_solitary", "UNDETERMINED")
        cheng = mm.get("marriage_count_signal", "UNDETERMINED")
        solitary_txt = f"/独身={solitary}" if solitary == "SHUI_ZHONG_LAO_YUE" else ""
        anchor = f"配偶宫={palace}({_BR_OBJ.get(palace,'')})/宫动静={mm.get('palace_state','')}/婚次数={cheng}{solitary_txt}/早晚={mm.get('marriage_timing','')}/正偏夫={getattr(res,'poshui_star','')}"
        chref = _evidence(res, "marriage_evidence") or _evidence(res, "poshui_star_evidence")
        return (hit, (t if hit else miss), anchor, chref, "婚姻口舌")

    if dom == "健康":
        b = res.body_event_candidate if isinstance(res.body_event_candidate, dict) else {}
        lu_present = b.get("lu_present", "False") in ("True", True)
        lu_attacked = b.get("lu_attacked", "False") in ("True", True)
        candidate = b.get("candidate", "UNDETERMINED")
        # ㊻s124g 精度打磨: 健康 3 子维各查各字段, 不再混读 candidate:
        # 部位=引擎 body_part(ch5 宫位八维 年腿足/月躯干/日支五脏/时头面, 禄被冲穿才确认受损);
        # 禄刃受损=candidate 非 UNDET(禄受损/刃坐/刃冲); 慢病=墓库收物做功(ch4 闭库收该五行=慢病, 消费已产方法)
        body_part = b.get("body_part", "UNDETERMINED")
        muku_shouwu = "墓库收物" in res.zuo_gong_methods
        submap = {
            "干支对应身体部位": ("身体部位可定位(支被冲穿=对应宫位部位伤, ch5)", body_part not in ("UNDETERMINED", "")),
            "禄刃受损": ("禄刃受损象(禄被冲穿/刃被冲=血光, ch4/ch5)", candidate not in ("UNDETERMINED", "")),
            "墓库看慢病伤病": ("墓库慢病象(墓库收物=收该五行慢病, ch4)", muku_shouwu),
        }
        t, hit = submap.get(sub, (miss, False))
        anchor = f"禄在={lu_present}/禄被冲={lu_attacked}/候选={candidate}/部位={body_part}/墓库收物={muku_shouwu}"
        return (hit, (t if hit else miss), anchor, _evidence(res, "body_event_evidence"), "官贵刑伤")

    if dom == "灾厄是非":
        off = res.official_event_structure if isinstance(res.official_event_structure, dict) else {}
        b = res.body_event_candidate if isinstance(res.body_event_candidate, dict) else {}
        crime = getattr(res, "crime_structure", "UNDETERMINED") or "UNDETERMINED"
        crime_present = getattr(res, "crime_present", False)
        # ㊻s124g 精度打磨: 灾厄 4 子维各查各字段, 不再混读:
        # 官杀破损=官方态 DAMAGED(官根受损); 穿禄=禄被冲穿; 冲刃=刃在且被冲(候选 YANG_REN_CLASHED);
        # 牢狱伤病=crime_present(犯罪结构坐实)
        lu_present = b.get("lu_present", "False") in ("True", True)
        lu_attacked = b.get("lu_attacked", "False") in ("True", True)
        candidate = b.get("candidate", "UNDETERMINED")
        submap = {
            "官杀破损": ("官杀破损象(官根损=官非/是非, ch9/ch12)", off.get("official_state", "") == "DAMAGED"),
            "穿禄": ("穿禄象(禄被冲穿=身体/灾, ch4)", lu_present and lu_attacked),
            "冲刃": ("冲刃象(刃被冲=血光/刑伤, ch4)", candidate == "YANG_REN_CLASHED"),
            "官司意外牢狱伤病": ("官司/牢狱象(犯罪结构坐实, ch12)", crime_present),
        }
        t, hit = submap.get(sub, (miss, False))
        anchor = f"犯罪结构={crime}/犯罪present={crime_present}/官状态={off.get('official_state','')}/禄在={lu_present}/禄被冲={lu_attacked}/候选={candidate}"
        chref = _evidence(res, "crime_evidence")
        return (hit, (t if hit else miss), anchor, chref, "官贵刑伤")

    if dom == "人际合伙":
        ip = getattr(res, "interpersonal_structure", "UNDETERMINED")
        submap = {
            "同辈互动": ("同辈互动(比肩在局=有同辈缘, ch6)", res.bijie_zhichai_fenliu not in ("UNDETERMINED", "")),
            "合伙成败": ("合伙成败可断(比劫当财=合伙成/分禄=合伙散, ch8)", ip in ("HEHUA_DECAI", "FENLU_ZHENGDUI")),
            "利益争夺": ("利益争夺(主位比劫分禄=争财被分, ch6)", ip == "FENLU_ZHENGDUI" or res.bijie_zhichai_fenliu == "FENLU_POCAI"),
            "同伴反目": ("同伴反目(比劫伤官=拉帮结派, ch12)", ip == "BIXIONG" or (getattr(res, "crime_structure", "UNDETERMINED") not in ("UNDETERMINED", ""))),
        }
        t, hit = submap.get(sub, (miss, False))
        return (hit, (t if hit else miss), f"人际结构={ip}", _evidence(res, "interpersonal_evidence"), "人事竞争")

    if dom == "家宅居所":
        sd = getattr(res, "space_dynamic", "UNDETERMINED")
        submap = {
            "搬迁移居": ("搬迁移居(驿马/空间动, ch4/ch5)", sd in ("YIDI", "CHUYING", "BANQIAN")),
            "宅内是非": ("宅内是非(月柱被冲=家宅动荡, ch5)", sd == "JIAZHAI_DONG"),
            "房屋纠纷": ("房屋纠纷(库冲/破, ch4)", sd in ("BANQIAN", "JIAZHAI_DONG")),
        }
        if sub == "置业变卖":
            hit = res.wealth_event_structure.get("shi_zhicaixiang", "UNDETERMINED") not in ("UNDETERMINED", "")
            return (hit, ("置业/变产象(财库/墓库, ch8)" if hit else miss), f"财象替={res.wealth_event_structure.get('image_substitution','')}", "", "财富")
        t, hit = submap.get(sub, (miss, False))
        return (hit, (t if hit else miss), f"空间={sd}/宫位={getattr(res,'space_palace','')}", "", "长辈家宅")

    if dom == "名气口碑":
        mq = getattr(res, "mingqi_structure", "UNDETERMINED")
        off = res.official_event_structure if isinstance(res.official_event_structure, dict) else {}
        submap = {
            "扬名机会": ("扬名机会(泄秀/官杀虚透=成名, ch9/ch11)", mq in ("XUTOU_MINGQU", "XIUXIU_CHENGMING", "XINGZUO_DEJIANG")),
            "流言非议": ("流言非议象(官杀制不净=口舌, ch9)", off.get("official_state", "") == "CONTROLLED_PARTIAL"),
            "公众评价": ("公众评价(名气做功方向, ch9)", mq not in ("UNDETERMINED", "")),
            "声誉得失": ("声誉得失(名气坐实/被夺, ch9)", mq not in ("UNDETERMINED", "")),
        }
        t, hit = submap.get(sub, (miss, False))
        return (hit, (t if hit else miss), f"名结构={mq}", _evidence(res, "mingqi_evidence"), "学业文书")

    if dom == "学业技艺":
        edu = getattr(res, "education_level", "UNDETERMINED") or "UNDETERMINED"
        eff = res.zuo_gong_methods
        submap = {
            "悟性高低": ("悟性(印星/食伤=聪慧度, ch11)", any(m in ("印制食伤", "食伤泄秀", "食伤生财", "财制印") for m in eff)),
            "文凭证书": ("文凭证书可断(学历三神: 官杀/印/食神, ch11)", edu in ("HIGHER_EDU", "BASIC_EDU", "NO_EDU")),
            "技艺类型": ("技艺类型(食伤做功=技艺/作品, ch11)", any(m in ("食伤生财", "食伤泄秀") for m in eff)),
            "考证成败": ("考证成败(学域做功方向, ch11)", edu not in ("UNDETERMINED", "")),
        }
        t, hit = submap.get(sub, (miss, False))
        # 颗粒度: 学科分流(引擎 education_field) + 学中断
        anchor = f"学历={edu}/学科={getattr(res,'education_field','')}/学中断={getattr(res,'edu_zhongduan','')}"
        return (hit, (t if hit else miss), anchor, _evidence(res, "education_evidence"), "学业文书")

    if dom == "出行异地":
        sd = getattr(res, "space_dynamic", "UNDETERMINED")
        submap = {
            "异地谋生": ("异地谋生(驿马/空间动=外出, ch4/ch5)", sd in ("YIDI", "CHUYING")),
            "远行吉凶": ("远行吉凶(马星方向, ch4)", sd in ("YIDI", "CHUYING", "BANQIAN")),
            "在外定居": ("在外定居象(驿马坐库/合, ch4)", sd in ("YIDI", "CHUYING")),
            "奔波变动": ("奔波变动(马多动/冲, ch4)", sd in ("BANQIAN", "JIAZHAI_DONG")),
        }
        t, hit = submap.get(sub, (miss, False))
        yima = getattr(res, "yima_branches", None)
        anchor = f"空间={sd}/驿马={yima}"
        return (hit, (t if hit else miss), anchor, "", "长辈家宅")

    if dom == "心性性格":
        dm = getattr(res, "day_master_personality", "UNDETERMINED") or "UNDETERMINED"
        xx = getattr(res, "xingxing_cheganshen", "UNDETERMINED") or "UNDETERMINED"
        eff = res.zuo_gong_methods
        submap = {
            "内心底色": ("内心底色(日主性格, ch14)", dm not in ("UNDETERMINED", "")),
            "处事模式": ("处事模式(取财/制官做功路径可定位, ch8)",
                        any(m in ("食伤生财","食伤泄秀","合财入库","比劫制财","财制比劫",
                                  "官杀制比劫","伤官制官","印制食伤","印化官杀","食伤制杀") for m in eff)),
            "城府深浅": ("城府深浅(暗合/包局=有城府, ch7)", any(m in ("暗合", "包局") for m in eff)),
            "脾气特质": ("脾气特质(撤干神二象, ch14)", xx not in ("UNDETERMINED", "")),
        }
        t, hit = submap.get(sub, (miss, False))
        # 颗粒度: 日干物象(ch3 干象四层)
        anchor = f"日主象={dm}/撤干神={xx}/做功={len(eff)}种"
        return (hit, (t if hit else miss), anchor, _evidence(res, "day_master_personality_evidence", "xingxing_evidence"), "")

    if dom == "福分寿元":
        ff = getattr(res, "fufen_structure", "UNDETERMINED")
        eff = res.zuo_gong_methods
        submap = {
            "寿元厚薄": ("寿元厚薄(食伤=寿有根/枭夺食=受损, ch4)", ff in ("SHOULD_YANHE", "SHOUYUAN_XUEYUAN")),
            "享福安稳": ("享福安稳(正印为忌=操劳/享福薄, ch13)", ff == "CAOLAO" or "印制食伤" in eff),
            "操劳程度": ("操劳程度(做功散=操劳/集中=安稳, ch13)", res.work_efficiency not in ("UNDETERMINED", "")),
            "福气得失": ("福气得失(结构清晰度/一贵抵九贱, ch13)", res.structure_clarity not in ("UNDETERMINED", "")),
        }
        t, hit = submap.get(sub, (miss, False))
        anchor = f"福结构={ff}/做功效率={res.work_efficiency}/结构清晰度={res.structure_clarity}"
        # ch2 应期定法是流年定点(禄/原身到字), 心性/福寿属长期基调不断流年;
        # 寿元受损/享福薄等"结构象"挂 官贵刑伤 域(刑伤事件=寿损应期), 其余子维不挂.
        if hit and sub in ("寿元厚薄", "享福安稳"):
            key = "官贵刑伤"
        else:
            key = ""
        return (hit, (t if hit else miss), anchor, _evidence(res, "fufen_evidence"), key)

    return (False, miss, "", "", "")


def _yu_period(yq, birth, gender, key: str, top_n: int) -> str:
    """子维应期: 仅 hit 时按子维定位域键挂 top N 年. key 空 = 不挂年(性格/福寿不断年)."""
    if not key or not yq or not birth:
        return ""
    try:
        loc = yq.locate_event(birth, gender, domain=key, top_n=top_n)
    except Exception:
        loc = []
    if not loc:
        return ""
    return "；".join(f"{x['year']}({_gz_cn(x.get('ganzhi', ''))})" for x in loc[:top_n])


def renshu(res, yq: Optional[BlindYingqiEngine] = None,
           birth: Optional[Tuple] = None, gender: str = "male",
           year_range: Optional[Tuple] = None, top_n: int = 3) -> Dict[str, object]:
    """释义层入口(㊻s124 子维级·原著颗粒度): 13 域 → N 子维, 逐维查真实字段象存在性.

    取到象的子维 → 白话 + 类象锚点 + ch依据 + 应期; 取不到 → 登记 "象未坐实".
    铁律: 案例不进引擎(本层纯 mapper, 只读 res 字段 + duanju + yq 定位).
    """
    duj = _dj.generate_duanju(res, yq=yq, birth=birth, gender=gender,
                              year_range=year_range, top_n=top_n)
    huaxiang = duj.get("画像") or []
    tongsang = " ".join(huaxiang)

    yuzi: Dict[str, Dict] = {}
    for dom in _SUBDIM:
        zivi: Dict[str, Dict] = {}
        for sub in _SUBDIM[dom]:
            hit, rns, anchor, chref, key = _probe(res, dom, sub)
            yq_txt = _yu_period(yq, birth, gender, key, top_n) if hit else ""
            zivi[sub] = {"取象": hit, "白话": rns, "类象": anchor, "依据": chref, "应期": yq_txt}
        yuzi[dom] = {"子维": zivi}
    return {"画像": huaxiang, "总纲": tongsang, "域子维": yuzi}


def renshu_to_text(rs: Dict[str, object]) -> str:
    """子维级·原著颗粒度成文: 取到象的子维 ✓ 出 白话+类象锚点+ch依据+应期; 未取象 × 登记不坐实.

    ch13 虚实法则: 虚象(未取到)不出断语/不挂应期, 只登记"未坐实"供核证."""
    lines = ["═══ 盲派释义 (子维级·ch13虚实: 取到象才断, 虚象不坐实, 附类象锚点+ch依据) ═══"]
    lines.append(rs.get("总纲", ""))
    lines.append("")
    for dom, dv in (rs.get("域子维") or {}).items():
        zivi = dv["子维"]
        hit_subs = [(s, v) for s, v in zivi.items() if v["取象"]]
        miss_subs = [s for s, v in zivi.items() if not v["取象"]]
        lines.append(f"  【{dom}】")
        for s, v in hit_subs:
            yq = f"  应期: {v['应期']}" if v.get("应期") else ""
            anchor = f"  [类象: {v['类象']}]" if v.get("类象") else ""
            chref = f"  [{v['依据']}]" if v.get("依据") else ""
            lines.append(f"    ✓ {s}: {v['白话']}{anchor}{chref}{yq}")
        if miss_subs:
            lines.append(f"    × 象未坐实(不坐实断): {'、'.join(miss_subs)}")
    return "\n".join(lines)
