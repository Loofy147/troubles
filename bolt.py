import time,sys,subprocess as sp,cProfile as cp,pstats as ps,io,os;from functools import wraps as rw
_L,_T,_P,_O={},time.perf_counter_ns,{},os.getenv("BOLT_OFF")in{"1","true","TRUE"}
_W=sys.stderr
try:
 b=os.getenv("BOLT_OUT")
 if b:_W=open(b,"a",1)
except:pass
_f=lambda n:f"{n}ns"if n<1e3 else f"{n/1e3:.1f}µs"if n<1e6 else f"{n/1e6:.1f}ms"if n<1e9 else f"{n/1e9:.3f}s"
_v=lambda s:(s[1]//s[0],int(max(0,s[4]/s[0]-(s[1]/s[0])**2)**.5))
class bolt:
 __slots__=('_l','_t','_sl')
 _S={"n":0,"e":0,"r":0,"t":150,"b":False,"T":0}
 _L=_L
 _P=_P
 def __new__(c,x=None,*a,**k):
  L=c._L
  if _O or c._S["b"]:return x(*a,**k)if(callable(x)and(a or k))else x if callable(x)else super().__new__(c)
  if callable(x):
   w=c._w(x,x.__name__,L)
   return w(*a,**k)if(a or k)else w
  return super().__new__(c)
 def __init__(s,x="block"):
  c=s.__class__;s._sl=c._L;P=c._P
  s._l=P.get(x,f"layer[{x}]")if isinstance(x,int)else x
 __class_getitem__=lambda c,i:c(i)
 def __call__(s,f):return f if (_O or s._S["b"]) else s._w(f,s._l,s._sl)
 def __enter__(s):
  if not _O:s._t=_T()
  return s
 def __exit__(s,*_):
  if not (_O or s._S["b"]):s._e(s._l,_T()-s._t,s._sl)
 @classmethod
 def _e(c,n,v,L):
  s=c._S;s["n"]+=1;s["T"]+=v
  if s["e"]and s["n"]>=s["e"]:L.clear();s["n"]=s["T"]=0;print("⚡ Bolt Epoch Reset",file=_W)
  if s["r"]and s["n"]%1000==0:
   o=s["n"]*s["t"]
   if o/(o+s["T"]or 1)>s["r"]:s["b"]=True;print(f"⚠️ [bolt.TRIPWIRE] '{n}' overhead exceeded {s['r']*100:.1f}%. Telemetry disengaged.",file=_W)
  try:
   st=L[n];st[0]+=1;st[1]+=v;st[4]+=v*v
   if v<st[2]:st[2]=v
   elif v>st[3]:st[3]=v
  except KeyError:L[n]=[1,v,v,v,v*v];print(f"⚡ {n}  {_f(v)}",file=_W)
 @classmethod
 def _w(c,f,n,L):
  @rw(f)
  def w(*a,**k):
   if _O or c._S["b"]:return f(*a,**k)
   t=_T();r=f(*a,**k);c._e(n,_T()-t,L);return r
  return w
 @classmethod
 def arm(c,e=0,r=0,t=None):
  c._S.update({"e":e,"r":r,"n":0,"T":0,"b":False})
  if t is not None:c._S["t"]=t
  else:
   print("⚡ Auto-calibrating Bolt Tax...",file=_W)
   c._S["t"]=c.check(10000);c._S["n"]=c._S["T"]=0
  print(f"🛡️ bolt armed [Epoch: {c._S['e']} | Tripwire: {c._S['r']*100:.1f}% | Tax: {c._S['t']}ns]",file=_W)
 @classmethod
 def register(c,*l):
  P=c._P
  if l:
   if isinstance(l[0],dict):P.update(l[0])
   else:
    it=l if isinstance(l[0],(list,tuple))else enumerate(l)
    for i,n in it:P[i]=n
 @classmethod
 def deep(c,f,*a,**k):
  if _O or c._S["b"]:return f(*a,**k)
  p=cp.Profile();r=p.runcall(f,*a,**k);s=io.StringIO();ps.Stats(p,stream=s).strip_dirs().sort_stats('cumtime').print_stats(8);print(s.getvalue(),file=_W);return r
 @classmethod
 def stats(c,n=None):
  L=c._L
  for k,st in({n:L[n]}if n and n in L else L if not n else {}).items():
   a,d=_v(st);print(f"{k:20s} n={st[0]:>5}  μ={_f(a)}  σ={_f(d)}  min={_f(st[2])}  max={_f(st[3])}  total={_f(st[1])}")
 @classmethod
 def pipeline(c):
  L,P=c._L,c._P
  v={n:l[1]//l[0]for n,l in L.items()if n in P.values()};t,cum=sum(v.values())or 1,0;print("── pipeline ──",file=_W)
  for i in sorted(P):
   n=P[i];st=L.get(n)
   if st:
    a,d=_v(st);cum+=a;print(f"  [{i:2d}] {n:20s}  μ={_f(a)}  σ={_f(d)}  {100*a//t:2d}%  cum={_f(cum)}",file=_W)
   else:print(f"  [{i:2d}] {n:20s}  —",file=_W)
 @classmethod
 def top(c,n=5):
  L=c._L
  for k,st in sorted(L.items(),key=lambda x:-x[1][1]//x[1][0])[:n]:a,d=_v(st);print(f"🔥 {k:20s}  μ={_f(a)}  σ={_f(d)}  n={st[0]}")
 @classmethod
 def check(c,n=100000):
  def f():pass
  o_s=c._S.copy();c._S.update({"e":0,"r":0,"n":0,"T":0,"b":False})
  t=_T();[f()for _ in range(n)];r=(_T()-t)/n
  t=_T();[c(f)()for _ in range(n)];b=(_T()-t)/n
  c._S.update(o_s)
  print(f"⚡ Bolt Tax: {b-r:.1f}ns/call (accuracy: {100*r/b:.1f}%)",file=_W)
  return b-r
 reset=classmethod(lambda c:c._L.clear())
