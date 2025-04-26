from itertools import chain

import pytest
from auditwheel_emscripten.lib_utils import get_all_shared_libs_in_dir
from paths import SHAPELY_WHEEL, TEST_DATA

from auditwheel_emscripten.repair import copylib, repair, resolve_sharedlib
from auditwheel_emscripten.show import show
from auditwheel_emscripten.wheel_utils import WHEEL_INFO_RE, unpack
from auditwheel_emscripten.emscripten_tools.webassembly import parse_dylink_section


@pytest.mark.parametrize(
    "wheel_file, expected",
    [
        (
            SHAPELY_WHEEL,
            [
                "libgeos_c.so",
                "libgeos.so.3.10.3",
            ],
        ),
    ],
)
def test_resolve_sharedlib(wheel_file, expected):
    dep_map = resolve_sharedlib(wheel_file, TEST_DATA)
    required_libs = dep_map.keys()

    for expected_lib in expected:
        assert expected_lib in required_libs, f"expected lib {expected_lib} not found"


@pytest.mark.parametrize(
    "wheel_file, expected",
    [
        (
            SHAPELY_WHEEL,
            [
                "libgeos_c.so",
                "libgeos.so.3.10.3",
            ],
        ),
    ],
)
def test_copylib(tmp_path, wheel_file, expected):
    dep_map = resolve_sharedlib(wheel_file, TEST_DATA)

    extract_dir = unpack(wheel_file, tmp_path)
    lib_sdir = WHEEL_INFO_RE.match(wheel_file.name).group("name") + ".libs"
    copylib(extract_dir, dep_map, lib_sdir)

    for expected_lib in expected:
        assert (
            extract_dir / lib_sdir / expected_lib
        ).is_file(), f"expected lib {expected_lib} not found"


@pytest.mark.parametrize(
    "wheel_file, expected",
    [
        (
            SHAPELY_WHEEL,
            [
                "libgeos.so.3.10.3",
                "libgeos_c.so",
            ],
        ),
    ],
)
def test_repair(tmp_path, wheel_file, expected):
    repaired_wheel = repair(wheel_file, TEST_DATA, tmp_path, modify_rpath=True)

    libs = show(repaired_wheel)
    libs_dependencies = list(chain(*[dep for (dep, _) in libs.values()]))
    for expected_lib in expected:
        assert (
            expected_lib in libs_dependencies
        ), f"expected lib {expected_lib} not found in dependencies"


@pytest.mark.parametrize(
    "wheel_file, libname, expected",
    [
        (
            SHAPELY_WHEEL,
            [
                "_speedups.cpython-310-wasm32-emscripten.so",
                "_vectorized.cpython-310-wasm32-emscripten.so",
                "libgeos.so.3.10.3",
                "libgeos_c.so",
            ],
            [
                "$ORIGIN/../../Shapely.libs",
                "$ORIGIN/../../Shapely.libs",
                "$ORIGIN",
                "$ORIGIN",
            ],
        ),
    ],
)
def test_repair_rpath(tmp_path, wheel_file, libname, expected):
    repaired_wheel = repair(wheel_file, TEST_DATA, tmp_path, modify_rpath=True)

    # Unpack the wheel and check individual libraries
    extract_dir = unpack(repaired_wheel, tmp_path / "unpacked")
    shared_libs = get_all_shared_libs_in_dir(extract_dir)

    assert len(shared_libs) > 0, "No shared libraries found in the repaired wheel"

    # Each shared library should have the correct runtime path
    for lib in shared_libs:
        lib_dylink = parse_dylink_section(lib)
        libname_index = libname.index(lib.name)
        assert (
            expected[libname_index] in lib_dylink.runtime_paths
        ), f"expected runtime path {expected[libname_index]} not found in {lib.name}"
