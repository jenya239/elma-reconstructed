"""Execute original grid builder, lookup and narrow phase; replace heap/CRT only."""
import struct,math,random,pathlib,json
from terrain import *
from oracle import Oracle
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
class TerrainOracle(Oracle):
 GRID=0x2200000;SEG=0x2210000;HEAP=0x5000000
 def __init__(self):
  super().__init__();self.initialize();self.u.hook_del(self.hooks[4]);self.u.mem_map(self.GRID,0x100000);self.u.mem_map(self.HEAP,0x1000000);self.heap=self.HEAP
  for a,cb in [(0x1404e459c,self.alloc),(0x1404e3f0c,self.alloc),(0x1404e5f62,self.memset)]:self.hooks.append(self.u.hook_add(UC_HOOK_CODE,cb,begin=a,end=a))
 def alloc(self,u,a,s,d):
  n=u.reg_read(UC_X86_REG_RCX);p=self.heap;self.heap+=(n+15)&~15
  assert self.heap<=self.HEAP+0x1000000
  u.reg_write(UC_X86_REG_RAX,p);self.ret()
 def memset(self,u,a,s,d):
  p=u.reg_read(UC_X86_REG_RCX);n=u.reg_read(UC_X86_REG_R8);v=u.reg_read(UC_X86_REG_RDX)&255
  u.mem_write(p,bytes([v])*n);u.reg_write(UC_X86_REG_RAX,p);self.ret()
 def build(self,edges,margin=.4):
  self.heap=self.HEAP;self.u.mem_write(self.GRID,bytes(0x58));self.q(self.GRID,self.SEG)
  self.u.mem_write(self.GRID+0xc,struct.pack('<i',len(edges)))
  for i,(a,b) in enumerate(edges):self.vec(self.SEG+i*0x38,a);self.vec(self.SEG+i*0x38+0x10,sub(b,a))
  self.q(0x1407009a8,self.GRID);self.call(0x140111c60,ints=(self.GRID,),floats={1:margin})
 def cells(self):
  nx,ny=struct.unpack('<ii',self.u.mem_read(self.GRID+0x20,8));table=self.q(self.GRID+0x18);cells={}
  for y in range(ny):
   for x in range(nx):
    node=self.q(table+(y*nx+x)*8);ids=[]
    while node:ids.append((self.q(node)-self.SEG)//0x38);node=self.q(node+8)
    if ids:cells[x,y]=ids
  return cells
 def query(self,p,radius):
  self.vec(self.AUX,p);self.call(0x14011a9b0,ints=(self.AUX,0,self.AUX+16,self.AUX+32),floats={1:radius},stack=(self.AUX+48,self.AUX+56))
  return [self.vec(self.AUX+16+i*16) for i in range(self.u.reg_read(UC_X86_REG_RAX))]
if __name__=='__main__':
 o=TerrainOracle();r=random.Random(54124);queries=0;error=0.
 print('head radius',o.d(0x1406ccca8),flush=True)
 for run in range(40):
  edges=[((r.uniform(-5,5),r.uniform(-5,5)),(r.uniform(-5,5),r.uniform(-5,5))) for _ in range(1+run%15)]
  margin=r.uniform(.1,1.);t=Terrain(edges,margin);o.build(edges,margin)
  assert t.origin==o.vec(o.GRID+0x30)
  assert t.cells==o.cells(),('cells',run)
  for _ in range(50):
   p=(r.uniform(-7,7),r.uniform(-7,7));radius=r.uniform(.1,margin)
   expected=o.query(p,radius);actual=t.contacts(p,radius);assert len(expected)==len(actual)
   for a,b in zip(expected,actual):
    for x,y in zip(a,b):error=max(error,abs(x-y));assert math.isclose(x,y,rel_tol=2e-12,abs_tol=2e-10)
   queries+=1
 result={'grids':40,'queries':queries,'ordered_cell_lists':'exact match','max_abs_error':error,'scope':'original grid construction + lookup + narrow phase; heap and memset supplied'}
 print(json.dumps(result,indent=2));pathlib.Path(__file__).with_name('terrain-verification.json').write_text(json.dumps(result,indent=2))
