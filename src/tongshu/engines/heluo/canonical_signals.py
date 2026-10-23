# -*- coding: utf-8 -*-
"""平台信号出口（canonical_signals.py）。

**为什么有这个模块**
------------------

主仓早就有河洛→信号的消费契约，但**从未被喂过数据**：

* `D:\\shuntian\\src\\tongshu\\pipeline_stages\\compute_stage.py:166-168`
  把 `heluo_result` 置为 None（河洛已拆为独立包，主链主动断开）；
* `D:\\shuntian\\src\\tongshu\\signal\\adapters\\__init__.py:188-247` 的
  `HeluoAdapter` 期望河洛侧产出如下 **dict 形状**，再交给
  `D:\\shuntian\\src\\tongshu\\signal\\normalizer.py:120-177` 的
  `normalize_heluo()` 归一化（卦+爻 → 信号；`shi` 文本含「吉/亨/利」→
  POSITIVE，含「凶/不利/吝」→ NEGATIVE，否则 NEUTRAL）：

  ```
  {'gua': str, 'yao': int, 'position': str,
   'shi': str, 'strength': float, 'temporal_scope': dict}
  ```

本模块**按该既有契约**产出信号项：主链一旦把 `heluo_result` 回灌，
河洛侧不需要再改代码即可被消费。这正是此前「四个解读层模块零生产消费者」
的**出口落点**（平台侧缺的是回灌，不是河洛侧的字段）。

**边界（不做的事）**
--------------------

* **不发明事件本体 id**：主仓 17 类 USO 事件本体不在本包内，故只产出适配器
  契约要求的六个字段 + 少量可追溯附加字段（平台适配器会忽略附加字段）。
* **不臆造强度**：`strength` 沿用平台默认 0.5
  （`adapters/__init__.py:232-237`），并在字段里注明来源。
* **不判定方向**：吉凶方向由平台 `normalize_heluo` 按文本关键词判定；
  本包只给**原文**（爻辞 + 原典叶吉/不叶断语），不替平台下结论。
* 卦名一律用引擎内部全名（如「风火家人」），爻位用 1..6 的整数 +
  爻名（如「九五」），两者都可回查 `guajie` 的 64 卦逐爻数据。
"""
from __future__ import annotations

from typing import Any

__all__ = ["build_platform_signals", "YAO_POSITION_INDEX"]

#: 爻名 → 爻位序号（1..6，初爻为 1）
YAO_POSITION_INDEX: dict[str, int] = {
    "初": 1, "二": 2, "三": 3, "四": 4, "五": 5, "上": 6,
}

#: 平台适配器默认强度（`signal/adapters/__init__.py:232-237`）——本包不建模强度
_PLATFORM_DEFAULT_STRENGTH = 0.5


def _yao_index(yao_name: str) -> int:
    """从爻名取爻位序号 1..6；取不到返回 0。

    爻名有两种写法：**初爻/上爻在前**（初九、上六），**二三四五爻在中间**
    （九二、六三、九五）—— 故不能一律用前缀匹配。
    """
    name = (yao_name or "").strip()
    if not name:
        return 0
    if name.startswith("初"):
        return 1
    if "上" in name:
        return 6
    for token in ("二", "三", "四", "五"):
        if token in name:
            return YAO_POSITION_INDEX[token]
    return 0


def _dispute_text(yao: dict | None) -> str:
    """拼出该爻的**原文**断语（爻辞 + 叶吉/不叶断语），供平台按关键词判方向。

    只取原典文本，不做吉凶判定 —— 方向由平台 `normalize_heluo` 判。
    """
    if not yao:
        return ""
    parts = [yao.get("ci") or "", yao.get("ye") or "", yao.get("buye") or ""]
    return "；".join(p for p in parts if p)


def _signal(gua: str, yao_name: str, shi: str, scope: dict, layer: str) -> dict:
    return {
        # —— 平台适配器契约字段（adapters/__init__.py:203-211）——
        "gua": gua,
        "yao": _yao_index(yao_name),
        "position": yao_name,
        "shi": shi,
        "strength": _PLATFORM_DEFAULT_STRENGTH,
        "temporal_scope": scope,
        # —— 可追溯附加字段（平台忽略）——
        "layer": layer,
        "source_engine": "Heluo",
        "strength_source": "platform_default(0.5)：河洛侧未建模强度",
    }


