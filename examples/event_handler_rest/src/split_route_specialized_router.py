from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.router import APIGatewayRouter

app = APIGatewayRestResolver()
router = APIGatewayRouter()


@router.get("/me")
def get_self():
    # router.current_event is a APIGatewayProxyEvent
    account_id = router.current_event.request_context.account_id

    return {"account_id": account_id}


app.include_router(router)


def lambda_handler(event, context):
    return app.resolve(event, context)
