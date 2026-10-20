"""Z78: 《紫微斗数全书》经典格局母表——Evidence/Rule 录入层。

来源：本地《紫微斗数全书_完整原文.txt》卷一/卷二
分类：
- WEALTH_PATTERN (富局)
- NOBILITY_PATTERN (贵局)
- POVERTY_PATTERN (贫贱局)
- MISC_PATTERN (杂局)
- PALACE_FORTUNE_RULE (十二宫得地合格诀)
- PALACE_DEPRIVATION_RULE (十二宫失陷破格诀)

5条硬规矩：
1. 不把格局名当结论——每条有 conditions/supporting_stars/breaking_conditions
2. 成格条件机器可验证——消费 palace_relationship.py
3. 破格独立——breaking_conditions 与 formation_conditions 分开
4. school=CLASSICAL_SOURCE——不混南北派
5. 12×2逐宫诀做 RULE 不做 PATTERN

Z80-H 接线（2026-10-15）：本模块资产已接入生产 —— 落点 classical_detail.palace_jue + classical_detail.classical_patterns（build_answer 顶层键 classical_detail，独立通道，
  不并入 12 宫位维/体用层）。
  依据：docs/audit/ZIWEI_ENGINE_FULL_AUDIT_20261014.md（Z80-H 收口）
"""
from __future__ import annotations

SRC = "紫微斗数全书·卷一"
SRC2 = "紫微斗数全书·卷二"

# ============================================================
# WEALTH_PATTERN (富局) 6条
# ============================================================
WEALTH_PATTERN = [
    {
        "pattern_id": "WEALTH-01",
        "pattern_name": "财荫夹印",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "富局第十六",
        "verbatim": "财荫夹印，相守命武梁来夹是也，田宅宫亦然。",
        "formation_conditions": ["命宫(或田宅宫)有武曲+天相"],
        "supporting_stars": ["武曲", "天相"],
        "breaking_conditions": ["空亡"],
        "note": "武梁夹印，主财荫",
    },
    {
        "pattern_id": "WEALTH-02",
        "pattern_name": "日月夹财",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "富局第十六",
        "verbatim": "日月夹财，武守命日月来夹是也，财帛宫亦然。",
        "formation_conditions": ["命宫(或财帛宫)有武曲", "太阳太阴在夹宫"],
        "supporting_stars": ["武曲", "太阳", "太阴"],
        "breaking_conditions": ["空亡"],
    },
    {
        "pattern_id": "WEALTH-03",
        "pattern_name": "财禄夹马",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "富局第十六",
        "verbatim": "财禄夹马，马守命武禄来夹是也，逢生旺尤妙。",
        "formation_conditions": ["命宫有天马", "武曲+禄存来夹"],
        "supporting_stars": ["天马", "武曲", "禄存"],
        "breaking_conditions": ["空亡", "马落空亡"],
    },
    {
        "pattern_id": "WEALTH-04",
        "pattern_name": "荫印拱身",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "富局第十六",
        "verbatim": "荫印拱身，身临田宅梁相拱冲是也，勿坐空亡。",
        "formation_conditions": ["身宫在田宅", "天梁+天相对拱"],
        "supporting_stars": ["天梁", "天相"],
        "breaking_conditions": ["空亡"],
    },
    {
        "pattern_id": "WEALTH-05",
        "pattern_name": "日月照璧",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "富局第十六",
        "verbatim": "日月照璧，日月临田宅宫是也，喜居墓库。",
        "formation_conditions": ["田宅宫有太阳+太阴"],
        "supporting_stars": ["太阳", "太阴"],
        "breaking_conditions": ["反背"],
    },
    {
        "pattern_id": "WEALTH-06",
        "pattern_name": "金灿光辉",
        "school": "CLASSICAL_SOURCE",
        "source": SRC,
        "source_section": "富局第十六",
        "verbatim": "金灿光辉，太阳单守，命在午宫是也。",
        "formation_conditions": ["命宫在午", "太阳单守命宫"],
        "supporting_stars": ["太阳"],
        "breaking_conditions": ["空亡", "巨暗同宫"],
    },
]

