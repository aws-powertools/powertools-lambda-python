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

This documentation specifically focuses on the utility's validation and OpenAPI capabilities. These features are built on top of the Event Handler utility, thereby streamlining the process of validating inputs and outputs and automatically generating OpenAPI specifications based on your API definitions.

### Basic usage

Enable the REST API's validation by setting the `enable_validation` parameter in your API resolver. This changes how your resolver is called.
Powertools examines your handler to pinpoint input and output parameters, then validates and coerces the data before it reaches your handler.

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

When data fails to match the input schema during validation, a validation error occurs, leading to an HTTP 422 Unprocessable Entity error, signaling that the server understood the input but found invalid fields.

Below is a sample error response for failed validation due to incorrect input:

=== "bad_input_event.json"

    ```json hl_lines="4"
    --8<-- "examples/event_handler_validation/src/getting_started_bad_input.json"
    ```

=== "output.json"

    ```json hl_lines="2 3"
    --8<-- "examples/event_handler_validation/src/getting_started_bad_input_output.json"
    ```

???+ note "Pydantic v1 vs v2"
	Pydantic versions 1 and 2 may report validation errors differently. Refer to the documentation for your specific version to grasp the precise format and style of the error messages.

### Using Pydantic models

Pydantic models allow you to define complex data structures and validation rules. Use these models as input parameters or return types to leverage Pydantic's features like data coercion, default values, and advanced validation.

Here's how to use Pydantic models:

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

Swagger UI offers a web interface for visualizing and interacting with your API's resources. Enable Swagger UI to generate an interactive documentation page for testing and exploring your API endpoints in real time.

