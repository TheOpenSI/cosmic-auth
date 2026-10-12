"""Google as a direct identity provider (not used today).

Google is configured as an identity provider *inside* Keycloak and the realm
export wires the broker callback
(``http://localhost:8080/realms/cosmic/broker/google/endpoint``), so the Auth
service never talks to Google directly. Implement the flow methods here if a
direct Google integration is ever needed.
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
from ...models.datas.claims import NormalisedClaims
from ..abstracts.idp import IdentityProvider


_BROKERED: str = (
    "Google is brokered by Keycloak; start the flow at GET /api/v1/auth/login."
)


class GoogleIdP(IdentityProvider):
    """Keycloak-brokered Google identity provider."""

    name: ClassVar[str] = "google"

    @property
    def broker_alias(self) -> str:
        return "google"

    async def authorize_redirect(
        self,
        request:        Request,
        redirect_uri:   str
    ) -> RedirectResponse:
        raise NotImplementedError(_BROKERED)

    async def exchange_code(self, request: Request) -> dict[str, Any]:
        raise NotImplementedError(_BROKERED)

    def claims_from_user_info(self, user_info: Mapping[str, Any]) -> NormalisedClaims:
        raise NotImplementedError(_BROKERED)
