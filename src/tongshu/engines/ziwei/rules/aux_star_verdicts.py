"""Z77: 辅曜/煞曜/杂曜断语层——《紫微斗数全书·诸星问答论》原文录入。

每条遵守：原典出处→原文→适用条件→星曜→宫位→断言。
status=VERIFIED 表示原文已核对本地《全书》文本。

Z80-G 审核标注（2026-10-14）：本模块在 src/ 内**零引用**（仅测试/文档提及）。
  处置建议：证据资产 —— 辅煞杂曜断语（诸星问答论），与 palace_star_verdicts/nihai 重叠
  依据：docs/audit/ZIWEI_ENGINE_FULL_AUDIT_20261014.md
"""
from __future__ import annotations

SRC = "紫微斗数全书·诸星问答论"

# 辅曜
AUX_STAR_VERDICTS = [
    {"star": "左辅", "palace": "命宫", "verbatim": "左辅帝极主宰之星，守身命诸宫降福。主人形貌敦厚慷慨风流。紫府禄权若得三合冲照，主文武大贵。火忌冲破，虽富贵不久。", "source": SRC, "status": "VERIFIED"},
    {"star": "右弼", "palace": "命宫", "verbatim": "右弼帝极主宰之星，守身命文墨精通。紫府吉星同垣，财官双美，文武双全。羊陀火忌冲破，下局断之。女人贤良有志，纵四杀冲破，不为下贱。", "source": SRC, "status": "VERIFIED"},
    {"star": "文昌", "palace": "命宫", "verbatim": "文昌主科甲，守身命主人幽闲儒雅，清秀魁梧，博文广记，机变异常，一举成名，披绯衣紫，福寿双全。纵四杀冲破不为下贱。", "source": SRC, "status": "VERIFIED"},
    {"star": "文曲", "palace": "命宫", "verbatim": "文曲属水，北斗第四星也，主科甲文车之宿。其象属水，与文昌同协，吉数最为祥，临身命中作科第之客。桃花浪暖，入仕无疑。", "source": SRC, "status": "VERIFIED"},
    {"star": "天魁", "palace": "命宫", "verbatim": "魁钺斗中司科之星，入命坐贵向贵，或得左右吉聚无不富贵。若遇大难，必得贵人成就扶助。", "source": SRC, "status": "VERIFIED"},
    {"star": "天钺", "palace": "命宫", "verbatim": "魁钺斗中司科之星，入命坐贵向贵，或得左右吉聚无不富贵。若遇大难，必得贵人成就扶助。", "source": SRC, "status": "VERIFIED"},
    {"star": "禄存", "palace": "命宫", "verbatim": "禄存北斗第三星，真人之宿，主人贵爵，掌人寿基。守身命主人慈厚信直，通文济楚。大抵此星诸宫降福消灾。", "source": SRC, "status": "VERIFIED"},
    {"star": "天马", "palace": "命宫", "verbatim": "诸宫各有制化，如身命临之谓之驿马。喜禄存、紫府、昌曲守照为吉。与禄存同宫谓之禄马交驰。", "source": SRC, "status": "VERIFIED"},
]

# 煞曜
SHA_STAR_VERDICTS = [
    {"star": "擎羊", "palace": "命宫", "verbatim": "擎羊北斗之助星。守身命性粗行暴，孤单，视亲为疏，翻恩为怨。入庙性刚果决，机谋好勇，主权贵。", "source": SRC, "status": "VERIFIED"},
    {"star": "陀罗", "palace": "命宫", "verbatim": "陀罗北斗之助星。守身命心行不正，暗泪长流，性刚威猛，作事进退。横成横破，飘荡不定。", "source": SRC, "status": "VERIFIED"},
    {"star": "火星", "palace": "命宫", "verbatim": "火星乃南斗浮星也。性气亦沉毒，刚强出众人。若得贪狼会，旺地贵无伦。三方无杀破，中年后始兴。", "source": SRC, "status": "VERIFIED"},
    {"star": "铃星", "palace": "命宫", "verbatim": "铃星乃南斗助星也。值人身命者，性格亦沉吟，形貌多异类，威势有声名。若与贪狼会，指日立边庭。", "source": SRC, "status": "VERIFIED"},
    {"star": "地空", "palace": "命宫", "verbatim": "劫空为害最愁人，才智英雄误一身，只好为僧并学术，堆金积玉也须贫。", "source": SRC, "status": "VERIFIED"},
    {"star": "地劫", "palace": "命宫", "verbatim": "劫空为害最愁人，才智英雄误一身，只好为僧并学术，堆金积玉也须贫。", "source": SRC, "status": "VERIFIED"},
]

# 杂曜
MISC_STAR_VERDICTS = [
    {"star": "天刑", "palace": "命宫", "verbatim": "天刑守命身，不为僧道定主孤刑，不夭则贫。父母兄弟不得全。入庙则吉。", "source": SRC, "status": "VERIFIED"},
    {"star": "天姚", "palace": "命宫", "verbatim": "天姚守身命，心性阴毒，多疑恐，善颜色，风流多婢，主淫。入庙旺主富贵多奴。会恶星破家败产，因色犯刑。", "source": SRC, "status": "VERIFIED"},
]

ALL_AUX_STARS = list({x["star"] for x in AUX_STAR_VERDICTS})
ALL_SHA_STARS = list({x["star"] for x in SHA_STAR_VERDICTS})
ALL_MISC_STARS = list({x["star"] for x in MISC_STAR_VERDICTS})


def count_verified() -> int:
    return sum(1 for x in AUX_STAR_VERDICTS + SHA_STAR_VERDICTS + MISC_STAR_VERDICTS if x["status"] == "VERIFIED")


def count_gap() -> int:
    return sum(1 for x in AUX_STAR_VERDICTS + SHA_STAR_VERDICTS + MISC_STAR_VERDICTS if x["status"] == "EVIDENCE_GAP")
