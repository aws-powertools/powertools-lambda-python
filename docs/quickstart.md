---
title: QuickStart
description: Powertools introduction
---
Quickstart introducing core Powertools functionalities.


## Installation
With [SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) installed, you can either follow this quickstart step by step or you can create project with final quickstart code to play with.
If you want to follow it from very beginning just create new empty project.
=== "shell"
```bash
sam init --runtime python3.9 --dependency-manager pip --app-template hello-world --name powertools-quickstart
```
If you want to play with the final code then you can download it from [aws-samples](https://github.com/aws-samples/cookiecutter-aws-sam-python) github repository.
=== "shell"
```bash
sam init --location https://github.com/aws-samples/cookiecutter-aws-sam-python
```


### Code example and Configuration
Inside of the powertools-quickstart directory we will modify following files:

* **app.py** - File that contains our application code.
* **template.yaml** - AWS infrastructure configuration using SAM template format.
* **requirements.txt** - Python pip packages configuration.

Also, ensure you [configure your AWS credentials](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-set-up-credentials.html) to be able to connect and deploy example code into your AWS account. 
Once it is done, lets configure our basic application to looks like the following code snippet.
=== "app.py"

    ```python
    def hello():
        return {"statusCode": 200, "body": {"message": "hello unknown!"}}

    def lambda_handler(event, context):
        return hello()
    ```

=== "template.yaml"

    ```yaml
    AWSTemplateFormatVersion: '2010-09-09'
    Transform: AWS::Serverless-2016-10-31
    Description: >
        Sample SAM Template for powertools-quickstart
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
Our lambda code consist of `lambda_handler` method which is invoked by API and `hello` method which returns result to the API Gateway and is invoked by handler itself.
SAM template configures API Gateway that redirects traffic to Lambda for only one path: `hello`. 
!!! Warning 
    For simplicity we don't configure authentication and authorization in the example!
### Run your code
On every step you have two ways of testing your code. Locally and in your AWS account. Since we use SAM both methods are equally straightforward.
#### Local test
SAM allows you to run serverless application locally. Run following command in a shell.
```bash
> sam build && sam local start-api
...
2021-11-26 17:43:08  * Running on http://127.0.0.1:3000/ (Press CTRL+C to quit)
```
As a result API endpoint will be exposed for you. You can trigger it using `curl` command as with following example.
```bash
> curl http://127.0.0.1:3000/hello
{"statusCode":200,"body":{"message":"hello unknown!"}}%  
```
!!! info
    You can read more about local testing under following link: [SAM local testing](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html)
!!! warning
    **Powertools Tracer** requires X-RAY service to work. It means that you won't be able to see traces locally. Deploy example to your AWS account instead.
#### Remote test
You may also deploy your application into AWS Account by issuing following command.
```bash
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
This command will build package and deploy it to your AWS Account. Make sure you configure AWS credentials beforehand. In the outputs section you find API Url you can issue request against.
!!! Info
    To learn more about SAM deployment mechanism follow this [link](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-deploy.html).

## API Gateway router
Let's say you have been asked to create another method that respond with caller name under `/hello/<name>` URL path.
One approach would be to create another lambda with required method and configure API gateway to call it.
=== "app_name.py"

    ```python
    def hello_name(name):
        return {"statusCode": 200, "body": {"message": f"hello {name}!"}}


    def lambda_handler(event, context):
        name = event["pathParameters"]["name"]
        return hello_name(name)
    ```

=== "template.yaml"

    ```yaml hl_lines="22-33"
    AWSTemplateFormatVersion: "2010-09-09"
    Transform: AWS::Serverless-2016-10-31
    Description: > 
        Sample SAM Template for powertools-quickstart
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
        HelloWorldFunctionName:
            Type: AWS::Serverless::Function
            Properties:
            CodeUri: hello_world/
            Handler: app_name.lambda_handler
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

This way definitively works. The downside of this approach is that you need to create new lambda file for every method or path and also configure SAM template to add new lambda configuration and configure API Gateway to point into them. For small additional methods it might be too much boilerplate code.  
Another approach though that might be more suitable in this case is to have all of our methods under control of one lambda and "route" into specific method based on a request. 
!!! Info
    If you are interested in more detailed explanation between those two approaches we explained considerations [here](../core/event_handler/api_gateway/#considerations)
Example, naive code might look like the following code snippet.
=== "app.py"

    ```python hl_lines="10-23 26-28 34-35"
        def hello_name(event, **kargs):
            username = event["pathParameters"]["name"]
            return {"statusCode": 200, "body": {"message": f"hello {username}!"}}


        def hello(**kargs):
            return {"statusCode": 200, "body": {"message": "hello unknown!"}}


        class Router:
            def __init__(self):
                self.routes = {}

            def set(self, path, method, handler):
                self.routes[f"{path}-{method}"] = handler

            def get(self, path, method):
                try:
                    route = self.routes[f"{path}-{method}"]
                except:
                    print("Cannot route request to correct method")
                    raise NotImplemented
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

    ```yaml hl_lines="18-28"
        AWSTemplateFormatVersion: "2010-09-09"
        Transform: AWS::Serverless-2016-10-31
        Description: >
            Sample SAM Template for powertools-quickstart
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
In this example we added two methods `hello_name` and `hello` next to each other. We added `Router` class that allow us to register what method should be called when specific request comes. 
We created instance of it and added configuration with mapping between processing methods and http request method. 
In lambda handler we call router instance get method to fetch reference to processing method (`hello` or `hello_name`) that will handle the request. 
Finally we run this method and return result to API Gateway.

Thanks to this approach, we can simplify our infrastructure configuration since we added all API Gateway path under `HelloWorldFunction` event section. 
Downside of current approach is that we need to add custom class and with every new method or path we want to serve we need to add explicit configuration. 
Also, we need to understand API Gateway request event structure in order to decapsulate requested path and http method. 
In order to mitigate this downsides we use Lambda Powertools.

=== "app.py"

    ```python hl_lines="1 4 7 12 18"
    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver


    app = ApiGatewayResolver()


    @app.get("/hello/<name>")
    def hello_name(name):
        return {"statusCode": 200, "body": {"message": f"hello {name}!"}}


    @app.get("/hello")
    def hello():
        return {"statusCode": 200, "body": {"message": "hello unknown!"}}


    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```
=== "requirements.txt"

    ```bash
    aws-lambda-powertools
    ```

Since we used powertools api_gateway event handler we don't need to know internal event structure. All we do we instantiate `ApiGatewayResolver` class and we call it in our `lambda_handler`.
Since we added route annotation as a decorator for our methods we can directly use parameters passed in request.
In order for SAM to build our package correctly we specified lambda powertools package in our requirements file. 
It is then automatically downloaded by SAM and added to lambda zip file. 

!!! tip
    If you are interested in learning how python decorators work under the hood you can follow great article from [Real Python](https://realpython.com/primer-on-python-decorators/).
## Structured Logging
In next step you have been tasked to propose production grade logging capabilities to your lambda code.
You decided to follow [structured logging approach](https://docs.aws.amazon.com/lambda/latest/operatorguide/parse-logs.html) which means that you don’t write hard-to-parse and hard-to-keep-consistent prose in your logs but that you log events that happen in a context instead. 
We want our log event to be in JSON format. This will allow us to search through it easily in CloudWatch Logs or Cloudwatch Insight.
Initial idea might be to initiate logger from standard library and use `pythonjsonlogger` library to simplify structured log creation.

=== "app.py"

    ```python hl_lines="1 4 8-13 20 26 31"
    import logging
    import os

    from pythonjsonlogger import jsonlogger

    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

    logger = logging.getLogger("APP")
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s")
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

    app = ApiGatewayResolver()


    @app.get("/hello/<name>")
    def hello_name(name):
        logger.info(f"Request from {name} received")
        return {"statusCode": 200, "body": {"message": f"hello {name}!"}}


    @app.get("/hello")
    def hello():
        logger.info(f"Request from unknown received")
        return {"statusCode": 200, "body": {"message": "hello unknown!"}}


    def lambda_handler(event, context):
        logger.debug(event)
        return app.resolve(event, context)
    ```
=== "requirements.txt"

    ```bash
    aws-lambda-powertools
    python-json-logger
    ```
So in our first attempt we create new APP Logger. We configure Log Handler, formatter and log level. Then we use this logger to log required information. We will see logs structured like that
```json
{"asctime": "2021-11-22 15:32:02,145", "levelname": "INFO", "name": "APP", "message": "Request from unknown received"}
```
instead of
```json
[INFO]  2021-11-22T15:32:02.145Z        ba3bea3d-fe3a-45db-a2ce-72e813d55b91    Request from unknown received
```

So far so good! You might also decide to add additional context into your logs.
You can take it from lambda context or event. Downside of this approach is that we would add additional complexity to ensure that you always add those specific attributes in every place.
Also, we added boilerplate code and even with additional third party library it is not straightforward. 
Can we do better? Yes! We can use powertools logger capabilities as with next example.
=== "app.py"

    ```python hl_lines="1 6 13 19 23"
    from aws_lambda_powertools import Logger
    from aws_lambda_powertools.logging import correlation_paths

    from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

    logger = Logger(service="APP")

    app = ApiGatewayResolver()


    @app.get("/hello/<name>")
    def hello_name(name):
        logger.info(f"Request from {name} received")
        return {"statusCode": 200, "body": {"message": f"hello {name}!"}}


    @app.get("/hello")
    def hello():
        logger.info(f"Request from unknown received")
        return {"statusCode": 200, "body": {"message": "hello unknown!"}}


    @logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```

We imported powertools Logger class which we created instance from in line 6. And this is basically it! By using powertools logger we have all required configuration done out of the box. 
We used `logger.inject_lambda_context` decorator to inject lambda context into every log. We also instruct logger to log correlation id taken from API Gateway and to log coming event automatically. 
Correlation id will help with tracking request between api gateway and lambda.

As a result, we should see logs with following attributes.
=== "Example Application Structured Log"
```json
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
By having structured logs like this, we might easily search and analyse them in [CloudWatch Logs Insight](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html).
=== "CloudWatch Logs Insight Example"
![CloudWatch Logs Insight Example](./media/cloudwatch_logs_insight_example.png)
## Tracing
Next task you decided to work on is to add proper tracing mechanism to your stack. Developers want to be able to analyse request traces coming through API Gateway to your Lambda. 
Together with structured logs it will be a great step to providing observability for your application!
Ideal service for this purpose is [AWS X-RAY](https://aws.amazon.com/xray/). How can we send traces from our application to the AWS X-RAY service?
Lets look first how we can achieve this with [x-ray sdk](https://docs.aws.amazon.com/xray-sdk-for-python/latest/reference/index.html) and then try to simplify it using powertools library.

=== "app.py"

    ```python hl_lines="1 12 18 19 26 27 33-39"
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
                logger.info(f"Request from {name} received")
                subsegment.put_annotation("User", name)
                return {"statusCode": 200, "body": {"message": f"hello {name}!"}}


        @app.get("/hello")
        def hello():
            with xray_recorder.in_subsegment("hello") as subsegment:
                subsegment.put_annotation("User", "unknown")
                logger.info(f"Request from unknown received")
                return {"statusCode": 200, "body": {"message": "hello unknown!"}}


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
    Description: >
        Sample SAM Template for powertools-quickstart
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

Few things happened here. Firstly, we imported required x-ray SDK classes. 
`xray_recorder` is instance of global AWS X-Ray recorder class that will begin/end segments/subsegments and send them to the X-Ray daemon.
In order to create new sub-segments we use `xray_recorder.in_subsegment` method as context manager. 
By using custom subsegments we were able to add granular sub-traces visible in our X-RAY console, separated by called method name.
Also we track lambda cold start by setting global variable outside of handler. Variable is set only during lambda runtime initialization. 
In order to enable tracing for our Lambda we need to configure it in our SAM template.yaml and add `Tracing: Active` under lambda `Properties` section.
!!! Info 
    Interested in diving deep in Context Managers and understanding benefits of using them? Follow [article](https://realpython.com/python-with-statement/) from Real Python.
!!! Info
   If you want to understand how Lambda execution environment works and why cold starts may occur, follow great [blog series](https://aws.amazon.com/blogs/compute/operating-lambda-performance-optimization-part-1/.

Can we simplify it, so we don't need to worry about adding segment or subsegments? Lets see how Powertools Lambda can help us here.

=== "app.py"

    ```python hl_lines="1 11 13 19 21 27"
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
        return {"statusCode": 200, "body": {"message": f"hello {name}!"}}


    @app.get("/hello")
    @tracer.capture_method
    def hello():
        tracer.put_annotation("User", "unknown")
        logger.info(f"Request from unknown received")
        return {"statusCode": 200, "body": {"message": "hello unknown!"}}


    @logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```
    
Thanks to using powertools tracer we have much cleaner code right now. 
In order to make our methods visible in traces we added `@tracer.capture_method` decorator to processing methods. 
We added  annotations directly in code without adding it with context manager using `tracer.put_annotation` method. 
Since we added `@tracer.capture_lambda_handler` decorator for our `lambda_handler`, powertools will automatically add information about cold start as an annotation. 
It also automatically adds lambda response as a metadata into trace so we don't need to worry about it as well.
!!! tip 
    To read about differences between annotation and metadata in traces please follow [link](https://awslabs.github.io/aws-lambda-powertools-python/latest/core/tracer/#annotations-metadata). 
As a result, you should see traces for your lambda in the X-RAY console.
=== "Example X-RAY Console View"
![Tracer utility](./media/tracer_utility_showcase_2.png)

You may also consider using **CloudWatch ServiceLens** which ties together CloudWatch metrics and logs, in addition to traces from AWS X-Ray.
It gives you a complete view of your applications and their dependencies enhancing the observability of your services. 
From there you can easily navigate to specific logs in CloudWatch Logs Insight, Metrics Dashboard or Traces in CloudWatch X-Ray traces.
=== "Example CloudWatch ServiceLens View"
![CloudWatch ServiceLens View](./media/tracer_utility_showcase_3.png)
!!! Info
    If you want to learn more about CloudWatch ServiceLens follow this [link](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ServiceLens.html)
## Custom Metrics
Last step in order to provide full observability is to add some business level metrics. 
Lambda adds low level technical metrics (Invocations, Duration, Error Count & Success Rate etc) into CloudWatch Metrics out of the box. 
You have decided to add some custom metrics in order to increase visibility into what happens with your application. 
Let's extend our application with custom metrics without Powertools to see how it works and then lets improve it with Powertools :-)

=== "app.py"

    ```python hl_lines="1 13 17-32 39 49"
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
        return {"statusCode": 200, "body": {"message": f"hello {name}!"}}


    @app.get("/hello")
    @tracer.capture_method
    def hello():
        tracer.put_annotation("User", "unknown")
        logger.info(f"Request from unknown received")
        put_metric_data(service=service, method="/hello")
        return {"statusCode": 200, "body": {"message": "hello unknown!"}}


    @logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```
=== "template.yaml"

    ```yaml hl_lines="27 28"
    AWSTemplateFormatVersion: "2010-09-09"
    Transform: AWS::Serverless-2016-10-31
    Description: >
        Sample SAM Template for powertools-quickstart
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

To add our custom metric into **CloudWatch** we added `boto3` cloudwatch client followed by creating new method `put_metric_data` that use this client to put metric in CloudWatch synchronously. We then call it in our `hello` and `hello_name` method. We slice our metrics per application name and method. This way, we can track how often specific methods are called. We also need to add additional inline policy allowing our lambda to write metrics into CloudWatch. In `template.yaml` we added `CloudWatchPutMetricPolicy` policy.
!!! Info
    We use here direct synchronous call to CloudWatch Metrics API. It will be visible in your AWS X-RAY traces as additional external call. Considering your architecture scale this approach might bring visible downsides like increased cost for metrics data collection and increased lambda latency.

Lets change our code to use Powertools Library

=== "app.py"

    ```python hl_lines="1 10 20-21 30-31 36"
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
        return {"statusCode": 200, "body": {"message": f"hello {name}!"}}


    @app.get("/hello")
    @tracer.capture_method
    def hello():
        tracer.put_annotation("User", "unknown")
        logger.info(f"Request from unknown received")
        metrics.add_dimension(name="method", value="/hello/<name>")
        metrics.add_metric(name="AppMethodsInvocations", unit=MetricUnit.Count, value=1)
        return {"statusCode": 200, "body": {"message": "hello unknown!"}}


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
We imported Powertools `Metric` class which we create metrics instance in line 10. We use it in `hello` and `hello_name` method to firstly configure dimension specific to called method and we add our custom `AppMethodsInvocations` metric. In order to ensure that our metrics are flushed to standard output and validated we added `metrics.log_metrics` decorator for our `lambda_handler`.
Powertools Metrics uses [Amazon CloudWatch Embedded Metric Format (EMF)](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html) to create custom metrics. In
general we create log with specific format. This log, once pushed to CloudWatch Log is automatically transformed to CloudWatch Metric.
!!!Info
    if you are interested in details of EMF mechanism, please follow [blog post](https://aws.amazon.com/blogs/mt/enhancing-workload-observability-using-amazon-cloudwatch-embedded-metric-format/).

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