# ============================================================
# NOBILITY_PATTERN (贵局) 27条（NOB-01~27；Z80-G 实测校准）
# ============================================================
NOBILITY_PATTERN = [
    {"pattern_id": "NOB-01", "pattern_name": "日月夹命", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "日月夹命，不坐空亡遇逢本宫有吉星是也。",
     "formation_conditions": ["命宫被太阳太阴夹"], "supporting_stars": ["太阳","太阴"], "breaking_conditions": ["空亡"]},
    {"pattern_id": "NOB-02", "pattern_name": "日出扶桑", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "日出扶桑，日在卯守命是也，守官禄宫亦然。",
     "formation_conditions": ["命宫在卯", "太阳守命"], "supporting_stars": ["太阳"], "breaking_conditions": ["空亡","巨暗"]},
    {"pattern_id": "NOB-03", "pattern_name": "月落亥宫(月朗天门)", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "月落亥宫，月在亥守命是也，又名月朗天门。",
     "formation_conditions": ["命宫在亥", "太阴守命"], "supporting_stars": ["太阴"], "breaking_conditions": ["空亡"]},
    {"pattern_id": "NOB-04", "pattern_name": "月生沧海", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "月生沧海，月在子宫守田宅是也。",
     "formation_conditions": ["田宅宫在子", "太阴守田宅"], "supporting_stars": ["太阴"], "breaking_conditions": ["空亡"]},
    {"pattern_id": "NOB-05", "pattern_name": "辅弼拱主", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "辅弼拱主，紫微守命二星来拱是也，夹之亦然。",
     "formation_conditions": ["紫微守命", "左辅右弼拱夹"], "supporting_stars": ["紫微","左辅","右弼"], "breaking_conditions": ["空亡"]},
    {"pattern_id": "NOB-06", "pattern_name": "君臣庆会", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "君臣庆会，紫微左右同守命是也，更会相武阴妙上。",
     "formation_conditions": ["紫微+左辅+右弼同守命"], "supporting_stars": ["紫微","左辅","右弼"], "breaking_conditions": ["空亡"]},
    {"pattern_id": "NOB-07", "pattern_name": "财印夹禄", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "财印夹禄，禄守命梁相来夹是也，入财亦然。",
     "formation_conditions": ["禄存守命", "天梁+天相夹"], "supporting_stars": ["禄存","天梁","天相"], "breaking_conditions": ["空亡"]},
    {"pattern_id": "NOB-08", "pattern_name": "禄马佩印", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "禄马佩印，马前有禄印星同宫是也。",
     "formation_conditions": ["命宫有天马", "禄存+天相同宫"], "supporting_stars": ["天马","禄存","天相"], "breaking_conditions": ["空亡"]},
    {"pattern_id": "NOB-09", "pattern_name": "坐贵向贵", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "坐贵向贵，谓魁钺在命迭相坐拱是也。",
     "formation_conditions": ["天魁天钺坐拱命宫"], "supporting_stars": ["天魁","天钺"], "breaking_conditions": ["空亡"]},
    {"pattern_id": "NOB-10", "pattern_name": "马头带剑", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "马头带剑，谓马有刃是也，居午格。",
     "formation_conditions": ["命宫在午", "天马+擎羊同宫"], "supporting_stars": ["天马","擎羊"], "breaking_conditions": []},
    {"pattern_id": "NOB-11", "pattern_name": "七杀朝斗", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "七杀朝斗爵禄荣昌；七杀寅申子午一生爵禄荣昌，为七杀朝斗格。",
     "formation_conditions": ["七杀守命在寅申子辰"], "supporting_stars": ["七杀"], "breaking_conditions": ["空亡","羊陀夹"]},
    {"pattern_id": "NOB-12", "pattern_name": "日月并明", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "日月并明，佐九重于尧殿。",
     "formation_conditions": ["太阳在午", "太阴在子", "同守命/三方"], "supporting_stars": ["太阳","太阴"], "breaking_conditions": ["反背"]},
    {"pattern_id": "NOB-13", "pattern_name": "明珠出海", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "明珠出海，太阴居亥卯未，太阳对照，文星得地。",
     "formation_conditions": ["太阴守命在亥卯未"], "supporting_stars": ["太阴"], "breaking_conditions": ["空亡"]},
    {"pattern_id": "NOB-14", "pattern_name": "日月同临", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "日月同临，官居侯伯。",
     "formation_conditions": ["太阳太阴同宫守命"], "supporting_stars": ["太阳","太阴"], "breaking_conditions": ["反背"]},
    {"pattern_id": "NOB-15", "pattern_name": "刑囚夹印", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "刑囚夹印，天刑廉贞同临身命主武勇之人。",
     "formation_conditions": ["天刑+廉贞同守身命"], "supporting_stars": ["天刑","廉贞"], "breaking_conditions": []},
    {"pattern_id": "NOB-16", "pattern_name": "科权禄拱", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "科权禄拱，定为扳桂之高人，名誉昭彰。",
     "formation_conditions": ["生年化禄+化权+化科三方拱命"], "supporting_stars": [], "sihua_required": ["禄","权","科"], "breaking_conditions": ["化忌冲"]},
    {"pattern_id": "NOB-17", "pattern_name": "贪火相逢", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "贪火相逢，谓二星守命同居庙旺是也。",
     "formation_conditions": ["贪狼+火星同守命庙旺"], "supporting_stars": ["贪狼","火星"], "breaking_conditions": ["落陷"]},
    {"pattern_id": "NOB-18", "pattern_name": "武曲守垣", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "武曲守垣，武守命卯宫是也，余不是。",
     "formation_conditions": ["命宫在卯", "武曲守命"], "supporting_stars": ["武曲"], "breaking_conditions": []},
    {"pattern_id": "NOB-19", "pattern_name": "府相朝垣", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "府相朝垣命必荣，千锺食禄；命寅申，府相在财帛宫，禄官朝者，上格。",
     "formation_conditions": ["天府+天相三方朝拱命宫"], "supporting_stars": ["天府","天相"], "breaking_conditions": ["空亡"]},
    {"pattern_id": "NOB-20", "pattern_name": "紫府朝垣", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "紫府朝垣食禄万钟，终身福厚至三公；命坐寅申再加吉星妙。",
     "formation_conditions": ["紫微+天府三方朝拱命宫"], "supporting_stars": ["紫微","天府"], "breaking_conditions": ["空亡"]},
    {"pattern_id": "NOB-21", "pattern_name": "文星暗拱", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "文星暗拱，贾谊允矣登科。",
     "formation_conditions": ["文昌文曲三方暗拱命宫"], "supporting_stars": ["文昌","文曲"], "breaking_conditions": []},
    {"pattern_id": "NOB-22", "pattern_name": "权禄生逢", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "权禄生逢，二星守命庙旺是也，陷不是。",
     "formation_conditions": ["生年化权+化禄守命庙旺"], "supporting_stars": [], "sihua_required": ["权","禄"], "breaking_conditions": ["落陷","空亡"]},
    {"pattern_id": "NOB-23", "pattern_name": "羊刃入庙", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "羊刃入庙，辰戌丑未守命遇吉是也。",
     "formation_conditions": ["擎羊守命在辰戌丑未", "遇吉曜"], "supporting_stars": ["擎羊"], "breaking_conditions": []},
    {"pattern_id": "NOB-24", "pattern_name": "巨机居卯", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "巨机居卯，乙辛己丙至公卿，不贵即富；甲人平常，因甲禄到寅卯宫有擎羊破格。",
     "formation_conditions": ["巨门+天机同守命在卯"], "supporting_stars": ["巨门","天机"], "breaking_conditions": ["羊陀冲"]},
    {"pattern_id": "NOB-25", "pattern_name": "明禄暗禄", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "明禄暗禄，锦上添花，位至公卿。",
     "formation_conditions": ["禄存+生年化禄明见暗拱"], "supporting_stars": ["禄存"], "sihua_required": ["禄"], "breaking_conditions": []},
    {"pattern_id": "NOB-26", "pattern_name": "金舆扶驾", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "金舆扶驾，紫微守命前后有日月来夹是也。",
     "formation_conditions": ["紫微守命", "太阳太阴前后夹"], "supporting_stars": ["紫微","太阳","太阴"], "breaking_conditions": ["空亡"]},
    {"pattern_id": "NOB-27", "pattern_name": "科明暗禄", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贵局第十七",
     "verbatim": "科明禄暗，位列三台。",
     "formation_conditions": ["化科明见", "化禄暗拱"], "supporting_stars": [], "sihua_required": ["科","禄"], "breaking_conditions": ["空亡"]},
]

