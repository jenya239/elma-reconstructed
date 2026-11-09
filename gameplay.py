"""Original-derived placement, input gating and object effects.
Placement11a5e0, object order115980, effecte9f60, inpute7fb0/e8ae9.
Replay/event queue and multiplayer lifecycle are not reconstructed here.
"""
from dataclasses import dataclass,replace
from physics import *
from bike import Bike,head_collision_center
from controls import VoltState

def ordered_objects(level):
    priority={3:1,2:2,1:3}
    return [dict(o,p=(o['p'][0],-o['p'][1]),active=o['type']!=4)
            for o in sorted(level['objects'],key=lambda o:priority.get(o['type'],10))]

def spawn(level):
    starts=[o for o in level['objects'] if o['type']==4]
    if len(starts)!=1:raise ValueError('Original requires exactly one start')
    p=(starts[0]['p'][0],-starts[0]['p'][1]);b,w1,w2=initial_bodies()
    shift=sub(p,w1.p)
    return Bike(replace(b,p=add(b.p,shift)),replace(w1,p=add(w1.p,shift)),
                replace(w2,p=add(w2.p,shift)),add((2.75,4.04),shift),(0.,0.),VoltState())

@dataclass
class InputState:
    last_volt: float=-100.
    turn_was_down: bool=False

def input_step(state,bike,time,left=False,right=False,turn=False):
    """Held controls -> core volt pulses; original strict 0.4 time cooldown.
    Turn toggles direction on a rising edge, without swapping wheels.
    """
    s=replace(state);b=replace(bike);negative=positive=False
    if s.last_volt+.4<time:
        negative=left;positive=right
        if left or right:s.last_volt=time
    if turn and not s.turn_was_down:b.flipped=not b.flipped
    s.turn_was_down=turn
    return s,b,negative,positive

def object_effect(obj,apples,total,gravity,other_apples=0):
    """Return original status (0 death,1 finish,2 continue), count, gravity.
    Caller updates object active flag after an apple. 0 gravity means unchanged.
    """
    kind=obj['type']
    if kind==3:return 0,apples,gravity
    if kind==2:
        apples+=1
        if obj['gravity'] in (1,2,3,4):gravity=obj['gravity']-1
    elif kind==1 and total<=apples+other_apples:return 1,apples,gravity
    return 2,apples,gravity
