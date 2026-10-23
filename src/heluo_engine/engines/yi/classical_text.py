"""层 C：经典层（Classical Text）

职责：从知识库中检索卦辞/彖辞/象辞/爻辞的原文
约束：无 AI 介入，纯知识库检索。所有输出必须标注原文出处。

BUG-P0-02 修复：
  - 原 CLASSICAL_TEXTS 为空字典，get_classical_text() 返回全空字符串
  - 修复：内嵌64卦卦辞 + 大象辞数据（周易原文）
  - 约束：不修改 KbLoader，只读取数据
  - 当 KbLoader 中有易经 passages 时优先使用，否则使用内嵌数据
"""

from __future__ import annotations
import logging
from .models import ClassicalText

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 64卦卦辞 + 大象辞 内嵌数据库（周易原文）
# 数据来源：周易正义（王弼注、孔颖达疏）
# ═══════════════════════════════════════════════════════════════════

_CLASSICAL_TEXTS: dict[str, dict] = {
    "乾为天": {
        "gua_ci": "元亨利贞。",
        "tuan_ci": "大哉乾元，万物资始，乃统天。",
        "da_xiang_ci": "天行健，君子以自强不息。",
    },
    "坤为地": {
        "gua_ci": "元亨，利牝马之贞。君子有攸往，先迷后得主。利西南得朋，东北丧朋。安贞吉。",
        "tuan_ci": "至哉坤元，万物资生，乃顺承天。",
        "da_xiang_ci": "地势坤，君子以厚德载物。",
    },
    "水雷屯": {
        "gua_ci": "元亨利贞。勿用有攸往，利建侯。",
        "tuan_ci": "屯，刚柔始交而难生。动乎险中，大亨贞。",
        "da_xiang_ci": "云雷屯，君子以经纶。",
    },
    "山水蒙": {
        "gua_ci": "亨。匪我求童蒙，童蒙求我。初筮告，再三渎，渎则不告。利贞。",
        "tuan_ci": "蒙，山下有险，险而止，蒙。",
        "da_xiang_ci": "山下出泉，蒙。君子以果行育德。",
    },
    "水天需": {
        "gua_ci": "有孚，光亨贞吉。利涉大川。",
        "tuan_ci": "需，须也。险在前也，刚健而不陷，其义不困穷矣。",
        "da_xiang_ci": "云上于天，需。君子以饮食宴乐。",
    },
    "天水讼": {
        "gua_ci": "有孚窒惕，中吉，终凶。利见大人，不利涉大川。",
        "tuan_ci": "讼，上刚下险，险而健，讼。",
        "da_xiang_ci": "天与水违行，讼。君子以作事谋始。",
    },
    "地水师": {
        "gua_ci": "贞，丈人吉，无咎。",
        "tuan_ci": "师，众也。贞，正也。能以众正，可以王矣。",
        "da_xiang_ci": "地中有水，师。君子以容民畜众。",
    },
    "水地比": {
        "gua_ci": "吉。原筮元永贞，无咎。不宁方来，后夫凶。",
        "tuan_ci": "比，吉也。比，辅也。下顺从也。",
        "da_xiang_ci": "地上有水，比。先王以建万国，亲诸侯。",
    },
    "风天小畜": {
        "gua_ci": "亨。密云不雨，自我西郊。",
        "tuan_ci": "小畜，柔得位而上下应之，曰小畜。",
        "da_xiang_ci": "风行天上，小畜。君子以懿文德。",
    },
    "天泽履": {
        "gua_ci": "履虎尾，不咥人，亨。",
        "tuan_ci": "履，柔履刚也。说而应乎乾，是以履虎尾不咥人亨。",
        "da_xiang_ci": "上天下泽，履。君子以辨上下，定民志。",
    },
    "地天泰": {
        "gua_ci": "小往大来，吉亨。",
        "tuan_ci": "泰，小往大来吉亨，则是天地交而万物通也，上下交而其志同也。",
        "da_xiang_ci": "天地交，泰。后以财成天地之道，辅相天地之宜，以左右民。",
    },
    "天地否": {
        "gua_ci": "否之匪人，不利君子贞。大往小来。",
        "tuan_ci": "否之匪人不利君子贞，大往小来，则是天地不交而万物不通也。",
        "da_xiang_ci": "天地不交，否。君子以俭德辟难，不可荣以禄。",
    },
    "天火同人": {
        "gua_ci": "同人于野，亨。利涉大川，利君子贞。",
        "tuan_ci": "同人，柔得位得中而应乎乾，曰同人。",
        "da_xiang_ci": "天与火，同人。君子以类族辨物。",
    },
    "火天大有": {
        "gua_ci": "元亨。",
        "tuan_ci": "大有，柔得尊位大中，而上下应之，曰大有。",
        "da_xiang_ci": "火在天上，大有。君子以遏恶扬善，顺天休命。",
    },
    "地山谦": {
        "gua_ci": "亨，君子有终。",
        "tuan_ci": "谦亨，天道下济而光明，地道卑而上行。",
        "da_xiang_ci": "地中有山，谦。君子以裒多益寡，称物平施。",
    },
    "雷地豫": {
        "gua_ci": "利建侯行师。",
        "tuan_ci": "豫，刚应而志行，顺以动，豫。",
        "da_xiang_ci": "雷出地奋，豫。先王以作乐崇德，殷荐之上帝，以配祖考。",
    },
    "泽雷随": {
        "gua_ci": "元亨利贞，无咎。",
        "tuan_ci": "随，刚来而下柔，动而说，随。",
        "da_xiang_ci": "泽中有雷，随。君子以向晦入宴息。",
    },
    "山风蛊": {
        "gua_ci": "元亨，利涉大川。先甲三日，后甲三日。",
        "tuan_ci": "蛊，刚上而柔下，巽而止，蛊。",
        "da_xiang_ci": "山下有风，蛊。君子以振民育德。",
    },
    "地泽临": {
        "gua_ci": "元亨利贞。至于八月有凶。",
        "tuan_ci": "临，刚浸而长，说而顺，刚中而应。",
        "da_xiang_ci": "泽上有地，临。君子以教思无穷，容保民无疆。",
    },
    "风地观": {
        "gua_ci": "盥而不荐，有孚颙若。",
        "tuan_ci": "大观在上，顺而巽，中正以观天下。",
        "da_xiang_ci": "风行地上，观。先王以省方观民设教。",
    },
    "火雷噬嗑": {
        "gua_ci": "亨，利用狱。",
        "tuan_ci": "颐中有物曰噬嗑。噬嗑而亨，刚柔分，动而明。",
        "da_xiang_ci": "雷电噬嗑，先王以明罚敕法。",
    },
    "山火贲": {
        "gua_ci": "亨，小利有攸往。",
        "tuan_ci": "贲亨，柔来而文刚，故亨。分刚上而文柔，故小利有攸往。",
        "da_xiang_ci": "山下有火，贲。君子以明庶政，无敢折狱。",
    },
    "山地剥": {
        "gua_ci": "不利有攸往。",
        "tuan_ci": "剥，剥也，柔变刚也。不利有攸往，小人长也。",
        "da_xiang_ci": "山附于地，剥。上以厚下安宅。",
    },
    "地雷复": {
        "gua_ci": "亨。出入无疾，朋来无咎。反复其道，七日来复。利有攸往。",
        "tuan_ci": "复亨，刚反。动而以顺行，是以出入无疾，朋来无咎。",
        "da_xiang_ci": "雷在地中，复。先王以至日闭关，商旅不行，后不省方。",
    },
    "天雷无妄": {
        "gua_ci": "元亨利贞。其匪正有眚，不利有攸往。",
        "tuan_ci": "无妄，刚自外来而为主于内，动而健，刚中而应。",
        "da_xiang_ci": "天下雷行，物与无妄。先王以茂对时育万物。",
    },
    "山天大畜": {
        "gua_ci": "利贞，不家食吉，利涉大川。",
        "tuan_ci": "大畜，刚健笃实辉光，日新其德。",
        "da_xiang_ci": "天在山中，大畜。君子以多识前言往行，以畜其德。",
    },
    "山雷颐": {
        "gua_ci": "贞吉。观颐，自求口实。",
        "tuan_ci": "颐贞吉，养正则吉也。观颐，观其所养也。",
        "da_xiang_ci": "山下有雷，颐。君子以慎言语，节饮食。",
    },
    "泽风大过": {
        "gua_ci": "栋桡，利有攸往，亨。",
        "tuan_ci": "大过，大者过也。栋桡，本末弱也。",
        "da_xiang_ci": "泽灭木，大过。君子以独立不惧，遁世无闷。",
    },
    "坎为水": {
        "gua_ci": "习坎，有孚，维心亨，行有尚。",
        "tuan_ci": "习坎，重险也。水流而不盈，行险而不失其信。",
        "da_xiang_ci": "水洊至，习坎。君子以常德行，习教事。",
    },
    "离为火": {
        "gua_ci": "利贞，亨。畜牝牛，吉。",
        "tuan_ci": "离，丽也。日月丽乎天，百谷草木丽乎土。",
        "da_xiang_ci": "明两作，离。大人以继明照于四方。",
    },
    "泽山咸": {
        "gua_ci": "亨，利贞，取女吉。",
        "tuan_ci": "咸，感也。柔上而刚下，二气感应以相与。",
        "da_xiang_ci": "山上有泽，咸。君子以虚受人。",
    },
    "雷风恒": {
        "gua_ci": "亨，无咎，利贞。利有攸往。",
        "tuan_ci": "恒，久也。刚上而柔下，雷风相与，巽而动，刚柔皆应。",
        "da_xiang_ci": "雷风恒，君子以立不易方。",
    },
    "天山遁": {
        "gua_ci": "亨，小利贞。",
        "tuan_ci": "遁亨，遁而亨也。刚当位而应，与时行也。",
        "da_xiang_ci": "天下有山，遁。君子以远小人，不恶而严。",
    },
    "雷天大壮": {
        "gua_ci": "利贞。",
        "tuan_ci": "大壮，大者壮也。刚以动，故壮。",
        "da_xiang_ci": "雷在天上，大壮。君子以非礼弗履。",
    },
    "火地晋": {
        "gua_ci": "康侯用锡马蕃庶，昼日三接。",
        "tuan_ci": "晋，进也。明出地上，顺而丽乎大明，柔进而上行。",
        "da_xiang_ci": "明出地上，晋。君子以自昭明德。",
    },
    "地火明夷": {
        "gua_ci": "利艰贞。",
        "tuan_ci": "明入地中，明夷。内文明而外柔顺，以蒙大难。",
        "da_xiang_ci": "明入地中，明夷。君子以莅众，用晦而明。",
    },
    "风火家人": {
        "gua_ci": "利女贞。",
        "tuan_ci": "家人，女正位乎内，男正位乎外。男女正，天地之大义也。",
        "da_xiang_ci": "风自火出，家人。君子以言有物而行有恒。",
    },
    "火泽睽": {
        "gua_ci": "小事吉。",
        "tuan_ci": "睽，火动而上，泽动而下，二女同居其志不同行。",
        "da_xiang_ci": "上火下泽，睽。君子以同而异。",
    },
    "水山蹇": {
        "gua_ci": "利西南，不利东北。利见大人，贞吉。",
        "tuan_ci": "蹇，难也，险在前也。见险而能止，知矣哉。",
        "da_xiang_ci": "山上有水，蹇。君子以反身修德。",
    },
    "雷水解": {
        "gua_ci": "利西南。无所往，其来复吉。有攸往，夙吉。",
        "tuan_ci": "解，险以动，动而免乎险，解。",
        "da_xiang_ci": "雷雨作，解。君子以赦过宥罪。",
    },
    "山泽损": {
        "gua_ci": "有孚，元吉，无咎，可贞。利有攸往。曷之用？二簋可用享。",
        "tuan_ci": "损，损下益上，其道上行。",
        "da_xiang_ci": "山下有泽，损。君子以惩忿窒欲。",
    },
    "风雷益": {
        "gua_ci": "利有攸往，利涉大川。",
        "tuan_ci": "益，损上益下，民说无疆。自上下下，其道大光。",
        "da_xiang_ci": "风雷益，君子以见善则迁，有过则改。",
    },
    "泽天夬": {
        "gua_ci": "扬于王庭，孚号有厉。告自邑，不利即戎。利有攸往。",
        "tuan_ci": "夬，决也，刚决柔也。健而说，决而和。",
        "da_xiang_ci": "泽上于天，夬。君子以施禄及下，居德则忌。",
    },
    "天风姤": {
        "gua_ci": "女壮，勿用取女。",
        "tuan_ci": "姤，遇也，柔遇刚也。勿用取女，不可与长也。",
        "da_xiang_ci": "天下有风，姤。后以施命诰四方。",
    },
    "泽地萃": {
        "gua_ci": "亨。王假有庙。利见大人，亨，利贞。用大牲吉，利有攸往。",
        "tuan_ci": "萃，聚也。顺以说，刚中而应，故聚也。",
        "da_xiang_ci": "泽上于地，萃。君子以除戎器，戒不虞。",
    },
    "地风升": {
        "gua_ci": "元亨。用见大人，勿恤。南征吉。",
        "tuan_ci": "柔以时升，巽而顺，刚中而应，是以大亨。",
        "da_xiang_ci": "地中生木，升。君子以顺德，积小以高大。",
    },
    "泽水困": {
        "gua_ci": "亨，贞大人吉，无咎。有言不信。",
        "tuan_ci": "困，刚掩也。险以说，虽困不失其所亨，其唯君子乎。",
        "da_xiang_ci": "泽无水，困。君子以致命遂志。",
    },
    "水风井": {
        "gua_ci": "改邑不改井，无丧无得。往来井井。汔至亦未繘井，羸其瓶，凶。",
        "tuan_ci": "巽乎水而上水，井。井养而不穷也。",
        "da_xiang_ci": "木上有水，井。君子以劳民劝相。",
    },
    "泽火革": {
        "gua_ci": "巳日乃孚，元亨利贞，悔亡。",
        "tuan_ci": "革，水火相息，二女同居其志不相得，曰革。",
        "da_xiang_ci": "泽中有火，革。君子以治历明时。",
    },
    "火风鼎": {
        "gua_ci": "元吉，亨。",
        "tuan_ci": "鼎，象也。以木巽火，亨饪也。圣人亨以享上帝，而大亨以养圣贤。",
        "da_xiang_ci": "木上有火，鼎。君子以正位凝命。",
    },
    "震为雷": {
        "gua_ci": "亨。震来虩虩，笑言哑哑。震惊百里，不丧匕鬯。",
        "tuan_ci": "震亨，震来虩虩，恐致福也。笑言哑哑，后有则也。",
        "da_xiang_ci": "洊雷震，君子以恐惧修省。",
    },
    "艮为山": {
        "gua_ci": "艮其背，不获其身。行其庭，不见其人。无咎。",
        "tuan_ci": "艮，止也。时止则止，时行则行，动静不失其时，其道光明。",
        "da_xiang_ci": "兼山艮，君子以思不出其位。",
    },
    "风山渐": {
        "gua_ci": "女归吉，利贞。",
        "tuan_ci": "渐之进也，女归吉也。进得位，往有功也。",
        "da_xiang_ci": "山上有木，渐。君子以居贤德善俗。",
    },
    "雷泽归妹": {
        "gua_ci": "征凶，无攸利。",
        "tuan_ci": "归妹，天地之大义也。天地不交而万物不兴。",
        "da_xiang_ci": "泽上有雷，归妹。君子以永终知敝。",
    },
    "雷火丰": {
        "gua_ci": "亨，王假之。勿忧，宜日中。",
        "tuan_ci": "丰，大也。明以动，故丰。王假之，尚大也。",
        "da_xiang_ci": "雷电皆至，丰。君子以折狱致刑。",
    },
    "火山旅": {
        "gua_ci": "小亨，旅贞吉。",
        "tuan_ci": "旅小亨，柔得中乎外而顺乎刚，止而丽乎明，是以小亨旅贞吉也。",
        "da_xiang_ci": "山上有火，旅。君子以明慎用刑而不留狱。",
    },
    "巽为风": {
        "gua_ci": "小亨，利有攸往，利见大人。",
        "tuan_ci": "重巽以申命，刚巽乎中正而志行，柔皆顺乎刚，是以小亨。",
        "da_xiang_ci": "随风巽，君子以申命行事。",
    },
    "兑为泽": {
        "gua_ci": "亨，利贞。",
        "tuan_ci": "兑，说也。刚中而柔外，说以利贞，是以顺乎天而应乎人。",
        "da_xiang_ci": "丽泽兑，君子以朋友讲习。",
    },
    "风水涣": {
        "gua_ci": "亨。王假有庙。利涉大川，利贞。",
        "tuan_ci": "涣亨，刚来而不穷，柔得位乎外而上同。",
        "da_xiang_ci": "风行水上，涣。先王以享于帝立庙。",
    },
    "水泽节": {
        "gua_ci": "亨。苦节不可贞。",
        "tuan_ci": "节亨，刚柔分而刚得中。苦节不可贞，其道穷也。",
        "da_xiang_ci": "泽上有水，节。君子以制数度，议德行。",
    },
    "风泽中孚": {
        "gua_ci": "豚鱼吉。利涉大川，利贞。",
        "tuan_ci": "中孚，柔在内而刚得中，说而巽，孚乃化邦也。",
        "da_xiang_ci": "泽上有风，中孚。君子以议狱缓死。",
    },
    "雷山小过": {
        "gua_ci": "亨，利贞。可小事，不可大事。飞鸟遗之音，不宜上宜下，大吉。",
        "tuan_ci": "小过，小者过而亨也。过以利贞，与时行也。",
        "da_xiang_ci": "山上有雷，小过。君子以行过乎恭，丧过乎哀，用过乎俭。",
    },
    "水火既济": {
        "gua_ci": "亨小，利贞。初吉终乱。",
        "tuan_ci": "既济亨，小者亨也。利贞，刚柔正而位当也。",
        "da_xiang_ci": "水在火上，既济。君子以思患而预防之。",
    },
    "火水未济": {
        "gua_ci": "亨，小狐汔济，濡其尾，无攸利。",
        "tuan_ci": "未济亨，柔得中也。小狐汔济，未出中也。",
        "da_xiang_ci": "火在水上，未济。君子以慎辨物居方。",
    },
}

