# parking/origin.py

import contextlib
import threading

_local = threading.local()


def get_ws_origin() -> str | None:
    return getattr(_local, "ws_origin", None)


@contextlib.contextmanager
def set_ws_origin(origin: str):
    prev = getattr(_local, "ws_origin", None)
    _local.ws_origin = origin
    try:
        yield
    finally:
        if prev is None:
            if hasattr(_local, "ws_origin"):
                delattr(_local, "ws_origin")
        else:
            _local.ws_origin = prev
