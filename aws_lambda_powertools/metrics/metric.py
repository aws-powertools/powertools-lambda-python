# NOTE: prevents circular inheritance import
from aws_lambda_powertools.metrics.base import SingleMetric, single_metric

__all__ = ["SingleMetric", "single_metric"]
