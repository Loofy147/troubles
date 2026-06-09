import ctypes
import os
import numpy as np
from bolt import bolt

class RustFSC:
    _lib = None

    @classmethod
    def load(cls):
        if cls._lib is None:
            lib_path = os.path.join(os.path.dirname(__file__), "libfsc.so")
            cls._lib = ctypes.CDLL(lib_path)

            cls._lib.fsc_gf_gauss.argtypes = [
                ctypes.POINTER(ctypes.c_int64),
                ctypes.POINTER(ctypes.c_int64),
                ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_int64)
            ]
            cls._lib.fsc_gf_gauss.restype = ctypes.c_int32

            cls._lib.fsc_vertical_solve.argtypes = [
                ctypes.POINTER(ctypes.c_int64), # a
                ctypes.POINTER(ctypes.c_uint8), # shards
                ctypes.c_size_t,               # k
                ctypes.c_size_t,               # payload_len
                ctypes.POINTER(ctypes.c_uint8)  # out
            ]
            cls._lib.fsc_vertical_solve.restype = ctypes.c_int32

            cls._lib.fsc_vertical_encode.argtypes = [
                ctypes.POINTER(ctypes.c_int64), # g
                ctypes.POINTER(ctypes.c_uint8), # data
                ctypes.c_size_t,               # k
                ctypes.c_size_t,               # n
                ctypes.c_size_t,               # payload_len
                ctypes.POINTER(ctypes.c_uint8)  # out
            ]
            cls._lib.fsc_vertical_encode.restype = None

            cls._lib.start_native_proxy.argtypes = [
                ctypes.c_uint16,
                ctypes.c_size_t,
                ctypes.c_size_t,
                ctypes.c_int32,
                ctypes.POINTER(ctypes.c_char_p),
                ctypes.c_size_t
            ]
            cls._lib.start_native_proxy.restype = None

            cls._lib.get_native_bolt_stats.argtypes = []
            cls._lib.get_native_bolt_stats.restype = None
        return cls._lib

def gf_gauss_rust(A, b, p=251):
    lib = RustFSC.load()
    k = A.shape[1]
    a_data = A.astype(np.int64).flatten()
    b_data = b.astype(np.int64)
    out_data = np.zeros(k, dtype=np.int64)
    a_ptr = a_data.ctypes.data_as(ctypes.POINTER(ctypes.c_int64))
    b_ptr = b_data.ctypes.data_as(ctypes.POINTER(ctypes.c_int64))
    out_ptr = out_data.ctypes.data_as(ctypes.POINTER(ctypes.c_int64))
    ok = lib.fsc_gf_gauss(a_ptr, b_ptr, k, out_ptr)
    return out_data.tolist() if ok else None

def vertical_solve_rust_opt(A, shards_buffer, k, payload_len):
    lib = RustFSC.load()
    a_data = A.astype(np.int64).flatten()
    out_data = np.zeros(k * payload_len, dtype=np.uint8)
    a_ptr = a_data.ctypes.data_as(ctypes.POINTER(ctypes.c_int64))
    shards_ptr = shards_buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
    out_ptr = out_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
    ok = lib.fsc_vertical_solve(a_ptr, shards_ptr, k, payload_len, out_ptr)
    return out_data if ok else None

def vertical_encode_rust_opt(G, data_buffer, k, n, payload_len):
    lib = RustFSC.load()
    g_data = G.astype(np.int64).flatten()
    out_data = np.zeros(n * payload_len, dtype=np.uint8)
    g_ptr = g_data.ctypes.data_as(ctypes.POINTER(ctypes.c_int64))
    data_ptr = data_buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
    out_ptr = out_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
    lib.fsc_vertical_encode(g_ptr, data_ptr, k, n, payload_len, out_ptr)
    return out_data

def start_native_proxy(port, k, n, mode='egress', peers=None):
    lib = RustFSC.load()
    m = 0 if mode == 'egress' else 1
    p_ptr = None
    p_count = 0
    if peers:
        p_count = len(peers)
        p_ptr = (ctypes.c_char_p * p_count)(*[p.encode('utf-8') for p in peers])
    lib.start_native_proxy(port, k, n, m, p_ptr, p_count)

def print_native_stats():
    lib = RustFSC.load()
    print("\n── native data plane ──")
    lib.get_native_bolt_stats()
