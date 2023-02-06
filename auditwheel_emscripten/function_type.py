from pathlib import Path

from .emscripten_tools.webassembly import FuncType
from .module import _get_function_type_by_idx, _get_function_type_by_typeval


def get_function_type_by_idx(wasm_file: str | Path, idx: int) -> FuncType:
    function_type: FuncType = _get_function_type_by_idx(str(wasm_file), idx)
    return function_type


def get_function_type_by_typeval(wasm_file: str | Path, typeval: int) -> FuncType:
    function_type: FuncType = _get_function_type_by_typeval(str(wasm_file), typeval)
    return function_type


def format_function_type(function_type: FuncType) -> str:
    params = function_type.params
    returns = function_type.returns

    params_str = ", ".join([p.name.lower() for p in params])
    returns_str = ", ".join([p.name.lower() for p in returns])
    return f"({params_str}) -> ({returns_str})"
