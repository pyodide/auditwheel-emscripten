import zipfile
from itertools import chain

import pytest
from auditwheel_emscripten.lib_utils import get_all_shared_libs_in_dir, sha256
from paths import SHAPELY_WHEEL, TEST_DATA

from auditwheel_emscripten.repair import (
    copylib,
    repair,
    resolve_sharedlib,
)
from auditwheel_emscripten.show import show
from auditwheel_emscripten.wheel_utils import WHEEL_INFO_RE, unpack
from auditwheel_emscripten.emscripten_tools.webassembly import parse_dylink_section


def mangled_name(path):
    shorthash = sha256(path)[:8]
    base, extension = path.name.split(".", 1)
    return f"{base}-{shorthash}.{extension}"


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

    dep_map = resolve_sharedlib(wheel_file, ["/not-existing-path", TEST_DATA])
    required_libs = dep_map.keys()
    for expected_lib in expected:
        assert expected_lib in required_libs, f"expected lib {expected_lib} not found"


def test_copylib(tmp_path):
    dep_map = resolve_sharedlib(SHAPELY_WHEEL, TEST_DATA)

    extract_dir = unpack(SHAPELY_WHEEL, tmp_path)
    match = WHEEL_INFO_RE.match(SHAPELY_WHEEL.name)
    assert match is not None
    lib_sdir = match.group("name") + ".libs"
    copied = copylib(extract_dir, dep_map, lib_sdir)

    for original_name, source in dep_map.items():
        expected_name = mangled_name(source)
        assert copied[original_name] == extract_dir / lib_sdir / expected_name
        assert copied[original_name].is_file()
        assert not (extract_dir / lib_sdir / original_name).exists()


def test_copylib_without_mangling(tmp_path):
    dep_map = resolve_sharedlib(SHAPELY_WHEEL, TEST_DATA)
    extract_dir = unpack(SHAPELY_WHEEL, tmp_path)
    copied = copylib(extract_dir, dep_map, "Shapely.libs", mangle=False)

    for original_name in dep_map:
        assert copied[original_name].name == original_name
        assert copied[original_name].is_file()


def test_repair(tmp_path):
    repaired_wheel = repair(SHAPELY_WHEEL, TEST_DATA, tmp_path, modify_rpath=True)

    libs = show(repaired_wheel)
    libs_dependencies = list(chain(*[dep for (dep, _) in libs.values()]))
    geos_c_name = mangled_name(TEST_DATA / "libgeos_c.so")
    geos_name = mangled_name(TEST_DATA / "libgeos.so.3.10.3")

    assert geos_c_name in libs_dependencies
    assert geos_name in libs_dependencies
    assert "libgeos_c.so" not in libs_dependencies
    assert "libgeos.so.3.10.3" not in libs_dependencies
    assert libs[f"Shapely.libs/{geos_c_name}"][0] == [geos_name]
    assert libs[f"Shapely.libs/{geos_name}"][0] == []


def test_repair_without_mangling(tmp_path):
    repaired_wheel = repair(
        SHAPELY_WHEEL, TEST_DATA, tmp_path, modify_rpath=True, mangle=False
    )

    libs = show(repaired_wheel)
    libs_dependencies = list(chain(*[dep for (dep, _) in libs.values()]))
    assert "libgeos_c.so" in libs_dependencies
    assert "libgeos.so.3.10.3" in libs_dependencies
    assert "Shapely.libs/libgeos_c.so" in libs
    assert "Shapely.libs/libgeos.so.3.10.3" in libs


def test_repair_already_repaired_wheel(tmp_path):
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"
    first_output.mkdir()
    second_output.mkdir()
    first_wheel = repair(SHAPELY_WHEEL, TEST_DATA, first_output)
    second_wheel = repair(first_wheel, TEST_DATA, second_output)

    assert show(second_wheel) == show(first_wheel)


def test_repair_regenerates_record_with_mangled_names(tmp_path):
    repaired_wheel = repair(SHAPELY_WHEEL, TEST_DATA, tmp_path)
    geos_c_path = f"Shapely.libs/{mangled_name(TEST_DATA / 'libgeos_c.so')}"
    geos_path = f"Shapely.libs/{mangled_name(TEST_DATA / 'libgeos.so.3.10.3')}"

    with zipfile.ZipFile(repaired_wheel) as wheel:
        names = wheel.namelist()
        record_path = next(name for name in names if name.endswith(".dist-info/RECORD"))
        record = wheel.read(record_path).decode()

    assert geos_c_path in names
    assert geos_path in names
    assert "Shapely.libs/libgeos_c.so" not in names
    assert "Shapely.libs/libgeos.so.3.10.3" not in names
    assert f"{geos_c_path},sha256=" in record
    assert f"{geos_path},sha256=" in record


def test_repair_rpath(tmp_path):
    repaired_wheel = repair(SHAPELY_WHEEL, TEST_DATA, tmp_path, modify_rpath=True)

    # Unpack the wheel and check individual libraries
    extract_dir = unpack(repaired_wheel, tmp_path / "unpacked")
    shared_libs = get_all_shared_libs_in_dir(extract_dir)

    assert len(shared_libs) > 0, "No shared libraries found in the repaired wheel"

    # Each shared library should have the correct runtime path
    for lib in shared_libs:
        lib_dylink = parse_dylink_section(lib)
        expected = (
            "$ORIGIN"
            if lib.parent.name == "Shapely.libs"
            else "$ORIGIN/../../Shapely.libs"
        )
        assert expected in lib_dylink.runtime_paths
