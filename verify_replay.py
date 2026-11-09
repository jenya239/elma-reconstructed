from paths import EXE as ORIGINAL_EXE, RES as ORIGINAL_RES
"""Compare REC parsing and playback with original x64 loader/player."""
import json,struct,random,pathlib
from oracle import Oracle
from replay import *
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
class ReplayOracle(Oracle):
 def __init__(self):
  super().__init__();self.u.hook_add(UC_HOOK_CODE,self.read,begin=0x140173e20,end=0x140173e20)
  for a in [0xb2c0,0xb2e0,0xb300,0xb320,0xb360,0xb340,0xb380]:self.call(0x140000000+a)
 def read(self,u,a,s,d):
  size=u.reg_read(UC_X86_REG_RDX);count=u.reg_read(UC_X86_REG_R8);n=size*count
  data=self.raw[self.pos:self.pos+n];assert len(data)==n
  u.mem_write(u.reg_read(UC_X86_REG_RCX),data);self.pos+=n;u.reg_write(UC_X86_REG_RAX,count);self.ret()
 def load(self,raw,rec):
  self.raw=raw;self.pos=0;self.u.mem_write(self.B,bytes(0x1000))
  for k,(name,fmt,off) in enumerate(COLUMNS):self.q(self.B+off,self.AUX+k*0x10000)
  self.q(self.B+0x78,self.AUX+0xe0000)
  self.call(0x14010c790,ints=(self.B,self.B+0x800,1,0))
  assert self.pos==len(raw)
  assert self.u.reg_read(UC_X86_REG_RAX)&0xffffffff==rec['level_link']
  for name,fmt,off in COLUMNS:
   expected=struct.pack('<'+str(rec['frame_count'])+fmt,*rec['columns'][name]);assert bytes(self.u.mem_read(self.q(self.B+off),len(expected)))==expected
  assert bytes(self.u.mem_read(self.B+0xb0,16)).split(b'\0')[0].decode()==rec['level']
  events=raw[-4-16*len(rec['events']):-4] if rec['events'] else b''
  assert bytes(self.u.mem_read(self.q(self.B+0x78),len(events)))==events
 def sample(self,t):
  self.u.mem_write(self.B+0x74,bytes(4));b=self.B+0x1000;v=self.B+0x2000
  self.call(0x14010d400,ints=(self.B,b,0,v),floats={2:t})
  result={key:list(self.vec(b+off)) for key,off in [('body',0x48),('wheel1',0xb0),('wheel2',0x118),('head',0x158)]}
  result.update({key:self.d(b+off) for key,off in [('body_angle',0x20),('wheel1_angle',0x88),('wheel2_angle',0xf0)]})
  result.update(flipped=int.from_bytes(self.u.mem_read(b+0x148,4),'little'),flag0=self.u.mem_read(v+8,1)[0],flag2=int.from_bytes(self.u.mem_read(0x1406d7bd8,4),'little'),flag3=int.from_bytes(self.u.mem_read(0x1406d7bdc,4),'little'),visual_scale=self.d(v),visual_value=self.d(v+0x10))
  return result
if __name__=='__main__':
 o=ReplayOracle();demos=extract_demos();raw=Path(ORIGINAL_RES).read_bytes();rng=random.Random(1341);worst=0;count=0
 for rec in demos:
  e=rec['resource'];o.load(raw[e['offset']:e['offset']+e['size']],rec)
  times=[i/FRAME_RATE for i in range(rec['frame_count'])]+[rng.uniform(0,rec['frame_count']-1)/FRAME_RATE for _ in range(1000)]+[-.1,rec['frame_count']/FRAME_RATE]
  for t in times:
   actual=o.sample(t);expected=sample(rec,t)
   for k,v in expected.items():
    pairs=zip(v,actual[k]) if isinstance(v,list) else [(v,actual[k])]
    for a,b in pairs:
     err=abs(a-b);worst=max(worst,err);assert err<1e-10,(rec['resource']['name'],t,k,a,b)
   count+=1
 result=dict(demos=len(demos),playback_samples=count,max_absolute_error=worst,columns='all bytes identical to original loader',events='all bytes identical to original loader')
 Path(__file__).with_name('replay-verification.json').write_text(json.dumps(result,indent=2));print(result)
