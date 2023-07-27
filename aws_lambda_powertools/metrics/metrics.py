# NOTE: keeps for compatibility
from aws_lambda_powertools.metrics.provider.amazon_cloudwatch_emf import (
    EphemeralMetrics,
    Metrics,
)

__all__ = ["Metrics", "EphemeralMetrics"]
