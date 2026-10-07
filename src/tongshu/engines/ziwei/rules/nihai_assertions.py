# -*- coding: utf-8 -*-
"""倪海厦紫微斗数断言库（天纪精选集）.

架构定位:
    本模块是独立断言库，不消费 MultiMethodSignal，不重算任何事实。
    直接从 FrozenZiweiChart 读取「每宫主星」→ 输出断言条目。
    解层可选项地合并到 ZiweiInterpretationOutput。

断言风格:
    倪师断言 = 星 × 宫 → 具体断语（一句话判断）
    特点：直接、具体、可验证，不说"可能"只说"主"
    例：紫微在命「代表官印，官的命」/ 禄存在命「标准小气」

断言来源:
    D:\顺天系统资料\倪海厦天纪-断言资料精选集.md
    语料库：4886 条判语（v2.0, Renhuai123/nihai-tianji-corpus）

Z18 扩容（2026-09-14）:
    - 数据结构由 (star, palace) → 单条 升级为 → 多条（list）
    - 同星宫支持多条断言（原先同键覆盖导致丢失信息）
    - 从精选集逐字提取：14 主星 × 命宫（每条 2-3 断语）+ 辅煞星 + 十二宫总论
      + 格局 + 四化
    - 保持 fail-closed：未命中的星不产生断言，无原话依据不编造

约束:
    1. 断言只读 chart.palaces[*].major（主星列表），不重算四化/飞星
    2. 断言不带 LLM / score / weight
    3. 未命中的星不产生断言（fail-closed）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ===========================================================================
# 数据模型
# ===========================================================================

@dataclass(frozen=True)
class NihaiAssertion:
    """单条倪师断言."""
    star: str              # 主星（如 "紫微"）
    palace: str            # 宫位（如 "命宫"）
    source: str            # 出处（章节+页码或讲次）
    category: str          # 断言类别（personality/career/wealth/marriage/health/fortune）
    direction: str         # "吉"/"凶"/"中性"
    strength: str          # "强"/"中"/"弱"
    text: str              # 断语原文（倪师原话，逐字抄录）

    def to_dict(self) -> dict[str, Any]:
        return {
            "star": self.star,
            "palace": self.palace,
            "source": self.source,
            "category": self.category,
            "direction": self.direction,
            "strength": self.strength,
            "text": self.text,
        }


# ===========================================================================
# 断言库（主星 × 宫位 → 断语列表）
#
# 断言覆盖原则:
#   - 每条断言必须有倪师原话依据（精选集可追溯）
#   - 无依据的不编造（宁可少不可编）
#   - 断言按宫位覆盖主星核心特征（命宫优先）
#   - 同 (star, palace) 允许多条断言，按注册顺序输出
# ===========================================================================

# 断言条目注册表: (star, palace) → [NihaiAssertion, ...]
_NIHAI_ASSERTIONS: Dict[Tuple[str, str], List[NihaiAssertion]] = {}


def _register(star: str, palace: str, source: str,
              category: str, direction: str, strength: str,
              text: str) -> None:
    """注册一条断言（同键追加，不覆盖）."""
    _NIHAI_ASSERTIONS.setdefault((star, palace), []).append(
        NihaiAssertion(
            star=star, palace=palace, source=source,
            category=category, direction=direction, strength=strength,
            text=text,
        )
    )


# ============================================================================
# 十四主星 × 命宫断言
# ============================================================================

# 紫微：北斗帝星，主官带
_register(
    "紫微", "命宫", "主星册·紫微",
    category="career", direction="吉", strength="强",
    text="紫微星是帝星，主的是官，官带。有紫微星出现的时候，代表的是官印，官的命。",
)
_register(
    "紫微", "命宫", "主星册·紫微",
    category="fortune", direction="吉", strength="强",
    text="紫微星出现的时候，代表的是官印，有紫微星在命宫的人，先天有贵气。",
)
_register(
    "紫微", "命宫", "主星册·紫微",
    category="personality", direction="中性", strength="强",
    text="我们分南斗还有北斗。北斗星系第一颗星我们叫做紫微星。它是北斗星君，它是个帝星。",
)

# 天机：北斗文官带
_register(
    "天机", "命宫", "主星册·天机",
    category="career", direction="吉", strength="强",
    text="天机星也是个官带星，但是天机星是文官带，干公务人员、老师、银行做事都是。",
)
_register(
    "天机", "命宫", "主星册·天机",
    category="personality", direction="中性", strength="中",
    text="天机星是属于阴星。紫微星是属于阳星。星分阴阳就好了。",
)

# 太阳：中天武官带，也主财禄
_register(
    "太阳", "命宫", "主星册·太阳",
    category="career", direction="吉", strength="强",
    text="太阳星是武官带，军人、警察、法官、外交官都是属于武官带。太阳也代表财禄。",
)
_register(
    "太阳", "命宫", "主星册·太阳",
    category="fortune", direction="吉", strength="强",
    text="太阳星主贵，也代表财禄，官禄宫就主官，财帛宫就主财。",
)
_register(
    "太阳", "命宫", "主星册·太阳",
    category="fortune", direction="中性", strength="中",
    text="不要说有的人命是太阳，有的太阴，太阳就是完全受到父亲的影响。",
)

# 武曲：北斗财星王，也主武官
_register(
    "武曲", "命宫", "主星册·武曲",
    category="wealth", direction="吉", strength="强",
    text="武曲星第一个它代表的是武官，第二个它也代表财星，而且它是财星的王。",
)
_register(
    "武曲", "命宫", "主星册·武曲",
    category="personality", direction="吉", strength="强",
    text="武曲星的人个性跟太阳一样很火爆。但是这种一发就过去了，随发随走。",
)
_register(
    "武曲", "命宫", "主星册·武曲",
    category="fortune", direction="吉", strength="强",
    text="武曲星也代表贵人。像紫微太阳武曲这种通通是贵人星。",
)

# 天同：南斗福星，人和之星
_register(
    "天同", "命宫", "主星册·天同",
    category="personality", direction="吉", strength="强",
    text="天同星是个人和的星，一看今年正好天同，合伙吉。",
)
_register(
    "天同", "命宫", "主星册·天同",
    category="fortune", direction="中性", strength="中",
    text="有的事情一定要人和才能成事。有的事情要天时才能成事。流年要到化禄才能成事。",
)

# 廉贞：北斗桃花星，也主武官
_register(
    "廉贞", "命宫", "主星册·廉贞",
    category="personality", direction="中性", strength="中",
    text="廉贞星是桃花星，也代表武官带，武官星在边疆去打仗。",
)
_register(
    "廉贞", "命宫", "主星册·廉贞",
    category="marriage", direction="中性", strength="中",
    text="桃花星第一个指的是桃花。但是这个还是次桃花还不是主桃花。这个也是桃花星。",
)
_register(
    "廉贞", "命宫", "主星册·廉贞",
    category="career", direction="中性", strength="中",
    text="廉贞星在武官带主武官的带兵打仗。那廉贞星进来武官带的时候一般来说他是到边疆去打仗。",
)

# 天府：南斗帝星，文官教星
_register(
    "天府", "命宫", "主星册·天府",
    category="career", direction="吉", strength="强",
    text="天府星是南斗星君，是个文官星，也是一个教星。很多天府坐命的人去当公务人员当教员。",
)
_register(
    "天府", "命宫", "主星册·天府",
    category="wealth", direction="吉", strength="强",
    text="天府星是很善于理财，又很厚道又拼命做事情，人又很善良的一种人，又非常善于理财的。",
)

# 太阴：中天主富星
_register(
    "太阴", "命宫", "主星册·太阴",
    category="personality", direction="吉", strength="强",
    text="如果女命女孩子坐太阴星很漂亮。美的像月里嫦娥一样。两只眼睛呀像月亮一样那么大。",
)
_register(
    "太阴", "命宫", "主星册·太阴",
    category="wealth", direction="吉", strength="强",
    text="太阴在命宫的女孩子主富贵，皮肤白细细，这是水澄桂萼格。",
)
_register(
    "太阴", "命宫", "主星册·太阴",
    category="personality", direction="吉", strength="中",
    text="太阴出来的一定是月亮嘛，瘦瘦的有没有，白白皙皙的，人非常的清秀，但是两个骨碌眼睛大大的，这是月朗天门这是重点。",
)

# 贪狼：北斗桃花/财气
_register(
    "贪狼", "命宫", "主星册·贪狼",
    category="personality", direction="中性", strength="中",
    text="贪狼星是属于桃花星，主桃花也指的是酒、财、气，通通在这个酒、色、财、气、赌里面。",
)
_register(
    "贪狼", "命宫", "主星册·贪狼",
    category="fortune", direction="中性", strength="中",
    text="贪狼入命的人他有生杀之权，如果还有天魁星来会，文武双全。",
)
_register(
    "贪狼", "命宫", "主星册·贪狼",
    category="wealth", direction="中性", strength="中",
    text="这颗星呢（贪狼），主的是财，所以它不但有刚刚讲的酒、色财，它主的是财。",
)

# 巨门：北斗暗星，庙旺能言善道，落陷主是非
_register(
    "巨门", "命宫", "主星册·巨门",
    category="personality", direction="吉", strength="强",
    text="巨门星如果是庙旺，就是能言善道口才非常好。那巨富的人再逢到巨门星入庙的时候，代表他豪门宅地。",
)
_register(
    "巨门", "命宫", "主星册·巨门",
    category="personality", direction="凶", strength="弱",
    text="巨门星落陷的话问题就来了，这个巨门就是门很大，监狱的门也还是大但是是关到的，落陷要坐在牢里。",
)
_register(
    "巨门", "命宫", "主星册·巨门",
    category="wealth", direction="吉", strength="强",
    text="那巨富的人再逢到巨门星入庙的时候，代表他豪门宅地，那如果生下来就是巨门星入庙，那个双禄禄马交驰在命，生下来就在豪门世家里面。",
)

# 天相：南斗印星，佐才
_register(
    "天相", "命宫", "主星册·天相",
    category="career", direction="吉", strength="强",
    text="天相星是天上的宰相，是一个佐才星。你如果是天相入命的人你适合去当人家的助理当人家的秘书去当师爷。",
)
_register(
    "天相", "命宫", "主星册·天相",
    category="personality", direction="吉", strength="强",
    text="天相入命的人从来不去想权位，她只是很好，她是很好的辅佐的人才，位高无权。",
)
_register(
    "天相", "命宫", "主星册·天相",
    category="marriage", direction="吉", strength="强",
    text="我们算命的时候女孩子是天相星最好，天相是什么，天上的宰相，是非常好的良佐，辅佐的人才。",
)

# 天梁：南斗阴贵星，文武双全
_register(
    "天梁", "命宫", "主星册·天梁",
    category="career", direction="吉", strength="强",
    text="天梁星是文武双全，允文允武的星。所以很多人武官天梁星，文官也有天梁星。",
)
_register(
    "天梁", "命宫", "主星册·天梁",
    category="health", direction="吉", strength="强",
    text="天梁星是阳星，化权的时候是武官权，像司法官外交官，大部分人的司法官是天梁星化权的。",
)
_register(
    "天梁", "命宫", "主星册·天梁",
    category="personality", direction="中性", strength="中",
    text="天梁星是阳星代表男人，天机星是女的代表阴的。",
)

# 七杀：南斗杀星，将星
_register(
    "七杀", "命宫", "主星册·七杀",
    category="career", direction="吉", strength="强",
    text="七杀入命的人目大，做事情性子很急。这个如果在命宫有七杀在午，这也称为将星。",
)
_register(
    "七杀", "命宫", "主星册·七杀",
    category="personality", direction="中性", strength="中",
    text="七杀、破军跟贪狼这三颗星，全部主的是武官，主的是耗主的是劳。",
)
_register(
    "七杀", "命宫", "主星册·七杀",
    category="career", direction="凶", strength="中",
    text="七杀破军这两颗星主的是耗主的是劳，如果遇到流年遇到这两颗星的话，主劳辛苦的奔波劳碌，孤单要一个人拼命去做事情，然后呢又耗，有财钱财进来钱财出去又不容易聚财。",
)

# 破军：北斗杀星，流浪在外
_register(
    "破军", "命宫", "主星册·破军",
    category="personality", direction="中性", strength="中",
    text="破军星比较孤僻，个性很孤僻，非常的孤，一个人孤芳自赏。吃五谷杂粮怎么吃都不胖。",
)
_register(
    "破军", "命宫", "主星册·破军",
    category="fortune", direction="中性", strength="中",
    text="破军星是要流浪在外要走天下，技术专长捧着饭碗走天下。对钱财不重利，男人女人都一样。",
)
_register(
    "破军", "命宫", "主星册·破军",
    category="marriage", direction="中性", strength="中",
    text="破军星对钱财不重利，然后一般来说，这种人男人女人都会婚姻都很晚都会晚婚，这是英星入庙。",
)

# 文昌文曲：六吉星，文星
_register(
    "文昌", "命宫", "主星册·文昌文曲",
    category="career", direction="吉", strength="强",
    text="文昌星代表的是科甲读书考试。没有会到，就不是金榜题名了。",
)
_register(
    "文曲", "命宫", "主星册·文昌文曲",
    category="career", direction="吉", strength="强",
    text="文曲星主的是才艺博学，博学多能的人。完全着重在读书文笔才华。",
)
_register(
    "文曲", "命宫", "主星册·文昌文曲",
    category="personality", direction="中性", strength="中",
    text="文曲星呢，顾名思义看起来就是比较斯文文绉绉的。",
)

# 左辅右弼：六吉星，辅星
_register(
    "左辅", "命宫", "主星册·左辅右弼",
    category="career", direction="吉", strength="强",
    text="左辅和右弼是辅助紫微星的，只要是看到紫微星出现的时候，如果有辅弼来会，这紫微星就变成君王诸侯之相。",
)
_register(
    "右弼", "命宫", "主星册·左辅右弼",
    category="career", direction="吉", strength="强",
    text="我生下来就是辅弼之才，我当你的助手，我当你的秘书，我当你的助教，很好。",
)
_register(
    "右弼", "命宫", "主星册·左辅右弼",
    category="fortune", direction="吉", strength="中",
    text="反过来紫微星呢，应该有辅弼星来会，同样辅弼星也有紫微星来会。",
)

# ============================================================================
# 六煞星断言
# ============================================================================

_register(
    "擎羊", "命宫", "主星册·六杀",
    category="personality", direction="凶", strength="中",
    text="六杀出现的时候，它在你的命宫有人的宫，基本上脱离不了通通是杀星。",
)
_register(
    "陀罗", "命宫", "主星册·六杀",
    category="personality", direction="凶", strength="中",
    text="六杀出现的时候，它在你的命宫有人的宫，基本上脱离不了通通是杀星。",
)
_register(
    "火星", "命宫", "主星册·六杀",
    category="personality", direction="凶", strength="中",
    text="六杀出现的时候，它在你的命宫有人的宫，基本上脱离不了通通是杀星。",
)
_register(
    "铃星", "命宫", "主星册·六杀",
    category="personality", direction="凶", strength="中",
    text="六杀出现的时候，它在你的命宫有人的宫，基本上脱离不了通通是杀星。",
)
_register(
    "天空", "命宫", "主星册·六杀",
    category="fortune", direction="凶", strength="中",
    text="六杀出现的时候，如果在命宫有人的宫，基本上脱离不了通通是杀星。",
)
_register(
    "地劫", "命宫", "主星册·六杀",
    category="fortune", direction="凶", strength="中",
    text="六杀出现的时候，如果在命宫有人的宫，基本上脱离不了通通是杀星。",
)
_register(
    "六杀", "命宫", "主星册·六杀",
    category="fortune", direction="凶", strength="强",
    text="我们一个宫里面有个原则，就是说你有杀星在里面，有吉星来的话杀星就杀的力量很差，什么吉星都没有，一颗小杀星，哪怕一个地劫或一个天空星，可能都会要你的命。",
)

# ============================================================================
# 特殊辅星断言
# ============================================================================

_register(
    "禄存", "命宫", "主星册·禄存",
    category="wealth", direction="吉", strength="强",
    text="禄存星同于化禄，禄存最重要的是指的是财星。禄存星在命，这种人就是标准的小气。",
)
_register(
    "禄存", "财帛宫", "主星册·禄存",
    category="wealth", direction="吉", strength="强",
    text="如果在财帛流年逢到禄存的时候，财星都很旺事业上都会大赚钱。",
)
_register(
    "天魁", "命宫", "主星册·天魁天钺",
    category="career", direction="吉", strength="强",
    text="天魁天钺这两颗星呢也是主科甲读书星，读书星如果有个人的命里面文昌文曲也来会，天魁天钺也来会。",
)
_register(
    "天钺", "命宫", "主星册·天魁天钺",
    category="career", direction="吉", strength="强",
    text="天魁天钺这两颗星呢也是主科甲读书星，读书星如果有个人的命里面文昌文曲也来会。",
)
_register(
    "天魁", "命宫", "主星册·天魁天钺",
    category="career", direction="吉", strength="中",
    text="天魁还有天钺，这两个是科甲星，科甲星夹到命，命宫旁边的天魁天钺夹的时候夹贵。",
)
_register(
    "天马", "命宫", "主星册·天马",
    category="career", direction="中性", strength="中",
    text="天马星是吃苦耐劳你奔波啊。",
)
_register(
    "红鸾", "命宫", "主星册·红鸾天喜",
    category="marriage", direction="吉", strength="强",
    text="红鸾天喜星，顾名思义就是这样红鸾心动嘛，中国人说红鸾心动这个成语是从斗数里面来的。",
)
_register(
    "天喜", "命宫", "主星册·红鸾天喜",
    category="marriage", direction="吉", strength="强",
    text="红鸾天喜星代表喜庆的星，天喜红鸾星一定相对。",
)
_register(
    "红鸾", "命宫", "主星册·红鸾天喜",
    category="marriage", direction="中性", strength="中",
    text="红鸾天喜星牛郎织女星。",
)

# ============================================================================
# 庙旺利陷总则断言
# ============================================================================

_register(
    "庙旺利陷", "总论", "主星册·庙旺利陷",
    category="fortune", direction="中性", strength="强",
    text="所有的星在庙旺的时候都是最好，在利的时候是平平，在陷的时候是最差。如果你遇到杀星在陷地的话，那是差中更差，凶中之凶。",
)
_register(
    "庙旺利陷", "总论", "主星册·庙旺利陷",
    category="fortune", direction="中性", strength="强",
    text="一个星在里面如果不亮的时候，它没有其他吉星来会，你看只有一个杀星，那杀星就很强了。",
)

# ============================================================================
# 格局断言
# ============================================================================

_register(
    "日月反背", "格局", "格局册·必定成格",
    category="fortune", direction="中性", strength="强",
    text="日月反背主披星戴月，工作常常白天忙完晚上比白天还忙。这是六亲不靠，靠不到父母亲。",
)
_register(
    "日月反背", "格局", "格局册·必定成格",
    category="fortune", direction="凶", strength="强",
    text="如果这个日月反背在父母宫又化忌，太阴化忌代表妈妈，太阳也在这边，那父母亲代表会不在身边，或者父母双亡。",
)
_register(
    "杀破狼", "格局", "格局册·凶格",
    category="fortune", direction="凶", strength="中",
    text="七杀、破军跟贪狼这三颗星，全部主的是武官，主的是耗主的是劳。流年逢到这两颗星的话，主劳辛苦的奔波劳碌。",
)
_register(
    "半空折翅", "格局", "格局册·凶格",
    category="fortune", direction="凶", strength="强",
    text="有的人命很好就限不好，就半空折翅。不到30岁就走人了。",
)
_register(
    "廉贪落陷", "格局", "格局册·凶格",
    category="fortune", direction="凶", strength="强",
    text="廉贞贪狼落陷，这个有个特别一个格局，我给它叫半空折翅，这种八字在算命的立场上，就是属于一种天罗地网。",
)

# ============================================================================
# 四化断言
# ============================================================================

_register(
    "化科", "四化", "四化册·化科",
    category="career", direction="吉", strength="强",
    text="科本身，第一个科名，比如说我们参加考试金榜题名，这是一个科。还有我们文章写的很好，文笔写的很好也是科。",
)
_register(
    "化权", "四化", "四化册·化权",
    category="career", direction="吉", strength="强",
    text="它代表的是官印。当官的时候我们有个印盖一下，那个就是官印。第二个它代表的是性刚，个性很刚。命里面有化权的人，先天上面来说，这种人天生的就是一个领导者。",
)
_register(
    "化权", "四化", "四化册·化权",
    category="career", direction="吉", strength="强",
    text="很多将领，很多总经理，很多银行的经理，很多厂长，就是命中他就有权的人。",
)
_register(
    "化禄", "四化", "四化册·化禄",
    category="wealth", direction="吉", strength="强",
    text="禄就是财，钱财。禄是性守，性比较守。生下来的话，权禄这是豪门，巨富啊，生在家里面一定很有钱。",
)
_register(
    "化禄", "四化", "四化册·化禄",
    category="wealth", direction="吉", strength="强",
    text="有的人禄在财帛宫他自己会做生意。有的人禄在命宫，先天就会有祖业到他身上去。",
)
_register(
    "化忌", "四化", "四化册·化忌",
    category="fortune", direction="凶", strength="强",
    text="这个忌我们意思就是说有凶星在兄弟宫。这忌是一个杀星。化忌代表劫杀。第二个化忌代表想不开。",
)

# ============================================================================
# 疾厄断言
# ============================================================================

_register(
    "疾厄", "疾厄宫", "疾厄册·核心方法论",
    category="health", direction="中性", strength="强",
    text="诸位看斗数上面的疾厄宫，参考可以。但是你真的批的时候他就没有用。我们算命要讲致命伤。",
)
_register(
    "疾厄", "疾厄宫", "疾厄册·核心方法论",
    category="health", direction="中性", strength="中",
    text="七杀在疾厄宫代表痔疮，这个不重要。",
)

# ============================================================================
# 十二宫总断言
# ============================================================================

_register(
    "命宫", "命宫", "十二宫册·命宫",
    category="personality", direction="中性", strength="强",
    text="我们在看命宫的时候，命宫讲的是就是你本人你自己，讲的你的先天。什么叫做先天，生下来你是什么咖，讲的是先天。从命宫一看就已经知道成败。",
)
_register(
    "兄弟宫", "兄弟宫", "十二宫册·兄弟宫",
    category="fortune", direction="凶", strength="强",
    text="你的兄弟宫化忌。这个忌我们意思就是说有凶星在兄弟宫。有两个解释。第一个，有兄弟不和，非常不和睦。第二个解释，有兄弟夭折。第三个解释，兄弟姐妹合伙破财。",
)
_register(
    "夫妻宫", "夫妻宫", "十二宫册·夫妻宫",
    category="marriage", direction="中性", strength="强",
    text="夫妻顾名思义就是看她的婚姻。如果是光论宫的时候，你光看夫妻宫你大错特错，一定要看福德宫。",
)
_register(
    "子女宫", "子女宫", "十二宫册·子女宫",
    category="fortune", direction="中性", strength="中",
    text="真的要讨论子女宫的将来如何，最好的方式就是看子女的八字。",
)
_register(
    "财帛宫", "财帛宫", "十二宫册·财帛宫",
    category="wealth", direction="中性", strength="强",
    text="财帛是什么，你到私人企业你自己去做生意当老板。有的星代表财。还有财帛宫就是财星，也是家财万贯。",
)
_register(
    "迁移宫", "迁移宫", "十二宫册·迁移宫",
    category="fortune", direction="中性", strength="强",
    text="有的人他命中注定他要到迁移。有的人必须要到外地经历一圈，回来以后他才会好。",
)
_register(
    "仆役宫", "仆役宫", "十二宫册·仆役宫",
    category="fortune", direction="凶", strength="强",
    text="仆役宫太凶太差，都是耗星的话，合伙你还想赚钱啊，必败。",
)
_register(
    "官禄宫", "官禄宫", "十二宫册·官禄宫",
    category="career", direction="中性", strength="强",
    text="官禄，你到公家单位去领固定的薪水。有的星代表官，他带个印，所以当官的有个官印。官星一定要进入官禄宫最好。财星要进入财帛宫最好。叫做适得其所，叫做正位。",
)
_register(
    "田宅宫", "田宅宫", "十二宫册·田宅宫",
    category="fortune", direction="中性", strength="强",
    text="紫微斗数的田宅有两个意义。第一个代表你的祖业、祖产有多少。第二个田宅代表你置产吉与不吉。",
)
_register(
    "田宅宫", "田宅宫", "十二宫册·田宅宫",
    category="fortune", direction="凶", strength="强",
    text="有的人火星落在田宅，结果他买了房子一把火烧了。",
)
_register(
    "福德宫", "福德宫", "十二宫册·福德宫",
    category="fortune", direction="中性", strength="强",
    text="祸福无门，咎由自取。我曾经批过夫妻宫很好，那福德宫很烂，散夫妻要散。同时看看福德宫。福德宫代表夫妻的关系，也代表一世的福禄。",
)
_register(
    "父母宫", "父母宫", "十二宫册·父母宫",
    category="fortune", direction="中性", strength="中",
    text="有的人出来的时候父母宫是黯淡无光的，那这个有可能是庶出，就是给人家养的，或者螟蛉子，抱领养的。",
)


# ── Z50 扩容（2026-10-06）：十二宫总论补全，逐字取自精选集十二宫册 ──

_register(
    "命宫", "命宫", "十二宫册·命宫",
    category="personality", direction="中性", strength="中",
    text="命宫探讨的东西就是一般的我们个性，我们的动作还有我们的长相，这些外相而已。",
)
_register(
    "兄弟宫", "兄弟宫", "十二宫册·兄弟宫",
    category="fortune", direction="凶", strength="中",
    text="兄弟在一起不和，你看他的眉毛。那个眉毛乱七八糟长得前后。那他突然都是颠倒，左叉右叉。兄弟不和，他就写在脸上。",
)
_register(
    "兄弟宫", "兄弟宫", "十二宫册·兄弟宫",
    category="fortune", direction="中性", strength="弱",
    text="眉毛断掉，断眉。左边眉毛代表兄兄弟，右边眉毛代表姐妹。",
)
_register(
    "夫妻宫", "夫妻宫", "十二宫册·夫妻宫",
    category="marriage", direction="中性", strength="强",
    text="如果你的夫妻宫化权，代表你的那一半在个性上面领导力很强，主见很强的一个人。",
)
_register(
    "夫妻宫", "夫妻宫", "十二宫册·夫妻宫",
    category="marriage", direction="中性", strength="弱",
    text="外面所有坊间的算命，都是必须要会到红鸾天喜星才会结婚其实不然",
)
_register(
    "子女宫", "子女宫", "十二宫册·子女宫",
    category="fortune", direction="中性", strength="弱",
    text="外面很多相书上去统计几男几女，实际上你不用去，光算男的就好了。算男的有几个。",
)
_register(
    "子女宫", "子女宫", "十二宫册·子女宫",
    category="fortune", direction="中性", strength="中",
    text="你的命里面两个，你的太太命里面两个，加起来的话四个儿子。他的命上两个，他就会生到两个脸孔像他。他的另外一半命里两个，生的另外两个脸孔像她。",
)
_register(
    "仆役宫", "仆役宫", "十二宫册·仆役宫",
    category="fortune", direction="中性", strength="弱",
    text="仆役也可以叫朋友宫，交友宫，这个名词不重要。你要知道它的意义最重要。",
)
_register(
    "仆役宫", "仆役宫", "十二宫册·仆役宫",
    category="fortune", direction="中性", strength="弱",
    text="这个宫里面落入了星，我们看它的星辰的吉凶来断定。",
)
_register(
    "官禄宫", "官禄宫", "十二宫册·官禄宫",
    category="career", direction="中性", strength="中",
    text="有的星代表官，他带个印，所以当官的有个官印。",
)
_register(
    "官禄宫", "官禄宫", "十二宫册·官禄宫",
    category="career", direction="凶", strength="强",
    text="官星一定要进入官禄宫最好。财星要进入财帛宫最好。叫做适得其所，叫做正位。你的财星跑到官星里面就是贪官。",
)
_register(
    "田宅宫", "田宅宫", "十二宫册·田宅宫",
    category="fortune", direction="凶", strength="弱",
    text="还有的人田宅宫是小人星，看不到的小人。",
)
_register(
    "福德宫", "福德宫", "十二宫册·福德宫",
    category="fortune", direction="中性", strength="中",
    text="祸福无门，咎由自取。咎是咎在易经里面就是悔恨后悔懊恼，都是自找的。",
)
_register(
    "福德宫", "福德宫", "十二宫册·福德宫",
    category="fortune", direction="凶", strength="中",
    text="福德宫代表夫妻的关系，也代表一世的福禄，他的财禄他的事业。所以福德宫很差的人很累。",
)
_register(
    "父母宫", "父母宫", "十二宫册·父母宫",
    category="fortune", direction="中性", strength="弱",
    text="一上一下，左右不对称。我们眼睛是平的。他怎么一上一下。庶出，领养。",
)
_register(
    "父母宫", "父母宫", "十二宫册·父母宫",
    category="fortune", direction="中性", strength="弱",
    text="我养儿子烦恼的时候纹路是这样的。我养不是我的儿子，领养过来的儿子，烦恼的时候皱的纹路不一样，鼻子变成一条直纹。",
)



# ============================================================================
# Z51 扩容（2026-10-07）：星×他宫断言，逐字取自 ziwei-samples-toolkit
# corpus/verified（已验证倪师原话册）。仅收本机制可无歧义触发的条目；
# 含地支宫位或双星复合前提的原话（如「火星地空在丑=肝」「廉破在福德=横祸」
# 「贪狼在午非桃花」）不入本库，待断言引擎支持条件触发后再迁，避免死数据。
# 出处照抄原册标注：02-palaces 财帛/迁移/田宅三节原文无"出处"行，故不标集数。
# ============================================================================

_register(
    "太阴", "财帛", "02-palaces·财帛宫",
    category="wealth", direction="吉", strength="强",
    text="太阴入财帛 = 正财",
)
_register(
    "武曲", "财帛", "02-palaces·财帛宫",
    category="wealth", direction="吉", strength="强",
    text="武曲入财帛 = 大财星",
)
_register(
    "紫微", "财帛", "02-palaces·财帛宫",
    category="wealth", direction="中性", strength="中",
    text="紫微入财帛 = 守成为主（不主动生财）",
)
_register(
    "禄存", "财帛", "02-palaces·财帛宫",
    category="wealth", direction="中性", strength="中",
    text="禄存入财帛 = 守财能力强（小气鬼）",
)
_register(
    "紫微", "迁移", "02-palaces·迁移宫",
    category="fortune", direction="中性", strength="强",
    text="紫微在迁移 = 外地会逢贵人，但也是孤君象",
)
_register(
    "紫微", "田宅", "02-palaces·田宅宫",
    category="fortune", direction="吉", strength="中",
    text="紫微入田宅 = 祖产有规模",
)
_register(
    "擎羊", "疾厄", "05-illness·煞星入疾厄(天纪11、12)",
    category="health", direction="凶", strength="强",
    text="擎羊、陀罗入疾厄 = 开刀见血光",
)
_register(
    "陀罗", "疾厄", "05-illness·煞星入疾厄(天纪11、12)",
    category="health", direction="凶", strength="强",
    text="擎羊、陀罗入疾厄 = 开刀见血光",
)

# ===========================================================================
# 查询接口
# ===========================================================================

def get_assertions(star: str, palace: str) -> List[NihaiAssertion]:
    """按星×宫查询全部断言（同星宫可有多条）.

    Args:
        star: 主星名（如 "紫微"）
        palace: 宫位名（如 "命宫"）

    Returns:
        NihaiAssertion 列表（无命中返回空列表）
    """
    return list(_NIHAI_ASSERTIONS.get((star, palace), []))


def get_assertion(star: str, palace: str) -> Optional[NihaiAssertion]:
    """按星×宫查询首条断言（兼容旧接口）.

    Returns:
        NihaiAssertion 或 None（未命中则不产生断言）
    """
    items = _NIHAI_ASSERTIONS.get((star, palace))
    return items[0] if items else None


def get_all_assertions() -> List[NihaiAssertion]:
    """返回全部断言条目（供测试和审计用）."""
    return [a for items in _NIHAI_ASSERTIONS.values() for a in items]


def count_assertions() -> int:
    """返回断言条目总数（含同星宫多条）."""
    return sum(len(items) for items in _NIHAI_ASSERTIONS.values())


def count_keys() -> int:
    """返回 (星, 宫) 组合键数."""
    return len(_NIHAI_ASSERTIONS)


def get_palace_overview(palace: str) -> List[NihaiAssertion]:
    """按宫位查『本宫总论』断言（自动归一宫名后缀）.

    命盘宫名不带"宫"字（如 "夫妻"/"疾厄"），而总论注册键带"宫"
    （("夫妻宫","夫妻宫")；疾厄册特例 ("疾厄","疾厄宫")）。
    本函数按 (X宫,X宫) → (X不带宫,X宫) 顺序回退，避免调用方各自拼键。
    """
    bare = palace[:-1] if palace.endswith("宫") else palace
    full = bare + "宫"
    items = _NIHAI_ASSERTIONS.get((full, full))
    if not items:
        items = _NIHAI_ASSERTIONS.get((bare, full))
    return list(items or [])


def get_assertions_by_category(category: str) -> List[NihaiAssertion]:
    """按类别过滤断言."""
    return [a for items in _NIHAI_ASSERTIONS.values() for a in items
            if a.category == category]


# ===========================================================================
# 公开导出
# ===========================================================================

__all__ = [
    "NihaiAssertion",
    "get_assertion",
    "get_assertions",
    "get_palace_overview",
    "get_all_assertions",
    "count_assertions",
    "count_keys",
    "get_assertions_by_category",
]
