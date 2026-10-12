"""
Contract between the Auth BFF and an Identity and Access Management (IAM)
provider.


Only the pieces that the framework actually needs are declared here. This way,
when a new provider is addded, we can simply inherit this class plus registering
it in :func:`interfaces.iams.get_iam_provider`. This way, no route changes will
ever be required anymore.
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


class IAMProvider(ABC):
    """IAM operations used by the Auth BFF."""

    name: ClassVar[str]

    @property
    @abstractmethod
    def issuer(self) -> str:
        """Issuer the provider's ID tokens must come from."""

    @abstractmethod
    async def authorise_redirect(
        self,
        request:        Request,
        redirect_uri:   str
    ) -> RedirectResponse:
        """Send the browser to the provider's authorise endpoint."""

    @abstractmethod
    async def exchange_code(
        self,
        request: Request
    ) -> dict[str, Any]:
        """Exchange the authorisation code for a token set (issuer verified)."""

    @abstractmethod
    async def parse_id_token(
        self,
        tokens: dict[str, Any]
    ) -> dict[str, Any]:
        """Read the user info back out of an ID token."""

    @abstractmethod
    async def refresh(
        self,
        refresh_token: str
    ) -> dict[str, Any]:
        """Exchange a refresh token for a fresh token set."""

    @abstractmethod
    async def revoke(
        self,
        refresh_token: str
    ) -> None:
        """Best-effort end of the provider session behind that refresh token."""

    @abstractmethod
    def logout_redirect(
        self,
        post_logout_redirect_uri:  str,
        id_token:                  str | None = None
    ) -> str:
        """Full RP-initiated logout URL with query parameters included."""

    @abstractmethod
    def callback_url(self) -> str:
        """This service's callback URL, which must match the provider console."""

    @abstractmethod
    def claims_from_user_info(
        self,
        user_info: Mapping[str, Any]
    ) -> NormalisedClaims:
        """Map provider user info onto the single CoSMIC claim shape."""
