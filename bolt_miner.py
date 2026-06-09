import asyncio, json, hashlib, binascii, struct, time, sys, ssl, multiprocessing as mp
from bolt import bolt

bolt.register({20:"Stratum Connect", 21:"Job Setup", 22:"Control Plane", 23:"Share Submission"})

def hasher(h_fix, target_bytes, n_start, result_queue, stop_event, hashes_val):
    header, sha, pack = bytearray(h_fix + b'\x00'*4), hashlib.sha256, struct.pack_into
    n, local = n_start, 0
    try:
        while not stop_event.is_set():
            for _ in range(5000):
                pack("<I", header, 76, n)
                if sha(sha(header).digest()).digest()[::-1] < target_bytes:
                    result_queue.put(n)
                n = (n + 1) & 0xffffffff
            local += 5000
            if local >= 100000:
                with hashes_val.get_lock(): hashes_val.value += local
                local = 0
    finally:
        with hashes_val.get_lock(): hashes_val.value += local

class BoltMiner:
    def __init__(self, url, worker, password="123"):
        self.url, self.worker, self.password = url, worker, password
        self.extranonce1, self.extranonce2_size = "", 4
        self.target = (1 << 256) - 1
        self.reader, self.writer = None, None
        self.processes, self.stop_event, self.result_queue = [], mp.Event(), mp.Queue()
        self.hashes, self.start_time = mp.Value('Q', 0), time.time()
        self.cur_job, self.cur_ntime = None, None

    async def send(self, m, p, i=1):
        try:
            line = json.dumps({"id": i, "method": m, "params": p}) + "\n"
            self.writer.write(line.encode()); await self.writer.drain()
            print(f">>> {line.strip()}")
        except: pass

    async def run(self):
        try:
            with bolt[20]:
                u = self.url.split("://")[-1].split(":")
                host, port = u[0], int(u[1])
                ctx = ssl.create_default_context() if port == 443 else None
                if ctx: ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
                self.reader, self.writer = await asyncio.open_connection(host, port, ssl=ctx)
                print(f"⚡ Connected to {host}:{port}")
                await self.send("mining.subscribe", ["bolt-miner/1.0"], 1)

            asyncio.create_task(self.stats_loop())
            asyncio.create_task(self.result_listener())

            while True:
                line = await self.reader.readline()
                if not line: break
                msg = json.loads(line)
                with bolt[22]:
                    if "method" in msg:
                        if msg["method"] == "mining.notify": self.start_mining(*msg["params"])
                        elif msg["method"] == "mining.set_difficulty":
                            d = msg["params"][0] or 1
                            self.target = int(0x00000000FFFF000000000000000000000000000000000000000000000000 // d)
                            print(f"🎯 Difficulty: {d}")
                    elif msg.get("id") == 1:
                        res = msg.get("result")
                        if res:
                            self.extranonce1, self.extranonce2_size = res[1], res[2]
                            await self.send("mining.authorize", [self.worker, self.password], 3)
                    elif msg.get("id") == 3: print(f"🔐 Authorized: {msg.get('result')}")
                    elif msg.get("id") == 4: print(f"✅ Share Response: {msg.get('result') or msg.get('error')}")
        finally: self.stop_mining()

    async def stats_loop(self):
        while True:
            await asyncio.sleep(10)
            el = time.time() - self.start_time
            if el > 0: print(f"📊 Hashrate: {self.hashes.value / el / 1000:.2f} kH/s")

    async def result_listener(self):
        while True:
            while not self.result_queue.empty():
                n = self.result_queue.get()
                print(f"⚡ Share Found! Nonce: {n:08x}")
                await self.send("mining.submit", [self.worker, self.cur_job, "00"*self.extranonce2_size, self.cur_ntime, f"{n:08x}"], 4)
            await asyncio.sleep(0.1)

    def start_mining(self, job_id, prev, cb1, cb2, branch, v, nbits, ntime, clean):
        self.stop_mining(); self.cur_job, self.cur_ntime = job_id, ntime
        with bolt[21]:
            en2 = "00" * self.extranonce2_size
            coin = hashlib.sha256(hashlib.sha256(binascii.unhexlify(cb1 + self.extranonce1 + en2 + cb2)).digest()).digest()
            for b in branch: coin = hashlib.sha256(hashlib.sha256(coin + binascii.unhexlify(b)).digest()).digest()
            h_fix = binascii.unhexlify(v)[::-1] + binascii.unhexlify(prev)[::-1] + coin + binascii.unhexlify(ntime)[::-1] + binascii.unhexlify(nbits)[::-1]
            t_bytes = self.target.to_bytes(32, "big")
        print(f"⚒️  New Job: {job_id}")
        self.stop_event.clear()
        cpus = mp.cpu_count()
        for i in range(cpus):
            p = mp.Process(target=hasher, args=(h_fix, t_bytes, i * 10000000, self.result_queue, self.stop_event, self.hashes))
            p.start(); self.processes.append(p)

    def stop_mining(self):
        self.stop_event.set()
        for p in self.processes: p.terminate(); p.join()
        self.processes = []

if __name__ == "__main__":
    u = sys.argv[1] if len(sys.argv) > 1 else "stratum+tcp://sha256.poolbinance.com:443"
    w = sys.argv[2] if len(sys.argv) > 2 else "Hich101.001"
    bolt.arm(r=0.5);
    try: asyncio.run(BoltMiner(u, w).run())
    except KeyboardInterrupt: bolt.stats()
