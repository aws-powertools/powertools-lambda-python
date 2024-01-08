---
title: Bedrock Agents
description: Core utility
---

Event handler for Amazon Bedrock Agents, including auto generation of OpenAPI schemas.

## Key features

* Same declarative syntax as the [other Powertools event handlers](api_gateway.md)
* Drastically reduce the boilerplate to build Agents for Amazon Bedrock
* Automatic generation of OpenAPI schemas from the API
* Built-in data validation for requests/responses

## Getting started

In order to build Bedrock Agents, you need:

* Create the Lambda function that defines the business logic for the action that your agent will carry out
* Create an OpenAPI schema with the API description, structure, and parameters for the action group.
* Ensure that Bedrock and your Lambda functions have the [necessary permissions](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-permissions.html).

AWS Lambda Powertools facilitates the process by providing support for the development of the Lambda function and the creation of the OpenAPI specification.

!!! info "This is not necessary if you're installing Powertools for AWS Lambda (Python) via [Lambda Layer/SAR](../../index.md#lambda-layer){target="_blank"}."

You need to add `pydantic` as a dependency in your preferred tool _e.g., requirements.txt, pyproject.toml_.

As of now, both Pydantic V1 and V2 are supported. For a future major version, we will only support Pydantic V2.

### Your first Agent

To create a Bedrock Agent, use the `BedrockAgentResolver` to annotate your actions. This is
similar to the way [all the other Powertools](api_gateway.md) resolvers work.

Be aware that it's important to include a description for each API endpoint. The description is essential because it provides Bedrock Agents with an understanding of the primary function of your API action.

=== "Lambda handler"

    ```python hl_lines="4 9 12 21"
    --8<-- "examples/event_handler_bedrock_agents/src/getting_started.py"
    ```

	1. `description` is a required field in order for Bedrock Agents to work.

=== "Input payload"

	```json hl_lines="7 9 16"
	--8<-- "examples/event_handler_bedrock_agents/src/getting_started.json"
	```

=== "Output payload"

	```json hl_lines="12-14"
	--8<-- "examples/event_handler_bedrock_agents/src/getting_started_output.json"
	```

The resolvers utilized by Bedrock Agents are also compatible with the full suite of Powertools utilities. This ensures seamless integration and functionality across the different tools provided by Powertools when working with Bedrock Agents.

### Generating OpenAPI schemas

To create a schema for your API, use the `get_openapi_json_schema` function provided by the Bedrock Agent resolver. This function will produce a JSON-serialized string that represents your schema. You have the option to either display this string output or save it to a file for future reference.

=== "Generating the OpenAPI schem"

    ```python hl_lines="24 25"
    --8<-- "examples/event_handler_bedrock_agents/src/generating_openapi_schema.py"
    ```

=== "OpenAPI schema"

    ```json hl_lines="13 16 24"
    --8<-- "examples/event_handler_bedrock_agents/src/generating_openapi_schema.json"
    ```

To obtain the OpenAPI schema, execute the Python script from the command line interface (CLI). Upon execution, the script will generate the schema, which will be output directly to the console.

### Creating your Agent in the AWS Console

To create a Bedrock Agent, you should refer to the [official documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-create.html) provided by AWS.

During the creation process, when the user interface (UI) prompts you for an OpenAPI specification, you should input the specification that was generated in the previous step. This is the spec that you obtained by running your Python script, which produced the OpenAPI schema as output.

### Enabling the Swagger UI

--8<-- "docs/core/event_handler/_swagger_ui.md"

```python hl_lines="10" title="enabling_swagger.py"
--8<-- "examples/event_handler_bedrock_agents/src/enabling_swagger.py"
```

1. `enable_swagger` creates a route to serve Swagger UI and allows quick customizations. <br><br> You can also include  middlewares to protect or enhance the overall experience.

## Advanced

### Additional metadata

To enrich the view that Bedrock Agents has of your Lambda functions, we use a combination of Pydantic Models and [OpenAPI](https://www.openapis.org/){target="_blank"} type annotations to add constraints to your API's parameters.

--8<-- "docs/core/event_handler/_openapi_customization_intro.md"

#### Customizing OpenAPI parameters

--8<-- "docs/core/event_handler/_openapi_customization_parameters.md"

#### Customizing API operations

--8<-- "docs/core/event_handler/_openapi_customization_operations.md"

To implement these customizations, include extra parameters when defining your routes:

```python hl_lines="14-23 25" title="customizing_api_operations.py"
--8<-- "examples/event_handler_bedrock_agents/src/customizing_api_operations.py"
```

#### Customizing Swagger UI

--8<-- "docs/core/event_handler/_openapi_customization_swagger.md"

Below is an example configuration for serving Swagger UI from a custom path or CDN, with assets like CSS and JavaScript loading from a chosen CDN base URL.

=== "customizing_swagger.py"

    ```python hl_lines="10"
    --8<-- "examples/event_handler_bedrock_agents/src/customizing_swagger.py"
    ```

=== "customizing_swagger_middlewares.py"

A Middleware can handle tasks such as adding security headers, user authentication, or other request processing for serving the Swagger UI.

   ```python hl_lines="7 13-18 21"
   --8<-- "examples/event_handler_bedrock_agents/src/customizing_swagger_middlewares.py"
   ```

#### Customizing OpenAPI metadata

--8<-- "docs/core/event_handler/_openapi_customization_metadata.md"

Include extra parameters when exporting your OpenAPI specification to apply these customizations:

=== "customizing_api_metadata.py"

    ```python hl_lines="25-31"
    --8<-- "examples/event_handler_bedrock_agents/src/customizing_api_metadata.py"
    ```

### Data validation

The Bedrock Agents Resolver allows for the clear definition of the expected format for incoming data and responses. By delegating data validation tasks to the Event Handler resolvers, you can significantly reduce the amount of repetitive code in your project.

For detailed guidance on implementing this feature, please consult the [REST API validation documentationi](api_gateway.md#data-validation). There, you'll find step-by-step instructions on how to apply data validation when using the resolver.

???+ note
	When using the Bedrock Agent resolver, there's no need to add the `enable_validation` parameter, as it's enabled by default.

## Testing your code

You can test your routes by passing a proxy event request with required params.

=== "assert_bedrock_agent_response.py"

	```python hl_lines="21-23"
	--8<-- "examples/event_handler_bedrock_agents/src/assert_bedrock_agent_response.py"
	```

=== "assert_bedrock_agent_response_module.py"

	```python
	--8<-- "examples/event_handler_bedrock_agents/src/assert_bedrock_agent_response_module.py"
	```
