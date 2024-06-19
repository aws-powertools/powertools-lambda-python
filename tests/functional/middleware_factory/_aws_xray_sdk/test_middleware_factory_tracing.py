from aws_lambda_powertools.middleware_factory import lambda_handler_decorator


def test_factory_explicit_tracing(monkeypatch):
    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "true")

    @lambda_handler_decorator(trace_execution=True)
    def no_op(handler, event, context):
        ret = handler(event, context)
        return ret

    @no_op
    def lambda_handler(evt, ctx):
        return True

    lambda_handler({}, {})


def test_factory_explicit_tracing_env_var(monkeypatch):
    monkeypatch.setenv("POWERTOOLS_TRACE_MIDDLEWARES", "true")
    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "true")

    @lambda_handler_decorator
    def no_op(handler, event, context):
        ret = handler(event, context)
        return ret

    @no_op
    def lambda_handler(evt, ctx):
        return True

    lambda_handler({}, {})
