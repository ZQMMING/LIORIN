# -*- coding: utf-8 -*-
"""河洛**解读层编排**：把引擎产出接到解读层六模块，产出统一可下发结构（2026-10-24）。

为什么需要这一层
----------------
解读层六模块（``interpretation`` / ``guidance`` / ``diagnosis_rule_graph`` /
``metrics_v2`` / ``hexagram_state`` / ``canonical_signals``）此前在
``src/`` 内**零生产调用方** —— 逻辑与单测都在，但生产链从不产出它们的输出。
本模块是**唯一的接线点**，把「河洛判词层 → 解读层 → 平台」这条链补上。

⚠ **不作废、不复活自拟分数**
---------------------------
``hexagram_state.calculate_hexagram_state`` 与
``interpretation._hexagram_base_score`` / ``_year_cycle_factor`` 已于 2026-10-07/08
**作废**（自拟浮点分数无原典依据，恒抛 ``NotImplementedError``）。
本模块**不复活**它们；对「静/动/变/互的机会风险」改用
:mod:`gui_ming_liu_ju` 的**六项原典判据**（起例卷之中 L630–L648），
对「五行旺衰」改用 :func:`hexagram_state.judge_element_state`（起例卷之上 L102）。

**降级原则**：任一子块失败**不阻塞主链**，但必须写入 ``warnings`` ——
「缺失被当成正常，比答错更坏」。
"""
from __future__ import annotations

from typing import Any

from .dimensions import DIM_PROCESS, DIM_UNCLASSIFIED, DOMAINS, label_of

#: 爻位序号 → 爻位名（用于 interpretation.line_position / 元堂名）
_YAO_POS = ("初爻", "二爻", "三爻", "四爻", "五爻", "上爻")


def _safe_getattr(obj: Any, name: str, default: Any = None,
                  on_error: Any = None) -> Any:
    """安全取属性：**属性访问本身抛异常**时返回默认值。

    ⚠ 2026-10-25 审计修（真实缺陷）：``getattr(obj, name, default)`` 的
      ``default`` **只对「属性不存在」生效**；若属性访问**本身抛异常**
      （代理对象 / 惰性属性 / ``__getattr__`` 抛错），异常会**穿透**。
      实测：解读层因此成为「唯一能让主链崩掉的入口」，
      违反本模块的降级原则（任一子块失败不阻塞主链）。
      ⇒ 对 result 的取值一律走本助手。

    Args:
        obj:      取属性的对象。
        name:     属性名。
        default:  取不到时的默认值。
        on_error: 属性访问**抛异常**时的回调（可调用）。
                  传它是为了让失败**留痕** —— 缺失被当成正常，比答错更坏。
    """
    try:
        return getattr(obj, name, default)
    except Exception as exc:
        if callable(on_error):
            try:
                on_error(exc)
            except Exception:
                pass
        return default


def _plain(obj: Any) -> Any:
    """任意对象 → 可 JSON 序列化的结构（不丢信息、不造值）。"""
    import dataclasses
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    # ⚠⚠ 2026-10-26 修（变异扫描抓到的真实缺陷）：
    #   **类对象**（type）必须**在最前面**排除。
    #   原因：dataclass 的**字段默认值**是写在**类**上的属性 ⇒
    #   `vars(SomeDataclass)` 会直接拿到那些默认值 ⇒
    #   把类对象展开成 `{'a': 1, 'b': 'x'}` ⇒ **造值**
    #   （那不是任何实例的真实数据！）。
    #   原实现只在 dataclass 分支上写了 `not isinstance(obj, type)`，
    #   但**后面的 `hasattr(obj, "__dict__")` 分支照样把类展开了**
    #   ⇒ 那道防线形同虚设（实测 `_plain(_D)` → `{'a': 1, 'b': 'x'}`）。
    #   ⇒ 现在提到最前面统一处理：类对象一律转字符串表示。
    if isinstance(obj, type):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_plain(v) for v in obj]
    if dataclasses.is_dataclass(obj):
        return {f.name: _plain(getattr(obj, f.name))
                for f in dataclasses.fields(obj)}
    if hasattr(obj, "to_dict"):
        try:
            return _plain(obj.to_dict())
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return {k: _plain(v) for k, v in vars(obj).items()
                if not k.startswith("_")}
    return str(obj)


def _yao_name(index: Any) -> str:
    """爻位下标（0=初爻 … 5=上爻）→ 爻位名。"""
    try:
        i = int(index)
    except Exception:
        return ""
    return _YAO_POS[i] if 0 <= i < 6 else ""


