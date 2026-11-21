from __future__ import annotations

from contextlib import contextmanager
from importlib.machinery import SourceFileLoader
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


@contextmanager
def track_layer_compilation(layer_root: str = "/opt/python") -> Iterator[list[str]]:
    """Record source compilation in the layer, restoring the loader even on failure."""
    compiled_files: list[str] = []
    source_to_code = SourceFileLoader.source_to_code
    prefix = f"{layer_root.rstrip('/')}/"

    def track(loader, data, path, *, _optimize=-1):
        if path.startswith(prefix):
            compiled_files.append(path)
        return source_to_code(loader, data, path, _optimize=_optimize)

    SourceFileLoader.source_to_code = track  # type: ignore[method-assign]
    try:
        yield compiled_files
    finally:
        SourceFileLoader.source_to_code = source_to_code  # type: ignore[method-assign]


def verify_layer_bytecode(compiled_files: list[str]) -> None:
    if compiled_files:
        sample = ", ".join(compiled_files[:5])
        raise ValueError(f"Layer recompiled {len(compiled_files)} source files instead of using bytecode: {sample}")
