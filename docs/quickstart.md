---
title: QuickStart
description: Powertools introduction
---

This quickstart progressively introduces Lambda Powertools core utilities by using one feature at a time.

## Requirements

* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html){target="_blank"} and [configured with your credentials](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-set-up-credentials.html){target="_blank"}.
* [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html){target="_blank"} installed.

## Getting started

Let's clone our sample project before we add one feature at a time.

???+ tip "Tip: Want to skip to the final project?"
    Bootstrap directly via SAM CLI: `sam init --location https://github.com/aws-samples/cookiecutter-aws-sam-python`

```bash title="Use SAM CLI to initialize the sample project"
sam init --runtime python3.9 --dependency-manager pip --app-template hello-world --name powertools-quickstart
```

### Project structure

As we move forward, we will modify the following files within the `powertools-quickstart` folder:

* **app.py** - Application code.
* **template.yaml** - AWS infrastructure configuration using SAM.
* **requirements.txt** - List of extra Python packages needed.

### Code example

Let's configure our base application to look like the following code snippet.

=== "app.py"

    ```python
    import json


    def hello():
        return {"statusCode": 200, "body": json.dumps({"message": "hello unknown!"})}


    def lambda_handler(event, context):
        return hello()
    ```

=== "template.yaml"

    ```yaml
    AWSTemplateFormatVersion: '2010-09-09'
    Transform: AWS::Serverless-2016-10-31
    Description: Sample SAM Template for powertools-quickstart
    Globals:
        Function:
            Timeout: 3
    Resources:
        HelloWorldFunction:
            Type: AWS::Serverless::Function
            Properties:
                CodeUri: hello_world/
                Handler: app.lambda_handler
                Runtime: python3.9
                Architectures:
                    - x86_64
                Events:
                    HelloWorld:
                        Type: Api
                        Properties:
                            Path: /hello
                            Method: get
    Outputs:
        HelloWorldApi:
            Description: "API Gateway endpoint URL for Prod stage for Hello World function"
            Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/hello/"
    ```
Our Lambda code consists of an entry point function named `lambda_handler`, and a `hello` function.

When API Gateway receives a HTTP GET request on `/hello` route, Lambda will call our `lambda_handler` function, subsequently calling the `hello` function. API Gateway will use this response to return the correct HTTP Status Code and payload back to the caller.

!!! Warning
    For simplicity, we do not set up authentication and authorization! You can find more information on how to implement it on [AWS SAM documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-controlling-access-to-apis.html){target="_blank"}.
### Run your code

At each point, you have two ways to run your code: locally and within your AWS account.

#### Local test

AWS SAM allows you to execute a serverless application locally by running `sam build && sam local start-api` in your preferred shell.

```bash title="Build and run API Gateway locally"
> sam build && sam local start-api
...
2021-11-26 17:43:08  * Running on http://127.0.0.1:3000/ (Press CTRL+C to quit)
```

