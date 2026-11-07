import sys; sys.path.insert(0, ".")
from p0_v2.bazi_gate import paipan
# de_di patch 后: 中余气盘 de_di 应翻 True; f(strength_verdict) 不变(仍用 dm_ben_eff)
print("=== de_di patch AFTER: 4 盘 de_di/root_grade + strength_verdict ===")
for bz in ["丁未庚戌庚辰丙子", "丁酉癸卯丙辰丙申", "癸卯甲寅丁卯甲辰", "壬辰壬寅甲寅庚午"]:
    o = paipan(bz); lc = o.get("l3_contract") or {}
    sv = (lc.get("strength_verdict") or {}).get("value")
    print(f"  {bz} 日主{o.get('daymaster_element','?')}: de_di={lc.get('de_di')} "
          f"root_grade={lc.get('root_grade')} ling={lc.get('ling_state')} "
          f"dm_ben_eff={lc.get('dm_ben_eff')} sv={sv}")

# de_ling patch: 相 现在算得令
print("\n=== de_ling patch: '相' 现在算得令 (de_ling=True) ===")
for bz in ["丁未庚戌庚辰丙子", "癸卯甲寅丁卯甲辰"]:  # ling=相 的盘
    lc = paipan(bz).get("l3_contract") or {}
    print(f"  {bz} ling={lc.get('ling_state')} de_ling={lc.get('de_ling')}")

# 全量回归: de_di 下游 0 消费, 只翻字段; 数 100 案例 de_di 翻转数
import json
res = json.load(open("scripts/_c100_result.json", encoding="utf-8"))
from collections import Counter
flip = 0; sv_dist = Counter()
for r in res["rows"]:
    o = paipan(r["bazi"].replace(" ", ""))
    lc = o.get("l3_contract") or {}
    # de_di 翻转 = root_grade in (本,余) 但 dm_ben_eff==0 (旧 False 新 True)
    if lc.get("root_grade") in ("本", "余") and lc.get("dm_ben_eff") == 0:
        flip += 1
    sv_dist[(lc.get("strength_verdict") or {}).get("value")] += 1
print(f"\n=== 100 案例 de_di 翻转 + f 分布 (patch 后) ===")
print(f"  de_di 翻转(中余气有根): {flip} 盘")
print(f"  strength_verdict.value 分布: {dict(sv_dist)}")
