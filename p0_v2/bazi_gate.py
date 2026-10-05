# -*- coding: utf-8 -*-
"""
四柱临时接口 + 切片/案例入口 —— 顺天子平线唯一正式工作入口
================================================================
User 2026-10-01 定的三类保留:
  ① 八字排盘临时接口  ② 切片  ③ 案例

铁律(v1.8 §10.3 卡点六/七):
  · 一切十神/五行/藏干/旺衰/格局/喜忌判定 **必须走本接口进真实引擎**
  · 禁止手写 GAN_WX / SH / KE / SHENG 等映射表替代引擎实现
    (全仓已有 13 处重复 GAN_WX, 见 _archive_scratch/README.md)
  · 禁止在脚本内自行推旺衰/轻重结论 —— 引擎没输出的就是没有
  · 数据来源必须声明, 不凭控制台印象下结论

用法:
    from p0_v2.bazi_gate import paipan, walk_layers, load_slices, load_cases, read_slice

    # ① 排盘: 四柱进引擎
    r = paipan("癸酉丁巳己卯甲戌")
    r["ten_god"]["hour"]        # '正官'  ← 引擎算的
    r["hidden"]["month"]        # ['己']   ← 引擎算的
    r["wuxing_power"]["木"]     # {ling_state, ben_n, ...}  ← 引擎算的
    r["ge_cheng"]               # {ge, xi_wx, ti_wx, po_ge, rule}
    r["special"]                # {cong_type, zhuanwang, hua_qi, ...}

    # ② 切片: 查判据依据 (改判据前必查, 卡点八)
    sl = read_slice("STRUCTURE.GE_JU.HUA_GE.001")
    sl["准神归属"]              # '准' / '旁参' / '被DTS否决'
    sl["原文"]

    # ③ 案例: 取古籍命例
    for c in load_cases("PZZQ"):
        c["case_id"], c["bazi"], c["analysis"], c["pollution"]
"""
from __future__ import annotations
import os
import re
import sys
import json
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 本文件在 p0_v2/ 下, 必须把仓根加进 sys.path 才能 import engines.*
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ---- 引擎入口(唯一, 全部来自引擎实现, 本文件不复制任何映射表) ----
from engines.common.l0_fact_builder import build as _l0build, ten_god, HIDDEN
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.daymaster_power_structure import build_power_structure
from engines.common.daymaster_root_class import build_root_classes
from engines.common.daymaster_tou_cang import build_tou_cang
from engines.common.daymaster_wang_xiang import build_wang_xiang
from engines.common.daymaster_root_relations import build_root_relations
from engines.common.daymaster_two_side import build_two_side
from engines.common.daymaster_branch_tier import build_branch_tiers
from engines.common.daymaster_power_network import build_power_network
from engines.common.daymaster_power_queries import run_queries
from engines.common.root_effectiveness_filter import filter_root_effectiveness
from engines.common.wangshuai_structure import build_wangshuai_structure
from engines.common.bingyao_layer import build_bingyao_layer
from engines.common.bing_debate import resolve_primary_bing
from engines.common.zhuangui_layer import resolve_zhuangui
from engines.common.qtbj_climate_candidates import build_climate_candidates
from engines.common.yongyao_resolve import resolve_yongyao
from engines.common.fan_ju import resolve_fan_ju
from engines.common.special_pattern import build_special_patterns
from engines.common.ge_jie_layer import (build_ge_cheng, apply_he_po_ge,
                                              normalize_ti_wx)  # STEP-2.4b / STEP-DBG-4
# ★ 裁七十一乙 (2026-10-04) 拓扑派生层接入 (原孤立模块, 见契约 §4.0 v1.9)
#   只调 4 个已落函数 + 通关映射表; 不调 loose 对照版(不供判定)。
from engines.common.topology_paths import (
    build_yuan_liu_skeleton, find_tong_guan, check_fang_ju_ming_same_wx,
    check_guan_topology, TONG_GUAN_MAP)

# 十神/藏干来自 l0_fact_builder(引擎自己的), 供外部引用
TEN_GOD = ten_god
HIDDEN_STEMS = HIDDEN

SLICE_LIB = os.path.join(ROOT, "p0_v2", "六部经典MD文库")
CASE_DIR = os.path.join(ROOT, "p0_v2", "case_audit")
BOOKS = ("DTS", "PZZQ", "QTBJ", "SFTK", "SMTH", "YHZP")

_POS = ("year", "month", "day", "hour")


# ==================== ① 八字排盘临时接口 ====================

