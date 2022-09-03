# import pytest

# from tests.e2e.lambda_layer.infrastructure import build_layer
# from tests.e2e.utils.infrastructure import call_once


# # @pytest.fixture(scope="session")
# # def lambda_layer_arn(lambda_layer_deployment: dict):
# #     yield lambda_layer_deployment.get("LayerArn")


# @pytest.fixture(scope="session", autouse=True)
# def lambda_layer_deployment(tmp_path_factory: pytest.TempPathFactory, worker_id: str):
#     """Setup and teardown logic for E2E test infrastructure

#     Parameters
#     ----------
#     tmp_path_factory : pytest.TempPathFactory
#         pytest temporary path factory to discover shared tmp when multiple CPU processes are spun up
#     worker_id : str
#         pytest-xdist worker identification to detect whether parallelization is enabled

#     Yields
#     ------
#     Dict[str, str]
#         CloudFormation Outputs from deployed infrastructure
#     """
#     yield from call_once(
#         callable=build_layer,
#         tmp_path_factory=tmp_path_factory,
#         worker_id=worker_id,
#     )
