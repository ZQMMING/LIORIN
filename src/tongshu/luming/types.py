# -*- coding: utf-8 -*-
"""禄命法引擎数据类型 — LumingChart (frozen, from_bazi_chart 唯一构造路径).

对齐项目 canonical 范式 (CanonicalBaziChart):
  - frozen=True, 构造后不可变
  - from_bazi_chart 为唯一合法构造路径, 登记 provenance, 可机器校验
  - 只消费 BaziChart 已算好的排盘事实, 不重算任何排盘字段
"""

from __future__ import annotations

import weakref
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

LM_PROVENANCE_FACTORY = "from_bazi_chart"
LM_PROVENANCE_DIRECT = "direct"

# 经 from_bazi_chart() 工厂构造的实例集合 (weakref, 不阻止 GC)
_FACTORY_OBJECT_IDS: weakref.WeakSet = weakref.WeakSet()


def _register_factory_instance(instance: "LumingChart") -> None:
    _FACTORY_OBJECT_IDS.add(instance)


def is_luming_factory_provenance(instance: "LumingChart") -> bool:
    """True 若经 from_bazi_chart() 工厂构造."""
    return id(instance) in _FACTORY_OBJECT_IDS


def assert_luming_gate(instance: "LumingChart", require_factory: bool = True) -> None:
    """下游消费前调用: 校验 LumingChart 来自合法工厂路径 (MUST NOT recompute)."""
    if require_factory and not is_luming_factory_provenance(instance):
        raise ValueError(
            "LumingChart 必须经 LumingEngine.from_bazi_chart() 构造, 不得直接实例化/重算排盘事实"
        )


@dataclass(frozen=True)
class LumingChart:
    """禄命法引擎产物: 年本三元立极 + 禄马 + 化气 + 岁运消费视图.

    全部字段为禄命法层判定结果, 消费自 BaziChart 排盘事实, 不重算。
    """

    # === 排盘事实引用 (透传, 供下游直接消费) ===
    four_pillars: tuple = field(default_factory=tuple)          # ((干, 支) x4)
    day_master: str = ""
    gender: str = "male"
    luck_pillars: tuple = field(default_factory=tuple)          # (干, 支) xN
    start_age: float = 0.0
    nayin: dict = field(default_factory=dict)                  # 四柱纳音名
    nayin_five_element: dict = field(default_factory=dict)     # 四柱纳音五行

    # === 年本三元立极 (禄命法核心: 年干=禄, 年支=命, 年纳音=身) ===
    san_yuan: dict = field(default_factory=dict)

    # === 禄马视图 (干禄 + 驿马) ===
    lu_ma: dict = field(default_factory=dict)

    # === 天乙贵人 (年干为主 + 日干辅助, 昼夜分治) ===
    gui_ren: dict = field(default_factory=dict)

    # === 禄命法神煞视图 (将星/华盖/劫煞/亡神/桃花/孤辰寡宿) ===
    shen_sha: dict = field(default_factory=dict)

    # === 化气判定 (天干五合成立 / 六合助力 / 三合成局) ===
    hua_qi: dict = field(default_factory=dict)

    # === 缺口补齐第三批: 原局三刑/六害/纳音生克链/文昌/拱 ===
    san_xing: tuple = field(default_factory=tuple)     # 原局三刑组
    liu_hai: tuple = field(default_factory=tuple)      # 原局六害对
    nayin_chain: dict = field(default_factory=dict)    # 四柱+胎元+命宫+身宫纳音 vs 年命
    wen_chang: dict = field(default_factory=dict)      # 文昌 (默认年干表 L2010; lookup_mode=day 时日干查)
    gong: dict = field(default_factory=dict)           # 拱 (夹拱/三合虚拱)

    # === 结构化断语 (确定性事实 → 原文断语, 带证据ID) ===
    verdicts: tuple = field(default_factory=tuple)

    # === 吉凶分级 (tone 只按原文明示吉凶词核定; 分层计数 + 当前运 + overall) ===
    tone_scope: dict = field(default_factory=dict)

    # === 岁运消费 (大运透传; 小运来自 spec 层, 待接标记) ===
    luck_scope: dict = field(default_factory=dict)

    # === 原局喜忌层 (卷七论五行一 L1254-1270) ===
    xi_ji: dict = field(default_factory=dict)

    # === 日主旺衰 (得令/得地/得势, 滴天髓任铁樵口径) — 原局根本 ===
    day_strength: dict = field(default_factory=dict)

    # === 来源 ===
    provenance: str = LM_PROVENANCE_FACTORY

    # frozen dataclass 含 dict 字段时默认 __hash__ 会失败 (unhashable dict),
    # 显式用对象身份 hash, 供 WeakSet provenance 登记使用。
    __hash__ = object.__hash__

    def to_dict(self) -> dict:
        """序列化 (调试/日志)."""
        return {
            "four_pillars": [list(p) for p in self.four_pillars],
            "day_master": self.day_master,
            "gender": self.gender,
            "luck_pillars": [list(p) for p in self.luck_pillars],
            "start_age": self.start_age,
            "nayin": dict(self.nayin),
            "nayin_five_element": dict(self.nayin_five_element),
            "san_yuan": {k: dict(v) for k, v in self.san_yuan.items()},
            "lu_ma": {k: (dict(v) if isinstance(v, dict) else v) for k, v in self.lu_ma.items()},
            "gui_ren": {k: (dict(v) if isinstance(v, dict) else v) for k, v in self.gui_ren.items()},
            "shen_sha": {k: (dict(v) if isinstance(v, dict) else v) for k, v in self.shen_sha.items()},
            "hua_qi": {k: dict(v) for k, v in self.hua_qi.items()},
            "san_xing": list(self.san_xing),
            "liu_hai": [list(p) for p in self.liu_hai],
            "nayin_chain": dict(self.nayin_chain),
            "wen_chang": dict(self.wen_chang),
            "gong": dict(self.gong),
            "verdicts": [dict(v) for v in self.verdicts],
            "tone_scope": {k: (dict(v) if isinstance(v, dict) else v)
                           for k, v in self.tone_scope.items()},
            "luck_scope": {k: dict(v) if isinstance(v, dict) else v
                           for k, v in self.luck_scope.items()},
            "xi_ji": {k: (list(v) if isinstance(v, (list, tuple))
                          else (dict(v) if isinstance(v, dict) else v))
                      for k, v in self.xi_ji.items()},
            "provenance": self.provenance,
        }
