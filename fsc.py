import numpy as np
from bolt import bolt

# ── Finite Field Kernels ──────────────────────────────────────────────
def gf_inv(n, p):
    t, nt, r, nr = 0, 1, p, n % p
    while nr:
        q = r // nr
        t, nt = nt, t - q * nt
        r, nr = nr, r - q * nr
    return (t % p) if r == 1 else None

def gf_gauss(A, b, p):
    m, n = A.shape
    M = np.zeros((m, n + 1), dtype=np.int64)
    M[:, :n] = A % p
    M[:, n] = b % p
    rank = 0
    for col in range(n):
        nz = np.nonzero(M[rank:, col])[0]
        if not len(nz): continue
        piv = rank + nz[0]
        if piv != rank: M[[rank, piv]] = M[[piv, rank]]
        iv = gf_inv(int(M[rank, col]), p)
        if iv is None: return None
        M[rank] = M[rank] * iv % p
        rows = np.arange(m) != rank
        f = M[rows, col].copy()
        M[rows] = (M[rows] - np.outer(f, M[rank])) % p
        rank += 1
        if rank == n: break
    return None if np.any(M[rank:, n]) else M[:n, n].tolist()

# ── Rust Integration ──────────────────────────────────────────────────
try:
    from fsc_rust import vertical_encode_rust_opt, vertical_solve_rust_opt, gf_gauss_rust
    _USE_RUST = True
except ImportError:
    _USE_RUST = False

def gf_gauss_fast(A, b, p):
    if _USE_RUST and p == 251:
        return gf_gauss_rust(A, b, p)
    return gf_gauss(A, b, p)

# ── Engines ───────────────────────────────────────────────────────────
class FSC:
    P = 251
    def __init__(self, fields=64, constraints=14):
        self.F, self.C = fields, constraints
        self.W = np.array([[pow(i + 1, j, self.P) for i in range(fields)]
                          for j in range(constraints)], dtype=np.int64)
        self.T = np.zeros(constraints, dtype=np.int64)
        self.data = np.zeros(fields, dtype=np.int64)

    def inject(self, cidx, val=137):
        self.data[:] = 0
        self.data[list(cidx)] = val

    def heal(self, cidx):
        d = self.data.copy()
        with bolt("Syndrome Compute"):
            syn = (self.T - self.W @ d) % self.P
            fail = np.where(syn != 0)[0]
        if not len(fail): return True
        with bolt("Submatrix Extract"):
            A = self.W[fail][:, list(cidx)]
            b = syn[fail]
        with bolt("GF Overdetermined"):
            sol = gf_gauss_fast(A, b, self.P)
        if sol is None: return False
        with bolt("Apply + Verify"):
            for i, ci in enumerate(cidx): d[ci] = (d[ci] + sol[i]) % self.P
            ok = np.all((self.T - self.W @ d) % self.P == 0)
            if ok: self.data[:] = d
        return ok

class ErasureManifold:
    P = 251
    def __init__(self, K=8, N=14):
        self.K, self.N = K, N
        self.G = np.array([[pow(i + 1, j, self.P) for j in range(K)]
                          for i in range(N)], dtype=np.int64)

    def encode(self, data):
        with bolt("RS Encode"):
            return (self.G @ np.array(data, dtype=np.int64)) % self.P

    def decode(self, received_shards):
        if len(received_shards) < self.K: return None
        idx = sorted(received_shards.keys())[:self.K]
        vals = np.array([received_shards[i] for i in idx], dtype=np.int64)
        with bolt("Submatrix Extract"):
            G_sub = self.G[idx]
        with bolt("GF Solve"):
            return gf_gauss_fast(G_sub, vals, self.P)

class VerticalManifold:
    """High-throughput Erasure Coding for 1KB+ payloads."""
    P = 251
    def __init__(self, K=8, N=14, payload_len=1024):
        self.K, self.N, self.payload_len = K, N, payload_len
        self.G = np.array([[pow(i + 1, j, self.P) for j in range(K)]
                          for i in range(N)], dtype=np.int64)

    def encode(self, data_buffer):
        if _USE_RUST:
            with bolt("Vertical Encode [RUST]"):
                encoded = vertical_encode_rust_opt(self.G, data_buffer, self.K, self.N, self.payload_len)
            return encoded.reshape(self.N, self.payload_len)

        with bolt("Vertical Encode [PY]"):
            out = np.zeros((self.N, self.payload_len), dtype=np.uint8)
            data = data_buffer.reshape(self.K, self.payload_len)
            for i in range(self.payload_len):
                col = data[:, i].astype(np.int64)
                res = (self.G @ col) % self.P
                out[:, i] = res.astype(np.uint8)
            return out

    def decode(self, received_shards):
        if len(received_shards) < self.K: return None
        idx = sorted(received_shards.keys())[:self.K]
        shards_buffer = np.vstack([np.frombuffer(received_shards[i], dtype=np.uint8) for i in idx])
        G_sub = self.G[idx]

        if _USE_RUST:
            with bolt("Vertical Solve [RUST]"):
                decoded = vertical_solve_rust_opt(G_sub, shards_buffer, self.K, self.payload_len)
            return decoded.tobytes() if decoded is not None else None

        with bolt("Vertical Solve [PY]"):
            out = np.zeros((self.K, self.payload_len), dtype=np.uint8)
            for i in range(self.payload_len):
                b = shards_buffer[:, i].astype(np.int64)
                sol = gf_gauss(G_sub, b, self.P)
                if sol: out[:, i] = np.array(sol, dtype=np.uint8)
                else: return None
            return out.tobytes()

bolt.register({
    1: "Syndrome Compute",
    2: "Submatrix Extract",
    3: "GF Overdetermined",
    4: "GF Solve",
    5: "RS Encode",
    6: "Apply + Verify",
    7: "Vertical Encode [RUST]",
    8: "Vertical Solve [RUST]",
    9: "Vertical Encode [PY]",
    10: "Vertical Solve [PY]"
})
