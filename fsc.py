import numpy as np
from bolt import bolt

# ── Finite Field Kernels ──────────────────────────────────────────────
def gf_inv(n, p):
    """Modular inverse via Extended Euclidean Algorithm."""
    t, nt, r, nr = 0, 1, p, n % p
    while nr:
        q = r // nr
        t, nt = nt, t - q * nt
        r, nr = nr, r - q * nr
    return (t % p) if r == 1 else None

def gf_gauss(A, b, p):
    """Overdetermined RREF mod p — O(m·e²). Returns solution or None."""
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

# ── Engines ───────────────────────────────────────────────────────────
class FSC:
    """Forward Security/Coding: Vertical Fiber Error Correction."""
    P = 257
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
            sol = gf_gauss(A, b, self.P)
        if sol is None: return False
        with bolt("Apply + Verify"):
            for i, ci in enumerate(cidx): d[ci] = (d[ci] + sol[i]) % self.P
            ok = np.all((self.T - self.W @ d) % self.P == 0)
            if ok: self.data[:] = d
        return ok

class ErasureManifold:
    """Reed-Solomon Erasure Coding: K-of-N Reconstruction."""
    P = 257
    def __init__(self, K=8, N=14):
        self.K, self.N = K, N
        self.G = np.array([[pow(i + 1, j, self.P) for j in range(K)]
                          for i in range(N)], dtype=np.int64)

    def encode(self, data):
        """K values -> N shards."""
        with bolt("RS Encode"):
            return (self.G @ np.array(data, dtype=np.int64)) % self.P

    def decode(self, received_shards):
        """Map of {index: value} -> K reconstructed values."""
        if len(received_shards) < self.K: return None
        idx = sorted(received_shards.keys())[:self.K]
        vals = np.array([received_shards[i] for i in idx], dtype=np.int64)
        with bolt("Submatrix Extract"):
            G_sub = self.G[idx]
        with bolt("GF Solve"):
            return gf_gauss(G_sub, vals, self.P)

# ── Telemetry Registration ───────────────────────────────────────────
bolt.register({
    1: "Syndrome Compute",
    2: "Submatrix Extract",
    3: "GF Overdetermined",
    4: "GF Solve",
    5: "RS Encode",
    6: "Apply + Verify"
})
