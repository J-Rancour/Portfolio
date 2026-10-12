import itertools

import pytest

from app import wxcore


@pytest.mark.parametrize(
    "vis, ceiling, expected",
    [
        (10, None, "VFR"),
        (10, 5000, "VFR"),
        (4, None, "MVFR"),
        (10, 3000, "MVFR"),
        (10, 800, "IFR"),
        (2, None, "IFR"),
        (0.5, 5000, "LIFR"),
        (10, 200, "LIFR"),
    ],
)
def test_flight_category(vis, ceiling, expected):
    assert wxcore.flight_category(vis, ceiling) == expected


def test_wind_components():
    head, cross = wxcore.wind_components(270, 20, 240)
    assert head == pytest.approx(17.32, abs=0.01)
    assert cross == pytest.approx(10.0, abs=0.01)


@pytest.mark.skipif(wxcore.ENGINE != "cpp", reason="C++ library not built")
def test_cpp_matches_python_reference():
    # The Python fallback doubles as an oracle: both must agree everywhere,
    # including the boundary values (1, 3, 5 sm; 500, 1000, 3000 ft).
    visibilities = [0, 0.5, 0.99, 1, 2.9, 3, 5, 5.01, 10]
    ceilings = [-1, 0, 499, 500, 999, 1000, 3000, 3001, 12000]
    for vis, ceil in itertools.product(visibilities, ceilings):
        expected = wxcore.CATEGORIES[wxcore.py_flight_category(vis, ceil)]
        assert wxcore.flight_category(vis, None if ceil < 0 else ceil) == expected, (vis, ceil)
    for wd, ws, rwy in itertools.product([0, 90, 185, 359], [0, 15], [0, 90, 240]):
        assert wxcore.wind_components(wd, ws, rwy) == pytest.approx(wxcore.py_wind_components(wd, ws, rwy))
