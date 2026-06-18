use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};

#[repr(C)]
#[derive(Clone, Copy)]
pub struct SHA256_CTX {
    h: [u32; 8],
    nl: u32,
    nh: u32,
    data: [u8; 64],
    num: u32,
    md_len: u32,
}

#[link(name = "crypto")]
extern "C" {
    fn SHA256_Init(c: *mut SHA256_CTX) -> i32;
    fn SHA256_Update(c: *mut SHA256_CTX, data: *const u8, len: usize) -> i32;
    fn SHA256_Final(md: *mut u8, c: *mut SHA256_CTX) -> i32;
}

#[no_mangle]
pub extern "C" fn miner_sha256d_search(
    header_fix: *const u8,
    target: *const u8,
    n_start: u32,
    n_step: u32,
    result: *mut u32,
    stop: *const AtomicBool,
    hashes: *const AtomicU64
) -> i32 {
    let fix = unsafe { std::slice::from_raw_parts(header_fix, 76) };
    let mut tgt = [0u8; 32];
    unsafe { std::ptr::copy_nonoverlapping(target, tgt.as_mut_ptr(), 32) };
    let stop_ref = unsafe { &*stop };
    let hashes_ref = unsafe { &*hashes };

    let mut ctx_mid = unsafe { std::mem::zeroed() };
    unsafe {
        SHA256_Init(&mut ctx_mid);
        SHA256_Update(&mut ctx_mid, fix.as_ptr(), 64);
    }

    let mut h1 = [0u8; 32];
    let mut h2 = [0u8; 32];
    let mut local_hashes = 0u64;

    let mut n = n_start;
    loop {
        if local_hashes >= 1000000 {
            hashes_ref.fetch_add(local_hashes, Ordering::Relaxed);
            local_hashes = 0;
            if stop_ref.load(Ordering::Relaxed) { return 0; }
        }

        let mut ctx1 = ctx_mid;
        unsafe {
            SHA256_Update(&mut ctx1, fix[64..76].as_ptr(), 12);
            SHA256_Update(&mut ctx1, n.to_le_bytes().as_ptr(), 4);
            SHA256_Final(h1.as_mut_ptr(), &mut ctx1);

            let mut ctx2 = std::mem::zeroed();
            SHA256_Init(&mut ctx2);
            SHA256_Update(&mut ctx2, h1.as_ptr(), 32);
            SHA256_Final(h2.as_mut_ptr(), &mut ctx2);
        }

        let mut reversed = h2;
        reversed.reverse();

        if reversed < tgt {
            unsafe { *result = n };
            hashes_ref.fetch_add(local_hashes, Ordering::Relaxed);
            return 1;
        }

        local_hashes += 1;
        let (next_n, overflow) = n.overflowing_add(n_step);
        if overflow { break; }
        n = next_n;
    }
    0
}
