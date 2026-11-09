"""Rider position constraint recovered from original 0x1400cecc0."""
from math import sqrt

def constrain_head(body_position, head_position, forward, up, flipped=False):
    delta=(head_position[0]-body_position[0],head_position[1]-body_position[1])
    # The original dot product adds y products before x products.
    x=forward[1]*delta[1]+forward[0]*delta[0]
    y=up[1]*delta[1]+up[0]*delta[0]
    if flipped:x=-x
    nx,ny=-.22999999999999998,.49
    inv=1.0/sqrt(nx*nx+ny*ny);nx*=inv;ny*=inv
    distance=(y-.13)*ny+(x-(-.35))*nx
    if distance<0.0:x-=nx*distance;y-=ny*distance
    y=min(y,.48);x=max(-.5,min(.26,x))
    length2=x*x*3.4082840236686387+y*y
    if x>0 and y>0 and length2>.2304:
        scale=sqrt(.2304)/sqrt(length2);x*=scale;y*=scale
    if flipped:
        return (up[0]*y-forward[0]*x+body_position[0],up[1]*y-forward[1]*x+body_position[1])
    return (forward[0]*x+up[0]*y+body_position[0],forward[1]*x+up[1]*y+body_position[1])

def head_step(body, head_position, head_velocity, gravity_direction, forward, up, dt, flipped=False):
    """Original rider spring update 0x1400ce460, including clamp-before-integration."""
    hp=constrain_head(body.p,head_position,forward,up,flipped)
    error=(body.p[0]+up[0]*.43999999999999995-hp[0],body.p[1]+up[1]*.43999999999999995-hp[1])
    length=max(1e-7,sqrt(error[0]*error[0]+error[1]*error[1]))
    unit=(error[0]*(1.0/length),error[1]*(1.0/length))
    strength=(length*10000.0)*5.0
    spring=(unit[0]*strength,unit[1]*strength)
    delta=(hp[0]-body.p[0],hp[1]-body.p[1])
    attached_velocity=(-delta[1]*body.omega+body.v[0],delta[0]*body.omega+body.v[1])
    damp=(((head_velocity[0]-attached_velocity[0])*1000.0)*3.0,((head_velocity[1]-attached_velocity[1])*1000.0)*3.0)
    force=(spring[0]-damp[0]+(gravity_direction[0]*body.mass)*10.0,spring[1]-damp[1]+(gravity_direction[1]*body.mass)*10.0)
    inv=1.0/body.mass
    hv=(head_velocity[0]+(force[0]*inv)*dt,head_velocity[1]+(force[1]*inv)*dt)
    return (hp[0]+hv[0]*dt,hp[1]+hv[1]*dt),hv
