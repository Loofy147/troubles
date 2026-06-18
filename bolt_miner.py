import asyncio, json, hashlib, binascii, struct, time, sys, ssl, multiprocessing as mp
from bolt import bolt

bolt.register({20:"Stratum Connect", 21:"Job Setup", 22:"Control Plane", 23:"Share Submission"})

def sha256d(b): return hashlib.sha256(hashlib.sha256(b).digest()).digest()

def hasher_fallback(h_fix, target_bytes, n_start, n_step, result_queue, stop_event, hashes_val):
    header, sha, pack = bytearray(h_fix + b'\x00'*4), hashlib.sha256, struct.pack_into
    n, local = n_start, 0
    try:
        while not stop_event.value:
            for _ in range(5000):
                pack("<I", header, 76, n)
                if sha(sha(header).digest()).digest()[::-1] < target_bytes:
                    result_queue.put(n)
                n = (n + n_step) & 0xffffffff
            local += 5000
            if local >= 100000:
                with hashes_val.get_lock(): hashes_val.value += local
                local = 0
    finally:
        with hashes_val.get_lock(): hashes_val.value += local

def hasher_native(h_fix, target_bytes, n_start, n_step, result_queue, stop_event, hashes_val):
    from bolt_miner_rust import search_native
    search_native(h_fix, target_bytes, n_start, n_step, result_queue, stop_event, hashes_val)

class BoltMiner:
    def __init__(self, url, worker, password="x"):
        self.url, self.worker, self.password = url, worker, password
        self.extranonce1, self.extranonce2_size = "", 4
        self.target = (1 << 256) - 1
        self.reader, self.writer = None, None
        self.processes, self.stop_event, self.result_queue = [], mp.Value('b', False), mp.Queue()
        self.hashes, self.shares = mp.Value('Q', 0), mp.Value('I', 0)
        self.start_time = time.time()
        self.cur_job, self.cur_ntime = None, None

        # Detect native core
        import os
        self.use_native = os.path.exists("./libboltminer.so")
        print(f"⚡ Bolt Miner | Native: {'ON' if self.use_native else 'OFF'} | Pool: {url}")

    async def send(self, m, p, i=1):
        try:
            line = json.dumps({"id": i, "method": m, "params": p}) + "\n"
            self.writer.write(line.encode()); await self.writer.drain()
            if m != "mining.submit": print(f">>> {m}")
        except: pass

    async def run(self):
        while True:
            try:
                with bolt[20]:
                    u = self.url.split("://")[-1].split(":")
                    h, p = u[0], int(u[1])
                    ctx = ssl.create_default_context() if p in [443, 4443, 1443] else None
                    if ctx: ctx.check_hostname, ctx.verify_mode = False, ssl.CERT_NONE
                    self.reader, self.writer = await asyncio.open_connection(h, p, ssl=ctx)
                    await self.send("mining.subscribe", ["cpuminer/2.5.0"], 1)

                asyncio.create_task(self.stats_loop())
                asyncio.create_task(self.result_listener())

                while True:
                    line = await self.reader.readline()
                    if not line: break
                    msg = json.loads(line)
                    with bolt[22]:
                        if "method" in msg:
                            meth, params = msg["method"], msg.get("params", [])
                            if meth == "mining.notify": self.start_mining(*params)
                            elif meth == "mining.set_difficulty":
                                d = params[0] or 1
                                self.target = int(0x00000000FFFF000000000000000000000000000000000000000000000000 // d)
                                print(f"🎯 Diff: {d}")
                        elif msg.get("id") == 1:
                            res = msg.get("result")
                            if res:
                                # Handle varied subscribe responses
                                if isinstance(res[0], list) and len(res[0]) > 0 and isinstance(res[0][0], list):
                                    self.extranonce1, self.extranonce2_size = res[1], res[2]
                                else:
                                    self.extranonce1 = res[1] if len(res) > 1 else ""
                                    self.extranonce2_size = res[2] if len(res) > 2 else 4

                                # Steering: check for worker+diff
                                if "+" in self.worker:
                                    try:
                                        target_diff = float(self.worker.split("+")[-1])
                                        await self.send("mining.suggest_difficulty", [target_diff], 2)
                                    except: pass

                                await self.send("mining.authorize", [self.worker, self.password], 3)
                        elif msg.get("id") == 3:
                            if msg.get("result"): print(f"🔐 Authorized: {self.worker}")
                            else: print(f"❌ Auth Failed: {msg.get('error')}")
                        elif msg.get("id") == 4:
                            if msg.get("result") is True:
                                with self.shares.get_lock(): self.shares.value += 1
                                print(f"✅ Share Accepted!")
                            else: print(f"⚠️ Share Rejected: {msg.get('error')}")
            except Exception as e:
                print(f"⚠️ Error: {e}. Retry in 5s..."); self.stop_mining(); await asyncio.sleep(5)

    async def stats_loop(self):
        while True:
            await asyncio.sleep(10)
            el = time.time() - self.start_time
            if el > 0: print(f"📊 {self.hashes.value / el / 1000:.2f} kH/s | Shares: {self.shares.value}")

    async def result_listener(self):
        while True:
            while not self.result_queue.empty():
                n = self.result_queue.get()
                print(f"⚡ Found! Nonce: {n:08x}")
                await self.send("mining.submit", [self.worker, self.cur_job, "00"*self.extranonce2_size, self.cur_ntime, f"{n:08x}"], 4)
            await asyncio.sleep(0.1)

    def start_mining(self, job_id, prev, cb1, cb2, branch, v, nbits, ntime, clean):
        self.stop_mining(); self.current_job_id, self.current_ntime = job_id, ntime
        with bolt[21]:
            en2 = "00" * self.extranonce2_size
            coin = hashlib.sha256(hashlib.sha256(binascii.unhexlify(cb1 + self.extranonce1 + en2 + cb2)).digest()).digest()
            for b in branch: coin = hashlib.sha256(hashlib.sha256(coin + binascii.unhexlify(b)).digest()).digest()
            h_fix = binascii.unhexlify(v)[::-1] + binascii.unhexlify(prev)[::-1] + coin + binascii.unhexlify(ntime)[::-1] + binascii.unhexlify(nbits)[::-1]
            t_bytes = self.target.to_bytes(32, "big")

        self.stop_event.value = False
        cpus = mp.cpu_count()
        for i in range(cpus):
            target = hasher_native if self.use_native else hasher_fallback
            p = mp.Process(target=target, args=(h_fix, t_bytes, i, cpus, self.result_queue, self.stop_event, self.hashes))
            p.start(); self.processes.append(p)

    def stop_mining(self):
        self.stop_event.value = True
        for p in self.processes: p.terminate(); p.join()
        self.processes = []

if __name__ == "__main__":
    u = sys.argv[1] if len(sys.argv) > 1 else "stratum+tcp://sha256.poolbinance.com:443"
    w = sys.argv[2] if len(sys.argv) > 2 else "Hich101.001"
    p = sys.argv[3] if len(sys.argv) > 3 else "123456"
    bolt.arm(r=0.5);
    try: asyncio.run(BoltMiner(u, w, p).run())
    except KeyboardInterrupt: bolt.stats()
