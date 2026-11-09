import json,struct,random,pathlib
from gameplay import *
from oracle import Oracle
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
o=Oracle();o.initialize();LEVEL=o.AUX;OBJ=o.B+0x2000
o.q(0x140708920,LEVEL)
def noop(u,a,s,d):o.ret()
def random_zero(u,a,s,d):u.reg_write(UC_X86_REG_RAX,0);o.ret()
for addr,cb in [(0x14014eda0,random_zero),(0x14010e010,noop)]:o.u.hook_add(UC_HOOK_CODE,cb,begin=addr,end=addr)
world=json.load(open(pathlib.Path(__file__).with_name('original-world.json')))
for level in world['levels']:
 o.initialize();o.u.mem_write(LEVEL,bytes(0x50000))
 for i,obj in enumerate(ordered_objects(level)):
  a=OBJ+i*0x40;o.q(LEVEL+0x3a990+i*8,a);o.vec(a,obj['p']);o.u.mem_write(a+0x20,struct.pack('<ii',obj['type'],obj['gravity']))
 o.call(0x14011a5e0,ints=(LEVEL,o.B));b=spawn(level)
 for off,point in [(0x48,b.body.p),(0xb0,b.wheel1.p),(0x118,b.wheel2.p),(0x158,b.head_position)]:assert o.vec(o.B+off)==point
 assert o.u.reg_read(UC_X86_REG_RAX)==sum(x['type']==2 for x in level['objects'])
r=random.Random(221);o.q(LEVEL+0x3a990,OBJ)
for i in range(1000):
 kind=r.randint(1,4);g=r.randint(0,4);apples=r.randint(0,8);other=r.randint(0,8);total=r.randint(0,16);gravity=r.randint(0,3)
 o.u.mem_write(OBJ+0x20,struct.pack('<ii',kind,g));o.u.mem_write(OBJ+0x2c,struct.pack('<i',1))
 o.u.mem_write(o.B+0x178,struct.pack('<i',apples));o.u.mem_write(o.B+0x1000+0x178,struct.pack('<i',other));o.u.mem_write(0x1406d7f08,struct.pack('<i',total));o.u.mem_write(o.B+0x150,struct.pack('<i',gravity))
 o.call(0x1400e9f60,ints=(0,o.B+0x178,o.B))
 actual=(o.u.reg_read(UC_X86_REG_RAX),struct.unpack('<i',o.u.mem_read(o.B+0x178,4))[0],struct.unpack('<i',o.u.mem_read(o.B+0x150,4))[0])
 assert actual==object_effect({'type':kind,'gravity':g},apples,total,gravity,other)
 if kind==2:assert struct.unpack('<i',o.u.mem_read(OBJ+0x2c,4))[0]==0
result={'placements':55,'object_effect_cases':1000,'result':'Exact original values/status; random animation phase and sound replaced'}
print(json.dumps(result));pathlib.Path(__file__).with_name('gameplay-verification.json').write_text(json.dumps(result,indent=2))
