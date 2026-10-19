# -*- coding: utf-8 -*-
"""恶神抵消表 (V7.25 收敛, 替换 case-by-case 散落 if).

方法论: 引擎按算理算, 不按案例调 —— 恶神判定收敛成本模块一张集中表,
suiyun_validate verdict / yongshen_engine 多轨 B4 两处消费, 不再各补 if.

算理(原典):
  刑/冲月令/冲主药根/破格 = 恶神(刑伤/提纲伤/药根拔/格破) —— 原典重刑重冲,
  刑伤主凶, 与制化之功不同类(刑是结构伤, 制化是病药路), 不抵消药。
  冲药根 + 岁运支本气化泄 = 冲药假象, 抵消化泄(不抵冲药之凶)。
  合绊 = 药被合去失制力(抵消制), 与刑冲不同类(合去=失用, 刑=受伤)。
  全为布尔/字符串前缀判定, 禁浮点。

原典锚点:
  丑戌未恃势之刑/寅巳申无恩之刑/子卯刑 -> 刑伤主凶(不抵消制化)
  冲月令提纲 -> 提纲伤(原典"提纲为月令, 冲提纲主凶")
  冲主药根 -> 药根拔失用(冲药假象抵消化泄)
  破格 -> 格破(原典"破格则凶")
"""
from typing import List, Dict, Any, Optional

# 恶神前缀表: 命中即入 evil_no_offset(刑/冲药根/破格), 不抵消制化之功 -> 判毒药主凶.
#   冲月令提纲/冲日主重根 = 提纲伤(交战性, 非刑伤), 走平战(吉凶交战), 不入毒药.
#   原典: 刑(恃势/无恩/无礼)主凶伤; 冲提纲=提纲伤交战(平战), 冲药根=药根拔(毒药).
_EVIL_PREFIX = ('三刑', '格局破格')
# 交战性前缀: 命中即入 hard_bad(凶), 但不抵消制化之功(平战, 非毒药)
_CONFLICT_PREFIX = ('冲月令', '冲日主重根')
# 冲药根专属前缀: 命中则抵消该岁运支本气的"化泄"(冲药假象)
_MED_PULLED_PREFIX = '冲拔主药根'
# 合绊前缀: 药被合去失制力(抵消制, 走 hard_bad)
_BLOCK_PREFIX = '主药被合绊'


def evil_no_offset(bad_items: List[str]) -> bool:
    """bad 列表中有无恶神(刑/冲药根/破格). 有 -> 不抵消制化之功 -> 判毒药主凶.
    全布尔, 禁浮点."""
    return any(any(k in b for k in (_EVIL_PREFIX + (_MED_PULLED_PREFIX,))) for b in (bad_items or []))


def conflict_no_offset(bad_items: List[str]) -> bool:
    """bad 列表中有无交战性恶神(冲提纲/冲重根). 有 -> 走平战(吉凶交战), 非毒药.
    原典: 冲提纲=提纲伤交战, 不抵消化/制之功(平战), 但记凶. 全布尔."""
    return any(any(k in b for k in _CONFLICT_PREFIX) for b in (bad_items or []))


def medicine_pulled(bad_items: List[str]) -> bool:
    """bad 中是否含冲药根 -> 该岁运支本气的化泄为冲药假象, 抵消化泄."""
    return any(_MED_PULLED_PREFIX in b for b in (bad_items or []))


def medicine_blocked(bad_items: List[str]) -> bool:
    """bad 中是否含合绊 -> 药被合去失制力(抵消制, 走 hard_bad)."""
    return any(_BLOCK_PREFIX in b for b in (bad_items or []))


def verdict_arbitrate(good: List[str], bad: List[str]) -> Dict[str, Any]:
    """verdict 集中裁决(恶神抵消表): 查 good/bad -> level/shorthand/direction.
    全为布尔, 禁浮点。

    裁决序:
      - 恶神(刑/冲药根/破格) -> 毒药(level-2), 不抵消制化之功
      - 交战(冲提纲/重根) + hard_good -> 平战(level0, 吉凶交战), 提綱伤非刑伤
      - hard_good(无恶神/交战) -> 良药(level2)
      - 纯 good(非 hard_good) -> 平药(level1)
      - 纯 bad(无 hard_good) -> 毒药(level-2)
      - else -> 平(level0)
    """
    hard_good = any(('制主病' in x or '化泄' in x or '暖化' in x) for x in (good or []))
    if bad and evil_no_offset(bad or []):
        return {'level': -2, 'shorthand': '毒药',
                'note': '恶神(刑/冲药根/破格)不抵消制化之功, 判主凶'}
    if bad and conflict_no_offset(bad or []):
        return {'level': 0, 'shorthand': '平战',
                'note': '交战(冲提纲/重根)+制化之功, 吉凶交战不平'}
    if bad:
        return {'level': -2, 'shorthand': '毒药', 'note': '药受制(凶)'}
    if hard_good:
        return {'level': 2, 'shorthand': '良药', 'note': '病得制化/暖解, 可顺势进取'}
    if good:
        return {'level': 1, 'shorthand': '良药', 'note': '身得帮, 宜稳守蓄力'}
    return {'level': 0, 'shorthand': '平', 'note': '平淡无大关目, 常守'}
