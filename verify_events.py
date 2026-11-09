"""Run actual object queries, collector/tree, FIFO and effect code.
Only allocation/free, host initialization and head terrain hit are supplied.
"""
import struct,random,copy,json,pathlib,math
from oracle import Oracle
from events import *
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
class EventOracle(Oracle):
 LEVEL=0x7000000;CONFIG=0x70c0000;OBJECTS=0x7060000;HEAP=0x8000000
 head_hit=False
 def __init__(self):
  super().__init__();self.initialize();self.u.mem_map(self.LEVEL,0x100000);self.u.mem_map(self.HEAP,0x100000);self.heap=self.HEAP
  self.q(0x140708920,self.LEVEL);self.q(0x1406cdf10,self.CONFIG)
  self.vec(self.CONFIG+0x28,(0.,0.))
  for addr,cb in [(0x1404e3f0c,self.alloc),(0x1404e3f48,self.free)]:self.u.hook_add(UC_HOOK_CODE,cb,begin=addr,end=addr)
 def empty(self,u,a,s,d):u.reg_write(UC_X86_REG_RAX,int(self.head_hit));self.ret()
 def alloc(self,u,a,s,d):
  n=u.reg_read(UC_X86_REG_RCX);p=self.heap;self.heap+=(n+15)&~15;assert self.heap<self.HEAP+0x100000
  u.reg_write(UC_X86_REG_RAX,p);self.ret()
 def free(self,u,a,s,d):self.ret()
 def i(self,a,v=None):
  if v is None:return struct.unpack('<i',self.u.mem_read(a,4))[0]
  self.u.mem_write(a,struct.pack('<i',v))
 def setup(self,objects,ignore=False):
  self.heap=self.HEAP;self.i(0x1406ff92c,0);self.u.mem_write(self.LEVEL+0x3a990,bytes(10000*8));self.i(0x1406b84d0,0);self.i(0x1406d7ebc,int(ignore))
  for i,obj in enumerate(objects):
   a=self.OBJECTS+i*0x40;self.q(self.LEVEL+0x3a990+i*8,a);self.vec(a,obj['p']);self.i(a+0x10,obj['pixel'][0]);self.i(a+0x14,obj['pixel'][1]);self.i(a+0x20,obj['type']);self.i(a+0x24,obj['gravity']);self.i(a+0x2c,int(obj['active']))
 def collect(self,probes):
  for off,(p,r,pixel) in zip([0xb0,0x118,0x138],probes):self.vec(self.B+off,p)
  self.d(self.B+0x98,probes[0][1]);self.d(self.B+0x100,probes[1][1]);self.d(0x1406ccca8,probes[2][1]);self.call(0x1400eb770,ints=(self.B,))
  return self.u.reg_read(UC_X86_REG_RAX)
 def queue(self):return [(self.i(0x1406ff9a0+i*4),self.d(0x1406ffcc0+i*8),self.i(0x140700300+i*4)) for i in range(self.i(0x1406ff92c))]
 def pop(self):
  self.call(0x14010c540,ints=(self.AUX,self.AUX+8,self.AUX+16))
  if not self.u.reg_read(UC_X86_REG_RAX):return None
  return self.i(self.AUX),self.d(self.AUX+8),self.i(self.AUX+16)
if __name__=='__main__':
 o=EventOracle();r=random.Random(4119);scale=o.d(0x1406cccc0);total_events=0;deaths=0
 print('coordinate scale',scale,flush=True)
 for case in range(400):
  objects=[]
  for _ in range(case%18):
   p=(r.uniform(-1,1),r.uniform(-1,1));objects.append({'p':p,'type':r.randint(1,4),'gravity':r.randint(0,4),'active':bool(r.getrandbits(1)),'pixel':(int(p[0]*scale)+(1200 if case%11==0 else 0),int(p[1]*scale))})
  probes=[]
  for _ in range(3):
   p=(r.uniform(-.6,.6),r.uniform(-.6,.6));probes.append((p,r.uniform(.1,.6),(int(p[0]*scale),int(p[1]*scale))))
  ignore=bool(case%2);hit=case%17==0;o.setup(objects,ignore);o.head_hit=hit
  expected_objects=copy.deepcopy(objects);q=EventQueue();status=collect_objects(probes,expected_objects,q,hit,ignore)
  assert o.collect(probes)==status;assert o.queue()==q.items,(case,o.queue(),q.items)
  for i,obj in enumerate(expected_objects):assert bool(o.i(o.OBJECTS+i*0x40+0x2c))==obj['active']
  total_events+=len(q.items);deaths+=int(hit)
  apples=r.randint(0,5);other=r.randint(0,5);total=sum(x['type']==2 for x in objects);gravity=r.randint(0,3)
  o.i(o.B+0x178,apples);o.i(o.B+0x1000+0x178,other);o.i(o.B+0x150,gravity);o.i(0x1406d7f08,total)
  expected=drain_events(q,expected_objects,apples,total,gravity,other);consumed=[];dead=finished=False
  while (event:=o.pop()) is not None:
   consumed.append(event)
   if event[2]>=0:
    o.call(0x1400e9f60,ints=(event[2],o.B+0x178,o.B));ret=o.u.reg_read(UC_X86_REG_RAX);dead|=ret==0;finished|=ret==1
  actual={'apples':o.i(o.B+0x178),'gravity':o.i(o.B+0x150),'dead':dead,'finished':finished,'events':consumed}
  assert actual==expected,(case,actual,expected)
 # Native FIFO capacity and ordering, including silent drops after 200.
 o.i(0x1406ff92c,0);q=EventQueue()
 for i in range(250):o.call(0x14010e010,ints=(i,0,i-1),floats={1:i*.125});q.push(i,i*.125,i-1)
 assert o.queue()==q.items and len(q.items)==200
 for _ in range(201):assert o.pop()==q.pop()
 result={'collector_and_effect_scenarios':400,'collected_events':total_events,'terrain_death_cases':deaths,'fifo_capacity':200,'fifo_insertions':250,'result':'Exact status, ordered events, object active flags, apple counts and gravity'}
 print(json.dumps(result,indent=2));pathlib.Path(__file__).with_name('events-verification.json').write_text(json.dumps(result,indent=2))
