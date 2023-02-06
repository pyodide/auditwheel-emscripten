import pytest
from paths import LIBCRYPTO_SO, LIBSSL_SO

from auditwheel_emscripten.exports import get_exports
from auditwheel_emscripten.function_type import (
    format_function_type,
    get_function_type_by_idx,
    get_function_type_by_typeval,
)
from auditwheel_emscripten.imports import get_imports


@pytest.mark.parametrize(
    "shared_lib, expected",
    [
        (
            LIBCRYPTO_SO,
            {
                "X509_get1_email": "(i32) -> (i32)",
                "X509_email_free": "(i32) -> ()",
            },
        ),
    ],
)
def test_get_function_type_by_idx(shared_lib, expected):
    wasmfile, exports = list(get_exports(shared_lib).items())[0]

    for export in exports:
        func_name = export.name
        if func_name in expected:
            function_type = get_function_type_by_idx(wasmfile, export.index)
            formatted = format_function_type(function_type)
            assert (
                formatted == expected[func_name]
            ), f"expected {expected[func_name]} but got {formatted}"


@pytest.mark.parametrize(
    "shared_lib, expected",
    [
        (
            LIBSSL_SO,
            {
                "RSA_private_decrypt": "(i32, i32, i32, i32, i32) -> (i32)",
                "memchr": "(i32, i32, i32) -> (i32)",
            },
        ),
    ],
)
def test_get_function_type_by_typeval(shared_lib, expected):
    wasmfile, imports = list(get_imports(shared_lib).items())[0]

    for _import in imports:
        func_name = _import.field
        if func_name in expected:
            function_type = get_function_type_by_typeval(wasmfile, _import.type)
            formatted = format_function_type(function_type)
            assert (
                formatted == expected[func_name]
            ), f"expected {expected[func_name]} but got {formatted}"
