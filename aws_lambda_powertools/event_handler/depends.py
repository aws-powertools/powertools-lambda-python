"""Lightweight dependency injection primitives — no pydantic import."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


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
    from typing_extensions import Annotated

    from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
    from aws_lambda_powertools.event_handler.depends import Depends

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