def paipan(bazi: str) -> Dict[str, Any]:
    """四柱字符串进真实引擎, 返回全部层事实。只排盘, 不下任何结论。"""
    bz = "".join(str(bazi).split())
    if len(bz) != 8:
        raise ValueError("四柱须 8 字(4干4支), 收到 %r" % bazi)

    p = _pillars(bz)
    f = _l0build(p)
    f["pillars"] = p
    f["wuxing_power"] = build_wuxing_power(p, f)
    th = build_tian_he(p, f)
    hst = {p[k][1]: f["hidden_stems"][k] for k in _POS}

    # 根分类单一数据源(补 production_entry.py L200-213 覆盖, 2026-10):
    #   l0_fact_builder L118-141 的 rt 只认「日干同字」藏干(dg in HIDDEN[z]),
    #   判不出同五行根 -> PZ-0016 戊戌甲子己巳戊辰: 戌藏戊辛丁/辰藏戊乙癸皆无己 -> rt={} 空 dict,
    #   致 bingyao_layer L204-207 的 has_root/has_heavy_root 全 False, 与 L3 实测矛盾。
    #   改以 build_root_classes(同五行+十二长生) 为唯一来源, 与 production_entry 一致。
    # 依据(准神 STATE.WANG_SHUAI.GEN_QI.001, 依 DTS 原句「水至巳有庚金为水之根, 火至亥有木为火之根」
    #   「乙木死亥, 亥中有壬水, 乃其嫡母, 何为死哉」): 支中藏同五行即根, 不限是否四库。
    #   旁参 STATE.WANG_SHUAI.DE_DI.003(PZZQ 行201)「长生禄旺, 根之重者也; 墓库余气, 根之轻者也」
    #   「乙逢戌、丁逢丑, 不作此论, 以戌中无藏木, 丑中无藏火也」
    #   -> 同字之外仍须认同五行藏干; l0 旧 rt 违反「不作此论」句。
    # 影响面(tools/rwcf_impact.py 实测 PZZQ 319): 逐支 class 有差异 306 条;
    #   重根新增 48 条 / 重根丢失 27 条 / 覆盖前空 dict 65 条 -> 覆盖后全 NONE 22 条。
    #   27 条「重根丢失」是口径收紧(新口径只有禄/刃/帝旺/四库本气算 HEAVY, 同类藏干一律 LIGHT),
    #   非缺陷 —— 与 DE_DI.003「墓库余气根之轻」「得三比肩不如得一长生禄刃」一致。
    # 归一化后 bingyao_layer 只读 class 三值(HEAVY/LIGHT/NONE), 细标签不可见, 故不构成口径冲突。
    # (覆盖落在 L3 段 rc 生成之后, 见下)

    # L3 旺衰层(引擎只给 ling_state + root_grade, 不给身强身弱终判)
    pa = build_power_structure(p)
    rc = build_root_classes(p, hst)

    # 根分类单一数据源(补 production_entry.py L200-213 覆盖, 2026-10):
    #   l0_fact_builder L118-141 的 rt 只认「日干同字」藏干(dg in HIDDEN[z]),
    #   判不出同五行根 -> PZ-0016 戊戌甲子己巳戊辰: 戌藏戊辛丁/辰藏戊乙癸皆无己 -> rt={} 空 dict,
    #   致 bingyao_layer L204-207 的 has_root/has_heavy_root 全 False, 与 L3 实测矛盾。
    #   改以 build_root_classes(同五行+十二长生) 为唯一来源, 与 production_entry 一致。
    # 依据(准神 STATE.WANG_SHUAI.GEN_QI.001, 依 DTS 原句「水至巳有庚金为水之根, 火至亥有木为火之根」
    #   「乙木死亥, 亥中有壬水, 乃其嫡母, 何为死哉」): 支中藏同五行即根, 不限是否四库。
    #   旁参 STATE.WANG_SHUAI.DE_DI.003(PZZQ 行201)「长生禄旺, 根之重者也; 墓库余气, 根之轻者也」
    #   「乙逢戌、丁逢丑, 不作此论, 以戌中无藏木, 丑中无藏火也」
    #   -> 同字之外仍须认同五行藏干; l0 旧 rt 违反「不作此论」句。
    # 影响面(tools/rwcf_impact.py 实测 PZZQ 319): 逐支 class 有差异 306 条;
    #   重根新增 48 条 / 重根丢失 27 条 / 覆盖前空 dict 65 条 -> 覆盖后全 NONE 22 条。
    #   27 条「重根丢失」是口径收紧(新口径只有禄/刃/帝旺/四库本气算 HEAVY, 同类藏干一律 LIGHT),
    #   非缺陷 —— 与 DE_DI.003「墓库余气根之轻」「得三比肩不如得一长生禄刃」一致。
    # 归一化后 bingyao_layer 只读 class 三值(HEAVY/LIGHT/NONE), 细标签不可见, 故不构成口径冲突。
    def _norm_root_class(rcv):
        if rcv.startswith("HEAVY"):
            return "HEAVY"
        if rcv.startswith("LIGHT") or rcv == "SPECIAL_LONGSHENG_YIN":
            return "LIGHT"
        return "NONE"

    f["root_weight_class_facts"] = {
        pos: {"branch": p[pos][1],
              "class": _norm_root_class(rc["per_pillar"][pos]["root_class"])}
        for pos in _POS}

    tc = build_tou_cang(f)
    wx = build_wang_xiang(f, f["day_stem"])
    rr = build_root_relations(rc, f["combination_facts"])
    f["root_relations"] = rr   # STEP-L5-1 (2026-10): 根气关系(含合解冲裁决)挂回 facts 供下游消费
    ts = build_two_side(rc, tc, rr)
    bt = build_branch_tiers(p, f)
    net = build_power_network(pa, rc, tc, wx, rr, ts,
                              branch_tier=bt, tian_he=th, facts=f)
    queries = run_queries(net)

    # L3 旺衰结构层(党众/助寡 = DE_SHI.001「强众而敌寡/强寡而敌众」的计数基础)
    # 只输出多维结构事实, 不输出综合裁决(DTS SHUAI.001「旺中有衰/衰中有旺」)。
    root_eff = filter_root_effectiveness(rc, f["combination_facts"], p, f["day_stem"])
    f["root_effectiveness"] = root_eff   # STEP-L5-2 (2026-10): 根效力事实挂回 facts
    structure = build_wangshuai_structure(f, root_eff, rc)

    # L4 格局层
    special = build_special_patterns(p, f, f.get("wuxing_power"), th)
    f["special"] = special   # PATCH-GAP11d: 单一数据源, 供 ge_jie_layer 读, 免其内部重算
    build_ge_cheng(f)
    # STEP-2.4b (2026-10) 接上「规则2 冲解合破格」执行器。
    #   apply_he_po_ge 此前从未接线(全仓 0 调用), 是 po_ge 24 处声明无执行器的根因。
    #   必须在 build_ge_cheng 之后: 它要读 ge_cheng 的 ti_wx/xi_wx 才能判破格;
    #   而 special_pattern 不读这两个字段(已 grep 确认 0 命中), 故接入点唯一。
    #   口径见《架构层规范》§7.2「破格清空 ti_wx/xi_wx 应影响 P1, P1 读到空值是设计预期」——
    #   bingyao_layer.py:570 既有注释即同一口径("破格时格局层同时清空ti_wx/xi_wx(同失效)")。
    #   破格后 P1 两道过滤走 if _ti_wx:/if _xi_wx: 假分支, 整段不执行 = 不否决病机。
    #   原典 DT-0380 卯酉冲破亥卯未印局=凶; PZ-0034/PZ-0279 冲而月令五行不在
    #   格体/喜神内, 条件不成立, 不破(前置验证已实测确认)。
    apply_he_po_ge(f)
    # STEP-DBG-4 (2026-10-03) ti_wx 规则归位 —— 必须接在 apply_he_po_ge 【之后】。
    #   apply_he_po_ge 的判据读 ti_wx(『月令五行 ∈ ti_wx∪xi_wx 且月令被冲 -> 破格清空』),
    #   归位把月令五行填进 ti_wx, 顺序反了会给破格执行器喂新输入 -> 多 125 盘误判破格。
    #   顺序: build_ge_cheng -> apply_he_po_ge(破格清空) -> normalize_ti_wx(归位)。
    #   规则见 ge_jie_layer.normalize_ti_wx 上方注释(DTS L210 准神 + PZZQ L4652 同向)。
    normalize_ti_wx(f)
    ge_cheng = f.get("ge_cheng") or {}

    # C 块 · 格局救应字段 (jiu_ying): 附加信息, 不回填 cheng_bai (裁146乙)
    #   149甲/150甲/151甲 精确化接线: .001通关/.004澄浊/.005八格10子型
    #   纯函数入参映射: po_ge(破格条件列表) -> po_n(有破格需求); xi_wx_status -> xi_status
    try:
        from p0_v2.jiu_ying import build_jiu_ying
        f["jiu_ying"] = build_jiu_ying(bz, {
            "ge": ge_cheng.get("ge"),
            "po_n": 1 if ge_cheng.get("po_ge") else 0,
            "xi_status": ge_cheng.get("xi_wx_status"),
            "cong_type": ge_cheng.get("cong_type"),
        })
    except Exception:
        f["jiu_ying"] = None

    # ---- STEP-2.2 (2026-10) L3 契约字段(《架构层规范》§2.5 五字段) ----
    #   纯新增输出, 不改任何既有值; comprehensive_verdict 保持 NOT_AUTHORIZED 不动。
    #   五个字段此前或从未产出, 或只在 special_pattern 内部私产, 从未进 facts 输出 ——
    #   实跑确认 facts 里 dm_ben_eff/root_grade/support_state/strength_verdict 全缺。
    #   dm_ben_eff / yin_ben_eff: 已在 special['dm_ben_eff'] 里算好(含孤根被冲拔 T30
    #     与合局化去根两层修正, L120-121), 此处只做契约位提升, 【不在本层重造】。
    #   root_grade: 由 L0 root_weight_class_facts 归一为 无/余/中/本 四档(离散枚举)。
    #   support_state: 同党 vs 异党 计数对比, 离散枚举, 不评分。
    #   strength_verdict: §2.5 要求「按 DTS 方向输出, 不做单极裁决」——
    #     但本引擎 Strength Resolver 明确 NOT_AUTHORIZED, 故此处【不出结论】,
    #     只落 NOT_AUTHORIZED + 依据, 与 structure.comprehensive_verdict 口径一致。
    #     不臆造强/弱, 不引浮点。
    _wpd = (f.get("wuxing_power") or {}).get("wuxing_power", {}) or {}
    _dmwx = f.get("daymaster_element", "")
    _dmp = _wpd.get(_dmwx, {}) or {}
    _yinwx = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}.get(_dmwx, "")
    _yinp = _wpd.get(_yinwx, {}) or {}
    # ★ 裁四十九甲 (2026-10-03) 冲激字段取值行修正 —— 契约与实现口径对齐
    #   错位根因: transit_power.py L269 `if wx == month_wx:` 只在【月令五行】行赋 5 冲激字段,
    #             而此处原用 _dmp(=_wpd[日主五行]) 读它们 -> 日主五行 != 月令五行的盘,
    #             5 字段恒 None(DT-0008 日主金/月令土 实测 5 字段全 None)。
    #   语义依据: 5 冲激字段判的是【月令受冲】(见 transit_power L267-L284),
    #             与日主五行无关 -> 必须从月令行取。
    #   保留 _dmp 供 ling_state 等日主相关字段使用, 两者分行不混用。
    _monthwx = f.get("month_qi_element", "") or (f.get("wuxing_power") or {}).get("month_element", "")
    _dmp_month = _wpd.get(_monthwx, {}) or {}
    # 只在月令行确实带冲激字段时才用; 月令行缺键 -> 显式 None, 不静默回落日主行。
    _CHONG_KEYS = ("chong_adjust", "chong_role", "chong_by",
    "library_open", "ling_state_eff")
    
    def _grade_of(cls_set):
        if not cls_set:
            return "无"
        if "HEAVY" in cls_set:
            return "本"
        if "LIGHT" in cls_set:
            return "余"
        return "无"

    # STEP-DBG-12 (2026-10-03) root_grade 两处真错修正 —— 旺衰层不得自相矛盾
    #   错1: _classes 收全盘四柱 class, 【不分日主五行】。
    #        DT-0044 壬午己酉甲申甲子(日主甲木) 四柱 class={NONE,NONE,NONE,LIGHT},
    #        「子」中癸水与甲木无关却被算入 -> root_grade='余',
    #        而 dm_ben_eff=0(甲木四支无根)。L0 root_weight_class_facts 未标五行归属,
    #        此处按日主五行自查各柱藏干, 只收含日主五行的柱。
    #   错2: root_grade 只看根级别(HEAVY/LIGHT), 【不跟随 dm_ben_eff 的拔根修正】。
    #        DT-0029 甲申甲戌甲寅甲戌: 寅为甲木之禄(class=HEAVY) 但寅被申冲,
    #        DTS L110「子旺午衰, 冲则午拔不能立」+ L139「主衰逢冲, 则根拔而祸更甚」
    #        -> dm_ben_eff=0(根已拔, 正确), 而 root_grade='本' —— 同一数据两个结论。
    #   修法: root_grade 定为【有效根级别】, 跟随 dm_ben_eff 修正;
    #        同时保留 root_grade_raw(原始根级别)备查, 不丢原值。
    #   全部整数/枚举比较, 无浮点。
    _CANG = {"子": ["癸"], "丑": ["己", "辛", "癸"], "寅": ["甲", "丙", "戊"],
             "卯": ["乙"], "辰": ["戊", "乙", "癸"], "巳": ["丙", "戊", "庚"],
             "午": ["丁", "己"], "未": ["己", "丁", "乙"], "申": ["庚", "壬", "戊"],
             "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"]}
    _GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
               "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
    _rwc = f.get("root_weight_class_facts") or {}
    _classes = set()
    for _pos, _v in _rwc.items():
        _bz = (_v or {}).get("branch")
        _cls = (_v or {}).get("class")
        if _cls not in ("HEAVY", "LIGHT"):
            continue
        # 只收【含日主五行】的柱
        if any(_GAN_WX.get(_g) == _dmwx for _g in _CANG.get(_bz, ())):
            _classes.add(_cls)
    _root_grade_raw = _grade_of(_classes)
    _dm_ben_eff0 = int(special.get("dm_ben_eff", 0) or 0)
    _root_grade = "无" if _dm_ben_eff0 <= 0 else _root_grade_raw

    # 同党 = 日主五行 + 生我(印); 异党 = 克泄耗三向
    _sheng_back = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}
    _sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    _ke = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}

    def _mass(wx):
        if not wx or wx not in _wpd:
            return 0
        _v = _wpd[wx] or {}
        return (int(_v.get("ben_n", 0) or 0) + int(_v.get("zhong_n", 0) or 0)
                + int(_v.get("yu_n", 0) or 0) + int(_v.get("stem_n", 0) or 0))

    _tong_party = _mass(_dmwx) + _mass(_sheng_back.get(_dmwx, ""))
    _yi_party = _mass(_sheng.get(_dmwx, "")) + _mass(_ke.get(_dmwx, ""))
    _support_state = ("SHENG_FU_CHENG_SHI" if _tong_party > _yi_party
                      else ("KE_XIE_CHENG_SHI" if _yi_party > _tong_party
                            else "PINGHENG"))

    # STEP-DBG-13 (2026-10-03) 反局层接入 L3 (DTS 准神「### 十七、反局」)
    #   切片 STATE.WANG_SHUAI.FAN_JU.001~004 已建已校验, 引擎此前零实现,
    #   而 P1「印多埋子」引 DTS L445「君赖臣生」为 primary —— 依据悬空。
    #   反局是旺衰结构判断(切片前缀 STATE_* 即归旺衰层), 不是格名也不是病,
    #   故接 L3, 不改既有字段, 只新增维度。判据全整数/枚举, 无浮点。
    _fan_ju = resolve_fan_ju(f)

    f["l3_contract"] = {
        "dm_ben_eff": int(special.get("dm_ben_eff", 0) or 0),
        "yin_ben_eff": int(special.get("yin_ben_eff", 0) or 0),
        "ling_state": _dmp.get("ling_state", ""),
        "root_grade": _root_grade,
        "root_grade_raw": _root_grade_raw,
        "support_state": _support_state,
        # ★ PATCH-L3-02 (2026-10-05) 枚举判据落码 —— 裁丙(dict 结构版)
        #   契约: p0_v2/l3_contract_spec.md v1.11 §2.6.6
        #   ★ 为什么是 dict 不是裸字符串:
        #     §2.6.6 实测(301盘): 用 support_state/de_ling/de_di 任何组合
        #     做输入, 对案例断语(身旺/身弱)的二元切分准确率 = 73.6%
        #     = 多数类基线, 提升 0.0 个百分点 —— 输入不含信息。
        #     裸字符串 "STRONG" 会让下游写 == 'STRONG' 时以为它是预测性判定。
        #     dict 结构使裸比较恒 False → 运行时防误用, 不靠读文档。
        #   ★ predictive=False 是本字段的实测属性, 不是免责声明:
        #     它是【规则输出】, 不是【事实度量】。L4 要判定仍须自己合。
        #   ★ value 三态(裁丙):
        #     None       三档映射未落 —— 键在, 值不出
        #     "STRONG"/"WEAK"/"EXTREME_WEAK"  映射已落但仍 predictive=False
        #     恒不出 "EXTREME_STRONG"(§2.4 已否决, 三源语义冲突)
        "strength_verdict": {
            "value": None,
            "status": "ENGINE_DEFINED",
            "predictive": False,
            "basis": "L110 相对比较 + L235 方向 + L245 取最多最旺; 阈值 ENGINE_DEFINED",
        },
        # ★ PATCH-L3-01 (2026-10-03) L3 契约补 5 冲激字段
        #   契约: p0_v2/l3_contract_spec.md v1.0 §1 字段 6~10
        #   值【直取 _dmp_month】(wuxing_power[月令五行]) —— 不是从 six_dims 复制。
        #   零复制: six_dims 与 l3_contract 同读 wuxing_power, 是两个出口同源, 不是两份数据。
        #   ★ §1.3 硬约束: 此 5 字段【仅月令五行行有值】(transit_power.py:269
        #     `if wx == month_wx:` 条件块内赋值)。
        #     裁四十九甲(2026-10-03) 修正: 改从【月令行】_dmp_month 取 ——
        #     原从 _dmp(日主行)取, 致日主五行!=月令五行的盘 5 字段恒 None(DT-0008 实测)。
        #   ★ 裁四十九甲: 5 字段统一改从【月令行】取(语义是「月令受冲」, 与日主五行无关)。
        "chong_adjust": _dmp_month.get("chong_adjust"),
        "chong_role": _dmp_month.get("chong_role"),
        "chong_by": _dmp_month.get("chong_by"),
        "library_open": _dmp_month.get("library_open"),
        # 合成字段 role=COMPOSITE, 合成式见契约 §1.2:
        #   if _adj:                                   → CHONG_BA / CHONG_FA
        #   elif role=='BROTHER_CHONG' and library_open: → KU_KAI
        #   else:                                        → ling_state 原值
        # ★ chong_adjust 值域严格 {-1,0,+1}; 越界 = 契约违反, 下游应断言不得静默
        "ling_state_eff": _dmp_month.get("ling_state_eff"),
        # ★ PATCH-L3-02 (2026-10-03) 第1刀 布尔补齐
        #   契约: p0_v2/l3_contract_spec.md v1.1 §1 字段 11~13
        #   三个布尔, 值域严格 {True, False}, 由已有判据投影, 不新增判据。
        #   de_ling  : (ling_state == '旺')          DTS L225「气象得令者吉」
        #   de_di    : (dm_ben_eff >= 1)              DTS L119「有根无根」+ L9「根拔」
        #   dang_duo : (support_state == 同党成势)    DTS L280/L604「党多/党少」
        #   ★ de_di 与 root_grade 的关系(见契约 §1.5):
        #     root_grade == '无'  当且仅当  dm_ben_eff == 0
        #     root_grade 是 dm_ben_eff 的【门控派生】(L240: "无" if dm_ben_eff0<=0 else raw)
        #     故 de_di 是 dm_ben_eff 的布尔投影, 【不是】root_grade 的。
        #     实测 2106 盘: de_di_raw(de_di) 与 de_di_eff 完全恒等, 零差异 -> 落一个不落两个。
        "de_ling": _dmp.get("ling_state") == "旺",
        "de_di": int(special.get("dm_ben_eff", 0) or 0) >= 1,
        "dang_duo": _support_state == "SHENG_FU_CHENG_SHI",
        "fan_ju": {
            "types": _fan_ju.get("types", []),
            "count": _fan_ju.get("count", 0),
            "state": _fan_ju.get("state"),
            "detail": _fan_ju.get("detail", []),
            "role_map": _fan_ju.get("role_map", {}),
            "power_map": _fan_ju.get("power_map", {}),
            "flag_map": _fan_ju.get("flag_map", {}),
            "boundary_note": _fan_ju.get("boundary_note"),
        },
        "boundary_note": ("§2.5 L3 契约位。dm_ben_eff 含孤根被冲拔/合局化根修正, 由 "
                          "special_pattern 计算后提升, 不在本层重算; root_grade 由 L0 "
                          "root_weight_class_facts 归一为无/余/本; support_state 为"
                          "同党异党离散计数对比; strength_verdict 本引擎 "
                          "Strength Resolver NOT_AUTHORIZED, 不出强/弱结论, 与 "
                          "structure.comprehensive_verdict 口径一致; 全部整数/枚举, 无浮点。"),
        "evidence_refs": ["ARCH v1.0 §2.5", "DTS L442-L451 反局章",
                          "STATE.WANG_SHUAI.FAN_JU.001~004"],
    }

    # P1 病药 / 消解 / 用神
    by = build_bingyao_layer(f, queries)
    debate = resolve_primary_bing(f, by.get("bing_list") or [])
    zg = resolve_zhuangui(f, debate)
    cli = build_climate_candidates(f)
    yy = resolve_yongyao(f, debate, cli)

    dm = f["day_stem"]
    # STEP-2.3 (2026-10): daymaster_element 改为读 L0 契约, 不再绕道 wuxing_power 顶层。
    #   改前: f["wuxing_power"].get("daymaster_element", "")
    #   改后: f.get("daymaster_element", "")
    #   依据《架构层规范》§2.2「L0 是唯一源, 任何字段下游只读」+ §2.3 L1 契约
    #   —— wuxing_power 契约内只有五行 {ling_state/ben_n/zhong_n/yu_n/ju_n/
    #   banhe_n/stem_n/root_detail}, daymaster_element 是 wuxing_power.py L16
    #   为兼容旧接口补的额外键, 不在 L1 契约内(记一笔: L1 契约外泄)。
    #   值等价: l0_fact_builder L188 与 wuxing_power.py L16 同用 WUXING[日干],
    #   8 盘实跑逐盘一致, 纯重构零副作用。
    #   注: daymaster_root_class.build_root_classes 也输出同名字段,
    #   但其签名只有 (pillars, hidden_stems_table), 无 facts 入参, 属接口自包含,
    #   非重复实现, 本 step 不动(潜在不一致源, 归 §7 缺口 1)。

    # ★ 裁七十一乙 (2026-10-04) 拓扑派生层装配函数
    #   核验(2026-10-04): 4 块全部不依赖 L4 —— xi_wx 只出现在注释与 endpoint_pending
    #   标记里, 不是真依赖; 入参 relations(L0)/pan_zhi(四柱)/mass(L1)/pos_of(四柱) 全部现成。
    def _build_topology(facts, pillars):
        rels = facts.get("relations") or []
        zhis = [pillars[k][1] for k in _POS]          # 四柱地支, 标准柱序
        # mass 用引擎口径四项(ben+zhong+yu+stem) —— 与 L1 wuxing_power 同源, 不重算
        _mass = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        _wpd_t = (facts.get("wuxing_power") or {}).get("wuxing_power", {}) or {}
        for _wx, _row in _wpd_t.items():
            _mass[_wx] = (int(_row.get("ben_n", 0) or 0)
                          + int(_row.get("zhong_n", 0) or 0)
                          + int(_row.get("yu_n", 0) or 0)
                          + int(_row.get("stem_n", 0) or 0))
        # pos_of: 支名 -> 柱位列表(重复支盘一视同仁)
        _pos_of = {}
        for _pos, _v in pillars.items():
            _pos_of.setdefault(_v[1], []).append(_pos)
        return {
            "yuan_liu": build_yuan_liu_skeleton(_mass),
            "fang_ju": check_fang_ju_ming_same_wx(rels, zhis),
            "tong_guan": {
                "rules": [{"guan": m["guan"], "tong": m["tong"],
                           "trigger": m["trigger"], "inert": bool(m.get("inert")),
                           "evidence": m["evidence"], "line": m["line"]}
                          for m in TONG_GUAN_MAP],
                "note": "前三组相克成关可触发; 第四组金水不相克 inert(见契约 §4.4)",
            },
            "guan_topo": check_guan_topology(rels, zhis[0], zhis[2], _pos_of),
            "boundary_note": ("派生层(L0+L1 的确定性派生), 不塞 L0~L4 任何一层。"
                              "源流读 mass(L1), 方局/通关/关拓扑读 relations(L0)。"
                              "★ 不放 raw_facts —— 会让 L0 输出依赖 L1 输出, 层次倒挂。"),
        }

    dm_wx = f.get("daymaster_element", "") or (f["wuxing_power"].get("daymaster_element", ""))
    dmd = (f["wuxing_power"].get("wuxing_power", {}) or {}).get(dm_wx, {}) or {}

    return {
        "bazi": bz,
        "pillars": p,
        "day_stem": dm,
        "daymaster_element": dm_wx,
        "month_qi_element": f.get("month_qi_element", ""),
        "month_qi_ten_god": f.get("month_qi_ten_god", ""),
        # L0 L90 已算 month_branch, 但投影未带出 -> 下游读 None,
        # 离散拓扑/结构匹配缺第一个节点输入(架构层 §2.2 L0 契约字段)。
        "month_branch": f.get("month_branch", ""),
        # 十神/藏干 —— 引擎算的, 禁止手写替代
        "ten_god": {k: {p[k][0]: ten_god(dm, p[k][0])} for k in _POS},
        "hidden": {k: f["hidden_stems"][k] for k in _POS},
        "wuxing_power": f["wuxing_power"].get("wuxing_power", {}),
        "daymaster_power": {k: dmd.get(k) for k in
                            ("ling_state", "ben_n", "zhong_n", "yu_n",
                             "ju_n", "banhe_n", "stem_n", "root_detail")},
        "root_weight_class": f.get("root_weight_class_facts", {}),
        "l3_contract": f.get("l3_contract", {}),
        # ★ 裁七十一乙 (2026-10-04) 拓扑派生层 —— 与 l3_contract 平级, 不塞 L0~L4
        #   语义: L0(relations) + L1(wuxing_power) 的确定性派生, 无判定无阈值。
        "topology": _build_topology(f, p),
        "combination_facts": f.get("combination_facts", {}),
        # STEP-L0-1 (2026-10): L0 冲合互动裁决块独立顶层投影。
        #   原本嵌在 combination_facts.resolved(已算: chong_actions 733/2106,
        #   chong_active/canceled/survive/liuhe_canceled/xinghe 等), 顶层无独立键,
        #   下游(格局/病药/域裁决)无处消费 → 「有输出不投影」实锤修复。
        #   只补投影, 不改 combination_facts 任何计算。
        "resolved": (f.get("combination_facts") or {}).get("resolved"),
        "root_relations": f.get("root_relations"),          # STEP-L5-3 投影(算而未投影实锤修复)
        "root_effectiveness": f.get("root_effectiveness"),  # STEP-L5-3 投影
        "stem_combination_facts": f.get("stem_combination_facts", {}),
        "tian_he": th,
        "power_queries": queries,
        "structure": structure,
        "ge_cheng": ge_cheng,
        "jiu_ying": f.get("jiu_ying"),   # C 块格局救应(149/150/151, 附加不回填)
        "special": {k: special.get(k) for k in
                    ("cong_type", "cong_state", "zhuanwang", "zhuanwang_state",
                     "hua_qi", "hua_qi_state", "liangqi", "mu_mie",
                     # ★ PATCH-L4-01 (2026-10-05, 裁九十八甲) patterns 必须出口。
                     #   ge_jie_layer._special_of L110 的判据是 spv.get('patterns') is not None;
                     #   白名单缺 patterns → 该判据恒 False → 复用分支永不命中,
                     #   每盘 build_special_patterns 被重算两遍, PATCH-GAP11d 完全失效,
                     #   且 L902 从格证据链 _cong_pat 恒为 None（判定无出处）。
                     #   patterns 是唯一带 note + facts 的证据链载体 → COMPUTED。
                     #   ★ 只加 patterns: judgment_status / mu_mie_state 生产消费者 0,
                     #     加了徒增顶层键数与回归面（裁九十八甲）。
                     "patterns")},
        "bing_list": by.get("bing_list", []),
        "bing_yao": {"bing_count": by.get("bing_count"),
                     "yao_count": by.get("yao_count"),
                     "boundary_note": by.get("boundary_note")},
        "bing_debate": {"state": debate.get("state"),
                        "primary": (debate.get("primary_bing") or {}).get("bing_id"),
                        "primary_detail": debate.get("primary_bing"),
                        "secondary": debate.get("secondary_bing"),
                        "domain_primaries": debate.get("domain_primaries"),
                        "ranked": debate.get("ranked"),
                        "compare_key": debate.get("compare_key")},
        "zhuangui": zg,
        "climate": cli,
        # STEP-DBG-11 (2026-10-03) 用神层投影补全 (GAP-7)
        #   yongyao_resolve 内部【已算好】all_edges / auxiliary_medicine /
        #   medicine_blocked 三项, 但顶层只投影 primary/ji_shen 两个键,
        #   导致离散三边拓扑与安全检查结果全丢 —— 「有输出不投影」。
        #   本次只补投影, 不改 yongyao_resolve 任何计算; primary/ji_shen 原样保留。
        #   注: 三键在无主病盘为 None(上游本就返回空 / NO_BING), 属正常。
        "yongyao": {"primary": (yy.get("primary_medicine") or {}).get("wuxing", ""),
                    "ji_shen": yy.get("ji_shen", []),
                    "all_edges": yy.get("all_edges"),
                    "auxiliary_medicine": yy.get("auxiliary_medicine"),
                    "medicine_blocked": yy.get("medicine_blocked"),
                    "rejected_climate": yy.get("rejected_climate"),
                    "rule": yy.get("rule"),
                    "evidence_refs": yy.get("evidence_refs")},
        # ★ PATCH-L3-03 (2026-10-03) 旺衰矩阵投影 (six_dims 已废弃)
        #   L1 数据出口: dm_row(日主整行) / yin_row(印行) / by_element(五行全表)
        #   L3 判定出口: l3_contract (13 字段, 契约见 p0_v2/l3_contract_spec.md v1.1)
        #   ★ 原 six_dims 块与「旺衰六维矩阵」note 已删:
        #     - 8 个 L1 字段经核与 by_element[日主] 完全恒等(2106x8=16848 次 diff=0), 是纯副本
        #     - 5 个冲激字段已迁入 l3_contract(PATCH-L3-01), 值直取 _dmp 非复制
        #     - note 的「六维」定义经原典核验不作准(DTS 不按维度组织文本, 见契约 §〇),
        #       且已无消费者(wangshuai_matrix.note 零引用)
        "wangshuai_matrix": {
            "daymaster_element": _dmwx,
            "month_element": (f.get("wuxing_power") or {}).get("month_element", ""),
            "month_qi_ling_state": _dmp.get("ling_state"),
            "fan_ju": _fan_ju,
            "dm_row": _dmp,
            "yin_row": _yinp,
            "by_element": _wpd,
            # 月令冲激全貌(含未被日主五行覆盖的部分)
            # ★ STEP-DBG-14 branch_chong: 四支各自的受冲处境(柱位维度)
            "branch_chong": (f.get("wuxing_power") or {}).get("branch_chong"),
            "month_chong": {
                "month_branch": (f.get("wuxing_power") or {}).get("month_branch"),
                "month_pos": ((f.get("wuxing_power") or {}).get("branch_chong") or {}).get("month"),
            },
        },
        "raw_facts": f,
    }


