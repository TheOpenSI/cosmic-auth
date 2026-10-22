"""
Keycloak implementation of the IAM provider contract.


Only Keycloak is registered since Google & Microsoft are brokered *inside* it
(see ``docker/keycloak/cosmic-realm.json``). This way, the Auth micro-service
always talks to a single OpenID Connect provider and runs a single authorisation
code flow.

The browser must be sent to ``KEYCLOAK_PUBLIC_URL`` while the container exchanges
the code and fetches JWKS from ``KEYCLOAK_INTERNAL_URL``. The endpoints are
therefore registered explicitly instead of relying on OIDC discovery, whose
``token_endpoint``/``jwks_uri`` would resolve to a browser-only host from inside
the container.
"""


### Core modules ###
from base64 import urlsafe_b64decode
from binascii import Error
from http import HTTPStatus
from json import loads
from urllib.parse import (
    quote,
    urlencode
)
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.integrations.starlette_client import OAuth
from fastapi import (
    HTTPException,
    Request,
    status
)
from fastapi.responses import RedirectResponse
from httpx import (
    AsyncClient,
    Response as HTTPXResponse
)


### Type hints ###
from collections.abc import (
    Collection,
    Mapping
)
from typing import (
    Any,
    ClassVar,
    Final,
    override
)


### Internal modules ###
from ...cores.configs import (
    AUTH_PUBLIC_URL,
    KEYCLOAK_CLIENT_ID,
    KEYCLOAK_CLIENT_SECRET,
    KEYCLOAK_INTERNAL_URL,
    KEYCLOAK_PUBLIC_URL,
    KEYCLOAK_REALM,
    KEYCLOAK_SERVICE_ACCOUNT_CLIENT_ID,
    KEYCLOAK_SERVICE_ACCOUNT_CLIENT_SECRET
)
from ..abstracts.iam import IAMProvider
from ...models.datas.claims import NormalisedClaims


_KEYCLOAK_CLIENT_NAME:  Final[str] = "keycloak"
_KEYCLOAK_REALM_PATH:   Final[str] = f"/realms/{KEYCLOAK_REALM}/protocol/openid-connect"
_KEYCLOAK_ADMIN_TIMEOUT: Final[float] = 15.0


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


def keycloak_service_account_token_url() -> str:
    """Container-facing token endpoint for the Admin REST service account."""
    return f"{KEYCLOAK_INTERNAL_URL}{_KEYCLOAK_REALM_PATH}/token"


def _keycloak_admin_url(path: str) -> str:
    return f"{KEYCLOAK_INTERNAL_URL}/admin/realms/{KEYCLOAK_REALM}{path}"


def _status_label(status_code: int) -> str:
    try:
        return f"{status_code} - {HTTPStatus(status_code).phrase}"

    except ValueError:
        return str(status_code)


def _error_message(
    response: HTTPXResponse,
    fallback: str
) -> str:
    try:
        body: Any = response.json()

    except ValueError:
        body = None

    if isinstance(
        body,
        dict
    ):
        for key in (
            "errorMessage",
            "error_description",
            "error",
            "message"
        ):
            value: Any = body.get(key)

            if value is None:
                continue

            text: str = str(value).strip()

            if text:
                return text

    return fallback


def _admin_error(
    response: HTTPXResponse,
    fallback: str
) -> HTTPException:
    status_code: int = response.status_code
    message: str = _error_message(
        response=response,
        fallback=fallback
    )

    # The service account is our own infrastructure credential. A 401/403 from
    # Keycloak means the deployment is misconfigured, not that the caller sent
    # bad credentials, so surface it as a server-side failure.
    if status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN
    ):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = f"Keycloak service account is not authorised: {message}"

    return HTTPException(
        status_code=status_code,
        detail={
            "status": _status_label(status_code),
            "message": message
        }
    )


def _name_parts(name: str) -> tuple[str, str]:
    """Split CoSMIC's single `name` field into Keycloak's first/last names."""
    parts: list[str] = name.strip().split(
        sep=None,
        maxsplit=1
    )

    if not parts:
        return ("", "")

    return (
        parts[0],
        (
            parts[1]
            if len(parts) > 1
            else ""
        )
    )


