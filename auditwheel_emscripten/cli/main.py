from pathlib import Path

import typer
from rich.pretty import pprint

from .. import get_exports, get_imports, repair, show

app = typer.Typer()


@app.callback(no_args_is_help=True)
def main():
    """Auditwheel-like tool for emscripten wheels and shared libraries."""


@app.command("show")
def _show(
    wheel_or_so_file: Path = typer.Argument(
        ..., help="Path to wheel or a shared library file."
    )
):
    """
    Show shared library dependencies of a wheel or a shared library file.
    """
    try:
        dependencies = show(wheel_or_so_file)
        pprint(dependencies)
    except Exception as e:
        raise e


@app.command("repair")
def _repair(
    wheel_file: Path = typer.Argument(..., help="Path to wheel file."),
    libdir: Path = typer.Option(
        "lib",
        help="Path to the directory containing the shared libraries.",
    ),
    output_dir: Path = typer.Option(
        None,
        help="Directory to output repaired wheel or shared library. (default: overwrite the input file)",
    ),
):
    """
    [Experimental] Repair a wheel file: copy shared libraries to the wheel directory and modify the path in the wheel file.
    """
    try:
        repaired_wheel = repair(
            wheel_file, libdir, output_dir, modify_needed_section=True
        )
        dependencies = show(repaired_wheel)
        pprint(dependencies)
    except RuntimeError as e:
        raise e


@app.command("copy")
def _copy(
    wheel_file: Path = typer.Argument(..., help="Path to wheel file."),
    libdir: Path = typer.Option(
        "lib",
        help="Path to the directory containing the shared libraries.",
    ),
    output_dir: Path = typer.Option(
        None,
        help="Directory to output repaired wheel or shared library. (default: overwrite the input file)",
    ),
):
    """
    Copy shared libraries to the wheel directory. Similar to repair but does not modify the needed section of WASM module.
    """
    try:
        repaired_wheel = repair(
            wheel_file, libdir, output_dir, modify_needed_section=False
        )
        dependencies = show(repaired_wheel)
        pprint(dependencies)
    except RuntimeError as e:
        raise e


@app.command("exports")
def _exports(
    wheel_or_so_file: Path = typer.Argument(
        ..., help="Path to wheel or a shared library file."
    )
):
    """
    Show exports of a wheel or a shared library file.
    """
    try:
        exports = get_exports(wheel_or_so_file)
        for export in exports:
            print(f"{export}:")
            for symbol in exports[export]:
                print(f"{symbol.kind.name:>10}\t{symbol.name}")
    except Exception as e:
        raise e


@app.command("imports")
def _imports(
    wheel_or_so_file: Path = typer.Argument(
        ..., help="Path to wheel or a shared library file."
    )
):
    """
    Show imports of a wheel or a shared library file.
    """
    try:
        imports = get_imports(wheel_or_so_file)
        for _import in imports:
            print(f"{_import}:")
            for symbol in imports[_import]:
                print(f"{symbol.module:>10}{symbol.kind.name:>10}\t{symbol.field}")
    except Exception as e:
        raise e
