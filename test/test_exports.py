import pytest
from paths import LIBCRYPTO_SO

from auditwheel_emscripten.exports import get_exports


@pytest.mark.parametrize(
    "shared_lib, expected",
    [
        (
            LIBCRYPTO_SO,
            [
                "X509_it",
                "X509_get1_email",
                "X509_get1_ocsp",
            ],
        ),
    ],
)
def test_exports(shared_lib, expected):
    _, exports = list(get_exports(shared_lib).items())[0]

    export_list = []
    for export in exports:
        field = export.name
        export_list.append(field)

    for expected_export in expected:
        assert (
            expected_export in export_list
        ), f"expected import {expected_export} not found"
