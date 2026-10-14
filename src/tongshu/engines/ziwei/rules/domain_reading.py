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
    "夫妻": "对宫官禄，事业状态与波动会直接传导至婚姻",
    "官禄": "对宫夫妻，感情状态直接影响事业发展",
    "财帛": "对宫福德，精神状态直接影响理财判断",
    "疾厄": "对宫父母，遗传因素和长辈健康影响自身",
    "福德": "对宫财帛，财务状况直接影响精神状态",
    "田宅": "对宫子女，子女状况影响家运",
    "子女": "对宫田宅，家宅环境影响子女",
    "兄弟": "对宫仆役，下属和朋友关系互为影响",
    "迁移": "迁移受命宫气质投射，自身格局决定外出际遇，外出发展对人生格局有直接冲击",
    "仆役": "对宫兄弟，朋友下属与手足同辈关系互为影响",
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
    "不": "不得地力量偏弱，该星特质容易走样",
    "弱": "落弱力量不足，该星特质受阻",
    "陷": "落陷力量最弱，该星负面特质容易显现",
}

# ============================================================================
# Z80-B：主星组合语义（同宫双星 → 连贯论断）。
# 键为"宫名|星1+星2"（星名按字面排序拼接），值为组合论断。
# 依据：紫微斗数同宫组合的星性叠加是常规象义，非单星相加。
# ============================================================================

STAR_PAIR_VERDICTS: Dict[str, str] = {
    "夫妻|天相+武曲": "武曲天相为印星组合，配偶稳重务实、有责任心，具备承担家庭责任的能力，做事稳重，重视个人名声，婚姻不会轻易决裂；但武曲刚硬，二人遇到矛盾容易冷战讲道理，缺少情绪共情，容易为金钱与工作事务争吵；不要试图改造伴侣，出现矛盾避免冷战，重大事业变动前提前沟通",
    "疾厄|太阴+天同": "太阴属阴水，对应妇科、内分泌、肾脏、泌尿系统、眼睛、睡眠，情绪焦虑与神经衰弱需留意",
    "福德|紫微+天府": "紫微守福德，内心自尊心极强，精神追求高，很难长期屈居人下",
    "福德|紫微": "紫微独处容易精神孤独，心事难与人言，高标准常常自我内耗，很难真正放松",
    "兄弟|天梁+太阳": "手足与同辈个性要强、喜欢发表意见，朋友中贵人小人并存，不宜和朋友大额合伙经商，容易起权力纠纷与利益矛盾",
    "官禄|廉贞+天府": "廉贞天府外出机遇多，适合异地工作、出差、外地发展，能拓展眼界",
    "迁移|廉贞+天府": "廉贞天府坐迁移，外出机遇多，适合异地工作、出差、外地发展，能拓展眼界",
    "子女|巨门+天机": "子女主见极强、思维活跃、口才出众，不喜欢被管控",
}

# ============================================================================
# Z80-B：命宫独座星的个人底色（坐命主星 → 性格与应对方式）
# ============================================================================

STAR_SOLO_VERDICTS: Dict[str, str] = {
    "七杀": "独立要强，不喜受人支配，遇到困难习惯独自承担，有魄力，适合开拓、管理、技术赛道；学习易有三分钟热度，缺乏耐心容易半途而废，感兴趣深耕就能出成绩，建议持续进修、考证、技能提升，中年进修能有效提升事业层次",
    "破军": "敢于破旧立新，一生起伏变化大，适合创新赛道但不宜守成",
    "贪狼": "多才多艺、欲望强、善于交际，需节制欲望防沉迷",
    "紫微": "自尊心强，有领袖气质，需防孤高自赏",
    "武曲": "刚毅务实，理财能力强，但缺少浪漫，宜修柔和之德",
    "天相": "辅佐之才，做事周到重信誉，但位高无权，需防缺乏主见",
    "巨门": "口才与钻研能力强，但易招口舌是非，宜谨言慎行",
    "太阳": "光明博爱，付出多，需防心力交瘁",
    "太阴": "细腻内敛，重情绪与家庭，需防敏感多虑",
    "天同": "温和享乐，不喜竞争，需防懒散依赖",
    "天梁": "长者之风，乐于助人逢凶化吉，需防孤克",
    "天机": "机敏善谋，学习悟性高，需防思虑过多、缺乏耐心",
    "天府": "稳重守成，善理财库，需防保守迟疑",
    "廉贞": "精明干练富艺术气质，需防情绪用事与桃花纠纷",
}

