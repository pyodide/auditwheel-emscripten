import tempfile
from pathlib import Path

from .emscripten_tools.webassembly import Import
from .lib_utils import get_all_shared_libs_in_dir, sharedlib_regex
from .module import _get_imports
from .wheel_utils import is_emscripten_wheel, unpack


def get_imports_dylib(dylib_file: Path) -> list[Import]:
    if dylib_file.read_bytes()[:4] not in (b"\0asm", b"asm\0"):
        raise RuntimeError(f"{dylib_file} is not a wasm file")

    exports = _get_imports(dylib_file)
    return exports


def get_imports_wheel_unpacked(
    wheel_extract_dir: str | Path,
) -> dict[str, list[Import]]:
    exports_map = {}

    shared_libs = get_all_shared_libs_in_dir(wheel_extract_dir)
    for shared_lib in shared_libs:
        exports = get_imports_dylib(shared_lib)
        exports_map[str(shared_lib.relative_to(wheel_extract_dir))] = exports

    return exports_map


def get_imports_wheel(wheel_file: Path) -> dict[str, list[Import]]:

    if not is_emscripten_wheel(wheel_file.name):
        raise RuntimeError(f"{wheel_file} is not an emscripten wheel")

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)

        extract_dir = unpack(str(wheel_file), str(tmpdir))
        return get_imports_wheel_unpacked(extract_dir)


def get_imports(wheel_or_so_file: str | Path) -> dict[str, list[Import]]:
    file = Path(wheel_or_so_file)
    if not file.exists():
        raise RuntimeError(f"no such file: {file}")

    so_regex = sharedlib_regex()
    if file.is_dir():
        return get_imports_wheel_unpacked(file)
    elif file.suffix == ".whl":
        return get_imports_wheel(file)
    elif so_regex.search(file.name) is not None:
        return {
            str(file): get_imports_dylib(file),
        }
    else:
        raise RuntimeError(f"unknown file type: {file}")