# ============================================================
# POVERTY_PATTERN (贫贱局) 8条
# ============================================================
POVERTY_PATTERN = [
    {"pattern_id": "POV-01", "pattern_name": "生不逢时", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贫贱局第十八",
     "verbatim": "生不逢时，命坐空亡逢廉贞是也。",
     "formation_conditions": ["命宫空亡", "廉贞守命"], "supporting_stars": ["廉贞"], "breaking_conditions": ["吉解"]},
    {"pattern_id": "POV-02", "pattern_name": "禄逢两杀", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贫贱局第十八",
     "verbatim": "禄逢两杀，禄坐空亡又逢空劫杀星是也。",
     "formation_conditions": ["禄存坐空亡", "地空地劫杀星同宫"], "supporting_stars": ["禄存","地空","地劫"], "breaking_conditions": []},
    {"pattern_id": "POV-03", "pattern_name": "马落空亡", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贫贱局第十八",
     "verbatim": "马落空亡，马既落亡虽禄冲会无用主奔波。",
     "formation_conditions": ["天马落空亡"], "supporting_stars": ["天马"], "breaking_conditions": ["禄存同宫解"]},
    {"pattern_id": "POV-04", "pattern_name": "日月藏辉", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贫贱局第十八",
     "verbatim": "日月藏辉，日月反背又逢巨暗是也。",
     "formation_conditions": ["太阳太阴反背", "巨门暗曜同会"], "supporting_stars": ["太阳","太阴","巨门"], "breaking_conditions": []},
    {"pattern_id": "POV-05", "pattern_name": "财与囚仇", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贫贱局第十八",
     "verbatim": "财与囚仇，武贞同守身命是也。",
     "formation_conditions": ["武曲+廉贞同守身命"], "supporting_stars": ["武曲","廉贞"], "breaking_conditions": []},
    {"pattern_id": "POV-06", "pattern_name": "一生孤贫", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贫贱局第十八",
     "verbatim": "一生孤贫，谓破守命星陷地是也。",
     "formation_conditions": ["破军守命落陷"], "supporting_stars": ["破军"], "breaking_conditions": []},
    {"pattern_id": "POV-07", "pattern_name": "君子在野", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贫贱局第十八",
     "verbatim": "君子在野，谓四杀守身命而言临陷地是也。",
     "formation_conditions": ["羊陀火铃四杀守身命陷地"], "supporting_stars": ["擎羊","陀罗","火星","铃星"], "breaking_conditions": []},
    {"pattern_id": "POV-08", "pattern_name": "两重华盖", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "贫贱局第十八",
     "verbatim": "两重华盖，谓禄存化禄坐命遇空劫是也。",
     "formation_conditions": ["禄存+化禄坐命", "遇地空地劫"], "supporting_stars": ["禄存","地空","地劫"], "breaking_conditions": []},
]

