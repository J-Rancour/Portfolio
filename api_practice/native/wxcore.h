// wxcore: small aviation-weather calculations exposed with a C ABI.
//
// Why `extern "C"`? C++ compilers "mangle" function names to encode overloads
// (wx_flight_category becomes something like ?wx_flight_category@@YAHNN@Z).
// A C ABI keeps the plain name, so Python's ctypes (or C#, Java JNA, Rust...)
// can find the symbol. Only plain C types cross the boundary: no std::string,
// no exceptions, no classes.
#pragma once

#if defined(_WIN32)
#  if defined(WXCORE_BUILD)
#    define WX_API __declspec(dllexport)
#  else
#    define WX_API __declspec(dllimport)
#  endif
#else
#  define WX_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

enum { WX_VFR = 0, WX_MVFR = 1, WX_IFR = 2, WX_LIFR = 3 };

// FAA flight category from visibility (statute miles) and ceiling (feet AGL).
// Pass a negative ceiling for "no ceiling".
WX_API int wx_flight_category(double visibility_sm, double ceiling_ft);

// Splits wind into components along a runway. Results go through out-pointers.
// headwind > 0 is a headwind (< 0 tailwind); crosswind > 0 comes from the right.
WX_API void wx_wind_components(double wind_dir_deg, double wind_speed_kt, double runway_heading_deg,
                               double* headwind_kt, double* crosswind_kt);

WX_API const char* wx_version(void);

#ifdef __cplusplus
}
#endif