def _role_key(name: Any) -> str:
    return (
        str(name).strip().lower()
        if name is not None
        else ""
    )


def _access_token_claims(tokens: dict[str, Any]) -> dict[str, Any]:
    """
    Read the claims Keycloak puts on its access token.

    Keycloak keeps realm roles under ``realm_access`` on the access token. The
    ID token/user info payload does not always include that claim, so merge it in
    before normalising the CoSMIC claims.
    """
    access_token: str | None = tokens.get("access_token")

    if not isinstance(access_token, str):
        return {}

    try:
        (
            _,
            payload,
            _
        ) = access_token.split(".")

        payload += "=" * (-len(payload) % 4)
        claims: Any = loads(s=urlsafe_b64decode(s=payload.encode("ascii")))

    except (
        ValueError,
        UnicodeDecodeError,
        Error
    ):
        return {}

    return (
        claims
        if   (isinstance(claims, dict))
        else ({})
    )


def _merge_access_token_claims(
    user_info: Mapping[str, Any],
    tokens: dict[str, Any]
) -> dict[str, Any]:
    merged:         dict[str, Any] = dict(user_info)
    access_claims:  dict[str, Any] = _access_token_claims(tokens=tokens)

    if (
        not merged.get(
            "realm_access",
            None
        )
        and access_claims.get(
            "realm_access",
            None
        )
    ):
        merged["realm_access"] = access_claims["realm_access"]

    for claim in (
        "sub",
        "email",
        "name",
        "preferred_username"
    ):
        if (
            not merged.get(
                claim,
                None
            )
            and access_claims.get(
                claim,
                None
            )
        ):
            merged[claim] = access_claims[claim]

    return merged


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
    """Keycloak adapter (backed by ``Authlib``)."""

    name: ClassVar[str] = _KEYCLOAK_CLIENT_NAME

    @property
    @override
    def issuer(self) -> str:
        return keycloak_issuer()

    @override
    async def authorise_redirect(
        self,
        request:        Request,
        redirect_uri:   str
    ) -> RedirectResponse:
        return await oauth.keycloak.authorize_redirect(
            request,
            redirect_uri
        )

    @override
    async def exchange_code(
        self,
        request: Request
    ) -> dict[str, Any]:
        tokens: dict[str, Any] = await oauth.keycloak.authorize_access_token(
            request,
            claims_options={
                "iss": {
                    "essential": True,
                    "value": self.issuer
                }
            }
        )
        tokens["userinfo"] = _merge_access_token_claims(
            user_info=tokens.get("userinfo") or {},
            tokens=tokens
        )

        return tokens

    @override
    async def parse_id_token(
        self,
        tokens: dict[str, Any]
    ) -> dict[str, Any]:
        user_info: dict[str, Any] = await oauth.keycloak.parse_id_token(
            tokens,
            nonce=None
        )

        return _merge_access_token_claims(
            user_info=user_info,
            tokens=tokens
        )

    @override
    async def refresh(
        self,
        refresh_token: str
    ) -> dict[str, Any]:
        """Exchange a refresh token at Keycloak without a metadata round-trip."""
        async with AsyncOAuth2Client( # pyright: ignore[reportGeneralTypeIssues]
            client_id=str(KEYCLOAK_CLIENT_ID),
            client_secret=str(KEYCLOAK_CLIENT_SECRET)
        ) as client:
            return await client.refresh_token(
                keycloak_token_url(),
                refresh_token=refresh_token
            )

    @override
    async def revoke(
        self,
        refresh_token: str
    ) -> None:
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

    async def _admin_token(
        self,
        client: AsyncClient
    ) -> str:
        """Get a Keycloak Admin REST token for the dedicated service account."""
        if not KEYCLOAK_SERVICE_ACCOUNT_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": _status_label(status.HTTP_500_INTERNAL_SERVER_ERROR),
                    "message": "Keycloak service account secret is not configured."
                }
            )

        response: HTTPXResponse = await client.post(
            url=keycloak_service_account_token_url(),
            data={
                "grant_type":       "client_credentials",
                "client_id":        str(KEYCLOAK_SERVICE_ACCOUNT_CLIENT_ID),
                "client_secret":    str(KEYCLOAK_SERVICE_ACCOUNT_CLIENT_SECRET)
            }
        )

        if response.is_error:
            raise _admin_error(
                response=response,
                fallback="Keycloak service account authentication failed."
            )

        payload: Any = response.json()
        token: Any = (
            payload.get("access_token")
            if isinstance(payload, dict)
            else None
        )

        if not isinstance(token, str) or not token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": _status_label(status.HTTP_500_INTERNAL_SERVER_ERROR),
                    "message": "Keycloak did not return a service-account access token."
                }
            )

        return token

    @staticmethod
    def _admin_headers(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    async def _admin_get_user(
        self,
        client:     AsyncClient,
        token:      str,
        subject:    str
    ) -> dict[str, Any] | None:
        response: HTTPXResponse = await client.get(
            url=_keycloak_admin_url(f"/users/{quote(subject, safe='')}"),
            headers=self._admin_headers(token=token)
        )

        if response.status_code == status.HTTP_404_NOT_FOUND:
            return None

        if response.is_error:
            raise _admin_error(
                response=response,
                fallback="Could not read the Keycloak user."
            )

        payload: Any = response.json()

        return (
            payload
            if isinstance(payload, dict)
            else None
        )

    async def _admin_find_users_by_email(
        self,
        client: AsyncClient,
        token:  str,
        email:  str
    ) -> list[dict[str, Any]]:
        response: HTTPXResponse = await client.get(
            url=_keycloak_admin_url("/users"),
            headers=self._admin_headers(token=token),
            params={
                "email": email,
                "exact": "true"
            }
        )

        if response.is_error:
            raise _admin_error(
                response=response,
                fallback="Could not check the Keycloak email uniqueness."
            )

        payload: Any = response.json()

        return (
            payload
            if isinstance(payload, list)
            else []
        )

    async def _admin_get_role(
        self,
        client: AsyncClient,
        token:  str,
        name:   str
    ) -> dict[str, Any] | None:
        response: HTTPXResponse = await client.get(
            url=_keycloak_admin_url(f"/roles/{quote(name, safe='')}"),
            headers=self._admin_headers(token=token)
        )

        if response.status_code == status.HTTP_404_NOT_FOUND:
            return None

        if response.is_error:
            raise _admin_error(
                response=response,
                fallback=f"Could not read the Keycloak role [{name}]."
            )

        payload: Any = response.json()

        return (
            payload
            if isinstance(payload, dict)
            else None
        )

    async def _admin_ensure_role(
        self,
        client: AsyncClient,
        token:  str,
        name:   str,
        desc:   str | None = None
    ) -> dict[str, Any]:
        """Return the realm role, creating/synchronising it when needed."""
        role: dict[str, Any] | None = await self._admin_get_role(
            client=client,
            token=token,
            name=name
        )

        if role is None:
            response: HTTPXResponse = await client.post(
                url=_keycloak_admin_url("/roles"),
                headers=self._admin_headers(token=token),
                json={
                    "name":         name,
                    "description":  desc
                }
            )

            # Someone else may have created it between the GET and the POST.
            if response.status_code != status.HTTP_409_CONFLICT:
                if response.is_error:
                    raise _admin_error(
                        response=response,
                        fallback=f"Could not create the Keycloak role [{name}]."
                    )

            role = await self._admin_get_role(
                client=client,
                token=token,
                name=name
            )

            if role is None:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail={
                        "status": _status_label(status.HTTP_502_BAD_GATEWAY),
                        "message": f"Keycloak role [{name}] could not be created or read back."
                    }
                )

        if (
            desc is not None
            and
            role.get("description") != desc
        ):
            response = await client.put(
                url=_keycloak_admin_url(f"/roles/{quote(name, safe='')}"),
                headers=self._admin_headers(token=token),
                json={
                    "name":         str(role.get("name", name)),
                    "description":  desc
                }
            )

            if response.is_error:
                raise _admin_error(
                    response=response,
                    fallback=f"Could not update the Keycloak role [{name}]."
                )

            role = {
                **role,
                "description": desc
            }

        return role

    async def _admin_set_role_mapping(
        self,
        client:         AsyncClient,
        token:          str,
        subject:        str,
        role:           dict[str, Any],
        managed_roles:  Collection[str]
    ) -> None:
        response: HTTPXResponse = await client.get(
            url=_keycloak_admin_url(
                f"/users/{quote(subject, safe='')}/role-mappings/realm"
            ),
            headers=self._admin_headers(token=token)
        )

        if response.is_error:
            raise _admin_error(
                response=response,
                fallback="Could not read the Keycloak user role mappings."
            )

        payload: Any = response.json()
        mappings: list[dict[str, Any]] = (
            payload
            if isinstance(payload, list)
            else []
        )

        managed_keys: set[str] = {
            _role_key(managed_role)
            for managed_role in managed_roles
            if _role_key(managed_role)
        }
        target_key: str = _role_key(role.get("name", ""))
        current_keys: set[str] = {
            _role_key(mapping.get("name"))
            for mapping in mappings
        }

        to_remove: list[dict[str, Any]] = [
            mapping
            for mapping in mappings
            if (
                _role_key(mapping.get("name")) in managed_keys
                and
                _role_key(mapping.get("name")) != target_key
            )
        ]

        if to_remove:
            response = await client.request(
                method="DELETE",
                url=_keycloak_admin_url(
                    f"/users/{quote(subject, safe='')}/role-mappings/realm"
                ),
                headers=self._admin_headers(token=token),
                json=to_remove
            )

            if response.is_error:
                raise _admin_error(
                    response=response,
                    fallback="Could not remove the old Keycloak role mapping."
                )

        if target_key not in current_keys:
            response = await client.post(
                url=_keycloak_admin_url(
                    f"/users/{quote(subject, safe='')}/role-mappings/realm"
                ),
                headers=self._admin_headers(token=token),
                json=[role]
            )

            if response.is_error:
                raise _admin_error(
                    response=response,
                    fallback="Could not assign the new Keycloak role mapping."
                )

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
        async with AsyncClient(timeout=_KEYCLOAK_ADMIN_TIMEOUT) as client:
            token: str = await self._admin_token(client=client)
            current_user: dict[str, Any] | None = await self._admin_get_user(
                client=client,
                token=token,
                subject=subject
            )

            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "status": _status_label(status.HTTP_404_NOT_FOUND),
                        "message": "The user is not available in the IAM provider."
                    }
                )

            user_payload: dict[str, Any] = {}

            if name is not None:
                first_name: str
                last_name: str
                first_name, last_name = _name_parts(name=name)

                if not first_name:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "status": _status_label(status.HTTP_400_BAD_REQUEST),
                            "message": "The user name cannot be empty."
                        }
                    )

                user_payload["firstName"] = first_name
                user_payload["lastName"]  = last_name

            if email is not None:
                normalised_email: str = email.strip().lower()

                if not normalised_email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "status": _status_label(status.HTTP_400_BAD_REQUEST),
                            "message": "The user email cannot be empty."
                        }
                    )

                duplicate_users: list[dict[str, Any]] = await self._admin_find_users_by_email(
                    client=client,
                    token=token,
                    email=normalised_email
                )

                if any(
                    str(duplicate.get("id")) != subject
                    for duplicate in duplicate_users
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "status": _status_label(status.HTTP_409_CONFLICT),
                            "message": f"An IAM user with [{normalised_email}] email already exists."
                        }
                    )

                user_payload["email"] = normalised_email
                # Admin-driven profile edits must not silently lock the account
                # out by clearing the verified flag.
                user_payload["emailVerified"] = bool(
                    current_user.get(
                        "emailVerified",
                        False
                    )
                )

            role_representation: dict[str, Any] | None = None

            if role is not None:
                role_representation = await self._admin_ensure_role(
                    client=client,
                    token=token,
                    name=role,
                    desc=role_desc
                )

            if user_payload:
                response: HTTPXResponse = await client.put(
                    url=_keycloak_admin_url(
                        f"/users/{quote(subject, safe='')}"
                    ),
                    headers=self._admin_headers(token=token),
                    json=user_payload
                )

                if response.is_error:
                    raise _admin_error(
                        response=response,
                        fallback="Could not update the Keycloak user."
                    )

            if role_representation is not None:
                await self._admin_set_role_mapping(
                    client=client,
                    token=token,
                    subject=subject,
                    role=role_representation,
                    managed_roles=managed_roles
                )

            return None

    @override
    async def delete_user(
        self,
        subject: str
    ) -> None:
        async with AsyncClient(timeout=_KEYCLOAK_ADMIN_TIMEOUT) as client:
            token: str = await self._admin_token(client=client)
            response: HTTPXResponse = await client.delete(
                url=_keycloak_admin_url(
                    f"/users/{quote(subject, safe='')}"
                ),
                headers=self._admin_headers(token=token)
            )

            if response.status_code == status.HTTP_404_NOT_FOUND:
                return None

            if response.is_error:
                raise _admin_error(
                    response=response,
                    fallback="Could not delete the Keycloak user."
                )

            return None

    @override
    async def create_role(
        self,
        name: str,
        desc: str | None = None
    ) -> None:
        async with AsyncClient(timeout=_KEYCLOAK_ADMIN_TIMEOUT) as client:
            token: str = await self._admin_token(client=client)

            await self._admin_ensure_role(
                client=client,
                token=token,
                name=name,
                desc=desc
            )

            return None

    @override
    async def update_role(
        self,
        current_name:   str,
        *,
        name:           str | None = None,
        desc:           str | None = None
    ) -> None:
        async with AsyncClient(timeout=_KEYCLOAK_ADMIN_TIMEOUT) as client:
            token: str = await self._admin_token(client=client)
            current_role: dict[str, Any] | None = await self._admin_get_role(
                client=client,
                token=token,
                name=current_name
            )
            effective_name: str = current_name

            if current_role is None:
                # A previous attempt may have renamed the role and then failed
                # before the local DB write. Treat that as the successful state.
                if name is not None:
                    renamed_role: dict[str, Any] | None = await self._admin_get_role(
                        client=client,
                        token=token,
                        name=name
                    )

                    if renamed_role is not None:
                        current_role = renamed_role
                        effective_name = name

                if current_role is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "status": _status_label(status.HTTP_404_NOT_FOUND),
                            "message": f"The role [{current_name}] is not available in the IAM provider."
                        }
                    )

            target_name: str = (
                name
                if name is not None
                else str(current_role.get("name", effective_name))
            )
            target_desc: str | None = (
                desc
                if desc is not None
                else current_role.get("description")
            )

            response: HTTPXResponse = await client.put(
                url=_keycloak_admin_url(
                    f"/roles/{quote(effective_name, safe='')}"
                ),
                headers=self._admin_headers(token=token),
                json={
                    "name":         target_name,
                    "description":  target_desc
                }
            )

            if response.is_error:
                raise _admin_error(
                    response=response,
                    fallback=f"Could not update the Keycloak role [{current_name}]."
                )

            return None

    @override
    async def delete_role(
        self,
        name: str
    ) -> None:
        async with AsyncClient(timeout=_KEYCLOAK_ADMIN_TIMEOUT) as client:
            token: str = await self._admin_token(client=client)
            response: HTTPXResponse = await client.delete(
                url=_keycloak_admin_url(
                    f"/roles/{quote(name, safe='')}"
                ),
                headers=self._admin_headers(token=token)
            )

            if response.status_code == status.HTTP_404_NOT_FOUND:
                return None

            if response.is_error:
                raise _admin_error(
                    response=response,
                    fallback=f"Could not delete the Keycloak role [{name}]."
                )

            return None

    @override
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

    @override
    def callback_url(self) -> str:
        return f"{AUTH_PUBLIC_URL}/api/v1/auth/callback/{self.name}"

    @override
    def claims_from_user_info(
        self,
        user_info: Mapping[str, Any]
    ) -> NormalisedClaims:
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
            sub=user_info.get(
                "sub",
                ""
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