# ============================================================
# MISC_PATTERN (杂局) 8条
# ============================================================
MISC_PATTERN = [
    {"pattern_id": "MISC-01", "pattern_name": "风云际会", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "杂局第十九",
     "verbatim": "风云际会，身命虽弱二限逢禄马是也。",
     "formation_conditions": ["身命弱", "二限逢禄存天马"], "supporting_stars": ["禄存","天马"], "breaking_conditions": []},
    {"pattern_id": "MISC-02", "pattern_name": "锦上添花", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "杂局第十九",
     "verbatim": "锦上添花，谓限破恶星而行吉地是也。",
     "formation_conditions": ["本命限破恶星", "行运入吉地"], "supporting_stars": [], "breaking_conditions": []},
    {"pattern_id": "MISC-03", "pattern_name": "禄衰马困", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "杂局第十九",
     "verbatim": "禄衰马困，限逢七杀禄马空亡是也。",
     "formation_conditions": ["行限逢七杀", "禄马空亡"], "supporting_stars": ["七杀","禄存","天马"], "breaking_conditions": []},
    {"pattern_id": "MISC-04", "pattern_name": "衣锦还乡", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "杂局第十九",
     "verbatim": "衣锦还乡，少年不遂四十后行墓运是也。",
     "formation_conditions": ["少年不遂", "四十后行墓库运"], "supporting_stars": [], "breaking_conditions": []},
    {"pattern_id": "MISC-05", "pattern_name": "步数无依", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "杂局第十九",
     "verbatim": "步数无依，前限接后限连绵不分是也。",
     "formation_conditions": ["前后限连绵"], "supporting_stars": [], "breaking_conditions": []},
    {"pattern_id": "MISC-06", "pattern_name": "水上驾星", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "杂局第十九",
     "verbatim": "水上驾星，一年好一年不好是也。",
     "formation_conditions": ["运势一年好一年坏"], "supporting_stars": [], "breaking_conditions": []},
    {"pattern_id": "MISC-07", "pattern_name": "吉凶相伴", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "杂局第十九",
     "verbatim": "吉凶相伴，命有主星限前则发限衰不发是也。",
     "formation_conditions": ["命有主星", "限前发限衰不发"], "supporting_stars": [], "breaking_conditions": []},
    {"pattern_id": "MISC-08", "pattern_name": "枯木逢春", "school": "CLASSICAL_SOURCE", "source": SRC, "source_section": "杂局第十九",
     "verbatim": "枯木逢春，谓命衰限好是也。",
     "formation_conditions": ["本命衰", "行限好"], "supporting_stars": [], "breaking_conditions": []},
]

