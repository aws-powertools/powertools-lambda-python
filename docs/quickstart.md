---
title: QuickStart
description: Powertools introduction
---
Quickstart introducing core Powertools functionalities.


## Installation 
With [SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) installed, you can follow this Quickstart step by step or you can build a project with the final Quickstart code you can play with.
If you want to follow it all along, create a new empty project.
=== "shell"
```bash
sam init --runtime python3.9 --dependency-manager pip --app-template hello-world --name powertools-quickstart
```
If you want to play with the final code, then you can download it from [aws-samples](https://github.com/aws-samples/cookiecutter-aws-sam-python) github repository.
=== "shell"
```bash
sam init --location https://github.com/aws-samples/cookiecutter-aws-sam-python
```
### Configuration
If you decide to deploy code from Quickstart make sure to [set up your AWS credentials](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-set-up-credentials.html).

### Code example
In the `powertools-quickstart` folder, we will modify the following files:

* **app.py** - Application code.
* **template.yaml** - AWS infrastructure configuration using SAM.
* **requirements.txt** - List of extra Python packages needed.

Let's configure our base application to look like the following code snippet.
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
Our lambda code consists of the `lambda_handler` method that is invoked by the API and the `hello` method that returns the results to the API gateway and is invoked by the handler itself.
The SAM model configures API Gateway, which redirects traffic to Lambda for one path only: `hello`.
!!! Warning 
    For simplicity, we do not set up authentication and authorisation in the example!
### Run your code
At each point, you have two ways to run your code. Locally and within your AWS account. Given that we use SAM, the two methods are just as simple.
#### Local test
SAM allows you to execute a server-less application locally. Perform the next command in a shell.
```bash
> sam build && sam local start-api
...
2021-11-26 17:43:08  * Running on http://127.0.0.1:3000/ (Press CTRL+C to quit)
```
As a result API endpoint will be exposed for you. You can trigger it with the 'curl' command like in the following example.
```bash
> curl http://127.0.0.1:3000/hello
{"statusCode":200,"body":{"message":"hello unknown!"}}%
```
!!! info
    To learn more about local testing, please visit [SAM local testing](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html) page
!!! warning
    **Powertools Tracer** requires X-RAY service to work. This means that you will not see the traces locally. Roll it out on your AWS account instead.
#### Remote test
You may also deploy your application into AWS Account by issuing the following command.
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
This command will build a package and deploy it to your AWS Account. In the output section, you will find the API Url against which you can launch requests. Now, you can trigger your endpoints.
```bash
> curl https://1234567890.execute-api.eu-central-1.amazonaws.com/Prod/hello
{"statusCode":200,"body":{"message":"hello unknown!"}}%
```
!!! Info
    For more details on the SAM deployment mechanism, see [link](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-deploy.html).

## API Gateway router
Let's say we want to have another method that acts like an echo server. It takes user input (username) and output it to the caller. We would need to create an API with an URL path /hello/<name>, where the name string is the input from the user.
One approach would be to create another lambda using the required method and set up the API gateway to call it.
=== "app_name.py"

    ```python
    def hello_name(name):
        return {"statusCode": 200, "body": {"message": f"hello {name}!"}}


    def lambda_handler(event, context):
        name = event["pathParameters"]["name"]
        return hello_name(name)
    ```

=== "template.yaml"

    ```yaml hl_lines="21-32"
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

This way certainly works for simple use-case. But what happens if your application gets bigger and we need to cover numerous URL paths and HTTP methods for them? If that is the case, we should:

* Add a new lambda handler with business logic for each new URL path and HTTP method used.
* Add a new Lambda configuration to a SAM template file to map the lambda function to the required path and HTTP URL method.

This could result in a number of similar lambda files and large SAM configuration file with similar configuration sections. 
In this case where we see that the addition of new URL paths lead to the boilerplate code, we should lean towards the routing approach.
!!! Info
    If you want a more detailed explanation of these two approaches, we have explained the considerations [here](.. /core/event_handler/api_gateway/#considerations)
The simple code might look similar to the following code snippet.
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

    ```yaml hl_lines="15-25"
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

* We added two `hello_name` and `hello` methods (line 1-7). 
* We added the `Router` class which allows us to record the method that should be called when the specific request arrives (line 10-23). 
* We created the instance and added the configuration with the mapping of the processing methods and the http query method (line 26-28). 
* In the lambda handler, we call router instance `get` method to retrieve a reference to the processing method (`hello` or `hello_name`) that will process the query (line 34). 
* Finally, we run this method and send the results back to API Gateway (line 35).

This approach allows us to simplify the configuration of our infrastructure since we have added all Gateway API paths in the `HelloWorldFunction` event section. We need to understand the internal structure of the API Gateway request events though, to deduce the requested path, http method and path parameters. This requires us to put additional engineering effort to provide proper error handling. Also, if we decide to use another event source for our lambda, since we are highly coupled it would require rewriting of our lambda handler to get the information we need.
Let's see how we can improve it with Powertools.

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

Powertools provides an `ApiGatewayResolver` class, which helps you understand the structure, no need to look it up.
We can also directly use the parameters passed in the request now, because we have added the route annotation as the decorator for our methods.
For SAM to build our package correctly, we have specified lambda powertools package in our `requirement.txt` file. 

!!! tip
    If you'd like to learn how python decorators work under the hood, you can follow [Real Python](https://realpython.com/primer-on-python-decorators/)'s article.
## Structured Logging
In the next step, you have been given the task of proposing production quality logging capabilities to your lambda code.
We want our log event to be in a JSON format. Also, You decided to follow [structured logging approach](https://docs.aws.amazon.com/lambda/latest/operatorguide/parse-logs.html). In a result, we expect easy to search, consistent logs containing enough context and data to analyse the status of our system. We can take advantage of CloudWatch Logs and Cloudwatch Insight for this purpose.

The first option could be to use a python logger in combination with the `pythonjsonlogger` library for simple structured logging.

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
On the first try, we did a couple of steps to set up our logging:

* Create an application logger called `APP`.
* Configure handler and formatter.
* Set log level.

After that, we use this logger in our application code to record the required information. We see logs structured as follows:
```json
{"asctime": "2021-11-22 15:32:02,145", "levelname": "INFO", "name": "APP", "message": "Request from unknown received"}
```
instead of
```json
[INFO]  2021-11-22T15:32:02.145Z        ba3bea3d-fe3a-45db-a2ce-72e813d55b91    Request from unknown received
```

So far, so good! To make things easier, we want to add extra context to the logs. We can extract it from a lambda context or an event passed to lambda handler at the time of invocation. We have to make sure that we always add those specific attributes wherever a logger is used. Can we ensure that the required attributes are added automatically on our behalf without having to move them around? Yes! Powertools Logger to the rescue :-)
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

We added powertools logger in line 6 and all the configuration is done. 
We also used `logger.inject_lambda_context` decorator to inject lambda context into every log. We instruct logger to log correlation id taken from API Gateway and event automatically. Because powertools library adds a correlation identifier to each log, we can easily correlate all the logs generated for a specific request.

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
The next task we have chosen to work on is to add an appropriate tracking mechanism to your stack. Developers want to be able to analyze traces of queries that pass via the API gateway to your Lambda. 
With structured logs, it will be an important step to provide the observability of your application!
The AWS service that has these capabilities is [AWS X-RAY](https://aws.amazon.com/xray/). How do we send application trace to the AWS X-RAY service then?
Let's first explore how we can achieve this with [x-ray SDK](https://docs.aws.amazon.com/xray-sdk-for-python/latest/reference/index.html), and then try to simplify it with the Powertools library.

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

A lot has happened here. First, we imported required X-ray SDK classes. 
`xray_recorder` is a global AWS X-ray recorder class instance that starts/ends segments/sub-segments and sends them to the X-ray daemon.
To build new sub-segments, we use `xray_recorder.in_subsegment` method as a context manager. 
Using customized sub-segments, we were able to add visible granular sub-traces into our X-ray, separated by the method name.
Also, we track lambda cold start by setting global variable outside of a handler. The variable is defined only upon lambda initialization. This information provides an overview of how often the runtime is reused by lambda invoked, which directly impacts perceived lambda performance and latency.

To allow the tracking of our Lambda, we need to set it up in our SAM template and add `Tracing: Active` under lambda `Properties` section.
!!! Info 
    Want to know more about context managers and understand the benefits of using them? Follow [article](https://realpython.com/python-with-statement/) from Real Python.
!!! Info
    If you want to understand how the Lambda execution environment works and why cold starts can occur, follow [blog series](https://aws.amazon.com/blogs/compute/operating-lambda-performance-optimization-part-1/).
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
    
Thanks to the help of powertools tracer we have much cleaner code right now. 
To make our methods visible in the traces, we added `@tracer.capture_method` decorator to the processing methods. 
We added annotations directly in the code without adding it with the context handler using the `tracer.put_annotation` method. 
Since we added the `@tracer.capture_lambda_handler` decorator for our `lambda_handler`, powertools automatically adds cold start information as an annotation. 
It also automatically adds lambda response as a metadata into trace, so we don't need to worry about it as well.
!!! tip 
    For differences between annotations and metadata in traces, please follow [link](https://awslabs.github.io/aws-lambda-powertools-python/latest/core/tracer/#annotations-metadata). 
Therefore, you should see traces of your lambda in the X-ray console.
=== "Example X-RAY Console View"
![Tracer utility](./media/tracer_utility_showcase_2.png)

You may also consider using **CloudWatch ServiceLens** which links the CloudWatch metrics and logs, in addition to traces from the AWS X-Ray.
It gives you a complete view of your apps and their dependencies, making your services more observable. 
From here, you can easily browse to specific logs in CloudWatch Logs Insight, Metrics Dashboard or Traces in CloudWatch X-Ray traces.
=== "Example CloudWatch ServiceLens View"
![CloudWatch ServiceLens View](./media/tracer_utility_showcase_3.png)
!!! Info
    For more information on CloudWatch ServiceLens, please visit [link](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ServiceLens.html).
## Custom Metrics
The final step to provide complete observability is to add certain measures at the business level. 
Lambda adds low-level technical metrics (such as Invocations, Duration, Error Count & Success Rate) to the CloudWatch metrics out of the box. 
Let's expand our application with custom metrics without Powertools to see how it works, then let's upgrade it with Powertools:-)

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

To add our custom metric in **CloudWatch** we added `boto3` cloudwatch client followed by creation of the new `put_metric_data` method that uses this client to put the metric in CloudWatch synchronously. We call it in our method `hello` and `hello_name`. We divide our measures by type of application and method. Thus, we can follow the frequency at which specific methods are called. We also need to add additional inline policy allowing our lambda to write metrics in the CloudWatch. In `template.yaml` we added `CloudWatchPutMetricPolicy` policy.
!!! Info
    We use direct synchronous call to CloudWatch Metrics API. It will be visible in your AWS X-RAY traces as additional external call. Given your architecture scale, this approach might lead to disadvantages such as increased cost of measuring data collection and increased lambda latency.

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
We imported Powertools `Metric` class which we create metrics instance in line 10. We use it in the `hello` and `hello_name` method to first configure the dimension specific to the called method and we add our custom `AppMethodsInvocations` metric. To ensure that our metrics are aligned with the standard output and validated, we have added the metrics.log_metrics designer for our lambda_handler'.
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
