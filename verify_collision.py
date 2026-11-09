import math,random,json,pathlib
from collision import *
from verify_contact import ContactOracle,values
from unicorn.x86_const import *
class MultiOracle(ContactOracle):
    contacts=[]
    def empty(self,u,a,s,d):
        for reg,point in zip([UC_X86_REG_R8,UC_X86_REG_R9],self.contacts):self.vec(u.reg_read(reg),point)
        u.reg_write(UC_X86_REG_RAX,len(self.contacts));self.ret()
    def multi_step(self,b,f,t,dt,points):
        self.contacts=points
        return self.step(b,f,t,dt,points[0] if points else (0.,0.))
if __name__=='__main__':
 o=MultiOracle();r=random.Random(18254);error=0.;counts=[0,0,0]
 print('constants',o.d(0x1406ccc68),o.vec(0x1406cd1a0),flush=True)
 for i in range(5000):
  b=Body((r.uniform(-10,10),r.uniform(-10,10)),(r.uniform(-3,3),r.uniform(-3,3)),r.uniform(-4,4),r.uniform(-100,100),r.uniform(1,250),r.uniform(.1,80),r.uniform(.1,1))
  if i%3==0:b=replace(b,v=mul(b.v,.1))
  points=[]
  for _ in range(i%3):
   angle=r.uniform(-math.pi,math.pi);points.append(add(b.p,mul((cos(angle),sin(angle)),b.radius*r.uniform(.4,1.01))))
  counts[len(points)]+=1
  f=(r.uniform(-10000,10000),r.uniform(-10000,10000));t=r.uniform(-600,600);dt=r.uniform(0,.0055)
  expected=o.multi_step(b,f,t,dt,points);actual=contact_step(b,f,t,dt,points)
  for x,y in zip(values(expected),values(actual)):
   error=max(error,abs(x-y));assert math.isclose(x,y,rel_tol=2e-12,abs_tol=2e-10),(i,b,points,f,t,expected,actual)
 result={'cases':5000,'by_contact_count':counts,'max_abs_error':error,'scope':'complete contact response, supplied points, muted impact audio'}
 print(json.dumps(result,indent=2));pathlib.Path(__file__).with_name('collision-verification.json').write_text(json.dumps(result,indent=2))
