from aws_lambda_powertools.event_handler.api_gateway_websocket import Router

router = Router()


@router.route("orderUpdate")
def order_update():
    order = router.current_event.json_body  # (1)!
    return {"orderId": order["orderId"], "status": "received"}


@router.route("orderCancel")
def order_cancel():
    order = router.current_event.json_body
    return {"orderId": order["orderId"], "status": "cancelled"}