def walk_layers(bazi: str) -> List[Dict[str, Any]]:
    """逐层走 L0→L7, 返回每层出口或异常。用于定位断点层。"""
    out: List[Dict[str, Any]] = []

    def rec(layer, fn):
        try:
            out.append({"layer": layer, "ok": True, "out": fn()})
        except Exception as e:
            out.append({"layer": layer, "ok": False,
                        "err": type(e).__name__, "msg": str(e)[:120]})

    def _p():
        bz = "".join(str(bazi).split())
        p = _pillars(bz)
        f = _l0build(p)
        f["pillars"] = p
        f["wuxing_power"] = build_wuxing_power(p, f)
        th = build_tian_he(p, f)
        return p, f, th

    state = {}

    def s0():
        state["p"], state["f"], state["th"] = _p()
        return {"n_facts": len(state["f"])}
    rec("L0_facts", s0)
    if not out[-1]["ok"]:
        return out

    def s3():
        p, f, th = state["p"], state["f"], state["th"]
        hst = {p[k][1]: f["hidden_stems"][k] for k in _POS}
        net = build_power_network(
            build_power_structure(p), build_root_classes(p, hst),
            build_tou_cang(f), build_wang_xiang(f, f["day_stem"]),
            build_root_relations(build_root_classes(p, hst), f["combination_facts"]),
            build_two_side(build_root_classes(p, hst), build_tou_cang(f), {}),
            branch_tier=build_branch_tiers(p, f), tian_he=th, facts=f)
        state["queries"] = run_queries(net)
        return {"n_query": len(state["queries"])}
    rec("L3_wangshuai", s3)
    if not out[-1]["ok"]:
        return out

    def s4a():
        state["special"] = build_special_patterns(
            state["p"], state["f"], state["f"].get("wuxing_power"), state["th"])
        return {"cong": state["special"].get("cong_type")}
    rec("L4_special", s4a)
    if not out[-1]["ok"]:
        return out

    def s4b():
        build_ge_cheng(state["f"])
        state["ge"] = state["f"].get("ge_cheng") or {}
        return {"ge": state["ge"].get("ge")}
    rec("L4_geju", s4b)
    if not out[-1]["ok"]:
        return out

    def s5():
        state["by"] = build_bingyao_layer(state["f"], state["queries"])
        return {"n_bing": state["by"].get("bing_count", 0)}
    rec("P1_bingyao", s5)
    if not out[-1]["ok"]:
        return out

    def s6():
        state["debate"] = resolve_primary_bing(
            state["f"], state["by"].get("bing_list") or [])
        return {"state": state["debate"].get("state")}
    rec("P1_bingdebat", s6)
    if not out[-1]["ok"]:
        return out

    def s7():
        state["zg"] = resolve_zhuangui(state["f"], state["debate"])
        state["cli"] = build_climate_candidates(state["f"])
        state["yy"] = resolve_yongyao(state["f"], state["debate"], state["cli"])
        return {"primary": (state["yy"].get("primary_medicine") or {}).get("wuxing", "")}
    rec("P1_yongyao", s7)
    return out


