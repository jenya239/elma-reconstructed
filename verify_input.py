"""Verify held-key -> gas/brake/volt pulse logic at e7fb0..e80f5.
Key state/config getter/sound are host substitutions; stop before physics.
"""
import random,struct,json,pathlib
from oracle import Oracle,number
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
o=Oracle();o.initialize();r=random.Random(331);keys={};captured=[]
KEYS=o.AUX;STATE=o.AUX+0x100;CONFIG=o.AUX+0x10000
o.q(0x1407009e0,CONFIG);o.u.mem_write(CONFIG+0x10918,struct.pack('<i',77));o.u.mem_write(KEYS,struct.pack('<iiii',10,11,12,13))
def key(u,a,s,d):u.reg_write(UC_X86_REG_RAX,int(keys.get(u.reg_read(UC_X86_REG_RCX),False)));o.ret()
def config(u,a,s,d):u.reg_write(UC_X86_REG_RAX,99);o.ret()
def noop(u,a,s,d):o.ret()
def capture(u,a,s,d):
 sp=u.reg_read(UC_X86_REG_RSP)
 captured[:]=[u.reg_read(UC_X86_REG_R9),o.q(sp+0x28),o.q(sp+0x30),o.q(sp+0x38)]
 u.reg_write(UC_X86_REG_RIP,o.STOP)
for addr,cb in [(0x140016e50,key),(0x1400d4b00,config),(0x14010e010,noop),(0x1400ea7f0,capture)]:o.u.hook_add(UC_HOOK_CODE,cb,begin=addr,end=addr)
for i in range(2000):
 keys={k:bool(r.getrandbits(1)) for k in [10,11,12,13,77,99]};now=r.uniform(-1,3);last=r.uniform(-1,3);o.d(STATE+0x28,last)
 o.call(0x1400e7fb0,ints=(o.B,KEYS,STATE,o.AUX+0x200),stack=(o.AUX+0x300,o.AUX+0x308,now,.0055))
 gate=last+.4<now;negative=gate and (keys[12] or keys[77]);positive=gate and (keys[13] or keys[77])
 assert captured==[int(keys[10]),int(keys[11] or keys[99]),int(negative),int(positive)],(i,captured)
 assert o.d(STATE+0x28)==(now if negative or positive else last)
result={'cases':2000,'result':'Exact flags and cooldown time','scope':'Original held-key gate incl alternate brake and combined volt; turn edge statically traced only'}
print(json.dumps(result));pathlib.Path(__file__).with_name('input-verification.json').write_text(json.dumps(result,indent=2))
