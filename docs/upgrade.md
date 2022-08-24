---
title: Upgrade guide
description: Guide to update between major Powertools versions
---

<!-- markdownlint-disable MD043 -->

## Migrate to v2 from v1

The transition from Powertools for Python v1 to v2 is as painless as possible, as we aimed for minimal breaking changes.
Changes at a glance:

* The API for **event handler's `Response`** has minor changes to support multi value headers and cookies.

???+ important
    Powertools for Python v2 drops suport for Python 3.6, following the Python 3.6 End-Of-Life (EOL) reached on December 23, 2021.

### Initial Steps

Before you start, we suggest making a copy of your current working project or create a new branch with git.

1. **Upgrade** Python to at least v3.7

2. **Ensure** you have the latest `aws-lambda-powertools`

    ```bash
    pip install aws-lambda-powertools -U
    ```

3. **Review** the following sections to confirm whether they affect your code

## Event Handler Response (headers and cookies)

The `Response` class of the event handler utility changed slightly:

1. The `headers` parameter now expects a list of values per header (type `Dict[str, List[str]]`)
2. We introduced a new `cookies` parameter (type `List[str]`)

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

