"""Normal-speed single-player frame adapter, recovered from e86e4..e8991.
UI pause/focus handling is supplied by our desktop shell, not original menus.
"""
import math
from gameplay import input_step
EPSILON=1e-6
MAX_STEP=.0055

def frame_steps(time,elapsed_ms):
    if not math.isfinite(elapsed_ms) or elapsed_ms<0:raise ValueError('Invalid elapsed milliseconds')
    target=max(EPSILON,(int(elapsed_ms)*.182)*.0024)
    while target-EPSILON>=time:
        dt=MAX_STEP
        if time+MAX_STEP>target:dt=target-time
        yield time,dt
        time+=dt

class Runtime:
    def __init__(self,session):self.session=session
    def frame(self,elapsed_ms,**controls):
        s=self.session;events=[]
        if s.dead or s.finished:return events
        turn=controls.pop('turn',False)
        for time,dt in frame_steps(s.time,elapsed_ms):
            events.extend(s.step(dt=dt,turn=s.input.turn_was_down,**controls))
            if s.dead or s.finished:return events
        # Original checks the turn edge after the substep batch.
        s.input,s.bike,_,_=input_step(s.input,s.bike,s.time,turn=turn)
        return events
