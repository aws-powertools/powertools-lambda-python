from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

metrics = Metrics()  # Sets metric namespace and service via env var
# OR
metrics = Metrics(
    namespace="ServerlessAirline", service="orders"
)  # Sets metric namespace, and service as a metric dimension
