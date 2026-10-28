# -*- coding: utf-8 -*-
"""ZIPING 解层 — 12人生维度 (子平五经体系).

基于五经原文重新设计12人生维度:
- 《滴天髓·何知章》: 富贵贫贱吉凶寿夭
- 《子平真诠》: 论妻子/论子息/论六亲
- 《渊海子平》: 六亲总论/十神论
- 《穷通宝鉴》: 调候用神

钩子采用五经原文真实词汇 (如"财气通门户"而非"财运好").
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

DUANYU_DB = Path(__file__).parent.parent.parent.parent.parent.parent / \
            "顺天系统资料" / "五部经典断语库" / "03_综合索引" / "all_duanyu.json"


@dataclass
class TriggeredDuanyu:
    """单条断语触发结果."""
    classic: str
    source: str
    primary_category: str
    text: str
    trigger_rule: str
    evidence_ref: str
    confidence: str
    quality: str = "UNKNOWN"


@dataclass
class InterpretationOutput:
    """解层输出契约 (15辨层域 + 12人生维度)."""
    # 各域断语
    ling: List[TriggeredDuanyu] = field(default_factory=list)
    growth: List[TriggeredDuanyu] = field(default_factory=list)
    root: List[TriggeredDuanyu] = field(default_factory=list)
    party: List[TriggeredDuanyu] = field(default_factory=list)
    strength: List[TriggeredDuanyu] = field(default_factory=list)
    qing: List[TriggeredDuanyu] = field(default_factory=list)
    climate: List[TriggeredDuanyu] = field(default_factory=list)
    tongguan: List[TriggeredDuanyu] = field(default_factory=list)
    disease: List[TriggeredDuanyu] = field(default_factory=list)
    qi: List[TriggeredDuanyu] = field(default_factory=list)
    pattern: List[TriggeredDuanyu] = field(default_factory=list)
    pattern_quality: List[TriggeredDuanyu] = field(default_factory=list)
    true: List[TriggeredDuanyu] = field(default_factory=list)
    special: List[TriggeredDuanyu] = field(default_factory=list)
    yong: List[TriggeredDuanyu] = field(default_factory=list)
    xiang: List[TriggeredDuanyu] = field(default_factory=list)
    xiji: List[TriggeredDuanyu] = field(default_factory=list)
    temporal: List[TriggeredDuanyu] = field(default_factory=list)
    
    # 人生维度断语 (子平五经体系 — 12维)
    # 01 性情禀赋: 《滴天髓·性情论》
    temperament: List[TriggeredDuanyu] = field(default_factory=list)
    # 02 交游人际: 《渊海子平·六亲》比劫关系
    social: List[TriggeredDuanyu] = field(default_factory=list)
    # 03 婚姻配偶: 《子平真诠·论妻子》
    marriage: List[TriggeredDuanyu] = field(default_factory=list)
    # 04 子女: 《子平真诠·论子息》
    children: List[TriggeredDuanyu] = field(default_factory=list)
    # 05 财帛: 《滴天髓·何知章》财气通门户
    wealth: List[TriggeredDuanyu] = field(default_factory=list)
    # 06 身体疾厄: 《滴天髓·疾病论》
    health: List[TriggeredDuanyu] = field(default_factory=list)
    # 07 迁移出行: 地支冲合驿马
    migration: List[TriggeredDuanyu] = field(default_factory=list)
    # 08 事业功名: 《滴天髓·何知章》官星有理会
    career: List[TriggeredDuanyu] = field(default_factory=list)
    # 09 田宅家业: 印星+库+年月柱
    property: List[TriggeredDuanyu] = field(default_factory=list)
    # 10 福德精神: 《滴天髓·何知章》性定元神厚
    fortune: List[TriggeredDuanyu] = field(default_factory=list)
    # 11 父母长辈: 《渊海子平·论父论母》
    parents: List[TriggeredDuanyu] = field(default_factory=list)
    # 12 才艺学业: 食伤吐秀+印星
    talent: List[TriggeredDuanyu] = field(default_factory=list)
    
    undetermined_domains: List[str] = field(default_factory=list)


class DuanyuLoader:
    """断语库加载器."""
    _EXCLUDE_PREFIXES = ("原注", "任氏曰", "书云", "目录")
    _EXCLUDE_STARTS = ("序", "《", "目")

    def __init__(self, db_path: Path = DUANYU_DB):
        self._db_path = db_path
        self._cache: Optional[List[Dict[str, Any]]] = None

    def load(self) -> List[Dict[str, Any]]:
        if self._cache is not None:
            return self._cache
        if not self._db_path.exists():
            raise FileNotFoundError(f"断语库不存在: {self._db_path}")
        with open(self._db_path, encoding="utf-8") as f:
            data = json.load(f)
        filtered = []
        for item in data:
            text = item.get("text", "")
            if not text:
                continue
            stripped = text.lstrip()
            if stripped[:2] in self._EXCLUDE_PREFIXES or stripped[:1] in self._EXCLUDE_STARTS:
                continue
            if not item.get("primary_category"):
                continue
            filtered.append(item)
        self._cache = filtered
        return filtered

    def load_by_categories(self, cats: List[str]) -> List[Dict[str, Any]]:
        all_data = self.load()
        return [x for x in all_data
                if x.get("primary_category") in cats or
                any(c in x.get("categories", []) for c in cats)]


class DomainResolver:
    """解层核心: §28状态 → 五经钩子 (真实原文词汇)."""

    # ═══════════════════════════════════════════════════════════════
    # 15辨层域钩子 (保持不变)
    # ═══════════════════════════════════════════════════════════════
    _LING_HOOKS = {"DE_LING": ["得令", "得时", "乘时", "当权", "司令"],
                   "SHI_LING": ["失令", "失时", "不当令"]}
    _GROWTH_HOOKS = {"ROOTING": ["有根", "根气", "通根", "落地"],
                     "WEAK_ROOT": ["根弱", "根浅", "虚浮"],
                     "NO_ROOT": ["无根", "虚浮", "根气全无"]}
    _ROOT_HOOKS = {"DETERMINED": ["有根", "根基稳固"]}
    _PARTY_HOOKS = {"DETERMINED": ["党众", "比劫帮身", "印绶生扶"],
                    "DOMINANT_SUPPORT": ["党众集中", "比劫旺盛"],
                    "DOMINANT_OPPOSE": ["党众分散", "孤立无援"]}
    _STRENGTH_HOOKS = {
        "STRONG": ["身旺", "得令", "有根", "党众"],
        "WEAK": ["身弱", "失令", "无根", "无助"],
        "BALANCED": ["中和", "平衡"],
        "WANG_BUT_NOT_STRONG": ["旺而不强", "身旺有制"],
        "WANG_OVER": ["旺极", "太过"],
        "WEAK_OVER": ["弱极", "不及"],
    }
    _PATTERN_HOOKS = {
        "SUCCESS": ["成格", "格局成立"],
        "FAIL": ["破格", "格局破坏"],
        "BLADE_FORMED": ["阳刃格", "刃旺宜制"],
        "OFFICER_FORMED": ["正官格", "官星有理会"],
        "WEALTH_FORMED": ["财格", "财气通门户"],
        "RESOURCE_FORMED": ["印格", "印绶生身"],
        "OUTPUT_FORMED": ["食神格", "食神吐秀"],
        "CHAI_GE": ["杂格", "格局杂乱"],
    }
    _CLIMATE_HOOKS = {"HOT": ["火炎土燥", "夏火", "暑热"],
                      "COLD": ["金寒水冷", "冬水", "寒冷"]}
    _QING_HOOKS = {"CLEAR": ["清纯", "不杂"],
                   "TURBID": ["混杂", "官杀混杂"]}
    _TONGGUAN_HOOKS = {
        "OPPOSITION_RESOLVED": ["通关", "化解"],
        "TONGGUAN_ABSENT": ["无通关", "争战无解"],
        "TONGGUAN_EFFECTIVE": ["通关有效", "桥用神得力"],
    }
    _DISEASE_HOOKS = {
        "HAS_DISEASE": ["有病", "有病无药"],
        "HAS_MEDICINE": ["有药", "有病有药"],
        "DISEASE_PRESENT": ["有病", "结构失衡"],
        "DISEASE_UNRESOLVED": ["有病无药", "病重药轻"],
        "DISEASE_ABSENT": ["无病", "结构平衡"],
    }
    _QI_HOOKS = {"CONCENTRATED": ["专", "清纯", "一气"]}
    _TRUE_HOOKS = {"TRUE": ["真", "真神", "真用"],
                   "FALSE": ["假", "假神", "假用"]}
    _SPECIAL_HOOKS = {"NONE": ["非从格", "普通格局"],
                      "CONG_WEAK": ["从弱", "弃命从势"],
                      "CONG_STRONG": ["从旺", "顺势而为"],
                      "ZHUN_WANG": ["专旺", "一气专旺"]}
    _XIANG_HOOKS = {"DETERMINED": ["相神", "用神得力"]}
    _YONG_HOOKS = {"BLADE_FORMED": ["阳刃格", "刃旺宜制"],
                   "OFFICER_FORMED": ["正官格", "官星有理会"],
                   "WEALTH_FORMED": ["财格", "财气通门户"],
                   "RESOURCE_FORMED": ["印格", "印绶生身"]}
    _XIJI_HOOKS = {"STRONG": ["身旺宜克泄"],
                   "WEAK": ["身弱宜生扶"]}
    _TEMPORAL_HOOKS = {"LUCK_PHASED": ["大运", "行运"]}

    # ═══════════════════════════════════════════════════════════════
    # 12人生维度钩子 (五经原文词汇)
    # ═══════════════════════════════════════════════════════════════

    # 01 性情禀赋: 《滴天髓·性情论》
    _TEMPERAMENT_HOOKS = {
        "FIRE_DAY": ["丙火猛烈", "丁火柔中", "炎上", "热情", "性急", "文明", "礼"],
        "WOOD_DAY": ["甲木参天", "乙木虽柔", "曲直", "仁", "温和", "条达"],
        "WATER_DAY": ["壬水通河", "癸水至弱", "润下", "智", "聪明", "变通"],
        "METAL_DAY": ["庚金带煞", "辛金软弱", "从革", "义", "刚毅", "果断"],
        "EARTH_DAY": ["戊土固重", "己土卑湿", "稼穑", "信", "厚重", "稳重"],
        "SHI_SHEN": ["食神吐秀", "伤官见官", "才华", "表达", "秀气"],
        "OFFICER_SHEN": ["正官清秀", "七杀刚猛", "权威", "纪律"],
    }

    # 02 交游人际: 《渊海子平·六亲》比劫关系
    _SOCIAL_HOOKS = {
        "GOOD": ["比肩帮身", "兄弟有助", "朋友多助", "贵人临门", "人脉广阔"],
        "BAD": ["比劫夺财", "兄弟参商", "孤立无援", "小人暗算", "众叛亲离"],
    }

    # 03 婚姻配偶: 《子平真诠·论妻子》
    _MARRIAGE_HOOKS = {
        "GOOD": ["坐下财官", "妻当贤贵", "财官有情", "妻能内助", "良缘佳偶"],
        "BAD": ["刑妻克子", "妻宫受冲", "夫星受损", "婚姻不顺", "离婚再嫁"],
    }

    # 04 子女: 《子平真诠·论子息》
    _CHILDREN_HOOKS = {
        "GOOD": ["长生四子", "沐浴一双", "冠带临官", "麟儿绕膝", "子贵"],
        "BAD": ["死中至老没儿郎", "入墓之时命夭亡", "子息艰难", "克子"],
    }

    # 05 财帛: 《滴天髓·何知章》
    _WEALTH_HOOKS = {
        "RICH": ["财气通门户", "富贵双全", "堆金积玉", "财源茂盛", "身强担财"],
        "POOR": ["财神反不真", "财多身弱", "一贫如洗", "劳碌无财", "富屋贫人"],
    }

    # 06 身体疾厄: 《滴天髓·疾病论》
    _HEALTH_HOOKS = {
        "HEALTHY": ["安康", "身体康健", "气脉调和", "五行中和"],
        "SICK": ["有病无药", "五行偏枯", "疾病缠身", "医药难救"],
    }

    # 07 迁移出行: 地支冲合驿马 (子平无专论，从冲合+气势推断)
    _MIGRATION_HOOKS = {
        "MOBILE": ["远行", "迁徙", "动中求财", "奔波", "出外发达"],
        "STABLE": ["安居乐业", "守成", "不动", "稳定", "本地发达"],
    }

    # 08 事业功名: 《滴天髓·何知章》
    _CAREER_HOOKS = {
        "SUCCESS": ["官星有理会", "功名显达", "科甲及第", "官印相生", "飞黄腾达"],
        "FAIL": ["官星还不见", "破格丢官", "仕途多蹇", "官非口舌"],
    }

    # 09 田宅家业: 印星+库
    _PROPERTY_HOOKS = {
        "GOOD": ["田宅丰隆", "家业兴旺", "祖业有靠", "印星得位"],
        "BAD": ["田宅破耗", "家业凋零", "祖业无靠", "印星受损"],
    }

    # 10 福德精神: 《滴天髓·何知章》性定元神厚/气浊神枯
    _FORTUNE_HOOKS = {
        "HIGH": ["元神厚", "福慧", "精神", "安乐", "心神安定", "福泽深厚"],
        "LOW": ["气浊", "神枯", "福薄", "精神困顿", "心神不宁"],
    }

    # 11 父母长辈: 《渊海子平·论父论母》
    _PARENTS_HOOKS = {
        "GOOD": ["父母双全", "长辈得力", "印星得用", "偏财有根"],
        "BAD": ["父母早丧", "六亲无靠", "印星受损", "偏财受克"],
    }

    # 12 才艺学业: 食伤+印星
    _TALENT_HOOKS = {
        "HIGH": ["食伤吐秀", "学业有成", "文采风流", "科甲联登", "文昌入命"],
        "LOW": ["食伤受制", "学业不顺", "怀才不遇", "科途受阻"],
    }

    DOMAIN_HOOKS = {
        "LING": _LING_HOOKS,
        "GROWTH": _GROWTH_HOOKS,
        "ROOT": _ROOT_HOOKS,
        "PARTY": _PARTY_HOOKS,
        "STRENGTH": _STRENGTH_HOOKS,
        "QING": _QING_HOOKS,
        "CLIMATE": _CLIMATE_HOOKS,
        "TONGGUAN": _TONGGUAN_HOOKS,
        "DISEASE": _DISEASE_HOOKS,
        "QI": _QI_HOOKS,
        "PATTERN": _PATTERN_HOOKS,
        "TRUE": _TRUE_HOOKS,
        "SPECIAL": _SPECIAL_HOOKS,
        "XIANG": _XIANG_HOOKS,
        "YONG": _YONG_HOOKS,
        "YONG-PATTERN": _YONG_HOOKS,
        "YONG-CLIMATE": _CLIMATE_HOOKS,
        "YONG-DISEASE": _DISEASE_HOOKS,
        "YONG-BRIDGE": _TONGGUAN_HOOKS,
        "XIJI": _XIJI_HOOKS,
        "TEMPORAL": _TEMPORAL_HOOKS,
        # 12人生维度
        "TEMPERAMENT": _TEMPERAMENT_HOOKS,
        "SOCIAL": _SOCIAL_HOOKS,
        "MARRIAGE": _MARRIAGE_HOOKS,
        "CHILDREN": _CHILDREN_HOOKS,
        "WEALTH": _WEALTH_HOOKS,
        "HEALTH": _HEALTH_HOOKS,
        "MIGRATION": _MIGRATION_HOOKS,
        "CAREER": _CAREER_HOOKS,
        "PROPERTY": _PROPERTY_HOOKS,
        "FORTUNE": _FORTUNE_HOOKS,
        "PARENTS": _PARENTS_HOOKS,
        "TALENT": _TALENT_HOOKS,
    }

    @classmethod
    def resolve_hooks(cls, domain: str, state: str) -> List[str]:
        hooks_dict = cls.DOMAIN_HOOKS.get(domain, {})
        return hooks_dict.get(state, [])


class DuanyuMatcher:
    """断语匹配器: 条件钩子 → 命局状态 → 断语文本."""

    def __init__(self, loader: DuanyuLoader):
        self._loader = loader

    def match(self, hooks: List[str], target_cats: List[str], limit: int = 20) -> List[TriggeredDuanyu]:
        candidates = self._loader.load_by_categories(target_cats)
        matched = []
        seen_texts = set()
        for cand in candidates:
            text = cand.get("text", "")
            if not text or len(text) < 8:
                continue
            if text in seen_texts:
                continue
            matched_hook = None
            for hook in sorted(hooks, key=len, reverse=True):
                if hook in text:
                    matched_hook = hook
                    break
            if matched_hook:
                seen_texts.add(text)
                matched.append(TriggeredDuanyu(
                    classic=cand.get("classic", ""),
                    source=cand.get("source", ""),
                    primary_category=cand.get("primary_category", ""),
                    text=text,
                    trigger_rule=f"{matched_hook}∈hooks",
                    evidence_ref=f"{cand.get('classic','')}·{cand.get('source','')}:{text[:40]}...",
                    confidence="STRONG",
                ))
                if len(matched) >= limit:
                    break
        return matched


def build_interpretation(judgments: List[Any], day_master: str = '') -> InterpretationOutput:
    """解层入口: §28状态 → 五经断语触发.

    Args:
        judgments: 判定的judgment列表
        day_master: 日主天干 (如'BING'), 用于性情维度判定
    """
    output = InterpretationOutput()
    domain_hooks = {}
    for j in judgments:
        if hasattr(j, 'domain'):
            dom = getattr(j, 'domain', '')
            st = getattr(j, 'state', '')
        else:
            dom = j.get('domain', '')
            st = j.get('state', '')
        if dom and st and st != 'UNDETERMINED':
            hooks = DomainResolver.resolve_hooks(dom, st)
            if hooks:
                domain_hooks[dom] = hooks

    matcher = DuanyuMatcher(DuanyuLoader())

    # 15辨层域断语
    DOMAIN_CATS = {
        "LING": ["用神喜忌类", "旺衰类"],
        "STRENGTH": ["旺衰类", "贫贱富贵类"],
        "QING": ["刑冲合害类"],
        "CLIMATE": ["用神喜忌类"],
        "TONGGUAN": ["刑冲合害类"],
        "DISEASE": ["疾病类", "用神喜忌类"],
        "QI": ["旺衰类"],
        "PATTERN": ["格局类"],
        "TRUE": ["格局类"],
        "SPECIAL": ["特殊格"],
        "XIJI": ["用神喜忌类"],
        "TEMPORAL": ["流年大运类"],
    }
    DOMAIN_FIELD = {
        "LING": "ling", "STRENGTH": "strength", "QING": "qing",
        "CLIMATE": "climate", "TONGGUAN": "tongguan", "DISEASE": "disease",
        "QI": "qi", "PATTERN": "pattern", "TRUE": "true",
        "SPECIAL": "special", "XIJI": "xiji", "TEMPORAL": "temporal",
    }
    for dom, hooks in domain_hooks.items():
        if dom in DOMAIN_FIELD:
            cats = DOMAIN_CATS.get(dom, ["用神喜忌类"])
            hits = matcher.match(hooks=hooks, target_cats=cats, limit=10)
            setattr(output, DOMAIN_FIELD[dom], hits)

    # 12人生维度断语 — 从辨层状态推导
    LIFE_CATS = {
        "TEMPERAMENT": ["用神喜忌类", "旺衰类"],
        "SOCIAL": ["六亲类", "用神喜忌类"],
        "MARRIAGE": ["婚姻类", "财运类"],
        "CHILDREN": ["子息类", "六亲类"],
        "WEALTH": ["财运类", "贫贱富贵类"],
        "HEALTH": ["疾病类", "寿夭类"],
        "MIGRATION": ["刑冲合害类", "神煞类"],
        "CAREER": ["官运类", "格局类"],
        "PROPERTY": ["财运类", "六亲类"],
        "FORTUNE": ["贫贱富贵类", "旺衰类"],
        "PARENTS": ["六亲类", "寿夭类"],
        "TALENT": ["官运类", "用神喜忌类"],
    }
    LIFE_FIELD = {
        "TEMPERAMENT": "temperament", "SOCIAL": "social", "MARRIAGE": "marriage",
        "CHILDREN": "children", "WEALTH": "wealth", "HEALTH": "health",
        "MIGRATION": "migration", "CAREER": "career", "PROPERTY": "property",
        "FORTUNE": "fortune", "PARENTS": "parents", "TALENT": "talent",
    }
    def derive_life_dimension(judgments, dimension, day_master):
        """基于15辨层域状态推导人生维度."""
        states = {}
        for j in judgments:
            if hasattr(j, 'domain'):
                dom = getattr(j, 'domain', '')
                st = getattr(j, 'state', '')
            else:
                dom = j.get('domain', '')
                st = j.get('state', '')
            if dom and st and st != 'UNDETERMINED':
                states[dom] = st
        
        if dimension == "TEMPERAMENT":
            # 性情禀赋: 日主五行+十神配置
            # day_master可能是拼音(BING)或中文(丙), 统一转大写比较
            dm_upper = day_master.upper()
            if 'BING' in dm_upper or 'DING' in dm_upper:
                return "FIRE_DAY"
            elif 'JIA' in dm_upper or 'YI' in dm_upper:
                return "WOOD_DAY"
            elif 'REN' in dm_upper or 'GUI' in dm_upper:
                return "WATER_DAY"
            elif 'GENG' in dm_upper or 'XIN' in dm_upper:
                return "METAL_DAY"
            elif 'WU' in dm_upper or 'JI' in dm_upper:
                return "EARTH_DAY"
            return "CONDITIONAL"
        
        elif dimension == "MARRIAGE":
            # 婚姻配偶: 清浊+通关+格局
            qing = states.get('QING', '')
            tongguan = states.get('TONGGUAN', '')
            pattern = states.get('PATTERN', '')
            if qing == 'CLEAR' and tongguan == 'OPPOSITION_RESOLVED':
                return "GOOD"
            elif qing == 'TURBID' or tongguan == 'TONGGUAN_ABSENT':
                return "BAD"
            return "CONDITIONAL"
        
        elif dimension == "WEALTH":
            # 财帛: 身强弱+党众
            strength = states.get('STRENGTH', '')
            party = states.get('PARTY', '')
            if strength in ('STRONG', 'WANG_BUT_NOT_STRONG', 'BALANCED'):
                return "RICH"
            elif strength in ('WEAK', 'WEAK_OVER'):
                return "POOR"
            return "CONDITIONAL"
        
        elif dimension == "CAREER":
            # 事业功名: 格局成败+相神
            pattern = states.get('PATTERN', '')
            xiang = states.get('XIANG', '')
            # PATTERN状态可能是BLADE_FORMED/SUCCESS/FAIL等
            if pattern in ('SUCCESS', 'BLADE_FORMED', '官格成', '财格成') and xiang in ('SUCCESS', 'DETERMINED'):
                return "SUCCESS"
            elif pattern in ('FAIL', 'BLADE_FAILED'):
                return "FAIL"
            return "CONDITIONAL"

        elif dimension == "CHILDREN":
            # 子女: 格局成败+时柱
            pattern = states.get('PATTERN', '')
            if pattern in ('SUCCESS', 'BLADE_FORMED'):
                return "GOOD"
            elif pattern in ('FAIL', 'BLADE_FAILED'):
                return "BAD"
            return "CONDITIONAL"
        
        elif dimension == "HEALTH":
            # 身体疾厄: 清浊+病药
            qing = states.get('QING', '')
            disease = states.get('DISEASE', '')
            if qing == 'CLEAR' and disease == 'DISEASE_ABSENT':
                return "HEALTHY"
            elif qing == 'TURBID' or disease == 'HAS_DISEASE':
                return "SICK"
            return "CONDITIONAL"
        
        elif dimension == "FORTUNE":
            # 福德精神: 气势+格局
            qi = states.get('QI', '')
            pattern = states.get('PATTERN', '')
            if qi == 'CONCENTRATED' and pattern in ('SUCCESS', 'BLADE_FORMED'):
                return "HIGH"
            elif qi == 'SCATTERED' or pattern in ('FAIL', 'BLADE_FAILED'):
                return "LOW"
            return "CONDITIONAL"

        elif dimension == "PARENTS":
            # 父母长辈: 党众+印星
            party = states.get('PARTY', '')
            if party in ('DOMINANT_SUPPORT', 'DETERMINED'):
                return "GOOD"
            elif party == 'DOMINANT_OPPOSE':
                return "BAD"
            return "CONDITIONAL"

        elif dimension == "TALENT":
            # 才艺学业: 身强弱+食伤
            strength = states.get('STRENGTH', '')
            if strength in ('STRONG', 'WANG_BUT_NOT_STRONG'):
                return "HIGH"
            elif strength in ('WEAK', 'WEAK_OVER'):
                return "LOW"
            return "CONDITIONAL"

        elif dimension == "SOCIAL":
            # 交游人际: 党众
            party = states.get('PARTY', '')
            if party in ('DOMINANT_SUPPORT', 'DETERMINED'):
                return "GOOD"
            elif party == 'DOMINANT_OPPOSE':
                return "BAD"
            return "CONDITIONAL"

        elif dimension == "MIGRATION":
            # 迁移出行: 气势流通
            qi = states.get('QI', '')
            if qi == 'CONCENTRATED':
                return "STABLE"
            elif qi == 'SCATTERED':
                return "MOBILE"
            return "CONDITIONAL"

        elif dimension == "PROPERTY":
            # 田宅家业: 印星+库
            party = states.get('PARTY', '')
            if party in ('DOMINANT_SUPPORT', 'DETERMINED'):
                return "GOOD"
            return "CONDITIONAL"
        
        return "CONDITIONAL"

    # 执行12人生维度推导
    for dom in ['TEMPERAMENT', 'SOCIAL', 'MARRIAGE', 'CHILDREN', 'WEALTH', 'HEALTH',
                'MIGRATION', 'CAREER', 'PROPERTY', 'FORTUNE', 'PARENTS', 'TALENT']:
        state = derive_life_dimension(judgments, dom, day_master)
        hooks = DomainResolver.resolve_hooks(dom, state)
        if hooks:
            cats = LIFE_CATS.get(dom, ["用神喜忌类"])
            hits = matcher.match(hooks=hooks, target_cats=cats, limit=10)
            field = LIFE_FIELD.get(dom, dom.lower())
            setattr(output, field, hits)

    return output
