"""Whole original bike core + original terrain on extracted Warm Up.
Recorded control schedule is a test input, not an original replay.
"""
import json,pathlib,struct,math
from dataclasses import replace
from verify_terrain import TerrainOracle
from verify_head import setup_tls
from physics import *
from bike import *
from gameplay import spawn
from terrain import Terrain
from collision import contact_step
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
o=TerrainOracle();setup_tls(o)
def silence(u,a,s,d):o.ret()
o.u.hook_add(UC_HOOK_CODE,silence,begin=0x14010e010,end=0x14010e010)
level=json.load(open(pathlib.Path(__file__).with_name('original-world.json')))['levels'][0]
t=Terrain.polygons(level['polygons']);o.build(t.edges);b=spawn(level)
for off,bb in [(0,b.body),(0x68,b.wheel1),(0xd0,b.wheel2)]:
 for field,v in [(0x20,bb.angle),(0x28,bb.omega),(0x30,bb.radius),(0x38,bb.mass),(0x40,bb.inertia)]:o.d(o.B+off+field,v)
 o.vec(o.B+off+0x48,bb.p);o.vec(o.B+off+0x58,bb.v)
o.vec(o.B+0x158,b.head_position);o.vec(o.B+0x168,b.head_velocity)
# cbf20 already initialized flags and volt state.
def pack(bs,hp):return [[*x.p,x.angle,x.omega,*x.v] for x in bs]+[[*hp]]
samples=[];error=0.;steps=0;death=None;contacts_seen=0
for i in range(1600):
 time=i*.0055;gas=True;brake=False;neg=False;pos=False
 o.call(0x1400ea7f0,ints=(o.B,0,0,int(gas)),floats={1:time,2:.0055},stack=(int(brake),int(neg),int(pos)))
 def wheel_step(w,f,torque,dt):
  global contacts_seen
  points=t.contacts(w.p,w.radius);contacts_seen+=len(points)
  return contact_step(w,f,torque,dt,points)
 b=bike_step(b,time,.0055,gas,brake,neg,pos,wheel_step)
 native=o.state();original=[Body(**native[k]) for k in ['body','wheel1','wheel2']]
 pa=pack(original,o.vec(o.B+0x158));pb=pack([b.body,b.wheel1,b.wheel2],b.head_position)
 for aa,bb in zip(pa,pb):
  for x,y in zip(aa,bb):
   error=max(error,abs(x-y));assert math.isclose(x,y,rel_tol=1e-8,abs_tol=1e-8),(i,error,x,y)
 steps+=1
 if i%4==0:samples.append({'t':(i+1)*.0055,'original':pa,'rebuilt':pb})
 center=head_collision_center(b.head_position,b.body.angle,b.flipped)
 if t.contacts(center,.238):death=(i+1)*.0055;break
result={'level':'Warm Up','steps':steps,'wheel_contacts_seen':contacts_seen,'max_abs_error':error,'head_collision_time':death,'scope':'Complete original bike core and original terrain grid/query; host sin/cos, TLS guards, heap, memset, sound substituted; fixed gas test schedule'}
print(json.dumps(result,indent=2));pathlib.Path(__file__).with_name('world-ride-verification.json').write_text(json.dumps(result,indent=2))
pathlib.Path(__file__).with_name('warm-up-ride.json').write_text(json.dumps({'result':result,'samples':samples},separators=(',',':')))