# 卦名别名映射（支持简称查找）
_HEXAGRAM_ALIASES: dict[str, str] = {
    "乾": "乾为天", "坤": "坤为地", "屯": "水雷屯", "蒙": "山水蒙",
    "需": "水天需", "讼": "天水讼", "师": "地水师", "比": "水地比",
    "小畜": "风天小畜", "履": "天泽履", "泰": "地天泰", "否": "天地否",
    "同人": "天火同人", "大有": "火天大有", "谦": "地山谦", "豫": "雷地豫",
    "随": "泽雷随", "蛊": "山风蛊", "临": "地泽临", "观": "风地观",
    "噬嗑": "火雷噬嗑", "贲": "山火贲", "剥": "山地剥", "复": "地雷复",
    "无妄": "天雷无妄", "大畜": "山天大畜", "颐": "山雷颐", "大过": "泽风大过",
    "坎": "坎为水", "离": "离为火", "咸": "泽山咸", "恒": "雷风恒",
    "遁": "天山遁", "大壮": "雷天大壮", "晋": "火地晋", "明夷": "地火明夷",
    "家人": "风火家人", "睽": "火泽睽", "蹇": "水山蹇", "解": "雷水解",
    "损": "山泽损", "益": "风雷益", "夬": "泽天夬", "姤": "天风姤",
    "萃": "泽地萃", "升": "地风升", "困": "泽水困", "井": "水风井",
    "革": "泽火革", "鼎": "火风鼎", "震": "震为雷", "艮": "艮为山",
    "渐": "风山渐", "归妹": "雷泽归妹", "丰": "雷火丰", "旅": "火山旅",
    "巽": "巽为风", "兑": "兑为泽", "涣": "风水涣", "节": "水泽节",
    "中孚": "风泽中孚", "小过": "雷山小过", "既济": "水火既济", "未济": "火水未济",
}

