"""OpenAPI Merge - Generate unified OpenAPI schema from multiple Lambda handlers."""

from __future__ import annotations

import ast
import fnmatch
import importlib.util
import logging
import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from aws_lambda_powertools.event_handler.openapi.config import OpenAPIConfig
from aws_lambda_powertools.event_handler.openapi.constants import (
    DEFAULT_API_VERSION,
    DEFAULT_OPENAPI_TITLE,
    DEFAULT_OPENAPI_VERSION,
)
from aws_lambda_powertools.event_handler.openapi.exceptions import OpenAPIMergeError

if TYPE_CHECKING:
    from aws_lambda_powertools.event_handler.openapi.models import (
        Contact,
        ExternalDocumentation,
        License,
        SecurityScheme,
        Server,
        Tag,
    )

logger = logging.getLogger(__name__)

ConflictStrategy = Literal["warn", "error", "first", "last"]

RESOLVER_CLASSES = frozenset(
    {
        "APIGatewayRestResolver",
        "APIGatewayHttpResolver",
        "ALBResolver",
        "LambdaFunctionUrlResolver",
        "VPCLatticeResolver",
        "VPCLatticeV2Resolver",
        "BedrockAgentResolver",
        "ApiGatewayResolver",
    },
)


def _is_resolver_call(node: ast.expr) -> bool:
    """Check if an AST node is a call to a resolver class."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id in RESOLVER_CLASSES:
        return True
    if isinstance(func, ast.Attribute) and func.attr in RESOLVER_CLASSES:
        return True
    return False


def _file_has_resolver(file_path: Path, resolver_name: str) -> bool:
    """Check if a Python file contains a resolver instance using AST."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return False

    for node in ast.walk(tree):
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        for target in targets:
            if isinstance(target, ast.Name) and target.id == resolver_name:
                if value is not None and _is_resolver_call(value):
                    return True
    return False


