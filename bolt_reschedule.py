import re, json, concurrent.futures as cf, urllib.request as ur, time, collections, threading
from bolt import bolt

S = [
    ("https://raw.githubusercontent.com/marcelscruz/public-apis/main/db/resources.json", "json"),
    ("https://raw.githubusercontent.com/public-apis/public-apis/master/README.md", "md"),
    ("https://raw.githubusercontent.com/n0shake/Public-APIs/master/README.md", "md"),
    ("https://raw.githubusercontent.com/cporter202/API-mega-list/main/ai-apis-1208/README.md", "md"),
    ("https://raw.githubusercontent.com/cporter202/API-mega-list/main/agents-apis-697/README.md", "md")
]

bolt.register("collect", "parse", "consensus", "broadcast")

class Lib:
    class C:
        _c = {}
        @staticmethod
        @bolt("collect")
        def get(u, t=5):
            if u not in Lib.C._c or time.time()-Lib.C._c[u]['t'] > 300:
                try:
                    req = ur.Request(u, method="HEAD")
                    with ur.urlopen(req, timeout=t) as r: Lib.C._c[u] = {'s': r.status, 't': time.time()}
                except: Lib.C._c[u] = {'s': 0, 't': time.time()}
            return Lib.C._c[u]

    @staticmethod
    @bolt("parse")
    def parse_all(raw_data):
        apis = []
        for t, m in raw_data:
            if m == "json":
                for e in json.loads(t).get("entries", []):
                    if "Link" in e: apis.append((e["Link"], e.get("Category", "Misc")))
            else:
                cur_cat = "Misc"
                for line in t.split('\n'):
                    h = re.match(r'^#+\s+(.*)', line);
                    if h: cur_cat = h.group(1).strip()
                    l = re.search(r'\|\s*\[.*?\]\((.*?)\)', line)
                    if l: apis.append((l.group(1), cur_cat))
        return apis

    class P:
        @staticmethod
        @bolt("consensus")
        def run(batch):
            groups = collections.defaultdict(list)
            for _, cat, s in batch: groups[cat].append(1 if 200<=s<400 else 0)
            entents = {}
            for cat, votes in groups.items():
                voted_up = sum(votes)
                entents[cat] = {"v": "UP" if voted_up > len(votes)/2 else "DOWN", "c": f"{voted_up}/{len(votes)}"}
            return entents

    class B:
        @staticmethod
        @bolt("broadcast")
        def emit(entents):
            out = [f"{c}:{v['v']}({v['c']})" for c, v in entents.items()]
            print(f"📡 [ENTENTS] " + " | ".join(out[:3]) + (f" (+{len(out)-3})" if len(out)>3 else ""))

def run():
    bolt.arm(e=10000, r=0.5, t=150)
    print("⚡ BOLT COMPACTED CONSENSUS BROADCASTER (MEGA-LIST INTEGRATED)")

    raw = []
    for u, m in S:
        try:
            with ur.urlopen(u, timeout=10) as r: raw.append((r.read().decode('utf-8', 'ignore'), m))
        except: pass

    apis = Lib.parse_all(raw)
    print(f"📦 Combined Ecosystem: {len(apis)} nodes.")

    for cycle in range(5):
        print(f"F{cycle+1:02d} | ", end="", flush=True)
        window = apis[(cycle*300)%len(apis) : ((cycle+1)*300)%len(apis)]
        with cf.ThreadPoolExecutor(60) as ex:
            def probe(item):
                u, cat = item
                res = Lib.C.get(u, t=2)
                return (u, cat, res['s'])
            batch = list(ex.map(probe, window))
        Lib.B.emit(Lib.P.run(batch))
        time.sleep(1)

    bolt.stats()

if __name__ == "__main__": run()