# ============================================================================
# Z80-B：星曜 → 身体系统映射（疾厄宫专用）
# ============================================================================

STAR_BODY_ORGANS: Dict[str, str] = {
    "太阴": "太阴属阴水，对应妇科、内分泌、肾脏、泌尿系统、眼睛、睡眠，主情绪焦虑与神经衰弱，容易长期失眠、情绪性体虚、干眼症、湿气重、妇科周期性不适",
    "太阳": "太阳主心血管、眼睛、血压，落陷易体虚易疲劳",
    "武曲": "武曲属金，对应肺部与呼吸系统，需防皮肤与外伤",
    "天同": "天同属水，对应泌尿与肾脏系统，需注意湿气重与情绪性体虚",
    "廉贞": "廉贞属火，对应心血管与炎症，需防情绪影响健康",
    "天机": "天机主神经系统与肝胆，需防失眠焦虑",
    "巨门": "巨门主呼吸系统与咽喉，需注意口腔与消化道",
    "贪狼": "贪狼主肝肾与生殖系统，需节制欲望",
    "天相": "天相主皮肤与泌尿系统，需防内分泌失调",
    "天梁": "天梁主骨骼、脊椎与脾胃，注意慢性疾病",
    "七杀": "七杀主肺部与外伤，需防意外与手术",
    "破军": "破军主肾水与泌尿系统，身体易有突发变化",
    "紫微": "紫微主脾胃与消化系统，需防压力大导致体虚",
    "天府": "天府主脾胃与消化系统，体质稳定但需防湿气",
}

# 煞星 → 病程特征
SHA_DISEASE_TRAIT: Dict[str, str] = {
    "陀罗": "陀罗代表慢性病反复缠绵，湿气重，压力一大立刻躯体不适",
    "擎羊": "擎羊主外伤手术之厄，急性炎症",
    "火星": "火星主突发高热与急性炎症",
    "铃星": "铃星主隐性焦虑与情绪性体虚，长期失眠",
    "地空": "地空主精神消耗与体质虚弱",
    "地劫": "地劫主健康突变与意外耗损",
}

# ============================================================================
# Z80-B：格局/星曜 → 适配行业与职业赛道
# ============================================================================

CAREER_FIT: Dict[str, str] = {
    "杀破狼": "杀破狼格局适合变动与创新赛道：项目管理、技术研发、策划咨询、运营、文创、医美、教育培训，也适合自主轻创业；事业节奏早年摸索起伏多，中年大限逐步稳定，机遇都伴随转型而来；长期困守僵化岗位、压抑个性、规则僵化是大忌，切忌盲目裸辞",
    "七杀": "七杀坐命适合开拓型赛道：项目管理、技术研发、运营管理，需大破大立，不适合一辈子一成不变",
    "破军": "破军坐官禄主大破大立格局，事业经常伴随岗位调整与公司变动，每一次良性转型都能带来收入提升，但不宜频繁无规划跳槽",
    "武曲": "武曲适合金融、工程、财务、技术等以专业与执行立身的领域",
    "巨门": "巨门适合律师、讲师、外语、谈判等以口为业的领域",
    "天机": "天机适合策划、咨询、技术、研究类工作",
    "太阳": "太阳适合公益、教育、媒体、传播等发挥影响力的行业",
    "太阴": "太阴适合设计、财务、内务、文化艺术类工作",
    "贪狼": "贪狼适合销售、公关、娱乐、文创等需要人缘的领域",
    "廉贞": "廉贞适合创意、演艺、公关、法律类工作",
    "天相": "天相适合执行、管理、协调类岗位，位高但需借势",
    "天梁": "天梁适合医疗、审计、监督、教育等需要原则性的职业",
    "紫微": "紫微适合管理、领导、自主创业，需防志大才疏",
    "天府": "天府适合大企业稳定发展、仓储财务类守成岗位",
    "天同": "天同适合福利、文化、服务业，宜稳定不宜冒险创业",
}

# ============================================================================
# Z80-B：来因宫语义（北派：来因宫为一生因果所系）
# ============================================================================

