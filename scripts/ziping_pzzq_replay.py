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
    ("pzzq-016", ["庚午", "乙酉", "甲子", "乙亥"], "金", "两乙合庚, 仍作合煞留官, 无减福也(高太尉)"),
    ("pzzq-020", ["庚申", "乙酉", "癸未", "乙卯"], "木", "印格用食(朱家宝: 身印两旺用食伤泄; 财不透虚财无力 L543/L1146)"),
    ("pzzq-017", ["癸巳", "壬戌", "乙巳", "戊寅"], "水", "戊癸合而间乙, 惟其不合, 故财局可以用印(朱有卿 L486; V7.203 遥隔无禄刃->印)"),
    ("pzzq-019", ["癸酉", "癸亥", "戊子", "丁巳"], "火", "两癸合戊, 虽不以合论, 为财格用禄比, 时逢归禄(王某 L543; V7.203 争合归禄->禄)"),
    ("pzzq-021", ["己酉", "丙子", "戊辰", "癸亥"], "火", "丙火调候为用, 无如戊癸相合, 日主之情向财不向印(佩印×财专向->用印, V7.205)"),
]

# 已知口径冲突（不计入断言分母，但仍打印）：
#  - pzzq-002：V7.183 从儿格印根门控 / V7.184 泄气太重格体豁免修正后已命中（2026-11-09）；
#  - ★ V7.203 五合终裁判据层落地（2026-11-10 §二十六.3）: 017/019 收平入 CASES——
#    佩印合去三态(紧贴作合/间干克其配偶=制于势 L481/遥隔通月令禄刃仍合 L495 张耀曾
#    庚禄在申, 反证朱有卿 戊墓在戌+间乙克戊 L486) + 争合归禄(L541-543「两癸合戊, 虽
#    不以合论, 而终有合意。为财格用禄比…时逢归禄」); 004 张耀曾/015 甲用己财 locked 双锚保持。
#  - pzzq-018 从势(伍廷芳造): ★格层已收平(V7.207, 2026-11-11 §二十六.11)——徐注 L182
#    「己土虽通根月令, 而见木之势盛, 即从木」: 阴干从势通道落码 special_pattern(势盛=月令
#    财官/三合局+食伤当令·比劫党·通根·印通道[透被财合去→从门开] 六门), 018 → 从杀格
#    CONFIRMED/CHENG, 原典正反例锚全过(阎锡山/许世英 不从, 004/辛未 主路径不变)。
#    用神级仍登记配合级: 判词「从木」=格局定性非用神五行; engine 从杀格喜神=财(水,
#    PZZQ5000「从杀忌食伤, 财生煞顺旺势为喜」既有锚), 沈未亲证用神→不擅断, 保持 conflict。
#  - pzzq-020 朱家宝: 2026-11-10 V7.201 收平(CASES)。印重两说判别式=制药(财)透干/本气根
#    在→用财损印(pzzq-007 财坐酉本气亲证); 财不透无本气根而食伤透干或本气根在→用食泄
#    (朱家宝 财金不透, 食乙×2透+卯根, L1146「身印两旺, 用食伤泄」成句+L543 亲证)。
#    引擎落码: yongyao_resolve 印病加食伤泄边 + 制无透无本气根而泄有力时泄升主。
#  - pzzq-010 蔡孑民: 2026-11-10 V7.204 收平(CASES)。扶抑扶边判据(DTS L215「提纲食伤
#    财官太旺, 取年月时上印比为喜神」+PZZQ L971 伍朝枢用印/L975 蔡孑民用劫两案亲证):
#    身弱(得令得地双失)且病∈{官杀/食伤/财}→扶边(印/劫)升主, 透干有力者优先(丁劫透),
#    同档印主比辅。
#  - ★ V7.205 调候案收平（2026-11-10 §二十六.5）: 021 入 CASES——L530-531 亲证「丙火
#    调候为用, 无如戊癸相合, 日主之情, 向财不向印」: 戊癸合(财专向 V7.191)与佩印并存时
#    用神仍归印(L3341「孤财不贵, 佩印帮身, 即印取贵」+L3344「需要佩印, 必是身弱」),
#    合只是「用神之情不专」之瑕(L533); 印被财合去之佩印仍用财(张耀曾 004 V7.203 终裁)。
KNOWN_CONFLICTS = {"pzzq-018"}
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
