from paths import EXE as ORIGINAL_EXE, RES as ORIGINAL_RES
"""Execute selected original x64 functions in Unicorn, without starting the game.
External sin/cos use host libm; the level query can be stubbed as empty space.
"""
import struct, math, pathlib, hashlib, os
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE
from unicorn.x86_const import *

EXE=os.environ.get('ELMA_EXE',ORIGINAL_EXE)
SHA='d2caa85701535b866fca6310320bc078a00571221ce6d02b1d7c525718d80d5a'
def bits(x):return struct.unpack('<Q',struct.pack('<d',x))[0]
def number(x):return struct.unpack('<d',struct.pack('<Q',x&((1<<64)-1)))[0]
class Oracle:
    B=0x2000000; AUX=0x2100000; STACK=0x3000000; STOP=0x4000000
    def __init__(self,path=EXE):
        raw=pathlib.Path(path).read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
        pe=pefile.PE(data=raw);self.u=Uc(UC_ARCH_X86,UC_MODE_64)
        self.u.mem_map(pe.OPTIONAL_HEADER.ImageBase,(pe.OPTIONAL_HEADER.SizeOfImage+4095)&~4095)
        self.u.mem_write(pe.OPTIONAL_HEADER.ImageBase,pe.get_memory_mapped_image())
        for a,size in [(self.B,0x200000),(self.STACK,0x100000),(self.STOP,4096)]:self.u.mem_map(a,size)
        self.hooks=[];self.empty_queries=0
        for a,cb in [(0x14000f9f0,self.string),(0x140018840,self.timer),(0x1404e6010,self.sin),(0x1404e600a,self.cos),(0x14011a9b0,self.empty)]:
            self.hooks.append(self.u.hook_add(UC_HOOK_CODE,cb,begin=a,end=a))
    def ret(self):
        sp=self.u.reg_read(UC_X86_REG_RSP);dst=self.q(sp);self.u.reg_write(UC_X86_REG_RSP,sp+8);self.u.reg_write(UC_X86_REG_RIP,dst)
    def string(self,u,a,s,d):u.reg_write(UC_X86_REG_RAX,u.reg_read(UC_X86_REG_RCX));self.ret()
    def timer(self,u,a,s,d):u.reg_write(UC_X86_REG_RAX,1000);self.ret()
    def sin(self,u,a,s,d):u.reg_write(UC_X86_REG_XMM0,bits(math.sin(number(u.reg_read(UC_X86_REG_XMM0)))));self.ret()
    def cos(self,u,a,s,d):u.reg_write(UC_X86_REG_XMM0,bits(math.cos(number(u.reg_read(UC_X86_REG_XMM0)))));self.ret()
    def empty(self,u,a,s,d):self.empty_queries+=1;u.reg_write(UC_X86_REG_RAX,0);self.ret()
    def q(self,a,v=None):
        if v is None:return struct.unpack('<Q',self.u.mem_read(a,8))[0]
        self.u.mem_write(a,struct.pack('<Q',v))
    def d(self,a,v=None):
        if v is None:return struct.unpack('<d',self.u.mem_read(a,8))[0]
        self.u.mem_write(a,struct.pack('<d',v))
    def vec(self,a,v=None):
        if v is None:return struct.unpack('<dd',self.u.mem_read(a,16))
        self.u.mem_write(a,struct.pack('<dd',*v))
    def call(self,addr,ints=(),floats={},stack=()):
        sp=self.STACK+0x80008;self.q(sp,self.STOP)
        for r,v in zip([UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_R9],ints):self.u.reg_write(r,v)
        for i,v in floats.items():self.u.reg_write(UC_X86_REG_XMM0+i,bits(v))
        for i,v in enumerate(stack):self.q(sp+0x28+i*8,bits(v) if isinstance(v,float) else v)
        self.u.reg_write(UC_X86_REG_RSP,sp)
        try:self.u.emu_start(addr,self.STOP,timeout=3_000_000,count=500000)
        except Exception as e:raise RuntimeError(f'{e}; RIP={self.u.reg_read(UC_X86_REG_RIP):x}') from e
        assert self.u.reg_read(UC_X86_REG_RIP)==self.STOP,'instruction/time budget exhausted'
    def initialize(self):
        self.q(0x1406b7f08,self.B);self.q(0x1406b7f10,self.B+0x1000)
        for a in [0x140008c20,0x140008c40,0x140008c60,0x1400cbf20]:self.call(a)
    def state(self):
        return {name:{'angle':self.d(self.B+off+0x20),'omega':self.d(self.B+off+0x28),'radius':self.d(self.B+off+0x30),'mass':self.d(self.B+off+0x38),'inertia':self.d(self.B+off+0x40),'p':self.vec(self.B+off+0x48),'v':self.vec(self.B+off+0x58)} for name,off in [('body',0),('wheel1',0x68),('wheel2',0xd0)]}

if __name__=='__main__':
    import json
    o=Oracle();o.initialize();print(json.dumps(o.state(),indent=2))
