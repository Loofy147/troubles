import time,sys,subprocess as sp,cProfile as cp,pstats as ps,io,os;from functools import wraps as rw
_L,_T,_P,_O={},time.perf_counter_ns,{},os.getenv("BOLT_OFF")in{"1","true"}
_W=sys.stderr
try:
 b=os.getenv("BOLT_OUT")
 if b:_W=open(b,"a",1)
except:pass
_f=lambda n:f"{n}ns"if n<1e3 else f"{n/1e3:.1f}µs"if n<1e6 else f"{n/1e6:.1f}ms"if n<1e9 else f"{n/1e9:.3f}s"
_sd=lambda s,m:int(max(0,s[4]/m-(s[1]/m)**2)**.5)
def _e(n,v):
 if n not in _L:_L[n]=[1,v,v,v,v*v];print(f"⚡ {n}  {_f(v)}",file=_W)
 else:
  s=_L[n];s[0]+=1;s[1]+=v;s[4]+=v*v;s[2]=min(s[2],v);s[3]=max(s[3],v);m=s[0]
  if m in{2,5,10,50,100}or m%100==0:print(f"⚡ {n}  ×{m}  μ={_f(s[1]//m)}  σ={_f(_sd(s,m))}  [{_f(s[2])}…{_f(s[3])}]",file=_W)
class bolt:
 __slots__=('_l','_t')
 def __new__(c,x=None,*a,**k):
  if _O:return x(*a,**k)if(callable(x)and(a or k))else x if callable(x)else super().__new__(c)
  if callable(x)and not a and not k:
   @rw(x)
   def w(*a,**k):t=_T();r=x(*a,**k);_e(x.__name__,_T()-t);return r
   return w
  if callable(x):t=_T();r=x(*a,**k);_e(getattr(x,'__name__','fn'),_T()-t);return r
  return super().__new__(c)
 def __init__(s,x="block"):s._l=_P.get(x,f"layer[{x}]")if isinstance(x,int)else x
 __class_getitem__=lambda c,i:c(i)
 def __call__(s,f):
  if _O:return f
  @rw(f)
  def w(*a,**k):t=_T();r=f(*a,**k);_e(s._l,_T()-t);return r
  return w
 def __enter__(s):
  if not _O:s._t=_T()
  return s
 def __exit__(s,*_):
  if not _O:_e(s._l,_T()-s._t)
 @staticmethod
 def register(*l):
  if l:
   if isinstance(l[0],dict):_P.update(l[0])
   else:
    for i,n in(l if isinstance(l[0],(list,tuple))else enumerate(l)):_P[i]=n
 @staticmethod
 def deep(f,*a,**k):
  if _O:return f(*a,**k)
  p=cp.Profile();r=p.runcall(f,*a,**k);s=io.StringIO();ps.Stats(p,stream=s).strip_dirs().sort_stats('cumtime').print_stats(8);print(s.getvalue(),file=_W);return r
 @staticmethod
 def stats(n=None):
  for k,s in({n:_L[n]}if n and n in _L else _L if not n else {}).items():
   m=s[0];print(f"{k:20s} n={m:>5}  μ={_f(s[1]//m)}  σ={_f(_sd(s,m))}  min={_f(s[2])}  max={_f(s[3])}  total={_f(s[1])}")
 @staticmethod
 def pipeline():
  v={n:l[1]//l[0]for n,l in _L.items()if n in _P.values()};t,c=sum(v.values())or 1,0;print("── pipeline ──",file=_W)
  for i in sorted(_P):
   n=_P[i];s=_L.get(n)
   if s:
    a=v[n];c+=a;print(f"  [{i:2d}] {n:20s}  μ={_f(a)}  σ={_f(_sd(s,s[0]))}  {100*a//t:2d}%  cum={_f(c)}",file=_W)
   else:print(f"  [{i:2d}] {n:20s}  —",file=_W)
 @staticmethod
 def top(n=5):
  for k,s in sorted(_L.items(),key=lambda x:-x[1][1]//x[1][0])[:n]:print(f"🔥 {k:20s}  μ={_f(s[1]//s[0])}  n={s[0]}",file=_W)
 reset=staticmethod(lambda:_L.clear())
if __name__=="__main__":
 if len(sys.argv)>1:t=_T();sp.run(sys.argv[1:]);_e("run",_T()-t)
