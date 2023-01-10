from aws_lambda_powertools.event_handler.router import APIGatewayRouter

router = APIGatewayRouter()


@router.get("/me")
def get_self():
    # router.current_event is a APIGatewayProxyEvent
    principal_id = router.current_event.request_context.authorizer.principal_id

    return {"principal_id": principal_id}
