"""Python <-> C++ bridge using ctypes.

Loads native/build/wxcore.dll (Windows), libwxcore.so (Linux) or
libwxcore.dylib (macOS). If the library is missing or can't load (not built
yet, or built for the wrong bitness: "[WinError 193] %1 is not a valid Win32
application"), we fall back to an equivalent pure-Python version so the API
still runs. `ENGINE` says which one is live, and /health reports it.
"""

import ctypes
import logging
import math
import os
import sys
from pathlib import Path

log = logging.getLogger("api")

CATEGORIES = ("VFR", "MVFR", "IFR", "LIFR")
LIB_NAME = {"win32": "wxcore.dll", "darwin": "libwxcore.dylib"}.get(sys.platform, "libwxcore.so")
DEFAULT_PATH = Path(__file__).resolve().parent.parent / "native" / "build" / LIB_NAME


def _load():
    path = Path(os.environ.get("WXCORE_LIB", DEFAULT_PATH))
    try:
        lib = ctypes.CDLL(str(path))
    except OSError as e:
        log.warning("C++ core not loaded from %s (%s); using Python fallback", path, e)
        return None
    # Declare the C signatures. Without argtypes, ctypes refuses Python floats
    # (ArgumentError) and passes Python ints as C ints, which a function
    # expecting doubles reads as garbage. Without restype it assumes every
    # function returns int, so a returned char* gets truncated to a number.
    lib.wx_flight_category.argtypes = [ctypes.c_double, ctypes.c_double]
    lib.wx_flight_category.restype = ctypes.c_int
    lib.wx_wind_components.argtypes = [ctypes.c_double] * 3 + [ctypes.POINTER(ctypes.c_double)] * 2
    lib.wx_wind_components.restype = None
    lib.wx_version.argtypes = []
    lib.wx_version.restype = ctypes.c_char_p
    log.info("loaded %s", lib.wx_version().decode())
    return lib


_lib = _load()
ENGINE = "cpp" if _lib else "python"


def py_flight_category(visibility_sm: float, ceiling_ft: float) -> int:
    """Pure-Python twin of wx_flight_category (also used to test the C++ one)."""
    by_vis = 3 if visibility_sm < 1 else 2 if visibility_sm < 3 else 1 if visibility_sm <= 5 else 0
    by_ceil = (
        0 if ceiling_ft < 0 else 3 if ceiling_ft < 500 else 2 if ceiling_ft < 1000 else 1 if ceiling_ft <= 3000 else 0
    )
    return max(by_vis, by_ceil)


def py_wind_components(wind_dir_deg: float, wind_speed_kt: float, runway_heading_deg: float) -> tuple[float, float]:
    angle = math.radians(wind_dir_deg - runway_heading_deg)
    return wind_speed_kt * math.cos(angle), wind_speed_kt * math.sin(angle)


def flight_category(visibility_sm: float, ceiling_ft: float | None) -> str:
    ceiling = -1.0 if ceiling_ft is None else float(ceiling_ft)
    if _lib:
        return CATEGORIES[_lib.wx_flight_category(visibility_sm, ceiling)]
    return CATEGORIES[py_flight_category(visibility_sm, ceiling)]


def wind_components(wind_dir_deg: float, wind_speed_kt: float, runway_heading_deg: float) -> tuple[float, float]:
    if _lib:
        head, cross = ctypes.c_double(), ctypes.c_double()
        # byref passes a pointer to our doubles; C writes the results into them.
        _lib.wx_wind_components(
            wind_dir_deg, wind_speed_kt, runway_heading_deg, ctypes.byref(head), ctypes.byref(cross)
        )
        return head.value, cross.value
    return py_wind_components(wind_dir_deg, wind_speed_kt, runway_heading_deg)
