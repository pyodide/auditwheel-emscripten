# auditwheel-emscripten

[![PyPI Latest Release](https://img.shields.io/pypi/v/auditwheel-emscripten.svg)](https://pypi.org/project/auditwheel-emscripten/)
![Test Status](https://github.com/ryanking13/auditwheel-emscripten/actions/workflows/test.yml/badge.svg)



auditwheel-like tool for Pyodide

```sh
$ pip install auditwheel-emscripten
```

## Usage (CLI)

```sh
 Usage: pyodide auditwheel [OPTIONS] COMMAND [ARGS]...

 Auditwheel-like tool for emscripten wheels and shared libraries.

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                         │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ copy      Copy shared libraries to the wheel directory. Similar to repair but does not modify the needed section of WASM module.    │
│ exports   Show exports of a wheel or a shared library file.                                                                         │
│ imports   Show imports of a wheel or a shared library file.                                                                         │
│ repair    [Experimental] Repair a wheel file: copy shared libraries to the wheel directory and modify the path in the wheel file.   │
│ show      Show shared library dependencies of a wheel or a shared library file.                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

```sh
# wget https://cdn.jsdelivr.net/pyodide/v0.21.3/full/Shapely-1.8.2-cp310-cp310-emscripten_3_1_14_wasm32.whl
$ pyodide auditwheel show Shapely-1.8.2-cp310-cp310-emscripten_3_1_14_wasm32.whl

The following external shared libraries are required:
{
│   'shapely/speedups/_speedups.cpython-310-wasm32-emscripten.so': ['libgeos_c.so'],
│   'shapely/vectorized/_vectorized.cpython-310-wasm32-emscripten.so': ['libgeos_c.so']
}
```

```sh
$ pyodide auditwheel copy --libdir <directory which contains libgeos_c.so> Shapely-1.8.2-cp310-cp310-emscripten_3_1_14_wasm32.whl

Repaired wheel has following external shared libraries:
{
│   'Shapely.libs/libgeos.so.3.10.3': [],
│   'Shapely.libs/libgeos_c.so': ['libgeos.so.3.10.3'],
│   'shapely/speedups/_speedups.cpython-310-wasm32-emscripten.so': ['libgeos_c.so'],
│   'shapely/vectorized/_vectorized.cpython-310-wasm32-emscripten.so': ['libgeos_c.so']
}
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
    # If set this to true, modify the needed section of WASM module.
    # Note that is not compatible with WebAssembly dynamic linking ABI.
    # https://github.com/WebAssembly/tool-conventions/blob/main/DynamicLinking.md
    modify_needed_section=False,
)
libs = show(repaired_wheel)
print(libs)
# {'Shapely.libs/libgeos.so.3.10.3': [], 'Shapely.libs/libgeos_c.so': ['libgeos.so.3.10.3'], 'shapely/speedups/_speedups.cpython-310-wasm32-emscripten.so': ['libgeos_c.so'], 'shapely/vectorized/_vectorized.cpython-310-wasm32-emscripten.so': ['libgeos_c.so']}
```
```
