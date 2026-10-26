"""
Authentik implementation of the IAM provider contract.

Authentik is the IAM this platform intends to move to, but it is not wired up
yet. For now, only the Keycloak adapter is implemented. This module exists so the
seam is explicit and the future adapter has an obvious home. See
:class:`interfaces.abstracts.iam.IAMProvider` for the contract it must satisfy.
"""

### Core modules ###
from fastapi import Request
from fastapi.responses import RedirectResponse


### Type hints ###
from collections.abc import (
    Collection,
    Mapping
)
from typing import (
    Any,
    ClassVar,
    override
)


### Internal modules ###
from ..abstracts.iam import IAMProvider
from ...models.datas.claims import NormalisedClaims


_NOT_IMPLEMENTED: str = "The Authentik IAM provider is not implemented yet. Keep IAM_PROVIDER=keycloak for now."


class AuthentikIAM(IAMProvider):
    """Placeholder for the planned Authentik adapter."""

    name: ClassVar[str] = "authentik"

    @property
    @override
    def issuer(self) -> str:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    async def authorise_redirect(
        self,
        request:        Request,
        redirect_uri:   str
    ) -> RedirectResponse:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    async def exchange_code(
        self,
        request: Request
    ) -> dict[str, Any]:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    async def parse_id_token(
        self,
        tokens: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    async def refresh(
        self,
        refresh_token: str
    ) -> dict[str, Any]:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    async def revoke(
        self,
        refresh_token: str
    ) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    async def update_user(
        self,
        subject: str,
        *,
        email:           str | None = None,
        name:            str | None = None,
        role:            str | None = None,
        role_desc:       str | None = None,
        managed_roles:   Collection[str] = ()
    ) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    async def delete_user(
        self,
        subject: str
    ) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    async def create_role(
        self,
        name: str,
        desc: str | None = None
    ) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    async def update_role(
        self,
        current_name:   str,
        *,
        name:           str | None = None,
        desc:           str | None = None
    ) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    async def delete_role(
        self,
        name: str
    ) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    def logout_redirect(
        self,
        post_logout_redirect_uri:  str,
        id_token:                  str | None = None
    ) -> str:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    def callback_url(self) -> str:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @override
    def claims_from_user_info(
        self,
        user_info: Mapping[str, Any]
    ) -> NormalisedClaims:
        raise NotImplementedError(_NOT_IMPLEMENTED)
