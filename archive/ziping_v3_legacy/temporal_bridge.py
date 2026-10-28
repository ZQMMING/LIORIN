# -*- coding: utf-8 -*-
"""ZIPING V3.1 时序桥接引擎 (LiuYue/LiuRi).

基于sxtwl库实现流月/流日干支计算，
叠加于原局+大运+流年之后，形成五重时序推演。

原局 → 大运 → 流年 → 流月 → 流日
"""
from __future__ import annotations
import sxtwl
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


@dataclass
class LiuYueVerdict:
    """流月吉凶判定结果."""
    month: str = ""           # 干支, 如 "丁酉"
    month_num: int = 0        # 农历月份 1-12
    
    stem_relation: str = "NEUTRAL"
    branch_relation: str = "NEUTRAL"
    relations: List[Dict[str, str]] = field(default_factory=list)
    
    yong_effect: str = "NEUTRAL"
    yong_detail: str = ""
    
    ji_xiong: str = "UNKNOWN"
    reason: str = ""


@dataclass
class LiuRiVerdict:
    """流日吉凶判定结果."""
    day: str = ""
    date: str = ""
    
    stem_relation: str = "NEUTRAL"
    branch_relation: str = "NEUTRAL"
    relations: List[Dict[str, str]] = field(default_factory=list)
    
    yong_effect: str = "NEUTRAL"
    yong_detail: str = ""
    
    ji_xiong: str = "UNKNOWN"
    reason: str = ""


