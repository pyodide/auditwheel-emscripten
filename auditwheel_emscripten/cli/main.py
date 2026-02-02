from pathlib import Path

import click

from .. import function_type, get_exports, get_imports, repair, show
from ..show import locate_dependency
from ..wheel_utils import unpack_if_wheel


@click.group(no_args_is_help=True)
def app():
    """Auditwheel-like tool for emscripten wheels and shared libraries."""


def print_dylib(
    library: str,
    deps: list[str],
    runtime_paths: list[str],
    libraries: list[str],
    show_runtime_paths: bool = False,
):
    """
    Print shared library dependencies and runtime paths.
    The output looks similar to the output of `ldd`
    """
    print(f"{library}:")

    for dep in deps:
        line = f"\t{dep:>10}"
        deppath = locate_dependency(library, dep, libraries, runtime_paths)
        if deppath:
            line += f" => {deppath}"
        print(line)

    if show_runtime_paths and runtime_paths:
        print("\n\tRuntime search paths:")
        for path in runtime_paths:
            print(f"\t  {path}")

    print()


@app.command("show")
@click.argument("wheel_or_so_file", type=click.Path(path_type=Path))
@click.option(
    "--with-runtime-paths",
    "-r",
    "show_runtime_paths",
    is_flag=True,
    help="Show runtime paths.",
)
def _show(
    wheel_or_so_file: Path,
    show_runtime_paths: bool,
):
    """
    Show shared library dependencies of a wheel or a shared library file.

    \b
    Arguments:
        WHEEL_OR_SO_FILE: Path to wheel or a shared library file. (required)
    """
    try:
        libraries = show(wheel_or_so_file)
        for lib, (deps, runtime_paths) in libraries.items():
            print_dylib(
                lib, deps, runtime_paths, list(libraries.keys()), show_runtime_paths
            )
    except Exception as e:
        raise e


@app.command("repair")
@click.argument("wheel_file", type=click.Path(path_type=Path))
@click.option(
    "--libdir",
    type=click.Path(path_type=Path),
    default="lib",
    help="Path to the directory containing the shared libraries.",
    show_default=True,
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory to output repaired wheel or shared library. (default: overwrite the input file)",
)
@click.option(
    "--with-runtime-paths",
    "-r",
    "show_runtime_paths",
    is_flag=True,
    help="Show runtime paths.",
)
def _repair(
    wheel_file: Path,
    libdir: Path,
    output_dir: Path | None,
    show_runtime_paths: bool,
):
    """
    Repair a wheel file: copy shared libraries to the wheel directory.

    \b
    Arguments:
        WHEEL_FILE: Path to wheel file. (required)
    """
    try:
        repaired_wheel = repair(
            wheel_file,
            libdir,
            output_dir,
            modify_rpath=True,
        )
        libraries = show(repaired_wheel)
        for lib, (deps, runtime_paths) in libraries.items():
            print_dylib(
                lib, deps, runtime_paths, list(libraries.keys()), show_runtime_paths
            )
    except RuntimeError as e:
        raise e


@app.command("copy")
@click.argument("wheel_file", type=click.Path(path_type=Path))
@click.option(
    "--libdir",
    type=click.Path(path_type=Path),
    default="lib",
    help="Path to the directory containing the shared libraries.",
    show_default=True,
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory to output repaired wheel or shared library. (default: overwrite the input file)",
)
def _copy(
    wheel_file: Path,
    libdir: Path,
    output_dir: Path | None,
):
    """
    [Deprecated] Copy shared libraries to the wheel directory. Works same as `repair`. Use `repair` instead.

    \b
    Arguments:
        WHEEL_FILE: Path to wheel file. (required)
    """
    return _repair(wheel_file, libdir, output_dir)


@app.command("exports")
@click.argument("wheel_or_so_file", type=click.Path(path_type=Path))
@click.option(
    "--show-type",
    is_flag=True,
    help="Show function type.",
    default=False,
    show_default=True,
)
def _exports(
    wheel_or_so_file: Path,
    show_type: bool,
):
    """
    Show exports of a wheel or a shared library file.

    \b
    Arguments:
        WHEEL_OR_SO_FILE: Path to wheel or a shared library file. (required)
    """
    try:
        exports = get_exports(wheel_or_so_file)
        with unpack_if_wheel(wheel_or_so_file) as unpacked_dir:
            for wasmfile in exports:
                print(f"{wasmfile}:")
                for symbol in exports[wasmfile]:
                    msg = f"{symbol.kind.name:>10}\t{symbol.name}"
                    if show_type:
                        typ = function_type.get_function_type_by_idx(
                            unpacked_dir / wasmfile, symbol.index
                        )
                        msg += f"\t{function_type.format_function_type(typ)}"

                    print(msg)
    except Exception as e:
        raise e


@app.command("imports")
@click.argument("wheel_or_so_file", type=click.Path(path_type=Path))
@click.option(
    "--show-type",
    is_flag=True,
    help="Show function type.",
    default=False,
    show_default=True,
)
def _imports(
    wheel_or_so_file: Path,
    show_type: bool,
):
    """
    Show imports of a wheel or a shared library file.

    \b
    Arguments:
        WHEEL_OR_SO_FILE: Path to wheel or a shared library file. (required)
    """
    try:
        imports = get_imports(wheel_or_so_file)
        with unpack_if_wheel(wheel_or_so_file) as unpacked_dir:
            for wasmfile in imports:
                print(f"{wasmfile}:")
                for symbol in imports[wasmfile]:
                    msg = f"{symbol.module:>10}{symbol.kind.name:>10}\t{symbol.field}"

                    if show_type and symbol.kind.name == "FUNC":
                        typ = function_type.get_function_type_by_typeval(
                            unpacked_dir / wasmfile, symbol.type
                        )
                        msg += f"\t{function_type.format_function_type(typ)}"

                    print(msg)
    except Exception as e:
        raise e
