"""Compare the whole original physics core against its reconstructed composition."""
import random,math,json,pathlib,struct
from dataclasses import astuple
from oracle import Oracle
from verify_head import setup_tls
from physics import Body
from controls import VoltState
from bike import Bike,bike_step,head_collision_center
r=random.Random(876);o=Oracle();o.initialize();setup_tls(o);error=0

def write_body(addr,b):
    for off,val in [(0x20,b.angle),(0x28,b.omega),(0x30,b.radius),(0x38,b.mass),(0x40,b.inertia)]:o.d(addr+off,val)
    o.vec(addr+0x48,b.p);o.vec(addr+0x58,b.v)
for i in range(500):
    a=r.uniform(-3,3);f=(math.cos(a),math.sin(a));up=(-f[1],f[0])
    body=Body((2.75,3.6),(r.uniform(-3,3),r.uniform(-3,3)),a,r.uniform(-12,12),200,60.500000000000014,.3)
    def wheel(sign):return Body((body.p[0]+sign*.85*f[0]-.6*up[0]+r.uniform(-.05,.05),body.p[1]+sign*.85*f[1]-.6*up[1]+r.uniform(-.05,.05)),(r.uniform(-3,3),r.uniform(-3,3)),r.uniform(-4,4),r.uniform(-120,120),10,.32,.4)
    b=Bike(body,wheel(-1),wheel(1),(2.75+r.uniform(-.6,.6),3.6+r.uniform(-.6,.6)),(r.uniform(-3,3),r.uniform(-3,3)),VoltState(body.omega,bool(i&1),bool(i&2),.2,.3,1.1,-2.2),bool(i&4),i%4,bool(i&8),(.1,.2))
    gas=bool(i&16);brake=bool(i&32);neg=bool(i&64);pos=bool(i&128);time=r.uniform(0,1);dt=r.uniform(.0001,.0055)
    for off,bb in [(0,b.body),(.0 if False else 0x68,b.wheel1),(0xd0,b.wheel2)]:write_body(o.B+off,bb)
    o.q(o.B+0x148,int(b.flipped));o.q(o.B+0x150,b.gravity);o.q(o.B+0x17c,int(b.was_brake));o.d(o.B+0x180,b.locks[0]);o.d(o.B+0x188,b.locks[1]);o.vec(o.B+0x158,b.head_position);o.vec(o.B+0x168,b.head_velocity)
    o.u.mem_write(o.B+0x190,struct.pack('<ii',b.volt.negative_active,b.volt.positive_active))
    for off,v in [(0x198,.2),(0x1a0,.3),(0x1a8,1.1),(0x1b0,-2.2)]:o.d(o.B+off,v)
    o.call(0x1400ea7f0,ints=(o.B,0,0,int(gas)),floats={1:time,2:dt},stack=(int(brake),int(neg),int(pos)))
    expected=bike_step(b,time,dt,gas,brake,neg,pos)
    actual=[];desired=[]
    for name in ['body','wheel1','wheel2']:
        ob=o.state()[name];eb=getattr(expected,name);actual.extend([*ob['p'],*ob['v'],ob['angle'],ob['omega']]);desired.extend([*eb.p,*eb.v,eb.angle,eb.omega])
    actual.extend([*o.vec(o.B+0x158),*o.vec(o.B+0x168),*o.vec(o.B+0x138)])
    desired.extend([*expected.head_position,*expected.head_velocity,*head_collision_center(expected.head_position,expected.body.angle,expected.flipped)])
    for x,y in zip(actual,desired):
        error=max(error,abs(x-y));assert math.isclose(x,y,abs_tol=1e-10,rel_tol=1e-10),(i,actual,desired)
result={'full_core_cases':500,'max_abs_error':error,'function':'0x1400ea7f0','scope':'Full core, empty terrain query; all 4 gravity directions, gas/brake/volt/flip flags'}
print(json.dumps(result,indent=2));pathlib.Path(__file__).with_name('bike-verification.json').write_text(json.dumps(result,indent=2))
