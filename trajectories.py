import pathlib,sys,json,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from physics import *
from oracle import Oracle
from verify_contact import ContactOracle
from dataclasses import replace

o=Oracle();o.initialize()
co=ContactOracle()
def put(a,b):
 for off,v in [(0x20,b.angle),(0x28,b.omega),(0x30,b.radius),(0x38,b.mass),(0x40,b.inertia)]:o.d(a+off,v)
 o.vec(a+0x48,b.p);o.vec(a+0x58,b.v)
def integrate(b,f,t,dt):
 put(o.B,b);o.vec(o.AUX,f);o.call(0x1400cdf50,ints=(o.B,o.AUX),floats={2:t,3:dt},stack=(0,))
 return replace(b,p=o.vec(o.B+0x48),v=o.vec(o.B+0x58),angle=o.d(o.B+0x20),omega=o.d(o.B+0x28))
def spring(b,w,rest,t):
 put(o.B,b);put(o.B+0x68,w);o.vec(o.AUX,(cos(b.angle),sin(b.angle)));o.vec(o.AUX+16,(-sin(b.angle),cos(b.angle)));o.d(o.AUX+96,t)
 o.call(0x1400ea220,ints=(o.B,o.B+0x68,o.AUX,o.AUX+16),stack=(*rest,o.AUX+32,o.AUX+48,o.AUX+64,o.AUX+96))
 return o.vec(o.AUX+32),o.vec(o.AUX+48),o.d(o.AUX+64)
def step(bodies,gas,fixed=False,original=False,ground=False):
 b,w1,w2=bodies
 t1,t2,a1,a2=wheel_torques(b,w1,w2,gas=gas)
 w1=replace(w1,angle=a1);w2=replace(w2,angle=a2)
 sf=spring if original else suspension
 def it(b,f,t,dt):
  if ground and b.p[1]<=b.radius:
   point=(b.p[0],0.)
   return co.step(b,f,t,dt,point) if original else one_contact_step(b,f,t,dt,point)
  return integrate(b,f,t,dt) if original else free_step(b,f,t,dt)
 f1,b1,tb1=sf(b,w1,(-.8500000000000001,-.6000000000000001),t1)
 f2,b2,tb2=sf(b,w2,(.8500000000000001,-.6000000000000001),t2)
 g=0 if fixed else -10.
 return [b if fixed else it(b,add(add(b1,b2),(0,b.mass*g)),tb1+tb2,.0055),it(w1,add(f1,(0,w1.mass*g)),t1,.0055),it(w2,add(f2,(0,w2.mass*g)),t2,.0055)]
def pack(bs):return [[*b.p,b.angle,b.omega,*b.v] for b in bs]
scenes=[]
for name,title,gas,fixed in [('fall','Свободное падение',False,False),('gas','Газ в воздухе',True,False),('spring','Подвеска · рама закреплена',False,True),('ground','Приземление и газ · ровная площадка',True,False)]:
 a=list(initial_bodies());b=list(initial_bodies())
 if fixed:
  a[1]=replace(a[1],p=add(a[1].p,(.15,-.25)));b=list(a)
 samples=[];worst=0
 for i in range(201):
  pa=pack(a);pb=pack(b)
  worst=max(worst,max(abs(x-y) for aa,bb in zip(pa,pb) for x,y in zip(aa,bb)))
  samples.append({'t':i*.0055,'original':pa,'rebuilt':pb})
  a=step(a,gas,fixed,True,name=="ground");b=step(b,gas,fixed,False,name=="ground")
 scenes.append({'id':name,'title':title,'samples':samples,'maxError':worst})
 print(name,'max state difference',worst,flush=True)
pathlib.Path(__file__).with_name('trajectories.json').write_text(json.dumps(scenes,separators=(',',':')))
