# -*- coding: utf-8 -*-
"""禄命法 · NAYIN_NATURE：六十甲子纳音取象性质表（映射层释义原子库 · 二）

quote 全部逐字摘录《五行精纪》L215-309 各柱正注句（去阎东叟/五行要论/玉霄宝鉴等附注）；
庚午辛未/戊子己丑/庚寅辛卯/丙申丁酉/壬寅癸卯/丙午丁未/庚戌辛亥/壬子癸丑/甲寅乙卯/
戊午己未/庚申辛酉/壬戌癸亥 十二组为原著合注柱，quote 共用（原书合注）。
strength 全为 逐字（原文摘录）；quote_status 全 complete；topic 全 综合（性质取象，供总论引用）。
"""
from __future__ import annotations

NAYIN_NATURE: dict[str, dict] = {
    "甲子": {"nayin": "海中金", "quote": "甲子从革之金，其气散，得戊申土，癸巳水相之，则吉。戊申乃金临官之地，土者更旺于子，必能生成，癸巳系金，生于巳，水旺于子，纳音各有所归，又为朝元禄，忌丁卯丁酉戊午之火（五行精纪 L215）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "乙丑": {"nayin": "海中金", "quote": "乙丑自库之金，火不能克，盖退藏之金，苟无刑害冲破，未有不显荣者，独忌己丑戊午己未之火（五行精纪 L217）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "丙寅": {"nayin": "炉中火", "quote": "丙寅赫牺之火，无水制之，则为燔灼炎烈之患，水不可遇，独爱甲寅之水，就位济之，又名朝元禄（五行精纪 L219）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "丁卯": {"nayin": "炉中火", "quote": "丁卯伏明之火，气弱宜木生之，遇水则凶，乙卯乙酉水最毒（五行精纪 L221）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "戊辰": {"nayin": "大林木", "quote": "戊辰两土下木，众金不能克，盖生金，有母子之道，得土生之为佳（五行精纪 L224）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "己巳": {"nayin": "大林木", "quote": "己巳为近火之木，金自此生，于我无伤，忌见生旺之火（五行精纪 L225）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "庚午": {"nayin": "路旁土", "quote": "庚午辛未始生之土，木不能克，惟忌水多，反伤其气，木多却有归，盖归未也（五行精纪 L228，庚午辛未合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "辛未": {"nayin": "路旁土", "quote": "庚午辛未始生之土，木不能克，惟忌水多，反伤其气，木多却有归，盖归未也（五行精纪 L228，庚午辛未合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "壬申": {"nayin": "剑锋金", "quote": "壬申临官之金，利见水土，若丙申丙寅戊午之火，则为灾害（五行精纪 L230）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "癸酉": {"nayin": "剑锋金", "quote": "癸酉坚成之金，火死于酉，见火何伤，惟忌丁酉火，就位克之（五行精纪 L232）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "甲戌": {"nayin": "山头火", "quote": "甲戌自库之火，不嫌众水，惟忌壬戌，所谓墓中受克，其患难逃（五行精纪 L234）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "乙亥": {"nayin": "山头火", "quote": "乙亥伏明之火，其气湮欎而不发，借己亥辛卯己巳壬午癸未木生之，则精神旺相。癸巳癸亥丙午水，有之则不吉（五行精纪 L236）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "丙子": {"nayin": "涧下水", "quote": "丙子流衍之水，不忌众土，惟嫌庚子，乃旺中逢鬼，不祥莫大焉（五行精纪 L238）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "丁丑": {"nayin": "涧下水", "quote": "丁丑福聚之水，最爱金生，忌辛未丙辰丙戌相刑破也（五行精纪 L241）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "戊寅": {"nayin": "城头土", "quote": "戊寅受伤之土，最为无力，要生旺火，以资其气，忌己亥庚寅辛卯诸色木克之，主短夭之凶（五行精纪 L243）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "己卯": {"nayin": "城头土", "quote": "己卯自死之土，抑有甚焉，贵得丁卯甲戌乙亥己未之火，由合而来，以致其福（五行精纪 L245）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "庚辰": {"nayin": "白蜡金", "quote": "庚辰气聚之金，不用火制，其器自成，火盛反丧其器，病绝火无害，若甲辰乙巳火，恶不可言，亦不能克众木，益我气亦繁耳（五行精纪 L247）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "辛巳": {"nayin": "白蜡金", "quote": "辛巳自生之金，精神具足，体气完备，炎烈炽火而不忌，忌丙寅乙巳戊午之火，盖金生于巳而不能生，败于午，绝于寅而气散，复见生旺之火，焉可当之（五行精纪 L249）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "壬午": {"nayin": "杨柳木", "quote": "壬午柔和之木，枝干微弱，木能生火，却忌见火多，多则烬矣。虽生旺之金，亦不能伤，盖金就我败，得金反贵，水土盛者亦贵，惟忌甲午金伤之（五行精纪 L251）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "癸未": {"nayin": "杨柳木", "quote": "癸未自库之木，生旺尤佳，虽乙丑金不能冲破，各归其根，而不相犯，忌庚戌乙未金（五行精纪 L253）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "甲申": {"nayin": "泉中水", "quote": "甲申者自生之水，其气流衍，宜有所贵，亦藉金生，不忌众土，特嫌戊申庚子之土（五行精纪 L255）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "乙酉": {"nayin": "泉中水", "quote": "乙酉自败之水，假众金以相之，盖我气既弱，藉母以育，忌己酉乙卯戊申庚子辛丑之土，则夭折穷贱（五行精纪 L257）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "丙戌": {"nayin": "屋上土", "quote": "丙戌福壮禄厚之土，木不能克，忌见生旺之金，若遇火盛，则贵不可言（五行精纪 L258）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "丁亥": {"nayin": "屋上土", "quote": "丁亥临官之土，木不能克，嫌金多，须得火生救之乃吉，忌己亥辛卯之木（五行精纪 L259）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "戊子": {"nayin": "霹雳火", "quote": "戊子己丑水中之火，又曰神龙之火，遇水方贵，为六气之君可也（五行精纪 L261，戊子己丑合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "己丑": {"nayin": "霹雳火", "quote": "戊子己丑水中之火，又曰神龙之火，遇水方贵，为六气之君可也（五行精纪 L261，戊子己丑合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "庚寅": {"nayin": "松柏木", "quote": "庚寅辛卯岁寒之木，雪霜无以改其操，况金能克之乎？上有庚辛，不假制治，自然成材（五行精纪 L263，庚寅辛卯合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "辛卯": {"nayin": "松柏木", "quote": "庚寅辛卯岁寒之木，雪霜无以改其操，况金能克之乎？上有庚辛，不假制治，自然成材（五行精纪 L263，庚寅辛卯合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "壬辰": {"nayin": "长流水", "quote": "壬辰自库之水，若池沼水积之地，忌金来决破，若再见壬辰，是谓自刑，别辰无咎，遇多水土皆喜，惟畏壬戌癸亥丙子之水，生旺太过，汗漫无归（五行精纪 L265）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "癸巳": {"nayin": "长流水", "quote": "癸巳为自绝之水，名曰涸流，若丙戌丁亥庚子壮厚之土，其涸可待；若得三合生旺之金生之，则源泉溷溷，盈科而进也（五行精纪 L267）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "甲午": {"nayin": "砂中金", "quote": "甲午自败之金，亦曰强悍之金，遇火生旺，其器乃成，忌丁卯、丁酉、戊子之火，凶（五行精纪 L269）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "乙未": {"nayin": "砂中金", "quote": "乙未偏库之金，亦欲火制，而土生之，则福壮气聚，忌己未、丙申、丁酉之火（五行精纪 L271）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "丙申": {"nayin": "山下火", "quote": "丙申自病之火，丁酉自死之火，其气极微，假木相助，其气方生，忌甲申乙酉甲寅乙卯之水（五行精纪 L273，丙申丁酉合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "丁酉": {"nayin": "山下火", "quote": "丙申自病之火，丁酉自死之火，其气极微，假木相助，其气方生，忌甲申乙酉甲寅乙卯之水（五行精纪 L273，丙申丁酉合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "戊戌": {"nayin": "平地木", "quote": "戊戌土中之木，忌重见土，若纳音土多，一生迍蹇，金不能克，盖金气至戌而散，遇金乃能致福，利见多水木盛而为贵格（五行精纪 L275）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "己亥": {"nayin": "平地木", "quote": "己亥自生之木，根本繁盛，不忌众金，惟嫌辛亥辛巳癸酉之金，若见己卯丁未水、癸未木，未有不大贵（五行精纪 L277）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "庚子": {"nayin": "壁上土", "quote": "庚子厚德之土，能克众水，不忌他木，盖木至子无气，若遇壬申之金，谓之明位禄，其贵必矣（五行精纪 L280）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "辛丑": {"nayin": "壁上土", "quote": "辛丑福聚之土，众木不能克，盖丑为金库，丑中有金，见木何伤（五行精纪 L281）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "壬寅": {"nayin": "金箔金", "quote": "壬寅自绝之金，癸卯气散之金，若见众火则丧气，惟水土朝之则吉（五行精纪 L283，壬寅癸卯合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "癸卯": {"nayin": "金箔金", "quote": "壬寅自绝之金，癸卯气散之金，若见众火则丧气，惟水土朝之则吉（五行精纪 L283，壬寅癸卯合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "甲辰": {"nayin": "覆灯火", "quote": "甲辰偏库之火，多火助之吉，所谓同气相救，以资其不足，若见戊辰戊戌木生之为贵格，忌壬辰壬戌丙午丁未水最毒（五行精纪 L286）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "乙巳": {"nayin": "覆灯火", "quote": "乙巳临官之火，水不能克，盖水绝于巳，得水济之，则为纯粹，若得二三火助之亦佳（五行精纪 L288）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "丙午": {"nayin": "天河水", "quote": "丙午丁未银汉之水，土不能克，天上之水地金不能生也。生旺太过，反伤于万物，死绝太多，又不能生万物也（五行精纪 L290，丙午丁未合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "丁未": {"nayin": "天河水", "quote": "丙午丁未银汉之水，土不能克，天上之水地金不能生也。生旺太过，反伤于万物，死绝太多，又不能生万物也（五行精纪 L290，丙午丁未合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "戊申": {"nayin": "大驿土", "quote": "戊申重阜之土，木绝于申不能克，若见金水多助，则富贵尊荣之格也（五行精纪 L292）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "己酉": {"nayin": "大驿土", "quote": "己酉自败之土，其气不足，藉火以相助之。见丁卯丁酉火则吉，切忌死绝，畏辛卯辛酉木，灾蹇夭折（五行精纪 L293）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "庚戌": {"nayin": "钗钏金", "quote": "庚戌辛亥坚成之金，不可见火，恐有所伤，若得水土相之为贵（五行精纪 L294，庚戌辛亥合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "辛亥": {"nayin": "钗钏金", "quote": "庚戌辛亥坚成之金，不可见火，恐有所伤，若得水土相之为贵（五行精纪 L294，庚戌辛亥合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "壬子": {"nayin": "桑柘木", "quote": "壬子专位之木，癸丑偏库之木，遇死绝则富贵，生旺则贫贱，水多则夭折，金多土盛为佳（五行精纪 L296，壬子癸丑合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "癸丑": {"nayin": "桑柘木", "quote": "壬子专位之木，癸丑偏库之木，遇死绝则富贵，生旺则贫贱，水多则夭折，金多土盛为佳（五行精纪 L296，壬子癸丑合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "甲寅": {"nayin": "大溪水", "quote": "甲寅自病之水，已卯自死之水，虽然死病，土不能克，盖干支二木，可以制土，若见壬寅癸卯之金则为优裕（五行精纪 L298，甲寅己卯合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "乙卯": {"nayin": "大溪水", "quote": "甲寅自病之水，已卯自死之水，虽然死病，土不能克，盖干支二木，可以制土，若见壬寅癸卯之金则为优裕（五行精纪 L298，甲寅己卯合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "丙辰": {"nayin": "沙中土", "quote": "丙辰自库之土厚且壮，喜甲辰恶戊辰，此土木不能伤，盖丙火也。辰为火偏库，土已成器，惟嫌戊戌己亥辛卯戊辰之木（五行精纪 L300）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "丁巳": {"nayin": "沙中土", "quote": "丁巳自绝之土，又不为绝，盖一土居二火之下，在父母之邦，乘天属之恩，故不为绝，木不能克，火多益佳（五行精纪 L302）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "戊午": {"nayin": "天上火", "quote": "戊午自旺之火，己未偏库之火，居离明之方，旺相之地，其气极盛，他水无伤，忌丙午丁未天上之水（五行精纪 L304，戊午己未合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "己未": {"nayin": "天上火", "quote": "戊午自旺之火，己未偏库之火，居离明之方，旺相之地，其气极盛，他水无伤，忌丙午丁未天上之水（五行精纪 L304，戊午己未合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "庚申": {"nayin": "石榴木", "quote": "庚申辛酉二金居木上，因金以成器，忌再见金，致毁其器，若见甲申乙酉水则入格也（五行精纪 L307，庚申辛酉合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "辛酉": {"nayin": "石榴木", "quote": "庚申辛酉二金居木上，因金以成器，忌再见金，致毁其器，若见甲申乙酉水则入格也（五行精纪 L307，庚申辛酉合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "壬戌": {"nayin": "大海水", "quote": "壬戌偏库之水，癸亥临官之水，名曰大海水，盖干支纳音皆水，忌见众水，虽壬辰水库，亦不能当，不忌他土，死绝则吉，生旺则泛滥而无所归也（五行精纪 L309，壬戌癸亥合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
    "癸亥": {"nayin": "大海水", "quote": "壬戌偏库之水，癸亥临官之水，名曰大海水，盖干支纳音皆水，忌见众水，虽壬辰水库，亦不能当，不忌他土，死绝则吉，生旺则泛滥而无所归也（五行精纪 L309，壬戌癸亥合注）", "strength": "逐字", "quote_status": "complete", "topic": ["综合"]},
}

# 六十甲子全集（与 NAYIN_NATURE 键对应，供校验）
_SIXTY_JIAZI: list[str] = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥",
]


def audit_nayin_nature() -> dict:
    """六十甲子全覆盖 + 字段合法校验."""
    errors, missing = [], []
    for gz in _SIXTY_JIAZI:
        rec = NAYIN_NATURE.get(gz)
        if rec is None:
            missing.append(gz)
            continue
        if rec["strength"] != "逐字" or rec["quote_status"] != "complete":
            errors.append(f"{gz}: strength/quote_status 非法")
        if not rec["quote"]:
            errors.append(f"{gz}: quote 为空")
        if not rec["nayin"]:
            errors.append(f"{gz}: nayin 为空")
    return {"ok": not errors and not missing, "errors": errors, "missing": missing, "total": len(_SIXTY_JIAZI)}
