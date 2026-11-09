import sys,math,random,json,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from physics import *
from oracle import Oracle,bits,number
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
r=random.Random(20261108); o=Oracle();o.initialize(); results={}
def put(a,b):
 for off,v in [(0x20,b.angle),(0x28,b.omega),(0x30,b.radius),(0x38,b.mass),(0x40,b.inertia)]:o.d(a+off,v)
 o.vec(a+0x48,b.p);o.vec(a+0x58,b.v)
def body():return Body((r.uniform(-10,10),r.uniform(-10,10)),(r.uniform(-5,5),r.uniform(-5,5)),r.uniform(-4,4),r.uniform(-100,100),r.uniform(1,250),r.uniform(.1,80),r.uniform(.1,1))
def close(values,expected,scope):
 err=max(abs(a-b) for a,b in zip(values,expected)); results[scope]['max_abs_error']=max(results[scope]['max_abs_error'],err)
 for a,b in zip(values,expected):assert math.isclose(a,b,rel_tol=2e-12,abs_tol=2e-10),(scope,values,expected)
 results[scope]['cases']+=1
results['free_step']={'cases':0,'max_abs_error':0}
for i in range(1000):
 b=body();f=(r.uniform(-10000,10000),r.uniform(-10000,10000));torque=r.uniform(-1000,1000);dt=r.uniform(0,.0055)
 put(o.B,b);o.vec(o.AUX,f)
 o.call(0x1400cdf50,ints=(o.B,o.AUX),floats={2:torque,3:dt},stack=(0,))
 e=free_step(b,f,torque,dt)
 close([o.d(o.B+0x20),o.d(o.B+0x28),*o.vec(o.B+0x48),*o.vec(o.B+0x58)],[e.angle,e.omega,*e.p,*e.v],'free_step')
results['suspension']={'cases':0,'max_abs_error':0}
for i in range(1000):
 b=body();w=body();rest=((-1 if i%2 else 1)*.8500000000000001,-.6000000000000001);t=r.uniform(-600,600)
 if i<10:
  a=(cos(b.angle),sin(b.angle));w.p=add(b.p,add(mul(a,rest[0]),mul(perp(a),rest[1])))
 put(o.B,b);put(o.B+0x68,w)
 o.vec(o.AUX,(cos(b.angle),sin(b.angle)));o.vec(o.AUX+16,(-sin(b.angle),cos(b.angle)));o.d(o.AUX+96,t)
 o.call(0x1400ea220,ints=(o.B,o.B+0x68,o.AUX,o.AUX+16),stack=(*rest,o.AUX+32,o.AUX+48,o.AUX+64,o.AUX+96))
 fw,fb,tb=suspension(b,w,rest,t)
 close([*o.vec(o.AUX+32),*o.vec(o.AUX+48),o.d(o.AUX+64)],[*fw,*fb,tb],'suspension')
results['wheel_controls']={'cases':0,'max_abs_error':0}
# Stop after the real control branch, before unrelated suspension/head calls.
def stop(u,a,s,d):u.emu_stop()
h=o.u.hook_add(UC_HOOK_CODE,stop,begin=0x1400eaa30,end=0x1400eaa30)
for i in range(1000):
 b=body();w1=body();w2=body();w1.angle=r.uniform(-8,8);w2.angle=r.uniform(-8,8);w1.omega=r.uniform(-130,130);w2.omega=r.uniform(-130,130)
 gas=bool(i&1);brake=bool(i&2);flipped=bool(i&4);was_brake=bool(i&8);locks=(r.uniform(-4,4),r.uniform(-4,4))
 put(o.B,b);put(o.B+0x68,w1);put(o.B+0xd0,w2);o.q(o.B+0x148,int(flipped));o.q(o.B+0x17c,int(was_brake));o.d(o.B+0x180,locks[0]);o.d(o.B+0x188,locks[1])
 if brake and not was_brake:locks=(w1.angle-b.angle,w2.angle-b.angle)
 sp=o.STACK+0x80008;o.q(sp,o.STOP);o.u.reg_write(UC_X86_REG_RSP,sp);o.u.reg_write(UC_X86_REG_RCX,o.B);o.u.reg_write(UC_X86_REG_R9,int(gas));o.q(sp+0x28,int(brake))
 o.u.emu_start(0x1400ea7f0,o.STOP,count=10000)
 assert o.u.reg_read(UC_X86_REG_RIP)==0x1400eaa30
 vals=[number(o.u.reg_read(UC_X86_REG_XMM7)),number(o.u.reg_read(UC_X86_REG_XMM8)),o.d(o.B+0x88),o.d(o.B+0xf0)]
 close(vals,wheel_torques(b,w1,w2,gas,brake,flipped,locks),'wheel_controls')
o.u.hook_del(h)
print(json.dumps(results,indent=2));pathlib.Path(__file__).with_name('verification.json').write_text(json.dumps(results,indent=2))
