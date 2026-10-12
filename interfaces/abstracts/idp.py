"""Contract for a single identity provider (Google, Microsoft, ...).

Only the pieces a *direct* provider integration needs are declared here. Today
Google and Microsoft are configured as identity providers *inside* Keycloak, so
the Auth service never talks to them directly; see `interfaces/idps/` for the
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
    """Identity provider operations used by the Auth service."""

    name: ClassVar[str]

    @property
    @abstractmethod
    def broker_alias(self) -> str:
        """Keycloak identity-provider alias this IdP is brokered under."""

    @abstractmethod
    async def authorize_redirect(
        self,
        request:        Request,
        redirect_uri:   str
    ) -> RedirectResponse:
        """Send the browser straight to the provider (direct flow)."""

    @abstractmethod
    async def exchange_code(self, request: Request) -> dict[str, Any]:
        """Exchange the authorization code straight with the provider."""

    @abstractmethod
    def claims_from_user_info(self, user_info: Mapping[str, Any]) -> NormalisedClaims:
        """Map the provider's user info onto the single CoSMIC claim shape."""
