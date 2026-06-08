use std::time::Instant;

// ── Bolt Integration (Minimal RAII) ──────────────────────────────────
static mut STATS: Option<Vec<(String, u64, u64)>> = None;

struct Bolt(String, Instant);
impl Bolt {
    fn new(label: &str) -> Self { Bolt(label.to_string(), Instant::now()) }
}
impl Drop for Bolt {
    fn drop(&mut self) {
        let dur = self.1.elapsed().as_nanos() as u64;
        unsafe {
            if STATS.is_none() { STATS = Some(Vec::new()); }
            if let Some(ref mut v) = STATS {
                if let Some(entry) = v.iter_mut().find(|e| e.0 == self.0) {
                    entry.1 += 1; entry.2 += dur;
                } else {
                    v.push((self.0.clone(), 1, dur));
                }
            }
        }
    }
}

// ── Finite Field Kernels ──────────────────────────────────────────────
const P: i64 = 251;

fn gf_inv(n: i64) -> i64 {
    let mut t = 0; let mut new_t = 1;
    let mut r = P; let mut new_r = n % P;
    while new_r != 0 {
        let q = r / new_r;
        let tmp_t = t; t = new_t; new_t = tmp_t - q * new_t;
        let tmp_r = r; r = new_r; new_r = tmp_r - q * new_r;
    }
    if r > 1 { return -1; }
    if t < 0 { t += P; }
    t
}

pub fn gf_gauss(a: &[i64], b: &[i64], k: usize) -> Option<Vec<i64>> {
    let _g = Bolt::new("GF Solve Rust");
    let mut m = vec![0i64; k * (k + 1)];
    for r in 0..k {
        for c in 0..k { m[r * (k + 1) + c] = a[r * k + c] % P; }
        m[r * (k + 1) + k] = b[r] % P;
    }

    for r in 0..k {
        let mut pivot = r;
        while pivot < k && m[pivot * (k + 1) + r] == 0 { pivot += 1; }
        if pivot == k { return None; }
        if pivot != r {
            for i in 0..=k {
                let tmp = m[r * (k + 1) + i];
                m[r * (k + 1) + i] = m[pivot * (k + 1) + i];
                m[pivot * (k + 1) + i] = tmp;
            }
        }

        let inv = gf_inv(m[r * (k + 1) + r]);
        for i in r..=k { m[r * (k + 1) + i] = (m[r * (k + 1) + i] * inv) % P; }

        for row in 0..k {
            if row != r {
                let factor = m[row * (k + 1) + r];
                for i in r..=k {
                    m[row * (k + 1) + i] = (m[row * (k + 1) + i] - factor * m[r * (k + 1) + i]) % P;
                    if m[row * (k + 1) + i] < 0 { m[row * (k + 1) + i] += P; }
                }
            }
        }
    }

    let mut res = vec![0i64; k];
    for i in 0..k { res[i] = m[i * (k + 1) + k]; }
    Some(res)
}

// ── Swarm Benchmark ──────────────────────────────────────────────────
fn main() {
    let k = 8;
    let n_iters = 100_000;

    // Example K=8 square matrix and vector
    let a = vec![1, 2, 3, 4, 5, 6, 7, 8,
                 1, 4, 9, 16, 25, 36, 49, 64,
                 1, 8, 27, 64, 125, 216, 343, 512,
                 1, 16, 81, 256, 625, 1296, 2401, 4096,
                 1, 32, 243, 1024, 3125, 7776, 16807, 32768,
                 1, 64, 729, 4096, 15625, 46656, 117649, 262144,
                 1, 128, 2187, 16384, 78125, 279936, 823543, 2097152,
                 1, 256, 6561, 65536, 390625, 1679616, 5764801, 16777216];
    let b = vec![42, 137, 201, 7, 88, 255, 0, 127];

    println!("⚡ Benchmarking Rust FSC Kernel (K={}, iterations={})", k, n_iters);
    let start = Instant::now();
    for _ in 0..n_iters {
        gf_gauss(&a, &b, k);
    }
    let total = start.elapsed();

    unsafe {
        if let Some(ref v) = STATS {
            for (label, n, t) in v {
                println!("  {:<16} n={:<10} μ={:.1}ns total={:?}", label, n, (*t as f64) / (*n as f64), total);
            }
        }
    }
}
