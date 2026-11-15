"""Deprecated import path. Auth graduated to ``aws_lambda_powertools.utilities.auth``; this alias goes away in v4."""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import sys
import warnings
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.warnings import PowertoolsDeprecationWarning

if TYPE_CHECKING:
    from importlib.machinery import ModuleSpec
    from types import ModuleType

_OLD = __name__
_NEW = "aws_lambda_powertools.utilities.auth"

warnings.warn(
    f"{_OLD} is deprecated and will be removed in v4. Import from {_NEW} instead; the API is the same.",
    category=PowertoolsDeprecationWarning,
    stacklevel=2,
)


class _AliasFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Serve ``auth_alpha.<submodule>`` with the very same module object as ``auth.<submodule>``."""

    def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> ModuleSpec | None:
        if fullname.startswith(f"{_OLD}."):
            return importlib.util.spec_from_loader(fullname, self)
        return None

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        return importlib.import_module(f"{_NEW}{spec.name[len(_OLD) :]}")

    def exec_module(self, module: ModuleType) -> None:
        return None


if not any(isinstance(finder, _AliasFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, _AliasFinder())


def __getattr__(name: str) -> Any:
    return getattr(importlib.import_module(_NEW), name)


def __dir__() -> list[str]:
    return dir(importlib.import_module(_NEW))
