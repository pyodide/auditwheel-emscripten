import pytest
from paths import LIBSSL_SO

from auditwheel_emscripten.imports import get_imports


@pytest.mark.parametrize(
    "shared_lib, expected",
    [
        (
            LIBSSL_SO,
            [
                ("GOT.func", "tls1_enc"),
                ("GOT.func", "tls1_mac"),
                ("GOT.mem", "X509_it"),
            ],
        ),
    ],
)
def test_imports(shared_lib, expected):
    _, imports = list(get_imports(shared_lib).items())[0]

    import_list = []
    for _import in imports:
        module = _import.module
        field = _import.field
        import_list.append((module, field))

    for expected_import in expected:
        assert (
            expected_import in import_list
        ), f"expected import {expected_import} not found"
