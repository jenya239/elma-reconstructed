"""Run original narrow-phase code; only its candidate iterator is supplied."""
import math,random,json,pathlib
from collision import *
from oracle import Oracle
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
class QueryOracle(Oracle):
 def __init__(self):
  super().__init__();self.initialize();self.u.hook_del(self.hooks[4]);self.items=[];self.index=0
  for a,cb in [(0x140111a40,self.begin),(0x140111c20,self.next)]:self.hooks.append(self.u.hook_add(UC_HOOK_CODE,cb,begin=a,end=a))
 def begin(self,u,a,s,d):self.index=0;self.ret()
 def next(self,u,a,s,d):
  u.reg_write(UC_X86_REG_RAX,self.items[self.index] if self.index<len(self.items) else 0);self.index+=1;self.ret()
 def query(self,p,r,segments):
  self.items=[]
  for i,s in enumerate(segments):
   a=self.B+0x10000+i*0x80;self.vec(a,s.start);self.vec(a+0x20,s.axis);self.d(a+0x30,s.length);self.items.append(a)
  self.vec(self.AUX,p)
  self.call(0x14011a9b0,ints=(self.AUX,0,self.AUX+16,self.AUX+32),floats={1:r},stack=(self.AUX+48,self.AUX+56))
  n=self.u.reg_read(UC_X86_REG_RAX)
  return [self.vec(self.AUX+16+i*16) for i in range(n)]
if __name__=='__main__':
 o=QueryOracle();r=random.Random(41974);error=0.;counts=[0,0,0];merge=o.d(0x1406ccc68)
 print('merge_distance',merge,flush=True)
 for i in range(3000):
  p=(r.uniform(-4,4),r.uniform(-4,4));radius=r.uniform(.1,1.);segments=[]
  for _ in range(i%7):
   a=add(p,(r.uniform(-2,2),r.uniform(-2,2)));b=add(p,(r.uniform(-2,2),r.uniform(-2,2)));segments.append(Segment.endpoints(a,b))
  expected=o.query(p,radius,segments);actual=query_contacts(p,radius,segments,merge)
  assert len(expected)==len(actual),(i,expected,actual)
  counts[len(actual)]+=1
  for a,b in zip(expected,actual):
   for x,y in zip(a,b):
    error=max(error,abs(x-y));assert math.isclose(x,y,rel_tol=2e-12,abs_tol=2e-10),(i,expected,actual)
 result={'cases':3000,'by_contact_count':counts,'max_abs_error':error,'merge_distance':merge,'scope':'original narrow phase; ordered candidate iterator supplied'}
 print(json.dumps(result,indent=2));pathlib.Path(__file__).with_name('query-verification.json').write_text(json.dumps(result,indent=2))
