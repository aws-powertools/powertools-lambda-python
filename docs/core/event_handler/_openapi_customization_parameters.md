<!-- markdownlint-disable MD041 MD043 -->
Whenever you use OpenAPI parameters to validate [query strings](api_gateway.md#validating-query-strings) or [path parameters](api_gateway.md#validating-path-parameters), you can enhance validation and OpenAPI documentation by using any of these parameters:

| Field name            | Type        | Description                                                                                                                                                                |
|-----------------------|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `alias`               | `str`       | Alternative name for a field, used when serializing and deserializing data                                                                                                 |
| `validation_alias`    | `str`       | Alternative name for a field during validation (but not serialization)                                                                                                     |
| `serialization_alias` | `str`       | Alternative name for a field during serialization (but not during validation)                                                                                              |
| `description`         | `str`       | Human-readable description                                                                                                                                                 |
| `gt`                  | `float`     | Greater than. If set, value must be greater than this. Only applicable to numbers                                                                                          |
| `ge`                  | `float`     | Greater than or equal. If set, value must be greater than or equal to this. Only applicable to numbers                                                                     |
| `lt`                  | `float`     | Less than. If set, value must be less than this. Only applicable to numbers                                                                                                |
| `le`                  | `float`     | Less than or equal. If set, value must be less than or equal to this. Only applicable to numbers                                                                           |
| `min_length`          | `int`       | Minimum length for strings                                                                                                                                                 |
| `max_length`          | `int`       | Maximum length for strings                                                                                                                                                 |
| `pattern`             | `string`    | A regular expression that the string must match.                                                                                                                           |
| `strict`              | `bool`      | If `True`, strict validation is applied to the field. See [Strict Mode](https://docs.pydantic.dev/latest/concepts/strict_mode/){target"_blank" rel="nofollow"} for details |
| `multiple_of`         | `float`     | Value must be a multiple of this. Only applicable to numbers                                                                                                               |
| `allow_inf_nan`       | `bool`      | Allow `inf`, `-inf`, `nan`. Only applicable to numbers                                                                                                                     |
| `max_digits`          | `int`       | Maximum number of allow digits for strings                                                                                                                                 |
| `decimal_places`      | `int`       | Maximum number of decimal places allowed for numbers                                                                                                                       |
| `examples`            | `List[Any]` | List of examples of the field                                                                                                                                              |
| `deprecated`          | `bool`      | Marks the field as deprecated                                                                                                                                              |
| `include_in_schema`   | `bool`      | If `False` the field will not be part of the exported OpenAPI schema                                                                                                       |
| `json_schema_extra`   | `JsonDict`  | Any additional JSON schema data for the schema property                                                                                                                    |
