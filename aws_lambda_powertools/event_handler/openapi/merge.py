"""OpenAPI Merge - Generate unified OpenAPI schema from multiple Lambda handlers."""

from __future__ import annotations

import ast
import fnmatch
import importlib.util
import logging
import sys
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
    if isinstance(func, ast.Attribute) and func.attr in RESOLVER_CLASSES:  # pragma: no cover
        return True
    return False  # pragma: no cover


def _file_has_resolver(file_path: Path, resolver_name: str) -> bool:
    """Check if a Python file contains a resolver instance using AST."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == resolver_name:
                    if _is_resolver_call(node.value):
                        return True
    return False


def _is_excluded(file_path: Path, root: Path, exclude_patterns: list[str]) -> bool:
    """Check if a file matches any exclusion pattern."""
    relative_str = str(file_path.relative_to(root))

    for pattern in exclude_patterns:
        if pattern.startswith("**/"):
            sub_pattern = pattern[3:]
            if fnmatch.fnmatch(relative_str, pattern) or fnmatch.fnmatch(file_path.name, sub_pattern):
                return True
            # Check directory parts - remove trailing glob patterns
            clean_pattern = sub_pattern.replace("/**", "").replace("/*", "")
            for part in file_path.relative_to(root).parts:
                if fnmatch.fnmatch(part, clean_pattern):  # pragma: no cover
                    return True
        elif fnmatch.fnmatch(relative_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):  # pragma: no cover
            return True
    return False


def _get_glob_pattern(pat: str, recursive: bool) -> str:
    """Get the glob pattern based on recursive flag."""
    if recursive and not pat.startswith("**/"):
        return f"**/{pat}"
    if not recursive and pat.startswith("**/"):
        return pat[3:]  # Strip **/ prefix
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


def _load_resolver(file_path: Path, resolver_name: str) -> Any:
    """Load a resolver instance from a Python file."""
    file_path = Path(file_path).resolve()
    module_name = f"_powertools_openapi_merge_{file_path.stem}_{id(file_path)}"

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"Cannot load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    module_dir = str(file_path.parent)
    original_path = sys.path.copy()

    try:
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        if not hasattr(module, resolver_name):
            raise AttributeError(f"Resolver '{resolver_name}' not found in {file_path}.")
        return getattr(module, resolver_name)
    finally:
        sys.path = original_path
        sys.modules.pop(module_name, None)


def _model_to_dict(obj: Any) -> Any:
    """Convert Pydantic model to dict if needed."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(by_alias=True, exclude_none=True)
    return obj  # pragma: no cover


