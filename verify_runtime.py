"""Execute original timer and frame partition fragment, supplying tick sink."""
import random,json,pathlib,math
from oracle import Oracle,bits,number
from runtime import frame_steps
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
o=Oracle();samples=[];timer_value=0.;counter=0

def timer(u,a,s,d):u.reg_write(UC_X86_REG_XMM0,bits(timer_value));o.ret()
def noop(u,a,s,d):o.ret()
def tick(u,a,s,d):
 samples.append((number(u.reg_read(UC_X86_REG_XMM7)),number(u.reg_read(UC_X86_REG_XMM6))));u.reg_write(UC_X86_REG_RIP,0x1400e8982)
def stop(u,a,s,d):u.reg_write(UC_X86_REG_RIP,o.STOP)
def freq(u,a,s,d):u.reg_write(UC_X86_REG_RAX,1_000_000_000);o.ret()
def clock(u,a,s,d):u.reg_write(UC_X86_REG_RAX,counter);o.ret()
for a,cb in [(0x140016ed0,noop),(0x1400e873b,tick),(0x1400e8991,stop),(0x1404e5bba,freq),(0x1404e5bb4,clock)]:o.u.hook_add(UC_HOOK_CODE,cb,begin=a,end=a)
r=random.Random(815)
for i in range(100):
 counter=r.randrange(0,100_000_000_000);o.call(0x14014eb50);got=number(o.u.reg_read(UC_X86_REG_XMM0));assert got==(counter//1_000_000)*.182,(counter,got)
o.u.hook_add(UC_HOOK_CODE,timer,begin=0x14014eb50,end=0x14014eb50)
count=0
for i in range(1000):
 elapsed=r.randrange(0,200000) if i else 0;current=max(0.,elapsed*.0004368-r.uniform(-.01,.2));timer_value=elapsed*.182;samples=[]
 for reg,val in [(UC_X86_REG_XMM7,current),(UC_X86_REG_XMM10,.0055),(UC_X86_REG_XMM12,1e-6),(UC_X86_REG_XMM14,.0024)]:o.u.reg_write(reg,bits(val))
 o.call(0x1400e86e4);expected=list(frame_steps(current,elapsed));assert samples==expected,(i,samples,expected);count+=len(samples)
result=dict(timer_cases=100,partition_cases=1000,substeps=count,result='Exact times, substep sizes and ordering',scope=__doc__)
pathlib.Path(__file__).with_name('runtime-verification.json').write_text(json.dumps(result,indent=2));print(result)
