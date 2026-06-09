import asyncio, json, hashlib, binascii, struct, time, sys, ssl
from bolt import bolt

bolt.register({
    20: "Stratum Connect",
    21: "Job Setup",
    22: "Hashing Core",
    23: "Share Submission"
})

def sha256d(b): return hashlib.sha256(hashlib.sha256(b).digest()).digest()

class BoltMiner:
    def __init__(self, url, worker, password="123"):
        self.url = url
        self.worker = worker
        self.password = password
        self.extranonce1 = ""
        self.extranonce2_size = 4
        self.target = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
        self.reader = None
        self.writer = None
        self._task = None

    async def send(self, method, params, id=1):
        try:
            line = json.dumps({"id": id, "method": method, "params": params}) + "\n"
            self.writer.write(line.encode())
            await self.writer.drain()
        except: pass

    async def run(self):
        try:
            with bolt[20]:
                u = self.url.split("://")[-1].split(":")
                host, port = u[0], int(u[1])
                use_ssl = (port == 443)
                print(f"⚡ Connecting to {host}:{port} (SSL: {use_ssl})...")

                ctx = ssl.create_default_context() if use_ssl else None
                if use_ssl:
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE

                self.reader, self.writer = await asyncio.open_connection(host, port, ssl=ctx)
                print("📡 Connection established. Subscribing...")
                await self.send("mining.subscribe", [])

            while True:
                line = await self.reader.readline()
                if not line: break
                msg = json.loads(line)

                if "method" in msg:
                    if msg["method"] == "mining.notify":
                        if self._task: self._task.cancel()
                        self._task = asyncio.create_task(self.mine(*msg["params"]))
                    elif msg["method"] == "mining.set_difficulty":
                        diff = msg["params"][0] or 1
                        self.target = int(0x00000000FFFF000000000000000000000000000000000000000000000000 // diff)
                        print(f"🎯 Difficulty: {diff}")
                    elif msg["method"] == "mining.set_extranonce":
                        self.extranonce1 = msg["params"][0]
                        self.extranonce2_size = msg["params"][1]
                        print(f"📡 Extranonce set: {self.extranonce1}")
                elif msg.get("id") == 1:
                    res = msg.get("result")
                    if res:
                        # Handle varied response formats
                        if isinstance(res[0], list) and len(res[0]) > 0 and isinstance(res[0][0], list):
                            # [[["mining.set_difficulty", "deadbeef"], ...], "extranonce1", extranonce2_size]
                            self.extranonce1 = res[1]
                            self.extranonce2_size = res[2]
                        else:
                            # ["extranonce1", extranonce2_size] or similar
                            self.extranonce1 = res[1] if len(res) > 1 else ""
                            self.extranonce2_size = res[2] if len(res) > 2 else 4
                        print(f"📡 Subscribed. Extranonce1: {self.extranonce1}")
                        await self.send("mining.authorize", [self.worker, self.password], 2)
                elif msg.get("id") == 2:
                    print(f"🔐 Authorized: {msg.get('result')}")
                elif msg.get("id") == 4:
                    print(f"✅ Share Response: {msg.get('result') or msg.get('error')}")
        except Exception as e:
            print(f"⚠️ Error: {e}")

    async def mine(self, job_id, prevhash, cb1, cb2, branch, version, nbits, ntime, clean):
        try:
            with bolt[21]:
                en2 = "00" * self.extranonce2_size
                coinbase = binascii.unhexlify(cb1 + self.extranonce1 + en2 + cb2)
                merkle_root = sha256d(coinbase)
                for b in branch:
                    merkle_root = sha256d(merkle_root + binascii.unhexlify(b))

                h_fix = binascii.unhexlify(version)[::-1] + \
                        binascii.unhexlify(prevhash)[::-1] + \
                        merkle_root + \
                        binascii.unhexlify(ntime)[::-1] + \
                        binascii.unhexlify(nbits)[::-1]

            print(f"⚒️  Job {job_id} | Target: {self.target:064x}")
            for n_base in range(0, 0xffffffff, 5000):
                await asyncio.sleep(0.01)
                with bolt[22]:
                    for n in range(n_base, n_base + 5000):
                        header = h_fix + struct.pack("<I", n)
                        h = sha256d(header)[::-1]
                        if int.from_bytes(h, "big") < self.target:
                            print(f"⚡ Found! Nonce: {n:08x}")
                            with bolt[23]:
                                await self.send("mining.submit", [self.worker, job_id, en2, ntime, f"{n:08x}"], 4)
                            return
        except asyncio.CancelledError: pass
        except Exception as e: print(f"⚠️ Mining error: {e}")

if __name__ == "__main__":
    u = sys.argv[1] if len(sys.argv) > 1 else "stratum+tcp://btc.poolbinance.com:1800"
    w = sys.argv[2] if len(sys.argv) > 2 else "Hich101.001"
    bolt.arm(r=0.5)
    try: asyncio.run(BoltMiner(u, w).run())
    except KeyboardInterrupt: bolt.stats()
