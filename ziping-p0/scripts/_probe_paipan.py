# -*- coding: utf-8 -*-
import sys, os, json
ROOT=r"D:/shuntian-ziping-p0"
sys.path.insert(0,ROOT)
sys.path=[p for p in sys.path if os.path.abspath(p)!=os.path.join(ROOT,"p0_v2")]
from p0_v2.bazi_gate import paipan
res=paipan("辛卯 丁酉 庚午 丙子")
print("paipan 返回类型:", type(res).__name__)
if isinstance(res,dict):
    print("顶层键:", list(res.keys()))
    for k,v in res.items():
        t=type(v).__name__
        extra=""
        if isinstance(v,dict): extra=" 子键="+str(list(v.keys())[:12])
        if isinstance(v,list): extra=f" [len{len(v)}]"
        print(f"  {k}: {t}{extra}")
