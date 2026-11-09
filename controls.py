"""Original-derived volt state machine, 0x1400eab32..0x1400ead66.
Inputs are the core's pulse flags, NOT raw held keyboard keys.
"""
from dataclasses import dataclass, replace

@dataclass
class VoltState:
    omega: float = 0.0
    negative_active: bool = False
    positive_active: bool = False
    negative_time: float = -1.0
    positive_time: float = -1.0
    negative_saved: float = -1.0
    positive_saved: float = -1.0

def volt_step(state, time, negative, positive, head_position, body_position, head_velocity):
    s = replace(state)
    old = s.omega
    pulse = negative or positive
    if s.negative_active and (pulse or s.negative_time + .4 * .25 < time):
        s.omega = min(12.0 + s.omega, s.negative_saved)
        if s.omega > 0.0:
            s.omega -= 3.0
            if s.omega < 0.0: s.omega = 0.0
        s.negative_active = False
        s.negative_saved = s.negative_time = -1.0
    if s.positive_active:
        if pulse or s.positive_time + .4 * .25 < time:
            s.omega = max(s.omega - 12.0, s.positive_saved)
            if s.omega < 0.0:
                s.omega += 3.0
                if s.omega > 0.0: s.omega = 0.0
            s.positive_active = False
            s.positive_saved = s.positive_time = -1.0
        else:
            return s, head_velocity
    if negative:
        s.negative_saved = s.omega
        s.negative_time = time
        s.negative_active = True
        s.omega -= 12.0
    if positive:
        s.positive_saved = s.omega
        s.positive_time = time
        s.positive_active = True
        s.omega += 12.0
    if pulse:
        delta = s.omega - old
        x,y = head_position[0]-body_position[0], head_position[1]-body_position[1]
        head_velocity = (head_velocity[0]-y*delta, head_velocity[1]+x*delta)
    return s, head_velocity