class OpenAPIMerge:
    """
    Discover and merge OpenAPI schemas from multiple Lambda handlers.

    This class is designed for micro-functions architectures where you have multiple
    Lambda functions, each with its own resolver, and need to generate a unified
    OpenAPI specification. It's particularly useful for:

    - CI/CD pipelines to generate and publish unified API documentation
    - Build-time schema generation for API Gateway imports
    - Creating a dedicated Lambda that serves the consolidated OpenAPI spec

    The class uses AST analysis to detect resolver instances without importing modules,
    making discovery fast and safe.

    Parameters
    ----------
    title : str
        The title of the unified API.
    version : str
        The version of the API (e.g., "1.0.0").
    openapi_version : str, default "3.1.0"
        The OpenAPI specification version.
    summary : str, optional
        A short summary of the API.
    description : str, optional
        A detailed description of the API.
    tags : list[Tag | str], optional
        Tags for API documentation organization.
    servers : list[Server], optional
        Server objects for API connectivity information.
    terms_of_service : str, optional
        URL to the Terms of Service.
    contact : Contact, optional
        Contact information for the API.
    license_info : License, optional
        License information for the API.
    security_schemes : dict[str, SecurityScheme], optional
        Security scheme definitions.
    security : list[dict[str, list[str]]], optional
        Global security requirements.
    external_documentation : ExternalDocumentation, optional
        Link to external documentation.
    openapi_extensions : dict[str, Any], optional
        OpenAPI specification extensions (x-* fields).
    on_conflict : Literal["warn", "error", "first", "last"], default "warn"
        Strategy when the same path+method is defined in multiple handlers:
        - "warn": Log warning and keep first definition
        - "error": Raise OpenAPIMergeError
        - "first": Silently keep first definition
        - "last": Use last definition (override)

    Example
    -------
    **CI/CD Pipeline - Generate unified schema at build time:**

    >>> from aws_lambda_powertools.event_handler.openapi import OpenAPIMerge
    >>>
    >>> merge = OpenAPIMerge(
    ...     title="My Unified API",
    ...     version="1.0.0",
    ...     description="Consolidated API from multiple Lambda functions",
    ... )
    >>> merge.discover(
    ...     path="./src/functions",
    ...     pattern="**/handler.py",
    ...     exclude=["**/tests/**"],
    ... )
    >>> schema_json = merge.get_openapi_json_schema()
    >>>
    >>> # Write to file for API Gateway import or documentation
    >>> with open("openapi.json", "w") as f:
    ...     f.write(schema_json)

    **Dedicated OpenAPI Lambda - Serve unified spec at runtime:**

    >>> from aws_lambda_powertools.event_handler import APIGatewayRestResolver
    >>>
    >>> app = APIGatewayRestResolver()
    >>> app.configure_openapi_merge(
    ...     path="./functions",
    ...     pattern="**/handler.py",
    ...     title="My API",
    ...     version="1.0.0",
    ... )
    >>> app.enable_swagger(path="/docs")  # Swagger UI with merged schema
    >>>
    >>> def handler(event, context):
    ...     return app.resolve(event, context)

    See Also
    --------
    OpenAPIMergeError : Exception raised on merge conflicts when on_conflict="error"
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
        self._resolver_name: str = "app"
        self._on_conflict = on_conflict
        self._cached_schema: dict[str, Any] | None = None

    def discover(
        self,
        path: str | Path,
        pattern: str | list[str] = "handler.py",
        exclude: list[str] | None = None,
        resolver_name: str = "app",
        recursive: bool = False,
    ) -> list[Path]:
        """
        Discover resolver files in the specified path using glob patterns.

        This method scans the directory tree for Python files matching the pattern,
        then uses AST analysis to identify files containing resolver instances.

        Parameters
        ----------
        path : str | Path
            Root directory to search for handler files.
        pattern : str | list[str], default "handler.py"
            Glob pattern(s) to match handler files.
        exclude : list[str], optional
            Patterns to exclude. Defaults to ["**/tests/**", "**/__pycache__/**", "**/.venv/**"].
        resolver_name : str, default "app"
            Variable name of the resolver instance in handler files.
        recursive : bool, default False
            Whether to search recursively in subdirectories.

        Returns
        -------
        list[Path]
            List of discovered files containing resolver instances.

        Example
        -------
        >>> merge = OpenAPIMerge(title="API", version="1.0.0")
        >>> files = merge.discover(
        ...     path="./src",
        ...     pattern=["handler.py", "api.py"],
        ...     exclude=["**/tests/**", "**/legacy/**"],
        ...     recursive=True,
        ... )
        >>> print(f"Found {len(files)} handlers")
        """
        exclude = exclude or ["**/tests/**", "**/__pycache__/**", "**/.venv/**"]
        self._resolver_name = resolver_name
        self._discovered_files = _discover_resolver_files(path, pattern, exclude, resolver_name, recursive)
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

    def get_openapi_schema(self) -> dict[str, Any]:
        """
        Generate the merged OpenAPI schema as a dictionary.

        Loads all discovered resolver files, extracts their OpenAPI schemas,
        and merges them into a single unified specification.

        The schema is cached after the first generation for performance.

        Returns
        -------
        dict[str, Any]
            The merged OpenAPI schema.

        Raises
        ------
        OpenAPIMergeError
            If on_conflict="error" and duplicate path+method combinations are found.
        """
        if self._cached_schema is not None:
            return self._cached_schema

        # Load schemas from discovered files
        for file_path in self._discovered_files:
            try:
                resolver = _load_resolver(file_path, self._resolver_name)
                if hasattr(resolver, "get_openapi_schema"):
                    self._schemas.append(_model_to_dict(resolver.get_openapi_schema()))
            except (ImportError, AttributeError, FileNotFoundError) as e:  # pragma: no cover
                logger.warning(f"Failed to load resolver from {file_path}: {e}")

        self._cached_schema = self._merge_schemas()
        return self._cached_schema

    def get_openapi_json_schema(self) -> str:
        """
        Generate the merged OpenAPI schema as a JSON string.

        This is the recommended method for CI/CD pipelines and build-time
        schema generation, as the output can be directly written to a file
        or used for API Gateway imports.

        Returns
        -------
        str
            The merged OpenAPI schema as formatted JSON.

        Example
        -------
        >>> merge = OpenAPIMerge(title="API", version="1.0.0")
        >>> merge.discover(path="./functions", pattern="**/handler.py")
        >>> json_schema = merge.get_openapi_json_schema()
        >>> with open("openapi.json", "w") as f:
        ...     f.write(json_schema)
        """
        from aws_lambda_powertools.event_handler.openapi.compat import model_json
        from aws_lambda_powertools.event_handler.openapi.models import OpenAPI

        schema = self.get_openapi_schema()
        return model_json(OpenAPI(**schema), by_alias=True, exclude_none=True, indent=2)

    @property
    def discovered_files(self) -> list[Path]:
        """Get the list of discovered resolver files."""
        return self._discovered_files.copy()

    def _merge_schemas(self) -> dict[str, Any]:
        """Merge all schemas into a single OpenAPI schema."""
        cfg = self._config

        # Build base schema
        merged: dict[str, Any] = {
            "openapi": cfg.openapi_version,
            "info": {"title": cfg.title, "version": cfg.version},
            "servers": [_model_to_dict(s) for s in cfg.servers] if cfg.servers else [{"url": "/"}],
        }

        # Add optional info fields
        self._add_optional_info_fields(merged, cfg)

        # Merge paths and components
        merged_paths: dict[str, Any] = {}
        merged_components: dict[str, dict[str, Any]] = {}

        for schema in self._schemas:
            self._merge_paths(schema.get("paths", {}), merged_paths)
            self._merge_components(schema.get("components", {}), merged_components)

        # Add security schemes from config
        if cfg.security_schemes:
            merged_components.setdefault("securitySchemes", {}).update(cfg.security_schemes)

        if merged_paths:
            merged["paths"] = merged_paths
        if merged_components:
            merged["components"] = merged_components

        # Merge tags
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
        """Merge components from source into target.

        Note: Components with the same name are silently overwritten (last wins).
        This is intentional as component conflicts are typically user errors
        (e.g., two handlers defining different 'User' schemas).
        """
        for component_type, components in source.items():
            target.setdefault(component_type, {}).update(components)

    def _merge_tags(self) -> list[dict[str, Any]]:
        """Merge tags from config and schemas."""
        tags_map: dict[str, dict[str, Any]] = {}

        # Config tags first
        for tag in self._config.tags or []:
            if isinstance(tag, str):
                tags_map[tag] = {"name": tag}
            else:
                tag_dict = _model_to_dict(tag)
                tags_map[tag_dict["name"]] = tag_dict

        # Schema tags (don't override config)
        for schema in self._schemas:
            for tag in schema.get("tags", []):
                name = tag["name"] if isinstance(tag, dict) else tag
                if name not in tags_map:
                    tags_map[name] = tag if isinstance(tag, dict) else {"name": tag}  # pragma: no cover

        return list(tags_map.values())
