import re, json, concurrent.futures as cf, urllib.request as ur, sys, time
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

@bolt
def check(u):
    try:
        req = ur.Request(u, method="HEAD")
        with ur.urlopen(req, timeout=2) as r: return u, r.status
    except: return u, 0

def run():
    bolt.arm(e=500, r=0.05)
    with cf.ThreadPoolExecutor(16) as ex:
        raw = list(ex.map(lambda x: (fetch(x[0]), x[1]), S))
        apis = {u for t, m in raw for u in parse(t, m) if u.startswith("http")}

        print(f"📦 Total unique APIs: {len(apis)}")
        sample = list(apis)[:50] # Check 50 for a solid performance profile
        print(f"⚡ Rescheduling (health check) {len(sample)} APIs...")

        results = list(ex.map(check, sample))
        ok = sum(1 for _, s in results if 200 <= s < 400)
        print(f"✅ {ok}/{len(sample)} online.")

    print("\n── BOLT PERFORMANCE STATS ──")
    bolt.stats()

if __name__ == "__main__": run()
