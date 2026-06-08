import re, json, concurrent.futures as cf, urllib.request as ur, time, collections, threading
from bolt import bolt

S = [
    ("https://raw.githubusercontent.com/marcelscruz/public-apis/main/db/resources.json", "json"),
    ("https://raw.githubusercontent.com/public-apis/public-apis/master/README.md", "md"),
    ("https://raw.githubusercontent.com/n0shake/Public-APIs/master/README.md", "md")
]

bolt.register("collect", "predict", "broadcast", "reschedule", "loop")

class Lib:
    class C:
        _c = {}
        @staticmethod
        @bolt("collect")
        def get(u, t=3):
            if u not in Lib.C._c or time.time()-Lib.C._c[u]['t'] > 300:
                try:
                    req = ur.Request(u, method="HEAD" if "raw" not in u else "GET")
                    with ur.urlopen(req, timeout=t) as r:
                        Lib.C._c[u] = {'s': r.status, 'h': dict(r.headers), 't': time.time(), 'd': r.read() if "raw" in u else b""}
                except: Lib.C._c[u] = {'s': 0, 'h': {}, 't': time.time(), 'd': b""}
            return Lib.C._c[u]

    class P:
        st = {"health": 0.5, "lat": 1.0, "needs": 200, "pressure": 0.0}
        @staticmethod
        @bolt("predict")
        def run(batch):
            h = sum(1 for r in batch if 200<=r['s']<400) / (len(batch) or 1)
            l = sum(r.get('l', 1.0) for r in batch) / (len(batch) or 1)
            Lib.P.st["health"] = Lib.P.st["health"]*0.6 + h*0.4
            Lib.P.st["lat"] = Lib.P.st["lat"]*0.6 + l*0.4
            # PRESSURE: combination of dropping health and rising latency
            Lib.P.st["pressure"] = (1 - Lib.P.st["health"]) * 0.5 + min(1, Lib.P.st["lat"]/10.0) * 0.5
            Lib.P.st["needs"] = int(100 + Lib.P.st["pressure"] * 900)
            return Lib.P.st

    class B:
        @staticmethod
        @bolt("broadcast")
        def emit(st, cycle):
            print(f"📡 [ENTENT] C:{cycle:02d} | H:{st['health']:.1%} | L:{st['lat']:.2f}s | PRESS:{st['pressure']:.1%} | NEXT:{st['needs']}pkts")

    class R:
        @staticmethod
        @bolt("reschedule")
        def flow(apis, st, cycle):
            # Sliding window based on predicted needs
            start = (cycle * 200) % len(apis)
            size = min(len(apis)-start, st["needs"])
            return apis[start:start+size]

_prog = 0
_plock = threading.Lock()

@bolt("loop")
def cycle_task(apis, cycle):
    global _prog
    target = Lib.R.flow(apis, Lib.P.st, cycle)
    _prog = 0
    with cf.ThreadPoolExecutor(64) as ex:
        def probe(u):
            global _prog
            start = time.perf_counter()
            res = Lib.C.get(u, t=2)
            res['l'] = time.perf_counter() - start
            with _plock:
                _prog += 1
                if _prog % 50 == 0: print("▓", end="", flush=True)
            return res
        batch = list(ex.map(probe, target))
    print("] ", end="")
    Lib.B.emit(Lib.P.run(batch), cycle)

def run():
    bolt.arm(e=20000, r=0.5, t=150)
    print("🚀 BOLT SHOWCASE: DYNAMIC STATE-MACHINE BROADCAST")
    print("Collecting ecosystem seeds...")
    raw = [Lib.C.get(s[0]) for s in S]
    apis = []
    for i, r in enumerate(raw):
        t = r['d'].decode('utf-8', 'ignore')
        if S[i][1] == "json": apis.extend([e["Link"] for e in json.loads(t or "{}").get("entries", []) if "Link" in e])
        else: apis.extend(re.findall(r'\|\s*\[.*?\]\((.*?)\)', t or ""))
    apis = list(set(u for u in apis if u.startswith("http")))
    print(f"📦 Tracking {len(apis)} endpoints.")

    for c in range(1, 11):
        print(f"FLOW {c:02d} [", end="", flush=True)
        cycle_task(apis, c)
        time.sleep(0.5)

    print("\n── BOLT PIPELINE SHOWCASE ──")
    bolt.stats()
    bolt.pipeline()

if __name__ == "__main__": run()
