# Installation
With [SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)  installed, let's create powertools example project.
=== "shell"
```bash
sam init --location https://github.com/aws-samples/cookiecutter-aws-sam-python
```
Inside of the project directory you will find README.md file with detailed information how to use and deploy the code. Let's go through the code and discuss implemented functionalities in details.

## Code example
Looking at the code included in an app.py file from our hello world project we see 4 Lambda Powertools features included. It is tracing, logging, custom metrics and event handler routing. Our hello-world application consist of few visible sections. First in line 1-6 imports all necessary lambda Powertools packages. Second in line 8-10 institutes all features. Last section creates 3 methods (hello, hello_you and lambda_handler). Every of them is extended with Powertools  functionality instantiated in section two by using decorators.

=== "app.py"
```python
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

tracer = Tracer()
logger = Logger()
metrics = Metrics()
app = ApiGatewayResolver()

@app.get("/hello")
@tracer.capture_method
def hello():
    query_string_name = app.current_event.get_query_string_value(name="name", default_value="universe")
    logger.info(f"Message returned:  {query_string_name}")
    return {"message": f"hello {query_string_name}"}


@app.get("/hello/<name>")
@tracer.capture_method
def hello_you(name):
    metrics.add_metric(name="SuccessfulMessageGeneration", unit=MetricUnit.Count, value=1)
    tracer.put_annotation(key="path", value=f"/hello/{name}")
    return {"message": f"hello {name}"}


@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception(e)
        raise
```

## Structured Logging
Build the package and invoke lambda code locally.
=== "bash"
```bash
make build && make run
```

=== "app.py"
```python hl_lines="1 2 8 16 28 35"
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

tracer = Tracer()
logger = Logger()
metrics = Metrics()
app = ApiGatewayResolver()

@app.get("/hello")
@tracer.capture_method
def hello():
    query_string_name = app.current_event.get_query_string_value(name="name", default_value="universe")
    logger.info(f"Message returned: {query_string_name}")
    return {"message": f"hello {query_string_name}"}


@app.get("/hello/<name>")
@tracer.capture_method
def hello_you(name):
    metrics.add_metric(name="SuccessfulMessageGeneration", unit=MetricUnit.Count, value=1)
    tracer.put_annotation(key="path", value=f"/hello/{name}")
    return {"message": f"hello {name}"}


@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception(e)
        raise
```

As a result, we should see two records in our logs following the same structured pattern. First one includes the whole event and context thanks to `inject_lambda_context` decorator. Second is the result of invoking `logger.info` in `hello` method.
=== "Example CloudWatch Log"
```json
{"level":"INFO","location":"hello:17","message":"Message returned:  universe","timestamp":"2021-10-22 16:29:58,367+0000","service":"hello","sampling_rate":"0.1","cold_start":true,"function_name":"HelloWorldFunction","function_memory_size":"256","function_arn":"arn:aws:lambda:us-east-1:012345678912:function:HelloWorldFunction","function_request_id":"d50bb07a-7712-4b2d-9f5d-c837302221a2","correlation_id":"bf9b584c-e5d9-4ad5-af3d-db953f2b10dc"}
```

## X-Ray Tracing

=== "app.py"
```python hl_lines="1 7 13 21 30"
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

tracer = Tracer()
logger = Logger()
metrics = Metrics()
app = ApiGatewayResolver()

@app.get("/hello")
@tracer.capture_method
def hello():
    query_string_name = app.current_event.get_query_string_value(name="name", default_value="universe")
    logger.info(f"Message returned: {query_string_name}")
    return {"message": f"hello {query_string_name}"}


@app.get("/hello/<name>")
@tracer.capture_method
def hello_you(name):
    metrics.add_metric(name="SuccessfulMessageGeneration", unit=MetricUnit.Count, value=1)
    tracer.put_annotation(key="path", value=f"/hello/{name}")
    return {"message": f"hello {name}"}


@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception(e)
        raise
```    

Configure aws credentials to ensure you deploy it to the specific account then build and deploy your code. Next invoke your remote lambda.
=== "bash"
```bash
make deploy.guided && aws lambda invoke --function-name <function-name> response.json
```

As a result, you should see traces for your lambda in X-RAY console.
![Tracer utility](./media/tracer_utility_showcase_2.png)

## Custom Metrics
Let's extend our code with application metrics.

=== "app.py"
```python hl_lines="1 9 23"
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

tracer = Tracer()
logger = Logger()
metrics = Metrics()
app = ApiGatewayResolver()

@app.get("/hello")
@tracer.capture_method
def hello():
    query_string_name = app.current_event.get_query_string_value(name="name", default_value="universe")
    logger.info(f"Message returned: {query_string_name}")
    return {"message": f"hello {query_string_name}"}


@app.get("/hello/<name>")
@tracer.capture_method
def hello_you(name):
    metrics.add_metric(name="SuccessfulMessageGeneration", unit=MetricUnit.Count, value=1)
    tracer.put_annotation(key="path", value=f"/hello/{name}")
    return {"message": f"hello {name}"}


@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception(e)
        raise
```
In order to see CloudWatch Embedded Metric Format logs you can invoke lambda locally.
=== "shell"
```shell
make build && make invoke
```

=== "Example CloudWatch EMF Log"
```json
{"_aws":{"Timestamp":1634299249318,"CloudWatchMetrics":[{"Namespace":"ApplicationMetrics","Dimensions":[["service"]],"Metrics":[{"Name":"SuccessfulMessageGeneration","Unit":"Count"}]}]},"service":"exampleAPP","SuccessfulMessageGeneration":[1.0]}
```
if you deploy this changes into your account those logs will be picked up by cloudwatch and corresponding metrics will be generated.
=== "shell"
```bash
make build && make deploy
```
![Custom Metrics](./media/metrics_utility_showcase.png)

## Event Handler for Amazon API Gateway
You might also add event handler router capabilities into your lambda. This way you might configure different methods in your lambda code to be triggered by different API paths.

=== "app.py"
```python hl_lines="5 10 12 20 33"
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

tracer = Tracer()
logger = Logger()
metrics = Metrics()
app = ApiGatewayResolver()

@app.get("/hello")
@tracer.capture_method
def hello():
    query_string_name = app.current_event.get_query_string_value(name="name", default_value="universe")
    logger.info(f"Message returned: {query_string_name}")
    return {"message": f"hello {query_string_name}"}


@app.get("/hello/<name>")
@tracer.capture_method
def hello_you(name):
    metrics.add_metric(name="SuccessfulMessageGeneration", unit=MetricUnit.Count, value=1)
    tracer.put_annotation(key="path", value=f"/hello/{name}")
    return {"message": f"hello {name}"}


@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception(e)
        raise
```

Let's test it locally. Run following command in one shell.
=== "shell"
```sh
make build && make invoke
```
and trigger `/hello` and `/hello/<name>` endpoints in second.

=== "shell"
```sh
curl http://127.0.0.1:3000/hello
{"message":"hello universe"}
curl http://127.0.0.1:3000/hello/john
{"message":"hello john"}
curl http://127.0.0.1:3000/hello/anna
{"message":"hello anna"}
```