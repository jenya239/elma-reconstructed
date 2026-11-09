from paths import EXE as ORIGINAL_EXE, RES as ORIGINAL_RES
"""Compare decoded directory and every internal level record with original x64 code.
Only file reads, allocation, and stack-cookie helper are replaced; record logic is native.
"""
from pathlib import Path
import json,struct
from oracle import Oracle,UC_HOOK_CODE,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_R9,UC_X86_REG_RBX,UC_X86_REG_R10,UC_X86_REG_R11,UC_X86_REG_RAX
from world import resources,decode_directory,extract
res=Path(ORIGINAL_RES).read_bytes()
o=Oracle();u=o.u
u.mem_write(o.AUX,res[4:72004])
for reg,value in [(UC_X86_REG_RCX,23),(UC_X86_REG_R10,0x26fe),(UC_X86_REG_R11,0xd3f),(UC_X86_REG_R8,o.AUX),(UC_X86_REG_RBX,3000)]:u.reg_write(reg,value)
u.emu_start(0x140140110,0x140140167,count=3000000)
assert bytes(u.mem_read(o.AUX,72000))==decode_directory(res[4:72004])
source=b'';pos=0

def fread(u,a,s,d):
 global pos
 dest=u.reg_read(UC_X86_REG_RCX);size=u.reg_read(UC_X86_REG_RDX);count=u.reg_read(UC_X86_REG_R8);n=size*count
 block=source[pos:pos+n];assert len(block)==n;u.mem_write(dest,block);pos+=n;u.reg_write(UC_X86_REG_RAX,count);o.ret()
def alloc(u,a,s,d):
 assert u.reg_read(UC_X86_REG_RCX)<0xf0000;u.reg_write(UC_X86_REG_RAX,o.AUX);o.ret()
def cookie(u,a,s,d):o.ret()
for addr,fn in [(0x140173e20,fread),(0x1404e459c,alloc),(0x1404e4550,cookie)]:u.hook_add(UC_HOOK_CODE,fn,begin=addr,end=addr)
world=extract(ORIGINAL_RES,ORIGINAL_EXE)
counts={'directory_bytes':72000,'levels':len(world['levels']),'polygons':0,'objects':0,'pictures':0}
for level in world['levels']:
 entry=level['resource'];source=res[entry['offset']:entry['offset']+entry['size']]
 for poly in level['polygons']:
  pos=poly['offset'];o.call(0x1400ddd30,ints=(o.B,1,14))
  n=struct.unpack('<i',u.mem_read(o.B+4,4))[0];grass=struct.unpack('<i',u.mem_read(o.B+16,4))[0]
  assert n==len(poly['vertices']) and grass==poly['grass'];p=o.q(o.B+8)
  assert [list(o.vec(p+i*16)) for i in range(n)]==poly['vertices'];assert pos==poly['offset']+8+n*16;counts['polygons']+=1
 for obj in level['objects']:
  pos=obj['offset'];o.call(0x1401132d0,ints=(o.B,1,14))
  assert list(o.vec(o.B))==obj['p'];assert list(struct.unpack('<iii',u.mem_read(o.B+32,12)))==[obj['type'],obj['gravity'],obj['animation']];assert pos==obj['offset']+28;counts['objects']+=1
 for pic in level['pictures']:
  pos=pic['offset'];o.call(0x140113950,ints=(o.B,1))
  for off,key in [(0,'picture'),(10,'texture'),(20,'mask')]:assert bytes(u.mem_read(o.B+off,10)).split(b'\0',1)[0].decode('latin1')==pic[key][:9]
  assert list(o.vec(o.B+32))==pic['p'];assert list(struct.unpack('<ii',u.mem_read(o.B+64,8)))==[pic['distance'],pic['clipping']];assert pos==pic['offset']+54;counts['pictures']+=1
counts['result']='Exact parsed values and consumed byte counts match original machine code'
Path(__file__).with_name('world-verification.json').write_text(json.dumps(counts,indent=2));print(json.dumps(counts))