# BUG-P0-02: 从 KbLoader passages 筛选出的易经原文（运行时覆盖内嵌数据）。
# 键为解析后的卦名（全名），值为 {"gua_ci" | "tuan_ci" | "da_xiang_ci": text}。
# 空时退化为纯内嵌数据；load_from_kb() 会填充此字典。
_KB_TEXTS: dict[str, dict] = {}

# 易经/周易 book_id 与标题关键字（用于从 KbLoader passages 中筛选易经原文）
_YI_BOOK_KEYWORDS = ("易经", "周易", "易經", "YIJING", "ZHOUYI", "YI-JING")
_YI_TEXT_MARKERS = ("卦辞", "彖辞", "大象", "爻辞")


def _resolve_hexagram_name(name: str) -> str:
    """解析卦名：支持全称和简称。"""
    if name in _CLASSICAL_TEXTS or name in _KB_TEXTS:
        return name
    if name in _HEXAGRAM_ALIASES:
        return _HEXAGRAM_ALIASES[name]
    # 尝试模糊匹配（如 "地天泰" 匹配 "泰"）
    for full_name in _CLASSICAL_TEXTS:
        if full_name.endswith(name) or name in full_name:
            return full_name
    return name


def _get_hexagram_data(hexagram_name: str) -> tuple[str, dict]:
    """返回 (解析后卦名, 合并后的原文数据)。

    合并优先级（BUG-P0-02）：KbLoader 筛选结果 > 内嵌64卦数据。
    """
    resolved = _resolve_hexagram_name(hexagram_name)
    data = dict(_CLASSICAL_TEXTS.get(resolved, {}))
    data.update(_KB_TEXTS.get(resolved, {}))
    return resolved, data


