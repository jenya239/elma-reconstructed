"""Execute complete original e7fb0 tick, with real terrain/objects/FIFO/effects.
Host substitutes keyboard/config, allocation, CRT math, audio and replay sinks.
Turn edges use the original outer-loop fragment e8acc..e8b0e before each tick.
"""
import json,pathlib,struct,math
from oracle import bits,number
from verify_terrain import TerrainOracle
from verify_events import EventOracle
from verify_head import setup_tls
from session import Session
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
class SessionOracle(TerrainOracle):
 LEVEL=EventOracle.LEVEL;CONFIG=EventOracle.CONFIG;OBJECTS=EventOracle.OBJECTS
 i=EventOracle.i;setup=EventOracle.setup;queue=EventOracle.queue
 def __init__(self):
  super().__init__();setup_tls(self);self.u.mem_map(self.LEVEL,0x100000)
  self.q(0x140708920,self.LEVEL);self.q(0x1406cdf10,self.CONFIG);self.q(0x1407009e0,self.CONFIG)
  self.i(self.CONFIG+0x10918,77);self.i(self.CONFIG+0x108e0,14);self.keys={};self.recorded=[]
  self.KEYS=self.AUX+0x100;self.STATE=self.AUX+0x200;self.FINISH=self.AUX+0x400;self.DEAD=self.AUX+0x408
  self.u.mem_write(self.KEYS,struct.pack('<iiii',10,11,12,13))
  for a,cb in [(0x140016e50,self.key),(0x1400d4b00,self.config),(0x1404e3f48,self.noop),(0x1404e6016,self.exp),(0x14010e050,self.noop),(0x140132e30,self.noop),(0x14010c2b0,self.record),(0x1400e8b0e,self.turn_done)]:self.u.hook_add(UC_HOOK_CODE,cb,begin=a,end=a)
 def turn_done(self,u,a,s,d):u.reg_write(UC_X86_REG_RIP,self.STOP)
 def key(self,u,a,s,d):u.reg_write(UC_X86_REG_RAX,int(self.keys.get(u.reg_read(UC_X86_REG_RCX),False)));self.ret()
 def config(self,u,a,s,d):u.reg_write(UC_X86_REG_RAX,99);self.ret()
 def noop(self,u,a,s,d):self.ret()
 def exp(self,u,a,s,d):u.reg_write(UC_X86_REG_XMM0,bits(math.exp(number(u.reg_read(UC_X86_REG_XMM0)))));self.ret()
 def record(self,u,a,s,d):
  idx=self.i(u.reg_read(UC_X86_REG_RSP)+0x28)
  self.recorded.append((u.reg_read(UC_X86_REG_R8)&255,number(u.reg_read(UC_X86_REG_XMM3)),idx));self.ret()
 def reset(self,s):
  # setup resets heap; build afterwards so tree allocation does not overwrite grid.
  self.setup(s.objects);self.build(s.terrain.edges);self.u.mem_write(self.B,bytes(0x200));self.call(0x1400cc2b0,ints=(self.B,));self.call(0x1400eb5d0,ints=(self.B,))
  self.i(0x1406d7f08,s.total);self.i(self.B+0x1000+0x178,0)
  for off,b in [(0,s.bike.body),(0x68,s.bike.wheel1),(0xd0,s.bike.wheel2)]:
   for field,v in [(0x20,b.angle),(0x28,b.omega),(0x30,b.radius),(0x38,b.mass),(0x40,b.inertia)]:self.d(self.B+off+field,v)
   self.vec(self.B+off+0x48,b.p);self.vec(self.B+off+0x58,b.v)
  self.vec(self.B+0x158,s.bike.head_position);self.vec(self.B+0x168,s.bike.head_velocity)
  self.u.mem_write(self.STATE,bytes(0xa0));self.d(self.STATE+0x28,s.input.last_volt);self.i(self.FINISH,-1);self.i(self.DEAD,0);self.i(self.AUX+0x800-0x58,0)
 def step(self,t,dt,controls):
  self.keys={k:controls.get(name,False) for k,name in [(10,'gas'),(11,'brake'),(12,'left'),(13,'right'),(14,'turn')]};self.recorded=[]
  for reg,value in [(UC_X86_REG_R12,0),(UC_X86_REG_R14,0),(UC_X86_REG_RBX,self.CONFIG),(UC_X86_REG_RDI,self.B),(UC_X86_REG_RBP,self.AUX+0x800)]:self.u.reg_write(reg,value)
  self.call(0x1400e8acc)
  self.call(0x1400e7fb0,ints=(self.B,self.KEYS,self.STATE,self.AUX+0x600),stack=(self.FINISH,self.DEAD,t,dt))
  return self.recorded

