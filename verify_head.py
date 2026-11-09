"""Execute original rider clamp, including actual static constant initialization.
Only CRT thread-local guards are simulated, not the constraint mathematics.
"""
import math,random,struct,pathlib,json
from oracle import Oracle
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from head import constrain_head

def setup_tls(o):
    gs=o.B+0x180000;table=gs+0x1000;tls=gs+0x2000
    o.u.reg_write(UC_X86_REG_GS_BASE,gs);o.q(gs+0x58,table);o.q(table,tls)
    o.u.mem_write(tls+0x28,struct.pack('<i',-2147483648))
    def header(u,a,s,d):
        p=u.reg_read(UC_X86_REG_RCX);o.u.mem_write(p,struct.pack('<i',-1));o.ret()
    def footer(u,a,s,d):
        p=u.reg_read(UC_X86_REG_RCX);o.u.mem_write(p,struct.pack('<i',0));o.ret()
    for a,cb in [(0x1404e4328,header),(0x1404e42c8,footer)]:o.hooks.append(o.u.hook_add(UC_HOOK_CODE,cb,begin=a,end=a))

def main():
    o=Oracle();o.initialize();setup_tls(o);r=random.Random(5531);error=0
    for i in range(3000):
        angle=r.uniform(-8,8);forward=(math.cos(angle),math.sin(angle));up=(-forward[1],forward[0]);flipped=bool(i&1)
        bp=(r.uniform(-10,10),r.uniform(-10,10));hp=(bp[0]+r.uniform(-2,2),bp[1]+r.uniform(-2,2))
        o.vec(o.B+0x48,bp);o.vec(o.B+0x158,hp);o.q(o.B+0x148,int(flipped));o.vec(o.AUX,forward);o.vec(o.AUX+16,up)
        o.call(0x1400cecc0,ints=(o.B,o.AUX,o.AUX+16))
        got=o.vec(o.B+0x158);expected=constrain_head(bp,hp,forward,up,flipped)
        for a,b in zip(got,expected):
            error=max(error,abs(a-b));assert math.isclose(a,b,abs_tol=1e-12,rel_tol=1e-12),(i,got,expected)
    result={'head_clamp_cases':3000,'max_abs_error':error,'function':'0x1400cecc0','scope':'Position clamp only; rider spring and head terrain collision not included'}
    print(json.dumps(result,indent=2));pathlib.Path(__file__).with_name('head-verification.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
