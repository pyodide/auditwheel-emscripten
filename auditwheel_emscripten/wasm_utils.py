from pathlib import Path


def is_wasm_module(module: Path) -> bool:
    """
    Returns True if the given file is a WASM module.
    """
    with module.open("rb") as f:
        return f.read(4) in (b"\0asm", b"asm\0")
