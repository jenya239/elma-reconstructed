"""Single-player substep compared with original e7fb0 and turn-edge fragment.
See session-verification.json for tested scenarios; window lifecycle excluded.
No display/audio/replay-file lifecycle. Time is internal game time.
"""
from bike import bike_step,head_collision_center
from gameplay import spawn,ordered_objects,input_step,InputState
from terrain import Terrain
from collision import contact_step
from events import EventQueue,collect_objects,drain_events
class Session:
 def __init__(self,level):
  self.level=level;self.terrain=Terrain.polygons(level['polygons']);self.bike=spawn(level)
  self.objects=ordered_objects(level)
  for o in self.objects:o['pixel']=(int(o['p'][0]*100.),int(o['p'][1]*100.))
  self.total=sum(o['type']==2 for o in self.objects);self.apples=0;self.input=InputState();self.time=0.;self.dead=False;self.finished=False;self.finish_centiseconds=None;self.events=EventQueue()
 def step(self,dt=.0055,gas=False,brake=False,left=False,right=False,turn=False):
  if self.dead or self.finished:return []
  if not 0<dt<=.0055:raise ValueError('Original max physics substep is .0055')
  self.input,self.bike,negative,positive=input_step(self.input,self.bike,self.time,left,right,turn)
  if negative:self.events.push(6,.99,-1)
  if positive:self.events.push(7,.99,-1)
  def wheel(w,f,t,dt):return contact_step(w,f,t,dt,self.terrain.contacts(w.p,w.radius),self.events.push)
  self.bike=bike_step(self.bike,self.time,dt,gas,brake,negative,positive,wheel)
  head=head_collision_center(self.bike.head_position,self.bike.body.angle,self.bike.flipped)
  if self.terrain.contacts(head,.238):
   self.dead=True;self.time+=dt;return []
  probes=[(b.p,b.radius,(int(b.p[0]*100.),int(b.p[1]*100.))) for b in [self.bike.wheel1,self.bike.wheel2]]
  probes.append((head,.238,(int(head[0]*100.),int(head[1]*100.))))
  collect_objects(probes,self.objects,self.events)
  result=drain_events(self.events,self.objects,self.apples,self.total,self.bike.gravity)
  self.apples=result['apples'];self.bike.gravity=result['gravity'];self.dead=result['dead'];self.finished=result['finished'];
  if self.finished:self.finish_centiseconds=int((self.time*100.)/.43679999999999997)
  self.time+=dt
  return result['events']
