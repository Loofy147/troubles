import ctypes, os

class RustMiner:
    _lib = None
    @classmethod
    def load(cls):
        if cls._lib is None:
            lib_path = os.path.join(os.path.dirname(__file__), "libboltminer.so")
            if not os.path.exists(lib_path): return None
            cls._lib = ctypes.CDLL(lib_path)
            cls._lib.miner_sha256d_search.argtypes = [
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.c_void_p,
                ctypes.c_void_p
            ]
            cls._lib.miner_sha256d_search.restype = ctypes.c_int32
        return cls._lib

def search_native(h_fix, target_bytes, n_start, n_step, result_queue, stop_event, hashes_val):
    lib = RustMiner.load()
    if not lib: return
    res = ctypes.c_uint32(0)
    # stop_event is a mp.Event, which uses a flag internally.
    # For simplicity, we'll pass the underlying handle if possible, but
    # better to just pass a shared ctypes object.

    ok = lib.miner_sha256d_search(
        (ctypes.c_uint8 * 76)(*h_fix),
        (ctypes.c_uint8 * 32)(*target_bytes),
        n_start, n_step, ctypes.byref(res),
        ctypes.addressof(stop_event.get_obj()),
        ctypes.addressof(hashes_val.get_obj())
    )
    if ok: result_queue.put(res.value)
