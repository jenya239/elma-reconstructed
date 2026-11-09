from paths import EXE as ORIGINAL_EXE, RES as ORIGINAL_RES
"""Read original elma.res index and LEB geometry. No guessed/recreated terrain.
Derived from x64 loader 140140010, level reader 140116f00, and record readers
1400ddd30 (polygon), 1401132d0 (object), 140113950 (picture).
"""
from pathlib import Path
import struct, hashlib, json, argparse, math

def signed16(n): return (n + 32768) % 65536 - 32768

def decode_directory(data):
    out = bytearray(data)
    c, b = 23, 0x26fe
    for i in range(len(out)):
        out[i] ^= c & 255
        c = signed16(c)
        remainder = c - int(c / 3391) * 3391  # C signed remainder, not Python %
        b = signed16(b + remainder * 3391)
        c = signed16(b * 31 + 3391)
    return bytes(out)

def resources(raw):
    count, = struct.unpack_from('<I', raw)
    if not 0 < count <= 3000 or struct.unpack_from('<I',raw,72004)[0] != 0x1490ff:
        raise ValueError('Unsupported resource header')
    directory = decode_directory(raw[4:72004])
    entries = []
    for i in range(count):
        record = directory[i*24:(i+1)*24]
        name = record[:16].split(b'\0',1)[0].decode('ascii')
        size, offset = struct.unpack_from('<II',record,16)
        if offset < 72008 or offset+size > len(raw): raise ValueError('Resource outside file')
        entries.append(dict(name=name,size=size,offset=offset))
    return entries

class Reader:
    def __init__(self,data): self.data=data; self.pos=0
    def take(self,n):
        if self.pos+n>len(self.data): raise ValueError('Truncated record')
        d=self.data[self.pos:self.pos+n];self.pos+=n;return d
    def unpack(self,fmt): return struct.unpack('<'+fmt,self.take(struct.calcsize('<'+fmt)))
    def string(self,n): return self.take(n).split(b'\0',1)[0].decode('latin1')
    def count(self,limit):
        value,=self.unpack('d')
        if not math.isfinite(value) or not 0<=value<=limit:raise ValueError('Invalid count')
        return int(value)  # original cvttsd2si deliberately discards fractional padding

def read_leb(data):
    r=Reader(data)
    if r.take(5)!=b'@@^!@':raise ValueError('Unsupported LEB format')
    reserved,link=r.unpack('HI'); integrity=r.unpack('dddd')
    title=r.string(51);lgr=r.string(16);ground=r.string(10);sky=r.string(10)
    polygon_count,object_count=r.count(30000),r.count(10000)
    polygons=[]
    for _ in range(polygon_count):
        offset=r.pos; grass,n=r.unpack('ii')
        if not 3<=n<=10000:raise ValueError('Invalid vertex count')
        vertices=[list(r.unpack('dd')) for _ in range(n)]
        if not all(math.isfinite(v) for p in vertices for v in p):raise ValueError('Invalid coordinate')
        polygons.append(dict(offset=offset,grass=grass,vertices=vertices))
    objects=[]
    for _ in range(object_count):
        offset=r.pos;x,y,kind,gravity,animation=r.unpack('ddiii')
        objects.append(dict(offset=offset,p=[x,y],type=kind,gravity=gravity,animation=animation))
    pictures=[]
    for _ in range(r.count(50000)):
        offset=r.pos;picture,texture,mask=(r.string(10) for _ in range(3));x,y,distance,clipping=r.unpack('ddii')
        pictures.append(dict(offset=offset,picture=picture,texture=texture,mask=mask,p=[x,y],distance=distance,clipping=clipping))
    return dict(title=title,lgr=lgr,ground=ground,sky=sky,link=link,polygons=polygons,objects=objects,pictures=pictures,parsed_bytes=r.pos,trailing_bytes=len(data)-r.pos)

def extract(res_path,exe_path):
    raw=Path(res_path).read_bytes();exe=Path(exe_path).read_bytes();entries=resources(raw)
    lookup={e['name'].upper():e for e in entries}
    desc=lookup['DESCLIST.TXT'];names=raw[desc['offset']:desc['offset']+desc['size']].decode('ascii').splitlines()
    # Original build's fixed 14-byte internal filename table, after nulla.leb.
    table=exe.index(b'nulla.leb\0\0\0\0\0')
    levels=[]
    for i,name in enumerate(names):
        if not name:continue
        filename=exe[table+(i+1)*14:table+(i+2)*14].split(b'\0',1)[0].decode('ascii')
        entry=lookup[filename.upper()];data=raw[entry['offset']:entry['offset']+entry['size']]
        level=read_leb(data);level.update(number=i+1,name=name,resource=entry,sha256=hashlib.sha256(data).hexdigest());levels.append(level)
    return dict(source_sha256=hashlib.sha256(raw).hexdigest(),exe_sha256=hashlib.sha256(exe).hexdigest(),coordinate_system='Raw original coordinates; preserve exactly. Presentation may invert Y.',resources=entries,levels=levels)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--res',default=ORIGINAL_RES);ap.add_argument('--exe',default=ORIGINAL_EXE);ap.add_argument('--out',default=str(Path(__file__).with_name('original-world.json')));a=ap.parse_args()
    result=extract(a.res,a.exe);Path(a.out).write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
    print(json.dumps({'levels':len(result['levels']),'polygons':sum(len(l['polygons']) for l in result['levels']),'objects':sum(len(l['objects']) for l in result['levels']),'out':a.out}))