def _extract_passage_text(passage: dict) -> str:
    """从 passage 提取原文文本（兼容 classical_original / original_text 两种形状）。"""
    co = passage.get("classical_original") or {}
    if isinstance(co, dict) and co.get("text"):
        return str(co["text"])
    text = passage.get("original_text")
    return str(text) if text else ""


def _is_yi_passage(passage: dict, text: str) -> bool:
    """判断 passage 是否属于易经/周易原文。"""
    title = str(passage.get("title", ""))
    book_id = str(passage.get("book_id", ""))
    chapter_id = str(passage.get("chapter_id", ""))
    haystack = f"{title}{book_id}{chapter_id}".upper()
    if any(kw.upper() in haystack for kw in _YI_BOOK_KEYWORDS):
        return True
    return any(marker in text for marker in _YI_TEXT_MARKERS)


def _match_hexagram_name(text: str) -> str | None:
    """在原文文本中匹配卦名（全名优先，其次简称）。"""
    for full_name in _CLASSICAL_TEXTS:
        if full_name in text:
            return full_name
    for alias, full_name in _HEXAGRAM_ALIASES.items():
        if alias in text:
            return full_name
    return None


def _detect_slot(text: str) -> str | None:
    """根据文本标记判断属于哪个原文槽位（卦辞/彖辞/大象辞）。"""
    if "卦辞" in text:
        return "gua_ci"
    if "彖辞" in text or "彖曰" in text or "彖" in text:
        return "tuan_ci"
    if "大象" in text:
        return "da_xiang_ci"
    if "爻辞" in text:
        return None  # 爻辞暂不映射到 ClassicalText（384 条，见 get_yao_ci）
    return None


