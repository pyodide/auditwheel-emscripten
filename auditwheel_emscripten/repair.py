import shutil
import tempfile
from collections import deque
from pathlib import Path

from .lib_utils import get_all_shared_libs_in_dir, libdir_candidates
from .module import patch_needed_libs_path
from .show import show
from .wheel_utils import WHEEL_INFO_RE, is_emscripten_wheel, pack, unpack


def resolve_sharedlib(wheel_file: str | Path, libdir: str | Path) -> dict[str, Path]:
    """
    Resolve the full path of shared libraries inside the wheel file
    """

    libdirs = libdir_candidates(libdir)

    dependencies = show(wheel_file)
    dep_queue = deque([lib, deps] for lib, deps in dependencies.items())

    dependencies_resolved: dict[str, Path] = {}
    while dep_queue:
        lib, deps = dep_queue.popleft()
        for dep in deps:
            if dep in dependencies_resolved:
                continue

            for libdir in libdirs:
                dep_path = libdir / dep
                if dep_path.exists():
                    dependencies_resolved[dep] = dep_path

                    # A shared library can have its own dependencies
                    # So we need to resolve them as well
                    _dependencies = show(dep_path)
                    dep_queue.append([str(dep_path), _dependencies[str(dep_path)]])
                    break
            else:
                raise RuntimeError(f"Cannot find a library: {dep} (required by {lib})")

    return dependencies_resolved


def copylib(
    wheel_extract_dir: str | Path, dep_map: dict[str, Path], dest_dir: str
) -> dict[str, Path]:
    """
    Copy shared libraries to the destination directory inside a wheel file
    """
    lib_dir = Path(wheel_extract_dir) / dest_dir
    lib_dir.mkdir(parents=True, exist_ok=True)

    new_dep_map = {}
    for depname, realpath in dep_map.items():
        new_path = lib_dir / depname
        shutil.copy(realpath, new_path)
        new_dep_map[depname] = new_path

    return new_dep_map


def repair_extracted(
    wheel_extract_dir: str | Path,
    dep_map: dict[str, Path],
    lib_sdir: str,
) -> dict[str, Path]:
    dep_map_copied = copylib(wheel_extract_dir, dep_map, lib_sdir)

    shared_libs = get_all_shared_libs_in_dir(wheel_extract_dir)
    for shared_lib in shared_libs:
        patched_module = patch_needed_libs_path(shared_lib, dep_map_copied)
        shared_lib.write_bytes(patched_module)

    return dep_map_copied


def repair(
    wheel_file: str | Path,
    libdir: str | Path,
    outdir: str | Path | None,
    lib_sdir: str = ".libs",
    modify_needed_section: bool = False,
) -> Path:
    file = Path(wheel_file)
    if not file.exists():
        raise RuntimeError(f"no such file: {file}")
    if not is_emscripten_wheel(file.name):
        raise RuntimeError(f"{wheel_file} is not an emscripten wheel")

    match = WHEEL_INFO_RE.match(file.name)
    if match is None:
        raise RuntimeError(f"Failed to parse wheel file name: {file.name}")

    dep_map: dict[str, Path] = resolve_sharedlib(wheel_file, libdir)
    lib_sdir = match.group("name") + lib_sdir
    outdir = file.parent if outdir is None else Path(outdir)

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)

        extract_dir = unpack(str(wheel_file), str(tmpdir))
        if modify_needed_section:
            repair_extracted(extract_dir, dep_map, lib_sdir)
        else:
            copylib(extract_dir, dep_map, lib_sdir)
        pack(str(extract_dir), str(outdir), None)

    return outdir / file.name
