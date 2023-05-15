from auditwheel_emscripten.wasm_utils import is_wasm_module

import pytest
from paths import LIBSSL_SO, ELF_BINARY


@pytest.mark.parametrize(
    "file, expected",
    [
        (LIBSSL_SO, True),
        (ELF_BINARY, False),
    ],
)
def test_is_wasm_module(file, expected):
    assert is_wasm_module(file) == expected
