#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Golden Replay Runner (V2 E6 — Cross-Version Regression)

对每个引擎的 Golden Set 执行重放，输出 LOAD/EXECUTE/结果统计。
用途: 任何算法变更后运行本脚本, Golden 结果差异必须分类为 EXPECTED_CHANGE / REGRESSION。

V2规范 §21: 禁止"新版本结果不同, 所以新版本就是对的"。
Expected Change 必须: 说明原因 + 更新证据 + 更新版本 + 更新Golden + 记录裁决。

用法:
    python scripts/golden_replay.py              # 重放全部引擎
    python scripts/golden_replay.py --engine ziwei   # 单引擎
    python scripts/golden_replay.py --snapshot    # 记录当前基线(变更前)
    python scripts/golden_replay.py --check       # 对比基线(变更后)
"""
import json
import sys
import hashlib
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

GOLDEN_SETS = {
    "ziwei": "cases/golden/ziwei_golden_set.json",
    "meihua": "cases/golden/meihua_golden_set.json",
    "huangli": "cases/golden/huangli_golden_set.json",
    "yijing": "cases/golden/yijing_golden_set.json",
    "blind": "cases/golden/blind_engine_snapshot.json",
    "ziping": "cases/golden/ziping_golden_set.json",
}
SNAPSHOT_PATH = ROOT / "cases" / "baselines" / "golden_replay_baseline.json"


def _canon(o):
    """深度规范化(消除set/PYTHONHASHSEED顺序噪声) — 与cross_engine_baseline同源."""
    if isinstance(o, dict):
        return {k: _canon(v) for k, v in sorted(o.items(), key=lambda kv: str(kv[0]))}
    if isinstance(o, (list, tuple)):
        items = [_canon(x) for x in o]
        if items and all(isinstance(x, (str, int, float)) for x in items):
            return sorted(items, key=lambda x: str(x))
        return items
    if isinstance(o, (set, frozenset)):
        return sorted(str(x) for x in o)
    return o


def _hash(obj) -> str:
    def default(o):
        if isinstance(o, (set, frozenset)):
            return sorted(str(x) for x in o)
        if hasattr(o, "to_dict"):
            return _canon(o.to_dict())
        if hasattr(o, "__dict__"):
            return _canon(o.__dict__)
        return str(o)
    s = json.dumps(_canon(obj), default=default, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _load_cases(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d.get("cases", [])


def _time_index_to_hour24(ti) -> int:
    """时辰序号 0–12 → 24h 时钟（紫微 golden 集字段语义，见下）。

    `cases/golden/ziwei_golden_set.json` 的 `input.birth_hour` 是**时辰序号**
    （0=早子 … 11=亥 … 12=晚子），因为该数据集生成时直接把它当 iztro timeIndex
    传给 `bySolar`。而生产适配器 `ZiweiSolarAdapter` 按 **24h 时钟** 解析后再转
    timeIndex。若直接把序号当小时喂进去，每个案例会系统性偏 1–2 个时辰
    （2026-11-04 审计实录：80 案中 68 案命宫错位）。此处做显式换算，口径为
    h = 2ti − 1（ti≥1），ti=0→0（早子）、ti=12→23（晚子）。
    """
    ti = int(ti)
    if ti <= 0:
        return 0
    if ti >= 12:
        return 23
    return 2 * ti - 1


def _exec_case(engine: str, case: dict):
    """执行单案例, 返回结果对象(异常则抛出). 适配各引擎Golden Set的实际input schema."""
    inp = case.get("input", case)
    if engine == "ziwei":
        from tongshu.engines.ziwei_adapter import ZiweiSolarAdapter
        y = inp.get("year", inp.get("birth_year"))
        m = inp.get("month", inp.get("birth_month"))
        dd = inp.get("day", inp.get("birth_day"))
        if "birth_hour" in inp:
            # golden 集字段 = 时辰序号，必须换算为 24h 时钟
            h = _time_index_to_hour24(inp["birth_hour"])
        else:
            h = inp.get("hour")
        return ZiweiSolarAdapter().compute(y, m, dd, h, inp.get("gender", "male"))
    if engine == "meihua":
        from tongshu.engines.meihua import cast_by_time, cast_by_numbers
        if "upper_num" in inp or "upper_number" in inp:
            return cast_by_numbers(inp.get("upper_num", inp.get("upper_number")),
                                   inp.get("lower_num", inp.get("lower_number", 1)))
        y = inp.get("year", inp.get("birth_year"))
        m = inp.get("month", inp.get("birth_month"))
        dd = inp.get("day", inp.get("birth_day"))
        h = inp.get("hour", inp.get("birth_hour"))
        return cast_by_time(y, m, dd, h)
    if engine == "huangli":
        from datetime import date as _date
        from tongshu.engines.huangli_engine import HuangliEngine
        if "date" in inp:
            ds = inp["date"]
            y, m, dd = (int(x) for x in ds.split("-"))
            return HuangliEngine().get_day(_date(y, m, dd))
        if "ganzhi" in inp:
            # 干支锚点查询类案例 → 返回干支本身作为可重放占位(确定性)
            return {"ganzhi_query": inp["ganzhi"]}
        y, m, dd = inp["year"], inp["month"], inp["day"]
        return HuangliEngine().get_day(_date(y, m, dd))
    if engine == "yijing":
        from tongshu.engines.yi.hexagram_symbol import get_hexagram_symbol
        name = inp.get("hexagram_name") or inp.get("name")
        if name:
            return get_hexagram_symbol(name)
        # 负向/特殊查询类案例(空卦名/ganzhi/line_position等) → 占位结果保持可重放
        special_keys = {"line_position", "check_all", "check_format", "hexagram_names"}
        if special_keys & set(inp.keys()):
            if inp.get("check_all") or inp.get("check_format"):
                from tongshu.engines.yi.hexagram_symbol import SIXTY_FOUR_MAP
                return {str(k): get_hexagram_symbol(v) if isinstance(v, str) else str(v)
                        for k, v in list(SIXTY_FOUR_MAP.items())[:64]}
            if "hexagram_names" in inp:
                return {n: get_hexagram_symbol(n) for n in inp["hexagram_names"] if n}
            return {"negative_case": True, "input": {k: str(v) for k, v in inp.items()}}
        raise ValueError(f"yijing case input unsupported: {list(inp.keys())}")
    if engine == "blind":
        from tongshu.engines.blind_bazi_engine import compute_blind_bazi
        return compute_blind_bazi(
            (inp.get("birth_year", inp.get("year")),
             inp.get("birth_month", inp.get("month")),
             inp.get("birth_day", inp.get("day")),
             inp.get("birth_hour", inp.get("hour"))),
            inp.get("gender", "male"),
        )
    if engine == "ziping":
        from tongshu.engines.bazi_engine import BaziEngine
        from tongshu.reasoning.ziping_bridge import run_ziping_judgment, synthesis_to_dict
        chart = BaziEngine().compute((
            inp.get("birth_year", inp.get("year")),
            inp.get("birth_month", inp.get("month")),
            inp.get("birth_day", inp.get("day")),
            inp.get("birth_hour", inp.get("hour")),
        ))
        synth = run_ziping_judgment(chart)
        d = synthesis_to_dict(synth)
        # 剥离运行时时间戳(同cross_engine_baseline处理)
        def _strip(o):
            if isinstance(o, dict):
                return {k: _strip(v) for k, v in o.items() if k != "created_at"}
            if isinstance(o, list):
                return [_strip(x) for x in o]
            return o
        return _strip(d)
    raise ValueError(f"unknown engine: {engine}")


def replay_engine(engine: str) -> dict:
    path = ROOT / GOLDEN_SETS[engine]
    if not path.exists():
        return {"engine": engine, "error": f"golden set missing: {path}"}
    cases = _load_cases(path)
    loaded = executed = 0
    errors = []
    case_hashes = []
    for i, case in enumerate(cases):
        loaded += 1
        try:
            r = _exec_case(engine, case)
            executed += 1
            case_hashes.append(_hash(r))
        except (TypeError, ValueError) as e:
            # 负向案例(无效输入)的预期异常 — 记录异常类型本身为确定性hash输入
            desc = str(case.get("description") or case.get("category") or "")
            note = str(case.get("note") or "")
            if any(w in desc for w in ("负向", "负校验", "negative", "invalid")) or "小数" in note:
                executed += 1
                case_hashes.append(_hash({"expected_exception": type(e).__name__, "msg": str(e)[:40]}))
            else:
                errors.append(f"case[{i}]: {type(e).__name__}: {str(e)[:80]}")
        except Exception as e:
            errors.append(f"case[{i}]: {type(e).__name__}: {str(e)[:80]}")
    # 引擎整体hash = 各案例hash串接再hash(顺序敏感, 反映案例集与结果)
    engine_hash = _hash(case_hashes) if case_hashes else "EMPTY"
    return {
        "engine": engine,
        "total": loaded,
        "executed": executed,
        "errors": errors[:5],
        "engine_hash": engine_hash,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=None, help="single engine name")
    ap.add_argument("--snapshot", action="store_true", help="write replay baseline")
    ap.add_argument("--check", action="store_true", help="compare against baseline")
    args = ap.parse_args()

    engines = [args.engine] if args.engine else list(GOLDEN_SETS)
    results = {e: replay_engine(e) for e in engines}

    print("=" * 62)
    print("V2 E6 Golden Replay — Cross-Version Regression")
    print("=" * 62)
    if args.snapshot:
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(
            json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"Baseline snapshot written: {SNAPSHOT_PATH}")
    for e, r in results.items():
        if "error" in r and "engine_hash" not in r:
            print(f"  {e:<10} : ERROR {r['error']}")
            continue
        mark = "OK" if r["executed"] == r["total"] else "PARTIAL"
        print(f"  {e:<10} : LOAD {r['total']}, EXECUTE {r['executed']}/{r['total']} [{mark}]  hash={r['engine_hash']}")
        for err in r["errors"]:
            print(f"      - {err}")
    if args.check:
        if not SNAPSHOT_PATH.exists():
            print("FAIL: baseline 不存在, 先运行 --snapshot")
            sys.exit(1)
        base = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        print("-" * 62)
        dirty = False
        for e in results:
            old = base.get(e, {}).get("engine_hash")
            new = results[e].get("engine_hash")
            if old != new:
                dirty = True
                print(f"  {e:<10} : {old}  ->  {new}   CHANGED")
        if dirty:
            print("FAIL: Golden 结果变化 — 按 V2 §21 分类: EXPECTED_CHANGE(须5步记录) 或 REGRESSION(修复)")
            sys.exit(1)
        print("PASS: 全部 Golden Replay 结果与基线一致")


if __name__ == "__main__":
    main()
