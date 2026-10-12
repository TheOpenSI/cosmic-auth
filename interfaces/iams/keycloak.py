"""Keycloak implementation of the IAM provider contract.

Only Keycloak is registered since Google & Microsoft are brokered *inside*
Keycloak (see ``docker/keycloak/cosmic-realm.json``). This way, the Auth service
always talks to a single OpenID Connect provider and runs a single
authorisation-code flow.

The browser must be sent to ``KEYCLOAK_PUBLIC_URL`` while the container exchanges
the code and fetches JWKS from ``KEYCLOAK_INTERNAL_URL``. The endpoints are
therefore registered explicitly instead of relying on OIDC discovery, whose
``token_endpoint``/``jwks_uri`` would resolve to a browser-only host from inside
the container.
"""


### Core modules ###
from urllib.parse import urlencode
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from fastapi.responses import RedirectResponse


### Type hints ###
from collections.abc import Mapping
from typing import (
    Any,
    ClassVar,
    Final
)


### Internal modules ###
from ...cores.configs import (
    AUTH_PUBLIC_URL,
    KEYCLOAK_CLIENT_ID,
    KEYCLOAK_CLIENT_SECRET,
    KEYCLOAK_INTERNAL_URL,
    KEYCLOAK_PUBLIC_URL,
    KEYCLOAK_REALM
)
from ..abstracts.iam import IAMProvider
from ...models.datas.claims import NormalisedClaims


_KEYCLOAK_CLIENT_NAME: Final[str] = "keycloak"
_KEYCLOAK_REALM_PATH: Final[str] = f"/realms/{KEYCLOAK_REALM}/protocol/openid-connect"


def keycloak_issuer() -> str:
    """Token issuer the ID tokens must come from (browser-facing host)."""
    return f"{KEYCLOAK_PUBLIC_URL}/realms/{KEYCLOAK_REALM}"


def keycloak_authorise_url() -> str:
    """Browser-facing authorise endpoint (public host)."""
    return f"{KEYCLOAK_PUBLIC_URL}{_KEYCLOAK_REALM_PATH}/auth"


def keycloak_token_url() -> str:
    """Container-facing token endpoint (internal host)."""
    return f"{KEYCLOAK_INTERNAL_URL}{_KEYCLOAK_REALM_PATH}/token"


def keycloak_jwks_url() -> str:
    """Container-facing JWKS endpoint (internal host)."""
    return f"{KEYCLOAK_INTERNAL_URL}{_KEYCLOAK_REALM_PATH}/certs"


def keycloak_logout_url() -> str:
    """Browser-facing RP-initiated logout endpoint (public host)."""
    return f"{KEYCLOAK_PUBLIC_URL}{_KEYCLOAK_REALM_PATH}/logout"


oauth: OAuth = OAuth()


oauth.register(
    name=_KEYCLOAK_CLIENT_NAME,
    client_id=str(KEYCLOAK_CLIENT_ID),
    client_secret=str(KEYCLOAK_CLIENT_SECRET),
    authorize_url=keycloak_authorise_url(),
    access_token_url=keycloak_token_url(),
    jwks_uri=keycloak_jwks_url(),
    client_kwargs={"scope": "openid profile email"}
)


class KeycloakIAM(IAMProvider):
    """Authlib-backed Keycloak adapter."""

    name: ClassVar[str] = _KEYCLOAK_CLIENT_NAME

    @property
    def issuer(self) -> str:
        return keycloak_issuer()

    async def authorize_redirect(
        self,
        request:        Request,
        redirect_uri:   str
    ) -> RedirectResponse:
        return await oauth.keycloak.authorize_redirect( # pyright: ignore[reportGeneralTypeIssues]
            request,
            redirect_uri
        )

    async def exchange_code(self, request: Request) -> dict[str, Any]:
        return await oauth.keycloak.authorize_access_token( # pyright: ignore[reportGeneralTypeIssues]
            request,
            claims_options={
                "iss": {
                    "essential": True,
                    "value": self.issuer
                }
            }
        )

    async def parse_id_token(self, tokens: dict[str, Any]) -> dict[str, Any]:
        return await oauth.keycloak.parse_id_token( # pyright: ignore[reportGeneralTypeIssues]
            tokens,
            nonce=None
        )

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        """Exchange a refresh token at Keycloak without a metadata round-trip."""
        async with AsyncOAuth2Client( # pyright: ignore[reportGeneralTypeIssues]
            client_id=str(KEYCLOAK_CLIENT_ID),
            client_secret=str(KEYCLOAK_CLIENT_SECRET)
        ) as client:
            return await client.refresh_token(
                keycloak_token_url(),
                refresh_token=refresh_token
            )

    async def revoke(self, refresh_token: str) -> None:
        """Best-effort end of the Keycloak session tied to this refresh token."""
        async with AsyncOAuth2Client( # pyright: ignore[reportGeneralTypeIssues]
            client_id=str(KEYCLOAK_CLIENT_ID),
            client_secret=str(KEYCLOAK_CLIENT_SECRET)
        ) as client:
            await client.post(
                keycloak_logout_url(),
                data={
                    "client_id":        str(KEYCLOAK_CLIENT_ID),
                    "client_secret":    str(KEYCLOAK_CLIENT_SECRET),
                    "refresh_token":    refresh_token
                },
            )

            return None

    def logout_redirect(
        self,
        post_logout_redirect_uri:  str,
        id_token:                  str | None = None
    ) -> str:
        params: dict[str, str] = {
            "client_id":                str(KEYCLOAK_CLIENT_ID),
            "post_logout_redirect_uri": post_logout_redirect_uri
        }

        if id_token:
            params["id_token_hint"] = id_token

        return f"{keycloak_logout_url()}?{urlencode(query=params)}"

    def callback_url(self) -> str:
        return f"{AUTH_PUBLIC_URL}/api/v1/auth/callback/{self.name}"

    def claims_from_user_info(self, user_info: Mapping[str, Any]) -> NormalisedClaims:
        """
        Map Keycloak's OIDC user info onto :class:`NormalisedClaims`.

        Roles are read from Keycloak's `realm_access.roles` claim. Google &
        Microsoft logins arrive through Keycloak identity brokering, so they are
        normalised here exactly like a native Keycloak login.
        """
        realm_access: Mapping[str, Any] = user_info.get("realm_access") or {}
        roles: list[str] = (
            list(realm_access.get("roles") or [])
            if   (realm_access)
            else ([])
        )

        return NormalisedClaims(
            provider=self.name,
            sub=str(
                user_info.get(
                    "sub",
                    ""
                )
            ),
            email=user_info.get(
                "email",
                None
            ),
            name=(
                user_info.get(
                    "name",
                    None
                )
                or
                user_info.get(
                    "preferred_username",
                    None
                )
                or
                user_info.get(
                    "email",
                    None
                )
            ),
            roles=roles
        )
