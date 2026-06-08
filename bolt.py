import time,sys,subprocess as sp,cProfile,pstats,io,os;from functools import wraps
_log,_T,_PIPE={},time.perf_counter_ns,{}
_OFF=os.getenv("BOLT_OFF") in{"1","true","TRUE"}
_OUT=sys.stderr
try:
 _BO=os.getenv("BOLT_OUT")
 if _BO:_OUT=open(_BO,"a",1)
except:pass
def _fmt(ns):
 if ns<1000:return f"{ns}ns"
 if ns<1e6:return f"{ns/1e3:.1f}µs"
 if ns<1e9:return f"{ns/1e6:.1f}ms"
 return f"{ns/1e9:.3f}s"
def _emit(n,ns):
 if n not in _log:_log[n]=[1,ns,ns,ns,ns*ns];print(f"⚡ {n}  {_fmt(ns)}",file=_OUT)
 else:
  s=_log[n];s[0]+=1;s[1]+=ns;s[4]+=ns*ns
  if ns<s[2]:s[2]=ns
  if ns>s[3]:s[3]=ns
  m=s[0]
  if m in{2,5,10,50,100} or m%100==0:
   avg=s[1]//m;sd=int(max(0,s[4]/m-(s[1]/m)**2)**.5)
   print(f"⚡ {n}  ×{m}  μ={_fmt(avg)}  σ={_fmt(sd)}  [{_fmt(s[2])}…{_fmt(s[3])}]",file=_OUT)
class bolt:
 __slots__=('_l','_t')
 def __new__(cls,x=None,*a,**k):
  if _OFF:
   if callable(x):return x(*a,**k) if(a or k)else x
   return super().__new__(cls)
  if callable(x) and not a and not k:
   @wraps(x)
   def w(*a,**k):t=_T();r=x(*a,**k);_emit(x.__name__,_T()-t);return r
   return w
  if callable(x):t=_T();r=x(*a,**k);_emit(getattr(x,'__name__','fn'),_T()-t);return r
  return super().__new__(cls)
 def __init__(self,x="block"):self._l=_PIPE.get(x,f"layer[{x}]") if isinstance(x,int) else x
 def __class_getitem__(cls,idx):return cls(idx)
 def __call__(self,f):
  if _OFF:return f
  @wraps(f)
  def w(*a,**k):t=_T();r=f(*a,**k);_emit(self._l,_T()-t);return r
  return w
 def __enter__(self):
  if not _OFF:self._t=_T()
  return self
 def __exit__(self,*_):
  if not _OFF:_emit(self._l,_T()-self._t)
 @staticmethod
 def register(*layers):
  if not layers:return
  if isinstance(layers[0],dict):_PIPE.update(layers[0]);return
  it=layers if isinstance(layers[0],(list,tuple)) else enumerate(layers)
  for i,n in it:_PIPE[i]=n
 @staticmethod
 def deep(f,*a,top=8,**k):
  if _OFF:return f(*a,**k)
  pr=cProfile.Profile();r=pr.runcall(f,*a,**k);s=io.StringIO();pstats.Stats(pr,stream=s).strip_dirs().sort_stats('cumtime').print_stats(top);print(s.getvalue(),file=_OUT);return r
 @staticmethod
 def stats(n=None):
  for k,s in({n:_log[n]} if n and n in _log else _log if not n else {}).items():
   avg=s[1]//s[0];sd=int(max(0,s[4]/s[0]-(s[1]/s[0])**2)**.5)
   print(f"{k:20s} n={s[0]:>5}  μ={_fmt(avg)}  σ={_fmt(sd)}  min={_fmt(s[2])}  max={_fmt(s[3])}  total={_fmt(s[1])}")
 @staticmethod
 def pipeline():
  avgs={n:l[1]//l[0] for n,l in _log.items() if n in _PIPE.values()}
  total=sum(avgs.values()) or 1;cum=0
  print("── pipeline ──",file=_OUT)
  for idx in sorted(_PIPE):
   n=_PIPE[idx];s=_log.get(n)
   if s:
    avg=avgs[n];cum+=avg;sd=int(max(0,s[4]/s[0]-(s[1]/s[0])**2)**.5)
    print(f"  [{idx:2d}] {n:20s}  μ={_fmt(avg)}  σ={_fmt(sd)}  {100*avg//total:2d}%  cum={_fmt(cum)}",file=_OUT)
   else:print(f"  [{idx:2d}] {n:20s}  —",file=_OUT)
 @staticmethod
 def top(n=5):
  for k,s in sorted(_log.items(),key=lambda x:-x[1][1]//x[1][0])[:n]:
   print(f"🔥 {k:20s}  μ={_fmt(s[1]//s[0])}  n={s[0]}",file=_OUT)
 @staticmethod
 def reset():_log.clear()
if __name__=="__main__":
 if len(sys.argv)>1:t=_T();sp.run(sys.argv[1:]);_emit("run",_T()-t)
