import os
import pickle
import hashlib
from functools import wraps

def disk_cache(cache_dir="cache"):
    os.makedirs(cache_dir, exist_ok=True)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_raw = (func.__name__, args, tuple(sorted(kwargs.items())))
            key = hashlib.sha256(pickle.dumps(key_raw)).hexdigest()
            path = os.path.join(cache_dir, key + ".pkl")

            if os.path.exists(path):
                with open(path, "rb") as f:
                    return pickle.load(f)

            result = func(*args, **kwargs)
            with open(path, "wb") as f:
                pickle.dump(result, f)
            return result
        return wrapper
    return decorator