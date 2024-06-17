import pytest

from auditwheel_emscripten.wheel_utils import is_emscripten_wheel


@pytest.mark.parametrize(
    "wheel_name, expected",
    [
        ("foo-1.0-cp38-cp38-linux_x86_64.whl", False),
        ("foo-1.0-py3-none-any.whl", False),
        ("foo-1.0-cp312-cp312-pyodide_2024_0_wasm32.whl", True),
        ("foo-1.0-cp312-cp312-emscripten_3_1_52_wasm32.whl", True),
    ],
)
def test_is_emscripten_wheel(wheel_name, expected):
    assert is_emscripten_wheel(wheel_name) == expected
