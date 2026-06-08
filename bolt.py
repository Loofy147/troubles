import time,sys,subprocess as sp,cProfile as cp,pstats as ps,io,os;from functools import wraps as rw
_L,_T,_P,_O={},time.perf_counter_ns,{},os.getenv("BOLT_OFF")in{"1","true"}
_W=sys.stderr
try:
 b=os.getenv("BOLT_OUT")
 if b:_W=open(b,"a",1)
except:pass
_f=lambda n:f"{n}ns"if n<1e3 else f"{n/1e3:.1f}µs"if n<1e6 else f"{n/1e6:.1f}ms"if n<1e9 else f"{n/1e9:.3f}s"
_v=lambda s:(s[1]//s[0],int(max(0,s[4]/s[0]-(s[1]/s[0])**2)**.5))
def _e(n,v,L):
 s=L.get(n)
 if s:
  s[0]+=1;s[1]+=v;s[4]+=v*v
  if v<s[2]:s[2]=v
  elif v>s[3]:s[3]=v
 else:L[n]=[1,v,v,v,v*v];print(f"⚡ {n}  {_f(v)}",file=_W)
def _w(f,n,L):
 @rw(f)
 def w(*a,**k):t=_T();r=f(*a,**k);_e(n,_T()-t,L);return r
 return w
class bolt:
 __slots__=('_l','_t','_sl')
 def __new__(c,x=None,*a,**k):
  L=getattr(c,'_L',_L)
  if _O:return x(*a,**k)if(callable(x)and(a or k))else x if callable(x)else super().__new__(c)
  if callable(x):return _w(x,x.__name__,L)(*a,**k)if(a or k)else _w(x,x.__name__,L)
  return super().__new__(c)
 def __init__(s,x="block"):
  c=s.__class__;s._sl=getattr(c,'_L',_L);P=getattr(c,'_P',_P)
  s._l=P.get(x,f"layer[{x}]")if isinstance(x,int)else x
 __class_getitem__=lambda c,i:c(i)
 def __call__(s,f):return f if _O else _w(f,s._l,s._sl)
 def __enter__(s):
  if not _O:s._t=_T()
  return s
 def __exit__(s,*_):
  if not _O:_e(s._l,_T()-s._t,s._sl)
 @classmethod
 def register(c,*l):
  P=getattr(c,'_P',_P)
  if l:
   if isinstance(l[0],dict):P.update(l[0])
   else:
    it=l if isinstance(l[0],(list,tuple))else enumerate(l)
    for i,n in it:P[i]=n
 @classmethod
 def deep(c,f,*a,**k):
  if _O:return f(*a,**k)
  p=cp.Profile();r=p.runcall(f,*a,**k);s=io.StringIO();ps.Stats(p,stream=s).strip_dirs().sort_stats('cumtime').print_stats(8);print(s.getvalue(),file=_W);return r
 @classmethod
 def stats(c,n=None):
  L=getattr(c,'_L',_L)
  for k,s in({n:L[n]}if n and n in L else L if not n else {}).items():
   a,d=_v(s);print(f"{k:20s} n={s[0]:>5}  μ={_f(a)}  σ={_f(d)}  min={_f(s[2])}  max={_f(s[3])}  total={_f(s[1])}")
 @classmethod
 def pipeline(c):
  L,P=getattr(c,'_L',_L),getattr(c,'_P',_P)
  v={n:l[1]//l[0]for n,l in L.items()if n in P.values()};t,cum=sum(v.values())or 1,0;print("── pipeline ──",file=_W)
  for i in sorted(P):
   n=P[i];s=L.get(n)
   if s:
    a,d=_v(s);cum+=a;print(f"  [{i:2d}] {n:20s}  μ={_f(a)}  σ={_f(d)}  {100*a//t:2d}%  cum={_f(cum)}",file=_W)
   else:print(f"  [{i:2d}] {n:20s}  —",file=_W)
 @classmethod
 def top(c,n=5):
  L=getattr(c,'_L',_L)
  for k,s in sorted(L.items(),key=lambda x:-x[1][1]//x[1][0])[:n]:a,d=_v(s);print(f"🔥 {k:20s}  μ={_f(a)}  σ={_f(d)}  n={s[0]}")
 @classmethod
 def check(c,n=100000):
  def f():pass
  t=_T();[f()for _ in range(n)];r=(_T()-t)/n
  t=_T();[c(f)()for _ in range(n)];b=(_T()-t)/n
  print(f"⚡ Bolt Tax: {b-r:.1f}ns/call (accuracy: {100*r/b:.1f}%)",file=_W)
  return b-r
 reset=classmethod(lambda c:getattr(c,'_L',_L).clear())
