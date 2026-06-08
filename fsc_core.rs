const P: i64 = 251;

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

    for r in 0..k {
        for c in 0..k {
            inv_out[r * k + c] = m[r * 2 * k + k + c];
        }
    }
    true
}

#[no_mangle]
pub extern "C" fn fsc_vertical_solve(
    a_ptr: *const i64,
    shards_ptr: *const u8,
    k: usize,
    payload_len: usize,
    out_ptr: *mut u8
) -> i32 {
    let a = unsafe { std::slice::from_raw_parts(a_ptr, k * k) };
    let shards = unsafe { std::slice::from_raw_parts(shards_ptr, k * payload_len) };
    let out = unsafe { std::slice::from_raw_parts_mut(out_ptr, k * payload_len) };

    let mut inv = vec![0i64; k * k];
    if !gf_invert(a, k, &mut inv) { return 0; }

    for byte_idx in 0..payload_len {
        for i in 0..k {
            let mut sum = 0i64;
            for j in 0..k {
                sum += inv[i * k + j] * shards[j * payload_len + byte_idx] as i64;
            }
            out[i * payload_len + byte_idx] = (sum % P) as u8;
        }
    }
    1
}

#[no_mangle]
pub extern "C" fn fsc_vertical_encode(
    g_ptr: *const i64,
    data_ptr: *const u8,
    k: usize,
    n: usize,
    payload_len: usize,
    out_ptr: *mut u8
) {
    let g = unsafe { std::slice::from_raw_parts(g_ptr, n * k) };
    let data = unsafe { std::slice::from_raw_parts(data_ptr, k * payload_len) };
    let out = unsafe { std::slice::from_raw_parts_mut(out_ptr, n * payload_len) };

    for byte_idx in 0..payload_len {
        for i in 0..n {
            let mut sum = 0i64;
            for j in 0..k {
                sum += g[i * k + j] * data[j * payload_len + byte_idx] as i64;
            }
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
            for j in 0..k {
                sum = (sum + inv[i * k + j] * b_slice[j]) % P;
            }
            out_slice[i] = sum;
        }
        1
    } else {
        0
    }
}
