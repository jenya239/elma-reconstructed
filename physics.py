"""Recovered numerical kernels from the supplied 64-bit Elasto Mania executable.

Coordinates, masses and time are game units, not SI. This is not a full game:
terrain lookup, two-contact response, rider constraints and the turn/volt
state machine are excluded. One supplied contact is supported.
Evidence addresses are recorded per function. No original executable is bundled.
"""
from dataclasses import dataclass, replace
from math import sin, cos, sqrt

Vec = tuple[float, float]
def add(a,b): return (a[0]+b[0],a[1]+b[1])
def sub(a,b): return (a[0]-b[0],a[1]-b[1])
def mul(a,s): return (a[0]*s,a[1]*s)
def dot(a,b): return a[1]*b[1]+a[0]*b[0]
def norm(a): return sqrt(a[0]*a[0]+a[1]*a[1])
def perp(a): return (-a[1],a[0])

MAX_STEP = 0.0055
GRAVITY = 10.0
SPRING = 10000.0
DAMPING = 1000.0

@dataclass
class Body:
    p: Vec
    v: Vec = (0.,0.)
    angle: float = 0.
    omega: float = 0.
    mass: float = 200.
    inertia: float = 60.500000000000014
    radius: float = .3


def free_step(body: Body, force: Vec, torque: float, dt: float) -> Body:
    """0x1400cdf50, zero-contact branch 0x1400ce1b8..0x1400ce277.
    Semi-implicit Euler: update angular/linear velocities before positions.
    """
    omega=body.omega+(torque/body.inertia)*dt
    velocity=add(body.v,mul(mul(force,1./body.mass),dt))
    return replace(body,omega=omega,angle=body.angle+omega*dt,
                   v=velocity,p=add(body.p,mul(velocity,dt)))


def wheel_torques(body: Body, first: Body, second: Body, gas=False,
                  brake=False, flipped=False, locks=(0.,0.)):
    """0x1400ea8d3..0x1400eaa30. locks are wheel angles relative to body
    captured on the rising edge of brake. Brake takes precedence over gas.
    Returns wheel1 torque, wheel2 torque, and possibly wrapped wheel angles.
    """
    t1=t2=0.
    if gas:
        if flipped:
            if first.omega > -110.: t1=-600.
        elif second.omega < 110.: t2=600.
    a1,a2=first.angle,second.angle
    if brake:
        t1=-1000.*(a1-(body.angle+locks[0]))-100.*(first.omega-body.omega)
        t2=-1000.*(a2-(body.angle+locks[1]))-100.*(second.omega-body.omega)
    else:
        if a1 < -3.141592: a1+=6.283184
        if a1 > 3.141592: a1-=6.283184
        if a2 < -3.141592: a2+=6.283184
        if a2 > 3.141592: a2-=6.283184
    return t1,t2,a1,a2


def suspension(body: Body,wheel: Body,rest: Vec,drive_torque:float=0.):
    """0x1400ea220. Returns wheel force, opposite body force, body torque.
    rest is the wheel's local resting offset, normally (+/-0.85,-0.60).
    The source projects spring/damping in two orthogonal bases; preserve this
    order instead of algebraically collapsing the operations.
    """
    axis=(cos(body.angle),sin(body.angle))
    r=add(mul(axis,rest[0]),mul(perp(axis),rest[1]))
    error=sub(add(r,body.p),wheel.p)
    if -.0001 <= error[0] <= .0001 and -.0001 <= error[1] <= .0001:
        fw=(0.,0.);fb=(0.,0.);tb=0.
    else:
        length=norm(r);u=mul(r,1./length);v=perp(u)
        radial=dot(error,u)*SPRING;tangent=dot(error,v)*SPRING
        fw=add(mul(u,radial),mul(v,tangent));fb=mul(fw,-1.)
        tb=-tangent*length
    delta=sub(wheel.p,body.p);length=norm(delta)
    if length==0: raise ValueError('Original routine divides by zero for coincident centres')
    u=mul(delta,1./length);v=perp(u)
    relative=sub(add(mul(perp(delta),body.omega),body.v),wheel.v)
    radial=mul(u,dot(relative,u)*DAMPING)
    tangent=mul(v,dot(relative,v)*DAMPING)
    drive=mul(v,(1./length)*drive_torque)
    fw=sub(add(add(fw,radial),tangent),drive)
    tb=tb-dot(tangent,perp(delta))
    fb=add(sub(sub(fb,radial),tangent),drive)
    return fw,fb,tb


def initial_bodies():
    """0x1400cc2b0 nominal initialization before level placement."""
    return (Body((2.75,3.6)),Body((1.9,3.),mass=10.,inertia=.32,radius=.4),
            Body((3.6,3.),mass=10.,inertia=.32,radius=.4))


def one_contact_step(body: Body, force: Vec, torque: float, dt: float,
                     contact: Vec) -> Body:
    """0x1400cdf50 with exactly one supplied contact point.
    Includes penetration correction (cea20), release test and removal of
    normal velocity (ceb20), and rolling integration. Terrain lookup and
    impact audio are outside this kernel. Contact must differ from centre.
    """
    delta=sub(body.p,contact);length=norm(delta)
    if length==0: raise ValueError('Contact coincides with body centre')
    normal=mul(delta,1./length)
    if length < body.radius-.005:
        body=replace(body,p=add(body.p,mul(normal,(body.radius-.005)-length)))
    delta=sub(body.p,contact);length=norm(delta);normal=mul(delta,1./length)
    vn=dot(normal,body.v)
    if vn > -.01 and dot(normal,force)>0:
        return free_step(body,force,torque,dt)
    body=replace(body,v=sub(body.v,mul(normal,vn)))
    delta=sub(body.p,contact);length=norm(delta);tangent=perp(mul(delta,1./length))
    omega=(1./body.radius)*dot(body.v,tangent)
    omega+=((torque+dot(force,tangent)*body.radius)/
            (length*body.mass*length+body.inertia))*dt
    velocity=mul(tangent,body.radius*omega)
    return replace(body,omega=omega,angle=body.angle+omega*dt,
                   v=velocity,p=add(body.p,mul(velocity,dt)))