???+ warning "Publicly accessible by default"
	Enabling Swagger UI makes it public. To protect sensitive API endpoints or restrict documentation access, consider implementing authentication or other security measures.
	See the [Customize the Swagger UI](#customizing-the-swagger-ui) section for instructions on customizing and securing your Swagger UI to meet your needs and safeguard your interactive API documentation.

```python hl_lines="9 10"
--8<-- "examples/event_handler_validation/src/swagger.py"
```

Here's an example of what it looks like by default:

![Swagger UI](../../media/swagger.png)

## Advanced

### Customizing parameters

Use annotations to add metadata and validation constraints to your API's parameters, improving functionality and documentation. Python's [Annotated type from PEP 593](https://peps.python.org/pep-0593/) lets you append metadata to type hints for use by validation libraries or documentation tools.

For URL path, query string, or request body parameters, use specialized classes or decorators to define parameters with defaults, validation rules, and descriptions for enhanced OpenAPI output.

Below is an example of customizing API parameters with annotations:

```python hl_lines="1 7 19 20"
--8<-- "examples/event_handler_validation/src/customizing_parameters.py"
```

???+ note
	Powertools doesn't have support for files, form data, and header parameters at the moment. If you're interested in this, please [open an issue](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=feature-request%2Ctriage&projects=&template=feature_request.yml&title=Feature+request%3A+TITLE).

Titles and descriptions clarify parameter use and constraints for both end-users and developers. In OpenAPI documentation tools, these annotations become readable descriptions, offering a self-explanatory API interface. This enhances the developer experience and eases the learning curve for new API users.

Below is a table detailing all possible parameter customizations:

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

With Pydantic models, managing JSON objects in API request bodies is straightforward. The models you define automatically parse request bodies, confirming that received data structures match your API's specifications.

To define and parse body parameters with a Pydantic model, follow this example:

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

When you use the Body wrapper with the `embed` option, nest your JSON payload under a key that corresponds to the parameter name.

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

Customize your API endpoints by adding metadata to endpoint definitions. This provides descriptive documentation for API consumers and gives extra instructions to the framework.

Here's a breakdown of various customizable fields:

| Field Name             | Type                        | Description                                                                                                                                                                                                                                                                                                      |
|------------------------|-----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `summary`              | `str`                       | A concise overview of the main functionality of the endpoint. This brief introduction is usually displayed in autogenerated API documentation and helps consumers quickly understand what the endpoint does.                                                                                                     |
| `description`          | `str`                       | A more detailed explanation of the endpoint, which can include information about the operation's behavior, including side effects, error states, and other operational guidelines.                                                                                                                               |
| `responses`            | `Dict[int, Dict[str, Any]]` | A dictionary that maps each HTTP status code to a Response Object as defined by the [OpenAPI Specification](https://swagger.io/specification/#response-object). This allows you to describe expected responses, including default or error messages, and their corresponding schemas for different status codes. |
| `response_description` | `str`                       | Provides the default textual description of the response sent by the endpoint when the operation is successful. It is intended to give a human-readable understanding of the result.                                                                                                                             |
| `tags`                 | `List[str]`                 | Tags are a way to categorize and group endpoints within the API documentation. They can help organize the operations by resources or other heuristic.                                                                                                                                                            |
| `operation_id`         | `str`                       | A unique identifier for the operation, which can be used for referencing this operation in documentation or code. This ID must be unique across all operations described in the API.                                                                                                                             |
| `include_in_schema`    | `bool`                      | A boolean value that determines whether or not this operation should be included in the OpenAPI schema. Setting it to `False` can hide the endpoint from generated documentation and schema exports, which might be useful for private or experimental endpoints.                                                |

To implement these customizations, include extra parameters when defining your routes:

=== "Customizing API operations metadata"

    ```python hl_lines="11-20"
    --8<-- "examples/event_handler_validation/src/customizing_operations.py"
    ```

### Generating OpenAPI specifications

OpenAPI specifications detail web APIs, covering routes, parameters, responses, etc. They can be auto-generated from your code, keeping them synchronized with your API's actual implementation.

Powertools allows exporting these specifications as a Pydantic object or a JSON schema string:

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
	The OpenAPI specification as a Pydantic object offers benefits:

	1. **Post-Processing:** Alter or enrich the specification programmatically after generation, such as adding examples, merging specs, or updating descriptions.
	2. **Internal Use:** Use the specification within your system for validation, mocking, or other quality assurance methods, rather than exposing it externally.
	3. **Dynamic Behavior:** Manipulate the schema representation before serialization to reflect conditions like user permissions or environment variables.
	4. **Fragment Reuse:** In microservices or plugin architectures, generate partial schemas to assemble into a comprehensive API gateway schema.
	5. **Testing and Automation:** For testing, a manipulatable schema form is useful to confirm changes or automate API tests.

#### Customizing OpenAPI metadata

Defining and customizing OpenAPI metadata gives detailed, top-level information about your API. Here's the method to set and tailor this metadata:

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

Include extra parameters when exporting your OpenAPI specification to apply these customizations:

=== "Customizing OpenAPI metadata"

    ```python hl_lines="25-31"
    --8<-- "examples/event_handler_validation/src/customize_api_metadata.py"
    ```

### Customizing the Swagger UI

The Swagger UI appears by default at the `/swagger` path, but you can customize this to serve the documentation from another path and specify the source for Swagger UI assets.

Below is an example configuration for serving Swagger UI from a custom path or CDN, with assets like CSS and JavaScript loading from a chosen CDN base URL.

=== "Customizing Swagger path and CDN"

    ```python hl_lines="10"
    --8<-- "examples/event_handler_validation/src/swagger_customize.py"
    ```

???+note "Customizing the Swagger metadata"
	The `enable_swagger` method accepts the same metadata as described at [Customizing OpenAPI metadata](#customizing-openapi-metadata).

=== "Using middlewares with the Swagger UI"

You can enhance these customizations by adding middleware to the Swagger UI endpoint. Middleware can handle tasks such as adding security headers, user authentication, or other request processing for serving the Swagger UI.

   ```python hl_lines="7 13-18 21"
   --8<-- "examples/event_handler_validation/src/swagger_middlewares.py"
   ```

## Testing your code

For detailed instructions on testing your code, consult the [REST API documentation](../api_gateway/#testing-your-code).
This guide offers best practices, testing methods, and examples for writing API tests.
