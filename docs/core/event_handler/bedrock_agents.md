---
title: Agents for Amazon Bedrock
description: Core utility
---

Author [Agents for Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html#agents-how){target="_blank"} using event handlers and auto generation of OpenAPI schemas.

<center>
```mermaid
--8<-- "docs/core/event_handler/bedrock_agents.mermaid"
```
</center>

## Key features

* Similar experience when authoring [REST](api_gateway.md){target="_blank"} and [GraphQL APIs](appsync.md){target="_blank"}
* Minimal boilerplate to build Agents for Amazon Bedrock
* Automatic generation of [OpenAPI schemas](https://www.openapis.org/){target="_blank"} from your business logic code
* Built-in data validation for requests and responses

## Terminology

**Data validation** automatically validates the user input and the response of your AWS Lambda function against a set of constraints defined by you.

**Event handler** is a Powertools for AWS feature that processes an event, runs data parsing and validation, routes the request to a specific function, and returns a response to the caller in the proper format.

**[OpenAPI schema](https://www.openapis.org/){target="_blank"}** is an industry standard JSON-serialized string that represents the structure and parameters of your API.

**Action group** is a collection of two resources where you define the actions that the agent should carry out: an OpenAPI schema to define the APIs that the agent can invoke to carry out its tasks, and a Lambda function to execute those actions.

**Large Language Models (LLM)** are very large deep learning models that are pre-trained on vast amounts of data, capable of extracting meanings from a sequence of text and understanding the relationship between words and phrases on it.

**Agent for Amazon Bedrock** is an AWS service to build and deploy conversational agents that can interact with your customers using Large Language Models (LLM) and AWS Lambda functions.

## Getting started

???+ tip "All examples shared in this documentation are available within the [project repository](https://github.com/aws-powertools/powertools-lambda-python/tree/develop/examples)"

### Install

!!! info "This is unnecessary if you're installing Powertools for AWS Lambda (Python) via [Lambda Layer/SAR](../../index.md#lambda-layer){target="_blank"}."

You need to add `pydantic` as a dependency in your preferred tool _e.g., requirements.txt, pyproject.toml_. At this time, we support both Pydantic V1 and V2. For a future major version, we will only support Pydantic V2.

### Required resources

To build Agents for Amazon Bedrock, you will need:

| Requirement                                                                                                           | Description                                                                    | SAM Supported | CDK Supported |
|-----------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|:-------------:|:-------------:|
| [Lambda Function](#your-first-agent)                                                                                  | Defines your business logic for the action group                               |       ✅       |       ✅       |
| [OpenAPI Schema](#generating-openapi-schemas)                                                                         | API description, structure, and action group parameters                        |       ❌       |       ✅       |
| Bedrock [Service Role](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-permissions.html){target="_blank"} | Allows Amazon Bedrock to invoke foundation models                              |       ✅       |       ✅       |
| Agent for Bedrock                                                                                                     | The service that will combine all the above to create the conversational agent |       ❌       |       ✅       |

=== "Using AWS Serverless Application Model (SAM)"
	Using [AWS SAM](https://aws.amazon.com/serverless/sam/){target="_blank"} you can create your Lambda function and the necessary permissions. However, you still have to create your Agent for Amazon Bedrock [using the AWS console](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-create.html){target="_blank"}.

	```yaml hl_lines="18 26 34 61"
	--8<-- "examples/event_handler_bedrock_agents/sam/template.yaml"
	```

	1. Amazon Bedrock needs permissions to invoke this Lambda function
	2. Check the [supported foundational models](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-supported.html){target="_blank"}
	3. You need the role ARN when creating the Agent for Amazon Bedrock

=== "Using AWS Cloud Developer Kit (CDK)"
	This example uses the [Generative AI CDK constructs](https://awslabs.github.io/generative-ai-cdk-constructs/src/cdk-lib/bedrock/#agents){target="_blank"} to create your Agent with [AWS CDK](https://aws.amazon.com/cdk/){target="_blank"}.
	These constructs abstract the underlying permission setup and code bundling of your Lambda function.

	```python
    --8<-- "examples/event_handler_bedrock_agents/cdk/bedrock_agent_stack.py"
	```

	1. The path to your Lambda function handler
	2. The path to the OpenAPI schema describing your API

### Your first Agent

To create an Agent for Amazon Bedrock, use the `BedrockAgentResolver` to annotate your actions.
This is similar to the way [all the other Event Handler](api_gateway.md) resolvers work.

It's required to include a `description` for each API endpoint and input parameter. This will improve the understanding Amazon Bedrock has of your actions.

=== "Lambda handler"

	The resolvers used by Agents for Amazon Bedrock are compatible with all Powertools for AWS Lambda [features](../../index.md#features){target="blank"}.
	For reference, we use [Logger](../logger.md) and [Tracer](../tracer.md) in this example.

    ```python hl_lines="4 9 12 21"
    --8<-- "examples/event_handler_bedrock_agents/src/getting_started.py"
    ```

	1. `description` is a **required** field that should contain a human readable description of your action
	2. We take care of **parsing**, **validating**, **routing** and **responding** to the request.

=== "OpenAPI schema"

	Powertools for AWS Lambda [generates this automatically](#generating-openapi-schemas) from the Lambda handler.

	```json
	--8<-- "examples/event_handler_bedrock_agents/src/getting_started_schema.json"
	```

=== "Input payload"

	```json hl_lines="4 6 13"
	--8<-- "examples/event_handler_bedrock_agents/src/getting_started.json"
	```

=== "Output payload"

	```json hl_lines="10"
	--8<-- "examples/event_handler_bedrock_agents/src/getting_started_output.json"
	```

### Validating input and output

You can define the expected format for incoming data and responses by using type annotations.
Define constraints using standard Python types, [dataclasses](https://docs.python.org/3/library/dataclasses.html) or [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/).
Pydantic is a popular library for data validation using Python type annotations.

=== "Lambda handler"
	This example uses [Pydantic's EmailStr](https://docs.pydantic.dev/2.0/usage/types/string_types/#emailstr){target="_blank"} to validate the email address passed to the `schedule_meeting` function.
    The function then returns a boolean indicating if the meeting was successfully scheduled.

	```python hl_lines="1 2 16-18"
	--8<-- "examples/event_handler_bedrock_agents/src/getting_started_with_validation.py"
	```

	1. No need to add the `enable_validation` parameter, as it's enabled by default.
	2. Describe each input using human-readable descriptions
	3. Add the typing annotations to your parameters and return types, and let the event handler take care of the rest

=== "OpenAPI schema"

	```json
	--8<-- "examples/event_handler_bedrock_agents/src/getting_started_with_validation_schema.json"
	```

=== "Input payload"

	```json hl_lines="6-13 20"
	--8<-- "examples/event_handler_bedrock_agents/src/getting_started_with_validation.json"
	```

=== "Output payload"

	```json hl_lines="10"
	--8<-- "examples/event_handler_bedrock_agents/src/getting_started_with_validation_output.json"
	```

If the request validation fails, your event handler will not be called, and an error message is returned to Bedrock.
Similarly, if the response fails validation, your handler will abort the response.

???+ info "What does this mean for my Agent?"
	The event handler will always return a response according to the OpenAPI schema.
	A validation failure always results in a [422 response](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/422).
	However, how Amazon Bedrock interprets that failure is non-deterministic, since it depends on the characteristics of the LLM being used.

<center>
```mermaid
--8<-- "docs/core/event_handler/bedrock_agents_validation_sequence_diagram.mermaid"
```
</center>

### Generating OpenAPI schemas

Use the `get_openapi_json_schema` function provided by the resolver.
This function will produce a JSON-serialized string that represents your OpenAPI schema.
You can print this string or save it to a file. You'll use the file later when creating the Agent.

You'll need to regenerate the OpenAPI schema and update your Agent everytime your API changes.

=== "app.py"

    ```python hl_lines="24 25"
    --8<-- "examples/event_handler_bedrock_agents/src/generating_openapi_schema.py"
    ```

	1. This ensures that it's only executed when running the file directly, and not when running on the Lambda runtime.
    2. You can use [additional options](#customizing-openapi-metadata) to customize the OpenAPI schema.

=== "OpenAPI schema"

    ```json hl_lines="13 16 24"
    --8<-- "examples/event_handler_bedrock_agents/src/generating_openapi_schema.json"
    ```

To get the OpenAPI schema, run the Python script from your terminal.
The script will generate the schema directly to standard output, which you can redirect to a file.

```sh
python3 app.py > schema.json
```

### Crafting effective OpenAPI schemas

Working with Agents for Amazon Bedrock will introduce [non-deterministic behaviour to your system](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-how.html#agents-rt){target="_blank"}.
The OpenAPI schema provides context and semantics to the Agent that will support the decision process for invoking our Lambda function. Sparse or ambiguous schema can result in unexpected outcomes.

We recommend enriching your OpenAPI schema with as many details as possible to help the Agent understand your functions, and make correct invocations. To achieve that, keep the following suggestions in mind:

* Always describe your function behaviour using the `description` field in your annotations
* When refactoring, update your description field to match the function outcomes
* Use distinct `description` for each function to have clear separation of semantics

### Video walkthrough

To create an Agent for Amazon Bedrock, refer to the [official documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-create.html) provided by AWS.

The following video demonstrates the end-to-end process:

<center>
<iframe width="720" height="405" src="https://www.youtube-nocookie.com/embed/NWoC5FTSt7s?si=AG2qpLJbxCkyiLma&amp;controls=1" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
</center>

During the creation process, you should use the schema generated in the previous step when prompted for an OpenAPI specification.

## Advanced

### Accessing custom request fields

The event sent by Agents for Amazon Bedrock into your Lambda function contains a number of event fields that might be interesting. The event handler exposes them in the `app.current_event` field:

=== "Accessing request fields"

	```python hl_lines="15-17"
	--8<-- "examples/event_handler_bedrock_agents/src/accessing_request_fields.py"
	```

The input event fields are:

| Name                      | Type                         | Description                                                                                                                                                                                                      |
|---------------------------|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| message_version           | `str`                        | The version of the message that identifies the format of the event data going into the Lambda function and the expected format of the response from a Lambda function. Amazon Bedrock only supports version 1.0. |
| agent                     | `BedrockAgentInfo`           | Contains information about the name, ID, alias, and version of the agent that the action group belongs to.                                                                                                       |
| input_text                | `str`                        | The user input for the conversation turn.                                                                                                                                                                        |
| session_id                | `str`                        | The unique identifier of the agent session.                                                                                                                                                                      |
| action_group              | `str`                        | The name of the action group.                                                                                                                                                                                    |
| api_path                  | `str`                        | The path to the API operation, as defined in the OpenAPI schema.                                                                                                                                                 |
| http_method               | `str`                        | The method of the API operation, as defined in the OpenAPI schema.                                                                                                                                               |
| parameters                | `List[BedrockAgentProperty]` | Contains a list of objects. Each object contains the name, type, and value of a parameter in the API operation, as defined in the OpenAPI schema.                                                                |
| request_body              | `BedrockAgentRequestBody`    | Contains the request body and its properties, as defined in the OpenAPI schema.                                                                                                                                  |
| session_attributes        | `Dict[str, str]`             | Contains session attributes and their values.                                                                                                                                                                    |
| prompt_session_attributes | `Dict[str, str]`             | Contains prompt attributes and their values.                                                                                                                                                                     |

### Additional metadata

To enrich the view that Agents for Amazon Bedrock has of your Lambda functions,
use a combination of [Pydantic Models](https://docs.pydantic.dev/latest/concepts/models/){target="_blank"} and [OpenAPI](https://www.openapis.org/){target="_blank"} type annotations to add constraints to your APIs parameters.

???+ info "When is this useful?"
	Adding constraints to your function parameters can help you to enforce data validation and improve the understanding of your APIs by Amazon Bedrock.

#### Customizing OpenAPI parameters

--8<-- "docs/core/event_handler/_openapi_customization_parameters.md"

To implement these customizations, include extra constraints when defining your parameters:

```python hl_lines="19" title="customizing_api_parameters.py" title="Customizing API parameters"
--8<-- "examples/event_handler_bedrock_agents/src/customizing_bedrock_api_parameters.py"
```

1. Title should not be larger than 200 characters and [strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/){target="_blank"} is activated

#### Customizing API operations

--8<-- "docs/core/event_handler/_openapi_customization_operations.md"

To implement these customizations, include extra parameters when defining your routes:

```python hl_lines="13-22" title="customizing_api_operations.py" title="Customzing API operations"
--8<-- "examples/event_handler_bedrock_agents/src/customizing_bedrock_api_operations.py"
```

## Testing your code

Test your routes by passing an [Agent for Amazon Bedrock proxy event](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html#agents-lambda-input) request:

=== "assert_bedrock_agent_response.py"

	```python hl_lines="21-23 27"
	--8<-- "examples/event_handler_bedrock_agents/src/assert_bedrock_agent_response.py"
	```

=== "assert_bedrock_agent_response_module.py"

	```python hl_lines="14-17"
	--8<-- "examples/event_handler_bedrock_agents/src/assert_bedrock_agent_response_module.py"
	```
