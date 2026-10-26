# -*- coding: utf-8 -*-
"""Behaviour snapshot for the heluo engine — used to tell EQUIVALENT mutants
from REAL blind spots.

A mutation that survives the test suite is NOT automatically a blind spot:
defensive code (e.g. ``return ("", "")`` guarded by a caller's ``or ""``)
often has an equivalent mutant — the observable behaviour is unchanged.

So we compare a **behaviour snapshot** (deterministic JSON of the engine's
observable output on several fixed cases) between the baseline and the mutant:

  * output identical  ⇒ EQUIVALENT mutant (no blind spot; not a defect)
  * output differs    ⇒ REAL blind spot: behaviour changed, nobody noticed
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# ⚠ **自举**：让本脚本能从**任意目录**运行（不依赖 PYTHONPATH 已设好）。
#   原因：这是一个**工具**，用户会直接 `python tools/heluo/behaviour_snapshot.py`
#   来人工比对输出；若必须先设 PYTHONPATH 才能跑 ⇒ 极易被误判为「脚本坏了」。
#   ⇒ 找不到包时，把仓库的 ``src`` 加进 sys.path 再试一次。
if __package__ in (None, ""):
    _SRC = Path(__file__).resolve().parents[2] / "src"
    if _SRC.is_dir() and str(_SRC) not in sys.path:
        sys.path.insert(0, str(_SRC))

#: 固定的若干盘（覆盖不同路径：男/女、纯卦/杂卦、不同流月流日）
CASES = [
    ((1980, 6, 22, 10), "male", "2026-10-23"),
    ((1975, 11, 22, 1), "male", "2026-09-15"),
    ((1983, 11, 3, 12), "female", "2027-05-10"),
    ((1990, 3, 15, 14), "male", "2026-10-23"),
    ((1965, 8, 8, 8), "female", "2026-01-20"),
]


def _round(obj, n=6):
    """Round floats so the snapshot is stable across runs."""
    if isinstance(obj, float):
        return round(obj, n)
    if isinstance(obj, dict):
        return {str(k): _round(v, n) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if isinstance(obj, (list, tuple)):
        return [_round(v, n) for v in obj]
    return obj


def snapshot() -> dict:
    """Deterministic snapshot of the engine's observable behaviour.

    ⚠ **覆盖面决定结论的可信度**（2026-10-25 实测教训）：
      若某模块的产出**不在**快照里 ⇒ 该模块的变异会让快照输出**不变**
      ⇒ 被误判成「等价变异」⇒ **真盲区被静默掩盖**。
      实测踩过：``frozen_state`` 的 3 条变异全被误判成等价
      （``FrozenHeluoState`` 压根没进快照）。

    ⇒ 故本函数覆盖 **HeluoResult 的全部主要输出面**：
      数值（numbers）/ 元气（yuan_qi）/ 世代（era）/ 节候（seasonal）/
      卦象结构（structure）/ 运程（timeline）/ 判词（guajie）/
      解读层（interpretation）/ 冻结状态（frozen_state）/ 时间层判定。
    """
    from heluo_engine.adapter import HeluoAdapter
    from heluo_engine.engines.heluo.frozen_state import build_frozen_state
    from heluo_engine.engines.heluo.time_layer_judgment import (
        collect_dayun_judgment, collect_time_layer_judgments,
    )

    ad = HeluoAdapter()
    out = []
    for solar, gender, target in CASES:
        rec = {"case": "%s|%s|%s" % (solar, gender, target)}
        try:
            res = ad.compute(solar, gender=gender, target_date=target)
            rec["prenatal"] = res.prenatal.hexagram_name
            rec["postnatal"] = res.postnatal.hexagram_name
            rec["yuantang"] = res.yuantang.yuantang
            rec["target_date"] = res.target_date
            rec["hua_gong"] = (res.hua_gong.state.value if res.hua_gong else None)
            tj = [_j.to_dict() for _j in
                  collect_time_layer_judgments(res) + [collect_dayun_judgment(res)]]
            rec["time_layers"] = tj

            # ── 数值层（numbers）──
            n = res.numbers
            rec["numbers"] = {
                "tian_shu": getattr(n, "tian_shu", None),
                "di_shu": getattr(n, "di_shu", None),
                "tian_reduced": getattr(n, "tian_reduced", None),
                "di_reduced": getattr(n, "di_reduced", None),
                "details": list(getattr(n, "details", []) or []),
            }

            # ── 元气层（yuan_qi）──
            yq = res.yuan_qi
            rec["yuan_qi"] = None if yq is None else {
                "state": getattr(getattr(yq, "state", None), "value", None),
                "tian": getattr(yq, "tian_yuan_qi", None),
                "di": getattr(yq, "di_yuan_qi", None),
                "evidence": list(getattr(yq, "evidence", []) or []),
            }
            rec["yuan_qi_error"] = res.yuan_qi_error

            # ── 世代 / 节候 / 卦象结构 ──
            rec["era"] = res.era
            rec["era_source"] = res.era_source
            rec["birth_year"] = res.birth_year
            rec["birth_year_source"] = res.birth_year_source
            rec["seasonal_hexagram"] = res.seasonal_hexagram
            st = res.structure
            rec["structure"] = None if st is None else {
                "name": getattr(st, "name", None),
                "upper": getattr(st, "upper_gua", None),
                "lower": getattr(st, "lower_gua", None),
                "lines": list(getattr(st, "lines", []) or []),
                "ti_yong": getattr(st, "ti_yong", None),
                "sheng_ke": getattr(st, "sheng_ke", None),
                "hu_gua": getattr(st, "hu_gua", None),
                "cuo_gua": getattr(st, "cuo_gua", None),
                "zong_gua": getattr(st, "zong_gua", None),
            }

            # ── 运程层（timeline）──
            tl = res.timeline
            rec["timeline"] = None if tl is None else {
                "target_year_hexagram": getattr(tl, "target_year_hexagram", None),
                "yearly_hexagrams": [
                    {
                        "year": y.get("year"),
                        "hexagram": y.get("hexagram"),
                        "xingnian_yao_index": y.get("xingnian_yao_index"),
                        "dayun_seg_yuantang_index":
                            y.get("dayun_seg_yuantang_index"),
                        "months": [
                            {"month": m.get("month"), "name": m.get("name"),
                             "yue_yao_index": m.get("yue_yao_index")}
                            for m in (y.get("months") or []) if isinstance(m, dict)
                        ],
                    }
                    for y in (getattr(tl, "yearly_hexagrams", []) or [])
                    if isinstance(y, dict)
                ],
                "daily_hexagram": getattr(tl, "daily_hexagram", None),
            }

            # ── 判词层（guajie）──
            rec["guajie"] = res.guajie

            # ── 解读层（interpretation）──
            rec["interpretation"] = res.interpretation

            # ⚠ 2026-10-25 补：**冻结状态**（FrozenHeluoState）。
            #   为什么必须加：``frozen_state.build_frozen_state`` 是一条
            #   **独立于 adapter.compute 主链**的产物线，而快照原先
            #   完全没覆盖它 ⇒ 该模块的变异（如 ``return → None``）
            #   会让快照输出**不变** ⇒ 被误判成「等价变异」
            #   ⇒ **真盲区被静默掩盖**。
            #   实测（2026-10-25）：frozen_state 的 3 条变异全部被误判成等价。
            #   ⇒ 凡「模块产出对外可见」就必须进快照，否则该模块的盲区不可见。
            try:
                fs = build_frozen_state(res)
                rec["frozen_state"] = fs.to_dict() if fs is not None else None
            except Exception as exc:
                rec["frozen_state_error"] = "%s: %s" % (type(exc).__name__, exc)
        except Exception as exc:
            rec["error"] = "%s: %s" % (type(exc).__name__, exc)
        out.append(rec)
    return _round(out)


def main() -> int:
    data = snapshot()
    text = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)
    out_path = sys.argv[1] if len(sys.argv) > 1 else None
    if out_path:
        # 显式 UTF-8 写文件（避免 shell 重定向的编码问题）
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