def _pillars(bz: str) -> Dict[str, List[str]]:
    return {k: [bz[i], bz[i + 1]] for i, k in zip((0, 2, 4, 6), _POS)}


# ==================== ② 切片 ====================

_SLICE_CACHE: Dict[str, Dict[str, Any]] = {}


def load_slices(subdir: str = "") -> List[Dict[str, Any]]:
    """读全部 MD 切片(或某子目录), 解析头部字段。"""
    base = os.path.join(SLICE_LIB, subdir) if subdir else SLICE_LIB
    out = []
    for root, _dirs, files in os.walk(base):
        for fn in sorted(files):
            if not fn.endswith(".md") or fn.startswith("_"):
                continue
            out.append(_parse_slice(os.path.join(root, fn)))
    return out


def _parse_slice(path: str) -> Dict[str, Any]:
    key = os.path.abspath(path)
    if key in _SLICE_CACHE:
        return _SLICE_CACHE[key]
    txt = open(path, encoding="utf-8", errors="replace").read()
    head = {}
    for m in re.finditer(r"^>\s*\*\*([^*]+)\*\*[：:]\s*(.+?)\s*$", txt, re.M):
        head[m.group(1).strip()] = m.group(2).strip()
    body = txt.split("## 原文", 1)[-1].split("## 语义解析", 1)[0] if "## 原文" in txt else ""
    rec = {
        "file": os.path.relpath(path, SLICE_LIB).replace("\\", "/"),
        "切片ID": head.get("切片ID", ""),
        "来源": head.get("来源", ""),
        "版本": head.get("版本", ""),
        "行号": head.get("页码/行号", ""),
        "Category": head.get("G1-A Category", ""),
        "切片类型": head.get("切片类型", ""),
        "准神归属": head.get("准神归属", ""),      # 准 / 旁参 / 被DTS否决
        "适用范围": head.get("适用范围", ""),
        "校验状态": head.get("校验状态", ""),
        "原文": body.strip(),
        "path": path,
    }
    _SLICE_CACHE[key] = rec
    return rec