def load_from_kb(kb_loader) -> int:
    """从 KbLoader 的 passages 中筛选易经相关原文（BUG-P0-02）。

    约束：不修改 KbLoader，只读取 `kb_loader.passages` 数据。
    命中的 passage 按卦名归入 _KB_TEXTS，get_classical_text() 会优先使用。

    返回：成功合并的 passage 条数。
    """
    merged = 0
    if kb_loader is None:
        return merged
    try:
        passages = kb_loader.passages
    except AttributeError:
        return merged

    for p in passages or []:
        try:
            text = _extract_passage_text(p)
            if not _is_yi_passage(p, text):
                continue
            name = _match_hexagram_name(text)
            if name is None:
                continue
            slot = _detect_slot(text)
            if slot is None:
                continue
            resolved = _resolve_hexagram_name(name)
            _KB_TEXTS.setdefault(resolved, {})[slot] = text
            merged += 1
        except Exception as exc:  # noqa: BLE001 — 单条 passage 失败不阻断整体加载
            log.warning("classical_text: skip passage %s (%s)", p.get("passage_id", "?"), exc)
    return merged


def get_classical_text(
    hexagram_name: str,
    line_position: str | None = None
) -> ClassicalText:
    """
    从知识库中检索经典原文。

    检索优先级（BUG-P0-02）：
    1. KbLoader passages（load_from_kb 筛选出的易经原文）
    2. 内嵌64卦数据库（gua_ci + tuan_ci + da_xiang_ci）
    3. 失败时返回空 ClassicalText（不抛异常，保持向后兼容）
    """
    resolved, data = _get_hexagram_data(hexagram_name)

    gua_ci = data.get("gua_ci", "")
    tuan_ci = data.get("tuan_ci", "")
    da_xiang_ci = data.get("da_xiang_ci", "")

    # 来源标注
    gua_ci_source = f"周易·{resolved}·卦辞" if gua_ci else ""
    tuan_ci_source = f"周易·{resolved}·彖辞" if tuan_ci else ""
    da_xiang_ci_source = f"周易·{resolved}·大象" if da_xiang_ci else ""

    return ClassicalText(
        hexagram_name=resolved,
        gua_ci=gua_ci,
        gua_ci_source=gua_ci_source,
        tuan_ci=tuan_ci,
        tuan_ci_source=tuan_ci_source,
        da_xiang_ci=da_xiang_ci,
        da_xiang_ci_source=da_xiang_ci_source,
        yao_ci=None,
        yao_ci_source=None,
        yao_position=None,
        xiao_xiang_ci=None,
        xiao_xiang_ci_source=None,
    )