LAIYIN_SEMANTICS: Dict[str, str] = {
    "疾厄": "来因疾厄，来因宫落疾厄，身心绑定是此命底色，压力无法释放就会转化为慢性病，情绪直接等于健康开关",
    "命宫": "来因宫在命宫，一生际遇多由自身性格与选择引发，自我主导意识强",
    "官禄": "来因宫在官禄，人生因果多系于事业成就与职业变动",
    "财帛": "来因宫在财帛，一生因果与金钱往来、理财方式紧密相连",
    "夫妻": "来因宫在夫妻，人生起伏与感情婚姻最为相关",
    "福德": "来因宫在福德，精神世界与福报是此命的关键课题",
    "田宅": "来因宫在田宅，家宅与产业是此生因果所在",
    "子女": "来因宫在子女，与子女、晚辈、合伙事业的牵连最深",
    "迁移": "来因宫在迁移，外出与异地发展是此生因果的触发点",
    "仆役": "来因宫在仆役，朋友人脉与下属关系是因果主战场",
    "兄弟": "来因宫在兄弟，手足同辈与人脉往来是此生关键课题",
    "父母": "来因宫在父母，与长辈、上司、文书缘分的牵连最深",
}

# ============================================================================
# Z80-B：宫位补强语义（特定星曜组合在特定宫的论断）
# ============================================================================

PALACE_EXTRA_SEMANTICS: Dict[str, str] = {
    # 命宫辅星的心理底色
    "命宫|铃星": "铃星持续带来隐性焦虑，压力积压不会主动倾诉，长期容易躯体化",
    "命宫|文昌": "文昌坐命，学习悟性优秀，擅长文字、策划与艺术，遇事懂得寻找方法提升自己",
    "命宫|陀罗": "陀罗坐命，做事反复拖延，遇事宜三思不宜钻牛角尖",
    # 财帛
    "财帛|禄存+贪狼": "禄忌共处，财格矛盾明显：既有正财机会，又因贪狼忌形成欲望无底洞，容易赚得多开销更大，守财难度高",
    "财帛|贪狼": "贪狼在财帛，欲望无底洞，容易因人情往来、人情借贷、盲目副业、娱乐消费、投机投资持续破财，切忌跟风投资，远离股票虚拟币加盟，不与人合伙投资",
    "财帛|咸池": "咸池同宫，需防范因桃花与异性关系破财",
    # 官禄
    "官禄|破军": "官禄破军属大破大立格局，不适合一辈子一成不变，适合项目管理、技术革新、策划、运营、自主创业、跨行业转型",
    "官禄|无吉": "官禄无吉星辅佐，凡事需亲力亲为，成功全靠自身打拼",
    # 福德
    "福德|紫微": "紫微守福德，内心自尊心极强，精神追求高，很难长期屈居人下；有福报，绝境之中常有转机；但紫微独处容易精神孤独，心事难与人言，高标准常常自我内耗，很难真正放松",
    # 田宅
    "田宅|无主星": "田宅无主星，房产运有机会购置不动产但过程一波三折；家中氛围容易冷清，家人各自独立；不宜盲目炒房或多处购置房产增加负担",
    # 子女
    "子女|巨门": "子女主见极强、思维活跃、口才出众，不喜欢被管控；亲子之间容易口舌争执，两代人观念差距大，教育切忌强硬压制，适合平等沟通",
    "子女|巨门+擎羊": "巨门加擎羊，沟通方式容易尖锐，亲子之间容易口舌争执，两代人观念差距大；教育管教切忌强硬压制，适合平等沟通",
    # 父母
    "父母|地空地劫": "空劫同宫，容易和长辈聚少离多",
    "父母|天马": "天马代表长辈经常奔波，或者命主长期离家",
    "父母|天机": "天机在父母宫，长辈遇事倾向理性解决，但很难提供强大物质助力，祖业薄弱",
    # 仆役
    "仆役|无主星": "仆役宫无主星，朋友多为利益人脉往来，泛交居多、知己稀少",
    "仆役|贪狼": "贪狼在仆役宫，容易被朋友拖累、人情破财，需谨慎借钱给他人，不宜涉入人情借贷",
    # 疾厄（星→器官映射另由 STAR_BODY_ORGANS 事实驱动，此处仅病程特征）
    # 迁移
    "迁移|文曲": "文曲在迁移，外出注意文书合同出错",
}

