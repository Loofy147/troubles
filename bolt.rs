use std::time::Instant;
use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

struct _E { n: u64, t: u64, m: u64, x: u64, s: f64 }
static _L: OnceLock<Mutex<HashMap<String, _E>>> = OnceLock::new();
fn _log() -> &'static Mutex<HashMap<String, _E>> { _L.get_or_init(|| Mutex::new(HashMap::new())) }

pub struct BoltGuard(String, Instant);
impl BoltGuard { pub fn new(l: &str) -> Self { Self(l.to_string(), Instant::now()) } }
impl Drop for BoltGuard {
    fn drop(&mut self) {
        let v = self.1.elapsed().as_nanos() as u64;
        let mut l = _log().lock().unwrap();
        let e = l.entry(self.0.clone()).or_insert(_E { n: 0, t: 0, m: v, x: v, s: 0.0 });
        e.n += 1; e.t += v; e.s += (v as f64).powi(2);
        if v < e.m { e.m = v } if v > e.x { e.x = v }
    }
}
#[macro_export] macro_rules! bolt { ($l:expr, $b:block) => {{ let _g = $crate::bolt::BoltGuard::new($l); $b }}; }
pub fn stats() {
    let l = _log().lock().unwrap();
    for (k, e) in l.iter() {
        let a = e.t as f64 / e.n as f64;
        println!("{:<16} n={:<8} μ={:.1}ns σ={:.1}ns [{}ns…{}ns]", k, e.n, a, (e.s/e.n as f64 - a*a).max(0.0).sqrt(), e.m, e.x);
    }
}
