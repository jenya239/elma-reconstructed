"""Differential test of actual volt branch; no replacement physics hooks."""
import random, struct, json, pathlib, math
from dataclasses import astuple
from oracle import Oracle,bits
from controls import VoltState,volt_step
from unicorn.x86_const import *
o=Oracle();o.initialize();r=random.Random(777);error=0
for i in range(2500):
    s=VoltState(r.uniform(-50,50), bool(i&1),bool(i&2),r.uniform(-1,1),r.uniform(-1,1),r.uniform(-50,50),r.uniform(-50,50))
    t=r.uniform(-1,2);neg=bool(i&4);pos=bool(i&8)
    hp=(r.uniform(-4,4),r.uniform(-4,4));bp=(r.uniform(-4,4),r.uniform(-4,4));hv=(r.uniform(-4,4),r.uniform(-4,4))
    o.d(o.B+0x28,s.omega)
    o.u.mem_write(o.B+0x190,struct.pack('<ii',s.negative_active,s.positive_active))
    for off,val in [(0x198,s.negative_time),(0x1a0,s.positive_time),(0x1a8,s.negative_saved),(0x1b0,s.positive_saved)]:o.d(o.B+off,val)
    o.vec(o.B+0x158,hp);o.vec(o.B+0x48,bp);o.vec(o.B+0x168,hv)
    sp=o.STACK+0x80000;bpreg=sp+0x200
    o.u.reg_write(UC_X86_REG_RSP,sp);o.u.reg_write(UC_X86_REG_RBP,bpreg);o.u.reg_write(UC_X86_REG_RDI,o.B)
    o.q(bpreg+0xc8,int(neg));o.q(bpreg+0xd0,int(pos))
    o.u.reg_write(UC_X86_REG_XMM9,bits(0.0));o.u.reg_write(UC_X86_REG_XMM10,bits(t))
    o.u.emu_start(0x1400eab32,0x1400ead66,count=10000)
    assert o.u.reg_read(UC_X86_REG_RIP)==0x1400ead66
    expected,ev=volt_step(s,t,neg,pos,hp,bp,hv)
    actual=[o.d(o.B+0x28),*struct.unpack('<ii',o.u.mem_read(o.B+0x190,8)),*[o.d(o.B+x) for x in [0x198,0x1a0,0x1a8,0x1b0]],*o.vec(o.B+0x168)]
    desired=[*astuple(expected),*ev]
    for a,b in zip(actual,desired):
        error=max(error,abs(a-b));assert math.isclose(a,b,abs_tol=1e-12,rel_tol=1e-12),(i,actual,desired)
result={'volt_cases':2500,'max_abs_error':error,'original_range':'0x1400eab32..0x1400ead66','scope':'Core input pulses only; keyboard edge/repeat decoding not covered'}
print(json.dumps(result,indent=2));pathlib.Path(__file__).with_name('controls-verification.json').write_text(json.dumps(result,indent=2))