class LiuYueEngine:
    """流月引擎 — 基于sxtwl库计算农历月干支."""
    
    BRANCH_CHONG = {
        "ZI": "WU", "WU": "ZI", "CHOU": "WEI", "WEI": "CHOU",
        "YIN": "SHEN", "SHEN": "YIN", "MAO": "YOU", "YOU": "MAO",
        "CHEN": "XU", "XU": "CHEN", "SI": "HAI", "HAI": "SI",
    }
    BRANCH_HE = {
        "ZI": "CHOU", "CHOU": "ZI", "YIN": "HAI", "HAI": "YIN",
        "MAO": "XU", "XU": "MAO", "CHEN": "YOU", "YOU": "CHEN",
        "SI": "SHEN", "SHEN": "SI", "WU": "WEI", "WEI": "WU",
    }
    STEM_HE = {
        "JIA": "JI", "JI": "JIA",
        "BING": "XIN", "XIN": "BING",
        "WU": "GUI", "GUI": "WU",
        "DING": "REN", "REN": "DING",
        "GENG": "YI", "YI": "GENG",
    }
    STEM_WUXING = {
        "JIA": "WOOD", "YI": "WOOD",
        "BING": "FIRE", "DING": "FIRE",
        "WU": "EARTH", "JI": "EARTH",
        "GENG": "METAL", "XIN": "METAL",
        "REN": "WATER", "GUI": "WATER",
    }
    
    # 五虎遁: 甲己年起丙寅
    MONTH_START_STEM = {
        "JIA": "BING", "JI": "BING",
        "BING": "GENG", "XIN": "GENG",
        "WU": "REN", "GUI": "REN",
        "GENG": "WU", "YI": "WU",
        "REN": "JIA", "DING": "JIA",
    }
    
    MONTH_BRANCHES = ["YIN", "MAO", "CHEN", "SI", "WU", "WEI", 
                      "SHEN", "YOU", "XU", "HAI", "ZI", "CHOU"]
    
    # sxtwl整数 → 天干拼音映射 (sxtwl tg/dz 为 0-based: 0=JIA, 0=ZI)
    TG_MAP = {
        0: "JIA", 1: "YI", 2: "BING", 3: "DING", 4: "WU",
        5: "JI", 6: "GENG", 7: "XIN", 8: "REN", 9: "GUI",
    }
    DZ_MAP = {
        0: "ZI", 1: "CHOU", 2: "YIN", 3: "MAO", 4: "CHEN", 5: "SI",
        6: "WU", 7: "WEI", 8: "SHEN", 9: "YOU", 10: "XU", 11: "HAI",
    }

    def get_month_gz(self, year: int, month: int) -> str:
        """计算流月干支 (基于五虎遁规则).

        修: 原 str(year_gz.tg) 查 拼音表 永不命中 (sxtwl 返回整数, 原 MONTH_START_STEM
        键为拼音), 一律 fallback JIA; 现先映射为拼音再查表.
        年干取 1月1日 的 getYearGZ (sxtwl 内部按立春边界已处理).
        """
        year_gz = sxtwl.Day.fromSolar(year, 1, 1).getYearGZ()
        year_gan = self.TG_MAP.get(year_gz.tg, "JIA")
        start_gan = self.MONTH_START_STEM.get(year_gan, "JIA")
        month_zhi = self.MONTH_BRANCHES[(month - 1) % 12]
        
        stems = ["JIA", "YI", "BING", "DING", "WU", "JI", 
                 "GENG", "XIN", "REN", "GUI"]
        start_idx = stems.index(start_gan)
        month_gan = stems[(start_idx + month - 1) % 10]
        
        return f"{month_gan}{month_zhi}"
    
    def verdict(self, liuyue_gz: str, chart_info: Dict[str, Any],
                yongshen: Any) -> LiuYueVerdict:
        """判定流月吉凶."""
        lv = LiuYueVerdict(month=liuyue_gz)
        gan = liuyue_gz[:2].upper()
        zhi = liuyue_gz[2:].upper()
        
        lv.relations = self._check_relations(gan, zhi, chart_info)
        lv.stem_relation = self._classify_relation(lv.relations, "stem")
        lv.branch_relation = self._classify_relation(lv.relations, "branch")
        lv.yong_effect, lv.yong_detail = self._judge_yong_effect(gan, chart_info, yongshen)
        lv.ji_xiong, lv.reason = self._synthesize(lv, lv.yong_effect)
        
        return lv
    
    def _check_relations(self, gan: str, zhi: str, 
                         chart_info: Dict[str, Any]) -> List[Dict[str, str]]:
        four_stems = chart_info.get("four_stems", [])
        four_branches = chart_info.get("four_branches", [])
        relations = []
        
        for i, bz in enumerate(four_branches):
            if bz == zhi:
                relations.append({"type": "伏吟", "target": f"第{i+1}柱地支{bz}", 
                                 "effect": "流月伏吟"})
            elif self.BRANCH_CHONG.get(bz) == zhi:
                relations.append({"type": "冲", "target": f"第{i+1}柱地支{bz}", 
                                 "effect": f"流月{zhi}冲命局{bz}"})
            elif self.BRANCH_HE.get(bz) == zhi:
                relations.append({"type": "合", "target": f"第{i+1}柱地支{bz}", 
                                 "effect": f"流月{zhi}合命局{bz}"})
        
        for i, bs in enumerate(four_stems):
            if bs == gan:
                relations.append({"type": "伏吟", "target": f"第{i+1}柱天干{bs}", 
                                 "effect": "流月伏吟"})
            elif self.STEM_HE.get(bs) == gan:
                relations.append({"type": "合", "target": f"第{i+1}柱天干{bs}", 
                                 "effect": f"流月{gan}合命局{bs}"})
        
        return relations
    
    def _classify_relation(self, relations: List[Dict], dim: str) -> str:
        target_list = [r for r in relations if dim in r.get("target", "")]
        if not target_list:
            return "NEUTRAL"
        types = [r["type"] for r in target_list]
        if "冲" in types:
            return "CHONG"
        if "合" in types:
            return "HE"
        if "伏吟" in types:
            return "FUYIN"
        return "NEUTRAL"
    
    def _judge_yong_effect(self, gan: str, chart_info: Dict, yongshen: Any) -> tuple:
        yong_5x = yongshen.primary_yong if hasattr(yongshen, 'primary_yong') else ""
        ji_5x = yongshen.Ji_shen if hasattr(yongshen, 'Ji_shen') else ""
        help_5x = yongshen.primary_help if hasattr(yongshen, 'primary_help') else ""
        
        gan_5x = self.STEM_WUXING.get(gan, "UNKNOWN")
        
        if gan_5x == yong_5x:
            return "HELP", f"流月天干{gan}为用神{yong_5x}"
        elif gan_5x == ji_5x:
            return "HARM", f"流月天干{gan}为忌神{ji_5x}"
        elif gan_5x == help_5x:
            return "HELP", f"流月天干{gan}为喜神{help_5x}"
        return "NEUTRAL", ""
    
    def _synthesize(self, lv: LiuYueVerdict, effect: str) -> tuple:
        # 枚举契约: JI=吉, XIONG=凶
        if effect == "HELP":
            return "JI", "流月助用神"
        elif effect == "HARM":
            return "XIONG", "流月助忌神"
        return "UNCLEAR", "关系复杂需详判"
    
    @staticmethod
    def to_dict(lv: LiuYueVerdict) -> Dict[str, Any]:
        return {
            "month": lv.month,
            "month_num": lv.month_num,
            "stem_relation": lv.stem_relation,
            "branch_relation": lv.branch_relation,
            "relations": lv.relations,
            "yong_effect": lv.yong_effect,
            "yong_detail": lv.yong_detail,
            "ji_xiong": lv.ji_xiong,
            "reason": lv.reason,
        }


