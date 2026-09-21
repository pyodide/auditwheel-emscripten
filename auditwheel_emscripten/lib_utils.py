import hashlib
import re
from functools import cache
from pathlib import Path


def libdir_candidates(libdir: str | Path) -> list[Path]:
    libdir = Path(libdir)
    return [
        libdir,
        libdir / "lib",
        # search relocatable first.
        libdir / "lib" / "wasm32-emscripten" / "pic",
        libdir / "lib" / "wasm32-emscripten",
    ]


@cache
def sharedlib_regex() -> re.Pattern:
    return re.compile(r"(\.so(.\d+)*|\.wasm)$")


def get_all_shared_libs_in_dir(directory: str | Path) -> list[Path]:
    directory = Path(directory)
    so_regex = sharedlib_regex()
    return list(
        filter(lambda f: so_regex.search(f.name) is not None, directory.glob("**/*"))
    )


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()