def build_platform_signals(result: Any) -> list[dict]:
    """从河洛计算结果产出平台可消费的信号项列表。

    参数
    ----
    result: ``HeluoResult``（或带 ``guajie`` 字典的等价对象）。

    返回
    ----
    ``list[dict]``：每项符合平台 ``HeluoAdapter`` 期望的 dict 形状；
    没有对应判词时不产出该项（**宁缺勿造**）。
    """
    gj = getattr(result, "guajie", None)
    if not gj:
        return []
    if not isinstance(gj, dict):
        try:
            gj = gj.to_dict()
        except AttributeError:
            return []

    out: list[dict] = []
    year = gj.get("liunian_year")

    # ① 流年（周期层）
    gua = gj.get("liunian_hexagram") or ""
    yao = gj.get("liunian_yao") or {}
    if gua and yao.get("yao"):
        out.append(_signal(
            gua, yao.get("yao", ""), _dispute_text(yao),
            {"start_year": year, "end_year": year, "granularity": "YEARLY"},
            "CYCLE_CONTEXT"))

    # ② 流月（日激活层）
    gua = gj.get("liuyue_hexagram") or ""
    yao = gj.get("liuyue_yao") or {}
    if gua and yao.get("yao"):
        scope: dict[str, Any] = {"start_year": year, "end_year": year,
                                  "granularity": "MONTHLY"}
        lunar = gj.get("liuri_lunar") or {}
        solar_date = lunar.get("solar_date") or ""
        if len(solar_date) >= 7:
            scope["start_month"] = int(solar_date[5:7])
            scope["end_month"] = int(solar_date[5:7])
        out.append(_signal(gua, yao.get("yao", ""), _dispute_text(yao),
                            scope, "DAILY_ACTIVATION"))

    # ③ 流日（日激活层）
    gua = gj.get("liuri_hexagram") or ""
    yao = gj.get("liuri_yao") or {}
    if gua and yao.get("yao"):
        scope = {"start_year": year, "end_year": year, "granularity": "DAILY"}
        lunar = gj.get("liuri_lunar") or {}
        solar_date = lunar.get("solar_date") or ""
        if len(solar_date) >= 10:
            scope["start_day"] = int(solar_date[8:10])
            scope["end_day"] = int(solar_date[8:10])
        out.append(_signal(gua, yao.get("yao", ""), _dispute_text(yao),
                            scope, "DAILY_ACTIVATION"))

    # ④ 本命（基线层）：先天卦 + 元堂爻，取该爻原典爻辞
    # ⚠ 2026-10-24 第三轮审计修：原实现读 `benming.get("prenatal") or
    #   benming.get("gua")` 与 `benming.get("yuantang")` —— 但判词层
    #   `compose_guajie` 落的键是 {"hexagram", "gua_ci", "gua_ci_jingyi",
    #   "gua_ci_shiyi", "lines", "lines_jingyi", "lines_shiyi"}，
    #   **这三个键一个都不存在** ⇒ gua/yt 恒为 "" ⇒ `if gua and yt` 恒假
    #   ⇒ **BASELINE 层永不产出**，且无任何痕迹。
    #   而守卫 tests/heluo/test_heluo_canonical_signals.py 只断言
    #   `layers ⊆ {BASELINE, CYCLE_CONTEXT, DAILY_ACTIVATION}`（子集），
    #   永不断言 BASELINE **存在** ⇒ 回灌后基线层凭空消失，无人察觉。
    #
    #   修法：
    #   ① 卦名取 `benming["hexagram"]`（判词层实际落的键）；
    #   ② 元堂爻名本判词层 benming 里**没有** → 从 result 取
    #      （result.yuantang.yuantang 形如「六四」「初六」），
    #      **不改公开签名**（`build_platform_signals(result)`），
    #      直接从传入的 result 上取，不新增必填参数。
    benming = gj.get("benming") or {}
    gua = benming.get("hexagram") or benming.get("prenatal") or benming.get("gua") or ""
    _yt_obj = getattr(result, "yuantang", None)
    yt = (getattr(_yt_obj, "yuantang", "") or "").strip()
    if gua and yt:
        try:
            from .guajie import query_yao_duan
            from .numbers import short_hexagram_name
            yao_duan = query_yao_duan(short_hexagram_name(gua) or gua, yt)
        except Exception:
            yao_duan = None
        if yao_duan is not None:
            shi = "；".join(p for p in (yao_duan.ci, yao_duan.ye, yao_duan.buye) if p)
            out.append(_signal(gua, yt, shi,
                                {"granularity": "YEARLY"}, "BASELINE"))

    return out
