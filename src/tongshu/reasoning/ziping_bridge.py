"""ZIPING 辨层接线 — BAZI Chart → Judgment context → JudgmentFactory

架构位置 (V2 算→辨→解):
    BaziEngine.compute()  [算]
        ↓ BaziChart
    ZipingBridge.build_context()  [接线]
        ↓ NatalContext-dict
    JudgmentFactory.judge_all()  [辨]
        ↓ JudgmentSynthesis
    解层消费 (渲染/输出)

职责:
    1. 将 BaziChart 的四柱事实转换为 judgment.py 期望的 context 格式
    2. 调用 JudgmentFactory 生成五大域判断
    3. 返回 JudgmentSynthesis (含 rule_refs/evidence_refs 可追溯)

原则:
    - 只做数据转换，不做辨证判断 (BAZI 事实 → 判断层)
    - 确定性: 相同 BaziChart → 相同 judgment
    - Fail Closed: context 缺关键字段 → 返回 UNKNOWN，不强行判断
    - 不修改 BAZI 代码，只消费其字段
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .judgment import (
    DomainJudgment,
    JudgmentConclusion,
    JudgmentDomain,
    JudgmentFactory,
    JudgmentSynthesis,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _unknown(domain: JudgmentDomain, reasoning: str, evidence_refs=None) -> DomainJudgment:
    """fail-closed 单域判断: 明确给出未知原因, 不伪造结论。"""
    return DomainJudgment(
        domain=domain,
        conclusion=JudgmentConclusion.UNKNOWN,
        reasoning=reasoning,
        rule_refs=["ZIPING_ENGINES_P0"],
        evidence_refs=list(evidence_refs or []),
    )


def _pillars_from_chart(chart: Any) -> Dict[str, list]:
    """BaziChart → engines 生产入口要求的 canonical pillars dict。"""
    getter = getattr(chart, "get_pillars_chinese", None)
    if not callable(getter):
        raise ValueError("chart 缺 get_pillars_chinese()")
    pillars = getter()
    if not isinstance(pillars, dict):
        raise ValueError("get_pillars_chinese() 未返回 dict")
    out = {}
    for pos in ("year", "month", "day", "hour"):
        text = pillars.get(pos) or ""
        if len(text) != 2:
            raise ValueError(f"{pos} 柱缺干支")
        out[pos] = [text[0], text[1]]
    return out


def _rule_id(gc: Dict[str, Any]) -> str:
    """p0 规则码：`PZZQ255: 印格重…` → `PZZQ255`。"""
    text = str((gc.get("ge_evidence") or {}).get("rule_text") or "")
    return text.split(":", 1)[0].strip() if ":" in text else ""


def _ge_evidence_refs(gc: Dict[str, Any]) -> list:
    """ge_evidence 里的切片锚（zhun/zhu/pang/xiong）→ 已登记证据 ID。"""
    from . import p0_evidence

    gv = gc.get("ge_evidence") or {}
    refs = []
    for key in ("zhun", "zhu", "pang", "xiong"):
        refs.extend(list(gv.get(key) or []))
    return p0_evidence.resolve(refs)


_SHISHEN_ANCHOR = "FOUNDATION.RELATION.SHI_SHEN.001"
_WX_CAT_ORDER = ("比劫", "食伤", "财", "官杀", "印")


def _wx_category(wx: str, daymaster_wx: str) -> str:
    """五行 → 相对日主的十神大类（比劫/食伤/财/官杀/印）。"""
    from .ziping_classic_check import GEN, KE

    if not wx or not daymaster_wx:
        return ""
    if wx == daymaster_wx:
        return "比劫"
    if GEN.get(daymaster_wx) == wx:
        return "食伤"
    if KE.get(daymaster_wx) == wx:
        return "财"
    if KE.get(wx) == daymaster_wx:
        return "官杀"
    if GEN.get(wx) == daymaster_wx:
        return "印"
    return ""


def _shishen_from_facts(facts: Dict[str, Any], refs: list) -> DomainJudgment:
    """十神域: 以 wuxing_power 计最旺十神, 对照喜神/病神判吉凶(原典·论十神)。

    - 十神名以《三命通会》论十神（印食官财四纲）为锚 (FOUNDATION.RELATION.SHI_SHEN.001)；
    - 喜 = 用药五行 ∪ 格用神五行；忌 = 主病五行（且非喜）；
    - 最旺十神既非喜亦非忌 → UNKNOWN（不硬断吉凶）。
    """
    dm = facts.get("daymaster_element") or ""
    wp = (facts.get("wuxing_power") or {}).get("wuxing_power") or {}
    if not dm or not wp:
        return _unknown(JudgmentDomain.SHISHEN,
                        "缺日主五行或五行力量表, 十神强弱不可计", evidence_refs=refs)
    scores: Dict[str, float] = {}
    for wx, row in wp.items():
        if not isinstance(row, dict):
            continue
        scores[wx] = (2.0 * float(row.get("ben_n") or 0)
                      + 1.0 * float(row.get("zhong_n") or 0)
                      + 0.5 * float(row.get("yu_n") or 0)
                      + 1.0 * float(row.get("stem_n") or 0)
                      + 2.0 * float(row.get("ju_n") or 0)
                      + 1.0 * float(row.get("banhe_n") or 0))
    if not scores:
        return _unknown(JudgmentDomain.SHISHEN, "五行力量表为空", evidence_refs=refs)
    best_wx = max(scores, key=lambda w: (scores[w], w))
    cat = _wx_category(best_wx, dm)
    med = (((facts.get("__yongyao") or {}).get("primary_medicine")) or {}).get("wuxing")
    ge_yong = (facts.get("__ge_yong_wx") or "")
    bing = (((facts.get("__bing") or {}).get("primary_bing")) or {}).get("bing_wx")
    xi_set = {w for w in (med, ge_yong) if w}
    ji_set = {w for w in (bing,) if w and w not in xi_set}
    # 病反向推导（沈孝瞻配合论, 仅限「制」形明确的格用神类别）：
    #   用=食伤：
    #     · 日元太旺（旺衰 STRONG）→ 泄秀抑身，病=比劫（PZZQ L978/L986
    #       「日元太旺…用以泄日元之秀, 亦抑之之意」）；
    #     · 否则 → 所制之官杀为病（官多同煞/食伤制煞）。
    #   用=官杀（阳刃以官煞制刃 / 建禄透官同官格 / 财旺生官护财）→ 比劫为病。
    #   印/财/比劫类用神配合形态不唯一（化杀亦制食伤等），不反推，宁缺勿猜。
    _ge_yong_cat = _wx_category(ge_yong, dm) if ge_yong else ""
    from .ziping_classic_check import KE as _KE_BRIDGE

    _sha_wx = next((w for w, tgt in _KE_BRIDGE.items() if tgt == dm), "")  # 克我者=官杀
    _ws_concl = str(facts.get("__wangshuai") or "")
    if _ge_yong_cat == "食伤":
        if _ws_concl == "STRONG" and dm not in xi_set:
            ji_set.add(dm)  # 日元太旺泄秀 → 比劫为病
        elif _sha_wx and _sha_wx not in xi_set:
            ji_set.add(_sha_wx)  # 食伤制官杀 → 官杀为病
    elif _ge_yong_cat == "官杀" and dm not in xi_set:
        ji_set.add(dm)
    detail = (f"最旺十神: {cat}({best_wx}) 权重{scores[best_wx]:g}; "
              f"药={med or '-'} 格用神={ge_yong or '-'}({(_ge_yong_cat or '-')}), "
              f"病={sorted(ji_set) if ji_set else '-'}")
    if best_wx in xi_set:
        concl = JudgmentConclusion.SEMANTIC_POSITIVE
        why = f"{detail}; 最旺十神为用药/格用神五行 → 十神吉"
    elif best_wx in ji_set:
        concl = JudgmentConclusion.SEMANTIC_NEGATIVE
        why = f"{detail}; 最旺十神为病五行 → 十神凶(病神当权)"
    else:
        return _unknown(JudgmentDomain.SHISHEN,
                        f"{detail}; 最旺十神非喜非忌, 吉凶不硬断", evidence_refs=refs)
    refs2 = [r for r in refs if r] + [_SHISHEN_ANCHOR]
    return DomainJudgment(
        domain=JudgmentDomain.SHISHEN,
        conclusion=concl,
        reasoning=why,
        rule_refs=["ZIPING_ENGINES_P0", _SHISHEN_ANCHOR],
        evidence_refs=refs2,
    )


_SHIJIAN_ANCHORS = ("SUI_YUN.RE_EVALUATION.LIU_NIAN.005",
                    "SUI_YUN.RE_EVALUATION.DA_YUN_YIN_DONG.002")


_PINYIN_STEM = {"JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁", "WU": "戊",
                "JI": "己", "GENG": "庚", "XIN": "辛", "REN": "壬", "GUI": "癸"}
_PINYIN_BRANCH = {"ZI": "子", "CHOU": "丑", "YIN": "寅", "MAO": "卯", "CHEN": "辰", "SI": "巳",
                  "WU": "午", "WEI": "未", "SHEN": "申", "YOU": "酉", "XU": "戌", "HAI": "亥"}


def _dayun_from_chart(chart: Any):
    """BaziChart.luck_pillars(拼音 Pillar) → 中文干支列表 + 起运岁。

    Returns: (dayun_ganzhi_list, start_age)；不可用 → ([], None)（不猜）。
    """
    try:
        pillars = list(getattr(chart, "luck_pillars", None) or [])
        out = []
        for p in pillars:
            hs = _PINYIN_STEM.get(str(getattr(p, "heavenly_stem", "")).upper())
            eb = _PINYIN_BRANCH.get(str(getattr(p, "earthly_branch", "")).upper())
            if hs and eb:
                out.append(hs + eb)
        sa = getattr(chart, "start_age", None)
        if not out or sa is None:
            return out, None
        return out, float(sa)
    except Exception:
        return [], None


def _current_dayun(dayun: list, start_age: Optional[float],
                   target_year: Optional[int], birth_year: Optional[int]):
    """target_year 所在大运干支；越界/未知 → None（不猜）。"""
    if not dayun or start_age is None or not target_year or not birth_year:
        return None
    age = target_year - birth_year
    if age < 0:
        return None
    idx = int((age - start_age) // 10)
    if 0 <= idx < len(dayun):
        return dayun[idx]
    return None


def _ganzhi_of_year(year: int) -> str:
    """公历年 → 六十甲子干支（1984 甲子基准；(year-4)%10 / (year-4)%12）。"""
    from .ziping_classic_check import BRANCHES, STEMS

    if not year:
        return ""
    return STEMS[(int(year) - 4) % 10] + BRANCHES[(int(year) - 4) % 12]


def _shijian_from_facts(result: Dict[str, Any],
                        current_dayun: Optional[str] = None) -> DomainJudgment:
    """事件域: 以分析年流年冲合事实判事件存在性（原典·岁运）。

    口径(不夸大): 只判"有无冲(事件触发符号)", 冲的实际作用 p0 明示未核验,
    故 reasoning 带 boundary; 无分析年/无流年事实 → UNKNOWN。
    """
    ls = result.get("liunian_summary") or {}
    if not ls:
        return _unknown(JudgmentDomain.SHIJIAN,
                        "未指定分析年, 流年事实未出 → 事件域不判")
    ly = ls.get("liunian") or ""
    transit = ls.get("liunian_transit") or {}
    pairs = [c.get("pair") for c in (transit.get("clash_facts") or []) if c.get("pair")]
    root_pairs = [c.get("pair") for c in (ls.get("liunian_root_clash_facts") or [])
                  if c.get("pair")]
    # V7.192: 太岁冲运(流年支冲当前大运支)亦是事件触发符号(原典·岁运冲战)
    yun_pairs = []
    if current_dayun and len(current_dayun) >= 2:
        from .ziping_classic_check import CHONG as _CHONG
        _ly_branch = ly[-1] if len(ly) >= 2 else ""
        if _ly_branch and _CHONG.get(_ly_branch) == current_dayun[-1]:
            yun_pairs = [f"{_ly_branch}{current_dayun[-1]}(流年冲大运)"]
    if not (pairs or root_pairs or yun_pairs):
        return DomainJudgment(
            domain=JudgmentDomain.SHIJIAN,
            conclusion=JudgmentConclusion.EVENT_ABSENT,
            reasoning=f"分析年流年 {ly}: 流年支与命局四支及当前大运无冲 → 无事件触发符号；"
                      "（流年合/运限吉凶另属解层，不在本域）",
            rule_refs=["ZIPING_ENGINES_P0", _SHIJIAN_ANCHORS[0]],
            evidence_refs=list(_SHIJIAN_ANCHORS),
        )
    shown = [f"{a}{b}冲" for a, b in (pairs + root_pairs)] + yun_pairs
    return DomainJudgment(
        domain=JudgmentDomain.SHIJIAN,
        conclusion=JudgmentConclusion.EVENT_EXIST,
        reasoning=f"分析年流年 {ly}: 触发 {', '.join(shown)}；"
                  "冲为事件触发符号，实际作用 p0 明示未核验（不判吉凶/应期）",
        rule_refs=["ZIPING_ENGINES_P0", _SHIJIAN_ANCHORS[0], _SHIJIAN_ANCHORS[1]],
        evidence_refs=list(_SHIJIAN_ANCHORS),
    )


def _wangshuai_from_pillars(pillars: Optional[Dict[str, list]]) -> DomainJudgment:
    """旺衰域：得令/得地/得势 三才合参 + 成局（原典判据独立实现）。

    依据 STATE.WANG_SHUAI.PAN_DUAN_FA.001「其法不可执一」、DE_LING.001
    「不必论当令不令」、DE_DI.001、DE_SHI.001，见 ziping_classic_check.judge_strength。
    """
    if not pillars:
        return _unknown(JudgmentDomain.WANGSHUAI, "四柱缺失，旺衰不判")
    try:
        from .ziping_classic_check import judge_strength

        r = judge_strength(pillars)
    except Exception as exc:  # pragma: no cover - 防御性
        return _unknown(JudgmentDomain.WANGSHUAI,
                        f"旺衰判据异常: {type(exc).__name__}: {exc}")
    concl = {
        "STRONG": JudgmentConclusion.STRONG,
        "MODERATE": JudgmentConclusion.MODERATE,
        "WEAK": JudgmentConclusion.WEAK,
    }[r["conclusion"]]
    return DomainJudgment(
        domain=JudgmentDomain.WANGSHUAI,
        conclusion=concl,
        reasoning=(f"旺衰(三才合参)={r['conclusion']}(score={r['score']}): "
                   + "；".join(r["reasons"])),
        rule_refs=["ZIPING_ENGINES_P0"] + list(r["basis"]),
        evidence_refs=list(r["basis"]),
    )


def _engines_p0_synthesis(result: Dict[str, Any],
                          pillars: Optional[Dict[str, list]] = None,
                          target_year: Optional[int] = None,
                          current_dayun: Optional[str] = None) -> JudgmentSynthesis:
    """engines(p0 线) production_entry 输出 → 五大域。

    映射口径(不夸大):
    - 旺衰: p0 线自身只出得令/失令候选; 本桥接按原典三才判据独立计算
      （得令/得地/得势/成局），结论带原典切片证据锚。
    - 格局: ge_cheng['cheng_bai'] CHENG→ESTABLISHED / BAI→BROKEN / 其余 UNKNOWN。
    - 用神: zhenglun.yongyao.primary_medicine.wuxing → PRIMARY(用药方向, 非吉凶裁决)。
    - 十神/事件: p0 线未输出 → UNKNOWN。
    - 证据锚: 结论必须带可解析的 p0_v2 切片 ID（G1 证据闸要求），
      无锚则该域降级 UNKNOWN（不产无证据 claim）。
    """
    from . import p0_evidence

    facts = result.get("engine_result") or {}
    zhenglun = result.get("zhenglun") or {}

    gc = facts.get("ge_cheng") or {}
    cheng = gc.get("cheng_bai")
    ge_name = gc.get("ge") or ""
    ge_ev = _ge_evidence_refs(gc)
    ge_verifiable = gc.get("ge_rule_verification") != "NOT_EVALUABLE"
    rule_refs = [r for r in ("ZIPING_ENGINES_P0", _rule_id(gc)) if r]
    if cheng == "CHENG" and ge_name and ge_ev and ge_verifiable:
        geju = DomainJudgment(
            domain=JudgmentDomain.GEJU,
            conclusion=JudgmentConclusion.ESTABLISHED,
            reasoning=f"格局={ge_name}; cheng_bai=CHENG; 证据锚={len(ge_ev)} 片",
            rule_refs=rule_refs,
            evidence_refs=ge_ev,
        )
    elif cheng == "BAI" and ge_name and ge_ev and ge_verifiable:
        geju = DomainJudgment(
            domain=JudgmentDomain.GEJU,
            conclusion=JudgmentConclusion.BROKEN,
            reasoning=f"格局={ge_name or '未知'}; cheng_bai=BAI",
            rule_refs=rule_refs,
            evidence_refs=ge_ev,
        )
    else:
        geju = _unknown(
            JudgmentDomain.GEJU,
            f"格局未成/无证据锚: ge={ge_name or '未知'} cheng_bai={cheng!r} refs={len(ge_ev)}")

    yy = zhenglun.get("yongyao") or {}
    pm = yy.get("primary_medicine") or {}
    wx = pm.get("wuxing")
    state = yy.get("state")
    yy_ev = p0_evidence.resolve(list(yy.get("evidence_refs") or []))
    _ge_yong = pm.get("kind") == "格局用神"
    if (not yy_ev and state == "GE_FALLBACK" and ge_verifiable
            and cheng == "CHENG" and ge_name
            and str(yy.get("ge_fallback_source") or "").startswith("源2:格体喜神")):
        # 仅对已核验成格的格体喜神复用格局依据；救应/其他路径需独立证据。
        yy_ev = ge_ev
    if (not yy_ev and _ge_yong and state in ("NO_BING", "NO_BING_GE_XIJI")
            and ge_verifiable and cheng == "CHENG" and ge_name):
        # 无病时格之用神：用神由已核验之格局派生(PZZQ 论用神/论八格)，共用格证据锚。
        yy_ev = ge_ev
    if (wx in ("木", "火", "土", "金", "水")
            and (state in ("YONGYAO_RESOLVED", "GE_FALLBACK") or _ge_yong)
            and yy.get("evidence_status") != "NOT_EVALUABLE"
            and yy.get("primary_selection_status") != "NOT_EVALUABLE"
            and pm.get("stem_equivalence_status") != "NOT_EVALUABLE"
            and pm.get("candidate_source_verification") != "SOURCE_VERSION_CONFLICT" and yy_ev):
        yongshen = DomainJudgment(
            domain=JudgmentDomain.YONGSHEN,
            conclusion=JudgmentConclusion.PRIMARY,
            reasoning=(f"用药方向={wx}; 功能={pm.get('function')}; "
                       f"层状态={state}; 证据锚={len(yy_ev)} 片"),
            rule_refs=[r for r in ("ZIPING_ENGINES_P0", str(state or "YONGYAO_RESOLVE")) if r],
            evidence_refs=yy_ev,
        )
    else:
        yongshen = _unknown(JudgmentDomain.YONGSHEN,
                            f"用药未裁定/无证据锚: state={state!r} "
                            f"selection={yy.get('primary_selection_status')!r} refs={len(yy_ev)}; "
                            "证据仅供候选追溯，不代表用药结论成立",
                            evidence_refs=yy_ev)

    _facts_for_shishen = dict(facts)
    _facts_for_shishen["__yongyao"] = yy or {}
    _facts_for_shishen["__bing"] = (result.get("zhenglun") or {}).get("zhuangui") or {}
    # 格用神五行: 引擎把「格局用神」kind 的主药即格用神（源2 override 路径
    # 不回填 yy.ge_yong_wx），kind 白名单内直接取 pm.wuxing，其余取回填字段。
    _gy_wx = ""
    if isinstance(pm, dict) and pm.get("kind") == "格局用神":
        _gy_wx = str(pm.get("wuxing") or "")
    _gy_wx = _gy_wx or str((yy or {}).get("ge_yong_wx") or "")
    _facts_for_shishen["__ge_yong_wx"] = _gy_wx
    _ws_judgment = _wangshuai_from_pillars(pillars)
    _facts_for_shishen["__wangshuai"] = _ws_judgment.conclusion.value
    _shishen_refs = list(ge_ev) + list(yy_ev)

    return JudgmentSynthesis(
        wangshuai=_ws_judgment,
        geju=geju,
        yongshen=yongshen,
        shishen=_shishen_from_facts(_facts_for_shishen, _shishen_refs),
        shijian=_shijian_from_facts(result, current_dayun),
    )


def _pillar_dict(pillar: Any, position: str) -> Dict[str, str]:
    """Pillar → dict {position, heavenly_stem, earthly_branch}。"""
    return {
        "position": position,
        "heavenly_stem": getattr(pillar, "heavenly_stem", ""),
        "earthly_branch": getattr(pillar, "earthly_branch", ""),
    }


def build_context(chart: Any) -> Dict[str, Any]:
    """将 BaziChart 转换为 Judgment 期望的 NatalContext 形态 dict。

    Args:
        chart: BaziChart 实例 (需有 year_pillar/month_pillar/day_pillar/hour_pillar/day_master)

    Returns:
        {"natal": {"pillars": [...], "day_master": ...}}

    若 chart 缺少必需字段，返回含空 day_master 的 context，
    由 Judgment 层 fail-closed 处理 (返回 UNKNOWN)。
    """
    day_master = getattr(chart, "day_master", "") or ""
    pillars = [
        _pillar_dict(getattr(chart, "year_pillar", None), "YEAR"),
        _pillar_dict(getattr(chart, "month_pillar", None), "MONTH"),
        _pillar_dict(getattr(chart, "day_pillar", None), "DAY"),
        _pillar_dict(getattr(chart, "hour_pillar", None), "HOUR"),
    ]
    return {"natal": {"pillars": pillars, "day_master": day_master}}


def run_ziping_judgment(chart: Any, target_year: Optional[int] = None) -> JudgmentSynthesis:
    """对 CanonicalBaziChart 执行五大域判断。

    BZ-FNDR-15 (⑮-0 接入契约): Ziping 入口接收 CanonicalBaziChart.
    真实生产路径必须经过 assert_canonical_gate(require_factory=True).

    [2026-11-07 用户裁决] 子平引擎最终版本 = D:\\shuntian-ziping-p0 (engines p0 线).
    本桥接改为调用 engines.production_entry(唯一生产入口, G-P01~G-P05 gate),
    再把 engine_result/zhenglun 映射为五域; 映射不能确定的域一律 UNKNOWN 并写明原因。

    Args:
        chart: CanonicalBaziChart 实例

    Returns:
        JudgmentSynthesis (wangshuai/geju/yongshen/shishen/shijian)

    任何异常不阻断: 返回五域全 UNKNOWN 的 synthesis。
    """
    try:
        # BZ-FNDR-15: 真实生产入口 provenance gate (审计模式).
        from tongshu.models.canonical_bazi import assert_canonical_gate
        assert_canonical_gate(chart, require_factory=False)
    except Exception as exc:
        return JudgmentSynthesis(
            wangshuai=_unknown(JudgmentDomain.WANGSHUAI,
                               f"canonical gate 拒绝: {type(exc).__name__}: {exc}"),
            geju=_unknown(JudgmentDomain.GEJU, "canonical gate 未通过"),
            yongshen=_unknown(JudgmentDomain.YONGSHEN, "canonical gate 未通过"),
            shishen=_unknown(JudgmentDomain.SHISHEN, "canonical gate 未通过"),
            shijian=_unknown(JudgmentDomain.SHIJIAN, "canonical gate 未通过"),
        )

    try:
        pillars = _pillars_from_chart(chart)
    except Exception as exc:
        return JudgmentSynthesis(
            wangshuai=_unknown(JudgmentDomain.WANGSHUAI,
                               f"四柱不可用: {type(exc).__name__}: {exc}"),
            geju=_unknown(JudgmentDomain.GEJU, "四柱不可用"),
            yongshen=_unknown(JudgmentDomain.YONGSHEN, "四柱不可用"),
            shishen=_unknown(JudgmentDomain.SHISHEN, "四柱不可用"),
            shijian=_unknown(JudgmentDomain.SHIJIAN, "四柱不可用"),
        )

    try:
        if str(_REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(_REPO_ROOT))
        from engines.production_entry import (
            FrozenCanonicalBaziChart,
            production_entry,
        )
        _liunian = _ganzhi_of_year(target_year) if target_year else None
        _dayun, _start_age = _dayun_from_chart(chart)
        _birth_year = None
        _bdt = getattr(chart, "birth_datetime", None)
        try:
            if _bdt is not None:
                _birth_year = int(getattr(_bdt, "year", None) or 0) or None
        except Exception:
            _birth_year = None
        result = production_entry(FrozenCanonicalBaziChart(
            pillars=pillars, liunian=_liunian, dayun=(_dayun or None)))
    except Exception as exc:  # pragma: no cover - 防御性
        return JudgmentSynthesis(
            wangshuai=_unknown(JudgmentDomain.WANGSHUAI,
                               f"engines 生产入口异常: {type(exc).__name__}: {exc}"),
            geju=_unknown(JudgmentDomain.GEJU, "engines 生产入口异常"),
            yongshen=_unknown(JudgmentDomain.YONGSHEN, "engines 生产入口异常"),
            shishen=_unknown(JudgmentDomain.SHISHEN, "engines 生产入口异常"),
            shijian=_unknown(JudgmentDomain.SHIJIAN, "engines 生产入口异常"),
        )

    if not result.get("gate_passed"):
        reason = f"engines gate 失败({result.get('gate')}): {result.get('reason')}"
        return JudgmentSynthesis(
            wangshuai=_unknown(JudgmentDomain.WANGSHUAI, reason),
            geju=_unknown(JudgmentDomain.GEJU, reason),
            yongshen=_unknown(JudgmentDomain.YONGSHEN, reason),
            shishen=_unknown(JudgmentDomain.SHISHEN, reason),
            shijian=_unknown(JudgmentDomain.SHIJIAN, reason),
        )

    _cur_dyun = _current_dayun(_dayun, _start_age, target_year, _birth_year)
    return _engines_p0_synthesis(result, pillars, target_year=target_year,
                                 current_dayun=_cur_dyun)


def synthesis_to_dict(synthesis: JudgmentSynthesis) -> dict:
    """JudgmentSynthesis → dict (供 pipeline 序列化/解层消费)。"""
    return synthesis.to_dict()
