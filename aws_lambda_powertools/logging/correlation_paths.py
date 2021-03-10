"""Built-in correlation paths"""

API_GATEWAY_REST = "requestContext.requestId"
API_GATEWAY_HTTP = API_GATEWAY_REST
APPLICATION_LOAD_BALANCER = "headers.x-amzn-trace-id"
EVENT_BRIDGE = "id"
