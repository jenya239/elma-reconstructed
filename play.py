"""Playable desktop shell over recovered physics. Standard-library Tk only.
Rendering, camera and pause UI are ours; original textures/audio not yet used.
"""
import json,math,time,tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from session import Session
from runtime import Runtime
from bike import head_collision_center

class GameWindow:
 def __init__(self,root):
  self.root=root;root.title('Elasto Mania — восстановленная физика');root.geometry('1000x700');root.minsize(600,420)
  world_path=Path(__file__).with_name('original-world.json')
  if not world_path.exists():
   messagebox.showerror('Нужны уровни', 'Сначала извлеките уровни из своей копии игры: python3 world.py --res /путь/elma.res --exe /путь/elma.exe');root.destroy();raise SystemExit(1)
  self.levels=json.loads(world_path.read_text())['levels'][:54]
  self.keys=set();self.paused=True;self.elapsed=0.;self.last=time.perf_counter();self.pending={};self.closed=False
  bar=ttk.Frame(root,padding=10);bar.pack(fill='x')
  self.choice=ttk.Combobox(bar,state='readonly',values=[f"{l['number']}. {l['name']}" for l in self.levels],width=30);self.choice.current(0);self.choice.pack(side='left');self.choice.bind('<<ComboboxSelected>>',lambda e:self.restart())
  self.start=ttk.Button(bar,text='Начать',command=self.toggle);self.start.pack(side='left',padx=10)
  ttk.Button(bar,text='Заново · R',command=self.restart).pack(side='left')
  self.status=tk.StringVar();ttk.Label(root,textvariable=self.status,padding=(10,0,10,8)).pack(anchor='w')
  self.canvas=tk.Canvas(root,bg='#18252d',highlightthickness=0);self.canvas.pack(fill='both',expand=True)
  ttk.Label(root,text='↑ газ   ↓ тормоз   ← → вольты   Пробел разворот   Esc пауза   Enter следующий уровень после финиша\nИсходная физика и трассы · схематический вид',padding=10).pack(anchor='w')
  root.bind('<KeyPress>',self.press);root.bind('<KeyRelease>',self.release);root.bind('<FocusOut>',lambda e:root.after_idle(self.focus_lost));root.protocol('WM_DELETE_WINDOW',self.close)
  self.canvas.bind('<Configure>',lambda e:self.draw());self.canvas.bind('<Button-1>',lambda e:self.canvas.focus_set())
  self.restart();root.after(16,self.loop)
 def close(self):self.closed=True;self.root.destroy()
 def restart(self):
  self.session=Session(self.levels[self.choice.current()]);self.runtime=Runtime(self.session);self.elapsed=0.;self.paused=True;self.keys.clear();self.last=time.perf_counter();self.start.configure(text='Начать');self.canvas.focus_set();self.draw()
 def toggle(self):
  if self.session.dead or self.session.finished:self.restart()
  self.paused=not self.paused;self.last=time.perf_counter();self.start.configure(text='Продолжить' if self.paused else 'Пауза');self.canvas.focus_set();self.draw()
 def focus_lost(self):
  if not self.closed and self.root.focus_displayof() is None:
   self.keys.clear();self.paused=True;self.start.configure(text='Продолжить');self.draw()
 def next_level(self):
  if not self.session.finished or self.session.dead:return
  index=self.choice.current()+1
  if index>=len(self.levels):return
  self.choice.current(index);self.restart();self.toggle()
 def press(self,e):
  key=e.keysym.lower()
  if key in self.pending:self.root.after_cancel(self.pending.pop(key))
  fresh=key not in self.keys;self.keys.add(key)
  if fresh and key=='escape':self.toggle()
  if fresh and key=='r':self.restart()
  if fresh and key in ['return','kp_enter']:self.next_level()
  if key in ['up','down','left','right','space','escape','r','return','kp_enter']:return 'break'
 def release(self,e):
  key=e.keysym.lower()
  def done():self.keys.discard(key);self.pending.pop(key,None)
  self.pending[key]=self.root.after_idle(done)
 def advance(self,seconds):
  if self.paused or self.session.dead or self.session.finished:return
  self.elapsed+=seconds
  self.runtime.frame(self.elapsed*1000,gas='up' in self.keys,brake='down' in self.keys,left='right' in self.keys,right='left' in self.keys,turn='space' in self.keys)
 def loop(self):
  if self.closed:return
  now=time.perf_counter();delta=now-self.last;self.last=now
  # Shell policy: pause on a long stall instead of applying stale held keys.
  if delta>.25:
   self.paused=True;self.keys.clear();self.start.configure(text='Продолжить')
  else:self.advance(delta)
  self.draw();self.root.after(16,self.loop)
 def draw(self):
  if not hasattr(self,'session'):return
  c=self.canvas;c.delete('all');s=self.session;b=s.bike;w=max(c.winfo_width(),1);h=max(c.winfo_height(),1);scale=min(55,w/17,h/10);cx,cy=b.body.p
  def point(p):return ((p[0]-cx)*scale+w*.45,h*.55-(p[1]-cy)*scale)
  def line(a,b,color,width=2):c.create_line(*point(a),*point(b),fill=color,width=width)
  def circle(p,r,color,fill=''):
   x,y=point(p);r*=scale;c.create_oval(x-r,y-r,x+r,y+r,outline=color,width=2,fill=fill)
  for poly in s.level['polygons']:
   if poly['grass']:continue
   pts=[(x,-y) for x,y in poly['vertices']]
   for a,end in zip(pts,pts[1:]+pts[:1]):
    aa,bb=point(a),point(end)
    if max(aa[0],bb[0])<0 or min(aa[0],bb[0])>w or max(aa[1],bb[1])<0 or min(aa[1],bb[1])>h:continue
    line(a,end,'#9dc7a7')
  for obj in s.objects:
   if not obj['active']:continue
   p=obj['p'];x,y=point(p)
   if not (-30<x<w+30 and -30<y<h+30):continue
   if obj['type']==2:circle(p,.2,'#f9c35b','#f9c35b')
   elif obj['type']==3:
    c.create_line(x-10,y-10,x+10,y+10,fill='#f77975',width=4);c.create_line(x-10,y+10,x+10,y-10,fill='#f77975',width=4)
   elif obj['type']==1:
    c.create_rectangle(x-9,y-9,x+9,y+9,outline='#c6a3f7',width=3);c.create_text(x,y-23,text='Финиш',fill='#e8e5f4')
  line(b.wheel1.p,b.body.p,'#6ec8ff',4);line(b.body.p,b.wheel2.p,'#6ec8ff',4);line(b.wheel1.p,b.wheel2.p,'#6ec8ff')
  head=head_collision_center(b.head_position,b.body.angle,b.flipped);line(b.body.p,b.head_position,'#e7ebed',4);line(b.head_position,head,'#e7ebed',3)
  for wheel in [b.wheel1,b.wheel2]:
   circle(wheel.p,wheel.radius,'#e7ebed','#18252d');line(wheel.p,(wheel.p[0]+.34*math.cos(wheel.angle),wheel.p[1]+.34*math.sin(wheel.angle)),'#e7ebed')
  circle(head,.238,'#e7ebed','#18252d')
  seconds=s.time/.43679999999999997;label='Пауза' if self.paused else 'Заезд'
  if s.dead:label='Падение — R, чтобы начать заново'
  elif s.finished:
   action='Enter — следующая трасса' if self.choice.current()+1<len(self.levels) else 'Все трассы пройдены · R — повторить'
   label=f'Финиш: {s.finish_centiseconds/100:.2f} с · {action}'
  self.status.set(f'{label}   |   {seconds:.2f} с   |   Яблоки {s.apples}/{s.total}')
  if self.paused or s.dead or s.finished:c.create_text(w/2,35,text=label,fill='#e7ebed',font=('sans',14))

def main():
 root=tk.Tk();GameWindow(root);root.mainloop()
if __name__=='__main__':main()
