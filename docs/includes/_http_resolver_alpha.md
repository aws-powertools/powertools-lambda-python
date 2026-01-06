<!-- markdownlint-disable MD041 MD043 -->
#### Http Resolver (Alpha)

???+ warning "Alpha Feature"
    `HttpResolverAlpha` is an alpha feature intended for local development and testing only.
    The API may change in future releases. **Do not use in production environments.**

When developing locally, you can use `HttpResolverAlpha` to run your API with any ASGI server like [uvicorn](https://www.uvicorn.org/){target="_blank"}. It implements the [ASGI specification](https://asgi.readthedocs.io/){target="_blank"}, is lightweight with no external dependencies, and the same code works on any compute platform, including Lambda.

If your Lambda is behind [Lambda Web Adapter](https://github.com/awslabs/aws-lambda-web-adapter){target="_blank"} or any other HTTP proxy that speaks the HTTP protocol, it works seamlessly.

All existing resolver features work out of the box: routing, middleware, validation, OpenAPI/Swagger, CORS, exception handling, and more.

**Install uvicorn**:

```bash
pip install uvicorn
```

=== "Basic Usage"

    ```python hl_lines="1 3"
    --8<-- "examples/event_handler_rest/src/http_resolver_basic.py"
    ```

    Run locally: `uvicorn app:app --reload`

=== "With Validation & Swagger"

    ```python hl_lines="13-16"
    --8<-- "examples/event_handler_rest/src/http_resolver_validation_swagger.py"
    ```

    Access Swagger UI at `http://localhost:8000/swagger`

=== "Exception Handling"

    ```python hl_lines="12-18 21-27"
    --8<-- "examples/event_handler_rest/src/http_resolver_exception_handling.py"
    ```
