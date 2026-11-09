from paths import EXE as ORIGINAL_EXE, RES as ORIGINAL_RES
"""Original REC v131 parser and playback, from 14010c790 / 14010d400.
Replay stores sampled states and events, not enough control inputs to resimulate.
"""
from pathlib import Path
import struct,json,hashlib
from world import Reader,resources
FRAME_RATE=30.0/0.43679999999999997
POSITION_SCALE=1.0/1000.0
BODY_ANGLE_SCALE=1.0/1591.5497620314795
WHEEL_ANGLE_SCALE=1.0/39.78874405078699
COLUMNS=[('body_x','f',0),('body_y','f',8),('wheel1_dx','h',16),('wheel1_dy','h',24),('wheel2_dx','h',32),('wheel2_dy','h',40),('head_dx','h',48),('head_dy','h',56),('body_angle','h',80),('wheel1_angle','B',64),('wheel2_angle','B',72),('flags','B',104),('visual_scale','B',88),('visual_value','B',96)]

def read_replay(data):
 r=Reader(data);n,version,flag,multiplayer,link=r.unpack('iiiii')
 if not 0<n<=0x1a4fc or version!=131:raise ValueError('Only original REC131 single-rider data supported')
 level=r.string(16);columns={};offsets={}
 for name,fmt,_ in COLUMNS:
  offsets[name]=r.pos;columns[name]=list(r.unpack(str(n)+fmt))
 count,=r.unpack('i')
 if not 0<=count<=0xb6d0:raise ValueError('Invalid event count')
 events=[]
 for _ in range(count):
  t,obj,kind,padding,value=r.unpack('dhBBf');events.append(dict(time=t,object_index=obj,type=kind,value=value))
 sentinel,=r.unpack('I')
 if sentinel!=0x492f75 or r.pos!=len(data):raise ValueError('Invalid trailer or unsupported extra rider')
 return dict(frame_count=n,version=version,header_flag=flag,multiplayer=multiplayer,level=level,level_link=link&0xffffffff,columns=columns,column_offsets=offsets,events=events,duration_seconds=(n-1)/30.0,sha256=hashlib.sha256(data).hexdigest())

def sample(rec,time):
 """Playback at original internal game time; one real second = .4368 game units.
 Matches original interpolation, including repeated old-weight multiplication
 in the increasing-wrap branch of the rotation interpolation.
 """
 f=FRAME_RATE*time;i=int(f);w=min(1.0,max(0.0,f-i));old=1.0-w
 n=rec['frame_count'];i=min(n-1,max(0,i));j=min(n-1,max(0,int(f)+1));c=rec['columns']
 def mix(key):return c[key][j]*w+c[key][i]*old
 x,y=mix('body_x'),mix('body_y')
 def rotation(key,limit,period,scale):
  a,b=c[key][i],c[key][j]
  if i<2:return b*scale
  if abs(a-b)>limit:
   if a>b:a-=period
   else:b-=period;a=a*old # exact original double-weight behavior
  return (a*old+b*w)*scale
 flags=c['flags'][i]
 return dict(body=[x,y],wheel1=[mix('wheel1_dx')*POSITION_SCALE+x,mix('wheel1_dy')*POSITION_SCALE+y],wheel2=[mix('wheel2_dx')*POSITION_SCALE+x,mix('wheel2_dy')*POSITION_SCALE+y],head=[mix('head_dx')*POSITION_SCALE+x,mix('head_dy')*POSITION_SCALE+y],body_angle=rotation('body_angle',9000,10000,BODY_ANGLE_SCALE),wheel1_angle=rotation('wheel1_angle',220,250,WHEEL_ANGLE_SCALE),wheel2_angle=rotation('wheel2_angle',220,250,WHEEL_ANGLE_SCALE),flipped=(flags>>1)&1,flag0=flags&1,flag2=(flags>>2)&1,flag3=(flags>>3)&1,visual_scale=c['visual_scale'][i]*(1/250.0)+1.0,visual_value=c['visual_value'][i]*(1/125.0))

def extract_demos(path=ORIGINAL_RES):
 raw=Path(path).read_bytes();out=[]
 for entry in resources(raw):
  if entry['name'].startswith('DEMOR') and entry['name'].endswith('.REC'):
   rec=read_replay(raw[entry['offset']:entry['offset']+entry['size']]);rec['resource']=entry
   # QWQUU006.LEV is the internal menu level number, confirmed via formatter refs.
   rec['internal_level_number']=int(rec['level'][5:8]) if rec['level'].startswith('QWQUU') else None
   out.append(rec)
 return out

if __name__=='__main__':
 demos=extract_demos();Path(__file__).with_name('original-demos.json').write_text(json.dumps(demos,separators=(',',':')))
 print(json.dumps([dict(name=d['resource']['name'],frames=d['frame_count'],events=len(d['events']),level=d['internal_level_number'],duration=d['duration_seconds']) for d in demos]))
