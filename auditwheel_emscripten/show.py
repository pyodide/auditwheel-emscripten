import tempfile
from pathlib import Path

from .lib_utils import get_all_shared_libs_in_dir, sharedlib_regex
from .module import parse_dylink_section
from .wheel_utils import is_emscripten_wheel, unpack
from .wasm_utils import is_wasm_module


def show_dylib(dylib_file: Path) -> list[str]:
    if not is_wasm_module(dylib_file):
        raise RuntimeError(f"{dylib_file} is not a WASM file")

    dylink = parse_dylink_section(dylib_file)
    return dylink.needed


def show_wheel_unpacked(wheel_extract_dir: str | Path) -> dict[str, list[str]]:
    dependencies = {}

    shared_libs = get_all_shared_libs_in_dir(wheel_extract_dir)
    for shared_lib in shared_libs:
        deps = show_dylib(shared_lib)
        dependencies[str(shared_lib.relative_to(wheel_extract_dir))] = deps

    return dependencies


def show_wheel(wheel_file: Path) -> dict[str, list[str]]:
    if not is_emscripten_wheel(wheel_file.name):
        raise RuntimeError(f"{wheel_file} is not an emscripten wheel")

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)

        extract_dir = unpack(str(wheel_file), str(tmpdir))
        return show_wheel_unpacked(extract_dir)


def show(wheel_or_so_file: str | Path) -> dict[str, list[str]]:
    file = Path(wheel_or_so_file)
    if not file.exists():
        raise RuntimeError(f"no such file: {file}")

    so_regex = sharedlib_regex()
    if file.is_dir():
        return show_wheel_unpacked(file)
    elif file.suffix == ".whl":
        return show_wheel(file)
    elif so_regex.search(file.name) is not None:
        return {
            str(file): show_dylib(file),
        }
    else:
        raise RuntimeError(f"unknown file type: {file}")
