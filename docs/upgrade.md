---
title: Upgrade guide
description: asdfasdf
---

<!-- markdownlint-disable MD043 -->

## Migrate to v2 from v1

The transition from Powertools for Python v1 to v2 is as painless as possible, as we strove for minimal breaking changes.
The API for event handler's Response has minor changes, but we kept the breaking changes to a bare minimum. We've also added some new features to some components.

???+ important
    Powertools for Python v2 drops suport for Python 3.6, following the Python 3.6 End-Of-Life (EOL) reached on December 23, 2021.

### Initial Steps

Before starting, it is highly suggested to make a copy of your current working project or create a new branch with git.

1. **Upgrade** Python to at least v3.7

2. **Ensure** you have the latest `aws-lambda-powertools`

    ```bash
    pip install aws-lambda-powertools -U
    ```

3. **Check** the following sections to see if any of your code is affected

## Event Handler Response (headers and cookies)

The `Response` class of the event handler utility was changed slightly:

1. The `headers` parameter now has a type signature of `Dict[str, List[str]]`
2. A new `cookies` parameter was added (type `List[str]`)

```python hl_lines="6 12 13"
@app.get("/todos")
def get_todos():
    # Before
    return Response(
        # ...
        headers={"Content-Type": "text/plain"}
    )

    # After
    return Response(
        # ...
        headers={"Content-Type": ["text/plain"]},
        cookies=["CookieName=CookieValue"]
    )
```

In the same way, it can be more convenient to just append headers to the response object:

```python hl_lines="4 5"
@app.get("/todos")
def get_todos():
    response = Response(...)
    response.headers["Content-Type"].append("text/plain")
    response.cookies.append("CookieName=CookieValue")
```