def main():
 levels=json.loads(pathlib.Path(__file__).with_name('original-world.json').read_text())['levels'];o=SessionOracle();worst=0.;steps=0;event_count=0;results=[]
 def close(a,b):
  nonlocal worst
  worst=max(worst,abs(a-b));assert math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-8),(level['name'],mode,tick,a,b,worst)
 scenarios=[(levels[n-1],mode,450) for n in [1,6,12,28] for mode in ['gas','mixed']]
 def fixture(name,objects):
  return dict(name=name,polygons=[dict(grass=0,vertices=[[-20,2],[20,2],[20,3],[-20,3]])],objects=[dict(type=4,p=[0,0],gravity=0)]+objects)
 def obj(kind,x=0,y=0,gravity=0):return dict(type=kind,p=[x,y],gravity=gravity)
 for gravity in range(1,5):scenarios.append((fixture('fixture: gravity '+str(gravity),[obj(2,gravity=gravity)]),'gas',12))
 for name,objects in [('apple and finish',[obj(2),obj(1)]),('two apples and finish',[obj(2),obj(2),obj(1)]),('locked finish',[obj(1),obj(2,8)]),('killer',[obj(3)]),('apple, killer and finish',[obj(2),obj(3,1.7),obj(1)])]:scenarios.append((fixture('fixture: '+name,objects),'gas',12))
 for level,mode,limit in scenarios:
   s=Session(level)
   if level['name'].startswith('fixture:'):s.time=.432123
   o.reset(s);events=0
   for tick in range(limit):
    c={'gas':True} if mode=='gas' else dict(gas=tick%90<65,brake=65<=tick%90<80,left=90<=tick%160<110,right=130<=tick%160<150,turn=35<=tick%100<50)
    dt=[.001,.003,.0055][tick%3] if level['name'].startswith('fixture:') else .0055
    native=o.step(s.time,dt,c);actual=s.step(dt=dt,**c);assert len(native)==len(actual),(level['name'],mode,tick,native,actual)
    for a,b in zip(native,actual):assert (a[0],a[2])==(b[0],b[2]);close(a[1],b[1])
    for key in ['body','wheel1','wheel2']:
     expected=o.state()[key];body=getattr(s.bike,key)
     for k in ['angle','omega']:close(expected[k],getattr(body,k))
     for k in ['p','v']:
      for a,b in zip(expected[k],getattr(body,k)):close(a,b)
    for off,values in [(0x158,s.bike.head_position),(0x168,s.bike.head_velocity)]:
     for a,b in zip(o.vec(o.B+off),values):close(a,b)
    assert bool(o.i(o.DEAD))==s.dead;assert (o.i(o.FINISH)>=0)==s.finished
    if s.finished:assert o.i(o.FINISH)==s.finish_centiseconds
    assert bool(o.i(o.B+0x148))==s.bike.flipped;assert bool(o.i(o.AUX+0x800-0x58))==s.input.turn_was_down
    assert bool(o.i(o.B+0x17c))==s.bike.was_brake
    if s.bike.was_brake:
     for off,v in zip([0x180,0x188],s.bike.locks):close(o.d(o.B+off),v)
    for off,k in [(0x190,'negative_active'),(0x194,'positive_active')]:assert bool(o.i(o.B+off))==getattr(s.bike.volt,k)
    for off,k in [(0x198,'negative_time'),(0x1a0,'positive_time'),(0x1a8,'negative_saved'),(0x1b0,'positive_saved')]:close(o.d(o.B+off),getattr(s.bike.volt,k))
    assert o.i(o.B+0x178)==s.apples;assert o.i(o.B+0x150)==s.bike.gravity;close(o.d(o.STATE+0x28),s.input.last_volt)
    for i,obj in enumerate(s.objects):assert bool(o.i(o.OBJECTS+i*0x40+0x2c))==obj['active']
    assert len(o.queue())==len(s.events.items)
    for a,b in zip(o.queue(),s.events.items):assert (a[0],a[2])==(b[0],b[2]);close(a[1],b[1])
    events+=len(actual);steps+=1
    if s.dead or s.finished:break
   event_count+=events;results.append(dict(level=level['name'],controls=mode,steps=tick+1,dead=s.dead,finished=s.finished,apples=s.apples,events=events));print(results[-1],flush=True)
 result=dict(steps=steps,events=event_count,max_absolute_error=worst,scenarios=results,scope=__doc__)
 pathlib.Path(__file__).with_name('session-verification.json').write_text(json.dumps(result,indent=2));print('error',worst)
if __name__=='__main__':main()
