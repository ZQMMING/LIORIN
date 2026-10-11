"""HeluoViewRenderer — HeluoResult 字段 → 用户视角中文文本 的映射层。

⚠ 2026-10-11：用户口径「用户看什么」——之前 rendered_text 是 18 条通用模板，
跟卦象/命局完全脱节。这里把 HeluoResult 的解卦/诊断/建议/六层卦象按字段
一对一映射成中文文本行，**每条数据字段对应一行中文**，没有的话跳过。

不做：
- 不靠 LLM（纯引擎组装）
- 不挑拣（用户问"看到什么"，看全才算数）
- 不编造（字段不存在就跳过）

调用：HeluoViewRenderer.render(heluo_result, theme="WORK") -> str
"""

from __future__ import annotations
from typing import Any, Optional


# 6 层卦象显示顺序 + 字段映射
_GUA_LAYERS = [
    ("命卦根基（先天卦）", "_render_prenatal"),
    ("时空变换（后天卦）", "_render_postnatal"),
    ("大运当年", "_render_dayun"),
    ("流年卦", "_render_liunian"),
    ("流月卦", "_render_liuyue"),
    ("流日卦", "_render_liuri"),
]


def _safe(value: Any, default: str = "") -> str:
    """字段取值：None/空串/0 都返回 default，绝不抛。"""
    if value is None:
        return default
    if isinstance(value, str) and not value.strip():
        return default
    return str(value)


def _truncate(value: str, limit: int = 200) -> str:
    """超长截断（防止 evidence 流过长文本刷屏）。"""
    if len(value) <= limit:
        return value
    return value[:limit] + "…"


