from itertools import chain

import pytest
from paths import SHAPELY_WHEEL, TEST_DATA

from auditwheel_emscripten.repair import copylib, repair, resolve_sharedlib
from auditwheel_emscripten.show import show
from auditwheel_emscripten.wheel_utils import WHEEL_INFO_RE, unpack


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
                "../../Shapely.libs/libgeos_c.so",
            ],
        ),
    ],
)
def test_repair(tmp_path, wheel_file, expected):
    repaired_wheel = repair(wheel_file, TEST_DATA, tmp_path)

    libs = show(repaired_wheel)
    libs_dependencies = list(chain(*libs.values()))
    for expected_lib in expected:
        assert (
            expected_lib in libs_dependencies
        ), f"expected lib {expected_lib} not found in dependencies"