def _gua_full_name(upper: Any, lower: Any) -> str:
    """上下卦 → 「X上Y下」格式（interpretation 模块的卦名口径）。"""
    u = str(upper or "").strip()
    l = str(lower or "").strip()
    return f"{u}上{l}下" if (u and l) else ""


def _ganzhi_of(target_date: str | None) -> tuple[str, str]:
    """目标日（公历）→ （月柱干支, 日柱干支）。

    月柱取**节气月柱**（八字口径，getMonthInGanZhiExact2），与河洛
    「以节气定月」一致（起例卷之上 L62「未得十月节气，只作九月论」）。
    取不到则返回空串 —— **不猜**。
    """
    if not target_date:
        return "", ""
    try:
        from lunar_python import Solar
        y, m, d = (int(x) for x in str(target_date)[:10].split("-"))
        lunar = Solar.fromYmd(y, m, d).getLunar()
        return lunar.getMonthInGanZhiExact2(), lunar.getDayInGanZhi()
    except Exception:
        return "", ""


def _build_engine_evidences(result: Any, dims: list[str],
                            evidence: list[str]) -> tuple[list, list[str]]:
    """判词层证据 → V13 ``EngineEvidence`` 列表。

    ⚠ **rule_id 是「机制」，不是「维度」**：
      rule_id 回答「这条结论由哪条机制算出」（诊断图的节点），
      维度回答「它落在哪个人生领域」（放 ``attributes``）。
      映射见 :data:`dimensions.DIM_TO_RULE`；无对应机制的维度
      （如「三刑六列」——原典有载、引擎未实现）**不进诊断图**，
      其证据条目数在返回的 skipped 里报出（不静默丢）。
    """
    from ...spec.canonical import EngineEvidence, EngineName, TemporalScope
    from .dimensions import DIM_TO_RULE

    out = []
    skipped: list[str] = []
    for i, (text, dim) in enumerate(zip(evidence, dims)):
        if dim in (DIM_PROCESS, DIM_UNCLASSIFIED):
            continue
        rule_id = DIM_TO_RULE.get(dim, "")
        if not rule_id:
            skipped.append(dim)
            continue
        out.append(EngineEvidence(
            evidence_id=f"HELUO.EV.{i:03d}",
            engine=EngineName.HE_LUO,
            rule_id=rule_id,
            value=text,
            temporal_scope=TemporalScope.BIRTH,
            attributes={
                "dimension": dim,
                "dimension_label": label_of(dim),
                "domain": DOMAINS.get(dim.split(".")[0], ""),
                "evidence_index": i,
            },
            source_rule_ref="heluo_engine/guajie.py",
            source_field="evidence",
            calculation_version="2026.10",
        ))
    return out, skipped


def _hexagram_state_block(result: Any) -> tuple[dict, list[str]]:
    """卦象状态：**有据**实现（替代已作废的 calculate_hexagram_state）。

    · 静/动/变/互的机会风险 → :func:`gui_ming_liu_ju.judge_liu_ju`
      的六项原典判据（一卦名吉/二爻吉/三辞吉/四得时/五有援/六顺时）
    · 五行旺衰 → :func:`hexagram_state.judge_element_state`
      （起例卷之上 L102「当生者王，所生者相…」）
    """
    warnings: list[str] = []
    block: dict[str, Any] = {}
    gua = getattr(_safe_getattr(result, "prenatal", None), "hexagram_name", "") or ""
    try:
        from .gui_ming_liu_ju import judge_liu_ju
        yt = _safe_getattr(result, "yuantang", None)
        gj = _safe_getattr(result, "guajie", None) or {}
        benming = gj.get("benming") if isinstance(gj, dict) else None
        yb = gj.get("liunian_ye_buye") if isinstance(gj, dict) else None
        nums = _safe_getattr(result, "numbers", None)
        bazi = _safe_getattr(result, "bazi", None) or []
        j = judge_liu_ju(
            gua_name=gua,
            gua_ci=str((benming or {}).get("gua_ci", "") or ""),
            yuantang_index=getattr(yt, "yuantang_index", None),
            month=(bazi[1][1] if len(bazi) > 1 else None),
            gua_qi_month=(yb or {}).get("gua_qi_month") if isinstance(yb, dict) else None,
            tian_shu=getattr(nums, "tian_shu", None),
            di_shu=getattr(nums, "di_shu", None),
        )
        # judge_liu_ju 返回 dict[str, JuResult]（**绝不臆造分数**，
        # 原典未言者 passed=None）⇒ 直接序列化，不做分数化。
        block["liu_ju"] = {k: _plain(v) for k, v in j.items()}
    except Exception as exc:
        warnings.append(f"卦象状态·六项判据未产出（{type(exc).__name__}: {exc}）")
    try:
        from .hexagram_state import judge_element_state
        bazi = _safe_getattr(result, "bazi", None) or []
        month_branch = bazi[1][1] if len(bazi) > 1 else ""
        els = {}
        for el in ("木", "火", "土", "金", "水"):
            try:
                els[el] = judge_element_state(el, month_branch)
            except Exception:
                els[el] = ""
        block["element_state"] = els
        block["month_branch"] = month_branch
        if not month_branch:
            warnings.append("卦象状态·五行旺衰缺月支（按空处理，不猜）")
    except Exception as exc:
        warnings.append(f"卦象状态·五行旺衰未产出（{type(exc).__name__}: {exc}）")
    block["note"] = ("机会/风险以**原典六项判据**（起例卷之中 L630–L648）给出"
                      "吉/凶/不判，**不给 0–1 分数**；"
                      "已作废的自拟分数（hexagram_state.calculate_hexagram_state）"
                      "不予复活。")
    return block, warnings


