# -*- coding: utf-8 -*-
"""禄命法 · 报告生成层 (纯视图, 不新增任何断语).

把 LumingChart 的确定性事实组织成"禄命法批断"报告结构:
  一、命盘纳音与神煞排定 (四柱/胎元/命宫身宫/神煞)
  二、原局断语 (吉凶分级)
  三、大运详批 (每运柱: 神煞临/合冲害刑/纳音三纲)
  四、太岁断语
  五、吉凶汇总 (原局/运/太岁 + 当前运 + overall)

硬约束:
  - 报告内容 100% 来自 lm.verdicts / lm.tone_scope / lm.to_dict() 排盘事实;
  - 不做原文之外的新推论 (如事业方向/健康建议等自由发挥);
  - rule_id/evidence/tone 原样透出, 保证可溯源;
  - 视图层只做 中文化/截断/排序, 不改判定数据。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

NAYIN_ELEMENT_CN = {
    "海中金": "金", "炉中火": "火", "大林木": "木", "路旁土": "土", "剑锋金": "金",
    "山头火": "火", "涧下水": "水", "城头土": "土", "白蜡金": "金", "杨柳木": "木",
    "泉中水": "水", "屋上土": "土", "霹雳火": "火", "松柏木": "木", "长流水": "水",
    "沙中金": "金", "山下火": "火", "平地木": "木", "壁上土": "土", "金箔金": "金",
    "覆灯火": "火", "天河水": "水", "大驿土": "土", "钗钏金": "金", "桑柘木": "木",
    "大溪水": "水", "沙中土": "土", "天上火": "火", "石榴木": "木", "大海水": "水",
}
STEM_CN = {"JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁", "WU": "戊",
           "JI": "己", "GENG": "庚", "XIN": "辛", "REN": "壬", "GUI": "癸"}
BRANCH_CN = {"ZI": "子", "CHOU": "丑", "YIN": "寅", "MAO": "卯", "CHEN": "辰", "SI": "巳",
             "WU": "午", "WEI": "未", "SHEN": "申", "YOU": "酉", "XU": "戌", "HAI": "亥"}
WX_CN = {"WOOD": "木", "FIRE": "火", "EARTH": "土", "METAL": "金", "WATER": "水"}
STEMS10 = ["JIA", "YI", "BING", "DING", "WU", "JI", "GENG", "XIN", "REN", "GUI"]
BRANCHES12 = ["ZI", "CHOU", "YIN", "MAO", "CHEN", "SI", "WU", "WEI", "SHEN", "YOU", "XU", "HAI"]

# 60 甲子成对中文映射 (先于单 token, 解决 WU=天干戊/地支午 歧义)
_60_PAIRS = {
    STEMS10[i % 10] + BRANCHES12[i % 12]:
        STEM_CN[STEMS10[i % 10]] + BRANCH_CN[BRANCHES12[i % 12]]
    for i in range(60)
}
# 中文上下文里 \b 词边界失效 (CJK 字符算 \w), 改用前后非 A-Z 断言
# 三合组英文连写 (engine 按地支序 sorted, 如 MAOWEIHAI=亥卯未) 非 60 甲子对, 单独映射
_SANHE_SETS = {("ZI", "CHEN", "SHEN"): "申子辰", ("MAO", "WEI", "HAI"): "亥卯未",
               ("YIN", "WU", "XU"): "寅午戌", ("CHOU", "SI", "YOU"): "巳酉丑"}
_SANHE_CN = {"".join(sorted(grp, key=BRANCHES12.index)): cn
             for grp, cn in _SANHE_SETS.items()}
_SANHE_RE = re.compile(r"(?<![A-Z])(" + "|".join(_SANHE_CN) + r")(?![A-Z])")
_PAIR_RE = re.compile(r"(?<![A-Z])(" + "|".join(sorted(_60_PAIRS, key=len, reverse=True))
                      + r")(?![A-Z])")
_BRANCH_RE = re.compile(r"(?<![A-Z])(" + "|".join(sorted(BRANCHES12, key=len, reverse=True))
                        + r")(?![A-Z])")
_STEM_RE = re.compile(r"(?<![A-Z])(" + "|".join(sorted(STEMS10, key=len, reverse=True))
                      + r")(?![A-Z])")
_WX_RE = re.compile(r"(?<![A-Z])(" + "|".join(sorted(WX_CN, key=len, reverse=True))
                    + r")(?![A-Z])")


def _zh(s: str) -> str:
    """detail/断语中英文干支·五行·三合组 → 中文 (前后非字母断言, 60甲子优先)."""
    if not s:
        return s
    s = _SANHE_RE.sub(lambda m: _SANHE_CN[m.group(1)], s)
    s = _PAIR_RE.sub(lambda m: _60_PAIRS[m.group(1)], s)
    s = _BRANCH_RE.sub(lambda m: BRANCH_CN[m.group(1)], s)
    s = _STEM_RE.sub(lambda m: STEM_CN[m.group(1)], s)
    s = _WX_RE.sub(lambda m: WX_CN[m.group(1)], s)
    return s


def _clip(s: str, n: int = 64) -> str:
    s = s.strip()
    return s if len(s) <= n else s[:n] + "…"


def _gz(stem: str, branch: str) -> str:
    return f"{STEM_CN.get(stem, stem)}{BRANCH_CN.get(branch, branch)}"


def build_report(lm: Any) -> Dict[str, Any]:
    """LumingChart → 报告结构 (纯视图)."""
    d = lm.to_dict()
    verdicts = list(lm.verdicts)
    ts = lm.tone_scope

    # 一、命盘
    pillars = d.get("four_pillars", [])
    nayin = d.get("nayin", {})
    pos_names = ("年", "月", "日", "时")
    pos_keys = ("year", "month", "day", "hour")
    four = []
    for i, p in enumerate(pillars):
        nk = pos_keys[i]
        four.append({
            "pos": pos_names[i],
            "gz": _gz(p[0], p[1]),
            "nayin": nayin.get(nk, ""),
            "element": NAYIN_ELEMENT_CN.get(nayin.get(nk, ""), ""),
        })
    nc = d.get("nayin_chain", {})
    tai = nc.get("tai_yuan", {}) or {}
    gong = nc.get("gong", {}) or {}
    ming_gong = gong.get("ming", {}) or {}
    shen_gong = gong.get("shen", {}) or {}
    luck_scope = d.get("luck_scope", {}) or {}
    start_age = luck_scope.get("start_age", 0) or 0
    paiban = {
        "four": four,
        "tai_yuan": _gz(tai.get("stem", ""), tai.get("branch", "")),
        "tai_yuan_nayin": tai.get("nayin", ""),
        "ming_gong": ming_gong.get("pillar", ""),
        "ming_gong_nayin": ming_gong.get("nayin", ""),
        "ming_gong_algorithm": ming_gong.get("algorithm", ""),
        "shen_gong": shen_gong.get("pillar", ""),
        "shen_gong_nayin": shen_gong.get("nayin", ""),
        "start_age": round(start_age, 1),
        "first_luck": (luck_scope.get("pillars", [{}])[0] or {}).get("stem", "") +
                      (luck_scope.get("pillars", [{}])[0] or {}).get("branch", ""),
    }

    # 神煞集解 (确定性事实; 视图层中文化)
    ss = d.get("shen_sha", {})
    san_yuan = d.get("san_yuan", {})
    lu_ma = d.get("lu_ma", {})
    gui_ren = d.get("gui_ren", {}).get("by_year", {})
    wen_chang = d.get("wen_chang", {})
    lu_info = lu_ma.get("lu", {})
    lu_branch_cn = BRANCH_CN.get(lu_info.get("lu_branch", ""), "")
    lu_present = bool(lu_info.get("present"))
    tao_branch = ss.get("tao_hua", {}).get("branch", "")
    tao_present = bool(ss.get("tao_hua", {}).get("present"))
    ming_w = san_yuan.get("ming", {}).get("month_wang_shuai", "")
    shen_w = san_yuan.get("shen", {}).get("month_wang_shuai", "")
    ming_g = san_yuan.get("ming", {}).get("growth_stage", "")
    shen_g = san_yuan.get("shen", {}).get("growth_stage", "")
    san_xing_cn = [f"{s['type']}({'、'.join(BRANCH_CN.get(b, b) for b in s['branches'])})"
                   for s in d.get("san_xing", [])]
    liu_hai_cn = [f"{BRANCH_CN.get(h[0], h[0])}害{BRANCH_CN.get(h[1], h[1])}"
                  for h in d.get("liu_hai", [])]
    shen_sha = {
        # 2026-10-21 双坐标标注: 月令旺衰 vs 十二宫, 消除"命死/身死 vs 临官"歧义
        "三元旺衰": f"月令[命{ming_w}/身{shen_w}]；十二宫[命{ming_g}/身{shen_g}]"
                    if (ming_w or shen_w) else "",
        "干禄": f"{lu_branch_cn}（{'临支' if lu_present else '不临'}）" if lu_branch_cn else "",
        "驿马": BRANCH_CN.get(lu_ma.get("ma", {}).get("branch", ""), ""),
        "贵人": BRANCH_CN.get(gui_ren.get("gui_ren_branch", ""), "") if gui_ren.get("present") else "",
        "华盖": BRANCH_CN.get(ss.get("hua_gai", {}).get("branch", ""), ""),
        "桃花": (f"{BRANCH_CN.get(tao_branch, '')}（{'现' if tao_present else '不现'}）"
                if tao_branch else ""),
        "魁罡": "、".join((ss.get("kui_gang", {}) or {}).get("days", [])) or "",
        "文昌": BRANCH_CN.get(wen_chang.get("branch", ""), "") if wen_chang.get("present") else "",
        "三刑": san_xing_cn,
        "六害": liu_hai_cn,
    }

    # 二、原局断语
    yuan_ju = [v for v in verdicts if v["scope"] == "原局"]

    # 三、大运详批
    pillars_view = {p["stem"] + p["branch"]: p for p in
                    (d.get("luck_scope", {}).get("pillars", []))}
    luck_rows = []
    for _i, _p in enumerate(d.get("luck_pillars", [])):
        gz = _p[0] + _p[1]
        pv = pillars_view.get(gz, {})
        p_verdicts = [v for v in verdicts if v["scope"] == "运" and v["target"] == gz]
        sees = []
        for flag, name in ((pv.get("sees_gui_ren"), "见贵人"), (pv.get("sees_lu"), "见禄"),
                           (pv.get("sees_ma"), "见驿马"), (pv.get("sees_hua_gai"), "见华盖"),
                           (pv.get("sees_tao_hua"), "见咸池"), (pv.get("sees_jiang_xing"), "见将星")):
            if flag:
                sees.append(name)
        tones = [v["tone"] for v in p_verdicts]
        # 吉凶列: 固定顺序 吉→凶→平→滞 (含空=无断语; 滞=十二宫败衰病/沐浴等迟滞信号)
        tone_summary = "、".join(f"{t}{tones.count(t)}" for t in ("吉", "凶", "平", "滞")
                                 if tones.count(t)) or "—"
        luck_rows.append({
            "gz": _gz(_p[0], _p[1]),
            "age_range": f"{round(start_age + _i * 10, 1)}-{round(start_age + _i * 10 + 9, 1)}岁",
            "nayin": pv.get("nayin", ""),
            "nayin_relation": pv.get("nayin_relation", ""),
            "shier_gong": pv.get("shier_gong", ""),
            "gan_rel": pv.get("gan_rel", ""),
            "zhi_rel": pv.get("zhi_rel", ""),
            "sees": "、".join(sees),
            "verdicts": [{"tone": v["tone"], "out": v["out"], "detail": v["detail"]}
                         for v in p_verdicts],
            "tone_summary": tone_summary,
        })

    # 四、太岁
    tai_sui = [v for v in verdicts if v["scope"] == "太岁"]
    # 二运喜会/厄会 (V23/V24/V25: target='大运{D}', 非柱名)
    er_yun = [v for v in verdicts if v["scope"] == "运" and v["target"].startswith("大运")]

    # 五、吉凶汇总 (tone_scope 结构: current={pillar,verdict,counts} overall={counts,verdict})
    cur = ts.get("current", {})
    ov = ts.get("overall", {})
    hui_zong = {
        "layers": {k: {"吉": v["吉"], "凶": v["凶"], "平": v["平"], "滞": v["滞"]}
                   for k, v in ts.get("layers", {}).items()},
        "current_pillar": cur.get("pillar", ""),
        "current_counts": cur.get("counts", {}),
        "current_verdict": cur.get("verdict", ""),
        "overall_counts": ov.get("counts", {}),
        "overall_verdict": ov.get("verdict", ""),
    }

    return {
        "paiban": paiban,
        "shen_sha": shen_sha,
        "yuan_ju": [{"tone": v["tone"], "out": v["out"], "detail": v["detail"],
                     "evidence": v["evidence"]} for v in yuan_ju],
        "luck": luck_rows,
        "er_yun": [{"tone": v["tone"], "out": v["out"], "detail": v["detail"],
                    "target": v["target"]} for v in er_yun],
        "tai_sui": [{"tone": v["tone"], "out": v["out"], "detail": v["detail"]}
                    for v in tai_sui],
        "hui_zong": hui_zong,
        "luck_scope": {"current_year": luck_scope.get("current_year", 0),
                       "current_luck_branch": luck_scope.get("current_luck_branch", ""),
                       "xiaoyun_zhi": luck_scope.get("xiaoyun_zhi", "")},
    }


def render_markdown(report: Dict[str, Any], gender: str = "") -> str:
    """报告结构 → Markdown (对齐'禄命法批断'惯用格式)."""
    lines: List[str] = []
    lines.append("# 禄命法批断")
    if gender:
        lines.append(f"性别: {gender}")
    lines.append("")

    # 一、命盘
    lines.append("## 一、命盘纳音与神煞排定")
    lines.append("")
    lines.append("| 柱位 | 干支 | 纳音 | 五行 |")
    lines.append("| --- | --- | --- | --- |")
    p = report["paiban"]
    for f in p["four"]:
        lines.append(f"| {f['pos']} | {f['gz']} | {f['nayin']} | {f['element']} |")
    lines.append(f"| 胎元 | {p['tai_yuan']} | {p['tai_yuan_nayin']} |"
                 f" {NAYIN_ELEMENT_CN.get(p['tai_yuan_nayin'], '')} |")
    lines.append(f"| 命宫 | {p['ming_gong']} | {p['ming_gong_nayin']} |"
                 f" {NAYIN_ELEMENT_CN.get(p['ming_gong_nayin'], '')} |")
    lines.append(f"| 身宫 | {p['shen_gong']} | {p['shen_gong_nayin']} |"
                 f" {NAYIN_ELEMENT_CN.get(p['shen_gong_nayin'], '')} |")
    lines.append("")
    if p.get("start_age") is not None:
        lines.append(f"> 起运: {p['start_age']}岁交第一步大运 {p.get('first_luck', '')}"
                     f"（阳男阴女顺行/阴男阳女逆行，折除以三日为年）")
        lines.append("")
    lines.append("> 命宫/身宫算法: 五行精纪起命宫例(太阳加时顺数见卯)与太阴星宫法"
                 "（WXJJ L3736-3739，与三命通会 L2679-2683 互证），非袁树珊月数法。"
                 "验算例: 原文'甲子年三月戌时'起得丁卯宫，与本算法输出一致。")
    lines.append("")
    lines.append("神煞集解:")
    ss = report["shen_sha"]
    for k, v in ss.items():
        if isinstance(v, list):
            v = "、".join(v)
        if v not in ("", [], False):
            lines.append(f"- {k}: {v}")
    lines.append("")

    # 二、原局断语
    lines.append("## 二、原局断语（吉凶分级）")
    lines.append("")
    if report["yuan_ju"]:
        for v in report["yuan_ju"]:
            lines.append(f"- [{v['tone']}] {_clip(_zh(v['out']))}（{_clip(_zh(v['detail']))}）")
    else:
        lines.append("- （无）")
    lines.append("")

    # 三、大运详批
    lines.append("## 三、大运详批")
    lines.append("")
    lines.append("| 大运 | 岁数 | 纳音 | 生克 | 十二宫 | 干支纲 | 断语 | 吉凶 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in report["luck"]:
        details = "；".join(_clip(_zh(v["detail"])) for v in r["verdicts"])
        sees = r["sees"]
        gan_zhi = f"{_zh(r['gan_rel'])}/{_zh(r['zhi_rel'])}" if r["gan_rel"] else ""
        duan = details if not sees else f"{sees}；{details}"
        lines.append(f"| {r['gz']} | {r['age_range']} | {r['nayin']} | {r['nayin_relation']} |"
                     f" {r['shier_gong']} | {gan_zhi} | {duan} | {r['tone_summary']} |")
    lines.append("")

    # 四、太岁
    lines.append("## 四、太岁断语")
    lines.append("")
    if report["tai_sui"]:
        for v in report["tai_sui"]:
            lines.append(f"- [{v['tone']}] {_clip(_zh(v['out']))}（{_clip(_zh(v['detail']))}）")
    else:
        lines.append("- （当前视角太岁无触发断语；逐年太岁断语见报告末流年表，逐年按大运×太岁×小运完整展开）")
    lines.append("")

    # 二运喜会/厄会 (大运×小运)
    if report["er_yun"]:
        lines.append("## 五、二运喜会/厄会（大运×小运）")
        lines.append("")
        # 当前视角年份+大运×小运 (2026-10-21 用户第三轮: 厄会须落到具体条目)
        ls2 = (report.get("luck_scope") or {})
        _cy = ls2.get("current_year") or 0
        _dl2 = BRANCH_CN.get(ls2.get("current_luck_branch", ""), "")
        _xy2 = BRANCH_CN.get(ls2.get("xiaoyun_zhi", ""), "")
        _yr_tag = f"（{_cy} 视角: 大运{_dl2}×小运{_xy2}触发）" if _cy else ""
        for v in report["er_yun"]:
            lines.append(f"- [{v['tone']}] {_clip(_zh(v['out']))}"
                         f"（{_clip(_zh(v['detail']))}{_yr_tag}；按流年逐年见报告末流年表）")
        lines.append("")

    # 吉凶汇总
    lines.append(f"## {'六' if report['er_yun'] else '五'}、吉凶汇总")
    lines.append("")
    hz = report["hui_zong"]
    lines.append("| 层 | 吉 | 凶 | 平 | 滞 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for k in ("原局", "运", "太岁"):
        c = hz["layers"].get(k, {"吉": 0, "凶": 0, "平": 0, "滞": 0})
        lines.append(f"| {k} | {c['吉']} | {c['凶']} | {c['平']} | {c['滞']} |")
    lines.append("")
    lines.append("> 注：运层计数含二运视角断语（大运×小运厄会，不入单柱行）与十二宫滞信号；逐柱行已按同口径列出滞数。"
                 "本例运层凶17 = 逐柱凶16 + 二运厄会（LM-V24 厄会②，运层视角计1条）。")
    cc = hz["current_counts"]
    oc = hz["overall_counts"]
    # 2026-10-20 原著措辞统一 (L4276): 偏吉→吉 / 吉凶相当→吉凶相杂 / 偏凶→凶
    _gx = {"偏吉": "吉", "吉凶相当": "吉凶相杂", "偏凶": "凶"}
    _cv = _gx.get(hz["current_verdict"], hz["current_verdict"])
    _ov = _gx.get(hz["overall_verdict"], hz["overall_verdict"])
    lines.append(f"当前大运: {_zh(hz['current_pillar'])}"
                 f"（吉 {cc.get('吉', 0)} · 凶 {cc.get('凶', 0)}"
                 f" · 平 {cc.get('平', 0)} · 滞 {cc.get('滞', 0)} → {_cv}）")
    lines.append(f"总体: 吉 {oc.get('吉', 0)} · 凶 {oc.get('凶', 0)}"
                 f" · 平 {oc.get('平', 0)} · 滞 {oc.get('滞', 0)} → {_ov}")
    lines.append("")
    return "\n".join(lines)