def _file_imports_resolver(file_path: Path, resolver_file: Path, resolver_name: str, root: Path) -> bool:
    """Check if a Python file imports the resolver from the resolver file."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return False

    # Get the module path of the resolver file relative to root
    # e.g., "service/handlers/utils/rest_api_resolver.py" -> "service.handlers.utils.rest_api_resolver"
    resolver_relative = resolver_file.relative_to(root).with_suffix("")
    resolver_module = ".".join(resolver_relative.parts)

    for node in ast.walk(tree):
        # Check "from X import app" or "from X import app as something"
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name == resolver_name:
                    # Check if the import module matches the resolver module
                    if node.module == resolver_module:
                        return True
    return False


def _find_dependent_files(
    search_path: Path,
    resolver_file: Path,
    resolver_name: str,
    exclude: list[str],
    project_root: Path,
) -> list[Path]:
    """Find all Python files that import the resolver.

    Parameters
    ----------
    search_path : Path
        Directory to search for dependent files.
    resolver_file : Path
        The resolver file that dependents import from.
    resolver_name : str
        Variable name of the resolver.
    exclude : list[str]
        Patterns to exclude.
    project_root : Path
        Root directory for resolving Python imports.
    """
    dependent_files: list[Path] = []

    for file_path in search_path.rglob("*.py"):
        if file_path == resolver_file:
            continue
        if _is_excluded(file_path, search_path, exclude):
            continue
        if _file_imports_resolver(file_path, resolver_file, resolver_name, project_root):
            dependent_files.append(file_path)

    return sorted(dependent_files)


def _is_excluded(file_path: Path, root: Path, exclude_patterns: list[str]) -> bool:
    """Check if a file matches any exclusion pattern."""
    relative_str = str(file_path.relative_to(root))

    for pattern in exclude_patterns:
        if pattern.startswith("**/"):
            sub_pattern = pattern[3:]
            if fnmatch.fnmatch(relative_str, pattern) or fnmatch.fnmatch(file_path.name, sub_pattern):
                return True
            clean_pattern = sub_pattern.replace("/**", "").replace("/*", "")
            for part in file_path.relative_to(root).parts:
                if fnmatch.fnmatch(part, clean_pattern):
                    return True
        elif fnmatch.fnmatch(relative_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):
            return True
    return False


def _get_glob_pattern(pat: str, recursive: bool) -> str:
    """Get the glob pattern based on recursive flag."""
    if recursive and not pat.startswith("**/"):
        return f"**/{pat}"
    if not recursive and pat.startswith("**/"):
        return pat[3:]
    return pat


def _discover_resolver_files(
    path: str | Path,
    pattern: str | list[str],
    exclude: list[str],
    resolver_name: str,
    recursive: bool = False,
) -> list[Path]:
    """Discover Python files containing resolver instances."""
    root = Path(path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")

    patterns = [pattern] if isinstance(pattern, str) else pattern
    found_files: set[Path] = set()

    for pat in patterns:
        glob_pattern = _get_glob_pattern(pat, recursive)
        for file_path in root.glob(glob_pattern):
            if (
                file_path.is_file()
                and not _is_excluded(file_path, root, exclude)
                and _file_has_resolver(file_path, resolver_name)
            ):
                found_files.add(file_path)

    return sorted(found_files)


def _load_module(file_path: Path, module_name: str) -> Any:
    """Load a Python module from file."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_resolver_with_dependencies(
    file_path: Path,
    resolver_name: str,
    dependent_files: list[Path],
    root: Path,
) -> Any:
    """Load a resolver instance, first loading all dependent files that register routes."""
    file_path = Path(file_path).resolve()

    # Add root to sys.path if not already there
    root_str = str(root)
    original_path = sys.path.copy()

    try:
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

        # First, load all dependent files (they will import the resolver and register routes)
        for dep_file in dependent_files:
            dep_module_name = f"_powertools_dep_{dep_file.stem}_{id(dep_file)}"
            try:
                _load_module(dep_file, dep_module_name)
                logger.debug(f"Loaded dependent file: {dep_file}")
            except Exception as e:
                warnings.warn(
                    f"Failed to load dependent file {dep_file}: {e}. "
                    "If your handler module has side effects at import time "
                    "(e.g. environment variable validation, database connections), "
                    "consider deferring them to runtime.",
                    stacklevel=2,
                )

        # Now get the resolver - it should already be loaded by the dependent files
        # Try to get it from the module that was loaded by dependents
        resolver_relative = file_path.relative_to(root).with_suffix("")
        resolver_module_name = ".".join(resolver_relative.parts)

        if resolver_module_name in sys.modules:
            module = sys.modules[resolver_module_name]
        else:
            # Fallback: load the resolver file directly
            module_name = f"_powertools_openapi_merge_{file_path.stem}_{id(file_path)}"
            module = _load_module(file_path, module_name)

        if not hasattr(module, resolver_name):
            raise AttributeError(f"Resolver '{resolver_name}' not found in {file_path}.")
        return getattr(module, resolver_name)
    finally:
        sys.path = original_path


