"""Composition matching original 0x1400ea7f0. Collision queries are supplied by caller."""
from dataclasses import dataclass,replace
from math import sin,cos
from physics import Body,wheel_torques,suspension,free_step,add,mul
from controls import VoltState,volt_step
from head import head_step

@dataclass
class Bike:
    body: Body
    wheel1: Body
    wheel2: Body
    head_position: tuple
    head_velocity: tuple
    volt: VoltState
    flipped: bool=False
    gravity: int=1
    was_brake: bool=False
    locks: tuple=(0.0,0.0)

def head_collision_center(position,angle,flipped):
    f=(cos(angle),sin(angle));u=(-f[1],f[0]);sign=1.0 if flipped else -1.0
    return (position[0]+sign*f[0]*.09+u[0]*.63,position[1]+sign*f[1]*.09+u[1]*.63)

def bike_step(bike,time,dt,gas=False,brake=False,negative=False,positive=False,wheel_step=None):
    """wheel_step(body,force,torque,dt) must provide original collision handling.
    If omitted, the original empty-space case is used for wheels.
    """
    b=replace(bike);body=replace(b.body);w1=replace(b.wheel1);w2=replace(b.wheel2)
    if brake and not b.was_brake:b.locks=(w1.angle-body.angle,w2.angle-body.angle)
    b.was_brake=brake
    t1,t2,w1.angle,w2.angle=wheel_torques(body,w1,w2,gas,brake,b.flipped,b.locks)
    fw1,fb1,tb1=suspension(body,w1,(-.8500000000000001,-.6000000000000001),t1)
    fw2,fb2,tb2=suspension(body,w2,(.8500000000000001,-.6000000000000001),t2)
    b.volt=replace(b.volt,omega=body.omega)
    b.volt,b.head_velocity=volt_step(b.volt,time,negative,positive,b.head_position,body.p,b.head_velocity)
    body.omega=b.volt.omega
    direction=[(0.,1.),(0.,-1.),(-1.,0.),(1.,0.)][b.gravity]
    f=(cos(body.angle),sin(body.angle));up=(-f[1],f[0])
    b.head_position,b.head_velocity=head_step(body,b.head_position,b.head_velocity,direction,f,up,dt,b.flipped)
    gravity=lambda mass:mul(mul(direction,mass),10.0)
    b.body=free_step(body,add(add(fb1,fb2),gravity(body.mass)),tb2+tb1,dt)
    integrate=wheel_step or free_step
    b.wheel1=integrate(w1,add(fw1,gravity(w1.mass)),t1,dt)
    b.wheel2=integrate(w2,add(fw2,gravity(w2.mass)),t2,dt)
    b.volt.omega=b.body.omega
    return b
