import math
cx,cy=94.84,94.41;ro,rm,dr,sw=92.22,30.38,2.76,0.43;sc="#B6B6B7"
L=[]
L.append('<?xml version="1.0" encoding="UTF-8"?>')
L.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 189.29 189.23" width="100%" height="100%">')
L.append('  <defs><style type="text/css">')
L.append('.ring{fill:none;stroke:'+sc+';stroke-width:'+str(sw)+'}')
L.append('.white{fill:#FEFEFE;stroke:'+sc+';stroke-width:'+str(sw)+'}')
L.append('.black{fill:#332C2B;stroke:'+sc+';stroke-width:'+str(sw)+'}')
L.append('  </style></defs>')
L.append('  <circle class="ring" cx="%.2f" cy="%.2f" r="%.2f"/>'%(cx,cy,ro))
L.append('  <circle class="ring" cx="%.2f" cy="%.2f" r="%.2f"/>'%(cx,cy,rm))
L.append('  <circle class="white" cx="%.2f" cy="%.2f" r="%.2f"/>'%(cx,cy,dr))
ic=['white','black','white','black','white','black','white','black']
for i in range(8):
    a=math.radians(i*45);x=cx+rm*math.sin(a);y=cy-rm*math.cos(a)
    L.append('  <circle class="%s" cx="%.2f" cy="%.2f" r="%.2f"/>'%(ic[i],x,y,dr))
n=35;step=360.0/n
for i in range(n):
    a=math.radians(i*step);x=cx+ro*math.sin(a);y=cy-ro*math.cos(a)
    c='white' if(i==0 or i>=18) else 'black'
    L.append('  <circle class="%s" cx="%.2f" cy="%.2f" r="%.2f"/>'%(c,x,y,dr))
L.append('</svg>')
with open('D:/shuntian/hetu.svg','w',encoding='utf-8') as f:f.write('\n'.join(L))
print('Done',1+8+n,'dots W=%d B=%d'%(sum(1 for l in L if 'class="white"' in l),sum(1 for l in L if 'class="black"' in l)))
