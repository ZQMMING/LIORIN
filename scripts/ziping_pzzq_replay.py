"""子平用神真值量具：以《子平真诠》原典 12 案的四柱直接回放 p0 engines 线。

度量口径
  - 输入：原典案例的四柱（全部为合法干支组合，避免 G-P03 拒斥）；
  - 输出：production_entry 的格局、用神层状态、主药五行；
  - 真值：案例原文明确给出的用神五行（沈孝瞻断语），逐案附 verbatim。

用途：把「用神算得对不对」变成可复现数字（当前 10/12），并登记不一致案的口径冲突。
运行：python scripts/ziping_pzzq_replay.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from engines.production_entry import (  # noqa: E402
    FrozenCanonicalBaziChart,
    production_entry,
)

CASES = [
    ("pzzq-001", ["癸未", "辛酉", "甲申", "丙寅"], "火", "官多同煞，以丙火制官为用"),
    ("pzzq-002", ["戊子", "癸亥", "庚寅", "戊寅"], "土", "泄气太重，以戊土扶身制伤为用"),
    ("pzzq-003", ["丁卯", "丙午", "丙子", "壬辰"], "水", "煞刃格，以煞制刃为用"),
    ("pzzq-004", ["乙酉", "甲申", "丁巳", "庚戌"], "金", "以庚劈甲引丁为用"),
    ("pzzq-005", ["辛酉", "丙申", "庚子", "丙戌"], "火", "煞刃格，合一留一（丙煞）"),
    ("pzzq-006", ["丙子", "壬辰", "壬申", "乙巳"], "木", "日元太旺，辰中乙木余气透干，用以泄秀"),
    ("pzzq-007", ["戊辰", "甲寅", "丁卯", "己酉"], "金", "印星太旺，取财损印为用"),
    ("pzzq-008", ["辛卯", "丁酉", "庚午", "丙子"], "火", "煞刃格，丁火制辛为用"),
    ("pzzq-009", ["癸巳", "丁巳", "丁卯", "丙午"], "水", "日元太旺，取年上癸水抑制为用"),
    ("pzzq-010", ["丁卯", "癸丑", "丙申", "戊子"], "火", "水旺火弱，用劫帮身为用神"),
    ("pzzq-011", ["己卯", "丁丑", "癸丑", "乙卯"], "木", "月令七煞透干，取食神制煞为用"),
    ("pzzq-012", ["壬寅", "戊申", "丙寅", "癸巳"], "水", "合官留煞（去煞留官）"),
    ("pzzq-013", ["甲子", "丁卯", "己亥", "戊辰"], "火", "甲己合而间丁, 所谓以印化官也(杨增新)"),
    ("pzzq-014", ["戊戌", "甲子", "己巳", "戊辰"], "木", "月令偏财生官, 劫财重重, 用官制劫护财"),
    ("pzzq-015", ["戊寅", "己未", "甲寅", "乙亥"], "土", "甲用己财; 甲己相合, 己土之财, 专向日主也"),
    ("pzzq-016", ["庚午", "乙酉", "甲子", "乙亥"], "金", "两乙合庚, 仍作合煞留官, 无减福也(高太尉)"),]

# 已知口径冲突（不计入断言分母，但仍打印）：
#  - pzzq-002：V7.183 从儿格印根门控 / V7.184 泄气太重格体豁免修正后已命中（2026-11-09）；
#  - pzzq-010：p0 走源1病药取土，沈取劫帮身，属病药与格用神优先级之外的断法差异。
#  - pzzq-017 朱有卿(癸巳 壬戌 乙巳 戊寅): 财格身弱, 沈云「戊癸合而间乙, 惟其不合,
#    故财局可以用印」(PZZQ L486)+「伤官暗藏而旺, 土燥木枯, 非用印不可」(L3351);
#    引擎表取官杀(配合级: 印为药 vs 官杀).
#  - pzzq-019 钜商王某(癸酉 癸亥 戊子 丁巳): 财格(两癸合戊, 财向日主), 沈云
#    「为财格用禄比…时逢归禄」「以劫护印分为财用」(L543/L3353) -> want=火(戊禄在巳);
#    引擎 V7.191 日主合财规则取财(水). 与 pzzq-015(甲用己财, 单财透合日主 -> 用财 HIT)
#    同机制异裁: 019 双财争合+归禄在时+印(丁)可护 -> 禄比分财; 015 单财专向 -> 用财.
#    判据候选: 财透数(单/双)+禄刃在支+印透可护 —— 三因子配合级, 未见单句明文, 不强判.
#  - pzzq-018 从势: 沈云「己土虽通根月令, 而见木之势盛, 即从木(从势无情义)」; 引擎从格判据
#    要求日主无本气根, 「通根月令仍从」阈值未及(gap 登记, 待立项).
#  - pzzq-019 钜商王某: 见上方详细登记(判据候选: 财透数+禄刃+印护 三因子配合级).
#  - pzzq-020 朱家宝: 沈徐注「朱造 印格用食」; 引擎病药判印太重取财损印(印重两说: 财损印 vs 食泄秀).
#  - pzzq-021 调候案: 沈徐注「丙火调候为用」属调候口径(引擎源2 格用神优先, 与调候两轨).
KNOWN_CONFLICTS = {"pzzq-010", "pzzq-017", "pzzq-018", "pzzq-019", "pzzq-020", "pzzq-021"}
MIN_COVERAGE = 10


def run(verbose: bool = True) -> int:
    hit = 0
    rows = []
    for cid, pillars, want, why in CASES:
        pl = {pos: [p[0], p[1]] for pos, p in zip(("year", "month", "day", "hour"), pillars)}
        result = production_entry(FrozenCanonicalBaziChart(pillars=pl))
        facts = result.get("engine_result") or {}
        yy = ((result.get("zhenglun") or {}).get("yongyao") or {})
        pm = yy.get("primary_medicine") or {}
        got = pm.get("wuxing") or ""
        ge = (facts.get("ge_cheng") or {}).get("ge") or ""
        ok = got == want
        hit += ok
        rows.append((cid, pillars, ge, want, got, yy.get("state"), pm.get("kind") or "", ok, why))
        if verbose:
            print(f"{cid} {' '.join(pillars)} ge={ge or '-':<10} want={want} "
                  f"got={got or '-':<2} state={yy.get('state')} kind={pm.get('kind') or '-':<12} "
                  f"{'HIT' if ok else 'MISS'} | {why}")
    if verbose:
        n_assert = len([c for c in CASES if c[0] not in KNOWN_CONFLICTS])
        print(f"coverage {hit}/{n_assert} (known conflicts: {sorted(KNOWN_CONFLICTS)})")
    return hit


def main() -> int:
    hit = run(verbose=True)
    return 0 if hit >= MIN_COVERAGE else 1


if __name__ == "__main__":
    raise SystemExit(main())
