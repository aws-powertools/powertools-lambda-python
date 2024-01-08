<!-- markdownlint-disable MD041 MD043 -->
Behind the scenes, the [data validation](api_gateway.md#data-validation) feature auto-generates an OpenAPI specification from your routes and type annotations. You can use [Swagger UI](https://swagger.io/tools/swagger-ui/){target="_blank" rel="nofollow"} to visualize and interact with your newly auto-documented API.

There are some important **caveats** that you should know before enabling it:

| Caveat                                           | Description                                                                                                                                                                                            |
| ------------------------------------------------ |--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Swagger UI is **publicly accessible by default** | When using `enable_swagger` method, you can [protect sensitive API endpoints by implementing a custom middleware](api_gateway.md#customizing-swagger-ui) using your preferred authorization mechanism. |
| **No micro-functions support** yet               | Swagger UI is enabled on a per resolver instance which will limit its accuracy here.                                                                                                                   |
| You need to expose **new routes**                | You'll need to expose the following paths to Lambda: `/swagger`, `/swagger.css`, `/swagger.js`; ignore if you're routing all paths already.                                                            |
