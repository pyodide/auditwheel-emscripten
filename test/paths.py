from pathlib import Path

TEST_DATA = Path(__file__).parent / "test_data"

NUMPY_WHEEL = TEST_DATA / "numpy-1.22.4-cp310-cp310-emscripten_3_1_14_wasm32.whl"
GALPY_WHEEL = TEST_DATA / "galpy-1.8.0-cp310-cp310-emscripten_3_1_14_wasm32.whl"
SHAPELY_WHEEL = TEST_DATA / "Shapely-1.8.2-cp310-cp310-emscripten_3_1_14_wasm32.whl"

LIBSSL_SO = TEST_DATA / "libssl.so"
LIBCRYPTO_SO = TEST_DATA / "libcrypto.so"
