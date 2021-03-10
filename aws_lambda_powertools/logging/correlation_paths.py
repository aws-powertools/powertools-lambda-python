"""Built-in correlation paths"""

API_GATEWAY_REST = "requestContext.requestId"
API_GATEWAY_HTTP = API_GATEWAY_REST
APP_SYNC_RESOLVER = "request.headers.x-amzn-trace-id"
APPLICATION_LOAD_BALANCER = "headers.x-amzn-trace-id"
EVENT_BRIDGE = "id"
