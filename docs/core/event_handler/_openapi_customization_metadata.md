<!-- markdownlint-disable MD041 MD043 -->

Defining and customizing OpenAPI metadata gives detailed, top-level information about your API. Here's the method to set and tailor this metadata:

| Field Name         | Type           | Description                                                                                                                                                                         |
| ------------------ | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`            | `str`          | The title for your API. It should be a concise, specific name that can be used to identify the API in documentation or listings.                                                    |
| `version`          | `str`          | The version of the API you are documenting. This could reflect the release iteration of the API and helps clients understand the evolution of the API.                              |
| `openapi_version`  | `str`          | Specifies the version of the OpenAPI Specification on which your API is based. When using Pydantic v1 it defaults to 3.0.3, and when using Pydantic v2, it defaults to 3.1.0.       |
| `summary`          | `str`          | A short and informative summary that can provide an overview of what the API does. This can be the same as or different from the title but should add context or information.       |
| `description`      | `str`          | A verbose description that can include Markdown formatting, providing a full explanation of the API's purpose, functionalities, and general usage instructions.                     |
| `tags`             | `List[str]`    | A collection of tags that categorize endpoints for better organization and navigation within the documentation. This can group endpoints by their functionality or other criteria.  |
| `servers`          | `List[Server]` | An array of Server objects, which specify the URL to the server and a description for its environment (production, staging, development, etc.), providing connectivity information. |
| `terms_of_service` | `str`          | A URL that points to the terms of service for your API. This could provide legal information and user responsibilities related to the usage of the API.                             |
| `contact`          | `Contact`      | A Contact object containing contact details of the organization or individuals maintaining the API. This may include fields such as name, URL, and email.                           |
| `license_info`     | `License`      | A License object providing the license details for the API, typically including the name of the license and the URL to the full license text.                                       |