def build_interpretation(result: Any) -> dict:
    """河洛产出 → 解读层统一输出。

    Returns:
        ``{platform_signals, interpretation, guidance, diagnosis, metrics,
        hexagram_state, dimension_view, warnings}``
        —— 任一子块失败都不阻塞主链，失败原因写入 ``warnings``。
    """
    out: dict[str, Any] = {}
    warnings: list[str] = []

    # ⚠ 2026-10-25 审计修（真实缺陷）：原为
    #     ``guajie = getattr(result, "guajie", None) or {}``
    #   —— ``getattr`` 的**默认值只对「属性不存在」生效**；若属性访问**本身抛异常**
    #   （如代理对象 / 惰性属性 / __getattr__ 抛错），异常会**穿透**到调用方
    #   ⇒ 解读层变成「唯一能让主链崩掉的入口」，违反「任一子块失败不阻塞主链」。
    #   实测：喂一个 __getattr__ 抛 RuntimeError 的对象即崩。
    #   现改为：经 _safe_getattr 取值，并把失败**留痕**在 warnings
    #   （缺失被当成正常，比答错更坏）。
    def _note_attr_error(exc: Exception) -> None:
        warnings.append(f"判词层读取失败（{type(exc).__name__}: {exc}）")

    guajie = _safe_getattr(result, "guajie", None,
                           on_error=_note_attr_error) or {}
    if not isinstance(guajie, dict):
        guajie = {}
    evidence = list(guajie.get("evidence") or [])
    dims = list(guajie.get("evidence_dims") or [])
    if len(dims) != len(evidence):
        dims = ["UNCLASSIFIED"] * len(evidence)

    # ── ① 平台信号 ────────────────────────────────────────────────
    try:
        from .canonical_signals import build_platform_signals
        out["platform_signals"] = build_platform_signals(result)
    except Exception as exc:
        out["platform_signals"] = []
        warnings.append(f"平台信号未产出（{type(exc).__name__}: {exc}）")

    # ── ② 解读层（interpretation）─────────────────────────────────
    interp_dict: dict[str, Any] = {}
    try:
        from .interpretation import HeluoInput as _IInput
        from .interpretation import interpret as _interpret
        pre = _safe_getattr(result, "prenatal", None)
        post = _safe_getattr(result, "postnatal", None)
        yt = _safe_getattr(result, "yuantang", None)
        tl = _safe_getattr(result, "timeline", None)
        ty = (getattr(tl, "target_year_hexagram", None) or {}) if tl else {}
        daily = ((getattr(tl, "daily_hexagram", None) or {}).get("base_hex") or {}) if tl else {}
        m_ganzhi, d_ganzhi = _ganzhi_of(_safe_getattr(result, "target_date", None))
        _inp = _IInput(
            prenatal_hexagram=_gua_full_name(getattr(pre, "upper_gua", ""),
                                            getattr(pre, "lower_gua", "")),
            yuan_tang=_yao_name(getattr(yt, "yuantang_index", -1)),
            postnatal_hexagram=_gua_full_name(getattr(post, "upper_gua", ""),
                                             getattr(post, "lower_gua", "")),
            day_hexagram=str(daily.get("name", "") or ""),
            year_cycle=str(ty.get("ganzhi", "") or ""),
            month_cycle=m_ganzhi,
            day_cycle=d_ganzhi,
            # ⚠ 不传 element_state：原典只给旺衰**名目**，无数值刻度；
            #   编一个数值刻度就是「复活自拟分数」。留空 ⇒ 走「证据不全」路径。
            element_state={},
            line_position={
                "active_line": getattr(yt, "yuantang_index", -1),
                "position_type": _yao_name(getattr(yt, "yuantang_index", -1)),
                "yinyang": getattr(yt, "yao_nature", "") or "",
            },
            time_state={
                "solar_term": str((_safe_getattr(result, "seasonal_hexagram", None) or {})
                                   .get("jieqi", "") or ""),
                "hour": 0,
                "true_solar_time": False,
            },
        )
        _out = _interpret(_inp)
        interp_dict = _plain(_out)
        out["interpretation"] = interp_dict
    except Exception as exc:
        out["interpretation"] = {}
        warnings.append(f"解读层未产出（{type(exc).__name__}: {exc}）")

    # ── ③ 诊断规则图（维度 → 规则节点）────────────────────────────
    diag_dict: dict[str, Any] = {}
    assertions: list = []
    judgment: Any = None
    try:
        from .diagnosis_rule_graph import build_diagnosis_graph, dropped_rules
        evs, skipped = _build_engine_evidences(result, dims, evidence)
        _dr = build_diagnosis_graph(evs, out.get("platform_signals") or [], result,
                                    subject="heluo")
        diag_dict = _plain(_dr)
        assertions = list(_dr.assertions)
        judgment = _dr.judgment
        out["diagnosis"] = diag_dict
        _drop = dropped_rules()
        if _drop:
            warnings.append(f"诊断规则图丢弃了未注册授权的规则：{_drop}")
        if skipped:
            warnings.append(
                f"以下维度无对应机制规则，其证据未进诊断图（引擎未实现/无授权）："
                f"{sorted(set(skipped))}")
    except Exception as exc:
        out["diagnosis"] = {}
        warnings.append(f"诊断规则图未产出（{type(exc).__name__}: {exc}）")

    # ── ④ 行动指引（guidance）────────────────────────────────────
    try:
        from .guidance import generate_guidance
        pre = _safe_getattr(result, "prenatal", None)
        post = _safe_getattr(result, "postnatal", None)
        yt = _safe_getattr(result, "yuantang", None)
        tl = _safe_getattr(result, "timeline", None)
        ty = (getattr(tl, "target_year_hexagram", None) or {}) if tl else {}
        hg = _safe_getattr(result, "hua_gong", None)
        _g = generate_guidance(
            assertions, judgment,
            source_gua=str(getattr(pre, "hexagram_name", "") or ""),
            target_gua=str(ty.get("hexagram", "") or
                           getattr(post, "hexagram_name", "") or ""),
            yuan_tang=str(getattr(yt, "yuantang", "") or ""),
            hua_gong_state=str(getattr(hg, "state", "") or "") if hg else None,
            subject="heluo",
        )
        out["guidance"] = _plain(_g)
    except Exception as exc:
        out["guidance"] = {}
        warnings.append(f"行动指引未产出（{type(exc).__name__}: {exc}）")

    # ── ⑤ 解读质量指标（metrics_v2）──────────────────────────────
    try:
        from .metrics_v2 import evaluate_interpretation
        _m = evaluate_interpretation(
            interp_dict,
            classical_source=out.get("interpretation", {}).get("classical_reference"),
            evidence_chain=[{"text": t} for t in evidence],
        )
        out["metrics"] = _plain(_m)
    except Exception as exc:
        out["metrics"] = {}
        warnings.append(f"解读质量指标未产出（{type(exc).__name__}: {exc}）")

    # ── ⑥ 卦象状态（有据实现，替代已作废的自拟分数）──────────────
    _hs, _hw = _hexagram_state_block(result)
    out["hexagram_state"] = _hs
    warnings.extend(_hw)

    # ── ⑦ 维度视图（复用判词层已打好的标签）─────────────────────
    out["dimension_view"] = guajie.get("by_dimension") or {}
    out["dimension_coverage"] = guajie.get("dimension_coverage") or {}

    # ── ⑧ 平台 17 类**候选证据**（河洛只给候选，最终裁定属平台）────
    try:
        from .dimensions import build_event_candidates
        out["event_candidates"] = build_event_candidates(
            out["dimension_view"], guajie)
    except Exception as exc:
        out["event_candidates"] = {}
        warnings.append(f"平台事件候选未产出（{type(exc).__name__}: {exc}）")

    out["warnings"] = warnings
    return out