class LiuRiEngine:
    """流日引擎 — 基于sxtwl库计算日干支."""
    
    BRANCH_CHONG = LiuYueEngine.BRANCH_CHONG
    BRANCH_HE = LiuYueEngine.BRANCH_HE
    STEM_HE = LiuYueEngine.STEM_HE
    STEM_WUXING = LiuYueEngine.STEM_WUXING
    TG_MAP = LiuYueEngine.TG_MAP
    DZ_MAP = LiuYueEngine.DZ_MAP
    
    def verdict(self, date: datetime, chart_info: Dict[str, Any],
                yongshen: Any) -> LiuRiVerdict:
        """判定流日吉凶."""
        d = sxtwl.Day.fromSolar(date.year, date.month, date.day)
        gz = d.getDayGZ()
        # sxtwl返回整数, 需映射为拼音
        day_gz = f"{self.TG_MAP.get(gz.tg, '?')}{self.DZ_MAP.get(gz.dz, '?')}"
        
        lv = LiuRiVerdict(day=day_gz, date=date.strftime("%Y-%m-%d"))
        gan = self.TG_MAP.get(gz.tg, "").upper()
        zhi = self.DZ_MAP.get(gz.dz, "").upper()
        
        lv.relations = self._check_relations(gan, zhi, chart_info)
        lv.stem_relation = self._classify_relation(lv.relations, "stem")
        lv.branch_relation = self._classify_relation(lv.relations, "branch")
        lv.yong_effect, lv.yong_detail = self._judge_yong_effect(gan, chart_info, yongshen)
        lv.ji_xiong, lv.reason = self._synthesize(lv, lv.yong_effect)
        
        return lv
    
    def _check_relations(self, gan: str, zhi: str, 
                         chart_info: Dict[str, Any]) -> List[Dict[str, str]]:
        four_stems = chart_info.get("four_stems", [])
        four_branches = chart_info.get("four_branches", [])
        relations = []
        
        for i, bz in enumerate(four_branches):
            if bz == zhi:
                relations.append({"type": "伏吟", "target": f"第{i+1}柱地支{bz}", 
                                 "effect": "流日伏吟"})
            elif self.BRANCH_CHONG.get(bz) == zhi:
                relations.append({"type": "冲", "target": f"第{i+1}柱地支{bz}", 
                                 "effect": f"流日{zhi}冲命局{bz}"})
            elif self.BRANCH_HE.get(bz) == zhi:
                relations.append({"type": "合", "target": f"第{i+1}柱地支{bz}", 
                                 "effect": f"流日{zhi}合命局{bz}"})
        
        for i, bs in enumerate(four_stems):
            if bs == gan:
                relations.append({"type": "伏吟", "target": f"第{i+1}柱天干{bs}", 
                                 "effect": "流日伏吟"})
            elif self.STEM_HE.get(bs) == gan:
                relations.append({"type": "合", "target": f"第{i+1}柱天干{bs}", 
                                 "effect": f"流日{gan}合命局{bs}"})
        
        return relations
    
    def _classify_relation(self, relations: List[Dict], dim: str) -> str:
        target_list = [r for r in relations if dim in r.get("target", "")]
        if not target_list:
            return "NEUTRAL"
        types = [r["type"] for r in target_list]
        if "冲" in types:
            return "CHONG"
        if "合" in types:
            return "HE"
        if "伏吟" in types:
            return "FUYIN"
        return "NEUTRAL"
    
    def _judge_yong_effect(self, gan: str, chart_info: Dict, yongshen: Any) -> tuple:
        yong_5x = yongshen.primary_yong if hasattr(yongshen, 'primary_yong') else ""
        ji_5x = yongshen.Ji_shen if hasattr(yongshen, 'Ji_shen') else ""
        help_5x = yongshen.primary_help if hasattr(yongshen, 'primary_help') else ""
        
        gan_5x = self.STEM_WUXING.get(gan, "UNKNOWN")
        
        if gan_5x == yong_5x:
            return "HELP", f"流日天干{gan}为用神{yong_5x}"
        elif gan_5x == ji_5x:
            return "HARM", f"流日天干{gan}为忌神{ji_5x}"
        elif gan_5x == help_5x:
            return "HELP", f"流日天干{gan}为喜神{help_5x}"
        return "NEUTRAL", ""
    
    def _synthesize(self, lv: LiuRiVerdict, effect: str) -> tuple:
        # 枚举契约: JI=吉, XIONG=凶
        if effect == "HELP":
            return "JI", "流日助用神"
        elif effect == "HARM":
            return "XIONG", "流日助忌神"
        return "UNCLEAR", "关系复杂需详判"
    
    @staticmethod
    def to_dict(lv: LiuRiVerdict) -> Dict[str, Any]:
        return {
            "day": lv.day,
            "date": lv.date,
            "stem_relation": lv.stem_relation,
            "branch_relation": lv.branch_relation,
            "relations": lv.relations,
            "yong_effect": lv.yong_effect,
            "yong_detail": lv.yong_detail,
            "ji_xiong": lv.ji_xiong,
            "reason": lv.reason,
        }
