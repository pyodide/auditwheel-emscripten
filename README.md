# auditwheel-emscripten

[![PyPI Latest Release](https://img.shields.io/pypi/v/auditwheel-emscripten.svg)](https://pypi.org/project/auditwheel-emscripten/)
![Test Status](https://github.com/pyodide/auditwheel-emscripten/actions/workflows/test.yml/badge.svg)

auditwheel-like tool for wheels targeting Emscripten platform

```sh
$ pip install auditwheel-emscripten
```

## What is this?

auditwheel-emscripten is a tiny tool to facilitate the creation of Python wheel packages for
[Emscripten](https://emscripten.org/). auditwheel-emscripten is originally created for
[Pyodide](https://pyodide.org/en/stable/), but it can be used in any other projects that target
Python-in-the-browser using Emscripten.

- `pyodide auditwheel show`: shows external shared libraries that the wheel depends on.
- `pyodide auditwheel repair`: copies these external shared libraries into the wheel itself, and update the RPATH of the WASM module correspondingly.

## Usage (CLI)

```sh
 Usage: pyodide auditwheel [OPTIONS] COMMAND [ARGS]...

 Auditwheel-like tool for emscripten wheels and shared libraries.

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                         │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ copy      [Deprecated] Copy shared libraries to the wheel directory. Works same as repair. Use repair instead.          │
│ exports   Show exports of a wheel or a shared library file.                                                                         │
│ imports   Show imports of a wheel or a shared library file.                                                                         │
│ repair    Repair a wheel file: copy shared libraries to the wheel directory.   │
│ show      Show shared library dependencies of a wheel or a shared library file.                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

```sh
$ pyodide auditwheel show shapely-2.0.7-cp313-cp313-pyodide_2025_0_wasm32.whl
shapely/speedups/_speedups.cpython-310-wasm32-emscripten.so:
        libgeos_c.so

shapely/vectorized/_vectorized.cpython-310-wasm32-emscripten.so:
        libgeos_c.so
```

```sh
$ pyodide auditwheel repair --libdir <directory which contains libgeos_c.so> shapely-2.0.7-cp313-cp313-pyodide_2025_0_wasm32.whl
shapely/lib.cpython-313-wasm32-emscripten.so:
        libgeos_c.so => shapely.libs/libgeos_c.so

shapely/_geometry_helpers.cpython-313-wasm32-emscripten.so:
        libgeos_c.so => shapely.libs/libgeos_c.so

shapely/_geos.cpython-313-wasm32-emscripten.so:
        libgeos_c.so => shapely.libs/libgeos_c.so

shapely.libs/libgeos.so:

shapely.libs/libgeos_c.so:
        libgeos.so => shapely.libs/libgeos.so
```


## Usage (API)

Listing shared library dependencies of a wheel file:

```py
from auditwheel_emscripten import show
libs = show("Shapely-1.8.2-cp310-cp310-emscripten_3_1_14_wasm32.whl")
print(libs)
# {'shapely/vectorized/_vectorized.cpython-310-wasm32-emscripten.so': ['libgeos_c.so'], 'shapely/speedups/_speedups.cpython-310-wasm32-emscripten.so': ['libgeos_c.so']}
```

Copying shared libraries to the wheel:

```py
from auditwheel_emscripten import repair, show
repaired_wheel = repair(
    "Shapely-1.8.2-cp310-cp310-emscripten_3_1_14_wasm32.whl",
    libdir="/path/where/shared/libraries/are/located",
    outdir="/path/to/output/directory",
)
libs = show(repaired_wheel)
print(libs)
# {'Shapely.libs/libgeos.so.3.10.3': [], 'Shapely.libs/libgeos_c.so': ['libgeos.so.3.10.3'], 'shapely/speedups/_speedups.cpython-310-wasm32-emscripten.so': ['libgeos_c.so'], 'shapely/vectorized/_vectorized.cpython-310-wasm32-emscripten.so': ['libgeos_c.so']}
```

## Implementation details / limitations

### Dynamic linking in Emscripten

Dynamic linking is not in the WebAssembly specification,
but Emscripten has its own dynamic linking support,
which is required for building Python wheels targeting Emscripten platform.

This tool is based on:

- Loosely documented Emscripten dynamic linking specification: https://github.com/WebAssembly/tool-conventions/blob/main/DynamicLinking.md
- Emscripten's internal utility for inspecting WASM module: https://github.com/emscripten-core/emscripten/blob/main/tools/webassembly.py
- Emscripten dylink implementation: https://github.com/emscripten-core/emscripten/blob/main/src/library_dylink.js

### auditwheel vs auditwheel-emscripten

`auditwheel` is a tool that helps repair and modify Python wheels (pre-compiled packages)
to be compatible with a wide range of Linux distributions.
It does this by copying external shared libraries into the wheel and
repairing the RPATH (a file path that is used to locate shared libraries at runtime)
of the ELF binary so that the Linux operating system can locate the library when the program is run.

`auditwheel-emscripten` is a variation of auditwheel that is specifically designed
to work with Emscripten-generated WebAssembly (WASM) modules.
It does not perform an audit on the wheel, as Emscripten does not guarantee compatibility between versions.
Instead, it simply copies the required libraries into the wheel without modifying the module itself.
It is up to the user to manually implement a way to locate these libraries at runtime.