As a result, a local API endpoint will be exposed and you can invoke it using your browser, or your preferred HTTP API client e.g., [Postman](https://www.postman.com/downloads/){target="_blank"}, [httpie](https://httpie.io/){target="_blank"}, etc.

```bash title="Invoking our function locally via curl"
> curl http://127.0.0.1:3000/hello
{"message": "hello unknown!"}
```

!!! info
    To learn more about local testing, please visit the [AWS SAM CLI local testing](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html) documentation.


#### Live test

First, you need to deploy your application into your AWS Account by issuing `sam build && sam deploy --guided` command. This command builds a ZIP package of your source code, and deploy it to your AWS Account.

```bash title="Build and deploy your serverless application"
> sam build && sam deploy --guided
...
CloudFormation outputs from deployed stack
------------------------------------------------------------------------------------------------------------------------------------------
Outputs
------------------------------------------------------------------------------------------------------------------------------------------
Key                 HelloWorldFunctionIamRole
Description         Implicit IAM Role created for Hello World function
Value               arn:aws:iam::123456789012:role/sam-app-HelloWorldFunctionRole-1T2W3H9LZHGGV

Key                 HelloWorldApi
Description         API Gateway endpoint URL for Prod stage for Hello World function
Value               https://1234567890.execute-api.eu-central-1.amazonaws.com/Prod/hello/

Key                 HelloWorldFunction
Description         Hello World Lambda Function ARN
Value               arn:aws:lambda:eu-central-1:123456789012:function:sam-app-HelloWorldFunction-dOcfAtYoEiGo
------------------------------------------------------------------------------------------------------------------------------------------
Successfully created/updated stack - sam-app in eu-central-1
```

At the end of the deployment, you will find the API endpoint URL within `Outputs` section. You can use this URL to test your serverless application.

```bash title="Invoking our application via API endpoint"
> curl https://1234567890.execute-api.eu-central-1.amazonaws.com/Prod/hello
{"message": "hello unknown!"}%
```
!!! Info
    For more details on AWS SAM deployment mechanism, see [SAM Deploy reference docs](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-deploy.html).

## Routing

### Adding a new route

Let's expand our application with a new route - `/hello/{name}`. It will accept an username as a path input and return it in the response.

For this to work, we could create a new Lambda function to handle incoming requests for `/hello/{name}` - It'd look like this:

=== "hello_by_name.py"

    ```python
    import json


    def hello_name(name):
        return {"statusCode": 200, "body": json.dumps({"message": f"hello {name}!"})}


    def lambda_handler(event, context):
        name = event["pathParameters"]["name"]
        return hello_name(name)
    ```

=== "template.yaml"

    ```yaml hl_lines="21-32"
    AWSTemplateFormatVersion: "2010-09-09"
    Transform: AWS::Serverless-2016-10-31
    Description: Sample SAM Template for powertools-quickstart
    Globals:
        Function:
            Timeout: 3
    Resources:
        HelloWorldFunction:
            Type: AWS::Serverless::Function
            Properties:
                CodeUri: hello_world/
                Handler: app.lambda_handler
                Runtime: python3.9
                Events:
                    HelloWorld:
                        Type: Api
                        Properties:
                            Path: /hello
                            Method: get

        HelloWorldByNameFunctionName:
            Type: AWS::Serverless::Function
            Properties:
                CodeUri: hello_world/
                Handler: hello_by_name.lambda_handler
                Runtime: python3.9
                Events:
                    HelloWorldName:
                        Type: Api
                        Properties:
                            Path: /hello/{name}
                            Method: get
    Outputs:
        HelloWorldApi:
            Description: "API Gateway endpoint URL for Prod stage for Hello World function"
            Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/hello/"
    ```

???+ question
    But what happens if your application gets bigger and we need to cover numerous URL paths and HTTP methods for them?

**This would quickly become non-trivial to maintain**. Adding new Lambda function for each path, or multiple if/else to handle several routes & HTTP Methods can be error prone.

### Creating our own router

???+ question
    What if we create a simple router to reduce boilerplate?

We could group similar routes and intents, separate read and write operations resulting in fewer functions. It doesn't address the boilerplate routing code, but maybe it will be easier to add additional URLs.

!!! Info "Info: You might be already asking yourself about mono vs micro-functions"
    If you want a more detailed explanation of these two approaches, head over to the [trade-offs on each approach](../core/event_handler/api_gateway/#considerations){target="_blank"} later.

A first attempt at the routing logic might look similar to the following code snippet.

=== "app.py"

    ```python hl_lines="4 9 13 27-29 35-36"
        import json


        def hello_name(event, **kargs):
            username = event["pathParameters"]["name"]
            return {"statusCode": 200, "body": json.dumps({"message": f"hello {username}!"})}


        def hello(**kargs):
            return {"statusCode": 200, "body": json.dumps({"message": "hello unknown!"})}


        class Router:
            def __init__(self):
                self.routes = {}

            def set(self, path, method, handler):
                self.routes[f"{path}-{method}"] = handler

            def get(self, path, method):
                try:
                    route = self.routes[f"{path}-{method}"]
                except KeyError:
                    raise RuntimeError(f"Cannot route request to the correct method. path={path}, method={method}")
                return route

        router = Router()
        router.set(path="/hello", method="GET", handler=hello)
        router.set(path="/hello/{name}", method="GET", handler=hello_name)


        def lambda_handler(event, context):
            path = event["resource"]
            http_method = event["httpMethod"]
            method = router.get(path=path, method=http_method)
            return method(event=event)
    ```

=== "template.yaml"

    ```yaml hl_lines="15-24"
        AWSTemplateFormatVersion: "2010-09-09"
        Transform: AWS::Serverless-2016-10-31
        Description: Sample SAM Template for powertools-quickstart
        Globals:
            Function:
                Timeout: 3
        Resources:
            HelloWorldFunction:
                Type: AWS::Serverless::Function
                Properties:
                    CodeUri: hello_world/
                    Handler: app.lambda_handler
                    Runtime: python3.9
                    Events:
                        HelloWorld:
                            Type: Api
                            Properties:
                                Path: /hello
                                Method: get
                        HelloWorldName:
                            Type: Api
                            Properties:
                                Path: /hello/{name}
                                Method: get
        Outputs:
            HelloWorldApi:
                Description: "API Gateway endpoint URL for Prod stage for Hello World function"
                Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/hello/"
    ```

Let's break this down:

* **L4-9**: We defined two `hello_name` and `hello` functions to handle `/hello/{name}` and `/hello` routes
* **L13:** We added a `Router` class to map a path, a method, and the function to call
* **L27-29**: We create a `Router` instance and map both `/hello` and `/hello/{name}`
* **L35:** We use Router's `get` method to retrieve a reference to the processing method (`hello` or `hello_name`)
* **L36:** Finally, we run this method and send the results back to API Gateway

This approach simplifies the configuration of our infrastructure since we have added all API Gateway paths in the `HelloWorldFunction` event section.

However, it forces us to understand the internal structure of the API Gateway request events, responses, and it could lead to other errors such as CORS not being handled properly, error handling, etc.

### Simplifying with Event Handler

We can massively simplify cross-cutting concerns while keeping it lightweight by using [Event Handler](./core/event_handler/api_gateway.md){target="_blank"}

!!! tip
    This is available for both [REST API (API Gateway, ALB)](./core/event_handler/api_gateway.md){target="_blank"} and [GraphQL API (AppSync)](./core/event_handler/appsync.md){target="_blank"}.

Let's include Lambda Powertools as a dependency in `requirement.txt`, and use Event Handler to refactor our previous example.

=== "app.py"

    ```python hl_lines="3 5 8 13 19"
    import json

    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

    app = ApiGatewayResolver()


    @app.get("/hello/<name>")
    def hello_name(name):
        return {"message": f"hello {name}!"}


    @app.get("/hello")
    def hello():
        return {"message": "hello unknown!"}


    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```
=== "requirements.txt"

    ```bash
    aws-lambda-powertools
    ```

Use `sam build && sam local start-api` and try run it locally again.

???+ note
    If you're coming from [Flask](https://flask.palletsprojects.com/en/2.0.x/){target="_blank"}, you will be familiar with this experience already. [Event Handler for API Gateway](./core/event_handler/api_gateway.md){target="_blank"} uses `ApiGatewayResolver` to give a Flask-like experience while staying true to our tenet `Keep it lean`.

We have added the route annotation as the decorator for our methods. It enables us to use the parameters passed in the request directly, and our responses are simply dictionaries.

Lastly, we used `return app.resolve(event, context)` so Event Handler can resolve routes, inject the current request, handle serialization, route validation, etc.

From here, we could handle [404 routes](./core/event_handler/api_gateway.md#handling-not-found-routes){target="_blank"}, [error handling](./core/event_handler/api_gateway.md#http://127.0.0.1:8000/core/event_handler/api_gateway/#exception-handling){target="_blank"}, [access query strings, payload, etc.](./core/event_handler/api_gateway.md#http://127.0.0.1:8000/core/event_handler/api_gateway#accessing-request-details){target="_blank"}.


!!! tip
    If you'd like to learn how python decorators work under the hood, you can follow [Real Python](https://realpython.com/primer-on-python-decorators/)'s article.
## Structured Logging

Over time, you realize that searching logs as text results in poor observability, it's hard to create metrics from, enumerate common exceptions, etc.

Then, you decided to propose production quality logging capabilities to your Lambda code. You found out that by having logs as `JSON` you can [structure them](https://docs.aws.amazon.com/lambda/latest/operatorguide/parse-logs.html), so that you can use any Log Analytics tool out there to quickly analyze them.

This helps not only in searching, but produces consistent logs containing enough context and data to ask arbitrary questions on the status of your system. We can take advantage of CloudWatch Logs and Cloudwatch Insight for this purpose.

### JSON as output

The first option could be to use the standard Python Logger, and use a specialized library like `pythonjsonlogger` to create a JSON Formatter.

=== "app.py"

    ```python hl_lines="2 5 9-14 21 27 32"
    import json
    import logging
    import os

    from pythonjsonlogger import jsonlogger

    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

    logger = logging.getLogger("hello")
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s")
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

    app = ApiGatewayResolver()


    @app.get("/hello/<name>")
    def hello_name(name):
        logger.info(f"Request from {name} received")
        return {"statusCode": 200, "body": json.dumps({"message": f"hello {name}!"})}


    @app.get("/hello")
    def hello():
        logger.info("Request from unknown received")
        return {"statusCode": 200, "body": json.dumps({"message": "hello unknown!"})}


    def lambda_handler(event, context):
        logger.debug(event)
        return app.resolve(event, context)
    ```
=== "requirements.txt"

    ```bash
    aws-lambda-powertools
    python-json-logger
    ```

With just a few lines our logs will now output to `JSON` format. We've taken the following steps to make that work:

* **L9**: Creates an application logger named `hello`
* **L10-13**: Configures handler and formatter
* **L14**: Sets the logging level set in the `LOG_LEVEL` environment variable, or `INFO` as a sentinel value

After that, we use this logger in our application code to record the required information. We see logs structured as follows:

=== "JSON output"

    ```json
    {
        "asctime": "2021-11-22 15:32:02,145",
        "levelname": "INFO",
        "name": "hello",
        "message": "Request from unknown received"
    }
    ```

=== "Normal output"

    ```python
    [INFO]  2021-11-22T15:32:02.145Z        ba3bea3d-fe3a-45db-a2ce-72e813d55b91    Request from unknown received
    ```

So far, so good! We can take a step further now by adding additional context to the logs.

We could start by creating a dictionary with Lambda context information or something from the incoming event, which should always be logged. Additional attributes could be added on every `logger.info` using `extra` keyword like in any standard Python logger.


### Simplifying with Logger

???+ question "Surely this could be easier, right?"
    Yes! Powertools Logger to the rescue :-)

As we already have Lambda Powertools as a dependency, we can simply import [Logger](./core/logger.md){target="_blank"}.

=== "app.py"

    ```python hl_lines="3 5 7 14 20 24"
    import json

    from aws_lambda_powertools import Logger
    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
    from aws_lambda_powertools.logging import correlation_paths

    logger = Logger(service="order")

    app = ApiGatewayResolver()


    @app.get("/hello/<name>")
    def hello_name(name):
        logger.info(f"Request from {name} received")
        return {"statusCode": 200, "body": json.dumps({"message": f"hello {name}!"})}


    @app.get("/hello")
    def hello():
        logger.info("Request from unknown received")
        return {"statusCode": 200, "body": json.dumps({"message": "hello unknown!"})}


    @logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```

Let's break this down:

* **L8**: We add Lambda Powertools Logger; the boilerplate is now done for you. By default, we set `INFO` as the logging level if `LOG_LEVEL` env var isn't set
* **L24**: We use `logger.inject_lambda_context` decorator to inject key information from Lambda context into every log.
* **L24**: We also instruct Logger to use the incoming API Gateway Request ID as a [correlation id](./core/logger.md##set_correlation_id-method) automatically.
* **L24**: Since we're in dev, we also use `log_event=True` to automatically log each incoming request for debugging. This can be also set via [environment variables](./index.md#environment-variables){target="_blank"}.

We can now search our logs by the request ID to find a specific operation. Additionally, we can also search our logs for function name, Lambda request ID, Lambda function ARN, find out whether an operation was a cold start, etc.

This is how the logs would look like now:

```json title="Our logs are now structured consistently"
{
    "level":"INFO",
    "location":"hello:17",
    "message":"Request from unknown received",
    "timestamp":"2021-10-22 16:29:58,367+0000",
    "service":"hello",
    "sampling_rate":"0.1",
    "cold_start":true,
    "function_name":"HelloWorldFunction",
    "function_memory_size":"256",
    "function_arn":"arn:aws:lambda:us-east-1:123456789012:function:HelloWorldFunction",
    "function_request_id":"d50bb07a-7712-4b2d-9f5d-c837302221a2",
    "correlation_id":"bf9b584c-e5d9-4ad5-af3d-db953f2b10dc"
    }
```

From here, we could [set specific keys](./core/logger.md#append_keys-method){target="_blank"} to add additional contextual information about a given operation, [log exceptions](./core/logger.md#logging-exceptions){target="_blank"} to easily enumerate them later, [sample debug logs](./core/logger.md#sampling-debug-logs){target="_blank"}, etc.

By having structured logs like this, we can easily search and analyse them in [CloudWatch Logs Insight](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html){target="_blank"}.

=== "CloudWatch Logs Insight Example"
![CloudWatch Logs Insight Example](./media/cloudwatch_logs_insight_example.png)
## Tracing

!!! warning
    **Tracer** uses AWS X-Ray and you will not see any traces when executing your function locally.

The next improvement is to add an appropriate tracking mechanism to your stack. Developers want to analyze traces of queries that pass via the API gateway to your Lambda.
With structured logs, it is an important step to provide the observability of your application!
The AWS service that has these capabilities is [AWS X-RAY](https://aws.amazon.com/xray/). How do we send application trace to the AWS X-RAY service then?

Let's first explore how we can achieve this with [x-ray SDK](https://docs.aws.amazon.com/xray-sdk-for-python/latest/reference/index.html), and then try to simplify it with the Powertools library.

=== "app.py"

    ```python hl_lines="3 14 19-20 27-28 35-41"
    import json

    from aws_xray_sdk.core import xray_recorder

    from aws_lambda_powertools import Logger
    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
    from aws_lambda_powertools.logging import correlation_paths

    logger = Logger(service="APP")

    app = ApiGatewayResolver()


    cold_start = True


    @app.get("/hello/<name>")
    def hello_name(name):
        with xray_recorder.in_subsegment("hello_name") as subsegment:
            subsegment.put_annotation("User", name)
            logger.info(f"Request from {name} received")
            return {"statusCode": 200, "body": json.dumps({"message": f"hello {name}!"})}


    @app.get("/hello")
    def hello():
        with xray_recorder.in_subsegment("hello") as subsegment:
            subsegment.put_annotation("User", "unknown")
            logger.info("Request from unknown received")
            return {"statusCode": 200, "body": json.dumps({"message": "hello unknown!"})}


    @logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
    def lambda_handler(event, context):
        global cold_start
        with xray_recorder.in_subsegment("handler") as subsegment:
            if cold_start:
                subsegment.put_annotation("ColdStart", "True")
                cold_start = False
            else:
                subsegment.put_annotation("ColdStart", "False")
            return app.resolve(event, context)
    ```

=== "template.yaml"

    ```yaml hl_lines="15"
    AWSTemplateFormatVersion: "2010-09-09"
    Transform: AWS::Serverless-2016-10-31
    Description: Sample SAM Template for powertools-quickstart
    Globals:
        Function:
            Timeout: 3
    Resources:
        HelloWorldFunction:
            Type: AWS::Serverless::Function
            Properties:
                CodeUri: hello_world/
                Handler: app.lambda_handler
                Runtime: python3.9
                Tracing: Active
                Events:
                    HelloWorld:
                        Type: Api
                        Properties:
                            Path: /hello
                            Method: get
                    HelloWorldName:
                        Type: Api
                        Properties:
                            Path: /hello/{name}
                            Method: get
    Outputs:
        HelloWorldApi:
            Description: "API Gateway endpoint URL for Prod stage for Hello World function"
            Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/hello/"
    ```

* First, we import required X-ray SDK classes. `xray_recorder` is a global AWS X-ray recorder class instance that starts/ends segments/sub-segments and sends them to the X-ray daemon.
* To build new sub-segments, we use `xray_recorder.in_subsegment` method as a context manager.
* We track Lambda cold start by setting global variable outside of a handler. The variable is defined only upon Lambda initialization. This information provides an overview of how often the runtime is reused by Lambda invoked, which directly impacts Lambda performance and latency.

To allow the tracking of our Lambda, we need to set it up in our SAM template and add `Tracing: Active` under Lambda `Properties` section.
!!! Info
    Want to know more about context managers and understand the benefits of using them? Follow [article](https://realpython.com/python-with-statement/) from Real Python.
!!! Info
    If you want to understand how the Lambda execution environment works and why cold starts can occur, follow [blog series](https://aws.amazon.com/blogs/compute/operating-lambda-performance-optimization-part-1/).

Now, let's try to simplify it with Lambda Powertools:

=== "app.py"

    ```python hl_lines="3 13 15 21 23 29"
    import json

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
    from aws_lambda_powertools.logging import correlation_paths

    logger = Logger(service="APP")
    tracer = Tracer()
    app = ApiGatewayResolver()


    @app.get("/hello/<name>")
    @tracer.capture_method
    def hello_name(name):
        tracer.put_annotation("User", name)
        logger.info(f"Request from {name} received")
        return {"statusCode": 200, "body": json.dumps({"message": f"hello {name}!"})}


    @app.get("/hello")
    @tracer.capture_method
    def hello():
        tracer.put_annotation("User", "unknown")
        logger.info("Request from unknown received")
        return {"statusCode": 200, "body": json.dumps({"message": "hello unknown!"})}


    @logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```

With powertools tracer we have much cleaner code right now.

To make our methods visible in the traces, we add `@tracer.capture_method` decorator to the processing methods.
We add annotations directly in the code without adding it with the context handler using the `tracer.put_annotation` method.
Since we add the `@tracer.capture_lambda_handler` decorator for our `lambda_handler`, powertools automatically adds cold start information as an annotation.
It also automatically append Lambda response as a metadata into trace, so we don't need to worry about it.
!!! tip
    For differences between annotations and metadata in traces, please follow [link](https://awslabs.github.io/aws-lambda-powertools-python/latest/core/tracer/#annotations-metadata).

Therefore, you should see traces of your Lambda in the X-ray console.
=== "Example X-RAY Console View"
![Tracer utility](./media/tracer_utility_showcase_2.png)

You may consider using **CloudWatch ServiceLens** which links the CloudWatch metrics and logs, in addition to traces from the AWS X-Ray.

It gives you a complete view of your apps and their dependencies, making your services more observable.
From here, you can browse to specific logs in CloudWatch Logs Insight, Metrics Dashboard or Traces in CloudWatch X-Ray traces.
=== "Example CloudWatch ServiceLens View"
![CloudWatch ServiceLens View](./media/tracer_utility_showcase_3.png)
!!! Info
    For more information on CloudWatch ServiceLens, please visit [link](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ServiceLens.html).
## Custom Metrics
The final step to provide complete observability is to add business metrics (such as number of sales or reservations).
Lambda adds technical metrics (such as Invocations, Duration, Error Count & Success Rate) to the CloudWatch metrics out of the box.

Let's expand our application with custom metrics without Powertools to see how it works, then let's upgrade it with Powertools:-)

=== "app.py"

    ```python hl_lines="3 15 19 41 51"
    import json

    import boto3

    from aws_lambda_powertools import Logger, Tracer
    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
    from aws_lambda_powertools.logging import correlation_paths

    service = "APP"

    logger = Logger(service=service)
    tracer = Tracer()
    app = ApiGatewayResolver()

    metrics = boto3.client("cloudwatch")


    @tracer.capture_method
    def put_metric_data(service: str, method: str):
        response = metrics.put_metric_data(
            MetricData=[
                {
                    "MetricName": "AppMethodsInvocations",
                    "Dimensions": [
                        {"Name": "SERVICE", "Value": service},
                        {"Name": "METHOD", "Value": method},
                    ],
                    "Unit": "None",
                    "Value": 1,
                },
            ],
            Namespace="CustomMetrics",
        )
        return response


    @app.get("/hello/<name>")
    @tracer.capture_method
    def hello_name(name):
        logger.info(f"Request from {name} received")
        put_metric_data(service=service, method="/hello/<name>")
        tracer.put_annotation("User", name)
        return {"statusCode": 200, "body": json.dumps({"message": f"hello {name}!"})}


    @app.get("/hello")
    @tracer.capture_method
    def hello():
        tracer.put_annotation("User", "unknown")
        logger.info("Request from unknown received")
        put_metric_data(service=service, method="/hello")
        return {"statusCode": 200, "body": json.dumps({"message": "hello unknown!"})}


    @logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        return app.resolve(event, context)

    ```
=== "template.yaml"

    ```yaml hl_lines="27 28"
    AWSTemplateFormatVersion: "2010-09-09"
    Transform: AWS::Serverless-2016-10-31
    Description: Sample SAM Template for powertools-quickstart
    Globals:
        Function:
            Timeout: 3
    Resources:
        HelloWorldFunction:
            Type: AWS::Serverless::Function
            Properties:
                CodeUri: hello_world/
                Handler: app.lambda_handler
                Runtime: python3.9
                Tracing: Active
                Events:
                    HelloWorld:
                        Type: Api
                        Properties:
                            Path: /hello
                            Method: get
                    HelloWorldName:
                        Type: Api
                        Properties:
                            Path: /hello/{name}
                            Method: get
                Policies:
                    - CloudWatchPutMetricPolicy: {}
    Outputs:
        HelloWorldApi:
            Description: "API Gateway endpoint URL for Prod stage for Hello World function"
            Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/hello/"

    ```

To add custom metric in **CloudWatch** we add the `boto3` cloudwatch client. Next, we create the new `put_metric_data` method that uses this client to put the metric in CloudWatch synchronously. We call it in our method `hello` and `hello_name`. We divide our metrics by type of application and method. Thus, we can follow the frequency at which specific methods are called. We also need to add additional inline policy allowing our Lambda to write metrics in the CloudWatch. In `template.yaml` we add `CloudWatchPutMetricPolicy` policy.
!!! Info
    We use direct synchronous call to CloudWatch Metrics API. It will be visible in your AWS X-RAY traces as additional external call. Given your architecture scale, this approach might lead to disadvantages such as increased cost of measuring data collection and increased Lambda latency.

=== "app.py"

    ```python hl_lines="3 12 22-23 32-33 38"
    import json

    from aws_lambda_powertools import Logger, Tracer, Metrics
    from aws_lambda_powertools.metrics import MetricUnit
    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
    from aws_lambda_powertools.logging import correlation_paths

    service = "APP"

    logger = Logger(service=service)
    tracer = Tracer()
    metrics = Metrics(namespace="CustomMetrics", service=service)

    app = ApiGatewayResolver()


    @app.get("/hello/<name>")
    @tracer.capture_method
    def hello_name(name):
        tracer.put_annotation("User", name)
        logger.info(f"Request from {name} received")
        metrics.add_dimension(name="method", value="/hello/<name>")
        metrics.add_metric(name="AppMethodsInvocations", unit=MetricUnit.Count, value=1)
        return {"statusCode": 200, "body": json.dumps({"message": f"hello {name}!"})}


    @app.get("/hello")
    @tracer.capture_method
    def hello():
        tracer.put_annotation("User", "unknown")
        logger.info("Request from unknown received")
        metrics.add_dimension(name="method", value="/hello/<name>")
        metrics.add_metric(name="AppMethodsInvocations", unit=MetricUnit.Count, value=1)
        return {"statusCode": 200, "body": json.dumps({"message": "hello unknown!"})}


    @logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
    @metrics.log_metrics(capture_cold_start_metric=True)
    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        try:
            return app.resolve(event, context)
        except Exception as e:
            logger.exception(e)
            raise
    ```
We import Powertools `Metric` class which we create metrics instance from (line 10). We use it in the `hello` and `hello_name` method to first configure the dimension specific to the called method and we add our custom `AppMethodsInvocations` metric. To ensure that our metrics are aligned with the standard output and validated, we add the `metrics.log_metrics` decorator'.

Powertools Metrics uses [Amazon CloudWatch Embedded Metric Format (EMF)](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html) to create custom metrics. In
general we create log with specific format. This log, once pushed toward the CloudWatch Log Service, is automatically transformed into a CloudWatch metric.
!!!Info
    If you are interested in the details of the EMF mechanism, follow [blog post](https://aws.amazon.com/blogs/mt/enhancing-workload-observability-using-amazon-cloudwatch-embedded-metric-format/).

=== "Example CloudWatch EMF Log"
```json
{
  "_aws": {
    "Timestamp": 1638115724269,
    "CloudWatchMetrics": [
      {
        "Namespace": "CustomMetrics",
        "Dimensions": [
          [
            "method",
            "service"
          ]
        ],
        "Metrics": [
          {
            "Name": "AppMethodsInvocations",
            "Unit": "Count"
          }
        ]
      }
    ]
  },
  "method": "/hello/<name>",
  "service": "APP",
  "AppMethodsInvocations": [
    1
  ]
}
```
=== "Example CloudWatch Metric Console View"
![Custom Metrics Example](./media/metrics_utility_showcase.png)
