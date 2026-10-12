"""Authentik IAM provider (planned).

Authentik is the IAM this platform intends to move to, but it is not wired up
yet: only the Keycloak adapter is implemented. This module exists so the seam is
explicit and the future adapter has an obvious home - see
:class:`interfaces.abstracts.iam.IAMProvider` for the contract it must satisfy.
"""

### Core modules ###
from fastapi import Request
from fastapi.responses import RedirectResponse


### Type hints ###
from collections.abc import Mapping
from typing import (
    Any,
    ClassVar
)


### Internal modules ###
from ..abstracts.iam import IAMProvider
from ...models.datas.claims import NormalisedClaims


_NOT_IMPLEMENTED: str = (
    "The Authentik IAM provider is not implemented yet. "
    "Keep IAM_PROVIDER=keycloak for now."
)


class AuthentikIAM(IAMProvider):
    """Placeholder for the planned Authentik adapter."""

    name: ClassVar[str] = "authentik"

    @property
    def issuer(self) -> str:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    async def authorize_redirect(
        self,
        request:        Request,
        redirect_uri:   str
    ) -> RedirectResponse:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    async def exchange_code(self, request: Request) -> dict[str, Any]:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    async def parse_id_token(self, tokens: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    async def revoke(self, refresh_token: str) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def logout_redirect(
        self,
        post_logout_redirect_uri:  str,
        id_token:                  str | None = None
    ) -> str:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def callback_url(self) -> str:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def claims_from_user_info(self, user_info: Mapping[str, Any]) -> NormalisedClaims:
        raise NotImplementedError(_NOT_IMPLEMENTED)
