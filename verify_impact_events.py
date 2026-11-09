"""Contact response and impact events, including strict 1.5 threshold/cap."""
import random,math,json,pathlib
from collision import *
from verify_collision import MultiOracle
from verify_contact import values
from oracle import number
from unicorn.x86_const import *
class ImpactOracle(MultiOracle):
 def silence(self,u,a,s,d):
  idx=u.reg_read(UC_X86_REG_R8)&0xffffffff
  self.events.append((u.reg_read(UC_X86_REG_RCX),number(u.reg_read(UC_X86_REG_XMM1)),idx if idx<2**31 else idx-2**32));self.ret()
if __name__=='__main__':
 o=ImpactOracle();r=random.Random(16280);worst=0.;event_count=0
 for case in range(600):
  vy=[0.,-1.5,-1.500000001,-7.92,-20.,2.][case] if case<6 else r.uniform(-20,20)
  b=Body((0.,.4),(0. if case<6 else r.uniform(-5,5),vy),0.,r.uniform(-10,10),10.,.32,.4)
  points=[(0.,0.)] if case<6 or case%2 else [(-.15,.03),(.15,.03)]
  force=(0.,-100.);torque=r.uniform(-10,10);dt=.003;o.events=[];events=[]
  expected=o.multi_step(b,force,torque,dt,points);actual=contact_step(b,force,torque,dt,points,lambda *e:events.append(e))
  assert len(o.events)==len(events),(case,o.events,events)
  for a,bv in zip(o.events,events):
   assert (a[0],a[2])==(bv[0],bv[2]);worst=max(worst,abs(a[1]-bv[1]));assert math.isclose(a[1],bv[1],abs_tol=1e-12)
  for a,bv in zip(values(expected),values(actual)):assert math.isclose(a,bv,abs_tol=1e-10,rel_tol=1e-12)
  if case in [0,1]:assert not events
  if case==2:assert len(events)==1
  if case==4:assert events[0][1]==.99
  event_count+=len(events)
 result=dict(cases=600,events=event_count,max_event_value_error=worst,threshold=1.5,cap=.99)
 pathlib.Path(__file__).with_name('impact-events-verification.json').write_text(json.dumps(result,indent=2));print(result)