# Z80-C：借宫语义模板（按对宫实际主星填充，不写死案例盘）
BORROWED_SEMANTICS: Dict[str, str] = {
    "财帛": "借对宫财帛{stars}之气，主求财与资源往来牵动此宫事项",
    "福德": "借对宫福德{stars}之气，主精神福泽牵动此宫事项",
    "官禄": "借对宫官禄{stars}之气，主事业变动牵动此宫事项",
    "夫妻": "借对宫夫妻{stars}之气，主感情缘分牵动此宫事项",
    "迁移": "借对宫迁移{stars}之气，主外出际遇牵动此宫事项",
    "命宫": "借对宫命宫{stars}之气，主自身格局牵动此宫事项",
    "兄弟": "借对宫兄弟{stars}之气，主手足同辈牵动此宫事项",
    "子女": "借对宫子女{stars}之气，主子女晚辈牵动此宫事项",
    "田宅": "借对宫田宅{stars}之气，主家宅产业牵动此宫事项",
    "父母": "借对宫父母{stars}之气，主长辈文书牵动此宫事项",
    "仆役": "借对宫仆役{stars}之气，主朋友下属牵动此宫事项",
    "疾厄": "借对宫疾厄{stars}之气，主身体健康牵动此宫事项",
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
    extra_interpretation: str = ""  # Z80-B：组合/身体/行业/来因/补强语义
    conclusion: str = ""     # 综合断语段落
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


def _split_key_stars(spec: str) -> List[str]:
    """把词表键中"|"后的星描述拆成星名列表。

    兼容两种写法："星1+星2"（显式加号）与连写（如「太阳天梁」「地空地劫」，
    按两字星名切分）。特殊标记（无吉/科）原样返回。
    """
    if "+" in spec:
        return [s for s in spec.split("+") if s]
    if spec in ("无吉", "无主星", "科", "忌", "禄", "权"):
        return [spec]
    return [spec[i:i + 2] for i in range(0, len(spec), 2)]


def _match_star_keys(
    table: Dict[str, str],
    pname: str,
    major: List[str],
    minor: List[str],
    flags: Optional[List[str]] = None,
    extra_stars: Optional[List[str]] = None,
) -> List[str]:
    """在「宫名|星描述」词表中查出本宫命中的论断。

    flags 传入生年四化类型（如 ["科"]）与吉煞状态（如 ["无吉"]、["借对宫"]），
    用于「疾厄|科」「官禄|无吉」「田宅|借对宫」这类状态型键。
    extra_stars 传入借对宫主星（空宫时）。
    """
    hits: List[str] = []
    star_set = set(major) | set(minor) | set(extra_stars or [])
    flag_set = set(flags or [])
    for key, text in table.items():
        if "|" not in key:
            continue
        kp, spec = key.split("|", 1)
        if kp != pname:
            continue
        want = _split_key_stars(spec)
        if want[0] in ("无吉", "科", "忌", "禄", "权", "借对宫", "无主星"):
            if want[0] in flag_set:
                hits.append(text)
            continue
        if all(s in star_set for s in want):
            hits.append(text)
    return hits


def _push_extra(extras: List[str], text: str) -> None:
    """把一条补强语义按"；"拆成片段逐条加入 extras。

    Z80-D：整句相等去重拦不住"部分包含"重复（如「子女主见极强…」
    既在双星组合文案里、又是单星文案的前半句），故拆片段级去重：
    新片段已被现有 extras 包含则跳过；新片段包含旧片段则以新片段替换旧的。
    """
    for frag in (f.strip() for f in text.split("；")):
        if not frag:
            continue
        joined = "；".join(extras)
        if frag in joined:
            continue
        for i, old in enumerate(extras):
            if old in frag:
                extras[i] = frag
                break
        else:
            extras.append(frag)


def _synthesize_extra(
    pname: str,
    major: List[str],
    minor: List[str],
    sihua_text: str,
    zihua_text: str,
    opposite_text: str,
    all_palaces: dict,
    chart_body_flags: Optional[List[str]] = None,
) -> str:
    """Z80-B：合成组合语义 / 身体映射 / 行业适配 / 来因宫 / 宫位补强。"""
    extras: List[str] = []
    flags: List[str] = list(chart_body_flags or [])
    # Z80-B：空宫借对宫 —— 把对宫主星纳入组合匹配，并给"借对宫"状态标记
    borrowed: List[str] = []
    if not major:
        opp = OPPOSITE_PALACE.get(pname, "")
        if opp:
            borrowed = list(all_palaces.get(opp, {}).get("major", []))
    # Z80-B：三方会照星（同三合局地支之宫的主星）也纳入组合匹配
    SANHE_GROUPS = ({"申", "子", "辰"}, {"亥", "卯", "未"},
                    {"寅", "午", "戌"}, {"巳", "酉", "丑"})
    my_branch = str(all_palaces.get(pname, {}).get("branch", "")).strip("'\"")
    sanhe_stars: List[str] = []
    for grp in SANHE_GROUPS:
        if my_branch in grp:
            for op, od in all_palaces.items():
                if op != pname and str(od.get("branch", "")).strip("'\"") in grp:
                    sanhe_stars.extend(od.get("major", []))
    if "科" in sihua_text:
        flags.append("科")
    if "忌" in sihua_text:
        flags.append("忌")
    if "禄" in sihua_text:
        flags.append("禄")
    if "权" in sihua_text:
        flags.append("权")
    ji_stars = {"左辅", "右弼", "天魁", "天钺", "禄存", "文昌", "文曲"}
    if pname == "官禄" and not (set(minor) & ji_stars):
        flags.append("无吉")
    if not major:
        flags.append("无主星")

    # 1. 主星组合 / 宫位补强（含状态型键；Z80-D：组合只认本宫实际星，
    #    三方会照星不得冒充"同宫"组合，否则虚匹配出重复/错误文案）
    for t in (STAR_PAIR_VERDICTS, PALACE_EXTRA_SEMANTICS):
        for v in _match_star_keys(t, pname, major, minor, flags):
            _push_extra(extras, v)

    # 1.5 Z80-C：借宫语义按本盘实际对宫主星动态生成（不写死案例盘）
    if not major and borrowed:
        opp = OPPOSITE_PALACE.get(pname, "")
        tpl = BORROWED_SEMANTICS.get(opp, "")
        if tpl:
            _push_extra(extras, tpl.format(stars="、".join(borrowed)))

    # 2. 疾厄宫：星曜 → 身体系统 + 煞星病程
    if pname == "疾厄":
        for s in major:
            _push_extra(extras, STAR_BODY_ORGANS.get(s, ""))
        for s in minor:
            _push_extra(extras, SHA_DISEASE_TRAIT.get(s, ""))

    # 3. 命宫：独座主星的人生底色
    if pname == "命宫":
        for s in major:
            _push_extra(extras, STAR_SOLO_VERDICTS.get(s, ""))

    # 4. 官禄/命宫：适配行业赛道
    if pname in ("官禄", "命宫"):
        for s in major:
            _push_extra(extras, CAREER_FIT.get(s, ""))
        # 杀破狼格局（命宫三方会齐七杀/破军/贪狼）
        if pname == "命宫" and {"七杀", "破军", "贪狼"} <= (set(major) | set(borrowed) | set(sanhe_stars)):
            _push_extra(extras, CAREER_FIT.get("杀破狼", ""))

    # 5. 来因宫（isOriginal 标记）
    pdata = all_palaces.get(pname, {})
    if pdata.get("isOriginal"):
        _push_extra(extras, LAIYIN_SEMANTICS.get(pname, ""))
    # 身宫标记
    if pname != "命宫" and pdata.get("isBody"):
        _push_extra(extras, f"{pname}为身宫所在，后天际遇与精神寄托偏向此宫")

    return "；".join(extras)


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
        # Z80-D：仆役宫消费「交友」措辞的表时，宫名措辞随盘面统一，
        # 避免输出"天姚称入交友"而本盘宫名实为"仆役"的宫名不一致。
        if interp and pname == "仆役":
            interp = interp.replace("入交友", "入仆役").replace("交友宫", "仆役宫")
        if interp and interp not in minor_parts:
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
            # Z80-D：仆役宫消费「交友」措辞表时统一宫名
            if interp and pname == "仆役":
                interp = interp.replace("交友", "仆役")
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

    # ── 5.5 组合语义 / 身体映射 / 行业 / 来因宫（Z80-B）──
    extra_text = _synthesize_extra(
        pname, major, all_minor, sihua_text, zihua_text,
        opposite_text, all_palaces,
    )

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
    if extra_text:
        parts.append(extra_text)

    conclusion = "；".join(parts) + "。" if parts else f"{pname}暂无主星，借对宫论断。"

    # ── 7. 关键概念提取 ──
    concepts = []
    full_text = " ".join([major_text, minor_text, sihua_text, zihua_text, opposite_text, extra_text])
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
        extra_interpretation=extra_text,
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
        # Z80-C：并入相关宫的补强语义（组合/身体/行业/来因），
        # 并按领域主题过滤，避免跨领域污染（如事业断语混入健康）
        extra_bits = []
        for p in related:
            ex = getattr(pr_map[p], "extra_interpretation", "")
            if not ex:
                continue
            for bit in ex.split("；"):
                bit = bit.strip()
                if bit and bit not in extra_bits and _extra_on_domain(bit, domain):
                    extra_bits.append(bit)
        if extra_bits:
            domain_conclusion = domain_conclusion.rstrip("。") + "；" + "；".join(extra_bits) + "。"

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
        parts.append(f"{jiao.palace}{jiao.major_interpretation}")
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


# ============================================================================
# Z80-C：领域主题过滤——extra 语义按主题并入对应领域，避免跨领域污染
# （例：命宫"杀破狼行业赛道"不得混入健康领域）
# ============================================================================

DOMAIN_STRONG_TERMS: Dict[str, List[str]] = {
    "健康": ["疾厄", "健康", "体质", "慢性病", "妇科", "内分泌", "肾脏", "泌尿",
             "失眠", "焦虑", "神经", "躯体", "手术", "炎症", "体虚", "湿气", "良医",
             "脾胃", "消化", "呼吸", "咽喉", "骨骼", "脊椎", "血压", "心血管",
             "眼睛", "皮肤", "肝胆", "肺部", "生殖"],
    "学业": ["学业", "学习", "进修", "考证", "深耕专业", "悟性", "考试", "研究", "学术"],
    "事业": ["事业", "官禄", "创业", "跳槽", "岗位", "职业", "赛道", "行业",
             "项目管理", "技术研发", "运营", "转型", "亲力亲为", "裸辞"],
    "财运": ["财帛", "理财", "破财", "守财", "投资", "储蓄", "消费", "投机",
             "求财", "房产", "置业", "产业", "借贷", "开销", "正财"],
    "人际": ["兄弟", "交友", "朋友", "人脉", "贵人", "小人", "知己", "合伙",
             "交游", "手足", "下属"],
    "婚恋": ["夫妻", "配偶", "婚姻", "感情", "伴侣", "恋爱", "第三者", "冷战",
             "桃花", "争吵"],
    "子女": ["子女", "亲子", "教养", "管教", "晚辈"],
    "父母": ["父母", "长辈", "祖业", "遗传"],
}


def _extra_on_domain(text: str, domain: str) -> bool:
    """判断一条宫位补强语义是否与该领域主题相关（供领域聚合过滤）。"""
    terms = DOMAIN_STRONG_TERMS.get(domain, [])
    if any(t in text for t in terms):
        return True
    # 通用语义（命宫底色/来因/身宫等未命中任何领域特征词）允许并入
    all_terms = [t for tl in DOMAIN_STRONG_TERMS.values() for t in tl]
    return not any(t in text for t in all_terms)


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
                    advice.append("定期妇科体检，长期调理")
                elif star == "铃星" and domain == "健康":
                    risks.append("铃星持续带来隐性焦虑，压力积压容易躯体化")
                    advice.append("固定作息，情绪宣泄，减少熬夜")
            # Z80-F（2026-10-14）：贪狼是欲望/桃花星，非煞星，须独立判定。
            # 此前该分支嵌在煞星 if 内，而外层元组不含「贪狼」→ elif 永不可达，
            # 「贪狼忌破财」风险与建议从不产出。
            if star == "贪狼" and "忌" in full_text and domain == "财运":
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
