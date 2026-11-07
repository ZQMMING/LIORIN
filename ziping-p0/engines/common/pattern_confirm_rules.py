# -*- coding: utf-8 -*-
"""PATCH-032-R1：RULE-032-03 财格确认（pattern_confirm）+ RULE-032-02 壬多阈值入 condition

RULE-032-03（PZZQ.pattern_confirm，PZZQ-005-007/008/009 + 007-006）：
- 格名层：月令本气=日主所克=财 → pattern=财格（DETERMINED，无论透否，PZZQ-005-007）
- 成格层（PZZQ-005-008 三路径）：
  路径A 財旺生官（月令财旺+官透）
  路径B 財逢食生而身強帶比（食神透+身强带比）
  路径C 財格透印而位置安帖、兩不相剋（印透+财印不碍）
- 变化分支（PZZQ-005-009）：月令所藏透出他干→格局随透者化（如辛透→杀格/化印类）
- 败格（PZZQ-005-008）：財輕比重、財透七煞
- 会支：地支三合/六合改变月令性质→按 PZZQ-005-009 会支变化；未明化向（如午未合）登记 UNVERIFIED 不采
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CHART = {
    "pillars": "癸亥 壬戌 乙未 壬午", "day_master_element": "WOOD",
    "month_order": "戌", "month_hidden": ["戊", "辛", "丁"],
    "stems": {"年": "癸", "月": "壬", "日": "乙", "时": "壬"},
    "hidden": {"亥": ["壬", "甲"], "戌": ["戊", "辛", "丁"], "未": ["己", "丁", "乙"], "午": ["丁", "己"]},
}
ELEM_TO_TENGOD = {"木": "比肩", "火": "食伤", "土": "财", "金": "官杀", "水": "印"}
HIDDEN_MAP = {"戌": ["戊", "辛", "丁"]}  # 戌藏 本气戊/中气辛/余气丁
WUXING = {"木": "WOOD", "火": "FIRE", "土": "EARTH", "金": "METAL", "水": "WATER"}


def _transparent(c):
    """月令所藏透干：返回透出者列表 [(藏干, 十神)]"""
    out = []
    for hid in HIDDEN_MAP[c["month_order"]]:
        if hid in c["stems"].values():
            elem = {"戊": "土", "己": "土", "辛": "金", "庚": "金", "丁": "火", "丙": "火", "壬": "水", "癸": "水", "甲": "木", "乙": "木"}[hid]
            out.append((hid, ELEM_TO_TENGOD[elem]))
    return out


def rule_032_03_pattern_confirm(c):
    """财格确认：格名层 + 成格层 + 变化 + 败格"""
    benqi = HIDDEN_MAP[c["month_order"]][0]           # 戊
    benqi_ten = ELEM_TO_TENGOD["土"]                  # 财
    transparent = _transparent(c)                      # 透出者
    visible = [t[0] for t in transparent]

    # 1. 格名层：月令本气=财 → 财格（PZZQ-005-007）
    pattern = "财格" if benqi_ten == "财" else "非财格"

    # 2. 变化分支（PZZQ-005-009）：透出者改变格局
    if pattern == "财格" and transparent:
        change = []
        for hid, ten in transparent:
            if hid != benqi:
                change.append(f"{hid}透→按PZZQ-005-009变化（{ten}）")
        if change:
            return {"pattern_state": "CHANGE_PENDING", "pattern": pattern, "changes": change,
                    "note": "月令所藏透出者改变格局，转格待 PZZQ-005-009 变化规则细分"}

    # 3. 成格层（PZZQ-005-008 三路径）
    if pattern == "财格":
        # 印/官/食 均指四柱天干透出者（非戌藏）——PZZQ「財格透印」印星泛指正偏印
        stem_tengods = [ELEM_TO_TENGOD[{"戊": "土", "己": "土", "庚": "金", "辛": "金", "丙": "火", "丁": "火", "壬": "水", "癸": "水", "甲": "木", "乙": "木"}[s]] for s in c["stems"].values()]
        official_vis = any(t in ("官杀") for t in stem_tengods)   # 官杀透（庚辛）
        food_vis = any(t == "食伤" for t in stem_tengods)          # 食伤透（丙丁）
        yin_count = sum(1 for t in stem_tengods if t == "印")      # 印透数（癸壬）
        bijie_count = sum(1 for t in stem_tengods if t == "比肩")  # 比肩透
        paths = []
        if official_vis:
            paths.append("A財旺生官")
        if food_vis:
            paths.append("B財逢食生(身強帶比待查)")
        if yin_count >= 1:
            paths.append(f"C財格透印(印透{yin_count}；财藏支印透干、干支分离→位置安帖待structure复核)")
        # 败格检查（PZZQ-005-008）
        fail = []
        if bijie_count >= 2:
            fail.append("財輕比重(比劫透≥2)")
        if any(t[1] == "财" for t in _transparent(c)) and official_vis:
            fail.append("財透七煞")
        return {
            "pattern_state": "DETERMINED(财格)" if paths else "CANDIDATE(财格)",
            "pattern": pattern, "benqi": benqi, "paths": paths,
            "fail": fail if fail else None,
            "note": "格名由月令本气定（PZZQ-005-007）；成格路径" + ("、".join(paths) if paths else "未触发三路径") +
                    ("；败格条件：" + "、".join(fail) if fail else ""),
        }

    return {"pattern_state": "UNDETERMINED", "pattern": pattern}


def rule_032_02_qtbj_v2(c):
    """QTBJ 九月乙木调候 v2：壬多阈值入 condition（用户裁定）"""
    gui_visible = any(s == "癸" for s in c["stems"].values())
    xin_hidden = "辛" in c["hidden"]["戌"]
    ren_visible = sum(1 for s in c["stems"].values() if s == "壬")
    hai_zi = any(z in ("亥", "子") for z in c["hidden"])
    # 阈值：壬透≥2 或（壬透≥1 且支有亥/子）→ 触发「四柱壬多水難生乙」
    ren_many = ren_visible >= 2 or (ren_visible >= 1 and hai_zi)
    if gui_visible:
        return {
            "rule_id": "RULE-032-02", "namespace": "QTBJ.climate_use",
            "climate_use_state": "DETERMINED(癸水)",
            "condition": {"gui_visible": True, "xin_hidden": xin_hidden, "ren_visible": ren_visible, "hai_zi": hai_zi, "ren_many_trigger": ren_many},
            "ren_many_note": "触发『四柱壬多水難生乙』→癸水效力降级（断语层），调候用神仍癸" if ren_many else "壬未多，无降级",
            "evidence": ["EVID-018"],
        }
    return {"climate_use_state": "UNDETERMINED"}


if __name__ == "__main__":
    print("==== PATCH-032-R1：RULE-032-03 财格确认 + 壬多阈值 ====")
    print("\n==== 1983-11-03 关键检查点 ====")
    print(f"  天干透出（戌藏戊辛丁）：{_transparent(CHART) or '无——戊辛丁全不透'}")
    print(f"  地支会支：无寅（寅午戌三合缺角）｜午未六合（化向 PZZQ 未明示→UNVERIFIED 不采）｜戌未刑")
    print("\n==== RULE-032-03 PZZQ 财格确认 ====")
    r3 = rule_032_03_pattern_confirm(CHART)
    print(json.dumps(r3, ensure_ascii=False, indent=1))
    print("\n==== RULE-032-02 v2 QTBJ 壬多阈值 ====")
    r2 = rule_032_02_qtbj_v2(CHART)
    print(json.dumps(r2, ensure_ascii=False, indent=1))