def get_yao_ci(
    hexagram_name: str,
    line_position: str
) -> tuple[str, str]:
    """
    获取特定爻位的爻辞。
    如 get_yao_ci("地天泰", "六四") → ("翩翩不富以其邻，不戒以孚", "周易·泰卦·六四")

    当前为简化实现，后续可从知识库扩展。
    """
    # 爻辞数据暂不内嵌（64卦×6爻=384条），后续从 KbLoader 加载
    return ("", "")


def load_classical_database(path: str | None = None, kb_loader=None) -> None:
    """
    加载经典原文数据库。

    BUG-P0-02 修复说明：
    - 原实现为空 pass，CLASSICAL_TEXTS 为空字典
    - 修复后：内嵌64卦数据在模块加载时初始化（保证至少覆盖64卦卦辞+大象辞）
    - 提供 kb_loader 时，从 KbLoader.passages 筛选易经原文并覆盖/补充内嵌数据
    - 约束：不修改 KbLoader，只读取数据
    """
    # 内嵌数据已在模块级别初始化，无需额外加载
    # 如果提供了外部路径，可以尝试扩展（但不修改内嵌数据）
    if path:
        log.info(f"classical_text: external path {path} noted, using embedded data")
    if kb_loader is not None:
        merged = load_from_kb(kb_loader)
        log.info(f"classical_text: loaded {merged} passages from KbLoader")
    log.debug(f"classical_text: loaded {len(_CLASSICAL_TEXTS)} hexagram entries")


def get_all_hexagram_names() -> list[str]:
    """返回所有64卦全名列表。"""
    return list(_CLASSICAL_TEXTS.keys())


def get_coverage_stats() -> dict:
    """返回经典原文覆盖统计。"""
    total = len(_CLASSICAL_TEXTS)
    has_gua_ci = sum(1 for v in _CLASSICAL_TEXTS.values() if v.get("gua_ci"))
    has_tuan_ci = sum(1 for v in _CLASSICAL_TEXTS.values() if v.get("tuan_ci"))
    has_da_xiang = sum(1 for v in _CLASSICAL_TEXTS.values() if v.get("da_xiang_ci"))
    return {
        "total_hexagrams": total,
        "gua_ci_coverage": has_gua_ci,
        "tuan_ci_coverage": has_tuan_ci,
        "da_xiang_ci_coverage": has_da_xiang,
    }
