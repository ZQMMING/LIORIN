import sys; sys.path.insert(0, ".")
from p0_v2.bazi_gate import paipan
import json
for bz in ["丁未庚戌庚辰丙子", "丁酉癸卯丙辰丙申", "癸卯甲寅丁卯甲辰", "壬辰壬寅甲寅庚午"]:
    o = paipan(bz)
    lc = o.get("l3_contract") or {}
    rwcf = (o.get("l0_fact") or {}).get("root_weight_class_facts") or {}
    print(f"{bz} 日主{o.get('daymaster_element','?')}: dm_ben_eff={lc.get('dm_ben_eff')} "
          f"root_grade={lc.get('root_grade')} ling={lc.get('ling_state')} de_di={lc.get('de_di')}")
    if rwcf:
        print(f"    root_weight_class_facts(含中余气): {json.dumps(rwcf, ensure_ascii=False)}")
