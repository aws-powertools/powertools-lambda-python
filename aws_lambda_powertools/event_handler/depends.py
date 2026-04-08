"""Lightweight dependency injection primitives — no pydantic import."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin, get_type_hints

if TYPE_CHECKING:
    from collections.abc import Callable

    from aws_lambda_powertools.event_handler.openapi.params import Dependant
    from aws_lambda_powertools.event_handler.request import Request


class Depends:
    """
    Declares a dependency for a route handler parameter.

    Dependencies are resolved automatically before the handler is called. The return value
    of the dependency callable is injected as the parameter value.

    Parameters
    ----------
    dependency: Callable[..., Any]
        A callable whose return value will be injected into the handler parameter.
        The callable can itself declare ``Depends()`` parameters to form a dependency tree.
    use_cache: bool
        If ``True`` (default), the dependency result is cached per invocation so that
        the same dependency used multiple times is only called once.

    Examples
    --------

    ```python
    from typing import Annotated

    from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Depends

    app = APIGatewayHttpResolver()

    def get_tenant() -> str:
        return "default-tenant"

    @app.get("/orders")
    def list_orders(tenant_id: Annotated[str, Depends(get_tenant)]):
        return {"tenant": tenant_id}
    ```
    """

    def __init__(self, dependency: Callable[..., Any], *, use_cache: bool = True) -> None:
        self.dependency = dependency
        self.use_cache = use_cache


class DependencyTree:
    """Lightweight dependency tree — no pydantic required.

    This mirrors the shape that ``solve_dependencies`` expects (a ``.dependencies``
    attribute containing ``DependencyParam`` objects), but can be built without
    importing pydantic.
    """

    def __init__(self, *, dependencies: list[DependencyParam] | None = None) -> None:
        self.dependencies: list[DependencyParam] = dependencies or []


class DependencyParam:
    """Holds a dependency's parameter name and its resolved dependency sub-tree."""

    def __init__(self, *, param_name: str, depends: Depends, dependant: Dependant | DependencyTree) -> None:
        self.param_name = param_name
        self.depends = depends
        self.dependant = dependant


def _get_depends_from_annotation(annotation: Any) -> Depends | None:
    """Extract a Depends instance from an Annotated[Type, Depends(...)] annotation."""
    if get_origin(annotation) is Annotated:
        for arg in get_args(annotation)[1:]:
            if isinstance(arg, Depends):
                return arg
    return None


def _has_depends(func: Callable[..., Any]) -> bool:
    """Check if a callable has any Depends() parameters, without importing pydantic."""
    signature = inspect.signature(func)
    globalns = getattr(func, "__globals__", {})

    for param in signature.parameters.values():
        annotation = param.annotation
        if isinstance(annotation, str):  # pragma: no cover - from __future__ annotations
            try:
                annotation = eval(annotation, globalns)  # noqa: S307
            except Exception:
                continue
        if _get_depends_from_annotation(annotation) is not None:
            return True
    return False


def build_dependency_tree(func: Callable[..., Any]) -> DependencyTree:
    """Build a lightweight dependency tree from a callable's signature.

    This inspects the function parameters for ``Annotated[Type, Depends(...)]``
    annotations and recursively builds the tree — all without importing pydantic.
    """
    signature = inspect.signature(func)
    globalns = getattr(func, "__globals__", {})
    dependencies: list[DependencyParam] = []

    for param_name, param in signature.parameters.items():
        annotation = param.annotation
        if isinstance(annotation, str):  # pragma: no cover - from __future__ annotations
            try:
                annotation = eval(annotation, globalns)  # noqa: S307
            except Exception:
                continue

        depends_instance = _get_depends_from_annotation(annotation)
        if depends_instance is not None:
            sub_tree = build_dependency_tree(depends_instance.dependency)
            dependencies.append(
                DependencyParam(
                    param_name=param_name,
                    depends=depends_instance,
                    dependant=sub_tree,
                ),
            )

    return DependencyTree(dependencies=dependencies)


def solve_dependencies(
    *,
    dependant: Dependant | DependencyTree,
    request: Request | None = None,
    dependency_overrides: dict[Callable[..., Any], Callable[..., Any]] | None = None,
    dependency_cache: dict[Callable[..., Any], Any] | None = None,
) -> dict[str, Any]:
    """
    Recursively resolve all ``Depends()`` parameters for a given dependant.

    Parameters
    ----------
    dependant: Dependant
        The dependant model containing dependency declarations
    request: Request, optional
        The current request object, injected into dependencies that declare a Request parameter
    dependency_overrides: dict, optional
        Mapping of original dependency callable to override callable (for testing)
    dependency_cache: dict, optional
        Per-invocation cache of resolved dependency values

    Returns
    -------
    dict[str, Any]
        Mapping of parameter name to resolved dependency value
    """
    from aws_lambda_powertools.event_handler.request import Request as RequestClass

    if dependency_cache is None:
        dependency_cache = {}

    values: dict[str, Any] = {}

    for dep in dependant.dependencies:
        use_fn = dep.depends.dependency

        # Apply overrides (for testing)
        if dependency_overrides and use_fn in dependency_overrides:
            use_fn = dependency_overrides[use_fn]

        # Check cache
        if dep.depends.use_cache and use_fn in dependency_cache:
            values[dep.param_name] = dependency_cache[use_fn]
            continue

        # Recursively resolve sub-dependencies
        sub_values = solve_dependencies(
            dependant=dep.dependant,
            request=request,
            dependency_overrides=dependency_overrides,
            dependency_cache=dependency_cache,
        )

        # Inject Request if the dependency declares it
        if request is not None:
            try:
                hints = get_type_hints(use_fn)
            except Exception:  # pragma: no cover - defensive for broken annotations
                hints = {}
            for param_name, annotation in hints.items():
                if annotation is RequestClass:
                    sub_values[param_name] = request

        solved = use_fn(**sub_values)

        # Cache result
        if dep.depends.use_cache:
            dependency_cache[use_fn] = solved

        values[dep.param_name] = solved

    return values
