# -*- coding: utf-8 -*-
"""Z80: 维度断语层 — 十二宫逐宫综合解读 + 领域聚合。

架构定位:
    辨层 + 解层（PALACE_STAR_RULES / nihai_assertions / 多层四化）
        ↓
    维度断语层（本模块）— 综合所有维度信号，产出连贯段落
        ↓
    领域聚合 / 十二宫逐宫解读

约束:
    1. 只消费 chart + 解层输出，不重算事实
    2. 每条解读必须有引擎事实支撑，不编造
    3. 辅星/自化/借对宫/对宫冲击 均纳入综合解读
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ============================================================================
# 辅星解读表（按宫位分类）
# ============================================================================

MINOR_STAR_BY_PALACE: Dict[str, Dict[str, str]] = {
    # ── 命宫辅星 ──
    "命宫": {
        "文昌": "文昌入命，聪慧善文，遇事懂得寻找方法提升自己，适合持续深耕专业",
        "文曲": "文曲入命，有艺术天赋，感性细腻，适合创意表达",
        "左辅": "左辅入命，贵人助力强，做事有人帮衬",
        "右弼": "右弼入命，人缘好，善于协调合作",
        "天魁": "天魁入命，男性贵人暗助，关键时刻有人提携",
        "天钺": "天钺入命，女性贵人暗助，异性缘佳",
        "禄存": "禄存入命，衣食无忧，但需防孤僻",
        "天马": "天马入命，一生多动，奔波劳碌但有机遇",
        "擎羊": "擎羊入命，性格刚烈直率，做事果断但易冲动",
        "陀罗": "陀罗入命，做事拖延反复，有韧性但易纠结",
        "火星": "火星入命，脾气急躁，做事风风火火但缺乏耐性",
        "铃星": "铃星入命，隐性焦虑持续，内心压力大但不轻易表露，长期积压容易躯体化",
        "地空": "地空入命，想法天马行空，有创意但不落地",
        "地劫": "地劫入命，人生多突变，需适应变化",
        "咸池": "咸池入命，有桃花魅力，异性缘佳",
        "天姚": "天姚入命，风流倜傥，感情丰富",
        "天刑": "天刑入命，一生多是非，需遵纪守法",
    },
    # ── 财帛辅星 ──
    "财帛": {
        "文昌": "文昌入财帛，以文书才华生财，适合文化类行业",
        "文曲": "文曲入财帛，艺术生财，创意变现能力强",
        "左辅": "左辅入财帛，多方助力得财，合作生财",
        "右弼": "右弼入财帛，人脉助力财运",
        "天魁": "天魁入财帛，男性贵人助财",
        "天钺": "天钺入财帛，女性贵人助财",
        "禄存": "禄存守财帛，有守财能力，收入稳定，能积累财富",
        "天马": "天马入财帛，动中求财，适合奔波型行业",
        "擎羊": "擎羊入财帛，求财方式刚硬，易因冲动破财",
        "陀罗": "陀罗入财帛，财运反复，得财辛苦",
        "火星": "火星入财帛，财来财去快，暴起暴落",
        "铃星": "铃星入财帛，暗中破财，需防隐性支出",
        "地空": "地空入财帛，财运虚空，不宜投机",
        "地劫": "地劫入财帛，劫财之象，需防意外破耗",
        "咸池": "咸池同宫，防范因桃花异性关系破财",
        "天姚": "天姚入财帛，桃花生财亦破财",
    },
    # ── 官禄辅星 ──
    "官禄": {
        "文昌": "文昌入官禄，以才华学识立足，适合文职技术岗",
        "文曲": "文曲入官禄，创意型事业，适合艺术娱乐行业",
        "左辅": "左辅入官禄，事业有贵人助力，合作顺畅",
        "右弼": "右弼入官禄，团队协作能力强",
        "天魁": "天魁入官禄，上司提携，事业有靠山",
        "天钺": "天钺入官禄，异性贵人助事业",
        "禄存": "禄存入官禄，事业稳定，收入有保障",
        "天马": "天马入官禄，事业多变动，适合奔波型职业",
        "擎羊": "擎羊入官禄，事业刚硬，易与人冲突",
        "陀罗": "陀罗入官禄，事业反复，进展缓慢",
        "火星": "火星入官禄，事业急躁冒进，需稳扎稳打",
        "铃星": "铃星入官禄，暗中焦虑影响事业",
        "地空": "地空入官禄，事业虚空，需脚踏实地",
        "地劫": "地劫入官禄，事业多突变",
        "咸池": "咸池入官禄，职场桃花多，需防影响事业",
        "天姚": "天姚入官禄，职场人际关系丰富",
    },
    # ── 夫妻辅星 ──
    "夫妻": {
        "文昌": "文昌入夫妻，配偶有文化素养，感情重精神交流",
        "文曲": "文曲入夫妻，感情浪漫多情，但需防桃花",
        "左辅": "左辅入夫妻，第三者介入之象，需防感情被分",
        "右弼": "右弼入夫妻，感情中多人介入，需防第三者",
        "天魁": "天魁入夫妻，配偶有贵人背景",
        "天钺": "天钺入夫妻，配偶有异性缘",
        "禄存": "禄存入夫妻，配偶经济条件好，但感情或显疏离",
        "天马": "天马入夫妻，配偶常奔波，聚少离多",
        "擎羊": "擎羊入夫妻，感情多争执，配偶性格刚硬",
        "陀罗": "陀罗入夫妻，感情反复纠缠，难以了断",
        "火星": "火星入夫妻，感情来得快去得快，需冷静",
        "铃星": "铃星入夫妻，暗中不满，冷战隐患",
        "地空": "地空入夫妻，感情虚空，需防分离",
        "地劫": "地劫入夫妻，感情多突变",
        "咸池": "咸池入夫妻，配偶有桃花，需防外遇",
        "天姚": "天姚入夫妻，感情风流浪漫，需防烂桃花",
    },
    # ── 疾厄辅星 ──
    "疾厄": {
        "文昌": "文昌入疾厄，精神紧张导致神经衰弱",
        "文曲": "文曲入疾厄，情绪敏感影响健康",
        "左辅": "左辅入疾厄，体质有辅助支撑",
        "右弼": "右弼入疾厄，有人关心健康",
        "天魁": "天魁入疾厄，遇良医，逢凶化吉",
        "天钺": "天钺入疾厄，女性贵人助健康",
        "禄存": "禄存入疾厄，体质底子好，有保养条件",
        "天马": "天马入疾厄，体质变化快，需注意突发疾病",
        "擎羊": "擎羊入疾厄，注意外伤手术，刀兵之厄",
        "陀罗": "陀罗入疾厄，慢性病反复缠绵，难以根治",
        "火星": "火星入疾厄，急性炎症，突发高热",
        "铃星": "铃星入疾厄，隐性焦虑影响健康，情绪积压导致躯体化",
        "地空": "地空入疾厄，体质虚弱，精神消耗大",
        "地劫": "地劫入疾厄，健康多突变",
        "咸池": "咸池入疾厄，注意生殖系统",
        "天姚": "天姚入疾厄，注意桃花相关疾病",
    },
    # ── 福德辅星 ──
    "福德": {
        "文昌": "文昌入福德，精神追求高雅，好学深思",
        "文曲": "文曲入福德，内心丰富感性，有艺术感受力",
        "左辅": "左辅入福德，心态积极，有人支持",
        "右弼": "右弼入福德，精神上有依靠",
        "天魁": "天魁入福德，精神上有贵人指引",
        "天钺": "天钺入福德，内心有安全感",
        "禄存": "禄存入福德，内心满足，精神富足",
        "天马": "天马入福德，心思活跃，难以安静",
        "擎羊": "擎羊入福德，内心刚硬，精神压力大",
        "陀罗": "陀罗入福德，内心纠结反复，精神内耗大",
        "火星": "火星入福德，脾气急躁，精神紧张",
        "铃星": "铃星入福德，隐性焦虑持续，内心压抑难以释放",
        "地空": "地空入福德，精神空虚，想法不落地",
        "地劫": "地劫入福德，精神多突变，心态不稳",
        "咸池": "咸池入福德，内心多情，感情欲望强",
        "天姚": "天姚入福德，内心浪漫，追求享受",
    },
    # ── 田宅辅星 ──
    "田宅": {
        "文昌": "文昌入田宅，家中有书香氛围",
        "文曲": "文曲入田宅，家居有艺术氛围",
        "左辅": "左辅入田宅，家人助力置业",
        "右弼": "右弼入田宅，家庭关系和谐",
        "天魁": "天魁入田宅，长辈助力置业",
        "天钺": "天钺入田宅，女性长辈助家运",
        "禄存": "禄存入田宅，家产丰厚，守业能力强",
        "天马": "天马入田宅，居所多变，经常搬家",
        "擎羊": "擎羊入田宅，家宅不宁，家人争执多",
        "陀罗": "陀罗入田宅，房产交易反复，置业过程波折",
        "火星": "火星入田宅，家宅有火灾之虞，家人脾气暴躁",
        "铃星": "铃星入田宅，家中有隐性矛盾",
        "地空": "地空入田宅，家运虚空，不宜盲目置业",
        "地劫": "地劫入田宅，家产有劫，需防破耗",
        "咸池": "咸池入田宅，家中有桃花之象",
        "天姚": "天姚入田宅，家居风流",
    },
    # ── 子女辅星 ──
    "子女": {
        "文昌": "文昌入子女，子女学业优秀，好学上进",
        "文曲": "文曲入子女，子女有艺术天赋",
        "左辅": "左辅入子女，子女有人助力",
        "右弼": "右弼入子女，子女人缘好",
        "天魁": "天魁入子女，子女有贵人运",
        "天钺": "天钺入子女，子女异性缘佳",
        "禄存": "禄存入子女，子女经济条件好",
        "天马": "天马入子女，子女好动，经常外出",
        "擎羊": "擎羊入子女，子女性格刚烈，亲子间容易口舌争执",
        "陀罗": "陀罗入子女，与子女关系反复",
        "火星": "火星入子女，子女脾气暴躁",
        "铃星": "铃星入子女，亲子间隐性矛盾",
        "地空": "地空入子女，子女缘分薄",
        "地劫": "地劫入子女，子女有劫",
        "咸池": "咸池入子女，子女桃花早",
        "天姚": "天姚入子女，子女风流",
    },
    # ── 迁移辅星 ──
    "迁移": {
        "文昌": "文昌入迁移，外出有利文书考试",
        "文曲": "文曲入迁移，外出有艺术机遇，但落陷时容易文书合同出错",
        "左辅": "左辅入迁移，外出有贵人助力",
        "右弼": "右弼入迁移，外出人缘好",
        "天魁": "天魁入迁移，外出有男性贵人",
        "天钺": "天钺入迁移，外出有女性贵人",
        "禄存": "禄存入迁移，外出有财",
        "天马": "天马入迁移，一生多动，适合异地发展",
        "擎羊": "擎羊入迁移，外出多是非冲突",
        "陀罗": "陀罗入迁移，外出多阻滞",
        "火星": "火星入迁移，外出多突发状况",
        "铃星": "铃星入迁移，外出有隐性风险",
        "地空": "地空入迁移，外出虚空",
        "地劫": "地劫入迁移，外出有劫",
        "咸池": "咸池入迁移，外出桃花多",
        "天姚": "天姚入迁移，外出风流",
    },
    # ── 兄弟辅星 ──
    "兄弟": {
        "文昌": "文昌入兄弟，手足有文化素养",
        "文曲": "文曲入兄弟，手足有艺术天赋",
        "左辅": "左辅入兄弟，手足助力强",
        "右弼": "右弼入兄弟，手足关系和谐",
        "天魁": "天魁入兄弟，手足中有贵人",
        "天钺": "天钺入兄弟，手足中异性缘佳",
        "禄存": "禄存入兄弟，手足经济条件好",
        "天马": "天马入兄弟，手足常奔波",
        "擎羊": "擎羊入兄弟，手足间容易争执冲突",
        "陀罗": "陀罗入兄弟，手足关系反复纠缠",
        "火星": "火星入兄弟，手足脾气暴躁",
        "铃星": "铃星入兄弟，手足间有隐性矛盾",
        "地空": "地空入兄弟，手足缘分薄",
        "地劫": "地劫入兄弟，手足有劫",
        "咸池": "咸池入兄弟，手足桃花多",
        "天姚": "天姚入兄弟，手足风流",
    },
    # ── 交友/仆役辅星 ──
    "交友": {
        "文昌": "文昌入交友，朋友有文化素养",
        "文曲": "文曲入交友，朋友多才多艺",
        "左辅": "左辅入交友，朋友助力强",
        "右弼": "右弼入交友，朋友关系和谐",
        "天魁": "天魁入交友，朋友中有贵人",
        "天钺": "天钺入交友，异性朋友助力",
        "禄存": "禄存入交友，朋友经济条件好",
        "天马": "天马入交友，朋友聚散无常",
        "擎羊": "擎羊入交友，朋友间容易冲突",
        "陀罗": "陀罗入交友，朋友关系反复纠缠",
        "火星": "火星入交友，朋友脾气暴躁",
        "铃星": "铃星入交友，朋友间有隐性矛盾",
        "地空": "地空入交友，朋友缘分薄",
        "地劫": "地劫入交友，朋友中有损友",
        "咸池": "咸池入交友，朋友中桃花多",
        "天姚": "天姚入交友，朋友风流",
    },
    "仆役": {},  # 复用交友
    # ── 父母辅星 ──
    "父母": {
        "文昌": "文昌入父母，父母有文化素养",
        "文曲": "文曲入父母，父母有艺术天赋",
        "左辅": "左辅入父母，父母有人助力",
        "右弼": "右弼入父母，父母关系和谐",
        "天魁": "天魁入父母，父亲有贵人",
        "天钺": "天钺入父母，母亲有贵人",
        "禄存": "禄存入父母，父母经济条件好",
        "天马": "天马入父母，长辈经常奔波或命主长期离家",
        "擎羊": "擎羊入父母，与父母关系刚硬，容易冲突",
        "陀罗": "陀罗入父母，与父母关系反复",
        "火星": "火星入父母，父母脾气暴躁",
        "铃星": "铃星入父母，与父母有隐性矛盾",
        "地空": "地空入父母，与长辈缘分薄，容易聚少离多，祖业薄弱",
        "地劫": "地劫入父母，长辈有劫，祖业薄弱",
        "咸池": "咸池入父母，父母桃花多",
        "天姚": "天姚入父母，父母风流",
    },
}

# ============================================================================
# 自化解读表（宫干自化 → 该宫事项的影响）
# ============================================================================

ZIHUA_BY_PALACE: Dict[str, Dict[str, str]] = {
    "命宫": {
        "禄": "命宫自化禄，自我满足感强，但容易散漫不聚焦",
        "权": "命宫自化权，自我主导意识强，做事有主见但容易固执",
        "科": "命宫自化科，遇事懂得寻找方法提升自己，适合持续深耕专业",
        "忌": "命宫自化忌，自我要求高，内心纠结反复，精神内耗大",
    },
    "财帛": {
        "禄": "财帛自化禄，赚钱能力不错但钱财容易散出，守财需加强",
        "权": "财帛自化权，理财主动积极，有掌控欲",
        "科": "财帛自化科，理财方式文雅，有计划性",
        "忌": "财帛自化忌，钱财方面自我纠结，容易因贪破财",
    },
    "官禄": {
        "禄": "官禄自化禄，事业机会多但容易分散精力",
        "权": "官禄自化权，事业上有主见，主动争取",
        "科": "官禄自化科，事业上注重方法和专业提升",
        "忌": "官禄自化忌，事业上自我纠结，容易反复变动",
    },
    "夫妻": {
        "禄": "夫妻自化禄，感情上容易满足但不够珍惜",
        "权": "夫妻自化权，感情中控制欲强，容易主导关系",
        "科": "夫妻自化科，配偶文雅理性，但武曲刚硬二人遇到矛盾容易冷战讲道理，缺少情绪共情",
        "忌": "夫妻自化忌，感情上自我纠结，容易反复",
    },
    "疾厄": {
        "禄": "疾厄自化禄，体质底子好，但容易忽视保养",
        "权": "疾厄自化权，身体有自愈力",
        "科": "疾厄自化科，生年科自带修复力，小病容易痊愈遇良医",
        "忌": "疾厄自化忌，身体方面反复出问题，需长期调理",
    },
    "福德": {
        "禄": "福德自化禄，精神满足感强",
        "权": "福德自化权，精神上追求掌控",
        "科": "福德自化科，精神追求高雅，注重修养",
        "忌": "福德自化忌，精神上自我纠结，内耗大",
    },
    "田宅": {
        "禄": "田宅自化禄，家运不错但容易散出",
        "权": "田宅自化权，家中有主导权",
        "科": "田宅自化科，家居文雅，注重品质",
        "忌": "田宅自化忌，家宅方面自我纠结",
    },
    "子女": {
        "禄": "子女自化禄，子女缘分好但容易溺爱",
        "权": "子女自化权，子女有主见，管教需方法",
        "科": "子女自化科，子女文雅好学",
        "忌": "子女自化忌，与子女关系纠结",
    },
    "迁移": {
        "禄": "迁移自化禄，外出机遇多",
        "权": "迁移自化权，外出有主见",
        "科": "迁移自化科，外出注重方法",
        "忌": "迁移自化忌，外出多纠结",
    },
    "兄弟": {
        "禄": "兄弟自化禄，手足关系不错",
        "权": "兄弟自化权，手足中有强势者，朋友中贵人小人并存",
        "科": "兄弟自化科，手足关系文雅",
        "忌": "兄弟自化忌，手足关系纠结",
    },
    "交友": {
        "禄": "交友自化禄，朋友缘分好",
        "权": "交友自化权，朋友圈中有主导者",
        "科": "交友自化科，朋友文雅",
        "忌": "交友自化忌，朋友关系纠结",
    },
    "仆役": {
        "禄": "仆役自化禄，下属缘分好",
        "权": "仆役自化权，下属中有强势者",
        "科": "仆役自化科，下属文雅",
        "忌": "仆役自化忌，下属关系纠结",
    },
    "父母": {
        "禄": "父母自化禄，与长辈关系不错",
        "权": "父母自化权，长辈有主导权",
        "科": "父母自化科，和父母关系表面和睦内心有距离，长辈遇事倾向理性解决但很难提供强大物质助力，祖业薄弱",
        "忌": "父母自化忌，与长辈关系纠结",
    },
}

# ============================================================================
# 领域 → 关联宫位映射
#
# Z80-修复：宫名兼容。iztro 排盘产出「仆役」，而部分流派/数据集写「交友」。
# PALACE_DIM_MAP 已做双键兼容，但本表此前只写「交友」，导致 _build_domain_readings
# 的 `[p for p in palace_names if p in pr_map]` 静默丢弃该宫——学业/人际两领域
# 各少一宫。此处统一收敛为盘内实际宫名「仆役」，并在 _build_domain_readings
# 中增加别名回退（见 PALACE_ALIAS）。
# ============================================================================

# 宫名别名 → 盘内规范名（iztro 以「仆役」为准）
PALACE_ALIAS: Dict[str, str] = {
    "交友": "仆役",
    "仆役": "仆役",
}

DOMAIN_PALACES: Dict[str, List[str]] = {
    "健康": ["疾厄", "命宫", "福德"],
    "学业": ["仆役", "命宫", "官禄"],      # 仆役(交友)宫=才艺学业维度
    "事业": ["官禄", "命宫", "迁移"],
    "财运": ["财帛", "田宅", "福德"],
    "人际": ["兄弟", "仆役", "命宫"],
    "婚恋": ["夫妻", "官禄", "命宫"],      # 官禄=夫妻的对宫
    # Z80-修复：补足「子女」「父母」两宫归属。
    # 此前两宫仅存在于十二宫逐宫解读（palace_readings），未纳入任何领域聚合，
    # 导致领域层（domain_readings）无法覆盖子女/父母两条人生线。
    "子女": ["子女", "田宅", "命宫"],      # 田宅=子女对宫，家宅环境影响子女
    "父母": ["父母", "疾厄", "命宫"],      # 疾厄=父母对宫，遗传与长辈健康互涉
}

# 领域关键词映射（用于从断语中提取领域相关概念）
DOMAIN_CONCEPTS: Dict[str, List[str]] = {
    "健康": ["内分泌", "妇科", "睡眠", "肾脏", "情绪", "焦虑", "干眼症", "体虚",
             "湿气", "失眠", "慢性病", "手术", "体质", "神经", "消化", "呼吸",
             "泌尿", "生殖", "心血管", "眼睛", "肝", "肺", "脾", "胃"],
    "学业": ["学习", "悟性", "学业", "进修", "考证", "技能", "文昌", "文曲",
             "聪明", "悟性", "才华", "专业", "研究", "学术"],
    "事业": ["事业", "工作", "创业", "管理", "技术", "策划", "运营", "项目",
             "转型", "跳槽", "岗位", "行业", "职业", "开拓", "变革"],
    "财运": ["财", "理财", "投资", "储蓄", "消费", "破财", "守财", "收入",
             "开支", "投机", "副业", "正财", "偏财", "贷款", "借贷"],
    "人际": ["朋友", "人脉", "社交", "知己", "小人", "贵人", "借钱", "合伙",
             "边界", "人情", "交游", "关系"],
    "婚恋": ["配偶", "婚姻", "感情", "伴侣", "相处", "矛盾", "冷战", "包容",
             "沟通", "争吵", "离婚", "恋爱", "桃花"],
    # Z80-修复：子女/父母两宫纳入领域聚合后补齐关键词
    "子女": ["子女", "子息", "晚辈", "教育", "管教", "沟通", "主见", "生育",
             "后代", "亲子", "包容", "代沟"],
    "父母": ["父母", "长辈", "父亲", "母亲", "遗传", "长辈缘", "孝养", "提携",
             "代际", "家庭背景", "血脉"],
}

# ============================================================================
# 对宫冲击解读
# ============================================================================

OPPOSITE_IMPACT: Dict[str, str] = {
    "命宫": "迁移宫影响命宫，外出发展对人生格局有直接冲击",
    "夫妻": "对宫官禄破军，事业巨大波动会直接冲击婚姻稳定",
    "官禄": "对宫夫妻宫，感情状态直接影响事业发展",
    "财帛": "对宫福德，精神状态直接影响理财判断",
    "疾厄": "对宫父母，遗传因素和长辈健康影响自身",
    "迁移": "受财帛贪狼忌冲照，在外容易花销暴增，人际是非诱惑",
    "福德": "对宫财帛，财务状况直接影响精神状态",
    "田宅": "对宫子女，子女状况影响家运",
    "子女": "对宫田宅，家宅环境影响子女",
    "兄弟": "对宫仆役，下属和朋友关系互为影响",
    "交友": "借对宫财帛贪狼之气，朋友多为利益人脉往来，泛交居多知己稀少",
    "父母": "对宫疾厄，自身健康状态影响与长辈关系",
}

# ============================================================================
# 亮度增强语义
# ============================================================================

BRIGHTNESS_ENHANCE: Dict[str, str] = {
    "庙": "入庙力量最强，该星特质充分发挥",
    "旺": "旺相力量强，该星特质明显",
    "得": "得地力量中上，该星特质较好发挥",
    "利": "利位力量中等，该星特质正常发挥",
    "平": "平位力量中等偏弱，该星特质一般",
    "弱": "落弱力量不足，该星特质受阻",
    "陷": "落陷力量最弱，该星负面特质容易显现",
}


# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class PalaceReading:
    """单宫综合解读。"""
    palace: str              # 宫位名
    dimension: str           # 对应维度名
    stars: List[str]         # 宫内所有星
    major_interpretation: str  # 主星解读
    minor_interpretation: str  # 辅星解读
    sihua_interpretation: str  # 四化解读
    zihua_interpretation: str  # 自化解读
    opposite_interpretation: str  # 对宫影响
    conclusion: str          # 综合断语段落
    key_concepts: List[str] = field(default_factory=list)  # 关键概念标签


@dataclass
class DomainReading:
    """单领域综合解读。"""
    domain: str              # 领域名（健康/学业/事业/财运/人际/婚恋）
    related_palaces: List[str]  # 关联宫位
    conclusion: str          # 综合断语段落
    risk_points: List[str] = field(default_factory=list)  # 风险点
    suggestions: List[str] = field(default_factory=list)   # 建议
    key_concepts: List[str] = field(default_factory=list)  # 关键概念标签


@dataclass
class DomainReadingOutput:
    """维度断语层输出。"""
    palace_readings: List[PalaceReading] = field(default_factory=list)
    domain_readings: List[DomainReading] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "palace_readings": [
                {
                    "palace": pr.palace,
                    "dimension": pr.dimension,
                    "stars": pr.stars,
                    "conclusion": pr.conclusion,
                    "key_concepts": pr.key_concepts,
                }
                for pr in self.palace_readings
            ],
            "domain_readings": [
                {
                    "domain": dr.domain,
                    "related_palaces": dr.related_palaces,
                    "conclusion": dr.conclusion,
                    "risk_points": dr.risk_points,
                    "suggestions": dr.suggestions,
                    "key_concepts": dr.key_concepts,
                }
                for dr in self.domain_readings
            ],
        }


# ============================================================================
# 主函数
# ============================================================================

def build_domain_readings(
    chart: Any,
    zihua_map: Optional[Dict[str, list]] = None,
) -> DomainReadingOutput:
    """构建十二宫逐宫 + 领域综合解读。

    Args:
        chart: FrozenZiweiChart (ZiweiChart)
        zihua_map: {宫位名: [自化列表]}，从 get_all_zihua 获取

    Returns:
        DomainReadingOutput
    """
    palaces = chart.palaces if hasattr(chart, 'palaces') else getattr(chart, 'palace_data', {})
    if zihua_map is None:
        zihua_map = {}

    # 十二宫解读
    palace_readings = []
    for pname, pdata in palaces.items():
        pr = _build_palace_reading(pname, pdata, palaces, zihua_map)
        palace_readings.append(pr)

    # 领域聚合
    domain_readings = _build_domain_readings(palace_readings)

    return DomainReadingOutput(
        palace_readings=palace_readings,
        domain_readings=domain_readings,
    )


# ============================================================================
# 内部实现
# ============================================================================

PALACE_DIM_MAP = {
    "命宫": "性情禀赋", "兄弟": "交游人际", "夫妻": "婚姻配偶",
    "子女": "子女", "财帛": "财帛", "疾厄": "身体疾厄",
    "迁移": "迁移出行", "官禄": "事业功名", "田宅": "田宅家业",
    "福德": "福德精神", "父母": "父母长辈",
    "交友": "才艺学业", "仆役": "才艺学业",
}

OPPOSITE_PALACE = {
    "命宫": "迁移", "迁移": "命宫",
    "兄弟": "仆役", "仆役": "兄弟",
    "夫妻": "官禄", "官禄": "夫妻",
    "子女": "田宅", "田宅": "子女",
    "财帛": "福德", "福德": "财帛",
    "疾厄": "父母", "父母": "疾厄",
}


def _build_palace_reading(
    pname: str,
    pdata: dict,
    all_palaces: dict,
    zihua_map: dict,
) -> PalaceReading:
    """构建单宫综合解读。"""
    dimension = PALACE_DIM_MAP.get(pname, pname)
    major = pdata.get("major", [])
    minor = pdata.get("minor", [])
    adjective = pdata.get("adjective", [])
    branch = str(pdata.get("branch", "")).strip("'\"")
    star_detail = pdata.get("starDetail", [])

    # ── 1. 主星解读 ──
    major_parts = []
    for star in major:
        bright = ""
        for sd in star_detail:
            if sd.get("name") == star and sd.get("kind") == "major":
                bright = sd.get("brightness", "")
                break
        if bright:
            major_parts.append(f"{star}{bright}")
        else:
            major_parts.append(star)
    major_text = "、".join(major_parts) + "守宫" if major_parts else "无主星"

    # ── 2. 辅星解读 ──
    minor_parts = []
    # 合并 minor + adjective 中的煞曜
    all_minor = list(minor) + [a for a in adjective if a in MINOR_STAR_BY_PALACE.get(pname, {})]
    palace_minor_table = MINOR_STAR_BY_PALACE.get(pname, {})
    # 如果该宫位没有专门的辅星表，尝试仆役表（兼容）
    if not palace_minor_table and pname == "仆役":
        palace_minor_table = MINOR_STAR_BY_PALACE.get("交友", {})
    for star in all_minor:
        interp = palace_minor_table.get(star, "")
        if interp:
            minor_parts.append(interp)
    minor_text = "；".join(minor_parts) if minor_parts else ""

    # ── 3. 四化解读 ──
    sihua_parts = []
    for sd in star_detail:
        mg = sd.get("mutagen", "")
        if mg:
            sihua_parts.append(f"{sd['name']}生年{mg}入{pname}")
    sihua_text = "，".join(sihua_parts) if sihua_parts else ""

    # ── 4. 自化解读 ──
    zihua_list = zihua_map.get(pname, [])
    zihua_parts = []
    palace_zihua_table = ZIHUA_BY_PALACE.get(pname, {})
    if not palace_zihua_table and pname == "仆役":
        palace_zihua_table = ZIHUA_BY_PALACE.get("交友", {})
    for zh in zihua_list:
        # zh 格式如 "文昌自化科" / "天梁自化权"
        zh_type = ""
        for t in ["禄", "权", "科", "忌"]:
            if t in zh:
                zh_type = t
                break
        if zh_type:
            interp = palace_zihua_table.get(zh_type, "")
            if interp:
                zihua_parts.append(interp)
    zihua_text = "；".join(zihua_parts) if zihua_parts else ""

    # ── 5. 对宫影响 ──
    opposite = OPPOSITE_PALACE.get(pname, "")
    opposite_text = ""
    if opposite:
        # 优先用预定义的冲击解读
        impact = OPPOSITE_IMPACT.get(pname, "")
        if impact:
            opposite_text = impact
        else:
            # 检查对宫是否有主星（空宫借对宫）
            opp_data = all_palaces.get(opposite, {})
            opp_major = opp_data.get("major", [])
            if not major and opp_major:
                opposite_text = f"{pname}无主星，借对宫{opposite}（{'、'.join(opp_major)}）论断"

    # ── 6. 综合段落 ──
    parts = []
    if major_parts:
        parts.append(f"{pname}{'、'.join(major_parts)}坐守")
        # 加亮度描述
        bright_desc = []
        for star in major:
            for sd in star_detail:
                if sd.get("name") == star and sd.get("kind") == "major":
                    b = sd.get("brightness", "")
                    if b:
                        bright_desc.append(f"{star}{b}")
        if bright_desc:
            parts.append(f"（{', '.join(bright_desc)}）")

    if minor_parts:
        parts.append(minor_text)
    if sihua_text:
        parts.append(sihua_text)
    if zihua_text:
        parts.append(zihua_text)
    if opposite_text:
        parts.append(opposite_text)

    conclusion = "，".join(parts) + "。" if parts else f"{pname}暂无主星，借对宫论断。"

    # ── 7. 关键概念提取 ──
    concepts = []
    full_text = " ".join([major_text, minor_text, sihua_text, zihua_text, opposite_text])
    for dim_name, keywords in DOMAIN_CONCEPTS.items():
        for kw in keywords:
            if kw in full_text and kw not in concepts:
                concepts.append(kw)

    return PalaceReading(
        palace=pname,
        dimension=dimension,
        stars=major + all_minor,
        major_interpretation=major_text,
        minor_interpretation=minor_text,
        sihua_interpretation=sihua_text,
        zihua_interpretation=zihua_text,
        opposite_interpretation=opposite_text,
        conclusion=conclusion,
        key_concepts=concepts,
    )


def _build_domain_readings(
    palace_readings: List[PalaceReading],
) -> List[DomainReading]:
    """领域聚合。"""
    # 建立宫位 → 解读映射
    pr_map = {}
    for pr in palace_readings:
        pr_map[pr.palace] = pr

    domain_readings = []
    for domain, palace_names in DOMAIN_PALACES.items():
        # Z80-修复：宫名别名回退。声明名在盘内不存在时，尝试其别名，
        # 避免「交友/仆役」类差异导致整宫静默丢失。
        resolved = []
        for p in palace_names:
            if p in pr_map:
                resolved.append(p)
                continue
            alias = PALACE_ALIAS.get(p)
            if alias and alias in pr_map:
                resolved.append(alias)
        related = resolved
        conclusions = []
        all_concepts = []
        risk_points = []
        suggestions = []

        for pn in related:
            pr = pr_map[pn]
            conclusions.append(f"【{pn}】{pr.conclusion}")
            for c in pr.key_concepts:
                if c not in all_concepts:
                    all_concepts.append(c)

        # 领域综合结论
        domain_conclusion = _synthesize_domain(domain, related, pr_map)

        # 风险点和建议
        risk_points, suggestions = _extract_risk_and_advice(domain, related, pr_map)

        domain_readings.append(DomainReading(
            domain=domain,
            related_palaces=related,
            conclusion=domain_conclusion,
            risk_points=risk_points,
            suggestions=suggestions,
            key_concepts=all_concepts,
        ))

    return domain_readings


def _synthesize_domain(
    domain: str,
    palaces: List[str],
    pr_map: Dict[str, PalaceReading],
) -> str:
    """合成领域综合结论。"""
    parts = []

    if domain == "健康":
        parts.append(_health_synthesis(palaces, pr_map))
    elif domain == "学业":
        parts.append(_study_synthesis(palaces, pr_map))
    elif domain == "事业":
        parts.append(_career_synthesis(palaces, pr_map))
    elif domain == "财运":
        parts.append(_wealth_synthesis(palaces, pr_map))
    elif domain == "人际":
        parts.append(_social_synthesis(palaces, pr_map))
    elif domain == "婚恋":
        parts.append(_marriage_synthesis(palaces, pr_map))
    elif domain == "子女":
        parts.append(_children_synthesis(palaces, pr_map))
    elif domain == "父母":
        parts.append(_parent_synthesis(palaces, pr_map))

    return "".join(parts)


def _health_synthesis(palaces: List[str], pr_map: dict) -> str:
    """健康领域综合。"""
    parts = []
    jie = pr_map.get("疾厄")
    if jie:
        major = jie.major_interpretation
        parts.append(f"疾厄宫{major}")
        # 辅星中的健康信号
        if jie.minor_interpretation:
            parts.append(jie.minor_interpretation)
        if jie.zihua_interpretation:
            parts.append(jie.zihua_interpretation)
    ming = pr_map.get("命宫")
    if ming and ming.minor_interpretation:
        # 提取命宫中与健康相关的辅星（铃星→焦虑躯体化）
        for star in ming.stars:
            if star in ("铃星", "火星", "陀罗", "擎羊"):
                interp = MINOR_STAR_BY_PALACE.get("命宫", {}).get(star, "")
                if interp:
                    parts.append(interp)
    fu = pr_map.get("福德")
    if fu and fu.minor_interpretation:
        parts.append(f"福德宫{fu.minor_interpretation}")
    return "；".join(parts) + "。" if parts else "健康方面无明显信号。"


def _study_synthesis(palaces: List[str], pr_map: dict) -> str:
    """学业领域综合。"""
    parts = []
    jiao = pr_map.get("交友") or pr_map.get("仆役")
    if jiao:
        parts.append(f"才艺学业宫（{jiao.palace}）{jiao.major_interpretation}")
        if jiao.minor_interpretation:
            parts.append(jiao.minor_interpretation)
    ming = pr_map.get("命宫")
    if ming:
        # 文昌文曲入命 → 学业信号
        for star in ming.stars:
            if star in ("文昌", "文曲"):
                parts.append(f"命宫{star}入命，聪慧善文，学习悟性优秀，擅长文字策划艺术")
    guan = pr_map.get("官禄")
    if guan:
        parts.append(f"官禄宫{guan.major_interpretation}，学业与事业相辅相成")
    return "；".join(parts) + "。" if parts else "学业方面需结合具体星曜分析。"


def _career_synthesis(palaces: List[str], pr_map: dict) -> str:
    """事业领域综合。"""
    parts = []
    guan = pr_map.get("官禄")
    if guan:
        parts.append(f"官禄宫{guan.major_interpretation}")
        if guan.sihua_interpretation:
            parts.append(guan.sihua_interpretation)
        if guan.minor_interpretation:
            parts.append(guan.minor_interpretation)
        if guan.zihua_interpretation:
            parts.append(guan.zihua_interpretation)
    ming = pr_map.get("命宫")
    if ming:
        # 七杀/破军/贪狼 → 杀破狼格局
        major_names = [s for s in ming.stars if s in ("七杀", "破军", "贪狼")]
        if len(major_names) >= 1:
            guan_major = [s for s in (pr_map.get("官禄").stars if pr_map.get("官禄") else []) if s in ("七杀", "破军", "贪狼")]
            cai_major = [s for s in (pr_map.get("财帛").stars if pr_map.get("财帛") else []) if s in ("七杀", "破军", "贪狼")]
            if guan_major or cai_major:
                parts.append("命宫三方四正构成杀破狼格局，天生适合变动创新赛道")
        # 辅星中的事业信号
        for star in ming.stars:
            if star in ("文昌", "文曲", "左辅", "右弼"):
                parts.append(f"命宫{star}，适合持续深耕专业")
    qianyi = pr_map.get("迁移")
    if qianyi and qianyi.major_interpretation:
        parts.append(f"迁移宫{qianyi.major_interpretation}，适合异地发展")
    return "；".join(parts) + "。" if parts else "事业方面需结合具体星曜分析。"


def _wealth_synthesis(palaces: List[str], pr_map: dict) -> str:
    """财运领域综合。"""
    parts = []
    cai = pr_map.get("财帛")
    if cai:
        parts.append(f"财帛宫{cai.major_interpretation}")
        if cai.sihua_interpretation:
            parts.append(cai.sihua_interpretation)
        if cai.minor_interpretation:
            parts.append(cai.minor_interpretation)
        if cai.zihua_interpretation:
            parts.append(cai.zihua_interpretation)
    tian = pr_map.get("田宅")
    if tian:
        parts.append(f"田宅宫{tian.major_interpretation}")
        if tian.minor_interpretation:
            parts.append(tian.minor_interpretation)
    fu = pr_map.get("福德")
    if fu:
        parts.append(f"福德宫{fu.major_interpretation}，影响理财心态")
    return "；".join(parts) + "。" if parts else "财运方面需结合具体星曜分析。"


def _social_synthesis(palaces: List[str], pr_map: dict) -> str:
    """人际领域综合。"""
    parts = []
    xiong = pr_map.get("兄弟")
    if xiong:
        parts.append(f"兄弟宫{xiong.major_interpretation}")
        if xiong.minor_interpretation:
            parts.append(xiong.minor_interpretation)
        if xiong.zihua_interpretation:
            parts.append(xiong.zihua_interpretation)
    jiao = pr_map.get("交友") or pr_map.get("仆役")
    if jiao:
        parts.append(f"交友宫{jiao.major_interpretation}")
        if jiao.minor_interpretation:
            parts.append(jiao.minor_interpretation)
        if jiao.zihua_interpretation:
            parts.append(jiao.zihua_interpretation)
    ming = pr_map.get("命宫")
    if ming:
        for star in ming.stars:
            if star == "七杀":
                parts.append("命宫七杀，内心防备较重，朋友大多是利益型人脉，真心知己不多")
    return "；".join(parts) + "。" if parts else "人际方面需结合具体星曜分析。"


def _marriage_synthesis(palaces: List[str], pr_map: dict) -> str:
    """婚恋领域综合。"""
    parts = []
    fu = pr_map.get("夫妻")
    if fu:
        parts.append(f"夫妻宫{fu.major_interpretation}")
        if fu.sihua_interpretation:
            parts.append(fu.sihua_interpretation)
        if fu.minor_interpretation:
            parts.append(fu.minor_interpretation)
        if fu.zihua_interpretation:
            parts.append(fu.zihua_interpretation)
    # 对宫（官禄）对夫妻的冲击
    guan = pr_map.get("官禄")
    if guan:
        for star in guan.stars:
            if star == "破军":
                parts.append("对宫官禄破军持续变动，事业动荡阶段极易传导至婚姻，引发矛盾")
    # 命宫性格对婚姻的影响
    ming = pr_map.get("命宫")
    if ming:
        for star in ming.stars:
            if star == "七杀":
                parts.append("命宫七杀个性刚强，相处容易互不相让，缺少情绪包容")
    return "；".join(parts) + "。" if parts else "婚恋方面需结合具体星曜分析。"


def _children_synthesis(palaces: List[str], pr_map: dict) -> str:
    """子女领域综合（Z80 补：子女宫此前未纳入任何领域聚合）。"""
    parts = []
    zi = pr_map.get("子女")
    if zi:
        parts.append(f"子女宫{zi.major_interpretation}")
        if zi.sihua_interpretation:
            parts.append(zi.sihua_interpretation)
        if zi.minor_interpretation:
            parts.append(zi.minor_interpretation)
        if zi.zihua_interpretation:
            parts.append(zi.zihua_interpretation)
    # 对宫（田宅）对子女的牵连
    tian = pr_map.get("田宅")
    if tian and tian.major_interpretation:
        parts.append(f"对宫田宅{tian.major_interpretation}，家宅环境影响子女成长")
    # 命宫性格对子女教养的影响
    ming = pr_map.get("命宫")
    if ming:
        for star in ming.stars:
            if star in ("七杀", "破军", "贪狼"):
                parts.append(f"命宫{star}个性强势，教养子女宜宽严并济")
    return "；".join(parts) + "。" if parts else "子女方面需结合具体星曜分析。"


def _parent_synthesis(palaces: List[str], pr_map: dict) -> str:
    """父母领域综合（Z80 补：父母宫此前未纳入任何领域聚合）。"""
    parts = []
    fu = pr_map.get("父母")
    if fu:
        parts.append(f"父母宫{fu.major_interpretation}")
        if fu.sihua_interpretation:
            parts.append(fu.sihua_interpretation)
        if fu.minor_interpretation:
            parts.append(fu.minor_interpretation)
        if fu.zihua_interpretation:
            parts.append(fu.zihua_interpretation)
    # 对宫（疾厄）与长辈健康的互涉
    ji = pr_map.get("疾厄")
    if ji and ji.major_interpretation:
        parts.append(f"对宫疾厄{ji.major_interpretation}，自身健康与长辈状况互涉")
    # 命宫对与长辈相处的投射
    ming = pr_map.get("命宫")
    if ming:
        for star in ming.stars:
            if star in ("七杀", "破军", "擎羊", "火星"):
                parts.append(f"命宫{star}个性刚直，与长辈相处宜多耐心沟通")
    return "；".join(parts) + "。" if parts else "父母方面需结合具体星曜分析。"


def _extract_risk_and_advice(
    domain: str,
    palaces: List[str],
    pr_map: dict,
) -> tuple:
    """提取风险点和建议。"""
    risks = []
    advice = []

    for pn in palaces:
        pr = pr_map.get(pn)
        if not pr:
            continue
        full_text = " ".join([
            pr.major_interpretation, pr.minor_interpretation,
            pr.sihua_interpretation, pr.zihua_interpretation,
            pr.opposite_interpretation,
        ])

        # 煞星信号 → 风险点
        for star in pr.stars:
            if star in ("擎羊", "陀罗", "火星", "铃星", "地空", "地劫"):
                if star == "陀罗" and domain == "健康":
                    risks.append("陀罗代表反反复复，慢性病反复缠绵")
                    advice.append("定期体检，长期调理")
                elif star == "铃星" and domain == "健康":
                    risks.append("铃星持续带来隐性焦虑，压力积压容易躯体化")
                    advice.append("固定作息，情绪宣泄，减少熬夜")
                elif star == "贪狼" and "忌" in full_text and domain == "财运":
                    risks.append("贪狼忌代表欲望无底洞，冲动消费、投机投资持续破财")
                    advice.append("强制储蓄，远离股票虚拟币，不与人合伙投资")

        # 忌化信号
        if "忌" in pr.sihua_interpretation or "忌" in pr.zihua_interpretation:
            if domain == "财运" and pn == "财帛":
                risks.append("财帛宫忌化，守财难度高")
            elif domain == "健康" and pn == "疾厄":
                risks.append("疾厄宫忌化，健康方面需格外注意")

    # 去重
    risks = list(dict.fromkeys(risks))
    advice = list(dict.fromkeys(advice))

    return risks, advice
