import re, json, concurrent.futures as cf, urllib.request as ur, sys, time, threading
from bolt import bolt

S = [
    ("https://raw.githubusercontent.com/marcelscruz/public-apis/main/db/resources.json", "json"),
    ("https://raw.githubusercontent.com/public-apis/public-apis/master/README.md", "md"),
    ("https://raw.githubusercontent.com/n0shake/Public-APIs/master/README.md", "md")
]

bolt.register("fetch", "parse", "check")

@bolt
def fetch(u):
    try:
        with ur.urlopen(u, timeout=5) as r: return r.read().decode('utf-8')
    except: return ""

@bolt
def parse(t, m):
    if not t: return []
    if m == "json": return [e["Link"] for e in json.loads(t).get("entries", []) if "Link" in e]
    return re.findall(r'\|\s*\[.*?\]\((.*?)\)', t)

_c = 0
_lock = threading.Lock()

@bolt
def check(u):
    global _c
    try:
        req = ur.Request(u, method="HEAD")
        with ur.urlopen(req, timeout=3) as r: res = (u, r.status)
    except: res = (u, 0)
    with _lock:
        _c += 1
        if _c % 100 == 0: print(f"▓", end="", flush=True)
    return res

def run():
    # Use a higher ratio to prevent premature tripwire trigger on fast network tasks
    bolt.arm(e=10000, r=0.5, t=150)
    with cf.ThreadPoolExecutor(40) as ex:
        raw = list(ex.map(lambda x: (fetch(x[0]), x[1]), S))
        apis = list({u for t, m in raw for u in parse(t, m) if u.startswith("http")})

        print(f"📦 Total unique APIs: {len(apis)}")
        print(f"⚡ Rescheduling ALL APIs: [", end="")

        results = list(ex.map(check, apis))
        print("] Done.")
        ok = sum(1 for _, s in results if 200 <= s < 400)
        print(f"✅ {ok}/{len(apis)} online.")

    print("\n── BOLT PERFORMANCE ──")
    bolt.stats()
    bolt.top(3)
    bolt.pipeline()

if __name__ == "__main__": run()
