#include "wxcore.h"

#include <algorithm>
#include <cmath>

namespace {

const double kPi = 3.14159265358979323846;

int category_from_visibility(double vis_sm) {
    if (vis_sm < 1.0) return WX_LIFR;
    if (vis_sm < 3.0) return WX_IFR;
    if (vis_sm <= 5.0) return WX_MVFR;
    return WX_VFR;
}

int category_from_ceiling(double ceiling_ft) {
    if (ceiling_ft < 0.0) return WX_VFR;  // no ceiling reported
    if (ceiling_ft < 500.0) return WX_LIFR;
    if (ceiling_ft < 1000.0) return WX_IFR;
    if (ceiling_ft <= 3000.0) return WX_MVFR;
    return WX_VFR;
}

}  // namespace

extern "C" {

int wx_flight_category(double visibility_sm, double ceiling_ft) {
    // The worse of the two conditions wins (higher enum value = worse).
    return std::max(category_from_visibility(visibility_sm), category_from_ceiling(ceiling_ft));
}

void wx_wind_components(double wind_dir_deg, double wind_speed_kt, double runway_heading_deg,
                        double* headwind_kt, double* crosswind_kt) {
    // Out-pointers can be null if the caller only wants one value.
    double angle = (wind_dir_deg - runway_heading_deg) * kPi / 180.0;
    if (headwind_kt) *headwind_kt = wind_speed_kt * std::cos(angle);
    if (crosswind_kt) *crosswind_kt = wind_speed_kt * std::sin(angle);
}

const char* wx_version(void) {
    // A string literal has static storage, so returning its pointer is safe.
    // Returning a pointer to a local buffer here would be a dangling pointer.
    return "wxcore 1.0";
}

}  // extern "C"
