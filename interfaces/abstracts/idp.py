"""
Contract for a single identity provider (IdP) such as Google, Microsoft, etc.


Only the pieces a *direct* provider integration needs are declared here. However,
due to our way of setting up IdPs, all of them are configured as IdP *inside*
Keycloak (unless they didn't support it, yet). This way, the Auth micro-service
never need to talk to them directly. See `interfaces/idps/` for the
implementations, which document the Keycloak broker callback instead and are the
place to wire in a direct flow if that is ever needed.
"""


### Core modules ###
from abc import (
    ABC,
    abstractmethod
)


### Type hints ###
from collections.abc import Mapping
from typing import (
    Any,
    ClassVar
)
from fastapi import Request
from fastapi.responses import RedirectResponse


### Internal modules ###
from ...models.datas.claims import NormalisedClaims


class IdentityProvider(ABC):
    """IdP operations used by the Auth service."""

    name: ClassVar[str]

    @property
    @abstractmethod
    def broker_alias(self) -> str:
        """Keycloak IdP alias value (on admin console) for brokered IdP."""

    @abstractmethod
    async def authorise_redirect(
        self,
        request:        Request,
        redirect_uri:   str
    ) -> RedirectResponse:
        """Send the browser straight to the provider (direct flow)."""

    @abstractmethod
    async def exchange_code(
        self,
        request: Request
    ) -> dict[str, Any]:
        """Exchange the authorisation code straight with the provider."""

    @abstractmethod
    def claims_from_user_info(
        self,
        user_info: Mapping[str, Any]
    ) -> NormalisedClaims:
        """Map the provider's user info onto the single CoSMIC claim shape."""
