---
title: Validation & OpenAPI
description: Core utility
---

Comprehensive data validation and OpenAPI generation based on introspection of Python types.

## Key Features

* Declarative validation of inputs and outputs
* Support for scalar types, dataclasses and Pydantic models
* Automatic generation of OpenAPI specifications from the API definition
* Embedded Swagger UI for interactive API documentation

## Getting started

To use validation and OpenAPI features with our core utility, you must first ensure that pydantic is installed as it is a prerequisite. This utility framework supports both pydantic version 1 and version 2. For detailed guidance on setting up the parser, visit the [Parser documentation](./../../../../utilities/parser/#getting-started).

This documentation specifically focuses on the utility's validation and OpenAPI capabilities. These features are built on top of the Event Handler, thereby streamlining the process of validating inputs and outputs and automatically generating OpenAPI specifications based on your API definitions.

### Basic usage

To enable the validation logic, you need to pass the `enable_validation` parameter to your REST API resolver. This changes the way your resolver gets called. We will inspect
your handler do termine the input and output parameters, and will validate / coerce the data before calling your handler.

To enable the validation mechanism within your REST API, you'll need to use the `enable_validation` parameter when defining your API resolver.
This modifies the invocation process of your resolver function. Powertools will analyze your handler to identify the input and output parameters.
Once these parameters are determined, we ensure that the data is validated and coerced accordingly before it ever reaches your handler.
This process is designed to enforce a layer of integrity, so that your functions operate on clean and verified inputs, leading to more reliable and maintainable code.

=== "getting_started.py"

    ```python hl_lines="10 13 15 19"
    --8<-- "examples/event_handler_validation/src/getting_started.py"
    ```

=== "event.json"

    ```json hl_lines="4"
    --8<-- "examples/event_handler_validation/src/getting_started.json"
    ```

=== "output.json"

    ```json hl_lines="2 8"
    --8<-- "examples/event_handler_validation/src/getting_started_output.json"
    ```

If the validation process encounters data that does not conform to the specified input schema, the system triggers a validation error. This results in an HTTP 442 Unprocessable Entity error, which indicates that the input was understood by the server but contained invalid fields.

Here's an example of what the error response might look like when the validation fails due to bad input:

=== "bad_input_event.json"

    ```json hl_lines="4"
    --8<-- "examples/event_handler_validation/src/getting_started_bad_input.json"
    ```

=== "output.json"

    ```json hl_lines="2 3"
    --8<-- "examples/event_handler_validation/src/getting_started_bad_input_output.json"
    ```

???+ note "Pydantic v1 vs v2"
	Pydantic version 1 and version 2 might describe these validation errors differently. Hence, you should consult the relevant version's documentation to understand the exact format and style of the error messages for the version you are using.

### Using Pydantic models

Pydantic models provide a powerful syntax for declaring complex data structures along with the rules to validate the incoming data. These models can be used directly as input parameters or return types, letting you take full advantage of Pydantic's breadth of features, including data coercion, default values, and advanced validation.

Let's take a look at how you can utilize Pydantic models:

=== "getting_started_pydantic.py"

    ```python hl_lines="9 12 20 24"
    --8<-- "examples/event_handler_validation/src/getting_started_pydantic.py"
    ```

=== "event.json"

    ```json hl_lines="4 5 15"
    --8<-- "examples/event_handler_validation/src/getting_started_pydantic.json"
    ```

=== "output.json"

    ```json hl_lines="2 3"
    --8<-- "examples/event_handler_validation/src/getting_started_pydantic_output.json"
    ```

### SwaggerUI

Swagger UI provides a web-based interface for visualizing and interacting with your API's resources. By enabling Swagger UI for your API, you create an interactive documentation page that can be used for testing and exploring your API endpoints in real-time.

WARNING: this will create a publicly accessible Swagger UI page. See Advanced for how to customize and protect your
Swagger UI

???+ warning "Publicly accessible by default"
	The Swagger UI page will be publicly accessible when enabled. If your API contains sensitive endpoints or you wish to restrict access to the documentation, it's crucial to consider adding authentication mechanisms or other protections.
	See the [Customize the Swagger UI](#customizing-the-swagger-ui) section of this documentation to learn details on customizing and securing your Swagger UI, ensuring it suits your specific requirements while providing the necessary protection for your API's interactive documentation.

```python hl_lines="9 10"
--8<-- "examples/event_handler_validation/src/swagger.py"
```

Here's an example of what it looks like by default:

![Swagger UI](../../media/swagger.png)

## Advanced

### Customizing parameters

Annotations are a useful way to enrich your API's parameters with metadata and validation constraints, thereby enhancing the functionality and documentation of your API. Python's [Annotated type, introduced in PEP 593](https://peps.python.org/pep-0593/), allows you to attach additional metadata to type hints, which can then be used by your validation library or documentation tools.

If you are working with parameters that are part of the URL path, query strings, or request bodies, certain specialized classes or decorators are often available to assist with defining these parameters more explicitly. This can include specifying default values, validation rules, and descriptions for better OpenAPI generation.

Here is an example demonstrating how you might customize your API parameters using annotations:

```python hl_lines="1 7 19 20"
--8<-- "examples/event_handler_validation/src/customizing_parameters.py"
```

???+ note
	Powertools doesn't have support for files, form data, and header parameters at the moment. If you're interested in this, please [open an issue](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=feature-request%2Ctriage&projects=&template=feature_request.yml&title=Feature+request%3A+TITLE).

Adding titles and descriptions to your parameters is beneficial because it clarifies the intended use and constraints of the API for end-users and developers alike.
When the API is rendered in OpenAPI documentation tools, these annotations will be converted into readable descriptions, providing a self-explanatory interface for interacting with your API.
This can significantly improve the developer experience and reduce the learning curve for new users of your API.

Here's a table of all possible customizations you can do:

| Field name            | Type          | Description                                                                                                                                 |
|-----------------------|---------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `alias`               | `str`         | Alternative name for a field, used when serializing and deserializing data                                                                  |
| `validation_alias`    | `str`         | Alternative name for a field during validation (but not serialization)                                                                      |
| `serialization_alias` | `str`         | Alternative name for a field during serialization (but not during validation)                                                               |
| `description`         | `str`         | Human-readable description                                                                                                                  |
| `gt`                  | `float`       | Greater than. If set, value must be greater than this. Only applicable to numbers                                                           |
| `ge`                  | `float`       | Greater than or equal. If set, value must be greater than or equal to this. Only applicable to numbers                                      |
| `lt`                  | `float`       | Less than. If set, value must be less than this. Only applicable to numbers                                                                 |
| `le`                  | `float`       | Less than or equal. If set, value must be less than or equal to this. Only applicable to numbers                                            |
| `min_length`          | `int`         | Minimum length for strings                                                                                                                  |
| `max_length`          | `int`         | Maximum length for strings                                                                                                                  |
| `pattern`             | `string`      | A regular expression that the string must match.                                                                                            |
| `strict`              | `bool`        | If `True`, strict validation is applied to the field. See [Strict Mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) for details |
| `multiple_of`         | `float`       | Value must be a multiple of this. Only applicable to numbers	                                                                               |
| `allow_inf_nan`       | `bool`        | Allow `inf`, `-inf`, `nan`. Only applicable to numbers	                                                                                     |
| `max_digits`          | `int`         | Maximum number of allow digits for strings                                                                                                  |
| `decimal_places`      | `int`         | Maximum number of decimal places allowed for numbers                                                                                        |
| `examples`            | `List\[Any\]` | List of examples of the field                                                                                                               |
| `deprecated`          | `bool`        | Marks the field as deprecated                                                                                                               |
| `include_in_schema`   | `bool`        | If `False` the field will not be part of the exported OpenAPI schema                                                                        |
| `json_schema_extra`   | `JsonDict`    | Any additional JSON schema data for the schema property                                                                                     |

### Body parameters

Handling JSON objects in the body of your API requests is simple with Pydantic models. We automate the parsing of the request bodies using the models you define,
ensuring that the data structures rescived are aligned with your API's expectations.

Here's how to define and parse body parameters using a Pydantic model:

=== "body_parsing.py"

    ```python hl_lines="12 19 20"
    --8<-- "examples/event_handler_validation/src/body_parsing.py"
    ```

=== "event.json"

    ```json hl_lines="21 22 33"
    --8<-- "examples/event_handler_validation/src/body_parsing.json"
    ```

=== "output.json"

    ```json hl_lines="3"
    --8<-- "examples/event_handler_validation/src/body_parsing_output.json"
    ```

When using the Body wrapper with embed, your JSON payload will need to be provided as a nested object under a key that matches the name of the parameter:

=== "body_parsing_embed.py"

    ```python hl_lines="1 7 21"
    --8<-- "examples/event_handler_validation/src/body_parsing_embed.py"
    ```

=== "event.json"

    ```json hl_lines="21 22 33"
    --8<-- "examples/event_handler_validation/src/body_parsing_embed.json"
    ```

=== "output.json"

    ```json hl_lines="3"
    --8<-- "examples/event_handler_validation/src/body_parsing_embed_output.json"
    ```

### Customizing API operations

Customizing your API endpoints involves adding specific metadata to your endpoint definitions, allowing you to provde descriptive documentation for API consumers and offer additional instructions to the underlying framework.
Below is a detailed explanation of various fields that you can customize:

| Field Name             | Type                        | Description                                                                                                                                                                                                                                                                                                      |
|------------------------|-----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `summary`              | `str`                       | A concise overview of the main functionality of the endpoint. This brief introduction is usually displayed in autogenerated API documentation and helps consumers quickly understand what the endpoint does.                                                                                                     |
| `description`          | `str`                       | A more detailed explanation of the endpoint, which can include information about the operation's behavior, including side effects, error states, and other operational guidelines.                                                                                                                               |
| `responses`            | `Dict[int, Dict[str, Any]]` | A dictionary that maps each HTTP status code to a Response Object as defined by the [OpenAPI Specification](https://swagger.io/specification/#response-object). This allows you to describe expected responses, including default or error messages, and their corresponding schemas for different status codes. |
| `response_description` | `str`                       | Provides the default textual description of the response sent by the endpoint when the operation is successful. It is intended to give a human-readable understanding of the result.                                                                                                                             |
| `tags`                 | `List[str]`                 | Tags are a way to categorize and group endpoints within the API documentation. They can help organize the operations by resources or other heuristic.                                                                                                                                                            |
| `operation_id`         | `str`                       | A unique identifier for the operation, which can be used for referencing this operation in documentation or code. This ID must be unique across all operations described in the API.                                                                                                                             |
| `include_in_schema`    | `bool`                      | A boolean value that determines whether or not this operation should be included in the OpenAPI schema. Setting it to `False` can hide the endpoint from generated documentation and schema exports, which might be useful for private or experimental endpoints.                                                |

To apply these customizations, you add additional parameters when declaring your routes:

=== "Customizing API operations metadata"

    ```python hl_lines="11-20"
    --8<-- "examples/event_handler_validation/src/customizing_operations.py"
    ```

### Generating OpenAPI specifications

OpenAPI specifications are integral to understanding and interacting with modern web APIs. They describe the entire API, including routes, parameters, responses, and more. This specification can be machine-generated from your codebase, ensuring it remains up-to-date with your API's implementation.

With Powertools, these specifications can be outputted as a Pydantic object or as a raw JSON schema string:

=== "OpenAPI specification as a Pydantic object"

    ```python hl_lines="32"
    --8<-- "examples/event_handler_validation/src/generate_openapi_spec.py"
    ```

=== "OpenAPI specification as a JSON schema string"

    ```python hl_lines="32"
    --8<-- "examples/event_handler_validation/src/generate_openapi_json_spec.py"
    ```

=== "OpenAPI JSON schema"

    ```json
    --8<-- "examples/event_handler_validation/src/generate_openapi_json_spec.json"
    ```

???+ note "Why opt for the Pydantic object?"
	Having the OpenAPI specification as a Pydantic object provides several advantages:

	1. **Post-Processing:** You may wish to programmatically alter or enrich the OpenAPI specification after it's generated but before you serve it or pass it on. For instance, you could add examples, merge multiple specifications, or adjust descriptions dynamically.
	2. **Internal Use:** Maybe your goal is not to expose the specification externally but to utilize it within your system for validation, mocking, or other quality assurance techniques.
	3. **Dynamic Behavior:** If you need to control the representation of the schema based on conditions not expressible statically in the code (e.g., user permissions, environment variables), a Pydantic object could be manipulated prior to serialization.
	4. **Fragment Reuse:** If your setup involves microservices or a plugin architecture, you might need to generate partial schemas and combine them into a larger API gateway schema.
	5. **Testing and Automation:** For testing purposes, it’s often useful to have the schema in a manipulatable form to validate that certain changes are present or to automate API tests.

#### Customizing OpenAPI metadata

Customizing the OpenAPI metadata allows you to provide detailed, top-level information about your API. Here's how you can define and customize this metadata:

| Field Name         | Type           | Description                                                                                                                                                                         |
|--------------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `title`            | `str`          | The title for your API. It should be a concise, specific name that can be used to identify the API in documentation or listings.                                                    |
| `version`          | `str`          | The version of the API you are documenting. This could reflect the release iteration of the API and helps clients understand the evolution of the API.                              |
| `openapi_version`  | `str`          | Specifies the version of the OpenAPI Specification on which your API is based. For most contemporary APIs, the default value would be `3.0.0` or higher.                            |
| `summary`          | `str`          | A short and informative summary that can provide an overview of what the API does. This can be the same as or different from the title but should add context or information.       |
| `description`      | `str`          | A verbose description that can include Markdown formatting, providing a full explanation of the API's purpose, functionalities, and general usage instructions.                     |
| `tags`             | `List[str]`    | A collection of tags that categorize endpoints for better organization and navigation within the documentation. This can group endpoints by their functionality or other criteria.  |
| `servers`          | `List[Server]` | An array of Server objects, which specify the URL to the server and a description for its environment (production, staging, development, etc.), providing connectivity information. |
| `terms_of_service` | `str`          | A URL that points to the terms of service for your API. This could provide legal information and user responsibilities related to the usage of the API.                             |
| `contact`          | `Contact`      | A Contact object containing contact details of the organization or individuals maintaining the API. This may include fields such as name, URL, and email.                           |
| `license_info`     | `License`      | A License object providing the license details for the API, typically including the name of the license and the URL to the full license text.                                       |

To apply these customizations, you add additional parameters when exporting your OpenAPI specification:

=== "Customizing OpenAPI metadata"

    ```python hl_lines="25-31"
    --8<-- "examples/event_handler_validation/src/customize_api_metadata.py"
    ```

### Customizing the Swagger UI

By default, the Swagger UI may be served under the `/swagger` path, but customization options are often provided to allow you to serve the documentation from a different path, as well as to define where the necessary Swagger UI assets are loaded from.

Here is an example of how you could configure the loading of the Swagger UI from a custom path or CDN. Additionally, the Swagger UI assets such as the CSS and JavaScript bundles are directed to load from a specified CDN base URL.

=== "Customizing Swagger path and CDN"

    ```python hl_lines="10"
    --8<-- "examples/event_handler_validation/src/swagger_customize.py"
    ```

???+note "Customizing the Swagger metadata"
	The `enable_swagger` method accepts the same metadata as described at [Customizing OpenAPI metadata](#customizing-openapi-metadata).

=== "Using middlewares with the Swagger UI"

To complement these customizations, it's possible to introduce middleware on the Swagger UI endpoiunt.
Middleware can be used for tasks like adding security headers, user authentication, or other processing that needs to occur on requests serving the Swagger UI.

   ```python hl_lines="7 13-18 21"
   --8<-- "examples/event_handler_validation/src/swagger_middlewares.py"
   ```

## Testing your code

For comprehensive guidance on how to test your code effectively, please refer to the documentation specific to the [REST API documentation](../api_gateway/#testing-your-code).
The referenced documentation will provide you with best practices, testing techniques, and examples on how to write tests for your API code.
