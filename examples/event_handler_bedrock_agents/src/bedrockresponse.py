from http import HTTPStatus

from aws_lambda_powertools.event_handler import BedrockResponse

response = BedrockResponse(
    status_code=HTTPStatus.OK.value,
    body={"message": "Hello from Bedrock!"},
    session_attributes={"user_id": "123"},
    prompt_session_attributes={"context": "testing"},
    knowledge_bases_configuration={
        "knowledgeBaseId": "kb-123",
        "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": 3, "overrideSearchType": "HYBRID"}},
    },
)
