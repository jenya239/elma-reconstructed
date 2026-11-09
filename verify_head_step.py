import random,math,json,pathlib
from oracle import Oracle
from verify_head import setup_tls
from physics import Body
from head import head_step
r=random.Random(674);o=Oracle();o.initialize();setup_tls(o);error=0
for i in range(2000):
    a=r.uniform(-8,8);f=(math.cos(a),math.sin(a));up=(-f[1],f[0]);flip=bool(i&1)
    b=Body((r.uniform(-10,10),r.uniform(-10,10)),(r.uniform(-10,10),r.uniform(-10,10)),a,r.uniform(-15,15),r.uniform(10,250),60,.3)
    hp=(b.p[0]+r.uniform(-1,1),b.p[1]+r.uniform(-1,1));hv=(r.uniform(-5,5),r.uniform(-5,5));g=[(0,1),(0,-1),(-1,0),(1,0)][i%4];dt=r.uniform(0,.0055)
    o.vec(o.B+0x48,b.p);o.vec(o.B+0x58,b.v);o.d(o.B+0x28,b.omega);o.d(o.B+0x38,b.mass);o.q(o.B+0x148,int(flip));o.vec(o.B+0x158,hp);o.vec(o.B+0x168,hv)
    o.vec(o.AUX,g);o.vec(o.AUX+16,f);o.vec(o.AUX+32,up)
    o.call(0x1400ce460,ints=(o.B,o.AUX,o.AUX+16,o.AUX+32),stack=(dt,))
    ep,ev=head_step(b,hp,hv,g,f,up,dt,flip);got=(*o.vec(o.B+0x158),*o.vec(o.B+0x168));expected=(*ep,*ev)
    for x,y in zip(got,expected):
        error=max(error,abs(x-y));assert math.isclose(x,y,rel_tol=1e-11,abs_tol=1e-11),(i,got,expected)
result={'head_step_cases':2000,'max_abs_error':error,'function':'0x1400ce460','scope':'Full rider clamp and spring integration, no head terrain collision'}
print(json.dumps(result,indent=2));pathlib.Path(__file__).with_name('head-step-verification.json').write_text(json.dumps(result,indent=2))
