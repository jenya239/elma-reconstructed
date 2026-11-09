"""Differential test of entire one-contact path, using original x64 code.
Only terrain lookup (supplied point) and impact sound are replaced.
"""
import random, math, json, pathlib
from physics import *
from oracle import Oracle
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
class ContactOracle(Oracle):
    contact=(0.,0.)
    def empty(self,u,a,s,d):
        self.vec(u.reg_read(UC_X86_REG_R8),self.contact)
        u.reg_write(UC_X86_REG_RAX,1);self.ret()
    def silence(self,u,a,s,d):self.ret()
    def __init__(self):
        super().__init__();self.initialize()
        self.hooks.append(self.u.hook_add(UC_HOOK_CODE,self.silence,begin=0x14010e010,end=0x14010e010))
    def step(self,b,f,t,dt,point):
        self.contact=point
        for off,v in [(0x20,b.angle),(0x28,b.omega),(0x30,b.radius),(0x38,b.mass),(0x40,b.inertia)]:self.d(self.B+off,v)
        self.vec(self.B+0x48,b.p);self.vec(self.B+0x58,b.v);self.vec(self.AUX,f)
        self.call(0x1400cdf50,ints=(self.B,self.AUX),floats={2:t,3:dt},stack=(1,))
        return Body(**self.state()['body'])
def values(b):return [*b.p,*b.v,b.angle,b.omega]
if __name__=='__main__':
    o=ContactOracle();r=random.Random(92411);error=0.;released=0
    for i in range(2000):
        point=(r.uniform(-10,10),r.uniform(-10,10));a=r.uniform(-math.pi,math.pi);radius=r.uniform(.1,1.)
        b=Body(add(point,mul((cos(a),sin(a)),radius*r.uniform(.25,1.01))),
               (r.uniform(-10,10),r.uniform(-10,10)),r.uniform(-4,4),r.uniform(-100,100),r.uniform(1,250),r.uniform(.1,80),radius)
        f=(r.uniform(-10000,10000),r.uniform(-10000,10000));t=r.uniform(-600,600);dt=r.uniform(0,.0055)
        expected=o.step(b,f,t,dt,point);actual=one_contact_step(b,f,t,dt,point)
        for x,y in zip(values(expected),values(actual)):
            error=max(error,abs(x-y));assert math.isclose(x,y,rel_tol=2e-12,abs_tol=2e-10),(i,expected,actual)
    result={'one_contact':{'cases':2000,'max_abs_error':error,'terrain_query':'supplied point','impact_audio':'disabled'}}
    print(json.dumps(result,indent=2));pathlib.Path(__file__).with_name('contact-verification.json').write_text(json.dumps(result,indent=2))
