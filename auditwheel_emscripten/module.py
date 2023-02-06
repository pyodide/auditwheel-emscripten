import functools
import os
from pathlib import Path

import leb128

from .emscripten_tools import webassembly
from .emscripten_tools.webassembly import HEADER_SIZE, DylinkType


class ModuleWritable(webassembly.Module):
    def encode_dylink_section(self, dylink: webassembly.Dylink) -> bytes:
        """
        Encode given dylib section to bytes
        """

        _dylink_section = next(self.sections())
        if _dylink_section.name not in ("dylink", "dylink.0"):
            raise RuntimeError(f"dylink section not found in {self.filename}")

        section_name = _dylink_section.name.encode()

        buf = bytearray()

        # section name
        buf.extend(leb128.u.encode(len(section_name)))
        buf += section_name

        # section body
        # 1. MEM_INFO
        subsection_buf = bytearray()
        subsection_buf.extend(leb128.u.encode(dylink.mem_size))
        subsection_buf.extend(leb128.u.encode(dylink.mem_align))
        subsection_buf.extend(leb128.u.encode(dylink.table_size))
        subsection_buf.extend(leb128.u.encode(dylink.table_align))

        buf.extend(leb128.u.encode(DylinkType.MEM_INFO))
        buf.extend(leb128.u.encode(len(subsection_buf)))
        buf.extend(subsection_buf)

        # 2. NEEDED
        subsection_buf = bytearray()
        subsection_buf.extend(leb128.u.encode(len(dylink.needed)))
        for lib in dylink.needed:
            subsection_buf.extend(leb128.u.encode(len(lib.encode())))
            subsection_buf += lib.encode()

        buf.extend(leb128.u.encode(DylinkType.NEEDED))
        buf.extend(leb128.u.encode(len(subsection_buf)))
        buf.extend(subsection_buf)

        # 3. EXPORT_INFO
        subsection_buf = bytearray()
        subsection_buf.extend(leb128.u.encode(len(dylink.export_info)))
        for sym, flags in dylink.export_info.items():
            subsection_buf.extend(leb128.u.encode(len(sym.encode())))
            subsection_buf += sym.encode()
            subsection_buf.extend(leb128.u.encode(flags))

        buf.extend(leb128.u.encode(DylinkType.EXPORT_INFO))
        buf.extend(leb128.u.encode(len(subsection_buf)))
        buf.extend(subsection_buf)

        # 4. IMPORT_INFO
        subsection_buf = bytearray()
        subsection_buf.extend(leb128.u.encode(len(dylink.import_info)))
        for module, fields in dylink.import_info.items():
            for field, flags in fields.items():
                subsection_buf.extend(leb128.u.encode(len(module.encode())))
                subsection_buf += module.encode()
                subsection_buf.extend(leb128.u.encode(len(field.encode())))
                subsection_buf += field.encode()
                subsection_buf.extend(leb128.u.encode(flags))

        buf.extend(leb128.u.encode(DylinkType.IMPORT_INFO))
        buf.extend(leb128.u.encode(len(subsection_buf)))
        buf.extend(subsection_buf)

        section_buf = bytearray()

        # custom section
        section_buf += b"\x00"

        # section size
        section_buf.extend(leb128.u.encode(len(buf)))
        section_buf.extend(buf)

        return bytes(section_buf)

    def patch_dylink(self, data: bytes) -> bytes:
        orignal_module = open(self.filename, "rb").read()
        section = next(self.sections())
        if section.name not in ("dylink", "dylink.0"):
            raise RuntimeError(f"dylink section not found in {self.filename}")

        patched_module = (
            orignal_module[:HEADER_SIZE]
            + data
            + orignal_module[section.offset + section.size :]
        )
        return patched_module

    def patch_needed_path(self, dep_map: dict[str, Path]) -> bytes:
        curfile = Path(self.filename).resolve()

        dylink_section: webassembly.Dylink = self.parse_dylink_section()
        needed_relpath = []
        for needed_lib in dylink_section.needed:
            relpath = os.path.relpath(dep_map[needed_lib], curfile.parent)
            needed_relpath.append(relpath)

        patched_dylink_section = dylink_section._replace(needed=needed_relpath)
        encoded_dylink_section = self.encode_dylink_section(patched_dylink_section)
        patched_module = self.patch_dylink(encoded_dylink_section)

        return patched_module


def parse_dylink_section(dylib: Path):
    """
    Get dylink section from given dylib
    """
    with ModuleWritable(dylib) as m:
        dylink = m.parse_dylink_section()

    return dylink


def patch_needed_libs_path(dylib: Path, dep_map: dict[str, Path]):
    """
    Patch needed path in dylink section
    """
    with ModuleWritable(dylib) as m:
        patched_module = m.patch_needed_path(dep_map)

    return patched_module


@functools.cache
def _load_module(wasm_file):
    return ModuleWritable(wasm_file)


def _get_exports(wasm_file):
    with _load_module(wasm_file) as module:
        exports = module.get_exports()
        return exports


def _get_imports(wasm_file):
    with _load_module(wasm_file) as module:
        imports = module.get_imports()
        return imports


def _get_function_type_by_idx(wasm_file, idx):
    with _load_module(wasm_file) as module:
        function_type = module.get_function_type(idx)
        return function_type


def _get_function_type_by_typeval(wasm_file, typeval):
    with _load_module(wasm_file) as module:
        return module.get_types()[typeval]