def read_slice(slice_id_or_kw: str) -> List[Dict[str, Any]]:
    """按切片ID或关键词查切片。改判据前必查 —— 确认准神归属。

    查法优先级: 切片ID精确 → 切片ID包含 → 标题/原文/来源含关键词。
    (切片ID是英文如 STRUCTURE.GE_JU.HUA_GE.001, 中文关键词走第三种)
    """
    kw = str(slice_id_or_kw).strip()
    if not kw:
        return []
    allsl = load_slices()
    exact = [s for s in allsl if s["切片ID"] == kw]
    if exact:
        return exact
    part = [s for s in allsl if kw in s["切片ID"]]
    if part:
        return part
    # 内容搜: 文件名 / 标题行 / 原文 / 来源
    hit = []
    for s in allsl:
        title = ""
        try:
            first = open(s["path"], encoding="utf-8", errors="replace").readline()
            title = first.lstrip("# ").strip()
        except Exception:
            pass
        if (kw in s["file"] or kw in title or kw in s["原文"]
                or kw in s["来源"] or kw in s["适用范围"]):
            hit.append(s)
    return hit


def slice_authority(slice_id: str) -> Dict[str, Any]:
    """取某切片的准神归属(v1.8 §1.3 三档: 准/旁参/被DTS否决)。

    改判据前必调。返回 authority=primary/support/vetoed。
    """
    s = read_slice(slice_id)
    if not s:
        return {"found": False, "slice_id": slice_id}
    a = s[0]["准神归属"]
    m = {"准": "primary", "旁参": "support", "被DTS否决": "vetoed"}
    return {
        "found": True,
        "slice_id": s[0]["切片ID"],
        "准神归属": a,
        "authority": m.get(a, "?"),
        "文件": s[0]["file"],
        "来源": s[0]["来源"],
        "依据1": s[0]["原文"][:120].replace("\n", " "),
    }


