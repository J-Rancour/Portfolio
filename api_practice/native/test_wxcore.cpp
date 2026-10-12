// Minimal C++ unit tests: no framework, non-zero exit code on failure so
// CI (ctest / the build scripts) marks the build red.
#include <cmath>
#include <cstdio>

#include "wxcore.h"

static int failures = 0;

static void expect(bool ok, const char* what) {
    std::printf("%s  %s\n", ok ? "PASS" : "FAIL", what);
    if (!ok) ++failures;
}

static bool near(double a, double b) { return std::fabs(a - b) < 0.01; }

int main() {
    expect(wx_flight_category(10, -1) == WX_VFR, "clear and 10sm is VFR");
    expect(wx_flight_category(10, 5000) == WX_VFR, "ceiling 5000 is VFR");
    expect(wx_flight_category(4, -1) == WX_MVFR, "4sm is MVFR");
    expect(wx_flight_category(10, 3000) == WX_MVFR, "ceiling 3000 is MVFR (boundary)");
    expect(wx_flight_category(10, 800) == WX_IFR, "ceiling 800 is IFR");
    expect(wx_flight_category(2, -1) == WX_IFR, "2sm is IFR");
    expect(wx_flight_category(0.5, 5000) == WX_LIFR, "1/2sm is LIFR even with high ceiling");
    expect(wx_flight_category(10, 200) == WX_LIFR, "ceiling 200 is LIFR");

    double head = 0, cross = 0;
    wx_wind_components(270, 20, 240, &head, &cross);
    expect(near(head, 17.32) && near(cross, 10.0), "270@20 on runway 24: 17.3 head, 10 from right");
    wx_wind_components(60, 10, 240, &head, &cross);
    expect(near(head, -10.0) && near(cross, 0.0), "direct tailwind is negative headwind");
    wx_wind_components(0, 0, 90, nullptr, nullptr);
    expect(true, "null out-pointers don't crash");

    std::printf("%d failure(s)\n", failures);
    return failures == 0 ? 0 : 1;
}
