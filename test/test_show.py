from itertools import chain

import pytest
from paths import GALPY_WHEEL, NUMPY_WHEEL, SHAPELY_WHEEL

from auditwheel_emscripten.show import show, locate_dependency


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

    libs_dependencies = list(chain(*[dep for (dep, _) in libs.values()]))
    for expected_lib in expected:
        assert (
            expected_lib in libs_dependencies
        ), f"expected lib {expected_lib} not found in dependencies"


def test_locate_dependency():
    # Test case 1: Dependency found in runtime path
    base = "dir/lib.so"
    dep = "libdep.so"
    libraries = ["dir/subdir/libdep.so", "other/lib.so"]
    runtime_paths = ["$ORIGIN/subdir"]

    result = locate_dependency(base, dep, libraries, runtime_paths)
    assert result == "dir/subdir/libdep.so"

    # Test case 2: Dependency not found
    base = "dir/lib.so"
    dep = "libmissing.so"
    libraries = ["dir/subdir/libdep.so", "other/lib.so"]
    runtime_paths = ["$ORIGIN/subdir"]

    result = locate_dependency(base, dep, libraries, runtime_paths)
    assert result is None

    # Test case 3: Multiple runtime paths, dependency in second path
    base = "dir/lib.so"
    dep = "libdep.so"
    libraries = ["dir/path2/libdep.so", "other/lib.so"]
    runtime_paths = ["$ORIGIN/path1", "$ORIGIN/path2"]

    result = locate_dependency(base, dep, libraries, runtime_paths)
    assert result == "dir/path2/libdep.so"

    # Test case 4: rpath contains ".."
    base = "dir/subdir/lib.so"
    dep = "libdep.so"
    libraries = ["dir/libdep.so", "other/lib.so"]
    runtime_paths = ["$ORIGIN/.."]

    result = locate_dependency(base, dep, libraries, runtime_paths)
    assert result == "dir/libdep.so"