def read_slice_full(path_or_id: str) -> str:
    """取切片全文(含依据链/备注)。"""
    s = read_slice(path_or_id)
    if not s:
        return ""
    return open(s[0]["path"], encoding="utf-8", errors="replace").read()


# ==================== ③ 案例 ====================

def load_cases(book: str = "PZZQ") -> List[Dict[str, Any]]:
    """读某书案例库。pollution 字段必看 —— 旁证/增补不能当准神依据。"""
    p = os.path.join(CASE_DIR, "%s_clean.jsonl" % book.upper())
    if not os.path.exists(p):
        raise FileNotFoundError("无案例库: %s (可选 %s)" % (p, ", ".join(BOOKS)))
    return [json.loads(l) for l in open(p, encoding="utf-8-sig") if l.strip()]


# ==================== 纪律自检 ====================

def selfcheck() -> Dict[str, Any]:
    """接口自检: 确认引擎链路通、十神由引擎产出。"""
    r = paipan("癸酉丁巳己卯甲戌")
    return {
        "bazi": r["bazi"],
        "day_stem": r["day_stem"],
        "ten_god_hour": r["ten_god"]["hour"],       # 必须是引擎值
        "hidden_month": r["hidden"]["month"],
        "ling": r["daymaster_power"]["ling_state"],
        "ben": r["daymaster_power"]["ben_n"],
        "ge": r["ge_cheng"].get("ge"),
        "n_bing": r["bing_yao"]["bing_count"],
        "n_queries": len(r["power_queries"]),
        "n_slices": len(load_slices()),
        "n_cases_pzzq": len(load_cases("PZZQ")),
    }


if __name__ == "__main__":
    import json as _j
    print(_j.dumps(selfcheck(), ensure_ascii=False, indent=2))
