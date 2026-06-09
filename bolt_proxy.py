import asyncio
import struct
import numpy as np
from fsc import VerticalManifold
from bolt import bolt

# ── Protocol Definition ───────────────────────────────────────────────
# [SeqID: Q] [ShardIdx: B] [Payload: 1024s]
PAYLOAD_LEN = 1024
PKT_FMT = f">QB{PAYLOAD_LEN}s"
PKT_SIZE = struct.calcsize(PKT_FMT)

bolt.register({
    10: "Ingress Flow",
    11: "Egress Flow",
    12: "Manifold Reconstruction",
    13: "Network Broadcast",
    14: "UDP Receive"
})

class IngressProxy(asyncio.DatagramProtocol):
    def __init__(self, vm, peer_addrs):
        self.vm = vm
        self.peer_addrs = peer_addrs
        self.seq = 0
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        with bolt[10]:
            target_len = self.vm.K * self.vm.payload_len
            buf = np.frombuffer(data[:target_len].ljust(target_len, b'\0'), dtype=np.uint8)
            shards = self.vm.encode(buf)

            with bolt[13]:
                for i, shard in enumerate(shards):
                    pkt = struct.pack(PKT_FMT, self.seq, i, shard.tobytes())
                    for peer in self.peer_addrs:
                        self.transport.sendto(pkt, peer)
            self.seq += 1

class EgressProxy(asyncio.DatagramProtocol):
    def __init__(self, vm, output_callback):
        self.vm = vm
        self.cb = output_callback
        self.buffer = {}
        self.reconstructed = set()
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        with bolt[14]:
            if len(data) < PKT_SIZE: return
            seq, idx, payload = struct.unpack(PKT_FMT, data)

            if seq in self.reconstructed: return
            if seq not in self.buffer: self.buffer[seq] = {}
            self.buffer[seq][idx] = payload

            if len(self.buffer[seq]) >= self.vm.K:
                with bolt[12]:
                    with bolt[11]:
                        sol = self.vm.decode(self.buffer[seq])
                        if sol:
                            self.cb(sol)
                            self.reconstructed.add(seq)
                            if seq in self.buffer: del self.buffer[seq]

async def start_proxy(local_port, peer_addrs, K=8, N=14, mode='ingress'):
    vm = VerticalManifold(K=K, N=N, payload_len=PAYLOAD_LEN)
    loop = asyncio.get_running_loop()

    if mode == 'ingress':
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: IngressProxy(vm, peer_addrs),
            local_addr=('127.0.0.1', local_port)
        )
    else:
        def on_data(d): pass
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: EgressProxy(vm, on_data),
            local_addr=('127.0.0.1', local_port)
        )
    return transport, protocol

def start_native_swarm(local_port, k, n, mode='egress'):
    from fsc_rust import start_native_proxy
    start_native_proxy(local_port, k, n, mode)

def show_native_telemetry():
    from fsc_rust import print_native_stats
    print_native_stats()
