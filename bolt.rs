use std::time::Instant;
use std::collections::HashMap;
use std::sync::{Mutex, OnceLock, atomic::{AtomicU64, AtomicBool, Ordering}};
use std::borrow::Cow;

struct _E { n: u64, t: u64, m: u64, x: u64, s: f64 }
struct _S {
    gn: AtomicU64, ge: AtomicU64, gt: AtomicU64, gT: AtomicU64,
    gr: Mutex<f64>, gb: AtomicBool
}
static _L: OnceLock<Mutex<HashMap<Cow<'static, str>, _E>>> = OnceLock::new();
static _ST: OnceLock<_S> = OnceLock::new();

fn _log() -> &'static Mutex<HashMap<Cow<'static, str>, _E>> { _L.get_or_init(|| Mutex::new(HashMap::new())) }
fn _state() -> &'static _S {
    _ST.get_or_init(|| _S {
        gn: AtomicU64::new(0), ge: AtomicU64::new(0), gt: AtomicU64::new(100),
        gT: AtomicU64::new(0), gr: Mutex::new(0.0), gb: AtomicBool::new(false)
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
        let gn = s.gn.fetch_add(1, Ordering::SeqCst) + 1;
        let gT = s.gT.fetch_add(v, Ordering::SeqCst) + v;

        let ge = s.ge.load(Ordering::Relaxed);
        if ge > 0 && gn >= ge {
            let mut l = _log().lock().unwrap();
            l.clear();
            s.gn.store(0, Ordering::SeqCst);
            s.gT.store(0, Ordering::SeqCst);
            println!("⚡ Bolt Epoch Reset");
        }

        let gr = *s.gr.lock().unwrap();
        if gr > 0.0 && gn % 1000 == 0 {
            let o = gn * s.gt.load(Ordering::Relaxed);
            if (o as f64) / ((o + gT) as f64) > gr {
                s.gb.store(true, Ordering::SeqCst);
                println!("⚡ Bolt Tripwire");
            }
        }

        let mut l = _log().lock().unwrap();
        let e = l.entry(self.0.clone()).or_insert(_E { n: 0, t: 0, m: v, x: v, s: 0.0 });
        e.n += 1; e.t += v; e.s += (v as f64).powi(2);
        if v < e.m { e.m = v } if v > e.x { e.x = v }
    }
}

pub fn arm(e: u64, r: f64, t: u64) {
    let s = _state();
    s.ge.store(e, Ordering::SeqCst);
    *s.gr.lock().unwrap() = r;
    s.gt.store(t, Ordering::SeqCst);
    s.gn.store(0, Ordering::SeqCst);
    s.gT.store(0, Ordering::SeqCst);
    s.gb.store(false, Ordering::SeqCst);
}

#[macro_export] macro_rules! bolt { ($l:expr, $b:block) => {{ if let Some(_g) = $crate::BoltGuard::new($l) { $b } else { $b } }}; }
pub fn stats() {
    let l = _log().lock().unwrap();
    for (k, e) in l.iter() {
        let a = e.t as f64 / e.n as f64;
        println!("{:<16} n={:<8} μ={:.1}ns σ={:.1}ns [{}ns…{}ns]", k, e.n, a, (e.s/e.n as f64 - a*a).max(0.0).sqrt(), e.m, e.x);
    }
}
pub fn check() {
    let n = 1_000_000;
    let t = Instant::now();
    for _ in 0..n { let _g = BoltGuard::new("check"); }
    println!("⚡ Rust Bolt Tax: {:.1}ns/call", t.elapsed().as_nanos() as f64 / n as f64);
}