# ============================================================
# PALACE_FORTUNE_RULE (十二宫得地合格诀) 12条
# ============================================================
PALACE_FORTUNE_RULE = [
    {"rule_id": "PF-01", "palace_branch": "子", "verbatim": "子宫贪狼杀阴星，机梁相拱福兴隆，庚辛乙癸生人美，一生富贵足丰荣。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星得地合格诀第十二"},
    {"rule_id": "PF-02", "palace_branch": "丑", "verbatim": "丑宫立命日月朝，丙戌生人福禄饶，正坐平常中局论，对照富贵祸皆消。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星得地合格诀第十二"},
    {"rule_id": "PF-03", "palace_branch": "寅", "verbatim": "寅宫巨日足丰隆，七杀天梁百事通，申巳庚人皆为吉，男子为官女受封。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星得地合格诀第十二"},
    {"rule_id": "PF-04", "palace_branch": "卯", "verbatim": "卯宫机巨武曲逢，辛乙生人福气隆，男子为当廪禄，女人享福受褒封。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星得地合格诀第十二"},
    {"rule_id": "PF-05", "palace_branch": "辰", "verbatim": "辰位机梁坐命宫，天府戌地最盈丰，腰金衣紫真荣显，富华贵辉宜到终。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星得地合格诀第十二"},
    {"rule_id": "PF-06", "palace_branch": "巳", "verbatim": "巳位天机天相临，紫府朝垣福更深，戊辛壬丙皆为贵，一生顺遂少灾侵。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星得地合格诀第十二"},
    {"rule_id": "PF-07", "palace_branch": "午", "verbatim": "午宫紫府太阳同，机梁破杀喜相逢，甲丁己癸生人福，一世风光廪禄丰。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星得地合格诀第十二"},
    {"rule_id": "PF-08", "palace_branch": "未", "verbatim": "未宫紫武廉贞同，日月巨门喜相逢，女人值此全福寿，男子逢之位三公。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星得地合格诀第十二"},
    {"rule_id": "PF-09", "palace_branch": "申", "verbatim": "申宫紫帝贞梁同，武曲巨门喜相逢，甲庚癸人如得喜，一生富贵逞英雄。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星得地合格诀第十二"},
    {"rule_id": "PF-10", "palace_branch": "酉", "verbatim": "酉宫最喜太阴逢，巨日又逢当面冲，辛乙生人为贵格，一生福禄永亨通。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星得地合格诀第十二"},
    {"rule_id": "PF-11", "palace_branch": "戌", "verbatim": "戌宫紫微对冲辰，富而不贵有虚名，更加吉曜多权禄，只利开张贸易人。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星得地合格诀第十二"},
    {"rule_id": "PF-12", "palace_branch": "亥", "verbatim": "亥宫最喜太阴逢，若人值此福禄隆，男女逢之皆称意，富贵荣华直到终。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星得地合格诀第十二"},
]

