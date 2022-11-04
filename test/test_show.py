from itertools import chain

import pytest
from paths import GALPY_WHEEL, NUMPY_WHEEL, SHAPELY_WHEEL

from auditwheel_emscripten.show import show


@pytest.mark.parametrize(
    "wheel_file, expected",
    [
        (
            NUMPY_WHEEL,
            [
                "numpy/core/_multiarray_umath.cpython-310-wasm32-emscripten.so",
                "numpy/random/_common.cpython-310-wasm32-emscripten.so",
            ],
        ),
        (
            GALPY_WHEEL,
            [
                "libgalpy.cpython-310-wasm32-emscripten.so",
            ],
        ),
        (
            SHAPELY_WHEEL,
            [
                "shapely/vectorized/_vectorized.cpython-310-wasm32-emscripten.so",
                "shapely/speedups/_speedups.cpython-310-wasm32-emscripten.so",
            ],
        ),
    ],
)
def test_show(wheel_file, expected):
    libs = show(wheel_file)
    libs_inside_wheel = libs.keys()

    assert libs_inside_wheel, "no libs found inside wheel"
    assert all(
        [lib.endswith(".so") for lib in libs_inside_wheel]
    ), "not all libs are .so files"
    for expected_lib in expected:
        assert (
            expected_lib in libs_inside_wheel
        ), f"expected lib {expected_lib} not found"


@pytest.mark.parametrize(
    "wheel_file, expected",
    [
        (
            SHAPELY_WHEEL,
            [
                "libgeos_c.so",
            ],
        ),
    ],
)
def test_show_dependencies(wheel_file, expected):
    libs = show(wheel_file)

    libs_dependencies = list(chain(*libs.values()))
    for expected_lib in expected:
        assert (
            expected_lib in libs_dependencies
        ), f"expected lib {expected_lib} not found in dependencies"
