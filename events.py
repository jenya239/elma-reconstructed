"""Original event collection and FIFO, 10e010/10c540/eb770/11ad40.
Model inputs preserve original object ordering and cached coarse coordinates.
"""
from dataclasses import dataclass,field
from physics import sub,dot
from gameplay import object_effect

@dataclass
class EventQueue:
    items:list=field(default_factory=list)
    def push(self,kind,value=0.,object_index=-1):
        if len(self.items)<200:self.items.append((kind,value,object_index))
    def pop(self):return self.items.pop(0) if self.items else None

def object_query(position,radius,objects,pixel_position,ignore_finish=False):
    x,y=pixel_position
    for i,o in enumerate(objects):
        if o is None:return -1
        if not o['active'] or (ignore_finish and o['type']==1):continue
        ox,oy=o['pixel']
        if not x-1000<=ox<=x+1000 or not y-1000<=oy<=y+1000:continue
        delta=sub(position,o['p'])
        if dot(delta,delta)<(radius+.4)*(radius+.4):return i
    return -1

def collect_objects(probes,objects,queue,terrain_hit=False,ignore_finish=False):
    """probes are wheel1,wheel2,head: (position,radius,pixel_position).
    Queries all three before processing results; apples deduplicate per call.
    Non-apple contacts may repeat across probes/passes, as in the original.
    """
    if terrain_hit:return 0
    seen=set()
    while True:
        hits=[object_query(p,r,objects,pixel,ignore_finish) for p,r,pixel in probes]
        repeat=False
        for idx in hits:
            if idx<0 or idx in seen:continue
            queue.push(0,0.,idx)
            if objects[idx]['type']==2:
                objects[idx]['active']=False;repeat=True;seen.add(idx)
        if not repeat:return 2

def drain_events(queue,objects,apples,total,gravity,other_apples=0):
    """Main-loop e8332..e8396 order. Continues draining after death/finish.
    Apple handling appends its sound event to the same FIFO.
    Returns state and every consumed event (also destined for replay).
    """
    death=False;finish=False;consumed=[]
    while queue.items:
        event=queue.pop();kind,value,idx=event;consumed.append(event)
        if idx>=0:
            o=objects[idx];status,apples,gravity=object_effect(o,apples,total,gravity,other_apples)
            if o['type']==2:
                o['active']=False;queue.push(4,.99,-1)
            if status==0:death=True
            if status==1:finish=True
    return {'apples':apples,'gravity':gravity,'dead':death,'finished':finish,'events':consumed}
