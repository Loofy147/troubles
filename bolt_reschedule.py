import re, json, concurrent.futures as cf, urllib.request as ur, time, collections
from bolt import bolt

S = [
    ("https://raw.githubusercontent.com/marcelscruz/public-apis/main/db/resources.json", "json"),
    ("https://raw.githubusercontent.com/public-apis/public-apis/master/README.md", "md"),
    ("https://raw.githubusercontent.com/n0shake/Public-APIs/master/README.md", "md")
]

# Register with explicit names used in methods
bolt.register("collect", "predict", "broadcast", "reschedule", "loop")

class Lib:
    class C:
        _c = {}
        @staticmethod
        @bolt("collect")
        def get(u, t=5):
            if u not in Lib.C._c or time.time()-Lib.C._c[u]['t'] > 60:
                try:
                    req = ur.Request(u, method="HEAD" if "raw" not in u else "GET")
                    with ur.urlopen(req, timeout=t) as r:
                        Lib.C._c[u] = {'s': r.status, 'h': dict(r.headers), 't': time.time(), 'd': r.read() if "raw" in u else b""}
                except: Lib.C._c[u] = {'s': 0, 'h': {}, 't': time.time(), 'd': b""}
            return Lib.C._c[u]

    class P:
        st = {"health": 0.5, "lat": 1.0, "needs": 100}
        @staticmethod
        @bolt("predict")
        def run(batch):
            h = sum(1 for r in batch if 200<=r['s']<400) / (len(batch) or 1)
            l = sum(r.get('l', 1.0) for r in batch) / (len(batch) or 1)
            Lib.P.st["health"] = Lib.P.st["health"]*0.7 + h*0.3
            Lib.P.st["lat"] = Lib.P.st["lat"]*0.7 + l*0.3
            Lib.P.st["needs"] = int(100 + (1 - Lib.P.st["health"]) * 900)
            return Lib.P.st

    class B:
        @staticmethod
        @bolt("broadcast")
        def emit(st):
            print(f"📡 [ENTENT] H:{st['health']:.1%} | L:{st['lat']:.2f}s | Next_Window:{st['needs']}pkts")

    class R:
        @staticmethod
        @bolt("reschedule")
        def flow(apis, st):
            size = min(len(apis), st["needs"])
            return apis[:size]

@bolt("loop")
def cycle_task(apis):
    target = Lib.R.flow(apis, Lib.P.st)
    with cf.ThreadPoolExecutor(50) as ex:
        def probe(u):
            start = time.perf_counter()
            res = Lib.C.get(u, t=3)
            res['l'] = time.perf_counter() - start
            return res
        batch = list(ex.map(probe, target))
    Lib.B.emit(Lib.P.run(batch))

def run():
    bolt.arm(e=10000, r=0.5, t=150)
    print("⚡ BOLT ENHANCED M:N FLOW ACTIVE")
    raw = [Lib.C.get(s[0]) for s in S]
    apis = []
    for i, r in enumerate(raw):
        t = r['d'].decode('utf-8', 'ignore')
        if S[i][1] == "json": apis.extend([e["Link"] for e in json.loads(t or "{}").get("entries", []) if "Link" in e])
        else: apis.extend(re.findall(r'\|\s*\[.*?\]\((.*?)\)', t or ""))
    apis = list(set(u for u in apis if u.startswith("http")))

    for c in range(5):
        print(f"Cycle {c+1:02d} | ", end="")
        cycle_task(apis)
        time.sleep(1)

    print("\n── BOLT PIPELINE OBSERVABILITY ──")
    bolt.stats()
    bolt.pipeline()

if __name__ == "__main__": run()
