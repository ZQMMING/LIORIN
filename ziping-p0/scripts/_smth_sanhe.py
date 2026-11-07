ls=open(r"registries/source/raw/SMTH_三命通会_原文.md",encoding="utf-8",errors="ignore").read().splitlines()
out=[]
for i in range(2759,2810):
    t=ls[i].strip()
    if t: out.append("L%d %s"%(i+1,t[:80]))
print(chr(10).join(out[:60]))
print("== 1590-1600 ==")
for i in range(1589,1600):
    t=ls[i].strip()
    if t: print("L%d %s"%(i+1,t[:80]))
