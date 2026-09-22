import shutil
import tempfile
from collections import deque
from pathlib import Path

from .lib_utils import get_all_shared_libs_in_dir, libdir_candidates, sha256
from .module import patch_needed, patch_runtime_path
from .show import locate_dependency, show
from .wheel_utils import WHEEL_INFO_RE, is_emscripten_wheel, pack, unpack


def resolve_sharedlib(
    wheel_file: str | Path, libdir: str | Path | list[str | Path]
) -> dict[str, Path]:
    """
    Resolve the full path of shared libraries inside the wheel file
    """
    libdirs = []
    libdir_list = libdir if isinstance(libdir, list) else [libdir]

    for d in libdir_list:
        libdirs.extend(libdir_candidates(d))

    dependencies = show(wheel_file)
    libraries = list(dependencies)
    dep_queue: deque[tuple[str, tuple[list[str], list[str]]]] = deque(
        dependencies.items()
    )

    dependencies_resolved: dict[str, Path] = {}
    while dep_queue:
        lib, (deps, runtime_paths) = dep_queue.popleft()
        for dep in deps:
            if dep in dependencies_resolved:
                continue
            if locate_dependency(lib, dep, libraries, runtime_paths) is not None:
                continue

            for candidate in libdirs:
                dep_path = candidate / dep
                if dep_path.exists():
                    dependencies_resolved[dep] = dep_path

                    # A shared library can have its own dependencies
                    # So we need to resolve them as well
                    _dependencies = show(dep_path)
                    dep_queue.append((str(dep_path), _dependencies[str(dep_path)]))
                    break
            else:
                raise RuntimeError(f"Cannot find a library: {dep} (required by {lib})")

    return dependencies_resolved


def copylib(
    wheel_extract_dir: str | Path,
    dep_map: dict[str, Path],
    dest_dir: str,
    mangle: bool = True,
) -> dict[str, Path]:
    """
    Copy shared libraries to the destination directory inside a wheel file
    """
    lib_dir = Path(wheel_extract_dir) / dest_dir
    if lib_dir.is_symlink():
        raise RuntimeError(f"Library directory cannot be a symlink: {lib_dir}")
    lib_dir.mkdir(parents=True, exist_ok=True)

    new_dep_map: dict[str, Path] = {}
    for depname, realpath in dep_map.items():
        source_hash = sha256(realpath)
        copied_name = _mangle_name(realpath, source_hash) if mangle else depname
        new_path = lib_dir / copied_name
        if new_path.exists():
            if sha256(new_path) != source_hash:
                raise RuntimeError(
                    f"Library destination conflicts with source: {new_path}"
                )
        else:
            shutil.copy(realpath, new_path)
        new_dep_map[depname] = new_path

    return new_dep_map


def _mangle_name(path: Path, file_hash: str) -> str:
    """Return the content-hashed library name used by auditwheel."""
    shorthash = file_hash[:8]

    try:
        base, extension = path.name.split(".", 1)
    except ValueError as error:
        raise ValueError(
            f"Shared library name must contain a period: {path.name}"
        ) from error

    if base.endswith(f"-{shorthash}"):
        return path.name
    return f"{base}-{shorthash}.{extension}"


def modify_needed(wheel_extract_dir: str | Path, dep_map: dict[str, Path]) -> None:
    """Patch copied library names into dylink dependency declarations."""
    replacements = {name: path.name for name, path in dep_map.items()}
    for shared_lib in get_all_shared_libs_in_dir(wheel_extract_dir):
        patched_module = patch_needed(shared_lib, replacements)
        shared_lib.write_bytes(patched_module)


def modify_runtime_path(wheel_extract_dir: str | Path, runtime_path: str) -> None:
    """
    Patch the runtime path of shared libraries inside the wheel file

    Parameters
    ----------
    wheel_extract_dir : str | Path
        The directory containing the extracted wheel file

    runtime_path : str
        The target directory name where the shared libraries are located
    """
    runtime_path_full = Path(wheel_extract_dir) / runtime_path
    assert runtime_path_full.exists(), f"lib directory not found: {runtime_path_full}"

    shared_libs = get_all_shared_libs_in_dir(wheel_extract_dir)
    for shared_lib in shared_libs:
        patched_module = patch_runtime_path(shared_lib, runtime_path_full)
        shared_lib.write_bytes(patched_module)


def repair(
    wheel_file: str | Path,
    libdir: str | Path,
    outdir: str | Path | None,
    lib_sdir: str = ".libs",
    modify_rpath: bool = True,
    mangle: bool = True,
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
        copied_dep_map = copylib(extract_dir, dep_map, lib_sdir, mangle=mangle)
        if mangle:
            modify_needed(extract_dir, copied_dep_map)
        if modify_rpath:
            modify_runtime_path(extract_dir, lib_sdir)
        pack(str(extract_dir), str(outdir), None)

    return outdir / file.name