# ============================================================
# PALACE_DEPRIVATION_RULE (十二宫失陷破格诀) 9条（PD-01~09；Z80-G 实测校准）
# ============================================================
PALACE_DEPRIVATION_RULE = [
    {"rule_id": "PD-01", "palace_branch": "子丑", "verbatim": "子午天机丑巨铃，此星落陷果为真，纵然化吉更为美，任他富贵不清宁。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星失陷破格诀第十三"},
    {"rule_id": "PD-02", "palace_branch": "寅", "verbatim": "寅上机昌曲月逢，虽然吉拱不丰隆，男为伴仆女娼婢，若非夭折即贫穷。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星失陷破格诀第十三"},
    {"rule_id": "PD-03", "palace_branch": "卯辰", "verbatim": "卯上太阴擎羊逢，辰宫巨宿紫微同，纵然化吉非全美，若非加杀到头凶。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星失陷破格诀第十三"},
    {"rule_id": "PD-04", "palace_branch": "巳", "verbatim": "巳宫武月天梁巨，贪宿廉贞共到蛇，三方吉曜皆不贵，下贱贫穷度岁华。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星失陷破格诀第十三"},
    {"rule_id": "PD-05", "palace_branch": "午", "verbatim": "午宫贪巨月昌从，羊刃三合最嫌冲，虽然化吉居仕路，横破横成到老穷。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星失陷破格诀第十三"},
    {"rule_id": "PD-06", "palace_branch": "未", "verbatim": "未宫巨宿太阳嫌，纵少灾危有克伤，劳碌奔波官事至，随缘下贱度时光。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星失陷破格诀第十三"},
    {"rule_id": "PD-07", "palace_branch": "申酉", "verbatim": "申宫机巨为破格，男人浪荡女人贫，二宫若然桃花见，男女逢之总不荣。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星失陷破格诀第十三"},
    {"rule_id": "PD-08", "palace_branch": "戌", "verbatim": "戌上紫破若相逢，天同太阳皆主凶，若还孤寒更夭折，随缘勤苦免贫穷。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星失陷破格诀第十三"},
    {"rule_id": "PD-09", "palace_branch": "亥", "verbatim": "亥宫贪火天梁同，飘荡浪子走西东，若还富贵也年促，不然隶仆与贫穷。",
     "school": "CLASSICAL_SOURCE", "source": SRC2, "source_section": "十二宫诸星失陷破格诀第十三"},
]

# 注：PD-10~12 原文未单列，PD-01/03/07 覆盖子丑/卯辰/申酉合并宫位

# ============================================================
# 汇总
# ============================================================
ALL_PATTERNS = WEALTH_PATTERN + NOBILITY_PATTERN + POVERTY_PATTERN + MISC_PATTERN
ALL_PALACE_RULES = PALACE_FORTUNE_RULE + PALACE_DEPRIVATION_RULE


def coverage() -> dict:
    return {
        "wealth": len(WEALTH_PATTERN),
        "nobility": len(NOBILITY_PATTERN),
        "poverty": len(POVERTY_PATTERN),
        "misc": len(MISC_PATTERN),
        "palace_fortune": len(PALACE_FORTUNE_RULE),
        "palace_deprivation": len(PALACE_DEPRIVATION_RULE),
        "total_patterns": len(ALL_PATTERNS),
        "total_palace_rules": len(ALL_PALACE_RULES),
    }
