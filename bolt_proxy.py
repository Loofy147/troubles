import asyncio
import struct
import numpy as np
from fsc import ErasureManifold
from bolt import bolt

# ── Protocol Definition ───────────────────────────────────────────────
# [SeqID: Q] [ShardIdx: B] [Payload: 1024s]
PKT_FMT = ">QB1024s"
PKT_SIZE = struct.calcsize(PKT_FMT)

bolt.register({
    10: "Ingress Flow",
    11: "Egress Flow",
    12: "Manifold Reconstruction",
    13: "Network Broadcast",
    14: "UDP Receive"
})

class IngressProxy(asyncio.DatagramProtocol):
    """Encodes stream into a K-of-N Swarm and broadcasts."""
    def __init__(self, em, peer_addrs):
        self.em = em
        self.peer_addrs = peer_addrs
        self.seq = 0
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        with bolt[10]:
            # Simple chunking: split incoming data into K chunks
            # In a real proxy, this would be a buffer filling up K slots
            # For the prototype, we treat the 'data' as a block of K bytes for the FF solver
            # and pad with zeros to K=8.
            vals = list(data[:self.em.K]) + [0]*(self.em.K - len(data))
            shards = self.em.encode(vals)

            with bolt[13]:
                for i, val in enumerate(shards):
                    pkt = struct.pack(PKT_FMT, self.seq, i, bytes([val]))
                    for peer in self.peer_addrs:
                        self.transport.sendto(pkt, peer)
            self.seq += 1

class EgressProxy(asyncio.DatagramProtocol):
    """Reconstructs stream from K-of-N shards."""
    def __init__(self, em, output_callback):
        self.em = em
        self.cb = output_callback
        self.buffer = {} # seq -> {idx: val}
        self.reconstructed = set()
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        with bolt[14]:
            seq, idx, val_byte = struct.unpack(PKT_FMT, data)
            val = val_byte[0]

            if seq in self.reconstructed: return

            if seq not in self.buffer: self.buffer[seq] = {}
            self.buffer[seq][idx] = val

            if len(self.buffer[seq]) >= self.em.K:
                with bolt[12]:
                    with bolt[11]:
                        sol = self.em.decode(self.buffer[seq])
                        if sol:
                            self.cb(bytes(sol))
                            self.reconstructed.add(seq)
                            del self.buffer[seq]

async def start_proxy(local_port, peer_addrs, K=8, N=14, mode='ingress'):
    em = ErasureManifold(K=K, N=N)
    loop = asyncio.get_running_loop()

    if mode == 'ingress':
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: IngressProxy(em, peer_addrs),
            local_addr=('127.0.0.1', local_port)
        )
    else:
        def on_data(d): pass # print(f"Output: {d}")
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: EgressProxy(em, on_data),
            local_addr=('127.0.0.1', local_port)
        )
    return transport, protocol
