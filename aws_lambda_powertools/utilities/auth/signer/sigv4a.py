"""Sign HTTP requests with Signature Version 4A, valid across a set of regions. Needs the ``awscrt`` package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities.auth.signer.exceptions import SignerConfigError
from aws_lambda_powertools.utilities.auth.signer.sigv4 import _S3_SERVICES, SigV4Signer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from botocore.auth import BaseSigner
    from botocore.credentials import Credentials
    from botocore.session import Session

__all__ = ["SigV4aSigner"]


class SigV4aSigner(SigV4Signer):
    """Sign HTTP requests with AWS Signature Version 4A (ECDSA), for services that accept one
    signature across several regions, such as S3 Multi-Region Access Points.

    Install the extra: ``pip install "aws-lambda-powertools[auth-sigv4a]"``. The Lambda runtime
    does not ship ``awscrt``, so package it with your function.

    Parameters
    ----------
    service : str
        Signing name of the target service.
    region_set : str | Sequence[str]
        Regions the signature is valid for, for example ``["us-east-1", "eu-west-1"]``. ``"*"`` means every region.
    credentials, session
        Same as :class:`SigV4Signer`.
    """

    def __init__(
        self,
        service: str,
        *,
        region_set: str | Sequence[str] = "*",
        credentials: Credentials | None = None,
        session: Session | None = None,
    ) -> None:
        try:
            import botocore.auth  # noqa: F401  botocore wires the CRT signers only after its own auth module loads
            import botocore.crt.auth  # noqa: F401
        except ImportError as exc:
            raise SignerConfigError(
                "SigV4a needs the awscrt package; install aws-lambda-powertools[auth-sigv4a]",
            ) from exc
        self.region_set = region_set if isinstance(region_set, str) else ",".join(region_set)
        if not self.region_set:
            raise SignerConfigError("region_set cannot be empty; use '*' for every region")
        super().__init__(service, region=self.region_set, credentials=credentials, session=session)

    def _auth(self) -> BaseSigner:
        from botocore.crt.auth import CrtS3SigV4AsymAuth, CrtSigV4AsymAuth

        auth_class = CrtS3SigV4AsymAuth if self.service in _S3_SERVICES else CrtSigV4AsymAuth
        return auth_class(self._credentials, self.service, self.region_set)
