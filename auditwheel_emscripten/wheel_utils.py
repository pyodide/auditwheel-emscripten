import re
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Generator

from packaging.utils import parse_wheel_filename

# Copied from auditwheel
WHEEL_INFO_RE = re.compile(
    r"""^(?P<namever>(?P<name>.+?)-(?P<ver>\d.*?))(-(?P<build>\d.*?))?
     -(?P<pyver>[a-z].+?)-(?P<abi>.+?)-(?P<plat>.+?)(\.whl|\.dist-info)$""",
    re.VERBOSE,
)


@contextmanager
def unpack_if_wheel(path: str | Path) -> Generator[Path, None, None]:
    """
    Unpack a wheel to a temporary directory if the input is a wheel,
    then return the path to the temporary directory.
    Otherwise yield an empty path.
    """

    if Path(path).suffix != ".whl":
        yield Path()
    else:
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield unpack(path, tmpdirname)


def is_emscripten_wheel(filename: str) -> bool:
    _, _, _, tags = parse_wheel_filename(filename)
    tag = list(tags)[0]
    platform = tag.platform
    return platform.startswith(("emscripten", "pyodide"))


def parse_wheel_extract_dir(wheel_file: str | Path) -> str:
    """Parse the wheel file name and return the directory name where the wheel
    will be extracted.
    """
    wheel_file = Path(wheel_file)
    m = WHEEL_INFO_RE.match(wheel_file.name)
    if m is None:
        raise ValueError(f"Invalid wheel file name: {wheel_file.name}")

    return m.group("namever")


def unpack(path: str | Path, dest: str | Path = ".") -> Path:
    """Unpack a wheel.
    Wheel content will be unpacked to {dest}/{name}-{ver}, where {name}
    is the package name and {ver} its version.
    :param path: The path to the wheel.
    :param dest: Destination directory (default to current directory).
    """
    path = str(path)
    dest = str(dest)

    result = subprocess.run(
        ["wheel", "unpack", path, "--dest", dest],
        check=True,
        encoding="utf-8",
        capture_output=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to unpack wheel: {result.stderr}")

    return Path(dest) / parse_wheel_extract_dir(path)


def pack(directory: str | Path, dest_dir: str | Path, build_number: str | None) -> None:
    """Repack a previously unpacked wheel directory into a new wheel file.
    The .dist-info/WHEEL file must contain one or more tags so that the target
    wheel file name can be determined.
    :param directory: The unpacked wheel directory
    :param dest_dir: Destination directory (defaults to the current directory)
    :param build_number: Optional build number for the wheel
    """
    directory = str(directory)
    dest_dir = str(dest_dir)

    cmd = ["wheel", "pack", directory, "--dest-dir", dest_dir]

    if build_number is not None:
        cmd.extend(["--build-number", build_number])

    result = subprocess.run(cmd, check=True, encoding="utf-8", capture_output=True)

    if result.returncode != 0:
        raise RuntimeError(f"Failed to pack wheel: {result.stderr}")
