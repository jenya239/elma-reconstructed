"""Desktop smoke test: real Tk key events, frame advance, pause, death, restart."""
import tkinter as tk,json,pathlib
from play import GameWindow

def main():
 root=tk.Tk();app=GameWindow(root);root.update();root.focus_force();app.canvas.focus_set();root.update()
 initial=app.session.bike.body.p
 app.start.invoke();app.canvas.event_generate('<KeyPress-Up>');root.update();assert 'up' in app.keys
 for _ in range(20):app.advance(1/60)
 assert app.session.bike.body.p!=initial and not app.session.dead
 app.canvas.event_generate('<KeyPress-space>');root.update();app.advance(1/60);assert app.session.bike.flipped
 app.canvas.event_generate('<KeyPress-space>');root.update();app.advance(1/60);assert app.session.bike.flipped
 app.canvas.event_generate('<KeyRelease-space>');root.update();app.advance(1/60)
 app.canvas.event_generate('<KeyPress-space>');root.update();app.advance(1/60);assert not app.session.bike.flipped
 app.draw();root.update()
 if __import__('os').environ.get('ELMA_SCREENSHOT'):
  from PIL import ImageGrab
  x,y=root.winfo_rootx(),root.winfo_rooty();ImageGrab.grab(bbox=(x,y,x+root.winfo_width(),y+root.winfo_height())).save(__import__('os').environ['ELMA_SCREENSHOT'])
 app.toggle();before=app.session.time;app.advance(.1);assert app.session.time==before
 app.restart();assert app.paused and app.session.time==0 and not app.keys
 app.start.invoke();app.keys.add('up');app.advance(5);assert app.session.dead
 app.restart();app.choice.current(5);app.choice.event_generate('<<ComboboxSelected>>');root.update();assert app.session.level['name']=='Long Haul'
 app.start.invoke();app.advance(.1);assert app.session.time>0
 # Enter is gated by successful completion, and never wraps past level 54.
 app.canvas.event_generate('<KeyPress-Return>');root.update();assert app.choice.current()==5
 app.canvas.event_generate('<KeyRelease-Return>');root.update()
 app.session.finished=True;app.session.finish_centiseconds=1234
 app.canvas.event_generate('<KeyPress-Return>');root.update()
 assert app.choice.current()==6 and not app.paused and not app.session.finished and not app.keys
 app.choice.current(53);app.restart();app.session.finished=True;app.session.finish_centiseconds=1234
 app.canvas.event_generate('<KeyPress-Return>');root.update();assert app.choice.current()==53
 app.close()
 result=dict(result='Passed',checks=['keyboard gas','turn edge and held repeat','pause','death','restart','level change','Enter only after finish','Enter starts next level','last level does not wrap'],levels_available=len(app.levels))
 pathlib.Path(__file__).with_name('play-verification.json').write_text(json.dumps(result,indent=2));print(result)
if __name__=='__main__':main()
