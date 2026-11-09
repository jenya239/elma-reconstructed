"""Original 1-unit collision grid, recovered from 111c60/111450/111a40.
Bounds padded by six units; candidates keep polygon/edge insertion order.
"""
from collision import *
class Terrain:
 def __init__(self,edges,margin=.4):
  self.edges=list(edges)
  if not self.edges:raise ValueError('Original grid requires nonempty geometry')
  self.segments=[Segment.endpoints(a,b) for a,b in self.edges]
  self.origin=tuple(min(p[k] for e in self.edges for p in e)-6. for k in (0,1))
  high=tuple(max(p[k] for e in self.edges for p in e)+6. for k in (0,1))
  self.size=tuple(int(high[k]-self.origin[k]+1.) for k in (0,1))
  if max(self.size)>200:raise ValueError('Original grid limit is 200 cells per axis')
  self.cells={};padding=margin*1.5
  for idx,(a,b) in enumerate(self.edges):
   x,y=sub(a,self.origin);dx,dy=sub(b,a);swap=abs(dy)>abs(dx)
   if swap:x,y,dx,dy=y,x,dy,dx
   if dx<0:x+=dx;y+=dy;dx=-dx;dy=-dy
   slope=dy/dx;intercept=y-slope*x
   for i in range(max(0,int(x-padding)),int(x+dx+padding)+1):
    y1=i*slope+intercept;y2=(i+1)*slope+intercept
    lo=min(y1,y2)-padding;hi=max(y1,y2)+padding
    if hi<0:raise ValueError('Original insertion rejects negative range')
    for j in range(max(0,int(lo)),int(hi)+1):
     cell=(j,i) if swap else (i,j)
     if cell[0]<self.size[0] and cell[1]<self.size[1]:self.cells.setdefault(cell,[]).append(idx)
 def candidates(self,p):
  cell=[max(0,int(p[k]-self.origin[k])) for k in (0,1)]
  for k in (0,1):
   if cell[k]>self.size[k]:raise ValueError('Position exceeds original grid bounds')
   if cell[k]==self.size[k]:cell[k]-=1
  return self.cells.get(tuple(cell),[])
 def contacts(self,p,radius):return query_contacts(p,radius,[self.segments[i] for i in self.candidates(p)])
 @classmethod
 def polygons(cls,polygons,margin=.4):
  edges=[]
  for poly in polygons:
   if poly['grass']:continue
   points=[(v[0],-v[1]) for v in poly['vertices']]
   edges.extend(zip(points,points[1:]+points[:1]))
  return cls(edges,margin)
