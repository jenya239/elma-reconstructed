"""Original-derived segment narrow phase and 0/1/2-point contact solver.
Query 0x14011a9b0; response 0x1400cdf50; selection ce7a0 / ce8e0.
Broad-phase segment selection/order is supplied by caller, not recovered here.
"""
from dataclasses import dataclass,replace
from physics import *
@dataclass
class Segment:
    start: Vec
    axis: Vec
    length: float
    @classmethod
    def endpoints(cls,a,b):
        delta=sub(b,a);length=norm(delta)
        if length==0:raise ValueError('Zero-length segment')
        return cls(a,mul(delta,1./length),length)

def query_contacts(position,radius,segments,merge_distance=.1):
    """Ordered candidate segments -> up to two contact points.
    Interior uses inclusive distance; endpoints use strict radius.
    Nearby contacts merge repeatedly; return immediately on two distinct hits.
    """
    contacts=[]
    for s in segments:
        relative=sub(position,s.start);along=dot(relative,s.axis)
        if along<0:
            if norm(relative)>=radius:continue
            point=s.start
        elif along<=s.length:
            distance=dot(relative,perp(s.axis))
            if not -radius<=distance<=radius:continue
            point=add(s.start,mul(s.axis,along))
        else:
            end=add(s.start,mul(s.axis,s.length))
            if norm(sub(position,end))>=radius:continue
            point=end
        if not contacts:contacts.append(point)
        elif norm(sub(contacts[0],point))>=merge_distance:
            contacts.append(point);return contacts
        else:contacts[0]=mul(add(contacts[0],point),.5)
    return contacts

def push_out(b,point):
    delta=sub(b.p,point);length=norm(delta)
    if length==0:raise ValueError('Contact coincides with centre')
    normal=mul(delta,1./length)
    if length<b.radius-.005:b=replace(b,p=add(b.p,mul(normal,(b.radius-.005)-length)))
    return b

def retain(b,point,force,event=None):
    delta=sub(b.p,point);normal=mul(delta,1./norm(delta));vn=dot(normal,b.v)
    if vn>-.01 and dot(normal,force)>0:return b,False
    removed=mul(normal,vn)
    impact=norm(removed)
    if event is not None and impact>1.5:event(1,min(.99,(impact/.8)*.1),-1)
    return replace(b,v=sub(b.v,removed)),True

def selection(first,second,b,force,torque,fast):
    delta=sub(b.p,second);length=norm(delta);tangent=perp(mul(delta,1./length))
    projected=dot(mul(tangent,length),b.v if fast else force)
    return (projected+(b.omega if fast else torque))*dot(sub(first,second),tangent)>=0

def rolling(b,point,force,torque,dt):
    delta=sub(b.p,point);length=norm(delta);tangent=perp(mul(delta,1./length))
    omega=(1./b.radius)*dot(b.v,tangent)
    omega+=((torque+dot(force,tangent)*b.radius)/(length*b.mass*length+b.inertia))*dt
    velocity=mul(tangent,b.radius*omega)
    return replace(b,omega=omega,angle=b.angle+omega*dt,v=velocity,p=add(b.p,mul(velocity,dt)))

def contact_step(b,force,torque,dt,contacts,event=None):
    if len(contacts)>2:raise ValueError('Original narrow phase returns at most two contacts')
    if not contacts:return free_step(b,force,torque,dt)
    n=len(contacts);first=contacts[0];second=contacts[1] if n==2 else (0.,0.)
    b=push_out(b,first)
    if n==2:
        b=push_out(b,second)
        if norm(b.v)>1:
            if not selection(first,second,b,force,torque,True):first=second;n=1
            elif not selection(second,first,b,force,torque,True):n=1
        if n==2:
            if norm(b.v)<1:
                if not selection(first,second,b,force,torque,False):first=second;n=1
                elif not selection(second,first,b,force,torque,False):n=1
            if n==2:
                b,keep=retain(b,second,force,event)
                if not keep:n=1
    b,keep=retain(b,first,force,event)
    if not keep:
        if n!=2:return free_step(b,force,torque,dt)
        first=second
    elif n==2:return replace(b,v=(0.,0.),omega=0.)
    return rolling(b,first,force,torque,dt)
