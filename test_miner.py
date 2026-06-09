import asyncio, json, time, sys
from bolt_miner import BoltMiner

async def mock_pool(reader, writer):
    print("🧊 Mock Pool: Client connected.")
    try:
        # 1. Subscribe
        line = await reader.readline()
        writer.write((json.dumps({"id": 1, "result": [None, "01234567", 4], "error": None}) + "\n").encode())
        await writer.drain()

        # 2. Authorize
        line = await reader.readline()
        writer.write((json.dumps({"id": 3, "result": True, "error": None}) + "\n").encode())
        await writer.drain()

        # 3. Set Difficulty (impossible for instant share)
        writer.write((json.dumps({"id": None, "method": "mining.set_difficulty", "params": [1e-12]}) + "\n").encode())
        await writer.drain()

        # 4. Notify Job
        job = ["bf", "4d16b6f85af6e2198f44ae2a6de67f78487ae5611b51c4000000000000000000",
               "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff20020862062f503253482f04b824dc500810000001ec411000",
               "00000000", [], "00000002", "1c2ac4af", "50dc24b8", True]
        writer.write((json.dumps({"id": None, "method": "mining.notify", "params": job}) + "\n").encode())
        await writer.drain()

        # 5. Wait for Submission
        line = await reader.readline()
        if line:
            print(f"🧊 Mock Pool: Received Submission: {line.decode().strip()}")
            msg = json.loads(line)
            if msg["method"] == "mining.submit":
                writer.write((json.dumps({"id": msg["id"], "result": True, "error": None}) + "\n").encode())
                await writer.drain()
                print("🧊 Mock Pool: Share ACCEPTED. Test SUCCESS.")
                sys.exit(0)
    except Exception as e:
        print(f"🧊 Mock Pool Error: {e}")

async def main():
    server = await asyncio.start_server(mock_pool, '127.0.0.1', 3333)
    miner = BoltMiner("stratum+tcp://127.0.0.1:3333", "Hich101.001")
    try:
        await asyncio.wait_for(miner.run(), timeout=5)
    except SystemExit: pass
    except Exception as e: print(f"❌ Test ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
