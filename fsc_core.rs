use std::net::{UdpSocket, SocketAddr};
use std::sync::{Mutex, OnceLock};
use std::thread;
use std::collections::{HashMap, HashSet};
use std::time::Instant;
use std::borrow::Cow;
use std::sync::atomic::{AtomicU64, AtomicBool, Ordering};

const P: i64 = 251;
const PAYLOAD_LEN: usize = 1024;

// ── Bolt.rs Integration ──────────────────────────────────────────────
struct BoltEntry { n: u64, t: u64, m: u64, x: u64, s: f64 }
struct BoltState {
    gn: AtomicU64,
    gb: AtomicBool
}
static LOG: OnceLock<Mutex<HashMap<Cow<'static, str>, BoltEntry>>> = OnceLock::new();
static STATE: OnceLock<BoltState> = OnceLock::new();

fn _log() -> &'static Mutex<HashMap<Cow<'static, str>, BoltEntry>> { LOG.get_or_init(|| Mutex::new(HashMap::new())) }
fn _state() -> &'static BoltState {
    STATE.get_or_init(|| BoltState {
        gn: AtomicU64::new(0),
        gb: AtomicBool::new(false)
    })
}

pub struct BoltGuard(Cow<'static, str>, Instant);
impl BoltGuard {
    pub fn new(l: impl Into<Cow<'static, str>>) -> Option<Self> {
        if _state().gb.load(Ordering::Relaxed) { None } else { Some(Self(l.into(), Instant::now())) }
    }
}
impl Drop for BoltGuard {
    fn drop(&mut self) {
        let v = self.1.elapsed().as_nanos() as u64;
        let s = _state();
        let _gn = s.gn.fetch_add(1, Ordering::SeqCst) + 1;
        let mut l = _log().lock().unwrap();
        if let Some(e) = l.get_mut(&self.0) {
            e.n += 1; e.t += v; e.s += (v as f64).powi(2);
            if v < e.m { e.m = v } if v > e.x { e.x = v }
        } else {
            l.insert(self.0.clone(), BoltEntry { n: 1, t: v, m: v, x: v, s: (v as f64).powi(2) });
        }
    }
}

// ── Finite Field Logic ───────────────────────────────────────────────
#[inline(always)]
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

#[inline(always)]
fn gf_invert(a: &[i64], k: usize, inv_out: &mut [i64]) -> bool {
    let mut m = vec![0i64; k * 2 * k];
    for r in 0..k {
        for c in 0..k { m[r * 2 * k + c] = a[r * k + c]; }
        m[r * 2 * k + k + r] = 1;
    }
    for r in 0..k {
        let mut pivot = r;
        while pivot < k && m[pivot * 2 * k + r] == 0 { pivot += 1; }
        if pivot == k { return false; }
        if pivot != r {
            for i in 0..2*k {
                let tmp = m[r * 2 * k + i];
                m[r * 2 * k + i] = m[pivot * 2 * k + i];
                m[pivot * 2 * k + i] = tmp;
            }
        }
        let inv = gf_inv(m[r * 2 * k + r]);
        if inv == -1 { return false; }
        for i in r..2*k { m[r * 2 * k + i] = (m[r * 2 * k + i] * inv) % P; }
        for row in 0..k {
            if row != r {
                let factor = m[row * 2 * k + r];
                if factor == 0 { continue; }
                for i in r..2*k {
                    m[row * 2 * k + i] = (m[row * 2 * k + i] - factor * m[r * 2 * k + i]) % P;
                    if m[row * 2 * k + i] < 0 { m[row * 2 * k + i] += P; }
                }
            }
        }
    }
    for r in 0..k { for c in 0..k { inv_out[r * k + c] = m[r * 2 * k + k + c]; } }
    true
}

// ── Reactor Core ─────────────────────────────────────────────────────
pub fn run_egress(port: u16, k: usize, sink: Option<SocketAddr>) {
    let socket = UdpSocket::bind(format!("127.0.0.1:{}", port)).expect("Bind failed");
    let mut buffer = HashMap::new();
    let mut reconstructed = HashSet::new();
    let mut pkt_buf = [0u8; 2048];
    let mut inv = vec![0i64; k * k];
    for i in 0..k { inv[i * k + i] = 1; }

    println!("⚡ Rust Native Egress Proxy [K={}] on port {} -> Sink {:?}", k, port, sink);
    loop {
        match socket.recv_from(&mut pkt_buf) {
            Ok((size, _addr)) => {
                let _g_read = BoltGuard::new("Native Wire Read");
                if size < 10 { continue; }
                let mut seq_bytes = [0u8; 8];
                seq_bytes.copy_from_slice(&pkt_buf[0..8]);
                let seq = u64::from_be_bytes(seq_bytes);
                let idx = pkt_buf[8] as usize;
                let payload = &pkt_buf[9..size];
                if reconstructed.contains(&seq) { continue; }
                let entry = buffer.entry(seq).or_insert_with(|| (0u16, vec![0u8; k * PAYLOAD_LEN]));
                if (entry.0 & (1 << idx)) == 0 {
                    entry.0 |= 1 << idx;
                    if idx < k {
                        let start_idx = idx * PAYLOAD_LEN;
                        let end_idx = start_idx + payload.len();
                        if end_idx <= entry.1.len() { entry.1[start_idx..end_idx].copy_from_slice(payload); }
                    }
                }
                if entry.0.count_ones() as usize >= k {
                    let _g_solve = BoltGuard::new("Native Vertical Solve");
                    let mut out = vec![0u8; k * PAYLOAD_LEN];
                    for byte_idx in 0..PAYLOAD_LEN {
                        for i in 0..k {
                            let mut sum = 0i64;
                            for j in 0..k { sum += inv[i * k + j] * entry.1[j * PAYLOAD_LEN + byte_idx] as i64; }
                            out[i * PAYLOAD_LEN + byte_idx] = (sum % P) as u8;
                        }
                    }
                    if let Some(sink_addr) = sink {
                        let _ = socket.send_to(&out, sink_addr);
                    }
                    reconstructed.insert(seq);
                    buffer.remove(&seq);
                    if reconstructed.len() > 5000 { reconstructed.clear(); }
                }
            }
            Err(_) => break,
        }
    }
}

pub fn run_ingress(port: u16, k: usize, n: usize, peers: Vec<SocketAddr>) {
    let socket = UdpSocket::bind(format!("127.0.0.1:{}", port)).expect("Bind failed");
    let mut pkt_buf = [0u8; PAYLOAD_LEN * 16];
    let mut seq = 0u64;
    let mut g = vec![0i64; n * k];
    for i in 0..n { for j in 0..k { g[i * k + j] = (i as i64 + 1).pow(j as u32) % P; } }

    println!("⚡ Rust Native Ingress Proxy [K={}, N={}] on port {} -> Peers {:?}", k, n, port, peers);
    loop {
        match socket.recv_from(&mut pkt_buf) {
            Ok((size, _addr)) => {
                let _g_ing = BoltGuard::new("Native Ingress Encode");
                let mut out = vec![0u8; n * PAYLOAD_LEN];
                for byte_idx in 0..PAYLOAD_LEN {
                    for i in 0..n {
                        let mut sum = 0i64;
                        for j in 0..k {
                            let val = if j * PAYLOAD_LEN + byte_idx < size { pkt_buf[j * PAYLOAD_LEN + byte_idx] as i64 } else { 0 };
                            sum += g[i * k + j] * val;
                        }
                        out[i * PAYLOAD_LEN + byte_idx] = (sum % P) as u8;
                    }
                }
                for i in 0..n {
                    let mut pkt = Vec::with_capacity(9 + PAYLOAD_LEN);
                    pkt.extend_from_slice(&seq.to_be_bytes());
                    pkt.push(i as u8);
                    pkt.extend_from_slice(&out[i * PAYLOAD_LEN..(i + 1) * PAYLOAD_LEN]);
                    for peer in &peers { let _ = socket.send_to(&pkt, peer); }
                }
                seq += 1;
            }
            Err(_) => break,
        }
    }
}

// ── FFI ─────────────────────────────────────────────────────────────
#[no_mangle]
pub extern "C" fn start_native_proxy(port: u16, k: usize, n: usize, mode: i32, peers_ptr: *const *const i8, peers_count: usize) {
    let mut peers = Vec::new();
    if !peers_ptr.is_null() {
        for i in 0..peers_count {
            let c_str = unsafe { std::ffi::CStr::from_ptr(*peers_ptr.add(i)) };
            if let Ok(s) = c_str.to_str() { if let Ok(addr) = s.parse::<SocketAddr>() { peers.push(addr); } }
        }
    }
    if mode == 0 {
        let sink = if peers.is_empty() { None } else { Some(peers[0]) };
        thread::spawn(move || run_egress(port, k, sink));
    } else {
        thread::spawn(move || run_ingress(port, k, n, peers));
    }
}

#[no_mangle]
pub extern "C" fn get_native_bolt_stats() {
    let l = _log().lock().unwrap();
    for (k, e) in l.iter() {
        let a = e.t as f64 / e.n as f64;
        println!("  {:<20} n={:<8} μ={:.1}ns σ={:.1}ns", k, e.n, a, (e.s/e.n as f64 - a*a).max(0.0).sqrt());
    }
}

#[no_mangle]
pub extern "C" fn fsc_vertical_solve(
    a_ptr: *const i64, shards_ptr: *const u8, k: usize, payload_len: usize, out_ptr: *mut u8
) -> i32 {
    let a = unsafe { std::slice::from_raw_parts(a_ptr, k * k) };
    let shards = unsafe { std::slice::from_raw_parts(shards_ptr, k * payload_len) };
    let out = unsafe { std::slice::from_raw_parts_mut(out_ptr, k * payload_len) };
    let mut inv = vec![0i64; k * k];
    if !gf_invert(a, k, &mut inv) { return 0; }
    for byte_idx in 0..payload_len {
        for i in 0..k {
            let mut sum = 0i64;
            for j in 0..k { sum += inv[i * k + j] * shards[j * payload_len + byte_idx] as i64; }
            out[i * payload_len + byte_idx] = (sum % P) as u8;
        }
    }
    1
}

#[no_mangle]
pub extern "C" fn fsc_vertical_encode(
    g_ptr: *const i64, data_ptr: *const u8, k: usize, n: usize, payload_len: usize, out_ptr: *mut u8
) {
    let g = unsafe { std::slice::from_raw_parts(g_ptr, n * k) };
    let data = unsafe { std::slice::from_raw_parts(data_ptr, k * payload_len) };
    let out = unsafe { std::slice::from_raw_parts_mut(out_ptr, n * payload_len) };
    for byte_idx in 0..payload_len {
        for i in 0..n {
            let mut sum = 0i64;
            for j in 0..k { sum += g[i * k + j] * data[j * payload_len + byte_idx] as i64; }
            out[i * payload_len + byte_idx] = (sum % P) as u8;
        }
    }
}

#[no_mangle]
pub extern "C" fn fsc_gf_gauss(a: *const i64, b: *const i64, k: usize, out: *mut i64) -> i32 {
    let a_slice = unsafe { std::slice::from_raw_parts(a, k * k) };
    let b_slice = unsafe { std::slice::from_raw_parts(b, k) };
    let mut inv = vec![0i64; k * k];
    if gf_invert(a_slice, k, &mut inv) {
        let out_slice = unsafe { std::slice::from_raw_parts_mut(out, k) };
        for i in 0..k {
            let mut sum = 0i64;
            for j in 0..k { sum = (sum + inv[i * k + j] * b_slice[j]) % P; }
            out_slice[i] = sum;
        }
        1
    } else { 0 }
}