def _model_to_dict(obj: Any) -> Any:
    """Convert Pydantic model to dict if needed."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(by_alias=True, exclude_none=True)
    return obj


class OpenAPIMerge:
    """
    Discover and merge OpenAPI schemas from multiple Lambda handlers.

    This class supports two patterns:
    1. Standard pattern: Each handler file defines its own resolver with routes
    2. Shared resolver pattern: A central resolver file is imported by multiple handler files
       that register routes on it

    For the shared resolver pattern, this class automatically discovers files that import
    the resolver and loads them before extracting the schema, ensuring all routes are registered.
    """

    def __init__(
        self,
        *,
        title: str = DEFAULT_OPENAPI_TITLE,
        version: str = DEFAULT_API_VERSION,
        openapi_version: str = DEFAULT_OPENAPI_VERSION,
        summary: str | None = None,
        description: str | None = None,
        tags: list[Tag | str] | None = None,
        servers: list[Server] | None = None,
        terms_of_service: str | None = None,
        contact: Contact | None = None,
        license_info: License | None = None,
        security_schemes: dict[str, SecurityScheme] | None = None,
        security: list[dict[str, list[str]]] | None = None,
        external_documentation: ExternalDocumentation | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        on_conflict: ConflictStrategy = "warn",
    ):
        self._config = OpenAPIConfig(
            title=title,
            version=version,
            openapi_version=openapi_version,
            summary=summary,
            description=description,
            tags=tags,
            servers=servers,
            terms_of_service=terms_of_service,
            contact=contact,
            license_info=license_info,
            security_schemes=security_schemes,
            security=security,
            external_documentation=external_documentation,
            openapi_extensions=openapi_extensions,
        )
        self._schemas: list[dict[str, Any]] = []
        self._discovered_files: list[Path] = []
        self._dependent_files: dict[Path, list[Path]] = {}
        self._resolver_name: str = "app"
        self._on_conflict = on_conflict
        self._cached_schema: dict[str, Any] | None = None
        self._root: Path | None = None
        self._exclude: list[str] = []

    def discover(
        self,
        path: str | Path,
        pattern: str | list[str] = "handler.py",
        exclude: list[str] | None = None,
        resolver_name: str = "app",
        recursive: bool = False,
        project_root: str | Path | None = None,
    ) -> list[Path]:
        """Discover resolver files and their dependent handler files.

        Parameters
        ----------
        path : str | Path
            Directory to search for resolver files.
        pattern : str | list[str]
            Glob pattern(s) to match handler files.
        exclude : list[str] | None
            Patterns to exclude.
        resolver_name : str
            Variable name of the resolver instance.
        recursive : bool
            Whether to search recursively.
        project_root : str | Path | None
            Root directory for resolving Python imports. If None, uses current working directory.
            This is needed when handlers import the resolver using absolute imports like
            'from service.handlers.utils.resolver import app'.
        """
        exclude = exclude or ["**/tests/**", "**/__pycache__/**", "**/.venv/**"]
        self._exclude = exclude
        self._resolver_name = resolver_name
        self._search_path = Path(path).resolve()
        self._root = Path(project_root).resolve() if project_root else self._search_path

        self._discovered_files = _discover_resolver_files(path, pattern, exclude, resolver_name, recursive)

        # For each resolver file, find files that import it (search within path, resolve imports with project_root)
        for resolver_file in self._discovered_files:
            dependent = _find_dependent_files(self._search_path, resolver_file, resolver_name, exclude, self._root)
            self._dependent_files[resolver_file] = dependent
            logger.debug(f"Found {len(dependent)} dependent files for {resolver_file}")

        return self._discovered_files

    def add_file(self, file_path: str | Path, resolver_name: str | None = None) -> None:
        """Add a specific file to be included in the merge.

        Note: Must be called before get_openapi_schema(). Adding files after
        schema generation will not affect the cached result.
        """
        path = Path(file_path).resolve()
        if path not in self._discovered_files:
            self._discovered_files.append(path)
        if resolver_name:
            self._resolver_name = resolver_name

    def add_schema(self, schema: dict[str, Any]) -> None:
        """Add a pre-generated OpenAPI schema to be merged.

        Note: Must be called before get_openapi_schema(). Adding schemas after
        schema generation will not affect the cached result.
        """
        self._schemas.append(_model_to_dict(schema))

    @property
    def discovered_files(self) -> list[Path]:
        """Get the list of discovered resolver files."""
        return self._discovered_files.copy()

    @property
    def dependent_files(self) -> dict[Path, list[Path]]:
        """Get the mapping of resolver files to their dependent handler files."""
        return {k: v.copy() for k, v in self._dependent_files.items()}

    def get_openapi_schema(self) -> dict[str, Any]:
        """Generate the merged OpenAPI schema."""
        if self._cached_schema is not None:
            return self._cached_schema

        for file_path in self._discovered_files:
            try:
                dependent = self._dependent_files.get(file_path, [])
                root = self._root or file_path.parent
                resolver = _load_resolver_with_dependencies(
                    file_path,
                    self._resolver_name,
                    dependent,
                    root,
                )
                if hasattr(resolver, "get_openapi_schema"):
                    self._schemas.append(_model_to_dict(resolver.get_openapi_schema()))
            except (ImportError, AttributeError, FileNotFoundError) as e:
                warnings.warn(
                    f"Failed to load resolver from {file_path}: {e}. "
                    "If your handler module has side effects at import time "
                    "(e.g. environment variable validation, database connections), "
                    "consider deferring them to runtime.",
                    stacklevel=1,
                )

        self._cached_schema = self._merge_schemas()

        if self._discovered_files and not self._cached_schema.get("paths"):
            warnings.warn(
                f"OpenAPIMerge discovered {len(self._discovered_files)} handler file(s) "
                "but the final schema has no paths. "
                "Check if your handler modules have side effects at import time "
                "that prevent route registration.",
                stacklevel=1,
            )

        return self._cached_schema

    def get_openapi_json_schema(self) -> str:
        """Generate the merged OpenAPI schema as JSON string."""
        from aws_lambda_powertools.event_handler.openapi.compat import model_json
        from aws_lambda_powertools.event_handler.openapi.models import OpenAPI

        schema = self.get_openapi_schema()
        return model_json(OpenAPI(**schema), by_alias=True, exclude_none=True, indent=2)

    def _merge_schemas(self) -> dict[str, Any]:
        """Merge all schemas into a single OpenAPI schema."""
        cfg = self._config

        merged: dict[str, Any] = {
            "openapi": cfg.openapi_version,
            "info": {"title": cfg.title, "version": cfg.version},
            "servers": [_model_to_dict(s) for s in cfg.servers] if cfg.servers else [{"url": "/"}],
        }

        self._add_optional_info_fields(merged, cfg)

        merged_paths: dict[str, Any] = {}
        merged_components: dict[str, dict[str, Any]] = {}

        for schema in self._schemas:
            self._merge_paths(schema.get("paths", {}), merged_paths)
            self._merge_components(schema.get("components", {}), merged_components)

        if cfg.security_schemes:
            merged_components.setdefault("securitySchemes", {}).update(cfg.security_schemes)

        if merged_paths:
            merged["paths"] = merged_paths
        if merged_components:
            merged["components"] = merged_components

        if merged_tags := self._merge_tags():
            merged["tags"] = merged_tags

        return merged

    def _add_optional_info_fields(self, merged: dict[str, Any], cfg: OpenAPIConfig) -> None:
        """Add optional fields from config to the merged schema."""
        if cfg.summary:
            merged["info"]["summary"] = cfg.summary
        if cfg.description:
            merged["info"]["description"] = cfg.description
        if cfg.terms_of_service:
            merged["info"]["termsOfService"] = cfg.terms_of_service
        if cfg.contact:
            merged["info"]["contact"] = _model_to_dict(cfg.contact)
        if cfg.license_info:
            merged["info"]["license"] = _model_to_dict(cfg.license_info)
        if cfg.security:
            merged["security"] = cfg.security
        if cfg.external_documentation:
            merged["externalDocs"] = _model_to_dict(cfg.external_documentation)
        if cfg.openapi_extensions:
            merged.update(cfg.openapi_extensions)

    def _merge_paths(self, source_paths: dict[str, Any], target: dict[str, Any]) -> None:
        """Merge paths from source into target."""
        for path, path_item in source_paths.items():
            if path not in target:
                target[path] = path_item
            else:
                for method, operation in path_item.items():
                    if method not in target[path]:
                        target[path][method] = operation
                    else:
                        self._handle_conflict(method, path, target, operation)

    def _handle_conflict(self, method: str, path: str, target: dict, operation: Any) -> None:
        """Handle path/method conflict based on strategy."""
        msg = f"Conflict: {method.upper()} {path} is defined in multiple schemas"
        if self._on_conflict == "error":
            raise OpenAPIMergeError(msg)
        elif self._on_conflict == "warn":
            logger.warning(f"{msg}. Keeping first definition.")
        elif self._on_conflict == "last":
            target[path][method] = operation

    def _merge_components(self, source: dict[str, Any], target: dict[str, dict[str, Any]]) -> None:
        """Merge components from source into target."""
        for component_type, components in source.items():
            target.setdefault(component_type, {}).update(components)

    def _merge_tags(self) -> list[dict[str, Any]]:
        """Merge tags from config and schemas."""
        tags_map: dict[str, dict[str, Any]] = {}

        for tag in self._config.tags or []:
            if isinstance(tag, str):
                tags_map[tag] = {"name": tag}
            else:
                tag_dict = _model_to_dict(tag)
                tags_map[tag_dict["name"]] = tag_dict

        for schema in self._schemas:
            for tag in schema.get("tags", []):
                name = tag["name"] if isinstance(tag, dict) else tag
                if name not in tags_map:
                    tags_map[name] = tag if isinstance(tag, dict) else {"name": tag}

        return list(tags_map.values())