class HeluoViewRenderer:
    """HeluoResult → 用户视角中文文本的视图层映射器。

    输出结构：
        §1 命卦根基（先天卦）+ 元堂爻
        §2 时空变换（后天卦）
        §3 大运当年（虚岁 X → 段 X-X）
        §4 流年卦（X 干支年）
        §5 流月卦（X 月）
        §6 流日卦（X 日）
        §7 元气化工（先天后天元气 / 化工）
        §8 诊断（8 条 HL_* + ZPZ 断言）
        §9 建议（3 条行动 + 2 条警示）
    """

    def render(self, heluo_result, theme: str = "WORK", target_year: int | None = None) -> str:
        """主入口。target_year 决定大运当年段；不传取 yearly 末年（兜底）。"""
        if heluo_result is None:
            return ""

        sections = []
        for title, method_name in _GUA_LAYERS:
            method = getattr(self, method_name)
            # 大运当年传 target_year（其它方法忽略）
            if method_name == "_render_dayun":
                block = method(heluo_result, target_year=target_year)
            else:
                block = method(heluo_result)
            if block:
                sections.append(block)
        sections.append(self._render_yuan_qi(heluo_result))
        sections.append(self._render_diagnosis(heluo_result))
        sections.append(self._render_guidance(heluo_result))

        body = "\n\n".join(s for s in sections if s)
        if theme:
            return f"【{theme}主题解读】\n\n{body}"
        return body

    # ── §1 命卦根基（先天卦） ──────────────────────
    def _render_prenatal(self, h) -> str:
        pre = h.prenatal
        if pre is None:
            return ""
        name = _safe(getattr(pre, "hexagram_name", ""))
        upper = _safe(getattr(pre, "upper_gua", ""))
        lower = _safe(getattr(pre, "lower_gua", ""))
        lines = []
        lines.append(f"卦名：{name}（上{upper} 下{lower}）" if name else "卦名：缺")
        # 元堂爻
        yt = h.yuantang
        if yt is not None:
            yt_name = _safe(getattr(yt, "yuantang", ""))
            yt_idx = getattr(yt, "yuantang_index", -1)
            yt_nature = _safe(getattr(yt, "yao_nature", ""))
            if yt_name:
                lines.append(f"元堂爻：{yt_name}（index={yt_idx}，{yt_nature}爻）")
        # 卦辞（来自 guajie.evidence 或 guajie.benming）
        gj = h.guajie or {}
        benming = gj.get("benming") or {}
        if benming.get("gua_ci"):
            lines.append(f"卦辞：{benming['gua_ci']}")
        if benming.get("gua_ci_jingyi"):
            lines.append(f"卦辞精义：{benming['gua_ci_jingyi']}")
        if benming.get("gua_ci_shiyi"):
            lines.append(f"卦辞释义：{benming['gua_ci_shiyi']}")
        # 元堂爻辞
        guj_lines = gj.get("evidence") or []
        for e in guj_lines:
            if "元堂" in e and "爻辞" in str(e):
                lines.append(_truncate(str(e), 240))
                break
        return "§1 命卦根基（先天卦）\n" + "\n".join(lines) if lines else ""

    # ── §2 时空变换（后天卦） ──────────────────────
    def _render_postnatal(self, h) -> str:
        post = h.postnatal
        if post is None:
            return ""
        name = _safe(getattr(post, "hexagram_name", ""))
        upper = _safe(getattr(post, "upper_gua", ""))
        lower = _safe(getattr(post, "lower_gua", ""))
        post_lines = list(getattr(post, "lines", []) or [])
        lines = []
        lines.append(f"卦名：{name}（上{upper} 下{lower}）")
        if post_lines:
            lines.append(f"六爻：{post_lines}")
        # 后天卦辞：直接从 guajie_data 查（短卦名）
        try:
            from tongshu.engines.heluo.guajie import load_guajie_data
            data = load_guajie_data()
            short = name[-1] if name else ""
            if short in data:
                gd = data[short]
                if gd.gua_ci:
                    lines.append(f"卦辞：{gd.gua_ci}")
                if gd.gua_ci_jingyi:
                    lines.append(f"卦辞精义：{gd.gua_ci_jingyi}")
                if gd.gua_ci_shiyi:
                    lines.append(f"卦辞释义：{gd.gua_ci_shiyi}")
        except Exception:
            pass
        return "§2 时空变换（后天卦）\n" + "\n".join(lines) if lines else ""

    # ── §3 大运当年 ──────────────────────
    def _render_dayun(self, h, target_year: int | None = None) -> str:
        if h.timeline is None:
            return ""
        qi = (h.timeline.qi_phase or {})
        dayun = qi.get("dayun") or []
        yearly = h.timeline.yearly_hexagrams or []
        if not yearly:
            return ""
        if target_year is None:
            target_year_yr = yearly[-1].get("year")
        else:
            target_year_yr = target_year
        age_now = None
        for e in yearly:
            if e.get("year") == target_year_yr:
                age_now = e.get("age")
                break
        if age_now is None:
            return ""
        seg = None
        for d in dayun:
            if d.get("age_start") and d.get("age_end"):
                if d["age_start"] <= age_now <= d["age_end"]:
                    seg = d
                    break
        if seg is None:
            return ""
        lines = []
        lines.append(f"虚岁 {age_now}（{target_year_yr} 年）")
        # 爻名：line_index 0..5 → 初/二/三/四/五/上；line_nature 阳/阴 → 九/六
        idx = seg.get("line_index")
        nature = seg.get("line_nature")
        if idx is not None:
            yao_pos = ["初", "二", "三", "四", "五", "上"][idx]
            yao_char = "九" if nature == "阳" else "六"
            yao_name = f"{yao_pos}{yao_char}"
        else:
            yao_name = ""
        hua_name = seg.get("hexagram", "")
        lines.append(f"段：{seg['age_start']}-{seg['age_end']} 岁（{seg.get('phase', '')}{hua_name}·{yao_name} / line_index={idx}）")
        # 查 guajie 表取爻辞/岁运逢之
        try:
            from tongshu.engines.heluo.guajie import query_yao_duan as _qyd
        except Exception:
            _qyd = None
        if _qyd is not None and hua_name and yao_name:
            # 大运 hexagram 是全名（"风山渐"），query_yao_duan 要短卦名（"渐"）
            short_name = hua_name[-1] if hua_name else ""
            yd = _qyd(short_name, yao_name)
            if yd:
                if yd.ci:
                    lines.append(f"爻辞：{yd.ci}")
                if yd.xiang:
                    lines.append(f"象辞：{yd.xiang}")
                if yd.yi:
                    lines.append(f"释义：{_truncate(yd.yi, 240)}")
                if yd.suiyun:
                    lines.append(f"岁运逢之：{_truncate(yd.suiyun, 200)}")
                if yd.jingyi:
                    lines.append(f"精义：{yd.jingyi}")
        return "§3 大运当年\n" + "\n".join(lines) if lines else ""

    # ── §4 流年卦 ──────────────────────
    def _render_liunian(self, h) -> str:
        gj = h.guajie or {}
        name = _safe(gj.get("liunian_hexagram"))
        yao = gj.get("liunian_yao") or {}
        yao_name = _safe(yao.get("yao")) if isinstance(yao, dict) else ""
        year = gj.get("liunian_year") or ""
        if not name:
            return ""
        lines = [f"流年卦：{name}（{yao_name} 爻 / {year}）"]
        if isinstance(yao, dict):
            if yao.get("ci"):
                lines.append(f"卦辞：{yao['ci']}")
            if yao.get("xiang"):
                lines.append(f"象辞：{yao['xiang']}")
            if yao.get("yi"):
                lines.append(f"爻辞：{_truncate(yao['yi'], 240)}")
            if yao.get("suiyun"):
                lines.append(f"岁运逢之：{_truncate(yao['suiyun'], 200)}")
            if yao.get("jingyi"):
                lines.append(f"精义：{yao['jingyi']}")
            if yao.get("shiyi"):
                lines.append(f"释义：{_truncate(yao['shiyi'], 360)}")
        return "§4 流年卦\n" + "\n".join(lines) if lines else ""

    # ── §5 流月卦 ──────────────────────
    def _render_liuyue(self, h) -> str:
        gj = h.guajie or {}
        name = _safe(gj.get("liuyue_hexagram"))
        yao = gj.get("liuyue_yao") or {}
        yao_name = _safe(yao.get("yao")) if isinstance(yao, dict) else ""
        if not name:
            return ""
        lines = [f"流月卦：{name}（{yao_name} 爻）"]
        if isinstance(yao, dict):
            if yao.get("ci"):
                lines.append(f"卦辞：{yao['ci']}")
            if yao.get("xiang"):
                lines.append(f"象辞：{yao['xiang']}")
            if yao.get("yi"):
                lines.append(f"爻辞：{_truncate(yao['yi'], 240)}")
            if yao.get("suiyun"):
                lines.append(f"岁运逢之：{_truncate(yao['suiyun'], 200)}")
            if yao.get("jingyi"):
                lines.append(f"精义：{yao['jingyi']}")
        return "§5 流月卦\n" + "\n".join(lines) if lines else ""

    # ── §6 流日卦 ──────────────────────
    def _render_liuri(self, h) -> str:
        gj = h.guajie or {}
        name = _safe(gj.get("liuri_hexagram"))
        yao = gj.get("liuri_yao") or {}
        yao_name = _safe(yao.get("yao")) if isinstance(yao, dict) else ""
        if not name:
            return ""
        lines = [f"流日卦：{name}（{yao_name} 爻）"]
        if isinstance(yao, dict):
            if yao.get("ci"):
                lines.append(f"卦辞：{yao['ci']}")
            if yao.get("xiang"):
                lines.append(f"象辞：{yao['xiang']}")
            if yao.get("yi"):
                lines.append(f"爻辞：{_truncate(yao['yi'], 240)}")
            if yao.get("suiyun"):
                lines.append(f"岁运逢之：{_truncate(yao['suiyun'], 200)}")
            if yao.get("jingyi"):
                lines.append(f"精义：{yao['jingyi']}")
        return "§6 流日卦\n" + "\n".join(lines) if lines else ""

    # ── §7 元气化工 ──────────────────────
    def _render_yuan_qi(self, h) -> str:
        hg = h.hua_gong
        gj = h.guajie or {}
        lines = []
        if hg is not None:
            state = _safe(getattr(getattr(hg, "state", None), "value", ""), "—")
            tri = _safe(getattr(hg, "huagong_trigram", ""), "—")
            level = _safe(getattr(hg, "level", ""), "—")
            reduced = getattr(hg, "reduced", None)
            lines.append(f"化工：{tri}（{level}层 / state={state} / 减半={reduced}）")
            ev = getattr(hg, "evidence", None) or []
            if ev:
                lines.append(f"化工证据：{len(ev)} 条")
                for e in ev[:4]:
                    lines.append(f"  · {_truncate(str(e), 200)}")
        # 元气（先天后天）
        evs = gj.get("evidence") or []
        for e in evs:
            if "元气" in str(e):
                lines.append(_truncate(str(e), 240))
                break
        return "§7 元气化工\n" + "\n".join(lines) if lines else ""

    # ── §8 诊断 ──────────────────────
    def _render_diagnosis(self, h) -> str:
        # 诊断来自 heluo_diagnosis（ComputeResult.heluo_diagnosis）
        # 我们这里拿不到 compute，所以从 guajie.evidence 提刻诊
        gj = h.guajie or {}
        evs = gj.get("evidence") or []
        # 抓诊断相关条目（运反流反、十二神杀、四段、贵贱十体）
        keys = ["运/流年数反", "贵贱", "数之凶吉", "十二凶", "四段", "纳音元气",
                "五命得卦", "月令非时", "六位贵贱", "相生为福", "叶/不叶"]
        lines = []
        for e in evs:
            es = str(e)
            for k in keys:
                if k in es:
                    lines.append(f"  · {_truncate(es, 220)}")
                    break
        return "§8 诊断与判据\n" + "\n".join(lines[:18]) if lines else ""

    # ── §9 建议 ──────────────────────
    def _render_guidance(self, h) -> str:
        # 建议/警示同样不在 HeluoResult，需要 compute.heluo_guidance。
        # fallback：从 guajie.summary / guajie.evidence 抓尾段
        gj = h.guajie or {}
        summary = _safe(gj.get("summary"))
        lines = []
        if summary:
            lines.append(f"总览：{summary}")
        evs = gj.get("evidence") or []
        # 抓含有「建议」字样的
        for e in evs:
            if "建议" in e or "警示" in e or "禄神" in e or "元辰" in e:
                lines.append(f"  · {_truncate(str(e), 220)}")
        return "§9 总结\n" + "\n".join(lines) if lines else ""